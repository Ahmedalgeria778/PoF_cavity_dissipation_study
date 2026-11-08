# Field archives behind Main Fig. 4 (stationary N=512 campaign)

Written by `scripts/manifest_fig4_fields.py`; regenerate with
`py scripts/manifest_fig4_fields.py --fields-dir DIR --make-tar`.

Main Fig. 4 is rendered by
`scripts/make_fig_mechanism.py` from the three steady velocity fields below,
which are raw dumps of some 16 MB per control and are therefore kept outside
the git tree, as the temporal captures of `results/09_d2_capture/` are. Each
archive holds the arrays `ux`, `uy`, `psi`, `vort`, `phi`, `phi_xx`, `phi_yy`,
`phi_xy` on the `N x N` lattice, the lid profiles `U_lid` and `U_lid_imposed`,
the wall-shear profile `tau_w`, and the scalars `control`, `Re`, `N`, all
`float64` at N = 512, Re = 500 and E* = 0.25.

| File | Control | Bytes | SHA-256 |
| --- | --- | --- | --- |
| `fields_UNem_0p5_Re500_N512.npz` | uniform lid | 15946918 | `dadf9b12c8e33e4a5e7b7d2c8dd9a0a31b86963ee3e15da3a289c343d6c72c01` |
| `fields_S1em_0p707107_Re500_N512.npz` | k=1 | 15952846 | `819e14c24707da0ac8bcbb48594dc2a9ae95573508edc6dcbdb9e955702eed5b` |
| `fields_B1em_0p707107_Re500_N512.npz` | k=2 | 13040223 | `7c739104344b2f59f941f1b307c9d7fced36c84916ed6bbcf3eca3f85e843af0` |
| **total** | | **44939987** (42.86 MiB) | |

They are the converged steady states of the stationary `Re = 500`,
`E* = 0.25` campaign whose solver-recorded dissipation is committed in
`results/p1_gci_iso/p1_gci_raw.csv` (Sec. S4.4 of the supplement).

Supplied as `bundle/PoF_fig4_fields_v1.tar`: 44943360 bytes (42.86 MiB), SHA-256 `7f2fe53617d437f82d500746833c1bfd38dea600c73572df4244efb6a03c6144`.

## Quantities recomputed from these files

`scripts/make_fig_mechanism.py` and this inventory use the same definitions:
`S_ij` from centred differences of the stored `ux`, `uy` with `h = 1/(N-1)`,
the interior statistics over the window that excludes `BORDER = 3` cells on
every side (the window of panel (c)), and the domain integral of `phi` by
trapezoid over the full node lattice (the annotation of panel (b)). The stored
`phi` array and the field rebuilt from `ux`, `uy` agree to better than `1e-12`,
so the archive is self-consistent.

| Control | eps (field integral) | eps (committed csv) | deviation | max\|S\| | <|S|>_interior |
| --- | --- | --- | --- | --- | --- |
| uniform lid | 1.109808e-02 | 1.102085e-02 | +0.701% | 169.378 | 1.0388 |
| k=1 | 7.172501e-03 | 7.126369e-03 | +0.647% | 14.983 | 1.0880 |
| k=2 | 1.189867e-02 | 1.185313e-02 | +0.384% | 23.413 | 1.4497 |

The `max|S|` and `<|S|>_interior` columns reproduce the values quoted in Main
Sec. 5.3 and in the caption of Main Fig. 4 (169, 15.0 and 23.4 for the peak;
1.039, 1.088 and 1.450 for the interior mean), and the two lid-shear ratios of
Main Sec. 5.3 (4.7% and 39.6%) follow from them.

The two `eps` columns are two estimators of the dissipation of the same
converged run: the field integral above, which is what panel (b) annotates,
and the volume integral recorded by the solver during the run, which is the
value committed in `results/p1_gci_iso/p1_gci_raw.csv` and quoted in Main
Table 2, Main Sec. 5.1 and Main Fig. 3. They differ by +0.70%, +0.65% and
+0.38%, all of them inside the 3.9-7.8% fine-grid GCI already attached to
those dissipation values (Sec. S4.4), so no ordering, ratio or conclusion of
the paper depends on which of the two is used; every quoted number is the
solver-recorded one, and the field integral is shown here only to prove that
the archives reproduce the run they came from.
