#!/usr/bin/env python3
"""S204 — the L-04 board-wall verdict: push to #557 (Coder 3) + #536 central."""
import json, subprocess, sys

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


def post(issue, body):
    TOK = token()
    r = subprocess.run(["curl", "-s", "-X", "POST",
                        "-H", f"Authorization: token {TOK}",
                        "-H", "Accept: application/vnd.github+json",
                        "-d", json.dumps({"body": body}),
                        f"https://api.github.com/repos/{REPO}/issues/{issue}/comments"],
                       capture_output=True, text=True)
    j = json.loads(r.stdout)
    cid = j.get("id")
    if not cid:
        print(f"POST FAIL #{issue}: {r.stdout[:300]}")
        sys.exit(1)
    print(f"POSTED #{issue} comment id={cid}")
    return cid


V557 = """# [S204] THE BOARD WALL FELL — first real tictactoe BOARD + full tap interaction on screen; ONE missing law (F-NEW-630 typed-view limit() GETTER) was the whole L-04 wall | Binary **`4f5c5b9a11a8b9d2`** (HEAD `40eee95e`, pushed)

Continues the S203 record. The named suspects ("zero glDrawElements in the whole run; ShortBuffer.put([SII) index fill + the DrawElements dispatch") are now both RESOLVED — and the resolution came from an unexpected direction: **the two suspects were the same one-law wall.**

## 1. What the dex ground truth showed (before any fix)

Invoke census of the app's own classes (`s204_ttt_invoke_census.py`, dex ground truth, no guessing):
- `TicTacToeRenderer.draw` = `Input.justTouched` → `ShapeRenderer.begin/setColor/rect×4/end` (the grid) → `+ rectLine` (win line) — **NO menu screen exists; the board draws from frame 1**.
- `XActor.draw` = `ShapeRenderer.begin/rectLine×2/end`; `OActor.draw` = `begin/circle×2/end`.
- The board route is **gdx ShapeRenderer → ImmediateModeRenderer20 → Mesh** — NOT an app-specific DrawElements mesh. The SpriteBatch quad run is separate (its index path was the "DrawElements route" suspect).

## 2. The ordered method-trace window (the exact stop)

`MINIANDROID_METHOD_TRACE` + GL_DEBUG, per flush:
`ShapeRenderer.begin → rect×4 → IRM20.vertex×24 → IRM20.end → flush → ShaderProgram.begin → glUniformMatrix4fv (u_projModelView — the engine=2 line) → Mesh.setVertices → VBO.setVertices → BufferUtils.copy → bufferChanged → Mesh.render(2-arg) → IndexBufferObject.getNumMaxIndices → Mesh.getNumVertices → VBO.getNumVertices → …` **→ next entry = ShaderProgram.end.** No bind, no glDrawArrays, no unbind. gdx 1.9.10 law: `Mesh.render: if (count == 0) return;` — the early-out fired.

## 3. The root cause (ONE law)

- gdx law: `VertexBufferObject.getNumVertices() = buffer.limit() * 4 / attributes.vertexSize` — `buffer` is the **FloatBuffer typed VIEW** (`byteBuffer.asFloatBuffer()`).
- Engine: the typed-view block had `position()` (getter), `position(int)`/`limit(int)` (setters, F-NEW-610), `capacity`, `remaining`, `flip`, `clear`, `rewind` — but **NO no-arg `limit()` GETTER**. The generic miss answered 0 → getNumVertices = 0 → `count==0` → every shape pass silently swallowed (`Mesh.render` ×120, zero draws from prog=2 across 40 frames).
- **The same getter gates the SpriteBatch DrawElements route** (its index ShortBuffer view reads `limit()` too) — which is why S203 saw "zero glDrawElements in the whole run". One law, two named suspects.

**F-NEW-630 (S204): typed-view `limit()` getter + `hasRemaining()`** (the ByteBuffer parent law has both; the view block now does too — OpenJDK view-cursor independence). One file: `dalvik_engine.cpp` (typed-view family).

## 4. The proof (canonical `4f5c5b9a11a8b9d2`)

- **The board renders**: `#` grid + score `0 | 0` + restart ↻ glyph — from the app's OWN ShapeRenderer art, frame 1, no taps. No-tap face **`f1157d7eba20bedf` ×3 byte-identical** (was `0cd50fa91686a751` = grid-less), honest gate center-64×64 = **1 color** (clean white, zero noise), 0 uncaught.
- **DrawElements now fires**: `[GLDBG] DELE count=66 i0..5=0,1,2,2,3,0` … real quad index runs (was zero in the whole run). The shape pass draws `mode=4 count=24` per frame — exactly 4 rects × 6 verts.
- **FULL INTERACTION**: tap center cell → **X renders** (rectLine×2); tap top-left → **O renders** (circle×2) — the app's own turn state machine working end-to-end, 0 uncaught, face `446dbeb0d7c10836`.

## 5. The gates (all HOLD — and one golden IMPROVED)

| Gate | Result |
|---|---|
| bouncy | **`8a6c24ac8a7d718e` — the ORIGINAL pin is BACK.** The S203 delta-24 re-pin (`90c18ddf`) was a symptom of the same view-cursor defect (a SpriteBatch buffer's limit() answering 0 shifted one overlay blend); root-caused away, the byte-exact golden holds again. Re-pin withdrawn. |
| unote | `3b8dcb0adbbc17a9` EXACT HOLD |
| dooz (plain) | `a0fae9072313e2d1` HOLD (pin protocol `31ddd4d5b8e6d18e` untouched) |
| gmdice 5-tap ×2 | rerun-identical `3891679dff449331` == standing record |
| microtimer | 0 uncaught, `b39665f68f3938e6` == standing record |
| tictactoe ×3 | deterministic `f1157d7eba20bedf` ×3, 0 uncaught |

## 6. What remains (next named walls, in order)

1. **Text glyphs render as SOLID tinted blocks** (title/score quads: blue/cyan rectangles, no glyph shapes — the ↻ arrow glyph renders FINE via the font-page route, so the wall is the BitmapFont-tint quad path's alpha/glyph-mask sampling, not the atlas itself). Named next.
2. **L-06 win/stalemate**: 3-in-a-row tap sequence → winning `rectLine` + the winner text update (route now proven — `TicTacToeRenderer.draw`'s `rectLine` leg).
3. Then: 3 clean runs with a full game → the completion rule on tictactoe.

Ledger: L-04 **DONE (board + interaction, pixel-verified)**; L-05 tap-reachability **DONE for the board route** (X/O proven); L-06 open behind the win-line taps; text-glyph blocks = the next named wall. Full evidence: `evidence/s204/` (S204_PROBE.json, S204_GATE.json, runs/), commit `40eee95e` pushed."""

CID1 = post(557, V557)

CENTRAL = """# [S204 central record] THE TIC-TAC-TOE BOARD WALL FELL — F-NEW-630 (typed-view limit() getter): one missing law WAS the L-04 wall; first real board + full X/O tap interaction on screen; bouncy golden RESTORED to the original pin

- Binary **`4f5c5b9a11a8b9d2`** (HEAD `40eee95e`, pushed). Commit message carries the full chain: dex invoke census → ordered METHOD-TRACE window → `Mesh.render count==0` early-out → gdx law `VBO.getNumVertices = buffer.limit()*4/vertexSize` → **the typed-view block had no no-arg `limit()` getter** (F-NEW-610 landed setters only) → F-NEW-630 (getter + hasRemaining).
- **Proof**: board `#` grid + `0 | 0` + ↻ from frame 1 (no-tap face `f1157d7eba20bedf` ×3, center-64×64 = 1 color, 0 uncaught); DELE fires with real quad index runs (was zero in run); tap → **X renders**, tap → **O renders** (turn state machine live).
- **Gates all HOLD**: unote `3b8dcb0a` / dooz `a0fae907` / gmdice `3891679d` ×2 identical / microtimer 0-uncaught `b39665f6` / ttt deterministic ×3 — and **bouncy returned to the ORIGINAL pin `8a6c24ac8a7d718e`** (the S203 delta-24 re-pin `90c18ddf` withdrawn: symptom of the same view-cursor defect, now root-caused away).
- Next named walls: ① text glyphs as solid tinted blocks (BitmapFont-tint quad alpha/mask path — the ↻ glyph renders fine, so the atlas is healthy), ② L-06 win-line (`rectLine` leg now proven reachable), ③ full-game 3-clean-runs completion.
- Coder-3 S202-W2 wave-2 verdicts also pushed this session (#557 c=6740701981): probe reproduced EXACTLY, F-NEW-627 ≡ main F-NEW-626b convergence, 612b-restore superseded by 626d, renumber 626a→628/626b→629, next free F-NEW-630 (now consumed by this wave — next free **F-NEW-631**)."""

CID2 = post(536, CENTRAL)

led = json.load(open('/home/z/my-project/evidence/s200/posted_comment_ids.json'))
led.update({"557_s204_board_verdict": CID1, "536_s204_board_record": CID2})
json.dump(led, open('/home/z/my-project/evidence/s200/posted_comment_ids.json', 'w'), indent=1)
print("ledger updated")
