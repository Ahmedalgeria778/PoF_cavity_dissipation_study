"""Spatial sine decomposition, harmonic by harmonic, of the three imposed lid series.

Reads the archived D2 lid series (256 samples per period, endpoint=False) that
scripts/run_branch_capture_d2.py actually imposes, so the decomposition describes
the control as it is realised in the captures of results/09_d2_capture/.

Output: results/lid_spatial_decomposition.json and the rows of
supplementary/data_appendix/p2_table_lid_structure.tex.
"""
import json
import os

import numpy as np

ARCHIVE = os.path.join("data", "lid_series")
SERIES = {
    "B1": "fourier_Re500.npz",
    "B2": "B2_seed5_E025_re500_e0.25.npz",
    "B3": "B3_seed0_E025_re500_e0.25.npz",
}
M = 7
E_TARGET = 0.25
RESCALE = {"B1": True, "B2": False, "B3": False}


def sine(a1d, x):
    a = [2.0 * np.trapezoid(a1d * np.sin(m * np.pi * x), x) for m in range(1, M + 1)]
    e = np.array([0.5 * v * v for v in a])
    return a, e / e.sum() if e.sum() else e


out = {}
for b, fn in SERIES.items():
    U = np.asarray(np.load(os.path.join(ARCHIVE, fn))["U_series"], dtype=float)
    nt, nx = U.shape
    x = np.linspace(0.0, 1.0, nx)
    e_raw = float(np.mean([np.trapezoid(row ** 2, dx=1.0 / (nx - 1)) for row in U]))
    scale = float(np.sqrt(E_TARGET / e_raw)) if RESCALE[b] else 1.0
    U = U * scale
    r = np.fft.rfft(U, axis=0)
    amp = 2.0 * np.abs(r) / nt
    amp[0] = r[0].real / nt                             # signed time mean

    out[b] = {"file": fn, "nt": int(nt), "nx": int(nx),
              "e_raw": round(e_raw, 6), "scale": round(scale, 6)}
    print("=" * 62, b)
    for n in range(5):
        a, fr = sine(amp[n], x)
        energy = float(np.trapezoid(amp[n] ** 2, x)) * (0.5 if n else 1.0)
        out[b]["n%d" % n] = dict(a_m=[round(v, 4) for v in a],
                                 frac=[round(float(v), 3) for v in fr],
                                 E=round(energy, 5))
        print(" n=%d  E=%.5f  a_m=%s  share(m=1..4)=%s"
              % (n, energy, [round(v, 3) for v in a[:4]],
                 [round(float(v), 3) for v in fr[:4]]))
    e_tot = sum(out[b]["n%d" % n]["E"] for n in range(5))
    out[b]["E_tot_5harmonics"] = round(e_tot, 5)
    out[b]["share_of_total"] = {"n%d" % n: round(out[b]["n%d" % n]["E"] / e_tot, 4)
                                for n in range(5)}
    out[b]["f10"] = round(out[b]["share_of_total"]["n0"]
                          * out[b]["n0"]["frac"][0], 4)
    out[b]["f20"] = round(out[b]["share_of_total"]["n0"]
                          * out[b]["n0"]["frac"][1], 4)
    rev = (U.min(axis=0) < 0.0) & (U.max(axis=0) > 0.0)
    out[b]["reversing_span_fraction"] = round(float(rev[1:-1].mean()), 3)
    out[b]["reversing_span_extent"] = ([round(float(x[i]), 2)
                                       for i in (np.where(rev)[0][[0, -1]])]
                                       if rev.any() else None)
    mid = 0.5 * (U[:, nx // 2 - 1] + U[:, nx // 2])   # x = 1/2 (even grid)
    out[b]["sign_changes_at_midline"] = int(np.sum(np.diff(np.sign(mid)) != 0))
    print(" shares of total: %s  f10=%.4f f20=%.4f"
          % (out[b]["share_of_total"], out[b]["f10"], out[b]["f20"]))
    print(" reversing span: fraction=%.3f extent=%s   midline sign changes=%d"
          % (out[b]["reversing_span_fraction"], out[b]["reversing_span_extent"],
             out[b]["sign_changes_at_midline"]))

os.makedirs("results", exist_ok=True)
json.dump(out, open("results/lid_spatial_decomposition.json", "w"), indent=1)
