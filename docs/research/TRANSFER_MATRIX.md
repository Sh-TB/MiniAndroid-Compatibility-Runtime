# TRANSFER_MATRIX — research-to-code, this campaign's §18 table

Campaign: REUSE-FIRST FULL COMPATIBILITY + RESEARCH-TO-CODE
Date: 2026-09-05 · Local HEAD: `9e7c0e9b`

§18 format: no mechanism enters code without provenance. "Implemented"
means compiled into the runtime at the cited commit AND validated by the
cited test at the current HEAD.

| Project | URL | Revision | Mechanism | MiniAndroid target | Reusable? | Implemented? | Evidence |
|---|---|---|---|---|---|---|---|
| WineDroid | github.com/rickbergs/winedroid | a784c0b | MUTF-8 decode (0xC080 NUL, CESU-8 pairs, declared-vs-actual cross-check) | DEX string pool | YES | **YES — commit 2c8bf2da** | tests/mutf8_string_pool_test.cpp 7/7; reproducer pre-fix proved live truncation |
| WineDroid | github.com/rickbergs/winedroid | a784c0b | Hardened ULEB128 (≤5B, final ≤0x0F, bounds) | DEX index/class-data parsing | YES | **YES — commit 2c8bf2da** (single primitive replaces 3 copies) | battery T5 + primitive window |
| WineDroid | github.com/rickbergs/winedroid | a784c0b | payload-is-data switch invariant | instruction scanner law | YES (as test) | **YES — commit 9e7c0e9b** | `sw_packed_payload_is_data_winedroid011` PASS |
| WineDroid | github.com/rickbergs/winedroid | a784c0b | absent-arg determinism at callee boundary | invoke argument marshalling law | YES (as test) | **YES — commit 9e7c0e9b** | `wd_absent_arg_deterministic_winedroid007` PASS |
| WineDroid | github.com/rickbergs/winedroid | a784c0b | per-table bounds/alignment pre-validation | dex_parser table loop | YES | QUEUED (design in WINEDROID_DEEP_STUDY.md) | — |
| WineDroid | github.com/rickbergs/winedroid | a784c0b | inspect diagnostics block + warning accumulation | APK report / BLOCKED reporting | YES | QUEUED | — |
| AOSP frameworks/base | android.googlesource.com/platform/frameworks/base | 1cdfff55 | LinearLayout container-gravity law | layout engine | YES | YES (prior campaign, 738ac50) | helloworld golden centered-children checks |
| AOSP frameworks/base | android.googlesource.com/platform/frameworks/base | 1cdfff55 | setTextSize sp law | TextView metrics | YES | YES (prior campaign, 738ac50) | 28sp→73.5px checks |
| AOSP ART | android.googlesource.com/platform/art | pinned | Dalvik arithmetic/conversion/comparison semantics | dalvik_engine | YES (as law) | YES (battery 96/96) | semantic_long_cmp_conv 14, switch-neg 25, bridge 57 |
| ARSCLib | github.com/REAndroid/ARSCLib | pinned | ARSC edge semantics (NULL-empty, dynamic ref) | arsc_parser fixtures | YES (as fixtures) | QUEUED (2 vectors queued from RRO-006) | — |
| Robolectric+4 screenshot projects | see auxiliary-repo-studies.md | pinned | mismatch triage ladder, failure artifacts, UI-tree sidecar | frames_manifest hardening | YES | QUEUED (10-item ranked recipe) | — |
| JADX / Apktool / droidsaw | github (pinned) | pinned | static analysis → hypothesis generation | findings pipeline | YES (methodology) | process-level | findings in master matrix |
| Waydroid/Cuttlefish/crosvm/AVF | urls above | pinned | headless/determinism/isolation concepts | architecture contrast | concepts only | N/A (no import) | external-repositories.md |
| sim-use | github.com/SimulaVR/sim-use | — | — | — | — | UNAVAILABLE (2 sessions) | REPOSITORY_UNAVAILABLE record |

## Anti-reuse ledger (what we deliberately did NOT import)

| Source | Temptation | Decision | Reason |
|---|---|---|---|
| WineDroid | adopt its AOT C-emission pipeline | REJECTED | different execution model; would fork the architecture |
| dexterpreter | copy its CESK skeleton | REJECTED | no license; 3 opcodes only |
| Android-Dex | adopt its scrcpy capture | REJECTED | lossy + closed source |
| mirzachi/android-rro | implement RRO/OMS semantics | REJECTED (now) | needs PMS/AMS layer MiniAndroid does not have; kept its 2 ARSC test vectors |
| Any source under GPL while we ship Apache/MIT components | verbatim code copy | REJECTED | §32 provenance law: license-incompatible sources are reference-only |

## Reduction this matrix made possible

MUTF-8/ULEB128: 3 implementations → 1 primitive; every future string
fix lands once. Discriminator tests now pin two more external laws, so
future refactors get machine-checked instead of re-derived from source
study each campaign.
