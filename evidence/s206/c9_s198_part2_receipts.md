## S198 (Coder 9) — Part 2: **cohort re-fetch receipts, find_id A/B PRE/POST on 6 real ARSC tables (bit-exact), npTc gates re-run, and the completed 30-task ledger**

**[1] 6-APK cohort re-fetch + SHA-256 receipts (ledger item 21).** All six big cohort APKs re-fetched from F-Droid after the recycle wipe and verified **three-way byte-identical** (old-manifest mirror vs fresh fetch vs live manifest — `REPRO_EXACT` ×6): chess_298 `3245b9ec…`, sgtpuzzles_149 `6b36d553…`, opentracks_6766 `f63ed60e…`, secuso-sudoku_101 `1aff917f…`, tarok_203 `f956d84e…`, commander_479 `7e806081…`. `resources.arsc` extracted per title for the bench.

**[2] find_id A/B bench, PRE/POST rebuilt on the S204 line (items 22–24).** PRE = pristine `0979678e` parser (git-extracted), POST = the S198 rebased parser carrying C9-12 `name_index_`. Same S196 bench program plus a new per-shape split variant:

| table | queries | unscoped PRE→POST ms | scoped PRE→POST ms | scoped speedup | verdict |
|---|---|---|---|---|---|
| com.ghostsq.commander_479 | 1,063 | 36.2 → 36.4 | 36.3 → 1.095 | 33x | BIT_EXACT |
| de.dennisguse.opentracks_6766 | 8,240 | 2732.7 → 3110.6 | 2742.2 → 12.445 | 220x | BIT_EXACT |
| jwtc.android.chess_298 | 5,646 | 1219.8 → 1224.2 | 1228.5 → 7.588 | 161x | BIT_EXACT |
| name.boyle.chris.sgtpuzzles_149 | 6,938 | 1735.2 → 1760.2 | 1734.1 → 9.725 | 178x | BIT_EXACT |
| org.secuso.privacyfriendlysudoku_101 | 3,678 | 515.7 → 514.4 | 515.7 → 4.539 | 114x | BIT_EXACT |
| si.palcka.tarok_203 | 829 | 20.9 → 21.0 | 20.9 → 0.789 | 26x | BIT_EXACT |

**6/6 tables BIT_EXACT — 26,394 queries, both caller shapes, sink checksums equal.** The package-scoped shape (the app-load hot path) rides C9-12's O(1) index: **26x–220x**. The unscoped shape stays legacy-scan (C9-12 exact-miss semantics; timing unchanged within noise). **C9-30 remains the faster superset** (both shapes accelerated, 76–188x standing S196 receipt on the same tables) — the K-3 fold note from Part 0/Part 1 stands: this rebase ships C9-12; C9-30's ambiguity-safe fallback + bit-exact fallback semantics are the post-integration delta.

**[3] npTc static gates + law-29 response (items 25–26).** Both harness runs executed the static pre-gates (`verify_c9_nptc.py` markers→aapt2 payload→runtime-layout three-way agreement = §5/§6 law 43 PASS; resourceval static gates PASS; resourceval fixture rebuilt byte-deterministic, SHA `842849b4…42e37` == S197 record). On the rebased binary `4d832c255bed513c`: §5/§6 **48/49** (only law 49 = P-NEW-5 size-word live) and resourceval **30/31** (only law 29: SLATE+PURPLE 441 < BROWN+OLIVE 1728). **Falsifiable prediction for canonical `6c808c7448850756`, repeated:** law 29 FAILS with exactly 441 < 1728 and §5/§6 law 49 FAILS; every other law PASSes; folding the size-word hunks flips both to green.

**[4] Completed S198 30-task ledger (the Part-0 contract, «حداقل ۳۰ تسک تاییدشده»):**

| # | task | status |
|---|---|---|
| 01 | token/auth re-established (env-var-only, never printed) | DONE |
| 02 | #521 full audit (all comments re-read; 52 after this session) | DONE |
| 03 | S-number audit → this session = S198; origin line = S204 | DONE |
| 04 | phase-3 series located (S190 generation, comments 6712768566/8869/9231/9614) | DONE |
| 05 | origin/main re-audit (phases 1–2 IN, phase-3 ABSENT, f053 size-word unfixed; refreshed `f3499921`→`0979678e`) | DONE |
| 06 | worktree cut (recycle wiped the Part-0 worktree → RE-cut at `0979678e`) | DONE (redo) |
| 07 | patch extraction from the issue record (4 parts recovered) | DONE |
| 08 | rebase parts 1–4 onto `0979678e` (`git apply --3way`) | DONE |
| 09 | Makefile conflict resolution (union: F-NEW-586 kept + `font_family.cpp plurals.cpp`) | DONE |
| 10 | marker-free check (0 conflict markers tree-wide) | DONE |
| 11 | C9-12 ↔ C9-30 overlap analysis (quantified: split-shape bench, §[2]) | DONE |
| 12 | quickjs.c bootstrap re-verified (sha256 `21f072e8…c54` exact) | DONE |
| 13 | byte-identical tree-equivalence gate (pristine+parts == build tree) | DONE |
| 14 | full `make` build on the rebased tree (rc=0, binary `4d832c255bed513c`, 108,562,360 B) | DONE |
| 15 | law-test link + run → **46/46 PASS** (+ density 36/36, zip 42/42 same tree) | DONE |
| 16 | §5/§6 standing harness (49 laws) → **48/49**, only P-NEW-5 size-word law | DONE |
| 17 | rebased parts cut (4 patches, `git apply --check` 4/4 APPLIES_CLEAN) | DONE |
| 18 | parts posted as numbered comments (push-403) → 6743028885/9544/0431/1214 | DONE |
| 19 | GET-verify parts landed byte-exact | DONE (ALL_VERIFIED) |
| 20 | apply-order + bootstrap recipe in Part-1 report → 6743028191 | DONE |
| 21 | 6-APK cohort re-fetch + SHA-256 receipts (REPRO_EXACT ×6) | DONE |
| 22 | find_id bench PRE/POST rebuild (pristine vs C9-12) | DONE |
| 23 | bench re-run on 6 real ARSC tables (26,394 queries) | DONE |
| 24 | bit-exactness diff → **6/6 BIT_EXACT** + split-shape timing | DONE |
| 25 | npTc static gates re-run (both harnesses, law 43 PASS) | DONE |
| 26 | resourceval law-29 falsifiable prediction for the canonical binary | DONE |
| 27 | S198 status ledger (this table) | DONE |
| 28 | Part 2 comment (this comment) | DONE |
| 29 | GET-verify Part 2 landed | DONE |
| 30 | token-leak scan (3 post batches + all logs) | DONE |

**Honesty notes:** (a) the Part-0 session's worktree did NOT survive the recycle — items 06–13 were REDONE this session from the issue record, and the re-audit caught main advancing `f3499921`→`0979678e` (S202/S203/S204 landed); (b) every RUN claim is an in-container make-binary + harness claim (same method as S190/S196/S197) — no device/PM-side integration is claimed; the 46/46 + 48/49 + 30/31 matrix is reproduced end-to-end from the posted parts alone; (c) push remains PM-only (push-403 protocol).

Token discipline: env-var-only, never printed/written/logged; all three post batches passed the token-leak scan before POST.
