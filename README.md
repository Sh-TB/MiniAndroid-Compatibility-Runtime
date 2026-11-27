# MiniAndroid Showcase

Public static evidence gallery for the MiniAndroid Compatibility Runtime.

## Updating the gallery
Edit `data/achievements.json`. Add only records backed by inspectable evidence. Do not invent totals, screenshots, APK hashes, runtime commits, or test results.

Required fields per record:
- `title`, `type` (`app` or `game`), `status`
- `package`, `version`, `apk_source`, `apk_sha256`
- `runtime_commit`, `runtime_binary_sha256`, `test_date`
- `launch_result`, `visual_result`, `interaction_result`
- `notes`; optional `screenshot`, `issue_url`, `log_url`, `blocker`

Statuses: `CURRENT-REPRODUCIBLE`, `INTERACTIVE`, `HISTORICAL-REAL`, `PARTIAL`, `REGRESSED`, `BLOCKED`, `PENDING`, `NOISE`.

Use genuine, unaltered MiniAndroid runtime captures only. Keep images small (prefer 400–500 px wide), link evidence to the relevant issue/log, and preserve regressions. Historical success must never be presented as current reproducibility.

The previous S80 gameplay page is preserved at `archive/s80/index.html`; its original GIF files remain at the branch root.
