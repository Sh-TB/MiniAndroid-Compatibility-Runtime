# S15 branch classification evidence (2026-11-20)

## 1. Remote census re-run (corrects AUD-57's "absent" rows)

`git ls-remote --heads origin` (run 2026-11-20, after the S10 census):

```
951ea2bf  refs/heads/audit/m16-litehtml
0f4e43b3  refs/heads/audit/s236
d723a93e  refs/heads/cont24/skeleton-light-experiment
4beacdfa  refs/heads/gh-pages
fca59025  refs/heads/main
671d2577  refs/heads/wave10/dalvik-accel      <- refs/pull/626/head (same SHA)
1e5c8fb9  refs/heads/wave9/dev-so-clean       <- refs/pull/625/head (same SHA)
4f34a77f  refs/heads/wave9/dev-so-integration
```

NO `layout-geometry-001` — RC-12 (AUD-53) re-verified UNRECOVERABLE from the remote.

All four census-"absent" lines fetched into this clone:

| branch | ahead of main | merge-base | classification |
|---|---|---|---|
| wave10/dalvik-accel (PR #626) | 15 | 1e5c8fb9 (wave9 tip) | SUPERSEDED IN FULL — see §2 |
| audit/s236 | 7 | 74eb5efc | SUPERSEDED (evidence-only remainder) — see §3 |
| audit/m16-litehtml | 3 | ba184db9 | reachable flag-gated prototype — see §4 |
| cont24/skeleton-light-experiment | 534 (old fork) | f172e64e | reachable measured experiment — see §4 |

## 2. wave10/dalvik-accel = PR #626: 15 commits, every content piece present in main

Commit list (W11..W20 P2 + FINAL-INTEGRATION + WAVE-10/10.1): W11-APPS (F-NEW-709/710/711),
W12 (712/713/714), W13 (717/718), W14 (719/721/722/723/723b), W15, W16 x2, W17, W18,
P0 split (8e225b25), W19 evidence (8d843248), W20 P2 (671d2577), WAVE-10 (f727991e),
WAVE-10.1 (96cd29e2), FINAL-INTEGRATION (b5799977).

Content checks against main TODAY:

- **F-NEW id matrix** — `grep -rhoE "F-NEW-7[0-9]+[b]?" src/` in main returns ALL of:
  709 x3, 710 x6, 711, 712 x2, 713 x4, 714, 717, 718, 719 x2, 721, 722, 723, 723b.
- **F-NEW-710 by-value fix verbatim in main**: `src/dex/dalvik_engine_invoke.cpp:187-191` —
  `const std::string declaring_class,  // BY VALUE (F-NEW-710): callers may bind this to
  heap_obj->class_descriptor; downstream laws allocate on the heap and a realloc would dangle`.
- **W11-W14 law tests in main**: f709_filedescriptor_law_test.cpp, f714_measurespec_law_test.cpp,
  f716_view_tag_law_test.cpp + the F-NEW rows inside input_pipeline_law_test.cpp.
- **W20 P2 fix 1** (dev-so dep-graph: .d files generated but never included): main Makefile
  lines 817-820 carry the fix with the comment "-include must live BELOW the
  DEV_SO_PIC/DEV_SO_TEST_EXES" — `-include $(DEV_SO_PIC:.o=.d)` + `-include
  $(DEV_SO_TEST_EXES:=.d)` present.
- **W20 P2 fix 2** (adapter_scrap_bin.h <cstdint>): main's
  src/framework/adapter_scrap_bin.h contains cstdint (88-line file).
- **W20 P2 fix 3** (dalvik_engine_tail.cpp unnecessary android_shadows.h include removed):
  main's src/dex/dalvik_engine_tail.cpp has 0 android_shadows.h references (599 lines).
- **P0 architectural split (8e225b25)**: main has its own further-evolved landing — the five
  dalvik_bridge_domain_*.cpp TUs + dalvik_bridge_frame.h compile in every main build (49/49
  battery), refined by W22-C measurements and the W23 header split.
- **WAVE-10 dev-so profiles + FINAL-INTEGRATION doc**: main has the dev-so block (DEV=1,
  DEV_SO_PIC/DEV_SO_LIB rules, build_dev_so tree) — refined by W22-C/W23 (dev cycles
  interpreter 19.4->13.1s etc.) — plus docs/dev-so-architecture.md (93 lines).
- **Zero missing code**: `git diff --stat main...origin/wave10/dalvik-accel -- miniandroid/src/*
  miniandroid/tests/*` — every touched src/tests path EXISTS in main (`git cat-file -e`
  per path; zero MISSING-IN-MAIN). Remaining delta = branch-only scripts/ + evidence/
  corpus artifacts (historical working material; main holds its own richer W22/W23/W24
  evidence set).
- Domain-law spot checks: inflate (6 domain files), getFields/make_field500 (1),
  dispatch_item_click/dispatch_click (1), addAll (2), createBitmap (4), extras family
  (ui_graphics/android_core domains).

**Verdict: PR #626 needs NO rebase and NO cherry-pick — every code/law/fix piece it carries
is already in main (integrated directly in W22-W24 sessions with measurements). Rebasing the
15-commit line onto main would resurrect duplicate implementations and conflict with main's
further-evolved P0/header-split architecture. Disposition: SUPERSEDED-IN-FULL (documented
closure; branch stays on the remote as the coder's original history).**

## 3. audit/s236 (7 commits): SUPERSEDED, evidence remainder

- tests/s236_port_laws_test.cpp EXISTS in main AND is registered in Makefile TEST_LAW
  (line 531, between s235_lane_laws_test and s237_append_bounded_law_test).
- The law markers (0xFFFFFFFF/GETXML-NOTFOUND/composed-CREATE families) are present in
  dalvik_bridge_domain_android_core / app_runtime / io_lang.
- Branch remainder = raw audit evidence (deep-verify harness, rerun logs, #596 phase-1
  evidence) — historical; the selectively-merged laws it backs are already gated by the
  in-main test (14 record/expect rows in the branch copy).

## 4. audit/m16-litehtml + cont24/skeleton-light-experiment: reachable experiments

- m16-litehtml: the OPTIONAL render path behind a MINIANDROID_ flag + third_party/litehtml
  (191 files, ~71K lines). Intentionally branch-only — never adopted in main's default
  graph; reachability restored (S10 census said absent).
- cont24/skeleton-light-experiment: old fork (534 commits ahead, base f172e64e) carrying the
  measured branch-only experiment. Reachability restored; disposition unchanged.
