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
│   ├── 09_d2_capture/           # temporal capture logs + MANIFEST.md (the field archives themselves ship separately)
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
python scripts/lid_modal_fractions.py                     # modal fractions of the three imposed series
python scripts/export_legacy_supp_tables.py              # the five appendix tables of the stationary campaign
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

All figure scripts read from `results/` and write to `figures/`, and the build
refreshes the copies in `manuscript/figures/` and `supplementary/figures/` from them;
Main Fig. 4 is the single exception, listed in `docs/PACKAGE_CERTIFICATION.md`.

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

# Figure 4 (the mechanism panels) is the one figure not redrawn here: it is rendered
# from the steady field files of the stationary N=512 campaign, held outside the tree
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
- `results/09_d2_capture/MANIFEST.md` — filenames, byte sizes and SHA-256 of the seven field archives shipped outside the git tree
- `results/10_fig4_stationary_fields/FIELDS_MANIFEST.md` — filenames, byte sizes and SHA-256 of the three steady \(N=512\) field archives Main Fig. 4 is rendered from, which are also held outside the git tree, with the strain-rate magnitudes of Sec. 5.3 recomputed from them
- `results/d2_derived/` — `d2_summary.json`, `d2_extra.json`, `lid_modal_fractions.json`, `topology_numbers.txt`, `capture_window_justification_N256.json`, `staircase_control_B2_N256.json`, `resolution_sensitivity_hold.json`
- `results/streaming_forcing_d2.json`, `results/stokes_scaling_estimate_d2.json`, `results/lid_spatial_decomposition.json`
- `results/07_d2_smoke/`, `results/08_stokes_analytic/` — protocol verifications
- `results/p1_gci_iso/*.csv` — stationary grid-convergence records, the input of the three `p1_table_*.tex` appendix tables
- `results/01_ReE_star_map/branch_runs.csv` — one row per identification run (185 runs), with \(f_2\) and \(f_t\); the input of `p3_table_threshold.tex`
- `results/02_lambda_var/*.csv` — the \(\lambda_{\mathrm{var}}=0\) ablation runs with their modal shares; the input of `p2_table_bfirst_ablation.tex`
- `supplementary/data_appendix/*.csv` and `Paper2_all_campaigns_results.tex` — cell-aggregated record of the 185 identification runs

Every appendix table and every figure, Main Fig. 4 included, is therefore written by
a committed script; what the scripts read is split between committed derived records
and raw fields held outside the git tree. `scripts/make_fig_mechanism.py` renders
Fig. 4 from the three steady velocity files of the stationary \(N=512\) campaign
(uniform lid, \(k=1\), \(k=2\)); `scripts/manifest_fig4_fields.py` inventories them by
filename, byte size and SHA-256 in
[`results/10_fig4_stationary_fields/FIELDS_MANIFEST.md`](results/10_fig4_stationary_fields/FIELDS_MANIFEST.md),
recomputes the peak and interior-mean strain-rate magnitudes of Sec. 5.3 from them and
fails if they no longer match. `python scripts/certify_package.py`
regenerates [`docs/PACKAGE_CERTIFICATION.md`](docs/PACKAGE_CERTIFICATION.md), which
lists each resource the two documents pull in, the script that writes it, and the page
count and checksum of the compiled PDFs. It also counts the words of the manuscript
abstract (each inline math span as one word) and fails above the 250-word submission
limit.

### Compile Manuscript and Supplementary

The supplement `\input`s `data_appendix/...` and the figures live in the source
directories, so each document must be compiled from its own directory, with the
build output collected in `build/`:

```bash
sh scripts/build_all.sh   # 3 passes per document, then all three gates
```

which is equivalent to, and safer than, doing it by hand:

```bash
for i in 1 2 3; do cd manuscript    && pdflatex -output-directory ../build manuscript_final.tex    && cd ..; done
for i in 1 2 3; do cd supplementary && pdflatex -output-directory ../build supplementary_final.tex && cd ..; done
python scripts/check_build_logs.py      # parses the four .log files; exit 0 = nothing to fix
```

The bibliography has two gates of its own. `python scripts/check_bibliography.py`
verifies that every citation key resolves in the document that uses it, that no
`\bibitem` is left uncited, and that the entries shared by the manuscript and the
supplement agree verbatim (a divergent copy is how a wrong volume or page range survives
one round of editing). `python scripts/audit_references_crossref.py` goes to the
publisher: for each entry it takes the quoted title and year, queries Crossref and prints
the recorded volume, pages and year next to the local text, flagging every disagreement;
`--show-keys k1,k2` lists all candidates for a flagged entry when the search hit is not
the right record. Monographs carry no quoted title and are reported as unmatched by
design.

A third script is advisory on purpose. `python scripts/check_style.py [file ...]`
extracts the running text of a document (comments, display math, floats, section
headings and bibliography entries removed) and prints the counts of the connectives and
set phrases that give away templated writing, with the line numbers where they occur,
plus the distribution of sentence openings and the longest sentences. It reports and
never fails: a style count is not a correctness criterion, so it is not one of the
`build_all.sh` gates.

Two letters go with the papers. `docs/RESPONSE_TO_EDITOR_summary.tex` is the
short response addressed to the Deputy Editor: it answers the pre-review
comments in the order they were given and is signed on behalf of the authors,
without repeating the revision details. `docs/RESPONSE_TO_EDITOR.tex` is the
complete point-by-point reply to all sixty-three comments, nine from the Deputy
Editor and fifty-four from the reviewers, and it remains the record of the
revision; the summary letter does not replace it. Both are rebuilt by
`build_all.sh`.

The two marked-up copies diff against the previous submission round and need one extra
pass each (their table of contents shifts between runs):

```bash
py scripts/mark_manuscript.py build/_mark_base/old_manuscript.tex     manuscript/manuscript_final.tex     manuscript/manuscript_final_marked.tex
py scripts/mark_manuscript.py build/_mark_base/old_supplementary.tex  supplementary/supplementary_final.tex supplementary/supplementary_final_marked.tex
cd manuscript     && for i in 1 2 3; do pdflatex -output-directory ../build manuscript_final_marked.tex; done                  && cd ..
cd supplementary  && for i in 1 2 3; do pdflatex -output-directory ../build supplementary_final_marked.tex; done               && cd ..
python scripts/certify_package.py       # -> docs/PACKAGE_CERTIFICATION.md
```

Always compile with `-output-directory ../build`: an `.aux` left in the source
directory is read in preference to the one just written, which silently resurrects the
labels and citations of the previous round.

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
  agrees with the measured fluctuating dissipation of the lid-oscillatory and mixed
  branches (B2, whose lid reverses over the whole span, and B3, whose reversing band
  is the central 36 % of it)
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
The raw phase-resolved field archives are the only data held outside the git tree: the
six branch captures (`results/09_d2_capture/capture_*_D2_N{256,512}.npz`, 419.90 MB)
plus the exact-in-time control (`capture_B2_D2_N256_exact.npz`, 28.24 MB), 448.15 MB
in total, of which the three `N=512` files exceed GitHub's 100 MB per-file limit for a
git tree. They ship as the single bundle `PoF_d2_captures_v1.tar`, indexed by the
committed [`results/09_d2_capture/MANIFEST.md`](results/09_d2_capture/MANIFEST.md),
which lists each filename, byte size and SHA-256 so that a copy obtained from the
corresponding author can be verified before the scripts are re-run. The bundle is
supplied alongside the submission and is available from the corresponding author upon
reasonable request.

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
