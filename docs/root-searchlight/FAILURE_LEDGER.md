# FAILURE LEDGER (append-only — failures are evidence, §14/§30 speed-addendum)

| # | Failure / False lead | First seen | Root/cluster | Evidence | Verdict | Fix | Status |
|---|---|---|---|---|---|---|---|
| L-01 | "SnapshotKt readError sequencing is the dooz frontier" (forensic report claim) | pre-M4 | Compose cluster | live trace: readError site no longer throws after F-028/F-030 | **FALSE_LEAD (stale claim)** | n/a — eliminated upstream | REJECTED_CLAIM recorded in ROOT_LAW_GLOBAL_AUDIT |
| L-02 | "Implement Compose Snapshot v0 micro-proof next" (report recommendation) | pre-M6 | Compose cluster | F-044 proved the real root was per-frame return-descriptor corruption | **FALSE_LEAD (as stated)**; snapshot knowledge retained as radar | F-044 (774d6cdd) | RESOLVED-BY-OTHER-ROOT |
| L-03 | M5 "insert never commits" spin (dooz scatter-map) | M5 | Collections/DEX cluster | M6 F-040 + M9 F-056 proved the SAME hole from two sides (missing Arrays.fill EMPTY-tag law) | DUPLICATED DISCOVERY (divergent lines) | F-040 kept (superset); F-056 handler deduped at merge 0383f19f with traceability note | RETIRED |
| L-04 | Frame-clock hypothesis as THE blank-frame root (withFrameNanos) | M9 | Compose cluster | withFrameNanos never reached at the symptom layer; real chain was upstream (lifecycle/composition) | **FALSE_LEAD at symptom layer**; frame-pump family still real (F-050) | F-050 pump roots fixed (ad4349a9) | PARTIALLY RETIRED — pump fixed, first frame still pending |
| L-05 | battery gate "88/88 vs 91/91 mystery" | M9 Phase-0 | tooling | battery grew per campaign (88 stages at M7 → 91 with F-050 stages); no gate anomaly | FALSE_ALARM | n/a | RESOLVED (counts explained) |
| L-06 | dooz "SUCCESS" reports from generator gossip (screenshot byte-identical to blank baseline) | M4 | evidence discipline | pixel forensics: 0 non-white despite report status | EVIDENCE-GAP (tool-output ≠ root-proof) | pixel-count law + screenshot metrics mandated | LAW ENFORCED |

## Live observed failures (current frontier evidence)

| # | Symptom | Root | Evidence |
|---|---|---|---|
| F-01 | dooz ComposeView children=0, framebuffer 0/2073600 non-white | R-NEW-246/259/279/285 cluster | run/m9_merge_dooz at 0383f19f (rc=0, no exceptions, lifecycle RESUMED) |
| F-02 | Window.setDecorFitsSystemWindows REC-MISS | R-NEW-286 | same run log |
| F-03 | tictactoe real APK (libGDX) T3/BLANK | R-NEW-075 surface boundary | G09 record; honest UNVERIFIED-BY-DESIGN |

## S21 failures & tool drift (evidence-first, never re-mixed)
- **PROBE-DRIFT (latent, fixed)**: s19/s20 DEX probe lineage carried a wrong
  opcode-size table (const/4 0x12, monitor-enter/exit 0x1d/0x1e, array-length
  0x21, throw 0x27 decoded as 2 units; filled-new-array 0x24/0x25 and
  fill-array-data 0x26 as 2 instead of 3) — any method containing these
  decoded with SHIFTED linear pcs after the opcode, and 21t/22t branch
  targets read from the wrong unit. F-070..F-073 conclusions were proven by
  runtime register traces and androguard cross-checks, so they stand; the
  scripts/forensic/s21_frame_probe.py replaces the lineage with a spec-exact table (all
  structural findings re-verified against the androguard oracle).
- **GATE H + EXT-01/EXT-02 environmental (container reset)**: GATE H
  (simplestopwatch settings glyph white=0) reproduces identically with the
  S21 fix stashed (stash-bisect run recorded in /tmp/gateh_pre.log); EXT-01/
  EXT-02 require /home/z/corpus/external_hello/* which the container reset
  wiped. Not S21 regressions. Restore path: re-provision /home/z/corpus.
- **FALSE LEAD retired**: "callback removed-not-run" — the J$c.run
  removeFrameCallback branch is upstream-LEGAL (toRunOnFrame empty cleanup,
  AndroidUiDispatcher.android.kt lines 58-66); the real break was upstream
  (F-074 silent drop), and the second break (F-075) was upstream of that.
