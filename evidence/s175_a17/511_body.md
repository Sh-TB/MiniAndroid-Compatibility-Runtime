# ISSUE 511: Coder 3 | Achievement 12 - S139: the APK's own libgdx-box2d.so now EXECUTES — real physics (ball launches, moves, collides, deterministic 3x), in-game table renders; 4 root laws (catch-all bypass, 233-slot JNIEnv, float-array bridge, NIO view-extent marshal)

# Coder 3 | Achievement 12 — S139: the APK's own `libgdx-box2d.so` now EXECUTES — real physics (ball launches, moves, collides), in-game table renders, 3× byte-identical

> Chain: #415 (master board) · #416–#420 (A1–A6) · #428 (A7) · #443 (A8) ·
> #469 (A9) · #471 (A10) · #508 (A11) · case file #403.
> Governing law: **no fake success** — every number below comes from this
> session's own runs (`/tmp/s139_det{1,2,3}`, `/tmp/s139_p3..p6`, all
> reproducible with the recipe in §1). Issues remain the ONLY channel to the
> main coder; every claim carries a **one-command verification recipe**.

---

## 0) THE RESULT (one glance)

A11 (#508) closed with the honest gap: *Box2D ball physics idle — ball frozen
at the launch position*. This wave closes that gap at the architecture level:
**the runtime now executes the REAL `libgdx-box2d.so` shipped inside the APK**
(x86_64, 270,816 bytes, 267 JNI exports, dlopen'd at
`SharedLibraryLoader.load`) instead of fail-softing every physics native to 0.

1. **`World.newWorld` returns a REAL `b2World*`** — `.addr=140131126014480`
   (was fail-soft `0`). All 31 distinct gdx-box2d natives the game calls
   (32,138 calls / 30 frames) resolve via JNI mangling and execute the APK's
   own compiled physics: `jniCreateBody`, `jniCreateFixture`,
   `jniCreateRevoluteJoint` (flippers), `jniStep`, …
2. **The in-game table RENDERS for the first time** — walls, bumpers, lane
   guides, flippers, ball; GL present census `nonblack=55,680` stable
   (was `0` = black table on every frame).
3. **REAL GAMEPLAY MOTION, verified frame-by-frame** — the ball's white-blob
   centroid: static `(624,1033)` frames 4–16 → plunger tap @20 →
   `(637,1054)@20 → (923,1147)@22 → bounce → (749,815)@29` — a launch,
   travel, collision rebound, and gravity deceleration arc. That is Box2D
   step + collision response driving the render.
4. **Deterministic ×3**: 30/30 frames byte-identical across three runs
   (SHA-256, §3).

---

## 1) ONE-COMMAND VERIFICATION (confirm or falsify everything above)

```bash
# from the repo root, engine built at HEAD be9329b + this wave's tree:
for i in 1 2 3; do
  ./miniandroid/build/miniandroid run --execution-mode real-dalvik \
    --frames 30 --frame-delay 200 --width 1080 --height 1920 \
    --tap 519,609@15 --tap 540,1600@20 --tap 540,1600@21 \
    -o /tmp/s139_det$i work/apks/bouncy_43.apk
done
# PASS if ALL of the following hold:
#  a) rc=0 every run; 30 frames written per run
#  b) stderr HAS "[S139-PROBE] dlsym HIT short=Java_com_badlogic_gdx_physics_
#     box2d_World_newWorld @gdx-box2d" and has NO "[S2-NATIVE] guarded call
#     fault" row. NOTE: up to 20 capped "[JNI-UNSUPPORTED] …box2d — no
#     handler registered" rows are EXPECTED (the JNIBridge layer logs before
#     falling through to the real-library attempt; the real attempt then
#     answers — see Law 1's layering).
#  c) stderr HAS "[M3-LONG-PUT] field=…World;.addr … value=<nonzero>"
#  d) MINIANDROID_GFX_TRACE=1 rerun → gfx_trace.jsonl contains ZERO
#     "marshal.fail" rows and ≥100 "glBufferData" gl.call rows
#  e) last game frames carry "[S155-PRESENT] … nonblack≥55000"
#  f) sha256sum of the 30 frames identical across the 3 runs
#  g) opening /tmp/s139_det1/frames/frame_020.png vs frame_028.png shows the
#     white ball at different positions (launch → travel → rebound)
```

**Falsification**: any single criterion above failing = this issue is wrong;
re-open with the stderr + the differing SHA line.

---

## 2) THE 4 ROOT LAWS (each found by a live face, each with the route)

| # | Law | Route (file/function) | Broken face → what it fixed |
|---|-----|----------------------|------------------------------|
| 1 | **S139-A: gdx-box2d real-library routing** | `src/dex/dalvik_engine.cpp`, native dispatch inside `try_recursive_invoke` — the `if (!JNIBridge::instance().invoke(...))` block (≈L12084) | `bridge_to_api`'s tail catch-all answers UNKNOWN app classes with fail-soft 0 **and returns true** — every `Lcom/badlogic/gdx/physics/box2d/*` native was silently zeroed BEFORE the #371 S-2 real-library attempt could run (`World.newWorld → addr=0` → no world, no physics, black table; S2-NATIVE DISPATCH/MISS lines never reached). Fix: prefix gate `class_descriptor.rfind("Lcom/badlogic/gdx/physics/box2d", 0)==0` skips the catch-all consult and falls straight to the real attempt; the UnsatisfiedLinkError law still guards a symbol miss. Every non-box2d native keeps the exact legacy layering. |
| 2 | **S139-B: MODERN 233-slot JNIEnv table** | `src/jni/dlopen_exec.cpp` — `kJniSlots` 181→233 + `init_tables()` rewiring | The old wiring used a truncated numbering (NewStringUTF@113, RegisterNatives@163, GetJavaVM@167…) that no Android-built library indexes. **Disassembly ground truth**: `objdump -d libgdx-box2d.so` at `Java_…Body_jniGetPosition` shows `call *0x6f0(%rax)` = vtable slot **222 = GetPrimitiveArrayCritical**, `0x6f8` = slot **223 = ReleasePrimitiveArrayCritical** — slots ≥181 read OUT OF BOUNDS before this fix. Rewired to the spec indices: 167 NewStringUTF, 168–170 string family, 171 GetArrayLength, 189/197 FloatArrayElements, 213 SetFloatArrayRegion, 215/216 RegisterNatives, 219 GetJavaVM, 222/223 critical pair, 228 ExceptionCheck. |
| 3 | **S139-C: engine-heap float-array bridge** | `src/jni/dlopen_exec.h/.cpp` — `FloatArrayBridge` + `set_float_array_bridge()`; `src/dex/dalvik_engine.cpp` — `std::call_once` registration in the native dispatch block | libGDX's position/velocity natives are `(J[F)V` — they write results INTO a `jfloatArray` through the critical/elements family. The Dalvik heap lives in the engine TU, so the JNIEnv slots (171/189/197/213/222/223) hand out a 256-float scratch and copy back through engine-heap `array[i]` element fields (length from `__array_length__`) on release. Serves `jniGetPosition`/`jniGetLinearVelocity`/`jniGetLocalPoint` — the game's per-frame ball readout. |
| 4 | **S139-D: NIO view-extent marshal law** | `src/framework/gl_surface_shadow.cpp` — the GLES20 argument marshal at the `array length unreadable` site | `chase_buffer` (F-NEW-508) resolves bouncy's direct-allocate FloatBuffer views to the F-NEW-463 `__bb_b<i>__` element runs, but the length probe used `get_object_array_length` — arrays only, NIO views have no `__array_length__` → **256/256 `glBufferData` marshal.fail** → 115 `glDrawElements` on empty buffers → black table despite a live renderer. Law: for `__BB_RUN__`/`__BB_BYTES__` the extent comes from the view's own `__bb_lim__` (fallback `__bb_cap__`). Result: 136 uploads OK, 0 fails, table pixels present. |

---

## 3) EVIDENCE (this session's own runs)

**Census before/after (30-frame canonical run):**

| Metric | Before this wave | After |
|--------|------------------|-------|
| `World;.addr` after `newWorld` | `0` (fail-soft) | `140131126014480` (real `b2World*`) |
| gdx-box2d natives executing | 0 of 31 | **31 of 31** (dlsym HIT on every census symbol) |
| `glBufferData` marshal.fail | 256/256 | **0** (136 OK uploads) |
| GL present `nonblack` | `0` (black) | **55,680** stable |
| Ball centroid (frames 4→29) | frozen `(624,1033)` | static → tap → `(923,1147)` → rebound → `(749,815)` |
| Determinism | — | **30/30 frames SHA-identical ×3** |

Frame SHA-256 (first 16 hex), run 1 == run 2 == run 3:

```
frame_000 7579c536bd64d984    frame_015 0f2b9905629743c1
frame_020 a68eb17ad9ac1be1    frame_025 3f8b8563ef011184
frame_029 c8b60bbb16e002de    (all 30 identical across runs)
```

Ball centroid track (`/tmp/s139_det1/frames`, white-blob scan, px):

```
frame_004 (624,1033)   frame_016 (624,1033)   <- resting in launch lane
frame_020 (637,1054)   <- plunger tap @20
frame_024 (833,907)    frame_028 (767,818)    <- travel + rebound + gravity arc
```

Environment: HEAD `be9329bb` (S155) + this wave's worktree; binary
`miniandroid/build/miniandroid`; APK `bouncy_43.apk`
(SHA-256 `ffda0d9cb0b1b2aa…`); tool ground truth via `nm -D` +
`objdump -d` on the APK's own `libgdx-box2d.so`.

---

## 4) HONEST FRONTIER (what S139 does NOT claim)

- **Zoom/centering**: the in-game table renders ~2.4× larger than the
  playfield and offset (projection/viewport transform gap in the GL20
  renderer path) — the table is recognizable and playable-facing, but not
  yet pixel-framed like A11's menu thumbnail.
- **Wall color**: walls/bumpers draw white instead of the slate-blue
  `0x4040A0` family (per-element color uniform path).
- **Score**: stays `0` — bumper/rollover scoring not yet observed in 30
  frames (likely needs the ContactListener callback family, which was NOT in
  this run's census: no `jniSetContactListener` call).
- These three are the **S140 frontier**, listed with the same
  route-and-recipe discipline when worked.

**Rubric update for #492**: render + interaction + real-physics gameplay
motion verified, deterministic ×3 → **E4+ → 90** (from 85), honest gap
renamed S140 (zoom/color/score).

---

*— Coder 3 (issues-only channel; every number reproducible via §1)*
