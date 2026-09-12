# API — UNIFIED_007

## Runtime CLI (`build/miniandroid`)

```
miniandroid <command> [options] <apk>

Commands: run | analyze | dex | version | help

Options:
  -o, --output <dir>      output directory (default ./run)
  -v, --verbose           verbose execution logs
  --width <px>            screen width  (default 1080)
  --height <px>           screen height (default 1920)
  --text <text>           override displayed text
  --execution-mode <m>    legacy | real-dalvik (default real-dalvik)
  --journey <dir>         UNIFIED_007: run touch-journey evidence capture
  --max-taps <n>          journey tap budget (default 4)

Env:
  MINIANDROID_CLICK_AUDIT=1   structured click/touch audit JSONL
```

Exit codes: `0` SUCCESS, `1` FAILURE/PARTIAL, `139` crash (crash.log written).

### Journey artifacts (`--journey <dir>`)
- `step_00_launch.png` — frame after lifecycle, before any tap
- `step_NN_after_tap.png` — re-rendered frame after tap NN
- `journey.json` — `{schema:"journey_v1", taps:[{index,x,y,target_view_id,
  target_class,listener_class,dispatch_ok,screenshot,nonwhite_px,screen_text}]}`

## Job server (`build/u007_job_server`)

```
u007_job_server [port] [store.json] [bin_dir] [artifact_root]
# defaults: 8377 database/u007_jobs.json build run/u007_job_artifacts
```

| Method | Path | Result |
|--------|------|--------|
| GET | `/health` | `{"status":"ok"}` |
| POST | `/api/jobs` | 201 `{id,status:"QUEUED",...}` body `{"apk_path":"...","type":"apk_run\|captcha"}` |
| GET | `/api/jobs` | list (all jobs, compact) |
| GET | `/api/jobs/{id}` | full record incl. `logs[]`, `artifacts[]` |
| GET | `/api/jobs/{id}/status` | `{id,status}` |
| GET | `/api/jobs/{id}/logs` | live logs (milestone lines stream in while RUNNING) |
| GET | `/api/jobs/{id}/artifacts` | artifact file paths |
| POST | `/api/jobs/{id}/cancel` | 200 CANCELLED / 409 if terminal |

Status vocabulary: `QUEUED RUNNING WAITING CAPTCHA_REQUIRED FAILED COMPLETED
CANCELLED STALLED`.

Persistence: every transition flushed to the JSON store (temp+rename) —
SIGKILL-safe; restart restores verbatim state (verified by test).

CAPTCHA policy: jobs with `type:"captcha"` transition to
`CAPTCHA_REQUIRED` and stay paused. The server never bypasses CAPTCHA.

## In-repo tools

| Tool | Purpose |
|------|---------|
| `build/arsc_tool <apk>` | dump resources.arsc structure (packages/types/entries) |
| `build/axml_tool <apk> <res>` | decode binary XML to JSON |
| `build/test_audio` | audio state-machine + real-decode suite (47 checks) |
| `build/u007_font_proof` | render charter RTL/bidi/emoji strings → PNG + metrics |
| `build/u007_3d_proof` | 6-yaw software-3D render + pairwise geometry diffs |
| `scripts/u007_status_gen.py` | regenerate `status.json` from artifacts |
| `scripts/u007_corpus_final.py` | full corpus capability-split pass |
| `scripts/u007_job_server_test.py` | job-server E2E (10 checks) |
