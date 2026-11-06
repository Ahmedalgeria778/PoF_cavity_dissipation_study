# -*- coding: utf-8 -*-
"""Validate the two LaTeX builds: log errors, unresolved references, citations.

Logs are read with newlines stripped because pdflatex wraps warning messages.
Usage: py scripts/check_build_logs.py   (exit 0 only when nothing needs attention)
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
BUILD = os.path.join(REPO, "build")

TARGETS = [
    ("manuscript_final", os.path.join(REPO, "manuscript", "manuscript_final.tex")),
    ("supplementary_final",
     os.path.join(REPO, "supplementary", "supplementary_final.tex")),
    ("manuscript_final_marked",
     os.path.join(REPO, "manuscript", "manuscript_final_marked.tex")),
    ("supplementary_final_marked",
     os.path.join(REPO, "supplementary", "supplementary_final_marked.tex")),
]

FATAL_PATTERNS = [
    "LaTeX Error",
    "Undefined control sequence",
    "Emergency stop",
    "Fatal KernelCrash",
]
WARNING_PATTERNS = [
    ("undefined_reference", r"LaTeX Warning: Reference `([^']+)' on page \d+ undefined"),
    ("undefined_citation", r"LaTeX Warning: Citation `([^']+)' on page \d+ undefined"),
    ("missing_figure", r"LaTeX Error: File `([^']+)' not found"),
    ("graphics_not_found", r"Cannot find file `([^']+)'"),
    ("rerun_needed", r"Rerun to get (cross-references|the references) right"),
    ("multiply_defined", r"multiply-defined refs?\[([^\]]*)\]"),
]


def check(name, tex):
    log_path = os.path.join(BUILD, name + ".log")
    problems = 0
    if not os.path.exists(log_path):
        print("MISSING LOG", log_path)
        return 1
    raw = open(log_path, encoding="utf-8", errors="replace").read()
    flat = re.sub(r"\n", "", raw)

    pdf = re.findall(r"Output written on\s*(\S+?)\s*\((\d+)\s+pages", flat)
    print("-- %s: %s pages, pdf=%s" % (name, pdf[0][1] if pdf else "?",
                                       os.path.basename(pdf[0][0]) if pdf else "NONE"))
    if not pdf:
        problems += 1

    for pat in FATAL_PATTERNS:
        hits = re.findall(pat + r"(.{0,120})", flat)
        if hits:
            problems += 1
            print("   FATAL %s x%d: %s" % (pat, len(hits), hits[0][:120]))
    for label, pat in WARNING_PATTERNS:
        keys = sorted(set(re.findall(pat, flat)))
        if keys:
            problems += 1
            print("   %s: %s" % (label, ", ".join(map(str, keys[:20]))))

    over = [float(v) for v in re.findall(r"Overfull \\hbox \(([\d.]+)pt", flat)]
    under = len(re.findall(r"Underfull \\[vh]box", flat))
    print("   boxes: overfull=%d (max %.1f pt, >20pt: %d), underfull=%d"
          % (len(over), max(over) if over else 0.0,
             sum(1 for v in over if v > 20), under))

    src = open(tex, encoding="utf-8").read()
    aux = open(os.path.join(BUILD, name + ".aux"), encoding="utf-8",
               errors="replace").read()
    defined = set(re.findall(r"\\newlabel\{([^}]+)\}", aux))
    defined |= set(re.findall(r"\\bibcite\{([^}]+)\}", aux))
    used = set(re.findall(r"\\ref\{([^}]+)\}", src)) | set(re.findall(r"\\eqref\{([^}]+)\}", src))
    for grp in re.findall(r"\\cite[pt]?\*?(?:\[[^\]]*\])*\{([^}]+)\}", src):
        used |= {k.strip() for k in grp.split(",")}
    missing = sorted(used - defined)
    if missing:
        problems += 1
        print("   unresolved after build: %s" % ", ".join(missing))
    orphan = sorted(defined - used)
    if orphan:
        print("   defined but not referenced: %s" % ", ".join(orphan))
    return problems


def main():
    total = 0
    for name, tex in TARGETS:
        print("=" * 72)
        total += check(name, tex)
    print("=" * 72)
    print("TOTAL PROBLEMS:", total)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
