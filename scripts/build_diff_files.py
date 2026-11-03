# -*- coding: utf-8 -*-
"""Build the two files compared by latexdiff.

Both files share the preamble of the new physics-first manuscript, so that
latexdiff marks only body changes.  The old file is the old body (from
\\begin{document} onwards) placed under the new preamble.

Two transformations make the marked-up file compile:

* comments are stripped, because latexdiff represents deleted comments as
  ``%DIFDELCMD <`` lines and leaves stray empty lines behind;
* blank lines become an explicit ``\\endgraf`` token, because a real ``\\par``
  token cannot appear inside the argument of ``\\DIFdel``.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
FINAL = os.path.abspath(os.path.join(HERE, ".."))
OLD = os.path.abspath(os.path.join(FINAL, "..", "manuscript.tex"))


def strip_comments(text):
    out = []
    for line in text.split("\n"):
        # keep escaped percents, drop the rest of a real comment
        m = re.search(r"(?<!\\)%", line)
        if m:
            line = line[: m.start()]
        out.append(line.rstrip())
    return "\n".join(out)


def join_paragraphs(body):
    body = body.replace("\r\n", "\n")
    body = re.sub(r"\n[ \t]*\n", lambda m: "\n\\endgraf\n", body)
    return body


new = open(os.path.join(FINAL, "manuscript_final.tex"), encoding="utf-8").read()
old = open(OLD, encoding="utf-8").read()

i = new.index(r"\begin{document}")
preamble = new[:i]
new_body = new[i:]

j = old.index(r"\begin{document}")
old_body = old[j:]

open(os.path.join(FINAL, "diff_new.tex"), "w", encoding="utf-8").write(
    preamble + join_paragraphs(strip_comments(new_body)))
open(os.path.join(FINAL, "diff_old.tex"), "w", encoding="utf-8").write(
    preamble + join_paragraphs(strip_comments(old_body)))
print("wrote diff_new.tex and diff_old.tex")
