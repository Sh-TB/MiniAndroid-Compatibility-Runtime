#!/usr/bin/env python3
"""Mine GitHub topic pages (HTML, no JS/auth) for candidate repos.

Each topic page lists repos server-side; we extract owner/name hrefs that look
like repo links inside the item list. Output: topics_candidates.txt
"""
import concurrent.futures as cf
import re
import urllib.request

TOPICS = [
    "arsc", "apk-parser", "apk", "dex", "dalvik", "compose-desktop",
    "jetpack-compose", "compose-android", "skia", "opengl-es", "vulkan",
    "text-rendering", "text-layout", "harfbuzz", "freetype", "font-rendering",
    "lottie", "rlottie", "minimp3", "audio-player", "sqlite", "image-decoding",
    "png-decoder", "webp", "svg-renderer", "renderer", "software-rendering",
    "android-runtime", "android-emulator", "fdroid", "libgdx", "2d-game",
    "tictactoe", "exoplayer", "media3", "androidx", "android-ui", "view-rendering",
    "java-game-library", "foss", "open-source-android", "android-app",
]
UA = {"User-Agent": "miniandroid-mining/009 (research cataloging)"}

REPO_HREF = re.compile(r'href="/([A-Za-z0-9_.\-]+)/([A-Za-z0-9_.\-]+)"')
BAD = {
    "features", "topics", "collections", "trending", "events", "about", "pricing",
    "security", "login", "join", "site", "organizations", "sponsors", "customer-stories",
    "readme", "enterprise", "team", "jobs", "press", "blog", "docs", "github-copilot",
    "marketplace", "explore", "contact", "terms", "privacy", "mockups", "apps", "search",
    "settings", "notifications", "watching", "new", "import", "orgs", "account",
    "github", "git", "codespaces", "issues", "pulls", "codespaces", "education",
    "linkedin", "twitter", "facebook", "youtube", "static", "assets", "cdn-cgi",
    "home", "explore", "topics", "about", "solutions",
}


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(1500000).decode("utf-8", errors="replace")


def mine_topic(topic):
    found = []
    for page in ("", "?page=2"):
        try:
            html = fetch(f"https://github.com/topics/{topic}{page}")
        except Exception:  # noqa: BLE001
            continue
        # only take hrefs from the article item list region to reduce noise
        items = re.findall(r'<h3 class="h3 lh-condensed">.*?href="/([A-Za-z0-9_.\-]+)/([A-Za-z0-9_.\-]+)"',
                           html, re.S)
        if not items:  # layout fallback: any repo-looking link not in BAD and not a file
            for owner, name in REPO_HREF.findall(html):
                o, n = owner.lower(), name
                if o in BAD or n.lower() in BAD or n.endswith((".png", ".svg", ".ico", ".js", ".css", ".json")):
                    continue
                items.append((owner, name))
        for owner, name in items:
            if owner.lower() in BAD or name.lower() in BAD:
                continue
            found.append(f"{owner}/{name}")
    return list(dict.fromkeys(found))


def main():
    cands = {}
    with cf.ThreadPoolExecutor(max_workers=6) as ex:
        futs = {ex.submit(mine_topic, t): t for t in TOPICS}
        for fut in cf.as_completed(futs):
            t = futs[fut]
            try:
                got = fut.result()
            except Exception as e:  # noqa: BLE001
                got = []
            cands[t] = got
            print(f"topic={t:22s} repos={len(got)}", flush=True)
    all_repos = []
    for t, got in cands.items():
        for r in got:
            all_repos.append(r)
    all_repos = list(dict.fromkeys(all_repos))
    with open("/home/z/my-project/scripts/p1_mining/topics_candidates.txt", "w") as f:
        for t, got in cands.items():
            for r in got:
                f.write(f"{t}\t{r}\n")
    print(f"TOTAL unique topic candidates: {len(all_repos)}")


if __name__ == "__main__":
    main()
