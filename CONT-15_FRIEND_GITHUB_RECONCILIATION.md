# CONT-15 — COMPLETE GITHUB LINEAGE + FRIEND-AGENT FINDINGS RECONCILIATION

Wave: CONT-15 · date 2026-10-07 · merged HEAD `9ab1b891` (= remote `f0a36646`
CONT-12 W8 + local CONT-14 artifacts, fast-merge committed this wave) ·
rebuilt binary at merged HEAD: **`0ee46f5a719d2a8c` — byte-identical to the
binary CONT-12 itself recorded**, proving source-lineage identity.

Audit method: every verdict below is grounded in (a) actual git commits
(fetched and merged this wave), (b) evidence documents committed in-repo,
(c) live runs at the merged HEAD, (d) the canonical registry. Where an item
is absent, the report says NOT FOUND IN GITHUB / ABSENT rather than guessing.

---

## A. GITHUB LINEAGE

| Wave | Commit | Main frontier | Actual root/decision | Evidence | Status |
|---|---|---|---|---|---|
| CONT-8 W4 | `299e84d2` | Compose draw frontier | F-NEW-256 refined (mid-content-pass apply reading — later REFUTED by CONT-9) | `evidence/cont8/*` | CLASSIFIED (256) |
| CONT-9 W5 | `f5a2c399` | F-256 re-proof, dooz structure discovered | W4 apply-order claim REFUTED; refined divergence = recompose scope re-invocation | `evidence/cont9/*` | CLASSIFIED (256) |
| CONT-10 W6 | `6a66806a` | NavHost data path | **F-NEW-259 + F-NEW-259b ROOT-CAUSED-FIXED** (DEX-iterator by-NAME law; addAll silent no-op); dooz materializes LayoutNodes; draw path remains 0 ops | `evidence/cont10/fnew259_evidence.json` | FIXED (259/259b) |
| CONT-11 W7 | `ee7bf6c3` | External-runtime feasibility + draw path re-root | **External runtime REJECTED with measured evidence (KEEP MINIANDROID PATH)**; **F-NEW-265** (draw machinery EXONERATED: measure dies on null-text ctor cascade → isPlaced=false); F-NEW-264/264b/264c fixes; 264d collection-law grouping; 259g-a/b registered; registry 566→573 | `evidence/cont11/CONT11_EXECUTION_LEDGER.md` | FIXED (264c) / CLASSIFIED (265) / REGISTERED (259g-a/b) |
| CONT-12 W8 | `f0a36646` | External real-Compose ORACLE (TEST-ONLY) | B1 literal merge proven inert ×3 (binding wall real); **F-NEW-266 ROOT-CAUSED-FIXED** (invoke-virtual transitive interface-default dispatch → silent null; Modifier.then → NPE×172 → setContent dead); **F-NEW-266a** honest fail (null-receiver dispatch gap); registry 573→575 | `evidence/cont12/CONT12_EXTERNAL_COMPOSE_ORACLE.md` | FIXED (266) / CLASSIFIED (266a) |
| CONT-13 | **NOT FOUND IN GITHUB** (no commit; ran in the severed session) | validation of friend's 14-APK claims | never landed | — | NO CANONICAL RECORD |
| CONT-14 | local `5059ff79` (committed this container; pushed via merge) | audit of friend's F-271..277 | 0 real roots / 1 refuted / 2 invalid suppressions / 4 unverifiable; 55/100 rejected | `CONT-14_FRIEND_FINDINGS_AUDIT.md` | AUDIT-ONLY |
| CONT-15 (this wave) | `9ab1b891` | lineage merge + reconciliation | this document; registry counter reconciled 566(stale)→575; full battery green | `evidence/cont15/*` | CURRENT HEAD |

Commits `06c9f853` (CONT-11 ledger post to #379/#375) and `22875aa3`/`e5ea3e53`
(uuid housekeeping commits) also present. Issue bodies/comments (#375/#379/#380)
**NOT FOUND VIA API THIS WAVE — GitHub API rate-limited (recorded honestly)**;
the commit messages quote the ledger postings verbatim.

## B. FRIEND FINDINGS — one row per F-NEW-266..277

| Finding | Friend claim | GitHub evidence | Current implementation | First divergence | Generic? | Shim? | Suppression? | Runtime proof | 3-run | Final status |
|---|---|---|---|---|---|---|---|---|---|---|
| **F-NEW-266** | (friend asserted Compose ctor/R8-name work) | **REAL, CONT-12**: invoke-virtual → transitive superinterface default method returned silent null; Modifier.then NPE×172 | `try_interface_default_invoke()` wired into BOTH 35c + 3rc paths, memoized, framework-gated | oracle12 `AndroidComposeView.<init>` pc=247 | **YES — generic (JVMS 5.4.5)** | no | no | probe f266 5/6 live this wave (A/B/C/E/F PASS) | anchors byte-identical ×3 this wave | **IMPLEMENTED/TESTED — ROOT-CAUSED-FIXED (canonical)** |
| **F-NEW-266a** | — | REAL, CONT-12: typed-null receiver dispatched a DEX default body instead of NPE | deliberately NOT patched | probe row D | generic law gap | no | no | probe D FAIL reproduced this wave (honest) | — | **CLASSIFIED (registered, next-wave)** |
| F-NEW-267 | unknown (report lost) | NOT FOUND IN GITHUB | none | — | — | — | — | none | — | **UNVERIFIABLE** (needs friend re-supply; collection-family gaps already grouped under 264d) |
| F-NEW-268 | unknown (report lost) | NOT FOUND IN GITHUB | none | — | — | — | — | none | — | **UNVERIFIABLE** (idem) |
| **F-NEW-271** | hardcoded `Lr;` in AbstractComposeView ctor Context | NOT FOUND IN GITHUB; **grep `'"Lr;"'` = 0 hits in whole engine** | generic F-031 law already captures FIRST ctor Context arg (`android_shadows.cpp:4421`, dooz named in its comment) | none — dooz chain receives MainActivity and proceeds past ctor | n/a — **defect absent** | no | no | dooz runs to measure/layout at HEAD (d602648e ×3) | — | **REJECTED (non-root; hypothesis itself was withdrawn by the friend's own tracing)** |
| **F-NEW-272** | FirebaseInitProvider.onCreate → no-op; Telegram exceptions ↓ | NOT FOUND IN GITHUB; 0 hits for FirebaseInitProvider in src/ | none | Telegram's recorded GMS faces were analyzed canonically (LocationController getImpliedScopes NPE — worklog S-record), never stubbed | unproven | maybe-shim at best | risk: hides provider-init contract | none beyond exception count | — | **UNPROVEN → REJECTED as root** (AOSP provider contract not audited by friend; no second-Firebase-APK cross-check) |
| **F-NEW-273** | BillingController.getInstance → unavailable singleton | NOT FOUND IN GITHUB; 0 hits in src/ | none | — | unproven | capability-shim shape at best | no | none | — | **UNPROVEN** (return contract never proven; Play-Billing second app never tested) |
| **F-NEW-274** | GoogleApiAvailability.isGooglePlayServicesAvailable → unconditional SUCCESS | NOT FOUND IN GITHUB; 0 hits in src/ | none | — | **NO as stated** — unconditional SUCCESS contradicts the GMS contract (unavailable device must answer FAILURE-family code) | capability-shim shape | risk: caller then calls real GMS APIs and dies | none | — | **INVALID as proposed** (a correct law would answer per-device capability, not always-SUCCESS) |
| **F-NEW-275** | PowerManager.isPowerSaveMode → false | NOT FOUND IN GITHUB; engine: PowerManager shadows exist generically | env-default false is plausibly the honest AOSP default for a no-battery-validator host env, but friend proved nothing | — | environment-default, not a root | env contract | no | not probed | — | **ENVIRONMENT DEFAULT (plausible, UNPROVEN as a law; needs +probe/-probe)** |
| **F-NEW-276** | suppress `LF/r;.c` Compose consistency helper | NOT FOUND IN GITHUB; 0 suppression sites in engine | none (dooz still reports its 6 uncaught honestly) | friend's OWN data: exceptions↓ but 0 draw ops / 0 px | no | no | **YES** | friend's own counter-evidence | — | **INVALID-SUPPRESSION** (exception-count ↓ ≠ compatibility ↑; PHASE-9 lesson) |
| **F-NEW-277** | suppress THROW for short R8 names (`LF/h;`, `LH/k;`) | NOT FOUND IN GITHUB; no THROW-site suppression in engine | none | — | **NO — R8 names carry no semantics** | no | **YES** | none | — | **INVALID-SUPPRESSION** (forbidden matcher class) |
| "F-NEW-236 JNI slot binding" | affects libtmessages/libgdx/Telegram/tictactoe | NOT FOUND IN GITHUB | **canonical F-NEW-236 = JDK Set-Family (fairymahjong) — ID COLLISION confirmed** | tictactoe's real chain measured this wave: F-NEW-219 (GLSurfaceView20 reflection) + SharedLibraryLoader.loadFile | JNI binding law itself unproven | no | no | tictactoe first divergence captured live (b5a7a35d, 9 uncaught) | ×1 this wave | **DUPLICATE-ID (rejected); JNI law = future candidate, next free ID F-NEW-267-slot reserved-by-convention only** |

## C. SIX-GAME CLAIM (friend KB; CONT-9 mandate) — independently re-validated THIS wave

All six at merged HEAD, ×3 byte-identical each, engine frame-truth verdicts:

| Game | APK sha16 | screenshot ×3 | verdict | draw ops |
|---|---|---|---|---|
| 2048 | `1b1c602a5f0a2723` | `59ca1526611c4622` | REAL_APP_CONTENT | 28 |
| mini-tetris | `cb2818dfe6c6cadb` | `f360daa244cfca8d` | REAL_APP_CONTENT | 71 |
| minicraft | `77b9629ee111b968` | `b0876952f41e4af2` | REAL_APP_CONTENT | 401 |
| snake-deluxe | `551eca798f88c1bb` | `34a712689ce66e58` | REAL_APP_CONTENT | 263 |
| snake-neon | `b36885c181a323ab` | `24fb7694eb64634a` | REAL_APP_CONTENT | 44 |
| tictactoe-deluxe | `d04d92eab8dbbb11` | `af6094295ecb50e3` | REAL_APP_CONTENT | 35 |

**6/6 CONFIRMED** (screenshot SHAs differ from CONT-7-era records because the
fixture APKs themselves were rebuilt at different SHAs since — noted honestly;
the claim's substance, real app-owned pixels, holds 6/6).

## D. FRIEND 14-APK BATCH — reconciliation where artifacts exist

| Friend row | Friend claim | This wave's independent result |
|---|---|---|
| patolli | REAL_APP_CONTENT | **BLOCKED-APK-ABSENT** (no artifact in container) |
| gmdice | REAL_APP_CONTENT | **CONFIRMED** — `f3b483fe7b7cf51b` ×3 REAL_APP_CONTENT, 6 ops |
| hayago | REAL_APP_CONTENT | **BLOCKED-APK-ABSENT** |
| openchaoschess | REAL_APP_CONTENT | **BLOCKED-APK-ABSENT** |
| Telegram | REAL_APP_CONTENT | **CONFIRMED at HEAD — but caused by the canonical lineage, not friend fixes (§E)** |
| unote | REAL_APP_CONTENT | **CONFIRMED** — `4f1a9e4e8f64fae8` ×3 (recorded golden anchor) |
| Dooz F-Droid vc=18 | DEFAULT_BACKGROUND_ONLY | vc18 APK absent; **vc23 ×3 = d602648e DEFAULT_BACKGROUND_ONLY** (honest; F-NEW-265 stands) |
| janken | DEFAULT_BACKGROUND_ONLY | APK absent; **recorded s107 pixels = C013 placeholder "custom view (not rendered)"** — friend's DEFAULT_BACKGROUND verdict consistent with recorded pixels |
| bullseye | DEFAULT_BACKGROUND_ONLY | **BLOCKED-APK-ABSENT** |
| tictactoe_emmanuel | DEFAULT_BACKGROUND_ONLY | **CONFIRMED HONEST** — `b5a7a35d` DEFAULT_BACKGROUND_ONLY, 0 ops, first divergence freshly captured (F-NEW-219 + SharedLibraryLoader chain) |
| kaesekaestchen | NO_ROOT | **BLOCKED-APK-ABSENT** |
| stopwatch | NO_ROOT | muellerma stopwatch APK present (not run this wave — time box); recorded CONT-11 fan-out: stopwatch deterministic `31ddd4d5` ×3 |
| (counts) | 12/14 RESUMED, 7/14 real pixels | only 3 of the friend's REAL_APP_CONTENT rows verifiable here (gmdice/telegram/unote) — all 3 confirmed; nothing counted from background/fallback/harness pixels |

## E. TELEGRAM — causal explanation (no credit to absent patches)

- Friend claimed: exceptions 14→3, Firebase/GMS changes "helped", REAL_APP_CONTENT.
- **Canonical causal chain (all recorded in-repo, none of it friend code):**
  1. S107→S110 fix-waves: telegram errors 32→7→6→0 (ROOT-062 created-phase
     lifecycle fan-out; ROOT-063 StaticLayout.Builder) — `evidence/s115_telegram/REPORT.md`.
  2. s115 run4: first fully clean execution; login tree **measured but not painted**.
  3. V-wave (F-NEW-193 frame-truth census): **forkgram `cf4c41e62ceb6557` ×3 =
     REAL_APP_CONTENT — 31 nodes, 11 draw ops, 117,133 app-owned px INSIDE content
     bounds, chrome 0** — first Telegram-class flagship with in-bounds proof.
  4. This wave at merged HEAD: telegram = `cf4c41e62ceb6557` REAL_APP_CONTENT
     (byte-identical across three different binary builds — pre-CONT-11 aed46450,
     CONT-12 0ee46f5a) → the state is stable canonical lineage, independent of
     friend patches (which are absent from the tree).
- **Remaining honest faces at HEAD:** title-overlap (`LowPowerEnabledTitle` drawn
  twice), `deferred_ui_pending=True` (2 queued), 6 EXC-UNCAUGHT-TOP / 44 in-flight,
  NOT the login flow / chat list.
- The friend's 3-exception state is therefore **not relevant as a fix signal**;
  the remaining faces are registered layout/paint frontiers.

## F. COMPOSE — actual current first divergence (native, at merged HEAD)

`F-NEW-265` (CLASSIFIED, CONT-11, re-verified live in CONT-12 at the SAME binary
`0ee46f5a719d2a8c` this wave rebuilds):

```
setContent → composition → change recording → applyChanges   ✓ (CONT-9/10 proofs)
LayoutNodes materialize                                       ✓ (CONT-10 proof)
measure/layout begins (Lzs0.m fires 45× under Lt4.onMeasure)  ✓
Lm7.<init> receives NULL text CharSequence (Lvs0.c caller)    ✗ FIRST DIVERGENCE
  → legal R8 kotlin null-check throws
  → deferred-throw blast radius (F-264 delivery law carries the real NPE)
  → compose report helper Lel0.Y gets real Throwable ×11
  → measure dies → placement never runs → isPlaced=false everywhere
draw walk faithfully honors isPlaced (Lel0.J→Lil0.p→Lbt0.w)   ✓ (machinery EXONERATED)
0 content canvas ops → DEFAULT_BACKGROUND_ONLY (d602648e ×3)  ✓ honest
```

Friend's deep conclusion (onMeasure/onDraw reachable with 0 ops because state
materialization is incomplete) is **the same divergence CONT-11 already rooted
more precisely** — the friend observed the symptom, the canonical lineage holds
the link-by-link proof. Not "Compose works"; not "restart from zero" either.

## G. ROOT ACCOUNTING (final, with the required statuses)

- **GENERIC ROOTS (proven, canonical):** F-NEW-266 (IMPLEMENTED/TESTED —
  ROOT-CAUSED-FIXED), F-NEW-266a (CLASSIFIED — registered gap), F-NEW-265
  (CLASSIFIED — first divergence fully proven), F-NEW-264c (ROOT-CAUSED-FIXED,
  probe-verified 11/13 this wave), F-NEW-259/259b (ROOT-CAUSED-FIXED, probe 7/7
  this wave), F-NEW-259g-a/b (REGISTERED, honest FAILs reproduced this wave).
- **VALID SHIMS:** none accepted this wave. (F-NEW-274's *shape* — a capability
  query — could become a VALID capability shim only if it answers per-device
  contract, never unconditional SUCCESS; F-NEW-275's false-default is an
  environment contract, not a shim.)
- **DUPLICATES:** "F-NEW-236 JNI" (ID collision with JDK Set-Family);
  F-NEW-271 (duplicates the already-closed F-031 law family);
  F-NEW-276/277 (duplicate the already-REFUTED suppression family).
- **SOURCE-ONLY:** friend KB 5,976 records (snapshot `d717e9c7…`, audited HEAD
  `f8d4088b`) — ABSENT-THIS-CONTAINER, searchlight-only per MANIFEST hard rules;
  5,434 "VERIFIED-NEW" are NOT runtime-proven roots.
- **UNPROVEN:** F-NEW-272 (Firebase), F-NEW-273 (Billing), F-NEW-275 (PowerSave
  as a law), F-NEW-267/268 (content unknown).
- **INVALID SUPPRESSIONS:** F-NEW-276, F-NEW-277.
- **ENVIRONMENT:** F-NEW-275 classification (default-state, not a root).
- **BLOCKED:** friend batch APKs (patolli, hayago, openchaoschess, bullseye,
  kaesekaestchen, dooz-vc18, janken) — APK-ABSENT with exact missing artifact
  named per row in §D.

## H. NEXT FRONTIER — exactly one highest-ROI generic root

**F-NEW-265 — the dooz/compose measure-pass death: `Lm7.<init>` null-text
CharSequence from `Lvs0.c` (deferred-throw blast → placement never runs →
isPlaced=false → 0 content ops).**

Scores highest on the mandated rubric: FIRST DIVERGENCE precisely named at
instruction level; affects **every Compose app family** (dooz + sudokusolver +
sudoku_secuso + any future Compose APK — the largest single family in the
corpus); visual impact = full-screen content vs background; genericity = pure
framework text-layout contract (no R8/app knowledge); implementation cost =
bounded (text-CharSequence contract at the ctor + the deferred-throw semantics
already built in F-264); regression risk = low (anchors byte-identical across
the whole CONT-11/12 work at the same binary, and the F-264 law shows the
delivery path is already honest). Runner-up (explicitly NOT chosen): JNI slot
binding for registered natives (tictactoe F-NEW-219 + SharedLibraryLoader) —
higher cost, narrower family until a second native APK is re-supplied.

## FINAL ANSWER (the directive's one question, plainly)

After reading the actual GitHub lineage (CONT-9 `f5a2c399` → CONT-10 `6a66806a`
→ CONT-11 `ee7bf6c3` → CONT-12 `f0a36646` → merged HEAD `9ab1b891`) and
re-checking every friend finding against it:

1. **Real reusable MiniAndroid semantic roots discovered by the friend: ZERO.**
   Every semantic law the friend's findings touch was already discovered, fixed,
   or classified by the canonical lineage with strictly deeper proofs:
   the Compose ctor/Context face = F-031 (long closed); the "Compose advances
   but draws nothing" face = F-NEW-265 (CONT-11, instruction-level proof); the
   "external Compose runtime changes nothing unless bound" face = CONT-12's
   measured B1 experiment; the collection/descriptor faces = F-NEW-259/259b/264
   family. The one genuinely new generic root of this era — F-NEW-266
   (invoke-virtual transitive interface-default dispatch) — came from the
   canonical CONT-12 oracle wave, not from the friend.
2. **Valid compatibility shims: ZERO accepted.** Three friend items had
   shim-shaped surfaces (Firebase no-op, Billing unavailable-singleton, GMS
   availability) but none proved its Android contract; the GMS one as proposed
   (unconditional SUCCESS) is contractually WRONG, not merely unproven.
3. **Already solved by CONT-9..12:** F-NEW-271 (F-031 + F-NEW-259/259b data path
   were the real story), F-NEW-276's symptom area (F-NEW-265), the deep-Compose
   conclusion (§F chain), the six-game claim (already a canonical current-HEAD
   fact since CONT-7, re-confirmed 6/6 this wave).
4. **Duplicates:** "F-NEW-236 JNI" (ID collision — canonical 236 is the JDK
   Set-Family; the JNI law itself remains a legitimate FUTURE root awaiting its
   own proof chain and a fresh ID), F-NEW-277/276 (duplicate the
   suppression-refuted law), F-NEW-271 (duplicate of closed F-031).
5. **Symptom suppression:** F-NEW-276 and F-NEW-277 — INVALID (the friend's own
   data shows exception-count ↓ with 0 draw ops / 0 px; R8 short names carry no
   semantics). **Unproven claims:** F-NEW-272/273/274/275 and the unknown
   F-NEW-267/268 (report lost with the severed context — UNVERIFIABLE, not
   "wrong"; re-audit on re-supply).

*Evidence this wave: `evidence/cont15/{battery.json, sixgame_validation.json}`,
`run/cont15/*` (dooz ×3, anchors ×3×3, probes f259 7/7 · f259g 11/13 · f266 5/6,
gate A 98/0/1, negatives 19/19, skill 13/13, telegram, tictactoe), probe
screenshots with rendered row verdicts. No engine source modified this wave;
registry bookkeeping counter reconciled (575); no KB import; no suppression;
no fallback pixels counted.*
