#!/usr/bin/env python3
# S64 candidate survey — REAL search evidence (no guessing).
# Data sources:
#   1. F-Droid full index-v2.json (one download, local keyword scan)
#   2. fdroiddata metadata yml (Repo URL, build system) via GitLab raw
#   3. GitHub raw build.gradle* / settings.gradle to detect androidx/support/WebCompose deps
# Exclusions: every package already in the corpus (spotlight manifest +
# canonical ACHIEVEMENTS list + campaign014 apps).
import json, re, gzip, sys, os, urllib.request, io

OUT = "/tmp/s64_survey"
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (survey script)"}

def fetch(url, timeout=60, binary=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "replace")

# ---------- 1. exclusions ----------
EXCLUDE = set()
man = json.load(open("/home/z/my-project/docs/corpus/spotlight_manifest.json"))
for a in man["apps"]:
    EXCLUDE.add(a["package"])
# canonical / campaign014 / known-deferred
EXCLUDE |= {
    "de.duenndns.gmdice", "org.billthefarmer.siggen", "com.palahsu.ttt",
    "emmanuelmess.tictactoe", "com.itsfrz.tictactoe", "com.example.tictactoe",
    "com.vocollapse.blockinger", "org.secuso.privacyfriendlydame",
    "dubrowgn.microtimer", "omegacentauri.mobi.simplestopwatch",
    "com.chessclock.android", "app.varlorg.unote", "com.gmail.jeremyj",  # loose tail
    "org.billthefarmer.notes", "org.billthefarmer.diary", "org.billthefarmer.tuner",
    "org.billthefarmer.accordion", "org.billthefarmer.pckeyboard", "org.billthefarmer.shorty",
    "org.billthefarmer.viewer", "org.billthefarmer.editor",
    "ch.logixisland.anuto", "cz.romario.opensudoku", "com.dozingcatsoftware.bouncy",
    "io.github.dooz", "com.github.dooz",
    "org.dslul.openboard", "fr.neamar.kiss", "com.droidify", "com.looker.droidify",
    "com.maxfour.music", "com.mrhabibi.???",
}
print(f"[exclusions] {len(EXCLUDE)} packages")

# ---------- 2. F-Droid index (one download, local scan) ----------
idxp = os.path.join(OUT, "index-v2.json")
if not os.path.exists(idxp):
    print("[fdroid] downloading index-v2.json.gz (~one-time)...")
    raw = fetch("https://f-droid.org/repo/index-v2.json", 300, binary=True)
    print("[fdroid] bytes:", len(raw))
    with open(idxp, "wb") as f:
        f.write(raw)
idx = json.load(open(idxp))
print("[fdroid] packages in index:", len(idx["packages"]))

def name_of(pkg_entry):
    md = pkg_entry.get("metadata", {})
    def loc(field):
        v = md.get(field, {})
        if isinstance(v, dict):
            return next(iter(v.values()), "") if v else ""
        return v if isinstance(v, str) else ""
    src = md.get("sourceCode", "")
    lic = md.get("license", "")
    return loc("name"), loc("summary"), src, lic

# ---------- 3. keyword scan ----------
QUERIES = [
    "fifteen", "lights out", "tic tac toe", "hangman", "snake game",
    "memory game", "pong", "tic-tac-toe", "sliding puzzle", "calculator",
    "minesweeper", "2048", "word search", "solitaire", "mastermind",
    "battleship", "sudoku", "nonogram", "lightsout", "dices",
]
hits = {}
for pkg, pe in idx["packages"].items():
    if pkg in EXCLUDE: continue
    nm, sm, src, lic = name_of(pe)
    txt = (nm + " " + sm).lower()
    if not txt.strip(): continue
    for q in QUERIES:
        if q in txt:
            hits.setdefault(pkg, {"name": nm, "summary": sm, "query": q, "source": src, "license": lic})
            break
print("[scan] keyword hits:", len(hits))
json.dump(hits, open(os.path.join(OUT, "keyword_hits.json"), "w"), indent=1, ensure_ascii=False)

# ---------- 4. score by summary simplicity signals ----------
GOOD = re.compile(r"game|puzzle|dice|calc|timer|note|draw|level", re.I)
BAD = re.compile(r"matrix|client|server|sync|cloud|crypto|wallet|torrent|rss|podcast|mail|chat|social|mastodon|vpn|proxy|tracker|map|navigat|weather|launcher|keyboard|file manag|backup|browser|reader|player|stream|scanner|camera|notebook|database|sql|learning|language|dictionary|translat|network|analyz|monitor|automation|root|adb|debloat|download|torrent|ebook|rss|podcast", re.I)
short = []
for pkg, v in hits.items():
    blob = v["name"] + " " + v["summary"]
    if BAD.search(blob): continue
    if not GOOD.search(blob): continue
    short.append(pkg)
print("[scan] simple-signal shortlist:", len(short))
json.dump(sorted(short), open(os.path.join(OUT, "shortlist_raw.json"), "w"), indent=1)

# ---------- 5. per-candidate GitHub probe: gradle deps + java file count ----------
GHR = "https://api.github.com"
def gh_json(url):
    try:
        return json.loads(fetch(url, 30))
    except Exception as e:
        return {"error": str(e)}

def gh_raw(owner, repo, path, branch=None):
    if branch is None:
        info = gh_json(f"{GHR}/repos/{owner}/{repo}")
        branch = info.get("default_branch", "master")
    try:
        return fetch(f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}", 30)
    except Exception:
        return None

out = {}
for pkg in short[:60]:
    src = hits[pkg]["source"] or ""
    m = re.match(r"https?://(?:www\.)?github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", src)
    rec = {"name": hits[pkg]["name"], "summary": hits[pkg]["summary"],
           "license": hits[pkg]["license"], "repo": src or None}
    if m:
        owner, repo = m.group(1), m.group(2)
        info = gh_json(f"{GHR}/repos/{owner}/{repo}")
        rec["github"] = {"full_name": info.get("full_name"), "stars": info.get("stargazers_count"),
                         "pushed_at": info.get("pushed_at"), "default_branch": info.get("default_branch"),
                         "language": info.get("language"), "archived": info.get("archived")}
        br = info.get("default_branch", "master")
        gd = ""
        for p in ("app/build.gradle", "build.gradle", "app/build.gradle.kts"):
            t = gh_raw(owner, repo, p, br)
            if t: gd += t
        rec["androidx"] = bool(re.search(r"androidx\.|com\.android\.support|material", gd))
        rec["compose"] = bool(re.search(r"compose", gd, re.I))
        rec["agp8_manifest_ns"] = bool("namespace " in gd)
        tree = gh_json(f"{GHR}/repos/{owner}/{repo}/git/trees/{br}?recursive=1")
        if "tree" in tree:
            java = [t for t in tree["tree"] if t.get("path", "").endswith((".java", ".kt"))]
            rec["java_kt_files"] = len(java)
            rec["has_xml_layouts"] = any(t.get("path", "").endswith(".xml") and "/layout" in t.get("path", "") for t in tree["tree"])
            rec["manifests"] = [t["path"] for t in tree["tree"] if t.get("path", "").endswith("AndroidManifest.xml") and "test" not in t["path"]][:4]
    out[pkg] = rec
    print(f"  {pkg:45s} stars={rec.get('github',{}).get('stars')} androidx={rec.get('androidx')} compose={rec.get('compose')} files={rec.get('java_kt_files')}")
json.dump(out, open(os.path.join(OUT, "shortlist_repos.json"), "w"), indent=1, ensure_ascii=False)
print("[done] artifacts in", OUT)
