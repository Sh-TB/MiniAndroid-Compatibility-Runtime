# W21 RUNTIME TRACE SUMMARY — how the 15x5 baseline decomposes

## Startup constant (the shared-runtime floor)
- W21 floor: HelloWorldToast 4.55/4.58s (CPU 4.21s), randomix 4.42s, notepad 4.71s,
  minos/blockinger/ugalay 4.76-4.77s — down from the W20-K2 5.7-6.4s band (delta
  attributed to machine state, not code; non-webview TUs byte-identical).
- CPU/wall ~= 0.92-1.0 for EVERY app = fully CPU-bound single-thread execution.
- No per-stage timer lines are printed by the binary in normal runs; the gprof
  profile decomposes the startup window (see W21_RUNTIME_HOTSPOT_REPORT.md).

## Cold vs warm
- Cold and warm medians differ by <10% for 13/15 APKs (fresh data-root per APK;
  warm reps share it). notepad cold 7.52 vs warm ~4.6 (first-write cost);
  randomix shows the cold=31ddd4d5 / warm=b5a7a35d two-face pattern (identical in
  W20-K2's TSV — not a regression; recorded in W21_RUNTIME_BASELINE.md).

## Outliers / honest failures preserved
- chess: rc=124 at the 60s outer cap in all 5 reps (CPU 59.7s = CPU-bound at cap;
  peak RSS 888MB — the only app exceeding 512MB besides tallybook 508MB).
- rc=1 apps: the 7 known in-app-exception APKs (janken, itsfrz ttt, authsrng, minos,
  chess, tallybook, gaskell dicer) — same first-divergence class as the W20 census;
  screenshots still deterministic per APK.
- blank_ratio column: 1.0 = solid default face (crash faces), 0.76-0.99 = real content.

## Determinism
- Every APK's screenshot sha16 is stable across its 5 reps (see baseline CSV).

## Method
- scripts/w21_runtime_perf.sh + scripts/w21_runner.py (per-fresh-process
  getrusage(RUSAGE_CHILDREN) — wall + CPU user/sys + peak RSS, fields W20-K2 could
  not capture because /usr/bin/time is absent on this host).
