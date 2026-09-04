# OPEN SOURCE USED — UNIFIED_008 (adoption evidence, charter §36)

Each adoption: source URL, version, build command, test command, result,
integration point.

---

## 1. ARSCLib V1.4.0 — ARSC ground-truth oracle  [ADOPTED]

- **source**: https://github.com/REAndroid/ARSCLib (release V1.4.0)
- **license**: Apache-2.0
- **download**: `curl -L -o ARSCLib-1.4.0.jar https://github.com/REAndroid/ARSCLib/releases/download/V1.4.0/ARSCLib-1.4.0.jar`
- **build**: none for the jar; our CLI: `javac -cp ARSCLib-1.4.0.jar ArscDump.java` (JDK 21.0.5)
- **run**: `java -cp .:ARSCLib-1.4.0.jar ArscDump <apk>`
- **result**:
  - gmdice: `packages=1, types=8, entries=73` — MiniAndroid `arsc_tool` reports
    `packages=1 type_chunks=14 entry_configs=99 named_ids=73 types=8` with identical
    per-type counts (attr 5, drawable 20, string 19, color 6, id 16, layout 5,
    menu 1, style 1) → **MATCH**
  - dooz: `types=11 entries=249` recorded as oracle baseline
- **integration point**: regression oracle for `src/resources/arsc_parser.cpp`;
  artifacts: `run/u008_oracle/arsclib_gmdice.txt`, `arsclib_dooz.txt`
- **verdict**: MiniAndroid ARSC parser = **AUGMENT** (keep C++ parser for runtime,
  ARSCLib as external ground truth; full write-support NOT needed by runtime)

## 2. Apktool 3.0.3 — second ARSC/AXML oracle  [ADOPTED]

- **source**: https://github.com/iBotPeaches/Apktool (release v3.0.3)
- **license**: Apache-2.0
- **download**: `curl -L -o apktool.jar https://github.com/iBotPeaches/Apktool/releases/download/v3.0.3/apktool_3.0.3.jar`
- **run**: `java -jar apktool.jar d -f -o <outdir> gmdice.apk` → SUCCESS
  (AndroidManifest decoded, res/values/strings.xml, smali/)
- **result**: string VALUES ground truth — `app_name="GM Dice"`,
  `roll_placeholder="Roll it!"`, `log_empty="Push buttons to roll!…"`;
  these are exactly the strings MiniAndroid renders on the golden screen
- **integration point**: oracle only (no runtime dependency)

## 3. androguard 4.1.4 — ARSC value extraction + DEX disassembly  [ADOPTED IN PRODUCTION]

- **source**: https://github.com/androguard/androguard (pip 4.1.4)
- **license**: Apache-2.0 / LGPL-2.1
- **build**: none (pip)
- **run**: `python3 tools/u008_gen_resource_values.py <apk> <out.json>`
- **result**:
  - Telegram: **11,314 strings + 165 colors + 179 dimens + 18 integers**
    extracted from the real 73MB APK's resources.arsc
  - `SentSmsCodeTitle` now resolves to **"Enter code"** on the SMS screen
    (evidence: `run/u008_telegram_v3/stderr.log` RES-INTERCEPT lines)
  - gmdice: 19 strings + 6 colors, byte-equal to apktool ground truth
  - DEX oracle: every root-cause finding in this campaign was confirmed
    against androguard's disassembly before touching the C++ interpreter
- **integration point**: `resource_values.json` consumed by the runtime
  (LocaleController.getString interception) — a REAL runtime data dependency

## 4. SwiftShader — GLES bridge candidate  [INVESTIGATED / BLOCKED by env]

- **source**: https://github.com/google/swiftshader — cloned HEAD **694585a**
- **license**: Apache-2.0
- **build attempt**:
  - `git clone --depth 1` → 14,398 files SUCCESS
  - `cmake -B build -S . -DCMAKE_BUILD_TYPE=Release` → **configure SUCCESS**
    (build files written; cmake 4.4.2 via pip)
  - compile: **BLOCKED** — environment: 2 vCPU, **3 GB RAM**; SwiftShader
    Reactor/LLVM translation units exceed available memory; per-file compile
    also exceeds the session tool timeout
- **integration plan** (for a 16GB+ host):
  1. `cmake --build build --parallel $(nproc)` → libEGL.so, libGLESv2.so
  2. run MiniAndroid GLES test APKs with `EGL_PLATFORM=surfaceless`
     `LIBGL_ALWAYS_SOFTWARE=1`, capturing the framebuffer read-back
  3. MiniAndroid `jni/gles` shim maps GLES calls → the SwiftShader context
- **verdict**: REAL GLES APK stays **BLOCKED** in this environment with a
  precise, tested blocker (not a guess — the configure step ran)

## 5. Temurin JDK 21.0.5 — oracle build host  [AUX TOOL]

- **source**: https://github.com/adoptium/temurin21-binaries
- **license**: GPL-2.0-with-classpath-exception
- **why**: system env has JRE only (no javac); ARSCLib CLI needs javac
- **result**: javac 21.0.5 compiled ArscDump.java cleanly

## 6. git ls-remote — API-free GitHub verification  [ADOPTED for this env]

- **why**: `gh` CLI absent; api.github.com rate limit exhausted (60/h, IP shared)
- **result**: 114/119 catalog entries verified with real HEAD commit hashes
  (git protocol is not rate-limited); 5 entries documented as upstream-elsewhere
- **integration point**: `run/u008_oracle/opensource_catalog.json`
