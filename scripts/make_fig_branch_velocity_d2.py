# -*- coding: utf-8 -*-
"""Figure 21: velocity fields and centreline profiles of the three branch
captures, built exclusively from results/09_d2_capture/capture_*_D2_N256.npz.

  (a) mean u, (b) mean v, (c) streamwise r.m.s. fluctuation u'_rms, each on one
      common scale for the three branches;
  (d) mean u along x = 1/4 with the +/- u'_rms band;
  (e) mean v along y = 1/2, plotted against x;
  (f) the maxima of the three fields.

Outputs figures/fig21_branch_velocity.pdf/.png and a caption fact file.
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
CAP = os.path.join(REPO, "results", "09_d2_capture")
OUT = os.path.join(REPO, "figures")
FACTS = os.path.join(REPO, "results", "d2_derived", "fig21_facts.txt")

CASES = ["B1", "B2", "B3"]


def load(case):
    z = np.load(os.path.join(CAP, "capture_%s_D2_N256.npz" % case),
                allow_pickle=True)
    return dict(
        x=np.asarray(z["x"], dtype=float),
        y=np.asarray(z["y"], dtype=float),
        ux=np.asarray(z["ux_mean"], dtype=float),
        uy=np.asarray(z["uy_mean"], dtype=float),
        ux_rms=np.asarray(z["ux_rms"], dtype=float),
        uy_rms=np.asarray(z["uy_rms"], dtype=float),
    )


def main():
    os.makedirs(OUT, exist_ok=True)
    data = {c: load(c) for c in CASES}
    X, Y = np.meshgrid(data["B1"]["x"], data["B1"]["y"])

    def lim(key):
        return max(float(np.abs(d[key]).max()) for d in data.values())

    lims = {"ux": lim("ux"), "uy": lim("uy"), "ux_rms": lim("ux_rms")}
    fig, axs = plt.subplots(2, 3, figsize=(10.2, 6.4))
    fig.subplots_adjust(left=0.075, right=0.985, top=0.90, bottom=0.115,
                        hspace=0.32, wspace=0.24)

    for col, (key, title) in enumerate([
            ("ux", r"(a)  $\bar{u}$"),
            ("uy", r"(b)  $\bar{v}$"),
            ("ux_rms", r"(c)  $u'_{x,\mathrm{rms}}$")]):
        ax = axs[0, col]
        v = lims[key]
        yy = data["B1"]["y"]
        xs = [d["x"] + k for k, d in enumerate(data.values())]
        Xc, Yc = np.meshgrid(np.concatenate(xs), yy)
        zz = np.hstack([d[key] for d in data.values()])
        if key == "ux_rms":
            im = ax.contourf(Xc, Yc, zz, levels=17, cmap="inferno",
                             norm=Normalize(0.0, v))
        else:
            im = ax.contourf(Xc, Yc, zz, levels=17, cmap="RdBu_r",
                             norm=Normalize(-v, v), extend="both")
        ax.set_xlim(0, 3)
        ax.set_ylim(0, 1)
        ax.set_xticks([0.5, 1.5, 2.5])
        ax.set_xticklabels([r"$B_1$", r"$B_2$", r"$B_3$"], fontsize=9)
        ax.set_yticks([0.0, 0.5, 1.0])
        ax.tick_params(labelsize=7.5, length=2)
        ax.set_title(title + "   (range $0$ to $%.3f$)" % v
                     if key == "ux_rms" else
                     title + "   (range $\\pm%.3f$)" % v, fontsize=9)
        for k in range(1, 3):
            ax.axvline(k, color="w", lw=1.0)
        cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.02)
        cb.ax.tick_params(labelsize=6.5, length=2)

    # ---- (d) u along x = 1/4 with the r.m.s. band ----------------------
    ax = axs[1, 0]
    for c in CASES:
        d = data[c]
        i = int(np.argmin(np.abs(d["x"] - 0.25)))
        ax.plot(d["ux"][:, i], d["y"], lw=1.5, label=r"$B_%s$" % c[1])
        ax.fill_betweenx(d["y"], d["ux"][:, i] - d["ux_rms"][:, i],
                         d["ux"][:, i] + d["ux_rms"][:, i], alpha=0.25, lw=0)
    ax.axvline(0.0, color="0.7", lw=0.6)
    ax.set_xlabel(r"$\bar{u}$ and $\bar{u}\pm u'_{x,\mathrm{rms}}$ at"
                  r" $x=1/4$", fontsize=8)
    ax.set_ylabel(r"$y$", fontsize=9)
    ax.set_title(r"(d)  streamwise mean profile", fontsize=9)
    ax.tick_params(labelsize=7.5, length=2)
    ax.legend(fontsize=6.6, frameon=False, loc="lower right")

    # ---- (e) v along y = 1/2 -------------------------------------------
    ax = axs[1, 1]
    for c in CASES:
        d = data[c]
        j = int(np.argmin(np.abs(d["y"] - 0.5)))
        ax.plot(d["x"], d["uy"][j, :], lw=1.5, label=r"$B_%s$" % c[1])
    ax.axhline(0.0, color="0.7", lw=0.6)
    ax.set_xlabel(r"$x$", fontsize=8)
    ax.set_ylabel(r"$\bar{v}$ at $y=1/2$", fontsize=8)
    ax.set_title(r"(e)  transverse mean profile", fontsize=9)
    ax.tick_params(labelsize=7.5, length=2)
    ax.legend(fontsize=6.6, frameon=False)

    # ---- (f) maxima -----------------------------------------------------
    ax = axs[1, 2]
    ax.axis("off")
    lines = []
    for c in CASES:
        d = data[c]
        j = int(np.argmin(np.abs(d["y"] - 0.5)))
        lines.append(r"$B_%s$: $\max|\bar{u}|=%.3f$,"
                     "\n" r"$\max u'_{x,\mathrm{rms}}=%.3f$,"
                     "\n" r"$\max|\bar{v}(y=1/2)|=%.3f$"
                     % (c[1], np.abs(d["ux"]).max(), d["ux_rms"].max(),
                        np.abs(d["uy"][j, :]).max()))
    ax.text(0.02, 0.96, "\n\n".join(lines), fontsize=7.6, va="top",
            linespacing=1.9)
    ax.set_title(r"(f)  maxima of the three fields", fontsize=9)

    base = os.path.join(OUT, "fig21_branch_velocity")
    fig.savefig(base + ".pdf")
    fig.savefig(base + ".png", dpi=300)
    plt.close(fig)

    with open(FACTS, "w", encoding="utf-8") as fh:
        fh.write("wrote %s.pdf\n" % base)
        for c in CASES:
            d = data[c]
            j = int(np.argmin(np.abs(d["y"] - 0.5)))
            fh.write("%s: abs_ux_max=%.4f abs_uy_max=%.4f ux_rms_max=%.4f "
                     "uy_rms_max=%.4f abs_v_midline=%.4f abs_u_quarter=%.4f\n"
                     % (c, np.abs(d["ux"]).max(), np.abs(d["uy"]).max(),
                        d["ux_rms"].max(), d["uy_rms"].max(),
                        np.abs(d["uy"][j, :]).max(),
                        np.abs(d["ux"][:, int(np.argmin(abs(d["x"]-0.25)))]).max()))


if __name__ == "__main__":
    main()
