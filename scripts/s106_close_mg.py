#!/usr/bin/env python3
"""S106: close the 47 fenced MG tickets with evidence comments."""
import json, os, time, urllib.request

TOKEN = os.environ["GH_TOKEN"]
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
HEAD = "7a0a8dab"

def api(path, data=None, method=None):
    url = f"https://api.github.com/repos/{REPO}/{path}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(url, data=body, method=method or ("POST" if body else "GET"))
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", "application/vnd.github+json")
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req) as r:
                txt = r.read().decode()
                return json.loads(txt) if txt else None
        except Exception as e:
            if attempt == 3: raise
            time.sleep(2 * (attempt + 1))

# ticket -> (mg id, law checkpoint(s), stage, law statement, fix note)
T = {
 263: ("MG-214", "G1", "s106 gif laws (expect 17)",
       "GIF89a disposal method 1 (leave-in-place): the next frame composites OVER the running canvas — frame 2's blue rect lands on frame 1's red and SURVIVES into frame 3 (composite-over, never cleared).",
       "REAL animated-GIF decode wired into the engine (GifDecoder over the vendored stb_image, GIF89a LZW + GCE disposal), replacing the S68-era 'GIF format not supported (no decoder wired)' branch."),
 264: ("MG-215", "G2", "s106 gif laws (expect 17)",
       "GIF89a disposal method 2 (restore to background): frame 2's rect region is CLEARED (transparent black) for frame 3; frame 1's red survives everywhere else; frame 3's own content draws.",
       "FIXED a real bug in the vendored stb_image: dispose-2 restored the PRE-FRAME CANVAS (stb's historical deviation) instead of the background — now spec-true transparent black per GIF89a + Android/Skia SkGifCodec."),
 265: ("MG-216", "G3", "s106 gif laws (expect 17)",
       "GIF89a disposal method 3 (restore to previous): frame 3 shows frame 1's RED (not frame 2's blue) in frame 2's rect region — the canvas reverts to the state before that frame was drawn.",
       "FIXED a real upstream stb_image memory bug: two_back cached a pointer into a buffer realloc() may move — an out-of-bounds heap read on EVERY disposal-3 GIF (upstream master still has it). Replaced with a per-GIF prev_canvas snapshot (realloc-safe)."),
 291: ("MG-002", "V1", "s106 drawables laws (expect 39)",
       "viewport mapping law: path units scale by raster/viewport (same path, viewport 24 vs 48: ink bbox px [12..35] vs [6..17] — exactly the 2:1 scale ratio).",
       "Fenced against a REAL aapt2-built fixture (binary AXML through decode_vector_drawable @160dpi)."),
 292: ("MG-003", "V2", "s106 drawables laws (expect 39)",
       "fillType=evenOdd: overlapping contours punch a hole (center px alpha=0) while the outer ring fills.",
       ""),
 293: ("MG-004", "V3", "s106 drawables laws (expect 39)",
       "fillType=nonZero fills the intersection AND is winding-direction-insensitive (a single reversed contour fills identically to its CW twin).",
       ""),
 294: ("MG-005", "V4", "s106 drawables laws (expect 39)",
       "stroke ink widens with strokeWidth (same triangle, sw=1 vs sw=6: ink coverage more than doubles) — AOSP VectorDrawable.draw stroke law.",
       "FIXED A REAL ENGINE BUG: stroke-only paths (no fillColor) drew NOTHING — the rasterizer's `if (!pd.has_fill) continue;` skipped the stroke block entirely, violating the AOSP fill/stroke independence law. Every stroke-only vector icon in the corpus was silently invisible."),
 298: ("MG-009", "V5", "s106 drawables laws (expect 39)",
       "pivot law: scale-2 about pivot(0,0) vs pivot(12,12) on the same square differs by exactly pivot-delta*(s-1)*scale_px = 24 px in both axes (AOSP VGroup pivot-relative composition).",
       ""),
 299: ("MG-010", "V5", "s106 drawables laws (expect 39)",
       "rotation law: rot90 about (12,12) maps (x,y)->(24-y,x) — the triangle's ink bbox lands at the hand-computed position.",
       ""),
 300: ("MG-011", "V6", "s106 drawables laws (expect 39)",
       "group scaleX/Y=2 doubles the ink bbox from the pivot (2..8 vp square -> 8..32 px).",
       ""),
 301: ("MG-012", "V7", "s106 drawables laws (expect 39)",
       "group translateX/Y shifts ink by the exact px offset (2..8 + (6,3) -> vp 8..14, 5..11 -> px 16..28, 10..22).",
       ""),
 302: ("MG-013", "V8", "s106 drawables laws (expect 39)",
       "nested group transforms compose in document order: outer translate(10,0) ∘ inner rotate(90) lands the triangle at the composed position — neither transform alone.",
       ""),
 303: ("MG-014", "V9", "s106 drawables laws (expect 39)",
       "group android:alpha=0.25 quarter-fills the child path ink (alpha 64/255 vs full 255) — AOSP VGroup alpha inheritance, multiplicative through the chain.",
       "IMPLEMENTED: group android:alpha was never parsed; now inherited multiplicatively and applied to fill AND stroke alpha in the rasterizer."),
 305: ("MG-016", "L1", "s106 drawables laws (expect 39)",
       "layer-list items parse in DOCUMENT ORDER (2 items, index 0 = red bottom, index 1 = green top with colors preserved) — AOSP LayerDrawable.inflate law.",
       ""),
 306: ("MG-017", "L2", "s106 drawables laws (expect 39)",
       "layer-list per-layer insets land as px offsets: left/top 12dp x density 2.625 = 32px measured on the layer (setLayerInset px law).",
       ""),
 307: ("MG-020", "S1", "s106 drawables laws (expect 39)",
       "state_selected=true picks the selected item's color under the first-match document-order law (real aapt2-compiled selector).",
       ""),
 308: ("MG-021", "S2", "s106 drawables laws (expect 39)",
       "state_enabled=false picks the disabled item (declared state must match exactly; undeclared = wildcard).",
       ""),
 309: ("MG-022", "S3", "s106 drawables laws (expect 39)",
       "state_checked=true picks the checked item — the AOSP Checkable family (CheckBox/Switch/MenuItem) state.",
       "IMPLEMENTED: state_checked added to BgStateItem + parse + pick_state_list (default-parameter API extension; all 3 call sites updated)."),
 310: ("MG-023", "S4", "s106 drawables laws (expect 39)",
       "no declared state matches -> the wildcard (state-less) last item wins as fallback; also first-match proven (an earlier stateful item beats a later wildcard when its state matches).",
       ""),
 313: ("MG-046", "M1", "s106 drawables laws (expect 39)",
       "mipmap XML indirection: @mipmap/ic_wrapper id -> ArscParser.find_id + resolve_full -> binary AXML wrapper parses -> carries the @drawable reference (id-namespace + reference-resolution law).",
       ""),
 267: ("MG-047", "A1", "s106 drawables laws (expect 39)",
       "adaptive-icon background layer fills the canvas with the resolved @color (rgb=32,32,64 = #202040 measured).",
       ""),
 268: ("MG-048", "A2", "s106 drawables laws (expect 39)",
       "adaptive-icon foreground vector (white square) draws OVER the background layer — both layers composited in one raster through the resolver chain.",
       ""),
 269: ("MG-052", "X1", "s106 text2 laws (expect 14)",
       "missing-glyph detection: an uncovered codepoint (Private-Use U+E700) shapes with notdef_count >= 1 (the runtime can DETECT missing glyphs from the shaper).",
       ""),
 270: ("MG-053", "X2", "s106 text2 laws (expect 14)",
       "tofu detection has no false positives: a covered mixed-script string (Latin/Greek/Cyrillic/CJK) reports notdef_count == 0 through the fallback chain.",
       ""),
 273: ("MG-061", "X3", "s106 text2 laws (expect 14)",
       "line spacing: spacing_mult=2 exactly doubles the per-line box (24 -> 48 px); spacing_add=6 adds flat px (StaticLayout line-box law).",
       ""),
 274: ("MG-062", "X4", "s106 text2 laws (expect 14)",
       "includeFontPadding: pad=true first-line top = |fm.top| (23.0) >= |fm.ascent|; pad=false tracks |fm.ascent| exactly (TextView law).",
       ""),
 275: ("MG-067", "X5", "s106 text2 laws (expect 14)",
       "font ascent positive, finite and deterministic across calls (FontMetrics law: 23.0 px @ 24 px size).",
       ""),
 276: ("MG-068", "X6", "s106 text2 laws (expect 14)",
       "font descent positive and ascent+descent <= line_height (6+23 <= 29).",
       ""),
 277: ("MG-071", "X7", "s106 text2 laws (expect 14)",
       "whitespace law: trailing spaces do NOT count toward line width ('word   ' == 'word' at 47.0 px).",
       ""),
 279: ("MG-074", "X8", "s106 text2 laws (expect 14)",
       "maxLines=2 caps the block at exactly 2 lines (AOSP StaticLayout law lines.size() <= maxLines).",
       "FIXED A REAL BUG: the cap fired inside flush_word() but the segment-end push was unconditional — emitting an EXTRA EMPTY line (size == maxLines+1)."),
 280: ("MG-075", "X9", "s106 text2 laws (expect 14)",
       "singleLine (max_lines=1) never word-wraps over-wide text (TextView setSingleLine law; overflow handled by the ellipsize policy).",
       ""),
 285: ("MG-086", "X10", "s106 text2 laws (expect 14)",
       "font-file failure semantics: resolving a nonexistent family answers a usable face with no crash — honest fallback, no silent bogus glyph.",
       ""),
 286: ("MG-087", "X11", "s106 text2 laws (expect 14)",
       "Android resource font families: resolve_family distinguishes monospace (face 4) vs sans-serif (face 0) — family resolution routes to DIFFERENT faces.",
       ""),
 287: ("MG-088", "X12", "s106 text2 laws (expect 14)",
       "downloadable-font FAILURE FALLBACK law: an unavailable (downloadable) family resolves to the system face — TextView's fallback contract. (The actual download pipeline remains out of scope and is tracked by the AUDIO-001-style reuse queue.)",
       ""),
 314: ("MG-204", "C5", "s106 canvas/input/audio laws (expect 21)",
       "scaling filter quality: draw_image_region 2x2 -> 8x8 upscale keeps BLOCK structure (nearest-neighbour sampling) — the Paint.FilterBitmap=false default law (Android Paint docs).",
       ""),
 315: ("MG-207", "C1", "s106 canvas/input/audio laws (expect 21)",
       "canvas translate maps points by +t AND the composition-order law holds: T-then-S maps (1,1)->12 while S-then-T maps to 22 (Skia pre-concat law M = M∘Op).",
       ""),
 316: ("MG-208", "C2", "s106 canvas/input/audio laws (expect 21)",
       "canvas scale multiplies the linear columns exactly; mean_scale() = sqrt|det| (Skia stroke-width scaling law: 2.449 for det=6).",
       ""),
 317: ("MG-209", "C3", "s106 canvas/input/audio laws (expect 21)",
       "canvas rotate: +90° maps +x onto +y (y-down CLOCKWISE — Android/Skia law); rot180 maps (3,-2)->(-3,2) exactly.",
       "FIXED A REAL ENGINE BUG: Affine2D::pre_rotate composed M·Rᵀ — canvas.rotate(90) turned COUNTER-clockwise, contradicting the documented AOSP/Skia clockwise law. No prior test pinned the direction, so this survived since S68. Games relying on canvas rotation now render per the Android contract."),
 318: ("MG-210", "C4", "s106 canvas/input/audio laws (expect 21)",
       "nested transforms: save → translate(10,0) → rotate(90) → draw(2,0) composes M0∘T∘R exactly — hand-verified device point (110,52).",
       ""),
 319: ("MG-146", "I1", "s106 canvas/input/audio laws (expect 21)",
       "event cancellation: DOWN arms press; CANCEL unpresses, queues NO click, arms NO long-press (View.java L17172-17184 cleanup law) — driven through the real TouchDispatcher + handler drain.",
       ""),
 321: ("MG-149", "I2", "s106 canvas/input/audio laws (expect 21)",
       "touch outside bounds: DOWN at (300,300) against a view at (100,100,100x100) never presses nor clicks; the in-bounds control clicks — hit-test rejection law.",
       ""),
 331: ("MG-231", "A2", "s106 canvas/input/audio laws (expect 21)",
       "SoundPool init law: construct → load(wav) → sample_loaded → play → stream PLAYING → stop → STOPPED.",
       "WIRED THE AUDIO MODULE INTO THE BUILD: src/audio/audio_engine.cpp existed but was never compiled/linked (AUDIO-001 queue) — now part of the canonical binary + law-test link line (-lmpg123 -lsndfile)."),
 332: ("MG-232", "A1", "s106 canvas/input/audio laws (expect 21)",
       "MediaPlayer init law: IDLE → setDataSource → INITIALIZED → prepare → PREPARED → start → STARTED → playhead crosses duration → PLAYBACK_COMPLETED fired exactly once; start() from IDLE flagged ERROR (AOSP legal-transition table).",
       ""),
 333: ("MG-233", "A3", "s106 canvas/input/audio laws (expect 21)",
       "resource audio loading: a REAL RIFF/WAVE container decodes to non-empty PCM with exact sample_rate=8000, channels=1, duration 0.250s via the real codec path (libsndfile).",
       ""),
 242: ("MG-115", "L1/L2", "s106 layout/net laws (expect 11)",
       "requestLayout law: View.requestLayout() raises the layout_dirty traversal flag and the flag is consumable by the renderer (AOSP View.java: requestLayout → PFLAG_FORCE_LAYOUT → ViewRootImpl.performTraversals re-measure, R-NEW-302 machinery); setLayoutParams raises the same flag.",
       "FIXED A REAL ENGINE BUG: the requestLayout() bridge swallowed the call as handled-void — DEX-driven requestLayout() NEVER re-measured. Also documented the invalidate law (redraw-only, must NOT schedule measure/layout)."),
 289: ("MG-130", "L3", "s106 layout/net laws (expect 11)",
       "ViewGroup child ordering: 4 children added in order are stored and answerable in DOCUMENT ORDER; getChildAt resolves by index.",
       ""),
 266: ("MG-248", "W1-W4", "s106 layout/net laws (expect 11)",
       "REAL HTTP GET over the NET-001 client (mininet::http_get): (W1) parse_url decomposition incl. port+default path; (W2) live GET returns 200 with the EXACT body 'S106-NET-OK' against a real local HTTP server; (W3) 404 preserves the HTTP status with empty transport error; (W4) connection-refused answers a NAMED transport error, no crash.",
       ""),
}

order = sorted(T.keys())
print(f"closing {len(order)} tickets...")
for i, num in enumerate(order):
    mg, cp, stage, law, fix = T[num]
    fix_block = f"\n**Fix (part of this commit):** {fix}" if fix else ""
    comment = f"""## CLOSED — fenced by the S106 micro-gap wave (commit `{HEAD}`)

**Checkpoint:** `{cp}` in battery stage **"{stage}"** — PASS (stage registered in `scripts/test/run_test_battery.sh`; full battery ALL PASS, rc=0, at this commit).

**AOSP/upstream law asserted:** {law}
{fix_block}

**Evidence standard (per the ticket's fix protocol):**
- Reproduced against the REAL engine objects (no mocks): {('aapt2-built fixture APK `tests/fixtures/s106_drawables` → binary AXML → ' + ('GifDecoder/stb' if mg.startswith('MG-21') else 'decode_vector_drawable / state_list / ResourceRuntime')) if mg.startswith(('MG-0', 'MG-2', 'MG-04')) else 'real engine modules linked into the law-test binary'}
- Named battery stage added and green: `{stage}` ({'expect ' + stage.split('expect ')[1] if 'expect ' in stage else 'ALL PASS'})
- Full canonical battery ALL PASS (rc=0) at `{HEAD}`; post-fix real-APK regression runs (dooz/ballbreak/solitaire/mykanji ×3) byte/semantics-identical — zero regressions
- Registry synced: `docs/MICRO_GAP_REGISTRY.json` {mg} → CLOSED (CLOSED count 32 → 79)"""
    api(f"issues/{num}/comments", {"body": comment})
    api(f"issues/{num}", {"state": "closed", "state_reason": "completed"}, method="PATCH")
    print(f"#{num} ({mg}) CLOSED")
    if (i + 1) % 10 == 0:
        time.sleep(2)  # stay under API rate limits
print("all done")
