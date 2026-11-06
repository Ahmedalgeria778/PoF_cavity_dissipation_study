"""Stokes-layer scaling estimate recomputed from the D2 branch captures.

Input: results/09_d2_capture/capture_B?_D2_N256.npz, array U_lid_native
(256 x 256): one forcing period of the lid signal actually imposed, sampled on
theta in [0,1) with endpoint excluded, columns on the lid nodes, velocities in
cavity units. Period T = 2, so omega_n = n*pi.

Model: second problem of Stokes, as in stokes_scaling_estimate.py:
    D_St = sum_{n>=1} E_n sqrt(nu omega_n / 2),  E_n = 1/2 int_0^1 U_n(x)^2 dx.
The comparison quantity is the fluctuating part D_fluct = Dbar - D(u_mean)
measured in the same runs.
"""

import io
import json

import numpy as np

RE = 500.0
NU = 1.0 / RE
T = 2.0
BASE = "results/09_d2_capture/capture_%s_D2_N256.npz"

rows = []
detail = {}
for b in ("B1", "B2", "B3"):
    d = np.load(BASE % b, allow_pickle=True)
    m = json.loads(str(d["meta"].item()))
    U = np.asarray(d["U_lid_native"], dtype=float)
    x = np.asarray(d["x"], dtype=float)
    nt, nx = U.shape
    dt = T / nt
    k = np.fft.rfftfreq(nt, d=dt)
    omega = 2.0 * np.pi * k
    c = np.fft.rfft(U, axis=0) / nt
    amp = 2.0 * np.abs(c)
    amp[0] = np.abs(c[0])

    E_n = 0.5 * np.trapezoid(amp**2, x, axis=1)
    E_n[0] = np.trapezoid(amp[0] ** 2, x)
    total = E_n.sum()
    ft = 1.0 - E_n[0] / total
    stokes = float(np.sum(E_n[1:] * np.sqrt(NU * omega[1:] / 2.0)))
    peak = float(amp.max(axis=0).max())
    n_dom = int(np.argmax(E_n[1:])) + 1
    frac_top = float(E_n[1:6].sum() / total)
    delta1 = float(np.sqrt(2.0 * NU / omega[1]))
    delta_max = float(np.sqrt(2.0 * NU / omega[min(4, len(omega) - 1)]))

    Dbar = m["eps_cycle_mean"]
    Dfl = Dbar - m["eps_meanfield"]
    Dk = m["K_cycle_mean"]
    Kfl = m["K_fluct"]

    rows.append((b, total, ft, stokes, Dbar, Dfl, Dfl / stokes, n_dom, frac_top))
    detail[b] = dict(E_n=E_n[:6].tolist(), omega=omega[:6].tolist(),
                     total=float(total), ft=float(ft), stokes=stokes,
                     Dbar=Dbar, Dfluct=float(Dfl), fluct_over_stokes=Dfl / stokes,
                     Kbar=Dk, Kfluct=Kfl, n_dom=n_dom, frac_first4=frac_top,
                     lid_peak=peak, delta_n1=delta1, delta_n4=delta_max,
                     cells_n1=delta1 * 256.0, cells_n4=delta_max * 256.0,
                     warm_periods=m["warm_periods"], drift=m["drift"],
                     half_spread=max(m["phase_half_diff"]))
    print("%s  E*=%.4f  f_t=%.4f  peak lid=%.3f  dominant n=%d  first4 share=%.3f"
          % (b, total, ft, peak, n_dom, frac_top))
    print("    E_n (n=0..4): " + "  ".join("%.4f" % v for v in E_n[:5]))
    print("    D_St = %.5f   D_fluct = %.5f   fluct/D_St = %.3f"
          % (stokes, Dfl, Dfl / stokes))
    print("    delta_1/L = %.4f (%.1f cells), delta_4/L = %.4f (%.1f cells)"
          % (delta1, delta1 * 256.0, delta_max, delta_max * 256.0))

print()
hdr = ("branch", "E*", "f_t", "D_St", "Dbar", "D_fluct", "fluct/St", "n_dom", "f(first4)")
print("%-7s %-8s %-7s %-9s %-9s %-9s %-10s %-6s %s" % hdr)
for r in rows:
    print("%-7s %-8.4f %-7.4f %-9.5f %-9.5f %-9.5f %-10.3f %-6d %.3f" % r)

out = "results/stokes_scaling_estimate_d2.json"
io.open(out, "w", encoding="utf-8").write(json.dumps(detail, indent=1))
print("\nwrote", out)
