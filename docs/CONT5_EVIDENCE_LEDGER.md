# CONT-5 — Final Compatibility Closure Evidence Ledger (Issue #375)

Binary `miniandroid/build/miniandroid` sha16 `1177e1d08e09ee72` (clean-tree rebuild at
HEAD bb2f4f49 = 1c2ccdfd + tmp comment copy; zero code delta). Head identity and every
bootstrap repair are recorded in the worklog (`cont375-CONT-5` entry).

## PHASE 4 — F-NEW-239..242 (+243/245/246) genericity table

| Law | Semantic law | Implementation site | Original failing behavior | Corrected behavior | Fairy Mahjong evidence | Independent consumer |
|---|---|---|---|---|---|---|
| F-NEW-239 | ArrayList.set(i,E) returns the PREVIOUS element (OpenJDK) | dalvik_engine.cpp CollectionShadow set + engine array-backed set | set() returned VOID → every Kotlin shuffled() swap poisoned a slot with "" | kind-faithful prior-element serve | solver face-set became string-typed → counts 46/68 → parity ISE; post-fix exit=0 ×3 | f235_set_probe rows (15/15, sha ea31dc0dc539df73); any List-swap idiom |
| F-NEW-240 | BitmapFactory.Options: inJustDecodeBounds fills out* + returns null; inSampleSize honored (AOSP BitmapFactory.java) | f240_decode_with_options | decodeStream ran FULL decode, never wrote outWidth/Height → "Invalid fairy artwork" on valid 1122x1402 PNG | bounds-first law + nearest subsample | artwork chain passes; render reaches full-screen content | any bounds-first loader (probe rows in gate A decode family) |
| F-NEW-241 | Reader.read(char[]) fills from the wrapped stream; -1 at EOF (OpenJDK Reader.java) | read law over resolve_asset_stream wrapper hops | BufferedReader.read → stub 0 → `while(read>=0)` spun → F084 halt Ln5;.b pc=0x108 ×3 | char-faithful fills, -1 EOF | artwork-config JSON copy loop completes | any `while((n=read(cbuf))>=0)` loop (f084_loop_probe P1/P2/N1 3/3) |
| F-NEW-242 | StringWriter.write appends; toString() = accumulated chars, never null | sb_value convention (F-NEW-242 block) | toString() → null → R8 getClass NPE Ln5;.b pc=278 | full write/toString/getBuffer laws | JSON asset parse completes | f084 probe; any StringWriter-JSON chain |
| F-NEW-243 | org.json real laws (put/toString/get/opt/parse; toString null ONLY for unserializable members — AOSP catch law) | F-NEW-243 block (nlohmann ordered_json) | NO org.json at all → toString() stub null for serializable settings → Lr5;.g pc=150 NPE | real serialization + AOSP parity | settings save chain completes; Lr5 NPE 0/3; [F243-DIAG] content dump | f235 probe unaffected (regression clean); any org.json consumer |
| F-NEW-245 | System.out/err NEVER null (OpenJDK System.java) + PrintStream println/print/write to real stdout/stderr | sget-object synthesis + PrintStream bridge | sget System.out → NULL → first println NPE → APP BOUNDARY death (raumballer pc=81) | non-null PrintStream, real console I/O | regression clean (76e097244767d6c3) | **raumballer** (real APK): death → SUCCESS ×3 |
| F-NEW-246 | Vector store laws + elements()/Hashtable.keys() NON-NULL snapshot Enumeration (OpenJDK Vector/Hashtable.java) | F-NEW-246/246b blocks | elements()/keys() → stub NULL → Enumeration NPE (raumballer defineMedia pc=0x82, stopAudio pc=6) | snapshot enumeration, NoSuchElementException at exhaustion | regression clean | **raumballer**: defineMedia/stopAudio pass |

**Genericity discipline**: every law is keyed on receiver runtime-class semantics, never on
package/APK identity. Independent consumers: F-NEW-245/246 proven on raumballer (a REAL
third-party APK, previously L0 LOADED_ONLY); F-NEW-239/243 on fairymahjong (real APK) +
f235 probe; F-NEW-240..242 on fairymahjong + f084 probe. Implementation location ≠ proof —
each row above cites a runtime execution path.

## PHASE 5 — full battery debt (honest)

- **The recorded 124-stage battery runner is NOT in the repository** (CONT-3/CONT-4
  already recorded "no runner in repo"; tmp/apks corpus wiped by container resets). Blocker
  class: TOOLING (P3). A/B vs clean baseline: the recorded gates below are screenshot-SHA
  pinned, so drift is measurable without the old runner.
- **Reconstructible battery executed this wave** (all at binary 1177e1d0):
  - S67 foundation pixel battery: **16/24 PASS** (pixel+ViewTree asserts). 8 rows
    NO_VISUAL_PROOF = fixture build prerequisites absent post-container-reset (harness
    prerequisite, not a runtime divergence). f54 "3 failed" = `engine.log missing`
    (harness artifact — the file the verifier reads is no longer emitted at that path; P3).
    vs CONT-3's "8 pre-existing fails (f06/f08/f26/f38/f39/f45/f49/f52)": **f08/f38/f45/f49/f52
    now PASS** — the fixture-rebuild drift was repaired in later waves.
  - Unknown-APK gate live matrix over **56 real APK rows** (see PHASE 6) — the largest
    single-run corpus sweep recorded on this binary.
  - All recorded gates green: anchors 5/5 ×3 byte-identical, goldens 4/4
    REAL_APP_CONTENT, gate A 97/0/2, negatives 19/19, reinstall 8/8, multiapp 5/5,
    loading, uninstall, skill 13/13, NATX 10/10 ×3 byte-identical (14672668f77e69ba),
    f235 probe 15/15 ×3 (ea31dc0dc539df73), f084 probe 3/3.

## PHASE 6 — unknown-APK gate LIVE coverage matrix (issue contract)

CLI: `scripts/unknown_apk_preflight.py` (MINIANDROID_UNKNOWN_APK_PREFLIGHT/1.0), executed
over 56 locally-available APK rows (foundation 26 + canonical/stash/wave 27 + negatives 3),
all rows in `run/cont5/gate_matrix/` and machine ledger below.

| Verdict | Status | Rows | Evidence |
|---|---|---|---|
| PREFLIGHT_PASS | LIVE-PROVEN | 3 | f27_nav, opmt ×2 (frames>0 + callbacks>0) |
| CAPTURE_ONLY | LIVE-PROVEN | 35 | budget-stopped clean captures (f01..f54 family, stopwatch, klondike, …) |
| RUNTIME_ROOT | LIVE-PROVEN | 13 | bouncy, tictactoe, gmdice, dooz_23, opencalc, chess, clock, sudokusolver, raumballer, mentalmath, f39, f45 (+first_divergence recorded) |
| RESOURCE_BLOCKED | LIVE-PROVEN | 3 | unote, notes_secuso @15s budget (+identity_tamper) — honest note: the two anchors are green at the recorded 110s budget; the 15s sweep budget clips them into resource-fail (budget artifact, recorded) |
| UNKNOWN | LIVE-PROVEN | 2 | truncated APK (N-04 law), no-manifest zip (N-05 law) |
| INSTALL_BLOCKED | OBSERVED | — | law exists (classify: install FAILED non-identity); N-04/N-05 rows exercise the install-refusal path at gate level; CLI row not produced this sweep |
| IDENTITY_BLOCKED | OBSERVED | — | live refusal proven by reinstall matrix 8/8 + reinstall-identity law (s41_gatea_reinstall); the zip-comment tamper did NOT trigger the CLI identity branch (recorded honestly) |
| SECURITY_BLOCKED | NOT-YET-EXERCISED | — | no corpus APK hits launch_stage=security |
| SERVICE_BLOCKED | NOT-YET-EXERCISED | — | no corpus APK hits launch_stage=service |
| EXECUTION_BLOCKED | NOT-YET-EXERCISED (emittable) | — | law wired (launch_stage=dex); no row this sweep |
| GRAPHICS_BLOCKED | NOT-YET-EXERCISED (emittable) | — | GLES>2 gate wired; no corpus APK requests GLES3+ |
| ENVIRONMENT_BLOCKED | OBSERVED | — | recorded CONT-3 evidence (EggReturnsHome arm64-only; arm-only ABI law + FA-01/FA-02 honest ABI advertisement); APK not re-fetched this wave |
| MEDIA_BLOCKED / NETWORK_BLOCKED / INPUT_BLOCKED | NOT-EMITTABLE (dead branches) | — | verdicts listed in ALL_VERDICTS and the env-prerequisite tuple, but classify() has NO emit path — dead code, honestly recorded as a gate-tooling gap (P3), NOT claimed as covered |

Honest total: **5 verdicts LIVE-PROVEN, 2 OBSERVED, 5 emittable-but-not-exercised,
3 non-emittable dead branches** (15 total, no fabrication).

## PHASE 9 — white/black/partial audit (first divergences)

| App | Frame verdict | Pixel truth | First divergence |
|---|---|---|---|
| fairymahjong | SUCCESS ×3 | full-screen app content 2073600/2073600 px, sha 76e097244767d6c3 ×3 | — (board→solver→artwork→render pipeline completes; save chain now real JSON) |
| raumballer | SUCCESS ×3 | JGView own onDraw ops=3 replayed; 3 colors; sha a7a73cc61722497c ×3 | — (jgame engine canvas; menu-level content) |
| chess (anchor) | PARTIAL (background-only pixels) | uniform (48,48,48) | F-NEW-244 spin at Ln3/b clinit — **FIXED this wave**; next face below the window stage (recorded, open) |
| dooz (anchor) | PARTIAL (background-only pixels) | uniform (250,250,250) | Compose draw frontier (R-NEW-381 family) — open |
| Fossify Clock | NO_ROOT → advanced past kotlin-reflect spin | white | provider chain "Unknown authority org.fossify.android.provider" at SplashActivity.onCreate (AOSP-honest IAE; app-side handling boundary) — named, open |
| Compose Sudoku | DEFAULT_BACKGROUND_ONLY | uniform (250,250,250) | composition materializes + decor attach PROVEN (R005-DECOR view=1574 under decor=1075); APP_DRAW_OPS missing — Compose draw frontier open |
| TriPeaks | DEFAULT_BACKGROUND_ONLY | uniform (48,48,48) | APK ships NO assets/banner.html (honest WebView miss) + splash timer deferred UI — named |
| TicTacToe Classic | APP BOUNDARY death | uniform (48,48,48) | libGDX GLSurfaceView20.setPreserveEGLContextOnPause NoSuchMethodException (F-144 GL surface family) |
| bubbleshooter / sidhant.puzzle | NO_ROOT | white | **Flutter** engine architecture boundary (flutter_assets; own native rendering) |
| mentalmath | DEFAULT_BACKGROUND_ONLY | uniform dark | Compose frontier (ComposeView not in class index; UC009) |

"RESUMED"/"View exists"/"PNG valid" claims are NOT counted as visual success anywhere above.

## PHASE 10 — no-new-app-specific-hack audit

Every fix this wave states a generic law + fan-out + API family + runtime + regression
evidence (see PHASE 4 table + registry entries F-NEW-243/244/245/246). Zero package-name
special cases, zero APK-specific branches, zero hardcoded coordinates, zero state
injection, zero screenshot substitution. Diagnostics added this wave are env-gated
(MINIANDROID_F243_DIAG / F244_DIAG) and read-only.
