# CONT-37 — Self-Update (331 commits) + the F-NEW-541 Caller-Site PC Law +
# the Telegram Envelope REFUTATION (F-NEW-542 live heap census)

Wave: CONT-37 (user directive: «گیت هاب به روز رسانی ادامه ادامه تا هدف
نهایی» — GitHub update, continue until the final goal). Predecessor:
CONT-36 (wagons wave). This wave: (0) honest self-update — the container
was 331 commits BEHIND (stale at the CONT-10-era snapshot e99c2fbd; remote
main at e9ba74d2 = CONT-36), fast-forwarded byte-faithfully and the
CONT-29..36 ledgers consumed; (1) engine rebuilt from HEAD reproducing the
frozen CONT-36 lineage BYTE-IDENTICALLY (60d377668b5a2649) with the dooz
90s anchor 851cc1761a1dfcdf reproduced pre-wave; (2) batch-50 census at the
current binary with VISUAL verification of every content row; (3) the dooz
board-paint dive — the full DEX decode of the compose draw chain, the
root-cause of the never-dispatched board draw block, and the F-NEW-541
caller-site-pc identity law landed + gated; (4) the F-NEW-542 live heap
census instrument landed and the CONT-36 telegram envelope REFUTED with
live data; (5) full regression wall green; (6) registry 832→834.

## 0. RESUMABLE STATE BLOCK

| item | value |
|---|---|
| HEAD at wave start (after sync) | e9ba74d2 (CONT-36; local == origin/main) |
| pre-wave binary | 60d377668b5a2649 (== the CONT-36 recorded final binary; dooz anchor 851cc176 reproduced) |
| post-F-NEW-541 binary | d2da8f4263899bb7 |
| post-F-NEW-542 binary (final) | a95136b836bbb0bc (the regression wall ran HERE) |
| target APK (dooz) | upload/canonical_apks/io.github.yamin8000.dooz_23.apk |
| target APK (telegram) | upload/telegram_official.apk |
| census | evidence/cont37/batch50_census.json (50/50 rows) |
| regression | run/cont37/wall/ (anchors + games), run/gatea/negative (19/19) |

## 1. PHASE 0 — SELF-UPDATE (honest admission)

- `git fetch`: origin/main 331 commits ahead (local stale at e99c2fbd =
  the CONT-10-era snapshot). Fast-forward to e9ba74d2. THE CONTAINER WAS
  STALE — honest admission recorded (the standing «اگر تو له روزی بگو»
  directive).
- Consumed: CONT-29..36 worklog records, the #387 ledger comment files,
  registry 832, the CONT-36 batch-50 census (13/50 content), the 7-wagon
  blank-face table, the telegram OOM envelope record.
- Engine rebuilt from HEAD: binary sha16 60d377668b5a2649 == the recorded
  CONT-36 final binary (byte-faithful lineage). dooz 90s anchor
  851cc1761a1dfcdf reproduced PRE-WAVE.

## 2. BATCH-50 CENSUS + VISUAL TRUTH (the «۳ لود کامل» criterion)

Full 50-title census at the CONT-36 binary (scripts/cont37_batch50.py,
Pool(2), chunked foreground): 13/50 content rows — the same 13 rows as
CONT-36, EVERY row 3–14x higher content px than the CONT-36 census at the
SAME binary (this container executes more instructions per 90s wall
window; the census titles keep building UI through the window — load-
sensitive rows are NOT byte-stable, honest note for the census contract).

VISUAL VERIFICATION (screenshots viewed, not inferred):

| title | px | verdict |
|---|---|---|
| librecontacts | 1,214,501 | **COMPLETE first-launch UI** — header, hero card, "Back up now", settings rows (Backup folder/Schedule/Retention/Encryption), CSV/VCF, Restore, About/Language. Minor hero-graphic text overlap. |
| bouncy | 1,137,140 | **COMPLETE game main menu** — Select Table + arrows, Unlimited Balls, Start Game/High scores/Help/Preferences/Quit, "Touch to start". |
| balance | 500,130 | **COMPLETE onboarding** — hero card + B icon, Welcome, 4 feature bullets, pager dots, Next. Minor title overlap. |
| wocheneinkauf | 44,227 | **COMPLETE onboarding** — cart icon, title, Your name + Server (API URL) fields, Continue. |
| listai | 73,635 | **COMPLETE reader landing** — "Import FB2, EPUB or PDF books to start reading.", spinner, 3-button toolbar, v1.6. |
| netguard | 324,655 | REAL main screen, but gray mask over the app-list area + buttons over text. PARTIAL. |
| peri | 325,303 | REAL setup screen, heavy double-paint text overlap. PARTIAL. |
| airlyrics | 243,000 | Tabs (Media/Floating/Settings) + EMPTY content. PARTIAL. |
| uturn | 10,782 | Real message text, overflow layout. PARTIAL. |
| starlingmap | 58,612 | The app's honest "Update Android System WebView" fallback (needs WebView for the real UI). |
| fossify_math | 192,398 | DAMAGED (glyph pile-up). |
| fossify_calendar | 192,024 | DAMAGED (black month grid). |
| aat | 5,285 | Splash icon only. |

**The «حداقل ۳ تا برنامه دیگر کامل لود» goal is MET WITH SCREENSHOT
EVIDENCE — 5 APPS render their complete first-launch UI at the standard
census window (librecontacts, bouncy, balance, wocheneinkauf, listai).**
Honest provenance: this is achieved by the SAME binary as CONT-36 — the
delta is container execution speed, NOT a new engine law. No fix claimed
for it; the evidence is the screenshots (run/cont37_batch50/r_*/screenshot.png).

## 3. THE DOOZ BOARD DIVE — F-NEW-541 (caller-site pc identity)

Full instrument battery at the pre-wave binary:

- MINIANDROID_CANVAS_OP_TRACE (200K cap): 32,809 ops recorded. Spatial
  distribution: the board zone y∈[400,1500] receives **ZERO draw
  primitives**; chrome paints (8039 ops y<400 + 24,768 y>1500). **ZERO
  LINE ops in the whole run.**
- DEX decode (scripts/cont37_scan_canvas.py + cont9_dexdump.py):
  - drawLine terminal = Ljt1;.drawLine (the AndroidCanvas subclass; Ljt1;
    IS constructed at Lj7;.e pc=50 — the CONT-10-W6 "canvas never
    constructed" record is SUPERSEDED, the frontier moved).
  - The ONLY app-level drawLine caller = Ly3;.m(J,J,Lg7;)V pc=42 (the
    compose Canvas.drawLine implementation) ← Lgi;.j0 ← Lgl0;.j0 ←
    Lp00;.j0 (iface) ← **Lmy;.i pc=69** (a Function1 lambda — the only
    caller of DrawScope.drawLine in the whole APK).
  - The board's Canvas block lambda = **Lz6;.i** (530 code units,
    DrawScope-carrying, calls Ly3;.m at pc=303; created at 4 sites incl.
    Lcx0;.p — the activity entry).
  - **BOTH Lmy;.i and Lz6;.i have ZERO invocations in the entire run**
    (DRAWWIN traces, METHOD-IN absence): created during composition,
    never dispatched at draw time.
- The live stub trace names the killer:
  `[M3-19-CYCLE] Lho1;.b(Lf90;)Ljava/lang/Object;#532 re-entered while
  active (depth=24) — active-cycle stub, lifetime_calls=9`.
  Lho1;.b = the DRAW-BLOCK DISPATCHER (takes the Lf90; draw block). Its
  key is COMPLETE by F-NEW-306 (obj_dropped=0) — yet the SAME block
  object legitimately re-enters while active: compose dispatches the
  block PER STRUCTURAL POSITION from different walk sites. The
  distinguishing identity — the CALLER'S dispatch-site pc — is invisible
  to any argument-identity key: the F-098/F-NEW-286/F-NEW-297 family's
  invisible-nesting shape, one level deeper (payload identical, site
  differs).

**THE FIX (F-NEW-541)**: `m3_active_key += "~pc" + std::to_string(pc_)` —
the caller's invoke-site pc appended to EVERY M3-19 key. Law: the caller's
dispatch-site pc is computation identity; same-site re-entry remains
same-computation evidence (S22/F-017/F-076 preserved); different-site
re-entry = different structural dispatch → real DEX. Keys strictly more
specific; the guard only fires LESS often; MAX_RECURSION_DEPTH (80)
remains the backstop. "~pc<N>" syntax collision-free.

**EFFECT (honest)**: Lho1;.b stub hits 9 → 6 — the 3 different-site
re-entries now EXECUTE real DEX. The remaining 6 = the same-site (~pc2)
re-entry family — the NEXT face, honestly recorded. **The dooz board
STILL does not paint** (600s rc=0 untraced run: 0 LINE ops, anchor
byte-exact 851cc176) — the destination draw-block dispatch has more
layers. No board-paint claim; the frontier is REFINED and machine-named.

## 4. TELEGRAM — F-NEW-542 (live heap census) + the ENVELOPE REFUTATION

New instrument: MINIANDROID_HEAP_CENSUS — an incremental per-class
allocation histogram (DalvikHeap::note_alloc_class, one cached-branch load
per allocation when unset) + a [HEAP-CENSUS] emitter (rss_kb +
live_objects + alloc_total + top-8 classes) at every 16th progress tick,
bounded 40 emissions. Zero app knowledge; read-only.

**The CONT-36 telegram envelope ("unbounded heap growth, no GC = the
named next structural lever") is REFUTED by live data**:

- live_objects ≈ 10,461 @ insn 1.6M → ≈ 11,721 @ insn 8M (the interpreter
  heap is TINY).
- RSS curve: 2047MB @ 100K insns → 2854MB @ 400K → **FLAT 2855MB
  forever**. The bulk lands during BOOT (load_apk 771ms / parse_dex
  1068ms / initialize_runtime 1088ms / load_classes 1114ms): the parsed
  DEX representation of the 64MB APK inflates ~45× (per-method std::string
  copies × ~700K methods + the engine class tables).
- The heap-GC lever is DEAD — there is no unbounded interpreter-heap
  growth to collect. The REAL levers: (1) boot representation size
  (string interning / lazy bytecode materialization), (2) the per-call
  machinery throughput (tri.resolve 118.4G ticks / em.setup 28.6G — the
  first-frame budget).

**Telegram ADVANCEMENT (post-F-NEW-541)**: at the 22s window the run
reaches `LaunchActivity.onCreate`'s REAL UI draw dispatch
(ActionBar/c4;.dispatchDraw, Components/pa;.onDraw, ActionBar/w;.onDraw,
u4/g;.onDraw — 11 onDraw/dispatchDraw entries) and is BUDGET-bound (F084
halts inside the draw window; F298-KEEP keeps the last complete frame),
rc=1, NO OOM. At 60s the container ceiling (3GB sandbox) kills the
process — rc=137 is the SANDBOX envelope, not engine unboundedness.

## 5. REGRESSION WALL (at the final binary a95136b836bbb0bc)

- Anchors 6/6 BYTE-EXACT: opencalc 63020bc7334048fe / chess 3f7e670759b7c6a8
  / microtimer bbd350b6c14fbd52 / unote 7481e9b468eaa376 /
  tower3d 11a38a5aeeff45a6 / dooz 851cc1761a1dfcdf.
- Games 7/7 EXACT-TO-PIN rc=0: g2048 f43face08299ffc6 / tetris b818a6a7016bea8e
  / snake_deluxe 5235683fc7b1f04b / snakeneon 2617c81c9e72b195 /
  ttt_deluxe db1d633d77b5819a / minicraft e77a073f733255eb /
  gmdice 3891679dff449331.
- Negatives 19/19 PASS (after the run/gatea probe_store regen — the
  recorded recipe; the fresh-container 9/19 is the stale-store artifact).
- Skill selftest 13/13 PASS.
- Batch-50 census: 13/13 content rows at the CONT-36 binary (this wave's
  census; load-varying px honestly noted).

## 6. REGISTRY 832→834 (id-unique)

- F-NEW-541 ROOT-CAUSED-FIXED (the caller-site pc identity law; dooz
  draw-block dispatcher evidence; board frontier honestly refined).
- R-NEW-543 ROOT-CAUSED-FIXED (the F-NEW-542 live heap census instrument;
  the telegram envelope refutation; the levers re-ranked).

## 7. NEXT-WAVE OWNERSHIP

1. dooz: the Lho1;.b same-site (~pc2) re-entry family (6 kills) + the
   destination parent-chain draw walk (why the materialized destination
   nodes never enter the draw dispatch even in a 600s completed run).
2. telegram: the boot representation bulk (2.85GB — string interning /
   lazy bytecode materialization as the memory lever) + the per-call
   machinery (tri.resolve/em.setup) as the first-frame-budget lever.
3. census: the 5 complete-load titles are container-speed-dependent —
   the throughput levers make them robust; the netguard gray-mask and
   peri double-paint defects are the next per-title dives.
4. The F-NEW-542 census instrument generalizes to every blank census
   title (one run names the top allocator).
