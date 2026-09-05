# GITHUB_RESEARCH_INDEX — §26 permanent institutional memory

Law: every repository appears EXACTLY ONCE. Columns per §26. This file is
updated at the END of every campaign session; the per-mechanism detail
lives in the study docs referenced by each row's Evidence cell.

Status vocabulary: REUSED-IMPLEMENTED / REUSED-DISCRIMINATOR / REFERENCE /
REJECTED / UNAVAILABLE / URL_UNVERIFIED / CLOSED.

| Project | Exact URL | Revision | Area | Finding | Reusable | Used | LOC saved | Maintenance saved | Evidence |
|---|---|---|---|---|---|---|---:|---:|---|
| WineDroid | https://github.com/rickbergs/winedroid | a784c0b | DEX parsing/AOT | MUTF-8 + hardened ULEB128 laws; absent-arg determinism; payload-is-data; 20-mechanism catalog | YES (laws + discriminators) | REUSED-IMPLEMENTED + REUSED-DISCRIMINATOR | ≈ −68 (FIND-REUSE-001: 3 copies → 1) + prevented future bug cost | 1 repair point instead of 3; 2 permanent discriminators | docs/research/WINEDROID_DEEP_STUDY.md; tests/mutf8_string_pool_test.cpp; semantic_pass3_bridge_test.cpp (007/011) |
| aapt2 (Android Asset Packaging Tool) | https://dl.google.com/dl/android/maven2/com/android/tools/build/aapt2/8.13.2-14304508/aapt2-8.13.2-14304508-linux.jar (Google Maven, com.android.tools.build:aapt2) | 8.13.2-14304508 (aapt 2.20) | resources.arsc + binary AXML compilation | canonical compiler replaces ANY hand-written binary AXML/ARSC generator; fixed-1980 zip epoch = deterministic fixture APKs; R.java generation | YES (tool reuse, zero MiniAndroid format-writer LOC) | REUSED-IMPLEMENTED (2026-09-05) | ≈ −400 avoided (no generator written); −0 existing | fixtures build REAL APKs; per-fixture resource code = 0 | docs/evidence/GOLDEN_HELLOWORLD.md (§36.E); scripts/build_fixture_apk.sh; tools/aapt2/ |
| D8/r8 | https://github.com/google/r8 (r8.jar) | 8.3.37 | DEX compilation | D8 rejects bare class DIRECTORY input → deterministic classes.jar packaging | YES | REUSED-IMPLEMENTED | 0 | fixture builder robust to `$`-named inner classes | scripts/build_fixture_apk.sh "[3/4] jar entries" |
| ECJ | https://github.com/eclipse-jdt/eclipse.jdt.core (ecj.jar) | 3.x | Java compilation | MIT-licensed javac replacement; -proc:none = deterministic | YES | REUSED-IMPLEMENTED | — | no JDK requirement | scripts/build_fixture_apk.sh |
| AOSP ART | https://android.googlesource.com/platform/art/ | pinned in aosp-runtime-study.md | DEX semantics oracle | instruction/register/wide/invoke/exception semantics extracted as laws, never copied | YES (oracle) | REFERENCE (oracle) | — | semantic battery laws traceable to source | docs/research/aosp-runtime-study.md; docs/research/AGENT_FINDINGS_VALIDATION.md |
| AOSP Framework (frameworks/base) | https://android.googlesource.com/platform/frameworks/base/ | 1cdfff55 | framework behavior oracle | gravity law (EXT-AOSP-001), sp law (EXT-AOSP-002), LinearLayout/TextView semantics pinned by goldens | YES (oracle) | REUSED-DISCRIMINATOR | 0 | golden gates pin AOSP laws | docs/evidence/GOLDEN_HELLOWORLD.md; EXT-AOSP rows |
| AOSP androidfw ResStringPool | (frameworks/base/libs/androidfw ResourceTypes.cpp) | pinned | string pools | ONE pool class for ARSC/AXML/manifest; decodeLength 1-or-2-byte law; offsets-table indexing | YES (law) | REUSED-IMPLEMENTED (FIND-REUSE-004) | −158 net (3 copies → 1) | 1 pool decoder; BLOCKER-006 bug class structurally dead | miniandroid/src/resources/string_pool.{h,cpp}; corpus pixel-identity runs |
| AOSP String.cpp utf16_to_utf8 | (core/jni/String.cpp) | pinned | UTF-16→UTF-8 | surrogate combine law; unpaired → U+FFFD | YES (law) | REUSED-IMPLEMENTED (FIND-REUSE-002) | −94 net (5 copies → 1; 1 buggy) | 1 encoder; manifest double-encoding bug fixed | src/dex/mutf8.cpp; tests/mutf8_string_pool_test.cpp T8-T12 |
| AOSP Native | https://android.googlesource.com/platform/frameworks/native/ | pinned | graphics/binder | concepts only | no | REFERENCE | — | — | docs/research/graphics-rendering-study.md |
| Android Emulator/tools | https://android.googlesource.com/platform/tools/ | pinned | headless testing | headless/determinism concepts | no | REFERENCE | — | — | docs/research/external-mechanism-matrix.md |
| Cuttlefish | https://android.googlesource.com/device/google/cuttlefish/ | pinned | VM test harness | web-RTC/display bridge concepts; NOT architecture | no | REFERENCE | — | — | docs/research/external-mechanism-matrix.md |
| AVF Virtualization | https://android.googlesource.com/platform/packages/modules/Virtualization/ | pinned | VM | isolation concepts | no | REFERENCE | — | — | docs/research/external-mechanism-matrix.md |
| crosvm | https://github.com/google/crosvm | pinned | VM/render bridge | concepts only; MiniAndroid must NOT become a VM | no | REFERENCE | — | — | docs/research/external-mechanism-matrix.md |
| Waydroid | https://github.com/waydroid/waydroid | pinned | container | container contrast; answered study question | no | REFERENCE | — | — | docs/research/external-mechanism-matrix.md |
| VineOS | https://github.com/Hexadecinull/VineOS | pinned | container | contrast only | no | REFERENCE | — | — | docs/research/auxiliary-repo-studies.md |
| Skydnir | https://github.com/ryo100794/skydnir | pinned | userspace runtime | one-canonical-config/diagnostic principle (issue #16) | principle | REFERENCE | — | battery gate = same principle | docs/research/external-mechanism-matrix.md |
| DroidVM | https://github.com/Droid-VM/DroidVM | pinned | VM | what MiniAndroid can AVOID by staying a runtime | no | REFERENCE | — | — | docs/research/external-mechanism-matrix.md |
| JADX | https://github.com/skylot/jadx | pinned | analysis oracle | decompile ≠ execute; hypothesis generator | offline oracle | REFERENCE | — | prevents in-runtime analyzer bloat | docs/research/apk-toolchain-study.md |
| Apktool | https://github.com/iBotPeaches/Apktool | pinned | APK/ARSC/AXML oracle | analysis oracle; aapt2 now covers fixture PRODUCTION | offline oracle | REFERENCE | — | — | docs/research/apk-toolchain-study.md |
| droidsaw | https://github.com/droidsaw/droidsaw | pinned | static analysis | analysis ≠ runtime | no | REFERENCE | — | — | docs/research/auxiliary-repo-studies.md |
| libarsc | https://github.com/auxten/libarsc | pinned | ARSC parser | cross-check reference | diff-oracle | REFERENCE | — | — | docs/research/arsc-resource-study.md |
| ARSCLib | https://github.com/REAndroid/ARSCLib | pinned | ARSC reference | gap table; NOT linked (runtime path stays in-house per charter) | diff-oracle | REFERENCE | — | — | docs/research/MASTER_EXTERNAL_REFERENCE_MATRIX.md |
| Android-RRO | https://github.com/mirzachi/android-rro | a113f0a | runtime resource overlay | RRO proper REJECTED; RRO-0 concept noted | no | REJECTED (partial note) | 0 | avoided wrong architecture | docs/research/auxiliary-repo-studies.md |
| bundletool | https://github.com/google/bundletool | pinned | AAB/packaging | what MiniAndroid must UNDERSTAND, not implement | no | REFERENCE | — | — | docs/research/apk-toolchain-study.md |
| dexterpreter | https://github.com/vimalloc/dexterpreter | b83d151 | DEX interpreter | study row from prior campaign (see doc; prior instruction cycles also cite CalebFention/simplify as "dexterpreter" — both recorded here to avoid URL ambiguity) | no | REFERENCE | — | — | docs/research/auxiliary-repo-studies.md |
| sim-use | https://github.com/SimulaVR/sim-use | — | UI observation | mandated exact URL | — | UNAVAILABLE | — | — | docs/research/auxiliary-repo-studies.md (REPOSITORY_UNAVAILABLE, two consecutive sessions) |
| AndroidRecomp | search pending | — | — | mandate: SEARCH AND VERIFY FIRST | — | URL_UNVERIFIED | — | — | docs/research/auxiliary-repo-studies.md |
| ReSource | search pending | — | — | mandate: SEARCH AND VERIFY FIRST | — | URL_UNVERIFIED | — | — | docs/research/auxiliary-repo-studies.md |
| Reveree | search pending | — | — | mandate: SEARCH AND VERIFY FIRST | — | URL_UNVERIFIED | — | — | docs/research/auxiliary-repo-studies.md |
| Robolectric / Paparazzi / Roborazzi / Shot / Dropshots | github.com (revs in auxiliary-repo-studies.md) | pinned | screenshot testing | comparator concepts; screenshot-testing discipline | concepts | REFERENCE | — | differential-comparator design input | docs/research/auxiliary-repo-studies.md |
| Android-Dex | https://github.com/Shrey113/Android-Dex | c57cbc8 | device runner | physical-device diagnostics contrast | no | REFERENCE | — | — | docs/research/auxiliary-repo-studies.md |
| FreeType / HarfBuzz / FriBidi | github.com/freetype, github.com/harfbuzz, github.com/fribidi | system libs | text pipeline | LINKED as the ONE text path (no second engine allowed) | YES | REUSED-IMPLEMENTED (UNIFIED_007) | — | replaced 8x16 BitmapFont as TextView answer; BitmapFont retirement = open R4 | docs/research/font-runtime-study.md; src/fonts/text_shaper.cpp |
| WineDroid (sohzm) | winedroid.soham.sh (repo private) | — | — | DIFFERENT project from mandated rickbergs/winedroid | — | REJECTED (never substitute) | — | — | docs/research/winedroid-study.md disambiguation |

## Session append — 2026-09-05 (REUSE-FIRST MAXIMUM PROGRESS campaign)

- aapt2 row ADDED (REUSED-IMPLEMENTED): fixture toolchain now
  aapt2 + ECJ + D8; §36.E resource-backed Hello World lands with ZERO
  new binary-format code in MiniAndroid.
- FIND-REUSE-002/003/004 rows for AOSP String.cpp + androidfw
  ResStringPool promoted from "laws on paper" to REUSED-IMPLEMENTED
  with corpus pixel-identity evidence.
- No URL changed, no row deleted: append-only institutional memory.
