# S199 NEXT ASSIGNMENTS — per coder, evidence-based

Recorded: 2026-11-08 20:03 UTC. Binary 97628b00d237f9eb.

## Coder 3 (owner: the two named tictactoe walls)
1. Shape-renderer VBO attribute bind: the ImmediateModeRenderer20 draws
   issue with attrib0=(nil) — Mesh.render → bind(shader) →
   VertexBufferObject.bind loop does not emit glVertexAttribPointer for
   the shape mesh. Reproduce: `/tmp/ttt_dbg8.log` sequence (copy into
   o10616 → mat4 engine=2 → DRAW count=66 attrib0=(nil)). Deliver the
   first divergence (marshal fail? skipped loop?) with a trace.
2. Per-frame re-render: frames after boot are identical (frame_000 ==
   frame_023). The GLSurfaceView CONTINUOUS render re-arm never happens;
   Choreographer quiesces at tick=0 with pending_cb=0. Make the shape
   draws appear per frame, then re-run the tictactoe 3-run battery.
3. gmdice stays the permanent interactive regression — no new test needed.

## Coder 2 (corpus): rank the next 5–10 small APKs by §2 (microtimer
validated end-to-end first). Include per-APK: launcher, native deps,
API path, expected difficulty, what it validates.

## Coder 4: W17 F-C4-631 stays intake; provide the minimal repro APK.
Audit W15–W17 laws for overlaps with the S199 identity family (the
one-identity direct-buffer law supersedes any per-app buffer law).

## Coder 5: authoritative sources for (a) gdx VertexBufferObject.bind VBO
semantics (what glVertexAttribPointer receives with a bound GL_ARRAY_BUFFER
— offset vs pointer), (b) Choreographer/GLSurfaceView continuous render
re-arm. Deliver minimal distinguishing tests, not reports.

## Coder 6: the shared chain now renders real texture content; do NOT
return to Mindustry until the shape-line leg renders (small APK first —
tictactoe IS the small test APK). No second GL system (mission §4 law held:
one registry, one marshal).

## Coder 7: build the SQLite 1–2 min regression battery + the 3-DB-APK
selection (see S199_SQLITE_IMPACT.md); the cross-package scenario battery
remains as scoped in S195.

## Coder 8: rerun the 97/97 marker probe + 3-run determinism on 97628b00d237f9eb
(the W11/W12 patch stack is untouched but the binary changed). Then the
real-APK async test (§2 C8): any cohort app doing post-launch async UI
work counts.

## Coder 9: the S192 npTc SUPERSEDED state stands; deliver the dedicated
resource-validation APK (§2 C9) exercising npTc/BitmapFactory density/
AssetFileDescriptor — the ARSC label + asset stream chain is now proven
end-to-end, so the validator rides a real pipeline.


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
