#!/usr/bin/env python3
"""s59_reconcile_matrix.py — build the full open-issue reconciliation matrix.

For each of the 278 open issues, records:
  issue number, title, label group (per-app vs work), package (per-app),
  corpus status (sourced? sha? profile present?), label-implied state,
  registry cross-reference (F-NEW ids named in body), and reconciliation
  verdict using the evidence statuses:
  IMPLEMENTED / TESTED / OBSERVED / PARTIAL / BLOCKED / PENDING / SUPERSEDED

Closure rule applied: NO per-app record is closed without current-HEAD
runtime evidence meeting its acceptance criteria; per-app records whose
state labels were maintained by earlier waves are cross-checked against
the canonical corpus profiles (run/s88/corpus/profiles.json).
"""
import json
import re

PAGES = ["run/audit/issues_p1.json", "run/audit/issues_p2.json", "run/audit/issues_p3.json"]
PROFILES = "run/s88/corpus/profiles.json"
OUT = "run/audit/reconciliation_matrix.json"


def lab(i):
    return [l["name"] if isinstance(l, dict) else l for l in i["labels"]]


def main():
    items = []
    for p in PAGES:
        items += json.load(open(p))
    profiles = json.load(open(PROFILES))
    corpus_pkgs = set(profiles.keys())

    rows = []
    stats = {"per_app": 0, "work": 0,
             "per_app_sourced": 0, "per_app_unsourced": 0,
             "verdicts": {}}
    for it in items:
        labels = lab(it)
        body = it.get("body") or ""
        is_per_app = any(x in labels for x in ("compatibility", "app", "game"))
        m = re.search(r"Package:\s*`([A-Za-z0-9._]+)`", body)
        pkg = m.group(1) if m else None
        # package from title fallback: [GAME-074] org.secuso.privacyfriendlymemory
        if not pkg:
            m2 = re.match(r"\[(?:GAME|APP)-\d+\]\s+(\S+)\s", it["title"])
            pkg = m2.group(1) if m2 else None
        in_corpus = pkg in corpus_pkgs if pkg else False
        fnew_ids = sorted(set(re.findall(r"F-NEW-\d+", body)))
        row = {
            "n": it["number"],
            "title": it["title"][:120],
            "labels": labels,
            "per_app": is_per_app,
            "package": pkg,
            "in_corpus": in_corpus,
            "state_label": next((x for x in labels if x.startswith("state-")), None),
            "executed": "executed" in labels,
            "fnew_named": fnew_ids[:8],
            "updated": it["updated_at"][:10],
        }
        if is_per_app:
            stats["per_app"] += 1
            if in_corpus:
                stats["per_app_sourced"] += 1
                row["verdict"] = "PENDING"  # sourced but runtime acceptance not proven per-issue
            else:
                stats["per_app_unsourced"] += 1
                row["verdict"] = "PENDING"
            if "blocked" in labels:
                row["verdict"] = "BLOCKED"
            if row["state_label"] == "state-nonblank":
                row["verdict"] = "OBSERVED"
        else:
            stats["work"] += 1
            if it["number"] == 386:
                row["verdict"] = "PENDING"   # this mission's host issue
            elif it["number"] == 375:
                row["verdict"] = "PENDING"
            else:
                row["verdict"] = "PENDING"
        stats["verdicts"][row["verdict"]] = stats["verdicts"].get(row["verdict"], 0) + 1
        rows.append(row)

    rows.sort(key=lambda r: r["n"])
    json.dump({"total": len(rows), "stats": stats, "rows": rows},
              open(OUT, "w"), indent=1)
    print(f"matrix rows: {len(rows)} -> {OUT}")
    print(f"stats: {json.dumps(stats, indent=1)}")
    # cross-check: label state-notblank vs corpus
    nonblank = [r for r in rows if r["state_label"] == "state-nonblank"]
    in_c = sum(1 for r in nonblank if r["in_corpus"])
    print(f"state-nonblank rows: {len(nonblank)}, of which package in corpus: {in_c}")
    executed = [r for r in rows if r["executed"]]
    in_c2 = sum(1 for r in executed if r["in_corpus"])
    print(f"executed rows: {len(executed)}, of which in corpus: {in_c2}")
    notested = [r for r in rows if "not-tested" in r["labels"]]
    in_c3 = sum(1 for r in notested if r["in_corpus"])
    print(f"not-tested rows: {len(notested)}, of which in corpus: {in_c3}")


if __name__ == "__main__":
    main()
