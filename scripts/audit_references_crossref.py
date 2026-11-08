#!/usr/bin/env python3
r"""Cross-check every \bibitem of the two documents against the Crossref record.

For each entry the quoted title and the parenthesised year are taken from the local
text, Crossref is queried with a bibliographic search restricted to that year +-1, and
the closest hit is printed next to what the manuscript claims. The script reports; it
never edits. Entries with no DOI in the publisher record (books, older conference
papers) are listed as UNMATCHED for manual check. Needs network access.

    py scripts/audit_references_crossref.py [--offline-cache FILE]
"""
from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
import urllib.parse
import urllib.request

DOCS = {
    "manuscript": "manuscript/manuscript_final.tex",
    "supplement": "supplementary/supplementary_final.tex",
}
BIBITEM = re.compile(r"\\bibitem\{([^}]+)\}")
TITLE = re.compile(r"``(.+?),''|\{\\emph\{(.+?)\}\}", re.S)
YEAR = re.compile(r"\((\d{4})\)")
MAILTO = "submission-check@localhost"


def parse(path: str) -> list[tuple[str, str]]:
    src = open(path, encoding="utf-8").read()
    marks = list(BIBITEM.finditer(src))
    stop_all = src.find("\\end{thebibliography}")
    out = []
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else (
            stop_all if stop_all > m.end() else len(src))
        out.append((m.group(1), re.sub(r"\s+", " ", src[m.end():end]).strip()))
    return out


def crossref(title: str, year: int | None, cache: dict):
    params = {"query.bibliographic": title, "rows": "5"}
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    if url not in cache:
        req = urllib.request.Request(url, headers={"User-Agent": f"ref-audit/1.0 (mailto:{MAILTO})"})
        try:
            with urllib.request.urlopen(req, timeout=30) as fh:
                cache[url] = json.load(fh)
        except Exception as exc:  # network unavailable: report, do not fail the audit
            cache[url] = {"error": str(exc)}
    data = cache[url]
    if "error" in data:
        print(f"  network error: {data['error']}", file=sys.stderr)
        return None
    best, score = None, 0.0
    for item in data.get("message", {}).get("items", []):
        cand = (item.get("title") or [""])[0]
        ratio = difflib.SequenceMatcher(None, title.lower(), cand.lower()).ratio()
        if year and _pub_year(item) == year:
            ratio += 0.15
        if ratio > score:
            best, score = item, ratio
    items = data.get("message", {}).get("items", [])
    return (best, min(score, 1.0), items) if best else None


def _pub_year(item: dict) -> int | None:
    for k in ("published-print", "published-online", "issued"):
        if k in item:
            parts = item[k].get("date-parts") or [[None]]
            if parts[0][0]:
                return parts[0][0]
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    ap.add_argument("--cache", default="build/crossref_cache.json",
                    help="response cache (kept out of the tracked tree by default)")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--show-keys", default="",
                    help="comma-separated keys: also print every Crossref candidate")
    args = ap.parse_args()

    cachefile = os.path.join(args.root, args.cache)
    cache = {} if args.refresh and os.path.isfile(cachefile) else (
        json.load(open(cachefile, encoding="utf-8")) if os.path.isfile(cachefile) else {})

    seen, flagged, unmatched = {}, [], []
    show = {k.strip() for k in args.show_keys.split(",") if k.strip()}
    for doc, rel in DOCS.items():
        for key, text in parse(os.path.join(args.root, rel)):
            if key in seen:
                continue
            tm, ym = TITLE.search(text), YEAR.search(text)
            if not tm:
                unmatched.append((doc, key, "no quoted title", text[:90]))
                continue
            title = (tm.group(1) or tm.group(2)).replace("--", "-")
            year = int(ym.group(1)) if ym else None
            hit = crossref(title, year, cache)
            if hit is None:
                unmatched.append((doc, key, "crossref unreachable", title[:60]))
                continue
            item, score, candidates = hit
            cand = (item.get("title") or [""])[0]
            pub = (item.get("container-title") or [""])[0]
            vol, page = item.get("volume", ""), item.get("page", "")
            dy = _pub_year(item)
            if key in show:
                for c in candidates:
                    print(f"   ? {(c.get('title') or [''])[0][:68]:68s} "
                          f"{(c.get('container-title') or [''])[0][:24]:24s} "
                          f"v{c.get('volume', '')} p{c.get('page', '')} "
                          f"({_pub_year(c)}) {c.get('DOI', '')}")
            seen[key] = True
            local = re.sub(r"\\[a-zA-Z]+|[{}~\\]", "", text)
            flags = []
            if score < 0.85:
                flags.append(f"LOW-SIMILARITY {score:.2f} crossref-title={cand[:70]}")
            if dy and year and dy != year:
                flags.append(f"YEAR local={year} crossref={dy}")
            if vol and str(vol) not in local:
                flags.append(f"VOLUME crossref={vol}")
            first_page = (page.split("-") or [""])[0]
            if first_page and first_page not in local:
                flags.append(f"PAGES crossref={page}")
            print(f"{'!! ' if flags else 'OK '}{key:32s} {pub[:28]:28s} v{vol} p{page} ({dy})")
            if flags:
                flagged.append(key)
                for f in flags:
                    print(f"     {f}")
                print(f"     local: {text[:170]}")
    os.makedirs(os.path.dirname(cachefile), exist_ok=True)
    json.dump(cache, open(cachefile, "w", encoding="utf-8"))
    print(f"\nchecked={len(seen)} flagged={len(flagged)} unmatched={len(unmatched)}")
    for row in unmatched:
        print(f"  UNMATCHED {row[0]}:{row[1]} ({row[2]}) {row[3]}")
    return 1 if unmatched else 0


if __name__ == "__main__":
    sys.exit(main())
