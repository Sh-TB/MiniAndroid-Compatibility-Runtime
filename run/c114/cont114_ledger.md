# CONT-114 RESULT — «ادامه فیل و یوز» · F-NEW-462 closed with an honest refinement (CONT-113's ctor-this-binding theory REFUTED by probe; the true law is the GL frame pump's renderer receiver) · java.nio view-buffer family (F-NEW-463) + initializer-ctor execution (F-NEW-464) · tower3d advanced three death-layers · battery green, zero drift · registry 777→780

**Wave:** CONT-114 (elephant batch) · **Base:** origin/main `23948dd8` (CONT-113; container truth re-established: stale snapshot e99c2fbd [registry 566] reset via git fetch — 229 commits were missing; registry 777 + worklog matched remote exactly; fresh rebuild reproduced `9f0fd0f4b9faa016` byte-identical, deterministic-rebuild law re-proven) · **Final binary:** `9b5d38f5742eb99c` (lineage: 9f0fd0f4 → +462 → +463 → +464) · **Registry:** 777 → **780** id-unique (main == mirror) · **Evidence:** `evidence/cont114/evidence.json`

## Lever 1 — F-NEW-462 ROOT-CAUSED-FIXED (fixture-first, honest refinement)

- **V1 probe refutes the old theory:** the CONT-113 "ctor this-binding" hypothesis was tested first (fixtures/c114_f462_probe, real aapt2/ECJ/D8): a Gfx ctor that creates a GLSurfaceView-subclass view then stores its own fields kept ALL fields correct pre-fix (`[C462-SELF] app_null=false cfg_null=false view_null=false lft=77`). Theory REFUTED, honestly.
- **True root (fresh trace):** all 11 `[IGET-MISS-DIAG]` rows on obj#138 (heap class GLSurfaceView20) have `caller=AndroidGraphics.onDrawFrame` — the frame pump `dispatch_gl_surface_view_frame` passed the **VIEW object** as args[0] of `onSurfaceCreated`/`onSurfaceChanged`/`onDrawFrame` while dispatching the **renderer's** class methods. AOSP law (GLSurfaceView.GLThread.guardedRun): the callbacks run ON the renderer installed by setRenderer.
- **Fix:** one line — bind args[0] to the renderer object stored in the view's `glRenderer` field.
- **Bracket:** probe V2 rows pre-fix 0/3 (ctorStamp/seq read 0 on every callback) → post-fix 3/3 (`ctorStamp=777`, `seq=4242`, 6 frames, exit 0→0). Tower3d: obj#138 misses 11 → **0**; setupGL now completes (`Gdx.app` stored at pc=85, past the old pc=29/pc=7 NPEs).

## Lever 2 — F-NEW-463 ROOT-CAUSED-FIXED (java.nio typed view-buffer family + GL state query)

- Next layer: `DefaultTextureBinder.getMaxTextureUnits` NPE'd on `IntBuffer.get` — libGDX `BufferUtils.newIntBuffer` ends at `ByteBuffer.asIntBuffer()`, which had NO handler (REC-MISS) → null view.
- **Fix (OpenJDK law):** `ByteBuffer.as{Int,Short,Long,Float,Double,Char}Buffer` allocate typed views with the same `__bb_*` buffer algebra (cap = remaining()/element_size, `__bb_parent__` identity) and full `get/get(i)/put/position/capacity/remaining/flip/clear/rewind`; `GLES20.glGetIntegerv` writes the queried state into the view object (ES2 spec-minimum table, documented as the software-GL model).
- Tower3d: getMaxTextureUnits progressed past the NPE to the `Gdx.gl` read.

## Lever 3 — F-NEW-464 ROOT-CAUSED-FIXED (initializer defaults execute their ctor)

- Next layer: `Array.add` ARR-LEN-NULL — R-NEW-414 materialized `DirectionalLightsAttribute.lights = new Array` as a BARE shell (F-NEW-274 gates on the ()V ctor's existence, but `materialize_init_default` never RAN it).
- **Fix (ART law completed):** materialize_init_default now executes the `()V` ctor for DEX-defined types (+ same-type re-entrancy guard, framework shells unchanged).

## Honest remaining face — F-NEW-465 CONFIRMED_OPEN_GAP (registered with allocation-site evidence)

The second attribute's lights Array (obj#393) was allocated `frame=0 pc=0 seq=392` — **neither** `execute_new_instance` **nor** `materialize_init_default` — and dispatched `Array.add` with zero field keys. Correlated rows: `[REC-MISS] java/lang/reflect/Array;.newInstance` (libGDX ArrayReflection) + the ClassReflection getConstructor/Constructor.newInstance attribute-copy path. Named lever: pin the (0,0) allocation site + make a DEX-defined `<init>` dispatch miss LOUD (CONT-28 ctor-skip identifiability). No false closure.

## Battery at 9b5d38f5 — zero unadjudicated drift

- f462 probe 3/3 · c448 7/7 · c449 4/4 · **wall 12/12 MATCH byte-identical ×3** (dooz `d602648e` / opencalc `d5f3c7b5` / unote `90a67cc1` / microtimer `bbd350b6`) · goldens 4/4 (helloworld canonical `83720c1028f832d0`) · negatives **19/19** (canonical gate_a probe store regenerated per the CONT-111 remedy; interim 9/19 = documented sequence artifact) · MG-310 7/7 · MG-150 3/3 (F-NEW-408 fence held) · selftest 13/13 · c74esc green.

## Honest pendings (named next)

tower3d's visible face stands at DEFAULT_BACKGROUND_ONLY (`11a38a5a`) — the wave advanced the runtime three death-layers to the draw-op frontier with a healthy AndroidGraphics state for the first time; the pixels themselves remain the frontier. Next: F-NEW-465 allocation-site pinning, F-NEW-449 MessageInfo, chess RecyclerView content layer, virtual-time measurement law (tripeaks/fishrings 5000ms redirect Timer).

(issue #364 CONT-114, elephant batch, fixture-first)
