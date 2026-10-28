// cont48_f1_probe.cpp — F1 probe: parse telegram's resources.arsc with the
// ENGINE's own ArscParser, then resolve one drawable resid end-to-end.
// Answers: (1) does parse() succeed? (2) resolve(0x7f080016)? (3) its value
// type/string, (4) select_file with the real zip entry list.
#include <cstdio>
#include <fstream>
#include <string>
#include <vector>
#include <zip.h>

#include "resources/arsc_parser.h"

using namespace resources;

int main(int argc, char** argv) {
    const char* apk = argc > 1 ? argv[1]
                               : "/home/z/my-project/upload/telegram_official.apk";
    // read resources.arsc from the zip (system libzip)
    int err = 0;
    zip* z = zip_open(apk, 0, &err);
    if (!z) { printf("ZIP-OPEN-FAIL err=%d\n", err); return 1; }
    zip_file_t* zf = zip_fopen(z, "resources.arsc", 0);
    if (!zf) { printf("NO-ARSC\n"); return 1; }
    std::vector<uint8_t> data;
    uint8_t buf[65536];
    zip_int64_t n;
    while ((n = zip_fread(zf, buf, sizeof buf)) > 0)
        data.insert(data.end(), buf, buf + n);
    zip_fclose(zf);
    printf("ARSC-BYTES=%zu\n", data.size());

    ArscParser arsc;
    bool ok = arsc.parse(data);
    printf("PARSE=%s err=%s\n", ok ? "OK" : "FAIL", arsc.last_error());
    const auto& st = arsc.stats();
    printf("STATS packages=%zu type_chunks=%zu entries=%zu named=%zu\n",
           st.package_count, st.type_count, st.entry_count, st.named_ids);

    uint32_t resid = 0x7f080016;
    auto r = arsc.resolve(resid);
    printf("RESOLVE 0x%08x = %s\n", resid, r ? "HIT" : "NULL");
    if (r) {
        printf("  type=%s name=%s configs=%zu\n", r->type_name.c_str(),
               r->name.c_str(), r->configs.size());
        if (!r->configs.empty()) {
            const auto& e = r->configs.front();
            printf("  value.type=%d str='%.80s'\n", (int)e.value.type,
                   e.value.string_value.c_str());
        }
    }

    // zip entry list
    std::vector<std::string> paths;
    zip_int64_t nc = zip_get_num_entries(z, 0);
    for (zip_int64_t i = 0; i < nc; i++) {
        const char* nm = zip_get_name(z, i, 0);
        if (nm) paths.push_back(nm);
    }
    printf("ZIP-ENTRIES=%zu\n", paths.size());
    auto sel = arsc.select_file(resid, paths, device_config());
    printf("SELECT_FILE = %s\n", sel ? sel->path.c_str() : "NULL");
    zip_close(z);
    return 0;
}
