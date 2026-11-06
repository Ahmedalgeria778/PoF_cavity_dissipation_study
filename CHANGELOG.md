# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-11-06

### Added
- Temporal mapping of the imposed actuation, stated once and used everywhere:
  `T = 2` cavity units, `dt_phys = U_ref/N`, `N_T = 40 N` lattice steps per forced
  period (`10 240` at `N = 256`, `20 480` at `N = 512`), each of the 256 exported
  waveform samples held for `N_T/256` steps, so `omega_1 = pi` and the staircase is
  resolution common-mode (Sec. 4.2, Sec. S4.5).
- `scripts/lid_command.py`: spectral projection of an archived lid series onto the
  `sin((i+1) pi x) cos(j pi t)` basis with an exactness gate, plus time-exact
  re-evaluation at arbitrary `(x, t)`.
- `scripts/build_lid_series_n512.py` and `data/lid_series_n512/`: the same three
  controls on 512 nodes, with a build report proving the actuation energy is
  resolution-independent to 2e-16.
- `scripts/run_branch_capture_d2.py`: checkpointed branch capture with `--N`,
  `--forcing`, `--smoke` and `--bench`; bit-exactness of kill/resume verified by
  `scripts/test_checkpoint_resume.py`.
- `scripts/compare_n256_n512_d2.py`: per-capture acceptance gate (field and
  dissipation frequency, realised energy, periodicity, drift, budget closure) and
  the `256 -> 512` variation table; `scripts/export_resolution_sensitivity_table.py`
  writes the appendix table from its JSON.
- Protocol verifications: `scripts/smoke_d2_period_lattice.py` (`omega_1 = pi`
  measured on the field), `scripts/validate_stokes_analytic.py` (oscillatory
  Stokes layer),
  `scripts/compare_forcing_staircase.py` (zero-order-hold control, `+0.114 %` on the
  cycle mean), `scripts/justify_capture_window.py` (32-period window).
- Grid-refinement sensitivity of the temporal campaign (`N = 256 -> 512`), reported
  as a variation and not as an extrapolated convergence order.
- `scripts/check_build_logs.py`: parses the four LaTeX build logs for fatal errors,
  unresolved references, missing graphics and overfull boxes.
- `figures/highlight_image.png`: table-of-contents highlight, assembled from the
  archived D2 field captures (2220 x 900 px at 300 dpi).

### Changed
- All temporal numbers, tables and figures regenerated from the new captures
  (`results/09_d2_capture/`, `results/d2_derived/`).
- Data availability split between what the git tree carries (waveforms, manifest,
  logs, derived records, appendix tables) and the raw phase-resolved field archives
  (~0.4 GB, above the per-file limit), supplied separately.
- Response letter: two points (15 and 16) now state the temporal mapping and the
  grid-refinement sensitivity in full, and every page count, object count, residual
  and ratio quoted there was re-extracted from the compiled documents.

### Removed
- Pre-mapping scripts and their outputs (the superseded capture drivers, the
  pre-mapping energy figure, the pre-mapping Stokes-layer and steady-streaming
  estimates, and the wall-power closure script and record): the distributed pipeline
  is only the one that reproduces this paper.
- Working notes on the correction workflow (`CORRECTIONS_STATUS.md`,
  `PLAN_CORRECTIONS.md`, `FIGURE_ISSUES.md`) and the appendix tables that are no
  longer included in either document.

## [1.0.0] - 2026-11-03

### Added
- Initial release of the complete study
- Main manuscript (clean and marked-up versions)
- Supplementary material (clean and marked-up versions)
- Response to editor letter
- All figures (PDF and PNG formats):
  - Figure 1: Controlled-cavity geometry and stationary modes
  - Figure 2: Spatio-temporal signatures of three branches
  - Additional supplementary figures
- Complete computational results data:
  - Branch audit and landmark separability
  - Reynolds-Energy parameter map
  - Variance regularization sweep
  - Branch classification results
  - Independent MRT-LBM validation
  - Cycle-average dissipation analysis
  - Cross-check case study
  - Branch figure captures
  - Conditional accessibility analysis
  - Grid convergence index (GCI) data
  - Symbolic regression (LOCO) results
- Analysis and visualization scripts:
  - `make_fig_modes.py`: Generate Figures 1 and 2
- Tables data for all manuscript and supplementary tables
- Comprehensive README with:
  - Project overview and abstract
  - Installation and requirements
  - Usage instructions
  - Results and data documentation
  - Reproducibility guidelines
  - Citation information
- MIT License
- CITATION.cff for easy citation
- CONTRIBUTING.md guidelines
- SECURITY.md for vulnerability reporting
- .gitignore for clean repository

### Changed
- N/A (initial release)

### Fixed
- N/A (initial release)

### Removed
- N/A (initial release)

---

## Previous Versions

This is the first public release of the repository. All development history
prior to this release is maintained in the authors' local repositories.
