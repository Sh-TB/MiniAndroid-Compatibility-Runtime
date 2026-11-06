import json, subprocess, os
tok = subprocess.run(["git","credential","fill"], input="protocol=https\nhost=github.com\n", capture_output=True, text=True).stdout
token = [l.split("=",1)[1] for l in tok.splitlines() if l.startswith("password=")][0]
os.environ["GH"]=token
import urllib.request
def api(url):
    r = urllib.request.Request(url, headers={"Authorization": f"token {token}", "User-Agent":"s183"})
    return json.load(urllib.request.urlopen(r))
for num in (11,12):
    iss = api(f"https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/{num}")
    body = iss.get("body") or ""
    print(f"=== #{num} {iss['title']} | state={iss['state']} | comments={iss['comments']} ===")
    print(body[:3000])
    print("...")
    cms = api(f"{iss['comments_url']}?per_page=100")
    for c in cms:
        print(f"--- comment {c['id']} by {c['user']['login']} at {c['created_at']} ---")
        print((c.get("body") or "")[:2500])
        print()
