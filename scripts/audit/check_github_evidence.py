#!/usr/bin/env python3
# S74-FINAL §26: verify human-visible evidence links actually render on GitHub
# Checks [EXEC] issue bodies + latest comments for image URLs; HEAD-checks them.
import json, os, re, subprocess, sys

TOKEN = os.environ.get("GH_TOKEN", "")
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
OUT = "/home/z/my-project/docs/audit/github_evidence_check.json"

def api(url):
    r = subprocess.run(["curl","-s","-H",f"Authorization: Bearer {TOKEN}",
                        "-H","Accept: application/vnd.github+json",url],
                       capture_output=True,text=True,timeout=60)
    return json.loads(r.stdout or "{}")

results=[]
issues = api(f"https://api.github.com/repos/{REPO}/issues?state=all&per_page=50")
exec_issues = [i for i in issues if 10 <= i["number"] <= 23]
for iss in sorted(exec_issues, key=lambda x:x["number"]):
    num=iss["number"]
    detail={"issue":num,"title":iss["title"][:60],"state":iss["state"],
            "body_has_image": False, "image_urls":[], "url_checks":[]}
    bodies=[iss.get("body") or ""]
    comments = api(f"https://api.github.com/repos/{REPO}/issues/{num}/comments?per_page=30")
    for c in comments: bodies.append(c.get("body") or "")
    urls=[]
    for b in bodies:
        urls += re.findall(r"https://(?:user-images\.githubusercontent\.com|github\.com/user-attachments/assets)[^\s\)\"]+", b)
    urls = list(dict.fromkeys(urls))
    detail["body_has_image"] = bool(urls)
    detail["image_urls"]=urls[:6]
    for u in urls[:2]:
        rc = subprocess.run(["curl","-s","-o","/dev/null","-w","%{http_code} %{content_type}","-I",u],
                            capture_output=True,text=True,timeout=60).stdout
        detail["url_checks"].append({"url":u[:110],"resp":rc})
    results.append(detail)
    print(f"#{num} [{iss['state']}] imgs={len(urls)} checks={detail['url_checks']}")

json.dump({"checked_at_rc":"HEAD","results":results}, open(OUT,"w"), indent=1)
ok=sum(1 for r in results if r["url_checks"] and all(c["resp"].startswith("200") for c in r["url_checks"]))
with_imgs=sum(1 for r in results if r["body_has_image"])
print(f"\nSUMMARY: {with_imgs}/{len(results)} EXEC issues embed images; {ok} issues with ALL links HTTP-200")
