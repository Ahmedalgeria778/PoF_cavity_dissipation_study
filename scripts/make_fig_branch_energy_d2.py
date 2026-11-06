# -*- coding: utf-8 -*-
"""Figure 22: phase-resolved energetic response of the three branches,
built exclusively from results/09_d2_capture/capture_B?_D2_N256.npz
(32 captured periods at N=256, Re=500, recorded every eighth lattice step).

  (a) actuation norm of one forcing period, normalised by the target E*,
  (b) kinetic energy over the first eight periods (log ordinate),
  (c) dissipation: instantaneous, cycle mean with the block-uncertainty band,
      and the dissipation of the time-mean field,
  (d) lid power over the first eight periods, same conventions, annotated with
      the cycle-mean residual of the two recorded signals.

Outputs figures/fig22_branch_energy.pdf/.png.
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
CAP = os.path.join(REPO, "results", "09_d2_capture")
OUT = os.path.join(REPO, "figures")

CASES = ["B1", "B2", "B3"]
COLOURS = {"B1": "tab:blue", "B2": "tab:red", "B3": "tab:green"}
N_SHOW = 8
E_TARGET = 0.25
STRIDE = 8
PERIOD = 10240


def load(case):
    z = np.load(os.path.join(CAP, "capture_%s_D2_N256.npz" % case),
                allow_pickle=True)
    m = json.loads(str(z["meta"].item()))
    u_lid = np.asarray(z["U_lid_series"], dtype=float)
    dx = 1.0 / (u_lid.shape[1] - 1)
    t = np.asarray(z["t_series"], dtype=float)
    n_per_period = PERIOD // STRIDE
    sel = (t - t[0]) / PERIOD
    keep = sel < N_SHOW
    return dict(
        m=m,
        tau=np.arange(u_lid.shape[0], dtype=float) / u_lid.shape[0],
        e_period=(u_lid ** 2).sum(axis=1) * dx,
        k=np.asarray(z["K_series"], dtype=float)[keep],
        d=np.asarray(z["eps_series"], dtype=float)[keep],
        p=np.asarray(z["P_series"], dtype=float)[keep],
        t_over=sel[keep],
        cyc=np.asarray(z["cyc_eps"], dtype=float),
    )


def main():
    os.makedirs(OUT, exist_ok=True)
    data = {c: load(c) for c in CASES}

    fig, axs = plt.subplots(2, 2, figsize=(9.6, 7.0))
    fig.subplots_adjust(left=0.075, right=0.985, top=0.895, bottom=0.085,
                        hspace=0.34, wspace=0.24)

    # ---- (a) actuation norm over one period ----------------------------
    ax = axs[0, 0]
    handles = []
    for c in CASES:
        d = data[c]
        ax.plot(d["tau"], d["e_period"] / E_TARGET, color=COLOURS[c], lw=1.5,
                zorder=3)
        handles.append(plt.Line2D(
            [], [], color=COLOURS[c], lw=2,
            label=r"$%s$  $\overline{E}_{\mathrm{act}}/E^\ast=%.4f$"
                  % (c.replace("B", r"B_"),
                     d["m"]["E_r_realized"] / E_TARGET)))
    ax.axhline(1.0, color="0.45", ls="--", lw=1.2, zorder=2)
    ax.text(0.965, 1.03, r"$E^\ast$", color="0.4", fontsize=9, ha="right")
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 2.55)
    ax.set_xlabel(r"$t/T$", fontsize=11)
    ax.set_ylabel(r"(a)  $E_{\mathrm{act}}(t)/E^\ast$", fontsize=11)
    ax.legend(handles=handles, loc="upper right", fontsize=8.5, frameon=True,
              framealpha=0.9, borderpad=0.5)

    # ---- (b) kinetic energy, first eight periods ------------------------
    ax = axs[0, 1]
    for c in CASES:
        d = data[c]
        ax.plot(d["t_over"], d["k"], color=COLOURS[c], lw=0.9, alpha=0.85,
                zorder=3)
        ax.axhline(d["m"]["K_cycle_mean"], color=COLOURS[c], lw=1.3, ls="--",
                   alpha=0.8, zorder=2)
    ax.set_yscale("log")
    ax.set_xlim(0, N_SHOW)
    ax.set_xlabel(r"$t/T$", fontsize=11)
    ax.set_ylabel(r"(b)  $K(t)=\frac{1}{2}\int_\Omega|\mathbf{u}|^2"
                  r"\,\mathrm{d}\Omega$", fontsize=10)

    # ---- (c) dissipation and (d) lid power ------------------------------
    for col, key, sym, extra in [
            (0, "d", r"$D(t)=\frac{2}{Re}\int_\Omega \mathbf{S}\!:\!\mathbf{S}"
                     r"\,\mathrm{d}\Omega$", None),
            (1, "p", r"$P_{\mathrm{lid}}(t)=\int_0^1 U_{\mathrm{lid}}\,"
                     r"\tau_w\,\mathrm{d}x$", "residual")]:
        ax = axs[1, col]
        for c in CASES:
            d = data[c]
            m = d["m"]
            mean = m["eps_cycle_mean"] if key == "d" else m["P_cycle_mean"]
            ax.plot(d["t_over"], d[key], color=COLOURS[c], lw=0.9, alpha=0.85,
                    zorder=3)
            ax.axhline(mean, color=COLOURS[c], lw=2.6, zorder=4)
            if key == "d":
                blocks = np.array_split(d["cyc"], 4)
                unc = np.std([b.mean() for b in blocks], ddof=1) / 2.0 * 3.182
                ax.fill_between([0, N_SHOW], mean - unc, mean + unc,
                                color=COLOURS[c], alpha=0.25, zorder=2, lw=0)
                ax.axhline(m["eps_meanfield"], color=COLOURS[c], lw=1.1,
                           ls=":", zorder=4)
        ax.set_xlim(0, N_SHOW)
        ax.set_xlabel(r"$t/T$", fontsize=11)
        ax.set_ylabel("(%s)  %s" % ("cd"[col], sym), fontsize=10)
        if extra == "residual":
            txt = []
            for c in CASES:
                m = data[c]["m"]
                r = 100.0 * (m["P_cycle_mean"] / m["eps_cycle_mean"] - 1.0)
                txt.append(r"$B_%s$: $\overline{P}_{\mathrm{lid}}"
                           r"-\overline{D}=%+.1f\%%$" % (c[1], r))
            ax.text(0.97, 0.95, "\n".join(txt), transform=ax.transAxes,
                    ha="right", va="top", fontsize=9.5, linespacing=1.5,
                    color="k")

    handles = [plt.Line2D([], [], color="0.55", lw=1.0, label="instantaneous"),
               plt.Line2D([], [], color="0.45", lw=2.6,
                          label="cycle mean (band: block uncertainty)"),
               plt.Line2D([], [], color="0.45", lw=1.2, ls=":",
                          label=r"$D(\langle\mathbf{u}\rangle)$"),
               plt.Line2D([], [], color="0.45", lw=1.3, ls="--",
                          label="window mean")]
    fig.legend(handles=handles, loc="upper center", ncol=4, fontsize=9.5,
               frameon=False, bbox_to_anchor=(0.5, 1.005))

    base = os.path.join(OUT, "fig22_branch_energy")
    fig.savefig(base + ".pdf")
    fig.savefig(base + ".png", dpi=300)
    plt.close(fig)
    facts = []
    for c in CASES:
        m = data[c]["m"]
        facts.append("%s: series residual %+0.2f%%  D range over cycle "
                     "[%.4e, %.4e]  Kbar=%.4e" %
                     (c, 100.0 * (m["P_cycle_mean"] / m["eps_cycle_mean"] - 1.0),
                      data[c]["d"].min(), data[c]["d"].max(),
                      m["K_cycle_mean"]))
    with open(os.path.join(REPO, "results", "d2_derived",
                           "fig22_facts.txt"), "w", encoding="utf-8") as fh:
        fh.write("wrote %s.pdf\n" % base + "\n".join(facts) + "\n")


if __name__ == "__main__":
    main()
