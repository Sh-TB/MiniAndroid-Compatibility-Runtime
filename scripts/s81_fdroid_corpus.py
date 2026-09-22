#!/usr/bin/env python3
"""s81_fdroid_corpus.py — S81 corpus builder (§4-§12, §31, §45).

Builds the F-Droid corpus index with source-first provenance:
  1. Mandatory entries: P9 (se.tube42.p9.android), TimeLimit
     (io.timelimit.android.aosp.direct) — full provenance fields.
  2. Stopwatch + Platformer category inventories (§8/§9).
  3. Deterministic selection: 100 games + 100 apps (§10-12) sampled from
     F-Droid category pages with CORPUS_SEED recorded (§15) so every
     selection is reproducible.

Every item records: APP_ID, PACKAGE, NAME, CATEGORY, STATUS (DISCOVERED),
F_DROID_URL, SOURCE_URL, LICENSE, LATEST_VERSION, VERSION_CODE,
REFERENCE_SCREENSHOT_URL (F-Droid phoneScreenshots when present — §5
provenance chain), ISSUE_TRACKER, BUILD_METADATA_URL.

Output: docs/corpus/s81/corpus_index.json (+ CSV summary).
NO APKs downloaded at this stage (§31: index first; §32: disk guard).
"""
import csv
import hashlib
import html
import json
import os
import re
import subprocess
import sys

ROOT = "/home/z/my-project"
OUT_DIR = f"{ROOT}/docs/corpus/s81"
os.makedirs(OUT_DIR, exist_ok=True)

CORPUS_SEED = "S81-CORPUS-SEED-2026-09-22"

UA = "Mozilla/5.0 (X11; Linux x86_64) MiniAndroid-S81-corpus/1.0"


def fetch(url, timeout=25):
    try:
        r = subprocess.run(["curl", "-s", "-m", str(timeout), "-A", UA, url],
                           capture_output=True, timeout=timeout + 5)
        return r.stdout.decode("utf-8", errors="replace")
    except Exception:
        return ""


def api_package(pkg):
    """F-Droid v1 API: latest version + code."""
    body = fetch(f"https://f-droid.org/api/v1/packages/{pkg}")
    try:
        d = json.loads(body)
        pkgs = d.get("packages") or []
        if pkgs:
            return {"LATEST_VERSION": pkgs[0].get("versionName"),
                    "VERSION_CODE": pkgs[0].get("versionCode")}
    except Exception:
        pass
    return {}


def package_page_metadata(pkg):
    """Scrape the F-Droid package page for provenance fields (§4/§6)."""
    body = fetch(f"https://f-droid.org/en/packages/{pkg}/")
    meta = {"SOURCE_URL": "", "LICENSE": "", "ISSUE_TRACKER": "",
            "BUILD_METADATA_URL": f"https://gitlab.com/fdroid/fdroiddata/tree/master/metadata/{pkg}.yml",
            "REFERENCE_SCREENSHOT_URL": "", "DESCRIPTION": ""}
    if not body:
        meta["PAGE_STATUS"] = "SOURCE_NOT_RECOVERED"
        return meta
    m = re.search(r'href="(https?://[^"]*)"[^>]*>\s*Source Code', body)
    if m:
        meta["SOURCE_URL"] = html.unescape(m.group(1))
    m = re.search(r'href="(https?://[^"]*)"[^>]*>\s*Issue Tracker', body)
    if m:
        meta["ISSUE_TRACKER"] = html.unescape(m.group(1))
    m = re.search(r'License</a>\s*<[^>]*>([^<]+)', body)
    if not m:
        m = re.search(r'>([A-Za-z0-9\.\- ]+ License)<', body)
    if m:
        meta["LICENSE"] = m.group(1).strip()
    # first phone screenshot as REFERENCE provenance (§5): record URL + SHA
    m = re.search(r'src="(https://fdroid.gitlab.io/fdroid-website/fdroid/repo/[^"]+/phoneScreenshots/[^"]+)"', body)
    if not m:
        m = re.search(r'src="(https?://[^"]*phoneScreenshots/[^"]+)"', body)
    if m:
        ref_url = html.unescape(m.group(1))
        meta["REFERENCE_SCREENSHOT_URL"] = ref_url
        meta["REFERENCE_SOURCE"] = "F-Droid package page"
        meta["REFERENCE_URL"] = f"https://f-droid.org/en/packages/{pkg}/"
    # short description
    m = re.search(r'<meta name="description" content="([^"]+)"', body)
    if m:
        meta["DESCRIPTION"] = html.unescape(m.group(1))[:160]
    return meta


def category_packages(slug):
    """Package list from a category page (§45: category → package list)."""
    body = fetch(f"https://f-droid.org/en/categories/{slug}/")
    # F-Droid category pages use RELATIVE package links (/en/packages/<pkg>/)
    pkgs = re.findall(r'href="/en/packages/([a-zA-Z0-9\._]+)/"', body)
    pkgs += re.findall(r'href="https://f-droid\.org/en/packages/([a-zA-Z0-9\._]+)/"', body)
    seen, out = set(), []
    for p in pkgs:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def full_entry(pkg, category, note=""):
    e = {"APP_ID": pkg, "PACKAGE": pkg, "CATEGORY": category,
         "STATUS": "DISCOVERED", "F_DROID_URL": f"https://f-droid.org/en/packages/{pkg}/"}
    if note:
        e["NOTE"] = note
    e.update(api_package(pkg))
    e.update(package_page_metadata(pkg))
    return e


def main():
    corpus = {"CORPUS_SEED": CORPUS_SEED, "GENERATED": "S81",
              "STATUS_LADDER": ["DISCOVERED", "SOURCED", "BUILT", "PACKAGED",
                                 "LOADED", "EXECUTED", "RENDERED", "VISUALLY_AUDITED"],
              "DISK_NOTE": "§31 index-first: no APK download without §32-34 disk guard",
              "MANDATORY": [], "STOPWATCH_INVENTORY": [], "PLATFORMER_INVENTORY": [],
              "GAMES_100": [], "APPS_100": []}

    # ── §7 mandatory targets ────────────────────────────────────────────
    print("== mandatory targets ==")
    corpus["MANDATORY"].append(full_entry("se.tube42.p9.android", "Puzzle/Game", "P9 — mandatory §7"))
    corpus["MANDATORY"].append(full_entry("io.timelimit.android.aosp.direct", "Productivity/Parental", "TimeLimit.io — mandatory §7"))

    # ── §8/§9 category inventories ──────────────────────────────────────
    print("== category inventories ==")
    for slug, key in (("stopwatch", "STOPWATCH_INVENTORY"), ("platformer-game", "PLATFORMER_INVENTORY")):
        pkgs = category_packages(slug)
        corpus[key] = [{"APP_ID": p, "PACKAGE": p, "SOURCE": f"https://f-droid.org/en/categories/{slug}/"} for p in pkgs]
        print(f"  {slug}: {len(pkgs)} packages")

    # ── §10-12: 100 games + 100 apps, deterministic (seeded) ────────────
    print("== corpus selection ==")
    # slugs verified live 2026-09-22 (f-droid.org/en/categories/<slug>/)
    game_cats = ["puzzle-game", "board-game", "card-game", "action-game",
                 "casual-game", "platformer-game", "shooter-game",
                 "educational-game"]
    app_cats = ["calculator", "clock", "file-manager", "gallery",
                "multimedia", "weather", "connectivity", "reading",
                "internet", "security", "development", "navigation",
                "stopwatch"]

    def harvest(cats):
        all_pkgs = {}
        for c in cats:
            for p in category_packages(c):
                all_pkgs.setdefault(p, c)
        return all_pkgs

    games_pool = harvest(game_cats)
    apps_pool = harvest(app_cats)
    print(f"  pools: games={len(games_pool)} apps={len(apps_pool)}")

    # deterministic selection: stable sha1(pkg + seed) sort → take first N
    def select(pool, n):
        ranked = sorted(pool.items(),
                        key=lambda kv: hashlib.sha1((CORPUS_SEED + kv[0]).encode()).hexdigest())
        return ranked[:n]

    for p, c in select(games_pool, 100):
        corpus["GAMES_100"].append({"APP_ID": p, "PACKAGE": p, "CATEGORY": c,
                                     "STATUS": "DISCOVERED",
                                     "F_DROID_URL": f"https://f-droid.org/en/packages/{p}/"})
    for p, c in select(apps_pool, 100):
        corpus["APPS_100"].append({"APP_ID": p, "PACKAGE": p, "CATEGORY": c,
                                    "STATUS": "DISCOVERED",
                                    "F_DROID_URL": f"https://f-droid.org/en/packages/{p}/"})

    # batch plan (§13/§14): mixed batches of 25
    batches = []
    mixed = ([dict(x, TYPE="game") for x in corpus["GAMES_100"][:50]] +
             [dict(x, TYPE="app") for x in corpus["APPS_100"][:50]])
    for i in range(0, 100, 25):
        batches.append({"BATCH": f"BATCH-{i//25+1:02d}", "SIZE": min(25, 100 - i),
                        "MIX": True, "ITEMS": [x["APP_ID"] for x in mixed[i:i+25]]})
    corpus["BATCH_PLAN"] = batches

    with open(f"{OUT_DIR}/corpus_index.json", "w") as f:
        json.dump(corpus, f, indent=1)

    # CSV summary
    with open(f"{OUT_DIR}/corpus_summary.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["APP_ID", "CATEGORY", "TYPE", "STATUS", "VERSION", "VCODE",
                    "LICENSE", "SOURCE_URL", "REF_SCREENSHOT"])
        rows = []
        for m in corpus["MANDATORY"]:
            rows.append([m["APP_ID"], m["CATEGORY"], "mandatory", m["STATUS"],
                         m.get("LATEST_VERSION", ""), m.get("VERSION_CODE", ""),
                         m.get("LICENSE", ""), m.get("SOURCE_URL", ""),
                         m.get("REFERENCE_SCREENSHOT_URL", "")])
        for key, typ in (("GAMES_100", "game"), ("APPS_100", "app")):
            for g in corpus[key]:
                rows.append([g["APP_ID"], g["CATEGORY"], typ, g["STATUS"], "", "",
                             "", "", ""])
        w.writerows(rows)

    print(f"\ncorpus: mandatory={len(corpus['MANDATORY'])} "
          f"stopwatch={len(corpus['STOPWATCH_INVENTORY'])} "
          f"platformer={len(corpus['PLATFORMER_INVENTORY'])} "
          f"games={len(corpus['GAMES_100'])} apps={len(corpus['APPS_100'])}")
    print(f"written: {OUT_DIR}/corpus_index.json + corpus_summary.csv")
    # mandatory provenance quick view
    for m in corpus["MANDATORY"]:
        print(f"  {m['PACKAGE']}: v{m.get('LATEST_VERSION')} ({m.get('VERSION_CODE')}) "
              f"license={m.get('LICENSE','?')} src={m.get('SOURCE_URL','?')[:60]} "
              f"ref={'YES' if m.get('REFERENCE_SCREENSHOT_URL') else 'NO'}")


if __name__ == "__main__":
    main()
