# [S205] CODER 3 — THE 30-PROBLEM LEDGER (list-and-solve, updated for the S203/S204 main state)

Directive frame (user): «ادامه به از جایی که ناقص موندی حداقل ۳۰ مورد رو باید لیست بکنی و حل بکنی» — continue from where it stopped being complete; list AT LEAST 30 concrete problems and solve them, until apps and games render completely. English per K-5; statuses per K-6; every solved item gets its own confirmation link in the closing report.

## 0) State recovery first (what changed since my last on-record wave, S196)

Fresh-container honesty: my previous session's context was lost; this session re-derives everything from the records. Read before listing:

- **origin/main moved to `0979678e`** (S204 verdict push, 2026-11-09T13:39Z): the tictactoe BOARD WALL fell (Coder-5, L-04: F-NEW-630 typed-view `limit()` getter; binary `4f5c5b9a11a8b9d2`), board renders + X/O tap interaction proven, **L-06 (win/stalemate) named OPEN by Coder-5** with the text-glyph-blocks wall named next.
- **#572** (main coder, S195): unote_30 SQLite write→read→rendered-row round trip, five F-S195 laws — unote deep lane is THEIRS now.
- **#573** (S168 lane): dooz 20-problem render ladder — #1 CLOSED (framework-table restore → `a0fae9072313e2d1` byte-exact), #2..20 OPEN — **dooz board frontier is THEIRS; I do not touch it.**
- **#565** K-1..K-7 governance adopted for this ledger.
- Environment restored per record: origin/main fetched into a clean worktree @ `0979678e`; androguard 4.1.4 installed; framework-table restored from the PUBLIC pinned toolchain (`dl.google.com/android/repository/platform-34-ext7_r03.zip` → `android-34/android.jar` → `resources.arsc` 16,390,624 bytes → `miniandroid/framework_res/resources.arsc`) — **byte-size differs from the #573 pin (16,424,688): P-08 verifies equivalence empirically instead of assuming it.**

## 1) Anti-parallel dedup (what I will NOT redo)

| Lane | Owner | My action |
|---|---|---|
| dooz board frontier (#573 #2..20) | S168 lane | none — goldens only |
| tictactoe L-06 fix + text-glyph wall | Coder-5 (#557) | decode-intel + empirical verify ONLY (Lane A) |
| unote SQLite depth (#572) | main coder | golden anchor P-07 only |
| androidx fragment/UriMatcher/Godot (#568/#569/#571) | Coder-5/Coder-4 | none |
| base-layer W-laws (#563/#564/#566/#567) | Coder-4 | none |

## 2) The 30 problems (P-01..P-30)

Status legend: OPEN / IN_PROGRESS / CLOSED(this session, with link) / VERIFIED / SUPERSEDED.

**Lane A — tictactoe win-chain: androguard ground truth + empirical verification (complements Coder-5 L-06, no fix duplication)**
- **P-01** androguard static decode of the input→state chain (onTouchEvent → renderer input → actor placement) with precise numbers (classes, methods, bytecode offsets). — OPEN
- **P-02** decode the win/judge logic (3-in-a-row test + winner-text update path), exact methods+offsets. — OPEN
- **P-03** decode X/O/win-line render calls vs engine shadow coverage; cross-check vs the S204 census. — OPEN
- **P-04** deterministic full-game tap sequence (cell→coordinate map) as an executable K-4 recipe. — OPEN
- **P-05** run the full game on the current main HEAD binary; record whether the win line + winner text present; if an ENGINE gap blocks the judge path, root-cause it and fix only inside my law families (string/boxing/collections), otherwise hand the precise defect to #557. — OPEN

**Lane B — the golden anchor wall on the NEW main HEAD (all ×3, byte-exact or honest delta)**
- **P-06** bouncy `8a6c24ac8a7d718e` (the restored original pin). — OPEN
- **P-07** unote `3b8dcb0adbbc17a9`. — OPEN
- **P-08** dooz chrome `a0fae9072313e2d1` on the ext7_r03-derived framework table (equivalence check vs the #573 pin). — OPEN
- **P-09** microtimer `b39665f68f3938e6`. — OPEN
- **P-10** opencalc `63020bc7334048fe`. — OPEN
- **P-11** tictactoe no-tap `f1157d7eba20bedf` ×3 + gmdice 5-tap `3891679dff449331`. — OPEN

**Lane C — my law stack re-verified on the new line**
- **P-12** F-NEW-588 present and green on `0979678e`. — OPEN
- **P-13** F-NEW-589 present and green on `0979678e`. — OPEN
- **P-14** F-NEW-601–602 (S191 gmdice stack) landed-status audit on main source. — OPEN
- **P-15** F-NEW-603–605 landed-status audit. — OPEN
- **P-16** F-NEW-582/586 merged-superset behavior re-check (S196 §3 law: symbol-collision merges). — OPEN

**Lane D — RENDER-DEPTH A25/A26/A27 (my androguard apps: rc=0 → deeper journeys + pins)**
- **P-17** headingcalculator full journey re-verify (TC360/TAS100/WD270/WS30 → TH=343 GS=95) ×3. — OPEN
- **P-18** chessclock first deterministic tap journey (start/stop) + face pin. — OPEN
- **P-19** gmdice extended multi-state journey + pin re-verify. — OPEN
- **P-20** chessclock+gmdice androguard render-path census → engine gap list (named walls for a future wave). — OPEN
- **P-21** headingcalculator output-text pixel-depth: the computed numbers must be rendered text, not chrome-only (text-law check on my lane). — OPEN
- **P-22** register A25/A26/A27 face pins into evidence + this board. — OPEN

**Lane E — protocol + evidence replay (close the publication-defect class)**
- **P-23** §8-PREFLIGHT rule formalized: `git apply --check` mandatory pre-post + the S196 symbol-collision cross-check law, posted to the #565 governance thread. — OPEN
- **P-24** replay S192 `APPLY_MATRIX.json` against current main (apply CLEAN or document drift per hunk). — OPEN
- **P-25** replay S192 `SEAM_TEST.json` (6/6 rc=0) on the new build. — OPEN
- **P-26** S191 independent re-verification from the #561 published patch parts (cross-confirm the main coder's reproduction record). — OPEN
- **P-27** libGDX host-native builder law: generic build script + sha16 table so the maintainer line can regenerate `libgdx64/box2d64/freetype64` (#557 §5 need). — OPEN

**Lane F — board + governance close-out**
- **P-28** this ledger live on #492 (this post) with per-item statuses maintained. — CLOSED (this post)
- **P-29** #570 external-tool audit contribution: androguard quantified-impact row (S157→S196 numbers from on-record issues). — OPEN
- **P-30** final S205 wave report on this thread: all 30 statuses + confirmation links + K-7 checklist. — OPEN

## 3) Execution order

Build main HEAD first (running) → Lane B gates (P-06..P-11) → Lane C audits (P-12..P-16) → Lane A decode+run (P-01..P-05) → Lane D (P-17..P-22) → Lane E (P-23..P-27) → Lane F close (P-29, P-30).

Every claim in the closing report carries a runnable command + expected/observed (K-4). No fix lands outside my lane families; anything discovered elsewhere is handed to the owning thread with evidence.
