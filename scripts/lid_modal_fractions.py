# -*- coding: utf-8 -*-
"""Modal fractions of the three imposed controls, on the rule of Supp. Sec. S2.2.

The series stored in each capture archive is decomposed in the identification
basis, U(x, tau) = sum_m sin(m pi x) [a_m0 + sum_{n>=1} (A_mn cos 2 pi n tau
+ B_mn sin 2 pi n tau)], whose modal energies are E_m0 = a_m0^2 / 2 and
E_mn = (A_mn^2 + B_mn^2) / 4. The fractions quoted in Main Table 1 and in
Supp. Secs. S2.2 and S4.6 are normalized by the total energy of the control,
f_2 = E_20 / sum E and f_t = sum_{n>=1} E / sum E, which is the rule of the
classification; the time-mean denominators used by
scripts/d2_derived_quantities.py give the slightly larger f_2 values quoted
next to them in Main Table 1.

Produces results/d2_derived/lid_modal_fractions.json.
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
CAP = os.path.join(REPO, "results", "09_d2_capture")
OUTDIR = os.path.join(REPO, "results", "d2_derived")
OUT = os.path.join(OUTDIR, "lid_modal_fractions.json")

CASES = ["B1", "B2", "B3"]
RESOLUTIONS = [256, 512]
NM_MAX = 20


def modal_energies(ul, x, nm_max=NM_MAX):
    """Modal energy matrix E[m, n] of one exported period, m one-based."""
    nt = ul.shape[0]
    emn = np.zeros((nm_max + 1, nt // 2 + 1))
    for m in range(1, nm_max + 1):
        sx = np.sin(m * np.pi * x)
        # sine projection: <sin^2>_x = 1/2, so the factor 2 recovers a_m(tau)
        pm = 2.0 * np.trapezoid(ul * sx[None, :], x=x, axis=1)
        a_m0 = pm.mean()
        emn[m, 0] = 0.5 * a_m0 ** 2
        coef = np.fft.rfft(pm - a_m0) / nt
        amp = 2.0 * np.abs(coef)
        emn[m, 1:] = 0.25 * amp[1:] ** 2
    return emn


def fractions(emn):
    tot = emn.sum()
    return dict(f1=float(emn[1, 0] / tot), f2=float(emn[2, 0] / tot),
                f_hi=float(emn[3:, 0].sum() / tot),
                f_t=float(emn[:, 1:].sum() / tot),
                E_total=float(tot),
                E_mean_field=float(emn[:, 0].sum()),
                f2_mean_denominator=float(emn[2, 0] / emn[:, 0].sum()))


def report(case, resolution):
    path = os.path.join(CAP, f"capture_{case}_D2_N{resolution}.npz")
    d = np.load(path, allow_pickle=True)
    ul = np.asarray(d["U_lid_native"], dtype=np.float64)
    x = np.asarray(d["x"], dtype=np.float64)
    return fractions(modal_energies(ul, x))


def main():
    out = {}
    for case in CASES:
        out[case] = {}
        for res in RESOLUTIONS:
            try:
                r = report(case, res)
            except FileNotFoundError:
                continue
            out[case][f"N{res}"] = r
            print("%s N=%d  f1=%.4f  f2=%.4f (mean-denom %.4f)  f_m>=3=%.4f  "
                  "f_t=%.4f  E=%.6f" %
                  (case, res, r["f1"], r["f2"], r["f2_mean_denominator"],
                   r["f_hi"], r["f_t"], r["E_total"]))
        print("    rule: Supp. Sec. S2.2, total-energy denominator; "
              "nm_max=%d" % NM_MAX)
    os.makedirs(OUTDIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
