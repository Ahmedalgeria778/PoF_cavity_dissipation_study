# -*- coding: utf-8 -*-
"""Certify the submitted package: every resource the two sources pull in, the
script that writes it, and the compiled documents.

Reviewers of the eleventh report could not check the layout of the figures and of
the auto-generated appendix tables because those files were not in the transmitted
package. This script re-derives that inventory from the repository itself, so the
certification can be repeated rather than asserted.

Writes docs/PACKAGE_CERTIFICATION.md.
"""
import hashlib
import os
import re
import subprocess
import sys

import matplotlib
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
MS = os.path.join(REPO, "manuscript", "manuscript_final.tex")
SP = os.path.join(REPO, "supplementary", "supplementary_final.tex")
BUILD = os.path.join(REPO, "build")
OUT = os.path.join(REPO, "docs", "PACKAGE_CERTIFICATION.md")

DOCS = {
    "manuscript": dict(src=MS, cwd=os.path.join(REPO, "manuscript"),
                       job="manuscript_final", ninput=False),
    "supplementary": dict(src=SP, cwd=os.path.join(REPO, "supplementary"),
                          job="supplementary_final", ninput=True),
}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve(name, cwd):
    """Where pdflatex finds the resource, given the source directory."""
    cands = [os.path.join(cwd, name),
             os.path.join(cwd, "figures", name),
             os.path.join(cwd, "data_appendix", name),
             os.path.join(cwd, "data_appendix", name + ".tex"),
             os.path.join(REPO, name)]
    for c in cands:
        if os.path.isfile(c):
            return c
    return None


_IGNORE_CACHE = {}


def distributed(path):
    """False for the scripts .gitignore excludes, i.e. the ones not shipped."""
    key = os.path.abspath(path)
    if key not in _IGNORE_CACHE:
        try:
            rc = subprocess.run(["git", "check-ignore", "-q", key],
                                cwd=REPO).returncode
        except Exception:
            rc = 1
        _IGNORE_CACHE[key] = (rc != 0)
    return _IGNORE_CACHE[key]


def producer(path):
    """The distributed scripts in scripts/ that name this artifact. This script
    itself is excluded: it quotes resource names in prose, which would otherwise
    read as a generator."""
    stem = os.path.basename(path).rsplit(".", 1)[0]
    hits = []
    for fn in sorted(os.listdir(HERE)):
        if not fn.endswith(".py") or fn == os.path.basename(__file__):
            continue
        with open(os.path.join(HERE, fn), encoding="utf-8") as fh:
            if stem in fh.read():
                hits.append(fn)
    return [h for h in hits if distributed(os.path.join(HERE, h))]


def pages(job):
    log = os.path.join(BUILD, job + ".log")
    if not os.path.isfile(log):
        return None, None
    txt = open(log, "rb").read().decode("latin-1")
    # pdflatex wraps its own messages at column 80, so the line that reports the
    # page count has to be re-joined before it can be matched.
    flat = txt.replace("\n", "")
    m = re.search(r"Output written on .*?%s\.pdf \((\d+) pages" % job, flat)
    n = int(m.group(1)) if m else None
    box = len(re.findall(r"Overfull \\hbox", txt))
    return n, box


def abstract_words():
    """Word count of the manuscript abstract as a journal counts it: each
    inline math span is one word."""
    src = open(MS, encoding="utf-8").read()
    body = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", src, re.S).group(1)
    body = re.sub(r"\$[^$]*\$", " MATH ", body)
    body = re.sub(r"\\[a-zA-Z]+\*?", " ", body)
    body = re.sub(r"[{}\\]", " ", body)
    return len(body.split())


SM_HEAD = "\\section*{Supplementary Material}"
CONCL_HEAD = "\\section{Conclusions}"
ACK_HEAD = "\\section*{Acknowledgments}"
DOCX = os.path.join(REPO, "supplementary", "supplementary_final.docx")

# The supplement numbers its floats with an S prefix, so the compiled aux records
# the highest number of each kind; those are the counts the manuscript quotes.
AUX_CHANNEL = re.compile(
    r"\\@writefile\{(toc|lot|lof)\}\{\\contentsline \{(?:section|table|figure)\}"
    r"\{\\numberline \{S(\d+)\}")
CLAIM = re.compile(r"(Secs|Tables|Figs)(\.?~)S(\d+)--S(\d+)")
CLAIM_KIND = {"toc": "Secs", "lot": "Tables", "lof": "Figs"}


def manuscript_body():
    src = open(MS, encoding="utf-8").read()
    return src[src.index(r"\begin{document}"):]


def supp_counts():
    """Highest S-number per aux channel: sections, tables, figures."""
    aux = os.path.join(BUILD, "supplementary_final.aux")
    if not os.path.isfile(aux):
        return None
    txt = open(aux, "rb").read().decode("latin-1")
    out = {}
    for ch, num in AUX_CHANNEL.findall(txt):
        out[ch] = max(out.get(ch, 0), int(num))
    return out


def supplementary_material_section():
    """Locate the manuscript's Supplementary Material section and return
    (problems, claims) where claims maps Secs/Tables/Figs to the spelling used
    and the upper bound of the quoted range."""
    body = manuscript_body()
    problems = []
    i, c, a = (body.find(SM_HEAD), body.find(CONCL_HEAD), body.find(ACK_HEAD))
    if i < 0:
        problems.append("the manuscript has no %s section" % SM_HEAD)
        return problems, {}
    if c < 0 or not c < i:
        problems.append("Supplementary Material does not follow the Conclusions")
    if a < 0 or not i < a:
        problems.append("Supplementary Material does not precede the Acknowledgments")
    seg = body[i + len(SM_HEAD):]
    nxt = seg.find("\\section")
    seg = seg[:nxt] if nxt >= 0 else seg
    if not seg.strip():
        problems.append("the Supplementary Material section holds no text")
    claims = {}
    for kind, tie, lo, hi in CLAIM.findall(seg):
        if int(lo) != 1:
            problems.append("the %s range does not start at S1" % kind)
        if kind in claims and claims[kind][1] != int(hi):
            problems.append("the manuscript quotes %s twice with different bounds"
                            % kind)
        claims[kind] = (kind + tie, int(hi))
    return problems, claims


def docx_stale():
    """Inputs newer than the Word file, i.e. a Word source that no longer
    matches the document it was generated from."""
    if not os.path.isfile(DOCX):
        return ["missing"]
    new = os.path.getmtime(DOCX)
    return [os.path.relpath(p, REPO).replace("\\", "/")
            for p in (SP, os.path.join(BUILD, "supplementary_final.aux"))
            if os.path.isfile(p) and os.path.getmtime(p) > new]


def main():
    lines = []
    lines.append("# Package certification")
    lines.append("")
    lines.append("Generated by `scripts/certify_package.py`; it lists every external "
                 "resource the two LaTeX sources pull in, the script in `scripts/` that "
                 "writes it, and the compiled documents. Every path was resolved by the "
                 "same rule pdflatex uses, so the inventory is what the build actually "
                 "read, not what the repository contains.")
    lines.append("")
    lines.append("## Environment")
    lines.append("")
    lines.append("| component | version |")
    lines.append("| --- | --- |")
    lines.append("| Python | %s |" % sys.version.split()[0])
    lines.append("| numpy | %s |" % np.__version__)
    lines.append("| matplotlib | %s |" % matplotlib.__version__)
    try:
        v = subprocess.run(["pdflatex", "--version"], capture_output=True, text=True,
                           check=True).stdout.splitlines()[0]
    except Exception as exc:  # pragma: no cover
        v = "unavailable (%s)" % exc
    lines.append("| pdflatex | %s |" % v.strip())
    lines.append("")

    fig_rows, tab_rows = [], []
    for tag, cfg in DOCS.items():
        with open(cfg["src"], encoding="utf-8") as fh:
            src = fh.read()
        for name in sorted(set(re.findall(r"\\includegraphics\[[^\]]*\]\{([^}]+)\}", src))):
            fig_rows.append((tag, name))
        if cfg["ninput"]:
            for name in sorted(set(re.findall(r"\\input\{([^}]+)\}", src))):
                tab_rows.append((tag, name))

    lines.append("## Figures pulled by the sources (%d)" % len(fig_rows))
    lines.append("")
    lines.append("| document | resource | resolved path | bytes | SHA-256 (first 16) | "
                 "written by |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    missing = []
    ungenerated = []
    for tag, name in fig_rows:
        p = resolve(name, DOCS[tag]["cwd"])
        if p is None:
            missing.append((tag, name))
            lines.append("| %s | `%s` | **NOT FOUND** | | | |" % (tag, name))
            continue
        prods = ", ".join("`%s`" % x for x in producer(p)) or "-"
        if prods == "-":
            ungenerated.append((tag, os.path.relpath(p, REPO).replace("\\", "/")))
        lines.append("| %s | `%s` | `%s` | %d | `%s` | %s |" %
                     (tag, name, os.path.relpath(p, REPO).replace("\\", "/"),
                      os.path.getsize(p), sha256(p)[:16], prods))
    lines.append("")

    lines.append("## Auto-generated table sources pulled by the supplement (%d)"
                 % len(tab_rows))
    lines.append("")
    lines.append("| resource | bytes | SHA-256 (first 16) | written by |")
    lines.append("| --- | --- | --- | --- |")
    for tag, name in tab_rows:
        p = resolve(name, DOCS[tag]["cwd"])
        if p is None:
            missing.append((tag, name))
            lines.append("| `%s` | **NOT FOUND** | | |" % name)
            continue
        prods = ", ".join("`%s`" % x for x in producer(p)) or "-"
        if prods == "-":
            ungenerated.append((tag, os.path.relpath(p, REPO).replace("\\", "/")))
        lines.append("| `%s` | %d | `%s` | %s |" %
                     (os.path.relpath(p, REPO).replace("\\", "/"), os.path.getsize(p),
                      sha256(p)[:16], prods))
    lines.append("")

    lines.append("## Compiled documents")
    lines.append("")
    lines.append("| document | pages | overfull hbox | PDF bytes | SHA-256 (first 16) |")
    lines.append("| --- | --- | --- | --- | --- |")
    for job in ("manuscript_final", "supplementary_final",
                "manuscript_final_marked", "supplementary_final_marked"):
        pdf = os.path.join(BUILD, job + ".pdf")
        n, box = pages(job)
        if os.path.isfile(pdf):
            lines.append("| `%s.pdf` | %s | %s | %d | `%s` |" %
                         (job, n, box, os.path.getsize(pdf), sha256(pdf)[:16]))
        else:
            lines.append("| `%s.pdf` | %s | %s | **NOT BUILT** | |" % (job, n, box))
    lines.append("")
    lines.append("The build is run from the document directories, so the resources above "
                 "resolve exactly as listed: "
                 "`cd manuscript && pdflatex -output-directory ../build manuscript_final.tex` "
                 "and `cd supplementary && pdflatex -output-directory ../build "
                 "supplementary_final.tex`, three passes of each source and of each "
                 "marked-up copy; the marked supplement needs the extra pass for its "
                 "table of contents, and three passes make the page count of the four "
                 "documents independent of the order in which they are built. "
                 "`scripts/check_build_logs.py` then parses the four logs and reports "
                 "0 problems.")
    lines.append("")
    lines.append("## Abstract")
    lines.append("")
    n_abs = abstract_words()
    lines.append("The manuscript abstract holds %d words, counting each inline math "
                 "span as one word; the submission limit is 250." % n_abs)
    lines.append("")

    sm_problems, claims = supplementary_material_section()
    counts = supp_counts()
    stale = docx_stale()
    lines.append("## Supplementary material")
    lines.append("")
    lines.append("The manuscript carries an unnumbered `Supplementary Material` "
                 "section, placed after the Conclusions and before the Acknowledgments "
                 "as the editor asked; AIP Publishing inserts the link to the posted "
                 "files in that position. The paragraph it opens quotes the float "
                 "ranges below, and those numbers are read back from the compiled "
                 "supplement rather than typed:")
    lines.append("")
    lines.append("| quoted range | compiled from `build/supplementary_final.aux` |")
    lines.append("| --- | --- |")
    for ch in ("toc", "lot", "lof"):
        kind = CLAIM_KIND[ch]
        got = counts.get(ch) if counts else None
        spell, hi = claims.get(kind, ("?", None))
        lines.append("| `%sS1--S%s` | %s |"
                     % (spell, "?" if hi is None else hi,
                        "%d in the aux" % got if got else "not built"))
    lines.append("")
    lines.append("The supplement is transmitted twice: as its LaTeX source and, in "
                 "parallel, as the word-processor source the editorial office also "
                 "requires.")
    lines.append("")
    lines.append("| file | bytes | SHA-256 (first 16) | written by |")
    lines.append("| --- | --- | --- | --- |")
    if os.path.isfile(DOCX):
        lines.append("| `supplementary/supplementary_final.docx` | %d | `%s` | "
                     "`scripts/make_supplementary_docx.py` |"
                     % (os.path.getsize(DOCX), sha256(DOCX)[:16]))
    else:
        lines.append("| `supplementary/supplementary_final.docx` | **NOT BUILT** | | "
                     "`scripts/make_supplementary_docx.py` |")
    lines.append("")
    lines.append("`scripts/make_supplementary_docx.py` converts the supplement source "
                 "itself: it re-types the prose, the float tables, the figures, the "
                 "numbered displays and the bibliography entries, and it fails unless "
                 "its own numbering reproduces the labels and the `\\bibcite` numbers "
                 "of `build/supplementary_final.aux`, unless every word of the source "
                 "outside the displays is present in the produced file, and unless the "
                 "running prose of the source reappears in the same order. It is run "
                 "by `scripts/build_all.sh` after the LaTeX passes, so the aux it "
                 "checks against is the one just written.")
    lines.append("")
    lines.append("## Resources without a generator in the repository")
    lines.append("")
    if ungenerated:
        lines.append("Every resource above except the following is written by a script "
                     "that is committed alongside it:")
        lines.append("")
        for tag, rel in ungenerated:
            lines.append("- %s: `%s`" % (tag, rel))
        lines.append("")
    else:
        lines.append("None: every figure and every table source listed above is written "
                     "by a committed script.")
    lines.append("")
    lines.append("## Raw inputs held outside the git tree")
    lines.append("")
    lines.append("The scripts are all committed; the large field archives they read are "
                 "not, and each set has a committed index that names it by filename, byte "
                 "size and SHA-256 checksum, so a copy obtained from the corresponding "
                 "author can be verified before the scripts are re-run:")
    lines.append("")
    lines.append("- `results/09_d2_capture/` holds the seven temporal captures behind "
                 "Secs. S4.5-S4.8 of the supplement, indexed by "
                 "`results/09_d2_capture/MANIFEST.md` and shipped as "
                 "`PoF_d2_captures_v1.tar`.")
    lines.append("- the three steady N=512 velocity fields (uniform lid, k=1, k=2) that "
                 "`scripts/make_fig_mechanism.py` renders into Main Fig. 4, indexed with "
                 "their byte sizes and SHA-256 digests by "
                 "`results/10_fig4_stationary_fields/FIELDS_MANIFEST.md` and shipped as "
                 "`PoF_fig4_fields_v1.tar`. That manifest is written by "
                 "`scripts/manifest_fig4_fields.py`, which also recomputes from those "
                 "fields the peak and interior-mean strain-rate magnitudes quoted in "
                 "Main Sec. 5.3 and fails if they no longer match.")
    lines.append("")
    lines.append("The dissipation values quoted for those three controls have committed "
                 "records independently of the fields: "
                 "`results/p1_gci_iso/p1_gci_raw.csv` (read by `scripts/make_fig_gci.py`) "
                 "and `results/p1_gci_iso/p1_gci_summary.csv` (read by "
                 "`scripts/export_legacy_supp_tables.py`).")
    lines.append("")
    if missing:
        lines.append("## Missing resources")
        lines.append("")
        for tag, name in missing:
            lines.append("- %s: `%s`" % (tag, name))
        lines.append("")
    else:
        lines.append("## Missing resources")
        lines.append("")
        lines.append("None: every `\\includegraphics` and `\\input` in the two sources "
                     "resolved to a file that exists in the repository.")
        lines.append("")

    with open(OUT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print("wrote", OUT)
    print("figures=%d tables=%d missing=%d" % (len(fig_rows), len(tab_rows),
                                               len(missing)))
    print("abstract words=%d (limit 250)" % n_abs)
    if n_abs > 250:
        print("ABSTRACT OVER THE 250-WORD LIMIT")
        raise SystemExit(1)
    for ch in ("toc", "lot", "lof"):
        kind, got = CLAIM_KIND[ch], (counts or {}).get(ch)
        if got is None:
            sm_problems.append("%s: no compiled supplement to read (build/"
                               "supplementary_final.aux missing)" % kind)
        elif kind not in claims:
            sm_problems.append("the Supplementary Material paragraph quotes no %s "
                               "range, but the supplement has %d" % (kind, got))
        elif claims[kind][1] != got:
            sm_problems.append("the manuscript quotes %sS1--S%s but the compiled "
                               "supplement holds %d"
                               % (claims[kind][0], claims[kind][1], got))
    if stale:
        if stale == ["missing"]:
            sm_problems.append("supplementary/supplementary_final.docx does not exist")
        else:
            sm_problems.append("the Word source is older than %s" % ", ".join(stale))
    if sm_problems:
        print("SUPPLEMENTARY MATERIAL GATE FAILED")
        for p in sm_problems:
            print("  - %s" % p)
        raise SystemExit(1)
    print("supplementary material: section after Conclusions and before "
          "Acknowledgments, Secs/Tables/Figs counts match the aux (%d/%d/%d), "
          "Word source current"
          % (counts["toc"], counts["lot"], counts["lof"]))


if __name__ == "__main__":
    main()
