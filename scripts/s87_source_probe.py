#!/usr/bin/env python3
"""s87_source_probe.py — PHASE 6 source-first corpus preparation.

For each probe title:
  1. resolve upstream source repo via fdroiddata metadata (or registry pin)
  2. download the pinned APK (verify SHA256 against registry pin when present)
  3. download the upstream source tarball (codeload HEAD)
Outputs run/s87/probe/manifest.json.
"""
import hashlib, json, os, subprocess, sys, urllib.request

ROOT = "/home/z/my-project"
OUT = f"{ROOT}/run/s87/probe"
REG = {t["package"]: t for t in json.load(
    open(f"{ROOT}/docs/evidence/canonical/registry.json"))["titles"]}

FD_API = "https://f-droid.org/api/v1/packages/"
FD_REPO = "https://f-droid.org/repo/"
FDATA = ("https://gitlab.com/fdroid/fdroiddata/-/raw/master/metadata/"
         "{pkg}.yml")

PROBES = [
    # pkg, family reason
    "org.secuso.privacyfriendlydame",      # secuso scaffold ×8 fan-out
    "org.secuso.privacyfriendly2048",      # secuso scaffold 2nd probe
    "de.tobiasbielefeld.solitaire",        # solitaire family ×5
    "com.sidhant.bubbleshooter",           # sidhant family ×3
    "eu.veldsoft.no.thanks",               # veldsoft control (3 siblings work)
    "jwtc.android.chess",                  # classic View chess UI
    "com.galaxyrio.sudokusolver",          # puzzle utility
    "com.newsblur",                        # text-heavy heavy app
    "io.github.hathibelagal.mykanji",      # L0 small game
    "app.halma",                           # L1 board game
]

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()

def fetch(url, dst, timeout=240):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MiniAndroid-S87/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r, open(dst, "wb") as f:
            while True:
                chunk = r.read(1 << 20)
                if not chunk: break
                f.write(chunk)
        return True
    except Exception as e:
        print(f"  fetch fail {url}: {e}")
        return False

def parse_yaml_minimal(text):
    """Extract Repo, and Build versionCode/VersionName list from fdroiddata yml."""
    repo = None
    builds = []
    in_builds = False
    for line in text.splitlines():
        if line.startswith("Repo:"):
            repo = line.split(":", 1)[1].strip()
        if line.startswith("Builds:"):
            in_builds = True
            continue
        if in_builds:
            s = line.strip()
            if line.startswith("  - ") or s.startswith("versionName:"):
                pass
            if s.startswith("versionCode:"):
                try: builds.append(int(s.split(":", 1)[1].strip()))
                except ValueError: pass
            if s.startswith("Disable:") and builds:
                builds.pop()  # disabled build — skip last
    return repo, builds

def api_pkgs(pkg):
    return json.load(urllib.request.urlopen(FD_API + pkg, timeout=30)).get("packages", [])

def main():
    os.makedirs(OUT, exist_ok=True)
    manifest = {}
    for pkg in PROBES:
        print(f"== {pkg}")
        rec = {"pkg": pkg, "registered": bool(REG.get(pkg)),
              "reg_sha": (REG.get(pkg, {}).get("apk_sha256") or ""),
              "reg_version": (REG.get(pkg, {}).get("version") or "")}
        # fdroiddata metadata for source repo + version codes
        yml = f"{OUT}/meta/{pkg}.yml"
        ok = fetch(FDATA.format(pkg=pkg), yml, timeout=60)
        repo, vcs = None, []
        if ok:
            repo, vcs = parse_yaml_minimal(open(yml, errors="replace").read())
        rec["repo"] = repo
        rec["version_codes"] = vcs[-6:]
        # choose version code: prefer one matching registered version/sha via API
        chosen = None
        try:
            api = json.load(urllib.request.urlopen(FD_API + pkg, timeout=30))
            rec["fdroid_versions"] = [(p.get("versionName"), p.get("versionCode"))
                                      for p in api.get("packages", [])][-6:]
            if rec["reg_version"]:
                for p in api.get("packages", []):
                    if str(p.get("versionName")) == str(rec["reg_version"]):
                        chosen = p.get("versionCode"); break
            if chosen is None and api.get("suggestedVersionCode"):
                chosen = api["suggestedVersionCode"]
        except Exception as e:
            print("  api fail:", e)
        if chosen is None and vcs:
            chosen = vcs[-1]
        rec["chosen_vc"] = chosen
        # APK download + sha (retry version codes until the registry pin matches)
        apk = f"{OUT}/apks/{pkg}.apk"
        candidates = []
        if chosen: candidates.append(chosen)
        try:
            for p in api_pkgs(pkg):
                vc = p.get("versionCode")
                if vc and vc not in candidates: candidates.append(vc)
        except Exception:
            pass
        if os.path.exists(apk) and rec["reg_sha"] and \
                not sha256(apk).startswith(rec["reg_sha"][:16]):
            os.remove(apk)
        for vc in candidates[:5]:
            if os.path.exists(apk):
                rec["apk_sha256"] = sha256(apk)
                if not rec["reg_sha"] or rec["apk_sha256"].startswith(rec["reg_sha"][:16]):
                    rec["chosen_vc"] = vc
                    break
                os.remove(apk)
            url = f"{FD_REPO}{pkg}_{vc}.apk"
            rec["apk_url"] = url
            if not fetch(url, apk):
                continue
            rec["apk_sha256"] = sha256(apk)
            rec["chosen_vc"] = vc
            if not rec["reg_sha"] or rec["apk_sha256"].startswith(rec["reg_sha"][:16]):
                break
        if os.path.exists(apk):
            rec["apk_sha256"] = sha256(apk)
            rec["apk_size"] = os.path.getsize(apk)
            rec["sha_matches_pin"] = bool(rec["reg_sha"]) and \
                rec["apk_sha256"].startswith(rec["reg_sha"][:16])
        # source tarball
        if repo and "github.com" in repo:
            head = repo.rstrip("/").split("github.com/")[1].replace(".git", "")
            tar = f"{OUT}/src/{pkg}.tar.gz"
            if not os.path.exists(tar):
                fetch(f"https://codeload.github.com/{head}/tar.gz/HEAD", tar)
            if not os.path.exists(tar) or os.path.getsize(tar) < 1000:
                fetch(f"https://codeload.github.com/{head}/tar.gz/refs/heads/master", tar)
            if not os.path.exists(tar) or os.path.getsize(tar) < 1000:
                fetch(f"https://codeload.github.com/{head}/tar.gz/refs/heads/main", tar)
            rec["src_tarball"] = tar if os.path.exists(tar) and os.path.getsize(tar) > 1000 else None
            if rec["src_tarball"]:
                d = f"{OUT}/src/{pkg}"
                if not os.path.isdir(d):
                    os.makedirs(d, exist_ok=True)
                    subprocess.call(["tar", "xzf", tar, "-C", d, "--strip-components=1"])
                rec["src_dir"] = d
        elif repo:
            rec["src_note"] = f"non-github repo: {repo}"
        else:
            # fallback: scrape the F-Droid page for a source github link
            page = f"{OUT}/meta/{pkg}.html"
            if fetch(f"https://f-droid.org/en/packages/{pkg}/", page, timeout=60):
                import re as _re
                m = _re.search(r'href="(https://github\\.com/[^"#?]+)"',
                               open(page, errors="replace").read())
                if m:
                    rec["repo_scraped"] = m.group(1).rstrip("/").replace(".git", "")
                    head2 = rec["repo_scraped"].split("github.com/")[1]
                    tar = f"{OUT}/src/{pkg}.tar.gz"
                    if not os.path.exists(tar):
                        fetch(f"https://codeload.github.com/{head2}/tar.gz/HEAD", tar)
                    if os.path.exists(tar) and os.path.getsize(tar) > 1000:
                        rec["src_tarball"] = tar
                        d = f"{OUT}/src/{pkg}"
                        if not os.path.isdir(d):
                            os.makedirs(d, exist_ok=True)
                            subprocess.call(["tar", "xzf", tar, "-C", d, "--strip-components=1"])
                        rec["src_dir"] = d
        manifest[pkg] = rec
        print(f"   vc={chosen} sha={rec.get('apk_sha256','')[:16]} "
              f"pin_match={rec.get('sha_matches_pin')} repo={repo}")
    json.dump(manifest, open(f"{OUT}/manifest.json", "w"), indent=1)
    print("manifest written")

if __name__ == "__main__":
    main()
