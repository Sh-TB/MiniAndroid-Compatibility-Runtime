#!/usr/bin/env python3
"""CONT-18 T-01: re-run the f084 loop probe (F-NEW-217 live evidence) at the
CONT-17 binary a8761a482a186eac. Reproduces run/cont17/f084_run procedure.

Probe: fixtures/f084_loop_probe APK (com.probe.f084, sha 21351bd0df1571cd).
Expected: [HALT-LOOP] deterministic at 50,001 visits in the 2-byte stall loop;
[SPIN-HISTO]/[SPIN-REGS] diagnostics; deferred VirtualMachineError delivered
(F084-HALT-RETURN); instruction budget NEVER raised.
Writes run/cont18/f084_run/ + evidence/cont18/t01_f084_probe.json
"""
import hashlib, json, os, re, shutil, subprocess, sys

BASE = "/home/z/my-project"
BIN = f"{BASE}/miniandroid/build/miniandroid"
APK = f"{BASE}/run/w7/f084.apk"
OUT = f"{BASE}/run/cont18/f084_run"
REPORT = f"{BASE}/evidence/cont18/t01_f084_probe.json"


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16] \
        if os.path.exists(p) else None


def main():
    shutil.rmtree(OUT, ignore_errors=True)
    os.makedirs(OUT)
    store = f"{OUT}/store"
    os.makedirs(store)
    inst = subprocess.run([BIN, "install", APK, "--data-root", store],
                          capture_output=True, text=True, timeout=300)
    pkg = None
    if "{" in inst.stdout:
        try:
            pkg = json.JSONDecoder().raw_decode(
                inst.stdout[inst.stdout.index('{'):])[0].get("package")
        except Exception:
            pass
    env = dict(os.environ)
    for k in list(env):
        if k.startswith("MINIANDROID_"):
            del env[k]
    run = subprocess.run(
        [BIN, "run", "--package", "com.probe.f084", "--data-root", store,
         "--max-seconds", "120", "--frames", "40", "-o", OUT],
        capture_output=True, text=True, timeout=300, env=env)
    log = run.stdout + run.stderr
    open(f"{OUT}/run.log", "w").write(log)

    rows = {
        "binary_sha16": sha16(BIN),
        "apk_sha16": sha16(APK),
        "package": pkg or "com.probe.f084",
        "run_rc": run.returncode,
    }
    halt = re.findall(r"\[HALT-LOOP\][^\n]*", log)
    spin_h = re.findall(r"\[SPIN-HISTO\][^\n]*", log)
    spin_r = re.findall(r"\[SPIN-REGS\][^\n]*", log)
    haltret = re.findall(r"F084-HALT-RETURN[^\n]*", log)
    vme = re.findall(r"VirtualMachineError[^\n]*", log)
    rows["halt_loop_lines"] = halt[:6]
    rows["spin_histo_lines"] = spin_h[:6]
    rows["spin_regs_lines"] = spin_r[:6]
    rows["halt_return_lines"] = haltret[:4]
    rows["vme_lines"] = vme[:4]
    rows["halt_loop_count"] = len(halt)
    visits = None
    for h in halt:
        m = re.search(r"visited\s+(\d[\d,]*)\s+times", h)
        if m:
            visits = int(m.group(1).replace(",", ""))
            break
    rows["halt_visits"] = visits
    # expectations from the recorded CONT-17 task-33 evidence
    rows["expect_halt_visits"] = 50001
    rows["halt_deterministic"] = visits == 50001
    rows["deferred_vme_delivered"] = bool(haltret) and bool(vme)
    rows["cap_never_raised"] = visits is not None and visits <= 50001
    rows["VERIFIED"] = (rows["halt_deterministic"]
                        and rows["deferred_vme_delivered"]
                        and rows["cap_never_raised"])
    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    json.dump(rows, open(REPORT, "w"), indent=2, ensure_ascii=False)
    print(json.dumps({k: rows[k] for k in
                      ["halt_visits", "halt_deterministic",
                       "deferred_vme_delivered", "cap_never_raised",
                       "VERIFIED"]}, indent=2))
    for h in halt[:2]:
        print("LOG:", h[:160])
    for h in haltret[:1]:
        print("LOG:", h[:200])


if __name__ == "__main__":
    main()
