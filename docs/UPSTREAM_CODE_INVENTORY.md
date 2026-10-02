# UPSTREAM CODE INVENTORY (issue #364)

Generated at HEAD `438f8e85` from verified facts: Makefile link flags,
`miniandroid/third_party/` contents, `canonical/reuse_registry.json`,
`docs/GRAPHICS_SOURCE_REGISTRY.md`. Classes: VENDORED (in-tree),
HOST-LINKED (system lib), AOSP-PORTED (in-repo adapted code with AOSP
law citations), ADAPTED (wrapper over vendored substrate), REGISTRY.
Citation is not reuse: every row records the runtime call path; rows
whose consumer is not yet measured say so explicitly (PortableGL,
audio).

| Component | Class | License | Runtime call path |
|---|---|---|---|
| QuickJS | VENDORED | MIT | webview_engine -> QuickJS eval; Breakout-71 real game loop proven (#353) |
| nlohmann/json | VENDORED | MIT | pkgstore records, pkgaudit output, file-IO provenance JSONL |
| PortableGL | VENDORED | MIT | COMPILED-BUT-ZERO-CALLER at audit time (LOAD-AUDIT census) — honest note: wired into build, not into a measured consumer |
| stb family (stb_image/stb_vorbis) + minimp3 | VENDORED-ADAPTED | Public Domain / CC0 | renderer/gif_decoder, audio paths |
| zlib/libpng/libjpeg/libwebp(+demux) | HOST-LINKED | zlib / libpng / IJG-BSD / BSD-3 | BitmapFactory decode* paths (decodeStream/decodeFile verified by probe 23/23) |
| SQLite | HOST-LINKED | Public Domain | SQLiteDatabase family; real WAL pragma + single databases_dir verified (probe: WAL/db persisted on store) |
| OpenSSL (libssl/libcrypto) | HOST-LINKED | Apache-2.0 | S100 Mini Browser real HTTPS GET + 307 redirect (E5, canonical GIFs) |
| FreeType / HarfBuzz / FriBidi | HOST-LINKED | FTL/GPL-2.0 dual / MIT / LGPL-2.1+ | TextView/paint text path; glyph consumption proven by text-bearing goldens |
| mpg123 / libsndfile | HOST-LINKED | LGPL-2.1 / LGPL-2.1 | audio_engine (compiled; consumer proof pending — ST frontier) |
| AOSP-derived semantic ports (in-repo code) | AOSP-PORTED | Apache-2.0 (AOSP) — attribution in source headers/docs | engine-wide; probe 23/23 + goldens x3 |
| GRAPHICS_SOURCE_REGISTRY candidates | REGISTRY | mixed (per entry) | reference + decision record; reuse_registry.json is the decision layer |

Machine rows: `docs/UPSTREAM_CODE_INVENTORY.jsonl` (11 rows).
