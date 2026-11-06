#!/bin/bash
# Chaine D2 : B1 -> B2 -> B3 sequentiel.
set -e
ROOT="C:/Users/user/Documents/Qoder/2026-11-03/2b4d7c2e/PoF_cavity_dissipation_study"
cd "$ROOT"
mkdir -p results/09_d2_capture
for CASE in B1 B2 B3; do
  echo "===== D2 branch $CASE ====="
  PYTHONIOENCODING=utf-8 py scripts/run_branch_capture_d2.py --case "$CASE"
done
echo "===== D2 campaign finished ====="
