# -*- coding: utf-8 -*-
"""Extra derived quantities (quadrature error, instantaneous deviations,
full-period min/max, vortex centres) -> results/d2_derived/d2_extra.json.
Written to a file because console output is unreliable in this session.
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
CAP = os.path.join(REPO, "results", "09_d2_capture")
OUT = os.path.join(REPO, "results", "d2_derived", "d2_extra.json")
N = 256
DX = 1.0 / (N - 1)
PERIOD = 10240
NPH = 8

res = {}
for c in ("B1", "B2", "B3"):
    d = np.load(os.path.join(CAP, "capture_%s_D2_N256.npz" % c),
                allow_pickle=True)
    m = json.loads(str(d["meta"].item()))
    eps = np.asarray(d["eps_series"], dtype=float)
    per_bin = PERIOD // NPH // 8
    dph = eps[:per_bin * NPH].reshape(NPH, per_bin).mean(axis=1)
    ux_m = np.asarray(d["ux_mean"], dtype=float)
    uy_m = np.asarray(d["uy_mean"], dtype=float)
    ux_r = np.asarray(d["ux_rms"], dtype=float)
    uy_r = np.asarray(d["uy_rms"], dtype=float)
    psi = np.asarray(d["psi_mean"], dtype=float)
    y = np.asarray(d["y"], dtype=float)
    x = np.asarray(d["x"], dtype=float)
    mean_speed = np.hypot(ux_m, uy_m)
    # field-norm deviation of the phase-resolved states from the mean field
    p_ux = np.asarray(d["phase_ux"], dtype=float)
    p_uy = np.asarray(d["phase_uy"], dtype=float)
    dev = [float(np.linalg.norm(p_ux[k] - ux_m) / np.linalg.norm(ux_m))
           for k in range(NPH)]
    # vortex extremes of psi (interior only)
    inner = psi[2:-2, 2:-2]
    jmax, imax = np.unravel_index(np.argmax(inner), inner.shape)
    jmin, imin = np.unravel_index(np.argmin(inner), inner.shape)
    res[c] = dict(
        eightbin_quadrature_D=float(dph.mean()),
        quadrature_error_pct=100.0 * (dph.mean() / m["eps_cycle_mean"] - 1.0),
        D_period_min=float(eps.min()), D_period_max=float(eps.max()),
        D_period_ratio=float(eps.max() / eps.min()),
        mean_profile_abs_peak=float(np.abs(ux_m).max()),
        mean_speed_peak=float(mean_speed.max()),
        rms_over_mean_peak=float(ux_r.max() / mean_speed.max()),
        phase_field_deviation=dev,
        phase_field_deviation_max=float(max(dev)),
        vortex_max_pos=[float(y[jmax + 2]), float(x[imax + 2])],
        vortex_min_pos=[float(y[jmin + 2]), float(x[imin + 2])],
        vortex_max_val=float(inner.max()), vortex_min_val=float(inner.min()),
        energy_half_below_meanfield=float(
            np.trapezoid(np.trapezoid(np.where(y[:, None] <= 0.5,
                                               0.5 * (ux_m ** 2 + uy_m ** 2), 0.0),
                                     dx=DX, axis=1), dx=DX)),
    )

    # lid-profile peaks in U_ref units: time-mean profile vs instantaneous
    ul = np.asarray(d["U_lid_native"], dtype=float)
    u_mean_prof = ul.mean(axis=0)
    cf = np.fft.rfft(ul, axis=0) / ul.shape[0]
    af = 2.0 * np.abs(cf)
    af[0] = np.abs(cf[0])
    prof_peak = float(np.abs(u_mean_prof).max())
    harmonic_peak = float(af.max(axis=0).max())
    inst_peak_wave = float(np.abs(ul).max())
    res[c].update(
        lid_profile_peak=prof_peak,
        lid_harmonic_peak=harmonic_peak,
        lid_instantaneous_peak_waveform=inst_peak_wave,
        Re_max_profile=prof_peak * 500.0,
        Re_max_instantaneous=inst_peak_wave * 500.0,
    )

with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(res, fh, indent=1)
