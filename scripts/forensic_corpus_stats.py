#!/usr/bin/env python3
"""Corpus stats: issues, comments, commits — compact overview."""
import json, re
from collections import Counter
D="/home/z/my-project/forensic_data/"
issues=json.load(open(D+"issues_all.json"))
comments=json.load(open(D+"all_issue_comments.json"))
commits=json.load(open(D+"commits.json"))
prs=[i for i in issues if "pull_request" in i]
real=[i for i in issues if "pull_request" not in i]
print(f"issues(all incl PR): {len(issues)}  real-issues: {len(real)}  PRs: {len(prs)}")
print(f"comments: {len(comments)}  commits(remote first 597): {len(commits)}")
# issue number range
nums=[i["number"] for i in real]
print(f"issue numbers: min={min(nums)} max={max(nums)}")
# state
st=Counter(i["state"] for i in real); print("state:",dict(st))
# comment distribution
cc=Counter(c["issue_number"] for c in comments) if "issue_number" in comments[0] else Counter()
if not cc:
    # derive from issue_url
    for c in comments:
        m=re.search(r"/issues/(\d+)$", c.get("issue_url",""))
        if m: cc[int(m.group(1))]+=1
print("top15 commented:", cc.most_common(15))
# comment authors
au=Counter(c["user"]["login"] for c in comments); print("comment authors:", dict(au))
# commits per month/day
cd=Counter(c["commit"]["author"]["date"][:10] for c in commits)
print("commit days (latest 25):", sorted(cd.items())[-25:])
