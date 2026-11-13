#!/usr/bin/env python3
"""R25 — post the evidence-heavy closeout comment on #587."""
import json, subprocess, urllib.request

tok = subprocess.run(["bash", "-c", 'printf "protocol=https\\nhost=github.com\\n" | git credential fill 2>/dev/null | grep "^password=" | cut -d= -f2'], capture_output=True, text=True).stdout.strip()
API = "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime"

body = r"""# S212 closeout — RELEASE-0.0.6.2 delivered (WP0–WP11, R01–R35)

**1. HEAD before/after.** Audit HEAD `9d6a29d6` → release HEAD `5c71b22c` (tag **`v0.0.6.2`**). Wave commits (reviewable, in order): `1a0fa259` S226 Vector Pinball fix (independently verified before landing), `27f02359` WP1 residue, `3d242e42` WP0+WP1 inventory+dedup, `550b4b36` WP10§6 W18 batch, `df3f74b2` WP2/R26 OSMesa, `b49ae71c` WP2/R27 forensic, `a4fb6df1` WP2/R06 compose, `490d97e3`+`a609913e` WP1/R28 root law, `d5e53fef` WP4/R11 portability, `7d22f5d3` WP11/R30-32 Constitution+validator, `3b2ab6a4` WP3/R35+WP10, `701f53e9` WP5/R13-14 README+metrics, `b9fb2ccc` WP4/R23 clean-room, `3bd2757a`+`ecd7bf12` WP7 release docs, `5c71b22c` R32 honesty fix (workflow-scope blocker documented).

**2. Final structure.** `docs/REPOSITORY_STRUCTURE.md` (R35) maps every retained top-level directory: `miniandroid/` runtime+framework data · `tests/` maintained tests (+ `graphics/backends/osmesa/` opt-in oracle) · `fixtures/` intentional inputs · `examples/`+`games/` first-party source · `third_party/` consumed vendored deps · `upstream/` pinned build-consumed sources · `docs/upstream/` versioned reference snapshots with MANIFEST · `canonical/` machine registries · `registry/` legacy distinct-contract · `docs/` human docs (+`docs/history/` frozen campaign records) · `evidence/` historical campaign evidence (transitional) · `scripts/`+`tools/` maintained tooling · `library_ecosystem/` metadata-only build-on-demand registry · `.github/`+`.agent/` governance · `audit/`,`probe_store/`,`hc_provenance/`,`reports/`,`research/`,`campaigns/`,`plugins/` frozen historical (no new writes) · root allowlist exactly: README, LICENSE, CONSTITUTION_V2.md, .gitignore, root_registry.json (documented compatibility projection).

**3. Before/after measurements** (baseline frozen in `evidence/s212/wp0_baseline/baseline.{json,md}`; never substituted between columns):
| metric | before `9d6a29d6` | after `5c71b22c` |
|---|---:|---:|
| tracked paths | 16,269 | 14,777 (−1,492) |
| path-summed bytes | 409,187,306 B (390.23 MiB) | 253,903,453 B (242.14 MiB; **−148.09 MiB**) |
| unique blobs | 12,611 | 12,347 |
| duplicate SHA groups | 1,066 (115.35 MiB checkout waste) | 888 (25.25 MiB) |
| tracked checkout bytes | 390.23 MiB | 242.14 MiB |
| local .git dir | 179.93 MiB | 181.49 MiB (grew — this wave's new objects; history rewrite forbidden) |
| GitHub metadata (API) | 125,334 KB | unchanged method; GitHub recomputes post-push |

**4. Removed/moved/deduplicated (SHA + consumer proofs in `evidence/s212/wp1_inventory/disposition_ledger.tsv` + `evidence_duplicate_groups.tsv`):** 29 session-residue files (root `s203_out*`/`gfx_trace.jsonl`, `make_out/err*`, `build_status.txt` — writers only, no readers); 1,199 byte-identical evidence paths (14.62 MiB; one canonical path kept per SHA group incl. `s195 comments_raw.partial.json` = dup of `comments_raw.json` sha `386eb21b…`; 335 members kept because live full-path/specific-name references exist — e.g. canonical GIF dup `docs/evidence/s80/*.gif` referenced by `docs/achievements/ASSET_MANIFEST.json`); W18 Halma 10 full PNGs (~27.3 MiB; SHAs + run identity preserved in `halma_w18_batch_summary.json`); OSMesa bundle 39 paths (94.39 MiB; six paths = one 15,693,864-byte blob `75dd953d…`); forensic dumps 237 paths (10.88 MiB; every SHA recorded in `docs/FORENSIC_DATA_DISPOSITION.md`); root `MessageSchema.java` (byte-identical ×3; canonical `docs/upstream/MessageSchema.java` already cited by `docs/upstream/INDEX.md`); root campaign docs → `docs/history/`.

**5. The three questioned directories.** `reference/compose_167` = AndroidX Compose 1.6.7 verbatim snapshot (42 files, Apache-2.0, single consumer `scripts/s146_train64_liw0_disasm.py`) → moved to `docs/upstream/androidx/compose/1.6.7/` with MANIFEST; `reference/` retired. `third_party/osmesa` = optional headless real-GL test backend, NO build/runtime consumer (whole-tree search) → vendored bundle removed; `tests/graphics/backends/osmesa/` keeps `test_osmesa.c` + README + MANIFEST with pinned Debian 13 packages; **clean-room proof: `apt-get download` reproduces the exact deb SHAs (`libosmesa6 d0260a10…` == the previously vendored copy) and the build+run prints `OSMESA REAL GL OK` (Mesa llvmpipe GL 4.5, pixel readback correct)**. `library_ecosystem` = retained (metadata-only build-on-demand dependency registry, S185/S186 law; 5 files ~25 KB); its distinct contract documented in REPOSITORY_STRUCTURE.md (R07).

**6. Final README + demos.** README is now an 80-line landing page (`701f53e9`). Five complete demos, each re-verified TODAY on the RC binary `06f98d2a9c21ea92` with byte-exact faces: Vector Pinball (menu over GL surface, `98abca38`, fresh ×2 + 936,460-px single-color-pair pixel proof — see the S226 verification receipt `evidence/s212/verify/verify_record.json`), GameMasterDice (`3891679d` ×2 identical), TicTacToe Deluxe (`7354c1b2` ×3 deterministic), uNote (`3b8dcb0a`), MicroTimer (`b39665f6`). Exactly two partials with exact frontiers: dooz (Compose first frame `a0fae907`; deeper state unproven) and Halma (first-frame boundary only; `app_draw_ops=0`, F-016, stub-bounded — W18 truthful batch report). No blank frame is called a render anywhere.

**7. Delta + gates.** `miniandroid/CHANGELOG.md#v0062` + `docs/releases/RELEASE_v0.0.6.2.md`: F-GLZ-2/F-BLANK-1 with pixel proof, S225-M diagnostics laws, evidence-honesty wave, repository law. Gates at the release commit: 6-pin byte-exact HOLD, `make test-all` **28/28**, policy validator **0 violations** (`docs/POLICY_ALLOWLIST.json`: 4,990 reviewed per-entry grandfather records with reason/owner/expiry; executable code never allowlisted; maintained areas zero machine paths), forensic ledger validate **390 rows / 0 errors**, metrics staleness **OK**, release-content validator **PASS**. Known limitations recorded (ARM-only out of scope; Compose subset; per-run stub census; Windows binary honestly omitted).

**8. Release.** Tag `v0.0.6.2` (annotated, at `5c71b22c`); GitHub Release **https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/releases/tag/v0.0.6.2** with asset `MiniAndroid-v0.0.6.2-linux-x64.tar.gz` (sha256 `e45433dda4ca897e9cd95e78f9c77bac0d48a594e18386930056b061f9c14629`, 4,761,562 B, release-content validator PASS). Built in a clean clone; stripped binaries from clean clone vs main tree are byte-identical except the 20-byte GNU build-id. Out-of-source smoke test reproduced the byte-exact pinned gmdice face `3891679d`. Windows asset honestly omitted (no pinned toolchain in the build environment; v0.0.3 precedent). Manifest: `docs/releases/RELEASE_MANIFEST.json` (v0.0.6.1 record archived).

**9. R01–R35 status + evidence** (evidence paths are clickable in the repo):
- **R01 IMPLEMENTED** — `evidence/s212/wp0_baseline/`
- **R02 IMPLEMENTED** — `evidence/s212/wp1_inventory/inventory.tsv.gz` + summary (every path classified)
- **R03 IMPLEMENTED** — baseline.json: checkout/.git/GitHub-metadata measured separately
- **R04 IMPLEMENTED** — batches `27f02359`,`3d242e42`,`490d97e3`; ledger + duplicate redirect map
- **R05 IMPLEMENTED** — `df3f74b2` + `tests/graphics/backends/osmesa/{README,MANIFEST}.json` + live clean-room proof
- **R06 IMPLEMENTED** — `a4fb6df1` `docs/upstream/androidx/compose/1.6.7/MANIFEST.json`
- **R07 IMPLEMENTED** — retained + documented in REPOSITORY_STRUCTURE.md
- **R08 IMPLEMENTED** — REPOSITORY_STRUCTURE.md owner/allowed/forbidden per directory
- **R09 IMPLEMENTED** — one canonical machine source `docs/METRICS.json`; `root_registry.json` retained as documented projection (265 readers)
- **R10 IMPLEMENTED** — `evidence/evidence_size_inventory.tsv` (1,349 images, class/disposition) + `evidence_retention_manifest.json` + duplicate groups
- **R11 IMPLEMENTED** — `d5e53fef`,`b9fb2ccc`: zero machine paths in maintained tools; classifier verified from /tmp
- **R12 PARTIAL** — validator + positive/negative law test (`tests/policy_validator_law_test.py` PASS: baseline accepted, 8 negative classes rejected); CI trigger shipped at `docs/ci/policy.yml` because the environment token lacks the `workflow` scope — GitHub rejected the push of `.github/workflows/policy.yml` (exact error recorded in `5c71b22c`); all four checks run green locally; activation = copy the file with a workflow-scope token
- **R13 IMPLEMENTED** — 80-line landing page, 5 verified demos + exactly 2 partials
- **R14 IMPLEMENTED** — counts reconciled (152/24/91/15/797); stale 148/150/22/36/421/853 not copied; `tools/check_readme_metrics.py` CI-wired
- **R15 IMPLEMENTED** — release delta from exact `v0.0.6.1-Exchequer` tree (213+ commits; diverged graph → count via git log, not API ahead/behind)
- **R16 IMPLEMENTED** — CHANGELOG `[v0.0.6.2]`
- **R17 IMPLEMENTED** — release doc + manifest + indexes agree (one source)
- **R18 IMPLEMENTED** — Linux x86_64 package built/validated/smoke-tested/SHA-pinned
- **R19 BLOCKED** — Windows: no pinned toolchain in this build environment; not faked (explicitly omitted per v0.0.3 precedent)
- **R20 IMPLEMENTED** — 5 demos on RC binary, fresh runs today, byte-exact faces + pixel proof
- **R21 IMPLEMENTED** — exactly 2 partials with frontier evidence (dooz, Halma)
- **R22 IMPLEMENTED** — test-all 28/28; policy/ledger/metrics/release validators green; failures: none
- **R23 IMPLEMENTED** — clean clone → bootstrap → build → README quick-start commands succeed with no `/home/z` dependency (the tracked dangling `/tmp/my-project` toolchain symlinks that broke this were found and removed in `b9fb2ccc`)
- **R24 IMPLEMENTED** — tag + Release published only after gates agreed
- **R25 IMPLEMENTED** — this comment
- **R26 OSMESA PURPOSE IMPLEMENTED** — consumers documented; test-only; duplicates resolved; clean optional test proof attached
- **R27 FORENSIC DATA IMPLEMENTED** — 237 inputs dispositioned; 3 patch parts all MERGED (markers verified in main); ledger rebuild validated (390 rows); raw dumps removed with SHA retrieval record
- **R28 ROOT LAW IMPLEMENTED** — root = exact allowlist; strays moved with provenance
- **R29 DIRECTORY OWNERSHIP IMPLEMENTED** — `reference/` retired; every top-level dir owned in the map
- **R30 CONSTITUTION IMPLEMENTED** — §172 added, linked from README/structure docs
- **R31 FILE CONTRACT IMPLEMENTED** — §172.3 normative; validator enforces consumer-less/unknown-class paths
- **R32 CI ENFORCEMENT PARTIAL** — validator + law test complete and green; CI trigger blocked by token scope (see R12); negative test proves the next deliberately misplaced file is rejected
- **R33 NO-REGRESSION IMPLEMENTED** — clean builds/tests leave no tracked residue (policy validator enforces)
- **R34 CODER ALIGNMENT PARTIAL** — Constitution §172 is the normative authority referenced by README/structure/agent docs; per-coder request-template updates require owner action
- **R35 FINAL MAP IMPLEMENTED** — `docs/REPOSITORY_STRUCTURE.md`

**10. #386 reconciliation.** This issue executed #386's unresolved hygiene intent (disposition ledger → small batches → consumer proofs → retention policy) but does not close #386: remaining there = the historical one-off script corpus externalization (the grandfather allowlist's recorded expiry trigger) and per-wave evidence retention sweeps for pre-#587 folders (`evidence/` remains transitional). Policy: no history rewrite, no force-push, no tag movement anywhere in this wave.

**Prevention (WP10 §7) is live**: `scripts/s207_gate.py` now flags any screenshot >800 KB as `NOISE-SUSPECT` / >1 MiB as `NOISE` (uninitialized-buffer suspicion never silently accepted), and the evidence-size gate rejects new >1 MiB images without a reviewed allowlist entry.
"""

req = urllib.request.Request(f"{API}/issues/587/comments", data=json.dumps({"body": body}).encode(),
    headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json",
             "Content-Type": "application/json", "User-Agent": "miniandroid-s212"})
c = json.load(urllib.request.urlopen(req, timeout=120))
print("closeout posted:", c["html_url"], "| id:", c["id"])
