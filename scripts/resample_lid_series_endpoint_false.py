# -*- coding: utf-8 -*-
"""Régénère les npz B1/B2/B3 sur la grille temporelle périodique correcte.

Problème : make_pinn_lid_series.py et build_controls.py utilisaient
    ts = torch.linspace(0, T_PERIOD, nt)
qui INCLUT la borne t=T_PERIOD. U_lid(t=2) = U_lid(t=0) exactement, donc le
256e échantillon recopie le 1er et le cycle physique est échantillonné sur 255
intervalles au lieu de 256. Le LBM joue chaque échantillon pour un pas lattice,
donc le dernier intervalle est légèrement "stretché" et la moyenne cyclique
des modes cos(jπt) porte un biais DC de l'ordre de 4e-3 relatif.

Correctif :
    ts = arange(nt) * (T_PERIOD / nt)

Comme U_lid est une somme finie Σ_{i,j} c_ij sin((i+1)πx) cos(jπt) et que la
projection de l'npz endpoint=True sur cette base reproduit c_ij à la précision
machine, on évite torch :
    1. charger l'npz original (256x256, endpoint=True)
    2. recouvrer les 30 c_ij (N_MX=6, N_MT=5) par projection trapèze
    3. vérifier ||U_old - Σ c_ij φ_ij||_inf < tol_reconstruction
    4. reconstruire U_new sur la grille arange(256) * 2/256
    5. ré-écrire l'npz à côté (<stem>_v2.npz), sans écraser l'original

Utiliser --apply pour écraser en place l'original (après backup).
"""
import argparse
import json
import os
import shutil
import sys

import numpy as np

if not hasattr(np, "trapz"):
    np.trapz = np.trapezoid

N_MX = 6
N_MT = 5
N_LBM = 256
NT_PER = 256
T_PERIOD = 2.0
E_TARGET = 0.25


def project_coefficients(U_series, x, t_old):
    """Récupère les c_ij par projection trapèze sur la base sin((i+1)πx)·cos(jπt).

    U_series : (nt, nx), échantillonné sur t_old ∈ [0, T_PERIOD] (endpoint inclus).
    Retourne c (n_mx, n_mt) et le résidu max de la reconstruction.
    """
    nt, nx = U_series.shape
    dx = x[1] - x[0]
    dt = t_old[1] - t_old[0]
    wx = np.ones(nx); wx[0] = wx[-1] = 0.5
    wt = np.ones(nt); wt[0] = wt[-1] = 0.5
    W = np.outer(wt, wx) * dx * dt

    sx = np.array([np.sin((i + 1) * np.pi * x) for i in range(N_MX)])          # (n_mx, nx)
    cj = np.array([np.cos(j * np.pi * t_old) for j in range(N_MT)])            # (n_mt, nt)

    c = np.zeros((N_MX, N_MT))
    U_rec = np.zeros_like(U_series)
    for i in range(N_MX):
        for j in range(N_MT):
            outer = np.outer(cj[j], sx[i])                                     # (nt, nx)
            norm2 = float(np.sum(W * outer ** 2)) + 1e-30
            cij = float(np.sum(W * U_series * outer) / norm2)
            c[i, j] = cij
            U_rec += cij * outer
    resid = float(np.max(np.abs(U_series - U_rec)))
    return c, resid


def reconstruct(c, x, t_new):
    nt = len(t_new)
    sx = np.array([np.sin((i + 1) * np.pi * x) for i in range(N_MX)])
    cj = np.array([np.cos(j * np.pi * t_new) for j in range(N_MT)])
    U = np.zeros((nt, len(x)))
    for i in range(N_MX):
        for j in range(N_MT):
            if c[i, j] != 0.0:
                U += c[i, j] * np.outer(cj[j], sx[i])
    return U


def energy_of(series, x, t):
    nt, nx = series.shape
    dx = x[1] - x[0]
    dt = t[1] - t[0]
    wx = np.ones(nx); wx[0] = wx[-1] = 0.5
    wt = np.ones(nt); wt[0] = wt[-1] = 0.5
    W = np.outer(wt, wx) * dx * dt
    # Moyenne temporelle de la norme spatiale ∫U(x,t)² dx, comme dans les drivers LBM
    e_per_t = np.array([np.trapz(row ** 2, dx=dx) for row in series])
    return float(np.mean(e_per_t)), float(np.sum(W * series ** 2) / (T_PERIOD * 1.0))


def modal_fractions(c):
    """f_2 = fraction d'énergie du mode spatial (i=1) tous j confondus.
       f_t = fraction d'énergie des modes temporels j >= 1.
       Norme modale : E_ij = c_ij² * ||φ_ij||² où ||sin((i+1)πx)||² = 1/2
       et ||cos(jπt)||² = 1 sur j=0, = 1/2 sur j>=1 (intégrale sur [0,1]).
    On suit la convention de analyze_control (norme sur [0, T_MAX=1]).
    """
    w_j = np.ones(N_MT); w_j[1:] = 0.5   # ∫ cos²(jπt) dt sur [0,1]
    w_i = 0.5 * np.ones(N_MX)             # ∫ sin²((i+1)πx) dx sur [0,1]
    E = (c ** 2) * w_i[:, None] * w_j[None, :]
    E_tot = E.sum()
    f_2 = E[1, :].sum() / E_tot
    f_t = E[:, 1:].sum() / E_tot
    return f_2, f_t, E_tot


def resample(path_in, path_out, tol=1e-9, apply=False):
    with np.load(path_in) as z:
        U_old = np.asarray(z["U_series"], dtype=np.float64)
        NT = int(z["NT_PER"])
        Tp = float(z["T_PERIOD"])
        keys = list(z.keys())
        extras = {k: z[k] for k in keys if k not in ("U_series", "U_mean", "E_mean", "E_measured")}
    if U_old.shape[1] != N_LBM or NT != NT_PER:
        raise SystemExit(f"{path_in} : shape {U_old.shape} NT={NT}, attendu ({NT_PER},{N_LBM})")
    x = np.linspace(0.0, 1.0, N_LBM)
    t_old = np.linspace(0.0, Tp, NT)                 # endpoint inclus
    t_new = np.arange(NT) * (Tp / NT)                # endpoint exclus
    c, resid = project_coefficients(U_old, x, t_old)
    U_new = reconstruct(c, x, t_new)

    e_old_x_t, e_old_trapz = energy_of(U_old, x, t_old)
    e_new_x_t, e_new_trapz = energy_of(U_new, x, t_new)
    f2, ft, Etot = modal_fractions(c)

    print(f"{os.path.basename(path_in)}")
    print(f"  max|U_old - sum c_ij phi_ij| = {resid:.2e}   tol={tol:.0e}")
    if resid > tol:
        raise SystemExit("  RECONSTRUCTION TROP IMPRECISE - base sin*cos non suffisante")
    print(f"  E_act(old, int U^2 dx moyen t) = {e_old_x_t:.6f}   E_act(new) = {e_new_x_t:.6f}")
    print(f"  E_act(old, trapz 2D / T)        = {e_old_trapz:.6f}   E_act(new) = {e_new_trapz:.6f}")
    print(f"  f_2 (mode spatial 2) = {f2:.6f}   f_t (modes temporels) = {ft:.6f}")
    print(f"  max|U_old| = {np.abs(U_old).max():.6f}   max|U_new| = {np.abs(U_new).max():.6f}")
    print(f"  U_new vs U_old : max|diff| = {np.max(np.abs(U_new - U_old)):.3e}")
    print(f"  U_old[0] vs U_old[-1] (0 attendu, endpoint=True)  : "
          f"{np.max(np.abs(U_old[0] - U_old[-1])):.2e}")
    print(f"  U_new[0] vs U_new[-1] (non-nul attendu, cycle propre) : "
          f"{np.max(np.abs(U_new[0] - U_new[-1])):.3e}")

    if apply:
        shutil.copy2(path_in, path_in + ".bak")
    out = path_in if apply else path_out
    np.savez(out, U_series=U_new, U_mean=U_new.mean(axis=0), **extras)
    if apply:
        print(f"  OVERWRITE -> {out} (backup .bak)")
    else:
        print(f"  -> {out}")
    return c, resid, e_new_x_t


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="écraser l'npz original (après backup .bak)")
    args = ap.parse_args()

    P1 = "C:/Users/user/Documents/travail pc taki_final/Default Project/PoF_R_lid_driven_paper/lbm_mrt_validation/lid_series"
    CS = "C:/Users/user/Documents/travail pc taki_final/Default Project/papier 2 date_14_09_2026/paper_2_case_study_15_09_2026/data/lid_series"
    files = [
        ("B1", os.path.join(P1, "fourier_Re500.npz")),
        ("B2", os.path.join(CS, "B2_seed5_E025_re500_e0.25.npz")),
        ("B3", os.path.join(CS, "B3_seed0_E025_re500_e0.25.npz")),
    ]
    for tag, path in files:
        if not os.path.exists(path):
            print(f"MISSING {tag}: {path}")
            continue
        stem, ext = os.path.splitext(path)
        out = stem + "_v2" + ext
        resample(path, out, tol=1e-9, apply=args.apply)
        print()


if __name__ == "__main__":
    main()
