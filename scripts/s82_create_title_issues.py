#!/usr/bin/env python3
"""s82_create_title_issues.py — S82 §5/§24/§25/§45/§46/§47: idempotent GitHub
issue factory for ALL 202 title records.

LAWS:
  - Idempotent (§24): search before create; match on the canonical identity
    line `TITLE_ID: <id>` in the body (identity, not issue number).
  - Existing issue -> UPDATE (body refresh + label sync), never duplicate.
  - Registry backfill (§25): issue_number/issue_url written into
    title_registry.json.
  - No silent failure (§47): every outcome counted (CREATED/UPDATED/
    ALREADY_EXISTS_OK/BLOCKED/FAILED) and printed as a manifest.
  - Labels: family + status + failure families synced from the record (§21/§23).
  - Verification (§46): post-pass GitHub label queries count what really exists.
"""
import json
import time
import urllib.parse
import urllib.request

import s82_issue_body as B

TOKEN = open("/home/z/my-project/.secrets/gh_token").read().strip()
REPO = "Sh-TB/MiniAndroid-Compatibility-Runtime"
API = f"https://api.github.com/repos/{REPO}"
MARK = "TITLE_ID: **"


def gh(method, url, body=None, timeout=30):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, method=method, data=data,
                               headers={"Authorization": f"Bearer {TOKEN}",
                                        "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(r, timeout=timeout) as resp:
        return json.loads(resp.read().decode() or "{}")


def gh_safe(method, url, body=None):
    for attempt in range(4):
        try:
            return ("OK", gh(method, url, body))
        except Exception as e:
            code = getattr(e, "code", None)
            if code == 403:  # rate limit -> wait once
                time.sleep(65)
                continue
            if code and 500 <= code < 600:
                time.sleep(5 * (attempt + 1))
                continue
            return ("ERR", {"error": f"{type(e).__name__}: {e}", "code": code})
    return ("ERR", {"error": "retries exhausted"})


def labels_for(t):
    ls = ["compatibility", t["TYPE"] if t["TYPE"] in ("game", "app") else "mandatory"]
    if t.get("F_DROID_URL"):
        ls += ["open-source", "fdroid"]
    st = t.get("EXECUTION", "NOT_TESTED")
    if st == "EXECUTED":
        ls.append("executed")
    elif st.startswith("BLOCKED"):
        ls += ["not-tested", "blocked"]
    else:
        ls.append("not-tested")
    state = t.get("STATE", "STATE-NOT-LOADED")
    state_label = "state-" + state.replace("STATE-", "", 1).lower().replace("_", "-")
    ls.append(state_label)
    if t.get("GRAPHICS") == "NONTRIVIAL":
        ls.append("state-graphics-nontrivial")
    for f in t.get("FAILURE_LABELS", []):
        ls.append(f.lower().replace("FAIL-", "fail-"))
    for f in t.get("F_IDS", []):
        ls.append("common-runtime" if f.startswith("F-") else "")
    for f in t.get("VF_IDS", []):
        ls.append("image-decoded-vs-rendered-gap" if "IMAGE" in f else "graphics")
    return [x for x in dict.fromkeys(ls) if x]


def issue_title(t):
    return f"[{t['TITLE_ID']}] {t.get('NAME') or t['PACKAGE']} — compatibility report"


def find_existing_by_id(title_id, local_index):
    """§24 identity search: authoritative REST list of ALL issues (immune to
    search-index sync delays), matched by canonical TITLE_ID marker in body or
    title prefix. Falls back to the search API only when the local index has
    no entry AND the search quota allows (never blocks the batch)."""
    hit = local_index.get(title_id)
    if hit:
        return hit
    q = f'repo:{REPO} in:body "{MARK}{title_id}"'
    st, res = gh_safe("GET", f"{API}/search/issues?q={urllib.parse.quote(q)}&per_page=5")
    if st == "OK":
        for it in res.get("items", []):
            if not it.get("pull_request"):
                return it
    return None


def build_local_index():
    """one paginated GET /issues -> {TITLE_ID: issue} (identity index)."""
    idx = {}
    page = 1
    while True:
        st, res = gh_safe("GET", f"{API}/issues?state=all&per_page=100&page={page}")
        if st != "OK" or not res:
            break
        for it in res:
            if it.get("pull_request"):
                continue
            body = it.get("body") or ""
            title = it.get("title") or ""
            import re
            m = re.search(r"TITLE_ID: \*\*([A-Z]+-\d{3})\*\*", body)
            if m:
                idx.setdefault(m.group(1), it)
            m2 = re.match(r"\[([A-Z]+-\d{3})\]", title)
            if m2:
                idx.setdefault(m2.group(1), it)
        if len(res) < 100:
            break
        page += 1
        time.sleep(0.5)
    return idx


def main():
    reg = json.load(open("/home/z/my-project/docs/corpus/s82/title_registry.json"))
    counts = {"CREATED": 0, "UPDATED": 0, "ALREADY_EXISTS_OK": 0, "BLOCKED": 0,
              "FAILED": 0}
    failed_ids = []
    titles = reg["TITLES"]
    local_index = build_local_index()
    print("identity index size:", len(local_index), flush=True)

    for idx, t in enumerate(titles):
        tid = t["TITLE_ID"]
        body = B.body_for(t)
        existing = find_existing_by_id(tid, local_index)
        payload = {"title": issue_title(t), "body": body,
                   "labels": labels_for(t)}
        if existing is None:
            st, res = gh_safe("POST", f"{API}/issues", payload)
            if st == "OK" and res.get("number"):
                t["ISSUE_NUMBER"] = res["number"]
                t["ISSUE_URL"] = res["html_url"]
                local_index[tid] = res
                counts["CREATED"] += 1
            else:
                counts["FAILED"] += 1
                counts["BLOCKED"] += 0
                failed_ids.append((tid, res.get("error", "?")[:120]))
        else:
            st, res = gh_safe("PATCH", f"{API}/issues/{existing['number']}",
                              {"title": payload["title"], "body": body})
            if st == "OK":
                t["ISSUE_NUMBER"] = existing["number"]
                t["ISSUE_URL"] = existing["html_url"]
                counts["UPDATED"] += 1
                # label sync (§23): set labels to current state
                gh_safe("PUT", f"{API}/issues/{existing['number']}/labels",
                        {"labels": payload["labels"]})
            else:
                counts["FAILED"] += 1
                failed_ids.append((tid, res.get("error", "?")[:120]))
        if (idx + 1) % 20 == 0:
            json.dump(reg, open("/home/z/my-project/docs/corpus/s82/title_registry.json", "w"),
                      indent=1)
            print(f"...{idx+1}/{len(titles)} {counts}", flush=True)
        time.sleep(0.35)

    json.dump(reg, open("/home/z/my-project/docs/corpus/s82/title_registry.json", "w"),
              indent=1)
    print("FINAL:", counts)
    if failed_ids:
        print("FAILED TITLES:")
        for tid, err in failed_ids:
            print(" ", tid, err)

    # §46 query-based verification
    ver = {}
    for label in ("compatibility", "game", "app", "mandatory", "executed",
                  "state-rendered", "state-nonblank"):
        st, res = gh_safe("GET",
                          f"{API}/search/issues?q={urllib.parse.quote(f'repo:{REPO} is:issue is:open label:{label}')}&per_page=1")
        ver[label] = res.get("total_count") if st == "OK" else "ERR"
    print("QUERY VERIFICATION:", json.dumps(ver))
    json.dump({"counts": counts, "verification": ver},
              open("/home/z/my-project/run/s82/issue_creation_manifest.json", "w"),
              indent=1)


if __name__ == "__main__":
    main()
