# S67 · FOUNDATION HARDENING — MASTER WORK LIST
# (the giant list: my census merged with the user's 26 sections, ordered fan-out-first)

Contract cycle for EVERY item (no exceptions):
`BASE CONTRACT → SOURCE/UPSTREAM LAW → MINIANDROID IMPLEMENTATION → MICRO TEST →
 REAL APK TEST → PIXEL/STATE/TRACE PROOF → REGRESSION → ONLY THEN IMPLEMENTATION`

Anti-false-success law: rc=0 / PNG exists / nonwhite>0 / handler-called / state_changed
are NOT success. Proof is per-subsystem semantic (render: expected geometry→expected
pixels→raw fb→decoded PNG; input: MotionEvent→hit-test→listener→state→rerender;
layout: measure→layout→ViewTree geometry→actual pixel geometry; resource: id→table
entry→typed value→consumer→visible effect).

Statuses allowed: PROVEN PARTIAL IMPLEMENTED TESTED OBSERVED RESEARCHED BLOCKED UNTESTED.
(For visual claims also: VISUALLY_PROVEN / NO_VISUAL_PROOF / RENDER_BLOCKED.)

---

## WAVE 0 — RECON (user §1) — DONE this session
- [x] HEAD/origin/dirty/pending/battery/environment snapshot → S67_RECON.md
- [x] Architecture graph draw+input from real live build files
- [x] Renderer / layout / resource / DEX / input / scheduler / text / image / evidence
      subsystem census (3 parallel deep-census agents + manual runtime census)
- [x] Contract-gap registry (S67_MY_CENSUS.md: A1-A10, B1-B12, C1-C12, D1-D7)
- [x] Toolchain restore (bootstrap_toolchain.sh) + engine rebuild (zero code changes)

## WAVE 1 — BASE MICRO-CORPUS (user §17, 45 fixtures) — harness this session
Infrastructure: `tests/fixtures_foundation/fXX_<name>/` each with src/ + res/ +
AndroidManifest.xml → build via scripts/build/build_fixture_apk.sh → run engine →
verify harness `scripts/foundation/verify_foundation.py` (PNG re-decode + pixel
assertions + trace checks, independent of engine logs).
- [ ] R01 color solid, R02 shapes, R03 alpha blend, R04 text, R05 Persian, R06 image,
      R07 bitmap scaling, R08 canvas transform, R09 clipping, R10 nested views
- [ ] L11 LinearLayout, L12 weight, L13 FrameLayout, L14 RelativeLayout, L15 nested,
      L16 margins, L17 padding, L18 gravity, L19 wrap_content, L20 match_parent
- [ ] I21 button, I22 nested click, I23 overlapping views, I24 disabled, I25 long press
- [ ] LC26 initial activity, LC27 startActivity, LC28 constructor, LC29 field init,
      LC30 static init
- [ ] RES31 string, RES32 color, RES33 drawable, RES34 style, RES35 theme, RES36
      reference, RES37 density
- [ ] RT38 object identity, RT39 null, RT40 arrays, RT41 primitive arrays, RT42
      reflection, RT43 superclass dispatch, RT44 interface dispatch, RT45 exceptions

## WAVE 2 — RESOURCE FOUNDATION (user §3) — fixes for Tier A resource items
- [ ] A1 ?attr at inflate: upstream ResTableManager/Theme.applyStyle law → implement
      resolve_theme_attr at inflate → micro RES35/RES36 → OPMT real APK → regression
- [ ] A2+A8 dimen seeding/convert law (complex_to_dimension_pixel_size at seed;
      remove 24px fallback, resolve via ARSC) → RES37 → gmdice/TriPeaks
- [ ] A7 manifest label via resources + icon parse → HelloWorld/TriPeaks
- [ ] A10 Theme.resolveAttribute + Theme.getColor + Resources.getSystem → RES35
- [ ] B11 view-level android:theme, B12 @android: framework id mapping (static table
      of the ~40 ids apps actually use), C11 fraction, C12 fontScale note

## WAVE 3 — RENDERER FOUNDATION (user §5, §8, §9, §10) — fixes for Tier B render items
- [ ] View→pixel provenance fixture (user §10: RED view at (100,200,300,400), assert
      red exactly in that box) → R01/R02
- [ ] A4 INVISIBLE must not draw → R10 + real APK + regression
- [ ] A5 Paint.setARGB handler; B8 setTextSize consumed; A9 getWidth from canvas
- [ ] B7 roundRect radius raster; circle stroke ring raster
- [ ] B1 canvas matrix stack (scale/rotate/skew/concat as real matrix, applied at
      replay for rect/text/path/bitmap) — architecture risk: full evidence first
- [ ] B2 clipRect enforcement (clip stack intersect at replay)
- [ ] B4 saveLayer offscreen + restoreToCount
- [ ] Alpha semantics: document/handle C8 (framebuffer opaque; alpha visible only
      within frame) — 1-LSB rounding law from S66 note
- [ ] Colors/alpha numeric fixture (user §8: 000000/FFFFFF/FF0000/00FF00/0000FF/
      80FFFFFF/80FF0000, expected vs actual vs cause table)

## WAVE 4 — TEXT FOUNDATION (user §7)
- [ ] A6 Canvas text: route through TextShaper (HarfBuzz) instead of ASCII bitmap
      (or shrink: keep bitmap font but honest NO-OP + warning for non-ASCII)
- [ ] Persian fixture R05: shaping/joining/order/baseline proven via pixel bbox +
      glyph metrics (NOT just "pixels exist")
- [ ] B9 italic synthesis; B10 fallback chain (at least honest notdef counting
      surfaced in trace)

## WAVE 5 — IMAGE PIPELINE (user §6)
- [ ] A3: dispatch non-PNG drawables through correct decoder (magic-based), error
      placeholder + trace line when undecodable
- [ ] B3 BitmapFactory.decodeStream/decodeResource/decodeFile/decodeByteArray laws
- [ ] assets/ image decode path; density inDensity→inTargetDensity fixture R07

## WAVE 6 — LAYOUT/MEASURE (user §4) — Tier B/C layout items
- [ ] C2: render-without-measure RL path must run measure_layout (or refuse loudly)
- [ ] C1: programmatic RL children edge resolution (LayoutParams p rules)
- [ ] C3 LL horizontal TOP gravity; C4 gravity field separation
- [ ] B5 setX/setTranslationX + AbsoluteLayout x-y LayoutParams
- [ ] B6 ScrollView scrollY/scrollTo/scrollBy + draw translation + clip
- [ ] TriPeaks real APK re-run (R-NEW-388 residual closure proof)
- [ ] C5/C6: setText raises layout dirty; invalidate → explicit full-frame law

## WAVE 7 — INPUT + STATE→RENDER (user §11, §12)
- [ ] I21-I25 fixtures: hit-test coordinates vs rendered coordinates SAME-SOURCE proof
      (click at rendered cell center → listener)
- [ ] disabled/invisible/overlapping/long-press trace laws
- [ ] state→invalidation fixture: state mutation → framebuffer changed (STATE_ONLY
      vs VISUALLY_PROVEN distinction, user §12)
- [ ] Dooz: compose foundation gap list (user §20): snapshot/atomic publication/
      LayoutNode measure precondition — generic micro-proof per missing piece

## WAVE 8 — RUNTIME/DEX CENSUS + MICRO-PROOFS (user §2, §16, RT38-45)
- [ ] class/method/field/static/clinit/ctor/object-identity/null/primitive-ref/arrays/
      multi-dim/reflection/exceptions/type-conv/wide/register-typing micro fixtures
- [ ] F-118 law re-check across Fragment/Dialog/Service objects (user §2)
- [ ] startActivity == initial-activity semantic equality fixture (LC26/LC27)

## WAVE 9 — CROSS-VALIDATION + DETERMINISM (user §13, §18)
- [ ] HelloWorld, TicTacToe, gmdice, FishRings, TriPeaks: source/build provenance →
      DEX → manifest → resource → ViewTree → layout → render → input → state →
      frame SHA, each linked to the micro-test proving its base contract
- [ ] 3-run determinism per fixture: trace SHA + frame SHA + pixel SHA
      (deterministic != correct noted explicitly)

## WAVE 10 — SEARCHLIGHT (user §14, §15) — tools must be USED, ledger per subsystem
- [ ] zoekt/csearch re-index (shards lost to reset) or fetch-file citations with
      SHA-verified pinned commits (S66 pattern)
- [ ] Per-law ledger rows: tool/query/repository/result/class/method/decision

## WAVE 11 — MATRICES + DOOZ GAP + FINAL (user §19, §21, §22, §24)
- [ ] FOUNDATION_GAP_MATRIX.md (P0/P1/P2 × fan-out/current-impl/upstream-law/test-
      coverage/APK-consumers/known-failure/next-fix)
- [ ] FOUNDATION_TEST_MATRIX / RENDER_MATRIX / RESOURCE_MATRIX / LAYOUT_MATRIX /
      RUNTIME_MATRIX (canonical, updated as tests run)
- [ ] Every failure → generic contract classification (user §19), no app-patching
- [ ] Final report with the exact user-specified counters + ROOT CAUSE NOT SYMPTOM
      per failure

## Sequencing law (this session)
Wave 0 done → harness + first fixtures (R01/R02/R03/R04, L11/L13/L14, RES31/RES32,
I21) → matrices created → honest report. Remaining waves are explicitly queued work,
not silent omissions.
