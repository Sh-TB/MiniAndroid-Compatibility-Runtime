## CONT-11 WAVE 7 — PROBLEM SOLVED: the batch-20 crash family (F-NEW-509, re-verified on the merged CONT-159 lineage)

Follow-up to [my earlier comment](https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/380#issuecomment-6346086651): the wave was rebased onto the parallel CONT-156..159 lineage and everything re-verified at the merged HEAD.

### Corrections from the rebase

1. **ID collision resolved**: the remote registry already had `F-NEW-261` (CONT-45's S83-APXACT activity-bypass law — a stale-snapshot rebase of an earlier local wave). The prefs-ancestry root is now registered as **`F-NEW-509`** (`ROOT-CAUSED-FIXED`, registry 822 → 823, ids unique).
2. **Lineage proof**: the merged tree WITHOUT my fix builds to `2acd3a23e7064f2c` — byte-identical to the recorded CONT-159 binary. WITH the fix: `55c5e06b1e0a3997`.

### The solved problem (unchanged by the rebase)

`bridge_to_api`'s Context-family guard (P0.12 `getSharedPreferences`/`getPreferences`) matched receivers by **runtime-class name substring**; real APK hierarchies (R8'd support-v7/v4 chains) missed it → NULL prefs → 145 uncaught exceptions across 10 of the 20 batch APKs. **Fix**: bounded 16-hop DEX-chain ancestry walk (the F-NEW-259 slot-resolution law). **A/B: all 10 crash-family APKs → 0 uncaught.**

### Re-verification at the merged binary `55c5e06b1e0a3997`

| Gate | Result |
|---|---|
| Batch-20 uncaught | **20/20 = 0** (composes cleanly with remote F-NEW-494..507) |
| Batch-20 content | 6 REAL_APP_CONTENT — fishrings `a341e3ad` / tripeaks `e2a290ab` exactly the recorded CONT-158 crossing anchors; bouncy/opmt/smt_calc/quelltext_mem real |
| secuso_memory REAL→PARTIAL | **A/B-ATTRIBUTED to the remote lineage** (identical PARTIAL frame `6da289aa` on both arms) — not an F-NEW-509 interaction; next-wave root-cause |
| Anchors ×3 | chess `a0319686` / dooz `31ddd4d5` / unote `7481e9b4` / tower3d `11a38a5a` — exactly the remote re-based faces; opencalc/microtimer deterministic ×3 on both arms |
| Gate A / negatives / skill | **98/0/1 · 19/19 · 13/13** |
| F261 probe | **5/5 PASS** (110 PASS / 0 FAIL across frames) + F259 probe A..G all PASS |

### Honest frontier (next wave owns)

13/20 still `DEFAULT_BACKGROUND_ONLY` — zero exceptions, content-attach faces: compose_stopwatch (Compose 1.11.3, independent consumer for the §6 AndroidCanvas bridge), andstatus2048 (Kotlin model-init), tananaev (fragment/Prefs), tictactoe_em/stacktower (F-NEW-498 libGDX native family), plus the secuso PARTIAL attribution. §9's reuse decision matrix stays open.

Pushed: `980dabd2..4f0149cb`. Evidence: `evidence/cont11/{batch20_ledger.json, regression_summary.json, regression_summary_rebased.json}`.
