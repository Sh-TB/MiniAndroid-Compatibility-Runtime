# S87 PHASE 0–3 AUDIT REPORT — Achievement & Evidence Census

**Generated:** 2026-09-23 · HEAD `2a86a3eb` (S86) · branch `main` · working tree clean
**Method:** `scripts/s87_inventory.py` → `docs/audit/S87_INVENTORY.json` (machine-readable, every number below is computed, none guessed)
**Rule honored:** COUNT → MAP → CLASSIFY → SHOW THE REAL STATE *before* any structural change. Nothing was deleted in this phase.

---

## 1. TITLE INVENTORY (from `docs/evidence/canonical/registry.json` — the SSoT)

| Metric | Value |
|---|---|
| Total records | **148** |
| Unique packages | **148** (duplicate packages: **0**) |
| Games / Apps / Fixture | 87 / 60 / 1 |
| With canonical artifact (visual) | **36** (12 GIF + 24 JPG) |
| Text-only honest records (S54 gate, no artifact) | 112 |
| With APK SHA256 pinned | 102 |
| With source/upstream link | 126 |
| Records missing achievement text (`proven`) | 0 |
| **Executed but not recorded** | **0** (every executed package found in evidence filenames is registered) |
| **Recorded but never executed** | **0** (all 148 have a session + stage record) |
| Stale evidence (registry SHA ≠ disk SHA) | **0**; `SHA256SUMS` 36/36 verified OK |

### Status & level distribution

| Status | Count | | Level | Count |
|---|---:|---|---|---:|
| OBSERVED | 112 | | L0 | 15 |
| VERIFIED | 22 | | L1 | 82 |
| VERIFIED-INTERACTIVE | 12 | | L2 | 37 |
| PARTIAL | 2 | | L3 | 5 |
| | | | L5 | 3 |
| Flags: launched 123 · rendered 129 · interacted 13 · state_changed 12 | | | L6 | 2 |
| | | | L9/L10 | 4 |

### OBSERVED = 112 decomposed by root-cause family (the real frontier)

| Family | Count | Root cause |
|---|---:|---|
| **near-blank engine-default shell class** | **58** | **UNSOLVED as a family** — the dominant frontier |
| compose internals (F-NEW-161) | 41 | OPEN, upstream-gated |
| androidx adapter fallback (F-NEW-162) | 12 | OPEN, upstream-gated |
| Telegram static-init chain | 1 | specific divergence recorded (S85) |

**Family clusters inside the 58** (fan-out targets): secuso PrivacyFriendly scaffold ×8, solitaire family ×5, sidhant games ×3, clocks/apps ×4, SDL/native engines (surge, thextech, sgtpuzzles, aaaaxy) ×4, remaining singles.

---

## 2. IMAGE CENSUS (repository-wide, `.git` excluded)

| Format | Count | Bytes |
|---|---:|---:|
| PNG | 266 | 5.36 MB |
| JPG | 215 | 8.00 MB |
| GIF | 20 | 5.46 MB |
| WebP | 10 | 1.82 MB |
| **Total** | **511** | **20.7 MB** |

- **Exact duplicates by SHA256: 21 groups (4.52 MB wasted)**
  - 18 groups live in `skills/design/design-templates/` — pre-existing design-skill assets, **not project evidence** (untouched).
  - **3 groups are project-relevant:** `canonical/com.miniandroid.tetris.gif` == `s80/tetris_gameplay.gif`, `canonical/com.miniandroid.g2048.gif` == `s80/g2048_gameplay.gif`, `canonical/com.miniandroid.snakedeluxe.gif` == `s80/snake_gameplay.gif` (2.19 MB). The canonical files are byte-identical copies of the S80 session originals. Session originals are referenced by `S80_REPORT` and kept as execution evidence; canonical dir itself contains **zero internal duplicates**.
- **Near-duplicates (16×16 ahash, hamming ≤ 8): 88 groups** — dominated by the engine-default shell class frames (by design near-identical; already gated by the S54/S85 near-blank laws, never shipped as per-title achievements).
- **Orphan images (referenced nowhere in md/json/py/html): 39** — benign: s80 `*_frame_a/b/c.jpg` (superseded by the canonical GIFs), spotlight/session PNGs, upstream source-tree assets (FishRings mipmaps, Dooz screenshots), fixture resources, `docs/runtime/knowledge/run-assets/`, and a legacy nested tree `miniandroid/docs/evidence/apps_ledger/`.
- **Multi-referenced images: 334** (mostly referenced by both an index and a report — expected).
- **GIF frame counts (canonical):** snakedeluxe 49 · g2048 65 · tetris 75 · dodge 14 · minicraft 15 · tictactoedeluxe 4 · bouncy/bobball/urlchecker/nounours/hotdeath 2–3 · tictactoe(classic) 3.

---

## 3. DIRECTORY CENSUS (evidence-relevant)

| Path | Files | Size | Images | Role |
|---|---:|---:|---:|---|
| `docs/evidence/` (whole) | 1251 | 19.94 MB | 278 | session evidence tree |
| ─ `docs/evidence/canonical/` | 38 | 3.32 MB | 36 | **canonical achievements (ONE per title) + registry.json + SHA256SUMS** |
| ─ `docs/evidence/s80` | 16 | 2.49 MB | 12 | S80 games session (GIF originals) |
| ─ `docs/evidence/foundation` | 435 | 1.51 MB | 27 | foundation fixture evidence |
| ─ 60+ session dirs `sNN_*` | ~700 | ~10 MB | ~200 | per-session evidence (logs, JPGs ≤100KB, SHA256SUMS) |
| `upload/` | 549 | 18.56 MB | 0 | user uploads + pinned APK build outputs (no images) |
| `upstream/` | 1642 | 16.08 MB | 97 | upstream source trees (incl. their own assets) |
| `docs/upstream/` | 100 | 1.32 MB | 0 | curated upstream law files (SHA-pinned) |
| `docs/history/` | 93 | 0.59 MB | 4 | wave-history archive |
| `docs/compatibility/` | 55 | 0.21 MB | 0 | older matrices |
| `run/` | 3 | 0.02 MB | 0 | transient run dir (s83b only) |
| root `evidence/` | 7 | 0.03 MB | 0 | cleanup ledger only |

Conclusion: **no screenshot explosion exists** — 20.7 MB total, canonical layer only 3.32 MB. The S84 cleanup already removed 345 MB of raw dumps.

---

## 4. REGISTRY SYSTEMS (PHASE 3 — who is the real "achievement source"?)

| File | Records | Unique titles | Purpose | Canonical? |
|---|---:|---:|---|---|
| **`docs/evidence/canonical/registry.json`** | **148** | **148** | per-title machine registry (wave, law, artifact, SHA, flags, root cause) | **YES — Single Source of Truth** |
| `docs/ACHIEVEMENTS.md` | 148 | 148 | human-readable one-record-per-title page | derived (generated) |
| `docs/evidence/CANONICAL_SCREENSHOTS.md` | 148 | 148 | machine-checkable index table | derived (generated) |
| `docs/EXECUTION_ACHIEVEMENTS.md` | 0 | 0 | S54 superseded pointer, 14 lines | NO (marked superseded) |
| `root_registry.json` | 420 | n/a (R-NEW-*) | **runtime root-cause registry — different axis, not titles** | YES (its own axis) |
| `docs/evidence/SCREENSHOT_INDEX.md` | 19 | ? | legacy screenshot index (S-era) | NO — stale parallel |
| `docs/evidence/SCREENSHOT_INDEX_013.md` | 14 | ? | legacy | NO — stale parallel |
| `docs/evidence/SCREENSHOT_INDEX_S51.md` | 33 | ? | legacy | NO — stale parallel |
| `docs/evidence/CURRENT_COMPATIBILITY_MATRIX.md` | 32 | ? | older compatibility matrix | NO — stale parallel |
| `docs/compatibility/APP_COMPATIBILITY_REGISTRY.md` | 43 | ? | older compat registry | NO — legacy |
| `docs/compatibility/EXECUTION_MATRIX.md` | 17 | ? | older execution matrix | NO — legacy |
| `docs/compatibility/COMPATIBILITY_CLOSURE_MATRIX.md` | 20 | ? | older closure matrix | NO — legacy |

**Answer to PHASE 3:** the Single Source of Truth **exists and is already enforced**: `registry.json` → (generator) → `ACHIEVEMENTS.md` + `CANONICAL_SCREENSHOTS.md` + README stats, checked by `tools/verify_canonical_evidence.py` (ALL CHECKS PASS at audit time; WARNs are honest artifact-less records only).

---

## 5. PROBLEMS FOUND (real, ranked)

1. **58-title near-blank shell family is unsolved as a family** — the largest honest gap; clustered upstream families (secuso ×8, solitaire ×5) suggest 2–3 shared root causes with large fan-out.
2. **5 stale parallel index/matrix files** (`SCREENSHOT_INDEX*.md` ×3, `CURRENT_COMPATIBILITY_MATRIX.md`, plus legacy `docs/compatibility/*`) can drift and mislead; they are not generated and not validated.
3. **3 byte-identical GIF copies** (canonical == s80 originals, 2.19 MB) — documented, not deleted (session originals are referenced by S80_REPORT; canonical layer itself is clean).
4. **39 orphan images** — all benign (session frames, upstream assets, fixtures); a legacy nested tree `miniandroid/docs/` adds confusion.
5. **`root_registry.json` internal drift:** `summary.total_roots=412` vs actual `roots[]=420` (S79-era summary not regenerated) — cosmetic but worth fixing in a later wave.
6. Titles without source link: 22 (mostly legacy in-house/fixture records).

## 6. PROPOSED STANDARD (PHASE 4 verdict)

The structure the taskbook proposes **already exists since S84 and is validated**:

```text
README.md (generated landing stats + hero)
    ↓
docs/ACHIEVEMENTS.md            (one record per title, generated)
    ↓
docs/evidence/CANONICAL_SCREENSHOTS.md (index, generated)
    ↓
docs/evidence/canonical/        (ONE artifact per title + SHA256SUMS + registry.json = SSoT)
```

**Decision: keep this structure. Do not rebuild.** Required maintenance actions only (PHASE 5/14, minimal & reversible):
- add `SUPERSEDED → docs/ACHIEVEMENTS.md` banner headers to the 5 stale parallel files (no deletion of content/history);
- regenerate `root_registry.json` summary block in a later wave;
- no image deletion warranted by data (all duplicates/orphans are either non-evidence, referenced, or gated).

## 7. ONE TITLE = ONE CANONICAL (PHASE 5 verdict)

Verified: 148 records → 36 artifacts, each record ≤1 artifact, canonical dir has **zero internal duplicates**, every artifact SHA-pinned in both `SHA256SUMS` and the registry, validator enforces R1–R12. Debug/session evidence (frames, near-blank classes, spotlight probes) remains in session dirs — separated from achievements by law.

## 8. S87 EXECUTION PLAN (PHASE 6–10, source-first)

Corpus selection strategy (not yet executed at time of writing — executed in the remainder of this wave):
1. **Source-first probes into the 58-title near-blank family**, prioritizing upstream-clustered targets: `org.secuso.privacyfriendly*` (×8 fan-out), `de.tobiasbielefeld.solitaire` + solitaire family (×5), `com.sidhant.*` (×3), plus SDL/native engines and one text-heavy app.
2. For each: fetch upstream source → identify entry Activity, layout XMLs, rendering tech, expected first screen (visual spec) → execute APK at HEAD → **SOURCE-expectation vs screenshot semantic table** → first-divergence trace → new F-NEW law with fan-out, A/B-proven, regression-gated (battery 26/26 + golden ladder).
3. Render-family coverage requirement honored via existing corpus + new picks (Canvas/onDraw, SurfaceView, XML drawables, text-heavy, image-heavy, compose/libGDX frontiers as controls).

---

# S87 EXECUTION RESULTS (PHASE 6–9 — appended post-execution)

## Corpus

10 titles (all inside the 148-record registry), selected to hit the
unsolved near-blank family with upstream clustering: secuso pfacore ×2
(dame/2048 — family ×8), solitaire family, sidhant family, veldsoft
control (3 siblings render), classic View chess, Kotlin sudoku, text-heavy
NewsBlur, libGDX Halma, WebView-first MyKanji. APKs: F-Droid, SHA256
recorded; 3/3 pins that exist match exactly (dame 41727c01…, 2048
02c799d3…, mykanji b20274a0…). Upstream sources fetched and read BEFORE
execution (PHASE 6 law): SecUSo/privacy-friendly-dame,
SecUSo/privacy-friendly-2048, TobiasBielefeld/Simple-Solitaire,
jcarolus/android-chess, VelbazhdSoftwareLLC/No-Thanks-for-Android,
Galaxy-rio/SudokuYou, Crazy-Marvin/Halma.

## SOURCE EXPECTATION vs SCREENSHOT (semantic tables, per probe)

| Title | Source says (expected first screen) | MiniAndroid at S87 HEAD | Verdict |
|---|---|---|---|
| secuso dame | SplashActivity → routes → TutorialActivity (ViewPager page: icon + label + SeekBar + Skip/Next) | real navigation happened; Tutorial inflated (6 views); Skip/Next painted (uniq 213); pager page text/icon missing | STRUCTURE PASS, content FAIL (text) |
| secuso 2048 | Splash → (FirstLaunch) Tutorial, same pfacore scaffold | tutorial screen painted (uniq 160, Skip visible); dies later in Glide engine loop | STRUCTURE PASS, then HALT (Glide, open) |
| mykanji | MainActivity builds LinearLayout hosting a full-screen WebView over local HTML | LinearLayout→WebView tree inflates; WebView content blank | STRUCTURE PASS, content FAIL (WebView assets) |
| no.thanks | Splash → menu (ConstraintLayout) | ConstraintLayout→WebView tree inflates; savedstate adapter CNFE + TypedArray null | STRUCTURE PASS, blocked by F-NEW-175 |
| Simple-Solitaire | GameActivity over support-lib v7 | support chain NPEs (Context.getResources / Window.getCallback on null) | FAIL (f141 family, open) |
| android-chess | ChessBoardView (plain onDraw Canvas board) | clinit TypedArray/Field nulls before the board ever inflates | FAIL (F-NEW-175, open) |
| SudokuYou | Kotlin app, XML UI | kotlin-reflect ReflectionFactoryImpl CNFE | FAIL (FORNAME family, open) |
| NewsBlur | feed list (SQLite-backed) | Cursor.moveToNext on null (query path) | FAIL (SQLite, open) |
| Halma | libGDX AndroidInput lifecycle | AndroidInput.onResume on null receiver | FAIL (F-NEW-157 GL frontier, reconfirmed) |
| BubbleShooter | SurfaceView game | zero exceptions, zero nodes, silent blank | FAIL (unlocalized — honest open) |

## FIRST DIVERGENCES → ROOT CAUSES (PHASE 9)

The first divergence for 4 of 10 probes was the SAME engine bug chain,
now A/B-proven and fixed at HEAD (see
[ROOT_CAUSE_REGISTRY.md](../evidence/ROOT_CAUSE_REGISTRY.md)
F-NEW-171..174): **uint32 recursion-depth underflow in the S83 APXACT
intercepts** (wrapped 0xFFFFFFFF → recursion guard killed every frame →
engine-default blank shell), masked second-layer FragmentActivity
super-chain NPEs, missing ViewConfiguration object law, and the
beneath-finisher destroy-the-wrong-activity law. Visual impact:
dame uniq 2 → 213, 2048 uniq 2 → 160 (real painted UI structures for the
first time); regression gates unchanged (battery 26/26, ladder 10/10 with
pixel checks, S83-B2 2/2).

Open families registered honestly: F-NEW-175 (TypedArray null, 2-title
fan-out observed) + per-title next-divergence ledger (Glide, WebView
assets, kotlin-reflect, SQLite cursor, libGDX, one unlocalized).

## Verdict

The near-blank family is no longer a monolith: it decomposes into one
fixed 4-law cluster + 6 named open frontiers, each with a first
divergence signature and a source-read explanation. Every number in this
report is machine-checkable in `S87_INVENTORY.json`, `EXEC_RESULTS.json`,
`DIVERGENCE.json` and the canonical validator (ALL CHECKS PASS).
