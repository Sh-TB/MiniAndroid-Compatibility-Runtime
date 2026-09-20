# tools/architecture/ — S69 SOURCE-LINKED RUNTIME graph & index generators

Campaign law (§2/§3/§10/§13/§23 of the FINAL FOUNDATION / SOURCE-LINKED brief):
graph nodes and index rows are EXTRACTED, not hand-annotated; every tool
records its data origin; every honest over/under-approximation is flagged in
the JSON it emits.

## Tools

| tool | purpose | outputs |
|---|---|---|
| `engine_extractor.py` | parse the LIVE engine TUs (dead TUs per S68_BUILD_GRAPH are excluded on purpose) → function bodies, string guards, call edges, class inheritance | `docs/foundation/graph/{served_api,class_graph,subsystem_graphs}.json` |
| `dex_census.py` | walk every corpus APK's DEX (androguard): app classes/methods, every invoke-* call site, corpus-wide android API fan-out | `docs/foundation/dex_census/<pkg>.json` + `_aggregate.json` |
| `build_api_matrix.py` | merge static fan-out × live dispatch traces × static served surface → status law (LIVE-IMPL > LIVE-PARTIAL > LIVE-STUB > SERVED-STATIC > UNSERVED) | `docs/foundation/api_matrix.json` |
| `build_source_map.py` | source file ↔ DEX class ↔ android API ↔ live status ↔ frame evidence per pinned APK (R8-obfuscated = UNMAPPED, honest) | `docs/foundation/source_map.json` |
| `build_failure_index.py` | root_registry.json (372 roots) → campaign failure schema (nulls, never invented) | `docs/foundation/failure_index.json` |

## Live dispatch surface

`miniandroid run --dump-api-trace` (added S69, same pattern as S67's
`--dump-view-tree`) writes `<output>/api_calls.json` — every invoke bridged to
the framework layer with per-call status. `scripts/s69_live_runs.sh` runs the
whole canonical corpus with it (canonical S65 recipe: `--execution-mode
real-dalvik --frames 9 --frame-delay 1500`) and summarizes to
`docs/foundation/live_runs.json`.

## Regeneration order

```bash
python3 tools/architecture/engine_extractor.py
python3 tools/architecture/dex_census.py
bash scripts/s69_live_runs.sh          # live traces + live_runs.json
python3 tools/architecture/build_api_matrix.py
python3 tools/architecture/build_source_map.py
python3 tools/architecture/build_failure_index.py
# aggregator → docs/foundation/runtime_graph.json is generated in the
# S69 session script (same merge, single file)
```

## Source pins

`scripts/s69_source_inventory.py` (+ `_complete.py`) pin each corpus APK to
its upstream commit via fdroiddata build metadata (SourceCode + per-versionCode
commit), fetch the tarball (codeload / GitLab archive), and write
`upstream/corpus/<pkg>/PROVENANCE.json` (tarball SHA256 included). Session-ledger
pins (S65/S66) cover the three veldsoft/OPMT apps.
