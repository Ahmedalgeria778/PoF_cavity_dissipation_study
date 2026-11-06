"""Preflight de la campagne D2 a N=512 : tout verifier avant les heures de calcul.

Ce script ne resout PAS l'ecoulement. Il controle, pour les trois branches,
les invariants du protocole et les deux precautions demandees avant le
lancement :

  P1  les fichiers N=256 ne peuvent pas etre ecrases (nommage explicite) ;
  P2  la commande temporelle sur les 20480 pas : difference hold vs exact,
      et energie d'actionneur correspondante ;
  +   convention spatiale (512 nœuds = linspace(0,1,512), coins a zero),
      invariants physiques (nu_phys = 1/Re aux deux resolutions, omega_1 = pi),
      identite des coefficients spectraux 256 -> 512, memoire et cout estime.

Sortie : un dossier imprimable sur stdout (a joindre a l'audit du script de
lancement). Sortie code 0 = pret, 1 = un controle a echoue.
"""

import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lid_command as L                                    # noqa: E402
import run_branch_capture_d2 as R                          # noqa: E402

RE = R.RE
E_TARGET = R.E_TARGET
U_REF = R.U_REF
T = R.T_PERIOD
N_REF = 256
CASES = ("B1", "B2", "B3")
N512_DIR = "data/lid_series_n512"
N256_DIR = "data/lid_series"

fail = []


def chk(ok, label, detail=""):
    mark = "OK  " if ok else "FAIL"
    print(f"[{mark}] {label} {detail}")
    if not ok:
        fail.append(label)
    return ok


def phys(N):
    nu_latt = U_REF * N / RE
    tau = 3.0 * nu_latt + 0.5
    return nu_latt, tau, nu_latt / (N * U_REF)


print("=" * 74)
print("PROTOCOLE / INVARIANTS PHYSIQUES")
print("=" * 74)
for N in (N_REF, 512):
    steps, slowdown, dt = R.protocol(N)
    nu_latt, tau, nu_phys = phys(N)
    print(f"N={N}: pas/periode={steps} SLOWDOWN={slowdown} dt_phys={dt:.6e}")
    print(f"       T_phys = steps*dt = {steps * dt:.12f}  omega_1 = "
          f"{2 * np.pi / (steps * dt):.9f} (vises 2.0 / pi={np.pi:.9f})")
    print(f"       nu_latt={nu_latt:.6f} tau={tau:.6f} omega_MRT={1/tau:.6f} "
          f"nu_phys={nu_phys:.6e} (1/Re={1/RE:.6e})")
    chk(abs(steps * dt - T) < 1e-12, f"N={N}: T_phys=2 exactement")
    chk(abs(2 * np.pi / (steps * dt) - np.pi) < 1e-9, f"N={N}: omega_1=pi")
    chk(abs(nu_phys - 1.0 / RE) < 1e-15, f"N={N}: nu_phys=1/Re")
    chk(slowdown * L.NT_WAVE == steps, f"N={N}: slowdown entier, pas de reste")

# Mach : U_lid au plus ~1.1 * U_ref sur le profil scale
print()
print("=" * 74)
print("P2  COMMANDE TEMPORELLE SUR LES 20480 PAS : HOLD vs EXACT (N=512)")
print("=" * 74)
rows = {}
for case in CASES:
    p256 = os.path.join(N256_DIR, {
        "B1": "fourier_Re500.npz",
        "B2": "B2_seed5_E025_re500_e0.25.npz",
        "B3": "B3_seed0_E025_re500_e0.25.npz"}[case])
    d = L.load_case(p256, rescale_to=E_TARGET)
    c = d["c"]
    steps, slowdown, dt = R.protocol(512)
    x512 = np.linspace(0.0, 1.0, 512)
    U_exact = L.evaluate(c, x512, np.arange(steps) * dt)
    U_hold = np.repeat(L.evaluate(c, x512,
                                  np.arange(L.NT_WAVE) * (T / L.NT_WAVE)),
                       slowdown, axis=0)
    dmax = float(np.max(np.abs(U_hold - U_exact)))
    peak = float(np.max(np.abs(U_exact)))
    l2 = float(np.sqrt(np.mean((U_hold - U_exact) ** 2)))
    rms = float(np.sqrt(np.mean(U_exact ** 2)))
    e_hold = float(np.mean([np.trapezoid(r ** 2, dx=x512[1] - x512[0])
                            for r in U_hold[::slowdown]]))
    e_exact = float(np.mean([np.trapezoid(r ** 2, dx=x512[1] - x512[0])
                             for r in U_exact[::slowdown]]))
    rows[case] = dict(max_abs_delta=dmax, rel_to_peak=dmax / peak,
                      l2_rel=l2 / rms, peak_lid=peak, rms_lid=rms,
                      E_hold=e_hold, E_exact=e_exact, dE_rel=abs(e_hold - e_exact) / e_exact)
    r = rows[case]
    print(f"{case}: max|U_hold-U_exact|={dmax:.4e} = {100*dmax/peak:.2f}% du pic "
          f"({peak:.4f})  ||D||/||U||={l2/rms:.3e}")
    print(f"     E_act hold={e_hold:.12f} exact={e_exact:.12f} "
          f"dE/E={abs(e_hold-e_exact)/e_exact:.2e}")
    chk(abs(e_hold - E_TARGET) < 1e-9 and abs(e_exact - E_TARGET) < 1e-9,
        f"{case}: E*=0.25 dans les deux modes")
    chk(dmax / peak < 0.05, f"{case}: escalier < 5% du pic")

print()
print("=" * 74)
print("CONVENTION SPATIALE 256 -> 512 ET IDENTITE SPECTRALE")
print("=" * 74)
for case in CASES:
    p256 = os.path.join(N256_DIR, {
        "B1": "fourier_Re500.npz",
        "B2": "B2_seed5_E025_re500_e0.25.npz",
        "B3": "B3_seed0_E025_re500_e0.25.npz"}[case])
    p512 = os.path.join(N512_DIR, {
        "B1": "fourier_Re500_n512.npz",
        "B2": "B2_seed5_E025_re500_e0.25_n512.npz",
        "B3": "B3_seed0_E025_re500_e0.25_n512.npz"}[case])
    if not os.path.exists(p512):
        chk(False, f"{case}: archive 512 presente", f"(manque {p512})")
        continue
    with np.load(p512) as z:
        U512 = np.asarray(z["U_series"], float)
        xg = np.asarray(z["x_grid"], float)
        c512 = np.asarray(z["coeffs"], float)
        e512 = float(z["E_act"])
        resid = float(z["reconstruction_residual"])
    d = L.load_case(p256)
    # L'archive 512 est STOCKEE non scalee (E_act = energie native) ; le runner,
    # lui, re-evalue c256 sur la grille 512 puis scale (build_command). On
    # compare donc les coefficients RAMENES a E*=0.25 des deux cotes.
    s512 = float(np.sqrt(E_TARGET / e512))
    s256 = float(np.sqrt(E_TARGET / d["e_raw"]))
    dc = float(np.max(np.abs(c512 * s512 - d["c"] * s256)))
    xref = np.linspace(0.0, 1.0, 512)
    dx = float(np.max(np.abs(xg - xref)))
    corners = float(np.max(np.abs(U512[:, [0, 511]])))
    U_run, U_play, e_raw_run, scale_run, _p, _c, e_play = \
        R.build_command(case, 512, "hold")
    dU = float(np.max(np.abs(U512 * s512 - U_run)))
    dEraw = abs(e512 - e_raw_run) / e512
    print(f"{case}: U_series{U512.shape} residu={resid:.2e} "
          f"E_act native={e512:.12f} (runner {e_raw_run:.12f}, rel {dEraw:.2e})")
    print(f"     scale archive={s512:.9f} runner={scale_run:.9f} | "
          f"max|c512*s512 - c256*s256|={dc:.2e}")
    print(f"     x=linspace(0,1,512) : {dx:.2e}   coins |U(0,t)|=|U(1,t)|={corners:.2e}  "
          f"max|archive-scale - runner|={dU:.2e}")
    chk(dc < 1e-12, f"{case}: coefficients identiques 256<->512 (a E* normalise)")
    chk(dU < 1e-12, f"{case}: profil 512 du runner = archive 512 scalee")
    chk(dEraw < 1e-12, f"{case}: energie native identique aux deux grilles")
    chk(abs(s512 - s256) < 1e-12, f"{case}: facteur d'echelle independant de N")
    chk(dx < 1e-15, f"{case}: meme convention de coordonnee (linspace(0,1,512))")
    chk(corners < 1e-14, f"{case}: paroi immobile aux coins (profils nuls en x=0,1)")
    chk(abs(float(np.mean(e_play)) - E_TARGET) < 1e-12,
        f"{case}: mean_t int U^2 dx = 0.25 realise sur la grille 512 par le runner")
    chk(U_play.shape == (20480, 512), f"{case}: U_play a la forme (20480, 512)")
    chk(float(np.max(np.abs(U_play - np.repeat(U_run, 80, axis=0)))) == 0.0,
        f"{case}: hold = chaque echantillon joue exactement 80 pas")

print()
print("=" * 74)
print("P1  PROTECTION DES CAPTURES N=256")
print("=" * 74)
for case in CASES:
    ref256 = os.path.join(R.OUTDIR if hasattr(R, "OUTDIR") else "results/09_d2_capture",
                          f"capture_{case}_D2_N256.npz")
    tag512 = R.out_tag(case, 512, "hold")
    print(f"{case}: reference {ref256} existe={os.path.exists(ref256)} ; "
          f"sortie 512 -> {tag512}.npz")
    chk(tag512 != f"capture_{case}_D2_N256", f"{case}: nom 512 distinct du 256")

print()
print("=" * 74)
print("CHARGE ET COUT ESTIMES")
print("=" * 74)
steps, slowdown, dt = R.protocol(512)
f_bytes = 9 * 512 * 512 * 8
play_bytes = steps * 512 * 8
acc_bytes = (2 + 6 * R.N_PHASE) * 512 * 512 * 8
print(f"f (D2Q9,N=512) = {f_bytes/2**20:.1f} MiB ; U_play ({steps},512) = "
      f"{play_bytes/2**20:.1f} MiB ; accumulateurs (mean+8 phases) = {acc_bytes/2**20:.1f} MiB")
print(f"total ~ {(f_bytes+play_bytes+acc_bytes)/2**20:.0f} MiB hors solveur")

bench_path = "results/d2_derived/preflight_bench_n512.json"
if os.path.exists(bench_path):
    with open(bench_path) as fh:
        b = json.load(fh)
    print()
    print("=" * 74)
    print("MESURE REELLE (bench N=512, meme boucle que la capture)")
    print("=" * 74)
    for k, v in b.items():
        sp = v["s_per_step"]
        per = sp * steps
        tot56 = 56 * per
        tot88 = 88 * per
        print(f"{k}: {sp*1e3:.2f} ms/pas -> {per:.1f} s/periode -> "
              f"56P(warm24+cap32) = {tot56/3600:.1f} h ; "
              f"88P(warm24+cap64) = {tot88/3600:.1f} h ; "
              f"3 branches 56P = {3*tot56/3600:.1f} h")
else:
    print("(pas de mesure bench : lancer `py scripts/run_branch_capture_d2.py "
          "--case B2 --N 512 --bench` pour un ETA mesure)")

print()
print("=" * 74)
if fail:
    print(f"PREFLIGHT NON PRET : {len(fail)} controle(s) echoue(s) -> {fail}")
    sys.exit(1)
print("PREFLIGHT PRET : tous les controles passent.")
