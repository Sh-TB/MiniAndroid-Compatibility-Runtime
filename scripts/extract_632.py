#!/usr/bin/env python3
"""Extract EVERY finding from #632 (body + 11 comments) into 632_FINDINGS.csv.
- stable IDs, original wording preserved verbatim
- registry status: LIVE / RETRACTED-BY-AUTHOR / DEAD-CODE-RESCOPED / FALSIFIED
- source check: cited file:line verified against the active tree
"""
import json, re, csv, os, sys

REPO = "/home/z/my-project/miniandroid"
BODY_MD = "/tmp/i632_body.md"
COMMENTS = "/tmp/i632_comments.json"
OUT = "/home/z/my-project/miniandroid/evidence/audit/632_FINDINGS.csv"

body = open(BODY_MD, encoding="utf-8").read()
comments = json.load(open(COMMENTS))

# ---------- registry status maps (from the author's own corrections) ----------
RETRACTED = {  # id -> (retraction source, author's note)
 "O1": ("body §0", "WRONG — blend() SRC-OVER premultiplied layer exists software_renderer.h:142-167"),
 "O3": ("body §0", "WRONG — every write bounds-guarded software_renderer.h:143"),
 "J3": ("body §0", "WRONG — same bounds guard as O3"),
 "J5": ("body §0", "WRONG for JPEG & GIF — libjpeg wrapper + stb_image GIF89a wired"),
 "K3": ("body §0", "LIKELY WRONG — PNG via libpng handles interlaced/palette/16-bit"),
 "K4": ("body §0", "LIKELY WRONG — same libpng basis as K3"),
 "K6": ("body §0", "WRONG — straight-RGBA storage + premultiplied math documented"),
 "C1": ("batch2 7034254502", "WRONG — MeasureSpec2 + M_UNSPEC + child_spec exist in layout_inflater.cpp; re-scoped to fallback engine"),
 "E1": ("batch2 7034254502", "WRONG for the inflater engine — :4757 supports shrink; re-scoped"),
 "E2": ("batch2 7034254502", "WRONG — weightSum read at :1672/:2195/:4759; re-scoped"),
 "G1": ("batch2 7034254502", "WRONG — anchors parsed+stored :2002-2004; resolution still open (NEW-1); re-scoped"),
 "H1": ("batch2 7034254502", "WRONG — Bellman-Ford arc solver :2898/:4364-4380; re-scoped"),
 "H2": ("batch2 7034254502", "WRONG — same solver as H1; re-scoped"),
 "I1": ("batch2 7034254502", "WRONG — UNSPEC both axes :3889/:3897; re-scoped"),
 "I3": ("batch2 7034254502", "WRONG — same basis as I1; re-scoped"),
 "I5": ("batch2 7034254502", "WRONG — same basis as I1; re-scoped"),
 "E8": ("batch2 7034254502", "WRONG — :4767 second pass re-measure; re-scoped"),
 "C5": ("batch3 7034329407", "wrong — window_insets_shadow.cpp + locale_insets_shadow.cpp are manifest TUs"),
 "NEW-11": ("batch4 7034373205", "FALSIFIED by compiled probes — live engine is a faithful AOSP port"),
 "NEW-12": ("batch4 7034373205", "FALSIFIED by compiled probes — live engine is a faithful AOSP port"),
}
DEAD_CODE_FILES = ("view_renderer.cpp", "real_layout.cpp")  # NOT in core_sources.manifest

def source_check(text):
    """verify cited file:line against the active tree"""
    cites = re.findall(r'([\w/]+\.(?:cpp|h)):(\d+)(?:-(\d+))?', text)
    checked, ok = 0, 0
    for fname, l1, l2 in cites:
        for base in (REPO, os.path.join(REPO, "src"), REPO):
            p = os.path.join(base, fname)
            if os.path.exists(p):
                break
        else:
            p = None
        if p is None or not os.path.exists(p):
            return f"cited {fname} ABSENT"
        try:
            n = sum(1 for _ in open(p, errors="ignore"))
        except Exception:
            return f"cited {fname} unreadable"
        lo = int(l1)
        hi = int(l2) if l2 else lo
        checked += 1
        if hi <= n and lo >= 1:
            ok += 1
    if checked == 0:
        return "NO-CITE"
    if ok == checked:
        return f"cites OK ({checked} ref(s) in active tree)"
    return f"STALE-CITE ({checked-ok}/{checked} refs out of range)"

# ---------- parse body tables ----------
items = []
tbl = re.compile(r'^\|\s*([A-R]\d+)\s*\|\s*(P\d)\s*\|\s*`?\[([VFCR])\]`?\s*\|\s*(.+?)\s*\|\s*$', re.M)
section = None
for line in body.splitlines():
    m = re.match(r'^## §([A-R0])\. (.+)$', line)
    if m:
        section = m.group(1)
        continue
    m = tbl.match(line)
    if m:
        iid, sev, tag, text = m.groups()
        items.append(dict(fid=f"632-{iid}", orig=iid, src="body", ref="issue #632 body", sev=sev, tag=tag,
                          text=text, section=section))

# ---------- parse comments ----------
NEW_H = re.compile(r'^#{2,4}\s+((?:NEW-\d+|B\d+|SQL-\d+)\s*\([^)]*\)\s*[—-]\s*.+)$', re.M)
for c in comments:
    b = c["body"]
    buildperf = c["id"] in (7038195837, 7038248330)  # batch B1/B2 — author's B-IDs collide with body §B
    for m in NEW_H.finditer(b):
        head = m.group(1)
        im = re.match(r'((?:NEW-\d+|B\d+|SQL-\d+))\s*\(([^)]*)\)\s*[—-]\s*(.+)$', head)
        if not im:
            continue
        iid, sevtag, text = im.groups()
        tag = "V" if "`[V]`" in sevtag or "[V]" in sevtag else ("C" if "[C]" in sevtag else "V")
        sev = re.match(r'P[\d/P]+', sevtag).group(0) if re.match(r'P\d', sevtag) else "P?"
        fid = f"632-BP-{iid[1:]}" if buildperf else f"632-{iid}"
        items.append(dict(fid=fid, orig=iid, src=f"comment {c['id']}", ref=c["created_at"],
                          sev=sev, tag=tag, text=text.strip(), section=c["id"]))
    # S-rows and other tables (batch 7 ImageView probe results; batch 11 reuse)
    for lm in re.finditer(r'^\|\s*(S\d+)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*$', b, re.M):
        items.append(dict(fid=f"632-{lm.group(1)}", orig=lm.group(1), src=f"comment {c['id']}", ref=c["created_at"],
                          sev="PLAN", tag="P", text=f"sweep plan: {lm.group(2).strip()} (expected yield {lm.group(3).strip()})",
                          section=c["id"]))
    # R-rows (reuse registry)
    for lm in re.finditer(r'^\|\s*(R-\d)\s+([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|\s*([^|]+)\|', b, re.M):
        items.append(dict(fid=f"632-{lm.group(1)}", orig=lm.group(1), src=f"comment {c['id']}", ref=c["created_at"],
                          sev="P?", tag="R", text=f"{lm.group(2).strip()} | effort {lm.group(3).strip()} | risk {lm.group(4).strip()} | {lm.group(5).strip()}",
                          section=c["id"]))
    if c["id"] == 7037681554:
        items.append(dict(fid="632-SWEEP-S2", orig="SWEEP-S2", src=f"comment {c['id']}", ref=c["created_at"],
                          sev="P0", tag="V", text="Sweep S2: 174 Android XML attributes silently dropped by the inflater (stronger explanation for wrong widths/heights than missing layout laws) — grouped list with impact ranking in comment",
                          section=c["id"]))
        # preserve the 174-attribute lists verbatim
        sweep = b[b.find("## The 174 dropped attributes"):] if "## The 174 dropped attributes" in b else ""
        if sweep:
            sweep = sweep.split("## Why this batch matters")[0]
            open("/home/z/my-project/miniandroid/evidence/audit/632_BATCH8_174_ATTRIBUTES.md", "w",
                 encoding="utf-8").write("# BATCH 8 — Sweep S2: the 174 dropped attributes (verbatim from comment 7037681554)\n\n" + sweep)
    if c["id"] == 7038547151:
        items.append(dict(fid="632-REUSE-TOTAL", orig="REUSE-TOTAL", src=f"comment {c['id']}", ref=c["created_at"],
                          sev="P1", tag="V",
                          text="~600 KB hand-written C++ that authoritative upstream already provides (resource tables ~196 KB, webview ~398 KB, matrix/vector/blend) — reuse ROI table + constitution amendment proposal in comment",
                          section=c["id"]))

# dedupe by fid (keep first, note dups)
seen, dups = {}, []
final = []
for it in items:
    if it["fid"] in seen:
        dups.append(it["fid"])
        continue
    seen[it["fid"]] = True
    final.append(it)

# ---------- classify + source check ----------
manifest = open(os.path.join(REPO, "core_sources.manifest"), errors="ignore").read() if os.path.exists(os.path.join(REPO, "core_sources.manifest")) else ""
for it in final:
    orig = it.get("orig", it["fid"].split("-", 1)[1])
    if orig in RETRACTED:
        s, note = RETRACTED[it["fid"].split("-", 1)[1]]
        it["status"] = "RETRACTED-BY-AUTHOR"
        it["status_note"] = f"{s}: {note}"
    elif any(f in it["text"] for f in DEAD_CODE_FILES):
        it["status"] = "DEAD-CODE-RESCOPED"
        it["status_note"] = "cites view_renderer.cpp/real_layout.cpp — NOT in core_sources.manifest (batch 3, proven 3 ways); observation true of the uncompiled fallback engine only"
    else:
        it["status"] = "LIVE"
        it["status_note"] = ""
    if re.match(r"^632-S\d+$", it["fid"]):
        it["status"] = "PLAN-SWEEP"
        it["status_note"] = "systematic sweep proposal (batch 7 table); S2 was EXECUTED in batch 8 -> 174 dropped attributes (632-SWEEP-S2)"
    it["source_check"] = source_check(it["text"])

FIELDS = ["finding_id","original_id","batch_source","ref","section","severity","evidence_tag","registry_status",
          "status_note","source_check","original_wording"]
final.sort(key=lambda x: x["fid"])
with open(OUT, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=FIELDS, quoting=csv.QUOTE_MINIMAL)
    w.writeheader()
    for it in final:
        w.writerow({
            "finding_id": it["fid"], "original_id": it.get("orig", ""), "batch_source": it["src"], "ref": it["ref"],
            "section": it["section"], "severity": it["sev"], "evidence_tag": it["tag"],
            "registry_status": it["status"], "status_note": it["status_note"],
            "source_check": it["source_check"], "original_wording": it["text"],
        })

from collections import Counter
st = Counter(it["status"] for it in final)
print("registry items:", len(final))
for k, v in sorted(st.items()):
    print(f"  {k}: {v}")
print("dups skipped:", len(dups))
sc = Counter(it["source_check"].split(" ")[0] for it in final)
print("source checks:", dict(sc))
# reconciliation vs title
print("title claims 194 items; registry rows:", len(final), "; delta:", len(final) - 194)
