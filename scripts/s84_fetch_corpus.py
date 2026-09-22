#!/usr/bin/env python3
"""s84_fetch_corpus.py — S84 NEW-50 corpus fetch (user mandate: 50 new apps/games).

Tier 1: 21 never-run APKs already cached in /tmp/my-project/apk_cache/s82.
Tier 2/3: F-Droid games + apps selected from docs/corpus/s81/corpus_index.json
          (fan-out coverage families: board/card/puzzle/action games,
           widget/clock/calculator/utility apps).
For each fetched title: F-Droid API -> latest versionCode -> repo APK download
(cap 48 MB) -> SHA256. Metadata written to run/s84/manifest_new.json.

Law: every title records SOURCE (F-Droid URL + upstream when resolvable).
"""
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT = "/home/z/my-project"
OUT = f"{ROOT}/run/s84"
APKS = f"{OUT}/apks"
os.makedirs(APKS, exist_ok=True)
UA = "Mozilla/5.0 (X11; Linux x86_64) MiniAndroid-S84-corpus/1.0"
SIZE_CAP = 48 * 1024 * 1024

# ---- Tier 1: already cached, never executed -------------------------------
T1 = [
    "bim.app", "com.clavierhaus.gnubg", "com.hegocre.nextcloudpasswords",
    "com.hfut.schedule", "com.justdeax.composeStopwatch", "com.qwde.ccm",
    "com.vovagorodok.blichess", "com.vovagorodok.blidraughts",
    "de.seemoo.at_tracking_detection", "de.taz.android.app.free",
    "foehnix.widget", "io.github.aoc_normal", "io.github.hathibelagal.mykanji",
    "me.river.nightbell", "me.timeto.app", "org.nitri.opentopo",
    "org.opensurge2d.surgeengine", "ru.wohlsoft.thextech.fdroid",
    "site.leos.apps.lespas", "tibarj.tranquilstopwatch", "xyz.deepdaikon.quinb",
]
T1_FILES = {
    "bim.app": "bim.app_1600.apk", "com.clavierhaus.gnubg": "com.clavierhaus.gnubg_102.apk",
    "com.hegocre.nextcloudpasswords": "com.hegocre.nextcloudpasswords_49.apk",
    "com.hfut.schedule": "com.hfut.schedule_2724.apk",
    "com.justdeax.composeStopwatch": "com.justdeax.composeStopwatch_1009011.apk",
    "com.qwde.ccm": "com.qwde.ccm_5.apk", "com.vovagorodok.blichess": "com.vovagorodok.blichess_29.apk",
    "com.vovagorodok.blidraughts": "com.vovagorodok.blidraughts_3.apk",
    "de.seemoo.at_tracking_detection": "de.seemoo.at_tracking_detection_68.apk",
    "de.taz.android.app.free": "de.taz.android.app.free_20102900.apk",
    "foehnix.widget": "foehnix.widget_40.apk", "io.github.aoc_normal": "io.github.aoc_normal_1.apk",
    "io.github.hathibelagal.mykanji": "io.github.hathibelagal.mykanji_7.apk",
    "me.river.nightbell": "me.river.nightbell_41.apk", "me.timeto.app": "me.timeto.app_624.apk",
    "org.nitri.opentopo": "org.nitri.opentopo_82.apk",
    "org.opensurge2d.surgeengine": "org.opensurge2d.surgeengine_30650.apk",
    "ru.wohlsoft.thextech.fdroid": "ru.wohlsoft.thextech.fdroid_1030703.apk",
    "site.leos.apps.lespas": "site.leos.apps.lespas_118.apk",
    "tibarj.tranquilstopwatch": "tibarj.tranquilstopwatch_17.apk",
    "xyz.deepdaikon.quinb": "xyz.deepdaikon.quinb_10.apk",
}
S82 = "/tmp/my-project/apk_cache/s82"

# ---- Tier 2: F-Droid games (fan-out families) ------------------------------
GAMES = [
    "com.sidhant.puzzle", "io.github.ebraminio.bouncy", "com.dash1971.maia_chess",
    "com.kingalex.kingpong", "io.itch.pirate_solitaire", "com.dozingcatsoftware.dodge",
    "com.helddertierwelt.mentalmath", "com.sidhant.bubbleshooter",
    "net.tigr.navyfleetbattle", "ca.rmen.nounours", "com.willie.mancala",
    "de.georgsieber.ballbreak", "com.octbit.rutmath", "com.galaxyrio.sudokusolver",
    "org.lufebe16.pysolfc", "com.kaeruct.raumballer", "com.sanskritbasics.memory",
    "com.smorgasbork.hotdeath", "com.serwylo.retrowars", "com.yepgoryo.EggReturnsHome",
    "io.github.johnathan.minesweeper", "jwtc.android.chess",
    "org.pipoypipagames.cowsrevenge", "org.bobstuff.bobball",
    "com.vayunmathur.games.alchemist", "ru.hyst329.openfool",
]
# ---- Tier 3: F-Droid apps ---------------------------------------------------
APPS = [
    "fr.shiningcat.binclockwidget", "net.diffengine.romandigitalclock",
    "com.jherkenhoff.qalculate", "com.madlonkay.orgro", "com.kompact",
    "com.ma.tehro", "com.forrestguice.suntimeswidget", "com.vayunmathur.clock",
    "com.vagujhelyigergely.calculatorm3", "fr.corenting.convertisseureurofranc",
    "com.kolakek.pimiwidget", "com.davidtakac.bura",
    "org.ucam.ssb22.pinyinfdroid", "com.ominous.quickweather",
]


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def api_pkg(pkg):
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


def upstream_src(pkg):
    """Extract upstream Source Code URL from the F-Droid package page."""
    r = subprocess.run(["curl", "-s", "-m", "15", "-A", UA,
                        f"https://f-droid.org/en/packages/{pkg}/"],
                       capture_output=True)
    body = r.stdout.decode("utf-8", errors="replace")
    m = re.search(r'href="(https?://[^"]+)"[^>]*>\s*Source Code', body)
    if m:
        return m.group(1)
    m = re.search(r'Source Code.*?href="(https?://[^"]+)"', body, re.S)
    return m.group(1) if m else ""


def fetch(pkg, kind, dst_manifest):
    fn = f"{pkg}.apk"
    dst = f"{APKS}/{fn}"
    if os.path.exists(dst) and os.path.getsize(dst) > 100000:
        ver, vc = api_pkg(pkg)
        dst_manifest.append({"package": pkg, "kind": kind, "file": fn,
                             "version": ver, "vc": vc, "sha256": sha256(dst),
                             "source": f"https://f-droid.org/en/packages/{pkg}/",
                             "origin": "fdroid-repo"})
        print(f"CACHED {pkg}")
        return True
    ver, vc = api_pkg(pkg)
    if not vc:
        print(f"NO-API {pkg}")
        return False
    url = f"https://f-droid.org/repo/{pkg}_{vc}.apk"
    rc = subprocess.call(["curl", "-sL", "-m", "240", "-A", UA, "-o", dst, url])
    if rc != 0 or not os.path.exists(dst) or os.path.getsize(dst) < 100000:
        print(f"FAIL {pkg} ({url})")
        if os.path.exists(dst):
            os.remove(dst)
        return False
    if os.path.getsize(dst) > SIZE_CAP:
        print(f"TOO-BIG {pkg} {os.path.getsize(dst)//1024//1024}MB")
        os.remove(dst)
        return False
    dst_manifest.append({"package": pkg, "kind": kind, "file": fn,
                         "version": ver, "vc": vc, "sha256": sha256(dst),
                         "source": f"https://f-droid.org/en/packages/{pkg}/",
                         "origin": "fdroid-repo"})
    print(f"OK {pkg} {ver} vc{vc} {os.path.getsize(dst)//1024//1024}MB")
    return True


def main():
    manifest = []
    n = 0
    # Tier 1: adopt cached APKs
    for pkg in T1:
        src = f"{S82}/{T1_FILES[pkg]}"
        if os.path.exists(src):
            dst = f"{APKS}/{pkg}.apk"
            if not os.path.exists(dst):
                os.link(src, dst) if os.stat(src).st_dev == os.stat(APKS).st_dev else None
                if not os.path.exists(dst):
                    subprocess.call(["cp", src, dst])
            ver, vc = api_pkg(pkg)
            manifest.append({"package": pkg, "kind": "s82-cache", "file": f"{pkg}.apk",
                             "version": ver, "vc": vc, "sha256": sha256(dst),
                             "source": f"https://f-droid.org/en/packages/{pkg}/",
                             "origin": "s82-cache"})
            n += 1
            print(f"T1 {pkg} (cached)")
        else:
            print(f"T1-MISS {pkg}")
    # Tier 2/3: fetch until we hit 50
    need = 50 - n
    got = 0
    for kind, pool in (("game", GAMES), ("app", APPS)):
        for pkg in pool:
            if got >= need:
                break
            if fetch(pkg, kind, manifest):
                got += 1
        if got >= need:
            break
    print(f"\nTOTAL {n + got} titles (T1 {n} + fetched {got})")
    with open(f"{OUT}/manifest_new.json", "w") as f:
        json.dump({"wave": "S84", "count": len(manifest), "titles": manifest}, f, indent=1)
    print(f"manifest: {OUT}/manifest_new.json")


if __name__ == "__main__":
    main()
