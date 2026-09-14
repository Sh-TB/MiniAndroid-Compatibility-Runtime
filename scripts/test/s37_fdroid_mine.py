#!/usr/bin/env python3
"""S37 corpus wave-3 mining: filter the F-Droid index-v2 for simple game
candidates (tictactoe/dooz family, wordle/word games, dice, other tiny games).
Output: JSON candidate list with package id, latest versionCode, summary.
GitHub-first law satisfied by downstream release probing; this is corpus
discovery, the same F-Droid repo source every prior ledger row used."""
import json
import re
import sys

INDEX = "/tmp/fdroid_index.json"
OUT = "/tmp/s37_candidates.json"

PATTERNS = {
    "tictactoe": re.compile(r"tic.?tac.?toe|dooz|x.?o.?game", re.I),
    "wordle": re.compile(r"wordle|word.?puzzle|word.?game", re.I),
    "dice": re.compile(r"\bdice\b|\bdie\b|yahtzee|\broll\b", re.I),
    "other_game": re.compile(r"\bminesweeper\b|\bsudoku\b|2048|\bpuzzle\b|\bcheckers\b|\breversi\b|\bnim\b|\bhanoi\b", re.I),
}


def localized(d, *keys):
    """index-v2 stores localized fields as {lang: {value: ...}}."""
    cur = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    if isinstance(cur, dict):
        cur = cur.get("en-US") or cur.get("en") or next(iter(cur.values()), None)
    if isinstance(cur, dict):
        cur = cur.get("value")
    return cur


def main():
    with open(INDEX) as f:
        idx = json.load(f)
    pkgs = idx.get("packages", {})
    cands = []
    for pkg, meta in pkgs.items():
        summary = (localized(meta, "summary") or "")[:90]
        name = localized(meta, "name") or ""
        hay = f"{pkg} {name} {summary}"
        cats = localized(meta, "categories") or []
        if not isinstance(cats, list):
            cats = [str(cats)]
        # games category preferred
        is_game = any("Game" in str(c) for c in cats)
        hits = [t for t, rx in PATTERNS.items() if rx.search(hay)]
        if not hits:
            continue
        versions = meta.get("versions", {})
        if not versions:
            continue
        # latest version by added epoch
        best = max(versions.items(), key=lambda kv: kv[1].get("added", 0))
        vc, vmeta = best
        apk_name = vmeta.get("file", {}).get("name")
        size = vmeta.get("file", {}).get("size", 0)
        min_sdk = vmeta.get("minSdkVersion")
        native = bool(vmeta.get("nativecode"))
        # prefer small, pure-java/dex, recent builds
        cands.append({
            "package": pkg, "versionCode": vc, "apk": apk_name,
            "size": size, "minSdk": min_sdk, "native": native,
            "name": name[:60], "summary": summary,
            "tags": hits, "is_game_cat": is_game,
            "url": f"https://f-droid.org/repo/{apk_name}" if apk_name else None,
        })
    cands.sort(key=lambda c: (not c["is_game_cat"], c["native"], c["size"]))
    with open(OUT, "w") as f:
        json.dump(cands, f, indent=1)
    print(f"candidates: {len(cands)}")
    for c in cands[:60]:
        flag = "NATIVE" if c["native"] else "     "
        print(f"{c['package']:<55} vc{c['versionCode']:<8} {c['size']/1e6:6.1f}MB {flag} {c['tags']} {c['summary'][:44]}")


if __name__ == "__main__":
    main()
