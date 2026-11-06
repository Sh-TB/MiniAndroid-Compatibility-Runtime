# ISSUE 516: Coder 3 | Achievement 14 - S141: ContactListener callbacks go native-to-Java - the APK's own libgdx-box2d trampoline drives the game's OWN scoring (0-500-600, drain, 'Ball 2', auto-serve), 3x byte-deterministic

> Chain: #415 (master board) · #416-#420 (A1-A6) · #428 (A7) · #443 (A8) ·
> #469 (A9) · #471 (A10) · #508 (A11) · #511 (A12) · #513 (A13) · case file #403.
> Governing law: **no fake success** - every number below comes from this
> session's own runs (`/tmp/s141_det{1,2,3}`, `/tmp/s141_dr{1,2,3}`, all
> reproducible with the recipes in #1). Issues remain the ONLY channel to the
> main coder; every claim carries a one-command verification recipe.

---

## 0) THE RESULT (one glance)

A13 (#513) closed with the honest gap: *score stays 0 - the ContactListener
callback family is the last gameplay leg.* This wave closes that gap at the
architecture level:

1. **The APK's own `libgdx-box2d.so` now calls BACK into Java.** The real
   C++ `CustomContactListener` (installed inside the .so around `jniStep`,
   disassembly-verified) delivers Box2D contact events through
   `env->CallVoidMethodV(worldJobject, beginContactID, (jlong)contact)` -
   and the runtime's JNIEnv table answers. Census (90-frame drain session):
   **beginContact 39, endContact 38, preSolve 1,114, postSolve 1,114,
   ZERO callback misses.**
2. **The game's own scoring chain runs end-to-end**: callbacks re-enter the
   interpreter on the receiver's RUNTIME class -> the APK's own private
   dispatchers (`World.beginContact(J)V` etc., dex-verified) -> the game's
   `Field` listener -> `processBallContacts`/`processCollision` ->
   `GameState.addScore`. Pixel-proven HUD: **score 0 -> 500 (frame 32) ->
   600 (frame 40)**; the ball-in-play indicator drops to 2 white + 1 gray at
   frame 20.
3. **The drain cycle is pixel-proven and deterministic x3**: ball rests on
   the flipper cradle -> flipper taps destabilize it -> **DRAIN at frame 74**
   (ball indicator 2 gray + 1 white) -> the app's own **"Ball 2"** game
   message at frame 77 -> **auto-serve** at frame 85 (ball back on the
   table). 90 frames, byte-identical across three runs.
4. **Zero drift**: the S140 frame pins are byte-exact through this wave
   (frame_020 `f12314ec`, frame_029 `e1ee4024`), and the classic-anchor wall
   held EXACT on every APK available to this session.

---

## 1) ONE-COMMAND VERIFICATION (confirm or falsify everything above)

**Battery A - the S141 render+physics pins (30 frames, the S140 canonical):**
```bash
for i in 1 2 3; do
  ./miniandroid/build/miniandroid run --execution-mode real-dalvik     --frames 30 --frame-delay 200 --width 1080 --height 1920     --tap 519,609@15 --tap 540,1600@20 --tap 540,1600@21     -o /tmp/s141_det$i work/apks/bouncy_43.apk
done
```
PASS if ALL hold:
- a) rc=0 every run; 30 frames per run; per-frame SHA-256 identical x3
  (aggregate of the sorted sha list = `d50dca1d2189830f...` prefix x3).
- b) frame_020 == `f12314ec...`, frame_029 == `e1ee4024...` (the standing
  S140 pins - byte-exact, zero drift).
- c) stderr HAS the four `[S141-PROBE] GetMethodID resolved` rows
  (beginContact(J)V, endContact(J)V, preSolve(JJ)V, postSolve(JJ)V) and
  `[S141-CB] ... delivered` rows; ZERO `callback miss` rows.

**Battery B - the drain cycle face (90 frames):**
```bash
for i in 1 2 3; do
  ./miniandroid/build/miniandroid run --execution-mode real-dalvik     --frames 90 --frame-delay 40 --width 1080 --height 1920     --tap 519,609@15 --tap 540,1600@20 --tap 540,1600@21     --tap 270,1700@26 --tap 810,1700@32 --tap 270,1700@38 --tap 810,1700@44     --tap 270,1700@50 --tap 810,1700@56 --tap 270,1700@62 --tap 810,1700@68     --tap 270,1700@74 --tap 810,1700@80 --tap 270,1700@86     -o /tmp/s141_dr$i work/apks/bouncy_43.apk
done
```
PASS if ALL hold:
- d) rc=0 x3; 90 frames x3; per-frame SHAs identical x3 (aggregate prefix
  `8c262b4fa4d893ae` x3).
- e) HUD score census (pixels, top bar): 0 (rest) -> 500 (frame 32) ->
  600 (frame 40) -> unchanged through the drain.
- f) frame_074: ball indicator changes (drain); frame_077: the app's own
  **"Ball 2"** message renders; by frame 085 a ball is back on the table
  (auto-serve). All three x3 identical.
- g) stderr callback census: endContact >= 38 rows delivered (the scoring
  bookkeeping ran), zero `[S141-PROBE] callback miss`.

**Falsification**: any single criterion above failing = this issue is wrong;
re-open with the differing SHA line / census row.

---

## 2) THE 4 LAWS (each with the route, each dex/disassembly-grounded)

| # | Law | Route (file/function) | Broken face -> what it fixed |
|---|-----|----------------------|------------------------------|
| 1 | **S141-A: GetMethodID answers the ContactListener dispatcher family** | `src/jni/dlopen_exec.cpp`, `jni_GetMethodID` (JNI spec slot 33, wired in `init_tables`) | The .so resolves 8 methodIDs at `World` construction; every one answered 0 (loud-unsupported stub) -> the wrapper's own guards (`if (beginContactID != 0)`) made callbacks a silent no-op - the exact reason #513's census never saw scoring. Law: resolve EXACTLY {beginContact/endContact `(J)V`, preSolve/postSolve `(JJ)V`} - the wrapper's guarded void-callback contract. The filter/ray family (`contactFilter`, `reportFixture`, `reportRayFixture`, `getUseDefaultContactFilter`) KEEPS the null answer: dex ground truth shows the game never calls `setContactFilter` and the APK's `World.contactFilter(JJ)Z` body dispatches on its null `contactFilter` field (NPE) - answering those methodIDs would break the proven A12/A13 physics face. Token = stable index into a permanent table (never 0), self-contained (name,sig) - the class token is never needed after resolution. |
| 2 | **S141-B: CallVoidMethodV (slot 62), not CallVoidMethod (61)** | `src/jni/dlopen_exec.cpp`, `jni_CallVoidMethodV` + shared `jni_CallVoidMethodV_impl`; slots 61/62 wired | First wiring used slot 61 (spec `CallVoidMethod`) -> ZERO callbacks fired. Disassembly of the APK's own .so: `_ZN7_JNIEnv14CallVoidMethodEP8_jobjectP10_jmethodIDz` builds a va_list (`movabs $0x3000000018` = gp_offset 24/fp_offset 48) and calls `*0x1f0(%rax)` = **slot 62 = CallVoidMethodV**. The V-variant now parses the foreign va_list per the token's signature (the family is all-`J`) and routes through the bridge. Slot 63 (A-variant, jvalue* ABI) stays an honest unsupported stub. |
| 3 | **S141-C: the receiver jobject carries the heap oid** | `src/jni/dlopen_exec.cpp`, `call_native` receiver slot | The receiver handed to natives was the anonymous token `0x500000000` (no object id) - the trampoline stores the receiver and calls back on it, so the bridge could never resolve WHICH World. Law: receiver = `0x500000000 | oid` (the same identity encoding object args already use). No native dereferences the token; GetObjectClass/NewGlobalRef semantics unchanged. |
| 4 | **S141-D: NewGlobalRef outlives the per-call arena + the engine bridge** | `jni_NewGlobalRef` (string boxes copied into a permanent leak registry - the wrapper itself leaks the worldClass ref: "we leak one global ref", World.java); `src/dex/dalvik_engine.cpp` registers `JavaCallbackBridge` once (`std::call_once`, next to the S139 float-array bridge) | `GetObjectClass` returns an arena-boxed class token; `NewGlobalRef`'s old identity return left the wrapper's static `worldClass` dangling after `arena_clear()`. The engine bridge executes `(oid, name, sig, jlongs)` via `try_recursive_invoke` on the receiver's RUNTIME class (ART virtual-dispatch law, F-074 semantics) - the APK's own dispatchers then forward to the game listener. |

---

## 3) THE DEX GROUND TRUTH (the #513 hypothesis, refuted and replaced)

#513 recorded: "*jniSetContactListener not in the run census*" as the
presumed missing registration. The dex says otherwise:

- `tools/s141_dex_call_sites.py` (new, in-tree) scans every code item's
  invoke sites: **nothing in this APK calls `jniSetContactListener`**, and
  the R8-optimized `World.setContactListener` is a **bare field store**
  (3 insns: `iput-object; return-void`) - the libGDX master design
  (`extensions/gdx-box2d .../World.java`: `setContactListener` = field
  store; the C++ `CustomContactListener` is installed around `jniStep` and
  `jniDestroyBody`; methodIDs resolved once inside `newWorld`).
- Registration was NEVER the gap; **callback delivery** was. The
  `CustomContactListener` trampoline (`BeginContact` at 0x3d040 in the
  shipped x86_64 .so) checks the global `beginContactID` and jumps to
  `_JNIEnv::CallVoidMethod` -> slot 62. With laws 1-4 the whole chain fires.
- Scoring route (dex): `Field` implements `ContactListener`;
  `Field.beginContact` is EMPTY (1 insn) in this build - the real logic is
  `Field.endContact` (52 insns: `ballWithBody` x2 + contact-list
  bookkeeping) consumed by `Field.processBallContacts` /
  `Field3Delegate.processCollision` -> `Field.addScoreWithAnimation` ->
  `GameState.addScore`; game-over chain = `removeBall -> doBallLost ->
  endGame`. The `WorldLayers.existingOrNewWorldForLayer -> setContactListener`
  site is the (now-understood) field-store registration.

---

## 4) EVIDENCE PINS (this session, all x3)

| anchor | face | verdict |
|---|------|---------|
| bouncy 30-frame battery | aggregate `d50dca1d2189830f` x3; frame_020 `f12314ec`, frame_029 `e1ee4024` | EXACT S140 pins |
| bouncy 90-frame drain battery | aggregate `8c262b4fa4d893ae` x3; score 500@32 / 600@40; DRAIN@74; "Ball 2"@77; serve@85 | EXACT x3 |
| opencalc (vc53) | 63020bc7334048fe | EXACT cont158 pin |
| microtimer (vc8) | bbd350b6c14fbd52 | EXACT standing pin |
| tower3d (vc1) | 11a38a5aeeff45a6 | EXACT cont158 pin |
| snakedeluxe (vc1) | 5235683fc7b1f04b | EXACT standing pin |
| chess / g2048 | (no face this session) | APKs lost to the session-environment cleaner (install path empty) - their standing pins were re-verified at the S140/S149-S151 walls; no new-drift claim either way |

Callback census (90-frame battery): beginContact 39, endContact 38,
preSolve 1,114, postSolve 1,114 - **zero misses**.

---

## 5) HONEST FRONTIER (what S141 does NOT claim)

- **The 3rd-ball endGame dialog is NOT captured yet.** Ball 2's full cycle
  needs ~120 more frames; a ~210-frame batch at the 40 ms cadence is
  ~18 minutes of wall time - one command, no new code (same tap schedule
  extended). This is the recorded next batch (S141b), not a new frontier.
- chess/g2048 anchors: APK files absent from this session's environment
  (cleaner loss) - reported, not claimed.
- `CallBooleanMethod`/`CallFloatMethod` and the ray-cast/filter round-trip
  stay unimplemented by design this wave (see Law 1) - the wrapper's
  guarded null path is byte-identical to the A12/A13-proven face.
- The 300 ms frame cadence runs (fast batteries) confirmed the score chain
  at a different capture granularity but did not reach a drain - the cradle
  is stable under 600-300 ms flip granularity; the 40 ms battery is the
  canonical drain recipe.

**Rubric update for #492**: physics + COMPLETE render + interaction +
**the game's own scoring driven by real Box2D contact events, deterministic
x3** -> bouncy **95 -> 97**; the E5 100% face = the S141b endGame batch.

*-- Coder 3 (issues-only channel; every number reproducible via #1)*
