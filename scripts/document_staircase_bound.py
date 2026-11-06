# -*- coding: utf-8 -*-
"""Documente numeriquement le defaut d'echantillon-maintenu (commande « en escalier »).

Pour chaque branche et chaque resolution, compare la commande jouee par le
solveur (chaque echantillon maintenu SLOWDOWN pas) a la commande temps-exacte
evaluee pas a pas depuis les coefficients c_ij, et ecrit le resultat dans
results/d2_derived/staircase_bound.json.

Point cle : la DUREE PHYSIQUE d'un echantillon est T/256 = 7.8125e-3 quelle que
soit la resolution (40 pas a N=256, 80 pas a N=512). Le defaut d'escalier est
donc commun aux deux grilles et ne contamine pas la comparaison 256/512 ; il ne
modifie pas non plus l'energie d'actionneur moyenne sur le cycle, parce que la
moyenne sur le cycle d'un signal maintenu est exactement la moyenne des 256
echantillons.
"""
import json
import os

import numpy as np

import lid_command as L

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
SRC = os.path.join(ROOT, "data", "lid_series")
CASES = {
    "B1": "fourier_Re500.npz",
    "B2": "B2_seed5_E025_re500_e0.25.npz",
    "B3": "B3_seed0_E025_re500_e0.25.npz",
}


def main():
    out = {"sample_duration_phys": L.T_PERIOD / L.NT_WAVE, "cases": {}}
    for case, fname in CASES.items():
        d = L.load_case(os.path.join(SRC, fname))
        rows = {}
        for N in (256, 512):
            steps = int(round(L.T_PERIOD * N / 0.05))
            slowdown = steps // L.NT_WAVE
            m = L.hold_vs_exact(d["c"], N, slowdown)
            m["dt_phys"] = 0.05 / N
            m["steps_per_period"] = steps
            rows[N] = m
            print(f"{case} N={N}: max|exact-hold|={m['max_abs_delta']:.3e} "
                  f"({100 * m['rel_to_peak']:.2f}% de la vitesse de pointe), "
                  f"L2_rel={m['l2_rel']:.2e}, dE_act/E_act={m['dE_rel']:.2e}, "
                  f"E={m['E_hold']:.9f}")
        same = abs(rows[256]["rel_to_peak"] - rows[512]["rel_to_peak"])
        print(f"   ecart de rel_to_peak entre 256 et 512 = {same:.2e} "
              f"(defaut commun aux deux grilles)\n")
        out["cases"][case] = {"by_N": rows, "rel_peak_grid_diff": same,
                              "resid": d["resid"]}
    dest = os.path.join(ROOT, "results", "d2_derived", "staircase_bound.json")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    print("->", dest)


if __name__ == "__main__":
    main()
