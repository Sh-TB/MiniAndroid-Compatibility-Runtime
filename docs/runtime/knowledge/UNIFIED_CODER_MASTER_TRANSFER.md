# UNIFIED_CODER_MASTER_TRANSFER

**Campaign:** Unified Multi-Workstream Coder (C2+C3+C4+C5) — **Date:** 2026-08-27
**Baseline:** `bbe0ce3` · **Generated on:** `86bd646` (UC-CM-001) · **Reference APK:** Telegram 12.10.1 (vc 70389)
**PUSH:** PUSH_PENDING (no credential in the sandbox) — everything was delivered as files.

---

# TOP 10 DISCOVERIES

1. **Forward-version compat PROVEN:** Telegram 12.10.1 (never-before-seen, 5 DEX, 12,544 classes) executed; 3/3 identical SHA `06fb40da…`, 0 errors, SMS-family screen rendered (41,233px). The runtime architecture is version-agnostic.
2. **UC-CM-001 (closing F012):** the API-bridge catch-all is now type-aware (0/false/null/0.0 instead of VOID) — with zero regression. Patch ready.
3. **Persian/RTL full-pipeline PROVEN:** FriBidi 1.0.16 → HarfBuzz 10.2.0 → FreeType 2.13.3; 4/4 samples (letter joining, first-strong, right-align) — not yet inside the runtime.
4. **base-direction is critical:** with a forced LTR base, Persian lines break completely (Latin reversed); the FIRSTSTRONG heuristic (AOSP) fixed the problem — it must be implemented inside the runtime.
5. **Uri is ABSENT in the runtime** (the charter assumed it proven) — grep over the whole src = 0 handlers for `Landroid/net/Uri`.
6. **SystemClock still ABSENT** (F004 still OPEN) — after the value-wide fix only the mechanism had been opened.
7. **The per-version resource map is fragile (new SFS-010):** in v12 the texts = R field names (SMSWordTitle/WrongCode), not the actual values → solution: automatic generation from resources.arsc at load-time.
8. **The generic RLottie wiring hooked on v12 too** (7 pending views identified) but the render needs a new R$raw mapping.
9. **No external project executes a real APK CPU-only without Android** (12 projects surveyed) — MiniAndroid's niche confirmed; closest templates: Robolectric architecture + RNG/Paparazzi render.
10. **F017/N9 (Makefile header deps) is already fixed on HEAD** — `(-MMD -MP)` present; the old open finding is closed.

# TOP 10 ACTIONS FOR PRIMARY

1. `git am 0001-UC-CM-001-….patch` (already applied; zero regression on v12).
2. FontBackend: FreeType+HarfBuzz+FriBidi with FIRSTSTRONG — POC code ready to copy (`scripts/wsc2_text_pipeline.cpp`).
3. Implement the `android.net.Uri` bridge (parse/Builder/queryParameter/normalizeScheme) — reference: AOSP Uri.java.
4. SystemClock with `clock_gettime(CLOCK_MONOTONIC/BOOTTIME)` + a deterministic-clock key.
5. Auto-generate the string/raw resource map from ARSC (removing dependence on the hand-made resource_values.json) — closes SFS-010 and RLottie-v12 together.
6. SQLite amalgamation → DatabaseBackend + contract tests (§10) — the biggest open corpus item.
7. Benchmark libdeflate on the Telegram load; if it wins, an adapter with zlib fallback.
8. Build `SERVICE_INTERCEPTION_MAP.md` (list of proxy clusters from VirtualApp/Evoke/Robolectric) — a targeted map for F007/F010.
9. Environment simulation: controllable clock + reset-state between runs (@Resetter pattern) — structural determinism.
10. Put the full 100+ corpus registry in the repo (JSON/CSV in `tests/corpus/results/`) — the current claim is not verifiable from the clone.

# TOP 10 THINGS NOT TO IMPLEMENT

1. KVM/container paths (redroid/cuttlefish/Waydroid) — outside the headless mission.
2. Chromium/Servo embed (WebView) — forbidden without evidence (§8); WPE DEFER only.
3. F012-AMPLIFIER (unmerged branch ab48fbc) — UC-CM-001 closed the goal with less risk.
4. Rewriting proven decoders (PNG/WebP/JPEG/RLottie).
5. fdk-aac (conditional license) and Unicorn in-process (GPL).
6. RapidJSON/LevelDB/RocksDB/DuckDB/Cronet/Cairo/Pango/NanoVG (rejected by the matrix).
7. Fully replacing BitmapFont before FontBackend is ready (fallback needed).
8. Telegram-specific mapping in core (all mappings must be generic from ARSC).
9. Premature Rust migration (§ priority 10 of the second charter).
10. Wide Google Play Services — census only (§31).

# CURRENT BLOCKERS

- PUSH_PENDING — no push credential in the sandbox.
- RLottie render on v12: needs the R$raw map (resolved by action 5).
- Corpus 100+: registry outside the clone — UNKNOWN per §18.
- non-Telegram regression for this campaign: NOT RUN (corpus download not done) — recorded per §18.
- ASAN for this campaign: NOT RUN (the change was value-mapping only; review done).

# HIGHEST-VALUE SOURCES

- AOSP: `TextDirectionHeuristics`, `Uri.java`, minikin `Layout` (shape-per-run)
- Robolectric: `AndroidTestEnvironment`, `@Resetter`, `SQLiteMode.NATIVE` (nativeruntime)
- Paparazzi/Roborazzi: capture-at-canvas + diff engines (PixelPerfect/MSSIM/ΔE2000)
- VirtualApp proxies/ + Evoke (0BSD): service-interception map
- dexlib2: cross-check for the DEX parser
- Tooling matrix: `WS-C4_TOOL_MATRIX.md` (top ten candidates)

# REAL APK PROOF

| APK | SHA256 (prefix) | Result |
|---|---|---|
| Telegram 12.10.1 vc70389 | `f5e1192725…` | exit=0 · 12,544 classes · 41,233px · 3/3 deterministic · identical before/after UC-CM-001 |

# BACKEND RECOMMENDATIONS

| Backend | First choice | Alternative | Source |
|---|---|---|---|
| Font | FreeType+HarfBuzz+FriBidi (proven) | BitmapFont fallback | WS-C2 |
| Image | libpng+libjpeg-turbo+libwebp (present) + Wuffs long-tail | stb_image decode-only | WS-C4 |
| Animation | rlottie (present) | ThorVG v1.0 (DEFER) | WS-C4 |
| Database | SQLite amalgamation | SQLCipher (DEFER) | WS-C4 |
| Network | libcurl+OpenSSL/mbedTLS | curl's built-in nghttp2 | WS-C4 |
| Archive | zlib (present) + libdeflate (hot path) + zstd/lz4 | — | WS-C4 |
| Audio | miniaudio (deterministic decode→PCM) | libFLAC/opus/vorbis/mpg123 direct | WS-C4 |
| Video | FFmpeg-trim (oracle→adapter) | dav1d/libvpx per-codec | WS-C4 |

# REGRESSION RISKS

1. UC-CM-001 changes STUBBED values → apps that "happened to" work with void may take a different path (e.g. if-nez now sees false instead of stale). **Current campaign: zero regression; but re-run the full corpus after merge.**
2. New FontBackend → the visual output of all screens changes; PNG/SHA baselines must be re-baselined.
3. Automatic resource-map from ARSC → may differ from the current hand mapping in a few cases; the OX gate afterwards is mandatory.
4. libdeflate → byte-level output may differ (only speed should differ; keep the CRC gate).

# CONFIDENCE

| Topic | Confidence | Reason |
|---|---|---|
| UC-CM-001 regression-free | HIGH | 3/3 SHA + equal trace counts + fallback logic |
| Uri/SystemClock absence | HIGH | grep over the whole src (two methods) |
| typography POC | HIGH | image + metrics JSON + library versions |
| tooling matrix | MED-HIGH | mid-2026 web research; 3 items marked UNVERIFIED |
| WS-C5 synthesis | HIGH | 12 projects with sources; uncertain items flagged |
| forward-compat v12 | HIGH | real deterministic execution |

---

# Appendix: delivery list (this pack)

| File | Content |
|---|---|
| `SOURCE_CHANGES.md` | **source changes + full explanations for future application** (your request) |
| `0001-UC-CM-001-….patch` | patch applicable via `git am` |
| `WS-C2_KNOWLEDGE.md` / `_PRIMARY_TRANSFER.md` / `_EVIDENCE.md` | graphics/text/animation |
| `WS-C3_KNOWLEDGE.md` / `_PRIMARY_TRANSFER.md` / `_CORPUS.md` | framework/corpus |
| `WS-C4_TOOL_MATRIX.md` / `_PRIMARY_TRANSFER.md` / `_TO_C2_C3.md` | tools |
| `MINIANDROID_EXTERNAL_RUNTIME_KNOWLEDGE.md` / `_INDEX.md` / `WS-C5_PRIMARY_TRANSFER.md` | external runtimes |
| `CROSS_WORKSTREAM_TRANSFERS.md` | transfers + CROSS_CODER_RECONCILIATION |
| `SOURCE_REFERENCE_INDEX_UPDATE.md` | append to SOURCE_REFERENCE_INDEX |
| `wsc2_text_pipeline.cpp` + images | typography POC + evidence |
| `uc_v12_top.png` and previews | v12 visual evidence |

Suggested commit location in the repo:
- WS documents → `docs/runtime/knowledge/`
- `SOURCE_CHANGES.md` → repo root
- POC → `miniandroid/scripts/`, image evidence → `run/` (or `docs/knowledge/assets/`)
