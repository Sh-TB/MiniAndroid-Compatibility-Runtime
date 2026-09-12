# GOLDEN-03 — RESOURCE COMPATIBILITY INFRASTRUCTURE + RESOURCE→PIXEL

Campaign: MASTER VISUAL COMPATIBILITY · Date: 2026-09-06
Fixture: `EXT-01-HELLOWORLDSELFAWARE-1.1.0` (frozen, SHA-256
`009b4671…cc41` — re-verified this session; no substitution).
Head: `6c352981` (see commit map below).

## A. What was implemented (generic; zero fixture-specific code)

1. **Canonical ResId model (§3)** — `res_id.h`: the single 0xPPTTEEEE
   decomposition/composition; 6+ duplicated bit-manipulation sites folded
   onto it (`finish_index`, `resolve`, `find_id`).
2. **Canonical resolution API (§4)** — `resolve_full(resourceId,
   deviceConfig, maxDepth) → ResolutionResult`: package/type/entry names,
   requested + selected configuration per chain step, raw vs resolved value
   distinction, `to_json()` evidence. `resolve_value`/`resolve_string` are
   projections of this path.
3. **Configuration engine (§5)** — the G31 law (`ResTableConfig.size` gate,
   version tie-break, `match`/`isBetterThan`) preserved and expanded into a
   48-check generic matrix: locale (match/rejection/refinement/no-country),
   density closest-bucket family, orientation, sw/w dp, uiMode, exact
   screen. All through `best_for()` — no fixture logic.
4. **Reference resolution (§6)** — bounded depth (16), cycle detection,
   named deterministic failures: `INVALID_ID`, `MISSING_ENTRY`,
   `MISSING_REFERENCE_TARGET`, `CYCLE`, `DEPTH_EXCEEDED`,
   `NOT_RESOLVABLE`.
5. **TypedValue semantics (§7)** — `res_id.{h,cpp}` as the ONE law source:
   complexToFloat, applyDimension (PX/DIP/SP/PT/IN/MM), pixel-size rounding
   + nonzero-floor, complexToFraction, color decode. FRACTION (0x06) now
   decoded (was declared, never handled). Manifest AXML dispatch aligned to
   AOSP Res_value constants.
6. **Bags/styles/attributes/themes (§8)** — `bag_value(style, attrKey,
   device)` with `ResTable_map_entry` parent inheritance (cycle-safe,
   hop-bounded); key-aware `apply_style` (textSize 0x01010095, textColor
   0x01010098 — byte-verified); style values now actually reach the node;
   `textAppearance` generic (app bags via bag_value, framework via
   byte-verified table); windowBackground chain rewritten on the canonical
   path.
7. **Dimension/density (§9)** — every consumer routed through the canonical
   `DensityContext` law (inflater dimens/styles/appearance, engine
   setTextSize with corrected AOSP unit constants PX=0/DIP=1/SP=2).
   22sp → 58px preserved (G46 law now *derived*, not hardcoded).
8. **String resources (§10)** — ARSC is the ONLY value source: the
   `resource_values.json` sidecar override is REMOVED from the production
   path (both loaders); integers/raw seeded ARSC-first; drawable paths
   resolved ARSC-first via the value-IS-path law; the sidecar's
   wrong-byte dimension decode retired with it.
9. **resource_trace (§12)** — `build/resource_trace <apk> <id|type/name>
   [--theme] [--bag key] [--json] [--density/--locale/--sdk]`: id →
   candidates → selected configs → raw value → reference chain → final
   value → apk path. Uses ONLY the canonical resolver.
10. **Resource matrix (§13)** — `docs/compatibility/RESOURCE_MATRIX.md`:
    parsed/resolved/consumed/rendered/pixel-verified per type × dimension.
11. **Hostile safety (§14)** — parser hardening (entryCount offsets bound,
    entries_start range, entry-esize underflow) + 18-check hostile suite:
    named, deterministic, crash-free, hang-free.

## B. Commits (logical boundaries)

| Commit | Boundary |
|---|---|
| `3c87e279` | §3/§4/§6/§7/§8/§9 resource resolver core (ResId, resolve_full, TypedValue laws, bag_value) + 42-check law test |
| `724e5a0b` | §5 configuration-engine matrix 19 → 48 |
| `86f47365` | §7/§10 sidecar removal + AOSP manifest type constants + ARSC-first seeding |
| `bf3056c1` | §8/§9 key-aware style bags + ONE TypedValue dimension path |
| `d306f1e2` | §12/§13 resource_trace + matrix doc |
| `40eaca85` | §14 hostile safety + parser hardening; battery 23 → 27 |
| `6c352981` | §15/§16 cwd-independent font law + external visual proof |

## C. Test evidence (all synthetic unless noted; battery stage counts)

| Suite | Checks | Law |
|---|---|---|
| resource_core_law_test | 42/42 | ResId; TypedValue laws; chain structure; named failures; bag inheritance; FRACTION |
| resource_config_selection_test | 48/48 | full match/isBetterThan matrix |
| resource_hostile_test | 18/18 | §14 safety contract |
| encoded_value_law_test | 18/18 | P2 carry-over |
| mutf8 | 14/14 | string pool |
| semantic | 96/96 (14+25+57) | interpreter |
| helloworld_golden | 26/26 | resource-backed boot/render |
| tictactoe_golden | 8/8 | interaction |
| corpus | 3/3 | real external APKs |
| **battery** | **27 stages ALL PASS** | zero-skip gate |

## D. Runtime-proven resource→pixel (frozen EXT-01, hash re-verified)

- **Chain A — theme/background**: manifest `android:theme` 0x7f060000 →
  style/AppTheme bag → `windowBackground` 0x01010054 → REFERENCE 0x7f010001
  → `color/colorPrimary` RGB8 #000000 → **5 static framebuffer regions
  EXACTLY rgb(0,0,0)** (no tolerance needed — the law is exact).
- **Chain B — text resource**: `@string/hello_message`
  (`hello world\ni'm %1$s\na version %2$s android\nwith api level %3$d`)
  → ARSC → `getString(id, 3 args)` ARSC-first (log `[EXT01-CTXGETSTR]`
  resid=0x7f050002 fargs=3) → TextView → **ink 25,988 px**, bbox
  [216,732,865,1195], centered.
- **Chain C — dimension/style**: `textAppearance` 0x01030042 (framework,
  byte-verified) → TextAppearance.Large 22sp → scaledDensity 2.625 →
  **tallest line band EXACTLY 58px** (heights [45,45,45,58]); log
  `[G46-TEXTAPPEARANCE] TextAppearance textSize=58px`.
- Whole-screen typography vs the trusted reference: **9/9 static checks**
  (block height Δ 0.64%, spacing Δ 1.58%, advance Δ 3.03%).

## E. Determinism (§16)

3 independent runs → **byte-identical** screenshot SHA-256
`142238fd92b69e11d3407526de95cad29bf46e3f4191767d09a24379fbe0bbf2`
(= the frozen G48 golden). The evidence harness EXPOSED and FIXED a real
determinism violation: monospace font resolution was cwd-relative; now
exe-relative (FIND-REUSE-RES-006). Dynamic device values (ANDROID_ID,
versions) are same-length by design and never compared — static geometry
fully checked (recorded in the comparators).

## F. No-fixture-specific-implementation audit (§19)

- No EXT-01 branch: `rg -n "7f060000|appliberated|hello_message|colorPrimary" src/`
  → zero hits in runtime sources (all fixture knowledge enters through the
  ARSC/AXML bytes at runtime).
- Hardcoded framework ids are platform constants, each byte-verified from
  real APKs and cited (FIND-REUSE-RES-007).
- No screenshot playback, no synthetic resource database, no ARSC bypass
  (the only bypass was REMOVED this gate), no direct renderer injection.

## G. Tooling (§17 — justified, minimal)

- `resource_trace` (new, reusable): replaces repeated manual ARSC/AXML
  reverse-engineering; enables the matrix's "resolved" column; future
  gates reuse it for any APK.
- `dump_ext01_attr_ids.py` (oracle): byte-verifies framework attr ids.
- `golden03_evidence.sh` + `golden03_chains.py`: one-command evidence
  regeneration from any HEAD.
- NOT built (would be unjustified now): arsc_dump (to_json covers it),
  config_matrix CLI (the synthetic test suite covers it), resource_diff.

## H. Residual / researched-not-implemented (honest ledger)

- Parent-theme resolution for FRAMEWORK themes (0x0103xxxx) is not
  implemented (bag_value walks only in-table parents; the framework side
  is the byte-verified TextAppearance table). Documented residual; EXT-01
  carries its own windowBackground so Chain A is unaffected.
- Plurals (`getQuantityString`) remain unsupported (pre-existing, unchanged).
- `RES_TABLE_TYPE_SPEC` flags parsed but not consumed (unchanged).
- Density in `match()` intentionally does NOT reject (AOSP closest-bucket
  law — FIND-RES-003 family); recorded because it surprised even the test
  author.
- All FIND-REUSE-RES statuses are per file; none is promoted to "verified"
  from source review alone.

## Verdict

```
GOLDEN-03 RESOURCE COMPATIBILITY INFRASTRUCTURE: VERIFIED
(§22 checklist: canonical ids ✓ · generic config selection ✓ · traceable
selected config ✓ · TypedValue semantics ✓ · generic references ✓ · cycle
safety ✓ · generic bags/themes ✓ · dimension/density law ✓ · ARSC-first
strings ✓ · AXML canonical resolver ✓ · hostile inputs fail safely ✓ ·
trace tooling ✓ · external resource→view→pixel ✓ · 3-run determinism ✓ ·
full battery 27/27 ✓ · no fixture-specific code ✓ · reproducible from
HEAD ✓)
```
