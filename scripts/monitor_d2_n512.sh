#!/bin/bash
# Surveille (et releve) les trois branches N=512 de la campagne D2.
#
# Pourquoi un deuxieme chien de garde : le launcher a deja ete tuer externement
# le 2026-11-05 a ~19:17 (balayage de tous les processus dont la ligne de
# commande contenait run_branch_capture_d2 / campaign). Le watchdog interne du
# launcher meurt avec lui. Ce script-la, lance detache, verifie chaque cycle :
#   archive presente          -> branche finie, on ne fait plus rien
#   solveur python vivant     -> on releve la progression dans le journal
#   solveur absent            -> on relance un launcher (Start-Process detache)
#
# Budget de relance borne (MAX_HEAL) pour ne pas tourner en boucle si un agent
# exterieur tue les runs plus vite qu'ils n'avancent.
#
# Usage : bash scripts/monitor_d2_n512.sh          # tourne jusqu'a ce que les 3
#         bash scripts/monitor_d2_n512.sh --once   # un seul releve, puis sort
set -e
ROOT="C:/Users/user/Documents/Qoder/2026-11-03/2b4d7c2e/PoF_cavity_dissipation_study"
cd "$ROOT"
OUT="results/09_d2_capture"
MON="$OUT/monitor_status.log"
CASES="B1 B2 B3"
INTERVAL=300
MAX_HEAL=12
CYCLES=200          # 200 x 300 s = ~16 h de surveillance
ONCE=0
[ "${1:-}" = "--once" ] && ONCE=1

count_alive() {                     # $1 = case
  powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { \$_.Name -eq 'python.exe' -and \$_.CommandLine -match 'run_branch_capture_d2\.py --case $1 --N 512' } | Measure-Object | Select-Object -ExpandProperty Count" 2>/dev/null | tr -d '\r'
}

last_line() {                       # $1 = case : derniere ligne de progression
  local f
  f=$(ls -t "$OUT"/campaign_n512_hold_c32_*_"$1"_stdout.log 2>/dev/null | head -1)
  [ -z "$f" ] && f=$(ls -t "$OUT"/campaign_n512_hold_c32_*"$1"*stdout.log 2>/dev/null | head -1)
  [ -z "$f" ] && { echo "aucun journal"; return; }
  grep -aE "warm it=|WARMUP|capture P|RESUME|DONE|branche|echouee|CKPT" "$f" | tail -1
}

heal() {                            # $1 = case
  powershell -NoProfile -Command "Start-Process -FilePath 'C:\Program Files\Git\bin\bash.exe' -ArgumentList '$ROOT/scripts/launch_d2_n512_campaign.sh','--cases','$1','--allow-other-python' -WindowStyle Hidden" 2>/dev/null
  echo "  -> relance $1 $(date '+%F %T')"
}

HEAL_USED=0
for ((i = 0; i < CYCLES; i++)); do
  ALL_DONE=1
  for CASE in $CASES; do
    TAG="capture_${CASE}_D2_N512"
    if [ -f "$OUT/${TAG}.npz" ]; then
      SZ=$(( $(stat -c %s "$OUT/${TAG}.npz") / 1048576 ))
      echo "$(date '+%F %T') $CASE ARCHIVEE ${SZ} Mo" >> "$MON"
      continue
    fi
    ALL_DONE=0
    N=$(count_alive "$CASE")
    if [ "$N" -ge 1 ]; then
      echo "$(date '+%F %T') $CASE VIVANT x$N | $(last_line "$CASE")" >> "$MON"
    else
      if [ "$HEAL_USED" -lt "$MAX_HEAL" ]; then
        HEAL_USED=$((HEAL_USED + 1))
        echo "$(date '+%F %T') $CASE MORT -> relance ($HEAL_USED/$MAX_HEAL) | $(last_line "$CASE")" >> "$MON"
        heal "$CASE"
      else
        echo "$(date '+%F %T') $CASE MORT -> budget de relance epuise, ne rien faire" >> "$MON"
      fi
    fi
  done
  if [ "$ALL_DONE" = 1 ]; then
    echo "$(date '+%F %T') TOUTES LES ARCHIVES PRESENTES -> moniteur s'arrete" >> "$MON"
    exit 0
  fi
  [ "$ONCE" = 1 ] && exit 0
  sleep "$INTERVAL"
done
echo "$(date '+%F %T') fin du budget de surveillance ($CYCLES cycles)" >> "$MON"
