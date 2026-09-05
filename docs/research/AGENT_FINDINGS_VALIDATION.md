# AGENT_FINDINGS_VALIDATION — findings are leads, HEAD is the judge

Campaign: REUSE-FIRST FULL COMPATIBILITY + RESEARCH-TO-CODE
Date: 2026-09-05 · Local HEAD: `9e7c0e9b`

Chain per campaign law: LEAD → CURRENT-HEAD VALIDATION → REPRODUCER →
ROOT CAUSE → FIX → REGRESSION TEST → RUNTIME EVIDENCE → VERIFIED.

Prior campaigns produced a 118-finding master audit
(`docs/research/AGENT_FINDING_AUDIT.md`) and subsystem studies. This
campaign re-ran the executable gates at the current HEAD and processed
the highest-priority open leads from the WineDroid study. Results:

## 1. Current-HEAD revalidation of previously-claimed results

| Gate (claimed by prior campaign) | Claim | This campaign's HEAD re-run | Verdict |
|---|---|---|---|
| helloworld_golden §28 (18 checks) | PASS at 738ac50 | **18/18 PASS, screenshot SHA256 93b42621… byte-identical** | VERIFIED at 9e7c0e9b |
| tictactoe_golden §29 (interaction) | PASS at de5f370e | **ALL PASS — 9/9 clicks, 'X to move'→'O to move'→'X WINS', 10 frames, deterministic replay** | VERIFIED at 9e7c0e9b |
| semantic battery 94/94 | PASS at 738ac50 | 14 + 57 + 25 = **96/96 PASS** (battery grew by 2 WineDroid discriminators) | VERIFIED |
| build | PASS | clean rebuild PASS (twice) | VERIFIED |
| u011 matrix hashes | 6/7 unchanged at 738ac50 | not re-run (no layout/font change this campaign; re-run mandated after any such change) | NOT_RE_RUN (honest) |
| font Cases A–F consolidation | A/B/D/E VERIFIED, C open-blocked, F pinned (fe5e5ba) | not re-litigated; six-evidence record stands at its cited HEAD | carried at fe5e5ba |

## 2. New finding processed THIS campaign (full chain)

### FIND-REUSE-001 — DEX string pool corrupts non-ASCII strings (REAL bug)
- **Lead source**: WineDroid study WINEDROID-004/005 gap analysis
  (winedroid-study.md said "REIMPLEMENT CONCEPT").
- **CURRENT-HEAD validation**: audit of `dex_parser.cpp::read_dex_string`
  + `dalvik_engine.cpp::read_dex_string_from_raw` found THREE duplicated
  ULEB128/MUTF-8 implementations, all treating the string_data_item
  utf16_size (UTF-16 code units) as a BYTE count; no 5-byte ULEB cap.
- **Reproducer**: `tests/mutf8_string_pool_test.cpp` predecessors ran at
  HEAD before any fix — S1 "héllo→!" returned 7 raw bytes
  (`68 C3 A9 6C 6C 6F E2`), S2 encoded-NUL returned `61 C0 80`.
- **Root cause**: `std::string(data+pos, length)` with length=code units,
  no MUTF-8→UTF-8 decode, duplicated partial readers.
- **Fix**: ONE shared primitive `src/dex/mutf8.{h,cpp}` (commit
  `2c8bf2da`) — hardened ULEB128 + MUTF-8 decode + declared-vs-actual
  cross-check; all three call sites delegate.
- **Regression test**: mutf8 battery T1–T6 + primitive window (7 checks).
- **Runtime evidence**: full gate after fix — build PASS, battery 96/96,
  helloworld 18/18 (screenshot SHA unchanged), tictactoe ALL PASS.
- **Status**: **VERIFIED** (bug was real; fix is in; gate green).

## 3. Why the semantic battery did NOT catch FIND-REUSE-001 earlier
(process finding, recorded per §15 no-dead-tests law)

`semantic_pass3_bridge_test` builds its synthetic DEX by writing
`report.strings` DIRECTLY (bypassing `read_dex_string`), so the string
pool parse path was untested by design — a dead path with respect to
string decoding. The unicode concat case (`ps_concat_unicode_bytes`)
exercised the interpreter only. Lesson now pinned by the new battery,
which drives the REAL `DexParser::parse_data` path. The dead-path risk
is added to the audit method: every battery must name the entry point it
exercises; entry points with zero named coverage are findings.

## 4. Open leads NOT promoted this campaign (honest queue)

| Lead | Origin | Why deferred |
|---|---|---|
| WINEDROID-003 table alignment pre-validation | WineDroid study | queued with design; touches shared parse loop, deserves its own reproducer battery |
| WINEDROID-015/016 inspect block + warnings | WineDroid study | diagnostics-only; no runtime-behavior risk |
| RRO-006 ARSC edge vectors (TYPE_NULL/DATA_NULL_EMPTY, dynamic ref) | android-rro study | fixture work; ARSC behavior already RESULT_016-clean at last validation |
| frames_manifest triage ladder + failure artifacts | screenshot-testing synthesis | tooling; current SHA-pin oracle remains primary |
| Font Case C (open-blocked) | §26 six-evidence record | requires its fixture; separate session |

No finding was upgraded by claim alone; every VERIFIED above has an
executable artifact at the cited HEAD.
