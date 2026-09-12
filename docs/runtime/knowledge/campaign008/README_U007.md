# MiniAndroid — UNIFIED_007 FINAL

C++ Android-compatibility runtime: parses real APKs, executes real Dalvik
bytecode, inflates real layouts from `resources.arsc` + binary AXML, shapes
text through FriBidi → HarfBuzz → FreeType (+ color-emoji fallback), renders
the view tree to a framebuffer, dispatches hit-tested touch events into real
DEX callbacks, and captures per-tap screenshot evidence.

## What to run first

```bash
make -j4            # build runtime (~2 min)
./build/miniandroid run --output run/demo --journey run/demo/journey \
    download/corpus/gmdice.apk
open run/demo/journey/step_00_launch.png
```

## UNIFIED_007 capabilities (all evidence-backed)

| Area | Status | Evidence entry point |
|------|--------|----------------------|
| Real APK user journey | PROVEN (Telegram chain) / PARTIAL (gmdice) | `run/u007_telegram_v2/telegram_01..05.png` |
| ARSC resource table | PROVEN | `build/arsc_tool download/corpus/gmdice.apk` |
| Layout inflation | PROVEN | `[U007-INFLATE]` stderr + `[EXP092-RENDER]` tree dump |
| Font pipeline (RTL/bidi/emoji) | PROVEN | `run/u007_font_proof/proof.png` |
| Touch → DEX callbacks | PROVEN | `journey.json` + `touch_audit_v1` records |
| Audio state machine | PROVEN 47/47 | `./build/test_audio` |
| Software 3D | PROVEN | `run/u007_3d/frame_metrics.json` |
| Persistent jobs + REST API | PROVEN 10/10 | `python3 scripts/u007_job_server_test.py` |
| Jetpack Compose apps | BLOCKED | `status.json → dooz` |

Machine-readable truth: `run/u007_status/status.json` (regenerate with
`python3 scripts/u007_status_gen.py`). Every value is auto-extracted from
artifacts on disk — the file is the single source of truth for grading.

## Layout of this deliverable

- `QUICKSTART.md` — 60-second commands
- `ARCHITECTURE.md` — subsystem map + data flow
- `API.md` — runtime CLI + job server REST
- `STATUS.md` — per-requirement grades with honest failure records
- `src/` — runtime source (fonts/, audio/, resources/, runtime/, renderer/)
- `tools/u007_job_server.cpp` — persistent job server (REST, refresh-safe)
- `tests/` + `scripts/` — test suites and evidence generators
