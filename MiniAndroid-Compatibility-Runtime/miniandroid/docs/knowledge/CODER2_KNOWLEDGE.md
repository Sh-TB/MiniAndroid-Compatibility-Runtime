# Coder 2 Knowledge Archive

**Mission:** Independent OX/Tic-Tac-Toe + libGDX + graphics + GUI + gameplay research.

**Status:** Active (secondary lab, no GitHub write access)

## GUI Infrastructure

- Xvfb works for headless display.
- `-ac` may be needed because xauth is unavailable.
- ffmpeg x11grab captures real display pixels.
- tkinter `event_generate(when="now")` can provide application-level input.
- VNC is optional and was unavailable; do not block work on VNC.
- A real display + capture + input route is sufficient.

## OX / libGDX Research

- OX/Tic-Tac-Toe is libGDX-based.
- Uses GLSurfaceView / GL20.
- ShapeRenderer is central to board drawing.
- Real `create()` bytecode executes.
- Real `render()` executes.
- `TicTacToeRenderer.draw` executes.
- `Stage.draw` is reached.
- Cross-DEX GameData execution works.
- `ArraysKt.fill$default` and `List.clear` have been exercised.
- SoftwareGL20, GdxApp/GdxInput, and NIO shadow infrastructure were developed.

## Generic Findings

### C2-F01: Receiver/this propagation
- **Status:** PROVEN, integrated in primary branch
- Receiver/`this` propagation failures can silently break field writes.
- Primary branch already contains historical fix (EXP-061).

### C2-F02: Gdx.gl20 static state
- **Status:** PROVEN (game-specific)
- `Gdx.gl20` can be read separately from `Gdx.gl`; static state must be coherent.

### C2-F03: NIO getter/setter semantics
- **Status:** HYPOTHESIS (not yet integrated)
- NIO getter/setter semantics require exact signature distinction:
  `limit()` vs `limit(int)` and equivalents.

### C2-F04: Unsafe glBufferData traversal
- **Status:** HYPOTHESIS (game-specific)
- Unsafe `glBufferData` traversal can overrun buffers/heap.

### C2-F05: Interface dispatch ordering
- **Status:** PROVEN, relevant
- Interface dispatch ordering can allow framework/JNI stubs to swallow real calls.

### C2-F06: D8/R8 lambda resolution
- **Status:** PROVEN, integrated in primary branch
- invoke-static/D8/R8 lambda resolution can select the wrong implementation.
- Primary branch fixed this with exact-match behavior for `$r8$lambda` names.

### C2-F07: array-length bugs
- **Status:** PROVEN, integrated in primary branch
- Two generic bugs:
  1. 12x B-register must be read from `(instr >> 12) & 0xF`
  2. object-array length must come from heap metadata

### C2-F08: ViewShadow over-interception
- **Status:** PROVEN (game-specific)
- ViewShadow can over-intercept `draw`, `layout`, `measure` on arbitrary classes.
- Only genuine Android View inheritance should receive Android View semantics.

### C2-F09: AssetManager/shadow ordering
- **Status:** HYPOTHESIS
- AssetManager/shadow ordering can be wrong.
- Do not make AssetManager.load a blanket no-op without proof.

### C2-F10: Array.add (negative finding)
- **Status:** NEGATIVE_FINDING
- Array.add was suspected, but a minimal reproducer showed it can work.
- Do not blame Array.add without a reproducer.

### C2-F11: DEX tooling misdecode
- **Status:** PROVEN (tooling warning)
- Secondary lab's own DEX tools sometimes misdecoded 23x register packing, instruction width, array-length, register lists.
- Independent verification is mandatory before changing VM code.

### C2-F12: Wide-value findings
- **Status:** PROVEN, integrated in primary branch
- Missing return-wide (opcode 0x10)
- Bad move-result-wide (hardcoded to 0)
- MOVE_WIDE (opcode 0x04) missing
- All fixed in primary branch with permanent regression tests.

### C2-F13: Lazy-load/reserve/reference-lifetime
- **Status:** HYPOTHESIS
- A possible lazy-load/reserve/reference-lifetime issue was observed in a secondary branch.
- Treat as hypothesis until independently reproduced on current HEAD.
- Primary branch audited: no `reserve(43895)` exists. Defense-in-depth added.

### C2-F14: Swallowed C++ exceptions
- **Status:** HYPOTHESIS
- C++ exceptions swallowed at invocation boundaries can produce misleading success/fallback.

## Research Tracks

- **A — APK Intelligence:** APK → static map → JSON/MD
- **B — Real Micro-APK Generator:** primitive → real APK → reproducible test
- **C — UI Evidence Comparator:** expected screenshot/hierarchy ↔ actual → machine-readable diff

## OX Final Acceptance Criteria

- real board pixels
- external input
- visual board recognition
- autonomous move choice from pixels
- real UI clicks
- computer response
- AI WIN / COMPUTER WIN / DRAW
- reproducibility
- no internal GameData access by AI

## Historical OX Evidence

Historical archive contains evidence of an earlier real OX board/frame reaching framebuffer pixels, with real 3x3 geometry and pixel comparisons, and a center-cell click reaching a visible view. This is historical evidence only, not proof of current HEAD.

---

## C2-F22: BOOLEAN zero-ness in if-eqz/if-nez (independently confirmed)

### Status: PROVEN, INTEGRATED (Primary commit 063c772)

Coder 2 independently hypothesized that BOOLEAN type values with int_val==0
were not being treated as zero by if-eqz. This was independently confirmed
by Primary Coder's Telegram source-first investigation:

- **Source-first**: Used Telegram source (LoginActivity.java line 3185-3197)
  to understand the callback semantics.
- **DEX verification**: Traced `lambda$onNextPressed$22` PC=8 where
  `if-eqz v4(BOOLEAN false)` was NOT taken (should have been).
- **Root cause**: `is_zero` check in `execute_if_eqz` was missing BOOLEAN type.
- **Fix**: Added BOOLEAN, BYTE, SHORT, CHAR to is_zero/is_nonzero checks.
- **Generic impact**: Affects ALL APKs using instance-of results in branches.

This finding is promoted to high-confidence generic VM knowledge and
cross-referenced in CODER_MAIN_KNOWLEDGE.md as CM-008.

### C2-F31: OX/TicTacToe real board rendering

Three bugs were fixed by Coder 2:
1. BitmapFontData.missingGlyph was null.
2. fetch_vertex byte-VBO path did not assign output data.
3. Pools.get / Pool.obtain / Pool.free lacked compatibility handling.

Results: ASAN EXIT=0, regular EXIT=0, real board pixels reach framebuffer.
Status: PROVEN on Coder 2's branch. Not yet integrated into main.

### General Reconciliation Status

| Finding | Status on Current HEAD |
|---------|----------------------|
| C2-F01 (receiver/this) | INTEGRATED (EXP-061) |
| C2-F06 (D8/R8 lambda) | INTEGRATED (EXP-089) |
| C2-F07 (array-length) | INTEGRATED |
| C2-F12 (wide values) | INTEGRATED (EXP-089) |
| C2-F22 (BOOLEAN if-eqz) | INTEGRATED (EXP-093, CM-008) |
| C2-F31 (OX board rendering) | NOT YET INTEGRATED (on Coder 2 branch) |
| C2-F13 (lazy-load) | HYPOTHESIS (defense-in-depth added) |
| C2-F14 (swallowed exceptions) | HYPOTHESIS |
