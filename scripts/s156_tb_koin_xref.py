#!/usr/bin/env python3
"""s156_tb_koin_xref.py — T4 stage-2b: androguard xref of the Koin startKoin
chain in net.thunderbird.android_33.

Questions:
  1. Who calls startKoin (Lorg/koin/core/context/StartKt or GlobalContext)?
  2. In ThunderbirdApp.attachBaseContext / BaseApplication.onCreate /
     FeatureFlagApplication.onCreate — what is the ORDER of invokes
     (startKoin before or after the first inject)?
  3. What does DecryptedFileProvider.<clinit> call (the R8-merged
     CacheControl$Companion.get$default chain)?
Output: stdout + evidence/s156_4app/TB_KOIN_XREF.json
"""
import json
from pathlib import Path

from androguard.core.dex import DEX
from loguru import logger

logger.remove()

BASE = Path("/home/z/my-project/repo")
EVID = BASE / "evidence/s156_4app"
EVID.mkdir(parents=True, exist_ok=True)
APK = Path("/home/z/my-project/upload/canonical_apks/net.thunderbird.android_33.apk")

TARGETS = [
    "Lnet/thunderbird/android/ThunderbirdApp;",
    "Lnet/thunderbird/app/common/BaseApplication;",
    "Lcom/fsck/k9/provider/DecryptedFileProvider;",
    "Lokhttp3/CacheControl$Companion;",
]
METHODS_OF_INTEREST = ("attachBaseContext", "onCreate", "<clinit>", "get$default")


def invoke_refs(m):
    """Ordered list of (idx, opcode, method_ref) for invoke-* instructions."""
    out = []
    idx = 0
    for ins in m.get_instructions():
        op = ins.get_name()
        if op.startswith("invoke"):
            last = ins.get_operands()[-1]
            ref = last[2] if isinstance(last, tuple) and len(last) >= 3 else "?"
            out.append((idx, op, str(ref)))
        idx += ins.get_length()
    return out


def main():
    dexes = sorted(EVID.glob("tb_dex/*.dex"))
    if not dexes:
        import zipfile
        with zipfile.ZipFile(APK) as z:
            dexdir = EVID / "tb_dex"
            dexdir.mkdir(exist_ok=True)
            for n in z.namelist():
                if n.endswith(".dex") and n.count("/") == 0:
                    (dexdir / Path(n).name).write_bytes(z.read(n))
        dexes = sorted(dexdir.glob("*.dex"))
    print("dexes:", [d.name for d in dexes])

    startkoin_callers = []
    target_calls = {}
    for dpath in dexes:
        d = DEX(dpath.read_bytes())  # EncodedMethods via class iteration
        for c in d.get_classes():
            cls = c.get_name()
            for m in c.get_methods():
                name = m.get_name()
                try:
                    refs = invoke_refs(m)
                except Exception:
                    continue
                for idx, op, ref in refs:
                    if "startKoin" in ref:
                        startkoin_callers.append({"from": f"{cls}->{name}", "at": idx, "via": ref, "dex": dpath.name})
                if cls in TARGETS and any(k in name for k in METHODS_OF_INTEREST):
                    key = f"{cls}->{name}"
                    target_calls[key] = [{"pc": i, "op": o, "ref": r} for i, o, r in refs]

    out = {"startkoin_callers": startkoin_callers, "target_calls": target_calls}
    (EVID / "TB_KOIN_XREF.json").write_text(json.dumps(out, indent=1))
    print("== startKoin callers ==")
    for c in startkoin_callers:
        print("  ", c["from"], "pc", c["at"], "via", c["via"], c["dex"])
    print("== target method invoke orders ==")
    for k, rows in target_calls.items():
        print(" --", k, f"({len(rows)} invokes)")
        for r in rows[:28]:
            print(f"    pc={r['pc']:5d} {r['op']:18s} {r['ref']}")


if __name__ == "__main__":
    main()
