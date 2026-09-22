#!/usr/bin/env python3
"""s82_refs_bulk.py — §10 bulk pass: official F-Droid reference screenshot for
EVERY remaining title (never fabricated; REFERENCE_NOT_AVAILABLE recorded when
the package page ships none). Resumable via registry REFERENCE.STATUS."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import s82_lib as L  # noqa


def main():
    reg = L.load_registry()
    todo = [t for t in reg["TITLES"]
            if (t.get("REFERENCE") or {}).get("STATUS") in (None, "PENDING", "REFERENCE_NOT_AVAILABLE", "")]
    print("bulk references todo:", len(todo), flush=True)
    for i, t in enumerate(todo):
        r = L.get_reference(t["PACKAGE"])
        t["REFERENCE"] = r
        if (i + 1) % 10 == 0:
            L.save_registry(reg)
            print(f"...{i+1}/{len(todo)}", flush=True)
    L.save_registry(reg)
    ok = sum(1 for t in reg["TITLES"] if (t.get("REFERENCE") or {}).get("STATUS") == "OK")
    na = sum(1 for t in reg["TITLES"] if (t.get("REFERENCE") or {}).get("STATUS") == "REFERENCE_NOT_AVAILABLE")
    print(f"TOTAL references OK={ok} NA={na} of {len(reg['TITLES'])}")


if __name__ == "__main__":
    main()
