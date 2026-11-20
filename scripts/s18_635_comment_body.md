**S18 — #632 classification + focused-law expansion (AUD-54 phase 2 cont.): 131/131 claims classified, 5 new law families / 29 laws all green, per-family negative-mutation validated, full law battery 48/48 rc=0; S17's queue arithmetic corrected (honest 114/234)**

**Exact commits:** main `ed7df15f` (S18 work) + `3c6007b7` (housekeeping), pushed on top of S17's `3f9a3f6c`. Ledger: 65 rows (AUD-59 added), validator OVERALL: PASS.

**1. Baseline integrity (S18-1).** origin/main verified at `3f9a3f6c`; both S17 commits in ancestry; `tests/s17_focus_laws_test.cpp` in main. Compiler g++ 14.2.0, CXXFLAGS `-std=c++17 -Wall -Wextra -g -O2 -MMD -MP` (+WEBP). Honest finding: the sandbox recycle had **wiped `build/`** — `make -q` could NOT reuse (incremental reuse impossible; full rebuild recorded), after which the 43-test battery and the 14 S17 laws re-ran green. Disk 5.6 GB free; no committed evidence deleted (AUD-51 tree untouched).

**2. Classification (S18-2) — all 120 reported remaining claims, corrected.** First, an arithmetic correction: S17's "131 → 120 remaining / 114/234 settled" **double-counted the 11 rows it upgraded** (they were already inside S16's 103 machine-marked rows). True pre-S18 state: **103/234 marked, 131 NO-CITE**. Every one of the 131 rows now carries an explicit `S18-CLASS` verdict in `632_FINDINGS.csv` (ID + provenance preserved):

| category | rows |
|---|---|
| TESTABLE-NO-APK | 84 |
| UNVERIFIABLE | 28 (sweep plans S1–S9, port plans R-1..R-5, perf-without-oracle, retracted, process suggestions, external-service state) |
| DUPLICATE | 6 (Q1/Q2/Q3/Q5/Q6/Q7 — explicit "see X") |
| NEEDS-EXTERNAL-ORACLE | 5 (M4, N5, NEW-23 locale half, P5, S4) |
| ALREADY-RESOLVED | 4 (E2, E8, H1, NEW-3) |
| TESTABLE-WITH-NEW-FIXTURE | 3 (N2/NEW-24 font, P8 mini-DEX) |
| NEEDS-IMAGE-FIXTURE | 1 (N8) |
| NEEDS-MISSING-APK / CODER-ARTIFACT / FONT-FIXTURE | **0** — no claim actually requires the missing APKs or coder files |

**3. New laws (S18-3/4) — 5 families, 29 laws, all rc=0**, each on the real execution path (no private copies), expectations fixed BEFORE implementation (pre-computed arithmetically or from the documented production law; 3 observe-then-pin laws marked):

- **A** [s18_dimension_rounding_laws_test.cpp](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/blob/main/miniandroid/tests/s18_dimension_rounding_laws_test.cpp) 7/7 — M3 rounding tail + nonzero floor (0.1dp→1, −0.1dp→−1), physical units off xdpi=420 (1in→420, 1mm→17, 1pt→6), typed-word path agreement.
- **B** [s18_weightsum_laws_test.cpp](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/blob/main/miniandroid/tests/s18_weightsum_laws_test.cpp) 4/4 — weightSum=3 → 360/360 (**settles E2 both ways: weightSum IS read**), weightSum=0 → derived-sum fallback, weightSum=2 with 3 children → 540/540/0 (AOSP sequential exhaustion).
- **C** [s18_text_layout_laws_test.cpp](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/blob/main/miniandroid/tests/s18_text_layout_laws_test.cpp) 8/8 — G47 field law (`line_above`=|top| vs |ascent|), spacing add/multiplier box laws, **ellipsize END truncates an over-wide last line with U+2026** ("throu…" 57≤60px; a fitting wrap has nothing to truncate), maxLines ≠ singleLine, first-strong rtl_base (NEW-23 partial).
- **F** [s18_sql_shadow_laws_test.cpp](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/blob/main/miniandroid/tests/s18_sql_shadow_laws_test.cpp) 6/6 — REAL DatabaseShadow path: **BLOB column NOT surfaced** (SQL-4 CONFIRMED-LIVE), CursorFactory accepted-and-ignored (SQL-5), **WAL set at open does not stick — readback `journal_mode=delete`** (SQL-6 confirmed *stronger* than claimed).
- **G** [s18_renderer_surface_laws_test.cpp](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/blob/main/miniandroid/tests/s18_renderer_surface_laws_test.cpp) 4/4 — **fresh framebuffer = every pixel WHITE {255,255,255,255}** (O4 defect pinned), get_pixels_mut bit-exact bypass (O5), set_pixel blend law.

Families D (grid margins/stretch) and E (gravity FILL) remain **defined-not-implemented** — deliberately deferred rather than rushed at session end; the classification keeps their rows TESTABLE-NO-APK.

**4. Mutation validation (S18-5)** — one controlled production mutation per family, exact failures recorded in [s18_mutation_2026-11-20.log](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/blob/main/miniandroid/evidence/audit/RAW_LOGS/s18_mutation_2026-11-20.log):

| mutation | detected by | result |
|---|---|---|
| A: nonzero floor removed | A2+A3 | 5/2 FAIL rc=1 |
| B: weight_sum override removed | B1+B3 (540/540, 360/360/360 observed) | 2/2 FAIL rc=1 |
| C2: ellipsis glyph → "?" | C6 | 7/1 FAIL rc=1 |
| F: row-count under-report | F1.b | 5/1 FAIL rc=1 |
| G: init WHITE→TRANSPARENT | G1+G3 | 2/2 FAIL rc=1 |

All reverted; post-revert 7/4/8/6/4 green; `git diff src/ | grep -c MUTATION` = 0. Two process notes kept honestly: the first F injection was a **no-op** (placed before the assignment — visible in the log); the first C attempt proved the law tested the **wrong field** and the law was FIXED to the documented G47 field before its mutation was retargeted — precisely the harness-defect class this validation exists to catch.

**5. Regression (S18-6).** Full law battery with the 5 families registered (Makefile TEST_LAW +5): **BATTERY SUMMARY total=48 passed=48 failed=0, rc=0** ([s18_battery_2026-11-20.log](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/blob/main/miniandroid/evidence/audit/RAW_LOGS/s18_battery_2026-11-20.log)).

**6. Deliverables (S18-7).** MASTER_AUDIT §1 item 16 + the S17-correction note; §4 114/234 honest; NEXT_INTEGRATION_PLAN item 8 updated; BLOCKED_AND_PENDING AUD-54 row; ACHIEVEMENT_LEDGER +AUD-59; LEDGER_VALIDATION_REPORT OVERALL: PASS; 11 rows upgraded `S18-LAW` (M3, E2, N2, N3, N4, NEW-23, SQL-4, SQL-5, SQL-6, O4, O5); methodology doc [s18_methodology_2026-11-20.md](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/blob/main/miniandroid/evidence/audit/RAW_LOGS/s18_methodology_2026-11-20.md); regen verified idempotent apart from the self-referential session-HEAD line (documented convention).

**Remaining (not blockers of S18):** 120 classified rows (84 TESTABLE-NO-APK — next: D/E families + the census batch); AUD-10b/42; coder-local artifacts (#634 MG-012, #295/#296/#297, RC-12, #630/#631); PR #626 close decision (owner). AUD-54 stays open by definition — S18 neither claims nor closes it.
