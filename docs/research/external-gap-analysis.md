# External Gap Analysis — what MiniAndroid still lacks, ranked by evidence

Input: source studies in this directory + MiniAndroid's own evidence base
(AGENT_FINDING_AUDIT.md, CAMPAIGN_FINAL_REPORT.md,
COMPATIBILITY_REFERENCE_MATRIX.md) at HEAD 8233432.

Gaps are ranked by (corpus evidence × pipeline criticality). "No corpus
demand" is an honest classification, not a dismissal — it means no APK in
the current corpus exercised the behavior.

## G1 — Font pipeline completeness (highest criticality)
- Gap: res/font (Case B/C) has NO corpus APK and NO synthetic fixture;
  Typeface fixtures D/E (explicit create / fallback) queued from prior
  campaign; Case F (unloadable font) has no distinguishing fixture
  (AOSP evidence now pins the expected behavior — font-runtime-study.md
  FONT-002).
- Evidence: prior-session corpus scan (tictactoe/openlauncher/system
  classes proven); res/font open.
- Next action: synthetic-ARSC res/font fixture + Case-F fixture with
  distinct diagnostic events. Blocks: full §27 font law closure.

## G2 — Complete-APK program extension beyond tictactoe_golden
- Gap: exactly one complete GUI golden exists (tictactoe_golden).
  Every additional complete-APK run (HelloWorld-class golden, then one
  Compose-class app) multiplies the pipeline's evidential value.
- Next action: build HelloWorld-class real APK golden per §25 as the
  second permanent golden; dooz/Compose depth next.

## G3 — Resource differential coverage (ARSC-001/005)
- Gap: sparse type chunks (0x01) and offset16 (0x02) encodings lack unit
  fixtures; per-category differential fixtures (§13 list) partially exist
  (string/color proven; dimen/integer/boolean/style/theme/aliases queued).
- Next action: ARSC round-trip + category fixtures (DEX-009 methodology).

## G4 — Invoke-argument discriminators (WINEDROID-007)
- Gap: receiver/wide/float/absent-arg delivery is covered by prior
  fixtures for present args; the zero-fill-of-absent-incoming-registers
  behavior is untested.
- Next action: one fixture with ins_size < allocated incoming tail;
  assert zeroed values.

## G5 — Scanner payload-is-data invariant (WINEDROID-011)
- Gap: no fixture where a switch payload byte pattern equals a valid
  opcode byte sequence (the exact bug class that bit WineDroid).
- Next action: crafted fixture; assert interpreter routes around payload.

## G6 — Diagnostics surface (WINEDROID-015/016, AOSP-016)
- Gap: no per-DEX stats block in inspect-style output; no explicit cdex
  rejection message; warnings not accumulated into a structured report.
- Next action: extend existing probe/inspect path (small, self-contained).

## G7 — Per-method link/reject graph (WINEDROID-009)
- Gap: for a real APK we cannot yet print "which methods are runnable,
  which rejected, why" as an artifact — the single most useful
  compatibility communication tool observed this campaign.
- Next action: extend try_recursive_invoke with the structured report.

## G8 — Handler dispatch third tier (AOSP-009)
- Gap: msg.callback (Runnable) and listener dispatch verified;
  Handler.Callback (`mCallback.handleMessage`) tier has no fixture and no
  shadow behavior distinction.
- Next action: fixture when a corpus app exercises it (none currently —
  honest no-corpus-demand classification).

## G9 — Sandboxing posture (WINEDROID-017, GFX-004)
- Gap: MiniAndroid loads untrusted APKs in-process with no size caps
  beyond implicit memory and no documented sandbox story.
- Next action: adopt per-entry size caps + document posture (docs-only
  first step; process isolation deferred until a deployment story exists).

## G10 — Repository-law follow-ups
- sim-use: REPOSITORY_UNAVAILABLE (became 404 mid-session) — recheck
  periodically; do NOT substitute lycorp-jp/sim-use.
- AndroidRecomp / ReSource / Reveree: REPOSITORY_URL_UNVERIFIED — if the
  user can supply exact URLs, they enter the inventory lawfully.
- frameworks/av: reachable but unstudied (media stack — below current
  criticality line).

## Non-gaps (explicitly closed by evidence)
- DEX arithmetic/switch/exception semantics (fixtures at prior HEAD;
  re-validation queued but expected green).
- Core layout table (AOSP-003 parity confirmed line-by-line this session).
- Canvas/Path surface for the corpus (Cycle E; re-validation queued).
- Font discovery for assets-based apps (corpus-proven).
- ARSC classic-format resolution chain (RESULT_016 family).
