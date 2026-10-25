#!/usr/bin/env python3
"""CONT-34 F-NEW-525: ProviderInfo.exported + multiprocess seeding law.

DEX ground truth (cont26 disasm, aurora APK):
  ShizukuProvider.attachInfo @0x3 iget-boolean multiprocess @0x5 if-nez->0x15
  @0x7 iget-boolean exported @0x9 if-eqz->0xf @0xf const 'android:exported
  must be true' @0x11 invoke Lop0;.a = ISE. Engine seeds left both unset ->
  exported read 0 -> ISE at pc0x11 = exact crash (aurora/batterymonitor/
  shizuwall). Manifest truth: ShizukuProvider android:exported=true.
AOSP law: PackageParser populates ProviderInfo.exported (android:exported,
default FALSE) and multiprocess (android:multiprocess, default FALSE).
Fix mirrors the proven #371 grantUriPermissions law at all 3 seed sites.
Idempotent; anchor-verified."""
import re, sys
from pathlib import Path

ENG_H = Path("miniandroid/src/dex/dalvik_engine.h")
ENG_C = Path("miniandroid/src/dex/dalvik_engine.cpp")
EXEC_C = Path("miniandroid/src/runtime/execution_engine.cpp")

def patch():
    n = 0
    # ---- 1. dalvik_engine.h: member + setter after grants member ----
    h = ENG_H.read_text()
    if "manifest_provider_exported_" not in h:
        anchor = ("    std::vector<std::pair<std::string, bool>> "
                  "manifest_provider_grants_;")
        assert anchor in h, "h member anchor missing"
        h = h.replace(anchor, anchor + (
            "\n    // F-NEW-525: per-provider android:exported (AOSP PackageParser\n"
            "    // ProviderInfo law — ShizukuProvider.attachInfo enforces\n"
            "    // exported=true / multiprocess=false; manifest_reader already\n"
            "    // parses both).\n"
            "    std::vector<std::pair<std::string, bool>> "
            "manifest_provider_exported_;"), 1)
        setter_anchor = (
            "    void set_manifest_provider_grants(\n"
            "        std::vector<std::pair<std::string, bool>> name_grants) {\n"
            "        manifest_provider_grants_ = std::move(name_grants);\n"
            "    }")
        assert setter_anchor in h, "h setter anchor missing"
        h = h.replace(setter_anchor, setter_anchor + (
            "\n    // F-NEW-525: per-provider android:exported (AOSP law).\n"
            "    void set_manifest_provider_exported(\n"
            "        std::vector<std::pair<std::string, bool>> name_exported) {\n"
            "        manifest_provider_exported_ = std::move(name_exported);\n"
            "    }"), 1)
        ENG_H.write_text(h); n += 1
        print("h: member+setter added")
    # ---- 2. execution_engine.cpp: populate after prov_grants call ----
    e = EXEC_C.read_text()
    if "set_manifest_provider_exported" not in e:
        anchor = ("            dalvik_engine_.set_manifest_provider_grants"
                  "(prov_grants);")
        assert anchor in e, "exec anchor missing"
        e = e.replace(anchor, anchor + (
            "\n            // F-NEW-525: per-provider android:exported "
            "(AOSP PackageParser law).\n"
            "            std::vector<std::pair<std::string, bool>> "
            "prov_exported;\n"
            "            for (const auto& p : result.apk_info.providers) {\n"
            "                std::string cls = p.name;\n"
            "                if (!cls.empty()) {\n"
            "                    if (cls[0] == '.')\n"
            "                        cls = result.apk_info.package_name + cls;\n"
            "                    else if (cls.find('.') == std::string::npos)\n"
            "                        cls = result.apk_info.package_name + \".\" "
            "+ cls;\n"
            "                }\n"
            "                prov_exported.emplace_back(cls, p.exported);\n"
            "            }\n"
            "            dalvik_engine_.set_manifest_provider_exported"
            "(prov_exported);"), 1)
        EXEC_C.write_text(e); n += 1
        print("exec: population added")
    # ---- 3. dalvik_engine.cpp: seed at 3 sites ----
    c = ENG_C.read_text()
    if "F-NEW-525" not in c:
        # helper text used at all sites (lookup fn name varies)
        def seed_block(lookup_expr):
            return (
                "\n                // F-NEW-525: exported + multiprocess "
                "(AOSP PackageParser\n"
                "                // ProviderInfo law — defaults FALSE, manifest"
                " value wins;\n"
                "                // ShizukuProvider.attachInfo enforces "
                "exported=true /\n"
                "                // multiprocess=false at attach). Unset "
                "previously read\n"
                "                // 0 for exported too — the seed is drift-free"
                " for every\n"
                "                // manifest that does not declare exported"
                "=true.\n"
                f"                for (const auto& [ename, eval] : "
                f"manifest_provider_exported_) {{\n"
                f"                    if ({lookup_expr}) {{\n"
                "                        heap_.set_object_field(\n"
                "                            pi_id, \"exported\",\n"
                "                            DalvikValue::make_bool(eval));\n"
                "                        break;\n"
                "                    }\n"
                "                }\n"
                "                heap_.set_object_field(\n"
                "                    pi_id, \"multiprocess\",\n"
                "                    DalvikValue::make_bool(false));")
        # site A: attachInfo install (uses grant loop keyed gname == pcls)
        a_anchor = ("                heap_.set_object_field(pinfo_id, "
                    "\"grantUriPermissions\",\n"
                    "                                       "
                    "DalvikValue::make_bool(grant_up));")
        assert a_anchor in c, "site A anchor missing"
        c = c.replace(a_anchor, a_anchor + seed_block("ename == pcls"), 1)
        print("cpp: site A (attachInfo) seeded")
        # site B: resolveContentProvider (grant loop keyed gname == owner_class)
        b_anchor = ("            for (const auto& [gname, gval] : "
                    "manifest_provider_grants_) {\n"
                    "                if (gname == owner_class) {\n"
                    "                    heap_.set_object_field(\n"
                    "                        pi_id, \"grantUriPermissions\",\n"
                    "                        DalvikValue::make_bool(gval));\n"
                    "                    break;\n"
                    "                }\n"
                    "            }")
        assert b_anchor in c, "site B anchor missing"
        c = c.replace(b_anchor, b_anchor + (
            "\n            // F-NEW-525: exported + multiprocess (AOSP "
            "PackageParser law).\n"
            "            for (const auto& [ename, eval] : "
            "manifest_provider_exported_) {\n"
            "                if (ename == owner_class) {\n"
            "                    heap_.set_object_field(\n"
            "                        pi_id, \"exported\",\n"
            "                        DalvikValue::make_bool(eval));\n"
            "                    break;\n"
            "                }\n"
            "            }\n"
            "            heap_.set_object_field(\n"
            "                pi_id, \"multiprocess\",\n"
            "                DalvikValue::make_bool(false));"), 1)
        print("cpp: site B (resolveContentProvider) seeded")
        # site C: getProviderInfo (grant loop keyed gname in norm/bare/prov_class)
        c_anchor = ("        for (const auto& [gname, gval] : "
                    "manifest_provider_grants_) {\n"
                    "            if (gname == norm || gname == bare || "
                    "gname == prov_class) {\n"
                    "                heap_.set_object_field(pi_id, "
                    "\"grantUriPermissions\",\n"
                    "                                       "
                    "DalvikValue::make_bool(gval));\n"
                    "                break;\n"
                    "            }\n"
                    "        }")
        assert c_anchor in c, "site C anchor missing"
        c = c.replace(c_anchor, c_anchor + (
            "\n        // F-NEW-525: exported + multiprocess (AOSP "
            "PackageParser law).\n"
            "        for (const auto& [ename, eval] : "
            "manifest_provider_exported_) {\n"
            "            if (ename == norm || ename == bare || "
            "ename == prov_class) {\n"
            "                heap_.set_object_field(pi_id, \"exported\",\n"
            "                                       "
            "DalvikValue::make_bool(eval));\n"
            "                break;\n"
            "            }\n"
            "        }\n"
            "        heap_.set_object_field(\n"
            "            pi_id, \"multiprocess\", "
            "DalvikValue::make_bool(false));"), 1)
        print("cpp: site C (getProviderInfo) seeded")
        ENG_C.write_text(c); n += 1
    print(f"patched: {n} file groups")

if __name__ == "__main__":
    patch()
