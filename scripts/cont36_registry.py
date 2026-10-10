#!/usr/bin/env python3
# cont36_registry.py — add F-NEW-297 to root_registry.json (605 -> 606),
# dedup-checked.
import json

REG = "/home/z/my-project/root_registry.json"
with open(REG) as f:
    r = json.load(f)

ids = [x.get("id") for x in r["roots"]]
assert "F-NEW-297" not in ids, "dedup check failed — F-NEW-297 already present"
assert ids[-1] == "F-NEW-296", f"unexpected tail: {ids[-1]}"

e = {
    "id": "F-NEW-297",
    "status": "ROOT_CAUSED_FIXED",
    "title": "RE-ENTRY IDENTITY CAP STARVES COMPOSE NESTED DRAW SUBTREES + NO "
             "LAYOUT.draw TEXT LAW: (a) the M3-19/F-098/S122 active-cycle-stub "
             "key appended only the FIRST 2 object args after the receiver — the "
             "R8'd Compose CanvasDrawScope Loc0;.c(Ltf;JLmo0;Luv;Lt40;)V is a "
             "REUSED dispatcher called once per SUBTREE with the same canvas/"
             "size/transform and a DIFFERENT draw block (args[4]/args[5], beyond "
             "the cap), so every nested subtree draw collided on one key and was "
             "silently stubbed mid-dispatch ([M3-19-CYCLE] lifetime_calls=32, "
             "depth 109-111): outer roundrects painted (ops=64) and the text "
             "paint chain (TextPainter Lg6 → Layout.draw) NEVER ran (0 "
             "executions in the whole run). (b) android.text.Layout.draw(Canvas) "
             "— the framework entry the Compose paragraph paint funnels into "
             "(AndroidParagraph.paint → layout.paint(nativeCanvas) → Layout."
             "draw) — had NO engine law: a silent void, so even un-stubbed text "
             "paints produced 0 DRAW_TEXT ops. (c) CanvasShadow::handles_class "
             "matched only graphics/Paint — Landroid/text/TextPaint; never "
             "reached the paint-state shadow (setColor swallowed, black text) "
             "(F-NEW-285 gate-vs-dispatch alignment family). (d) ROOT-063's "
             "paint_size probe missed the F-NEW-226 __text_size_px__ field so "
             "layout metrics fell back to 42px.",
    "priority": "P0",
    "layer": "runtime/draw-dispatch-identity + framework/text-layout",
    "root_cause": "FIRST DIVERGENCE PROVEN AT RUNTIME (2026-10-10, run/cont36: "
                  "composeStopwatch v1.9.1 vc1009011 sha256 dbf937ebbe7c0b3d on "
                  "binary 6508a51d01b54280 == CONT-35 record; op-attributed draw "
                  "window MINIANDROID_CANVAS_DRAW_WIN_TRACE): ALL 64 first-frame "
                  "canvas ops from ONE caller Ln3 (the Compose Canvas wrapper), "
                  "roundrect/clip ONLY; Lg6/Lce1-paint/Lr40 (the layer-draw "
                  "lambda containing the only reachable Canvas.drawRenderNode "
                  "call sites: Lr40.I → Lxk0.m) execute ZERO times; the ONLY "
                  "site that invokes a draw block is Loc0.c pc=106 "
                  "(invoke-interface Luv;->I(Loc0;)V — androguard "
                  "scripts/cont36_disasm_loc0.py), and [M3-19-CYCLE] stubs fired "
                  "INTERLEAVED with the draws at depth 109-111 (lifetime 32) — "
                  "the nested subtree draws were stubbed. Probe "
                  "fixtures/fnew297_probe (real toolchain) reproduced the exact "
                  "shape: reused Scope.draw(canvas,J,obj,obj,Runnable) nested "
                  "with a different Runnable — PRE ×3 on 6508a51d01b54280: "
                  "OUTER-EXEC PASS but NESTED-EXEC/TEXT-CALLED FAIL (SGET "
                  "outerRan=1 nestedRan=0 in the run log), SUMMARY FAIL ×3, 0 "
                  "TEXT ops.",
    "fix": "FOUR coordinated generic points, one semantic family, no name "
           "dispatch beyond platform classes: (1) the F-098/S122 instance "
           "identity refinement widens the object-payload cap 2 → 8 — object "
           "args BEYOND the cap are still computation identity (a reused "
           "dispatcher's nestings differ by their block/target args); keys "
           "become strictly more specific, the guard only fires LESS often, "
           "MAX_RECURSION_DEPTH (80) remains the loud backstop "
           "(dalvik_engine.cpp, the M3-19 key construction). (2) "
           "LAYOUT.draw(Canvas) TEXT LAW in the StaticLayout shadow block: "
           "reads the ROOT-063 text/lineHeight/textSize fields + the carried "
           "paintOid, records one DRAW_TEXT op per layout line at the canvas "
           "translate state (first baseline 0.928em ascent — the engine's "
           "FontMetrics model), honest no-op diag for text-less layouts; the "
           "build law stores paintOid on the layout. (3) CanvasShadow::"
           "handles_class gains the generic 'Paint;' suffix row (TextPaint "
           "reaches the paint-state shadow — same gate-vs-dispatch alignment "
           "as F-NEW-285). (4) ROOT-063 paint_size probes __text_size_px__ "
           "(the F-NEW-226 storage). Env-gated draw-window op-attribution diag "
           "(MINIANDROID_CANVAS_DRAW_WIN_TRACE, bounded 400) added as the "
           "evidence instrument.",
    "evidence": "evidence/cont36/DRAW_DISPATCH_FRONTIER.md; runs run/cont36/"
                "{f297_pre_r1..3,f297_post_r1..3,f297_post2_r1..3,"
                "csw_optrace,csw_attr,csw_post297_r1..3,dooz_optrace,"
                "dooz_post297_r1..3,csw_post297_dw}; probe fixtures/"
                "fnew297_probe committed + wired into scripts/w4_build_probes.sh "
                "and scripts/cont35_regression.sh (standing battery). POST ×3 on "
                "054b9bd52fa695fc: 42/0 PASS ×3 with BOTH TEXT ops carrying the "
                "true color/size (F297-TEXT ffcc3333 @60,320; F297-LAYOUT-TEXT "
                "ff2244cc @0,66.8=72×0.928). Target ×3: M3-19 stubs 125→1, "
                "Loc0.c stubs 0, first-frame draw ops 64→236 (nested subtrees "
                "paint again), frame UNCHANGED 9afb2bd2606f303e ×3 (the new ops "
                "are the app's own dark-on-dark shapes — zero render drift); "
                "dooz anchor d602648e8e401895 byte-stable ×3. FULL REGRESSION "
                "ZERO DRIFT at 054b9bd52fa695fc: anchors 24/24 ×3, battery == "
                "CONT-28..35 records EXACTLY (fnew297 42/0), simplecalc ×3 rc=0 "
                "7960bce447ac6d8f.",
    "bounds": "composeStopwatch text is NOT yet visible: with the stub dead the "
              "draw walk goes deeper (236 ops) but the paragraph-paint chain "
              "(Lte1.I/Lod1.I → Lg6.e/f → Lg6.d → Layout.draw) is STILL never "
              "entered — the R8-renamed DrawScope.drawText dispatch to the "
              "TextPainter was not reached in this wave; recorded as the exact "
              "next checkpoint. The per-frame F084 halt face (boot composition "
              "burns the wall-clock budget; per-frame renders halt at "
              "dispatchDraw pc=2 and the frame shows the theme background — "
              "dooz's byte-stable 'anchor' decoded as RGB(250,250,250) theme "
              "background, NOT content) is ROOT_CAUSED but UNPATCHED this wave "
              "(a harness frame-honesty law — PENDING with its own design).",
}
r["roots"].append(e)
r["total"] = len(r["roots"])
with open(REG, "w") as f:
    json.dump(r, f, indent=2, ensure_ascii=False)
print("registry updated:", r["baseline_head"], "roots:", len(r["roots"]))
