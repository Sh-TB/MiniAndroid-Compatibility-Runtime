# Windows x86_64 toolchain recipe + measured portability diagnosis (S214-WP1, #587)

**Status: Windows artifact BLOCKED — measured, not assumed.** This document is the pinned
recipe and the exact blocker evidence required by S214-WP1 ("Add a Windows build workflow
and a pinned toolchain recipe... If the current source genuinely cannot build on Windows,
diagnose and fix portability errors"). R19 stays OPEN until a real PE x86-64 artifact
passes the full acceptance battery.

## 1. Pinned cross-compile route (the attempt that produced this diagnosis)

The build environment has no Windows VM, no wine, and no `apt` mingw-w64 access (no root).
The reproducible cross route used for the probe:

```bash
pip install ziglang==0.17.1          # pinned; bundles mingw-w64 headers + CRT
cd miniandroid
python3 -m ziglang c++ -target x86_64-windows-gnu -std=c++17 -fsyntax-only \
    -Isrc -Isrc/apk -Isrc/dex ... src/dex/dalvik_engine.cpp
```

`scripts/release/build_windows_zig.sh` runs the same probe over the four representative
translation units below and fails with the recorded errors (that failure IS the current
honest Windows result). When the dependency/porting blockers are cleared, the same script
is extended to `zig build-exe` + `package_release.sh --platform windows`.

## 2. Measured diagnosis (2026-11-13, zig 0.17.1, `-target x86_64-windows-gnu`)

| TU (representative) | First failure | Windows port required |
|---|---|---|
| `src/dex/dalvik_engine.cpp` | `fatal error: 'dlfcn.h' file not found` | dlopen/dlsym/dlerror → `LoadLibraryW`/`GetProcAddress` shim |
| `src/apk/apk_parser.cpp` | `fatal error: 'zlib.h' file not found` | Windows zlib build (pinned source or vcpkg) |
| `src/main.cpp` | `fatal error: 'execinfo.h' file not found` | glibc `backtrace()` → DbgHelp/`CaptureStackBackTrace` port |
| `src/storage/sqlite_shadow.cpp` | `fatal error: 'sqlite3.h' file not found` | Windows sqlite3 amalgamation build |

`grep -rl` census on current main: **15 tracked sources** use POSIX-only APIs
(`dlopen` / `mmap` / `pthread_create` / `sys/utsname` / `execinfo` families).

## 3. The dependency matrix (the real blocker)

`miniandroid/Makefile` links: `z libjpeg sqlite3 ssl crypto mpg123 sndfile pthread stdc++ m`
plus `freetype harfbuzz fribidi png webp webpdemux`. None of these ships Windows builds in
the tree; a Windows binary requires **11 C-dependency families** built for
x86_64-windows-gnu first (vcpkg manifest or pinned-source builds, each with license +
provenance records per §172), then the POSIX shim layer, then the full acceptance battery
(version/help smoke, one native APK integration test, one deterministic output comparison,
out-of-source execution) on a real Windows host/runner — none of which can be run in this
environment today.

## 4. CI wiring (same PAT-scope constraint as policy.yml)

`docs/ci/windows-build.yml` + `docs/ci/windows-release-gate.yml` are shipped here because
the release token lacks the `workflow` scope to push `.github/workflows/`. Activation:
copy both to `.github/workflows/` with a workflow-scope token. The release-gate job runs
`scripts/release/validate_release_manifest.py` (works locally today — it is what keeps a
"stable"-labelled release with a missing Windows artifact from ever passing) and fails any
release whose required platforms are not both PASS with evidence.

## 5. Acceptance to un-BLOCK (S214-WP1 verbatim requirements)

1. Real PE32+ `MiniAndroid.exe` built from the exact release tag/commit (not a relabel,
   not a placeholder).
2. Archive contents validated (`validate_release_content.py --platform windows`),
   PE architecture + DLL dependency inspection recorded.
3. Windows-host smoke: version/help, one native APK integration test, one deterministic
   output comparison, out-of-source execution — logs + hashes.
4. `RELEASE_MANIFEST.json` windows-x64 flips to PASS with sha256/bytes/provenance; the
   manifest gate and the GitHub release page must agree.
5. Only then may R19 close and the release be labelled stable/cross-platform.
