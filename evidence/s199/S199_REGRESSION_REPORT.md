# S199 REGRESSION REPORT — before/after on the integration line

Recorded: 2026-11-08 20:03 UTC. Baseline = S195 binary 31be843614e67bab; After = S199
binary 97628b00d237f9eb (the S196+S198c port + the W19a family on top).

| Metric | Before (31be…) | After (97628b00d237f9eb) | Verdict |
|---|---|---|---|
| tictactoe uncaught / APP BOUNDARY | 1 fatal GdxRuntimeException (AssetManager.load NPE) | 0 / 0 | IMPROVED (execution-depth: death → full boot + GL render) |
| tictactoe frame analysis | REAL_APP_CONTENT ×2 (GL-noise honestly recorded) | REAL_APP_CONTENT with REAL font glyphs (10 colors, black glyph pixels + AA grays) | IMPROVED (noise → real content) |
| gmdice interactive | 5 taps → 5 states | 5 taps → 5 states, rerun IDENTICAL | PRESERVED |
| goldens bouncy/unote/dooz | 3/3 pins | 3/3 pins | PRESERVED |
| floor battery | 11/11 | 11/11 | PRESERVED |
| microtimer | REAL_APP_CONTENT | 0 uncaught / 0 boundary / REAL_APP_CONTENT | PRESERVED (cleanest profile) |
| opencalc / chessclock | REAL_APP_CONTENT | 0 uncaught / 1 boundary each | UNCHANGED-ISH (1 boundary each — not newly introduced by the P0 chain; recorded for the next wave) |
| dooz uncaught baseline | 6 (pinned record) | 6 | PRESERVED (pin = byte-identical face) |
| C8 97/97 marker probe | previously verified on W18 binary | NOT RERUN this wave | PENDING |

New successes: tictactoe AssetManager/I18NBundle/FreeType/atlas/SpriteBatch
chain reaches the framebuffer (the S196 port + W19a family).
Execution-depth improvements are NOT counted as app completion anywhere in
this report (mission §7 law).


## NOTE — identity refresh (S199 close)
The S199 wave made two further source commits after the baseline was
written (F-NEW-619 typed-view parent chase at the f590 hook; F-NEW-620/
620b GL_ACTIVE_ATTRIBUTES=3 + glGetActiveAttrib canonical-name law).
The FINAL canonical S199 binary is 97628b00d237f9eb — goldens 3/3 ALL
HOLD and floor 11/11 CLEAN re-verified on it (this is the identity all
future waves compare against). The 619/620 laws did NOT yet move the
shape-attrib needle (glGetActiveAttrib never dispatched — the
fetchAttributes loop is gated deeper, at the AndroidGL20 real-native
path); that remains the named Coder-3 frontier with the evidence above.
