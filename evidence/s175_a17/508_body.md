# ISSUE 508: Coder 3 | Achievement 11 - S138: Vector Pinball's game STARTS and the full table renders on EVERY present (33/33 consistent, 116,550 px, 52,588 wall px), 3x byte-identical; the doDraw F084 halt is gone (wait-yield law)

# Coder 3 | Achievement 11 — S138: the game starts, every present carries the full table

> Chain: #415 (master board) · #416–#420 (A1–A6) · #428 (A7) · #443 (A8) ·
> #469 (A9) · #471 (A10) · case files #21/#403.
> Governing law: **no fake success** — every number below comes from this
> session's own runs (`work/run/s138_det/d30_{1,2,3}`, `s138_det/full90`).
> User directive: *make the page load COMPLETE — not incomplete, not
> half-complete — COMPLETE.* Issues remain the ONLY channel to the main
> coder; every claim carries a **one-command verification recipe**.

---

## 0) THE RESULT (one glance)

The sandbox was recycled: the S154 engine tree existed only as the published
Issues. This wave **re-derived the entire S136+S137+S154 stack at the current
HEAD `7bbf087a`** (the post-slim + AWAIT-UP commit), then pushed through
**8 new laws** that the re-derive exposed. Result at HEAD + the recipe below:

1. **The full Vector Pinball table renders on EVERY present** — 33/33 GL
   presents carry `nonblack=116550 bluish=52588` (walls/bumpers/ball/flippers/
   launch lane in 7 distinct colors). The S154 flip-flop face
   (`112723 → 8 → 9710`, #471 §4) is **CLOSED**: per-present consistency is
   the natural state of the corrected stack, no pump rework needed.
2. **The game STARTS**: the Start-Game tap runs `doStartGame` through its
   `isPaused()` gate (unpause chain: F-NEW-515 window focus →
   `onWindowFocusChanged(true)` → `unpauseGame()` → `GameState.setPaused(false)`)
   and **18 × `isGameInProgress ret=TRUE`** land in the 30-frame run
   (79 × in the 90-frame run).
3. **The `GL20Renderer.doDraw` F084 halt is GONE**: 50001-visit wait-loop
   spins → **0 HALT rows** (the S138 monitor-wait yield law, §2 law 7).
4. Determinism holds: **3 runs × 30 frames, byte-identical final frame**
   (`90e7816cfee16cf5` ×3), 0 draw-guard refusals.

**Verification recipe (main coder, two commands):**

```bash
# (a) canonical battery (30 frames, Start-Game taps):
./miniandroid/build/miniandroid run --execution-mode real-dalvik \
  --frames 30 --frame-delay 200 --width 1080 --height 1920 \
  --tap 519,609@15 --tap 540,1600@20 --tap 540,1600@21 \
  -o /tmp/s138_check work/apks/bouncy_43.apk
# (b) 90-frame full session:
./miniandroid/build/miniandroid run --execution-mode real-dalvik \
  --frames 90 --frame-delay 200 --width 1080 --height 1920 \
  --tap 519,609@15 --tap 540,1600@30 --tap 540,1600@31 --tap 540,1600@45 \
  -o /tmp/s138_90 work/apks/bouncy_43.apk
```

**Confirm** = `frame_029.png` SHA256 starts `90e7816cfee16cf5` ×3 runs AND
`grep -c "isGameInProgress.*ret=TRUE"` ≥ 18 AND the `[S155-PRESENT]` rows
show `nonblack=116550 bluish=52588` on every post-GL present AND
`grep -c HALT-LOOP` = 0.
**Reject** = the SHA differs across runs, any present drops below 100,000
non-black, or the registered-shader lines
(`[GLES20-BRIDGE] registered C shader program: engine=1 pgl=1 kind=circle`
+ `engine=2 kind=line`) disappear → a regression; re-open with the stderr.

---

## 1) THE RE-APPLIED STACK (verified law-by-law against #443/#469/#471)

Every A8+A9+A10 law re-implemented at HEAD and re-verified live: F-243c/d/e,
F-NEW-507 (bouncy line/circle shaders as C programs — both register), the
GLES-constant translations (probe-verified against the shipped portablegl.h,
`scripts/pglconsts3.c`), F-NEW-508/509 (buffer-view chase + string content),
F-NEW-510..513 (bulk put, allocate capacity, base-declaration, view limit),
F-NEW-514 (Matrix: frustumM/orthoM/setLookAtM/multiplyMM/multiplyMV/
setIdentityM/translateM/scaleM — GL-spec column-major definitions),
F-NEW-515 (window focus: both resume paths + `hasWindowFocus()` shadow law),
S137/S154 draw-guards, store keying, offset-0-by-kind, elem-size,
index-VALUE law, GLSurfaceView ancestry gate + laid_out gate, nativeOrder.
Measured re-apply ground truth: `[PARSE]` rows **3757 = the S154 d30_1 count
exactly**; the F089 map-put key sequence
`delegate → ballcolor → ballradius → elements → … → launchPosition` matches.

## 2) THE 8 NEW LAWS (each found by a live face, each with the route)

| # | Law | Route (file/function) | Broken face → what it fixed |
|---|-----|----------------------|------------------------------|
| 1 | **F-243a law-wide string identity** (re-apply completion) | `dex/dalvik_engine.cpp` F-243 block entry | My first re-apply missed it: `JSONObject(String)` args ride heap String objects; the STRING_REF-only `<init>` gate parsed `{}` → all 9 tables empty → `launchPosition` EMPTY_LIST → `Field.zoomCenterPoint` IndexOutOfBounds every tick. Fix: block-scope shadow unwraps EVERY heap-String arg to `__string_value__` once at the law boundary. Measured: full key sequence returns, PARSE rows 1→3757. |
| 2 | **F-243b no-arg length** (re-apply completion) | `dalvik_engine.cpp` JSONArray law | `length()` sat inside the indexed `args>=2` gate — never fired → every JSONArray→List empty → `Color.fromList` `IllegalArgumentException "Invalid color size: 0"` at APP BOUNDARY (onCreate died). Fix: dedicated no-arg arm. |
| 3 | **S155 ELEMENT-KIND** | `dalvik_engine.cpp` bulk-put | `IntBuffer.put(int[])` stored IEEE float bits — indices `0,1,2` crossed as `0.0f/1.0f/2.0f` bits (the `[S155-DRAW]` dump shows the exact bytes) → the index-VALUE guard read garbage → every wall draw refused. Fix: element kind by view type (Int/Short/Char/Long = raw; Float/Double = IEEE bits). |
| 4 | **S155 PGL OFFSET-SEMANTICS** | `gles/gles20_bridge.cpp` glVertexAttribPointer/glDrawElements | PortableGL (compatibility profile, `get_v_attrib`) expects the pointer arg to be the BYTE OFFSET against its own buffer copies when a buffer is bound — passing a real data pointer made PGL add a wild address to its internal store → SIGSEGV in `run_pipeline` (rc=139). Fix: `(const void*)(uintptr_t)off` for bound buffers; PGL owns the data (copied at glBufferData). |
| 5 | **S155 CLIENT-ARRAY LIFETIME** | `gles20_bridge.{h,cpp}` AttribBind + `framework/gl_surface_shadow.cpp` GlMarshal.plen | Client attrib pointers rode marshal holds that die with the call. Fix: the bridge copies client arrays at pointer time (bounded 1 MiB); the dispatch signature carries per-pointer byte lengths (`plens`); draws re-issue from the copy. |
| 6 | **S155 EXACT-FIT GUARD BOUND** | `gles20_bridge.cpp` draw-guard | `need=(max_idx+1)*stride+vsize` over-counted one stride: exact-fit wall meshes refused (`32*32+12=1036 > 1024` while the true bound is `31*32+12=1004 ≤ 1024`). Fix: `need = offset + max_idx*stride + vsize` (GL §2.8 exact fit). Measured: draw-guard refusals → 0. |
| 7 | **S138 MONITOR-WAIT YIELD** | `dalvik_engine.cpp` `Object.wait/notify/notifyAll` law | The app's render contract `doDraw → requestRender → while(!renderDone) renderLock.wait()` (FieldDriver game thread) spun 50001 visits → F084 halt every tick (the #469 honest gap 1). Fix: `wait()` parks the drained body via the F-110b sleep-yield mechanism; the frame pump's `onDrawFrame` lands `renderDone=true` + `notifyAll` between boundaries; the app's while-loop re-checks under Java's spurious-wakeup semantics. Measured: `[WAIT-YIELD]` rows, HALT-LOOP **0**. |
| 8 | **S138 NumberFormat family** | `dalvik_engine.cpp` Ljava/text/NumberFormat law | `ScoreView.formatScore` → `NumberFormat.getInstance()` null → NPE every draw + the tail APP-BOUNDARY unwind. Fix: getInstance family + `format(long)` thousands grouping + `format(double)` maxFractionDigits=3 (OpenJDK defaults). |

Diagnostics (all bounded): `[GLES20] <method> ni/np` first-two-calls census,
`[S155-PRESENT]` per-present census (nonblack/bluish at the real blit site),
`[S155-DRAW]` index-store dump, `[S155-PUMP]` gate census, `[WAIT-YIELD]`,
`[NOTIFY]`.

## 3) MEASURED STATE (this session's own artifacts)

**Canonical determinism battery** (30 frames, taps `519,609@15` + `540,1600@20/21`):

| Run | rc | Final-frame SHA256 (first 16) | isGameInProgress TRUE | Presents |
|-----|----|------------------------------|----------------------|----------|
| d30_1 | 1 | `90e7816cfee16cf5` | 18 | 33×(116550/52588) + 1 pre-GL |
| d30_2 | 1 | `90e7816cfee16cf5` | 18 | identical |
| d30_3 | 1 | `90e7816cfee16cf5` | 18 | identical |

90-frame full session: **79 × `isGameInProgress ret=TRUE`**, 94 presents
(93 consistent + the first pre-GL), 7 element colors present
(walls `0,0,255` ×52,588 · ball/flippers/launch-lane white ×32,234 ·
bumpers magenta ×15,700 · cyan ×9,474 · green ×3,023 · red ×2,349 ·
yellow ×1,175).

## 4) HONEST REMAINING GAP (registered, not hidden)

**The libGDX-Box2D native family is unimplemented** → ball physics idle.
`World/Body/Fixture` JNI addresses stay 0 → `Fixture.getShape` throws
`GdxRuntimeException` (the app's own `addr==0` guard) → caught by
`onDrawFrame`'s catch-all → deferred APP-BOUNDARY unwind at
`BouncyActivity.onCreate invoke_pc=632` (the #469 gap-3 shape) → rc=1 /
PARTIAL status. The table, the game state machine, the taps, the score bar
and the per-present rendering are real and deterministic; the ball renders
at its launch position because `World.step` has no engine counterpart yet.
**The S139 frontier**: the Box2D JNI family (world/body/fixture address
minting + `World.step` integration + contact callbacks → bumper scores →
launch → game over).

**Reject criteria for this achievement:** the §0 recipe's Confirm set fails
on any clause. Re-open with the stderr.

> Coder 3 — the game starts and every present carries the full table.
> Verification recipes above; reject with stderr if any face regresses.
