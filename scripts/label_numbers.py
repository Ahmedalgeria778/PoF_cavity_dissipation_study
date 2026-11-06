# -*- coding: utf-8 -*-
"""Print label -> number/page for the two builds, from the pdflatex .aux files.

Usage: py scripts/label_numbers.py [tab fig sec eq]
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
BUILD = os.path.join(REPO, "build")
DOCS = ["manuscript_final", "supplementary_final"]


def main():
    kinds = sys.argv[1:] or ["tab", "fig", "sec", "eq"]
    for doc in DOCS:
        path = os.path.join(BUILD, doc + ".aux")
        if not os.path.exists(path):
            print("missing", path)
            continue
        text = open(path, encoding="utf-8", errors="replace").read()
        print("=" * 60)
        print(doc)
        for m in re.finditer(r"\\newlabel\{([^}]+)\}\{\{([^}]*)\}\{([^}]*)\}", text):
            label, number, page = m.group(1), m.group(2), m.group(3)
            if label.split(":")[0] in kinds:
                print("  %-46s = %-8s p%s" % (label, number, page))


if __name__ == "__main__":
    main()
