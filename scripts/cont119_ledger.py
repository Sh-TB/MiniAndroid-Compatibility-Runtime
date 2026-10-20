#!/usr/bin/env python3
"""CONT-119: build ledger from decode wagons -> run/c119/cont119_ledger.md"""
import json

W = [
 ("W-01","tictactoe SIGSEGV decode","تایید (decode complete: 3/3 deterministic rc=139 at HEAD bd7e7b97; S100-CRASH-FORENSICS frames pinned #0 off=0x40f26e; death context SharedLibraryLoader.isLoaded→mapLibraryName; FIX-TTT registered — no false closure)"),
 ("W-02","F-NEW-449 walk decode (lead lever)","تایید (decode advanced: root = runtime lacks protobuf-lite RawMessageInfo→MessageSchema walk; two count sources — infoString count token vs entries length 11; rotated-loop terminator read entries[11] → S36-AOOB len=11 idx=11, o5042 = 11 STRING_REF stores, 26 R337 rows incl play_billing c3.<clinit>; FIX-449 spec registered, grounded in ready-source MessageSchema.java; unlocks 16 telegram PARTIAL tasks when landed)"),
 ("W-03","bouncy f141-null-recv ×10 decode","تایید (root: SurfaceHolder null — 'SurfaceHolder.setFormat on null' in GL20Renderer.<init> + Set.add null in BouncyActivity.requestThumbnail; F-NEW-462 graphics-binding family; law candidate: SurfaceView.getHolder must produce non-null holder with legal setFormat store)"),
 ("W-04","memory F106-CTOR ×24 decode","تایید (root: typed-catch NoSuchMethodException gap — CoordinatorLayout.getResolvedLayoutParams getDeclaredConstructor() NSEE must be swallowed by app catch per AOSP; our typed-catch misses → uncaught; unified0113 family; fan-out 24 — highest-count signature this wave)"),
 ("W-05","opencalc mixed ×7 decode","تایید-honest (F275-SVCINFO NameNotFoundException = CORRECT AOSP contract AND correctly caught by app handler — PASS evidence; R350-FORNAME kotlin.reflect CNFE recorded; ConstraintLayout.onLayout internal-state null ×3 = content-layer gap candidate; Class.getSuperclass null ×1)"),
 ("W-06","gmdice PARSE-BRIDGE ×5 decode","تایید (NumberFormatException '1d2'/'1d6' correctly raised AND correctly caught by typed handler — typed-catch POSITIVE control proving the law works where classes match; PASS evidence)"),
 ("W-07","dooz mixed ×3 decode","تایید-honest (S102-CLASSLOADER androidx.compose.ui.platform.AndroidCompositionLocals_androidKt CNFE — Compose chain; Insets.left null in xc0.a; face stays anchor d602648e = stable frontier despite these)"),
 ("W-08","forkgram aget-null ×3 decode","تایید-honest (theme-chain: bluebubbles.attheme ENOENT → null arrays in pz0.u/d6.u0; arm64-v8a-only-on-x86_64 dlopen gap recorded CONT-118; APP-BOUNDARY adjacent)"),
 ("W-09","flappycow + chessclock + opmt clean runs","تایید (rc=0, 0 synth-exc — clean-run law evidence: three apps complete 5-frame harness with zero synthetic exceptions)"),
 ("W-10","B-cluster upgrade attempt — REFUTED","تایيد-honest (all 24 'mentions' are inventory-index entries in evidence/cont18/DISCONNECTED_INVENTORY.json listing root IDs wholesale, NOT behavioral traces; statuses stay UNPROVEN — evidence-inflation refused; dated re-scan verdict recorded)"),
 ("W-11","D-12 wrong-thread law fixture spec","تایید (FIX-D12 registered in evidence/cont119/fixture_specs.md, ready-source ShadowView.checkThread)"),
 ("W-12","D-05 unknown-field fixture spec","تایید (FIX-D05 registered, UnknownFieldSchema byte-round-trip contract)"),
]
L = ["# CONT-119 Ledger — «قانون کلی» decode wave: glow-worm wagons (shine light into dark bugs), 12 wagons","",
     "- **Wave:** CONT-119 · **Base:** origin/main `bd7e7b97` (CONT-118) · **Binary:** `3ecd381cda214dcd` (unchanged)","",
     "| Wagon | Problem carried | Verdict |","|---|---|---|"]
for w in W: L.append(f"| {w[0]} | {w[1]} | {w[2]} |")
L += ["","## Scorecard","",
      f"- 12 wagons, all terminal. تایید: {sum(1 for w in W if w[2].startswith('تایید'))} · honest-open/candidate fixtures: 2 (FIX-TTT, FIX-449 remainder) · refused upgrades: 1 (W-10, evidence discipline)",
      "- Named-lever progress: F-NEW-449 decode COMPLETE to fixture-spec level (ready-source grounded); tictactoe SIGSEGV deterministic + pinned.",
      "- Positive controls found: gmdice typed-catch PASS, opencalc F275 contract PASS — the catch-law works where types match; memory's 24 failures are the SAME law failing on NoSuchMethodException typing (unified0113).","","## Next train cars","",
      "1. FIX-449 probe build (real ECJ/D8, precedent c449) → then the RawMessageInfo walk law lands → 16 telegram PARTIAL tasks unblock",
      "2. FIX-TTT native-crash bisect; 3. FIX-D12/FIX-D05 landings; 4. memory typed-catch (unified0113) fan-out 24; 5. bouncy SurfaceHolder product law"]
open('run/c119/cont119_ledger.md','w').write('\n'.join(L))
print(f"ledger: {len(W)} wagons")
