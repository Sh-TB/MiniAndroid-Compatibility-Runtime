# MiniAndroid Compatibility Runtime

**A from-scratch, CPU-first Android APK compatibility runtime for x86/x86_64 Linux hosts** — it parses real APKs, executes Dalvik bytecode with its own engine, and drives real app UI (lifecycle, layout, input, rendering, state) without an emulator, a VM, or ARM translation.

## Mission

MiniAndroid exists to run real Android applications directly on the host CPU, and to prove every claim with reproducible evidence: a demonstration is only a demonstration when the APK identity, the exact runtime build, the run command, the rendered frames, the input, and the measured state change are all recorded. Where something does not work yet, the frontier is documented instead of claimed.

## Scope (read this first)

- **Runs today:** pure-DEX APKs (no native libraries — ABI-neutral) and APKs shipping **x86/x86_64** native libraries.
- **Out of scope:** ARM-only APKs (`ABI_OUT_OF_SCOPE` — skipped, never counted as a failure), and MiniAndroid is **not** a full Android OS, not an emulator, not an Android agent, and not an ARM translator.
- **Never claimed:** "runs Android apps" without per-app evidence. Every count in this README comes from [`docs/METRICS.json`](docs/METRICS.json), generated from the canonical registries — 152 canonical titles (24 `VERIFIED`, 112 `OBSERVED`), 91 games + 15 apps registered, 797 recorded root causes.

## How it works

```
APK → ZIP/AXML/resources parsing → Dalvik-class DEX execution (own engine)
    → Android object model + lifecycle (Activity/Service/Receiver/Provider shadows)
    → layout + render (View walk, Compose subset, PortableGL GLES bridge) → input dispatch
    → state/storage (SharedPreferences, SQLite shadow, files)
```

Maintained C++ sources live under [`miniandroid/`](miniandroid/) (74 TUs listed in `core_sources.manifest`); the repository layout law is [CONSTITUTION_V2 §172](CONSTITUTION_V2.md), mapped in [`docs/REPOSITORY_STRUCTURE.md`](docs/REPOSITORY_STRUCTURE.md).

## What genuinely runs (all re-verified on release-candidate binary `06f98d2a9c21ea92`, 2026-11-13)

| Demo | What is proven | Current evidence |
|---|---|---|
| **Vector Pinball** (bouncy) | GL surface + app menu composited per the SurfaceView z-order law: Select-Table panel, 5 menu buttons, status bar render above the GL frame; face `98abca38` byte-exact, 0 uncaught | [run](evidence/s207/runs/s207_gold_bouncy/report.md) · [GIF](docs/evidence/canonical/com.dozingcatsoftware.bouncy.gif) |
| **GameMasterDice** | real dice-roll taps; two independent runs byte-identical (`3891679d`) | [r1](evidence/s207/runs/s207_gmdice_r1/report.md) · [r2](evidence/s207/runs/s207_gmdice_r2/report.md) |
| **TicTacToe Deluxe** | full game loop; 3 runs deterministic `7354c1b2`; win/stalemate board states | [ttt0–2](evidence/s207/runs/s207_ttt0/report.md) · [GIF](docs/evidence/canonical/com.emmanuelmess.tictactoe.gif) |
| **uNote** | notes app UI; VERIFIED canonical title; face `3b8dcb0a` | [run](evidence/s207/runs/s207_gold_unote/report.md) · [image](docs/evidence/canonical/app.varlorg.unote.jpg) |
| **MicroTimer** | timer UI + taps; face `b39665f6`, 0 uncaught | [run](evidence/s207/runs/s207_mtm_spot/report.md) · [image](docs/evidence/canonical/dubrowgn.microtimer.jpg) |

The gate battery (`scripts/s207_gate.py`) pins all of the above byte-exactly and runs `make test-all` (28/28) — see [`docs/releases/RELEASE_v0.0.6.2.md`](docs/releases/RELEASE_v0.0.6.2.md).

## In progress — honest partials (never labeled complete)

| Example | What works | Exact frontier |
|---|---|---|
| **dooz** (Compose Tic-Tac-Toe) | Compose UI first frame: 3×3 board + turn-state text render, pin `a0fae907` | deeper Compose game-state interaction unproven; first-frame boundary is the current frontier ([run](evidence/s207/runs/s207_gold_dooz/report.md)) |
| **Halma** | APK load → manifest/DEX parse → lifecycle dispatch → surface creation → repeatable first frame (11-run batch, one canonical frame) | `app_draw_ops=0`, one uncaught in-flight exception, stub-bounded census — **not** gameplay ([batch report](evidence/s188_w18/halma_w18_BATCH_REPORT.md)) |

## Known limitations

- ARM-only native libraries are skipped by the ABI gate (no translation layer).
- Compose support is a subset: first-frame/board rendering proven; complex stateful apps remain partial.
- API coverage is stub-bounded in places — every run records its `IMPLEMENTED/STUBBED` census (F-NEW-200) and uncaught exceptions (F-016); "SUCCESS" is never claimed past those caveats.
- Networking, media playback and background services are not claim-complete; per-title facts live in the [canonical registry](docs/evidence/canonical/registry.json).

## Quick start (tested on Debian 13, g++ 14.2)

```bash
git clone https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime
cd MiniAndroid-Compatibility-Runtime
make -C miniandroid -j4            # builds miniandroid/build/miniandroid

# install a pure-DEX or x86/x86_64 APK and run it:
./miniandroid/build/miniandroid install app.apk --data-root /tmp/ma_store
./miniandroid/build/miniandroid run --execution-mode real-dalvik --data-root /tmp/ma_store \
    -o /tmp/ma_out --package <app.package> --frames 8 --frame-delay 250
# → /tmp/ma_out/screenshot.png + report.md + traces
```

Repository policy: machine paths, run stores, raw logs and oversized non-canonical images are rejected by [`tools/policy_validator.py`](tools/policy_validator.py) (CI: `policy-guard`).

## Project map

| | |
|---|---|
| Architecture & structure | [`docs/REPOSITORY_STRUCTURE.md`](docs/REPOSITORY_STRUCTURE.md) · [Constitution](CONSTITUTION_V2.md) |
| Contributing & evidence standards | [`docs/REPOSITORY_HYGIENE.md`](docs/REPOSITORY_HYGIENE.md) · [CONTRIBUTING](docs/CONTRIBUTING.md) |
| Status & roadmap | [`docs/METRICS.json`](docs/METRICS.json) · [canonical registry](docs/evidence/canonical/registry.json) |
| Release | [`docs/releases/RELEASE_v0.0.6.2.md`](docs/releases/RELEASE_v0.0.6.2.md) · [changelog](miniandroid/CHANGELOG.md) |
| Evidence tiers & retention | [`evidence/evidence_retention_manifest.json`](evidence/evidence_retention_manifest.json) |

## License

MIT — see [LICENSE](LICENSE). Third-party pinned sources carry their own licenses, recorded per directory (`docs/upstream/*/MANIFEST.json`, `tests/graphics/backends/osmesa/MANIFEST.json`).
