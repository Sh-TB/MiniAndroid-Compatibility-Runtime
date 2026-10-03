#!/usr/bin/env python3
"""GATE A (issue #370) — §20 RESTART / UNINSTALL / REINSTALL MATRIX.

INSTALL → INSPECT → WRITE → RESTART → INSPECT → UNINSTALL → VERIFY ABSENCE
→ REINSTALL → VERIFY CLEAN STATE. Machine-readable matrix rows.
"""
import json, os, shutil, subprocess, sys

B = "/home/z/my-project/miniandroid/build/miniandroid"
BASE = "/home/z/my-project/run/gatea"
MAT = f"{BASE}/reinstall_matrix"
PROBE_APK = f"{BASE}/gate_a_probe.apk"
PKG = "com.probe.gatea"

def run(cmd, env_extra=None):
    env = None
    if env_extra:
        env = {**os.environ, **env_extra}
    return subprocess.run(cmd, cwd="/home/z/my-project", capture_output=True,
                          text=True, env=env)

def results_file(store):
    return f"{store}/data/data/{PKG}/files/gate_a_results.jsonl"

def counter(store):
    p = results_file(store)
    if not os.path.exists(p):
        return None
    for line in open(p):
        if line.startswith("GATEA|PREF-06|"):
            return int(line.strip().split("restart_counter=")[1].split(" ")[0])
    return None

def main():
    shutil.rmtree(MAT, ignore_errors=True)
    os.makedirs(MAT, exist_ok=True)
    store = f"{MAT}/store"
    os.makedirs(store)
    rows = []

    def rec(step, expected, observed, verdict, evidence):
        rows.append({"step": step, "expected": expected, "observed": observed,
                     "verdict": verdict, "evidence": evidence})
        print(("PASS " if verdict == "PASS" else "FAIL ") + step)

    # 1. INSTALL
    r = run([B, "install", PROBE_APK, "--data-root", store])
    rec("INSTALL", "rc=0, record + base.apk committed",
        f"rc={r.returncode}",
        "PASS" if r.returncode == 0 else "FAIL", f"{MAT}/install.json")

    # 2. RUN 1 — writes state (restart_counter=1, db row 1)
    r = run([B, "run", "--package", PKG, "--data-root", store,
             "-o", f"{MAT}/run1"])
    c1 = counter(store)
    # rc carries the F-NEW-233 frame verdict (0/1), NOT persistence; the
    # persistence law here is the counter state the run physically wrote.
    rec("WRITE(run1)", "restart_counter=1 physically written",
        f"rc={r.returncode} counter={c1}",
        "PASS" if c1 == 1 else "FAIL", results_file(store))

    # 3. RESTART RUN 2 — state must persist
    r = run([B, "run", "--package", PKG, "--data-root", store,
             "-o", f"{MAT}/run2"])
    c2 = counter(store)
    rec("RESTART(run2)", "counter persists and grows to 2",
        f"counter={c2}",
        "PASS" if c2 == 2 else "FAIL", results_file(store))

    # 4. INSPECT state snapshot
    r = run([B, "pkginspect", "--package", PKG, "--data-root", store,
             "--what", "data,prefs,dbs", "--jsonl", f"{MAT}/before_uninstall.jsonl"])
    n_files = r.stdout.count('"logical"')
    rec("INSPECT", "data tree + prefs + db inventory (rc=0)",
        f"rc={r.returncode} data_rows={n_files}",
        "PASS" if r.returncode == 0 and n_files > 0 else "FAIL",
        f"{MAT}/before_uninstall.jsonl")

    # 5. UNINSTALL — everything gone
    r = run([B, "uninstall", "--package", PKG, "--data-root", store])
    gone = all(not os.path.exists(p) for p in (
        f"{store}/data/app/{PKG}",
        f"{store}/data/data/{PKG}",
        f"{store}/storage/emulated/0/Android/data/{PKG}",
        f"{store}/storage/emulated/0/Android/media/{PKG}",
        f"{store}/storage/emulated/0/Android/obb/{PKG}"))
    rec("UNINSTALL", "codePath + internalData + external trees REMOVED",
        f"rc={r.returncode} all_removed={gone} out={r.stdout.strip()[:60]}",
        "PASS" if r.returncode == 0 and gone else "FAIL", f"{MAT}/uninstall.json")

    # 6. UNINSTALL again — NOT_INSTALLED honesty
    r = run([B, "uninstall", "--package", PKG, "--data-root", store])
    rec("UNINSTALL(again)", "NOT_INSTALLED verdict (exit 2)",
        f"rc={r.returncode} NOT_INSTALLED={'NOT_INSTALLED' in r.stdout}",
        "PASS" if r.returncode == 2 else "FAIL", f"{MAT}/uninstall2.json")

    # 7. REINSTALL — clean namespace
    r = run([B, "install", PROBE_APK, "--data-root", store])
    def _empty(p):
        return not os.path.exists(p) or os.listdir(p) == []
    clean = all(_empty(p) for p in (
        f"{store}/data/data/{PKG}/files",
        f"{store}/data/data/{PKG}/shared_prefs",
        f"{store}/data/data/{PKG}/databases"))
    rec("REINSTALL", "codePath restored, data namespace clean (no leftover state; empty AOSP framework dirs are install-legal)",
        f"rc={r.returncode} clean_namespace={clean}",
        "PASS" if r.returncode == 0 and clean else "FAIL", f"{MAT}/reinstall.json")

    # 8. RUN 3 — fresh state per Android semantics (counter back to 1)
    r = run([B, "run", "--package", PKG, "--data-root", store,
             "-o", f"{MAT}/run3"])
    c3 = counter(store)
    rec("POST-REINSTALL STATE", "fresh app state: restart_counter=1",
        f"counter={c3}",
        "PASS" if c3 == 1 else "FAIL", results_file(store))

    with open(f"{MAT}/matrix.json", "w") as f:
        json.dump(rows, f, indent=1)
    fails = [r for r in rows if r["verdict"] != "PASS"]
    print(f"REINSTALL MATRIX: {len(rows) - len(fails)}/{len(rows)} PASS")
    return 0 if not fails else 1

if __name__ == "__main__":
    sys.exit(main())
