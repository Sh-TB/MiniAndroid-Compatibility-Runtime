#!/usr/bin/env python3
"""S199 deliverables — the 9 required documents + worklog entry.
Every claim is tied to an artifact on disk; observed facts are separated
from interpretations and proposed work."""
import json, hashlib, subprocess, datetime
from pathlib import Path

BASE = Path('/home/z/my-project')
OUT = BASE / 'evidence/s199'
OUT.mkdir(parents=True, exist_ok=True)

BIN = BASE / 'miniandroid/build/miniandroid'
BIN_SHA = hashlib.sha256(BIN.read_bytes()).hexdigest()
BIN16 = BIN_SHA[:16]
head = subprocess.run(['git', 'log', '--oneline', '-1'], cwd=BASE / 'miniandroid',
                      capture_output=True, text=True).stdout.strip()
dirty = subprocess.run(['git', 'status', '--porcelain'], cwd=BASE / 'miniandroid',
                       capture_output=True, text=True).stdout.strip()
DT = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

# ---------- 1. S199_CURRENT_BASELINE.md ----------
(OUT / 'S199_CURRENT_BASELINE.md').write_text(f"""# S199 CURRENT BASELINE

Recorded: {DT}

## Environment
- Runtime repo: `/home/z/my-project/miniandroid` (branch `main`)
- HEAD at wave start: `74d7693a` (S195 integration line, binary 31be843614e67bab)
- HEAD at S199 close: `{head.split()[0] if head else 'n/a'}`
- Working tree at close: {'CLEAN' if not dirty else 'DIRTY: ' + dirty[:120]}

## Canonical integrated binary
- Path: `miniandroid/build/miniandroid`
- SHA-256: `{BIN_SHA}`
- sha16 (evidence records): `{BIN16}`
- Built from HEAD with `make -j$(nproc)` (reproducible-build law: rebuild
  from the same tree reproduces the same sha16 — re-verified this wave)

## What changed this wave (S199 P0 chain)
Laws ported / implemented on top of the S195 line (all committed):
| Law | Source | Content |
|---|---|---|
| F-NEW-580 | C3 S196 | S100 String-family receiver identity-form normalization (heap-String OBJECT_REF read via `__string_value__`/`value`) |
| F-NEW-580b | C3 S196 | bridge_to_api boundary String receiver normalization (the ONE chokepoint; alias keeps zero cost for non-heap receivers) |
| F-NEW-582 | C3 S196 | engine allocateDirect + newDisposableByteBuffer mint REAL calloc'd backing, register through the f590 hook (ONE registry — no second registry per mission §4 C6) |
| F-NEW-582 put/get mirror | C3 S196 | ByteBuffer bulk put([B)/put(ByteBuffer)/get([B) + put_wide/get_wide real-memory mirror |
| F-NEW-582b | C3 S196 | BufferUtils.copyJni 5-arg byte form (engine-side REAL law, structural arg resolution) |
| F-NEW-588 | C3 S196 | heap-String replace family: replaceAll/replaceFirst/replace(CharSequence)/replace(CC)/matches/contains with real regex semantics (regex_error falls through honestly) |
| F-NEW-589 | C3 S196 | java.util.Stack REAL LIFO (push/pop/peek/size/empty; AssetManager taskQueue) |
| F-NEW-587 | C3 S196 | GLES20.glGetString GL_EXTENSIONS law (GLTexture.<clinit> supportsExtension) |
| F-NEW-610 | C3 S198c | typed-view position(int)/limit(int) setters (reconstructed from the truncated part-2/2 tail, defect #557 6725597246) |
| F-NEW-615 | S199 W19a | zero-capacity direct-buffer validity (AOSP: 0-cap direct ByteBuffer is well-formed; NewDirectByteBuffer(pixels,0) must answer a box) |
| F-NEW-616 | S199 W19a | GL marshal TYPED-VIEW PARENT-FIRST resolution (the view's own f590 lookup took the zeroed __bb_b{{i}}__ snapshot leg) |
| F-NEW-616b | S199 W19a | typed-view put/get PARENT MIRROR (one identity, engine writer surface) |
| F-NEW-616c | S199 W19a | GL out-param write-back mirrors into parent memory (glGetShaderiv/glGetIntegerv/gen*) |
| F-NEW-616d | S199 W19a | one identity, TWO mint forms: `__bb_addr__` (native-mint) resolved everywhere alongside `__bb_direct__` (engine-mint) |
| F-NEW-617 | S199 W19a | copyJni 4-arg ELEMENT copier ([F Buffer I I — Mesh.setVertices rides it; real native disasm 0x67f0: memcpy(GetDirectBufferAddress(dst), src+off*esz, num*esz)) |
| F-NEW-618 | S199 W19a | [F raw-bits element law in the GLES marshal (F-028 dual convention: INT32-stored float element = raw bits; get_object_array_float_element) |

## Gates at close
- Goldens 3/3 HOLD (bouncy 8a6c24ac, unote 3b8dcb0a, dooz 31ddd4d5) — evidence/s199/../s188_w18 chain, rerun on {BIN16}
- Floor 11/11 CLEAN — scripts/s188_w18_floor_rerun.py output
- gmdice 5-tap interactive regression PRESERVED (5 taps → 5 distinct result states, rerun identical)
""")

# ---------- 2. S199_CONTRIBUTOR_AUDIT.md ----------
(OUT / 'S199_CONTRIBUTOR_AUDIT.md').write_text(f"""# S199 CONTRIBUTOR AUDIT (Coders 2–9) — verified integration states

Recorded: {DT}. Statuses use the S199 evidence-state vocabulary. "Independent
reproduction" = behavior observed on the S199 canonical binary {BIN16}.

## Coder 3 (UI execution / ViewTree / adapter / native GL) — the P0 chain
| Contribution | Original claim | Independent reproduction on {BIN16} | Integration state | App impact |
|---|---|---|---|---|
| S196 F-NEW-580/580b String-boundary | AssetManager.load NPE dies at desc.fileName.equals(null) after replaceAll stub | Ported verbatim; `npe_asset_load` count went 1 → 0 on tictactoe | **INTEGRATED + BUILD-VERIFIED + APP-OBSERVED** | tictactoe passes AssetDescriptor/I18NBundle ladder |
| S196 F-NEW-588 replace family | replaceAll("\\\\\\\\","/") answered null → null fileName | 6 live replaceAll calls logged; `i18n/TicTacToe` path built correctly | INTEGRATED, UNIT-OBSERVED | the named NPE chain closed |
| S196 F-NEW-589 Stack LIFO | Stack.size answered 0 → AssetManager.update believed queue empty | 19–22 live Stack.push/pop/size calls driving the async loader | INTEGRATED | font asset task actually runs |
| S196 F-NEW-582/582b direct-buffer family | copyJni faulted on NULL addresses | copyJni 5-arg live (font bytes stream into REAL memory, chunks 0..+28672) | INTEGRATED | FreeType font parses from REAL registered memory |
| S196 F-NEW-581 loadLibrary NOT-EXTRACTED | host-native not found when APK lib unextracted | SUPERSEDED: this line's S183/B1 host-native-first law already covers the shape (current code attempts host-native before any APK .so attempt) | SUPERSEDED (recorded in #557 reply) | — |
| S198a/b GLES raster + marshal | GL calls execute but nothing rasterizes | draws dispatch (GL_TRIANGLES 66/30/6/12), attribs coherent after F-NEW-616 | INTEGRATED (with the S199 parent-first fix) | font glyphs rasterize end-to-end |
| S198c F-NEW-610 typed-view setters | floatBuffer.position(3) lost → texcoord pointer at 0 | ported from the truncated tail; position/limit setters live | INTEGRATED | attribute offsets correct (attrib2 = base+12) |

## S199 additions the audit surfaced as REQUIRED for the chain
| Law | First divergence it closes |
|---|---|
| F-NEW-615 | Gdx2DPixmap.<init> "Error loading pixmap." on the SPACE glyph (empty outline → 0-cap NewDirectByteBuffer) |
| F-NEW-616/616b/616c/616d | three zeroed attribute pointers (typed views resolved through the view snapshot instead of the parent's real memory); shader COMPILE_STATUS read back 0 |
| F-NEW-617 | mesh vertex data never written (4-arg copyJni missing; Mesh.setVertices path dead) |
| F-NEW-618 | u_projTrans m33 = 1.06535e9 (F-028 raw-bits element read numerically cast) |

## Coder 4 (framework laws) — W17/F-C4-631
- F-C4-631 (provider authority via resource reference): verified ABSENT from
  origin/main in S195 (#566 6725597661 intake). Not touched this wave;
  remains intake (PENDING) — no caller in the current cohort failed on it
  this wave, so no independent reproduction exists yet.
- W17 F-NEW-601..604 remain INTEGRATED/REGRESSION-VERIFIED (goldens hold).

## Coder 9 (resources) — S195/S192 npTc
- npTc patch verified TRUE for origin/main but SUPERSEDED-by-f053 on this
  line (#521 6725597895). No regression: floor 11/11 holds. State stays
  SUPERSEDED; the C9 asset/ARSC chain is INTEGRATED (ARSC label + drawable
  resolution live in the tictactoe run).

## Coder 7 (components/SQLite), Coder 8 (concurrency), Coder 6 (native EGL),
## Coder 2 (corpus), Coder 5 (research)
- C8 W11+W12 97/97 probe: NOT rerun this wave (P0 consumed the budget) —
  PENDING on the S199 binary; the W11/W12 regression surface is covered by
  the floor battery (all HOLD).
- C7 SQLite impact audit: see S199_SQLITE_IMPACT.md (semantic coverage
  audit only — no cross-app claim made).
- C6 Mindustry composite gap: stays OPEN by law (mission §2 C6) — no new
  GL system was created; the S199 identity work advances the shared chain.
""")

# ---------- 3. S199_CONTRIBUTOR_FEEDBACK.md ----------
(OUT / 'S199_CONTRIBUTOR_FEEDBACK.md').write_text(f"""# S199 CONTRIBUTOR FEEDBACK — what was communicated, where

Recorded: {DT}. Comments follow the mandatory S199 response structure.
Posted from this wave (IDs recorded after posting; see the script output):

1. **C3 — issue #557** (S196/S198 verdict thread): S196/S198c PORT verdict
   per law (INTEGRATED/SUPERSEDED), the S199 additions their reconstruction
   made possible (615/616*/617/618), remaining gap = shape-renderer VBO
   attrib bind + per-frame re-render, next test = tictactoe board render
   with the shared chain, request = publish the untruncated S198c tail.
2. **C4 — issue #566** (W17 F-C4-631 intake): no new evidence this wave;
   state stays intake/PENDING; asked for the minimal provider-authority
   resource-reference APK that would let mainline reproduce it.
3. **C9 — issue #521** (npTc): SUPERSEDED state unchanged; floor re-run
   evidence attached (11/11 on {BIN16}); asked for the dedicated
   resource-validation APK (§2 C9) as the next joint test.
4. **C8 — issue #492** (wave record thread): S199 wave record; 97/97 probe
   rerun on the S199 binary named as the next required gate.

Evidence/artifact references embedded in each comment: this directory's
JSON/MD artifacts + the tictactoe run logs + the first-glyphs screenshot
(face_ttt_first_glyphs.png sha16 fc0997a63f3b2dec).
""")

# ---------- 4. S199_SQLITE_IMPACT.md ----------
(OUT / 'S199_SQLITE_IMPACT.md').write_text(f"""# S199 SQLITE IMPACT — honest scope statement

Recorded: {DT}. Binary {BIN16}.

## What is verified
1. `storage/sqlite_shadow.cpp` is INTEGRATED (links real libsqlite3;
   the build line includes -lsqlite3) — state: BUILD-VERIFIED.
2. The S195 cohort battery runs on the same binary show opencalc /
   chessclock / microtimer all reaching REAL_APP_CONTENT — none of them
   is SQLite-blocked on the visible path.

## What is NOT claimed
- No dedicated SQLite semantic battery was run this wave (the P0 GL chain
  consumed the budget). The S195-era isolated-call evidence stands; it is
  NOT re-measured here.
- No cross-app SQLite impact number is claimed: no corpus APK in this
  wave's runs failed on a first divergence that reaches SQLite, so the
  honest statement is "SQLite is not the binding constraint for the
  currently-proceeding cohort", NOT "SQLite is complete".

## Next test (assigned, see S199_NEXT_ASSIGNMENTS.md)
- Build the 1–2 minute SQLite regression battery (create/schema/insert/
  query/update/delete/txn rollback/cursor/persistence) and the three-DB-
  APK selection from the corpus (notes: TODO-apps and any note/list APKs
  in `upload/canonical_apks/` are the natural candidates; Coder 2 to rank).
""")

# ---------- 5. S199_APP_CANDIDATES.md ----------
(OUT / 'S199_APP_CANDIDATES.md').write_text(f"""# S199 APP CANDIDATES — evaluated on the S199 binary

Recorded: {DT}. All candidates below are REAL corpus APKs located and
inspected this wave (no invented names). Depth = observed on {BIN16}.

| App | APK | Architecture | Observed depth this wave | Blocks |
|---|---|---|---|---|
| microtimer | canonical_apks/dubrowgn.microtimer_8.apk | View/Service timer, no GL | 0 uncaught, 0 boundary, REAL_APP_CONTENT ×2 | none observed |
| opencalc | opencalculator_53.apk | View calculator, history DB (Room/SQLite) | 0 uncaught, 1 boundary, REAL_APP_CONTENT | the 1 boundary (persistence path) |
| chessclock | chessclock_29.apk | View + service | 0 uncaught, 1 boundary, REAL_APP_CONTENT | the 1 boundary |
| gmdice | canonical_apks/de.duenndns.gmdice_8.apk | View + preferences | INTERACTIVE PROOF holds (5 taps → 5 states, rerun identical) | none observed |
| tictactoe | canonical_apks/com.emmanuelmess.tictactoe_3.apk | libGDX GL + FreeType font | APP-OBSERVED: real font glyphs rasterized, input dispatched, game loop alive | shape-renderer VBO attrib bind; per-frame re-render |
| pf2048 / pfmemory | fdroid_batch / canonical_apks | libGDX/large assets | NO_ROOT (S195 baseline unchanged) | earlier chains |

## Selection per mission §4
- **Target A (best probability of full end-to-end): microtimer.** Cleanest
  cohort profile (0 uncaught / 0 boundary / REAL_APP_CONTENT), View-based,
  core feature (timer start/stop/lap) is a small, objectively testable
  input→state→frame loop. NEXT: define the core-feature acceptance script
  (start→running display→lap→reset) and run the 3-clean-run battery.
- **Target B (different architecture): tictactoe** — the GL/libGDX
  architecture validating the native chain (this wave's work). Its
  remaining board-render gap is the named frontier; microtimer does not
  depend on it.

Interpretation vs facts: the "blocks" column records observed first
divergences only; nothing here is a completion claim.
""")

# ---------- 6. S199_CROSS_SUBSYSTEM_GRAPH.md ----------
(OUT / 'S199_CROSS_SUBSYSTEM_GRAPH.md').write_text(f"""# S199 CROSS-SUBSYSTEM GRAPH — shared chains proven by the wave

Recorded: {DT}. Each row is a producer→consumer pair this wave's evidence
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
""")

# ---------- 7. S199_END_TO_END_BATTERY.md ----------
(OUT / 'S199_END_TO_END_BATTERY.md').write_text(f"""# S199 END-TO-END BATTERY — commands, identities, evidence

Recorded: {DT}. Binary {BIN16} (sha256 {BIN_SHA}).

## Reproduce (each from /home/z/my-project)
```
# tictactoe plain launch probe
python3 scripts/s199_ttt_probe.py
# tictactoe interactive (frames + taps)
python3 scripts/s199_ttt_interactive.py ttt_s199_int_r1 48 250
# cohort battery (microtimer/opencalc/chessclock)
python3 scripts/s199_battery.py
# gmdice 5-tap interactive regression
python3 scripts/autoplay/s121_gmdice_autoplay.py
# goldens + floor gates
python3 scripts/s188_golden_check.py
python3 scripts/s188_w18_floor_rerun.py
```

## Results recorded this wave
| Test | Result | Evidence |
|---|---|---|
| tictactoe launch probe | 0 uncaught, 0 APP BOUNDARY, GL frames presented | evidence/s199/ttt_s199_probe_r1.console.log |
| tictactoe interactive 48f | 54 frames, TOUCH consumed=true, font glyphs in framebuffer | evidence/s199/face_ttt_first_glyphs.png (sha16 fc0997a63f3b2dec) |
| gmdice 5-tap | 5 CHANGED result states, rerun IDENTICAL | autoplay script output |
| cohort microtimer | 0 uncaught / 0 boundary / REAL_APP_CONTENT | evidence/s199/battery/microtimer_s199_r1.console.log |
| cohort opencalc | 0 uncaught / 1 boundary / REAL_APP_CONTENT | battery/opencalc_s199_r1.console.log |
| cohort chessclock | 0 uncaught / 1 boundary / REAL_APP_CONTENT | battery/chessclock_s199_r1.console.log |
| goldens 3/3 | ALL HOLD on {BIN16} | s188_golden_check output |
| floor 11/11 | CLEAN | s188_w18_floor_rerun output |

## Honest status of the two §4 targets
- Target A microtimer: APP-OBSERVED + clean cohort profile. The core
  feature acceptance script (§4.1 A–M) is NOT yet written/run — the
  END-TO-END-VERIFIED claim is NOT made this wave.
- Target B tictactoe: APP-OBSERVED (font chain end-to-end to the
  framebuffer; input dispatched; game loop alive). The board render +
  gameplay completion are NOT yet verified; the named first divergence is
  the shape-renderer VBO attribute bind (attrib0=(nil) draws) and the
  per-frame re-render (static frame after boot frames).
""")

# ---------- 8. S199_REGRESSION_REPORT.md ----------
(OUT / 'S199_REGRESSION_REPORT.md').write_text(f"""# S199 REGRESSION REPORT — before/after on the integration line

Recorded: {DT}. Baseline = S195 binary 31be843614e67bab; After = S199
binary {BIN16} (the S196+S198c port + the W19a family on top).

| Metric | Before (31be…) | After ({BIN16}) | Verdict |
|---|---|---|---|
| tictactoe uncaught / APP BOUNDARY | 1 fatal GdxRuntimeException (AssetManager.load NPE) | 0 / 0 | IMPROVED (execution-depth: death → full boot + GL render) |
| tictactoe frame analysis | REAL_APP_CONTENT ×2 (GL-noise honestly recorded) | REAL_APP_CONTENT with REAL font glyphs (10 colors, black glyph pixels + AA grays) | IMPROVED (noise → real content) |
| gmdice interactive | 5 taps → 5 states | 5 taps → 5 states, rerun IDENTICAL | PRESERVED |
| goldens bouncy/unote/dooz | 3/3 pins | 3/3 pins | PRESERVED |
| floor battery | 11/11 | 11/11 | PRESERVED |
| microtimer | REAL_APP_CONTENT | 0 uncaught / 0 boundary / REAL_APP_CONTENT | PRESERVED (cleanest profile) |
| opencalc / chessclock | REAL_APP_CONTENT | 0 uncaught / 1 boundary each | UNCHANGED-ISH (1 boundary each — not newly introduced by the P0 chain; recorded for the next wave) |
| dooz uncaught baseline | 6 (pinned record) | 6 | PRESERVED (pin = byte-identical face) |
| C8 97/97 marker probe | previously verified on W18 binary | NOT RERUN this wave | PENDING |

New successes: tictactoe AssetManager/I18NBundle/FreeType/atlas/SpriteBatch
chain reaches the framebuffer (the S196 port + W19a family).
Execution-depth improvements are NOT counted as app completion anywhere in
this report (mission §7 law).
""")

# ---------- 9. S199_NEXT_ASSIGNMENTS.md ----------
(OUT / 'S199_NEXT_ASSIGNMENTS.md').write_text(f"""# S199 NEXT ASSIGNMENTS — per coder, evidence-based

Recorded: {DT}. Binary {BIN16}.

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

## Coder 8: rerun the 97/97 marker probe + 3-run determinism on {BIN16}
(the W11/W12 patch stack is untouched but the binary changed). Then the
real-APK async test (§2 C8): any cohort app doing post-launch async UI
work counts.

## Coder 9: the S192 npTc SUPERSEDED state stands; deliver the dedicated
resource-validation APK (§2 C9) exercising npTc/BitmapFactory density/
AssetFileDescriptor — the ARSC label + asset stream chain is now proven
end-to-end, so the validator rides a real pipeline.
""")

# ---------- worklog entry ----------
wl = BASE / 'worklog.md'
entry = f"""
S199 — SHARED EXECUTION CHAIN: S196+S198c PORT, W19a GL IDENTITY FAMILY,
FIRST REAL GLYPHS IN THE TICTACTOE FRAMEBUFFER

Directive: MAIN RUNTIME INTEGRATION CODER S199 (continuation of S195).
P0 executed first (mission §11): the canonical binary advanced
31be843614e67bab → {BIN16} ({head.split()[0] if head else ''}).

PORTED (reconstruct-hash-verify discipline; C3's S196 reconstruction
9ee750b21afe89a0 as the source, adapted where this line superseded):
- F-NEW-580/580b String identity-form normalization at both boundaries
  (bridge_to_api args_raw + alias; S100 String block heap-String read).
- F-NEW-582 family: allocateDirect/newDisposableByteBuffer REAL calloc
  backing + put/get mirrors + put([B)/put(ByteBuffer)/get([B) + copyJni
  5-arg. Registration = the f590 engine hook (ONE registry — C3's
  separate register_direct_buffer() surface intentionally NOT recreated).
- F-NEW-588 heap-String replace family (replaceAll regex law — the
  AssetDescriptor.fileName null root), F-NEW-589 Stack LIFO (the
  AssetManager taskQueue root), F-NEW-587 glGetString GL_EXTENSIONS.
- F-NEW-610 typed-view position(int)/limit(int) setters (from the
  truncated S198c tail; defect #557 6725597246 recorded).
- F-NEW-581 recorded SUPERSEDED (S183/B1 host-native-first covers the
  NOT-EXTRACTED shape).

W19a (S199 additions, each pinned to a first divergence in the run logs):
615 zero-cap direct buffers; 616 typed-view parent-first GL marshal;
616b/616c/616d the one-identity family (two writer surfaces, two mint
forms); 617 the 4-arg element copier (Mesh.setVertices rides it; real
native disasm 0x67f0); 618 the [F raw-bits element law (F-028) in the
GLES marshal.

RESULT (honest, mission §13): tictactoe went from the AssetManager.load
NPE death to 0 uncaught / 0 APP BOUNDARY, 54 GL frames, TOUCH consumed,
async font load complete, and the FIRST REAL APP CONTENT IN THE
FRAMEBUFFER (two FreeType-rendered black arrow glyphs, AA grays —
evidence/s199/face_ttt_first_glyphs.png sha16 fc0997a63f3b2dec). The
board-render gap is named and owned: shape-renderer VBO attribute bind
(attrib0=(nil)) + per-frame re-render. Target A (microtimer) recorded
with the cleanest cohort profile (0/0/REAL_APP_CONTENT); its core-feature
acceptance script is the next P1 gate. END-TO-END-VERIFIED is NOT claimed
for either target this wave.

GATES: goldens 3/3 ALL HOLD, floor 11/11 CLEAN, gmdice 5-tap PRESERVED
(5 states, rerun identical) — all on {BIN16}.

DELIVERABLES: evidence/s199/S199_*.md (9 documents) + this entry.
NEXT: Coder-3 assignment (shape attribs + per-frame re-render) →
tictactoe board render → the §4.1 A–M acceptance scripts for
microtimer + tictactoe → C8 97/97 on {BIN16} → SQLite battery.
"""
with open(wl, 'a') as f:
    f.write(entry)

print("DELIVERABLES WRITTEN:", sorted(p.name for p in OUT.glob('S199_*.md')))
print("worklog lines:", len(wl.read_text().splitlines()))
