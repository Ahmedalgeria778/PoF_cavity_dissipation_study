# -*- coding: utf-8 -*-
"""Figure 12: grid convergence of the iso-energetic dissipation comparison.

Reads results/p1_gci_iso/p1_gci_raw.csv and writes fig12_gci_updated.pdf/png
into the figures/ directory.

Panel (a): absolute dissipation vs grid resolution.
Panel (b): ratio to the sharp uniform lid (does not converge).
Panel (c): ratio to the corner-regularized uniform lid (converges).
"""
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
RAW = os.path.join(REPO, "results", "p1_gci_iso", "p1_gci_raw.csv")
OUT = os.path.join(REPO, "figures")

STYLE = {
    "uniform": dict(label="uniform lid (sharp)", marker="o",
                    color="0.15", ls="-"),
    "uniform_smooth": dict(label=r"uniform lid (regularized)",
                           marker="v", color="0.55", ls="-."),
    "k1": dict(label=r"$k=1$ ($\sin\pi x$)", marker="s",
               color="tab:blue", ls="-"),
    "k2": dict(label=r"$k=2$ ($\sin 2\pi x$)", marker="^",
               color="tab:red", ls="-"),
    "b1mean": dict(label=r"$B_1$ PINN mean", marker="D",
                   color="tab:green", ls="--"),
}
ORDER = ["uniform", "uniform_smooth", "k1", "k2", "b1mean"]
CONTROLS = ["k1", "k2", "b1mean"]


def load():
    data = {}
    with open(RAW, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            case = row["case"]
            data.setdefault(case, {})[int(row["N"])] = float(row["eps"])
    return data


def ratio_panel(ax, data, ref, title):
    for case in CONTROLS:
        if case not in data or ref not in data:
            continue
        Ns = sorted(set(data[case]) & set(data[ref]))
        ax.plot(Ns, [data[case][n] / data[ref][n] for n in Ns],
                ms=6, lw=1.4, **STYLE[case])
    ax.axhline(1.0, color="0.15", lw=1.0, ls=":")
    ax.set_xscale("log", base=2)
    ax.set_xticks([128, 256, 512])
    ax.set_xticklabels(["128", "256", "512"])
    ax.set_xlabel(r"grid resolution $N$")
    ax.set_title(title, fontsize=10)
    ax.grid(alpha=0.3, ls=":")
    ax.legend(fontsize=8, frameon=False)


def main():
    os.makedirs(OUT, exist_ok=True)
    data = load()

    fig, axes = plt.subplots(1, 3, figsize=(13.2, 3.5))

    ax = axes[0]
    for case in ORDER:
        if case not in data:
            continue
        Ns = sorted(data[case])
        ax.plot(Ns, [data[case][n] for n in Ns], ms=6, lw=1.4, **STYLE[case])
    ax.set_xscale("log", base=2)
    ax.set_xticks([128, 256, 512])
    ax.set_xticklabels(["128", "256", "512"])
    ax.set_xlabel(r"grid resolution $N$")
    ax.set_ylabel(r"integrated dissipation $\varepsilon$")
    ax.set_title("(a) absolute dissipation", fontsize=10)
    ax.grid(alpha=0.3, ls=":")
    ax.legend(fontsize=7.5, frameon=False)

    ratio_panel(axes[1], data, "uniform",
                "(b) normalized to the sharp lid")
    axes[1].set_ylabel(
        r"$\varepsilon/\varepsilon_{\mathrm{uniform}}^{\mathrm{sharp}}$")

    ratio_panel(axes[2], data, "uniform_smooth",
                "(c) normalized to the regularized lid")
    axes[2].set_ylabel(
        r"$\varepsilon/\varepsilon_{\mathrm{uniform}}^{\mathrm{reg}}$")

    fig.tight_layout()
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, f"fig12_gci_updated.{ext}"), dpi=300)
    plt.close(fig)
    print("wrote fig12_gci_updated.pdf/png to", OUT)


if __name__ == "__main__":
    main()
