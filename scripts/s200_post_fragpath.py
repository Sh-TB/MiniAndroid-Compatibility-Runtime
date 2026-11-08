#!/usr/bin/env python3
"""S200 — push the fragment-path resolution comment (golden rule)."""
import json, subprocess, time
import urllib.request
import pathlib

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"


def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True,
                         cwd="/home/z/my-project").stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return ""


TOK = token()
HDRS = {"Authorization": f"token {TOK}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "s200-main-integration-coder"}

BODY = """## S200 P0 Target B — the fragment-path frontier is RESOLVED: the GLES pipeline is proven; the remaining wall is named (empty font pages)

Binary **`6c808c7448850756`** (canonical; byte-identical rebuild from HEAD `463608f2`). The question left by the last wave record — *"the fragment path for the shape program (sb_frag texture-multiply vs v_color semantics, or clip/raster state)"* — is now **answered with probes on live dispatch traces, an app-exact isolation test, and a live quad on screen**. Full report: `evidence/s200/S200_TARGETB_FRAGMENT_PATH.md`.

**1. The fragment path is CORRECT — proven twice.**
- App-exact isolation test (`scripts/s200_pgl_blend_test.cpp`): the real vertex format is the gdx SpriteBatch **20-byte vertex** (`pos 2×F32 + color 4×u8@+8 + uv 2×F32@+12`) — decoded from a draw-time hexdump (`0000b841 0000f242 000000fe 0000043d 0000803a` = x=23, y=121, RGBA(0,0,0,254), uv=(0.0322,0.0010)). Replaying that exact path through PGL lands pixels precisely as the shader math predicts — including blend with **alpha > 1** (a=17.6 → committed black; a=0.7 → exact 0x4c4c4c).
- Live run: tile fragments sample REAL texels (`texel.a=1.000`, `out=0,0,0,17.6`) and the pixels reach the framebuffer.

**2. The first real textured quad is ON SCREEN.** The face's only non-white content — previously read as SW-path glyphs — is the game's **96×96 tile quad (draw count=6, texture name 4)** at the panned-camera position (x≈468, y≈1750+). Its geometry matches the upload dump's art bbox (16,8)-(76,80). A real APK texture, uploaded by the app, sampled by the app's own shader path, blended, presented through `stage_gl_surfaces`.

**3. Texture objects are sound.** The new texture audit shows all 4 uploads land on the right PGL objects with real data (3 font pages 1024×1024 + the 96×96 tile), and the bind→draw mapping is clean (30←tex2, 6←tex4, 12←tex3, 66←tex1).

**4. The remaining wall is NAMED: the font pages upload EMPTY** — all three 1024×1024 pages are pure (255,255,255,0); the glyph blit never draws. Root pinned: the FreeType native family hits the engine **STUB tail** (`[W18-FT-BRIDGE] stub tail`: initFreeTypeJni, newMemoryFace, setPixelSizes, loadChar, getGlyph, getMetrics) **while the real `libgdx-freetype.so` is loaded and DOES export the symbols** (`nm -D` verifies `Java_..._00024Face_loadChar` etc. — the F-NEW-611 `_00024` mangling is already right). Stub-minted fake handles → the downstream real renderGlyph/getBitmap fail → gdx `generateGlyphAndBitmap` → null → pages stay white → **all text draws (counts 30/12/66) sample transparent white**. One wall, now named, between the runtime and a fully rendered tictactoe.

**5. Second bug pinned (cosmetic until #4 falls): the a_color buffer-position law.** The bridge serves the color attribute at base+0 instead of base+8 — the vertex color reads position bytes (`v_color=(0,0,184,65)` for pos (23,121)). The shared FloatBuffer is repositioned (0→2→3) between the three attribute binds; the color bind's position=2 is missed while uv's position=3 lands. One law to fix at the marshal.

**6. Acquittals worth recording:** the PGL const map is CORRECT (`0x302→87` IS PGL's GL_SRC_ALPHA; `0x1406→248` IS PGL's GL_FLOAT — counted from the enum head); dooz emits **zero** GLES-bridge calls (View lane — tictactoe is the first real app through the sb pipeline, which is why no golden ever exercised this family).

**Gates on the same canonical binary (fresh post-investigation proof):** goldens **3/3 ALL HOLD** (bouncy `8a6c24ac` / unote `3b8dcb0a` / dooz `31ddd4d5` — pin invocation, rerun-identical), gmdice 5-tap **PASS** (rerun-identical), microtimer spot **0 uncaught**. Floor 11/11 verified on this exact binary identity in commit `00783ccd`; the rebuild is deterministic.

**Next P0 (single named task):** make the FreeType family resolve the REAL `libgdx-freetype.so` symbols (F-C4-594 native-precedence for this library — symbols exist, mangling is correct, find why the lookup missed) or give the engine stub a real-bitmap leg backed by the runtime's own FreeType (already linked for text_shaper; the font is already registered via FONT_SOURCE). Then text renders → the menu becomes tappable → the board/X-O screen is reachable → full interaction proof."""

posted = {}
IDS = pathlib.Path('/home/z/my-project/evidence/s200/posted_comment_ids.json')
if IDS.exists():
    posted = json.loads(IDS.read_text())

KEY = '557_targetB_fragpath'
if posted.get(KEY):
    print(f"already posted: {posted[KEY]}")
else:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/issues/557/comments",
        data=json.dumps({"body": BODY}).encode(),
        headers=HDRS, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            j = json.load(r)
        posted[KEY] = j.get("id")
        IDS.write_text(json.dumps(posted, indent=1))
        print(f"#557: POSTED {j.get('id')} -> {j.get('html_url')}")
    except Exception as e:
        print(f"#557: FAILED {e}")
