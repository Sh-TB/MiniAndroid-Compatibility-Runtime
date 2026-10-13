#!/usr/bin/env python3
"""cont61_registry.py — CONT-61 W1: append F-NEW-344 (the compose text
intrinsic leg — Layout.getDesiredWidth) and sync the counters."""
import json, datetime

PATH = "/home/z/my-project/root_registry.json"
d = json.load(open(PATH))

entry = {
    "id": "F-NEW-344",
    "status": "ROOT-CAUSED-FIXED",
    "priority": "P1",
    "layer": "dex/Layout.getDesiredWidth + fonts/TextShaper",
    "title": (
        "The compose text INTRINSIC leg never measured: AndroidTextLayoutIntrinsics "
        "(dooz v23 R8: Lsk0;.c x2) asks Layout.getDesiredWidth(text, paint, textDir, "
        "firstPassMode) for the wrap-content paragraph width (the compose Constraints "
        "FocusInterceptor encodes maxWidth=Infinity as all-zero bits - the WRAP-CONTENT "
        "normal state, measured [F344-PCTOR] Lj7.<init> a4 lo32=0). The engine had NO "
        "getDesiredWidth law - the typed-default answered 0.0 -> TextDelegate width 0 -> "
        "StaticLayout.Builder.obtain received width=0 (a4_type=1 a4_int=0, [F298-OBTAIN] "
        "extended) -> every compose StaticLayout corpus-wide built WIDTH=0 (pre-fix "
        "[ROOT-063] width=0 at BUILD time) -> AndroidParagraph.paint (Lj7.e) "
        "clipRect(0,0,0,h) -> Canvas.getClipBounds answered the EMPTY clip "
        "([F298-GCB] clip=540,59,540,108 = l==r) -> the compose 1.11 paint cull "
        "(if (!canvas.getClipBounds(r)) return) skipped Layout.draw -> SLDRAW 0, zero "
        "exceptions, zero text pixels."
    ),
    "root_cause": (
        "Decode chain (all read-only env-gated probes at HEAD e63feef5+c1e4b9dd): "
        "(1) [F343-SL] census: StaticLayout measurement getters arrive (getLineCount/"
        "getLineBottom/getLineBaseline x14...) but method=draw NEVER dispatches. "
        "(2) [DRAWWIN-BRIDGE]: the walk = Lj7;.e save -> Lrw1;.a getLineBottom -> "
        "clipRect -> getClipBounds -> restore (draw missing between gate and restore). "
        "(3) [F298-GCB]: the clip answer (540,59,540,108) is l==r EMPTY (the worklog "
        "record mis-read it as 540x108 w-h). (4) [F298-OBTAIN] extended: width arg "
        "a4_type=1 INT32 VALUE=0 - compose GENUINELY passed zero (caller Lxd1;.e; "
        "chain ^1<Lrw1;.<init> ^2<Lj7;.a> ^3<Lj7;.<init>). (5) [F344-PCTOR]: the "
        "paragraph ctor constraints long lo32=0 = compose Infinity encoding - the "
        "wrap-content normal state, NOT an engine long-corruption. (6) [F344-LAYOUT]: "
        "Landroid/text/Layout;.getDesiredWidth DOES arrive (argc=4, caller Lsk0;.c) "
        "and had no law. FIX (one generic site, zero app knowledge): the "
        "getDesiredWidth law shapes the text with the SAME pipeline the Canvas "
        "drawText replay uses (fonts::TextShaper FreeType/HarfBuzz real advances) at "
        "the paint's recorded __text_size_px__ (the F-NEW-226 identity store, the "
        "same probe the build law consumes) - measured geometry and painted pixels "
        "stay one source of truth. Both overloads (2-arg/4-arg), both CharSequence "
        "payload forms (STRING_REF + OBJECT_REF value/sb_value)."
    ),
    "result": (
        "Measured: intrinsics 104px (\"Dooz\") / 219px (\"New game\") / 421px "
        "(\"Compose Stopwatch\") / 39px (\"0.\") / 52px (\"00\"); layouts build "
        "NON-ZERO ([ROOT-063] width=104/219); Layout.draw DISPATCHES ([F-NEW-297] "
        "text ops, 45 rows/run on csw - the CONT-36 record count, now with real "
        "widths); the dooz face renders the \"Dooz\" title + \"New game\" button "
        "label as REAL GLYPHS for the first time (face 6841d52a20e6597e -> "
        "4f32f50fd55ccf90 x3 deterministic at 180s; title-area dark pixels 0 -> "
        "9030). csw RAW-DIFF: the title \"Compose Stopwatch\" moved from CLIPPED "
        "OFF-SCREEN (op x~1070) INTO VIEW (x=607, fully readable); diff bbox "
        "(607,36)-(1080,1095) = title + digits bands only; cards/pill/track pixels "
        "byte-identical (face 3442d9a9dc0fa0f9 -> d3c26b73ee21e571 x3). "
        "ZERO-DRIFT REGRESSION (binary 4f32f50f-wave): anchors 27/27 MATCH "
        "(dooz15 31ddd4d5b8e6d18e, micro 55343bbec712618d, unote 90a67cc1ddda57b7, "
        "gmdice 3891679dff449331, opencalc f25b754c4565c38b, ttt af6094295ecb50e3, "
        "flappy 13cf47464d9787f4, g2048 59ca1526611c4622, tanana afe0bd8dd4d09ca6 "
        "x3 byte-identical) + csw x3 re-pin (rationale in gate script) + simplecalc "
        "x3 341b9cec89d8f182 + dooz180 x3 re-pin + probe battery == records "
        "(f259g 84/7 + fnew302 48/24 documented known rows; fnew298 KEEP=5 "
        "corner=PASS). HONEST scope: the law fixes the INTRINSIC width leg - the "
        "compose text now flows end-to-end; exact per-glyph fidelity (the paint's "
        "42px fallback size question, icon glyphs as black boxes on dooz) remains "
        "the named next work."
    ),
    "evidence": (
        "run/cont61/dooz_w1_p1..p6 (the probe ladder), run/cont61/dooz_w1_fix1/"
        "fix2 + dooz180_det2/3 (the fix faces), run/cont61/csw_post1 + csw_det2/3 "
        "(the csw raw-diff pair), run/cont37/regression/* (the 36-run gate), "
        "evidence/cont61/ (views + DIFF audit)."
    ),
}
d["roots"].append(entry)
n = len(d["roots"])
d["total"] = n
d["count"] = n
d["total_roots"] = n
d["generated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
json.dump(d, open(PATH, "w"), indent=1, ensure_ascii=False)
print("roots:", n)
sc = {}
for r in d["roots"]:
    sc[r["status"]] = sc.get(r["status"], 0) + 1
d["status_counts"] = sc
json.dump(d, open(PATH, "w"), indent=1, ensure_ascii=False)
print("status:", sc)
