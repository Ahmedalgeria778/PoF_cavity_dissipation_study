# -*- coding: utf-8 -*-
"""Construit les series de lid a 512 noeuds pour la verification de resolution D2.

Pas d'interpolation : les archives 256 noeuds sont exactement representables
sur la base
    sin((i+1) pi x) cos(j pi t),  i=0..5, j=0..4
a la precision machine (residu <= 1.5e-15 mesure), donc la serie a 512 noeuds
est la MEME fonction continue evaluee sur x = j/(512-1). La convention
d'espace reste celle du solveur : x in [0,1] avec les parois laterales sur les
nœuds extremes, i.e. np.linspace(0,1,N) ; le lid est la rangee i=N-1 et
l'abscisse du profil est l'indice j.

Grille temporelle inchangee : 256 echantillons sur T=2, endpoint=False. La
finesse temporelle du solveur ne vient pas du nombre d'echantillons mais du
nombre de pas lattice par periode (SLOWDOWN).

Sorties : data/lid_series_n512/<stem>_n512.npz avec U_series (256,512),
U_mean, coefficients c (6,5), grilles, et l'energie d'actioneur mesuree aux deux
resolutions (elle doit coincidence : la regle periodique sur une serie
bande-limitee est exacte).

Usage : py scripts/build_lid_series_n512.py
"""
import json
import os

import numpy as np

import lid_command as L

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SRC = os.path.join(ROOT, "data", "lid_series")
DST = os.path.join(ROOT, "data", "lid_series_n512")

CASES = {
    "B1": "fourier_Re500.npz",
    "B2": "B2_seed5_E025_re500_e0.25.npz",
    "B3": "B3_seed0_E025_re500_e0.25.npz",
}
N_TARGET = 512


def main():
    os.makedirs(DST, exist_ok=True)
    report = {}
    for case, fname in CASES.items():
        path = os.path.join(SRC, fname)
        d = L.load_case(path)                       # verifie le residu < 1e-9
        c = d["c"]
        x512 = np.linspace(0.0, 1.0, N_TARGET)      # memes parois, meme convention
        t = d["t"]
        U512 = L.evaluate(c, x512, t)
        e512 = L.actuation_energy(U512, x512)
        e256 = d["e_raw"]
        # auto-controle : re-projection de la serie 512 doit rendre les c_ij
        c_back, resid_back = L.coefficients_from_series(U512, x512, t)
        d_coef = float(np.max(np.abs(c - c_back)))
        resid_512 = float(resid_back)
        # NOTE : np.linspace(0,1,256) et (0,1,512) ne sont pas emboitees
        # (1/255 != 2/511) ; la coherence entre resolutions se verifie donc sur
        # les coefficients, pas sur des nœuds communs.
        out = os.path.join(DST, fname.replace(".npz", "_n512.npz"))
        np.savez(
            out,
            U_series=U512,
            U_mean=U512.mean(axis=0),
            coeffs=c,
            N=N_TARGET,
            NT_PER=L.NT_WAVE,
            T_PERIOD=L.T_PERIOD,
            t_grid=t,
            x_grid=x512,
            E_act=e512,
            E_act_source_256=e256,
            source=os.path.basename(path),
            reconstruction_residual=d["resid"],
            roundtrip_coeff_residual=d_coef,
            residual_512=resid_512,
            max_abs=float(np.max(np.abs(U512))),
        )
        report[case] = dict(
            file=os.path.basename(out), source=os.path.basename(path),
            resid_256=d["resid"], resid_512=resid_512,
            E_256=e256, E_512=e512, dE_rel=(e512 - e256) / e256,
            scale_needed_256=(0.25 / e256) ** 0.5,
            scale_needed_512=(0.25 / e512) ** 0.5,
            roundtrip_coeff_residual=d_coef,
            max_abs_256=float(np.max(np.abs(d["U"]))),
            max_abs_512=float(np.max(np.abs(U512))),
        )
        print(f"{case}: {os.path.basename(out)}")
        print(f"   residu projection : 256 -> {d['resid']:.2e}   "
              f"512 -> {resid_512:.2e}")
        print(f"   E_act 256 = {e256:.12f}   E_act 512 = {e512:.12f}"
              f"   dE/E = {(e512 - e256) / e256:.2e}")
        print(f"   scale pour E*=0.25 : 256 -> {report[case]['scale_needed_256']:.9f}"
              f"   512 -> {report[case]['scale_needed_512']:.9f}")
        print(f"   re-projection 512 : max|c-c_back| = {d_coef:.2e}")
        print(f"   max|U| : 256 -> {report[case]['max_abs_256']:.6f}   "
              f"512 -> {report[case]['max_abs_512']:.6f}")
        print()
    with open(os.path.join(DST, "build_report_n512.json"), "w",
              encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, sort_keys=True)
    print("->", os.path.join(DST, "build_report_n512.json"))


if __name__ == "__main__":
    main()
