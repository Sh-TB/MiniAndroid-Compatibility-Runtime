#!/usr/bin/env python3
"""CONT-37: the interface families behind the text painter.
(a) dump Lec0;, Lm51;, Luv;, Lvv; method tables;
(b) scan EVERY invoke of form <iface>->I(Loc0;)V (any of those ifaces);
(c) callers of Lqe1.d / Lld1.d (the painter factories) and where results flow."""
import zipfile
from loguru import logger
logger.remove()
from androguard.core.dex import DEX

z = zipfile.ZipFile("/home/z/my-project/tmp/cont35_apks/composeStopwatch_1009011.apk")
d = DEX(z.read("classes.dex"))

IFACES = {"Lec0;", "Lm51;", "Luv;", "Lvv;"}

print("== interface method tables ==")
for c in d.get_classes():
    if c.get_name() in IFACES:
        print(f"  {c.get_name()}:")
        for m in c.get_methods():
            print(f"     {m.get_name()}{m.get_descriptor()}")

sig_sites = []
fact_calls = []
for c in d.get_classes():
    for m in c.get_methods():
        try:
            if m.get_code() is None:
                continue
            for ins in m.get_instructions():
                nm = ins.get_name()
                out = ins.get_output().strip()
                if "invoke" not in nm or "->" not in out:
                    continue
                pre = out.split("->")[0]
                tcls = pre.split(",")[-1].strip() if "," in pre else pre.strip()
                rest = out.split("->")[1]
                tm = rest.split(":")[0].split("(")[0]
                tdesc = rest.split(":")[0]
                if tcls in IFACES and tm == "I" and tdesc.startswith("I(Loc0;)"):
                    sig_sites.append((m.get_class_name(), m.get_name(), nm, tcls, out[:120]))
                if nm.startswith("invoke") and tcls in ("Lqe1;", "Lld1;") and tm == "d":
                    fact_calls.append((m.get_class_name(), m.get_name(), nm, tcls, out[:120]))
        except Exception:
            continue

print(f"\n== I(Loc0;)V invocations on painter ifaces: {len(sig_sites)} ==")
for x in sig_sites:
    print(" ", x)
print(f"\n== painter-factory (Lqe1.d/Lld1.d) call sites: {len(fact_calls)} ==")
for x in fact_calls:
    print(" ", x)
