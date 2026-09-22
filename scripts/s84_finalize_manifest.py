#!/usr/bin/env python3
"""s84_finalize_manifest.py — final S84 NEW-50 manifest with provenance.

For every APK in run/s84/apks: F-Droid API version, SHA256, F-Droid page,
upstream source URL (from F-Droid page), kind (game/app/s82-cache).
Output: run/s84/manifest_new.json (50 titles).
"""
import hashlib
import json
import os
import re
import subprocess

ROOT = "/home/z/my-project"
APKS = f"{ROOT}/run/s84/apks"
UA = "MiniAndroid-S84/1.0"
GAMES = {
    "com.sidhant.puzzle", "com.kingalex.kingpong", "io.itch.pirate_solitaire",
    "com.helddertierwelt.mentalmath", "com.sidhant.bubbleshooter",
    "net.tigr.navyfleetbattle", "ca.rmen.nounours", "com.willie.mancala",
    "de.georgsieber.ballbreak", "com.octbit.rutmath",
    "com.galaxyrio.sudokusolver", "org.lufebe16.pysolfc",
    "com.kaeruct.raumballer", "com.sanskritbasics.memory",
    "com.smorgasbork.hotdeath", "com.serwylo.retrowars",
    "io.github.johnathan.minesweeper", "jwtc.android.chess",
    "org.bobstuff.bobball", "com.vayunmathur.games.alchemist",
    "io.github.ebraminio.bouncy", "com.dozingcatsoftware.dodge",
    "xyz.deepdaikon.quinb", "com.qwde.ccm", "bim.app",
    "io.github.hathibelagal.mykanji", "com.clavierhaus.gnubg",
    "com.vovagorodok.blichess", "com.vovagorodok.blidraughts",
    "org.opensurge2d.surgeengine", "ru.wohlsoft.thextech.fdroid",
}


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def api_ver(pkg):
    r = subprocess.run(["curl", "-s", "-m", "15", "-A", UA,
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


def upstream(pkg):
    r = subprocess.run(["curl", "-s", "-m", "15", "-A", UA,
                        f"https://f-droid.org/en/packages/{pkg}/"],
                       capture_output=True)
    body = r.stdout.decode("utf-8", errors="replace")
    m = re.search(r'href="(https?://[^"]+)"[^>]*>\s*Source Code', body)
    if not m:
        m = re.search(r'Source Code.*?href="(https?://[^"]+)"', body, re.S)
    return m.group(1) if m else ""


def main():
    titles = []
    for apk in sorted(os.listdir(APKS)):
        if not apk.endswith(".apk"):
            continue
        pkg = apk[:-4]
        ver, vc = api_ver(pkg)
        kind = "game" if pkg in GAMES else "app"
        src = upstream(pkg)
        titles.append({
            "package": pkg, "kind": kind, "file": apk,
            "version": ver, "vc": vc,
            "sha256": sha256(f"{APKS}/{apk}"),
            "source": f"https://f-droid.org/en/packages/{pkg}/",
            "upstream": src,
            "origin": "s82-cache" if os.path.exists(
                f"/tmp/my-project/apk_cache/s82/{pkg}_" + "*.apk") else "fdroid-repo",
        })
        print(f"{pkg:<44} {str(ver):<14} {kind:<5} upstream={src[:60]}")
    with open(f"{ROOT}/run/s84/manifest_new.json", "w") as f:
        json.dump({"wave": "S84", "count": len(titles), "titles": titles}, f, indent=1)
    games = sum(1 for t in titles if t["kind"] == "game")
    ups = sum(1 for t in titles if t["upstream"])
    print(f"\nFINAL: {len(titles)} titles ({games} games / {len(titles)-games} apps), "
          f"{ups} with upstream source links")


if __name__ == "__main__":
    main()
