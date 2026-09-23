#!/usr/bin/env python3
"""s88_corpus.py — S88 §2-§4 SOURCE-FIRST corpus scanner (user mandate:
understand across ~200 games/apps which classes repeat most, which APIs
matter, which API families to fix for maximum execution gains).

Streaming discipline (S84 disk law): download APK (cap 48 MB) → sha256 →
parse every dex type_ids table → aggregate framework class descriptors +
lib-family signals → DELETE apk unless in EXECUTE set → record profile.

Outputs:
  run/s88/corpus/profiles.json   per-title machine profile
  run/s88/corpus/frequency.json  corpus-wide class frequency + lib families
  run/s88/corpus/queue.json      execution queue (user-named + representatives)
"""
import hashlib
import json
import os
import re
import subprocess
import struct
import sys
import zipfile

ROOT = "/home/z/my-project"
OUT = f"{ROOT}/run/s88/corpus"
APKS = f"{OUT}/apks"
os.makedirs(APKS, exist_ok=True)
UA = "Mozilla/5.0 (X11; Linux x86_64) MiniAndroid-S88-corpus/1.0"
SIZE_CAP = 48 * 1024 * 1024

# ── dedup: everything already registered or previously executed ──────────
def existing_packages():
    pkgs = set()
    r = json.load(open(f"{ROOT}/docs/evidence/canonical/registry.json"))
    for t in r["titles"]:
        pkgs.add(t["package"])
    for wave, path in (("s84", f"{ROOT}/run/s84/manifest_new.json"),
                       ("s85", f"{ROOT}/run/s85/manifest_new.json"),
                       ("s87", f"{ROOT}/run/s87/probe/manifest.json")):
        if os.path.exists(path):
            m = json.load(open(path))
            items = m if isinstance(m, list) else m.keys()
            for it in items:
                p = it["package"] if isinstance(it, dict) else it
                pkgs.add(p)
    return pkgs

EXISTING = existing_packages()
print(f"dedup base: {len(EXISTING)} known packages", flush=True)

# ── user-mandated candidates (Persian brief: snake games, flashlight,
#    Signal, Telegram, small light games) ─────────────────────────────────
USER_NAMED = {
    "org.thoughtcrime.securesms": "app",      # Signal — open source, F-Droid
    "org.telegram.messenger": "app",          # Telegram official F-Droid pkg
    "org.telegram.messenger.web": "app",      # Telegram FOSS web build (pinned in registry)
    "com.whatsapp": "app",                    # NOT open source — record honestly
}

SEARCH_TERMS_GAMES = ["snake", "flashlight"]
CATEGORIES_GAMES = ["games/puzzle", "games/arcade", "games/action",
                    "games/board", "games/card", "games/casual"]
CATEGORIES_APPS = ["tools", "productivity", "multimedia", "internet",
                   "security", "science-and-education"]

def http(url, timeout=25):
    r = subprocess.run(["curl", "-s", "-L", "-m", str(timeout), "-A", UA, url],
                       capture_output=True)
    return r.stdout

def scrape_search(term, limit=12):
    body = http(f"https://f-droid.org/en/search/?q={term}", 20).decode(
        "utf-8", errors="replace")
    out = []
    for m in re.finditer(r'/en/packages/([a-z0-9_.]+)/', body, re.I):
        p = m.group(1)
        if p not in out:
            out.append(p)
        if len(out) >= limit:
            break
    return out

def scrape_category(cat, pages=3, limit=40):
    pkgs = []
    for pg in range(1, pages + 1):
        url = f"https://f-droid.org/en/categories/{cat}/?page={pg}" if pg > 1 \
            else f"https://f-droid.org/en/categories/{cat}/"
        body = http(url, 25).decode("utf-8", errors="replace")
        for m in re.finditer(r'/en/packages/([a-z0-9_.]+)/', body, re.I):
            p = m.group(1)
            if p not in EXISTING and p not in pkgs:
                pkgs.append(p)
            if len(pkgs) >= limit:
                return pkgs
    return pkgs

def api_latest(pkg):
    d = http(f"https://f-droid.org/api/v1/packages/{pkg}", 15)
    try:
        j = json.loads(d.decode("utf-8", errors="replace"))
        pkgs = j.get("packages") or []
        for p in pkgs:  # API returns newest first
            if p.get("versionCode"):
                return p.get("versionName"), p.get("versionCode")
    except Exception:
        pass
    return None, None

def upstream_src(pkg):
    body = http(f"https://f-droid.org/en/packages/{pkg}/", 20).decode(
        "utf-8", errors="replace")
    m = re.search(r'href="(https?://[^"]+)"[^>]*>\s*Source Code', body)
    if m:
        return m.group(1)
    m = re.search(r'Source Code.*?href="(https?://[^"]+)"', body, re.S)
    return m.group(1) if m else ""

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

# ── dex scanning ──────────────────────────────────────────────────────────
LIB_SIGS = {
    "compose":      ["Landroidx/compose/"],
    "glide":        ["Lcom/bumptech/glide/"],
    "libgdx":       ["Lcom/badlogic/gdx/", "Lorg/libgdx/"],
    "flutter":      ["Lio/flutter/"],
    "react-native": ["Lcom/facebook/react/"],
    "webview-heavy":["Landroid/webkit/", "Landroid/webkit/WebView;"],
    "kotlin":       ["Lkotlin/", "Lkotlinx/"],
    "coroutines":   ["Lkotlinx/coroutines/"],
    "room":         ["Landroidx/room/"],
    "sqlite":       ["Landroid/database/sqlite/", "Landroidx/sqlite/"],
    "material":     ["Lcom/google/android/material/"],
    "appcompat":    ["Landroidx/appcompat/"],
    "constraint":   ["Landroidx/constraintlayout/"],
    "okhttp":       ["Lokhttp3/", "Lcom/squareup/okhttp"],
    "retrofit":     ["Lretrofit2/", "Lcom/squareup/retrofit"],
    "rxjava":       ["Lio/reactivex/"],
    "gms":          ["Lcom/google/android/gms/"],
    "lottie":       ["Lcom/airbnb/lottie/"],
    "coil":         ["Lcoil/"],
    "picasso":      ["Lcom/squareup/picasso/"],
    "jsoup":        ["Lorg/jsoup/"],
    "gson":         ["Lcom/google/gson/"],
    "recyclerview": ["Landroidx/recyclerview/widget/"],
    "viewpager":    ["Landroidx/viewpager/", "Landroidx/viewpager2/"],
    "fragment":     ["Landroidx/fragment/app/"],
    "lifecycle":    ["Landroidx/lifecycle/"],
    "workmanager":  ["Landroidx/work/"],
    "datastore":    ["Landroidx/datastore/"],
    "media3":       ["Landroidx/media3/"],
    "exoplayer":    ["Lcom/google/android/exoplayer2/"],
    "glsl-gles":    ["Landroid/opengl/"],
    "surf":         ["Landroid/view/SurfaceView;", "Landroid/view/SurfaceHolder;"],
}

FRAMEWORK_PREFIXES = ("Landroid/", "Landroidx/", "Ljava/", "Ljavax/",
                      "Lcom/google/android/material/", "Lkotlin")

def scan_dex(path):
    """Parse every dex type_ids table; return Counter of descriptors."""
    from collections import Counter
    cnt = Counter()
    libs = Counter()
    webview = False
    try:
        z = zipfile.ZipFile(path)
    except Exception:
        return cnt, libs, False, 0
    dexes = [n for n in z.namelist() if n.endswith(".dex")]
    for name in dexes:
        d = z.read(name)
        # lib family signals via raw bytes (fast + exact prefix match)
        for fam, sigs in LIB_SIGS.items():
            for s in sigs:
                if s.encode() in d:
                    libs[fam] += 1
        try:
            ssz, sof = struct.unpack_from("<II", d, 0x38)
            tsz, tof = struct.unpack_from("<II", d, 0x40)

            def uleb(f):
                r = 0; s = 0
                while True:
                    b = f.read(1)[0]
                    r |= (b & 0x7F) << s
                    s += 7
                    if not b & 0x80:
                        break
                return r

            def string(i):
                off = struct.unpack_from("<I", d, sof + i * 4)[0]
                f = io.BytesIO(d); f.seek(off)
                n = uleb(f)
                return f.read(n).decode("utf-8", "replace")

            for ti in range(tsz):
                sidx = struct.unpack_from("<I", d, tof + ti * 4)[0]
                desc = string(sidx)
                if desc.startswith(FRAMEWORK_PREFIXES) or \
                   desc.startswith("Lcom/google/android/"):
                    cnt[desc] += 1
        except Exception:
            continue
    return cnt, libs, webview, len(dexes)

import io  # noqa: E402  (used by scan_dex)

# ── candidate pool (§3: ≥100 games + ≥100 apps target; this run ~120) ────
def build_pool():
    pool = {}
    for term in SEARCH_TERMS_GAMES:
        for p in scrape_search(term):
            if p not in EXISTING:
                pool.setdefault(p, {"kind": "game", "why": f"search:{term}"})
    for cat in CATEGORIES_GAMES:
        for p in scrape_category(cat):
            pool.setdefault(p, {"kind": "game", "why": f"cat:{cat}"})
    for cat in CATEGORIES_APPS:
        for p in scrape_category(cat):
            pool.setdefault(p, {"kind": "app", "why": f"cat:{cat}"})
    for p, kind in USER_NAMED.items():
        pool.setdefault(p, {"kind": kind, "why": "user-named"})
    return pool

def main():
    n_target = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    from collections import Counter
    corpus_class = Counter()
    corpus_libs = Counter()
    profiles = {}

    pool = build_pool()
    print(f"pool: {len(pool)} candidates", flush=True)

    # prioritize small packages (F-Droid API has no size; try in listed order
    # but keep the user-named first)
    ordered = [p for p in USER_NAMED if p in pool] + \
              [p for p in pool if p not in USER_NAMED]
    scanned = 0
    for pkg in ordered:
        if scanned >= n_target:
            break
        meta = pool[pkg]
        ver, vc = api_latest(pkg)
        if not vc:
            profiles[pkg] = {"kind": meta["kind"], "state": "FDROID_API_MISS"}
            print(f"  [{scanned}] {pkg}: api miss", flush=True)
            scanned += 1
            continue
        apk_url = f"https://f-droid.org/repo/{pkg}_{vc}.apk"
        dst = f"{APKS}/{pkg}.apk"
        r = subprocess.run(["curl", "-s", "-L", "-m", "120", "-A", UA,
                            "--max-filesize", str(SIZE_CAP), "-o", dst,
                            apk_url], capture_output=True)
        if r.returncode != 0 or not os.path.exists(dst) or \
                os.path.getsize(dst) < 10000:
            if os.path.exists(dst):
                os.remove(dst)
            profiles[pkg] = {"kind": meta["kind"], "version": ver, "vc": vc,
                             "state": "DOWNLOAD_BLOCKED",
                             "url": apk_url, "why": meta["why"]}
            print(f"  [{scanned}] {pkg}: download blocked/oversize", flush=True)
            scanned += 1
            continue
        size = os.path.getsize(dst)
        cnt, libs, _, ndex = scan_dex(dst)
        # lib family normalized: 1 if present
        libflags = {k: 1 for k, v in libs.items() if v > 0}
        prof = {
            "kind": meta["kind"], "why": meta["why"], "version": ver,
            "vc": vc, "sha256": sha256(dst), "size": size, "url": apk_url,
            "upstream": upstream_src(pkg), "dexes": ndex,
            "libs": libflags,
            "top_classes": cnt.most_common(25),
            "android_type_count": sum(v for k, v in cnt.items()
                                      if k.startswith("Landroid/")),
        }
        profiles[pkg] = prof
        corpus_class.update(cnt)
        corpus_libs.update(libflags)
        print(f"  [{scanned}] {pkg}: {size//1024}KB dexes={ndex} "
              f"libs={sorted(libflags)[:6]}", flush=True)
        os.remove(dst)   # streaming discipline — keep disk bounded
        scanned += 1

    json.dump(profiles, open(f"{OUT}/profiles.json", "w"), indent=1)
    freq = {
        "scanned": scanned,
        "top_classes_corpus": corpus_class.most_common(80),
        "lib_families": dict(corpus_libs.most_common()),
        "class_family_counts": {},
    }
    # collapse to class-family level (the actionable granularity)
    fam = Counter()
    for desc, c in corpus_class.items():
        parts = desc.rstrip(";").split("/")
        f = "/".join(parts[:4]) + ";"
        fam[f] += c
    freq["class_family_counts"] = dict(fam.most_common(60))
    json.dump(freq, open(f"{OUT}/frequency.json", "w"), indent=1)
    print(f"=== scanned {scanned} | pool {len(pool)} ===", flush=True)

if __name__ == "__main__":
    main()
