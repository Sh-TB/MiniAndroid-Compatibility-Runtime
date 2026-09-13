#!/usr/bin/env python3
"""S35 patch 1 (R-NEW-334): stale-read evidence probe.

Adds an env-gated (MINIANDROID_S35_TRACE=1) bounded probe after method
dispatch that, for four anchor sites, prints receiver/value object ids AND
ArrayList sizes read from the engine heap (read-only, same law as the S34
probes):

  1. LF/w.b entry        -> tracker id + tracker.j state id
  2. LF/V0.getValue ret  -> state obj read + returned list size
  3. LF/F.getValue ret   -> derived state read + returned list size
  4. LF/F.m ret          -> derived dependency-compare result (int)
Answers WHERE the visible-entries list loses its entry between
navigation write and NavHost read.
"""
import re

P = "src/dex/dalvik_engine.cpp"
src = open(P).read()

ANCHOR = """        // S33 (R-NEW-332): generic return-value trace — env-gated by
        // MINIANDROID_RET_TRACE=<class-substring>; prints the resolved
        // return value (object id/class or NULL) for every invocation
        // whose DECLARING class contains the substring."""
assert ANCHOR in src, "anchor missing"

PROBE = '''        // S35 (R-NEW-334): stale-read evidence probe — env-gated
        // MINIANDROID_S35_TRACE=1, bounded 64 lines. Prints receiver/value
        // object ids and ArrayList sizes for the visible-entries chain:
        // LF/w.b entry (tracker), LF/V0.getValue ret (remembered state),
        // LF/F.getValue ret (derived state), LF/F.m ret (dep compare).
        {
            static thread_local const bool s35_on =
                std::getenv("MINIANDROID_S35_TRACE") != nullptr;
            if (s35_on) {
                static thread_local uint64_t s35_n = 0;
                if (s35_n < 64) {
                    bool s35_hit = false;
                    std::string s35_line;
                    if (cls_ref.name == "LF/w;" && method.name == "b" &&
                        !args.empty() && args[0].type == DalvikType::OBJECT_REF) {
                        s35_hit = true;
                        auto jst = heap_.get_object_field(args[0].object_id,
                                                          "LZ1/z;.j");
                        s35_line = " [S35] LF/w.b tracker=o" +
                                   std::to_string(args[0].object_id) + " j=" +
                                   (jst.has_value() && jst->type == DalvikType::OBJECT_REF
                                        ? ("o" + std::to_string(jst->object_id))
                                        : std::string("?"));
                    } else if (method.name == "getValue" &&
                               (cls_ref.name == "LF/V0;" ||
                                cls_ref.name == "LF/F;") &&
                               !args.empty() &&
                               args[0].type == DalvikType::OBJECT_REF &&
                               return_val.type == DalvikType::OBJECT_REF) {
                        s35_hit = true;
                        auto sz = heap_.get_object_field(
                            return_val.object_id, "__array_length__");
                        s35_line = " [S35] " + cls_ref.name + ".getValue recv=o" +
                                   std::to_string(args[0].object_id) + " -> o" +
                                   std::to_string(return_val.object_id) + " sz=" +
                                   (sz.has_value() ? std::to_string(sz->int_val)
                                                   : std::string("n/a"));
                    } else if (cls_ref.name == "LF/F;" && method.name == "m" &&
                               return_val.type == DalvikType::INT32) {
                        s35_hit = true;
                        s35_line = " [S35] LF/F.m (derived dep compare) -> " +
                                   std::to_string(return_val.int_val);
                    }
                    if (s35_hit) {
                        ++s35_n;
                        std::cerr << s35_line << std::endl;
                    }
                }
            }
        }
'''

src = src.replace(ANCHOR, PROBE + ANCHOR, 1)
open(P, "w").write(src)
print("patched", P, "- anchor occurrences:", src.count("S35 (R-NEW-334)"))
