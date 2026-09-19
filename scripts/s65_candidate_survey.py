#!/usr/bin/env python3
# S65 candidate survey — REAL search evidence (no guessing), S65 breadth.
# Reuses the S64 law (scripts/s64_candidate_survey.py) with:
#   - expanded exclusion set (S64 picks pmk/klondike/shopcalc now corpus)
#   - WIDER keyword net (40 queries: board/card/arcade/puzzle/utility faces)
# Data sources:
#   1. F-Droid full index-v2.json (one download, local keyword scan)
#   2. GitHub raw build.gradle probe (androidx/support/compose detectors)
#   3. git trees API fallback -> direct clone for finalists
import json, re, os, urllib.request

OUT = "/tmp/s65_survey"
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (s65 survey)"}

def fetch(url, timeout=60, binary=False):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
    return data if binary else data.decode("utf-8", "replace")

# ---------- 1. exclusions: EVERYTHING already corpus or deferred ----------
EXCLUDE = set()
man = json.load(open("/home/z/my-project/docs/corpus/spotlight_manifest.json"))
for a in man["apps"]:
    EXCLUDE.add(a["package"])
EXCLUDE |= {
    # S63/S64 source-first picks (now regression corpus, not breadth targets)
    "de.duenndns.gmdice", "org.billthefarmer.siggen", "com.cax.pmk",
    "com.cax.pmk.ext", "eu.veldsoft.free.klondike",
    "io.github.buildsbyben.shoppinglistcalc",
    # S62/S63 surveyed + deferred (facts recorded; not re-picked without cause)
    "com.vocollapse.blockinger", "zikalify.bmicalculator", "com.zola.bmi",
    "alexbarry.AlexCalc", "alexbarry.alexcalc", "com.sidhant.nonogram",
    # earlier corpus / campaign apps
    "emmanuelmess.tictactoe", "com.itsfrz.tictactoe", "com.example.tictactoe",
    "com.palahsu.ttt", "org.secuso.privacyfriendlydame",
    "dubrowgn.microtimer", "omegacentauri.mobi.simplestopwatch",
    "com.chessclock.android", "app.varlorg.unote", "org.billthefarmer.notes",
    "org.billthefarmer.diary", "org.billthefarmer.tuner",
    "org.billthefarmer.accordion", "org.billthefarmer.pckeyboard",
    "org.billthefarmer.shorty", "org.billthefarmer.viewer",
    "org.billthefarmer.editor", "ch.logixisland.anuto",
    "cz.romario.opensudoku", "com.dozingcatsoftware.bouncy",
    "org.dslul.openboard", "fr.neamar.kiss", "com.droidify",
    "com.looker.droidify", "com.maxfour.music",
    # known heavy families (native/compose/web) seen in past surveys
    "org.ligi.survivalmanual", "com.artemkaxboy.android.autoredial",
}
print(f"[exclusions] {len(EXCLUDE)} packages")

# ---------- 2. F-Droid index (one download, local scan) ----------
idxp = os.path.join(OUT, "index-v2.json")
if not os.path.exists(idxp):
    print("[fdroid] downloading index-v2.json (~60MB, one-time)...")
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

# ---------- 3. keyword scan — WIDER than S64's 20 ----------
QUERIES = [
    # S64 net (keep for continuity)
    "fifteen", "lights out", "tic tac toe", "hangman", "snake game",
    "memory game", "pong", "tic-tac-toe", "sliding puzzle", "calculator",
    "minesweeper", "2048", "word search", "solitaire", "mastermind",
    "battleship", "sudoku", "nonogram", "lightsout", "dices",
    # S65 widening: board/card/arcade/utility faces
    "chess", "checkers", "draughts", "reversi", "othello", "go board",
    "gomoku", "connect four", "connect-four", "sokoban", "tetris",
    "breakout", "asteroids", "mahjong", "peg solitaire", "domino",
    "backgammon", "cribbage", "hearts", "spades", "whist", "blackjack",
    "memory", "pairs", "matching game", "quiz", "trivia", "flashcard",
    "stopwatch", "countdown", "counter", "clicker", "level", "maze",
    "labyrinth", "mines", "minesw", "klondike", "freecell", "spider",
    "patience", "card game", "board game", "puzzle game", "arcade game",
]
hits = {}
for pkg, pe in idx["packages"].items():
    if pkg in EXCLUDE: continue
    nm, sm, src, lic = name_of(pe)
    txt = (nm + " " + sm).lower()
    if not txt.strip(): continue
    for q in QUERIES:
        if q in txt:
            hits.setdefault(pkg, {"name": nm, "summary": sm, "query": q,
                                  "source": src, "license": lic})
            break
print("[scan] keyword hits:", len(hits))
json.dump(hits, open(os.path.join(OUT, "keyword_hits.json"), "w"),
          indent=1, ensure_ascii=False)

# ---------- 4. score by summary simplicity signals ----------
GOOD = re.compile(r"game|puzzle|dice|calc|timer|note|draw|level|chess|card|board|quiz|memory", re.I)
BAD = re.compile(r"matrix|client|server|sync|cloud|crypto|wallet|torrent|rss|podcast|mail|chat|social|mastodon|vpn|proxy|tracker|map|navigat|weather|launcher|keyboard|file manag|backup|browser|reader|player|stream|scanner|camera|notebook|database|sql|learning|language|dictionary|translat|network|analyz|monitor|automation|root|adb|debloat|download|ebook|online|multiplayer|bluetooth|wifi", re.I)
short = []
for pkg, v in hits.items():
    blob = v["name"] + " " + v["summary"]
    if BAD.search(blob): continue
    if not GOOD.search(blob): continue
    short.append(pkg)
print("[scan] simple-signal shortlist:", len(short))
json.dump(sorted(short), open(os.path.join(OUT, "shortlist_raw.json"), "w"), indent=1)

# ---------- 5. per-candidate probe: raw.githubusercontent gradle read ----------
# NOTE: GitHub API rate-limited in S64 mid-run; use raw file reads + HTML-free
# probing (raw is not API-rate-limited the same way). Repo default branch
# resolved via the F-Droid "sourceCode" + common branch names tried in order.
def gh_raw(owner, repo, path, branches=("master", "main", "head")):
    for br in branches:
        try:
            return fetch(f"https://raw.githubusercontent.com/{owner}/{repo}/{br}/{path}", 20), br
        except Exception:
            continue
    return None, None

out = {}
for pkg in short[:80]:
    src = hits[pkg]["source"] or ""
    m = re.match(r"https?://(?:www\.)?github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$", src)
    rec = {"name": hits[pkg]["name"], "summary": hits[pkg]["summary"],
           "license": hits[pkg]["license"], "repo": src or None}
    if m:
        owner, repo = m.group(1), m.group(2)
        rec["gh"] = f"{owner}/{repo}"
        gd = ""
        br_used = None
        for p in ("app/build.gradle", "build.gradle", "app/build.gradle.kts",
                  "android/app/build.gradle"):
            t, br = gh_raw(owner, repo, p)
            if t: gd += t; br_used = br; break
        rec["androidx"] = bool(re.search(r"androidx\.|com\.android\.support|material", gd))
        rec["compose"] = bool(re.search(r"compose", gd, re.I))
        rec["ndk"] = bool(re.search(r"externalNativeBuild|ndkBuild|cmake", gd, re.I))
        rec["branch"] = br_used
        rec["gradle_found"] = bool(gd)
    out[pkg] = rec

json.dump(out, open(os.path.join(OUT, "probes.json"), "w"), indent=1, ensure_ascii=False)

# ---------- 6. tier ranking: prefer NO androidx / NO compose / NO ndk ----------
tier0, tier1, rest = [], [], []
for pkg, rec in out.items():
    if not rec.get("gradle_found"): continue
    if not rec["androidx"] and not rec["compose"] and not rec["ndk"]:
        tier0.append(pkg)
    elif not rec["ndk"]:
        tier1.append(pkg)
    else:
        rest.append(pkg)
print(f"[tier] tier0(no androidx/compose/ndk, gradle found): {len(tier0)}")
print(f"[tier] tier1(androidx but no ndk): {len(tier1)}")
print(f"[tier] rest(ndk): {len(rest)}")
json.dump({"tier0": sorted(tier0), "tier1": sorted(tier1), "rest": sorted(rest)},
          open(os.path.join(OUT, "tiers.json"), "w"), indent=1)
for label, lst in (("TIER0", tier0), ("TIER1", tier1)):
    print(f"--- {label} ---")
    for p in lst[:40]:
        r = out[p]
        print(f"  {p} | {r['name'][:38]} | {r['gh'] or r['repo']} | {r['license']}")
print("SURVEY DONE")
