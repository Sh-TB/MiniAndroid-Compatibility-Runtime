# cont375 CONT-4 — solver ISE CLASSIFIED (runtime root, proven — not presumed) + 4 generic laws; fairymahjong runs to SUCCESS x3; CONT-3 gaps closed

Commit **1c2ccdfd**, final binary rebuilt with the law set. Starting HEAD f3a1268c verified == origin/main.

## STATUS — RESULT — EVIDENCE

**1. PHASE 1 CLASSIFICATION — COMPLETE (the CONT-4 core demand)**
- RESULT: `Lm2;.b pc=1471` ISE "Even face counts always permit a completion" is a **RUNTIME ROOT**, proven by a deterministic diagnostic chain (new env-gated read-only diagnostic `dump_cont4_solver_diag` + full METHOD-TRACE of a throwing run) — NOT an app bug.
- The proof chain (every step observed, none presumed):
  1. The solver's face set is `toSet(take(shuffled(tiles, Random), n))` — `Lt;.r`=shuffled, `Ls;.y`=take, `Ls;.D`=toSet (identified from DEX, R8-merged Kotlin stdlib).
  2. Kotlin `shuffled(rng)` swaps via `list[i] = list.set(j, list[i])` — **ArrayList.set must return the PREVIOUS element** (OpenJDK law). The engine returned VOID → every swap poisoned a slot with an empty string (observed: `[CONT4-SET-EMPTY] … Lt;.r@pc198 ← Lm2;.b@pc138`).
  3. The take/toSet outputs became string-typed (`[0]str"" …` slots) → `contains(Integer)` always missed.
  4. Per-face availability counts initialized to **46 units for a 68-tile board**; the solver drains exactly 1 unit per outer iteration (trace-verified 46→45→…→0), so the game's own parity guard legitimately fired at iteration 47 with 22 tiles unpaired.
- Also attributed: the "different board per run" behavior is the game's own wall-clock-seeded random board roll (16x4 / 17x4 / 72-tile flower variants) — unrelated to the ISE mechanism.
- F-NEW-235 is now **CLOSED-CLASSIFIED** (full proof chain in the registry).

**2. FOUR NEW GENERIC LAWS (source-first, zero app conditions)**
- **F-NEW-239 ROOT-CAUSED-FIXED**: `ArrayList.set(int,E)` returns the previous element, kind-faithful (int/string/object/null); OOB answers null with the divergence documented. Generic: `Collections.shuffle`, Kotlin `shuffled`, sort internals, every swap-via-set idiom.
- **F-NEW-240 ROOT-CAUSED-FIXED**: `BitmapFactory.Options` law — `inJustDecodeBounds=true` fills `outWidth/outHeight/outMimeType` and returns **null without allocating**; `inSampleSize` honored ((dim+s-1)/s nearest); out* filled in full-decode mode too. Pre-fix the game's bounds-first loader threw "Invalid fairy artwork: tiles/07-portrait.png" on a valid 1122x1402 PNG.
- **F-NEW-241 ROOT-CAUSED-FIXED**: `BufferedReader/InputStreamReader.read(char[])` real-character reads over the same wrapper hops readLine uses, **-1 at EOF**. Pre-fix the stub default (0) spun every `while ((n = read(cbuf)) >= 0)` copy loop → F084 forward-progress halt `Ln5;.b pc=0x108` (deterministic x3).
- **F-NEW-242 ROOT-CAUSED-FIXED**: `StringWriter` accumulation law (write/toString/getBuffer; `sb_value` convention). Pre-fix `toString()` answered null → R8 getClass null-check NPE at `Ln5;.b pc=278`.

**3. fairymahjong POST-FIX (general-compatibility proof for the wave)**
- RESULT: **exit=0, Status: SUCCESS, x3 runs, BYTE-IDENTICAL screenshot `76e097244767d6c3`**; the game's own pipeline runs board → solver → artwork → render deeper than any prior wave; full-screen content painted (2073600/2073600 px).
- One residual named face (caught by the app's own handlers, does not affect run completion): `Lr5;.g pc=150` deferred getClass-on-null NPE — registered as the next session's entry point.

**4. CONT-3 NAMED GAPS — CLOSED**
- NATX: the probe APK now packages `libprobe.so` (x86_64 rebuilt byte-exact `d5ec1f57fef3d271`) → **NATX 10/10 ×3 byte-identical (`14672668f77e69ba`)** — the exact gap hypothesized in the CONT-3 ledger ("needs the lib packaged into the probe APK").
- Gate A probe rebuilt WITH the lib → **97 PASS / 0 FAIL / 2 INFO**.
- Skill selftest: probe staged at the documented root path + PORT-1 generalized to accept explicit repo-tool CLI surfaces (`python3 scripts/…` names its own surface) → **13/13**.

**5. REGRESSION — ALL GATES GREEN**
- anchors 5/5 ×3 BYTE-IDENTICAL (opencalc e364b001…, chess b5a7a35d…, dooz d602648e…, microtimer da73010a…, unote 4f1a9e4e…); goldens 5/5 ×3; user goldens 4/4 REAL_APP_CONTENT; gate A 97/0/2; negatives 19/19; reinstall matrix 8/8; multiapp 5/5; loading probe ALL PASS; uninstall proof ALL PASS; skill 13/13; NATX 10/10 ×3.
- Honest note: the full 124-corpus battery is still unavailable in this container (tmp/apks wiped; no runner committed) — the green gates above are the recorded equivalent coverage.
- Registry: 548 roots; reconciliation count synced; validator V1–V7 ALL PASS.

## NEXT (continuing per §0 — do not stop)
- `Lr5;.g pc=150` deferred NPE (the named residual, now the deepest fairymahjong face).
- §6/§7 corpus-derived discovery + the independent new-app acceptance leg.
