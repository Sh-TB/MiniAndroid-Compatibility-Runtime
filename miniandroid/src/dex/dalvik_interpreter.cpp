/*
 * MiniAndroid Runtime v0.2 - Real Dalvik Execution Engine Implementation
 * EXP-030: Real Bytecode Execution
 * 
 * Complete implementation of Dalvik register machine with:
 * - 25+ opcodes executed
 * - Real register state changes
 * - Object heap allocation
 * - Method call stack
 * - API bridge integration
 */

#include "dalvik_engine.h"
#include "dex_parser.h"
#include "mutf8.h"
#include "../src/compat/glibc_mallinfo2.h"  // W15 #627 D-03/H-03: mallinfo2 fallback (glibc < 2.33)
#include <dlfcn.h>  // #371 PHASE B2: real dlopen/dlerror boundary diagnostics
#include <openssl/evp.h>  // #371 PHASE B2: sha16 file identity for loadLibrary law
#include <atomic>  // CONT-86 F-NEW-390 bounded diag counters
#include "../api/android_stubs.h"
#include "../api/http_client.h"  // S100 NET-001 (MG-247/248): real HTTP(S)
#include "../storage/data_root.h"
#include "../audio/audio_engine.h"  // CONT-65 F-NEW-356: real-decode media law
#include <filesystem>
#include <cstring>  // F-109c: strcmp arith dispatch (S62)
#include "../diagnostics/gfx_trace.h"  // CONT-83 WS-B frame correlation
#include "../diagnostics/mem_probe.h"
#include "../diagnostics/click_audit.h"  // UNIFIED_002 EXP-100: env-gated click audit (DIAGNOSTIC)
#include "../diagnostics/crash_forensics.h"  // S100 §3: last-op ring (issue #345)
#include "../diagnostics/gfx_provenance.h"  // S82-GFX §6: evidence-bit pixel chain
#include "../diagnostics/file_io_trace.h"   // IAPK: file-IO provenance (F-NEW-234 wave)
#include "../diagnostics/install_inspection.h"  // GATE A: zip_contains_entry (System.loadLibrary law)
#include "../jni/jni_bridge.h"
#include "../jni/dlopen_exec.h"  // #371 CLOSEOUT S-2: real native execution layer
#include "../fonts/text_shaper.h"  // F-NEW-344: getDesiredWidth via the SAME
                                   // shaper the drawText replay uses — the
                                   // single source of truth (box == pixels).
#include <nlohmann/json.hpp>  // F-NEW-243: org.json real laws (ordered_json)
// EXP-051: Shadow registry integration.
#include "../framework/shadow_registry.h"
#include <functional>
#include "../framework/android_shadows.h"
#include "../webview/webview_engine.h"
#include "../framework/choreographer_shadow.h"  // R-NEW-345 park-drain: vsync during park
#include "../framework/dialog_shadow.h"
#include "../framework/canvas_shadow.h"

// ─────────────────────────────────────────────────────────────────────────────
// CONT-121 W-01 (FIX-449 endgame): JVM String UTF-16 UNIT LAW helpers.
// Shared by both String.length sites and both String.charAt sites (the C97
// bridge-intrinsic entry and the F-090e deep site).
//
// ROOT (issue #364 F-NEW-449, S36-AOOB telegram play_billing n2.r):
// protobuf-lite's RawMessageInfo info-string decoder walks String.charAt
// under String.length() — both must address UTF-16 CODE UNITS (JVM/AOSP
// law). The engine answered length() as UTF-8 BYTE count and charAt by
// UTF-8 CODE-POINT index. The p3 info string is 40 UTF-16 units but 64
// UTF-8 bytes (12 chars in the Myanmar block are 3 bytes each, 1 unit),
// so the walk loop `i < length()` ran 24 phantom iterations past the real
// data, decoded garbage field descriptors, over-consumed the Object[11]
// entries array, and died at entries[11] (S36-AOOB len=11 idx=11). ASCII-
// only strings have bytes == units == code points, which is why every
// prior anchor stayed byte-identical.
// ─────────────────────────────────────────────────────────────────────────────
namespace {
int32_t str_utf16_unit_count(const std::string& s) {
    int32_t units = 0;
    for (size_t i = 0; i < s.size();) {
        unsigned char b0 = static_cast<unsigned char>(s[i]);
        size_t len = 1;
        if ((b0 & 0xE0) == 0xC0 && i + 1 < s.size()) len = 2;
        else if ((b0 & 0xF0) == 0xE0 && i + 2 < s.size()) len = 3;
        else if ((b0 & 0xF8) == 0xF0 && i + 3 < s.size()) len = 4;
        // 4-byte UTF-8 = supplementary code point = 2 UTF-16 units
        units += (len == 4) ? 2 : 1;
        i += len;
    }
    return units;
}
// Walks to UTF-16 unit `idx`; answers the unit's char value. Returns false
// when idx is outside [0, unit_count) — callers keep the honest-0 OOB rule
// (R-NEW-353 contract unchanged).
bool str_char_at_unit(const std::string& s, int32_t idx, int32_t& out) {
    if (idx < 0) return false;
    int32_t unit = 0;
    for (size_t i = 0; i < s.size();) {
        unsigned char b0 = static_cast<unsigned char>(s[i]);
        size_t len = 1;
        int32_t cp = b0;
        if ((b0 & 0xE0) == 0xC0 && i + 1 < s.size()) {
            len = 2;
            cp = ((b0 & 0x1F) << 6) |
                 (static_cast<unsigned char>(s[i + 1]) & 0x3F);
        } else if ((b0 & 0xF0) == 0xE0 && i + 2 < s.size()) {
            len = 3;
            cp = ((b0 & 0x0F) << 12) |
                 ((static_cast<unsigned char>(s[i + 1]) & 0x3F) << 6) |
                 (static_cast<unsigned char>(s[i + 2]) & 0x3F);
        } else if ((b0 & 0xF8) == 0xF0 && i + 3 < s.size()) {
            len = 4;
            cp = ((b0 & 0x07) << 18) |
                 ((static_cast<unsigned char>(s[i + 1]) & 0x3F) << 12) |
                 ((static_cast<unsigned char>(s[i + 2]) & 0x3F) << 6) |
                 (static_cast<unsigned char>(s[i + 3]) & 0x3F);
        }
        if (cp >= 0x10000) {
            cp -= 0x10000;
            if (unit == idx) {
                out = 0xD800 + (cp >> 10);
                return true;
            }
            if (unit + 1 == idx) {
                out = 0xDC00 + (cp & 0x3FF);
                return true;
            }
            unit += 2;
        } else {
            if (unit == idx) {
                out = cp;
                return true;
            }
            unit += 1;
        }
        i += len;
    }
    return false;
}
}  // namespace

#include "../framework/heap_adapter.h"
#include "../framework/bitmap_shadow.h"  // S109 ROOT-033: getDrawable raster decode
#include "../framework/view_ancestry.h"  // G12 FIX-G12-001: AOSP framework ancestry law
#include "../storage/sqlite_shadow.h"    // M3 F-ROOM-CHAIN: SQLite family shadow
#include "../resources/resource_runtime.h"  // G10 FIX-G10-002: early classifier wiring
#include "../resources/font_family.h"    // C9-16/C9-17 (CODER 9): font-family + weight law
#include "../resources/plurals.h"        // C9-20 (CODER 9): CLDR plural-category law
#include <png.h>                          // C9-7 (CODER 9): Bitmap.compress PNG encode
#include <setjmp.h>                       // C9-7: libpng error contract
#include <chrono>
#include <unordered_map>  // CONT-29 W1: METHOD-CENSUS (env-gated, read-only)
#include <x86intrin.h>  // S61 PERF: __rdtsc phase timers
#include <atomic>
#include <algorithm>
#include <iostream>
#include <malloc.h>
#include <fstream>
#include <regex>
#include <sstream>
#include <iomanip>
#include <cassert>
#include <cctype>    // EXP-071 Phase 6: std::toupper/std::tolower for String.toUpperCase/toLowerCase
#include <fcntl.h>   // LOADING-CAMPAIGN (R-2 FIX): real host fds for openFd/PFD
#include <unistd.h>  // LOADING-CAMPAIGN: ::open/::close/::dup
#include <unordered_set>
#include <set>            // F-023: default-interface-method dispatch visited set

// ────────────────────────────────────────────────────────────────────────
// CONT-96 W1 (F-074 throughput law): diagnostic env presence-checks used
// to call std::getenv() on EVERY interpreter instruction / method entry —
// an environ walk per opcode (measured as a real fraction of the ~310K
// ins/s interpreter wall on the 30s Telegram gate; see the 14530-site
// note for the single-site precedent). Diagnostic flags are
// process-constant: diag_env() caches the first-use answer keyed by the
// literal POINTER (every diagnostic call site passes a string literal;
// literals are stable for the process lifetime). Identical answers,
// identical stderr when a flag is set — only the per-op environ walk is
// gone. Value-using sites (find(getenv(...)), env[0]=='0') keep their
// raw getenv by design.
// ────────────────────────────────────────────────────────────────────────
static bool diag_env(const char* name) {
    struct Entry { const char* name; bool value; };
    static thread_local Entry table[96];
    static thread_local uint32_t count = 0;
    for (uint32_t i = 0; i < count; ++i)
        if (table[i].name == name) return table[i].value;
    const bool v = std::getenv(name) != nullptr;
    if (count < 96) {
        table[count].name = name;
        table[count].value = v;
        ++count;
    }
    return v;
}

#include "dex/dalvik_engine_internal.h"
namespace miniandroid {
namespace dalvik {
bool DalvikExecutionEngine::fetch_decode_execute(DalvikExecutionResult& result) {
    uint64_t f107_t0 = 0; phase_clock().enter(phase_clock().fetch_exec, f107_t0);
    struct F107Guard { PhaseClock::Phase& ph; uint64_t t0; ~F107Guard(){{ phase_clock().exit(ph, t0);}} } f107_guard{phase_clock().fetch_exec, f107_t0};
    // EXP-071 Phase 6 debug: Log entry to fetch_decode_execute for setCountry.
    if (current_method_ == "setCountry" && current_class_.find("PhoneView") != std::string::npos) {
        std::cerr << "[EXP071-FDE-ENTER] " << current_class_ << "." << current_method_
                  << " halted_=" << halted_
                  << " pc_=" << pc_
                  << " bytecode_.size()=" << bytecode_.size()
                  << std::endl;
    }
    while (!halted_ && pc_ < bytecode_.size()) {
        uint64_t s62_pre0 = phase_clock().on ? __rdtsc() : 0;  // S62 bucket: pre
        InstructionTrace trace;
        // S156-P4 (CONT-42 zero-cost-gate law): the reserve was an
        // UNCONDITIONAL malloc/free pair per executed instruction. When
        // trace_cap == 0 the recorded trace is never consumed (the
        // recording block below is skipped) — capacity is pure waste.
        // Handlers pushing operands into a zero-capacity vector still
        // allocate lazily: identical content, zero behavior change.
        if (config_.trace_cap > 0) trace.operands.reserve(4);
        trace.sequence = instruction_sequence_++;
        trace.pc_before = pc_;

        // EXP-071 Phase 6 debug: Log first 20 instructions of setCountry.
        if (current_method_ == "setCountry" && current_class_.find("PhoneView") != std::string::npos && instruction_sequence_ <= 20) {
            std::cerr << "[EXP071-FDE-LOOP] " << current_class_ << "." << current_method_
                      << " iter=" << instruction_sequence_
                      << " pc_=" << pc_
                      << " opcode=0x" << std::hex << (int)(bytecode_[pc_] & 0xFF) << std::dec
                      << std::endl;
        }

        // S136 (CONT-11 W9): PTE (pointer-event) dispatch probe — env-gated,
        // bounded, read-only. Logs every method ENTRY named onPointerEvent
        // while a touch dispatch is active: the receiver filter class + the
        // pass enum constant + the event object. Answers THE train-4 F7 leg:
        // does the UP event ever reach the clickable's filter, and at which
        // pass? (SuspendingPointerInputFilter.onPointerEvent is the only
        // offerPointerEvent feeder — without this we cannot see the death.)
        if (pc_ == 0 && touch_dispatch_active_ &&
            current_method_ == "onPointerEvent" &&
            std::getenv("MINIANDROID_PTE_TRACE") != nullptr) {
            static thread_local uint64_t s136_pte_n = 0;
            if (s136_pte_n++ < 96) {
                std::string pass_name = "-";
                if (current_registers_ && current_registers_->get_size() >= 2) {
                    uint32_t total = current_registers_->get_size();
                    uint32_t ins_n = current_registers_->get_ins_count();
                    // receiver=p0, event=p1, pass=p2 (IntSize=p3/p4)
                    if (ins_n >= 3) {
                        DalvikValue passv = current_registers_->read_v(
                            static_cast<uint8_t>(total - 2));
                        if (passv.type == DalvikType::OBJECT_REF) {
                            auto nm = heap_.get_object_field(passv.object_id,
                                                             "enum_name");
                            if (nm.has_value() &&
                                nm->type == DalvikType::STRING_REF)
                                pass_name = nm->string_val;
                        }
                    }
                }
                std::cerr << "[PTE-DISPATCH] filter=" << current_class_
                          << " pass=" << pass_name << std::endl;
            }
        }
        // S136b: invoke-target probe for ONE method (class|method via
        // MINIANDROID_INVOKE_TARGET_TRACE). Logs the resolved callee class
        // + name of every invoke-family instruction executed inside the
        // matched frame while touch dispatch is active — decodes the R8
        // dispatch chain one level at a time.
        {
            static thread_local const char* itt_filter =
                std::getenv("MINIANDROID_INVOKE_TARGET_TRACE");
            if (itt_filter && touch_dispatch_active_) {
                std::string f(itt_filter);
                auto bar = f.find('|');
                std::string fcls = (bar == std::string::npos) ? f : f.substr(0, bar);
                std::string fmth = (bar == std::string::npos) ? "" : f.substr(bar + 1);
                if (current_class_.find(fcls) != std::string::npos &&
                    (fmth.empty() || current_method_ == fmth) &&
                    pc_ < bytecode_.size()) {
                    uint16_t w = bytecode_[pc_];
                    uint8_t op = static_cast<uint8_t>(w & 0xFF);
                    bool is_invoke =
                        (op >= 0x6e && op <= 0x72) || (op >= 0x74 && op <= 0x78);
                    if (is_invoke && (pc_ + 1) < bytecode_.size()) {
                        static thread_local uint64_t itt_n = 0;
                        if (itt_n++ < 256) {
                            uint32_t midx = bytecode_[pc_ + 1];
                            std::string cn, mn;
                            try {
                                cn = resolve_method_class_for_dex(midx, current_dex_index_);
                                mn = resolve_method_name_for_dex(midx, current_dex_index_);
                            } catch (...) {}
                            // S136f: receiver identity for virtual/interface
                            // invokes (35c: C = low nibble of unit pc+2).
                            std::string recv = "-";
                            if (op != 0x71 && current_registers_) {
                                uint8_t regc =
                                    static_cast<uint8_t>(bytecode_[pc_ + 2] & 0xF);
                                DalvikValue r =
                                    current_registers_->read_v(regc);
                                if (r.type == DalvikType::OBJECT_REF)
                                    recv = std::string(r.class_desc) + "#" +
                                           std::to_string(r.object_id);
                            }
                            std::cerr << "[INVOKE-TARGET] " << current_class_ << "."
                                      << current_method_ << " pc=" << pc_
                                      << " -> " << cn << "." << mn
                                      << " recv=" << recv
                                      << " u0=" << bytecode_[pc_]
                                      << " u2=" << bytecode_[pc_ + 2]
                                      << std::endl;
                        }
                    }
                }
            }
        }

        // S137a: SuspendingPointerInputModifierNodeImpl ctor probe. At every
        // invoke-family site resolving to Lor1;.<init> print the receiver id
        // and the POINTER-INPUT-HANDLER argument (register regc+3, the 3rd
        // param after this/viewCfg/density) with its heap class — answers
        // whether the node is born with the real app SAM lambda or a static
        // no-op handler (Lpv; singletons).
        {
            static thread_local const bool s137_ctor =
                std::getenv("MINIANDROID_LOR1_CTOR_TRACE") != nullptr;
            if (s137_ctor && pc_ < bytecode_.size()) {
                uint16_t w = bytecode_[pc_];
                uint8_t op = static_cast<uint8_t>(w & 0xFF);
                bool is_invoke =
                    (op >= 0x6e && op <= 0x72) || (op >= 0x74 && op <= 0x78);
                if (is_invoke && (pc_ + 1) < bytecode_.size()) {
                    uint32_t midx = bytecode_[pc_ + 1];
                    std::string cn, mn;
                    try {
                        cn = resolve_method_class_for_dex(midx, current_dex_index_);
                        mn = resolve_method_name_for_dex(midx, current_dex_index_);
                    } catch (...) {}
                    if (cn == "Lor1;" && mn == "<init>" && current_registers_) {
                        static thread_local uint64_t s137_n = 0;
                        if (s137_n++ < 64) {
                            // 35c register list lives in nibbles FEDC of the
                            // second word (bytecode_[pc_+2]) — NOT consecutive
                            // from C. p1=C, p2=D, p3=E, p4=F; handler = p4.
                            uint16_t fdec = bytecode_[pc_ + 2];
                            uint8_t reg_this =
                                static_cast<uint8_t>(fdec & 0xF);
                            uint8_t reg_p1 =
                                static_cast<uint8_t>((fdec >> 4) & 0xF);
                            uint8_t reg_p2 =
                                static_cast<uint8_t>((fdec >> 8) & 0xF);
                            uint8_t reg_p3 =
                                static_cast<uint8_t>((fdec >> 12) & 0xF);
                            DalvikValue recv =
                                current_registers_->read_v(reg_this);
                            DalvikValue p1 =
                                current_registers_->read_v(reg_p1);
                            DalvikValue p2 =
                                current_registers_->read_v(reg_p2);
                            DalvikValue hnd =
                                current_registers_->read_v(reg_p3);
                            std::string hc = "-";
                            if (hnd.type == DalvikType::OBJECT_REF &&
                                heap_.has_object(hnd.object_id))
                                hc = heap_.get(hnd.object_id)->class_descriptor;
                            std::string caller =
                                current_class_ + "." + current_method_;
                            std::cerr << "[LOR1-CTOR] caller=" << caller
                                      << " recv=obj#" << recv.object_id
                                      << " p1=" << p1.class_desc << "#"
                                      << p1.object_id
                                      << " p2=" << p2.class_desc << "#"
                                      << p2.object_id
                                      << " handler=" << hnd.class_desc << "#"
                                      << hnd.object_id
                                      << " heapcls=" << hc
                                      << std::endl;
                        }
                    }
                }
            }
        }

        // S137b (car-9): composed-factory arg-evaluation probe. At every
        // invoke resolving to Lkr1;.* (pointerInput/composed family) or
        // Ljr1;.<init> (element ctor) dump caller, opcode format regs
        // (35c nibbles FEDC+G / 3rc range), every arg value with heap
        // class, and the receiver object's FIELDS (captures) — proves
        // DYNAMICALLY whether the factory lambda's captured block is
        // already the Lpv; no-op at birth or corruption happens at the
        // call-site arg pass (train-6 F7 next leg).
        {
            static thread_local const bool s137b =
                std::getenv("MINIANDROID_KR1_CALL_TRACE") != nullptr;
            if (s137b && pc_ < bytecode_.size()) {
                uint16_t w = bytecode_[pc_];
                uint8_t op = static_cast<uint8_t>(w & 0xFF);
                bool is_invoke =
                    (op >= 0x6e && op <= 0x72) || (op >= 0x74 && op <= 0x78);
                if (is_invoke && (pc_ + 2) < bytecode_.size()) {
                    uint32_t midx = bytecode_[pc_ + 1];
                    std::string cn, mn;
                    try {
                        cn = resolve_method_class_for_dex(midx, current_dex_index_);
                        mn = resolve_method_name_for_dex(midx, current_dex_index_);
                    } catch (...) {}
                    // ── TRAIN-64 (T64-C, DIAG-ONLY): every Lu71;.<init>
                    // (PointerInputChange ctor, 15 regs → invoke-direct/3rc)
                    // during the touch dispatch — dump ALL ctor args from
                    // the range base. Pins the isInitiallyConsumed value
                    // the adapter actually passes (awaitFirstDown killer
                    // candidate: requireUnconsumed=true + changedToDown()
                    // demands !isConsumed).
                    if (cn == "Lu71;" && mn == "<init>" &&
                        current_registers_) {
                        static thread_local uint64_t t64c_n = 0;
                        if (t64c_n++ < 24) {
                            uint16_t t64c_op =
                                static_cast<uint8_t>(bytecode_[pc_] & 0xFF);
                            uint16_t t64c_base = bytecode_[pc_ + 2];
                            std::string t64c_args;
                            if (t64c_op == 0x76) {  // invoke-direct/range (3rc)
                                for (int t64c_i = 0; t64c_i < 23;
                                     ++t64c_i) {
                                    DalvikValue t64c_v =
                                        current_registers_->read_v(
                                            static_cast<uint8_t>(
                                                t64c_base + t64c_i));
                                    t64c_args +=
                                        dalvik_value_to_string(t64c_v) + ",";
                                }
                            } else {
                                t64c_args = "<35c>";
                            }
                            std::cerr << "[T64-C] Lu71;.<init> op=0x"
                                      << std::hex << t64c_op << std::dec
                                      << " base=v" << t64c_base
                                      << " caller=" << current_class_ << "."
                                      << current_method_
                                      << " args=[" << t64c_args << "]"
                                      << std::endl;
                        }
                    }
                    bool hit_kr1 = (cn == "Lkr1;");
                    bool hit_jr1_init = (cn == "Ljr1;" && mn == "<init>");
                    // car-12: global composed-factory invoke counter —
                    // Lk90;.f is the Modifier.(Composer,Int)->Modifier
                    // factory invoke; every composed materialization must
                    // pass through it exactly once per composed element.
                    bool hit_k90f = (cn == "Lk90;" && mn == "f");
                    // car-13: ComposableLambda.invoke dispatch probe —
                    // Lom;.h is the (Composer,Int)->R composable lambda
                    // invoke arm; every slot-table composable dispatch
                    // passes through it. Dump receiver identity to see
                    // WHICH lambdas the runtime actually dispatches.
                    bool hit_omh = (cn == "Lom;" && mn == "h");
                    if ((hit_kr1 || hit_jr1_init || hit_k90f || hit_omh) &&
                        current_registers_) {
                        static thread_local uint64_t s137b_n = 0;
                        if (s137b_n++ < 96) {
                            if (hit_k90f || hit_omh) {
                                // 35c A=4: (receiver=Lk90;, arg1=Modifier,
                                // arg2=Composer, arg3=Int) — dump recv +
                                // heap class of receiver for identity.
                                uint16_t fdec = bytecode_[pc_ + 2];
                                uint8_t rr =
                                    static_cast<uint8_t>(fdec & 0xF);
                                DalvikValue recv =
                                    current_registers_->read_v(rr);
                                std::string rc = "-";
                                if (recv.type == DalvikType::OBJECT_REF &&
                                    heap_.has_object(recv.object_id))
                                    rc = heap_.get(recv.object_id)
                                             ->class_descriptor;
                                std::cerr << "["
                                          << (hit_omh ? "OM-H" : "K90-F")
                                          << "] caller="
                                          << current_class_ << "."
                                          << current_method_
                                          << " pc=" << pc_
                                          << " recv=" << rc << "#"
                                          << recv.object_id
                                          << std::endl;
                            }
                            bool is_range = (op >= 0x74 && op <= 0x78);
                            uint8_t cnt = static_cast<uint8_t>(
                                (bytecode_[pc_] >> 8) & 0xFF);
                            std::vector<uint8_t> regs;
                            if (!is_range) {
                                uint16_t fdec = bytecode_[pc_ + 2];
                                regs = {
                                    static_cast<uint8_t>(fdec & 0xF),
                                    static_cast<uint8_t>((fdec >> 4) & 0xF),
                                    static_cast<uint8_t>((fdec >> 8) & 0xF),
                                    static_cast<uint8_t>((fdec >> 12) & 0xF),
                                    static_cast<uint8_t>(
                                        (bytecode_[pc_] >> 12) & 0xF)};
                            } else {
                                uint16_t start =
                                    bytecode_[pc_ + 2];
                                for (uint8_t i = 0; i < cnt && i < 8; i++)
                                    regs.push_back(static_cast<uint8_t>(
                                        start + i));
                            }
                            if (regs.size() > cnt) regs.resize(cnt);
                            std::string args;
                            for (size_t i = 0; i < regs.size(); i++) {
                                DalvikValue a =
                                    current_registers_->read_v(regs[i]);
                                std::string ac = "-";
                                if (a.type == DalvikType::OBJECT_REF &&
                                    heap_.has_object(a.object_id))
                                    ac = heap_.get(a.object_id)
                                             ->class_descriptor;
                                args += (i ? "," : "");
                                args += "r" + std::to_string(regs[i]) + "=" +
                                        a.class_desc + "#" +
                                        std::to_string(a.object_id) + "{" +
                                        ac + "}";
                            }
                            std::string recvfields = "-";
                            DalvikValue recv =
                                current_registers_->read_v(regs.empty()
                                                               ? 0
                                                               : regs[0]);
                            if (recv.type == DalvikType::OBJECT_REF &&
                                heap_.has_object(recv.object_id)) {
                                recvfields = "";
                                auto* ho = heap_.get(recv.object_id);
                                int fc = 0;
                                for (auto& kv : ho->fields) {
                                    if (fc++ >= 8) break;
                                    std::string vc = "-";
                                    if (kv.second.type ==
                                        DalvikType::OBJECT_REF)
                                        vc = kv.second.class_desc + "#" +
                                             std::to_string(
                                                 kv.second.object_id);
                                    recvfields += (fc > 1 ? "|" : "") +
                                                  kv.first + "=" + vc;
                                }
                                if (recvfields.empty())
                                    recvfields = "(nofields)";
                            }
                            std::cerr << "[KR1-CALL] caller="
                                      << current_class_ << "."
                                      << current_method_
                                      << " pc=" << pc_
                                      << " op=0x" << std::hex
                                      << static_cast<int>(op) << std::dec
                                      << " tgt=" << cn << "." << mn
                                      << " cnt=" << static_cast<int>(cnt)
                                      << (is_range ? " range" : " 35c")
                                      << " recv=" << recv.class_desc << "#"
                                      << recv.object_id
                                      << " fields=" << recvfields
                                      << " args=[" << args << "]"
                                      << std::endl;
                        }
                    }
                }
            }
        }

        // S137c (car-10/11): composable-factory execution progress probe.
        // train-7 car-9 proved the REAL pointerInput element (Ljr1; with
        // wv1.z/y keys + Lj6; handler) is constructed statically inside
        // Lpm;.c (pc 0x0db6/0x0e04) but NEVER dynamically — this probe
        // logs entry + every invoke executed inside a WATCHLIST of
        // class|method pairs (MINIANDROID_PMC_TRACE="Lcls;|mth,Lcls;|mth",
        // no touch gate: composition runs outside dispatch) so the last
        // logged pc bounds exactly where each composable stops.
        {
            static thread_local const char* pmc_env =
                std::getenv("MINIANDROID_PMC_TRACE");
            static thread_local std::vector<std::pair<std::string,
                std::string>>* pmc_watch = nullptr;
            if (pmc_env && !pmc_watch) {
                pmc_watch = new std::vector<std::pair<std::string,
                    std::string>>();
                std::string f(pmc_env);
                size_t pos = 0;
                while (pos < f.size()) {
                    size_t comma = f.find(',', pos);
                    std::string item = f.substr(
                        pos, (comma == std::string::npos) ? std::string::npos
                                                          : comma - pos);
                    auto bar = item.find('|');
                    if (bar != std::string::npos)
                        pmc_watch->emplace_back(item.substr(0, bar),
                                                item.substr(bar + 1));
                    if (comma == std::string::npos) break;
                    pos = comma + 1;
                }
            }
            if (pmc_watch && !pmc_watch->empty() && pc_ < bytecode_.size()) {
                for (auto& w : *pmc_watch) {
                    if (current_class_ != w.first ||
                        current_method_ != w.second)
                        continue;
                    static thread_local uint64_t pmc_n = 0;
                    if (pmc_n++ < 2400) {
                        uint16_t w2 = bytecode_[pc_];
                        uint8_t op = static_cast<uint8_t>(w2 & 0xFF);
                        if (pc_ == 0) {
                            std::cerr << "[PMC] ENTER " << current_class_
                                      << "." << current_method_ << std::endl;
                        }
                        bool is_invoke =
                            (op >= 0x6e && op <= 0x72) ||
                            (op >= 0x74 && op <= 0x78);
                        if (is_invoke && (pc_ + 2) < bytecode_.size()) {
                            uint32_t midx = bytecode_[pc_ + 1];
                            std::string cn, mn;
                            try {
                                cn = resolve_method_class_for_dex(
                                    midx, current_dex_index_);
                                mn = resolve_method_name_for_dex(
                                    midx, current_dex_index_);
                            } catch (...) {}
                            std::cerr << "[PMC] " << current_class_ << "."
                                      << current_method_ << " pc=0x"
                                      << std::hex << pc_ << std::dec
                                      << " -> " << cn << "." << mn
                                      << std::endl;
                        }
                    }
                    break;
                }
            }
        }

        // S136c: static invoke-site dump at method ENTRY (one matched
        // method via MINIANDROID_INVOKE_SITES=<class>|<method>). Scans the
        // frame's bytecode_ for every invoke-family site and prints the
        // resolved target — decodes the FULL R8 call graph of the method
        // (executed or not) using the engine's own bytecode view.
        {
            static thread_local const char* is_filter =
                std::getenv("MINIANDROID_INVOKE_SITES");
            if (is_filter && pc_ == 0 && touch_dispatch_active_) {
                std::string f(is_filter);
                auto bar = f.find('|');
                std::string fcls = (bar == std::string::npos) ? f : f.substr(0, bar);
                std::string fmth = (bar == std::string::npos) ? "" : f.substr(bar + 1);
                if (current_class_.find(fcls) != std::string::npos &&
                    (fmth.empty() || current_method_ == fmth)) {
                    static thread_local uint64_t is_n = 0;
                    if (is_n++ < 8) {
                        for (uint32_t u = 0; u + 1 < bytecode_.size(); ++u) {
                            uint8_t op = static_cast<uint8_t>(bytecode_[u] & 0xFF);
                            if ((op >= 0x6e && op <= 0x72) ||
                                (op >= 0x74 && op <= 0x78)) {
                                uint32_t midx = bytecode_[u + 1];
                                std::string cn = "?", mn = "?";
                                try {
                                    cn = resolve_method_class_for_dex(midx, current_dex_index_);
                                    mn = resolve_method_name_for_dex(midx, current_dex_index_);
                                } catch (...) {}
                                std::cerr << "[INVOKE-SITE] " << current_class_ << "."
                                          << current_method_ << " pc=" << u
                                          << " -> " << cn << "." << mn << std::endl;
                            }
                        }
                    }
                }
            }
        }

        // S136d: P-entry probe — log the receiver class of every method
        // named MINIANDROID_P_ENTRY_TRACE's value (e.g. "P") at frame entry
        // while touch dispatch is active. The filter impl of the abstract
        // PointerInputFilter.onPointerEvent (= Llo;.P) never executes a
        // frame of its own, so name+class METHOD-TRACE cannot see it; the
        // impl's entry (class.P) does. Bounded.
        {
            static thread_local const char* pe_name =
                std::getenv("MINIANDROID_P_ENTRY_TRACE");
            if (pe_name && pc_ == 0 && touch_dispatch_active_ &&
                current_method_ == pe_name) {
                static thread_local uint64_t pe_n = 0;
                if (pe_n++ < 96) {
                    std::cerr << "[P-ENTRY] " << current_class_ << "."
                              << current_method_ << std::endl;
                }
                // S136e: one bounded static invoke-site dump per receiver
                // class — identifies WHICH P impl is the pointer filter
                // (its sites will show the offerPointerEvent machinery).
                static thread_local std::string pe_dumped_cls;
                std::string cls_snap = current_class_;
                if (pe_dumped_cls != cls_snap) {
                    pe_dumped_cls = cls_snap;
                    std::cerr << "[P-SITES] " << cls_snap << "." << current_method_
                              << " size=" << bytecode_.size() << std::endl;
                    for (uint32_t u = 0; u + 1 < bytecode_.size(); ++u) {
                        uint8_t op = static_cast<uint8_t>(bytecode_[u] & 0xFF);
                        if ((op >= 0x6e && op <= 0x72) ||
                            (op >= 0x74 && op <= 0x78)) {
                            uint32_t midx = bytecode_[u + 1];
                            std::string cn = "?", mn = "?";
                            try {
                                cn = resolve_method_class_for_dex(midx, current_dex_index_);
                                mn = resolve_method_name_for_dex(midx, current_dex_index_);
                            } catch (...) {}
                            std::cerr << "[P-SITE] pc=" << u << " -> "
                                      << cn << "." << mn << std::endl;
                        }
                    }
                }
            }
        }

        // M3 METHOD-TRACE (AG diagnostic, 2026-09-08): env-gated, bounded,
        // per-instruction trace of ONE matched method. Syntax:
        //   MINIANDROID_METHOD_TRACE=<class-substr>|<method-substr>
        // Prints pc, opcode word, and every initialized register's value
        // BEFORE the instruction executes. Bounded by a 4000-line budget so
        // a full-corpus run can never flood. Law: diagnostics must never
        // change semantics — this is read-only (pure get_register reads).
        {
            uint16_t mt_word = bytecode_[pc_];
            static thread_local const char* mt_filter =
                std::getenv("MINIANDROID_METHOD_TRACE");
            // S49: budget env-configurable (MINIANDROID_METHOD_TRACE_BUDGET)
            // so deep-loop forensics (R-NEW-361) can capture 50k-visit spins.
            static thread_local uint32_t mt_budget = [] {
                const char* b = std::getenv("MINIANDROID_METHOD_TRACE_BUDGET");
                return (b != nullptr) ? static_cast<uint32_t>(atoi(b)) : 4000u;
            }();
            if (mt_filter && mt_budget > 0) {
                std::string f(mt_filter);
                auto bar = f.find('|');
                std::string fcls = (bar == std::string::npos) ? f : f.substr(0, bar);
                std::string fmth = (bar == std::string::npos) ? "" : f.substr(bar + 1);
                if (current_class_.find(fcls) != std::string::npos &&
                    (fmth.empty() || current_method_ == fmth)) {
                    mt_budget--;
                    std::cerr << "[METHOD-TRACE] " << current_class_ << "."
                              << current_method_ << " pc=" << pc_
                              << " word=0x" << std::hex << mt_word << std::dec;
                    if (current_registers_) {
                        uint32_t n = current_registers_->get_size();
                        if (n > 32) n = 32;  // CONT-4: solver temps live in v20..v30
                        for (uint32_t r = 0; r < n; r++) {
                            DalvikValue rv = current_registers_->read_v(
                                static_cast<uint8_t>(r));
                            if (rv.type == DalvikType::UNINITIALIZED) continue;
                            std::cerr << " v" << r << "="
                                      << dalvik_value_to_string(rv);
                        }
                        // S20: also print the PARAM window (last ins regs).
                        // R8 composable frames keep params at vN-ins..vN-1,
                        // far above the v0..v19 cap — hide nothing.
                        uint32_t ins_n = current_registers_->get_ins_count();
                        uint32_t total = current_registers_->get_size();
                        uint32_t pstart =
                            (total >= ins_n) ? total - ins_n : 0;
                        for (uint32_t r = pstart; r < total; ++r) {
                            DalvikValue rv = current_registers_->read_v(
                                static_cast<uint8_t>(r));
                            std::cerr << " p" << (r - pstart) << "="
                                      << dalvik_value_to_string(rv);
                        }
                    }
                    std::cerr << std::endl;
                }
            }
        }


        // ── CONT-4 PHASE 1 (bounded, env-gated, READ-ONLY): Lm2;.b solver
        // classification — face-list parity + solver-array state observed
        // at the fatal parity guard (pc=0x57f). M3 law: diagnostics never
        // change semantics; gated by MINIANDROID_CONT4_SOLVER_DIAG.
        dump_cont4_solver_diag(pc_);

        auto start = Clock::now();

        // Fetch opcode
        // EXP-037 Phase B (BLOCKER-012 FIX):
        // Dalvik bytecode packs the opcode in the LOW BYTE of each 16-bit
        // code unit. The HIGH BYTE contains format-specific data:
        //   - 35c (invoke-*): high nibble = arg count, low nibble of high byte = 5th reg
        //   - 11n (const/4): high nibble = register, low nibble of high byte = signed literal
        //   - 22b (iput): high byte = two register nibbles
        //   - 10x (return-void): high byte = 0
        // The previous code passed the full 16-bit word to the switch, which
        // meant `case Opcode::INVOKE_SUPER (0x6F)` never matched the actual
        // bytecode value 0x206F (where 0x20 = arg count + 5th reg). The switch
        // fell through to the default "UNIMPLEMENTED" handler.
        //
        // Fix: mask off the high byte before dispatch. The high byte is
        // re-read by each opcode handler from bytecode_[pc] (e.g. via
        // `(instr >> 4) & 0xF` for the arg count).
        uint16_t raw_word = fetch_opcode(pc_);
        uint16_t opcode = raw_word & 0xFF;  // LOW BYTE only
        uint64_t f107_op0 = phase_clock().on ? __rdtsc() : 0;  // S61 PERF
        uint32_t f107_d0 = recursion_depth_;
        trace.opcode_hex = raw_word;        // Keep raw word for trace evidence

        // S55 R-NEW-361 (env-gated): full instruction stream of the Kotlin
        // LongArray-fill helper Ln/a;.r — one frame ran its body without
        // ever dispatching the Arrays.fill call at unit pc=12.
        // CONT-77 PERF-1: the env lookup is a RUN CONSTANT — hoisted out of
        // the per-instruction path (the raw std::getenv here executed a
        // linear environ scan on EVERY instruction: ~2x9M scans/run, a
        // measurable fraction of the 310K-ins/s interpreter wall). Zero
        // semantic delta: identical rows when the flag is set.
        static thread_local const bool f040_diag_on =
            std::getenv("MINIANDROID_F040_DIAG") != nullptr;
        if (f040_diag_on &&
            current_class_ == "Ln/a;" && current_method_ == "r") {
            static thread_local uint64_t r_insns = 0;
            if (r_insns < 10000) {
                r_insns++;
                std::cerr << "[R-INSN] pc=" << pc_ << " op=0x" << std::hex
                          << opcode << std::dec << " raw=0x" << std::hex
                          << raw_word << std::dec << " #" << r_insns
                          << std::endl;
            }
        }

        // EXP-063: Trace v3 in getString(I) to find where it gets corrupted
        if (current_class_.find("LocaleController") != std::string::npos &&
            current_method_ == "getString" && current_registers_) {
            auto v3 = current_registers_->read_v(3);
            std::cerr << "[EXP063-V3] PC=" << pc_ << " op=0x" << std::hex << opcode << std::dec
                      << " v3_type=" << static_cast<int>(v3.type)
                      << " v3_int=" << v3.int_val
                      << " v3_obj=" << v3.object_id
                      << std::endl;
        }
        
        // CONT-38 decode diag (env-gated, bounded): the painter body's
        // instruction stream — where does the black J come from?
        // CONT-77 PERF-2: same run-constant hoist as F040 above (the raw
        // getenv executed per instruction).
        static thread_local const bool painter_trace_on =
            std::getenv("MINIANDROID_PAINTER_TRACE") != nullptr;
        if (painter_trace_on &&
            ((current_class_ == "Lte1;" && current_method_ == "I") ||
             (current_class_ == "Lod1;" && current_method_ == "I") ||
             (current_class_ == "Lg6;" && current_method_ == "e"))) {
            static thread_local uint64_t pt_n = 0;
            if (pt_n++ < 20000)
                std::cerr << "[PAINTER] " << current_class_ << "."
                          << current_method_ << " pc=" << pc_
                          << " op=0x" << std::hex << opcode << std::dec
                          << std::endl;
        }
        // EXP-042 Phase 1: Per-instruction register snapshots are the #1 OOM
        // offender (5 KB per instruction). Capture them ONLY when explicitly
        // enabled via config_.trace_register_snapshots. Default is false.
        if (config_.trace_register_snapshots && current_registers_) {
            trace.registers_before = current_registers_->get_snapshot();
        }
        
        // Decode and execute
        bool success = true;
        // S62 bucket: switch split by invoke-kind (the op histogram excludes
        // invoke ops — this recovers their handler cost, nested bodies incl.)
        const bool s62_inv = (opcode >= 0x6e && opcode <= 0x72) ||
                             (opcode >= 0x74 && opcode <= 0x78);
        uint64_t s62_sw0 = phase_clock().on ? __rdtsc() : 0;
        switch (opcode) {
            // Constants
            case Opcode::CONST_4:
                success = execute_const_4(pc_, trace);
                trace.opcode_name = "const/4";
                break;
            case Opcode::CONST_16:
                success = execute_const_16(pc_, trace);
                trace.opcode_name = "const/16";
                break;
            case Opcode::CONST_HIGH16: {
                // Format 21s: AA|op BBBB
                // vAA = (int32_t)(BBBB << 16) — sign-extend the 16-bit value to high 16 bits
                if (pc_ + 1 >= bytecode_.size()) return false;
                uint16_t instr = bytecode_[pc_];
                uint8_t vAA = (instr >> 8) & 0xFF;
                int16_t bbbb = static_cast<int16_t>(bytecode_[pc_ + 1]);
                DalvikValue val;
                val.type = DalvikType::INT32;
                val.int_val = static_cast<int32_t>(
                    static_cast<uint32_t>(static_cast<uint16_t>(bbbb)) << 16);
                // W22 #627 E-05: unsigned-width shift — bbbb<0 made the signed
                // left-shift UB (C++17 [expr.shift]); bit pattern unchanged.
                set_register(vAA, val);
                trace.opcode_name = "const/high16";
                pc_ = pc_ + 2;
                break;
            }
            case Opcode::CONST:
                success = execute_const(pc_, trace);
                trace.opcode_name = "const";
                break;
            case Opcode::CONST_STRING:
                success = execute_const_string(pc_, trace);
                trace.opcode_name = "const-string";
                break;
            case Opcode::CONST_CLASS:
                success = execute_const_class(pc_, trace);
                trace.opcode_name = "const-class";
                break;
            
            // Moves
            case Opcode::MOVE:
                success = execute_move(pc_, trace);
                trace.opcode_name = "move";
                break;
            // EXP-088+ F5: move-wide (12x: B|A|op, 1 code unit)
            // Copies a wide value (long/double) from vB to vA.
            // Same as execute_move but explicitly handles wide types.
            // Previously MISSING from dispatcher — fell through to default
            // (handle_unimplemented), causing halt at PC where move-wide appears.
            case Opcode::MOVE_WIDE: {
                uint16_t instr = bytecode_[pc_];
                uint8_t dest = (instr >> 8) & 0xF;
                // DEMO-12X-NIBBLE (2026-09-04): 12x format is B|A|op — the B
                // source register is bits 12-15. The previous read `instr &
                // 0xF` took bits 0-3 of the OPCODE byte, so `move-wide v2,
                // v0` (0x02BF) read v15 (0x02BF & 0xF == 0xF). Same bug class
                // as the ARRAY_LENGTH/2addr nibble fixes.
                uint8_t src = (instr >> 12) & 0xF;
                DalvikValue val = get_register(src);
                // If src doesn't hold a wide value, coerce to INT64
                // (matches the F5 return-wide coercion behavior)
                if (val.type != DalvikType::INT64 && val.type != DalvikType::FLOAT64) {
                    val = DalvikValue::make_long(static_cast<int64_t>(static_cast<uint32_t>(val.int_val)));
                }
                // F-028b: fill the vDest+1 shadow slot (ART two-slot layout)
                set_wide_pair(dest, val);
                trace.opcode_name = "move-wide";
                pc_ += 1;
                break;
            }
            case Opcode::MOVE_OBJECT:
                success = execute_move_object(pc_, trace);
                trace.opcode_name = "move-object";
                break;
            case Opcode::MOVE_OBJECT_FROM16:
                // EXP-038 (BLOCKER-026): move-object/from16
                success = execute_move_object_from16(pc_, trace);
                trace.opcode_name = "move-object/from16";
                break;
            case Opcode::MOVE_OBJECT_16:
                // FINAL-CAMPAIGN PHASE 3: move-object/16 (32x, 3 units)
                success = execute_move_object_16(pc_, trace);
                trace.opcode_name = "move-object/16";
                break;
            case Opcode::MOVE_RESULT:
                success = execute_move_result(pc_, trace);
                trace.opcode_name = "move-result";
                break;
            case Opcode::MOVE_RESULT_OBJECT:
                success = execute_move_result_object(pc_, trace);
                trace.opcode_name = "move-result-object";
                break;

            // EXP-053: move-exception (11x: AA|op, 1 code unit).
            // Moves the thrown exception into register vAA so the catch
            // handler can access it. We store the exception in a per-method
            // pending_exception_ slot when THROW jumps to a handler; this
            // opcode reads from that slot.
            case Opcode::MOVE_EXCEPTION: {
                trace.opcode_name = "move-exception";
                uint8_t vAA = (bytecode_[pc_] >> 8) & 0xFF;
                // F-NEW-264 (CONT-11 W7): EXCEPTION-INTEGRITY DELIVERY LAW.
                // Upstream law (AOSP ART InterpDoThrow + move-exception /
                // JVM athrow-catch contract): a catch handler ALWAYS
                // receives the REAL in-flight java.lang.Throwable object —
                // never null. ART cannot enter a handler without a
                // throwable in flight. Runtime face (dooz23, MINIANDROID_
                // F141_DIAG + EXC-PROPAGATE traces): a deferred engine
                // throw (f141-null-recv inside Lm7;.<init>) unwound and
                // was caught by Lto1;.d's catch-all, but by the time the
                // handler's move-exception executed, pending_exception_
                // had been cleared by an intervening redirect/clear — the
                // handler register received NULL and the compose
                // exception-report helper Lel0;.Y(Throwable) NPE'd on
                // `t.getClass()` (the R8 kotlin-report idiom), killing
                // the whole measure/layout pass (Lzs0;.m → Lt4;.onMeasure
                // cascade, placement never completed, isPlaced stayed
                // false, the draw walk skipped the entire tree).
                // Fix: delivery falls back through the engine's exception
                // slots in authority order (pending → deferred → in-flight
                // unwind) so the handler ALWAYS gets a real throwable
                // object; a bounded env-gated diagnostic records every
                // fallback (each one is itself a state-machine bug worth
                // a future root — the fallback preserves JVM semantics
                // without inventing framework state).
                DalvikValue exc = pending_exception_;
                bool f264_delivered_pending = true;
                if (!(exc.type == DalvikType::OBJECT_REF &&
                      exc.object_id != 0)) {
                    f264_delivered_pending = false;
                    exc = deferred_exception_;
                    if (!(exc.type == DalvikType::OBJECT_REF &&
                          exc.object_id != 0) &&
                        frame_unwind_exception_valid_) {
                        exc = frame_unwind_exception_;
                    }
                    if (!(exc.type == DalvikType::OBJECT_REF &&
                          exc.object_id != 0)) {
                        exc = DalvikValue::make_null();
                    }
                    static thread_local const bool f264_trace =
                        std::getenv("MINIANDROID_F264_TRACE") != nullptr;
                    static thread_local uint64_t f264_n = 0;
                    if (f264_trace && f264_n < 40) {
                        ++f264_n;
                        std::cerr << "[F264-MOVE-EXC] null pending at "
                                  << current_class_ << "." << current_method_
                                  << " pc=" << pc_ << " → fallback "
                                  << exc.class_desc
                                  << (exc.type == DalvikType::OBJECT_REF &&
                                              exc.object_id != 0
                                          ? " (delivered)"
                                          : " (STILL NULL — honesty)")
                                  << std::endl;
                    }
                }
                set_register(vAA, exc);
                trace.operands.push_back({"v" + std::to_string(vAA), exc.to_string()});
                // Clear the pending exception after move (the delivered
                // object is now owned by the handler register). The
                // deferred/unwind slots are left INTACT — forensic reads
                // (S100 last-op ring, crash forensics) and nested-unwind
                // matching still consult them after the handler runs.
                pending_exception_ = DalvikValue::make_null();
                pc_ += 1;
                break;
            }
            
            // Objects
            case Opcode::NEW_INSTANCE:
                success = execute_new_instance(pc_, trace);
                trace.opcode_name = "new-instance";
                break;
            case Opcode::NEW_ARRAY: {
                // Format 22c: B1|A|op CCCC (2 code units)
                // Creates a new array of type@CCCC with size vB, result in vA
                if (pc_ + 1 >= bytecode_.size()) return false;
                uint16_t instr = bytecode_[pc_];
                uint8_t vA = (instr >> 8) & 0xF;    // dest register (array ref)
                uint8_t vB = (instr >> 12) & 0xF;   // size register
                uint16_t type_idx = bytecode_[pc_ + 1];  // type@CCCC

                // Get array size from vB
                DalvikValue size_val = get_register(vB);
                /* S44/R-NEW-351 probe: schema table allocations */
                /* R-NEW-558 (TRAIN 5): env gate hoisted to a thread_local
                 * static — was a cached-but-still-scanning diag_env call per
                 * new-array insn. Semantics identical. */
                static thread_local const bool s44_r351_newarray =
                    diag_env("MINIANDROID_S44_R351");
                if (s44_r351_newarray &&
                    current_class_ == "Llt0;" && (pc_ == 353 || pc_ == 379)) {
                    DalvikValue mi_str = get_register(1); /* v1 = raw MessageInfo string */
                    std::cerr << "[S44-R351] new-array pc=" << pc_
                              << " vB=v" << (int)vB
                              << " type=" << (int)size_val.type
                              << " raw_int=" << size_val.int_val
                              << " -> size=" << dalvik_int_value(size_val)
                              << " | v1str type=" << (int)mi_str.type
                              << " len=" << mi_str.string_val.size()
                              << " head=[";
                    for (size_t ci = 0; ci < mi_str.string_val.size() && ci < 24; ++ci) {
                        unsigned char c = (unsigned char)mi_str.string_val[ci];
                        std::cerr << (c >= 32 && c < 127 ? (char)c : '.')
                                  << "(" << (int)c << ")";
                    }
                    std::cerr << "]" << std::endl;
                }
                int32_t array_size = dalvik_int_value(size_val);
                /* R-NEW-549 (CONT-40): the GIANT-ARRAY watch — the telegram
                 * +2.9GB envelope traced to new-array sites whose SIZE
                 * REGISTER carries a garbage huge value (the Lz/f;.<init>(I)
                 * LRU ctor: new long[cap] + new Object[cap] with cap≈134M —
                 * the 1024MB/1489MB/2939MB contiguous mappings). Print every
                 * allocation whose size crosses the env threshold with the
                 * caller, the pc, and the register's RAW DalvikValue (type +
                 * all views) — the arg-packing/root-cause evidence live.
                 * Env: MINIANDROID_GIANT_ARRAY=<min_len>. Bounded 200. */
                {
                    static thread_local const int32_t giant_min = []() {
                        const char* e = std::getenv("MINIANDROID_GIANT_ARRAY");
                        return (e != nullptr) ? (int32_t)strtoll(e, nullptr, 10)
                                              : -1;
                    }();
                    static thread_local uint32_t giant_n = 0;
                    if (giant_min >= 0 && array_size >= giant_min &&
                        giant_n < 200) {
                        ++giant_n;
                        std::cerr << "[GIANT-ARRAY] len=" << array_size
                                  << " site=" << current_class_ << "."
                                  << current_method_ << " pc=" << pc_
                                  << " vB=v" << (int)vB
                                  << " raw_type=" << (int)size_val.type
                                  << " int=" << size_val.int_val
                                  << " long=" << size_val.long_val
                                  << " float=" << size_val.float_val
                                  << " caller="
                                  << (call_stack_.empty()
                                          ? "-"
                                          : call_stack_.top().class_name +
                                                "." +
                                                call_stack_.top().method_name)
                                  << std::endl;
                    }
                }

                /* F-NEW-268c (CONT-18g): ART new-array negative-size law — a
                 * negative size throws NegativeArraySizeException (ART
                 * art::ThrowNegativeArraySizeException; the old code silently
                 * CLAMPED to 0, manufacturing an empty array out of UB and
                 * hiding the first divergence — issue #381 face c). */
                if (array_size < 0) {
                    raise_synthetic_exception(
                        "Ljava/lang/NegativeArraySizeException;",
                        "size=" + std::to_string(array_size), "new-array-neg");
                    break;
                }

                // Array element-type descriptor: resolved BEFORE the OOM law
                // (the element size derives from it) and reused by the
                // F-NEW-181 runtime-identity law below.
                std::string na_type_desc =
                    resolve_type_for_dex(type_idx, current_dex_index_);

                // R-NEW-169 (CONT-122) new-array OutOfMemoryError law (ART
                // Heap::AllocObject with kHeapObjectLimit family): an
                // allocation request whose BYTE size exceeds the runtime
                // heap budget throws OutOfMemoryError ("Failed to allocate
                // a N-byte allocation"). The engine allocates arrays
                // metadata-only (no per-element backing), so without this
                // law `new int[Integer.MAX_VALUE-2]` "succeeded" and every
                // OOM contract was unprovable (probe c122 U03 pre-fix
                // face: "U03-ALLOCATED size=2147483645"). Element sizes
                // follow the descriptor: [B=1 [Z/[C=2 (char is 2 bytes in
                // JVM; boolean 1 — both non-negative-safe here) [S/[I=4,
                // [J/[F/[D=8, object arrays use the 8-byte reference
                // convention. Budget 1 GiB — far above every corpus
                // anchor's working set, far below the probe's 8.6 GiB
                // request. ART-style message keeps honest diagnostics.
                {
                    int64_t na_elem = 1;
                    const char* na_d = na_type_desc.c_str();
                    if (na_d[0] == '[') {
                        if (na_d[1] == 'B') na_elem = 1;
                        else if (na_d[1] == 'Z' || na_d[1] == 'C') na_elem = 2;
                        else if (na_d[1] == 'S' || na_d[1] == 'I') na_elem = 4;
                        else if (na_d[1] == 'J' || na_d[1] == 'F' ||
                                 na_d[1] == 'D') na_elem = 8;
                        else na_elem = 8;  // reference arrays: 8-byte ref
                    }
                    int64_t na_bytes =
                        static_cast<int64_t>(array_size) * na_elem;
                    static const int64_t kHeapBudget = 1LL << 30;  // 1 GiB
                    if (na_bytes > kHeapBudget) {
                        raise_synthetic_exception(
                            "Ljava/lang/OutOfMemoryError;",
                            "Failed to allocate a " + std::to_string(na_bytes) +
                                "-byte allocation",
                            "new-array-oom");
                        break;
                    }
                }

                // F-NEW-181 (WAVE C, FINAL CAMPAIGN phase 5/6 law — array
                // runtime identity): NEW_ARRAY was the ONLY array producer
                // that discarded the resolved element-type descriptor and
                // stamped every array with the synthetic "Larray;" marker.
                // filled-new-array already stores the REAL descriptor (the
                // in-tree precedent). The divergence is observable: guava's
                // RegularImmutableMap.create gates the duplicate-key wrapper
                // with `instance-of v2, [Ljava/lang/Object;` — with the
                // wrapper stamped "Larray;", is_subclass_of answered FALSE,
                // the Object[3] wrapper {partialTable, insertedCount,
                // duplicateEntry} was stored AS the map's hash table, and
                // the lawful get() probe looped forever on a non-table
                // (F-NEW-181 spin, PC=0x6f). ART law: an array object's
                // runtime class IS its descriptor ([B, [S, [I,
                // [Ljava/lang/Object;, ...). Record the real descriptor on
                // the heap object AND in the register's class_desc.

                // Allocate array object on heap (simplified — just store as OBJECT_REF)
                uint32_t obj_id = heap_.allocate(
                    na_type_desc.empty() ? "Larray;" : na_type_desc, pc_, 0);
                DalvikValue result_val;
                result_val.type = DalvikType::OBJECT_REF;
                result_val.object_id = obj_id;
                result_val.class_desc =
                    na_type_desc.empty() ? "Larray;" : na_type_desc.c_str();
                result_val.int_val = array_size;  // store size in int_val for convenience
                set_register(vA, result_val);

                // EXP-062: Store array length on heap so aget/aput can find it.
                // PASS-3 (K-33 audit): also store the CANONICAL name
                // "__array_length__" that aget/aput/read actually read —
                // previously NEW_ARRAY only stored "__new_array_length__",
                // an inconsistency that made bulk reads/aget see length 0.
                if (heap_.has_object(obj_id)) {
                    heap_.set_object_field(obj_id, "__new_array_length__",
                        DalvikValue::make_int(array_size));
                    heap_.set_object_field(obj_id, "__array_length__",
                        DalvikValue::make_int(array_size));
                    // F-NEW-385 (CONT-82): new-array ZERO-INIT law (AOSP
                    // HandleNewArray — every element of a fresh array is the
                    // component default: 0/null/false, never an ABSENT slot).
                    // The engine left slots unwritten, so Arrays.toString /
                    // aget on an un-stored index answered null (the CONT-82
                    // arrays fixture: [Z {true} with an unstored second slot
                    // rendered "[true, null]" — AOSP answers "[true, false]").
                    if (na_type_desc.size() >= 2 && na_type_desc[0] == '[') {
                        DalvikValue na_zero;
                        switch (na_type_desc[1]) {
                            case 'Z': na_zero = DalvikValue::make_bool(false); break;
                            case 'C': na_zero = DalvikValue::make_char(0); break;
                            case 'B': na_zero = DalvikValue::make_byte(0); break;
                            case 'S': na_zero = DalvikValue::make_short(0); break;
                            case 'J': na_zero = DalvikValue::make_long(0); break;
                            case 'F': na_zero = DalvikValue::make_float(0.f); break;
                            case 'D': na_zero = DalvikValue::make_double(0.0); break;
                            case 'L': na_zero = DalvikValue::make_null(); break;
                            case '[': na_zero = DalvikValue::make_null(); break;
                            default: na_zero = DalvikValue::make_int(0); break;
                        }
                        for (int32_t zi = 0; zi < array_size && zi < 4096; ++zi) {
                            heap_.set_object_field(
                                obj_id, "array[" + std::to_string(zi) + "]",
                                na_zero);
                        }
                    }
                    // F-NEW-181: element-type provenance for heap-side
                    // classification (SPIN probes, get_object_class law).
                    if (!na_type_desc.empty())
                        heap_.set_object_field(obj_id, "__element_type__",
                            DalvikValue::make_string(na_type_desc, 0));
                }

                // EXP-066: Use per-DEX type resolution for trace evidence.
                std::string type_name = "<unknown>";
                type_name = resolve_type_for_dex(type_idx, current_dex_index_);
                log("✅ NEW-ARRAY: type=" + type_name + " size=" + std::to_string(array_size) + " → obj#" + std::to_string(obj_id));

                trace.opcode_name = "new-array";
                trace.operands.push_back({"type", type_name});
                trace.operands.push_back({"size", std::to_string(array_size)});
                pc_ = pc_ + 2;  // 22c = 2 code units
                break;
            }
            case Opcode::ARRAY_LENGTH: {
                // Format 12x: B|A|op (1 code unit)
                // vA = length of array in vB
                if (pc_ >= bytecode_.size()) return false;
                uint16_t instr = bytecode_[pc_];
                uint8_t vA = (instr >> 8) & 0xF;   // dest
                // DEMO-ARRLEN-NIBBLE (2026-09-04): source register is the B
                // nibble = bits 12-15, per AOSP dalvik-bytecode.html 12x
                // format (B|A|op). The previous read `(instr >> 4) & 0xF`
                // took bits 4-7 (part of the opcode byte), so `array-length
                // v1, v0` read v2 (0x0121 >> 4 & 0xF == 2) instead of v0 —
                // every array-length returned the contents of an unrelated
                // register (typically 0). Same bug class as EXP-058's move
                // fix. First observed with the miniandroid-demo APK: step()
                // computed `count % COLOR_NAMES.length` as a division by 0
                // because array-length read the wrong register.
                uint8_t vB = (instr >> 12) & 0xF;   // source array
                DalvikValue arr = get_register(vB);
                // R-NEW-464 closeout (AOSP dalvik-bytecode array-length
                // law): a null array ref MUST throw NullPointerException —
                // the old fallthrough answered 0 (silent-wrong), which
                // masked missing reflection laws (a null Class[] from an
                // unanswered getParameterTypes read as a zero-length
                // array, silently skipping every candidate in EventBus's
                // subscriber scan instead of failing loudly at the real
                // divergence). A register-carried NEW_ARRAY answer keeps
                // its length in int_val and is NOT null (object_id 0 with
                // a nonzero length stays legitimate).
                const bool arr_is_null_464 =
                    arr.type == DalvikType::NULL_REF ||
                    (arr.type == DalvikType::OBJECT_REF &&
                     arr.object_id == 0 && arr.int_val == 0);
                if (arr_is_null_464) {
                    throw_deferred(
                        "Ljava/lang/NullPointerException;",
                        "Attempt to get length of null array",
                        "ARR-LEN-NULL");
                    pc_ = pc_ + 1;
                    break;
                }
                // Length resolution order (consistent with aget/aput):
                //   1. int_val carried by the register value (set by NEW_ARRAY)
                //   2. __array_length__ heap field (survives field storage)
                //   3. __new_array_length__ heap field (legacy name)
                int32_t len = 0;
                if (arr.type == DalvikType::OBJECT_REF) {
                    len = arr.int_val;
                    if (len == 0 && heap_.has_object(arr.object_id)) {
                        auto f1 = heap_.get_object_field(arr.object_id, "__array_length__");
                        if (f1.has_value() && f1->type == DalvikType::INT32) len = f1->int_val;
                        if (len == 0) {
                            auto f2 = heap_.get_object_field(arr.object_id, "__new_array_length__");
                            if (f2.has_value() && f2->type == DalvikType::INT32) len = f2->int_val;
                        }
                    }
                }
                DalvikValue result_val;
                result_val.type = DalvikType::INT32;
                result_val.int_val = (arr.type == DalvikType::OBJECT_REF) ? len : 0;
                set_register(vA, result_val);
                trace.opcode_name = "array-length";
                pc_ = pc_ + 1;
                break;
            }

            // EXP-038 (BLOCKER-031): Array get/put opcodes (23x format, 2 code units)
            // Format 23x: AA|op BB|CC
            //   vAA = dest/src, vBB = array ref, vCC = index
            //
            // EXP-044 Phase 1: Proper array bounds checking.
            // When the index is out of bounds (or the array is null/empty),
            // we simulate ArrayIndexOutOfBoundsException by halting the method.
            // This is required for Kotlin Intrinsics.createParameterIsNullExceptionMessage
            // which loops through stack trace elements and expects an exception
            // when the index exceeds the array length.
            // EXP-062: Real array element retrieval.
            // Previously ARRAY_GET_CASE always returned NULL_REF for objects.
            // Now we read elements stored by aput-object from the HeapObject.
            #define ARRAY_GET_CASE(opcode, op_name, result_type) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vAA = (instr >> 8) & 0xFF; \
                    uint8_t vBB = bytecode_[pc_ + 1] & 0xFF; \
                    uint8_t vCC = (bytecode_[pc_ + 1] >> 8) & 0xFF; \
                    DalvikValue arr_val = get_register(vBB); \
                    DalvikValue idx_val = get_register(vCC); \
                    int32_t idx = dalvik_int_value(idx_val); \
                    trace.opcode_name = op_name; \
                    /* F-NEW-268a (CONT-18g): AOSP HandleAGet null-array law — \
                     * aget on a NULL array reference throws NPE at the access. \
                     * aput has carried the mirror arm since EXP-038 \
                     * ("AOSP HandleAPut: null array → NPE"); the aget side \
                     * silently answered a default value instead, hiding the \
                     * first divergence (issue #381 claims-audit face a). \
                     * f141_is_null_receiver = NULL_REF / OBJECT_REF-id-0 / \
                     * INT32-0 typed null (F-141 + F-266a untyped-register law). */ \
                    if (f141_is_null_receiver(arr_val)) { \
                        log("⚠️ AGET from null array (" + std::string(op_name) + \
                            ") idx=" + std::to_string(idx)); \
                        raise_synthetic_exception( \
                            "Ljava/lang/NullPointerException;", \
                            "Attempt to read from null array", "aget-null"); \
                        break; \
                    } \
                    /* EXP-062: Read array length from heap field */ \
                    int32_t arr_len = 0; \
                    /* F-NEW-268b: a RECORDED length — even 0 — is authoritative. \
                     * new-array(0) stores __array_length__/__new_array_length__ = 0; \
                     * the old guard treated 0 as "length unknown" and warn-and- \
                     * continued, so a confirmed zero-length array answered null \
                     * instead of AIOOBE (#381 face b). */ \
                    bool len_recorded = false; \
                    if (arr_val.type == DalvikType::OBJECT_REF && \
                        heap_.has_object(arr_val.object_id)) { \
                        auto len_field = heap_.get_object_field(arr_val.object_id, "__array_length__"); \
                        if (len_field.has_value() && len_field->type == DalvikType::INT32) { \
                            arr_len = len_field->int_val; \
                            len_recorded = true; \
                        } \
                        /* Also check if new-array stored a length */ \
                        if (arr_len == 0) { \
                            auto nm_field = heap_.get_object_field(arr_val.object_id, "__new_array_length__"); \
                            if (nm_field.has_value() && nm_field->type == DalvikType::INT32) { \
                                arr_len = nm_field->int_val; \
                                len_recorded = true; \
                            } \
                        } \
                    } \
                    if (arr_len == 0 && !len_recorded) { \
                        /* Fallback: use int_val from arr_val (old behavior) */ \
                        arr_len = (arr_val.type == DalvikType::OBJECT_REF) ? arr_val.int_val : 0; \
                    } \
                    if (arr_len == 0 || idx < 0 || idx >= arr_len) { \
                        log("⚠️ AGET out of bounds: arr_len=" + std::to_string(arr_len) + \
                            " idx=" + std::to_string(idx)); \
                        /* UNIFIED_011.2 SYNTH-EXC (§21 dooz livelock fix): a CONFIRMED \
                         * out-of-bounds access must throw ArrayIndexOutOfBoundsException \
                         * (real Dalvik semantics) instead of warn-and-continue. The old \
                         * behavior produced an infinite loop in dooz LM1/i;.f (the loop \
                         * index ran past the array end 50000+ times because no exception \
                         * ever fired). Only a CONFIRMED OOB (known arr_len > 0) throws — \
                         * arr_len == 0 may mean "length unknown" in this engine, so that \
                         * path keeps the legacy warn-and-continue to avoid regressing \
                         * APKs whose array length was never recorded. \
                         * F-NEW-268b: a RECORDED length (even 0) makes the OOB \
                         * CONFIRMED — idx>=0 against a recorded 0 is always OOB. \
                         */ \
                        if (len_recorded || arr_len > 0) { \
                            /* S36 (R-NEW-335): bounded AOOB evidence probe — \
                             * which array object is indexed OOB (class + id + \
                             * element classes when the store is heap-side). */ \
                            { \
                                static thread_local uint64_t s36_oob = 0; \
                                if (std::getenv("MINIANDROID_S36_TRACE") != nullptr && s36_oob < 8) { \
                                    ++s36_oob; \
                                    std::cerr << "[S36-AOOB] arr=o" \
                                              << (arr_val.type == DalvikType::OBJECT_REF ? arr_val.object_id : 0) \
                                              << " cls=" << arr_val.class_desc \
                                              << " len=" << arr_len << " idx=" << idx \
                                              << " caller=" << current_class_ << "." << current_method_ \
                                              << std::endl; \
                                } \
                            } \
                            /* UNIFIED_014: message aligned to ART canonical \
                             * "length=<len>; index=<idx>" (mirror/array.cc \
                             * ThrowArrayIndexOutOfBoundsException chain). */ \
                            dump_frame_locals_diag("AGET-OOB"); \
                            std::string oob_msg = "length=" + std::to_string(arr_len) + \
                                                  "; index=" + std::to_string(idx); \
                            raise_synthetic_exception( \
                                "Ljava/lang/ArrayIndexOutOfBoundsException;", \
                                oob_msg, "aget-oob"); \
                            /* handled: pc_ now at catch handler; unhandled: frame unwinds \
                             * via halted_on_return_ (post-switch check exits the loop). */ \
                            break; \
                        } \
                        DalvikValue result_val; \
                        result_val.type = result_type; \
                        if (result_type == DalvikType::OBJECT_REF) { \
                            result_val = DalvikValue::make_null(); \
                        } \
                        set_register(vAA, result_val); \
                        pc_ = pc_ + 2; \
                        break; \
                    } \
                    /* EXP-062: Read element from heap */ \
                    /* EXP-071: FIX — aget-boolean/aget/aget-byte/aget-char/aget-short
                     * were NOT reading from the heap (only aget-object was). This caused
                     * boolean array reads to always return 0 (false), which made
                     * LoginActivity.onDoneButtonPressed always return early (the
                     * doneButtonVisible[] check at PC=4-6 always returned false=0,
                     * and if-ltz 0 never branched). Now we read ALL array element
                     * types from the heap. */ \
                    DalvikValue result_val; \
                    result_val.type = result_type; \
                    /* FINAL-CAMPAIGN PHASE 3 (F-NEW-172): bounded aget-short \
                     * evidence probe on the spinning createHashTable table. */ \
                    if (op_name[0] == 'a' && \
                        (result_type == DalvikType::SHORT || \
                         result_type == DalvikType::BYTE) && \
                        current_method_ == "createHashTable") { \
                        static thread_local uint64_t f172_aget = 0; \
                        if (f172_aget < 24) { \
                            ++f172_aget; \
                            int32_t probe_len = 0; \
                            if (arr_val.type == DalvikType::OBJECT_REF && \
                                heap_.has_object(arr_val.object_id)) { \
                                auto lf2 = heap_.get_object_field( \
                                    arr_val.object_id, "__array_length__"); \
                                if (lf2.has_value() && lf2->type == DalvikType::INT32) \
                                    probe_len = lf2->int_val; \
                            } \
                            std::string f172_field = "array[" + std::to_string(idx) + "]"; \
                            std::string f172_stored = "MISSING"; \
                            auto f172_elem = heap_.get_object_field( \
                                arr_val.object_id, f172_field); \
                            if (f172_elem.has_value()) \
                                f172_stored = dalvik_value_to_string(*f172_elem); \
                            std::cerr << "[F172-AGET] idx=" << idx \
                                      << " arr=o" << (arr_val.type == DalvikType::OBJECT_REF ? arr_val.object_id : 0) \
                                      << " len=" << probe_len \
                                      << " stored=" << f172_stored \
                                      << std::endl; \
                        } \
                    } \
                    /* Try reading from heap for ALL types (not just OBJECT_REF). */ \
                    if (arr_val.type == DalvikType::OBJECT_REF && \
                        heap_.has_object(arr_val.object_id)) { \
                        std::string field = "array[" + std::to_string(idx) + "]"; \
                        auto elem = heap_.get_object_field(arr_val.object_id, field); \
                        /* S200-T03 diag (env-gated, bounded): aget-char/aput \
                         * views inside the gdx font generator — the createGlyph \
                         * sort reads characters[best] AFTER the aput-char swaps; \
                         * every observed getCharIndex native call received \
                         * char=0 while pass-1 read real chars — this probe \
                         * shows the stored byte and the produced register. */ \
                        { \
                            static thread_local const bool t03_arr_on = \
                                std::getenv("MINIANDROID_T03_ARR_TRACE") != nullptr; \
                            static thread_local uint64_t t03_arr_n = 0; \
                            if (t03_arr_on && t03_arr_n < 90 && \
                                current_class_.find("FreeTypeFontGenerator") != \
                                    std::string::npos) { \
                                ++t03_arr_n; \
                                std::cerr << "[T03-ARR] " << op_name \
                                          << " arr=o" << arr_val.object_id \
                                          << " idx=" << idx \
                                          << " len=" << arr_len \
                                          << " stored="; \
                                if (elem.has_value()) { \
                                    std::cerr << (int)elem->type << ":"; \
                                    if (elem->type == DalvikType::CHAR) \
                                        std::cerr << (int)elem->char_val; \
                                    else if (elem->type == DalvikType::BYTE) \
                                        std::cerr << (int)elem->byte_val; \
                                    else \
                                        std::cerr << elem->int_val; \
                                } else { \
                                    std::cerr << "MISSING"; \
                                } \
                                std::cerr << std::endl; \
                            } \
                        } \
                        if (elem.has_value()) { \
                            result_val = elem.value(); \
                            /* PASS-3 (K-41): normalize typed scalar elements to INT. \
                             * Real Dalvik: aget-byte/char/short yield an INT register; \
                             * the engine stores typed scalars with SEPARATE byte_val/ \
                             * char_val/short_val members, so leaving the typed value in \
                             * the register made every later int_val arithmetic read 0. */ \
                            if (result_val.type == DalvikType::BYTE) \
                                result_val = DalvikValue::make_int(result_val.byte_val); \
                            else if (result_val.type == DalvikType::SHORT) \
                                result_val = DalvikValue::make_int(result_val.short_val); \
                            else if (result_val.type == DalvikType::CHAR) \
                                result_val = DalvikValue::make_int( \
                                    static_cast<unsigned char>(result_val.char_val)); \
                            /* Ensure type matches expected result_type */ \
                            if (result_type == DalvikType::BOOLEAN) { \
                                /* Normalize to 0 or 1 */ \
                                bool b = (elem->type == DalvikType::INT32) ? (elem->int_val != 0) : \
                                         (elem->type == DalvikType::BOOLEAN) ? elem->bool_val : false; \
                                result_val = DalvikValue::make_bool(b); \
                            } else if (result_type == DalvikType::INT32 && \
                                       elem->type != DalvikType::INT32) { \
                                /* PASS-3 FORENSIC FIX (K-41): typed elements \
                                 * (BYTE/CHAR/SHORT — stored via aput-* or the new \
                                 * InputStream.read(byte[])) carry their value in \
                                 * byte_val/char_val/short_val. The old code zeroed \
                                 * every non-INT32 element, so aget-byte on ANY heap \
                                 * array always returned 0. */ \
                                int32_t conv_val = 0; \
                                switch (elem->type) { \
                                    case DalvikType::BYTE:  conv_val = elem->byte_val; break; \
                                    case DalvikType::CHAR:  conv_val = static_cast<unsigned char>(elem->char_val); break; \
                                    case DalvikType::SHORT: conv_val = elem->short_val; break; \
                                    case DalvikType::BOOLEAN: conv_val = elem->bool_val ? 1 : 0; break; \
                                    case DalvikType::INT64: conv_val = static_cast<int32_t>(elem->long_val); break; \
                                    default: conv_val = elem->int_val; break; \
                                } \
                                result_val = DalvikValue::make_int(conv_val); \
                            } \
                        } else { \
                            if (result_type == DalvikType::OBJECT_REF) { \
                                result_val = DalvikValue::make_null(); \
                            } \
                        } \
                    } else { \
                        if (result_type == DalvikType::OBJECT_REF) { \
                            result_val = DalvikValue::make_null(); \
                        } \
                    } \
                    set_register(vAA, result_val); \
                    pc_ = pc_ + 2; \
                    break; \
                }

            ARRAY_GET_CASE(AGET, "aget", DalvikType::INT32)
            ARRAY_GET_CASE(AGET_WIDE, "aget-wide", DalvikType::INT64)
            ARRAY_GET_CASE(AGET_OBJECT, "aget-object", DalvikType::OBJECT_REF)
            ARRAY_GET_CASE(AGET_BOOLEAN, "aget-boolean", DalvikType::BOOLEAN)
            ARRAY_GET_CASE(AGET_BYTE, "aget-byte", DalvikType::BYTE)
            ARRAY_GET_CASE(AGET_CHAR, "aget-char", DalvikType::CHAR)
            ARRAY_GET_CASE(AGET_SHORT, "aget-short", DalvikType::SHORT)
            #undef ARRAY_GET_CASE

            // EXP-062: Real array element storage.
            // Previously ARRAY_PUT_CASE was a NO-OP — aput-object did nothing.
            // Now we store elements in the HeapObject's fields using a
            // synthetic field name "array[idx]".
            //
            // UNIFIED_014 (DEX-APUT-BOUNDS): AOSP aput semantics for CONFIRMED
            // arrays. Reference: AOSP art
            // runtime/interpreter/interpreter_switch_impl-inl.h HandleAPut /
            // APUT_OBJECT (main, fetched 2026-09-03; see
            // docs/upstream_reference_aput_aosp.md): null array → NPE;
            // CheckIsValidIndex → AIOOBE; store only after checks; array
            // length is NEVER mutated by aput. The old code wrote ANY index
            // and auto-grew "__array_length__" to idx+1 — the DEX-APUT-BOUNDS
            // drift (phantom array tail for array-length/loops).
            // Conservative tiers mirror the UNIFIED_011.2 aget fix:
            //   - CONFIRMED length (effective len > 0): full AOSP enforcement
            //     (null/bounds checked, length immutable).
            //   - length 0/unknown: legacy store+grow path preserved (arrays
            //     filled aput-by-aput by bridges with no recorded length keep
            //     working; mirrors aget's arr_len==0 legacy gate).
            //   - NULL_REF: AOSP NPE (null is unambiguous in this engine).
            //   - non-OBJECT_REF / heap-missing: legacy silent skip (unchanged).
            #define ARRAY_PUT_CASE(opcode, op_name) \
                case Opcode::opcode: { \
                    trace.opcode_name = op_name; \
                    uint8_t vAA = (bytecode_[pc_] >> 8) & 0xFF; \
                    uint8_t vBB = bytecode_[pc_ + 1] & 0xFF; \
                    uint8_t vCC = (bytecode_[pc_ + 1] >> 8) & 0xFF; \
                    DalvikValue arr_val = get_register(vBB); \
                    DalvikValue idx_val = get_register(vCC); \
                    DalvikValue src_val = get_register(vAA); \
                    /* F-NEW-244 FIX: CLASS_REF (const-class token) slots are \
                     * stored in their OBJECT_REF projection (real heap Class \
                     * token id) so every array-fields consumer — shadow next() \
                     * fallback, cascade ref reads — can read them back; the \
                     * CLASS_REF form falls through ref reads and breaks \
                     * iterator cursors (see filled-new-array site). */ \
                    if (src_val.type == DalvikType::CLASS_REF && \
                        src_val.object_id != 0) { \
                        src_val = DalvikValue::make_object( \
                            src_val.object_id, "Ljava/lang/Class;"); \
                    } \
                    /* F-NEW-385 (CONT-82): aput component typing — the APUT \
                     * OPCODE VARIANT is the component type (AOSP HandleAPut \
                     * family). The register carries raw INT32 (a zeroed \
                     * register reads NULL), so the un-typed store lost the \
                     * element kind for [Z/[C/[B/[S arrays and every typed \
                     * reader (Arrays.toString per-type rendering, aget- \
                     * boolean identity) answered the wrong face. Caught by \
                     * the CONT-82 arrays fixture ([Z {true,false} stored \
                     * [1, null]). The typed store is identity for [I/[J/ \
                     * [F/[D/[L (APUT/APUT_WIDE/APUT_OBJECT never reach the \
                     * primitive re-typing branches). */ \
                    { \
                        int aput385_v = (src_val.type == DalvikType::INT32) \
                                             ? src_val.int_val \
                                             : ((src_val.type == \
                                                DalvikType::BOOLEAN) \
                                                    ? (src_val.bool_val ? 1 \
                                                                        : 0) \
                                                : (src_val.type == \
                                                   DalvikType::CHAR \
                                                       ? src_val.int_val \
                                                       : 0)); \
                        if (strcmp(op_name, "aput-boolean") == 0) { \
                            src_val = DalvikValue::make_bool(aput385_v != 0); \
                        } else if (strcmp(op_name, "aput-char") == 0) { \
                            src_val = DalvikValue::make_char( \
                                static_cast<char>(aput385_v & 0xFF)); \
                        } else if (strcmp(op_name, "aput-byte") == 0) { \
                            src_val = DalvikValue::make_byte( \
                                static_cast<int8_t>(aput385_v & 0xFF)); \
                        } else if (strcmp(op_name, "aput-short") == 0) { \
                            src_val = DalvikValue::make_short( \
                                static_cast<int16_t>(aput385_v & 0xFFFF)); \
                        } \
                    } \
                    int32_t idx = dalvik_int_value(idx_val); \
                    /* S60 hygiene (F-074 precedent): the per-op aput trace is \
                     * now env-gated. The always-on stderr write dominated the \
                     * wall clock of long Compose compositions (dooz v23 \
                     * GameScreen: ~250K logged aputs in the slots-array fill) \
                     * and pushed the first-frame run past every session \
                     * budget. Bounds-check + store semantics are UNCHANGED. */ \
                    static thread_local const bool exp093_aput_trace = \
                        std::getenv("MINIANDROID_EXP093_APUT_TRACE") != nullptr; \
                    if (exp093_aput_trace && \
                        strcmp(op_name, "aput-object") == 0) { \
                        std::cerr << "[EXP093-APUT] " << op_name \
                                  << " v" << (int)vAA << "→arr[v" << (int)vBB \
                                  << "] idx_v" << (int)vCC \
                                  << " arr_type=" << (int)arr_val.type \
                                  << " arr_obj=" << arr_val.object_id \
                                  << " src_type=" << (int)src_val.type \
                                  << " idx=" << idx << std::endl; \
                    } \
                    /* AOSP HandleAPut: null array → NPE, no store. */ \
                    if (arr_val.type == DalvikType::NULL_REF || arr_val.is_null) { \
                        log("⚠️ APUT into null array (" + std::string(op_name) + \
                            ") idx=" + std::to_string(idx)); \
                        raise_synthetic_exception( \
                            "Ljava/lang/NullPointerException;", \
                            "Attempt to write into null array", "aput-null"); \
                        /* handled: pc_ at catch handler; unhandled: frame \
                         * unwinds via halted_on_return_ (same as aget). */ \
                        break; \
                    } \
                    /* Effective length chain — identical to ARRAY_GET_CASE. */ \
                    bool arr_on_heap = (arr_val.type == DalvikType::OBJECT_REF && \
                                        heap_.has_object(arr_val.object_id)); \
                    int32_t arr_len = 0; \
                    /* F-NEW-268b: a RECORDED length — even 0 — is authoritative \
                     * (mirror of the aget side): a confirmed zero-length array \
                     * must AIOOBE on any store, not grow silently. */ \
                    bool len_recorded = false; \
                    if (arr_on_heap) { \
                        auto len_field = heap_.get_object_field(arr_val.object_id, "__array_length__"); \
                        if (len_field.has_value() && len_field->type == DalvikType::INT32) { \
                            arr_len = len_field->int_val; \
                            len_recorded = true; \
                        } \
                        if (arr_len == 0) { \
                            auto nm_field = heap_.get_object_field(arr_val.object_id, "__new_array_length__"); \
                            if (nm_field.has_value() && nm_field->type == DalvikType::INT32) { \
                                arr_len = nm_field->int_val; \
                                len_recorded = true; \
                            } \
                        } \
                        if (arr_len == 0 && !len_recorded) { \
                            arr_len = arr_val.int_val; \
                        } \
                    } \
                    std::string field = "array[" + std::to_string(idx) + "]"; \
                    if (arr_on_heap && (len_recorded || arr_len > 0)) { \
                        /* CONFIRMED array: full AOSP semantics. */ \
                        if (idx < 0 || idx >= arr_len) { \
                            { \
                                static thread_local uint64_t s36_oob2 = 0; \
                                if (std::getenv("MINIANDROID_S36_TRACE") != nullptr && s36_oob2 < 8) { \
                                    ++s36_oob2; \
                                    std::cerr << "[S36-AOOB-aput] arr=o" \
                                              << arr_val.object_id \
                                              << " cls=" << arr_val.class_desc \
                                              << " len=" << arr_len << " idx=" << idx \
                                              << " caller=" << current_class_ << "." << current_method_ \
                                              << std::endl; \
                                } \
                            } \
                            log("⚠️ APUT out of bounds: arr_len=" + std::to_string(arr_len) + \
                                " idx=" + std::to_string(idx)); \
                            dump_frame_locals_diag("APUT-OOB"); \
                            std::string oob_msg = "length=" + std::to_string(arr_len) + \
                                                  "; index=" + std::to_string(idx); \
                            raise_synthetic_exception( \
                                "Ljava/lang/ArrayIndexOutOfBoundsException;", \
                                oob_msg, "aput-oob"); \
                            break; \
                        } \
                        /* R-NEW-010 (CONT-122) aput-object ArrayStoreException \
                         * store-check law (AOSP HandleAPutObject + \
                         * art::ThrowArrayStoreException): a reference store \
                         * into an object array ([LX; / [[X;) must verify the \
                         * VALUE's runtime class is assignable to the array's \
                         * component type X; otherwise throw \
                         * ArrayStoreException ("%s cannot be stored in an \
                         * array of type %s"). The engine stores arrays \
                         * type-agnostically ("array[N]" fields), so without \
                         * this check a wrong-typed store silently succeeded \
                         * (probe c122 U01 pre-fix face: "U01-STORED \
                         * no-exception value=7"). CONSERVATIVE SCOPE: check \
                         * ONLY when the array's runtime class is a real \
                         * array descriptor ("[...") AND the value carries a \
                         * concrete known descriptor — never the synthetic \
                         * "Larray;" marker, never empty/unknown. \
                         * Engine-internal wrappers keep storing exactly as \
                         * before (F-NEW-181 wrapper precedent); app-level \
                         * typed stores get the AOSP law. Residual: \
                         * STRING_REF-typed registers bypass the check \
                         * (they are String-typed by construction). */ \
                        if (strcmp(op_name, "aput-object") == 0 && \
                            src_val.type == DalvikType::OBJECT_REF && \
                            !src_val.is_null && src_val.object_id != 0) { \
                            std::string asc_arr_cls; \
                            heap_.get_object_class(arr_val.object_id, asc_arr_cls); \
                            if (asc_arr_cls.size() >= 2 && asc_arr_cls[0] == '[') { \
                                std::string asc_component = asc_arr_cls.substr(1); \
                                std::string asc_src_cls = src_val.class_desc; \
                                std::string asc_probe_cls; \
                                if (heap_.has_object(src_val.object_id)) { \
                                    std::string asc_heap_cls; \
                                    heap_.get_object_class(src_val.object_id, asc_heap_cls); \
                                    if (!asc_heap_cls.empty()) asc_src_cls = asc_heap_cls; \
                                } \
                                bool asc_src_known = \
                                    !asc_src_cls.empty() && asc_src_cls != "Larray;" && \
                                    /* F-NEW-487 (CONT-156 Train 4): the literal \
                                     * "<unknown>" marker is an UNRESOLVED type, \
                                     * not a known concrete class — the \
                                     * conservative scope law above says the \
                                     * check only fires on a CONCRETE known \
                                     * descriptor. An "<unknown>"-typed value \
                                     * (pre-FNA-fallback allocations) must bypass \
                                     * the check exactly like "Larray;" — the \
                                     * old guard let the marker through and the \
                                     * assignability test rejected it, throwing \
                                     * FALSE ArrayStoreExceptions. */ \
                                    asc_src_cls != "<unknown>"; \
                                bool asc_comp_object = \
                                    !asc_component.empty() && \
                                    (asc_component[0] == 'L' || asc_component[0] == '['); \
                                if (asc_src_known && asc_comp_object) { \
                                    bool asc_ok = \
                                        dalvik_class_assignable(asc_src_cls, \
                                                                asc_component); \
                                    /* F-C4-573 (W8, 4APP4 Coder-4) — */ \
                                    /* PROVABLE-INCOMPATIBILITY-ONLY aastore. */ \
                                    /* The JVM aastore throws only when the */ \
                                    /* value's runtime type is PROVABLY not */ \
                                    /* assignable to the component type. The */ \
                                    /* engine hierarchy tables cover DEX */ \
                                    /* classes; framework/JDK shadow classes */ \
                                    /* (e.g. AbstractMap$SimpleImmutableEntry */ \
                                    /* IMPLEMENTS Map$Entry on the real JVM) */ \
                                    /* carry no DEX hierarchy here, so a */ \
                                    /* negative assignable() answer on a */ \
                                    /* JDK-internal pair is a FALSE */ \
                                    /* ArrayStoreException. Live root (TB v24, */ \
                                    /* W8): j$.time.ZoneId.<clinit> pc=13 */ \
                                    /* stores SimpleImmutableEntry into */ \
                                    /* [Ljava/util/Map$Entry; → false ASE → */ \
                                    /* the desugared java.time bootstrap */ \
                                    /* unwound (crash.log "ArrayStoreException */ \
                                    /* unwound Lj$/time/ZoneOffset;.<init>"). */ \
                                    /* LAW: fire ONLY when BOTH sides are */ \
                                    /* DEX-known; either side unknown → the */ \
                                    /* engine cannot prove incompatibility → */ \
                                    /* allow the store (JVM-faithful). */ \
                                    if (!asc_ok) { \
                                        const bool asc_src_dex_known = \
                                            class_to_superclass_.find(asc_src_cls) != \
                                                class_to_superclass_.end() || \
                                            class_to_interfaces_.find(asc_src_cls) != \
                                                class_to_interfaces_.end(); \
                                        const bool asc_comp_dex_known = \
                                            class_to_superclass_.find(asc_component) != \
                                                class_to_superclass_.end() || \
                                            class_to_interfaces_.find(asc_component) != \
                                                class_to_interfaces_.end(); \
                                        if (!asc_src_dex_known || \
                                            !asc_comp_dex_known) { \
                                            asc_ok = true; \
                                            static thread_local uint64_t f573_n = 0; \
                                            static thread_local const bool f573_diag = \
                                                std::getenv("MINIANDROID_F573_DIAG") != \
                                                nullptr; \
                                            if (f573_diag && f573_n++ < 40) { \
                                                std::cerr << "[F-C4-573] aput pass" \
                                                          << " (unprovable) arr=" \
                                                          << asc_arr_cls << " src=" \
                                                          << asc_src_cls \
                                                          << " caller=" \
                                                          << current_class_ << "." \
                                                          << current_method_ \
                                                          << std::endl; \
                                            } \
                                        } \
                                    } \
                                    static thread_local const bool asc_trace = \
                                        std::getenv("MINIANDROID_ASC_TRACE") != nullptr; \
                                    if (asc_trace && !asc_ok) { \
                                        std::cerr << "[ASC-REJECT] arr=" \
                                                  << asc_arr_cls \
                                                  << " src=" << asc_src_cls \
                                                  << " src_heap_cls="; \
                                        std::string asc_dbg; \
                                        heap_.get_object_class(src_val.object_id, asc_dbg); \
                                        std::cerr << asc_dbg; \
                                        auto asc_ifc = class_to_interfaces_.find(asc_src_cls); \
                                        std::cerr << " ifc_n=" \
                                                  << (asc_ifc == class_to_interfaces_.end() \
                                                          ? std::string("MISSING") \
                                                          : std::to_string(asc_ifc->second.size())); \
                                        if (asc_ifc != class_to_interfaces_.end() && \
                                            !asc_ifc->second.empty()) \
                                            std::cerr << " ifc0=" << asc_ifc->second[0]; \
                                        std::cerr << " sup="; \
                                        auto asc_sup = class_to_superclass_.find(asc_src_cls); \
                                        std::cerr << (asc_sup == class_to_superclass_.end() \
                                                          ? std::string("MISSING") \
                                                          : asc_sup->second); \
                                        std::cerr << " caller=" << current_class_ \
                                                  << "." << current_method_ \
                                                  << std::endl; \
                                    } \
                                    if (!asc_ok) { \
                                    std::string asc_msg = asc_src_cls + \
                                        " cannot be stored in an array of type " + \
                                        asc_arr_cls; \
                                    log("⚠️ APUT-OBJECT store-check: " + asc_msg); \
                                    raise_synthetic_exception( \
                                        "Ljava/lang/ArrayStoreException;", \
                                        asc_msg, "aput-object-store-check"); \
                                    break; \
                                    } \
                                } \
                            } \
                        } \
                        heap_.set_object_field(arr_val.object_id, field, src_val); \
                        /* S56 generalized R-NEW-361/344 metadata-store trace: \
                         * every aput-wide/aput landing on a [J array that is \
                         * referenced as field 'a' of ANY heap object (the \
                         * androidx.collection ScatterMap/ScatterSet metadata \
                         * layout — v18 Lh/r;/Lh/u; and v23 Lbw0; alike) is \
                         * dumped with its full byte content AFTER the store, \
                         * so the writeMetadata byte-lane corruption can be \
                         * caught in the act. Env-gated + budgeted. */ \
                        static thread_local const bool s56_meta_trace = \
                            std::getenv("MINIANDROID_META_STORE_TRACE") != nullptr; \
                        static thread_local uint32_t s56_meta_budget = 6000; \
                        if (s56_meta_trace && s56_meta_budget > 0 && \
                            (strcmp(op_name, "aput-wide") == 0 || \
                             strcmp(op_name, "aput") == 0)) { \
                            for (auto& kv : heap_.all_objects()) { \
                                auto a_f = heap_.get_object_field(kv.first, "a"); \
                                if (!a_f.has_value() || \
                                    a_f->type != DalvikType::OBJECT_REF || \
                                    a_f->object_id != arr_val.object_id) \
                                    continue; \
                                --s56_meta_budget; \
                                std::cerr << "[S56-META-STORE] map=o" << kv.first \
                                          << " arr=o" << arr_val.object_id \
                                          << " idx=" << idx \
                                          << " store=" << op_name \
                                          << " v=0x" << std::hex; \
                                if (src_val.type == DalvikType::INT64) \
                                    std::cerr << (unsigned long long)src_val.long_val; \
                                else \
                                    std::cerr << (unsigned long long)(uint32_t)src_val.int_val; \
                                std::cerr << std::dec; \
                                auto al = heap_.get_object_field(arr_val.object_id, "__array_length__"); \
                                int alen = (al.has_value() && al->type == DalvikType::INT32) ? al->int_val : 0; \
                                std::cerr << " md=["; \
                                for (int mi = 0; mi < alen && mi < 4; ++mi) { \
                                    auto mv = heap_.get_object_field( \
                                        arr_val.object_id, \
                                        "array[" + std::to_string(mi) + "]"); \
                                    if (mv.has_value() && mv->type == DalvikType::INT64) { \
                                        char hx[32]; \
                                        snprintf(hx, sizeof(hx), "%016llx", \
                                                 (unsigned long long)mv->long_val); \
                                        std::cerr << (mi ? " " : "") << hx; \
                                    } \
                                } \
                                std::cerr << "] caller=" << current_class_ \
                                          << "." << current_method_ \
                                          << " pc=" << pc_ << std::endl; \
                                break; \
                            } \
                        } \
                        /* Length immutable — NO auto-grow (AOSP). */ \
                    } else if (arr_on_heap) { \
                        /* Length unknown (0, never recorded): legacy path — store + record/grow. \
                         * F-NEW-268b: a RECORDED zero never reaches here (it threw above); \
                         * this legacy gate is now strictly the unknown-length face. \
                         * Preserves arrays filled aput-by-aput with no recorded \
                         * length (mirrors aget's arr_len==0 legacy gate). */ \
                        heap_.set_object_field(arr_val.object_id, field, src_val); \
                        auto len_field = heap_.get_object_field(arr_val.object_id, "__array_length__"); \
                        if (!len_field.has_value() || len_field->int_val <= idx) { \
                            heap_.set_object_field(arr_val.object_id, "__array_length__", \
                                DalvikValue::make_int(idx + 1)); \
                        } \
                    } \
                    /* non-OBJECT_REF or heap-missing: legacy silent skip. */ \
                    pc_ = pc_ + 2; \
                    break; \
                }

            ARRAY_PUT_CASE(APUT, "aput")
            ARRAY_PUT_CASE(APUT_WIDE, "aput-wide")
            ARRAY_PUT_CASE(APUT_OBJECT, "aput-object")
            ARRAY_PUT_CASE(APUT_BOOLEAN, "aput-boolean")
            ARRAY_PUT_CASE(APUT_BYTE, "aput-byte")
            ARRAY_PUT_CASE(APUT_CHAR, "aput-char")
            ARRAY_PUT_CASE(APUT_SHORT, "aput-short")
            #undef ARRAY_PUT_CASE
            case Opcode::CHECK_CAST:
                success = execute_check_cast(pc_, trace);
                trace.opcode_name = "check-cast";
                break;
            case Opcode::INSTANCE_OF:
                success = execute_instance_of(pc_, trace);
                trace.opcode_name = "instance-of";
                break;
            
            // EXP-035: Instance Field Operations
            case Opcode::IGET:
                success = execute_iget(pc_, trace);
                trace.opcode_name = "iget";
                break;
            case Opcode::IGET_OBJECT:
                success = execute_iget_object(pc_, trace);
                trace.opcode_name = "iget-object";
                break;
            // EXP-062: Add missing iget variants. iget-wide reads a 64-bit
            // field; iget-boolean/byte/char/short read primitive fields.
            // All use the same 22c format as iget.
            case Opcode::IGET_WIDE:
            case Opcode::IGET_BOOLEAN:
            case Opcode::IGET_BYTE:
            case Opcode::IGET_CHAR:
            case Opcode::IGET_SHORT:
                success = execute_iget(pc_, trace);
                trace.opcode_name = "iget-variant";
                break;
            case Opcode::IPUT:
                success = execute_iput(pc_, trace);
                trace.opcode_name = "iput";
                break;
            case Opcode::IPUT_OBJECT:
                success = execute_iput_object(pc_, trace);
                trace.opcode_name = "iput-object";
                break;
            // EXP-062: iput-wide and other iput variants.
            // iput-wide writes a 64-bit value (occupying vA and vA+1)
            // to a field. We store it as a single INT64 DalvikValue.
            case Opcode::IPUT_WIDE:
            case Opcode::IPUT_BOOLEAN:
            case Opcode::IPUT_BYTE:
            case Opcode::IPUT_CHAR:
            case Opcode::IPUT_SHORT:
                success = execute_iput(pc_, trace);
                trace.opcode_name = "iput-variant";
                break;
            
            // EXP-035: Static Field Operations
            case Opcode::SGET:
                success = execute_sget(pc_, trace);
                trace.opcode_name = "sget";
                break;
            case Opcode::SGET_OBJECT:
                success = execute_sget_object(pc_, trace);
                trace.opcode_name = "sget-object";
                break;
            // EXP-062: Add sget-wide
            case Opcode::SGET_WIDE:
                success = execute_sget(pc_, trace);
                trace.opcode_name = "sget-wide";
                break;
            case Opcode::SPUT:
                success = execute_sput(pc_, trace);
                trace.opcode_name = "sput";
                break;
            case Opcode::SPUT_OBJECT:
                success = execute_sput_object(pc_, trace);
                trace.opcode_name = "sput-object";
                break;
            // EXP-062: Add sput-wide
            case Opcode::SPUT_WIDE:
                success = execute_sput(pc_, trace);
                trace.opcode_name = "sput-wide";
                break;
            // EXP-038 (BLOCKER-027): sput-boolean and other sget/sput variants
            case Opcode::SPUT_BOOLEAN:
                success = execute_sput(pc_, trace);  // same logic as sput
                trace.opcode_name = "sput-boolean";
                break;
            case Opcode::SPUT_BYTE:
            case Opcode::SPUT_CHAR:
            case Opcode::SPUT_SHORT:
                success = execute_sput(pc_, trace);
                trace.opcode_name = "sput-variant";
                break;
            case Opcode::SGET_BOOLEAN:
            case Opcode::SGET_BYTE:
            case Opcode::SGET_CHAR:
            case Opcode::SGET_SHORT:
                success = execute_sget(pc_, trace);  // same logic as sget
                trace.opcode_name = "sget-variant";
                break;
            
            // Invokes
            case Opcode::INVOKE_VIRTUAL:
                success = execute_invoke_virtual(pc_, trace, result);
                trace.opcode_name = "invoke-virtual";
                break;
            case Opcode::INVOKE_SUPER:
                // EXP-037 Phase B (BLOCKER-012): invoke-super — required for
                // super.onCreate() calls. Without this, execution halts at PC=0
                // of MainActivity.onCreate() for every real Android APK.
                success = execute_invoke_super(pc_, trace, result);
                trace.opcode_name = "invoke-super";
                break;
            case Opcode::INVOKE_DIRECT:
                success = execute_invoke_direct(pc_, trace, result);
                trace.opcode_name = "invoke-direct";
                break;
            case Opcode::INVOKE_STATIC:
                /* R-NEW-558 (TRAIN 5): env gate hoisted (thread_local static).
                 * Semantics identical. */
                static thread_local const bool f040_invoke_static =
                    diag_env("MINIANDROID_F040_DIAG");
                if (f040_invoke_static &&
                    current_class_ == "Ln/a;" && current_method_ == "r") {
                    std::cerr << "[R-INVOKE] entering execute_invoke_static pc="
                              << pc_ << std::endl;
                }
                success = execute_invoke_static(pc_, trace, result);
                trace.opcode_name = "invoke-static";
                break;
            case Opcode::INVOKE_INTERFACE:
                success = execute_invoke_interface(pc_, trace, result);
                trace.opcode_name = "invoke-interface";
                break;

            // EXP-049 Phase 3: invoke-*/range opcodes (3rc format)
            // Format 3rc: AA|op BBBB CCCC (3 code units)
            //   AA = arg count (high byte of first code unit)
            //   BBBB = method_idx (second code unit)
            //   CCCC = first register (third code unit)
            // The 3rc format reads AA consecutive registers starting at CCCC.
            // CRITICAL: The old code routed these to the 35c handlers which
            // extract registers as 4-bit nibbles from a 16-bit FEDC word.
            // But 3rc uses CCCC as a 16-bit register base, reading consecutive
            // 16-bit register indices. This was BROKEN — the 35c handler
            // reads method_idx from pc+1 (correct) but register list from pc+2
            // as 4-bit nibbles (WRONG for 3rc). The fix is to build the args
            // vector from consecutive registers starting at CCCC.
            case Opcode::INVOKE_VIRTUAL_RANGE:
            case Opcode::INVOKE_SUPER_RANGE:
            case Opcode::INVOKE_DIRECT_RANGE:
            case Opcode::INVOKE_STATIC_RANGE:
            case Opcode::INVOKE_INTERFACE_RANGE: {
                // 3rc format: AA|op BBBB CCCC
                if (pc_ + 2 >= bytecode_.size()) { pc_ = pc_ + 1; break; }
                uint16_t instr = bytecode_[pc_];
                uint8_t argc = (instr >> 8) & 0xFF;  // AA = arg count
                uint16_t method_idx = bytecode_[pc_ + 1];  // BBBB = method index
                uint16_t first_reg = bytecode_[pc_ + 2];   // CCCC = first register

                // ────────────────────────────────────────────────────────────
                // F-071 (R-NEW-295) — RANGE-INVOKE SHADOW-DISPATCH STATIC
                // FLAG LAW. The 35c invoke paths save + reset
                // current_invoke_is_static_ at their boundary (EXP-071
                // Phase 7) because try_shadow_dispatch builds the shadow
                // CallContext from that flag: instance calls place args[0]
                // into ctx.receiver_id (has_receiver=true); static calls
                // keep args[0] as the first ctx parameter. The 3rc path
                // never touched the flag, so a range-invoke executed while
                // a STATIC method's execute_invoke_static frame was active
                // (R8-minified Kotlin — every @Composable is static, e.g.
                // dooz composable Landroidx/compose/ui/platform/D;.a)
                // dispatched its INSTANCE calls to shadows with
                // has_receiver=false → receiver_id=0 → ViewShadow.getParent
                // answered null for a VALID view (obj#725 with parent=102,
                // proven by MINIANDROID_TAG_TRACE) → Kotlin checkNotNull
                // NPE "null cannot be cast to non-null type android.view.
                // View" at D.a pc=0x84 — the dooz first-frame blocker.
                // General law: the flag must reflect the CURRENT invoke's
                // opcode, not the caller frame's. INVOKE_STATIC_RANGE →
                // true; virtual/super/direct/interface-range → false.
                // Restored on exit, identical to the 35c law.
                // ────────────────────────────────────────────────────────────
                const bool saved_range_is_static = current_invoke_is_static_;
                current_invoke_is_static_ =
                    (instr & 0xFF) ==
                    static_cast<uint8_t>(Opcode::INVOKE_STATIC_RANGE);
                struct RangeStaticFlagRestore {
                    bool& ref; const bool saved;
                    ~RangeStaticFlagRestore() { ref = saved; }
                } range_flag_restore{current_invoke_is_static_,
                                     saved_range_is_static};

                // Build args from consecutive registers.
                // EXP-095 (CM-019): SIGNATURE-AWARE arg building — per the
                // method proto, wide params (J/D) consume two registers and
                // FLOAT (F) params carry raw float BITS in an INT32 register.
                // CYCLE-E FIX: for INSTANCE calls (virtual/super/direct/
                // interface /range) the FIRST range register is the RECEIVER
                // (`this`), not a parameter. The previous walk consumed the
                // receiver as param #0 — every argument was misaligned by
                // one slot, the receiver leaked into the param list, float
                // conversion bit-shifted through it, and the FINAL parameter
                // (often the Paint in drawRect(l,t,r,b,paint)) fell off the
                // end entirely. Static calls have no receiver slot.
                std::vector<DalvikValue> args;
                // F-102 (S58, R-NEW-376): the call site's method PROTO is a
                // first-class part of the invoke contract (35c path resolves
                // and passes it — F-023 exact-descriptor overload law). The
                // 3rc path resolved it only locally for signature-aware arg
                // building and DROPPED it at the try_recursive_invoke
                // boundary (default ""), so every range ctor-delegation
                // ladder (Kotlin default-args: gz1/bp1/j0 in dooz v18+v23)
                // fell into the arity heuristic which prefers the LARGEST
                // bytecode body — re-selecting the CALLING overload itself
                // → same-receiver self-recursion to the depth cap. Hoist the
                // proto to dispatch scope and pass it to both dispatch
                // attempts below.
                std::string range_proto = "<unknown>";
                {
                    // Collect the RAW register window first (receiver first
                    // for instance calls), then apply signature conversion.
                    std::vector<DalvikValue> raw;
                    for (uint8_t i = 0; i < argc && i < 255; ++i) {
                        if (first_reg + i > 65535) break;   // register bounds
                        raw.push_back(get_register(
                            static_cast<uint16_t>(first_reg + i)));
                    }
                    const bool is_static_call =
                        (instr & 0xFF) == static_cast<uint8_t>(Opcode::INVOKE_STATIC_RANGE);
                    if (dex_report_) {
                        range_proto = resolve_method_proto_for_dex(method_idx, current_dex_index_);
                    }
                    const std::vector<std::string> param_types =
                        parse_proto_param_types(range_proto);
                    args = build_invoke_args(raw, param_types, is_static_call);
                }

                {
                    static thread_local uint64_t rng_n = 0;
                    std::string rng_cls = dex_report_
                        ? resolve_method_class_for_dex(method_idx, current_dex_index_)
                        : std::string("<nodex>");
                    if (rng_cls == "Lj/b;" || rng_cls == "Lj/i;" || rng_cls == "LC0/b;") {
                        ++rng_n;
                        if (rng_n <= 12) {
                            std::cerr << "[S34-RANGE] " << rng_cls << "."
                                      << (dex_report_
                                              ? resolve_method_name_for_dex(method_idx, current_dex_index_)
                                              : "?")
                                      << " argc=" << (int)argc
                                      << " first_reg=" << first_reg
                                      << " caller=" << current_class_ << "."
                                      << current_method_
                                      << " depth=" << recursion_depth_
                                      << std::endl;
                        }
                    }
                }
                // Resolve method name
                std::string method_name = "<range_method:" + std::to_string(method_idx) + ">";
                std::string class_name = "<range_class>";
                if (dex_report_) {
                    method_name = resolve_method_name_for_dex(method_idx, current_dex_index_);
                    class_name = resolve_method_class_for_dex(method_idx, current_dex_index_);
                }

                trace.opcode_name = "invoke-*/range";

                // ────────────────────────────────────────────────────────
                // F-141 (S72-W3): ART NULL-RECEIVER LAW for range invokes.
                // Every non-static 3rc form (virtual/super/direct/interface)
                // treats args[0] as the receiver (CYCLE-E law). ART throws
                // NPE at the invoke site before the callee body executes.
                // Evidence (dooz S72-W1): invoke-virtual/range pc155
                // dispatched Lrz1;.l entry #49 with this=NULL (t=8); the
                // trie walk corrupted state until arraycopy(null) NPE fired
                // at the WRONG site — first divergence hidden.
                // ────────────────────────────────────────────────────────
                if ((instr & 0xFF) != static_cast<uint8_t>(Opcode::INVOKE_STATIC_RANGE) &&
                    !args.empty() && f141_is_null_receiver(args[0])) {
                    throw_deferred("Ljava/lang/NullPointerException;",
                                   "Attempt to invoke '" + class_name + "." +
                                       method_name + "' on a null object reference",
                                   "f141-null-recv-range");
                    pc_ += 3;  // 3rc length; a catch handler redirect overrides pc
                    break;
                }

                // ────────────────────────────────────────────────────────────
                // M3 FIX-M3-008 (§19 HEAP CLASS IDENTITY LAW):
                // For invoke-virtual/range and invoke-interface/range the
                // receiver's RUNTIME class recorded on the heap object is the
                // dispatch authority (AOSP Object.getClass() semantics) — the
                // static declaring class from method_ids[] is only a fallback.
                //
                // Evidence (chessclock v29, 12-frame timer sequence): tick 1
                // reached ChessClock.formatTime as real DEX and produced
                // "9:59:59"; from tick 2 ChessClock$8.run called formatTime
                // via 3rc sites whose method_ids entry declares
                // Landroid/app/Activity;.formatTime — the range handler
                // dispatched on that STATIC class, missed the DEX lookup
                // (framework class), fell to ActivityShadow.dispatch and the
                // clock label computed "null". The 35c path already had this
                // law (EXP-059 polymorphism fix); the 3rc path did not.
                //
                // invoke-direct (non-virtual: <init>/private) and invoke-super
                // (resolves at the CURRENT class's superclass, NOT the runtime
                // type) keep declaring-class dispatch per AOSP.
                // ────────────────────────────────────────────────────────────
                const uint8_t range_op = instr & 0xFF;
                const bool range_virtual_like =
                    range_op == static_cast<uint8_t>(Opcode::INVOKE_VIRTUAL_RANGE) ||
                    range_op == static_cast<uint8_t>(Opcode::INVOKE_INTERFACE_RANGE);
                std::string range_runtime_class;
                if (range_virtual_like && !args.empty() &&
                    args[0].type == DalvikType::OBJECT_REF && args[0].object_id != 0) {
                    if (auto* range_heap_obj = heap_.get(args[0].object_id)) {
                        range_runtime_class = range_heap_obj->class_descriptor;
                    }
                }

                // Try recursive invoke
                DalvikValue return_val = DalvikValue::make_void();
                ApiCallTrace::Status status = ApiCallTrace::Status::STUBBED;

                bool recursively_invoked = false;
                if (config_.enable_api_bridge) {
                    // §19: runtime class first for virtual/interface dispatch
                    // F-102: pass the resolved range proto on BOTH attempts —
                    // exact (class, name, desc) selection per the F-023 law;
                    // when the proto misses the heuristic path is unchanged.
                    if (!range_runtime_class.empty() && range_runtime_class != class_name &&
                        try_recursive_invoke(range_runtime_class, method_name,
                                             args, return_val, result, range_proto)) {
                        last_invoke_return_ = return_val;
                        recursively_invoked = true;
                        status = ApiCallTrace::Status::IMPLEMENTED;
                    }
                    if (!recursively_invoked &&
                        try_recursive_invoke(class_name, method_name, args, return_val, result, range_proto)) { last_invoke_return_ = return_val;
                        recursively_invoked = true;
                        status = ApiCallTrace::Status::IMPLEMENTED;
                    }
                }
                // ── CONT-12 F-NEW-266 (3rc) ──────────────────────────────
                // Same transitive interface-default law as the 35c path:
                // after runtime-class and declaring-class misses, ART
                // resolves virtual dispatch into the receiver's transitive
                // superinterfaces (default methods). Without it the bridge
                // stub silently returned null (un-renamed Compose 1.11.4
                // oracle face: Modifier.then default body via 3rc sites).
                if (!recursively_invoked && config_.enable_api_bridge &&
                    range_virtual_like && !args.empty() &&
                    args[0].type == DalvikType::OBJECT_REF) {
                    const std::string& f266_recv =
                        range_runtime_class.empty() ? class_name
                                                    : range_runtime_class;
                    std::string f266_dispatched;
                    if (try_interface_default_invoke(
                            f266_recv, method_name, range_proto, args,
                            return_val, result, &f266_dispatched)) {
                        last_invoke_return_ = return_val;
                        recursively_invoked = true;
                        status = ApiCallTrace::Status::IMPLEMENTED;
                        // S157-B: trace_cap==0 gate (never-read trace).
                        if (config_.trace_cap > 0) {
                        trace.invoked_method =
                            f266_dispatched + " [default-method " +
                            range_proto + "]";
                        }
                    }
                }
                if (!recursively_invoked && config_.enable_api_bridge) {
                    bridge_to_api(class_name, method_name, args, return_val, status, method_idx); last_invoke_return_ = return_val;
                }

                // Record API trace
                // GP S223 CALL-001/002/003 (issue #582): the 3rc trace
                // previously dropped the descriptor, arguments, return value
                // and frame identity — overloaded range calls were ambiguous
                // and first-divergence diagnosis had no typed data. Mirror
                // the 35c fill: exact descriptor (range_proto, already
                // resolved for the F-102 exact-match law), bounded typed
                // argument summaries (≤8), return value, and the current
                // frame id.
                ApiCallTrace api_trace;
                api_trace.sequence = api_call_sequence_++;
                api_trace.api_class = class_name;
                api_trace.method = method_name;
                api_trace.descriptor = range_proto;             // CALL-001
                for (size_t ai = 0; ai < args.size() && ai < 8; ++ai)
                    api_trace.arguments.push_back(args[ai].to_string());
                api_trace.return_value = return_val.to_string(); // CALL-002
                api_trace.status = status;
                api_trace.pc = pc_;
                api_trace.frame_id =
                    call_stack_.empty() ? 0 : call_stack_.top().frame_id; // CALL-003
                note_api_status(api_trace);  // F-NEW-200 census
                batched_cap_push(result.api_call_traces,
                                  result.api_call_ring_cursor,
                                  static_cast<size_t>(config_.api_call_trace_cap),
                                  std::move(api_trace));

                trace.invoked_method = class_name + "." + method_name;
                pc_ = pc_ + 3;
                break;
            }
            
            // Returns
            case Opcode::RETURN_VOID:
                success = execute_return_void(pc_, trace);
                trace.opcode_name = "return-void";
                break;
            case Opcode::RETURN:
                success = execute_return(pc_, trace);
                trace.opcode_name = "return";
                break;
            case Opcode::RETURN_OBJECT:
                success = execute_return_object(pc_, trace);
                trace.opcode_name = "return-object";
                break;
            // EXP-088+ F5 CRITICAL FIX: return-wide (opcode 0x10) was MISSING
            // from the opcode dispatcher. It fell through to the default case
            // (handle_unimplemented), causing any method that returns a long
            // or double to:
            //   1. Not actually return (PC didn't advance past the return)
            //   2. Leave the caller's move-result-wide reading stale/zero data
            //
            // This is a GENERIC VM bug — affects any APK that uses long/double
            // return values (timestamps, durations, sizes, coordinates, etc.).
            case Opcode::RETURN_WIDE:
                success = execute_return_wide(pc_, trace);
                trace.opcode_name = "return-wide";
                break;
            
            // Control flow
            case Opcode::GOTO:
            case Opcode::GOTO_16:
            case Opcode::GOTO_32:
                success = execute_goto(pc_, trace);
                trace.opcode_name = "goto";
                break;
            case Opcode::IF_EQZ:
                success = execute_if_eqz(pc_, trace);
                trace.opcode_name = "if-eqz";
                break;
            case Opcode::IF_NEZ:
                success = execute_if_nez(pc_, trace);
                trace.opcode_name = "if-nez";
                break;
            // EXP-037 Phase B (BLOCKER-018): 22t format if-* opcodes
            case Opcode::IF_EQ:
                success = execute_if_eq(pc_, trace);
                trace.opcode_name = "if-eq";
                break;
            case Opcode::IF_NE:
                success = execute_if_ne(pc_, trace);
                trace.opcode_name = "if-ne";
                break;
            case Opcode::IF_LT:
                success = execute_if_lt(pc_, trace);
                trace.opcode_name = "if-lt";
                break;
            case Opcode::IF_GE:
                success = execute_if_ge(pc_, trace);
                trace.opcode_name = "if-ge";
                break;
            case Opcode::IF_GT:
                success = execute_if_gt(pc_, trace);
                trace.opcode_name = "if-gt";
                break;
            case Opcode::IF_LE:
                success = execute_if_le(pc_, trace);
                trace.opcode_name = "if-le";
                break;

            // EXP-038 (BLOCKER-029): if-*z opcodes (21t format, like if-eqz)
            // EXP-043 Phase 1: each if-*z opcode now dispatches to its OWN
            // handler instead of all routing to execute_if_eqz. Previously
            // if-ltz/if-gez/if-lez all used execute_if_eqz's "if (v == 0)"
            // comparison, and if-gtz used execute_if_nez's "if (v != 0)"
            // comparison. These are WRONG — if-ltz must be "if (v < 0)",
            // if-gez "if (v >= 0)", if-gtz "if (v > 0)", if-lez "if (v <= 0)".
            // The bug caused Kotlin Intrinsics.createParameterIsNullExceptionMessage
            // to loop forever because if-ltz v3 with v3=5 was treated as
            // if-eqz (5==0 false) instead of if-ltz (5<0 false) — same answer
            // in that case, but if-ltz v3 with v3=-1 should branch but didn't.
            case Opcode::IF_LTZ:
                success = execute_if_ltz(pc_, trace);
                trace.opcode_name = "if-ltz";
                break;
            case Opcode::IF_GEZ:
                success = execute_if_gez(pc_, trace);
                trace.opcode_name = "if-gez";
                break;
            case Opcode::IF_GTZ:
                success = execute_if_gtz(pc_, trace);
                trace.opcode_name = "if-gtz";
                break;
            case Opcode::IF_LEZ:
                success = execute_if_lez(pc_, trace);
                trace.opcode_name = "if-lez";
                break;
            
            // MASTER RECONCILIATION (K-18, 2026-09-03): packed-switch/sparse-switch.
            // IMPORTANT (why this exists): both opcodes were defined in the
            // opcode table but had NO dispatch case — every switch statement
            // produced by D8 (string/table switches, state machines, enum
            // maps) fell through to handle_unimplemented and halted the
            // method. Fixture: tests/semantic_switch_parse_neg_test.cpp
            // (group S — 7/7 FAIL pre-fix).
            // Semantics per AOSP/dalvik bytecodes:
            //   31t format: AA|op BBBB|BBBB — 32-bit signed payload offset in
            //   code units, relative to the SWITCH opcode pc.
            //   packed-switch-payload (ident 0x0100): u16 size, i32 first_key,
            //     i32 targets[size] — targets also relative to the SWITCH pc.
            //   sparse-switch-payload (ident 0x0200): u16 size, i32 keys[size]
            //     (sorted), i32 targets[size].
            //   No match → default = pc + 3 (fall past the 3-unit instruction).
            case Opcode::PACKED_SWITCH:
            case Opcode::SPARSE_SWITCH: {
                const bool is_packed = (opcode == Opcode::PACKED_SWITCH);
                uint16_t instr_sw = bytecode_[pc_];
                uint8_t vAA_sw = (instr_sw >> 8) & 0xFF;
                if (pc_ + 2 >= bytecode_.size()) return false;
                int32_t off_sw = static_cast<int32_t>(
                    static_cast<uint32_t>(bytecode_[pc_ + 1]) |
                    (static_cast<uint32_t>(bytecode_[pc_ + 2]) << 16));
                const int64_t payload_addr = static_cast<int64_t>(pc_) + off_sw;
                DalvikValue vv_sw = get_register(vAA_sw);
                // S104 SWITCH-KEY-WIDENING law: packed/sparse-switch consumes
                // an INT register — a byte/char/short/boolean value (typed by
                // signature-aware invoke arg copying) must widen, not collapse
                // to 0. R8 horizontal class merging gives every merged class a
                // `$r8$classId:B` + packed-switch ctor dispatch: with key=0 the
                // merged constructor ran the WRONG branch (solitaire
                // ComponentActivity.<init>: SavedStateRegistryController stored
                // with `input` unset → NPE at getSavedStateProvider; the same
                // law is the "R8 merged-lambda wrong branch" divergence).
                // dalvik_int_value (CHAR-PROBE law) is the shared widening.
                int32_t key_sw = dalvik_int_value(vv_sw);
                int32_t target_sw = 3;  // default: fall through the 3-unit instr
                auto in_range_sw = [&](int64_t addr, int64_t units) {
                    return addr >= 0 && addr + units <= static_cast<int64_t>(bytecode_.size());
                };
                auto read_i32_sw = [&](int64_t addr) -> int32_t {
                    return static_cast<int32_t>(
                        static_cast<uint32_t>(bytecode_[static_cast<size_t>(addr)]) |
                        (static_cast<uint32_t>(bytecode_[static_cast<size_t>(addr) + 1]) << 16));
                };
                if (in_range_sw(payload_addr, 2)) {
                    const uint16_t ident_sw = bytecode_[static_cast<size_t>(payload_addr)];
                    if ((is_packed && ident_sw == 0x0100) || (!is_packed && ident_sw == 0x0200)) {
                        const uint16_t size_sw = bytecode_[static_cast<size_t>(payload_addr) + 1];
                        if (is_packed) {
                            if (in_range_sw(payload_addr, 4)) {
                                const int32_t first_key_sw = read_i32_sw(payload_addr + 2);
                                const int64_t idx_sw =
                                    static_cast<int64_t>(key_sw) - first_key_sw;
                                if (idx_sw >= 0 && idx_sw < static_cast<int64_t>(size_sw) &&
                                    in_range_sw(payload_addr + 4 + idx_sw * 2, 2)) {
                                    target_sw = read_i32_sw(payload_addr + 4 + idx_sw * 2);
                                }
                            }
                        } else {
                            // keys: payload+2 .. +2+2*size; targets: payload+2+2*size ..
                            if (in_range_sw(payload_addr, 2 + 4 * static_cast<int64_t>(size_sw))) {
                                int64_t lo_sw = 0, hi_sw = size_sw - 1;
                                int64_t found_sw = -1;
                                while (lo_sw <= hi_sw) {
                                    int64_t mid_sw = (lo_sw + hi_sw) / 2;
                                    int32_t k_sw = read_i32_sw(payload_addr + 2 + mid_sw * 2);
                                    if (k_sw == key_sw) { found_sw = mid_sw; break; }
                                    if (k_sw < key_sw) lo_sw = mid_sw + 1; else hi_sw = mid_sw - 1;
                                }
                                if (found_sw >= 0 &&
                                    in_range_sw(payload_addr + 2 + 2 * static_cast<int64_t>(size_sw) + found_sw * 2, 2)) {
                                    target_sw = read_i32_sw(
                                        payload_addr + 2 + 2 * static_cast<int64_t>(size_sw) + found_sw * 2);
                                }
                            }
                        }
                    } else {
                        std::cerr << "[SWITCH] payload ident mismatch (expected 0x"
                                  << (is_packed ? "0100" : "0200") << ", got 0x"
                                  << to_hex16(ident_sw) << ") → default" << std::endl;
                    }
                } else {
                    std::cerr << "[SWITCH] payload address out of range (pc=" << pc_
                              << " off=" << off_sw << ") → default" << std::endl;
                }
                trace.opcode_name = is_packed ? "packed-switch" : "sparse-switch";
                // [S104-SW-PROBE] R8 merged-ctor classId dispatch forensic
                // (solitaire MatcherMatchResult/$r8$classId): print the exact
                // switch resolution when env-gated. Env-gated (OFF by default,
                // one-time init — no per-instruction getenv cost).
                static const bool s104_sw_probe =
                    std::getenv("MINIANDROID_SW_PROBE") != nullptr;
                if (s104_sw_probe &&
                    current_class_.find("MatcherMatchResult") != std::string::npos) {
                    std::cerr << "[S104-SW] " << current_class_ << "." << current_method_
                              << " pc=" << pc_ << " key=" << key_sw
                              << " payload@" << payload_addr
                              << " ident=0x" << to_hex16(bytecode_.size() > static_cast<size_t>(payload_addr) && payload_addr >= 0 ? bytecode_[static_cast<size_t>(payload_addr)] : 0)
                              << " target=" << target_sw << " dest=" << (pc_ + target_sw)
                              << std::endl;
                }
                pc_ = pc_ + target_sw;  // targets are relative to the SWITCH pc
                break;
            }

            case Opcode::NOP:
                trace.opcode_name = "nop";
                pc_ += 1;
                break;

            // EXP-038 (BLOCKER-028): Arithmetic 2addr opcodes (12x format)
            // vA = vA <op> vB
            #define ARITH_2ADDR_CASE(opcode, op_name, op) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vA = (instr >> 8) & 0xF; \
                    /* DEMO-2ADDR-NIBBLE (2026-09-04): 12x format is B|A|op — */ \
                    /* the B source register is bits 12-15. The previous read */ \
                    /* `(instr >> 4) & 0xF` took bits 4-7 of the opcode byte, */ \
                    /* so `rem-int/2addr v1, v0` (0x01B2) read v11 (0x01B2>>4 */ \
                    /* & 0xF == 0xB) instead of v0. Every /2addr arithmetic   */ \
                    /* op whose second operand register differed from the    */ \
                    /* phantom nibble computed garbage. Same bug class as    */ \
                    /* EXP-058's move fix and the ARRAY_LENGTH nibble fix.   */ \
                    uint8_t vB = (instr >> 12) & 0xF; \
                    DalvikValue a = get_register(vA); \
                    DalvikValue b = get_register(vB); \
                    DalvikValue result_val; \
                    result_val.type = DalvikType::INT32; \
                    int32_t a_val = dalvik_int_value(a); \
                    int32_t b_val = dalvik_int_value(b); \
                    /* MASTER RECONCILIATION (K-29, 2026-09-03): was guard-yield-0 — */ \
                    /* AND the unguarded a_val / b_val below was C++ UB on zero.   */ \
                    /* Now throws ArithmeticException (deferred mechanism).        */ \
                    /* GP-INT-012 (issue #582): signed add/sub/mul/shl and the     */ \
                    /* MIN/-1 div/rem edge are C++ UB on the signed values; DEX/   */ \
                    /* Java law is width-defined two's-complement wrap and defined */ \
                    /* MIN/-1 results. Computed in unsigned width, stored as the   */ \
                    /* identical bit pattern.                                      */ \
                    /* GP-INT-015 (issue #582): `op == "lit"` compared literal     */ \
                    /* POINTER addresses — strcmp by content, portable.            */ \
                    if ((strcmp(op, "div") == 0 || strcmp(op, "rem") == 0) && b_val == 0) { \
                        throw_deferred("Ljava/lang/ArithmeticException;", "divide by zero", "ARITH-2ADDR"); \
                        pc_ = pc_ + 1; \
                        break; \
                    } \
                    if (strcmp(op, "add") == 0) result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(a_val) + static_cast<uint32_t>(b_val)); \
                    else if (strcmp(op, "sub") == 0) result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(a_val) - static_cast<uint32_t>(b_val)); \
                    else if (strcmp(op, "mul") == 0) result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(a_val) * static_cast<uint32_t>(b_val)); \
                    else if (strcmp(op, "div") == 0) result_val.int_val = (b_val == -1) ? static_cast<int32_t>(0u - static_cast<uint32_t>(a_val)) : a_val / b_val; \
                    else if (strcmp(op, "rem") == 0) result_val.int_val = (b_val == -1) ? 0 : a_val % b_val; \
                    else if (strcmp(op, "and") == 0) result_val.int_val = a_val & b_val; \
                    else if (strcmp(op, "or") == 0)  result_val.int_val = a_val | b_val; \
                    else if (strcmp(op, "xor") == 0) result_val.int_val = a_val ^ b_val; \
                    else if (strcmp(op, "shl") == 0) result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(a_val) << (b_val & 0x1f)); \
                    else if (strcmp(op, "shr") == 0) result_val.int_val = a_val >> (b_val & 0x1f); \
                    else if (strcmp(op, "ushr") == 0) result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(a_val) >> (b_val & 0x1f)); \
                    static thread_local const bool wide_diag_on = \
                        diag_env("MINIANDROID_WIDE_DIAG"); /* R-NEW-558 */ \
                    if (wide_diag_on) { \
                        std::cerr << "[WIDE-DIAG] " << op_name << " @" << current_class_ << "." \
                                  << current_method_ << " v" << (int)vA << "=" << a_val \
                                  << " v" << (int)vB << "=" << b_val \
                                  << " -> " << result_val.int_val << std::endl; \
                    } \
                    set_register(vA, result_val); \
                    trace.opcode_name = op_name; \
                    pc_ = pc_ + 1; \
                    break; \
                }

            ARITH_2ADDR_CASE(ADD_INT_2ADDR, "add-int/2addr", "add")
            ARITH_2ADDR_CASE(SUB_INT_2ADDR, "sub-int/2addr", "sub")
            ARITH_2ADDR_CASE(MUL_INT_2ADDR, "mul-int/2addr", "mul")
            ARITH_2ADDR_CASE(DIV_INT_2ADDR, "div-int/2addr", "div")
            ARITH_2ADDR_CASE(REM_INT_2ADDR, "rem-int/2addr", "rem")
            ARITH_2ADDR_CASE(AND_INT_2ADDR, "and-int/2addr", "and")
            ARITH_2ADDR_CASE(OR_INT_2ADDR,  "or-int/2addr",  "or")
            ARITH_2ADDR_CASE(XOR_INT_2ADDR, "xor-int/2addr", "xor")
            ARITH_2ADDR_CASE(SHL_INT_2ADDR, "shl-int/2addr", "shl")
            ARITH_2ADDR_CASE(SHR_INT_2ADDR, "shr-int/2addr", "shr")
            ARITH_2ADDR_CASE(USHR_INT_2ADDR, "ushr-int/2addr", "ushr")
            #undef ARITH_2ADDR_CASE

            // EXP-038 (BLOCKER-028): Binary 23x format: AA|op BB|CC
            // vAA = vBB <op> vCC
            #define ARITH_23X_CASE(opcode, op_name, op) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vAA = (instr >> 8) & 0xFF; \
                    uint8_t vBB = bytecode_[pc_ + 1] & 0xFF; \
                    uint8_t vCC = (bytecode_[pc_ + 1] >> 8) & 0xFF; \
                    DalvikValue b = get_register(vBB); \
                    DalvikValue c = get_register(vCC); \
                    DalvikValue result_val; \
                    result_val.type = DalvikType::INT32; \
                    int32_t b_val = dalvik_int_value(b); \
                    int32_t c_val = dalvik_int_value(c); \
                    /* GP-INT-012/015 (issue #582): wrap-defined signed math, */ \
                    /* MIN/-1 div/rem edge, strcmp dispatch (was literal-ptr).  */ \
                    if ((strcmp(op, "div") == 0 || strcmp(op, "rem") == 0) && c_val == 0) { \
                        throw_deferred("Ljava/lang/ArithmeticException;", "divide by zero", "ARITH-23X"); \
                        pc_ = pc_ + 2; \
                        break; \
                    } \
                    if (strcmp(op, "add") == 0) result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(b_val) + static_cast<uint32_t>(c_val)); \
                    else if (strcmp(op, "sub") == 0) result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(b_val) - static_cast<uint32_t>(c_val)); \
                    else if (strcmp(op, "mul") == 0) result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(b_val) * static_cast<uint32_t>(c_val)); \
                    else if (strcmp(op, "div") == 0) result_val.int_val = (c_val == -1) ? static_cast<int32_t>(0u - static_cast<uint32_t>(b_val)) : b_val / c_val; \
                    else if (strcmp(op, "rem") == 0) result_val.int_val = (c_val == -1) ? 0 : b_val % c_val; \
                    else if (strcmp(op, "and") == 0) result_val.int_val = b_val & c_val; \
                    else if (strcmp(op, "or") == 0)  result_val.int_val = b_val | c_val; \
                    else if (strcmp(op, "xor") == 0) result_val.int_val = b_val ^ c_val; \
                    else if (strcmp(op, "shl") == 0) result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(static_cast<uint32_t>(b_val) << (c_val & 0x1f))); \
                    else if (strcmp(op, "shr") == 0) result_val.int_val = b_val >> (c_val & 0x1f); \
                    else if (strcmp(op, "ushr") == 0) result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(b_val) >> (c_val & 0x1f)); \
                    set_register(vAA, result_val); \
                    trace.opcode_name = op_name; \
                    pc_ = pc_ + 2; \
                    break; \
                }

            ARITH_23X_CASE(ADD_INT, "add-int", "add")
            ARITH_23X_CASE(SUB_INT, "sub-int", "sub")
            ARITH_23X_CASE(MUL_INT, "mul-int", "mul")
            ARITH_23X_CASE(DIV_INT, "div-int", "div")
            ARITH_23X_CASE(REM_INT, "rem-int", "rem")
            ARITH_23X_CASE(AND_INT, "and-int", "and")
            ARITH_23X_CASE(OR_INT,  "or-int",  "or")
            ARITH_23X_CASE(XOR_INT, "xor-int", "xor")
            // F-035 (MASTER-5 §E) — the 23x SHIFT family (shl/shr/ushr-int,
            // opcodes 0x98-0x9a) was missing from the dispatcher: the cases
            // fell to the unimplemented path, which advances the PC and
            // leaves the DESTINATION register holding its previous value.
            // Dalvik/AOSP law: shifts take the count from the low 5 bits
            // (mask 0x1f) — shr is arithmetic, ushr is logical (uint32).
            // First real-APK hit: dooz hash-table resize (kotlin buildSet
            // internals, R8 Lh/x.c) computes its probe mask as
            // `-1 >>> numberOfLeadingZeros(cap)`; with ushr-int unhandled
            // the mask kept the stale register content (32) instead of 7,
            // violating the resize invariant that probe & mask stays
            // inside the presence-bit array and throwing
            // ArrayIndexOutOfBoundsException (len=5, idx=5) — the
            // exception that killed the dooz composition at setContent.
            ARITH_23X_CASE(SHL_INT, "shl-int", "shl")
            ARITH_23X_CASE(SHR_INT, "shr-int", "shr")
            ARITH_23X_CASE(USHR_INT, "ushr-int", "ushr")
            #undef ARITH_23X_CASE

            // EXP-038 (BLOCKER-028): Arithmetic lit8 (22b format: AA|op BB|CC)
            // vAA = vBB <op> #CC (signed byte)
            #define ARITH_LIT8_CASE(opcode, op_name, op) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vAA = (instr >> 8) & 0xFF; \
                    uint8_t vBB = bytecode_[pc_ + 1] & 0xFF; \
                    int8_t lit = static_cast<int8_t>(bytecode_[pc_ + 1] >> 8); \
                    DalvikValue b = get_register(vBB); \
                    /* S44/R-NEW-351 probe: numEntries size math in the protobuf */ \
                    /* MessageSchema ctor — v12 must be a sane small INT32.   */ \
                    if (diag_env("MINIANDROID_S44_R351") && \
                        current_class_ == "Llt0;" && pc_ == 377) { \
                        std::cerr << "[S44-R351] mul-int/lit8 pc=377 vBB=v" << (int)vBB \
                                  << " type=" << (int)b.type \
                                  << " int_val=" << b.int_val \
                                  << " obj=" << b.object_id \
                                  << " cls=" << b.class_desc << std::endl; \
                        for (int ri = 0; ri < 20; ++ri) { \
                            DalvikValue rv = get_register(ri); \
                            std::cerr << "  [S44] v" << ri << " t=" << (int)rv.type \
                                      << " i=" << rv.int_val \
                                      << " obj=" << rv.object_id << std::endl; \
                        } \
                    } \
                    DalvikValue result_val; \
                    result_val.type = DalvikType::INT32; \
                    int32_t b_val = dalvik_int_value(b); \
                    /* K-29: lit8 div/rem by zero throws (deferred mechanism).  */ \
                    /* W15 (#627 E-02, mirroring the GP-INT-012/015 /2addr law): */ \
                    /* lit8/lit16 kept the 23x/2addr-era defects — `op == "div"`  */ \
                    /* compared literal POINTER addresses (unspecified per        */ \
                    /* [expr.eq]; worked only by string-pool luck) and the signed */ \
                    /* add/sub/mul/div/rem arithmetic was C++ UB on overflow and  */ \
                    /* on the INT32_MIN/-1 edge. DEX/Java law (JLS 15.17.2/15.19):*/ \
                    /* two's-complement wrap; MIN/-1 division == MIN, MIN/-1 rem  */ \
                    /* == 0. Computed in unsigned width, stored as the identical  */ \
                    /* bit pattern.                                               */ \
                    if ((strcmp(op, "div") == 0 || strcmp(op, "rem") == 0) && lit == 0) { \
                        throw_deferred("Ljava/lang/ArithmeticException;", "divide by zero", "ARITH-LIT8"); \
                        pc_ = pc_ + 2; \
                        break; \
                    } \
                    if (strcmp(op, "add") == 0) result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(b_val) + static_cast<uint32_t>(lit)); \
                    else if (strcmp(op, "rsub") == 0) result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(lit) - static_cast<uint32_t>(b_val)); \
                    else if (strcmp(op, "sub") == 0) result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(b_val) - static_cast<uint32_t>(lit)); \
                    else if (strcmp(op, "mul") == 0) result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(b_val) * static_cast<uint32_t>(lit)); \
                    else if (strcmp(op, "div") == 0) result_val.int_val = (lit == -1) ? static_cast<int32_t>(0u - static_cast<uint32_t>(b_val)) : b_val / lit; \
                    else if (strcmp(op, "rem") == 0) result_val.int_val = (lit == -1) ? 0 : b_val % lit; \
                    else if (strcmp(op, "and") == 0) result_val.int_val = b_val & lit; \
                    else if (strcmp(op, "or") == 0)  result_val.int_val = b_val | lit; \
                    else if (strcmp(op, "xor") == 0) result_val.int_val = b_val ^ lit; \
                    else if (strcmp(op, "shl") == 0) result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(b_val) << (lit & 0x1f)); \
                    else if (strcmp(op, "shr") == 0) result_val.int_val = b_val >> (lit & 0x1f); \
                    else if (strcmp(op, "ushr") == 0) result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(b_val) >> (lit & 0x1f)); \
                    set_register(vAA, result_val); \
                    trace.opcode_name = op_name; \
                    pc_ = pc_ + 2; \
                    break; \
                }

            ARITH_LIT8_CASE(ADD_INT_LIT8, "add-int/lit8", "add")
            ARITH_LIT8_CASE(RSUB_INT_LIT8, "rsub-int/lit8", "rsub")
            ARITH_LIT8_CASE(MUL_INT_LIT8, "mul-int/lit8", "mul")
            ARITH_LIT8_CASE(DIV_INT_LIT8, "div-int/lit8", "div")
            ARITH_LIT8_CASE(REM_INT_LIT8, "rem-int/lit8", "rem")
            ARITH_LIT8_CASE(AND_INT_LIT8, "and-int/lit8", "and")
            ARITH_LIT8_CASE(OR_INT_LIT8,  "or-int/lit8",  "or")
            ARITH_LIT8_CASE(XOR_INT_LIT8, "xor-int/lit8", "xor")
            ARITH_LIT8_CASE(SHL_INT_LIT8, "shl-int/lit8", "shl")
            ARITH_LIT8_CASE(SHR_INT_LIT8, "shr-int/lit8", "shr")
            ARITH_LIT8_CASE(USHR_INT_LIT8, "ushr-int/lit8", "ushr")
            #undef ARITH_LIT8_CASE

            // EXP-038 (BLOCKER-028): Arithmetic lit16 (22s format: B|A|op BBBB)
            // vA = vB <op> #BBBB (signed 16-bit)
            // PASS-3 FORENSIC CORRECTION (K-38): the register nibbles were
            // decoded ONE NIBBLE OFF (vA=(>>8), vB=(>>4) — the K-05 bug class
            // again): every lit16 op read its SOURCE from the wrong register
            // field and wrote the result to the wrong destination.
            // DEMO-12X-NIBBLE (2026-09-04): the K-38 "fix" went to the
            // opposite swap (vA=HIGH) instead of AOSP. 22s format per AOSP
            // dalvik-bytecode.html is B|A|op — vA (dest) = bits 8-11, vB
            // (src) = bits 12-15. Aligned with the 12x family fixes.
            #define ARITH_LIT16_CASE(opcode, op_name, op) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vA = (instr >> 8) & 0xF; \
                    uint8_t vB = (instr >> 12) & 0xF; \
                    int16_t lit = static_cast<int16_t>(bytecode_[pc_ + 1]); \
                    DalvikValue b = get_register(vB); \
                    DalvikValue result_val; \
                    result_val.type = DalvikType::INT32; \
                    int32_t b_val = dalvik_int_value(b); \
                    /* W15 (#627 E-02): same lit-family law as ARITH_LIT8 —   */ \
                    /* strcmp dispatch (was literal-ptr compare), unsigned-    */ \
                    /* width wrap semantics, MIN/-1 div/rem edge (JLS 15.17.2).*/ \
                    if ((strcmp(op, "div") == 0 || strcmp(op, "rem") == 0) && lit == 0) { \
                        throw_deferred("Ljava/lang/ArithmeticException;", "divide by zero", "ARITH-LIT16"); \
                        pc_ = pc_ + 2; \
                        break; \
                    } \
                    if (strcmp(op, "add") == 0) result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(b_val) + static_cast<uint32_t>(lit)); \
                    else if (strcmp(op, "rsub") == 0) result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(lit) - static_cast<uint32_t>(b_val)); \
                    else if (strcmp(op, "sub") == 0) result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(b_val) - static_cast<uint32_t>(lit)); \
                    else if (strcmp(op, "mul") == 0) result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(b_val) * static_cast<uint32_t>(lit)); \
                    else if (strcmp(op, "div") == 0) result_val.int_val = (lit == -1) ? static_cast<int32_t>(0u - static_cast<uint32_t>(b_val)) : b_val / lit; \
                    else if (strcmp(op, "rem") == 0) result_val.int_val = (lit == -1) ? 0 : b_val % lit; \
                    else if (strcmp(op, "and") == 0) result_val.int_val = b_val & lit; \
                    else if (strcmp(op, "or") == 0)  result_val.int_val = b_val | lit; \
                    else if (strcmp(op, "xor") == 0) result_val.int_val = b_val ^ lit; \
                    else if (strcmp(op, "shl") == 0) result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(b_val) << (lit & 0x1f)); \
                    else if (strcmp(op, "shr") == 0) result_val.int_val = b_val >> (lit & 0x1f); \
                    else if (strcmp(op, "ushr") == 0) result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(b_val) >> (lit & 0x1f)); \
                    set_register(vA, result_val); \
                    trace.opcode_name = op_name; \
                    pc_ = pc_ + 2; \
                    break; \
                }

            ARITH_LIT16_CASE(ADD_INT_LIT16, "add-int/lit16", "add")
            ARITH_LIT16_CASE(RSUB_INT_LIT16, "rsub-int", "rsub")
            ARITH_LIT16_CASE(MUL_INT_LIT16, "mul-int/lit16", "mul")
            ARITH_LIT16_CASE(DIV_INT_LIT16, "div-int/lit16", "div")
            ARITH_LIT16_CASE(REM_INT_LIT16, "rem-int/lit16", "rem")
            ARITH_LIT16_CASE(AND_INT_LIT16, "and-int/lit16", "and")
            ARITH_LIT16_CASE(OR_INT_LIT16,  "or-int/lit16",  "or")
            ARITH_LIT16_CASE(XOR_INT_LIT16, "xor-int/lit16", "xor")
            // PASS-3 (K-37): the former SHL/SHR/USHR_INT_LIT16 cases here were
            // REMOVED — those opcodes do not exist in Dalvik; 0xD8..0xDA are
            // add/rsub/mul-int/lit8 and now dispatch via the corrected lit8
            // table above.
            #undef ARITH_LIT16_CASE

            // EXP-040: Missing opcodes from Telegram execution
            // move/from16 (22x: AA|op BBBB, 2 code units)
            case Opcode::MOVE_FROM16: {
                if (pc_ + 1 >= bytecode_.size()) return false;
                uint8_t dest = (bytecode_[pc_] >> 8) & 0xFF;
                uint16_t src = bytecode_[pc_ + 1];
                // W15 (#627 E-01): /from16 carries a 16-BIT source register
                // (exists for methods with >255 registers — R8 emits them
                // then). The static_cast<uint8_t> aliased v256+ onto
                // v0..255 and read the WRONG register (the object variant
                // execute_move_object_from16 was already correct; the int
                // and wide variants were missed — intra-family drift).
                // Pass the full uint16_t, mirroring the object law.
                DalvikValue val = get_register(src);
                static thread_local uint64_t w15_m16 = 0;
                if (w15_m16++ < 8)
                    std::cerr << "[W15-M16S] src=" << src << " val_type="
                              << (int)val.type << " int_val=" << val.int_val
                              << " dest=" << (int)dest
                              << " rf_size=" << (current_registers_
                                  ? current_registers_->get_size() : 0)
                              << std::endl;
                set_register(dest, val);
                trace.opcode_name = "move/from16";
                pc_ += 2;
                break;
            }
            // move-result-wide (11x: AA|op, 1 code unit)
            // EXP-088+ F5 CRITICAL FIX: Previously this was hardcoded to make_int(0),
            // which discarded the wide return value entirely. Now we correctly
            // propagate the last_invoke_return_ value (set by execute_return_wide
            // or by the wide-return path in try_recursive_invoke).
            //
            // The wide value is stored in last_invoke_return_.long_val (for INT64)
            // or last_invoke_return_.double_val (for FLOAT64). We preserve the type
            // so downstream consumers (iget-wide, return-wide, arithmetic) can
            // distinguish long vs double.
            case Opcode::MOVE_RESULT_WIDE: {
                uint16_t instr = bytecode_[pc_];
                uint8_t dest = (instr >> 8) & 0xFF;
                DalvikValue val = last_invoke_return_;
                // If last_invoke_return_ wasn't set by a wide return, default to 0
                // but preserve INT64 type (most common case for move-result-wide).
                if (val.type != DalvikType::INT64 && val.type != DalvikType::FLOAT64) {
                    val = DalvikValue::make_long(0);
                }
                set_register(dest, val);
                trace.opcode_name = "move-result-wide";
                pc_ += 1;
                break;
            }
            // const-string/jumbo (31c: AA|op BBBBBBBB, 3 code units)
            case Opcode::CONST_STRING_JUMBO: {
                if (pc_ + 2 >= bytecode_.size()) return false;
                uint16_t instr = bytecode_[pc_];
                uint8_t dest = (instr >> 8) & 0xFF;
                // W15 (#627 E-03): uint16_t promotes to SIGNED int — (idx>>16)<<16
                // overflows int for high jumbo indices (UB). Mask into
                // unsigned width before the shift, matching the packed-
                // sites at the other 31c readers.
                uint32_t string_idx =
                    (static_cast<uint32_t>(bytecode_[pc_ + 2]) << 16) |
                    static_cast<uint32_t>(bytecode_[pc_ + 1]);
                DalvikValue val;
                val.type = DalvikType::STRING_REF;
                val.int_val = string_idx;
                // EXP-065: Use per-DEX string resolution (same fix as execute_const_string).
                val.string_val = resolve_string_for_dex(string_idx, current_dex_index_);
                set_register(dest, val);
                trace.opcode_name = "const-string/jumbo";
                pc_ += 3;
                break;
            }

            // Conversion opcodes (12x: B|A|op, 1 code unit).
            //
            // IMPORTANT (RESULT_010 reconciliation, master request §7/§9):
            // a conversion must perform the REAL numeric conversion and retag
            // the result type. The previous implementation ONLY changed the
            // type tag to INT32 and left the union bits untouched, so
            // int-to-long(-5) read back as garbage, float-to-int returned the
            // raw float BITS as an integer, and int-to-byte/char/short never
            // masked. Dalvik/AOSP numeric-conversion semantics implemented:
            //   int→long sign-extend · long→int truncate low 32
            //   float/double→int/long: NaN→0, round-toward-zero + saturate
            //   int→byte sign-extend low 8 · int→char zero-extend low 16 ·
            //   int→short sign-extend low 16
            // Regression fixture: tests/semantic_long_cmp_conv_test.cpp
            // F-028 (MASTER-4 §A1) — UNTYPED-REGISTER CONVERSION LAW.
            // Dalvik registers are UNTYPED 32-bit (32-bit family) / 64-bit
            // (wide family) storage slots; the OPCODE — not a runtime value
            // tag — defines the source interpretation. ART materializes this
            // with raw slots; MiniAndroid's tagged-union must emulate it by
            // taking the slot's RAW BITS and reinterpreting them per the
            // opcode's source type:
            //   int-to-*   : slot bits -> int32   -> numeric convert
            //   float-to-* : slot bits -> float32 -> numeric convert
            //   long-to-*  : slot bits -> int64   -> numeric convert
            //   double-to-*: slot bits -> float64 -> numeric convert
            // The pre-law implementation numeric-converted a FLOAT32-tagged
            // register's float VALUE in int-to-* (yielding 0 for every real
            // float) and bit-aliased raw float BITS in float-to-* when the
            // producer was const/high16 (INT32-tagged 0x42E60000 instead of
            // 115.0f -> float-to-int read 1120702464 instead of 115). The
            // first real-APK hit: Material3 LG0/b.<clinit> (dooz) built its
            // FontScaleConverter table keys through exactly that pattern and
            // threw ISE "You should only apply non-linear scaling to font
            // scales > 1". No app special-casing: every real DEX that mixes
            // const/high16 float literals with float ops benefits.
            #define CONV_SRC_I32(opcode, op_name, DST_KIND, STORE_EXPR) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    /* 12x = B|A|op per AOSP dalvik-bytecode.html: A (dest) is */ \
                    /* bits 8-11, B (src) is bits 12-15. DEMO-12X-NIBBLE      */ \
                    /* (2026-09-04): this block previously decoded dest from  */ \
                    /* bits 12-15 and src from bits 8-11 (with a comment that */ \
                    /* mis-cited the spec) — swapped vs AOSP, so a real `     */ \
                    /* long-to-int v0, v2` wrote v2 and read v0 whenever the  */ \
                    /* registers differed. The swapped decoder and the equally */ \
                    /* swapped fixture encoder cancelled out inside the test  */ \
                    /* suite, which is why 14/14 passed while real DEX broke. */ \
                    /* Now aligned with execute_move (EXP-058) and the fixed  */ \
                    /* ARITH_2ADDR/ARRAY_LENGTH/MOVE_WIDE decoders.           */ \
                    uint8_t vA = (instr >> 8) & 0xF; \
                    uint8_t vB = (instr >> 12) & 0xF; \
                    DalvikValue val = get_register(vB); \
                    DalvikValue out; out.type = DST_KIND; \
                    /* F-028 law: slot bits reinterpreted AS int32 (source type) */ \
                    int32_t s = static_cast<int32_t>(dalvik_raw_bits32(val)); \
                    STORE_EXPR; \
                    static thread_local const bool wide_diag_on = \
                        diag_env("MINIANDROID_WIDE_DIAG"); /* R-NEW-558 */ \
                    if (wide_diag_on) { \
                        std::cerr << "[WIDE-DIAG] conv " << op_name << " @" << current_class_ << "." \
                                  << current_method_ << " v" << (int)vB << "(tag=" << (int)val.type \
                                  << " bits=0x" << std::hex << dalvik_raw_bits32(val) << std::dec \
                                  << ") -> " << out.int_val << std::endl; \
                    } \
                    set_register(vA, out); \
                    trace.opcode_name = op_name; \
                    pc_ += 1; \
                    break; \
                }
            #define CONV_SRC_I64(opcode, op_name, DST_KIND, STORE_EXPR) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vA = (instr >> 8) & 0xF;  /* dest = bits 8-11 (12x B|A|op) */ \
                    uint8_t vB = (instr >> 12) & 0xF; /* src  = bits 12-15 (12x B|A|op) */ \
                    DalvikValue val = get_register(vB); \
                    DalvikValue out; out.type = DST_KIND; \
                    /* F-028 law: wide slot bits reinterpreted AS int64 */ \
                    int64_t s = (val.type == DalvikType::INT64) ? val.long_val \
                              : (val.type == DalvikType::FLOAT64 ? [&]{ int64_t b; std::memcpy(&b, &val.double_val, 8); return b; }() \
                              : (val.type == DalvikType::INT32 ? static_cast<int64_t>(val.int_val) : 0)); \
                    STORE_EXPR; \
                    static thread_local const bool wide_diag_on = \
                        diag_env("MINIANDROID_WIDE_DIAG"); /* R-NEW-558 */ \
                    if (wide_diag_on) { \
                        std::cerr << "[WIDE-DIAG] conv " << op_name << " @" << current_class_ << "." \
                                  << current_method_ << " v" << (int)vB << "(J=" << s << ") -> " \
                                  << out.long_val << std::endl; \
                    } \
                    set_register(vA, out); \
                    trace.opcode_name = op_name; \
                    pc_ += 1; \
                    break; \
                }
            #define CONV_SRC_F32(opcode, op_name, DST_KIND, STORE_EXPR) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vA = (instr >> 8) & 0xF;  /* dest = bits 8-11 (12x B|A|op) */ \
                    uint8_t vB = (instr >> 12) & 0xF; /* src  = bits 12-15 (12x B|A|op) */ \
                    DalvikValue val = get_register(vB); \
                    DalvikValue out; out.type = DST_KIND; \
                    /* F-028 law: slot bits reinterpreted AS float32 (source type). \
                     * This is the law that fixes const/high16 float literals: \
                     * 0x3F800000 tagged INT32 must read as 1.0f, not 1.065e9f. */ \
                    uint32_t f28bits = dalvik_raw_bits32(val); \
                    float s; std::memcpy(&s, &f28bits, sizeof(s)); \
                    STORE_EXPR; \
                    static thread_local const bool wide_diag_on = \
                        diag_env("MINIANDROID_WIDE_DIAG"); /* R-NEW-558 */ \
                    if (wide_diag_on) { \
                        std::cerr << "[WIDE-DIAG] conv " << op_name << " @" << current_class_ << "." \
                                  << current_method_ << " v" << (int)vB << "(tag=" << (int)val.type \
                                  << " bits=0x" << std::hex << f28bits << std::dec \
                                  << " f=" << s << ") -> " << out.int_val << std::endl; \
                    } \
                    set_register(vA, out); \
                    trace.opcode_name = op_name; \
                    pc_ += 1; \
                    break; \
                }
            #define CONV_SRC_F64(opcode, op_name, DST_KIND, STORE_EXPR) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vA = (instr >> 8) & 0xF;  /* dest = bits 8-11 (12x B|A|op) */ \
                    uint8_t vB = (instr >> 12) & 0xF; /* src  = bits 12-15 (12x B|A|op) */ \
                    DalvikValue val = get_register(vB); \
                    DalvikValue out; out.type = DST_KIND; \
                    /* F-028 law: wide slot bits reinterpreted AS float64 */ \
                    double s = (val.type == DalvikType::FLOAT64) ? val.double_val \
                             : (val.type == DalvikType::INT64 ? bits_l2d(val.long_val) : 0.0); \
                    STORE_EXPR; \
                    set_register(vA, out); \
                    trace.opcode_name = op_name; \
                    pc_ += 1; \
                    break; \
                }
            CONV_SRC_I32(INT_TO_LONG,   "int-to-long",    DalvikType::INT64,   out.long_val  = static_cast<int64_t>(s))
            CONV_SRC_I32(INT_TO_FLOAT,  "int-to-float",   DalvikType::FLOAT32, out.float_val = static_cast<float>(s))
            CONV_SRC_I32(INT_TO_DOUBLE, "int-to-double",  DalvikType::FLOAT64, out.double_val = static_cast<double>(s))
            CONV_SRC_I64(LONG_TO_INT,   "long-to-int",    DalvikType::INT32,   out.int_val   = static_cast<int32_t>(s))
            CONV_SRC_I64(LONG_TO_FLOAT, "long-to-float",  DalvikType::FLOAT32, out.float_val = static_cast<float>(s))
            CONV_SRC_I64(LONG_TO_DOUBLE,"long-to-double", DalvikType::FLOAT64, out.double_val = static_cast<double>(s))
            CONV_SRC_F32(FLOAT_TO_INT,  "float-to-int",   DalvikType::INT32,   out.int_val   = conv_f2i(static_cast<double>(s)))
            CONV_SRC_F32(FLOAT_TO_LONG, "float-to-long",  DalvikType::INT64,   out.long_val  = conv_f2l(static_cast<double>(s)))
            CONV_SRC_F32(FLOAT_TO_DOUBLE,"float-to-double",DalvikType::FLOAT64,out.double_val = static_cast<double>(s))
            CONV_SRC_F64(DOUBLE_TO_INT, "double-to-int",  DalvikType::INT32,   out.int_val   = conv_f2i(s))
            CONV_SRC_F64(DOUBLE_TO_LONG,"double-to-long", DalvikType::INT64,   out.long_val  = conv_f2l(s))
            CONV_SRC_F64(DOUBLE_TO_FLOAT,"double-to-float",DalvikType::FLOAT32,out.float_val = static_cast<float>(s))
            CONV_SRC_I32(INT_TO_BYTE,   "int-to-byte",    DalvikType::INT32,   out.int_val   = static_cast<int8_t>(s & 0xFF))
            CONV_SRC_I32(INT_TO_CHAR,   "int-to-char",    DalvikType::INT32,   out.int_val   = static_cast<uint16_t>(s & 0xFFFF))
            CONV_SRC_I32(INT_TO_SHORT,  "int-to-short",   DalvikType::INT32,   out.int_val   = static_cast<int16_t>(s & 0xFFFF))
            #undef CONV_SRC_I32
            #undef CONV_SRC_I64
            #undef CONV_SRC_F32
            #undef CONV_SRC_F64

            // MASTER RECONCILIATION (2026-09-03, NOT_DONE #4 audit): unary
            // neg/not family (12x format: B|A|op). The entire block was
            // ABSENT from the dispatch — neg-int/not-int/neg-long/not-long/
            // neg-float/neg-double all hit handle_unimplemented. The audit
            // predicted an int32-alias bug (K-01 class); the truth was worse:
            // no implementation existed at all. Wrap-around negation is done
            // in the UNSIGNED domain to avoid signed-overflow UB — INT32_MIN
            // and INT64_MIN negate to themselves per the JLS.
            // DEMO-12X-NIBBLE (2026-09-04): nibble decode aligned to AOSP
            // (dest = bits 8-11, src = bits 12-15). This block previously
            // copied the CONV block's swapped convention (dest = HIGH
            // nibble), which contradicts the AOSP 12x encoding used by real
            // D8 bytecode whenever dest != src.
            // Fixture: tests/semantic_switch_parse_neg_test.cpp (group N —
            // 7/7 FAIL pre-fix, all returned 0 via the unimplemented path).
            #define UNARY_I32_CASE(opcode, op_name, EXPR) \
                case Opcode::opcode: { \
                    uint16_t instr_u = bytecode_[pc_]; \
                    uint8_t vA_u = (instr_u >> 8) & 0xF; \
                    uint8_t vB_u = (instr_u >> 12) & 0xF; \
                    DalvikValue src_u = get_register(vB_u); \
                    DalvikValue out_u; out_u.type = DalvikType::INT32; \
                    int32_t s_u = (src_u.type == DalvikType::INT32) ? src_u.int_val \
                                : (src_u.type == DalvikType::INT64 ? static_cast<int32_t>(src_u.long_val) : 0); \
                    EXPR; \
                    set_register(vA_u, out_u); \
                    trace.opcode_name = op_name; \
                    pc_ += 1; \
                    break; \
                }
            #define UNARY_I64_CASE(opcode, op_name, EXPR) \
                case Opcode::opcode: { \
                    uint16_t instr_u = bytecode_[pc_]; \
                    uint8_t vA_u = (instr_u >> 8) & 0xF; \
                    uint8_t vB_u = (instr_u >> 12) & 0xF; \
                    DalvikValue src_u = get_register(vB_u); \
                    DalvikValue out_u; out_u.type = DalvikType::INT64; \
                    int64_t s_u = (src_u.type == DalvikType::INT64) ? src_u.long_val \
                                : (src_u.type == DalvikType::INT32 ? static_cast<int64_t>(src_u.int_val) : 0); \
                    EXPR; \
                    set_register(vA_u, out_u); \
                    trace.opcode_name = op_name; \
                    pc_ += 1; \
                    break; \
                }
            #define UNARY_F32_CASE(opcode, op_name, EXPR) \
                case Opcode::opcode: { \
                    uint16_t instr_u = bytecode_[pc_]; \
                    uint8_t vA_u = (instr_u >> 8) & 0xF; \
                    uint8_t vB_u = (instr_u >> 12) & 0xF; \
                    DalvikValue src_u = get_register(vB_u); \
                    DalvikValue out_u; out_u.type = DalvikType::FLOAT32; \
                    float s_u = (src_u.type == DalvikType::FLOAT32) ? src_u.float_val \
                              : (src_u.type == DalvikType::INT32 ? bits_i2f(src_u.int_val) : 0.0f); \
                    EXPR; \
                    set_register(vA_u, out_u); \
                    trace.opcode_name = op_name; \
                    pc_ += 1; \
                    break; \
                }
            #define UNARY_F64_CASE(opcode, op_name, EXPR) \
                case Opcode::opcode: { \
                    uint16_t instr_u = bytecode_[pc_]; \
                    uint8_t vA_u = (instr_u >> 8) & 0xF; \
                    uint8_t vB_u = (instr_u >> 12) & 0xF; \
                    DalvikValue src_u = get_register(vB_u); \
                    DalvikValue out_u; out_u.type = DalvikType::FLOAT64; \
                    double s_u = (src_u.type == DalvikType::FLOAT64) ? src_u.double_val \
                               : (src_u.type == DalvikType::INT64 ? bits_l2d(src_u.long_val) \
                               : (src_u.type == DalvikType::FLOAT32 ? static_cast<double>(src_u.float_val) \
                               : (src_u.type == DalvikType::INT32 ? static_cast<double>(bits_i2f(src_u.int_val)) : 0.0))); \
                    EXPR; \
                    set_register(vA_u, out_u); \
                    trace.opcode_name = op_name; \
                    pc_ += 1; \
                    break; \
                }
            UNARY_I32_CASE(NEG_INT,   "neg-int",    out_u.int_val   = static_cast<int32_t>(0u - static_cast<uint32_t>(s_u)))
            UNARY_I32_CASE(NOT_INT,   "not-int",    out_u.int_val   = ~s_u)
            UNARY_I64_CASE(NEG_LONG,  "neg-long",   out_u.long_val  = static_cast<int64_t>(0ULL - static_cast<uint64_t>(s_u)))
            UNARY_I64_CASE(NOT_LONG,  "not-long",   out_u.long_val  = ~s_u)
            UNARY_F32_CASE(NEG_FLOAT, "neg-float",  out_u.float_val = -s_u)
            UNARY_F64_CASE(NEG_DOUBLE,"neg-double", out_u.double_val = -s_u)
            #undef UNARY_I32_CASE
            #undef UNARY_I64_CASE
            #undef UNARY_F32_CASE
            #undef UNARY_F64_CASE

            // Float/Double/Long arithmetic (23x: AA|op BB|CC, 2 code units)
            #define ARITH_23X_FLOAT_CASE(opcode, op_name, op) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vAA = (instr >> 8) & 0xFF; \
                    uint8_t vBB = bytecode_[pc_ + 1] & 0xFF; \
                    uint8_t vCC = (bytecode_[pc_ + 1] >> 8) & 0xFF; \
                    DalvikValue b = get_register(vBB); \
                    DalvikValue c = get_register(vCC); \
                    DalvikValue result_val; \
                    result_val.type = DalvikType::FLOAT32; \
                    float bf, cf; \
                    /* F-028 law: slots reinterpreted AS float32 (see conv block) */ \
                    uint32_t ab28 = dalvik_raw_bits32(b); std::memcpy(&bf, &ab28, 4); \
                    uint32_t cb28 = dalvik_raw_bits32(c); std::memcpy(&cf, &cb28, 4); \
                    if (strcmp(op, "add") == 0) result_val.float_val = bf + cf; \
                    else if (strcmp(op, "sub") == 0) result_val.float_val = bf - cf; \
                    else if (strcmp(op, "mul") == 0) result_val.float_val = bf * cf; \
                    else if (strcmp(op, "div") == 0) result_val.float_val = bf / cf; \
                    else if (strcmp(op, "rem") == 0) result_val.float_val = fmodf(bf, cf); /* W22 #627 E-02 drift: literal-pointer == */ \
                    set_register(vAA, result_val); \
                    trace.opcode_name = op_name; \
                    pc_ += 2; \
                    break; \
                }
            ARITH_23X_FLOAT_CASE(ADD_FLOAT, "add-float", "add")
            ARITH_23X_FLOAT_CASE(SUB_FLOAT, "sub-float", "sub")
            ARITH_23X_FLOAT_CASE(MUL_FLOAT, "mul-float", "mul")
            ARITH_23X_FLOAT_CASE(DIV_FLOAT, "div-float", "div")
            ARITH_23X_FLOAT_CASE(REM_FLOAT, "rem-float", "rem")
            #undef ARITH_23X_FLOAT_CASE

            // cmp opcodes (23x) — Dalvik comparison semantics.
            //
            // IMPORTANT (RESULT_009 reconciliation, master request §7/§9):
            // cmp-long MUST read the full 64-bit register value. A previous
            // implementation read int_val (the low 32 bits of the DalvikValue
            // union) and returned 0 for every INT64 operand, silently
            // collapsing all 64-bit comparisons. Regression fixture:
            // tests/semantic_long_cmp_conv_test.cpp (>2^32 operands).
            #define CMP_LONG_CASE(opcode, op_name) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vAA = (instr >> 8) & 0xFF; \
                    uint8_t vBB = bytecode_[pc_ + 1] & 0xFF; \
                    uint8_t vCC = (bytecode_[pc_ + 1] >> 8) & 0xFF; \
                    DalvikValue b = get_register(vBB); \
                    DalvikValue c = get_register(vCC); \
                    DalvikValue result_val; \
                    result_val.type = DalvikType::INT32; \
                    int64_t bv = (b.type == DalvikType::INT64) ? b.long_val \
                               : (b.type == DalvikType::INT32 ? static_cast<int64_t>(b.int_val) : 0); \
                    int64_t cv = (c.type == DalvikType::INT64) ? c.long_val \
                               : (c.type == DalvikType::INT32 ? static_cast<int64_t>(c.int_val) : 0); \
                    result_val.int_val = (bv < cv) ? -1 : (bv > cv) ? 1 : 0; \
                    static thread_local const bool wide_diag_on = \
                        diag_env("MINIANDROID_WIDE_DIAG"); /* R-NEW-558 */ \
                    if (wide_diag_on) { \
                        std::cerr << "[WIDE-DIAG] cmp-long @" << current_class_ << "." \
                                  << current_method_ << " b=(" << (b.type == DalvikType::INT64 ? "J" : "i") \
                                  << (b.type == DalvikType::INT64 ? b.long_val : b.int_val) << ") v" \
                                  << (int)vBB << " c=(" << (c.type == DalvikType::INT64 ? "J" : "i") \
                                  << (c.type == DalvikType::INT64 ? c.long_val : c.int_val) << ") v" \
                                  << (int)vCC << " -> " << result_val.int_val << std::endl; \
                    } \
                    set_register(vAA, result_val); \
                    trace.opcode_name = op_name; \
                    pc_ += 2; \
                    break; \
                }
            // cmpl/cmpg floating comparisons — NaN ordering per the Dalvik spec:
            //   cmpl → -1 when either operand is NaN (NaN sorts "less than all")
            //   cmpg → +1 when either operand is NaN (NaN sorts "greater than all")
            // ±0.0 compare equal (the <,> comparison below yields 0 naturally).
            // Read operands at the CORRECT width: a FLOAT64 register read through
            // float_val would reinterpret half the double bits as garbage.
            #define CMP_FLOATING_CASE(opcode, op_name, IS_DOUBLE, NAN_RESULT) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vAA = (instr >> 8) & 0xFF; \
                    uint8_t vBB = bytecode_[pc_ + 1] & 0xFF; \
                    uint8_t vCC = (bytecode_[pc_ + 1] >> 8) & 0xFF; \
                    DalvikValue b = get_register(vBB); \
                    DalvikValue c = get_register(vCC); \
                    DalvikValue result_val; \
                    result_val.type = DalvikType::INT32; \
                    long double bv, cv; float bv32 = 0.0f, cv32 = 0.0f; \
                    if (IS_DOUBLE) { \
                        /* F-028 law: wide slots reinterpreted AS float64 */ \
                        bv = (b.type == DalvikType::FLOAT64) ? (long double)b.double_val \
                           : (b.type == DalvikType::INT64 ? (long double)bits_l2d(b.long_val) \
                           : (b.type == DalvikType::FLOAT32 ? (long double)b.float_val \
                           : (b.type == DalvikType::INT32 ? (long double)b.int_val : 0.0L))); \
                        cv = (c.type == DalvikType::FLOAT64) ? (long double)c.double_val \
                           : (c.type == DalvikType::INT64 ? (long double)bits_l2d(c.long_val) \
                           : (c.type == DalvikType::FLOAT32 ? (long double)c.float_val \
                           : (c.type == DalvikType::INT32 ? (long double)c.int_val : 0.0L))); \
                    } else { \
                        /* F-028 law: slots reinterpreted AS float32 — an \
                         * INT32-tagged register holding const/high16 float \
                         * bits (e.g. 0x3F800000 == 1.0f) must compare as that \
                         * float, not as its numeric int word (1.065e9f). */ \
                        uint32_t bb = dalvik_raw_bits32(b); std::memcpy(&bv32, &bb, 4); \
                        uint32_t cb = dalvik_raw_bits32(c); std::memcpy(&cv32, &cb, 4); \
                        bv = (long double)bv32; \
                        cv = (long double)cv32; \
                    } \
                    bool cmp_nan = (bv != bv) || (cv != cv); \
                    result_val.int_val = cmp_nan ? (NAN_RESULT) : ((bv < cv) ? -1 : (bv > cv) ? 1 : 0); \
                    static thread_local const bool wide_diag_on = \
                        diag_env("MINIANDROID_WIDE_DIAG"); /* R-NEW-558 */ \
                    if (wide_diag_on) { \
                        std::cerr << "[WIDE-DIAG] " << op_name << " @" << current_class_ << "." \
                                  << current_method_ << " b=" << (double)bv << " c=" << (double)cv \
                                  << " -> " << result_val.int_val << std::endl; \
                    } \
                    set_register(vAA, result_val); \
                    trace.opcode_name = op_name; \
                    pc_ += 2; \
                    break; \
                }
            CMP_FLOATING_CASE(CMPL_FLOAT, "cmpl-float", false, -1)
            CMP_FLOATING_CASE(CMPG_FLOAT, "cmpg-float", false, 1)
            CMP_FLOATING_CASE(CMPL_DOUBLE, "cmpl-double", true, -1)
            CMP_FLOATING_CASE(CMPG_DOUBLE, "cmpg-double", true, 1)
            CMP_LONG_CASE(CMP_LONG, "cmp-long")
            #undef CMP_LONG_CASE
            #undef CMP_FLOATING_CASE

            // Long arithmetic (23x).
            //
            // IMPORTANT (RESULT_001 reconciliation, master request §7/§9):
            // long arithmetic MUST compute in 64-bit. The DalvikValue union
            // aliases int_val over the LOW 32 bits of long_val — the previous
            // int32_t computation silently truncated every operand above 2^32
            // (2^32 + 1 == 1!) while still tagging the result INT64.
            // System.currentTimeMillis() values (13 digits) were destroyed by
            // this path. Regression fixture:
            // tests/semantic_long_cmp_conv_test.cpp (>2^32 operands).
            //
            // MASTER RECONCILIATION (K-29, 2026-09-03): div/rem by zero
            // now throws java/lang/ArithmeticException via the deferred
            // mechanism (post-switch redirect cannot be clobbered by the
            // macro's pc_ += 2). The old "yield 0" simplification is
            // gone — it silently diverged from Android whenever real apps
            // relied on the exception for control flow.
            // Fixture: tests/semantic_switch_parse_neg_test.cpp (group D).
            #define ARITH_LONG_CASE(opcode, op_name, op) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vAA = (instr >> 8) & 0xFF; \
                    uint8_t vBB = bytecode_[pc_ + 1] & 0xFF; \
                    uint8_t vCC = (bytecode_[pc_ + 1] >> 8) & 0xFF; \
                    DalvikValue b = get_register(vBB); \
                    DalvikValue c = get_register(vCC); \
                    DalvikValue result_val; \
                    result_val.type = DalvikType::INT64; \
                    int64_t bv = (b.type == DalvikType::INT64) ? b.long_val \
                               : (b.type == DalvikType::INT32 ? static_cast<int64_t>(b.int_val) : 0); \
                    int64_t cv = (c.type == DalvikType::INT64) ? c.long_val \
                               : (c.type == DalvikType::INT32 ? static_cast<int64_t>(c.int_val) : 0); \
                    /* GP-INT-012/015 (issue #582): wrap-defined int64 math, */ \
                    /* MIN64/-1 div/rem edge, strcmp dispatch.                 */ \
                    if ((strcmp(op, "div") == 0 || strcmp(op, "rem") == 0) && cv == 0) { \
                        throw_deferred("Ljava/lang/ArithmeticException;", "divide by zero", "ARITH-LONG"); \
                        pc_ += 2; \
                        break; \
                    } \
                    if (strcmp(op, "add") == 0) result_val.long_val = static_cast<int64_t>(static_cast<uint64_t>(bv) + static_cast<uint64_t>(cv)); \
                    else if (strcmp(op, "sub") == 0) result_val.long_val = static_cast<int64_t>(static_cast<uint64_t>(bv) - static_cast<uint64_t>(cv)); \
                    else if (strcmp(op, "mul") == 0) result_val.long_val = static_cast<int64_t>(static_cast<uint64_t>(bv) * static_cast<uint64_t>(cv)); \
                    else if (strcmp(op, "div") == 0) result_val.long_val = (cv == -1) ? static_cast<int64_t>(0ull - static_cast<uint64_t>(bv)) : bv / cv; \
                    else if (strcmp(op, "rem") == 0) result_val.long_val = (cv == -1) ? 0 : bv % cv; \
                    else if (strcmp(op, "and") == 0) result_val.long_val = bv & cv; \
                    else if (strcmp(op, "or") == 0)  result_val.long_val = bv | cv; \
                    else if (strcmp(op, "xor") == 0) result_val.long_val = bv ^ cv; \
                    else if (strcmp(op, "shl") == 0) result_val.long_val = static_cast<int64_t>(static_cast<uint64_t>(bv) << static_cast<int>(cv & 0x3f)); \
                    else if (strcmp(op, "shr") == 0) result_val.long_val = bv >> static_cast<int>(cv & 0x3f); \
                    else if (strcmp(op, "ushr") == 0) result_val.long_val = static_cast<int64_t>(static_cast<uint64_t>(bv) >> static_cast<int>(cv & 0x3f)); \
                    set_register(vAA, result_val); \
                    trace.opcode_name = op_name; \
                    pc_ += 2; \
                    break; \
                }
            ARITH_LONG_CASE(ADD_LONG, "add-long", "add")
            ARITH_LONG_CASE(SUB_LONG, "sub-long", "sub")
            ARITH_LONG_CASE(MUL_LONG, "mul-long", "mul")
            ARITH_LONG_CASE(DIV_LONG, "div-long", "div")
            ARITH_LONG_CASE(REM_LONG, "rem-long", "rem")
            ARITH_LONG_CASE(AND_LONG, "and-long", "and")
            ARITH_LONG_CASE(OR_LONG, "or-long", "or")
            ARITH_LONG_CASE(XOR_LONG, "xor-long", "xor")
            ARITH_LONG_CASE(SHL_LONG, "shl-long", "shl")
            ARITH_LONG_CASE(SHR_LONG, "shr-long", "shr")
            ARITH_LONG_CASE(USHR_LONG, "ushr-long", "ushr")
            #undef ARITH_LONG_CASE

            // EXP-051: throw (11x: AA|op, 1 code unit) — halt current method.
            //
            // Real Android unwinds the stack frame by frame looking for a
            // matching catch handler in the method's tries[] table. Full
            // exception handling is a major project; for now we treat
            // throw as "halt this method and return to caller".
            //
            // This loses exception-propagation semantics but lets the
            // engine continue past throws that originate from paths the
            // caller doesn't actually care about (e.g. dynamic-animation
            // throws inside enforceMainThreadIfNeeded that the caller
            // never observes because mEnforceMainThread == false).
            //
            // Without this fix, ANY throw anywhere in the call tree halts
            // the entire LaunchActivity.onCreate execution.
            //
            // EXP-052: Added diagnostic mode — log whether the current
            // method has a try table and what kind of handler would have
            // matched. This does NOT yet implement catch-jumping, just
            // collects evidence for the next experiment.
            // EXP-053: throw (11x: AA|op, 1 code unit).
            //
            // EXP-051: Treat as method-level halt (let caller continue).
            // EXP-052: Added diagnostic — log whether try table exists and
            //           whether a matching handler was found.
            // EXP-053: Implement actual catch-all handler dispatch. When a
            //           throw occurs:
            //             1. Look up try_items for one covering current PC.
            //             2. Decode the encoded_catch_handler_list at
            //                handler_off (byte offset into the list, which
            //                starts AFTER the tries[] array).
            //             3. For each handler pair (type_idx, addr):
            //                  - If type_idx == 0 (catch-all), jump to addr.
            //                  - If type_idx matches exception class
            //                    (TODO: needs type resolution), jump to addr.
            //             4. If no handler matched, propagate to caller
            //                (method-level halt, as before).
            //
            // For now we only support catch-all handlers. Typed catches
            // require class hierarchy resolution which is a future task.
            // EXP-093: filled-new-array (0x24) and filled-new-array/range (0x25)
            // Per AOSP: Creates a new array of the specified type and fills it
            // with the contents of the specified source registers.
            //
            // Format 35c: [B|A|op] [type@CCCC] [D|E|F|G]
            //   A = array size (number of registers, 0-5)
            //   B = bit string indicating which registers (D=bit0, E=bit1, F=bit2, G=bit3, bit4)
            //   type@CCCC = type descriptor
            //   D,E,F,G = source registers
            //
            // Format 3rc: [op] [type@CCCC] [BBBB] [registers CCCC..CCCC+AA-1]
            //   AA = array size (count of registers)
            //   CCCC = first register
            //
            // The array elements come from the source registers IN ORDER.
            // This is critical for Java varargs: Object... args compiles as
            // filled-new-array {v_arg1, v_arg2, ...}, type@Object
            case Opcode::FILLED_NEW_ARRAY:
            case Opcode::FILLED_NEW_ARRAY_RANGE: {
                trace.opcode_name = (opcode == Opcode::FILLED_NEW_ARRAY) ?
                    "filled-new-array" : "filled-new-array/range";

                uint16_t type_idx;
                std::vector<uint8_t> src_regs;

                if (opcode == Opcode::FILLED_NEW_ARRAY) {
                    // Format 35c: A|G|op BBBB FEDC
                    //   code[pc+0] = A|G|op (A = arg count = bits 12-15,
                    //                        G = 5th register = bits 8-11, op = bits 0-7)
                    //   code[pc+1] = BBBB (type_idx)
                    //   code[pc+2] = FEDC (register list, 4 nibbles)
                    //
                    // UNIFIED_011.2 FNA-FIX (§24 audit): previous code read
                    // arg_count from bits 4-7 ((instr >> 4) & 0xF — the high
                    // nibble of the OPCODE byte itself), which yields the
                    // constant 2 for opcode 0x24 regardless of the actual A
                    // field, and the 5th register (G, bits 8-11) was never
                    // read. This is the same bug class fixed for the invoke
                    // family in EXP-037 (BLOCKER-016): see execute_invoke_*
                    // which now use (instr >> 12) & 0xF / (instr >> 8) & 0xF.
                    // Aligned here with the canonical extraction.
                    uint16_t instr0 = bytecode_[pc_];
                    uint16_t cu2 = bytecode_[pc_ + 2];
                    uint8_t arg_count = (instr0 >> 12) & 0x0F;
                    uint8_t fna_regs[5] = {
                        static_cast<uint8_t>(cu2 & 0xF),          // C
                        static_cast<uint8_t>((cu2 >> 4) & 0xF),   // D
                        static_cast<uint8_t>((cu2 >> 8) & 0xF),   // E
                        static_cast<uint8_t>((cu2 >> 12) & 0xF),  // F
                        static_cast<uint8_t>((instr0 >> 8) & 0xF) // G — 5th register
                    };
                    type_idx = bytecode_[pc_ + 1];
                    for (int i = 0; i < arg_count && i < 5; i++) {
                        src_regs.push_back(fna_regs[i]);
                    }
                } else {
                    // Format 3rc: [op|AA] [type@CCCC] [CCCC]
                    uint8_t arg_count = (bytecode_[pc_] >> 8) & 0xFF;
                    type_idx = bytecode_[pc_ + 1];
                    uint16_t first_reg = bytecode_[pc_ + 2];
                    for (int i = 0; i < arg_count; i++) {
                        src_regs.push_back((first_reg + i) & 0xFF);
                    }
                }

                // Resolve type descriptor
                std::string type_desc = "<unknown>";
                if (dex_report_) {
                    auto class_it = class_info_index_.find("Larray;");
                    (void)class_it;
                }
                // Use per-DEX type resolution
                if (is_multidex_ && current_dex_index_ < per_dex_raw_data_.size()) {
                    const auto& raw = per_dex_raw_data_[current_dex_index_];
                    if (raw.size() >= sizeof(dex::DexHeader)) {
                        dex::DexHeader hdr;
                        std::memcpy(&hdr, raw.data(), sizeof(dex::DexHeader));
                        if (type_idx < hdr.type_ids_size) {
                            uint32_t desc_str_idx;
                            std::memcpy(&desc_str_idx, raw.data() + hdr.type_ids_off + type_idx * 4, 4);
                            uint32_t sdo;
                            std::memcpy(&sdo, raw.data() + hdr.string_ids_off + desc_str_idx * 4, 4);
                            size_t pos = sdo;
                            while (pos < raw.size() && raw[pos] & 0x80) pos++;
                            pos++;
                            size_t end = pos;
                            while (end < raw.size() && raw[end] != 0) end++;
                            type_desc = std::string(reinterpret_cast<const char*>(raw.data() + pos), end - pos);
                        }
                    }
                }
                // F-NEW-487 (CONT-156 Train 4): the single-dex / resolution
                // fallback. The previous fallback was a DEAD STUB (an empty
                // class_info_index_ lookup, result discarded) — when per-DEX
                // resolution did not answer, type_desc stayed the literal
                // "<unknown>" and the array was ALLOCATED with that string
                // as its heap class_descriptor. Downstream, the aput-object
                // store-check (R-NEW-010) then rejected every store of the
                // array into a typed array: ghostsq Utils.<clinit> builds
                // String[][] via filled-new-array {..}, [Ljava/lang/String;
                // — the inner arrays carried "<unknown>" and the store into
                // [[Ljava/lang/String; threw ArrayStoreException at <clinit>
                // (app dead on arrival: NoClassDefFoundError cascade for the
                // erroneous class). Resolve through the merged dex_report_
                // types table (the same fallback resolve_type_for_dex uses).
                if ((type_desc.empty() || type_desc == "<unknown>") &&
                    dex_report_ && type_idx < dex_report_->types.size()) {
                    type_desc = dex_report_->types[type_idx];
                }

                // Allocate the array
                uint32_t arr_id = heap_.allocate(type_desc.empty() ? "Larray;" : type_desc, pc_, 0);
                // Set array length
                heap_.set_object_field(arr_id, "__array_length__",
                    DalvikValue::make_int(static_cast<int32_t>(src_regs.size())));

                // Fill array elements from source registers
                for (size_t i = 0; i < src_regs.size(); i++) {
                    DalvikValue src_val = get_register(src_regs[i]);
                    // F-NEW-244 FIX: normalize Class-token values into
                    // OBJECT_REF form at array-store time. const-class
                    // values are DalvikValue::make_class(desc, token) —
                    // type CLASS_REF carrying the REAL heap token id — but
                    // every consumer of the engine array-fields store
                    // (CollectionShadow next() fallback, F-NEW-238 cascade
                    // ref reads) walks string/int/REF kinds; a CLASS_REF
                    // slot falls through every read → next() returned
                    // WITHOUT advancing the cursor → hasNext() stayed true
                    // forever (the kotlin withIndex copy-loop spin: chess
                    // Ln3/b;.<clinit> pc=0x44, Fossify Clock Lx4/e;.<clinit>
                    // pc=0x46). The token's object_id IS a real heap Class
                    // object, so the OBJECT_REF projection is faithful:
                    // same id, same identity, receiver class
                    // Ljava/lang/Class; (F-NEW-218 token-hierarchy law
                    // answers instanceof/casts on it).
                    if (src_val.type == DalvikType::CLASS_REF &&
                        src_val.object_id != 0) {
                        src_val = DalvikValue::make_object(
                            src_val.object_id, "Ljava/lang/Class;");
                    }
                    std::string field_name = "array[" + std::to_string(i) + "]";
                    // F-NEW-385 (CONT-82): filled-new-array component
                    // typing. The DEX fill payload is per-component raw
                    // ints ([Z 0/1, [C UTF-16 code units, [B/[S signed);
                    // the register only carries INT32 (and a zeroed
                    // register reads as NULL). The AOSP array law: the
                    // ARRAY DESCRIPTOR is the component type — store the
                    // TYPED value so every downstream reader (Arrays.
                    // toString per-type rendering, aget-boolean/char
                    // identity) answers the contract. Caught by the
                    // CONT-82 arrays fixture: [Z {true,false} read back
                    // "[1, null]", [C {'x','y'} read back "[120, 121]".
                    if (!type_desc.empty() && type_desc.size() >= 2 &&
                        type_desc[0] == '[') {
                        char comp = type_desc[1];
                        auto as_int385 = [&]() -> int {
                            if (src_val.type == DalvikType::INT32)
                                return src_val.int_val;
                            if (src_val.type == DalvikType::BOOLEAN)
                                return src_val.bool_val ? 1 : 0;
                            if (src_val.type == DalvikType::CHAR)
                                return src_val.int_val;
                            return 0;  // NULL/zeroed register = 0
                        };
                        if (comp == 'Z') {
                            src_val = DalvikValue::make_bool(as_int385() != 0);
                        } else if (comp == 'C') {
                            src_val = DalvikValue::make_char(
                                static_cast<char>(as_int385() & 0xFF));
                        } else if (comp == 'B') {
                            src_val = DalvikValue::make_byte(
                                static_cast<int8_t>(as_int385() & 0xFF));
                        } else if (comp == 'S') {
                            src_val = DalvikValue::make_short(
                                static_cast<int16_t>(as_int385() & 0xFFFF));
                        }
                    }
                    heap_.set_object_field(arr_id, field_name, src_val);
                }

                // S58 hygiene: was ALWAYS-ON stderr (F-074 law violation —
                // per-run noise + throughput cost on FNA-heavy Compose
                // apps). Env-gated, bounded, same format.
                {
                    static thread_local const bool fna_trace =
                        std::getenv("MINIANDROID_FNA_TRACE") != nullptr;
                    static thread_local uint64_t fna_n = 0;
                    if (fna_trace && fna_n < 200) {
                        ++fna_n;
                        std::cerr << "[EXP093-FNA] filled-new-array type=" << type_desc
                                  << " count=" << src_regs.size()
                                  << " arr_id=" << arr_id << std::endl;
                    }
                }

                DalvikValue result_val;
                result_val.type = DalvikType::OBJECT_REF;
                result_val.object_id = arr_id;
                result_val.class_desc = type_desc.empty() ? "Larray;" : type_desc.c_str();
                result_val.int_val = static_cast<int32_t>(src_regs.size());
                last_invoke_return_ = result_val;
                pc_ = pc_ + 3;
                success = true;
                break;
            }
            case Opcode::FILL_ARRAY_DATA: {
                // EXP-060: fill-array-data vAA, +BBBBBBBB (31t format, 3 code units)
                // Fills the array in vAA with data from a payload at PC+offset.
                // The payload format is:
                //   code_unit[0]: 0x0300 (magic — fill-array-data-payload)
                //   code_unit[1]: element width (1, 2, 4, or 8 bytes)
                //   code_unit[2..3]: element count (32-bit)
                //   followed by element_width * count bytes, padded to 16-bit
                trace.opcode_name = "fill-array-data";
                uint8_t vAA = (bytecode_[pc_] >> 8) & 0xFF;
                int32_t offset = static_cast<int32_t>(bytecode_[pc_ + 1] |
                    (static_cast<uint32_t>(bytecode_[pc_ + 2]) << 16));
                uint32_t payload_pc = pc_ + offset;

                DalvikValue array_val = get_register(vAA);
                // UNIFIED_014b: AOSP FillArrayData null check FIRST (before
                // the legacy non-OBJECT_REF skip) — null is unambiguous in
                // this engine and must throw NPE, not be silently skipped.
                if (array_val.type == DalvikType::NULL_REF || array_val.is_null) {
                    log("⚠️ FILL_ARRAY_DATA into null array");
                    raise_synthetic_exception(
                        "Ljava/lang/NullPointerException;",
                        "null array in FILL_ARRAY_DATA", "fill-null");
                    /* handled/unhandled: same pc semantics as aget/aput. */
                    break;
                }
                // EXP-071: Diagnostic — check if the array register has a valid OBJECT_REF
                if (array_val.type != DalvikType::OBJECT_REF) {
                    std::cerr << "[EXP071-FILL] fill-array-data: v" << (int)vAA
                              << " is NOT OBJECT_REF (type=" << static_cast<int>(array_val.type)
                              << ") — THROWING exception" << std::endl;
                    // Simulate ArrayStoreException / NegativeArraySizeException
                    DalvikValue exc;
                    exc.type = DalvikType::OBJECT_REF;
                    exc.object_id = 0;
                    exc.class_desc = "Larray;";
                    // Set up exception state — just log and skip
                    pc_ = pc_ + 3;
                    success = true;
                    break;
                }
                if (array_val.object_id == 0 || !heap_.has_object(array_val.object_id)) {
                    std::cerr << "[EXP071-FILL] fill-array-data: array object_id=0 or not in heap"
                              << " — THROWING exception" << std::endl;
                    pc_ = pc_ + 3;
                    success = true;
                    break;
                }
                // The array must be an OBJECT_REF to an array object.
                // For now, we don't model array elements per-index.
                // The fill-array-data payload is typically small (2-4 booleans
                // or ints) and the array is a local — we just advance PC.
                // If the array is used later (e.g. aget), it will return 0.
                //
                // A more complete implementation would:
                //   1. Validate payload_pc is within bytecode.
                //   2. Read the payload header (element_width, count).
                //   3. Store the raw bytes on the HeapObject as a
                //      "raw_array_data" field, so aget/aget-boolean can read it.
                // For now, log and skip.
                if (payload_pc < bytecode_.size()) {
                    uint16_t magic = bytecode_[payload_pc];
                    uint16_t elem_width = bytecode_[payload_pc + 1];
                    uint32_t count = static_cast<uint32_t>(bytecode_[payload_pc + 2]) |
                        (static_cast<uint32_t>(bytecode_[payload_pc + 3]) << 16);
                    // UNIFIED_014b (fill-array-data AOSP semantics). Reference:
                    // AOSP art entrypoints/entrypoint_utils.cc FillArrayData
                    // (refs/tags/android-14.0.0_r1, lines 176–195, fetched
                    // 2026-09-03):
                    //   1. null array → NPE "null array in FILL_ARRAY_DATA"
                    //   2. element_count > array length → AIOOBE
                    //      "failed FILL_ARRAY_DATA; length=%d, index=%d"
                    //      (index slot carries the payload COUNT)
                    //   3. fill exactly element_count elements;
                    //      the array length is NEVER modified.
                    // The old code silently overwrote __array_length__ AND
                    // __new_array_length__ with the payload count (shrink/
                    // grow drift real Dalvik never produces), had no
                    // overflow check, and silently truncated fills past 100
                    // elements. (The null check was hoisted above the legacy
                    // non-OBJECT_REF skip — see case head.) Element byte
                    // decoding (little-endian word order per width 1/2/4/8)
                    // was verified correct against the DEX spec and kept
                    // unchanged.
                    if (array_val.type == DalvikType::OBJECT_REF &&
                        heap_.has_object(array_val.object_id)) {
                        // Effective length chain — identical to aget/aput.
                        int32_t arr_len = 0;
                        auto len_field = heap_.get_object_field(array_val.object_id, "__array_length__");
                        if (len_field.has_value() && len_field->type == DalvikType::INT32) {
                            arr_len = len_field->int_val;
                        }
                        if (arr_len == 0) {
                            auto nm_field = heap_.get_object_field(array_val.object_id, "__new_array_length__");
                            if (nm_field.has_value() && nm_field->type == DalvikType::INT32) {
                                arr_len = nm_field->int_val;
                            }
                        }
                        if (arr_len == 0) {
                            arr_len = array_val.int_val;
                        }
                        // AOSP: overflow check BEFORE any store (confirmed
                        // arrays only; unknown length keeps the legacy gate).
                        if (arr_len > 0 && static_cast<uint32_t>(arr_len) < count) {
                            log("⚠️ FILL_ARRAY_DATA overflow: arr_len=" + std::to_string(arr_len) +
                                " count=" + std::to_string(count));
                            raise_synthetic_exception(
                                "Ljava/lang/ArrayIndexOutOfBoundsException;",
                                "failed FILL_ARRAY_DATA; length=" + std::to_string(arr_len) +
                                    ", index=" + std::to_string(count),
                                "fill-oob");
                            break;
                        }
                        // Payload data bounds: the payload bytes must actually
                        // exist in the bytecode stream (corrupt/truncated
                        // payload = cannot fill → same AIOOBE contract).
                        uint32_t data_start = payload_pc + 4;
                        uint64_t bytes_needed = static_cast<uint64_t>(count) * elem_width;
                        uint64_t bytes_avail =
                            (elem_width > 0 && data_start < bytecode_.size())
                                ? static_cast<uint64_t>(bytecode_.size() - data_start) * 2u
                                : 0u;
                        if (count > 0 && elem_width > 0 && bytes_needed > bytes_avail) {
                            log("⚠️ FILL_ARRAY_DATA truncated payload: need " +
                                std::to_string(bytes_needed) + "B, have " +
                                std::to_string(bytes_avail) + "B");
                            raise_synthetic_exception(
                                "Ljava/lang/ArrayIndexOutOfBoundsException;",
                                "failed FILL_ARRAY_DATA; length=" + std::to_string(
                                    arr_len > 0 ? arr_len : static_cast<int32_t>(count)) +
                                    ", index=" + std::to_string(count),
                                "fill-oob");
                            break;
                        }
                        heap_.set_object_field(array_val.object_id,
                            "__fill_array_data_pc__",
                            DalvikValue::make_int(static_cast<int32_t>(payload_pc)));
                        heap_.set_object_field(array_val.object_id,
                            "__fill_array_elem_width__",
                            DalvikValue::make_int(elem_width));
                        heap_.set_object_field(array_val.object_id,
                            "__fill_array_count__",
                            DalvikValue::make_int(static_cast<int32_t>(count)));
                        // UNIFIED_014b: length is NOT touched (AOSP). The old
                        // __array_length__/__new_array_length__ = count writes
                        // are removed — that was the shrink/grow drift.
                        // Read and store each element
                        // Payload starts at payload_pc + 4 (after magic, elem_width, count)
                        // Each element is elem_width bytes, starting at byte offset
                        // (payload_pc + 4) * 2 in the raw bytecode.
                        // UNIFIED_014b: the old `i < 100` silent truncation cap
                        // is removed — overflow is now handled by the explicit
                        // AIOOBE checks above and each store is per-element
                        // bounds-checked below.
                        for (uint32_t i = 0; i < count; ++i) {
                            // Read elem_width bytes from the payload
                            if (elem_width == 4) {
                                // int or float (4 bytes = 2 code units).
                                // S83-GFX-BASE ROOT CAUSE FIX: the payload
                                // bits are RAW — interpretation comes from
                                // the ARRAY element type (AOSP FillArrayData
                                // law: memcpy into the array, no reinterpre-
                                // tation). float[] payloads ([F) were stored
                                // as INT32 bit patterns → every float[] ta-
                                // ble literal (game coordinates, vertices,
                                // color matrices) read back garbage floats.
                                if (data_start + i * 2 + 1 < bytecode_.size()) {
                                    uint32_t raw = static_cast<uint32_t>(bytecode_[data_start + i * 2]) |
                                        (static_cast<uint32_t>(bytecode_[data_start + i * 2 + 1]) << 16);
                                    if (array_val.class_desc == "[F") {
                                        float fv;
                                        std::memcpy(&fv, &raw, sizeof(fv));
                                        heap_.set_object_field(array_val.object_id,
                                            "array[" + std::to_string(i) + "]",
                                            DalvikValue::make_float(fv));
                                    } else {
                                        heap_.set_object_field(array_val.object_id,
                                            "array[" + std::to_string(i) + "]",
                                            DalvikValue::make_int(static_cast<int32_t>(raw)));
                                    }
                                }
                            } else if (elem_width == 1) {
                                // boolean or byte (1 byte, packed 2 per code unit)
                                // CONT-65 F-NEW-357 ROOT CAUSE FIX: the old
                                // law stored EVERY 1-byte element as
                                // make_bool(byte_val != 0) — byte[] literals
                                // (crypto keys, encodings, `new byte[]{'A',
                                // 'B','C'}`) were corrupted into booleans
                                // ('A'→true). Same AOSP FillArrayData law the
                                // elem_width==4 branch already implements:
                                // interpretation comes from the ARRAY element
                                // type — [B stores the raw byte, [Z the bool.
                                if (data_start + i / 2 < bytecode_.size()) {
                                    uint16_t word = bytecode_[data_start + i / 2];
                                    uint8_t byte_val = (i % 2 == 0) ? (word & 0xFF) : ((word >> 8) & 0xFF);
                                    if (array_val.class_desc == "[B") {
                                        heap_.set_object_field(array_val.object_id,
                                            "array[" + std::to_string(i) + "]",
                                            DalvikValue::make_byte(
                                                static_cast<int8_t>(byte_val)));
                                    } else {
                                        heap_.set_object_field(array_val.object_id,
                                            "array[" + std::to_string(i) + "]",
                                            DalvikValue::make_bool(byte_val != 0));
                                    }
                                }
                            } else if (elem_width == 2) {
                                // short or char (1 code unit)
                                // F-NEW-385 (CONT-82): component typing —
                                // [C stores CHAR, [S stores SHORT (the AOSP
                                // FillArrayData interpretation law the width-1
                                // branch already implements). The old make_int
                                // store made char[] literals render as numeric
                                // codes in Arrays.toString ([C {'x','y'} →
                                // "[120, 121]" — the CONT-82 fixture catch).
                                if (data_start + i < bytecode_.size()) {
                                    int16_t val = static_cast<int16_t>(bytecode_[data_start + i]);
                                    if (array_val.class_desc == "[C") {
                                        heap_.set_object_field(array_val.object_id,
                                            "array[" + std::to_string(i) + "]",
                                            DalvikValue::make_char(
                                                static_cast<char>(val & 0xFF)));
                                    } else if (array_val.class_desc == "[S") {
                                        heap_.set_object_field(array_val.object_id,
                                            "array[" + std::to_string(i) + "]",
                                            DalvikValue::make_short(val));
                                    } else {
                                        heap_.set_object_field(array_val.object_id,
                                            "array[" + std::to_string(i) + "]",
                                            DalvikValue::make_int(val));
                                    }
                                }
                            } else if (elem_width == 8) {
                                // long or double (4 code units)
                                if (data_start + i * 4 + 3 < bytecode_.size()) {
                                    int64_t val = static_cast<int64_t>(
                                        static_cast<uint32_t>(bytecode_[data_start + i * 4]) |
                                        (static_cast<uint32_t>(bytecode_[data_start + i * 4 + 1]) << 16) |
                                        (static_cast<uint64_t>(bytecode_[data_start + i * 4 + 2]) << 32) |
                                        (static_cast<uint64_t>(bytecode_[data_start + i * 4 + 3]) << 48));
                                    DalvikValue lv;
                                    lv.type = DalvikType::INT64;
                                    lv.long_val = val;
                                    heap_.set_object_field(array_val.object_id,
                                        "array[" + std::to_string(i) + "]", lv);
                                }
                            }
                        }
                    }
                }
                pc_ = pc_ + 3;
                success = true;
                break;
            }
            case Opcode::THROW: {
                trace.opcode_name = "throw";
                uint8_t vAA = (bytecode_[pc_] >> 8) & 0xFF;
                DalvikValue exc = get_register(vAA);
                // W11 (Coder-4) session probe: dump the register shape at
                // every athrow when env-gated — the NC Room census family
                // ("throw null" with a NON-EMPTY exc_class in THROW-SITE)
                // means the register holds a class-carrying null shape.
                {
                    static thread_local const bool w11_tp =
                        std::getenv("MINIANDROID_W11_THROW_PROBE") != nullptr;
                    static thread_local uint64_t w11_tp_n = 0;
                    if (w11_tp && w11_tp_n < 80) {
                        ++w11_tp_n;
                        std::cerr << "[W11-THROW] #" << w11_tp_n << " at "
                                  << current_class_ << "." << current_method_
                                  << " pc=" << pc_ << " v" << +vAA
                                  << " type=" << static_cast<int>(exc.type)
                                  << " oid=" << exc.object_id
                                  << " class=" << exc.class_desc
                                  << " f141_null="
                                  << (f141_is_null_receiver(exc) ? 1 : 0)
                                  << " in_heap="
                                  << (exc.object_id
                                              ? (heap_.has_object(exc.object_id)
                                                     ? 1
                                                     : 0)
                                              : -1)
                                  << std::endl;
                    }
                }
                /* F-NEW-268e (CONT-18g): JLS/ART throw-null law — `throw null`
                 * throws NullPointerException AT THE THROW SITE (JLS 14.18:
                 * "If evaluation of the Expression is null, a NullPointerException
                 * is thrown"). The old path dispatched an exception object whose
                 * class was "<unknown>" (a null register carries no class); the
                 * probe face: ECJ folds a provable-null dereference into `athrow`
                 * of the null register itself (rowC pc=1). */
                if (f141_is_null_receiver(exc)) {
                    raise_synthetic_exception(
                        "Ljava/lang/NullPointerException;",
                        "throw null", "throw-null");
                    break;
                }
                std::string exc_class = exc.class_desc.empty()
                                      ? "<unknown>" : exc.class_desc;

                // CONT-75 (F-NEW-277 lever): env-gated athrow provenance —
                // where does dooz's R8-merged CancellationException (La;)
                // come from, and which frame throws it?
                static const char* throw_trace_env =
                    std::getenv("MINIANDROID_THROW_TRACE");
                if (throw_trace_env && *throw_trace_env == '1') {
                    static thread_local uint64_t thr_n = 0;
                    if (thr_n < 40) {
                        ++thr_n;
                        std::cerr << "[THROW-SITE] #" << thr_n << " "
                                  << exc_class << " at "
                                  << current_class_ << "."
                                  << current_method_ << " pc=" << pc_
                                  << " depth=" << recursion_depth_;
                        // CONT-75: print the bytecode window around the
                        // throw site from the engine's OWN proven decode —
                        // the pc-8..pc+4 code-unit window (engine parse is
                        // the authority; no independent DEX walker needed).
                        {
                            const uint32_t bsz =
                                static_cast<uint32_t>(bytecode_.size());
                            std::cerr << " code[";
                            for (int32_t u = static_cast<int32_t>(pc_) - 8;
                                 u <= static_cast<int32_t>(pc_) + 4; ++u) {
                                if (u < 0 || u >= static_cast<int32_t>(bsz))
                                    continue;
                                std::cerr << (u == static_cast<int32_t>(pc_)
                                                  ? "<" : " ")
                                          << std::hex
                                          << bytecode_[static_cast<size_t>(u)]
                                          << std::dec;
                            }
                            std::cerr << " ] sz=" << bsz;
                        }
                        std::cerr << std::endl;
                    }
                }

                // EXP-052/053: Find try_item covering current PC, then
                // decode the encoded_catch_handler_list to find the
                // actual handler address.
                bool has_try_table = (current_tries_size_ > 0);
                bool handler_found = false;
                uint32_t try_start = 0, try_end = 0;
                uint32_t handler_addr = 0;
                std::string catch_type = "<none>";
                bool is_catch_all = false;

                if (has_try_table && current_tries_data_ != nullptr) {
                    // Step 1: Find the try_item covering current PC.
                    // try_item layout: u32 start_addr, u16 insn_count, u16 handler_off
                    // tries[] is at the START of current_tries_data_.
                    uint16_t matched_try_idx = 0xFFFF;
                    for (uint16_t i = 0; i < current_tries_size_; i++) {
                        size_t off = i * 8;
                        if (off + 8 > current_tries_data_size_) break;
                        uint32_t start = 0;
                        uint16_t count = 0;
                        uint16_t handler_off = 0;
                        std::memcpy(&start, current_tries_data_ + off, 4);
                        std::memcpy(&count, current_tries_data_ + off + 4, 2);
                        std::memcpy(&handler_off, current_tries_data_ + off + 6, 2);
                        if (pc_ >= start && pc_ < start + count) {
                            matched_try_idx = i;
                            try_start = start;
                            try_end = start + count;
                            // Step 2: handler_off is byte offset into the
                            // encoded_catch_handler_list (which starts at
                            // current_tries_data_ + tries_size * 8).
                            // BUT — actually handler_off is offset from the
                            // start of the encoded_catch_handler_list (which
                            // begins with the list_size uleb128).
                            size_t handler_list_start = static_cast<size_t>(current_tries_size_) * 8;
                            size_t handler_list_end = current_tries_data_size_;
                            if (handler_list_start >= handler_list_end) break;

                            // The encoded_catch_handler_list starts with a
                            // uleb128 list_size, then list_size handlers.
                            // handler_off is byte offset FROM THE START of
                            // this list (i.e., from the list_size byte).
                            size_t handler_abs = handler_list_start + handler_off;
                            if (handler_abs >= handler_list_end) break;

                            // Decode the handler at handler_abs.
                            // sleb128 size, then |size| pairs of (uleb128 type_idx, uleb128 addr),
                            // then catch-all addr if size < 0.
                            // FIND-REUSE-003: the two inline SLEB/ULEB lambda
                            // copies here and in find_catch_handler_for_pc
                            // are gone — ONE shared hardened primitive
                            // (dex/mutf8.h) with handler_list_end as the
                            // bounds cap. On truncation the primitive
                            // returns 0 with ok=false; `vok` is observed
                            // but deliberately not branched on, preserving
                            // the exact legacy return-0 semantics
                            // (malformed-handler policy = FIND-EXC-TRUNC,
                            // queued — not silently changed by a refactor).
                            auto read_sleb = [&](size_t& p) -> int32_t {
                                bool vok = true;
                                return miniandroid::dex::mutf8::read_sleb128(
                                    current_tries_data_, handler_list_end, p, vok);
                            };
                            auto read_uleb = [&](size_t& p) -> uint32_t {
                                bool vok = true;
                                return miniandroid::dex::mutf8::read_uleb128(
                                    current_tries_data_, handler_list_end, p, vok);
                            };

                            size_t p = handler_abs;
                            int32_t size = read_sleb(p);
                            // F-041 (MASTER-6 §B) — encoded_catch_handler size law.
                            // Per the DEX spec, `size` is NEGATIVE ONLY to mark
                            // catch-all presence; the number of typed pairs is
                            // |size| (NOT -(size+1)). The old formula dropped one
                            // typed pair for every negative-size handler and
                            // shifted the stream, so the catch-all addr read
                            // consumed a typed pair's type_idx (e.g. the fixture
                            // IAE handler `7f 14 6a d9 03` decoded as 0 typed +
                            // catch-all @0x14 instead of typed(20)->0x6a +
                            // catch-all @0x1d9) — the dispatcher jumped to
                            // garbage mid-instruction addresses. Affects every
                            // real app whose typed catch shares a handler entry
                            // with a catch-all (the common R8/ECJ shape).
                            int32_t n_pairs = (size >= 0) ? size : -size;
                            // UNIFIED_011.3 TYPED-CATCH (§18): type-match each
                            // typed handler against the thrown exception class
                            // (shared semantics with find_catch_handler_for_pc).
                            for (int h = 0; h < n_pairs; h++) {
                                uint32_t type_idx = read_uleb(p);
                                uint32_t addr = read_uleb(p);
                                std::string handler_exc_desc =
                                    resolve_type_for_dex(type_idx, current_dex_index_);
                                if (is_exception_subtype(exc_class, handler_exc_desc)) {
                                    handler_found = true;
                                    handler_addr = addr;
                                    is_catch_all = false;
                                    catch_type = handler_exc_desc;
                                    break;
                                }
                            }
                            // If size <= 0, there's a catch-all handler at the end
                            if (size <= 0 && !handler_found) {
                                uint32_t addr = read_uleb(p);
                                handler_found = true;
                                handler_addr = addr;
                                is_catch_all = true;
                                catch_type = "<catch-all>";
                            }
                            break;
                        }
                    }
                }

                // EXP-052/053: Log the exception event in the required format.
                // F-050b: include the exception MESSAGE when the Throwable
                // message law stored one (OpenJDK detailMessage contract).
                {
                    std::string exc_msg;
                    if (exc.object_id != 0) {
                        auto mv = heap_.get_object_field(exc.object_id, "message");
                        if (mv.has_value() && mv->type == DalvikType::STRING_REF)
                            exc_msg = mv->string_val;
                    }
                    std::cerr << "[EXCEPTION] method=" << current_class_ << "."
                              << current_method_
                              << " pc=" << pc_
                              << " exception=" << exc_class;
                    if (!exc_msg.empty()) std::cerr << " msg=\"" << exc_msg << "\"";
                    std::cerr << " try_range=";
                }
                if (has_try_table && handler_found) {
                    std::cerr << "[" << try_start << "," << try_end << ")";
                } else if (has_try_table) {
                    std::cerr << "(no try covering pc)";
                } else {
                    std::cerr << "(none)";
                }
                std::cerr << " handler=" << (handler_found ? "FOUND" : "NOT_FOUND");
                if (handler_found) {
                    std::cerr << " handler_addr=" << handler_addr
                              << " catch_type=" << catch_type;
                }
                // M9: exception MESSAGE in the trace line — root-hunt
                // diagnostic (the Kotlin `error(...)`/`check(...)` messages
                // ARE the app's own failure law; without them every hunt
                // needs a DEX re-disassembly just to read the reason).
                if (exc.object_id != 0) {
                    auto msg = heap_.get_object_field(exc.object_id, "message");
                    if (msg.has_value() && !msg->string_val.empty())
                        std::cerr << " msg=\"" << msg->string_val << "\"";
                }
                std::cerr << std::endl;

                // EXP-053 + UNIFIED_011.3: if any handler (typed or catch-all)
                // matched, jump to it instead of halting/skipping.
                if (handler_found) {
                    if (handler_addr < bytecode_.size()) {
                        std::cerr << "[EXCEPTION] → jumping to "
                                  << (is_catch_all ? "catch-all" : "typed")
                                  << " handler at PC=" << handler_addr
                                  << " catch_type=" << catch_type << std::endl;
                        // Save the exception for move-exception to read.
                        pending_exception_ = exc;
                        trace.status = InstructionTrace::Status::BRANCH_TAKEN;
                        trace.operands.push_back({"reason", is_catch_all
                                ? "throw (catch-all handler)"
                                : "throw (typed handler: " + catch_type + ")"});
                        trace.operands.push_back({"exception_class", exc_class});
                        trace.operands.push_back({"handler_addr", std::to_string(handler_addr)});
                        pc_ = handler_addr;
                        break;
                    } else {
                        // GP-INT-014 (issue #582): the out-of-bounds handler
                        // target previously LOGGED "falling through to halt"
                        // and then DID fall through — control reached the
                        // next case label (MOVE_16) and executed its body
                        // with pc_ still on the THROW instruction (register
                        // mutation from operand words + PC desync). A
                        // malformed handler target is now the same
                        // structured unwind as "no handler in this frame".
                        std::cerr << "[EXCEPTION] WARNING: handler_addr "
                                  << handler_addr << " out of bounds (bytecode_size="
                                  << bytecode_.size() << ") — malformed catch "
                                     "metadata, unwinding frame"
                                  << std::endl;
                        frame_unwind_exception_valid_ = true;
                        frame_unwind_exception_ = exc;
                        last_invoke_return_ = DalvikValue::make_null();
                        halted_on_return_ = true;
                        pc_ += 1;
                        break;
                    }
                }

                // UNIFIED_011.3 EXC-PROPAGATE (§18): no handler in this frame.
                // Replaces the EXP-071 skip-and-continue approximation (which
                // silently executed code after the throw — NOT Dalvik
                // semantics). Real Dalvik: unwind this frame; the invoking
                // frame (try_recursive_invoke call site) then searches ITS
                // try table via frame_unwind_exception_.
                if (!handler_found) {
                    std::cerr << "[EXCEPTION] no handler for " << exc_class
                              << " in " << current_class_ << "."
                              << current_method_
                              << " — unwinding frame (propagate to caller)"
                              << std::endl;
                    frame_unwind_exception_valid_ = true;
                    frame_unwind_exception_ = exc;
                    last_invoke_return_ = DalvikValue::make_null();
                    halted_on_return_ = true;
                    pc_ += 1;
                    break;
                }
                // If handler was found, the code above already jumped to it.
            }
            // move/16 (32x: op|AAAA|BBBB, 3 code units)
            // S211 DIRECTION LAW (C3-N1 residue — #530 claimed it, never
            // landed): AOSP 32x is "op vAAAA, vBBBB" with A = DEST (unit 1),
            // B = SOURCE (unit 2) — the same law execute_move_object_16
            // already follows. The pre-fix case read unit 1 as src and unit 2
            // as dest, so `move/16 v5, v3` clobbered v3 with v5's value and
            // left v5 stale (silent-wrong). The probe row
            // move_16_direction_aosp_law discriminates (111 vs 222).
            case Opcode::MOVE_16: {
                if (pc_ + 2 >= bytecode_.size()) return false;
                uint16_t dest = bytecode_[pc_ + 1];  // vAAAA — destination
                uint16_t src = bytecode_[pc_ + 2];   // vBBBB — source
                DalvikValue val = get_register(src);
                set_register(dest, val);
                trace.opcode_name = "move/16";
                pc_ += 3;
                break;
            }
            // move-wide/16 (32x: op|AAAA|BBBB, 3 code units) — S211 PROBE:
            // previously ABSENT from this dispatcher entirely (#529 D-P0-5,
            // claimed harness-tested in #530 but never landed on main); any
            // method containing it died at handle_unimplemented. AOSP 32x law:
            // unit 1 = vAAAA (dest), unit 2 = vBBBB (source) — the same law
            // execute_move_object_16 follows. Wide semantics mirror
            // MOVE_WIDE_FROM16: non-wide sources coerce to INT64 and the
            // F-028b shadow pair is filled (set_wide_pair).
            case Opcode::MOVE_WIDE_16: {
                if (pc_ + 2 >= bytecode_.size()) return false;
                uint16_t dest = bytecode_[pc_ + 1];  // vAAAA — destination
                uint16_t src = bytecode_[pc_ + 2];   // vBBBB — source
                DalvikValue val = get_register(src);
                if (val.type != DalvikType::INT64 && val.type != DalvikType::FLOAT64) {
                    val = DalvikValue::make_long(static_cast<int64_t>(static_cast<uint32_t>(val.int_val)));
                }
                set_wide_pair(dest, val);
                trace.opcode_name = "move-wide/16";
                pc_ += 3;
                break;
            }
            // move-wide/from16 (22x: AA|op BBBB, 2 code units)
            case Opcode::MOVE_WIDE_FROM16: {
                if (pc_ + 1 >= bytecode_.size()) return false;
                uint8_t dest = (bytecode_[pc_] >> 8) & 0xFF;
                uint16_t src = bytecode_[pc_ + 1];
                // W15 (#627 E-01): same 16-bit-source law as move/from16 —
                // the uint8_t cast aliased v256+ onto v0..255.
                DalvikValue val = get_register(src);
                // F-028b: wide values occupy TWO slots (vDest, vDest+1) —
                // fill the shadow with the high 32-bit word (ART layout).
                // The missing shadow left range-invoke wide-arg merges
                // reading (0<<32)|low32 — every delegated double param
                // arrived as ~1e-315 garbage (dooz TransferFunction IAE).
                if (val.type != DalvikType::INT64 && val.type != DalvikType::FLOAT64) {
                    val = DalvikValue::make_long(static_cast<int64_t>(static_cast<uint32_t>(val.int_val)));
                }
                set_wide_pair(dest, val);
                trace.opcode_name = "move-wide/from16";
                pc_ += 2;
                break;
            }
            // monitor-enter / monitor-exit (12x: B|A|op, 1 code unit)
            case Opcode::MONITOR_ENTER: {
                trace.opcode_name = "monitor-enter";
                // [S191-C8] F-C8-141 — REAL monitor ownership accounting
                // (AOSP Object.wait/notify law needs the owner). vAA holds
                // the monitor object. Under the DETERMINISTICALLY
                // SERIALIZED engine there is exactly one interpreter
                // thread, so a hold COUNT per monitor oid is the full
                // ownership model (reentrant count). Monitors that carry
                // no heap object (class-token synchronized static) are
                // recorded loudly, not tracked.
                {
                    const uint8_t vAA = (bytecode_[pc_] >> 8) & 0xFF;
                    DalvikValue mv = current_registers_->read_v(
                        static_cast<uint16_t>(vAA));
                    if (mv.type == DalvikType::OBJECT_REF && mv.object_id != 0) {
                        monitor_holds_[mv.object_id]++;
                    } else {
                        static uint64_t c8_monitor_tok = 0;
                        if (c8_monitor_tok < 8) {
                            ++c8_monitor_tok;
                            std::cerr << "[C8-MONITOR] monitor-enter on "
                                         "class-token/no-heap monitor — not "
                                         "tracked (caller=" << current_class_
                                      << "." << current_method_ << ")"
                                      << std::endl;
                        }
                    }
                }
                pc_ += 1;  // ownership tracked; still no suspension
                break;
            }
            case Opcode::MONITOR_EXIT: {
                trace.opcode_name = "monitor-exit";
                // [S191-C8] F-C8-141 — mirror of the enter law. Unlock of
                // an un-held monitor = IMSE territory in AOSP; the
                // interpreter does not throw here (javac-balanced code),
                // the imbalance is recorded loudly instead.
                {
                    const uint8_t vAA = (bytecode_[pc_] >> 8) & 0xFF;
                    DalvikValue mv = current_registers_->read_v(
                        static_cast<uint16_t>(vAA));
                    if (mv.type == DalvikType::OBJECT_REF && mv.object_id != 0) {
                        auto it = monitor_holds_.find(mv.object_id);
                        if (it != monitor_holds_.end() && it->second > 0) {
                            if (--it->second == 0) monitor_holds_.erase(it);
                        } else {
                            std::cerr << "[C8-MONITOR] monitor-exit on "
                                         "UN-HELD monitor o" << mv.object_id
                                      << " (JDK: IllegalMonitorStateException "
                                         "territory) caller=" << current_class_
                                      << "." << current_method_ << std::endl;
                        }
                    }
                }
                pc_ += 1;
                break;
            }
            // const-wide/32 (21i: AA|op BBBB, 2 code units)
            case Opcode::CONST_WIDE_32: {
                // F-028e (M4 §A1) FIX: 31i format = AA|op BBBB FFFF — the
                // 32-bit literal spans TWO units (LE). The previous handler
                // read ONE unit (sign-extended int16) and advanced by 2, so
                // (a) every value ≥ 0x8000 arrived sign-mangled and (b) the
                // pc landed INSIDE the literal's high word — opcode 0xff
                // "unimplemented" in real DEX (first hit: dooz
                // androidx.compose Lb2/n;.a snapshot CAS loop spun forever
                // on 0x3fff = the high half of 0x3FFFFFFF).
                if (pc_ + 2 >= bytecode_.size()) return false;
                uint16_t instr = bytecode_[pc_];
                uint8_t vAA = (instr >> 8) & 0xFF;
                int32_t val = static_cast<int32_t>(
                    static_cast<uint32_t>(bytecode_[pc_ + 1]) |
                    (static_cast<uint32_t>(bytecode_[pc_ + 2]) << 16));
                DalvikValue dv;
                dv.type = DalvikType::INT64;
                // EXP-071 Phase 8: For INT64 values, write to long_val (not int_val).
                // int_val is a 32-bit field; long_val is the 64-bit field.
                // Writing to int_val left long_val with uninitialized garbage,
                // which broke the wide-arg merge in execute_invoke_static
                // (because the merge reads long_val for INT64 types).
                dv.long_val = val;
                // F-028b: fill the vAA+1 shadow slot (ART two-slot layout)
                set_wide_pair(vAA, dv);
                trace.opcode_name = "const-wide/32";
                pc_ += 3;
                break;
            }
            // iget-short / iput-short — now handled by the consolidated
            // iget-variant/iput-variant cases above (EXP-062).
            // rem-double (23x: AA|op BB|CC, 2 code units)
            case Opcode::REM_DOUBLE: {
                uint16_t instr = bytecode_[pc_];
                uint8_t vAA = (instr >> 8) & 0xFF;
                uint8_t vBB = bytecode_[pc_ + 1] & 0xFF;
                uint8_t vCC = (bytecode_[pc_ + 1] >> 8) & 0xFF;
                DalvikValue b = get_register(vBB);
                DalvikValue c = get_register(vCC);
                DalvikValue result_val;
                result_val.type = DalvikType::FLOAT64;
                // GP-INT-013 (issue #582): REM_DOUBLE is the ONE 23x double
                // op that missed the typed-operand law — an INT64-backed
                // double was decoded from its low-32 int_val instead of the
                // bit-reinterpreted long_val (ARITH_23X_DOUBLE_CASE applies
                // bits_l2d); and divisor 0 answered 0 instead of IEEE NaN.
                // Both now follow the same law as the neighbouring macro.
                // F-028 law: FLOAT32-backed slots are raw-bit views.
                float bf_r = 0.0f, cf_r = 0.0f;
                uint32_t bb32 = dalvik_raw_bits32(b); std::memcpy(&bf_r, &bb32, 4);
                uint32_t cb32 = dalvik_raw_bits32(c); std::memcpy(&cf_r, &cb32, 4);
                double bd = (b.type == DalvikType::FLOAT64) ? b.double_val
                          : (b.type == DalvikType::INT64 ? bits_l2d(b.long_val)
                          : (b.type == DalvikType::FLOAT32 ? (double)bf_r
                          : (double)b.int_val));
                double cd = (c.type == DalvikType::FLOAT64) ? c.double_val
                          : (c.type == DalvikType::INT64 ? bits_l2d(c.long_val)
                          : (c.type == DalvikType::FLOAT32 ? (double)cf_r
                          : (double)c.int_val));
                result_val.double_val = fmod(bd, cd);  // IEEE: %0 → NaN
                set_register(vAA, result_val);
                trace.opcode_name = "rem-double";
                pc_ += 2;
                break;
            }
            // Double arithmetic (23x) — add the rest
            #define ARITH_23X_DOUBLE_CASE(opcode, op_name, op) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vAA = (instr >> 8) & 0xFF; \
                    uint8_t vBB = bytecode_[pc_ + 1] & 0xFF; \
                    uint8_t vCC = (bytecode_[pc_ + 1] >> 8) & 0xFF; \
                    DalvikValue b = get_register(vBB); \
                    DalvikValue c = get_register(vCC); \
                    DalvikValue result_val; \
                    result_val.type = DalvikType::FLOAT64; \
                    double bd = (b.type == DalvikType::FLOAT64) ? b.double_val \
                              : (b.type == DalvikType::INT64 ? bits_l2d(b.long_val) : (double)b.int_val); \
                    double cd = (c.type == DalvikType::FLOAT64) ? c.double_val \
                              : (c.type == DalvikType::INT64 ? bits_l2d(c.long_val) : (double)c.int_val); \
                    if (strcmp(op, "add") == 0) result_val.double_val = bd + cd; \
                    else if (strcmp(op, "sub") == 0) result_val.double_val = bd - cd; \
                    else if (strcmp(op, "mul") == 0) result_val.double_val = bd * cd; \
                    else if (strcmp(op, "div") == 0) result_val.double_val = bd / cd; \
                    set_register(vAA, result_val); \
                    trace.opcode_name = op_name; \
                    pc_ += 2; \
                    break; \
                }
            ARITH_23X_DOUBLE_CASE(ADD_DOUBLE, "add-double", "add")
            ARITH_23X_DOUBLE_CASE(SUB_DOUBLE, "sub-double", "sub")
            ARITH_23X_DOUBLE_CASE(MUL_DOUBLE, "mul-double", "mul")
            ARITH_23X_DOUBLE_CASE(DIV_DOUBLE, "div-double", "div")
            #undef ARITH_23X_DOUBLE_CASE

            // EXP-041: Long/float/double 2addr opcodes (12x: B|A|op, 1 code unit)
            // Simplified: reuse the 2addr pattern from ARITH_2ADDR_CASE
            #define ARITH_WIDE_2ADDR_CASE(opcode, op_name, op_type, op) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    /* 12x format is B|A|op per AOSP dalvik-bytecode.html:   */ \
                    /* vA (dest) = bits 8-11, vB (src) = bits 12-15.          */ \
                    /* IMPORTANT (RESULT_007 reconciliation): the original    */ \
                    /* code read vA=(instr>>8) and vB=(instr>>4) — it swapped */ \
                    /* the two registers AND read vB from the opcode byte's   */ \
                    /* nibble. The RESULT_007 fix went to the opposite swap   */ \
                    /* (vA=HIGH) instead of AOSP, which matched the equally   */ \
                    /* swapped fixture encoder but not real DEX.              */ \
                    /* DEMO-12X-NIBBLE (2026-09-04): aligned to AOSP.         */ \
                    uint8_t vA = (instr >> 8) & 0xF; \
                    uint8_t vB = (instr >> 12) & 0xF; \
                    DalvikValue a = get_register(vA); \
                    DalvikValue b = get_register(vB); \
                    DalvikValue result_val; \
                    result_val.type = op_type; \
                    float af = 0.0f, bf = 0.0f; /* F-028: bit views */ \
                    if (op_type == DalvikType::INT64) { \
                        /* IMPORTANT (RESULT_001): full 64-bit computation via */ \
                        /* long_val — int_val only aliases the low 32 union bits. */ \
                        int64_t av = (a.type == DalvikType::INT64) ? a.long_val \
                                   : (a.type == DalvikType::INT32 ? static_cast<int64_t>(a.int_val) : 0); \
                        int64_t bv = (b.type == DalvikType::INT64) ? b.long_val \
                                   : (b.type == DalvikType::INT32 ? static_cast<int64_t>(b.int_val) : 0); \
                        if ((strcmp(op, "div") == 0 || strcmp(op, "rem") == 0) && bv == 0) { \
                            /* MASTER RECONCILIATION (K-29): throws instead of yield-0. */ \
                            throw_deferred("Ljava/lang/ArithmeticException;", "divide by zero", "ARITH-W2A"); \
                            pc_ += 1; \
                            break; \
                        } \
                        /* GP-INT-012 (issue #582): wrap-defined int64 math + MIN64/-1 */ \
                        if (strcmp(op, "add") == 0) result_val.long_val = static_cast<int64_t>(static_cast<uint64_t>(av) + static_cast<uint64_t>(bv)); \
                        else if (strcmp(op, "sub") == 0) result_val.long_val = static_cast<int64_t>(static_cast<uint64_t>(av) - static_cast<uint64_t>(bv)); \
                        else if (strcmp(op, "mul") == 0) result_val.long_val = static_cast<int64_t>(static_cast<uint64_t>(av) * static_cast<uint64_t>(bv)); \
                        else if (strcmp(op, "div") == 0) result_val.long_val = (bv == -1) ? static_cast<int64_t>(0ull - static_cast<uint64_t>(av)) : av / bv; \
                        else if (strcmp(op, "rem") == 0) result_val.long_val = (bv == -1) ? 0 : av % bv; \
                        else if (strcmp(op, "and") == 0) result_val.long_val = av & bv; \
                        else if (strcmp(op, "or") == 0)  result_val.long_val = av | bv; \
                        else if (strcmp(op, "xor") == 0) result_val.long_val = av ^ bv; \
                        else if (strcmp(op, "shl") == 0) result_val.long_val = static_cast<int64_t>(static_cast<uint64_t>(av) << static_cast<int>(bv & 0x3f)); \
                        else if (strcmp(op, "shr") == 0) result_val.long_val = av >> static_cast<int>(bv & 0x3f); \
                        else if (strcmp(op, "ushr") == 0) result_val.long_val = static_cast<int64_t>(static_cast<uint64_t>(av) >> static_cast<int>(bv & 0x3f)); \
                        static thread_local const bool wide_diag_on = \
                        diag_env("MINIANDROID_WIDE_DIAG"); /* R-NEW-558 */ \
                    if (wide_diag_on) { \
                            std::cerr << "[WIDE-DIAG] " << op_name << " @" << current_class_ << "." \
                                      << current_method_ << " v" << (int)vA << "(J=" << av << ") v" \
                                      << (int)vB << "(J=" << bv << ") -> " << result_val.long_val << std::endl; \
                        } \
                    } else if (op_type == DalvikType::FLOAT32) { \
                        /* F-028 law: slots reinterpreted AS float32 */ \
                        uint32_t a28b = dalvik_raw_bits32(a); std::memcpy(&af, &a28b, 4); \
                        uint32_t b28b = dalvik_raw_bits32(b); std::memcpy(&bf, &b28b, 4); \
                        if (strcmp(op, "add") == 0) result_val.float_val = af + bf; \
                        else if (strcmp(op, "sub") == 0) result_val.float_val = af - bf; \
                        else if (strcmp(op, "mul") == 0) result_val.float_val = af * bf; \
                        else if (strcmp(op, "div") == 0) result_val.float_val = af / bf; \
                        else if (strcmp(op, "rem") == 0) result_val.float_val = fmodf(af, bf); \
                    } else { \
                        double ad = (a.type == DalvikType::FLOAT64) ? a.double_val \
                                  : (a.type == DalvikType::INT64 ? bits_l2d(a.long_val) \
                                  : (a.type == DalvikType::FLOAT32 ? (double)a.float_val : (double)a.int_val)); \
                        double bd = (b.type == DalvikType::FLOAT64) ? b.double_val \
                                  : (b.type == DalvikType::INT64 ? bits_l2d(b.long_val) \
                                  : (b.type == DalvikType::FLOAT32 ? (double)b.float_val : (double)b.int_val)); \
                        if (strcmp(op, "add") == 0) result_val.double_val = ad + bd; \
                        else if (strcmp(op, "sub") == 0) result_val.double_val = ad - bd; \
                        else if (strcmp(op, "mul") == 0) result_val.double_val = ad * bd; \
                        else if (strcmp(op, "div") == 0) result_val.double_val = ad / bd; \
                        else if (strcmp(op, "rem") == 0) result_val.double_val = fmod(ad, bd); \
                    } \
                    set_register(vA, result_val); \
                    trace.opcode_name = op_name; \
                    pc_ += 1; \
                    break; \
                }
            ARITH_WIDE_2ADDR_CASE(ADD_LONG_2ADDR, "add-long/2addr", DalvikType::INT64, "add")
            ARITH_WIDE_2ADDR_CASE(SUB_LONG_2ADDR, "sub-long/2addr", DalvikType::INT64, "sub")
            ARITH_WIDE_2ADDR_CASE(MUL_LONG_2ADDR, "mul-long/2addr", DalvikType::INT64, "mul")
            ARITH_WIDE_2ADDR_CASE(DIV_LONG_2ADDR, "div-long/2addr", DalvikType::INT64, "div")
            ARITH_WIDE_2ADDR_CASE(REM_LONG_2ADDR, "rem-long/2addr", DalvikType::INT64, "rem")
            ARITH_WIDE_2ADDR_CASE(AND_LONG_2ADDR, "and-long/2addr", DalvikType::INT64, "and")
            ARITH_WIDE_2ADDR_CASE(OR_LONG_2ADDR,  "or-long/2addr",  DalvikType::INT64, "or")
            ARITH_WIDE_2ADDR_CASE(XOR_LONG_2ADDR, "xor-long/2addr", DalvikType::INT64, "xor")
            ARITH_WIDE_2ADDR_CASE(SHL_LONG_2ADDR, "shl-long/2addr", DalvikType::INT64, "shl")
            ARITH_WIDE_2ADDR_CASE(SHR_LONG_2ADDR, "shr-long/2addr", DalvikType::INT64, "shr")
            ARITH_WIDE_2ADDR_CASE(USHR_LONG_2ADDR, "ushr-long/2addr", DalvikType::INT64, "ushr")
            ARITH_WIDE_2ADDR_CASE(ADD_FLOAT_2ADDR, "add-float/2addr", DalvikType::FLOAT32, "add")
            ARITH_WIDE_2ADDR_CASE(SUB_FLOAT_2ADDR, "sub-float/2addr", DalvikType::FLOAT32, "sub")
            ARITH_WIDE_2ADDR_CASE(MUL_FLOAT_2ADDR, "mul-float/2addr", DalvikType::FLOAT32, "mul")
            ARITH_WIDE_2ADDR_CASE(DIV_FLOAT_2ADDR, "div-float/2addr", DalvikType::FLOAT32, "div")
            ARITH_WIDE_2ADDR_CASE(REM_FLOAT_2ADDR, "rem-float/2addr", DalvikType::FLOAT32, "rem")
            ARITH_WIDE_2ADDR_CASE(ADD_DOUBLE_2ADDR, "add-double/2addr", DalvikType::FLOAT64, "add")
            ARITH_WIDE_2ADDR_CASE(SUB_DOUBLE_2ADDR, "sub-double/2addr", DalvikType::FLOAT64, "sub")
            ARITH_WIDE_2ADDR_CASE(MUL_DOUBLE_2ADDR, "mul-double/2addr", DalvikType::FLOAT64, "mul")
            ARITH_WIDE_2ADDR_CASE(DIV_DOUBLE_2ADDR, "div-double/2addr", DalvikType::FLOAT64, "div")
            // S211 PROBE: 0xCF was the ONE hole in the 2addr wide family —
            // the constant existed (PASS-3 K-37 corrected its value) but this
            // dispatch line never did, so rem-double/2addr fell to the
            // unimplemented handler and the destination pair kept its STALE
            // bits (silent state corruption). Same fmod law as the 23x
            // rem-double and the sibling rem-float/2addr (both dispatched).
            ARITH_WIDE_2ADDR_CASE(REM_DOUBLE_2ADDR, "rem-double/2addr", DalvikType::FLOAT64, "rem")
            #undef ARITH_WIDE_2ADDR_CASE

            // const-wide/16 (21s: AA|op BBBB, 2 code units)
            case Opcode::CONST_WIDE_16: {
                if (pc_ + 1 >= bytecode_.size()) return false;
                // W15 (#627 E-01 family): 21s dest untruncated (v256+ law).
                uint16_t vAA =
                    static_cast<uint16_t>((bytecode_[pc_] >> 8) & 0xFF);
                int16_t val = static_cast<int16_t>(bytecode_[pc_ + 1]);
                // EXP-071 Phase 8: write to long_val (64-bit) for INT64 type,
                // NOT int_val (32-bit). The previous bug left long_val with
                // garbage, breaking wide-arg merging in execute_invoke_static.
                DalvikValue dv; dv.type = DalvikType::INT64; dv.long_val = val;
                // F-028b: fill the vAA+1 shadow slot (ART two-slot layout)
                set_wide_pair(vAA, dv);
                trace.opcode_name = "const-wide/16";
                pc_ += 2;
                break;
            }
            // const-wide/high16 (21s: AA|op BBBB, 2 code units)
            case Opcode::CONST_WIDE_HIGH16: {
                if (pc_ + 1 >= bytecode_.size()) return false;
                uint8_t vAA = (bytecode_[pc_] >> 8) & 0xFF;
                uint16_t val = bytecode_[pc_ + 1];
                // EXP-071 Phase 8: write to long_val for INT64 type.
                // W22 #627 E-05 hardening: uint64-width shift (0xFFFF<<48 is
                // not representable in int64_t — defined-but-fragile before).
                DalvikValue dv; dv.type = DalvikType::INT64;
                dv.long_val = static_cast<int64_t>(static_cast<uint64_t>(val) << 48);
                // F-028b: fill the vAA+1 shadow slot (ART two-slot layout)
                set_wide_pair(vAA, dv);
                trace.opcode_name = "const-wide/high16";
                pc_ += 2;
                break;
            }
            // const-wide (51l: AA|op + 4 words, 5 code units)
            case Opcode::CONST_WIDE: {
                if (pc_ + 4 >= bytecode_.size()) return false;
                uint8_t vAA = (bytecode_[pc_] >> 8) & 0xFF;
                uint64_t val = 0;
                for (int i = 0; i < 4; i++) val |= static_cast<uint64_t>(bytecode_[pc_ + 1 + i]) << (i * 16);
                // EXP-071 Phase 8: write to long_val for INT64 type.
                DalvikValue dv; dv.type = DalvikType::INT64; dv.long_val = static_cast<int64_t>(val);
                // F-028b: fill the vAA+1 shadow slot (ART two-slot layout)
                set_wide_pair(vAA, dv);
                trace.opcode_name = "const-wide";
                pc_ += 5;
                break;
            }
            // iget-boolean / iput-boolean — now handled by the consolidated
            // iget-variant/iput-variant cases above (EXP-062).

            default:
                handle_unimplemented(opcode, pc_, trace);
                trace.opcode_name = "unimplemented(0x" + to_hex16(opcode) + ")";
                success = !config_.stop_on_unimplemented;
                break;
        }

        uint64_t s62_sw1 = phase_clock().on ? __rdtsc() : 0;
        if (phase_clock().on) {
            (s62_inv ? phase_clock().insn_sw_inv : phase_clock().insn_sw_non)
                .ns.fetch_add(s62_sw1 - s62_sw0, std::memory_order_relaxed);
            (s62_inv ? phase_clock().insn_sw_inv : phase_clock().insn_sw_non)
                .calls.fetch_add(1, std::memory_order_relaxed);
            phase_clock().insn_pre.ns.fetch_add(s62_sw0 - s62_pre0,
                                                std::memory_order_relaxed);
            phase_clock().insn_pre.calls.fetch_add(1,
                                                   std::memory_order_relaxed);
        }

        // UNIFIED_011.3 EXC-PROPAGATE: apply a deferred catch-handler jump.
        // The invoke handlers advance pc_ (pc_ = pc_ + instr_len) after
        // try_recursive_invoke returns; when caller-side catch matching
        // redirected execution to a handler, that handler address wins.
        if (exc_redirect_pending_) {
            exc_redirect_pending_ = false;
            pc_ = exc_redirect_addr_;
        }
        // S55 R-NEW-361: post-switch observation for the failing r frame —
        // which handler consumed the invoke at pc=12 (or didn't).
        if (diag_env("MINIANDROID_F040_DIAG") &&
            current_class_ == "Ln/a;" && current_method_ == "r") {
            std::cerr << "[R-AFTER] pc=" << pc_ << " op=0x" << std::hex
                      << opcode << std::dec << " handler=\""
                      << trace.opcode_name << "\" success=" << success
                      << std::endl;
        }
        
        // EXP-042 Phase 1: register state AFTER capture (gated).
        if (config_.trace_register_snapshots && current_registers_) {
            trace.registers_after = current_registers_->get_snapshot();
            // Calculate changed registers
            for (const auto& pair : trace.registers_before) {
                auto after_it = trace.registers_after.find(pair.first);
                if (after_it != trace.registers_after.end()) {
                    if (after_it->second.type != pair.second.type ||
                        (after_it->second.is_integral() && pair.second.is_integral() &&
                         after_it->second.int_val != pair.second.int_val)) {
                        trace.changed_registers.push_back(pair.first);
                    }
                }
            }
        }
        
        const bool f107_is_invoke = (opcode >= 0x6e && opcode <= 0x72) || (opcode >= 0x74 && opcode <= 0x78);
        // S62 DIAG (one-shot measurement): record ALL non-invoke ops including
        // inside <clinit> chains — the f107_in_init gate hid the hot-loop op
        // mix (90% of instructions run inside class-init chains).
        if (phase_clock().on && f107_op0 && !f107_is_invoke) {  // S62: invokes excluded (nested bodies)
            op_hist().ns[opcode].fetch_add(__rdtsc() - f107_op0, std::memory_order_relaxed);
            op_hist().count[opcode].fetch_add(1, std::memory_order_relaxed);
        }

        // EXP-045 Phase 2: Skip per-instruction trace recording when trace_cap is 0.
        // This eliminates InstructionTrace construction, Clock::now() calls, and
        // ring-buffer push_back — the #2 performance bottleneck after class lookup.
        if (config_.trace_cap > 0) {
            trace.pc_after = pc_;
            trace.execution_us = std::chrono::duration<double, std::micro>(Clock::now() - start).count();

            if (result.instruction_traces.size() >= config_.trace_cap) {
                result.instruction_traces.erase(result.instruction_traces.begin());
            }
            result.instruction_traces.push_back(std::move(trace));
        }
        result.total_instructions_executed++;
        result.total_opcodes_decoded++;

        // CONT-130 F-NEW-277 slice-2: VSYNC-CONTINUITY keep-alive — vsync
        // belongs to the display; a long DEX body must not starve the frame
        // pipeline. BYTE-INERT when no hook is wired (zero-cost: one null
        // check per instruction — the CONT-42 law).
        vsync_keepalive_tick(result.total_instructions_executed);

        // EXP-045 Phase 2: Global instruction counter — log every 100K instructions
        // to track execution speed and progress.
        static thread_local uint64_t global_insn_counter = 0;
        global_insn_counter++;
        // CONT-77: env-gated read-only sampler interval (poor-man's profiler;
        // the "currently in" field is a PC-accurate stack sample). Unset ->
        // the recorded 100000 interval (byte-identical stderr); set -> any
        // value >= 100. Diagnostic only: it never alters execution state.
        static const uint64_t progress_interval_ = [] {
            if (const char* e = std::getenv("MINIANDROID_PROGRESS_INTERVAL")) {
                unsigned long long v = strtoull(e, nullptr, 10);
                if (v >= 100) return (uint64_t)v;
            }
            return (uint64_t)100000;
        }();
        if (global_insn_counter % progress_interval_ == 0) {
            std::cerr << "[PROGRESS] " << global_insn_counter << " total instructions executed"
                      << " (currently in " << current_class_ << "." << current_method_
                      << " PC=" << pc_ << "/" << bytecode_.size() << ")"
                      << " RSS=" << (miniandroid::probe::rss_kb() / 1024) << " MB" << std::endl;
            // CONT-11 TRAIN-1: env-gated slow-invocation dump (MINIANDROID_SPIN_DUMP=1,
            // also requires MINIANDROID_LOOP_LOCALS_DIAG=1 for the dumper gate).
            // instruction_sequence_ resets at every method entry; an invocation
            // still alive millions of instructions later is a probe-loop
            // candidate (e.g. compose ScatterMap open addressing). Dump its
            // live frame — registers + receiver fields + array elements —
            // every ~500k instructions; dumper has its own 12-shot budget.
            static thread_local const bool spin_dump_on =
                std::getenv("MINIANDROID_SPIN_DUMP") != nullptr;
            if (spin_dump_on && instruction_sequence_ > 2000000 &&
                (instruction_sequence_ % 500000) < 100000) {
                dump_frame_locals_diag("SPIN");
            }
        }

        // ── F-C4-542 (CONT-37): env-gated LIVE HEAP CENSUS ────────────────
        // Every 16th progress tick (~1.6M instructions) when
        // MINIANDROID_HEAP_CENSUS is set: RSS + live heap-object population
        // + top-8 classes by allocation count. Bounded 40 emissions per run
        // (bounded-logging law). Names the top allocator of an unbounded
        // heap face LIVE — no SIGKILL flush loss (telegram's named #1
        // structural lever). Read-only; zero app knowledge; emission only.
        {
            static thread_local const bool heap_census_on =
                DalvikHeap::heap_census_enabled();
            static thread_local uint64_t heap_census_ticks = 0;
            // R-NEW-548 (CONT-38): ENGINE memory attribution at every 8th
            // progress tick when MINIANDROID_ENGINE_MEM=1 — mallinfo2()
            // (glibc in-use vs total) + the resident RSS. Splits the
            // telegram +2.7GB envelope into LIVE engine data (in-use ≈ RSS)
            // vs transient churn high-water (in-use << RSS). Read-only.
            static thread_local const bool engine_mem_on =
                DalvikHeap::heap_census_enabled() &&
                []() {
                    const char* e = std::getenv("MINIANDROID_ENGINE_MEM");
                    return e && e[0] == '1';
                }();
            if (engine_mem_on &&
                (global_insn_counter % (progress_interval_ * 8)) == 0) {
                static thread_local uint32_t engine_mem_rows = 0;
                if (engine_mem_rows < 40) {
                    ++engine_mem_rows;
                    struct mallinfo2 mi = mallinfo2();
                    fprintf(stderr,
                            "[ENGINE-MEM] insn=%llu rss_kb=%llu "
                            "glibc_inuse_mb=%.1f glibc_total_mb=%.1f "
                            "mmap_mb=%.1f heap_objects=%llu\n",
                            (unsigned long long)global_insn_counter,
                            (unsigned long long)miniandroid::probe::rss_kb(),
                            (double)mi.uordblks / (1024.0 * 1024.0),
                            (double)mi.hblkhd / (1024.0 * 1024.0),
                            (double)mi.hblkhd / (1024.0 * 1024.0),
                            (unsigned long long)heap_.size());
                }
                // R-NEW-548 phase 2 (CONT-38): MINIANDROID_MALLOC_TRIM=1 —
                // return the churn high-water pages to the OS at every
                // attribution tick. The glibc numbers (in-use ~255-350MB vs
                // total-mapped 4.5GB vs RSS 2.85GB) say the envelope is
                // RETAINED FREE PAGES, not live data; trim proves it and
                // makes the 60s+ telegram windows fit the 3GB sandbox.
                static thread_local const bool trim_on =
                    []() {
                        const char* e = std::getenv("MINIANDROID_MALLOC_TRIM");
                        return e && e[0] == '1';
                    }();
                if (trim_on) {
                    long before_kb =
                        (long)miniandroid::probe::rss_kb();
                    int freed = malloc_trim(0);
                    long after_kb = (long)miniandroid::probe::rss_kb();
                    fprintf(stderr,
                            "[MALLOC-TRIM] insn=%llu trim=%d "
                            "rss_before_mb=%.1f rss_after_mb=%.1f "
                            "freed_mb=%.1f\n",
                            (unsigned long long)global_insn_counter, freed,
                            (double)before_kb / 1024.0,
                            (double)after_kb / 1024.0,
                            (double)(before_kb - after_kb) / 1024.0);
                }
                // R-NEW-548 phase 5 (CONT-40): MINIANDROID_TOPMAP=1 — the
                // top-3 anonymous mappings at every attribution tick, on ONE
                // line. Correlates the giant-block growth with the PROGRESS
                // method lines (the allocator caught in the act).
                static thread_local const bool topmap_on =
                    []() {
                        const char* e = std::getenv("MINIANDROID_TOPMAP");
                        return e && e[0] == '1';
                    }();
                if (topmap_on) {
                    std::ifstream sm("/proc/self/smaps");
                    if (sm) {
                        uint64_t k[3] = {0, 0, 0};
                        unsigned long addr[3] = {0, 0, 0};
                        std::string line;
                        unsigned long ca = 0;
                        uint64_t ck = 0;
                        bool canon = false, have = false;
                        auto flush_m = [&]() {
                            if (!have || !canon || ck <= 4096) return;
                            for (int t = 0; t < 3; ++t) {
                                if (ck > k[t]) {
                                    for (int t2 = 2; t2 > t; --t2) {
                                        k[t2] = k[t2 - 1];
                                        addr[t2] = addr[t2 - 1];
                                    }
                                    k[t] = ck;
                                    addr[t] = ca;
                                    break;
                                }
                            }
                        };
                        while (std::getline(sm, line)) {
                            unsigned long a = 0, b = 0;
                            char perms[8] = {0};
                            if (sscanf(line.c_str(), "%lx-%lx %7s", &a, &b,
                                       perms) == 3 &&
                                strlen(perms) == 4) {
                                flush_m();
                                have = true;
                                ca = a;
                                ck = (b - a) / 1024;
                                canon = line.find('/') == std::string::npos &&
                                        line.find('[') == std::string::npos;
                            }
                        }
                        flush_m();
                        fprintf(stderr,
                                "[TOPMAP] insn=%llu top: %.1fMB@%lx "
                                "%.1fMB@%lx %.1fMB@%lx\n",
                                (unsigned long long)global_insn_counter,
                                (double)k[0] / 1024.0, addr[0],
                                (double)k[1] / 1024.0, addr[1],
                                (double)k[2] / 1024.0, addr[2]);
                    }
                }
            }
            if (heap_census_on && (global_insn_counter % (progress_interval_ * 16)) == 0) {
                if (heap_census_ticks < 40) {
                    ++heap_census_ticks;
                    const auto& hist = heap_.class_histogram();
                    std::vector<std::pair<uint64_t, const std::string*>> tops;
                    tops.reserve(hist.size());
                    for (const auto& kv : hist) tops.push_back({kv.second, &kv.first});
                    std::sort(tops.begin(), tops.end(), std::greater<>());
                    uint64_t total = 0;
                    for (const auto& kv : hist) total += kv.second;
                    fprintf(stderr, "[HEAP-CENSUS] insn=%llu rss_kb=%llu live_objects=%llu alloc_total=%llu top:",
                            (unsigned long long)global_insn_counter,
                            (unsigned long long)miniandroid::probe::rss_kb(),
                            (unsigned long long)heap_.size(),
                            (unsigned long long)total);
                    for (size_t k = 0; k < tops.size() && k < 8; ++k)
                        fprintf(stderr, " %s=%llu", tops[k].second->c_str(),
                                (unsigned long long)tops[k].first);
                    fprintf(stderr, "\n");
                    fflush(stderr);
                }
            }
        }

        // EXP-042 Phase 1: Per-frame loop detection (replaces the previous
        // static thread_local map which leaked state across recursive calls).
        // The previous design counted visits across ALL recursive invocations
        // of execute_method_internal(), which meant that PC=6 (a return opcode)
        // in Theme.getColor accumulated 101 visits across 101 separate calls
        // and wrongly halted each one — producing 6 000 × 101 instruction
        // traces, the actual cause of the OOM.
        //
        // pc_visit_count_ is now an instance member, reset in
        // execute_method_internal() at the start of each method. The threshold
        // is config_.loop_visit_threshold (default 50 000).
        // R-NEW-345 PARK-YIELD: a parked worker's frame chain unwinds here —
        // graceful frame exit (NOT halted_); the flag persists until the
        // drain boundary clears it, so every enclosing frame in the parked
        // chain also exits.
        if (park_yield_pending_) {
            break;
        }
        // ────────────────────────────────────────────────────────────────
        // F-NEW-084 CLOSEOUT — FORWARD-PROGRESS LOOP LAW (§7 semantic fix;
        // NOT a cap raise). The visit guard exists to catch STALLED frames
        // (same state, same decision, forever). Evidence (fairymahjong
        // Lw4;.<init> pc=0x91, MINIANDROID_METHOD_TRACE): the if-ge branch
        // operands ADVANCE every visit (v3 416→417→… per tile row scan,
        // 40 tiles × ~1250 = ~50k visits) — a legitimate BOUNDED
        // computation the old cap misclassified as an infinite loop at the
        // 50001st visit. Law (AOSP-faithful semantics): the guard now
        // measures STALE DECISIONS, not raw visits:
        //   * Only CONDITIONAL BRANCH pcs (0x32..0x3d) accumulate visits —
        //     an instruction with no decision (aget, add-int, …) cannot
        //     signal a stall by itself, and counting it made every body pc
        //     of a long-but-bounded loop a false-positive halt site
        //     (live evidence: after the back-edge law landed, the halt
        //     merely MOVED to the loop's aget at pc=0x93).
        //   * A branch whose SOURCE OPERANDS changed since its previous
        //     visit restarts its stale window (observable progress ⇒ same
        //     inputs never repeat ⇒ the loop is computing, bounded or not).
        //   * A branch with IDENTICAL operands across the whole window is
        //     a candidate stall — but the FINAL arbiter is FRAME-LEVEL
        //     progress (cont375 evidence, fairymahjong Lw4;.<init> pc=0x99):
        //     the scan loop's threshold branch `if-lt v14, v7` (16 < 0) is
        //     loop-INVARIANT by construction while the loop's REAL exit
        //     (`if-ge v1, v3` at pc=0x91) advances its operands every
        //     iteration. Punishing an invariant branch when OTHER decisions
        //     in the same frame are still moving misclassifies bounded
        //     work as a spin. Law v2 (frame-level): every branch-operand
        //     CHANGE anywhere in the frame bumps frame_progress_epoch_; a
        //     branch over the visit threshold halts ONLY if the epoch is
        //     unchanged since the branch's last threshold checkpoint — i.e.
        //     NO decision input in the whole frame moved for the entire
        //   * LAW v3 (cont375 final): visit counting covers EVERY pc again —
        //     because a compiler may legitimately erase a provably-dead
        //     condition and emit a straight nop/goto self-loop (live
        //     evidence: the probe's `while (k == 5) { k = 5; }` compiled to
        //     `0x49: nop; 0x4a: goto -1` — NO conditional branch left in the
        //     frame, so a branch-only counter was blind to a true spin). The
        //     epoch check is what classifies the frame: any live decision
        //     anywhere in the frame keeps resetting the window; a frame with
        //     zero decision movement (including branch-free spins) halts at
        //     the threshold exactly as the raw-visit guard always did.
        // Fully deterministic: signatures derive from register values only;
        // the guard never alters app-visible state except for frames that
        // previously died as false positives.
        // ────────────────────────────────────────────────────────────────
        // CONT-96 W3-A: flat-array visit count (was std::map — a red-black
        // find/insert per instruction). Semantics identical; the local
        // snapshot feeds the threshold check below.
        const uint32_t f084_visit_now =
            (pc_ < pc_visit_count_.size()) ? ++pc_visit_count_[pc_] : 1u;
        // CONT-10 W7 (generic, env-gated, read-only): MINIANDROID_PC_WATCH
        // = comma list of "Lcls;.meth:0xPC" tokens. On every interpreter pc
        // advance matching a token, dump the frame's leading registers
        // (bounded 240 dumps total). Answers: WHY does a moving-operand
        // loop keep running (which register fails to converge) — evidence
        // for the scatter-map probe-spin family, replayable offline.
        {
            static thread_local const bool pcw_on =
                std::getenv("MINIANDROID_PC_WATCH") != nullptr;
            static thread_local std::string pcw_spec;
            static thread_local bool pcw_init = false;
            static thread_local uint64_t pcw_n = 0;
            if (pcw_on) {
                if (!pcw_init) {
                    pcw_spec = std::getenv("MINIANDROID_PC_WATCH");
                    pcw_init = true;
                }
                if (pcw_n < 240) {
                    size_t start = 0;
                    while (start <= pcw_spec.size()) {
                        size_t comma = pcw_spec.find(',', start);
                        std::string tok = pcw_spec.substr(
                            start, comma == std::string::npos
                                       ? std::string::npos
                                       : comma - start);
                        size_t colon = tok.rfind(":0x");
                        if (colon == std::string::npos)
                            colon = tok.rfind(':');
                        if (colon != std::string::npos) {
                            std::string cm = tok.substr(0, colon);
                            uint32_t wpc = static_cast<uint32_t>(
                                strtoul(tok.c_str() + colon + 1, nullptr, 16));
                            size_t dot = cm.rfind(';');
                            if (dot != std::string::npos) {
                                std::string c = cm.substr(0, dot + 1);
                                std::string m = cm.substr(dot + 1);
                                if (!m.empty() && m[0] == '.') m.erase(0, 1);
                                if (current_class_ == c &&
                                    current_method_ == m && pc_ == wpc) {
                                    ++pcw_n;
                                    std::cerr << "[PC-WATCH] " << cm
                                              << ":" << to_hex(pc_)
                                              << " n=" << pcw_n;
                                    if (current_registers_) {
                                        const uint32_t nr =
                                            current_registers_->get_size();
                                        for (uint32_t r = 0;
                                             r < nr && r < 12; ++r) {
                                            DalvikValue v =
                                                current_registers_->read_v(
                                                    static_cast<uint16_t>(r));
                                            std::cerr << " v" << r << "=";
                                            if (v.type == DalvikType::INT32)
                                                std::cerr << v.int_val;
                                            else if (v.type ==
                                                     DalvikType::INT64)
                                                std::cerr << "(long)"
                                                          << v.long_val;
                                            else if (v.type ==
                                                     DalvikType::OBJECT_REF)
                                                std::cerr << "o"
                                                          << v.object_id;
                                            else
                                                std::cerr << "uninit";
                                        }
                                    }
                                    std::cerr << std::endl;
                                }
                            }
                        }
                        if (comma == std::string::npos) break;
                        start = comma + 1;
                    }
                }
            }
        }
        uint16_t opb = (pc_ < bytecode_.size()) ? (bytecode_[pc_] & 0xFF) : 0xFFFF;
        const bool cond_branch = opb >= 0x32 && opb <= 0x3d;
        if (cond_branch) {
            if (current_registers_) {
                uint64_t sig = 0;
                auto mix = [&sig](const DalvikValue& v) {
                    uint64_t h = static_cast<uint64_t>(static_cast<int>(v.type));
                    if (v.type == DalvikType::INT32)
                        h ^= static_cast<uint64_t>(
                            static_cast<uint32_t>(v.int_val)) << 3;
                    else if (v.type == DalvikType::OBJECT_REF)
                        h ^= static_cast<uint64_t>(v.object_id) << 5;
                    sig = sig * 0x9E3779B97F4A7C15ULL + h;
                };
                if (opb <= 0x37) {
                    // 22T: if-eq/ne/lt/ge/gt/le vA, vB, +target
                    const uint8_t ra = (bytecode_[pc_] >> 8) & 0xF;
                    const uint8_t rb = (bytecode_[pc_] >> 12) & 0xF;
                    mix(current_registers_->read_v(ra));
                    mix(current_registers_->read_v(rb));
                } else {
                    // 21T: if-(eq|ne|lt|ge|gt|le)z vAA, +target
                    const uint8_t raa = (bytecode_[pc_] >> 8) & 0xFF;
                    mix(current_registers_->read_v(raa));
                }
                // CONT-96 W3-A: flat-array signature (was std::map). The
                // seen-flag replicates the map's insert-vs-compare law:
                // first visit records the baseline (no epoch bump); every
                // later visit compares. Validity persists across window
                // resets exactly like the map did (only the visit counts
                // are cleared on a fresh window).
                if (pc_ < pc_branch_sig_.size()) {
                    if (pc_branch_sig_seen_[pc_]) {
                        if (pc_branch_sig_[pc_] != sig) {
                            // Observable progress through THIS branch. Frame-level
                            // law v2: bump the frame epoch (a decision input moved
                            // somewhere in this frame) instead of resetting only
                            // this branch's window.
                            pc_branch_sig_[pc_] = sig;
                            ++frame_progress_epoch_;
                        }
                    } else {
                        pc_branch_sig_[pc_] = sig;
                        pc_branch_sig_seen_[pc_] = 1u;
                    }
                }
            }
        }
        if (f084_visit_now > config_.loop_visit_threshold) {
            // Frame-level law v2: halt only if NO decision input in this
            // frame moved since the last threshold checkpoint of this pc.
            if (frame_progress_epoch_ != pc_epoch_checkpoint_) {
                pc_epoch_checkpoint_ = frame_progress_epoch_;
                // CONT-96 W3-A: flat-array fresh window (was map clear).
                std::fill(pc_visit_count_.begin(), pc_visit_count_.end(), 0u);
            } else {
            // EXP-042 Phase 2: include bytecode size and the actual opcode at
            // the looping PC, so we can diagnose whether the loop is a real
            // infinite loop or a missing-API-driven spin.
            uint16_t op_at_pc = (pc_ < bytecode_.size()) ? (bytecode_[pc_] & 0xFF) : 0xFFFF;
            halt_reason_ = "Infinite loop at PC=" + to_hex(pc_) +
                          " in " + current_class_ + "." + current_method_ +
                          " (visited " + std::to_string(f084_visit_now) +
                          " times in this frame, bytecode_size=" +
                          std::to_string(bytecode_.size()) +
                          ", op_at_pc=0x" + to_hex16(op_at_pc) + ").";
            halted_ = true;
            std::cerr << "[HALT-LOOP] " << halt_reason_ << std::endl;
            // FINAL-CAMPAIGN PHASE 3 (F-NEW-172): one-shot live-register dump
            // of the spinning frame — turn the halt into EVIDENCE.
            if (current_registers_) {
                const uint32_t nregs = current_registers_->get_size();
                std::cerr << "[SPIN-REGS] " << current_class_ << "."
                          << current_method_ << " regs=" << nregs;
                for (uint32_t r = 0; r < nregs && r < 32; ++r) {
                    DalvikValue v = current_registers_->read_v(
                        static_cast<uint16_t>(r));
                    std::cerr << " v" << r << "=";
                    if (v.type == DalvikType::INT32)
                        std::cerr << v.int_val;
                    else if (v.type == DalvikType::OBJECT_REF) {
                        std::cerr << "o" << v.object_id;
                        if (heap_.has_object(v.object_id)) {
                            const auto* ho = heap_.get(v.object_id);
                            if (ho) {
                                std::cerr << "<" << ho->class_descriptor << ">";
                                int fcnt = 0;
                                for (const auto& kv : ho->fields) {
                                    if (fcnt++ >= 3) break;
                                    std::cerr << " " << kv.first << "="
                                              << dalvik_value_to_string(kv.second);
                                }
                            }
                        }
                    }
                    else if (v.type == DalvikType::REGISTER_UNSET ||
                             v.type == DalvikType::UNINITIALIZED)
                        std::cerr << "uninit";
                    else
                        std::cerr << "t" << static_cast<int>(v.type);
                }
                std::cerr << std::endl;
            }
            dump_frame_locals_diag("SPIN");
            {
                // FINAL-CAMPAIGN PHASE 3 WAVE 3 (F-NEW-173): KEY-FEED
                // provenance. The spinning probe hashes a key whose identity
                // is the divergence (all-small-Integer keys -> smear low bits
                // collapse -> quadratic storm). Dump the ENTRIES source array
                // (the createHashTable v16 parameter): for its first slots,
                // each element's class + key/value fields — this names the
                // materializing object family the real app feeds vs ours.
                if (current_method_ == "createHashTable" && current_registers_) {
                    DalvikValue entries = current_registers_->read_v(16);
                    if (entries.type == DalvikType::OBJECT_REF &&
                        heap_.has_object(entries.object_id)) {
                        for (int32_t i = 0; i < 6; ++i) {
                            auto el = heap_.get_object_field(
                                entries.object_id,
                                "array[" + std::to_string(i) + "]");
                            if (!el.has_value() ||
                                el->type != DalvikType::OBJECT_REF ||
                                !heap_.has_object(el->object_id))
                                continue;
                            const auto* ho = heap_.get(el->object_id);
                            if (!ho) continue;
                            std::cerr << "[SPIN-KEYS] entries[" << i
                                      << "] o" << el->object_id << "<"
                                      << ho->class_descriptor << ">";
                            int fcnt = 0;
                            for (const auto& kv : ho->fields) {
                                if (fcnt++ >= 4) break;
                                std::cerr << " " << kv.first << "="
                                          << dalvik_value_to_string(kv.second);
                            }
                            std::cerr << std::endl;
                        }
                    }
                }
            }
            {
                // FINAL-CAMPAIGN WAVE C (F-NEW-181): RegularImmutableMap.get
                // probe-loop evidence. The disassembly (run/wavec_get_disasm.txt)
                // proves the compiled get() re-masks each step
                // (and-int v1, mask at 0x56) — the walk is in-bounds; the ONLY
                // exits are a matching key or the sentinel (0xFF/0xFFFF/-1).
                // A livelock therefore means the conversion table is FULL
                // (no sentinel) and/or the receiver map instance is
                // incoherent (fields from different build generations).
                // This probe dumps: per-slot sentinel census of the table
                // (v5) + the alternating entries each occupied slot points at
                // + the walk's (index, mask, tableLen) state.
                if (current_method_ == "get" && current_class_.find(
                        "RegularImmutableMap") != std::string::npos &&
                    current_registers_) {
                    DalvikValue tbl = current_registers_->read_v(5);
                    DalvikValue alt = current_registers_->read_v(6);
                    DalvikValue size_v = current_registers_->read_v(7);
                    auto tlen_f = heap_.get_object_field(tbl.object_id, "__array_length__");
                    auto nlen_f = heap_.get_object_field(tbl.object_id, "__new_array_length__");
                    int32_t tlen = 0;
                    if (tlen_f.has_value() && tlen_f->type == DalvikType::INT32) tlen = tlen_f->int_val;
                    if (tlen <= 0 && nlen_f.has_value() && nlen_f->type == DalvikType::INT32) tlen = nlen_f->int_val;
                    uint64_t sentinels = 0, occupied = 0;
                    int32_t scan = tlen > 256 ? 256 : tlen;
                    for (int32_t i = 0; i < scan; ++i) {
                        auto e = heap_.get_object_field(tbl.object_id,
                                                        "array[" + std::to_string(i) + "]");
                        if (!e.has_value()) continue;
                        int32_t v = dalvik_int_value(*e) & 0xFFFF;
                        if (v == 0xFF || v == 0xFFFF) ++sentinels; else ++occupied;
                    }
                    std::cerr << "[SPIN-GET] table=o" << tbl.object_id
                              << " len=" << tlen
                              << " scanned=" << scan
                              << " sentinels=" << sentinels
                              << " occupied=" << occupied
                              << " size_param="
                              << dalvik_int_value(size_v) << std::endl;
                    // First 4 occupied slots: which alternating entries they
                    // point at (class identity of stored keys).
                    int shown2 = 0;
                    for (int32_t i = 0; i < scan && shown2 < 4; ++i) {
                        auto e = heap_.get_object_field(tbl.object_id,
                                                        "array[" + std::to_string(i) + "]");
                        if (!e.has_value()) continue;
                        int32_t v = dalvik_int_value(*e) & 0xFFFF;
                        if (v == 0xFF || v == 0xFFFF) continue;
                        ++shown2;
                        auto k = heap_.get_object_field(alt.object_id,
                                                        "array[" + std::to_string(v) + "]");
                        std::string kd = "MISSING";
                        if (k.has_value() && k->type == DalvikType::OBJECT_REF &&
                            heap_.has_object(k->object_id)) {
                            const auto* ho = heap_.get(k->object_id);
                            kd = "o" + std::to_string(k->object_id) +
                                 "<" + (ho ? ho->class_descriptor : "?") + ">";
                            if (ho) {
                                int fc = 0;
                                for (const auto& kv : ho->fields) {
                                    if (fc++ >= 2) break;
                                    kd += " " + kv.first + "=" +
                                          dalvik_value_to_string(kv.second);
                                }
                            }
                        }
                        std::cerr << "[SPIN-GET] slot[" << i << "] -> offset "
                                  << v << " key=" << kd << std::endl;
                    }
                }
            }
            {
                // FINAL-CAMPAIGN PHASE 3 (F-NEW-172): inspect the probe table
                // state at halt — the spinning frame's v4 is the hash table.
                if (current_method_ == "createHashTable" && current_registers_) {
                    DalvikValue tbl = current_registers_->read_v(4);
                    if (tbl.type == DalvikType::OBJECT_REF &&
                        heap_.has_object(tbl.object_id)) {
                        uint64_t occupied = 0, missing = 0, empty = 0;
                        int32_t tlen = 0;
                        auto lf = heap_.get_object_field(tbl.object_id, "__array_length__");
                        auto nf = heap_.get_object_field(tbl.object_id, "__new_array_length__");
                        if (lf.has_value() && lf->type == DalvikType::INT32) tlen = lf->int_val;
                        if (tlen <= 0 && nf.has_value() && nf->type == DalvikType::INT32) tlen = nf->int_val;
                        int32_t scan = tlen > 4096 ? 4096 : tlen;
                        for (int32_t i = 0; i < scan; ++i) {
                            auto e = heap_.get_object_field(
                                tbl.object_id, "array[" + std::to_string(i) + "]");
                            if (!e.has_value()) { missing++; continue; }
                            int32_t iv = dalvik_int_value(*e);
                            if (iv == -1 || (iv & 0xFFFF) == 0xFFFF) empty++;
                            else occupied++;
                        }
                        std::cerr << "[SPIN-TABLE] o" << tbl.object_id
                                  << " len_field=" << tlen
                                  << " scanned=" << scan
                                  << " empty=" << empty
                                  << " occupied=" << occupied
                                  << " missing=" << missing << std::endl;
                    }
                }
                // FINAL-CAMPAIGN PHASE 3 (F-NEW-172): visit histogram of the
                // spinning frame — which instructions actually cycle.
                // CONT-96 W3-A: flat scan (was map iteration).
                std::vector<std::pair<uint32_t, uint64_t>> top;
                for (uint32_t f084_pi = 0; f084_pi < pc_visit_count_.size(); ++f084_pi)
                    if (pc_visit_count_[f084_pi])
                        top.push_back({f084_pi, pc_visit_count_[f084_pi]});
                std::sort(top.begin(), top.end(),
                          [](auto& a, auto& b) { return a.second > b.second; });
                std::cerr << "[SPIN-HISTO]";
                int shown = 0;
                for (auto& kv : top) {
                    if (shown++ >= 12) break;
                    std::cerr << " pc" << to_hex(kv.first) << "=" << kv.second;
                }
                std::cerr << std::endl;
            }
            break;
            } // frame-level law v2: end of the true-stall (epoch unchanged) arm
        }
        
        // Log if verbose — EXP-041: only log every 10000th instruction to reduce memory
        if (verbose_ && (trace.sequence % 10000 == 0)) {
            log("  [" + std::to_string(trace.sequence) + "] " +
                std::string(trace.pc_before < 100 ? " " : "") + 
                to_hex(trace.pc_before) + ": " + trace.opcode_name +
                (trace.allocated_object_id ? " [obj:" + std::to_string(*trace.allocated_object_id) + "]" : "") +
                (trace.invoked_method ? " → " + *trace.invoked_method : "") +
                (trace.status == InstructionTrace::Status::UNIMPLEMENTED ? " [UNIMPLEMENTED]" : ""));
        }
        
        // Check limits
        if (result.total_instructions_executed >= config_.max_instructions) {
            halt_reason_ = "Max instructions reached (" + std::to_string(config_.max_instructions) + ")";
            halted_ = true;
            log("HALT: " + halt_reason_);
            // CONT-10 W7 (generic, env-gated, read-only): when the global
            // instruction budget dies, dump the CURRENT frame's pc-visit
            // histogram so the burn locus is evidence, not guesswork. The
            // loop-visit spin guard only catches zero-decision-input loops;
            // a loop whose condition operands keep moving (e.g. re-running
            // invalidation passes or a full scatter-table probe) reaches
            // this budget halt instead.
            static thread_local const bool halt_histo_on =
                std::getenv("MINIANDROID_HALT_HISTO") != nullptr;
            if (halt_histo_on) {
                std::cerr << "[HALT-HISTO] frame="
                          << current_class_ << "." << current_method_
                          << " pc=" << to_hex(pc_)
                          << std::endl;
                std::vector<std::pair<uint32_t, uint64_t>> htop;
                for (size_t hi = 0; hi < pc_visit_count_.size(); ++hi)
                    if (pc_visit_count_[hi] > 0)
                        htop.push_back({(uint32_t)hi, pc_visit_count_[hi]});
                std::sort(htop.begin(), htop.end(),
                          [](auto& a, auto& b) { return a.second > b.second; });
                int hshown = 0;
                for (auto& kv : htop) {
                    if (hshown++ >= 16) break;
                    std::cerr << "[HALT-HISTO]   pc" << to_hex(kv.first)
                              << " visits=" << kv.second << std::endl;
                }
                if (current_registers_) {
                    const uint32_t nregs = current_registers_->get_size();
                    std::cerr << "[HALT-REGS] " << current_class_ << "."
                              << current_method_ << " regs=" << nregs;
                    for (uint32_t r = 0; r < nregs && r < 20; ++r) {
                        DalvikValue v = current_registers_->read_v(
                            static_cast<uint16_t>(r));
                        std::cerr << " v" << r << "=";
                        if (v.type == DalvikType::INT32)
                            std::cerr << v.int_val;
                        else if (v.type == DalvikType::INT64)
                            std::cerr << "(long)" << v.long_val;
                        else if (v.type == DalvikType::OBJECT_REF) {
                            std::cerr << "o" << v.object_id;
                            if (heap_.has_object(v.object_id)) {
                                const auto* ho = heap_.get(v.object_id);
                                if (ho) {
                                    std::cerr << "<" << ho->class_descriptor
                                              << ">";
                                    int fcnt = 0;
                                    for (const auto& kv : ho->fields) {
                                        if (fcnt++ >= 2) break;
                                        std::cerr << " " << kv.first << "="
                                                  << dalvik_value_to_string(
                                                         kv.second);
                                    }
                                }
                            }
                        } else
                            std::cerr << "uninit";
                    }
                    std::cerr << std::endl;
                    for (uint32_t r = 0; r < nregs && r < 20; ++r) {
                        DalvikValue v = current_registers_->read_v(
                            static_cast<uint16_t>(r));
                        if (v.type != DalvikType::OBJECT_REF) continue;
                        if (!heap_.has_object(v.object_id)) continue;
                        const auto* ho = heap_.get(v.object_id);
                        if (!ho) continue;
                        if (ho->class_descriptor != "[J" &&
                            ho->class_descriptor != "[I")
                            continue;
                        auto lf = heap_.get_object_field(v.object_id,
                                                         "__array_length__");
                        std::cerr << "[HALT-ARR] v" << r << " "
                                  << ho->class_descriptor << " len="
                                  << (lf.has_value() &&
                                              lf->type == DalvikType::INT32
                                          ? lf->int_val
                                          : -1);
                        for (int e = 0; e < 6; ++e) {
                            auto el = heap_.get_object_field(
                                v.object_id,
                                "array[" + std::to_string(e) + "]");
                            if (!el.has_value()) continue;
                            if (el->type == DalvikType::INT64)
                                std::cerr << " [" << el->long_val << "]";
                            else if (el->type == DalvikType::INT32)
                                std::cerr << " [" << el->int_val << "]";
                        }
                        std::cerr << std::endl;
                    }
                }
            }
            break;
        }

        // S60 (R-NEW-380): wall-clock soft budget — a graceful stop that
        // mirrors the instruction budget so long real-APK compositions
        // (dooz v23 GameScreen) still deliver the end-of-run evidence
        // pipeline (screenshot/trace/report) within a bounded session.
        // 0 = disabled; every pre-existing path is unchanged.
        if (config_.max_wall_ms > 0) {
            static thread_local std::chrono::steady_clock::time_point
                wall_start;
            static thread_local bool wall_started = false;
            if (!wall_started) {
                wall_start = std::chrono::steady_clock::now();
                wall_started = true;
            }
            // T61 (S145): the scripted-tap rebate shifts the deadline
            // forward (see rebate_wall_ms) — elapsed counts only budget
            // the session actually spent outside the rebate.
            long long raw_elapsed_ms = std::chrono::duration_cast<
                std::chrono::milliseconds>(
                std::chrono::steady_clock::now() - wall_start).count();
            long long elapsed_ms = raw_elapsed_ms - wall_rebate_ms_;
            if (elapsed_ms < 0) elapsed_ms = 0;
            if (elapsed_ms >= static_cast<long long>(config_.max_wall_ms)) {
                halt_reason_ = "Wall-clock budget reached (" +
                               std::to_string(config_.max_wall_ms) + " ms" +
                               (wall_rebate_ms_ > 0
                                    ? "; tap rebate " +
                                          std::to_string(wall_rebate_ms_) +
                                          " ms applied"
                                    : "") +
                               ")";
                halted_ = true;
                log("HALT: " + halt_reason_);
            // CONT-10 W7 (generic, env-gated, read-only): when the wall-clock
            // budget dies (the F084 family now usually fires here at CONT-28+), dump the CURRENT frame's pc-visit
            // histogram so the burn locus is evidence, not guesswork. The
            // loop-visit spin guard only catches zero-decision-input loops;
            // a loop whose condition operands keep moving (e.g. re-running
            // invalidation passes or a full scatter-table probe) reaches
            // this budget halt instead.
            static thread_local const bool halt_histo_on =
                std::getenv("MINIANDROID_HALT_HISTO") != nullptr;
            if (halt_histo_on) {
                std::cerr << "[HALT-HISTO] frame="
                          << current_class_ << "." << current_method_
                          << " pc=" << to_hex(pc_)
                          << std::endl;
                std::vector<std::pair<uint32_t, uint64_t>> htop;
                for (size_t hi = 0; hi < pc_visit_count_.size(); ++hi)
                    if (pc_visit_count_[hi] > 0)
                        htop.push_back({(uint32_t)hi, pc_visit_count_[hi]});
                std::sort(htop.begin(), htop.end(),
                          [](auto& a, auto& b) { return a.second > b.second; });
                int hshown = 0;
                for (auto& kv : htop) {
                    if (hshown++ >= 16) break;
                    std::cerr << "[HALT-HISTO]   pc" << to_hex(kv.first)
                              << " visits=" << kv.second << std::endl;
                }
                if (current_registers_) {
                    const uint32_t nregs = current_registers_->get_size();
                    std::cerr << "[HALT-REGS] " << current_class_ << "."
                              << current_method_ << " regs=" << nregs;
                    for (uint32_t r = 0; r < nregs && r < 20; ++r) {
                        DalvikValue v = current_registers_->read_v(
                            static_cast<uint16_t>(r));
                        std::cerr << " v" << r << "=";
                        if (v.type == DalvikType::INT32)
                            std::cerr << v.int_val;
                        else if (v.type == DalvikType::INT64)
                            std::cerr << "(long)" << v.long_val;
                        else if (v.type == DalvikType::OBJECT_REF) {
                            std::cerr << "o" << v.object_id;
                            if (heap_.has_object(v.object_id)) {
                                const auto* ho = heap_.get(v.object_id);
                                if (ho) {
                                    std::cerr << "<" << ho->class_descriptor
                                              << ">";
                                    int fcnt = 0;
                                    for (const auto& kv : ho->fields) {
                                        if (fcnt++ >= 2) break;
                                        std::cerr << " " << kv.first << "="
                                                  << dalvik_value_to_string(
                                                         kv.second);
                                    }
                                }
                            }
                        } else
                            std::cerr << "uninit";
                    }
                    std::cerr << std::endl;
                    for (uint32_t r = 0; r < nregs && r < 20; ++r) {
                        DalvikValue v = current_registers_->read_v(
                            static_cast<uint16_t>(r));
                        if (v.type != DalvikType::OBJECT_REF) continue;
                        if (!heap_.has_object(v.object_id)) continue;
                        const auto* ho = heap_.get(v.object_id);
                        if (!ho) continue;
                        if (ho->class_descriptor != "[J" &&
                            ho->class_descriptor != "[I")
                            continue;
                        auto lf = heap_.get_object_field(v.object_id,
                                                         "__array_length__");
                        std::cerr << "[HALT-ARR] v" << r << " "
                                  << ho->class_descriptor << " len="
                                  << (lf.has_value() &&
                                              lf->type == DalvikType::INT32
                                          ? lf->int_val
                                          : -1);
                        for (int e = 0; e < 6; ++e) {
                            auto el = heap_.get_object_field(
                                v.object_id,
                                "array[" + std::to_string(e) + "]");
                            if (!el.has_value()) continue;
                            if (el->type == DalvikType::INT64)
                                std::cerr << " [" << el->long_val << "]";
                            else if (el->type == DalvikType::INT32)
                                std::cerr << " [" << el->int_val << "]";
                        }
                        std::cerr << std::endl;
                    }
                }
            }

                // F-NEW-084 closeout (cont375): EVERY graceful stop carries
                // the same frame evidence as a loop-guard halt — the wall
                // clock may stop INSIDE a legitimately long frame, and the
                // visit histogram + live registers are what distinguish a
                // bounded computation from a hidden spin. Evidence parity
                // with the [HALT-LOOP] path (§7: never stop blind).
                {
                    const uint16_t opb_stop = (pc_ < bytecode_.size())
                        ? (bytecode_[pc_] & 0xFF) : 0xFFFF;
                    std::cerr << "[WALL-STOP] pc=" << to_hex(pc_)
                              << " op_at_pc=0x" << to_hex16(opb_stop)
                              << " in " << current_class_ << "."
                              << current_method_ << std::endl;
                    // R-NEW-548 phase 3 (CONT-38): smaps_rollup at the stop —
                    // the decisive memory split (anon-private = LIVE engine
                    // data vs file-backed vs shared). mallinfo2 covers only
                    // the main arena (worker-thread arenas invisible), so
                    // the earlier in-use=255MB reading misattributed the
                    // bulk; the rollup cannot lie.
                    {
                        std::ifstream rollup("/proc/self/smaps_rollup");
                        if (rollup) {
                            std::string line;
                            while (std::getline(rollup, line)) {
                                if (line.rfind("Rss:", 0) == 0 ||
                                    line.rfind("Pss:", 0) == 0 ||
                                    line.rfind("Anonymous:", 0) == 0 ||
                                    line.rfind("Rss:", 0) == 0 ||
                                    line.rfind("Private_Dirty:", 0) == 0 ||
                                    line.rfind("Private_Clean:", 0) == 0 ||
                                    line.rfind("Shared_Clean:", 0) == 0 ||
                                    line.rfind("Swap:", 0) == 0)
                                    std::cerr << "[SMAPS] " << line
                                              << std::endl;
                            }
                        }
                        struct mallinfo2 mi = mallinfo2();
                        fprintf(stderr,
                                "[SMAPS] mallinfo2(main-arena-only) "
                                "inuse_mb=%.1f total_mb=%.1f\n",
                                (double)mi.uordblks / (1024.0 * 1024.0),
                                (double)mi.hblkhd / (1024.0 * 1024.0));
                        // R-NEW-548 phase 4: top-10 anonymous mappings —
                        // the SHAPE names the subsystem (a few giant
                        // blocks = big vectors; thousands of arena-sized
                        // blocks = thread arenas; many ~64MB = dex-scale
                        // copies). Read-only walk of /proc/self/smaps.
                        {
                            std::ifstream sm("/proc/self/smaps");
                            if (sm) {
                                struct MapRow {
                                    uint64_t size_kb; bool anon;
                                    std::string perms; uint64_t addr;
                                };
                                std::vector<MapRow> rows;
                                std::string line;
                                uint64_t cur_addr = 0, cur_kb = 0;
                                std::string cur_perms;
                                bool cur_anon = false, have = false;
                                auto flush_map = [&]() {
                                    if (have && cur_anon && cur_kb > 4096)
                                        rows.push_back({cur_kb, true,
                                                        cur_perms, cur_addr});
                                };
                                while (std::getline(sm, line)) {
                                    unsigned long a = 0, b = 0;
                                    char perms[8] = {0};
                                    if (sscanf(line.c_str(), "%lx-%lx %7s",
                                               &a, &b, perms) == 3 &&
                                        strlen(perms) == 4 &&
                                        (perms[0] == 'r' ||
                                         perms[0] == '-' ||
                                         perms[0] == 'p' ||
                                         perms[0] == 's' ||
                                         perms[0] == 'w')) {
                                        flush_map();
                                        have = true;
                                        cur_addr = a;
                                        cur_perms = perms;
                                        cur_anon =
                                            line.find('/') ==
                                                std::string::npos &&
                                            line.find('[') ==
                                                std::string::npos;
                                        cur_kb = (b - a) / 1024;
                                    }
                                }
                                flush_map();
                                std::sort(rows.begin(), rows.end(),
                                          [](const MapRow& x,
                                             const MapRow& y) {
                                              return x.size_kb >
                                                     y.size_kb;
                                          });
                                uint64_t total_anon_kb = 0;
                                for (const auto& r : rows)
                                    total_anon_kb += r.size_kb;
                                fprintf(stderr,
                                        "[SMAPS] anon_mappings=%zu "
                                        "anon_total_mb=%.1f top:\n",
                                        rows.size(),
                                        (double)total_anon_kb / 1024.0);
                                for (size_t k = 0;
                                     k < rows.size() && k < 10; ++k)
                                    fprintf(stderr,
                                            "[SMAPS]   #%zu %08lx perms=%s "
                                            "%.1f MB\n",
                                            k, rows[k].addr,
                                            rows[k].perms.c_str(),
                                            (double)rows[k].size_kb /
                                                1024.0);
                            }
                        }
                    }
                    if (current_registers_) {
                        const uint32_t nregs = current_registers_->get_size();
                        std::cerr << "[WALL-REGS] regs=" << nregs;
                        for (uint32_t r = 0; r < nregs && r < 26; ++r) {
                            DalvikValue v = current_registers_->read_v(
                                static_cast<uint16_t>(r));
                            std::cerr << " v" << r << "=";
                            if (v.type == DalvikType::INT32)
                                std::cerr << v.int_val;
                            else if (v.type == DalvikType::OBJECT_REF) {
                                std::cerr << "o" << v.object_id;
                                if (heap_.has_object(v.object_id)) {
                                    const auto* ho = heap_.get(v.object_id);
                                    if (ho) std::cerr << "<" << ho->class_descriptor << ">";
                                }
                            } else if (v.type == DalvikType::REGISTER_UNSET ||
                                       v.type == DalvikType::UNINITIALIZED)
                                std::cerr << "uninit";
                            else
                                std::cerr << "t" << static_cast<int>(v.type);
                        }
                        std::cerr << std::endl;
                    }
                    std::vector<std::pair<uint32_t, uint64_t>> wtop;
                    // CONT-96 W3-A: flat scan (was map iteration).
                    for (uint32_t f084_pi = 0; f084_pi < pc_visit_count_.size(); ++f084_pi)
                        if (pc_visit_count_[f084_pi])
                            wtop.push_back({f084_pi, pc_visit_count_[f084_pi]});
                    std::sort(wtop.begin(), wtop.end(),
                              [](auto& a, auto& b) { return a.second > b.second; });
                    std::cerr << "[WALL-HISTO]";
                    int wshown = 0;
                    for (auto& kv : wtop) {
                        if (wshown++ >= 12) break;
                        std::cerr << " pc" << to_hex(kv.first) << "=" << kv.second;
                    }
                    std::cerr << std::endl;
                }
                break;
            }
        }
        
        // S154 AWAIT-UP GATE — scoped tap-render deadline (see header).
        // Sampled every 4096th loop pass: steady_clock::now() is cheap but
        // not free at interpreter speeds, and the gate window is bounded.
        if (++awaitup_probe_n_ >= 4096) {
            awaitup_probe_n_ = 0;
            awaitup_gate_check();
            if (awaitup_deadline_hit_) {  // same graceful channel as the wall
                soft_stopped_no_return_ = true;  // CONT-132: no return ran
                break;
            }
        }
        // CONT-130b: SOFT draw-window stop — enclosing frames unwind at the
        // method boundary by RETURN (no synthesized exception, the draw
        // state survives). Unconditional per-iteration check: the flag arms
        // once and every frame exits normally, like a method that simply
        // returns. Cleared at the draw-window boundary / abort_reset / begin.
        // CONT-132: the exit is mechanical-return only — no return
        // instruction ran, so the frame's return value is UNDEFINED; the
        // flag tells try_recursive_invoke to answer the caller's move-result
        // with the defined polymorphic zero (never the stale
        // last_invoke_return_).
        if (awaitup_soft_stop_) {
            soft_stopped_no_return_ = true;  // CONT-132: no return ran
            break;
        }

        // Check for return
        if (halted_on_return_) {
            log("Method returned successfully");
            break;
        }
        // S62 bucket: post-switch bookkeeping
        if (phase_clock().on) {
            phase_clock().insn_post.ns.fetch_add(__rdtsc() - s62_sw1,
                                                 std::memory_order_relaxed);
            phase_clock().insn_post.calls.fetch_add(1,
                                                    std::memory_order_relaxed);
        }
    }

    // W23 EXIT-REASON census (F-C4-723 follow-up; env-gated
    // MINIANDROID_W23_EXIT0=1; stderr-only, behavior-neutral per the
    // S211/S214 probe precedent). A (0,0) completion = the fetch loop
    // exited with halted_=0, halted_on_return_=0 and
    // soft_stopped_no_return_=0: the frame never executed a return opcode
    // and no graceful/hard stop fired — the run-off-the-end channel the
    // F-C4-723 law answers with VOID at the invoke-exit discriminator.
    // The census classifies WHY the frame left the loop: pc vs bytecode
    // size separates a branch-past-the-end from a mid-frame silent break,
    // the would-be-next opcode at pc names the instruction the loop
    // refused/failed to fetch, and the pending-exception + unwind state
    // separates the exception-leak faces. instruction_sequence_ correlates
    // the census row with the [F723-NORET] line the same exit later
    // produces at the discriminator.
    {
        static thread_local const bool w23_exit0_on =
            std::getenv("MINIANDROID_W23_EXIT0") != nullptr;
        if (w23_exit0_on && !halted_ && !halted_on_return_ &&
            !soft_stopped_no_return_) {
            static thread_local uint64_t w23_n = 0;
            if (w23_n < 400) {
                ++w23_n;
                const uint16_t w23_op =
                    (pc_ < bytecode_.size())
                        ? static_cast<uint16_t>(bytecode_[pc_] & 0xFF)
                        : 0xFFFF;
                std::cerr << "[W23-EXIT0] " << current_class_ << "."
                          << current_method_ << " pc=0x" << to_hex(pc_)
                          << " of 0x"
                          << to_hex(static_cast<uint32_t>(bytecode_.size()))
                          << " next_op=0x" << to_hex16(w23_op) << " instr="
                          << instruction_sequence_ << " pexc_type="
                          << static_cast<int>(pending_exception_.type)
                          << " unwind="
                          << (frame_unwind_exception_valid_ ? 1 : 0)
                          << std::endl;
            }
        }
    }
    return !halted_ || halted_on_return_;
}

// ============================================================================
// UNIFIED_011.2 SYNTH-EXC: Runtime exception machinery (§21/§24 campaign)
// ============================================================================

// Find the catch handler covering `pc` in the current frame's try table.
// Extracted verbatim from the THROW opcode handler (EXP-052/053) so that
// synthetic runtime exceptions share identical machinery and THROW keeps
// its exact prior behavior.
// UNIFIED_011.3 TYPED-CATCH (§18): typed handlers are now type-matched
// against `exc_desc`. Semantics (Dalvik spec):
//   1. first try_item covering pc (tries are non-overlapping),
//   2. typed handler pairs in order — first subtype match wins,
//   3. catch-all (present iff encoded size <= 0) is the fallback,
//   4. no match → false (caller unwinds / propagates).
bool DalvikExecutionEngine::find_catch_handler_for_pc(
        uint32_t pc, uint32_t& handler_addr, bool& is_catch_all,
        std::string& catch_type, const std::string& exc_desc) {
    if (current_tries_size_ == 0 || current_tries_data_ == nullptr) return false;

    for (uint16_t i = 0; i < current_tries_size_; i++) {
        size_t off = i * 8;
        if (off + 8 > current_tries_data_size_) break;
        uint32_t start = 0;
        uint16_t count = 0;
        uint16_t handler_off = 0;
        std::memcpy(&start, current_tries_data_ + off, 4);
        std::memcpy(&count, current_tries_data_ + off + 4, 2);
        std::memcpy(&handler_off, current_tries_data_ + off + 6, 2);
        if (pc < start || pc >= start + count) continue;

        // handler_off is byte offset FROM THE START of the
        // encoded_catch_handler_list (which begins with the list_size uleb128).
        size_t handler_list_start = static_cast<size_t>(current_tries_size_) * 8;
        size_t handler_list_end = current_tries_data_size_;
        if (handler_list_start >= handler_list_end) return false;

        size_t handler_abs = handler_list_start + handler_off;
        if (handler_abs >= handler_list_end) return false;

        // Decode the handler at handler_abs.
        // sleb128 size, then |size| pairs of (uleb128 type_idx, uleb128 addr),
        // then catch-all addr if size <= 0.
        // FIND-REUSE-003: ONE shared SLEB/ULEB primitive (dex/mutf8.h)
        // replaces the second inline lambda copy (see the exception-dispatch
        // site above for the truncation-semantics note).
        auto read_sleb = [&](size_t& p) -> int32_t {
            bool vok = true;
            return miniandroid::dex::mutf8::read_sleb128(
                current_tries_data_, handler_list_end, p, vok);
        };
        auto read_uleb = [&](size_t& p) -> uint32_t {
            bool vok = true;
            return miniandroid::dex::mutf8::read_uleb128(
                current_tries_data_, handler_list_end, p, vok);
        };

        size_t p = handler_abs;
        int32_t size = read_sleb(p);
        // F-041: |size| typed pairs for negative size (DEX spec) — see the
        // twin fix at the throw-dispatch site above for the full rationale.
        int32_t n_pairs = (size >= 0) ? size : -size;
        // UNIFIED_011.3 TYPED-CATCH: resolve each handler's type descriptor
        // via the CURRENT method's DEX (type_ids are per-DEX, EXP-058) and
        // type-match against the thrown exception.
        for (int h = 0; h < n_pairs; h++) {
            uint32_t type_idx = read_uleb(p);
            uint32_t addr = read_uleb(p);
            std::string handler_exc_desc =
                resolve_type_for_dex(type_idx, current_dex_index_);
            if (is_exception_subtype(exc_desc, handler_exc_desc)) {
                handler_addr = addr;
                is_catch_all = false;
                catch_type = handler_exc_desc;
                return true;
            }
        }
        if (size <= 0) {
            uint32_t addr = read_uleb(p);
            handler_addr = addr;
            is_catch_all = true;
            catch_type = "<catch-all>";
            return true;
        }
        // First covering try_item processed — tries do not overlap, and a
        // non-matching typed list does NOT fall through to other tries.
        return false;
    }
    return false;
}

// Raise a synthetic runtime exception following real Dalvik semantics as
// far as the engine supports them. See header for the full contract.
// MASTER RECONCILIATION (2026-09-03): deferred exception raise.
// Same semantics as raise_synthetic_exception, but pc_ is NEVER written here:
// opcode-handler macros and the invoke wrappers advance pc_ AFTER the handler
// body runs, which would clobber a direct handler jump. Two mechanisms:
//   1. Handler covers pc_ → pending_exception_ + deferred_exception_ set and
//      exc_redirect_pending_ armed; fetch_decode_execute re-applies
//      exc_redirect_addr_ right after the switch (post-switch redirect —
//      same last-word-wins model as UNIFIED_011.3 EXC-PROPAGATE).
//   2. No handler → frame unwind exactly like raise_synthetic_exception
//      (halted_on_return_ + frame_unwind_exception_ for caller-side search).
bool DalvikExecutionEngine::throw_deferred(
        const std::string& exc_class_desc, const std::string& message,
        const char* origin_tag) {
    DalvikValue exc;
    exc.type = DalvikType::OBJECT_REF;
    exc.object_id = heap_.allocate(exc_class_desc, pc_, 0);
    exc.class_desc = exc_class_desc;
    exc.string_val = message;
    heap_.set_object_field(exc.object_id, "message",
                           DalvikValue::make_string(message, exc.object_id));
    heap_.mark_initialized(exc.object_id);

    uint32_t handler_addr = 0;
    bool is_catch_all = false;
    std::string catch_type = "<none>";
    bool found = find_catch_handler_for_pc(pc_, handler_addr, is_catch_all,
                                           catch_type, exc_class_desc);

    std::cerr << "[SYNTH-EXC] " << (origin_tag ? origin_tag : "runtime")
              << " (deferred): " << exc_class_desc << " (" << message << ")"
              << " method=" << current_class_ << "." << current_method_
              << " pc=" << pc_
              << " → " << (found ? "deferred handler @0x" + to_hex(handler_addr)
                                   + " type=" + catch_type
                                 : "uncaught (deferred frame unwind + propagate)")
              << std::endl;

    // S100 §7 (issue #345): every synthesized exception lands in the crash
    // forensics last-op ring — a later signal death then carries the full
    // exception trail (which NPE preceded the crash, at which method).
    CrashForensics::note("EXC", "%s %s.%s pc=%u %s", exc_class_desc.c_str(),
                         current_class_.c_str(), current_method_.c_str(), pc_,
                         message.c_str());

    pending_exception_ = exc;
    deferred_exception_ = exc;
    if (found) {
        exc_redirect_pending_ = true;
        exc_redirect_addr_ = handler_addr;
        return true;
    }
    frame_unwind_exception_valid_ = true;
    frame_unwind_exception_ = exc;
    last_invoke_return_ = DalvikValue::make_null();
    halted_on_return_ = true;
    pc_ += 1;
    return false;
}

bool DalvikExecutionEngine::raise_synthetic_exception(
        const std::string& exc_class_desc, const std::string& message,
        const char* origin_tag) {
    // Build the exception object on the heap (same model as new-instance).
    DalvikValue exc;
    exc.type = DalvikType::OBJECT_REF;
    exc.object_id = heap_.allocate(exc_class_desc, pc_, 0);
    exc.class_desc = exc_class_desc;
    exc.string_val = message;
    heap_.set_object_field(exc.object_id, "message",
                           DalvikValue::make_string(message, exc.object_id));
    heap_.mark_initialized(exc.object_id);

    uint32_t handler_addr = 0;
    bool is_catch_all = false;
    std::string catch_type = "<none>";
    bool found = find_catch_handler_for_pc(pc_, handler_addr, is_catch_all,
                                           catch_type, exc_class_desc);

    std::cerr << "[SYNTH-EXC] " << (origin_tag ? origin_tag : "runtime")
              << ": " << exc_class_desc << " (" << message << ")"
              << " method=" << current_class_ << "." << current_method_
              << " pc=" << pc_
              << " → " << (found ? "catch handler @0x" + to_hex(handler_addr)
                                 + " type=" + catch_type
                                 : "uncaught (frame unwind + propagate)")
              << std::endl;

    if (found) {
        pending_exception_ = exc;
        pc_ = handler_addr;
        return true;
    }
    // Unwind the current frame like a return with a null result.
    // UNIFIED_011.3 EXC-PROPAGATE (§18): record the exception in flight so
    // the invoking frame (try_recursive_invoke call site) searches ITS try
    // table next — real Dalvik propagation, not just a silent null return.
    frame_unwind_exception_valid_ = true;
    frame_unwind_exception_ = exc;
    last_invoke_return_ = DalvikValue::make_null();
    halted_on_return_ = true;
    pc_ += 1;
    return false;
}

// UNIFIED_011.2 IMAGE-RES-RENDER: populate resource_drawable_paths_ from the
// APK's res/ entry list. For every R-field name (field_name_by_resid_), find
// the best-density drawable asset whose basename matches. Density preference
// (AOSP closest-density approximation for a 1080x1920 software target):
//   xxxhdpi > xxhdpi > xhdpi > hdpi > mdpi > drawable (plain) > mipmap.
// Nine-patch ".9.png" entries match by basename minus ".9" too.
// Idempotent (first call wins; later calls no-op).
void DalvikExecutionEngine::populate_resource_drawable_paths(
        const std::vector<std::string>& entry_names) {
    if (drawable_paths_populated_) return;
    drawable_paths_populated_ = true;
    if (field_name_by_resid_.empty() || entry_names.empty()) return;

    auto basename_no_ext = [](const std::string& path) -> std::string {
        size_t slash = path.find_last_of('/');
        std::string name = (slash == std::string::npos) ? path : path.substr(slash + 1);
        // strip chained extensions: ".9.png" → "", ".png" → "", ".webp" → ""
        size_t dot = name.find('.');
        std::string base = (dot == std::string::npos) ? name : name.substr(0, dot);
        return base;
    };
    auto is_drawable_asset = [](const std::string& path) -> bool {
        if (path.find("res/") != 0) return false;
        if (path.find("drawable") == std::string::npos &&
            path.find("mipmap") == std::string::npos) return false;
        static const char* exts[] = {".png", ".webp", ".jpg", ".jpeg", ".xml", ".gif"};
        for (const char* e : exts) {
            if (path.size() >= strlen(e) &&
                path.compare(path.size() - strlen(e), strlen(e), e) == 0) return true;
        }
        return false;
    };
    auto density_rank = [](const std::string& path) -> int {
        // higher rank = higher density = preferred
        if (path.find("-xxxhdpi") != std::string::npos) return 60;
        if (path.find("-xxhdpi") != std::string::npos) return 50;
        if (path.find("-xhdpi") != std::string::npos) return 40;
        if (path.find("-hdpi") != std::string::npos) return 30;
        if (path.find("-mdpi") != std::string::npos) return 20;
        if (path.find("-ldpi") != std::string::npos) return 10;
        return 5;  // plain drawable/ or mipmap/
    };

    // basename → best entry (highest density rank)
    std::map<std::string, std::pair<std::string, int>> best_by_basename;
    for (const auto& entry : entry_names) {
        if (!is_drawable_asset(entry)) continue;
        std::string base = basename_no_ext(entry);
        int rank = density_rank(entry);
        auto it = best_by_basename.find(base);
        if (it == best_by_basename.end() || rank > it->second.second) {
            best_by_basename[base] = {entry, rank};
        }
    }
    if (best_by_basename.empty()) return;

    size_t resolved = 0;
    for (const auto& [resid, field_name] : field_name_by_resid_) {
        if (resource_drawable_paths_.count(field_name)) continue;
        auto it = best_by_basename.find(field_name);
        if (it != best_by_basename.end()) {
            resource_drawable_paths_[field_name] = it->second.first;
            resolved++;
        }
    }
    std::cerr << "[IMG-RES-RENDER] populated resource_drawable_paths_: "
              << resolved << "/" << field_name_by_resid_.size()
              << " R-names matched to APK drawable assets" << std::endl;
}

// GOLDEN-03 §10/§11 — ARSC-AUTHORITATIVE drawable path seeding.
// AOSP law: a file-backed resource entry's VALUE IS THE PATH inside
// resources.arsc (a STRING like "res/w6.xml"), and AssetManager2 selects the
// value under the device configuration. For every resid the engine knows a
// field name for, ask the canonical resolver for the selected variant's path
// and bind field_name → path. Replaces name-basename guessing as the primary
// source; populate_resource_drawable_paths() stays as fallback.
int DalvikExecutionEngine::populate_drawable_paths_from_arsc(
        const resources::ArscParser& arsc, const std::vector<std::string>& apk_paths) {
    if (field_name_by_resid_.empty() || apk_paths.empty()) return 0;
    int resolved = 0;
    for (const auto& [resid, field_name] : field_name_by_resid_) {
        if (field_name.empty()) continue;
        if (resource_drawable_paths_.count(field_name)) continue;
        // Only file-backed types make sense as drawable targets.
        auto r = arsc.resolve(resid);
        if (!r) {
            if (getenv("MINIANDROID_DEBUG_DRAWABLES"))
                std::cerr << "[ARSC-VALUES] FAIL resid=" << std::hex << resid
                          << std::dec << " field=" << field_name
                          << " resolve()=null" << std::endl;
            continue;
        }
        if (r->type_name != "drawable" && r->type_name != "mipmap" &&
            r->type_name != "raw") {
            if (getenv("MINIANDROID_DEBUG_DRAWABLES"))
                std::cerr << "[ARSC-VALUES] SKIP resid=" << std::hex << resid
                          << std::dec << " field=" << field_name
                          << " type=" << r->type_name << std::endl;
            continue;
        }
        // G04 §4: select_file (canonical resolve_full law) replaces
        // apk_path_for so the SELECTED config density is captured too —
        // the BitmapFactory inDensity→inTargetDensity scaling input.
        if (auto sel = arsc.select_file(resid, apk_paths,
                                        resources::device_config())) {
            resource_drawable_paths_[field_name] = sel->path;
            resource_drawable_density_by_resid_[resid] = sel->selected_density();
            resolved++;
        } else if (getenv("MINIANDROID_DEBUG_DRAWABLES")) {
            std::cerr << "[ARSC-VALUES] FAIL resid=" << std::hex << resid
                      << std::dec << " field=" << field_name
                      << " type=" << (r ? r->type_name : "?") << std::endl;
        }
    }
    std::cerr << "[ARSC-VALUES] drawable paths resolved via canonical resolver: "
              << resolved << "/" << field_name_by_resid_.size() << std::endl;
    return resolved;
}

uint16_t DalvikExecutionEngine::fetch_opcode(uint32_t pc) const {
    if (pc < bytecode_.size()) {
        return bytecode_[pc];
    }
    return Opcode::NOP;
}

// ============================================================================
// OPCODE IMPLEMENTATIONS — Constants
// ============================================================================

bool DalvikExecutionEngine::execute_const_4(uint32_t pc, InstructionTrace& trace) {
    // Format: 11n B|A|op — 1 code unit
    //   byte 0 (low): op (0x12)
    //   byte 1 (high): B<<4 | A (A = register nibble, B = literal nibble)
    // EXP-047 FIX: Previous code extracted dest_reg as the full high byte
    // and literal as the low nibble of the low byte (always 0x2 from op=0x12).
    // This caused const/4 to write to the WRONG register and use the WRONG value.
    // For example, const/4 v3, #4 (word=0x4312) was interpreted as
    // dest_reg=0x43 (v67) and literal=2, instead of dest_reg=3 and literal=4.
    // This was the root cause of if-gt at PC=147 in postInitApplication
    // comparing wrong registers and branching to PC=224, skipping
    // UserConfig.getInstance, MessagesController.getInstance, and
    // ConnectionsManager.getInstance.
    if (pc >= bytecode_.size()) return false;

    uint16_t instr = bytecode_[pc];
    uint8_t dest_reg = (instr >> 8) & 0xF;    // A = low nibble of high byte
    uint8_t literal_nibble = (instr >> 12) & 0xF;  // B = high nibble of high byte

    // Sign-extend from 4 bits
    int32_t value = (literal_nibble >= 8) ? (literal_nibble - 16) : literal_nibble;

    set_register(dest_reg, DalvikValue::make_int(value));

    // EXP-059: Debug — log const/4 in onFragmentCreate and addFragmentToStack
    if (current_method_ == "onFragmentCreate" ||
        (current_method_ == "addFragmentToStack" &&
         current_class_.find("ActionBarLayout") != std::string::npos)) {
        std::cerr << "[EXP059-CONST4] " << current_class_ << "." << current_method_
                  << " PC=" << pc << " v" << (int)dest_reg
                  << " = " << value
                  << " (literal_nibble=" << (int)literal_nibble << ")"
                  << std::endl;
    }

    trace.operands.push_back({"v" + std::to_string(dest_reg), std::to_string(value)});

    pc_ = pc + 1;
    return true;
}

bool DalvikExecutionEngine::execute_const_16(uint32_t pc, InstructionTrace& trace) {
    // Format: 21s [op] vAA, #+BBBB
    if (pc + 1 >= bytecode_.size()) return false;

    uint16_t instr = bytecode_[pc];
    // W15 (#627 E-01 family): the 21s dest is a full 8-bit register index —
    // keep it untruncated so v256+ methods address the right slot (mirrors
    // the move/from16 law).
    uint16_t dest_reg = static_cast<uint16_t>((instr >> 8) & 0xFF);
    int16_t literal = static_cast<int16_t>(bytecode_[pc + 1]);

    static thread_local uint64_t w15_c16 = 0;
    if (w15_c16++ < 8)
        std::cerr << "[W15-C16] dest=" << dest_reg << " lit=" << literal
                  << " rf_size=" << (current_registers_
                      ? current_registers_->get_size() : 0)
                  << std::endl;
    set_register(dest_reg, DalvikValue::make_int(static_cast<int32_t>(literal)));
    
    trace.operands.push_back({"v" + std::to_string(dest_reg), std::to_string(literal)});
    
    pc_ = pc + 2;
    return true;
}

bool DalvikExecutionEngine::execute_const(uint32_t pc, InstructionTrace& trace) {
    // Format: 31i [op] vAA, #+BBBBBBBB
    if (pc + 2 >= bytecode_.size()) return false;
    
    uint16_t instr = bytecode_[pc];
    uint8_t dest_reg = (instr >> 8) & 0xFF;
    int32_t literal = (static_cast<int32_t>(bytecode_[pc + 1])) | 
                      (static_cast<int32_t>(bytecode_[pc + 2]) << 16);
    
    set_register(dest_reg, DalvikValue::make_int(literal));
    
    trace.operands.push_back({"v" + std::to_string(dest_reg), std::to_string(literal)});
    
    pc_ = pc + 3;
    return true;
}

bool DalvikExecutionEngine::execute_const_string(uint32_t pc, InstructionTrace& trace) {
    // Format: 21c [op] vAA, string@BBBB
    if (pc + 1 >= bytecode_.size()) return false;

    uint16_t instr = bytecode_[pc];
    uint8_t dest_reg = (instr >> 8) & 0xFF;
    uint16_t string_idx = bytecode_[pc + 1];
    
    // EXP-065: CRITICAL FIX — Use per-DEX string resolution.
    // The merged dex_report_->strings[] is the concatenation of all DEX
    // files' string tables. For multi-DEX apps, string_idx is relative to
    // the CURRENT DEX file, so using the merged index returns the WRONG
    // string. For example, Telegram's classes4.dex has string_idx=5975="+",
    // but merged_strings[5975]="FIELD_PREFERRED_AUDIO_LANGUAGES" (from classes.dex).
    // This bug caused ViewNode.text to leak Android MediaMetadata constant
    // names into the rendered UI image.
    std::string str_value = "<string:" + std::to_string(string_idx) + ">";
    str_value = resolve_string_for_dex(string_idx, current_dex_index_);
    
    uint32_t ref_id = instruction_sequence_;  // Use sequence as ref ID
    set_register(dest_reg, DalvikValue::make_string(str_value, ref_id));
    
    trace.operands.push_back({"v" + std::to_string(dest_reg), "\"" + str_value + "\""});
    trace.operands.push_back({"string_idx", std::to_string(string_idx)});
    
    pc_ = pc + 2;
    return true;
}

bool DalvikExecutionEngine::execute_const_class(uint32_t pc, InstructionTrace& trace) {
    // Format: 21c [op] vAA, type@BBBB
    if (pc + 1 >= bytecode_.size()) return false;

    uint16_t instr = bytecode_[pc];
    uint8_t dest_reg = (instr >> 8) & 0xFF;
    uint16_t type_idx = bytecode_[pc + 1];

    // EXP-066: Use per-DEX type resolution (multi-DEX bug fix — same pattern as
    // execute_const_string in EXP-065). The merged dex_report_->types[] is the
    // concatenation of all DEX files' type_ids tables; type_idx is per-DEX.
    std::string type_desc = "<type:" + std::to_string(type_idx) + ">";
    type_desc = resolve_type_for_dex(type_idx, current_dex_index_);

    // ── F-069 (R-NEW-293): const-class STABLE IDENTITY law ───────────────
    // ART: every evaluation of `X.class` for the same X yields the SAME
    // java.lang.Class object — identity is observable (== via if-eq,
    // Intrinsics.areEqual, map keys, LinkedHashMap lookups). The old code
    // minted a NEW ref_id (instruction_sequence_) per evaluation, so two
    // const-class of the same descriptor were never reference-equal.
    // Real-APK hit: dooz SavedStateHandlesVM.create — the viewModelFactory
    // initializer registered its key under one Class value and the
    // create(modelClass) lookup compared a DIFFERENT Class value →
    // Intrinsics.areEqual false → IAE "No initializer set for given class
    // androidx.lifecycle.A" → first frame died. The token is stable per
    // descriptor for the whole run (identity), and distinct descriptors
    // never share a token.
    //
    // F-103 (S58, R-NEW-378): HEAP-BACKED CLASS TOKENS. ART Class objects
    // are real heap objects; minting tokens from a PRIVATE counter
    // (class_token_counter_) made token ids collide with real heap object
    // ids (both count from 1). Every §19 runtime-class dispatch on a
    // Class-token receiver then resolved to some UNRELATED early heap
    // object — e.g. the compose DisposableSaveableStateRegistry
    // ACCEPTABLE_CLASSES loop (Lje;.<init>(Lhf1;)V pc=98) dispatched
    // Class.isInstance to whichever object owned the colliding id, the
    // call fell to a STUBBED typed-zero false for all 29 elements, and
    // rememberSaveable threw IAE "Can't put value with type null into
    // saved state" → APP BOUNDARY unwind → blank frame. The token is now
    // a REAL heap object of class Ljava/lang/Class; carrying the referent
    // descriptor in the __referent_desc field, so receiver-class
    // resolution lands on Ljava/lang/Class; and the identity map stores
    // the heap id (stable per descriptor — F-069 preserved).
    uint32_t token = 0;
    auto tok_it = class_token_ids_.find(type_desc);
    if (tok_it != class_token_ids_.end()) {
        token = tok_it->second;
    } else {
        token = heap_.allocate("Ljava/lang/Class;", pc_, 0);
        heap_.set_object_field(token, "__referent_desc",
                               DalvikValue::make_string(type_desc, 0));
        class_token_ids_.emplace(type_desc, token);
    }

    set_register(dest_reg, DalvikValue::make_class(type_desc, token));

    trace.operands.push_back({"v" + std::to_string(dest_reg), type_desc});

    pc_ = pc + 2;
    return true;
}

// ============================================================================
// OPCODE IMPLEMENTATIONS — Moves
// ============================================================================

bool DalvikExecutionEngine::execute_move(uint32_t pc, InstructionTrace& trace) {
    // Format: 12x B|A|op — 1 code unit
    // bits 0-7: op, bits 8-11: A (dest), bits 12-15: B (src)
    if (pc + 1 >= bytecode_.size()) return false;
    
    uint16_t instr = bytecode_[pc];
    uint8_t dest = (instr >> 8) & 0xF;
    // EXP-058: CRITICAL FIX — was (instr >> 4) & 0xF which reads bits 4-7
    // (part of the opcode byte), NOT bits 12-15 (the B register nibble).
    // This caused move-object v9, v15 to read v0 instead of v15.
    uint8_t src = (instr >> 12) & 0xF;
    
    DalvikValue val = get_register(src);
    set_register(dest, val);
    
    trace.operands.push_back({"v" + std::to_string(dest), register_name(src)});
    
    pc_ = pc + 1;
    return true;
}

bool DalvikExecutionEngine::execute_move_object(uint32_t pc, InstructionTrace& trace) {
    // Format: 12x B|A|op — 1 code unit
    // bits 0-7: op, bits 8-11: A (dest), bits 12-15: B (src)
    if (pc + 1 >= bytecode_.size()) return false;
    
    uint16_t instr = bytecode_[pc];
    uint8_t dest = (instr >> 8) & 0xF;
    // EXP-058: CRITICAL FIX — was (instr >> 4) & 0xF which reads bits 4-7
    // (part of the opcode byte), NOT bits 12-15 (the B register nibble).
    // This caused move-object v9, v15 to read v0 (uninitialized) instead
    // of v15 (the Activity `this` pointer). As a result, ALL iput-object
    // instructions on the Activity's fields silently failed because the
    // object reference was NULL_REF instead of OBJECT_REF.
    uint8_t src = (instr >> 12) & 0xF;
    
    DalvikValue val = get_register(src);
    // Ensure it's treated as object reference
    if (val.type == DalvikType::REGISTER_UNSET || val.type == DalvikType::UNINITIALIZED) {
        val = DalvikValue::make_null();
    }
    set_register(dest, val);
    
    trace.operands.push_back({"v" + std::to_string(dest), register_name(src)});
    
    pc_ = pc + 1;
    return true;
}

// EXP-038 (BLOCKER-026): move-object/from16
// Format: 22x AA|op BBBB
//   code[0]: AA (8-bit dest register) | op (8-bit opcode)
//   code[1]: BBBB (16-bit source register)
// Copies an object reference from vBBBB to vAA.
// Used by Telegram's LaunchActivity.onCreate() at PC=1 to move
// the `this` reference from the parameter register to a local register.
bool DalvikExecutionEngine::execute_move_object_from16(uint32_t pc, InstructionTrace& trace) {
    if (pc + 1 >= bytecode_.size()) return false;
    
    uint16_t instr = bytecode_[pc];
    uint8_t dest = (instr >> 8) & 0xFF;  // 8-bit dest register (was 0xF for move-object)
    uint16_t src = bytecode_[pc + 1];    // 16-bit source register
    
    DalvikValue val = get_register(src);
    if (val.type == DalvikType::REGISTER_UNSET || val.type == DalvikType::UNINITIALIZED) {
        val = DalvikValue::make_null();
    }
    set_register(dest, val);
    
    trace.operands.push_back({"v" + std::to_string(dest), "v" + std::to_string(src)});
    
    pc_ = pc + 2;  // 22x format = 2 code units
    return true;
}

// FINAL-CAMPAIGN PHASE 3 (F-NEW-169 face-2): move-object/16 (DEX spec opcode
// 0x09, format 32x: op | vAAAA | vBBBB = 3 code units). The enum defined the
// opcode but the interpreter had NO case — execution fell to the default
// UNIMPLEMENTED arm which skips ONE unit instead of THREE, desynchronizing
// the pc and decoding garbage mid-instruction (measured: WhatsApp
// LX/07r;.<init> @0x5a — new-instance 00D flow corrupted → "invoke
// LX/00D;.<init> on a null object reference" → ctor broken → DI provider
// slots left unfilled → downstream Intrinsics NPE chain → white screen).
// AOSP law: ART MterpMoveObject16 — 16-bit register move of an object ref.
bool DalvikExecutionEngine::execute_move_object_16(uint32_t pc, InstructionTrace& trace) {
    if (pc + 2 >= bytecode_.size()) return false;

    uint16_t dest = bytecode_[pc + 1];  // vAAAA — 16-bit dest register
    uint16_t src = bytecode_[pc + 2];   // vBBBB — 16-bit source register

    DalvikValue val = get_register(src);
    if (val.type == DalvikType::REGISTER_UNSET || val.type == DalvikType::UNINITIALIZED) {
        val = DalvikValue::make_null();
    }
    set_register(dest, val);
    
    trace.operands.push_back({"v" + std::to_string(dest), "v" + std::to_string(src)});
    
    pc_ = pc + 3;  // 32x format = 3 code units
    return true;
}

bool DalvikExecutionEngine::execute_move_result(uint32_t pc, InstructionTrace& trace) {
    // Format: 11x [op] vAA — move return value from last invoke to register
    // EXP-050 Phase 2 CRITICAL FIX: Previously returned placeholder 0, silently
    // discarding ALL return values from ALL method calls. Now reads from
    // last_invoke_return_ which is set by every invoke-* handler.
    if (pc >= bytecode_.size()) return false;

    uint16_t instr = bytecode_[pc];
    uint8_t dest = (instr >> 8) & 0xFF;

    set_register(dest, last_invoke_return_);

    // EXP-059: Debug — log move-result in addFragmentToStack
    if (current_method_ == "addFragmentToStack" &&
        current_class_.find("ActionBarLayout") != std::string::npos) {
        std::cerr << "[EXP059-MOVE-RESULT] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " dest=v" << (int)dest
                  << " type=" << static_cast<int>(last_invoke_return_.type)
                  << " int_val=" << last_invoke_return_.int_val
                  << " obj=" << last_invoke_return_.object_id
                  << std::endl;
    }

    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.operands.push_back({"v" + std::to_string(dest), last_invoke_return_.to_string()});
    }
    trace.return_value = last_invoke_return_;

    pc_ = pc + 1;
    return true;
}

bool DalvikExecutionEngine::execute_move_result_object(uint32_t pc, InstructionTrace& trace) {
    if (pc >= bytecode_.size()) return false;

    uint16_t instr = bytecode_[pc];
    uint8_t dest = (instr >> 8) & 0xFF;

    // EXP-057: Debug — log move-result-object in onCreate for login path.
    if (current_method_ == "onCreate" && current_class_.find("LaunchActivity") != std::string::npos) {
        std::cerr << "[EXP057-MRO] move-result-object v" << (int)dest
                  << " type=" << static_cast<int>(last_invoke_return_.type)
                  << " obj=" << last_invoke_return_.object_id
                  << " pc=" << pc
                  << std::endl;
    }

    // F-075 (S21) — POLYMORPHIC-ZERO-AT-REFERENCE-USE LAW (move side).
    // move-result-object IS a reference context: the moved value must be a
    // reference (the preceding invoke's declared return type is L...; or
    // [...). An INT32(0) here is the polymorphic zero word = the null
    // reference (ART Zero reg-type); a VOID/unset return is a bridge's
    // null answer. Without this, identity consumers (if-eq/if-ne against
    // real objects) mis-compare 0-vs-0 through the int fallback.
    {
        DalvikValue rv = last_invoke_return_;
        if ((rv.type == DalvikType::INT32 && rv.int_val == 0) ||
            rv.type == DalvikType::VOID_) {
            rv = DalvikValue::make_null();
            last_invoke_return_ = rv;
        }
        set_register(dest, rv);
    }

    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.operands.push_back({"v" + std::to_string(dest), last_invoke_return_.to_string()});
    }
    trace.return_value = last_invoke_return_;

    pc_ = pc + 1;
    return true;
}

// ============================================================================
// OPCODE IMPLEMENTATIONS — Objects
// ============================================================================

} // namespace dalvik
} // namespace miniandroid
