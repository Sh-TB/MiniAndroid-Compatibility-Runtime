# SELF-VERIFICATION — UNIFIED_008_FINAL.zip (charter §43)

Verified from the archive ITSELF, in a clean directory, third-party style
(no repo state reused):

```
zip:    UNIFIED_008_FINAL.zip
sha256: 34f85362e56ee06410f74057be7d4f23051884420cf71355c9f56b1fca0d11c0
size:   7,593,681 bytes · 649 members · 0 *.apk / *.aab (policy §1)
```

## Steps executed

| # | step | command | result |
|---|---|---|---|
| 1 | extract | `unzip UNIFIED_008_FINAL.zip` | 649 files (miniandroid/ + evidence/ + README_ARCHIVE.txt) |
| 2 | clean build | `cd miniandroid && make -j4` | **Build complete**, 0 errors |
| 3 | download test APKs | `bash tools/download_test_apks.sh` | exit 0; cache at ~/.cache/miniandroid/apks (never inside archive); symlinks into download/corpus + download/exp038_telegram; **resource_values.json regenerated from the real Telegram ARSC via androguard oracle: 11,314 strings / 165 colors / 179 dimens / 18 integers** |
| 4 | golden journey | `./build/miniandroid run download/corpus/gmdice.apk --journey … --max-taps 3` | exit 0; button texts from real DEX (`3D20 / 1d20 / 1d6 / 1d6+4`); **state-change taps [2,3]** — roll "18 ·4 ·20" rendered, pixels changed |
| 5 | telegram | `./build/miniandroid run download/exp038_telegram/Telegram.apk --journey …` | exit 0; 5/5 stage captures; `getString(0xf10ff) → "Enter code"` rendered on SMS screen |
| 6 | audio suite | `./build/test_audio` | **47 PASS / 0 FAIL** |
| 7 | font proof | `./build/u007_font_proof` | proof.png written (FriBidi→HarfBuzz→FreeType→blit) |
| 8 | APK policy | zip member scan | 0 *.apk / *.aab members |
| 9 | evidence dir | — | golden journey step PNGs + journey.json, telegram 5 stage PNGs, ARSCLib/Apktool oracle dumps, opensource_catalog.json (119 entries / 114 commit-verified), corpus_results.json, font proof |

Dependencies a third party needs: g++ (C++17), make, python3+androguard (pip),
curl, java (only for the optional ARSCLib/Apktool oracles), system
libpng/libjpeg/libwebp/zlib/freetype/harfbuzz/fribidi/mpg123/libsndfile,
rlottie at ../tools/rlottie (built once per env; see docs).
