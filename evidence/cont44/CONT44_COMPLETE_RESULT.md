# CONT-44 — Complete Result: the three recorded frontiers closed, zero drift

Binary chain: `3dab3038c222031e` (CONT-43) → `94f49a9a338d0879` (F-NEW-306 only)
→ `3d77c6e55c6c8ab2` (+F-NEW-307) → **`b067df784adfa727`** (final: +F-NEW-305).
Baseline HEAD `900efcbf` (CONT-43 + checkpoint), registry 615 → **616**.

## 1. F-NEW-306 (P0) — composeStopwatch content REGAINED, root-caused and fixed

**Decode (scripts/cont44_a_decode*.py, run/cont44/csw_pre, MINIANDROID_ALLOC_TRACE):**
the CONT-43 premise was corrected — `Lgi0;` (androidx.compose.ui.node.
DepthSortedSet, `Lg91;`→TreeSet) **was** allocated pre-measure; the real failure
is the kotlinx.collections.immutable persistent-hash **trie builder
`Lch1;.j(I,Object,Object,I,Object,Object,I,Lzv;)Lch1;`**: its only allocation in
the whole run was the EMPTY root singleton (`[ALLOC-TRACE] obj#664 Lch1;`,
buffer `d = new Object[0]`) because all 3 node-building calls were
**cycle-stubbed** (`[M3-19-CYCLE] lifetime_calls=2`, depths 23/28). The trie
never grew → `Lch1;.s` pc=4 (nodeAt) read a null cell → `getClass` NPE →
ComposerImpl.recompose cascade → `Lh4;.onMeasure` catch-all → boot degrades
4.4M → 600k insns. The key carried **2 of 4 objects + 2 of 3 ints**: the static
arms' 2-object/2-primitive caps dropped `args[5]`, `args[7]` (the `Lzv;` owner)
and `args[6]` — **the recursion shift**, exactly the part distinguishing
collision-path nesting levels. Zero REC-MISS on the path: the stub's
same-computation claim was false. Verdict: REAL-MISSING-LAW (not an
interleaving-contract violation) — the discriminating evidence is the
same-binary trace itself (stub fired on a progress-bearing, upstream-bounded
re-entrancy; no shadow gap anywhere on the chain).

**LAW (src/dex/dalvik_engine.cpp, try_recursive_invoke):** an active-cycle key
that dropped ANY argument identity — non-null objects beyond the cap, primitives
beyond the cap, CLASS_REFs beyond the cap, or null positions (uncapturable
positional identity) — is **not same-computation evidence**; real DEX executes,
loudly traced `[M3-19-OPEN]` (3 firings in the POST run, 0 `[M3-19-CYCLE]` on
`Lch1;`). Generalizes F-NEW-286 from "no payload captured" to "payload capture
incomplete". `[RECURSION-LIMIT]` depth-80 remains the loud backstop.

**POST:** csw `3442d9a9dc0fa0f9` ×3 REGAINED (the pinned healthy face — content
restored byte-exactly, NOT re-baselined down).

## 2. F-NEW-305 (P1) — the action-bar inset law (tananaev rows below the band)

**Decode (run/cont44/tan_pre, tan_decode):** the CONT-43 "bar measured height
105" was corrected — 105 was the generic-else 40dp **default floor**, not a
measurement. The bar actually measured **0**: the appcompat DEX onMeasure chain
degenerates (`ViewGroup.measureChildWithMargins` has no engine shadow →
`[DEX-MEASURE] ActionBarContainer.onMeasure → 1080x1920` demoted → native
re-measure `1080x0`; zero DEX-LAYOUT dispatch). ContentFrameLayout content built
at y=0; rows rendered under the (empty) bar band.

**LAW (src/resources/layout_inflater.cpp, LayoutInflater::measure_layout):**
class-dispatched, zero app knowledge —
- the **ActionBarContainer** child lays out at (paddingLeft, paddingTop) with
  its real measured size;
- every other child lays out at `top = paddingTop + effective_bar_height +
  lp.topMargin` with an `EXACTLY(ch − bar)` second-pass re-measure (fixed-height
  content keeps its own height — only match_parent shrinks by the inset);
- the bar-height **floor resolves the THEME's actionBarSize** (`arsc.find_id("",
  "attr", "actionBarSize")` → `resolve_theme_attr_typed` → reference deref →
  `complex_to_dimension_pixel_size`; framework `android:actionBarSize`
  0x010102EB fallback) — the exact attr the appcompat DEX reads in
  `ActionBarOverlayLayout.<init>`; **never a constant**;
- scope: the non-overlay path (no byte-exact anchor uses ActionBarOverlayLayout
  except simplecalc — see below).

**POST:** tananaev content 0 → **126 px** (48dp × 2.625), bar band 1080×126,
rows `126..346`, rc=0 **SUCCESS** — fix face `5f7e0114c3bfd6b5` ×3 (re-pinned).
**simplecalc = the SECOND appcompat host the law fixed the same way**: content
+126 with the display/pad layout intact — `e847ca0346708f07` ×3 rc=0
(re-pinned; the old face `7960bce4` had the calculator's top row under the
band). Anchors without ActionBarOverlayLayout (opencalc / microtimer / unote /
gmdice verified 0 ABOL lines; dooz / csw / ttt / flappy / g2048 all MATCH) are
structural no-ops — byte-identical. Remaining face: **F-NEW-308** (the rows'
TextView glyphs never paint — 0 dark px in the rows zone while simplecalc's
Button labels paint on the same binary).

## 3. F-NEW-307 (P1) — the census attribution (measurement-only)

**Decode (run/cont44/dooz180, census classifier in
ExecutionEngine::stage_render_frame_impl):** the final dooz180 frame's draw is
killed by the F084 wall-budget halt (154 WALL-STOPs) → ops sequence
`1189, 604, 604, 415, 0, 0` → the F-NEW-298 frame-honesty law SKIPS
presentation (the PNG holds the prior frame) while the census describes the
**aborted** frame (app_draw_ops=0) → `first_missing=APP_DRAW_OPS` (checked
before the pixel stage) → `VIEWTREE_NO_APP_PIXELS` against the kept scaffold's
pixels. Additionally the Compose paint path reaches the framebuffer through
`dispatch_custom_view_draw` / the CDW recorder, which the per-ViewShadow op
ledger does not cover.

**LAW (src/runtime/execution_engine.{h,cpp}):**
- the `APP_DRAW_OPS` missing-stage is gated on **pixel evidence**
  (`app_draw_ops==0 && app_owned_px==0 && !dialog_content_rendered`) —
  presented app pixels outrank an empty ledger;
- **kept-frame attribution**: the F298-KEEP path tags `draw_budget_halt=true`,
  `kept_prior_frame=true` and carries the kept frame's ledger
  (`kept_prior_app_draw_ops` from `last_presented_app_draw_ops_`) — the census
  JSON gains `draw_budget_halt` / `presentation` / `kept_prior_app_draw_ops`.

**POST:** dooz180 `6841d52a20e6597e` ×3 gate + ×1 = **×4 byte-identical**,
verdict **REAL_APP_CONTENT**, run **Status SUCCESS** (the 21-P0 law's honest
upgrade — the exact flip the CONT-43 gate comment predicted). Rendering bytes
unchanged by construction. Boot cost (~25M insns / ~80s wall) stays the perf
frontier.

## 4. Full gate at b067df784adfa727 — ZERO DRIFT

- **anchors 27/27 ×3 byte-identical** (81 runs): dooz `31ddd4d5b8e6d18e`,
  microtimer `da73010a37dd0189`, unote `4f1a9e4e8f64fae8`, gmdice
  `f3b483fe7b7cf51b`, opencalc `a976d2f9fb675cb3`, tttdeluxe
  `af6094295ecb50e3`, flappycow `13cf47464d9787f4`, g2048 `59ca1526611c4622`,
  tananaev **re-pinned** to the fix face `5f7e0114c3bfd6b5` ×3;
- **target csw ×3 `3442d9a9dc0fa0f9` REGAINED**;
- **dooz180 ×3 `6841d52a20e6597e`** (byte-identical);
- **probes == records exactly**: fcol 140/0, f259 49/0, f259g 84/7, f266 42/0,
  f268 96/0, fnew253 147/0, fnew286 10/0, fnew289 28/0, ckey 105/0, cpipe
  119/0, fnew302 48/24 (documented), fnew252 56/0, fnew290..296 == records,
  fnew297 42/0, fnew298 19/0 KEEP=5 corner=PASS; **frag_tx_probe 12/0**,
  **notif_builder_probe 56/0**;
- **control simplecalc ×3 `e847ca0346708f07`** rc=0 (the F-NEW-305 fix face,
  re-pinned with the same honest disposition as tananaev).

The only frames that moved are the two the inset law FIXED (tananaev,
simplecalc) — both re-pins carry the fix-face argument in the gate script.

## 5. Cross-app impact of the white-screen fix set (the user's question)

Delivered in `evidence/cont44/CROSS_APP_IMPACT.md` (CONT44-C audit): 32-app
corpus classified by static DEX scan — Fragment ×13, Preference ×9, AppCompat
×10, Compose ×3, View-only ×14; **19/32 in the benefit blast radius** of the
CONT-42..44 laws; the 6 untouched View-world games carry byte-identical ×3
proofs. CONT-44 adds two more concrete beneficiaries: **simplecalc** (the inset
law, second host) and every appcompat fragment-host app that will inherit the
F-NEW-305 geometry. 11 recommended new gates listed (notes/sudoku secuso,
chess_jwtc, klondike, chessclock, bouncy, opmt, muellerma.stopwatch,
emmanuelmess.tictactoe, dooz toplevel variant, telegram/forkgram long-horizon).

## 6. Artifacts

- Runs: `run/cont44/` (csw_pre/csw_post_r1..3, tan_pre/tan_post/tan_post2,
  dooz180_post, anchor_*, probe_frag_tx, probe_notif_builder),
  `run/cont37/regression/` (the full gate).
- Decode scripts: `scripts/cont44_a_decode{,2,3}.py`, `scripts/cont44_b_*.py`,
  `scripts/cont44_c_scan.py`, `scripts/cont44_registry.py`.
- Fixes: `src/dex/dalvik_engine.cpp` (F-NEW-306), `src/resources/layout_inflater.cpp`
  (F-NEW-305), `src/runtime/execution_engine.{h,cpp}` (F-NEW-307).
- Gate: `scripts/cont37_regression.sh` (tananaev/simplecalc re-pins + the csw
  target comment updated to REGAINED).
