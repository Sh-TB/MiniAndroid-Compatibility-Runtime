// Inline memory probe — read /proc/self/status VmRSS.
// EXP-042 Phase 1: Lightweight RSS sampler for diagnosing memory growth.
// All functions are static inline so they can be #included multiple times.
#pragma once
#include <cstdint>
#include <fstream>
#include <sstream>
#include <string>
#include <iostream>

namespace miniandroid { namespace probe {
static inline uint64_t rss_kb() {
    std::ifstream f("/proc/self/status");
    std::string line;
    while (std::getline(f, line)) {
        if (line.rfind("VmRSS:", 0) == 0) {
            std::istringstream iss(line.substr(6));
            uint64_t v; iss >> v;
            return v;
        }
    }
    return 0;
}
static inline void mark(const char* phase) {
    std::cerr << "[MEM] " << phase << " RSS=" << (rss_kb()/1024.0) << " MB" << std::endl;
}
}}
