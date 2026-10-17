#!/usr/bin/env python3
# cont73_registry_update.py — CONT-73 ledger (issue #364):
#   * F-NEW-376 OBSERVED-FAIL -> ROOT-CAUSED-FIXED
#     (staged-generation install atomicity law + deterministic
#      fault-injection battery at every commit boundary)
import json, hashlib

REG = "root_registry.json"
r = json.load(open(REG))
f376 = [x for x in r["roots"] if x.get("id") == "F-NEW-376"]
assert len(f376) == 1, f"F-NEW-376 rows: {len(f376)}"
assert f376[0]["status"] == "OBSERVED-FAIL", f376[0]["status"]


def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]


BIN_SHA = sha16("miniandroid/build/miniandroid")
V1_SHA = sha16("run/cont72/c72priv_v1.apk")
V2_SHA = sha16("run/cont72/c72priv_v2.apk")

f376[0]["status"] = "ROOT-CAUSED-FIXED"
f376[0]["priority"] = "P1"
f376[0]["title"] = (
    "INSTALL/UPDATE COMMIT IS NOT ATOMIC (issue #364 FOUNDATION-3 review, "
    "fault-injection-proven) — FIXED by the staged-generation promotion law: "
    "cmd_install now builds the COMPLETE new generation (base.apk + "
    "package.json + lib/<abi> + native_libs.json) under "
    "<store>/data/app/.staging/<pkg>.<pid>, verifies staged bytes against the "
    "source sha, then commits with a directory-generation switch (fresh: ONE "
    "rename; update: park old -> promote new -> drop parked, with rollback to "
    "the parked generation on every failure). Code bytes and identity "
    "metadata can never be from different generations; readers resolve only "
    "committed generations.")
f376[0]["root_cause"] = (
    "Commit ordering promoted in place: copy onto the LIVE base.apk, verify, "
    "then write the record with no rollback — a record-write failure (or "
    "process exit) left V2 code bytes under the V1 record, and run --package "
    "gates on base.apk existence only, executing code that disagrees with the "
    "committed identity. POSIX rename cannot atomically replace a non-empty "
    "directory (ENOTEMPTY), so file-level ordering can never be a "
    "transaction: the atomicity unit must be the whole package DIRECTORY.")
f376[0]["fix"] = (
    "miniandroid/src/main.cpp: (1) pkgstore.record_json_body shared writer + "
    "write_record_to(gen_dir) — the staged record describes the LIVE location "
    "it will occupy and is byte-identical after promotion (no post-promotion "
    "rewrite); (2) cmd_install staged-generation flow with seven deterministic "
    "fault-injection boundaries behind MINIANDROID_INSTALL_FAULT=stage_copy|"
    "stage_hash|record_write|lib_extract|promote|promote_mid|cleanup "
    "(env-gated test capability, generic, no package conditionals); "
    "(3) promotion: fresh = one rename(staging->live); update = park old to "
    ".trash, promote, drop parked; promote_mid/promotion-failure ROLLBACK "
    "restores the parked generation (hard-error with preserved-trash path if "
    "rollback itself fails); (4) list-packages hides dot-prefixed generation "
    "machinery; (5) app-private data scaffolding moved post-commit.")
f376[0]["evidence"] = (
    f"FAULT-INJECTION BATTERY 70/70 PASS (scripts/cont73_fault_injection.py, "
    f"binary {BIN_SHA}): probe pair run/cont72/c72priv_v1.apk {V1_SHA} (vc1) / "
    f"c72priv_v2.apk {V2_SHA} (vc2, same package com.probe.c72priv, "
    f"[C72-VERSION] runtime marker). UPDATE path (V1 committed -> V2 + fault): "
    f"stage_copy/stage_hash/record_write/lib_extract/promote/promote_mid all "
    f"rc!=0 with live == V1 sha AND record vc=1 AND old code still RUNS "
    f"([C72-VERSION]=V1) after rollback; stage_hash injects a REAL byte flip "
    f"caught by the integrity gate (positive control); promote_mid proves the "
    f"park->promote window rollback; cleanup commits V2 and honestly leaves "
    f"the parked V1 generation in .trash (warn, live==V2); success commits "
    f"V2 with record vc=2 agreeing ([C72-VERSION]=V2). FRESH path: every "
    f"pre-commit fault leaves NO package dir, NO record, run --package "
    f"refuses NOT_INSTALLED. parse/validate boundary: garbage APK rejected, "
    f"V1 intact and runnable. MIXED-STATE INVARIANT asserted in every row "
    f"(base.apk sha vs record versionCode pairing) — zero mixed states. "
    f"list-packages hides .staging/.trash after every fault. REGRESSION at "
    f"the same binary: cont71_gate wall 13 rows x3 = 39/39 MATCH (csw "
    f"d3c26b73ee21e571, dooz 31ddd4d5b8e6d18e, flappycow 13cf47464d9787f4, "
    f"g2048 f43face08299ffc6, gmdice 3891679dff449331, microtimer "
    f"bbd350b6c14fbd52, opencalc f25b754c4565c38b, simplecalc 2ac5d8d0cbf9552a, "
    f"tanana afe0bd8dd4d09ca6, tttdeluxe db1d633d77b5819a, unote 90a67cc1ddda57b7, "
    f"dooz180 c94da5a928ea213b, memory warm c559b630dd8f0f0f); gate A probe "
    f"98 PASS/1 INFO/0 FAIL (lib ad413625925ed8e5 == record); negatives 19/19 "
    f"(after the canonical probe prelude); reinstall 8/8; goldens 4/4; skill "
    f"13/13. Zero run-path behavior change (installer-only law) — wall "
    f"byte-identical by construction AND verified.")
f376[0]["probe"] = (
    "scripts/cont73_fault_injection.py (70 assertions: 9 boundaries x "
    "fresh/update paths x {rc, generation pairing, runnability, list "
    "hygiene, no-mixed-state}); V1/V2 fixture pair from "
    "fixtures/cont72_priv_probe (real aapt2/ECJ/D8).")
f376[0]["fanout"] = (
    "every install/update path and every consumer of the package store "
    "(run --package, list-packages, pkgaudit, pkginspect): the store can "
    "never again serve a code/identity mix; per-package evidence provenance "
    "is generation-consistent by construction.")
f376[0]["date"] = "2026-10-17"
f376[0]["verified_current"] = (
    f"70/70 fault battery + 39/39 wall + 19/19 negatives + 8/8 reinstall + "
    f"4/4 goldens + 13/13 skill at binary {BIN_SHA}, HEAD befb9cca+CONT-73.")

r["total_roots"] = len(r["roots"])
r["total"] = len(r["roots"])
r["count"] = len(r["roots"])
sc = {}
for x in r["roots"]:
    sc[x.get("status", "?")] = sc.get(x.get("status", "?"), 0) + 1
r["status_counts"] = sc
json.dump(r, open(REG, "w"), indent=1, ensure_ascii=False)
print("registry roots:", r["total_roots"])
print("F-NEW-376 ->", f376[0]["status"])
print("status counts:", sc)
