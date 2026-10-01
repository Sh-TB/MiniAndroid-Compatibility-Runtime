#!/usr/bin/env python3
"""s132_register_waves.py — S132 Waves 2/3 decision registration.
Wave-2 (SVG/nanoSVG): measured Telegram subset (50 files: path/circle/rect/
ellipse; zero gradients/masks/clips/strokes) → SVG-ASSET adapter law
(R-NEW-442) over the EXISTING PathParser+scanline-fill substrate (~260 LOC);
nanoSVG EVALUATED→NOT_USEFUL_FOR_MEASURED_SUBSET (would duplicate both laws,
4k LOC, frozen upstream). Honest: no corpus APK loads .svg via the drawable
slot yet — Telegram SvgHelper decodes via its own stream path (recorded
frontier), so the law is IMPLEMENTED, not real-APK-TESTED.
Wave-3 (video/audio): corpus scan — ZERO video assets anywhere; audio
formats ogg/wav/mp3 already covered by adopted stb_vorbis/sndfile/mpg123.
FFmpeg PLANNED → NOT_USEFUL_NOW (corpus gate) with an explicit re-trigger.
"""
import json

REUSE = "/home/z/my-project/canonical/reuse_registry.json"
ROOTS = "/home/z/my-project/root_registry.json"

with open(REUSE) as f:
    reuse = json.load(f)

for c in reuse["candidates"]:
    name = c.get("REUSE_CANDIDATE", "")
    if name == "nanosvg":
        c["status"] = "EVALUATED_NOT_USEFUL_FOR_MEASURED_SUBSET"
        c["DECISION"] = "EVALUATED → NOT_USEFUL for the measured feature set (existing components superior)"
        c["REASON"] = (
            "S132 Wave-2 measured evidence (scripts corpus scan): Telegram/Forkgram ship 50 .svg assets "
            "(656KB, max 507KB) using ONLY <path>/<circle>/<rect>/<ellipse> — zero gradients, masks, "
            "clipPaths, strokes or path-attr transforms. The runtime ALREADY owns the SVG path grammar "
            "(flatten_path_data = PathParser/PathEvaluator law) and the scanline fill (bg_vector paint). "
            "R-NEW-442 added a ~260 LOC text-XML adapter over that substrate; nanoSVG (~4k LOC parser + "
            "rasterizer, frozen upstream) would DUPLICATE both existing laws for the same subset. "
            "Re-trigger: a corpus APK measuring gradients/masks in real SVG assets."
        )
    if name == "ffmpeg":
        c["status"] = "NOT_USEFUL_NOW_CORPUS_GATE"
        c["DECISION"] = "EVALUATED → NOT_USEFUL NOW (corpus gate) — re-trigger on a measured video root"
        c["REASON"] = (
            "S132 Wave-3 corpus-first scan (the directive's own evidence rule): ZERO video assets "
            "(.mp4/.mkv/.webm/.3gp) across the entire corpus; VideoView/ExoPlayer/MediaCodec references exist "
            "only as library class names (Telegram/Forkgram/sudoku) with NO exercised video-playback root. "
            "The measured audio needs (ogg/wav/mp3 in 8 APKs) are already served by ADOPTED components "
            "(stb_vorbis, sndfile, mpg123). Integrating FFmpeg now would create a dead dependency — the exact "
            "'library graveyard' the reuse law forbids. RE-TRIGGER: any corpus APK measured FAILING at a "
            "video decode/playback root (MediaCodec/VideoView exercised at runtime), or the video-game class "
            "entering the campaign targets."
        )
reuse["counts"]["s132_wave2"] = "svg law implemented; nanoSVG not adopted (measured subset)"
reuse["counts"]["s132_wave3"] = "no video corpus need; audio already covered by adopted codecs"
with open(REUSE, "w") as f:
    json.dump(reuse, f, indent=1)
print("reuse registry: wave2/3 decisions recorded")

with open(ROOTS) as f:
    reg = json.load(f)
roots = reg["roots"] if isinstance(reg, dict) else reg
entry = {
    "id": "R-NEW-442",
    "status": "IMPLEMENTED",
    "priority": "P2",
    "fg": False,
    "title": "SVG-asset law missing (Telegram SvgHelper family loads plain-text .svg assets; no text-XML reader existed) — adapter law over the existing path/fill substrate",
    "evidence": (
        "S132 Wave-2 measured subset: 50 Telegram/Forkgram svg assets, path/circle/rect/ellipse only. "
        "IMPLEMENTED: miniandroid/src/resources/s132_svg_reader.cpp (~260 LOC) — text-XML adapter reusing "
        "flatten_path_data + bg_vector paint; wired at apply_shape_background (.svg extension) and the "
        "src/srcCompat inflate slot. Battery ALL PASS (114 stages) post-landing. HONEST GAP: no corpus APK "
        "loads .svg via the drawable slot — Telegram SvgHelper decodes via its own stream/file path "
        "(BLOCKED frontier: stream decode + SvgHelper bitmap pipeline); real-APK proof pending that frontier."
    ),
    "missing": "Telegram SvgHelper stream-decode path (real-APK exercise)",
    "next": "SvgHelper stream law when the file/stream read frontier lands",
    "commit": "S132",
}
by_id = {r.get("id"): r for r in roots}
if "R-NEW-442" in by_id:
    by_id["R-NEW-442"].update(entry)
else:
    roots.append(entry)
with open(ROOTS, "w") as f:
    json.dump(reg, f, indent=1)
print("R-NEW-442 registered; total roots:", len(roots))
