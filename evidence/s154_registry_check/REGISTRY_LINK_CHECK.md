# S154 — REGISTRY LINK CHECK (frozen-mirror law, Coder-2 #449/#458 adopted)

Method: `scripts/registry_link_check.py` (Coder-2's #449 proposal, implemented
after live verification of both drift claims). Scans the canonical registries
for artifact URLs; classifies OK / PARTIAL-OK (PK payload, pin compare needs
full fetch) / PAGE-OK (package page, HTML by design) / DRIFT / DEAD.

## Live verification of the coder claims (2026-11-02, this sandbox)

| claim | live test | verdict |
|---|---|---|
| #449 Telegram pin unfetchable — live link serves HTML | `curl -sL https://telegram.org/dl/android` → **1,256,261-byte HTML document** (sha16 `2e7a7ea76336580e`, differs per fetch — matches Coder-2's two differing fetches) | **CONFIRMED** |
| #458 Tiny Music Player v1 dead | `curl -sL .../com.martinmimigames.tinymusicplayer_1.apk` → **HTTP 404, 12,950-byte HTML page** — byte-exact match to #458 | **CONFIRMED** |

## Checker verdicts (this run)

- 7 × PARTIAL-OK — F-Droid APK artifact URLs serve real PK payloads
  (full-file pin compare is a follow-up; first-256KB sha recorded in JSON).
- 87 × PAGE-OK — package pages (HTML by design, not artifacts).
- 1 × DEAD — canonical registry `titles[146].source`
  `https://telegram.org/dl/android/apk (official CDN)`: live link is DRIFT
  (serves HTML; the checker's InvalidURL is the annotation suffix — the real
  URL was verified drifted by the manual fetch above).

## Law adopted (from #449, tested)

Registry entries with a LIVE fetch link must gain `frozen_url` +
`frozen_sha256` (perma-hosted copy); reproduction only fetches frozen
artifacts. The Telegram 12.10.1 re-pin (73,028,xxx-byte true APK on a frozen
mirror) is a follow-up — no mirror URL is invented here; the pin sha256
`f5e1192725772960cc94b83e54ffd8939f876b2b6e5f21d4a8537eb6fcba50e6` stays the
authority. Re-run: `python3 scripts/registry_link_check.py`.
