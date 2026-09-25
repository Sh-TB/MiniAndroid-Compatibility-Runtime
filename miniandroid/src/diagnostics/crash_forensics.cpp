// S100 §3/§7 — crash forensics implementation (see crash_forensics.h).
#include "crash_forensics.h"

#include <atomic>
#include <cstdarg>
#include <cstdio>
#include <cstring>
#include <execinfo.h>
#include <signal.h>
#include <unistd.h>

namespace {

constexpr int kRingSlots = 64;
constexpr int kSlotBytes = 160;

struct Ring {
    std::atomic<uint64_t> seq{0};
    char slots[kRingSlots][kSlotBytes];
};
Ring g_ring;

// Installed flag (handler must not re-enter install).
std::atomic<bool> g_installed{false};

// PIE load base captured at install() (main executable's first mapping).
// Frame offsets = runtime_addr - load_base are stable for addr2line.
uintptr_t g_load_base = 0;

void capture_load_base() {
    FILE* f = fopen("/proc/self/maps", "r");
    if (!f) return;
    char exe[1024];
    ssize_t rl = readlink("/proc/self/exe", exe, sizeof(exe) - 1);
    if (rl <= 0) { fclose(f); return; }
    exe[rl] = '\0';
    char line[2048];
    while (fgets(line, sizeof(line), f)) {
        if (strstr(line, exe)) {
            uintptr_t lo = 0;
            size_t i = 0;
            for (; line[i] && line[i] != '-'; ++i) {
                char c = line[i];
                int v = (c >= '0' && c <= '9') ? c - '0'
                      : (c >= 'a' && c <= 'f') ? c - 'a' + 10
                      : (c >= 'A' && c <= 'F') ? c - 'A' + 10 : -1;
                if (v < 0) { lo = 0; break; }
                lo = lo * 16 + (uintptr_t)v;
            }
            if (lo) g_load_base = lo;
            break;
        }
    }
    fclose(f);
}

// Async-signal-safe: minimal unsigned-to-hex/dec into a raw buffer.
size_t fmt_u(char* out, size_t cap, uint64_t v, int base) {
    char tmp[24];
    size_t n = 0;
    if (v == 0) tmp[n++] = '0';
    while (v && n < sizeof(tmp)) {
        int d = (int)(v % (uint64_t)base);
        tmp[n++] = (char)(d < 10 ? '0' + d : 'a' + d - 10);
        v /= (uint64_t)base;
    }
    size_t w = 0;
    while (n && w + 1 < cap) out[w++] = tmp[--n];
    if (w < cap) out[w] = '\0';
    return w;
}

size_t append_str(char* out, size_t cap, size_t pos, const char* s) {
    while (*s && pos + 1 < cap) out[pos++] = *s++;
    if (pos < cap) out[pos] = '\0';
    return pos;
}

size_t append_u(char* out, size_t cap, size_t pos, uint64_t v, int base = 10) {
    char tmp[24];
    size_t n = 0;
    if (v == 0) tmp[n++] = '0';
    while (v && n < sizeof(tmp)) {
        int d = (int)(v % (uint64_t)base);
        tmp[n++] = (char)(d < 10 ? '0' + d : 'a' + d - 10);
        v /= (uint64_t)base;
    }
    while (n && pos + 1 < cap) out[pos++] = tmp[--n];
    if (pos < cap) out[pos] = '\0';
    return pos;
}

void handler(int sig, siginfo_t* info, void*) {
    char buf[4096];
    size_t pos = 0;
    pos = append_str(buf, sizeof(buf), pos,
                     "\n[S100-CRASH-FORENSICS] signal=");
    pos = append_u(buf, sizeof(buf), pos, (uint64_t)sig);
    if (info) {
        pos = append_str(buf, sizeof(buf), pos, " si_code=");
        pos = append_u(buf, sizeof(buf), pos, (uint64_t)info->si_code);
        pos = append_str(buf, sizeof(buf), pos, " fault_addr=0x");
        pos = append_u(buf, sizeof(buf), pos,
                       (uint64_t)(uintptr_t)info->si_addr, 16);
    }
    pos = append_str(buf, sizeof(buf), pos, " pid=");
    pos = append_u(buf, sizeof(buf), pos, (uint64_t)getpid());
    pos = append_str(buf, sizeof(buf), pos, " load_base=0x");
    pos = append_u(buf, sizeof(buf), pos, (uint64_t)g_load_base, 16);
    pos = append_str(buf, sizeof(buf), pos, "\n");

    // Last semantic operations (newest last).
    uint64_t s = g_ring.seq.load(std::memory_order_relaxed);
    uint64_t count = s < (uint64_t)kRingSlots ? s : (uint64_t)kRingSlots;
    pos = append_str(buf, sizeof(buf), pos, "[S100-LAST-OPS] count=");
    pos = append_u(buf, sizeof(buf), pos, count);
    pos = append_str(buf, sizeof(buf), pos, "\n");
    uint64_t start = s >= (uint64_t)kRingSlots ? s - (uint64_t)kRingSlots : 0;
    for (uint64_t i = start; i < s; ++i) {
        size_t slot = (size_t)(i % (uint64_t)kRingSlots);
        // Slot is published by index.store after memcpy; a torn read is
        // acceptable diagnostics — prefix guard keeps the block parseable.
        if (g_ring.slots[slot][0] == '\0') continue;
        pos = append_str(buf, sizeof(buf), pos, "  op[");
        pos = append_u(buf, sizeof(buf), pos, i);
        pos = append_str(buf, sizeof(buf), pos, "] ");
        pos = append_str(buf, sizeof(buf), pos, g_ring.slots[slot]);
        pos = append_str(buf, sizeof(buf), pos, "\n");
        if (pos > sizeof(buf) - 512) break;
    }

    // Native frames (addresses only; resolved offline via addr2line).
    void* frames[64];
    int nf = backtrace(frames, 64);
    pos = append_str(buf, sizeof(buf), pos, "[S100-NATIVE-FRAMES] count=");
    pos = append_u(buf, sizeof(buf), pos, (uint64_t)(nf > 0 ? nf : 0));
    pos = append_str(buf, sizeof(buf), pos, "\n");
    for (int i = 0; i < nf; ++i) {
        pos = append_str(buf, sizeof(buf), pos, "  #");
        pos = append_u(buf, sizeof(buf), pos, (uint64_t)i);
        pos = append_str(buf, sizeof(buf), pos, " 0x");
        pos = append_u(buf, sizeof(buf), pos, (uint64_t)(uintptr_t)frames[i], 16);
        pos = append_str(buf, sizeof(buf), pos, " off=0x");
        pos = append_u(buf, sizeof(buf), pos,
                       (uint64_t)((uintptr_t)frames[i] - g_load_base), 16);
        pos = append_str(buf, sizeof(buf), pos, "\n");
        if (pos > sizeof(buf) - 128) break;
    }
    pos = append_str(buf, sizeof(buf), pos, "[S100-CRASH-FORENSICS-END]\n");

    ssize_t rc = write(2, buf, pos);
    (void)rc;

    // Restore default disposition and re-raise: honest signal death (rc stays
    // signal-class) with the evidence block already on stderr.
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = SIG_DFL;
    sigemptyset(&sa.sa_mask);
    sigaction(sig, &sa, nullptr);
    raise(sig);
    _exit(128 + sig);  // unreachable in practice
}

}  // namespace

namespace CrashForensics {

void install() {
    bool expect = false;
    if (!g_installed.compare_exchange_strong(expect, true)) return;
    capture_load_base();
    // Warm backtrace()'s lazy initialization outside any handler.
    void* warm[8];
    backtrace(warm, 8);

    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_sigaction = handler;
    sa.sa_flags = SA_SIGINFO | SA_RESETHAND;
    sigemptyset(&sa.sa_mask);
    sigaction(SIGSEGV, &sa, nullptr);
    sigaction(SIGBUS, &sa, nullptr);
    sigaction(SIGFPE, &sa, nullptr);
    sigaction(SIGILL, &sa, nullptr);
    sigaction(SIGABRT, &sa, nullptr);
}

void note(const char* tag, const char* fmt, ...) {
    uint64_t idx = g_ring.seq.fetch_add(1, std::memory_order_relaxed);
    size_t slot = (size_t)(idx % (uint64_t)kRingSlots);
    char* dst = g_ring.slots[slot];
    size_t pos = 0;
    pos = append_str(dst, kSlotBytes, pos, tag);
    pos = append_str(dst, kSlotBytes, pos, " ");
    va_list ap;
    va_start(ap, fmt);
    // vsnprintf always NUL-terminates within the (dst+pos, kSlotBytes-pos)
    // window — do NOT write another NUL at the old pos (that would clip the
    // payload to the tag, the S100-repro-1 bug).
    vsnprintf(dst + pos, kSlotBytes - pos, fmt, ap);
    va_end(ap);
}

}  // namespace CrashForensics
