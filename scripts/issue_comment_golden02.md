## GOLDEN-02 — EXTERNAL INTERACTIVE VISUAL: REAL USER ACTION → CALLBACK → STATE MUTATION → SECOND FRAME — commit `7babcbd6`

**CLAIM.** The same frozen external APK (EXT-01 HelloWorldSelfAware v1.1.0, SHA-256 `009b4671…cc41`, no substitution) exercises MiniAndroid's real interaction path end-to-end:

```
long-press gesture → ACTION_DOWN → hit-test (ViewShadow tree, AOSP touch law)
→ target = the APK's own full-screen TextView → 500 ms ViewConfiguration
long-press timeout → performLongClick → the APK's OWN registered listener
object (MainActivity implements View$OnLongClickListener, DEX-verified)
→ real dalvik dispatch of its own onLongClick bytecode
→ ClipData.newPlainText + ClipboardManager.setPrimaryClip  (REAL state mutation)
→ Toast.makeText(…).show() → toast window painted by the SAME framebuffer
pipeline → second rendered frame (frame_001.png) → ACTION_UP click
SUPPRESSED per AOSP mHasPerformedLongPress law.
```

**INTERACTION CHAIN FROM APK BYTES** (oracle `scripts/dump_apk_interaction.py`, 7/7 chain links PASS, independent of the runtime parser): `onCreate: invoke-virtual TextView.setOnLongClickListener(this)` → `onLongClick(View)Z` → `Utils.copyText` (SDK_INT 34 branch → ClipData.newPlainText → setPrimaryClip) → `Toast.makeText(…, toast_copied, LENGTH_LONG).show()` → `return true`.

**QUANTITATIVE EVIDENCE** (`scripts/compare_ext01_interaction.py`, `interaction/interaction_golden.json` committed — never a single number):

| Quantity | Value |
|---|---|
| frame size | 1080×1920 (both frames) |
| background (modal) | rgb(0,0,0) both |
| changed pixels | 12,488 |
| changed bbox | (428,1768)–(650,1823) = 222×55 px |
| toast band | inside bottom quarter (y ≥ 1440) ✓ |
| centering | bbox center x=539 vs 540 → centered ✓ |
| hello text block above band | pixel-identical ✓ |

**GOLDEN-02 VERDICT: PASS (12/12 static checks)** — dimensions, background, changed-pixels exist, bottom-band confinement, centering, text-block unchanged, dispatched, consumed, click-suppressed, press on-screen, target is TextView, hello text unchanged.

**DETERMINISM.** 3 independent runs (`runA`, `detB`, `detC`) of `--long-press 540,960`: target=4, dispatched=true, consumed=true, suppressed=true, diff_px=12,488 — **frame_000 and frame_001 byte-identical across all 3 runs** (unique SHA count = 1 each; `e242ac1e…d7a0`).

**GENERIC PLATFORM BEHAVIOR ADDED (no fixture-specific code).** (1) `dispatch_long_click(view_id, consumed&)` per AOSP `View.performLongClick` law — real registered listener object, listener's boolean return = consumed. (2) Long-press gesture driver `stage_long_press` + `--long-press x,y` (hit test → 500 ms law → dispatch → UP suppression per `mHasPerformedLongPress`). (3) Hit-test touchability extended: `LONG_CLICKABLE` views are touch targets (AOSP `View.isTouchable`). (4) `ClipboardShadow` — `ClipData.newPlainText`, `setPrimaryClip`/`getPrimaryClip`/`getText`, legacy `ClipboardManager.setText`. (5) Toast rendering via the pre-existing `DialogShadow` law into the same framebuffer.

**REGRESSION AFTER THE CHANGE: ALL PASS** — helloworld 26/26, tictactoe 8/8, mutf8 14/14, semantic 96/96, corpus 3/3.

**CLAIM DISCIPLINE.** `runtime-proven (interaction)`. NOT claimed: pixel-identity of toast typography to a device reference (no trusted long-press reference exists for this fixture — recorded residual); ACTION_MOVE out-of-bounds cancellation (single-point driver; queued for a later input gate).

**EVIDENCE FILES.** `docs/evidence/GOLDEN02_EXTERNAL_INTERACTION_RECORD.md` · `docs/evidence/external_hello_golden/interaction/` (frame_000.png, frame_001.png, interaction_golden.json, manifest.json) · `scripts/dump_apk_interaction.py` · `scripts/compare_ext01_interaction.py`.

Pushed to `main` — verified this session via `git ls-remote` (HEAD `dc18dcd2`, local↔remote in sync, 0 ahead / 0 behind).
