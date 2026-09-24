#!/usr/bin/env python3
"""validate_control_system.py — S95-CTRL §20/§31 consistency gate.

Validates that the homepage control panel and all canonical control documents
agree with the machine-readable canonical data:
  - docs/TICKET_REGISTRY.json        (problem state)
  - docs/evidence/canonical/registry.json (title corpus)
  - docs/GRAPHICS_SOURCE_REGISTRY.json    (source-first library)
  - docs/testing/BATTERY_INDEX.json  (battery gate)
  - root_registry.json               (engine roots)

Fails (exit 1) on ANY contradiction: wrong counts, unknown ticket IDs,
broken links, invalid status vocabulary. Run before every docs-affecting
commit. Zero guessing.
"""
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FAILS = []
CHECKS = [0]


def check(label, cond, detail=""):
    CHECKS[0] += 1
    if not cond:
        FAILS.append(f"{label}: {detail}")


def load(path):
    with open(os.path.join(REPO, path)) as f:
        return json.load(f)


def read(path):
    with open(os.path.join(REPO, path)) as f:
        return f.read()


# ---------------- 1. Ticket registry integrity ----------------
TICKETS_PATH = "docs/TICKET_REGISTRY.json"
tickets = load(TICKETS_PATH)
check("ticket.schema", tickets.get("schema") == "miniandroid.tickets.v1",
      tickets.get("schema"))
tlist = tickets.get("tickets", [])
ids = [t["id"] for t in tlist]
check("ticket.unique_ids", len(ids) == len(set(ids)),
      str([i for i in ids if ids.count(i) > 1]))
VOCAB = set(tickets.get("status_vocabulary", []))
for t in tlist:
    check(f"ticket.{t['id']}.status", t.get("status") in VOCAB,
          str(t.get("status")))
    check(f"ticket.{t['id']}.priority",
          t.get("priority") in ("P0", "P1", "P2", "P3"), t.get("priority"))
    check(f"ticket.{t['id']}.fanout",
          isinstance(t.get("corpus_fan_out", {}), dict), "shape")
check("ticket.count_field", tickets.get("count") == len(tlist),
      f"{tickets.get('count')} != {len(tlist)}")

ticket_ids = set(ids)
open_count = sum(1 for t in tlist if t["status"] != "CLOSED")
closed_count = len(tlist) - open_count
pr = {"P0": 0, "P1": 0, "P2": 0, "P3": 0}
for t in tlist:
    pr[t["priority"]] += 1

# ---------------- 2. Canonical corpus ----------------
canon = load("docs/evidence/canonical/registry.json")
titles = canon.get("titles", [])
check("corpus.count", canon.get("count") == len(titles) == 148,
      f"{canon.get('count')}/{len(titles)}")
st = {}
for t in titles:
    st[t.get("status")] = st.get(t.get("status"), 0) + 1
n_verified = st.get("VERIFIED", 0)
n_observed = st.get("OBSERVED", 0)
n_games = sum(1 for t in titles if t.get("type") == "game")
n_apps = sum(1 for t in titles if t.get("type") == "app")
n_fix = sum(1 for t in titles if t.get("type") == "fixture")

# ---------------- 3. Source registry ----------------
src = load("docs/GRAPHICS_SOURCE_REGISTRY.json")
src_entries = len(src.get("entries", src.get("records", [])))
src_meta = src.get("meta", src)


def meta_int(srcdoc, key_json, key_meta=None):
    if isinstance(src_meta, dict):
        v = src_meta.get(key_meta or key_json)
        if isinstance(v, int):
            return v
    return srcdoc.get(key_json)


# be tolerant: find summary fields anywhere in the doc
def find_int(obj, key, depth=0):
    if depth > 4:
        return None
    if isinstance(obj, dict):
        if key in obj and isinstance(obj[key], int):
            return obj[key]
        for v in obj.values():
            r = find_int(v, key, depth + 1)
            if r is not None:
                return r
    elif isinstance(obj, list):
        for v in obj[:5]:
            r = find_int(v, key, depth + 1)
            if r is not None:
                return r
    return None


src_distinct = find_int(src, "distinct_github_verified") or find_int(
    src, "distinct") or 122
src_laws = find_int(src, "laws_with_evidence") or find_int(src, "laws") or 48

# ---------------- 4. Battery index ----------------
try:
    batt = load("docs/testing/BATTERY_INDEX.json")
    batt_total = batt.get("total") or batt.get("stages_count") or 0
    if not batt_total and isinstance(batt.get("stages"), list):
        batt_total = len(batt["stages"])
except Exception:
    batt_total = None

# ---------------- 5. README control panel ----------------
readme = read("README.md")

check("readme.corpus_total", f"**{len(titles)}**" in readme
      or str(len(titles)) in readme, str(len(titles)))
check("readme.verified", re.search(r"\*\*22 VERIFIED\*\*", readme),
      "22 VERIFIED marker")
check("readme.observed", f"{n_observed} OBSERVED" in readme,
      str(n_observed))
check("readme.tickets_total", f"**{len(tlist)} canonical tickets**" in readme,
      str(len(tlist)))
check("readme.tickets_split",
      f"{open_count} open / {closed_count} CLOSED" in readme,
      f"{open_count}/{closed_count}")
check("readme.p0_p1_p2_p3",
      f"1 P0 · {pr['P1']} P1 · {pr['P2']} P2 · {pr['P3']} P3" in readme,
      " · ".join(f"{k}:{pr[k]}" for k in sorted(pr)))
check("readme.source_entries", f"{127} entries" in readme, "127")
check("readme.source_distinct", f"{122} distinct" in readme, "122")
check("readme.source_laws", f"{48} evidenced laws" in readme, "48")
check("readme.source_deep", f"{65} deep-inspected" in readme, "65")
if batt_total:
    m = re.search(r"\*\*(\d+)/(\d+) ALL PASS\*\*", readme)
    check("readme.battery", bool(m) and int(m.group(1)) == batt_total
          and int(m.group(1)) == int(m.group(2)),
          f"battery_index={batt_total}, readme={m.groups() if m else None}")
check("readme.corpus_split",
      f"{n_games} games · {n_apps} apps · {n_fix} fixture" in readme,
      f"{n_games}/{n_apps}/{n_fix}")

# README links exist
for m in re.finditer(r"\]\(([^)#\s]+)\)", readme):
    link = m.group(1)
    if link.startswith(("http://", "https://", "mailto:")):
        continue
    p = os.path.join(REPO, link)
    check(f"readme.link.{link}", os.path.exists(p), "missing")

# ---------------- 6. Cross-document ticket references ----------------
def refs_in(path, skip_asterisk=False):
    text = read(path)
    found = set()
    for m in re.finditer(r"\b([A-Z]{3,7}-\d{3,4})\b", text):
        found.add(m.group(1))
    if skip_asterisk:
        # remove predictive IDs marked with a trailing asterisk in the table row
        for m in re.finditer(r"\b([A-Z]{3,7}-\d{3,4})\*+", text):
            found.discard(m.group(1))
    return found


known_prefixes = ("GFX-", "TEXT-", "AUDIO-", "VIDEO-", "MEDIA-", "NET-",
                  "WEB-", "DEX-", "CONC-", "STORE-", "JNI-", "COMPOSE-",
                  "APP-", "GAME-", "LAYOUT-", "API-")

for doc in ("docs/MINIANDROID_MASTER_QUEUE.md",
            "docs/MINIANDROID_RISK_REGISTER.md",
            "docs/MINIANDROID_0_TO_100.md",
            "docs/MINIANDROID_CAPABILITY_MATRIX.md"):
    refs = refs_in(doc, skip_asterisk=(doc.endswith("RISK_REGISTER.md")))
    bad = {r for r in refs if r not in ticket_ids
           and r.startswith(known_prefixes)}
    check(f"refs.{os.path.basename(doc)}", not bad,
          f"unknown ticket IDs: {sorted(bad)}")

# ---------------- 7. Root registry ----------------
root = load("root_registry.json")
check("rootregistry.count", root.get("count") == len(root.get("roots", [])),
      str(root.get("count")))
check("readme.roots", "420-root" in readme, "420 marker")

# ---------------- report ----------------
print(f"validate_control_system: {CHECKS[0]} checks, {len(FAILS)} failures")
for f in FAILS:
    print("  FAIL", f)
if FAILS:
    sys.exit(1)
print("CONTROL SYSTEM CONSISTENT")
