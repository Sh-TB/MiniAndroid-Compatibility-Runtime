# EXECUTION_ACHIEVEMENTS — Canonical Record of Real APK Executions

> **SINGLE SOURCE OF TRUTH.** Every real APK execution MiniAndroid has achieved,
> verified, or honestly failed is recorded HERE — one entry per application.
> Supersedes `SCREENSHOT_INDEX.md`, `SCREENSHOT_INDEX_013.md`,
> `SCREENSHOT_INDEX_S51.md` (kept as era records with pointer notes) and any
> per-app achievement files.
>
> Status vocabulary (canonical, unchanged): `VERIFIED / PARTIAL / BLOCKED /
> NOT_TESTED` over the four evidence states `LOCAL / REMOTE / REMOTE HISTORY /
> GITHUB ATTACHMENTS`. Nothing is upgraded without runtime evidence.

## 0. Reading this file

| Field | Meaning |
|---|---|
| App | application (corpus APK or in-repo fixture) |
| Version | APK version (versionName / vc) |
| APK SHA256 | full SHA256 of the exact artifact; `-16` = first 16 hex chars |
| Source | F-Droid / telegram.org / in-repo fixture |
| Runtime HEAD | commit the verdict was produced at |
| Result | SUCCESS / PARTIAL / BLOCKED / FAIL (+ honest one-line reason) |
| Ladder | highest proven level of L0 recognized → L1 manifest → L2 DEX → L3 lifecycle → L4 UI machinery → L5 meaningful frame → L6 real input → L7 input→state change → L8 multiple interactions → L9 app-specific behavior (win/game-over) → L10 close/reopen persistence |
| Persistence | PERSISTENCE VERIFIED / NOT VERIFIED / PARTIAL (storage round-trip only) / NOT TESTED |
| Screenshot | only screenshots with real, recognizable UI; deterministic name, ≤100 KB JPG, SHA256 in `docs/evidence/s51_audit/SHA256SUMS` |
| ASC | what the ASC (Droid ASC, MG1937/ASC) reconnaissance added |
| Root cause | registry ID when known |
| Next action | the concrete next step |

Reproduce any run: `./build/miniandroid run <apk> -o /tmp/<dir>` at the recorded
HEAD (battery gate: `bash scripts/test/run_test_battery.sh` → "ALL PASS 92/92").

---

## 1. Master matrix — current-HEAD verdicts

Verdicts at HEAD `1b37afd1` (S51 all-front audit, runtime rebuilt from canonical
tree, battery 92/92) unless marked **[S52]** (this session, HEAD bf32dc93).
Shared-frame honesty: `31ddd4d5…` = deterministic blank Compose frame;
`eb16ab5c…` = deterministic default/entry screen. Identical SHAs across apps are
the signature of these two known render classes, not copy errors.

| # | App | Version | APK SHA256-16 | Source | Result | Ladder | Persistence |
|---|-----|---------|---------------|--------|--------|--------|-------------|
| 1 | Chess Clock | 2.11.2 (vc29) | `5ca6f2c54c05efe7` | F-Droid | **SUCCESS** | L7 + storage round-trip **[S52]** | PARTIAL (prefs round-trip; no persisted-state scenario) |
| 2 | uNote | 30 | `be91103f0e7db443` | F-Droid | **SUCCESS** (render) | L5; L6 blocked **[S52]** | PARTIAL (notes.db round-trip; input blocked) |
| 3 | Bouncy (ball) | 39 | (registry) | F-Droid | **SUCCESS** | L5 | NOT TESTED |
| 4 | Heading Calculator | 1 | `274ec873098eea51` | F-Droid | **SUCCESS** | L5 | NOT TESTED |
| 5 | Notes (billthefarmer) | 139 | `82cf8bc44c163748` | F-Droid | **SUCCESS** | L5 | NOT TESTED |
| 6 | MicroTimer | 8 | `79c6f730f64886e7` | F-Droid | **SUCCESS** | L5 | NOT TESTED |
| 7 | Simple Stopwatch | 26 | `b3ec1a5ec24ce53b` | F-Droid | **SUCCESS** | L5 | NOT TESTED |
| 8 | GM Dice | 8 | `1621eda11b5dbc0c` | F-Droid | **SUCCESS** | L5 | NOT TESTED |
| 9 | Simple Keyboard | 145 | `d83060833dc2bc97` | F-Droid | SUCCESS (entry screen — IME, no launch UI) | L5 (entry class `eb16ab5c…`) | NOT TESTED |
| 10 | RTTT (kirkezz) | 1.3 (vc3) | `704fa51869ad7ff4` | F-Droid | SUCCESS (entry screen; Compose frontier) | L5 (entry class) | NOT TESTED |
| 11 | Dooz v18 | 18 | `d81292cd346dcb23` | F-Droid | **PARTIAL** — R-NEW-361 signature reproduced | L3 (composition halt) | NOT TESTED |
| 12 | Dooz v23 | 23 | (corpus `io.github.yamin8000.dooz_23`) | F-Droid | **PARTIAL** — deterministic pipeline completion, blank first frame | L4 (blank `31ddd4d5…`) | NOT TESTED |
| 13 | TicTacToe (emmanuelmess) | 3 | `760fe5acf7b39435` | F-Droid | PARTIAL — blank first frame | L4 (blank class) | NOT TESTED |
| 14 | Telegram v12 | 12.10.1 (vc70389) | `f5e1192725772960` | telegram.org | **PARTIAL** — 540 s inside real init, no frame yet | L3-attempt (init depth) | NOT TESTED |
| 15 | WhatsApp | — | **NO APK** (0-byte placeholder in local cache) | — | **BLOCKED — APK unavailable** | — | — |
| 16 | Stopwatch (muellerma) | 6 | `3b6a10c8dc8ddc72` | F-Droid | PARTIAL — manifest has NO launchable Activity (QuickSettings Tile app) | L2 (by design) | — |
| 17 | BGClock | 2 | `72c140b0083ef273` | F-Droid | PARTIAL — WebView root (clock face is HTML/JS) | L4-minus (frame `2f85dd74…`) | NOT TESTED |
| 18 | TicTacToe (itsfrz) | 1.0.5 (vc5) | `2a057a9a519acd81` | F-Droid | PARTIAL — NPE at app boundary | L3 | NOT TESTED |
| 19 | Privacy Friendly Dicer | 2.0.0 (vc101) | `f2b4d3f021c3a620` | F-Droid | PARTIAL — ISE at app boundary | L3 | NOT TESTED |
| 20 | OpenLauncher | 39 | `b3320463a7a1ed46` | F-Droid | PARTIAL — heavy launcher, default screen | L5 (entry class) | NOT TESTED |
| 21 | Simple Flashlight | 66 | (corpus) | F-Droid | PARTIAL — app-boundary, default screen | L5 (entry class) | NOT TESTED |
| 22 | Antimine | 17.6.3 F (vc1706031) | `e7b635b6629bc5b0` | F-Droid | PARTIAL — killed at 300 s (no status line); registry: reaches MainActivity.onCreate | L3-attempt | NOT TESTED |
| 23 | Secuso Memory / Sudoku | 8 / 19 | (corpus) | F-Droid | PARTIAL — >300 s each, killed | L3-attempt | NOT TESTED |
| 24 | Secuso 2048 / Lexica | 1.4.2 / 3.13.1 | `02c799d3d582669d` / `255d26352ab1247c` | F-Droid | NOT re-run at S51/S52 — historical EXEC BUDGET TIMEOUT (540 s heavy) | L3-attempt | NOT TESTED |
| 25 | s36/s37 game corpus (solitaire, braincup, minesweepers ×3, word game, puzzle, dice overflow, roll, game2048, yahtzee dicer, droidify) | various | (corpus) | F-Droid | NOT re-run this session — campaign014/u011-era sheets stand | era records | NOT TESTED |
| 26 | Tiny Music Player | 1.0 | `d7bcb24d101b04be` | F-Droid | era record (campaign014) | era record | NOT TESTED |

**Count summary (current HEAD):** SUCCESS full-render 6 (+2 entry-class) ·
PARTIAL 14 · BLOCKED 1 (WhatsApp — no APK) · persistence storage-round-trip
verified 2 · meaningful-UI-frame apps 6.

## 2. In-repo fixture achievements (strongest ladder proofs)

| Fixture | What is proven | Ladder | Evidence |
|---|---|---|---|
| **tictactoe_golden** | 9 scripted taps, X→O→X chain, **win state detected**, pixel-deterministic replay | **L9** | battery §29 ("tictactoe_golden PASS, interaction 9/9") |
| **helloworld_golden** | 18-check golden render (typography, density) | L5 | battery §28 |
| **hello_widgets** | most advanced View-world render: ImageView drawable + EditText + Button + TableLayout 3 rows + RelativeLayout layout_below (2,059,104 non-white px golden) | L5 | S38/S39 records |
| **hello_smoke** | click → setText state change under LinearLayout | L7 | S38 record |
| **s38_shift_law** | androidx.collection ScatterMap long-arithmetic law probe (7 laws, 26 checks) | law probe | S38 record |
| EXT-01/02 HelloWorldSelfAware | external APK re-fetched + SHA-verified (`009b4671…`, `121d479c…`), typography 9 + interaction 12 checks | L7 | `docs/evidence/EXTERNAL_FIXTURE_HELLOWORLDSELFAWARE.md` |
| density_matrix / G06-G08 / M3 chain | toolchain fixtures, 3-run determinism, ARSC/style chain | — | battery 92/92 |
| F-0xx law chain | F-012/016/020/024/025/026/027/028/030/040/044/050/074 | — | battery 92/92 |

---

## 3. Per-app detail cards

### 3.1 SUCCESS — full render

**Chess Clock** `com.chessclock.android` v2.11.2 (vc29) · APK SHA256
`5ca6f2c54c05efe7…` (full in `miniandroid/APK_REGISTRY.json`) · Source F-Droid ·
Runtime HEAD `1b37afd1` (S51) + `bf32dc93` (S52)
- Lifecycle: launch→RESUMED real DEX execution, rc=0, 0 errors.
- UI: real clock-face render. Frame PNG SHA-16 `e4a2d7c90cd2fd26` (S51) —
  **re-exact-matched in S52 run 2** (cross-session determinism proven).
- Input **[S52]**: `--tap 540,900` consumed → final frame changed
  (`93c3121c…` ≠ base `e4a2d7c9…`) → **L6+L7 VERIFIED**.
- Persistence **[S52]**: with `--data-root` shared across close/reopen, the app
  created and RE-READ `com.chessclock.android/shared_prefs/default.xml`
  (package-scoped dir law R-NEW-367). Prefs map empty → no persisted visual
  state scenario driven → **PARTIAL** (storage round-trip VERIFIED; state
  persistence NOT VERIFIED).
- Screenshot: `docs/evidence/s51_audit/chessclock.jpg` (≤100 KB, SHA256SUMS).
- ASC: manifest decode 294 ms (`.ChessClock` launcher, `.Prefs`, max_aspect
  2.1, minSdk 21/target 25) + `getclass` on ChessClock (BRONSTEIN/FISCHER delay
  modes, TICK_LENGTH, P1/P2 click handlers).
- Next: drive a prefs-changing interaction (menu → settings) → PERSISTENCE VERIFIED upgrade.

**uNote** `app.varlorg.unote` v30 · APK SHA256 `be91103f0e7db443…` · F-Droid ·
HEAD `1b37afd1` + `bf32dc93`
- Lifecycle: launch→RESUMED, rc=0, 0 errors.
- UI: real texts rendered (`Add note` / `Search` / `Quit` Buttons,
  `Ignore case` / `Search in content` CheckBoxes, view_ids 13/14/15/22/23).
- Persistence **[S52]**: created `app.varlorg.unote/databases/notes.db`
  (SQLite) under shared `--data-root`; file survives close/reopen → storage
  round-trip VERIFIED.
- Input **[S52]**: **BLOCKED — R-NEW-368**: 16 tap probes on a grid
  (x∈{270,540,810,940} × y∈{300…1780}) ALL return "no touch target",
  target_view_id=0; frames byte-identical (`7b30d52201bb22ac…`). Paint path and
  touch-hit path disagree on geometry → L6 unreachable. Registered
  `R-NEW-368` (OBSERVED-FAIL, P1).
- Screenshot: `docs/evidence/s51_audit/unote.jpg`.
- ASC: manifest + class recon of NoteMain activity family.
- Next: verbose run → ViewShadow bounds for ids 13-15 → paint-vs-touch rect divergence.

**Bouncy / Heading Calculator / Notes (billthefarmer) / MicroTimer / Simple
Stopwatch / GM Dice** — all SUCCESS rc=0 full runs at HEAD `1b37afd1` with
deterministic frame SHAs (`4219c511…`, `293b6761…`, `ae697935…`,
`c51269309cd14594`, simplestopwatch + gmdice per battery hashes); screenshots in
the s51_audit gallery. Ladder L5. Persistence NOT TESTED (next-session ladder
work). Input: gmdice/simplestopwatch have battery-level interaction coverage;
others not yet driven.

### 3.2 Entry-class SUCCESS (default screen rendered; no app-specific UI beyond it)

**Simple Keyboard** (`rkr.simplekeyboard.inputmethod` v145): IME — correctly
renders its entry/settings surface only; full IME experience requires the
input-method service stack (documented boundary). **RTTT** (Compose frontier,
entry class). **OpenLauncher** (heavy launcher, entry class). **Simple
Flashlight** (app-boundary). Shared deterministic frame `eb16ab5c…`.

### 3.3 PARTIAL — open roots (the honest frontier)

**Dooz v18** `io.github.yamin8000.dooz` v18 · APK SHA256
`d81292cd346dcb23b04488bca400ca95af0f6eaa4aefefd31f847fe535cbdc17` · F-Droid
- Result: **PARTIAL** — `[HALT-LOOP] Lh/r;.c PC=0x1c 50001 visits` +
  `aput-oob length=7 index=613985991 LP/v$a;.c pc=28` reproduced at HEAD.
- Root cause: **R-NEW-361 (OBSERVED-FAIL, P0)** — androidx.collection
  ScatterMap.set group-scan long-metadata arithmetic.
- ASC **[S52]**: `getclass Lh/r;` decompiled in seconds → the FULL set() loop is
  now visible: growth-metadata sentinel writes (`254` tombstone / empty), group
  mask `-9187201950435737472`, hash multiplier `-862048943` + `<<16`/
  `>>7`, probe stride `v7_4 += 8` with `& capacity-mask` wrap, and
  `Long.numberOfTrailingZeros` slot resolution. Root-cause candidate set (all
  engine-law checkable): (a) long-shift sentinel write, (b) mask-wrap of probe
  index, (c) numberOfTrailingZeros, (d) `h.x.c` capacity normalization. This
  decompilation is the direct input for the next law probe fixture.
- Evidence: `local/asc_out/dooz18_hr.java` (LOCAL-ONLY, untracked — ASC output
  never committed); excerpt recorded in `docs/evidence/s52_asc/R-NEW-361_SCATTERMAP.md`.
- Next: build the probe fixture for candidates (a)-(d).

**Dooz v23** (`io.github.yamin8000.dooz_23`, corpus) — deterministic pipeline
completion; first frame = blank Compose class `31ddd4d5…` (identical ×4+ runs,
S41→S51). F-016 honesty now surfaces 1 uncaught in-flight exception (7 unwind
entries = R-NEW-344 refined chain — accounting change, not behavior regression).
Root: **R-NEW-344** (Recomposer suspends without re-posting frame callback).
Blank frame is NOT an achievement; first *meaningful* frame is the goal.
Next: recomposer post-resume pump law.

**Telegram v12** `org.telegram.messenger` 12.10.1 (vc70389 universal) · APK
SHA256 `f5e1192725772960…` · telegram.org
- Result: **PARTIAL** — 540 s budget consumed INSIDE real init (989k log lines,
  androidx SafeIterableMap cycle-stub ≥18k calls, 400 REC-MISS); no frame yet
  at S51 HEAD. Historical golden login-stall frame `088ea640…` (41,233 px)
  stands at its recorded campaign HEAD.
- ASC **[S52]** (milliseconds vs 540 s runtime): manifest decoded from the
  73 MB APK in 319 ms → `ApplicationLoaderImpl` (application) + `LaunchActivity`
  (MAIN). `ApplicationLoader.onCreate` startup path fully mapped: static
  `applicationContext` init → `getSystemService("connectivity")` →
  `getFilesDir()/dataDir` → `registerReceiver` (CONNECTIVITY_CHANGE,
  ScreenReceiver) → **`NativeLoader.initNativeLibs`** (native .so loading —
  engine has no native-lib loader: known boundary) → `SharedConfig.loadConfig()`
  → `SharedPrefsHelper.init` → push/`"__NO_GOOGLE_PLAY_SERVICES__"` →
  location/maps providers. `findrefs type SafeIterableMap` cross-checks the
  runtime observation: consumed by `androidx.lifecycle.LiveData.<init>` +
  `SavedStateRegistry.<init>` — the init-time observer registration storm.
- Root-cause targets ranked: (1) REC-MISS surface along the ApplicationLoader
  static-init chain; (2) SafeIterableMap iterator-stub cycle law; (3)
  NativeLoader boundary decision (stub vs skip).
- Evidence: `docs/evidence/s52_asc/TELEGRAM_STARTUP.md` (compact card);
  decompiled sources LOCAL-ONLY.

**WhatsApp** — **BLOCKED — APK unavailable.** The only local file is a
**0-byte placeholder** (`real_apps/WhatsApp.apk`, SHA256 =
`e3b0c442…b855` = SHA256 of the empty string; same for the local
`Signal.apk`). No fake evidence. Historical u011_3 probe evidence (entry chain
+ typed catches + `LX/0F7` stall) stands at its recorded HEAD. Next: obtain a
real APK externally, register it in APK_REGISTRY.json, then and only then run.

**TicTacToe (emmanuelmess)** v3 — blank first frame (Compose/libGDX family,
frame class `31ddd4d5…`). **BGClock** v2 — WebView root boundary, frame
`2f85dd74aa54e463` EXACT u013 match. **muellerma Stopwatch** v6 — manifest
proves NO launchable Activity (QuickSettings Tile service app): ladder stops at
L2 by design, not by engine failure. **itsfrz TicTacToe** (NPE at app boundary),
**Privacy Friendly Dicer** (ISE at app boundary). **Antimine / Secuso memory /
sudoku** — >300 s kills, no first frame this session; registry standings stand.

## 4. Persistence testing (S52 experiment, section-14 protocol)

Method: two runs with the SAME `--data-root` (Android `/data/data` analog),
run 1 with one canonical tap, run 2 fresh; compare data-root tree + frames.

| App | data-root artifact | Survives reopen? | State delta observable? | Verdict |
|---|---|---|---|---|
| Chess Clock | `com.chessclock.android/shared_prefs/default.xml` | YES | no (empty prefs map; tap state in-memory by design) | **PARTIAL** — storage round-trip VERIFIED |
| uNote | `app.varlorg.unote/databases/notes.db` | YES | no — input blocked (R-NEW-368) | **PARTIAL** — storage round-trip VERIFIED |

Discipline: no persistence claim is inferred from the mere existence of storage
APIs; both verdicts are bounded to what was observed. Full ladder (add note →
close → reopen → note visible) requires R-NEW-368 fixed first.

## 5. ASC reconnaissance ledger (S52)

Tool: **Droid ASC (MG1937/ASC)** v0.1.1.post1 @ `3279d9dd6ffb9c844f8599bd2bf69a13bb602480`,
installed into a LOCAL venv (`local/ASC/venv`, gitignored). ASC is a
reconnaissance helper ONLY — never a substitute for MiniAndroid runtime
evidence; no ASC output (decompiled sources, indexes) is committed; each claim
is cross-checked against runtime observations.

| Query | Target | Time | Outcome |
|---|---|---|---|
| `getmanifest` | chessclock vc29 | 0.29 s | launcher + Prefs + sdk levels — matched runtime render |
| `listclass --prefix` / `getclass` | chessclock | ms | ChessClock fields/handlers recon |
| `findrefs field/string` | chessclock | ms | validated ref-search semantics |
| `getmanifest` | Telegram v12 (73 MB) | **0.32 s** | ApplicationLoaderImpl + LaunchActivity |
| `getclass` ×2 | ApplicationLoader(+Impl) | s | full startup-path law list (see §3.3) |
| `findrefs type` | SafeIterableMap | s | LiveData/SavedStateRegistry consumers — matches S51 runtime cycle-stub observation |
| `getclass` | Dooz18 `Lh/r;` | s | ScatterMap.set loop → R-NEW-361 candidate set |
| `getmanifest` | WhatsApp placeholder | — | exposed 0-byte file → BLOCKED made PROVABLE |

Where ASC helped: manifest/startup recon in milliseconds on a 73 MB APK that
cost 540 s in runtime; precise decompile of the single root-suspect class for
R-NEW-361; honest WhatsApp BLOCKED proof. Where it did not: Compose
Recomposer suspension (R-NEW-344) is engine-machinery, not bytecode-recon —
recorded as "not useful there" and skipped.

Compact evidence cards: `docs/evidence/s52_asc/`. Raw decompiled files stay
LOCAL-ONLY (`local/asc_out/`, gitignored).

## 6. Screenshot policy (binding)

A screenshot may be committed only if: real recognizable UI · proves something
text alone cannot · linked to an entry above · SHA256 recorded · deterministic
name · ≤100 KB JPG. Blank/white/black frames are NEVER committed as images —
they are recorded as text (`blank-frame observed`, class `31ddd4d5…` /
`eb16ab5c…`) exactly as done above. Current gallery:
`docs/evidence/s51_audit/*.jpg` + `SHA256SUMS` (17 curated files). No gallery
is generated for its own sake.

## 7. Historical records (superseded pointers)

- `docs/evidence/SCREENSHOT_INDEX_S51.md` — S51 all-front audit era (verdicts
  absorbed into §1/§3 above).
- `docs/evidence/SCREENSHOT_INDEX.md`, `SCREENSHOT_INDEX_013.md` — §39 /
  campaign-013 era galleries.
- `docs/evidence/campaign014/`, `master_campaign/`, `m3_campaign/`, `g09_corpus/`,
  `u013/` — era evidence trees (raw traces removed from tree per S52 residue
  record; recoverable from git history; SHA256 recorded).
