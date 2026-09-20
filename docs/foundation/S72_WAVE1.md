# S72 — SCREENSHOT-FIRST FOUNDATION CLOSURE (Wave 1: Forensic Re-run)

Session date: 2026-09-20. Start HEAD: 1271b869 (S71) → this wave lands on top.
Directive: minimize analysis, maximize real APK execution + verifiable
screenshots. Rule 0 (S71) honored: no fix without a first-divergence.

## 1. Push debt cleared (S64 carry-over)

- 11 pending commits (S68..S71 + session records) pushed to
  `github.com/Sh-TB/MiniAndroid-Compatibility-Runtime`:
  `289e33d3..82156d03 main -> main` (remote verified = local HEAD).
- PAT passed via one-shot env var; NEVER written to any file; unset after
  use; repo's own fail-closed secret-guard hook PASSED; manual scan of the
  pushed range: only a doc mention of the scan procedure itself (no tokens).

## 2. REAL APP EXECUTION DASHBOARD (baseline, fresh s71_live traces + re-runs)

KPI measured at PIXEL level (nonwhite/2073600), not PNG existence:

| APK | nonwhite | state |
|---|---|---|
| bouncy | 100% | fully painted (Canvas app) |
| microtimer | 50.2% | real UI |
| unote | 11.4% | real UI |
| opmt | 10.3% | real UI |
| gmdice | 8.8% | real UI |
| stopwatch | 1.1% | empty window (correct: see §3) |
| tictactoe | 0.0% | blank — GL family |
| dooz | 0.0% (197px) | blank — trie corruption chain (§4) |
| fishrings | 0.0% | window law OK now; paint gap (§5) |
| tripeaks | 0.0% | app-specific (S71: WebView splash), unchanged |

Interactive: TicTacToe tap path exists from earlier sessions; not re-proven
this wave (defers to Rule 11 — next wave target).

## 3. stopwatch — ROOT-CAUSED: service-only app (NOT an engine bug)

Manifest declares **NO `<activity>`**: only StopwatchTile (QS Tile service),
StopwatchService (foreground), androidx startup provider. Engine correctly
found no launch target → 1-node tree. Real Android has no full-screen UI
either (UI = tile + notification).

NEW FOUNDATION FAMILY (registered): **Service launch/lifecycle**
(Service.onCreate/onStartCommand/startForeground) — zero support in engine
today (grep-verified). Stopwatch's honest screenshot target = notification
surface, blocked on that family.

## 4. dooz — deep chain root-caused, instrumentation landed (fix deferred)

Evidence chain (all deterministic, all on current binary):

- Escaping exception: NPE "arraycopy: null array argument" @ `Lid;.K` pc=3
  (unhandled) → EXC-PROPAGATE out of MainActivity.onCreate → app frame
  unwind → Compose never paints (fb=197px). Upstream law (OpenJDK
  System.arraycopy NPE) is CORRECT — the defect is the null producer.
- [AC-NULL] probe (new) isolated the ONE null site:
  `Lid;.K ← Lid;.M ← Lqe1;.k ← Lrz1;.l ← Lrz1;.l ← Lrz1;.m ← Lh51;.putAll ←
  Lnb0;.f0` — androidx compose PersistentHashMapBuilder.putAll trie walk.
- [PARAM-TRACE] (existing tool) on `Lrz1;.l` proved entry #49 receives
  `this = NULL` (t=8) via the `invoke-virtual/range` recursion at pc155,
  while entries #1..#48 received real nodes. Null `this` propagated from
  `s(I)` (child nav) returning null → move-result-object v0 → recursion.
- CONFIRMED ENGINE LAW GAPS (the corruption is engine-made, not upstream):
  1. **invoke-virtual on null receiver does NOT throw NPE** (ART throws
     before dispatch) — the engine executes real DEX bodies with null
     `this`, silently (matches the 12× `<unknown>.getClass` STUBBED
     entries: getClass served on null receivers at `Lid;.K` pc0).
  2. F-075 move-result-object law converts INT32(0)/VOID but NOT NULL_REF
     produced by a prior silent path — null propagates into `this` slots.
  3. Once null enters the trie, every read continues silently
     (iget-object on null-this → typed null) until the arraycopy NPE fires
     at the WRONG site with the WRONG attribution.
- API dispatch is otherwise healthy: 2080 IMPLEMENTED / 77 STUBBED of 2157
  bridge calls; ViewTree reaches 39 real compose nodes; Lho 1080x1920.
- REC-MISS ≠ failure: [REC-MISS] lines (Enum.<init> ×93 etc.) are DEX-lookup
  logs for framework classes; the bridge serves them (Enum F-020 law
  verified present, F-137 ancestry verified). No action on those lines.

Registered as **F-141 (OPEN, P0): ART null-receiver invoke NPE law +
null-propagation hardening** — needs its own implementation wave with the
corpus battery (a blanket law changes every APK; must be measured).

## 5. fishrings — window law already fixed; remaining root = ImageView paint

- S71-era trace was STALE for this behavior: on the CURRENT binary the
  splash → GameActivity transition WORKS: startActivity → GameActivity
  onCreate → setContentView(int) → [U007-INFLATE] root_id=29 views=44 →
  render pump switches to node=29 (children=43) with REAL geometry
  (ImageViews 788x788 grid, bottom bar at y=1747).
- Remaining first divergence: the game board is RelativeLayout+ImageViews;
  the pump visits every node but NOTHING paints (0 px). The inflate stats
  show `strings=0 ids=0` — the ImageView src drawable refs never became
  bitmap-backed nodes (image_resource_id unresolved) → ImageView paint
  path has no bitmap → 0 px. Engine HAS bitmap foundation (S68 W1) and
  ImageView drawable painting (hello_widgets proof) — the gap is the
  LAYOUT-INFLETTED src→bitmap resolution law.
- Registered as **F-142 (OPEN, P1): layout-inflated ImageView src/drawable
  → Bitmap resolution + paint**. Best KPI/root ratio: fishrings is a real
  canvas game; fix → real screenshot next wave.

## 6. tictactoe (deferred, root-caused enough)

libGDX app: `EGLContext.getEGL` REC-MISS → checkGL20 fails →
GdxRuntimeException node in tree. GL/EGL family = large; per Rule 8 the
GL path has no real execution without a surface — deferred behind the
cheaper roots above (no priority by raw counts anywhere).

## 7. Tooling added this wave (all env-gated, render-neutral, reusable)

- `MINIANDROID_ARRAYCOPY_TRACE=1` — [AC-NULL] which arg is null + 8-frame
  stack snapshot + [AC-NULL-FRAME] deep register/heap-field dump of the 4
  frames below the arraycopy caller (uses new read-only
  `CallStack::peek_frames_top_first()` — deep-copy, no dangling pointers).
- `MINIANDROID_NULLFIELD_TRACE=<field|*>` — [NULLFIELD] field reads where
  the heap object has NO entry (iput never ran) + [IPUT-DROP] the write-side
  twin: iput-object falling into the legacy silent-drop path.
- scripts/s72_disasm_lid.py — androguard disasm helper (dvm import path).

## 8. FOUNDATION STATUS

NOT COMPLETE — with the honest note that this wave MOVED the frontier:
4 of 4 blank-app first divergences are now root-caused with machine
evidence (vs. S71: 2 classified, 2 unproven). Zero implementation landed
in the runtime this wave by design (Rule 0 of the directive: first root
selection came FROM this evidence); the selected first roots are F-142
(fishrings paint, smallest→screenshot) then F-141 (dooz null laws,
deepest→compose family).
