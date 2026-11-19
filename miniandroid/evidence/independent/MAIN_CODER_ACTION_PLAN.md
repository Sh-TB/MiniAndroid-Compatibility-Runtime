# MAIN CODER ACTION PLAN (W20-K2)

## Immediate (next session, ordered)
1. **Reproduce the SolitaireCG + Frozen Bubble live re-runs** on current HEAD
   (patches are IN source; the APKs are not in the local corpus — attach
   them). Evidence class upgrades PATCHED -> TESTED.
2. **E-03 audit** (const-string/jumbo signed-shift index): one-line source
   audit + fix if needed + a jumbo-index contract test (low risk).
3. **E-01 focused test** (move/from16 + move-wide/from16 register-edge
   contract test) — the handlers exist; the historical edge law was never
   re-proven on this lineage.
4. **G-01 recovery**: re-read #627 with API access; the definition was not
   surfaced by the HTML fetch.
5. **Runtime perf phase 2**: with the Phase-1 baseline (this wave), instrument
   the three ranked hotspots (method-resolution scan order, BitmapStore
   re-decode, full-frame state-list re-pick) and land the highest measured
   one behind its focused benchmark.

## Standing decisions (do not reopen without new evidence)
- FANOUT-EXP stays REJECTED (coder retraction).
- GGC claims stay REJECTED until a valid matrix exists.
- W19 125s figure stays INVALID (use 401.8s).
- D-01/D-02/D-03 stay DEFER (portability offers for old toolchains only).
- WS2.02 splash stays by-design (never a failure).

## Registry audit note (Part 8)
The 35 zero-comment issues were cross-referenced in previous waves; the
identity mapping was corrected to package-name-canonical in the census
(evidence/w20/corpus_census.md). This session added no new per-issue rows
(step budget went to the knowledge recovery + baseline); the audit CSV rows
reference the registry identities where applicable. Remaining work is the
per-issue checkpoint sweep — DEFERRED with reason, not silently dropped.

## Phase-1 baseline ADDENDUM (measured this session)
The 15-APK bounded-run baseline is DONE (RUNTIME_PERFORMANCE_BASELINE.md):
chess 60.03s (cap), tallybook 17.2s, ~5.7-9.9s band for the rest, cold==warm
within noise, per-APK determinism shas stable. Phase-2 = instrument the
startup constant + chess/tallybook, then land the top measured hotspot.
