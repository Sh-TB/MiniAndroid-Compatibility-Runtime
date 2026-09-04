# QUICKSTART — 60 seconds to real APK execution

```bash
cd miniandroid
make -j4
```

## 1. Run a real APK with a touch journey

```bash
./build/miniandroid run \
    --output run/gmdice \
    --journey run/gmdice/journey \
    --max-taps 6 \
    download/corpus/gmdice.apk
```

Outputs:
- `run/gmdice/journey/step_00_launch.png` — launch frame (real inflated UI)
- `run/gmdice/journey/step_01_after_tap.png` — frame after a REAL tap
- `run/gmdice/journey/journey.json` — tap records (x, y, target view, class,
  listener, dispatch result, per-frame nonwhite counts)
- stderr: `[U007-MOTION] DOWN/UP …` + `[UI-EVENT] CLICK …` + deep DEX traces

## 2. Telegram full auth chain (real 5-DEX APK)

```bash
MINIANDROID_CLICK_AUDIT=1 ./build/miniandroid run \
    --output run/tg download/exp038_telegram/Telegram.apk
ls run/tg/telegram_0*.png   # 5-stage evidence chain
```

Chain proven: intro → StartMessaging click → LoginActivity → phone input →
onNextPressed → TL_auth_sendCode → controlled mock response →
RequestDelegate → fillNextCodeParams → setPage(2) → SmsView rendered.
Mock is ONLY at the network boundary; all logic is real interpreted DEX.

## 3. Font pipeline proof (RTL / mixed bidi / emoji)

```bash
./build/u007_font_proof run/fontproof
open run/fontproof/proof.png     # «سلام دنیا» «Hello دنیا» «۱۲۳۴۵» Hello World
```

## 4. Audio state machine (PLAYBACK_COMPLETED fix)

```bash
./build/test_audio               # 47/47 PASS (real mp3/wav/ogg decode)
```

## 5. Software 3D proof (yaw 0–300)

```bash
./build/u007_3d_proof run/3d
open run/3d/frame_000.ppm …      # 6 frames + pairwise geometry diffs
```

## 6. Persistent job server + REST API

```bash
./build/u007_job_server 8080 database/jobs.json build run/artifacts &
curl -X POST localhost:8080/api/jobs \
     -d '{"apk_path": "download/corpus/gmdice.apk", "type": "apk_run"}'
curl localhost:8080/api/jobs/<id>/logs     # live milestone logs
# kill -9 the server, restart it: state survives (refresh-safe)
python3 scripts/u007_job_server_test.py    # 10/10 PASS
```

## 7. Regenerate machine-readable status

```bash
python3 scripts/u007_status_gen.py run/status
cat run/status/status.json
```
