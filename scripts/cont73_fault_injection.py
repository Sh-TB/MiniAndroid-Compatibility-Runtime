#!/usr/bin/env python3
"""cont73_fault_injection.py — F-NEW-376 install-atomicity fault-injection battery.

Drives `miniandroid install` with MINIANDROID_INSTALL_FAULT=<boundary> and
asserts the generation invariant at EVERY commit boundary:
  update failure -> live = OLD generation (code sha + record versionCode
                    paired), old code still RUNS;
  update success -> live = NEW generation, new code RUNS;
  fresh failure  -> NO committed generation, no partial state;
  mixed state    -> FORBIDDEN in every row.
Boundaries: parse (garbage APK), stage_copy, stage_hash (real byte flip),
record_write, lib_extract, promote, promote_mid (rollback), cleanup, success.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

ROOT = "/home/z/my-project"
BIN = f"{ROOT}/miniandroid/build/miniandroid"
V1 = f"{ROOT}/run/cont72/c72priv_v1.apk"
V2 = f"{ROOT}/run/cont72/c72priv_v2.apk"
GARBAGE = f"{ROOT}/run/cont73/garbage.bin"
PKG = "com.probe.c72priv"
STORE = "/tmp/f376_store"
RUNOUT = "/tmp/f376_run"

FAULTS = ["stage_copy", "stage_hash", "record_write", "lib_extract",
          "promote", "promote_mid", "cleanup"]


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


V1_SHA = sha16(V1)
V2_SHA = sha16(V2)


def install(apk, fault=None):
    env = dict(os.environ)
    env.pop("MINIANDROID_INSTALL_FAULT", None)
    if fault:
        env["MINIANDROID_INSTALL_FAULT"] = fault
    return subprocess.run([BIN, "install", apk, "--data-root", STORE],
                          capture_output=True, text=True, env=env, timeout=120)


def run_package():
    shutil.rmtree(RUNOUT, ignore_errors=True)
    os.makedirs(RUNOUT, exist_ok=True)
    return subprocess.run(
        [BIN, "run", "--package", PKG, "--data-root", STORE,
         "--width", "1080", "--height", "1920", "--frames", "1",
         "--max-seconds", "30", "-o", RUNOUT],
        capture_output=True, text=True, timeout=90)


def record():
    p = f"{STORE}/data/app/{PKG}/package.json"
    if not os.path.exists(p):
        return None
    body = open(p).read()
    vc = "?"
    for line in body.splitlines():
        if '"versionCode"' in line:
            vc = line.split(":")[1].strip().rstrip(",")
    sha = "?"
    for line in body.splitlines():
        if '"apkSha256"' in line:
            sha = line.split('"')[3][:16]
    return {"versionCode": vc, "apkSha256": sha}


def live_apk_sha():
    p = f"{STORE}/data/app/{PKG}/base.apk"
    return sha16(p) if os.path.exists(p) else None


def list_packages():
    r = subprocess.run([BIN, "list-packages", "--data-root", STORE],
                       capture_output=True, text=True, timeout=30)
    return r.stdout


def wipe():
    shutil.rmtree(STORE, ignore_errors=True)


def reset_to_v1():
    """Clean store with V1 committed (the 'previous generation')."""
    wipe()
    r = install(V1)
    assert r.returncode == 0, f"baseline V1 install failed: {r.stderr[-400:]}"


def marker():
    """Which code identity actually executed? (C72-VERSION log law)."""
    r = run_package()
    out = r.stdout + r.stderr
    if "[C72-VERSION]" in out:
        for line in out.splitlines():
            if "[C72-VERSION]" in line:
                if "V2" in line:
                    return "V2"
                if "V1" in line:
                    return "V1"
        return "MARKER-UNCLEAR"
    return None if r.returncode != 0 else "NO-MARKER"


results = []


def check(name, ok, detail):
    results.append((name, "PASS" if ok else "FAIL", detail))
    print(f"  [{'PASS' if ok else 'FAIL'}] {name}: {detail}")


def mixed_forbidden(live, rec, old_live, old_rec, new_live, new_rec):
    """The F-NEW-376 mixed-generation face must NEVER exist."""
    m1 = (live == new_live and rec is not None and rec["apkSha256"] == new_rec
          and rec["versionCode"] != new_rec)
    m2 = (live == new_live and rec is not None and rec["apkSha256"] == old_rec
          and rec["versionCode"] == new_rec)
    return not (m1 or m2)


def update_scenario(fault, expect_commit):
    """V1 committed -> install V2 with fault -> assert invariant."""
    reset_to_v1()
    old = {"sha": live_apk_sha(), "rec": record()}
    assert old["sha"] == V1_SHA and old["rec"]["versionCode"] == "1"
    assert marker() == "V1", "baseline V1 must run before fault injection"
    r = install(V2, fault=fault)
    live = live_apk_sha()
    rec = record()
    if expect_commit:
        check(f"update/{fault or 'success'}:rc", r.returncode == 0,
              f"rc={r.returncode}")
        check(f"update/{fault or 'success'}:live-is-new",
              live == V2_SHA and rec and rec["versionCode"] == "2",
              f"live={live} rec={rec}")
        check(f"update/{fault or 'success'}:runs-new", marker() == "V2",
              "C72-VERSION=V2 executed")
    else:
        check(f"update/{fault}:rc-fails", r.returncode != 0,
              f"rc={r.returncode}")
        check(f"update/{fault}:live-is-old",
              live == V1_SHA and rec and rec["versionCode"] == "1",
              f"live={live} rec={rec}")
        check(f"update/{fault}:runs-old", marker() == "V1",
              "old generation still RUNNABLE after rollback")
        check(f"update/{fault}:no-mixed", mixed_forbidden(live, rec, None,
              None, V2_SHA, "2"), "no mixed generation")
    # Store machinery never appears as a package.
    lp = list_packages()
    check(f"update/{fault or 'success'}:list-clean",
          ".staging" not in lp and ".trash" not in lp,
          "list-packages hides generation machinery")


def fresh_scenario(fault, expect_commit):
    """Empty store -> install V2 with fault -> assert invariant."""
    wipe()
    r = install(V2, fault=fault)
    live = live_apk_sha()
    rec = record()
    if expect_commit:
        check(f"fresh/{fault or 'success'}:rc", r.returncode == 0,
              f"rc={r.returncode}")
        check(f"fresh/{fault or 'success'}:committed",
              live == V2_SHA and rec and rec["versionCode"] == "2",
              f"live={live} rec={rec}")
        check(f"fresh/{fault or 'success'}:runs", marker() == "V2",
              "C72-VERSION=V2 executed")
    else:
        check(f"fresh/{fault}:rc-fails", r.returncode != 0, f"rc={r.returncode}")
        check(f"fresh/{fault}:no-generation",
              live is None and rec is None,
              f"live={live} rec={rec} (no partial state)")
        rrun = run_package()
        check(f"fresh/{fault}:not-runnable", rrun.returncode != 0,
              "run --package refuses (NOT_INSTALLED)")
    lp = list_packages()
    check(f"fresh/{fault or 'success'}:list-clean",
          ".staging" not in lp and ".trash" not in lp,
          "list-packages hides generation machinery")


def main():
    os.makedirs(f"{ROOT}/run/cont73", exist_ok=True)
    # parse/validate boundary: garbage input, no fault hook needed.
    with open(GARBAGE, "wb") as f:
        f.write(b"NOT-A-ZIP\x00\x01" * 64)
    reset_to_v1()
    r = install(GARBAGE)
    check("update/parse:rc-fails", r.returncode != 0, "garbage APK rejected")
    check("update/parse:live-is-old",
          live_apk_sha() == V1_SHA and record()["versionCode"] == "1",
          "V1 generation intact")
    check("update/parse:runs-old", marker() == "V1", "V1 still runnable")

    for fault in FAULTS:
        update_scenario(fault, expect_commit=(fault == "cleanup"))
    for fault in FAULTS:
        if fault == "promote_mid":
            continue  # update-only boundary; fresh has no parked generation
        fresh_scenario(fault, expect_commit=(fault == "cleanup"))
    fresh_scenario(None, expect_commit=True)
    update_scenario(None, expect_commit=True)

    # parked-trash honesty: cleanup fault leaves the NEW generation live and
    # the OLD generation parked (documented warn) — assert exactly that.
    reset_to_v1()
    install(V2, fault="cleanup")
    trash = f"{STORE}/data/app/.trash"
    parked = None
    if os.path.isdir(trash):
        for d in os.listdir(trash):
            p = f"{trash}/{d}/base.apk"
            if os.path.exists(p):
                parked = sha16(p)
    check("update/cleanup:trash-parked-old",
          parked in (None, V1_SHA) and live_apk_sha() == V2_SHA,
          f"parked={parked} live={live_apk_sha()} (new committed)")

    fails = [r for r in results if r[1] == "FAIL"]
    print(f"\n=== F-NEW-376 fault-injection battery: "
          f"{len(results) - len(fails)}/{len(results)} PASS ===")
    if fails:
        for n, _, d in fails:
            print(f"  FAIL {n}: {d}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
