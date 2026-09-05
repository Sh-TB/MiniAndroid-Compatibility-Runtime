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

## Honest limits of this study

- WineDroid revision is pinned (a784c0b); re-run `ls crates` + `rg`
  before citing on any future revision (their ROADMAP moves fast).
- Their runtime has no graphics/resources yet — nothing to compare
  against our render/resource stacks; they remain the AOT sibling.
- We did NOT adopt their compilation pipeline (out of architecture
  scope; would violate "MiniAndroid is not a fork" law).
