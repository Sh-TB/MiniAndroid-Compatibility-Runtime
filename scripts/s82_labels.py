#!/usr/bin/env python3
"""s82_labels.py — S82 §21/§23: create the S82 label taxonomy idempotently.
Status labels and failure labels are SEPARATE families (§21 last law)."""
import json
import urllib.request

TOKEN = open("/home/z/my-project/.secrets/gh_token").read().strip()
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
API = f"https://api.github.com/repos/{REPO}"

# (name, color, description)
LABELS = [
    # families / campaign
    ("compatibility", "0e8a16", "S82 per-title compatibility record"),
    ("game", "5db2a6", "Title is a game"),
    ("app", "1d76db", "Title is a non-game app"),
    ("mandatory", "d93f0b", "Mandatory gate title (P9 / TimeLimit)"),
    ("open-source", "8f4a2a", "Open-source title"),
    ("fdroid", "6a737d", "Sourced from F-Droid with provenance"),
    # status ladder (S82 §7) — evidence-gated, never self-granted
    ("state-not-loaded", "ededed", "Did not load"),
    ("state-loaded", "c2e0c6", "Loaded only, no render"),
    ("state-oncreate", "fef2c0", "Reached onCreate boundary"),
    ("state-nonblank", "d4c5f9", "Pixels produced but two-color/blank (visual failure §16)"),
    ("state-rendered", "bfd4f2", "Rendered non-trivial pixels"),
    ("state-graphics-nontrivial", "0366d6", "Graphics beyond text (icons/images/widgets)"),
    ("state-interactive", "0e8a16", "Input dispatched and screen responded"),
    ("state-state-changed", "238636", "Before/after state transition proven"),
    ("state-semantically-correlated", "1a7f37", "L4: reference comparison structural+visual"),
    ("state-visually-verified", "7ee787", "L5: human-review verified (never self-granted)"),
    # execution/verification flags
    ("executed", "a2eeef", "Really executed in a session"),
    ("not-tested", "e1e4e8", "Record exists, no execution yet (honest §26)"),
    ("need-input-gate", "f9d0c4", "Awaiting interaction minimum gate"),
    # failure labels (separate family from status, §21)
    ("fail-crash", "b60205", "Crash"),
    ("fail-npe", "d93f0b", "NullPointerException"),
    ("fail-oncreate", "e99695", "Failure inside onCreate (F-NEW-156 family)"),
    ("fail-hang", "fbca04", "Hang/timeout"),
    ("fail-anr", "d4c5f9", "ANR"),
    ("fail-resource", "f9d0c4", "Resource missing/lookup failure"),
    ("fail-drawable", "c2e0c6", "Drawable subsystem failure"),
    ("fail-bitmap", "bef5c0", "Bitmap decode/draw failure"),
    ("fail-image", "bfdadc", "Image decoded but not rendered / render gap"),
    ("fail-icon", "fef2c0", "Icon pixels missing"),
    ("fail-text", "ffd782", "Text rendering failure"),
    ("fail-font", "fef2c0", "Font/glyph failure"),
    ("fail-layout", "d4c5f9", "Layout/measure failure"),
    ("fail-input", "b60205", "Input dispatch failure"),
    ("fail-state", "e99695", "State-change failure"),
    ("fail-lifecycle", "f9d0c4", "Lifecycle failure"),
    ("fail-canvas", "c2e0c6", "Canvas/paint failure"),
    ("fail-palette", "bfd4f2", "Palette/color-variety failure (two-color §16)"),
    ("fail-color", "006b75", "Color/theme color failure"),
    ("fail-animation", "5db2a6", "Animation failure"),
    ("fail-storage", "1d76db", "Storage failure"),
    ("fail-network", "0e8a16", "Network failure"),
    ("fail-unknown", "ffffff", "Unclassified failure"),
    # workflow
    ("root-cause", "ee0701", "Runtime root-cause issue (shared across titles)"),
    ("common-runtime", "8a4be8", "Failure owned by common runtime code"),
    ("app-specific", "9966e6", "Failure owned by the app"),
    ("image-decoded-vs-rendered-gap", "b60205", "IMAGE_DECODED_VS_RENDERED_GAP"),
]


def req(method, url, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, method=method, data=data,
                               headers={"Authorization": f"Bearer {TOKEN}",
                                        "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(r) as resp:
        return json.loads(resp.read().decode() or "{}")


def main():
    # existing labels
    ex = {}
    page = 1
    while True:
        with urllib.request.urlopen(urllib.request.Request(
                f"{API}/labels?per_page=100&page={page}",
                headers={"Authorization": f"Bearer {TOKEN}"})) as r:
            batch = json.loads(r.read().decode())
        if not batch:
            break
        ex.update({l["name"]: l for l in batch})
        page += 1
    created, updated = 0, 0
    for name, color, desc in LABELS:
        if name in ex:
            req("PATCH", f"{API}/labels/{urllib.parse.quote(name)}",
                {"color": color, "description": desc})
            updated += 1
        else:
            req("POST", f"{API}/labels", {"name": name, "color": color,
                                          "description": desc})
            created += 1
    print(f"labels created={created} updated={updated} total={len(LABELS)}")


if __name__ == "__main__":
    import urllib.parse
    main()
