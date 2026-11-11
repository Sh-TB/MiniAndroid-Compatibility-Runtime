# S215 — A-R4 INTEGRATION RECORD (#581, patch sha16-posted `8bdf0881e0d39bcd`)

## Provenance
- Delivery: issue #581 comments c=6787429312 (PART 1/2) + c=6787429768 (PART 2/2),
  posted 2026-11-11T04:56:34Z/36Z, base declared `34927880` (S213 HEAD).
- Supersedes: #577 3-part cumulative transfer (`b7d5372ba5fe8018`, base `6619c34a`)
  — registered S212 but never queued (the queue-discipline gap), made stale by
  `f34a4b12` (R2/R4 landed with own implementations). Cross-link: #577 c=6787436422.

## Integrity findings (honest, per K-2.4)
1. **sha16 mismatch**: the posted parts concatenated (any of 8 assembly variants
   tried) hash `8046eadf3369043c…`, NOT the advertised `8bdf0881e0d39bcd…`.
   The diff is internally self-consistent (16 files, proper hunks), so the
   advertised sha16 is treated as hashed on a pre-final-edit version.
2. **Blob verification on the declared base `34927880`** (authoritative): applied
   → **6/7 modified files reproduce the patch `index` post-image hashes EXACTLY**
   (android_shadows.cpp/.h, dlopen_exec.cpp/.h, worklog.md + fixtures/evidence
   new files as shipped). ONE mismatch: `dalvik_engine.cpp` — patch says
   post-image `4e448918`, pristine-base application yields `cda66364…`.
   ⇒ the posted dalvik_engine.cpp hunks differ from the tree state that produced
   the advertised sha16/index lines (edited after hashing, or the index lines
   are stale). Functionally harmless here (it builds and probes clean — below),
   but the lane should re-post the file's hunks or confirm the diff is what
   they gated. REQUEST recorded in the #581 verdict.
3. **On CURRENT main `56962181` (4 commits past the declared base)**: `git apply
   --check` **CLEAN rc=0** (all 8 dalvik_engine.cpp hunks apply with offsets
   1193–3525 lines — the S214 C7 W5→W11 rebase did not collide).

## Integration proof chain (this container)
| Step | Result |
|---|---|
| apply on `56962181` | CLEAN rc=0 |
| build | green (`make -j1`; `-j2` OOM-kills cc1plus on dalvik_engine.cpp even at the CONT-37 `-g0` rule — host 4 GB resource limit, matches the lane's honest note; binary `c13dfdef7e0e8796`, 115,261,992 B) |
| smoke | `MiniAndroid Runtime v0.1` + `EXP-001: HelloWorld Loader` |
| `make test` | **4 passed / 0 failed** (matches lane claim) |
| `mwr_opcode_probe` (LAWS130 pattern + THUNK_OBJECT; probe_link.mk) | **5/5 PASS** (4294967297.000000 pair-copy / 1.500000 fmod / −1.500000 sign-takes-dividend / 1.500000 negative-divisor / 111 direction-law) — matches lane claim |
| FULL 6-pin gate (`evidence/s215/A_R4_GATE.json`) | **ALL BYTE-EXACT HOLD**: bouncy `8a6c24ac8a7d718e` / unote `3b8dcb0adbbc17a9` / dooz `a0fae9072313e2d1` (281.5 s boot-composition face) / gmdice `3891679dff449331` ×2 rerun-identical / microtimer `b39665f68f3938e6` 0-uncaught / ttt `7354c1b231cd581d` ×3 deterministic — neutrality of R1/R3/R5 + interpreter transfer re-proven on the integrated line |

## APK probe battery (ar_probe 15/15, r1_jni_probe 2/2) — BLOCKED, environment-level
`tools/aapt2`, `tools/d8`, `tools/ecj`, `android-34.jar` are broken symlinks to the
old container's `/tmp/my-project/tools` (never committed; `tools/doctor.sh`
reports apk_tools/dex_tools/resource_tools/java_compiler ABSENT; a Google
repo re-download attempt did not resolve). Fixtures + `scripts/s211_build_probes.sh`
ship IN this patch — battery runs the moment a bootstrap toolchain container
exists. Same protocol as the A-R3 landing.

## What landed
R1 JNI pending-exception channel (ThrowNew/Throw record → engine discards native
return → throw_deferred(JNI-PENDING)) · R3 Random(long)/setSeed per-object
`__random_state__` splitmix64 (unseeded keeps shared lanes EXACTLY) · R5
accessibility arms (isEnabled deliberately ABSENT per the #576 A/B — shipping it
regresses dooz 26-uncaught; contentDescription capture/view_tree export shipped) ·
interpreter transfer: MOVE_WIDE_16 + REM_DOUBLE_2ADDR + MOVE_16 direction law +
probe · R2/R4 hunks DROPPED (already landed by `f34a4b12`).
