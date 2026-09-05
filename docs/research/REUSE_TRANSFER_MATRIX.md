# REUSE_TRANSFER_MATRIX — §37 research→code tracker

Campaign: MAXIMUM REUSE / FULL SOURCE AUDIT / COMPLETE APK EXECUTION (2026-09-05)
Law: every mechanism from every studied source gets one row; statuses move
forward only with a commit + test reference. No row is retired silently.

Statuses: DISCOVERED / AUDITED / REUSE-CANDIDATE / IMPLEMENTED / VALIDATED /
REJECTED / DUPLICATE / UNAVAILABLE

## WineDroid (rickbergs/winedroid @ a784c0b, Apache-2.0) — second pass 2026-09-05

| ID | Source file/symbol | Mechanism | MiniAndroid target | Status | Commit | Test | Result |
|---|---|---|---|---|---|---|---|
| WD-004 | winedroid-core dex.rs decode_mutf8 | MUTF-8 decode law | dex/mutf8.cpp decode_string_data | VALIDATED | 2c8bf2da (prior) | mutf8 T1–T6 | ONE decoder; non-ASCII corruption fixed |
| WD-005 | winedroid-core dex.rs read_uleb128 | hardened ULEB128 (≤5 bytes) | mutf8::read_uleb128 | VALIDATED | 2c8bf2da (prior) | T5 + ULEB window | 5-byte cap, no UB |
| WD-003 | winedroid-core dex.rs validate_table | per-table bounds/alignment pre-validation (offset≠0, 4-byte aligned, checked count×item_size BEFORE alloc) + file_size ≥ header_size | dex/dex_parser.cpp validate_section_table | **VALIDATED (2026-09-05)** | **b6ba545d** | mutf8 T7–T10 (hostile-header: zero offset / misaligned / count 0xFFFFFFFF / small file_size) | ONE gate for all 6 section tables; hostile count allocated ~16 GB pre-law (std::bad_alloc reproduced), now named error with no allocation |
| WD-ABI | docs/GENERIC_METHOD_ABI.md | uniform `method(argc, args)` ABI; `incoming_start = registers_size − ins_size`; ins_size ≤ registers_size guard | dalvik_engine invoke marshalling (MethodInfo.registers_size/ins_size stored since EXP-058) | AUDITED/DUPLICATE | — | pass3 bridge invoke cases | engine already maps incoming regs via ins_size; ins_size>registers_size hostile case = REUSE-CANDIDATE (queued, low priority — guarded upstream by code_item bounds) |
| WD-HDR | winedroid-core dex.rs parse_header | cdex magic rejection; unknown endian_tag hard reject; declared≠archive size WARN | dex_parser validate_header | DUPLICATE (stricter) | — | parse-neg battery | MiniAndroid whitelists magic 035–039 (rejects cdex), accepts only 0x12345678 |
| WD-PSW | tests/packed_switch.rs | per-destination payload validation | switch decoder + discriminator 011 | DUPLICATE | — | sw_packed_payload_is_data_winedroid011 | payload-is-data law pinned |
| WD-AOT | aot.rs / linked.rs / recursive.rs | AOT C-emission + ELF pipeline | n/a | REJECTED (architecture) | — | — | MiniAndroid is an in-process runtime; adopted laws only |

## AOSP (androidfw / frameworks/base @ 1cdfff55, Apache-2.0) — 2026-09-05

| ID | Source symbol | Mechanism | MiniAndroid target | Status | Commit | Test | Result |
|---|---|---|---|---|---|---|---|
| AOSP-LIN-V | LinearLayout.java layoutVertical | container main-axis gravity offsets the whole child block (CENTER → half leftover, BOTTOM → all) | resources/layout_inflater.cpp | **VALIDATED (2026-09-05)** | **d19bdd05** | helloworld golden 26/26 (headline block rows 881-945, centered) | FIND-GRAVITY-VERTICAL closed; corpus: 2 apps identical, simplestopwatch 1,777 px (0.09 %) one element repositioned |
| AOSP-LIN-H | LinearLayout.java layoutHorizontal | symmetric main-axis law + axis-field equality (mask 0x7 then compare) | same | **VALIDATED (2026-09-05)** | **d19bdd05** | same golden + cross-axis equality | `& 0x50`-style misfires structurally dead |
| AOSP-SP | String.cpp utf16_to_utf8 | surrogate combine / U+FFFD | mutf8::utf16le_to_utf8 | VALIDATED (prior) | e69bc496 | T8–T12 | manifest double-encoding fixed |
| AOSP-RSP | ResourceTypes.cpp ResStringPool | offsets-table indexing, decodeLength 1-or-2 | resources/string_pool.{h,cpp} | VALIDATED (prior) | 4d822256 | battery + corpus pixel-identity | BLOCKER-006 class dead |

## Dead-code audit (§25) — 2026-09-05

| ID | Target | Proof (no filename-only reasoning) | Status | Commit | Result |
|---|---|---|---|---|---|
| DEAD-001 | dex_interpreter{,.h,_v2.,_exp018.} + exp003a/exp018/exp019 mains + runtime_integration_exp019 | Makefile builds dex_interpreter_batch.cpp; zero live includes (only orphan standalone mains, no Makefile target); zero test references | **REMOVED+VALIDATED** | 41946f7c | −10,258 LOC; make clean rc=0; battery 11/11; corpus 3/3 exit 0; binary unchanged (dead code never linked) |

## Honest open queue (not claimed)

- ins_size > registers_size hostile code_item guard (WD-ABI) — REUSE-CANDIDATE
- declared-vs-archive size mismatch WARN (WD-HDR observability) — REUSE-CANDIDATE
- FIND-EXC-TRUNC SLEB truncation semantics audit — queued (prior session)
- Font pipeline structured FONT_* diagnostics (§5 of campaign mandate) — queued
- Compose multi-DEX method resolution, Telegram chain, WebView boundary — queued (prior records stand)
