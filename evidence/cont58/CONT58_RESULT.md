# CONT-58 Result — F-NEW-336: the app-package file-backed ColorStateList law

Wave: the user's standing "کامل کامل" (complete-complete) directive — the
tanana calculator rendered its preference screen as a blank gray bar. The
S57-B addendum had pinpointed `text_size=0.0` on the rows as the suspected
root; this wave REFUTED that hypothesis at HEAD and root-caused the real
one, fixed it generically, and re-proved the full standing gate.

## Baseline frozen

- Binary rebuilt from the clean `bebb7cd4` tree: `c8b078ba88ca255d` —
  byte-identical to the recorded CONT-56b merged binary (no toolchain
  drift adjudication needed this time).
- Gate at the base binary: anchors 27/27 + csw 3/3 + simplecalc 3/3
  (36 runs) all byte-identical to records. dooz180 ×3 = `6841d52a20e6597e`.

## Decode chain (all live-proven, no speculation)

1. **Symptom**: row band y=126..346 uniformly `(225,225,225)`;
   `dark_glyph_samples=0`. The five preference TextViews carry real text
   (`Notification settings`, `Ongoing notification`,
   `Calculator Notification can not be dismissed`, `Lock screen
   notification`, `Show Calculator Notification on lock screen`) at real
   geometry (1080×44 @ y=126/170/214/258/302) — view-tree ground truth.
2. **S57-B hypothesis REFUTED**: `MINIANDROID_S109_BITMAP` —
   `draw 'Notification settings' glyphs=20 avail=1 size=36.75` — the
   14sp-fallback textSize chain works (`14.0f × 2.625 density = 36.75`);
   20 real glyphs shaped; `TextShaper::draw` called every pass.
3. **Smoking gun**: the same trace with the color extension —
   `color=(0,0,97,0)`. The resolved text color was **alpha-0**: every
   glyph pixel `src_over`-blended away by `FrameBuffer::set_pixel`.
4. **Where the garbage color comes from**: `MINIANDROID_THEME_DIAG` —
   `attr=0x1010036 (textColorPrimary) -> BASE type=3 data=0x61` — a
   **STRING** typed value whose data is the string-pool INDEX 97. The
   S127 file branch fired but `find_id color/abc_primary_text_material_light
   -> MISS` (it only consults the framework router; appcompat library
   colors are APP-package entries). `MINIANDROID_THEME_ATTR_DIAG` —
   `str='res/color/abc_primary_text_material_light.xml'` — the file IS
   inside the app APK (464-byte binary AXML `<selector>`).
5. **Consumer law gap**: the engine's textColorPrimary consumer cast
   `(uint32_t)tcp_cached->data` = 0x61 as ARGB → `RGBA(0,0,97,0)`.
6. **Z-order EXCLUDED**: a temporary env-gated `MINIANDROID_RECT_TRACE`
   diagnostic proved the GREY_200 container fills paint BEFORE the text
   (parent-before-children DFS) and nothing paints over the rows after.

## Fix (three generic sites, zero app knowledge)

- `resource_runtime.cpp`: new `resolve_apk_file_color()` — extract the
  `res/color/…` entry from the APK itself, `parse_state_list`, default-state
  tri-match (window_focused=true, enabled=true,
  pressed/selected/checked/activated=false), in-item `@color/…` refs deref
  through the APP table (bounded depth 4).
- `resolve_theme_attr_typed()` S127 branch: on framework-router MISS, the
  app-package file law answers; the value is re-typed `INT_HEX`.
- `execution_engine.cpp` textColorPrimary consumer: **TYPE LAW** — only
  `is_int()/is_color()` answers paint as ARGB; any other type falls back to
  the legacy default. A string-pool index must never render as a color.

## Runtime result

- tanana: `dark_glyph_samples 0 → 4420`; all five rows render real text at
  `(29,29,29)` = the resolved `abc_primary_text_material_light`
  default-state color. New face `601e0219d4cab10b` ×3 deterministic.
- simplecalc fan-out: the display's initial "0" now renders. RAW-diff
  proven (base binary rebuilt via stash → `c8b078ba88ca255d` re-verified):
  the ONLY changed pixels in the entire 1080×1920 face are the 0-glyph bbox
  (1059-1078, 481-507). New face `950b955c6999d72a` ×3.
- BMI `b52252c2de19b03a`, alex `c8d69f811b23f245` byte-identical.

## Regression (fixed binary `06a08f7aadb3d402`)

- anchors 27/27 (8 faces byte-identical; tanana re-pinned)
- csw 3/3 (`3442d9a9dc0fa0f9`), simplecalc 3/3 (re-pinned), dooz180 3/3
  (`6841d52a20e6597e`)
- probe battery == records: 21 canonical probes (f259g 84/7 + fnew302
  48/24 documented known rows) + fnew322 5/0 + fnew326 13/0 + fnew326b
  13/0 + fnew327 3/0 + fnew328 4/0 ×3
- registry 646 → 647 (F-NEW-336 appended ROOT-CAUSED-FIXED; F-NEW-308
  marked DUPLICATE-SUPERSEDED with the refutation note); totals synced.

## Remaining named roots (unchanged)

BMI row-weight squeeze + Spinner selected-item content law; alex androidx
navigation chain (ISE "Fragment null has not been attached yet"); OpenCalc
srcCompat vector-drawable decode (F-NEW-309 family); dooz Compose draw
path (F-NEW-256 frontier) + Compose tap bridge (F-NEW-267).
