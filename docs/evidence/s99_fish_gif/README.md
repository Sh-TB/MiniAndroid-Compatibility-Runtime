# S99 FISH RINGS — CANONICAL INTERACTIVE GIF (fixes the "static JPG, not a GIF" homepage finding)

User finding (2026-09-25): the README Fish Rings demo embedded a static JPG —
the only one of the four homepage demos without real-motion evidence, and it
"never fully loaded" as a motion demo. This wave replaces it with the
canonical multi-state interactive GIF built from a real measured tap sequence.

## Run (real-dalvik, external F-Droid APK)

- APK: upload/canonical_apks/fishrings_v1.23_vc6.apk
  (eu.veldsoft.fish.rings vc6 v1.23, SHA-256
   c8a9cb7cadaaced37a1b13ba32ad9bdc1fbe6d38c9d5348aa56a78b4767c1c70 — identical
   to the S91 reproof fixture)
- Command: `./miniandroid/build/miniandroid run --execution-mode real-dalvik
  --frames 60 --tap 184,184@30 --tap 184,184@40 --tap 184,184@50
  -o run/s99/fish_gif/fish_tapseq upload/canonical_apks/fishrings_v1.23_vc6.apk`
- RC=0, 61 frames, Errors: 0, Warnings: 0

## Measured state changes (sampled full-res, PIL, stride 2 -> x4)

| Transition | Changed px | Meaning |
|---|---|---|
| frame_016 -> frame_021 | 2,073,600 | F-115 5000ms splash timer -> GameActivity (full-screen transition) |
| frame_031 | 4,304 | TAP 1: 36 ImageViews repaint via setImageResource (board appears) |
| frame_041 | 4,320 | TAP 2: ring rotation repaint |
| frame_051 | 4,308 | TAP 3: ring rotation repaint |

## Canonical GIF

- docs/evidence/canonical/eu.veldsoft.fish.rings.gif
- SHA-256 f225a04b9187b6074ad985ea4a8e8a8be8bcd15b3db39175f48262bda27e8e7c
- 400x711, 5 distinct states (Pillow delta-frame encoding accumulates dwell
  timing: splash 2.2s -> empty board 2.4s -> board painted 1.9s -> rotation
  1.9s -> final 2.2s), loop=0
- Builder: scripts/s99_fish_gif.py (deterministic: LANCZOS resize, MEDIANCUT
  palette, dither NONE)

## Homepage wiring

- README demo table row + demo grid now embed the GIF (was: static JPG).
- docs/EXECUTED_GIFS.md canonical table: 12/12 -> 13/13 interactive titles.
- docs/evidence/canonical/SHA256SUMS: GIF entry appended (JPG kept as the
  historical single-frame artifact).
