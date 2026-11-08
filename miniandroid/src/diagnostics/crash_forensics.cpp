// S100 §3/§7 — crash forensics implementation (see crash_forensics.h).
// W15 (S188): FAULTING-IP LAW — the handler's backtrace() starts in the
// handler itself and cannot cross the signal frame (live evidence: the
// W14 p9 forensics block showed only [handler, libc] frames — count=2 —
// while the faulting constructor context stayed invisible). The exact
// faulting instruction pointer lives in the ucontext the kernel hands the
// SA_SIGINFO handler; it is now captured, printed, and attributed
// (module + module offset via dladdr, /proc/self/maps fallback). Pure
// diagnostics — no behavior change.
#ifndef _GNU_SOURCE
#define _GNU_SOURCE 1
#endif
#include "crash_forensics.h"

#include <atomic>
#include <cstdarg>
#include <cstdio>
#include <cstring>
#include <execinfo.h>
#include <dlfcn.h>
#include <signal.h>
#include <unistd.h>
#include <ucontext.h>

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

// W15: faulting-IP capture from the ucontext (arch-conditional), with
// dladdr attribution and a /proc/self/maps fallback. The maps fallback
// mirrors the W10-FAULT guard precedent (fopen/fgets in-handler accepted
// for diagnostics in this codebase).
uintptr_t faulting_ip(const void* uctx_v) {
    const ucontext_t* uc = static_cast<const ucontext_t*>(uctx_v);
    if (!uc) return 0;
#if defined(__x86_64__)
    return (uintptr_t)uc->uc_mcontext.gregs[REG_RIP];
#elif defined(__aarch64__)
    return (uintptr_t)uc->uc_mcontext.pc;
#else
    return 0;
#endif
}

void handler(int sig, siginfo_t* info, void* uctx_v) {
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

    // W15: the exact faulting instruction pointer + module attribution.
    {
        uintptr_t ip = faulting_ip(uctx_v);
        pos = append_str(buf, sizeof(buf), pos, "[S100-FAULT-IP] ip=0x");
        pos = append_u(buf, sizeof(buf), pos, (uint64_t)ip, 16);
        bool attributed = false;
        Dl_info di;
        if (ip && dladdr((const void*)ip, &di) && di.dli_fname) {
            const char* bn = strrchr(di.dli_fname, '/');
            bn = bn ? bn + 1 : di.dli_fname;
            pos = append_str(buf, sizeof(buf), pos, " mod=");
            pos = append_str(buf, sizeof(buf), pos, bn);
            if (di.dli_fbase) {
                pos = append_str(buf, sizeof(buf), pos, " modoff=0x");
                pos = append_u(buf, sizeof(buf), pos,
                               (uint64_t)(ip - (uintptr_t)di.dli_fbase), 16);
            }
            if (di.dli_sname) {
                pos = append_str(buf, sizeof(buf), pos, " sym=");
                pos = append_str(buf, sizeof(buf), pos, di.dli_sname);
                if (di.dli_saddr) {
                    pos = append_str(buf, sizeof(buf), pos, "+0x");
                    pos = append_u(buf, sizeof(buf), pos,
                                   (uint64_t)(ip - (uintptr_t)di.dli_saddr),
                                   16);
                }
            }
            attributed = true;
        }
        if (ip && !attributed) {
            // dladdr could not name it — scan the maps like the W10-FAULT
            // guard does, so foreign-loader mappings still resolve.
            FILE* maps = fopen("/proc/self/maps", "r");
            if (maps) {
                char line[512];
                while (fgets(line, sizeof line, maps)) {
                    unsigned long lo, hi;
                    char perms[8], path[400] = "";
                    if (sscanf(line, "%lx-%lx %7s %*x %*x:%*x %*u %399s",
                               &lo, &hi, perms, path) >= 3) {
                        if (ip >= lo && ip < hi && path[0] == '/') {
                            const char* bn = strrchr(path, '/');
                            bn = bn ? bn + 1 : path;
                            pos = append_str(buf, sizeof(buf), pos, " mod=");
                            pos = append_str(buf, sizeof(buf), pos, bn);
                            pos = append_str(buf, sizeof(buf), pos,
                                             " modoff=0x");
                            pos = append_u(buf, sizeof(buf), pos,
                                           (uint64_t)(ip - lo), 16);
                            break;
                        }
                    }
                }
                fclose(maps);
            }
        }
        pos = append_str(buf, sizeof(buf), pos, "\n");
    }

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
        /* T19 attribution: name the module + nearest exported symbol */
        Dl_info di;
        if (dladdr(frames[i], &di) && di.dli_fname) {
            const char* base_name = strrchr(di.dli_fname, '/');
            base_name = base_name ? base_name + 1 : di.dli_fname;
            pos = append_str(buf, sizeof(buf), pos, " mod=");
            pos = append_str(buf, sizeof(buf), pos, base_name);
            if (di.dli_sname) {
                pos = append_str(buf, sizeof(buf), pos, " sym=");
                pos = append_str(buf, sizeof(buf), pos, di.dli_sname);
                pos = append_str(buf, sizeof(buf), pos, "+0x");
                pos = append_u(buf, sizeof(buf), pos,
                               (uint64_t)((uintptr_t)frames[i] -
                                          (uintptr_t)di.dli_saddr), 16);
            } else if (di.dli_fbase) {
                pos = append_str(buf, sizeof(buf), pos, " modoff=0x");
                pos = append_u(buf, sizeof(buf), pos,
                               (uint64_t)((uintptr_t)frames[i] -
                                          (uintptr_t)di.dli_fbase), 16);
            }
        }
        pos = append_str(buf, sizeof(buf), pos, "\n");
        if (pos > sizeof(buf) - 128) break;
    }
    pos = append_str(buf, sizeof(buf), pos, "[S100-CRASH-FORENSICS-END]\n");

    ssize_t rc = write(2, buf, pos);
    (void)rc;

    // Restore default disposition and re-raise: honest signal death (rc stays
    // signal-class) with the evidence block already on stderr.
    // W15: UNBLOCK the signal first. The kernel blocks the faulting signal
    // (and sa_mask) for the duration of a handler installed without
    // SA_NODEFER — raise() on a blocked signal only makes it PENDING, so
    // the raise silently returned, _exit(128+sig) ran, and the process
    // EXITED with code 128+sig instead of dying by signal. Live evidence:
    // the W14/W15 fork-probe children exited 0x8b (139) — the probe
    // classifier saw WIFEXITED, not WIFSIGNALED, and reported REFUSED for
    // an actually-FAULTED probe (parent then re-faulted: "post-probe
    // residual"). With the unblock, the death is genuinely signal-class.
    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = SIG_DFL;
    sigemptyset(&sa.sa_mask);
    sigaction(sig, &sa, nullptr);
    sigset_t block;
    sigemptyset(&block);
    sigaddset(&block, sig);
    sigprocmask(SIG_UNBLOCK, &block, nullptr);
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
