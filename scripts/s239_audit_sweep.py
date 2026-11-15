#!/usr/bin/env python3
"""The S239 wave-audit sweep: every open transfer/wave issue (558..589) ->
extract its law ids -> grep main -> the EXISTS/MISSING verdict table."""
import json, re, subprocess, urllib.request
from collections import OrderedDict

CRED = subprocess.run(["git","credential","fill"],
                      input="protocol=https\nhost=github.com\n\n",
                      capture_output=True, text=True).stdout
TOKEN=[l.split("=",1)[1] for l in CRED.splitlines() if l.startswith("password=")][0]
H={"Authorization":f"token {TOKEN}","Accept":"application/vnd.github+json","User-Agent":"s239-sweep"}
def api(u):
    with urllib.request.urlopen(urllib.request.Request(u,headers=H),timeout=30) as r:
        return json.loads(r.read().decode())

TARGETS = [589,587,586,585,584,583,582,581,580,579,578,577,576,575,574,
           573,572,571,570,569,568,567,566,565,564,563,562,561,560,558]
ID_RE = re.compile(r"\b(F-[A-Z0-9]+-\d+[a-z]?|R-NEW-\d+[a-z]?|EXP-\d+[a-z]?|"
                   r"UNIFIED-\d+[\.\d]*|F513|F516-L\d|F596(?:-P\d)?|F720)\b")

results = OrderedDict()
for n in TARGETS:
    try:
        i = api(f"https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/{n}")
        body = i["body"] or ""
        ids = []
        for m in ID_RE.finditer(body):
            if m.group(0) not in ids:
                ids.append(m.group(0))
        results[n] = {"title": i["title"][:70], "ids": ids}
    except Exception as e:
        results[n] = {"title": f"FETCH-FAIL {e}", "ids": []}

# grep main for every unique id (batched)
all_ids = sorted({i for v in results.values() for i in v["ids"]})
eng = "/home/z/my-project/miniandroid/src"
verdict = {}
for law in all_ids:
    r = subprocess.run(["grep","-rni","-l",law,eng],
                       capture_output=True,text=True)
    verdict[law] = len(r.stdout.strip().splitlines()) if r.stdout.strip() else 0

print(f"{'issue':6s} {'law':22s} hits  verdict")
for n,v in results.items():
    print(f"--- #{n} {v['title']}")
    if not v["ids"]:
        print("      (no explicit law ids in body — content audit)")
        continue
    for law in v["ids"]:
        h = verdict[law]
        print(f"      {law:22s} {h:4d}  {'PRESENT' if h else 'MISSING?'}")
missing = [k for k,h in verdict.items() if h == 0]
print(f"\nTOTAL ids={len(all_ids)}  zero-hit ids={len(missing)}")
for k in missing:
    print("  ZERO:", k)
json.dump({"verdict":verdict,"zero":missing},
          open("/home/z/my-project/scripts/s239_sweep_verdict.json","w"), indent=1)
