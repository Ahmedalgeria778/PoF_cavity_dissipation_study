# -*- coding: utf-8 -*-
"""Base spectrale des commandes de paroi, utilise par les runs D2.

Les series U_lid archivees sont des evaluations de
    U(x,t) = sum_{i=0..5} sum_{j=0..4} c_ij sin((i+1) pi x) cos(j pi t)
sur la grille periodique endpoint=False (256 echantillons sur T=2).
La projection trapeze sur cette meme base recouvre les c_ij a la precision
machine ; une fois les c_ij connus, la commande peut etre evaluee en tout
point (x,t), ce qui donne :
  * la conversion spatiale 256 -> 512 noeuds sans interpolation,
  * la commande temps-exacte (pas d'echantillon maintenu 40/80 pas).
"""
import numpy as np

N_MX = 6
N_MT = 5
NT_WAVE = 256
T_PERIOD = 2.0


def _trapezoid_weights(n, h):
    w = np.ones(n) * h
    w[0] = w[-1] = 0.5 * h
    return w


def _periodic_weights(n, h):
    """Poids du trapeze periodique : la grille couvre une periode sans repeter
    la borne (endpoint=False), donc f(t_0)=f(t_n) et les poids sont uniformes.
    Le trapeze "demi-bords" sur cette grille introduirait une erreur d'ordre h
    qui detruirait l'exactitude de la projection (residu ~2e-2 mesure)."""
    return np.full(n, h)


def sin_modes(x):
    return np.array([np.sin((i + 1) * np.pi * x) for i in range(N_MX)])


def cos_modes(t):
    return np.array([np.cos(j * np.pi * t) for j in range(N_MT)])


def coefficients_from_series(U, x, t, t_periodic=True):
    """Projection trapeze de U(t,x) sur la base sin((i+1)pi x) cos(j pi t).

    Retourne (c, residu_max) avec c de forme (N_MX, N_MT).
    """
    wx = _trapezoid_weights(len(x), x[1] - x[0])
    wt = (_periodic_weights if t_periodic else _trapezoid_weights)(
        len(t), t[1] - t[0])
    W = np.outer(wt, wx)
    sx = sin_modes(x)
    cj = cos_modes(t)
    c = np.zeros((N_MX, N_MT))
    U_rec = np.zeros_like(U)
    for i in range(N_MX):
        for j in range(N_MT):
            outer = np.outer(cj[j], sx[i])
            norm2 = float(np.sum(W * outer ** 2)) + 1e-30
            cij = float(np.sum(W * U * outer) / norm2)
            c[i, j] = cij
            U_rec += cij * outer
    return c, float(np.max(np.abs(U - U_rec)))


def evaluate(c, x, t):
    """U(t,x) = sum c_ij sin((i+1)pi x) cos(j pi t) sur toute grille (x,t)."""
    sx = sin_modes(np.asarray(x, dtype=np.float64))
    cj = cos_modes(np.asarray(t, dtype=np.float64))
    return np.einsum("ij,jt,ix->tx", c, cj, sx)


def load_case(path, rescale_to=None, tol=1e-9):
    """Charge une archive npz, verifie qu'elle vit exactement dans la base
    sin((i+1)pi x)cos(j pi t) et retourne les coefficients.

    L'archive peut etre echantillonnee sur la grille periodique endpoint=False
    (format D2 actuel) ou sur linspace(0,T,nt) endpoint=True (ancien format) :
    les deux conventions sont testees et celle qui reconstruit est retenue.
    """
    with np.load(path) as z:
        U = np.asarray(z["U_series"], dtype=np.float64)
        nt_per = int(z["NT_PER"])
        t_per = float(z["T_PERIOD"])
    if nt_per != NT_WAVE or t_per != T_PERIOD:
        raise RuntimeError(f"{path}: NT_PER={nt_per} T_PERIOD={t_per}")
    nx = U.shape[1]
    x = np.linspace(0.0, 1.0, nx)
    grids = [("endpoint=False",
              np.arange(NT_WAVE) * (T_PERIOD / NT_WAVE), True),
             ("endpoint=True",
              np.linspace(0.0, T_PERIOD, NT_WAVE), False)]
    best = None
    for name, t, periodic in grids:
        c, resid = coefficients_from_series(U, x, t, t_periodic=periodic)
        if best is None or resid < best[2]:
            best = (name, t, resid, c)
    name, t, resid, c = best
    if resid > tol:
        raise RuntimeError(f"{path}: reconstruction residuelle {resid:.3e} > {tol:.0e} "
                           f"(meilleure convention : {name})")
    out = dict(c=c, resid=resid, convention=name, U=U, x=x, t=t, path=path,
               e_raw=actuation_energy(U, x), nx=nx, scale=1.0)
    if rescale_to is not None:
        scale = float(np.sqrt(rescale_to / out["e_raw"]))
        out.update(c=c * scale, U=U * scale, scale=scale,
                   e_raw=out["e_raw"] * scale ** 2)
    return out


def actuation_energy(U, x):
    """Moyenne temporelle de E(t)=int U(x,t)^2 dx (regle trapeze, dx=1/(nx-1))."""
    return float(np.mean([np.trapezoid(row ** 2, dx=x[1] - x[0]) for row in U]))


def hold_vs_exact(c, nx, slowdown, nt_wave=NT_WAVE, t_period=T_PERIOD,
                  chunk=2048):
    """Quantifie l'ecart entre la commande « echantillon maintenu » (zero-order
    hold, ce que joue le solveur) et la commande temps-exacte evaluee a chaque
    pas a partir des c_ij.
    """
    x = np.linspace(0.0, 1.0, nx)
    dx = x[1] - x[0]
    wx = _trapezoid_weights(nx, dx)
    t_sample = np.arange(nt_wave) * (t_period / nt_wave)
    U_sample = evaluate(c, x, t_sample)
    steps = nt_wave * int(slowdown)
    e_exact = e_hold = 0.0
    peak_del = peak_hold = l2num = l2den = 0.0
    for start in range(0, steps, chunk):
        stop = min(start + chunk, steps)
        k = np.arange(start, stop)
        Ue = evaluate(c, x, k * (t_period / steps))
        Uh = U_sample[k // int(slowdown)]
        ee = (Ue * Ue) @ wx
        eh = (Uh * Uh) @ wx
        e_exact += float(ee.sum())
        e_hold += float(eh.sum())
        d = Ue - Uh
        peak_del = max(peak_del, float(np.max(np.abs(d))))
        peak_hold = max(peak_hold, float(np.max(np.abs(Uh))))
        l2num += float(np.sum(d * d))
        l2den += float(np.sum(Uh * Uh))
    n = float(steps)
    return dict(
        nx=nx, slowdown=int(slowdown), steps_per_period=steps,
        max_abs_delta=peak_del, rel_to_peak=peak_del / peak_hold,
        l2_rel=float(np.sqrt(l2num / l2den)),
        E_hold=e_hold / n, E_exact=e_exact / n,
        dE_rel=(e_exact - e_hold) / e_hold,
    )
