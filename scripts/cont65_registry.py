#!/usr/bin/env python3
"""cont65_registry.py — CONT-65 registry: add F-NEW-354..359 (the capability-
audit wave: direct-pixel image path, animated GIF render, real-decode media,
FillArrayData byte[] law, string-object materialization consumer law,
view-scale render law)."""
import json

PATH = "/home/z/my-project/root_registry.json"
with open(PATH) as f:
    reg = json.load(f)

NEW = [
    {
        "id": "F-NEW-354",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "layer": "renderer/imageview-bitmap-object + framework/bitmap-store",
        "title": (
            "DIRECT-PIXEL IMAGE PATH (setImageBitmap with store pixels, no "
            "APK-path provenance): the ADDITIONAL-AUDIT P1-2 law recorded "
            "'stored bitmap pixels without APK-path provenance — direct-pixel "
            "draw is a recorded frontier' and dropped the node blank. Fix: "
            "the ImageView image leg draws the BitmapStore raster 1:1 through "
            "the SAME g04 fit-rect + draw_image pipeline (decodeStream already "
            "applied density; no second rescale), with the "
            "image-bitmap-object-empty honest diag when the store is empty. "
            "Probe: capaudit R1d WebP (decodeStream asset -> setImageBitmap) "
            "renders 11264 cyan + 8068 magenta px; 22/22 pixel battery PASS."),
    },
    {
        "id": "F-NEW-355",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "layer": "renderer/gif-anim-timeline + framework/choreographer-clock",
        "title": (
            "ANIMATED GIF RENDER LAW + vsync display-tick clock: AOSP decodes "
            "the full AnimatedImageDrawable timeline and invalidates per "
            "frame-delay; the runtime renders every choreographer frame, so "
            "the faithful equivalent samples the SAME timeline by the "
            "deterministic virtual clock (last_frame_time_nanos % "
            "total_duration mapped through cumulative per-frame delays), "
            "decode-once cached per bitmap heap id. Probe: capaudit anim.gif "
            "3-frame cycle — blue@f8, green@f30, red@f55 (gifanim7 runs; "
            "full-cycle progression evidence), [GIFANIM] decode ok frames=3."),
    },
    {
        "id": "F-NEW-356",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "layer": "dex/media-mediaplayer + audio/real-decode-engine + sandbox",
        "title": (
            "REAL-DECODE MEDIA LAW (closes 'audio_engine real but unwired'): "
            "the audio::MediaPlayer decoder (mp3 via mpg123, wav/ogg/flac via "
            "sndfile) was compiled in with ZERO callers. Every DEX "
            "MediaPlayer heap object now lazily attaches one engine; "
            "setDataSource resolves through the ONE canonical sandbox law "
            "(Storage::resolve_android_path — DENIED = AOSP ERROR state, "
            "never a crash), prepare()/start() run the REAL decode; "
            "getDuration/getCurrentPosition answer from the decoder; output "
            "stays an honest no-op (no speaker). Probe: capaudit tone.wav — "
            "setDataSource OK, prepare OK dur=500ms playing=true; SoundPool "
            "load id=1. [MP-DECODE] traces committed."),
    },
    {
        "id": "F-NEW-357",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "layer": "dex/fill-array-data-byte-law",
        "title": (
            "FILL-ARRAY-DATA 1-byte-element law corrupted byte[] into "
            "boolean[]: the elem_width==1 branch stored EVERY element as "
            "make_bool(byte!=0) — 'new byte[]{'A','B','C'}' became "
            "(true,true,true); crypto keys, encodings, any byte[] literal "
            "were garbage. Fix: same AOSP FillArrayData law the "
            "elem_width==4 branch already implements — interpretation comes "
            "from the ARRAY element type; [B stores the raw byte "
            "(make_byte), [Z keeps the bool. Probe-proven via the "
            "F-NEW-358 chain: 'ABC' literal decodes to s=[ABC] len=3."),
    },
    {
        "id": "F-NEW-358",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P0",
        "layer": "dex/string-object-materialization-consumer-law",
        "title": (
            "STRING-OBJECT MATERIALIZATION CONSUMER LAW (five generic "
            "links): the String(byte[]) decode wrote decoded content to "
            "__string_value__ but consumers never read it, and the getBytes "
            "result array carried the synthetic 'Larray;' class breaking "
            "every [B-classifying consumer. Links: (1) String.getBytes "
            "allocates its result with the AOSP [B descriptor (the array "
            "compat shim treats both; [B is strictly more correct); (2) "
            "String.length on an unmaterialized String object answers the "
            "__string_value__ content length (was stub 0); (3) String.equals "
            "OBJECT-vs-OBJECT branch — identity first, else content compare "
            "(the sandbox roundtrip pair are two unmaterialized objects); "
            "(4) StringBuilder.append/Object-concat stringify reads "
            "__string_value__ after sb_value/value (was Class@oid garbage "
            "print); (5) String.valueOf OBJECT branch same fallback + the "
            "2-arg new String(byte[]) form enters the decode law ([B "
            "class-contract gate keeps String/CharSequence copy forms in "
            "Handler A). Probe: capaudit sandbox ROUNDTRIP_OK 22B (was "
            "MISMATCH), strctor s1=[ABC] len=3 s2=[ABC] len2=3 (was "
            "unmaterialized [Ljava/lang/String;@N len=0)."),
    },
    {
        "id": "F-NEW-359",
        "status": "ROOT-CAUSED-FIXED",
        "priority": "P1",
        "layer": "renderer/view-scale-render-law + framework/pivot-lazy-default",
        "title": (
            "VIEW-SCALE RENDER LAW (the recorded 'scale/rotation MATRIX "
            "application' frontier): setScaleX/setScaleY stored property "
            "state with getters but the draw walk never consumed it — the "
            "rendered face ignored view scale entirely. Fix: AOSP View.java "
            "mTransformationInfo law in BOTH draw paths (the classic "
            "execution_engine walk geometry + view_renderer draw_view "
            "guard-restored): scaleX/Y scale the drawn geometry about "
            "(pivotX,pivotY); pivot defaults to the view CENTER until "
            "setPivotX/Y overrides (mSetPivotX/Y flags added — the AOSP lazy "
            "default without which a stored 0 is ambiguous); the applied "
            "rect is what hit-testing records. Children keep laid-out "
            "absolute positions (recorded approximation: scaled-container "
            "subtree re-transform is the named frontier; rotation-about-"
            "pivot stays the rotation frontier). Probe: capaudit view_scale "
            "setScaleX(2.0)/setScaleY(1.5) renders bbox 200x150 exactly "
            "(was 100x100 unscaled). 36/36 anchor wall zero drift."),
    },
]

added = 0
for entry in NEW:
    if any(r.get("id") == entry["id"] for r in reg["roots"]):
        print(entry["id"], "already present — skip")
        continue
    reg["roots"].append(entry)
    added += 1

with open(PATH, "w") as f:
    json.dump(reg, f, indent=1, ensure_ascii=False)
print(f"added {added}; total roots: {len(reg['roots'])}")
