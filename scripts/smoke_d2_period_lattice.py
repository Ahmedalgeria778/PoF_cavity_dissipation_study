# -*- coding: utf-8 -*-
"""D2 smoke test : verifier que le LBM recoit bien omega=pi (T_phys=2).

Contexte
--------
La forme d'onde du PINN est definie sur 256 echantillons par periode T_PERIOD=2.
Le driver LBM joue un echantillon par pas lattice. Donc :

    period_lattice_actuel = 256 pas
    dt_phys par pas       = U_ref / N = 0.05 / 256 = 1.953e-4
    T_phys effectif       = 256 * 1.953e-4 = 0.05
    omega_1 effectif      = 2 pi / 0.05   = 40 pi           << FAUX

Correctif D2 : ralentir le playback d'un facteur 40 en maintenant chaque
echantillon pendant 40 pas lattice. Alors :

    period_lattice_D2 = 256 * 40 = 10240 pas
    T_phys_D2         = 10240 * 1.953e-4 = 2.0
    omega_1_D2        = 2 pi / 2         = pi              << CIBLE

Ce script fait un run court a N=256 (7 cycles : 3 warmup + 4 capture) et
mesure le spectre de la vitesse u au point-sonde (x, y) = (N//2, N//2).
Il doit exhiber un pic d'energie a omega = pi, sans harmonique de basse
frequence parasite (le contenu non-lineaire est a 2*omega, 3*omega... mais
tres attenue).

Usage :
    py scripts/smoke_d2_period_lattice.py
"""
import datetime
import os
import sys
import time

import numpy as np

if not hasattr(np, "trapz"):
    np.trapz = np.trapezoid

PAPER2 = os.path.normpath(os.path.join(
    os.path.expanduser("~"),
    "Documents", "travail pc taki_final", "Default Project",
    "papier 2 date_14_09_2026", "Paper2_branch_selection",
))
if not os.path.isdir(PAPER2):
    raise SystemExit(f"Missing paper2 folder: {PAPER2}")
sys.path.insert(0, PAPER2)
from paper_paths import find_lbm  # noqa: E402

LBM_DIR = find_lbm()
sys.path.insert(0, LBM_DIR)
sys.path.insert(0, os.path.dirname(LBM_DIR))

from lbm_mrt_pinn_validation import (  # noqa: E402
    LBM_MRT_Solver, mrt_step, M, M_INV, EX, EY, W, OPP,
)

RE = 500
N = 256
NT_WAVE = 256          # echantillons de la forme d'onde PINN par periode
SLOWDOWN = 40          # un echantillon joue SLOWDOWN pas lattice
PERIOD_LATTICE = NT_WAVE * SLOWDOWN           # = 10240
U_REF = 0.05
DT_PHYS = U_REF / N                           # = 1.953e-4
T_PHYS_PERIOD = PERIOD_LATTICE * DT_PHYS      # = 2.0
OMEGA_TARGET = 2.0 * np.pi / T_PHYS_PERIOD    # = pi

WARMUP_PERIODS = 3
CAPTURE_PERIODS = 4
N_WARM = WARMUP_PERIODS * PERIOD_LATTICE      # 30720
N_CAP = CAPTURE_PERIODS * PERIOD_LATTICE      # 40960

CASE_STUDY = os.path.join(os.path.dirname(PAPER2),
                          "paper_2_case_study_15_09_2026")
LID_DIR = os.path.join(CASE_STUDY, "data", "lid_series")
# B1 waveform = PINN fourier, exporte par make_pinn_lid_series.py a cote du solver LBM
P1_SERIES = os.path.join(LBM_DIR, "lid_series")

OUTROOT = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".."))
OUTDIR = os.path.join(OUTROOT, "results", "07_d2_smoke")
os.makedirs(OUTDIR, exist_ok=True)
LOG = os.path.join(OUTDIR, "smoke_d2.log")


def log(msg):
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def load_B1_hold():
    path = os.path.join(P1_SERIES, "fourier_Re500.npz")
    if not os.path.exists(path):
        path = os.path.join(LID_DIR, "fourier_Re500.npz")
    with np.load(path) as z:
        U = np.asarray(z["U_series"], dtype=np.float64)   # (256, 256)
        nt_per = int(z["NT_PER"])
        t_per = float(z["T_PERIOD"])
    log(f"B1 waveform loaded : {path}  shape={U.shape}  "
        f"NT_PER={nt_per}  T_PERIOD={t_per}")
    # hold-each-sample : (256, N) -> (10240, N)
    U_hold = np.repeat(U, SLOWDOWN, axis=0)
    assert U_hold.shape == (PERIOD_LATTICE, N), U_hold.shape
    return U_hold, path


def fft_dominant_omega(series, dt):
    n = len(series)
    x = series - series.mean()
    win = np.hanning(n)
    Xf = np.fft.rfft(x * win)
    freqs_hz = np.fft.rfftfreq(n, d=dt)      # cycles per physical time
    omega = 2.0 * np.pi * freqs_hz
    mag = np.abs(Xf)
    # exclure DC (omega=0)
    mag[0] = 0.0
    peak_bin = int(np.argmax(mag))
    peak_omega = omega[peak_bin]
    total = np.sum(mag ** 2)
    peak_frac = (mag[peak_bin] ** 2) / total
    top = np.argsort(mag)[::-1][:5]
    return peak_omega, peak_frac, omega[top], mag[top] / mag[peak_bin]


def main():
    log("=" * 72)
    log(f"D2 smoke : N={N}  period_lattice={PERIOD_LATTICE}  "
        f"dt_phys={DT_PHYS:.6e}  T_phys={T_PHYS_PERIOD:.4f}  "
        f"omega_cible={OMEGA_TARGET:.6f} (= pi)")
    log("=" * 72)

    U_hold, path = load_B1_hold()

    solver = LBM_MRT_Solver(RE, N, lid_profile="uniform", max_iter=1000)
    solver.U_lid_norm = np.ascontiguousarray(U_hold, dtype=np.float64)
    solver.period = PERIOD_LATTICE
    solver.U_lid2d = solver.U_ref * solver.U_lid_norm
    U_lid2d, S_diag = solver.U_lid2d, solver.S_diag
    U_ref = solver.U_ref

    log(f"solver  U_ref={U_ref}  nu_lbm={solver.nu_lbm:.6f}  tau={solver.tau:.6f}  "
        f"omega_relax={solver.omega:.6f}")

    t0 = time.time()
    f = solver.f.copy()
    it = 0
    probe_u = np.zeros(N_WARM + N_CAP, dtype=np.float64)
    probe_v = np.zeros(N_WARM + N_CAP, dtype=np.float64)
    lid_u = np.zeros(N_CAP, dtype=np.float64)
    xp = N // 2
    yp = N // 2

    # warmup (3 cycles = 30720 pas)
    for k in range(N_WARM):
        t_idx = it % PERIOD_LATTICE
        f, rho, ux, uy = mrt_step(f, M, M_INV, S_diag, EX, EY, W,
                                  U_lid2d, t_idx, N, OPP)
        probe_u[k] = ux[xp, yp] / U_ref
        probe_v[k] = uy[xp, yp] / U_ref
        it += 1
        if (k + 1) % PERIOD_LATTICE == 0:
            log(f"  warmup {(k + 1) // PERIOD_LATTICE}/{WARMUP_PERIODS} P "
                f"({time.time() - t0:.0f}s)  u_probe={probe_u[k]:.4f}")

    # capture (4 cycles = 40960 pas)
    for k in range(N_CAP):
        t_idx = it % PERIOD_LATTICE
        f, rho, ux, uy = mrt_step(f, M, M_INV, S_diag, EX, EY, W,
                                  U_lid2d, t_idx, N, OPP)
        probe_u[N_WARM + k] = ux[xp, yp] / U_ref
        probe_v[N_WARM + k] = uy[xp, yp] / U_ref
        lid_u[k] = ux[N - 1, xp] / U_ref
        it += 1
        if (k + 1) % PERIOD_LATTICE == 0:
            log(f"  capture {(k + 1) // PERIOD_LATTICE}/{CAPTURE_PERIODS} P "
                f"({time.time() - t0:.0f}s)")

    capture_u = probe_u[N_WARM:]
    capture_v = probe_v[N_WARM:]

    omega_u, frac_u, top_omega, top_rel = fft_dominant_omega(capture_u, DT_PHYS)
    omega_v, frac_v, _, _ = fft_dominant_omega(capture_v, DT_PHYS)
    omega_lid, frac_lid, _, _ = fft_dominant_omega(lid_u, DT_PHYS)

    log("-" * 72)
    log(f"FFT probe u : omega_peak={omega_u:.6f}   (cible pi = {np.pi:.6f})   "
        f"energy fraction={frac_u:.4f}")
    log(f"  top-4 pics omega = {', '.join(f'{o:.4f}' for o in top_omega[:4])} "
        f" (rel = {', '.join(f'{r:.3f}' for r in top_rel[:4])})")
    log(f"FFT probe v : omega_peak={omega_v:.6f}   energy fraction={frac_v:.4f}")
    log(f"FFT lid_u(x=N/2) : omega_peak={omega_lid:.6f}  frac={frac_lid:.4f}")
    log(f"  ratio omega_u / pi = {omega_u / np.pi:.4f}   "
        f"ratio omega_u / (40 pi) = {omega_u / (40 * np.pi):.4f}")
    ok = abs(omega_u - np.pi) < 0.05 * np.pi
    log(f"VERDICT omega=pi : {'PASS' if ok else 'FAIL'} "
        f"(|omega_meas - pi| / pi = {abs(omega_u - np.pi) / np.pi:.3f})")

    out = os.path.join(OUTDIR, "smoke_d2.npz")
    np.savez(out,
             probe_u=capture_u, probe_v=capture_v, lid_u=lid_u,
             dt_phys=DT_PHYS, omega_target=OMEGA_TARGET,
             omega_probe_u=omega_u, energy_frac_u=frac_u,
             omega_probe_v=omega_v, energy_frac_v=frac_v,
             N=N, RE=RE, period_lattice=PERIOD_LATTICE,
             warmup_periods=WARMUP_PERIODS, capture_periods=CAPTURE_PERIODS,
             slowdown=SLOWDOWN, waveform_file=path,
             lid_file=os.path.basename(path))
    log(f"  -> {out}")


if __name__ == "__main__":
    main()
