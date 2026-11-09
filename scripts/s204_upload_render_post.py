#!/usr/bin/env python3
"""S204 — GAME RENDER UPLOAD: post the real tictactoe render images (board +
X/O interaction) as embedded images on #557, with the permanent raw-github
links and the external image-host links. Golden rule: a deliverable exists
only once it is PUSHED."""
import json, subprocess, sys
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
LEDGER = Path('/home/z/my-project/evidence/s200/posted_comment_ids.json')

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

BODY = """# [GAME RENDER — UPLOADED] The real tictactoe render, as requested (image-upload links + embedded)

Two frames from the S204 board-fell verification (binary `4f5c5b9a11a8b9d2`,
HEAD `0979678e`), uploaded to external image hosts AND committed to this
public repo (raw links below are permanent):

## 1. After interaction — X (center) + O (top-left) rendered by the app's own turn state machine
![tictactoe X/O on board](https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/evidence/s204/runs/s204_ttt_tap2/screenshot.png)

- external: https://d.uguu.se/CEBorfie.png (uguu.se) · https://tmpfiles.org/w0ADWoVsTfoc/screenshot.png (tmpfiles.org)
- permanent raw: https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/evidence/s204/runs/s204_ttt_tap2/screenshot.png

## 2. Deterministic no-tap face — board grid + score `0 | 0` + restart glyph (identical sha256 ×3 reruns)
![tictactoe clean board](https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/evidence/s204/runs/s204_ttt0/screenshot.png)

- permanent raw: https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/main/evidence/s204/runs/s204_ttt0/screenshot.png

**Facts attached to these pixels** (full verdict = comment 6741461031):
- sha256 of the no-tap face: `f1157d7eba20bedf…` (deterministic ×3); tap face: `446dbeb0d7c10836…`.
- DrawElements now fires with real quad index runs `i0..5 = 0,1,2,2,3,0` (was zero in the whole run pre-S204).
- Root cause that fell: F-NEW-630 typed-view `limit()` GETTER — gdx `VertexBufferObject.getNumVertices = buffer.limit()*4/vertexSize` answered 0, so `Mesh.render`'s count==0 early-out swallowed every ShapeRenderer pass.
- Gates on the same binary: bouncy original pin `8a6c24ac` RESTORED, unote `3b8dcb0a`, dooz `a0fae907`, gmdice `3891679d` rerun-identical, microtimer 0-uncaught — ALL HOLD.
- Still visible in frame 2: title/score text renders as solid colored blocks — the SpriteBatch text route draws but samples the font atlas incorrectly; that is the named next frontier (next free law F-NEW-631).

Both images were uploaded to third-party hosts per the request (links above; tmpfiles.org expires in ~60 min, uguu.se in ~48h) and are permanently served by this repository."""

if __name__ == "__main__":
    cid = post(557, BODY)
    led = json.loads(LEDGER.read_text())
    led["557_render_upload"] = cid
    LEDGER.write_text(json.dumps(led, indent=1))
    print("ledger updated:", cid)
