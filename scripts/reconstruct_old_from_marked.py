# -*- coding: utf-8 -*-
"""Rebuild the previous-version baseline from a marked-up file.

The submission package stores no copy of the manuscript that the marked-up
version was diffed against, but the marked file contains it: its red
``chgdel`` blocks hold the obsolete paragraphs and its unmarked text was
carried over unchanged.  Dropping the blue blocks and unwrapping the red ones
therefore reconstructs the baseline well enough to re-run the paragraph diff,
which only needs the old text for matching and for reprinting deletions.

Usage:  py reconstruct_old_from_marked.py  marked.tex  old.tex
"""
import re
import sys


def cut_marker(text):
    """Drop the xcolor macro block and the boxed note the marker inserts."""
    out, skip = [], False
    for line in text.split("\n"):
        if "marked-up version" in line and line.startswith("%"):
            skip = True
        if skip:
            if re.match(r"^%[-\s]*$", line) and "marked-up" not in line:
                skip = False
            continue
        out.append(line)
    text = "\n".join(out)
    return re.sub(r"\\begin\{center\}\n\\fbox\{.*?\\end\{center\}\n", "", text,
                  flags=re.S)


def main(marked_path, out_path):
    text = open(marked_path, encoding="utf-8").read().replace("\r\n", "\n")
    text = cut_marker(text)

    def emit(m):
        return m.group(2) if m.group(1) == "chgdel" else ""

    text = re.sub(r"\\begin\{(chgadd|chgdel)\}\n(.*?)\n\\end\{\1\}", emit, text, flags=re.S)
    text = re.sub(r"\n{3,}", "\n\n", text)
    open(out_path, "w", encoding="utf-8").write(text)
    print("wrote", out_path, len(text), "chars")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
