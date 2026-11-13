# S229 closeout — #587 S213 + S214 governance packages (the "forgotten items" wave)

Date: 2026-11-13. Base: S212 closeout `ba178ed4` (v0.0.6.2 Silver + closeout comment 6847022917).
This wave implements the two owner packages that arrived AFTER the S212 closeout and were
not yet executed: **S213** (comment 6853869494 + GOVERNANCE ADDENDUM §S213) and **S214**
(comment 6853939129 + GOVERNANCE ADDENDUM §S214). Nothing from S212 was re-labelled.

## S213 — evidence image formats and storage budgets

- **A. JPEG-by-default policy — IMPLEMENTED.** `tools/evidence_image_optimizer.py`
  encodes the law: photographic/noisy → optimized JPEG (ladder 85→80→75→70, sRGB,
  optimize+progressive, metadata stripped), target ≤100 KiB, ≤200 KiB hard promote limit,
  PNG >100 KiB disallowed by default for photographic content, PNG mandatory kept for
  alpha/diagram/pixel-art, animations never flattened, `fixtures/`/`upstream/`/runtime
  resources never converted, idempotent (JPEG inputs skipped — no recompression, no
  derivative chains), resize ladder (1.0→0.75→0.5) only when the quality ladder cannot
  meet the budget, every conversion records source/output SHA-256 + settings + RMS-Δ.

- **B. Tooling + enforcement — IMPLEMENTED + TESTED.**
  - 9 unit tests: `tests/test_evidence_image_optimizer.py` covering all 8 required cases
    (JPEG idempotence, large noisy PNG, transparent PNG, pixel-art/diagram PNG, GIF
    animation preservation, corrupt input, duplicate-output determinism, already-small)
    + staging non-destructiveness. **Ran 2026-11-13: OK (9/9).**
  - Policy validator integration: `IMAGE_POLICY_NEW` / `IMAGE_POLICY_MUTATED` reject any
    new over-threshold tracked image without a per-file exception; the legacy §172.5
    >1 MiB gate now accepts narrow S213 exceptions.
  - Registries: `docs/IMAGE_POLICY_BASELINE.json` (72 per-path legacy entries,
    38,179,812 B — the adoption inventory, NOT a blanket exception; each entry carries
    owner/reason/review-trigger) + `docs/IMAGE_EXCEPTIONS.json` (narrow per-file
    exceptions; starts with exactly ONE entry: the cont69 PNG provenance exception).
  - Full tracked-image inventory: `evidence/s229_s213_s214/image_inventory.csv`
    (1,349 images: 1,184 OK / 90 MIGRATE_TO_JPEG / 22 REJECT_PROMOTION / 20 animations /
    7+2+6 exception-class / 17 unreadable-corrupt [0–33 B residue, DELETE_CANDIDATE at
    migration wave]).

- **C. cont69_mosaic — IMPLEMENTED (measured).** `evidence/s229_s213_s214/cont69_mosaic_audit.md`:
  claimed 12x is wrong — **measured 17.78x total (PNG 896,399 B vs tracked JPG 50,423 B),
  of which only 1.75x is the format effect at native resolution** (2160x5000 → 553x1280
  downsampling is 15.3x of it). JPG proven-derivative (RMS-Δ 0.814). Disposition: JPG =
  presentation asset; PNG = provenance source with the single narrow exception.

- **D. s195/s202 paths — IMPLEMENTED.** `evidence/s229_s213_s214/s195_s202_dispositions.md`:
  `evidence/s202_625_forced/` = NOT_PRESENT (no commit history — honest finding);
  `evidence/s195_audit/` = 252 files classified (compact metadata KEEP / 6 canonical JPG
  faces KEEP / 3 oversized PNGs MIGRATE_CANDIDATE / patches + store trees KEEP as
  provenance); `tictactoe_s195fix_r1/` = 4 compact metadata files KEEP + 3,360,833 B PNG
  MIGRATE_CANDIDATE **demonstrated**: optimizer produced 99,178 B JPEG (33.89x, RMS-Δ
  0.634) in `conversion_demo/` with SHA mapping — the frozen original untouched.

- **E. Canonical demo gallery — IMPLEMENTED.** All four named GIFs verified genuine
  animations (g2048 65 frames/22.5 s/979,913 B; tetris 75/13.66 s/770,771 B;
  snakedeluxe 49/14.4 s/493,247 B; minicraft 15/5.6 s/172,914 B; 400x737 / 360x640,
  RGB) with canonical-registry provenance (records 50/51/52/147, in-house APK SHA-256
  per record). README now displays the four-demo gallery **immediately after the scope
  statement, before architecture/build details**, with captions + registry links. RC-binary
  re-runs of these four are honestly marked PARTIAL in the gallery note (the five demos
  re-verified on `06f98d2a9c21ea92` remain the RC-proven set). No GIF flattened to JPEG.

- **F. Deliverables — IMPLEMENTED.** Before/after inventory (this dir + CSV), conversion
  manifest (`conversion_demo/`), policy + automated tests + validator/CI integration,
  cont69 measured comparison, three-path disposition report, README diff (gallery),
  clean-clone validation (`clean_clone_residue.log`).

## S214 — hard release gate + zero-drift repository law

- **WP1 Windows gate — IMPLEMENTED (gate) / BLOCKED (artifact, measured).**
  - `docs/releases/RELEASE_MANIFEST.json` schema v2: `required_platforms`
    (linux-x64=PASS with sha256/bytes/evidence; windows-x64=BLOCKED with exact blocker +
    diagnosis + unblock path) + `release_class=linux-only-preview` with the prominent
    Windows statement.
  - `scripts/release/validate_release_manifest.py`: fails any normal/stable release class
    with a non-PASS mandated platform (no-silent-downgrade), fails PASS without artifact
    name/sha/bytes, fails BLOCKED without blocker+diagnosis. **Negative tests: stable
    class + missing Windows → rejected; fake PASS without sha256 → rejected; missing
    platform enumeration → rejected. Positive: current manifest PASS.**
  - Windows build attempt (not assumed): pinned route `pip install ziglang==0.17.1`
    (`scripts/release/build_windows_zig.sh`) cross-probes 4 representative TUs —
    `dlfcn.h`, `zlib.h`, `execinfo.h`, `sqlite3.h` not found; 15 sources use POSIX-only
    APIs; 11 C-dependency families have no Windows builds. Full log:
    `windows_probe.log`; recipe + matrix + unblock path: `docs/ci/WINDOWS_TOOLCHAIN.md`.
  - CI: `docs/ci/windows-build.yml` + `docs/ci/windows-release-gate.yml` (shipped in
    docs/ci/ per the recorded PAT workflow-scope constraint; the manifest gate itself
    runs locally today and is wired into the local preflight).
  - v0.0.6.2 Silver reclassified **Linux-only preview** on the GitHub release page
    (body updated in place; no re-tag, no history rewrite, no binary claims). R19 stays
    OPEN/BLOCKED until a tested PE artifact passes the same gates.
- **WP2 default-deny path law — IMPLEMENTED + TESTED.**
  - `docs/PATH_OWNERSHIP.json`: per-area contract (owner/purpose/classes/lifecycle/size),
    500 approved dir prefixes (adoption inventory + 1 pre-registered wave path),
    9 frozen-area snapshots (audit, campaigns, reports, research, hc_provenance,
    probe_store, plugins, evidence, docs/history — count + path-list SHA-256), run-output
    routing to ignored `.cache/<tool-or-suite>/<run-id>/`, scratch rules.
  - `tools/policy_validator.py` extensions: `FROZEN_SNAPSHOT_DRIFT` (any added/removed
    child in a frozen area), `UNREGISTERED_DIRECTORY` (any new dir prefix),
    `SCRATCH_RESIDUE` (.rej/.bak/.orig everywhere + stdout/stderr/scratch/cache/build
    names outside exempt areas), `SYMLINK_ESCAPE` (absolute/out-of-repo targets),
    `SIZE_BUDGET_EXCEEDED`; the registry is authoritative for root/top-level law.
  - Local preflight = the same validator; CI wiring in docs/ci/. Warnings never pass:
    violations exit 1.
  - Required tests: **13/13 PASS** (`tests/path_ownership_gate_test.py`, log
    `gate_tests.log`): 2 positive + 11 negative, each asserting the exact rejection code
    and path. Clean-clone no-residue proof: `clean_clone_residue.log` — fresh clone builds
    (`make -C miniandroid -j1`), zero tracked changes, zero untracked residue outside
    ignored build dirs, validator green on the clone.
  - Demonstrated on itself: the wave's own evidence dir was **registered in the registry
    BEFORE creation** (`wave_evidence_registered`), then created — the S214 approval
    process executed end-to-end. Also: 3 tracked `.rej` patch-residue files found in
    `miniandroid/src/` and deleted under the new law; 3 s228 scripts' machine paths
    converted to repo-root discovery (WP4 law) before registration.
- **WP3 structure + evidence budget — IMPLEMENTED.** `docs/SIZE_BUDGET.json`: per-area
  tracked-byte budget (adoption measurement + 10% headroom, min 1 MiB) enforced by the
  validator; canonical/ remains index+curated-proof only; the four demo GIFs preserved
  animated with provenance; evidence promotion provenance requirements recorded in the
  registry (`promotion_requires`).
- **WP4 proof — IMPLEMENTED.** This directory is the proof package: inventories,
  manifests, logs, dispositions; commit series kept reviewable (see git log).

## What this wave did NOT do (honest boundaries)

- No Windows binary: BLOCKED with a measured diagnosis (S214's own escape hatch); no
  wine/Windows host in this environment — the gate makes that state impossible to
  mislabel rather than pretending progress.
- No legacy image migration: the 90 MIGRATE_TO_JPEG + 22 REJECT_PROMOTION legacy assets
  stay untouched under the per-path baseline (S213: "enforce for newly promoted evidence;
  migrate old assets incrementally") — the conversion was demonstrated on the named
  example instead.
- No legacy cleanup deletion: the 17 unreadable (0–33 B) images are recorded
  UNREADABLE_CORRUPT with DELETE_CANDIDATE dispositions for the #386 migration wave.
- The four gallery GIFs' RC-binary re-runs are PARTIAL (provenance is the canonical
  registry records; not re-run on `06f98d2a9c21ea92` this wave).

## Verification commands

```
python3 tests/test_evidence_image_optimizer.py      # 9/9 OK
python3 tests/path_ownership_gate_test.py           # 13/13 OK
python3 tools/policy_validator.py                   # 0 violations
python3 scripts/release/validate_release_manifest.py# PASS + negative tests
bash scripts/release/build_windows_zig.sh           # exit 1 = measured BLOCKED
bash scripts/s229_clean_clone_residue_test.sh       # PASS
python3 tools/check_readme_metrics.py               # OK
```
