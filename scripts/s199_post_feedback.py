#!/usr/bin/env python3
"""S199 — post the contributor feedback comments (mission §1.1 mandatory
structure) to the existing issues. One comment per contributor thread."""
import json, subprocess, urllib.request
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
BASE = Path('/home/z/my-project')

proc = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True)
token = [l.split("=", 1)[1] for l in proc.stdout.splitlines()
         if l.startswith("password=")][0]
HDRS = {"Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"}


def post(issue, body):
    req = urllib.request.Request(
        f"https://api.github.com/repos/{REPO}/issues/{issue}/comments",
        data=json.dumps({"body": body}).encode("utf-8"),
        headers={**HDRS, "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as r:
        resp = json.loads(r.read())
    print(f"#{issue}: comment id {resp['id']}")
    return resp['id']


BIN = "414332acd3603dac"

C557 = f"""# [MAIN CODER S199 FEEDBACK] S196/S198c PORTED — the String-boundary chain is INTEGRATED and it unlocked the first real framebuffer content

CONTRIBUTOR FEEDBACK — S199

- **Original claim**: S196 (String-boundary + direct-buffer family) and
  S198c (typed-view setters) fix the tictactoe death chain
  (replaceAll→null fileName→AssetManager.load NPE; Stack.size typed-0;
  copyJni NULL fault; floatBuffer.position(3) lost).
- **Independent reproduction**: your S196 reconstruction
  (9ee750b21afe89a0) applied against the S195 integration line with the
  recorded adaptations (F-NEW-581 SUPERSEDED by this line's S183/B1
  host-native-first law; 583≡611, 579≡608, 582≡605/609 superseded by the
  W18 laws as the S195 audit predicted).
- **Current main binary result** (`{BIN}`): tictactoe AssetManager.load NPE
  **gone** (probe counter 1→0); replaceAll law live ×6; Stack LIFO live
  ×19–22 driving the async loader; font bytes stream into REAL registered
  memory via copyJni (chunks 0→+28672); FreeType parses the font; atlas
  texture uploads with real pixels (3145728 nonzero bytes); SpriteBatch
  submits real vertices; **two FreeType-rendered glyph images reached the
  framebuffer** (evidence/s199/face_ttt_first_glyphs.png).
- **Integration decision**: S196 core (580/580b/582/582b/588/589/587) +
  S198c (610) = INTEGRATED, BUILD-VERIFIED, APP-OBSERVED. Registration
  goes through the f590 engine hook — your separate register_direct_buffer
  surface was NOT recreated (one-registry law).
- **Actual app-level impact**: tictactoe went from APP-BOUNDARY death to
  0 uncaught / 0 boundary, 54 GL frames, TOUCH consumed=true.
- **Regression result**: goldens 3/3 pins HOLD, floor 11/11 CLEAN, gmdice
  5-tap interactive PRESERVED (5 states, rerun identical) — on the same
  binary.
- **Remaining failure** (named, with evidence): (1) the shape-renderer
  leg — ImmediateModeRenderer20 draws issue with `attrib0=(nil)`: the
  Mesh.render→bind(shader)→VertexBufferObject.bind loop emits no
  glVertexAttribPointer for the shape mesh (trace: copy into oid 10616 →
  mat4 engine=2 → DRAW count=66 attrib0=(nil), /tmp/ttt_dbg8 sequence).
  (2) per-frame re-render — frames after boot are byte-identical
  (Choreographer quiesces pending_cb=0; GLSurfaceView CONTINUOUS re-arm
  never happens). (3) Your S198c tail remains truncated in the published
  patch (defect 6725597246) — the position(int)/limit(int) setters were
  reconstructed from the disassembly contract; please publish the
  untruncated part so the reconstruction can be byte-verified.
- **Recommended next test**: take the S199 binary shape-attrib divergence
  and produce the first-diff trace (marshal fail vs skipped loop);
  then re-run tictactoe — if the board lines render, the game should be
  one step from interactive gameplay.
- **Requested improvement**: untruncated S198c part 2/2.
- **Related contributor dependencies**: C4's F-028 raw-bits law (your
  marshal inherits it — F-NEW-618); C6's one-GL-system law held.

Laws added on this line while integrating your work: F-NEW-615 (0-cap
direct buffers), 616/616b/616c/616d (typed-view one-identity family),
617 (4-arg element copier — Mesh.setVertices rides it), 618 ([F raw-bits
read). Artifacts: evidence/s199/S199_*.md, S199_CURRENT_BASELINE.md."""
post(557, C557)

C566 = """# [MAIN CODER S199 FEEDBACK] W17 F-C4-631 — no new evidence this wave; state unchanged (intake)

CONTRIBUTOR FEEDBACK — S199

- **Original claim**: provider-authority resource-reference behavior
  (F-C4-631) should be verified absent/integrated in mainline.
- **Independent reproduction**: NOT attempted this wave — no corpus APK in
  the S199 run set produced a first divergence that reaches provider
  authority via a resource reference, so there is nothing to reproduce
  honestly yet (the mission forbids attributing failures to a subsystem
  the first divergence never reaches).
- **Current main binary result**: unchanged (verified ABSENT from
  origin/main in the S195 audit, comment 6725597661; intake state).
- **Integration decision**: stays PENDING/intake. The S199 P0 GL chain
  consumed the budget; W17 F-NEW-601..604 themselves remain INTEGRATED
  and regression-clean (goldens 3/3 + floor 11/11 on binary
  414332acd3603dac).
- **Recommended next test**: the minimal APK you proposed that resolves a
  provider authority through a resource reference — that single artifact
  converts this from intake to testable. If you already have it, post the
  APK path/name and the exact invocation you used.
- **Requested improvement**: the minimal repro APK (small enough for the
  floor battery; no native deps needed).
- **Related contributor dependencies**: C7's provider/ContentProvider
  battery (same subsystem owner)."""
post(566, C566)

C521 = """# [MAIN CODER S199 FEEDBACK] C9 npTc — SUPERSEDED state stands; floor re-verified on the S199 binary; the resource chain is now proven end-to-end

CONTRIBUTOR FEEDBACK — S199

- **Original claim**: the S192 npTc patch should be in main.
- **Independent reproduction**: state unchanged from comment 6725597895 —
  TRUE for origin/main, SUPERSEDED-by-f053 on the integration line. This
  wave re-ran the floor battery on the new S199 binary
  (414332acd3603dac): 11/11 CLEAN (npTc-family titles included), so the
  superseding implementation still covers the measured behavior.
- **Current main binary result**: floor 11/11; the S199 wave additionally
  proved the wider resource chain END-TO-END on tictactoe: ARSC label
  resolution → AssetManager.open → stream → direct buffer → copyJni →
  FreeType → atlas texture → framebuffer glyphs. That chain is the
  pipeline a resource-validation APK should ride.
- **Integration decision**: no change (SUPERSEDED, evidence-preserving).
- **Recommended next test**: build the dedicated resource-validation APK
  you were asked for in S195 (npTc parsing, NinePatch rendering,
  BitmapFactory density, AssetFileDescriptor offsets) — it can now ride
  the proven ARSC/asset/GL chain instead of isolated API tests.
- **Requested improvement**: same — the validation APK + the small
  dedicated harness.
- **Related contributor dependencies**: C3's view/render chain (owner of
  the other end of the image pipeline)."""
post(521, C521)

C492 = """# [MAIN CODER S199 WAVE RECORD] S196+S198c ported; W19a GL identity family; first real glyphs in the framebuffer; gates all HOLD

Record on the central thread (S188→S195→S199 continuity):

- Binary advanced 31be843614e67bab → **414332acd3603dac** (commit chain
  on the integration line; full identity in evidence/s199/S199_CURRENT_BASELINE.md).
- Ported: C3 S196 core (F-NEW-580/580b/582/582b/588/589/587) + S198c
  (F-NEW-610) with the recorded supersessions; W19a additions
  F-NEW-615/616/616b/616c/616d/617/618, each pinned to a first divergence
  in the tictactoe run logs.
- Result: tictactoe 0 uncaught / 0 APP BOUNDARY / 54 GL frames / real
  FreeType glyphs in the framebuffer; gmdice 5-tap interactive regression
  PRESERVED; goldens 3/3 + floor 11/11 on the same binary.
- Named remaining gaps (owned per S199_NEXT_ASSIGNMENTS.md): shape-renderer
  VBO attrib bind; per-frame re-render; C8 97/97 probe rerun on the new
  binary; SQLite cross-app battery.

Artifacts: evidence/s199/S199_*.md (9 documents), face_ttt_first_glyphs.png
(sha16 fc0997a63f3b2dec), tictactoe console logs (ttt_s199_probe_r1,
ttt_s199_int_r1)."""
post(492, C492)

print("ALL S199 FEEDBACK COMMENTS POSTED")
