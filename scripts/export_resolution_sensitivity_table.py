"""Ecrire le tableau de sensibilite au raffinement (N=256 -> N=512) des captures
D2, a partir de results/d2_derived/resolution_sensitivity_hold.json.

Ce JSON est lui-meme produit par scripts/compare_n256_n512_d2.py, qui lit les
archives results/09_d2_capture/capture_*_D2_N{256,512}.npz. Aucun nombre n'est
saisi ici. Deux grilles quantifient une VARIATION, pas un ordre de convergence :
le tableau est intitule "grid-refinement sensitivity".

Sortie : supplementary/data_appendix/p4_table_resolution_n512_supp.tex
         label tab:res_sensitivity
"""

import io
import json
import os

SRC = "results/d2_derived/resolution_sensitivity_hold.json"
APP = "supplementary/data_appendix"
OUT = "p4_table_resolution_n512_supp.tex"
ORDER = ["B1", "B2", "B3"]
NAMES = {"B1": r"$B_1$ full series", "B2": r"$B_2$ seed 5",
         "B3": r"$B_3$ seed 0"}


def sci(v, digits=3):
    if v == 0:
        return "$0$"
    m, e = ("%.*e" % (digits - 1, v)).split("e")
    return r"$%s\times10^{%d}$" % (m, int(e))


def per(v, digits=2):
    """Pourcentage signe, mode mathematique : $+5.40\\%$."""
    return "$%s%.{}f\\%%$".format(digits) % ("+" if v >= 0 else "-", abs(v))


def points(v, digits=1):
    """Ecart en points de pourcentage, mode mathematique."""
    return "$%s%.{}f$~pt".format(digits) % ("+" if v >= 0 else "-", abs(v))


d = json.load(io.open(SRC, encoding="utf-8"))
cases, var = d["cases"], d["variation"]

rows = []
for b in ORDER:
    r256, r512, v = cases[b]["256"], cases[b]["512"], var[b]
    rows.append(r"\textbf{%s} & 256 & %s & %s & %s & %.1f & %s & %s & %s & %.1f \\" % (
        NAMES[b], sci(r256["D"]), sci(r256["D_meanfield"]),
        sci(r256["D_fluct"]), 100.0 * r256["fluct_share"], sci(r256["K"]),
        sci(r256["P"]), per(100.0 * r256["balance_resid"]), 100.0 * r256["lid_max_error"]))
    rows.append(r" & 512 & %s & %s & %s & %.1f & %s & %s & %s & %.1f \\" % (
        sci(r512["D"]), sci(r512["D_meanfield"]),
        sci(r512["D_fluct"]), 100.0 * r512["fluct_share"], sci(r512["K"]),
        sci(r512["P"]), per(100.0 * r512["balance_resid"]), 100.0 * r512["lid_max_error"]))
    slip = 100.0 * (r512["lid_max_error"] - r256["lid_max_error"]) / r256["lid_max_error"]
    rows.append(r"\emph{change} & & %s & %s & %s & %s & %s & %s & %s & %s \\\noalign{\smallskip}" % (
        per(100.0 * v["Dbar"]["rel"], 1), per(100.0 * v["D(ubar)"]["rel"], 1),
        per(100.0 * v["D_fluct"]["rel"], 1),
        points(100.0 * v["share_fluct"]["rel"]),
        per(100.0 * v["Kbar"]["rel"], 1), per(100.0 * v["Pbar"]["rel"], 1),
        points(100.0 * (r512["balance_resid"] - r256["balance_resid"])),
        per(slip, 0)))

se_rel = max(cases[b][n]["se_D"] / cases[b][n]["D"] for b in ORDER for n in ("256", "512"))
gap256 = 100.0 * (cases["B1"]["256"]["D"] - cases["B3"]["256"]["D"]) / cases["B3"]["256"]["D"]
gap512 = 100.0 * (cases["B1"]["512"]["D"] - cases["B3"]["512"]["D"]) / cases["B3"]["512"]["D"]
res = {b: 100.0 * var[b]["Dbar"]["rel"] for b in ORDER}

body = r"""\begin{table*}[t]
\centering
\caption{Grid-refinement sensitivity of the temporal captures at $Re=500$ and
$E^\ast=0.25$. Each branch was run twice on the same D2 protocol (Main Sec.~4.2,
Sec.~S4.5): the fundamental of the imposed control is $\omega_1=\pi$ on both grids
because the number of lattice steps per forced period is $N_T=40N$, i.e.\
$10\,240$ at $N=256$ and $20\,480$ at $N=512$, and both runs use $24$ settling
periods and $32$ sampled periods. Two grids quantify a \emph{variation}, not a
convergence order, so no extrapolation and no convergence index is computed here,
and the $N=256$ values remain the ones quoted in the main text.
$\overline D$ is the cycle-mean dissipation, $D(\overline{\mathbf u})$ the same
functional evaluated on the time-mean field, $\overline D_{\mathrm{fluct}}$ their
difference, the next column the fluctuating share of the cycle mean,
$\overline K$ the cycle-mean kinetic energy and $\overline P_{\mathrm{lid}}$ the
lid power recovered at the boundary node. The two right-hand columns are the
balance residual $100(\overline P_{\mathrm{lid}}-\overline D)/\overline D$ and the
largest discrete slip of the velocity boundary condition over the record, in per
cent of the cavity speed. The third row of each block is the $256\to512$ change,
in per cent or in percentage points (pt). The relative standard error of every
$\overline D$ is below @SE@, which is three to four orders of magnitude below the
changes reported: the @D1@, @D2@ and @D3@ moves of $\overline D$ are resolved, and so is
the accompanying halving of the balance residual and the drop of the lid slip,
both consistent with the first-order truncation of the one-sided wall-shear
estimator (Sec.~S4.8). The ordering $B_2>B_1>B_3$ is preserved, while the
$B_1$--$B_3$ separation narrows from @G256@ to @G512@. Generated from
\texttt{results/d2\_derived/resolution\_sensitivity\_hold.json} by
\texttt{scripts/export\_resolution\_sensitivity\_table.py}.}
\label{tab:res_sensitivity}
\footnotesize
\setlength{\tabcolsep}{2pt}
\begin{tabular}{llcccccccc}
\toprule
Control & $N$ & $\overline D$ & $D(\overline{\mathbf u})$
& $\overline D_{\mathrm{fluct}}$ & share (\%) & $\overline K$
& $\overline P_{\mathrm{lid}}$ & residual (\%) & slip (\%)\\
\midrule
@ROWS@
\bottomrule
\end{tabular}
\end{table*}
""".replace("@ROWS@", "\n".join(rows)).replace(
    "@SE@", sci(se_rel, 2)).replace(
    "@D1@", per(res["B1"], 1)).replace(
    "@D2@", per(res["B2"], 1)).replace(
    "@D3@", per(res["B3"], 1)).replace(
    "@G256@", "$%.1f\\%%$" % gap256).replace(
    "@G512@", "$%.1f\\%%$" % gap512)

os.makedirs(APP, exist_ok=True)
path = os.path.join(APP, OUT)
io.open(path, "w", encoding="utf-8").write(
    "% auto-generated by scripts/export_resolution_sensitivity_table.py"
    " -- do not edit\n" + body)
print("wrote", path)
print("Dbar 256->512 : " + "  ".join("%s %+.2f%%" % (b, res[b]) for b in ORDER))
print("max se_rel = %.2e ; B1-B3 gap %.2f%% -> %.2f%%" % (se_rel, gap256, gap512))
