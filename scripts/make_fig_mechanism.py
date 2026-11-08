# -*- coding: utf-8 -*-
"""
Generator of Main Fig. 4 (fig15_mechanism_iso.pdf): the local mechanism of the
stationary ranking.

Rebuilds, from the stored steady MRT-LBM fields of the three stationary controls
at Re=500, N=512 and matched actuation norm E*=0.25 (uniform lid, k=1, k=2), the
three panels of the figure:

  (a) streamline topology of the steady response;
  (b) local viscous dissipation field phi = nu*(2 S11^2 + 2 S22^2 + 4 S12^2),
      plotted on a colour scale shared by the three controls;
  (c) probability density of the strain-rate magnitude |S| = (2 S:S)^(1/2).

The dissipation definition and the normalisation are those of the solver
integration (nu = 1/Re, dx = 1/(N-1), velocities in units of the reference lid
velocity), so the domain integral of panel (b) reproduces the tabulated epsilon of
the control; the script prints that check against
results/p1_gci_iso/p1_gci_raw.csv, whose rows back Main Table 2.

The three field archives are raw dumps held outside the git tree; their names,
sizes and SHA-256 checksums are recorded in
results/10_fig4_stationary_fields/FIELDS_MANIFEST.md by
scripts/manifest_fig4_fields.py. Point --fields-dir at the directory that holds
them (or set POF_FIELDS_DIR); by default the repository location for them is
used.

Output: manuscript/figures/fig15_mechanism_iso.{pdf,png}.
"""
import argparse
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.gridspec import GridSpec
from matplotlib.colors import Normalize, LogNorm

if not hasattr(np, "trapz"):
    np.trapz = np.trapezoid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIELDS = os.environ.get("POF_FIELDS_DIR",
                        os.path.join(ROOT, "results", "10_fig4_stationary_fields",
                                     "fields"))
RAW = os.path.join(ROOT, "results", "p1_gci_iso", "p1_gci_raw.csv")
OUTDIRS = [os.path.join(ROOT, "manuscript", "figures")]

RE = 500
N = 512
CONTROLS = [
    ("fields_UNem_0p5_Re500_N512.npz", "uniform",
     r"Uniform lid  $U=0.5$"),
    ("fields_S1em_0p707107_Re500_N512.npz", "k1",
     r"$k=1$  $A_1\sin(\pi x)$"),
    ("fields_B1em_0p707107_Re500_N512.npz", "k2",
     r"$k=2$  $A_2\sin(2\pi x)$"),
]
BORDER = 3          # cells excluded from the |S| statistics (boundary layers)
CMAP = "magma"


def load_case(fname):
    z = np.load(os.path.join(FIELDS, fname))
    ux = np.asarray(z["ux"], dtype=float)
    uy = np.asarray(z["uy"], dtype=float)
    psi = np.asarray(z["psi"], dtype=float)
    lid = np.asarray(z["U_lid"], dtype=float)
    return ux, uy, psi, lid


def strain_fields(ux, uy, dx):
    dUdx = np.gradient(ux, dx, axis=1)
    dUdy = np.gradient(ux, dx, axis=0)
    dVdx = np.gradient(uy, dx, axis=1)
    dVdy = np.gradient(uy, dx, axis=0)
    s11, s22, s12 = dUdx, dVdy, 0.5 * (dUdy + dVdx)
    phi = (1.0 / RE) * (2 * s11 ** 2 + 2 * s22 ** 2 + 4 * s12 ** 2)
    smag = np.sqrt(2.0 * (s11 ** 2 + s22 ** 2 + 2.0 * s12 ** 2))
    return phi, smag


def tabulated_eps():
    out = {}
    if not os.path.isfile(RAW):
        return out
    with open(RAW, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if int(row["N"]) == N:
                out[row["case"]] = float(row["eps"])
    return out


def main():
    dx = 1.0 / (N - 1)
    x = np.linspace(0.0, 1.0, N)
    X, Y = np.meshgrid(x, x)
    eps_ref = tabulated_eps()

    data = []
    for fname, key, label in CONTROLS:
        if not os.path.isfile(os.path.join(FIELDS, fname)):
            raise SystemExit(f"missing field file: {fname}")
        ux, uy, psi, lid = load_case(fname)
        phi, smag = strain_fields(ux, uy, dx)
        eps = float(np.trapz(np.trapz(phi, dx=dx, axis=1), dx=dx))
        ref = eps_ref.get(key)
        dev = 100.0 * (eps / ref - 1.0) if ref else float("nan")
        print(f"{label:32s} eps_field={eps:.6e}  eps_table={ref:.6e}  "
              f"dev={dev:+.3f}%  max|S|={smag.max():.3f}  "
              f"<|S|>={smag.mean():.4f}")
        data.append(dict(key=key, label=label, ux=ux, uy=uy, psi=psi,
                         phi=phi, smag=smag, eps=eps, lid=lid))

    phi_max = max(d["phi"].max() for d in data)
    psi_abs = max(np.abs(d["psi"]).max() for d in data)

    fig = plt.figure(figsize=(6.6, 7.1))
    gs = GridSpec(3, 3, height_ratios=[1, 1, 0.62], hspace=0.30, wspace=0.22,
                  left=0.10, right=0.885, top=0.965, bottom=0.085)

    # ---- (a) streamlines --------------------------------------------------
    for j, d in enumerate(data):
        ax = fig.add_subplot(gs[0, j])
        cs = ax.contourf(X, Y, d["psi"], levels=24, cmap="coolwarm",
                        norm=Normalize(-psi_abs, psi_abs), rasterized=True)
        ax.streamplot(X, Y, d["ux"], d["uy"], color="k", linewidth=0.55,
                      density=1.15, arrowsize=0.8, arrowstyle="-")
        ax.set_aspect("equal")
        ax.set_xticks([0, 0.5, 1]); ax.set_yticks([0, 0.5, 1])
        ax.tick_params(labelsize=7)
        if j == 0:
            ax.set_ylabel(r"(a) $\psi$", fontsize=8)
        ax.set_title(d["label"], fontsize=8)

    # ---- (b) local dissipation, shared colour scale ------------------------
    im = None
    phi_axes = []
    phi_min = phi_max * 1e-6
    phi_levels = np.geomspace(phi_min, phi_max, 40)
    for j, d in enumerate(data):
        ax = fig.add_subplot(gs[1, j])
        phi_axes.append(ax)
        im = ax.contourf(X, Y, np.maximum(d["phi"], phi_min), levels=phi_levels,
                        cmap=CMAP, norm=LogNorm(vmin=phi_min, vmax=phi_max),
                        rasterized=True)
        ax.set_aspect("equal")
        ax.set_xticks([0, 0.5, 1]); ax.set_yticks([0, 0.5, 1])
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)
        ax.tick_params(labelsize=7)
        if j == 0:
            ax.set_ylabel(r"(b) $\phi$", fontsize=8)
        ax.text(0.03, 0.94, r"$\varepsilon=%.3f\times10^{-3}$" % (1e3 * d["eps"]),
                transform=ax.transAxes, fontsize=7, va="top", color="w")
    cbar = fig.colorbar(im, ax=phi_axes, fraction=0.036, pad=0.015)
    cbar.set_label(r"$\phi$", fontsize=8)
    cbar.ax.tick_params(labelsize=6)

    # ---- (c) PDF of |S| --------------------------------------------------
    ax = fig.add_subplot(gs[2, :])
    smax = max(np.percentile(d["smag"][BORDER:-BORDER, BORDER:-BORDER], 99.9)
               for d in data)
    bins = np.geomspace(1e-3, smax, 80)
    for d, col in zip(data, ["tab:blue", "tab:green", "tab:red"]):
        s = d["smag"][BORDER:-BORDER, BORDER:-BORDER].ravel()
        ax.hist(s, bins=bins, histtype="step", lw=1.3, color=col,
                label=f"{d['label']}  $\\langle|S|\\rangle_{{\\mathrm{{int}}}}$={s.mean():.3f}")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(r"$|S|=(2\,S_{ij}S_{ij})^{1/2}$", fontsize=8)
    ax.set_ylabel(r"(c) $p(|S|)$", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.legend(fontsize=6.5, frameon=False, loc="upper left")
    ax.set_ylim(1e-2, None)

    for ax_ in fig.axes:
        for sp in ax_.spines.values():
            sp.set_linewidth(0.6)

    for outdir in OUTDIRS:
        if not os.path.isdir(outdir):
            continue
        base = os.path.join(outdir, "fig15_mechanism_iso")
        fig.savefig(base + ".pdf", dpi=250)
        fig.savefig(base + ".png", dpi=300)
        print("  ->", base + ".pdf/.png")
    plt.close(fig)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[2])
    ap.add_argument("--fields-dir", default=None,
                    help="directory holding the three steady N=512 field archives")
    ap.add_argument("--outdir", default=None,
                    help="directory to write the figure into "
                         "(default: manuscript/figures)")
    args = ap.parse_args()
    if args.fields_dir:
        FIELDS = args.fields_dir
    if args.outdir:
        OUTDIRS = [args.outdir]
    main()
