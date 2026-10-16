#!/usr/bin/env python3
# cont72_registry_update.py — CONT-72 (issue #364 three-card review) ledger:
#   * F-NEW-375 ROOT-CAUSED-FIXED  — path-identity/containment law
#   * F-NEW-376 OBSERVED-FAIL      — non-atomic install commit (new frontier)
#   * MG-116 PARTIAL -> CLOSED     — dedicated law fence supplied, passes x3
import json, hashlib, sys

REG = "root_registry.json"
r = json.load(open(REG))
ids = {x.get("id") for x in r["roots"]}
assert "F-NEW-375" not in ids and "F-NEW-376" not in ids, "id collision"

def sha16(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]

r["roots"].append({
    "id": "F-NEW-375",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P1",
    "title": "PATH-IDENTITY / CONTAINMENT LAW (issue #364 FOUNDATION-3 review, "
             "runtime-proven before fix): resolve_android_path enforced namespace "
             "SHAPE but not CALLER IDENTITY — the /data/data/<pkg>, /data/user/<id>/<pkg> "
             "and /data/user_de/<id>/<pkg> branches allowed ANY dotted package "
             "(runtime leak: package com.probe.c72priv read victim "
             "com.dubrowgn.microtimer's TOPSECRET72 bytes through 4 spellings: "
             "absolute, user-0 alias, and two relative .. traversals); the relative "
             "branch concatenated package_data_dir()/logical with NO containment "
             "check (OS resolves the .. for the caller); the /storage/emulated/0 "
             "dispatch used a bare prefix test so sibling volume names (0evil, "
             "0123) mapped INTO the primary volume. AOSP fences these at the "
             "kernel UID boundary (ActivityManager per-package uid + sepolicy "
             "appdomain); the single-process runtime must fence at the resolver — "
             "the ONE canonical law every consumer shares (FileInputStream/"
             "FileOutputStream ctors, BitmapFactory.decodeFile, Context file APIs).",
    "layer": "storage/path-resolution (resolve_android_path)",
    "root_cause": "THREE missing laws in data_root.cpp resolve_android_path: "
                  "(1) caller-identity — sandbox branches never compared the "
                  "extracted package to g_context_package; (2) relative-branch "
                  "containment — no lexical normalization check before allow; "
                  "(3) volume component boundary — prefix test without the "
                  "end-or-slash check. FIX: identity check on all three sandbox "
                  "branches (bound identity => own CE/DE tree only; empty identity "
                  "= legacy tool paths keep the old behavior), lexical "
                  "path_contained() fence on the relative branch, and the "
                  "component-boundary check on the external-volume dispatch.",
    "evidence": "PROBE (real aapt2/ECJ/D8 toolchain): fixtures/cont72_priv_probe "
                "-> run/cont72/c72priv_v1.apk 80e8a3f69255da9e, installed as "
                "com.probe.c72priv beside victim com.dubrowgn.microtimer in a "
                "fresh --data-root with planted canaries. PRE-FIX run/cont72/priv_run1: "
                "C72-XPKG-ABS LEAK + C72-XPKG-U0 LEAK + C72-REL-ESC LEAK + "
                "C72-REL-ESC2 LEAK (all four read TOPSECRET72, 11 bytes); "
                "negative controls already honest (/etc/passwd, /proc/self/status, "
                "/data/local/tmp, sibling-volume opens answered FileNotFoundException); "
                "own-namespace CE alias + DE round-trip OK. POST-FIX "
                "run/cont72/priv_fix1..3: all four leak rows DENIED with the AOSP "
                "FileNotFoundException face; ALIAS-SELF/DE-WRITE/NEG rows unchanged; "
                "C72 row matrix byte-identical x3 (md5 a18419faa24e). Binary "
                "19d090e78c5d8e23 (delta = data_root.cpp only; prior binary "
                "86e4ebd4a2c30592 was the CONT-71 record identity, verified "
                "byte-identical rebuild). MOUNT-ALIAS note: the pre-fix "
                "file-OPEN layer already answered absent for /storage/emulated/0evil "
                "(defense at a second check), so that row was not a live leak — the "
                "resolver mapping is still wrong-shaped and is fixed for every "
                "consumer (honest classification: source-level fix, not a "
                "runtime-reproducible leak).",
    "probe": "fixtures/cont72_priv_probe (C72- row matrix, 13 rows); harness "
             "run/cont72/droot (victim + canaries planted); rows logged by the "
             "code whose contract is asserted.",
    "fanout": "every app-visible file consumer that resolves a logical path "
              "(streams, bitmap decode, prefs/db/DE families) — one fence at "
              "the shared primitive instead of per-consumer patches; also "
              "protects future multi-package test corpora.",
    "date": "2026-10-16",
    "verified_current": "wall 13 rows x3 MATCH at the fix binary (csw/dooz/"
                        "flappycow/g2048/gmdice/microtimer/opencalc/simplecalc/"
                        "tanana/tttdeluxe/unote + memory warm x3 == record "
                        "c559b630dd8f0f0f, memory r1 == recorded TRUE-COLD "
                        "3a3ba8734b662e55); dooz180 == record c94da5a928ea213b x2; "
                        "negatives 19/19 (after the canonical closeout_baseline "
                        "probe prelude), reinstall 8/8, goldens 4/4, skill 13/13, "
                        "s82 validator PASS.",
})

r["roots"].append({
    "id": "F-NEW-376",
    "status": "OBSERVED-FAIL",
    "priority": "P2",
    "title": "INSTALL/UPDATE COMMIT IS NOT ATOMIC (issue #364 FOUNDATION-3 "
             "review, fault-injection-proven): cmd_install copies the new APK "
             "DIRECTLY onto <store>/data/app/<pkg>/base.apk (copy_file "
             "overwrite_existing) BEFORE write_record; a record-write failure or "
             "process exit between the two leaves V2 code bytes under the V1 "
             "committed record, and run --package gates on base.apk existence "
             "only — it executes code that disagrees with the committed identity.",
    "layer": "package-store install commit (main.cpp cmd_install / pkgstore)",
    "root_cause": "Commit ordering: promote-in-place -> hash-verify -> write "
                  "record. The hash-verify failure path remove_all()s the code "
                  "dir (availability loss of the previous working install, but "
                  "the private data tree <root>/data/data/<pkg> is a SEPARATE "
                  "tree and survives — the card's 'private data tree removal' "
                  "wording is imprecise). The record-write failure path has NO "
                  "rollback of the promoted base.apk. AOSP PMS law: stage first, "
                  "verify, then atomic promote + record (recovery on restart).",
    "evidence": "FAULT INJECTION (no engine change; failure injected at the "
                "record-write boundary): installed c72priv V1 (80e8a3f69255da9e, "
                "record 1.0-v1marker/vc1); chmod 444 package.json; install V2 "
                "(d66a3c0e0ef64bf9) -> '[ERROR] package.json write failed', "
                "true rc=1 (re-verified without a pipe eating $?) — post state: "
                "base.apk sha == V2 d66a3c0e0ef64bf9, package.json still "
                "versionCode 1; run --package then EXECUTED V2 code "
                "([C72-VERSION] code=V2) under the V1 record. Repro pair: "
                "run/cont72/c72priv_v1.apk / c72priv_v2.apk (same package, "
                "distinct versionCode/label/marker).",
    "probe": "harness-level fault injection (chmod 444 on package.json); "
             "V1/V2 fixture pair distinguishes code identity from record identity.",
    "fanout": "every install/update path; silently-mixed identity would poison "
              "per-package evidence (provenance rows recording a version the "
              "bytes do not carry).",
    "date": "2026-10-16",
    "next_fix_surface": "staging sibling file + validation + atomic rename + "
                        "record committed before/with promotion + recovery "
                        "marker; run --package verifies record-sha vs bytes-sha "
                        "agreement before launch. NOT FIXED this wave — no "
                        "engine change beyond F-NEW-375 was made for it.",
    "verified_current": "reproducible at binary 19d090e78c5d8e23; open frontier.",
})

r["total_roots"] = len(r["roots"])
r["total"] = len(r["roots"])
r["count"] = len(r["roots"])
sc = {}
for x in r["roots"]:
    sc[x.get("status", "?")] = sc.get(x.get("status", "?"), 0) + 1
r["status_counts"] = sc
json.dump(r, open(REG, "w"), indent=1, ensure_ascii=False)
print("registry roots:", r["total_roots"])
print("F-NEW-375 status:", [x["status"] for x in r["roots"] if x["id"] == "F-NEW-375"])
print("F-NEW-376 status:", [x["status"] for x in r["roots"] if x["id"] == "F-NEW-376"])

# ── MG-116 micro registry row ──
MG = "docs/MICRO_GAP_REGISTRY.json"
m = json.load(open(MG))
t = m["tickets"]["MG-116"]
assert t["STATUS"] == "PARTIAL"
t["STATUS"] = "CLOSED"
t["EVIDENCE"] = (
    "CONT-72 dedicated law fence (issue #364 FOUNDATION-1 review): DEX-driven "
    "probe fixtures/cont72_draw_probe (aapt2/ECJ/D8; DrawProbe custom View, "
    "phase-colored 750x750 region, onDraw/onMeasure/onLayout counters, "
    "Handler.postDelayed steps at 650ms against the +300ms/frame virtual "
    "boundaries). At the UNMODIFIED record binary 86e4ebd4a2c30592 x3: "
    "invDrawDelta=1 (state change + invalidate() -> traversal -> app-owned "
    "draw), rlMeasureDelta=4 (MG-115 requestLayout law intact), coalesced "
    "invalidate x3 -> latest state drawn, screenshot 6efceae5e82fffb9 x3 with "
    "562,500 px of the app's final-state color (exact app-owned pixel proof); "
    "res-less variant (no resources.arsc, 5fd04a96063a032b) identical verdict "
    "pre-fix. HONEST MODEL NOTE: delivery holds via per-boundary full-tree "
    "traversal+draw on BOTH paths (inflater gate rt.loaded(); programmatic "
    "captured-LP path) — AOSP's dirty-region damage tracking is a documented "
    "engine-model deviation, not a correctness gap; over-delivery (a no-"
    "invalidate mutation also appears) is benign. A trial invalidate->"
    "layout_dirty fix was A/B-tested and REVERTED (delivery identical without "
    "it; binary restored byte-identical) — failed-experiment record kept.")
t["TEST"] = ("miniandroid run run/cont72/c72draw.apk --width 1080 --height 1920 "
             "--frames 20 --max-seconds 25 (x3 byte-identical) + noarsc variant; "
             "rows [C72-*] in run/cont72/mg116_fence*.log")
t["FANOUT"] = "fenced_c72 (draw/text/custom-view/drawable-state families)"
t["COMMIT"] = "CONT-72"
m["counts"]["PARTIAL"] -= 1
m["counts"]["CLOSED"] += 1
json.dump(m, open(MG, "w"), indent=1)
print("MG-116 ->", m["tickets"]["MG-116"]["STATUS"], "| counts:", m["counts"])
