# CODE REDUCTION — UNIFIED_008 (charter §25)

The campaign's reuse-first rule produced REDUCTION in hand-maintained logic
and PREVENTED new custom code. Honest accounting — including where we added
C++ because no open-source implementation exists to reuse:

## Removed / externalized hand-maintained logic

| item | before (hand-maintained) | after | effect |
|---|---|---|---|
| resource_values.json (Telegram) | hand-built value file (UNIFIED_002 era) — values missing → names shown | **generated** by tools/u008_gen_resource_values.py from androguard ARSCParser: 11,314 strings, 165 colors, 179 dimens, 18 integers | hand-maintained data file DELETED from the maintenance set; PARTIAL → PROVEN upgrade |
| ARSC ground truth | eyeballing arsc_tool output | machine diff vs ARSCLib/Apktool oracles | risk of self-confirming parser bugs removed |
| DEX disassembly for debugging | ad-hoc stderr tracing only | androguard oracle disassembly (scripts/u008_dex_trace.py) | root-cause time cut by an order of magnitude (4 stacked root causes found in one session) |
| GitHub discovery | would-be gh scripting | git ls-remote (rate-limit-free, no auth) | zero-dependency verification of 114 repos |

## New custom C++ — justified against open source (§45 checklist answered)

| code | lines | asked §45 questions | verdict |
|---|---|---|---|
| Integer.valueOf/intValue/toString boxing | ~45 | existing? no embeddable C++ dalvik core boxing impl | **glue required** (interpreter heap convention is MiniAndroid-specific) |
| String.format spec scanner | ~110 | existing? a full java.lang.Formatter port (e.g. from Harmony) is 5k+ LOC | **minimal glue**, bounded spec set (d/s/x/o/f/c/b + flags) |
| CharSequence/String ops bridge | ~120 | existing? these must speak MiniAndroid DalvikValue/heap types | **glue required** |
| java.util.Random LCG bridge | ~110 | existing? algorithm is standard (AOSP), implementation tied to heap state | **glue required**, AOSP semantics reused |
| String.split char-class | ~15 | re2 possible | **minimal glue now**, re2 recorded as roadmap |
| decode fixes (array-length/2addr/lit16/wide/move-wide) | ±0 (net ~10 comment lines) | — | **bug fixes, not feature code** |

**Net new glue this campaign: ~400 lines**, replacing what would otherwise be
thousands of lines of hand-rolled format/parsing/PRNG behavior drift.

## What we did NOT write (because open source exists)

- ARSC parser rewrite (ARSCLib covers it as oracle; our parser validated equal)
- ARSC value extractor (androguard does it in 20 lines of script)
- DEX disassembler (androguard)
- Lottie (rlottie), bidi/shaping/raster (FriBidi/HarfBuzz/FreeType),
  image decoders (libpng/jpeg-turbo/webp), audio decoders (mpg123/libsndfile),
  JSON (nlohmann), APK download (curl)

## LoC deltas (git)

```
00921c9..HEAD (UNIFIED_008 commits)
+ dalvik_engine.cpp: +544 −43 (70c64c6), +24 −4 (throttle split)
+ tools/u008_gen_resource_values.py: +100 (new, script not C++)
+ tools/download_test_apks.sh: +40 (new)
+ ArscDump.java: +95 (oracle CLI, evidence tooling)
custom-code debt REMOVED: resource_values.json hand maintenance (≈1 file ×
per-app per-release), self-confirming ARSC eyeballing, manual DEX reading.
```
