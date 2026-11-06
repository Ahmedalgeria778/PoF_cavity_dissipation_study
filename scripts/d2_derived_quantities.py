# -*- coding: utf-8 -*-
"""All derived quantities of the branch captures, computed exclusively from
results/09_d2_capture/capture_B?_D2_N256.npz.

Produces results/d2_derived/d2_summary.json with every number quoted in the
manuscript tables (tab:modes, tab:cycle, tab:budget), in Sec. cycle-mean
comparison, Sec. topology and Sec. energy budget, plus the phase-resolved
dissipation/power series needed by the figure scripts.
"""
import json
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, ".."))
CAP = os.path.join(REPO, "results", "09_d2_capture")
OUTDIR = os.path.join(REPO, "results", "d2_derived")
OUT = os.path.join(OUTDIR, "d2_summary.json")

CASES = ["B1", "B2", "B3"]
RE = 500.0
N = 256
DX = 1.0 / (N - 1)
PERIOD = 10240
N_PHASE = 8


def trapz2(a, dx):
    return float(np.trapezoid(np.trapezoid(a, dx=dx, axis=1), dx=dx))


def load(case):
    d = np.load(os.path.join(CAP, "capture_%s_D2_N256.npz" % case),
                allow_pickle=True)
    m = json.loads(str(d["meta"].item()))
    out = {k: np.asarray(d[k], dtype=float) for k in
           ("ux_mean", "uy_mean", "ux_rms", "uy_rms", "psi_mean",
            "phase_ux", "phase_uy", "phase_cnt",
            "U_lid_native", "E_act_native", "E_act_series",
            "t_series", "eps_series", "K_series", "P_series",
            "E_act_series_t", "lid_error_series",
            "cyc_eps", "cyc_K", "cyc_P", "cyc_E")}
    out["x"] = np.asarray(d["x"], dtype=float)
    out["y"] = np.asarray(d["y"], dtype=float)
    return m, out


def phase_binned(arr, stride=8):
    """Average a stride-sampled time series over one period into N_PHASE bins."""
    per_bin = PERIOD // N_PHASE // stride          # 128 samples
    v = np.asarray(arr, dtype=float)[:per_bin * N_PHASE]
    return v.reshape(N_PHASE, per_bin).mean(axis=1)


def tau1(ux):
    return (RE ** -1.0) * (ux[N - 1, :] - ux[N - 2, :]) / DX


def tau2(ux):
    return (RE ** -1.0) * (3.0 * ux[N - 1, :] - 4.0 * ux[N - 2, :]
                           + ux[N - 3, :]) / (2.0 * DX)


def power(u_wall, tau):
    return float(np.sum(u_wall[1:-1] * tau[1:-1]) * DX)


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    report = {}
    for c in CASES:
        m, a = load(c)
        ux_m, uy_m = a["ux_mean"], a["uy_mean"]
        ux_r, uy_r = a["ux_rms"], a["uy_rms"]
        speed_mean = np.hypot(ux_m, uy_m)
        y = a["y"]
        Dbar = m["eps_cycle_mean"]
        Kbar = m["K_cycle_mean"]

        # --- streamfunction of the mean field ---------------------------
        psi = np.asarray(a["psi_mean"], dtype=float)
        psi_max = float(psi.max())
        psi_min = float(psi.min())
        i_max = int(np.unravel_index(np.argmax(psi), psi.shape)[1])
        j_max = int(np.unravel_index(np.argmax(psi), psi.shape)[0])
        i_min = int(np.unravel_index(np.argmin(psi), psi.shape)[1])
        j_min = int(np.unravel_index(np.argmin(psi), psi.shape)[0])

        # --- kinetic-energy partition between the two halves ------------
        kdens = 0.5 * (ux_m ** 2 + uy_m ** 2)
        below = trapz2(np.where((y[:, None] <= 0.5), kdens, 0.0), DX)
        above = trapz2(np.where((y[:, None] > 0.5), kdens, 0.0), DX)

        # --- fluctuation field statistics -------------------------------
        ux_rms_max = float(ux_r.max())
        uy_rms_max = float(uy_r.max())
        idx = np.unravel_index(np.argmax(ux_r), ux_r.shape)

        # --- waveform statistics ----------------------------------------
        ul = a["U_lid_native"]
        lid_peak = float(np.abs(ul).max())
        e_per_phase = a["E_act_native"]
        f2, ft = spatial_temporal_fractions(a, m)

        # --- phase-resolved dissipation / power (8 bins of 1/8 period) ---
        d_ph = phase_binned(a["eps_series"])
        p_ph = phase_binned(a["P_series"])
        k_ph = phase_binned(a["K_series"])
        d_mean_field_ph = float(np.mean(d_ph))
        half_spread = 0.5 * (d_ph.max() - d_ph.min())

        # --- wall-power closure, eight-phase quadrature -----------------
        w = a["phase_cnt"] / a["phase_cnt"].sum()
        p_ux = a["phase_ux"]
        u_lid_full = np.asarray(np.load(
            os.path.join(CAP, "capture_%s_D2_N256.npz" % c),
            allow_pickle=True)["U_lid_series"], dtype=float)
        p_rec = p_pre = 0.0
        for k in range(N_PHASE):
            tau = tau1(p_ux[k])
            p_rec += w[k] * power(p_ux[k][N - 1], tau)
            sl = u_lid_full[k * PERIOD // N_PHASE:(k + 1) * PERIOD // N_PHASE]
            p_pre += w[k] * power(sl.mean(axis=0), tau)
        t1 = tau1(ux_m)
        t2 = tau2(ux_m)
        mf1 = power(ux_m[N - 1], t1)
        mf2 = power(ux_m[N - 1], t2)

        # --- block uncertainty over the captured cycles -----------------
        cyc = a["cyc_eps"]
        blocks = np.array_split(cyc, 4)
        bmeans = np.array([b.mean() for b in blocks])
        sd_block = float(bmeans.std(ddof=1))
        t_crit = 3.182
        sigma_D = sd_block / 2.0 * t_crit     # stderr of blocks × t (block mean sd)

        report[c] = dict(
            meta=m,
            Dbar=Dbar, Dmf=m["eps_meanfield"],
            Dfluct=Dbar - m["eps_meanfield"],
            fluct_share=(Dbar - m["eps_meanfield"]) / Dbar,
            ratio_Dbar_Dmf=Dbar / m["eps_meanfield"],
            Kbar=Kbar, Kmf=m["K_meanfield"], Kfluct=m["K_fluct"], R_K=m["R_K"],
            Pbar=m["P_cycle_mean"], Pmf=m["P_meanfield"],
            K_ratio_mean_over_cycle=m["K_meanfield"] / Kbar,
            speed_mean_peak=float(speed_mean.max()),
            ux_mean_peak=float(np.abs(ux_m).max()),
            psi_max=psi_max, psi_min=psi_min,
            psi_center_max=[float(y[j_max]), float(a["x"][i_max])],
            psi_center_min=[float(y[j_min]), float(a["x"][i_min])],
            ux_rms_peak=ux_rms_max, ux_rms_peak_pos=[float(y[idx[0]]), float(a["x"][idx[1]])],
            uy_rms_peak=uy_rms_max,
            mean_energy_fraction_below_half=below / (below + above),
            lid_peak=lid_peak, Re_max_lid=lid_peak * RE,
            f2_spatial=f2, ft_temporal=ft,
            D_phase=d_ph.tolist(), P_phase=p_ph.tolist(), K_phase=k_ph.tolist(),
            D_half_spread=half_spread,
            D_min_phase=float(d_ph.min()), D_max_phase=float(d_ph.max()),
            D_ratio_within_cycle=float(d_ph.max() / d_ph.min()),
            P_negative_fraction_phase=float((p_ph < 0).mean()),
            P_negative_fraction_series=float((a["P_series"] < 0).mean()),
            K_ratio_within_cycle=float(k_ph.max() / k_ph.min()),
            eps_series_min=float(a["eps_series"].min()),
            eps_series_max=float(a["eps_series"].max()),
            P_rec_8phase=p_rec, residual_rec_8phase_pct=100.0 * (p_rec / Dbar - 1.0),
            P_prescribed_8phase=p_pre,
            residual_prescribed_8phase_pct=100.0 * (p_pre / Dbar - 1.0),
            residual_solver_series_pct=100.0 * (m["P_cycle_mean"] / Dbar - 1.0),
            meanfield_D=m["eps_meanfield"],
            meanfield_P_rec_first=mf1,
            residual_meanfield_first_pct=100.0 * (mf1 / m["eps_meanfield"] - 1.0),
            meanfield_P_rec_second=mf2,
            residual_meanfield_second_pct=100.0 * (mf2 / m["eps_meanfield"] - 1.0),
            cycle_sd_relative=float(cyc.std() / Dbar),
            block_sigma_relative=sigma_D / Dbar,
            lid_max_error=m["lid_max_error"],
        )

    # cross-branch ratios
    r = report
    r["ratios"] = dict(
        B2_over_B1_D=r["B2"]["Dbar"] / r["B1"]["Dbar"],
        B2_over_B3_D=r["B2"]["Dbar"] / r["B3"]["Dbar"],
        B1_over_B3_D=r["B1"]["Dbar"] / r["B3"]["Dbar"],
        B1_over_k1=r["B1"]["Dbar"] / 6.88e-3,
        B2_over_k1=r["B2"]["Dbar"] / 6.88e-3,
        B3_over_k1=r["B3"]["Dbar"] / 6.88e-3,
        B1_over_uniform=r["B1"]["Dbar"] / 9.48e-3,
        B2_over_uniform=r["B2"]["Dbar"] / 9.48e-3,
        B3_over_uniform=r["B3"]["Dbar"] / 9.48e-3,
        Kbar_B1_over_B2=r["B1"]["Kbar"] / r["B2"]["Kbar"],
    )

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(r, fh, indent=1)
    print("wrote", OUT)
    for c in CASES:
        d = r[c]
        print("%s  Dbar=%.5e  Dmf=%.5e  ratio=%.2f  fluct=%.1f%%  lid_peak=%.3f" %
              (c, d["Dbar"], d["Dmf"], d["ratio_Dbar_Dmf"],
               100 * d["fluct_share"], d["lid_peak"]))
        print("    Kbar=%.5e Kmf/Kbar=%.3f R_K=%.4f  |u|mean_peak=%.3f  psi=[%.4f,%.4f]" %
              (d["Kbar"], d["K_ratio_mean_over_cycle"], d["R_K"],
               d["speed_mean_peak"], d["psi_min"], d["psi_max"]))
        print("    ux_rms_peak=%.3f  energy below y=0.5: mean=%.3f" %
              (d["ux_rms_peak"], d["mean_energy_fraction_below_half"]))
        print("    D(t) phase: min=%.4e max=%.4e ratio=%.2f halfspread=%.2e" %
              (d["D_min_phase"], d["D_max_phase"], d["D_ratio_within_cycle"],
               d["D_half_spread"]))
        print("    P 8-phase rec=%.5e (%+.2f%%)  prescribed (%+.2f%%)  series (%+.2f%%)" %
              (d["P_rec_8phase"], d["residual_rec_8phase_pct"],
               d["residual_prescribed_8phase_pct"], d["residual_solver_series_pct"]))
        print("    meanfield P_rec 1st=%+.2f%%  2nd=%+.2f%%  negP=%.3f  rel sd=%.1e  sigma=%.1e" %
              (d["residual_meanfield_first_pct"], d["residual_meanfield_second_pct"],
               d["P_negative_fraction_series"], d["cycle_sd_relative"],
               d["block_sigma_relative"]))
        print("    f2=%.3f ft=%.3f  psi_max center=%s" % (d["f2_spatial"], d["ft_temporal"], d["psi_center_max"]))


def spatial_temporal_fractions(a, m):
    """f2: share of the k=2 spatial harmonic in the cycle-mean lid profile
    (Parseval over the Chebyshev-free sine basis used by the identification);
    ft: share of the temporal (n>=1) energy in the imposed waveform."""
    ul = a["U_lid_native"]
    x = a["x"]
    # temporal split, one period, endpoint-excluded sampling
    c = np.fft.rfft(ul, axis=0) / ul.shape[0]
    amp = 2.0 * np.abs(c)
    amp[0] = np.abs(c[0])
    e = 0.5 * np.trapezoid(amp ** 2, x, axis=1)
    e[0] = np.trapezoid(amp[0] ** 2, x)
    ft = float(1.0 - e[0] / e.sum())
    # spatial split of the cycle-mean profile into sine harmonics
    um = ul.mean(axis=0)
    kk = np.arange(1, 7)
    coef = np.array([2.0 * np.trapezoid(um * np.sin(k * np.pi * x), x)
                     for k in kk])
    tot = float(np.trapezoid(um ** 2, x))
    f2 = float((coef[1] ** 2) / 2.0 / tot) if tot > 0 else float("nan")
    return f2, ft


if __name__ == "__main__":
    main()
