// cont49_f2_probe2.cpp — F2 decode v2: route the windowBackground reference
// through the FRAMEWORK table (the law the live engine is missing).
// Chain: Theme.TMessages.Start (app 0x7f100149) → bag 0x01010054 →
// ref 0x0106000b → framework resolve_full → terminal ARGB.
#include <cstdio>
#include <fstream>
#include <string>
#include <vector>

#include "resources/arsc_parser.h"
#include "resources/res_config.h"

using namespace miniandroid;

int main() {
    std::ifstream f("/home/z/my-project/run/cont48/tg_arsc.bin", std::ios::binary);
    std::vector<uint8_t> data((std::istreambuf_iterator<char>(f)),
                              std::istreambuf_iterator<char>());
    resources::ArscParser app;
    if (!app.parse(data)) { printf("APP-PARSE-FAIL\n"); return 1; }

    std::ifstream ff("/home/z/my-project/miniandroid/framework_res/resources.arsc",
                     std::ios::binary);
    std::vector<uint8_t> fdata((std::istreambuf_iterator<char>(ff)),
                               std::istreambuf_iterator<char>());
    resources::ArscParser fw;
    if (!fw.parse(fdata)) { printf("FW-PARSE-FAIL %s\n", fw.last_error().c_str()); return 1; }
    printf("FW-STATS entries=%zu named=%zu\n", fw.stats().entry_count,
           fw.stats().named_ids);

    auto dev = resources::device_config();
    // 1. confirm the app-side bag hit
    auto wb = app.bag_value(0x7f100149, 0x01010054, dev);
    printf("APP-BAG winbg=%s", wb ? "HIT" : "MISS");
    if (wb)
        printf(" type=%d ref=%d data=0x%08x", (int)(uint8_t)wb->type,
               (int)wb->is_reference(), wb->data);
    printf("\n");
    if (!wb) return 1;

    // 2. framework-route the reference (the missing law)
    uint32_t rid = wb->data;
    auto r = fw.resolve_full(rid, dev);
    printf("FW-DEREF 0x%08x ok=%d name=%s\n", rid, (int)r.ok,
           r.entry_name.c_str());
    if (r.ok && r.value()) {
        const auto& v = *r.value();
        printf("  vtype=%d data=0x%08x str='%s'\n", (int)(uint8_t)v.type, v.data,
               v.string_value.c_str());
        if (v.is_int()) printf("  ARGB=#%08x\n", v.data);
        if (v.is_color()) printf("  COLOR data=0x%08x\n", v.data);
    }
    // 3. for contrast: background_light (0x0106000c)
    auto rl = fw.resolve_full(0x0106000c, dev);
    if (rl.ok && rl.value())
        printf("FW 0x0106000c name=%s vtype=%d data=0x%08x\n",
               rl.entry_name.c_str(), (int)(uint8_t)rl.value()->type,
               rl.value()->data);
    return 0;
}
