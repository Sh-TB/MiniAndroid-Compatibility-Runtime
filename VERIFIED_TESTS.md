# VERIFIED_TESTS — how to rebuild and rerun every protecting test (2026-09-02)

All results below were produced on `integration/master-reconciliation` with the
fixed engine (commit 6fda28d). Link pattern for fixtures: the fixture .cpp plus
every `build/**/*.o` except `main.o`.

## 0. Build

```bash
export MINIANDROID_APK_CACHE=/path/to/apk_cache      # external, zero-APK repo
cd miniandroid && make -j                            # → build/miniandroid
```

## 1. Canonical matrix + goldens

```bash
python3 miniandroid/scripts/u011_test_matrix.py
```

| app | expected exit | expected screenshot SHA | note |
|---|---|---|---|
| simplestopwatch | 0 | **2a12587a0acf196cb9a52a521d6a7bc7d72e2d21dfa71eba41a694dbaa3d8c1b** | BASELINE_MATCH — pixel-exact law |
| gmdice | 0 | 4fd3ce0e0c419119… (no pinned baseline in runner) | byte-stable across semantic fix |
| microtimer | 0 | eb16ab5c68fa9b6c… | byte-stable |
| unote | 0 | d6b854c45a16539f… | byte-stable |
| dooz | 0 | 31ddd4d5b8e6d18e… | deterministic BLANK (Compose blocker, expected) |
| telegram_v12 | — | — | BLOCKED: golden APK lost (K-26); runner exits 1 at 0.0s on bogus APK |
| stopwatch | 1 | — | known-corrupt APK (documented in TEST_MATRIX) |
| tictactoe | 1 | — | corpus/tictactoe.apk 0-byte (K-26 family); tictactoeemmanuelmess.apk restored separately |

## 2. Semantic fixtures (each must PASS; all discriminate the old bugs)

```bash
OBJS=$(ls build/apk/*.o build/dex/*.o build/runtime/*.o build/diagnostics/*.o \
         build/resources/*.o build/renderer/*.o build/framework/*.o \
         build/api/*.o build/storage/*.o | tr '\n' ' ')
LIBS="-lz -lwebp -lwebpdemux -ljpeg $RLOTTIE/build/src/librlottie.a -lstdc++ -lm -lpthread -lfreetype -lharfbuzz -lfribidi -lpng"
g++ -std=c++17 -O2 -Isrc -Ithird_party/nlohmann_json/include tests/<FIXTURE>.cpp \
    $OBJS $LIBS -o /tmp/fixture && /tmp/fixture
```

| fixture | result | protects |
|---|---|---|
| tests/semantic_long_cmp_conv_test.cpp | **14/14** (12/14 FAIL pre-fix — run/semantic_reconciliation/before_fix_FAIL.txt) | K-01..K-05: 64-bit long arith, cmp-long, NaN ordering, conversions, 12x nibbles |
| tests/unified0112_filled_new_array_test.cpp | 5/5 | K-07 FNA 35c nibbles |
| tests/unified0113_typed_catch_test.cpp | 8/8 | K-09 typed catch + propagation |
| tests/exp088_f5_return_wide_test.cpp | 5/5 | K-08 return-wide |
| tests/exp088_phasef_handler_queue_semantics.cpp | 23/23 | K-10 FIFO ordering |
| tests/simple_test.cpp | 4/4 | view hierarchy basics |

## 3. Resource / rendering

```bash
# ARSC resolution probe on a real APK (RESULT_016 / K-16):
g++ -std=c++17 -O2 -Isrc -Ithird_party/nlohmann_json/include tests/c013_arsc_probe.cpp \
    <same $OBJS> $LIBS -o /tmp/probe && /tmp/probe $MINIANDROID_APK_CACHE/corpus/simplestopwatch.apk
# expected: "arsc valid", "layouts with file: 3/3"
```

## 4. Determinism rule

Run any golden twice more; screenshot SHA must repeat exactly (campaign rule ×3).
2026-09-02: simplestopwatch/gmdice/microtimer/unote/dooz repeated identical
pre/post semantic fix — see FINAL_STATE.md metric table.
