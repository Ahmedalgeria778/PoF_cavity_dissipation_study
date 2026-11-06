"""Justification quantitative de la longueur de fenetre de capture.

Question du referee potentiel : "pourquoi N periodes de capture, et sont-elles
suffisantes ?". La reponse doit etre mesuree, pas asserted.

Pour chaque branche capturee, sur la serie des moyennes par periode :
  1. convergence de la moyenne cumulee en fonction de la longueur de fenetre
     (ecart relatif de mean(1..k) a mean(1..n) pour k = 4, 8, 16, 24, 32) ;
  2. test de tendance : pente lineaire sur la serie, avec son erreur, et ce
     que la tendance accumulerait sur la fenetre elle-meme (un derive residuelle
     imposerait une fenetre plus longue ou une chauffe plus longue) ;
  3. erreur-type de la moyenne avec correlation lag-1 (moyenne AR(1)) ;
  4. split-half : ecart relatif (moyenne des moitis impaires) - (paires), qui
     est l'erreur que deux captures independantes de la MEME longueur peuvent
     afficher — c'est la grandeur qu'il faut comparer a l'effet de resolution
     que la campagne N=512 doit resoudre.

Le seuil de decision est explicite : la fenetre est suffisante si l'erreur
d'echantillonnage de Dbar est tres inferieure au plus petit effet que l'on veut
resoudre (ici l'ecart B1/B3 ~2e-2 relatif, et la variation 256->512 attendue
entre 1e-3 et 1e-2 relatif).

Usage : py scripts/justify_capture_window.py [--N 256]
"""
import argparse
import json
import os

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CAP = os.path.join(ROOT, "results", "09_d2_capture")
CASES = ("B1", "B2", "B3")
KEYS = (("cyc_eps", "Dbar"), ("cyc_K", "Kbar"), ("cyc_P", "Pbar"))


def ar1_se(a):
    """Erreur-type de la moyenne d'une serie auto-corelee (lag-1)."""
    n = len(a)
    s = float(np.std(a, ddof=1))
    ac = a - a.mean()
    r1 = float(np.sum(ac[:-1] * ac[1:]) / np.sum(ac * ac)) if n > 2 else 0.0
    if abs(r1) >= 0.999:
        return float("nan"), r1
    return s / np.sqrt(n) * np.sqrt((1 + r1) / (1 - r1)), r1


def trend(a):
    """Pente par periode et sa significativite (regression lineaire + t-test)."""
    n = len(a)
    x = np.arange(n, dtype=float)
    xm, ym = x.mean(), a.mean()
    sxx = float(np.sum((x - xm) ** 2))
    b = float(np.sum((x - xm) * (a - ym)) / sxx)
    resid = (a - ym) - b * (x - xm)
    dof = n - 2
    if dof <= 0:
        return b, float("nan"), float("nan")
    s2 = float(np.sum(resid ** 2)) / dof
    seb = float(np.sqrt(s2 / sxx))
    return b, seb, b / seb if seb > 0 else float("nan")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--N", type=int, default=256)
    args = ap.parse_args()

    out = {"N": args.N, "cases": {}}
    print(f"fenetres sur les captures D2 N={args.N}")
    worst = {}
    for case in CASES:
        path = os.path.join(CAP, f"capture_{case}_D2_N{args.N}.npz")
        if not os.path.exists(path):
            print(f"{case}: ABSENT ({path})")
            continue
        with np.load(path) as z:
            series = {lab: np.asarray(z[k], float) for k, lab in KEYS}
        n = len(series["Dbar"])
        print("=" * 70)
        print(f"{case}: {n} periodes capturees")
        out["cases"][case] = {"n_periods": n}
        for lab, a in series.items():
            full = float(a.mean())
            se, r1 = ar1_se(a)
            b, seb, t = trend(a)
            # convergence en longueur de fenetre
            conv = [(k, float(np.mean(a[:k]))) for k in
                    sorted({4, 8, 16, 24, 32} & set(range(1, n + 1)))]
            devs = {str(k): abs(v - full) / abs(full) for k, v in conv}
            # split-half
            odd = float(np.mean(a[0::2]))
            even = float(np.mean(a[1::2]))
            sh = abs(odd - even) / abs(full)
            trend_win = abs(b) * n / abs(full)
            print(f"  {lab:<6} mean={full:.8e} sd/cycle={np.std(a, ddof=1):.2e} "
                  f"se(AR1)={se:.2e} ({se/abs(full):.1e} rel) lag1={r1:.2f}")
            print(f"      fenetre : " + "  ".join(
                f"k={k}:{d:.1e}" for k, d in sorted(devs.items(), key=lambda kv: int(kv[0]))))
            print(f"      tendance sur {n} P = {100*trend_win:.2e}% (t={t:.2f}) ; "
                  f"split-half = {100*sh:.2e}%")
            out["cases"][case][lab] = dict(
                mean=full, sd_cycle=float(np.std(a, ddof=1)), se_ar1=se,
                se_rel=se / abs(full), lag1=r1, window_dev=devs,
                trend_rel_over_window=trend_win, trend_t=t,
                split_half_rel=sh)
            key = lab
            prev = worst.get(key)
            if prev is None or sh > prev:
                worst[key] = sh

    print("=" * 70)
    print("DECISION")
    for lab, sh in worst.items():
        print(f"  {lab}: pire erreur de reproduction entre deux demi-fenetres "
              f"de {args.N}P = {sh:.1e} relatif")
    print("  Effet a resoudre : ecart B1/B3 ~ 2e-2 relatif ; variation de "
          "resolution attendue 1e-3 a 1e-2 relatif.")
    dest = os.path.join(ROOT, "results", "d2_derived",
                        f"capture_window_justification_N{args.N}.json")
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump({"N": args.N, "cases": out["cases"],
                   "worst_split_half": worst}, fh, indent=2, sort_keys=True)
    print("->", dest)


if __name__ == "__main__":
    main()
