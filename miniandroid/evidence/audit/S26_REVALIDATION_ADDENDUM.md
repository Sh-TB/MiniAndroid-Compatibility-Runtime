# S26 REVALIDATION ADDENDUM — the clean-rebuild authoritative record — 2026-11-22

**Base: S25 `f2823280` (== origin/main). This addendum supersedes the S25 report's final measurement round where they disagree: the S25 round ran on build9, an incremental link that the post-session recycle exposed as inconsistent (a fresh clean `make -j2 all` from the identical committed sources produces different randomix behavior). The clean rebuild is the authority; every number below is from it (log: `evidence/s26/bootstrap_build.log`, rc=0).**

## 1. What the clean rebuild REVALIDATES (S25 laws hold)

- **flip_a_coin ×3**: `[S25-W1-BIND-ADOPT]` ×1/run, `ActivityMainBindingImpl.setPresenter` ×1/run, `EXP060-LISTENER` (the app's generated OnClickListener on view 594) ×1/run, honest `IMAGE-BLOCKED: VectorDrawable` ×1/run; face `b270ff04` ×3, DEFAULT_BACKGROUND_ONLY. The S25-W1a/W1b/W1c/W1d chain is stable on the clean binary.
- **minos ×3**: EventBusException **0** ×3 + `METHOD_CACHE` registration put ×3 — S25-W2 holds.
- **Anchors**: HelloWorldToast `acdd9f05` ✓, chess `d602648e` ✓ byte-identical.
- **Six-pin (last-frame hash)**: guess `87fe2676…` ✓, np `31ddd4d5…` ✓, dice `0de952bf…` ✓, ttt `d55056a8…` ✓ — identical to the W23 canonicals; pz last-frame `6375a3a3813af176` — IDENTICAL to the S25-final-binary value, and the S24-tip worktree attribution (recorded in the S25 report, commit `e4994502`) already proved the pz delta predates S25 (S25 == S24 on pz).

## 2. What the clean rebuild CORRECTS (supersedes S25's record)

- **randomix is RUN-TO-RUN NONDETERMINISTIC at its init layer** — the S25 report's "b5a7a35d ×3 deterministic + named vk.a cause" record is **SUPERSEDED**: on the same clean `f2823280` binary, randomix_r0 reached the shared blank face (`31ddd4d5`, 2 unique hashes) while randomix_r1/r2 + anchor stayed at the boot face (`b5a7a35d`, 1 hash) — SAME binary, different outcomes. The vk.a fragment-container NPE seen on build9 did not reproduce at all on the clean binary (0 occurrences in 4 runs). New finding + next law: **the run-to-run nondeterminism itself** (a thread/scheduling or oid-ordering dependence in randomix's init chain — the engine's determinism contract is violated on this app) — to be root-caused before any fragment-container work.
- The build9 binary behind the S25 report's final round was an inconsistent incremental link (post-recycle object mixing during the session); its randomix-only divergence is hereby explained and withdrawn. flip/minos/anchors/six-pin values from that round are UNCHANGED by the clean rebuild (verified above row-by-row).

## 3. Evidence

`evidence/s26/`: bootstrap_build.log, randomix_r0/r1/r2 + anchor dirs, flip_r1..r3, minos_r1..r3, gate_pz/guess/np/dice/ttt, `s26_revalidation_matrix.tsv` (17 rows). Matrix also mirrored at `/home/z/my-project/download/`.

**Status vocabulary**: REVALIDATED (flip ×3, minos ×3, anchors, six-pin) / SUPERSEDED (S25's randomix deterministic-b5a7a35d record) / NEW-FINDING (randomix run-to-run nondeterminism on the clean binary — next root-cause target) / UNCHANGED (all other S24/S25 records).
