"""Advisory style report for the two transmitted documents.

Counts connective and filler phrases whose repetition reads as templated rather
than authored, and tabulates the opening words of sentences so that a single
crutch can be spotted. Nothing here is a verdict on correctness; the script is
advisory and is deliberately not part of the build gates.

Usage: py scripts/check_style.py [file ...]
"""
import re
import sys
from collections import Counter

FILLER = [
    "it is worth noting", "worth noting", "it should be noted", "note that",
    "keep in mind", "importantly", "importantly", "crucially", "notably",
    "interestingly", "remarkably", "we note that", "we emphasize", "we stress",
    "we highlight", "underscore", "plays a key role", "plays a crucial role",
    "serves as", "is designed to", "leverage", "utilize", "delve",
    "comprehensive", "seamless", "streamline", "holistic", "paradigm",
    "showcase", "harness", "foster", "facilitate", "in other words",
    "that is to say", "taken together", "all in all", "in summary",
    "let us", "it is important to", "matters because", "it is legitimate",
    "more importantly", "needless to say", "obviously", "very", "really",
    "quite a", "a lot of", "make sure", "furthermore", "moreover",
    "additionally", "therefore", "thus", "hence", "so that", "which is why",
]

DEFAULT = ["manuscript/manuscript_final.tex", "supplementary/supplementary_final.tex"]


def prose(path):
    """Return the running text of a LaTeX file: comments, display math,
    figure/table blocks and preambles removed, inline math kept as a token."""
    out = []
    skip_env = ("figure", "table", "longtable", "tabularx", "eqnarray", "align",
                "equation", "gather")
    depth = 0
    for line in open(path, encoding="utf-8"):
        line = line.split("%")[0].rstrip()
        inside = depth > 0
        if any("\\begin{" + env in line for env in skip_env):
            depth += 1
        if any("\\end{" + env in line for env in skip_env) and depth:
            depth -= 1
        if inside or depth:
            continue
        if re.match(r"\\(usepackage|documentclass|bibitem|label|newcommand|setlength|renewcommand)", line):
            continue
        if re.match(r"\\(section|subsection|subsubsection|paragraph|bibliography|input|includegraphics|maketitle)\*?\{", line):
            continue
        if re.match(r"\\(begin|end)\{", line) or "\\noindent\\textbf{Keywords" in line:
            continue
        line = re.sub(r"\\[a-zA-Z@]+\*?}", " ", line)
        line = re.sub(r"[{}&]", " ", line)
        if not line.strip():
            continue
        out.append(line.strip())
    return " ".join(out)


ABBREV = r"\b(?:Sec|Secs|Eq|Eqs|Fig|Figs|Tab|Tabs|Ref|Refs|Al|approx|cf|Vol|No|pp|etal|e\.g|i\.e)\.(?=\s)"


def sentences(text):
    text = re.sub(r"\$[^$]*\$", " MATH ", text)
    text = re.sub(r"\([^)]*\)", " ", text)
    text = re.sub(ABBREV, lambda m: m.group(0)[:-1] + "@", text)
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip().replace("@", ".").replace("MATH", "") for p in parts
            if len(p.strip().split()) > 3]


def main(argv):
    for path in argv or DEFAULT:
        text = prose(path)
        low = text.lower()
        print("=" * 72)
        print("-- %s: %d words of running text" % (path, len(text.split())))
        hits = [(len(re.findall(r"\b" + re.escape(p) + r"\b", low)), p) for p in FILLER]
        hits = sorted([c for c in hits if c[0]])
        for count, phrase in hits[:18]:
            print("   %-22s %d" % (phrase, count))
        lines = open(path, encoding="utf-8").read().splitlines()
        want = [p for c, p in hits if p in
                ("therefore", "thus", "hence", "which is why", "we note that",
                 "note that", "matters because", "taken together", "additionally",
                 "importantly", "it is legitimate", "in other words", "serves as")]
        if want:
            pat = "(" + "|".join(re.escape(w) for w in want) + ")"
            for i, line in enumerate(lines, 1):
                m = re.search(pat, line, re.I)
                if m:
                    print("   L%-5d %-16s | %s" % (i, m.group(1).lower(), line.strip()[:88]))
        sent = sentences(text)
        opens = Counter(" ".join(s.split()[:2]).title()[:24] for s in sent)
        print("   sentences: %d; mean length %.1f words; longest %d"
              % (len(sent), sum(len(s.split()) for s in sent) / max(len(sent), 1),
                 max((len(s.split()) for s in sent), default=0)))
        print("   repeated two-word openings:",
              ", ".join("%s (%d)" % (o, c) for o, c in opens.most_common(8) if c > 1))
        long_ones = [s for s in sent if len(s.split()) > 55]
        print("   sentences over 55 words: %d" % len(long_ones))
        for s in sorted(sent, key=lambda s: len(s.split()), reverse=True)[:3]:
            print("   longest (%d words): %s..." % (len(s.split()), s[:96]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
