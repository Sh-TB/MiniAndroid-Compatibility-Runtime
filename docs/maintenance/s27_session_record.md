# S27 — MASTER CAMPAIGN 3 continuation — session evidence record

HEAD at session start: `79874955` (clean; pushed to origin/main first per user directive).
HEAD at session end: S27 commit (this commit).

## 1. GitHub issue review (user directive: review the 9 open issues, approve the verified)

All 9 open issues audited against repository truth at HEAD; statuses re-confirmed per the
repo's own §29 audit + M8 sync comments; evidence paths verified post-migration
(`docs/testing/CURRENT_HEAD_BASELINE.md`, `docs/research/ROOT_IMPACT_MATRIX.md`,
`docs/compatibility/APK_LOADING_IMPACT_MATRIX.md`, `docs/research/ROOT_LAW_COMPLETENESS_MATRIX.md`,
`docs/evidence/GOLDEN_HELLOWORLD.md`, `docs/evidence/tictactoe_golden/`).

| Issue | Verdict | Action |
|---|---|---|
| #1 EXP-064 | HISTORICAL / primitives FIXED; Telegram externally blocked (artifact) | CLOSED (verified) |
| #2 EXP-065 | FIXED (multi-DEX const-string, battery-covered; F-050d same family) | CLOSED (verified) |
| #3 EXP-066 | FIXED (multi-DEX audit) | CLOSED (verified) |
| #4 EXP-067 | FIXED (resource+AXML+drawable; GATE H pipeline re-proven this session) | CLOSED (verified) |
| #5 EXP-068 | ABSORBED (F-031/F-023 View object-model; tictactoe_golden + gmdice interactive proofs) | CLOSED (verified) |
| #6 EXP-069 | FIXED (canonical tap/click pipeline) | CLOSED (verified) |
| #7 EXP-071 | PROVEN (completed experiment; current boundary = artifact, not code) | CLOSED (verified) |
| #8 evidence anchor | COMPLETE (53 entries; all artifacts committed + path-intact) | CLOSED (verified) |
| #9 MASTER-ROADMAP v3 | LIVING DOCUMENT — S27 frontier comment posted | KEPT OPEN (by design) |

## 2. BATTERY 100% — GATE H root-caused and re-earned (user question: "why 93%, not 100%?")

The battery was 93/94 since S25 because of the pre-existing GATE H failure. ROOT-CAUSED this session:

- **Root (evidence-grade):** the gate's frozen color laws encoded the freeze-era BUGGY rendering.
  The subject app (simplestopwatch) bakes an alpha-0x99 dim into its unfocused theme colors:
  DEX evidence — `ShowTime.focusedColor(I)` = `arg & 0x00FFFFFF | 0xFF000000` (forces opaque ONLY
  for the focused state); the idle branch keeps the raw color alpha; `MyStateDrawable.onStateChange`
  carries the same setAlpha(128/255) state law. The runtime now correctly alpha-blends app colors,
  so the idle render is the app-truth dim: glyph 255 × 153/255 = 153 (#999999), button blue
  #6FA8DC × 153/255 → (66,100,132) — both byte-exact under the floor law.
- **Pipeline integrity re-proven:** bbox-aligned IoU vs the source PNG alpha masks =
  **0.950 (settings) / 0.997 (menu)** (freeze record: 0.959/0.997) with a dim-aware mask threshold
  (>140); >8 distinct colors; 3-run byte-identical determinism unchanged. ARSC density selection →
  PNG decode → BitmapFactory scale → draw all intact.
- **Fix:** GATE H re-earned with dim-aware laws in `scripts/test/run_test_battery.sh`
  (threshold 200→140, blue law 111,168,220 → 66,100,132, full re-earn rationale in-line).
  **ZERO runtime code changed for the re-earn.**
- **Result: battery 94/94 = 100% PASS** (twice: pre-F-096b binary AND final binary).

## 3. R-NEW-329 CLOSED (F-096 + F-096b) — the compose placement gate

Static evidence (androguard, dooz classes.dex): `Landroidx/compose/ui/platform/AndroidComposeView;`
defines BOTH `onMeasure(II)V` and `onLayout(ZIIII)V` — and the runtime dispatched NEITHER:

- F-096 (family): the runtime's real-DEX lifecycle hooks covered inflate-ctor (G11), leaf-only
  onMeasure (F10 — requires the inflate-time `overrides_on_measure` flag), and onDraw (C013).
  AndroidComposeView is created PROGRAMMATICALLY (no inflate ctor hook) → its onMeasure
  (updateRootConstraints + measureOnly) and onLayout (measureAndLayout → root.place(0,0) →
  placeAt → isPlacedByParent → markNodeAndSubtreeAsPlaced — upstream 1.6.7
  MeasureAndLayoutDelegate.kt:523-536, LayoutNodeLayoutDelegate.kt:684-689) never ran →
  every LayoutNode isPlaced=false → InnerNodeCoordinator.performDraw skipped all children
  → 0 canvas ops (the R-NEW-329 frontier).
  **Fix:** `dispatch_view_lifecycle_once(view, l,t,r,b)` — one-time per-node real-DEX
  measure (EXACTLY(rect) specs) + layout (changed=true) dispatch in the render walk, AOSP order.
- F-096b (family): `View$MeasureSpec.getMode` returned the SHIFTED mode (0/1/2). AOSP View.java
  returns the IN-PLACE masked mode (`spec & 0xC0000000` = 0 / 0x40000000 / 0x80000000) — compose's
  `AndroidComposeView.z(I)J` compares `mode == 0x40000000` directly and THROWS
  `IllegalStateException()` otherwise (androguard-verified listing; the ISE was the app-boundary
  unwind after F-096 enabled the dispatch). **Fix:** getMode law corrected to the in-place mask.
- **Post-fix live evidence:** MSPEC diag (getMode 0x40000438/0x40000780/0x40000000/0x40000069 →
  in-place modes), F074 super-dispatch chains through the placement laws
  (node/c, node/l, k0/T k0/g0/D1/s1/m1...), onLayout → measureAndLayout reached.
- **New frontier R-NEW-330 (honest, open):** `IllegalStateException "DepthSortedSet.remove called
  on an unattached node"` at m0/m.c ← i.h (measureAndLayout popEach) ← AndroidComposeView.onLayout
  — a relayoutNodes entry has owner==null (attach propagation / active-cycle interaction).
- **Regression evidence:** dooz frame SHA UNCHANGED `193466ead8fd21d6` ×3 deterministic;
  stopwatch frame byte-identical pre/post F-096+F-096b (`81481eb2aa581c53`); battery 94/94.

## 4. Telegram golden RE-ACQUIRED — K-26 blocker LIFTED

`https://telegram.org/dl/android/apk` now serves the FULL APK again (was the 1.2 MB stub):
- File: `miniandroid/download/exp038_telegram/Telegram.apk` (gitignored — not committed, per §8)
- SHA256: `f5e1192725772960…` == the pinned lost golden (NOT_DONE item 10 / K-26) — EXACT build
- 11,576 zip entries, 5 DEX files, 69,148-byte binary manifest.
- Executed: parse + ApplicationLoader.onCreate + LifecycleRegistry machinery reached;
  honest frontier R-NEW-331 = FragmentManager.ensureExecReady "not been attached to a host"
  (SAME fragment-host family as STTT) + SafeIterableMap$IteratorWithAdditions.next active-cycle
  churn + MessagesController ISE "called wrong accept method". Not yet a rendered frame.

## 5. WhatsApp / TikTok (user-requested attempts)

- WhatsApp: `whatsapp.com/android` serves an HTML page (256 KB, no APK) — official distribution
  is Play-Store-only. HONEST: not directly acquirable.
- TikTok: `tiktok.com/download` HTML page; CDN guess 404 — Play-Store-only. HONEST: not directly
  acquirable.

## 6. S27 app suite (fresh runs, final binary)

| App | rc | Pixels | Screenshot SHA16 |
|---|---|---|---|
| dubrowgn.microtimer_8 | 0 | 1,041,437 non-white (full-frame metric) | c51269309cd14594 |
| de.duenndns.gmdice_8 | 0 | 1,744,539 non-white | 22f3730f452b562c |
| omegacentauri.mobi.simplestopwatch_26 | 0 | 1,944,411 non-white | 81481eb2aa581c53 |
| io.github.yamin8000.dooz_18 | 1 (honest, R-NEW-330) | 802 px placeholder | 193466ead8fd21d6 ×3 det |
| nl.hnogame.tictactoesuperttt_20 (STTT) | 1 (honest, R-NEW-331) | placeholder | eb16ab5c68fa9b6c |

Evidence images committed under `miniandroid/run/s27_suite/` (WebP-class budget: 10-28 KB each).

## 7. Registry

`root_registry.json`: +R-NEW-324..328 (back-filled from S25/S26 worklog records — registry JSON
debt), R-NEW-329 VERIFIED-FIXED (S27), R-NEW-330/R-NEW-331 OBSERVED-FAIL (honest frontiers).
Total: 318 roots.
