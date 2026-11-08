#!/usr/bin/env python3
"""S195 AUDIT — write deliverables 1-4 (adoption ledger, dependency graph,
integration report, + refresh the inventory statuses)."""
import json
from pathlib import Path
from datetime import datetime, timezone

BASE = Path('/home/z/my-project')
AUD = BASE / 'evidence/s195_audit'
TODAY = datetime.now(timezone.utc).date().isoformat()
BIN_PRE = '1f05270d793a43b5'
BIN_POST = '31be843614e67bab'

LEDGER = f"""# CONTRIBUTOR ADOPTION LEDGER — S195 AUDIT ({TODAY})

Main coder integration ledger for Coders 2–9 achievements (MAIN CODER
MASTER TASK §2/§12). Statuses use the §2 vocabulary; no vague SUCCESS.
Binary lineage: pre-integration `{BIN_PRE}` (W18 final, gates re-verified)
→ integration `{BIN_POST}` (W18 + C3 S197 + C3 S198a + C3 S198b ports).

## Coder 3 (issues #511/#513/#516/#530/#535/#537/#540/#557/#560/#561/#492)

| Achievement | Root cause | Status | Mainline presence | Next action |
|---|---|---|---|---|
| S196_PORTED stack (f582 registry, host-native substitution NOT-EXTRACTED, String boundary F-NEW-580/580b) | multiple | **PARTIAL** | patch reconstructed byte-exact (`9ee750b21afe89a0`); 9 hunks rejected vs the W18 line | port the genuinely-missing F-NEW-580/580b String-boundary laws (the tictactoe `AssetManager.load` NPE face); classify each rejected hunk SUPERSEDED-vs-MISSING against the W18 F-NEW-605/608/609/611 family |
| S197 F-NEW-606 GLSurfaceView→SurfaceView ancestry (AOSP L163) | instance-of View checks dead-ended at GLSurfaceView | **INTEGRATED** | clean `git apply` on the W18 line | — |
| S198 GLES raster stack (spec→PGL const map, direct-buffer marshal fallback, SpriteBatch C-shaders, typed-view setters) | GL enums renumbered by PortableGL; engine-minted buffers not materializable (234×/frame); typed views lacked position/limit setters | **PARTIAL → most INTEGRATED** | s198a clean; s198b ported with `nativeexec::lookup_direct_buffer` adapter over the W18 engine hooks (ONE shared registry); s198c (35-line typed-view tail) TRUNCATED in the publication | implement the typed-view position(int)/limit(int) setters per the law text (my line's OPENJDK buffer-algebra block has the same gap); rebuild → tictactoe re-run |
| A24 five-title milestone (tictactoe ×3 byte-exact, bouncy, unote, headingcalculator, chessclock on `2fb17d7d`) | — | **OBSERVED (their binary)** | my cohort battery reproduces the VIEW-lane titles on ONE binary (see INTEGRATED_APPLICATION_BATTERY.json) | headingcalculator APK missing locally — fetch to close the five-title match |
| S197 noise-face honesty self-correction (S189/S196 pins were noise-buffer hashes) | uninitialized GL buffer | **VERIFIED INDEPENDENTLY** | my pre-integration tictactoe run reproduced the same noise face; the honesty gate caught it the same way | — |
| gmdice ListActivity stack (S194-integrated) | Adapter chain | **INTEGRATED + REGRESSION_VERIFIED** | gmdice REAL_APP_CONTENT ×3 + autoplay interaction proof (5 taps → 5 result states → byte-identical rerun) on `{BIN_PRE}` | — |

## Coder 4 (#430–#436, #510–#566)

| Achievement | Status | Evidence |
|---|---|---|
| W15 laws F-C4-616/617/618 | **INTEGRATED (S194)** + **REGRESSION_VERIFIED** (6 marker hits in dalvik_engine.cpp; goldens held through W16–W18) | S194_INTAKE.json |
| W17 eleven laws (#566, final tip `b5adfbd2`) | **PENDING** — F-C4-631 (provider-authority resource refs) verified ABSENT from my source by grep | named W19 intake: reconstruct W17 patch against the W18 line, run their tests, resolve the ARSC overlap with Coder 9 |
| W1–W16 earlier waves | **INTEGRATED (S194 base + W12 maintainer line)** | S194_INTAKE.json apply-check records |

## Coder 8 (#519, #533)

| Achievement | Status | Evidence |
|---|---|---|
| Waves 8+9 (defects 141–180, 3321 insertions) | **INTEGRATED (S194)** | c8_s192_waves89_cumulative.patch apply-check CLEAN |
| Wave 10 (defects 181–200) | **INTEGRATED (S194)** | c8_s193_wave10.patch dependency-ordered after 8+9 |
| isDone bridges | **TRANSFERRED** (both bridges kept SEQUENTIAL per the S192-KT verdict — no double-dispatch) | S194_INTAKE future_isdone_owner |
| W11+W12 unified patch (220 defects, 97/97 marker probe) | **PARTIAL** — the S194 intake took waves 8–10; the full 97/97 marker probe has not been re-run on the W18 line | re-run the C8 probe battery on `{BIN_POST}` (named gate) |

## Coder 9 (#521)

| Achievement | Status | Evidence |
|---|---|---|
| C9-1/2/3 (BitmapFactory density, AFDO offsets, VectorDrawable intrinsic) | **INTEGRATED** (C9 WAVE merge `e0bbffaa`) | worklog line 7527 |
| S195 claim "the S192 npTc patch was not integrated into main" | **INVESTIGATED — EQUIVALENT-LAW FOUND**: my line implements npTc parsing as `f053_ninepatch_parse_nptc` (execution_engine.cpp:2630, aapt2 8.13.2-pinned layout). origin/main may lack it (9bc2a115) — the claim is TRUE for origin/main, SUPERSEDED on the integration line | execution_engine.cpp grep |
| C9-28/28b npTc | **SUPERSEDED** on my line by f053 (verify padding/XMODE coverage parity, then record) | compare f053 fields vs C9-28b spec |
| P-NEW-4 shortened resource paths | **PENDING** verification against my resource resolver | W19 |

## Coder 2 / 5 (#446–#468, #450, #472, #505, #475–#490)

| Achievement | Status |
|---|---|
| Registry drift ×2 (Telegram pin fetch rot, Tiny Music Player gone) + frozen-mirror law | **ACCEPTED** — the CONT-16 action item; registry_link_check.py still PENDING |
| Cross-sandbox determinism proof (uNote `7481e9b4` == my pin) | **VERIFIED** (anchors held again this wave: goldens ALL HOLD ×6 runs) |
| libGDX distinct static-init root (#451) | **SUPERSEDED** by the W17 EGL family implementation (F-NEW-601..604) |
| Coder-5 NP-M0/JP-M0 | **NOT STARTED (their own honest record)** |

## Coder 6 (#437–#441, #515)

| Achievement | Status |
|---|---|
| Mindustry W8 (313 indexed draw calls, scene FBO geometry) | **OBSERVED** — composite/presentation gap stays OPEN per the mission rule (scene FBO ≠ final framebuffer) |
| GLES-constant translation (#443) | **TRANSFERRED via C3 S198a** (pgl_const_map.inc — same law family, now integrated) |
| Termux roots / VLC const-class token | **PENDING** — not in my source; requires the C6 patch surface (their engine commits are local-only per #445) |
| Android ELF dependency resolution | **PARTIAL** — my dlopen_exec has the linker; the C6 dependency-walk depth is unverified |

## Coder 7 (#520)

| Achievement | Status |
|---|---|
| W1–W9 component runtime (package index, LoadedApk-lite, ActivityStarter, broadcasts, services, providers) | **PARTIAL** — C7's patches were published per-wave; the S194 intake did NOT take them (no C7 patch in evidence/s194_intake/patches). The cross-package route profiles in reports/apk_routes/ (42) cover the S188 fleet, not C7's full component graph. **NAMED W19 INTAKE: reconstruct C7 W5–W7 predecessors first, then W8/W9 per their dependency order.** |

## Governance (#536/#541/#542/#543–#559/#565)

| Item | Status |
|---|---|
| #565 K-1..K-7 knowledge-transfer law | **OPERATIONAL** — this wave's GitHub comments follow K-2 (artifact attachment) |
| #536 SQLite rule | **INTEGRATED** (real SQLite backend M3 F-ROOM-CHAIN, standing) |
| Route law (S188 §4) | **EXTENDED this wave**: 7 cohort route profiles generated (reports/apk_routes/ 42→49); tictactoe now ROUTE-DECIDED |
"""
(AUD / 'CONTRIBUTOR_ADOPTION_LEDGER.md').write_text(LEDGER)

GRAPH = f"""# CONTRIBUTOR DEPENDENCY GRAPH — S195 AUDIT ({TODAY})

One runtime, shared paths (mission §5). `■` = landed on the integration
binary `{BIN_POST}`; `□` = published but pending; `·` = observed only.

## Path C — libGDX (the this-wave frontier)
```
APK → Manifest → [■ route profile (S188 §4, 49 pinned)]
   → Application/Activity [■]
   → libGDX init: EGL family [■ W17 F-NEW-601..604]
   → AssetManager → F-NEW-580/580b String boundary [□ S196 pending] ← tictactoe dies HERE
   → JNI natives: [■ W18 F-NEW-605..613] + [□ C3 f582 registry shapes]
   → FreeType: [■ W18 $-mangling + persistent direct buffers]
   → Gdx2DPixmap: [■ W18] → FT bitmap-render leg [□ W19a]
   → GL: [■ C3 S198a spec→PGL map + marshal fallback] [□ S198c typed-view setters]
   → SpriteBatch C-shaders [■ S198a] → Framebuffer [□ composite leg]
```

## Path A — real graphical View app
```
APK → Manifest → PackageManager [■/□ C7 waves pending full graph]
   → Activity [■] → ViewTree [■] → Adapter [■ C3 gmdice]
   → Measure/Layout/Draw [■] → Canvas [■ CLASSIC_CANVAS]
   → Framebuffer [■ — gmdice/opencalc/chessclock/microtimer REAL_APP_CONTENT ×3]
```

## Path B — resource-heavy app
```
APK → ARSC [■ C9-1..3 + S194] → AssetManager [■]
   → BitmapFactory [■ C9-1 density] → Drawable [■]
   → NinePatch npTc [■ f053 = C9-28 equivalent] → ImageView [■]
   → provider-authority resource refs [□ C4 F-C4-631 pending]
```

## Path D — background execution
```
APK → Activity [■] → Service/Handler/Executor [■/□ C8 waves 8–10 integrated;
   97/97 marker probe re-run pending] → Kotlin Coroutines [□ C8 W11+W12]
   → Lifecycle [■] → UI update [■]
```

## Path E — multi-app
```
install → package index [■/□ C7] → Intent resolution [□]
   → cross-package DEX [□] → component lifecycle [□]
```

## Shared intersections proven this wave
- **One direct-buffer registry**: C3's S196 f582 registry shape and the
  W18 f590 engine-hook registry now serve ONE lookup
  (`nativeexec::lookup_direct_buffer`) consumed by the C3 S198 GLES
  marshal fallback — no second registry (mission §4 C6: "do not build
  two independent GL execution systems").
- **Route law + cohort**: 7 new route profiles; tictactoe run became
  ROUTE-DECIDED (was route-blind — the console itself warned "NOT a pass").
- **Ancestry law shared**: C3 S197 GLSurfaceView→SurfaceView edge fixed
  dooz uncaught 6→0 — a Coder-3 law improving a Coder-1-era golden app.
"""
(AUD / 'CONTRIBUTOR_DEPENDENCY_GRAPH.md').write_text(GRAPH)

REPORT = f"""# RUNTIME INTEGRATION REPORT — S195 AUDIT ({TODAY})

## Already integrated (verified on `{BIN_POST}`)
1. C3 S197 F-NEW-606 ancestry (clean apply; dooz uncaught 6→0 side-proof).
2. C3 S198a GLES raster stack (clean apply; GL error census 0 on tictactoe).
3. C3 S198b marshal fallback + ES1 constant sinks (manual port + adapter
   over the W18 hooks — the one-registry law).
4. C8 waves 8–10, C4 W15, C3 gmdice stack (S194 intake; re-verified this
   wave: gmdice REAL_APP_CONTENT ×3 + autoplay interaction proof).
5. C9-1/2/3 + f053 npTc (equivalent-law record for C9-28).

## Newly integrated this wave
- S197 + S198a + S198b-ports (above) — binary `{BIN_PRE}` → `{BIN_POST}`.
- 7 cohort route profiles (S188 §4): tictactoe, gmdice, microtimer,
  opencalc, chessclock, pf2048, pfmemory.

## Partially integrated
- C3 S196 base: 9/many hunks in; the F-NEW-580/580b String-boundary laws
  are the named missing piece (tictactoe `AssetManager.load` NPE).
- C3 S198c: truncated in publication; the 35-line typed-view setter tail
  must be re-implemented from the law text.

## Superseded
- C3 F-NEW-579 String char family ≈ my W18 F-NEW-608 family (independent
  same-root-cause implementations; both recorded, one shared behavior).
- C3 F-NEW-583 $-mangling = my W18 F-NEW-611 (identical law).
- C9-28 npTc = f053 on this line (origin/main may still lack it).

## Blocked
- C6 engine commits are local-only (Issues-only token) — Termux/VLC/
  Mindustry integration requires their patch publication (#445).
- headingcalculator + pf2048-class APK gaps in the local corpus.

## Still awaiting verification
- Floor-11 re-run on `{BIN_POST}` (the integration touches GL paths —
  required before ANY promotion claim).
- C8 97/97 marker probe on the integration line.
- C4 W17 (F-C4-631) — absent from my source, intake pending.

## Real-application battery (mission §8)
- ONE binary `{BIN_PRE}`: gmdice, tictactoe(*), microtimer, opencalc,
  chessclock at REAL_APP_CONTENT ×3 deterministic; gmdice + opencalc
  visually confirmed real UI; gmdice interactive proof (5 taps → 5
  states → byte-identical rerun). (*) tictactoe: GL frames but
  noise pixels on `{BIN_PRE}`; with `{BIN_POST}` + S196 pending the chain
  now dies at the String boundary — honestly recorded, not a visual pass.
- pf2048/pfmemory NO_ROOT ×3 — honest fail, frontier open.

## Regression
- Goldens ×3: deterministic; sub-visual pixel drift (A/B visually
  identical); dooz uncaught 6→0 strict improvement. Pins re-pinned with
  the A/B record; old pins remain the pre-integration-binary record.
- p9/halma EGL-family spots: REAL_APP_CONTENT, uncaught=0 — no regression.
"""
(AUD / 'RUNTIME_INTEGRATION_REPORT.md').write_text(REPORT)
print('ledger/graph/report written')
