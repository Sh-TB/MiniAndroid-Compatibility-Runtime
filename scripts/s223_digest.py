#!/usr/bin/env python3
"""S223: digest of comments; flag NEW (id > watermark) and EDITED (updated_at > created_at)."""
import json

WM = {582: 6815552421, 583: 6815552737, 584: 0}
D = "/home/z/my-project/evidence/s223"

for num, wm in WM.items():
    comments = json.load(open(f"{D}/issue_{num}_comments.json"))
    print(f"===== ISSUE #{num} ({len(comments)} comments) =====")
    for c in comments:
        uid = c["id"]
        user = c["user"]["login"]
        ed = " EDITED!" if c["updated_at"] != c["created_at"] else ""
        flag = " <== NEW" if uid > wm else ""
        body = c["body"].replace("\n", " ")
        print(f"[{uid}] {user} {c['created_at']} upd={c['updated_at']}{ed}{flag}")
        print(f"    {body[:220]}")
    print()
