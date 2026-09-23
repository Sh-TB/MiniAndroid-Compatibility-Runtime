# WS-C4 TOOL MATRIX — open-source tooling matrix (WS-C4-RESEARCH merged)

**Date:** 2026-08-27 · research status: web search (mid-2026 window) · uncertain items: UNVERIFIED
**Adoption units:** USE / ADAPT / ORACLE-ONLY / REFERENCE / DEFER / REJECT
**Currently linked in the runtime:** zlib, libwebp+libwebpdemux, libjpeg, rlottie (static), nlohmann/json

## GRAPHICS

| name | license | latest | build | C API | maintenance | size | relevance | class |
|---|---|---|---|---|---|---|---|---|
| Skia | BSD-3+patent | M144 (2025-12) | GN/Ninja | ❌ (C++) | very active | 30–70MB | med | **REFERENCE** |
| Blend2D | zlib | 2025-03 | CMake+asmjit | ✅ | active | 3–5MB | med | DEFER |
| ThorVG | MIT | v1.0 (2026-01) | CMake/Meson | ✅ | very active | 0.5–1.5MB | med | **DEFER** (rlottie successor) |
| NanoVG | zlib | discontinued | — | ✅ | dead | ~0.3MB | none | **REJECT** |
| Cairo | LGPL/MPL | 1.18.4 (2025-03) | Meson | ✅ | slow | 3–6MB | low | REJECT |
| Pango | LGPL | 1.56.x | Meson | ✅ | active | 5–10MB | low | REJECT |

## GPU / SW-RASTER

| name | license | C API | size | class | Note |
|---|---|---|---|---|---|
| ANGLE+SwiftShader | BSD/Apache | EGL/GLES | 30–60MB | **DEFER** | the only valid GLES path; after a GLES workstream exists |
| Mesa llvmpipe | MIT | GL | large | REJECT | heavy LLVM dependency |
| lavapipe | MIT | Vulkan | large | DEFER | |
| Zink | MIT | GL-on-Vulkan | — | REJECT | overhead on CPU |

## IMAGE

| name | license | latest | class | Note |
|---|---|---|---|---|
| stb_image | Public domain | 2.30 (2023) | **USE** (long-tail) | single file; BMP/GIF/TGA; for faster PNG/JPEG keep the original libpng/libjpeg-turbo |
| libpng | zlib | — | (present/current path) | PNG write needed |
| libjpeg-turbo | BSD-3 | — | (present) | |
| libwebp | BSD | 1.6.0 (2025-06) | (present) **USE** | demux is linked too |
| Wuffs | Apache-2.0 | 0.4.0-alpha.10 | **USE** | safe, memory-safe decode (GIF/NIE) |
| OpenJPEG | BSD-2 | 2.5.4 (2025-09) | DEFER | JPEG2000 is rare |
| libavif | BSD-2 | 1.3/1.4 (2025/26) | DEFER | AVIF is growing |
| libheif | LGPL-3 | 1.20.2 | DEFER | HEVC patent / x265 GPL risk |
| libjxl | BSD-3 | 0.11.1 | DEFER | 5–15MB |
| APNG | — | — | **ADAPT** | acTL/fcTL on libpng/Wuffs; no healthy standalone lib |

## ANIMATION — rlottie (present, USE) · animated-WebP via libwebpdemux (present, frame iteration remaining — CM-027 future)

## AUDIO

| name | license | latest | class |
|---|---|---|---|
| miniaudio | PD/MIT | 0.11.25 | **USE** (single file; playback+device) |
| Oboe | Apache | — | REJECT (Android-only) |
| PortAudio | MIT | 2019 dormant | REJECT |
| OpenAL Soft | LGPL | 1.25.2 | DEFER |
| libopus | BSD | 1.6.1 (2026-01) | USE |
| libvorbis | BSD | 1.3.7 | USE |
| libFLAC | BSD | 1.5.0 | USE (previous Coder4 bit-exact proof) |
| libmpg123 | LGPL | 1.33.x | USE |
| fdk-aac | conditional Fraunhofer | — | **REJECT** (license+C++ API; FFmpeg AAC is enough) |
| FFmpeg (audio) | LGPL-2.1+ | 8.0 (2025-08) | ADAPT (trim) |

## VIDEO

| name | license | latest | class |
|---|---|---|---|
| FFmpeg | LGPL-2.1+ | 8.0 | **ADAPT** — the main decode→frame→Bitmap path |
| GStreamer | LGPL | — | REJECT (a 50MB+ framework) |
| dav1d | BSD-2 | 1.5.2 (2025-11) | DEFER (AV1) |
| openh264 | BSD | 2.6.x | DEFER (patent pledge is Cisco binaries only) |
| libvpx | BSD | 1.15.1 (2025-01) | DEFER |
| libaom | BSD | 3.12.x | ORACLE-ONLY (slow) |
| Media3/ExoPlayer | Apache | — | REJECT (JVM/Android) |

## NETWORK

| name | license | latest | class |
|---|---|---|---|
| OkHttp | Apache | — | REJECT as a linked lib (JVM; inside APKs it runs by itself) |
| libcurl | curl | 8.14.0 (2025-05) | **USE** (first NetworkBackend) |
| Cronet | Apache | — | REJECT (Chromium stack) |
| nghttp2 | MIT | 1.68.0 | USE (usually via curl) |
| OpenSSL | Apache-2.0 | 3.5 LTS | USE |
| mbedTLS | Apache | 3.6 LTS | USE (smaller alternative) |
| BoringSSL | — | no versioning | DEFER |

## DATABASE

| name | license | latest | size | class |
|---|---|---|---|---|
| SQLite | Public domain | 3.50.x (2025) | ~1.5MB | **USE — critical** (11/11+ proven by Coder4; Precedent: Robolectric nativeruntime also bundles real SQLite) |
| SQLCipher | BSD | 4.10.0 (2025-08) | — | DEFER |
| LMDB | OpenLDAP | 1.0.0 (2026) | ~0.1MB | DEFER |
| LevelDB | BSD | 1.23 (2021) | — | REJECT (limited maintenance, self-declared) |
| RocksDB | GPLv2/Apache | 11.x | 10–25MB | REJECT |
| DuckDB | MIT | 1.4/1.5 | 40–80MB | REJECT |

## SERIALIZATION

| name | license | latest | class |
|---|---|---|---|
| protobuf | BSD | 31.x | DEFER (abseil dep) |
| FlatBuffers | Apache | 25.12.19 | DEFER |
| MessagePack (libmpack) | MIT | — | DEFER |
| tinycbor | MIT | 0.6.1→7.0 | DEFER |
| RapidJSON | MIT | 1.1.0 (2016!) | **REJECT** (frozen; nlohmann present) |
| simdjson | Apache | 4.0 | DEFER |

## ARCHIVES

| name | license | latest | class |
|---|---|---|---|
| zstd | BSD | 1.5.7 | **USE** (future APKs/alignment) |
| lz4 | BSD | 1.10.0 | USE (ART/odex) |
| bzip2 | BSD | 1.0.8 (2019) | DEFER |
| miniz | MIT | — | REJECT (zlib exists) |
| libarchive | BSD | 3.8.x | DEFER |
| **libdeflate** | MIT | 1.24 (2025-05) | **USE — highest value/size** (fast APK inflate, ~0.1MB) |

## APK/DEX TOOLING — all **ORACLE-ONLY** (never linked)
AAPT2 (AOSP binary) · apktool 2.10.x/v3.x (Apache) · baksmali/smali (dexlib2 3.0.x — Google) · JADX 1.5.6 (2026) · Androguard (Python) · bundletool 1.18.3 · APKEditor V1.4.8 (license UNVERIFIED) · enjarify (archived 2022 — REJECT)
+ **dexlib2 = a battle-tested reference model of the DEX format for cross-checking our own parser** (AppManager experience).

## JNI/NATIVE

| name | license | latest | class |
|---|---|---|---|
| libffi | MIT | 3.4.6→3.8.0 (2026-08) | **USE** (when real JNI starts) |
| Capstone | BSD-3 | 5.0.x/6.0-alpha | DEFER (safe disassembler) |
| Unicorn | GPL | 2.1.4 | **ORACLE-ONLY** (GPL; never in-process) |
| LIEF | Apache-2.0 | 0.17.1 (2025-10) | DEFER (ELF) |
| libdwarf | LGPL | 0.10–0.12 | DEFER |

## TEXT (this campaign's POC — WS-C2)

| name | license | sandbox | class |
|---|---|---|---|
| FreeType | FTL/GPL | 2.13.3 (upstream: 2.14.1 available) | **USE** (bump suggested) |
| HarfBuzz | Old-MIT | 10.2.0 (upstream: 14.4.0) | **USE** |
| FriBidi | LGPL | 1.0.16 | **USE** |
| SheenBidi | Apache-2.0 | 2.9.0/3.0.0 (2026-01) | USE (a permissive FriBidi replacement in the future) |

## WEBVIEW — Chromium embed (~150MB+) REJECT/DEFER · Servo (MPL, Rust) DEFER · **WPE WebKit** DEFER (the most practical headless CPU-only path)

---

## NOTABLE FINDINGS (summary)

1. Robolectric itself bundles a real native SQLite → a direct precedent for SQLite amalgamation.
2. **libdeflate**: the most value per kilobyte (fast APK inflate).
3. **ThorVG v1.0** a potential MIT/C-API successor for rlottie — DEFER for now.
4. Do not take fdk-aac (conditional license) — FFmpeg AAC is enough.
5. Unicorn only as an out-of-process ORACLE (GPL).
6. Do not take RapidJSON (2016) or LevelDB (limited maintenance).
7. No Zink on CPU — llvmpipe also rejected because of LLVM.
8. Skia: no stable C API → REFERENCE only for the Canvas semantics repertoire.
9. **Top ten candidates:** SQLite, libdeflate, miniaudio, FFmpeg-trim, libcurl+TLS, Wuffs, libffi, SheenBidi, zstd+lz4, ThorVG.
10. ANGLE+SwiftShader is the only valid GLES path — deferred until a GLES workstream is built.

## Answers to specific questions

- **A) stb_image:** v2.30, Public domain. Only better than the libpng/libjpeg pair for single-file decode-only and long-tail formats; it loses on SIMD speed, robustness, and PNG-write.
- **B) Robolectric native SQLite:** yes — `SQLiteMode.NATIVE` with `libnativeruntime.so` containing a real AOSP-derived libsqlite + ICU; exactly the pattern "real library as a resource → dlopen" for MiniAndroid.
- **C) Clean C API:** the majority (~40) have a C API; the dangerous C++-ABI ones: Skia, LevelDB, RocksDB, protobuf/FlatBuffers/simdjson/RapidJSON, the LIEF C++ layer → isolation needed.
