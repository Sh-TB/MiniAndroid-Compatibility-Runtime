# WineDroid Deep Study — REUSE-FIRST synthesis (WINEDROID_DEEP_STUDY.md)

Campaign: REUSE-FIRST FULL COMPATIBILITY + RESEARCH-TO-CODE
Date: 2026-09-05 · Exact URL (mandated, never substituted):
**https://github.com/rickbergs/winedroid**
Revision studied: `a784c0b956893733cc12ccd3bec7695b0791f978` (2026-07-14)
License: Apache-2.0 · Clone: `research-clones/winedroid` (origin verified
identical to the mandated URL; the DIFFERENT `sohzm/winedroid` /
winedroid.soham.sh project remains a separate matrix row).

This document is the REUSE-FIRST synthesis. The file-by-file mechanism
catalog (WINEDROID-001..020, every claim citing file+function) lives in
`docs/research/winedroid-study.md` from the previous campaign and was
verified against the same clone revision — it is NOT duplicated here.

## What WineDroid is (one paragraph)

A Rust workspace that AOT-compiles a bounded graph of Dalvik methods
(APK → DEX parse → C emission → Clang → ELF64 PIE x86-64) and runs it
natively on Linux — the Wine approach applied to Android *bytecode*.
MiniAndroid is the sibling with the OPPOSITE execution model (in-process
DEX interpreter). That difference decides every transfer decision below:
WineDroid's compilation-time machinery transfers as *law and
discriminator*, never as runtime code.

## What THIS campaign did with the study (research → code)

The prior campaign extracted 20 mechanisms and queued several as
"adapt". This campaign converted the queue into implementation and
executable law, each with a reproducer before the fix:

| ID | Mechanism | Status BEFORE | Action THIS campaign | Status AFTER |
|---|---|---|---|---|
| WINEDROID-004 | MUTF-8 decode: 0xC080-encoded NUL, CESU-8 surrogate pairs, declared-vs-actual utf16 cross-check | gap (raw-byte copy) | **IMPLEMENTED** as part of the shared primitive `src/dex/mutf8.{h,cpp}`; reproducer `tests/mutf8_string_pool_test.cpp` T1/T2/T4 first proved live truncation of "héllo→!" at HEAD | **IMPLEMENTED → VALIDATED (7/7 battery)** |
| WINEDROID-005 | Hardened ULEB128 (≤5 bytes, final ≤0x0F, bounds) | gap (unbounded shift → UB on hostile input, ×3 copies) | **IMPLEMENTED** in the same primitive (`read_uleb128`); T5 + primitive-window tests | **IMPLEMENTED → VALIDATED** |
| WINEDROID-007 | Generic invoke-argument law; absent args deterministic (zero-fill) | NOT_TESTED discriminator | **DISCRIMINATOR TEST** `wd_absent_arg_deterministic_winedroid007` — pins: absent args = deterministic (engine zero-init/invalid-state policy), never garbage | **VALIDATED (deterministic)** |
| WINEDROID-011 | packed-switch payload-is-data invariant | implicit | **DISCRIMINATOR TEST** `sw_packed_payload_is_data_winedroid011` — payload embeds a return-void encoding (0x0E00) as first_key; pc-driven execution must never decode it | **VALIDATED** |
| WINEDROID-003 | Per-table bounds/alignment pre-validation | gap (we validate, less strictly) | QUEUED with design (apply WineDroid's `offset + count*size <= size` + alignment law in dex_parser table loop; cheap, converts corrupt-input crashes into named diagnostics) | LEAD (queued) |
| WINEDROID-015/016 | `inspect` diagnostics block + warning-accumulation discipline | gap | QUEUED (extend APK report with per-DEX counts + warnings list; mirrors our BLOCKED-reason law at parse level) | LEAD (queued) |
| WINEDROID-006/013/014 | multi-dex ordering; INT32_MIN div/rem; sget/sput type-strictness | already ours | cross-checked against our battery — our tests already pin these; no change | VERIFIED (ours) |
| WINEDROID-012/018/019/020 | exceptions/emit-c/tests-as-spec/limitation-ledger | we are ahead | schedule-validation oracle only | REFERENCE |
| WINEDROID-001/002/008/009/010/017 | inspection/classification/objects/linker/namespace/security | mixed | see winedroid-study.md reconciliation table; unchanged this campaign | per prior doc |

## The one structural result: 3 copies → 1 primitive (FIND-REUSE-001)

Study said "REIMPLEMENT CONCEPT"; the reuse-first audit found the concept
existed THREE times in MiniAndroid, each incomplete:

1. `dex_parser.cpp::read_dex_string` — inline ULEB128 + **utf16_size
   treated as byte count** + no MUTF-8 decode (REAL bug: every non-ASCII
   string truncated; encoded NUL left raw).
2. `dex_parser.cpp` class-data lambda — inline ULEB128 with logging, no
   5-byte cap (UB on hostile input).
3. `dalvik_engine.cpp::read_dex_string_from_raw` — third ULEB128 + same
   byte-count truncation.

Now all three delegate to `src/dex/mutf8.{h,cpp}` — ONE primitive with
the WineDroid laws hardened in. Reproducer ran at HEAD BEFORE the fix:
S1 "héllo→!" → 7 garbled bytes; S2 encoded-NUL undecoded. After: 7/7
battery PASS, and the full gate (96 semantic + goldens) stayed green.

Maintenance effect (§22): future DEX string issues have exactly one
place to fix and one battery to extend; corruption is now observable
(declared-vs-actual cross-check) instead of silent.

## §2 mechanism mapping table (REUSE-FIRST MAXIMUM PROGRESS session, 2026-09-05)

The mandated per-mechanism chain — mechanism → MiniAndroid equivalent →
existing implementation → duplicate? → reusable primitive? → missing
behavior? → required test → can code be deleted? — resolved for the
high-value mechanisms. Strongest result: YES in the last column three
more times this session (FIND-REUSE-002/003/004).

| WineDroid mechanism | MiniAndroid equivalent | Existing implementation (current HEAD) | Duplicate? | Reusable primitive? | Missing behavior | Required test | Can code be deleted? |
|---|---|---|---|---|---|---|---|
| 004 MUTF-8 decode (0xC0 0x80 NUL, CESU-8 pairs, declared-vs-actual) | DEX string pool decode | `dex/mutf8.cpp decode_string_data` (ONE, since FIND-REUSE-001) | NO (was ×3) | YES — the only MUTF-8 decoder | none open | mutf8 battery T1–T6 | YES — deleted (−68 LOC, prior session) |
| 005 hardened ULEB128 (≤5 bytes, final ≤0x0F) | DEX varint readers | `mutf8::read_uleb128` | NO (was ×3) | YES | none open | T5 + ULEB window | YES — deleted (prior session) |
| (Dalvik format) SLEB128 handler sizes | try/catch handler parse | `mutf8::read_sleb128` (NEW, FIND-REUSE-003) | NO (was ×2 inline lambda pairs) | YES | truncation policy = FIND-EXC-TRUNC (queued) | mutf8 SLEB window (10 vectors) | YES — deleted this session (−56 LOC) |
| (ARSC/AXML law) UTF-16LE pool → UTF-8 | string pool text decode | `mutf8::utf16le_to_utf8` (NEW, FIND-REUSE-002) | NO (was ×5, one buggy) | YES | unpaired → U+FFFD law now applied (old copies WTF-8'd) | T8–T12 windows | YES — deleted this session (−94 LOC incl. bug fix) |
| (androidfw law) ONE ResStringPool for ARSC+AXML+manifest | pool chunk parse | `resources/string_pool.{h,cpp}` (NEW, FIND-REUSE-004) | NO (was ×3) | YES | offsets-table indexing replaces sequential walk (BLOCKER-006 class dead) | battery + corpus pixel-identity ×3 | YES — deleted this session (−158 LOC net) |
| 007 absent-arg determinism | invoke argument marshalling | engine zero-init policy | no | test only | — | `wd_absent_arg_deterministic_winedroid007` | — (test pins it) |
| 011 packed-switch payload-is-data | switch decode | switch decoder + discriminator | no | test only | — | `sw_packed_payload_is_data_winedroid011` | — |
| 003 per-table bounds/alignment pre-validation | DEX table loops | `dex_parser validate_section_table` (**IMPLEMENTED 2026-09-05, FIND-REUSE-005, commit b6ba545d**) | n/a | adapt — DONE | closed: zero-offset + 4-byte alignment + checked count×item_size BEFORE allocation + file_size ≥ header_size | mutf8 battery T7–T10 (hostile-header group; std::bad_alloc pre-law reproduced as discrimination proof) | 6 duplicated inline bounds checks collapsed into 1 gate |
| AOT C emission/ELF pipeline | (opposite model — in-process interpreter) | n/a | n/a | NO — architecture REJECTED for MiniAndroid | n/a | n/a | n/a |

## Honest limits of this study

- WineDroid revision is pinned (a784c0b); re-run `ls crates` + `rg`
  before citing on any future revision (their ROADMAP moves fast).
- Their runtime has no graphics/resources yet — nothing to compare
  against our render/resource stacks; they remain the AOT sibling.
- We did NOT adopt their compilation pipeline (out of architecture
  scope; would violate "MiniAndroid is not a fork" law).
