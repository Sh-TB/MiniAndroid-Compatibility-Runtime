# S186 — Library Ecosystem (Wave 1 audit, 2026-11-06)

Source of truth: `library_ecosystem/registry.json` (+ capability_matrix.json,
dependency_graph.json, reports/WAVE1_AUDIT.json). Everything below was measured
against current HEAD with ldd/nm on `miniandroid/build/miniandroid`.

## What actually exists (6-level audit)

| family | level | evidence |
|---|---|---|
| SQLite | linked+called+proven | libsqlite3.so.0, 27 U sqlite3_* |
| zlib | linked+called+proven | libz.so.1 |
| libpng | linked+called+proven | libpng16.so.16, 30 U png_* |
| libjpeg | linked+called+proven | libjpeg.so.62, 8 U jpeg_* |
| libwebp | linked+called | libwebp.so.7, 3 U WebP*; demux gap |
| stb_image | vendored+compiled+proven | v2.30 |
| FreeType | linked+called+proven | libfreetype.so.6, 11 U FT_* |
| HarfBuzz | linked+called | libharfbuzz.so.0, 9 U hb_* |
| FriBidi | linked+called | libfribidi.so.0, 2 U |
| mpg123 | linked+called | libmpg123.so.0, 8 U |
| libsndfile | linked+called | libsndfile.so.1, 4 U sf_* |
| OpenSSL | linked+called | libssl.so.3, 11 U SSL_* |
| QuickJS | vendored+compiled+proven | 172 T JS_* symbols |
| PortableGL | vendored+compiled+proven | 212 T gl* symbols; A_RICH faces |
| rlottie | ABSENT | no source/link/consumer |
| SDL | ABSENT | B1 host rebuild pending |
| libGDX | host-native+proven | 64 T syms |
| Box2D | host-native+proven | 266 T syms, GATE-A byte-exact |
| libgdx-freetype | host-native build-verified | 68 T syms, no APK proof yet |

Discovered extras: nlohmann_json (vendored), minimp3+stb_vorbis (vendored audio —
PRUNE CANDIDATE overlapping mpg123/libsndfile after trace), 11 anchor_libs stubs
(libEGL/libGLESv2/libOpenSLES are stub anchors — B2/B7 real backends open).

## Real gaps found by the audit (not in old reports)
1. libwebpdemux NOT linked → animated WebP impossible today.
2. Audio: zero real-APK end-to-end proof (Rule 5) despite two decode paths linked.
3. conscrypt JNI gap → TLS titles fail at UnsatisfiedLink (taz evidence).
4. libEGL/libGLESv2 anchors are stubs → GLES families beyond PortableGL's reach
   (GLES3, FBO edge semantics) have no path yet.
5. Duplicate audio implementations present simultaneously — Rule 3 trace required
   before pruning either.

