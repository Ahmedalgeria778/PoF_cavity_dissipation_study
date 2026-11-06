# Spatio-temporal Wall-Actuation Modes and Cycle-Mean Viscous Dissipation in a Lid-Driven Cavity

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Physics of Fluids](https://img.shields.io/badge/Journal-Physics%20of%20Fluids-blue.svg)](https://aip.scitation.org/journal/phf)

## Overview

This repository contains the manuscript, supplementary material, figures, and analysis scripts for the paper submitted to *Physics of Fluids* (2026).

**Title:** Spatio-temporal wall-actuation modes and cycle-mean viscous dissipation in a lid-driven cavity

**Authors:** Beniaiche Ahmed¹,*, Larabi Abderrahim¹, Belkadi Mbarek²

¹ Laboratory of Fluid Mechanics, Ecole Militaire Polytechnique, Algiers, Algeria  
² Laboratory of Turbomachinery, Ecole Militaire Polytechnique, Algiers, Algeria

*Corresponding author: beniaiche_ahmed25@yahoo.fr

## Repository Contents

```
PoF_cavity_dissipation_study/
├── README.md                    # This file
├── LICENSE                      # MIT License
├── CITATION.cff                 # Citation information
├── manuscript/                  # Main manuscript (LaTeX source + compiled PDF)
├── supplementary/               # Supplementary material
│   └── data_appendix/           # Auto-generated appendix tables (.tex) + campaign records (.csv)
├── data/lid_series/             # The three imposed lid waveforms + manifest.csv (SHA-256, shapes, scaling)
├── data/lid_series_n512/        # Same controls resampled on 512 nodes + build report
├── figures/                     # All figures (PDF + PNG)
├── results/                     # Derived records (JSON/TXT), verification runs, run logs
│   ├── 07_d2_smoke/             # omega_1 = pi smoke test of the temporal protocol
│   ├── 08_stokes_analytic/      # single-frequency oscillatory-Stokes verification
│   ├── 09_d2_capture/           # temporal captures (field archives are provided separately)
│   ├── d2_derived/              # every cycle mean, budget, sensitivity record quoted in the text
│   └── p1_gci_iso/              # stationary grid-convergence records
├── scripts/                     # Solver, post-processing and figure scripts
└── docs/                        # Response to the editor / reviewers
```

## Installation

### Requirements

- **Python 3.10+** with: `numpy`, `scipy`, `matplotlib`, `numba` (the lattice-Boltzmann
  kernel in `scripts/run_branch_capture_d2.py` is JIT-compiled, single-threaded, deterministic)
- **LaTeX:** MiKTeX or TeX Live with standard packages

### Setup

```bash
git clone https://github.com/Ahmedalgeria778/PoF_cavity_dissipation_study.git
cd PoF_cavity_dissipation_study
pip install numpy matplotlib scipy numba
```

## Usage

### Temporal campaign (the numbers of Secs. 4-6)

```bash
# 1. Impose the exact waveform period: 256 samples over T = 2, held 40 (N=256)
#    or 80 (N=512) lattice steps, so N_T = 40 N and omega_1 = pi at both grids
python scripts/resample_lid_series_endpoint_false.py     # provenance step: rewrites the two external
#   PINN lid archives (paths at the top of the script) on the endpoint=False grid; their output is
#   committed as data/lid_series/, so re-running it is only needed to regenerate them from the PINN side
python scripts/build_lid_series_n512.py                  # regenerates data/lid_series_n512/

# 2. Capture one branch (add --N 512 for the replicated protocol, --forcing exact for the control)
python scripts/run_branch_capture_d2.py --case B2 --N 256 --forcing hold

# 3. Derived quantities, appendix tables and the acceptance gate
python scripts/d2_derived_quantities.py                  # -> results/d2_derived/d2_summary.json
python scripts/d2_summary_numbers.py
python scripts/d2_extra_quantities.py
python scripts/d2_topology_numbers.py
python scripts/stokes_scaling_estimate_d2.py
python scripts/export_d2_supp_tables.py
python scripts/compare_n256_n512_d2.py                   # exits 0 only if all six captures pass
python scripts/export_resolution_sensitivity_table.py

# 4. Protocol verifications quoted in Secs. S4.1-S4.5
python scripts/smoke_d2_period_lattice.py
python scripts/validate_stokes_analytic.py
python scripts/compare_forcing_staircase.py
python scripts/justify_capture_window.py
python scripts/test_checkpoint_resume.py
```

### Generate Figures

All figure scripts read from `results/` and write to `figures/`.

```bash
# Figures 1 and 2: geometry, stationary modes, and branch signatures
python scripts/make_fig_modes.py

# Figure 3: grid convergence of the stationary controls
python scripts/make_fig_gci.py
# Branch topology of the three captures (main figure and its two supplementary variants)
python scripts/make_fig_branch_topology_d2.py
python scripts/make_fig_branch_topology_d2.py --variant phases8
python scripts/make_fig_branch_topology_d2.py --variant panelscale

# Phase-resolved energetics of the three branches (iso-cycle, velocity, energy panels)
python scripts/make_fig_branch_iso_cycle_d2.py
python scripts/make_fig_branch_velocity_d2.py
python scripts/make_fig_branch_energy_d2.py

# Highlight image for the table of contents
python scripts/make_highlight_image.py
```

Only the pipeline above reproduces this paper. Scripts that predate the temporal
mapping of Sec. 4.2 (the pre-mapping capture drivers, the pre-mapping energy figure, the
pre-mapping Stokes-layer and steady-streaming estimates, and the closure script that read
the superseded `results/06_branch_figures/` captures) are deliberately not distributed
here: they read or write archives that no figure and no table of this paper is built from,
so re-running them could not reproduce any number quoted in the text.

### Raw Data

The committed records are the ones every table and figure is generated from:

- `data/lid_series/` + `manifest.csv` — the three imposed waveforms (256 samples per period, `endpoint=False`), with SHA-256, shape, applied scaling and realised actuation energy
- `results/09_d2_capture/capture_d2_*.log` — run logs of the six temporal captures
- `results/d2_derived/` — `d2_summary.json`, `d2_extra.json`, `topology_numbers.txt`, `capture_window_justification_N256.json`, `staircase_control_B2_N256.json`, `resolution_sensitivity_hold.json`
- `results/streaming_forcing_d2.json`, `results/stokes_scaling_estimate_d2.json`, `results/lid_spatial_decomposition.json`
- `results/07_d2_smoke/`, `results/08_stokes_analytic/` — protocol verifications
- `results/p1_gci_iso/*.csv` — stationary grid-convergence records
- `supplementary/data_appendix/*.csv` and `Paper2_all_campaigns_results.tex` — cell-aggregated record of the 185 identification runs

### Compile Manuscript and Supplementary

The supplement `\input`s `data_appendix/...` and the figures live in the source
directories, so each document must be compiled from its own directory, with the
build output collected in `build/`:

```bash
cd manuscript     && pdflatex -output-directory ../build manuscript_final.tex     && cd ..
cd manuscript     && pdflatex -output-directory ../build manuscript_final.tex     && cd ..
cd supplementary  && pdflatex -output-directory ../build supplementary_final.tex  && cd ..
cd supplementary  && pdflatex -output-directory ../build supplementary_final.tex  && cd ..
python scripts/check_build_logs.py      # parses the four .log files; exit 0 = nothing to fix
```

## Key Results

- Stationary controls at Re=500, iso-energetic at E*=0.25: the first spatial harmonic
  reduces cycle-mean dissipation by **17.7 %** relative to the corner-regularized
  uniform lid, the second harmonic and the mean profile of the quasi-steady two-lobe
  branch increase it by **36.8 %** and **44.3 %**.
- Time-dependent branches: the fluctuating strain field carries **92.9 %**, **53.7 %**
  and **1.8 %** of the cycle-mean cost of the lid-oscillatory, mixed and quasi-steady
  branches. The ordering is B2 > B1 ≈ B3, with B2 the most dissipative by the modest
  factor **1.2** — 20.7 % above B1 and 23.2 % above B3 at N=256 — although its
  mean-field dissipation is fourteen times below its own cycle mean, while B1 and B3
  are nearly equal (2.1 % apart at N=256, 0.5 % at N=512).
- A second-Stokes boundary-layer estimate built from the imposed lid signal alone
  agrees with the measured fluctuating dissipation of the two time-reversing branches
  to within **5 %** and **2 %**, with no adjustable constant. The estimate is a
  half-space model, so it supports a wall-layer interpretation of the fluctuating
  cost rather than a spatial decomposition of the total.
- Grid-refinement sensitivity (N=256 → 512, same protocol): cycle means move by
  **+5.4 %**, **+7.3 %**, **+7.1 %**, the ranking is preserved and the B1-B3 gap
  narrows from 2.1 % to 0.5 %, while the power-balance residual halves — consistent
  with the first-order truncation of the wall-shear estimator.

## Data Availability

The repository contains the manuscript, the supplementary material, all figures, all
analysis scripts, the imposed waveforms with their checksum manifest, the run logs and
every derived record (JSON/TXT/CSV) that the tables and figures are generated from.
The raw phase-resolved field archives of the six temporal captures
(`results/09_d2_capture/capture_*_D2_N{256,512}.npz`, ≈ 0.4 GB, individual files above
GitHub's 100 MB per-file limit) are supplied as files alongside the repository and are
available from the corresponding author upon reasonable request.

## Citation

```bibtex
@article{beniaiche2026spatiotemporal,
  title={Spatio-temporal wall-actuation modes and cycle-mean viscous dissipation in a lid-driven cavity},
  author={Beniaiche, Ahmed and Larabi, Abderrahim and Belkadi, Mbarek},
  journal={Physics of Fluids},
  year={2026},
  publisher={AIP Publishing}
}
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Contact

**Beniaiche Ahmed**  
Email: beniaiche_ahmed25@yahoo.fr  
GitHub: https://github.com/Ahmedalgeria778
