# RESOURCE MATRIX — parsed → resolved → consumed → rendered → pixel-verified

GOLDEN-03 §13 — reusable matrix/test inventory for the resource subsystem.

**Law:** a resource type is only counted as compatibility-proven at the
deepest stage it has *runtime evidence* for. "Parser passed" is NOT
"compatibility passed": a table can parse and still resolve to the wrong
configuration, or resolve correctly and never reach a visible pixel.

## Stage definitions

| Stage | Meaning | Evidence source |
|---|---|---|
| parsed | bytes decoded without error, structure indexed | `ArscParser::parse()` valid + stats |
| resolved | `resolve_full(id, device)` returns ok with the expected chain/selected config | `build/resource_trace <apk> <id>` (§12 tool) |
| consumed | a framework consumer actually used the value (TextView text, theme background, dimen conversion, engine intercept) | runtime trace channels (`[ARSC-VALUES]`, `[G46-TEXTAPPEARANCE]`, `[EXT01-CTXGETSTR]`, inflate stats) |
| rendered | the value influenced the framebuffer | screenshot produced with the value applied |
| pixel-verified | quantitative pixel comparison proved the visible effect (Rule 10: region/bbox deltas, never one whole-image number) | comparator JSON (`typography_golden.json`, `interaction_golden.json`) |

## Type × dimension coverage (per frozen EXT-01 HelloWorldSelfAware v1.1.0)

`R` = runtime-proven at this HEAD · tool: `build/resource_trace` for the
resolved column. Extending to a new APK = add a row set, run the tool, add
comparator evidence. NO fixture-specific code path exists for any row.

| Type (EXT-01 entry) | Requested vs selected config | parsed | resolved | consumed by | rendered | pixel-verified |
|---|---|---|---|---|---|---|
| `string/hello_message` (formatted `%1$s %2$s %3$d`) | default | ✓ | ✓ (0 hops) | Context.getString(id, args) → TextView | ✓ | ✓ GOLDEN-01 9/9 (text block geometry) |
| `color/colorPrimary` (RGB8 #000000) | default | ✓ | ✓ | manifest theme → windowBackground → window surface | ✓ | ✓ GOLDEN-01 (background check 1) |
| `style/AppTheme` (bag, v9/v16/v21 variants) | device34 → **v16** bucket | ✓ | ✓ (bag_value key 0x01010054) | PhoneWindow law → DecorView background | ✓ | ✓ GOLDEN-01 (background identical) |
| `id/hello_world_text_View` | default | ✓ | ✓ | findViewById | ✓ | ✓ (text position) |
| `layout/activity_main` (obfuscated `res/UD.xml`) | device34 → **v16** variant | ✓ | ✓ value-IS-path | setContentView → inflate → measure | ✓ | ✓ GOLDEN-01 9/9 |
| `mipmap/BW` (adaptive icon XML) | default | ✓ | ✓ | (not consumed by the fixture's UI) | — | — (launcher-only) |
| framework attr `textSize` 0x01010095 | — | ✓ (AXML map) | ✓ | TextAppearance→22sp→**58px** (TypedValue law) | ✓ | ✓ GOLDEN-01 line-height law |
| framework attr `textColor` 0x01010098 | — | ✓ | ✓ | TextView → #FFFFFF ink | ✓ | ✓ GOLDEN-01 (ink present/centered) |
| framework attr `windowBackground` 0x01010054 | — | ✓ (AppTheme bag) | ✓ | window surface color | ✓ | ✓ GOLDEN-01 |
| `dimen`/`fraction`/`integer`/`bool`/`raw` types | synthetic tables | ✓ | ✓ (core law test 42/42) | engine intercepts (ARSC-first seeding) | corpus-dependent | corpus runs 3/3 |

## Generic regression inventory (all synthetic — reusable for ANY APK)

| Test binary | Checks | Law under test |
|---|---|---|
| `resource_config_selection_test` | 48 | match()/isBetterThan()/best_for(): version tie-break, size-gate, locale (refinement + rejection), density closest-bucket family (scale-down, bigger-wins, default≈mdpi), orientation, sw/w dp, uiMode, exact screen |
| `resource_core_law_test` | 42 | ResId model; TypedValue laws (complexToFloat, applyDimension PX/DIP/SP/PT/IN/MM, pixel-size rounding + nonzero floor, fraction); resolve_full chain structure + selected-config reporting; named failures (INVALID_ID / MISSING_ENTRY / MISSING_REFERENCE_TARGET / CYCLE / DEPTH_EXCEEDED); bag_value inheritance + parent cycles; FRACTION decode |
| `encoded_value_law_test` (P2 carry-over) | 18 | DEX encoded_value boundaries (FIND-REUSE-DEX) |
| `resource_hostile_test` (§14) | see file | truncated/oversized/invalid tables fail NAMED, deterministic, crash-free |

## Tooling

```
build/resource_trace <apk> <0xID | type/name> [--theme] [--bag <key>]
                     [--json out.json] [--density d] [--locale ll-CC] [--sdk n]
```

Example (Chain A of the frozen EXT-01):

```
$ build/resource_trace $APK style/AppTheme --theme
  manifest android:theme = 0x7f060000
  windowBackground item = REFERENCE 0x7f010001
  → tracing REFERENCE 0x7f010001
  ... entry 'colorPrimary' ... raw value: COLOR (type 0x1d) raw 0xff000000 → # ff000000
```
