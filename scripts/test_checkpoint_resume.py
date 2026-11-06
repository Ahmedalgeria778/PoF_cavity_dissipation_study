# -*- coding: utf-8 -*-
"""Test de la reprise sur checkpoint du runner D2.

Question centrale : le solveur est deterministe (aucun alea, la commande n'est
pilotee que par le compteur d'iterations), donc reprendre depuis l'etat `f`
sauvegarde en debut de periode doit redonner EXACTEMENT les memes series qu'un
run continu. Si ce test echoue, les checkpoints ne sont pas exploitables et
chaque incident oblige a relancer la branche entiere.

Trois phases, sur une resolution de test N=128 (PROTOCOLE IDENTIQUE :
steps = 40N = 5120 pas/periode, slowdown = steps/256 = 20, memes sondes et
memes fenetres de derive) pour rester sous les 5 minutes :
  A  run continu de reference, 3 periodes de capture
  B  run interromptu par TerminateProcess des que le checkpoint de la premiere
     periode de capture est ecrit (simule le blocage observe le 2026-11-05 a
     17:41 : le processus ne progresse plus et le .npz n'est jamais ecrit)
  C  relance : elle doit charger le checkpoint et finir les 2 periodes restantes
puis comparaison bit a bit (np.array_equal) de TOUTES les grilles et series de
l'archive. Seules differences admises : le drapeau resumed_from_checkpoint, et
seconds qui doit etre le CUMUL des segments, pas celui du dernier segment.

Usage : py scripts/test_checkpoint_resume.py
"""
import json
import os
import shutil
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
TESTDIR = os.path.join(ROOT, "results", "_ckpt_test")
N_TEST = 128
STEPS_TEST = 40 * N_TEST
CAPTURE_PERIODS = 12
CASE = "B1"
CK = os.path.join(TESTDIR, "checkpoints", f"ckpt_{CASE}_D2_N{N_TEST}_hold.npz")
ARCH = os.path.join(TESTDIR, f"capture_{CASE}_D2_N{N_TEST}.npz")

CHILD = """
import os, sys
sys.path.insert(0, os.path.abspath({here!r}))
import run_branch_capture_d2 as R
R.set_outdir(os.path.abspath({outdir!r}))
meta = R.capture({case!r}, {n}, "hold", {cap})
print("CHILD_DONE", meta["eps_cycle_mean"], flush=True)
"""


def run_child():
    src = CHILD.format(here=HERE, outdir=TESTDIR, case=CASE, n=N_TEST,
                       cap=CAPTURE_PERIODS)
    return subprocess.Popen([sys.executable, "-c", src], cwd=ROOT,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding="utf-8", errors="replace")


def ckpt_capture_periods():
    """Nombre de periodes de capture deja garanties par le checkpoint, ou None."""
    if not os.path.exists(CK):
        return None
    try:
        with np.load(CK) as z:
            if str(z["phase"]) != "capture":
                return None
            return int(np.asarray(z["cyc_eps"]).size)
    except Exception:                 # lecture pendant une ecriture : trop tot
        return None


def pump(p, sink, kill_when=None, timeout=2400):
    """Conduit l'enfant jusqu'a la fin, ou le tue des que kill_when() est vrai."""
    t0 = time.time()
    killed = False
    while True:
        line = p.stdout.readline()
        if line:
            sink.append(line.rstrip())
        elif p.poll() is not None:
            break
        if kill_when is not None and not killed and kill_when():
            p.kill()
            killed = True
            break
        if time.time() - t0 > timeout:
            p.kill()
            raise SystemExit("enfant trop long : test inadequat ou gel")
    p.wait(timeout=60)
    if killed:
        return "KILLED"
    return f"rc={p.returncode}"


def load_archive():
    if not os.path.exists(ARCH):
        raise SystemExit(f"archive absente: {ARCH}")
    with np.load(ARCH) as z:
        arrays = {k: np.asarray(z[k]) for k in z.files if k != "meta"}
        meta = json.loads(str(z["meta"]))
    return arrays, meta


def main():
    if os.path.exists(TESTDIR):
        shutil.rmtree(TESTDIR)
    os.makedirs(TESTDIR)

    print(f"phase A : run continu N={N_TEST}, {CAPTURE_PERIODS} periodes, "
          f"{STEPS_TEST} pas/periode")
    t0 = time.time()
    out = []
    st = pump(run_child(), out)
    print(f"   -> {st} en {time.time() - t0:.0f}s, {len(out)} lignes de journal")
    if not st.startswith("rc=0"):
        print("\n".join(out[-30:]))
        raise SystemExit("phase A echouee")
    ref, meta_ref = load_archive()
    shutil.move(ARCH, os.path.join(TESTDIR, "reference.npz"))
    if os.path.exists(CK):
        raise SystemExit("le checkpoint survit a un run fini (bug de nettoyage)")
    print(f"   reference : Dbar={meta_ref['eps_cycle_mean']:.6e} "
          f"warm={meta_ref['warm_periods']:.1f} P, "
          f"seconds={meta_ref['seconds']:.0f}s, checkpoint supprime OK")
    if meta_ref["resumed_from_checkpoint"]:
        raise SystemExit("phase A ne doit pas partir d'un checkpoint")

    print("phase B : run tue des que la periode 1 de capture est checkpointee")
    out = []
    seen = {"n": 0}

    def kill_when():
        n = ckpt_capture_periods()
        if n is not None and n >= 1:
            seen["n"] = n
            return True
        return False

    st = pump(run_child(), out, kill_when=kill_when)
    print(f"   -> {st} (checkpoint avec {seen['n']} periode(s) de capture)")
    if st != "KILLED":
        print("\n".join(out[-30:]))
        raise SystemExit("interruption non declenchee")
    if not os.path.exists(CK):
        raise SystemExit("checkpoint absent apres l'interruption")
    with np.load(CK) as z:
        phase, it = str(z["phase"]), int(z["it"])
    print(f"   checkpoint : phase={phase} it={it} ({it / STEPS_TEST:.2f} P) "
          f"tmp={os.path.exists(CK + '.tmp.npz')}")

    print("phase C : relance depuis le checkpoint")
    t0 = time.time()
    out = []
    st = pump(run_child(), out)
    print(f"   -> {st} en {time.time() - t0:.0f}s")
    if not st.startswith("rc=0"):
        print("\n".join(out[-40:]))
        raise SystemExit("phase C echouee")
    rl = [l for l in out if "RESUME" in l]
    if not rl:
        raise SystemExit("la relance n'a PAS utilise le checkpoint")
    print(f"   {rl[0].split('] ', 1)[-1]}")

    got, meta_got = load_archive()
    diffs = []
    for k in sorted(ref):
        b = got.get(k)
        if b is None:
            diffs.append(f"{k}: absent apres reprise")
        elif ref[k].shape != b.shape:
            diffs.append(f"{k}: formes {ref[k].shape} vs {b.shape}")
        elif not np.array_equal(ref[k], b):
            d = np.max(np.abs(ref[k] - b)) if ref[k].dtype.kind == "f" else None
            diffs.append(f"{k}: DIFFERENT (max|d|={d})")
    if meta_got["eps_cycle_mean"] != meta_ref["eps_cycle_mean"]:
        diffs.append(f"eps_cycle_mean {meta_got['eps_cycle_mean']:.12e} != "
                     f"{meta_ref['eps_cycle_mean']:.12e}")
    if meta_got["warm_periods"] != meta_ref["warm_periods"]:
        diffs.append(f"warm_periods {meta_got['warm_periods']} != "
                     f"{meta_ref['warm_periods']}")
    if meta_got["drift"] != meta_ref["drift"]:
        diffs.append(f"drift {meta_got['drift']:.3e} != {meta_ref['drift']:.3e}")
    if not meta_got["resumed_from_checkpoint"]:
        diffs.append("resumed_from_checkpoint faux")
    if meta_got["seconds"] < meta_ref["seconds"] - 1.0:
        diffs.append(f"seconds={meta_got['seconds']} < reference "
                     f"{meta_ref['seconds']} : cumul de reprise errone")
    print(f"   {len(ref)} champs compares bit a bit, "
          f"meta: warm/drift/identiques exigees")
    if diffs:
        print("ECHEC :")
        for d in diffs:
            print("   -", d)
        raise SystemExit(1)
    print("OK : reprise bit a bit identique au run continu, "
          f"seconds cumule ({meta_got['seconds']:.0f}s >= "
          f"{meta_ref['seconds']:.0f}s)")


if __name__ == "__main__":
    main()
