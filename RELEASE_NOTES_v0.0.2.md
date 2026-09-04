# Release v0.0.2 — Australorp (2026-09-04)

**The proof release.** For the first time, a public visitor can see — not
just read — that MiniAndroid executes a real Android APK end-to-end.

## Highlights

### 1. Real-APK execution proof (the headline)

A dedicated, MIT-licensed demo app (`demo/`, built with official Android
toolchain components: Eclipse ECJ 3.33 + AOSP D8 8.13.23 + Google API-34
`android.jar`) runs through MiniAndroid and demonstrates the complete chain:

```
APK install -> Activity.onCreate (122 real DEX instructions)
  -> programmatic View hierarchy -> rendered 1080x1920 frame
  -> dispatched click -> DEX onClick -> step()
  -> counter++ / box moves / color cycles / status text rebuilt
  -> re-render -> screenshot -> 9 frames + SHA256 manifest + GIF
```

* 8/8 clicks dispatched, ~51,000 pixels changed per click
* frame hashes all distinct; state sequence exactly as the DEX logic dictates
  (`count=1..9`, box cycling a 5x4 grid, red->green->blue->yellow palette)
* rendered pixels verified against the app's own on-screen state text
* deterministic replay: three clean runs -> byte-identical SHA256 sequences
* one command reproduces everything:
  `./run-miniandroid.sh run miniandroid-demo.apk -o proof --click-count 8`

Evidence: [docs/demo/EVIDENCE.md](docs/demo/EVIDENCE.md) · strip:
[docs/demo/demo_frames.png](docs/demo/demo_frames.png) · GIF attached to this
release (`miniandroid-demo-proof.gif`, assembled only from runtime frames).

### 2. Runtime fixes the proof forced into the open (AOSP-aligned)

| Fix | Impact |
|---|---|
| `onCreate` invoked without `this` (both entry paths) | every instance-field write inside `onCreate` was silently dropped; per AOSP `ActivityThread.performLaunchActivity` both paths now pass `[this, savedInstanceState]` with real code_item register sizes |
| `<clinit>` ran only for `org.telegram.*` | every other app's static final constants were null; now AOSP `ClassLinker::EnsureInitialized` semantics (first active use, re-entrancy guarded), `new-instance` triggers init too |
| `array-length` + all `/2addr` arithmetic read the wrong register nibble (`>>4` vs `>>12`, AOSP 12x = `B\|A\|op`) | `array-length v1, v0` read v2; `rem-int/2addr v1, v0` read v11 |
| plain-text manifest parser broke on AAPT-style multi-line tags | launcher activities were missed; entry-point search silently fell back to a name heuristic |
| the whole 12x/22s decode family (conversions, neg/not, wide /2addr, lit16, move-wide) decoded the mirror image of AOSP `B\|A\|op` — and the hand-built fixture encoders carried the same swap, cancelling out inside the suites while real DEX broke | every dest≠src conversion/negation on real D8 bytecode mis-decoded; engine + fixtures now uniformly AOSP, all semantic suites re-verified green (14/14, 55/55, 25/25) |

### 3. Regression status (13-APK open-source corpus, OLD vs NEW)

* 12/13 byte-identical — including the `simplestopwatch` pixel-exact golden
  (`2a12587a…`) on both binaries.
* 1 improvement: **microtimer** now completes its real `onCreate` (120 method
  entries vs 10 before) and renders its actual view tree (LinearLayout +
  ScrollView + buttons + custom `RoTimeControl` view) instead of a blank
  screen. Old hash `eb16ab5c…` documented as a symptom, not a law.
* 0 regressions. Pre-existing `stopwatchmuellerma` PARTIAL unchanged.

### 4. Windows binary is real

`MiniAndroid.exe` (PE32+ x86-64, UCRT, statically linked codecs) is built by
the reproducible pipeline `miniandroid/scripts/build_windows.sh` (llvm-mingw
20260826 + pinned upstream deps) and carries the same fixes as the Linux
binary. It imports only KERNEL32 and the UCRT — no bundled DLLs. Note: the
release host has no Wine; native-Windows smoke testing remains on the
checklist — the build recipe itself is pinned and auditable.

## Artifacts

| File | Purpose |
|---|---|
| `MiniAndroid-v0.0.2-Australorp-linux-x64.tar.gz` | Linux x64 runtime (stripped) + launcher + demo APK |
| `MiniAndroid-v0.0.2-Australorp-windows-x64.zip` | native `MiniAndroid.exe` + demo APK — runtime-only package, no toolchain, no DLLs needed |
| `miniandroid-demo-proof.gif` | animated proof (from runtime frames only) |
| `SHA256SUMS_v0.0.2.txt` | checksums for all artifacts |

Every package is produced by `scripts/package_release.sh` and gated by
`scripts/validate_release_content.py` (`RELEASE_CONTENT_CHECK: PASS`,
`DEVELOPMENT_ARTIFACTS: 0`) plus `scripts/release_clean_extract_test.sh`
(demo APK executed from a clean extraction of the shipped archive with a
deterministic per-frame SHA256 replay). The packages contain only the
runtime files — no compiler, no dependency source trees, no build trees.

Demo APK `miniandroid-demo.apk` SHA256:
`ffb50bc7826cd9512455443dc8ee6477ceca703fbb964d5706be47ed986022c1`

Linux binary (stripped; virtual-clock Looper, --frames time-driven capture, activity <init> fix) SHA256:
`a5f1d0eee8d73c4b89ecb8b14439bb7835a64fd059ffb3c0c2d03e822125cb70`

Windows `MiniAndroid.exe` SHA256:
`e1886d1f7cb7058e42c1a5e4d416c7898ab8b2891df9b43025fc4f478fa5872c`

Package SHA256 (see `SHA256SUMS_v0.0.2.txt` for the authoritative copy):

```
c24f5caa68984cd2414063f4e490a5a53cc240c2504b896d9432139bf70f11cc  MiniAndroid-v0.0.2-Australorp-linux-x64.tar.gz
b4360f186feb3d8515e0ffa1355c3188fa0965ff38167ae216e80ca5784e0c3a  MiniAndroid-v0.0.2-Australorp-windows-x64.zip
```

## Known limitations (transparent)

Same honest list as v0.0.1, unchanged in scope: Compose apps render a
deterministic blank frame; GLES/GLSurfaceView loop not wired; layout weight
approximation; BitmapFont long-string overlap; audio lane out of default
build; Telegram golden APK bytes still unreacquired; no Wine validation for
the Windows exe in this release cycle. Full list:
[README.md § Known Limitations](README.md#known-limitations-real-current--nothing-hidden).

## Try the proof yourself

```bash
tar xzf MiniAndroid-v0.0.2-Australorp-linux-x64.tar.gz
cd MiniAndroid-v0.0.2-Australorp-linux-x64
./run-miniandroid.sh run miniandroid-demo.apk -o proof --click-count 8
cat proof/frames/manifest.json     # per-frame state + SHA256 evidence
```

Expected: 9 frames, `count=1..9`, positions cycling, colors cycling, and the
exact hash sequence documented in `docs/demo/EVIDENCE.md`.
