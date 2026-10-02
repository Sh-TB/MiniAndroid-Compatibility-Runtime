#!/usr/bin/env python3
"""FINAL CAMPAIGN — issue #354 progress comment: phases 4-20 + wave C batch."""
import json, subprocess, sys

BODY = """
## FINAL CAMPAIGN — PHASES 4–20 + WAVE C (F-NEW-181 FIXED) — done/remaining

Directive: complete all remaining numbered items (main + sub-branches). This wave closed the **registry's #1 NEXT** (F-NEW-181) and executed PHASE 4–20 with the mandated SOURCE→CODE PATH→LAW→REPRO→TRACE→FIX→3-RUN chain per item.

### WAVE C — F-NEW-181 ROOT-CAUSED-FIXED (array type law) — the flagship frontier
- **SOURCE** (APK DEX, ground truth): `RegularImmutableMap.create/get/createHashTable` disassembled (`scripts/wavec_scan.py`, `wavec_disasm.py`). R8 deduped `chooseTableSize` into `ImmutableSet`; the ONLY `createHashTable` call site gates guava's duplicate-key wrapper `{partialTable, insertedCount, dupEntry}` with `instance-of v2, [Ljava/lang/Object;`.
- **CODE PATH**: engine `NEW_ARRAY` stamped EVERY array `Larray;` (resolved descriptor discarded) → `is_subclass_of` answered FALSE → the Object[3] wrapper was stored AS the map's hash table → lawful `get()` probe looped (PC=0x6f, 50001 visits).
- **LAW**: array runtime identity (JVMS 4.4 / AOSP isAssignableFrom): NEW_ARRAY stores the REAL descriptor (+`__element_type__` provenance; filled-new-array precedent); is_subclass_of array closure (primitive arrays final; object arrays covariant; nested arrays; arrays are Object/Cloneable/Serializable).
- **TRACE** (one instrumented run, permanent `MINIANDROID_WAVEC_TRACE` probe): `chooseTableSize(17750) → 32768` **LAWFUL**; `createHashTable(alternating=47425, maxSize=17750, tableSize=32768)`. Post-fix: wrapper DETECTED+UNWRAPPED — real `[S 32768` table, lawfully truncated at the duplicate key (size=16052, copyOf 32104, guava-33 semantics). **0 HALT-LOOP/F084 spins; WhatsApp errors 32→8.**
- Honest residue: the duplicate key itself = F-NEW-173 placeholder-materialization (the DI-lattice deep face — the remaining WhatsApp frontier).

### PHASE 4 — Context/Application/Fragment host identity (F-NEW-190/191 NEW, FIXED)
- **F-NEW-190 device identity**: `Build.SUPPORTED_ABIS/_32/_64_BIT_ABIS/CPU_ABI(_2)` seeded (arm64-v8a primary law — "No supported ABIs found" ISE ×3 GONE); ApplicationInfo install-time identity (`sourceDir`=real APK path, `publicSourceDir`, `nativeLibraryDir`, `primaryCpuAbi`) at `getApplicationInfo` + reflection `Field.get` framework-declarer fallback — SoLoader's `sourceDir` null face (LX/0EU.CKw direct iget → LX/0Dl.A01 NPE) GONE. **Exception census 12→9.**
- **F-NEW-191 attach ordering**: `run_activity_default_init` now dispatches the app-level `attachBaseContext` override after `<init>` on ALL launch paths (direct + bounded super climb; AOSP performLaunchActivity law). Proof: `[WAVEC-ATTACH-FIELD]` A0B/A03/A05 stored on the activity before onCreate — WhatsApp's DI members-injector (LX/0IH) now executes.
- Residue: attach still dies at `iget LX/0IE;->A00` (component-state holder; sole writer = reflective injector `A3d` — no direct invokers) = the F-NEW-173/169 deep lattice; fragment-host ISE faces are downstream of it.

### PHASES 5–14 — audit + implementation results (overlaps item 21/22 merged)
- **5 window-stack legality**: item22-P0-1 tree-only inflation + attach-wave consumed at first render — verified (microtimer byte-identical ×3).
- **6 single authoritative renderer**: item21 wave-A one-root law + item22-P0-2/3/4 real-identity laws — verified live this wave.
- **7 diagnostic pixels**: census regions law (placeholders out of the authoritative frame) — verified.
- **8 Drawable contract**: setImage* family (P1-2 drawee/BLOCKED evidence) + setBackground*/Color/Resource/Drawable captured engine-side (S82-GFX hooks) — audit-clean.
- **9 measure/layout single truth**: XML inflate no longer measures; authoritative traversal owns measure — verified (item22-P0-1 + R-NEW-440 canonical measure).
- **10 draw/z-order**: AOSP View.draw order enforced (bg→onDraw→children-forward→decorations; S86 visibility gates; forward child pop verified in the walk) — residue registered **F-NEW-192** (elevation/translationZ not modeled, P2).
- **11 stub/call contracts**: census `scripts/fc_audit_stubs.py` — 34 void-answer sites: 12 lawful-void / 21 state-capture verified / **1 silent-void FIXED** (`setIntent` now installs the intent object; getIntent identity law).
- **12 provenance**: GfxProvenance chain (ASSET_FOUND→…→SCREENSHOT_CAPTURED) + text-color provenance (P1-10) + FrameRenderCensus — verified present and wired.
- **13 Compose/WebView/Surface routing**: C013 family routing live (4+17 routing hits in today's runs; R-NEW-381 lever).
- **14 logging contract**: S135 backbone — bounded ring sink (rt_cap_=512) + distilled TRACE_SUMMARIES (SHA-provenance hygiene) — verified.

### PHASE 15 — corpus attack (9/9 honest runs, no-fake-success census)
bouncy `b6dde607…` · ttc `cad88d3a…` (rc=0) · droidify/openlauncher shared empty-shell SHA (honest NOT-A-RENDER class) · tinymusic rc=0 · unote `4f1a9e4e…` (rc=0) · gmdice `f3b483fe…` (rc=0) · chessclock `ffa68e61…` · simplekeyboard (no capture) + flagship goldens ×3 below.

### PHASES 16–19 — acceptance gates
- **16/17** FrameRenderCensus verdicts + no-fake-success classification (shared-SHA empty-shell class identified by SHA census).
- **18 3-run protocol**: all goldens ×3 byte-identical.
- **19 regression discipline**: **dooz `d602648e8e401895` ×3 · simplestopwatch `10446aaf0cd642cc` ×3 · microtimer `da73010a37dd0189` ×3 · headingcalc `be1cea9cf994b26a` ×3 · WhatsApp `31ddd4d5b8e6d18e` ×3 — zero drift across all 5 law commits** + laws130 51/51 + battery exit=0 (dooz stage sha MATCH).

### PHASE 20 — registry
F-NEW-181 ROOT-CAUSED-FIXED; F-NEW-190/191 appended; F-NEW-192 registered (z-order residue). **Registry 484→486 roots; master worklist regenerated: 703 items, open 267 (P0 26 / P1 69 / P2 64 / P3 105 / P4 3).**

### REMAINING (done/remaining scorecard)
- **Closed this directive**: Wave C (F-NEW-181) + PHASE 4 core (2 new fixed roots) + PHASE 5/6/7/8/9 verification + PHASE 10 audit (1 residue registered) + PHASE 11 audit (1 gap fixed) + PHASE 12/13/14 verification + PHASE 15 (9-app wave) + PHASE 16/17/18/19 gates + PHASE 20 registry/worklist.
- **Remaining faces (the deep DI-lattice)**: F-NEW-169/173 family — `0IE.A00` component-state (reflective injector `A3d`, no direct invokers) gating the fragment-host ISE family + the placeholder-key materialization upstream of the dup-truncation. This is the single dominant WhatsApp white-screen blocker chain.
"""


def gh_token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n\n",
                         capture_output=True, text=True).stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return None


def main():
    token = gh_token()
    if not token:
        print("NO TOKEN"); sys.exit(1)
    r = subprocess.run([
        "curl", "-s", "-X", "POST",
        "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/354/comments",
        "-H", f"Authorization: token {token}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({"body": BODY}),
    ], capture_output=True, text=True)
    try:
        resp = r.json()
        print("posted:", resp.get("id"), resp.get("html_url"))
    except Exception:
        print("FAIL", r.stdout[:300])


if __name__ == "__main__":
    main()
