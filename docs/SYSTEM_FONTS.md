# Virtual system-image fonts — `runtime/data/fonts/` (gitignored, bootstrap-restored)

Apache-2.0 fonts that ship in MiniAndroid's virtual system image, per the
AOSP `fonts.xml` law. Files here are fetched by the bootstrap flow
(source-first law: AOSP `platform/frameworks/base data/fonts/`), never
built. A missing file is a LOUD error in `[TEXTSHAPER]` — never a silent
substitution with a proportional face.

| File | Source (AOSP) | License | SHA-256 |
|------|---------------|---------|---------|
| DroidSansMono.ttf | platform/frameworks/base `data/fonts/DroidSansMono.ttf` (main) | Apache-2.0 (Google Corp., 2007 header) | `db19a1fdaba41cc4a2fec0330e5c15e71c6dd68a3ef074f4f28268828b45c862` |

Consumers:
- `miniandroid/src/fonts/text_shaper.cpp` — `kFaceMonospace` resolution
  (G32 law: `fontFamily="monospace"` / `Typeface.MONOSPACE` ->
  DroidSansMono.ttf). Resolution order: `MINIANDROID_FONT_DIR` env,
  exe-relative `runtime/data/fonts/`, then cwd-relative candidates.
  Missing file => loud `[TEXTSHAPER] SYSTEM FONT MISSING` diagnostic and
  `monospace=MISSING` in the READY banner.

Re-fetch (idempotent):
```
curl -s "https://android.googlesource.com/platform/frameworks/base/+/refs/heads/main/data/fonts/DroidSansMono.ttf?format=TEXT" | base64 -d > DroidSansMono.ttf
sha256sum -c <<< "db19a1fdaba41cc4a2fec0330e5c15e71c6dd68a3ef074f4f28268828b45c862  DroidSansMono.ttf"
```
