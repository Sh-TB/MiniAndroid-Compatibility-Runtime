#!/usr/bin/env python3
"""S34 probe 19 (fixed): list identity mapping between write and read.

All return-value logging lives inside try_recursive_invoke (where
return_val exists). The dispatch-chain probe only logs entries.
Bounded; idempotent.
"""
import sys

P = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(P).read()

if '[S34-LISTMAP]' in src:
    print('already present')
    sys.exit(0)

# 1. F/w.b and z1/r.A return logging inside try_recursive_invoke
a2 = """    if (declaring_class == "Lj/b;" && method_name == "b") {"""
assert a2 in src, 'a2 missing'
p2 = """    if ((declaring_class == "LF/w;" && method_name == "b") ||
        (declaring_class == "Lz1/r;" && method_name == "A")) {
        static thread_local uint64_t lm_r = 0;
        ++lm_r;
        if (lm_r <= 24) {
            std::cerr << "[S34-LISTMAP] " << declaring_class << "."
                      << method_name << " #" << lm_r
                      << " caller=" << current_class_ << "." << current_method_;
            if (!args.empty() && args[0].type == DalvikType::OBJECT_REF)
                std::cerr << " recv=o" << args[0].object_id;
            if (return_val.type == DalvikType::OBJECT_REF)
                std::cerr << " ret=o" << return_val.object_id
                          << (return_val.is_null ? "(NULL)" : "");
            std::cerr << std::endl;
        }
    }
    if (declaring_class == "Lj/b;" && method_name == "b") {"""
src = src.replace(a2, p2, 1)
open(P, 'w').write(src)
print('LISTMAP probes applied (fixed)')
