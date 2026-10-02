# CAMPAIGN_STATE — MiniAndroid-Compatibility-Runtime

HEAD at state update: F-NEW-234 wave (IAPK campaign) ← e9ce717b (MEGA-W2) ← 286b4994
Date: 2026-10-03 (INSTALLED-APP FILESYSTEM + MEDIA campaign)

## LAWS READ

CONSTITUTION_V2 (evidence/regression/lifecycle/rendering/screenshot/registry/disk laws),
MASTER ROADMAP, source-first law, issue-per-problem law, FRAME_CAPTURE_TRUTH (12-item
proof chain), FRAMEWORK_CHROME_ONLY ≠ REAL_APP_CONTENT, F084 freeze, DEX register law,
class-init honesty, REC-MISS 7-class, no-package-specific-fixes, bounded logging,
screenshot/runtime proof laws (21-P0-6 pixel ownership), APK hygiene laws,
installed-APK filesystem requirements, canonical/v10_results_latest.json,
docs/corpus/s82/title_registry.json (frozen corpus = 202 titles, NOT 255),
README/ACHIEVEMENTS/ROADMAP_STATUS, issue #354 comment 5956211403.

## MASTER MERGED CHECKLIST

The ONE master checklist lives at **docs/FINAL_COMPATIBILITY_CAMPAIGN.md**
(mega-campaign §15). Current highlights:

| # | Item | Status |
|---|------|--------|
| 1 | F-NEW-231 INSTALLED_APK_ACCESS (§3 mandatory) | IMPLEMENTED+TESTED — 10/10 claims, 2 APKs, source-hidden proof |
| 2 | F-NEW-234 per-package context-root law (installed-app FILESYSTEM) | IMPLEMENTED+TESTED — 3-layout mismatch root-caused; 12 installed runs ×3; sources quarantined; file-IO + asset provenance; pkgaudit capability; goldens ×3 MATCH |
| 3 | F-NEW-232 deferred-UI observability | IMPLEMENTED+TESTED — fishrings NEW SUCCESS ×3 |
| 4 | F-NEW-233 unconditional frame-truth law | IMPLEMENTED+TESTED — false-SUCCESS family closed |
| 5 | F-NEW-230 golden validity | PARTIAL — 4 goldens VALID ×3 w/ repro blocks; whatsapp REJECTED; 4 STALE recorded |
| 6 | F-NEW-229 CL MATCH_PARENT spec law | OPEN (next attack) |
| 7 | F-NEW-221 R8 merged-class / F-NEW-217 kotlinx resume / F-NEW-204..207 / F-NEW-192 | OPEN |
| 8 | secuso sudoku button-text gap | REGISTERED (wave-2 finding) |
| 9 | Telegram title-overlap + intro/auth chain | REGISTERED — installed-mode filesystem RULED OUT as cause (F-NEW-234 file-IO trace: only benign first-launch theme-extract misses) |
| 10 | Safir / Black sentinels | BLOCKED-BY-IDENTITY (zero project records; APKs needed) |
| 11 | Families A–W root/fan-out audit | IN PROGRESS — deferred-UI fan-out family identified (7+ titles) |
| 12 | README/front-page + release audit (Phases 10–21) | NOT STARTED (stray uuid auto-commit 7abb39ce flagged) |
| 13 | APK-inspection skill feasibility | PARTIAL — `pkgaudit` runtime capability landed (F-NEW-234 wave) |
| 14 | Uninstall command | PENDING (recorded, not faked) |

## LIVE STATE

- Registry: 529 roots (F-NEW-234 IMPLEMENTED+TESTED)
- Installed-state gate (store run/iapk/store2, sources hidden): opencalc
  e364b001ee7abd66 ×3 = golden; bouncy b6dde6074bf47264 ×3; chess
  b5a7a35d5fe0564b ×3; telegram bbb6cd10a834963d ×3; unote (seeded random)
  4f1a9e4e8f64fae8 = golden; whatsapp (seeded random) = known face, no drift.
- Golden gate (sideload, ×3): dooz/microtimer/unote/opencalc ALL MATCH under
  the F-NEW-234 law.
- Filesystem law: ALL runtime app writes land in
  <data-root>/data/data/<package>/ (23/23 files in the AFTER suite); external
  app dirs = <data-root>/storage/emulated/0/Android/data/<pkg>/.
- Instruments: MINIANDROID_FILE_IO (file-IO JSONL provenance), gfx
  byte_source, `pkgaudit` command.
- Corpus reality: 202 frozen titles (100 game + 100 app + 2 mandatory); s107
  tmp APKs purged; local honest pool ~25 APKs; random ledger row 1 banked
  (seed 20261002).
- Disk free: ~6.9G; run/ artifacts kept bounded.

## NEXT TARGETS (priority order)

1. F-NEW-229 (opencalc full button width — CL spec routing trace).
2. Sudoku button-text gap + forkgram/ssw/headingcalc/secuso golden re-banks (F-NEW-230).
3. Time-driven re-test of the deferred-UI family (chess/klondike/tripeaks/flappycow/
   ballbreak — same first divergence as fishrings).
4. Telegram intro/auth chain + title-overlap bug.
5. F-NEW-217/221 deep legs; README/release audit phases.
