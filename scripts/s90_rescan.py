#!/usr/bin/env python3
"""s90_rescan.py — S90 §4 re-extraction of exact class/method inventory
over the existing 225-title corpus.

Streams the queue, re-downloads each APK (lysator mirror, bounded 90s),
runs the FIXED scan_dex (types + exact method signatures + own classes),
MERGES into existing profiles.json (preserves upstream/state/exec fields),
deletes the APK, checkpoints every 10.

Resume-safe: skips profiles already carrying top_methods.
Disk bounded: one APK on disk at a time.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, "/home/z/my-project/scripts")
from s88_corpus2 import scan_dex, sha256  # noqa: E402

ROOT = "/home/z/my-project"
OUT = f"{ROOT}/run/s88/corpus"
APKS = f"{OUT}/apks"
os.makedirs(APKS, exist_ok=True)
UA = "Mozilla/5.0 (X11; Linux x86_64) MiniAndroid-S90/1.0"
SIZE_CAP = 48 * 1024 * 1024
MIRROR = "https://ftp.lysator.liu.se/pub/fdroid/repo/"
CURL_TIMEOUT = "90"


def load(path, default):
    if os.path.exists(path):
        return json.load(open(path))
    return default


def main():
    prof_path = f"{OUT}/profiles.json"
    profiles = load(prof_path, {})
    q = load(f"{OUT}/queue_index.json", {})
    sp = load(f"{OUT}/queue_special.json", {})

    pool = {}
    for r in q.get("games", []):
        pool[r["package"]] = dict(r, why="game")
    for r in q.get("apps", []):
        pool[r["package"]] = dict(r, why="app")
    for kw, lst in sp.items():
        for r in lst:
            pool.setdefault(r["package"], dict(r, why=f"special:{kw}"))

    todo = [p for p, v in profiles.items()
            if not v.get("top_methods") and not v.get("top_classes")]
    print(f"rescan target: {len(todo)} profiles "
          f"(of {len(profiles)}), pool={len(pool)}", flush=True)

    corpus_methods = {}
    corpus_types = {}
    done = 0
    for pkg in todo:
        prof = profiles[pkg]
        meta = pool.get(pkg, {})
        url = prof.get("url") or meta.get("url") or ""
        if not url and meta.get("vc"):
            url = MIRROR + f"{pkg}_{meta['vc']}.apk"
        if not url:
            prof["rescan"] = "NO_URL"
            done += 1
            continue
        dst = f"{APKS}/{pkg}.apk"
        rc = subprocess.run(["curl", "-s", "-L", "-m", CURL_TIMEOUT, "-A", UA,
                             "--max-filesize", str(SIZE_CAP), "-o", dst,
                             url.replace("https://f-droid.org/repo/", MIRROR)]
                            ).returncode
        if rc != 0:
            rc = subprocess.run(["curl", "-s", "-L", "-m", CURL_TIMEOUT,
                                 "-A", UA, "--max-filesize", str(SIZE_CAP),
                                 "-o", dst, url]).returncode
        if rc != 0 or not os.path.exists(dst) or os.path.getsize(dst) < 10000:
            if os.path.exists(dst):
                os.remove(dst)
            prof["rescan"] = "DOWNLOAD_BLOCKED"
            print(f"  [{done+1}/{len(todo)}] {pkg}: BLOCKED", flush=True)
            done += 1
            if done % 10 == 0:
                json.dump(profiles, open(prof_path, "w"), indent=1)
            continue
        cnt, meths, own, libs, ndex, pfail = scan_dex(dst, pkg)
        prof["sha256"] = sha256(dst)
        prof["dexes"] = ndex
        prof["parse_fail"] = pfail
        prof["top_classes"] = cnt.most_common(25)
        prof["top_methods"] = meths.most_common(40)
        prof["own_class_count"] = len(own)
        prof["android_type_count"] = sum(
            v for k, v in cnt.items() if k.startswith("Landroid/"))
        prof["rescan"] = "OK"
        for k, v in meths.items():
            corpus_methods[k] = corpus_methods.get(k, 0) + 1
        for k, v in cnt.items():
            corpus_types[k] = corpus_types.get(k, 0) + 1
        os.remove(dst)
        print(f"  [{done+1}/{len(todo)}] {pkg}: types={len(cnt)} "
              f"methods={len(meths)} fail={pfail}", flush=True)
        done += 1
        if done % 10 == 0:
            json.dump(profiles, open(prof_path, "w"), indent=1)
            emit(corpus_methods, corpus_types, len(profiles))

    json.dump(profiles, open(prof_path, "w"), indent=1)
    emit(corpus_methods, corpus_types, len(profiles))
    print(f"=== RESCAN DONE: {done}/{len(todo)} ===", flush=True)


def emit(corpus_methods, corpus_types, n):
    fam = {}
    for desc, c in corpus_types.items():
        f = "/".join(desc.rstrip(";").split("/")[:4]) + ";"
        fam[f] = fam.get(f, 0) + c
    top_m = sorted(corpus_methods.items(), key=lambda x: -x[1])[:300]
    top_t = sorted(corpus_types.items(), key=lambda x: -x[1])[:120]
    json.dump({"scanned": n,
               "top_classes_corpus": top_t,
               "top_methods_corpus": top_m,
               "class_family_counts": dict(sorted(
                   fam.items(), key=lambda x: -x[1])[:60])},
              open(f"{OUT}/frequency.json", "w"), indent=1)


if __name__ == "__main__":
    main()
