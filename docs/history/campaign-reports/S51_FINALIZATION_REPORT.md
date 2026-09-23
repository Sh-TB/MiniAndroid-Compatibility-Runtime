# S51 FINALIZATION REPORT — CANONICAL REPOSITORY PURGE + ROADMAP COMPLETION + APP CERTIFICATION

**Date:** 2026-09-17 · **Final HEAD:** `25cb11bb` (main, 27 commits ahead of `origin/main` @ `7967c037`)
**Mission anchor:** user brief "S51 FINALIZATION" + follow-up request to add simple
programs/games (crossword, word-prediction, a very simple 2D
ball game, an XP-style mine-finder). Status vocabulary: honest states only.

---

## A. Executive Summary

MiniAndroid reached its strongest verified state to date: **battery extended 94 → 98
stages, ALL PASS ×4 full runs**; **six agent-playable games** (4 brand-new, per the
user's request); one **new runtime law fixed (R-NEW-374)** discovered by a new fixture;
tree hygiene completed (zero APK/AAB/binaries; 144 residue/dead files removed with
provenance preserved); Telegram/WhatsApp re-campaigned honestly; roadmap reconciled;
README rebuilt as a landing page with a SHA-pinned achievements gallery.
**The single blocking item for remote finalization is the invalid GitHub credential.**

## B. GitHub Push Status

- **BLOCKED — invalid credential.** The supplied token fails on every path:
  `api.github.com/user` → **401** (raw and dot-stripped variants);
  `git push origin main` → **"Invalid username or token. Password authentication is
  not supported"**; `ls-remote` succeeds only because the repo is public (anonymous read).
- Consequence: **27 commits verified locally await push** (22 pre-existing S49–S51 +
  5 finalization commits). Nothing was force-pushed; nothing was lost.
- Required next step: a **fresh fine-grained PAT** (Contents: read/write). Then:
  `git push origin main` → fresh clone → battery → verify (§27 of brief).

## C. Repository Size Before/After (current tree)

| Metric | Before (S51 phase 0) | After (final HEAD) |
|---|---|---|
| Tracked files | 3,498 | **3,381** (−117: 51 dead stubs, 93 META-INF, 2 archived, + new game files) |
| Tracked content | ~44 MB | **42.6 MB** (max file = `dalvik_engine.cpp` 1.52 MB, source) |
| APK/AAB/SO/ZIP/TAR tracked | 0 | **0** (maintained) |
| `.git` / pack | 625 MB / 491.5 MiB | 626 MB / 491.5 MiB (unchanged by law — history untouched) |
| History (all remote refs) | ~1.99 GiB blobs>1MB | unchanged — see §D |

## D. Historical Blob Audit

`docs/history/HISTORICAL_BLOAT_REPORT.md` (new) records: main-reachable
**~987 MiB** (dominated by ~885 MiB session stderr logs), all-refs **~1.99 GiB**
(+ llvm-mingw 83.9 MB, Telegram.apk 82.7 MB, libLLVM 78.1 MB, call_graph 65.5 MB,
fdroid_index 53.3 MB). Post-rewrite potential: **well under 100 MiB pack**.
**No history rewrite was performed** — sequencing law: valid credential → push →
backup → `HISTORY_PURGE_PLAN.md` → verified rewrite. Mirror backup:
`/home/z/archive/s51_full_mirror` (506 MB).

## E. APK/AAB Audit

- Current tree: **0 APK/AAB/SO/ZIP/TAR** (verified by extension sweep).
- Removed from tree this session: `corpus_cache/dooz23_extracted/` (93 files — §H).
- Telegram APK for the live campaign was extracted **from git history to /tmp**
  (zero-APK tree law respected) — blob `b2d52d57…`, 82,680,854 bytes,
  SHA256 `193ad551…` (recorded).
- Fixture APKs: rebuilt reproducibly from source by
  `scripts/build/build_fixture_apk.sh` (byte-deterministic epoch-pinned) — no
  fixture APKs are committed.

## F. LLVM/Toolchain Audit

- `tools/android-34.jar` (132 MB), `d8/` (18 MB), `aapt2/` (7.4 MB), `ecj/` (3.1 MB)
  are **gitignored local build toolchain** — used by the fixture build pipeline
  (aapt2+ECJ+D8 authority, `TOOLING_BASELINE.md`). They are NOT in Git and NOT in
  releases. No libLLVM/llvm-mingw dependency exists in the current tree or build
  graph — those exist only as historical blobs (§D) and are removable by the
  future history operation.

## G. tools/ vs scripts/ Architecture

Audited: **zero basename duplicates**, no nested tools/scripts trees (skills/ is
local-only). Canonical layout documented in `docs/tooling/TOOLING_BASELINE.md`:
`scripts/` = 174 project-automation files; `tools/verify/` + `doctor.sh` = 10
standalone forensic/verification utilities; toolchain binaries untracked.

## H. corpus_cache/dooz23_extracted/META-INF Resolution

**Category D (reproducible extraction residue) — removed.** Forensics: 93 files =
AndroidX/Kotlin `.version` pins + version-control-info.textproto; produced by the
Dooz-v23 APK extraction during S43/S44 upstream pinning (compose runtime/ui 1.11.4);
**zero runtime/test/script consumers** (`rg dooz23_extracted` → docs only);
byte-reproducible from the APK (SHA `299eab21…` re-verified on disk).
Knowledge preserved: `docs/upstream/dooz23_meta_inf_provenance.md` (verbatim pin
list + provenance + repro command); `docs/upstream/INDEX.md` updated;
`corpus_cache/` gitignored against re-entry.

## I. Master Roadmap 3 Reconciliation

`docs/runtime/FUTURE_ROADMAP.md` annotated with a per-item reconciliation table
(original 2026-08-12 text preserved verbatim): P0-1 invoke-static **DONE**;
P0-2 real-APK infra **DONE**; P0-3 resources **PARTIAL**; P1-4 object init
**LARGELY DONE**; P1-5 exceptions **DONE**; P1-6 multi-dex **DONE**; P2-7 API
surface **PARTIAL→SUBSTANTIAL**; games/agent **DONE** (not even planned then).
Canonical live status: README + APPLICATION_MATRIX + `root_registry.json`.

## J. Issue #9 Reconciliation

`docs/maintenance/issue9_reconciliation_S51final.md` — paste-ready payload with
the full verified summary and remaining blockers. **Remote update BLOCKED** on the
same credential failure (§B); nothing was claimed remotely.

## K. R-NEW-361

VERIFIED-FIXED (S51, prior cluster): silent depth-80 refusal starved the ScatterMap
Empty-fill; fix = dedicated 512 MB interpreter stack + backstop 512 + bounded
diagnostic. Post-fix: Dooz v18 launch completes (exit 0). Blank first frame =
**separate** rendering frontier (honest).

## L. R-NEW-372

VERIFIED (S51, prior cluster): wrapper `.TYPE` → primitive component type →
`multianewarray char[6][7]`; probe `outer-null=false inner-null=false v=X`.

## M. R-NEW-374 — NEW (this session)

**VERIFIED-FIXED.** The new crossword fixture exposed it: `String.valueOf(char)`
rendered decimal ASCII codes ("66" not "B"). Root cause: bridge selected overloads
by runtime value tag; aget-char's INT normalization (correct Dalvik law, K-41)
misled it. Fix: **descriptor-driven overload selection** — proto `(C)` renders the
code point; `(I)` unchanged (ART/OpenJDK law). Registry 354→355; solved card +
test evidence committed (`9d67ec20`).

## N. TicTacToe

Remains certified — golden `613cfccc…`, 9/9 clicks, deterministic replay; battery
§29 PASS in every run; agent-playable (schema proven S50/S51).

## O. Connect Four

Remains certified — 24-click golden, Y WINS at 22, frozen tail, 25/25 replay,
agent schema `S51_AGENT_C4.json`; a fresh screenshot was captured this session for
the gallery (`3ea18845…`).

## P. Dooz v18

Launch **completes** (exit 0 / SUCCESS — first in campaign history); framebuffer
blank = Compose drawing frontier; **not claimed rendered**.

## Q. Dooz v23

PARTIAL SUCCESS, 1 frame; one residual spin face (R-NEW-373 registered, probes
listed) + depth-512 refusal in `Lbp1;.<init>`.

## R. chessclock

TESTED — exit 0, real dark-theme UI rendered (`e4a2d7c9…` ×3 historical; gallery
image committed).

## S. unote

TESTED — exit 0, real UI with legible texts; gallery image committed.

## T. Telegram

**Parse-bound BLOCKED (honest).** Real campaign at final HEAD: APK validation +
manifest OK; 11,531-entry central directory parsed; per-class DEX code-item
forensics continues past **7 min** (single-threaded parser; second background run
confirmed >25 min to parse completion). Not a crash — a throughput frontier.
Next semantic blocker beyond: R-NEW-303 (desugared streams). Log bounded to /tmp
(no new giant logs committed).

## U. WhatsApp

**UNVERIFIED — acquisition BLOCKED.** Proprietary distribution (no F-Droid
channel) incompatible with repo licensing + zero-APK law; no claim made;
provenance/acquisition instructions documented in the matrix + Issue #9 payload.

## V. Sandbox Persistence

Sandbox protocol remains **ALL PASS (20/20, 4 runs)** — S50 evidence valid at this
HEAD; battery includes persistence goldens (F-012, F-026/027).

## W. Agent Playability — 6 certified games

| Game | Steps | State-changing | Terminal state | Schema |
|---|---|---|---|---|
| TicTacToe | 9 taps | full game | X WINS | S50/S51 evidence |
| Connect Four | 24 taps | 22/24 | Y WINS | S51_AGENT_C4.json |
| **Crossword** | 9 fills | **9/9** | SOLVED! | S51_AGENT_NEW_GAMES.json |
| **WordPredict** | 6 answers | **6/6** | SCORE 5/5 DONE | S51_AGENT_NEW_GAMES.json |
| **BallTap** | 35 actions | **35/35** | GOAL 3/3 WIN | S51_AGENT_NEW_GAMES.json |
| **Minesweep** | 64 taps | 2/64 (flood law, honest) | 71/71 WIN | S51_AGENT_NEW_GAMES.json |

All hash chains continuous; all via the runtime's real click pipeline
(observation → action → state-hash → re-observe).

## X. Screenshot/Achievement Gallery + README

`docs/achievements/` — 8 SHA-pinned screenshots + README; linked from the main
README's new **Achievements** section (grid of 6 game shots + chessclock/unote).
README now includes: status table (98×3, registry 355), What-Runs/Games tables
with the 4 new games, honest Dooz wording, Telegram parse-bound wording,
Repository Policy section, limitations re-sequenced (R-NEW-361 correctly marked
FIXED; Compose drawing + Telegram throughput named as frontiers).

## Y. Security Audit

- `check_secrets.sh --tree` **PASS** at final HEAD; **every** commit guarded by the
  fail-closed pre-commit hook (all PASS in-session).
- The **provided token itself never entered the tree** (`rg github_pat_` → zero
  tracked/ignored hits; token used only as a session environment variable for the
  push attempt; recommendation: **revoke/rotate it** since it was shared in chat).
- Release v0.0.6 checksums EXACT MATCH (prior session verification stands).
- No new giant logs created during the campaign (bounded /tmp logs only; nothing
  committed).

## Z. Remaining Blockers

1. **GitHub push** — invalid credential (§B). All remote finalization (push,
   fresh-clone verification, Issue #9 update, future history rewrite) sequences
   behind a valid PAT.
2. **Compose drawing pipeline** — Dooz v18/v23 blank framebuffer (R-NEW-373 +
   Compose render path) — primary runtime frontier.
3. **Telegram multi-DEX parse throughput** — parallel/chunked parsing as future
   law work; R-NEW-303 beyond.
4. **WhatsApp acquisition** — licensing-blocked.

## Final Status Classification (honest)

- **DONE (local, verified):** tree purge, META-INF resolution, tools/scripts
  documentation, 4 new games + validators + agent schemas, R-NEW-374, battery
  98/98 ×4, roadmap reconciliation, README/gallery, bloat report, security scans.
- **DONE LOCALLY BUT NOT REMOTE:** the 27-commit push (credential), Issue #9
  update (credential), fresh-clone verification (depends on push).
- **REMOTE VERIFIED (unchanged):** v0.0.6 release assets (S51 phase 0 re-check).
- **GITHUB ATTACHMENTS:** PARTIALLY-VERIFIED (API auth blocked).
- **RUNTIME FRONTIER:** Compose rendering (Dooz), Telegram parse throughput.

*Every number in this report traces to a committed artifact or an in-repo
validator; where a thing could not be verified it is written down as such.*
