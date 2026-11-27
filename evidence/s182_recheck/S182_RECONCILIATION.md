# S182 HIDDEN ACHIEVEMENTS RECOVERY — historical-to-current reconciliation (2026-11-27)

Mission: the applications visible in `evidence/s182_mosaic/S182_MOSAIC.png`
(the S182 20-title battery, main `5d7edcdb`, 2026-11-06) were not represented
in the main achievement reports. This is the complete, measured
reconciliation of the NINE REAL_APP_CONTENT candidates on current HEAD
`96878de83` — no verdict assumed, every row re-run this session.

## 1. Why they were omitted (the audit answer)

Cross-check of `docs/evidence/canonical/registry.json`, `docs/ACHIEVEMENTS.md`
and `README.md` for the nine packages:

| packages with standing mentions | registry / achievements / readme |
|---|---|
| de.duenndns.gmdice | 3 / 3 / 0 |
| com.dozingcatsoftware.bouncy | 4 / 2 / 1 |
| org.secuso.privacyfriendlysolitaire | 3 / 2 / 0 |
| **ac.stresa.uturn, org.secuso.privacyfriendlydicer, com.ashkanrafiee.librecontactsbackup, app.wocheneinkauf, com.maxistar.textpad, app.simple.peri** | **0 / 0 / 0 — completely absent** |

Root cause: the S182 battery recorded its results in
`evidence/s182_minimal2/S182_BATTERY.json` (tracked) but the reconciliation
step into the canonical registry + ACHIEVEMENTS.md was never executed for six
of the nine titles; the S182 CLOSED_AUDIT (2026-11-06) audited ISSUE
CLOSURES, not the achievements ledger, so the gap survived five waves. The
omission is a REPORTING failure, not an evidence failure — the primary
records were tracked the whole time.

## 2. The reconciliation matrix (all 9 re-run on 96878de83 this session)

Protocol: the original `s182_minimal2_battery.py` law unchanged
(`run --execution-mode real-dalvik --data-root fresh-store --max-seconds 45/60
--frames 5 --trace --package <pkg>`), production binary
`v0.0.6.2` commit `96878de83`, fresh store per title, results in
`run_s182_recheck/S182_BATTERY.json` (committed as
`evidence/s182_recheck/S182_BATTERY.json`). The 7 fdroid_batch APKs were
restored byte-exact from `f-droid.org/repo` (versioned artifacts are
immutable; SHA256 receipts in `apk_shas.txt` + `scripts/s182_restore_receipt.txt`)
after the sandbox recycle lost them from disk — provenance honest, not assumed.

| Package | APK SHA256 | Historical (S182, 5d7edcdb) | Current HEAD (96878de83) | Visible content | Interaction | Determinism | Remaining blockers |
|---|---|---|---|---|---|---|---|
| de.duenndns.gmdice | `1621eda11b5dbc0c…` | REAL_APP_CONTENT, face `3891679dff449331`, px 182,535, unc 0 | **REAL_APP_CONTENT, face `3891679dff449331` BYTE-IDENTICAL**, px 182,535, unc 0 | game-owned dice face | S182 protocol launch+census; tap gameplay proven in later waves | byte-identical face = deterministic | none at this class |
| com.dozingcatsoftware.bouncy | `ffda0d9cb0b1b2aa…` | REAL_APP_CONTENT, face `dd0c14257fa1f2af`, px 978,380, **unc 18** | **REAL_APP_CONTENT, px 1,095,220, unc 0 — IMPROVED** | full pinball table | tap gameplay proven in later waves | face drifted (more content drawn) | none at this class |
| org.secuso.privacyfriendlydicer | `f2b4d3f021c3a620…` | REAL_APP_CONTENT, face `31ffa499c59e3e41`, px 1,041 | **REAL_APP_CONTENT, face BYTE-IDENTICAL**, unc 12 (nonfatal, face unchanged) | dice UI face | launch+census (S182 protocol) | byte-identical | unc-12 nonfatal exceptions recorded |
| org.secuso.privacyfriendlysolitaire | `b0e2adf991f94982…` | REAL_APP_CONTENT, face `88dbb4a719dbc8d4`, px 58,212 | **REAL_APP_CONTENT, face BYTE-IDENTICAL**, px 58,212, unc 0 | solitaire layout | launch+census | byte-identical | none at this class |
| com.maxistar.textpad | `322ba8b62ed791db…` | REAL_APP_CONTENT, face `27f44f4647bf76f2`, px 2,418 | **REAL_APP_CONTENT, face BYTE-IDENTICAL**, px 2,418, unc 0 | editor chrome | launch+census | byte-identical | none at this class |
| com.ashkanrafiee.librecontactsbackup | `1ae81c24dcaf2ec5…` | REAL_APP_CONTENT, face `e97c63673afdade2`, px 1,214,501 | **REAL_APP_CONTENT, face drifted** `79bb8fa317311c9a`, px 720,117, unc 4 | app content (less than 2026-11-06) | launch+census | deterministic run | px 1.21M→0.72M drift — content-set change to reconcile |
| ac.stresa.uturn | `dc8e08d4db9cc0c2…` | REAL_APP_CONTENT, face `a53523e7ca331866`, px 10,782 | **DEFAULT_BACKGROUND_ONLY, px 0, unc 8 — REGRESSED** | background only | — | background face `b5a7a35d5fe0564b` (shared default) | **Compose measure frontier:** `IllegalStateException` unwound in `androidx.compose.ui.platform.AbstractComposeView.internalOnMeasure$ui`/`.onMeasure` (named in trace) |
| app.wocheneinkauf | `02c08e2a3a1e585f…` | REAL_APP_CONTENT, face `eee8d351d081b2c7`, px 44,227, unc 0 | **DEFAULT_BACKGROUND_ONLY, px 0, unc 33 — REGRESSED** | background only | — | shared default face | **same Compose onMeasure ISE** (`Lt;.i`/`Lt;.onMeasure` unwind) |
| app.simple.peri | `78e04d5811464f2b…` | REAL_APP_CONTENT, face `8fc63a05e0d7b777`, px 325,303 (61.3 s wall) | **DEFAULT_BACKGROUND_ONLY, px 0, unc 33 — REGRESSED** | background only | — | shared default face | **same Compose onMeasure ISE** (`AbstractComposeView.internalOnMeasure$ui`) |

**Verdict classes (per the mission's own taxonomy):**
- **Genuine historical successes, still real today: 6/9** — gmdice,
  pfdicer, pfsolitaire, textpad (4 byte-identical faces — the strongest
  possible determinism proof), bouncy (improved: 18 uncaught → 0),
  librecontactsbackup (real, drifted).
- **Genuine historical successes that NO LONGER reproduce: 3/9** — uturn,
  wocheneinkauf, peri. All three are Compose-generation apps; all three die
  at the SAME named frontier (`AbstractComposeView.onMeasure`
  IllegalStateException). This is the known DEX-emulation Compose frontier
  (S27-RECON §1 "biggest shared-runtime bottleneck"), not three separate
  bugs. The historical evidence stands; the regression is on current HEAD.
- Static-first-frame-only vs fully interactive: the S182 protocol was
  launch+census (no taps); interactive play for gmdice/bouncy is proven by
  later waves; the other four holders are REAL content faces at this class.

## 3. Recommendations (registry + README — reporting only, no runtime changes)

1. **Registry**: add the six confirmed-current titles to
   `docs/evidence/canonical/registry.json` with the byte-identical face
   hashes above (REAL, current-HEAD-verified 2026-11-27), and the three
   regressed titles as `HISTORICAL_REAL / CURRENT-REGRESSED` rows carrying
   the Compose-onMeasure blocker name — never presented as current
   achievements.
2. **ACHIEVEMENTS.md**: one section per title with the matrix row; the
   mosaic PNG stays the visual index (it is the user-cited evidence).
3. **README**: no claim changes until the registry rows land; the six
   confirmed titles may join the rendered-content list.
4. **No issue closures** on the three regressed titles without re-verification;
   their blocker is the shared Compose-measure frontier (tracked at the
   S27/S181 blocker lines).
5. The face-drift rows (bouncy, librecontactsbackup) get a reconcile pass
   in the next compatibility census — drift is recorded, not adjudicated here.
