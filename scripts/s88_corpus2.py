#!/usr/bin/env python3
"""s88_corpus2.py — S89 resilient streaming corpus scanner.

Improvements over s88_corpus.py (container-reset hardening):
  - incremental dump: profiles.json rewritten every 10 titles
  - per-APK curl: 75s max, 1 retry, lysator mirror
  - resume: skips packages already present in profiles.json
  - disk bounded: APK deleted immediately after scan

Usage: s88_corpus2.py [n_target]
"""
import hashlib
import json
import os
import subprocess
import struct
import sys
import zipfile
from collections import Counter

ROOT = "/home/z/my-project"
OUT = f"{ROOT}/run/s88/corpus"
APKS = f"{OUT}/apks"
os.makedirs(APKS, exist_ok=True)
UA = "Mozilla/5.0 (X11; Linux x86_64) MiniAndroid-S89/1.0"
SIZE_CAP = 48 * 1024 * 1024
MIRROR = "https://ftp.lysator.liu.se/pub/fdroid/repo/"

LIB_SIGS = {
    "compose": [b"Landroidx/compose/"],
    "glide": [b"Lcom/bumptech/glide/"],
    "libgdx": [b"Lcom/badlogic/gdx/", b"Lorg/libgdx/"],
    "flutter": [b"Lio/flutter/"],
    "react-native": [b"Lcom/facebook/react/"],
    "kotlin": [b"Lkotlin/", b"Lkotlinx/"],
    "coroutines": [b"Lkotlinx/coroutines/"],
    "room": [b"Landroidx/room/"],
    "sqlite": [b"Landroid/database/sqlite/", b"Landroidx/sqlite/"],
    "material": [b"Lcom/google/android/material/"],
    "appcompat": [b"Landroidx/appcompat/"],
    "constraint": [b"Landroidx/constraintlayout/"],
    "okhttp": [b"Lokhttp3/"],
    "retrofit": [b"Lretrofit2/"],
    "rxjava": [b"Lio/reactivex/"],
    "gms": [b"Lcom/google/android/gms/"],
    "lottie": [b"Lcom/airbnb/lottie/"],
    "coil": [b"Lcoil/"],
    "picasso": [b"Lcom/squareup/picasso/"],
    "jsoup": [b"Lorg/jsoup/"],
    "gson": [b"Lcom/google/gson/"],
    "recyclerview": [b"Landroidx/recyclerview/widget/"],
    "viewpager": [b"Landroidx/viewpager/"],
    "fragment": [b"Landroidx/fragment/app/"],
    "lifecycle": [b"Landroidx/lifecycle/"],
    "workmanager": [b"Landroidx/work/"],
    "datastore": [b"Landroidx/datastore/"],
    "media3": [b"Landroidx/media3/"],
    "exoplayer": [b"Lcom/google/android/exoplayer2/"],
    "glsl-gles": [b"Landroid/opengl/"],
    "surfaceview": [b"Landroid/view/SurfaceView;"],
    "webkit": [b"Landroid/webkit/"],
    "multidex": [b"Landroidx/multidex/"],
    "kotlin-reflection": [b"Lkotlin/reflect/"],
    "desugar-j$": [b"Lj$/util/"],
}
FRAMEWORK_PREFIXES = ("Landroid/", "Landroidx/", "Ljava/", "Ljavax/",
                      "Lkotlin", "Lcom/google/android/")

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def scan_dex(path):
    cnt = Counter()
    libs = Counter()
    try:
        z = zipfile.ZipFile(path)
    except Exception:
        return cnt, libs, 0
    dexes = [n for n in z.namelist() if n.endswith(".dex")]
    for name in dexes:
        d = z.read(name)
        for fam, sigs in LIB_SIGS.items():
            for s in sigs:
                if s in d:
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
                if desc.startswith(FRAMEWORK_PREFIXES):
                    cnt[desc] += 1
        except Exception:
            continue
    return cnt, libs, len(dexes)

def main():
    n_target = int(sys.argv[1]) if len(sys.argv) > 1 else 220
    prof_path = f"{OUT}/profiles.json"
    freq_path = f"{OUT}/frequency.json"
    profiles = json.load(open(prof_path)) if os.path.exists(prof_path) else {}
    q = json.load(open(f"{OUT}/queue_index.json"))
    sp = json.load(open(f"{OUT}/queue_special.json")) if \
        os.path.exists(f"{OUT}/queue_special.json") else {}
    specials = {}
    for kw, lst in sp.items():
        for r in lst:
            specials[r["package"]] = dict(r, why=f"special:{kw}")

    pool = {}
    for r in q.get("games", []):
        pool[r["package"]] = dict(r, why="game")
    for r in q.get("apps", []):
        pool[r["package"]] = dict(r, why="app")
    for p, r in specials.items():
        pool.setdefault(p, r)
    print(f"queue: {len(pool)} | already scanned: {len(profiles)}", flush=True)

    corpus_class = Counter()
    corpus_libs = Counter()
    # rebuild corpus aggregates from prior profiles (resume-safe)
    for p, prof in profiles.items():
        if "top_classes" in prof:
            corpus_class.update(dict(prof["top_classes"]))
            corpus_libs.update(prof.get("libs", {}))

    ordered = [p for p in pool if p not in profiles]
    scanned = 0
    for pkg in ordered:
        if scanned >= n_target:
            break
        meta = pool[pkg]
        vc = meta.get("vc")
        apk_url = meta.get("url") or (MIRROR + f"{pkg}_{vc}.apk")
        dst = f"{APKS}/{pkg}.apk"
        rc = subprocess.run(["curl", "-s", "-L", "-m", "75", "-A", UA,
                             "--max-filesize", str(SIZE_CAP), "-o", dst,
                             apk_url.replace("https://f-droid.org/repo/",
                                             MIRROR)]).returncode
        if rc != 0:
            rc = subprocess.run(["curl", "-s", "-L", "-m", "75", "-A", UA,
                                 "--max-filesize", str(SIZE_CAP), "-o", dst,
                                 apk_url]).returncode
        if rc != 0 or not os.path.exists(dst) or \
                os.path.getsize(dst) < 10000:
            if os.path.exists(dst):
                os.remove(dst)
            profiles[pkg] = {"kind": meta.get("kind", "app"),
                             "why": meta.get("why", ""),
                             "state": "DOWNLOAD_BLOCKED",
                             "url": apk_url}
            print(f"  [{len(profiles)}] {pkg}: BLOCKED", flush=True)
        else:
            size = os.path.getsize(dst)
            cnt, libs, ndex = scan_dex(dst)
            libflags = {k: 1 for k, v in libs.items() if v > 0}
            profiles[pkg] = {
                "kind": meta.get("kind", "app"), "why": meta.get("why", ""),
                "version": meta.get("version"), "vc": vc,
                "sha256": sha256(dst), "size": size, "url": apk_url,
                "upstream": meta.get("source", ""), "dexes": ndex,
                "libs": libflags,
                "top_classes": cnt.most_common(25),
                "android_type_count": sum(v for k, v in cnt.items()
                                          if k.startswith("Landroid/")),
            }
            corpus_class.update(cnt)
            corpus_libs.update(libflags)
            print(f"  [{len(profiles)}] {pkg}: {size//1024}KB "
                  f"libs={sorted(libflags)[:5]}", flush=True)
            os.remove(dst)
        scanned += 1
        if scanned % 10 == 0:
            json.dump(profiles, open(prof_path, "w"), indent=1)
            fam = Counter()
            for desc, c in corpus_class.items():
                fam["/".join(desc.rstrip(";").split("/")[:4]) + ";"] += c
            json.dump({"scanned": len(profiles),
                       "top_classes_corpus": corpus_class.most_common(80),
                       "lib_families": dict(corpus_libs.most_common()),
                       "class_family_counts": dict(fam.most_common(60))},
                      open(freq_path, "w"), indent=1)

    json.dump(profiles, open(prof_path, "w"), indent=1)
    fam = Counter()
    for desc, c in corpus_class.items():
        fam["/".join(desc.rstrip(";").split("/")[:4]) + ";"] += c
    json.dump({"scanned": len(profiles),
               "top_classes_corpus": corpus_class.most_common(80),
               "lib_families": dict(corpus_libs.most_common()),
               "class_family_counts": dict(fam.most_common(60))},
              open(freq_path, "w"), indent=1)
    print(f"=== DONE: {len(profiles)} profiles ===", flush=True)

if __name__ == "__main__":
    main()
