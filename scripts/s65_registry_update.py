#!/usr/bin/env python3
"""S65 registry update: F-118 activity-constructor law (R-NEW-385) and
F-119 X.TYPE / primitive-array descriptor law (R-NEW-386) implemented.

Follows the S58/S62/S63/S64 registry-update pattern: load
root_registry.json, add the new roots with evidence-anchored entries, save.
"""
import json

REG = "root_registry.json"

with open(REG) as f:
    reg = json.load(f)

roots = reg["roots"]
by_id = {}
for r in roots:
    by_id.setdefault(r.get("id"), []).append(r)


def find(rid):
    return by_id.get(rid, [None])[0]


def add(entry):
    if entry["id"] in by_id:
        raise SystemExit(f"{entry['id']} already present — refusing to duplicate")
    roots.append(entry)
    by_id[entry["id"]] = [entry]


F118 = {
    "id": "F-118",
    "title": (
        "Activity-constructor law (R-NEW-385) — every activity-construction "
        "path must run the declared no-arg <init>()V before onCreate "
        "(Instrumentation.newActivity / performLaunchActivity contract)"
    ),
    "status": "IMPLEMENTED+TESTED",
    "priority": "P0",
    "fg": True,
    "first_seen": "S65 (TriPeaks v1.2.1 source-first build)",
    "evidence": (
        "G08 startActivity path (ExecutionEngine::consume_pending_intent) "
        "did heap.allocate() + onCreate and SKIPPED <init>: instance-field "
        "initializers never ran, so TriPeaks GameActivity's field-"
        "initialized cardClickListener stayed typed-zero; setOnClickListener "
        "registered listener_id=0 ([EXP060-LISTENER]) and all 52 card taps "
        "were silently dead (DOWN hit, no PerformClick). Upstream: AOSP "
        "Instrumentation.java:1448 newActivity(ClassLoader,String,Intent) → "
        "instantiateActivity (constructor runs; fetched 2026-09-19 from "
        "aosp-mirror/platform_frameworks_base @ main). Fix: <init> dispatched "
        "via try_recursive_invoke with a [G08-LIFECYCLE] record. After: "
        "listener_id=38, UI-EVENT CLICK → GameActivity$1 (real handler). "
        "Second consumers day one: OPMT GameActivity <init> 26 insns, "
        "FishRings GameActivity chain. Regression: battery 92/94 + "
        "EXT-01/02 environmental, zero new failures. Evidence: "
        "docs/evidence/s65_spotlight/S65_REPORT.md §3"
    ),
}

R385 = {
    "id": "R-NEW-385",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P0",
    "title": "TriPeaks dead card taps (field-initialized listener = typed-zero)",
    "fg": True,
    "first_seen": "S65 first TriPeaks board interaction",
    "evidence": (
        "SOURCE: GameActivity.java:74 field-initialized "
        "View.OnClickListener. TRACE: GameActivity;.<init> never executed "
        "(no TRY-ENTRY) while the launch activity's <init> ran — the G08 "
        "path skipped the constructor. UPSTREAM: Instrumentation.newActivity "
        "contract. LAW: F-118. AFTER: clicks dispatch to the real "
        "GameActivity$1; later stages blocked by the OBJECT-IDENTITY family "
        "(recorded, deferred). Evidence: "
        "docs/evidence/s65_spotlight/S65_REPORT.md §3"
    ),
}

F119 = {
    "id": "F-119",
    "title": (
        "X.TYPE primitive-class + primitive-array descriptor law (R-NEW-386) "
        "— Integer.TYPE & friends answer canonical Class objects; "
        "Array.newInstance builds [I-style descriptors for primitives"
    ),
    "status": "IMPLEMENTED+TESTED",
    "priority": "P0",
    "fg": True,
    "first_seen": "S65 (FishRings v1.23 source-first build)",
    "evidence": (
        "[SGET-MISS] Ljava/lang/Integer;.TYPE obj_id=0 → "
        "Array.newInstance(NULL, dims) → null matrix → aput-null NPE in "
        "FishRingsForAndroid Rings.init (3 uncaught, rc=1 PARTIAL). "
        "Upstream: OpenJDK Integer.java:106 'public static final "
        "Class<Integer> TYPE = Class.getPrimitiveClass(\"int\")' — "
        "JVM-injected, never written by <clinit>; Array.java:74/110 "
        "newInstance contract (fetched 2026-09-19 from openjdk/jdk @ "
        "master). Laws: (a) X.TYPE for "
        "Integer/Boolean/Byte/Character/Short/Long/Float/Double/Void → "
        "primitive Class descriptors I/Z/B/C/S/J/F/D/V; (b) "
        "Array.newInstance primitive components build '[I'-style "
        "descriptors (no L...; wrapper), recursively ('[[I') so check-cast "
        "succeeds. After: [R358-ANEW] newInstance(I, dims=[3,12]) -> [[I; "
        "rc=0 SUCCESS; FishRings full chain S10 det ×3. Regression: battery "
        "92/94 zero new failures (TicTacToe R-NEW-358 Button[][] golden "
        "PASS on the changed path). Evidence: "
        "docs/evidence/s65_spotlight/S65_REPORT.md §4"
    ),
}

R386 = {
    "id": "R-NEW-386",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P0",
    "title": "FishRings board NPE (Integer.TYPE typed-zero → null matrix)",
    "fg": True,
    "first_seen": "S65 first FishRings run",
    "evidence": (
        "SOURCE (dex dump): Rings.<init> int[12][3] board = "
        "Array.newInstance(Integer.TYPE, new int[]{12,3}). TRACE: "
        "[SGET-MISS] Integer.TYPE → null → [SYNTH-EXC] aput-null NPE. "
        "UPSTREAM: Integer.java:106 + Array.java:74/110. LAW: F-119a/b. "
        "AFTER: rc=0, full interaction chain, changed frames 483,395/"
        "478,169/7,347 px, det ×3, S10 PROVEN. Evidence: "
        "docs/evidence/s65_spotlight/S65_REPORT.md §4"
    ),
}

for e in (F118, R385, F119, R386):
    if find(e["id"]):
        raise SystemExit(f"{e['id']} duplicate")

add(F118)
add(R385)
add(F119)
add(R386)

reg["summary"]["total_roots"] = len(roots)
reg["summary"]["last_updated"] = "S65 2026-09-19"
reg["summary"]["note"] = (
    "S65 breadth: 3 NEW source-first apps executed (TriPeaks S7 + det ×3, "
    "FishRings S10 PROVEN with 3 input→state→changed-frame interactions "
    "det ×3, OPMT S6 + app-own nextInt(0) stopper). New laws: F-118 "
    "activity-constructor (R-NEW-385 — G08 launches now run <init>; 3 "
    "consumers day one) + F-119 X.TYPE/primitive-array (R-NEW-386). New "
    "open family: OBJECT-IDENTITY (field/array element view-ref identity "
    "churn — blocks TriPeaks S8/OPMT S7+, forensic trail recorded). "
    "Battery 92/94 + EXT-01/02 environmental; zero regressions. S64 "
    "commit carried PENDING-PUSH into this session (no credential); S65 "
    "commit carries both. || S64: 3 apps (pmk S6, FreeKlondike S10, SLC "
    "S9) + F-114..F-117."
)

with open(REG, "w") as f:
    json.dump(reg, f, indent=1, ensure_ascii=False)
    f.write("\n")

print(f"registry updated: {len(roots)} roots (added F-118, R-NEW-385, F-119, R-NEW-386)")
