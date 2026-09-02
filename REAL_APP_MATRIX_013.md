# REAL_APP_MATRIX_013 — Campaign 013 (same corpus, same classifier)

**Baseline note (evidence-first):** the directive baseline `v0.12.0 @ f5da664` 
does **not exist** in this environment. The SHA-verified lineage is 
`v0.11.3-unified-011-3 @ ea81e00` (handoff ZIP SHA256 
`45bae5948c0fe403a9d09bfd30ece63ccc70fbb755726b6b41fbb837ddfa9e6d`, manifest-matched). 
BEFORE = this verified baseline. AFTER = campaign-013 HEAD (5 fixes, all commits on branch `campaign-013`).

Classifier: `scripts/triage_013.py` (16-class taxonomy; identical before/after; 
nonwhite_px < 2000 can never classify REAL_UI; fallback-screen px=23472 with 
views=0 always classifies ACTIVITY_FAILED per the no-false-positive rule).

| APK | SHA256 (first 16) | Arch | BEFORE | AFTER | px B→A | views B→A | clicks changed B→A | first blocker (AFTER) |
|-----|-------------------|------|--------|-------|--------|-----------|--------------------|------------------------|
| gmdice | `1621eda11b5dbc0c` | F (productivity/dialogs) | REAL_UI | REAL_INTERACTION **+** | 158040→1744539 | 20→50 | 0→4 | [DalvikEngine] ⚠️ INVOKE-VIRTUAL: Null object reference (would be NullPointerExc |
| simplestopwatch | `b3ec1a5ec24ce53b` | A (classic views) | REAL_INTERACTION | REAL_INTERACTION | 916523→916523 | 29→29 | 2→2 | [DalvikEngine] ⚠️ INVOKE-VIRTUAL: Null object reference (would be NullPointerExc |
| microtimer | `79c6f730f64886e7` | F (productivity) | ACTIVITY_FAILED | ACTIVITY_FAILED | 23472→23472 | 0→0 | —→0 | [DalvikEngine]   METHOD [HAS CODE]: m(Ljava/lang/RuntimeException;)V / code_off= |
| unote | `be91103f0e7db443` | A/F (list + dialogs) | ACTIVITY_FAILED | REAL_INTERACTION **+** | 23472→2073600 | 0→64 | —→2 | [DalvikEngine] ⚠️ INVOKE-VIRTUAL: Null object reference (would be NullPointerExc |
| notesbillthefarmer | `82cf8bc44c163748` | A (classic views, obfuscated res) | ACTIVITY_FAILED | REAL_UI **+** | 23472→31752 | 0→9 | —→0 | [DalvikEngine]   METHOD [HAS CODE]: <init>(Lorg/billthefarmer/notes/Notes;Ljava/ |
| headingcalculator | `274ec873098eea51` | A (custom views) | ACTIVITY_FAILED | REAL_UI **+** | 23472→2073600 | 0→3 | —→0 |  |
| tinymusicplayer | `d7bcb24d101b04be` | A (WebView UI) | BOOT_FAILED | ACTIVITY_FAILED **+** | -1→23472 | 0→0 | —→0 |  |
| chessclock | `5ca6f2c54c05efe7` | A (classic views) | ACTIVITY_FAILED | REAL_UI **+** | 23472→2072520 | 0→15 | —→0 | [DalvikEngine] ⚠️ INVOKE-VIRTUAL: Null object reference (would be NullPointerExc |
| stopwatchmuellerma | `3b6a10c8dc8ddc72` | C (Kotlin/appcompat) | ACTIVITY_FAILED | ACTIVITY_FAILED | 23472→23472 | 0→0 | —→0 | [DexParser]   === EXP-031.6 CODE_ITEM @ offset=0x312368 for cancellationExceptio |
| bgclockhansdezwart | `72c140b0083ef273` | A (classic views) | REAL_UI | REAL_UI | 2073600→2073600 | 1→1 | 0→0 | [DexParser]   → Resolved name: [Landroidx/core/os/OperationCanceledException;] |
| simplekeyboard | `d83060833dc2bc97` | C (IME service) | ACTIVITY_FAILED | ACTIVITY_FAILED | 23472→23472 | 0→0 | —→0 |  |
| openlauncher | `b3320463a7a1ed46` | C (launcher/appcompat) | ACTIVITY_FAILED | ACTIVITY_FAILED | 23472→23472 | 0→0 | —→0 | [DexParser]   → Resolved name: [Landroid/support/v4/app/Fragment$InstantiationEx |
| tictactoeemmanuelmess | `760fe5acf7b39435` | E (libGDX/GLES) | PARTIAL_UI | PARTIAL_UI | 0→0 | 1→1 | 0→0 | [DexParser]   === EXP-031.6 CODE_ITEM @ offset=0x595328 for throwEglException == |
| dooz | `d81292cd346dcb23` | D (Compose) | PARTIAL_UI | PARTIAL_UI | 0→0 | 1→1 | 0→0 | [DalvikEngine]   METHOD [HAS CODE]: <init>(Ljava/lang/Exception;)V / code_off=0x |
| bouncy | `ffda0d9cb0b1b2aa` | E (libGDX canvas backend) | ACTIVITY_FAILED | REAL_INTERACTION **+** | 23472→2073600 | 0→280 | —→10 | [DexParser]   → Resolved name: [Lcom/badlogic/gdx/utils/GdxRuntimeException;] |
| droidify | `08d5a826be0cc5b6` | D (Compose) | ACTIVITY_FAILED | ACTIVITY_FAILED | 23472→23472 | 0→0 | —→0 | [DexParser]   → Resolved name: [Landroid/app/ServiceStartNotAllowedException;] |
| telegram_v12 | `f5e1192725772960` | E2E regression anchor | REAL_UI | REAL_UI | 41233→41233 | 234→234 | 0→0 | fatalError === |

## Status distribution (computed)

| Status | BEFORE | AFTER |
|--------|--------|-------|
| ACTIVITY_FAILED | 10 | 6 |
| BOOT_FAILED | 1 | 0 |
| PARTIAL_UI | 2 | 2 |
| REAL_INTERACTION | 1 | 4 |
| REAL_UI | 3 | 5 |
