#pragma once
// ============================================================================
// S100 §3/§7 — PERMANENT CRASH FORENSICS (issue #345 / F-NEW-168 dooz rc=-11)
//
// Law: no runtime death may remain a mystery. A signal death (SIGSEGV/SIGBUS/
// SIGABRT/SIGFPE/SIGILL) MUST produce an async-signal-safe evidence block:
//   signal number, si_code, fault address, native frame addresses, and the
//   last semantic operations (DEX method-entry ring) — written to stderr fd 2
//   (already captured by every runner log) before the default disposition
//   re-raises.
//
// The address block is resolved offline with addr2line against the -g binary;
// no symbolization (malloc) happens inside the handler.
//
// note() is the runtime's "last semantic op" trail: bounded 64-slot ring of
// 160-byte records, lock-free slot publish (safe under torn concurrent
// writes — diagnostics, not a data contract).
// ============================================================================
namespace CrashForensics {

// Install handlers for SIGSEGV/SIGBUS/SIGABRT/SIGFPE/SIGILL. Idempotent.
// Warms backtrace() once at install time (it may malloc on first use —
// never inside the handler).
void install();

// Record the last semantic operation. fmt printf-style, truncated to 160B.
// Cheap: one bounded snprintf + index.fetch_add + memcpy.
void note(const char* tag, const char* fmt, ...) __attribute__((format(printf, 2, 3)));

}  // namespace CrashForensics
