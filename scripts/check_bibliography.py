#!/usr/bin/env python3
r"""Audit the two reference lists: uncited entries, missing entries, and drift.

The manuscript and the supplement each carry their own \bibitem list, so an entry
cited in both can silently diverge in wording, volume or pages. This script compares
them verbatim after whitespace normalisation, and checks that every \cite key resolves
and that no listed entry is dead weight. Exit code 1 on any finding.
"""
from __future__ import annotations

import argparse
import re
import sys

DOCS = {
    "manuscript": "manuscript/manuscript_final.tex",
    "supplement": "supplementary/supplementary_final.tex",
}

BIBITEM = re.compile(r"\\bibitem\{([^}]+)\}")
CITE = re.compile(r"\\cite\{([^}]*)\}")


def normalize(text: str) -> str:
    text = text.replace("\\emph{", "").replace("\\textbf{", "").replace("}", "")
    text = text.replace("{", "").replace("$", "")
    return re.sub(r"\s+", " ", text).strip()


def parse(path: str) -> tuple[dict[str, str], set[str]]:
    src = open(path, encoding="utf-8").read()
    items: dict[str, str] = {}
    marks = list(BIBITEM.finditer(src))
    stop_all = src.find("\\end{thebibliography}")
    for i, m in enumerate(marks):
        if i + 1 < len(marks):
            end = marks[i + 1].start()
        else:
            end = stop_all if stop_all > m.end() else len(src)
        items[m.group(1)] = normalize(src[m.end():end])
    cited: set[str] = set()
    for m in CITE.finditer(src):
        cited.update(k.strip() for k in m.group(1).split(",") if k.strip())
    return items, cited


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    args = ap.parse_args()

    lists, cited_all, problems = {}, set(), []
    for name, rel in DOCS.items():
        items, cited = parse(f"{args.root}/{rel}")
        lists[name] = items
        cited_all |= cited
        for key in sorted(cited - set(items)):
            problems.append(f"{name}: \\cite{{{key}}} has no bibitem")
        for key in sorted(set(items) - cited):
            problems.append(f"{name}: bibitem{{{key}}} is never cited")

    shared = sorted(set(lists["manuscript"]) & set(lists["supplement"]))
    for key in shared:
        if lists["manuscript"][key] != lists["supplement"][key]:
            problems.append(f"drift: {key} differs between manuscript and supplement")
            problems.append(f"  manuscript: {lists['manuscript'][key][:180]}")
            problems.append(f"  supplement: {lists['supplement'][key][:180]}")

    print(f"entries: manuscript={len(lists['manuscript'])} "
          f"supplement={len(lists['supplement'])} shared={len(shared)} "
          f"cited={len(cited_all)}")
    if problems:
        print("\n".join(problems))
        print(f"PROBLEMS: {len(problems)}")
        return 1
    print("PROBLEMS: 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
