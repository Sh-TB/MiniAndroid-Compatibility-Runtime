#include <cstdio>
#include <cstring>
#include <fstream>
#include <vector>
#include <cstdint>
#pragma pack(push, 1)
struct Elf64Ehdr {
    uint8_t  e_ident[16];
    uint16_t e_type, e_machine;
    uint32_t e_version;
    uint64_t e_entry, e_phoff, e_shoff;
    uint32_t e_flags, e_ehsize, e_phentsize, e_phnum;
    uint32_t e_shentsize, e_shnum, e_shstrndx;
};
struct Elf64Phdr {
    uint32_t p_type, p_flags;
    uint64_t p_offset, p_vaddr, p_paddr, p_filesz, p_memsz, p_align;
};
#pragma pack(pop)
int main(int argc, char** argv) {
    std::ifstream f(argv[1], std::ios::binary);
    std::vector<uint8_t> buf((std::istreambuf_iterator<char>(f)), std::istreambuf_iterator<char>());
    Elf64Ehdr e; memcpy(&e, buf.data(), sizeof e);
    printf("size=%zu phoff=%llu phnum=%u phentsize=%u sizeofPhdr=%zu\n",
           buf.size(), (unsigned long long)e.e_phoff, e.e_phnum, e.e_phentsize, sizeof(Elf64Phdr));
    return 0;
}
