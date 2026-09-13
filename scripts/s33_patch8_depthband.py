#!/usr/bin/env python3
"""S33 probe 8: depth-window trace for the app-lambda composition phase.
Logs all method entries in the recursion-depth band [MIN,MAX] (env-gated
MINIANDROID_DEPTHBAND=min:max, bounded 500) to expose where the app
composable stops composing.
"""
import sys

C = '/tmp/my-project/miniandroid/src/dex/dalvik_engine.cpp'
src = open(C).read()

if '[DEPTHBAND' in src:
    print('already present')
    sys.exit(0)

anchor = """    // S33 (R-NEW-332): composition-window trace"""
assert anchor in src

probe = """    // S33 (R-NEW-332): depth-band trace — log method entries whose
    // recursion depth falls in the configured band (env-gated
    // MINIANDROID_DEPTHBAND=min:max, bounded 500). Exposes the app
    // composable's execution until its terminal point.
    {
        static thread_local const char* band_env =
            std::getenv("MINIANDROID_DEPTHBAND");
        if (band_env) {
            static thread_local int band_min = -1;
            static thread_local int band_max = -1;
            if (band_min < 0) {
                int mn = 0, mx = 0;
                if (sscanf(band_env, "%d:%d", &mn, &mx) == 2) {
                    band_min = mn;
                    band_max = mx;
                }
            }
            if (band_min >= 0 && recursion_depth_ >= band_min &&
                recursion_depth_ <= band_max) {
                static thread_local uint64_t band_logged = 0;
                if (band_logged < 500) {
                    ++band_logged;
                    std::cerr << "[DEPTHBAND d=" << recursion_depth_ << "] "
                              << class_name << "." << method_name << " "
                              << descriptor << std::endl;
                }
            }
        }
    }
    // S33 (R-NEW-332): composition-window trace"""
src = src.replace(anchor, probe, 1)
open(C, 'w').write(src)
print('depthband probe applied')
