#!/usr/bin/env python3
"""s99_fetch_apks.py — S99 full-load wave APK sourcing (games + APP tickets).

User mandate (S99): run SEVERAL DOZEN games to full execution, close their
tickets, file new bug tickets for failures. The container reset wiped
run/ (all previously downloaded corpus APKs). This script re-sources APKs
from F-Droid (API-validated, repo download, SHA256) for the registry's
external game corpus + the open APP-* ticket packages.

Honesty: every download is recorded with source URL + SHA256; failures are
recorded as NOT_SOURCED (never guessed) per §6.

Output: run/s99/apks/<package>.apk + run/s99/apk_manifest.json
"""
import hashlib
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = "/home/z/my-project"
OUT = f"{ROOT}/run/s99"
APKS = f"{OUT}/apks"
os.makedirs(APKS, exist_ok=True)
UA = "Mozilla/5.0 (X11; Linux x86_64) MiniAndroid-S99-fullload/1.0"
SIZE_CAP = 40 * 1024 * 1024

# Game corpus (registry type=game, external). In-house games are local builds,
# handled separately by the full-load runner.
GAMES = [
    "ca.rmen.nounours", "com.dozingcatsoftware.dodge", "com.helddertierwelt.mentalmath",
    "com.kaeruct.raumballer", "com.kingalex.kingpong", "com.sanskritbasics.memory",
    "com.sidhant.bubbleshooter", "com.sidhant.puzzle", "com.smorgasbork.hotdeath",
    "com.vovagorodok.blichess", "com.vovagorodok.blidraughts", "com.willie.mancala",
    "de.georgsieber.ballbreak", "io.github.ebraminio.bouncy", "io.github.hathibelagal.mykanji",
    "io.github.johnathan.minesweeper", "jwtc.android.chess", "org.bobstuff.bobball",
    "org.lufebe16.pysolfc", "xyz.deepdaikon.quinb", "io.github.yamin8000.dooz",
    "com.emmanuelmess.tictactoe", "com.sidhant.queens", "cos.premy.mines",
    "eu.veldsoft.no.thanks", "eu.quelltext.memory", "crypto.o0o0o0o0o.games.blackjack",
    "com.vayunmathur.games.solitaire", "de.tobiasbielefeld.solitaire",
    "org.secuso.privacyfriendlybattleship", "com.jeffliu.balancetheball",
    "com.simondalvai.ball2box", "app.halma", "com.astroloop.game", "si.palcka.tarok",
    "com.rocket9labs.boxcars", "com.eightsines.firestrike.opensource",
    "com.dozingcatsoftware.bouncy", "one.scarecrow.games.OPMT", "ch.logixisland.anuto",
    "cz.romario.opensudoku", "eu.veldsoft.free.klondike", "eu.veldsoft.tri.peaks",
    "name.boyle.chris.sgtpuzzles", "org.secuso.privacyfriendlydame",
    "org.secuso.privacyfriendlysudoku", "org.secuso.privacyfriendlysolitaire",
    "com.serwylo.babydots", "dev.lonami.klooni", "eu.quelltext.counting",
    "org.andstatus.game2048", "org.mattvchandler.a2050", "org.asafonov.accelerace",
    "com.trianguloy.adnihilation", "com.ahorcado", "x653.all_in_gold",
    "org.secuso.privacyfriendlymemory", "org.secuso.privacyfriendly2048",
    "net.sourceforge.solitaire_cg", "com.dozingcatsoftware.bouncy",
]
# de-dupe preserving order
GAMES = list(dict.fromkeys(GAMES))


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def api_suggest(pkg):
    """F-Droid API: suggested versionName/versionCode."""
    r = subprocess.run(["curl", "-s", "-m", "20", "-A", UA,
                        f"https://f-droid.org/api/v1/packages/{pkg}"],
                       capture_output=True)
    try:
        d = json.loads(r.stdout.decode("utf-8", errors="replace"))
        pkgs = d.get("packages") or []
        if pkgs:
            return pkgs[0].get("versionName"), pkgs[0].get("versionCode")
    except Exception:
        pass
    return None, None


def fetch_one(pkg):
    rec = {"package": pkg, "kind": "game"}
    vn, vc = api_suggest(pkg)
    rec["versionName"] = vn
    rec["versionCode"] = vc
    if not vc:
        rec["status"] = "API_MISS"
        return rec
    dest = f"{APKS}/{pkg}.apk"
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        rec["status"] = "CACHED"
        rec["sha256"] = sha256(dest)
        rec["size"] = os.path.getsize(dest)
        return rec
    url = f"https://f-droid.org/repo/{pkg}_{vc}.apk"
    r = subprocess.run(["curl", "-s", "-L", "-m", "240", "-A", UA, "-o", dest, url],
                       capture_output=True)
    if r.returncode != 0 or not os.path.exists(dest) or os.path.getsize(dest) < 1000:
        rec["status"] = "DOWNLOAD_FAIL"
        if os.path.exists(dest):
            os.remove(dest)
        return rec
    size = os.path.getsize(dest)
    if size > SIZE_CAP:
        os.remove(dest)
        rec["status"] = "TOO_BIG"
        rec["size"] = size
        return rec
    rec["status"] = "SOURCED"
    rec["sha256"] = sha256(dest)
    rec["size"] = size
    rec["url"] = url
    return rec


def main():
    results = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        for rec in ex.map(fetch_one, GAMES):
            results.append(rec)
            print(f"[{rec['status']:>13}] {rec['package']} "
                  f"v{rec.get('versionName')} ({rec.get('size', 0)//1024}KB)", flush=True)
    manifest = f"{OUT}/apk_manifest.json"
    old = []
    if os.path.exists(manifest):
        try:
            old = json.load(open(manifest))
        except Exception:
            old = []
    by_pkg = {r["package"]: r for r in old if isinstance(r, dict)}
    for r in results:
        by_pkg[r["package"]] = r
    merged = list(by_pkg.values())
    json.dump(merged, open(manifest, "w"), indent=1)
    sourced = [r for r in results if r["status"] in ("SOURCED", "CACHED")]
    print(f"\nSOURCED/CACHED: {len(sourced)}/{len(GAMES)}")
    for st in ("API_MISS", "DOWNLOAD_FAIL", "TOO_BIG"):
        n = sum(1 for r in results if r["status"] == st)
        if n:
            print(f"{st}: {n}")


if __name__ == "__main__":
    main()
