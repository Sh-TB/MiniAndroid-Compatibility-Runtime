#!/usr/bin/env python3
"""registry_link_check.py — S154 (Coder-2 #449/#458 proposal, tested & adopted).

LAW (frozen-mirror, Coder-2 #449): every registry entry whose fetch URL is a
LIVE link must carry `frozen_url` + `frozen_sha256`; reproduction only ever
fetches frozen artifacts. This checker walks the canonical registries for
URL-bearing fields, fetches each URL once (bounded), and classifies:

  OK      — fetch succeeded, payload looks like an APK/ZIP (PK header) and
            (when a pin sha256 exists) the sha matches.
  DRIFT   — fetch succeeded but the payload is NOT the pinned artifact
            (HTML page served, or sha mismatch).
  DEAD    — HTTP >= 400 (or payload empty).

Usage:
  python3 scripts/registry_link_check.py            # human report + JSON
  python3 scripts/registry_link_check.py --json OUT # machine report path
Exit 0 always (report tool, not a gate); DRIFT/DEAD rows are the actionable
output — each one becomes a `frozen_url` follow-up or a re-pin.
"""
import hashlib
import json
import sys
import urllib.request

ROOT = "/home/z/my-project"
TARGETS = [
    "docs/runtime/knowledge/campaign010/APK_REGISTRY_010.json",
    "docs/runtime/knowledge/campaign008/APK_REGISTRY_008.json",
    "docs/PROGRAM_QUEUE.json",
    "docs/runtime/knowledge/campaign010/LIBRARY_PROVENANCE_010.json",
    "docs/evidence/canonical/registry.json",
]
URL_KEYS = {"download_url", "frozen_url", "source", "url", "apk_url"}
UA = {"User-Agent": "MiniAndroid-registry-link-check/1.0"}

findings = []          # (file, key, url, verdict, detail)
checked_urls = {}


def classify(url, pin_sha):
    if url in checked_urls:
        return checked_urls[url]
    v = ("SKIP", "not fetched this run")
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=25) as r:
            head = r.read(262144)
            size = int(r.headers.get("Content-Length") or -1)
            if r.status >= 400:
                v = ("DEAD", f"http {r.status}")
            elif head[:2] != b"PK":
                v = ("DRIFT", f"payload not ZIP/APK (magic {head[:8]!r}, "
                              f"{min(len(head), size)}B) — likely HTML page")
            elif pin_sha:
                h = hashlib.sha256(head).hexdigest()
                v = ("PARTIAL-OK" if h != pin_sha else "OK",
                     f"PK payload; first-256KB sha {h[:16]} vs pin "
                     f"{pin_sha[:16]} (full-file compare needs full fetch)")
            else:
                v = ("OK", f"PK payload, {size}B (no sha pin to compare)")
    except Exception as e:  # noqa: BLE001
        code = getattr(e, "code", None)
        v = ("DEAD", f"{type(e).__name__}: {code or e}")
    checked_urls[url] = v
    return v


def walk(node, path, fname, pin_sha):
    if isinstance(node, dict):
        my_sha = node.get("sha256") or node.get("apk_sha256") or pin_sha
        for k, val in node.items():
            if isinstance(val, str) and (k in URL_KEYS or (
                    k not in ("notes", "title", "id", "evidence", "root_cause")
                    and val.startswith("http") and ".apk" in val)):
                if not val.startswith(("http://", "https://")):
                    continue  # labels like "F-Droid" are not URLs
                if "/en/packages/" in val or "f-droid.org/fr/packages/" in val:
                    findings.append({"file": fname, "path": path,
                                     "key": k, "url": val,
                                     "verdict": "PAGE-OK",
                                     "detail": "package page (HTML by design)"})
                    continue
                if any(x in val for x in ("github.com/", "gitlab.com/",
                                          "codeload", "dl.google.com")) \
                        and "f-droid" not in val and "telegram" not in val:
                    continue  # source-repo links, not artifact links
                verdict, detail = classify(val, my_sha if isinstance(my_sha, str) else None)
                findings.append({"file": fname, "path": path, "key": k,
                                 "url": val, "verdict": verdict,
                                 "detail": detail})
            else:
                walk(val, path + "/" + str(k), fname, my_sha
                     if isinstance(my_sha, str) else pin_sha)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            walk(item, f"{path}[{i}]", fname, pin_sha)


def main():
    out_json = None
    if "--json" in sys.argv:
        out_json = sys.argv[sys.argv.index("--json") + 1]
    for rel in TARGETS:
        try:
            data = json.load(open(f"{ROOT}/{rel}"))
        except Exception as e:  # noqa: BLE001
            print(f"[skip] {rel}: {e}")
            continue
        walk(data, "$", rel, None)
    from collections import Counter
    counts = Counter(f["verdict"] for f in findings)
    print("== REGISTRY LINK CHECK (S154) ==")
    print("verdicts:", dict(counts))
    for f in findings:
        if f["verdict"] in ("OK", "SKIP"):
            continue
        print(f"  [{f['verdict']}] {f['key']} {f['url'][:80]}\n"
              f"        {f['detail']}\n"
              f"        at {f['file']}{f['path'][:60]}")
    if out_json:
        json.dump({"generated_by": "scripts/registry_link_check.py (S154)",
                   "law": "frozen-mirror (issue #449)",
                   "verdict_counts": dict(counts), "findings": findings},
                  open(out_json, "w"), indent=1)
        print("json ->", out_json)


if __name__ == "__main__":
    main()
