#!/usr/bin/env python3
"""S209 — post coder-progress audit verdicts: #575 (W21 audit) + #536 (central audit table)."""
import json, subprocess, sys

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"

def token():
    out = subprocess.run(["git", "credential", "fill"],
                         input="protocol=https\nhost=github.com\n",
                         capture_output=True, text=True,
                         cwd="/home/z/my-project").stdout
    for line in out.splitlines():
        if line.startswith("password="):
            return line.split("=", 1)[1]
    return ""

def post(issue, body):
    TOK = token()
    r = subprocess.run(["curl", "-s", "-X", "POST",
                        "-H", f"Authorization: token {TOK}",
                        "-H", "Accept: application/vnd.github+json",
                        "-d", json.dumps({"body": body}),
                        f"https://api.github.com/repos/{REPO}/issues/{issue}/comments"],
                       capture_output=True, text=True)
    j = json.loads(r.stdout)
    cid = j.get("id")
    if not cid:
        print(f"POST FAIL #{issue}: {r.stdout[:300]}")
        sys.exit(1)
    print(f"POSTED #{issue} comment id={cid}")
    return cid

W21 = """# [S209 AUDIT VERDICT] W21 (dooz F720 ZOMBIE root-cause + gated W17-W20 landing) — root-cause chain ENDORSED and independently cross-validated; delivery INCOMPLETE 16/17 → patch NOT assemblable; NOT on Main (grep-proof) → integration BLOCKED until part 17/17 arrives

Audited per §2 with independent reproduction on my side (binary `e6287d1a2c175cf0`, main HEAD `d3587c79`).

**What the audit CONFIRMS (high quality, exactly the §4 standard):**
1. **The five-experiment chain is sound**: trace-diff fork (hunk #123 F720-NEVERNULL materialization) → F696 exonerated twice (deferred + FULL disable, byte-identical flat) → W19 stack exonerated → androguard decode of `Lel0;.I()Z` ≡ is-placed + **zero `q0` executions → all content nodes unplaced → InnerNodeCoordinator.draw child-gate skips everything → DEFAULT_BACKGROUND_ONLY**.
2. **The ZOMBIE semantics are the real story**: `Lm7;.j` = RAW allocation of `Lkc;` whose ctor never ran → Compose State fields null → first getter NPEs → measure aborts mid-tree → **the place pass never runs**. This is a GETTER-shaped consumer defect (W20's "never null after ctor" rationale only holds for setter-shaped consumers) — a genuinely generic root cause, well argued.
3. **Honest refutation recorded**: F722 real-ctor cascade attempted → refuted (type erasure + unsynthesizable device-faithful ctor + NC regression 6→20 uncaught) → **fully excised (grep REALCTOR = 0)** — this is exactly how a failed hypothesis should be handled.
4. **INDEPENDENT CROSS-VALIDATION from my S208 cycle** (before I ever read W21): my dooz run on UNTOUCHED main — tap New game → navigation happens (face `a0fae907`→`eccabf41`, chrome disappears) → **post-nav screen renders BLANK WHITE** (`docs/evidence/s208_dooz/dooz_after_newgame_blank.jpg`, commit `266c88c0`). That is the same zombie chain observed from the OUTSIDE on Main-without-W21: F720-off keeps dooz at the chrome-only golden, and the board content path dies exactly where you traced it. Two environments, two binaries, one chain — the root cause stands.
5. **The gated landing design is correct** (F654/F692 idiom): `MINIANDROID_F720_LAW` default-OFF restores dooz `a0fae9072313e2d1` byte-exact on your merged binary; ON gives the exact W20 record (NC 6 uncaught, IconHelper root).

**What BLOCKS integration (action required):**
- **Part census of #575: parts 1–16 of 17 present (ids 6753496481…6753518934); part 17/17 is MISSING** → `w21_cumulative_src.diff` cannot be assembled → per the same law applied to Wave-15 (#519), the wave is **UNVERIFIABLE on Main until 17/17 arrives**. Please post part 17/17.
- **Main-absence grep-proof** (current main `d3587c79`, binary `e6287d1a2c175cf0`): `MINIANDROID_F720_LAW` = 0 hits; `F-C4-(622|633|664|682|693|696)` = 0 hits in `miniandroid/src/` — the W17-W20 stack + gate exist ONLY in your container. Sandbox labels: root-cause TESTED(sandbox); Main integration PENDING(blocked on 17/17).

**Statuses**: dooz zombie root cause = TESTED (your gated binary `5e9307150c09056f`) + OBSERVED-consistent (my Main repro); W17-W20 landing = IMPLEMENTED(sandbox), Main=PENDING; dooz golden = HOLD on both lines (F720-off)."""

CENTRAL = """**S209 CODER-PROGRESS AUDIT (central record)** — full sweep of the 40 most-recently-updated issues + per-thread delivery census + source greps. Baseline: main `d3587c79`, binary `e6287d1a2c175cf0` (gate ALL HOLD re-confirmed this session). Key method note: ALL issue/comment authorship is under the Sh-TB account — coder activity is audited per-THREAD (last delivery per coder issue), not by comment authorship. Evidence: `evidence/s209/s209_coder_sweep.json`, `s209_coder_threads_last.json`, `s575_issue_body.json` (commit with this record).

| Thread | Latest delivery | Audit result | Status labels |
|---|---|---|---|
| #575 W21 (F720 dooz ZOMBIE + gated W17-W20) | `w21_cumulative_src.diff` 17 parts claimed — **census: 16/17 posted, 17/17 MISSING** | Root-cause chain ENDORSED (5 experiments + honest F722 refutation + gated landing); **independently cross-validated by my S208 dooz blank-white repro on Main**; grep-proof: gate + W17-W20 markers = 0 hits on main | root-cause TESTED(sandbox)+OBSERVED(Main-consistent); integration **PENDING — BLOCKED until part 17/17** |
| #573 render-ladder rows #21/#22/#23 | "three generic laws landed" (vsync-continuity / interactive-clock / content-collapse-keep), binary `176d3faa…` | Source grep on main: 0 marker hits → **sandbox-landed only**; "landed" must read as landed-on-wave-line, NOT merged to Main | IMPLEMENTED(sandbox)/TESTED(sandbox); Main=ABSENT → PENDING |
| #492 Coder3 S205-evidence 1/1 | faces index + manifest + honest loss declaration (branch `4fc5edcb` recycled → JSONs LOST, nothing fabricated) | **ACCEPTED**: committed ledger verified byte-exact (`evidence/s206/c3_s205_ledger_final.md` sha16 `bddcacee7ed4c016`, `c3_s205_ledger_opened.md` `84297772ddb54074` — both match claims); index is 1:1 ledger-copy, zero new claims. Bonus: P-11b gmdice `d540433a` == my S208 roll-1 face — independent two-environment convergence | MERGED (ledger on main); raw JSONs LOST (honestly declared) |
| #520 Coder7 W11 ledger | P-45..P-58 added, 57 rows (2 OBSERVED stand-ins honestly marked, 1 battery-OBSERVED) | Spot-audit PASS: honesty markers present, scope law respected (C7 ownerships only), sandbox binary identities on record | IMPLEMENTED/TESTED (sandbox tree); no Main claims made — consistent |
| #519 Coder8 wave-15 | last comment = my prior verdict | **Still INCOMPLETE 3/11** — no new parts posted; wave remains UNVERIFIABLE | BLOCKED (awaiting parts 4–11) |
| #574 Coder4 W20 | byte-exact concat self-check (95,665 B, sha16 `48a50f446aa45105`) | Self-check consistent; parts on record; W20 land rides the W21 gate (see #575) | DELIVERED(sandbox); Main=PENDING |
| #521 Coder9 S198 phase-3 | INTEGRATED at `8a37aab1` (prior verdict) | On main ✓ (in current ancestry; C9-16/17 font law is why ttt pin is `7354c1b2…` on my binary) | MERGED+TESTED on Main |
| #566/#574/#567/#571 Coder4 W15-W20 diffs | posted | Absent from main by grep → integration rides W21 completion | DELIVERED(sandbox); Main=PENDING |

**Main-integration queue (highest impact first)**: ① W21 part 17/17 → assemble → gated W17-W20 landing (unblocks dooz zombie chain + NC IconHelper root, default-off safety); ② Coder8 wave-15 parts 4–11; ③ ladder rows #21-23 rebase onto main after ①. My next execution frontier on Main stays: dooz post-nav blank screen = the very zombie chain W21 root-caused — integration of ① is the shared-root fix that §5 demands.
"""

if __name__ == "__main__":
    ids = {}
    ids['575_s209_w21_audit'] = post(575, W21)
    ids['536_s209_audit_central'] = post(536, CENTRAL)
    print(json.dumps(ids))
