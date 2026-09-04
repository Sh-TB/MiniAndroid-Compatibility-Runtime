# MASTER_PROJECT_STATE_011 — canonical project state

Generated: 2026-08-30 (UTC+3), CAMPAIGN 011 recovery session.
Companion files: `MASTER_CHANGELOG_KNOWLEDGE_011.md` (history),
`MASTER_HANDOFF_011.md` (onboarding), `status.json` (machine-readable).

---

## 1. Project

**MiniAndroid** — a research-grade Android APK compatibility runtime in C++17:
parses real APKs (ZIP + DEX + `resources.arsc` + AXML), interprets real Dalvik
bytecode with a register VM, bridges Android framework APIs through a shadow
layer, inflates real layouts into a ViewShadow tree, and renders frames to a
software framebuffer with deterministic pixel-evidence output. Acceptance has
always been: **real APKs, full journeys, byte-stable evidence**.

## 2. Current GitHub state

| item | value |
|---|---|
| remote | `origin` = https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime.git |
| upstream | NOT AVAILABLE (no second remote configured) |
| REMOTE_HEAD (`origin/main`) | `bbe0ce3` (verified via `git ls-remote` this session) |
| REMOTE_DEFAULT_BRANCH | `main` |
| LOCAL_HEAD | `937f043` (final; docs+START_HERE included) |
| LATEST_TAG | none yet — `v0.11-unified-011` created locally this session |
| DIVERGENCE | local ahead by 9 commits, 0 behind (86bd646 f2e8ad9 7cc4254 8f0a85b 23900f8 288ff6f +3 docs/cleanup commits) |
| PUSH | PUSH_PENDING — no credentials in this environment |

## 3. Architecture (subsystems, all in `src/`)

| subsystem | files | state |
|---|---|---|
| APK/ZIP parser | `apk/apk_parser.cpp`, `manifest_reader.cpp` | PROVEN (streaming ZIP, data descriptors, CRC) |
| DEX parser + class resolver | `dex/dex_parser.cpp`, `class_resolver.cpp` | PROVEN (multi-DEX, 5-DEX Telegram) |
| Dalvik interpreter | `dex/dalvik_engine.cpp`, `dex_interpreter_batch.cpp` | PROVEN on corpus; partial opcode/API coverage documented |
| Execution engine / journey stages | `runtime/execution_engine.cpp` | PROVEN (click/chain stages, render stages) |
| Resource parser (legacy sidecar) | `resources/resource_parser.cpp` | retained for compatibility |
| **Real resource pipeline (UNIFIED_007)** | `resources/arsc_parser.cpp`, `axml_parser.cpp`, `layout_inflater.cpp`, `resource_runtime.cpp` | PROVEN on non-obfuscated APKs (gmdice/simplestopwatch), guarded fallback otherwise |
| Renderer | `renderer/software_renderer.cpp` | PROVEN (PNG out, custom PNG/JPEG/WebP decode; libpng linked but decode path still custom) |
| Framework shadows | `framework/android_shadows.cpp` (95+ bridged classes), `shadow_registry.cpp` | PROVEN core; long tail STUBBED (type-aware defaults since `86bd646`) |
| Storage / prefs / file sandbox | `api/shared_prefs.cpp`, `storage/file_sandbox.cpp` | PROVEN (prefs persisted to `runtime/data/...`) |
| Diagnostics / observability | `diagnostics/trace_engine.cpp`, `dex/trace_exporter.cpp` | PROVEN (api_trace.json, click audit) |
| Lottie | external rlottie static lib | PROVEN (RLottieImageView wired, EXP-098/CM-027) |

## 4. Current proven capabilities (with evidence)

1. **Telegram v12.10.1 deterministic journey** — exit 0, 12,544 classes,
   41,233 non-white px, screenshot SHA `06fb40da16b1f473980cfea9b0dc83d9d1707c2573cf713d636fd91d196503b3`,
   **3/3 identical** this session AND exact match to UNIFIED_002 baseline. (VERIFIED)
2. **SMS auth chain at controlled boundary** — `onNextPressed` → `TL_auth_sendCode`
   → mocked `TL_auth_sentCode(type=Sms,len=5,timeout=30)` → `setPage(2)`.
   EXP-100 trace (UNIFIED_002). Real SMS/network NOT proven by design. (VERIFIED, boundary-limited)
3. **Real layout inflation (recovered UNIFIED_007)** — GMDice: `views=10 strings=2`,
   real UI texts rendered (`6425c0f6…`, 158,040 px). Simple Stopwatch: `views=11`,
   real Start/Reset controls (`ef334f7c…`, 930,980 px). (VERIFIED this session)
4. **Zero-regression guard** — headingcalc non-substantive inflation rejected →
   fallback byte-identical to HEAD baseline (`c200c521…`). (VERIFIED)
5. **Corpus execution** — 8-app canonical matrix: 7/8 exit 0; failures are
   pre-existing and baseline-identical (detailed in TEST_MATRIX.md). (VERIFIED)
6. **Persian/RTL shaping POC** — FriBidi 1.0.16 → HarfBuzz 10.2.0 → FreeType,
   6/6 samples (EXP-101, UNIFIED_002). POC-level: not the runtime TextView path. (VERIFIED as POC)
7. **Lottie on SMS screen** — EXP-098/CM-027 (rlottie static build). (VERIFIED historical commit)
8. **Deterministic evidence pipeline** — every run emits screenshot.png +
   api_trace.json + report.md; hashes reproducible across machines
   (dev binary vs clean-clone binary: identical screenshots). (VERIFIED)

## 5. Current partial capabilities

- `@string/` references inside inflated layouts are not resolved yet
  (headingcalc: `strings=0` → guarded fallback). Next: ARSC string-ref
  resolution in `layout_inflater.cpp`.
- Obfuscated resource trees (`res/0s.xml`, aapt2 name shortening) unsupported.
- Renderer image decode: custom PNG decoder (palette/tRNS supported since
  EXP-096), libwebp/libjpeg linked and used; **libpng linked but the decode
  path is still the custom one** (CAMPAIGN 010 R1 replacement NOT done — recorded honestly).
- Layout geometry: weight/measure semantics incomplete (simplestopwatch
  buttons stretch full-height). TextView text overlap under long strings (SFS-010).
- Robolectric oracle: builds and runs 1/1 as an external tool (EXP-102), not a
  CI-integrated oracle.

## 6. Current blockers

| blocker | root cause | evidence | next step |
|---|---|---|---|
| Dooz / Compose blank render | Compose view hierarchy expectations (on-demand inflation, kotlin intrinsics); UNIFIED_002 root-caused Kotlin Intrinsics NPE class | both baseline & current builds render `c035e9ba…` blank | prioritize Compose runtime shims or declare unsupported tier |
| tictactoe blank render | same family (blank since long ago; byte-identical baseline) | this session A/B | investigate after string-refs |
| real GLES/3D on real APKs | software 3D exists in renderer; no GLES/EGL backend | PortableGL/SwiftShader/ANGLE researched (CAMPAIGN 010, HISTORICAL) | integrate PortableGL backend behind an interface |
| Telegram real config edge cases | theme/locale pref writes differ across versions (default.xml churn observed) | this session runtime diff | pin prefs fixture per version |
| stopwatch corpus APK | truncated central directory | androguard agrees (UNIFIED_002) | re-download source |

## 7. Current tests

- `scripts/u011_test_matrix.py` — canonical 8-APK matrix; JSON summary;
  baseline SHA assertions for telegram_v12.
- `tests/` — per-experiment python/c++ checks (EXP-031.5 opcode tests,
  EXP-085 phases, EXP-088 PNG decoder tests, …).
- `tests/tools/` — arsc_tool / axml_tool / resolve_debug diagnostics (recovered).
- Robolectric oracle (external): `tools/robolectric-oracle` (target/ ignored).

## 8. Open-source integrations

See `OPEN_SOURCE_MASTER.md`. Integrated & load-bearing: rlottie, libwebp,
libjpeg-turbo, zlib, nlohmann/json, FreeType+HarfBuzz+FriBidi (POC path),
libpng (linked). Researched-not-integrated: Yoga, PortableGL, SwiftShader,
ANGLE, SkiaUI2/Skiko, resvg, ARSCLib, apktool, JADX, dexlib2/smali, Wuffs,
stb_image, libjpeg-turbo-vs-libjpeg comparisons.

## 9. Current corpus

`tests/corpus/apks.json` — 16 registry entries (15 F-Droid corpus + Telegram
10.14.5 + Telegram v12.10.1 = 16 rows incl. both Telegram versions). Storage:
EXTERNAL cache only (`MINIANDROID_APK_CACHE`, default `<repo-parent>/../apk_cache`).
Repository is ZERO-APK (verified this session: 0 tracked .apk/.aab).

## 10. Current release

`UNIFIED_011_CANONICAL` (local tag `v0.11-unified-011` on `937f043`).
GitHub Release: NOT AVAILABLE this session (no credentials). Release notes:
`RELEASE_NOTES_UNIFIED_011.md`. Handoff package:
`UNIFIED_011_CANONICAL_HANDOFF.zip` (built this session; SHA-256 in
`UNIFIED_011_CANONICAL_HANDOFF_SHA256.txt` alongside the zip).

## 11. Next recommended actions (priority order)

1. **ARSC string-ref resolution** in the inflater (`@string/…`, `strings=0`
   cases) — unlocks headingcalc-class apps; keep the substantive guard.
2. **Weight/measure semantics** in `measure_layout` (simplestopwatch geometry).
3. **Obfuscated resource names** — ARSC file-path mapping for `res/<hash>.xml`.
4. **libpng switch** for renderer PNG decode (CAMPAIGN 010 R1 — still custom).
5. **PortableGL GLES backend** behind a renderer interface (R9/R10 follow-up).
6. Push the 6 pending commits + tag when credentials are available
   (§35: `git push origin main && git push origin --tags`).

## 12. Consistency

All numbers in README / MASTER_* / TEST_MATRIX / status.json / evidence index
cross-check against this file (audited this session, §45).
