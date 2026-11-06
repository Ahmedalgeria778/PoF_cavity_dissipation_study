"""Topology and streaming-forcing numbers for the three D2 branch captures.

Writes ASCII facts to results/d2_derived/topology_numbers.txt, for Sec. 5.4 of
the manuscript. Two blocks:

 (1) mean-field organization: peak speeds, stream-function extrema and their
     locations, and the height that halves the mean-field kinetic energy.
 (2) Reynolds-stress forcing of the mean flow (steady-streaming diagnostic),
     identical definitions to scripts/streaming_forcing_diagnostic.py:
        u'_i(x,y,phi_k) = phase_u_i[k] - <u_i>
        tau_ij = <u'_i u'_j>_phase
        F_i    = -d_j tau_ij
        S_om   = d_x F_y - d_y F_x
     compared to the mean viscous term nu laplacian(<u>).
"""

import io
import json

import numpy as np

RE = 500.0
NU = 1.0 / RE
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


def argloc(a, x, y):
    i = np.unravel_index(np.argmax(a), a.shape)
    return float(x[i[1]]), float(y[i[0]]), int(i[0]), int(i[1])


out = []
stream = {}


def log(s):
    out.append(s)
    print(s)


for b in ("B1", "B2", "B3"):
    d = np.load("results/09_d2_capture/capture_%s_D2_N256.npz" % b)
    m = json.loads(str(d["meta"].item()))
    x, y = d["x"], d["y"]
    n = len(x)
    h = 1.0 / (n - 1)
    ux_m, uy_m = d["ux_mean"], d["uy_mean"]
    psi = d["psi_mean"]
    speed = np.hypot(ux_m, uy_m)
    log("=== %s ===" % b)
    log("mean_speed_peak %.5f" % speed[EXCL:-EXCL, EXCL:-EXCL].max())
    xp, yp, _, _ = argloc(interior(speed), x, y)
    log("mean_speed_peak_at %.4f %.4f" % (xp, yp))
    log("psi_min %.6f psi_max %.6f" % (psi.min(), psi.max()))
    a = argloc(psi, x, y)
    bb = argloc(-psi, x, y)
    log("psi_max_at %.4f %.4f  psi_min_at %.4f %.4f" % (a[0], a[1], bb[0], bb[1]))
    # mean-field kinetic energy cumulative in y
    ke_row = np.trapezoid(0.5 * (ux_m ** 2 + uy_m ** 2), x)
    cum = np.cumsum(ke_row) / ke_row.sum()
    y_half = float(np.interp(0.5, cum, y))
    y_90 = float(np.interp(0.9, cum, y))
    log("mean_ke_half_below_y %.4f  nine_tenth_above_y %.4f" % (y_half, y_90))
    log("frac_mean_ke_above_y0.9 %.4f" % (1.0 - cum[int(0.9 * (n - 1))]))
    # fluctuation amplitude and stationarity
    pu, pv = d["phase_ux"], d["phase_uy"]
    up, vp = pu - ux_m[None], pv - uy_m[None]
    ux_rms, uy_rms = d["ux_rms"], d["uy_rms"]
    ir = np.unravel_index(np.argmax(interior(ux_rms)), interior(ux_rms).shape)
    log("ux_rms_peak %.5f at x %.4f y %.4f" %
        (interior(ux_rms)[ir], x[EXCL:-EXCL][ir[1]], y[EXCL:-EXCL][ir[0]]))
    log("uy_rms_peak %.5f" % uy_rms.max())
    dev = [float(np.sqrt(np.mean((pu[k] - ux_m) ** 2 + (pv[k] - uy_m) ** 2))
                 / np.sqrt(np.mean(ux_m ** 2 + uy_m ** 2))) for k in range(pu.shape[0])]
    log("phase_dev_over_mean_rms_max %.4f" % max(dev))
    norm_dev = [float(np.linalg.norm(np.concatenate([pu[k] - ux_m, pv[k] - uy_m]))
                      / np.linalg.norm(np.concatenate([ux_m, uy_m])))
                for k in range(pu.shape[0])]
    log("phase_field_deviation_max %.4f" % max(norm_dev))
    # Reynolds-stress forcing
    tuu = np.mean(up ** 2, axis=0)
    tvv = np.mean(vp ** 2, axis=0)
    tuv = np.mean(up * vp, axis=0)
    Fx = -(d1(tuu, 1) + d1(tuv, 0)) / (2.0 * h)
    Fy = -(d1(tuv, 1) + d1(tvv, 0)) / (2.0 * h)
    So = (d1(Fy, 1) - d1(Fx, 0)) / (2.0 * h)
    visc_x = NU * (d1(d1(ux_m, 1), 1) + d1(d1(ux_m, 0), 0)) / h ** 2
    visc_y = NU * (d1(d1(uy_m, 1), 1) + d1(d1(uy_m, 0), 0)) / h ** 2
    F_mag = np.hypot(interior(Fx), interior(Fy))
    v_mag = np.hypot(interior(visc_x), interior(visc_y))
    log("tau_uu_lid %.6f tau_uu_max %.6f tau_uu_lid_peak_x %.4f" %
        (tuu[-1 - EXCL].max(), interior(tuu).max(),
         x[EXCL:-EXCL][np.argmax(tuu[-1 - EXCL, EXCL:-EXCL])]))
    log("rms_F %.6e rms_visc %.6e ratio_rms %.5f" %
        (np.sqrt(np.mean(F_mag ** 2)), np.sqrt(np.mean(v_mag ** 2)),
         np.sqrt(np.mean(F_mag ** 2)) / np.sqrt(np.mean(v_mag ** 2))))
    log("F_max %.6e visc_max %.6e ratio_max %.5f" %
        (F_mag.max(), v_mag.max(), F_mag.max() / v_mag.max()))
    iS = np.unravel_index(np.argmax(np.abs(interior(So))), interior(So).shape)
    log("S_peak %.4f at x %.4f y %.4f" %
        (interior(So)[iS], x[EXCL:-EXCL][iS[1]], y[EXCL:-EXCL][iS[0]]))
    iF = np.unravel_index(np.argmax(F_mag), F_mag.shape)
    log("F_peak %.4f at x %.4f y %.4f" %
        (F_mag.max(), x[EXCL:-EXCL][iF[1]], y[EXCL:-EXCL][iF[0]]))
    top = interior(So)[int(0.75 * So.shape[0]) - EXCL:, :]
    log("top_quarter_positive_frac %.3f" % float((top > 0).mean()))
    stream[b] = dict(
        tau_uu_lid=float(tuu[-1 - EXCL].max()),
        tau_uu_max=float(interior(tuu).max()),
        rms_F=float(np.sqrt(np.mean(F_mag ** 2))),
        rms_visc=float(np.sqrt(np.mean(v_mag ** 2))),
        ratio_rms=float(np.sqrt(np.mean(F_mag ** 2)) /
                        np.sqrt(np.mean(v_mag ** 2))),
        F_max=float(F_mag.max()), visc_max=float(v_mag.max()),
        ratio_max=float(F_mag.max() / v_mag.max()),
        S_peak=float(interior(So)[iS]), S_peak_x=float(x[EXCL:-EXCL][iS[1]]),
        S_peak_y=float(y[EXCL:-EXCL][iS[0]]),
        F_peak=float(F_mag.max()), F_peak_x=float(x[EXCL:-EXCL][iF[1]]),
        F_peak_y=float(y[EXCL:-EXCL][iF[0]]),
        tau_uu_lid_peak_x=float(x[EXCL:-EXCL][np.argmax(tuu[-1 - EXCL, EXCL:-EXCL])]),
        mean_speed_peak=float(speed[EXCL:-EXCL, EXCL:-EXCL].max()),
        psi_extrema=[float(psi.min()), float(psi.max())],
        mean_ke_half_y=y_half,
        phase_field_deviation_max=float(max(norm_dev)),
    )
    # integral measures
    kmf = 0.5 * np.trapezoid(np.trapezoid(ux_m ** 2 + uy_m ** 2, x), y)
    log("K_meanfield %.6e  K_cyclemean %.6e  ratio %.4f" %
        (kmf, m["K_cycle_mean"], kmf / m["K_cycle_mean"]))
    ce = np.asarray(d["cyc_eps"], dtype=float)
    ck = np.asarray(d["cyc_K"], dtype=float)
    n = len(ce)
    first = ce[: n // 2].mean() - ce[n // 2:].mean()
    kdrift = abs(ck[: n // 2].mean() - ck[n // 2:].mean()) / m["eps_cycle_mean"]
    log("drift_D_first_minus_last_half_pct %+.4e" % (100.0 * first / ce.mean()))
    log("K_halfwindow_drift_over_Dbar_pct %+.4e" % (100.0 * kdrift))
    log("cycle_to_cycle_sd_rel_D %.4e  K %.4e" %
        (np.std(ce, ddof=1) / ce.mean(), np.std(ck, ddof=1) / ck.mean()))
    log("")

io.open("results/d2_derived/topology_numbers.txt", "w",
        encoding="utf-8").write("\n".join(out) + "\n")
io.open("results/streaming_forcing_d2.json", "w",
        encoding="utf-8").write(json.dumps(stream, indent=1))
