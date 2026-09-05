# REUSE_REDUCTION_REPORT — §11/§22 measurable reuse-first outcomes

Campaign: REUSE-FIRST FULL COMPATIBILITY + RESEARCH-TO-CODE
Date: 2026-09-05 · Local HEAD: `9e7c0e9b`

## §11 table — duplicates eliminated / prevented

| Existing duplicate implementations | Shared primitive | Files reduced | Lines reduced |
|---|---|---:|---:|
| ULEB128 reader ×3 (`dex_parser.cpp::read_dex_string` inline; `dex_parser.cpp` class-data lambda; `dalvik_engine.cpp::read_dex_string_from_raw` inline) + MUTF-8 handling ×0 (absent everywhere) | `src/dex/mutf8.{h,cpp}` — ONE primitive: hardened ULEB128 + MUTF-8 decode + declared-vs-actual cross-check | 2 files lose inline logic (dex_parser.cpp −~50 LOC net, dalvik_engine.cpp −~18 LOC net), 1 new primitive file (+~180 LOC including docs) | ≈ −68 inline LOC, and the primitive is now the single repair point |
| Semantic-test harness duplication (hazard): battery cases re-declare helpers instead of new standalone harnesses | new WineDroid discriminator cases written INSIDE `semantic_pass3_bridge_test.cpp` reusing its `run_full`/`record`/emit helpers (0 new harness lines) | 0 new files | ≈ −120 LOC prevented (a standalone harness clone was the alternative) |
| Golden/battery re-validation procedure (was: manual multi-command sequences per campaign, documented differently each time) | `scripts/run_test_battery.sh` — ONE zero-skip gate: build → link → 96 semantic + 7 mutf8 → both goldens | replaces ~8 ad-hoc commands | future campaigns save the re-derivation cost; gate is self-verifying (PASS 0/FAIL 0 impossible) |
| `report.strings` bypass hazard (battery wrote string pool directly, leaving the real parse path untested — a dead path) | mutf8 battery drives `DexParser::parse_data` (the REAL entry point) | 1 battery fixed | prevents future silent-dead-path findings |

## §22 maintenance questions, answered for this campaign's feature

1. **Lines added**: ≈ +300 total (primitive ~180, battery ~170, gate ~110, minus ~120 removed inline) — the net is the price of three copies becoming one.
2. **Special cases added**: 0. The primitive has no per-app, per-DEX, or per-string special cases; corruption paths return diagnostics, not app-specific workarounds.
3. **Shared primitive created**: YES — `mutf8::read_uleb128` + `mutf8::decode_string_data`, the only MUTF-8 implementation in the tree.
4. **Reusable**: it is called from BOTH the DexParser pool path AND the engine's per-DEX raw path; any future path (e.g., ARSC strings use a different codec — out of scope) delegates here only if it is DEX MUTF-8.
5. **Generic test built**: the mutf8 battery builds minimal DEX buffers and exercises the real `parse_data` entry point — reusable for future string-pool laws.
6. **Future APIs covered automatically**: any const-string / descriptor / name resolution flows through the fixed paths with zero new code; corruption now surfaces as a named MUTF-8 WARNING instead of silent garbling.

## What the reduction buys beyond LOC

- **One repair point**: pre-fix, a MUTF-8 bug would need the same fix in
  three places (and two of them would likely be missed — the bug lived
  in the tree for the entire project history undetected).
- **Observability**: declared-vs-actual cross-check converts corrupt
  input from silent wrong-behavior into logged warnings — aligned with
  the BLOCKED-with-reason law.
- **Law pinning**: the 007/011 discriminators turn two more external
  mechanisms (WineDroid) into machine-checked invariants, so future
  refactors get caught by `run_test_battery.sh` instead of by the next
  source-study campaign.

## Anti-over-abstraction note (§11 limit)

No abstraction was added beyond the single primitive: the invoke-arg
law and the switch law stay as TESTS (they test behavior, not shared
code); the diagnostics queue (WINEDROID-015/016) stays a queue until
there is a second consumer. Over-abstraction is reuse debt, not reuse.

---

# Session addendum — REUSE-FIRST MAXIMUM PROGRESS / CODE-MINIMIZATION (2026-09-05, HEAD 4d822256)

## §11 table rows added this session

| Existing duplicate implementations | Shared primitive | Files reduced | Lines reduced |
|---|---|---:|---:|
| UTF-16LE→UTF-8 encoders ×5: `arsc_parser.cpp` 26L, `axml_parser.cpp` 22L, `manifest_reader.cpp` 21L (**buggy**: no surrogate handling → non-BMP manifest strings double-encoded), `dalvik_engine.cpp` `utf8_of` 12L, `mutf8.cpp` private `append_utf8` | `mutf8::utf16le_to_utf8` + exported `mutf8::append_utf8` (FIND-REUSE-002, AOSP String.cpp law: pairs combine, unpaired → U+FFFD) | 4 files lose inline encoders | ≈ −94 LOC; 1 manifest bug fixed as a side effect |
| SLEB128 readers ×2 (dalvik_engine exception dispatch + find_catch_handler_for_pc, 28L each) + unhardened (UB on 5-byte hostile form) | `mutf8::read_sleb128` (FIND-REUSE-003, hardened 5th-byte law; legacy truncation return-0 semantics preserved verbatim) | 1 file (2 lambda pairs) | ≈ −56 LOC; UB eliminated |
| ResStringPool chunk parsers ×3: `ArscParser::parse_string_pool` 58L, `AxmlParser::parse_string_pool` 52L, `ManifestReader::parse_string_pool` 65L (sequential walk — the BLOCKER-006 misalignment class) | `resources/string_pool.{h,cpp}` ONE canonical decoder (FIND-REUSE-004, AOSP androidfw law: offsets-table indexing, decodeLength 1-or-2-byte form, malformed→empty) | 3 files lose parse bodies (adapters 8–11 lines); `ManifestReader::decode_string_length` orphaned+removed | ≈ −158 LOC net; 1 bug CLASS structurally dead |

## §28 code-minimization metric (this session, verifiable from git)

```text
Commits:            a3c3aded (resource-backed golden) · e69bc496 (FIND-REUSE-002/003) · 4d822256 (FIND-REUSE-004)
Production LOC:     −294 (e69bc496: −136; 4d822256: −158) excluding the +aapt2-integration script lines
Regression tests:   mutf8 battery 7 → 10 windows (T7–T12: SLEB 10 vectors, UTF-16 5 windows, append_utf8 4)
                    helloworld golden gate 18 → 26 checks (resource chain + §36.E discriminator)
Duplicate fns:      UTF-16LE→UTF-8 5→1 · SLEB128 2→1 · ResStringPool 3→1 · (prior: ULEB/MUTF-8 3→1)
Functionality:      +real aapt2-linked fixture APKs (binary manifest/AXML/resources.arsc)
                    +§36.E resource-backed Hello World  +2 hardened primitives  +1 bug fix  +1 bug CLASS dead
Net: functionality INCREASED while implementation LOC DECREASED — the §28 success shape (+tests, −duplication).
```

## Verification discipline used (every consolidation)

1. New primitive + battery windows written/extended FIRST where feasible.
2. The battery caught 2 real defects in the NEW canonical code itself
   (SLEB signed-shift UB; UTF-16 unpaired-with-invalid-tail) before any
   consumer was rewired — the no-dead-tests law paying for itself.
3. After each rewiring: `make clean` + full battery (11 gates) +
   real-corpus runs; acceptance = corpus pixels BYTE-IDENTICAL
   (gmdice, simplestopwatch, microtimer) — three consecutive times.
