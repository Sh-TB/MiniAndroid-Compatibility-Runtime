**S18 addendum correction — one claim in [comment 7051278937](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/635#issuecomment-7051278937) was wrong, fixed with evidence**

**The wrong claim.** That comment said the battery was "re-run green post-reset". That was a verification error on my side: the result line was read from a `grep` whose matches came from the **pre-reset** 48/48 summaries, not from the post-reset section of the log. The actual post-reset battery was:

- **BATTERY SUMMARY total=48 passed=47 failed=1, rc=2** — the sole failure being `s254_version_identity_law_test` (the L3.1 law: generated-header commit == `git rev-parse HEAD` at run time).

**What happened next.** The next sandbox recycle wiped `build/` before the failing record (`build/tests/s254_version_identity_law_test.log`) could be inspected, so the precise mismatch mechanism is **not claimed** — the candidates (stale generated header disagreeing with the HEAD move at the reset, vs the header recipe not re-running under `make -q` reuse) are recorded as candidates only, in the log.

**The resolution, verified.** The version-header rule carries `FORCE` (`Makefile:338`), so every full make invocation regenerates the header at the current HEAD. A full post-recycle rebuild + battery at HEAD `9b135f3a` regenerated `MINIANDROID_COMMIT=9b135f3a0f37…` (== git HEAD) and produced **BATTERY SUMMARY total=48 passed=48 failed=0, rc=0** — including `[PASS] s254_version_identity_law_test`, plus a direct run ending in "VERSION IDENTITY DOMAIN CLOSED".

**The honest reading.** The identity law did exactly its job: it caught an identity state that was out of sync with the repository HEAD, and refused to call it good. The log (`RAW_LOGS/s18_freshrun_2026-11-20.log`, commit `a88101e7`) now keeps the complete, unedited battery history: 48/48, 48/48 (pre-reset), **47/48 (post-reset failure kept)**, 48/48 (post-recycle, resolved) — with a diagnosis note explaining the misread. No other claims in the S18 evidence comments are affected: the classification, ledger, law families, and mutation records stand as posted.
