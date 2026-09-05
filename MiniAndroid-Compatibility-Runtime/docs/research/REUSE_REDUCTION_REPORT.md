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
