#!/bin/sh
# Rebuild the four transmitted documents and re-run every package gate.
#
# The supplement must be compiled from inside supplementary/ because its appendix
# tables are pulled with \input{data_appendix/...}, which is resolved against the
# current directory. Auxiliaries go to build/ so the source trees stay clean; stale
# .aux files left in a source directory shadow the fresh ones in build/ and resurrect
# the previous round's labels.
#
# Usage: sh scripts/build_all.sh [--passes N]
set -eu

PASSES=3
if [ "${1:-}" = "--passes" ]; then PASSES="${2:?missing pass count}"; shift 2; fi
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"

for doc in manuscript/manuscript_final manuscript/manuscript_final_marked \
           supplementary/supplementary_final supplementary/supplementary_final_marked \
           docs/RESPONSE_TO_EDITOR; do
    dir=$(dirname "$doc")
    job=$(basename "$doc")
    rm -f "$dir/$job.aux" "$dir/$job.log" "$dir/$job.out" "$dir/$job.toc"
    i=0
    while [ "$i" -lt "$PASSES" ]; do
        (cd "$dir" && pdflatex -interaction=nonstopmode -output-directory ../build "./$job.tex" >/dev/null)
        i=$((i + 1))
    done
    cp "build/$job.pdf" "$dir/$job.pdf"
    echo "built $dir/$job.pdf"
done

py scripts/check_build_logs.py
py scripts/check_bibliography.py
py scripts/certify_package.py
