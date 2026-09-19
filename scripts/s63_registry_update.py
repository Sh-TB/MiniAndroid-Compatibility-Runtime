#!/usr/bin/env python3
"""S63 registry update: F-113 Random-inheritance law (R-NEW-382) implemented.

Follows the S58/S62/S62+ registry-update pattern: load root_registry.json,
patch/add the specific roots with evidence-anchored entries, save.
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


F113 = {
    "id": "F-113",
    "title": "java.security.SecureRandom IS-A Random bridge law (R-NEW-382) — framework-subclass virtual dispatch must resolve ancestor laws",
    "status": "IMPLEMENTED+TESTED",
    "priority": "P0",
    "fg": True,
    "first_seen": "S63 (gmdice v1.2 source-first build)",
    "evidence": (
        "miniandroid/src/dex/dalvik_engine.cpp F-086 block (S63): "
        "bridge_to_api receives the STATIC receiver class; SecureRandom "
        "instance calls never reached the F-086 Random law (Random + "
        "ThreadLocalRandom only) and nextInt(bound) answered typed-zero 0 — "
        "every die rolled 1 in gmdice (5x [EXP091-SETTEXT] text=\"1\"). "
        "Upstream law: OpenJDK SecureRandom.java:157 'public class "
        "SecureRandom extends java.util.Random' + :828 'protected final int "
        "next(int numBits)' (fetched from github.com/openjdk/jdk). Fix: law "
        "family += Ljava/security/SecureRandom;. Post-fix: dice 6/5/3/2, "
        "rollresult texts 6/5/3/2, frame SHA pair 5312266e→fa1d8612, pixel "
        "diff 1,584 px 100% inside the result band; 3-run det fa1d8612 ×3. "
        "Regression: battery ALL PASS (94 stages executed) on the fixed "
        "binary. Evidence: docs/evidence/s63_spotlight/S63_REPORT.md §1-§2"
    ),
}

R382 = {
    "id": "R-NEW-382",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P0",
    "title": "gmdice dice roll typed-zero face (SecureRandom.nextInt → 0)",
    "fg": True,
    "first_seen": "S63 first gmdice source-first run",
    "evidence": (
        "SOURCE OBSERVATION: gen.nextInt(sides) with "
        "Random generator = new SecureRandom(). MINIANDROID TRACE: 5 rolls "
        "all \"1\"; [REC-MISS] SecureRandom.nextInt → static-class bridge "
        "misses F-086. UPSTREAM: OpenJDK SecureRandom extends Random "
        "(:157), next(int) override (:828). SEMANTIC LAW: SecureRandom "
        "IS-A Random → F-113. FIXED: dice 6/5/3/2, changed frame proven "
        "(1,584 px diff in the rollresult band). Evidence: "
        "docs/evidence/s63_spotlight/S63_REPORT.md §1"
    ),
}

f113 = find("F-113")
if f113:
    raise SystemExit("F-113 duplicate")
add(F113)

r382 = find("R-NEW-382")
if r382:
    raise SystemExit("R-NEW-382 duplicate")
add(R382)

reg["summary"] = reg.get("summary", "")
reg["note"] = reg.get("note", "")

with open(REG, "w") as f:
    json.dump(reg, f, indent=1, ensure_ascii=False)
    f.write("\n")

print(f"registry updated: {len(roots)} roots (added F-113, R-NEW-382)")
