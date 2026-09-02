# BUG_RECONCILIATION_013 (§26 — historical BUG-01..85 as hypothesis pool)

Directive-mandated distinctions, applied to this campaign:

- **NOT_REPRODUCED** — historical documents lost (pre-011.1 campaigns were
  declared lost in 011.3); no current evidence either way.
- **VERIFIED** — reproduced on current HEAD with runtime evidence.
- **PARTIAL** — some aspect reproduced.
- **CONFIRMED_OPEN** — current evidence proves the blocker still exists.
- **BLOCKED** — artifact unavailable in this environment.
- **INVALID** — historical claim contradicted by current behavior.

Per the directive, this campaign does NOT claim "85/85 audited". The matrix
below records only items for which THIS campaign produced current evidence.
Everything else remains in its 011.3-era state (hypothesis pool).

| Item | Historical claim | Current-HEAD evidence (campaign 013) | Verdict |
|------|------------------|--------------------------------------|---------|
| "obfuscated ARSC resource paths" (011.3 open blocker #4; campaign-012 summary claimed fixed) | ARSC obfuscated names unresolved | notesbillthefarmer probe: ARSC value `res/w6.xml` IS the path; name-matching returned NONE → all layouts unresolved. FIXED this campaign (FIX-013-04) | CONFIRMED_OPEN → RESOLVED (FIX-013-04) |
| Compose children (dooz L4) | ComposeView children never compose | dooz still 1 view / 0 px; droidify dies earlier (appcompat attach chain) | CONFIRMED_OPEN (OB-1) |
| GLES static GLES20 wiring / no EGL | no GL context | tictactoe: game-surface View object flows through setContentView but no EGL/node exists | CONFIRMED_OPEN (OB-3) |
| runtime-view construction (gmdice L13, "second frame 0-px honest") | dialog/menu layer missing | RESOLVED: dialog object model (FIX-013-01); gmdice 4/4 interactions changed pixels | VERIFIED → RESOLVED |
| app-class name-list dispatch (per-app special cases) | ActivityShadow handled known app classes only | ChessClock silently no-op'd; RESOLVED by hierarchy dispatch (FIX-013-02) | VERIFIED → RESOLVED (FIX-013-02) |
| WhatsApp artifact | not in environment (0-byte cache lost) | not re-acquired this campaign | BLOCKED |
| Signal artifact | not in environment | not re-acquired this campaign | BLOCKED |
| Telegram v12 golden | L12 deterministic render | golden `088ea640` EXACT on current HEAD (re-verified twice this campaign) | VERIFIED (green) |
| GMDice golden `472c1d3c` | 3/3 deterministic | frame-1 SHA moved (158040→1744539 px): first-launch dialog now RENDERS — app-driven change, not a runtime regression; interaction evidence supersedes | INVALID as a frozen SHA (old golden embedded a rendered lie per §25); interaction evidence is the new anchor |
| SimpleStopwatch golden `2a12587a` | icons render | EXACT after every fix (including after onDraw execution: BigTextView dispatched=YES ops=0 graceful degradation) | VERIFIED (green) |
| semantic fixtures 8/8 + 5/5 | green | re-run after EVERY fix: green | VERIFIED (green) |
| bouncy "libGDX menu rendering" (campaign-012 claim, no local artifacts) | menu visible | not verifiable pre-fix; CURRENT state: 280 views + real onDraw pixels + REAL_INTERACTION | NOT_REPRODUCED (as a historical artifact) → current state VERIFIED independently |
| microtimer runnable | L1 default screen | app-side IAE aborts onCreate (OB-5) — WORSE than historical claim, honest status | CONFIRMED_OPEN (OB-5) |
| tinymusicplayer L2 | ran in 011.3 | v1 APK lost; v4 APK SHA-locked (`d7bcb24d…`), boots, WebView UI boundary | PARTIAL (artifact drift documented) |

New blockers discovered this campaign receive B13-NEW ids in
TOP_BLOCKERS_013.md (OB-1..OB-7); no findings were forced into old numbers.
