# FIND-REUSE-RES — AOSP resource-subsystem laws transferred to MiniAndroid

Campaign: GOLDEN-03 RESOURCE COMPATIBILITY INFRASTRUCTURE (2026-09-06).
Status discipline: `researched → implemented → tested → observed →
runtime-proven → verified`. Source review alone is NEVER "verified".

Common oracle: aosp-mirror/platform_frameworks_base @ 1cdfff555f4a —
`libs/androidfw/ResourceTypes.cpp`, `AssetManager2.cpp`,
`core/java/android/util/TypedValue.java`.

---

## FIND-REUSE-RES-001 — A lookup returns the value WITH its selected configuration

- **Android law**: `AssetManager2::FindEntry` selects an entry under the
  requested `ResTable_config` and returns the entry together with the
  config it was selected under; `resolveReference` is a separate step.
- **MiniAndroid before**: `resolve()` returned entries; no API surfaced the
  *selected* configuration or the reference chain; consumers re-derived
  `(id>>24)&0xFF` inline at 6+ sites.
- **Transfer**: `res_id.h ResId` (single 0xPPTTEEEE decomposition) +
  `ArscParser::resolve_full(id, device, maxDepth) → ResolutionResult`
  (per-step package/type/entry/selected-config/raw-value) +
  `ResolutionResult::to_json()` evidence.
- **Status**: implemented, tested (`resource_core_law_test` 42/42),
  runtime-proven (`resource_trace` on frozen EXT-01).

## FIND-REUSE-RES-002 — Reference resolution must be bounded and cycle-safe

- **Android law**: `ResTable::resolveReference` walks REFERENCE values
  entry-by-entry; Android tables are trusted, so AOSP has no depth cap.
  Hostile tables (cycles, 1000-hop chains) must fail deterministically in
  a compatibility runtime.
- **MiniAndroid before**: 4-hop inline loop, no cycle detection, silent
  stop on broken chains.
- **Transfer**: bounded depth (16) + visited-set cycle detection + NAMED
  deterministic errors: `INVALID_ID`, `MISSING_ENTRY`,
  `MISSING_REFERENCE_TARGET`, `CYCLE`, `DEPTH_EXCEEDED`, `NOT_RESOLVABLE`.
- **Status**: implemented, tested (cycle/self-cycle/30-hop cases),
  runtime-proven (hostile tables 18/18).

## FIND-REUSE-RES-003 — TypedValue laws are ONE conversion source

- **Android law**: `TypedValue.complexToFloat` (mantissa × radix
  multipliers, mantissa at bits 8-31), `applyDimension` (PX/DIP/SP/PT/IN/MM
  with `xdpi`), `complexToDimensionPixelSize` (round-toward-zero + nonzero-
  floor tail), `complexToFraction` (base/pbase), color types → 0xAARRGGBB.
- **MiniAndroid before**: `complexToFloat` lived in arsc_parser.cpp; every
  consumer re-implemented unit switches; PT/IN/MM were silently treated as
  px; FRACTION (0x06) was declared but never decoded; the manifest reader
  used non-AOSP type constants (STRING=1, REFERENCE=6, INT=18,
  INT_BOOLEAN=21); the Telegram sidecar decoded dimension units from the
  WRONG byte (`(raw>>24)&0xFF` instead of the low nibble).
- **Transfer**: `res_id.{h,cpp}` as the single law source; all consumers
  (ARSC parser, AXML parser, inflater, engine setTextSize) route through it.
- **Status**: implemented, tested (42/42 incl. 22sp→58px),
  runtime-proven (EXT-01 tallest line band = 58 px exactly).

## FIND-REUSE-RES-004 — Style bags are attribute-KEY maps with parent inheritance

- **Android law**: a style/theme entry is a `ResTable_map` bag keyed by
  attribute resource id; lookup by key walks the `ResTable_map_entry.parent`
  chain (style inheritance).
- **MiniAndroid before**: the inflater iterated bag items POSITIONALLY
  (any dimension → textSize, any color → textColor); only windowBackground
  was queried by key (hand-rolled scan).
- **Transfer**: `ArscParser::bag_value(style, attrKey, device,
  maxParentHops)` (cycle-safe) + key-aware `apply_style` +
  generic `textAppearance` resolution (app styles via bag_value; framework
  styles via a byte-verified table — TextAppearance.Large 0x01030042 = 22sp).
- **Status**: implemented, tested, runtime-proven (EXT-01 AppTheme →
  windowBackground chain; Chain C pixel metrics).

## FIND-REUSE-RES-005 — ARSC is the ONLY resource value source

- **Android law**: an APK's resources.arsc is authoritative; nothing
  outside the APK can override a resolved value.
- **MiniAndroid before**: `resource_values.json` sidecars (Telegram-era)
  were loaded AFTER the ARSC pass and OVERRODE real values; a hostile JSON
  next to the APK could steer the runtime.
- **Transfer**: sidecar loaders REMOVED from the production path
  (execution_engine + application_runtime); integers/raw/drawable paths
  seeded ARSC-first (`apk_path_for` value-IS-path law, config-selected).
- **Status**: implemented, tested (battery 27/27 after removal),
  runtime-proven (EXT-01/corpus unchanged outputs).

## FIND-REUSE-RES-006 — Font assets resolve against the system image, not the cwd

- **Android law**: framework fonts live in the system image
  (`/system/fonts`); rendering cannot depend on the invoking shell's
  working directory.
- **MiniAndroid before**: `DroidSansMono.ttf` (fonts.xml monospace law)
  resolved via cwd-relative candidates only — a run from another directory
  silently substituted the default sans face and changed pixels.
- **Transfer**: `/proc/self/exe`-relative candidates first (env override
  `MINIANDROID_FONT_DIR` still wins; cwd candidates kept as legacy
  fallback).
- **Status**: implemented, tested (battery 27/27), runtime-proven (3-run
  byte-identity `142238fd…bbf2` from two different cwds).

## FIND-REUSE-RES-007 — Framework attribute/style ids must be byte-verified

- **Android law**: framework attr ids (0x01xxxxxx) are platform constants.
- **Discipline**: no id enters the code from memory; each is read from real
  APK bytes (`scripts/dump_ext01_attr_ids.py`): textSize 0x01010095
  (helloworld fixture map), textColor 0x01010098 (EXT-01 ∩ fixture agree),
  textAppearance 0x01010034, fontFamily 0x010103ac,
  lineSpacingMultiplier 0x01010218, elegantTextHeight 0x0101045d,
  windowBackground 0x01010054 (AppTheme bag), theme 0x01010000.
- **Status**: observed (byte-verified oracle committed), used by runtime.

## FIND-REUSE-RES-008 — Hostile tables fail named, deterministic, crash-free

- **Android law (boundary hardening, WineDroid/DexFile philosophy)**: data-
  driven scans must be pre-bounded before dereferencing; failures carry a
  name; identical hostile input → identical failure.
- **MiniAndroid before**: `parse_type_chunk` read `offs[i]` for a hostile
  `entryCount` past the chunk (OOB read); hostile entry `esize` could
  underflow the availability bound.
- **Transfer**: entryCount×4 + entries_start bounds; vp+8 bound; hostile
  suite (truncation, bad offsets/counts, malformed values, parent cycles,
  impossible configs) — 18/18 with a 5s wall-clock guard per case.
- **Status**: implemented, tested, runtime-proven.
