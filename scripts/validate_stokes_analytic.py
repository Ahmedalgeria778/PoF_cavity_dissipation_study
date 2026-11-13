# -*- coding: utf-8 -*-
"""Validation de la couche limite de Stokes temporelle (D2).

Excitation analytique pure (pas de PINN) :

    U_wall(x, t) = A sin(2 pi x) cos(pi t),  A = 1  ->  E_act = 0.25

Analytique (second probleme, demi-espace) :

    delta = sqrt(2 nu / omega),  omega = pi,  nu = 1/Re = 2e-3
    delta_phys = 3.5682e-2 ;  en cellules : delta * (N-1) = 9.10 (N=256), 18.27 (N=512)

Protocole derive (identique a celui de la campagne D2) :

    U_ref = 0.05 (unites lattice), dt_phys = U_ref / N,
    SLOWDOWN = N / 6.4, period_lattice = 256 * SLOWDOWN = 40 N,
    T_phys = period_lattice * dt_phys = 2.0 exactement, donc omega = pi a tout N.

Usage :
    py scripts/validate_stokes_analytic.py --N 256            # archive deja committee
    py scripts/validate_stokes_analytic.py --N 512            # test de resolution
    py scripts/validate_stokes_analytic.py --N 512 --bench    # seul, 300 pas, chronometre

Sorties : results/08_stokes_analytic/stokes_analytic[_nN].npz et .log
A N=256 le nom de fichier et le protocole restent ceux de l'archive de reference ;
les autres resolutions ecrivent un fichier distinct et ne l'ecrasent pas.
"""
import argparse
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
sys.path.insert(0, PAPER2)
from paper_paths import find_lbm  # noqa: E402

LBM_DIR = find_lbm()
sys.path.insert(0, LBM_DIR)
sys.path.insert(0, os.path.dirname(LBM_DIR))

from lbm_mrt_pinn_validation import (  # noqa: E402
    LBM_MRT_Solver, mrt_step, M, M_INV, EX, EY, W, OPP,
)

RE = 500
NT_WAVE = 256
U_REF = 0.05
NU_PHYS = 1.0 / RE
OMEGA = np.pi                       # vise, et obtenu exactement pour tout N
DELTA_TH = np.sqrt(2.0 * NU_PHYS / OMEGA)   # 3.5682e-2, independant de N

OUTROOT = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), ".."))
OUTDIR = os.path.join(OUTROOT, "results", "08_stokes_analytic")
os.makedirs(OUTDIR, exist_ok=True)

# Fenetres d'ajustement, en cellules depuis la rangee du couvercle.
# 'protocol' = la fenetre qui a produit l'archive de reference (s = 1..11).
WINDOWS = [("protocol", 1, 12), ("s=1..23", 1, 24), ("s=1..47", 1, 48),
           ("s=2..11", 2, 12), ("phys 0.2-0.8 delta", None, None)]


class Log:
    def __init__(self, path):
        self.path = path

    def __call__(self, msg):
        stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"[{stamp}] {msg}"
        print(line, flush=True)
        with open(self.path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")


def protocol(N):
    """Derives the lattice protocol so that T_phys = 2 and omega = pi at any N."""
    slowdown = int(round(N / 6.4))
    period = NT_WAVE * slowdown                     # = 40 N
    dt_phys = U_REF / N
    assert abs(period * dt_phys - 2.0) < 1e-12, "T_phys != 2"
    assert abs(2.0 * np.pi / (period * dt_phys) - OMEGA) < 1e-12
    return slowdown, period, dt_phys


def amp_at_omega(series_col, dt, omega):
    """Single-sided amplitude at `omega` of each column of a (n_t, n_y) record."""
    n_t = series_col.shape[0]
    freqs = np.fft.rfftfreq(n_t, d=dt)
    omega_grid = 2.0 * np.pi * freqs
    bin_idx = int(np.round(omega / (omega_grid[1] - omega_grid[0])))
    if bin_idx >= len(omega_grid):
        raise RuntimeError("omega au-dela de Nyquist")
    win = np.hanning(n_t)
    X = np.fft.rfft(series_col * win[:, None], axis=0)
    A = 2.0 * np.abs(X[bin_idx]) / win.sum()        # gain coherent de Hann = 1/2
    # part de l'energie du signal totalise sur les colonnes qui porte la raie cible
    P_line = float(np.sum(np.abs(X[bin_idx]) ** 2))
    tot = float(np.sum(np.abs(X) ** 2))
    return A, omega_grid[bin_idx], P_line / tot


def fit_decay(prof, N, fit_lo, fit_hi):
    """Decay length from the lid row; `prof` is already ordered from the lid."""
    hi = min(fit_hi, len(prof))
    s = np.arange(len(prof), dtype=float)[fit_lo:hi]
    log_A = np.log(np.maximum(prof[fit_lo:hi], 1e-12))
    slope, intercept = np.polyfit(s, log_A, 1)
    r2 = float(np.corrcoef(s, log_A)[0, 1] ** 2)
    delta_cells = -1.0 / slope if slope < 0 else np.nan
    dx = 1.0 / (N - 1)
    return float(delta_cells * dx), float(delta_cells), float(slope), \
        float(intercept), r2, int(len(s))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--N", type=int, default=256, choices=(256, 512))
    ap.add_argument("--amp", type=float, default=1.0,
                    help="imposed lid amplitude; <1 probes the linear Stokes limit")
    ap.add_argument("--warm", type=int, default=3)
    ap.add_argument("--capture", type=int, default=4)
    ap.add_argument("--bench", type=int, default=0,
                    help="run only this many lattice steps, then stop")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)

    N = args.N
    slowdown, PERIOD, DT_PHYS = protocol(N)
    dx = 1.0 / (N - 1)
    DELTA_TH_CELLS = DELTA_TH / dx                  # 9.10 a 256, 18.27 a 512
    suffix = ("_n%d" % N if N != 256 else "")
    if args.amp != 1.0:
        suffix += "_a%g" % args.amp
    out_npz = os.path.join(OUTDIR, "stokes_analytic%s.npz" % suffix)
    log = Log(os.path.join(OUTDIR, "stokes_analytic%s.log" % suffix))

    if os.path.isfile(out_npz) and not args.force and not args.bench:
        raise SystemExit("%s existe deja (utiliser --force pour ecraser)" % out_npz)

    log("=" * 72)
    log(f"Stokes analytic validation : N={N}  amp={args.amp}  "
        f"omega={OMEGA:.6f}  "
        f"slowdown={slowdown}  period_lattice={PERIOD}  dt_phys={DT_PHYS:.6e}")
    log(f"  T_phys={PERIOD * DT_PHYS:.6f}  nu_latt={U_REF * N / RE:.6f}  "
        f"dx={dx:.6e}")
    log(f"  delta_theory = {DELTA_TH:.6f} phys = {DELTA_TH_CELLS:.2f} cells "
        f"(delta*N = {DELTA_TH * N:.2f})")
    log(f"  protocole : warmup {args.warm} P + capture {args.capture} P")

    n_warm = args.warm * PERIOD
    n_cap = args.capture * PERIOD

    t = np.arange(PERIOD) * DT_PHYS
    x = np.linspace(0.0, 1.0, N)
    U_wave = args.amp * np.outer(np.cos(OMEGA * t), np.sin(2.0 * np.pi * x))
    e_act = np.array([np.trapz(row ** 2, dx=dx) for row in U_wave])
    log(f"  waveform shape={U_wave.shape}  E_act_cycle_mean={e_act.mean():.6f}  "
        f"max|U|={np.max(np.abs(U_wave)):.6f}")

    solver = LBM_MRT_Solver(RE, N, lid_profile="uniform", max_iter=1000)
    solver.U_lid_norm = np.ascontiguousarray(U_wave, dtype=np.float64)
    solver.period = PERIOD
    solver.U_lid2d = solver.U_ref * solver.U_lid_norm
    U_lid2d, S_diag = solver.U_lid2d, solver.S_diag

    xp = N // 4
    log(f"  x_probe = {xp}, sin(2 pi x_probe) = "
        f"{np.sin(2 * np.pi * xp / (N - 1)):.6f}")

    f = solver.f.copy()
    it = 0
    t0 = time.time()
    u_rec = np.zeros((n_cap, N), dtype=np.float64)
    mean_col = np.zeros(N)
    per_period = []

    total = (args.bench or (n_warm + n_cap))
    for k in range(total):
        t_idx = it % PERIOD
        f, rho, ux, uy = mrt_step(f, M, M_INV, S_diag, EX, EY, W,
                                  U_lid2d, t_idx, N, OPP)
        if n_warm <= k < n_warm + n_cap:
            u_rec[k - n_warm] = ux[:, xp] / U_REF
            mean_col += ux[:, xp] / U_REF
        it += 1
        if (k + 1) % PERIOD == 0:
            n_p = (k + 1) // PERIOD
            phase = "warmup" if k < n_warm else "capture"
            log(f"  {phase} {n_p} ({time.time() - t0:.0f}s)")
            if phase == "capture":
                m = k + 1 - n_warm
                a, _, _ = amp_at_omega(u_rec[:m], DT_PHYS, OMEGA)
                pp = a[::-1]
                per_period.append((n_p, float(pp[0] / args.amp),
                                   float(pp[min(11, N - 1)] / pp[0])))

    if args.bench:
        dt = (time.time() - t0) / args.bench
        log(f"  bench : {dt * 1000:.2f} ms/pas -> "
            f"{(n_warm + n_cap) * dt / 60:.1f} min pour le run complet")
        return

    u_col = u_rec
    mean_col /= n_cap
    A_profile, omega_meas, frac_line = amp_at_omega(u_col, DT_PHYS, OMEGA)
    prof = A_profile[::-1]                          # 0 = rangee du couvercle

    log("-" * 72)
    log(f"  omega_meas = {omega_meas:.6f} (cible {OMEGA:.6f}, "
        f"rapport {omega_meas / OMEGA:.6f})")
    log(f"  A(lid) = {prof[0]:.4f} / imposee {args.amp:.4f}  "
        f"=> offset du noeud = {100 * (1 - prof[0] / args.amp):.2f} %   "
        f"fraction d'energie dans la raie = {100 * frac_line:.1f} %")
    log(f"  A(s=1)={prof[1]:.4e}  A(s=5)={prof[5]:.4e}  A(s=10)={prof[10]:.4e}  "
        f"A(s=20)={prof[20]:.4e}  A(s=40)={prof[40]:.4e}")
    log("  par periode capturee (n, A_lid/ampl, A(11)/A(0)) : "
        + ", ".join("%.4f/%.4f/%.3f" % p for p in per_period))

    fits = []
    log("  fit log A vs s (delta en cellules depuis le couvercle) :")
    for name, lo, hi in WINDOWS:
        if lo is None:                       # fenetre proportionnelle a l'epaisseur theorique
            lo = max(2, int(round(0.2 * DELTA_TH_CELLS)))
            hi = max(lo + 3, int(round(0.8 * DELTA_TH_CELLS)))
        label = "%s (s=%d..%d)" % (name, lo, hi - 1)
        d_phys, d_cells, slope, inter, r2, npts = fit_decay(prof, N, lo, hi)
        fits.append((label, lo, hi - 1, d_cells, d_phys, slope, r2, npts))
        log(f"    {label:34s} delta = {d_cells:6.2f} cells = {d_phys:.5f} "
            f"measured/theory = {d_cells / DELTA_TH_CELLS:.3f}  R2={r2:.5f}")

    # cisaillement moyen pres du couvercle : l'hypothese d'amincissement par
    # le retour permanent, quantifiee et non invoquee.
    g = np.gradient(mean_col, dx)
    shear = float(-g[::-1][1])
    log(f"  champ moyen (cycle) a la sonde : U_mean(lid)={mean_col[-1]:.4f}, "
        f"gradient pres du couvercle = {shear:.4f} / unite de longueur")
    log(f"  echelle de cisaillement vs pulsation : |dU/dy|/omega = "
        f"{abs(shear) / OMEGA:.3f} (comparaison indicative, pas un critere)")

    np.savez(out_npz, A_profile=A_profile, A_from_lid=prof,
             mean_profile=mean_col, shear_near_lid=shear,
             omega=OMEGA, omega_meas=omega_meas, line_fraction=frac_line,
             delta_theory=DELTA_TH, delta_cells_theory=DELTA_TH_CELLS,
             dt_phys=DT_PHYS, period_lattice=PERIOD, slowdown=slowdown,
             x_probe=xp, N=N, RE=RE, amp=args.amp,
             lid_node_offset=1.0 - prof[0] / args.amp, warmup_periods=args.warm,
             capture_periods=args.capture,
             per_period=np.array(per_period),
             fit_label=np.array([f[0] for f in fits]),
             fit_lo=np.array([f[1] for f in fits]),
             fit_hi=np.array([f[2] for f in fits]),
             fit_delta_cells=np.array([f[3] for f in fits]),
             fit_delta_phys=np.array([f[4] for f in fits]),
             fit_r2=np.array([f[6] for f in fits]))
    log(f"  -> {out_npz}")


if __name__ == "__main__":
    main()
