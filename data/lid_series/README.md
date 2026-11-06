# Lid-actuation waveforms used by the temporal (D2) campaign

These are the three time-dependent wall-actuation series that were transferred to
the MRT-LBM solver for the branch captures reported in Sec. 6 of the manuscript and
in Sec. S4.6 of the supplement. They are the exported outputs of the PINN control
network, resampled to 256 samples per period with `endpoint=False`
(`scripts/resample_lid_series_endpoint_false.py`), which is what the solver reads.

| file | branch | content |
| --- | --- | --- |
| `fourier_Re500.npz` | $B_1$ | full Fourier-series control at $Re=500$, $E^\ast=0.25$ |
| `B2_seed5_E025_re500_e0.25.npz` | $B_2$ | seed 5 of the temporally dominated class |
| `B3_seed0_E025_re500_e0.25.npz` | $B_3$ | seed 0 of the residual class |

## Array layout

Each file stores `U_series` of shape `(NT_PER, N_LBM)`, i.e. `U_series[n, i]` is the
prescribed lid velocity, in cavity units ($U_{\mathrm{ref}}=1$), at streamwise node
`i` of a $256\times256$ lattice at sample `n` of the period.

* `NT_PER = 256`, `T_PERIOD = 2.0` (cavity units of time), `N = 256` nodes per side.
* The solver holds each sample for `SLOWDOWN = 40` lattice steps, so one forcing
  period is $10\,240$ lattice steps and $\Delta t_{\mathrm{phys}} = U_{\mathrm{ref}}/N$,
  which reproduces $T_{\mathrm{phys}} = 10\,240 \times 1.953\times10^{-4} = 2.0$ and
  $\omega_1 = 2\pi/T = \pi$ exactly (Sec. S4.5 of the supplement).
* $B_1$ is the only control multiplied by a scalar before transfer
  ($0.99328$, native energy $0.25339 \to 0.25000$); $B_2$ and $B_3$ are used as
  exported, at native energy $0.25000$.

`manifest.csv` gives the SHA-256 of each file, its shape, the scale applied and the
cycle-mean actuation energy realised in the solver.

## Reproducing a capture

```
py scripts/run_branch_capture_d2.py --case B1     # or B2, B3
```

The runner reads these files first and falls back to the external PINN output
directory, so the captures of `results/09_d2_capture/` can be reproduced from this
repository alone (Numpy/Numba environment, Sec. S5.1).
