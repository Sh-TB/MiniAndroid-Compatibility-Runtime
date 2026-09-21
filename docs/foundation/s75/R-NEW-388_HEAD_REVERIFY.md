# R-NEW-388 RE-VERIFICATION AT HEAD — S75 CLOSURE WAVE

Generated: 2026-09-21 · HEAD: c67230be · Engine: rebuilt from HEAD (82.8 MB, make -j2 clean)

## Why this exists

The S75 closure audit (docs/audit/ITEM75_CLOSURE.md) reconciled ledger rows
ITEM75-023/024 (census C1/C2) as PARTIAL with the residual attributed to
R-NEW-388 ("measure-before-render law at render entry"). Before implementing
any render-entry change, this wave re-verified the R-NEW-388 registry record
("ROOT-CAUSED-REMEASURED-GENERIC-OK", S71 re-measure) against the CURRENT
binary at HEAD, because the registry record also stated the S66 wiring-gap
claim was STALE for HEAD.

Per constitution #6/#7/#8 (never invent semantics; unknown stays unknown;
hypothesis is not root cause): a render-entry implementation against a stale
or already-fixed claim would be an unfounded fix. The wave therefore PROBES
instead of implementing.

## Probe 1 — generic half: f14_relative at HEAD

Run: `docs/evidence/s75/rnew388_f14/` (engine.log, view_tree.json,
screenshot.png). rc=0.

Result: RL anchor geometry EXACT match to the S71 re-measure record:

| child                     | observed            | AOSP law expectation |
|---------------------------|---------------------|----------------------|
| alignParentRight (300px)  | x=780               | 1080-300 = 780       |
| below/margin chain        | y=300               | parent top + margin  |
| centerInParent (400x400)  | (340, 760)          | (1080-400)/2, (1920-400)/2 |
| (0,0) collapse            | ABSENT              | —                    |

GENERIC LAWS HOLD at HEAD. No measure-before-render implementation is
warranted by evidence.

## Probe 2 — app half: TriPeaks real APK at HEAD

Run: `docs/evidence/s75/rnew388_tripeaks/` (engine.log, view_tree.json,
screenshot.png). rc=0.

Result: ViewTree = splash only — RelativeLayout(1080x1920) + WebView(full) +
SplashActivity$1 handler node; screenshot nonwhite=0 (fresh run, no tap
input; WebView splash face). GameActivity/card geometry is UNREACHED via
fresh canonical runs — the app-specific SplashActivity navigation chain
remains the blocker, exactly as the registry record states.

## Verdict

- R-NEW-388 registry record CONFIRMED at HEAD (both halves).
- C1/C2 residual is APP-SPECIFIC (TriPeaks splash navigation), not a
  foundation render-entry gap. The foundation half is PROVEN.
- No runtime code change made by this verification (honest outcome).
- The "measure-before-render law at render entry" remains a REGISTERED
  future direction with NO current failing consumer at HEAD; implementing
  it now would fix nothing observable and was therefore NOT done.
