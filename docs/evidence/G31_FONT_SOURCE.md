# G31 — IDENTIFY REAL FONT SOURCE

Campaign: MASTER VISUAL COMPATIBILITY CAMPAIGN · Gate: G31
Date: 2026-09-06 · HEAD: `d1244ec9` (pre-fix diagnostics; fixes in C2+)
Fixture: `EXT-01-HELLOWORLDSELFAWARE-1.1.0` (frozen, SHA-256 `009b4671…cc41`,
re-verified this session after the sandbox corpus wipe — re-download +
SHA-256 match against the frozen record).

## Question

Which font does the external APK actually use on a trusted Android device?

## 1. APK evidence (from the frozen APK bytes — Rule: not from appearance)

Tool: `scripts/dump_axml_attrs.py` (stdlib AXML parser, ResXMLTree_attrExt
layout per AOSP ResourceTypes.h). The layout is a shortened resource path
(`res/02.xml` — aapt2 resource shortening); all three layout config variants
in the APK are byte-identical single-`TextView` layouts.

```
ELEMENT TextView
  ATTR textAppearance        id=0x01010034 type=0x01 (REFERENCE) data=0x01030042
  ATTR textColor             id=0x01010098 type=0x01 data=0x7f010003 (@color/hello_color)
  ATTR gravity               id=0x010100af type=0x11 data=0x00000011 (center)
  ATTR id                    id=0x010100d0 data=0x7f020000
  ATTR layout_width          id=0x010100f4 type=0x10 data=0xffffffff (MATCH_PARENT)
  ATTR layout_height         id=0x010100f5 type=0x10 data=0xffffffff (MATCH_PARENT)
  ATTR lineSpacingMultiplier id=0x01010218 type=0x04 (FLOAT) data=0x40000000 (=2.0f)
  ATTR fontFamily            id=0x010103ac type=0x03 (STRING) raw='monospace'
  ATTR elegantTextHeight     id=0x0101045d type=0x12 (BOOLEAN) data=0xffffffff (true)
```

- `android:fontFamily="monospace"` — the SYSTEM monospace family
  (`monospace` is a well-known system family alias, not an app-bundled font).
- NO `android:textSize` — the size comes from `textAppearance`.
- NO bundled font files: the APK has 21 PNGs + 7 XMLs, no `.ttf`/`.otf`
  entries (ZIP listing in EXTERNAL_FIXTURE_HELLOWORLDSELFAWARE.md).
- Cross-check: upstream source at tag v1.1.0 (commit `9526576`, layout file
  `191bb048834d`) matches the compiled AXML exactly (re-fetched + shown in
  the session transcript).

## 2. Android framework evidence (AOSP law, fetched at exact revisions)

`platform/frameworks/base@android-14.0.0_r50` (API 34) and
`@android-15.0.0_r2` (API 35) — both fetched from android.googlesource.com
this session (raw base64 blobs saved under /home/z/corpus/aosp/):

- `data/fonts/fonts.xml` L253-255 (identical in both tags):

  ```xml
  <family name="monospace">
      <font weight="400" style="normal">DroidSansMono.ttf</font>
  </family>
  <alias name="sans-serif-monospace" to="monospace" />
  ```

  → family "monospace" resolves to the platform font file
  **`/system/fonts/DroidSansMono.ttf`**.
- `DroidSansMono.ttf` is **byte-identical across android-14 and android-15**
  (SHA-256 `db19a1fdaba41cc4a2fec0330e5c15e71c6dd68a3ef074f4f28268828b45c862`,
  172,536 bytes, verified equal). The file exists and resolves the same way
  at API 36 (android-16.0.0_r2 path probe → HTTP 200). The trusted reference
  screenshot was taken on the app author's Android 16 (API 36) phone, so the
  AOSP mapping chain applies to it.
- `core/res/res/values/styles.xml` L862-864:

  ```xml
  <style name="TextAppearance.Large">
      <item name="textSize">22sp</item>
  </style>
  ```

  → the effective textSize law for this layout is **22 sp** (G46's input).
- License: Droid Sans Mono is shipped in AOSP under the Apache-2.0 license
  (Google, 2007 — embedded font name table confirms).

## 3. MiniAndroid evidence (current HEAD, runtime + code)

- `src/fonts/text_shaper.h` L191-196: the system faces are
  `DejaVuSans.ttf` (regular), `DejaVuSans-Bold.ttf`, `FreeSerif.ttf`
  (fallback), `NotoColorEmoji.ttf`. **There is no monospace family concept
  and no `fontFamily` attribute parsing anywhere in the runtime**
  (`grep -rn 'fontFamily' src/` → 0 hits in the inflate path).
- Runtime log of the EXT-01 run at this HEAD:
  `FONT_RESOLUTION source=SYSTEM bold=0 (app did not request an app face)`
  with `primary=DejaVuSans.ttf` — the app's `fontFamily="monospace"` was
  silently dropped and text rendered with the proportional default sans.
- `tests/font_pipeline_probe` (added this session, C1) dumps the live faces
  and per-glyph metrics for exactly this purpose.

## 4. Conclusion

| Question | Answer | Status |
|---|---|---|
| Bundled font? | NO — no font files in the APK | verified (ZIP listing) |
| System family? | YES — `android:fontFamily="monospace"` | verified (APK AXML) |
| Which platform file? | `DroidSansMono.ttf` (AOSP fonts.xml, stable API 34→36, byte-identical) | researched (AOSP source) |
| Effective textSize? | 22sp via `TextAppearance.Large` (no explicit textSize) | verified (APK AXML + AOSP styles.xml) |
| MiniAndroid current face? | DejaVuSans (proportional), family attr dropped | observed (runtime log) |

**Status: `verified`** (APK bytes + AOSP source + runtime observation all
agree; the only inference is that the reference phone's OEM does not remap
the `monospace` family away from AOSP's DroidSansMono — supported by the
byte-stability of the font across Android 14→16 and the G35/G46 measurement
agreement that follows).

Confidence: HIGH. Risk note (recorded, not acted on): an OEM could in
principle bundle a different monospace face (e.g. Roboto Mono); at the
reference screenshot's measurement precision the G35 gate cannot distinguish
Droid Sans Mono (advance 1233/2048 = 0.60205 em) from Roboto Mono
(1229/2048 = 0.60009 em); the AOSP law is the transferable rule and is what
G32 wires in.
