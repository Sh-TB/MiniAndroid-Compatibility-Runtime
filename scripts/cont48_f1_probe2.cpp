// cont48_f1_probe2.cpp — F1 probe v2 (no libzip): parse the extracted ARSC,
// resolve the first few R$drawable resids, print value type+string, then
// select_file against the REAL zip res/ entry list (tg_res_list.txt).
#include <cstdio>
#include <fstream>
#include <string>
#include <vector>

#include "resources/arsc_parser.h"

using namespace miniandroid::resources;

int main() {
    std::ifstream f("/home/z/my-project/run/cont48/tg_arsc.bin", std::ios::binary);
    std::vector<uint8_t> data((std::istreambuf_iterator<char>(f)),
                              std::istreambuf_iterator<char>());
    printf("ARSC-BYTES=%zu\n", data.size());

    ArscParser arsc;
    bool ok = arsc.parse(data);
    printf("PARSE=%s err=%s\n", ok ? "OK" : "FAIL", arsc.last_error().c_str());
    if (!ok) return 1;
    const auto& st = arsc.stats();
    printf("STATS packages=%zu type_chunks=%zu entries=%zu named=%zu\n",
           st.package_count, st.type_count, st.entry_count, st.named_ids);

    std::vector<std::string> paths;
    {
        std::ifstream lf("/home/z/my-project/run/cont48/tg_res_list.txt");
        std::string ln;
        while (std::getline(lf, ln))
            if (!ln.empty()) paths.push_back(ln);
    }
    printf("ZIP-RES-ENTRIES=%zu\n", paths.size());

    // R$drawable first fields from the DEX census: 0x7f080016 .. (probe 5)
    const uint32_t resids[] = {0x7f080016, 0x7f080017, 0x7f080801, 0x7f080020,
                               0x7f0d0000};
    for (uint32_t resid : resids) {
        auto r = arsc.resolve(resid);
        if (!r) { printf("0x%08x RESOLVE=NULL\n", resid); continue; }
        const auto& e = r->configs.front();
        printf("0x%08x type=%s name=%s cfgs=%zu vtype=%d str='%.60s'\n",
               resid, r->type_name.c_str(), r->name.c_str(), r->configs.size(),
               (int)e.value.type, e.value.string_value.c_str());
        auto sel = arsc.select_file(resid, paths, device_config());
        printf("        SELECT_FILE=%s\n", sel ? sel->path.c_str() : "NULL");
    }
    return 0;
}
