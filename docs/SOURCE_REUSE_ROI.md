# SOURCE REUSE ROI — open-source acceleration ledger (S96)

> **Purpose:** make every future MiniAndroid wave require LESS custom coding and
> produce MORE verified APK compatibility per unit of engineering time.
> This is the canonical reuse ledger: for every problem class it records the
> existing source/tool that was (or should be) reused, the reuse strategy, the
> custom work avoided (conservative ranges — never invented precise numbers),
> and the measured corpus fan-out.
>
> Companion laws: CONSTITUTION §170 (Graphics Source-First), §171 (Open-Source
> Advantage — added this wave). Registry:
> [GRAPHICS_SOURCE_REGISTRY.json](GRAPHICS_SOURCE_REGISTRY.json)
> (127 entries · 122 distinct verified repos · 48 evidenced laws · 65 deep-inspected ·
> 20 upstream test corpora · 3,996 test files · 426 hash-evidenced files · 789 symbol hits).
>
> ⚠ **Honesty law:** `time saved` values are conservative RANGES bounded by the
> recorded measured data (S95: 11 APKs re-measured, ~1,200 LOC implementation delta,
> 8 laws). Where no controlled baseline exists the entry says so — no invented hours.

---

## 1. Reuse ROI table

| Problem | Existing Source/Tool | Strategy | Custom Work Avoided | Corpus Fan-out | Status |
|---|---|---|---|---|---|
| Vector/adaptive drawable decode gap (WRONG_COLOR) | AOSP `VectorDrawable.java` / `AdaptiveIconDrawable.java` @ pinned `1cdfff55` | PORT_ALGORITHM + PORT_FIXTURE (9-law battery fixture) | 1–3 days (vector path parser + icon layer compositor from scratch) | 3 titles cleared (hotdeath PASS; bouncy + urlchecker 3×→0); every themed APK benefits | DONE (S95, measured) |
| Button wrap_content below material minimum (WRONG_CLIP) | AOSP `styles_material.xml` @ `1cdfff55` (sha `10eca71a…`), `TextView.onMeasure` clamp | PORT_ALGORITHM (48dip/88dip law = L-S95-BTNMIN-1) | 4–8 hours (blind measure debugging) + protects future menu layouts | bobball 4×→0; dodge 1 button fixed; all menu-bearing APKs | DONE (S95, measured) |
| Theme-less apps render with fabricated white window | AOSP `themes_device_defaults.xml`/`themes_material.xml`/`colors_material.xml` (3 files hash-pinned) | PORT_ALGORITHM (default-dark chain = L-S95-DEFTHEME-1) | 4–8 hours (theme resolver from scratch) | every theme-less APK (L0–L2 family); fixed gmdice regression too | DONE (S95, measured) |
| Color-less text color resolution | AOSP `TextView` default-textColor law + S68 theme chain | ADAPT (L-S95-TXTCLR-1) | 1–4 hours | textColorPrimary-bearing APKs (majority of L2 family) | DONE (S95, measured) |
| ImageButton default-fill bug | view_renderer UNIFIED_007 exclusion + S95 fill law | ADAPT (L-S95-ICONBTN-1) | <1 hour | ImageButton-family APKs | DONE (S95, measured) |
| ANIMATION_FROZEN misclassification | S95 corrected tap protocol in `scripts/s95_capture.py` (view-tree-derived touch targets) | TOOL_FIX (harness, not engine) | 1–3 days (wrong engine rewrite avoided) | mini-tetris + minicraft re-proven x3; all future tap captures | DONE (S95, measured) |
| GIF decode/disposal semantics (12 GIF titles) | google/wuffs (`wuffs_gif__decoder`, 437-file test corpus), Pillow `_seek`, golang `image/gif/reader.go`, FFmpeg `gifdec.c` | ADAPT (wuffs = drop-in candidate; compositor rework is the cost) | 3–7 days (GIF decoder from scratch) + test corpus free | 12 GIF VERIFIED-INTERACTIVE titles + animated-drawable APKs | OPEN (P0, source mapped) |
| Screenshot golden/gate infrastructure | ndtp/android-testify `ScreenshotRule.kt`, cashapp/paparazzi, takahirom/roborazzi | REFERENCE_ONLY + TEST_ONLY (record/verify separation) | 1–3 days (gate design) | all 148 canonical titles | PARTIAL (S93 repeatability gate operational) |
| WebView visual readiness | chromium `AwContents.java`, WebKit `ImageLoader.cpp`, electron `ready-to-show`, WPT corpus | REFERENCE_ONLY (readiness model design) | 3–7 days (blind readiness model) | 83 WebView titles in S91 demand map | OPEN (P1, source mapped) |
| Bidi / RTL shaping | unicode-org/icu `ubidi.cpp`, fribidi | ALGORITHM_PORT | 3–7 days | RTL/locale-split titles; Persian corpus (S90) | OPEN (P1) |
| HarfBuzz/Minikin complex shaping | AOSP minikin `Layout.cpp` (pinned raw fetch, S94) + HarfBuzz test suite | PORT_ALGORITHM — POC proven, wire-up pending (TEXT-001) | >1 week (shaper from scratch) | complex-script titles | PARTIAL |
| Layout measure laws (weights/gravity/minHeight) | AOSP `LinearLayout.java` measure chain (`LinearLayout.java` weight = leftover/sum law) | PORT_ALGORITHM (GFX-002 diagnosed, weight law next) | 4–8 hours per blind fix | dodge menu + all weighted-layout APKs | ROOT_CAUSE_FOUND (GFX-002) |
| DEX/interpreter semantics | dalvik/art source studies + 96-stage semantic family | PORT_TEST (CTS-style fixtures) | >1 week | every executed APK | DONE (S-era) |
| Kotlin object model / AtomicFU semantics | kotlinx-coroutines-atomicfu sources; Kotlin property-reader laws | PORT_ALGORITHM | 1–3 days | Dooz/Compose-chain titles (CONC-001) | PARTIAL |
| Dice randomness (gmdice SecureRandom) | OpenJDK `SecureRandom` law F-113 | PORT_ALGORITHM | 1–4 hours | gmdice + random-bearing APKs | DONE |
| APK/resource build toolchain | aapt2 + ECJ + D8 + android-34 stubs (`tools/`) | DIRECT_REUSE | >1 week (custom compiler avoided) | every fixture + in-house game build | DONE |
| Search over source library | zoekt + codesearch benchmarked vs ripgrep (`docs/corpus/SEARCH_LEDGER.md`) | DIRECT_REUSE (tooling) | 1–3 days (index build tuning) | all source-lookup waves | DONE (S61) |
| Automatic law consultation | `tools/source_lookup.py` (mandatory §170 step 2; S95: 6 recorded calls → 11 laws) | DIRECT_REUSE (tooling) | <1 hour per investigation | every graphics failure investigation | OPERATIONAL |
| Control-system consistency gate | `tools/validate_control_system.py` (147 checks) | DIRECT_REUSE (tooling) | 4–8 hours per audit wave | README/tickets/roadmap drift | OPERATIONAL |
| Canonical evidence validator | `tools/verify_canonical_evidence.py` (148 titles, SHA-linked) | DIRECT_REUSE (tooling) | 4–8 hours per evidence wave | all canonical artifacts | OPERATIONAL |

---

## 2. TIME SAVED records (§13 format — conservative ranges only)

| Tool/source | What it replaces | Estimated custom implementation avoided | Affected subsystem | Affected corpus | Evidence |
|---|---|---|---|---|---|
| S94 source registry + `source_lookup.py` | manual "read everything and guess" investigation | 1–4 hours per failure investigation (6 investigations in S95 alone) | graphics/resolver | 11 APKs re-measured in S95 | [roi_record.json](evidence/s95/roi_record.json) — 6 calls → 11 laws |
| AOSP pinned law files (5 hash-pinned) | reverse-engineering Android theme/style behavior from APK bytes | 1–3 days per subsystem | themes/styles/text | simplestopwatch + all theme-less APKs | [GRAPHICS_SOURCE_LIBRARY_VALIDATION.md](GRAPHICS_SOURCE_LIBRARY_VALIDATION.md) §3 |
| aapt2/ECJ/D8 toolchain | writing an APK build pipeline | >1 week (one-time, already amortized) | toolchain | every fixture + 5 in-house games | `tools/` + `games/*/` build scripts |
| wuffs/Pillow/golang GIF test corpora (planned) | designing GIF disposal test cases | 4–8 hours of test design | media/GIF | 12 GIF titles | [GRAPHICS_SOURCE_ROADMAP.md](GRAPHICS_SOURCE_ROADMAP.md) P0 row |
| zoekt/codesearch indexes | repeated manual grep across 122 checkouts | 1–4 hours per deep-dive wave | knowledge infra | 65 deep-inspected repos | [SEARCH_LEDGER.md](corpus/SEARCH_LEDGER.md) |
| S95 corrected capture harness | debugging "frozen" engine on a harness bug | 1–3 days (an engine rewrite was the wrong path) | verification | mini-tetris, minicraft + all future captures | [wave_c_determinism.json](evidence/s95/wave_c_determinism.json) |

**Aggregate honest statement:** across S94–S95 the source library demonstrably replaced
what would have been **weeks** of from-scratch graphics-semantics work (8 laws, ~1,200 LOC
implementation delta against 122 repos of reference material + 3,996 upstream test files).
No controlled baseline exists, therefore no precise hour count is claimed.

---

## 3. Source reuse map (Problem → source → implementation → test → MiniAndroid target)

```text
WRONG_COLOR  → AOSP VectorDrawable/AdaptiveIcon @1cdfff55 → vector_decode.c (933 LOC)
             → s95_vector battery fixture (9 checks)      → hotdeath/bouncy/urlchecker
WRONG_CLIP   → AOSP styles_material.xml @1cdfff55 → L-S95-BTNMIN-1 in view measure
             → real-APK layout dump (aapt2 xmltree)       → bobball/dodge
THEME-LESS   → AOSP themes_*.xml + colors_material.xml → L-S95-DEFTHEME-1/TXTCLR-1/ICONBTN-1
             → helloworld golden re-derivation (GATE H)   → simplestopwatch/gmdice
ANIMATION    → runtime interaction laws (R-NEW-*/F-117) → s95_capture.py corrected taps
             → x3 determinism protocol (S93 repeatability) → mini-tetris/minicraft
GIF (open)   → wuffs gif decoder (437 tests) → compositor rework → 12 GIF titles
WEIGHTS(open)→ AOSP LinearLayout.java → GFX-002 fix + fixture → dodge + weighted menus
NET (open)   → existing shadow API (NET-001) → real DNS/TCP/TLS/HTTP(S) → urlchecker first
MEDIA (open) → AOSP MediaPlayer/MediaCodec semantics + FFmpeg/GStreamer/SDL reference →
             → AUDIO-001 APK validation first; VIDEO-001 reuse matrix before any code
WEB (open)   → litehtml/WebKit/Servo study → WEB-001 decision doc (below) → SIMPLE BROWSER
```

---

## 4. Tool acceleration map (Tool → problem → expected time saved → affected corpus)

| Tool | Problem it accelerates | Expected time saved (range) | Affected corpus |
|---|---|---|---|
| `tools/source_lookup.py` | finding law + source per failure category | <1 h/investigation | every graphics investigation |
| `tools/verify_canonical_evidence.py` | canonical registry/SHA integrity | 4–8 h/wave | 148 titles |
| `tools/validate_control_system.py` | homepage/ticket/roadmap drift | 4–8 h/wave | control-system docs |
| `scripts/s95_capture.py` (+protocol law) | tap targeting + screenshot + ViewTree capture | 1–4 h/campaign | all interaction titles |
| `scripts/s92_run_battery.py` (99 stages) | regression detection before any claim | >1 day/wave avoided rework | whole engine |
| `s96_games_audit.py` (this wave) | executed-games evidence assembly + SHA cross-check | 4–8 h/wave | 23 artifact games + 64 trace-only |
| aapt2 `dump xmltree` | reading real APK layouts without decode code | <1 h/title | menu/layout investigations |
| zoekt/codesearch | symbol search over 122 checkouts | 1–4 h/deep-dive | 65 deep repos |
| `scripts/s95_fetch_p0_apks.py` / downloaders | SHA-verified corpus acquisition | <1 h/wave | corpus growth |

**Adoption bar (§12):** a tool enters this map only with setup cost, expected time
saved, applicable subsystems, reusable output, license, and maintenance cost
recorded. Tools that exist but were honestly NOT adopted (e.g. external runtime
surveys) stay labeled `AVAILABLE_NOT_USED` in [TOOL_UTILIZATION.md](compatibility/TOOL_UTILIZATION.md).

---

## 5. Corpus fan-out report (measured, law-level)

| Reusable law / family | Titles affected (measured) | Source of measurement |
|---|---|---|
| L-S95-VECTOR-1 / ADAPTIVE-1 (vector+adaptive decode) | 3 cleared; ~30 themed L1–L2 titles benefit | S95 before/after (11 APKs re-measured) |
| L-S95-BTNMIN-1 (48dip button minimum) | 2 cleared (bobball, dodge-a); menu-family wide | S95 §3 table |
| L-S95-DEFTHEME-1/TXTCLR-1/ICONBTN-1 | 1 cleared in part (simplestopwatch layers 1–3); gmdice regression fixed; all theme-less APKs | S95 §3 + worklog |
| Capture-protocol law (real touch targets) | 2 re-proven (mini-tetris, minicraft) + all future captures | wave_c_determinism.json |
| Class.forName Build-family bridge (F-NEW-160) | 9/50 titles hit the CNFE family | S84 A/B record |
| GIF disposal semantics (planned wuffs port) | 12 GIF titles + animated-drawable APKs | roadmap P0 row |
| LinearLayout weights (GFX-002, open) | dodge + weighted-layout family | S95 diagnosis |
| WebView readiness (open) | 83 WebView titles | S91 demand map |
| Compose runtime family (F-NEW-161, open) | nounours + Compose-chain titles | S84 record |

**Multi-app impact rule (§19):** every reusable semantic fix must be re-run against
≥5 corpus titles (10–25 for wide laws) with before/after/pass/fail/regression
recorded — the S95 battery pattern (11 titles × before/after + 3 controls) is the
template. A fix that works on one APK is not accepted.

---

## 6. Media reuse matrix (§15 — build the matrix BEFORE coding)

| Component | Candidate source | License | Reuse verdict | Need evidence |
|---|---|---|---|---|
| MediaPlayer/SoundPool/AudioTrack state machines (already IMPLEMENTED in engine) | in-engine codecs (S-era) + AOSP semantics | — | **Do NOT duplicate**; validate at APK level first (AUDIO-001) | audio engine exists; APK-level UNTESTED |
| Container/codec decode (video) | FFmpeg (LGPL/GPL overlay — configure carefully), GStreamer (LGPL), SDL_mixer (zlib), Media3/ExoPlayer (Apache-2.0, Java-layer) | mixed | ALGORITHM_PORT or process-isolated ADAPT; **size/build cost first**; Media3 needs ART-level Java runtime (large) | VIDEO-001 UNKNOWN; no real-APK video target yet |
| Image decode (already present) | engine decode_image_bytes + stb-class decoders | — | keep; extend via density laws | S95 measured |
| Test corpora | AOSP CTS media tests; ffmpeg FATE; gstreamer fixtures | various | TEST_ONLY | fixture plans |

First move: AUDIO-001 APK-level validation of the EXISTING engine (zero new code),
then decide video from real-APK demand — not from framework ambition.

---

## 7. Network plan (§16 — NET-001 is the P0)

- Do NOT build a giant stack. NET-001 (P0, OBSERVED): real HTTP(S) through the
  EXISTING shadow API surface — DNS → TCP → TLS → HTTP → redirects/headers/
  timeouts/response body/failure propagation.
- First real-APK validation target: **urlchecker** (already executed, GIF evidence,
  APP-0002 parent) — its core function is blocked exactly on real networking.
- Instrument everything (shadow-API tracking already DONE; extend to real socket paths).
- Reuse check before any new code: mature open-source TLS/HTTP client components
  (license + size + port cost) vs minimal socket implementation behind the existing
  API — decision recorded in the ticket before implementation.

---

## 8. Browser decision record (§17 — WEB-001; decision BEFORE implementation)

**Requirement (from the registered target):** SIMPLE BROWSER APK must run: URL entry,
HTTP(S) fetch, HTML parse, basic CSS, text/font render, images, links, scrolling,
page lifecycle. NOT a browser engine written from scratch.

| Candidate | Rendering/CSS scope | Size/deps | License (verify at adoption) | ADAPT fit |
|---|---|---|---|---|
| **litehtml** | HTML + CSS subset, images via callbacks, own layout — smallest complete fit | small, few deps | permissive (project states BSD-style — VERIFY before copy) | **leading ADAPT candidate**: port as a rendering backend behind a thin MiniAndroid View/Canvas layer |
| Chromium/WebView components | full fidelity | enormous | complex | NOT portable (REFERENCE_ONLY) |
| WebKit/Gecko/Servo | full engines | very large, Rust/C++ toolchains | mixed | NOT portable (REFERENCE_ONLY) |

**Decision:** proceed with a litehtml-ADAPT spike ONLY after NET-001 delivers real
HTTP(S); keep a written decision record (license file fetched + hash, size measured,
callback surface mapped) in the WEB-001 ticket before implementation starts.
This satisfies "decision document before implementation" without inventing license facts.

---

## 9. Execution-speed audit (§20 — measure first, then cache)

Measured/recorded loop costs (from existing run records; no new claims):

| Loop step | Current record | Where to cache/reuse (preferred order CACHE→REUSE→PARALLELIZE→STREAM→OPTIMIZE) |
|---|---|---|
| Cold build | binary built via `make -j` (92,296,064 B measured S95-CTRL recovery) | incremental toolchain targets already exist; do not optimize prematurely |
| APK acquisition | SHA-pinned downloaders + external cache (zero-APK-in-repo law) | cache EXISTS — reuse, don't rebuild |
| Source lookup | registry JSON in-memory; zoekt/codesearch indexes | already cached |
| Verification | 99-stage battery ≈ fast (rc=0 whole-gate runs recorded) | keep battery as the single gate; parallelize per-title captures when fan-out grows |
| Screenshot/semantic verify | S92/S93 verifier + goldens | golden cache EXISTS (2 documented re-derivations total) |

No correctness trade-offs: caches may only store DERIVED artifacts (goldens, indexes,
downloaded APKs), never verdicts.

---

## 10. Open-source advantage law (§22 — now CONSTITUTION §171)

> **When an APK is open source, its source code is primary behavioral evidence.**
> APK/DEX analysis remains necessary to verify the built artifact, but reverse
> engineering must not be the first path when authoritative source is available.
> Before substantial custom implementation, prove the chain:
> `SEARCHED → SOURCE FOUND/NOT FOUND → LICENSE CHECKED → REUSE DECISION →
> TEST/fixture identified → implementation justified`.

Reflected in: [MINIANDROID_CONTRIBUTING.md](MINIANDROID_CONTRIBUTING.md)
(source-first routing) and CONSTITUTION_V2 §171.

---

## 11. Next-wave queue (§23-G — prioritized by P0 → fan-out → reuse → APK impact → simplicity → testability → contributor accessibility)

| # | Item | Why here (measured justification) |
|---|---|---|
| 1 | **NET-001** real HTTP(S) behind existing shadow API; urlchecker as first real target | only P0; unblocks APP-0002 + WEB-001; high fan-out (network family) |
| 2 | **GFX-002** LinearLayout weight measure (law + fixture + multi-APK re-run) | ROOT_CAUSE_FOUND; dodge/bouncy visual residuals; weighted-layout fan-out |
| 3 | **GFX-001** programmatic UI color-scheme execution (onDraw dispatch + runtime setTextColor) | named P1 gap; simplestopwatch full pass blocked only on this |
| 4 | **GIF disposal port decision** (wuffs) for 12 GIF titles | biggest single measured visual fan-out (12 titles) with ready test corpus |
| 5 | **TEXT-001** Minikin/HarfBuzz wire-up (POC exists) | complex-script fan-out; upstream tests portable |
| 6 | **§29 promotion gate** for 7 candidate_* titles + per-game GitHub issues (audit follow-ups) | zero-runtime documentation debt from this audit |
| 7 | **AUDIO-001** APK-level audio validation (existing engine) | no new code; converts IMPLEMENTED → TESTED |
| 8 | **WEB-001 litehtml decision spike** (post-NET-001) | recorded decision before any browser code |

---

## 12. Validation

```text
python3 scripts/s96_games_audit.py        # executed-games machine index (SHA cross-checked)
python3 scripts/s96_gif_index.py          # GIF index regeneration
python3 tools/verify_canonical_evidence.py
python3 tools/validate_control_system.py
```
