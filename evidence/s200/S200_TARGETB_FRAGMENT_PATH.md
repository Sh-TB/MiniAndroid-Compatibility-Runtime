# S200 Target B — the fragment-path frontier: RESOLVED (pipeline proven; the remaining blocker is named)

Binary: **`6c808c7448850756`** (canonical; byte-identical rebuild from HEAD
`463608f2`). Wave date: 2026-11-09.

## The frontier question (from the wave record on #536/#557)

> "the shape draw's raster output still does not land in the framebuffer —
> the remaining question is now NARROW and named: the fragment path for the
> shape program (the sb_frag texture-multiply vs the shape's own v_color
> semantics, or clip/raster state)."

**Answer: the fragment path is CORRECT.** Every suspect in that question was
probed on live dispatch traces and acquitted; the pipeline was proven by an
app-exact isolation test AND by a live quad landing on screen.

## Findings (all evidence in `evidence/s200/`, probes in
`scripts/s200_probe_patch.diff` + `scripts/s200_pgl_blend_test.cpp`)

1. **dooz does not exercise the GLES bridge at all** (`GLDBG_DOOZ_VS_TTT.json`:
   dooz emits ZERO `[GLDBG]` rows — it renders through the View lane). The
   libGDX sb shader pair has no golden backer; tictactoe is the FIRST real
   app through this pipeline. (Also explains why the goldens never caught
   this family's issues.)

2. **The app's real vertex format is the gdx SpriteBatch 20-byte vertex**
   (`pos 2×F32 + color 4×u8@+8 + uv 2×F32@+12`, stride 20) — decoded from the
   draw-time hexdump (`vtx[0] 0000b841 0000f242 000000fe 0000043d 0000803a`
   = x=23, y=121, color RGBA(0,0,0,254), u=0.0322, v=0.0010).

3. **The sb fragment stage is correct, proven twice:**
   - Isolation test (`s200_pgl_blend_test.cpp`) with the app-exact path
     (stride-20 attribs, u8-normalized color at +8, 6-float varyings,
     texture-multiply frag, SRC_ALPHA blend): the quad lands black exactly as
     the shader math predicts. PGL's blend with alpha>1 commits correctly
     (a=17.6 → black; a=0.7 → 0x4c4c4c = precise).
   - Live run: tile fragments sample REAL texels (`sbf #900 texel=…,1.000`,
     `out=0,0,0,17.6`) and the pixels reach the framebuffer.

4. **The first real textured quad is ON SCREEN.** The face's only non-white
   content (previously read as "SW-path glyphs") is the game's 96×96 tile
   quad (draw count=6, texture name 4) rendered at the panned-camera screen
   position (x≈468, y≈1750+). Confirmed against the upload dump
   (`s200_texdump_4_96x96.rgba`: art bbox (16,8)-(76,80) matches the on-screen
   blob geometry).

5. **Texture objects are sound**: the texture audit shows all 4 uploads land
   on the right PGL objects with real data (3× font page 1024×1024
   white-transparent, 1× tile 96×96). The per-draw bind→draw mapping:
   count=30←tex2, count=6←tex4 (tile), count=12←tex3, count=66←tex1.

6. **The remaining blocker is NAMED: the font pages are empty.** All three
   1024×1024 pages upload as pure (255,255,255,0) — the glyph blit never
   draws. Root: the FreeType native family hits the engine STUB tail
   (`[W18-FT-BRIDGE] stub tail`: initFreeTypeJni, newMemoryFace,
   setPixelSizes, loadChar, getGlyph, getMetrics) while the real
   `libgdx-freetype.so` IS loaded and DOES export the symbols (verified with
   `nm -D`: `Java_..._00024Face_loadChar` etc.). The stub-minted fake handles
   make the downstream real renderGlyph/getBitmap fail → gdx
   `generateGlyphAndBitmap` returns null → `continue` → pages stay empty →
   ALL text draws (counts 30/12/66) sample transparent white → invisible.
   This is the single remaining wall between the runtime and a fully
   rendered tictactoe.

7. **Second bug found and pinned (cosmetic once #6 falls): the a_color
   buffer-position law.** The bridge serves the color attribute at base+0
   instead of base+8 (`vapPOST idx=1 off=base+0` while uv gets base+12) — the
   vertex color reads position bytes (v_color=(0,0,184,65) for pos (23,121)).
   The marshal's FloatBuffer `__bb_pos__` advance misses the color bind's
   position=2 (bytes 8). Law to fix: `addr = base + __bb_pos__ × esz` must see
   pos=2 for the color bind (the app repositions ONE shared FloatBuffer
   between the three attribute binds).

8. **PGL const map acquitted**: `0x302→87 (SRC_ALPHA)`, `0x1406→248 (FLOAT)`
   are CORRECT — PGL's internal enum block really uses those small integers
   (counted from the `enum` head; GL_SRC_ALPHA=87, GL_FLOAT=248). The earlier
   suspicion of mistranslation was wrong.

## Gates on the canonical binary (post-investigation freshness proof)

`S200_GATE_RERUN.json`: bouncy `8a6c24ac` HOLD · unote `3b8dcb0a` HOLD ·
dooz `31ddd4d5` HOLD (pin invocation, rerun-identical) · gmdice 5-tap
rerun-identical PASS · microtimer spot 0 uncaught. Floor 11/11 verified on
this exact binary identity in commit `00783ccd` (deterministic rebuild).

## Next P0 (single named task)

Make the FreeType family resolve the REAL `libgdx-freetype.so` symbols
(F-C4-594 native-precedence for this library — the symbols exist, the
mangling law F-NEW-611 is already correct; find why the lookup missed) OR
give the engine stub a real-bitmap leg backed by the runtime's own FreeType
(already linked for text_shaper, font already registered via FONT_SOURCE).
Then: text renders → the menu becomes tappable → the board/X-O screen is
reachable → full interaction proof.
