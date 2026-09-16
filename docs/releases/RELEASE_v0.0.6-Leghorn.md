# v0.0.6 — Leghorn (Repository Recovery, Battery Restoration, Evidence Compaction)

**Date:** 2026-09-16 · **Lineage:** S45 tip (b82b43c5) → S48 · **Registry:** 348 roots, honest per-root status

Named after the Leghorn hen — continuation of the release-mascot breed line
(Brahma → Australorp → Chantecler → Silkie → **Leghorn**). This is a
repository-recovery and release-hygiene release: **zero engine behavior
change except one generic storage fix (R-NEW-367)**, with the regression
battery fully restored and re-proven.

## Added

- `scripts/build/bootstrap_toolchain.sh` — one-command, hash-verifiable
  restoration of the fixture toolchain: aapt2 8.13.2-14304508 (Google Maven),
  ECJ 3.33.0 (Maven Central), r8 8.13.23 (Google Maven), android-34 framework
  stubs (Robolectric `android-all-14` mirror — the Google Maven
  `platform-34-ext7_r03` artifact is not public; `curl -f` so a 404 can never
  become a fake jar).
- `scripts/testing/BATTERY_INDEX.json` — machine-readable inventory of all 94
  battery stages (id, name, category, status) generated from a clean,
  no-cache run at this tag.
- `docs/evidence/ARCHIVE_MANIFEST.json` — 359 entries with per-file SHA-256,
  size, reason and issue for every artifact moved out of the operational tree.
- `scripts/maintenance/s48_archive_exhaust.py` — reproducible classification
  tool (dry-run + `--apply`) that produced the archive manifest.
- `scripts/release/check_release_artifacts.sh` — pre-release guard (S48 §23):
  fails if a staging tree or archive contains logs, traces, dumps, run
  outputs, forensic session dirs, VCS internals, build caches, or any artifact
  far above the recorded size envelope.
- `docs/upstream/INDEX.md` + `MessageSchema.java` relocated to
  `docs/upstream/` — upstream semantic-law index and the R-NEW-351 ground
  truth reference out of the repo root.

## Fixed

- **R-NEW-367 (VERIFIED-FIXED, P1)** — the SharedPreferences shadow
  hard-coded the EXP-era data dir `org.telegram.messenger/shared_prefs` for
  *every* app: any non-Telegram APK loaded prefs from / stored prefs into the
  wrong package directory. Per the AOSP `ContextImpl.getPreferencesDir` law
  the directory now resolves from the manifest-derived package (the same
  source `Context.getPackageName` uses). Generic fix, no package checks.
- `build_fixture_apk.sh` — framework stubs now compile on `-classpath`
  instead of `-bootclasspath`: the Robolectric android-all jar carries no
  `java.*` classes, so `-bootclasspath` broke `java.lang.Object` resolution
  (24 fixture compile errors).
- `build_windows.sh` — engine source list re-synced with the Linux Makefile's
  canonical lists; sqlite 3.46.1 amalgamation pinned and linked (matches the
  Linux system sqlite the battery runs against); `-D_USE_MATH_DEFINES` for
  MinGW `M_PI`; FreeType file list completed with `ftdebug.c` and
  `winfnt.c` (upstream INSTALL.ANY law); `text_shaper.cpp` exe-path
  resolution made portable (`GetModuleFileNameA` on Windows, `/proc/self/exe`
  on POSIX — Linux behavior byte-identical).
- `package_release.sh` / `release_clean_extract_test.sh` — REPO_ROOT
  resolution fixed after the scripts/ migration (both were silently pointing
  one level short and failing on a clean checkout).

## Improved

- Repository footprint: **1,076.3 MB of raw campaign exhaust (244 files)
  moved to the external archive** (`/home/z/archive/miniandroid`) with SHA-256
  provenance; 115 compact GPG-092..095 session records (0.58 MB) relocated to
  `docs/evidence/solved/gpg_092_095_session/`. Git history retains every
  blob — no history rewrite, lineage fully preserved.
- `.gitignore` hardened: raw run dumps (`*_stderr.txt`/`*_stdout.txt`) and
  `gpg_*` forensic session dirs are rejected at add time.
- `root_registry.json` summary canonicalized (total 347→348 roots, true
  frontier list, canonical status vocabulary, 4 lowercase `implemented`
  entries normalized).

## Testing

- **Battery: 94/94 ALL PASS** (`bash scripts/test/run_test_battery.sh`,
  clean run, no resume cache) — including §28 HelloWorld (26 checks),
  §29 TicTacToe interaction+determinism (8 checks), EXT-01 typography 9/9,
  EXT-02 interaction 12/12, G06/G07/G08 3-run frame-SHA determinism, and all
  fixture pixel goldens. Before this release the battery recorded 90/92 with
  EXT-01/EXT-02 env-blocked (external fixture missing) — the fixtures are now
  restored SHA-exact and the missing toolchain rebuilt.
- **Windows build**: `MiniAndroid.exe` PE32+ x86-64, 9,582,080 B, statically
  linked (UCRT + KERNEL32 only); clean-extract smoke test re-runs the demo
  app and byte-matches the committed per-frame SHA256 evidence.
- **Release clean-extract test: PASS** — both archives extract and run
  standalone with deterministic replay (wine not available: Windows check is
  static-PE + extract only, honestly labeled).

## Evidence

- Battery inventory: `docs/testing/BATTERY_INDEX.json` (94 stages, all PASS)
- Registry: `root_registry.json` (348 roots; primary frontier R-NEW-361)
- Archive provenance: `docs/evidence/ARCHIVE_MANIFEST.json` (359 entries)
- Release manifest: `docs/releases/RELEASE_MANIFEST.json`
- Artifacts: `MiniAndroid-v0.0.6-Leghorn-linux-x64.tar.gz` (SHA256
  `20ece925…`), `MiniAndroid-v0.0.6-Leghorn-windows-x64.zip` (SHA256
  `934d6edc…`)

## Known Limitations (honest, unchanged by this release)

- **R-NEW-361** (OBSERVED-FAIL, primary frontier) — dooz v18/v23 converge on
  one face: compose SlotTable/ScatterMap probe arithmetic yields negative
  32-bit indices (HALT-LOOP → aput-oob). Evidence and narrowing plan
  registered; not fixed here.
- Compose final UI not yet visible for dooz; 2048 renders only via the older
  simple model and is **not** claimed playable; Telegram stops at the
  desugared-streams gap (**R-NEW-303**).
- Windows runtime verification is static (no wine/native Windows in this
  environment) — labeled as such, not claimed as native verification.
- Battery stage count varies with conditional stages (94 in this
  environment); `BATTERY_INDEX.json` is the canonical inventory.
