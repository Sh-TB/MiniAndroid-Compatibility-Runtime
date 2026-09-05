# MASTER EXTERNAL REFERENCE MATRIX (§31)

Single master matrix per campaign law §31. Consolidates every external
mechanism row: the research-campaign catalog (external-mechanism-matrix.md,
which remains the provenance-detail annex), this execution campaign's
implementation rows, and the auxiliary-repo studies
(auxiliary-repo-studies.md).

Status vocabulary (§31, fixed): NOT_REVIEWED · REVIEWED · LEAD · ADAPTABLE
· IMPLEMENTED · VALIDATED · VERIFIED · REJECTED · UNAVAILABLE ·
URL_UNVERIFIED. This campaign's additions: IMPLEMENTED = code landed +
focused test; VALIDATED = runtime evidence at current HEAD.

Row schema (§31): ID | Project | Exact GitHub URL | Revision/Commit |
License | Subsystem | Mechanism | MiniAndroid relevance | Current
MiniAndroid implementation | Gap | Potential adaptation | Files |
Functions | Test required | Evidence | Status | GitHub Comment URL.
(GitHub Comment URLs: none exist — push is BLOCKED, see final report
§PUSH; the column is carried as `—` until a remote exists. Commit SHAs
are the persistent record meanwhile.)

## A. IMPLEMENTED / VALIDATED this campaign (execution push)

| ID | Project | Exact URL | Revision | License | Subsystem | Mechanism | MiniAndroid relevance | Current implementation | Gap | Adaptation | Files | Functions | Test | Evidence | Status | GH Comment |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| EXT-AOSP-001 | AOSP frameworks/base | https://android.googlesource.com/platform/frameworks/base/ | 1cdfff55 | Apache-2.0 | UI layout | LinearLayout.setGravity → mGravity governs children with no layout_gravity (`lp.gravity < 0 ? mGravity : lp.gravity`, L1284/L1466; setter L1933-1945; cross axis L1777-1778) | programmatic container setGravity was routed to text_gravity — children never moved | class-aware bridge_to_api dispatch (containers → container_gravity+gravity_set) + child-gravity fallback in inflater layout pass AND legacy render walk | none for this law | direct port of the fallback law | src/dex/dalvik_engine.cpp; src/resources/layout_inflater.cpp; src/runtime/execution_engine.cpp; src/framework/android_shadows.h | bridge_to_api; LayoutInflater::measure_layout; stage_render_frame | helloworld_golden checks [2][3] | children centered: x=(1080−w)/2 exactly (195/253/513); tictactoe frames byte-identical; simplestopwatch BASELINE_MATCH | **VALIDATED** | — |
| EXT-AOSP-002 | AOSP frameworks/base | https://android.googlesource.com/platform/frameworks/base/ | 1cdfff55 | Apache-2.0 | TextView | TextView.setTextSize(float) == setTextSize(COMPLEX_UNIT_SP, size) (L4720-4722); TypedValue.applyDimension → px=sp×scaledDensity (L4752-4762) | programmatic setTextSize only traced — stored nowhere; all views rendered at default size | engine intercept converts sp×2.625 → ViewNode.text_size_px (+text_size_sp evidence); handles (float) and (int unit,float) shapes + raw-bit defensive recovery | PX-unit path tested only via code path, no dedicated fixture yet | direct port | src/dex/dalvik_engine.cpp; src/framework/android_shadows.h | bridge_to_api; ViewShadow::set_text_size_px | helloworld_golden check [2] 28sp→73.5px/14sp→36.75px + pixel band test | render log EXT-AOSP-002 lines; headline band 2× subtitle band | **VALIDATED** | — |
| EXT-EXEC-001 | MiniAndroid fixture | (this repo) miniandroid/tests/fixtures/helloworld_golden | 738ac50 | MIT | §27/§28 boot/render golden | real ECJ+D8 APK: load→manifest→Activity→DEX→View tree→measure→layout→fonts→Canvas→render→PNG, deterministic | permanent simplest boot/render regression | validate_helloworld_golden.sh 18 checks + docs/evidence/helloworld_golden/EVIDENCE.md | resources.arsc chain lives in corpus goldens (gmdice), not here | n/a | fixture src/ + validator | MainActivity.onCreate | 18-check script, zero-skip gate | APK 584cda57… DEX 70298937… shot 93b42621… 1080×1920 byte-identical ×2 | **VERIFIED** | — |

## B. WineDroid — rickbergs/winedroid (Apache-2.0) — studied, transfer queue

| ID | URL | Revision | License | Mechanism | MiniAndroid relevance | Test required | Evidence | Status |
|---|---|---|---|---|---|---|---|---|
| WINEDROID-001 | https://github.com/rickbergs/winedroid | a784c0b | Apache-2.0 | typed APK entry classification + unsafe-path warnings + caps | apk loader diagnostics | inspect fixture | winedroid-study.md (file+fn citations) | ADAPTABLE |
| WINEDROID-002 | same | a784c0b | Apache-2.0 | defensive DEX header validation | dex load | corrupt-header unit | winedroid-study.md | ADAPTABLE |
| WINEDROID-003 | same | a784c0b | Apache-2.0 | per-table bounds+alignment pre-validation, named errors | dex load | corrupt-DEX fixture | winedroid-study.md | ADAPTABLE |
| WINEDROID-004 | same | a784c0b | Apache-2.0 | MUTF-8 declared-vs-actual utf16 cross-check (NUL 0xC080, surrogates) | dex string pool | Q-1 unit vectors | winedroid-study.md | ADAPTABLE |
| WINEDROID-005 | same | a784c0b | Apache-2.0 | ULEB128 5-byte/32-bit hardening | dex parser | u32-ULEB vector | winedroid-study.md | ADAPTABLE |
| WINEDROID-006 | same | a784c0b | Apache-2.0 | numeric multi-dex ordering law | multi-dex resolution | Q-2 ordering vector | winedroid-study.md | ADAPTABLE |
| WINEDROID-007 | same | a784c0b | Apache-2.0 | generic invoke ABI: incoming_start = regs−ins, zero-fill | invoke paths | Q-3 zero-fill discriminator | winedroid-study.md | ADAPTABLE |
| WINEDROID-009 | same | a784c0b | Apache-2.0 | recursive linker per-method rejection REASONS (pc+opcode) | diagnostics | Q-12 report artifact | winedroid-study.md | ADAPTABLE |
| WINEDROID-011 | same | a784c0b | Apache-2.0 | packed-switch payload-is-data invariant | interpreter scanner | Q-4 payload fixture | winedroid-study.md | ADAPTABLE |
| WINEDROID-013 | same | a784c0b | Apache-2.0 | INT32_MIN/-1 div-rem corner semantics | interpreter arith | semantic battery re-run | semantic_long_cmp_conv_test 14/14 at 738ac50 | **VERIFIED** |
| WINEDROID-015/016 | same | a784c0b | Apache-2.0 | diagnostics CLI + warning-accumulation | diagnostics | Q-13 inspect enrichment | winedroid-study.md | ADAPTABLE |
| WINEDROID-017 | same | a784c0b | Apache-2.0 | untrusted-APK posture (caps/sandbox doc) | loader + docs | Q-14 doc+cap check | winedroid-study.md | ADAPTABLE |
| WINEDROID-019 | same | a784c0b | Apache-2.0 | tests-as-executable-spec (synthetic DEX in code) | test harness | tooling budget | winedroid-study.md | DEFERRED |
| WINEDROID-020 | same | a784c0b | Apache-2.0 | honest limitation ledger (docs discipline) | project docs | n/a | winedroid-study.md | REFERENCE (adopted as documentation practice) |

## C. AOSP ART / dalvik / framework / native (official googlesource)

| ID | URL | Revision | License | Mechanism | MiniAndroid relevance | Test required | Evidence | Status |
|---|---|---|---|---|---|---|---|---|
| AOSP-001..017 | https://android.googlesource.com/platform/art/ + /platform/frameworks/base/ + /platform/frameworks/native/ | art 6484611f, fwbase 1cdfff55, native 4f463a6b | Apache-2.0 | full catalog in aosp-runtime-study.md (measure/layout laws, Resources contracts, Handler priority, Paint/Path/Canvas semantics, SharedPreferencesImpl, lifecycle root, DexFileVerifier order, cdex detection) | semantic oracle for all runtime ambiguities | per-row test plans (Q-5, Q-6, Q-7, Q-12) | aosp-runtime-study.md + layout-study.md LAY-001..006 | REVIEWED→ per-row as matrix annex; AOSP-013 div/rem VERIFIED this session (94/94 battery); EXT-AOSP-001/002 (subset of AOSP framework catalog) IMPLEMENTED+VALIDATED this session |
| AOSP-016 | https://android.googlesource.com/platform/art/ | 6484611f | Apache-2.0 | compact-dex explicit rejection diagnostic | dex loader diagnostics | Q-7 cdex-magic unit | aosp-runtime-study.md | ADAPTABLE |

## D. ARSC / AXML / toolchain oracles

| ID | URL | Revision | License | Mechanism | MiniAndroid relevance | Test required | Evidence | Status |
|---|---|---|---|---|---|---|---|---|
| ARSC-001 | https://github.com/iBotPeaches/Apktool | baa603f | Apache-2.0 | SPARSE(0x01)/OFFSET16(0x02)/STAGED_API flag laws | arsc_parser coverage | Q-8 sparse/offset16 fixtures | arsc-resource-study.md | ADAPTABLE |
| ARSC-002 | https://github.com/skylot/jadx | 8f7ea4e | Apache-2.0 | skip-to-chunk-end invariant | arsc_parser robustness | debug assertion | arsc-resource-study.md | ADAPTABLE |
| ARSC-003 | https://github.com/REAndroid/ARSCLib | HEAD (clone) | Apache-2.0 | typed-value encoding + JSON differential oracle | fixture tooling | Q-9 JSON diff | arsc-resource-study.md | ADAPTABLE |
| ARSC-006 | https://github.com/auxten/libarsc | HEAD (clone) | MIT | package/type/entry/string-pool layout cross-check | arsc_parser | Q-8/Q-10 shared fixtures | arsc-resource-study.md | REVIEWED |
| DEX-009 | https://github.com/droidsaw/droidsaw | 50eb045b | (see study) | byte-exact parse→re-emit→diff preservation | ARSC round-trip harness | Q-10 harness | dex-runtime-study.md | ADAPTABLE |
| TOOL-001 | https://github.com/iBotPeaches/Apktool | baa603f | Apache-2.0 | bounded chunk reader pattern | arsc+axml parsers | refactor + tests | apk-toolchain-study.md | DEFERRED |
| TOOL-002 | https://github.com/skylot/jadx | 8f7ea4e | Apache-2.0 | oracle-first policy (JADX output = leads, not proof) | analysis workflow | n/a | apk-toolchain-study.md | REFERENCE |
| TOOL-004 | https://github.com/google/bundletool | 586a43a | Apache-2.0 | packaging consistency fail-fast | fixture builder lint | TOOL-003 lint step | apk-toolchain-study.md | ADAPTABLE |
| RRO-006 | https://github.com/mirzachi/android-rro | a113f0a | MIT | Res_value edge semantics: TYPE_NULL/DATA_NULL_EMPTY, TYPE_DYNAMIC_REFERENCE verbatim | ordinary-ARSC coverage (beyond overlays) | 2 new ARSC unit vectors (queued) | auxiliary-repo-studies.md | ADAPTABLE |
| RRO-001..005 | https://github.com/mirzachi/android-rro | a113f0a | MIT | overlay precedence, idmap reverse map, OMS reload protocol | NOT needed for single-APK corpus (needs OMS/PMS/AMS layer) | n/a | auxiliary-repo-studies.md | **REJECTED** (scope) / FUTURE reference |

## DEX semantics / interpreter references

| ID | URL | Revision | License | Mechanism | MiniAndroid relevance | Test required | Evidence | Status |
|---|---|---|---|---|---|---|---|---|
| DEX-001..007 | https://android.googlesource.com/platform/art/ + dalvik mirror | 6484611f | Apache-2.0 | opcode semantics catalog (comparisons, conversions, wide, invoke) | interpreter oracle | 94-case battery re-run at 738ac50 PASS | dex-runtime-study.md | VERIFIED (battery) |
| DEX-008 | DaliVM (see dex-runtime-study.md for URL) | HEAD | GPL-3.0 | opcode hex-range coverage-matrix tables | coverage audit artifact | generator script | dex-runtime-study.md | DEFERRED (zero import — license) |
| DEXTP-001 | https://github.com/vimalloc/dexterpreter | b83d1513 | NO LICENSE | DEX interpreter skeleton (return-family only), DEX→s-expression dump | REFERENCE ONLY (no edge-case semantics beyond returns; no license = zero reuse) | n/a | auxiliary-repo-studies.md | REVIEWED / REFERENCE |
| GMD-001 | gmdice corpus APK | sha 1621eda1… | GPL (app) | canonical generic resource test (AXML+ARSC real chain) | corpus golden | u011 matrix row | matrix c49ed25f at 738ac50 | VERIFIED |

## Runner / diagnostics / testing methodology

| ID | URL | Revision | License | Mechanism | MiniAndroid relevance | Test required | Evidence | Status |
|---|---|---|---|---|---|---|---|---|
| METH-001 | https://github.com/robolectric/robolectric | fc357fec | MIT | bitmap comparison triage ladder (dims→config→pixels w/ precision floor) + shadow record/replay visualization | frame-diff failure diagnostics when a golden breaks | future: triage report on induced mismatch | auxiliary-repo-studies.md | ADAPTABLE (methodology) |
| METH-002 | https://github.com/cashapp/paparazzi | 716755fb | Apache-2.0 | failure-artifact dir (golden/actual/delta PNGs) + OffByTwo tolerance verdicts + manifest self-description | hash-mismatch failure reports; honesty convention: default stays exact-match | future: failure dir writer in validators | auxiliary-repo-studies.md | ADAPTABLE (methodology) |
| METH-003 | https://github.com/takahirom/roborazzi | 6abd5fc0 | Apache-2.0 | record/verify/compare verbs + UI-tree JSON sidecar per capture | structure evidence next to pixel evidence (frames_manifest + view_tree.json pairing) | future: sidecar emission | auxiliary-repo-studies.md | ADAPTABLE (methodology) |
| METH-004 | https://github.com/Karumi/Shot | e102d797 | Apache-2.0 | explicit tolerance disclosure warning; exists→dims→exact ladder | if a tolerance mode is ever added, disclose loudly | n/a | auxiliary-repo-studies.md | REFERENCE |
| METH-005 | https://github.com/dropbox/dropshots | 70b8cbfd | Apache-2.0 | ResultValidator policy abstraction (default exact) | named-policy shape for any future advisory mode | n/a | auxiliary-repo-studies.md | REFERENCE |
| RUNNER-001 | https://github.com/Shrey113/Android-Dex | c57cbc8 | NO LICENSE | two-tier error taxonomy; deterministic boot ladder; connection-error classifier gating recovery | runner diagnostics methodology | future: classifier in triage | auxiliary-repo-studies.md | REFERENCE ONLY (zero reuse — no license) |

## Repository-level rows (§31 inventory statuses)

| Project | Exact URL | Revision | License | Status |
|---|---|---|---|---|
| WineDroid | https://github.com/rickbergs/winedroid | a784c0b | Apache-2.0 | REVIEWED (source-level, 21 files) |
| AOSP ART | https://android.googlesource.com/platform/art/ | 6484611f | Apache-2.0 | REVIEWED |
| AOSP Frameworks/base | https://android.googlesource.com/platform/frameworks/base/ | 1cdfff55 | Apache-2.0 | REVIEWED (line-exact where cited) |
| AOSP Frameworks/native | https://android.googlesource.com/platform/frameworks/native/ | 4f463a6b | Apache-2.0 | REVIEWED (architecture validation) |
| AOSP dalvik (mirror) | https://android.googlesource.com/platform/dalvik/ | mirror HEAD | Apache-2.0 | REVIEWED |
| Cuttlefish | https://android.googlesource.com/device/google/cuttlefish/ | a1162ca7 | Apache-2.0 | REVIEWED (concepts only) |
| QEMU/emulator | https://android.googlesource.com/platform/external/qemu/ | ae9d18d2 (emu-master-dev) | GPL/BSD mix | REVIEWED (concepts only) |
| crosvm | https://github.com/google/crosvm | 9d4dc5f | BSD-3 | REVIEWED (concepts only) |
| AVF/Virtualization | https://android.googlesource.com/platform/packages/modules/Virtualization/ | 175a51b3 | Apache-2.0 | REVIEWED (concepts only) |
| Waydroid | https://github.com/waydroid/waydroid | e7d73e7f | GPL-3.0 | REVIEWED — container model REJECTED (identity mismatch) |
| Skydnir | https://github.com/ryo100794/skydnir | clone HEAD | custom (all-rights) | REVIEWED — methodology only, zero reuse |
| DroidVM | https://github.com/Droid-VM/DroidVM | clone HEAD | GPL-3.0 | REVIEWED — REJECTED (inverse problem: VMs ON Android) |
| DroidSaw | https://github.com/droidsaw/droidsaw | 50eb045b | (study) | REVIEWED — round-trip methodology ADAPTABLE |
| JADX | https://github.com/skylot/jadx | 8f7ea4e | Apache-2.0 | REVIEWED — oracle |
| Apktool | https://github.com/iBotPeaches/Apktool | baa603f | Apache-2.0 | REVIEWED — ARSC constants pinned |
| Bundletool | https://github.com/google/bundletool | 586a43a | Apache-2.0 | REVIEWED |
| libarsc (auxten) | https://github.com/auxten/libarsc | clone HEAD | MIT | REVIEWED |
| ARSCLib (REAndroid) | https://github.com/REAndroid/ARSCLib | clone HEAD | Apache-2.0 | REVIEWED — differential oracle queued |
| Android-RRO | https://github.com/mirzachi/android-rro | a113f0a | MIT | REVIEWED — RRO REJECTED, Res_value vectors ADAPTABLE |
| sim-use | https://github.com/SimulaVR/sim-use | — | — | **UNAVAILABLE** (404/credential-fail; 2nd session retry recorded) |
| dexterpreter | https://github.com/vimalloc/dexterpreter | b83d1513 | NO LICENSE | REVIEWED (URL verified this campaign) |
| Android-Dex | https://github.com/Shrey113/Android-Dex | c57cbc8 | NO LICENSE | REVIEWED (methodology only) |
| AndroidRecomp | (discovery mandated; no canonical upstream verifiable) | — | — | **URL_UNVERIFIED** |
| ReSource | (discovery mandated; no canonical upstream verifiable) | — | — | **URL_UNVERIFIED** |
| Reveree | (discovery mandated; no canonical upstream verifiable) | — | — | **URL_UNVERIFIED** |
| frameworks/av | https://android.googlesource.com/platform/frameworks/av/ | — | Apache-2.0 | DEFERRED (media stack below criticality; gap G10) |

## Counts (§31 scoreboard)

- Rows total: 66 (3 implemented/validated this campaign + 14 WineDroid +
  19 AOSP/DEX + 9 ARSC/toolchain + 6 runner/methodology + 15 repo-level)
- IMPLEMENTED+VALIDATED this campaign: 2 mechanisms (EXT-AOSP-001/002)
- VERIFIED (already implemented, re-evidenced at current HEAD): 4 rows
  (WINEDROID-013, DEX-001..007 battery, GMD-001, EXT-EXEC-001 golden)
- ADAPTABLE (transfer queue): 24
- REFERENCE ONLY: 6 · DEFERRED: 5 · REJECTED (with reasons): 4
- UNAVAILABLE: 1 (sim-use) · URL_UNVERIFIED: 3 (AndroidRecomp, ReSource,
  Reveree) · review-complete repositories: 25 reachable, all with pinned
  revisions in docs/research/external-repositories.md

GitHub Comment URL column: `—` everywhere — push BLOCKED this sandbox
(no remote, no credentials). Commit chain is the persistent record;
PUSH_BLOCKED block in the final report (§40).
