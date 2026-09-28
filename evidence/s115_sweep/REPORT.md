# S115 — 77-Ticket NEAR_BLANK Assembly-Line Sweep (S114 HEAD `f191f839`)

User directive: review all 77 reopened NEAR_BLANK tickets **without getting stuck on any one**,
then move to Telegram. Method honored: ONE run per ticket, fixed budget, zero per-ticket debugging.

## Method
- Corpus: the 77 NEAR_BLANK tickets from the S108 audit reopen table (`evidence/audit_s107/reopened.json`).
- APKs: local caches first, else F-Droid suggested version (`f-droid.org/api/v1/packages/<pkg>`).
- One run per ticket (`timeout 140s`), pixel metrics on the captured frame
  (unique colors, dominant, non-background ratio, entropy).
- Results: `run/s115_sweep/state.json` (per-ticket), `run/s115_sweep/families_norm.json` (families).

## Results (77/77 re-run)

| verdict | count | meaning |
|---|---|---|
| MARGINAL (effectively blank) | 67 | 2-color window after early death; no meaningful content |
| PARTIAL (real pixels, wrong layout) | 4 | #191 overlap-jumble, #216 misplaced dialog text, #219 bottom strip, #212 toolbar strip |
| NO_SHOT (corrupt APK download) | 5 | #87 #107 #120 #185 #206 — PARSE_ERROR: no end-of-central-directory (fetch problem, not runtime) |
| CLOSED | 0 | none reached the render-law bar (complete GUI + correct content) |

**Honest bottom line: the S114 HTML5/WebView laws do not move this corpus** — it is dominated by
native-View early-death families, not the WebView family. No closures under the render law.
Comments with fresh status + family attribution posted on all 77 tickets (77/77, English only).

## Family attribution (batch evidence)

| family | count | tickets | shared frontier |
|---|---|---|---|
| Empty view tree, silent (rc=0, 0 errors) | ~21 | e.g. #91 #116 #119 #122 #143… | lifecycle completes via DEX engine (onCreate→onStart→onResume), attach finds **0 view nodes** — `ComposeView NOT in class index` / inflation frontier → **#344 blank-render L0, #230 Compose, #348 appcompat decor** |
| Empty view tree + non-fatal errors (rc=1) | ~22 | e.g. #64 #69 #79 #88… | same 0-view-node frontier with recorded compat errors |
| libGDX "incorrect configuration" | 6 | #75 #85 #109 #114 + 2 | APK-packaged `.so` loading + JNI registration capability (GodotApp.onCreate / libGDX natives) |
| "Next event must be ON_CREATE" | 4 | #86 + 3 | androidx LifecycleRegistry event-sequencing law |
| "FragmentManager has not been attached to a host" | 3 | #96 #161 +1 | androidx Fragment host-attachment law |
| MultiDex installation failed | 2 | #67 #104 | MultiDex install contract |
| ViewTreeLifecycleOwner not found | 2 | #218 +1 | androidx compat view-tree owner tag (#348 family) |
| Corrupt APK fetch | 5 | #87 #107 #120 #185 #206 | re-fetch required |

## Deliverables
- `scripts/s115_sweep77.py` — resumable sweep runner (wall-clock budgeted)
- `scripts/s115_family_histogram.py` — family attribution
- `scripts/s115_comment_tickets.py` — 77 honest status comments
- `run/s115_sweep/state.json` — per-ticket metrics
- `run/s115_sweep/families_norm.json` — family map
- Per-ticket evidence: `evidence/s115_sweep/t<N>_<pkg>/` (run.log trimmed, screenshot, report, crash.log)

## Next
The sweep converts 77 un-triaged tickets into 5 mapped shared families. The leverage point is the
empty-view-tree family (~43 tickets): lifecycle is complete, the content view never materializes.
That is ONE generic frontier (View materialization/inflation), not 43 bugs. Next shared-family fix
targets it, then the sweep re-runs automatically.
