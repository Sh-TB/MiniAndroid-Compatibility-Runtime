#!/usr/bin/env python3
"""s88_index_harvest.py — one-shot F-Droid index harvest for the S89 200-title
corpus. Downloads index-v1.jar ONCE (lysator mirror — 100x faster than
f-droid.org from this container), selects smallest-first games+apps not in
the registry, and emits queue_index.json + queue_special.json.

Disk law: index jar deleted after extraction; only the queue JSONs remain.
"""
import io
import json
import os
import subprocess
import zipfile

ROOT = "/home/z/my-project"
OUT = f"{ROOT}/run/s88/corpus"
os.makedirs(OUT, exist_ok=True)
UA = "Mozilla/5.0 (X11; Linux x86_64) MiniAndroid-S89/1.0"
MIRROR = "https://ftp.lysator.liu.se/pub/fdroid/repo/index-v1.jar"

GAME_CATS = {"Puzzle Game", "Arcade Game", "Action Game", "Board Game",
             "Card Game", "Casual Game", "Strategy Game", "Word Game",
             "Educational Game", "Sport Game", "Shooter Game",
             "Role-Playing Game", "Platformer Game", "Party Game",
             "Game Helper"}
APP_CATS = {
    "System", "Internet", "Multimedia", "Science & Education",
    "Connectivity", "Security", "Sports & Health", "Reading", "Writing",
    "Navigation", "Development", "Note", "Graphics", "Finance Manager",
    "Calendar & Agenda", "Password & 2FA", "Messaging", "VPN & Proxy",
    "Phone & SMS", "Time", "Task", "Timer", "Weather", "File Management",
    "Backup", "Desk", "Wallpaper", "Launcher", "Theming", "Translation",
    "Dict", "Feed", "Mail", "Browser", "Gallery", "Camera",
}

def existing_packages():
    pkgs = set()
    r = json.load(open(f"{ROOT}/docs/evidence/canonical/registry.json"))
    for t in r["titles"]:
        pkgs.add(t["package"])
    for path in (f"{ROOT}/run/s84/manifest_new.json",
                 f"{ROOT}/run/s85/manifest_new.json",
                 f"{ROOT}/run/s87/probe/manifest.json"):
        if os.path.exists(path):
            m = json.load(open(path))
            items = m if isinstance(m, list) else m.keys()
            for it in items:
                pkgs.add(it["package"] if isinstance(it, dict) else it)
    return pkgs

def main():
    jar_path = f"{OUT}/index-v1.jar"
    if not os.path.exists(jar_path):
        subprocess.run(["curl", "-s", "-L", "-m", "300", "-A", UA,
                        "-o", jar_path, MIRROR], check=False)
    print("jar size:", os.path.getsize(jar_path), flush=True)

    with zipfile.ZipFile(jar_path) as z:
        name = [n for n in z.namelist() if n.endswith(".json")][0]
        with z.open(name) as f:
            idx = json.load(io.TextIOWrapper(f, encoding="utf-8"))
    os.remove(jar_path)
    print("index packages:", len(idx.get("packages", {})), flush=True)

    APPMETA = {a.get("packageName"): a for a in idx.get("apps", [])}
    EXISTING = existing_packages()
    games, apps = [], []
    for pkg, versions in idx.get("packages", {}).items():
        if pkg in EXISTING:
            continue
        best = max(versions, key=lambda v: v.get("versionCode", 0))
        if best.get("apkName") is None:
            continue
        size = best.get("size") or 0
        if size <= 0 or size > 48 * 1024 * 1024:
            continue
        meta = APPMETA.get(pkg, {})
        cats = meta.get("categories") or []
        is_game = any(c in GAME_CATS for c in cats)
        is_app = any(c in APP_CATS for c in cats) and not is_game
        if not (is_game or is_app):
            continue
        rec = {
            "package": pkg, "kind": "game" if is_game else "app",
            "vc": best.get("versionCode"), "version": best.get("versionName"),
            "size": size, "url": "https://f-droid.org/repo/" + best["apkName"],
            "source": meta.get("sourceCode") or "",
            "license": meta.get("license") or "",
        }
        (games if is_game else apps).append(rec)

    games.sort(key=lambda r: r["size"])
    apps.sort(key=lambda r: r["size"])
    json.dump({"games": games[:110], "apps": apps[:110]},
              open(f"{OUT}/queue_index.json", "w"), indent=1)

    KWS = ["flashlight", "torch", "snake"]
    specials = {}
    for pkg, meta in APPMETA.items():
        hay = (pkg + " " + (meta.get("summary") or "")).lower()
        for kw in KWS:
            if kw in hay:
                versions = idx.get("packages", {}).get(pkg, [])
                if versions:
                    best = max(versions, key=lambda v: v.get("versionCode", 0))
                    if best.get("apkName") and 0 < (best.get("size") or 0) \
                            <= 48 * 1024 * 1024:
                        specials.setdefault(kw, []).append({
                            "package": pkg, "size": best["size"],
                            "vc": best.get("versionCode"),
                            "version": best.get("versionName"),
                            "url": "https://f-droid.org/repo/" + best["apkName"],
                            "source": meta.get("sourceCode") or "",
                        })
    for kw in specials:
        specials[kw].sort(key=lambda r: r["size"])
    json.dump(specials, open(f"{OUT}/queue_special.json", "w"), indent=1)
    print(f"games: {min(110,len(games))}/{len(games)}  "
          f"apps: {min(110,len(apps))}/{len(apps)}", flush=True)
    for kw, lst in specials.items():
        print(f"special '{kw}': {[r['package'] for r in lst[:4]]}", flush=True)

if __name__ == "__main__":
    main()
