# CONT-6 — Required Final Table + Reasoned Verdict (Issue #377)

Wave: CONT-7 WAVE 3 (also executes CONT-6's runtime-verification duties)
HEAD at execution: `2938a888` (code base) → wave-3 engine edits
FINAL BINARY SHA16: `daeb0aa8daaec2b3` (deterministic rebuild of wave-2's
`5006834b2d2ae63b` first — byte-identical, proving clean repro — then +3
generic laws F-NEW-253/254/255)
SKILL SELFTEST: 13/13 PASS · LAW-001: zero census flips (ELF e_machine
from real APK bytes)

---

## 0. SNAPSHOT PROTOCOL PRINTOUT (mandatory per Issue #377)

**Snapshot consumed this run: NONE — the archive bytes are not readable in
this container.** The canonical snapshot per the Issue contract is
`MiniAndroid_Root_Audit_Archive (1).zip`
SHA-256 `d717e9c745609fdf3ca11eb5d60649910089c9e2ca1d2ad942c22f4712ad7931`
(2,171,810 bytes, audit 2026-10-05, audited HEAD `f8d4088b`). The container
reset lost the local artifact; only the Issue text (the stable contract)
survives. **Consequence, honestly enforced:** Phases 1 (per-record forensic
reconciliation) and 2 (semantic clustering) of the 5,976 records were NOT
performed, because they cannot be performed against bytes that are absent.
No fabricated per-record numbers appear anywhere in this table. The
`research/external-root-kb/current/MANIFEST.md` records the snapshot
history and the re-supply requirement.

## 1. REQUIRED FINAL TABLE

| Metric | Count | Basis |
|---|---|---|
| External raw records | 5,976 | Contract row (Issue #377); bytes NOT re-verifiable this container |
| VERIFIED-NEW source findings | 5,434 | Contract row; NOT runtime-proven (the audit's own report says registry roots were catalogued, not re-verified; 250 rows have empty `test_apks`) |
| Existing (VERIFIED-EXISTING) | 274 | Contract row |
| Existing (PARTIAL-EXISTING) | 266 | Contract row |
| REJECTED | 2 | Contract row |
| Semantic clusters | **NOT COMPUTED** | Phase 2 requires the archive; absent |
| A existing / B evidence-only / C missing sub-law / D genuinely new / E environment / F source-only / X duplicate | **NOT COMPUTED** | Phase 1 requires the archive; absent |
| Runtime-proven new roots **this wave** | **3** (F-NEW-253, F-NEW-254, F-NEW-255 — all from LOCAL runtime evidence: source→bytecode→runtime traces→generic fix→synthetic 12/12→real APK→3-run→full regression) | This wave |
| Roots classified (first divergence proven, fix owned by next wave) | **1** (F-NEW-256 Compose draw-ops frontier) | This wave |
| Roots imported FROM the external KB | **0** | Hard rule honored: nothing enters the registry from the KB without runtime proof |
| Real APK consumers exercised this wave | **13** (dooz ×many, chess, sudokusolver, 6 games ×3 runs each, gate-A probe, W3 synthetic probe, 5 anchors ×3) | This wave |
| Independently improved games | **0** (the six games were already REAL_APP_CONTENT — they re-validated, they did not improve) | Six-game re-validation |
| Independently improved apps | **1** — dooz: uncaught exceptions 3 (wave 1) → 1 (wave 2) → **0** (this wave); first fully clean composition | This wave |
| Regressions | **0** (anchors 5/5×3 byte-identical incl. dooz `d602648e…`; goldens 4/4; gate A 97/0/2 after fixture restoration; negatives 19/19; reinstall 8/8; loading ALL PASS; uninstall ALL PASS; skill 13/13) | Battery |

## 2. SIX-GAME CLAIM VERDICT (Phase 4) — **CONFIRMED 6/6**

The external audit claimed REAL_APP_CONTENT for six built-in games. All six
were re-validated **independently at current HEAD** — fresh install, 3
clean runs each, byte-identical screenshots, F-NEW-233 frame-truth verdict
+ app-owned pixel gate (`evidence/cont6/six_game_validation.json`):

| Game | Package | APK SHA-256 (prefix) | 3-run screenshot SHA16 | Verdict |
|---|---|---|---|---|
| 2048 | com.miniandroid.g2048 | (full SHA in JSON) | `7ad9a8bdefba539b` ×3 | **REAL_APP_CONTENT** |
| mini-tetris | com.miniandroid.tetris | — | `26ccfce917c0e24c` ×3 | **REAL_APP_CONTENT** |
| minicraft | com.miniandroid.minicraft | — | `ce27f331770f6979` ×3 | **REAL_APP_CONTENT** |
| snake-deluxe | com.miniandroid.snakedeluxe | — | `34a712689ce66e58` ×3 | **REAL_APP_CONTENT** |
| snake-neon | com.miniandroid.snakeneon | — | `477bb95e1e6398ce` ×3 | **REAL_APP_CONTENT** |
| tictactoe-deluxe | com.miniandroid.tictactoedeluxe | `d04d92ea…` | `0a1cd01bb490fdc5` ×3 | **REAL_APP_CONTENT** |

The audit's six-game claim is a **current-HEAD fact as of this wave**. The
honest caveat: five of the six titles are OUR OWN S80-archive builds
(source trees in `games/` + `upload/s80_games`), not third-party store
APKs — the claim is confirmed for what the archive actually contains.

## 3. REASONED VERDICT ON THE HUGE ROOT SET (the user's question)

The user asks: "we have a huge set of roots — confirm them, with
reasoning." The reasoned answer has four parts:

**(a) What is CONFIRMED by internal reasoning (no bytes needed).** The
contract's own arithmetic is self-consistent: 5,434 VERIFIED-NEW +
274 VERIFIED-EXISTING + 266 PARTIAL-EXISTING + 2 REJECTED = 5,976 = the
stated total, with 5,976 unique IDs and 40 domain files; `head` empty in
rows is consistent with the audited-HEAD provenance living in the archive
report. The label discipline the audit applies (VERIFIED-NEW ≠ runtime
proof; raw rows ≠ roots) is **methodologically sound and is CONFIRMED** —
it matches this project's own hard-won law that source-only findings are
hypotheses until a runtime divergence proves them.

**(b) What is CONFIRMED by independent runtime re-execution.** The KB's
most consequential runtime claim — the six games — was re-validated at
current HEAD and **holds 6/6** (§2). This is the only part of the KB that
can be confirmed without the archive bytes, because the games are locally
buildable. It is now re-proven with 3-run byte-identity per title.

**(c) What is NOT confirmed — and must not be pretended.** The 5,434
per-record classifications (A–F/X), the semantic-cluster collapse, and any
"how many of the 5,434 are already fixed at HEAD" estimate CANNOT be
confirmed this container: the archive is absent. Fabricating those numbers
would violate the Issue's hard rules (no registry pollution, no
source-only promotion). The honest status is **PENDING-RESUPPLY**; the
re-supplied archive will be SHA-checked against the contract row before
any per-record work.

**(d) The KB's real value, confirmed by this wave's practice.** Three new
runtime roots were closed this wave (F-NEW-253/254/255) — none came from
the KB; all came from the runtime itself. That is the KB's intended role
per the Issue: a **searchlight** that directs attention, not a worklist.
The structural claim "5,434 records collapse into far fewer semantic laws"
is CONFIRMED IN SPIRIT by our own registry: 562 roots cover hundreds of
observed API/method-level faces via ~40 semantic law families
(platform-class hierarchy, collection shadow, CAS/field identity,
ServiceLoader discovery, …). The KB's families and ours rhyme; the
per-record merge is exactly what the Issue forbids.

**RECOMMENDATION: PARTIAL-IMPORT (runtime-verified parts) /
DISCOVERY-ONLY (the rest) — and concretely:**

1. The six-game runtime claim: **CONFIRMED** (adopted as current-HEAD fact).
2. The KB as an artifact: keep at `research/external-root-kb/` per the
   access contract, **re-supply the archive** (re-attach to Issue #377 or
   drop into the manifest directory) before Phases 1–3 run.
3. Per-record import: **REJECT until Phase 1/2 + runtime proof exist**;
   promote only C/D-class candidates through the six promotion gates
   (registry search, evidence-history search, HEAD check, semantic
   duplicate check, external provenance, separate runtime proof).
4. This wave's 3 runtime-proven roots + 1 classified frontier were
   registered the normal way (from local evidence), keeping the registry
   clean at **562 roots**.

## 4. STALE / DUPLICATE ESTIMATES

Not computable without the archive (recorded honestly in §1). The one
stale-reference check that WAS possible: the Issue's audited HEAD
`f8d4088b` predates the current HEAD by many waves — any KB row describing
engine behavior at `f8d4088b` must be re-verified at HEAD before
promotion; the six-game claim was so re-verified and survived.
