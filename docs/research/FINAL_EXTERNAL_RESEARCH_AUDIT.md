# FINAL EXTERNAL RESEARCH AUDIT

Campaign: DEEP REPOSITORY RESEARCH & KNOWLEDGE TRANSFER
Date: 2026-09-05 · Baseline HEAD: `82334321a3f83a299131a4150bb2934ed893bcb5` (local main, clean tree at campaign start)
Law compliance: §0 exact-URL (no substitutions) · §18 discovery rule
(history-first) · §19 source-level citations · §23 provenance matrix ·
§29 zero-fabrication · §30 focused commits · §31 push verification.

---

## 1. Repository inventory (24 entries; full detail in external-repositories.md)

| Status | Count | Repositories |
|---|---|---|
| REPOSITORY_AVAILABLE + SOURCE_READ this campaign | 15 | winedroid (rickbergs, a784c0b), frameworks/base mirror (1cdfff55), ART official (6484611f), dalvik mirror, frameworks/native official (4f463a6b), qemu emu-master-dev (ae9d18d2), cuttlefish (a1162ca7), crosvm (9d4dc5f), AVF/Virtualization (175a51b3), waydroid (e7d73e7f), jadx (8f7ea4e), Apktool (baa603f), bundletool (586a43a), skydnir, DroidVM |
| SOURCE_READ via prior records + re-verified structure | 3 | droidsaw (50eb045b — README+layout this session), ARSCLib, auxten/libarsc |
| REPOSITORY_UNAVAILABLE | 1 | SimulaVR/sim-use (exact mandated URL returned 404/credential-fail after one successful listing earlier in the session; two retries failed; no substitute used) |
| REPOSITORY_URL_UNVERIFIED | 3 | AndroidRecomp, ReSource, Reveree (no identity-verifiable canonical upstream found; GitHub search only surfaced unrelated game-console "Recomp" ports) |
| Reachable, deferred | 1 | frameworks/av (media stack — below criticality line; recorded in gap analysis G10) |
| Parent project | 1 | MiniAndroid-Compatibility-Runtime (local HEAD 8233432) |

Identity-verification highlights:
- `aosp-mirror/platform_art` DOES NOT EXIST on GitHub (HTTP 404 verified);
  the official `android.googlesource.com/platform/art/` mandated by the
  campaign was used instead and cloned.
- `platform/external/qemu` default branch is frozen at 2015; the emulator
  develops on `emu-master-dev` (35.6.3 Canary, ae9d18d2) — branch fetched
  and locked.
- `rickbergs/winedroid` is confirmed PUBLIC, Apache-2.0, and is a
  DIFFERENT project from the previously recorded `winedroid.soham.sh`
  (GPL-3.0, private repo). Both are now distinct rows in the matrix.

## 2. Research totals

- Repositories studied at source level: 19
- Repositories unavailable: 1 (sim-use) · unverified URLs: 3
- Mechanisms discovered and documented with IDs:
  WineDroid 20 (WINEDROID-001..020) · AOSP 17 (AOSP-001..017) ·
  DEX 9 (DEX-001..009) · ARSC 6 (ARSC-001..006) · FONT 5 (FONT-001..005) ·
  GFX 5 (GFX-001..005) · LAYOUT 6 (LAY-001..006) · COMPOSE 3 (CMP-001..003)
  · TOOLCHAIN 4 (TOOL-001..004)
- Mechanisms transferred (knowledge + mapping, this campaign): 7
  (KT-001..KT-007 in knowledge-transfer-log.md)
- Mechanisms queued with named test plans: 14 (Q-1..Q-14)
- Implementation candidates pending decision: 12 (matrix rows)
- Deferred with reasons: 5 · Rejected with reasons: 7 · Verified-already-
  implemented (pending HEAD re-run): 4
- Campaign commits: see §7

## 3. WineDroid — useful mechanisms (all 20 in winedroid-study.md; highlights)

WINEDROID-001 typed APK entry classification + unsafe-path warnings ·
002 defensive DEX header validation · 003 per-table bounds+alignment
pre-validation · 004 MUTF-8 decoder with declared-vs-actual utf16
cross-check (NUL `0xC0 0x80`, surrogate pairs) · 005 ULEB128 5-byte/32-bit
hardening · 006 numeric multi-dex ordering law (`classes20.dex` test) ·
007 generic invoke ABI (`incoming_start = registers_size - ins_size`,
zero-fill, ins≤regs) · 008 object handles + shared field store with
allocation traces · 009 recursive linker with per-method rejection REASONS
(pc+opcode) and branch isolation · 010 external-namespace prefix law ·
011 packed-switch lowering + payload-is-data invariant · 012 throw
lowering without method poisoning · 013 Java div/rem corner semantics ·
014 sget/sput variant↔type strictness · 015 diagnostics CLI (per-DEX
count block, JSON) · 016 warning-accumulation discipline · 017
untrusted-APK posture (caps, sandbox doc) · 018 inspectable emitted
artifact · 019 tests-as-executable-spec (synthetic DEX in code) · 020
honest limitation ledger.
License: Apache-2.0 — concepts and code patterns transferable with
attribution (no wholesale import needed so far).

## 4. AOSP — useful mechanisms (all 17 in aosp-runtime-study.md; highlights)

View.measure() final-template caching + measured-dimension guard ·
resolveSizeAndState/getDefaultSize mode laws · getChildMeasureSpec 3×3
table (line-exact: ViewGroup.java L7048) · measureChildWithMargins margin
arithmetic · measureChildren GONE-skip · LinearLayout weight two-pass ·
Resources.getString/getIdentifier contracts (id 0 invalid) ·
Handler.dispatchMessage three-tier priority · Paint.Style
FILL_AND_STROKE CCW caveat · Path.FillType numeric ABI · Canvas
save/restore/clip surface · SharedPreferencesImpl read-your-write ·
Activity lifecycle root contract · ART DexFileVerifier check-order law ·
cdex detection · SurfaceFlinger/Binder boundary validation of
MiniAndroid's collapsed model.

## 5. Other projects — transferred mechanisms

- Apktool: ARSC SPARSE(0x01)/OFFSET16(0x02)/STAGED_API constants pinned;
  shared bounded-chunk-reader pattern noted (TOOL-001).
- JADX: per-chunk skip-to-end discipline + library-chunk handling;
  Apache-2.0 reconfirmed → oracle-first policy unchanged (TOOL-002).
- droidsaw: byte-exact parse→re-emit→diff preservation methodology →
  queued as ARSC round-trip harness (DEX-009).
- DaliVM: opcode hex-range tables = coverage-matrix oracle (GPL: zero
  import) (DEX-008).
- CrosVM/Cuttlefish/AVF/Waydroid/qemu: sandboxing and host/guest split
  patterns recorded for the future hardening roadmap (GFX-004, G9).
- Skydnir: release-gate methodology (already adopted in prior cycles as
  zero-skip gates; license forbids any reuse of text/code).

## 6. MiniAndroid state relative to this campaign

- Files changed by THIS campaign: documentation only —
  `docs/research/external-repositories.md`, `winedroid-study.md`,
  `aosp-runtime-study.md`, `dex-runtime-study.md`, `arsc-resource-study.md`,
  `font-runtime-study.md`, `graphics-rendering-study.md`, `layout-study.md`,
  `compose-study.md`, `apk-toolchain-study.md`,
  `external-mechanism-matrix.md`, `external-gap-analysis.md`,
  `knowledge-transfer-log.md`, this file. No runtime code was changed;
  therefore no regression risk was introduced (build state unchanged,
  verified by clean tree + prior HEAD build PASS).
- Tests added: none yet — the 14 queued items (Q-1..Q-14) each carry a
  named test plan and are the next sessions' implementation queue.
- Runtime evidence (standing, from prior campaigns, unaffected by this
  one): tictactoe_golden end-to-end run — real APK, launch board, real
  click, X-WINS board, deterministic replay; frames manifest with
  sha256 per frame in `docs/evidence/tictactoe_golden/frames_manifest.json`
  (e.g. board_launch.png sha256 `0d339d84…`, board_x_wins.png
  `510d4700…`); README embeds the runtime-produced frames
  (README L28).

## 7. Git / GitHub status

- Campaign commits (this series, local main, fast-forward on 8233432):
  1. `research: lock canonical repository inventory (exact URLs + revisions) and study WineDroid source file-by-file (WINEDROID-001..020)`
  2. `research: AOSP runtime study (AOSP-001..017) + DEX runtime study (DEX-001..009) with exact source citations`
  3. `research: subsystem studies — ARSC, font, graphics, layout, compose, apk-toolchain + mechanism matrix, gap analysis, transfer log`
  4. `research: final external research audit (§32) + worklog` (this commit)
- Remote push: the sandbox git checkout has NO configured remote
  (`git remote` empty — same condition as the prior campaign's honest
  PUSH BLOCKED record). Per §31:

```
PUSH BLOCKED
Remote:        (none configured in this environment)
Branch:        main
Local HEAD:    <see git log -1 at delivery time>
Remote HEAD:   N/A — no remote configured
Exact error:   n/a (no remote to contact)
Required user action: add the GitHub remote
  (git remote add origin https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime.git)
  and push; the commit chain is fast-forward-ready and docs-only.
```

## 8. Tic-Tac-Toe — separate report (§32 requirement)

Not re-run this campaign (documentation-only campaign; no runtime code
changed). Standing evidence at HEAD 8233432:
- APK: real fixture APK at `miniandroid/tests/fixtures/tictactoe_golden/`
  (classes.dex with game logic + assets/fonts + resources) — built by the
  fixture tool; validation script `validate_tictactoe_golden.sh`.
- Execution/UI/resources/font/measure/layout/Canvas/rendering: full chain
  evidenced in CAMPAIGN_FINAL_REPORT.md §24 stop-condition record.
- Interaction: real click → state update → X WINS board.
- Screenshots: `docs/evidence/tictactoe_golden/{board_launch,board_x_wins,
  launch_vs_xwins}.png` — runtime-produced (README-embedded).
- Deterministic replay: per-frame sha256 pinned in frames_manifest.json.
- Campaign-law note: Tic-Tac-Toe remains §24's first-class target; the
  queued Q-items (esp. Q-11 Case-F font fixture, Q-8 ARSC sparse fixtures)
  extend the SAME golden rather than replacing it.

## 9. Final principle compliance statement

The mission executed was: exact upstream repositories → actual source
inspection → concrete mechanisms extracted with IDs and citations →
MiniAndroid mapping written → knowledge preserved in-repo with provenance
→ implementation queue defined with named tests. No repository was
guessed, substituted, or silently dropped; no implementation was claimed
without evidence; no push was claimed without remote verification.
