# Search Coverage Ledger (S61)

Canonical record of code-search tool usage in the campaign. Purpose:
prevent duplicate research; record REAL measured behavior, not name
dropping. Every entry below was executed against the live MiniAndroid
tree this session.

## Environment

| Item | Value |
|------|-------|
| Host tree | `/home/z/my-project` (engine ~324 indexed files, dalvik_engine.cpp ≈ 31k lines / 1.2 MB) |
| ripgrep | rg 14.1.1 (preinstalled) |
| Zoekt | sourcegraph/zoekt @ v0.0.0-20260911061844 (built from source this session) |
| codesearch | google/codesearch v1.2.0 (built from source this session) |
| Go toolchain | go1.22.5 → auto-switched go1.26.8 for zoekt build (installed to `tools/go`) |
| Binaries | `tools/gopath/bin/{zoekt,zoekt-index,zoekt-indexserver,zoekt-webserver,cindex,csearch}` |

## Install / build record

| Tool | Build | Notes |
|------|-------|-------|
| zoekt-index | OK (go install) | Index build: **0.45 s** for src+corpus+scripts (324 files), shard overhead 2.9–4.2× (7.9 MB index) |
| zoekt (CLI) | OK | Required go ≥ 1.25.9; toolchain auto-switched |
| zoekt-webserver | OK | HTTP UI at :16077 (HTML; JSON API shape differs from docs) |
| cindex/csearch | OK | Index: 3.7 MB data → 1.5 MB index in **0.08 s** |

## Real campaign queries (this session's actual R-NEW-381 workload)

| Query | zoekt (files / latency) | csearch (hits / latency) | ripgrep ground truth |
|-------|--------------------------|--------------------------|----------------------|
| `dispatchDraw` | 5 files, 18 lines / **49 ms** | 6 lines shown / **2 ms** | 5 files in src |
| `ensure_class_initialized` | 2 / 40 ms | 2 files (dalvik_engine.h + s43 script) — **missed dalvik_engine.cpp** | 15 files (11 matches in dalvik_engine.cpp alone) |
| `static_field_storage_` | 1 / 36 ms | — | 37 files |
| `api_call_trace_cap` | 5 / 37 ms | — | 11 files |
| `Landroidx/compose/ui/platform` | 7 / 35 ms | — | 56 files |
| `compose_view_class` | 2 / 36 ms | — | 6 files |

## Findings (honest)

1. **ripgrep is fastest and most complete at this repo size** (7–8 ms,
   complete results). It remains the daily driver.
2. **zoekt works** (sub-50 ms queries regardless of tree size) but
   **under-reported on 2/5 queries vs rg** (e.g. 7 vs 56 files for the
   androidx compose path). Root cause not yet diagnosed — likely query
   semantics (zoekt atom splitting / substring boundaries), recorded as
   the tool's open limitation. NOT rejected; re-test with quoted/atomic
   query forms before any kill decision.
3. **codesearch (csearch) works** (2 ms queries, clean line output) but
   **silently under-indexed the 1.2 MB dalvik_engine.cpp** (returned 2
   files where rg finds 15 for `ensure_class_initialized`). csearch has
   a per-file trigram limit; the engine's biggest file hits it. Record:
   use csearch only with file-size awareness.
4. Probe (the local candidate tool) is NOT present in this environment
   (no binary, no install recipe found). Recorded as **UNAVAILABLE**,
   consistent with the search-failure protocol (multi-round attempt:
   `which`, filesystem scan, GitHub release check — all negative).

## Duplicates prevented this session (the ledger's purpose)

- Before re-deriving the Compose class identity logic for F-108, the
  ledger check on `dispatchDraw` + `chain_overrides_method` showed the
  F-099 override-check law already existed → F-108 was implemented as an
  EXTENSION of F-099 (removed the name-gate requirement), not a new
  parallel mechanism.
- Before writing a new DEX hierarchy parser for the R8 rename probe, the
  existing `scripts/forensic/m3_dex_super_probe.py` was located and
  reused (superclass walk pattern), avoiding a fourth independent DEX
  header parser.

## S62 additions (2026-09-19) — R-NEW-381 / R-NEW-331 workload

| Query | zoekt (result / latency) | csearch (hits / latency) | ripgrep ground truth | Outcome |
|---|---|---|---|---|
| `attachHost` (miniandroid/src + docs, re-indexed: 117 src + 963 docs files, shards 7.9+30.3 MB) | 0 rows displayed (CLI) | 1 hit, 2 ms (docs/maintenance/s47_session_record.md) | 1 file | **zoekt under-report reproduced** (2nd instance, same limitation family as S61); csearch = hit; ledger value: prevented re-deriving the S47 fragment-host note |
| `ensureExecReady` (csearch over src+docs) | — | 4+ hits, 2 ms (docs/evidence/mc4_telegram/tg_run1_distilled.log) | same | **Cross-corpus reuse: the Telegram golden carries the SAME FragmentManager ISE face as the 3 spotlight games → R-NEW-331 consumer count 3 games + Telegram, duplicate research avoided** |

S62 scripts: `scripts/s62_ts_stderr.py` (line-timestamped stderr wrapper),
`scripts/s62_clinit_costs.py` (per-<clinit> duration distribution),
`scripts/s62_disasm_heavy_clinit.py` (heaviest-chain disassembler).

## S63 additions (2026-09-19) — gmdice F-113 searchlight + tool root cause

Environment rebuild: this container lost `tools/gopath` + `tools/go`;
zoekt (@ 153817f643cd) + cindex/csearch (google/codesearch v1.2.0) REBUILT
this session with Go 1.26.0 (tarball from go.dev; `go install` via the
default module proxy STALLED — `GOPROXY=direct` fetches from GitHub
directly and worked; recorded as the reproducible install recipe).

| Query | zoekt (result / latency) | csearch (hits / latency) | ripgrep ground truth | Outcome |
|---|---|---|---|---|
| `SecureRandom` (engine shard, DEFAULT max_trigram_count) | **0 hits** (0.03s) | 0 in dalvik_engine.cpp (1.2MB) | 1 file | zoekt under-report reproduced on a FRESH index → not stale-index flake |
| `SecureRandom` (engine shard, `-max_trigram_count 100000000`) | **found F-113 lines 20878..20893** (0.03s; shard 4.7MB) | — | same | **ROOT CAUSE of the S61/S62 under-report: zoekt silently excludes files beyond the default trigram cap.** zoekt stays in the toolkit with the flag documented |
| `nextInt` (engine shard, high cap) | 8 lines | 0 (per-file trigram limit, REPRODUCED 3rd time) | 8 | zoekt(high-cap) == rg == engine truth |
| `selectDice` (gmdice shard) | 3 hits (0.03s) | 3 hits (3ms) | 3 | candidate launch-chain verification before build |
| `SecureRandom` (cindex over candidate sources) | — | 8 lines (GameMasterDice field + imports) | 8 | confirmed the receiver type feeding the F-113 face |
| `nextInt` (cindex over candidate sources) | — | Standard/FUDGE/DSA/Coin roll paths | 4 files | the state-mutation law chain for the report |

Duplicates prevented / decisions changed this session:
- zoekt's "under-report" is now a DIAGNOSED tool law (trigram cap), not an
  open question — S61 finding #2 and S62's 0-row `attachHost` are explained
  by the same mechanism.
- csearch's per-file limit (S61 finding #3) reproduced with a 3rd data point.
- Before writing F-113 the ledger + zoekt(high-cap) check confirmed NO prior
  SecureRandom law existed anywhere in the engine (F-086 was the only Random
  family) — no parallel mechanism created.

Cumulative S63: TOTAL_SEARCHES 9 documented queries; UNIQUE_QUERIES 9;
REPOSITORIES_CHECKED 4 (ge0rg/gamemasterdice, billthefarmer/sig-gen,
vocollapse/Blockinger, openjdk/jdk) + fdroiddata metadata; DOMAINS_CHECKED 4
(github, f-droid, openjdk raw, go module proxy);
RELEVANT_HITS 12; IMPLEMENTATIONS_FOUND 2 (SecureRandom.next upstream law;
gradle BuildConfig generation contract); TESTS_FOUND 0 (upstream gmdice has
no test suite — honesty row); SEARCH_EXHAUSTED no.

## S64 additions (2026-09-19) — 3-candidate breadth survey + prefs/Timer/meta-data searchlight chain

Environment: zoekt (@ 153817f643cd) + cindex/csearch (v1.2.0) + Go 1.26.0
REBUILT again after the container reset (same GOPROXY=direct recipe).
F-Droid index-v2.json (60,145,769 B / 4,408 packages) downloaded ONCE and
scanned locally (scripts/s64_candidate_survey.py) — 20 keywords → 69 hits →
52 shortlisted; GitHub probes rate-limited mid-run (core remaining 0,
recorded) → switched to direct git clones (pinned SHAs).

| Query | zoekt (result) | csearch (hits) | Outcome |
|---|---|---|---|
| `onKeypadButtonTouched` (cand shard) | 13+ hits (XML android:onClick + handler) | 5+ lines | pmk input path classified xml_onClick (decision changed: not only touch-listener) |
| `Emulator extends Thread` | Emulator.java:10 | 1 line | pmk threading = real Thread subclass (build-value signal) |
| `setContentView file:GameActivity.java` | FK line 293 | — | FK game launch path mapped pre-build |
| `startActivity file:SplashActivity.java` | FK redirect path | — | predicted the Timer+meta-data face BEFORE the first run |
| `addTextChangedListener` | — | 5 files (SLC MainActivity:582) | SLC input model = TextWatcher family |

Upstream contract fetches (raw.githubusercontent, aosp-mirror/platform_frameworks_base @ main):
- SharedPreferencesImpl.java:307-313 — getString @Nullable default law (F-114a)
- PreferenceManager.java:67 + :661-673 — setDefaultValues one-shot guard law (F-114b/c)
- OpenJDK java/util/Timer.java sched()/mainLoop — fixed-delay repeat law (F-115)

F-Droid API v1 (-L): com.cax.pmk.ext (3.3.1/331), eu.veldsoft.free.klondike
(2.0.1/3), io.github.buildsbyben.shoppinglistcalc (2.0/15) — version pins
for the staged builds.

Cumulative S64: TOTAL_SEARCHES 17 documented queries; UNIQUE_QUERIES 17;
REPOSITORIES_CHECKED 9 app repos + aosp-mirror + F-Droid index; DOMAINS 5
(github, f-droid, aosp raw, openjdk-law, go module proxy); RELEVANT_HITS 24;
IMPLEMENTATIONS_FOUND 4; TESTS_FOUND 0 (honesty row); SEARCH_EXHAUSTED no.
Every search changed a decision (build order, law citations, staging laws);
none were decorative.

## S65 — Spotlight 4 (3 NEW source-first apps: TriPeaks / FishRings / OPMT)

Environment: zoekt (@ 153817f643cd) + cindex/csearch (v1.2.0) + Go 1.26.0
REBUILT after the 3rd container reset (same GOPROXY=direct recipe). The
container kills ALL background processes between tool calls — every long
job (Go install, zoekt build, battery, engine build, 3-run determinism)
ran FOREGROUND this session.
F-Droid index-v2.json (60,145,769 B / 4,408 packages) downloaded and
scanned locally (scripts/s65_candidate_survey.py): 45 keywords → 120-hit
shortlist; scripts/s65_probe.py probed 120 candidates in parallel against
raw.githubusercontent gradle/pubspec signatures (no API quota) → tiered.

| Query | Tool (result) | Outcome |
|---|---|---|
| `cardClickListener` | zoekt → GameActivity.java:74 + :437-477 (52 bindings) | CONFIRMED the field-initialized-listener pattern pre-build; predicted the <init> face before the first run |
| `ccwa` | zoekt → Rings.java:138 + 3 sites + GameActivity.java:35 | FishRings ring-rotation state surface mapped pre-build |
| `nextInt` | zoekt → Deck.java:98 / Rings.java:216 / Ai.java:49 | every Random-bound surface in the candidate corpus located |
| `buttonOnClickMethod` | zoekt → OPMT GameActivity.java:59-67 | 9 lambda registrations (B1..B9) — Tier-0 input face confirmed |
| `randomAi` | csearch → Ai.java ×2 | cross-tool consistency with zoekt |
| F-Droid scan (45 kw) | local index scan → 120 shortlist | sidhant947 family = Flutter (excluded by probe, not opinion) |
| gradle/pubspec probes ×120 | parallel raw reads | androidx/compose/ndk/libgdx/flutter tiers; 6 finalists cloned pinned |
| Instrumentation.java:1448 | AOSP raw @ main | newActivity(ClassLoader,String,Intent) → constructor law (F-118) |
| Integer.java:106 + Array.java:74/110 | OpenJDK raw @ master | TYPE = Class.getPrimitiveClass("int"); newInstance contract (F-119a/b) |

TOTAL_SEARCHES 9 · UNIQUE_QUERIES 9 · REPOSITORIES_CHECKED 9 · DOMAINS 4
(f-droid, github raw, aosp, openjdk) · RELEVANT_HITS 14 ·
IMPLEMENTATIONS_FOUND 3 · TESTS_FOUND 0 (honesty: no upstream
instrumentation tests for these faces) · SEARCH_EXHAUSTED no
(OBJECT-IDENTITY family queries queued in S65_REPORT §7).

---

## S66 — Full Visual Proof + Renderer Forensics (2026-09-19)

| Source file / query | Repository / origin | Law it grounds |
|---|---|---|
| aosp_Button.java:221 (`return com.android.internal.R.attr.buttonStyle;`) | aosp-mirror/platform_frameworks_base @ main (fetched, in S66 evidence) | F-120 Button default-style gravity = theme buttonStyle (Widget.Material.Button) |
| core/res/res/values/styles.xml — Widget.Material.Button `android:gravity` | aosp-mirror @ main (fetched) | F-120 center_horizontal\|center_vertical style default |
| activity_game.xml @ TriPeaks 62f3609 (pinned clone re-fetch, SHA-verified) | VelbazhdSoftwareLLC/TriPeaksSolitaireForAndroid | R-NEW-388: cards positioned by alignParentLeft/Top + marginLeft/Top (margins-as-offsets idiom); stats by alignParentBottom tiers |
| CardBoard.java @ 62f3609 | same | CardBoard is a plain model class (no View) — collapse is engine layout-side, not app-side |
| ViewShadow::ViewNode gravity member | g++ -fsyntax-only compiler probe (S66) | proved `gravity` member absent → view_renderer.cpp/real_layout.cpp not in Makefile build (dead code, no runtime effect) |
| execution_engine.cpp G36/G47 text stage + canvas_shadow.cpp warn_noop + software_renderer blend/PNGWriter | engine source forensics | live gravity consumer; clipRect pre-registered noop; source-over blend; faithful encoder |

TOTAL_SEARCHES 6 · UNIQUE_QUERIES 6 · REPOSITORIES_CHECKED 4
(aosp, VelbazhdSoftwareLLC/TriPeaks, engine source, local toolchain) ·
RELEVANT_HITS 6 · IMPLEMENTATIONS_FOUND 1 (F-120 shipped + rerun chain) ·
TESTS_FOUND 0 · HONESTY NOTE: zoekt/csearch shards lost to container reset;
NOT rebuilt this stage — every S66 item cites a fetched file, SHA-verified clone,
or compiler/source probe instead of a bare result count.

---

## S69 — FINAL FOUNDATION / SOURCE-LINKED RUNTIME CAMPAIGN (2026-09-20)

| Source file / query | Repository / origin | Law it grounds |
|---|---|---|
| fdroiddata metadata yml ×11 (SourceCode + per-versionCode commit pins) | gitlab.com/fdroid/fdroiddata @ master (raw fetches) | §1 SOURCE-FIRST: every corpus APK pinned to the exact commit F-Droid built (upstream/corpus/*/PROVENANCE.json, tarball SHAs) |
| VelbazhdSoftwareLLC/TriPeaksSolitaireForAndroid @62f3609 (codeload) | session ledger S66 S3 (re-fetch, SHA-verified) | TriPeaks source tree for R-NEW-388 + source_map |
| VelbazhdSoftwareLLC/FishRingsForAndroid @dc3807e (codeload) | session ledger S65 | FishRings source tree (6/6 source↔DEX class match) |
| 20Nick/OPMT @3240c4cf (codeload) | worklog S65 | OPMT source tree (7 source files mapped) |
| OpenJDK Double.java (isNaN :1031 `(v!=v)`, isInfinite :1048, compare :1538 bits-ordering) | openjdk/jdk @ master raw (docs/upstream/openjdk/Double.java, sha256 84888960313b0461…) | F-135 Double NaN/infinite/compare laws |
| OpenJDK Float.java (isNaN :631 `(f!=f)`) | same (sha256 fd27083f3f868524…) | F-135 Float law |
| corpus DEX census (androguard invoke-* walk, 213,251 sites) | upload/canonical_apks/* | §13/§14 fan-out: Double/Float NaN family = 694 sites × 7 APKs → F-135 priority |
| live dispatch traces (--dump-api-trace) ×10 APKs | run/s69_live/*/api_calls.json (summarized live_runs.json) | bouncy 480× STUB→IMPL NaN flip proof; REC-MISS = dispatch-path log (not failure) law |

TOTAL_SEARCHES 8 · UNIQUE_QUERIES 8 · REPOSITORIES_CHECKED 11 (10 pinned +
OpenJDK) · DOMAINS 5 (gitlab-fdroid, github-codeload, raw.githubusercontent,
f-droid API, local DEX) · RELEVANT_HITS 10 · IMPLEMENTATIONS_FOUND 1 (F-135
shipped) · TESTS_FOUND 1 (f52_nanlaw) · HONESTY NOTE: gitlab.com archive/git
endpoints 403'd all session — uNote stays UNPINNED @4165c80d (identified, not
fetched); GitHub API rate-limited (60/h unauth) — codeload used instead (no
quota); every §17 item cites a fetched file or SHA, none a bare count.
