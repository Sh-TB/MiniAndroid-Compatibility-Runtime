#!/usr/bin/env python3
# cont44_registry.py — CONT-44 registry update ("complete result" wave):
#  (1) F-NEW-306 (P0) -> ROOT_CAUSED_FIXED: the M3-19 active-cycle stub no
#      longer fires on INCOMPLETE-payload keys; the csw healthy face
#      3442d9a9dc0fa0f9 regained byte-exact x3. Decode correction recorded:
#      the failing structure is the kotlinx persistent-hash TRIE builder
#      Lch1;.j (Lgi0;=DepthSortedSet WAS allocated — the CONT-43 note's
#      premise corrected by the CONT-44 alloc-trace decode).
#  (2) F-NEW-305 -> ROOT_CAUSED_FIXED: the ActionBarOverlayLayout inset law
#      in LayoutInflater::measure_layout (bar at paddingTop, content below
#      it with an EXACTLY re-measure; theme-resolved actionBarSize floor —
#      never a constant). tananaev fix face 5f7e0114c3bfd6b5 rc=0 SUCCESS
#      (content 0 -> 126 px below the band); simplecalc = the second
#      appcompat host fixed by the same law (e847ca0346708f07, layout
#      intact +126). Row glyphs recorded as the new root F-NEW-308.
#  (3) F-NEW-307 -> ROOT_CAUSED_FIXED (measurement-only): the census
#      APP_DRAW_OPS missing-stage is gated on pixel evidence + kept-frame
#      attribution fields (draw_budget_halt / presentation /
#      kept_prior_app_draw_ops); dooz180 sha byte-identical
#      6841d52a20e6597e x4, verdict flips to REAL_APP_CONTENT -> run
#      Status SUCCESS (the 21-P0 law's honest upgrade).
#  (4) F-NEW-308 appended (P1): tananaev preference-row TextView glyphs
#      never paint (0 dark px in the rows zone while the rows container's
#      own background paints) — the visible-rows leg's remaining face.
import json

P = '/home/z/my-project/root_registry.json'
d = json.load(open(P))
ids = {r.get('id') for r in d['roots']}
for need in ('F-NEW-305', 'F-NEW-306', 'F-NEW-307'):
    assert need in ids, f'{need} missing — wrong base'
for fresh in ('F-NEW-308',):
    assert fresh not in ids, f'{fresh} already present — dedup check'

# ── (1) F-NEW-306 -> FIXED ─────────────────────────────────────────────
for r in d['roots']:
    if r.get('id') == 'F-NEW-306':
        r['status'] = 'ROOT_CAUSED_FIXED'
        r['binary'] = 'b067df784adfa727'
        r['title'] += (
            ' CONT-44 FIX (decode-corrected + fixed): the alloc-trace decode '
            '(scripts/cont44_a_decode*.py, run/cont44/csw_pre) corrected the '
            'premise — Lgi0; (androidx.compose.ui.node.DepthSortedSet, '
            'Lg91;->TreeSet) WAS allocated pre-measure and the Laj0;.n '
            'isEmpty site was not the thrower; the REAL failure is the '
            'kotlinx.collections.immutable persistent-hash TRIE builder '
            'Lch1;.j(I,Object,Object,I,Object,Object,I,Lzv;)Lch1; — its '
            'only allocation in the whole run was the EMPTY root singleton '
            'because all 3 node-building calls were cycle-STUBBED '
            '([M3-19-CYCLE] lifetime_calls=2, depths 23/28), so the trie '
            'never grew and Lch1;.s pc=4 (nodeAt) read a null cell -> '
            'getClass NPE -> ComposerImpl.recompose cascade -> Lh4;.onMeasure '
            'catch-all. The key carried 2 of 4 objects + 2 of 3 ints: the '
            'static arms\u2019 2-object/2-primitive caps dropped args[5], '
            'args[7] (the Lzv; owner) and args[6] — the RECURSION SHIFT, '
            'exactly the part distinguishing collision-path levels. Zero '
            'REC-MISS on the path: the stub\u2019s same-computation CLAIM '
            'was false. LAW (dalvik_engine.cpp try_recursive_invoke): a key '
            'that dropped ANY argument identity — non-null objects beyond '
            'the cap, primitives beyond the cap, CLASS_REFs beyond the cap, '
            'or null positions (uncapturable positional identity) — is NOT '
            'same-computation evidence; real DEX executes, loudly traced '
            '[M3-19-OPEN] (3 firings in the POST run, 0 [M3-19-CYCLE] on '
            'Lch1;). Generalizes F-NEW-286 from "no payload captured" to '
            '"payload capture incomplete"; [RECURSION-LIMIT] depth-80 '
            'remains the backstop. POST: csw 3442d9a9dc0fa0f9 x3 REGAINED '
            '(the pinned healthy face, NOT re-baselined); anchors 27/27 x3 '
            'byte-identical; probes == records exactly; frag_tx 12/0, '
            'notif_builder 56/0; simplecalc moved by F-NEW-305 (below).')
        r['regression'] = (
            'ZERO DRIFT at b067df784adfa727: anchors 27/27 x3 byte-identical '
            '(dooz 31ddd4d5b8e6d18e, microtimer da73010a37dd0189, unote '
            '4f1a9e4e8f64fae8, gmdice f3b483fe7b7cf51b, opencalc '
            'a976d2f9fb675cb3, tttdeluxe af6094295ecb50e3, flappycow '
            '13cf47464d9787f4, g2048 59ca1526611c4622, tananaev re-pinned to '
            'the F-NEW-305 fix face 5f7e0114c3bfd6b5 x3); target csw '
            '3442d9a9dc0fa0f9 x3 REGAINED; dooz180 6841d52a20e6597e x3 '
            'byte-identical; probes == records exactly (fcol 140/0, f259 '
            '49/0, f259g 84/7, f266 42/0, f268 96/0, fnew253 147/0, fnew286 '
            '10/0, fnew289 28/0, ckey 105/0, cpipe 119/0, fnew302 48/24 '
            'documented, fnew252 56/0, fnew290..296 == records, fnew297 '
            '42/0, fnew298 19/0 KEEP=5 corner=PASS); frag_tx_probe 12/0; '
            'notif_builder_probe 56/0; simplecalc re-pinned to the F-NEW-305 '
            'fix face e847ca0346708f07 x3 rc=0 (the same honest re-pin '
            'disposition as tananaev).')

# ── (2) F-NEW-305 -> FIXED ─────────────────────────────────────────────
for r in d['roots']:
    if r.get('id') == 'F-NEW-305':
        r['status'] = 'ROOT_CAUSED_FIXED'
        r['binary'] = 'b067df784adfa727'
        r['title'] += (
            ' CONT-44 FIX: (a) the CONT-43 "bar measured height 105" premise '
            'was corrected — 105 was the generic-else 40dp default floor, '
            'the bar actually measured 0 (the DEX measure chain degenerates: '
            'ViewGroup.measureChildWithMargins has no engine shadow yet, '
            '[DEX-MEASURE] ActionBarContainer.onMeasure -> 1080x1920 demoted '
            '-> native re-measure 1080x0; no DEX-LAYOUT dispatch at all). '
            '(b) LAW (src/resources/layout_inflater.cpp measure_layout, '
            'class-dispatched, zero app knowledge): the ActionBarContainer '
            'child lays out at (paddingLeft, paddingTop) with its real '
            'measured size; every other child lays out at top = paddingTop '
            '+ effective bar height + lp.topMargin with an EXACTLY(ch - bar) '
            'second-pass re-measure (fixed-height content keeps its own '
            'height); (c) the bar-height floor resolves the THEME\u2019s '
            'actionBarSize (arsc find_id attr/actionBarSize -> '
            'resolve_theme_attr_typed -> complex_to_dimension_pixel_size; '
            'framework android:actionBarSize 0x010102EB fallback) — the '
            'exact attr the appcompat DEX reads in ActionBarOverlayLayout.'
            '<init>; never a constant. tananaev POST: content 0 -> 126 px '
            '(48dp x 2.625), bar band 1080x126, rows 126..346, rc=0 SUCCESS '
            '5f7e0114c3bfd6b5 x3 (re-pinned). simplecalc = the SECOND '
            'appcompat host the law fixed the same way: content +126, '
            'display+pad layout intact, e847ca0346708f07 x3 rc=0 '
            '(re-pinned; the old face 7960bce4 had the calculator top row '
            'under the band). Anchors without ActionBarOverlayLayout '
            '(opencalc/microtimer/unote/gmdice verified 0 ABOL lines) are '
            'structural no-ops — byte-identical. SCOPE: non-overlay path; '
            'row glyphs are F-NEW-308.')
        r['probe'] = ('tananaev tree: ContentFrameLayout#379 (0,126) '
                      '1080x1794, rows#456 (0,126) 1080x220, '
                      'ActionBarContainer#382 (0,0) 1080x126; '
                      'run/cont44/tan_post2; simplecalc tree: main LL#166 '
                      '(0,126), buttons y>=695 intact')

# ── (3) F-NEW-307 -> FIXED ─────────────────────────────────────────────
for r in d['roots']:
    if r.get('id') == 'F-NEW-307':
        r['status'] = 'ROOT_CAUSED_FIXED'
        r['binary'] = 'b067df784adfa727'
        r['title'] += (
            ' CONT-44 FIX (measurement-only, rendering bytes unchanged): '
            '(a) the census APP_DRAW_OPS missing-stage is gated on PIXEL '
            'EVIDENCE (app_draw_ops==0 && app_owned_px==0 && no dialog) — '
            'the op ledger counts per-ViewShadow paint sites; the Compose '
            'paint path reaches the framebuffer through '
            'dispatch_custom_view_draw/the CDW recorder which the ledger '
            'does not cover, so presented app pixels outrank the empty '
            'ledger; (b) kept-frame attribution: the F-NEW-298 keep path '
            'now tags draw_budget_halt=true, kept_prior_frame=true and '
            'carries the kept frame\u2019s ledger ('
            'last_presented_app_draw_ops_) as kept_prior_app_draw_ops — the '
            'census no longer reads an aborted walk\u2019s ledger against '
            'the kept frame\u2019s pixels (dooz180 final frame ops '
            '1189,604,604,415,0,0). POST: dooz180 6841d52a20e6597e x3 gate '
            '+ x1 = x4 byte-identical, verdict REAL_APP_CONTENT, run '
            'Status SUCCESS (the 21-P0 law\u2019s honest upgrade — the '
            'exact flip the CONT-43 gate comment predicted). Boot cost '
            '(~25M insns / ~80 s wall) stays the perf frontier.')

# ── (4) F-NEW-308 (new root) ───────────────────────────────────────────
d['roots'].append({
  "id": "F-NEW-308",
  "title": ("tananaev v1.10 preference-row glyphs never paint: after the "
            "F-NEW-305 inset fix the rows sit at their honest AOSP "
            "positions (rows#456 at y=126, 1080x220, 4 REAL rows at "
            "1080x44 pitch parsed from the app's own res/xml) but the "
            "frame still has ZERO dark pixels in the rows zone — the rows' "
            "TextView glyphs (real titles like 'Ongoing notification — "
            "Calculator Notification can not be dismissed') never reach "
            "the rasterizer, while simplecalc's Button labels ('mod', "
            "'^', '√', 'C') DO paint on the same binary. The delta is the "
            "View kind + ancestry: fragment-drain-created "
            "LinearLayout/TextView rows (no DEX onDraw override recorded) "
            "vs the inflater-built Button path. Decode+fix owned next "
            "(the fragment/preference family's slice 3): which paint path "
            "(draw_text_into / onDraw dispatch / text_color provenance) "
            "skips the fragment-hosted TextView rows."),
  "status": "OBSERVED",
  "priority": "P1",
  "layer": "framework/fragment-text-paint",
  "evidence": "evidence/cont44/CONT44_COMPLETE_RESULT.md",
  "probe": ("run/cont44/tan_post2 pixel census: rows zone "
            "(y=126..346) dark px = 0; row titles present in the tree "
            "text dump; simplecalc Button glyphs paint on the same binary"),
  "binary": "b067df784adfa727",
})

d['count'] = len(d['roots'])
d['total_roots'] = len(d['roots'])
d['generated'] = 'CONT-44 session'
json.dump(d, open(P, 'w'), indent=1, ensure_ascii=False)
print("registry:", len(d['roots']),
      "roots; F-NEW-306/305/307 -> ROOT_CAUSED_FIXED; F-NEW-308 appended")
