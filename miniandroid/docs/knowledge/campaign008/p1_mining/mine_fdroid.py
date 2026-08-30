#!/usr/bin/env python3
"""Mine F-Droid (HTML-only, via curl) for real-app corpus candidates.

Sources used:
  - https://f-droid.org/en/packages/        (index page, ~261 newest packages)
  - https://search.f-droid.org/?q=KEYWORD   (server-rendered search results)
  - https://f-droid.org/en/packages/PKG/    (package page: source link + categories)

Output:
  fdroid_index_packages.txt   (package ids from index)
  fdroid_search_results.json  (keyword -> [package ids])
  fdroid_packages.json        (package -> {categories, source_url, repo_hint})
"""
import concurrent.futures as cf
import json
import re
import subprocess

UA = "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0"
PKG = re.compile(r'href="/en/packages/([A-Za-z0-9_.]+?)/"')
CAT = re.compile(r'href="/en/categories2?/([a-zA-Z0-9\-]+)/"')


def curl(url, timeout=30):
    p = subprocess.run(["curl", "-sL", "--max-time", str(timeout), "-A", UA, url],
                       capture_output=True, text=True)
    return p.stdout or ""


def get_index_packages():
    html = curl("https://f-droid.org/en/packages/")
    pkgs = list(dict.fromkeys(PKG.findall(html)))
    return pkgs


def search_fdroid(kw):
    html = curl(f"https://search.f-droid.org/?q={kw.replace(' ', '+')}&lang=en")
    return list(dict.fromkeys(PKG.findall(html)))


def package_details(pkg):
    html = curl(f"https://f-droid.org/en/packages/{pkg}/")
    if "404 Page Not Found" in html[:3000]:
        return pkg, {"categories": [], "source_url": "", "repo_hint": "", "status": "404"}
    cats = list(dict.fromkeys(CAT.findall(html)))
    m = re.search(r'href="(https?://[^"]+)"[^>]*>\s*(?:<[^>]+>\s*)*Source Code', html)
    src = m.group(1).rstrip("/") if m else ""
    if not src:
        m2 = re.search(r'(https?://(?:github\.com|gitlab\.com|codeberg\.org|bitbucket\.org)/[A-Za-z0-9_.\-]+/[A-Za-z0-9_.\-]+)', html)
        src = m2.group(1).rstrip("/").rstrip(".") if m2 else ""
    return pkg, {"categories": cats, "source_url": src, "repo_hint": "", "status": "ok"}


def main():
    import os
    base = "/home/z/my-project/scripts/p1_mining"
    index = get_index_packages()
    with open(f"{base}/fdroid_index_packages.txt", "w") as f:
        f.write("\n".join(index))
    print(f"index packages: {len(index)}", flush=True)

    keywords = ["dooz", "retrowars", "pixel player", "brick", "compose", "tic tac toe",
                "simple gallery", "webview", "stopwatch", "calculator", "notes", "todo",
                "file manager", "music player", "video player", "sqlite", "chess",
                "sudoku", "2048", "solitaire", "weather", "keyboard", "launcher",
                "libgdx", "game", "media player", "rss reader", "password", "map",
                "podcast", "terminal", "sms", "camera", "clock"]
    searches = {}
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(search_fdroid, k): k for k in keywords}
        for fut in cf.as_completed(futs):
            k = futs[fut]
            try:
                searches[k] = fut.result()
            except Exception:  # noqa: BLE001
                searches[k] = []
            print(f"search '{k}': {len(searches[k])} pkgs", flush=True)
    json.dump(searches, open(f"{base}/fdroid_search_results.json", "w"), indent=1)

    # Candidate set: index + all search hits (capped per keyword)
    cand = list(index)
    for k, pkgs in searches.items():
        cand += pkgs[:12]
    cand = list(dict.fromkeys(cand))
    print(f"package-detail fetches: {len(cand)}", flush=True)

    details = {}
    with cf.ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(package_details, p): p for p in cand}
        done = 0
        for fut in cf.as_completed(futs):
            p = futs[fut]
            try:
                pkg, det = fut.result()
                details[pkg] = det
            except Exception:  # noqa: BLE001
                pass
            done += 1
            if done % 40 == 0:
                print(f"  pkg pages {done}/{len(cand)}", flush=True)
    json.dump(details, open(f"{base}/fdroid_packages.json", "w"), indent=1)
    withsrc = sum(1 for v in details.values() if v["source_url"])
    print(f"details: {len(details)}, with source link: {withsrc}")


if __name__ == "__main__":
    main()
