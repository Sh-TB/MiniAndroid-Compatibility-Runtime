# REFERENCE_PROJECT_MATRIX — canonical reference inventory (§18/§3/§4)

Campaign: REUSE-FIRST FULL COMPATIBILITY + RESEARCH-TO-CODE
Date: 2026-09-05 · Local HEAD: `9e7c0e9b`

This is the campaign-facing index over the reference projects. The full
provenance-detail rows (66 entries, §31 schema with
ID/URL/Revision/License/Subsystem/Mechanism/relevance/gap/adaptation/
files/functions/test/evidence/status) live in
`docs/research/MASTER_EXTERNAL_REFERENCE_MATRIX.md` — that document
remains the single source of row-level truth; THIS file answers, at a
glance: which project, which URL, studied at which revision, and what
the reuse-first campaign concluded.

| Project | Exact URL | Revision studied | License | Role for MiniAndroid | Reuse-first conclusion |
|---|---|---|---|---|---|
| WineDroid | https://github.com/rickbergs/winedroid | a784c0b | Apache-2.0 | P0 sibling (AOT model) | 004/005 IMPLEMENTED (mutf8 primitive), 007/011 pinned as tests; 003/015/016 queued — see WINEDROID_DEEP_STUDY.md |
| AOSP ART | https://android.googlesource.com/platform/art/ | (pinned revs in aosp-runtime-study.md) | Apache-2.0 | semantics oracle | DEX semantics law; all battery discriminators cite ART behavior |
| AOSP Framework | https://android.googlesource.com/platform/frameworks/base/ | 1cdfff55 | Apache-2.0 | framework oracle | EXT-AOSP-001/002 implemented (goldens prove them) |
| AOSP Native | https://android.googlesource.com/platform/frameworks/native/ | pinned | Apache-2.0 | graphics/binder concepts | REFERENCE (graphics-rendering-study.md) |
| Android Emulator / tools | https://android.googlesource.com/platform/tools/ | pinned | Apache-2.0 | headless/determinism concepts | REFERENCE ONLY |
| Cuttlefish | https://android.googlesource.com/device/google/cuttlefish/ | pinned | Apache-2.0 | VM/test harness concepts | concepts only (no VM architecture import) |
| AVF Virtualization | https://android.googlesource.com/platform/packages/modules/Virtualization/ | pinned | Apache-2.0 | isolation concepts | REFERENCE ONLY |
| crosvm | https://github.com/google/crosvm | pinned | BSD-3 | VM/render bridge concepts | REFERENCE ONLY |
| Waydroid | https://github.com/waydroid/waydroid | pinned | GPL-3.0 | container contrast | study question answered in external-repositories.md; no import |
| VineOS | https://github.com/Hexadecinull/VineOS | pinned | per repo | container contrast | REFERENCE ONLY |
| Skydnir | https://github.com/ryo100794/skydnir | pinned | per repo | DEX tooling lead | per master matrix row |
| DroidVM | https://github.com/Droid-VM/DroidVM | pinned | per repo | VM contrast | per master matrix row |
| JADX | https://github.com/skylot/jadx | pinned | GPL-3.0 | analysis oracle | decompile ≠ execute; hypothesis generator only |
| Apktool | https://github.com/iBotPeaches/Apktool | pinned | Apache-2.0 | APK/ARSC/AXML oracle | apk-toolchain-study.md; parser cross-checks |
| droidsaw | https://github.com/droidsaw/droidsaw | pinned | per repo | static analysis reference | analysis ≠ runtime compatibility |
| libarsc | https://github.com/auxten/libarsc | pinned | per repo | ARSC parser reference | arsc-resource-study.md cross-checks |
| ARSCLib | https://github.com/REAndroid/ARSCLib | pinned | Apache-2.0 | ARSC reference + gap table | master matrix (MiniAndroid/ARSCLib/Missing/Different/Reusable) |
| Android-RRO | https://github.com/mirzachi/android-rro | a113f0a | MIT | overlay semantics | RRO proper REJECTED; RRO-006 Res_value edge vectors queued |
| bundletool | https://github.com/google/bundletool | pinned | Apache-2.0 | AAB/build concepts | REFERENCE ONLY |
| dexterpreter (simplify ≠ dexterpreter) | https://github.com/vimalloc/dexterpreter | b83d151 | NONE | DEX interpreter reference | URL VERIFIED via GitHub search + identity; 3 opcodes, no license → REFERENCE ONLY, no import |
| sim-use | https://github.com/SimulaVR/sim-use | — | — | mandated exact URL | **REPOSITORY_UNAVAILABLE** (two consecutive sessions; no substitution) |
| AndroidRecomp / ReSource / Reveree | SEARCH AND VERIFY FIRST (mandate) | — | — | — | **REPOSITORY_URL_UNVERIFIED** — no canonical GitHub URL established by any session to date; never guessed |
| Robolectric / Paparazzi / Roborazzi / Shot / Dropshots | github.com (pinned revs in auxiliary-repo-studies.md) | pinned | Apache-2.0/MIT | screenshot-testing methodology | frames_manifest hardening recipe synthesized (triage ladder, failure artifacts, UI-tree sidecar) |
| Android-Dex | https://github.com/Shrey113/Android-Dex | c57cbc8 | NONE (closed) | device-runner diagnostics | physical-device execution ≠ compatibility proof; concepts only |
| FreeType / HarfBuzz / FriBidi | github.com/freetype, github.com/harfbuzz, github.com/fribidi | system libs | FT GPL-2+exception / MIT | text stack (linked) | already linked; font-runtime-study.md maps the chain |
| WineDroid (sohzm) | winedroid.soham.sh (repo private) | — | GPL-3.0 | DIFFERENT project | kept as separate row; never merged with rickbergs |

## Mandated search obligations status

- URL lock for ALL named projects: DONE except the three
  SEARCH-AND-VERIFY rows above, recorded honestly as
  REPOSITORY_URL_UNVERIFIED (§42 forbids guessed URLs).
- New-project search (20+ keywords over GitHub): performed in the prior
  campaign (external-repositories.md, 24 rows + auxiliary studies);
  no new P0-relevant runtime found beyond the rows above.

## Status counts (this matrix + master rows)

REVIEWED/source-studied: 30+ rows · IMPLEMENTED→VALIDATED: WineDroid
004/005/007/011 + EXT-AOSP-001/002 · REJECTED: RRO proper, scrcpy
capture, license-incompatible imports · UNAVAILABLE: sim-use ·
URL_UNVERIFIED: AndroidRecomp, ReSource, Reveree.
