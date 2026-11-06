# -*- coding: utf-8 -*-
"""Sensibilite a la resolution 256 -> 512 sur la campagne D2 (omega=pi).

Deux grilles quantifient une VARIATION, pas un ordre de convergence : un GCI de
Richardson exige au moins trois grilles et le regime asymptotique. Ce qui est
produit ici doit donc etre lu et ecrit comme « grid-refinement sensitivity ».

Le script applique la liste de validation demandee a CHAQUE capture :
  1. frequence fondamentale du CHAMP sur la sonde centrale (omega_1 = pi), et
     celle du signal de dissipation D(t), quadratique donc attendue a 2*omega_1 ;
  2. E_r realise = 0.25 ;
  3. derive de chauffe < 2e-3 ;
  4. periodicite a demi-periode < 2e-3 ;
  5. residu de bilan de puissance |Pbar - Dbar|/Dbar, a rapporter aux DEUX
     resolutions (le stencil de cisaillement de paroi est du premier ordre, il
     doit se reduire quand N augmente) ;
puis compare 256 et 512 separement sur Dbar, D(ubar), D_fluct, Kbar, K_fluct,
Pbar et les parts fluctuantes, chaque variation etant confrontee a l'erreur
d'echantillonnage de la fenetre (AR1) et, a titre de reference, au deplacement
connu du a la commande en escalier (0.11 %).

Usage : py scripts/compare_n256_n512_d2.py                 # trois branches
        py scripts/compare_n256_n512_d2.py --case B2 --forcing hold
"""
import argparse
import json
import os

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
CAP = os.path.join(ROOT, "results", "09_d2_capture")
DER = os.path.join(ROOT, "results", "d2_derived")
CASES = ("B1", "B2", "B3")
TOL_DRIFT = 2e-3
TOL_HALF = 2e-3
TOL_ER = 1e-6
TOL_BALANCE = 2e-2
# seuil de REJET du residu de bilan : au-dela, le budget ne se ferme plus du
# tout et la capture est inutilisable. En dessous, l'ecart est attribue au
# stencil de cisaillement de paroi (premier ordre) et doit se reduire avec N.
TOL_BALANCE_SANITY = 1e-1
# deplacement de Dbar mesure entre commande hold et commande temps-exact (B2,
# N=256, 32 periodes) : ordre de grandeur de ce qu'un changement de protocole de
# commande vaut, a citer quand une variation de grille tombe dessous.
STAIRCASE_REL_REF = 1.14e-3

ARR_KEYS = ("eps_series", "K_series", "P_series", "t_series",
             "cyc_eps", "cyc_K", "cyc_P", "ux_mean", "uy_mean",
             "ux_rms", "uy_rms")
BIG_KEYS = ("phase_half_ux", "phase_half_uy")


def load(case, N, forcing="hold"):
    tag = f"capture_{case}_D2_N{N}" + ("" if forcing == "hold" else f"_{forcing}")
    path = os.path.join(CAP, tag + ".npz")
    if not os.path.exists(path):
        return None
    with np.load(path) as z:
        meta = json.loads(str(z["meta"]))
        for k in ARR_KEYS:
            meta[k] = np.asarray(z[k])
        for k in BIG_KEYS:
            if k in z.files:
                meta[k] = np.asarray(z[k])
        if "probe_ux_center" in z.files:
            meta["probe_ux_center"] = np.asarray(z["probe_ux_center"])
    meta["path"] = path
    return meta


def ar1_se(a):
    """Erreur-type de la moyenne d'une serie auto-corelee (lag-1)."""
    a = np.asarray(a, dtype=np.float64)
    n = len(a)
    s = float(np.std(a, ddof=1))
    ac = a - a.mean()
    r1 = float(np.sum(ac[:-1] * ac[1:]) / np.sum(ac * ac)) if n > 2 else 0.0
    if abs(r1) >= 0.999:
        return float("nan")
    return s / np.sqrt(n) * np.sqrt((1 + r1) / (1 - r1))


def _fft_peak(y, dt, band=(0.5, 40.0)):
    y = np.asarray(y, dtype=np.float64)
    y = y - y.mean()
    n = len(y)
    spec = np.abs(np.fft.rfft(y * np.hanning(n)))
    omega = 2 * np.pi * np.fft.rfftfreq(n, d=dt)
    idx = int(np.argmax(np.where((omega > band[0]) & (omega < band[1]), spec, 0.0)))
    peak = float(omega[idx])
    k0 = int(round(peak / (2 * np.pi / (n * dt))))
    lo, hi = max(k0 - 2, 1), k0 + 3
    frac = float(np.sum(spec[lo:hi] ** 2) / np.sum(spec[1:] ** 2))
    return peak, frac


def measured_omega(c):
    """Pic de la sonde de champ (attendu omega_1) et de D(t) (attendu 2*omega_1)."""
    dt = c["dt_phys"] * c["stride"]
    w1 = c["omega"]
    out = {"target_omega1": w1, "has_probe": "probe_ux_center" in c}
    if out["has_probe"]:
        p, f = _fft_peak(c["probe_ux_center"], dt)
        out.update(field_peak=p, field_fraction=f, field_ratio=p / w1)
    p, f = _fft_peak(c["eps_series"], dt)
    out.update(dissipation_peak=p, dissipation_fraction=f,
               dissipation_ratio=p / w1)
    # critere : le champ doit batre a omega_1 ; si la sonde manque, le pic de D(t)
    # doit batre a omega_1 OU 2*omega_1 (reponse quadratique), jamais davantage.
    cand = [out.get("field_ratio"), out["dissipation_ratio"],
            out["dissipation_ratio"] / 2.0]
    err = min(abs(v - 1.0) for v in cand if v is not None)
    out["frequency_criterion_error"] = err
    return err < 1e-3, out


def line(name, value, tol, higher_is_bad=True):
    v = value if higher_is_bad else abs(value)
    return f"    {name:<34} {value:.3e}  (seuil {tol:.0e}) {'OK ' if v < tol else 'HORS'}"


def dmean_field(ux, uy, N, Re):
    """D(ū) = int |∇ū|² recompté depuis un champ moyen, avec le MEME stencil que
    la capture (eps_field). Sert a (a) verifier la coherence avec meta['eps_meanfield']
    et (b) estimer l'erreur d'echantillonnage de D(ū) par division de la fenetre."""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from run_branch_capture_d2 import eps_field
    return eps_field(np.asarray(ux, float), np.asarray(uy, float),
                     1.0 / (N - 1), 1.0 / Re)


def _time_mean(field):
    """Les champs resolu en phase sont des moyennes par bin ; les bins ont des
    comptages exactement egaux (n_steps = capture*period_lattice, divisible par
    N_PHASE), donc la moyenne des bins reconstitue la moyenne temporelle."""
    a = np.asarray(field, dtype=np.float64)
    return a.mean(axis=0) if a.ndim == 3 else a


def meanfield_error(c):
    """Erreur de D(ū) estimée en comparant le champ moyen de toute la fenêtre à
    celui de la première moitié (phase_half_*). D_fluct = Dbar - D(ū) est pour
    B1 une difference de deux grands nombres quasi egaux : son incertitude n'est
    PAS donnee par la seule erreur de Dbar."""
    N, Re = int(c["N"]), float(c["Re"])
    Dm_full = dmean_field(_time_mean(c["ux_mean"]), _time_mean(c["uy_mean"]), N, Re)
    consistency = abs(Dm_full - float(c["eps_meanfield"])) / float(c["eps_meanfield"])
    if "phase_half_ux" not in c:
        return Dm_full, float("nan"), float("nan"), consistency
    Dm_half = dmean_field(_time_mean(c["phase_half_ux"]),
                          _time_mean(c["phase_half_uy"]), N, Re)
    return Dm_full, Dm_half, abs(Dm_full - Dm_half), consistency


def report(c):
    D = float(c["eps_cycle_mean"])
    Dm = float(c["eps_meanfield"])
    K = float(c["K_cycle_mean"])
    P = float(c["P_cycle_mean"])
    ok, w = measured_omega(c)
    se_D = ar1_se(c["cyc_eps"])
    se_K = ar1_se(c["cyc_K"])
    se_P = ar1_se(c["cyc_P"])
    Dm_re, Dm_half, se_Dm, mf_consist = meanfield_error(c)
    se_Df = float(np.hypot(se_D, se_Dm))
    nu_latt = c.get("nu_latt", 0.05 * int(c["N"]) / float(c["Re"]))
    steps_p = c.get("steps_per_period", c.get("period_lattice"))
    print(f"  [{c['N']}] {os.path.basename(c['path'])}  "
          f"forcing={c.get('forcing','hold')} nu_latt={nu_latt:.6f} "
          f"dt={c['dt_phys']:.4e} steps/P={steps_p}")
    if w["has_probe"]:
        print(f"    omega_1 du CHAMP (sonde centre) = {w['field_peak']:.6f}  "
              f"(objectif {w['target_omega1']:.6f}, ratio {w['field_ratio']:.6f}, "
              f"part du pic {w['field_fraction']:.3f})")
    else:
        print("    (sonde absente sur cette capture : frequence du champ "
              "non mesurable ici ; voir la capture smoke du 2026-11-04)")
    print(f"    omega de D(t)             = {w['dissipation_peak']:.6f}  "
              f"(attendu {w['target_omega1']:.6f} ou {2*w['target_omega1']:.6f}, "
              f"ratio {w['dissipation_ratio']:.3f}, part {w['dissipation_fraction']:.3f}) "
              f"{'OK ' if ok else 'HORS'}")
    print(line("E_r realise - 0.25", abs(c["E_r_realized"] - 0.25), TOL_ER))
    print(line("derive de chauffe", c["drift"], TOL_DRIFT))
    print(line("periodicite demi-periode (max)",
               float(np.max(c["phase_half_diff"])), TOL_HALF))
    bal = (P - D) / D
    print(line("residu bilan |P-D|/D (indicatif)", abs(bal), TOL_BALANCE))
    print(f"    Dbar={D:.6e} (se {se_D:.1e})  D(ubar)={Dm:.6e}  "
          f"D_fluct={D - Dm:.6e} (se {se_Df:.1e})  Dbar/D(ubar)={D/Dm:.3f}")
    print(f"    D(ubar) recompte depuis le champ moyen : ecart relatif "
          f"{mf_consist:.1e} (doit etre ~0, meme formule que la capture)")
    print(f"    erreur de D(ubar) par split-half de fenetre : {se_Dm:.1e} "
          f"({100*se_Dm/Dm:.3f}% de D(ubar))")
    print(f"    part fluctuante D_fluct/Dbar = {100*(D-Dm)/D:.1f} %")
    print(f"    Kbar={K:.6e} (se {se_K:.1e})  K_fluct={c['K_fluct']:.6e}  "
          f"R_K={c['R_K']:.4f}")
    print(f"    Pbar={P:.6e} (se {se_P:.1e})  lid_max_error={c['lid_max_error']:.3e}")
    print(f"    warm={c['warm_periods']:.1f} P ({'stop' if c['warm_stopped'] else 'CAP'}) "
          f"capture={c['capture_periods']} P  {c['seconds']:.0f}s")
    return dict(N=c["N"], file=os.path.basename(c["path"]),
                forcing=c.get("forcing", "hold"), nu_latt=nu_latt,
                steps_per_period=steps_p,
                omega_field=w.get("field_peak"),
                omega_field_ratio=w.get("field_ratio"),
                omega_dissipation=w["dissipation_peak"],
                omega_dissipation_ratio=w["dissipation_ratio"],
                frequency_ok=ok, has_probe=w["has_probe"],
                frequency_criterion_error=w["frequency_criterion_error"],
                E_r=c["E_r_realized"], drift=c["drift"],
                phase_half_max=float(np.max(c["phase_half_diff"])),
                D=D, se_D=se_D, D_meanfield=Dm, se_Dm=se_Dm,
                D_meanfield_recomputed=Dm_re, meanfield_consistency=mf_consist,
                D_fluct=D - Dm, se_Dfluct=se_Df,
                fluct_share=(D - Dm) / D, ratio_D=D / Dm,
                K=K, se_K=se_K, K_fluct=c["K_fluct"], R_K=c["R_K"],
                P=P, se_P=se_P, balance_resid=bal,
                lid_max_error=c["lid_max_error"],
                warm_stopped=bool(c["warm_stopped"]),
                resumed_from_checkpoint=bool(c.get("resumed_from_checkpoint", False)),
                warm_periods=c["warm_periods"],
                capture_periods=c["capture_periods"], seconds=c["seconds"])


def gate(r):
    """Porte d'acceptation d'UNE capture. Aucun chiffre ne doit entrer dans le
    manuscrit si l'une de ces conditions tombe a faux : le message renvoie la
    liste de validation demandee, critere par critere."""
    fails = []
    if not r["frequency_ok"]:
        fails.append(f"frequence du champ hors criterion "
                     f"(erreur {r['frequency_criterion_error']:.1e})")
    if abs(r["E_r"] - 0.25) >= TOL_ER:
        fails.append(f"E_r={r['E_r']:.9f} != 0.25")
    if not r["drift"] < TOL_DRIFT:
        fails.append(f"derive de chauffe {r['drift']:.2e} >= {TOL_DRIFT:.0e}")
    if not r["phase_half_max"] < TOL_HALF:
        fails.append(f"periodicite demi-periode {r['phase_half_max']:.2e} "
                     f">= {TOL_HALF:.0e}")
    # le residu de bilan n'est PAS un critere de validite de la capture : il
    # mesure l'erreur d'estimation du cisaillement de paroi (stencil du premier
    # ordre), pas la justesse de Dbar. B1 est a -2,8 % a N=256 et le papier le
    # rapporte comme mesure. On ne rejette qu'une fermeture de budget franchement
    # anormale ; la comparaison utile est 256 vs 512, ou le stencil doit diviser
    # ce residu par ~2.
    if not abs(r["balance_resid"]) < TOL_BALANCE_SANITY:
        fails.append(f"fermeture du budget {100*abs(r['balance_resid']):.1f}% "
                     f">= {100*TOL_BALANCE_SANITY:.0f}% : le bilan P-D ne se "
                     f"ferme pas, la capture n'est pas exploitable")
    if not r["meanfield_consistency"] < 1e-12:
        fails.append(f"D(ubar) non reproductible depuis le champ moyen "
                     f"(ecart {r['meanfield_consistency']:.1e})")
    if not r["warm_stopped"]:
        fails.append("chauffe interrompue par le plafond de periodes, pas par "
                     "le critere de derive")
    if not r["se_D"] == r["se_D"] or not np.isfinite(r["se_D"]):
        fails.append("erreur-type de Dbar indisponible")
    return fails


def gate_diag(r):
    """Avertissements non bloquants : ce sont des ecarts dont l'origine est
    connue et qui doivent se reduire quand N augmente, pas des defauts de
    capture. Ils sont signales pour qu'aucun chiffre ne parte au manuscrit sans
    que l'explication ait ete ecrite."""
    out = []
    if abs(r["balance_resid"]) >= TOL_BALANCE:
        out.append(f"residu de bilan {100*r['balance_resid']:+.2f}% au-dessus du "
                   f"seuil indicatif de {100*TOL_BALANCE:.0f}% : stencil de "
                   f"cisaillement de paroi du premier ordre, a confronter a "
                   f"N=512 (division par ~2 attendue)")
    if not r["has_probe"]:
        out.append("sonde de champ absente : frequence du champ non verifiee "
                   "sur cette capture")
    return out


def variation(rows, label, key, se_key=None):
    a, b = rows[256][key], rows[512][key]
    rel = (b - a) / a
    if se_key:
        ea = rows[256][se_key] / abs(a)
        eb = rows[512][se_key] / abs(b)
        se_rel = float(np.hypot(ea, eb))
        if not np.isfinite(se_rel):
            verdict = "se indisponible"
        else:
            verdict = "resolue" if abs(rel) > 3 * se_rel else "sous 3 sigma"
    else:
        se_rel = float("nan")
        verdict = "-"
    print(f"    {label:<14} {a:.6e} -> {b:.6e}   {100*rel:+.3f}%  "
          f"(se_rel {se_rel:.1e})  {verdict}")
    return dict(from_256=a, to_512=b, rel=rel, se_rel=se_rel, verdict=verdict)


def compare(all_rows):
    """Tableau 256 -> 512 par branche, puis stabilité du classement entre branches."""
    summary = {}
    for case, rows in all_rows.items():
        if 256 not in rows or 512 not in rows:
            continue
        print(f"  variation 256 -> 512 pour {case} (grid-refinement sensitivity, "
              f"PAS un GCI) :")
        v = {}
        for key, label, se in (("D", "Dbar", "se_D"),
                               ("D_meanfield", "D(ubar)", "se_Dm"),
                               ("D_fluct", "D_fluct", "se_Dfluct"),
                               ("K", "Kbar", "se_K"),
                               ("K_fluct", "K_fluct", None),
                               ("P", "Pbar", "se_P")):
            v[label] = variation(rows, label, key, se)
        v["share_fluct"] = dict(from_256=rows[256]["fluct_share"],
                                to_512=rows[512]["fluct_share"],
                                rel=rows[512]["fluct_share"] - rows[256]["fluct_share"])
        print(f"    part fluctuante  {100*rows[256]['fluct_share']:.1f}% -> "
              f"{100*rows[512]['fluct_share']:.1f}%")
        print(f"    residu bilan    {100*rows[256]['balance_resid']:.2f}% -> "
              f"{100*rows[512]['balance_resid']:.2f}%  "
              f"({'reduit' if abs(rows[512]['balance_resid']) < abs(rows[256]['balance_resid']) else 'NON reduit'})")
        summary[case] = v
    if len(summary) == 3:
        print("  classement des branches, et ecart B1 vs B3 (la question qui "
              "justifie le run N=512) :")
        for N in (256, 512):
            d = {c: all_rows[c][N]["D"] for c in CASES}
            order = sorted(d, key=lambda c: d[c], reverse=True)
            gap13 = (d["B1"] - d["B3"]) / d["B3"]
            s1 = all_rows["B1"][N]["se_D"] / d["B1"]
            s3 = all_rows["B3"][N]["se_D"] / d["B3"]
            print(f"    N={N:<4} {' > '.join(order)}   B1/B3 - 1 = "
                  f"{100*gap13:+.2f}% (se {100*np.hypot(s1, s3):.1e}%)")
        d256 = {c: all_rows[c][256]["D"] for c in CASES}
        d512 = {c: all_rows[c][512]["D"] for c in CASES}
        same = sorted(d256, key=d256.get, reverse=True) == \
               sorted(d512, key=d512.get, reverse=True)
        print(f"    classement preserve 256 vs 512 : {'OUI' if same else 'NON'}")
        rel = {c: (d512[c] - d256[c]) / d256[c] for c in CASES}
        spread = max(rel.values()) - min(rel.values())
        print(f"    ecarts relatifs 256->512 : " +
              "  ".join(f"{c} {100*rel[c]:+.2f}%" for c in CASES))
        print(f"    dispersion des trois ecarts = {100*spread:.2f} pt ; "
              f"reference protocole (escalier) = {100*STAIRCASE_REL_REF:.2f} pt")
        summary["ranking_preserved"] = same
        summary["rel_change"] = rel
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", default="all", choices=("all",) + CASES)
    ap.add_argument("--forcing", default="hold", choices=("hold", "exact"))
    args = ap.parse_args()
    cases = CASES if args.case == "all" else (args.case,)
    all_rows = {}
    gates = {}
    diags = {}
    absent = []
    for case in cases:
        print(f"===== {case} =====")
        r = {}
        for N in (256, 512):
            c = load(case, N, args.forcing)
            if c is None:
                print(f"  [{N}] ABSENT (results/09_d2_capture/"
                      f"capture_{case}_D2_N{N}"
                      f"{'' if args.forcing=='hold' else '_'+args.forcing}.npz)")
                absent.append(f"{case}/N{N}")
                continue
            r[N] = report(c)
            gates[f"{case}/N{N}"] = gate(r[N])
            diags[f"{case}/N{N}"] = gate_diag(r[N])
        all_rows[case] = r
    print("=" * 72)
    summary = compare(all_rows)
    print("===== porte d'acceptation (toute capture doit passer) =====")
    for key in sorted(gates):
        fails = gates[key]
        print(f"  {key:<10} {'ACCEPTEE' if not fails else 'REJETEE'}")
        for w in diags[key]:
            print(f"      ! {w}")
        for f in fails:
            print(f"      - {f}")
    for key in sorted(absent):
        print(f"  {key:<10} ABSENTE")
    dest = os.path.join(DER, f"resolution_sensitivity_{args.forcing}.json")
    os.makedirs(DER, exist_ok=True)
    with open(dest, "w", encoding="utf-8") as fh:
        json.dump({"cases": all_rows, "variation": summary,
                   "gates": gates, "gate_warnings": diags,
                   "absent": sorted(absent),
                   "staircase_reference_rel": STAIRCASE_REL_REF,
                   "wording": "grid-refinement sensitivity (not a GCI)"},
                  fh, indent=2, sort_keys=True)
    print("->", dest)
    if any(gates[k] for k in gates):
        raise SystemExit(1)
    if absent:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
