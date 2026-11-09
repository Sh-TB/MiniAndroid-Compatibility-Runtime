## THE KNOWLEDGE TRANSFER LAW (standing governance — registered by user directive, 2026-11-08)

**Who this binds**: every contributor coder (Coder 2/3/4/6/8/...) posting work onto this repository.
**Authority**: the repository owner's directive. This law extends `.agent/CODER_REQUEST_PROTOCOL.md` (§ completion ledgers, § evidence standard) with the TRANSFER COMPLETENESS requirement. It does not replace that protocol; both apply.

---

### Law K-1 — AN ISSUE IS THE COMPLETE TRANSFER, OR IT IS NOTHING

Every issue that reports work MUST be **self-contained**: the main coder must be able to **rebuild, re-run, re-verify, and land** the work **without asking a single question**. A described-but-unattached patch, a referenced-but-missing log, a verify step without its exact command — each of these is a protocol violation, not a style problem.

**The motivating failure (real, this repository)**: issue #564 (W16, Coder-4) reported a 2030-line patch `w16_laws.diff` with sha16 `b729820a1f8202b1`, tip `6d0ea86`, nine laws, measured 4APP results — and **the diff itself was never attached**. The main coder cannot land what cannot be applied. Nine verified laws sat unlanded because the transfer was incomplete. This law exists so that never happens again.

### Law K-2 — THE PATCH MUST BE IN THE ISSUE, ALL OF IT

1. The **full diff** goes into issue comments as fenced `diff` blocks — every part, in order, nothing elided, no "see previous issue" shortcuts for hunks on which the wave depends.
2. Every diff block states: **base commit** (the main it applies on), **tip commit** (the branch head it produces), **line count**, and **sha16** (`sha256sum file | cut -c1-16`).
3. If the wave re-lands earlier waves' unlanded commits, the diff must be **cumulative** — one diff from the stated base to the final tip, so a single `git apply` reproduces the whole wave.
4. `git apply --check` on a clean tree at the stated base commit MUST be verified by the author before posting, and the verification stated in the issue.

### Law K-3 — CONTENTS ARE PLACED ONLY BY THE MAIN CODER

Contributor tokens are scoped **Issues: RW** (no `contents:write`). That is policy, not accident: repository Contents (commits, files, evidence directories) are placed **only by the main coder**, who reviews and lands contributor patches. Contributors:
- never push branches or commits to this repository;
- transfer patches as issue comments (Law K-2);
- may write evidence under the shared sandbox layout (`evidence/<wave>/`) for the main coder's intake, and must reference every such path explicitly (file name + one-line content summary + the log that produced it) so the main coder can commit it.

### Law K-4 — VERIFY COMMANDS ARE EXECUTABLE TEXT, NOT PROSE

Every claimed result carries its exact reproduction command, e.g.:
```
miniandroid/build/miniandroid run --execution-mode real-dalvik --data-root <store> \
  -o <rundir> --package <pkg> --seconds 40 --trace
grep -c "FATAL\|Uncaught" <rundir>.console.log     # expect: 0
grep "F-C4-62x" <rundir>.console.log | head         # expect: the law's trace line
```
plus the **expected output** and the **observed output**. "Verified" without a runnable command + expected/observed is a claim, not a transfer.

### Law K-5 — ENGLISH ONLY

Issues, comments, titles, labels, evidence filenames: **English only, always**. No Persian, no other natural language in any public artifact — issues are visible to every visitor.

### Law K-6 — HONEST STATUS PER REQUIREMENT

Every numbered requirement in the wave gets a status from the CODER_REQUEST_PROTOCOL set (IMPLEMENTED / TESTED / OBSERVED / PARTIAL / BLOCKED / PENDING / SUPERSEDED) with evidence. Silent scope reduction is a violation: if a planned law did not land, the issue says so and says why.

### K-7 — SELF-CHECK BEFORE POSTING (the author's checklist)

- [ ] base commit stated and is a real commit on `main`
- [ ] full cumulative diff attached, parts in order, line count + sha16 stated
- [ ] `git apply --check` verified on the stated base
- [ ] build command stated (exact flags)
- [ ] per-app verify commands + expected + observed
- [ ] regression battery + goldens run and stated
- [ ] every evidence path listed with a one-line summary
- [ ] every wave requirement has a status
- [ ] English only; signed with the coder number

---

### Immediate application of this law (Coder-4, this wave)

- Issue #564's missing `w16_laws.diff` will be **reconstructed, re-verified on current `main` (`9bc2a115`), and attached in full** as a comment there — closing the K-1 gap for W16.
- The unlanded W15 remnant (the `android_shadows.cpp` hunk of `w15_laws.diff`, sha16 `16d989f25c60290f` — applies clean on `d3a8d0e`, still absent from `main`) is re-carried in the same cumulative diff.
- All future Coder-4 waves carry the K-7 checklist, checked.

— Coder 4
