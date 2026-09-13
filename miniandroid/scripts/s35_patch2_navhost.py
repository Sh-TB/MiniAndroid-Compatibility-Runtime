#!/usr/bin/env python3
"""S35 patch 2 (R-NEW-334): NavHost identity probe.

Env-gated (MINIANDROID_S35_TRACE=1), bounded. At METHOD ENTRY of:
  - Landroidx/navigation/compose/p;.a   -> args[0] navController id + its .j
      tracker id (heap read) + 3 caller frames
  - LW1/G;.s                            -> rememberNavController entry/exit
  - Landroidx/navigation/c;.<init>      -> 3 caller frames (which path builds
      each NavController instance)
"""
P = "src/dex/dalvik_engine.cpp"
src = open(P).read()

ANCHOR = """        // S35 (R-NEW-334): stale-read evidence probe — env-gated"""
assert ANCHOR in src, "S35 anchor missing"

PROBE = '''        // S35 patch 2: NavHost identity — who runs p.a, with which
        // navController/tracker, and which path builds each controller.
        {
            static thread_local const bool s35b_on =
                std::getenv("MINIANDROID_S35_TRACE") != nullptr;
            if (s35b_on) {
                static thread_local uint64_t s35b_n = 0;
                if (s35b_n < 48) {
                    bool hit = false;
                    std::string line;
                    if (class_name == "Landroidx/navigation/compose/p;" &&
                        method_name == "a") {
                        hit = true;
                        line = " [S35b] p.a nav=o";
                        line += std::to_string(
                            (!args.empty() &&
                             args[0].type == DalvikType::OBJECT_REF)
                                ? args[0].object_id : 0);
                        if (!args.empty() &&
                            args[0].type == DalvikType::OBJECT_REF) {
                            auto trk = heap_.get_object_field(args[0].object_id,
                                                              "j");
                            line += " trk=";
                            line += (trk.has_value() &&
                                     trk->type == DalvikType::OBJECT_REF)
                                        ? ("o" + std::to_string(trk->object_id))
                                        : std::string("?");
                        }
                    } else if (class_name == "LW1/G;" && method_name == "s") {
                        hit = true;
                        line = " [S35b] W1/G.s (rememberNavController) entry";
                    } else if (class_name == "Landroidx/navigation/c;" &&
                               method_name == "<init>") {
                        hit = true;
                        line = " [S35b] c.<init>";
                    }
                    if (hit) {
                        auto frames = call_stack_.snapshot_top_first();
                        for (size_t fi = 0; fi < frames.size() && fi < 3; ++fi)
                            line += " <" + frames[fi].first + "." +
                                    frames[fi].second + ">";
                        ++s35b_n;
                        std::cerr << line << std::endl;
                    }
                }
            }
        }
'''

src = src.replace(ANCHOR, PROBE + ANCHOR, 1)
open(P, "w").write(src)
print("patched (s35 patch 2)")
