# S199 END-TO-END BATTERY — commands, identities, evidence

Recorded: 2026-11-08 20:03 UTC. Binary 97628b00d237f9eb (sha256 97628b00d237f9ebc2bd0c66251975998ee77384089384c7f47b8b3b339d335b).

## Reproduce (each from /home/z/my-project)
```
# tictactoe plain launch probe
python3 scripts/s199_ttt_probe.py
# tictactoe interactive (frames + taps)
python3 scripts/s199_ttt_interactive.py ttt_s199_int_r1 48 250
# cohort battery (microtimer/opencalc/chessclock)
python3 scripts/s199_battery.py
# gmdice 5-tap interactive regression
python3 scripts/autoplay/s121_gmdice_autoplay.py
# goldens + floor gates
python3 scripts/s188_golden_check.py
python3 scripts/s188_w18_floor_rerun.py
```

## Results recorded this wave
| Test | Result | Evidence |
|---|---|---|
| tictactoe launch probe | 0 uncaught, 0 APP BOUNDARY, GL frames presented | evidence/s199/ttt_s199_probe_r1.console.log |
| tictactoe interactive 48f | 54 frames, TOUCH consumed=true, font glyphs in framebuffer | evidence/s199/face_ttt_first_glyphs.png (sha16 fc0997a63f3b2dec) |
| gmdice 5-tap | 5 CHANGED result states, rerun IDENTICAL | autoplay script output |
| cohort microtimer | 0 uncaught / 0 boundary / REAL_APP_CONTENT | evidence/s199/battery/microtimer_s199_r1.console.log |
| cohort opencalc | 0 uncaught / 1 boundary / REAL_APP_CONTENT | battery/opencalc_s199_r1.console.log |
| cohort chessclock | 0 uncaught / 1 boundary / REAL_APP_CONTENT | battery/chessclock_s199_r1.console.log |
| goldens 3/3 | ALL HOLD on 97628b00d237f9eb | s188_golden_check output |
| floor 11/11 | CLEAN | s188_w18_floor_rerun output |

## Honest status of the two §4 targets
- Target A microtimer: APP-OBSERVED + clean cohort profile. The core
  feature acceptance script (§4.1 A–M) is NOT yet written/run — the
  END-TO-END-VERIFIED claim is NOT made this wave.
- Target B tictactoe: APP-OBSERVED (font chain end-to-end to the
  framebuffer; input dispatched; game loop alive). The board render +
  gameplay completion are NOT yet verified; the named first divergence is
  the shape-renderer VBO attribute bind (attrib0=(nil) draws) and the
  per-frame re-render (static frame after boot frames).


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
