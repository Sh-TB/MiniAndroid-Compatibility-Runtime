# v0.0.5 — Silkie (Hello Color Real APK Milestone)

**Date:** 2026-09-12 · **Lineage:** F-076 binary at S22 · **Registry:** 302 roots, honest per-root status

Named after the Silkie hen — the project's release-mascot breed line
(Brahma → Australorp → Chantecler → **Silkie**). Mascot: `docs/assets/miniandroid-silkie-mascot.png`
(decorative only).

## Highlights

- **Verified real APK execution for Hello Color** — forensic provenance from committed fixture
  sources to pixel evidence: APK rebuilt byte-identical (`77863f1f…`), executed through the
  first-party Dalvik interpreter, rendered by the first-party software renderer.
- **Real DEX interpreter execution** — opcode-level trace (`execution_source=REAL_DALVIK_INTERPRETER`),
  30 instructions with pc/opcode/return values from the app's own bytecode.
- **Real Android Activity/View dispatch** — `MainActivity` `<init>/onCreate/setContentView/
  onStart/onResume`; `setContentView` resolves a real resource ID from real binary
  `resources.arsc`; View calls (`setBackgroundColor`, `setTextColor` ×3, `findViewById` ×4)
  originate in app DEX.
- **Real framebuffer rendering** — raw PPM framebuffer captured per run; PNG proven
  pixel-identical to the framebuffer raster (byte-for-byte, 1080×1920×3).
- **Pixel-identical PNG provenance** — run PNG `11e00563…` equals the committed golden frame
  post-hoc; the golden was never an input (zero references in binary/source/scripts).
- **Three-run deterministic reproduction** — 3 independent standard-path runs: rc=0 ×3,
  identical framebuffer SHA (`fb9f1df2…` ×3) and PNG SHA (`11e00563…` ×3).
- **HelloWorld / TicTacToe verified progress** — §28 golden battery 26 checks PASS;
  TicTacToe real interaction X→O→X WINS with 10-frame per-frame-SHA golden (§29 PASS).
- **ChessClock real rendering evidence** — rc=0 ×3, deterministic framebuffer screenshot
  `e4a2d7c9…` ×3 byte-identical (1080×1920, 100% painted).

## Evidence

- Forensic record: `docs/evidence/hello_color_golden/PROVENANCE_FORENSIC.json`
- Golden + 3 retest frames: `docs/evidence/hello_color_golden/`
- Execution traces: run dirs `exp031_5/traces/com.miniandroid.hellocolor/`
  (`opcode_trace.json`, `method_trace.json`, `register_trace.json`, `heap_trace.json`)
- README-frame derivation (Lanczos resize, SHA relation): `docs/assets/DERIVED_IMAGE_PROVENANCE.json`
- ChessClock evidence: `docs/evidence/campaign3_chessclock_real_screenshot/EVIDENCE.json`
- TicTacToe golden: `docs/evidence/tictactoe_golden/`
- Root registry: `root_registry.json` (302 roots)

## Known Open Work (not fixed — do not cite as fixed)

- **F-077** (registry `R-NEW-301`, OBSERVED-FAIL, P0) — Compose initial composition hits a
  kotlinx `TrieNode` invariant NPE (`K/t.s` check-cast): the one remaining broken transition
  between the (now-starting) Recomposer loop and the first Compose frame request.
  dooz framebuffer honestly remains 0 non-white.
- **R-NEW-302** (OBSERVED-FAIL, P1) — demo layout regression: FrameLayout child
  leftMargin/topMargin ignored (box pinned at stage origin) + root LinearLayout MATCH_PARENT
  wraps to 600×1432 instead of filling the window. Kept open deliberately; the Hello Color
  milestone does NOT depend on it and does not close it.
- **GATE H** — simplestopwatch PNG-glyph-to-framebuffer gap (the 1 real battery FAIL; battery
  91/92 honest).
- Telegram artifact fetch remains BLOCKED (upstream URL unreachable; zero-skip law).

## Facts

- Tag: `v0.0.5-Silkie` (annotated)
- No runtime code changed for this release: docs + assets + evidence only.
