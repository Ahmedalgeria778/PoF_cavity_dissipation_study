# -*- coding: utf-8 -*-
"""Controle « commande en escalier » : hold vs exact, meme protocole.

Le solveur ne voit qu'un tableau (pas_par_periode, N) : la commande peut etre
jouee echantillon-maintenu (hold, np.repeat) ou evaluee a chaque pas a partir
des coefficients de Fourier (exact). Les deux coincident aux 256 temps
d'echantillonnage et different du ripple intra-echantillon.

Mesures analytiques (lid_command.hold_vs_exact) :
  * le defaut maximal vaut 0.5% (B1), 2.6% (B2), 2.1% (B3) de la vitesse de
    pointe et il est IDENTIQUE a N=256 et N=512, parce que la duree physique
    d'un echantillon est T/256 = 7.8125e-3 quelle que soit la resolution ;
  * l'energie d'actionneur moyenne sur le cycle n'en est pas modifiee
    (dE/E < 1e-15) : la normalisation E*=0.25 est la meme dans les deux modes.

Ce script compare les deux captures LBM et rend l'effet residuel sur Dbar,
Kbar, Pbar et la decomposition D(ū)/D_fluct, avec l'erreur d'echantillonnage
par periode (les periodes ne sont pas independantes : la correlation lag-1 est
~0.8, donc l'erreur affichee est une borne optimiste).

Usage :
    py scripts/compare_forcing_staircase.py --case B2
"""
import argparse
import json
import os

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CAP = os.path.join(ROOT, "results", "09_d2_capture")


def series(case, forcing, N):
    tag = f"capture_{case}_D2_N{N}" + ("" if forcing == "hold" else f"_{forcing}")
    path = os.path.join(CAP, tag + ".npz")
    if not os.path.exists(path):
        raise SystemExit(f"capture manquante : {path}")
    with np.load(path) as z:
        meta = json.loads(str(z["meta"]))
        d = {k: np.asarray(z[k]) for k in
             ("cyc_eps", "cyc_K", "cyc_P", "eps_series", "lid_error_series")}
    return meta, d, path


def stats(a):
    m = float(np.mean(a))
    s = float(np.std(a, ddof=1))
    n = len(a)
    ac = a - a.mean()
    r1 = float(np.sum(ac[:-1] * ac[1:]) / np.sum(ac * ac)) if n > 2 else 0.0
    # erreur effective avec correlation lag-1 (variance d'une moyenne AR(1))
    se = s / np.sqrt(n) * np.sqrt((1 + r1) / (1 - r1)) if abs(r1) < 0.999 else float("nan")
    return m, s, se, r1, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", default="B2")
    ap.add_argument("--N", type=int, default=256)
    args = ap.parse_args()

    mh, dh, ph = series(args.case, "hold", args.N)
    me, de, pe = series(args.case, "exact", args.N)
    n = min(len(dh["cyc_eps"]), len(de["cyc_eps"]))
    print(f"case={args.case} N={args.N}  hold: {len(dh['cyc_eps'])} P, "
          f"exact: {len(de['cyc_eps'])} P  -> comparaison sur les {n} premieres "
          f"periodes (fenetres identiques)")
    print(f"  hold : scale={mh['scale']:.9f} E_r={mh['E_r_realized']:.9f} "
          f"warm={mh['warm_periods']:.1f} P drift={mh['drift']:.2e}")
    print(f"  exact: scale={me['scale']:.9f} E_r={me['E_r_realized']:.9f} "
          f"warm={me['warm_periods']:.1f} P drift={me['drift']:.2e}")

    out = {"case": args.case, "N": args.N,
           "hold_file": os.path.basename(ph), "exact_file": os.path.basename(pe),
           "n_periods_compared": n, "hold_periods": mh["capture_periods"],
           "exact_periods": me["capture_periods"],
           "hold_seconds": mh["seconds"], "exact_seconds": me["seconds"]}
    print()
    print(f"{'quantite':<14}{'hold':>14}{'exact':>14}{'d(exact-hold)':>16}"
          f"{'relatif':>12}{'se(1period)':>14}")
    for key, label in (("cyc_eps", "Dbar"), ("cyc_K", "Kbar"), ("cyc_P", "Pbar")):
        a = dh[key][:n]
        b = de[key][:n]
        m_h, s_h, se_h, r1, _ = stats(a)
        m_e, s_e, se_e, _, _ = stats(b)
        diff = m_e - m_h
        rel = diff / m_h
        print(f"{label:<14}{m_h:>14.6e}{m_e:>14.6e}{diff:>16.3e}"
              f"{100 * rel:>11.3f}%{se_h:>14.2e}")
        out[label] = dict(hold=m_h, exact=m_e, diff=diff, rel=rel,
                          sd_per_period_h=s_h, se_per_period_h=se_h,
                          lag1_autocorr=r1, sd_per_period_e=s_e, se_exact=se_e)

    # decomposition de Jensen sur les moyennes de cycle completees
    for tag, m in (("hold", mh), ("exact", me)):
        Dm = m["eps_meanfield"]
        Dc = m["eps_cycle_mean"]
        print(f"  {tag:<6}: D(ubar)={Dm:.6e}  Dbar={Dc:.6e}  "
              f"D_fluct={Dc - Dm:.6e}  Dbar/D(ubar)={Dc / Dm:.3f}")
        out[f"jensen_{tag}"] = dict(D_meanfield=Dm, D_cycle=Dc,
                                    D_fluct=Dc - Dm, ratio=Dc / Dm)
    dfl = out["jensen_exact"]["D_fluct"] - out["jensen_hold"]["D_fluct"]
    base = out["jensen_hold"]["D_fluct"]
    print(f"  variation de D_fluct : {dfl:.3e} "
          f"({100 * dfl / base:.2f}% du fluctuant hold)")
    out["D_fluct_change"] = dict(abs=dfl, rel=dfl / base)

    # controle de la commande jouee : le ripple lui-meme, mesure sur les series
    print()
    print(f"  erreur de paroi max : hold={mh['lid_max_error']:.3e} "
          f"exact={me['lid_max_error']:.3e} (meme ordre = reponse du champ, "
          f"pas la commande)")

    dest = os.path.join(ROOT, "results", "d2_derived",
                        f"staircase_control_{args.case}_N{args.N}.json")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2, sort_keys=True)
    print("->", dest)


if __name__ == "__main__":
    main()
