# CAMPAIGN FINAL REPORT — REUSE-FIRST MAXIMUM PROGRESS / CODE-MINIMIZATION

Session: 2026-09-05 · Final HEAD: `4d822256` (main) · Base HEAD: `380f654a`
Prior campaign report (Deep Compatibility, Task 8+9):
`docs/CAMPAIGN_FINAL_REPORT.md` (preserved unchanged; this file supersedes
it as the newest campaign record).

## Repository

```text
HEAD:         4d822256
Branch:       main (worktree clean)
GitHub:       https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime
Remote main:  ad95d92876a355a719d2a8959053f8a47c2b1e79 (unrelated rebuilt local history)
Push status:  PUSH_BLOCKED — no credentials available in this environment
              ("could not read Username for 'https://github.com'"; gh CLI,
              ~/.ssh, ~/.netrc, token env vars all absent — probed fresh)
Unpushed:     31 local commits (recovered-history line + this campaign);
              remote 394-commit line preserved via archive/origin-main-ad95d928
```

## Verified execution (all on CURRENT HEAD, evidence-first)

| Requirement | Status | Evidence |
|---|---|---|
| Real APK reliably loads | PASS | fixture built by REAL toolchain (aapt2 8.13.2 + ECJ + D8 8.3.37), binary manifest/AXML/resources.arsc parsed by runtime |
| Real APK produces visible pixels | PASS | `golden_helloworld.png` 1080×1920, SHA256 `a61f5b22…`; tictactoe 10-frame sequence |
| Real APK receives real input | PASS | tictactoe 9/9 clicks via real DEX listeners |
| Tic-Tac-Toe visible board (§16) | PASS | marks in cells 2..8 with >100 px glyph ink each; "X to move"→"O to move"→"X WINS"; frozen frames byte-identical |
| Hello World resource-backed (§36.E) | PASS | 3 display strings in resources.arsc, ABSENT from classes.dex (byte search; permanent gate) |
| Deterministic replay | PASS | run A vs B byte-identical (both goldens); APK builds byte-deterministic (1980 epochs) |
| Corpus on current HEAD | PASS | simplestopwatch / gmdice / microtimer exit 0 + screenshots, SHA-verified downloads; gmdice visually verified |
| Automatic gate | PASS | `scripts/run_test_battery.sh` → 11/11 stages ALL PASS (build, 3 links, 96 semantic, mutf8 10/10, 2 goldens) |

APK SHA256 `3cf76fb7…` · DEX SHA256 `039e18ed…` (full §28 record:
`docs/evidence/GOLDEN_HELLOWORLD.md`).

## Research

- Repositories studied (this campaign, cumulative docs): 36 rows —
  `docs/research/GITHUB_RESEARCH_INDEX.md` (§26 permanent index, every
  repository exactly once, append-only).
- NEW REUSED-IMPLEMENTED this session: **aapt2** (Google Maven
  8.13.2-14304508, Apache-2.0) — the canonical Android resource compiler;
  replaces any hand-written binary AXML/ARSC generator with ZERO new
  format-writer LOC in MiniAndroid; R.java generation closes the
  Java↔ARSC id loop.
- Repositories rejected (kept): AOT C-emission pipeline (WineDroid),
  VM/container architectures (Waydroid/DroidVM/crosvm/Cuttlefish/AVF),
  RRO overlay model, sohzm/winedroid (different project).
- Unavailable / unverified (honest records): sim-use
  (REPOSITORY_UNAVAILABLE), AndroidRecomp / ReSource / Reveree
  (URL_UNVERIFIED — never guessed).

## Code reduction (§28)

| Metric | Before session | After session |
|---|---:|---:|
| UTF-16LE→UTF-8 encoder copies | 5 (1 buggy) | **1** (`mutf8::utf16le_to_utf8`) |
| SLEB128 reader copies | 2 (both UB-prone) | **1** (`mutf8::read_sleb128`, hardened) |
| ResStringPool chunk-parser copies | 3 (1 sequential-walk bug class) | **1** (`resources/string_pool.cpp`) |
| MUTF-8/ULEB128 copies (prior session) | 3 | **1** |
| Production LOC | — | **−294** (git-verified per commit) |
| Regression test volume | mutf8 7 windows; golden 18 checks | **mutf8 10 windows; golden 26 checks** |
| Bug fixes as consolidation side effects | — | manifest non-BMP double-encoding (FIX); BLOCKER-006 class dead; SLEB UB dead |
| Binary-format writer LOC written from scratch | — | **0** (aapt2 reused) |

Success shape §28 achieved: functionality UP (resource-backed real-APK
chain + §36.E gate) while duplicated implementation LOC went DOWN.

## Maintenance reduction (§29)

- One canonical decoder per format: DEX strings, DEX varints (signed +
  unsigned), Android string pools (all three consumers), UTF-16→UTF-8.
- One fixture builder (outer stale copy demoted to shim), one battery
  gate, one APK-diff oracle pattern (pixel byte-identity runs).
- Two more external mechanisms pinned as permanent discriminators
  (WineDroid 007/011, prior session) + golden gates now pin the FULL
  resource chain — future Coder sessions inherit machine-checked laws,
  not tribal knowledge (§31).

## New findings (FIND-*)

- FIND-REUSE-002 — UTF-16LE→UTF-8 ×5 → 1; manifest surrogate bug fixed.
- FIND-REUSE-003 — SLEB128 ×2 → 1; 5th-byte UB eliminated; legacy
  truncation semantics preserved (FIND-EXC-TRUNC queued).
- FIND-REUSE-004 — ResStringPool ×3 → 1; BLOCKER-006 class dead.
- FIND-GRAVITY-VERTICAL — LinearLayout container gravity vertical axis
  top-aligns vs AOSP (visible in old AND new goldens; queued for P0-9).
- FIND-EXT-AAPT2-002 — D8 8.3.37 rejects bare directory program input
  (classes.jar packaging is required; documented in builder).
- Maintenance leads recorded, NOT implemented (honest): BitmapFont vs
  TextShaper dual text path (= standing R4 item); dalvik_engine.cpp
  813 KB hotspot; dead experiment chain dex_interpreter{,_v2,exp018}
  (~160 KB, zero live refs, exp019 build script keeps it alive).

## Remaining blockers

1. PUSH_BLOCKED — no GitHub credentials in environment; all evidence
   committed locally with exact error records. 31 commits awaiting push.
2. COMMENT_BLOCKED — same cause; comment texts pre-drafted in
   `docs/research/GITHUB_EVIDENCE_INDEX.md`.
3. FIND-GRAVITY-VERTICAL open (layout engine vertical gravity).
4. BitmapFont retirement (R4) open — two text measurement paths remain.
5. res/font corpus coverage still open (no corpus APK carries res/font;
   synthetic-ARSC fixture pending — unchanged from prior report).
6. Telegram-class apps remain BLOCKED (prior campaign record stands).

## GitHub evidence

For this campaign's milestones: no comment URLs exist (COMMENT_BLOCKED);
commits are the evidence of record until credentials exist:

```text
a3c3aded  feat(golden): resource-backed Hello World — §36.E (26 checks)
e69bc496  refactor(primitives): FIND-REUSE-002/003 (UTF-16 5→1, SLEB 2→1)
4d822256  refactor(pools): FIND-REUSE-004 (ResStringPool 3→1)
```

Recovery instructions for a credentialed session:
`docs/evidence/PUSH_BLOCKED.json` (push archive branch first, then
`--force-with-lease` main, then post the pre-drafted comments).
