# S91 FISH RINGS ICON E2E — POST-REBOOT REPROOF (2026-09-23)

Fresh reproduction of the icon-pipeline proof after the 2026-09-23 21:27 UTC
container reset (the original run artifacts were untracked and wiped; this run
re-establishes the evidence chain on tracked paths).

## Fixture (SHA-exact)

- APK: eu.veldsoft.fish.rings vc6 v1.23 (F-Droid)
- SHA-256: c8a9cb7cadaaced37a1b13ba32ad9bdc1fbe6d38c9d5348aa56a78b4767c1c70
- Source: upstream/corpus/eu.veldsoft.fish.rings/ (commit dc3807e7, tarball
  SHA ffb13f0e...) — source-first law location below.

## Command

```
./build/miniandroid run --execution-mode real-dalvik --frames 60 \
    --tap 184,184@40 -o run/s91/fish_tap_reproof run/s91/fish_rings2.apk
```

RC=0, 61 frames rendered, 0 errors in crash.log.

## Provenance chain (every link re-verified in this run's log)

| Link | Evidence (grep targets in fish_tap_reproof.log) |
|---|---|
| SOURCE LAW | GameActivity.java: arrow onClick handlers call updateInfo() -> repaint(); repaint() sets R.mipmap.red/green/blue/violet on the 36 fish ImageViews (lines 100-121). The board starts EMPTY (no android:src on fish views) — icons appear ONLY through setImageResource. |
| TIMER TRANSITION (F-115) | `[F115-TIMER] schedule task=o20 delay=5000ms caller=...SplashActivity;.onResume` -> `[R350-FORNAME] eu.veldsoft.fish.rings.GameActivity` -> `[INTENT] startActivity called` |
| RESOURCE RESOLVED | `[EXP062-SV-DONE] R$mipmap with_defaults=16/16` — every R$mipmap field resolved |
| DECODED | `[A7b] icon @0x7f0e0005 -> res/RJ.png (11357 bytes) DECODED 144x144` |
| TAP DISPATCHED (F-117) | `[F117-TAP] frame 40 DOWN (184,184) target=31` — hit test reached a clickable view |
| VIEW BOUND | `SETIMAGE=36` — all 36 fish ImageViews received setImageResource in one repaint() |
| STATE CHANGE | frame_039.png vs frame_041.png: **4,312 pixels changed** (exact full-res count, PIL) — the fish board appeared at the tap |
| SCREENSHOT CAPTURED | frames/frame_039.png (pre) + frames/frame_041.png (post) in this directory |

## Measured corrections vs docs/S91_REPORT.md first wave

- Fish ImageViews: **36** (12 per ring x 3 rings, per the views[] array in
  onCreate) — the first wave wrote "49"; corrected here.
- setImageResource calls on first repaint: **36** (one per view) — the first
  wave wrote "46"; corrected here.
- Pixel change: first wave "4,257" (sampled); this run measured the exact
  value **4,312** on the same hardware path (different tap frame; both runs
  show the same magnitude — one ring rotation repaint).
