# CONT-59 RESULT — F-NEW-337 + F-NEW-337b (declarative Spinner content + theme-attr ColorStateList items)

Binary: 06a08f7aadb3d402 (base, byte-identical CONT-58 record) → c0162daeaee55a10 (fix). HEAD a212cbad.

## Legs closed

### F-NEW-337 — Spinner android:entries law (inflater)
- BMI v402 spinners (weightSpinner/heightSpinner, 817x105) rendered `text=''`, `children=0`: the
  adapter comes from the XML `entries` attr (AOSP widget-ctor ArrayAdapter — no DEX call).
- AXML decode: `<Spinner android:entries="@array/weight_units">`; arrays exist ONLY as compiled
  ARSc complex entries ('Kilograms'/'Pounds', 'Centimetres'/'Inches').
- FIX: one generic `entries` branch in layout_inflater.cpp → `resolve_string_array` (F-NEW-319)
  → selected item (index 0) into a.text → the generic text pipeline paints it.
- Measured: U007 shows text='Kilograms' / text='Centimetres'.

### F-NEW-337b — theme-attribute ColorStateList item law (framework + app paths)
- Spinner text traced `color=(0,0,16,0)` (alpha-0): the framework `text_color_primary.xml`
  default item color is `?attr/colorForeground` (TYPE_ATTRIBUTE 0x01010030) — the old deref fed
  the attr id to the resource table, read the attr-DEFINITION row, and painted its INT (16) as
  ARGB. Upstream AOSP selector verified byte-for-byte in structure
  (docs/upstream/aosp/res_color/text_color_primary.xml).
- FIX: `resolve_framework_file_color()` deref + `resolve_apk_file_color()` item loop route
  0x0101xxxx refs through `resolve_theme_attr_typed()` with the F-NEW-336 type law.
- Fan-out (raw-diff-proven): gmdice 'Push buttons to roll!' hint line now renders themed white —
  ONLY changed region (62,1155)-(1020,1332); everything else byte-identical.

## Regression
- anchors x3: 14 faces byte-identical (dooz, micro, unote, ttt, flappy, g2048, opencalc,
  tanana 601e0219, simplecalc 950b955c, csw, BMI→not-a-gate-anchor, alex, notes, sol).
- gmdice INTENTIONAL re-pin f3b483fe → 3891679d (rationale in cont37_regression.sh).
- probe battery == records (f259g 84/7 + fnew302 48/24 documented known rows).

## Honest remaining frontier (BMI spinner visibility)
The resolved item color is themed WHITE (the app's declared dark Material base theme — correct
AOSP chain), which sits on the engine's GREY_200 container fill → white-on-light. Named next
root: EXP-092 GREY_200 fill vs the AOSP transparent-container law. Measured blast radius
(tanana 1.9M / simplecalc 614k / opencalc 272k / microtimer 124k / unote 166k fill px) →
ships as its own wave (F-NEW-338 candidate) with per-anchor raw-diff audits.

## Artifacts
- evidence/cont59/{gmdice_f337b_before_after.png, bmi_f337_before_after.png}
- scripts/cont59_axml.py, scripts/cont59_registry.py (647 → 649)
