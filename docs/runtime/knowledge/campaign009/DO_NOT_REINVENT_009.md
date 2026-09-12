# DO_NOT_REINVENT_009 — standing orders derived from evidence

Purpose per §46: *"make MiniAndroid capable of more Android behavior while writing less custom code."* Each row: the custom-code temptation → the open-source answer → status.

| # | Temptation (custom subsystem) | Do NOT reinvent — use | Status |
|---|---|---|---|
| 1 | ARSC config bucket matching heuristics | AOSP `ResTable_config::match/isBetterThan` semantics (ported, now in `res_config.cpp`) — never replace with string heuristics again | DONE 009 |
| 2 | Another image decoder | `nothings/stb` (stb_image, MIT) — single header covers PNG/JPEG/BMP/GIF; runtime ALREADY links libpng+libjpeg+libwebp: the custom `PNGDecoder` inside `software_renderer.cpp` is duplication | PLAN (CODE_REDUCTION_009 §3) |
| 3 | More audio decoders | `mackron/dr_libs` (dr_wav/dr_mp3/dr_flac, Unlicense) + `lieff/minimp3` (CC0) — one header per format; do not add per-format custom parsers | PLAN |
| 4 | A second software rasterizer | `rswinkle/PortableGL` (MIT, proven this campaign: GLES2 shader triangle 31,104 px) for GLES2; keep custom raster only for the View-bridge | DECISION RECORDED |
| 5 | Compose runtime re-implementation | Compose classes are INSIDE the APK DEX — interpret them; bridge only the framework surface they reach (attach lifecycle, Canvas ops, Choreographer tick). Never write a "mini-Compose" in C++ | GOVERNING RULE (§10 evidence) |
| 6 | Bidi/shaping stack | FriBidi+HarfBuzz already integrated; `Tehreer/SheenBidi` (Apache-2.0) is the consolidation candidate — study before any custom bidi fix | STUDY |
| 7 | DEX opcode tables by memory | `androguard` + `JesusFreke/smali` + AOSP `platform_dalvik` source = verifiable opcode oracles | STANDING |
| 8 | View semantics guesses | Robolectric (proven EXP-102) + AOSP View.java — behavior oracle, not blind copy | STANDING |
| 9 | Lottie | rlottie already vendored + wired (EXP-097/098); `thorvg` (MIT) is the monitored alternative — do not fork custom Lottie paths | STANDING |
| 10 | SQLite wrappers | `sqlite/sqlite` public-domain amalgamation — no custom DB format code | STANDING |

## Anti-patterns observed this campaign (never again)

1. **String-heuristic config matching** (the pre-009 `best()`) — it preferred the DEFAULT bucket over a matching 480dpi bucket, the opposite of AOSP. Caught and replaced.
2. **Field layouts from memory** — first `res_config.cpp` draft had an off-by-4 after `inputFlags`; caught by re-reading the fetched AOSP header before merging (law #0 vindicated).
3. **Swallowing lifecycle callbacks in shadows** — `ViewShadow` `handled_void` on `onAttachedToWindow` silently killed the entire Compose chain. Lifecycle dispatch must reach DEX-side overrides (superclass walk included).
