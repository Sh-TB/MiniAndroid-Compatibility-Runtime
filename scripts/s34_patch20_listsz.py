#!/usr/bin/env python3
"""S34 probe 20: list content size at the lastOrNull sites + heap dump of
the key lists (o3013 read vs o2901 written).

Logs (bounded): z1/r.A entries with the recv list's size read from the heap
(fields tried: size / __array_length__). Also dumps the Z1/L getValue
returns for the trackers (Z1/z.getValue) with list sizes.
Idempotent.
"""
import sys

P = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(P).read()

if '[S34-LISTSZ]' in src:
    print('already present')
    sys.exit(0)

# hook: inside try_recursive_invoke entry probes region (before M3 strict-mode block)
a1 = """    if ((declaring_class == "LF/w;" && method_name == "b") ||"""
assert a1 in src, 'anchor missing (a1)'

p1 = """    if (declaring_class == "Lz1/r;" && method_name == "A") {
        static thread_local uint64_t lsz_n = 0;
        ++lsz_n;
        if (lsz_n <= 20 && !args.empty() &&
            args[0].type == DalvikType::OBJECT_REF) {
            uint32_t lid = args[0].object_id;
            long sz = -1;
            for (const char* fn : {"size", "__array_length__", "count"}) {
                auto mv = heap_.get_object_field(lid, fn);
                if (mv.has_value() && (mv->type == DalvikType::INT32 ||
                                       mv->type == DalvikType::INT64)) {
                    sz = (mv->type == DalvikType::INT32) ? mv->int_val
                                                         : mv->long_val;
                    break;
                }
            }
            std::cerr << "[S34-LISTSZ] z1/r.A #" << lsz_n
                      << " list=o" << lid << " size=" << sz
                      << " caller=" << current_class_ << "."
                      << current_method_ << std::endl;
        }
    }
    if (declaring_class == "LF/w;" && method_name == "b") {"""
src = src.replace(a1, p1, 1)

# hook: Z1/z.getValue entries with the inner list size
a2 = """            } else if ((class_name == "LF/w;" && method_name == "b") ||"""
assert a2 in src, 'anchor2 missing'
p2 = """            } else if (class_name == "LZ1/z;" && method_name == "getValue") {
                // [S34-LISTSZ] tracker reads with inner list size
                static thread_local uint64_t tz_n = 0;
                ++tz_n;
                if (tz_n <= 24) {
                    std::cerr << "[S34-LISTSZ] Z1/z.getValue #" << tz_n
                              << " d=" << recursion_depth_;
                    if (!args.empty() && args[0].type == DalvikType::OBJECT_REF)
                        std::cerr << " tracker=o" << args[0].object_id;
                    auto frames = call_stack_.snapshot_top_first();
                    if (!frames.empty())
                        std::cerr << " <" << frames[0].first << "."
                                  << frames[0].second << ">";
                    std::cerr << std::endl;
                }
            } else if ((class_name == "LF/w;" && method_name == "b") ||"""
src = src.replace(a2, p2, 1)
open(P, 'w').write(src)
print('LISTSZ probes applied')
