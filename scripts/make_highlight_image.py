# -*- coding: utf-8 -*-
"""Highlight image for the Physics of Fluids table of contents.

Three panels, one per identified branch (B1, B2, B3), showing the cycle-mean
local viscous dissipation density

    <phi> = (1/8) sum_k  2 nu ( S11^2 + S22^2 + 2 S12^2 )_k ,

evaluated at the eight phase bins stored in
results/09_d2_capture/capture_*_D2_N256.npz, with the same array convention as
scripts/make_fig_branch_topology_d2.py (fields indexed [j, i], x along axis 1).
Streamlines of the time-mean flow are overlaid, and each panel uses a
logarithmic colour map spanning five decades below its own maximum, so the
panels show where the dissipation is produced rather than its absolute
amplitude.

The number annotated on each panel is the cycle-mean dissipation of the 32
captured periods, read from results/d2_derived/d2_summary.json; it is the
value reported in the manuscript.  The domain integral of the eight-bin
reconstruction is printed as a consistency check and the density amplitude is
normalised to the reported cycle mean, so that the colour map and the annotated
number agree.

Outputs figures/highlight_image.png (300 dpi).
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
CAP = os.path.join(REPO, "results", "09_d2_capture")
DERIVED = os.path.join(REPO, "results", "d2_derived")
OUT = os.path.join(REPO, "figures")

CASES = ["B1", "B2", "B3"]
TITLES = {"B1": r"$B_1$  quasi-steady", "B2": r"$B_2$  lid-oscillatory",
          "B3": r"$B_3$  mixed"}
LABELS = {"B1": "(a)", "B2": "(b)", "B3": "(c)"}
CMAP = "inferno"
STREAM_DENSITY = 0.25


def density(ux, uy, dx, nu):
    """Local dissipation density phi = 2 nu S:S of a 2-D velocity field."""
    s11 = np.gradient(ux, dx, axis=1)
    s22 = np.gradient(uy, dx, axis=0)
    s12 = 0.5 * (np.gradient(ux, dx, axis=0) + np.gradient(uy, dx, axis=1))
    return 2.0 * nu * (s11 ** 2 + s22 ** 2 + 2.0 * s12 ** 2), s11, s22, s12


def main():
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(DERIVED, "d2_summary.json"), encoding="utf-8") as fh:
        summ = json.load(fh)

    fields = {}
    for c in CASES:
        z = np.load(os.path.join(CAP, f"capture_{c}_D2_N256.npz"),
                    allow_pickle=True)
        x = np.asarray(z["x"])
        y = np.asarray(z["y"])
        ux = np.asarray(z["ux_mean"])
        uy = np.asarray(z["uy_mean"])
        pux = np.asarray(z["phase_ux"])
        puy = np.asarray(z["phase_uy"])
        dx = float(x[1] - x[0])
        nu = 1.0 / float(summ[c]["meta"]["Re"])

        phi_bins = np.stack([density(pux[k], puy[k], dx, nu)[0]
                             for k in range(pux.shape[0])])
        phi_bar = phi_bins.mean(axis=0)
        integral = float(phi_bar.sum()) * dx * dx
        dbar = float(summ[c]["Dbar"])
        # The eight phase bins are time-averaged over 1/8 of a period, and the
        # wall-normal derivative of the thin Stokes layer is discretised
        # differently from the solver's own estimator, so the reconstructed
        # density integrates 5-8% above the reported cycle mean.  The shape is
        # kept and the amplitude is normalised to that cycle mean.
        scale = dbar / integral
        phi_bar = phi_bar * scale

        fields[c] = dict(X=np.meshgrid(x, y)[0], Y=np.meshgrid(x, y)[1],
                         phi=phi_bar, ux=ux, uy=uy,
                         integral=integral, scale=scale, dbar=dbar,
                         N=summ[c]["meta"]["N"], Re=summ[c]["meta"]["Re"])
        print("%s: 8-bin integral of <phi> = %.5e   cycle-mean D = %.5e   "
              "difference = %+.2f%%   normalisation applied = %.4f"
              % (c, integral, fields[c]["dbar"],
                 100.0 * (integral / fields[c]["dbar"] - 1.0), scale))

    fig = plt.figure(figsize=(7.4, 3.0))
    s = 0.255
    hs = s * 7.4 / 3.0
    x0 = 0.045
    gap = 0.030
    bottom = 0.235
    for r, c in enumerate(CASES):
        f = fields[c]
        ax = fig.add_axes([x0 + r * (s + gap), bottom, s, hs])
        norm = LogNorm(vmin=1.0e-5 * f["phi"].max(), vmax=f["phi"].max())
        im = ax.pcolormesh(f["X"], f["Y"],
                           np.maximum(f["phi"], 1.0e-5 * f["phi"].max()),
                           cmap=CMAP, norm=norm, shading="auto")
        ax.streamplot(f["X"], f["Y"], f["ux"], f["uy"],
                      color=(1.0, 1.0, 1.0, 0.85),
                      linewidth=0.45, density=STREAM_DENSITY, arrowsize=0.6,
                      broken_streamlines=False, minlength=0.08, zorder=3)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xticks([0.0, 0.5, 1.0])
        ax.set_yticks([0.0, 0.5, 1.0])
        ax.set_xticklabels(["0", "0.5", "1"] if r == 0 else [])
        ax.set_yticklabels(["0", "0.5", "1"] if r == 0 else [])
        ax.set_aspect("equal")
        ax.tick_params(labelsize=6.2, length=2, colors="w")
        for sp in ax.spines.values():
            sp.set_linewidth(0.6)
            sp.set_color("0.75")
        ax.set_title("%s  %s" % (LABELS[c], TITLES[c]), fontsize=8.2,
                     pad=4.0, color="k")
        ax.text(0.03, 0.045, r"$\overline{D}=%.2f\times10^{-2}$"
                % (100.0 * f["dbar"]), transform=ax.transAxes, fontsize=7.4,
                va="bottom", color="w",
                bbox=dict(fc="k", ec="none", alpha=0.55, pad=1.6), zorder=6)

    fig.text(x0, 0.955,
             r"Where the cycle-mean dissipation is produced, at matched "
             r"actuation norm $\overline{E}_{\mathrm{act}}=0.25$, $Re=%d$, $N=%d$"
             % (fields["B1"]["Re"], fields["B1"]["N"]),
             fontsize=8.4, va="top")
    fig.text(x0, 0.030,
             "Logarithmic colour map, five decades below the maximum of each "
             "panel; white lines: streamlines of the time-mean flow.\n"
             r"$\langle\phi\rangle$: local dissipation density reconstructed from "
             r"the eight phase bins, rescaled so that each panel integrates to" "\n"
             r"the annotated cycle mean $\overline{D}$ of the 32 captured periods "
             "(Table 4 of the manuscript). The panels show where the\n"
             "dissipation is produced, not its absolute amplitude.",
             fontsize=6.6, va="bottom", color="0.35", linespacing=1.55)

    base = os.path.join(OUT, "highlight_image")
    fig.savefig(base + ".png", dpi=300)
    plt.close(fig)
    print("wrote", base + ".png")


if __name__ == "__main__":
    main()
