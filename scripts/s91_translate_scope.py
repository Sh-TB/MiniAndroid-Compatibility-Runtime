#!/usr/bin/env python3
"""S91: translate remaining authored Persian to English in my scope.
Policy: authored prose/comments/strings -> English.
Kept (allowlisted): RTL test vectors, fixture generators, upstream third-party,
captured evidence JSON. Each replacement asserted by count.
"""
import json, re, sys

BASE = "/home/z/my-project/"
fails = []

def sub_file(path, pairs, regex=False):
    p = BASE + path
    try:
        s = open(p, encoding="utf-8").read()
    except FileNotFoundError:
        fails.append((path, "MISSING")); return
    orig = s
    for old, new in pairs:
        if regex:
            s2, n = re.subn(old, new, s, flags=re.DOTALL)
        else:
            n = s.count(old); s2 = s.replace(old, new)
        if n == 0:
            fails.append((path, f"NO MATCH: {old[:60]!r}"))
        s = s2
    if s != orig:
        open(p, "w", encoding="utf-8").write(s)
        print(f"UPDATED {path}")

def has_fa(s):
    return any(0x0600 <= ord(c) <= 0x06FF or 0x0750 <= ord(c) <= 0x077F
               or 0xFB50 <= ord(c) <= 0xFDFF or 0xFE70 <= ord(c) <= 0xFEFF for c in s)

# ---------- 1. canonical registry (json-aware, preserve 1-space indent) ----------
reg_path = BASE + "docs/evidence/canonical/registry.json"
r = json.load(open(reg_path, encoding="utf-8"))
changed = 0
for t in r["titles"]:
    if t["title"] == "TicTacToe Deluxe (دوز)":
        t["title"] = "TicTacToe Deluxe"; changed += 1
    if t["title"] == "MiniCraft (خانه سازی)":
        t["title"] = "MiniCraft (House Builder)"; changed += 1
    if "خانه سازی" in t.get("notes", ""):
        t["notes"] = t["notes"].replace("(خانه سازی)", ""); changed += 1
json.dump(r, open(reg_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
open(reg_path, "a", encoding="utf-8").write("\n") if not open(reg_path, encoding="utf-8").read().endswith("\n") else None
print(f"registry titles updated: {changed}")

# ---------- 2. global name replacements ----------
GLOBAL = [
    ("TicTacToe Deluxe (دوز)", "TicTacToe Deluxe"),
    ("MiniCraft (خانه سازی)", "MiniCraft (House Builder)"),
    ("Dooz (دوز, F-Droid)", "Dooz (TicTacToe, F-Droid)"),
    ("2048 (بازی جمع ۲ عدد)", "2048 (number-merge)"),
    ("Snake Deluxe (بازی مار)", "Snake Deluxe"),
    ("Snake Deluxe (مار)", "Snake Deluxe"),
    ("snake (مار) lifecycle", "snake lifecycle"),
    ("house-building game (خانه سازی)", "house-building game"),
    ("خانه سازی companion", "house-building companion"),
    ("Snake/2048/خانه سازی", "Snake/2048/MiniCraft"),
]
for f in ["README.md", "docs/ACHIEVEMENTS.md", "docs/achievements/GAMES_WITH_GIFS.md",
          "worklog.md", "scripts/s83_evidence_package.py", "scripts/s84_canonicalize.py",
          "scripts/s84_emit_readme.py", "scripts/s86_emit_impact.py",
          "scripts/s86_minicraft_canonical.py", "scripts/s83_snake_proof.sh"]:
    sub_file(f, GLOBAL)

# ---------- 3. per-file specifics ----------
sub_file("README.md", [
    ("TicTacToe Deluxe (دوز)", "TicTacToe Deluxe"),
])
sub_file("worklog.md", [
    ('user: "نه یک حمله چندین حمله متفاوت"', 'user: "multiple different attacks, not just one"'),
    ('"تمامیپوش"', '"publish all pushes"'),
    ("joined سلام vs spaced س ل ا م", "joined-form Persian word vs the same word's spaced letters"),
    ('Task: "ادامه"', 'Task: "continue"'),
    ("complete دوز (TicTacToe) + مار (Snake)", "complete TicTacToe + Snake"),
    ("دوز COMPLETE (real captures)", "TicTacToe COMPLETE (real captures)"),
    ("مار re-proven", "Snake re-proven"),
    ("دوز/مار complete", "TicTacToe/Snake complete"),
    ("دوز re-review", "TicTacToe re-review"),
    ('user: "فقط از دو رنگ دارن نمایش داده میشن"', 'user: "they only show two colors"'),
    ("Flashlight (نورافکن, user)", "Flashlight (user request)"),
])
sub_file("scripts/s83b_github_update.py", [
    ('user: "گیت هاب هر بازی و برنامه رو هم به روز رسانی\nبکن"', 'user: "update GitHub for every game and app"'),
])
sub_file("scripts/s85_game_sweep.py", [
    ('user mandate: "بررسی کلی سایر بازی ها"', 'user mandate: "general review of the other games"'),
])
sub_file("scripts/s85_rescue.py", [
    ('"اونای هم که ناقص موندن رو کامل بکن"', '"complete the ones that remained incomplete"'),
])
sub_file("scripts/s86_emit_impact.py", [
    ("از لول ۰ تا آخرین لول ۵ تا از هر کدام رو انتخاب ", "From each level 0 to the latest level, pick up to 5 of each "),
    ("بکن و نشون بده اینقدر پیشرفت چقدر تاثیر داشته", "and show how much impact the progress has had"),
])
sub_file("scripts/s86_level_impact.py", [
    (r'از لول ۰.*?داشته', "From each, level 0 to the latest level, pick up to 5 and show how much impact the progress has had"),
], regex=True)
sub_file("scripts/s79_snake_gif.py", [
    ('User directive: "یک گیف از گیم پلی اسنک برای من ... ببینم تونستی بازی بکنی"',
     'User directive: "make me a GIF of snake gameplay ... so I can see you can actually play"'),
])
sub_file("games/minicraft/java/com/miniandroid/minicraft/CraftWorldView.java", [
    # handled via GLOBAL? no: 'خانه سازی companion' rule is in GLOBAL but file not in GLOBAL list
])
sub_file("miniandroid/tests/fixtures/balltap_golden/src/com/miniandroid/balltap/MainActivity.java", [
    ('S51 finalization "بازی دو بعدی\n * خیلی ساده که توپ دارد" (very simple 2D game with a ball)',
     'S51 finalization (very simple 2D game with a ball)'),
])
sub_file("miniandroid/tests/fixtures/crossword_golden/src/com/miniandroid/crossword/MainActivity.java", [
    ('S51 finalization "بازی جدول"', 'S51 finalization "board game"'),
])
sub_file("miniandroid/tests/fixtures/crossword_golden/validate_crossword_golden.sh", [
    ('S51 finalization "بازی جدول" golden gate', 'S51 finalization "board game" golden gate'),
])
sub_file("miniandroid/tests/fixtures/wordpredict_golden/src/com/miniandroid/wordpredict/MainActivity.java", [
    ('"پیش‌بینی کلمات" (word prediction)', '"word prediction"'),
])
sub_file("miniandroid/tests/fixtures/wordpredict_golden/validate_wordpredict_golden.sh", [
    ('S51 finalization "پیش‌بینی کلمات" gate', 'S51 finalization "word prediction" gate'),
])
sub_file("miniandroid/tests/fixtures/minesweep_golden/src/com/miniandroid/minesweep/MainActivity.java", [
    ('S51 finalization "بازی بمب‌یاب\n * شبیه ویندوز XP" (mine-finding game in the Windows XP style)',
     'S51 finalization (mine-finding game in the Windows XP style)'),
])
sub_file("miniandroid/tests/fixtures/minesweep_golden/validate_minesweep_golden.sh", [
    ('S51 finalization "بازی بمب‌یاب XP-style" gate', 'S51 finalization XP-style mine-finder gate'),
])
sub_file("miniandroid/tests/fixtures/balltap_golden/validate_balltap_golden.sh", [
    ('S51 finalization "بازی توپ دو بعدی ساده" gate', 'S51 finalization simple-2D-ball-game gate'),
])
sub_file("miniandroid/tests/fixtures/s66_canvas_probe/src/com/miniandroid/canvasprobe/MainActivity.java", [
    ('T11 Persian text "دور" at (100,1500)', 'T11 Persian word (dour, "round") at (100,1500)'),
])
# CraftWorldView via its own call (not in GLOBAL list)
sub_file("games/minicraft/java/com/miniandroid/minicraft/CraftWorldView.java",
         [("خانه سازی companion", "house-building companion")])

# ---------- 4. verification ----------
REMAIN_ALLOW = [
    "upstream/",                                     # third-party source snapshots
    "scripts/foundation/make_fixtures.sh",           # fixture generators (RTL test vectors)
    "scripts/foundation/make_fixtures_wave2.sh",
    "miniandroid/scripts/exp101_persian_rtl_proof.cpp",
    "miniandroid/scripts/u007_font_proof.cpp",
    "miniandroid/scripts/exp099_wsc2_text_pipeline.cpp",
    "miniandroid/scripts/u007_status_gen.py",
    "miniandroid/tools/exp116_font_shaping_prototype.cpp",
    "miniandroid/tools/campaign010/uc010_sbidiff.c",
    "miniandroid/tests/fixtures_foundation/",        # RTL test fixtures
    "docs/evidence/foundation/determinism/",         # captured evidence
    "scripts/s91_english_audit.py",                  # audit tool itself
]
import subprocess
tracked = subprocess.run(["git", "ls-files"], capture_output=True, text=True, cwd=BASE).stdout.splitlines()
remaining = []
for f in tracked:
    if f.endswith((".png", ".jpg", ".gif", ".apk", ".jar", ".zip", ".so", ".bin", ".dex", ".webp", ".ico", ".ttf")):
        continue
    if any(f.startswith(a) or f == a for a in REMAIN_ALLOW):
        continue
    try:
        for ln, line in enumerate(open(BASE + f, encoding="utf-8"), 1):
            if has_fa(line):
                remaining.append(f"{f}:{ln}: {line.strip()[:100]}")
    except (UnicodeDecodeError, OSError):
        pass

print("\n=== NON-ALLOWLISTED PERSIAN REMAINING ===")
for x in remaining[:60]: print(" ", x)
print("COUNT:", len(remaining))
print("\n=== FAILED REPLACEMENTS ===")
for x in fails: print(" ", x)
sys.exit(0 if not remaining and not fails else 1)
