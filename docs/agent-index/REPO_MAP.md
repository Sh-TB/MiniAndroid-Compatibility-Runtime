# REPO_MAP — deterministic repository summary (generated; HEAD `bcfd4405`)

Purpose: the agent must NOT rediscover the tree every session (speed-addendum §7).
Regenerate: `python3 scripts/gen_agent_index.py`.

## Build & run
- Build: `make -C miniandroid` → `miniandroid/build/miniandroid` (g++ 14.2, C++17, -O2).
- Battery (full regression gate, 91 stages): `bash scripts/test/run_test_battery.sh`.
- Single APK run: `./build/miniandroid run --execution-mode real-dalvik -o run/<id> <apk>`.

## Subsystems (miniandroid/src — 108 files, 76,125 lines)
| dir | role | files | lines |
|---|---|---|---|
| apk | APK ZIP container parsing | 4 | 2,030 |
| dex | DEX parser + Dalvik interpreter engine (dalvik_engine.cpp = dispatch core) | 21 | 30,885 |
| runtime | execution/application runtime orchestration | 7 | 11,571 |
| framework | shadow layer: View/Context/Choreographer/atomic/locks/touch/canvas | 28 | 9,307 |
| resources | ARSC/AXML/layout inflation/resource runtime | 18 | 8,133 |
| renderer | software framebuffer renderer | 5 | 4,520 |
| fonts | FreeType/HarfBuzz/FriBidi text shaping | 2 | 1,205 |
| storage | SQLite/SharedPreferences/file sandbox/data root | 6 | 2,417 |
| api | application context/shared prefs API | 5 | 3,752 |
| diagnostics | trace engine | 4 | 811 |
| graphics | graphics helpers | 0 | 0 |
## Key single files
- `miniandroid/src/dex/dalvik_engine.cpp` — interpreter + F-law handlers (the DEX dispatch floodgate).
- `miniandroid/src/framework/shadow_registry.cpp` — shadow dispatch order (F-050/F-057 laws).
- `miniandroid/src/resources/layout_inflater.cpp` — XML layout → view tree (F-053 shape law).
- `miniandroid/src/renderer/software_renderer.cpp` — draw → pixels.
- `scripts/test/run_test_battery.sh` — the 91-stage gate.
- `root_registry.json` — machine-readable root registry (single source of truth).
- `docs/root-searchlight/ROOT_WORKLIST.md` — the live 286-root worklist.

## Corpus & fixtures
- Corpus APKs: `miniandroid/download/exp076_corpus/` (dooz pinned sha256 d81292cd…).
- Fixtures: `miniandroid/tests/fixtures/` (aapt2+ECJ+D8 built — authority per D-04).
- Evidence: `miniandroid/run/` (raw run records), `docs/evidence/` (curated, canonical). 
- Demo app source: `examples/demo-app/` (build: `bash examples/demo-app/build_demo_apk.sh`).
- Toolchain: `tools/` (aapt2 2.20-14304508, r8.jar, ecj.jar, android-34.jar).

## Verification fast path
- `tools/verify/verify.py --root R-NEW-XXX | --batch | --cluster apk|source|shot|symbols`
- `tools/verify/apk_artifacts.py <apk>` — shared cached APK/DEX/ARSC artifacts.
- `tools/verify/evidence.py` — evidence bundle collector.
- `tools/doctor.sh [--json]` — tool health check.
