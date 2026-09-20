#!/usr/bin/env python3
"""s70_register_f136_r389.py — S70 registry updates.

F-136: registered + FIXED (ARSC-first string resolution law).
  - contract: AOSP Context.java:945-978 -> Resources.java:464-592
    (docs/upstream/aosp/CONTEXT_STRING_LAW.md)
  - root cause: string resolution used the legacy name-keyed side cache
    (field_name_by_resid_ -> resource_string_values_) as PRIMARY, violating
    the single-resolution-path law (F-080/M3-007 precedent for colors);
    Resources.getString(int,Object...) format args were silently ignored;
    getText had no handler at all.
  - fix: dalvik_engine.cpp Resources block (ARSC-first + name-map fallback +
    java_format_walk) and Context-family block (ARSC-first primary).
  - proof: f53_getstring fixture (3 law paths, ViewTree texts + row ink),
    determinism x3 byte-identical (8c11659a7ca24512), foundation battery
    23/23 PASS, corpus A/B: 9/10 apps byte-identical.

R-NEW-389: registered, OPEN (P1) — bouncy 81-px top-band divergence.
  - observed: S70 A/B regression — bouncy frame_000 sha 53177d4a (S69 golden,
    reproduced by S69-source builds incl. comment-only probe) vs 4f41dda2
    (F-136 builds), 81 px in band (3,0)-(93,4), dark(24,24,24)->yellow(255,255,0).
  - evidence: bridged API dispatch traces IDENTICAL (0 status/count diffs),
    ViewTree texts IDENTICAL, determinism x3 on both sides (per-binary
    deterministic), reproducible across two independent F-136 builds and
    across two independent S69-source builds.
  - suspicion (NOT a verdict): sub-pixel paint path sensitive to binary/
    layout state in the score-bar top band; F-136 correlation may be
    incidental layout shift. Requires investigation before F-136 may claim
    zero collateral on bouncy.
"""
import json
from pathlib import Path

REG = Path("/home/z/my-project/root_registry.json")
reg = json.loads(REG.read_text())
ids = {r["id"] for r in reg["roots"]}

new = []
if "F-136" not in ids:
    new.append({
        "id": "F-136",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "title": "ARSC-first string resolution (Context/Resources.getString/getText law)",
        "fg": True,
        "first_seen": "S70 active-graph census: Resources.getString served only "
                      "the legacy name-map (EXP-052) while getColor was already "
                      "ARSC-first (F-080/M3-007); Resources format overload "
                      "ignored args; getText unserved",
        "evidence":
            "UPSTREAM: AOSP Context.java:945-978 + Resources.java:464-592 "
            "(docs/upstream/aosp/CONTEXT_STRING_LAW.md, fetched from googlesource "
            "main 2026-09-20). LAW: single resolution path — Context delegates "
            "to Resources; Resources resolves through the asset manager (ARSC); "
            "formatted overload == String.format(raw, args). FIX: dalvik_engine.cpp "
            "Resources block + Context-family block now resolve ARSC-first via "
            "ResourceRuntime::arsc().resolve_string, name-map kept as fallback, "
            "java_format_walk wired for formatted overloads (both sides). "
            "PROOF: f53_getstring fixture (Context plain + formatted + Resources "
            "direct; ViewTree asserts + row ink regions) PASS; determinism x3 "
            "byte-identical sha 8c11659a7ca24512; foundation battery 23/23 PASS; "
            "corpus A/B 9/10 byte-identical (bouncy delta registered separately "
            "as R-NEW-389). CONSUMERS: fan-out Context.getString 130 static "
            "sites x 8 APKs; Resources.getString 47 x 4.",
    })
if "R-NEW-389" not in ids:
    new.append({
        "id": "R-NEW-389",
        "status": "OBSERVED-FAIL",
        "priority": "P1",
        "title": "bouncy 81-px top-band divergence across builds — dispatch-"
                 "identical, ViewTree-identical, cause unidentified",
        "fg": True,
        "first_seen": "S70 corpus A/B regression (F-136 wave)",
        "evidence":
            "OBSERVED: bouncy frame_000 sha 53177d4a (S69 golden; reproduced by "
            "S69-source rebuilds AND a comment-only-probe rebuild) vs 4f41dda2 "
            "(F-136 builds, x3 deterministic). PIXEL: 81 px in band (3,0)-(93,4), "
            "(24,24,24)->(255,255,0) — score-bar top band. EVIDENCE AGAINST A "
            "DISPATCH CAUSE: bridged api_calls.json status/count aggregates "
            "IDENTICAL pre/post; ViewTree node texts IDENTICAL; getString "
            "dispatch markers identical (3x EXP088-B-DISPATCH, no F136 markers). "
            "DETERMINISM: per-binary x3 byte-identical on both sides — "
            "build-sensitive, not run-sensitive. SUSPICION (unproven): paint/"
            "layout state sensitive to binary layout (UB class) in a path "
            "without dispatch or ViewTree provenance. NEXT: instrument the "
            "score-bar paint path (SoftwareRenderer top band), audit for "
            "uninitialized/order-dependent state; per §25 F-136's collateral "
            "claim is bounded to the 23/23 fixture battery + 9/10 corpus apps "
            "until this closes.",
    })
added = 0
for n in new:
    if n["id"] not in {r["id"] for r in reg["roots"]}:
        reg["roots"].append(n)
        added += 1
reg["note"] = reg.get("note", "") + (
    f" | S70: F-136 (ARSC-first strings) FIXED, R-NEW-389 registered; "
    f"registry {len(reg['roots'])} roots.")
if added:
    REG.write_text(json.dumps(reg, indent=1))
print(f"registered {added}: registry now {len(reg['roots'])} roots")
