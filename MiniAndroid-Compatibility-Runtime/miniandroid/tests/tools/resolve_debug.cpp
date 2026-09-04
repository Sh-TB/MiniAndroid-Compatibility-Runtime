// UNIFIED_007 — debug: resolve specific resource ids in gmdice
#include <cstdio>
#include "../../src/resources/resource_runtime.h"

using namespace miniandroid::resources;

int main(int argc, char** argv) {
    const char* apk = argc > 1 ? argv[1] : "/home/z/my-project/repo/miniandroid/download/corpus/gmdice.apk";
    ResourceRuntime& rt = ResourceRuntime::instance();
    if (!rt.ensure_loaded(apk)) { printf("load failed\n"); return 1; }
    uint32_t ids[] = {0x7f040008, 0x7f04000c, 0x7f080000, 0x7f080001, 0x7f030000, 0x0102000a};
    for (uint32_t id : ids) {
        auto r = rt.arsc().resolve(id);
        if (!r) { printf("id %08x: NOT FOUND\n", id); continue; }
        printf("id %08x: type=%s name=%s configs=%zu", id, r->type_name.c_str(), r->name.c_str(), r->configs.size());
        const ArscEntry* e = r->best();
        if (e) {
            printf(" best_cfg='%s' dtype=%d", e->config_desc.c_str(), (int)e->value.type);
            if (e->value.is_string()) printf(" value='%s'", e->value.string_value.c_str());
        }
        printf("\n");
        // resolve_value (ref hop)
        auto v = rt.arsc().resolve_value(id);
        if (v && v->is_string()) printf("    resolve_value → '%s'\n", v->string_value.c_str());
        // apk path
        auto info = rt.apk().parse(apk);
        auto p = rt.arsc().apk_path_for(id, info.all_entries);
        if (p) printf("    path → %s\n", p->c_str());
    }
    return 0;
}
