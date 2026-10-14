# CONT-18f — ORPHAN FINDINGS AUDIT (discrete → dispositioned → usable)

Directive: *"بررسی بکن هر چیزی پیدا کردیم ولی به صورت گسسته هستن و ارتباطی با
فیکس ها ندارن و بلا استفاده رها شدن … اونا رو هم درست بکن"* — audit every
finding that ended up discrete/isolated, disconnected from the fix lines, and
abandoned unused; **fix them all**: either integrate into the main line or
dispose explicitly. No finding is allowed to float.

Method (evidence-first, constitution law): every row below names its source
artifact and its disposition. Statuses come from the task-list vocabulary
only. Nothing was "closed" without runnable evidence; nothing was inflated.

---

## 1. Where discrete findings lived (inventory sources)

| Source | Contents |
|---|---|
| `root_registry.json` (576 rows after this wave) | every registered root with a status from the vocabulary |
| `evidence/cont17/ijk_census.json` | 217 open rows classified by runnability at HEAD (37 IMPLEMENTED / 110 PARTIAL / 72 UNPROVEN) |
| worklog + CONT-8/9/10/17/18 ledgers | recorded loose ends that never became registry rows or fixes |
| `evidence/cont18/*` | T-01 baseline, collection audit, LAW-C/E/F determination, F-217 first-divergence |

The registry IS the disposition ledger — the audit's job is to verify there
are no findings that live OUTSIDE it (or outside an explicit evidence doc),
and to convert the recorded-but-unused ones.

---

## 2. Recorded loose ends (worklog-level orphans) → dispositions

These were findings recorded in worklogs/evidence docs but never converted
into a registry row, a fix, or a tool. Each is now dispositioned:

| # | Orphan (source) | Disposition | Where it lives now |
|---|---|---|---|
| L1 | **Pre-push guard empty-staged-list quirk** — recorded twice (CONT-8 W4, CONT-9 W5): "empty staged list → guard greps recursively into .git/ and hits .git/config's embedded remote PAT — fix candidates recorded for the next engine-touching wave" | **FIXED THIS WAVE** (main-code fix). Root cause verified live: GNU `grep -r` with NO path operands recurses into the CWD. Fix = empty scan set is a NO-OP in `scan_one_pattern` (fail-closed unchanged). Selftest extended with the empty-list law (plant dummy token in CWD, prove no-operand scan does not see it): `selftest: empty-list scan is a NO-OP (correct)`, all 7 detection rows + 5 FP rows still PASS. | `scripts/security/check_secrets.sh` (code + selftest arm); this doc |
| L2 | **T-01 remaining exposure: Compose tap frontier** — "the Compose tap pipeline answers target=0 (`run/cont18/t01_run_tap1`), which gates T-09/T-10" (committed T-01 doc). Recorded as exposure, never registered as a root | **REGISTERED THIS WAVE as F-NEW-267 (CLASSIFIED)** + LIVE reproduction at the reproduced binary: `run/cont18f/tap1/run.log` `[F117-TAP] frame 15 DOWN (540,960) target=0`; post-tap screenshot sha16 `d602648e8e401895` = dooz anchor (byte-identical = zero state consumed). Law surface + hard dependency (F-265 measure placement) recorded in the row. | `root_registry.json` F-NEW-267; `run/cont18f/tap1/` |
| L3 | **CONT-17 census (217 open rows)** — "feeds the next engine-wave queue" but no queue mechanism existed; the census stayed a dead JSON | **USABLE THIS WAVE**: `scripts/findings_queue.py` merges registry+census disposition law into a deterministic ranked queue (rank = priority → status class → id). Current output: **255 queued / 321 terminal** of 576 rows; queued by priority P0=32, P1=53, P2=65, P3=105. The "45 DEFERRED visibility" law is now mechanical (P3 rows are always first-class queue rows). | `scripts/findings_queue.py`; `evidence/cont18f/findings_queue.{json,md}` |
| L4 | **CONT-18 campaign fixes never re-proven live in a clean container** — LAW-A..F rows carried recorded evidence only | **REPRODUCED THIS WAVE**: clean rebuild reproduces the recorded CONT-18 binary **byte-identically** (`8ee839e718877216`); fcol probe rebuilt from fixture (`run/cont18f/probes/`) and run live: **fcol 18/18 PASS** (K1–K18, was 3/18 at CONT-18 baseline — the campaign's concrete code impact); anchors 6/6 ×3 = **18/18 MATCH byte-identical**. | `run/cont18f/probes/probe_report.json`; `run/cont18/anchors/` |
| L5 | **W3 ladder Probes C/D/E "not buildable (no kotlinc)"** (CONT-8 W4) | **RESOLVED BY TOOLCHAIN**: CONT-12 installed kotlinc 2.1.20 and built real Kotlin Compose probes (oracle12). No longer a gap; nothing to fix. | CONT-12 ledger; oracle toolchain in tree |
| L6 | **opencalc anchor change** `a976d2f9` (CONT-10 drift flag) | **RESOLVED**: the new render is the recorded anchor since CONT-10; this wave reproduces it ×3 byte-identically. | anchors battery |
| L7 | **Telegram run2 empty screenshot (120 s wall-cap flake)** (CONT-18 baseline) | **OBSERVED-RECORDED** (explicit): harness wall-clock cap, 2/3 + flake recorded honestly; not a runtime finding; the anchors script's telegram part records consistency runs. No registry row (no root). | `CONT18_BASELINE.md`; anchors script |
| L8 | **FishRings parcel calls unreachable at first launch — "harness lacks lifecycle-save trigger"** (CONT-8 §14) | **DEFERRED (scope: harness)**: requires a lifecycle-save event in the canonical harness; recorded as harness backlog item in the queue tool's P3 class via the F-150/scheduler rows it relates to; no runtime root. | this doc; harness backlog |
| L9 | **drawBitmap in-memory bitmaps "recorded-but-0-px"** (CONT-8 W4 ladder) | **SUPERSEDED-BY-EVIDENCE**: the frontier moved twice since (F-256 → F-265); the in-memory-bitmap face is folded into the draw-path family rows (F-NEW-256/F-265) which remain CLASSIFIED with the current first divergence. Re-opens only when the draw frontier reaches bitmap content. | F-256/F-265 rows |
| L10 | **FairyMahjong APK lost in reset** (CONT-8: F-243/244 SUPERSEDED + ARTIFACT-LOST, re-supply pending) | **BLOCKED-APK-ABSENT** (explicit): cannot re-verify without the artifact; KB archive still absent in-container. Stays recorded, not silently dropped. | CONT-8 ledger; registry F-243/244 rows |
| L11 | **f259g row-L (11/13 → 12/13)** (CONT-16/17) | **CLOSED-AS-DOCUMENTED** (CONT-17 W4): test-expectation artifact vs F-068 most-derived law; no suppression; 12/13 honest remains the recorded state and is reproduced by the probes battery. | CONT-17 W4 evidence |
| L12 | **fcol K14 toString `@hash` cosmetic sub-face** (task-list row 21) | **PENDING** (explicit, unchanged): recorded as LAW-C sub-face, cosmetics only; no semantic row depends on it. | `CONT18_TASK_LIST.md` row 21 |
| L13 | **F-238 diag false-positive (SET POISON on legal string sets)** | **FIXED** (CONT-18 LAW-A, commit `e41d6db3`): predicate fixed; re-proven live this wave inside fcol 18/18. | LAW-A evidence |
| L14 | **fcol probe APK absent from clean container** (previous builds were container-local `run/w7/*` artifacts) | **REBUILT THIS WAVE** from the committed fixture with the committed build script: `bash scripts/cont11_build_fcol.sh` → `run/cont18f/…` chain, apk sha16 `d03cc97f82f47c55`. Note (honest): probe-apk zip bytes are not cross-container deterministic (zip timestamps); the probe ROWS (K1–K18 verdicts) are the contract, not the zip sha. | `run/cont18f/`; build script committed |

## 3. Registry-level dispositions (not orphans, verified non-floating)

| Class | Count (after this wave) | Verification |
|---|---|---|
| Terminal (ROOT-CAUSED-FIXED / VERIFIED-* / TESTED / IMPLEMENTED+TESTED / NOT-APPLICABLE / REJECTED* / SUPERSEDED* / ROOT-CAUSED-CLOSED / USED_BY_EXECUTION) | **321** | each carries an evidence pointer; spot-audited in CONT-17 W5 census |
| Queued with explicit status (OPEN/PENDING/BLOCKED/CLASSIFIED/PARTIAL/UNPROVEN/IMPLEMENTED/…) | **255** | every one appears in the ranked queue (`findings_queue.py`) — visible, prioritized, non-floating |
| REJECTED/UNVERIFIABLE friend findings (CONT-15 F-266..277, F-236) | included in terminal | individually dispositioned with measured evidence (CONT-15 ledger) |

Status counts (post-registration): 125 ROOT-CAUSED-FIXED, 110 PARTIAL,
72 UNPROVEN, 56 VERIFIED-CORRECT, 49 VERIFIED-FIXED, 42 NOT-APPLICABLE,
37 IMPLEMENTED, 23 IMPLEMENTED+TESTED, 16 RESEARCHED-NOT-IMPLEMENTED,
12 SUPERSEDED-BY-EVIDENCE, 7 USED_BY_EXECUTION, 5 OBSERVED-FAIL, 4 OPEN,
4 CLASSIFIED, 3 ROOT-CAUSED-CLOSED, 3 VERIFIED, 2 REGISTERED, 2 PENDING,
2 OBSERVED, 1 BLOCKED, 1 TESTED — total **576** (F-NEW-267 is the new
CLASSIFIED row).

## 4. This wave's conversions (what "fix the unused findings" means concretely)

1. **Binary reproducibility** — clean cold rebuild reproduces the recorded
   CONT-18 binary `8ee839e718877216` byte-exactly (`build/miniandroid`).
2. **LAW-A..F cumulative impact proven live** — fcol **18/18** (K1–K18) at
   that binary, vs 3/18 recorded at the CONT-18 baseline. This is the
   concrete, runtime-visible impact of the campaign's main-code fixes.
3. **Zero-drift regression** — anchors 6/6 ×3 = 18/18 MATCH byte-identical.
4. **L2 → F-NEW-267** registered with live tap evidence (+1 row, 575→576).
5. **L1 → guard fixed in main code** with a permanent selftest law.
6. **L3 → findings queue tool** committed; the census became a living,
   ranked work order (255 queued rows, P0 first: F-NEW-156, F-NEW-157,
   F-NEW-265 …).

## 5. Laws going forward (so nothing floats again)

- Every new finding MUST land in `root_registry.json` with a status from the
  task-list vocabulary in the same wave it is discovered (T-01's tap exposure
  floated for one wave — F-NEW-267 closes that class of drift).
- Every recorded "fix candidate for the next wave" MUST either be fixed or
  get an explicit DEFERRED row; two-recording-without-action (the guard
  quirk) is the failure mode this audit removes.
- `scripts/findings_queue.py` is the single visibility mechanism: the queue
  is regenerated whenever the registry changes, and DEFERRED/P3 rows stay
  first-class members of it (the 45-DEFERRED visibility law, made mechanical).
