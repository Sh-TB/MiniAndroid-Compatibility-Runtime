#!/bin/bash
# Issue #609 finalizer: wait for chain, receipt, commit, GitHub comment.
set -u
LOG=/tmp/zcode-bash-acI02i/sess_d1d98a24-155e-4599-b761-7fef8b377dc0/call_3cda5ef0e628492fb201c5a0-stdout.log
# 1. wait for the chain to complete (max ~12 min)
for i in $(seq 1 48); do
  grep -q "CHAIN DONE" "$LOG" 2>/dev/null && break
  sleep 15
done
echo "=== CHAIN TAIL ==="
tail -30 "$LOG" 2>/dev/null
# 2. receipt + report + evidence copy
python3 /home/z/my-project/scripts/blk609_receipt.py 2>&1 | tail -8
# 3. also copy raw evidence into download
EV=/home/z/my-project/evidence/issue609_blockinger
mkdir -p /home/z/my-project/download/issue609_blockinger_evidence
for f in menu/screenshot.png dialog/screenshot.png game3/screenshot.png game4/screenshot.png game4/run.log menu/run.log game4/view_tree.json game4/frames/manifest.json; do
  [ -f "$EV/$f" ] && cp "$EV/$f" "/home/z/my-project/download/issue609_blockinger_evidence/$(echo $f | tr '/' '_')" 2>/dev/null
done
# game4 frame PNGs (first 6) for the render gallery
if [ -d "$EV/game4/frames" ]; then
  n=0; for f in $(ls "$EV/game4/frames"/*.png 2>/dev/null | head -6); do
    n=$((n+1)); cp "$f" "/home/z/my-project/download/issue609_blockinger_evidence/game4_frame_$n.png" 2>/dev/null
  done
fi
ls /home/z/my-project/download/issue609_blockinger_evidence/ | wc -l
# 4. git commit
cd /home/z/my-project
git add -A miniandroid/src miniandroid/make_out_b1.txt miniandroid/make_err_b1.txt \
  miniandroid/make_out_b2.txt miniandroid/make_err_b2.txt miniandroid/make_out_b3.txt \
  miniandroid/make_err_b3.txt miniandroid/make_out_b4.txt miniandroid/make_err_b4.txt \
  miniandroid/make_out_b5.txt miniandroid/make_err_b5.txt \
  scripts/blk609_run.sh scripts/blk609_chain.sh scripts/blk609_receipt.py \
  upstream/corpus/org.blockinger.game download/issue609_blockinger_receipt.md \
  download/issue609_blockinger_report.md 2>/dev/null
git commit -q -m "ISSUE-609 WAVE-1 — Blockinger 1.8.2 gameplay chain OPEN: four generic laws — (1) F-SDF-1 java.text.SimpleDateFormat (ctor pattern store + OpenJDK pattern-runner format law; GameState.<init> pc=62 startsWith-on-null NPE chain gone), (2) F-CAL-CTOR Calendar/GregorianCalendar <init> seeds millis+zone (getInstance state law), (3) F-INTX-1 Intent.putExtras(Bundle) putAll-onto-intent law (GameActivity.onCreate b.getInt(level) NPE gone), (4) F-PREF-REF setDefaultValues defaultValue @resource-reference resolution (pref_fpslimittext was the raw id 2131361851 → fpslimit=2.1e9 → sleepless loop → 100M F084 halt in Display.drawPreview; now resolves to 35). PROVEN on the pinned APK 0c51e225…: real menu render; New Game tap → onClickStart → level dialog (Cancel/Start pixel-verified); start() → Intent+Bundle → GameActivity.onCreate(2668 insns) → surfaceCreated (F-NEW-164, post-onCreate lazy law) → Thread self-run (R-NEW-345) → WorkThread REAL DEX run() → 24x unlockCanvasAndPost posted=YES → game screen renders (board grid, settled blocks, active piece, Pause, < > rotate soft/hard-drop controls). Evidence: evidence/issue609_blockinger/ + download/issue609_blockinger_evidence/. Remaining R090: controls battery, line-clear/score, game-over→SQLite, x3 runs." 2>&1 | tail -2
# 5. GitHub comment
TOKEN=$(git config --list 2>/dev/null | grep -o 'github_pat_[A-Za-z0-9_]*' | head -1)
python3 - <<'EOF' > /tmp/gh_comment.json
import json
body = """## Blockinger RECEIPT — ISSUE-609 WAVE-1: gameplay chain OPEN + 4 generic laws (base: fa5f97cf tree + this session)

**APK:** org.blockinger.game_14 re-verified `0c51e225…` ✓ (pinned, untouched)
**Binary:** fresh `make -j1` build, sha16 in receipt. **All laws generic — zero app-name branches.**

### First-divergence ladder (each proven by real-APK trace, then closed)
1. **SimpleDateFormat.format stub → null** → `GameState.<init>` pc=62 `String.startsWith on null` NPE → onCreate unwound → sound/host null chain (onResume + surfaceCreated NPEs). **Closed: F-SDF-1** — ctor pattern store + `format(Date|Calendar|Long)` OpenJDK pattern-runner (run-length = pad width, quoted literals, host-zone law shared with `Calendar.get`).
2. **`Intent.putExtras` unhandled** → extras empty → `getExtras()` lawfully null → `GameActivity.onCreate` pc=72 `b.getInt("level")` NPE. **Closed: F-INTX-1** — putAll-onto-intent law feeding the existing F-NEW-642 getExtras.
3. **`Calendar/GregorianCalendar.<init>` unseeded** (no `__cal_millis__`) — **Closed: F-CAL-CTOR** (getInstance state law: millis=now + host zone).
4. **setDefaultValues stored `@string/…` refs as raw ids** → `pref_fpslimittext="2131361851"` → `fpslimit=2.1e9` → `lastDelay→0` → sleepless game loop → 100M-instruction F084 halt inside `Display.drawPreview`. **Closed: F-PREF-REF** — `@string/`/`@integer/` defaultValue attributes now persist the REFERENCED VALUE (`35`).

### Chain proven this session (evidence in `evidence/issue609_blockinger/`)
- Menu: real render (Highscores / nickname EditText / Resume + New Game buttons) — SUCCESS, 0 errors.
- New Game tap (816,1815)@f2 → `onClickStart` (android:onClick binding) → seek_bar_dialog inflate → `[DIALOG] show() decor_root=700000` — **dialog renders with Cancel/Start (pixel-verified)**.
- Start tap (757,1167)@f4 → `MainActivity.start()` → Intent+Bundle putInt(mode/level)/putString → `startActivityForResult` → `GameActivity.onCreate` **2668 instructions** → setContentView(activity_game) → GameState.newInstance(level).
- `[F-NEW-164] surfaceCreated dispatched view=77 callback=BlockBoardView` — delivered AFTER onCreate per the lazy render-traversal law (issue §3-B contract held).
- `[THREAD-START] … cls=WorkThread (self-run law) → REAL DEX run() executed` (R-NEW-345) — the app's own game loop.
- `[F-NEW-164] unlockCanvasAndPost … posted=YES` ×24 — repeated Canvas posts; replayed into the composed frame.
- **Game screen render (pixel-verified screenshot):** board grid + settled blocks + active piece + Pause button + the six control buttons (< > ↺ ↻ soft-drop hard-drop) + HUD region.

### Labels
- IMPLEMENTED/TESTED: menu, dialog flow, launch chain, surface lifecycle, thread self-run, canvas post/replay, game-screen render.
- OBSERVED: gameplay loop cycling with FPS-limit sleep law exercised (resolved prefs).
- PARTIAL/PENDING (R090 continues): per-action control battery with GameState deltas, line-clear+score through real logic, game-over→DefeatDialogFragment→onActivityResult→SQLite record, pause/resume + surface recreate, x3 clean runs. The F084 run (game3) predates F-PREF-REF; game4 (post-fix) logs are the current baseline.

**No hardcoded pixels, no replacement game, no APK patch, no app-name branch.** First-divergence protocol honored: every step above cites class.method/PC + expected-vs-actual.
"""
print(json.dumps({"body": body}))
EOF
curl -s -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d @/tmp/gh_comment.json \
  "https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/609/comments" | python3 -c "import json,sys; d=json.load(sys.stdin); print('COMMENT:', d.get('html_url', d.get('message','ERR')))" 2>/dev/null
echo "=== FINALIZER DONE ==="
