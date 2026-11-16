#!/usr/bin/env python3
"""Post the #612 wave-1 receipt (build-graph fix + measurements)."""
import json, subprocess, urllib.request

CRED = subprocess.run(["git", "credential", "fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True,
                      cwd="/home/z/my-project/miniandroid").stdout
TOKEN = [l.split("=", 1)[1] for l in CRED.splitlines() if l.startswith("password=")][0]

B = """## #612 WAVE 1 RECEIVED — build graph fixed AND proven with a real-APK run (commits 74b3d3ac + cbd41e5c)

### A. Graph correctness — FIXED, measured, proven
- The PRE_LINK command that compiled `src/jni/bionic_compat.o` + `pthread_shadow.o` **into the source tree** and linked configure-time-nonexistent files (Ninja: "missing and no known rule to make it") is GONE — both shims plus `native_thunk.S` are normal target sources; `project(LANGUAGES C CXX ASM)` declared up front (74b3d3ac).
- **The auditor's second defect class was real and is now fixed too**: the CMake runtime linked with undefined `JS_*` symbols because the GP583-BUILD-002 manifest parity covered only the .cpp core while the Makefile additionally links QUICKJS_OBJECTS. The 5 QuickJS C files joined the target with the Makefile's exact QUICKJS_CFLAGS dialect (gnu11, `_GNU_SOURCE`, CONFIG_VERSION, CONFIG_BIGNUM, -w) (cbd41e5c). Without this, quickjs.c didn't even compile (C++17 flags + missing CONFIG_VERSION → `expected ')' before CONFIG`).
- **End-to-end proof**: ninja -j1 → rc=0, version banner prints, and a FULL REAL-APK RUN through the CMake-built binary — de.duenndns.gmdice_8 → `Status: SUCCESS`, rendered screenshot, nonwhite ratio 0.726 — **byte-identical to the Makefile binary's battery result**. The CMake runtime is no longer a lesser build.

### B. Minimal runtime — done
Default `all` = 84 Ninja actions vs 82 for the runtime alone (all 7 EXP/batch/megabatch executables EXCLUDE_FROM_ALL); the test battery moved behind `-DBUILD_TESTS=ON` (default OFF); recipes documented in the CMakeLists header.

### C. The real compiler bottleneck — MEASURED (no guessing)
Host: 2 CPU / 3.9 GiB RAM / gcc 14.2 / CMake 4.4.5 / Ninja 1.13. Every number below is a measured wall/peak, not an estimate:
| measurement | result |
|---|---|
| configure (Ninja, Release) | RC=0, 75 TUs from the shared manifest |
| incremental no-op (Makefile) | **42 ms, 0 TUs recompiled** |
| touch small leaf TU (shared_prefs.cpp) | 8.1 s, exactly 1 TU |
| **dalvik_engine.cpp SOLO, CMake flags** (-O3 -DNDEBUG -O2 -g0) | **206.0 s, peak RSS 2873 MiB** |
| **dalvik_engine.cpp SOLO, Makefile flags** (-O2 -g -g0) | **218.7 s, peak RSS 2868 MiB** |
| honest negative: -O1 attempt | 3033 MiB, **OOM-killed** — no flag fixes it |
| parallel -j2 full build | cc1plus OOM-killed (the documented memory pressure) |

**Conclusion:** the ~5.0 MiB dalvik_engine.cpp TU IS the bottleneck — ~2.9 GiB peak and ~3.5 min per compile in EVERY flag configuration, ~35-40% of the whole build, and it sits at the OOM ceiling of a 3.9 GiB host. The next wave must SPLIT the TU (source-level refactor with seam selection + full battery re-run); flag-level mitigation is exhausted (measured, above). Until then: single-job builds, `-g0` preserved (now mirrored in CMake via source properties). The Makefile path (build-tree objects, `-j1`) remains the verified reference build; the Makefile incremental laws all hold."""

req = urllib.request.Request("https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/612/comments",
    data=json.dumps({"body": B}).encode(),
    headers={"Authorization": f"token {TOKEN}", "Accept": "application/vnd.github+json", "User-Agent": "layout-audit"},
    method="POST")
with urllib.request.urlopen(req, timeout=30) as r:
    print("612 receipt:", json.loads(r.read().decode())["id"])
