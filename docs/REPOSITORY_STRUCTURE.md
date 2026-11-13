# Repository structure (#587 WP3/R35 — generated from CONSTITUTION_V2 §172)

Owner of record: **CONSTITUTION_V2.md §172** (normative authority). This
document is the explanatory map. Last regenerated: 2026-11-13 at `7d22f5d3`.

| Top-level path | Owner | Allowed | Forbidden | Notes |
|---|---|---|---|---|
| `miniandroid/` | runtime | implementation, framework data, build files, runtime tests, `core_sources.manifest` (Makefile+CMake consumer), `APK_REGISTRY.json` (registry consumers), `CHANGELOG.md` | run output, raw logs | `database/` = historical experiment censuses + framework data (EXP-022..032 docs reference basenames; `scripts/s125_build_canonical.py` reads `EVIDENCE_INDEX.json`) |
| `tests/` | quality | maintained tests incl. `graphics/backends/osmesa/` (opt-in real-GL oracle) and `policy_validator_law_test.py` | wave dumps | |
| `fixtures/` | quality | intentional test inputs referenced by tests | generated fixture build output | |
| `examples/` | docs/dev | runnable example source | | |
| `games/` | runtime | first-party game source | | |
| `third_party/` | deps | vendored dependencies actually consumed (portablegl, quickjs, nlohmann, minimp3, stb_vorbis under `miniandroid/third_party/`) | unused bundles | OSMesa vendored bundle REMOVED (#587 R26) → `tests/graphics/backends/osmesa/` + pinned bootstrap |
| `upstream/` | deps | pinned third-party source trees for source-first builds (e.g. `upstream/s43` Compose) | reference-only snapshots | versioned reference snapshots live in `docs/upstream/` |
| `docs/upstream/` | docs | versioned reference snapshots with per-version MANIFEST (URL/revision/license) | runtime sources | `androidx/compose/1.6.7/` moved here from retired `reference/` |
| `canonical/` | governance | machine-readable registries; generated projections declare their generator | hand-edited projections | `root_registry.json` at repo root is the documented compatibility projection (265 historical readers) |
| `registry/` | governance | legacy distinct-contract registries only | duplicates of canonical registries | |
| `docs/` | docs | human documentation; `docs/evidence/canonical/` curated proof; `docs/history/` frozen campaign records | raw run folders | |
| `evidence/` | evidence | historical campaign evidence (transitional); batch-level summaries per #587 WP10 | new unreviewed wave dumps | |
| `scripts/` | tooling | maintained build/test/release/audit scripts | run outputs beside scripts | historical one-off corpus grandfathered per `docs/POLICY_ALLOWLIST.json` |
| `tools/` | tooling | maintained developer tools (incl. `policy_validator.py`) | scratch binaries/caches | |
| `library_ecosystem/` | deps-doc | metadata-only build-on-demand dependency registry (S185/S186): registry/capability matrix/dependency graph/locks | bulky artifacts | retained as its own documented registry contract (#587 R07) |
| `.github/` | governance | workflows (`policy.yml`), issue templates | | |
| `.agent/` | governance | current agent contract + Constitution pointers | old campaign state | |
| `audit/` | historical | frozen s128 audit dumps | new writes | |
| `probe_store/` | historical | frozen gate-A probe store (documented by `docs/INSTALL_TREE_PROOF.jsonl`) | new writes | |
| `hc_provenance/` | historical | frozen hello_color run provenance | new writes | |
| `reports/`, `research/`, `campaigns/` | historical | frozen wave reports/notes | new writes | |
| `plugins/` | historical | frozen plugin metadata manifests | new writes | |
| `forensic_data/` | RETIRED | — | everything | raw API dumps removed (#587 R27); use `scripts/forensic_ledger.py fetch` → ignored `.cache/forensics/` |

## Root allowlist (exactly)

`README.md` · `LICENSE` · `CONSTITUTION_V2.md` · `.gitignore` ·
`root_registry.json` (compatibility projection of
`canonical/root_cause_registry.json`, byte-identical, retirement trigger =
externalization of the 265 historical reader scripts).

## Migration status (this release wave)

- removed: root session residue, `make_out/err` corpus, `s203_out*`,
  `gfx_trace.jsonl`, root `MessageSchema.java` (canonical `docs/upstream/`),
  root campaign docs → `docs/history/`
- deduplicated: 1,199 byte-identical evidence paths (14.62 MiB checkout),
  W18 Halma 11-run batch compacted to one canonical PNG + batch summary
- retired areas: `reference/` (moved to `docs/upstream/`),
  `third_party/osmesa/` (→ `tests/graphics/backends/osmesa/` + bootstrap),
  `forensic_data/` (→ ignored `.cache/forensics/` via `--fetch`)
- enforcement: `tools/policy_validator.py` + `tests/policy_validator_law_test.py`
  + `.github/workflows/policy.yml`
