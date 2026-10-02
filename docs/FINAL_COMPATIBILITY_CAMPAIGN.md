# FINAL COMPATIBILITY CAMPAIGN — MASTER CHECKLIST

The ONE permanent master checklist (user directive §15). No competing checklist.
Created: 2026-10-02 · HEAD at creation: 286b4994 · Registry: 525 roots

Status legend:

```text
[ ] NOT STARTED     [~] IN PROGRESS    [?] OBSERVED
[✓] IMPLEMENTED     [✓✓] TESTED        [+] NEW APP SUCCESS
[!] REGRESSION      [X] BLOCKED        [S] SUPERSEDED
```

A checkbox becomes [✓✓] ONLY with runtime evidence. [+] ONLY when a real
previously-failing APK/game becomes successful. No evidence = no checkmark.

---

## LAWS READ (recorded 2026-10-02)

CONSTITUTION_V2 (source-first §2, never-invent-semantics §6, unknown-remains-unknown §7,
hypothesis≠root §8, fresh-live-evidence §9, first-divergence §16, silent-wrong §17,
register-width §21, R8-layer §22, end-to-end §26), MASTER ROADMAP, CAMPAIGN_STATE.md,
worklog.md (tail through F-NEW-228 completion wave), root_registry.json (525 roots,
status census), evidence laws (FRAME_CAPTURE_TRUTH 12-item proof chain),
FRAMEWORK_CHROME_ONLY ≠ REAL_APP_CONTENT, F084 freeze, DEX register law,
class-init honesty (failed clinit → NCDFE), REC-MISS 7-class, no-package-specific-fixes,
bounded logging (S43 ring cap), screenshot/runtime proof laws (21-P0-6 pixel ownership),
APK hygiene laws (no APK/large binaries in git; tmp-only corpus artifacts),
installed-APK filesystem requirements (platform-audit Phases 5–8),
canonical/v10_results_latest.json (five-app gate), docs/corpus/s82/title_registry.json
(frozen corpus 202 titles: 100 game + 100 app + 2 mandatory), current README.md,
docs/ACHIEVEMENTS.md, docs/ROADMAP_STATUS.md, issue #354 checkpoint flow.

## CORPUS REALITY (§4 — do not trust old numbers)

- Frozen corpus: **202 titles** (100 GAME + 100 APP + 2 MANDATORY) in
  `docs/corpus/s82/title_registry.json` — NOT 255; older numbers (255/129) counted
  overlapping s107 run dirs. The s107 wave ran 129 unique titles from `/tmp/s107_apks/`
  which has been **purged from disk** (disk-hygiene law). No re-download.
- Locally present frozen-corpus APKs (the only honest random-selection pool):
  canonical 11 (dooz, microtimer, unote, bouncy, tictactoe, stopwatch, gmdice,
  fishrings, tripeaks, opmt, muellerma-stopwatch) + gates 9 (opencalc, forkgram,
  telegram_official, secuso notes, secuso sudoku, klondike, chess_jwtc, ballbreak,
  flappycow) + wave builds (g2048, snakedeluxe, tetris, ttt, minicraft, snakeneon,
  browsers, webfix).
- Random selection = deterministic seed over the local frozen pool; seed + pool
  recorded per iteration. Titles whose APKs were tmp-purged are UNTESTABLE-THIS-ENV
  (recorded, not hidden).

## MASTER CHECKLIST

### §1–2 Historical achievement audit (required legacy items)

| # | Item | Status |
|---|------|--------|
| 1 | F-NEW-221 R8 merged-class ctor/dispatch deep leg | [ ] |
| 2 | F-NEW-217 kotlinx resume protocol (dame leg) | [ ] |
| 3 | F-NEW-204..207 P1 audit batch | [ ] |
| 4 | F-NEW-192 | [ ] |
| 5 | secuso grey/white-face rendering/provenance | [ ] |
| 6 | §28 final deliverable refresh | [ ] |
| 7 | F-NEW-228 weight-pass (claimed DONE) — re-verify reproducible | [ ] |
| 8 | F-NEW-229 CL MATCH_PARENT spec law | [ ] |
| 9 | F-NEW-230 golden provenance/config gap | [ ] |
| 10 | Families A–W root/fan-out audit | [ ] |
| 11 | Real-APK matrix refresh | [ ] |
| 12 | Installed-APK filesystem model proof | [ ] |
| 13 | APK-inspection skill feasibility | [ ] |
| 14 | README/front-page audit | [ ] |
| 15 | Version/release audit + release candidate | [ ] |
| 16 | Registry/worklog/evidence reconciliation | [~] |

### §3 Installed-APK access (mandatory platform capability)

| # | Item | Status |
|---|------|--------|
| 1 | Gap audit: current install/discovery mechanism | [ ] |
| 2 | F-NEW-231 registered | [ ] |
| 3 | Generic `install` capability implemented | [ ] |
| 4 | Installed-package discovery (agent works from package identity alone) | [ ] |
| 5 | Manifest/DEX/resource inspection from installed state | [ ] |
| 6 | Launch from installed state + provenance | [ ] |
| 7 | APP proof (opencalc) ×3 runs | [ ] |
| 8 | GAME proof ×3 runs | [ ] |
| 9 | 10 platform claims answered | [ ] |

### §4–5 Random corpus loop

| Iteration | Seed | Random APK 1 | Before | Root | After | Random APK 2 | Before | Root | After |
|----------:|------|--------------|--------|------|-------|--------------|--------|------|-------|
| (pending) | | | | | | | | | |

### §6 Telegram

| # | Item | Status |
|---|------|--------|
| 1 | telegram_official install/inspect/launch/trace/screenshot at HEAD | [ ] |
| 2 | forkgram gate re-run at HEAD | [ ] |
| 3 | blank/grey/custom-view state identified with first missing law | [ ] |

### §7 Sentinels

- **Safir**: [X] BLOCKED-BY-IDENTITY — zero matches for "Safir" in registry/worklog/
  docs/evidence/issue checkpoints (searched 2026-10-02). The name does not exist in
  any project record. APK needed from user to become a sentinel. NOT silently closed.
- **Black**: same result — zero matches. BLOCKED-BY-IDENTITY.
- Working sentinels kept visible every wave: dooz d602648e8e401895, microtimer
  da73010a37dd0189, unote 4f1a9e4e8f64fae8, opencalc e364b001ee7abd66,
  forkgram cf4c41e62ceb6557.

### §9 F-NEW-230 golden validity

| Golden | Validity | Action |
|--------|----------|--------|
| whatsapp 31ddd4d5b8e6d18e | INVALID (100% white) | reject as gate |
| ssw / headingcalc / secuso | STALE (not reproducible at HEAD, F-NEW-230) | re-bank with repro block |
| dooz / microtimer / unote / opencalc | reproducing ×3 | keep |

### §10 F-NEW-229 CL MATCH_PARENT spec law

| # | Item | Status |
|---|------|--------|
| 1 | Trace ConstraintLayout→spec→child→final width | [ ] |
| 2 | Generic fix (AOSP MeasureSpec law) | [ ] |
| 3 | Fan-out search | [ ] |

### §20–22 README / achievements / release reconciliation

| # | Item | Status |
|---|------|--------|
| 1 | README matches measured reality (no "525 roots" as headline) | [ ] |
| 2 | ACHIEVEMENTS reclassified (VALID/STALE/UNVERIFIED/SUPERSEDED) | [ ] |
| 3 | Release audit: clean git state, no stray commits, registry consistent | [ ] |

## ENTRY FORMAT (§16 — every completed item)

```text
ID: / DATE: / ROOT: / SOURCE: / LAW: / BEFORE: / CHANGE: / AFTER:
APK: / PACKAGE: / APK SHA: / RUN CONFIG: / RUNTIME RESULT:
VIEWTREE/PROVENANCE: / SCREENSHOT: / SCREENSHOT SHA: / 3-RUN:
NEW SUCCESS: / REGRESSION: / COMMIT: / ISSUE: / STATUS:
```
