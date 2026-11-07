# Field-capture archives of the temporal (D2) campaign

These are the seven step-by-step field captures that every temporal number of the
manuscript and of the supplement is computed from. They are **not** hosted in the git
tree: each `N=512` archive exceeds GitHub's 100 MB per-file limit for a git tree, and
committing the whole set would add 0.45 GB of arrays to a repository whose text is
fully reproducible without them (`*.npz` is therefore ignored; see `.gitignore`). They
are supplied separately as the single bundle `PoF_d2_captures_v1.tar` (448.15 MB of
archive contents) and are available from the corresponding author on reasonable
request.

Everything the paper needs as *input* (the lid waveforms in `data/lid_series/` and
`data/lid_series_n512/`), as *provenance* (the run logs in this directory,
`results/07_d2_smoke/`, `results/08_stokes_analytic/`, `results/p1_gci_iso/`) or as
*derived record* (`results/d2_derived/`, `results/streaming_forcing_d2.json`,
`results/stokes_scaling_estimate_d2.json`) **is** committed, so each quoted number can
be regenerated from the repository alone; only the arrays of phase-resolved fields
themselves travel separately.

## Contents of the bundle

| file | role in the paper | bytes | MB |
| --- | --- | --- | --- |
| `capture_B1_D2_N256.npz` | $B_1$ full Fourier series, headline resolution | 28 778 530 | 28.78 |
| `capture_B2_D2_N256.npz` | $B_2$ seed 5, temporally dominated branch | 28 598 549 | 28.60 |
| `capture_B3_D2_N256.npz` | $B_3$ seed 0, residual branch | 28 724 393 | 28.72 |
| `capture_B1_D2_N512.npz` | $B_1$ on the finer lattice (grid sensitivity) | 111 477 006 | 111.48 |
| `capture_B2_D2_N512.npz` | $B_2$ on the finer lattice (grid sensitivity) | 111 017 805 | 111.02 |
| `capture_B3_D2_N512.npz` | $B_3$ on the finer lattice (grid sensitivity) | 111 304 629 | 111.30 |
| `capture_B2_D2_N256_exact.npz` | exact-in-time command control for $B_2$ | 28 244 935 | 28.24 |

The six branch captures ($3\times N=256$, $3\times N=512$) total 419 900 912 bytes
(419.90 MB); the exact-in-time control adds 28 244 935 bytes, for 448 145 847 bytes
(448.15 MB) for the bundle contents.

## SHA-256 of each archive

```
1e96a0f7914aa958525720a71e3b701f4f267d6f9b1ab061bc7a3f8a27e311a2  capture_B1_D2_N256.npz
eb9d6cbac34483e58840f95bf9e9ebc08ba36185aceb0fcd25e114f76ecf5078  capture_B2_D2_N256.npz
e3ed93476eba1d44093afd471edd2abcdd9153791e66fc22e5c988946edbeed4  capture_B3_D2_N256.npz
a0d7d2e3873a113651145e58c8a461ae9c7d7f809f6d0fdbe239225dd2e88a96  capture_B1_D2_N512.npz
9e61ca34d212741cf2ab408d1e8adfb1b773b3278dce0642940eb94e513cdba6  capture_B2_D2_N512.npz
1d4ab31b873c2328061a571e75ed9e9f13c35dbad58fe78a08c8a15aa6b6acc9  capture_B3_D2_N512.npz
0fb90183dff8bf61159d1901eb30f38b0d087d096828346fdf8f469cae3c3da2  capture_B2_D2_N256_exact.npz
```

A reader who obtains a copy from the authors can therefore check it against this
committed manifest before re-running the post-processing scripts.

## Array layout

Each archive stores, for one control and one resolution: the step-by-step dissipation,
kinetic-energy and lid-power series, the imposed and the recovered lid records, the
eight phase-resolved velocity fields of each of the 32 captured periods, and the
time-mean and r.m.s. fields. `run_branch_capture_d2.py` writes them and
`d2_derived_quantities.py`, `d2_extra_quantities.py`, `d2_summary_numbers.py`,
`d2_topology_numbers.py`, `compare_n256_n512_d2.py`, `compare_forcing_staircase.py`
and the figure scripts read them.

## Checksums recomputed on

2026-11-07, from `results/09_d2_capture/` of the working tree that produced the
submitted files.
