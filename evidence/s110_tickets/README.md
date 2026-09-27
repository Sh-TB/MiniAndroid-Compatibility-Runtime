# S110 — Ticket evidence pack (HTML5 / native games / Telegram)

Fresh runs at the S109 HEAD (2026-09-27, container Linux x86_64, real-dalvik mode,
standard 8 frames x 300 ms protocol + `--max-seconds` wall budgets shown per run).

## HTML5 / WebView family

- `html5_breakout/` — **me.lecaro.breakout 29826425** (F-Droid, GAME-070 / issue #94 family).
  Status SUCCESS, 0 errors. WebView node renders the game document: header
  `Breakout 71 ☰ menu`, full-screen dark game theme (~99.9% non-white pixels,
  2,071,677 / 2,073,600). `reference_froid.png` = official F-Droid screenshot.
  Screenshot SHA-16: `5bcd77b8b5e194de`.
- Historical web/HTML5 GIF evidence (already on origin): `docs/evidence/canonical/com.miniandroid.browser.zai.gif`
  (real TLS website load), `com.miniandroid.browser.gif`.

## Native games

- `native_games/ballbreak/` — **de.georgsieber.ballbreak 1.0.10**. SUCCESS, 0 errors.
  Screenshot SHA-16 `fe797c19...` — BYTE-IDENTICAL to the S107/S108 3-run anchor
  (zero regressions across three root waves). `--click-test` dispatched real clicks:
  GameView listener (GameView$1) + XML onClick buttons (`onClickWeb`, `onClickHighscores`) — all DISPATCHED.
- `native_games/dooz/` — **io.github.yamin8000.dooz 2.3** (Kotlin Compose). SUCCESS,
  6 handled errors, shot SHA-16 `a2ba4a49...` = the S107 first-Compose-pixels surface, stable.
- Canonical native-gameplay GIFs (on origin): bouncy / bobball / hotdeath / fish.rings /
  tictactoe / g2048 / tetris / minicraft / snakeneon — `docs/evidence/canonical/*.gif`.

## Telegram

- `../s109_telegram/run1/` — forkgram 12.10.8.0 (org.forkgram.classic), 540 s budget.
  PARTIAL SUCCESS, 6 residual errors. 163,212 real Dalvik instructions,
  10,818 heap objects, main entry LaunchActivity.onCreate. Shot SHA-16 `59fdbfcd...`
  (Telegram themed window 240,240,240), deterministic.
- `../s109_telegram/run2/` — 300 s budget with full console log (`final_run.log`):
  the REAL LOGIN UI view tree — ScrollView -> `he1$a` (login layout) ->
  `he1$d` **"StartMessaging"** button (1080x48 @ y=1656), ViewPager, TextureView 200x150,
  LinearLayout headers, bottom-sheet `yj$v` family — 30+ measured Telegram view nodes.
- S108 baseline evidence: `../s108_telegram/` (32->7 error wave, 8-node tree, real cache4.db).

## Zero-regression gates (this HEAD)

| title | status | errors | shot SHA-16 | anchor |
|---|---|---|---|---|
| ballbreak | SUCCESS | 0 | `fe797c19ba1920ed` | S107/S108 byte-identical |
| dooz | SUCCESS | 6 | `a2ba4a4942152926` | S107 final Compose surface |
| forkgram | PARTIAL SUCCESS | 6 | `59fdbfcd60b86a23` | S108 themed window, deterministic |
