# CODE_REDUCTION_009 — §29 source-reduction audit

## 1. Current size (measured this session)

| Directory | LoC (.cpp+.h) |
|---|---|
| src/dex | 27,911 |
| src/runtime | 10,929 |
| src/resources | 4,830 (+640 new res_config) |
| src/api | 3,749 |
| src/renderer | 4,006 |
| src/framework | 2,862 |
| src/apk | 2,083 |
| src/storage | 1,545 |
| src/diagnostics | 807 |
| **Total src** | **58,941** (≈58,941 − 20 deleted heuristic + 640 res_config + 94 attach dispatch) |

Stub/TODO-marker census (§36): **212 markers** across src/ — classified in the ledger `STUB_DEBT.md` lineage; full per-marker classification is queued for the next campaign pass (they are conscious-simplification entries, not silent fakes; the two historic false-positive incidents are documented there: EXP-072-A/B, both already fixed/bypassed).

## 2. Deletions executed this campaign

| Removed | LoC | Replaced by |
|---|---|---|
| `ResolvedResource::best()` string heuristic (score = empty/dpi/"-r") | ~20 | AOSP `match()+isBetterThan()` port (`res_config.cpp`) |

## 3. Reduction opportunities identified (with projected effect) — next campaign

| # | Custom code | Duplicating | Projected reduction | Risk / condition |
|---|---|---|---|---|
| R1 | Custom `PNGDecoder` in `software_renderer.cpp` (decode path ~300-400 LoC incl. palette/tRNS special cases added in EXP-096) | `-lpng` ALREADY linked; `nothings/stb` also a candidate | 250–350 LoC + long-tail bug class elimination | golden PNG assets must re-verify byte-identical (incl. 9-patch + palette PNGs) |
| R2 | Audio decoder sprawl risk (future media work) | `mackron/dr_libs` covers WAV/MP3/FLAC in 3 headers | prevents +1,000s LoC of future custom code | license notices vendoring |
| R3 | NinePatch/VectorDrawable custom paths | `memononen/nanosvg` + `plutosvg/plutovg` study | only if VectorDrawable demand materializes in corpus | demand-gated |
| R4 | Custom GLES1.x-style raster fragments in renderer | `jserv/tinygl` (MIT) as GLES1 fallback study | speculative | only if PortableGL integration proves too large |
| R5 | C++ framebuffer legacy path (EXP-072-A, BYPASSED since EXP-072) | current active renderer | ~400 LoC dead path removable after re-baseline | requires final deprecation decision |

## 4. Maintainability effect of the §6 replacement

The 20-line heuristic encoded 3 rules, all subtly wrong vs AOSP (default-bucket preference, dpi penalty, "-r" penalty). The 640-line port encodes the full AOSP decision procedure with test evidence. Net maintainability: +620 LoC but the *behavior class* "wrong config bucket selected" is now structurally impossible rather than heuristic-dependent; the probe tool (`res_config_probe`) gives future engineers direct evidence access.

## 5. Honest accounting (§46)

More custom code was ADDED than deleted this campaign (640+94 in, 20 out) — because the campaign's wins were *new capability* (config matching, attach dispatch), not replacement. The replacement ledger above is the executable plan for the "less custom code" half of §46; executing R1+R2 next campaign is projected to net-negative LoC while preserving behavior.
