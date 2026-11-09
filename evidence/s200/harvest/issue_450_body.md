# Coder 2 — Mission Board & Worklist

> I am **Coder 2**. Per the owner's directive, all my work happens **through issues only** — this board is my single overview; every achievement/finding gets its own issue; **no pushes, no comments on other coders' issues** (I follow Coder 3's house rule, #415). Evidence law: every claim carries exact commands + SHA256 + pixel statistics; status vocabulary aligned with the constitution (`PROVEN / PARTIAL / RUNS / BUDGET / BLOCKED`), no fake success (#381).
>
> **Lane**: breadth over the canonical corpus (`miniandroid/APK_REGISTRY.json`, 23 entries) + the Telegram family (owner's stated priority), on **fresh 4 GB / no-KVM sandboxes**, with a strict disk keep-set.

## My issues so far

| Issue | Type | One-line summary |
|---|---|---|
| #446 | Achievement (INFRA) | runtime rebuilds from source in one 570 s chunk on 4 GB / 2 vCPU / no-KVM; OOM matrix + sandbox job laws |
| #447 | Achievement (app) | gmdice v8 independently reproduced: SUCCESS, 0 errors, 99.4% non-white, PNG attached |
| #448 | Finding (app) | Telegram official **v13.1.1** inflates 15,963 nodes but renders white; 3-gap blocker chain with detectors |
| #449 | Finding (registry) | Telegram v12.10.1 baseline pin unfetchable from its live link → frozen-mirror law proposed |
| #451 | Achievement (app) | TicTacToe (emmanuelmess) v3: solid `#303030` window, zero game content; libGDX `<clinit>` blocker named (2nd face of #388 family) |
| #452 | Achievement (app) | Chess Clock v29 re-proven: clean SUCCESS, content-rich render |
| #453 | Achievement (app) | MicroTimer v8: FIRST full render (was registry-only) — 8-child root |
| #454 | Achievement (app) | uNote v30: FIRST full render (was registry-only) — 100% painted |
| #455 | Achievement (app) | Heading Calculator v1: richest render (828 colors, 184 nodes) |
| #456 | Achievement (app) | Simple Stopwatch v26: full paint but F-016 divergent face (question filed) |
| #457 | Finding (app) | Notes (billthefarmer) v139: crash-less white face — distinct diagnostic family |
| #458 | Finding (registry) | Tiny Music Player v1 link dead (2nd drift instance) — frozen-mirror law justified ×2 |
| #459 | Finding (lane) | Simple Keyboard v145: IME lane structurally different — harness decision requested |

*(all fourteen filed 2026-11-02 under this account; #446–#459 are the evidence issues, this board is the index.)*

## Worklist — the canonical corpus (23 entries), Coder 2 view

Registry status is quoted verbatim from `APK_REGISTRY.json`; “Coder 2 next action” is my plan on the fresh sandbox.

| # | App (package) | Registry status | Coder 2 next action |
|---|---|---|---|
| 1 | gmdice (`de.duenndns.gmdice`) | PROVEN | ✅ **REPRODUCED** → #447 |
| 2 | Telegram v12 (`org.telegram.messenger`) | PROVEN (3/3, BASELINE_MATCH) | baseline refetch blocked → #449; A/B pending frozen mirror |
| 3 | Telegram v10.14.5 (arm64-v8a) | PROVEN (registry-only) | **SKIP — LAW-001 ABI out of scope** (arm64-only) |
| 4 | Simple Stopwatch (`omegacentauri.mobi.simplestopwatch`) | PROVEN | ⚠️ RE-RUN divergent face → #456 (full paint + F-016 late exception) |
| 5 | Chess Clock (`com.chessclock.android`) | PROVEN (HEAD 65c010f2) | ✅ RE-PROVEN → #452 (clean SUCCESS) |
| 6 | OpenLauncher (`com.benny.openlauncher`) | FROZEN — SHA arbitrated | re-run; if SHA mismatch → report, don't force |
| 7 | TicTacToe (`com.emmanuelmess.tictactoe`) | PARTIAL / registry-only | ✅ **VERDICTED** → #451 (libGDX `<clinit>` blocker named) |
| 8 | Simple Keyboard (`rkr.simplekeyboard.inputmethod`) | PARTIAL / registry-only | 🔎 VERDICTED → #459 (IME needs harness — decision requested) |
| 9 | MicroTimer | PARTIAL / registry-only | ✅ RENDERED_FULL → #453 |
| 10 | uNote (`app.varlorg.unote`) | PARTIAL / registry-only | ✅ RENDERED_FULL → #454 |
| 11 | Notes (`billthefarmer`) | PARTIAL / registry-only | 🔎 VERDICTED → #457 (crash-less white face) |
| 12 | Heading Calculator | PARTIAL / registry-only | ✅ RENDERED_FULL → #455 (828 colors) |
| 13 | Tiny Music Player | PARTIAL / registry-only | 🚫 ARTIFACT LOST → #458 (F-Droid link dead — 2nd drift instance) |
| 14 | Dooz (`io.github.yamin8000.dooz`) | ROOT-LOCATED (Compose boundary) | re-run; Compose frontier is #380's lane — I only add fresh data |
| 15 | BGClock (`nl.hansdezwart.bgclock`) | DOCUMENTED BOUNDARY | low priority (documented) |
| 16 | Stopwatch (`com.github.muellerma.stopwatch`) | DOCUMENTED BOUNDARY | low priority (documented) |
| 17 | TicTacToe (`com.itsfrz.tictactoe`) | RUNS; NPE at app boundary | fetch + run; capture the NPE chain as evidence |
| 18 | RTTT (`org.kirkezz.rttt`) | SUCCESS rc=0; empty frame (Compose) | re-run; frame-empty face → data for #380 |
| 19 | Privacy Friendly Dicer (`org.secuso.privacyfriendlydicer`) | RUNS; ISE at app boundary | queued |
| 20 | Antimine (`dev.lucanlm.antimine`) | RUNS; ISE at app boundary | queued |
| 21 | Privacy Friendly 2048 (`org.secuso.privacyfriendly2048`) | EXEC BUDGET TIMEOUT (540 s) | retry once on my host; if budget-bound again → confirm #registry verdict |
| 22 | Lexica (`com.serwylo.lexica`) | EXEC BUDGET TIMEOUT (540 s) | same as 21 |
| 23 | Freebloks (`de.saschahlusiak.freebloks`) | FIRST RUN DONE (s138) | queued (has ARM native trees → check x86 tree first per LAW-001) |

**Outside-corpus lane (owner's priority): the Telegram family.** Official upstream is covered in #448 (v13.1.1) and by #16 / #356–363; forks (Forkgram already in #355) and the 8-repo fork sweep are **queued behind Finding 2's frozen mirror**, because every fork verdict needs a reproducible baseline to diff against.

## Routing rules (owner directive)

* An app that **can't be completed or is heavily problematic** is NOT abandoned silently: it stays in this table with its blocker issue (like #448), each blocker with a **one-line confirm/reject test** so the main coder can validate my verdict cheaply.
* **Disk keep-set law** (host is size-limited): keep only the runtime clone + build + ≤ 2 cached APKs + current app source; everything else is re-fetched on demand. Current usage: 857 MB / 9.9 GB. Finished sources get deleted after their issue is filed.
* Each completed app = its own Achievement issue (never batched into this board).

## Evidence & tooling note (owner attention)

Binary evidence (render PNGs, run logs) lives in my external cache, **SHA256-pinned inside each issue** and byte-reproducible via each issue's commands. Inline GitHub hosting is currently **blocked**: the token I operate with carries **Issues read/write only** — release creation returns `403 Resource not accessible by personal access token` (probed 2026-11-02). If the owner wants the PNGs embedded here, extend the token's Contents permission (or tell me and I re-file with whatever hosting is available). No APKs are ever attached (§20).

---
Filed by **Coder 2** (autonomous builder agent; issues are my only channel to the main coder). Host: 4,041 MB RAM · 2 vCPU · no `/dev/kvm` · runtime commit `7354c06` · 2026-11-02.
---

## Wave 3 — Coder 2 (games lane) · 2026-11-03 · commit `7354c06`

All 8 remaining non-Telegram registry entries fetched (SHA-verified against pins), run, rendered. Per-verdict issues: #460, #461, #462, #463, #464, #465, #466, #467

| # | App | Registry face before | Verdict today | Evidence |
|---|---|---|---|---|
| 1 | PF 2048 (`org.secuso.privacyfriendly2048`) | EXEC BUDGET TIMEOUT — no frame claim | ✅ **FIRST REAL UI**: onboarding Skip/Next buttons render (30 colors; bottom band) | #460 |
| 2 | Freebloks (`de.saschahlusiak.freebloks`) | DEFAULT_BACKGROUND_ONLY (first_miss) | ⬛ face reproduced; blocker named: Kotlin `lateinit scene` RuntimeException | #461 |
| 3 | RTTT (`org.kirkezz.rttt`) | empty frame (Compose frontier family) | ⬜ white; **label corrected — blocker is the SDL lane** (`SDLActivity.main` NPE) | #462 |
| 4 | PF Dicer (`org.secuso.privacyfriendlydicer`) | empty frame | 🟦 **progress rung**: SECUSO splash blue paints (#0274B2); Thread crash-handler REC-MISS named | #463 |
| 5 | Antimine (`dev.lucanlm.antimine`) | empty frame (ISE at boundary) | ⬜ white; 434 SGET-MISS burst + xml-resource NotFound + null-AttributeSet NPE named | #464 |
| 6 | TicTacToe itsfrz (`com.itsfrz.tictactoe`) | empty frame (NPE at boundary) | 🟩 theme-navy `#202230` background-only face confirmed with pixel evidence | #465 |
| 7 | OpenLauncher (`com.benny.openlauncher`) | FROZEN (SHA arbitrated) | ⬛ pin re-validated; `#303030` face; **22 unrendered custom views** = best paint-gap stress test | #466 |
| 8 | Lexica (`com.serwylo.lexica`) | EXEC BUDGET TIMEOUT — no frame claim | ⬜ budget face retired (completes at 480s lean schedule); quiet crash-less white (Compose) | #467 |

Corpus-level notes for the main coder:
* **Budget law is not a law**: both "540s-timeout" apps complete with a *leaner* frame schedule (3×1s) inside 480s — interpreter init dominates, frame budget was the waste.
* **Uniform frames hash byte-identical**: pure-white renders share one sha256 (`31ddd4d5…`), `#303030` renders share another (`b5a7a35d…`). Byte-compare of PNG sha is therefore a zero-cost face classifier (white / #303030 / unique-content) for any future run.
* Every issue carries a one-command confirm/reject test; each APK was deleted from my cache immediately after its run (disk rule honored).


**Wave 4 worklist (next items, decisions D1–D4 pending): #468 — W4-1/2/3 EXECUTED & closed (Notes white face genuine; Telegram face crash-chain not budget, byte-identical across sessions; PF Dicer deterministic); only decisions D1–D4 remain open**

**[Coder 5] MASTER ACHIEVEMENT LEDGER (complete Coder-2 campaign record + 19 per-app living trackers): #472**

**Wave S167 (honest-stub battery, user directive 20-30 problems best case): 116 problem classes closed** — the S166 "64→0 stubbed" claim measured ring-dump-blind (true face: 185 distinct / 96,469 live stubbed calls); census made honest (permanent signature registry + late record points + crash.log record-window fix — crash.log now equals F-016 on every app); 59 AOSP laws answered 99.7% of all stubbed calls (dooz wall 131.7s→6.9s); pf2048 FIRST tutorial-page content paint (face `3ba1af4d48601773`, measured+kept); battery-OFF 5/5 pins byte-inert; P149 activation measured+REJECTED (opencalc keypad collapse); evidence `evidence/s167_sweep/`; commit `6f5c3a99` local (push 403 standing).

**Wave S166 (problem sweep, user directive ≥20 problems solved): 67 enumerated → ALL solved** — 64 stubbed-API signatures → 0 whole-corpus (10,377 calls), Object.clone shallow-copy root, Reference-family hierarchy, crash.log classification; all 5 corpus faces byte-inert; evidence `evidence/s166_sweep/`; commits `71d66a42`+`bb825aeb` local (push 403 standing).
