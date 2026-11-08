# S199 CROSS-SUBSYSTEM GRAPH — shared chains proven by the wave

Recorded: 2026-11-08 20:03 UTC. Each row is a producer→consumer pair this wave's evidence
actually exercised (the tictactoe + gmdice runs are the witnesses).

## Chain A — UI chain (View → input → state → frame) — gmdice PROVEN
`Launcher/Activity (ViewShadow) → layout/measure (DEX-MEASURE) →
ViewTree render (EXP092) → input dispatch (UI-EVENT TOUCH, consumed=true)
→ app state change (dice result region) → next frame reflects it →
replay identical`. gmdice: 5 taps → 5 distinct states, rerun identical.

## Chain B — resource chain (APK → ARSC → assets → decode → view/pixmap)
`APK parse → ARSC label ("TicTacToe" via canonical resolver) →
AssetManager.open (STREAM-READ) → StreamUtils.copyStream → direct buffer
(F-NEW-582 real memory) → copyJni (F-NEW-582b) → FreeType native parse →
glyph bitmap → Gdx2DPixmap (F-NEW-615 0-cap law) → atlas texture upload
(GLDBG tex2D 1024×1024 nonzero=3145728) → SpriteBatch (F-NEW-616/617) →
screen glyphs`. Proven to the framebuffer this wave.

## Chain C — libGDX GL chain (DEX → JNI → native GL → framebuffer)
`DEX invoke → AndroidGL20/GLES20 dispatch (F-C4-594 native precedence →
GLES20Bridge) → marshal (F-NEW-616 parent-first, F-NEW-618 raw-bits) →
portablegl → PGL backbuffer → stage_gl_surfaces copy → framebuffer`.
Glyphs rendered; shape-line leg = the named next fix.

## Chain D — background chain (thread/async → state → UI)
`AssetManager async task (Stack F-NEW-589 + Executor/FUTURE boxes) →
task completion → Gdx.app.postRunnable → Handler pump → GL thread frame`.
The async font load completed and the GL frames presented (54 frames).

## Chain E — multi-app chain
Route law: `[ROUTE] REQUIRED_CAPS caps=NATIVE_LIB_LOAD,JNI,EGL_GLES,
ASSET_MANAGER,MEDIA_DEMUX_PER_ASSET` recorded for tictactoe;
ROUTE_VIOLATION=0 across all S199 runs.

## First-divergence clusters touched this wave
| Cluster | First divergence | Owner law | Apps it can improve |
|---|---|---|---|
| String identity-form | receiver OBJECT_REF read "" | F-NEW-580/580b/588 (C3) | any Properties/i18n app (halma W19b next) |
| Direct-buffer identity | view vs parent storage | F-NEW-616 family | all libGDX GL titles |
| Element copier | 4-arg copyJni missing | F-NEW-617 | all Mesh-based GL titles |
| Float raw bits | INT32-in-[F numeric cast | F-NEW-618 | all Matrix4/uniform apps |
| 0-cap buffers | capacity<=0 rejected | F-NEW-615 | empty-glyph fonts, 0-dim pixmaps |


## NOTE — identity refresh (S199 close)
The S199 wave made two further source commits after the baseline was
written (F-NEW-619 typed-view parent chase at the f590 hook; F-NEW-620/
620b GL_ACTIVE_ATTRIBUTES=3 + glGetActiveAttrib canonical-name law).
The FINAL canonical S199 binary is 97628b00d237f9eb — goldens 3/3 ALL
HOLD and floor 11/11 CLEAN re-verified on it (this is the identity all
future waves compare against). The 619/620 laws did NOT yet move the
shape-attrib needle (glGetActiveAttrib never dispatched — the
fetchAttributes loop is gated deeper, at the AndroidGL20 real-native
path); that remains the named Coder-3 frontier with the evidence above.
