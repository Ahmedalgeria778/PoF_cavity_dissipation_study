"""Quantify the 1/N vs 1/(N-1) spacing conventions used in the D2 post-processing.

The MRT-LBM mapping (dt, N_T, nu_latt) uses the hydrodynamic spacing dx = 1/N,
which is the spacing consistent with the half-way wall condition.  The cycle-mean
diagnostics integrate and differentiate on the archived node coordinates
x_j = j/(N-1), so they use h = 1/(N-1).  This script shows exactly which reported
quantities are sensitive to that choice.

A quantity built from (derivative)^2 times an area element, or from one derivative
times a line element, is invariant under h -> alpha*h: the stencil gains 1/alpha,
the measure gains alpha.  An area integral of a field that carries no derivative
(energies, streamfunction) scales as alpha^2, and a pointwise derivative scales as
1/alpha.  A RATIO of a one-derivative quantity to a two-derivative quantity scales
as alpha, so the forcing-to-viscous-term ratio of Sec. S4.7 is NOT invariant: it is
reduced by the factor (N-1)/N when h=1/(N-1) is replaced by 1/N.

Usage:  py scripts/spacing_convention_check.py
Writes results/d2_derived/spacing_convention_check.json
"""

import json
import os

import numpy as np

RE = 500.0
NU = 1.0 / RE
CASES = ("B1", "B2", "B3")
NS = (256, 512)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "d2_derived", "spacing_convention_check.json")


def trapz2(f, h):
    return float(np.trapezoid(np.trapezoid(f, dx=h, axis=1), dx=h))


def dissipation(ux, uy, h):
    dudx = np.gradient(ux, h, axis=1)
    dudy = np.gradient(ux, h, axis=0)
    dvdx = np.gradient(uy, h, axis=1)
    dvdy = np.gradient(uy, h, axis=0)
    phi = NU * (2 * dudx**2 + 2 * dvdy**2 + (dudy + dvdx) ** 2)
    return trapz2(phi, h)


def energy(ux, uy, h):
    return 0.5 * trapz2(ux**2 + uy**2, h)


def lid_power(ux, h, uw, n):
    du_dy = (ux[n - 1, :] - ux[n - 2, :]) / h
    return float(np.sum(uw * ux[n - 1, :] * NU * du_dy) * h)


def forcing_scale(uxm, uym, h):
    """Steady-streaming forcing magnitude of d2_topology_numbers.py (pointwise, ~1/h)."""
    tuu, tuv, tvv = uxm * uxm, uxm * uym, uym * uym
    d = lambda f, ax: (np.roll(f, -1, ax) - np.roll(f, 1, ax)) / 2.0
    fx = -(d(tuu, 1) + d(tuv, 0)) / (2.0 * h)
    fy = -(d(tuv, 1) + d(tvv, 0)) / (2.0 * h)
    return float(np.max(np.hypot(fx, fy)[1:-1, 1:-1]))


EXCL = 3


def d1(a, axis):
    out = np.zeros_like(a)
    sl_c = [slice(None)] * a.ndim
    sl_p = [slice(None)] * a.ndim
    sl_m = [slice(None)] * a.ndim
    sl_c[axis] = slice(1, -1)
    sl_p[axis] = slice(2, None)
    sl_m[axis] = slice(None, -2)
    out[tuple(sl_c)] = a[tuple(sl_p)] - a[tuple(sl_m)]
    return out


def interior(a):
    return a[EXCL:-EXCL, EXCL:-EXCL]


def streaming_ratios(pu, pv, um, vm, h):
    """Forcing-to-viscous-term ratio of Sec.~S4.7, same stencils as d2_topology_numbers.

    The forcing carries one divergence (~1/h), the mean viscous term two
    derivatives (~1/h^2), so the ratio scales as h and does NOT cancel.
    """
    up, vp = pu - um[None], pv - vm[None]
    tuu = np.mean(up**2, axis=0)
    tvv = np.mean(vp**2, axis=0)
    tuv = np.mean(up * vp, axis=0)
    fx = -(d1(tuu, 1) + d1(tuv, 0)) / (2.0 * h)
    fy = -(d1(tuv, 1) + d1(tvv, 0)) / (2.0 * h)
    visc_x = NU * (d1(d1(um, 1), 1) + d1(d1(um, 0), 0)) / h**2
    visc_y = NU * (d1(d1(vm, 1), 1) + d1(d1(vm, 0), 0)) / h**2
    f_mag = np.hypot(interior(fx), interior(fy))
    v_mag = np.hypot(interior(visc_x), interior(visc_y))
    rms = float(np.sqrt(np.mean(f_mag**2)) / np.sqrt(np.mean(v_mag**2)))
    mx = float(f_mag.max() / v_mag.max())
    return rms, mx


def main():
    rows = []
    for case in CASES:
        for n in NS:
            path = os.path.join(
                ROOT, "results", "09_d2_capture", f"capture_{case}_D2_N{n}.npz"
            )
            z = np.load(path)
            x = z["x"]
            h_nodes = float(x[1] - x[0])
            h_a, h_b = 1.0 / (n - 1), 1.0 / n
            uw = np.ones(n)
            uw[0] = uw[-1] = 0.5
            um, vm = z["ux_mean"], z["uy_mean"]
            rm, sm = z["ux_rms"], z["uy_rms"]
            pu, py = z["phase_ux"], z["phase_uy"]
            rec_a = float(np.mean([dissipation(pu[i], py[i], h_a) for i in range(len(pu))]))
            rec_b = float(np.mean([dissipation(pu[i], py[i], h_b) for i in range(len(pu))]))
            ratio_rms_a, ratio_max_a = streaming_ratios(pu, py, um, vm, h_a)
            ratio_rms_b, ratio_max_b = streaming_ratios(pu, py, um, vm, h_b)
            rows.append(
                {
                    "case": case,
                    "N": n,
                    "h_from_archived_x": h_nodes,
                    "h_1_over_Nm1": h_a,
                    "h_1_over_N": h_b,
                    "spacing_gap": h_b / h_a - 1.0,
                    "D_mean_field_rel_change": dissipation(um, vm, h_b) / dissipation(um, vm, h_a) - 1.0,
                    "D_fluct_field_rel_change": dissipation(rm, sm, h_b) / dissipation(rm, sm, h_a) - 1.0,
                    "D_phase_reconstruction_rel_change": rec_b / rec_a - 1.0,
                    "P_lid_mean_rel_change": lid_power(um, h_b, uw, n) / lid_power(um, h_a, uw, n) - 1.0,
                    "K_mean_field_rel_change": energy(um, vm, h_b) / energy(um, vm, h_a) - 1.0,
                    "K_fluct_field_rel_change": energy(rm, sm, h_b) / energy(rm, sm, h_a) - 1.0,
                    "streaming_forcing_rel_change": forcing_scale(rm, sm, h_b) / forcing_scale(rm, sm, h_a) - 1.0,
                    "forcing_over_viscous_ratio_rms_h": ratio_rms_a,
                    "forcing_over_viscous_ratio_rms_1_over_N": ratio_rms_b,
                    "forcing_over_viscous_ratio_rms_rel_change": ratio_rms_b / ratio_rms_a - 1.0,
                    "forcing_over_viscous_ratio_max_rel_change": ratio_max_b / ratio_max_a - 1.0,
                }
            )
            z.close()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as fh:
        json.dump({"Re": RE, "rows": rows}, fh, indent=2)
    for r in rows:
        print(
            f"{r['case']} N={r['N']:3d}  spacing gap {r['spacing_gap']:+.4%}  "
            f"D_mean {r['D_mean_field_rel_change']:+.2e}  D_fluct {r['D_fluct_field_rel_change']:+.2e}  "
            f"D_phase {r['D_phase_reconstruction_rel_change']:+.2e}  P_lid {r['P_lid_mean_rel_change']:+.2e}  "
            f"K_mean {r['K_mean_field_rel_change']:+.4%}  K_fluct {r['K_fluct_field_rel_change']:+.4%}  "
            f"|F| {r['streaming_forcing_rel_change']:+.4%}  "
            f"F/visc {r['forcing_over_viscous_ratio_rms_rel_change']:+.4%} "
            f"(rms ratio at h: {r['forcing_over_viscous_ratio_rms_h']:.5f})"
        )
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
