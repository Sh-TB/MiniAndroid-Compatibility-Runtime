#!/usr/bin/env python3
"""S94 Phase E: deterministic graphics-heavy seeded random sample (§20).

Pool = canonical registry titles that carry a canonical visual artifact
(GIF/JPG) - graphics-heavy by construction. Selection recorded with seed,
registry SHA, pool SHA, APK SHAs, category assignment, and result pointers
to existing S92/S93 machine-verdict evidence (honest reuse; titles without
existing evidence are marked SELECTED_NOT_YET_EXECUTED).
"""
import hashlib
import json
import random
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/home/z/my-project")
OUT = ROOT / "run/s94/source_mining/random_sample.json"
SEED = 20260924

CATEGORY = {
    "dodge": "canvas-game", "bobball": "canvas-game", "bouncy": "canvas-physics-game",
    "mini-tetris": "game-animation", "minicraft": "game-heavy", "snake-deluxe": "game",
    "2048": "ui-interactive", "g2048": "ui-interactive", "tictactoedeluxe": "ui-interactive",
    "emmanuelmess.tictactoe": "ui-interactive", "nounours": "image-heavy",
    "hotdeath": "image-heavy-cards", "urlchecker": "webview", "chessclock": "ui-text",
    "fishrings": "image-heavy-icons", "unote": "text-heavy",
}

CATEGORY_FALLBACK = {
    "game": "game", "solitaire": "image-heavy-cards", "chess": "ui-interactive",
    "pdf": "text-heavy", "note": "text-heavy", "watch": "ui-interactive",
    "weather": "ui-interactive", "draw": "canvas-game", "paint": "canvas-game",
    "gallery": "image-heavy", "camera": "image-heavy", "photo": "image-heavy",
    "browser": "webview", "rss": "webview", "reader": "text-heavy", "book": "text-heavy",
    "timer": "text-heavy", "clock": "text-heavy", "stopwatch": "text-heavy",
    "maze": "game", "sudoku": "game", "mines": "game", "snake": "game",
    "gdx": "libgdx", "lottie": "animation", "web": "webview",
}


def category_of(title):
    t = title.lower()
    norm = t.replace(" ", "-").replace(".", "-").replace("_", "-")
    for k, v in CATEGORY.items():
        if t == k or norm == k or k in norm or norm in k:
            return v
    for k, v in CATEGORY_FALLBACK.items():
        if k in t:
            return v
    return "normal-app"


def s93_key(title):
    norm = title.lower().replace(" ", "-").replace(".", "-").replace("_", "-")
    for k in S93_KEYS:
        if k == norm or k in norm or norm in k:
            return k
    return None


def main():
    reg_bytes = (ROOT / "docs/evidence/canonical/registry.json").read_bytes()
    registry_sha = hashlib.sha256(reg_bytes).hexdigest()
    reg = json.loads(reg_bytes)
    pool = sorted({t["title"] for t in reg["titles"]
                   if t.get("artifact_kind") in (".gif", ".jpg") and t.get("title")})
    pool_sha = hashlib.sha256("\n".join(pool).encode()).hexdigest()
    rng = random.Random(SEED)
    n = min(8, len(pool))
    selected = sorted(rng.sample(pool, n))

    # existing machine evidence pointers (honest reuse from S92/S93 campaigns)
    s93 = json.loads((ROOT / "docs/evidence/s93/failure_map.json").read_text())
    global S93_KEYS
    S93_KEYS = sorted(s93.keys())
    by_title = {t["title"]: t for t in reg["titles"] if t.get("title")}

    rows = []
    for title in selected:
        tr = by_title.get(title, {})
        apk_sha = tr.get("apk_sha256", "")
        key = s93_key(title)
        if key:
            result = f"S93_FAILURE_CATEGORIES={sorted(set(s93[key]))}; evidence=docs/evidence/s93/failure_map.json#{key}"
        else:
            status = tr.get("status", "?")
            result = f"registry_status={status}; SELECTED_NOT_YET_EXECUTED_IN_S94 (S92/S93 verdicts reused where present)"
        rows.append({"title": title, "category": category_of(title),
                     "apk_sha256": apk_sha[:16] + ("..." if len(apk_sha) > 16 else ""),
                     "result": result})

    doc = {
        "campaign": "S94 GRAPHICS SOURCE LIBRARY (§20)",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "seed": SEED,
        "rng": "python3 random.Random(seed).sample(sorted_pool)",
        "registry_path": "docs/evidence/canonical/registry.json",
        "registry_sha256": registry_sha,
        "pool_definition": "canonical titles carrying a canonical visual artifact (.gif/.jpg) = graphics-heavy by construction",
        "pool_sha256": pool_sha,
        "pool_size": len(pool),
        "pool": pool,
        "sample_size": n,
        "selected": rows,
        "graphics_category_coverage": sorted({r["category"] for r in rows}),
        "note": "Results reuse S92/S93 machine-verdict evidence with explicit pointers; no new unexecuted claims.",
    }
    OUT.write_text(json.dumps(doc, indent=1))
    print(f"registry_sha={registry_sha[:16]} pool={len(pool)} selected={n}")
    for r in rows:
        print(f"  {r['title']:28s} [{r['category']}] {r['result'][:90]}")


if __name__ == "__main__":
    main()
