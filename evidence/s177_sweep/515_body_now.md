# ISSUE 515 [Coder6] state=open

# CODER-6 ACHIEVEMENT 4 — WAVE 8: the [C6-GLBD] index-mesh law set — Mindustry's scene FBO receives REAL app geometry

**App:** Mindustry 7.0 build135 (`io.anuke.mindustry`), APK sha16 `64bf33842d8f5495`
**Binary:** sha16 `4ceec0ade8380d4d` (S157 base + full C6 wave-1..7 law set + wave-8 GLBD)
**Case file:** #441 · wave-8 report → [comment](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/441#issuecomment-6616060325) · board → [comment](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/437#issuecomment-6616068335)

## What the wave closed
The wave-7 frontier ("glBufferData=0 → pure clear-color frames") decomposed into **four independent generic roots**, each fixed and verified live:

| # | root | law | live effect |
|---|---|---|---|
| R-a | typed-view bulk put was `[F`-only — `ShortBuffer.put([S,int,int)` (arc IndexArray.set, 24576-short index upload) fell through | primitive-array bulk put for ALL prim arrays | index data lands in the view + parent backing |
| R-b | `IndexArray.size()` answers `buffer.limit()` — the no-arg `limit()` GETTER was unhandled (fail-soft 0) | nio getter law | `VertexData$-CC.$default$render` takes the DrawElements branch |
| R-c | the bridge read `count=I(2)/type=I(3)` — the TYPE (5123) was consumed as the index count → degenerate draws | glDrawElements overload-shape law | 313 real indexed draws, correct count/type |
| R-d | arc refills its one shared FloatBuffer between `glVertexAttribPointer` and the draw — the staged client store was stale | draw-time re-stage from the live heap backing | guard skips 40 → **0** |

## Verify
- `[C6-DRAWGUARD]` skips: 40 → **0**
- `glDrawElements`: 0 → **313 calls** (GL_TRIANGLES, GL_UNSIGNED_SHORT, element VBO)
- scene-FBO tex15: sentinel `0xefbeadde` everywhere → **22568 px real geometry** (`0x00ffffff` — the Mindustry logo, mid-screen rows ~499)
- vertex truth: `[C6-MESH] v0 pos=884.851,960 col=127,105,63,254` — real SpriteBatch vertex bytes
- engine allocations re-proven CORRECT via androground ground truth (16384 verts × 24B = 393216B; 24576 shorts = 49152B)

## Honest frontier
`frame verdict = DEFAULT_BACKGROUND_ONLY` — the window-composite/presentation of the scene FBO is the registered wave-6 bloom-combine frontier. Wave 8 proved the SOURCE (scene FBO carries real geometry) and unblocked the composite work.

## Workflow
Commit `4a5a9c93` on branch `c6-wave8-engine` (LOCAL — this session's token is Issues:write only; Contents push 403, same wall as waves 5–7; a Contents session can push `c6-wave8-engine` + `c6-wave8-glbd` verbatim). Evidence: `evidence/c6/w8_glbd/` in the commit.
