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
├── manuscript/                  # Main manuscript
│   ├── manuscript_final.tex     # LaTeX source
│   └── manuscript_final.pdf     # Compiled PDF
├── supplementary/               # Supplementary material
│   ├── supplementary_final.tex  # LaTeX source
│   └── supplementary_final.pdf  # Compiled PDF
├── figures/                     # All figures (PDF + PNG)
│   ├── fig01_modes.*            # Figure 1: Geometry and modes
│   ├── fig02_signatures.*       # Figure 2: Spatio-temporal signatures
│   └── ...                      # Additional figures
├── scripts/                     # Analysis scripts
│   ├── make_fig_modes.py        # Generate Figures 1 and 2
│   ├── make_fig_gci.py          # Generate Figure 12 (grid convergence)
│   └── make_fig_branch_topology.py  # Generate Figure 20 (branch topology)
├── tables/                      # Table data
└── docs/                        # Documentation
    └── RESPONSE_TO_EDITOR.*     # Response to editor letter
```

## Installation

### Requirements

- **Python 3.8+** with: `numpy`, `matplotlib`, `scipy`
- **LaTeX:** MiKTeX or TeX Live with standard packages

### Setup

```bash
git clone https://github.com/Ahmedalgeria778/PoF_cavity_dissipation_study.git
cd PoF_cavity_dissipation_study
pip install numpy matplotlib scipy
```

## Usage

### Generate Figures

All figure scripts read from `results/` and write to `figures/`.

```bash
# Figures 1 & 2: geometry, stationary modes, and branch signatures
python scripts/make_fig_modes.py

# Figure 12: grid convergence index (GCI)
python scripts/make_fig_gci.py

# Figure 20: branch flow topology (streamfunction + streamlines)
python scripts/make_fig_branch_topology.py
python scripts/make_fig_branch_topology.py --variant phases8     # supplementary Fig. S5
python scripts/make_fig_branch_topology.py --variant panelscale # supplementary Fig. S6
```

### Raw Data

The `results/` directory contains the simulation data used to generate all figures:

- `results/06_branch_figures/capture_B{1,2,3}.npz` — phase-resolved velocity fields, lid series, and energy budgets for the three branch classes at Re=500, E*=0.25
- `results/06_branch_figures/summary.json` — cycle-averaged diagnostics (dissipation, kinetic energy, lid power, closure residuals)
- `results/p1_gci_iso/p1_gci_raw.csv` — grid convergence data at N=128, 256, 512

### Compile Manuscript

```bash
cd manuscript
pdflatex manuscript_final.tex
pdflatex manuscript_final.tex
```

### Compile Supplementary

```bash
cd supplementary
pdflatex supplementary_final.tex
pdflatex supplementary_final.tex
```

## Key Results

- **First harmonic** reduces dissipation by **17.7%** at Re=500
- **Second harmonic** increases dissipation by **36.8%**
- **Temporally dominated branch** has **3.1×** the dissipation of stationary branch
- Cycle-mean dissipation ≠ dissipation of time-mean flow

## Data Availability

This repository contains the manuscript, figures, and scripts. The complete computational results (1.5 GB) are available from the corresponding author upon reasonable request.

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
