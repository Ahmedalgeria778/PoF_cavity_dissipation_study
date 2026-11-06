# -*- coding: utf-8 -*-
"""Figure: mean-field dissipation against cycle-mean dissipation for the controls
compared at Re=500, E_act=0.25, N=256.

Stationary controls come from results/p1_gci_iso/p1_gci_summary.csv (N=256
column); the three time-dependent branches come from
results/09_d2_capture/capture_B?_D2_N256.npz via results/d2_derived/*.json and
results/stokes_scaling_estimate_d2.json.

Outputs figures/fig18_branch_iso_cycle.pdf/.png and
results/d2_derived/fig18_facts.txt.
"""
import io
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(REPO, "figures")
FACTS = os.path.join(REPO, "results", "d2_derived", "fig18_facts.txt")

S = json.load(io.open(os.path.join(REPO, "results", "d2_derived",
                                    "d2_summary.json"), encoding="utf-8"))
ST = json.load(io.open(os.path.join(REPO, "results",
                                    "stokes_scaling_estimate_d2.json"),
                       encoding="utf-8"))

steady = {}
with io.open(os.path.join(REPO, "results", "p1_gci_iso", "p1_gci_summary.csv"),
             encoding="utf-8") as fh:
    hdr = fh.readline().strip().split(",")
    for line in fh:
        if not line.strip():
            continue
        v = dict(zip(hdr, line.strip().split(",")))
        steady[v["case"]] = dict(E_r=float(v["E_r"]), D=float(v["eps256"]))

LBL = {
    "uniform": "Uniform lid",
    "k1": r"$k=1$",
    "k2": r"$k=2$",
    "b1mean": r"$B_1$ profile",
}

CASES = ["uniform", "k1", "k2", "b1mean", "B1", "B2", "B3"]
NU, W1, EACT = 1.0 / 500.0, np.pi, 0.25
SLOPE = EACT * np.sqrt(NU * W1 / 2.0)


def values():
    rows = []
    for c in CASES:
        if c in steady:
            rows.append(dict(name=LBL[c], ft=0.0, dmf=steady[c]["D"],
                             dbar=steady[c]["D"], stationary=True))
        else:
            s = S[c]
            rows.append(dict(name=r"$B_%s$" % c[1], ft=s["ft_temporal"],
                             dmf=s["Dmf"], dbar=s["Dbar"],
                             stationary=False))
    return rows


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = values()
    xi = np.arange(len(rows))

    fig, axs = plt.subplots(1, 2, figsize=(10.2, 4.5))
    fig.subplots_adjust(left=0.085, right=0.985, top=0.875, bottom=0.275,
                        wspace=0.29)

    # ---- (a) the two functionals ---------------------------------------
    ax = axs[0]
    for i, r in enumerate(rows):
        ax.plot([i - 0.085, i + 0.085], [r["dmf"], r["dbar"]], color="0.6",
                lw=1.0, zorder=1)
    ax.plot(xi - 0.085, [r["dmf"] for r in rows], "o", ms=7.0,
            mfc="#1f4e79", mec="#1f4e79", ls="none",
            label=r"$D(\overline{\mathbf{u}})$, mean-field functional",
            zorder=3)
    ax.plot(xi + 0.085, [r["dbar"] for r in rows], "o", ms=7.5, mfc="white",
            mec="#c00000", mew=1.4, ls="none",
            label=r"$\overline{D}$, cycle mean", zorder=3)
    ax.axhspan(steady["k1"]["D"], steady["b1mean"]["D"], color="0.85",
               alpha=0.55, zorder=0,
               label=r"range of the stationary controls")
    ax.set_xticks(xi)
    ax.set_xticklabels([r["name"] for r in rows], rotation=25, ha="right",
                       fontsize=7.8)
    ax.set_xlim(-0.6, len(rows) - 0.4)
    ax.set_yscale("log")
    ax.set_ylim(6e-4, 4e-2)
    ax.tick_params(axis="y", labelsize=7.8)
    ax.set_ylabel(r"dissipation  $[\nu U_{\mathrm{ref}}^2/L]$", fontsize=8.8)
    ax.set_title(r"(a)  the two functionals of the same flow", fontsize=9.2)
    ax.legend(fontsize=7.4, frameon=False, loc="lower left",
              handletextpad=0.35)

    # ---- (b) fluctuating part against f_t ------------------------------
    ax = axs[1]
    fg = np.logspace(-2.3, 0.1, 50)
    ax.plot(fg, SLOPE * fg, ls="--", lw=1.1, color="0.4", zorder=1,
            label=r"$f_t\overline{E}_{\mathrm{act}}"
                  r"\sqrt{\nu\omega_1/2}$")
    for r in rows:
        if r["stationary"]:
            continue
        dfl = r["dbar"] - r["dmf"]
        ax.plot(r["ft"], dfl, "o", ms=8.0, mfc="#c00000", mec="#c00000",
                ls="none", zorder=3)
        ax.annotate(r["name"], (r["ft"], dfl), fontsize=8.0,
                    xytext=(6, 4), textcoords="offset points")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(6e-3, 2.2)
    ax.set_ylim(1.2e-4, 3e-2)
    ax.set_xticks([0.01, 0.1, 1.0])
    ax.set_xticklabels([r"$10^{-2}$", r"$10^{-1}$", r"$1$"], fontsize=7.8)
    ax.tick_params(axis="y", labelsize=7.8)
    ax.set_xlabel(r"temporal energy fraction of the control  $f_t$",
                  fontsize=8.8)
    ax.set_ylabel(r"fluctuating part  $\overline{D}-D"
                  r"(\overline{\mathbf{u}})$", fontsize=8.8)
    ax.set_title(r"(b)  fluctuating part of the cycle mean", fontsize=9.2)
    ax.grid(which="both", lw=0.4, color="0.85", zorder=0)
    ax.legend(fontsize=7.4, frameon=False, loc="upper left")

    base = os.path.join(OUT, "fig18_branch_iso_cycle")
    fig.savefig(base + ".pdf")
    fig.savefig(base + ".png", dpi=300)
    plt.close(fig)

    with io.open(FACTS, "w", encoding="utf-8") as fh:
        fh.write("wrote %s.pdf\n" % base)
        fh.write("slope E*sqrt(nu*w1/2) = %.6f\n" % SLOPE)
        for r in rows:
            fh.write("%-20s ft=%.4f Dmf=%.6e Dbar=%.6e ratio=%.3f "
                     "Dfluct=%.6e pred=%.6e obs/pred=%.3f\n"
                     % (r["name"].replace("\\", ""), r["ft"], r["dmf"],
                        r["dbar"], r["dbar"] / r["dmf"], r["dbar"] - r["dmf"],
                        SLOPE * r["ft"],
                        (r["dbar"] - r["dmf"]) / (SLOPE * r["ft"])
                        if r["ft"] > 0 else float("nan")))
        for c in ("B1", "B2", "B3"):
            fh.write("%s: Dfluct=%.6e DSt=%.6e Dfluct/DSt=%.3f n_dom=%d\n"
                     % (c, S[c]["Dfluct"], ST[c]["stokes"],
                        ST[c]["fluct_over_stokes"], ST[c]["n_dom"]))


if __name__ == "__main__":
    main()
