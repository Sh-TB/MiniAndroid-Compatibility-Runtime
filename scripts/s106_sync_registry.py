#!/usr/bin/env python3
"""S106: sync MICRO_GAP_REGISTRY.json — 47 micro-gaps CLOSED with the
S106 fence wave (battery stages + law tests + real fixes)."""
import json

REG = "/home/z/my-project/docs/MICRO_GAP_REGISTRY.json"

CLOSED = {
    # GIF animated decode (S106 GIF-ANIM-1, stb wiring + 2 upstream fixes)
    "MG-214": ("s106_gif_law_test G1", "GIF89a disposal 1 (leave-in-place) composited over canvas — stbi_load_gif_from_memory wired into GifDecoder; frame N content survives into N+1"),
    "MG-215": ("s106_gif_law_test G2", "disposal 2 = restore to BACKGROUND (transparent black, GIF89a + Android/Skia law) — FIXED vendored stb deviation (restored pre-frame canvas)"),
    "MG-216": ("s106_gif_law_test G3", "disposal 3 = restore to PREVIOUS — FIXED stb two_back dangling pointer (OOB read across realloc) with per-GIF prev_canvas snapshot"),
    # vector/drawable family (s106_drawables, aapt2-built fixture)
    "MG-002": ("s106_drawables_law_test V1", "viewport units map by raster/vp scale (24u@2x vs 48u@1x ink bboxes exact)"),
    "MG-003": ("s106_drawables_law_test V2", "fillType=evenOdd punches hole in overlap (center px alpha=0)"),
    "MG-004": ("s106_drawables_law_test V3", "nonZero fill winding-direction-insensitive (single reversed contour fills identically)"),
    "MG-005": ("s106_drawables_law_test V4", "stroke ink widens with strokeWidth; FIXED fill/stroke independence (stroke-only paths drew nothing)"),
    "MG-009": ("s106_drawables_law_test V5", "pivot-relative transform composition law (scale2 about pivot0 vs pivot12 differs by exactly pivot-delta*(s-1)*scale_px)"),
    "MG-010": ("s106_drawables_law_test V5", "rotation 90 exact mapping (x,y)->(24-y,x) about pivot (12,12)"),
    "MG-011": ("s106_drawables_law_test V6", "group scaleX/Y 2 doubles ink bbox from pivot"),
    "MG-012": ("s106_drawables_law_test V7", "group translateX/Y shifts ink by exact px"),
    "MG-013": ("s106_drawables_law_test V8", "nested group matrices compose in document order (outer translate ∘ inner rotate)"),
    "MG-014": ("s106_drawables_law_test V9", "IMPLEMENTED group android:alpha inheritance (multiplicative through the group chain; fill+stroke alpha multiply)"),
    "MG-016": ("s106_drawables_law_test L1", "layer-list items parse in DOCUMENT ORDER with colors preserved"),
    "MG-017": ("s106_drawables_law_test L2", "layer-list left/top insets land as px offsets (12dp x density 2.625 = 32px)"),
    "MG-020": ("s106_drawables_law_test S1", "state_selected=true picks the selected item (first-match)"),
    "MG-021": ("s106_drawables_law_test S2", "state_enabled=false picks the disabled item"),
    "MG-022": ("s106_drawables_law_test S3", "IMPLEMENTED state_checked in BgStateItem + pick_state_list (AOSP Checkable family law)"),
    "MG-023": ("s106_drawables_law_test S4", "no state match -> wildcard last item fallback"),
    "MG-046": ("s106_drawables_law_test M1", "mipmap XML indirection: @mipmap id -> resolve_full -> XML -> drawable reference chain"),
    "MG-047": ("s106_drawables_law_test A1", "adaptive-icon background color fills the canvas"),
    "MG-048": ("s106_drawables_law_test A2", "adaptive-icon foreground vector draws OVER background"),
    # text2 family
    "MG-052": ("s106_text2_law_test X1", "uncovered codepoint (PUA U+E700) flags notdef_count>=1"),
    "MG-053": ("s106_text2_law_test X2", "covered mixed-script string reports notdef_count==0 (no false tofu)"),
    "MG-061": ("s106_text2_law_test X3", "line spacing mult=2 doubles line box; add=6 adds flat px (StaticLayout law)"),
    "MG-062": ("s106_text2_law_test X4", "includeFontPadding: pad=true uses |fm.top| >= |fm.ascent|; pad=false tracks ascent exactly"),
    "MG-067": ("s106_text2_law_test X5", "font ascent positive + deterministic across calls"),
    "MG-068": ("s106_text2_law_test X6", "descent positive; ascent+descent <= line_height"),
    "MG-071": ("s106_text2_law_test X7", "trailing spaces excluded from line width (layout law)"),
    "MG-074": ("s106_text2_law_test X8", "max_lines=2 caps block at 2 lines; FIXED off-by-one that emitted an extra empty line past the cap"),
    "MG-075": ("s106_text2_law_test X9", "singleLine (max_lines=1) never word-wraps"),
    "MG-086": ("s106_text2_law_test X10", "unknown font family resolution falls back to usable face (honest failure semantics, no crash)"),
    "MG-087": ("s106_text2_law_test X11", "resolve_family distinguishes monospace vs sans-serif faces"),
    "MG-088": ("s106_text2_law_test X12", "unavailable (downloadable) family falls back to system face — TextView fallback law"),
    # canvas family
    "MG-204": ("s106_cia_law_test C5", "draw_image_region nearest-neighbour upscale keeps block structure (Paint.FilterBitmap=false default law)"),
    "MG-207": ("s106_cia_law_test C1", "canvas translate maps by +t; T∘S != S∘T pre-concat law (Skia)"),
    "MG-208": ("s106_cia_law_test C2", "scale multiplies linear columns; mean_scale=sqrt|det| (Skia stroke law)"),
    "MG-209": ("s106_cia_law_test C3", "rot90 maps +x onto +y (y-down clockwise); FIXED pre_rotate computing M·Rᵀ (rotated the wrong way)"),
    "MG-210": ("s106_cia_law_test C4", "nested save/translate/rotate composes M0∘T∘R exactly (hand-verified)"),
    # input family
    "MG-146": ("s106_cia_law_test I1", "DOWN→CANCEL unpresses, no click, no long-press (View.java L17172-17184 cleanup law)"),
    "MG-149": ("s106_cia_law_test I2", "touch outside bounds never targets/presses/clicks; in-bounds control clicks"),
    # audio family
    "MG-231": ("s106_cia_law_test A2", "SoundPool construct→load→play: sample loaded, stream PLAYING, stop->STOPPED; audio module WIRED into the build (was source-only)"),
    "MG-232": ("s106_cia_law_test A1", "MediaPlayer IDLE→INITIALIZED→PREPARED→STARTED→PLAYBACK_COMPLETED with AOSP illegal-transition error law"),
    "MG-233": ("s106_cia_law_test A3", "real RIFF/WAVE decodes to PCM (rate/channels/duration exact) via decode_audio_file"),
    # layout family
    "MG-115": ("s106_layout_net_law_test L1/L2", "FIXED View.requestLayout() bridge swallowing the call as no-op — now raises the R-NEW-302 layout_dirty traversal flag (AOSP PFLAG_FORCE_LAYOUT law); setLayoutParams path re-verified"),
    "MG-130": ("s106_layout_net_law_test L3", "ViewGroup children preserve document order; getChildAt/getChildCount resolve by index"),
    # net family
    "MG-248": ("s106_layout_net_law_test W1-W4", "REAL HTTP GET: parse_url decomposition, 200+exact body, 404 status preserved, transport error named (NET-001 client against a live local server)"),
}

reg = json.load(open(REG))
t = reg["tickets"]
closed_n = 0
for mgid, (stage, evidence) in CLOSED.items():
    if mgid not in t:
        print(f"MISSING {mgid}"); continue
    e = t[mgid]
    e["STATUS"] = "CLOSED"
    e["FANOUT"] = "fenced_s106"
    e["EVIDENCE"] = f"battery stage '{stage}' ({evidence}); commit of record = S106 wave; battery ALL PASS at close"
    closed_n += 1

# recount
import collections
reg["counts"] = dict(collections.Counter(v.get("STATUS") for v in reg["tickets"].values()))
reg["session"] = "S106-MG-FENCE (2026-09-26): 47 micro-gaps CLOSED with named battery stages; 5 real engine fixes (stroke independence, canvas rotate direction, maxLines off-by-one, requestLayout no-op bridge, stb GIF disposal-2 + two_back OOB) + group alpha + state_checked implementations; battery 105+ ALL PASS"
json.dump(reg, open(REG, "w"), indent=1)
print(f"registry updated: {closed_n} CLOSED; counts now {reg['counts']}")
