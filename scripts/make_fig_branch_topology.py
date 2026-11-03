# -*- coding: utf-8 -*-
"""Figure 20: flow topology of the three branch classes at Re=500, E*=0.25.

Three variants, all built from results/06_branch_figures/capture_*.npz:

  main        fig20_branch_topology          rows = B1/B2/B3, columns =
              time mean + the four phases t/T = 0, 1/4, 1/2, 3/4.
  phases8     figS5_branch_topology_phases   the same, with all eight phase
              bins (supplementary).
  panelscale  figS6_branch_topology_panelscale  the main layout with a separate
              psi scale per panel (supplementary).

Outputs go to figures/.
"""
import argparse
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
CAP = os.path.join(REPO, "results", "06_branch_figures")
OUT = os.path.join(REPO, "figures")

CASES = ["B1", "B2", "B3"]
PHASES = [0, 2, 4, 6]
TITLES = {"B1": r"$B_1$", "B2": r"$B_2$", "B3": r"$B_3$"}
SUBS = {"B1": r"$f_t=0.074$", "B2": r"$f_t=0.998$",
        "B3": r"$f_2=0.520,\ f_t=0.448$"}
COLOURS = {"B1": "tab:blue", "B2": "tab:red", "B3": "tab:green"}
NPHASE = 8
DENSITY = 1.30


def load(case):
    z = np.load(os.path.join(CAP, f"capture_{case}.npz"))
    d = dict(meta=json.loads(str(z["meta"])))
    d["x"] = np.asarray(z["x"])
    d["y"] = np.asarray(z["y"])
    d["psi"] = np.asarray(z["psi_mean"])
    d["pux"] = np.asarray(z["phase_ux"])
    d["puy"] = np.asarray(z["phase_uy"])
    d["ux"] = np.asarray(z["ux_mean"])
    d["uy"] = np.asarray(z["uy_mean"])
    d["ux_rms"] = np.asarray(z["ux_rms"])
    d["uy_rms"] = np.asarray(z["uy_rms"])
    d["np"] = NPHASE
    return d


def psi_of(ux, uy, dx):
    psi = np.cumsum(ux, axis=0) * dx
    psi -= psi[0, :][None, :]
    return psi


def stationarity(d):
    num = 0.0
    den = 0.0
    for k in range(d["np"]):
        num = max(num, float(np.linalg.norm(d["pux"][k] - d["ux"])
                             + np.linalg.norm(d["puy"][k] - d["uy"])))
        den = max(den, float(np.linalg.norm(d["pux"][k])
                             + np.linalg.norm(d["puy"][k])))
    return num / den if den else 0.0


def draw_panel(ax, X, Y, psi, ux, uy, levels, cmap, vlim, annotate,
               show_centre=None, fs=6.2, show_x=True, show_y=True):
    im = ax.contourf(X, Y, psi, levels=levels, cmap=cmap,
                     norm=Normalize(-vlim, vlim), extend="both")
    ax.streamplot(X, Y, ux, uy, color="k", linewidth=0.28,
                  density=DENSITY, arrowsize=0.42, arrowstyle="-|>",
                  broken_streamlines=False, minlength=0.08, zorder=2)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xticks([0.0, 0.5, 1.0])
    ax.set_yticks([0.0, 0.5, 1.0])
    ax.set_xticklabels(["0", "0.5", "1"] if show_x else [])
    ax.set_yticklabels(["0", "0.5", "1"] if show_y else [])
    ax.set_aspect("equal")
    ax.tick_params(labelsize=6.0, length=2, pad=1.2)
    if show_centre is not None:
        cx, cy = show_centre
        ax.plot([cx], [cy], marker="o", ms=3.2, mfc="none",
                mec="w", mew=0.8, zorder=5)
        ax.plot([cx], [cy], marker="+", ms=2.6, color="w",
                mew=0.7, zorder=5)
    if annotate:
        ax.text(0.035, 0.955, annotate, transform=ax.transAxes,
                fontsize=fs, va="top", color="k",
                bbox=dict(fc="w", ec="none", alpha=0.72, pad=1.1),
                zorder=6)
    return im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="main",
                    choices=["main", "phases8", "panelscale"])
    args = ap.parse_args()

    os.makedirs(OUT, exist_ok=True)

    data = {c: load(c) for c in CASES}
    dx = data["B1"]["x"][1] - data["B1"]["x"][0]
    for c in CASES:
        d = data[c]
        d["ppsi"] = np.stack([psi_of(d["pux"][k], d["puy"][k], dx)
                              for k in range(d["np"])])
        d["stat"] = stationarity(d)
        d["urms_max"] = float(
            np.hypot(d["ux_rms"], d["uy_rms"]).max())

    shown = []
    for c in CASES:
        shown.append(data[c]["psi"])
        if args.variant == "phases8":
            shown.extend(list(data[c]["ppsi"]))
        else:
            if c == "B1":
                shown.append(data[c]["ppsi"][0])
            else:
                shown.extend([data[c]["ppsi"][k] for k in PHASES])
    vlim = max(float(np.abs(s).max()) for s in shown)
    vlim = np.ceil(vlim * 24.0) / 24.0
    nlev = 24
    levels = np.linspace(-vlim, vlim, nlev + 1)
    print(f"common psi scale: +/-{vlim:.3f}, {nlev} intervals")

    cmap = "RdBu_r"
    if args.variant == "phases8":
        ncol = 9
        fw, fh = 6.3, 2.95
        s = 0.0785
        hs = s * fw / fh
        x0 = 0.075
        gap = 0.0105
        rows = [0.735, 0.735 - hs - 0.072, 0.735 - 2 * (hs + 0.072)]
    else:
        ncol = 5
        fw, fh = 6.3, 4.95
        s = 0.153
        hs = s * fw / fh
        x0 = 0.080
        gap = 0.0195
        rows = [0.780, 0.780 - hs - 0.048, 0.780 - 2 * (hs + 0.048)]
    xs = [x0 + i * (s + gap) for i in range(ncol)]

    fig = plt.figure(figsize=(fw, fh))
    axs = {}
    if args.variant == "phases8":
        for r, c in enumerate(CASES):
            for i in range(9):
                axs[(c, i)] = fig.add_axes([xs[i], rows[r], s, hs])
    else:
        for r, c in enumerate(CASES):
            for i in range(5):
                axs[(c, i)] = fig.add_axes([xs[i], rows[r], s, hs])
            if c == "B1":
                for i in range(1, 5):
                    axs[(c, i)].remove()
                    axs.pop((c, i))
                x_end = xs[4] + s
                axs[(c, "wide")] = fig.add_axes(
                    [xs[1], rows[r], x_end - xs[1], hs])
                axs[(c, "wide")].set_axis_off()

    im = None
    for r, c in enumerate(CASES):
        d = data[c]
        xx = d["x"]
        yy = d["y"]
        X, Y = np.meshgrid(xx, yy)
        if args.variant == "phases8":
            cols = range(9)
            for i in cols:
                ax = axs[(c, i)]
                if i == 0:
                    pl = d["psi"]
                    u, v = d["ux"], d["uy"]
                    ann = None
                else:
                    k = i - 1
                    pl = d["ppsi"][k]
                    u, v = d["pux"][k], d["puy"][k]
                    ann = None
                ex = None
                if i == 0:
                    iy, ix = np.unravel_index(np.argmin(pl), pl.shape)
                    ex = (xx[ix], yy[iy])
                im = draw_panel(ax, X, Y, pl, u, v, levels, cmap, vlim, ann,
                                show_centre=ex, fs=5.6,
                                show_x=(r == 2), show_y=(i == 0))
                if r == 0:
                    lab = (r"(a) mean" if i == 0
                           else r"(%s) %d/8" % (chr(ord("b") + i - 1), i - 1))
                    ax.set_title(lab, fontsize=6.0, pad=2.0)
                if i == 0:
                    ax.set_ylabel(r"%s" % TITLES[c], fontsize=9,
                                  labelpad=1.5)
        else:
            ax = axs[(c, 0)]
            pl = d["psi"]
            iy, ix = np.unravel_index(np.argmin(pl), pl.shape)
            ann = (r"$\psi_{\min}=%.3f$" % pl.min()
                   if args.variant == "main"
                   else r"$\max|\psi|=%.3f$" % np.abs(pl).max())
            if args.variant == "panelscale":
                v2 = float(np.abs(pl).max())
                im = draw_panel(ax, X, Y, pl, d["ux"], d["uy"],
                                np.linspace(-v2, v2, nlev + 1), cmap, v2,
                                ann, show_centre=(xx[ix], yy[iy]),
                                show_x=(r == 2), show_y=True)
            else:
                im = draw_panel(ax, X, Y, pl, d["ux"], d["uy"], levels,
                                cmap, vlim, ann,
                                show_centre=(xx[ix], yy[iy]),
                                show_x=(r == 2), show_y=True)
            ax.set_ylabel("%s\n%s" % (TITLES[c], SUBS[c]), fontsize=8.4,
                          labelpad=2.0)
            if r == 0:
                ax.set_title(r"(a)  $\langle\psi\rangle$", fontsize=7.4,
                             pad=5.0)
            if c == "B1":
                axw = axs[(c, "wide")]
                axw.text(
                    0.0, 0.90,
                    r"$B_1$ is stationary: the four phases coincide with"
                    "\n" r"the time mean to within $%.1f\%%$ "
                    r"(max over phases of" "\n"
                    r"$\|\mathbf{u}(t)-\langle\mathbf{u}\rangle\|"
                    r"/\|\mathbf{u}(t)\|$)," "\n"
                    r"with $u'_{\mathrm{rms,max}}/U_{\mathrm{ref}}"
                    r"=%.1f\%%$ and $R_K=%.2f$."
                    % (100 * d["stat"], 100 * d["urms_max"],
                       100 * d["meta"]["R_K"]),
                    transform=axw.transAxes, fontsize=7.0, va="top",
                    linespacing=1.55)
                if r == 0:
                    axw.set_title(
                        r"(b)–(e)  instantaneous: $t/T=0,\ 1/4,\ 1/2,\ 3/4$",
                        fontsize=7.4, pad=3.0)
                axw.text(
                    0.0, 0.24,
                    "One period of the lid control is shown in\n"
                    "Fig.~2(a); the flow itself has\n"
                    "no phase structure to display.",
                    transform=axw.transAxes, fontsize=6.6, va="top",
                    color="0.35", linespacing=1.5)
            else:
                for i, k in enumerate(PHASES, start=1):
                    ax = axs[(c, i)]
                    pl = d["ppsi"][k]
                    ann = (r"$|\psi|_{\max}=%.3f$" % np.abs(pl).max()
                           if args.variant != "main" else None)
                    draw_panel(ax, X, Y, pl, d["pux"][k], d["puy"][k],
                               levels, cmap, vlim, ann, fs=5.8,
                               show_x=(r == 2), show_y=False)
                    if r == 0:
                        ax.set_title(r"(%s)  %s" % (
                            chr(ord("b") + i - 1),
                            ["", r"t/T=0", r"t/T=1/4",
                             r"t/T=1/2", r"t/T=3/4"][i]),
                            fontsize=7.0, pad=3.0)

    if args.variant == "phases8":
        cax = fig.add_axes([xs[4], 0.105, 2 * s + gap, 0.026])
    else:
        cax = fig.add_axes([xs[0], 0.082, 0.36, 0.024])
    cb = fig.colorbar(im, cax=cax, orientation="horizontal",
                      ticks=[-0.04, 0.0, 0.04])
    cb.set_ticklabels([r"$-4$", r"$0$", r"$4$"])
    cb.set_label(r"stream function  $\psi/(U_{\mathrm{ref}})$   "
                 r"$[\times10^{-2}]$", fontsize=7.4, labelpad=1.6)
    cb.ax.tick_params(labelsize=7.2, length=2, pad=1.2)
    cb.outline.set_linewidth(0.5)
    if args.variant != "phases8":
        fig.text(xs[0] + 0.395, 0.090,
                 r"one scale and one level set for all eleven field panels"
                 "\n" r"streamlines: same density and placement rule",
                 fontsize=6.6, va="bottom", color="0.3", linespacing=2.0)

    for ax in fig.axes:
        for sp in ax.spines.values():
            sp.set_linewidth(0.6)

    name = {"main": "fig20_branch_topology",
            "phases8": "figS5_branch_topology_phases",
            "panelscale": "figS6_branch_topology_panelscale"}[args.variant]
    base = os.path.join(OUT, name)
    fig.savefig(base + ".pdf")
    fig.savefig(base + ".png", dpi=340)
    plt.close(fig)
    print("wrote", base + ".pdf/.png")

    for c, d in data.items():
        print("%s: psi in [%.4f, %.4f], max|psi|=%.4f, stationary to %.2f%%, "
              "u'rms_max/U_ref=%.4f"
              % (c, d["psi"].min(), d["psi"].max(), np.abs(d["psi"]).max(),
                 100 * d["stat"], d["urms_max"]))


if __name__ == "__main__":
    main()
