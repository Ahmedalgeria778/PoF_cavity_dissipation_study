# -*- coding: utf-8 -*-
"""Audit des formules de gradient utilisees par le traitement D2.

Verifie, contre des champs analytiques dont la valeur exacte est connue, les
 trois quantites differentielles citees dans le manuscrit :

   eps  = 2 nu S:S = nu (2 u_x^2 + 2 v_y^2 + (u_y + v_x)^2)   (run_branch_capture_d2.eps_field)
   K    = 1/2 |u|^2                                          (run_branch_capture_d2.k_field)
   S_om = d_x F_y - d_y F_x                                  (d2_topology_numbers, table S11)

Les champs de la campagne sont stockes F[i, j] avec i = y et j = x (le streaming
du solveur avance i avec EY et j avec EX).  Un echange d'axes ne change pas la
forme des ecritures, seule une valeur analytique le detecte : le test du cisaillement
lineaire u = G y vaut exactement nu G^2 dans le bon sens et 2 nu G^2 axes intervertis.

Tests :
  1. cisaillement lineaire   : eps = nu G^2 (exact, a l'erreur d'arrondi pres)
  2. tourbillon de Taylor-Green : eps = nu k^2, K = 1/2 <u^2+v^2> = 1/4, et
     identite periodique int 2 S:S = int omega^2
  3. donnees reelles (capture B2 N=256) : residual de continuite dans le sens
     de production vs le sens interverti, et coherence de psi = int u dy avec v
  4. sensibilite de eps au ordre aux bords (np.gradient edge_order 1 vs 2)

Usage :
    py scripts/test_gradient_identities.py
Ecrit results/d2_derived/gradient_identity_audit.json et sort avec un code
non nul si une identite analytique ou la convention d'axes echoue.
"""
import io
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
from run_branch_capture_d2 import eps_field, k_field  # noqa: E402

RE = 500.0
NU = 1.0 / RE
N = 256
H = 1.0 / (N - 1)
CAP = os.path.join(REPO, "results", "09_d2_capture", "capture_B2_D2_N256.npz")
OUT = os.path.join(REPO, "results", "d2_derived",
                   "gradient_identity_audit.json")

rows = []
failed = []


def check(name, got, want, tol):
    dev = abs(got / want - 1.0)
    ok = dev <= tol
    rows.append(dict(test=name, got=float(got), want=float(want),
                     dev=float(dev), tol=float(tol), ok=bool(ok)))
    print("%-46s got %-14.8g want %-14.8g dev %.3e  %s"
          % (name, got, want, dev, "[ok]" if ok else "[FAIL]"))
    if not ok:
        failed.append(name)
    return ok


def field(fn, x):
    """Build F[i, j] = fn(x_j, y_i): axis 0 is y, axis 1 is x (solver layout)."""
    y, xx = np.meshgrid(x, x, indexing="ij")
    return fn(xx, y)


x_nodes = np.linspace(0.0, 1.0, N)
K2 = 2.0 * np.pi

# --- 1. linear shear: eps = nu G^2 exactly (np.gradient is exact for a linear field)
G = 2.0
u_shear = field(lambda X, Y: G * Y, x_nodes)
v_zero = np.zeros_like(u_shear)
check("shear u=Gy: eps vs nu G^2", eps_field(u_shear, v_zero, H, NU),
      NU * G * G, 1e-12)
check("shear: swapped axes must differ by 2x",
      eps_field(u_shear.T, v_zero.T, H, NU) / (NU * G * G), 2.0, 1e-12)

# --- 2. Taylor-Green: u = sin(kx)cos(ky), v = -cos(kx)sin(ky), k = 2 pi
u_tg = field(lambda X, Y: np.sin(K2 * X) * np.cos(K2 * Y), x_nodes)
v_tg = field(lambda X, Y: -np.cos(K2 * X) * np.sin(K2 * Y), x_nodes)
# exact integrals over the unit cell: eps = nu k^2 (u_x = -v_y, u_y + v_x = 0),
# K = (1/2)(<u^2> + <v^2>) = 1/4, enstrophy int omega^2 = k^2
fd_err = (K2 * H) ** 2 / 6.0
check("Taylor-Green: eps vs nu k^2", eps_field(u_tg, v_tg, H, NU),
      NU * K2 ** 2, 4.0 * fd_err)
check("Taylor-Green: K vs 1/4", k_field(u_tg, v_tg, H), 0.25, 1e-3)
du_dy = np.gradient(u_tg, H, axis=0)
dv_dx = np.gradient(v_tg, H, axis=1)
omega = dv_dx - du_dy
enstrophy = float(np.trapezoid(np.trapezoid(omega ** 2, dx=H, axis=1), dx=H))
check("Taylor-Green: enstrophy vs k^2", enstrophy, K2 ** 2, 4.0 * fd_err)
check("Taylor-Green: int 2 S:S = int omega^2",
      eps_field(u_tg, v_tg, H, NU) / (NU * enstrophy), 1.0, 2e-3)

# --- 3. the archived D2 field must satisfy continuity in the production layout
d = np.load(CAP)
um = np.asarray(d["ux_mean"], dtype=float)
vm = np.asarray(d["uy_mean"], dtype=float)


def div_res(a_u, a_v):
    """max |du/dx + dv/dy| over the interior for a field given in production layout."""
    r = np.gradient(a_u, H, axis=1) + np.gradient(a_v, H, axis=0)
    return float(np.abs(r[3:-3, 3:-3]).max())


div_prod = div_res(um, vm)
div_swap = div_res(um.T, vm.T)
rows.append(dict(test="continuity max|div|, production layout", got=div_prod))
rows.append(dict(test="continuity max|div|, swapped layout", got=div_swap))
print("%-46s prod %.3e   swapped %.3e   ratio %.1f  %s"
      % ("continuity residual (axis 0 = y vs axis 0 = x)", div_prod, div_swap,
         div_swap / div_prod,
         "[ok]" if div_swap / div_prod > 50 else "[FAIL]"))
if not div_swap / div_prod > 50.0:
    failed.append("continuity layout discrimination")

psi = np.cumsum(um, axis=0) * H
psi -= psi[0, :][None, :]
psi_res = float(np.abs(np.gradient(psi, H, axis=1) + vm)[3:-3, 3:-3].max())
psi_res_swap = float(np.abs(np.gradient(psi, H, axis=0) + um)[3:-3, 3:-3].max())
rows.append(dict(test="psi cross-check residual, production", got=psi_res))
rows.append(dict(test="psi cross-check residual, swapped", got=psi_res_swap))
print("%-46s prod %.3e (rel %.2f%%)  swapped %.3e  %s"
      % ("psi = int u dy checked against v", psi_res,
         100 * psi_res / np.abs(vm).max(), psi_res_swap,
         "[ok]" if psi_res < 0.1 * np.abs(vm).max()
         and psi_res_swap > 5 * psi_res else "[FAIL]"))
if not (psi_res < 0.1 * np.abs(vm).max() and psi_res_swap > 5.0 * psi_res):
    failed.append("psi consistency")


# --- 4. edge_order sensitivity of the production eps on a real mean field
def eps_edge(a_u, a_v, edge_order):
    du_dx = np.gradient(a_u, H, axis=1, edge_order=edge_order)
    du_dy = np.gradient(a_u, H, axis=0, edge_order=edge_order)
    dv_dx = np.gradient(a_v, H, axis=1, edge_order=edge_order)
    dv_dy = np.gradient(a_v, H, axis=0, edge_order=edge_order)
    phi = NU * (2 * du_dx ** 2 + 2 * dv_dy ** 2 + (du_dy + dv_dx) ** 2)
    return float(np.trapezoid(np.trapezoid(phi, dx=H, axis=1), dx=H))


e1, e2 = eps_edge(um, vm, 1), eps_edge(um, vm, 2)
rows.append(dict(test="eps mean field: edge_order 1 vs 2", got=e2 / e1 - 1.0,
                 want=None, dev=None, tol=0.05, ok=bool(abs(e2 / e1 - 1) < 0.05)))
print("%-46s edge1 %.8f  edge2 %.8f  rel %+.3f%%  %s"
      % ("eps sensitivity to the wall stencil", e1, e2, 100 * (e2 / e1 - 1),
         "[ok]" if abs(e2 / e1 - 1) < 0.05 else "[FAIL]"))
if abs(e2 / e1 - 1) >= 0.05:
    failed.append("eps edge_order sensitivity")

meta = json.loads(str(d["meta"].item()))
summary = dict(
    Re=RE, N=N, h=H, checks=rows,
    continuity_prod=div_prod, continuity_swapped=div_swap,
    psi_residual=psi_res, psi_residual_swapped=psi_res_swap,
    eps_mean_field_edge1=e1, eps_mean_field_edge2=e2,
    eps_mean_field_edge_rel_change=e2 / e1 - 1.0,
    eps_cycle_mean_from_meta=float(meta["eps_cycle_mean"]),
    production_layout="axis 0 = y, axis 1 = x (verified)",
)
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with io.open(OUT, "w", encoding="utf-8") as fh:
    json.dump(summary, fh, indent=1)
print("\nwrote %s" % OUT)
if failed:
    sys.exit("GRADIENT AUDIT FAILED: " + ", ".join(failed))
print("gradient audit: all analytic identities and the axis convention hold")
