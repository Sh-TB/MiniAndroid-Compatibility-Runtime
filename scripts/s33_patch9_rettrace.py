#!/usr/bin/env python3
"""S33 probe 9: generic return-value trace (MINIANDROID_RET_TRACE=substr).
Prints [RET-TRACE] class.method -> return value (obj id/class or NULL) for
every resolved invocation whose DECLARING class contains the substring.
Bounded 200. Idempotent.
"""
import sys

C = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(C).read()

if '[RET-TRACE]' in src:
    print('already present')
    sys.exit(0)

anchor = """        if (lifecycle_window_active_) {"""
assert anchor in src

probe = """        // S33 (R-NEW-332): generic return-value trace — env-gated by
        // MINIANDROID_RET_TRACE=<class-substring>; prints the resolved
        // return value (object id/class or NULL) for every invocation
        // whose DECLARING class contains the substring.
        {
            static thread_local const char* ret_trace_env =
                std::getenv("MINIANDROID_RET_TRACE");
            if (ret_trace_env && ret_trace_env[0] &&
                cls_ref.name.find(ret_trace_env) != std::string::npos) {
                static thread_local uint64_t ret_count = 0;
                if (ret_count < 200) {
                    ++ret_count;
                    std::cerr << "[RET-TRACE] " << cls_ref.name << "."
                              << method.name << " -> "
                              << (return_val.is_null
                                      ? "NULL"
                                      : (return_val.type == DalvikType::OBJECT_REF
                                             ? ("obj#" + std::to_string(return_val.object_id) +
                                                " " + return_val.class_desc)
                                             : ("prim:" + std::to_string(return_val.int_val))))
                              << std::endl;
                }
            }
        }
        if (lifecycle_window_active_) {"""
src = src.replace(anchor, probe, 1)
open(C, 'w').write(src)
print('ret-trace probe applied')
