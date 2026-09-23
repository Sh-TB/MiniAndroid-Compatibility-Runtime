# WS-C4 PRIMARY TRANSFER

**To:** Primary Coder · **From:** WS-C4 · **Date:** 2026-08-27

## ADOPTION DECISIONS (with SOURCE/EVIDENCE/CONFIDENCE/BENEFIT/RISK/ACTION)

### D1 — SQLite amalgamation → DatabaseBackend (highest priority)
- SOURCE: sqlite.org 3.50.x, Public domain · EVIDENCE: previous Coder4 proof (11/11+) + Robolectric nativeruntime precedent
- CONFIDENCE HIGH · BENEFIT: a large part of the corpus (DB APKs) opens up · RISK: LOW (single C file)
- ACTION: adapter in `DatabaseBackend` + contract tests (open/query/transaction/rollback/persistence). **Do not rewrite SQLite internals.**

### D2 — libdeflate → the internal ZIP/APK inflate path
- SOURCE: github.com/ebiggers/libdeflate 1.24 MIT · CONFIDENCE HIGH
- BENEFIT: load speed on large APKs (Telegram 73–83MB) · RISK: LOW (zlib fallback)
- ACTION: before/after benchmark on the same v12 APK; keep zlib as fallback.

### D3 — miniaudio → AudioBackend (the deterministic decode→PCM stage)
- SOURCE: github.com/mackron/miniaudio 0.11.25 PD/MIT · CONFIDENCE HIGH · RISK: LOW
- ACTION: first decode→PCM buffer only (no device); §22 goal: deterministic virtual output.

### D4 — FFmpeg-trim → VideoBackend / supplementary audio
- SOURCE: ffmpeg.org 8.0 LGPL-2.1+ · CONFIDENCE HIGH · RISK: MED (binary size; license: dynamic-link LGPL is enough)
- ACTION: oracle first (compare against Coder4's previous H264/VP9/AV1/MJPEG evidence), then adapter.

### D5 — libcurl(+OpenSSL/mbedTLS) → NetworkBackend
- SOURCE: curl.se 8.14.0 · previous Coder4 proof: OkHttp 5/5, libcurl 6/6
- ACTION: shared network contract tests (HTTP/HTTPS/redirect/gzip/timeout) — §10 charter.

### D6 — FreeType+HarfBuzz+FriBidi (just proven now — WS-C2)
- Reference `WS-C2_PRIMARY_TRANSFER.md` T1. SheenBidi is the next permissive replacement.

## CODE REDUCTION LEDGER (§25 — code-reduction goals)
| Replacement | Existing code that is removed/shrunk |
|---|---|
| SQLite | the current/future hand-made db code (~thousands of avoided LOC) |
| libdeflate | hand-written inflate of hot sections (part of apk_parser) |
| miniaudio | — (nothing to remove; avoids writing a hand-rolled mixer/decode) |
| ThorVG (DEFER) | none — until rlottie needs replacing |

## REJECTED (PRIMARY must also know — §21)
NanoVG (dead), Cairo/Pango (heavy dependency/low value), LevelDB/RocksDB/DuckDB (maintenance/size), Oboe/PortAudio (platform-bound/dormant), fdk-aac (license), Media3/OkHttp/Cronet (JVM/Chromium), Unicorn in-process (GPL), RapidJSON (frozen 2016), llvmpipe (LLVM), Zink (overhead), enjarify (archived)。

## VERIFY AT ADOPTION TIME (UNVERIFIED in the research)
apktool v3.x status · APKEditor license · mbedTLS 4.x rollout.
