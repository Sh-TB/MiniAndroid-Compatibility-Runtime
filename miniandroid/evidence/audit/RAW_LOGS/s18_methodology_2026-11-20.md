# S18 methodology — focused-law expansion + full classification (2026-11-20)

Baseline verified: origin/main = 3f9a3f6c (both S17 commits in ancestry;
tests/s17_focus_laws_test.cpp present; working tree clean apart from the
classification + new tests). Compiler g++ (Debian) 14.2.0; CXXFLAGS
`-std=c++17 -Wall -Wextra -g -O2 -MMD -MP` (+MINIANDROID_HAVE_WEBP); disk
5.6 GB free at session start (the S17 cleanup had freed 3.2 GB); RAM 3 GB.

HONEST-COUNT CORRECTION: S17's commit reported "131 -> 120 remaining" and
"114/234 settled" — that arithmetic double-counted the 11 rows S17 upgraded
(they were already part of S16's 103 machine-marked rows, never in the 131
NO-CITE queue). True pre-S18 state: 103/234 marked, 131 NO-CITE. S18 restores
the 114/234 figure honestly: 11 more rows are now law-verified (below), and
the corrected queue is 120, every row carrying an explicit S18 classification.

## S18-2 — complete classification (all 131 rows, provenance preserved)

Row-level classes written into `source_check` as
`S18-CLASS 2026-11-20: <CATEGORY> — <note> (was NO-CITE)`:

| category | rows |
|---|---|
| TESTABLE-NO-APK | 84 (repo/code census + hand-built-node law candidates) |
| UNVERIFIABLE | 28 (sweep plans S1-S9, port plans R-1..R-5, perf-without-oracle, retracted claims, process suggestions, external-service state) |
| DUPLICATE | 6 (Q1/Q2/Q3/Q5/Q6/Q7 — explicit "see X" cross-refs) |
| NEEDS-EXTERNAL-ORACLE | 5 (M4, N5, NEW-23 locale half, P5, S4) |
| ALREADY-RESOLVED | 4 (E2, E8, H1, NEW-3 — retracted or pinned by existing laws) |
| TESTABLE-WITH-NEW-FIXTURE | 3 (N2, NEW-24, P8) |
| NEEDS-IMAGE-FIXTURE | 1 (N8) |
| NEEDS-MISSING-APK / NEEDS-MISSING-CODER-ARTIFACT / NEEDS-FONT-FIXTURE | 0 (none of the 131 claims actually requires the missing APKs or coder files — not inferred from earlier tests' APK usage) |

## S18-3/4 — five new law families on the real execution path

Expected behavior was fixed BEFORE implementation (methodology §A/§B computed
arithmetically; §C/§F/§G from the documented production laws), except the
three observe-then-pin laws marked (o) below, whose pins were recorded from
the first deterministic run and then held fixed:

1. `tests/s18_dimension_rounding_laws_test.cpp` — family A (#632-M3), 7 laws.
   Entry: the ONE canonical conversion (res_id.cpp
   complex_unit_to_dimension_pixel_size / complex_to_dimension_pixel_size).
   A1 20dp@2.625->53; A2 nonzero floor (0.2/0.1/0.04dp -> 1); A3 negative
   sign-mirror; A4 physical units off xdpi=420 (1in->420, 1mm->17, 1pt->6);
   A5 sp@scaled_density 3.4125 -> 34; A6 typed-word path agrees; A7 zero/1e6.
2. `tests/s18_weightsum_laws_test.cpp` — family B (#632-E2), 4 laws. Entry:
   real inflate_element + measure_layout. B1 weightSum=3 -> 360/360 (200
   unused); B2 weightSum=0 -> derived sum; B3 weightSum=2 with three children
   -> 540/540/0 (AOSP sequential exhaustion); B4 no attr -> derived sum.
3. `tests/s18_text_layout_laws_test.cpp` — family C (#632-N2/N3/N4 + NEW-23
   first-strong), 8 laws. Entry: fonts::layout_text — the single source of
   truth for text geometry. C1 includeFontPadding line_above = |top| vs
   |ascent| (the G47 field law — TextLayout.ascent stays the raw box);
   C2 last-line box >= no-pad; C3 shaped-run == face metrics; C4 spacingAdd
   box law (extra on NON-last lines only); C5 multiplier law; C6 ellipsize
   END truncates an OVER-WIDE last line with U+2026 (the trigger needs an
   unbreakable run wider than max_width — a fitting wrap has nothing to
   truncate; observed 'throu…' @57px <= 60); C7 maxLines caps (1 cap !=
   singleLine); C8 first-strong rtl_base (Arabic true / Latin false).
4. `tests/s18_sql_shadow_laws_test.cpp` — family F (#632-SQL-4/5/6), 6 laws.
   Entry: real DatabaseShadow dispatch (s248 harness shape; fresh-db cleanup
   for determinism). F1.a/b BLOB row live (o); F1.c BLOB column NOT surfaced
   — SQL-4 claim CONFIRMED-LIVE (o); F2 CursorFactory accepted-and-ignored
   (SQL-5, o); F3 WAL set at open does NOT stick — readback journal_mode =
   delete, SQL-6 confirmed STRONGER than claimed (o).
5. `tests/s18_renderer_surface_laws_test.cpp` — family G (#632-O4/O5), 4
   laws. Entry: real FrameBuffer. G1 fresh buffer = every pixel WHITE
   {255,255,255,255} — O4 defect pinned (o); G2 get_pixels_mut raw bypass,
   bit-exact (o); G3 set_pixel is a BLENDING API (opaque source sa=1 stores
   exactly — the first draft's "raw store" expectation was corrected from the
   production law, software_renderer.h:141-165); G4 clear() default WHITE.

Total: 29 new laws in 5 files, all rc=0. Family D (grid margins/stretch)
and E (gravity FILL) remain defined-but-unimplemented (the classification
keeps F3/F4/F5/D5/D6 TESTABLE-NO-APK) — deliberately left for the next
session rather than rushing observe-then-pin families at the end of this one.

## S18-5 — negative-mutation validation (RAW_LOGS/s18_mutation_2026-11-20.log)

| mutation | production site | detected by | result |
|---|---|---|---|
| A: nonzero floor removed | res_id.cpp rounding tail | A2 + A3 | 5/2 FAIL rc=1 |
| B: weight_sum override removed | layout_inflater.cpp:4930 | B1 + B3 (540/540 and 360/360/360 observed) | 2/2 FAIL rc=1 |
| C2: ellipsis glyph -> "?" | text_shaper.cpp:1464 | C6 | 7/1 FAIL rc=1 |
| F: row count under-report | sqlite_shadow.cpp cursor_row_count | F1.b | 5/1 FAIL rc=1 |
| G: init WHITE -> TRANSPARENT | software_renderer.h:122 | G1 + G3 | 2/2 FAIL rc=1 |

All reverted; post-revert runs green (7/4/8/6/4). Two process notes recorded
honestly in the log: (i) the first F injection was placed BEFORE the
assignment and was a no-op (the ineffective attempt stays in the log; the
corrected injection validated); (ii) the first C attempt (include_pad) did
not flip C1 because the law was reading the wrong field (TextLayout.ascent is
unconditional) — the law was FIXED to the documented G47 field (line_above)
and the family's mutation was retargeted to the ellipsis path. A mutation
that cannot fail means the law was testing the wrong field — exactly the
class of harness defect this validation exists to catch.

## S18-6 — regression

- 43-test law battery re-run after the recycle-rebuild: 43/43 PASS rc=0
  (RAW_LOGS/s18_baseline_2026-11-20.log; the sandbox recycle had wiped
  build/ — the rebuild was unavoidable, `make -q` could not reuse).
- Full battery WITH the 5 new families registered: see
  RAW_LOGS/s18_battery_2026-11-20.log (48 law tests).
- Production tree verified clean of all mutation markers
  (`git diff src/ | grep -c MUTATION` = 0).

## Rows upgraded to law-verified by S18 (11)

M3 RESOLVED-IN-TREE (A), E2 ALREADY-RESOLVED+law (B), N2/N3/N4 law-verified
(C), NEW-23 PARTIAL first-strong pinned (C8), SQL-4/SQL-5/SQL-6
CONFIRMED-LIVE (F), O4/O5 CONFIRMED-LIVE (G).
