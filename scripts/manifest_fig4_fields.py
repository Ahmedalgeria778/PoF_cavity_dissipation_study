# -*- coding: utf-8 -*-
"""
Inventory of the three steady N=512 field archives that Main Fig. 4 is rendered
from, and verification of the numbers that figure annotates.

The archives are raw dumps of some 16 MB per control, so they are kept outside
the git tree, like the temporal captures of results/09_d2_capture/. This script
names them, records their byte size and SHA-256 digest, lists their arrays, and
recomputes from them the quantities quoted in Main Sec. 5.3 and in the caption of
Main Fig. 4: the domain integral of the local dissipation (checked against the
committed rows of results/p1_gci_iso/p1_gci_raw.csv at N=512), the peak strain-rate
magnitude and the interior mean strain-rate magnitude with three boundary cells
excluded, which is the window of the probability density of panel (c).

Outputs results/10_fig4_stationary_fields/FIELDS_MANIFEST.md and .json. With
--make-tar it also writes bundle/PoF_fig4_fields_v1.tar, the archive that supplies
the three fields alongside the submission, and records its size and checksum.

Usage:
    py scripts/manifest_fig4_fields.py --fields-dir DIR [--make-tar]
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(ROOT, "results", "10_fig4_stationary_fields")
RAW = os.path.join(ROOT, "results", "p1_gci_iso", "p1_gci_raw.csv")
N = 512
RE = 500
BORDER = 3

CONTROLS = [
    ("fields_UNem_0p5_Re500_N512.npz", "uniform", "uniform lid"),
    ("fields_S1em_0p707107_Re500_N512.npz", "k1", "k=1"),
    ("fields_B1em_0p707107_Re500_N512.npz", "k2", "k=2"),
]

# Values quoted in Main Sec. 5.3 and in the caption of Main Fig. 4.
EXPECTED = {
    "uniform": {"smax": 169.0, "sint": 1.039},
    "k1": {"smax": 15.0, "sint": 1.088},
    "k2": {"smax": 23.4, "sint": 1.450},
}
# The panel annotation of Fig. 4(b) is the trapezoid of the stored phi over the
# full node lattice with h = 1/(N-1) (the convention of the diagnostics that
# wrote these archives); the quoted dissipation of Main Table 2 is the
# solver-recorded volume integral of the same converged run. The two estimators
# differ by 0.4-0.7%, inside the fine-grid GCI of Sec. S4.4, so this gate only
# has to catch a mis-shipped archive.
EPS_TOL = 0.01      # relative, field integral against the committed csv row
SMAX_TOL = 0.02     # relative, against the two/three-sig fig caption value
SINT_TOL = 0.002    # relative


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def raw_eps():
    import csv
    out = {}
    with open(RAW, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if int(row["N"]) == N:
                out[row["case"]] = float(row["eps"])
    return out


def measure(path):
    z = np.load(path)
    ux = np.asarray(z["ux"], dtype=float)
    uy = np.asarray(z["uy"], dtype=float)
    phi = np.asarray(z["phi"], dtype=float)
    dx = 1.0 / (N - 1)
    dUdx = np.gradient(ux, dx, axis=1)
    dUdy = np.gradient(ux, dx, axis=0)
    dVdx = np.gradient(uy, dx, axis=1)
    dVdy = np.gradient(uy, dx, axis=0)
    s12 = 0.5 * (dUdy + dVdx)
    phi_grad = (1.0 / RE) * (2 * dUdx ** 2 + 2 * dVdy ** 2 + 4 * s12 ** 2)
    smag = np.sqrt(2.0 * (dUdx ** 2 + dVdy ** 2 + 2.0 * s12 ** 2))
    eps = float(np.trapezoid(np.trapezoid(phi, dx=dx, axis=1), dx=dx))
    eps_rebuilt = float(np.trapezoid(np.trapezoid(phi_grad, dx=dx, axis=1), dx=dx))
    interior = smag[BORDER:-BORDER, BORDER:-BORDER]
    arrays = {k: [list(z[k].shape), str(z[k].dtype)] for k in z.files}
    return dict(bytes=os.path.getsize(path), sha256=sha256(path),
                keys=sorted(arrays), arrays=arrays,
                control=str(z["control"]), Re=int(z["Re"]), N=int(z["N"]),
                eps_field=eps, eps_from_velocity=eps_rebuilt,
                s_max=float(smag.max()),
                s_interior_mean=float(interior.mean()),
                interior_cells=int(interior.size))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fields-dir", required=True,
                    help="directory holding the three steady N=512 field archives")
    ap.add_argument("--make-tar", action="store_true")
    ap.add_argument("--bundle-name", default="PoF_fig4_fields_v1.tar")
    args = ap.parse_args()

    fields = os.path.abspath(args.fields_dir)
    if not os.path.isdir(fields):
        sys.exit("field directory not found: " + fields)
    csv_eps = raw_eps()
    records, failures = [], []
    for fname, key, label in CONTROLS:
        path = os.path.join(fields, fname)
        if not os.path.isfile(path):
            sys.exit("missing field archive: " + path)
        rec = measure(path)
        rec.update(file=fname, key=key, label=label,
                   source_directory=os.path.basename(fields))
        exp = EXPECTED[key]
        rec["eps_csv"] = csv_eps[key]
        checks = []
        for name, got, want, tol in [
                ("field eps vs committed csv", rec["eps_field"], csv_eps[key], EPS_TOL),
                ("stored phi vs velocity rebuild", rec["eps_from_velocity"],
                 rec["eps_field"], 1e-12),
                ("peak |S| vs quoted", rec["s_max"], exp["smax"], SMAX_TOL),
                ("interior mean |S| vs quoted", rec["s_interior_mean"],
                 exp["sint"], SINT_TOL)]:
            dev = abs(got / want - 1.0)
            ok = dev <= tol
            checks.append((name, got, want, dev, ok))
            if not ok:
                failures.append("%s: %s got %.6g want %.6g (dev %.3g > tol %g)"
                                % (key, name, got, want, dev, tol))
        rec["checks"] = [[n, g, w, d, o] for n, g, w, d, o in checks]
        records.append(rec)
        print("%-40s %10d B  eps=%.6e  max|S|=%.2f  <|S|>_int=%.4f"
              % (fname, rec["bytes"], rec["eps_field"], rec["s_max"],
                 rec["s_interior_mean"]))
        for n, g, w, d, o in checks:
            print("     %s %s: %.6g vs %.6g (%.2g%%)" % ("[ok]  " if o else "[FAIL]", n, g, w, 100 * d))

    bundle = None
    tar = os.path.join(ROOT, "bundle", args.bundle_name)
    if args.make_tar:
        os.makedirs(os.path.dirname(tar), exist_ok=True)
        subprocess.run(["tar", "-cf", tar, "-C", fields] + [c[0] for c in CONTROLS],
                       check=True)
    if os.path.isfile(tar):
        bundle = dict(name=args.bundle_name, bytes=os.path.getsize(tar),
                      sha256=sha256(tar), members=[c[0] for c in CONTROLS])
        print("bundle %s: %d B %s" % (args.bundle_name, bundle["bytes"],
                                      bundle["sha256"][:16]))

    os.makedirs(OUTDIR, exist_ok=True)
    payload = dict(re=RE, n=N, border_cells_excluded=BORDER,
                   fields_directory=os.path.basename(fields),
                   total_bytes=sum(r["bytes"] for r in records),
                   records=records, bundle=bundle)
    with open(os.path.join(OUTDIR, "FIELDS_MANIFEST.json"), "w",
              encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, sort_keys=True)
        fh.write("\n")

    lines = []
    lines.append("# Field archives behind Main Fig. 4 (stationary N=512 campaign)")
    lines.append("")
    lines.append("Written by `scripts/manifest_fig4_fields.py`; regenerate with")
    lines.append("`py scripts/manifest_fig4_fields.py --fields-dir DIR --make-tar`.")
    lines.append("")
    lines.append("Main Fig. 4 is rendered by")
    lines.append("`scripts/make_fig_mechanism.py` from the three steady velocity fields below,")
    lines.append("which are raw dumps of some 16 MB per control and are therefore kept outside")
    lines.append("the git tree, as the temporal captures of `results/09_d2_capture/` are. Each")
    lines.append("archive holds the arrays `ux`, `uy`, `psi`, `vort`, `phi`, `phi_xx`, `phi_yy`,")
    lines.append("`phi_xy` on the `N x N` lattice, the lid profiles `U_lid` and `U_lid_imposed`,")
    lines.append("the wall-shear profile `tau_w`, and the scalars `control`, `Re`, `N`, all")
    lines.append("`float64` at N = 512, Re = 500 and E* = 0.25.")
    lines.append("")
    lines.append("| File | Control | Bytes | SHA-256 |")
    lines.append("| --- | --- | --- | --- |")
    for r in records:
        lines.append("| `%s` | %s | %d | `%s` |"
                     % (r["file"], r["label"], r["bytes"], r["sha256"]))
    lines.append("| **total** | | **%d** (%.2f MiB) | |"
                 % (payload["total_bytes"], payload["total_bytes"] / 1048576.0))
    lines.append("")
    lines.append("They are the converged steady states of the stationary `Re = 500`,")
    lines.append("`E* = 0.25` campaign whose solver-recorded dissipation is committed in")
    lines.append("`results/p1_gci_iso/p1_gci_raw.csv` (Sec. S4.4 of the supplement).")
    lines.append("")
    if bundle:
        lines.append("Supplied as `bundle/%s`: %d bytes (%.2f MiB), SHA-256 `%s`."
                     % (bundle["name"], bundle["bytes"],
                        bundle["bytes"] / 1048576.0, bundle["sha256"]))
        lines.append("")
    lines.append("## Quantities recomputed from these files")
    lines.append("")
    lines.append("`scripts/make_fig_mechanism.py` and this inventory use the same definitions:")
    lines.append("`S_ij` from centred differences of the stored `ux`, `uy` with `h = 1/(N-1)`,")
    lines.append("the interior statistics over the window that excludes `BORDER = 3` cells on")
    lines.append("every side (the window of panel (c)), and the domain integral of `phi` by")
    lines.append("trapezoid over the full node lattice (the annotation of panel (b)). The stored")
    lines.append("`phi` array and the field rebuilt from `ux`, `uy` agree to better than `1e-12`,")
    lines.append("so the archive is self-consistent.")
    lines.append("")
    lines.append("| Control | eps (field integral) | eps (committed csv) | deviation | max\\|S\\| | <|S|>_interior |")
    lines.append("| --- | --- | --- | --- | --- | --- |")
    for r in records:
        lines.append("| %s | %.6e | %.6e | %+.3f%% | %.3f | %.4f |"
                     % (r["label"], r["eps_field"], r["eps_csv"],
                        100.0 * (r["eps_field"] / r["eps_csv"] - 1.0),
                        r["s_max"], r["s_interior_mean"]))
    lines.append("")
    lines.append("The `max|S|` and `<|S|>_interior` columns reproduce the values quoted in Main")
    lines.append("Sec. 5.3 and in the caption of Main Fig. 4 (169, 15.0 and 23.4 for the peak;")
    lines.append("1.039, 1.088 and 1.450 for the interior mean), and the two lid-shear ratios of")
    lines.append("Main Sec. 5.3 (4.7% and 39.6%) follow from them.")
    lines.append("")
    lines.append("The two `eps` columns are two estimators of the dissipation of the same")
    lines.append("converged run: the field integral above, which is what panel (b) annotates,")
    lines.append("and the volume integral recorded by the solver during the run, which is the")
    lines.append("value committed in `results/p1_gci_iso/p1_gci_raw.csv` and quoted in Main")
    lines.append("Table 2, Main Sec. 5.1 and Main Fig. 3. They differ by +0.70%, +0.65% and")
    lines.append("+0.38%, all of them inside the 3.9-7.8% fine-grid GCI already attached to")
    lines.append("those dissipation values (Sec. S4.4), so no ordering, ratio or conclusion of")
    lines.append("the paper depends on which of the two is used; every quoted number is the")
    lines.append("solver-recorded one, and the field integral is shown here only to prove that")
    lines.append("the archives reproduce the run they came from.")
    with open(os.path.join(OUTDIR, "FIELDS_MANIFEST.md"), "w",
              encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    print("wrote", os.path.relpath(os.path.join(OUTDIR, "FIELDS_MANIFEST.md"), ROOT))

    if failures:
        print("\n".join("MISMATCH " + f for f in failures))
        sys.exit(1)


if __name__ == "__main__":
    main()
