#!/usr/bin/env python3
"""Append the S37 corpus wave-3 section to APPS_EXECUTION_LEDGER.md with
full SHA-256 hashes for every screenshot and APK (zero-APK law)."""
import hashlib
from pathlib import Path

IMG = Path("/home/z/my-project/miniandroid/docs/evidence/apps_ledger")
LEDGER = Path("/home/z/my-project/miniandroid/docs/evidence/APPS_EXECUTION_LEDGER.md")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


ROWS = [
    # (img, apk_name, ver, apk_sha, url, grade, note)
    ("bouncy", "com.dozingcatsoftware.bouncy", "1.14.0 (vc39)",
     "d1cd7e40e84067aa0d663534eb7ebe97d461fcfedeb32bccbe9ac4f3f3d477a0",
     "https://f-droid.org/repo/com.dozingcatsoftware.bouncy_39.apk",
     "✅ FULL-RENDER",
     "wave-2 row 26 executed — **pinball 'Select Table' menu fully rendered**: title, 'Unlimited Balls', Start Game / High scores / Help / Preferences / Quit buttons, purple table frame with 2 corner ImageViews; **real game thread executes as bytecode**: FieldDriver.threadMain + GL20Renderer.doDraw live (900k+ instructions); click-test reaches quiescence-never (game loop never idles — engine alive); honest gap: corner ImageViews garbled debug glyphs"),
    ("tictactoe_classic", "com.palahsu.ttt", "(TicTacToe Classic)",
     "752852c94c9807883d38c0b74ab160809999897acda0cbc45f4f49f84e0a1b9a",
     "legacy corpus cache (identity verified via binary manifest)",
     "✅ FULL-RENDER",
     "**old/simpler tic-tac-toe model rendered**: 'Player 1: 0 / Player 2: 0' score card, blue play area, 'reset' button — SUCCESS rc=0 in 0.4s; honest gap: score card hugs left edge (layout-metric family), board grid not visible in this frame"),
    ("edgeroll", "edge.roll", "(vc11)",
     "799c651be1333741dae66c43bf97774b273b0b4e9439f5ff37f26e153159f640",
     "https://f-droid.org/repo/edge.roll_11.apk",
     "🟡 PARTIAL",
     "game canvas painted dark + real 'PAUSED / tap anywhere to resume' overlay rendered; honest gap: overlay drawn in top-left quadrant instead of centered (layout-metric family)"),
    ("dooz_vc23", "io.github.yamin8000.dooz", "1.0.23 (vc23) — NEWER Dooz variant",
     "299eab21ac8b3c6192edbd887966554fef84ad026d269b9067310215201b362b",
     "https://f-droid.org/repo/io.github.yamin8000.dooz_23.apk",
     "🔴 PLACEHOLDER",
     "wave-2 row 22 executed — **R-NEW-334 residual wall GONE on v23 too**: real measure+layout lifecycle dispatches (Lho; rect 0,0→1080×1920, LIFEWIN-CLOSE yes), framebuffer 100% painted; ISE escapes at MainActivity.onCreate compose-transition boundary; screen = placeholder family"),
    ("bouncycastle", "com.inspiredandroid.braincup", "3.4.0 (vc158)",
     "27a5b3a40dd21c2a4c0c9978875bbf343dbf293b80d41497b9e3b4c37a1a5b80",
     "https://f-droid.org/repo/com.inspiredandroid.braincup_158.apk",
     "🔴 PLACEHOLDER",
     "wave-2 row 23 executed — real onLayout dispatch (Lx20; 1080×1920), fb painted, placeholder frame; rc=1 ISE boundary"),
    ("solitaire", "de.tobiasbielefeld.solitaire", "3.12 (vc69)",
     "6b257d05f222d575639a8b411d90d7d3d39397ec737ee128cea365afc200fa9d",
     "https://f-droid.org/repo/de.tobiasbielefeld.solitaire_69.apk",
     "🔴 PLACEHOLDER",
     "wave-2 row 24 executed — GameSelector.onResume dispatched via real DEX (82 instructions); ComposeView NOT in class index (attach gap) → early boundary"),
    ("minesweep_johnathan", "io.github.johnathan.minesweeper", "(vc6)",
     "3b52a2fd21c4b4184eed1a1d4a9944e89bb9e7f99bf37329f03bd5eca962942e",
     "https://f-droid.org/repo/io.github.johnathan.minesweeper_6.apk",
     "🔴 PLACEHOLDER",
     "shared empty frame (same placeholder family)"),
    ("game2048", "org.andstatus.game2048", "(vc47)",
     "2d6707624623fe8857da271dcc19511ab52472ce1fee6ac23bc7f2ecf2e7eea9",
     "https://f-droid.org/repo/org.andstatus.game2048_47.apk",
     "🔴 PLACEHOLDER",
     "shared empty frame"),
    ("diceoverflow", "eu.veldsoft.dice.overflow", "(vc2)",
     "2d03b6450b7629e3e6af7540bee2f4fed26d2737b5c5daeca89d87f0ad58ef97",
     "https://f-droid.org/repo/eu.veldsoft.dice.overflow_2.apk",
     "⚫ NO-VISUAL",
     "Status: SUCCESS rc=0 in 2.1s — process clean, frame white (game draws via custom draw path not yet dispatched); no visual claim"),
    ("secuso_yahtzee", "org.secuso.privacyfriendlyyahtzeedicer", "(vc100)",
     "9926a19f9efa7c57c653b508b2630da3228443f3cdd1c8eb969db5550e55d548",
     "https://f-droid.org/repo/org.secuso.privacyfriendlyyahtzeedicer_100.apk",
     "⚫ NO-VISUAL",
     "rc=1 PARTIAL — black status bar + white frame only"),
    ("sidhant_puzzle", "com.sidhant.puzzle", "(vc293)",
     "ef82df814f44bbaf401fe8422da3b662b8a0f94fbc30deaa5135f9b813bd7fa9",
     "https://f-droid.org/repo/com.sidhant.puzzle_293.apk",
     "⚫ NO-VISUAL",
     "Status: SUCCESS rc=0 — white frame + status bar; no visual claim"),
    ("thesuncat_sudoku", "com.thesuncat.sudoku", "(vc4)",
     "863927be2d6a4d2dbb61587e8a876bad73e523ed237281258a199401c116036a",
     "https://f-droid.org/repo/com.thesuncat.sudoku_4.apk",
     "⚫ NO-VISUAL",
     "Status: SUCCESS rc=0 — white frame + status bar; no visual claim"),
    ("tictactoe_legacy", "com.emmanuelmess.tictactoe", "v3 (vc3) — corpus duplicate of ledger row 3",
     "760fe5acf7b394354bf02b7b3484c3eb442b491c1fa4325603ad3250f0dfa394",
     "https://f-droid.org/repo/com.emmanuelmess.tictactoe_3.apk",
     "✅ FULL-RENDER (re-verified)",
     "the cached 'older model' copy is byte-identical (same SHA) to ledger row 3's APK — re-ran at S37 HEAD: PARTIAL-status console but identical X/O board render family; row 3 golden remains the reference"),
    ("dooz_gvariant", "io.github.yamin8000.dooz", "1.0.18 (vc18) — corpus duplicate of ledger row 12",
     "d81292cd346dcb23b04488bca400ca95af0f6eaa4aefefd31f847fe535cbdc17",
     "https://f-droid.org/repo/io.github.yamin8000.dooz_18.apk",
     "🔴 PLACEHOLDER (progress evidence)",
     "cached 'G-variant' copy is byte-identical (same SHA) to ledger row 12; at S37 HEAD it now runs 409.6s to Status: PARTIAL (was the R-NEW-334 placeholder wall; post-F-101 it paints + lays out; AIOOBE R-NEW-335 evidence captured in the long-budget probe run)"),
]


def main():
    txt = LEDGER.read_text()
    lines = [
        "",
        "---",
        "",
        "## S37 corpus wave 3 (2026-09-14) — 19 runs executed: 5 SUCCESS, 8 PARTIAL-IMG, 5 budget-timeout; 3 NEW real renders",
        "",
        "Headline: **Bouncy (physics pinball) FULL-RENDER with its real game thread (FieldDriver/GL20Renderer) executing as bytecode**,",
        "**TicTacToe Classic (palahsu) FULL-RENDER** — the old/simpler tic-tac-toe model family — and **edge.roll PARTIAL with real PAUSED overlay**.",
        "Dooz v23 (newer variant) executed: real measure+layout lifecycle now dispatches (R-NEW-334 residual gone); placeholder family remains",
        "(R-NEW-335 frontier — scatter-set metadata corruption live-captured, see root_registry.json).",
        "All images 540×960 medium-quality compressed from 1080×1920 originals (originals under /tmp/s37_runs, gitignored).",
        "Zero-APK law: names, SHA-256 hashes, F-Droid links only.",
        "",
    ]
    for img, name, ver, apk_sha, url, grade, note in ROWS:
        p = IMG / f"s37_{img}.png"
        ssha = sha(p) if p.exists() else "n/a"
        lines.append(f"### S37: {name} {ver} — {grade}")
        lines.append("")
        if p.exists():
            lines.append(f"![{img}](apps_ledger/s37_{img}.png)")
            lines.append("")
        lines.append("| Field | Value |")
        lines.append("|---|---|")
        lines.append(f"| APK | `{name}` — {ver} |")
        lines.append(f"| APK SHA-256 | `{apk_sha}` |")
        lines.append(f"| Download | <{url}> |")
        lines.append(f"| Screenshot SHA-256 | `{ssha}` |")
        lines.append(f"| Evidence | {note} |")
        lines.append("")
    lines += [
        "### S37 budget-timeout family (⚫ NO-VISUAL — honest, same law as rows 20–21)",
        "",
        "| App | Version | APK SHA-256 | Download | Stage |",
        "|---|---|---|---|---|",
    ]
    for n, v, sh, u in [
        ("org.secuso.privacyfriendlysudoku", "3.2.4 (vc19)",
         "c2a582760a33b1c84d9de7247293091aea74832ab2c804337af56e21b3f06ba0",
         "https://f-droid.org/repo/org.secuso.privacyfriendlysudoku_19.apk"),
        ("org.secuso.privacyfriendlymemory", "1.1.1 (vc8)",
         "04fa2257526dcab66c9b3716403ffaaa523a75038ae0589d6cc913bfcd837397",
         "https://f-droid.org/repo/org.secuso.privacyfriendlymemory_8.apk"),
        ("com.wordgame.nian", "(vc11) — wordle-like",
         "bf19e069ba31ef0577065f833e8fa6e92f025e5d912be538ecbe696f15557c3b",
         "https://f-droid.org/repo/com.wordgame.nian_11.apk"),
        ("com.joeld.minesweeper", "(vc7)",
         "46964d6438a76a990f10e1653401067aa4dc5927c3050f13c56d33096742ff24",
         "https://f-droid.org/repo/com.joeld.minesweeper_7.apk"),
    ]:
        lines.append(f"| `{n}` | {v} | `{sh}` | <{u}> | no frame within 540 s budget |")
    lines += [
        "",
        "**Archive total after S37 wave 3: 40 APKs registered (28 prior + 12 new identities; 2 corpus copies proven byte-duplicates of rows 3/12).**",
        "Zero-APK law holds.",
        "",
    ]
    LEDGER.write_text(txt + "\n".join(lines))
    print("ledger appended:", len(lines), "lines")


if __name__ == "__main__":
    main()
