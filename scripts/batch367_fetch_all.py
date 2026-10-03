#!/usr/bin/env python3
"""Fetch all 108 closed issues for batches #367/#368/#369: bodies + comments."""
import subprocess, json, urllib.request, os, time

out = subprocess.run(["git","credential","fill"], input="protocol=https\nhost=github.com\n\n",
    capture_output=True, text=True, cwd="/home/z/my-project").stdout
token = [l.split("=",1)[1] for l in out.splitlines() if l.startswith("password=")][0]
HDRS = {"Authorization": f"token {token}", "Accept": "application/vnd.github+json", "User-Agent": "forensic"}
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"

B1 = [1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 15, 17, 18, 68, 81, 121, 166, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 334, 335, 336, 337, 338, 340, 341, 342, 345, 347, 349, 350, 352]
B2 = [252, 253, 254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 273, 274, 275, 276, 277, 279, 280, 285, 286, 287, 289, 291, 292, 293, 294, 298, 299, 300, 301, 302, 303, 305, 306, 307, 308, 309, 310, 313, 314, 315, 316]
B3 = [317, 318, 319, 321, 323, 331, 332, 333]
ALL = B1 + B2 + B3
assert len(ALL) == 108 and len(set(ALL)) == 108, f"membership wrong: {len(ALL)}"

os.makedirs("/home/z/my-project/forensic_data/batch367", exist_ok=True)
summary = []
for n in ALL:
    paths = [f"/home/z/my-project/forensic_data/batch367/issue_{n}.json",
             f"/home/z/my-project/forensic_data/batch367/issue_{n}_comments.json"]
    if all(os.path.exists(p) and os.path.getsize(p) > 50 for p in paths):
        obj = json.load(open(paths[0]))
        summary.append((n, obj["title"], obj["state"], len(json.load(open(paths[1])))))
        continue
    try:
        req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/issues/{n}", headers=HDRS)
        with urllib.request.urlopen(req) as r:
            obj = json.loads(r.read())
        with open(paths[0], "w") as f:
            json.dump(obj, f, indent=1)
        req2 = urllib.request.Request(f"https://api.github.com/repos/{REPO}/issues/{n}/comments?per_page=100", headers=HDRS)
        with urllib.request.urlopen(req2) as r:
            comments = json.loads(r.read())
        with open(paths[1], "w") as f:
            json.dump(comments, f, indent=1)
        summary.append((n, obj["title"], obj["state"], len(comments)))
        time.sleep(0.2)
    except Exception as e:
        print(f"ERROR fetching {n}: {e}")
        summary.append((n, "FETCH-ERROR", "?", -1))

# also fetch #367/368/369 bodies for reference
print(f"\n=== Fetched {len(summary)} ===")
for n, t, s, c in summary:
    print(f"#{n} [{s}] comments={c} :: {t[:90]}")
