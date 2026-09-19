#!/usr/bin/env python3
# S64 source forensics: class inventory + call-chain extraction for the 3
# selected candidates. Evidence-grade: every number comes from rg/python scans
# of the pinned clones under /tmp/cand/<repo>.
import os, re, json, subprocess

CANDS = {
    "NEW-001": ("pmk-android", "/tmp/cand/pmk-android/pmk/app/src/main/java", "com.cax.pmk"),
    "NEW-002": ("FreeKlondike", "/tmp/cand/FreeKlondike/FreeKlondike/src/main/java", "eu.veldsoft.free.klondike"),
    "NEW-003": ("shopping-list-calc", "/tmp/cand/shopping-list-calc/app/src/main/java", "io.github.buildsbyben.shoppinglistcalc"),
}
OUT = "/tmp/s64_forensics"
os.makedirs(OUT, exist_ok=True)

ACT = re.compile(r"extends\s+(?:android\.app\.)?(?:Activity|ListActivity|ExpandableListActivity|TabActivity|PreferenceActivity)")
FRAG = re.compile(r"extends\s+(?:android\.(?:support\.v4\.app|x\.fragment\.app)\.)?Fragment\b")
VIEW = re.compile(r"extends\s+(?:View|TextView|ImageView|SeekBar|SurfaceView|ViewGroup|LinearLayout|FrameLayout|EditText|Button)\b")
ADAPTER = re.compile(r"extends\s+(?:BaseAdapter|ArrayAdapter|CursorAdapter|RecyclerView\.Adapter|FragmentPagerAdapter|FragmentStatePagerAdapter)")
DB = re.compile(r"(SQLiteOpenHelper|SQLiteDatabase|Cursor\b.*query)")
THREAD = re.compile(r"(extends\s+Thread|implements\s+Runnable|new\s+Thread|CountDownTimer|Timer\b|HandlerThread)")
LISTEN = re.compile(r"implements\s+[^\{]*Listener|(?:setOn\w+Listener|OnClickListener|OnTouchListener|OnItemSelectedListener|OnKeyListener|OnCheckedChangeListener)\b")
DRAW = re.compile(r"(onDraw\s*\(|Canvas\s|Bitmap\.|drawBitmap|Paint\s|onTouchEvent)")
LAUNCH = re.compile(r"(setContentView|findViewById|onCreate\b)")

report = {}
for tag, (name, root, pkg) in CANDS.items():
    inv = {"TOTAL_FILES": 0, "CLASSES": 0, "ACTIVITIES": [], "FRAGMENTS": [],
           "CUSTOM_VIEWS": [], "ADAPTERS": [], "DB": [], "THREAD": [],
           "LISTENER_FILES": 0, "DRAWING": [], "INNER_CLASSES": 0}
    for dirpath, _, files in os.walk(root):
        for f in files:
            if not f.endswith(".java"): continue
            p = os.path.join(dirpath, f)
            src = open(p, encoding="utf-8", errors="replace").read()
            inv["TOTAL_FILES"] += 1
            # class declarations incl. inner
            cls = re.findall(r"(?:class|interface|enum)\s+(\w+)", src)
            inv["CLASSES"] += len(cls)
            inv["INNER_CLASSES"] += max(0, len(cls) - 1)
            rel = os.path.relpath(p, root)
            if ACT.search(src): inv["ACTIVITIES"].append(rel)
            if FRAG.search(src): inv["FRAGMENTS"].append(rel)
            if VIEW.search(src): inv["CUSTOM_VIEWS"].append(rel)
            if ADAPTER.search(src): inv["ADAPTERS"].append(rel)
            if DB.search(src): inv["DB"].append(rel)
            if THREAD.search(src): inv["THREAD"].append(rel)
            if LISTEN.search(src): inv["LISTENER_FILES"] += 1
            if DRAW.search(src): inv["DRAWING"].append(rel)
    report[tag] = {"name": name, "pkg": pkg, **inv}
    print(f"[{tag}] {name}: files={inv['TOTAL_FILES']} classes={inv['CLASSES']} "
          f"acts={len(inv['ACTIVITIES'])} frags={len(inv['FRAGMENTS'])} views={len(inv['CUSTOM_VIEWS'])} "
          f"threads={len(inv['THREAD'])} draw={len(inv['DRAWING'])}")

json.dump(report, open(os.path.join(OUT, "class_inventory.json"), "w"), indent=1)

# ---- call-chain evidence: grep key lines with file:line ----
CHAINS = {
    "NEW-001": [("setContentView", "pmk-android/pmk/app/src/main/java/com/cax/pmk/MainActivity.java"),
                 ("onKeypadButtonTouched", "pmk-android/pmk/app/src/main/java/com/cax/pmk/MainActivity.java"),
                 ("Emulator extends Thread", "pmk-android/pmk/app/src/main/java/com/cax/pmk/emulator/Emulator.java"),
                 ("indicator", "pmk-android/pmk/app/src/main/java/com/cax/pmk/MainActivity.java")],
    "NEW-002": [("setContentView", "FreeKlondike/FreeKlondike/src/main/java/eu/veldsoft/free/klondike/GameActivity.java"),
                 ("onTouch", "FreeKlondike/FreeKlondike/src/main/java/eu/veldsoft/free/klondike/GameActivity.java"),
                 ("setTimeout", "FreeKlondike/FreeKlondike/src/main/java/eu/veldsoft/free/klondike/SplashActivity.java")],
    "NEW-003": [("setContentView", "shopping-list-calc/app/src/main/java/io/github/buildsbyben/shoppinglistcalc/MainActivity.java"),
                 ("TextWatcher", "shopping-list-calc/app/src/main/java/io/github/buildsbyben/shoppinglistcalc/MainActivity.java")],
}
chain_txt = []
for tag, qs in CHAINS.items():
    chain_txt.append(f"===== {tag} call-chain grep evidence =====")
    base = {"NEW-001": "/tmp/cand", "NEW-002": "/tmp/cand", "NEW-003": "/tmp/cand"}[tag]
    for pat, path in qs:
        fp = os.path.join(base, path)
        if not os.path.exists(fp):
            chain_txt.append(f"  [{pat}] FILE-MISSING {path}")
            continue
        hits = [l for l in open(fp, encoding="utf-8", errors="replace").read().splitlines() if pat.lower() in l.lower()][:6]
        chain_txt.append(f"  [{pat}] {path}")
        for h in hits: chain_txt.append(f"      | {h.strip()[:160]}")
open(os.path.join(OUT, "callchain_grep.txt"), "w").write("\n".join(chain_txt) + "\n")
print("[done] inventory + callchain evidence in", OUT)
