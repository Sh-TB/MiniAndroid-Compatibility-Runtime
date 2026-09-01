# CAMPAIGN_REAL_GRAPHICS_COMPATIBILITY_FINAL — UNIFIED_011.3

Campaign: UNIFIED_011.3 (master directive: FULL HISTORICAL RECOVERY + COMPLETE GAP
AUDIT + REAL-APP GRAPHICS + VERSIONED GIT HANDOFF)
BASE_VERSION: v0.11.2-unified-011-2 (`6c9a91e`; tag applied retroactively for
monotonic versioning — the 011.2 campaign shipped as an untagged handoff)
BASE_HEAD: `6c9a91e` (BASE tag `v0.11.1-unified-011-1` = `340a9cf` for the §3 delta)
FINAL_VERSION: v0.11.3-unified-011-3
FINAL_HEAD: see VERSION_HANDOFF_MANIFEST.md (recorded at packaging time)
Method: git archaeology + in-repo semantic fixtures + real-APK execution + pixel
oracles. No RESULT numbers as identity. No claim trusted without reproduction.

---

## 1. What this campaign added (evidence-first)

### 1.1 Typed-catch + cross-frame exception propagation (§18) — REAL Dalvik semantics

Before 011.3, typed catch handlers were DECODED THEN DISCARDED (`(void)type_idx` in
both `find_catch_handler_for_pc` and the THROW opcode handler) — only catch-all
handlers ever fired, and a THROW with no handler silently continued past the throw
(EXP-071 approximation). 011.3 implements:

- `is_exception_subtype()`: DEX superclass-chain walk (`class_to_superclass_`) MERGED
  with a built-in java.lang/java.io/java.util exception hierarchy (framework
  exception classes whose class_defs are not in APK DEX files — mirroring the
  EXP-068 View-hierarchy seed approach).
- Typed-handler matching in BOTH lookup paths (shared machinery + THROW), Dalvik
  order: first covering try → first subtype match → catch-all fallback → unwind.
- Caller-side try-table search at invoke sites (EXC-PROPAGATE): an exception that
  unwinds a callee frame is searched against the CALLER's try table covering the
  invoke pc; a handler hit jumps there with `pending_exception_` set so
  move-exception works. A post-switch pc redirect prevents the invoke handlers'
  `pc_ += len` from clobbering the handler jump.
- **Documented uncaught tail**: if NO frame catches, the caller continues with a
  null return. Rationale (regression-proven in-campaign): full unwind-to-top let an
  ENGINE-ARTIFACT exception escape — Telegram's `LruCache.<init>` throws
  IllegalArgumentException("maxSize <= 0") because the size computes to 0 from
  engine-local display metrics (real Android never throws there) — which unwound
  LaunchActivity.onCreate and regressed the golden to the default screen. The tail
  is the EXP-071-policy successor; caught-type semantics are fully real.
- Unit-entry parity: `execute_method` now sets `dex_report_` and builds the
  class/superclass indexes (previously only the full-APK path did — the EXP-037
  BLOCKER-002 pattern had leaked into the unit entry).

**Proof**: `tests/unified0113_typed_catch_test.cpp` — 8/8 PASS. Old code FAILS cases
1 (exact typed match), 2 (subclass match), 5 (THROW typed), 7 (cross-frame catch);
case 6 proves skip-and-continue removed; case 8 pins the documented uncaught tail.
`tests/unified0112_filled_new_array_test.cpp` still 5/5 (no regression).

### 1.2 Second-frame visual correctness (§22/§23) — the central metric chain

The 011.2 click-test recorded "181,512 px" (gmdice) and "918,207 px" (ssw) state
changes. **This campaign reclassified those numbers as artifacts**: the probe
re-rendered via an ad-hoc `content_view->measure/layout/draw` that bypassed the real
renderer (root selection + SoftwareCanvas/BitmapFont + resource image decode) and
produced a near-blank second frame — visually verified during the campaign
(blank white + one black rectangle for gmdice).

Fixes (two root causes):

1. **GFX-FRAME2-RENDER**: the probe now calls `stage_render_frame` — the IDENTICAL
   pipeline that produced frame 1. A true before/after oracle is now possible.
2. **GFX-FRAME2-THIS**: XML `android:onClick` handlers were invoked with `this` =
   the clicked View object (the activity's heap object was never passed). Every
   instance-field access inside the handler (`this.big`, `this.chrono`) hit the
   wrong heap object — the smoking gun was `[EXP091-SETTEXT] view_id=0 text=""`.
   The activity heap id is now recorded at creation
   (`ActivityShadow::set_activity_heap_id`, called from `execute_apk_with_activity`)
   and passed as p0.

**Result (simplestopwatch, real APK, real click on "Start")**:

```text
before frame  →  real dispatch onButtonStart (activity 'this')
              →  app logic: pressFirstButton → MyChrono.firstButton
                 → startUpdating → save (SharedPreferences real file write)
                 → updateViews → setText on REAL view ids
              →  stage_render_frame re-render
              →  SECOND FRAME: buttons now read "Stop" / "Lap"
                 (the REAL running-state semantics of the app)
oracle: changed_px=12,373 (0.597%), bbox=(24,4)-(793,1919),
        bottom-third concentration 12,051 px (button row) — JSON evidence in
        docs/evidence/u011_3/oracle/ssw_start.json
```

Honest residual: the second frame renders the correct STATE with a reflow artifact
(buttons vertical vs horizontal — GFX-SSW-REFLOW, deferred cosmetic). GMDice's roll
click dispatches and the handler chain runs deep (getDiceSet → selectDice →
DiceCache.populate → 8× getString → new GameMasterDice$7), but its roll UI is
runtime-constructed (dialog/dynamic views) and never enters the ViewShadow — true
second-frame delta is 0 px (GFX-FRAME2-RUNTIMEVIEWS = the named next blocker).

### 1.3 Historical reconciliation (§3/§4) — git-only

- Every commit after `340a9cf` tabled with files/tests/real-app effect in
  `RECOVERED_11_1_TO_HEAD_DELTA.md`.
- What 011.1 LACKED (verified 0-occurrence at `340a9cf`): runtime exception
  machinery, typed catch, image resource chain population, click dispatch probe,
  FNA semantic fixture.
- `4a39f1b`/"176-176": **REJECTED** — not a valid object; absent from all 75
  commits and all 12 recovery archives. Preserved as evidence.
- The "121/122 smali semantic fixture suite" **exists nowhere** in tree, history,
  or archives — work lost without a handoff (the exact §0 failure mode). Revived
  in-repo as C++ semantic fixtures including the typed-exception class it
  reportedly failed.
- 011.5/012/NEXT campaigns: do not exist (re-verified via `git log --all`).

## 2. Real-app scorecard at FINAL_HEAD (§32; matrix 24/24 runs deterministic)

| App | Process | Activity | View Tree | Resources | First Frame | Correct Frame | Touch | Callback | State Change | Second Frame | Highest Stage |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Telegram v12 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (golden `088ea640…` 3/3) | ✓ (audit path) | ✓ | ✓ | ✓ (deterministic) | **L12 deterministic render preserved** |
| WhatsApp | ✓ (12 DEX) | ✓ (AppShell→Main.onCreate) | partial | partial | ✗ | ✗ | ✗ | ✓ (typed catches fire in LX/* code) | ✗ | ✗ | L2 (blocker: HandlerThread/Looper threading in LX/0F7 chain) |
| Signal | ✓ | ✓ (init) | ✗ | ✗ | ✗ | ✗ | ✗ | ✓ (2.8M instr into androidx camera/lifecycle init; ISE handled gracefully) | ✗ | ✗ | L2+ deep-init (probe window boundary) |
| GMDice | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (L12 visuals) | ✓ | ✓ | ✓ (logic) | 0 px (runtime-views gap) | **L12 — L13 pending runtime-view construction** |
| SimpleStopwatch | ✓ | ✓ | ✓ | ✓ (icons+strings) | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ (Stop/Lap, oracle 12,373 px) | **L13 candidate (visual-correct second frame)** |
| microtimer/unote/chessclock/headingcalc/notesbill/simplekeyboard/openlauncher | ✓ | ✓ | ✗ (default screen) | ✗ (obfuscated ARSC / entry chain) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | L1–L2 (grouped CONFIRMED_OPEN) |
| dooz | ✓ | ✓ | ComposeView 0 children | n/a | ✗ (blank) | ✗ | ✗ | n/a | ✗ | ✗ | L3 (0.8 s — livelock fix holds; Compose runtime BLOCKED) |
| tictactoe (libGDX) | ✓ | ✓ | ✗ | ✗ | ✗ (blank) | ✗ | ✗ | ✗ | ✗ | ✗ | L2 (libGDX backend BLOCKED) |
| stopwatch (muellerma) | ✗ exit 1 | — | — | — | — | — | — | — | — | — | L0 (truncated APK — external boundary) |

Baselines: telegram `088ea640587ec0d2…` PRESERVED 3/3; simplestopwatch `2a12587a…`
PRESERVED 3/3; gmdice `472c1d3c…` PRESERVED 3/3 (158,040 non-white px). No golden
was overwritten; the 011.2 anchor move (ssw, icons by design) remains the current
anchor with its recorded reason.

## 3. Graphics capability matrix (final §40 answers)

| Capability | State at FINAL_HEAD | Evidence |
|---|---|---|
| Real images render (XML src → decode → pixels) | **YES** | exp_graphics_image_e2e + ssw icons |
| Text render (BitmapFont/FreeType/HarfBuzz/FriBidi path) | **YES** | WS-C2 6/6 + ssw/gmdice frames |
| Canvas (subset: rects/text/measure; save/clip/transform partial) | YES (subset, STUB_DEBT documented) | render pipeline |
| Custom View render (app subclasses, e.g. BigTextView) | **YES** | ssw frames |
| PNG | **YES** (libpng; RGB/RGBA/palette/tRNS) | 12/12 fixture + real icons |
| WebP/JPEG | YES (libwebp/libjpeg, magic-selected) | decoder branch + prior evidence |
| VectorDrawable/NinePatch | NO (placeholder path) | CONFIRMED_OPEN |
| Visual oracle | **NEW** — px/%, bbox, row distribution | scripts/u0113_oracle_diff.py + JSONs |
| Exception machinery | **YES — typed matching + cross-frame catch** (uncaught tail = documented compat) | typed_catch_test 8/8 + Telegram LX catch-alls |
| Multi-DEX | YES for resolution (Telegram 5-DEX golden; WhatsApp 12-DEX parse + cross-DEX dispatch); entry threading = new named blocker | probes |

## 4. Versioned handoff (§0/§38/§39)

- VERSION_HANDOFF_MANIFEST.md — mandatory manifest, exact fields.
- MiniAndroid_v0.11.3_GIT_HANDOFF.zip — contains complete `.git`, tracked source,
  tests, experiments, docs, evidence indexes, campaign state; ZERO APKs; no file
  >5 MB; SHA256 recorded; clean-extract verified (git status clean vs tracked set,
  final commit verified, fixtures re-run FROM THE EXTRACT).
- Per-milestone commits during the campaign: code first, docs second — no work
  existed only in chat or an uncommitted worktree at any point.

## 5. Remaining high-value items (ranked per §36)

1. **GFX-FRAME2-RUNTIMEVIEWS** — runtime-constructed views (gmdice roll dialog,
   dynamic LinearLayouts) never enter ViewShadow; blocks L13 on the only real game.
2. **IMG-HEAP-MODEL** — Bitmap heap identity (decode→object→view state→renderer);
   unlocks setImageBitmap/decodeResource (WhatsApp avatars, broader image apps).
3. **APP-WA-THREADING** — WhatsApp HandlerThread/Looper semantics (LX/0F7 chain);
   entry chain itself already works (this campaign's probe evidence).
4. **APP-SIGNAL-INIT** — longer probe window once threading model lands (same
   family as #3).
5. **RES-OBFUSCATED** — ARSC obfuscated-name resolution (unote/headingcalc first
   screens).
6. VectorDrawable/NinePatch minimal decoder (state lists block several corpus
   first screens' pressed/selected states).
