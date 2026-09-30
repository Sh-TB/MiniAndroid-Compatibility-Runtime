#include "resources/arsc_parser.h"
#include <cstdio>
#include <vector>
#include <cstdint>
using namespace miniandroid::resources;
int main(){
    FILE* f=fopen("framework_res/resources.arsc","rb"); if(!f){printf("open fail\n");return 1;}
    std::vector<uint8_t> d; int c; while((c=fgetc(f))!=EOF) d.push_back((uint8_t)c); fclose(f);
    ArscParser p; if (!p.parse(d)) { printf("parse fail\n"); return 1; }
    ResTableConfig cfg;
    auto bag = p.bag_value(0x01030237u, 0x01010054u, cfg);
    if (bag) printf("wb item(type): type=%d data=0x%08x\n", (int)bag->type, bag->data);
    for (uint32_t id : {0x01080098u, 0x01080099u, 0x0106000eu, 0x0106000fu}) {
        auto r = p.resolve_full(id, cfg);
        printf("0x%08x ok=%d type=%s entry='%s'\n", id, r.ok?1:0, r.ok?r.type_name.c_str():"-", r.ok?r.entry_name.c_str():"-");
        if (r.ok) { auto v = p.resolve_value(id);
            if (v) printf("   value type=%d data=0x%08x\n", (int)v->type, v->data); }
    }
    return 0;
}
