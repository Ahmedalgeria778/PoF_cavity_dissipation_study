# -*- coding: utf-8 -*-
"""Build a marked-up version of a manuscript by paragraph-level diffing.

The two manuscripts compared here are not successive drafts with local edits:
the physics-first paper is a reorganised text in which most paragraphs were
rewritten, moved or deleted.  A word-level diff of such a pair is both
unreadable and fragile (latexdiff inserts markup that is illegal inside
alignments and display math).  This script therefore marks changes at the
paragraph level:

* paragraphs of the old text that have no counterpart are printed in red
  (removed);
* paragraphs of the new text that have no counterpart are printed in blue
  (added);
* unchanged paragraphs are printed in black.

Removed paragraphs are sanitised before they are typeset: labels, references,
citations and obsolete floats are stripped so that the marked file compiles
without duplicate labels or missing graphics.

Usage:  py mark_manuscript.py  old.tex  new.tex  output.tex
"""
import difflib
import re
import sys

SECTION = re.compile(r"\\(sub)*section\*?\s*\{")
CITE = re.compile(r"\\cite[a-zA-Z]*\{[^}]*\}")
LABEL = re.compile(r"\\label\{[^}]*\}")
REF = re.compile(r"\\[A-Za-z]*ref\*?\{[^}]*\}")


def strip_comments(text):
    out = []
    for line in text.split("\n"):
        m = re.search(r"(?<!\\)%", line)
        out.append((line[: m.start()] if m else line).rstrip())
    return "\n".join(out)


MATH_BEGIN = re.compile(
    r"\\begin\{(displaymath|equation|align|alignat|gather|multline|eqnarray|flalign)\*?\}")
MATH_END = re.compile(
    r"\\end\{(displaymath|equation|align|alignat|gather|multline|eqnarray|flalign)\*?\}")


def math_delta(block):
    """Unbalanced display math across a block: >0 means a display is left open."""
    d = len(MATH_BEGIN.findall(block)) - len(MATH_END.findall(block))
    d += len(re.findall(r"(?<!\\)\\\[", block)) - len(re.findall(r"(?<!\\)\\]", block))
    d += len(re.findall(r"\$\$", block)) % 2
    return d


def split_blocks(body):
    """Paragraph list, with displays that a blank line cut in half rejoined."""
    parts = [b for b in re.split(r"\n\s*\n", body) if b.strip()]
    merged = []
    pending = ""
    depth = 0
    for b in parts:
        pending = (pending + "\n\n" + b) if pending else b
        depth += math_delta(b)
        if depth <= 0:
            merged.append(pending)
            pending, depth = "", 0
    if pending:
        merged.append(pending)
    return merged


def normalise(block):
    return re.sub(r"\s+", " ", strip_comments(block)).strip()


def replace_sections(block):
    """Turn \\section{...} into \\textbf{...} with balanced-brace matching."""
    out = []
    i = 0
    while True:
        m = SECTION.search(block, i)
        if not m:
            out.append(block[i:])
            break
        out.append(block[i:m.start()])
        # find the balanced argument
        k = m.end()  # just after '{'
        depth = 1
        while k < len(block) and depth:
            if block[k] == "{":
                depth += 1
            elif block[k] == "}":
                depth -= 1
            k += 1
        title = block[m.end():k - 1]
        if depth:
            out.append(block[m.start():])
            break
        out.append("\\textbf{" + title + "}")
        i = k
    return "".join(out)


def sanitise_deleted(block):
    """Make an obsolete paragraph safe to typeset in red."""
    if re.search(r"\\begin\{(figure|table|longtable)\*?\}", block):
        return None
    block = re.sub(r"^\\input\{[^}]*\}\s*$", "", block, flags=re.M)
    block = replace_sections(block)
    block = LABEL.sub("", block)
    block = REF.sub("?", block)
    block = CITE.sub("", block)
    return block.strip()


def drop_empty_math_lines(text):
    """Remove empty lines left inside display-math environments.

    Stripping a \\label that stood on its own line leaves an empty line, which
    is a paragraph break inside a display environment and does not compile.
    """
    depth = 0
    out = []
    for line in text.split("\n"):
        stripped = line.strip()
        if MATH_BEGIN.search(stripped) or re.search(r"(?<!\\)\\\[", stripped):
            depth += 1
        if depth and stripped == "":
            continue
        if MATH_END.search(stripped) or re.search(r"(?<!\\)\\]", stripped):
            depth = max(0, depth - 1)
        out.append(line)
    return "\n".join(out)


def main(old_path, new_path, out_path):
    new = open(new_path, encoding="utf-8").read().replace("\r\n", "\n")
    old = open(old_path, encoding="utf-8").read().replace("\r\n", "\n")

    i = new.index(r"\begin{document}")
    preamble, new_body = new[:i], new[i:]
    j = old.index(r"\begin{document}")
    old_body = old[j:]

    old_body = old_body.split(r"\begin{thebibliography}")[0]
    old_body = old_body.replace(r"\end{document}", "")
    # the opening (title block) is taken from the new file
    old_body = old_body[old_body.index(r"\begin{document}") + len(r"\begin{document}"):]
    old_body = re.sub(r"^\s*\\maketitle", "", old_body)
    old_body = re.sub(r"^\s*\\tableofcontents", "", old_body)
    old_body = re.sub(r"^\s*\\newpage", "", old_body)
    new_body = new_body.replace(r"\end{document}", "")

    # keep the opening (title, \maketitle, table of contents) out of the diff
    m = re.search(r"\\maketitle", new_body)
    if m:
        head = new_body[: m.end()]
        rest = new_body[m.end():]
    else:
        head = r"\begin{document}"
        rest = new_body[len(head):]

    old_blocks = split_blocks(old_body)
    new_blocks = split_blocks(rest)

    sm = difflib.SequenceMatcher(None, [normalise(b) for b in old_blocks],
                                 [normalise(b) for b in new_blocks],
                                 autojunk=False)
    out = []
    for tag, a0, a1, b0, b1 in sm.get_opcodes():
        if tag == "equal":
            out.extend(new_blocks[b0:b1])
            continue
        if tag in ("delete", "replace"):
            kept = [sanitise_deleted(b) for b in old_blocks[a0:a1]]
            kept = [k for k in kept if k]
            if kept:
                out.append("\\begin{chgdel}\n" + "\n\n".join(kept) +
                           "\n\\end{chgdel}")
        if tag in ("insert", "replace"):
            out.append("\\begin{chgadd}\n" + "\n\n".join(new_blocks[b0:b1]) +
                       "\n\\end{chgadd}")

    macros = r"""
%-------------------------- marked-up version --------------------------
\usepackage{xcolor}
\newenvironment{chgadd}{\par\color{blue}}{\par\color{black}}
\newenvironment{chgdel}{\par\color{red}}{\par\color{black}}
%-----------------------------------------------------------------------
"""
    preamble = preamble + macros

    note = r"""

\begin{center}
\fbox{\parbox{0.92\linewidth}{\small
\textbf{Marked-up manuscript.} This file is the revised manuscript with the
changes made relative to the previous version marked. Text in
\textcolor{blue}{blue} is new or rewritten; text in \textcolor{red}{red}
belonged to the previous version and has been removed or replaced. Obsolete
figures and tables of the previous version are not reproduced here; the
corresponding changes are itemised in the response to the editor. Because the
physics-first version is a reorganisation of the paper, most paragraphs carry
a mark.}}
\end{center}
\medskip
"""
    text = (preamble + head + note + "\n\n" + "\n\n".join(out) +
            "\n\\end{document}\n")
    text = drop_empty_math_lines(text)
    open(out_path, "w", encoding="utf-8").write(text)
    print("wrote", out_path, ":", len(old_blocks), "old blocks,",
          len(new_blocks), "new blocks")


if __name__ == "__main__":
    main(*sys.argv[1:4])
