# -*- coding: utf-8 -*-
"""Campagne D2 : B1/B2/B3 a omega=pi (T_phys=2), N=256 ou N=512.

Protocole temporel (identique aux deux resolutions, seul le pas lattice change)
-------------------------------------------------------------------------------
La forme d'onde du PINN est une fonction continue
    U(x,t) = sum_{i=0..5} sum_{j=0..4} c_ij sin((i+1) pi x) cos(j pi t)
sur T=2, echantillonnee sur 256 temps (NT_WAVE) en endpoint=False. Le solveur
doit jouer un pas lattice de duree dt_phys = U_ref/N ; pour que la periode
physique reste T=2 (donc omega_1 = pi) a n'importe quelle resolution il faut

    steps_per_period = T / dt_phys = T*N/U_ref = 40*N
    SLOWDOWN         = steps_per_period / NT_WAVE = N/6.4   (40 a 256, 80 a 512)

soit T_phys = 2.0 et omega_1 = pi aux DEUX resolutions : la carte temporelle
est preservere par le raffinement (contrairement aux anciens runs N=512, qui
jouaient 256 echantillons par pas lattice et derivaient a omega_1 = 80 pi).

Commande au solveur (--forcing)
--------------------------------
hold  : chaque echantillon est maintenu SLOWDOWN pas (np.repeat). C'est ce qui
        a produit les captures N=256 existantes ; les fichiers N=512 de
        reference sont produits avec ce mode pour rester comparables.
exact : la commande est evaluee a CHAQUE pas lattice a partir des c_ij, sans
        escalier. Le defaut de l'escalier est borne numeriquement par
        lid_command.hold_vs_exact : il modifie la vitesse de paroi locale de
        2.6 % au pire (B2) mais laisse l'energie d'actionneur moyenne sur le
        cycle inchangee a 1e-16 pres. Un run de controle B2 exact vs hold a
        N=256 mesure l'effet residuel sur Dbar.

Espace
------
Le profil est evalue sur x = np.linspace(0,1,N), la MEME convention que la
grille 256 archivee (parois laterales sur les nœuds extremes, lid = rangee
i=N-1, abscisse = indice j). Il n'y a pas d'interpolation : la serie 512 est
la meme fonction continue vue sur 512 nœuds. Les series 512 sont aussi
archivees dans data/lid_series_n512/ (build_lid_series_n512.py) pour provenance.

Normalisation
-------------
E_act = moyenne sur le cycle de int U(x,t)^2 dx (trapeze, dx = 1/(N-1)) est
ramenee a E* = 0.25 par un facteur unique sqrt(E*/E_raw). Mesure : E_raw est
inchange entre 256 et 512 (a 2e-16 pres) donc le facteur d'echelle est le meme
aux deux resolutions (B1 : 0.993280746, B2/B3 : 1.0).

Usage
-----
    py scripts/run_branch_capture_d2.py --case B2 --N 256 --forcing exact      # controle escalier
    py scripts/run_branch_capture_d2.py --case B1 --N 512                       # campagne 512
    py scripts/run_branch_capture_d2.py --case B1 --N 512 --bench               # chrono ms/pas
"""
import argparse
import datetime
import json
import os
import sys
import time

import numpy as np

if not hasattr(np, "trapz"):
    np.trapz = np.trapezoid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lid_command as L  # noqa: E402

PAPER2 = os.path.normpath(os.path.join(
    os.path.expanduser("~"),
    "Documents", "travail pc taki_final", "Default Project",
    "papier 2 date_14_09_2026", "Paper2_branch_selection",
))
sys.path.insert(0, PAPER2)
from paper_paths import find_lbm  # noqa: E402

LBM_DIR = find_lbm()
sys.path.insert(0, LBM_DIR)
sys.path.insert(0, os.path.dirname(LBM_DIR))

from lbm_mrt_pinn_validation import (  # noqa: E402
    LBM_MRT_Solver, mrt_step, M, M_INV, EX, EY, W, OPP,
)

RE = 500
E_TARGET = 0.25
NT_WAVE = 256
U_REF = 0.05
T_PERIOD = 2.0
OMEGA = 2.0 * np.pi / T_PERIOD          # = pi, independant de N

SKIP_PERIODS = 15          # 15 x 2 = 30 unites physiques avant la fenetre de derive
WINDOW_PERIODS = 3         # fenetre derive -> 6 unites physiques
TOL_DRIFT = 2e-3
N_PHASE = 8
STRIDE = 8
DEFAULT_CAPTURE_PERIODS = 32
MAX_WARM_PERIODS = 60

CASE_STUDY = os.path.join(os.path.dirname(PAPER2),
                          "paper_2_case_study_15_09_2026")
LID_DIR_CS = os.path.join(CASE_STUDY, "data", "lid_series")
P1_SERIES = os.path.join(LBM_DIR, "lid_series")

OUTROOT = os.path.abspath(os.path.join(HERE, ".."))
ARCHIVE = os.path.join(OUTROOT, "data", "lid_series")

CASE_FILES = {
    "B1": ("fourier_Re500.npz", P1_SERIES),
    "B2": ("B2_seed5_E025_re500_e0.25.npz", LID_DIR_CS),
    "B3": ("B3_seed0_E025_re500_e0.25.npz", LID_DIR_CS),
}


def _lid(name, external_dir):
    """Prefer the copy archived in this repository, fall back to the PINN output."""
    local = os.path.join(ARCHIVE, name)
    return local if os.path.exists(local) else os.path.join(external_dir, name)


def set_outdir(path):
    global OUTDIR
    OUTDIR = path
    os.makedirs(OUTDIR, exist_ok=True)


def protocol(N):
    """steps/periode, slowdown, dt_phys : frequence preservee quelque soit N."""
    steps = int(round(T_PERIOD * N / U_REF))
    if steps % NT_WAVE:
        raise SystemExit(f"N={N} : {steps} pas/periode n'est pas un multiple de "
                         f"{NT_WAVE} echantillons")
    slowdown = steps // NT_WAVE
    dt = U_REF / N
    if abs(steps * dt - T_PERIOD) > 1e-12:
        raise SystemExit("incoherence temporelle")
    return steps, slowdown, dt


OUTDIR = os.path.join(OUTROOT, "results", "09_d2_capture")
os.makedirs(OUTDIR, exist_ok=True)


def out_tag(case, N, forcing):
    base = f"capture_{case}_D2_N{N}"
    return base if forcing == "hold" else base + f"_{forcing}"


def _log_path(case, N, forcing):
    return os.path.join(OUTDIR, f"capture_d2_{case}_N{N}_{forcing}.log")


def log(case, N, forcing, msg):
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {msg}"
    print(line, flush=True)
    with open(_log_path(case, N, forcing), "a", encoding="utf-8") as fh:
        fh.write(line + "\n")


def build_command(case, N, forcing):
    """Profil de lid (normalise) sur la grille N, en version hold ou exacte.

    Retourne (U_native, U_play, e_raw, scale, path, coeffs, e_play) :
      U_native (NT_WAVE, N)   : la forme d'onde aux 256 temps d'echantillonnage
      U_play   (steps, N)     : la commande vue par le solveur, pas a pas
      e_play   (steps,)       : E(t) = int U^2 dx de la commande jouee
      e_raw / scale           : energie native et facteur de normalisation vers E*
    """
    name, ext = CASE_FILES[case]
    path = _lid(name, ext)
    if not os.path.exists(path):
        raise SystemExit(f"waveform missing: {path}")
    d = L.load_case(path)
    if d["nx"] != 256:
        raise SystemExit(f"{path}: {d['nx']} nœuds, attendus 256")
    x = np.linspace(0.0, 1.0, N)
    dx = x[1] - x[0]
    t_sample = np.arange(NT_WAVE) * (T_PERIOD / NT_WAVE)
    steps, slowdown, dt = protocol(N)
    e_raw = L.actuation_energy(L.evaluate(d["c"], x, t_sample), x)
    scale = float(np.sqrt(E_TARGET / e_raw))
    c = d["c"] * scale
    U_native = L.evaluate(c, x, t_sample)                  # (256, N)
    if forcing == "hold":
        U_play = np.ascontiguousarray(np.repeat(U_native, slowdown, axis=0))
    elif forcing == "exact":
        U_play = np.ascontiguousarray(
            L.evaluate(c, x, np.arange(steps) * dt))
    else:
        raise SystemExit(f"forcing inconnu: {forcing}")
    if U_play.shape != (steps, N):
        raise SystemExit(U_play.shape)
    e_play = np.asarray([float(np.trapezoid(r ** 2, dx=dx)) for r in U_play])
    if N == 256:
        diff = float(np.max(np.abs(U_native - d["U"] * scale)))
        if diff > 1e-10:
            raise SystemExit(f"{case}: reconstruction != archive (max|d|={diff:.2e})")
    return U_native, U_play, e_raw, scale, path, c, e_play


def eps_field(ux, uy, dx, nu):
    dUdx = np.gradient(ux, dx, axis=1)
    dUdy = np.gradient(ux, dx, axis=0)
    dVdx = np.gradient(uy, dx, axis=1)
    dVdy = np.gradient(uy, dx, axis=0)
    S11, S22, S12 = dUdx, dVdy, 0.5 * (dUdy + dVdx)
    phi = nu * (2 * S11 ** 2 + 2 * S22 ** 2 + 4 * S12 ** 2)
    return float(np.trapz(np.trapz(phi, dx=dx, axis=1), dx=dx))


def k_field(ux, uy, dx):
    return float(np.trapz(np.trapz(0.5 * (ux ** 2 + uy ** 2),
                                    dx=dx, axis=1), dx=dx))


def plid_field(ux, dx, nu, uw, N):
    du_dy = (ux[N - 1, :] - ux[N - 2, :]) / dx
    tau_w = nu * du_dy
    return float(np.sum(uw * ux[N - 1, :] * tau_w) * dx)


def bench(case, N, forcing, n_steps=2048):
    """Chrono representative du TRUE taux de la campagne, pas du seul mrt_step.

    Reproduit la boucle de capture : mrt_step + normalisation U_ref + accumulateurs
    de moyenne/phase + sondes eps/K/P tous les STRIDE pas. C'est le nombre qui
    sert a l'ETA (le mrt_step seul sous-estime le cout de ~70 %).
    """
    steps, slowdown, dt = protocol(N)
    U_native, U_play, e_raw, scale, path, c, e_play = \
        build_command(case, N, forcing)
    solver = LBM_MRT_Solver(RE, N, lid_profile="uniform", max_iter=1000)
    solver.U_lid_norm = np.ascontiguousarray(U_play, dtype=np.float64)
    solver.period = steps
    solver.U_lid2d = solver.U_ref * solver.U_lid_norm
    S_diag, U_lid2d, U_ref = solver.S_diag, solver.U_lid2d, solver.U_ref
    nu, dx = 1.0 / RE, 1.0 / (N - 1)
    uw = np.ones(N); uw[0] = uw[-1] = 0.5
    f = solver.f.copy()
    sum_ux = np.zeros((N, N)); sum_uy = np.zeros((N, N))
    sum_ux2 = np.zeros((N, N)); sum_uy2 = np.zeros((N, N))
    ph_ux = np.zeros((N_PHASE, N, N)); ph_uy = np.zeros((N_PHASE, N, N))
    ph_ux2 = np.zeros((N_PHASE, N, N)); ph_uy2 = np.zeros((N_PHASE, N, N))
    ph_cnt = np.zeros(N_PHASE)
    probe = []

    def one(t_idx):
        nonlocal f, sum_ux, sum_uy, sum_ux2, sum_uy2
        f, rho, ux, uy = mrt_step(f, M, M_INV, S_diag, EX, EY, W,
                                  U_lid2d, t_idx, N, OPP)
        un = ux / U_ref; vn = uy / U_ref
        ph = (t_idx * N_PHASE) // steps
        sum_ux += un; sum_uy += vn
        sum_ux2 += un * un; sum_uy2 += vn * vn
        ph_ux[ph] += un; ph_uy[ph] += vn
        ph_ux2[ph] += un * un; ph_uy2[ph] += vn * vn
        ph_cnt[ph] += 1
        if t_idx % STRIDE == 0:
            probe.append(eps_field(un, vn, dx, nu))
            probe.append(k_field(un, vn, dx))
            probe.append(plid_field(un, dx, nu, uw, N))

    for t in range(200):                       # compilation / cache numba
        one(t % steps)
    probe.clear()
    t0 = time.time()
    for t in range(n_steps):
        one(t % steps)
    dt_ms = (time.time() - t0) / n_steps * 1000.0
    print(f"BENCH N={N} forcing={forcing}: {dt_ms:.3f} ms/pas de campagne "
          f"(mrt_step + accumulateurs + sondes chaque {STRIDE} pas), "
          f"{steps} pas/periode -> {dt_ms * steps / 1000.0:.0f} s/periode",
          flush=True)
    return dt_ms


def ckpt_path(case, N, forcing):
    """Sous-repertoire de OUTDIR : set_outdir() deplace aussi les checkpoints."""
    return os.path.join(OUTDIR, "checkpoints", f"ckpt_{case}_D2_N{N}_{forcing}.npz")


def fingerprint(case, N, forcing, capture_periods, steps, slowdown, scale,
                e_r_realized):
    """Tout ce qui doit etre identique pour qu'un checkpoint soit reutilisable.

    Le solveur est deterministe (pas d'alea, pas de dependance au temps mural :
    seul le compteur d'iterations pilote la commande), donc reprendre depuis
    l'etat `f` sauvegarde en debut de periode redonne des series bit a bit
    identiques a celles d'un run continu. Ce n'est vrai que si la commande, la
    grille et la fenetre sont les memes : d'ou cette empreinte.
    """
    return json.dumps({
        "case": case, "N": N, "forcing": forcing, "Re": RE,
        "capture_periods": int(capture_periods), "steps": int(steps),
        "slowdown": int(slowdown), "scale": float(scale),
        "E_r_realized": float(e_r_realized), "U_ref": U_REF,
        "T_period": T_PERIOD, "stride": STRIDE, "n_phase": N_PHASE,
        "skip_periods": SKIP_PERIODS, "window_periods": WINDOW_PERIODS,
        "tol_drift": TOL_DRIFT, "max_warm_periods": MAX_WARM_PERIODS,
    }, sort_keys=True)


def save_ckpt(path, fp, phase, f, it, drift, arrays):
    """Ecriture atomique : os.replace ne publie qu'un checkpoint complet."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp.npz"
    kw = dict(fingerprint=fp, phase=phase, it=np.int64(it),
              drift=np.float64(drift), f=np.asarray(f))
    kw.update({k: np.asarray(v) for k, v in arrays.items()})
    np.savez(tmp, **kw)                      # non compresse : 190 Mo en ~2 s
    os.replace(tmp, path)


def load_ckpt(path, fp):
    """Retourne l'etat du checkpoint si l'empreinte correspond, sinon None.

    Un checkpoint obsolete (autre branche, autre fenetre, autre commande) est
    ignore et sera ecrase par le premier checkpoint du nouveau run.
    """
    if not os.path.exists(path):
        return None
    try:
        with np.load(path, allow_pickle=False) as z:
            got = str(z["fingerprint"])
            if got != fp:
                print(f"CKPT ignore (empreinte differente) : {path}", flush=True)
                return None
            r = {k: z[k] for k in z.files if k != "fingerprint"}
            r["phase"] = str(r["phase"])
            if "f" not in r:
                # checkpoint ecrit par la version qui ne persistait pas le champ :
                # inutilisable pour une reprise, ignore puis ecrase
                print(f"CKPT sans champ d'ecart (version obsolete) : {path} "
                      f"-> reprise depuis zero", flush=True)
                return None
    except Exception as exc:                  # fichier troncage par un crash
        print(f"CKPT illisible ({exc}) : {path} -> reprise depuis zero",
              flush=True)
        return None
    return r


def capture(case, N, forcing, capture_periods, force=False):
    steps, slowdown, dt_phys = protocol(N)
    (U_native, U_play, e_raw, scale, path, coeffs,
     e_play) = build_command(case, N, forcing)
    solver = LBM_MRT_Solver(RE, N, lid_profile="uniform", max_iter=1000)
    solver.U_lid_norm = np.ascontiguousarray(U_play, dtype=np.float64)
    solver.period = steps
    solver.U_lid2d = solver.U_ref * solver.U_lid_norm
    U_lid2d, S_diag = solver.U_lid2d, solver.S_diag
    U_ref = solver.U_ref
    nu = 1.0 / RE
    nu_latt = U_ref * N / RE
    dx = 1.0 / (N - 1)
    uw = np.ones(N); uw[0] = uw[-1] = 0.5
    e_r_realized = float(e_play.mean())
    tag = out_tag(case, N, forcing)

    log(case, N, forcing, f"START case={case} file={os.path.basename(path)} "
        f"N={N} steps_per_period={steps} slowdown={slowdown} dt_phys={dt_phys:.3e} "
        f"T_phys={steps * dt_phys:.6f} omega_target={OMEGA:.6f} forcing={forcing} "
        f"E_raw={e_raw:.9f} scale={scale:.9f} E_realized={e_r_realized:.9f} "
        f"nu_latt={nu_latt:.6f} CAPTURE={capture_periods} P")

    t0 = time.time()
    f = solver.f.copy()
    it = 0
    skip = SKIP_PERIODS * steps
    hard_cap = MAX_WARM_PERIODS * steps
    eps_probe = []
    stopped = False
    drift = float("nan")
    ph_state = None
    resumed = False
    wall_prev = 0.0        # temps mural des segments deja cumulés (reprise)

    def el():
        """Secondes de calcul cumulees, segments de reprise incluses."""
        return time.time() - t0 + wall_prev

    ck = ckpt_path(case, N, forcing)
    fp = fingerprint(case, N, forcing, capture_periods, steps, slowdown,
                     scale, e_r_realized)
    if not force:
        r = load_ckpt(ck, fp)
        if r is not None:
            f = np.ascontiguousarray(r["f"])
            it = int(r["it"]); drift = float(r["drift"])
            resumed = True
            wall_prev = float(r["wall_cum"])
            if r["phase"] == "warm":
                eps_probe = list(r["eps_probe"])
            else:
                stopped = True
                ph_state = r
            log(case, N, forcing,
                f"   RESUME checkpoint {os.path.basename(ck)} : it={it} "
                f"({it / steps:.1f} P) phase={r['phase']} "
                f"eps_probe={len(eps_probe)}")
    while it < hard_cap and not stopped:
        for _ in range(10):
            t_idx = it % steps
            f, rho, ux, uy = mrt_step(f, M, M_INV, S_diag, EX, EY, W,
                                      U_lid2d, t_idx, N, OPP)
            if it >= skip and (it - skip) % STRIDE == 0:
                eps_probe.append(eps_field(ux / U_ref, uy / U_ref, dx, nu))
            it += 1
        n = len(eps_probe)
        if it % (2000 if N == 512 else 1000) == 0:
            msg = (f"   warm it={it} ({it / steps:.1f} P) samples={n} "
                   f"{el():.0f}s")
            if n:
                msg += f" eps_bar={np.mean(eps_probe):.5e}"
            print(msg, flush=True)
        if it % steps == 0:
            save_ckpt(ck, fp, "warm", f, it, drift,
                      {"eps_probe": np.asarray(eps_probe),
                        "wall_cum": np.float64(el())})
        w = WINDOW_PERIODS * steps // STRIDE
        if n >= 2 * w:
            a = np.mean(eps_probe[-2 * w:-w])
            b = np.mean(eps_probe[-w:])
            drift = abs(b - a) / abs(a)
            # meme porte qu'a N=256 : au moins 3 fenetres de derive observees
            # apres le skip, soit 9 periodes (skip 15 -> 24 P au plus tot)
            if it >= skip + 3 * w * STRIDE and drift < TOL_DRIFT:
                stopped = True

    log(case, N, forcing, f"   WARMUP iters={it} ({it / steps:.1f} P) "
        f"drift={drift:.2e} stopped={stopped} {el():.0f}s")

    n_steps = capture_periods * steps
    half_steps = n_steps // 2
    if ph_state is None:
        sum_ux = np.zeros((N, N)); sum_uy = np.zeros((N, N))
        sum_ux2 = np.zeros((N, N)); sum_uy2 = np.zeros((N, N))
        ph_ux = np.zeros((N_PHASE, N, N)); ph_uy = np.zeros((N_PHASE, N, N))
        ph_ux2 = np.zeros((N_PHASE, N, N)); ph_uy2 = np.zeros((N_PHASE, N, N))
        ph_cnt = np.zeros(N_PHASE)
        ph1_ux = np.zeros((N_PHASE, N, N)); ph1_uy = np.zeros((N_PHASE, N, N))
        ph1_ux2 = np.zeros((N_PHASE, N, N)); ph1_uy2 = np.zeros((N_PHASE, N, N))
        ph1_cnt = np.zeros(N_PHASE)

        t_s, eps_s, k_s, p_s, e_s, lid_err_s = [], [], [], [], [], []
        cx_s, cy_s = [], []      # sonde ponctuelle au centre : frequence du CHAMP
        c_ux, c_uy = N // 2, N // 2
        cyc_eps, cyc_K, cyc_P, cyc_E = [], [], [], []
        acc_e = acc_k = acc_p = 0.0
        acc_n = 0
        k_start = 0
    else:
        # reprise en cours de fenetre : les accumulateurs viennent du checkpoint,
        # rien n'est re-evalue, donc la fenetre reste exactement celles des
        # periodes deja jouees (it est repris tel quel).
        s = ph_state
        sum_ux, sum_uy = s["sum_ux"], s["sum_uy"]
        sum_ux2, sum_uy2 = s["sum_ux2"], s["sum_uy2"]
        ph_ux, ph_uy = s["ph_ux"], s["ph_uy"]
        ph_ux2, ph_uy2 = s["ph_ux2"], s["ph_uy2"]
        ph_cnt = s["ph_cnt"]
        ph1_ux, ph1_uy = s["ph1_ux"], s["ph1_uy"]
        ph1_ux2, ph1_uy2 = s["ph1_ux2"], s["ph1_uy2"]
        ph1_cnt = s["ph1_cnt"]
        t_s = list(s["t_s"]); eps_s = list(s["eps_s"]); k_s = list(s["k_s"])
        p_s = list(s["p_s"]); e_s = list(s["e_s"])
        lid_err_s = list(s["lid_err_s"])
        cx_s = list(s["cx_s"]); cy_s = list(s["cy_s"])
        c_ux, c_uy = N // 2, N // 2
        cyc_eps = list(s["cyc_eps"]); cyc_K = list(s["cyc_K"])
        cyc_P = list(s["cyc_P"]); cyc_E = list(s["cyc_E"])
        acc_e = float(s["acc"][0]); acc_k = float(s["acc"][1])
        acc_p = float(s["acc"][2]); acc_n = int(s["acc"][3])
        k_start = int(s["k_done"])
        if k_start >= n_steps or it != (int(s["it"])):
            raise SystemExit(f"checkpoint incoherent pour {tag}: "
                             f"k_start={k_start} it={it}")
        log(case, N, forcing,
            f"   RESUME capture : {k_start} pas sur {n_steps} deja faits, "
            f"{len(cyc_eps)} periodes archivees dans le checkpoint")

    for k in range(k_start, n_steps):
        t_idx = it % steps
        f, rho, ux, uy = mrt_step(f, M, M_INV, S_diag, EX, EY, W,
                                  U_lid2d, t_idx, N, OPP)
        un = ux / U_ref; vn = uy / U_ref
        ph = (t_idx * N_PHASE) // steps
        sum_ux += un; sum_uy += vn
        sum_ux2 += un * un; sum_uy2 += vn * vn
        ph_ux[ph] += un; ph_uy[ph] += vn
        ph_ux2[ph] += un * un; ph_uy2[ph] += vn * vn
        ph_cnt[ph] += 1
        if k < half_steps:
            ph1_ux[ph] += un; ph1_uy[ph] += vn
            ph1_ux2[ph] += un * un; ph1_uy2[ph] += vn * vn
            ph1_cnt[ph] += 1
        if k % STRIDE == 0:
            ep = eps_field(un, vn, dx, nu)
            kk = k_field(un, vn, dx)
            pp = plid_field(un, dx, nu, uw, N)
            t_s.append(it); eps_s.append(ep); k_s.append(kk)
            p_s.append(pp); e_s.append(e_play[t_idx])
            cx_s.append(float(un[c_ux, c_uy]))
            cy_s.append(float(vn[c_ux, c_uy]))
            lid_err_s.append(float(np.max(np.abs(
                un[N - 1, :] - U_play[t_idx]))))
            acc_e += ep; acc_k += kk; acc_p += pp; acc_n += 1
        it += 1
        if (k + 1) % steps == 0:
            cyc_eps.append(acc_e / acc_n)
            cyc_K.append(acc_k / acc_n)
            cyc_P.append(acc_p / acc_n)
            cyc_E.append(float(e_play.mean()))
            acc_e = acc_k = acc_p = 0.0
            acc_n = 0
            log(case, N, forcing,
                f"   capture P{len(cyc_eps)}/{capture_periods} "
                f"eps={cyc_eps[-1]:.6e} K={cyc_K[-1]:.6e} P={cyc_P[-1]:.6e} "
                f"lid_err={lid_err_s[-1]:.2e} {el():.0f}s")
            if len(cyc_eps) < capture_periods:
                save_ckpt(ck, fp, "capture", f, it, drift, {
                    "sum_ux": sum_ux, "sum_uy": sum_uy,
                    "sum_ux2": sum_ux2, "sum_uy2": sum_uy2,
                    "ph_ux": ph_ux, "ph_uy": ph_uy,
                    "ph_ux2": ph_ux2, "ph_uy2": ph_uy2, "ph_cnt": ph_cnt,
                    "ph1_ux": ph1_ux, "ph1_uy": ph1_uy,
                    "ph1_ux2": ph1_ux2, "ph1_uy2": ph1_uy2,
                    "ph1_cnt": ph1_cnt,
                    "t_s": np.asarray(t_s, dtype=np.int64),
                    "eps_s": np.asarray(eps_s), "k_s": np.asarray(k_s),
                    "p_s": np.asarray(p_s), "e_s": np.asarray(e_s),
                    "lid_err_s": np.asarray(lid_err_s),
                    "cx_s": np.asarray(cx_s), "cy_s": np.asarray(cy_s),
                    "cyc_eps": np.asarray(cyc_eps), "cyc_K": np.asarray(cyc_K),
                    "cyc_P": np.asarray(cyc_P), "cyc_E": np.asarray(cyc_E),
                    "acc": np.array([acc_e, acc_k, acc_p, float(acc_n)]),
                    "wall_cum": np.float64(el()),
                    "k_done": np.int64(k + 1)})

    n_tot = float(n_steps)
    ux_mean = sum_ux / n_tot
    uy_mean = sum_uy / n_tot
    ux_rms = np.sqrt(np.clip(sum_ux2 / n_tot - ux_mean ** 2, 0.0, None))
    uy_rms = np.sqrt(np.clip(sum_uy2 / n_tot - uy_mean ** 2, 0.0, None))

    cph = np.maximum(ph_cnt, 1)[:, None, None]
    p_ux = ph_ux / cph; p_uy = ph_uy / cph
    p_ux_rms = np.sqrt(np.clip(ph_ux2 / cph - p_ux ** 2, 0.0, None))
    p_uy_rms = np.sqrt(np.clip(ph_uy2 / cph - p_uy ** 2, 0.0, None))
    c1 = np.maximum(ph1_cnt, 1)[:, None, None]
    p1_ux = ph1_ux / c1; p1_uy = ph1_uy / c1
    d_ux = p_ux - p1_ux
    d_uy = p_uy - p1_uy
    phase_half_diff = [
        float(np.linalg.norm(d_ux[i]) / max(np.linalg.norm(p_ux[i]), 1e-30))
        for i in range(N_PHASE)]

    x = np.linspace(0.0, 1.0, N)
    y = np.linspace(0.0, 1.0, N)
    psi_mean = np.cumsum(ux_mean, axis=0) * dx
    psi_mean -= psi_mean[0, :][None, :]

    eps_mf = eps_field(ux_mean, uy_mean, dx, nu)
    k_mf = k_field(ux_mean, uy_mean, dx)
    p_mf = plid_field(ux_mean, dx, nu, uw, N)
    k_fluct = k_field(ux_rms, uy_rms, dx)

    out = os.path.join(OUTDIR, tag + ".npz")
    meta = dict(
        case=case, Re=RE, N=N,
        steps_per_period=steps, period_lattice=steps, slowdown=slowdown,
        dt_phys=dt_phys, T_phys=steps * dt_phys, omega=OMEGA,
        forcing=forcing, nt_wave=NT_WAVE,
        lid_file=os.path.basename(path), scale=scale, E_raw=e_raw,
        E_r=E_TARGET, E_r_realized=e_r_realized, nu_latt=nu_latt,
        warm_iters=int(it - n_steps), capture_iters=int(n_steps),
        warm_periods=(it - n_steps) / steps,
        capture_periods=capture_periods,
        drift=float(drift), warm_stopped=bool(stopped),
        stride=STRIDE, n_phase=N_PHASE, phase_bin_counts=ph_cnt.tolist(),
        eps_cycle_mean=float(np.mean(cyc_eps)),
        K_cycle_mean=float(np.mean(cyc_K)),
        P_cycle_mean=float(np.mean(cyc_P)),
        eps_meanfield=eps_mf, K_meanfield=k_mf, P_meanfield=p_mf,
        K_fluct=float(k_fluct),
        R_K=float(k_fluct / np.mean(cyc_K)) if np.mean(cyc_K) > 0 else None,
        phase_half_diff=phase_half_diff,
        lid_max_error=float(np.max(lid_err_s)),
        coeffs=coeffs.tolist(),
        resumed_from_checkpoint=bool(resumed),
        seconds=round(el(), 1), status="ok",
    )
    save_kw = dict(
        meta=json.dumps(meta),
        x=x, y=y,
        ux_mean=ux_mean, uy_mean=uy_mean, ux_rms=ux_rms, uy_rms=uy_rms,
        psi_mean=psi_mean,
        phase_ux=p_ux, phase_uy=p_uy,
        phase_ux_rms=p_ux_rms, phase_uy_rms=p_uy_rms,
        phase_cnt=ph_cnt, phase_half_ux=p1_ux, phase_half_uy=p1_uy,
        # U_lid_series : (steps, N) en mode hold (commande reellement jouee),
        # (NT_WAVE, N) en mode exact pour ne pas dupliquer 20480 rangees lisses ;
        # la commande exacte est reconstructible depuis coeffs + t = k*dt_phys.
        U_lid_series=U_play if forcing == "hold" else U_native,
        E_act_series=e_play,
        U_lid_native=U_native, coeffs=np.asarray(coeffs),
        t_series=np.asarray(t_s, dtype=np.int64),
        eps_series=np.asarray(eps_s), K_series=np.asarray(k_s),
        P_series=np.asarray(p_s), E_act_series_t=np.asarray(e_s),
        lid_error_series=np.asarray(lid_err_s),
        probe_ux_center=np.asarray(cx_s), probe_uy_center=np.asarray(cy_s),
        probe_index=np.array([c_ux, c_uy], dtype=np.int64),
        cyc_eps=np.asarray(cyc_eps), cyc_K=np.asarray(cyc_K),
        cyc_P=np.asarray(cyc_P), cyc_E=np.asarray(cyc_E),
    )
    np.savez_compressed(out, **save_kw)
    # l'archive est écrite : le checkpoint n'a plus de raison d'etre (il serait
    # de toute facon rejete par l'empreinte au prochain run de cette branche)
    if os.path.exists(ck):
        os.remove(ck)
    log(case, N, forcing, f"DONE  {tag} eps={np.mean(cyc_eps):.6e} "
        f"K={np.mean(cyc_K):.6e} P={np.mean(cyc_P):.6e} "
        f"eps_mf={eps_mf:.6e} P/eps={np.mean(cyc_P)/np.mean(cyc_eps):.3f} "
        f"phase_half_max={max(phase_half_diff):.2e} ({meta['seconds']:.0f}s)")
    print("  ->", out)
    return meta


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--case", choices=sorted(CASE_FILES), required=True)
    ap.add_argument("--N", type=int, choices=[256, 512], default=256)
    ap.add_argument("--forcing", choices=["hold", "exact"], default="hold")
    ap.add_argument("--capture-periods", type=int,
                    default=DEFAULT_CAPTURE_PERIODS)
    ap.add_argument("--bench", action="store_true",
                    help="mesure le cout en ms/pas et sort")
    ap.add_argument("--smoke", action="store_true",
                    help="protocole raccourci (2 P warmup + 1 P capture) ecrit "
                         "dans results/_smoke, ne touche aucune capture valide")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    if args.smoke:
        set_outdir(os.path.join(OUTROOT, "results", "_smoke"))
        SKIP_PERIODS = 1              # noqa: PLW0603 (module-level override)
        MAX_WARM_PERIODS = 2
        args.capture_periods = 1
        print(f"SMOKE -> {OUTDIR} (warmup<=2 P, capture 1 P)", flush=True)
    if args.bench:
        ms = bench(args.case, args.N, args.forcing)
        steps, slowdown, dt = protocol(args.N)
        rec = {"s_per_step": ms / 1000.0, "ms_per_step": ms, "N": args.N,
               "forcing": args.forcing, "steps_per_period": steps,
               "s_per_period": ms / 1000.0 * steps,
               "measured_at": time.strftime("%F %T")}
        p = os.path.join(OUTROOT, "results", "d2_derived",
                         f"preflight_bench_n{args.N}.json")
        data = {}
        if os.path.exists(p):
            with open(p) as fh:
                data = json.load(fh)
        data[args.case] = rec
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as fh:
            json.dump(data, fh, indent=1, sort_keys=True)
        print(f"BENCH ecrit -> {p}", flush=True)
        raise SystemExit(0)
    out = os.path.join(OUTDIR, out_tag(args.case, args.N, args.forcing) + ".npz")
    if os.path.exists(out) and not args.force:
        log(args.case, args.N, args.forcing, f"SKIP (already captured): {out}")
    else:
        capture(args.case, args.N, args.forcing, args.capture_periods)
