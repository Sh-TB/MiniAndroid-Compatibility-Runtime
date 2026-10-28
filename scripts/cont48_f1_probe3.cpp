// cont48_f1_probe3.cpp — F1 probe v3: mirror the RUNTIME path exactly —
// ResourceRuntime::instance().ensure_loaded(apk) then rt.arsc() resolve +
// select_file. Names the layer that differs from the fresh-parser probe
// (fresh parser: resolve HIT, select_file HIT for 0x7f080016).
#include <cstdio>
#include <fstream>
#include <string>
#include <vector>

#include "resources/resource_runtime.h"

using namespace miniandroid::resources;

int main() {
    const std::string apk = "/home/z/my-project/upload/telegram_official.apk";
    auto& rt = ResourceRuntime::instance();
    bool loaded = rt.ensure_loaded(apk);
    printf("ENSURE_LOADED=%s\n", loaded ? "true" : "false");
    if (!loaded) return 1;

    std::vector<std::string> paths;
    {
        std::ifstream lf("/home/z/my-project/run/cont48/tg_res_list.txt");
        std::string ln;
        while (std::getline(lf, ln))
            if (!ln.empty()) paths.push_back(ln);
    }
    printf("ZIP-RES-ENTRIES=%zu\n", paths.size());

    const uint32_t resids[] = {0x7f080016, 0x7f080017, 0x7f080801, 0x7f0d0000,
                               0x7f0f0000};
    for (uint32_t resid : resids) {
        auto r = rt.arsc().resolve(resid);
        if (!r) { printf("0x%08x RESOLVE=NULL\n", resid); continue; }
        const auto& e = r->configs.front();
        printf("0x%08x type=%s name=%s cfgs=%zu vtype=%d str='%.50s'\n",
               resid, r->type_name.c_str(), r->name.c_str(), r->configs.size(),
               (int)e.value.type, e.value.string_value.c_str());
        auto sel = rt.arsc().select_file(resid, paths, device_config());
        printf("        SELECT_FILE=%s\n", sel ? sel->path.c_str() : "NULL");
    }
    return 0;
}
