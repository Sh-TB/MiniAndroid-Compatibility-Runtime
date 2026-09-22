#!/usr/bin/env python3
"""s85_fetch_corpus.py — S85 corpus fetch (user mandate: 50 MORE new apps/games).

Wave S85 adds 50 titles NOT present in the S84 canonical registry (96 records).
Selection = fan-out coverage (graphics-heavy games, board/card/puzzle families,
compose-heavy apps, widget/clock/utility apps) — NOT random.

Tier A: curated confident F-Droid candidates (games + apps).
Tier B: F-Droid category-page scrape (games) to fill the game quota.
Every title: F-Droid API validation -> repo APK download (cap 48 MB) -> SHA256
-> F-Droid page URL + upstream Source Code link.

Dedup: run/s85/existing_pkgs.json (all 96 registry packages + titles).
"""
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT = "/home/z/my-project"
OUT = f"{ROOT}/run/s85"
APKS = f"{OUT}/apks"
os.makedirs(APKS, exist_ok=True)
UA = "Mozilla/5.0 (X11; Linux x86_64) MiniAndroid-S85-corpus/1.0"
SIZE_CAP = 48 * 1024 * 1024
TARGET = 50
GAME_QUOTA = 25
APP_QUOTA = 25

EXISTING = set(json.load(open(f"{OUT}/existing_pkgs.json")))

GAMES = [
    "name.boyle.chris.sgtpuzzles", "com.uberspot.a2048",
    "org.secuso.privacyfriendlydame", "org.secuso.privacyfriendlymemory",
    "org.secuso.privacyfriendly2048", "org.secuso.privacyfriendlysudoku",
    "org.secuso.privacyfriendlysolitaire", "org.jamienicol.edges",
    "org.blockinger.game", "net.sourceforge.solitaire_cg",
    "com.serwylo.lexisparta", "com.serwylo.babydots",
    "com.gitlab.bobbyunlocked.puzzles", "org.secuso.privacyfriendlydoodle",
    "com.darkempire78.minesweeper", "com.github.l一一一一",  # invalid filler ignored
]
APPS = [
    "com.gh4a", "com.nononsenseapps.notepad", "de.danoeh.antennapod",
    "org.tasks", "com.fsck.k9", "org.y20k.transistor", "eu.faircode.email",
    "com.beemdevelopment.aegis", "com.kunzisoft.keepass.libre",
    "com.aurora.store", "nl.mpcjanssen.simpletask",
    "de.markusfisch.android.binaryeye", "com.trianguloy.urlchecker",
    "org.fossify.clock", "org.fossify.gallery", "org.fossify.notes",
    "com.maltaisn.notes.sync", "org.secuso.privacyfriendlynotes",
    "org.secuso.privacyfriendlyweather", "org.secuso.privacyfriendlynetmonitor",
    "org.secuso.privacyfriendlyactivitytracker", "de.schildbach.wallet",
    "at.techbee.jtx", "it.niedermann.nextcloud.deck", "com.best.deskclock",
    "com.philliphsu.clock2", "org.y20k.trackbook", "org.dystopia.email",
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
    r = subprocess.run(["curl", "-s", "-m", "15", "-A", UA,
                        f"https://f-droid.org/en/packages/{pkg}/"],
                       capture_output=True)
    body = r.stdout.decode("utf-8", errors="replace")
    m = re.search(r'href="(https?://[^"]+)"[^>]*>\s*Source Code', body)
    if m:
        return m.group(1)
    m = re.search(r'Source Code.*?href="(https?://[^"]+)"', body, re.S)
    return m.group(1) if m else ""


def scrape_category(cat, pages=8):
    """Extract package ids from F-Droid category listing pages."""
    pkgs = []
    for pg in range(1, pages + 1):
        url = f"https://f-droid.org/en/categories/{cat}/?page={pg}" if pg > 1 \
            else f"https://f-droid.org/en/categories/{cat}/"
        r = subprocess.run(["curl", "-s", "-m", "20", "-A", UA, url],
                           capture_output=True)
        body = r.stdout.decode("utf-8", errors="replace")
        for m in re.finditer(r'/en/packages/([a-z0-9_.]+)/', body, re.I):
            p = m.group(1)
            if p not in EXISTING and p not in pkgs:
                pkgs.append(p)
    return pkgs


def fetch(pkg, kind, dst_manifest):
    fn = f"{pkg}.apk"
    dst = f"{APKS}/{fn}"
    if os.path.exists(dst) and os.path.getsize(dst) > 100000:
        ver, vc = api_pkg(pkg)
        dst_manifest.append({"package": pkg, "kind": kind, "file": fn,
                             "version": ver, "vc": vc, "sha256": sha256(dst),
                             "source": f"https://f-droid.org/en/packages/{pkg}/",
                             "upstream": upstream_src(pkg),
                             "origin": "fdroid-repo"})
        print(f"CACHED {pkg}", flush=True)
        return True
    ver, vc = api_pkg(pkg)
    if not vc:
        print(f"NO-API {pkg}", flush=True)
        return False
    url = f"https://f-droid.org/repo/{pkg}_{vc}.apk"
    rc = subprocess.call(["curl", "-sL", "-m", "240", "-A", UA, "-o", dst, url])
    if rc != 0 or not os.path.exists(dst) or os.path.getsize(dst) < 100000:
        print(f"FAIL {pkg} ({url})", flush=True)
        if os.path.exists(dst):
            os.remove(dst)
        return False
    if os.path.getsize(dst) > SIZE_CAP:
        print(f"TOO-BIG {pkg} {os.path.getsize(dst)//1024//1024}MB", flush=True)
        os.remove(dst)
        return False
    dst_manifest.append({"package": pkg, "kind": kind, "file": fn,
                         "version": ver, "vc": vc, "sha256": sha256(dst),
                         "source": f"https://f-droid.org/en/packages/{pkg}/",
                         "upstream": upstream_src(pkg),
                         "origin": "fdroid-repo"})
    print(f"OK {pkg} {ver} vc{vc} {os.path.getsize(dst)//1024//1024}MB", flush=True)
    return True


def save(manifest):
    with open(f"{OUT}/manifest_new.json", "w") as f:
        json.dump({"wave": "S85", "count": len(manifest), "titles": manifest},
                  f, indent=1)


def main():
    import time
    t0 = time.time()
    BUDGET = 420  # seconds per invocation (foreground chunked execution)
    manifest = []
    # resume: load existing manifest from prior chunks
    mpath = f"{OUT}/manifest_new.json"
    if os.path.exists(mpath):
        try:
            manifest = json.load(open(mpath)).get("titles", [])
        except Exception:
            manifest = []
    ng = sum(1 for m in manifest if m["kind"] == "game")
    na = len(manifest) - ng
    if len(manifest) >= TARGET:
        print(f"ALREADY-COMPLETE {len(manifest)}", flush=True)
        return
    # Tier A: curated candidates
    for kind, pool in (("game", GAMES), ("app", APPS)):
        for pkg in pool:
            if time.time() - t0 > BUDGET:
                save(manifest)
                print(f"TIME-BUDGET hit (A) games={ng} apps={na}", flush=True)
                return
            if not re.fullmatch(r"[a-z0-9_.]+", pkg or ""):
                continue
            if pkg in EXISTING:
                print(f"SKIP-EXISTING {pkg}", flush=True)
                continue
            if any(m["package"] == pkg for m in manifest):
                continue
            if kind == "game" and ng >= GAME_QUOTA:
                continue
            if kind == "app" and na >= APP_QUOTA:
                continue
            if fetch(pkg, kind, manifest):
                if kind == "game":
                    ng += 1
                else:
                    na += 1
                save(manifest)
    # Tier B: index-derived game fill (fan-out across the F-Droid Game category)
    if ng < GAME_QUOTA:
        print("scraping games from index-v1...", flush=True)
        try:
            more = json.load(open("/tmp/fd_game_candidates.json"))
        except Exception:
            more = []
        for cand in more:
            if ng >= GAME_QUOTA:
                break
            if time.time() - t0 > BUDGET:
                save(manifest)
                print(f"TIME-BUDGET hit (B-games) games={ng} apps={na}", flush=True)
                return
            pkg = cand["package"] if isinstance(cand, dict) else cand
            if any(m["package"] == pkg for m in manifest):
                continue
            if fetch(pkg, "game", manifest):
                ng += 1
                save(manifest)
    if na < APP_QUOTA:
        print("scraping apps...", flush=True)
        more = scrape_category("theming", pages=4) + scrape_category("office", pages=4)
        for pkg in more:
            if na >= APP_QUOTA:
                break
            if any(m["package"] == pkg for m in manifest):
                continue
            if fetch(pkg, "app", manifest):
                na += 1
                save(manifest)
    save(manifest)
    games = sum(1 for m in manifest if m["kind"] == "game")
    print(f"\nTOTAL {len(manifest)} (games {games} / apps {len(manifest)-games})")
    print(f"manifest: {OUT}/manifest_new.json")


if __name__ == "__main__":
    main()
