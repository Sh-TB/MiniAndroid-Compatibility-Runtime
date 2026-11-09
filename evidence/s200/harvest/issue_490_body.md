# [Coder 2] App tracker — OpenLauncher (`com.benny.openlauncher`) v39

**Living issue: every future progress note for this app goes into THIS body — no comments are used in this campaign.** Whenever I need this app's state, I re-read this issue. Identity: Coder 2 lane · Master ledger: **#472** · Deep-dive: **#466**

## Current face (tracker opened 2026-11-03 · runtime commit `7354c06`)
| Field | Value |
|---|---|
| Status | **BACKGROUND-ONLY #303030 — 22 custom views** |
| Face | FROZEN pin re-validated; 22 `unrendered custom view RECORDED` = best paint-gap stress test in corpus |
| Registry pin (SHA256) | `b3320463a7a1ed46c52464bae83a97317d062b1e2097bd1885cdf265f2089f89` |
| APK source | `https://f-droid.org/repo/com.benny.openlauncher_39.apk` |
| Render evidence | `17-openlauncher.png` · sha256 `b5a7a35d5fe0564b08842f187f4e293bbb1d1b63099ba43978542449ae8c1f5b` |
| Blocker | Custom-view paint path (22 inflated-but-unpainted views, individually recorded). |

## Simple verification test (one command)
```bash
curl -sL -o app.apk https://f-droid.org/repo/com.benny.openlauncher_39.apk && echo 'b3320463a7a1ed46c52464bae83a97317d062b1e2097bd1885cdf265f2089f89  app.apk' | sha256sum -c && \
./build/miniandroid run -o /tmp/vt --width 1080 --height 1920 --data-root /tmp/vtd --max-seconds 120 --frames 5 --frame-delay 2000 app.apk && \
python3 -c "from PIL import Image;import numpy as np;a=np.asarray(Image.open('/tmp/vt/screenshot.png').convert('RGB'));print('center:',a[960,540],'non-white px:',int((a.min(axis=2)<245).sum()))"
```

## Next rung
Best single-app delta meter for any custom-view draw fix.

## Progress log (newest on top; body-edited, never commented)
- 2026-11-03 · wave T (engine S155 `be9329bb`, local rebuild sha16 `9d5772d25d7b0102`): face re-run **byte-identical to pin** on S155 (default byte-inert confirmed on this app); no new PNG needed (`b5a7a35d…`). Plus **C013 census with 6 named classes** (log `35-openlauncher-s155-c013.log`): 4 app-owned launcher widgets — `Lcom/benny/openlauncher/widget/Desktop;`, `.SearchBar;`, `.AppDrawerController;`, `.PagerIndicator;` (×5 each) + 2 intro widgets `Lagency/tango/materialintroscreen/widgets/SwipeableViewPager;`, `.InkPageIndicator;`. The home-screen grid itself (`Desktop`) is inflated-but-unpainted — next rung = paint law for app-owned custom widgets.
- 2026-11-03 · wave S (W2-patch A/B + S154 attribution runs): **W2-patch cross-validation (Coder-4 nine-law stack, patch sha16 `9570a4da6f52ba5b`, applied at repo root, rebuilt local binary sha16 `d8c9bba94e21f4e1`)**: face re-run **byte-identical to pin** both with patched defaults and with `MINIANDROID_F261X_LAW=1` — the stack is **neutral** for this app. Control anchor intact; no new PNG (byte-identical).
- 2026-11-03 · engine S154 `7bbf087a` (rebuild binary per #446 recipe): face re-run **byte-identical** to pin: sha16 `b5a7a35d5fe0564b` == #466 pin; 22 unrendered custom views reproduced (`28-openlauncher-s154.png`).
- 2026-11-03: tracker opened. Face = **BACKGROUND-ONLY #303030 — 22 custom views** (carried from deep-dive #466).
