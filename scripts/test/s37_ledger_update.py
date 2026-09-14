#!/usr/bin/env python3
"""S37 ledger update — compress batch screenshots to 540x960 medium-quality
PNG, copy into miniandroid/docs/evidence/apps_ledger/, and emit a ready-to-
paste markdown table block with SHA-256 (screenshot + APK) for the
APPS_EXECUTION_LEDGER.md. Zero-APK law: only names/hashes/links.
"""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

WORK = Path("/tmp/s37_runs")
LEDGER_IMG_DIR = Path("/home/z/my-project/miniandroid/docs/evidence/apps_ledger")
OUT = Path("/tmp/s37_ledger_rows.md")

NAMES = {
    "dooz_vc23": ("io.github.yamin8000.dooz", "1.0.23 (vc23)", "https://f-droid.org/repo/io.github.yamin8000.dooz_23.apk", "Dooz newer variant"),
    "bouncycastle": ("com.inspiredandroid.braincup", "3.4.0 (vc158)", "https://f-droid.org/repo/com.inspiredandroid.braincup_158.apk", "puzzle/word games collection"),
    "solitaire": ("de.tobiasbielefeld.solitaire", "3.12 (vc69)", "https://f-droid.org/repo/de.tobiasbielefeld.solitaire_69.apk", "open-source Solitaire"),
    "secuso_sudoku": ("org.secuso.privacyfriendlysudoku", "3.2.4 (vc19)", "https://f-droid.org/repo/org.secuso.privacyfriendlysudoku_19.apk", "Sudoku"),
    "bouncy": ("com.dozingcatsoftware.bouncy", "1.14.0 (vc39)", "https://f-droid.org/repo/com.dozingcatsoftware.bouncy_39.apk", "physics pinball"),
    "secuso_memory": ("org.secuso.privacyfriendlymemory", "1.1.1 (vc8)", "https://f-droid.org/repo/org.secuso.privacyfriendlymemory_8.apk", "memory game"),
    "minesweep_johnathan": ("io.github.johnathan.minesweeper", None, "https://f-droid.org/repo/io.github.johnathan.minesweeper_6.apk", "minesweeper (tiny)"),
    "game2048": ("org.andstatus.game2048", None, "https://f-droid.org/repo/org.andstatus.game2048_47.apk", "2048"),
    "diceoverflow": ("eu.veldsoft.dice.overflow", None, "https://f-droid.org/repo/eu.veldsoft.dice.overflow_2.apk", "dice board game"),
    "wordgame_nian": ("com.wordgame.nian", None, "https://f-droid.org/repo/com.wordgame.nian_11.apk", "wordle-like"),
    "secuso_yahtzee": ("org.secuso.privacyfriendlyyahtzeedicer", None, "https://f-droid.org/repo/org.secuso.privacyfriendlyyahtzeedicer_100.apk", "yahtzee dice"),
    "minesweep_joeld": ("com.joeld.minesweeper", None, "https://f-droid.org/repo/com.joeld.minesweeper_7.apk", "minesweeper"),
    "edgeroll": ("edge.roll", None, "https://f-droid.org/repo/edge.roll_11.apk", "dice/roll game"),
    "sidhant_puzzle": ("com.sidhant.puzzle", None, "https://f-droid.org/repo/com.sidhant.puzzle_293.apk", "puzzle"),
    "thesuncat_sudoku": ("com.thesuncat.sudoku", None, "https://f-droid.org/repo/com.thesuncat.sudoku_4.apk", "sudoku"),
    "tictactoe_legacy": ("com.emmanuelmess.tictactoe (corpus copy — DUPLICATE of ledger row 3)", "v3 (vc3)", "https://f-droid.org/repo/com.emmanuelmess.tictactoe_3.apk", "legacy tictactoe model (dup)"),
    "tictactoe_classic": ("com.palahsu.ttt", None, "legacy corpus cache (TicTacToe Classic by palahsu)", "classic tictactoe — REAL RENDER"),
    "dooz_gvariant": ("io.github.yamin8000.dooz (corpus copy — DUPLICATE of ledger row 12)", "1.0.18 (vc18)", "https://f-droid.org/repo/io.github.yamin8000.dooz_18.apk", "dooz G-variant (dup)"),
    "dooz_variant": ("io.github.yamin8000.dooz (corpus copy — DUPLICATE of ledger row 12)", "1.0.18 (vc18)", "https://f-droid.org/repo/io.github.yamin8000.dooz_18.apk", "dooz variant (dup)"),
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    LEDGER_IMG_DIR.mkdir(parents=True, exist_ok=True)
    summary = json.loads((WORK / "s37_results_summary.json").read_text())
    lines = []
    for name, r in summary.items():
        pkg, ver, url, desc = NAMES[name]
        apk_sha = r.get("apk_sha256", "?")
        status = r.get("status")
        secs = r.get("seconds")
        shot_sha = r.get("screenshot_sha256")
        img_md = ""
        if r.get("screenshot"):
            src = WORK / name / "screenshot.png"
            orig_kb = src.stat().st_size // 1024
            dst = LEDGER_IMG_DIR / f"s37_{name}.png"
            subprocess.run(["python3", "-c", f"""
from PIL import Image
im = Image.open("{src}").convert("RGB").resize((540, 960), Image.LANCZOS)
im = im.quantize(colors=128, method=2).convert("P")
im.save("{dst}", optimize=True)
"""], check=True)
            new_kb = dst.stat().st_size // 1024
            shot_sha = sha256(dst)
            img_md = f"![{name}](apps_ledger/s37_{name}.png)"
            lines.append(f"### S37 {name} — {desc}")
            lines.append(f"\n{img_md}\n")
            lines.append("| Field | Value |")
            lines.append("|---|---|")
            lines.append(f"| APK | `{pkg}` {ver or '(vc in filename)'} — {desc} |")
            lines.append(f"| APK SHA-256 | `{apk_sha}` |")
            lines.append(f"| Download | <{url}> |")
            lines.append(f"| Status | {status} in {secs}s |")
            lines.append(f"| Screenshot SHA-256 | `{shot_sha}` (540×960, {orig_kb}KB→{new_kb}KB) |")
            lines.append("")
        else:
            lines.append(f"### S37 {name} — {desc}")
            lines.append("| Field | Value |")
            lines.append("|---|---|")
            lines.append(f"| APK | `{pkg}` {ver or '(vc in filename)'} — {desc} |")
            lines.append(f"| APK SHA-256 | `{apk_sha}` |")
            lines.append(f"| Download | <{url}> |")
            lines.append(f"| Status | {status} in {secs}s — no screenshot claim |")
            lines.append("")
    OUT.write_text("\n".join(lines))
    print(f"wrote {OUT} ({len(lines)} lines)")


if __name__ == "__main__":
    main()
