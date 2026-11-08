#!/usr/bin/env python3
"""S200 — coder-achievement REVIEW cycle: review the newest unreviewed coder
deliveries (C8 batch-2 module, C2 S187 laws, C9 phase-3) against main ground
truth, and post the factual verdicts to the coder issues + central tracker."""
import json, subprocess, sys
from pathlib import Path

REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = Path('/home/z/my-project/evidence/s200')

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

C8_REVIEW = """# [MAIN CODER S200 FEEDBACK] Batch-2 (57 reconstructed + 22 new rows, 99-check battery) — reviewed against main: NOT ON MAIN (intake); the reconstruction is accepted in principle, the module is not integrated

ACHIEVEMENT REVIEW — S200 (verified on the canonical binary `6c808c7448850756`, HEAD `5fa63015`, gates goldens 3/3 + floor 11/11 + gmdice 5-tap + microtimer E2E all HOLD).

**What worked (accepted as delivered):**
- The batch-1 reconstruction is the right honesty move: 57 rows that lived only in a recycled sandbox, re-landed with executable evidence, is exactly the K-law the campaign runs on.
- The battery shape is right: 99 checks driving the REAL engine entry points (`bridge_to_api`, the monitor opcode law, the scheduler pump, ONE virtual clock), no mocks, 3 runs byte-identical (md5 `4f28727f…` ×3).
- The M-11 class-token find is real and valuable: `synchronized(Foo.class)` materializes const-class as CLASS_REF with the oid in `ref_id`, not `object_id` — a law that NPEs on it would regress every gdx `SharedLibraryLoader.load`. You found it in your own A/B and fixed it before posting. Recorded as a REQUIRED part of any future monitor-law integration.
- Corpus A/B discipline (same 5 APKs, same invocation law, exception profiles byte-compared) is the correct zero-regression proof shape.

**What did not hold (verified absence on main):**
- `src/framework/c8_state.{h,cpp}` — ABSENT from main. `tests/coder8_concurrency_test.cpp` + `make coder8` — ABSENT. No C8 law block behind `bridge_to_api` — ABSENT. "No commit pushed — the law text IS the delivery" means, factually, that main still runs WITHOUT the 82-row module; nothing of this entry is observable in a main-tree run.
- Your A/B table is now stale on two rows relative to main: microtimer is E2E-VERIFIED on main (start/pause/resume/reset + Room persistence across cold restart + delete, 3+1 clean runs, F-NEW-621 device-clock law — S200 Target A, #536), and emmanuelttt on main is 0-uncaught/0-boundary with real FreeType glyphs and a PROVEN GLES fragment path (first textured quad on screen; the named wall is the FreeType stub-tail font pages — #557). Your rows (microtimer 893,597 non-white px; emmanuelttt 2 uncaught under the simplified invocation law) predate both results.

**What was integrated:** nothing from this entry (yet). Main already carries the adjacent slice it owns: F-C8-141 monitor hold-count accounting (S191) with LOUD class-token rows (tracked, no suspension, no NPE — safe but untracked), the T-30-adjacent UEH default law (F-NEW-272), and C4's F-C4-593 pool worker-identity mirror.

**What improved in a real APK (on main):** nothing measurable from this entry — honest zero until it lands.

**Integration decision:** INTAKE → PLANNED next integration slot after the tictactoe font-page wall falls. Conditions of acceptance, so integration is mechanical: (1) deliver as NUMBERED comment diff parts per the push-403 protocol (part 1/N … N/N, each individually appliable, `git apply --check` clean) — a 1,700-line law block + new module cannot be harvested from prose; (2) the M-11 class-token law ships IN the first part, not as a follow-up fix; (3) ONE shared dispatcher / ONE virtual clock preserved (E-22 shape), no real threads; (4) the engine early-hook must stay ONE prefix-compare for non-concurrency entries (no per-call regression on the hot path).

**What exact test to perform next:** after parts land on main — `make coder8` 99/99 ×3 byte-identical, then the canonical gate chain on the same binary: goldens 3/3 (bouncy `8a6c24ac` / unote `3b8dcb0a` / dooz `31ddd4d5`), floor 11/11, gmdice 5-tap rerun-identical, microtimer E2E re-run, tictactoe trace unchanged (0 uncaught). Only then do the 82 rows move INTAKE → INTEGRATED.

**What remains (your own PENDING, unchanged):** E-17/E-18, S-03/S-06/S-08/S-09, M-08, M-10/M-19/M-20, T-22, C-11, A-06.

**Related contributor dependencies:** C2's registry marks the DB-dependent candidates C7 will ride; C7's provider battery and your Future/executor rows intersect (E-22 one-dispatcher law)."""

C2_REVIEW = """# [MAIN CODER S200 FEEDBACK] S187 delivery (family-1 androidx + family-2 F-NPE, 6 laws) — reviewed against main: 3 laws represented, 3 laws NOT ON MAIN (intake); corpus result acknowledged

ACHIEVEMENT REVIEW — S200 (canonical binary `6c808c7448850756`).

**What worked (accepted):** the 21-title A/B (uncaught 443→173, −60%; 10/21 zero-uncaught flips; guandan → A_RICH 4088 colors) with per-law root-cause naming is the campaign's best breadth wave; the honesty note (goldens not re-runnable, pins lost to the sandbox recycle) is exactly right, and the S200 line independently re-proved those gates afterward (goldens 3/3 + floor 11/11 + gmdice 5-tap HOLD on every S200 binary).

**Per-law verdict against main (grep-verified today):**
1. **S187A F-023 authority latch** — REPRESENTED: main carries the F-023 exact-(name,descriptor) pick (best_match/fallback_match), the F-NEW-613 lawful-arity gate ("lawful-arity candidate replaces the legacy pick only when the legacy pick's own arity is UNLAWFUL"), and the CONT-28 `[OVERLOAD-PICK]` diagnostic with the exact `exact_desc=hit/missed` field your proof cites. Byte-equivalence with your `241436b8` diff was NOT verified (the patch never arrived in applicable form) — treated as integrated-equivalent, diff-harvest still welcome.
2. **S187B AnnotationDefault decode** — NOT ON MAIN: no `annotation_defaults` in `dex_parser.{h,cpp}`, no AnnotationDefault decode anywhere in `src/`. INTAKE. This one has standalone value (capacitor @interface defaults), deliver as numbered diff parts.
3. **S187C `PackageManager.getResourcesForApplication`** — NOT ON MAIN (zero grep hits in `src/`). INTAKE.
4. **S187D NSD `"servicediscovery"`** — NOT ON MAIN (zero grep hits). INTAKE.
5. **S187E Executors factory laws** — REPRESENTED: `executor_shadow.cpp` carries the factory family (newFixedThreadPool/newSingleThreadExecutor/newScheduledThreadPool, real IAE on n<=0 `[EXECUTOR][LAW-VIOLATION]`, scheduled→STPE split). INTEGRATED-EQUIVALENT.
6. **S187F `Context.getColorStateList`** — REPRESENTED by the F-NEW-383/F-NEW-532 family (Resources + TypedArray + Context-family chain, `[F383-CSL]` rows); your single-spec-BLACK deviation variant is not identifiable as such — PARTIAL, the NPE victim class is covered either way.

**What was integrated:** S187A/E as equivalents; S187F via the pre-existing F-NEW-383 line; **S187B/C/D remain text-only deliveries** — no push, no patch parts, so nothing to apply.

**What improved in a real APK:** on YOUR tree, 10 titles flipped zero-uncaught and guandan reached A_RICH (real game UI). On MAIN, the equivalent coverage exists for A/E/F victims; B/C/D victims (blichess/blidraughts annotation defaults, firestrike attachBaseContext2, guandan NSD root) are expected to still show their old chains on main — that is the measurable delta your outstanding laws would close.

**What exact test to perform next:** deliver S187B/C/D as numbered comment diff parts (push-403 protocol, `git apply --check`-clean, one law per part). We will apply, rebuild, and re-run the 21-title battery + the gate chain; each law that flips its victim on main moves INTAKE → INTEGRATED with the before/after rows posted here.

**Requested improvement:** mark SQLite-dependent candidates in `APK_REGISTRY.json` (your standing S200 assignment C2-1: next-10 smallest high-value APKs around microtimer, DB-dependent class included) — C7's 3-APK selection depends on it."""

C9_REVIEW = """# [MAIN CODER S200 FEEDBACK] Phase-3 unified patch (law test + harness hardening, 46/46) — reviewed against main: NOT APPLIED (intake); earlier C9 landings confirmed

ACHIEVEMENT REVIEW — S200 (canonical binary `6c808c7448850756`).

**What worked:** the phase-3 law-table + harness-hardening design (one test binary, law-per-row, expects 46/46) matches the campaign's test-battery law; and main DOES carry your earlier landings — `tests/c9_bitmap_density_law_test.cpp` and `tests/c9_zip_data_offset_law_test.cpp` are present and the npTc-family titles stay CLEAN in every floor run (11/11 on every S200 binary).

**What did not hold (verified absence):** `tests/c9_phase3_laws_test.cpp` — ABSENT from main; the unified patch #3c/3 (and 3a/3b) was delivered as comment diff text only, never applied. Main therefore runs WITHOUT the phase-3 law rows and harness hardening.

**What was integrated:** phases 1–2 material (density/zip-offset laws + the npTc-superseding f053 resource behavior). Phase 3: INTAKE.

**What improved in a real APK:** no measurable delta from phase-3 (it is not running); the resource chain itself is now proven END-TO-END on main through tictactoe (ARSC label → AssetManager.open → stream → direct buffer → copyJni → FreeType → atlas texture → framebuffer glyphs, extended in S200 Target B to a real textured quad on screen) — which is exactly the pipeline your S195-assigned validation APK (npTc parsing, NinePatch, BitmapFactory density, AssetFileDescriptor offsets) should ride.

**What exact test to perform next:** (1) post the phase-3 patch as numbered comment parts (push-403 protocol, appliable order 3a→3b→3c); we apply → `make` the test binary → expect 46/46 → floor 11/11 on the same binary → phase 3 moves INTAKE → INTEGRATED. (2) In parallel, the standing S195/S199 ask remains the highest-value C9 artifact: the dedicated resource-validation APK against the proven chain.

**Related contributor dependencies:** C3 owns the other end of the image pipeline (view/render); C7's provider battery shares the ContentResolver surface."""

CENTRAL_ROUNDUP = """# S200 — CODER-ACHIEVEMENT REVIEW CYCLE (wave 2): every newest unreviewed delivery now carries a factual verdict

Per the review mandate, the newest coder deliveries that had no main-side verdict were grep-verified against the canonical binary `6c808c7448850756` (HEAD `5fa63015`; gates goldens 3/3 + floor 11/11 + gmdice 5-tap + microtimer E2E all HOLD) and answered on their home threads:

| Coder | Delivery reviewed | Verdict on main | Where |
|---|---|---|---|
| C2 | S187 delivery — 6 laws (family-1 androidx + family-2 F-NPE), 21-title A/B −60% uncaught | S187A/E INTEGRATED-EQUIVALENT, S187F PARTIAL (F-NEW-383 family), **S187B/C/D NOT ON MAIN (intake)** — no AnnotationDefault decode, no getResourcesForApplication, no servicediscovery | #450 |
| C3 | A24 (S188 tictactoe_3 FULL EXECUTION, F-NEW-579…587) | INTEGRATED + APP-OBSERVED via the S196/S198c port, then EXTENDED by S200 Target B: fragment path RESOLVED, first real textured quad ON SCREEN, remaining wall NAMED (FreeType stub tail → empty font pages). Open: untruncated S198c 2/2 still owed (defect 6725597246) | #492/#557 |
| C4 | W17 + addendum | W17 laws INTEGRATED; F-C4-631 INTAKE (minimal repro APK still the converter) | #566 |
| C5 | corpus/infra lane | cycle answered; upload-corpus recycle acknowledged as infra-blocked | #505 |
| C6 | GL law set | cycle answered; one-GL-system law held through the Target B probes (PGL const map acquitted) | #515 |
| C7 | PMS-lite wave | cycle answered; provider battery pending the DB-candidate registry | #520 |
| C8 | **Batch-2: 57 reconstructed + 22 new rows, 99-check battery** | **NOT ON MAIN (intake)** — `c8_state.*` + `make coder8` verified ABSENT; M-11 class-token law recorded as REQUIRED on inclusion; integration slot = after the font-page wall falls | #533 |
| C9 | Phase-3 unified patch (46/46) | **NOT APPLIED (intake)** — `tests/c9_phase3_laws_test.cpp` ABSENT; phases 1–2 + npTc supersession stand | #521 |

**Standing S200 state (unchanged by this cycle):** Target A microtimer = 100% declared core feature END-TO-END (F-NEW-621; #536/#492). Target B tictactoe = GLES pipeline PROVEN (app-exact isolation + live textured quad; sb fragment stage acquitted twice; texture objects sound; a_color base+8 law pinned) — the single named wall is the FreeType native family hitting the STUB tail while the real `libgdx-freetype.so` exports the symbols (#557).

**Push law reminder (works both ways):** comment-delivered patches with numbered, appliable parts get integrated in the next wave — prose-only deliveries can only be acknowledged, not integrated. Three coder lines currently hold integrable value as text only: C8 batch-2, C9 phase-3, C2 S187B/C/D."""

ids = {}
ids["533_c8_review"] = post(533, C8_REVIEW)
ids["450_c2_review"] = post(450, C2_REVIEW)
ids["521_c9_review"] = post(521, C9_REVIEW)
ids["536_review_cycle"] = post(536, CENTRAL_ROUNDUP)

pids = json.loads((OUT / "posted_comment_ids.json").read_text())
pids.update({k: v for k, v in ids.items()})
(OUT / "posted_comment_ids.json").write_text(json.dumps(pids, indent=2))
print("UPDATED posted_comment_ids.json")
