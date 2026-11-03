# -*- coding: utf-8 -*-
"""New main-text Figs. 1 and 2 of the physics-first version.

Fig. 1  (a) controlled-cavity geometry with distributed wall actuation;
        (b) the stationary lid profiles compared at a common actuation norm.
Fig. 2  spatio-temporal signature of the three identified branches:
        U_lid(x,t) over one forcing period, the instantaneous actuation norm,
        and the modal composition (f1, f2, fm>=3, ft).

All profiles are taken from the archived data of the branch campaign
(results/05_crosscheck_case_study and results/06_branch_figures).
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(HERE, "..", "figures"))
PROJ = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
CAP = os.path.join(PROJ, "results", "06_branch_figures")

plt.rcParams.update({
    "font.size": 9,
    "font.family": "serif",
    "mathtext.fontset": "cm",
    "axes.linewidth": 0.8,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
})

E_STAR = 0.25
DELTA = 0.05


def taper(N=400):
    x = np.linspace(0.0, 1.0, N)
    raw = np.ones(N)
    left = x < DELTA
    right = x > 1.0 - DELTA
    raw[left] = 0.5 * (1.0 - np.cos(np.pi * x[left] / DELTA))
    raw[right] = 0.5 * (1.0 - np.cos(np.pi * (1.0 - x[right]) / DELTA))
    return x, raw


def scaled(raw, x, e=E_STAR):
    e_raw = np.trapezoid(raw ** 2, x)
    return raw * np.sqrt(e / e_raw)


def b1_mean_profile():
    d = np.load(os.path.join(CAP, "capture_B1.npz"), allow_pickle=True)
    x = d["x"]
    u = d["U_lid_series"].mean(axis=0)
    return x, u * np.sqrt(E_STAR / np.trapezoid(u ** 2, x))


def modal_fractions(U, nt_max=8, nm_max=10):
    """Sine-in-x / cosine-in-t projection of a periodic lid series."""
    nt, nx = U.shape
    x = np.linspace(0.0, 1.0, nx)
    tau = np.arange(nt) / nt
    emn = np.zeros((nm_max + 1, nt_max + 1))
    for m in range(1, nm_max + 1):
        sx = np.sin(m * np.pi * x)
        for nn in range(0, nt_max + 1):
            ct = np.cos(2.0 * np.pi * nn * tau)
            a = 2.0 * np.trapezoid(np.trapezoid(U * sx[None, :], x=x, axis=1) * ct, tau)
            if nn == 0:
                emn[m, nn] = 0.5 * a ** 2
            else:
                emn[m, nn] = 0.25 * a ** 2
    tot = emn.sum()
    f1 = emn[1, 0] / tot
    f2 = emn[2, 0] / tot
    f_hi = emn[3:, 0].sum() / tot
    ft = emn[:, 1:].sum() / tot
    return dict(f1=f1, f2=f2, fhi=f_hi, ft=ft, tot=tot, emn=emn)


# ----------------------------------------------------------------------
# Fig. 1
# ----------------------------------------------------------------------
fig = plt.figure(figsize=(7.1, 3.15))
gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.18], wspace=0.30)

ax = fig.add_subplot(gs[0, 0])
ax.set_aspect("equal")
ax.add_patch(Rectangle((0, 0), 1, 1, fill=True, facecolor="0.97",
                       edgecolor="0.25", lw=1.1, zorder=1))
# faint primary vortex
th = np.linspace(0, 2 * np.pi, 200)
ax.plot(0.50 + 0.30 * np.cos(th), 0.54 + 0.30 * np.sin(th),
        color="0.78", lw=0.8, ls="-", zorder=2)
# actuation arrows along the lid
xg = np.linspace(0.04, 0.96, 15)
prof = np.sin(2 * np.pi * xg)
for xx, pp in zip(xg, prof):
    ax.add_patch(FancyArrowPatch((xx, 1.02), (xx, 1.02 + 0.20 * np.sign(pp) * abs(pp)),
                                 arrowstyle="-|>", mutation_scale=7,
                                 color="tab:red" if pp >= 0 else "tab:blue",
                                 lw=1.0, zorder=3))
ax.axhline(1.0, color="0.25", lw=1.4, zorder=4)
ax.text(0.5, 1.42, r"$U_{\mathrm{lid}}(x,t)$", ha="center", fontsize=10)
ax.text(0.5, 1.30, r"distributed tangential actuation", ha="center",
        fontsize=7.5, color="0.35")
ax.text(-0.13, 0.5, r"$y$", va="center", fontsize=9)
ax.text(0.5, -0.13, r"$x$", ha="center", fontsize=9)
ax.text(0.5, 0.5, r"$\nabla\cdot\mathbf{u}=0$", ha="center", va="center",
        fontsize=9, color="0.45")
ax.text(0.5, 0.42, r"$\partial_t\mathbf{u}+(\mathbf{u}\cdot\nabla)\mathbf{u}"
        r"=-\nabla p+Re^{-1}\nabla^2\mathbf{u}$",
        ha="center", va="center", fontsize=6.4, color="0.45")
ax.text(-0.04, 0.5, "no-slip", rotation=90, ha="right", va="center", fontsize=7,
        color="0.3")
ax.text(1.04, 0.5, "no-slip", rotation=-90, ha="left", va="center", fontsize=7,
        color="0.3")
ax.text(0.5, -0.04, "no-slip", ha="center", va="top", fontsize=7, color="0.3")
ax.set_xlim(-0.22, 1.22)
ax.set_ylim(-0.30, 1.52)
ax.axis("off")
ax.text(-0.20, 1.46, "(a)", fontsize=10, fontweight="bold")

ax = fig.add_subplot(gs[0, 1])
x, raw = taper()
xs = np.linspace(0.0, 1.0, 256)
cases = [
    (xs, "uniform lid (sharp)", np.full_like(xs, 0.5), dict(color="0.15", ls="--", lw=1.3)),
    (x, "uniform lid, $\\delta=0.05$", scaled(raw, x), dict(color="0.45", ls="-.", lw=1.3)),
    (xs, "$k=1$: $\\sin\\pi x$", np.sqrt(2 * E_STAR) * np.sin(np.pi * xs),
     dict(color="tab:blue", ls="-", lw=1.6)),
    (xs, "$k=2$: $\\sin 2\\pi x$", np.sqrt(2 * E_STAR) * np.sin(2 * np.pi * xs),
     dict(color="tab:red", ls="-", lw=1.6)),
]
xb, ub = b1_mean_profile()
cases.append((xb, "$B_1$ mean profile", ub, dict(color="tab:green", ls="-", lw=1.8)))
for xa, lab, u, st in cases:
    ax.plot(xa, u, label=lab, **st)
ax.axhline(0, color="0.6", lw=0.6, zorder=1)
ax.set_xlim(0, 1)
ax.set_ylim(-0.95, 0.95)
ax.set_xlabel(r"$x/L$")
ax.set_ylabel(r"$U_{\mathrm{lid}}/U_0$")
ax.set_title(r"stationary modes at $E_{\mathrm{act}}=0.25$", fontsize=9)
ax.legend(fontsize=7, loc="lower left", frameon=False, handlelength=2.4)
ax.text(-0.14, 0.98, "(b)", transform=ax.transAxes, fontsize=10,
        fontweight="bold", va="top")
ax.text(0.03, 0.95, r"$U_{\max}=0.50,\ 0.52,\ 0.71,\ 0.71,\ 0.78$", transform=ax.transAxes,
        fontsize=7, va="top", color="0.3")
fig.savefig(os.path.join(OUT, "fig01_modes.pdf"), bbox_inches="tight")
fig.savefig(os.path.join(OUT, "fig01_modes.png"), dpi=320, bbox_inches="tight")
plt.close(fig)

# ----------------------------------------------------------------------
# Fig. 2
# ----------------------------------------------------------------------
data = {}
for b in ["B1", "B2", "B3"]:
    d = np.load(os.path.join(CAP, f"capture_{b}.npz"), allow_pickle=True)
    data[b] = dict(U=d["U_lid_series"], E=d["E_act_series"])
    data[b].update(modal_fractions(d["U_lid_series"]))
    print(b, {k: round(v, 4) for k, v in data[b].items()
              if k in ("f1", "f2", "fhi", "ft")})

fig = plt.figure(figsize=(7.1, 4.6))
gs = fig.add_gridspec(2, 3, height_ratios=[1.0, 0.85], hspace=0.55, wspace=0.28)
titles = {"B1": r"$B_1$ (Fourier series, $f_t=0.07$)",
          "B2": r"$B_2$ seed 5 ($f_t=1.00$)",
          "B3": r"$B_3$ seed 0 ($f_2=0.52$, $f_t=0.45$)"}
for j, b in enumerate(["B1", "B2", "B3"]):
    ax = fig.add_subplot(gs[0, j])
    U = data[b]["U"]
    tt = np.arange(U.shape[0]) / U.shape[0]
    im = ax.pcolormesh(tt, np.linspace(0, 1, U.shape[1]), U.T,
                       cmap="RdBu_r", vmin=-1.25, vmax=1.25, shading="auto")
    im.set_rasterized(True)
    ax.set_title(titles[b], fontsize=8)
    ax.set_xlabel(r"$t/T$")
    if j == 0:
        ax.set_ylabel(r"$x/L$")
    else:
        ax.set_yticklabels([])
    ax.text(-0.25, 1.05, "(" + "abc"[j] + ")", transform=ax.transAxes,
            fontsize=9, fontweight="bold")
cb = fig.colorbar(im, ax=fig.axes[:3], orientation="horizontal",
                  fraction=0.04, pad=0.35, aspect=60)
cb.set_label(r"$U_{\mathrm{lid}}(x,t)/U_0$ (common scale)", fontsize=8)

ax = fig.add_subplot(gs[1, 0])
for b, c in zip(["B1", "B2", "B3"], ["tab:green", "tab:purple", "tab:orange"]):
    E = data[b]["E"] / E_STAR
    ax.plot(np.arange(E.size) / E.size, E, color=c, lw=1.2, label=f"${b}$")
ax.axhline(1.0, color="0.5", lw=0.7, ls=":")
ax.set_xlim(0, 1)
ax.set_ylim(0, 2.45)
ax.set_xlabel(r"$t/T$")
ax.set_ylabel(r"$E_{\mathrm{act}}(t)/E^\ast$")
ax.legend(fontsize=6.5, frameon=False, ncol=3, loc="upper center",
          columnspacing=0.8, handlelength=1.2)
ax.text(-0.28, 1.02, "(d)", transform=ax.transAxes, fontsize=9, fontweight="bold")

ax = fig.add_subplot(gs[1, 1:3])
xx = np.linspace(0, 1, 256)
for b, c in zip(["B1", "B2", "B3"], ["tab:green", "tab:purple", "tab:orange"]):
    U = data[b]["U"]
    Um = U.mean(axis=0)
    Us = U.std(axis=0)
    ax.plot(xx, Um, color=c, lw=1.4, label=rf"$\langle U_{{\rm lid}}\rangle$, ${b}$")
    ax.fill_between(xx, Um - Us, Um + Us, color=c, alpha=0.18, lw=0)
ax.axhline(0, color="0.6", lw=0.6)
ax.set_xlim(0, 1)
ax.set_ylim(-0.95, 0.95)
ax.set_xlabel(r"$x/L$")
ax.set_ylabel(r"$\langle U_{\mathrm{lid}}\rangle\pm U'_{\mathrm{rms}}$")
ax.legend(fontsize=6.5, frameon=False, loc="lower left", ncol=1,
          handlelength=1.4)
ax.text(-0.10, 1.02, "(e)", transform=ax.transAxes, fontsize=9, fontweight="bold")
ax.text(0.52, 0.06, r"$B_2$: $\max|\langle U_{\mathrm{lid}}\rangle|=0.039$",
        transform=ax.transAxes, fontsize=6.6, color="0.3")
fig.savefig(os.path.join(OUT, "fig02_signatures.pdf"), bbox_inches="tight")
fig.savefig(os.path.join(OUT, "fig02_signatures.png"), dpi=320, bbox_inches="tight")
plt.close(fig)
print("written to", OUT)
