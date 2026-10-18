#!/usr/bin/env python3
"""cont99_img_registry_update.py — CONT-99 T3 registry append.

Three ROOT-CAUSED-FIXED roots (F-NEW-413/414/415) and one honestly
REJECTED_WITH_REASON root (F-NEW-412, the Drawable accessor mint — corpus
regression, wall DRIFT via the ISE cascade; recorded with its completion
precondition). Mirrors root_registry.json -> canonical/.
"""
import json
import shutil

BASE = "/home/z/my-project"
REG = f"{BASE}/root_registry.json"
MIRROR = f"{BASE}/canonical/root_cause_registry.json"

DIRECTIVE = ("#364 CONT-99 T3 (comment 6248236077) — ImageView/Drawable "
             "sizing, scaleType and image bounds")
FIXTURE = ("fixtures/cont99_img_probe (com.probe.c99im, V1-C99IM, apk "
           "run/cont99/c99im.apk sha16 95d6f88abd7f60b5, real aapt2 "
           "compile+link with res/, ECJ, D8; deterministic zlib-generated "
           "nodpi PNG assets red_land 200x100 / blue_port 100x200 / "
           "green_sq 100x100; 8 ImageView boxes covering fitCenter/"
           "centerCrop/fitXY/centerInside/center/wrap_content/missing-src "
           "with a deterministic 15-point pixel oracle over "
           "screenshot.ppm + state rows)")
RASTER = ("PIXEL RASTER CONTRACT ALREADY AT AOSP PARITY on current HEAD "
          "(S83-GFX-BASE section 19 + G04 density law): 15/15 pixel rows "
          "on BOTH the PRE (3b89722589ff5af7) and POST binaries — "
          "fitCenter letterbox, centerCrop reaching the box edge, fitXY "
          "fill, centerInside no-upscale, center natural-size, "
          "wrap_content == intrinsic with nothing painted beyond it, "
          "missing-src draws nothing, images never escape their own view "
          "bounds. Measured-size rows all OK (iv7 wrap_content 100x100). "
          "No stretch-to-fill default anywhere.")
REGRESSION = ("wall 12/12 MATCH byte-identical (dooz 31ddd4d5b8e6d18e, "
              "opencalc f25b754c4565c38b, unote 90a67cc1ddda57b7, "
              "microtimer bbd350b6c14fbd52, x3); goldens 4/4; negatives "
              "19/19; reinstall 8/8; MG-310 7/7; MG-150 3/3; selftests "
              "13/13; F-NEW-376 70/70; T2 probe re-run on the final "
              "binary: control B=1, translation D=1, scale F=1, scroll "
              "H=0 (F-NEW-408..411 intact); T3 pixels 15/15 both binaries")

ROOTS = [
    {
        "id": "F-NEW-413",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "title": ("Enum constants printed the identity form "
                  "(Class@id) instead of the declared name — "
                  "String.valueOf(Object)/StringBuilder.append(Object)/"
                  "Object.toString() had no Enum.toString()==name() law"),
        "layer": "runtime/enum-object-law",
        "directive": DIRECTIVE,
        "root_cause": (
            "The engine's sget-enum minting law already stores "
            "\"enum_name\" on every minted constant, but every string "
            "conversion site formatted the identity form: D8 compiles "
            "string concat to String.valueOf(Object) + StringBuilder, and "
            "valueOf's OBJECT_REF branch, the StringBuilder append "
            "stringify, and the Object.toString() bridge all answered "
            "class_desc + \"@\" + id. Probe: getScaleType() concat printed "
            "\"Landroid/widget/ImageView$ScaleType;@31\" (AOSP: "
            "FIT_CENTER). Fan-out: every app that logs, serializes or "
            "displays an enum."),
        "fix": (
            "All three conversion sites (String.valueOf OBJECT_REF, the "
            "StringBuilder stringify lambda, the Object.toString bridge) "
            "answer the receiver's stored enum_name field before the "
            "identity form (AOSP Enum.toString() == name(); OpenJDK "
            "Enum.java)."),
        "evidence": {
            "wave": "CONT-99", "fixture": FIXTURE,
            "paired_ab": ("PRE: st=Landroid/widget/ImageView$ScaleType;@31 "
                          "on all rows. POST: st=FIT_CENTER / CENTER_CROP / "
                          "FIT_XY / CENTER_INSIDE / CENTER — the declared "
                          "names."),
            "regression": REGRESSION, "raster": RASTER,
        },
        "issue": "#364",
    },
    {
        "id": "F-NEW-414",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "title": ("android.graphics.drawable family had ZERO entries in "
                  "the framework ancestry table — every is_subclass_of / "
                  "instanceof on a Drawable type answered FALSE"),
        "layer": "runtime/framework-ancestry",
        "directive": DIRECTIVE,
        "root_cause": (
            "view_ancestry.h carried no drawable edges at all, so "
            "is_subclass_of(BitmapDrawable, Drawable) returned FALSE and "
            "every IS-A gate on drawable receivers failed (the S109 "
            "ROOT-033b intrinsic getters missed their is_drawable_type "
            "gate and answered the generic 0 for a receiver that carried "
            "real __dr_width__/__dr_height__ values — proven by the "
            "MINIANDROID_S109_DIAG instrumented run: cls=BitmapDrawable "
            "is_drawable=0)."),
        "fix": (
            "Added the AOSP graphics.drawable subclass law to the "
            "ancestry table (frameworks/base/graphics): BitmapDrawable, "
            "ColorDrawable, GradientDrawable, ShapeDrawable, "
            "VectorDrawable, StateListDrawable, LayerDrawable, "
            "InsetDrawable, RippleDrawable — all IS-A Drawable."),
        "evidence": {
            "wave": "CONT-99", "fixture": FIXTURE,
            "paired_ab": ("Diagnostic A/B: with the S109 gate instrumented, "
                          "cls=Landroid/graphics/drawable/BitmapDrawable; "
                          "is_drawable=0 PRE; the ancestry edges flip it to "
                          "1 (the S109 law then reads the stored "
                          "intrinsics 200x100/100x200/100x100)."),
            "regression": REGRESSION, "raster": RASTER,
        },
        "issue": "#364",
    },
    {
        "id": "F-NEW-415",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "title": ("ImageView.getScaleType() minted a per-CLASS singleton "
                  "with no enum_name — all ScaleType constants shared ONE "
                  "overwritten object (identity law broken + name law "
                  "unreachable)"),
        "layer": "runtime/view-property-shadows",
        "directive": DIRECTIVE,
        "root_cause": (
            "getScaleType used heap get_or_create(CLASS) — ONE object for "
            "the whole ScaleType enum — and wrote only the receiver's "
            "current ordinal into it on every call. JVMS/AOSP enum law: "
            "constants are singletons PER CONSTANT. Two views with "
            "different scale types compared EQUAL; a view's scale type "
            "changed under every other view's feet; and the name-less "
            "object made Enum.toString()/name() impossible (identity "
            "form, F-NEW-413)."),
        "fix": (
            "Per-ordinal constant cache (one shared object per ScaleType "
            "ordinal, law-correct across receivers) seeded with the "
            "ordinal AND the declared name (MATRIX, FIT_XY, FIT_START, "
            "FIT_CENTER, FIT_END, CENTER, CENTER_CROP, CENTER_INSIDE — "
            "the AOSP ImageView.ScaleType order). setScaleType keeps "
            "reading the object's ordinal, so XML inflation + programmatic "
            "switches round-trip lawfully."),
        "evidence": {
            "wave": "CONT-99", "fixture": FIXTURE,
            "paired_ab": ("PRE: every row st=@31 (one shared class "
                          "singleton). POST: iv1 st=FIT_CENTER, iv2 "
                          "st=CENTER_CROP, iv4 st=FIT_XY, iv5 "
                          "st=CENTER_INSIDE, iv6 st=CENTER, and the "
                          "programmatic iv1 -> FIT_XY switch reads back "
                          "FIT_XY."),
            "regression": REGRESSION, "raster": RASTER,
            "honest_notes": ("cross-source identity (getScaleType() == "
                             "ScaleType.FIT_CENTER against the ENGINE-minted "
                             "sget constant) is the recorded residual: the "
                             "shadow layer and the engine constant cache "
                             "mint separately — unification needs the "
                             "engine-side static-field cache exposed to the "
                             "shadow layer."),
        },
        "issue": "#364",
    },
    {
        "id": "F-NEW-412",
        "status": "REJECTED_WITH_REASON",
        "priority": "P1",
        "title": ("ImageView.getDrawable() answered null despite an "
                  "applied android:src (AOSP mDrawable non-null law) — "
                  "FIX ATTEMPTED AND REVERTED: the Drawable object method "
                  "surface is incomplete, so the mint converted opencalc's "
                  "handled-null path into an ISE cascade + white render"),
        "layer": "runtime/view-property-shadows",
        "directive": DIRECTIVE,
        "root_cause": (
            "AOSP ImageView.getDrawable() returns the applied drawable; "
            "the engine stores the src on the node (src_drawable_path + "
            "src_w/src_h + src_density) but no object accessor existed "
            "(probe: pixels 15/15 drawn, getDrawable()=null). A mint of a "
            "BitmapDrawable-face object (cached per receiver, "
            "__dr_width__/__dr_height__ in the S109 density law) was "
            "implemented and PROVEN in-probe (drawable=true, intrinsics "
            "200x100/100x200/100x100, missing-src stays null/-1) — but "
            "the corpus rejected it: opencalc's appcompat path "
            "(Lg/F;.w -> Lg/m;.onPostCreate) took the previously-dead "
            "non-null branch and hit unimplemented Drawable methods → "
            "IllegalStateException cascade escaping at MainActivity → "
            "end-state framebuffer white → wall opencalc DRIFT "
            "(31ddd4d5b8e6d18e, the all-white PNG, x3; pristine "
            "3b89722589ff5af7 renders f25b754c4565c38b MATCH)."),
        "fix": (
            "REVERTED (the honest terminal state for this track): the "
            "null accessor is the pre-existing law and opencalc handles "
            "it. PRECONDITION for re-landing: the Drawable object method "
            "surface the corpus actually drives (setBounds/getBounds/"
            "getColorFilter/setColorFilter/mutate/getConstantState/"
            "inflate paths) must reach the same completeness the "
            "--click-test oracle needed before it could observe real "
            "pipelines (F-NEW-407 lesson). Recorded as the named "
            "completion precondition, not a silent gap."),
        "evidence": {
            "wave": "CONT-99", "fixture": FIXTURE,
            "paired_ab": ("in-probe POST (getDrawable mint active): "
                          "drawable=true iw=200/ih=100 etc. + pixels "
                          "15/15. corpus A/B: mint binary 59ee62616ce52eee "
                          "opencalc screenshot = all-white PNG "
                          "31ddd4d5b8e6d18e x3 (wall DRIFT, ISE cascade "
                          "in crash.log); revert binary 2f5faa881bd055e8 "
                          "renders f25b754c4565c38b MATCH."),
            "regression": REGRESSION, "raster": RASTER,
            "honest_notes": ("the probe row drawable=false iw=-1 in the "
                             "final binary is the HONEST residual: the "
                             "accessor stays null until the Drawable "
                             "method surface completes; the pixel raster "
                             "is unaffected (15/15 both binaries)."),
        },
        "issue": "#364",
    },
]

with open(REG) as f:
    reg = json.load(f)

existing = {r["id"] for r in reg}
added = 0
for root in ROOTS:
    if root["id"] not in existing:
        reg.append(root)
        added += 1

with open(REG, "w") as f:
    json.dump(reg, f, indent=1, ensure_ascii=False)
shutil.copyfile(REG, MIRROR)
print(f"registry: {len(reg) - added} -> {len(reg)} roots (+{added})")
