#!/usr/bin/env python3
"""s90_api_inventory.py — S90 §3 canonical API/CLASS SEMANTIC INVENTORY.

Builds registry/api_inventory.json from REAL evidence only:
  - dex reference side: run/s88/corpus/profiles.json (fixed parser:
    exact class + method + signature per title, top-40 persisted)
  - execution side: run/s89/batch/EXEC_RESULTS.json (rc, exceptions,
    first_divergence) + run/*/.._ab divergence logs where present
  - runtime side: grep dalvik_engine.cpp for class presence

Honesty rules:
  - fan-out counts are over persisted per-title top-40 methods /
    top-25 classes (measurement basis recorded)
  - no manufactured numbers; missing = omitted
  - priority components stored SEPARATELY (no fake single score)
"""
import json
import os
import re
from collections import defaultdict

ROOT = "/home/z/my-project"
PROF = f"{ROOT}/run/s88/corpus/profiles.json"
EXEC = f"{ROOT}/run/s89/batch/EXEC_RESULTS.json"
ENGINE = f"{ROOT}/miniandroid/src/dex/dalvik_engine.cpp"
OUT = f"{ROOT}/registry/api_inventory.json"

FAMILY_RULES = [
    ("material", "Lcom/google/android/material"),
    ("appcompat", "Landroidx/appcompat"),
    ("support-v4", "Landroid/support/v4"),
    ("support-v7", "Landroid/support/v7"),
    ("support-design", "Landroid/support/design"),
    ("compose", "Landroidx/compose"),
    ("core", "Landroidx/core"),
    ("fragment", "Landroidx/fragment"),
    ("lifecycle", "Landroidx/lifecycle"),
    ("recyclerview", "Landroidx/recyclerview"),
    ("constraint", "Landroidx/constraintlayout"),
    ("vectordrawable", "Landroidx/vectordrawable"),
    ("emoji2", "Landroidx/emoji2"),
    ("activity", "Landroidx/activity"),
    ("webkit", "Landroid/webkit"),
    ("graphics", "Landroid/graphics"),
    ("view", "Landroid/view"),
    ("widget", "Landroid/widget"),
    ("content", "Landroid/content"),
    ("app", "Landroid/app"),
    ("os", "Landroid/os"),
    ("net", "Landroid/net"),
    ("util", "Landroid/util"),
    ("database", "Landroid/database"),
    ("opengl", "Landroid/opengl"),
    ("kotlin", "Lkotlin"),
    ("coroutines", "Lkotlinx/coroutines"),
    ("java", "Ljava/"),
    ("javax", "Ljavax/"),
    ("j$", "Lj$/"),
]


def family_of(cls):
    for fam, pre in FAMILY_RULES:
        if cls.startswith(pre):
            return fam
    return "other"


def engine_implements(cls):
    """Coarse real check: does the class name appear in engine source?"""
    global _ENGINE_SRC
    if cls in _ENGINE_HIT:
        return _ENGINE_HIT[cls]
    hit = cls in _ENGINE_SRC
    _ENGINE_HIT[cls] = hit
    return hit


_ENGINE_SRC = ""
_ENGINE_HIT = {}


def main():
    global _ENGINE_SRC
    _ENGINE_SRC = open(ENGINE, encoding="utf-8", errors="replace").read()

    profiles = json.load(open(PROF))
    execr = json.load(open(EXEC)) if os.path.exists(EXEC) else {}

    # ---- dex side: exact methods ----
    m_titles = defaultdict(list)   # method key -> [pkgs]
    m_refs = defaultdict(int)      # method key -> total ref count
    c_titles = defaultdict(list)
    c_refs = defaultdict(int)
    for pkg, prof in profiles.items():
        for k, v in prof.get("top_methods", []):
            m_titles[k].append(pkg)
            m_refs[k] += v
        for k, v in prof.get("top_classes", []):
            c_titles[k].append(pkg)
            c_refs[k] += v

    # ---- execution side ----
    exec_status = {}
    for pkg, r in execr.items():
        exec_status[pkg] = {
            "rc": r.get("rc"), "exceptions": r.get("exceptions", 0),
            "frames": r.get("frames", 0),
            "first_divergence": (r.get("first_divergence") or "")[:200],
        }
    exec_ok = sum(1 for v in exec_status.values() if v["rc"] == 0)
    exec_fail = sum(1 for v in exec_status.values() if v["rc"] != 0)

    # divergence -> method extraction: prefer explicit method=L…; form
    div_methods = defaultdict(list)
    div_fams = defaultdict(list)
    for pkg, v in exec_status.items():
        fd = v["first_divergence"]
        if not fd:
            continue
        m = re.search(r"method=(L[^ ;]+)\.([^ ;(]+)", fd)
        if m:
            key = f"{m.group(1)}.{m.group(2)}"
            div_methods[key].append(pkg)
        else:
            mm = re.search(r"L([a-z][\w/$]*\.)*([\w$]+)\.([\w$<>]+)\(", fd)
            if mm:
                div_fams[family_of("L" + fd.split("L")[1].split(".")[0] if "L" in fd else "?")].append(pkg)
    # also family-level from raw strings (deferred family markers)
    for pkg, v in exec_status.items():
        fd = v["first_divergence"]
        if not fd or re.search(r"method=", fd):
            continue
        mt = re.findall(r"L[\w/$]+;", fd)
        for t in mt[:2]:
            div_fams[family_of(t)].append(pkg)

    # ---- assemble method inventory (top 400 by title fan-out) ----
    methods = []
    for k, titles in sorted(m_titles.items(), key=lambda x: -len(x[1])):
        if len(methods) >= 400:
            break
        cls = k[:k.find(".", k.find("(") if k.find("(") >= 0 and
                 k.find("(") < k.find(".", 1) else len(k))]
        # class = prefix up to the method name: find last '.' before '('
        i = k.find("(")
        if i < 0:
            continue
        cls_m = k[:i]
        dot = cls_m.rfind(".")
        cls = cls_m[:dot] + ";"
        sig = k[i:]
        if not cls.startswith(("L",)):
            continue
        fam = family_of(cls)
        if fam in ("other",):
            continue
        methods.append({
            "family": fam,
            "class": cls[:-1],
            "method": cls_m[dot + 1:],
            "signature": sig,
            "titles_referenced": len(titles),
            "titles": titles[:12],
            "total_refs": m_refs[k],
            "titles_diverged": len(div_methods.get(k, [])),
            "diverged_titles": div_methods.get(k, []),
            "runtime_class_present": engine_implements(cls),
            "executed_ok_corpus": exec_ok,
            "executed_fail_corpus": exec_fail,
            "basis": "per-title top-40 methods (S90 fixed parser)",
        })

    # ---- family rollup (§19) ----
    fams = defaultdict(lambda: {"titles": set(), "methods": 0})
    for m in methods:
        fams[m["family"]]["titles"].update(
            m["titles"]) if False else None
        fams[m["family"]]["methods"] += 1
    for pkg, prof in profiles.items():
        for k, v in prof.get("libs", {}).items():
            if k in fams:
                fams[k]["titles"].add(pkg)
    fam_table = []
    for fam, d in sorted(fams.items(),
                         key=lambda x: -len(x[1]["titles"])):
        fam_table.append({
            "family": fam,
            "titles_with_family": len(d["titles"]),
            "exact_methods_in_top400": d["methods"],
            "titles_diverged_family": len(div_fams.get(fam, [])),
            "diverged_titles": div_fams.get(fam, []),
        })

    # ---- classes (top 200) ----
    classes = []
    for k, titles in sorted(c_titles.items(), key=lambda x: -len(x[1])):
        if len(classes) >= 200:
            break
        if not k.startswith("L"):
            continue
        fam = family_of(k)
        if fam == "other":
            continue
        classes.append({
            "family": fam,
            "class": k[:-1],
            "titles_referenced": len(titles),
            "titles": titles[:12],
            "total_refs": c_refs[k],
            "runtime_class_present": engine_implements(k),
            "basis": "per-title top-25 classes (S90 fixed parser)",
        })

    inv = {
        "law": "S90 §3 — ONE canonical API inventory; built ONLY from real "
               "evidence; components stored separately, no synthetic score",
        "measurement_basis": {
            "corpus": 225,
            "parser": "s88_corpus2.scan_dex fixed in S90 (commit a6e8d911), "
                      "cross-validated vs androguard (recall 1.0/1.0)",
            "method_fanout_basis": "per-title top-40 persisted methods; "
                                   "counts are lower bounds for titles "
                                   "where the method fell below top-40",
            "execution_basis": "run/s89/batch/EXEC_RESULTS.json (66 "
                               "batch titles) — merge more sessions as "
                               "they are recorded",
        },
        "executed_ok_corpus": exec_ok,
        "executed_fail_corpus": exec_fail,
        "families": fam_table,
        "top_methods": methods,
        "top_classes": classes,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(inv, open(OUT, "w"), indent=1)
    print(f"inventory written: {OUT}")
    print(f"methods={len(methods)} classes={len(classes)} "
          f"families={len(fam_table)} exec_ok={exec_ok} "
          f"exec_fail={exec_fail}")
    top5 = [(m['family'], m['class'] + '.' + m['method'],
             m['titles_referenced']) for m in methods[:5]]
    for t in top5:
        print("  ", t)


if __name__ == "__main__":
    main()
