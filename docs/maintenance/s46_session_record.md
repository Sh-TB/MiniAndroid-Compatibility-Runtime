# S46 SESSION RECORD — R-NEW-361 ROOT-CAUSED+FIXED · AGENT GAMEPLAY PROVEN · PERSISTENCE GATED

Date: 2026-09-15 · Base: origin/main b82b43c5 (S45) · Binary: rebuilt from S45 sources + S46 laws

## 0. State reconciliation (mission §0)
- Local HEAD = origin/main = `b82b43c5` (stale local origin ref 7a172e7c healed by `git fetch`; 0/0 divergence; clean tree).
- Build from authoritative source: engine rebuilt (2× full make runs during diagnostics).

## 1. R-NEW-361 — ROOT-CAUSED, FIXED, VERIFIED (the S45→S46 frontier)
- **Class identity (DEX ground truth, raw bytes via scripts/s46_rawbytes.py)**: `Lbw0;` = androidx.collection **1.4.x MutableScatterSet** (R8-renamed): `.a`=add (iget size → invoke .d → move-result → iget elements → `aput-object v4, v2, v1` @pc=8 → return size!=oldSize), `.d`=findAbsoluteInsertIndex (671 units), `.c`=findKeyIndex, fields `.a`=metadata/.b=elements/.c=capacity/.d=size/.e=growthLimit. Upstream 1.4.0 fetched from Google Maven (`upstream/scatter_s37/collection-1.4.0-sources.jar`); S37's fetched ScatterMap.kt was a truncated copy.
- **Runtime forensics** (new env-gated diagnostics: MINIANDROID_S46_TABLEDUMP, MINIANDROID_S46_HALT_DUMP, MINIANDROID_MT_BUDGET/SKIP_INV):
  - Per-invocation `[S46-TABLE]` dumps (59 invocations) showed the table growing 7→15 CORRECTLY, inserts/removes correct, then at `size=14 growthLimit=0` **the whole table converted to 0xFE (Deleted)** — `dropDeletes()` taken where upstream law demands `resizeStorage(31)`: `adjustStorage()` = `if (capacity>8 && size*32 <= capacity*25) dropDeletes() else resizeStorage(...)` → 14×32=448 > 15×25=375 → RESIZE. The engine took dropDeletes → rehash degraded to one-byte-per-invocation → **final state `size=15=capacity, growthLimit=-1, ZERO 0x80 bytes`** → `findAbsoluteInsertIndex`'s probe loop can never satisfy `maskEmpty()!=0` → **HALT-LOOP at pc=0x1c after 50,001 visits / 2.4M instructions** → force-exit returns garbage → `.a`'s `elements[garbage]` → **`aput-oob length=15 index=-733270216`** (the exact S45 signature).
  - `[S46-HALT]` register dump at the halt: probeIndex=400000 (=50000×8), capacity=15, h2=56, h1=31341969.
- **ROOT CAUSE**: `Ljava/lang/Long;.compare(J,J)I` was UNIMPLEMENTED (F-055 implemented only the Long bit-method family). The unimplemented call returned 0 → `if-gtz 0` false → dropDeletes branch. (The `Integer.compare` 32-bit twin existed; the Long mirror did not.)
- **FIX (F-055b, generic, OpenJDK Long.java laws)**: `Long.compare / compareUnsigned / signum / sum / max / min` — 64-bit exact, in the Long block (dalvik_engine.cpp).
- **VERIFICATION**: dooz v23 post-fix = **0 AIOOBE, 0 HALT-LOOP** (run/s46_fix1_stderr.log); dooz v18 = past the old `LP/v$a;` crash, deep Compose flow (ComposeView children=1) — one generic fix advances both variants (mission §13 ✓). Regression: **battery 90/92 (only pre-existing EXT-01/02), TicTacToe §29 ALL PASS, deterministic replay 613cfccc0f27… intact.**

## 2. New honest frontiers (registered, not hidden)
- **R-NEW-362** (dooz v23, post-361): `IllegalArgumentException("Can't put value with type null into saved state")` from the compose saveable registry (`Lje;.<init>` message builder; `Lnb0;.n` pc=162/171/193/198 → `Lwo;.j` → `Lfb1;.a/.J`) → uncaught at MainActivity.onCreate → APP BOUNDARY. The saved value (or its class lookup) resolves NULL — next attack documented in the registry.
- **R-NEW-363** (2048): `org.secuso.privacyfriendly2048_100` (F-Droid, sha 02c799d3…) first run: `LifecycleRegistry.forwardPass` HALT-LOOP at pc=0xd — `SafeIterableMap$IteratorWithAdditions.next` re-entry cycle (M3-19-CYCLE depth=8, 66k+ calls) — live-iterator advance law gap. Next attack documented.

## 3. AGENT GAMEPLAY PROVEN (mission §7 — the acceptance test)
- New engine mode `--agent-play N` (`stage_agent_play`): per step **observe** the app's own rendered view texts → **decide** (win:complete-line > block:opponent-line > take-center > take-corner > first-empty) → **act** (real `dispatch_click` on the chosen view) → **verify** the observed state transition. Phase-b auto-probe skip fixed so the agent loop owns the interaction.
- TicTacToe fixture run: **9/9 dynamic moves, every transition verified, per-move pixel diffs 2,741–2,797 px, final rendered status = DRAW** (optimal hotseat play — the agent plays both sides; the WIN terminal state is separately proven by §29). Policy reasons differ per step (center/corner/win/block/first-empty) — dynamic selection, not scripted playback.
- Evidence: `docs/evidence/s46_agent/` (REPORT.md, engine manifest, GIF built from the actual runtime PNGs — sha c98214d3…, per-frame SHA list).

## 4. Install/Persistence status (mission §10/§11)
- **Battery-gated**: M3 F-012 persistence+fresh-state determinism golden — SQLite-backed app data committed in run A renders in run B's first frame on the SAME data root; byte-deterministic across two independent pairs (microtimer, ≥90 frames/run). = install → play → save → close → relaunch → restore (Phase A/B) with a real persistent app-data semantics (`runtime/data/<package>/databases`, `shared_prefs`).
- Cross-process board restoration also observed on the TicTacToe fixture (finished board restored at launch in a separate process).

## 5. Regression gate (mission §12)
- TicTacToe §29: ALL PASS (8 checks) at this HEAD.
- Full battery: **90/92 — only the pre-existing EXT-01/EXT-02 external-fixture gaps. ZERO regressions.** GATE H PASS.

## 6. Honest verdict
- The one-registered-root-away promise from S45 was kept: R-NEW-361 is ROOT-CAUSED to a missing JDK API and FIXED with a generic law; both Dooz models advanced past it.
- STOP COUNTING ROOTS → START COUNTING PLAYABLE GAMES: TicTacToe Classic remains the fully playable anchor (now with a proven agent loop); Dooz advanced one more frontier (R-NEW-362); 2048 adopted with its blocker (R-NEW-363) honestly registered.
