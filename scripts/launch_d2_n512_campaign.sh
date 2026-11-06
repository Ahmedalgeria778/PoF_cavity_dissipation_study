#!/bin/bash
# Campagne D2 a N=512 : B2 -> B3 -> B1 sequentiel, frequence preservee (omega=pi).
#
# Ce script NE TOUCHE PAS les captures N=256 existantes : les sorties sont
# nommees capture_<CASE>_D2_N512.npz (voir out_tag dans le runner).
#
# Protocole (identique a la reference N=256, seule la resolution change) :
#   Re=500, E*=0.25, T_phys=2, omega_1=pi, U_ref=0.05, N=512
#   dt_phys = U_ref/N = 9.7656e-5 ; pas lattice par periode = T/dt = 20480
#   SLOWDOWN = 20480/256 = 80 : un echantillon de la forme d'onde est joue 80 pas,
#            soit UNE DUREE PHYSIQUE DE T/256 = 7.8125e-3, INDEPENDANTE DE N.
#            C'est pour ca que la commande en escalier n'est pas un artefact de
#            resolution : elle est identique a 256 et 512 (mesure : 2.6% de la
#            vitesse de pointe au pire, pour B2 ; energie d'actionneur moyenne
#            inchangee a 1e-16 pres).
#   nu_latt = U_ref*N/Re = 0.0512 a N=512 (0.0256 a N=256) ; la viscosite
#            physique reste nu = nu_latt/(N*U_ref) = 1/Re = 2e-3 aux deux
#            resolutions. Le solveur calcule nu_lbm lui-meme (ligne 181 de
#            lbm_mrt_pinn_validation.py) ; le START de chaque run loggue nu_latt.
#   chauffe : min 15 periodes avant la fenetre de derive, arret quand la derive
#            inter-fenetres sur eps < 2e-3 sur 3 fenetres de 3 periodes, cap 60
#   capture : 32 periodes (justifiee par scripts/justify_capture_window.py :
#            convergence de fenetre <=7e-6, split-half <=2e-6, derive seculaire
#            residuelle 2-3e-5 sur toute la fenetre)
#
# Deux blindages ajoutes le 2026-11-05, apres l'incident de la premiere
# tentative (B1 fige a P20/32 a 17:41, aucun .npz ecrit, 5 h de calcul perdues) :
#  1. plus aucun tube : le launcher redirige TOUT son stdout vers le journal
#     (exec >>). Le blocage mesure etait un print(flush=True) de python sur un
#     pipe que tee ne vidait plus ; sans tee, ce mode de faillite disparait.
#  2. watchdog d'ecriture : si le journal n'a pas bouge depuis STALL secondes
#     (la cadence est ~596 s par periode, la marge est donc forte), le run est
#     tue et relance ; le runner reprend alors sur le checkpoint ecrit en fin de
#     periode, ce qui ne coute qu'une periode au lieu de la branche entiere.
#     La reprise bit a bit est verifiee par scripts/test_checkpoint_resume.py.
#
# Usage :
#   bash scripts/launch_d2_n512_campaign.sh                     # B2 B3 B1
#   bash scripts/launch_d2_n512_campaign.sh --dry-run           # affiche sans lancer
#   bash scripts/launch_d2_n512_campaign.sh --cases "B1 B2 B3"  # ordre different
#   bash scripts/launch_d2_n512_campaign.sh --capture 64        # allonge la capture
#   bash scripts/launch_d2_n512_campaign.sh --allow-other-python
set -eo pipefail
ROOT="C:/Users/user/Documents/Qoder/2026-11-03/2b4d7c2e/PoF_cavity_dissipation_study"
cd "$ROOT"
OUT=results/09_d2_capture
CAPTURE=32
FORCING=hold
DRY=0
CASES="B2 B3 B1"
STALL=1800          # 30 min sans ligne de journal -> run considered gele
MAX_TRIES=4         # tentatives par branche (reprise sur checkpoint)
ALLOW_OTHER=0
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY=1; shift ;;
    --capture) CAPTURE="$2"; shift 2 ;;
    --forcing) FORCING="$2"; shift 2 ;;
    --cases) CASES="$2"; shift 2 ;;
    --stall) STALL="$2"; shift 2 ;;
    --allow-other-python) ALLOW_OTHER=1; shift ;;
    *) echo "option inconnue: $1"; exit 2 ;;
  esac
done
STAMP=$(date +%Y%m%d_%H%M)
CASETAG=$(echo $CASES | tr ' ' '-')
LOG="$OUT/campaign_n512_${FORCING}_c${CAPTURE}_${STAMP}_${CASETAG}_stdout.log"

# --- garde-fou 1 : pas de doublon (un run de la meme campagne deja vivant) ---
if [ "$ALLOW_OTHER" != 1 ] && tasklist //FI "IMAGENAME eq python.exe" 2>/dev/null | grep -q python.exe; then
  echo "ABORT : un processus python est deja vivant."
  echo "Verifiez qu'aucune capture n'est en cours avant de lancer (regle d'orchestration)."
  echo "Si c'est un test legitime (ex. test_checkpoint_resume.py), relancer avec"
  echo "--allow-other-python."
  tasklist //FI "IMAGENAME eq python.exe"
  exit 1
fi

# --- garde-fou 2 : ne jamais ecraser une capture existante ---
for CASE in $CASES; do
  TAG="capture_${CASE}_D2_N512"
  [ "$FORCING" = exact ] && TAG="${TAG}_exact"
  if [ -f "$OUT/${TAG}.npz" ]; then
    echo "SKIP branche $CASE : $OUT/${TAG}.npz existe deja (ne pas ecraser)."
    CASES="${CASES/$CASE/}"
  fi
done
CASES=$(echo $CASES)
if [ -z "$(echo $CASES | tr -d ' ')" ]; then
  echo "Rien a faire : toutes les branches demandees sont deja capturees."
  exit 0
fi

echo "Campagne D2 N=512 | branches='$CASES' | forcing=$FORCING | capture=$CAPTURE periodes"
echo "Simplification temporelle : 20480 pas/periode, SLOWDOWN=80, T_phys=2, omega_1=pi"
echo "Watchdog : gele si aucune ecriture dans le journal pendant ${STALL}s ; max $MAX_TRIES tentatives/branche"
if [ "$DRY" = 1 ]; then
  for CASE in $CASES; do
    echo "DRY: py scripts/run_branch_capture_d2.py --case $CASE --N 512 --forcing $FORCING --capture-periods $CAPTURE"
  done
  exit 0
fi

# --- plus de tube : tout part dans le journal, y compris les echoes ---
mkdir -p "$OUT"
exec >> "$LOG" 2>&1
echo "===== journal demarre $(date '+%F %T') -> $LOG ====="

# Tue le run de cette branche. Les PID visibles par Git Bash ne sont pas les
# PID Windows : on cherche le processus par ligne de commande, pas par $!.
kill_run() {
  powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match 'run_branch_capture_d2\.py --case $1 ' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force -ErrorAction SilentlyContinue }" || true
}

for CASE in $CASES; do
  TAG="capture_${CASE}_D2_N512"
  [ "$FORCING" = exact ] && TAG="${TAG}_exact"
  TRIE=1
  while [ "$TRIE" -le "$MAX_TRIES" ]; do
    echo "===== N=512 branch $CASE tentative $TRIE ($(date '+%F %T')) ====="
    py scripts/run_branch_capture_d2.py \
        --case "$CASE" --N 512 --forcing "$FORCING" \
        --capture-periods "$CAPTURE" &
    CHILD=$!
    (
      while [ ! -f "$OUT/${TAG}.npz" ]; do
        sleep 120
        AGE=$(( $(date +%s) - $(stat -c %Y "$LOG") ))
        if [ "$AGE" -gt "$STALL" ]; then
          echo "===== VEILLE: $CASE sans ecriture depuis ${AGE}s -> arret, reprise sur checkpoint ($(date '+%F %T')) ====="
          kill_run "$CASE"
          break
        fi
      done
    ) &
    WD=$!
    set +e
    wait "$CHILD"
    RC=$?
    set -e
    kill "$WD" 2>/dev/null || true
    wait "$WD" 2>/dev/null || true
    if [ -f "$OUT/${TAG}.npz" ]; then
      echo "===== branche $CASE ARCHIVEE ($(date '+%F %T')) ====="
      break
    fi
    if [ "$RC" -ne 0 ]; then
      echo "===== branche $CASE echouee rc=$RC (tentative $TRIE/$MAX_TRIES) ====="
    else
      echo "===== branche $CASE sortie rc=0 sans archive (tentative $TRIE) ====="
    fi
    TRIE=$((TRIE + 1))
  done
done
echo "===== campagne N=512 terminee ($(date '+%F %T')) ====="
for CASE in $CASES; do
  TAG="capture_${CASE}_D2_N512"
  [ "$FORCING" = exact ] && TAG="${TAG}_exact"
  if [ -f "$OUT/${TAG}.npz" ]; then echo "  $TAG : OK"; else echo "  $TAG : ABSENTE"; fi
done
