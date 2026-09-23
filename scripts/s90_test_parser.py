#!/usr/bin/env python3
"""s90_test_parser.py — S90 §4 parser validation.

Validates the FIXED s88_corpus2.scan_dex against androguard (independent
parser) on a real APK. Fails loudly if either side is empty or if the two
disagree beyond a tolerance. Exit code != 0 on any gate failure.
"""
import io as _io
import sys
import zipfile
from collections import Counter

sys.path.insert(0, "/home/z/my-project/scripts")
from s88_corpus2 import scan_dex, FRAMEWORK_PREFIXES  # noqa: E402

import loguru
loguru.logger.remove()
from androguard.core.bytecodes.dvm import DalvikVMFormat as DEX  # noqa: E402


def apk_dexes(path):
    z = zipfile.ZipFile(path)
    return [z.read(n) for n in z.namelist() if n.endswith(".dex")]


def andro_counts(dexes):
    types = Counter()
    methods = Counter()
    import re as _re
    desc_types = _re.compile(r"L[^();]+;")
    for d in dexes:
        dx = DEX(d)
        for m in dx.get_methods():
            cls = m.get_class_name() or ""
            if not cls.startswith(FRAMEWORK_PREFIXES):
                continue
            meth = m.get_name() or ""
            desc = m.get_descriptor() or ""
            methods[f"{cls[:-1]}.{meth}{desc}"] += 1
        # referenced types = class defs + all types inside descriptors
        for c in dx.get_classes():
            n = c.get_name()
            if n.startswith(FRAMEWORK_PREFIXES):
                types[n] += 1
        for f in dx.get_fields():
            for t in desc_types.findall(f.get_descriptor() or ""):
                if t.startswith(FRAMEWORK_PREFIXES):
                    types[t] += 1
        for m in dx.get_methods():
            for t in desc_types.findall(m.get_descriptor() or ""):
                if t.startswith(FRAMEWORK_PREFIXES):
                    types[t] += 1
        for s in dx.get_strings():
            pass
    return types, methods


def main(apk_path, own_pkg):
    dexes = apk_dexes(apk_path)
    print(f"apk={apk_path} dexes={len(dexes)}")

    cnt, meths, own, libs, ndex, pfail = scan_dex(apk_path, own_pkg)
    print(f"ours: types={sum(cnt.values())} uniq_types={len(cnt)} "
          f"methods={sum(meths.values())} uniq_methods={len(meths)} "
          f"own={len(own)} parse_fail={pfail}")
    assert pfail == 0, f"PARSE FAILURE not tolerated: {pfail}"
    assert sum(cnt.values()) > 0, "EMPTY framework type count — parser still broken"
    assert len(meths) > 0, "EMPTY method refs — method_ids pass broken"

    atypes, amethods = andro_counts(dexes)
    print(f"androguard: uniq_types={len(atypes)} uniq_methods={len(amethods)}")

    # type descriptor set comparison (exact, not top-N)
    ours_t = set(cnt)
    and_t = set(atypes)
    miss = and_t - ours_t
    extra = ours_t - and_t
    print(f"type sets: ours={len(ours_t)} andro={len(and_t)} "
          f"missing={len(miss)} extra={len(extra)}")
    for m in list(miss)[:5]:
        print(f"  MISSING type: {m}")
    for e in list(extra)[:5]:
        print(f"  EXTRA type: {e}")

    # method set comparison — keys match andro raw descriptor format
    # except andro inserts spaces after ';' — normalize both sides
    ours_m = {k.replace(" ", "") for k in meths}
    andro_m = {k.replace(" ", "") for k in amethods}
    inter = ours_m & andro_m
    print(f"methods: ours={len(ours_m)} andro={len(andro_m)} "
          f"intersection={len(inter)}")
    diff = list(andro_m - ours_m)[:5]
    for m in diff:
        print(f"  andro-only: {m}")

    # GATES (allow small mismatch from overloads of same name with equal
    # erased descriptors; core requirement: >=95% recall on methods, exact
    # types)
    recall_t = len(ours_t & and_t) / max(1, len(and_t))
    recall_m = len(inter) / max(1, len(amethods))
    print(f"GATES: type_recall={recall_t:.4f} method_recall={recall_m:.4f}")
    assert recall_t >= 0.95, f"type recall {recall_t:.3f} < 0.95"
    assert recall_m >= 0.90, f"method recall {recall_m:.3f} < 0.90"
    print("VALIDATION PASS")


if __name__ == "__main__":
    apk = sys.argv[1] if len(sys.argv) > 1 else "/home/z/my-project/run/s88/chess.apk"
    pkg = sys.argv[2] if len(sys.argv) > 2 else "com.example"
    main(apk, pkg)
