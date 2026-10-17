#include <cstdio>
#include <cstring>
#include <fstream>
#include <vector>
#include <cstdint>
#pragma pack(push,1)
struct Ehdr { uint8_t id[16]; uint16_t type, mach; uint32_t ver; uint64_t entry, phoff, shoff; uint32_t flags; uint16_t ehsize, phentsize, phnum, shentsize, shnum, shstrndx; };
struct Phdr { uint32_t type, flags; uint64_t off, vaddr, paddr, filesz, memsz, align; };
struct Dyn { int64_t tag; uint64_t val; };
#pragma pack(pop)
int main(int argc, char** argv) {
    std::ifstream f(argv[1], std::ios::binary);
    std::vector<uint8_t> buf((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
    Ehdr e; memcpy(&e, buf.data(), sizeof e);
    printf("phnum=%u phentsize=%u\n", e.phnum, e.phentsize);
    for (uint32_t i = 0; i < e.phnum; i++) {
        Phdr p; memcpy(&p, buf.data() + e.phoff + (size_t)i*e.phentsize, sizeof p);
        if (p.type == 2) {
            printf("PT_DYNAMIC off=%llu filesz=%llu\n", (unsigned long long)p.off, (unsigned long long)p.filesz);
            Dyn* d = (Dyn*)(buf.data() + p.off);
            size_t n = p.filesz / sizeof(Dyn);
            for (size_t k = 0; k < n && d[k].tag != 0; k++) {
                if (d[k].tag == 1 || d[k].tag == 5 || d[k].tag == 10)
                    printf("  tag=%lld val=%llu (0x%llx)\n", (long long)d[k].tag,
                           (unsigned long long)d[k].val, (unsigned long long)d[k].val);
            }
        }
    }
    return 0;
}
