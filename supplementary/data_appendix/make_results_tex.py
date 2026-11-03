# -*- coding: utf-8 -*-
"""Génère Paper2_all_campaigns_results.tex : toutes les tables de toutes les campagnes Paper 2."""
import csv, os, re

BASE = r"C:\Users\kings\OneDrive\Documents\Default Project\papier 2 date_14_09_2026\Paper2_branch_selection\results"
OUT = r"C:\Users\kings\OneDrive\Documents\Default Project\papier 2 date_14_09_2026\Paper2_branch_selection\data_appendix\Paper2_all_campaigns_results.tex"

HDR = {
    "point_id": "point", "E_star": "$E^*$", "E_target": "$E_t$",
    "lambda_var": "$\\lambda_v$", "lambda_b": "$\\lambda_b$",
    "N_seeds": "$N_s$", "n_B1": "$n_1$", "n_B2": "$n_2$", "n_B3": "$n_3$",
    "n_NA": "$n_{NA}$", "P_B1": "$P_1$", "P_B2": "$P_2$", "P_B3": "$P_3$",
    "point_label_max": "label", "label_confidence": "conf",
    "needs_refinement": "affin.", "escalation_to_10": "esc10",
    "E_r": "$E_r$", "E_error": "$E_e$", "f_2": "$f_2$", "f_t": "$f_t$",
    "C_3": "$C_3$", "eps": "$\\epsilon$", "C3": "$C_3$", "A_2": "$A_2$",
    "A1": "$A_1$", "A2": "$A_2$", "A3": "$A_3$", "A4": "$A_4$",
    "branch_id": "id", "label_beh": "branch", "dominant_i": "$i$",
    "dominant_j": "$j$", "E_total": "$E_t$", "basis_type": "base",
    "L_total": "$L$", "L_pde": "$L_{pde}$", "L_bc": "$L_{bc}$",
    "L_diss": "$L_d$", "L_ctrl": "$L_c$", "L_var": "$L_\\lambda$",
    "L_re": "$L_{Re}$", "branch": "branch", "dominant_mode": "mode",
    "converged": "conv.", "modal_coverage": "cov.",
    "reconstruction_rmse": "rmse",
    "f2_mean": "$\\bar{f}_2$", "f2_median": "med $f_2$",
    "ft_mean": "$\\bar{f}_t$", "ft_median": "med $f_t$",
    "C3_mean": "$\\bar{C}_3$", "E_r_mean": "$\\bar{E}_r$",
    "nE_r_mean": "$\\bar{E}_r^n$", "dominant_modes": "modes",
    "converged_frac": "$r_c$", "cfd_verified": "CFD", "rep_cell": "repr.",
    "_mode_i": "$i$",
    "f_2_mean": "$\\bar{f}_2$", "f_t_mean": "$\\bar{f}_t$",
    "n": "$n$", "AR": "AR", "seed": "s", "N_MX": "$N_{MX}$",
    "N_MT": "$N_{MT}$",
    "study": "étude", "mean_count": "$\\bar{n}$", "mode_dom": "mode",
    "mode_frac": "$f_{dom}$", "mode_rms": "rms", "mode_rms_frac": "$r_{rms}$",
    "iters": "$n_{it}$", "period": "T", "lockin_final": "lock-in",
    "K": "$K$", "Z": "$Z$", "K_fluct": "$K_{fl}$", "Kf_over_K": "$K_f/K$",
    "n_cycles": "$n_{cy}$", "last_residual": "res.", "control": "contrôle",
    "eps_dissipation": "$\\epsilon_{dis}$", "K_kinetic": "$K_{kin}$",
    "Delta_eps_W": "$\\Delta\\epsilon$", "A_eps_W2": "$A_\\epsilon$",
    "R_K_W2": "$R_K$", "Delta_K": "$\\Delta K$", "K_mean_W2": "$\\bar{K}$",
    "Delta_RK": "$\\Delta R_K$", "eps_bar_W2": "$\\bar{\\epsilon}$",
    "n_periods_total": "$n_{pt}$", "n_periods_window": "$n_{pw}$",
    "pair": "paire", "eps_A": "$\\epsilon_A$", "eps_B": "$\\epsilon_B$",
    "Delta_eps_rel": "$\\Delta\\epsilon_{rel}$", "GCI_256": "GCI256",
    "GCI_512": "GCI512", "verdict": "verdict",
    "iters_run": "$n_{it}$", "n_cycles_recorded": "$n_{cy}$",
    "eps_mean_field": "$\\bar{\\epsilon}$", "K_mean_field": "$\\bar{K}$",
    "Z_mean_field": "$\\bar{Z}$",
    "E_modes_sum": "$\\sum E_m$", "domain_area": "A", "mode2_fraction": "$m_2$",
    "fourier_mode2_fraction": "$m_2^F$", "temporal_fraction": "$m_t$",
    "energy_final": "$E_f$", "pc1": "PC1", "pc2": "PC2",
    "cl_hc": "$c_{HC}$", "cl_db": "$c_{DB}$", "cl_km": "$c_{KM}$",
    "A10": "$A_{10}$", "A20": "$A_{20}$", "A30": "$A_{30}$", "A40": "$A_{40}$",
    "A50": "$A_{50}$", "A60": "$A_{60}$", "A70": "$A_{70}$", "A80": "$A_{80}$",
    "Efrac_0": "$E^f_{0J}$", "Efrac_1": "$E^f_{1J}$", "Efrac_2": "$E^f_{2J}$",
    "Efrac_3": "$E^f_{3J}$", "Efrac_4": "$E^f_{4J}$",
}
for _j in range(5):
    HDR[f"Efrac_{_j}"] = "$E^f_{%dJ}$" % _j


def esc(s):
    for ch, r in [("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"),
                  ("#", r"\#"), ("$", r"\$"), ("_", r"\_"),
                  ("{", r"\{"), ("}", r"\}"), ("^", r"\^{}")]:
        s = s.replace(ch, r)
    return s


def fmt(v):
    if v is None:
        return "--"
    s = str(v).strip()
    if s == "":
        return "--"
    if s in ("NA", "nan", "None", "NaN"):
        return r"\textit{NA}"
    if s in ("True",):
        return "Oui"
    if s in ("False",):
        return "Non"
    try:
        f = float(s)
    except ValueError:
        return esc(s)
    if f == 0.0:
        return "0"
    if abs(f) < 1e-4 or abs(f) >= 1e5:
        return "%.3e" % f
    return "%.3g" % f


def head(c):
    if c in HDR:
        return HDR[c]
    m = re.fullmatch(r"Efrac_(\d)_(\d)", c)
    if m:
        return "$E^f_{%s%s}$" % (m.group(1), m.group(2))
    m = re.fullmatch(r"native_c_(\d)_(\d)", c)
    if m:
        return "$c^{*}_{%s%s}$" % (m.group(1), m.group(2))
    m = re.fullmatch(r"c_(\d)_(\d)", c)
    if m:
        return "$c_{%s%s}$" % (m.group(1), m.group(2))
    return esc(c.replace("_", r"\_"))


def read_rows(fname):
    p = os.path.join(BASE, fname)
    with open(p, encoding="utf-8") as fh:
        return list(csv.DictReader(fh)), list(csv.reader(open(p, encoding="utf-8")))[0]


def table_src(fname):
    return "\\texttt{%s}" % fname.replace("_", "\\_")


def longtable(rows, cols, capt, lab, landscape=False, preformatted=False,
              fontsize="\\scriptsize", widths=None):
    n = len(cols)
    if not rows:
        return ""
    colspec = "*{%d}{l}" % n
    if widths:
        colspec = " ".join("p{%scm}" % w for w in widths)
    body = []
    if landscape:
        body = ["\\begin{landscape}",
                "\\begingroup\\tiny",
                "    \\setlength{\\tabcolsep}{1.2pt}",
                "    \\begin{longtable}{%s}" % colspec,
                "    \\caption{%s}\\\\" % capt,
                "    \\label{%s}\\\\" % lab,
                ]
    else:
        body = [
            "\\begingroup\\%s" % fontsize[1:],
            "    \\setlength{\\tabcolsep}{2pt}",
            "    \\begin{longtable}{%s}" % colspec,
            "    \\caption{%s}\\\\" % capt,
            "    \\label{%s}\\\\" % lab,
        ]
    hdr = " & ".join(head(c) for c in cols)
    body.append("    \\toprule\n    %s \\\\\n    \\midrule\n    \\endhead" % hdr)
    body.append("    \\bottomrule\n    \\endlastfoot")
    for r in rows:
        if preformatted:
            cells = [r.get(c, "---") for c in cols]
        else:
            cells = [fmt(r.get(c, "")) for c in cols]
        body.append("    %s \\\\" % " & ".join(cells))
    body.append("    \\end{longtable}")
    body.append("\\endgroup")
    if landscape:
        body.append("\\end{landscape}")
    return "\n".join(body) + "\n"


out = []
out.append(r"""% Auto-généré par make_results_tex.py — ne pas éditer à la main.
\documentclass[11pt,a4paper]{article}
\usepackage[margin=1.5cm]{geometry}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage{pdflscape}
\usepackage{parskip}
\usepackage{fontspec}
\usepackage{amsmath}
\sloppy
\setlength{\LTleft}{0pt}
\setlength{\LTright}{0pt}
\newcommand{\ruler}{\noindent\rule{\linewidth}{0.4pt}}
\begin{document}
\begin{center}
{\LARGE\bfseries Résultats complets de toutes les campagnes --- Paper 2}\\[6pt]
{\large Branch selection pour équilibres de Navier--Stokes basse dimension}\\[4pt]
Document de données --- 15 septembre 2026
\end{center}
\ruler
""")

# ---- Vue d'ensemble ----
overview_head = ["Campagne", "Étude", "Répertoire", "Courses", "Seeds/point", "Points", "Paramètres"]
overview_rows = [
    ["1. Carte (Re, $E^*$)", "phase1\\_re\\_estarmap", "01\\_ReE\\_star\\_map",
     "185", "5 (15--20)", "30 cellules", "Re $\\in$ {100,300,500,700,900,1000} ; $E^*$ $\\in$ {0.1,0.25,0.5,1,2} ; $\\lambda_v{=}1$, $\\lambda_b{=}0$"],
    ["2. Sensibilité $\\lambda_v$", "lambda\\_var sweep", "02\\_lambda\\_var",
     "90", "5", "3 $\\times$ 6", "$\\lambda_v$ $\\in$ {0,0.25,0.5,1,2,5} ; (500,0.25), (700,2), (1000,1)"],
    ["3. Classification", "branch classification", "03\\_branch\\_classification",
     "185 (réutilisés)", "5", "3 classes", "métriques $f_2$, $f_t$, $C_3$, $E_r$ ; validation CFD"],
    ["4. Validation LBM", "indep validation", "03\\_indep\\_validation",
     "3 contrôles", "1", "3 contrôles", "équivalence de performance (CFD) ; fenêtres ; GCI"],
    ["5. Séparabilité (repères)", "landmark sep.", "00\\_landmark\\_separability",
     "10 repères", "1", "10", "empreintes modales des points de repère"],
    ["Total", "---", "---", "285 courses + 10 repères", "---", "---", "données complètes dans les CSV"],
]
ov_rows = [dict(zip(overview_head, r)) for r in overview_rows]
out.append(longtable(ov_rows, overview_head,
                     "Vue d'ensemble des campagnes Paper 2 et des jeux de données produits.",
                     "tab:overview", preformatted=True, widths=["1.1", "2.3", "2.1", "1.3", "0.9", "1.1", "7.2"]))

# ---- Campagne 1 ----
out.append(r"\section{Campagne 1 --- Carte (Re, $E^*$) : 185 courses, 30 cellules}")
out.append(r"\subsection{Probabilités de bassin agrégées par cellule}")
rows, _ = read_rows("01_ReE_star_map/branch_points.csv")
cols = ["point_id", "Re", "E_star", "AR", "lambda_var", "lambda_b", "N_seeds",
        "n_B1", "n_B2", "n_B3", "n_NA", "P_B1", "P_B2", "P_B3",
        "point_label_max", "label_confidence", "needs_refinement", "escalation_to_10"]
out.append(longtable(rows, cols,
    "Probabilités $P(B_k)$ par cellule --- %d cellules, %s (5 seeds, escalate 15--20). "
    "Abréviations : label = branche majoritaire, conf = confiance du label, affin. = raffinement requis, esc10 = passage à 10 seeds." % (len(rows), table_src("branch_points.csv")),
    "tab:p1_points", landscape=True))

out.append(r"\subsection{Statistiques de bassin avec intervalles de confiance}")
rows, _ = read_rows("01_ReE_star_map/phase1_basin_stats.csv")
cols = ["Re", "E_star", "n", "p_B1", "lo_B1", "hi_B1", "p_B2", "lo_B2", "hi_B2",
        "p_B3", "lo_B3", "hi_B3", "H_N"]
out.append(longtable(rows, cols,
    "Estimation de bassin et intervalle de confiance 95\\%% --- %s ; entropie normalisée $H_N$." % table_src("phase1_basin_stats.csv"),
    "tab:p1_basins"))

out.append(r"\subsection{Détail par course --- métriques de classification}")
rows, _ = read_rows("01_ReE_star_map/branch_runs.csv")
cols = ["point_id", "study", "Re", "E_star", "AR", "lambda_var", "lambda_b", "seed",
        "E_r", "f_2", "f_t", "A_2", "C_3", "eps", "branch_id", "label_beh",
        "dominant_i", "dominant_j", "E_total", "basis_type"]
out.append(longtable(rows, cols,
    "Métriques par course (classification) --- %d courses, %s." % (len(rows), table_src("branch_runs.csv")),
    "tab:p1_runs", landscape=True))

out.append(r"\subsection{Détail complet par course --- pertes, amplitudes, modes}")
rows, _ = read_rows("01_ReE_star_map/phase1_all_results.csv")
cols = ["Re", "E_target", "E_star", "seed", "point_id", "N_MX", "N_MT", "AR",
        "lambda_var", "lambda_b", "E_r", "E_error", "f_2", "f_t", "A1", "A2", "A3", "A4",
        "C3", "epsilon", "L_total", "L_pde", "L_bc", "L_diss", "L_ctrl", "L_var", "L_re",
        "branch", "branch_id", "dominant_i", "dominant_j", "dominant_mode", "converged"]
out.append(longtable(rows, cols,
    "Détail complet des pertes et modes --- %d courses, %s. "
    "$L$: perte totale ; $L_{pde/bc/d/c/\\lambda/Re}$: composantes ; $E_e=|E_r-E^*|/E^*$." % (len(rows), table_src("phase1_all_results.csv")),
    "tab:p1_all", landscape=True))

# ---- Campagne 2 ----
out.append("\\section{Campagne 2 --- Sensibilité à $\\lambda_v$ : 90 courses, 3 cellules $\\times$ 6 valeurs}")
out.append(r"\subsection{Probabilités de bassin agrégées par point}")
rows, _ = read_rows("02_lambda_var/branch_points_lambda_var.csv")
cols = ["point_id", "Re", "E_star", "AR", "lambda_var", "lambda_b", "N_seeds",
        "n_B1", "n_B2", "n_B3", "n_NA", "P_B1", "P_B2", "P_B3",
        "point_label_max", "label_confidence", "needs_refinement", "escalation_to_10"]
out.append(longtable(rows, cols,
    "Probabilités $P(B_k)$ --- %d points, %s." % (len(rows), table_src("branch_points_lambda_var.csv")),
    "tab:lv_points", landscape=True))

out.append(r"\subsection{Détail par course}")
rows, _ = read_rows("02_lambda_var/branch_runs_lambda_var.csv")
cols = ["point_id", "study", "Re", "E_star", "AR", "lambda_var", "lambda_b", "seed",
        "E_r", "f_2", "f_t", "A_2", "C_3", "eps", "branch_id", "label_beh"]
out.append(longtable(rows, cols,
    "Métriques par course ($\\lambda_v$) --- %d courses, %s." % (len(rows), table_src("branch_runs_lambda_var.csv")),
    "tab:lv_runs", landscape=True))

# ---- Campagne 3 ----
out.append(r"\section{Campagne 3 --- Classification des branches}")
rows, _ = read_rows("03_branch_classification/branch_classification_summary.csv")
cols = ["branch", "n", "f2_mean", "f2_median", "ft_mean", "ft_median",
        "C3_mean", "E_r_mean", "nE_r_mean", "dominant_modes", "converged_frac",
        "cfd_verified", "rep_cell"]
out.append(longtable(rows, cols,
    "Résumé par classe de branche --- %s, %d classes." % (table_src("branch_classification_summary.csv"), len(rows)),
    "tab:classif", landscape=True))

# ---- Campagne 4 ----
out.append(r"\section{Campagne 4 --- Validation indépendante (LBM / CFD)}")
for fname, lab, title in [
    ("03_indep_validation/phase1d_validation.csv", "tab:v1", "Systèmes de contrôle (phase 1d) --- validation"),
    ("03_indep_validation/phase1d_validation_regen.csv", "tab:v1r", "Systèmes de contrôle régénérés (cycles complets)"),
    ("03_indep_validation/perf_equivalence.csv", "tab:v2", "Équivalence de performance des stimuli"),
    ("03_indep_validation/perf_equivalence_pairs.csv", "tab:v2p", "Paires d'équivalence et GCI"),
    ("03_indep_validation/window_statistics.csv", "tab:v3", "Statistiques de fenêtre"),
    ("03_indep_validation/window_statistics_regen.csv", "tab:v3r", "Statistiques de fenêtre régénérées"),
]:
    rows_t, head_total = read_rows(fname)
    out.append(longtable(rows_t, head_total,
        "%s --- %d lignes, %s." % (title, len(rows_t), table_src(os.path.basename(fname))),
        lab, landscape=True))

# ---- Appendice ----
out.append(r"\appendix")
out.append(r"\section{Annexe A --- Décomposition modale : 186 enregistrements}")
rows_t, head_total = read_rows("01_ReE_star_map/mode_analysis.csv")
base_cols = ["point_id", "Re", "E_star", "seed", "branch_id", "label_beh", "E_total",
             "modal_coverage", "dominant_i", "dominant_j", "reconstruction_rmse",
             "A10", "A20", "A30", "A40", "A50", "A60", "A70", "A80"]
efrac_cols = ["Efrac_0", "Efrac_1", "Efrac_2", "Efrac_3", "Efrac_4"]
rows_long = []
for r in rows_t:
    for i in range(6):
        row = {c: r[c] for c in base_cols}
        for j in range(5):
            row["Efrac_%d" % j] = r["Efrac_%d_%d" % (i, j)]
        row["_mode_i"] = str(i)
        rows_long.append(row)
head_all = base_cols + ["_mode_i"] + efrac_cols
out.append(longtable(rows_long, head_all,
    "Décomposition modale --- %d points, %d lignes (6 modes $i$ par point, colonnes $E^f_{iJ}$ pour $J{=}0..4$), %s." % (len(rows_t), len(rows_long), table_src("mode_analysis.csv")),
    "tab:modedec", landscape=True))

out.append(r"\section{Annexe B --- Séparabilité des points de repère : 10 points}")
rows_t, head_total = read_rows("00_landmark_separability/landmark_blabels.csv")
cols = ["Re", "E_total", "E_modes_sum", "modal_coverage", "domain_area",
        "A10", "A20", "A30", "A40", "A50", "A60", "A70", "A80",
        "mode2_fraction", "fourier_mode2_fraction", "temporal_fraction",
        "dominant_i", "dominant_j", "reconstruction_rmse",
        "energy_final", "E_r", "f_2", "f_t", "A_2", "eps", "C_3",
        "label_beh", "cl_hc", "cl_db", "cl_km", "pc1", "pc2", "branch_id",
        "basis_type", "seed"]
out.append(longtable(rows_t, cols,
    "Points de repère --- %d points, %s (colonnes brutes $c_{ij}$, $c^{*}_{ij}$ omises)." % (len(rows_t), table_src("landmark_blabels.csv")),
    "tab:landmark", landscape=True))

out.append(r"""\end{document}
""")

with open(OUT, "w", encoding="utf-8") as fh:
    fh.write("\n\n".join(out))
print("wrote", OUT, "|", len(out), "blocs")