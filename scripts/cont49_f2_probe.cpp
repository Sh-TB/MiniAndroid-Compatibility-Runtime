// cont49_f2_probe.cpp — F2 decode: theme → windowBackground → VALUE-TYPE chain
// on the telegram ARSC using the ENGINE's own ArscParser (androguard 3.3.5
// crashes on this table). Question: does the launch theme's 0x01010054
// (android:windowBackground) resolve to a COLOR (painted) or a res/ FILE
// reference (the un-bridged case — resolve_window_background_argb only
// answers colors, a file value nullopts to the white fallback)?
#include <cstdio>
#include <fstream>
#include <string>
#include <vector>

#include "apk/manifest_reader.h"
#include "resources/arsc_parser.h"
#include "resources/res_config.h"

using namespace miniandroid;

int main() {
    // 1. manifest → launch theme resid
    std::ifstream mf("/home/z/my-project/run/cont49/tg_manifest.bin", std::ios::binary);
    std::vector<uint8_t> mdata((std::istreambuf_iterator<char>(mf)),
                               std::istreambuf_iterator<char>());
    apk::ManifestReader mr;
    apk::ManifestInfo mi = mr.parse(mdata);
    printf("MANIFEST activity_theme=0x%08x application_theme=0x%08x\n",
           mi.activity_theme_resid, mi.application_theme_resid);

    // 2. ARSC parse (engine parser)
    std::ifstream f("/home/z/my-project/run/cont48/tg_arsc.bin", std::ios::binary);
    std::vector<uint8_t> data((std::istreambuf_iterator<char>(f)),
                              std::istreambuf_iterator<char>());
    resources::ArscParser arsc;
    bool ok = arsc.parse(data);
    printf("PARSE=%s err=%s\n", ok ? "OK" : "FAIL", arsc.last_error().c_str());
    if (!ok) return 1;

    uint32_t theme = mi.activity_theme_resid != 0 ? mi.activity_theme_resid
                                                  : mi.application_theme_resid;
    // manifest captures the LAST activity theme (S68 W2); also probe the
    // Theme.TMessages.Start candidates seen in prior decodes.
    const uint32_t themes[] = {theme, 0x7f0d0000, 0x7f0d0001, 0x7f0d0002,
                               0x7f0d0003, 0x7f0d0004, 0x7f0d0005};
    // zip res/ entry list for select_file
    std::vector<std::string> paths;
    {
        std::ifstream lf("/home/z/my-project/run/cont48/tg_res_list.txt");
        std::string ln;
        while (std::getline(lf, ln))
            if (!ln.empty()) paths.push_back(ln);
    }
    for (uint32_t th : themes) {
        if (th == 0) continue;
        auto r = arsc.resolve(th);
        printf("THEME 0x%08x name=%s\n", th,
               r ? (r->type_name + "/" + r->name).c_str() : "UNRESOLVED");
        auto wb = arsc.bag_value(th, 0x01010054, miniandroid::resources::device_config());
        if (!wb) {
            printf("  winbg=MISS\n");
            continue;
        }
        printf("  winbg type=%d ref=%d data=0x%08x str='%.80s'\n", (int)(uint8_t)wb->type,
               (int)wb->is_reference(), wb->data, wb->string_value.c_str());
        if (wb->is_reference()) {
            uint32_t rid = wb->data;
            auto rr = arsc.resolve_full(rid, miniandroid::resources::device_config());
            if (rr.ok && rr.value()) {
                const auto& v = *rr.value();
                printf("  deref 0x%08x name=%s vtype=%d str='%.80s'\n", rid,
                       rr.entry_name.c_str(), (int)(uint8_t)v.type,
                       v.string_value.c_str());
                auto sel = arsc.select_file(rid, paths, miniandroid::resources::device_config());
                printf("  SELECT_FILE=%s\n", sel ? sel->path.c_str() : "NULL");
            } else {
                printf("  deref 0x%08x FAIL ok=%d\n", rid, (int)rr.ok);
            }
        }
    }
    return 0;
}
