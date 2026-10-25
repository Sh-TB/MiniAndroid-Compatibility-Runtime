#!/usr/bin/env python3
"""CONT-34 F-NEW-526: android.os.ServiceManager framework law.

Ground truth (aurora, cont34 batch-50 census -> ShizukuProvider chain):
  [CLASS_INIT] Lpy7;.<clinit> ... [R350-FORNAME deferred CNF] android.os.ServiceManager
  -> clinit's own catch swallows CNF, getService static Method field NEVER set
  [SGET-MISS] key=Lpy7;.getService obj_id=0 -> f141-null-recv NPE
  'Method.invoke on a null object reference' @ Lpy7;.a pc=19 -> APP BOUNDARY.
AOSP law: android.os.ServiceManager is a REAL (hidden) framework class on
every device — Class.forName succeeds, getMethod('getService') finds it,
invoke answers the live IBinder. Engine had ZERO ServiceManager presence.
Fix (2 touch points, mirrors R-NEW-354 + F-NEW-516 exemplars):
  1. R-NEW-354 kFrameworkClasses += android.os.ServiceManager (forName law).
  2. bridge_to_api: ServiceManager.getService/checkService(String) ->
     deterministic per-name non-null Binder token (class_desc Binder; —
     hierarchy row Binder->IBinder exists, py7.a check-cast IBinder passes;
     approximation RECORDED: every name answers present — never-null family
     law, F-NEW-516 precedent)."""
import sys
from pathlib import Path

ENG_C = Path("miniandroid/src/dex/dalvik_engine.cpp")

def patch():
    c = ENG_C.read_text()
    n = 0
    # ---- 1. R-NEW-354 registry list ----
    old_reg = ('        static const char* kFrameworkClasses[] = {\n'
               '            "android.os.SystemProperties",\n'
               '        };')
    new_reg = ('        static const char* kFrameworkClasses[] = {\n'
               '            "android.os.SystemProperties",\n'
               '            // F-NEW-526: hidden-but-real framework class —\n'
               '            // shizuku-style reflective service holders probe it\n'
               '            // in <clinit> (py7.a evidence: forName CNF swallowed\n'
               '            // by the clinit catch left getService Method null ->\n'
               '            // NPE at the later getService.invoke). AOSP: forName\n'
               '            // succeeds on every device.\n'
               '            "android.os.ServiceManager",\n'
               '        };')
    if "android.os.ServiceManager" not in c:
        assert old_reg in c, "registry anchor missing"
        c = c.replace(old_reg, new_reg, 1)
        print("1. R-NEW-354 registry extended")
        n += 1
    # ---- 2. bridge_to_api law before the Logger block ----
    if "Landroid/os/ServiceManager;" not in c:
        anchor = '    if (class_name == "Ljava/util/logging/Logger;") {'
        assert anchor in c, "logger anchor missing"
        law = '''    // ────────────────────────────────────────────────────────────────────
    // F-NEW-526 — android.os.ServiceManager (AOSP hidden framework class,
    // android.os.ServiceManager.java). Statics: getService(String) /
    // checkService(String) answer the live IBinder for every framework
    // service name — deterministic per-name token (create-and-cache,
    // never-null family law, F-NEW-516 precedent; approximation RECORDED:
    // real AOSP answers null for unknown names, the engine models every
    // service as present — callers that probe optional services get a
    // non-null binder instead of an NPE kill). class_desc = Binder; (the
    // Binder→IBinder hierarchy row exists, so py7.a's check-cast
    // Landroid/os/IBinder; passes). The R-NEW-354 registry arm makes
    // Class.forName('android.os.ServiceManager') succeed, so reflective
    // holders (shizuku py7: forName → getMethod('getService') →
    // invoke(null, name)) complete the full AOSP round-trip.
    // ────────────────────────────────────────────────────────────────────
    if (class_name == "Landroid/os/ServiceManager;" &&
        (method == "getService" || method == "checkService")) {
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_null();
        std::string sname;
        for (const auto& a : args) {
            if (a.type == DalvikType::STRING_REF && !a.string_val.empty()) {
                sname = a.string_val;
                break;
            }
        }
        if (!sname.empty()) {
            static std::unordered_map<std::string, uint32_t> f526_services;
            uint32_t oid = 0;
            auto sit = f526_services.find(sname);
            if (sit != f526_services.end() && heap_.has_object(sit->second)) {
                oid = sit->second;
            } else {
                oid = heap_.allocate("Landroid/os/Binder;", pc_,
                    call_stack_.empty() ? 0 : call_stack_.top().frame_id);
                heap_.set_object_field(oid, "__service_name__",
                    DalvikValue::make_string(sname, 0));
                f526_services[sname] = oid;
            }
            static thread_local uint64_t f526_n = 0;
            if (f526_n < 8) { ++f526_n;
                std::cerr << "[F526-SM] " << method << "('" << sname
                          << "') -> oid=" << oid << " (never-null law)"
                          << std::endl; }
            result = DalvikValue::make_object(oid, "Landroid/os/Binder;");
        }
        return true;
    }
'''
        c = c.replace(anchor, law + anchor, 1)
        print("2. bridge_to_api ServiceManager law added")
        n += 1
    ENG_C.write_text(c)
    print(f"patched: {n} edits")

if __name__ == "__main__":
    patch()
