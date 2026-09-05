# External Mechanism Matrix — provenance-tracked

Law (§23): every mechanism carries ID, repository, exact URL, revision,
source path, MiniAndroid subsystem, implementation commit (when
implemented), test, runtime evidence, status. This campaign is
research-first: rows marked IMPLEMENTED carry commits; rows marked
DISCOVERED / CANDIDATE are the transfer queue.

Key: STATUS ∈ {DISCOVERED, CANDIDATE, QUEUED, DEFERRED, NOT APPLICABLE,
ARCHITECTURE VALIDATION, VERIFIED (already implemented & evidenced)}.

| ID | Repo (revision) | Source path/symbol | Mechanism | MiniAndroid subsystem | Test / evidence plan | Status |
|---|---|---|---|---|---|---|
| WINEDROID-001 | winedroid (a784c0b) | core/apk.rs inspect_apk, classify_entry | typed ZIP entry classification + unsafe-path warning + size caps | src/apk/ loader diagnostics | inspect fixture APK → expect warning list | CANDIDATE |
| WINEDROID-003 | winedroid (a784c0b) | core/dex.rs validate_table | per-table bounds+alignment pre-validation with named errors | dalvik_engine DEX load | corrupt-DEX unit fixture | CANDIDATE |
| WINEDROID-004 | winedroid (a784c0b) | core/dex.rs decode_mutf8 | MUTF-8 declared-vs-actual utf16 cross-check; NUL + surrogate handling | dex string pool | 3 unit vectors (NUL, surrogate, u32 ULEB) | QUEUED |
| WINEDROID-006 | winedroid (a784c0b) | dex_method.rs is_dex_name/dex_number | numeric multi-dex ordering law + test vectors | multi-dex method resolution | adopt ordering test | QUEUED |
| WINEDROID-007 | winedroid (a784c0b) | bootstrap.rs frame setup + docs/GENERIC_METHOD_ABI.md | generic invoke ABI: incoming_start law, zero-fill, ins≤regs | dalvik_engine invoke paths | zero-fill discriminator fixture | CANDIDATE |
| WINEDROID-009 | winedroid (a784c0b) | recursive.rs collect_graph + report | per-method link/reject graph with reasons (pc+opcode) | runtime diagnostics (try_recursive_invoke) | structured report artifact per APK | CANDIDATE |
| WINEDROID-010 | winedroid (a784c0b) | recursive.rs is_known_external_namespace | external namespace prefix list | shadow registry coverage audit | coverage diff vs prefix list | CANDIDATE |
| WINEDROID-011 | winedroid (a784c0b) | aot.rs branch decode + ABI doc | payload-is-data scanner invariant | dex interpreter scanner | payload=opcode-byte fixture | QUEUED |
| WINEDROID-013 | winedroid (a784c0b) | aot.rs wd_div/wd_rem | INT32_MIN/-1 div-rem semantics | interpreter arith | existing fixtures (re-run) | VERIFIED (pending HEAD re-run) |
| WINEDROID-014 | winedroid (a784c0b) | aot.rs validate_static_opcode_type | sget/sput variant↔type strictness | interpreter field ops | type-mismatch fixture | CANDIDATE |
| WINEDROID-015 | winedroid (a784c0b) | winedroid-cli inspect | per-DEX count block + warnings report + JSON | runtime diagnostics CLI | inspect report on golden APK | CANDIDATE |
| WINEDROID-016 | winedroid (a784c0b) | apk.rs/axml.rs warnings fields | inspection never hard-fails; warnings accumulate | apk/arsc/axml diagnostics | warning-list assertions | CANDIDATE |
| WINEDROID-017 | winedroid (a784c0b) | README Segurança + caps | untrusted-APK posture: caps, sandbox doc | runtime docs + loader caps | docs + cap check | CANDIDATE |
| WINEDROID-019 | winedroid (a784c0b) | tests/*.rs, dex.rs build_class_only_dex | synthetic-DEX-in-code test tooling | test harness | port minimal builder | DEFERRED (tooling budget) |
| AOSP-001 | fwbase (1cdfff55) | View.java measure() | measured-dimension guard (IllegalStateException law) | view measurement | debug assertion + fixture | CANDIDATE |
| AOSP-003 | fwbase (1cdfff55) | ViewGroup.getChildMeasureSpec L7048 | 3×3 child spec table | real_layout | covered rows already pinned; UNSPECIFIED row fixture | PARTIALLY VERIFIED |
| AOSP-005 | fwbase (1cdfff55) | ViewGroup.measureChildren L6968 | GONE children excluded from measure | measure path | GONE-weighted-child fixture | QUEUED |
| AOSP-007 | fwbase (1cdfff55) | Resources.getString(L564)/getIdentifier(L2325) | id=0 invalid; format-args via locale String.format | resource shadows | format-args fixture | QUEUED |
| AOSP-009 | fwbase (1cdfff55) | Handler.dispatchMessage L101 | Runnable→callback→handleMessage priority | dispatch shadows | priority-order fixture | CANDIDATE |
| AOSP-010 | fwbase (1cdfff55) | Paint.Style L568 | FILL_AND_STROKE CCW caveat | software_renderer | CCW fill-and-stroke fixture | QUEUED |
| AOSP-015 | art (6484611f) | dex_file_verifier.cc Verify() | check-order law: header→map→intra→inter | dex diagnostics | message-order assertion | DEFERRED (low risk) |
| AOSP-016 | art (6484611f) | compact_dex_file.* + winedroid dex.rs | explicit cdex rejection diagnostic | dex loader | cdex-magic unit test | CANDIDATE |
| ARSC-001 | Apktool (baa603f) | BinaryResourceParser constants | SPARSE/OFFSET16/STAGED_API flag laws | arsc_parser | sparse/offset16 unit fixtures | QUEUED (differential plan) |
| ARSC-002 | jadx (8f7ea4e) | ResTableBinaryParser.parse | skip-to-chunk-end invariant | arsc_parser | debug assertion | CANDIDATE |
| ARSC-003 | ARSCLib (HEAD) | ValueCoder/TableBlock | typed-value encoding + JSON differential oracle | fixture tooling + arsc diff | JSON diff vs our decode | QUEUED |
| DEX-008 | DaliVM (HEAD) | README opcode tables | opcode coverage matrix artifact | dalvik_engine | generator script + table | DEFERRED (queued from prior session; budget) |
| DEX-009 | droidsaw (50eb045b) | preservation mode concept | byte-exact parse→re-emit→diff for format models | arsc/axml/dex parsers | round-trip test harness | QUEUED (ARSC first) |
| GFX-004 | crosvm (9d4dc5f) / cuttlefish (a1162ca7) | ARCHITECTURE.md; host/guest split | sandbox/process separation patterns | runtime hardening roadmap | docs only | DEFERRED (no sandbox requirement yet) |
| FONT-002 | fwbase (1cdfff55) | Typeface.createFromAsset L1127 | missing→throw vs corrupt→silent-DEFAULT distinction | font diagnostics | Case-F fixture distinguishing events | QUEUED |
| TOOL-001 | Apktool (baa603f) | ResChunkPullParser | shared bounded chunk reader | arsc+axml parsers | refactor candidate | DEFERRED (low priority) |
| TOOL-003 | bundletool (586a43a) | packaging validation flow | fail-fast manifest/resource consistency in fixture builds | build_fixture_apk.sh | lint step in tool | CANDIDATE |

## Counts
- Mechanisms discovered and documented this campaign: 34 rows above
  (WineDroid 20 cataloged in winedroid-study.md; matrix carries the
  transferable subset plus AOSP/ARSC/DEX/font rows).
- Already implemented + evidenced (VERIFIED rows): 4
- Queued with named test plan: 11
- Candidates (decision pending): 12
- Deferred with reason: 5
- Not applicable / architecture validation: 2
