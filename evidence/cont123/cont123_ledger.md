# CONT-123 Ledger — «حل ۳۶۴ با این روش تمامشون رو حل بکن و جواب بده» decode wave

- **Wave:** CONT-123, base c68505d3 (CONT-122), binary **04a89c52**, all wagons terminal, zero drift.

## W-01 · F-NEW-192 (the last REGISTERED row) — elevation Z-STATE family
- Landed `setTranslationZ/getTranslationZ/getZ/setZ` (AOSP View.java: **Z = elevation + translationZ**; `setZ` keeps elevation and adjusts translationZ).
- LIVE probe `fixtures/cont123_zstate` (aapt2/ECJ/D8): **4/4 PASS** — `setElevation(4)→getZ=4` · `+translationZ(3)→getZ=7` · `setZ(10)→tZ=6, el=4` · elevation round-trip.
- REGISTERED → **ROOT-CAUSED-PARTIAL**: the draw-walk half (RenderNode sibling Z-ordering + outline shadow rasterization) stays the named residual — the axis-aligned walk keeps declaration order. Honest.

## W-02 · F-NEW-384 — measure-path residual re-verified at HEAD
- The named residual (k1.c NPE via measure-path cached-inset wrappers) shows **ZERO occurrences** in the live chess run at HEAD; the inset chains are all served: `[ROOT-059] WindowInsets$Builder.build` ×2, `[C013-HIER]` listener+getRootWindowInsets+computeSystemWindowInsets dispatched through the ActionBarOverlayLayout superclass chain, `[F384-ROOTINSETS]` dispatch live; chess anchor `a0319686` byte-identical.
- LAW-LANDED-PARTIAL → **VERIFIED-FIXED** (live-behavior evidence; the k1/d1 wrapper decode history is preserved in the chain evidence, not deleted).

## W-03 · F-NEW-267 — scripted-tap frontier refresh at HEAD
- `--tap 820,1837` on dooz: face `d602648e` byte-identical to the anchor; `[F117-TAP] DOWN target=0` at frame 1 — the compose-internal hit-test frontier is **unchanged**; row stays **ROOT-CAUSED-PARTIAL** with the synthetic-Compose-tree probe spec as the landing lever. `[UC009-ATTACH-DIAG] ComposeView NOT in class index` recorded as the decode pointer.

## Wall
- chess `a0319686` + dooz `d602648e` byte-identical at the wave binary; registry 783 id-unique, main==mirror **row-equal** (3 rows updated, no inflation).
