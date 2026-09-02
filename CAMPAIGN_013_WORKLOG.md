# CAMPAIGN_013_WORKLOG — chronological

## Baseline (00:26–00:40)
- Environment restored from SHA-verified v0.11.3 handoff ZIP (f5da664/v0.12.0
  NOT FOUND locally — recorded as baseline discrepancy, treated as unverified
  hypothesis per the evidence standard).
- branch campaign-013 + tag v0.13.0-baseline @ ea81e00.
- rlottie rebuilt from source; runtime built; fixtures 8/8 + 5/5 from clean
  extract.
- Corpus re-assembled: 12 registry APKs re-downloaded + SHA-verified (2 drifts
  documented), tinymusicplayer v4 + bouncy + droidify added, Telegram v12
  re-downloaded byte-identical (f5e11927) from telegram.org/dl/android/apk.
- triage_013.py pipeline built (16-class taxonomy, click probe, evidence-only
  classification).

## Finding: dialogs are the shared 0-px root cause (00:45)
- gmdice click trace: real callback → AlertDialog.Builder → show() → all
  bridged invisible. B1 confirmed live at baseline.

## FIX-013-01 dialog object model (00:50–01:05)
- DialogShadow/ArrayAdapterShadow + ViewNode dialog routing + window painter.
- gmdice: dialog visible 1.74M px, second dialog chained, 4/4 interactions.
- Goldens green. Commit a5f7995.

## Finding: chessclock class never reaches ActivityShadow (01:05)
- handles_class name-list antipattern → hierarchy dispatch (FIX-013-02).
- Inflation rejection guard inverted + screen-gated placeholders (FIX-013-03);
  first per-node placeholder version BROKE the simplestopwatch golden —
  caught by the gate, redesigned as screen-level, golden restored EXACT.
- Commit cb621fc.

## Finding: obfuscated ARSC values ARE the paths (01:20)
- c013_arsc_probe: layout/main → value "res/w6.xml"; name never a file.
- FIX-013-04 value-first resolution → notesbill/bouncy/unote unlock.
- Commit b9d93cc + tag v0.11.4-fix-01.

## Finding: onDraw never executed (01:35)
- CanvasShadow record/replay + dispatch_custom_view_draw; descriptor
  normalization + main.cpp registry registration were the debugging gates.
- bouncy ScoreView real pixels; ssw BigTextView ops=0 graceful (golden EXACT).
- Commit cd0463f.

## Final matrix + docs (01:50)
- Baseline vs AFTER triage recomputed; 6 apps moved up; goldens green.
- Deliverable docs written; evidence curated under docs/evidence/u013/.

## Stop-condition check (§29)
Remaining high-leverage blockers (OB-1 Compose, OB-2 appcompat chains, OB-3
GLES) are each multi-day architectural efforts; per §29 they are precisely
instrumented with minimal reproducers + next boundaries documented in
TOP_BLOCKERS_013.md / COMPOSE_REPORT_013.md / GLES_REPORT_013.md. Budget
exhausted; checkpoint + handoff per §28.
