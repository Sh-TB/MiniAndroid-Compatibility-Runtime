## S198 (Coder 9) — Part 1: **the phase-3 stack is rebased on CURRENT main `0979678e` (S202/S203/S204 line), self-verified in-container, and re-delivered as the four numbered parts below**

**Directives served:** your S200 feedback (comment 6728863894, item 1) + the ONE-BY-ONE TEST CYCLE (comment 6732820375, T29) + the «حداقل ۳۰ تسک تاییدشده» standing directive. The S198 Part-0 30-task checklist (comment 6732257444) is completed by this and the follow-up comment.

**Rebuild ledger (honest):** the previous session's `coder9/s198-phase3` worktree did NOT survive the container recycle — the rebase was REDONE this session from the issue record. Origin re-audited: main advanced again `f3499921` → `0979678e` (S202/S203/S204 landed, incl. F-NEW-626 shadow/buffer family and F-NEW-630). The four S190-generation parts were recovered from comments 6712768566 / 6712768869 / 6712769231 / 6712769614 and applied `--3way` onto `0979678e`. Conflict surface: exactly ONE hunk — the Makefile, resolved as the UNION (keep F-NEW-586 `gl_copy_bridge.cpp` AND add `font_family.cpp plurals.cpp` to `RESOURCES_SOURCES`). Zero conflict markers tree-wide. All other hunks applied clean on the S204 line.

**In-container proof on the rebased binary `4d832c255bed513c` (108,562,360 B, `make -j2 all` rc=0, 0 errors, full build of every TU incl. the two new resources TUs):**

| gate | result |
|---|---|
| `tests/c9_phase3_laws_test.cpp` (new in part 4) | **46/46 PASS** (rc=0) |
| `c9_bitmap_density_law_test` (phase 1, already on main) | 36/36 PASS |
| `c9_zip_data_offset_law_test` (phase 2, already on main) | 42/42 PASS |
| §5/§6 standing harness (49 laws) | **48/49 PASS — ONLY law 49 (npTc size-word live) fails** |
| resourceval harness (31 laws, fixture SHA `842849b4…42e37` == S197 record, byte-deterministic) | **30/31 PASS — ONLY law 29 (MULTI-stretch, SLATE+PURPLE 441 < BROWN+OLIVE 1728) fails** |

The single failing law in both harnesses is the SAME dimension: the npTc **size-word acceptance**. So the rebased stack is behaviorally EXACTLY the S197 item-D statement: everything green except the f053 size-word gap. **Falsifiable prediction for your canonical binary `6c808c7448850756` (f053, no size-word hunks): resourceval law 29 FAILS with exactly SLATE+PURPLE 441 < BROWN+OLIVE 1728 and §5/§6 law 49 FAILS; all other laws PASS. Folding the size-word hunks flips both to green** — same discriminator S197 recorded on `d90fa3b8` (PRE 30/31).

**Pre-post gate (done before this comment):** pristine `0979678e` worktree → `git apply --check` per part → 4/4 APPLIES_CLEAN; applying all four reproduces the verified tree **byte-identically** (src tree, Makefile, law test all `diff`-clean against the build tree).

**Bootstrap (unchanged since S190 §5, re-verified this session):** `miniandroid/third_party/quickjs/quickjs.c` fetch-if-missing from `https://bellard.org/quickjs/quickjs-2024-01-13.tar.xz`, extracted-file sha256 `21f072e8b24ee115562ff961bafd4b0464d7a30828c43b1884f4828c24370c54`. Recipe: apply parts 1→4 on `0979678e` → fetch-if-missing quickjs.c → `cd miniandroid && make -j2 all` → link per S190 §6 → `./build/c9_phase3_laws_test` → 46/46.

**C9-12 ↔ C9-30 integration note (stands from Part 0):** this rebase ships C9-12 `name_index_` (parse-time O(1) name→id, first-document-order-wins, exact-miss). C9-30's remaining delta over C9-12 = ambiguity-safe fallback semantics + the 6-table bit-exact A/B receipt — your call at K-3; the 46/46 law test pins C9-12's semantics either way.

Parts 1/4 … 4/4 follow as separate comments (push-403 protocol, appliable order 1→4). Apply report welcome: we expect 46/46 on your side.
