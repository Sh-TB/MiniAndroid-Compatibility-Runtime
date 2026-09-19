#!/usr/bin/env python3
# S65 fast probe — parallel raw.githubusercontent reads, no API quota.
# Detects per candidate: gradle files, androidx/support/compose/ndk/libgdx/
# flutter signatures. Writes /tmp/s65_survey/probes.json.
import json, os, re, concurrent.futures as cf, urllib.request

OUT = "/tmp/s65_survey"
hits = json.load(open(f"{OUT}/keyword_hits.json"))
UA = {"User-Agent": "s65-probe"}

def fetch(url, timeout=12):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

def repo_variants(src):
    m = re.match(r"https?://(?:www\.)?github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", src or "")
    if m: return [(m.group(1), m.group(2))]
    return []

def probe(pkg):
    v = hits[pkg]
    rec = {"name": v["name"], "summary": v["summary"], "license": v["license"],
           "repo": v["source"], "verdict": "NO-GH-REPO"}
    for owner, repo in repo_variants(v["source"]):
        rec["gh"] = f"{owner}/{repo}"
        gd, found, branch = "", False, None
        for br in ("master", "main", "HEAD"):
            for p in ("app/build.gradle", "app/build.gradle.kts", "build.gradle"):
                try:
                    t = fetch(f"https://raw.githubusercontent.com/{owner}/{repo}/{br}/{p}")
                    gd += t; found = True; branch = br; break
                except Exception:
                    continue
            if found: break
        # flutter signature
        flutter = False
        for br in ("master", "main"):
            try:
                fetch(f"https://raw.githubusercontent.com/{owner}/{repo}/{br}/pubspec.yaml")
                flutter = True; break
            except Exception:
                pass
        rec.update({
            "gradle_found": found, "branch": branch,
            "androidx": bool(re.search(r"androidx\.|com\.android\.support|com\.google\.android\.material", gd)),
            "compose": bool(re.search(r"compose", gd, re.I)),
            "ndk": bool(re.search(r"externalNativeBuild|ndkBuild|cmake", gd, re.I)),
            "libgdx": bool(re.search(r"libgdx|gdx-", gd, re.I)),
            "flutter": flutter,
            "minSdk": (lambda m: int(m.group(1)) if m else None)(re.search(r"minSdk(?:Version)?\s*=?\s*(\d+)", gd)),
            "targetSdk": (lambda m: int(m.group(1)) if m else None)(re.search(r"targetSdk(?:Version)?\s*=?\s*(\d+)", gd)),
        })
        rec["verdict"] = "PROBED"
        break
    return pkg, rec

# shortlist = all keyword hits minus known-heavy (fast pass; tier filter after)
sl = json.load(open(f"{OUT}/shortlist_raw.json"))
res = {}
with cf.ThreadPoolExecutor(max_workers=12) as ex:
    futs = [ex.submit(probe, p) for p in sl]
    for f in cf.as_completed(futs):
        try:
            pkg, rec = f.result()
            res[pkg] = rec
        except Exception as e:
            pass

json.dump(res, open(f"{OUT}/probes.json", "w"), indent=1, ensure_ascii=False)

# tier ranking — Tier0: gradle, no androidx/compose/ndk/libgdx/flutter
t0, t1, t2 = [], [], []
for pkg, r in res.items():
    if r.get("verdict") != "PROBED": t2.append(pkg); continue
    if r["flutter"] or r["libgdx"] or r["ndk"]: t2.append(pkg); continue
    if r["gradle_found"] and not r["androidx"] and not r["compose"]: t0.append(pkg)
    else: t1.append(pkg)
print(f"TIER0={len(t0)} TIER1={len(t1)} HEAVY/UNREACHABLE={len(t2)}")
for label, lst in (("TIER-0", t0), ("TIER-1", t1)):
    print(f"--- {label} ---")
    for p in sorted(lst):
        r = res[p]
        flags = "".join(c for c, on in (("A", r.get("androidx")), ("C", r.get("compose")),
                     ("N", r.get("ndk")), ("G", r.get("libgdx")), ("F", r.get("flutter"))) if on) or "-"
        print(f"  {p:52} [{flags}] {r.get('gh','') or r.get('repo','')[:45]}")
json.dump({"tier0": sorted(t0), "tier1": sorted(t1), "heavy": sorted(t2)},
          open(f"{OUT}/tiers.json", "w"), indent=1)
print("PROBE DONE")
