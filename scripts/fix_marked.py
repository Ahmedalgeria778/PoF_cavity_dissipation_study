# -*- coding: utf-8 -*-
"""Remove empty lines that latexdiff leaves inside display-math environments.

latexdiff represents a deleted comment or a deleted \\label as a
``%DIFDELCMD`` line followed by an empty line.  When such a deletion falls
inside a display-math environment that is itself wrapped in ``\\DIFdel{...}``,
the empty line becomes a ``\\par`` token inside a macro argument, which LaTeX
rejects.  The empty lines carry no information, so they are dropped.
"""
import re
import sys

path = sys.argv[1]
lines = open(path, encoding="utf-8").read().split("\n")

MATH_BEGIN = re.compile(
    r"\\begin\{(displaymath|equation|align|gather|multline)\*?\}")
MATH_END = re.compile(
    r"\\end\{(displaymath|equation|align|gather|multline)\*?\}")

depth = 0
out = []
for line in lines:
    stripped = line.strip()
    if MATH_BEGIN.search(stripped):
        depth += 1
    if depth > 0 and stripped == "":
        continue
    if MATH_END.search(stripped):
        depth = max(0, depth - 1)
    out.append(line)

open(path, "w", encoding="utf-8").write("\n".join(out))
print("removed", len(lines) - len(out), "empty math lines from", path)
