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
                val.int_val = static_cast<int32_t>(bbbb) << 16;
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
                    if ((op == "div" || op == "rem") && lit == 0) { \
                        throw_deferred("Ljava/lang/ArithmeticException;", "divide by zero", "ARITH-LIT8"); \
                        pc_ = pc_ + 2; \
                        break; \
                    } \
                    if (op == "add") result_val.int_val = b_val + lit; \
                    else if (op == "rsub") result_val.int_val = lit - b_val; \
                    else if (op == "sub") result_val.int_val = b_val - lit; \
                    else if (op == "mul") result_val.int_val = b_val * lit; \
                    else if (op == "div") result_val.int_val = b_val / lit; \
                    else if (op == "rem") result_val.int_val = b_val % lit; \
                    else if (op == "and") result_val.int_val = b_val & lit; \
                    else if (op == "or")  result_val.int_val = b_val | lit; \
                    else if (op == "xor") result_val.int_val = b_val ^ lit; \
                    else if (op == "shl") result_val.int_val = b_val << (lit & 0x1f); \
                    else if (op == "shr") result_val.int_val = b_val >> (lit & 0x1f); \
                    else if (op == "ushr") result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(b_val) >> (lit & 0x1f)); \
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
                    if ((op == "div" || op == "rem") && lit == 0) { \
                        throw_deferred("Ljava/lang/ArithmeticException;", "divide by zero", "ARITH-LIT16"); \
                        pc_ = pc_ + 2; \
                        break; \
                    } \
                    if (op == "add") result_val.int_val = b_val + lit; \
                    else if (op == "rsub") result_val.int_val = lit - b_val; \
                    else if (op == "sub") result_val.int_val = b_val - lit; \
                    else if (op == "mul") result_val.int_val = b_val * lit; \
                    else if (op == "div") result_val.int_val = b_val / lit; \
                    else if (op == "rem") result_val.int_val = b_val % lit; \
                    else if (op == "and") result_val.int_val = b_val & lit; \
                    else if (op == "or")  result_val.int_val = b_val | lit; \
                    else if (op == "xor") result_val.int_val = b_val ^ lit; \
                    else if (op == "shl") result_val.int_val = b_val << (lit & 0x1f); \
                    else if (op == "shr") result_val.int_val = b_val >> (lit & 0x1f); \
                    else if (op == "ushr") result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(b_val) >> (lit & 0x1f)); \
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
                DalvikValue val = get_register(static_cast<uint8_t>(src));
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
                uint32_t string_idx = (bytecode_[pc_ + 2] << 16) | bytecode_[pc_ + 1];
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
                    else if (op == "rem") result_val.float_val = fmodf(bf, cf); \
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
                DalvikValue val = get_register(static_cast<uint8_t>(src));
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
                uint8_t vAA = (bytecode_[pc_] >> 8) & 0xFF;
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
                DalvikValue dv; dv.type = DalvikType::INT64; dv.long_val = static_cast<int64_t>(val) << 48;
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
    uint8_t dest_reg = (instr >> 8) & 0xFF;
    int16_t literal = static_cast<int16_t>(bytecode_[pc + 1]);
    
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

bool DalvikExecutionEngine::execute_new_instance(uint32_t pc, InstructionTrace& trace) {
    // Format: 22c [op] vAA, type@BBBB
    if (pc + 1 >= bytecode_.size()) return false;
    
    uint16_t instr = bytecode_[pc];
    uint8_t dest_reg = (instr >> 8) & 0xFF;
    uint16_t type_idx = bytecode_[pc + 1];
    
    // EXP-058: Use per-DEX type resolution instead of merged global types.
    // type_idx is relative to the current DEX file's type_ids table.
    std::string class_desc = resolve_type_for_dex(type_idx, current_dex_index_);
    if (class_desc == "<unknown>" && dex_report_ && type_idx < dex_report_->types.size()) {
        class_desc = dex_report_->types[type_idx];
    }
    
    // Allocate on heap
    uint32_t frame_id = call_stack_.empty() ? 0 : call_stack_.top().frame_id;
    uint32_t obj_id = heap_.allocate(class_desc, pc, frame_id);

    // ── S222-A F-023b (AOSP Configuration.setToDefaults + the F-149
    // device-density law): framework objects materialized via new-instance
    // start ZERO-FILLED on the heap. ART runs the framework class's own
    // field initializers (Configuration.<init> → setToDefaults:
    // fontScale=1.0, densityDpi from the device, locale non-null;
    // DisplayMetrics: density/densityDpi/scaledDensity/widthPixels/
    // heightPixels). Live face (dooz s222_baseline): the Compose
    // LocalDensity chain answered InlineDensity(density=2.625, fontScale=
    // 0.000000) — the Density wrapper read OUR heap Configuration whose
    // fontScale was still the raw 0.0 because that Configuration instance
    // was new-instance-materialized, never routed through the
    // get_or_create_singleton pre-populate (F-023 v1). The ONE device
    // identity law: every materialization path answers the same values.
    if (class_desc == "Landroid/content/res/Configuration;") {
        DalvikValue s222_fs;
        s222_fs.type = DalvikType::FLOAT32;
        s222_fs.float_val = 1.0f;  // AOSP Configuration.setToDefaults()
        heap_.set_object_field(obj_id, "fontScale", s222_fs);
        DalvikValue s222_dd;
        s222_dd.type = DalvikType::INT32;
        s222_dd.int_val = 420;  // the ONE device density (F-149/C9-22)
        heap_.set_object_field(obj_id, "densityDpi", s222_dd);
        DalvikValue s222_or;
        s222_or.type = DalvikType::INT32;
        s222_or.int_val = 1;  // ORIENTATION_PORTRAIT
        heap_.set_object_field(obj_id, "orientation", s222_or);
        DalvikValue s222_sl;
        s222_sl.type = DalvikType::INT32;
        s222_sl.int_val = 0x40;  // SCREENLAYOUT_SIZE_NORMAL
        heap_.set_object_field(obj_id, "screenLayout", s222_sl);
    } else if (class_desc == "Landroid/util/DisplayMetrics;") {
        DalvikValue s222_dm;
        s222_dm.type = DalvikType::FLOAT32;
        s222_dm.float_val = 2.625f;  // THE device-density law (F-149)
        heap_.set_object_field(obj_id, "density", s222_dm);
        DalvikValue s222_sd;
        s222_sd.type = DalvikType::FLOAT32;
        s222_sd.float_val = 2.625f;  // scaledDensity = density × fontScale 1.0
        heap_.set_object_field(obj_id, "scaledDensity", s222_sd);
        DalvikValue s222_ddm;
        s222_ddm.type = DalvikType::INT32;
        s222_ddm.int_val = 420;
        heap_.set_object_field(obj_id, "densityDpi", s222_ddm);
        DalvikValue s222_wp;
        s222_wp.type = DalvikType::INT32;
        s222_wp.int_val = 1080;
        heap_.set_object_field(obj_id, "widthPixels", s222_wp);
        DalvikValue s222_hp;
        s222_hp.type = DalvikType::INT32;
        s222_hp.int_val = 1920;
        heap_.set_object_field(obj_id, "heightPixels", s222_hp);
    }

    // CONT-38 (F-C4-545 evidence, DIAG-ONLY, env-gated): MINIANDROID_NEW_WATCH
    // = class-desc substring. Prints every new-instance of a watched class
    // with the allocating caller — answers "was the draw-block lambda EVER
    // constructed" without a fragile static scanner (the dooz board block
    // Lz6; never constructed = composition never reached the Canvas block).
    static thread_local const char* nw_env =
        std::getenv("MINIANDROID_NEW_WATCH");
    if (nw_env && nw_env[0] && !class_desc.empty() &&
        std::string(class_desc).find(nw_env) != std::string::npos) {
        static thread_local uint32_t nw_n = 0;
        if (nw_n++ < 200)
            std::cerr << "[NEW-WATCH] " << class_desc << " obj#" << obj_id
                      << " caller=" << current_class_ << "." << current_method_
                      << " pc=" << pc << std::endl;
    }
    // ── S222-A (DIAG-ONLY, env-gated MINIANDROID_S222_CACHE): the dooz
    // text-cache layout-result materialization probe. Ltw1; = the
    // TextLayoutResult holder (fields a=Lsw1; b=Lwu0; c:J=packed density;
    // the ONLY DEX constructor caller is Lex1;.q — the paragraph-layout
    // completion). If Ltw1; NEVER materializes, the MultiParagraphLayoutCache
    // textLayoutResult stays null and EVERY draw throws the upstream ISE
    // ("could not provide TextLayoutResult during the draw phase") — the
    // storm the S221 bridge could not close. This answers whether the
    // layout completion chain is EVER reached.
    if (class_desc == "Ltw1;") {
        static thread_local const bool s222_tw_on =
            diag_env("MINIANDROID_S222_CACHE");
        static thread_local uint32_t s222_tw_n = 0;
        if (s222_tw_on && s222_tw_n < 64)
            std::cerr << "[S222-TW1] Ltw1; obj#" << obj_id
                      << " caller=" << current_class_ << "." << current_method_
                      << " pc=" << pc << std::endl;
        ++s222_tw_n;
    }


    // DEMO-CLINIT (2026-09-04): per AOSP jvm.cc ClassLinker semantics,
    // new-instance is an ACTIVE USE of the class and must trigger
    // initialization (its <clinit>) before the instance is created.
    // Previously only sget/sput triggered initialization, so classes that
    // were first touched via new-instance ran with uninitialized statics.
    ensure_class_initialized(class_desc);
    // F-NEW-215: new-instance on an ERRONEOUS class raises
    // NoClassDefFoundError (JVMS 5.5 new-instance is active use).
    if (class_clinit_failed(class_desc) &&
        !clinit_exc_already_in_flight()) {  // F-NEW-395: no double-raise at the triggering use
        static std::atomic<uint64_t> f215_new_n{0};
        if (f215_new_n.fetch_add(1, std::memory_order_relaxed) < 8) {
            std::cerr << "[F-NEW-215] ACTIVE-USE new-instance class="
                      << class_desc << " caller=" << current_class_ << "."
                      << current_method_ << std::endl;
        }
        throw_deferred("Ljava/lang/NoClassDefFoundError;",
                       class_desc + " <clinit> failed previously (erroneous class)",
                       "F-NEW-215");
        pc_ = pc + 2;
        return false;
    }

    // Store object reference in register
    set_register(dest_reg, DalvikValue::make_object(obj_id, class_desc));
    
    // EXP-061: Debug — trace new-instance for View/EditText/Button classes
    // to investigate why some views end up with object_id=0 in shadow dispatch.
    // EXP-089: Also trace LoginActivity creation (for Phase M1 verification).
    if (class_desc.find("EditText") != std::string::npos ||
        class_desc.find("TextView") != std::string::npos ||
        class_desc.find("Button") != std::string::npos ||
        class_desc.find("PhoneView") != std::string::npos ||
        class_desc.find("Keyboard") != std::string::npos ||
        class_desc.find("LoginActivity") != std::string::npos) {
        std::cerr << "[EXP061-NEW] new-instance " << class_desc
                  << " → v" << (int)dest_reg
                  << " obj_id=" << obj_id
                  << " pc=" << pc
                  << " caller=" << current_class_ << "." << current_method_
                  << std::endl;
    }
    
    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.operands.push_back({"v" + std::to_string(dest_reg), class_desc});
    }
    trace.allocated_object_id = obj_id;
    
    // S157-B (CONT-42): the log() argument was built BEFORE the verbose
    // gate — concat + to_string heap churn per new-instance even when
    // verbose_ is false. Identical output when verbose, zero cost when not.
    if (verbose_) log("  ALLOCATED: " + class_desc + " -> obj#" + std::to_string(obj_id));
    
    pc_ = pc + 2;
    return true;
}

bool DalvikExecutionEngine::execute_check_cast(uint32_t pc, InstructionTrace& trace) {
    // Format: 1c [op] vAA, type@BBBB
    if (pc + 1 >= bytecode_.size()) return false;

    uint16_t instr = bytecode_[pc];
    uint8_t reg = (instr >> 8) & 0xFF;
    uint16_t type_idx = bytecode_[pc + 1];

    // EXP-066: Use per-DEX type resolution (multi-DEX bug fix).
    std::string target_type = "<unknown>";
    target_type = resolve_type_for_dex(type_idx, current_dex_index_);

    // In full implementation, would check if register value is instance of target_type
    // For now, pass through (optimistic cast)
    DalvikValue val = get_register(reg);
    // If null or uninit, it's always ok
    if (val.type == DalvikType::NULL_REF || val.type == DalvikType::UNINITIALIZED ||
        val.type == DalvikType::REGISTER_UNSET) {
        // Null passes any check-cast
    }

    // F-090 (R-NEW-316): check-cast runtime-identity refinement.
    // ART law (dalvik bytecodes §check-cast / AOSP CheckCast.cc): the cast
    // ASSERTS the object is an instance of the target and the register's
    // static type is refined to the target; the OBJECT is untouched. This
    // engine carries a per-register class_desc that downstream identity
    // surfaces (Object.getClass F-088, Class.getAnnotation F-087 receiver,
    // EXP-059 runtime-type dispatch) read as the value's class. Without
    // refinement, the Kotlin idiom `map[key] as Navigator` left the register
    // poisoned with the container's declared type (Ljava/lang/Object; from
    // Map.get) — dooz addNavigator → nameForNavigator(read @Navigator.Name
    // off java.lang.Object) → IAE → MainActivity.onCreate died → blank Compose
    // frame. Refinement rule: the HEAP's runtime class is the identity
    // authority (EXP-059); use it when known, else refine to the cast target
    // (the verifier's static type). Optimistic pass retained (no ClassCast-
    // Exception yet — framework-side interface closure is not fully parsed;
    // a hard CCE here would wrongly reject valid framework casts).
    if (val.type == DalvikType::OBJECT_REF && val.object_id != 0) {
        // F-105 (S59, R-NEW-379): reconcile the register's creation-site
        // declaration with the heap record instead of letting the heap
        // record overwrite it unconditionally. The F-090 heap-authority
        // refinement poisoned view references whose id collides with an
        // unrelated heap object (activity-as-view: getParent result
        // declared Landroid/view/View; refined to heap#20's
        // MainActivity → the follow-up shadow dispatch lost the View
        // routing and the ViewTreeLifecycleOwner walk dead-ended).
        std::string runtime_desc =
            reconcile_class_decl(val.class_desc, val.object_id);
        std::string refined =
            !runtime_desc.empty() ? runtime_desc : target_type;
        if (!refined.empty() && refined != "<unknown>" &&
            refined != val.class_desc) {
            val.class_desc = refined;
            set_register(reg, val);
        }
    }

    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.operands.push_back({"v" + std::to_string(reg), target_type});
    }

    pc_ = pc + 2;
    return true;
}

bool DalvikExecutionEngine::execute_instance_of(uint32_t pc, InstructionTrace& trace) {
    // Format: 22c [op vA vB] type@CCCC  — 2 code units
    // Encoding: cu[0] = BBBBAAAA_op (low byte = op, high nibble = vB, low nibble of high byte = vA)
    //           cu[1] = CCCC (type_idx)
    // EXP-092+ CRITICAL FIX: Previous code read dest/src from the wrong bit positions.
    //   dest = (instr >> 8) & 0xFF  → 0xc0 (full high byte) — WRONG, should be & 0x0F
    //   src  = instr & 0xFF         → 0x20 (the opcode!)   — WRONG, should be >> 12
    // This caused instance-of to read the wrong register and write to the wrong
    // register, producing garbage results. fillNextCodeParams' instance-of check
    // for TL_auth_sentCodeTypeFirebaseSms was returning true for ALL types
    // (including TL_auth_sentCodeTypeSms), causing the wrong page transition.
    if (pc + 1 >= bytecode_.size()) return false;

    uint16_t instr = bytecode_[pc];
    uint8_t dest = (instr >> 8) & 0x0F;        // vA: low nibble of high byte
    uint8_t src = (instr >> 12) & 0x0F;        // vB: high nibble of high byte
    uint16_t type_idx = bytecode_[pc + 1];     // type@CCCC at pc+1 (not pc+2)

    // EXP-066: Use per-DEX type resolution (multi-DEX bug fix).
    std::string target_type = "<unknown>";
    target_type = resolve_type_for_dex(type_idx, current_dex_index_);

    // EXP-071: Use semantic superclass chain for instanceof check.
    // Previously this only did an EXACT class match (src_val.class_desc == target_type),
    // which failed for subclass checks like `obj instanceof Activity` when obj's
    // actual class is LaunchActivity (a subclass of Activity).
    // Now we use is_subclass_of() which walks the DEX superclass chain.
    DalvikValue src_val = get_register(src);
    bool is_instance = false;
    // F-105c (S59, R-NEW-379): INSTANCE-OF ON A CLASS TOKEN VALUE.
    // const-class (F-069/F-103) yields a CLASS_REF whose ref_id is the
    // heap-backed Ljava/lang/Class; token and whose class_desc is the
    // REFERENT descriptor (Lhb0; — the class the token represents, not
    // the token's own class). ART law: `X.class instanceof Y` classifies
    // the TOKEN — the token's runtime class IS java.lang.Class — so
    // `key instanceof Class` is TRUE for every class literal. Live face
    // (dooz v23): ViewModelProvider's ViewModelStore key guard
    // (Lwl0;.containsKey pc=0: instance-of key, Ljava/lang/Class; on the
    // KClass.java round-trip value stored via Ljj;->a) rejected the
    // CLASS_REF → IAE "Key must be a class" at depth 79 → APP BOUNDARY
    // unwind. Classify CLASS_REF values by the token's heap record.
    if (src_val.type == DalvikType::CLASS_REF) {
        // F-NEW-218 TOKEN-BACKING VALIDATION LAW (ART Object.getClass /
        // Class token identity): a Class token's runtime class IS
        // java.lang.Class — every CLASS_REF classifies as Ljava/lang/Class;
        // for the instanceof target, regardless of heap backing. The old
        // raw deref of ref_id adopted whatever heap record sat at that id
        // as the token's runtime class — but getClass answers tokens with
        // ref_id = instruction_sequence_ (an execution counter, NOT a heap
        // id) and the engine shares ONE integer id space (F-105's
        // premise), so the counter collides with live heap objects and the
        // token's classification became RANDOM (opencalculator vc53 face:
        // ArrayList.getClass() → `instanceof Class` FALSE → Gson
        // $Gson$Types.getRawType IAE "Expected a Class, ParameterizedType,
        // or GenericArrayType" at APP BOUNDARY → MainActivity.onCreate
        // aborted → empty frame). A heap record only backs a token when it
        // IS a Ljava/lang/Class; object — anything else at the shared id
        // belongs to a different entity (F-105 CONTRADICTION applied to
        // tokens). Detection is logged, bounded; classification stays
        // collision-proof.
        if (src_val.ref_id != 0 && heap_.has_object(src_val.ref_id)) {
            if (const auto* tok = heap_.get(src_val.ref_id);
                tok && !tok->class_descriptor.empty() &&
                tok->class_descriptor != "Ljava/lang/Class;") {
                static std::atomic<uint64_t> f218_n{0};
                if (f218_n.fetch_add(1, std::memory_order_relaxed) < 8) {
                    std::cerr << "[F-NEW-218] TOKEN-BACKING-COLLISION ref_id="
                              << src_val.ref_id << " heap_desc="
                              << tok->class_descriptor
                              << " token_referent=" << src_val.class_desc
                              << " caller=" << current_class_ << "."
                              << current_method_ << std::endl;
                }
            }
        }
        is_instance = is_subclass_of("Ljava/lang/Class;", target_type);
    }
    else if (src_val.type == DalvikType::OBJECT_REF &&
             src_val.object_id == 0 && !src_val.class_desc.empty()) {
        // F-NEW-197 DESC-ONLY REFERENCE law: a reference with no heap
        // object carries only its creation-site declaration — that
        // declaration is the only type information (F-103's authority
        // law degenerates to the declaration). Classify by class_desc.
        is_instance = is_subclass_of(src_val.class_desc, target_type);
    }
    else if (src_val.type == DalvikType::STRING_REF) {
        // F-NEW-258 (CONT-7 W3): STRING-VALUE RUNTIME-TYPE LAW. An
        // in-register string value IS a java.lang.String instance — ART
        // instance-of and Class.isInstance agree on every non-null
        // string (OpenJDK: String.class.isInstance(s) == true, s != null).
        // The reflection path (F-103 isInstance law) already classifies
        // STRING_REF probes as Ljava/lang/String;; the bytecode path
        // fell through EVERY branch and answered FALSE. is_subclass_of
        // then composes the framework closure so the full ART truth
        // holds: String is-a CharSequence / Serializable / Comparable.
        // Live face (directive §4 contract row B-07): a String retrieved
        // from Bundle.get() answered getClass().getName()="java.lang.String"
        // (getClass handles STRING_REF) while `raw instanceof String`
        // answered FALSE — the two type paths disagreed on the same value.
        is_instance = is_subclass_of("Ljava/lang/String;", target_type);
    }
    else if (src_val.type == DalvikType::OBJECT_REF && src_val.object_id != 0) {
        // F-103 (S58, R-NEW-378) ART RUNTIME-TYPE LAW: the class of the
        // object a reference points to is the AUTHORITY for instance-of.
        // The register's cached class_desc can be empty or a degraded
        // generic tag ("Ljava/lang/Object;" after a shadow round-trip) —
        // in those cases the heap record is the only type information.
        //
        // F-105 (S59, R-NEW-379) — DECLARATION↔HEAP RECONCILIATION LAW.
        // The heap record is the authority ONLY when it does not
        // contradict the reference's creation-site declaration. The
        // engine intentionally shares ONE integer id space between
        // shadow entities and heap objects (F-023 activity-as-view: the
        // activity object's id IS the activity's view node id), so a
        // heap record at a referenced id may belong to a DIFFERENT
        // entity than the one the reference means. Live face (dooz
        // v23): ViewShadow.getParent returned the activity-as-view node
        // id 20 declared "Landroid/view/View;" while heap#20 is the
        // MainActivity → the F-103 heap-authority classified the parent
        // reference as MainActivity → `parent as? View`
        // (instance-of, Landroid/view/View; in the Lxd1;.g walk) was
        // FALSE → the ViewTreeLifecycleOwner walk dead-ended at the
        // first hop → WindowRecomposer ISE "ViewTreeLifecycleOwner not
        // found from Lho;@1074" (R-NEW-379 APP BOUNDARY unwind).
        // reconcile_class_decl implements the rules: generic declaration
        // → heap wins; consistent pair → the more specific wins;
        // CONTRADICTION → the creation-site declaration wins (the heap
        // record at the shared integer belongs to a different entity).
        std::string obj_class =
            reconcile_class_decl(src_val.class_desc, src_val.object_id);
        if (!obj_class.empty()) {
            // Check if obj_class is a subclass of target_type (or equal)
            is_instance = is_subclass_of(obj_class, target_type);
        }
    }
    // Also check if null — null instanceof anything is false (already handled by OBJECT_REF check)
    // F-072 diag (env-gated): interface-closure forensics for collection
    // checks on the dooz composition path.
    // R-NEW-337: extend the gate — every instance-of inside Loj0; (JobSupport)
    // is logged WITH the dex_report_ interface lookup result for the object
    // class. The d0 pc=0 check (state is Incomplete) returning FALSE on an
    // Lh20;(Empty) object is the suspected root of the first-composition
    // ISE "already complete or completing".
    if (std::getenv("MINIANDROID_INSTANCEOF_TRACE") &&
        (current_class_ == "Loj0;" || current_class_ == "Lkp1;" ||
         target_type == "Ljava/util/Set;" ||
         target_type == "[Ljava/lang/Object;" ||
         // CONT-7 W3 F-NEW-253: the SaveableStateRegistry canBeSaved
         // platform walk checks Bundle-storability via instance-of on
         // these platform types — log the authoritative classification
         // for every check in that family (bounded by the 200 cap).
         target_type == "Landroid/os/Bundle;" ||
         target_type == "Landroid/os/Parcelable;" ||
         target_type == "Ljava/io/Serializable;" ||
         target_type == "Ljava/lang/String;" ||
         target_type == "Ljava/lang/Number;" ||
         target_type == "Ljava/lang/Boolean;" ||
         target_type == "Ljava/lang/Character;" ||
         target_type == "Ljava/util/List;" ||
         target_type == "Ljava/util/Map;" ||
         target_type == "Landroid/util/SparseArray;" ||
         target_type == "Landroid/os/IBinder;" ||
         // S59 R-NEW-379: view-tree owner walks (Lxd1;.g) check
         // `parent as? View` after a static-wrapper getParent — log the
         // authoritative classification for View targets too.
         target_type == "Landroid/view/View;" ||
         target_type == "Landroid/view/ViewParent;" ||
         // S59 R-NEW-379 follow-up: Lwl0;.containsKey "Key must be a
         // class" at depth 79 — the Class-key guard classification.
         target_type == "Ljava/lang/Class;" ||
         // CONT-38: the composition-local provider-map identity gate
         // (Lku0;.get instance-of Lky0; — ProvidableCompositionLocal)
         // — a FALSE here short-circuits every local read to its default
         // (the LocalContentColor black face) before the trie lookup.
         target_type == "Lky0;")) {
        static thread_local uint64_t iof_n = 0;
        if (iof_n < 200) {
            ++iof_n;
            std::string oc = (src_val.type == DalvikType::OBJECT_REF)
                                 ? std::string(src_val.class_desc) : std::string("-");
            std::string hc;
            if (src_val.type == DalvikType::OBJECT_REF &&
                src_val.object_id != 0 && heap_.has_object(src_val.object_id)) {
                hc = heap_.get(src_val.object_id)->class_descriptor;
            }
            // S59 R-NEW-379 diag: the printed class must be the EFFECTIVE
            // authority (heap wins when non-empty) — register tag alone
            // mislabels the check.
            std::string eff = oc;
            if (!hc.empty()) eff = hc;
            fprintf(stderr,
                    "[INSTANCEOF-DIAG] %s.%s pc=%u target=%s obj=obj#%u class=%s heap=%s is_instance=%s\n",
                    current_class_.c_str(), current_method_.c_str(), pc,
                    target_type.c_str(),
                    src_val.type == DalvikType::OBJECT_REF ? src_val.object_id : 0u,
                    oc.c_str(), hc.c_str(), is_instance ? "TRUE" : "FALSE");
            // R-NEW-337 forensics: does dex_report_ actually know this class
            // and its implements-set? Empty closure / missing class def here
            // is exactly how `Lh20; instanceof Lmf0;` degrades to false.
            if (!oc.empty() && dex_report_) {
                bool found337 = false;
                for (const auto& cd : dex_report_->classes) {
                    if (cd.name != oc) continue;
                    found337 = true;
                    std::string ifs337;
                    for (const auto& ifc : cd.interfaces) ifs337 += ifc + " ";
                    fprintf(stderr,
                            "[INSTANCEOF-DIAG]   dex_report class=%s FOUND "
                            "ninterfaces=%zu [%s]\n",
                            cd.name.c_str(), cd.interfaces.size(),
                            ifs337.c_str());
                    break;
                }
                if (!found337)
                    fprintf(stderr,
                            "[INSTANCEOF-DIAG]   dex_report class=%s "
                            "MISSING (%zu classes scanned)\n",
                            oc.c_str(), dex_report_->classes.size());
            }
        }

    }
    // CONT-10 W6 (F-NEW-259 forensics): env-gated bounded trace of the
    // AUTHORITATIVE instanceof result for OBJECT_REF checks — generic
    // (no class gating): answers "which check dropped this element"
    // without per-app knowledge. Cap 1024 lines.
    if (std::getenv("MINIANDROID_F259_TRACE")) {
        static thread_local uint64_t f259_ins = 0;
        bool f259_dex_target =
            target_type.size() > 1 && target_type[0] == 'L' &&
            target_type.rfind("Ljava/", 0) != 0 &&
            target_type.rfind("Landroid/", 0) != 0;
        if (f259_dex_target && f259_ins++ < 65536) {
            std::string f259_oc = src_val.type == DalvikType::OBJECT_REF
                                      ? std::string(src_val.class_desc)
                                      : std::string("-");
            std::cerr << "[F259-INS] " << current_class_ << "."
                      << current_method_ << " target=" << target_type
                      << " obj=o" << src_val.object_id << " " << f259_oc
                      << " -> " << (is_instance ? "TRUE" : "FALSE")
                      << std::endl;
        }
    }
    set_register(dest, DalvikValue::make_bool(is_instance));

    // EXP-092+ PHASE 1: Trace instance-of in fillNextCodeParams AND lambda$onNextPressed$22
    // to verify the type field is correctly read and the response type check returns correct results.
    if (current_class_.find("LoginActivity") != std::string::npos &&
        (current_method_ == "fillNextCodeParams" ||
         current_method_.find("lambda$onNextPressed") == 0 ||
         current_method_.find("lambda$") == 0)) {
        std::cerr << "[EXP092-INSTANCEOF] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " dest=v" << (int)dest
                  << " src=v" << (int)src
                  << " type_idx=" << type_idx
                  << " target_type=" << target_type
                  << " obj_class=" << (src_val.type == DalvikType::OBJECT_REF ? src_val.class_desc : "N/A")
                  << " obj_id=" << (src_val.type == DalvikType::OBJECT_REF ? src_val.object_id : 0)
                  << " is_instance=" << (is_instance ? "TRUE" : "FALSE")
                  << std::endl;
    }

    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.operands.push_back({"v" + std::to_string(dest), register_name(src)});
    trace.operands.push_back({"type", target_type});
    }

    pc_ = pc + 2;  // EXP-037 Phase B (BLOCKER-017 FIX): 22c format is 2 code units (was pc + 3)
    return true;
}

// ============================================================================
// EXP-035: OPCODE IMPLEMENTATIONS — Field Operations
// ============================================================================

DalvikExecutionEngine::FieldResolution DalvikExecutionEngine::resolve_field(uint16_t field_idx) {
    uint64_t f107_t0 = 0; phase_clock().enter(phase_clock().resolve_field_ph, f107_t0);
    struct F107Guard { PhaseClock::Phase& ph; uint64_t t0; ~F107Guard(){{ phase_clock().exit(ph, t0);}} } f107_guard{phase_clock().resolve_field_ph, f107_t0};
    // R-NEW-467 memo fast path: the resolved identity is run-invariant per
    // (dex, idx); the epoch guard re-derives on any hierarchy-table growth.
    if (field_memo_.size() == 65536) {
        const FieldMemo& m = field_memo_[field_idx];
        if (m.epoch == field_memo_epoch() && m.res.resolved)
            return m.res;
    }
    FieldResolution resolution;
    
    if (!dex_report_) {
        resolution.error_message = "No DexReport available (resolve_field)";
        return resolution;
    }

    // EXP-046: Per-DEX field resolution (same issue as BLOCKER-033 for methods).
    // The merged DexReport concatenates field_ids from all DEX files, so
    // field_idx from bytecode (which is per-DEX) points to the wrong field.
    if (is_multidex_ && current_dex_index_ < per_dex_raw_data_.size()) {
        const auto& raw = per_dex_raw_data_[current_dex_index_];
        if (raw.size() >= sizeof(dex::DexHeader)) {
            dex::DexHeader hdr;
            std::memcpy(&hdr, raw.data(), sizeof(dex::DexHeader));
            if (field_idx < hdr.field_ids_size) {
                size_t foff = hdr.field_ids_off + field_idx * 8;
                if (foff + 8 <= raw.size()) {
                    uint16_t class_idx, type_idx;
                    uint32_t name_idx;
                    std::memcpy(&class_idx, raw.data() + foff, 2);
                    std::memcpy(&type_idx, raw.data() + foff + 2, 2);
                    std::memcpy(&name_idx, raw.data() + foff + 4, 4);
                    if (class_idx < hdr.type_ids_size) {
                        uint32_t desc_str_idx;
                        std::memcpy(&desc_str_idx, raw.data() + hdr.type_ids_off + class_idx * 4, 4);
                        resolution.class_descriptor = read_dex_string_from_raw(raw, desc_str_idx, hdr);
                    }
                    resolution.field_name = read_dex_string_from_raw(raw, name_idx, hdr);
                    if (type_idx < hdr.type_ids_size) {
                        uint32_t type_str_idx;
                        std::memcpy(&type_str_idx, raw.data() + hdr.type_ids_off + type_idx * 4, 4);
                        resolution.field_type = read_dex_string_from_raw(raw, type_str_idx, hdr);
                    }
                    if (!resolution.class_descriptor.empty() &&
                        !resolution.field_name.empty() &&
                        resolution.class_descriptor[0] == 'L') {
                        resolution.resolved = true;
                        // R-NEW-467: bank the memo for this (dex, idx).
                        if (field_memo_.size() == 65536) {
                            FieldMemo& m = field_memo_[field_idx];
                            m.res = resolution;
                            m.s134_valid = false;
                            m.epoch = field_memo_epoch();
                        }
                        return resolution;
                    }
                }
            }
        }
    }

    // Fallback: use merged DexReport
    resolution.class_descriptor = dex_report_->get_field_class(field_idx);
    resolution.field_name = dex_report_->get_field_name(field_idx);
    resolution.field_type = dex_report_->get_field_type(field_idx);

    if (resolution.class_descriptor.rfind("<bad_", 0) == 0 ||
        resolution.field_name.rfind("<bad_", 0) == 0 ||
        resolution.field_type.rfind("<bad_", 0) == 0) {
        resolution.error_message =
            "Field index " + std::to_string(field_idx) +
            " out of range or references invalid string/type";
        log("❌ FIELD RESOLUTION FAILED: " + resolution.error_message);
        return resolution;
    }

    resolution.resolved = true;
    // R-NEW-467: bank the memo for this (dex, idx).
    if (field_memo_.size() == 65536) {
        FieldMemo& m = field_memo_[field_idx];
        m.res = resolution;
        m.s134_valid = false;
        m.epoch = field_memo_epoch();
    }
    // Look up field offset from runtime metadata cache if available
    auto class_it = class_info_cache_.find(resolution.class_descriptor);
    if (class_it != class_info_cache_.end() && class_it->second) {
        const auto& class_info = *(class_it->second);
        for (const auto& inst_field : class_info.instance_fields) {
            if (inst_field.name == resolution.field_name) {
                resolution.field_offset = inst_field.byte_offset;
                break;
            }
        }
        resolution.is_static = false;
    } else {
        // Heuristic: if the field is from a framework class like
        // Landroid/* or Ljava/*, assume instance field for iget/iput and
        // static for sget/sput. The calling opcode handler will override
        // is_static as needed (sget/sput set it to true explicitly).
        resolution.is_static = false;
    }

    log("✅ FIELD RESOLVED: " + resolution.class_descriptor + "." + resolution.field_name +
        " type=" + resolution.field_type +
        " offset=" + std::to_string(resolution.field_offset));
    return resolution;
}

// ── S134 (F-NEW-160) — DEX INSTANCE FIELD IDENTITY LAW ──────────────────
// A DEX instance field is identified by (declaring class, name, type) —
// NEVER by bare name. The heap's name-keyed field map makes two same-named
// fields of two different classes alias ONE storage slot (central §3
// hypothesis: two writers, one state). Measured face (solitaire 71,
// current HEAD): activity obj#16 read `iget-object e.m` (support
// AppCompatActivity delegate field) → the resolver answered the bare name
// "m" → the app's own `m` Handler field (b/b#30) leaked out as the
// "delegate" → e.onCreate invoked the delegate family on a HANDLER →
// g.a(Activity,f) got a Handler as its Activity arg → Window null →
// support/v7/app/h.<init> pc=11 NPE → APP-BOUNDARY unwind → blank
// two-color screen. ART law: fields occupy distinct slots per declaring
// class; a field of a superclass cannot alias a subclass field.
// Fix mechanics (no heap-storage refactor):
//   * NON-framework declaring class → key = "Lcls;->name" (qualified).
//     Reads answer the field DEFAULT (zero/null) when the qualified key
//     was never written — never another class's slot.
//   * FRAMEWORK declaring class (Landroid/*, Ljava/*, …) → bare name —
//     C++ shadow writers/readers keep their bare-key interop unchanged.
//   * DEX writes dual-write (qualified primary + bare legacy mirror) so
//     existing C++ bare-name readers of app fields stay fed.
// ─────────────────────────────────────────────────────────────────────────
std::string s134_dex_field_key(const std::string& cls,
                                      const std::string& name,
                                      bool dex_defined) {
    if (cls.empty() || name.empty()) return name;
    // S134 F-NEW-160: FRAMEWORK-OWNED classes (no DEX body - C++ shadows own
    // their fields) keep bare-name keys. DEX-defined classes (support lib /
    // androidx included, whatever their package prefix) use qualified
    // identity. Package-prefix heuristics are FORBIDDEN (S134 section 5):
    // the support library lives under Landroid/* and still collides.
    if (!dex_defined) return name;
    return cls + "->" + name;
}

// S134 F-NEW-160 implementation — see dalvik_engine.h declaration.
std::string DalvikExecutionEngine::resolved_field_declarer(
    const std::string& ref_cls, const std::string& name) const {
    if (ref_cls.empty() || name.empty()) return ref_cls;
    std::string walk = ref_cls;
    for (int hop = 0; hop < 32 && !walk.empty(); ++hop) {
        if (!is_dex_defined_class(walk)) break;  // framework ancestor: stop
        auto cit = class_info_index_.find(walk);
        if (cit != class_info_index_.end() && dex_report_ != nullptr) {
            const dex::ClassInfo& ci = dex_report_->classes[cit->second];
            for (const auto& f : ci.instance_fields)
                if (f.name == name) return walk;  // declarer found
        }
        auto sit = class_to_superclass_.find(walk);
        walk = (sit != class_to_superclass_.end()) ? sit->second : std::string();
    }
    return ref_cls;  // no DEX declarer found: keep the ref class as-is
}

// ── F-NEW-325 (CONT-53): the TRUE DEX declarer of an instance field ref.
// resolved_field_declarer returns ref_cls AS-IS when no DEX body on the
// chain declares the field — callers cannot distinguish "the ref class
// itself declares it" from "this field is declared by a FRAMEWORK
// ancestor" (solitaire: DrawerLayout$g [DEX] reads `width`, declared by
// the framework ViewGroup$LayoutParams; the DEX chain has NO declarer).
// Under the S134 law framework-owned fields keep ONE bare slot, but the
// iget/iput families keyed the read/write with the REF class
// (is_dex_defined_class(ref_cls)==true → qualified "LDrawerLayout$g;->width")
// while every non-interpreter writer (F-NEW-309's semantic write-back,
// the set_field_key_resolver) lands on the BARE slot → the interpreter
// read missed and answered the fabricated default (width=0 instead of the
// written WRAP_CONTENT -2 → DrawerLayout measured its drawer at 0x0).
// ART truth: field resolution walks the receiver's class chain; a field
// not declared by any DEX class lives in the framework superclass — one
// bare slot, whoever references it. This helper returns the ACTUAL DEX
// declarer (walking the chain, verifying the field body) or "" when the
// field is framework-owned — the key then stays bare.
std::string DalvikExecutionEngine::true_dex_field_declarer(
    const std::string& ref_cls, const std::string& name) const {
    if (ref_cls.empty() || name.empty()) return std::string();
    std::string walk = ref_cls;
    for (int hop = 0; hop < 32 && !walk.empty(); ++hop) {
        if (!is_dex_defined_class(walk)) break;  // framework ancestor: stop
        auto cit = class_info_index_.find(walk);
        if (cit != class_info_index_.end() && dex_report_ != nullptr) {
            const dex::ClassInfo& ci = dex_report_->classes[cit->second];
            for (const auto& f : ci.instance_fields)
                if (f.name == name) return walk;  // REAL declarer
        }
        auto sit = class_to_superclass_.find(walk);
        walk = (sit != class_to_superclass_.end()) ? sit->second : std::string();
    }
    return std::string();  // framework-owned field: no DEX declarer
}

// ── F-NEW-657 (#588 Games-g2): the STATIC-field declarer walker — the
// sput half of R-NEW-561. JVM static identity: an inherited static lives
// in the DECLARING class's ONE storage cell (javac/dx emit the access-site
// class for inherited statics, so a subclass <clinit> rebind keyed by the
// access-site lands in a cell the superclass query never reads — the
// lane's face: MyPuzzleProvider.<clinit> sput on ChessPuzzleProvider's
// sUriMatcher was invisible to the superclass query()). Mirrors
// true_dex_field_declarer over the DEX static_fields bodies; "" = not
// DEX-declared anywhere on the chain (engine-synthetic statics keep the
// ref-class key — every existing face preserved).
std::string DalvikExecutionEngine::static_field_declarer_of(
    const std::string& ref_cls, const std::string& name) const {
    if (ref_cls.empty() || name.empty()) return std::string();
    std::string walk = ref_cls;
    for (int hop = 0; hop < 32 && !walk.empty(); ++hop) {
        if (!is_dex_defined_class(walk)) break;  // framework ancestor: stop
        auto cit = class_info_index_.find(walk);
        if (cit != class_info_index_.end() && dex_report_ != nullptr) {
            const dex::ClassInfo& ci = dex_report_->classes[cit->second];
            for (const auto& f : ci.static_fields)
                if (f.name == name) return walk;  // the DECLARING class
        }
        auto sit = class_to_superclass_.find(walk);
        walk = (sit != class_to_superclass_.end()) ? sit->second : std::string();
    }
    return std::string();  // engine-synthetic static: keep the ref key
}

// ── CONT-29 W1 R-NEW-467: FIELD-RESOLUTION MEMOIZATION ──────────────────
// Epoch = the fingerprint of everything the resolution + declarer walk
// reads. Fixed after parse: nothing — BOTH hierarchy tables can grow
// mid-run (secondary-DEX class injection + [EXP095-HIER] superclass
// extension), and current_dex_index_ selects the multidex field table.
// All three are monotonically growing, so folding their sizes into the
// epoch makes ANY mid-run change invalidate every memo (re-derive once).
uint64_t DalvikExecutionEngine::field_memo_epoch() const {
    return (static_cast<uint64_t>(
                static_cast<uint32_t>(current_dex_index_))
            << 48)
         ^ (static_cast<uint64_t>(class_to_superclass_.size()) << 24)
         ^ static_cast<uint64_t>(class_info_index_.size());
}

const DalvikExecutionEngine::FieldMemo&
DalvikExecutionEngine::resolved_field_memo(uint16_t field_idx) {
    if (field_memo_.size() != 65536) field_memo_.resize(65536);
    FieldMemo& m = field_memo_[field_idx];
    const uint64_t ep = field_memo_epoch();
    // A hit requires BOTH the resolved identity AND the S134 parts: the
    // resolve_field-internal bank stores res-only entries (s134_valid=false,
    // empty fkey) — returning one of those would key every access with an
    // EMPTY string (the 851cc176→d602648e anchor collapse, first A/B).
    if (m.epoch == ep && m.res.resolved && m.s134_valid) return m;

    m.res = resolve_field(field_idx);
    m.s134_valid = false;
    m.epoch = ep;
    if (m.res.resolved) {
        m.s134_decl = true_dex_field_declarer(m.res.class_descriptor,
                                              m.res.field_name);
        m.s134_fkey = s134_dex_field_key(
            m.s134_decl, m.res.field_name, is_dex_defined_class(m.s134_decl));
        m.s134_valid = true;
    }
    return m;
}

static DalvikValue s134_field_default(const std::string& type_desc) {
    if (!type_desc.empty() && (type_desc[0] == 'L' || type_desc[0] == '['))
        return DalvikValue::make_null();
    switch (type_desc.empty() ? 'I' : type_desc[0]) {
        case 'J': return DalvikValue::make_long(0);
        case 'F': return DalvikValue::make_float(0.0f);
        case 'D': return DalvikValue::make_double(0.0);
        default: return DalvikValue::make_int(0);
    }
}

bool DalvikExecutionEngine::execute_iget(uint32_t pc, InstructionTrace& trace) {
    // Format: 22c iget vA, vB, field@CCCC (2 code units)
    // EXP-042 Phase 2 FIX: same advance-pc-on-failure strategy as iget-object.
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }
    
    uint16_t instr = bytecode_[pc];
    uint8_t dest_reg = (instr >> 8) & 0xF;
    uint8_t obj_reg = (instr >> 12) & 0xF;
    uint16_t field_idx = bytecode_[pc + 1];
    
    uint64_t f107_sr0 = 0; phase_clock().enter(phase_clock().sget_resolve_ph, f107_sr0);
    // R-NEW-467: memoized resolution + S134 identity (same value the fresh
    // walk answers; epoch-guarded on the mid-run-mutable hierarchy inputs).
    const DalvikExecutionEngine::FieldMemo& field_memo
        = resolved_field_memo(field_idx);
    const FieldResolution& field_res = field_memo.res;
    phase_clock().exit(phase_clock().sget_resolve_ph, f107_sr0);
    uint64_t f107_si0 = 0; phase_clock().enter(phase_clock().sget_init_ph, f107_si0);
    DalvikValue result_value;
    result_value.type = DalvikType::INT32;
    result_value.int_val = 0;
    
    if (field_res.resolved) {
        DalvikValue obj_ref = get_register(obj_reg);
        /* F-NEW-268d (CONT-18g): ART iget null-receiver law — iget on a null
         * receiver throws NullPointerException at the access (ART resolves
         * the field first, then null-checks — same order here; the silent
         * default-value answer hid the first divergence, issue #381 face d).
         * f141_is_null_receiver covers NULL_REF / OBJECT_REF-id-0 / INT32-0
         * typed null (F-141 + F-266a untyped-register law). */
        if (f141_is_null_receiver(obj_ref)) {
            raise_synthetic_exception(
                "Ljava/lang/NullPointerException;",
                "Attempt to read from field '" + field_res.class_descriptor +
                    "." + field_res.field_name +
                    "' on a null object reference",
                "iget-null-recv");
            return true;  /* pc_ set by raise (catch handler) or frame unwind */
        }
        // CONT-47 D7a: draw-window LayoutNode read census (env-gated,
        // bounded 64 distinct fields). Which Lel0; fields does the DEX
        // draw walk read — A/n folds vs q chain (D6 verdicts)?
        static const bool d7a_on_iget =
            diag_env("MINIANDROID_D7_READCENSUS");
        if (d7a_on_iget && draw_window_active_ &&
            field_res.class_descriptor == "Lel0;" &&
            g_d7_read_census.size() < 64)
            ++g_d7_read_census[field_res.field_name];
        if (obj_ref.type == DalvikType::OBJECT_REF && heap_.has_object(obj_ref.object_id)) {
            // S134 F-NEW-160: qualified field identity (declaring class + name).
            // F-NEW-325: a framework-owned field (no DEX declarer on the
            // chain — DrawerLayout$g -> width, declared by the framework
            // MarginLayoutParams) keeps ONE bare slot even when the REF
            // class is DEX-defined; the ref-class key fabricated a second
            // identity and the read answered a fabricated default.
            const std::string& s134_fkey = field_memo.s134_fkey;
            const bool s134_decl_is_dex = field_memo.s134_valid
                && is_dex_defined_class(field_memo.s134_decl);
            auto field_val = heap_.get_object_field(obj_ref.object_id, s134_fkey);
            // ── TRAIN-67 (T67, DIAG-ONLY, env-gated MINIANDROID_T67_LABEL_TRACE):
            // suspend-lambda STATE-MACHINE label-persistence probe. Lss1; = the
            // awaitEachGesture-level machine (R8): field l:I = the Kotlin
            // state-machine label, k:Ljava/lang/Object; = the L$0 spill. The
            // S146 death: on resume the machine re-awaits from label 0 — log
            // every read of these fields with the RECEIVER IDENTITY so the
            // iput-before-suspend vs iget-on-resume split becomes evidence.
            {
                static const bool t67_on = diag_env("MINIANDROID_T67_LABEL_TRACE");
                if (t67_on && (field_res.class_descriptor == "Lss1;" ||
                               field_res.class_descriptor == "Lxs1;" ||
                               field_res.class_descriptor == "Li6;")) {
                    static thread_local uint64_t t67_n = 0;
                    if (t67_n++ < 600) {
                        std::cerr << "[T67-IGET] Lss1;." << field_res.field_name
                                  << " obj#" << obj_ref.object_id
                                  << " hit=" << (field_val.has_value() ? 1 : 0)
                                  << " val="
                                  << (field_val.has_value()
                                          ? dalvik_value_to_string(*field_val)
                                          : std::string("(none)"))
                                  << " caller=" << current_class_ << "."
                                  << current_method_ << " pc=" << pc << std::endl;
                    }
                }
            }
            // ── S211 (DIAG-ONLY, env-gated MINIANDROID_S211_SEGTRACE):
            // dooz post-nav zombie probe — every iget of a Lbw0; (kotlinx
            // Segment family) INT field logs (obj#, field, value, caller,
            // pc). Answers: what did the .e scanner's mask register
            // (this.c) actually read at the divergence — 7 or garbage?
            {
                static const bool s211_on = diag_env("MINIANDROID_S211_SEGTRACE");
                if (s211_on && field_res.class_descriptor == "Lbw0;" &&
                    field_res.field_name == "c") {
                    static thread_local uint64_t s211_n = 0;
                    if (s211_n++ < 400) {
                        std::cerr << "[S211-IGET] Lbw0;." << field_res.field_name
                                  << " obj#" << obj_ref.object_id
                                  << " hit=" << (field_val.has_value() ? 1 : 0)
                                  << " val="
                                  << (field_val.has_value()
                                          ? dalvik_value_to_string(*field_val)
                                          : std::string("(none)"))
                                  << " caller=" << current_class_ << "."
                                  << current_method_ << " pc=" << pc << std::endl;
                    }
                }
            }
            // ── S221 (DIAG-ONLY, env-gated MINIANDROID_S221_DENSTRACE):
            // dooz post-NewGame text-cache ISE storm probe. The app-side
            // MultiParagraphLayoutCache flips density (2.625 real <-> 0.0
            // Unspecified) between layout and draw — each flip markDirty()s
            // the cache so EVERY draw throws the "could not provide
            // TextLayoutResult" ISE and one escapes MainActivity.onCreate
            // (ART process-death; the transition freezes half-slid).
            // Upstream law (TextStringSimpleNode.kt header): "the density
            // should not change between layout and draw phases". Every
            // float iget answering 0.0 INSIDE a draw window logs (field,
            // receiver, caller chain top 6) — the 0.0 delivery site becomes
            // evidence instead of a guess.
            {
                static const bool s221_on = diag_env("MINIANDROID_S221_DENSTRACE");
                if (s221_on && draw_window_active_ && field_val.has_value() &&
                    field_val->type == DalvikType::FLOAT32 &&
                    field_val->float_val == 0.0f) {
                    static thread_local uint64_t s221_n = 0;
                    if (s221_n++ < 40) {
                        std::cerr << "[S221-ZERODENS] "
                                  << field_res.class_descriptor << "."
                                  << field_res.field_name
                                  << " obj#" << obj_ref.object_id
                                  << " caller=" << current_class_ << "."
                                  << current_method_ << " pc=" << pc;
                        auto s221_frames = call_stack_.snapshot_top_first();
                        for (size_t fi = 0;
                             fi < s221_frames.size() && fi < 6; ++fi)
                            std::cerr << " <" << s221_frames[fi].first << "."
                                      << s221_frames[fi].second << ">";
                        std::cerr << std::endl;
                    }
                }
            }
            // ── TRAIN-68 (T68-JOBGET): the pointerInputJob null-check reads.
            // Lor1;.v:Lkp1; = the lazy coroutine job — every node reads it on
            // the first event (if-null-launch). Log the READ + the value with
            // receiver identity so the skipped-launch nodes (#6571/#14049)
            // become evidence: was v non-null, or did the read fail?
            {
                static const bool t68g_on = diag_env("MINIANDROID_T68_NODE_TRACE");
                if (t68g_on && field_res.class_descriptor == "Lor1;" &&
                    field_res.field_name == "v") {
                    static thread_local uint64_t t68g_n = 0;
                    if (t68g_n++ < 120)
                        std::cerr << "[T68-JOBGET] Lor1;.v obj#"
                                  << obj_ref.object_id
                                  << " hit=" << (field_val.has_value() ? 1 : 0)
                                  << " val="
                                  << (field_val.has_value()
                                          ? dalvik_value_to_string(*field_val)
                                          : std::string("(none)"))
                                  << " caller=" << current_class_ << "."
                                  << current_method_ << " pc=" << pc
                                  << std::endl;
                }
            }
            if (!field_val.has_value() && s134_decl_is_dex) {
                // AOSP law: an instance field never written answers its
                // DEFAULT value — never another class's same-named slot.
                // FINAL-CAMPAIGN PHASE 3 diag (SGET-MISS probe precedent):
                // a DEX-defined qualified read that misses means the writer
                // used a different identity — dump the asked key + the
                // object's actual keys (throttled) so the mismatch is
                // EVIDENCE, not a guess.
                static thread_local uint64_t iget_miss_diag_n = 0;
                if (iget_miss_diag_n < 16) {
                    ++iget_miss_diag_n;
                    const auto* hobj = heap_.get(obj_ref.object_id);
                    std::string have;
                    if (hobj) {
                        int cnt = 0;
                        for (const auto& kv : hobj->fields) {
                            if (cnt++ >= 6) break;
                            have += " " + kv.first;
                        }
                    }
                    std::cerr << "[IGET-MISS-DIAG] asked=\"" << s134_fkey
                              << "\" obj#" << obj_ref.object_id
                              << " cls="
                              << (hobj ? hobj->class_descriptor : std::string("<no-heap-obj>"))
                              << " keys:" << (have.empty() ? " <none>" : have)
                              << " caller=" << current_class_ << "."
                              << current_method_ << std::endl;
                }
                field_val = s134_field_default(field_res.field_type);
            }
            if (field_val.has_value()) {
                result_value = field_val.value();
            }
        }
    }
    // M3 FIELD-TRACE (AG diagnostic): env-gated field-access value trace.
    {
        DalvikValue tgt = get_register(obj_reg);
        if (field_trace_filter_set() &&
            field_trace_active(field_res.field_name.c_str(),
                               (current_class_ + "." + current_method_).c_str(),
                               field_res.class_descriptor.c_str())) {
            std::cerr << "[FIELD-TRACE] get " << current_class_ << "." << current_method_
                      << " " << field_res.class_descriptor << "." << field_res.field_name
                      << " obj#" << (tgt.type == DalvikType::OBJECT_REF ? tgt.object_id : 0)
                      << " value=" << dalvik_value_to_string(result_value)
                      << std::endl;
        }
        // F-NEW-267 (CONT-64 W1) HIT-TEST WIDE-READ probe — env-gated
        // MINIANDROID_TOUCH_FIELD_TRACE=1, bounded, ACTIVE ONLY during the
        // touch dispatch. Logs every iget-wide (64-bit = the packed
        // IntOffset/IntSize/Constraints value-class reads) on the compose
        // node-tree classes so the decode sees EXACTLY what bounds the
        // pure-DEX hit-test walk consumes.
        static thread_local const bool htft_on =
            std::getenv("MINIANDROID_TOUCH_FIELD_TRACE") != nullptr;
        if (htft_on && touch_dispatch_active_ &&
            result_value.type == DalvikType::INT64) {
            static const char* htft_classes[] = {
                "Lel0;", "Lkz0;", "Lug0;", "Lpz0;", "Lil0;", "Lzs0;",
                "Lbt0;", "Ld61;", "Las0;", "Lkc;", "Loh;", "Lg5;"};
            const std::string& cd = field_res.class_descriptor;
            for (const char* hc : htft_classes) {
                if (cd == hc) {
                    static thread_local uint64_t htft_n = 0;
                    if (htft_n++ < 240) {
                        DalvikValue tgt2 = get_register(obj_reg);
                        std::cerr << "[HT-WIDE] " << cd << "."
                                  << field_res.field_name
                                  << " obj#" << (tgt2.type == DalvikType::OBJECT_REF
                                                     ? tgt2.object_id : 0)
                                  << " = " << result_value.long_val
                                  << " caller=" << current_class_ << "."
                                  << current_method_ << std::endl;
                    }
                    break;
                }
            }
        }
        // ── TRAIN-64 (T64, DIAG-ONLY, env-gated MINIANDROID_T64_CHANGE_TRACE):
        // pointer-change field READ law. Lu71; = PointerInputChange (R8):
        // d=pressed, h=previousPressed, o=isConsumed, p. The tap state
        // machine (waitForUpOrCancellation: fastAll{changedToUp} =
        // !pressed && previousPressed; fastAny{isConsumed}) reads these
        // fields INLINE (R8), so no invoke probe can see them. Log every
        // boolean read during the touch dispatch — answers WHY the dooz
        // cell tap never fires onTap (changedToUp false? consumed?).
        static thread_local const bool t64r_on =
            std::getenv("MINIANDROID_T64_CHANGE_TRACE") != nullptr;
        if (t64r_on && touch_dispatch_active_ && field_res.resolved &&
            field_res.class_descriptor == "Lu71;") {
            static const char* t64_bools[] = {"d", "h", "o", "p"};
            for (const char* t64b : t64_bools) {
                if (field_res.field_name == t64b) {
                    static thread_local uint64_t t64r_n = 0;
                    if (t64r_n++ < 400) {
                        DalvikValue t64_t = get_register(obj_reg);
                        std::cerr << "[T64-R] Lu71;." << field_res.field_name
                                  << " obj#"
                                  << (t64_t.type == DalvikType::OBJECT_REF
                                          ? t64_t.object_id : 0)
                                  << " = "
                                  << dalvik_value_to_string(result_value)
                                  << " dst=v" << static_cast<int>(dest_reg)
                                  << " caller=" << current_class_ << "."
                                  << current_method_ << std::endl;
                    }
                    break;
                }
            }
            // T64-Q: the q-chain read (b()Z recurses into q when non-null —
            // a self/loop in q makes isConsumed answer from the WRONG change).
            if (field_res.field_name == "q") {
                static thread_local uint64_t t64q_n = 0;
                if (t64q_n++ < 200) {
                    DalvikValue t64_t3 = get_register(obj_reg);
                    std::cerr << "[T64-Q] Lu71;.q obj#"
                              << (t64_t3.type == DalvikType::OBJECT_REF
                                      ? t64_t3.object_id : 0)
                              << " -> "
                              << dalvik_value_to_string(result_value)
                              << " caller=" << current_class_ << "."
                              << current_method_ << std::endl;
                }
            }
            // T64b: the isOutOfBounds arm reads the packed position
            // (j = position, g = previousPosition) as iget-wide — log those
            // during the touch dispatch (bounds: size + extendedTouchPadding
            // decide the cancel).
            if (field_res.field_name == "j" || field_res.field_name == "g") {
                static thread_local uint64_t t64p_n = 0;
                if (t64p_n++ < 200 && result_value.type == DalvikType::INT64) {
                    DalvikValue t64_t2 = get_register(obj_reg);
                    std::cerr << "[T64-POS] Lu71;." << field_res.field_name
                              << " obj#"
                              << (t64_t2.type == DalvikType::OBJECT_REF
                                      ? t64_t2.object_id : 0)
                              << " = " << result_value.long_val
                              << " caller=" << current_class_ << "."
                              << current_method_ << std::endl;
                }
            }
        }
    }
    // EXP-042 Phase 2: on any failure path, fall through with default 0 and
    // advance pc_ — never return false (which would cause an infinite loop).
    
    set_register(dest_reg, result_value);
    // S157-B (CONT-42 zero-cost-gate law): the operand block below builds
    // concat/to_string heap strings per executed iget — with trace_cap == 0
    // the trace is destroyed unread (phase-A recording-block proof), so the
    // block is pure waste. Gated; content identical when consumed.
    if (config_.trace_cap > 0) {
    trace.operands.push_back({"v" + std::to_string(dest_reg), "destination"});
    trace.operands.push_back({"v" + std::to_string(obj_reg), "object"});
    trace.operands.push_back({"field", field_res.class_descriptor + "." + field_res.field_name});
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});
    }
    
    pc_ = pc + 2;
    return true;
}

// ── S122 (R-NEW-414) — instance field-initializer defaults ──────────────
// javac compiles `final Rect m = new Rect();` (and every other inline
// instance-field initializer) into the constructor body: new-instance T vN
// → invoke-direct T.<init> vN → iput-object vN → F. ART therefore
// guarantees such fields are NON-NULL on any constructed object. This
// runtime materializes view/heap objects for DEX-defined classes WITHOUT
// running the class's <init> (the subdecor ContentFrameLayout path), so
// iget-object on those fields answered null and apps died on the first
// method call (chess 10.6.0: ContentFrameLayout field l — the AOSP
// `mDecorPadding` Rect — read null in the measure path → Rect.set NPE →
// onCreate unwound → blank screen).
// LAW: a field whose constructor initializer is `new T` is materialized
// as an empty T on a heap read that would otherwise answer null. Generic
// across every DEX class; zero package checks.
// S122: DEX instruction sizes (in 16-bit code units) for the R-NEW-414
// initializer scan — standard format widths from the DEX spec tables.
static size_t r414_opcode_size(uint8_t op) {
    static const uint8_t k1[12] = {0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06,
                                   0x07, 0x08, 0x09, 0x0a, 0x0b};
    static const uint8_t k1b[16] = {0x0c, 0x0d, 0x0e, 0x0f, 0x10, 0x11, 0x12,
                                    0x1d, 0x1e, 0x27, 0x28, 0x7b, 0x7c, 0x7d,
                                    0x7e, 0x27};
    static const uint8_t k1c[8] = {0xb0, 0xb1, 0xb2, 0xb3, 0xb4, 0xb5, 0xb6,
                                   0xb7};
    if (op == 0x13 || op == 0x15 || op == 0x16 || op == 0x19 || op == 0x1c ||
        op == 0x1f || op == 0x20 || op == 0x21 || op == 0x22 || op == 0x23)
        return 2;
    if (op == 0x14 || op == 0x17 || op == 0x18) return 3;
    if (op == 0x1a) return 2;
    if (op == 0x1b) return 3;
    if (op == 0x29) return 2;
    if (op == 0x2a || op == 0x2b || op == 0x2c) return 3;
    if (op == 0x24 || op == 0x25 || op == 0x26) return 3;
    if ((op >= 0x2d && op <= 0x31) || (op >= 0x44 && op <= 0x6d)) return 2;
    if ((op >= 0x32 && op <= 0x3d)) return 2;
    if ((op >= 0x3e && op <= 0x43)) return 2;  // unused range (nop-width)
    if ((op >= 0x6e && op <= 0x72) || (op >= 0x74 && op <= 0x78)) return 3;
    if (op >= 0x7f && op <= 0xaf) return 2;
    for (uint8_t k : k1) if (op == k) return 1;
    for (uint8_t k : k1b) if (op == k) return 1;
    for (uint8_t k : k1c) if (op == k) return 1;
    if (op >= 0xb8 && op <= 0xcf) return 1;
    if (op >= 0xd0 && op <= 0xe2) return 2;
    return 1;  // unknown: conservative 1-unit stride
}

void DalvikExecutionEngine::scan_init_field_defaults(const std::string& cls) {
    if (init_defaults_scanned_.count(cls) > 0) return;
    init_defaults_scanned_.insert(cls);
    if (!dex_report_) return;
    auto class_it = class_info_index_.find(cls);
    if (class_it == class_info_index_.end()) return;
    const dex::ClassInfo& info = dex_report_->classes[class_it->second];
    uint32_t dex_idx = 0;
    if (auto dit = class_to_dex_index_.find(cls); dit != class_to_dex_index_.end())
        dex_idx = dit->second;
    auto& field_map = init_field_defaults_[cls];
    // S156-P4 (CONT-42 zero-cost-gate law): static-cached — one-time env read.
    static const bool r414_trace = std::getenv("MINIANDROID_R414_TRACE") != nullptr;
    for (const auto* list : {&info.direct_methods, &info.virtual_methods}) {
        for (const auto& m : *list) {
            if (m.name != "<init>" || m.bytecode.empty()) continue;
            // reg → newest new-instance type (javac initializers store the
            // freshly constructed object almost immediately)
            std::map<uint16_t, std::string> reg_types;
            const std::vector<uint16_t>& bc = m.bytecode;
            size_t pc2 = 0;
            while (pc2 + 1 < bc.size()) {
                uint16_t unit = bc[pc2];
                uint8_t op = unit & 0xFF;
                uint8_t hi = (unit >> 8) & 0xFF;
                if (op == 0x00) {
                    // nop; skip pseudo-data payloads so the scan stays aligned
                    if (hi == 0x01) {  // packed-switch-payload
                        if (pc2 + 3 >= bc.size()) break;
                        uint32_t sz = (uint32_t)bc[pc2 + 1] |
                                      ((uint32_t)bc[pc2 + 2] << 16);
                        pc2 += 4 + sz * 2;
                        continue;
                    }
                    if (hi == 0x02) {  // sparse-switch-payload
                        if (pc2 + 3 >= bc.size()) break;
                        uint32_t sz = (uint32_t)bc[pc2 + 1] |
                                      ((uint32_t)bc[pc2 + 2] << 16);
                        pc2 += 2 + sz * 4;
                        continue;
                    }
                    if (hi == 0x03) {  // fill-array-data-payload
                        if (pc2 + 5 >= bc.size()) break;
                        uint16_t ew = bc[pc2 + 1];
                        uint32_t sz = (uint32_t)bc[pc2 + 2] |
                                      ((uint32_t)bc[pc2 + 3] << 16);
                        pc2 += 4 + (size_t)((uint64_t)sz * ew + 1) / 2;
                        continue;
                    }
                    pc2 += 1;
                    continue;
                }
                if (op == 0x22 && pc2 + 1 < bc.size()) {  // new-instance
                    uint16_t reg = hi;
                    uint16_t tidx = bc[pc2 + 1];
                    reg_types[reg] = resolve_type_for_dex(tidx, dex_idx);
                    pc2 += r414_opcode_size(op);
                    continue;
                }
                if (op == 0x5B && pc2 + 1 < bc.size()) {  // iput-object
                    uint8_t src = (unit >> 8) & 0xF;
                    uint16_t fidx = bc[pc2 + 1];
                    auto rt = reg_types.find(src);
                    if (rt != reg_types.end()) {
                        FieldResolution fr = resolve_field((uint16_t)fidx);
                        if (fr.resolved && fr.field_type == rt->second) {
                            field_map[fr.field_name] = rt->second;
                        }
                    }
                    pc2 += r414_opcode_size(op);
                    continue;
                }
                pc2 += r414_opcode_size(op);  // spec-width stride keeps the scan aligned
            }
            if (r414_trace && !field_map.empty()) {
                std::cerr << "[R414-SCAN] " << cls << " initializers:";
                for (auto& kv : field_map)
                    std::cerr << " " << kv.first << "->" << kv.second;
                std::cerr << std::endl;
            }
        }
    }
}

DalvikValue DalvikExecutionEngine::materialize_init_default(
    const std::string& type_desc) {
    if (type_desc.empty() || type_desc[0] != 'L') return DalvikValue::make_null();
    uint32_t oid = heap_.allocate(type_desc, 0, 0);
    if (type_desc == "Landroid/graphics/Rect;" ||
        type_desc == "Landroid/graphics/Point;" ||
        type_desc == "Landroid/graphics/PointF;") {
        for (const char* f : {"left", "top", "right", "bottom", "x", "y"})
            heap_.set_object_field(oid, f, DalvikValue::make_int(0));
    } else if (type_desc == "Landroid/util/TypedValue;") {
        heap_.set_object_field(oid, "type", DalvikValue::make_int(0));
    } else if (type_desc == "Ljava/lang/StringBuilder;" ||
               type_desc == "Ljava/lang/StringBuffer;") {
        // leave empty shell; string methods are shadow-dispatched
    }
    // F-NEW-464 (CONT-114): EXECUTE the ()V constructor of a DEX-defined
    // initializer type. ART law (completed by this change): a field never
    // written reads null; an initializer-default object exists only after
    // its constructing <init> ran. F-NEW-274 already gates on the ()V
    // ctor's EXISTENCE, but the materializer only allocated — every
    // DEX-defined zero-state stayed a bare shell (tower3d: libGDX
    // DirectionalLightsAttribute.lights materialized as Array obj#393 with
    // ZERO fields; Array.add then read size off nothing -> ARR-LEN-NULL NPE
    // -> AndroidLauncher.onCreate death). Running the real ()V ctor gives
    // the object its true zero-state (Array: items/ordered/size). Framework
    // shells (Rect/Point/TypedValue above) keep their seeded zero-state.
    // Re-entrancy guard: a ctor whose body reads the SAME missing field
    // must not recurse forever — nested same-type materialization returns
    // the bare shell (documented honest frontier).
    static thread_local std::string f464_in_flight;
    if (f464_in_flight == type_desc) {
        return DalvikValue::make_object(oid, type_desc);
    }
    // F-NEW-464/465 (CONT-114 + CONT-116 correction): EXECUTE the ()V
    // constructor of a DEX-defined initializer type. CONT-116 found the
    // dispatch condition INVERTED: `!class_has_no_arg_ctor` ran the ()V
    // body only for classes WITHOUT one (a ctor that does not exist) and
    // skipped every class that HAS one — libGDX Array's ()V never ran, so
    // every R-NEW-414-materialized Array stayed a bare shell (tower3d
    // obj#393: zero fields → Array.add pc=4 ARR-LEN-NULL NPE →
    // AndroidLauncher.onCreate APP-BOUNDARY death). ART law: run the ()V
    // ctor exactly when it EXISTS; the F-NEW-274 gate upstream already
    // refuses fabrication for ctor-less classes (honest null path).
    if (class_info_index_.find(type_desc) != class_info_index_.end() &&
        dex_report_ && class_has_no_arg_ctor(type_desc)) {
        f464_in_flight = type_desc;
        DalvikValue recv = DalvikValue::make_object(oid, type_desc);
        DalvikValue ret = DalvikValue::make_void();
        DalvikExecutionResult res;
        // F-NEW-501 (CONT-159): pass the EXACT "()V" descriptor. The
        // materializer must run THE no-arg constructor — ART's default-
        // initialization contract. With the descriptor left empty, the
        // lenient overload selection (EXP-078 largest-bytecode law) picked
        // whichever same-name <init> had the biggest body: for libgdx Array
        // that was the COPY ctor (Array;(Array;)V, 30 units > 7) — it then
        // read the fresh shell's ABSENT items field → getClass() on null →
        // NPE → AndroidLauncher.onCreate death (tower3d uniform-black face).
        // The F-NEW-274 gate above already verified a local ()V exists, so
        // the exact-match law resolves it deterministically.
        bool ran = try_recursive_invoke(type_desc, "<init>", {recv}, ret, res,
                                        "()V");
        f464_in_flight.clear();
        if (ran) heap_.mark_initialized(oid);
        // ran == false: keep the seeded shell (honest — ctor not found in
        // the DEX chain after all); the read still answers a valid object.
    }
    DalvikValue v = DalvikValue::make_object(oid, type_desc);
    return v;
}

// F-NEW-274 (CONT-22) — ART constructor-contract gate for R-NEW-414
// initializer materialization (see header for the law). Live face (dooz,
// run/cont21/after/dooz_r3 + fresh CONT-22 runs): Lgf1;.g's initializer is
// `new Lwg0;(Lrf1;, I)` — an R8 merged-lambda class whose ONLY constructors
// take captured arguments; R414 fabricated a zero Lwg0; whose capture field
// .f stayed null, the caller's own `if-eqz` null-guard at the read site
// (Lg8;.a:  iget g; if-eqz; …invoke .y) then saw a NON-null broken object,
// invoked the save-lambda body, and died at `iget Lrf1;.f` on the null
// capture (SavedStateRegistry.performSave neighborhood). ART law: a field
// never written reads null; an initializer-default object exists only after
// its constructing <init> ran, so a class with no ()V ctor cannot have a
// legal zero-state instance. DEX-defined classes are inspected for a ()V
// <init>; non-DEX classes (framework Rect/Point/TypedValue shells the
// materializer seeds itself) keep the old behavior.
bool DalvikExecutionEngine::class_has_no_arg_ctor(const std::string& type_desc) {
    if (type_desc.empty() || type_desc[0] != 'L') return false;
    auto cit = class_info_index_.find(type_desc);
    if (cit == class_info_index_.end() ||
        cit->second >= dex_report_->classes.size()) {
        // Framework-owned type: materialize_init_default's seed block
        // defines its zero-state contract (Rect/Point/PointF/TypedValue).
        return true;
    }
    const auto& cls = dex_report_->classes[cit->second];
    for (const auto& m : cls.direct_methods) {
        if (m.name == "<init>" && m.descriptor == "()V") return true;
    }
    return false;
}

bool DalvikExecutionEngine::execute_iget_object(uint32_t pc, InstructionTrace& trace) {
    // Format: 22c iget-object vA, vB, field@CCCC
    // Read object field from object and place reference in destination register
    // EXP-042 Phase 2 FIX: Previously, every error path returned false WITHOUT
    // advancing pc_. The caller then re-fetched the same opcode, hit the same
    // error, and looped forever — the loop detector eventually halted the
    // method, but only after 50 001 wasted iterations. Now all error paths
    // advance pc_ by 2 (22c format is 2 code units) and return true so the
    // caller can continue with a sensible default (null/0).
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }
    
    uint16_t instr = bytecode_[pc];
    uint8_t dest_reg = (instr >> 8) & 0xF;    // vA - 4-bit destination reg
    uint8_t obj_reg = (instr >> 12) & 0xF;    // vB - 4-bit object reg
    uint16_t field_idx = bytecode_[pc + 1];   // CCCC - field index
    
    // Resolve field from DEX (R-NEW-467 memoized)
    const DalvikExecutionEngine::FieldMemo& field_memo
        = resolved_field_memo(field_idx);
    const FieldResolution& field_res = field_memo.res;
    if (!field_res.resolved) {
        trace.error_message = "Failed to resolve field index " + std::to_string(field_idx);
        trace.status = InstructionTrace::Status::CRASH_ERROR;
        // EXP-042 Phase 2: advance pc_ and continue rather than spin.
        set_register(dest_reg, DalvikValue::make_null());
        // S88 DIAG: unresolved-field silent-null route — count and name it.
        {
            static thread_local uint64_t s88_uf_n = 0;
            if (s88_uf_n < 40) {
                ++s88_uf_n;
                std::cerr << "[S88-UNRESOLVED-FIELD] idx=" << field_idx
                          << " caller=" << current_class_ << "." << current_method_
                          << " pc=" << pc << std::endl;
            }
        }
        pc_ = pc + 2;
        return true;
    }
    
    // Get object reference from register
    DalvikValue obj_ref = get_register(obj_reg);

    /* F-NEW-268d (CONT-18g): ART iget-object null-receiver law — mirror of
     * the iget arm (field resolved first, then the null check; issue #381
     * face d). The old path answered a silent null default. */
    if (f141_is_null_receiver(obj_ref)) {
        raise_synthetic_exception(
            "Ljava/lang/NullPointerException;",
            "Attempt to read from field '" + field_res.class_descriptor +
                "." + field_res.field_name +
                "' on a null object reference",
            "iget-null-recv");
        return true;  /* pc_ set by raise (catch handler) or frame unwind */
    }

    // CONT-47 D7a: draw-window LayoutNode read census (env-gated,
    // bounded 64 distinct fields) — same law as the iget arm.
    static const bool d7a_on_igeto =
        diag_env("MINIANDROID_D7_READCENSUS");
    if (d7a_on_igeto && draw_window_active_ &&
        field_res.class_descriptor == "Lel0;" &&
        g_d7_read_census.size() < 64)
        ++g_d7_read_census[field_res.field_name];

    // S88 DIAG (bounded, env-gated): MiniFont$Glyph field reads — tweakWidth
    // NPE "Path.transform on null" while iput traces show the path field
    // stored. This probe exposes resolved/has_object/result for every
    // Glyph iget-object.
    // S156-P4 (CONT-42 zero-cost-gate law): the raw std::getenv ran PER
    // iget-object call (7.06M calls on the dooz record phase = a linear
    // environ scan per op, ~hundreds of ns each). Static-cached: the env
    // is read once, the gate costs one branch.
    static const bool s88_glyph_diag = std::getenv("MINIANDROID_S88_GLYPH") != nullptr;
    if (s88_glyph_diag &&
        field_res.class_descriptor.find("MiniFont$Glyph") != std::string::npos) {
        std::cerr << "[S88-IGET] " << current_class_ << "." << current_method_
                  << " pc=" << pc
                  << " resolved=" << field_res.resolved
                  << " field=" << field_res.field_name
                  << " recv_type=" << static_cast<int>(obj_ref.type)
                  << " recv_id=" << obj_ref.object_id
                  << " in_heap=" << (heap_.has_object(obj_ref.object_id) ? "Y" : "N")
                  << std::endl;
    }

    // ── TRAIN-68 (T68-JOBGET-OBJ): the pointerInputJob null-check read is an
    // IGET-OBJECT (Lor1;.v:Lkp1;) — this arm, not the int iget arm. Log the
    // read with receiver identity: hit + value for every launch-gate check.
    {
        static const bool t68o_on = diag_env("MINIANDROID_T68_NODE_TRACE");
        if (t68o_on && field_res.class_descriptor == "Lor1;" &&
            field_res.field_name == "v") {
            static thread_local uint64_t t68o_n = 0;
            if (t68o_n++ < 120)
                std::cerr << "[T68-JOBGET-OBJ] Lor1;.v obj#"
                          << (obj_ref.type == DalvikType::OBJECT_REF
                                  ? obj_ref.object_id : 0)
                          << " in_heap="
                          << (heap_.has_object(obj_ref.object_id) ? "Y" : "N")
                          << " caller=" << current_class_ << "."
                          << current_method_ << " pc=" << pc << std::endl;
        }
    }

    DalvikValue result_value;
    result_value.type = DalvikType::NULL_REF;
    result_value.object_id = 0;
    
    if (obj_ref.type == DalvikType::OBJECT_REF) {
        // Look up object field from heap
        if (heap_.has_object(obj_ref.object_id)) {
            if (field_trace_filter_set() &&
                field_trace_active(field_res.field_name.c_str(),
                                   (current_class_ + "." + current_method_).c_str(),
                                   field_res.class_descriptor.c_str())) {
                DalvikValue tgt = get_register(obj_reg);
                std::cerr << "[FIELD-TRACE] get-obj " << current_class_ << "."
                          << current_method_ << " "
                          << field_res.class_descriptor << "." << field_res.field_name
                          << " obj#" << (tgt.type == DalvikType::OBJECT_REF ? tgt.object_id : 0)
                          << std::endl;
            }
            // F-NEW-325: true-declarer keying (see execute_iget).
            // R-NEW-467: the declarer walk + key concat are memoized.
            const std::string& s134_fkey = field_memo.s134_fkey;
            auto field_val = heap_.get_object_field(obj_ref.object_id,
                s134_fkey);
            // W5 (Coder-4) DIAG: Koin Module.includedModules read forensics.
            {
                static const bool f566f_on =
                    diag_env("MINIANDROID_F566_FIELD_DIAG");
                static thread_local uint64_t f566f_n = 0;
                if (f566f_on && field_res.resolved &&
                    (field_res.field_name == "includedModules" ||
                     field_res.field_name == "includes") &&
                    f566f_n++ < 60) {
                    std::cerr << "[F566-IGET] " << field_res.field_name << " obj#"
                              << obj_ref.object_id << " key=\"" << s134_fkey
                              << "\" hit="
                              << (field_val.has_value() ? 1 : 0) << " val=";
                    if (field_val.has_value())
                        std::cerr << dalvik_value_to_string(*field_val);
                    else
                        std::cerr << "(none=default-null)";
                    std::cerr << " caller=" << current_class_ << "."
                              << current_method_ << " pc=" << pc << std::endl;
                    // W6 (Coder-4): when loadModules reads the includes
                    // list, dump the value object's STORE SHAPE (class,
                    // heap array length, first elements) — the flatten
                    // drop forensics (F-C4-570 root-pinning).
                    if (field_val.has_value() &&
                        field_val->type == DalvikType::OBJECT_REF &&
                        field_val->object_id != 0 &&
                        current_class_ == "Lorg/koin/core/Koin;") {
                        uint32_t fv = field_val->object_id;
                        const auto* fvo = heap_.has_object(fv)
                            ? heap_.get(fv) : nullptr;
                        std::cerr << "[W6-INCL] list obj#" << fv << " class="
                                  << (fvo ? fvo->class_descriptor
                                          : std::string("?"));
                        int32_t w6_alen = -1;
                        {
                            auto w6_al =
                                heap_.get_object_field(fv, "__array_length__");
                            if (w6_al.has_value() &&
                                w6_al->type == DalvikType::INT32)
                                w6_alen = w6_al->int_val;
                            std::cerr << " __array_length__="
                                      << (w6_al.has_value()
                                              ? std::to_string(w6_alen)
                                              : std::string("ABSENT"));
                        }
                        if (fvo) {
                            std::cerr << " fields=";
                            size_t shown = 0;
                            for (const auto& w6f : fvo->fields) {
                                if (shown++ >= 6) { std::cerr << "…"; break; }
                                std::cerr << w6f.first << "("
                                          << static_cast<int>(w6f.second.type)
                                          << ",o" << w6f.second.object_id
                                          << ") ";
                            }
                        }
                        // first two array slots if present
                        for (int32_t w6_i = 0; w6_i < 2; ++w6_i) {
                            auto w6_ev = heap_.get_object_field(
                                fv, "array[" + std::to_string(w6_i) + "]");
                            if (w6_ev.has_value())
                                std::cerr << " arr[" << w6_i << "]=o"
                                          << w6_ev->object_id;
                        }
                        std::cerr << std::endl;
                    }
                }
            }
            // ── TRAIN-68 (T68-JOBGET-VAL): the pointerInputJob read VALUE.
            // The DOWN-window evidence: nodes #6571/#14049 jumped pc=8 -> 29
            // with the launch block skipped — this prints the exact value the
            // null-check saw (stale slot vs default-null vs wrong key).
            {
                static const bool t68v_on = diag_env("MINIANDROID_T68_NODE_TRACE");
                if (t68v_on && field_res.class_descriptor == "Lor1;" &&
                    field_res.field_name == "v") {
                    static thread_local uint64_t t68v_n = 0;
                    if (t68v_n++ < 120) {
                        std::cerr << "[T68-JOBGET-VAL] Lor1;.v obj#"
                                  << obj_ref.object_id << " key=\"" << s134_fkey
                                  << "\" hit=" << (field_val.has_value() ? 1 : 0)
                                  << " val=";
                        if (field_val.has_value())
                            std::cerr << dalvik_value_to_string(*field_val);
                        else
                            std::cerr << "(none=default-null)";
                        std::cerr << " caller=" << current_class_ << "."
                                  << current_method_ << " pc=" << pc
                                  << std::endl;
                    }
                }
            }
            // S134 F-NEW-160 probe: qualified-read hit/miss visibility.
            {
                static thread_local const bool s134_qprobe =
                    std::getenv("MINIANDROID_S134_QPROBE") != nullptr;
                if (s134_qprobe) {
                    static thread_local uint64_t s134_qn = 0;
                    // S49 convention: budget env-configurable
                    // (MINIANDROID_S134_QGET_BUDGET) so deep-boot forensics
                    // can capture beyond the default 60 rows.
                    static thread_local uint64_t s134_qcap = [] {
                        const char* b = std::getenv("MINIANDROID_S134_QGET_BUDGET");
                        return (b != nullptr) ? static_cast<uint64_t>(atoi(b)) : 60ull;
                    }();
                    if (s134_qn < s134_qcap) {
                        ++s134_qn;
                        std::cerr << "[S134-QGET] key="
                                  << s134_dex_field_key(field_res.class_descriptor,
                                                        field_res.field_name,
                                                        is_dex_defined_class(
                                                            field_res.class_descriptor))
                                  << " obj#" << obj_ref.object_id
                                  << " hit=" << (field_val.has_value() ? "Y" : "N")
                                  << (field_val.has_value()
                                          ? " val=" + field_val->to_string()
                                          : "")
                                  << " caller=" << current_class_ << "."
                                  << current_method_ << " pc=" << pc
                                  << std::endl;
                    }
                }
            }
            // S134 F-NEW-160: qualified identity read (declaring class + name);
            // non-framework miss answers the field DEFAULT (null for refs —
            // the R-NEW-414 initializer materialization below still applies
            // on top of the honest default).
            // S122 (R-NEW-414): field-initializer default. A field whose
            // constructor initializer is `new T` is NON-NULL on any real
            // instance. When the heap object (materialized for a DEX-defined
            // class, e.g. a view node whose <init> the inflater did not run)
            // has NO entry — or a null/zero entry — for the field, materialize
            // the initializer type instead of answering a manufactured null
            // (chess: ContentFrameLayout.mDecorPadding Rect read null ->
            // Rect.set NPE -> onCreate dead). The value is STORED so identity
            // stays stable.
            {
                // F-NEW-252 (explicit-null beats initializer law): a heap
                // ENTRY holding NULL_REF is a NULL that executed bytecode
                // WROTE (iput-object with a null source — dooz draw path:
                // Lpz0;.L0 stores its null p2 into Lkc;.c, and Lyl;.z's
                // `if-eqz v2` null-guard then skips the tracker block, which
                // is the real-ART behavior). Fabricating the initializer
                // default over an explicit null turned the app's legal null
                // into a fake `new Object`, forced the tracker read, and
                // crashed dispatchDraw with the app's own
                // "Only add dependencies during a tracking block" IAE.
                // Absent entries (no value at all) and dangling refs stay
                // missing — the chess ContentFrameLayout.mDecorPadding case
                // (inflater-materialized object whose <init> never ran) is
                // unchanged: its fields have NO entries.
                bool r414_missing = !field_val.has_value();
                if (!r414_missing) {
                    const DalvikValue& fv = field_val.value();
                    r414_missing =
                        (fv.type == DalvikType::OBJECT_REF &&
                         fv.object_id == 0) ||
                        (fv.type == DalvikType::OBJECT_REF &&
                         !heap_.has_object(fv.object_id));
                }
                if (r414_missing) {
                    const HeapObject* r414_hobj = heap_.get(obj_ref.object_id);
                    std::string r414_cls =
                        r414_hobj ? r414_hobj->class_descriptor
                                  : field_res.class_descriptor;
                    if (std::getenv("MINIANDROID_R414_TRACE") != nullptr) {
                        static thread_local uint64_t r414_dbg_n = 0;
                        if (r414_dbg_n < 40) {
                            ++r414_dbg_n;
                            std::cerr << "[R414-PROBE] field "
                                      << field_res.class_descriptor << "."
                                      << field_res.field_name << " recv_cls="
                                      << r414_cls << " dex_defined="
                                      << (class_info_index_.count(r414_cls) > 0)
                                      << " caller=" << current_class_ << "."
                                      << current_method_ << " pc=" << pc
                                      << std::endl;
                        }
                    }
                    // S134 F-NEW-160 LAW FIX: the initializer scan must read
                    // the FIELD'S DECLARING CLASS only, and the initializer
                    // type must MATCH the declared field type. The previous
                    // receiver-chain walk matched by NAME alone, so an
                    // unrelated same-named field of a superclass leaked its
                    // initializer into this read (solitaire 71: `e.m`
                    // (delegate, no initializer) picked up classes.c's
                    // `m = new b.b()` Handler → the Handler answered as the
                    // AppCompat delegate → Window null → boot death — the
                    // exact name-aliasing family this law closes).
                    // ART law: a field initializer belongs to the class that
                    // DECLARES the field; identity is (class, name, type).
                    if (!field_res.class_descriptor.empty() &&
                        field_res.class_descriptor[0] == 'L' &&
                        !field_res.field_name.empty()) {
                    {
                        std::string walk = field_res.class_descriptor;
                        scan_init_field_defaults(walk);
                        auto fm = init_field_defaults_.find(walk);
                        if (fm != init_field_defaults_.end()) {
                            auto ft = fm->second.find(field_res.field_name);
                            if (ft != fm->second.end() && !ft->second.empty() &&
                                ft->second == field_res.field_type) {
                                // F-NEW-274 constructor-contract gate: fabricate
                                // ONLY when the initializer type has a ()V ctor
                                // (or is framework-owned). Otherwise the honest
                                // ART default (null) flows and the app's own
                                // null-handling runs.
                                if (!class_has_no_arg_ctor(ft->second)) {
                                    // ── [S188-W4] INNER-CLASS INITIALIZER
                                    // CAPTURE LAW ─────────────────────────
                                    // F274 honest-null fired for
                                    // Material/RecyclerView
                                    // RecyclerViewAccessibilityDelegate
                                    // (tranquilstopwatch + solitaire census):
                                    // field Ls1/m1;.e : Ls1/l1; — l1 is the
                                    // INNER class whose ONLY ctor is
                                    // <init>(Ls1/m1;)V (outer-this capture,
                                    // javac lowers `this.new Inner()` to
                                    // exactly that). ART runs the REAL ctor
                                    // with the receiver as the outer
                                    // argument. Fabricate the same way: run
                                    // the REAL DEX ctor; fall back to honest
                                    // null only when no such capture-ctor
                                    // exists or it fails.
                                    bool inner_made = false;
                                    DalvikValue inner_dv;
                                    if (ft->second.size() > 2 &&
                                        ft->second.front() == 'L') {
                                        auto ccit =
                                            class_info_index_.find(ft->second);
                                        if (ccit != class_info_index_.end() &&
                                            ccit->second <
                                                dex_report_->classes.size()) {
                                            const auto& ccls =
                                                dex_report_->classes
                                                    [ccit->second];
                                            for (const auto& m :
                                                 ccls.direct_methods) {
                                                if (m.name != "<init>" ||
                                                    m.descriptor.empty() ||
                                                    m.descriptor.front() !=
                                                        '(')
                                                    continue;
                                                // capture-ctor shape:
                                                // (L<declaring>;)V where
                                                // declaring == walk
                                                std::string want =
                                                    "(L" + walk.substr(1);
                                                if (m.descriptor != want + ")V")
                                                    continue;
                                                uint32_t oid = heap_.allocate(
                                                    ft->second, pc, 0);
                                                if (oid == 0) break;
                                                DalvikValue self_v =
                                                    DalvikValue::make_object(
                                                        oid, ft->second);
                                                DalvikValue outer_v =
                                                    obj_ref;  // receiver IS
                                                              // the outer
                                                              // this
                                                DalvikValue ctor_ret;
                                                DalvikExecutionResult ctor_res;
                                                std::vector<DalvikValue>
                                                    ctor_args{self_v, outer_v};
                                                inner_made =
                                                    try_recursive_invoke(
                                                        ft->second, "<init>",
                                                        ctor_args, ctor_ret,
                                                        ctor_res,
                                                        m.descriptor);
                                                if (inner_made) {
                                                    inner_dv = self_v;
                                                    break;
                                                }
                                            }
                                        }
                                    }
                                    if (inner_made) {
                                        heap_.set_object_field(
                                            obj_ref.object_id,
                                            s134_dex_field_key(
                                                resolved_field_declarer(
                                                    field_res.class_descriptor,
                                                    field_res.field_name),
                                                field_res.field_name, true),
                                            inner_dv);
                                        heap_.set_object_field(
                                            obj_ref.object_id,
                                            field_res.field_name, inner_dv);
                                        std::cerr << "[S188-W4-INNER-INIT] "
                                                  << walk << "."
                                                  << field_res.field_name
                                                  << " = new " << ft->second
                                                  << "(this) REAL ctor obj#"
                                                  << inner_dv.object_id
                                                  << " caller="
                                                  << current_class_ << "."
                                                  << current_method_
                                                  << " pc=" << pc << std::endl;
                                        result_value = inner_dv;
                                        field_val = inner_dv;
                                    } else {
                                    static thread_local uint64_t f274_n = 0;
                                    if (f274_n < 16) {
                                        ++f274_n;
                                        std::cerr << "[F274-CTORGATE] "
                                                  << walk << "."
                                                  << field_res.field_name
                                                  << " initializer type "
                                                  << ft->second
                                                  << " has no ()V ctor -> honest null (recv="
                                                  << r414_cls << " caller="
                                                  << current_class_ << "."
                                                  << current_method_
                                                  << " pc=" << pc << ")"
                                                  << std::endl;
                                    }
                                    }
                                } else {
                                    DalvikValue dv =
                                        materialize_init_default(ft->second);
                                    if (dv.type == DalvikType::OBJECT_REF &&
                                        dv.object_id != 0) {
                                        // S134 F-NEW-160: store under the
                                        // QUALIFIED identity (declaring class
                                        // + name) so the next qualified read
                                        // re-hits the SAME object (identity
                                        // stability); bare mirror for legacy
                                        // C++ readers.
                                        heap_.set_object_field(
                                            obj_ref.object_id,
                                            s134_dex_field_key(
                                                resolved_field_declarer(
                                                    field_res.class_descriptor,
                                                    field_res.field_name),
                                                field_res.field_name, true),
                                            dv);
                                        heap_.set_object_field(
                                            obj_ref.object_id,
                                            field_res.field_name, dv);
                                        static thread_local uint64_t r414_n = 0;
                                        if (r414_n < 24) {
                                            ++r414_n;
                                            std::cerr << "[R414-INIT-DEFAULT] "
                                                      << walk << "."
                                                      << field_res.field_name
                                                      << " obj#"
                                                      << obj_ref.object_id
                                                      << " = new " << ft->second
                                                      << " (recv=" << r414_cls
                                                      << " caller="
                                                      << current_class_ << "."
                                                      << current_method_
                                                      << " pc=" << pc << ")"
                                                      << std::endl;
                                        }
                                        result_value = dv;
                                        field_val = dv;
                                    }
                                }
                            }
                        }
                    }
                    }
                }
            }
            // ── [S188-W4] FRAMEWORK OBSERVABLE INVARIANT LAW ──────────────
            // AOSP android.database.Observable: field initializer
            // `mObservers = new ArrayList<Object>()` runs for EVERY subclass
            // instance (javac inlines it into the default ctor the subclass
            // super() chain calls). Engine gap: framework superclasses have
            // no DEX body, so a Material Observable subclass (Ls1/o0; —
            // tranquilstopwatch + solitaire NavigationView chain) reached
            // `mObservers.isEmpty()` with a null list → NPE →
            // NavigationView.<init> died → app blank. AOSP invariant:
            // mObservers is NEVER null on a constructed Observable.
            if (!field_val.has_value() &&
                field_res.class_descriptor == "Landroid/database/Observable;" &&
                field_res.field_name == "mObservers" &&
                obj_ref.object_id != 0) {
                uint32_t list_oid =
                    heap_.allocate("Ljava/util/ArrayList;", pc, 0);
                if (list_oid != 0) {
                    DalvikValue dv =
                        DalvikValue::make_object(list_oid,
                                                 "Ljava/util/ArrayList;");
                    heap_.set_object_field(
                        obj_ref.object_id,
                        s134_dex_field_key(
                            resolved_field_declarer(field_res.class_descriptor,
                                                    field_res.field_name),
                            field_res.field_name, true),
                        dv);
                    heap_.set_object_field(obj_ref.object_id,
                                           field_res.field_name, dv);
                    std::cerr << "[S188-W4-OBSERVABLE] mObservers invariant "
                              << "obj#" << obj_ref.object_id
                              << " = ArrayList#" << list_oid
                              << " caller=" << current_class_ << "."
                              << current_method_ << " pc=" << pc << std::endl;
                    field_val = dv;
                }
            }
            // S72 null-field probe (env-gated, bounded, read-only): a read
            // where the heap object has NO ENTRY for the field means the
            // iput never ran (silent-lost write or skipped <init>) — the
            // engine then answers null-with-empty-desc downstream, which is
            // how dooz's trie nodes reached arraycopy(null).
            if (!field_val.has_value()) {
                static thread_local const char* nf_filter =
                    std::getenv("MINIANDROID_NULLFIELD_TRACE");
                static thread_local uint64_t nf_n = 0;
                if (nf_filter && nf_n < 30) {
                    if (std::string(nf_filter) == "*" ||
                        field_res.field_name == nf_filter) {
                        ++nf_n;
                        const HeapObject* hobj = heap_.get(obj_ref.object_id);
                        std::cerr << "[NULLFIELD] "
                                  << (hobj ? hobj->class_descriptor
                                           : field_res.class_descriptor)
                                  << "->" << field_res.field_name
                                  << " obj#" << obj_ref.object_id
                                  << " UNSET (iput never ran)"
                                  << " caller=" << current_class_ << "."
                                  << current_method_ << " pc=" << pc
                                  << std::endl;
                    }
                }
            }
            if (field_val.has_value()) {
                result_value = field_val.value();
                // ── F-065 (R-NEW-289): const-class FIELD ROUND-TRIP law ────
                // ART: java.lang.Class instances are real objects with
                // identity — a Class reference stored with iput-object and
                // read back with iget-object is the SAME reference, and is
                // NON-NULL. The engine's Class representation is CLASS_REF
                // (class_desc = referred type descriptor — the bridge law
                // FIX-M3-012 serves Class.getName/forName/getPackage on
                // exactly that form). The old blanket retag below rewrote a
                // stored CLASS_REF to OBJECT_REF while keeping object_id=0
                // (make_class stores the token in ref_id, not object_id) —
                // a pseudo-null by the is-zero law (OBJECT_REF && oid==0).
                // Every Kotlin `T::class.java` round-trip through a field
                // then failed Intrinsics.checkNotNull — real-APK hit: dooz
                // SavedStateHandlesVM creation (y.c → M1/u.a → new
                // LM1/d(jClass) → LM1/d;.a reads field a → OBJECT_REF{0}
                // → M1/i.d NPE "null cannot be cast to non-null type
                // java.lang.Class<...get-java>" → first frame died).
                // CLASS_REF now round-trips identity-verbatim like
                // OBJECT_REF/STRING_REF. No app special-casing: every
                // const-class field round-trip in every APK benefits.
                if (result_value.type != DalvikType::OBJECT_REF &&
                    result_value.type != DalvikType::NULL_REF &&
                    result_value.type != DalvikType::STRING_REF &&
                    result_value.type != DalvikType::CLASS_REF) {
                    result_value.type = DalvikType::OBJECT_REF;
                }
            }
        }
    }
    // S122 (R-NEW-414b): receiver NOT heap-backed — the in-heap law above
    // never ran. The receiver id is a VIEW NODE (e.g. the android.R.id.content
    // ContentFrameLayout node, id 800100 — chess evidence: Lg/c0;.y pc=454
    // reads the AOSP mDecorPadding Rect, gets a manufactured null, and the
    // following Rect.set NPE unwinds onCreate -> blank screen). Same honest
    // initializer default, answered from the field's DECLARING class and
    // cached per (node id, field) so identity stays stable across reads.
    if (result_value.type == DalvikType::NULL_REF &&
        obj_ref.type == DalvikType::OBJECT_REF && obj_ref.object_id != 0 &&
        !heap_.has_object(obj_ref.object_id) && !field_res.field_name.empty() &&
        !field_res.class_descriptor.empty() &&
        field_res.class_descriptor[0] == 'L') {
        auto nfkey = std::make_pair(obj_ref.object_id, field_res.field_name);
        auto cached = node_field_defaults_.find(nfkey);
        if (cached != node_field_defaults_.end()) {
            result_value =
                DalvikValue::make_object(cached->second, field_res.class_descriptor);
        } else {
            std::string walk = field_res.class_descriptor;
            for (int hop = 0; hop < 8 && !walk.empty(); ++hop) {
                scan_init_field_defaults(walk);
                auto fm = init_field_defaults_.find(walk);
                if (fm != init_field_defaults_.end()) {
                    auto ft = fm->second.find(field_res.field_name);
                    if (ft != fm->second.end() && !ft->second.empty()) {
                        // F-NEW-274 constructor-contract gate (same law as the
                        // in-heap arm): a class with no ()V constructor has no
                        // legal zero-state instance — answer the honest ART
                        // default (null) instead of a fabricated object.
                        if (!class_has_no_arg_ctor(ft->second)) {
                            static thread_local uint64_t f274b_n = 0;
                            if (f274b_n < 16) {
                                ++f274b_n;
                                std::cerr << "[F274-CTORGATE-B] field "
                                          << field_res.class_descriptor << "."
                                          << field_res.field_name
                                          << " initializer type " << ft->second
                                          << " has no ()V ctor -> honest null"
                                          << std::endl;
                            }
                            break;
                        }
                        DalvikValue dv = materialize_init_default(ft->second);
                        if (dv.type == DalvikType::OBJECT_REF &&
                            dv.object_id != 0) {
                            node_field_defaults_[nfkey] = dv.object_id;
                            static thread_local uint64_t r414b_n = 0;
                            if (r414b_n < 16) {
                                ++r414b_n;
                                std::cerr << "[R414B-NOHEAP] field "
                                          << field_res.class_descriptor << "."
                                          << field_res.field_name
                                          << " node#" << obj_ref.object_id
                                          << " = new " << ft->second
                                          << " (caller=" << current_class_
                                          << "." << current_method_
                                          << " pc=" << pc << ")"
                                          << std::endl;
                            }
                            result_value = dv;
                        }
                        break;
                    }
                }
                auto sit = class_to_superclass_.find(walk);
                walk = (sit != class_to_superclass_.end()) ? sit->second : "";
            }
        }
    }
    // ── F-NEW-271 LAW DIAG (read-side twin, env-gated MINIANDROID_FIELD_LAW_DIAG,
    // bounded, read-only). A field read answering a STRING_REF while the
    // field's declared type (from field_ids) is NOT Ljava/lang/String is an
    // alien-typed value — the exact face F-271 recorded on Lnb0.j (STRING_REF
    // in a :Lqb0 slot). Dump the read-key identity (qualified vs bare via the
    // resolved declarer), the receiver's heap class, and the receiver's FULL
    // field map (all slots, keys, types, bounded contents) so the polluted
    // slot and the value's origin are both visible. The write-side twin lives
    // in execute_iput_object and catches the alien store in the act.
    // S156-P4 (CONT-42 zero-cost-gate law): static-cached — was a raw
    // std::getenv per read.
    static const bool f271_law_diag = std::getenv("MINIANDROID_FIELD_LAW_DIAG") != nullptr;
    if (f271_law_diag &&
        result_value.type == DalvikType::STRING_REF &&
        field_res.field_type != "Ljava/lang/String;") {
        static thread_local uint64_t f271_rn = 0;
        if (f271_rn < 40) {
            ++f271_rn;
            std::cerr << "[F271-READ] " << current_class_ << "."
                      << current_method_ << " pc=" << pc
                      << " field=" << field_res.class_descriptor << "."
                      << field_res.field_name << " : " << field_res.field_type
                      << " answered STRING_REF len="
                      << result_value.string_val.size()
                      << " str=\"" << result_value.string_val.substr(0, 48)
                      << "\"";
            if (obj_ref.type == DalvikType::OBJECT_REF) {
                const std::string f271_decl = resolved_field_declarer(
                    field_res.class_descriptor, field_res.field_name);
                std::cerr << " recv#" << obj_ref.object_id
                          << " recv_reg_cls=" << obj_ref.class_desc
                          << " declarer=" << f271_decl
                          << " dex_defined="
                          << (is_dex_defined_class(f271_decl) ? 1 : 0)
                          << " readkey="
                          << s134_dex_field_key(
                                 f271_decl, field_res.field_name,
                                 is_dex_defined_class(f271_decl));
                if (heap_.has_object(obj_ref.object_id)) {
                    const HeapObject* f271_ho = heap_.get(obj_ref.object_id);
                    if (f271_ho) {
                        std::cerr << " heap_cls=" << f271_ho->class_descriptor
                                  << " fields[" << f271_ho->fields.size()
                                  << "]:";
                        int f271_nf = 0;
                        for (const auto& [fk, fv] : f271_ho->fields) {
                            if (f271_nf++ >= 20) {
                                std::cerr << " ...";
                                break;
                            }
                            std::cerr << " " << fk << "=t"
                                      << static_cast<int>(fv.type) << "/o"
                                      << fv.object_id;
                            if (fv.type == DalvikType::STRING_REF)
                                std::cerr << "(\""
                                          << fv.string_val.substr(0, 32)
                                          << "\")";
                        }
                    }
                } else {
                    std::cerr << " recv-not-in-heap";
                }
            }
            std::cerr << std::endl;
        }
    }
    // EXP-042 Phase 2: if obj_ref is not OBJECT_REF (uninit, null, primitive),
    // just return null. Previously this returned false and caused infinite
    // loops in ComponentActivity.onCreate, UserConfig.isClientActivated,
    // FragmentActivity.onCreate, etc.

    // EXP-055: Debug — log iget-object result for isClientActivated investigation.
    // R-NEW-539 (CONT-36): env-gated behind MINIANDROID_TG_DEBUG (the
    // telegram hot-path iget stream; ungated fprintf burn, bounded-logging
    // law). Identical output when the flag is set.
    {
        static thread_local const bool tg_dbg2 = diag_env("MINIANDROID_TG_DEBUG");
    if (tg_dbg2 &&
        current_class_.find("UserConfig") != std::string::npos &&
        (current_method_ == "isClientActivated" || current_method_ == "getCurrentUser")) {
        std::cerr << "[IGET-OBJ-DBG] " << current_class_ << "." << current_method_
                  << " pc=" << pc
                  << " field=" << field_res.class_descriptor << "." << field_res.field_name
                  << " obj_reg_type=" << static_cast<int>(obj_ref.type)
                  << " obj_id=" << obj_ref.object_id
                  << " result_type=" << static_cast<int>(result_value.type)
                  << " result_obj=" << result_value.object_id
                  << std::endl;
    }
    }

    // EXP-071 Phase 6 debug: Trace iget-object for TL_nearestDc.country
    // to understand why setCountry receives null for the country argument.
    // R-NEW-539 (CONT-36): env-gated (MINIANDROID_TG_DEBUG) — bounded-logging
    // law; the country-field stream is telegram hot-path.
    {
        static thread_local const bool tg_dbg4 = diag_env("MINIANDROID_TG_DEBUG");
    if (tg_dbg4 &&
        field_res.field_name == "country" &&
        field_res.class_descriptor.find("nearestDc") != std::string::npos) {
        std::cerr << "[EXP071-IGET-COUNTRY] " << current_class_ << "." << current_method_
                  << " pc=" << pc
                  << " field=" << field_res.class_descriptor << "." << field_res.field_name
                  << " obj_reg_type=" << static_cast<int>(obj_ref.type)
                  << " obj_id=" << obj_ref.object_id
                  << " result_type=" << static_cast<int>(result_value.type);
        if (result_value.type == DalvikType::STRING_REF) {
            std::cerr << " str=\"" << result_value.string_val << "\"";
        }
        std::cerr << std::endl;
    }
    }

    // EXP-059: Debug — log iget-object in addFragmentToStack
    // R-NEW-539 (CONT-36): env-gated (MINIANDROID_TG_DEBUG).
    {
        static thread_local const bool tg_dbg5 = diag_env("MINIANDROID_TG_DEBUG");
    if (tg_dbg5 && current_method_ == "addFragmentToStack" &&
        current_class_.find("ActionBarLayout") != std::string::npos) {
        std::cerr << "[EXP059-IGET] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " dest=v" << (int)dest_reg
                  << " obj=v" << (int)obj_reg
                  << " field=" << field_res.class_descriptor << "." << field_res.field_name
                  << " obj_type=" << static_cast<int>(obj_ref.type)
                  << " obj_id=" << obj_ref.object_id
                  << " result_type=" << static_cast<int>(result_value.type)
                  << " result_obj=" << result_value.object_id
                  << std::endl;
    }
    }

    // EXP-060: Debug — log iget-object for parentLayout in presentFragment
    // R-NEW-539 (CONT-36): env-gated (MINIANDROID_TG_DEBUG).
    {
        static thread_local const bool tg_dbg6 = diag_env("MINIANDROID_TG_DEBUG");
    if (tg_dbg6 && field_res.resolved &&
        field_res.field_name == "parentLayout" &&
        current_method_ == "presentFragment") {
        std::cerr << "[EXP060-IGET] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " obj=v" << (int)obj_reg
                  << " field=" << field_res.class_descriptor << "." << field_res.field_name
                  << " obj_type=" << static_cast<int>(obj_ref.type)
                  << " obj_id=" << obj_ref.object_id
                  << " result_type=" << static_cast<int>(result_value.type)
                  << " result_obj=" << result_value.object_id
                  << std::endl;
    }
    }

    set_register(dest_reg, result_value);
    
    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.operands.push_back({"v" + std::to_string(dest_reg), "destination"});
    trace.operands.push_back({"v" + std::to_string(obj_reg), "object"});
    trace.operands.push_back({"field", field_res.class_descriptor + "." + field_res.field_name});
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});
    }
    
    pc_ = pc + 2;  // 22c format = 2 code units
    return true;
}

bool DalvikExecutionEngine::execute_iput(uint32_t pc, InstructionTrace& trace) {
    // Format: 22c iput vA, vB, field@CCCC (2 code units)
    // EXP-042 Phase 2 FIX: never return false — always advance pc_.
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }

    uint16_t instr = bytecode_[pc];
    uint8_t src_reg = (instr >> 8) & 0xF;
    uint8_t obj_reg = (instr >> 12) & 0xF;
    uint16_t field_idx = bytecode_[pc + 1];

    // R-NEW-467: memoized resolution (same value the fresh walk answers).
    const DalvikExecutionEngine::FieldMemo& field_memo_iput
        = resolved_field_memo(field_idx);
    const FieldResolution& field_res = field_memo_iput.res;
    DalvikValue src_val = get_register(src_reg);
    DalvikValue obj_ref = get_register(obj_reg);

    // S135 F-NEW-365 (S57 wave, merge complement): ART null-receiver FIELD
    // law for the WRITE forms. F-NEW-268d (CONT-18g) closed iget/iget-object;
    // the iput family kept the EXP-042 silent-drop — a null receiver wrote
    // nowhere and the body kept running with this=NULL (same disease family
    // F-141/F-268d eliminated for reads). ART throws NPE at the write site
    // ("Attempt to write to field ... on a null object reference").
    if (field_res.resolved && f141_is_null_receiver(obj_ref)) {
        raise_synthetic_exception(
            "Ljava/lang/NullPointerException;",
            "Attempt to write to field '" + field_res.class_descriptor + "." +
                field_res.field_name + ":" + field_res.field_type +
                "' on a null object reference",
            "iput-null-recv");
        return true;  /* pc_ set by raise (catch handler) or frame unwind */
    }

    // ── S211 (DIAG-ONLY, env-gated MINIANDROID_S211_SEGTRACE): dooz zombie
    // probe — every iput into a Lbw0; (kotlinx Segment family) field logs
    // (obj#, field, written value, caller, pc). The initializer `.f` writes
    // the mask `c` — the writer identity + value answers whether c is
    // capacity-consistent (7 -> Object[7]) or garbage-sourced.
    {
        static const bool s211w_on = diag_env("MINIANDROID_S211_SEGTRACE");
        if (s211w_on && field_res.resolved &&
            field_res.class_descriptor == "Lbw0;") {
            static thread_local uint64_t s211_wn = 0;
            if (s211_wn++ < 400) {
                uint32_t s211_recv =
                    (obj_ref.type == DalvikType::OBJECT_REF)
                        ? obj_ref.object_id : 0;
                std::cerr << "[S211-IPUT] Lbw0;." << field_res.field_name
                          << " obj#" << s211_recv
                          << " val=" << dalvik_value_to_string(src_val)
                          << " caller=" << current_class_ << "."
                          << current_method_ << " pc=" << pc << std::endl;
            }
        }
    }

    // ── S221b (DIAG-ONLY, env-gated MINIANDROID_S221_DENSTRACE): the WRITE
    // twin of S221-ZERODENS — every iput of 0.0f into Lmb1; fields (the
    // InlineDensity value class: a=density b=fontScale) logs the WRITER
    // chain. Upstream constructs Unspecified ONLY from the cache density
    // setter's null path (`value?.let{...} ?: InlineDensity.Unspecified`);
    // the writer identity decides the fix surface (runtime delivery vs
    // app-side substitution-null propagation).
    {
        static const bool s221w_on = diag_env("MINIANDROID_S221_DENSTRACE");
        if (s221w_on && field_res.resolved &&
            field_res.class_descriptor == "Lmb1;" &&
            src_val.type == DalvikType::FLOAT32 &&
            src_val.float_val == 0.0f) {
            static thread_local uint64_t s221w_n = 0;
            if (s221w_n++ < 40) {
                uint32_t s221w_recv =
                    (obj_ref.type == DalvikType::OBJECT_REF)
                        ? obj_ref.object_id : 0;
                std::cerr << "[S221b-ZEROW] Lmb1;." << field_res.field_name
                          << " obj#" << s221w_recv
                          << " caller=" << current_class_ << "."
                          << current_method_ << " pc=" << pc;
                auto s221w_frames = call_stack_.snapshot_top_first();
                for (size_t fi = 0;
                     fi < s221w_frames.size() && fi < 6; ++fi)
                    std::cerr << " <" << s221w_frames[fi].first << "."
                              << s221w_frames[fi].second << ">";
                std::cerr << std::endl;
            }
        }
    }

    // ── CONT-47 D8 (DIAG-ONLY, env-gated): place-descent witness — every
    // write to Lel0;.e (the D7 placecheck showed e=F on all 44 inserted
    // chain nodes at draw: whatever sets e=T = the place walk). Print
    // receiver + written value + caller so the descent's reach is visible.
    {
        static const bool d8_on = diag_env("MINIANDROID_D8_EWRITE");
        if (d8_on && field_res.resolved &&
            field_res.class_descriptor == "Lel0;" &&
            field_res.field_name == "e") {
            static thread_local uint64_t d8_wn = 0;
            if (d8_wn < 64) {
                ++d8_wn;
                uint32_t d8_recv =
                    (obj_ref.type == DalvikType::OBJECT_REF)
                        ? obj_ref.object_id : 0;
                std::string d8_v = "?";
                if (src_val.type == DalvikType::BOOLEAN)
                    d8_v = src_val.bool_val ? "T" : "F";
                else if (src_val.type == DalvikType::INT32)
                    d8_v = src_val.int_val ? "T" : "F";
                std::cerr << "[D8-EWRITE] w#" << d8_wn
                          << " recv=o" << d8_recv << " e=" << d8_v
                          << " caller=" << current_class_ << "."
                          << current_method_ << std::endl;
            }
        }
    }

    // ── TRAIN-64 (T64, DIAG-ONLY, env-gated MINIANDROID_T64_CHANGE_TRACE):
    // pointer-change field WRITE law. Lu71; = PointerInputChange (R8):
    // d=pressed, h=previousPressed, o=isConsumed. The MotionEvent→
    // PointerInputChange adapter writes these during the touch dispatch;
    // waitForUpOrCancellation's fastAll{changedToUp} (= !d && h) dies when
    // the UP change never gets h=true. Log every boolean write — pairs
    // with the [T64-R] read probe to pin the exact wrong field.
    {
        static const bool t64w_on = diag_env("MINIANDROID_T64_CHANGE_TRACE");
        if (t64w_on && touch_dispatch_active_ && field_res.resolved &&
            field_res.class_descriptor == "Lu71;") {
            static const char* t64w_bools[] = {"d", "h", "o", "p"};
            for (const char* t64wb : t64w_bools) {
                if (field_res.field_name == t64wb) {
                    static thread_local uint64_t t64w_n = 0;
                    if (t64w_n++ < 400) {
                        uint32_t t64w_recv =
                            (obj_ref.type == DalvikType::OBJECT_REF)
                                ? obj_ref.object_id : 0;
                        std::cerr << "[T64-W] Lu71;." << field_res.field_name
                                  << " obj#" << t64w_recv << " = "
                                  << dalvik_value_to_string(src_val)
                                  << " caller=" << current_class_ << "."
                                  << current_method_ << std::endl;
                    }
                    break;
                }
            }
        }
        // T64-QW: the q-chain write (who links a change to another).
        if (t64w_on && touch_dispatch_active_ && field_res.resolved &&
            field_res.class_descriptor == "Lu71;" &&
            field_res.field_name == "q") {
            static thread_local uint64_t t64qw_n = 0;
            if (t64qw_n++ < 64) {
                uint32_t t64qw_recv =
                    (obj_ref.type == DalvikType::OBJECT_REF)
                        ? obj_ref.object_id : 0;
                std::cerr << "[T64-QW] Lu71;.q obj#" << t64qw_recv << " = "
                          << dalvik_value_to_string(src_val)
                          << " caller=" << current_class_ << "."
                          << current_method_ << std::endl;
            }
        }
        // T64-C2: the RAW PointerInputEventData isInitiallyConsumed write
        // (Lw71;.g) — feeds Las0;.t's change ctor slot 14; the DOWN was
        // born with 1 (should be 0) which kills awaitFirstDown's
        // changedToDown() (!isConsumed) — log the writer and the value.
        if (t64w_on && touch_dispatch_active_ && field_res.resolved &&
            field_res.class_descriptor == "Lw71;" &&
            field_res.field_name == "g") {
            static thread_local uint64_t t64g_n = 0;
            if (t64g_n++ < 64) {
                uint32_t t64g_recv =
                    (obj_ref.type == DalvikType::OBJECT_REF)
                        ? obj_ref.object_id : 0;
                std::cerr << "[T64-G] Lw71;.g obj#" << t64g_recv << " = "
                          << dalvik_value_to_string(src_val)
                          << " caller=" << current_class_ << "."
                          << current_method_ << std::endl;
            }
        }
    }

    // ── F-NEW-406 (CONT-99 T1): DEX float-bit register law at the FIELD-
    // STORE boundary. DEX float registers carry raw IEEE-754 BITS in int
    // registers — `const/high16 v0, 0x3f800000` IS the literal float 1.0f
    // and no conversion instruction runs along that path (int-to-float is
    // only emitted when the source was a genuine int). A store into a
    // declared-float field must therefore BIT-CAST the register bits into
    // the FLOAT32 value; the old raw store left the field as INT32 bits,
    // and every float reader saw the bit pattern VALUE-cast (c99lay probe:
    // LinearLayout.LayoutParams.weight read 1.06535e9 instead of 1.0f —
    // the 0px+weight children collapsed to width 0 / full-width garbage).
    // Symmetric law for declared-double fields (wide register = INT64
    // bits). Genuine-int stores into float fields do not exist in DEX
    // (the verifier requires float registers for F fields).
    if (field_res.resolved && field_res.field_type == "F" &&
        src_val.type == DalvikType::INT32) {
        float fbits = 0.0f;
        std::memcpy(&fbits, &src_val.int_val, sizeof(fbits));
        src_val.type = DalvikType::FLOAT32;
        src_val.float_val = fbits;
    } else if (field_res.resolved && field_res.field_type == "D" &&
               src_val.type == DalvikType::INT64) {
        double dbits = 0.0;
        std::memcpy(&dbits, &src_val.long_val, sizeof(dbits));
        src_val.type = DalvikType::FLOAT64;
        src_val.double_val = dbits;
    }
    if (field_res.resolved && obj_ref.type == DalvikType::OBJECT_REF &&
        heap_.has_object(obj_ref.object_id)) {
        // S134 F-NEW-160: dual write — qualified primary key (declaring
        // class + name) + bare legacy mirror (C++ shadow readers).
        // F-NEW-321 (CONT-50): the mirror write is RAW (exact bare key, no
        // F-NEW-251 redirect) — the redirect re-resolves the bare name
        // against the receiver's most-derived declarer, so a SUPERCLASS
        // write's mirror landed in the SUBCLASS's shadowed qualified slot
        // (solitaire 71: ay$a.<init> mObservable mirror clobbered c$b.a =
        // the outer presenter; probe fnew320 N2 PRE face). The mirror is a
        // legacy channel, not a second identity resolution.
        {
            // F-NEW-325: true-declarer keying — a framework-owned field
            // (no DEX declarer; the bare/raw mirror IS the slot) stays
            // bare even when the REF class is DEX-defined; a real DEX
            // declarer keeps the qualified slot + the raw bare mirror
            // (F-NEW-321 law unchanged).
            const std::string& s134_decl = field_memo_iput.s134_decl;
            if (!is_dex_defined_class(s134_decl)) {
                heap_.set_object_field(obj_ref.object_id, field_res.field_name,
                                       src_val);
            } else {
                heap_.set_object_field(obj_ref.object_id,
                    s134_dex_field_key(s134_decl, field_res.field_name, true),
                    src_val);
                heap_.set_object_field_raw(obj_ref.object_id,
                                           field_res.field_name, src_val);
            }
        }
        // ── TRAIN-68 (T68-JOBPUT): the pointerInputJob WRITE side — the lazy
        // launch stores the Job; log every write with receiver identity.
        {
            static const bool t68p_on = diag_env("MINIANDROID_T68_NODE_TRACE");
            if (t68p_on && field_res.class_descriptor == "Lor1;" &&
                field_res.field_name == "v") {
                static thread_local uint64_t t68p_n = 0;
                if (t68p_n++ < 120) {
                    std::cerr << "[T68-JOBPUT] Lor1;.v obj#"
                              << obj_ref.object_id << " val="
                              << dalvik_value_to_string(src_val)
                              << " caller=" << current_class_ << "."
                              << current_method_ << " pc=" << pc_ << std::endl;
                }
            }
        }
        // ── TRAIN-67 (T67-IPUT): the label WRITE side — the iput before the
        // suspend must land on the SAME object the resume reads. Log writes
        // to the machine's label (l) and spill (k) slots with obj identity.
        {
            static const bool t67w_on = diag_env("MINIANDROID_T67_LABEL_TRACE");
            if (t67w_on && (field_res.class_descriptor == "Lss1;" ||
                            field_res.class_descriptor == "Lxs1;" ||
                            field_res.class_descriptor == "Li6;")) {
                static thread_local uint64_t t67w_n = 0;
                if (t67w_n++ < 600) {
                    std::cerr << "[T67-IPUT] Lss1;." << field_res.field_name
                              << " obj#" << obj_ref.object_id
                              << " val=" << dalvik_value_to_string(src_val)
                              << " caller=" << current_class_ << "."
                              << current_method_ << " pc=" << pc << std::endl;
                }
            }
        }
        // M3 FIELD-TRACE (AG diagnostic): env-gated field-store value trace.
        // NOTE: render via dalvik_value_to_string — printing .long_val on an
        // INT32 union read shows stale upper bytes as false corruption.
        if (field_trace_filter_set() &&
            field_trace_active(field_res.field_name.c_str(),
                               (current_class_ + "." + current_method_).c_str(),
                               field_res.class_descriptor.c_str())) {
            std::cerr << "[FIELD-TRACE] put " << current_class_ << "."
                      << current_method_ << " "
                      << field_res.class_descriptor << "."
                      << field_res.field_name
                      << " obj#" << obj_ref.object_id
                      << " value=" << dalvik_value_to_string(src_val) << std::endl;
        }
        // M3-DIAG (temporary): long field writes — Alarm expiresMs math.
        static thread_local uint64_t m3w = 0;
        if (src_val.type == DalvikType::INT64 && m3w < 30) {
            m3w++;
            std::cerr << "[M3-LONG-PUT] field="
                      << field_res.class_descriptor << "."
                      << field_res.field_name
                      << " caller=" << current_class_ << "." << current_method_
                      << " value=" << src_val.long_val << std::endl;
        }
    }
    // EXP-042 Phase 2: on any failure path, just advance pc_ — never spin.

    // EXP-092+ INSTRUMENTATION: Log every write to PhoneView.countryState
    // to trace the root cause of the onNextPressed needShowAlert branch.
    // The field is field@33152 in classes4.dex, declared on
    // Lorg/telegram/ui/LoginActivity$PhoneView; as `int countryState`.
    // Values observed:
    //   0 = set by setCountry (after auto-detection from getNearestDc response)
    //   1 = set by <init> and afterTextChanged (default / user-typed-but-no-match)
    //   2 = set by afterTextChanged when country code matches (COUNTRY_SELECTED)
    if (field_res.resolved &&
        field_res.field_name == "countryState" &&
        field_res.class_descriptor.find("PhoneView") != std::string::npos) {
        int32_t new_val = 0;
        if (src_val.type == DalvikType::INT32 || src_val.type == DalvikType::BOOLEAN) {
            new_val = src_val.int_val;
        }
        std::cerr << "[EXP092-COUNTRYSTATE-WRITE] pc=" << pc
                  << " caller=" << current_class_ << "." << current_method_
                  << " obj_id=" << (obj_ref.type == DalvikType::OBJECT_REF ? obj_ref.object_id : 0)
                  << " new_value=" << new_val
                  << " src_type=" << static_cast<int>(src_val.type)
                  << std::endl;
    }

    // EXP-092+ PHASE 1: Log every write to LoginActivity.currentViewNum
    // (field@33189) to trace the page transition. This is the field that
    // tracks which page (PhoneView, SmsView, etc.) is currently active.
    if (field_res.resolved &&
        field_res.field_name == "currentViewNum" &&
        field_res.class_descriptor.find("LoginActivity;") != std::string::npos &&
        field_res.class_descriptor.find("PhoneView") == std::string::npos) {
        int32_t new_val = 0;
        if (src_val.type == DalvikType::INT32 || src_val.type == DalvikType::BOOLEAN) {
            new_val = src_val.int_val;
        }
        std::cerr << "[EXP092-CURRENTVIEWNUM-WRITE] pc=" << pc
                  << " caller=" << current_class_ << "." << current_method_
                  << " obj_id=" << (obj_ref.type == DalvikType::OBJECT_REF ? obj_ref.object_id : 0)
                  << " new_value=" << new_val
                  << " src_type=" << static_cast<int>(src_val.type)
                  << std::endl;
    }

    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.operands.push_back({"v" + std::to_string(src_reg), "source"});
    trace.operands.push_back({"v" + std::to_string(obj_reg), "object"});
    trace.operands.push_back({"field", field_res.class_descriptor + "." + field_res.field_name});
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});
    }

    pc_ = pc + 2;
    return true;
}

bool DalvikExecutionEngine::execute_iput_object(uint32_t pc, InstructionTrace& trace) {
    // Format: 22c iput-object vA, vB, field@CCCC (2 code units)
    // EXP-042 Phase 2 FIX: never return false — always advance pc_.
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }

    // F-NEW-282 (store side): a CLASS_REF source value written through
    // iput-object must land as its heap-backed Class token (F-103 identity
    // map), not as a raw class-typed register value — raw CLASS_REF does
    // not survive the frame machinery (see the F-NEW-282 law comment in
    // execute_method_internal) and consumers read the field back as
    // null/unset (oracle: ClassReference.jClass → getJClass/equals/
    // isInstance/getQualifiedName all null). Same generic law as the
    // argument-boundary materialization; no app knowledge.

    uint16_t instr = bytecode_[pc];
    uint8_t src_reg = (instr >> 8) & 0xF;
    uint8_t obj_reg = (instr >> 12) & 0xF;
    uint16_t field_idx = bytecode_[pc + 1];

    // R-NEW-467: memoized resolution (same value the fresh walk answers).
    const DalvikExecutionEngine::FieldMemo& field_memo_iputo
        = resolved_field_memo(field_idx);
    const FieldResolution& field_res = field_memo_iputo.res;
    DalvikValue src_val = get_register(src_reg);
    // F-NEW-282 (store side) — materialize now that src_val is bound.
    if (src_val.type == DalvikType::CLASS_REF && !src_val.class_desc.empty()) {
        auto f282_it = class_token_ids_.find(src_val.class_desc);
        uint32_t f282_token = 0;
        if (f282_it != class_token_ids_.end()) {
            f282_token = f282_it->second;
        } else {
            f282_token = heap_.allocate("Ljava/lang/Class;", pc_, 0);
            heap_.set_object_field(f282_token, "__referent_desc",
                                   DalvikValue::make_string(src_val.class_desc, 0));
            class_token_ids_.emplace(src_val.class_desc, f282_token);
        }
        src_val = DalvikValue::make_object(f282_token, "Ljava/lang/Class;");
    }
    DalvikValue obj_ref = get_register(obj_reg);
    // ── TRAIN-68 (T68-JOBPUT-OBJ): the pointerInputJob store is an
    // IPUT-OBJECT (Lor1;.v:Lkp1;) — log the write with receiver identity.
    {
        static const bool t68po_on = diag_env("MINIANDROID_T68_NODE_TRACE");
        if (t68po_on && field_res.class_descriptor == "Lor1;" &&
            field_res.field_name == "v") {
            static thread_local uint64_t t68po_n = 0;
            if (t68po_n++ < 120)
                std::cerr << "[T68-JOBPUT-OBJ] Lor1;.v obj#"
                          << (obj_ref.type == DalvikType::OBJECT_REF
                                  ? obj_ref.object_id : 0)
                          << " val="
                          << (src_val.type == DalvikType::OBJECT_REF
                                  ? ("obj#" + std::to_string(src_val.object_id))
                                  : dalvik_value_to_string(src_val))
                          << " caller=" << current_class_ << "."
                          << current_method_ << " pc=" << pc << std::endl;
        }
        // W5 (Coder-4) DIAG: Koin Module.includedModules store forensics.
        static const bool f566f_on =
            diag_env("MINIANDROID_F566_FIELD_DIAG");
        if (f566f_on && field_res.resolved &&
            (field_res.field_name == "includedModules" ||
             field_res.field_name == "includes")) {
            static thread_local uint64_t f566f_n = 0;
            if (f566f_n++ < 60)
                std::cerr << "[F566-IPUT] " << field_res.field_name << " obj#"
                          << (obj_ref.type == DalvikType::OBJECT_REF
                                  ? obj_ref.object_id : 0)
                          << " <- "
                          << (src_val.type == DalvikType::OBJECT_REF
                                  ? ("obj#" + std::to_string(src_val.object_id))
                                  : dalvik_value_to_string(src_val))
                          << " caller=" << current_class_ << "."
                          << current_method_ << " pc=" << pc << std::endl;
        }
    }
    // S135 F-NEW-365 (S57 wave, merge complement): ART null-receiver FIELD
    // law, iput-object form — same family as the execute_iput law above
    // (F-NEW-268d closed the reads; the writes stayed silent until now).
    if (field_res.resolved && f141_is_null_receiver(obj_ref)) {
        raise_synthetic_exception(
            "Ljava/lang/NullPointerException;",
            "Attempt to write to field '" + field_res.class_descriptor + "." +
                field_res.field_name + ":" + field_res.field_type +
                "' on a null object reference",
            "iput-null-recv");
        return true;  /* pc_ set by raise (catch handler) or frame unwind */
    }
    if (field_res.resolved && field_res.field_name == "actionBarLayout") {
        std::cerr << "[EXP058-IPUT] iput-object actionBarLayout"
                  << " src_reg=v" << (int)src_reg
                  << " src_type=" << static_cast<int>(src_val.type)
                  << " src_obj=" << src_val.object_id
                  << " obj_reg=v" << (int)obj_reg
                  << " obj_type=" << static_cast<int>(obj_ref.type)
                  << " obj_id=" << obj_ref.object_id
                  << " pc=" << pc
                  << " field_class=" << field_res.class_descriptor
                  << std::endl;
    }

    // EXP-060: Debug — log iput-object for parentLayout field.
    if (field_res.resolved && field_res.field_name == "parentLayout") {
        std::cerr << "[EXP060-IPUT] iput-object parentLayout"
                  << " src_reg=v" << (int)src_reg
                  << " src_type=" << static_cast<int>(src_val.type)
                  << " src_obj=" << src_val.object_id
                  << " obj_reg=v" << (int)obj_reg
                  << " obj_type=" << static_cast<int>(obj_ref.type)
                  << " obj_id=" << obj_ref.object_id
                  << " pc=" << pc
                  << " field_class=" << field_res.class_descriptor
                  << std::endl;
    }

    // EXP-062: Debug — log ALL iput-object in PhoneView.<init>
    if (field_res.resolved &&
        current_class_.find("PhoneView") != std::string::npos &&
        current_method_ == "<init>") {
        std::cerr << "[EXP062-IPUT] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " field=" << field_res.class_descriptor << "." << field_res.field_name
                  << " src=v" << (int)src_reg
                  << " src_type=" << static_cast<int>(src_val.type)
                  << " src_obj=" << src_val.object_id
                  << " obj=v" << (int)obj_reg
                  << " obj_type=" << static_cast<int>(obj_ref.type)
                  << " obj_id=" << obj_ref.object_id
                  << " obj_class=" << obj_ref.class_desc
                  << " stored=" << (obj_ref.type == DalvikType::OBJECT_REF && heap_.has_object(obj_ref.object_id) ? "YES" : "NO")
                  << std::endl;
    }

    // S24 frontier probe (env-gated, bounded): Navigator.state injection —
    // the single DEX writer is navigation/compose/p.a (iput l.a). If this
    // never fires (or fires on a different receiver than the one that later
    // reads getState()), the Compose NavHost chain dies with "You cannot
    // access the Navigator's state until the Navigator is attached".
    if (field_res.resolved && field_res.field_name == "a" &&
        field_res.class_descriptor == "Landroidx/navigation/l;" &&
        std::getenv("MINIANDROID_S24_TRACE") != nullptr) {
        static thread_local uint64_t s24_nav_iput = 0;
        if (s24_nav_iput < 24) {
            ++s24_nav_iput;
            std::cerr << "[S24-NAV-STATE-IPUT] pc=" << pc
                      << " recv_oid="
                      << (obj_ref.type == DalvikType::OBJECT_REF
                              ? obj_ref.object_id : 0)
                      << " recv_cls=" << obj_ref.class_desc
                      << " value_oid="
                      << (src_val.type == DalvikType::OBJECT_REF
                              ? src_val.object_id : 0)
                      << " heap_has_recv="
                      << (obj_ref.type == DalvikType::OBJECT_REF &&
                          heap_.has_object(obj_ref.object_id) ? 1 : 0)
                      << std::endl;
        }
    }

    if (field_res.resolved && obj_ref.type == DalvikType::OBJECT_REF &&
        heap_.has_object(obj_ref.object_id)) {
        // ── F-NEW-271 LAW DIAG (write-side twin, env-gated
        // MINIANDROID_FIELD_LAW_DIAG, bounded, read-only): an iput-object
        // storing a STRING_REF into a field whose declared type is not
        // Ljava/lang/String is the alien-typed store family — catch it in
        // the act with caller identity, both store keys, the receiver's
        // runtime class, and its pre-store field map.
        // S156-P4 (CONT-42 zero-cost-gate law): static-cached — was a raw
        // std::getenv per iput-object.
        static const bool f271_law_diag_w = std::getenv("MINIANDROID_FIELD_LAW_DIAG") != nullptr;
        if (f271_law_diag_w &&
            src_val.type == DalvikType::STRING_REF &&
            (field_res.field_type != "Ljava/lang/String;" ||
             src_val.string_val.empty())) {
            static thread_local uint64_t f271_wn = 0;
            if (f271_wn < 40) {
                ++f271_wn;
                std::cerr << "[F271-WRITE] " << current_class_ << "."
                          << current_method_ << " pc=" << pc
                          << " field=" << field_res.class_descriptor << "."
                          << field_res.field_name << " : "
                          << field_res.field_type
                          << " <- STRING_REF len=" << src_val.string_val.size()
                          << " str=\"" << src_val.string_val.substr(0, 48)
                          << "\" recv#" << obj_ref.object_id
                          << " recv_reg_cls=" << obj_ref.class_desc;
                {
                    const std::string f271_wdecl = resolved_field_declarer(
                        field_res.class_descriptor, field_res.field_name);
                    std::cerr << " declarer=" << f271_wdecl
                              << " qkey="
                              << s134_dex_field_key(
                                     f271_wdecl, field_res.field_name,
                                     is_dex_defined_class(f271_wdecl));
                }
                const HeapObject* f271_who = heap_.get(obj_ref.object_id);
                if (f271_who) {
                    std::cerr << " heap_cls=" << f271_who->class_descriptor
                              << " pre-fields["
                              << f271_who->fields.size() << "]:";
                    int f271_wnf = 0;
                    for (const auto& [fk, fv] : f271_who->fields) {
                        if (f271_wnf++ >= 12) {
                            std::cerr << " ...";
                            break;
                        }
                        std::cerr << " " << fk << "=t"
                                  << static_cast<int>(fv.type) << "/o"
                                  << fv.object_id;
                        if (fv.type == DalvikType::STRING_REF)
                            std::cerr << "(\""
                                      << fv.string_val.substr(0, 24)
                                      << "\")";
                    }
                }
                std::cerr << std::endl;
            }
        }
        // S134 F-NEW-160: dual write (qualified primary + bare legacy mirror).
        // F-NEW-321 (CONT-50): the mirror write is RAW — see the execute_iput
        // site for the law (a superclass write's mirror must not re-resolve
        // onto the subclass's shadowed slot; solitaire c$b.a face).
        {
            // F-NEW-325: true-declarer keying — a framework-owned field
            // (no DEX declarer; the bare/raw mirror IS the slot) stays
            // bare even when the REF class is DEX-defined; a real DEX
            // declarer keeps the qualified slot + the raw bare mirror
            // (F-NEW-321 law unchanged).
            const std::string& s134_decl = field_memo_iputo.s134_decl;
            if (!is_dex_defined_class(s134_decl)) {
                heap_.set_object_field(obj_ref.object_id, field_res.field_name,
                                       src_val);
            } else {
                heap_.set_object_field(obj_ref.object_id,
                    s134_dex_field_key(s134_decl, field_res.field_name, true),
                    src_val);
                heap_.set_object_field_raw(obj_ref.object_id,
                                           field_res.field_name, src_val);
            }
            // CONT-44 T24 (F-NEW-567 root evidence): record the compose
            // LayoutNode owner assignment. AOSP LayoutNode.insertAt
            // propagates Owner (Lel0;.r) to every inserted node via the
            // d/h writers; the second-wave insert never executes the h
            // path (runtime: Q/M/h ZERO runs), so late nodes carry NO
            // owner and V's guard skips Lt4;.z — the measure scheduler
            // (Lzs0;.r delegate.requestMeasure) is never re-armed and the
            // nodes stay unpositioned (dooz board region zero draw ops).
            // Record the most recent owner value; the V-entry repair
            // completes the propagation with exactly the value insertAt
            // would have written.
            if (field_res.class_descriptor == "Lel0;" &&
                field_res.field_name == "r" &&
                src_val.type == DalvikType::OBJECT_REF) {
                compose_owner_last_ = src_val.object_id;
            }
        }
        if (field_trace_filter_set() &&
            field_trace_active(field_res.field_name.c_str(),
                               (current_class_ + "." + current_method_).c_str(),
                               field_res.class_descriptor.c_str())) {
            std::cerr << "[FIELD-TRACE] put-obj " << current_class_ << "."
                      << current_method_ << " "
                      << field_res.class_descriptor << "." << field_res.field_name
                      << " obj#" << (obj_ref.type == DalvikType::OBJECT_REF ? obj_ref.object_id : 0)
                      << " value=" << dalvik_value_to_string(src_val) << std::endl;
        }

    } else if (field_res.resolved) {
        // S72 silent-lost-write probe (env-gated, bounded): the iput fell
        // into the legacy drop path — the write VANISHES and the field
        // later reads back as null-with-empty-desc. This is the write-side
        // twin of the [NULLFIELD] read probe (dooz trie-node evidence).
        {
            static thread_local const char* nf_filter =
                std::getenv("MINIANDROID_NULLFIELD_TRACE");
            static thread_local uint64_t nd_n = 0;
            if (nf_filter && nd_n < 30) {
                if (std::string(nf_filter) == "*" ||
                    field_res.field_name == nf_filter) {
                    ++nd_n;
                    std::cerr << "[IPUT-DROP] "
                              << field_res.class_descriptor << "."
                              << field_res.field_name
                              << " value_oid="
                              << (src_val.type == DalvikType::OBJECT_REF
                                      ? src_val.object_id : 0)
                              << " recv_type=" << static_cast<int>(obj_ref.type)
                              << " recv_oid=" << obj_ref.object_id
                              << " recv_desc=" << obj_ref.class_desc
                              << " heap_has="
                              << (obj_ref.type == DalvikType::OBJECT_REF &&
                                  heap_.has_object(obj_ref.object_id) ? 1 : 0)
                              << " caller=" << current_class_ << "."
                              << current_method_ << " pc=" << pc
                              << std::endl;
                }
            }
        }
    }
    // EXP-042 Phase 2: never return false; just advance pc_.

    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.operands.push_back({"v" + std::to_string(src_reg), "source"});
    trace.operands.push_back({"v" + std::to_string(obj_reg), "target"});
    trace.operands.push_back({"field", field_res.class_descriptor + "." + field_res.field_name});
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});
    }

    pc_ = pc + 2;
    return true;
}

// EXP-035: Static Field Operations

bool DalvikExecutionEngine::execute_sget(uint32_t pc, InstructionTrace& trace) {
    // Format: 21c sget vAA, field@BBBB (2 code units)
    // EXP-042 Phase 2 FIX: never return false on field resolution failure —
    // advance pc_ by 2 and return default 0.
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }

    uint16_t instr = bytecode_[pc];
    uint8_t dest_reg = (instr >> 8) & 0xFF;
    uint16_t field_idx = bytecode_[pc + 1];

    FieldResolution field_res = resolve_field(field_idx);
    // CONT-126: FIELD-TRACE statics coverage (sget family) — the trace tool
    // previously covered ONLY instance iget/iput, so static-field decode
    // (e.g. tictactoe's Gdx.app putstatic hunt) had no visibility. Same
    // env gate + qualified "Lcls;.field" filter semantics as the instance
    // paths. Read-only diagnostics: zero semantic change by construction.
    if (field_res.resolved &&
        field_trace_filter_set() &&
        field_trace_active(field_res.field_name.c_str(),
                           (current_class_ + "." + current_method_).c_str(),
                           field_res.class_descriptor.c_str())) {
        std::cerr << "[FIELD-TRACE] get-static " << current_class_ << "."
                  << current_method_ << " " << field_res.class_descriptor
                  << "." << field_res.field_name << std::endl;
    }
    // CONT-38 decode diag (env-gated, bounded): UNRESOLVED static-field
    // reads answer 0 silently — the theme-defaults zero face.
    if (!field_res.resolved) {
        static thread_local const bool ufs_on =
            std::getenv("MINIANDROID_CLINIT_PATH_TRACE") != nullptr;
        static thread_local uint64_t ufs_n = 0;
        if (ufs_on && ufs_n++ < 40)
            std::cerr << "[SGET-UNRESOLVED] field_idx=" << field_idx
                      << " caller=" << current_class_ << "."
                      << current_method_ << " pc=" << pc << std::endl;
    }

    // EXP-053: Ensure the class is initialized before reading its static field.
    // F-NEW-215: active use (sget) of an ERRONEOUS class raises
    // NoClassDefFoundError instead of silently reading a missing static.
    if (field_res.resolved) {
        ensure_class_initialized(field_res.class_descriptor);
        if (class_clinit_failed(field_res.class_descriptor) &&
            !clinit_exc_already_in_flight()) {  // F-NEW-395: no double-raise at the triggering use
            static std::atomic<uint64_t> f215_sget_n{0};
            if (f215_sget_n.fetch_add(1, std::memory_order_relaxed) < 8) {
                std::cerr << "[F-NEW-215] ACTIVE-USE sget class="
                          << field_res.class_descriptor << " caller="
                          << current_class_ << "." << current_method_
                          << std::endl;
            }
            throw_deferred("Ljava/lang/NoClassDefFoundError;",
                           field_res.class_descriptor +
                               " <clinit> failed previously (erroneous class)",
                           "F-NEW-215");
            pc_ = pc + 2;
            return false;
        }
    }

    DalvikValue result_value;
    result_value.type = DalvikType::INT32;
    result_value.int_val = 0;

    if (field_res.resolved) {
        std::string static_key = field_res.class_descriptor + "." + field_res.field_name;
        auto it = static_field_storage_.find(static_key);
        // R-NEW-561 (TRAIN 8): declarer-chain retry (same law as the
        // sget-object path above) — inherited statics resolve to the
        // declarer; the requesting-class key may miss while the write
        // landed under a declarer identity. On hit: answer + alias.
        if (it == static_field_storage_.end()) {
            std::string walk_cls = field_res.class_descriptor;
            for (int r561_hop = 0; r561_hop < 32; ++r561_hop) {
                auto sit = class_to_superclass_.find(walk_cls);
                if (sit == class_to_superclass_.end() || sit->second.empty())
                    break;
                walk_cls = sit->second;
                auto dit = static_field_storage_.find(
                    walk_cls + "." + field_res.field_name);
                if (dit != static_field_storage_.end()) {
                    static_field_storage_[static_key] = dit->second;
                    it = static_field_storage_.find(static_key);
                    break;
                }
            }
        }
        // CONT-38 decode diag (env-gated, bounded): the sget-WIDE color
        // statics — the actual path the painter takeOrElse chain reads.
        // S156-P4 (CONT-42 zero-cost-gate law): static-cached — was a raw
        // std::getenv per sget-wide.
        static thread_local const bool c38w_on =
            std::getenv("MINIANDROID_CLINIT_PATH_TRACE") != nullptr;
        if (c38w_on &&
            (field_res.class_descriptor == "Lzh;" ||
             field_res.class_descriptor == "Lai;" ||
             field_res.class_descriptor == "Lts0;" ||
             field_res.class_descriptor == "Lci;")) {
            static thread_local uint64_t c38s_n = 0;
            if (c38s_n++ < 8000)
                {
                    auto vit = static_field_storage_.find(static_key);
                    long long vhex = (vit != static_field_storage_.end() &&
                                      vit->second.type == DalvikType::INT64)
                                         ? vit->second.long_val : -1;
                    std::cerr << "[COLOR-SGET-W] " << static_key
                              << " hit=" << (vit != static_field_storage_.end())
                              << " val=0x" << std::hex << vhex << std::dec
                              << " caller=" << current_class_ << "."
                              << current_method_ << " pc=" << pc << std::endl;
                }
        }
        if (it != static_field_storage_.end()) {
            result_value = it->second;
        } else if (field_res.class_descriptor ==
                       "Landroid/view/View$MeasureSpec;" &&
                   (field_res.field_name == "EXACTLY" ||
                    field_res.field_name == "AT_MOST" ||
                    field_res.field_name == "UNSPECIFIED")) {
            // R500 (ROOT-VIEW-FRAME family): AOSP View$MeasureSpec mode
            // constants (EXACTLY = 0x40000000, AT_MOST = 0x80000000,
            // UNSPECIFIED = 0) are JVM-stable compile-time ints consumed
            // by every programmatic measure chain. The int sget path has
            // no constant synthesis — seed them BEFORE the typed-default
            // law answers 0 (probe evidence: makeMeasureSpec(200, EXACTLY)
            // returned the mode-less 0xc8 → default onMeasure -> 0x0).
            if (field_res.field_name == "EXACTLY") {
                result_value = DalvikValue::make_int(0x40000000);
            } else if (field_res.field_name == "AT_MOST") {
                result_value = DalvikValue::make_int((int32_t)0x80000000u);
            } else {
                result_value = DalvikValue::make_int(0);
            }
            static_field_storage_[static_key] = result_value;
        } else {
            static_field_storage_[static_key] = result_value;
        }
    }

    // ── F-062: capture the APK's compose_view_saveable_id_tag key ──────
    // Name-based capture (no hardcoded resource id): the androidx
    // saved-state migration reads this key on EVERY ancestor hop; the
    // ViewShadow decor-anchor law (getTag) needs the same int to answer
    // the terminating String at the window root. Evidence: dooz live run
    // walk 477→102→8→101 dead-ended at the unanchored root and the
    // `parent as View` unwrap NPE'd mid-composition (0-pixel first frame).
    if (field_res.resolved &&
        field_res.field_name == "compose_view_saveable_id_tag" &&
        result_value.type == DalvikType::INT32 && result_value.int_val != 0) {
        framework::ViewShadow::record_compose_saveable_id_key(
            result_value.int_val);
    }

    // EXP-053: Trace every sget (for resource ID investigation).
    // Throttled to first 100 to avoid log explosion.
    // EXP-063: Also trace R$string and R$drawable specifically.
    if (field_res.resolved) {
        static thread_local uint64_t sget_log_count = 0;
        static thread_local std::string last_method = "";
        static thread_local uint64_t method_sget_count = 0;
        if (current_method_ != last_method) {
            last_method = current_method_;
            method_sget_count = 0;
        }
        bool should_log = (sget_log_count < 100 && method_sget_count < 5);
        // EXP-063: Always log R$ fields
        bool is_r_field = (field_res.class_descriptor.find("R$") != std::string::npos);
        should_log = should_log || is_r_field;
        if (should_log) {
            sget_log_count++;
            method_sget_count++;
            std::cerr << "[SGET] class=" << current_class_
                      << " method=" << current_method_
                      << " pc=" << pc
                      << " field=" << field_res.class_descriptor << "."
                      << field_res.field_name
                      << " value=" << result_value.int_val
                      << std::endl;
        }
    }

    set_register(dest_reg, result_value);
    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.operands.push_back({"v" + std::to_string(dest_reg), "destination"});
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});
    }

    pc_ = pc + 2;
    return true;
}

bool DalvikExecutionEngine::execute_sget_object(uint32_t pc, InstructionTrace& trace) {
    // Format: 21c sget-object vAA, field@BBBB (2 code units)
    // EXP-042 Phase 2 FIX: never return false — advance pc_ on failure.
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }

    uint16_t instr = bytecode_[pc];
    uint8_t dest_reg = (instr >> 8) & 0xFF;
    uint16_t field_idx = bytecode_[pc + 1];

    uint64_t f107_sr0 = 0; phase_clock().enter(phase_clock().sget_resolve_ph, f107_sr0);
    FieldResolution field_res = resolve_field(field_idx);
    phase_clock().exit(phase_clock().sget_resolve_ph, f107_sr0);
    uint64_t f107_si0 = 0; phase_clock().enter(phase_clock().sget_init_ph, f107_si0);

    // CONT-126: FIELD-TRACE statics coverage (sget-object family) — same
    // law and same env gate as the sget hook; read-only diagnostics.
    if (field_res.resolved &&
        field_trace_filter_set() &&
        field_trace_active(field_res.field_name.c_str(),
                           (current_class_ + "." + current_method_).c_str(),
                           field_res.class_descriptor.c_str())) {
        std::cerr << "[FIELD-TRACE] get-static " << current_class_ << "."
                  << current_method_ << " " << field_res.class_descriptor
                  << "." << field_res.field_name << std::endl;
    }

    // EXP-053: Ensure the class is initialized before reading its static field.
    // F-NEW-215: active use (sget-object family) of an ERRONEOUS class
    // raises NoClassDefFoundError instead of answering null.
    if (field_res.resolved) {
        ensure_class_initialized(field_res.class_descriptor);
        if (class_clinit_failed(field_res.class_descriptor) &&
            !clinit_exc_already_in_flight()) {  // F-NEW-395: no double-raise at the triggering use
            static std::atomic<uint64_t> f215_sgeto_n{0};
            if (f215_sgeto_n.fetch_add(1, std::memory_order_relaxed) < 8) {
                std::cerr << "[F-NEW-215] ACTIVE-USE sget-object class="
                          << field_res.class_descriptor << " caller="
                          << current_class_ << "." << current_method_
                          << std::endl;
            }
            throw_deferred("Ljava/lang/NoClassDefFoundError;",
                           field_res.class_descriptor +
                               " <clinit> failed previously (erroneous class)",
                           "F-NEW-215");
            pc_ = pc + 2;
            return false;
        }
    }

    phase_clock().exit(phase_clock().sget_init_ph, f107_si0);
    uint64_t f107_st0 = 0; phase_clock().enter(phase_clock().sget_tail_ph, f107_st0);
    struct F107TailGuard { PhaseClock::Phase& ph; uint64_t t0; ~F107TailGuard(){ phase_clock().exit(ph, t0);} } f107_tailguard{phase_clock().sget_tail_ph, f107_st0};
    DalvikValue result_value;
    result_value.type = DalvikType::NULL_REF;
    result_value.object_id = 0;

    // S24 probe (env-gated, bounded): the Kotlin EmptyList singleton
    // (z1/t.i) feeds NavController.navigate's List param; a null answer
    // nulls z1/r.D's receiver and NPEs addAll ("parameter elements").
    if (field_res.resolved &&
        field_res.class_descriptor == "Lz1/t;" &&
        field_res.field_name == "i" &&
        std::getenv("MINIANDROID_S24_TRACE") != nullptr) {
        static thread_local uint64_t s24_emptylist = 0;
        if (s24_emptylist < 12) {
            ++s24_emptylist;
            auto probe = static_field_storage_.find("Lz1/t;.i");
            std::cerr << "[S24-EMPTYLIST] sget-object z1/t.i pc=" << pc
                      << " storage_hit=" << (probe != static_field_storage_.end())
                      << " oid="
                      << (probe != static_field_storage_.end()
                              ? probe->second.object_id : 0)
                      << " type="
                      << (probe != static_field_storage_.end()
                              ? static_cast<int>(probe->second.type) : -1)
                      << std::endl;
        }
    }

    if (field_res.resolved) {
        std::string static_key = field_res.class_descriptor + "." + field_res.field_name;
        auto it = static_field_storage_.find(static_key);
        // ── TRAIN-68 (T68-START): the CoroutineStart (Lyr;) enum static
        // reads — the node's lazy launch branches on the start constant;
        // log every Lyr; sget-object with field + loaded object id so the
        // inline-vs-deferred divergence per node becomes evidence.
        if (field_res.class_descriptor == "Lyr;" && touch_dispatch_active_) {
            static const bool t68s_on = diag_env("MINIANDROID_T68_NODE_TRACE");
            if (t68s_on) {
                static thread_local uint64_t t68s_n = 0;
                if (t68s_n++ < 80)
                    std::cerr << "[T68-START] sget Lyr;."
                              << field_res.field_name
                              << " caller=" << current_class_ << "."
                              << current_method_ << " pc=" << pc
                              << " storage_hit="
                              << (it != static_field_storage_.end() ? 1 : 0)
                              << " oid="
                              << (it != static_field_storage_.end()
                                      ? it->second.object_id : 0)
                              << std::endl;
            }
        }
        // R-NEW-561 (CONT-42 TRAIN 8): JVM static-field resolution law —
        // the static lives on its DECLARER (JVM sget resolution walks the
        // superclass chain). [SGET-MISS] evidence (this wave): the read key
        // (a requesting/alias class identity, e.g. telegram's Ljr;.b0)
        // missed while the write had landed under a DIFFERENT identity of
        // the SAME logical static (the declarer class, e.g.
        // Lcom/google/firebase/messaging/f;.b0). Walk the superclass chain
        // (bounded 32) and answer the first ancestor key that holds the
        // field; alias the requesting key so identity (==) holds from here
        // on. No ancestor hit = the ladder below answers as before.
        if (it == static_field_storage_.end()) {
            std::string walk_cls = field_res.class_descriptor;
            for (int r561_hop = 0; r561_hop < 32; ++r561_hop) {
                auto sit = class_to_superclass_.find(walk_cls);
                if (sit == class_to_superclass_.end() || sit->second.empty())
                    break;
                walk_cls = sit->second;
                auto dit = static_field_storage_.find(
                    walk_cls + "." + field_res.field_name);
                if (dit != static_field_storage_.end()) {
                    static_field_storage_[static_key] = dit->second;
                    it = static_field_storage_.find(static_key);
                    static thread_local uint64_t r561_hits = 0;
                    if (r561_hits++ < 12)
                        std::cerr << "[R561-DECLARER] sget-object "
                                  << static_key << " <- " << walk_cls << "."
                                  << field_res.field_name << std::endl;
                    break;
                }
            }
        }
        // CONT-38 decode diag (env-gated, bounded): the theme-defaults
        // color statics — who reads them and what the storage answers.
        // S156-P4 (CONT-42 zero-cost-gate law): static-cached — was a raw
        // std::getenv per sget.
        static thread_local const bool c38_on =
            std::getenv("MINIANDROID_CLINIT_PATH_TRACE") != nullptr;
        if (c38_on &&
            (field_res.class_descriptor == "Lzh;" ||
             field_res.class_descriptor == "Lai;" ||
             field_res.class_descriptor == "Lts0;")) {
            static thread_local uint64_t c38_n = 0;
            if (c38_n++ < 300)
                std::cerr << "[COLOR-SGET] " << static_key
                          << " hit=" << (it != static_field_storage_.end())
                          << " caller=" << current_class_ << "."
                          << current_method_ << " pc=" << pc << std::endl;
        }
        if (it != static_field_storage_.end()) {
            result_value = it->second;
        } else {
            // CYCLE-E: framework enum constant synthesis. android.* classes
            // are not defined in app DEX files, so their enum <clinit> never
            // runs and every sget-object of e.g. Paint$Style.STROKE produced
            // NULL — Paint.setStyle / Path.setFillType / PorterDuff modes
            // silently degraded for every real drawing call. Materialize the
            // constant as a real object carrying its AOSP ordinal, cached per
            // static_key so identity (==) comparisons hold.
            const int ordinal = framework_enum_ordinal(
                field_res.class_descriptor, field_res.field_name);
            if (field_res.class_descriptor ==
                           "Landroid/content/Context;" &&
                       field_res.field_name.size() > 8 &&
                       field_res.field_name.rfind("_SERVICE") ==
                           field_res.field_name.size() - 8) {
                // ── F-NEW-639 (S235-1, #588 Wave-5 lane): AOSP Context
                // .*_SERVICE string-constant law — the lane's F-NEW-637 face
                // (conversations POWER_SERVICE → silent null service): the
                // engine had NO framework static STRING table, so every
                // Context.POWER_SERVICE / TELEPHONY_SERVICE sget-object
                // answered null → getSystemService(null) → null manager →
                // the app dies at the cast/NPE boundary. AOSP Context.java:
                // every service constant is a public static final String
                // whose VALUE is the service-registry key ("power",
                // "phone", ...). Served from the table below (the AOSP
                // Context.java string truth), cached per static_key like
                // the Locale law.
                static const miniandroid::dalvik::KvPair t_ctx_services[] = {
                    {"POWER_SERVICE", "power"},
                    {"WINDOW_SERVICE", "window"},
                    {"LAYOUT_INFLATER_SERVICE", "layout_inflater"},
                    {"ACTIVITY_SERVICE", "activity"},
                    {"INPUT_METHOD_SERVICE", "input_method"},
                    {"ALARM_SERVICE", "alarm"},
                    {"KEYGUARD_SERVICE", "keyguard"},
                    {"LOCATION_SERVICE", "location"},
                    {"SEARCH_SERVICE", "search"},
                    {"NOTIFICATION_SERVICE", "notification"},
                    {"ACCESSIBILITY_SERVICE", "accessibility"},
                    {"DEVICE_POLICY_SERVICE", "device_policy"},
                    {"UI_MODE_SERVICE", "uimode"},
                    {"DOWNLOAD_SERVICE", "download"},
                    {"STORAGE_SERVICE", "storage"},
                    {"AUDIO_SERVICE", "audio"},
                    {"VIBRATOR_SERVICE", "vibrator"},
                    {"CONNECTIVITY_SERVICE", "connectivity"},
                    {"WIFI_SERVICE", "wifi"},
                    {"BATTERY_SERVICE", "battery"},
                    {"CLIPBOARD_SERVICE", "clipboard"},
                    {"INPUT_SERVICE", "input"},
                    {"DISPLAY_SERVICE", "display"},
                    {"SENSOR_SERVICE", "sensor"},
                    {"BLUETOOTH_SERVICE", "bluetooth"},
                    {"NSD_SERVICE", "nsd"},
                    {"MEDIA_ROUTER_SERVICE", "media_router"},
                    {"TELEPHONY_SERVICE", "phone"},
                    {"TELEPHONY_SUBSCRIPTION_SERVICE", "isub"},
                    {"CARRIER_CONFIG_SERVICE", "carrier_config"},
                    {"TELECOM_SERVICE", "telecom"},
                    {"APPWIDGET_SERVICE", "appwidget"},
                    {"WALLPAPER_SERVICE", "wallpaper"},
                    {"RESTRICTIONS_SERVICE", "restrictions"},
                    {"PRINT_SERVICE", "print"},
                    {"ACCOUNT_SERVICE", "account"},
                    {"JOB_SCHEDULER_SERVICE", "jobscheduler"},
                    {"MEDIA_SESSION_SERVICE", "media_session"},
                    {"DROPBOX_SERVICE", "dropbox"},
                    {"NETWORK_STATS_SERVICE", "networkstats"},
                    {"USB_SERVICE", "usb"},
                    {"VIBRATOR_MANAGER_SERVICE", "vibrator_manager"},
                    {"APP_OPS_SERVICE", "appops"},
                    {"CAMERA_SERVICE", "camera"},
                    {"USER_SERVICE", "user"},
                };
                if (const char* svc = kv_table_find(
                        t_ctx_services,
                        sizeof(t_ctx_services) /
                            sizeof(t_ctx_services[0]),
                        field_res.field_name)) {
                    result_value = DalvikValue::make_string(svc, pc);
                    static_field_storage_[static_key] = result_value;
                    static thread_local uint64_t f639_const_n = 0;
                    if (f639_const_n++ < 8)
                        std::cerr << "[F-NEW-639] Context."
                                  << field_res.field_name << " -> \"" << svc
                                  << "\" caller=" << current_class_ << "."
                                  << current_method_ << std::endl;
                } else {
                    static_field_storage_[static_key] = result_value;
                }
            } else if (ordinal >= 0) {
                uint32_t enum_id = heap_.allocate(field_res.class_descriptor, pc, 0);
                heap_.set_object_field(enum_id, "ordinal",
                                       DalvikValue::make_int(ordinal));
                heap_.set_object_field(enum_id, "enum_name",
                                       DalvikValue::make_string(field_res.field_name, 0));
                result_value = DalvikValue::make_object(enum_id,
                                                        field_res.class_descriptor);
                static_field_storage_[static_key] = result_value;
            } else if (field_res.class_descriptor == "Lkotlin/Unit;" &&
                       field_res.field_name == "INSTANCE") {
                // ── A-R6 R30 — KOTLIN UNIT OBJECT-DECLARATION LAW ──────
                // (roadmap §8 F1, the kotlin_family_probe census at
                // 1a0fa259: the unresolved-static world answered NULL for
                // Lkotlin/Unit;.INSTANCE — every Unit-typed expression in
                // a host-boundary report read null, and the null identity
                // propagated through static stores). Kotlin law
                // (Tier 1, kotlin/Unit): an object declaration holds
                // exactly ONE instance per runtime, loaded from the static
                // INSTANCE field. get_or_create_singleton mints it once
                // per engine — identity (===) across reads and
                // static-field roundtrips holds by construction, and the
                // a1/a2 probe rows are the executable proof.
                result_value = get_or_create_singleton("Lkotlin/Unit;");
                static_field_storage_[static_key] = result_value;
                static thread_local uint64_t r30_unit_n{0};
                if (r30_unit_n++ < 8)
                    std::cerr << "[R30-UNIT] sget-object Lkotlin/Unit;.INSTANCE -> o"
                              << result_value.object_id << " caller="
                              << current_class_ << "." << current_method_
                              << std::endl;
            } else if (field_res.class_descriptor == "Ljava/lang/Boolean;" &&
                       (field_res.field_name == "TRUE" ||
                        field_res.field_name == "FALSE")) {
                // F-050d: java.lang.Boolean static constant synthesis.
                // OpenJDK law (Boolean.java): public static final Boolean
                // TRUE = new Boolean(true); FALSE = new Boolean(false); —
                // and R8 rewrites Boolean.valueOf(true) INTO the sget of
                // TRUE. Live evidence (dooz v18): the Recomposer's channel
                // iterator resumed hasNext() with a boxed Boolean; the
                // resume path hit sget-object Boolean.TRUE, got NULL, the
                // unboxed result read false, the consume loop exited as if
                // the channel was exhausted, and cancelConsumed cancelled
                // the Recomposer's awaitWork channel mid-run — the frame
                // await never resumed (CancellationException "Channel was
                // cancelled"). Cached per static_key so identity (===)
                // comparisons against the canonical singleton hold.
                const bool bool_val = (field_res.field_name == "TRUE");
                uint32_t box_id = heap_.allocate("Ljava/lang/Boolean;", pc, 0);
                heap_.set_object_field(box_id, "value",
                                       DalvikValue::make_bool(bool_val));
                result_value = DalvikValue::make_object(box_id,
                                                        "Ljava/lang/Boolean;");
                static_field_storage_[static_key] = result_value;
            } else if (field_res.class_descriptor == "Ljava/lang/System;" &&
                       (field_res.field_name == "out" ||
                        field_res.field_name == "err")) {
                // F-NEW-245 (CONT-5): java.lang.System.out / System.err —
                // NEVER NULL. OpenJDK System.java: out/err are final
                // PrintStreams over FileDescriptor.out/err, initialized in
                // System.<clinit> before any app code runs. Pre-fix: no
                // static synthesis → sget-object answered NULL → the very
                // first System.out.println NPE'd ("PrintStream.println on
                // a null object reference") and killed the app at APP
                // BOUNDARY (raumballer JGEngine.initActivity pc=81, x3
                // deterministic; fan-out: every library/game that logs
                // via System.out). Cached per static_key so identity
                // (System.out == System.out) holds; __fd__ = 1|2 routes
                // println/print/write/flush to real stdout/stderr
                // (the PrintStream bridge law near the PrintWriter law).
                uint32_t ps_id = heap_.allocate("Ljava/io/PrintStream;", pc, 0);
                heap_.set_object_field(
                    ps_id, "__fd__",
                    DalvikValue::make_int(field_res.field_name == "out" ? 1
                                                                        : 2));
                result_value = DalvikValue::make_object(
                    ps_id, "Ljava/io/PrintStream;");
                static_field_storage_[static_key] = result_value;
            } else if (const int static_int_val = framework_static_int(
                           field_res.class_descriptor, field_res.field_name);
                       static_int_val >= 0) {
                // F-110e (S62+): framework static INT constant synthesis.
                // Cached per static_key like the enum law above so identity
                // semantics hold for later sgets of the same constant.
                result_value = DalvikValue::make_int(static_int_val);
                static_field_storage_[static_key] = result_value;
            } else if (field_res.class_descriptor == "Ljava/util/Locale;") {
                // M3 F-ROOM-CHAIN: java.util.Locale constant synthesis.
                // microtimer v8 Room init reads Locale.US inside the R8-inlined
                // Kotlin Intrinsics path (Le/o;.<init> — "(this as
                // java.lang.String).toLowerCase(locale)" expression check); a
                // NULL Locale.US produced "US must not be null" NPEs that the
                // uncaught-tail compatibility policy swallowed, breaking the
                // Room open chain. AOSP law: Locale.* constants are non-null
                // static objects; materialize them (cached per static_key so
                // identity comparisons hold) with __locale_tag__ carrying the
                // AOSP tag for String-case/Locale-sensitive bridges.
                static const miniandroid::dalvik::KvPair t_kLocaleConsts[] = {
    {"CANADA", "en_CA"},
    {"CANADA_FRENCH", "fr_CA"},
    {"CHINA", "zh_CN"},
    {"CHINESE", "zh"},
    {"ENGLISH", "en"},
    {"FRANCE", "fr_FR"},
    {"FRENCH", "fr"},
    {"GERMAN", "de"},
    {"GERMANY", "de_DE"},
    {"ITALIAN", "it"},
    {"ITALY", "it_IT"},
    {"JAPAN", "ja_JP"},
    {"JAPANESE", "ja"},
    {"KOREA", "ko_KR"},
    {"KOREAN", "ko"},
    {"PRC", "zh_CN"},
    {"SIMPLIFIED_CHINESE", "zh_CN"},
    {"TAIWAN", "zh_TW"},
    {"TRADITIONAL_CHINESE", "zh_TW"},
    {"UK", "en_GB"},
    {"US", "en_US"},
};
                const char* lv = kv_table_find(t_kLocaleConsts,
                        sizeof(t_kLocaleConsts) / sizeof(t_kLocaleConsts[0]),
                        field_res.field_name);
                if (lv) {
                    uint32_t loc_id = heap_.allocate("Ljava/util/Locale;", pc, 0);
                    heap_.set_object_field(loc_id, "__locale_tag__",
                                           DalvikValue::make_string(lv, 0));
                    heap_.set_object_field(loc_id, "__locale_name__",
                                           DalvikValue::make_string(field_res.field_name, 0));
                    result_value = DalvikValue::make_object(loc_id,
                                                            "Ljava/util/Locale;");
                    static_field_storage_[static_key] = result_value;
                    std::cerr << "[LOCALE-CONST] synthesized Locale."
                              << field_res.field_name << " tag=\"" << lv
                              << "\" oid=" << loc_id << std::endl;
                } else {
                    static_field_storage_[static_key] = result_value;
                }
            } else if (field_res.class_descriptor ==
                           "Ljava/nio/ByteOrder;" &&
                       (field_res.field_name == "LITTLE_ENDIAN" ||
                        field_res.field_name == "BIG_ENDIAN")) {
                // F-NEW-393 (CONT-86): AOSP ByteOrder law — LITTLE_ENDIAN /
                // BIG_ENDIAN are non-null singletons (OpenJDK ByteOrder.java);
                // org.andstatus.game2048's Lb8;.<init> reads both to build
                // its endian views. Materialize with ordinal 0/1 (cached per
                // static_key; nativeOrder() answers the LITTLE_ENDIAN one on
                // this aarch64 device model).
                const int bo_ord =
                    field_res.field_name == "LITTLE_ENDIAN" ? 0 : 1;
                uint32_t bo_id = heap_.allocate("Ljava/nio/ByteOrder;", pc, 0);
                heap_.set_object_field(bo_id, "ordinal",
                                       DalvikValue::make_int(bo_ord));
                heap_.set_object_field(bo_id, "__byteorder_name__",
                                       DalvikValue::make_string(
                                           field_res.field_name, 0));
                result_value = DalvikValue::make_object(
                    bo_id, "Ljava/nio/ByteOrder;");
                static_field_storage_[static_key] = result_value;
            } else if (field_res.class_descriptor == "Landroid/os/Environment;" &&
                       (field_res.field_name == "MEDIA_MOUNTED" ||
                        field_res.field_name == "MEDIA_MOUNTED_READ_ONLY" ||
                        field_res.field_name == "MEDIA_REMOVED" ||
                        field_res.field_name == "MEDIA_UNMOUNTED" ||
                        field_res.field_name == "MEDIA_BAD_REMOVAL" ||
                        field_res.field_name == "MEDIA_CHECKING" ||
                        field_res.field_name == "MEDIA_NOFS" ||
                        field_res.field_name == "MEDIA_SHARED" ||
                        field_res.field_name == "MEDIA_UNKNOWN" ||
                        field_res.field_name == "MEDIA_EJECTING")) {
                // F-NEW-223 (user campaign §H): Environment storage-state
                // String constants. AOSP Environment.java — apps gate their
                // storage paths on `state.equals(Environment.MEDIA_MOUNTED)`;
                // with no seed the sget answered null and String.equals(null)
                // returned false → the app concluded "no external storage" →
                // onCreate died. Values are the AOSP constant strings.
                const char* s223 =
                    field_res.field_name == "MEDIA_MOUNTED"            ? "mounted"
                    : field_res.field_name == "MEDIA_MOUNTED_READ_ONLY" ? "mounted_ro"
                    : field_res.field_name == "MEDIA_REMOVED"           ? "removed"
                    : field_res.field_name == "MEDIA_UNMOUNTED"         ? "unmounted"
                    : field_res.field_name == "MEDIA_BAD_REMOVAL"       ? "bad_removal"
                    : field_res.field_name == "MEDIA_CHECKING"          ? "checking"
                    : field_res.field_name == "MEDIA_NOFS"              ? "nofs"
                    : field_res.field_name == "MEDIA_SHARED"            ? "shared"
                    : field_res.field_name == "MEDIA_EJECTING"          ? "ejecting"
                                                                        : "unknown";
                result_value = DalvikValue::make_string(s223, 0);
                static_field_storage_[static_key] = result_value;
            } else if (field_res.class_descriptor == "Ljava/util/Collections;" &&
                       (field_res.field_name == "EMPTY_SET" ||
                        field_res.field_name == "EMPTY_LIST" ||
                        field_res.field_name == "EMPTY_MAP")) {
                // R-NEW-397 (S78, F-154): java.util.Collections empty-singleton
                // static-final law. OpenJDK Collections.java:
                //   public static final Set  EMPTY_SET  = new EmptySet<>();
                //   public static final List EMPTY_LIST = new EmptyList<>();
                //   public static final Map  EMPTY_MAP  = new EmptyMap<>();
                // JVM-injected-at-clinit constants — never null. Evidence:
                // dooz DataStore first-launch parse — Ljs0;.entrySet (REAL dex
                // bytecode) sgets Collections.EMPTY_SET; with no seed the
                // sget answered typed-zero NULL → Set.iterator() NPE at
                // Lh3;.h pc=36 → uncaught past all app frames (run/
                // s78_f152_postfix2). Materialized as heap-backed EMPTY
                // singletons ("__array_length__"=0) so the F-036 iterator
                // machinery + the R-NEW-397 Empty-family dispatch below
                // answer every read. Cached per static_key — identity holds.
                const char* empty_cls = nullptr;
                if (field_res.field_name == "EMPTY_SET")
                    empty_cls = "Ljava/util/Collections$EmptySet;";
                else if (field_res.field_name == "EMPTY_LIST")
                    empty_cls = "Ljava/util/Collections$EmptyList;";
                else
                    empty_cls = "Ljava/util/Collections$EmptyMap;";
                uint32_t e_id = heap_.allocate(empty_cls, pc, 0);
                heap_.set_object_field(e_id, "__array_length__",
                                       DalvikValue::make_int(0));
                heap_.set_object_field(e_id, "__iterator_pos__",
                                       DalvikValue::make_int(0));
                result_value = DalvikValue::make_object(e_id, empty_cls);
                static_field_storage_[static_key] = result_value;
                std::cerr << "[R-NEW-397] synthesized Collections."
                          << field_res.field_name << " obj#" << e_id
                          << std::endl;
            } else if (field_res.class_descriptor ==
                           "Landroid/graphics/Typeface;" &&
                       (field_res.field_name == "DEFAULT" ||
                        field_res.field_name == "DEFAULT_BOLD" ||
                        field_res.field_name == "SANS_SERIF" ||
                        field_res.field_name == "SERIF" ||
                        field_res.field_name == "MONOSPACE")) {
                // F-NEW-294 (CONT-35): AOSP Typeface static-constant law.
                // frameworks/base/graphics/java/android/graphics/Typeface.java
                // declares the family constants as static finals built by
                // create() inside <clinit>:
                //   DEFAULT       = create((String) null, NORMAL)
                //   DEFAULT_BOLD  = create((String) null, BOLD)
                //   SANS_SERIF    = create("sans-serif", NORMAL)
                //   SERIF         = create("serif", NORMAL)
                //   MONOSPACE     = create("monospace", NORMAL)
                // A live ART <clinit> ALWAYS completes — the constants are
                // NEVER null (same platform-constant law family as the
                // Boolean/Locale/StandardCharsets arms above). The engine
                // runs no framework <clinit> for the platform class, so the
                // sget hit [SGET-MISS] and answered NULL; the R8-inlined
                // Compose font resolver (FontListFontFamilyTypefaceAdapter
                // .resolve → TypefaceResult(value, immediate)) then handed
                // the null value to the consumer's Kotlin platform-type
                // `!!` check — compiled as invoke-virtual getClass() BEFORE
                // the check-cast — and composeStopwatch's
                // AndroidParagraphIntrinsics (Lk6;.<init> pc=409) NPE'd
                // once per run ("getClass on a null object reference"),
                // aborting the text pass and leaving the Compose stopwatch
                // view (Lh4;) at onDraw ops=0. Materialize each constant as
                // a REAL heap Typeface object carrying its family/style
                // (__typeface_family__/__typeface_style__), cached per
                // static_key so identity comparisons hold — the same shape
                // the bridge_to_api create/defaultFromStyle law answers.
                const char* fam = "sans-serif";
                int st = 0;
                if (field_res.field_name == "DEFAULT_BOLD") {
                    fam = "sans-serif"; st = 1;
                } else if (field_res.field_name == "SANS_SERIF") {
                    fam = "sans-serif"; st = 0;
                } else if (field_res.field_name == "SERIF") {
                    fam = "serif"; st = 0;
                } else if (field_res.field_name == "MONOSPACE") {
                    fam = "monospace"; st = 0;
                } else {
                    fam = "sans-serif"; st = 0;   // DEFAULT
                }
                uint32_t tf_id = heap_.allocate("Landroid/graphics/Typeface;",
                                                pc, 0);
                heap_.set_object_field(tf_id, "__typeface_family__",
                                       DalvikValue::make_string(fam, 0));
                heap_.set_object_field(tf_id, "__typeface_style__",
                                       DalvikValue::make_int(st));
                result_value = DalvikValue::make_object(
                    tf_id, "Landroid/graphics/Typeface;");
                static_field_storage_[static_key] = result_value;
                std::cerr << "[F-NEW-294] synthesized Typeface."
                          << field_res.field_name << " family=" << fam
                          << " style=" << st << " oid=" << tf_id
                          << std::endl;
            } else if (field_res.class_descriptor ==
                           "Landroid/view/View$MeasureSpec;" &&
                       (field_res.field_name == "EXACTLY" ||
                        field_res.field_name == "AT_MOST" ||
                        field_res.field_name == "UNSPECIFIED")) {
                // R500 (ROOT-VIEW-FRAME family): AOSP View.java MeasureSpec
                // mode constants are JVM-stable compile-time ints —
                //   UNSPECIFIED = 0, EXACTLY = 1 << 30 (0x40000000),
                //   AT_MOST = 2 << 30 (0x80000000)
                // — and the DEX measure chains (F-096b in-place getMode
                // law) compare them DIRECTLY. With no seed the sget
                // answered typed-default 0 for EXACTLY/AT_MOST, so every
                // programmatic makeMeasureSpec(size, EXACTLY) produced a
                // mode-less spec (probe evidence: makeMeasureSpec(200,
                // EXACTLY) -> 0xc8; default onMeasure then answered 0x0).
                if (field_res.field_name == "EXACTLY") {
                    result_value = DalvikValue::make_int(0x40000000);
                } else if (field_res.field_name == "AT_MOST") {
                    result_value = DalvikValue::make_int((int32_t)0x80000000u);
                } else {
                    result_value = DalvikValue::make_int(0);
                }
                static_field_storage_[static_key] = result_value;
            } else if (field_res.class_descriptor == "Ljava/io/File;" &&
                       (field_res.field_name == "separator" ||
                        field_res.field_name == "separatorChar" ||
                        field_res.field_name == "pathSeparator" ||
                        field_res.field_name == "pathSeparatorChar")) {
                // F-079 (R-NEW-305): java.io.File path-separator constant law.
                // OpenJDK/AOSP (ojluni File.java): the four static constants
                // are initialized from the platform FileSystem:
                //   separator      = fs.getSeparator()    → "/" on Linux/Android
                //   separatorChar  = separator.charAt(0)  → '/'
                //   pathSeparator  = fs.getPathSeparator() → ":" on Linux/Android
                //   pathSeparatorChar = pathSeparator.charAt(0) → ':'
                // They are compile-time-stable platform constants — never
                // null. Live evidence (dooz v18, post F-078): the Kotlin
                // stdlib FilePathString companion (<clinit> Lg2/m;) reads
                // File.separator via sget-object; with no seed the SGET
                // returned null and the companion's Intrinsics null-check
                // threw NPE "separator must not be null" DURING <clinit> —
                // the failing class-init killed the Recomposer's first
                // composition at the F/A0.a unwind.
                // Cached per static_key (same policy as Locale/Boolean).
                if (field_res.field_name == "separator") {
                    result_value = DalvikValue::make_string("/", 0);
                } else if (field_res.field_name == "pathSeparator") {
                    result_value = DalvikValue::make_string(":", 0);
                } else if (field_res.field_name == "separatorChar") {
                    result_value = DalvikValue::make_char('/');
                } else {
                    result_value = DalvikValue::make_char(':');
                }
                static_field_storage_[static_key] = result_value;
            } else if (
                // S123-CLINIT-MAT: shared-geometry static materialization
                // after a FAILED <clinit>. AOSP law: a class's <clinit> runs
                // before any static read; inline-initialized statics like
                // `public static final RectF rectTmp = new RectF()` are
                // therefore NEVER null at first use. If the class's clinit
                // aborted partway (unmodeled API mid-<clinit>), every static
                // declared AFTER the abort point reads back null and the app
                // draw code NPEs on the first geometry call (live evidence:
                // forkgram he1$d.onDraw pc=16 — sget-object
                // AndroidUtilities.rectTmp → null → RectF.set NPE ×65
                // APP-BOUNDARY unwinds; the "StartMessaging" text was already
                // measured on the login view). The class IS marked
                // initialized (attempted), so re-running clinit is not
                // possible; materialize the AOSP no-arg-ctor state (zero
                // geometry) for the shared graphics primitives, cached per
                // static_key so identity (==) holds across the app.
                field_res.field_type == "Landroid/graphics/RectF;" ||
                field_res.field_type == "Landroid/graphics/Rect;" ||
                field_res.field_type == "Landroid/graphics/Point;" ||
                field_res.field_type == "Landroid/graphics/Paint;") {
                const bool attempted =
                    initialized_classes_.find(field_res.class_descriptor) !=
                    initialized_classes_.end();
                auto null_probe = static_field_storage_.find(static_key);
                const bool stored_null =
                    null_probe != static_field_storage_.end() &&
                    null_probe->second.type == DalvikType::NULL_REF;
                // F-NEW-446 (CONT-106, fixture-first): S123 fires ONLY for a
                // genuinely FAILED <clinit> (the F-NEW-215 evidence map).
                // AOSP law: a COMPLETED clinit that leaves a static object
                // field null means the app's own lazy factory owns the first
                // assignment — sget MUST return that null faithfully so the
                // app's null-sentinel guards keep working. The old
                // `attempted || stored_null` gate materialized Paint/RectF
                // statics of HEALTHY classes, converting guarded early-return
                // paths into deep paths that read unrelated lazy singletons.
                // Live PRE evidence (run/cont105/tg_pre.log + probe
                // fixtures/cont106_clinitsentinel PRE, binary
                // afaad5bd4f56f9d3): o6.<clinit> result=OK (1736 sputs, no
                // k0/m0/u1 assignment — telegram's o6.P(Context) factory owns
                // them; single u1 writer, callers o6.R / r4.<init> /
                // CheckBoxSquare.<init>) → [S123-CLINIT-MAT] materialized
                // o6.k0/m0 on first sget → o6.k's `if-nez k0 → return-void`
                // guard (classes3.dex 0x0..0x8) fell through → iput-boolean
                // xj0.Y:Z on the never-factory u1 → uncaught NPE @o6.k pc=46.
                // Probe faces: [C106-SENTINEL] guardEscaped=true (AOSP false)
                // and [C106-INVOKE2] result=NO-EXC (AOSP NPE).
                // The original S123 evidence (forkgram he1$d →
                // AndroidUtilities.rectTmp, clinit ABORTED mid-way on an
                // unmodeled API) is exactly a failed_clinit_classes_ member —
                // preserved by this gate. POST faces: guardEscaped=false,
                // INVOKE2=NPE, failed-clinit materialization retained.
                const bool clinit_failed =
                    failed_clinit_classes_.find(field_res.class_descriptor) !=
                    failed_clinit_classes_.end();
                if (clinit_failed) {
                    uint32_t geo_id = heap_.allocate(field_res.field_type,
                                                     pc, 0);
                    // AOSP no-arg ctor state: zero geometry fields.
                    if (field_res.field_type == "Landroid/graphics/RectF;") {
                        heap_.set_object_field(geo_id, "left",
                                               DalvikValue::make_float(0.0f));
                        heap_.set_object_field(geo_id, "top",
                                               DalvikValue::make_float(0.0f));
                        heap_.set_object_field(geo_id, "right",
                                               DalvikValue::make_float(0.0f));
                        heap_.set_object_field(geo_id, "bottom",
                                               DalvikValue::make_float(0.0f));
                    } else if (field_res.field_type ==
                               "Landroid/graphics/Rect;") {
                        heap_.set_object_field(geo_id, "left",
                                               DalvikValue::make_int(0));
                        heap_.set_object_field(geo_id, "top",
                                               DalvikValue::make_int(0));
                        heap_.set_object_field(geo_id, "right",
                                               DalvikValue::make_int(0));
                        heap_.set_object_field(geo_id, "bottom",
                                               DalvikValue::make_int(0));
                    } else if (field_res.field_type ==
                               "Landroid/graphics/Point;") {
                        heap_.set_object_field(geo_id, "x",
                                               DalvikValue::make_int(0));
                        heap_.set_object_field(geo_id, "y",
                                               DalvikValue::make_int(0));
                    } else {
                        // Landroid/graphics/Paint; — AOSP default paint:
                        // FILL style, BLACK color, anti-alias off.
                        heap_.set_object_field(geo_id, "color",
                                               DalvikValue::make_int(
                                                   0xFF000000));
                    }
                    result_value = DalvikValue::make_object(
                        geo_id, field_res.field_type);
                    static_field_storage_[static_key] = result_value;
                    std::cerr << "[S123-CLINIT-MAT] materialized "
                              << field_res.class_descriptor << "."
                              << field_res.field_name
                              << " type=" << field_res.field_type
                              << " oid=" << geo_id
                              << " (clinit_failed="
                              << (clinit_failed ? "true" : "false")
                              << " attempted="
                              << (attempted ? "true" : "false")
                              << " stored_null="
                              << (stored_null ? "true" : "false") << ")"
                              << std::endl;
                } else {
                    result_value.type = DalvikType::NULL_REF;
                    result_value.object_id = 0;
                }
            } else {
                // OpenJDK Integer.java: `public static final Class<Integer>
                // TYPE = int.class;` (and the same for the other boxes) —
                // the primitive Class constants are JVM-injected, never
                // written by <clinit>. With no seed the sget-object answered
                // typed-zero NULL and Array.newInstance(Integer.TYPE, dims)
                // produced a null matrix (FishRingsForAndroid Rings.<init>
                // evidence: int[12][3] board → aput-null NPE in Rings.init).
                // Descriptor: the primitive letters (JLS/DEX spec) — mirrored
                // by the Array.newInstance primitive-component arm below.
                static const std::map<std::string, std::string>
                    k_primitive_type_desc = {
                        {"Ljava/lang/Integer;", "I"},
                        {"Ljava/lang/Boolean;", "Z"},
                        {"Ljava/lang/Byte;", "B"},
                        {"Ljava/lang/Character;", "C"},
                        {"Ljava/lang/Short;", "S"},
                        {"Ljava/lang/Long;", "J"},
                        {"Ljava/lang/Float;", "F"},
                        {"Ljava/lang/Double;", "D"},
                        {"Ljava/lang/Void;", "V"},
                    };
                auto prim = k_primitive_type_desc.find(
                    field_res.class_descriptor);
                if (prim != k_primitive_type_desc.end() &&
                    field_res.field_name == "TYPE") {
                    result_value = DalvikValue::make_class(
                        prim->second, instruction_sequence_);
                    static_field_storage_[static_key] = result_value;
                } else if (field_res.class_descriptor ==
                           "Lorg/json/JSONObject;") {
                // ── F-JSON-NULL (S226; #508 Vector-Pinball chain): the AOSP
                // JSONObject.NULL SENTINEL ────────────────────────────────
                // OpenJDK/Android org.json JSONObject: `public static final
                // Object NULL = new Object()` — the sentinel is a REAL
                // identity object (the docs' "a value equal to Java null"),
                // never Java null itself. The engine ran no framework
                // <clinit> for org.json, so the sget answered typed-zero
                // NULL — and bouncy v43's JSONUtils.objectFromJSONItem
                // (REAL bytecode, disassembled):
                //   0x0000 sget-object v0, Lorg/json/JSONObject;->NULL
                //   0x0004 if-ne v1, v0, +004h        ← != sentinel?
                //   0x0008 const/4 v1, 0             ← null the value
                //   0x000a return-object v1
                // compared every STRING_REF leaf against the null token —
                // the mixed compare saw "no object == no object" and nulled
                // EVERY leaf value before Map.put (MAPPUT val_kind=7 rows,
                // live run) → params.get("class") NPE at
                // FieldElement.createFromParameters pc=16 → onCreate APP
                // BOUNDARY unwind → no table render. Law: the sentinel is
                // minted ONCE (a heap Lorg/json/JSONObject; with
                // json_value="null" — the AOSP identity face) and cached;
                // identity comparisons against it now behave per ART.
                if (field_res.field_name == "NULL") {
                    auto nullit = static_field_storage_.find(static_key);
                    if (nullit == static_field_storage_.end() ||
                        nullit->second.type != DalvikType::OBJECT_REF ||
                        nullit->second.object_id == 0) {
                        uint32_t sid =
                            heap_.allocate("Lorg/json/JSONObject;", pc_, 0);
                        heap_.set_object_field(
                            sid, "json_value",
                            DalvikValue::make_string("null", 0));
                        result_value =
                            DalvikValue::make_object(sid,
                                                     "Lorg/json/JSONObject;");
                        static_field_storage_[static_key] = result_value;
                        static thread_local uint64_t fjsonnull_n = 0;
                        if (fjsonnull_n++ < 4)
                            std::cerr << "[F-JSON-NULL] JSONObject.NULL "
                                         "sentinel minted o"
                                      << sid
                                      << " (AOSP identity object law)"
                                      << std::endl;
                    }
                }
                } else if (field_res.class_descriptor ==
                           "Ljava/nio/charset/StandardCharsets;") {
                // FINAL-CAMPAIGN PHASE 3 (F-NEW-169 face-1):
                // java.nio.charset.StandardCharsets is a JDK platform-constant
                // holder — OpenJDK StandardCharsets.java defines the six
                // charset constants as static finals initialized in
                // <clinit>, which on a live JVM ALWAYS completes. The engine
                // runs no such <clinit> (framework class, no DEX body), so
                // the sget answered null and the first consumer (WhatsApp
                // 08D.<clinit> → Charset.name()) NPE'd → the requesting
                // clinit died leaving its statics unwritten (SGET-MISS →
                // null) → app-baked null-check NPE chain → white screen.
                // Object identity: the SAME heap Charset convention the
                // Charset.forName law uses (__charset_name__ field).
                static const std::map<std::string, std::string>
                    k_standard_charsets = {
                        {"UTF_8", "UTF-8"},
                        {"ISO_8859_1", "ISO-8859-1"},
                        {"US_ASCII", "US-ASCII"},
                        {"UTF_16", "UTF-16"},
                        {"UTF_16BE", "UTF-16BE"},
                        {"UTF_16LE", "UTF-16LE"},
                    };
                auto sc = k_standard_charsets.find(field_res.field_name);
                if (sc != k_standard_charsets.end()) {
                    uint32_t cs_id =
                        heap_.allocate("Ljava/nio/charset/Charset;", pc_, 0);
                    heap_.set_object_field(
                        cs_id, "__charset_name__",
                        DalvikValue::make_string(sc->second, 0));
                    result_value = DalvikValue::make_object(
                        cs_id, "Ljava/nio/charset/Charset;");
                    static_field_storage_[static_key] = result_value;
                }
                } else {
                // M3 FINDING-013 miss-probe: print the missing key and the
                // presence of ANY same-class keys in storage — a clinit that
                // ran but whose writes are invisible here means the two
                // paths disagree on the storage KEY (or engine instance).
                static thread_local uint64_t sget_miss_probe = 0;
                if (sget_miss_probe < 24) {
                    sget_miss_probe++;
                    size_t same_class = 0;
                    std::string sample;
                    for (const auto& [k, v] : static_field_storage_) {
                        if (k.rfind(field_res.class_descriptor + ".", 0) == 0) {
                            same_class++;
                            if (sample.empty()) sample = k;
                        }
                    }
                    std::cerr << "[SGET-MISS] key=" << static_key
                              << " storage_size=" << static_field_storage_.size()
                              << " same_class_keys=" << same_class
                              << " engine=" << (const void*)this
                              << (sample.empty() ? "" : " first=" + sample)
                              << std::endl;
                    // Where did a write with THIS field name land?
                    for (const auto& [k, v] : static_field_storage_) {
                        if (k.find("." + field_res.field_name) !=
                            std::string::npos) {
                            std::cerr << "[SGET-MISS]   landed: " << k
                                      << std::endl;
                        }
                    }
                }
                static_field_storage_[static_key] = result_value;
                }
            }
        }
    }

    // EXP-053: Trace sget-object (for singleton cache observation).
    if (field_res.resolved) {
        static thread_local uint64_t sget_obj_log_count = 0;
        if (sget_obj_log_count < 100) {
            sget_obj_log_count++;
            std::cerr << "[SGET] class=" << current_class_
                      << " method=" << current_method_
                      << " pc=" << pc
                      << " field=" << field_res.class_descriptor << "."
                      << field_res.field_name
                      << " obj_id=" << result_value.object_id
                      << std::endl;
        }
    }

    set_register(dest_reg, result_value);
    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.operands.push_back({"v" + std::to_string(dest_reg), "destination"});
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});
    }

    pc_ = pc + 2;
    return true;
}

bool DalvikExecutionEngine::execute_sput(uint32_t pc, InstructionTrace& trace) {
    // Format: 21c sput vAA, field@BBBB (2 code units)
    // EXP-042 Phase 2 FIX: never return false — advance pc_ on failure.
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }
    
    uint16_t instr = bytecode_[pc];
    uint8_t src_reg = (instr >> 8) & 0xFF;
    uint16_t field_idx = bytecode_[pc + 1];
    
    FieldResolution field_res = resolve_field(field_idx);
    DalvikValue src_val = get_register(src_reg);
    // CONT-126: FIELD-TRACE statics coverage (sput family) — same law and
    // same env gate as the sget hook; read-only diagnostics.
    if (field_res.resolved &&
        field_trace_filter_set() &&
        field_trace_active(field_res.field_name.c_str(),
                           (current_class_ + "." + current_method_).c_str(),
                           field_res.class_descriptor.c_str())) {
        std::cerr << "[FIELD-TRACE] put-static " << current_class_ << "."
                  << current_method_ << " " << field_res.class_descriptor
                  << "." << field_res.field_name << " reg=v"
                  << (int)src_reg << std::endl;
    }
    
    // F-NEW-215: sput is ACTIVE USE (JVMS 5.5) — the write must trigger
    // class initialization exactly like sget, and an ERRONEOUS class must
    // raise NoClassDefFoundError instead of silently writing a static the
    // class's own <clinit> never got to build.
    if (field_res.resolved) {
        ensure_class_initialized(field_res.class_descriptor);
        if (class_clinit_failed(field_res.class_descriptor) &&
            !clinit_exc_already_in_flight()) {  // F-NEW-395: no double-raise at the triggering use
            static std::atomic<uint64_t> f215_sput_n{0};
            if (f215_sput_n.fetch_add(1, std::memory_order_relaxed) < 8) {
                std::cerr << "[F-NEW-215] ACTIVE-USE sput class="
                          << field_res.class_descriptor << " caller="
                          << current_class_ << "." << current_method_
                          << std::endl;
            }
            throw_deferred("Ljava/lang/NoClassDefFoundError;",
                           field_res.class_descriptor +
                               " <clinit> failed previously (erroneous class)",
                           "F-NEW-215");
            pc_ = pc + 2;
            return false;
        }
    }
    
    if (field_res.resolved) {
        std::string static_key = field_res.class_descriptor + "." + field_res.field_name;
        // F-NEW-657 (#588 Games-g2): the sput half of R-NEW-561 — the
        // write lands in the DECLARING class's ONE storage cell. A
        // subclass <clinit> rebind of an inherited static keyed by the
        // access-site class was invisible to the superclass query()'s
        // cell (the chess provider face); key the write at the DEX
        // declarer when the chain declares the static. Engine-synthetic
        // statics (no DEX declarer) keep the ref-class key unchanged.
        std::string f657_decl = static_field_declarer_of(
            field_res.class_descriptor, field_res.field_name);
        if (!f657_decl.empty() && f657_decl != field_res.class_descriptor) {
            static thread_local uint64_t f657_writes = 0;
            if (f657_writes++ < 8)
                std::cerr << "[F-NEW-657] sput declarer-key "
                          << field_res.class_descriptor << "."
                          << field_res.field_name << " -> " << f657_decl
                          << " (caller " << current_class_ << "."
                          << current_method_ << ")" << std::endl;
            static_key = f657_decl + "." + field_res.field_name;
        }
        static_field_storage_[static_key] = src_val;
    }
    
    trace.operands.push_back({"v" + std::to_string(src_reg), "source"});
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});
    
    pc_ = pc + 2;
    return true;
}

bool DalvikExecutionEngine::execute_sput_object(uint32_t pc, InstructionTrace& trace) {
    // Format: 21c sput-object vAA, field@BBBB (2 code units)
    // EXP-042 Phase 2 FIX: never return false — advance pc_ on failure.
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }
    
    uint16_t instr = bytecode_[pc];
    uint8_t src_reg = (instr >> 8) & 0xFF;
    uint16_t field_idx = bytecode_[pc + 1];
    
    FieldResolution field_res = resolve_field(field_idx);
    DalvikValue src_val = get_register(src_reg);
    // CONT-126: FIELD-TRACE statics coverage (sput-object family) — same
    // law and same env gate as the sget hook; read-only diagnostics.
    if (field_res.resolved &&
        field_trace_filter_set() &&
        field_trace_active(field_res.field_name.c_str(),
                           (current_class_ + "." + current_method_).c_str(),
                           field_res.class_descriptor.c_str())) {
        std::cerr << "[FIELD-TRACE] put-static " << current_class_ << "."
                  << current_method_ << " " << field_res.class_descriptor
                  << "." << field_res.field_name << " reg=v"
                  << (int)src_reg << std::endl;
    }
    
    // F-NEW-215: sput-object is ACTIVE USE — same law as sput (init
    // trigger + NoClassDefFoundError on an erroneous class).
    if (field_res.resolved) {
        ensure_class_initialized(field_res.class_descriptor);
        if (class_clinit_failed(field_res.class_descriptor) &&
            !clinit_exc_already_in_flight()) {  // F-NEW-395: no double-raise at the triggering use
            static std::atomic<uint64_t> f215_sputo_n{0};
            if (f215_sputo_n.fetch_add(1, std::memory_order_relaxed) < 8) {
                std::cerr << "[F-NEW-215] ACTIVE-USE sput-object class="
                          << field_res.class_descriptor << " caller="
                          << current_class_ << "." << current_method_
                          << std::endl;
            }
            throw_deferred("Ljava/lang/NoClassDefFoundError;",
                           field_res.class_descriptor +
                               " <clinit> failed previously (erroneous class)",
                           "F-NEW-215");
            pc_ = pc + 2;
            return false;
        }
    }
    
    if (field_res.resolved) {
        std::string static_key = field_res.class_descriptor + "." + field_res.field_name;
        // F-NEW-657: the sput-object declarer-key law — same as the
        // sput scalar half (the sUriMatcher face is an OBJECT static).
        std::string f657_decl = static_field_declarer_of(
            field_res.class_descriptor, field_res.field_name);
        if (!f657_decl.empty() && f657_decl != field_res.class_descriptor) {
            static thread_local uint64_t f657_owrites = 0;
            if (f657_owrites++ < 8)
                std::cerr << "[F-NEW-657] sput-object declarer-key "
                          << field_res.class_descriptor << "."
                          << field_res.field_name << " -> " << f657_decl
                          << " (caller " << current_class_ << "."
                          << current_method_ << ")" << std::endl;
            static_key = f657_decl + "." + field_res.field_name;
        }
        static_field_storage_[static_key] = src_val;
        // S123 DIAG (bounded): where do ContainerHelpers' static writes land?
        if (current_method_ == "<clinit>" &&
            static_key.find("ContainerHelpers") != std::string::npos) {
            std::cerr << "[S123-SPUT-CH] key=" << static_key
                      << " val_type=" << static_cast<int>(src_val.type)
                      << " obj=" << src_val.object_id
                      << " caller=" << current_class_ << "." << current_method_
                      << std::endl;
        }
    } else {
        // M3 FINDING-013 diag: an UNRESOLVED sput-object silently vanishes —
        // exactly the invisible-state-loss class that cost dooz its
        // Lifecycle.State enum. Cap-limited visibility, semantics unchanged.
        static thread_local uint64_t sput_miss_count = 0;
        if (sput_miss_count < 40) {
            sput_miss_count++;
            std::cerr << "[SPUT-UNRESOLVED] field_idx=" << field_idx
                      << " src_class=" << src_val.class_desc
                      << " caller=" << current_class_ << "."
                      << current_method_ << std::endl;
        }
    }
    
    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.operands.push_back({"v" + std::to_string(src_reg), "source"});
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});
    }
    
    pc_ = pc + 2;
    return true;
}

// ============================================================================
// OPCODE IMPLEMENTATIONS — Invokes
// ============================================================================

// ────────────────────────────────────────────────────────────────────────
// F-NEW-249 (CONT-6): STABLE CLASS-TOKEN IDENTITY LAW (Object.getClass).
// ART ClassLinker mints ONE java.lang.Class instance per runtime class —
// identity is observable (==, HashSet<Class>, synchronized(Class), and
// androidx's NavigatorProvider name cache keyed by Class). The engine's
// const-class opcode already honors this via the F-069 class_token_ids_
// map; getClass stamped ref_id = instruction_sequence_, producing a
// DIFFERENT token per call site for the same class. This helper returns
// the stable per-descriptor token: first call allocates the backing heap
// object ("Ljava/lang/Class;" with __referent_desc) exactly like
// const-class, later calls reuse it. Type stays CLASS_REF with
// class_desc = the REFERRED descriptor (existing consumer contract).
// ────────────────────────────────────────────────────────────────────────
DalvikValue DalvikExecutionEngine::make_stable_class_token(
    const std::string& type_desc) {
    if (type_desc.empty())
        return DalvikValue::make_class("Ljava/lang/Class;",
                                       instruction_sequence_);
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
    return DalvikValue::make_class(type_desc, token);
}

bool DalvikExecutionEngine::execute_invoke_virtual(uint32_t pc, InstructionTrace& trace,
                                                  DalvikExecutionResult& result) {
    // Format: 35c [op] {vC..}, method@BBBB
    // EXP-035: Now uses VTable dispatch for proper polymorphic method resolution
    if (pc + 2 >= bytecode_.size()) return false;

    // S24 flow probe (env-gated, bounded): trace p.a (NavHost/NavController
    // R8-merged method) instruction flow — the navigator-attach block
    // (pc ~1240-1404) never executed its state iput while the graph build
    // (pc ~2546 c.h) did; this reveals the actual pc path.
    {
        static thread_local uint64_t s24_flow = 0;
        if (diag_env("MINIANDROID_S24_TRACE") &&
            current_class_ == "Landroidx/navigation/compose/p;" &&
            s24_flow < 120) {
            ++s24_flow;
            std::cerr << "[S24-PA-FLOW] virtual pc=" << pc << std::endl;
        }
    }

    // S58 R-NEW-378 probe (env-gated, bounded): every invoke-virtual from
    // the compose SaveableStateProvider init frame — reveals the
    // ACCEPTABLE_CLASSES loop traffic (isEmpty/size/get/isInstance) and
    // where each dispatch actually landed.
    {
        static thread_local uint64_t je_flow = 0;
        if (diag_env("MINIANDROID_CLASS_LAW_TRACE") &&
            current_class_ == "Lje;" && current_method_ == "<init>" &&
            je_flow < 40) {
            ++je_flow;
            uint16_t je_mi = bytecode_[pc + 1];
            std::cerr << "[JE-FLOW] virtual pc=" << pc
                      << " method_idx=" << je_mi
                      << " -> "
                      << (dex_report_ ? resolve_method_class_for_dex(je_mi, current_dex_index_) : "?")
                      << "."
                      << (dex_report_ ? resolve_method_name_for_dex(je_mi, current_dex_index_) : "?")
                      << std::endl;
        }
    }

    // EXP-071 Phase 7: Save and reset current_invoke_is_static_ to false
    // for invoke-virtual calls. This ensures try_shadow_dispatch correctly
    // treats args[0] as `this` (instance method, not static).
    bool saved_is_static = current_invoke_is_static_;
    current_invoke_is_static_ = false;

    // EXP-062: Debug — trace ALL invoke-virtual entry in PhoneView.<init>
    if (diag_env("MINIANDROID_EXP062_TRACE") && current_class_.find("PhoneView") != std::string::npos &&
        current_method_ == "<init>") {
        auto v1 = get_register(1);
        std::cerr << "[EXP062-ENTRY] invoke-virtual entry pc=" << pc
                  << " v1_type=" << static_cast<int>(v1.type)
                  << " v1_obj=" << v1.object_id
                  << std::endl;
    }

    uint16_t instr = bytecode_[pc];
    // EXP-037 Phase B (BLOCKER-015 FIX): Per AOSP dalvik-bytecode.html,
    // 35c format is "AA|op BBBB FEDC" where:
    //   code[pc+0] = AA|op (arg_count + 5th_reg in high byte, opcode in low byte)
    //   code[pc+1] = BBBB (method_idx, 16-bit)
    //   code[pc+2] = FEDC (register list, 4 nibbles packed)
    // The previous code read method_idx from code[pc+2] and regs from code[pc+1],
    // which is REVERSED. This caused every invoke-* to read the register list
    // as the method_idx (often out-of-bounds) and the method_idx as the
    // register list (corrupted register values).
    uint16_t method_idx = bytecode_[pc + 1];  // method reference (was pc+2)
    uint16_t regs_word = bytecode_[pc + 2];    // register list (was pc+1)
    std::vector<DalvikValue> args;
    std::vector<std::string> arg_names;
    
    // Extract 5 register args (vG, vH, vI, vJ, vK) from 35c encoding
    uint8_t regs[5] = {
        static_cast<uint8_t>(regs_word & 0xF),
        static_cast<uint8_t>((regs_word >> 4) & 0xF),
        static_cast<uint8_t>((regs_word >> 8) & 0xF),
        static_cast<uint8_t>((regs_word >> 12) & 0xF),
        static_cast<uint8_t>((instr >> 8) & 0xF)  // 5th reg (low nibble of AA) — was (instr >> 4) & 0xF
    };
    
    // EXP-045: Only push argc registers (from 35c format: high nibble of high byte)
    uint8_t argc = (instr >> 12) & 0xF;
    for (int i = 0; i < argc && i < 5; ++i) {
        DalvikValue val = get_register(regs[i]);
        args.push_back(val);
        arg_names.push_back(register_name(regs[i]));
    }

    // CYCLE-E: signature-aware param conversion for 35c instance calls.
    // 'F' params hold raw IEEE bits in INT32 registers (const is untyped);
    // 'J'/'D' params occupy TWO registers and must merge into one value.
    // Without this, literal float args (drawText x/y, drawRect edges,
    // drawCircle radius, drawOval/drawArc rects…) reached shadows and
    // callees as huge raw-bit integers and wide args arrived split.
    // F-090i (R-NEW-322): the proto is ALSO the callee's exact descriptor —
    // hoisted so every try_recursive_invoke below passes it (the F-023
    // exact-descriptor overload law can only fire when the descriptor is
    // supplied). Live evidence (dooz): c.a invoked the 1-arg
    // z1/i.addAll(Collection); with no descriptor the arity heuristic
    // executed the 2-arg addAll(I, Collection) body whose elements
    // register stayed unwritten → M1/i.f NPE "parameter elements is
    // null" → NavHost graph build died → Compose never composed.
    std::string invoke_descriptor_35c;
    if (dex_report_) {
        // CONT-96 W3-B: memo entry (proto string + parsed params resolve once).
        const auto& mre = method_resolve_entry(current_dex_index_, method_idx);
        invoke_descriptor_35c = mre.proto;
        if (invoke_descriptor_35c != "<unknown>") {
            args = build_invoke_args(args, mre.proto_params,
                                     /*is_static=*/false);
        } else {
            invoke_descriptor_35c.clear();
        }
    }
    
    // EXP-035: VTable-based method resolution
    std::string static_type = "<unknown>";      // Declared type in bytecode
    std::string runtime_type = "<unknown>";     // Actual type of object
    std::string resolved_method = "<unresolved>";

    // EXP-037 Phase B (BLOCKER-002 FIX): Now that DexReport exposes
    // method_ids[], we can resolve method_idx → method name + declaring class.
    std::string method_name_from_dex = "<method_idx:" + std::to_string(method_idx) + ">";
    std::string declaring_class = "<unknown>";
    if (dex_report_) {
        method_name_from_dex = resolve_method_name_for_dex(method_idx, current_dex_index_);
        declaring_class = resolve_method_class_for_dex(method_idx, current_dex_index_);
    }

    // S24 probe: c.a's addAll receives a null collection — print the arg.
    if (diag_env("MINIANDROID_S24_TRACE") &&
        method_name_from_dex == "addAll" &&
        current_class_ == "Landroidx/navigation/c;") {
        static thread_local uint64_t s24_addall = 0;
        if (s24_addall < 8) {
            ++s24_addall;
            std::cerr << "[S24-ADDALL] caller pc=" << pc
                      << " argc=" << args.size()
                      << " recv_oid="
                      << (args.empty() ? 0 : args[0].object_id)
                      << " elements_type="
                      << (args.size() > 1 ? static_cast<int>(args[1].type)
                                          : static_cast<int>(args[0].type))
                      << " elements_oid="
                      << (args.size() > 1 ? args[1].object_id
                                          : args[0].object_id)
                      << " elements_cls="
                      << (args.size() > 1 ? args[1].class_desc
                                          : args[0].class_desc)
                      << std::endl;
        }
    }
    // ── S173 NDFE probe (env-gated, bounded 96, zero behavior) ──────────
    // Koin 4.x keeps its definition index in a DESUGARED
    // j$/util/concurrent/ConcurrentHashMap (resolveDefinition$koin_core,
    // R8-merged into Lorg/slf4j/event/EventRecodingLogger;, reads it via
    // the merged field slot). The S172 residual NoDefinitionFoundException
    // is ONE index miss for the ':local:'-qualified
    // BaseCatalogFeatureFlagProvider. The index ops never reach
    // bridge_to_api (the CHM lives in the app dex and executes its real
    // bytecode per the F-C4-566 law), so this interpreter-level probe is
    // the only visibility: log the RAW get/put keys for the CHM surface.
    if (diag_env("MINIANDROID_S173_PROBE") &&
        declaring_class.find("ConcurrentHashMap") != std::string::npos &&
        // Only RESOLUTION-time lookups: resolveDefinition$koin_core is
        // R8-merged into EventRecodingLogger. The loadModules put/get
        // churn is already proven (BaseCatalog ':local:' put lands).
        (current_method_.find("resolveDefinition") != std::string::npos ||
         current_class_ == "Lorg/slf4j/event/EventRecodingLogger;")) {
        static thread_local uint64_t s173_chm = 0;
        if (s173_chm < 200 && args.size() >= 2 &&
            args[1].type == DalvikType::STRING_REF) {
            ++s173_chm;
            const std::string& keydesc = args[1].string_val;
            std::cerr << "[S173-CHM-V] " << method_name_from_dex
                      << " argc=" << args.size()
                      << " key=\"" << keydesc << "\""
                      << " caller=" << current_class_ << "."
                      << current_method_ << " pc=" << pc << std::endl;
        }
    }
    
    // ────────────────────────────────────────────────────────────────────
    // F-141 (S72-W3): ART NULL-RECEIVER INVOKE LAW. ART's interpreter
    // throws NullPointerException at the invoke site — BEFORE the callee
    // body executes — when an instance invoke's receiver is null
    // ("Attempt to invoke virtual method '<sig>' on a null object
    // reference"). The old path logged "would be NullPointerException"
    // and dispatched anyway: the callee ran with this=NULL, state
    // corruption compounded silently (dooz PersistentHashMapBuilder
    // putAll trie walk, entry #49 this=NULL → arraycopy(null) NPE at the
    // wrong site — first divergence hidden behind the last symptom,
    // constitution §030/§039/§177).
    // Covers NULL_REF and OBJECT_REF/object_id==0 (engine-wide null).
    // ────────────────────────────────────────────────────────────────────
    if (!args.empty() && f141_is_null_receiver(args[0])) {
            dump_frame_locals_diag("F141-OP");
        // S113 ROOT-059 law: shadow-claimed platform classes route null
        // receivers to the shadow's materialization law instead of the ART
        // NPE — androidx's insets chain (Builder→Impl30→consume*) was built
        // on non-null WindowInsets objects everywhere, and the runtime's
        // platform law provides them. Unclaimed classes keep the
        // ART-faithful throw below.
        // F-NEW-270 (CONT-18h) ROUTE DOMAIN LAW: the route is lawful for
        // FRAMEWORK classes only. ViewShadow's EXP-060 heuristic claims
        // every non-framework class ("could be a View subclass"), so an
        // ungated claims_class() check also captured R8-obfuscated app
        // classes and let their real DEX bodies run with this=null — the
        // wrong-site-exception disease F-141 eliminated (live face: dooz
        // Lhv0;.h→Lhv0;.d iget NPE at pc=17 inside the callee + silent
        // h() swallow). Non-framework classes keep the ART throw.
        // F-NEW-447 (CONT-107): CALLER-DOMAIN GATE on the ROOT-059 route.
        // The routing crutch exists to bridge engine gaps INSIDE framework
        // chains (androidx insets: Builder→Impl30→consume*) — those callers
        // are framework classes. When the CALLER is app DEX code (probe face:
        // Lcom/probe/c106a/MainActivity;.onCreate invoking
        // Landroid/graphics/Paint;.setStrokeWidth on a null never-assigned
        // static Paint), ART throws NPE at the invoke site; the silent
        // shadow route let app code proceed with the null static
        // ([C106-INVOKE2] NO-EXC vs ART NPE — F-NEW-447). Law: route only
        // when the current frame is framework-owned; app-caller sites get
        // the ART-faithful throw below. Unknown caller frames (engine-
        // internal invokes) keep the legacy route.
        const bool f447_caller_is_framework =
            current_class_.empty() || f141_is_framework_class(current_class_);
        if (shadow_registry_ && f141_is_framework_class(declaring_class) &&
            shadow_registry_->claims_class(declaring_class) &&
            f447_caller_is_framework) {
            std::cerr << "[ROOT-059] null-recv routed to shadow law: " << declaring_class
                      << "." << method_name_from_dex
                      << " caller=" << current_class_ << "." << current_method_
                      << std::endl;
            static_type = declaring_class;
            runtime_type = declaring_class;
            resolved_method = declaring_class + "." + method_name_from_dex;
        } else {
        // F-NEW-447 bounded marker: this invoke USED to route to the shadow
        // (ROOT-059); the caller-domain gate keeps ART NPE parity here.
        if (shadow_registry_ && f141_is_framework_class(declaring_class) &&
            shadow_registry_->claims_class(declaring_class) &&
            !f447_caller_is_framework) {
            static thread_local uint64_t f447_npe_n = 0;
            if (f447_npe_n++ < 16)
                std::cerr << "[F447-NPE] app-caller null-recv NPE parity: "
                          << declaring_class << "." << method_name_from_dex
                          << " caller=" << current_class_ << "."
                          << current_method_ << std::endl;
        }
        // F-141 DIAG (env-gated, bounded, remove after root closure §112-114):
        // dump the receiver value identity + current frame register window —
        // answers "which register carried the null receiver".
        if (diag_env("MINIANDROID_F141_DIAG") && current_registers_) {
            std::cerr << "[F141-DIAG] " << current_class_ << "."
                      << current_method_ << " pc=" << pc_
                      << " recv_type=" << static_cast<int>(args[0].type)
                      << " recv_oid=" << args[0].object_id
                      << " recv_cls=" << args[0].class_desc
                      << " bytecode_pc_range=[";
            for (uint32_t d = 0; d < 12 && pc_ + d < bytecode_.size(); ++d)
                std::cerr << std::hex << bytecode_[pc_ + d] << std::dec << " ";
            std::cerr << "] regs:";
            int dumped = 0;
            for (const auto& [rid, val] : current_registers_->get_snapshot()) {
                if (dumped++ >= 24) break;
                std::cerr << " " << rid << ":t" << static_cast<int>(val.type)
                          << "/o" << val.object_id;
            }
            std::cerr << std::endl;
        }
        throw_deferred("Ljava/lang/NullPointerException;",
                       "Attempt to invoke virtual method '" +
                           declaring_class + "." + method_name_from_dex +
                           "' on a null object reference",
                       "f141-null-recv");
        pc_ += 3;  // 35c length; a catch handler redirect overrides pc
        return true;
        }
    }

    // Get the object reference (first arg is 'this' for virtual calls)
    if (!args.empty() && args[0].type == DalvikType::OBJECT_REF &&
        !(args[0].object_id == 0)) {
        DalvikValue this_obj = args[0];
        static_type = this_obj.class_desc;

        // Look up actual object class from heap
        if (auto* heap_obj = heap_.get(this_obj.object_id)) {
            runtime_type = heap_obj->class_descriptor;
            resolved_method = runtime_type + "." + method_name_from_dex;
        } else {
            // Object not in heap - use static type as fallback
            runtime_type = static_type;
            resolved_method = static_type + "." + method_name_from_dex;
            log("⚠️ INVOKE-VIRTUAL: Object not found in heap, using static type");
        }

        // EXP-061: Debug — trace addView calls to find why child=0
        if (method_name_from_dex == "addView" && args.size() >= 2) {
            std::cerr << "[EXP062-ADDVIEW-TRACE] invoke-virtual addView"
                      << " argc=" << args.size()
                      << " this_id=" << args[0].object_id
                      << " this_class=" << runtime_type
                      << " child_type=" << static_cast<int>(args[1].type)
                      << " child_id=" << args[1].object_id
                      << " child_class=" << args[1].class_desc;
            for (size_t ai = 2; ai < args.size(); ++ai)
                std::cerr << " a" << ai << "=t" << static_cast<int>(args[ai].type)
                          << "/v" << (args[ai].type == DalvikType::OBJECT_REF
                                          ? args[ai].object_id
                                          : (int64_t)args[ai].int_val);
            std::cerr << " caller=" << current_class_ << "." << current_method_
                      << " pc=" << pc
                      << std::endl;
        }

        // R-NEW-347 (S42) diagnostic: where does the DEX-driven
        // View.measure(wSpec, hSpec) call go? Bounded probe (8 hits) —
        // remove after the measure chain is proven.
        if (method_name_from_dex == "measure") {
            static thread_local uint64_t r347_mprobe = 0;
            if (r347_mprobe < 8) {
                ++r347_mprobe;
                std::cerr << "[R347-MPROBE] invoke-virtual measure"
                          << " runtime=" << runtime_type
                          << " declaring=" << declaring_class
                          << " argc=" << args.size()
                          << " recv=" << (args.empty() ? 0 : args[0].object_id)
                          << " a1t=" << (args.size() > 1 ? static_cast<int>(args[1].type) : -1)
                          << " a2t=" << (args.size() > 2 ? static_cast<int>(args[2].type) : -1)
                          << " caller=" << current_class_ << "." << current_method_
                          << std::endl;
            }
        }

        // EXP-062: Debug — trace v1 in PhoneView.<init> after each invoke-virtual
        // EXP-063: Also trace getResourceEntryName
        if (method_name_from_dex == "getResourceEntryName" && args.size() >= 2) {
            std::cerr << "[EXP063-RES-ARGS] getResourceEntryName"
                      << " this_id=" << args[0].object_id
                      << " this_type=" << static_cast<int>(args[0].type)
                      << " resid_type=" << static_cast<int>(args[1].type)
                      << " resid=" << args[1].int_val
                      << " caller=" << current_class_ << "." << current_method_
                      << " pc=" << pc
                      << std::endl;
        }
        if (current_class_.find("PhoneView") != std::string::npos &&
            current_method_ == "<init>" && !args.empty()) {
            auto v1 = get_register(1);
            std::cerr << "[EXP062-V1] invoke-virtual " << method_name_from_dex
                      << " pc=" << pc
                      << " v1_type=" << static_cast<int>(v1.type)
                      << " v1_obj=" << v1.object_id
                      << " this_type=" << static_cast<int>(args[0].type)
                      << " this_obj=" << args[0].object_id
                      << std::endl;
        }
    } else {
        // No object reference or null - can't do virtual dispatch
        if (args.empty()) {
            log("❌ INVOKE-VIRTUAL: No arguments provided");
        } else if (args[0].type == DalvikType::NULL_REF) {
            log("⚠️ INVOKE-VIRTUAL: Null object reference (would be NullPointerException)");
        }
        resolved_method = (declaring_class.empty() ? static_type : declaring_class) +
                          "." + method_name_from_dex;
    }
    
    // S109 forensics: trace setFragmentStack dispatch end-to-end.
    if (method_name_from_dex == "setFragmentStack") {
        static thread_local uint64_t sfs_n = 0;
        if (sfs_n < 10) {
            ++sfs_n;
            std::cerr << "[S109-SFS] invoke-virtual entry pc=" << pc
                      << " declaring=" << declaring_class
                      << " runtime=" << runtime_type
                      << " argc=" << args.size()
                      << " a0=" << (args.empty() ? -1 : (int)args[0].type)
                      << " o0=" << (args.empty() ? 0 : args[0].object_id)
                      << " a1=" << (args.size() > 1 ? (int)args[1].type : -1)
                      << " o1=" << (args.size() > 1 ? args[1].object_id : 0)
                      << " caller=" << current_class_ << "." << current_method_
                      << std::endl;
        }
    }
    // Try API bridge with resolved method info
    DalvikValue return_val = DalvikValue::make_void();
    ApiCallTrace::Status api_status = ApiCallTrace::Status::STUBBED;

    // EXP-079: Debug — trace onNextPressed dispatch specifically
    if (method_name_from_dex == "onNextPressed" || method_name_from_dex == "onDoneButtonPressed") {
        std::cerr << "[EXP079-DISPATCH] method=" << method_name_from_dex
                  << " declaring_class=" << declaring_class
                  << " runtime_type=" << runtime_type
                  << " static_type=" << static_type
                  << " args[0]_type=" << (args.empty() ? -1 : (int)args[0].type)
                  << " args[0]_obj=" << (args.empty() ? 0 : args[0].object_id)
                  << " args[0]_class=" << (args.empty() ? "" : args[0].class_desc)
                  << std::endl;
    }

    // [S34-TSTATE] NavigatorState.createBackStackEntry dispatch forensics
    if (declaring_class == "Lh1/t;" && method_name_from_dex == "a") {
        static thread_local uint64_t tstate_n = 0;
        ++tstate_n;
        if (tstate_n <= 12) {
            std::cerr << "[S34-TSTATE] h1/t.a entry #" << tstate_n
                      << " runtime_type=" << runtime_type
                      << " recv=o" << (args.empty() ? 0 : args[0].object_id)
                      << " cls=" << (args.empty() ? "?" : args[0].class_desc);
            for (size_t ai = 1; ai < args.size() && ai < 3; ++ai)
                std::cerr << " a" << ai << "=o" << args[ai].object_id
                          << (args[ai].is_null ? "(NULL)" : "");
            std::cerr << std::endl;
        }
    }
    // EXP-038 (BLOCKER-034): Try recursive DEX method invocation first.
    // If the target method exists in DEX with bytecode, execute it recursively
    // instead of bridging to the API stub layer. This enables real execution
    // of helper methods (e.g., ApplicationLoader.init, AndroidUtilities, etc.)
    bool recursively_invoked = false;
    if (config_.enable_api_bridge) {
        // EXP-059: Polymorphism fix — invoke-virtual must dispatch using the
        // receiver's RUNTIME type, not the static declaring class from the
        // method_idx. Otherwise `BaseFragment.createView` (declared in the
        // base class) would be called instead of `MainTabsActivity.createView`
        // (the override that actually builds the UI).
        //
        // Strategy:
        //   1. If runtime_type is a known subclass of declaring_class, try
        //      the runtime_type FIRST. If it has the method, dispatch there.
        //   2. If the runtime_type doesn't have the method (or fails), fall
        //      back to the declaring_class (which is what the bytecode
        //      reference points to).
        bool tried_runtime_type = false;
        if (!args.empty() && args[0].type == DalvikType::OBJECT_REF &&
            runtime_type != "<unknown>" && runtime_type != declaring_class) {
            // Try the runtime type first — this is the polymorphic dispatch.
            if (try_recursive_invoke(runtime_type, method_name_from_dex,
                                     args, return_val, result,
                                     invoke_descriptor_35c)) {
                recursively_invoked = true;
                tried_runtime_type = true;
                api_status = ApiCallTrace::Status::IMPLEMENTED;
                last_invoke_return_ = return_val;
            }
        }
        // M3 F-020 ROOT FIX (§ ART vtable law — most-derived override):
        // after the runtime type misses, ART walks the RECEIVER's class
        // hierarchy IN ORDER (LP/a → LP/b → LP/g): the first level that
        // declares the method wins. The previous code jumped straight to
        // the STATIC declaring class, skipping intermediate overrides —
        // so Snapshot.s(I) (setWriteCount, overridden by MutableSnapshot
        // LP/b to store the count) executed the base LP/g.s which always
        // throws "Updating write count is not supported" → dooz ISE inside
        // setValue. Walk the chain via class_to_superclass_ (C013 map),
        // stopping at the declaring class; the declaring-class fallback
        // below remains the last resort for receivers whose hierarchy is
        // unknown (pure framework receivers).
        if (!recursively_invoked && !args.empty() &&
            args[0].type == DalvikType::OBJECT_REF &&
            runtime_type != "<unknown>" && runtime_type != declaring_class) {
            std::string f020_cur = runtime_type;
            int f020_guard = 0;
            while (!f020_cur.empty() && f020_guard++ < 12 &&
                   f020_cur != declaring_class &&
                   f020_cur != "Ljava/lang/Object;") {
                auto sup_it = class_to_superclass_.find(f020_cur);
                if (sup_it == class_to_superclass_.end()) break;
                const std::string& sup = sup_it->second;
                if (sup.empty() || sup == f020_cur) break;
                f020_cur = sup;
                if (f020_cur == "Ljava/lang/Object;") break;
                if (try_recursive_invoke(f020_cur, method_name_from_dex,
                                         args, return_val, result,
                                         invoke_descriptor_35c)) {
                    recursively_invoked = true;
                    api_status = ApiCallTrace::Status::IMPLEMENTED;
                    last_invoke_return_ = return_val;
                    break;
                }
            }
        }
        if (!tried_runtime_type && !recursively_invoked) {
            // M3 F-020: also gate on !recursively_invoked — a successful
            // hierarchy-walk dispatch above (most-derived override law)
            // must not be overwritten by the static declaring-class body.
            // Use declaring_class from method_ids[] for lookup
            if (try_recursive_invoke(declaring_class, method_name_from_dex,
                                     args, return_val, result,
                                     invoke_descriptor_35c)) {
                recursively_invoked = true;
                api_status = ApiCallTrace::Status::IMPLEMENTED;
                // EXP-057: CRITICAL FIX — must update last_invoke_return_ after
                // recursive invoke so move-result/move-result-object can read it.
                // try_recursive_invoke restores last_invoke_return_ to the saved
                // value internally, so we must re-set it from return_val here.
                // Without this, move-result-object reads stale VOID_ from a
                // previous method's return-void.
                last_invoke_return_ = return_val;
            }
        }
        // ── CONT-12 F-NEW-266 ─────────────────────────────────────────────
        // ART/JVMS 5.4.5: after the class chain misses, virtual resolution
        // continues into the receiver's TRANSITIVELY IMPLEMENTED INTERFACES
        // (default methods). The pre-266 path fell to the API bridge whose
        // stub silently returned null — the null fed the next instruction
        // (un-renamed Compose 1.11.4 oracle face: root$1$1.then(other) →
        // interface Modifier.then default body → null → chained
        // invoke-interface receiver NPE ×172 → setContent dead).
        if (!recursively_invoked && !args.empty() &&
            args[0].type == DalvikType::OBJECT_REF &&
            !runtime_type.empty() && runtime_type != "<unknown>") {
            std::string f266_dispatched;
            if (try_interface_default_invoke(
                    runtime_type, method_name_from_dex, invoke_descriptor_35c,
                    args, return_val, result, &f266_dispatched)) {
                recursively_invoked = true;
                api_status = ApiCallTrace::Status::IMPLEMENTED;
                last_invoke_return_ = return_val;
                // S157-B: trace_cap==0 gate (never-read trace).
                if (config_.trace_cap > 0) {
                trace.invoked_method = f266_dispatched +
                    " [default-method " + invoke_descriptor_35c + "]";
                }
            }
        }
    }

    if (declaring_class == "Lh1/t;" && method_name_from_dex == "a") {
        static thread_local uint64_t tstate_r = 0;
        ++tstate_r;
        if (tstate_r <= 12) {
            std::cerr << "[S34-TSTATE-RES] h1/t.a #" << tstate_r
                      << " recursively_invoked=" << (recursively_invoked ? 1 : 0)
                      << " runtime=" << runtime_type
                      << " status=" << (int)api_status;
            if (return_val.type == DalvikType::OBJECT_REF)
                std::cerr << " ret=o" << return_val.object_id;
            std::cerr << std::endl;
        }
    }
    if (!recursively_invoked && config_.enable_api_bridge) {
        // Use declaring_class (the static type from method_ids[]) if
        // runtime_type is unknown — this lets us route framework calls like
        // android.app.Activity.onCreate to the API stub layer.
        std::string api_class = (runtime_type != "<unknown>") ? runtime_type : declaring_class;
        // M3 FINDING-011 diag (bounded): does the View tag bridge entry fire?
        if (method_name_from_dex == "setTag" || method_name_from_dex == "getTag" ||
            method_name_from_dex == "obtainStyledAttributes") {
            static thread_local uint64_t tag_entry = 0;
            if (tag_entry < 16) {
                tag_entry++;
                std::cerr << "[TAG-ENTRY] bridge_to_api " << api_class << "."
                          << method_name_from_dex << " argc=" << args.size()
                          << " caller=" << current_class_ << "." << current_method_
                          << std::endl;
            }
        }
        bridge_to_api(api_class, method_name_from_dex, args, return_val, api_status, method_idx); last_invoke_return_ = return_val;
        // ── F-NEW-271 LAW DIAG (collection add/remove channel, env-gated
        // MINIANDROID_F271_COLL_TRACE, bounded, read-only). The F271-WRITE
        // face (dooz Lnb0.p pc=1553 storing STRING_REF "" into Lnb0.j:Lqb0)
        // is served by the CollectionShadow remove(int) channel: a slot that
        // stored a NULL/zero-ref element (kind-2 + "" null-element
        // representation) is served back as handled_string("") → STRING_REF/0
        // — an alien type ART would never produce (ArrayList.remove of a null
        // element returns typed null). This trace records BOTH directions of
        // the channel with the live arg kinds and the served value so the
        // first incorrect state (a legal add(null) vs a zero-ref OBJECT arg
        // fed by an upstream conversion defect) is evidence, not guesswork.
        if (diag_env("MINIANDROID_F271_COLL_TRACE") &&
            (method_name_from_dex == "add" || method_name_from_dex == "remove" ||
             method_name_from_dex == "removeAt" || method_name_from_dex == "removeFirst" ||
             method_name_from_dex == "removeLast" || method_name_from_dex == "pop" ||
             method_name_from_dex == "poll" || method_name_from_dex == "pollLast") &&
            (api_class.find("Ljava/util/ArrayList;") != std::string::npos ||
             api_class.find("Ljava/util/ArrayDeque;") != std::string::npos ||
             api_class.find("Ljava/util/LinkedList;") != std::string::npos)) {
            static thread_local uint64_t f271_coll_n = 0;
            if (f271_coll_n < 100) {
                ++f271_coll_n;
                std::cerr << "[F271-COLL] " << method_name_from_dex
                          << " recv=" << api_class
                          << " recv_id=" << (!args.empty() ? args[0].object_id : 0)
                          << " argc=" << args.size();
                for (size_t fci = 1; fci < args.size() && fci <= 3; ++fci) {
                    std::cerr << " a" << fci << ":t"
                              << static_cast<int>(args[fci].type) << "/o"
                              << args[fci].object_id;
                    if (args[fci].type == DalvikType::STRING_REF)
                        std::cerr << "(\"" << args[fci].string_val.substr(0, 24) << "\")";
                }
                std::cerr << " -> served t"
                          << static_cast<int>(return_val.type) << "/o"
                          << return_val.object_id;
                if (return_val.type == DalvikType::STRING_REF)
                    std::cerr << "(\"" << return_val.string_val.substr(0, 24) << "\")";
                std::cerr << " caller=" << current_class_ << "."
                          << current_method_ << " pc=" << pc << std::endl;
            }
        }
    }

    // EXP-094 (CM-018): Record the receiver of a successful "setParams" call.
    // Multi-page apps instantiate several same-class page views; the one the
    // app actively configures via setParams IS the current page. The render
    // stage uses this to pick the correct render root (see stage_render_frame).
    if (method_name_from_dex == "setParams" && !args.empty() &&
        args[0].type == DalvikType::OBJECT_REF && args[0].object_id != 0) {
        last_set_params_view_ = args[0].object_id;
        std::cerr << "[EXP094-SETPARAMS] active page view = obj#" << last_set_params_view_
                  << " class=" << args[0].class_desc << std::endl;
    }
    
    // Create API call trace with VTable information
    // GP S223 CALL-004 (issue #582): the 35c trace now carries the EXACT
    // descriptor (already resolved above for the F-023 overload law —
    // invoke_descriptor_35c) and the call's execution time; caller method
    // and PC were already present.
    ApiCallTrace api_trace;
    api_trace.sequence = api_call_sequence_++;
    api_trace.api_class = runtime_type;  // Use runtime type for accuracy
    api_trace.method = method_name_from_dex;
    api_trace.descriptor = invoke_descriptor_35c;   // CALL-004
    api_trace.arguments = arg_names;
    api_trace.return_value = return_val.to_string();
    api_trace.status = api_status;
    api_trace.pc = pc;
    api_trace.frame_id = call_stack_.empty() ? 0 : call_stack_.top().frame_id;
    note_api_status(api_trace);  // F-NEW-200 census
    
    batched_cap_push(result.api_call_traces, result.api_call_ring_cursor, static_cast<size_t>(config_.api_call_trace_cap), std::move(api_trace));
    
    // EXP-035: Evidence trace with VTable dispatch information
    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.invoked_method = resolved_method;
    trace.operands.push_back({"args", std::to_string(arg_names.size())});
    trace.operands.push_back({"method_idx", std::to_string(method_idx)});
    trace.operands.push_back({"method_name", method_name_from_dex});
    trace.operands.push_back({"static_type", static_type});       // CRITICAL EVIDENCE
    trace.operands.push_back({"runtime_type", runtime_type});     // CRITICAL EVIDENCE
    trace.operands.push_back({"resolved_method", resolved_method}); // CRITICAL EVIDENCE
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});  // MANDATORY TAG
    }

    // EXP-071 Phase 7: Restore the saved static flag.
    current_invoke_is_static_ = saved_is_static;
    pc_ = pc + 3;
    return true;
}

// EXP-037 Phase B (BLOCKER-012): invoke-super
// Format: 35c [op {vC..vG, vF}], method@BBBB
//   instr_word[0] = opcode | (arg_count << 4)
//   instr_word[1] = packed register args (4 nibbles)
//   instr_word[2] = method_idx
//
// Semantics (per AOSP dexlib2):
//   invoke-super dispatches a virtual method starting from the SUPERCLASS
//   of the static type of `this`, NOT the runtime type. This is critical
//   for `super.onCreate(bundle)` calls — the call site declares the parent
//   class explicitly so the runtime must walk to that class's vtable slot
//   rather than using the runtime-type vtable.
//
//   Without this opcode, NO real Android app can execute past PC=0 of its
//   onCreate method, because `super.onCreate(bundle)` is always the first
//   instruction in user onCreate() implementations.
//
// Implementation:
//   Since BLOCKER-002 (method_ids[] parsing) is still open, we cannot yet
//   resolve method_idx → method name from the DEX. We degrade gracefully:
//   1. Log the invoke-super attempt with method_idx.
//   2. Bridge to API layer (which currently has stub onCreate handler).
//   3. Advance PC by 3 (35c format = 3 code units).
//   4. Do NOT halt — let execution continue to the next instruction.
//
// When BLOCKER-002 lands, this method should be rewritten to:
//   1. Look up method_idx in DexReport::method_ids[] to get the
//      declaring class + method name + descriptor.
//   2. Resolve the parent class of `this`'s static type.
//   3. Walk the parent's virtual_methods[] to find the matching method.
//   4. Recursively invoke execute_method_internal() on that method.
bool DalvikExecutionEngine::execute_invoke_super(uint32_t pc, InstructionTrace& trace,
                                                  DalvikExecutionResult& result) {
    // Format: 35c — 3 code units (6 bytes)
    if (pc + 2 >= bytecode_.size()) {
        log("❌ INVOKE-SUPER: PC out of bounds");
        return false;
    }

    uint16_t instr = bytecode_[pc];
    // EXP-037 Phase B (BLOCKER-015 FIX): 35c format is "AA|op BBBB FEDC"
    //   code[pc+0] = AA|op
    //   code[pc+1] = BBBB (method_idx)
    //   code[pc+2] = FEDC (register list)
    uint16_t method_idx = bytecode_[pc + 1];  // was pc+2
    uint16_t regs_word = bytecode_[pc + 2];    // was pc+1

    // 35c register encoding: 5 nibbles packed
    //   vA = high nibble of opcode word = arg count (typically 1 or 2)
    //   vG = low nibble of opcode word = 5th register (or 0 if vA < 5)
    //   vC..vF = 4 nibbles of regs_word
    // EXP-037 Phase B (BLOCKER-016 FIX): 35c format AA|op where AA = high byte.
// arg_count = HIGH NIBBLE of AA = (instr >> 12) & 0xF (was (instr >> 4) & 0xF — wrong)
// 5th_reg   = LOW NIBBLE of AA  = (instr >> 8) & 0xF (was (instr >> 4) & 0xF — wrong)
uint8_t arg_count = static_cast<uint8_t>((instr >> 12) & 0xF);
    uint8_t regs[5] = {
        static_cast<uint8_t>(regs_word & 0xF),
        static_cast<uint8_t>((regs_word >> 4) & 0xF),
        static_cast<uint8_t>((regs_word >> 8) & 0xF),
        static_cast<uint8_t>((regs_word >> 12) & 0xF),
        static_cast<uint8_t>((instr >> 8) & 0xF)  // 5th reg (low nibble of AA) — was (instr >> 4) & 0xF
    };

    // Read up to arg_count registers (cap at 5 for 35c format)
    std::vector<DalvikValue> args;
    std::vector<std::string> arg_names;
    uint8_t n_args = std::min<uint8_t>(arg_count, 5);
    for (uint8_t i = 0; i < n_args; ++i) {
        DalvikValue val = get_register(regs[i]);
        args.push_back(val);
        arg_names.push_back(register_name(regs[i]));
    }

    // CYCLE-E: signature-aware param conversion for 35c instance calls
    // (super). See execute_invoke_virtual for the full rationale.
    // F-NEW-284: proto_35c is declared at dispatch scope (not inside the
    // dex_report_ guard) so the super-dispatch arm can pass it to
    // try_recursive_invoke as the F-023 exact-descriptor authority. Empty
    // when the proto is unresolvable — legacy behavior preserved.
    std::string proto_35c;
    if (dex_report_) {
        // CONT-96 W3-B: memo entry (proto string + parsed params resolve once).
        const auto& mre = method_resolve_entry(current_dex_index_, method_idx);
        proto_35c = mre.proto;
        if (proto_35c != "<unknown>") {
            args = build_invoke_args(args, mre.proto_params,
                                     /*is_static=*/false);
        } else {
            proto_35c.clear();
        }
    }

    // EXP-037 Phase B (BLOCKER-002 + BLOCKER-012): Now that DexReport exposes
    // method_ids[], we can resolve method_idx → method name + declaring class.
    std::string method_name = "<method_idx:" + std::to_string(method_idx) + ">";
    std::string declaring_class = "<unknown>";
    if (dex_report_) {
        method_name = resolve_method_name_for_dex(method_idx, current_dex_index_);
        declaring_class = resolve_method_class_for_dex(method_idx, current_dex_index_);
    }

    // Identify `this` (first arg) for diagnostic logging
    std::string runtime_type = "<unknown>";
    std::string static_type = "<unknown>";
    std::string resolved_method = declaring_class + "." + method_name + " (super)";

    // F-141 (S72-W3): ART null-receiver law — invoke-super with a null
    // receiver throws NPE at the call site before the ancestor body runs
    // (ART DoInvoke → ThrowNullPointerExceptionFromInterpreter). Old
    // behavior logged "would be NullPointerException on real Android"
    // and dispatched with this=NULL.
    if (!args.empty() && f141_is_null_receiver(args[0])) {
            dump_frame_locals_diag("F141-OP");
        throw_deferred("Ljava/lang/NullPointerException;",
                       "Attempt to invoke super method '" + declaring_class +
                           "." + method_name + "' on a null object reference",
                       "f141-null-recv");
        pc_ += 3;  // 35c length; a catch handler redirect overrides pc
        return true;
    }

    if (!args.empty() && args[0].type == DalvikType::OBJECT_REF) {
        const DalvikValue& this_obj = args[0];
        static_type = this_obj.class_desc;
        if (auto* heap_obj = heap_.get(this_obj.object_id)) {
            runtime_type = heap_obj->class_descriptor;
        } else {
            runtime_type = static_type;
        }
    } else if (!args.empty() && args[0].type == DalvikType::NULL_REF) {
        log("⚠️ INVOKE-SUPER: Null `this` reference (would be NullPointerException on real Android)");
        runtime_type = "<null>";
    } else {
        log("⚠️ INVOKE-SUPER: First argument is not an object reference (arg_count=" +
            std::to_string(arg_count) + ", arg[0].type=" +
            std::to_string(static_cast<int>(args.empty() ? DalvikType::UNINITIALIZED : args[0].type)) + ")");
    }

    log("📞 INVOKE-SUPER: " + declaring_class + "." + method_name +
        " (method_idx=" + std::to_string(method_idx) +
        ", arg_count=" + std::to_string(arg_count) +
        ", static_type=" + static_type +
        ", runtime_type=" + runtime_type + ")");

    // Bridge to API layer — for super.onCreate(), the API layer provides
    // the framework's Activity.onCreate implementation (window setup, etc.).
    DalvikValue return_val = DalvikValue::make_void();
    ApiCallTrace::Status api_status = ApiCallTrace::Status::STUBBED;

    // EXP-038 (BLOCKER-034): Try recursive invocation for super calls too.
    bool recursively_invoked = false;
    // F-NEW-284 (CONT-28): the call-site proto is the F-023 overload law's
    // AUTHORITY here too — the proto was already resolved above for the
    // EXP-095 arg conversion but was NOT passed to the dispatcher, so every
    // super-dispatch selected overloads by SHAPE. Real-Compose oracle proof
    // (proto-free selection, JVMS 5.4.5): NodeCoordinator declares TWO
    // same-name 32-unit overloads placeAt-f8xVGno(JF, GraphicsLayer)V and
    // placeAt-f8xVGno(JF, Function1)V; LayoutModifierNodeCoordinator.
    // placeAt(JF, Function1)V invoke-super'd without a descriptor, the
    // loose shape loop hit the GraphicsLayer body first, its `layer` param
    // register received the Function1 lambda, placeSelf carried the lambda
    // into the explicitLayer slot, and GraphicsLayerOwnerLayer ended up
    // with a lambda where its GraphicsLayer belongs — every later
    // GraphicsLayer.setPosition/record died f141-null-recv on the missing
    // impl field (the draw-pipeline APP BOUNDARY). The proto restores
    // exact-descriptor selection; without one the legacy behavior is
    // byte-identical (descriptor=="" keeps the old path).
    if (config_.enable_api_bridge) {
        if (try_recursive_invoke(declaring_class, method_name, args, return_val, result,
                                 proto_35c)) { last_invoke_return_ = return_val;
            recursively_invoked = true;
            api_status = ApiCallTrace::Status::IMPLEMENTED;
        }
    }
    if (!recursively_invoked && config_.enable_api_bridge) {
        // ── CONT-130 (F-NEW-471 SLICE 2): SUPERCLASS-CHAIN SUPER RESOLUTION ─
        // Byte-level ground truth (scripts/cont130_dex_truth.py, tictactoe v3
        // classes.dex, class_def[1563] @ class_data_off 0x3185fe): the
        // engine's class_data walk is BYTE-EXACT (DM diffs 1135/1/38 =
        // <clinit>/<init>/init; 49 VM diffs resolving 1137..1196 with 1184
        // SKIPPED by the encoded diff stream — the dex genuinely does NOT
        // declare AndroidApplication.onCreate while method_ids[1184]
        // references it for the invoke-super in AndroidLauncher.onCreate).
        // That is a NORMAL dex shape: a method_ids entry is a REFERENCE
        // pool slot, not a declaration; ART resolves the super-call by
        // walking the superclass chain (JVMS 5.4.3.3) — an app-parsed
        // ancestor's body if one declares it, else the first framework
        // ancestor (the F-NEW-324 boundary, already landed). The engine's
        // super path only tried the EXACT declaring class, so a
        // declared-ancestor super-call silently shadow-fallbacked.
        // LAW: after the exact-class miss, walk the app-parsed superclass
        // chain (the F-074/S21 walker, receiver identity preserved,
        // 16-hop cap) BEFORE the shadow bridge. Strictly closer to ART:
        // only reachable when the exact class missed, and a chain hit is
        // a real DEX body the old path never ran. Framework-bottomed
        // chains (tictactoe AndroidApplication→Activity) still resolve
        // through the F-NEW-324 boundary law — unchanged byte path.
        if (try_recursive_invoke_on_super(declaring_class, method_name, args,
                                          return_val, result, proto_35c)) {
            last_invoke_return_ = return_val;
            recursively_invoked = true;
            api_status = ApiCallTrace::Status::IMPLEMENTED;
            static std::atomic<uint64_t> f471_chain_n{0};
            if (f471_chain_n.fetch_add(1, std::memory_order_relaxed) < 40) {
                std::cerr << "[F-NEW-471-SUPER-CHAIN] super-call "
                          << declaring_class << "." << method_name
                          << " not declared locally; dispatched via"
                          << " app-parsed superclass chain (ART 5.4.3.3)"
                          << " caller=" << current_class_ << "."
                          << current_method_ << std::endl;
            }
        }
    }
    if (!recursively_invoked && config_.enable_api_bridge) {
        // ── CONT-127 (F-NEW-471 SLICE 1) + CONT-130 RECLASSIFICATION ────────
        // Byte truth (cont130_dex_truth.py): method_ids is a REFERENCE pool,
        // not a declaration table — a reference whose class declares no such
        // method in class_data is a NORMAL dex shape resolved by superclass
        // resolution, NOT evidence of a parse desync. The engine's
        // class_data walk was re-verified byte-exact for tictactoe v3
        // (class_def[1563]: 3 DM + 49 VM, diffs self-consistent, names
        // addAndroidEventListener..useImmersiveMode — onCreate omitted by
        // the dex itself). After SLICE 2's chain walk, reaching this point
        // means the whole app-parsed chain lacks a body: the call resolves
        // onto the first FRAMEWORK ancestor (F-NEW-324 boundary law below)
        // — the ART-equivalent shadow target. This log now DOCUMENTS that
        // resolution (bounded); it no longer claims a parse gap.
        if (dex_report_) {
            const auto& mre = method_resolve_entry(current_dex_index_,
                                                   method_idx);
            if (mre.cls == declaring_class && mre.name == method_name) {
                static std::atomic<uint64_t> f471_gap_n{0};
                if (f471_gap_n.fetch_add(1, std::memory_order_relaxed) < 40) {
                    std::cerr << "[F-NEW-471-RES-GAP] super-call "
                              << declaring_class << "." << method_name
                              << " method_id=" << method_idx
                              << " has no declaration in class_data or any"
                              << " app-parsed superclass (reference-only"
                              << " method_ids slot) — framework-boundary"
                              << " shadow dispatch (ART-equivalent)"
                              << " caller=" << current_class_ << "."
                              << current_method_ << std::endl;
                }
            }
        }
        // R-NEW-345 SUPER-DISPATCH IDENTITY LAW: pass the CLEAN declaring
        // class into the bridge. ART super-dispatch resolves the SAME
        // receiver/method identity as virtual dispatch; the old "<super>"
        // marker leaked into dispatch identity, so every framework-ancestor
        // super call silently missed its shadow — kotlinx scheduler
        // Worker.start() { super.start() } → Thread.start() never reached
        // ThreadShadow (no worker ever ran: runBlocking/BlockingCoroutine
        // spun forever in joinBlocking). Marker kept in the api_trace log
        // line below only.
        //
        // ── F-NEW-324 (CONT-52): the super-dispatch BOUNDARY law. When the
        // declaring class is a DEX-defined INTERMEDIATE that does not
        // define the method (NavigationView.onMeasure does invoke-super
        // f.onMeasure where f = ScrimInsetsFrameLayout is a DEX class with
        // NO onMeasure whose super is the FrameLayout boundary), ART
        // resolution continues PAST the DEX chain onto the FIRST framework
        // ancestor — the bridge must see THAT boundary class, not the DEX
        // declaring class, or every shadow keyed by a framework name
        // silently misses: the FrameLayout.onMeasure measure law never
        // ran, setMeasuredDimension was never reached, and the engine
        // recorded [DEX-MEASURE] NavigationView.onMeasure
        // "FAILED(no write-back)" on every pass → the whole drawer menu
        // measured 0x0 and the NavigationView node never entered the
        // render tree. Walk the DEX superclass chain up from the declaring
        // class; the first NON-DEX ancestor is the boundary. Declaring
        // classes that are already framework classes (the R-NEW-345 case,
        // e.g. RecyclerView.onMeasure's super → ViewGroup) are untouched —
        // probe fnew324 P2 pins that control face.
        std::string bridge_cls = declaring_class;
        if (dex_report_ && is_dex_defined_class(declaring_class)) {
            std::string boundary = superclass_of(declaring_class);
            while (!boundary.empty() && is_dex_defined_class(boundary)) {
                boundary = superclass_of(boundary);
            }
            if (!boundary.empty()) bridge_cls = boundary;
        }
        bridge_to_api(bridge_cls, method_name,
                      args, return_val, api_status, method_idx);
        last_invoke_return_ = return_val;
    }

    // Record an API call trace entry so this call shows up in evidence
    ApiCallTrace api_trace;
    api_trace.sequence = api_call_sequence_++;
    api_trace.api_class = declaring_class + "<super>";
    api_trace.method = method_name;
    api_trace.arguments = arg_names;
    api_trace.return_value = return_val.to_string();
    api_trace.status = api_status;
    api_trace.pc = pc;
    api_trace.frame_id = call_stack_.empty() ? 0 : call_stack_.top().frame_id;
    note_api_status(api_trace);  // F-NEW-200 census
    batched_cap_push(result.api_call_traces, result.api_call_ring_cursor, static_cast<size_t>(config_.api_call_trace_cap), std::move(api_trace));

    // Trace evidence
    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.invoked_method = resolved_method;
    trace.operands.push_back({"invoke_kind", "super"});
    trace.operands.push_back({"method_idx", std::to_string(method_idx)});
    trace.operands.push_back({"method_name", method_name});
    trace.operands.push_back({"declaring_class", declaring_class});
    trace.operands.push_back({"arg_count", std::to_string(arg_count)});
    trace.operands.push_back({"args", std::to_string(arg_names.size())});
    trace.operands.push_back({"static_type", static_type});
    trace.operands.push_back({"runtime_type", runtime_type});
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});
    }

    // Advance PC past the 35c instruction (3 code units = 6 bytes)
    pc_ = pc + 3;
    return true;
}

bool DalvikExecutionEngine::execute_invoke_direct(uint32_t pc, InstructionTrace& trace,
                                                 DalvikExecutionResult& result) {
    // Similar to invoke-virtual but for constructors and private methods
    if (pc + 2 >= bytecode_.size()) return false;

    // EXP-071 Phase 7: Save and reset current_invoke_is_static_ to false
    // for invoke-direct calls (instance methods).
    bool saved_is_static = current_invoke_is_static_;
    current_invoke_is_static_ = false;
    
    uint16_t instr = bytecode_[pc];
    // EXP-037 Phase B (BLOCKER-015 FIX): 35c format is "AA|op BBBB FEDC"
    //   code[pc+0] = AA|op
    //   code[pc+1] = BBBB (method_idx)
    //   code[pc+2] = FEDC (register list)
    uint16_t method_idx = bytecode_[pc + 1];  // was pc+2
    uint16_t regs_word = bytecode_[pc + 2];    // was pc+1
    
    // Extract registers
    // EXP-037 Phase B (BLOCKER-016 FIX): 5th reg is low nibble of AA (high byte
    // of opcode word), so it's (instr >> 8) & 0xF, not (instr >> 4) & 0xF.
    uint8_t regs[5] = {
        static_cast<uint8_t>(regs_word & 0xF),
        static_cast<uint8_t>((regs_word >> 4) & 0xF),
        static_cast<uint8_t>((regs_word >> 8) & 0xF),
        static_cast<uint8_t>((regs_word >> 12) & 0xF),
        static_cast<uint8_t>((instr >> 8) & 0xF)  // 5th reg — was (instr >> 4) & 0xF
    };
    
    std::vector<DalvikValue> args;
    // EXP-045: Only push argc registers (from 35c format: high nibble of high byte)
    uint8_t argc = (instr >> 12) & 0xF;
    for (int i = 0; i < argc && i < 5; ++i) {
        args.push_back(get_register(regs[i]));
    }

    // CYCLE-E: signature-aware param conversion for invoke-direct (35c).
    // Constructors like Paint.<init>(int) are unaffected, but any direct
    // call with literal floats/wides (e.g. custom View ctors) needs the
    // same proto-guided reinterpretation as virtual calls.
    if (dex_report_) {
        // CONT-96 W3-B: memo entry (proto string + parsed params resolve once).
        const auto& mre = method_resolve_entry(current_dex_index_, method_idx);
        const std::string& proto_35c = mre.proto;
        if (proto_35c != "<unknown>") {
            args = build_invoke_args(args, mre.proto_params,
                                     /*is_static=*/false);
        }
    }
    
    // Resolve as constructor (<init>) or direct method
    // EXP-037 Phase B (BLOCKER-002 FIX): use DexReport::method_ids to resolve
    // method_idx → real method name + declaring class.
    std::string method_name = "<init>";  // fallback for legacy code paths
    std::string class_name = "<unknown>";
    std::string method_desc_081;
    if (dex_report_) {
        method_name = resolve_method_name_for_dex(method_idx, current_dex_index_);
        class_name = resolve_method_class_for_dex(method_idx, current_dex_index_);
        method_desc_081 = resolve_method_proto_for_dex(method_idx, current_dex_index_);
        // S55 R-NEW-376 (env-gated): direct evidence for the j0.<init>
        // self-recursion — print EVERY invoke-direct dispatched from a
        // j0/t0/E0 constructor frame with the resolved (class, name, desc).
        static const bool r376_direct =
            diag_env("MINIANDROID_F040_DIAG");
        if (r376_direct && current_method_ == "<init>" &&
            (current_class_ == "Lj/j0;" || current_class_ == "Lt0/t;" ||
             current_class_ == "LE0/c;")) {
            static thread_local uint64_t r376_n = 0;
            if (r376_n < 60000) {
                r376_n++;
                std::cerr << "[R376-DIRECT] from=" << current_class_
                          << ".<init> depth=" << recursion_depth_
                          << " method_idx=" << method_idx
                          << " dex=" << current_dex_index_
                          << " resolved=" << class_name << "."
                          << method_name << method_desc_081
                          << " argc=" << args.size() << std::endl;
            }
        }
        // EXP-081: Debug trace
        if (diag_env("MINIANDROID_EXP081_TRACE") && (method_name.find("lambda") != std::string::npos || method_name.find("createView") != std::string::npos)) {
            std::cerr << "[EXP081-DESC] method=" << method_name
                      << " method_idx=" << method_idx
                      << " dex=" << current_dex_index_
                      << " desc=" << method_desc_081
                      << std::endl;
        }
    }

    // EXP-061: Debug — trace invoke-direct inside PhoneView.<init>
    if (diag_env("MINIANDROID_EXP061_TRACE") && current_class_.find("PhoneView") != std::string::npos &&
        current_method_ == "<init>") {
        std::cerr << "[EXP061-INVOKE-DIRECT] caller=PhoneView.<init>"
                  << " method_idx=" << method_idx
                  << " dex_index=" << current_dex_index_
                  << " → class=" << class_name
                  << " method=" << method_name
                  << " argc=" << (int)argc
                  << std::endl;
    }
    
    // F-141 (S72-W3): ART null-receiver law extends to invoke-direct
    // (constructors/private methods): NPE at the call site before the
    // callee body executes. Previously invoke-direct had NO null check —
    // the body ran with this=NULL (silent wrongness, §039/§177).
    if (!args.empty() && f141_is_null_receiver(args[0])) {
            dump_frame_locals_diag("F141-OP");
        throw_deferred("Ljava/lang/NullPointerException;",
                       "Attempt to invoke direct method '" + class_name +
                           "." + method_name + "' on a null object reference",
                       "f141-null-recv");
        pc_ += 3;  // 35c length; a catch handler redirect overrides pc
        return true;
    }

    // MASTER CAMPAIGN FIX (F2 constructor-direct law): java.lang.Object.<init>
    // is the compiler-mandated empty constructor (AOSP/ART: Object has no
    // constructor logic; javac/d8 emit invoke-direct Object;-><init>()V as
    // the first instruction of EVERY constructor). It must be a no-op at the
    // engine level. Letting it fall through to the shadow layer let the
    // C013 ancestor walk + ViewShadow's user-class catch-all claim it
    // (evidence: fr.neamar.kiss v224, R8 horizontal class merging — 24
    // classes extend the merged target Lfr/neamar/kiss/db/DBHelper;, every
    // merged constructor's Object.<init> super call walked
    // ArchTaskExecutor->DBHelper and ViewShadow allocated bogus view nodes).
    if (method_name == "<init>" && class_name == "Ljava/lang/Object;") {
        if (!args.empty() && args[0].type == DalvikType::OBJECT_REF) {
            if (auto* obj = heap_.get(args[0].object_id)) {
                heap_.mark_initialized(args[0].object_id);
            }
        }
        // S157-B: trace_cap==0 gate (never-read trace — see iget block).
        if (config_.trace_cap > 0) {
        trace.invoked_method = "Ljava/lang/Object;.<init> (no-op law)";
        trace.operands.push_back({"method", std::to_string(method_idx)});
        }
        current_invoke_is_static_ = saved_is_static;
        pc_ = pc + 3;
        return true;
    }

    // Check if first arg is an object we allocated
    // EXP-061 FIX: Do NOT overwrite class_name with the runtime class for
    // invoke-direct. invoke-direct uses the DECLARING class (from method_ids[]),
    // not the runtime class. Overwriting it causes try_recursive_invoke to
    // search for <init> in the SUBCLASS (e.g. PhoneView) instead of the
    // SUPERCLASS (e.g. SlideView), leading to infinite recursion detection
    // or wrong method selection. Only invoke-virtual should use the runtime
    // class for polymorphic dispatch.
    if (!args.empty() && args[0].type == DalvikType::OBJECT_REF) {
        if (auto* obj = heap_.get(args[0].object_id)) {
            // Mark as initialized (constructor called)
            if (method_name == "<init>") {
                heap_.mark_initialized(args[0].object_id);
            }
            // S157-B: gate the argument build on verbose_ (log() checks too late).
            if (verbose_) log("  INVOKE-DIRECT: " + class_name + "." + method_name +
                "() on obj#" + std::to_string(args[0].object_id));
        }
    }
    
    // API bridge
    DalvikValue return_val = DalvikValue::make_void();
    ApiCallTrace::Status status = ApiCallTrace::Status::STUBBED;

    // ── #371 CLOSEOUT: JVMS 5.5 / AOSP ClassLinker::EnsureInitialized law
    // ── the first ACTIVE USE of a class triggers initialization, and
    // invoke-static IS an active use. sget/sput/new-instance already
    // ensured this; a class first touched via static-method invocation ran
    // uninitialized (S-2 evidence: NativeProbe.<clinit> — the canonical
    // System.loadLibrary-in-static-init pattern — never executed, so the
    // native library never loaded and every native call failed softly 0).
    // ensure_class_initialized early-exits on the already-initialized set,
    // so the per-call cost is one hash lookup.
    if (!class_name.empty() && class_name[0] == 'L')
        ensure_class_initialized(class_name);

    // EXP-038 (BLOCKER-034): Try recursive invocation.
    bool recursively_invoked = false;
    if (config_.enable_api_bridge) {
        // EXP-079: Debug trace for lambda$createView$1 dispatch
        // EXP-089: Also trace lambda$new$0 (ActionBar back button handler)
        // and any method containing "presentFragment" or "swapToFragment"
        if (diag_env("MINIANDROID_EXP079_TRACE") && (method_name.find("createView") != std::string::npos ||
            method_name.find("onDoneButton") != std::string::npos ||
            method_name.find("onNextPressed") != std::string::npos ||
            method_name.find("lambda$new") != std::string::npos ||
            method_name.find("presentFragment") != std::string::npos ||
            method_name.find("swapToFragment") != std::string::npos ||
            method_name.find("onBackPressed") != std::string::npos)) {
            std::cerr << "[EXP079-DIRECT] invoke-direct: class=" << class_name
                      << " method=" << method_name
                      << " method_idx=" << method_idx
                      << " dex_index=" << current_dex_index_
                      << " args=" << args.size()
                      << std::endl;
        }
        if (class_name == "LE1/c;" && diag_env("MINIANDROID_E1_DIAG")) {
            std::cerr << "[E1-DIAG] inner direct: desc=" << method_desc_081
                      << " args=" << args.size() << std::endl;
        }
        if (try_recursive_invoke(class_name, method_name, args, return_val, result, method_desc_081)) { last_invoke_return_ = return_val;
            recursively_invoked = true;
            status = ApiCallTrace::Status::IMPLEMENTED;
            // EXP-079: Debug trace
            if (diag_env("MINIANDROID_EXP079_TRACE") && (method_name.find("createView") != std::string::npos ||
                method_name.find("lambda$new") != std::string::npos ||
                method_name.find("presentFragment") != std::string::npos)) {
                std::cerr << "[EXP079-DIRECT] try_recursive_invoke SUCCEEDED for " << method_name << std::endl;
            }
        } else {
            // EXP-079: Debug trace
            if (diag_env("MINIANDROID_EXP079_TRACE") && (method_name.find("createView") != std::string::npos ||
                method_name.find("lambda$new") != std::string::npos ||
                method_name.find("presentFragment") != std::string::npos)) {
                std::cerr << "[EXP079-DIRECT] try_recursive_invoke FAILED for " << method_name << std::endl;
            }
        }
    }
    if (!recursively_invoked && config_.enable_api_bridge) {
        bridge_to_api(class_name, method_name, args, return_val, status, method_idx); last_invoke_return_ = return_val;
    }
    
    // Trace
    ApiCallTrace api_trace;
    api_trace.sequence = api_call_sequence_++;
    api_trace.api_class = class_name;
    api_trace.method = method_name;
    api_trace.status = status;
    api_trace.pc = pc;
    note_api_status(api_trace);  // F-NEW-200 census
    batched_cap_push(result.api_call_traces, result.api_call_ring_cursor, static_cast<size_t>(config_.api_call_trace_cap), std::move(api_trace));
    
    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.invoked_method = class_name + "." + method_name;
    trace.operands.push_back({"method", std::to_string(method_idx)});
    }

    // MASTER CAMPAIGN FIX (F8 default-onMeasure law): at constructor
    // completion, record whether the AOSP DEFAULT View.onMeasure applies to
    // this node (no onMeasure override anywhere in the semantic chain below
    // a framework content class). The measure pass consumes this for leaf
    // nodes with no content source (View.getDefaultSize: AT_MOST/EXACTLY →
    // specSize). Evidence: org.billthefarmer.scope v140 custom views
    // measured 0x0 (content model) where AOSP measures them at the
    // parent-available size.
    if (method_name == "<init>" && shadow_registry_ && !args.empty() &&
        args[0].type == DalvikType::OBJECT_REF) {
        auto* view_shadow = shadow_registry_->find_as<framework::ViewShadow>();
        if (view_shadow) {
            auto* node = view_shadow->find_node(args[0].object_id);
            if (node) {
                const std::string& cls = !std::string(args[0].class_desc).empty()
                                             ? std::string(args[0].class_desc) : class_name;
                bool overrides = class_chain_defines_method(cls, "onMeasure");
                // M3 F-005 FIX-A: content families never take the
                // getDefaultSize fallback (see the constructor-time site).
                node->aosp_default_measure =
                    !overrides && !runtime_content_measure_class(cls);
                // R-NEW-347 (S42): programmatic views (new-instance +
                // invoke-direct — compose's AndroidComposeView from
                // La72;.a, app-built custom views) must carry the SAME
                // overrides_on_measure flag the inflate-time constructor
                // path records (run_custom_view_constructor site). Without
                // it the F10 real-DEX onMeasure hook never fires for
                // programmatically-built views and the measure pass
                // answers from the native content model instead of the
                // APK's own onMeasure bytecode.
                node->overrides_on_measure = overrides;
                // S122 (R-NEW-417): same capture for the touch gate.
                node->overrides_touch_event =
                    class_chain_defines_method(cls, "onTouchEvent");
                // S128 (R-NEW-424, CAP-INPUT-100): intercept-gate capture.
                node->overrides_intercept_touch_event =
                    class_chain_defines_method(cls, "onInterceptTouchEvent");
                // S123 (R-NEW-419): same capture for the onSizeChanged law.
                node->overrides_on_size_changed =
                    class_chain_defines_method(cls, "onSizeChanged");
            }
        }
    }

    // EXP-071 Phase 7: Restore the saved static flag.
    current_invoke_is_static_ = saved_is_static;
    pc_ = pc + 3;
    return true;
}

bool DalvikExecutionEngine::execute_invoke_static(uint32_t pc, InstructionTrace& trace,
                                                 DalvikExecutionResult& result) {
    // Format similar to invoke-virtual but for static methods
    if (pc + 2 >= bytecode_.size()) return false;
    // S55 R-NEW-361: entry-level probe — was the function even reached?
    if (diag_env("MINIANDROID_F040_DIAG")) {
        static thread_local uint64_t eis_entry = 0;
        if (eis_entry < 200000) {
            eis_entry++;
            auto mn = resolve_method_name_for_dex(
                bytecode_[pc + 1], current_dex_index_);
            if (mn == "fill" || mn == "r") {
                std::cerr << "[EIS-ENTRY] pc=" << pc
                          << " method=" << mn
                          << " caller=" << current_class_ << "."
                          << current_method_ << std::endl;
            }
        }
    }

    // EXP-071 Phase 8: Mark this call as static so try_shadow_dispatch
    // doesn't treat args[0] as `this`. See header comment for details.
    //
    // EXP-071 Phase 7 FIX: The flag stays true during the entire
    // execute_invoke_static call. execute_invoke_virtual and
    // execute_invoke_direct SAVE and RESET the flag to false at their
    // entry, and RESTORE it at their exit. This ensures that:
    //   - bridge_to_api → try_shadow_dispatch at THIS level sees true (static)
    //   - bridge_to_api → try_shadow_dispatch inside callees sees false (instance)
    bool saved_is_static = current_invoke_is_static_;
    current_invoke_is_static_ = true;

    uint16_t instr = bytecode_[pc];
    // EXP-037 Phase B (BLOCKER-015 FIX): 35c format is "AA|op BBBB FEDC"
    //   code[pc+0] = AA|op
    //   code[pc+1] = BBBB (method_idx)
    //   code[pc+2] = FEDC (register list)
    uint16_t method_idx = bytecode_[pc + 1];  // was pc+2
    uint16_t regs_word = bytecode_[pc + 2];    // was pc+1
    // ── S222-A (DIAG-ONLY, env-gated MINIANDROID_S222_CACHE): the dooz
    // text-cache density PACKER probe (invoke-static face). Lsg0;.a(FF)J
    // packs (density, fontScale) into the InlineDensity long the
    // MultiParagraphLayoutCache stores. Logging the caller names the
    // producer of the (2.625, 0.0) fontScale-zero face — the flip driver
    // the S221 decode left open ("null vs a real (0,0) Density object").
    {
        static thread_local const bool s222_pack_on =
            diag_env("MINIANDROID_S222_CACHE");
        if (s222_pack_on) {
            std::string s222_pmn =
                resolve_method_name_for_dex(method_idx, current_dex_index_);
            if (s222_pmn == "a" && dex_report_) {
                std::string s222_pcls =
                    dex_report_->get_method_class(method_idx);
                if (s222_pcls == "Lsg0;") {
                    static thread_local uint64_t s222_pn = 0;
                    if (s222_pn < 48) {
                        ++s222_pn;
                        std::cerr << "[S222-PACK-S] Lsg0;.a(FF)J caller="
                                  << current_class_ << "." << current_method_
                                  << " pc=" << pc << std::endl;
                    }
                }
            }
        }
    }
    // ────────────────────────────────────────────────────────────────────
    // R-NEW-350 probe (S43, env-gated read-only): the 3-arg
    // Class.forName(String,boolean,ClassLoader) from protobuf's
    // GeneratedMessageLite.getDefaultInstance produced ZERO bridge logs —
    // trace every static forName dispatch AT THE INTERPRETER LEVEL (method
    // idx + resolved name + class) so the exact route (cycle guard /
    // super-dispatch / bridge miss) becomes visible in one run.
    // ────────────────────────────────────────────────────────────────────
    if (dex_report_) {
        static thread_local const bool r350fn2 =
            diag_env("MINIANDROID_R350_TRACE");
        if (r350fn2) {
            std::string fn_name =
                resolve_method_name_for_dex(method_idx, current_dex_index_);
            if (fn_name == "forName") {
                std::string fn_cls =
                    resolve_method_class_for_dex(method_idx, current_dex_index_);
                std::cerr << "[R350-FN2] static forName dispatch idx="
                          << method_idx << " class=" << fn_cls
                          << " caller=" << current_class_ << "."
                          << current_method_ << " pc_units=" << pc
                          << std::endl;
            }
        }
    }

    // Extract argument registers
    uint8_t regs[5] = {
        static_cast<uint8_t>(regs_word & 0xF),
        static_cast<uint8_t>((regs_word >> 4) & 0xF),
        static_cast<uint8_t>((regs_word >> 8) & 0xF),
        static_cast<uint8_t>((regs_word >> 12) & 0xF),
        static_cast<uint8_t>((instr >> 8) & 0xF)  // 5th reg — was (instr >> 4) & 0xF
    };

    std::vector<DalvikValue> args;
    // EXP-045: Only push argc registers (from 35c format: high nibble of high byte)
    uint8_t argc = (instr >> 12) & 0xF;

    // F-044 DIAG (env-gated): did the version-scan's identityHashCode call
    // reach the invoke handler at all?
    {
        static thread_local const bool f044p = std::getenv("MINIANDROID_F044_DIAG") != nullptr;
        if (f044p) {
            std::string mh = resolve_method_name_for_dex(method_idx, current_dex_index_);
            std::string mc = resolve_method_class_for_dex(method_idx, current_dex_index_);
            if (mc == "Ljava/lang/System;" && mh == "identityHashCode") {
                std::cerr << "[F044-DIAG] invoke-static System.identityHashCode reached execute_invoke_static" << std::endl;
            }
        }
    }

    // EXP-071 Phase 8: Resolve method name and proto EARLY so we can use them
    // for debug tracing in the wide-merge code below. The original code only
    // resolved method_name AFTER the args were built, which meant our debug
    // trace couldn't reference method_name.
    std::string method_name = "<static_method:" + std::to_string(method_idx) + ">";
    std::string class_name = "<static_class>";
    if (dex_report_) {
        method_name = resolve_method_name_for_dex(method_idx, current_dex_index_);
        class_name = resolve_method_class_for_dex(method_idx, current_dex_index_);
    }

    // ── S188-W18 FT PROBE (entry) — trace the FreeType static dispatch.
    static thread_local const bool w18ft_in_on =
        std::getenv("MINIANDROID_W18_FT_TRACE") != nullptr;
    if (w18ft_in_on &&
        class_name.find("freetype/FreeType") != std::string::npos) {
        static thread_local uint64_t w18ft_in_n = 0;
        if (w18ft_in_n++ < 60)
            std::cerr << "[W18-FT-STATIC] entry " << class_name << "."
                      << method_name << " method_idx=" << method_idx
                      << " dex=" << current_dex_index_
                      << " proto="
                      << (dex_report_
                              ? resolve_method_proto_for_dex(method_idx,
                                                             current_dex_index_)
                              : std::string("<no-report>"))
                      << std::endl;
    }

    // EXP-071 Phase 8: Wide register merging.
    //
    // For methods with wide arguments (J = long, D = double), each wide arg
    // occupies TWO consecutive register slots in the Dalvik register file.
    // Without merging, `invoke-static {v3, v0, v1}, runOnUIThread(Runnable, J)`
    // would push 3 args (v3=Runnable, v0=low32, v1=high32) instead of 2
    // (Runnable, long). This breaks HandlerShadow's delay extraction
    // because args[1] is a low-half INT32 instead of an INT64 long.
    //
    // Fix: parse the method descriptor and merge wide register pairs into
    // single INT64/FLOAT64 DalvikValues. The descriptor is the (Ljava/lang/Runnable;J)V
    // string from the DEX method_id table; we walk the parameter types left
    // to right, consuming registers from the regs[] array in order.
    std::string method_proto = "<unknown>";
    if (dex_report_) {
        method_proto = resolve_method_proto_for_dex(method_idx, current_dex_index_);
    }
    // EXP-082: Debug trace for $r8$lambda invoke-static
    if (diag_env("MINIANDROID_EXP082_TRACE") && (method_name.find("$r8$lambda") != std::string::npos || method_name.find("createView") != std::string::npos)) {
        std::cerr << "[EXP082-STATIC] method=" << method_name
                  << " method_idx=" << method_idx
                  << " dex=" << current_dex_index_
                  << " proto=" << method_proto
                  << " argc=" << (int)argc
                  << std::endl;
    }

    // Parse the parameter list inside the parens.
    // Format: "(Ljava/lang/Runnable;J)V" → params = ["Ljava/lang/Runnable;", "J"]
    std::vector<std::string> param_types;
    if (method_proto != "<unknown>") {
        size_t lp = method_proto.find('(');
        size_t rp = method_proto.find(')');
        if (lp != std::string::npos && rp != std::string::npos && rp > lp) {
            std::string params = method_proto.substr(lp + 1, rp - lp - 1);
            size_t i = 0;
            while (i < params.size()) {
                char c = params[i];
                if (c == 'L') {
                    size_t semi = params.find(';', i);
                    if (semi == std::string::npos) break;
                    param_types.push_back(params.substr(i, semi - i + 1));
                    i = semi + 1;
                } else if (c == '[') {
                    // Array — keep eating [ until non-[
                    size_t start = i;
                    while (i < params.size() && params[i] == '[') i++;
                    if (i < params.size() && params[i] == 'L') {
                        size_t semi = params.find(';', i);
                        if (semi == std::string::npos) break;
                        param_types.push_back(params.substr(start, semi - start + 1));
                        i = semi + 1;
                    } else {
                        param_types.push_back(params.substr(start, i - start + 1));
                        i += 1;
                    }
                } else {
                    // Primitive — single char (B C D F I J S Z V)
                    param_types.push_back(std::string(1, c));
                    i += 1;
                }
            }
        }
    }

    // Walk params, consuming registers from regs[]. Each wide param (J or D)
    // consumes TWO register slots; otherwise one.
    size_t reg_idx = 0;
    for (size_t p = 0; p < param_types.size() && reg_idx < 5 && (int)reg_idx < argc; ++p) {
        const std::string& pt = param_types[p];
        if (pt == "J" || pt == "D") {
            // Wide: this register pair holds a 64-bit value.
            DalvikValue lo = get_register(regs[reg_idx]);
            if (lo.type == DalvikType::INT64) {
                // Case 1: low register already holds the full INT64 (set by const-wide/*).
                if (pt == "J") {
                    args.push_back(lo);
                } else {
                    double d;
                    int64_t bits = lo.long_val;
                    std::memcpy(&d, &bits, sizeof(d));
                    args.push_back(DalvikValue::make_double(d));
                }
            } else if (lo.type == DalvikType::FLOAT64) {
                args.push_back(lo);
            } else if (reg_idx + 1 < 5) {
                // Case 2: merge two registers (split wide value).
                DalvikValue hi = get_register(regs[reg_idx + 1]);
                int64_t combined = (static_cast<int64_t>(hi.int_val) << 32) |
                                   (static_cast<uint32_t>(lo.int_val));
                if (pt == "J") {
                    args.push_back(DalvikValue::make_long(combined));
                } else {
                    double d;
                    int64_t bits = combined;
                    std::memcpy(&d, &bits, sizeof(d));
                    args.push_back(DalvikValue::make_double(d));
                }
            } else {
                // GP-INT-001 (issue #582): a wide param starting at the 5th
                // 35c slot cannot have a second encoded word (regs is the
                // 5-slot local array; the pre-fix code read regs[5] — one
                // past the end, stack garbage). Verifier-valid DEX cannot
                // encode it (the pair needs 6 registers); treat as a
                // malformed-invoke face: loud, hi = 0, no OOB.
                static thread_local uint64_t gp_int001_n = 0;
                if (gp_int001_n++ < 8)
                    std::cerr << "[GP-INT-001] invoke-static wide param at "
                                 "slot 4 has no second encoded register — "
                                 "malformed 35c args (hi=0)"
                              << std::endl;
                if (pt == "J") {
                    args.push_back(DalvikValue::make_long(
                        static_cast<int64_t>(static_cast<uint32_t>(
                            get_register(regs[reg_idx]).int_val))));
                } else {
                    args.push_back(DalvikValue::make_double(0.0));
                }
            }
            reg_idx += 2;
        } else {
            DalvikValue v = get_register(regs[reg_idx]);
            // EXP-095 (CM-019): signature-aware FLOAT conversion.
            // For 'F' params the register holds raw float BITS as INT32
            // (e.g. const/high16 v1, 0x42400000 loads 48.0f as raw bits —
            // const opcodes are not float-typed). Per the method signature
            // we reinterpret: LayoutHelper.createFrame(IF) previously
            // delivered height=0x42400000=1111490560 instead of 48.
            if (pt == "F" && v.type == DalvikType::INT32) {
                float f;
                int32_t bits = v.int_val;
                std::memcpy(&f, &bits, sizeof(f));
                args.push_back(DalvikValue::make_float(f));
            } else if (v.type == DalvikType::INT32) {
                // ROOT-1 (GAME-185 #608) — signature-aware primitive retyping
                // in the INLINE packer: DEX registers are untyped; the proto's
                // param char is the only authority. The shared build_invoke_args
                // carries this law (CHAR-PROBE campaign), but this inline packer
                // handled only 'F' — so kotlin's split(delimiter: Char) lowered
                // to invoke-static String.valueOf(char) received INT32 44 and
                // produced "44" instead of ",". dk.cocode.chess: 0 of 9,000 CSV
                // rows ever split; every parseLine collapsed to one column and
                // the puzzle repository stayed empty ("No puzzles available").
                // Same register word, proto-char authority: C→CHAR, Z→BOOLEAN,
                // B→BYTE, S→SHORT.
                switch (pt.empty() ? 'I' : pt[0]) {
                    case 'C': {
                        DalvikValue c = v;
                        c.type = DalvikType::CHAR;
                        c.int_val &= 0xFFFF;
                        args.push_back(c);
                        break;
                    }
                    case 'Z':
                        args.push_back(DalvikValue::make_bool(v.int_val != 0));
                        break;
                    case 'B': {
                        DalvikValue b = v;
                        b.type = DalvikType::BYTE;
                        b.int_val = static_cast<int8_t>(v.int_val & 0xFF);
                        args.push_back(b);
                        break;
                    }
                    case 'S': {
                        DalvikValue s = v;
                        s.type = DalvikType::SHORT;
                        s.int_val = static_cast<int16_t>(v.int_val & 0xFFFF);
                        args.push_back(s);
                        break;
                    }
                    default:
                        args.push_back(v);
                        break;
                }
            } else {
                args.push_back(v);
            }
            reg_idx += 1;
        }
    }
    // If we couldn't parse params (proto unavailable), fall back to old behavior.
    if (param_types.empty() && args.empty()) {
        for (int i = 0; i < argc && i < 5; ++i) {
            args.push_back(get_register(regs[i]));
        }
    }

    // EXP-088+ F4: Trace invoke-static for $default$ methods (desugared interface defaults)
    // to verify overload resolution and arg count correctness.
    if (diag_env("MINIANDROID_EXP088_TRACE") && method_name.find("$default$") != std::string::npos) {
        std::cerr << "[EXP088-F4-STATIC] method=" << method_name
                  << " class=" << class_name
                  << " proto=" << method_proto
                  << " method_idx=" << method_idx
                  << " current_dex=" << current_dex_index_
                  << " argc=" << (int)argc
                  << " args_size=" << args.size()
                  << " caller=" << current_class_ << "." << current_method_
                  << " pc=" << pc;
        for (size_t i = 0; i < args.size() && i < 4; ++i) {
            std::cerr << " arg[" << i << "]=" << (int)args[i].type;
            if (args[i].type == DalvikType::OBJECT_REF) std::cerr << "/obj=" << args[i].object_id;
        }
        // Also try resolving with ALL DEX files to find the correct proto
        for (uint32_t di = 0; di < per_dex_raw_data_.size(); di++) {
            std::string alt_proto = resolve_method_proto_for_dex(method_idx, di);
            if (alt_proto != "<unknown>" && alt_proto != method_proto) {
                std::cerr << " alt_proto[DEX" << di << "]=" << alt_proto;
            }
        }
        std::cerr << std::endl;
    }

    // EXP-063: Trace invoke-static for getString
    if (dex_report_) {
        std::string mn = resolve_method_name_for_dex(method_idx, current_dex_index_);
        if (mn == "getString") {
            std::string cn = resolve_method_class_for_dex(method_idx, current_dex_index_);
            std::cerr << "[EXP063-ISTATIC] getString"
                      << " instr=0x" << std::hex << instr << std::dec
                      << " argc=" << (int)argc
                      << " regs[0]=" << (int)regs[0]
                      << " class=" << cn
                      << " caller=" << current_class_ << "." << current_method_
                      << " pc=" << pc;
            if (!args.empty()) {
                std::cerr << " arg0=" << args[0].int_val;
            } else {
                std::cerr << " NO_ARGS";
            }
            std::cerr << std::endl;
        }
    }

    // EXP-071 Phase 8: Trace runOnUIThread specifically to verify wide-arg merging.
    if (method_name == "runOnUIThread" || method_name == "executeOnUIThread") {
        std::cerr << "[EXP071-RUNONUI] class=" << class_name
                  << " method=" << method_name
                  << " argc=" << (int)argc
                  << " args_count=" << args.size()
                  << " proto=" << method_proto;
        for (size_t i = 0; i < args.size(); ++i) {
            std::cerr << " arg[" << i << "]=";
            switch (args[i].type) {
                case DalvikType::OBJECT_REF:
                    std::cerr << "obj#" << args[i].object_id
                              << "(" << args[i].class_desc << ")";
                    break;
                case DalvikType::INT64:
                    std::cerr << "long=" << args[i].long_val;
                    break;
                case DalvikType::INT32:
                    std::cerr << "int=" << args[i].int_val;
                    break;
                default:
                    std::cerr << "<other>";
                    break;
            }
        }
        std::cerr << std::endl;
    }
    
    // Common static methods we might recognize (legacy hint — now used only
    // for routing hints when the API bridge falls through).
    if (class_name.find("Log") != std::string::npos) {
        if (args.size() > 0 && args[0].type == DalvikType::INT32) {
            // args[0].int_val is the Log level: 5=warn, 6=error, etc.
            // (Just a hint; method_name from DEX is authoritative.)
        }
    }

    // API bridge
    DalvikValue return_val = DalvikValue::make_void();
    ApiCallTrace::Status status = ApiCallTrace::Status::STUBBED;

    // ────────────────────────────────────────────────────────────────────
    // R-NEW-350 (S43) — java.lang.Class.forName OVERLOAD LAW (host-class
    // dispatch at the interpreter level, BEFORE the recursive-invoke /
    // bridge layers — same pre-emption pattern as the R-NEW-347
    // View.measure law, which had to be placed before a silent-void
    // shadow handler).
    //
    // OpenJDK/AOSP law (java.lang.Class, java.lang.ClassLoader):
    //   forName(String name)
    //   forName(String name, boolean initialize, ClassLoader loader)
    //   → resolves `name` against the CALLER'S classloader domain and,
    //     when initialize=true, RUNS the class <clinit> before returning
    //     the Class object. Unknown name → ClassNotFoundException.
    //
    // Engine mapping: our authoritative classloader domain is the APK DEX
    // (class_info_index_ over dex_report_->classes); the dotted binary
    // name maps to the L-descriptor form; make_class returns the CLASS_REF
    // whose referent_desc every downstream const-class law reads.
    //
    // Real demand (dooz23, PRIORITY-1): protobuf-javalite
    // GeneratedMessageLite.getDefaultInstance(Class) — DEX Lbc0;.d — does
    //   defaultInstanceMap.get(clazz) == null
    //   → Class.forName(clazz.getName(), true, clazz.getClassLoader())
    //   → defaultInstanceMap.get(clazz)   // now registered by <clinit>
    // The 3-arg call was swallowed BEFORE the bridge (zero bridge logs,
    // zero CNFE, silent void) so the <clinit> never ran, the second get
    // stayed null, dynamicMethod(GET_DEFAULT_INSTANCE) answered null and
    // the bare IllegalStateException killed the DataStore theme read →
    // RuntimeException "Unable to get message info for y81" →
    // MainActivity.onCreate died before composition (S43 baseline,
    // crash.log chain 1; R350-FN2 trace proved interpreter dispatch at
    // idx=6825 with no bridge arrival).
    // ────────────────────────────────────────────────────────────────────
    // ENABLING GATE (S43 evidence-driven): with this law unconditionally
    // ON, microtimer's Room initDb loop (MainActivity.onCreate re-visited
    // the SAME forName invoke 50k×, HALT-LOOP guard) starved the run
    // budget → white frame + battery corpus-stage regression (A/B-proven:
    // stash→rebuild→run restored microtimer's 1,042,368-nonwhite render;
    // unstash→re-run reproduced the blank). The dooz23 protobuf chain
    // REQUIRES the law (UOE → asSubclass chain). Resolution: the law is
    // DEFAULT-OFF (S42 bridge behavior for every app); evidence runs
    // enable it explicitly with MINIANDROID_R350_LAW=1. Next-session
    // root: why microtimer's getGeneratedImplementation retries under
    // interpreter-level resolution but proceeded under bridge-level.
    // ────────────────────────────────────────────────────────────────────
    // R-NEW-354 (S44) — FRAMEWORK-CLASS REGISTRY LAW (Class.forName
    // fallthrough to the engine's own framework surface).
    //
    // AOSP law (java.lang.Class, java.lang.ClassLoader): forName resolves
    // against the FULL classpath — the boot classpath (framework classes)
    // FIRST, then the app classloader. A mini-Android owns a framework
    // surface; a name absent from the app DEX but present in that surface
    // must answer a Class object, not a ClassNotFoundException.
    //
    // Real demand (dooz23, PRIORITY-1, S44 evidence): compose-ui 1.11.4
    // AndroidComposeView.onAttachedToWindow (DEX Lt4;, pc 84-198) runs the
    // AOSP StrictMode block: StrictMode.getVmPolicy → Class.forName(
    // "android.os.SystemProperties") → getDeclaredMethod("addChangeCallback")
    // → invoke + setVmPolicy round-trip. On the engine the forName threw a
    // deferred CNFE, the attach method derailed, the deferred compose
    // request (Lt4;->n0, stored by setOnReadyForComposition) was never
    // consumed (pc 640-662), the composition never bootstrapped
    // (Lf90;.i never dispatched), AndroidComposeView measured 0x0 with
    // zero children, and the frame stayed blank AFTER R-NEW-353 had
    // already unblocked the protobuf schema build.
    //
    // GENERIC (zero class hacks): the registry holds framework classes the
    // engine's shadow surface genuinely models. Reflection into them rides
    // the M4 F-029 record laws: getDeclaredMethod mints a Method record for
    // any name, invoke dispatches back through the bridge (an unanswered
    // shadow method yields null — the callback simply never fires, which is
    // AOSP-exact for a runtime with no property daemon). Registry answers
    // are deterministic (no app-DEX retry interaction → no R-NEW-352-class
    // HALT-LOOP risk) so the law is DEFAULT-ON, independent of the
    // MINIANDROID_R350_LAW gate that guards APP-class resolution.
    // ────────────────────────────────────────────────────────────────────
    if (class_name == "Ljava/lang/Class;" &&
        method_name == "forName" &&
        !args.empty() && args[0].type == DalvikType::STRING_REF) {
        static const char* kFrameworkClasses[] = {
            "android.os.SystemProperties",
            // F-NEW-526: hidden-but-real framework class —
            // shizuku-style reflective service holders probe it
            // in <clinit> (py7.a evidence: forName CNF swallowed
            // by the clinit catch left getService Method null ->
            // NPE at the later getService.invoke). AOSP: forName
            // succeeds on every device.
            "android.os.ServiceManager",
        };
        const std::string& fw_name = args[0].string_val;
        for (const char* fw : kFrameworkClasses) {
            if (fw_name == fw) {
                std::string fw_desc = fw;
                for (char& c : fw_desc)
                    if (c == '.') c = '/';
                fw_desc = "L" + fw_desc + ";";
                std::cerr << "[R354-FORNAME] \"" << fw_name
                          << "\" -> framework registry " << fw_desc
                          << std::endl;
                return_val = DalvikValue::make_class(fw_desc,
                                                     instruction_sequence_);
                last_invoke_return_ = return_val;
                status = ApiCallTrace::Status::IMPLEMENTED;
                // R-NEW-355: pc-advance contract — 35c invoke = 3 units.
                pc_ = pc + 3;
                return true;
            }
        }
    }

    // S58 (R-NEW-352 CLOSED): DEFAULT-ON. The recorded blocker — microtimer's
    // Room initDb loop re-visiting the SAME forName invoke 50k× and starving
    // the run budget (A/B-proven S43) — was the MISSING PC-ADVANCE CONTRACT,
    // root-caused and fixed at S44 (R-NEW-355): every forName exit below now
    // advances pc_ past the 35c invoke before returning. S58 A/B re-proof at
    // the fixed HEAD: microtimer law-ON vs law-OFF are PIXEL-IDENTICAL
    // (1,041,437 non-white both; rc=0; HALT-LOOP 0; exactly 2 forName
    // resolutions — no retry storm; run/s58_r352_lawON vs s58_r352_lawOFF).
    // MINIANDROID_R350_LAW=0 is preserved as an explicit opt-out for A/B
    // hygiene runs.
    static thread_local const bool r350_law_off =
        std::getenv("MINIANDROID_R350_LAW") != nullptr &&
        std::getenv("MINIANDROID_R350_LAW")[0] == '0';
    static thread_local const bool r350_law_on = !r350_law_off;
    if (r350_law_on && class_name == "Ljava/lang/Class;" &&
        method_name == "forName") {
        // R-NEW-350 diagnostic: the 3-arg call's name argument may arrive
        // in a non-STRING_REF register shape — log every forName arg
        // vector (env-gated) so the shape is on record.
        {
            static thread_local const bool r350shape =
                diag_env("MINIANDROID_R350_TRACE");
            static thread_local uint64_t r350shape_n = 0;
            if (r350shape && r350shape_n < 40) {
                ++r350shape_n;
                std::cerr << "[R350-SHAPE] forName argc=" << args.size();
                for (size_t si = 0; si < args.size() && si < 3; ++si)
                    std::cerr << " a" << si << "k" << (int)args[si].type;
                std::cerr << " caller=" << current_class_ << "."
                          << current_method_ << std::endl;
            }
        }
    }
    if (r350_law_on && class_name == "Ljava/lang/Class;" &&
        method_name == "forName" &&
        !args.empty() && args[0].type == DalvikType::STRING_REF) {
        // dotted binary name → L-descriptor (ordinary classes only; the
        // deterministic subset documented in FIX-M3-012b).
        const std::string& want_name = args[0].string_val;
        std::string want_desc;
        if (!want_name.empty() && want_name[0] != '[') {
            bool r350_ordinary = true;
            for (char c : want_name) {
                if (!(c == '.' || c == '/' ||
                      (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
                      (c >= '0' && c <= '9') || c == '_' || c == '$')) {
                    r350_ordinary = false;
                    break;
                }
            }
            if (r350_ordinary) {
                want_desc = want_name;
                for (char& c : want_desc)
                    if (c == '.') c = '/';
                want_desc = "L" + want_desc + ";";
            }
        }
        auto r350_cit =
            want_desc.empty()
                ? class_info_index_.end()
                : class_info_index_.find(want_desc);
        if (r350_cit == class_info_index_.end()) {
            // S84 (F-NEW-160): framework-class bridge. On a real device
            // Class.forName NEVER throws ClassNotFoundException for a
            // framework/OpenJDK class the platform ships (AOSP
            // Class.forName → BootClassLoader lookup). MiniAndroid's DEX
            // class_info_index_ only covers APK classes, so framework
            // names (android.os.Build$VERSION — hit by 9/50 S84 titles)
            // fell through to CNFE although the engine models their
            // statics (seed table). A/B law (S84, foehnix.widget):
            // bridge ONLY pure-data holder classes — instantiable engine
            // artifacts (dalvik.system.CloseGuard) returned as Class
            // objects pushed apps into Class.getMethod/Method.invoke
            // recursion storms (RECURSION-LIMIT frame-drop cascade,
            // L2→L0 regression), so they STAY on the CNFE path that real
            // app catches handle gracefully. Members later ride the
            // normal shadow / unknown-API paths.
            static const std::array<const char*, 4> r350_fw_classes = {
                "Landroid/os/Build;",
                "Landroid/os/Build$VERSION;",
                "Landroid/os/Build$VERSION_CODES;",
                "Ljava/lang/Thread;",
            };
            bool r350_is_fw =
                std::find_if(r350_fw_classes.begin(), r350_fw_classes.end(),
                             [&](const char* c) { return want_desc == c; }) !=
                r350_fw_classes.end();
            if (r350_is_fw) {
                return_val = DalvikValue::make_class(want_desc,
                                                     instruction_sequence_);
                last_invoke_return_ = return_val;
                status = ApiCallTrace::Status::IMPLEMENTED;
                pc_ = pc + 3;  // R-NEW-355 pc-advance contract
                return true;
            }
            // ── R350-DEXPATH (NOTEPAD-GAP wave 4): ART's forName resolves
            // against the FULL classpath — the APK's OWN shipped classes
            // included. The old law answered CNFE for every non-whitelisted
            // name, so androidx DataStore's protobuf-lite schema factory
            // (Class.forName("…protobuf.ExtensionSchemaFull") family —
            // reflective schema lookup by design, NOT strippable by R8)
            // failed every read, NotepadActivity's preference-gated
            // setContentView never ran, and the window captured a blank
            // theme background. Law: a forName whose L-descriptor exists in
            // the loaded DEX class index answers a REAL class token,
            // initialized per the 3-arg initialize flag (ART semantics).
            if (!class_info_index_.empty() &&
                class_info_index_.find(want_desc) != class_info_index_.end()) {
                const bool r350_dx_init =
                    args.size() >= 2 && args[1].type == DalvikType::INT32 &&
                    args[1].int_val != 0;
                if (r350_dx_init) ensure_class_initialized(want_desc);
                std::cerr << "[R351-FORNAME-DEX] \"" << want_name
                          << "\" → APK classpath class token" << std::endl;
                return_val = DalvikValue::make_class(want_desc,
                                                     instruction_sequence_);
                last_invoke_return_ = return_val;
                status = ApiCallTrace::Status::IMPLEMENTED;
                pc_ = pc + 3;
                return true;
            }
            // Real law: unknown class → ClassNotFoundException (deferred —
            // the DEX catch at the call site must observe it).
            // ISSUE-617-FORNAME-BOOTSTRAP (Minos wave): ART's forName NEVER
            // throws for a BOOTSTRAP-CLASSPATH class — android.util.Log,
            // android.view.*, org.json.*, etc. are always present on
            // device. The old law answered CNFE for every non-whitelisted
            // framework name; live face (de.tcrass.minos): greenrobot
            // EventBus's AndroidLogger.<clinit> probes
            // Class.forName("android.util.Log") to select the log backend
            // and got a deferred CNFE (R350-FORNAME) instead of a class
            // token. Law: any name in a bootstrap namespace (android.,
            // androidx., dalvik., java., javax.) answers a REAL class
            // token (3-arg initialize flag honored, R-NEW-355 pc-advance
            // kept) — member access later rides the normal shadow /
            // unknown-API paths, exactly like the whitelist above.
            {
                const bool r350_bootstrap_ns =
                    want_name.rfind("android.", 0) == 0 ||
                    want_name.rfind("androidx.", 0) == 0 ||
                    want_name.rfind("dalvik.", 0) == 0 ||
                    want_name.rfind("java.", 0) == 0 ||
                    want_name.rfind("javax.", 0) == 0;
                if (r350_bootstrap_ns) {
                    const bool r350_bs_init =
                        args.size() >= 2 && args[1].type == DalvikType::INT32 &&
                        args[1].int_val != 0;
                    if (r350_bs_init) ensure_class_initialized(want_desc);
                    static thread_local uint64_t r350_bs_n = 0;
                    if (r350_bs_n < 16) {
                        ++r350_bs_n;
                        std::cerr << "[R350-FORNAME-BOOTSTRAP] \"" << want_name
                                  << "\" → framework classpath class token"
                                  << std::endl;
                    }
                    return_val = DalvikValue::make_class(
                        want_desc, instruction_sequence_);
                    last_invoke_return_ = return_val;
                    status = ApiCallTrace::Status::IMPLEMENTED;
                    pc_ = pc + 3;
                    return true;
                }
            }
            std::cerr << "[R350-FORNAME] \"" << want_name
                      << "\" → ClassNotFoundException" << std::endl;
            throw_deferred("Ljava/lang/ClassNotFoundException;",
                           want_name, "R350-FORNAME");
            status = ApiCallTrace::Status::IMPLEMENTED;
            return_val = DalvikValue::make_null();
            last_invoke_return_ = return_val;
            // R-NEW-355 (S44): INVOKE PC-ADVANCE CONTRACT — every early
            // return from execute_invoke_static must advance pc_ past the
            // 35c invoke (3 code units). The missing advance re-executed
            // the SAME forName invoke forever: the S43 "R-NEW-352 retry
            // loop" (microtimer 50001 re-visits → HALT-LOOP) and the S44
            // SystemProperties loop (50001 re-visits → HALT-LOOP) were
            // THIS contract violation, not app-level retries. The normal
            // path at the function tail already does pc_ = pc + 3.
            pc_ = pc + 3;
            return true;
        }
        // initialize flag: 2-arg and 3-arg overloads both carry it in
        // args[1] (boolean shares the INT32 register slot).
        const bool r350_init =
            args.size() >= 2 && args[1].type == DalvikType::INT32 &&
            args[1].int_val != 0;
        if (r350_init) {
            ensure_class_initialized(want_desc);
        }
        // The returned Class object rides the invoke return path
        // (return_val → move-result-object at the call site).
        // W8 (F-NEW-511a): STABLE CLASS-TOKEN IDENTITY LAW for Class.forName
        // (same defect F-NEW-249 fixed for Object.getClass): make_class
        // stamped ref_id = instruction_sequence_ — a monotonic COUNTER,
        // not a heap id — and the CLASS_REF→shadow-arg conversion carries
        // that counter as object_id, ALIASING an arbitrary live heap object.
        // Live face (W8 survivalmanual): forName tokens aliased heap ids 24/
        // 45/66/87 (PackageManager owned 24) → the androidx.startup HashSet
        // stored "Class<KotprefInitializer>" backed by a foreign object.
        return_val = make_stable_class_token(want_desc);
        last_invoke_return_ = return_val;
        status = ApiCallTrace::Status::IMPLEMENTED;
        // R-NEW-350 log cap: microtimer's Room init calls Class.forName
        // ~50k times (Database_Impl reflection loop); an unbounded log
        // line per call turned the law into an I/O bottleneck that
        // starved the run budget (S43 sweep evidence). Log the first 16
        // resolutions only — the law itself always executes.
        {
            static thread_local uint64_t r350_ok_n = 0;
            if (r350_ok_n < 16) {
                ++r350_ok_n;
                std::cerr << "[R350-FORNAME] \"" << want_name << "\" -> "
                          << want_desc << " (initialized=" << r350_init
                          << ")" << std::endl;
            }
        }
        // R-NEW-355: pc-advance contract (see the CNFE exit above) — the
        // missing advance made every gated forName an in-place spin.
        pc_ = pc + 3;
        return true;
    }

    // ── #371 CLOSEOUT: JVMS 5.5 / AOSP ClassLinker::EnsureInitialized law
    // ── the first ACTIVE USE of a class triggers initialization, and
    // invoke-static IS an active use. sget/sput/new-instance already
    // ensured this; a class first touched via static-method invocation ran
    // uninitialized (S-2 evidence: NativeProbe.<clinit> — the canonical
    // System.loadLibrary-in-static-init pattern — never executed, so the
    // native library never loaded and every native call failed softly 0).
    // ensure_class_initialized early-exits on the already-initialized set,
    // so the per-call cost is one hash lookup.
    if (!class_name.empty() && class_name[0] == 'L')
        ensure_class_initialized(class_name);

    // EXP-038 (BLOCKER-034): Try recursive invocation.
    bool recursively_invoked = false;
    // EXP-063: Intercept getString(String, int) before recursive invoke.
    if (config_.enable_api_bridge &&
        method_name == "getString" &&
        class_name.find("LocaleController") != std::string::npos &&
        args.size() >= 1 && args[0].type == DalvikType::STRING_REF) {
        std::string res_name = args[0].string_val;
        if (!res_name.empty()) {
            auto it = resource_string_values_.find(res_name);
            if (it != resource_string_values_.end()) {
                std::cerr << "[RES] getString name=" << res_name << " val=" << it->second << std::endl;
                return_val = DalvikValue::make_string(it->second, 0);
                last_invoke_return_ = return_val;
                recursively_invoked = true;
                status = ApiCallTrace::Status::IMPLEMENTED;
            }
        }
    }
    if (!recursively_invoked && config_.enable_api_bridge) {
        // current_invoke_is_static_ is already false (reset above).
        // S188-W18 FT PROBE: FreeType-family static dispatch — did
        // try_recursive_invoke claim it, and as what?
        static thread_local const bool w18ft_d_on =
            std::getenv("MINIANDROID_W18_FT_TRACE") != nullptr;
        bool w18ft_probe = w18ft_d_on &&
            class_name.find("freetype/FreeType") != std::string::npos;
        static thread_local uint64_t w18ft_d_n = 0;
        if (w18ft_probe && w18ft_d_n++ < 200)
            std::cerr << "[W18-FT-DISP] pre-RI " << class_name << "."
                      << method_name << " proto=" << method_proto << std::endl;
        if (try_recursive_invoke(class_name, method_name, args, return_val, result, method_proto)) { last_invoke_return_ = return_val;
            recursively_invoked = true;
            status = ApiCallTrace::Status::IMPLEMENTED;
            if (w18ft_probe && w18ft_d_n < 220)
                std::cerr << "[W18-FT-DISP] RI-claimed ret_type="
                          << static_cast<int>(return_val.type)
                          << " val=" << (return_val.type == DalvikType::INT64
                                             ? (long long)return_val.long_val
                                             : (long long)return_val.int_val)
                          << std::endl;
        } else if (w18ft_probe && w18ft_d_n < 220) {
            std::cerr << "[W18-FT-DISP] RI-miss -> bridge" << std::endl;
        }
    }
    if (!recursively_invoked && config_.enable_api_bridge) {
        // current_invoke_is_static_ is still true (set at top of execute_invoke_static).
        // try_shadow_dispatch inside bridge_to_api will see it and correctly
        // treat args[0] as the first parameter (not `this`).
        bridge_to_api(class_name, method_name, args, return_val, status, method_idx); last_invoke_return_ = return_val;
        // ────────────────────────────────────────────────────────────────
        // F-NEW-326 (CONT-54): the framework-boundary static resolution
        // law. ART invoke-static resolution walks the FULL superclass
        // chain — INCLUDING past the DEX boundary into the framework — to
        // the class that actually declares the method (Dalvik spec: the
        // method must be declared in the referenced class or one of its
        // superclasses). Byte-level evidence (solitaire classes.dex):
        // five support-lib classes (DrawerLayout m@5133, NestedScrollView
        // m@5251, ActionMenuView m@7364, Toolbar m@8216, ar m@8737) carry
        // method_ids naming THEIR OWN class as the owner of
        // getChildMeasureSpec(III)I while NO class in the DEX declares it
        // (DrawerLayout's class_data jumps m@5124 -> m@5143 — the id is
        // undeclared); on a real device every such invoke resolves to the
        // framework ViewGroup.getChildMeasureSpec law. try_recursive_invoke
        // (exact local match + F-074/F-280 super-walk) only walks DEX
        // ancestors, and the first bridge dispatch keyed on the APP class
        // identity — a STUBBED typed-default answer with NO handler run.
        // Law: when (a) the named class IS a DEX class and (b) the first
        // dispatch ended STUBBED (the typed-default tail — side-effect-
        // free, so a retry cannot double-fire any handler), walk the
        // superclass chain past the DEX boundary (nearest framework
        // ancestor first, bounded 16 hops) and accept the first
        // IMPLEMENTED framework law. Otherwise the original STUBBED
        // answer stands — byte-identical to the pre-law behavior.
        // ────────────────────────────────────────────────────────────────
        if (status == ApiCallTrace::Status::STUBBED &&
            class_info_index_.find(class_name) != class_info_index_.end()) {
            std::string walk = class_name;
            for (int hop = 0; hop < 16; ++hop) {
                auto sup_it = class_to_superclass_.find(walk);
                if (sup_it == class_to_superclass_.end()) break;
                std::string sup = sup_it->second;
                if (sup.empty() || sup == "Ljava/lang/Object;") break;
                walk = sup;
                // DEX ancestors were already covered by the resolver's
                // own walk — the retry is for the FRAMEWORK boundary.
                if (class_info_index_.find(sup) != class_info_index_.end())
                    continue;
                ApiCallTrace::Status f326_st = ApiCallTrace::Status::STUBBED;
                DalvikValue f326_rv = DalvikValue::make_void();
                bridge_to_api(sup, method_name, args, f326_rv, f326_st,
                              method_idx);
                if (f326_st == ApiCallTrace::Status::IMPLEMENTED) {
                    static thread_local uint64_t f326_redispatch_n = 0;
                    if (f326_redispatch_n < 40) {
                        ++f326_redispatch_n;
                        std::cerr << "[F-NEW-326] static re-dispatch "
                                  << class_name << "." << method_name
                                  << " as " << sup
                                  << " (framework boundary)" << std::endl;
                    }
                    return_val = f326_rv;
                    last_invoke_return_ = f326_rv;
                    status = f326_st;
                    break;
                }
            }
        }
    }

    ApiCallTrace api_trace;
    api_trace.sequence = api_call_sequence_++;
    api_trace.api_class = class_name;
    api_trace.method = method_name;
    api_trace.status = status;
    api_trace.pc = pc;
    note_api_status(api_trace);  // F-NEW-200 census
    batched_cap_push(result.api_call_traces, result.api_call_ring_cursor, static_cast<size_t>(config_.api_call_trace_cap), std::move(api_trace));

    // S157-B: trace_cap==0 gate (never-read trace — see iget block).
    if (config_.trace_cap > 0) {
    trace.invoked_method = class_name + "." + method_name;
    }

    // R-NEW-339 temp probe: every invoke-static dispatched from
    // Lt4;.<init> (AndroidComposeView ctor) — trace which call yields a
    // null/void where an object was expected around the autofill fetch.
    if (current_class_ == "Lt4;" && current_method_ == "<init>") {
        static thread_local uint64_t t4probe = 0;
        if (t4probe < 120) {
            ++t4probe;
            std::cerr << "[T4PROBE] invoke-static " << class_name << "."
                      << method_name << " pc=" << pc
                      << " ret_type=" << static_cast<int>(return_val.type)
                      << " ret_oid=" << return_val.object_id
                      << " ret_cls=" << return_val.class_desc
                      << std::endl;
        }
    }

    // EXP-071 Phase 7: Restore the saved static flag.
    current_invoke_is_static_ = saved_is_static;
    pc_ = pc + 3;
    return true;
}

bool DalvikExecutionEngine::execute_invoke_interface(uint32_t pc, InstructionTrace& trace,
                                                   DalvikExecutionResult& result) {
    // Similar to other invokes but for interface dispatch
    if (pc + 2 >= bytecode_.size()) return false;

    // ────────────────────────────────────────────────────────────────────
    // F-023 (EXP-071 Phase 7 completion — invoke-interface INSTANCE law):
    // execute_invoke_static/virtual/direct each SAVE + RESET + RESTORE
    // current_invoke_is_static_ at their boundary. invoke-interface is an
    // INSTANCE call form but was forgotten, so any ancestor window that had
    // left the flag true (e.g. a static-dispatched entry frame) leaked into
    // try_recursive_invoke's M3-19/F-017 active-cycle key construction —
    // the receiver's #object_id suffix was skipped for ALL
    // interface-dispatched methods. Same-class re-entrancy across different
    // instances (CombinedContext.get recursing over a CoroutineContext
    // chain) then collided into ONE key and was stubbed null mid-fold; the
    // null fed kotlin.coroutines plus → CombinedContext.<init>
    // checkNotNullParameter → the NPE that killed Compose composition
    // before the first frame (dooz M1/i.f).
    // Scope-guard restore covers every return path below.
    // ────────────────────────────────────────────────────────────────────
    const bool saved_is_static = current_invoke_is_static_;
    current_invoke_is_static_ = false;
    struct IsStaticRestore {
        bool& flag; bool saved;
        ~IsStaticRestore() { flag = saved; }
    } is_static_restore{current_invoke_is_static_, saved_is_static};

    uint16_t instr = bytecode_[pc];
    // EXP-045: Only push argc registers (from 35c format: high nibble of high byte)
    uint8_t argc = (instr >> 12) & 0xF;
    uint16_t method_idx = bytecode_[pc + 1];
    uint16_t regs_word = bytecode_[pc + 2];

    uint8_t regs[5] = {
        static_cast<uint8_t>(regs_word & 0xF),
        static_cast<uint8_t>((regs_word >> 4) & 0xF),
        static_cast<uint8_t>((regs_word >> 8) & 0xF),
        static_cast<uint8_t>((regs_word >> 12) & 0xF),
        static_cast<uint8_t>((instr >> 8) & 0xF)
    };

    std::vector<DalvikValue> args;
    for (int i = 0; i < argc && i < 5; ++i) {
        args.push_back(get_register(regs[i]));
    }

    // CYCLE-E: signature-aware param conversion for invoke-interface (35c).
    // See execute_invoke_virtual for the full rationale.
    // F-090i (R-NEW-322): hoisted proto — also the callee's exact descriptor
    // for the F-023 overload law at every DEX dispatch site below.
    std::string iface_proto;
    if (dex_report_) {
        // CONT-96 W3-B: memo entry (proto string + parsed params resolve once).
        const auto& mre = method_resolve_entry(current_dex_index_, method_idx);
        iface_proto = mre.proto;
        if (iface_proto != "<unknown>") {
            args = build_invoke_args(args, mre.proto_params,
                                     /*is_static=*/false);
        } else {
            iface_proto.clear();
        }
    }

    // EXP-037 Phase B (BLOCKER-002 FIX): resolve method_idx via DexReport.
    std::string method_name = "<interface_method:" + std::to_string(method_idx) + ">";
    std::string class_name = "<interface>";
    if (dex_report_) {
        method_name = resolve_method_name_for_dex(method_idx, current_dex_index_);
        class_name = resolve_method_class_for_dex(method_idx, current_dex_index_);
    }

    // ────────────────────────────────────────────────────────────────────────
    // CONT-37 (F-NEW-298 evidence, DIAG-ONLY): UV-DISPATCH watch. The Compose
    // text painter (Lte1/Lod1) reaches the canvas ONLY as a Luv draw block
    // through Loc0.c — this is the APK's SINGLE Luv;->I dispatch site. Log
    // the receiver's runtime class per dispatch: answers WHICH draw blocks
    // actually run per frame (observed: only 20 of 82 D0 walk nodes reach
    // here; the text painter's I never fires). Env-gated, bounded — zero
    // behavior change.
    // ────────────────────────────────────────────────────────────────────────
    {
        static thread_local const bool uvw_on =
            diag_env("MINIANDROID_UV_WATCH");
        if (uvw_on && class_name == "Luv;" && method_name == "I") {
            static thread_local uint64_t uvw_n = 0;
            if (uvw_n++ < 400) {
                const char* uvw_t = "(noargs)";
                if (!args.empty()) {
                    if (args[0].type == DalvikType::OBJECT_REF)
                        uvw_t = args[0].class_desc.c_str();
                    else if (args[0].type == DalvikType::NULL_REF)
                        uvw_t = "NULL";
                    else
                        uvw_t = "other";
                }
                std::cerr << "[UV-DISPATCH] recv-cls=" << uvw_t
                          << " obj=" << (args.empty() ? 0u : args[0].object_id)
                          << " caller=" << current_class_ << "."
                          << current_method_;
                // CONT-37: dump the receiver's attached flag (Lok0.r) — the
                // painter body's first gate — plus the coordinator field (l)
                // identity, to answer whether attach state survived to draw.
                if (!args.empty() &&
                    args[0].type == DalvikType::OBJECT_REF) {
                    auto rf = heap_.get_object_field(args[0].object_id, "r");
                    auto lf = heap_.get_object_field(args[0].object_id, "l");
                    std::cerr << " r="
                              << (rf ? std::to_string(rf->bool_val)
                                     : std::string("?"))
                              << " l="
                              << (lf ? std::to_string(lf->object_id)
                                     : std::string("?"));
                }
                std::cerr << std::endl;
            }
        }
    }

    // ── S173 NDFE probe (interface path, env-gated, bounded 96) ─────────
    // Same evidence as the [S173-CHM-V] block in execute_invoke_virtual:
    // the Koin index (desugared j$ ConcurrentHashMap) may be reached
    // through an interface-typed slot (invoke-interface on Lj$/util/Map;).
    if (diag_env("MINIANDROID_S173_PROBE") &&
        class_name.find("ConcurrentHashMap") != std::string::npos &&
        (current_method_.find("resolveDefinition") != std::string::npos ||
         current_class_ == "Lorg/slf4j/event/EventRecodingLogger;")) {
        static thread_local uint64_t s173_chm_i = 0;
        if (s173_chm_i < 200 && args.size() >= 2 &&
            args[1].type == DalvikType::STRING_REF) {
            ++s173_chm_i;
            const std::string& keydesc = args[1].string_val;
            std::cerr << "[S173-CHM-I] " << method_name
                      << " argc=" << args.size()
                      << " key=\"" << keydesc << "\""
                      << " caller=" << current_class_ << "."
                      << current_method_ << " pc=" << pc << std::endl;
        }
    }

    // ── F-068 (R-NEW-292): RUNTIME-CLASS-FIRST interface dispatch law ─────
    // DEX invoke-interface dispatch: ART resolves the target against the
    // RECEIVER'S RUNTIME CLASS — the most specific implementation among
    // the class hierarchy and the interfaces it implements. The declared
    // interface in the method ref supplies only the SIGNATURE; a default
    // method body living on the declared interface executes ONLY when the
    // runtime class does not override it.
    // The old order tried the DECLARED interface first. For interfaces
    // WITH default bodies that shadows the receiver's real override:
    // androidx F$b (ViewModelProvider.Factory, R8) has a default
    // b(Class, CreationExtras) that delegates to a throwing a(Class)
    // ("Factory.create(String) is unsupported…"), while the actual
    // factory Lf1/b (the viewModelFactory{} initializer-lambda SAM)
    // overrides b(Class, extras). Dooz SavedStateHandlesVM.create went
    // through the throwing default → UnsupportedOperationException →
    // MainActivity.onCreate died at invoke_pc=109 → first frame died.
    // Runtime-first also honors the simple case: abstract interfaces miss
    // on the runtime class and fall through unchanged.
    DalvikValue return_val = DalvikValue::make_void();
    // F-141 (S72-W3): ART null-receiver law — invoke-interface with a null
    // receiver throws NPE at the call site (ART: "Attempt to invoke
    // interface method '<sig>' on a null object reference"). Previously
    // the dispatch walk ran with heap_obj = nullptr and silent null
    // semantics.
    if (!args.empty() && f141_is_null_receiver(args[0])) {
            dump_frame_locals_diag("F141-OP");
        throw_deferred("Ljava/lang/NullPointerException;",
                       "Attempt to invoke interface method '" + class_name +
                           "." + method_name + "' on a null object reference",
                       "f141-null-recv");
        pc_ += 3;  // 35c length; a catch handler redirect overrides pc
        return true;
    }
    // Resolve the receiver's heap object once for the whole dispatch walk.
    const auto* heap_obj =
        (!args.empty() && args[0].type == DalvikType::OBJECT_REF &&
         heap_.has_object(args[0].object_id))
            ? heap_.get(args[0].object_id)
            : nullptr;
    // ── F-068 (R-NEW-292): RUNTIME-CLASS-FIRST interface dispatch law ─────
    // DEX invoke-interface dispatch: ART resolves the target against the
    // RECEIVER'S RUNTIME CLASS — the most specific implementation among
    // the class hierarchy and the interfaces it implements. The declared
    // interface in the method ref supplies only the SIGNATURE; a default
    // method body living on the declared interface executes ONLY when the
    // runtime class does not override it.
    // The old order tried the DECLARED interface first. For interfaces
    // WITH default bodies that shadows the receiver's real override:
    // androidx F$b (ViewModelProvider.Factory, R8) has a default
    // b(Class, CreationExtras) that delegates to a throwing a(Class)
    // ("Factory.create(String) is unsupported…"), while the actual
    // factory Lf1/b (the viewModelFactory{} initializer-lambda SAM)
    // overrides b(Class, extras). Dooz SavedStateHandlesVM.create went
    // through the throwing default → UnsupportedOperationException →
    // MainActivity.onCreate died at invoke_pc=109 → first frame died.
    if (heap_obj && !heap_obj->class_descriptor.empty() &&
        heap_obj->class_descriptor != class_name) {
        // F-NEW-281c: EXACT (name, descriptor) gate on the runtime-class-
        // first arm. JVMS 5.4.3.4: a same-name different-proto method is
        // NEVER a candidate for an interface invoke. With a concrete call-
        // site proto, this arm may dispatch via try_recursive_invoke's
        // legacy lenient (name-only) selection — which let a same-name
        // WRONG-shape overload win BEFORE the interface-default search
        // could run. Live face (real-Compose oracle): Factory.create(
        // KClass, extras) dispatched InitializerViewModelFactory.create(
        // Class, extras) — the KClass flowed into the Class slot,
        // getKotlinClass re-wrapped it, and the initializer match failed
        // with IAE "No initializer set for given class null" → APP
        // BOUNDARY. Gate: when the proto is resolvable, the runtime class
        // chain must declare an EXACT (name, proto) non-abstract method
        // for this arm to fire; otherwise control proceeds to the
        // declared-interface and interface-hierarchy default search
        // (F-023 / F-NEW-281), which find the TRUE candidate. Empty proto
        // keeps the legacy behavior unchanged.
        bool f281c_exact = false;
        if (!iface_proto.empty() && dex_report_) {
            std::string f281c_cls = heap_obj->class_descriptor;
            for (int f281c_hop = 0;
                 f281c_hop < 8 && !f281c_cls.empty() && !f281c_exact;
                 ++f281c_hop) {
                for (const auto& cls : dex_report_->classes) {
                    if (cls.name != f281c_cls) continue;
                    for (const auto& mi : cls.all_methods()) {
                        // S188-W17 (F-NEW-601) native-exact law: an
                        // ACC_NATIVE method has code_offset==0 and is NOT
                        // abstract — it is a REAL dispatch target (AOSP
                        // art_method: entry points, not "no method").
                        // Live evidence (p9, /tmp/p9probe.log): the
                        // interface call GL20.glCreateShader(I)I on the
                        // AndroidGL20 receiver skipped this walk entirely
                        // (native skipped by code_offset==0) →
                        // S186I-STUB answered 0 → ShaderProgram
                        // isCompiled=false → IllegalArgumentException
                        // "Error compiling shader" → APP BOUNDARY unwind
                        // before the first frame. An interface call whose
                        // runtime class declares a native with the EXACT
                        // name+descriptor is an EXACT hit; the native
                        // block in try_recursive_invoke runs it.
                        if (mi.is_abstract) continue;
                        if (mi.code_offset == 0 &&
                            !(mi.access_flags & 0x100))
                            continue;
                        if (mi.name != method_name) continue;
                        if (mi.descriptor == iface_proto) {
                            f281c_exact = true;
                            break;
                        }
                    }
                    break;  // found the class def
                }
                if (f281c_exact) break;
                auto f281c_sup = class_to_superclass_.find(f281c_cls);
                if (f281c_sup == class_to_superclass_.end()) break;
                f281c_cls = f281c_sup->second;
                if (f281c_cls == "Ljava/lang/Object;") break;
            }
        }
        // CONT-37 (F-NEW-298 evidence, DIAG-ONLY): log the f281c gate result
        // for the draw-block dispatch (Luv;.I) — if the exact walk misses a
        // method that exists, the runtime-first arm is skipped and the
        // dispatch falls to the deeper fallbacks (observed: painter paint
        // dispatch never reaches the body).
        if (diag_env("MINIANDROID_UV_WATCH") && class_name == "Luv;" &&
            method_name == "I" &&
            (heap_obj->class_descriptor == "Lte1;" ||
             heap_obj->class_descriptor == "Lod1;")) {
            static thread_local uint64_t uvf_n = 0;
            if (uvf_n++ < 60)
                std::cerr << "[UV-F281C] recv=" << heap_obj->class_descriptor
                          << " obj=" << (args.empty() ? 0u : args[0].object_id)
                          << " proto=" << iface_proto
                          << " exact=" << (f281c_exact ? 1 : 0)
                          << std::endl;
        }
        if (f281c_exact || iface_proto.empty())
        // F-090i (R-NEW-322): pass the interface proto as the exact
        // descriptor so the F-023 overload law resolves same-name
        // overloads on the runtime class correctly.
        if (try_recursive_invoke(heap_obj->class_descriptor, method_name,
                                 args, return_val, result, iface_proto)) {
            // S59 R-NEW-379 DIAG: the runtime-first dispatch claims success
            // — surface the resolved class/method and the return shape so
            // silent typed-zero/void returns become visible.
            if (diag_env("MINIANDROID_IFACE_FAIL_TRACE")) {
                fprintf(stderr,
                        "[IFACE-RT] %s.%s%s via runtime %s (recv obj#%u) "
                        "ret_type=%d ret_id=%u ret_int=%d\n",
                        class_name.c_str(), method_name.c_str(),
                        iface_proto.c_str(),
                        heap_obj->class_descriptor.c_str(),
                        args.empty() ? 0u : args[0].object_id,
                        static_cast<int>(return_val.type), return_val.object_id,
                        return_val.type == DalvikType::INT32 ? return_val.int_val
                        : (return_val.type == DalvikType::BOOLEAN ? (return_val.int_val != 0 ? 1 : 0) : -1));
                // S59: dump the receiver's stored fields for empty returns
                // (Ljj;.a returned empty for every KClass — was the <init>
                // iput ever persisted?)
                if (return_val.type != DalvikType::OBJECT_REF) {
                    std::string fl;
                    for (const auto& [fn, fv] : heap_obj->fields) {
                        fl += fn + "(t" + std::to_string(static_cast<int>(fv.type)) +
                              ",id" + std::to_string(fv.object_id) + ") ";
                    }
                    fprintf(stderr, "[IFACE-RT]   recv fields: %s\n",
                            fl.c_str());
                }
            }
            last_invoke_return_ = return_val;
            // S157-B: trace_cap==0 gate (never-read trace).
            if (config_.trace_cap > 0) {
            trace.invoked_method =
                heap_obj->class_descriptor + "." + method_name;
            }
            pc_ = pc + 3;
            return true;
        }
    }
    // Declared-interface dispatch — executes default bodies on the
    // interface itself (F-023 semantics for non-overridden defaults) and
    // still catches the historical "interface methods with impls" cases.
    if (try_recursive_invoke(class_name, method_name, args, return_val, result,
                             iface_proto)) { last_invoke_return_ = return_val;
        // S157-B: trace_cap==0 gate (never-read trace).
        if (config_.trace_cap > 0) {
        trace.invoked_method = class_name + "." + method_name;
        }
        pc_ = pc + 3;
        return true;
    }
    if (heap_obj) {
        // ────────────────────────────────────────────────────────────────
        // M3 F-ROOM-CHAIN (R8 interface-dispatch law): R8 renames the
        // interface method and the implementation method INDEPENDENTLY
        // (e.g. interface Lg/h;->X(IJ)V is implemented as Le/x;->h(IJ)V).
        // A NAME lookup on the runtime class then misses and the call
        // silently degrades to a void stub — exactly how Room's
        // EntityInsertionAdapter.bind lost every parameter bind (insert →
        // NOT NULL constraint failed on microtimer's alarm table). DEX
        // dispatch law: renaming preserves parameter/return types, so when
        // the name lookup misses, resolve by EXACT signature (descriptor)
        // inside the receiver's runtime class and dispatch THAT method.
        // ────────────────────────────────────────────────────────────────
        // F-090i: iface_proto is hoisted above — reuse it here.
        if (!iface_proto.empty()) {
            // F-091b (R-NEW-324, S25): ART interface-dispatch gate on the
            // descriptor-only walk below. The walk is ONLY legal when the
            // declared interface is itself DEX-defined — the R8 case where
            // interface method and implementation are renamed INDEPENDENTLY
            // (the descriptor stays the stable identity). For HOST
            // interfaces (Ljava/util/Iterator;, Ljava/util/Collection;, …)
            // R8 cannot rename: the name IS the contract and the name-based
            // dispatch above is authoritative. Descriptor-guessing on a
            // host interface dispatches an UNRELATED method that merely
            // shares the proto — dooz proof: Iterator.hasNext() →
            // z1/i.isEmpty() (first ()Z on the chain) → hasNext()=false
            // for a NON-EMPTY list → addAll's bulk-copy zero-iterated →
            // the NavController back stack lost the root-graph entry
            // (R-NEW-323 IAE).
            bool f91b_dex_interface = false;
            if (!class_name.empty() && dex_report_) {
                for (const auto& f91b_cls : dex_report_->classes) {
                    if (f91b_cls.name == class_name) {
                        f91b_dex_interface = true;
                        break;
                    }
                }
            }
            if (f91b_dex_interface) {
            // F-NEW-281: ART invoke-interface resolution law (JVMS
            // 5.4.3.4): the candidate must match the (NAME, descriptor)
            // pair — a same-descriptor different-name method is NEVER a
            // candidate. The descriptor-only walk below is the R8
            // independent-rename FALLBACK and must run LAST.
            // Oracle proof of the gap: CompositionLocalAccessorScope.
            // getCurrentValue(local) on a PersistentCompositionLocalHashMap
            // receiver — the class declares no getCurrentValue, so the
            // descriptor walk picked the FIRST same-shape method, the raw
            // PersistentMap.get override (invoke-super + check-cast
            // ValueHolder + return), answering a ValueHolder where the
            // accessor law demands readValue()'s value; the real
            // implementation is the inherited interface DEFAULT
            // PersistentCompositionLocalMap.getCurrentValue = read(this)
            // (getOrElse(key){defaultValueHolder}.readValue(this)).
            // Order: (1) exact (name, descriptor) in the receiver's class
            // chain; (2) exact (name, descriptor) DEFAULT body in the
            // interface hierarchy (receiver interfaces, transitive,
            // bounded); (3) legacy descriptor-only walk (unchanged).
            bool f281_diag = diag_env("MINIANDROID_F281_TRACE");
            {
                std::string f281_walk = heap_obj->class_descriptor;
                for (int hop = 0; hop < 8 && !f281_walk.empty(); ++hop) {
                    for (const auto& cls : dex_report_->classes) {
                        if (cls.name != f281_walk) continue;
                        for (const auto& mi : cls.all_methods()) {
                            if (mi.code_offset == 0 || mi.is_abstract) continue;
                            if (mi.descriptor != iface_proto) continue;
                            if (mi.name != method_name) continue;
                            if (try_recursive_invoke(f281_walk, mi.name, args,
                                                     return_val, result)) {
                                last_invoke_return_ = return_val;
                                trace.invoked_method =
                                    f281_walk + "." + mi.name;
                                if (f281_diag)
                                    std::cerr << "[F281-IFACE-NAME] "
                                              << f281_walk << "." << mi.name
                                              << iface_proto
                                              << " (exact name+descriptor, class chain; call-site "
                                              << class_name << "." << method_name
                                              << ") → REAL DEX dispatched"
                                              << std::endl;
                                pc_ = pc + 3;
                                return true;
                            }
                        }
                        break;  // found the class def; stop scanning classes
                    }
                    auto sup_it = class_to_superclass_.find(f281_walk);
                    if (sup_it == class_to_superclass_.end()) break;
                    f281_walk = sup_it->second;
                    if (f281_walk == "Ljava/lang/Object;") break;
                }
            }
            {
                // (2) interface-hierarchy DEFAULT bodies, exact
                // (name, descriptor). BFS from the receiver's direct
                // interfaces through super-interfaces (bounded 16 levels).
                std::vector<std::string> f281_q;
                auto ifc_it = class_to_interfaces_.find(
                    heap_obj->class_descriptor);
                if (ifc_it != class_to_interfaces_.end())
                    f281_q = ifc_it->second;
                for (int level = 0; level < 16 && !f281_q.empty(); ++level) {
                    std::vector<std::string> f281_next;
                    for (const auto& ifc : f281_q) {
                        bool ifc_has_def = false;
                        for (const auto& cls : dex_report_->classes) {
                            if (cls.name != ifc) continue;
                            for (const auto& mi : cls.all_methods()) {
                                if (mi.code_offset == 0 || mi.is_abstract)
                                    continue;
                                if (mi.descriptor != iface_proto) continue;
                                if (mi.name != method_name) continue;
                                ifc_has_def = true;
                                if (try_recursive_invoke(ifc, mi.name, args,
                                                         return_val, result)) {
                                    last_invoke_return_ = return_val;
                                    trace.invoked_method = ifc + "." + mi.name;
                                    if (f281_diag)
                                        std::cerr << "[F281-IFACE-DEFAULT] "
                                                  << ifc << "." << mi.name
                                                  << iface_proto
                                                  << " (interface-hierarchy default; call-site "
                                                  << class_name << "."
                                                  << method_name
                                                  << ") → REAL DEX dispatched"
                                                  << std::endl;
                                    pc_ = pc + 3;
                                    return true;
                                }
                            }
                            break;  // found the interface def
                        }
                        if (!ifc_has_def) {
                            auto sup_ifc = class_to_interfaces_.find(ifc);
                            if (sup_ifc != class_to_interfaces_.end())
                                for (const auto& p : sup_ifc->second)
                                    f281_next.push_back(p);
                        }
                    }
                    f281_q = f281_next;
                }
            }
            // Walk the receiver's class + superclass chain (DEX virtual
            // dispatch law: inherited implementations answer interface
            // calls; R8 renames per class, so the signature is the only
            // stable identity).
            std::string walk_cls = heap_obj->class_descriptor;
            for (int hop = 0; hop < 8 && !walk_cls.empty(); ++hop) {
                bool cls_found = false;
                for (const auto& cls : dex_report_->classes) {
                    if (cls.name != walk_cls) continue;
                    cls_found = true;
                    bool sig_found = false;
                    for (const auto& mi : cls.all_methods()) {
                        if (mi.code_offset == 0 || mi.is_abstract) continue;
                        if (mi.descriptor != iface_proto) continue;
                        sig_found = true;
                        if (try_recursive_invoke(walk_cls, mi.name, args,
                                                 return_val, result)) {
                            last_invoke_return_ = return_val;
                            trace.invoked_method =
                                walk_cls + "." + mi.name +
                                " [sig-dispatch " + iface_proto + "]";
                            std::cerr << "[INTERFACE-SIG] " << walk_cls << "."
                                      << mi.name << iface_proto
                                      << " (interface " << class_name << "."
                                      << method_name << ") → REAL DEX dispatched"
                                      << std::endl;
                            pc_ = pc + 3;
                            return true;
                        }
                    }
                    if (sig_found) break;
                    break;  // found the class def; stop scanning classes
                }
                auto sup_it = class_to_superclass_.find(walk_cls);
                if (sup_it == class_to_superclass_.end()) break;
                walk_cls = sup_it->second;
                if (walk_cls == "Ljava/lang/Object;") break;
            }
            } // end F-091b DEX-interface gate

            // ────────────────────────────────────────────────────────────
            // F-023 (DEX DEFAULT-INTERFACE-METHOD DISPATCH LAW): the class
            // extends-walk cannot see methods that live ON an interface
            // with code (DEX default methods). ART law: invoke-interface
            // consults every transitively implemented interface of the
            // receiver, including default methods. Generic: collect the
            // implements-set of each class in the receiver's extends
            // chain, close it over super-interfaces (bounded), then
            // dispatch the method matching the EXACT descriptor with code.
            // (Real-APK evidence: AndroidUiFrameClock.getKey default —
            // CoroutineContext.plus NPE before first frame.)
            // ────────────────────────────────────────────────────────────
            // 1. Receiver extends-chain (bounded).
            std::vector<std::string> cls_chain;
            std::string c = heap_obj->class_descriptor;
            for (int hop = 0; hop < 12 && !c.empty() &&
                              c != "Ljava/lang/Object;"; ++hop) {
                cls_chain.push_back(c);
                auto it2 = class_to_superclass_.find(c);
                if (it2 == class_to_superclass_.end()) break;
                c = it2->second;
            }
            // 2. Implements-set with transitive super-interfaces.
            std::vector<std::string> ifq;
            std::set<std::string> visited;
            auto enqueue_ifaces = [&](const std::string& cls) {
                for (const auto& cd : dex_report_->classes) {
                    if (cd.name != cls) continue;
                    for (const auto& ifc : cd.interfaces) {
                        if (!ifc.empty() && visited.insert(ifc).second) {
                            ifq.push_back(ifc);
                        }
                    }
                    break;  // found the class def
                }
            };
            for (const auto& cc : cls_chain) enqueue_ifaces(cc);
            for (size_t qi = 0; qi < ifq.size() && qi < 64; ++qi) {
                enqueue_ifaces(ifq[qi]);  // super-interfaces
            }
            // 3. Dispatch a default method with the exact descriptor
            //    (code, non-abstract).
            for (const auto& ifc : ifq) {
                for (const auto& cd : dex_report_->classes) {
                    if (cd.name != ifc) continue;
                    for (const auto& mi : cd.all_methods()) {
                        if (mi.code_offset == 0 || mi.is_abstract) continue;
                        if (mi.descriptor != iface_proto) continue;
                        if (try_recursive_invoke(ifc, mi.name, args,
                                                 return_val, result,
                                                 iface_proto)) {
                            last_invoke_return_ = return_val;
                            trace.invoked_method =
                                ifc + "." + mi.name +
                                " [default-method " + iface_proto + "]";
                            std::cerr << "[INTERFACE-DEFAULT] " << ifc << "."
                                      << mi.name << iface_proto
                                      << " (interface " << class_name << "."
                                      << method_name << ") → REAL DEX dispatched"
                                      << std::endl;
                            pc_ = pc + 3;
                            return true;
                        }
                    }
                    break;  // found the interface def
                }
            }
        }
    }
    if (!heap_obj && !args.empty() && method_name == "addFragmentToStack") {
        // EXP-058: Debug — why is interface dispatch not working?
        int arg0_type = static_cast<int>(args[0].type);
        uint32_t arg0_obj = args[0].object_id;
        bool has_obj = heap_.has_object(arg0_obj);
        std::string heap_class = has_obj ? heap_.get(arg0_obj)->class_descriptor : "<no heap obj>";
        std::cerr << "[EXP058-IFACE] addFragmentToStack dispatch failed"
                  << " arg0_type=" << arg0_type
                  << " arg0_obj=" << arg0_obj
                  << " has_heap_obj=" << has_obj
                  << " heap_class=" << heap_class
                  << " static_class=" << class_name
                  << std::endl;
    }

    // S59 R-NEW-379 DIAG (env-gated): why did the interface dispatch end
    // at the bridge fallback? Logs the receiver identity and heap state
    // for every interface call that reached this point without a REAL DEX
    // dispatch (no runtime-class hit, no declared-interface body, no
    // signature/default-method walk success).
    if (diag_env("MINIANDROID_IFACE_FAIL_TRACE") &&
        !args.empty()) {
        const DalvikValue& r0 = args[0];
        std::string r0_heap = "<none>";
        if (r0.type == DalvikType::OBJECT_REF && r0.object_id != 0 &&
            heap_.has_object(r0.object_id)) {
            r0_heap = heap_.get(r0.object_id)->class_descriptor;
        }
        fprintf(stderr,
                "[IFACE-FAIL] %s.%s%s recv_type=%d recv_id=%u recv_tag=%s "
                "heap=%s\n",
                class_name.c_str(), method_name.c_str(), iface_proto.c_str(),
                static_cast<int>(r0.type), r0.object_id,
                r0.class_desc.c_str(), r0_heap.c_str());
    }

    // EXP-048: Fall through to bridge_to_api for interface methods
    // F-090d (R-NEW-318): the bridge key must be the RECEIVER'S RUNTIME
    // class — the same EXP-059 law execute_invoke_virtual already applies.
    // The declared interface supplies only the SIGNATURE; framework API
    // handlers are keyed by implementation classes. Live evidence (dooz):
    // `route.isNotBlank()` compiled to invoke-interface
    // CharSequence.length()/charAt() on a real String; bridging with
    // "Ljava/lang/CharSequence;" found no handler → length answered 0 →
    // isBlank=true → NavDestination.setRoute IAE "Cannot have an empty
    // route" → MainActivity.onCreate died → Compose never composed.
    ApiCallTrace::Status status = ApiCallTrace::Status::STUBBED;
    if (config_.enable_api_bridge) {
        std::string api_cls = class_name;
        if (heap_obj && !heap_obj->class_descriptor.empty()) {
            api_cls = heap_obj->class_descriptor;
        } else if (!args.empty() && args[0].type == DalvikType::STRING_REF) {
            // String constants ride STRING_REF without a heap object; the
            // runtime class of any CharSequence-typed constant is String.
            api_cls = "Ljava/lang/String;";
        } else if (!args.empty() &&
                   args[0].type == DalvikType::OBJECT_REF &&
                   !args[0].class_desc.empty()) {
            api_cls = args[0].class_desc;
        }
        bridge_to_api(api_cls, method_name, args, return_val, status, method_idx); last_invoke_return_ = return_val;
    }

    ApiCallTrace api_trace;
    api_trace.sequence = api_call_sequence_++;
    api_trace.api_class = class_name;
    api_trace.method = method_name;
    api_trace.status = status;
    api_trace.pc = pc;
    note_api_status(api_trace);  // F-NEW-200 census
    batched_cap_push(result.api_call_traces, result.api_call_ring_cursor, static_cast<size_t>(config_.api_call_trace_cap), std::move(api_trace));

    trace.invoked_method = class_name + "." + method_name;

    pc_ = pc + 3;
    return true;
}

// ============================================================================
// OPCODE IMPLEMENTATIONS — Returns
// ============================================================================

bool DalvikExecutionEngine::execute_return_void(uint32_t pc, InstructionTrace& trace) {
    // Format: 10x [op] {} (no operands)
    trace.status = InstructionTrace::Status::HALT_RETURN;
    trace.return_value = DalvikValue::make_void();
    
    halted_ = true;
    halted_on_return_ = true;
    
    log("  RETURN_VOID at " + to_hex(pc));
    
    pc_ = pc + 1;
    return true;
}

bool DalvikExecutionEngine::execute_return(uint32_t pc, InstructionTrace& trace) {
    // Format: 11x [op] vAA (1 code unit)
    if (pc >= bytecode_.size()) return false;
    
    uint16_t instr = bytecode_[pc];
    uint8_t ret_reg = (instr >> 8) & 0xFF;
    
    DalvikValue val = get_register(ret_reg);
    
    // CHAR-PROBE campaign: signature-aware return typing. DEX registers are
    // untyped 32-bit cells — a boolean/char/byte/short return leaves the
    // register as raw INT32. Downstream consumers (StringBuilder.append,
    // string concat, ==/!= flows into text) then render "88" for 'X' or
    // "0"/"1" for false/true. Retype by the method's return-type descriptor
    // char, exactly per the Dalvik spec: only raw INT32 is reinterpreted;
    // already-typed values pass through untouched.
    if (val.type == DalvikType::INT32 &&
        current_method_descriptor_.size() >= 2) {
        size_t rparen = current_method_descriptor_.find(')');
        if (rparen != std::string::npos &&
            rparen + 1 < current_method_descriptor_.size()) {
            char rt = current_method_descriptor_[rparen + 1];
            switch (rt) {
                case 'Z':
                    val = DalvikValue::make_bool(val.int_val != 0);
                    break;
                case 'C':
                    val.type = DalvikType::CHAR;
                    val.int_val &= 0xFFFF;
                    break;
                case 'B':
                    val.type = DalvikType::BYTE;
                    val.int_val = static_cast<int8_t>(val.int_val & 0xFF);
                    break;
                case 'S':
                    val.type = DalvikType::SHORT;
                    val.int_val = static_cast<int16_t>(val.int_val & 0xFFFF);
                    break;
                default:
                    break;   // I/J/F/D/L/[/V — leave as-is
            }
        }
    }
    
    trace.status = InstructionTrace::Status::HALT_RETURN;
    trace.return_value = val;
    trace.operands.push_back({"v" + std::to_string(ret_reg), val.to_string()});
    
    // EXP-055: Store the return value so try_recursive_invoke can
    // propagate it to the caller. Previously, return_val was always
    // make_void() — so every recursive invoke returned void, and
    // move-result after an invoke always got 0/null. This caused
    // isClientActivated to return void (treated as false), which
    // happened to be correct for the login path but was fundamentally
    // broken for any method that returns a non-zero value.
    last_invoke_return_ = val;
    
    // EXP-059: Debug — log return values for onFragmentCreate and addFragmentToStack
    if (current_method_ == "onFragmentCreate" ||
        (current_method_ == "addFragmentToStack" &&
         current_class_.find("ActionBarLayout") != std::string::npos)) {
        std::cerr << "[EXP059-RETURN] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " ret_reg=v" << (int)ret_reg
                  << " type=" << static_cast<int>(val.type)
                  << " int_val=" << val.int_val
                  << " obj=" << val.object_id
                  << std::endl;
    }

    // F-044 DIAG (env-gated, diagnostic only): the live dooz derived-state
    // record-validity law (LF/F$a.c watermark/version check) mis-executes —
    // expose the exact DEX-level return values of the two law methods so the
    // comparison (record.g vs re-scanned dependency version) can be traced.
    {
        static thread_local const bool f044 = std::getenv("MINIANDROID_F044_DIAG") != nullptr;
        if (f044 && current_class_ == "LF/F$a;" && current_method_ == "d") {
            std::cerr << "[F044-DIAG] " << current_class_ << "." << current_method_
                      << "() return type=" << static_cast<int>(val.type)
                      << " int_val=" << val.int_val
                      << " obj=" << val.object_id
                      << std::endl;
            // One-shot register-file dump at return (capped at 3 dumps):
            // exposes every register's tag so the stale-tag source is exact.
            static thread_local uint64_t f044_dumps = 0;
            if (f044_dumps < 3 && current_registers_) {
                f044_dumps++;
                std::cerr << "[F044-DIAG] .d register file:";
                for (uint8_t ri = 0; ri < 23; ++ri) {
                    DalvikValue rv = current_registers_->read_v(ri);
                    if (rv.type == DalvikType::REGISTER_UNSET ||
                        rv.type == DalvikType::UNINITIALIZED) continue;
                    std::cerr << " v" << (int)ri << ":t" << static_cast<int>(rv.type)
                              << "(" << rv.int_val << ")";
                }
                std::cerr << std::endl;
            }
        }
        // SnapshotIdSet.contains (LP/j.q) — the record-walk invalidation
        // gate. A TRUE return on an empty set skips every record and makes
        // SnapshotKt.readable (P/l.r) return null inside the dependency
        // version scan while the same readable succeeds from P/l.i.
        if (f044 && current_class_ == "LP/j;" && current_method_ == "q") {
            std::cerr << "[F044-DIAG] LP/j.q(contains) -> "
                      << (val.type == DalvikType::INT32 ? val.int_val : -777)
                      << std::endl;
        }
    }

    halted_ = true;
    halted_on_return_ = true;
    
    log("  RETURN " + val.to_string() + " at " + to_hex(pc));
    
    pc_ = pc + 1;
    return true;
}

bool DalvikExecutionEngine::execute_return_object(uint32_t pc, InstructionTrace& trace) {
    // Format: 11x [op] vAA (1 code unit)
    if (pc >= bytecode_.size()) return false;
    
    uint16_t instr = bytecode_[pc];
    uint8_t ret_reg = (instr >> 8) & 0xFF;
    
    DalvikValue val = get_register(ret_reg);

    // F-075 (S21) — POLYMORPHIC-ZERO-AT-REFERENCE-USE LAW (return side).
    // Dalvik registers are untyped slots (F-028 law); `const/4 vX, #0` loads
    // the polymorphic zero word — INT32(0) in a primitive context, the NULL
    // REFERENCE in a reference context (ART verifier Zero reg-type,
    // convertible to any reference). return-object IS a reference context:
    // Kotlin `return null` compiles to `const/4 v0, 0; return-object v0`.
    // The old code propagated INT32(0) as the method's return — every
    // identity-sensitive consumer (if-ne vs an object, set/map identity
    // checks) then compared 0-vs-0 through the int fallback and answered
    // EQUAL for (object, null). First real-APK hit: dooz LL/b.remove
    // (PersistentOrderedSet) kept the UNREBUILT map after the trie emptied
    // (`if (node !== newNode)` mis-answered equal), the iterator walked the
    // sentinel and threw CME "Hash code of an element has changed", which
    // fatally killed the composition coroutine (S21 0-pixel gate). Same law
    // family as F-030 (zero-is-null at invoke params).
    if (val.type == DalvikType::INT32 && val.int_val == 0) {
        val = DalvikValue::make_null();
    } else if (val.type == DalvikType::VOID_) {
        val = DalvikValue::make_null();
    }

    trace.status = InstructionTrace::Status::HALT_RETURN;
    trace.return_value = val;
    trace.operands.push_back({"v" + std::to_string(ret_reg), val.to_string()});
    
    // EXP-055: Store the return value (same as execute_return).
    last_invoke_return_ = val;

    // F-044 DIAG (env-gated): the derived-state calculation channel —
    // AndroidComposeView$o.c (the calculation lambda) → P/g$a.a →
    // LF/F$b.o → the record.f store. Expose the return VALUE TAG at each
    // hop: a null that arrives as REGISTER_UNSET instead of a proper
    // null OBJECT_REF corrupts the derived record's value field
    // (field-trace showed f stored as <unset>).
    {
        static thread_local const bool f044 = std::getenv("MINIANDROID_F044_DIAG") != nullptr;
        if (f044 && (current_class_ == "LP/g$a;" ||
                     current_class_ == "LF/F$b;" ||
                     current_class_ == "Landroidx/compose/ui/platform/AndroidComposeView$o;" ||
                     current_class_ == "LP/l;" ||
                     current_class_ == "LF/F;")) {
            std::cerr << "[F044-DIAG] " << current_class_ << "." << current_method_
                      << "() return-object type=" << static_cast<int>(val.type)
                      << " obj=" << val.object_id
                      << " int_val=" << val.int_val
                      << std::endl;
        }
    }

    // ────────────────────────────────────────────────────────────────────────
    // CONT-37 (F-NEW-298 evidence, DIAG-ONLY): K0-DRAW-FETCH watch. The
    // Compose LayoutNode.draw dispatch (Lmo0.D0) branches on K0(4): null →
    // Z0 fallback (observed 0 executions in the draw window — impossible for
    // a real tree where most nodes have no draw modifier), non-null → block
    // dispatch (observed only 20 of 82). Watch K0's return value class to
    // answer WHICH node object the fetch answers per call. Env-gated,
    // bounded — zero behavior change.
    // ────────────────────────────────────────────────────────────────────────
    {
        static thread_local const bool k0w_on =
            std::getenv("MINIANDROID_K0_WATCH") != nullptr;
        if (k0w_on && current_class_ == "Lmo0;" && current_method_ == "K0") {
            static thread_local uint64_t k0w_n = 0;
            if (k0w_n++ < 400) {
                const char* k0w_t = "other";
                if (val.type == DalvikType::OBJECT_REF) k0w_t = val.class_desc.c_str();
                else if (val.type == DalvikType::NULL_REF) k0w_t = "NULL";
                else if (val.type == DalvikType::REGISTER_UNSET) k0w_t = "UNSET";
                std::cerr << "[K0-RET] obj=" << val.object_id
                          << " cls=" << k0w_t
                          << " null=" << (val.is_null ? 1 : 0)
                          << std::endl;
            }
        }
    }

    halted_ = true;
    halted_on_return_ = true;
    
    log("  RETURN_OBJECT " + val.to_string() + " at " + to_hex(pc));

    pc_ = pc + 1;
    return true;
}

// EXP-088+ F5: execute_return_wide — return-wide vAA (opcode 0x10, 11x format)
//
// Returns a 64-bit value (long or double) from a method.
//
// Per Dalvik spec: vAA holds the low 32 bits, vAA+1 holds the high 32 bits.
// Our register file already stores wide values as a single INT64 or FLOAT64
// DalvikValue in vAA (set by const-wide, iget-wide, etc.), so we just read
// the single register.
//
// The returned value is stored in last_invoke_return_ so the caller's
// move-result-wide can pick it up.
//
// Previously this opcode was MISSING from the dispatcher — it fell through
// to handle_unimplemented, causing methods that return long/double to:
//   1. Not actually return (execution continued past the return-wide)
//   2. Leave move-result-wide reading stale/zero data
//
// This is a GENERIC VM fix — affects any APK using long/double returns.
bool DalvikExecutionEngine::execute_return_wide(uint32_t pc, InstructionTrace& trace) {
    // Format: 11x [op] vAA (1 code unit)
    if (pc >= bytecode_.size()) return false;

    uint16_t instr = bytecode_[pc];
    uint8_t ret_reg = (instr >> 8) & 0xFF;

    DalvikValue val = get_register(ret_reg);

    // If the register doesn't already hold a wide value (INT64 or FLOAT64),
    // coerce to INT64 with the existing int_val as the low 32 bits.
    // This handles cases where const-wide wasn't used to set the register
    // (e.g., the value came from an arithmetic op that stored INT32).
    if (val.type != DalvikType::INT64 && val.type != DalvikType::FLOAT64) {
        int64_t coerced = static_cast<int64_t>(static_cast<uint32_t>(val.int_val));
        val = DalvikValue::make_long(coerced);
    }

    trace.status = InstructionTrace::Status::HALT_RETURN;
    trace.return_value = val;
    trace.operands.push_back({"v" + std::to_string(ret_reg), val.to_string()});

    // Store so try_recursive_invoke / move-result-wide can propagate.
    last_invoke_return_ = val;

    // EXP-088+ F5 diagnostic: log wide returns for key methods
    if (current_method_ == "getTime" ||
        current_method_ == "currentTimeMillis" ||
        current_method_ == "getDuration" ||
        current_method_ == "getSize" ||
        current_method_ == "getLong" ||
        current_method_ == "nextLong") {
        std::cerr << "[EXP088-F5-RETWIDE] " << current_class_ << "."
                  << current_method_ << " PC=" << pc
                  << " ret_reg=v" << (int)ret_reg
                  << " type=" << static_cast<int>(val.type)
                  << " long_val=0x" << std::hex << val.long_val << std::dec
                  << " (" << val.long_val << ")"
                  << std::endl;
    }

    halted_ = true;
    halted_on_return_ = true;

    log("  RETURN_WIDE " + val.to_string() + " at " + to_hex(pc));

    pc_ = pc + 1;
    return true;
}

// ============================================================================
// OPCODE IMPLEMENTATIONS — Control Flow
// ============================================================================

bool DalvikExecutionEngine::execute_goto(uint32_t pc, InstructionTrace& trace) {
    // EXP-039 (BLOCKER-036 FIX): Handle all goto variants correctly.
    // goto (0x28) = format 10t: AA|op (1 code unit, offset in high byte)
    // goto/16 (0x29) = format 20t: op|AAAA (2 code units, offset in next word)
    // goto/32 (0x2a) = format 30t: op|AAAAAAAA (3 code units, offset in next 2 words)
    if (pc >= bytecode_.size()) return false;

    uint16_t opcode = bytecode_[pc] & 0xFF;

    int32_t offset;
    uint32_t pc_advance;

    if (opcode == Opcode::GOTO) {
        // Format 10t: offset is in high byte (signed 8-bit)
        offset = static_cast<int8_t>((bytecode_[pc] >> 8) & 0xFF);
        pc_advance = 1;
        // EXP-071: D8/R8 hybrid goto encoding.
        // D8 uses op=0x28 (goto) for BOTH 10t and 20t formats:
        // 1. High byte != 0: Standard 10t format (1 code unit, offset in high byte).
        // 2. High byte == 0: Extended 20t format (2 code units, offset in next word).
        //    This is safe because D8 doesn't generate goto +0 (NOP).
        //    We check that the next word is a reasonable offset (< 10000).
        if (offset == 0 && pc + 1 < bytecode_.size()) {
            int16_t next_offset = static_cast<int16_t>(bytecode_[pc + 1]);
            if (next_offset != 0 && std::abs(next_offset) < 10000) {
                offset = next_offset;
                pc_advance = 2;
            }
        }
    } else if (opcode == Opcode::GOTO_16) {
        // EXP-044 Phase 1: D8/R8 hybrid goto/16 encoding.
        //
        // D8 uses op=0x28 (goto/16) in TWO modes:
        // 1. High byte != 0: The high byte IS the 8-bit signed offset.
        //    Total instruction size: 1 code unit (like 10t format).
        //    The "next word" is the START of the next instruction, NOT an offset.
        //    Example: AndroidUtilities.bold PC=24 → high=0x09=+9 → target=PC=33
        // 2. High byte == 0: Standard 20t format, 16-bit signed offset in next word.
        //    Total instruction size: 2 code units.
        //    Example: (rare, 578 out of 27381 in classes.dex)
        //
        // Evidence: 26803 goto/16 instructions have non-zero high byte,
        // 578 have high byte=0 (standard 20t). The high byte values are
        // always small (±12 range typical), matching short branch offsets.
        //
        // This was the root cause of 20 HALT-GOTO events in Telegram execution.
        uint8_t high_byte = (bytecode_[pc] >> 8) & 0xFF;
        if (high_byte != 0) {
            // D8 hybrid mode: 1-code-unit goto with 8-bit offset in high byte
            offset = static_cast<int8_t>(high_byte);
            pc_advance = 1;
        } else {
            // Standard 20t format: 2 code units, 16-bit offset in next word
            if (pc + 1 >= bytecode_.size()) return false;
            offset = static_cast<int16_t>(bytecode_[pc + 1]);
            pc_advance = 2;
        }
    } else if (opcode == Opcode::GOTO_32) {
        // EXP-044 Phase 1: D8/R8 hybrid goto/32 encoding (same as goto/16).
        //
        // D8 uses op=0x29 (goto/32) in TWO modes:
        // 1. High byte != 0 (10959 occurrences): 8-bit signed offset in high byte.
        //    Total instruction size: 1 code unit.
        // 2. High byte == 0 (24727 occurrences): 16-bit signed offset in next word.
        //    Total instruction size: 2 code units (NOT 3 as per AOSP 30t spec).
        //    The word at PC+2 is the start of the NEXT instruction, not the high
        //    16 bits of a 32-bit offset.
        //
        // Evidence: ApplicationLoader.postInitApplication PC=8:
        //   high=0x00, next=0x0101=257 → target=PC=265 (return-void). Correct!
        //   Standard 30t with 32-bit offset would give 0x10120101 → invalid.
        uint8_t high_byte = (bytecode_[pc] >> 8) & 0xFF;
        if (high_byte != 0) {
            // D8 hybrid mode: 1-code-unit goto with 8-bit offset in high byte
            offset = static_cast<int8_t>(high_byte);
            pc_advance = 1;
        } else {
            // D8 2-code-unit format: 16-bit offset in next word
            if (pc + 1 >= bytecode_.size()) return false;
            offset = static_cast<int16_t>(bytecode_[pc + 1]);
            pc_advance = 2;
        }
    } else {
        // Unknown goto variant — treat as 10t
        offset = static_cast<int8_t>((bytecode_[pc] >> 8) & 0xFF);
        pc_advance = 1;
    }

    uint32_t target = pc + offset;

    // EXP-051: D8 "unreachable" marker — `goto +0` (self-loop).
    //
    // D8/R8 replace `throw vAA` instructions with `goto +0` (a self-loop
    // at the throw site) when the throw is unreachable from the entry
    // point OR when D8 strips the throw as part of dead-code elimination.
    // This pattern shows up in LifecycleRegistry.enforceMainThreadIfNeeded
    // at PC=46 — the bytecode constructs an IllegalStateException but
    // then has `goto +0` instead of `throw v0`.
    //
    // Without special handling, the engine loops forever at this PC
    // (HALT-LOOP). We treat `goto +0` as a "halt method" — equivalent
    // to return-void — so execution continues with the caller.
    //
    // Evidence: bytecode at PC=46 of LifecycleRegistry.enforceMainThreadIfNeeded
    //   (classes.dex, code_off=0x250668) is 0x0027 (goto +0). The throw
    //   that should follow the IllegalStateException.<init> at PC=43 is
    //   missing — D8 replaced it with this self-loop.
    if (offset == 0) {
        trace.status = InstructionTrace::Status::HALT_RETURN;
        trace.operands.push_back({"offset", "0 (D8 unreachable marker)"});
        trace.operands.push_back({"target", "exit_method"});
        halted_ = true;
        halted_on_return_ = true;
        pc_ = pc + pc_advance;
        return true;
    }

    // EXP-044 Phase 1: When goto target == bytecode_.size(), it means "exit
    // the method" (branch past the end = return). This is valid Dalvik behavior
    // for methods that end with a goto that jumps past the last instruction.
    // Example: Intrinsics.throwParameterIsNullNPE PC=15: goto +1 → PC=16
    // where bytecode_size=16. This is equivalent to return-void.
    //
    // EXP-051: Also handle target > bytecode_.size() — D8/R8 sometimes emit
    // `goto +N` where N points past the end as an "unreachable" marker.
    // Example: SpringForce.setDampingRatio PC=19: goto +3 → PC=22,
    // but bytecode_size=20. Without this fix, the engine HALTs with
    // HALT-GOTO. With this fix, we treat it as "exit method" (= return).
    if (target >= bytecode_.size()) {
        trace.status = InstructionTrace::Status::HALT_RETURN;
        trace.operands.push_back({"offset", std::to_string(offset)});
        trace.operands.push_back({"target", "exit_method (past end)"});
        halted_ = true;
        halted_on_return_ = true;
        pc_ = pc + pc_advance;
        return true;
    }

    // Validate target
    if (target < bytecode_.size()) {
        trace.status = InstructionTrace::Status::BRANCH_TAKEN;
        pc_ = target;

        trace.operands.push_back({"offset", std::to_string(offset)});
        trace.operands.push_back({"target", to_hex(target)});
    } else {
        trace.status = InstructionTrace::Status::CRASH_ERROR;
        trace.error_message = "Invalid goto target: " + to_hex(target) +
                              " (offset=" + std::to_string(offset) +
                              ", bytecode_size=" + std::to_string(bytecode_.size()) + ")";
        halted_ = true;
        halt_reason_ = "Invalid goto target";
        pc_ = pc + pc_advance;
        // EXP-043 Phase 1: log invalid goto targets for debugging (first 20 only
        // to avoid log spam). These indicate either real bytecode verification
        // issues or goto/32 misinterpretation.
        static thread_local uint64_t halt_goto_count = 0;
        if (halt_goto_count < 20) {
            std::cerr << "[HALT-GOTO] Invalid goto target PC=" << to_hex(pc)
                      << " in " << current_class_ << "." << current_method_
                      << " target=" << to_hex(target)
                      << " bytecode_size=" << bytecode_.size() << std::endl;
            halt_goto_count++;
        }
    }

    return true;
}

bool DalvikExecutionEngine::execute_if_eqz(uint32_t pc, InstructionTrace& trace) {
    // Format: 21t [op] vAA, +BBBB
    if (pc + 1 >= bytecode_.size()) return false;

    uint16_t instr = bytecode_[pc];
    uint8_t test_reg = (instr >> 8) & 0xFF;
    int16_t offset = static_cast<int16_t>(bytecode_[pc + 1]);

    DalvikValue val = get_register(test_reg);
    // EXP-055: Treat OBJECT_REF with object_id=0 as null (same as NULL_REF).
    // EXP-058: Also treat VOID_ as zero (same rationale as if-nez).
    // EXP-092+ CRITICAL FIX: Also treat BOOLEAN with int_val==0 as zero.
    //   instance-of returns make_bool(false) which sets type=BOOLEAN, int_val=0.
    //   Without this check, if-eqz on a false BOOLEAN result returns is_zero=false,
    //   causing the branch to NOT be taken — which is the OPPOSITE of correct
    //   behavior. This affects ALL instance-of results in conditional branches.
    //   Same for BYTE, SHORT, CHAR — all integer-like types with int_val.
    // EXP-093/F014: Added INT64, FLOAT32, FLOAT64 to zero-ness check.
    // Per AOSP: if-eqz/if-nez treat ALL primitive types' zero as false.
    // Previously INT64 (long 0L), FLOAT32 (0.0f), FLOAT64 (0.0d) were
    // NOT treated as zero, causing if-eqz to return is_zero=FALSE for
    // a zero long/double/float — the OPPOSITE of correct behavior.
    bool is_zero = (val.type == DalvikType::NULL_REF) ||
                   (val.type == DalvikType::INT32 && val.int_val == 0) ||
                   (val.type == DalvikType::BOOLEAN && val.int_val == 0) ||
                   (val.type == DalvikType::BYTE && val.int_val == 0) ||
                   (val.type == DalvikType::SHORT && val.int_val == 0) ||
                   (val.type == DalvikType::CHAR && val.int_val == 0) ||
                   (val.type == DalvikType::INT64 && val.long_val == 0) ||
                   (val.type == DalvikType::FLOAT32 && val.float_val == 0.0f) ||
                   (val.type == DalvikType::FLOAT64 && val.double_val == 0.0) ||
                   (val.type == DalvikType::OBJECT_REF && val.object_id == 0) ||
                   (val.type == DalvikType::UNINITIALIZED || val.type == DalvikType::REGISTER_UNSET) ||
                   (val.type == DalvikType::VOID_);

    // EXP-059: Debug — log if-eqz in addFragmentToStack
    if (current_method_ == "addFragmentToStack" &&
        current_class_.find("ActionBarLayout") != std::string::npos) {
        std::cerr << "[EXP059-IF-EQZ] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " test_reg=v" << (int)test_reg
                  << " type=" << static_cast<int>(val.type)
                  << " int_val=" << val.int_val
                  << " obj=" << val.object_id
                  << " is_zero=" << is_zero
                  << " target=" << (pc + offset)
                  << std::endl;
    }

    // EXP-092+ PHASE 1: Log if-eqz in LoginActivity.setPage.
    if (current_class_.find("LoginActivity;") != std::string::npos &&
        current_class_.find("PhoneView") == std::string::npos &&
        current_method_ == "setPage") {
        std::cerr << "[EXP092-SETPAGE-IFZ] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " op=if-eqz"
                  << " v" << (int)test_reg
                  << " type=" << static_cast<int>(val.type)
                  << " int_val=" << val.int_val
                  << " obj=" << val.object_id
                  << " is_zero=" << is_zero
                  << " → target_pc=" << (pc + offset)
                  << " next_pc=" << (is_zero ? (pc + offset) : (pc + 2))
                  << std::endl;
    }

    // EXP-092+ PHASE D: Log if-eqz in lambda$onNextPressed$22 to trace the
    // critical branch at PC=8: if-eqz v4(instance-of result) → PC=46
    if (current_class_.find("LoginActivity$PhoneView") != std::string::npos &&
        current_method_ == "lambda$onNextPressed$22") {
        std::cerr << "[EXP092-IF-EQZ-22] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " op=if-eqz"
                  << " v" << (int)test_reg
                  << " type=" << static_cast<int>(val.type)
                  << " int_val=" << val.int_val
                  << " obj=" << val.object_id
                  << " is_zero=" << is_zero
                  << " → target_pc=" << (pc + offset)
                  << " next_pc=" << (is_zero ? (pc + offset) : (pc + 2))
                  << std::endl;
    }

    if (is_zero) {
        uint32_t target = pc + offset;
        // EXP-051: target >= bytecode_.size() = D8 unreachable marker (exit method).
        if (target >= bytecode_.size()) {
            halted_ = true; halted_on_return_ = true;
            trace.status = InstructionTrace::Status::HALT_RETURN;
            trace.operands.push_back({"target", "exit_method (past end)"});
            pc_ = pc + 2;
        } else {
            trace.status = InstructionTrace::Status::BRANCH_TAKEN;
            pc_ = target;
        }
    } else {
        trace.status = InstructionTrace::Status::BRANCH_NOT_TAKEN;
        pc_ = pc + 2;
    }

    trace.operands.push_back({"v" + std::to_string(test_reg), val.to_string()});
    trace.operands.push_back({"taken", is_zero ? "yes" : "no"});

    return true;
}

bool DalvikExecutionEngine::execute_if_nez(uint32_t pc, InstructionTrace& trace) {
    // Format: 21t [op] vAA, +BBBB
    if (pc + 1 >= bytecode_.size()) return false;
    
    uint16_t instr = bytecode_[pc];
    uint8_t test_reg = (instr >> 8) & 0xFF;
    int16_t offset = static_cast<int16_t>(bytecode_[pc + 1]);
    
    DalvikValue val = get_register(test_reg);
    // EXP-055: Treat OBJECT_REF with object_id=0 as null (same as NULL_REF).
    // EXP-058: Also treat VOID_ as zero — when bridge_to_api returns void
    // for unhandled methods, if-nez must NOT branch. Previously VOID_
    // was treated as non-zero, causing branches that skipped important
    // method calls (e.g., onFragmentCreate was never called because
    // needAddFragmentToStack returned VOID_ on a null delegate).
    // EXP-093/F014: Added INT64, FLOAT32, FLOAT64 to zero-ness check
    // (same as if-eqz handler above).
    bool is_nonzero = !(val.type == DalvikType::NULL_REF ||
                       (val.type == DalvikType::INT32 && val.int_val == 0) ||
                       (val.type == DalvikType::BOOLEAN && val.int_val == 0) ||
                       (val.type == DalvikType::BYTE && val.int_val == 0) ||
                       (val.type == DalvikType::SHORT && val.int_val == 0) ||
                       (val.type == DalvikType::CHAR && val.int_val == 0) ||
                       (val.type == DalvikType::INT64 && val.long_val == 0) ||
                       (val.type == DalvikType::FLOAT32 && val.float_val == 0.0f) ||
                       (val.type == DalvikType::FLOAT64 && val.double_val == 0.0) ||
                       (val.type == DalvikType::OBJECT_REF && val.object_id == 0) ||
                       (val.type == DalvikType::UNINITIALIZED || val.type == DalvikType::REGISTER_UNSET) ||
                       (val.type == DalvikType::VOID_));
    
    // EXP-059: Debug — log if-nez in addFragmentToStack
    if (current_method_ == "addFragmentToStack" &&
        current_class_.find("ActionBarLayout") != std::string::npos) {
        std::cerr << "[EXP059-IF-NEZ] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " test_reg=v" << (int)test_reg
                  << " type=" << static_cast<int>(val.type)
                  << " int_val=" << val.int_val
                  << " obj=" << val.object_id
                  << " is_nonzero=" << is_nonzero
                  << " target=" << (pc + offset)
                  << std::endl;
    }
    
    // EXP-046: Log if-nez in NativeLoader.initNativeLibs
    if (current_class_.find("NativeLoader") != std::string::npos) {
        std::cerr << "[IF-NEZ-DBG] " << current_class_ << "." << current_method_
                  << " PC=" << pc << " v" << (int)test_reg
                  << " type=" << static_cast<int>(val.type)
                  << " val=" << val.int_val
                  << " nonzero=" << is_nonzero
                  << " target=" << (pc + offset) << std::endl;
    }

    // ── TRAIN-64 (T64, DIAG-ONLY): the branch decision inside the R8-
    // inlined changedToUp helper (Lbo;.h: return h && !d). The UP change's
    // h read answered 1 yet the d read never ran — this logs the exact
    // register/type/value if-nez saw, pinning the drop point.
    if (touch_dispatch_active_ && current_class_ == "Lbo;" &&
        current_method_ == "h") {
        static thread_local uint64_t t64z_n = 0;
        if (t64z_n++ < 64) {
            std::cerr << "[T64-NEZ] Lbo;.h pc=" << pc
                      << " reg=v" << static_cast<int>(test_reg)
                      << " type=" << static_cast<int>(val.type)
                      << " int_val=" << val.int_val
                      << " bool_val="
                      << (val.type == DalvikType::BOOLEAN
                              ? static_cast<int>(val.bool_val) : -1)
                      << " nonzero=" << (is_nonzero ? 1 : 0)
                      << std::endl;
        }
    }

    // EXP-092+ DIRECT TRACE: Log if-nez in onNextPressed and lambda$new$12
    // to prove the exact condition that determines the needShowAlert side path.
    // Critical branches:
    //   lambda$new$12 PC=0:  if-nez v2(response), +3 → PC=3  (null check on response)
    //   lambda$new$12 PC=11: if-nez v0(codeField.length()), +11 → PC=22 (skip setCountry if codeField non-empty)
    if ((current_class_.find("LoginActivity$PhoneView") != std::string::npos &&
         (current_method_ == "onNextPressed" || current_method_ == "lambda$new$12" ||
          current_method_ == "setCountry" || current_method_ == "afterTextChanged" ||
          current_method_.find("lambda$") == 0)) ||
        current_class_.find("PhoneView$2") != std::string::npos) {
        std::cerr << "[EXP092-IF-NEZ] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " v" << (int)test_reg
                  << " type=" << static_cast<int>(val.type)
                  << " int_val=" << val.int_val
                  << " obj=" << val.object_id
                  << " string=\"" << val.string_val << "\""
                  << " is_nonzero=" << is_nonzero
                  << " → target_pc=" << (pc + offset)
                  << " next_pc=" << (is_nonzero ? (pc + offset) : (pc + 2))
                  << std::endl;
    }

    // EXP-092+ PHASE 1: Log if-nez/if-eqz in LoginActivity.setPage.
    // The setPage method has 309 instructions and many branches. We need
    // to trace ALL of them to understand what page_value=13 does.
    if (current_class_.find("LoginActivity;") != std::string::npos &&
        current_class_.find("PhoneView") == std::string::npos &&
        current_method_ == "setPage") {
        std::cerr << "[EXP092-SETPAGE-IFZ] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " op=if-nez"
                  << " v" << (int)test_reg
                  << " type=" << static_cast<int>(val.type)
                  << " int_val=" << val.int_val
                  << " obj=" << val.object_id
                  << " is_nonzero=" << is_nonzero
                  << " → target_pc=" << (pc + offset)
                  << " next_pc=" << (is_nonzero ? (pc + offset) : (pc + 2))
                  << std::endl;
    }

    // EXP-092+ PHASE 1: Log if-nez in fillNextCodeParams to trace why
    // page_value=13 is chosen even with type=TL_auth_sentCodeTypeSms.
    if (current_class_.find("LoginActivity;") != std::string::npos &&
        current_class_.find("PhoneView") == std::string::npos &&
        current_method_ == "fillNextCodeParams") {
        std::cerr << "[EXP092-FILLNEXT-IFZ] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " op=if-nez"
                  << " v" << (int)test_reg
                  << " type=" << static_cast<int>(val.type)
                  << " int_val=" << val.int_val
                  << " obj=" << val.object_id
                  << " is_nonzero=" << is_nonzero
                  << " → target_pc=" << (pc + offset)
                  << " next_pc=" << (is_nonzero ? (pc + offset) : (pc + 2))
                  << std::endl;
    }

    if (is_nonzero) {
        uint32_t target = pc + offset;
        // EXP-051: target >= bytecode_.size() = D8 unreachable marker (exit method).
        if (target >= bytecode_.size()) {
            halted_ = true; halted_on_return_ = true;
            trace.status = InstructionTrace::Status::HALT_RETURN;
            trace.operands.push_back({"target", "exit_method (past end)"});
            pc_ = pc + 2;
        } else {
            trace.status = InstructionTrace::Status::BRANCH_TAKEN;
            pc_ = target;
        }
    } else {
        trace.status = InstructionTrace::Status::BRANCH_NOT_TAKEN;
        pc_ = pc + 2;
    }
    
    trace.operands.push_back({"v" + std::to_string(test_reg), val.to_string()});
    trace.operands.push_back({"taken", is_nonzero ? "yes" : "no"});
    
    return true;
}

// ============================================================================
// EXP-043 Phase 1: Proper 21t format if-*z handlers
// Per AOSP:
//   if-ltz vAA, +BBBB : branch if (int) vAA < 0
//   if-gez vAA, +BBBB : branch if (int) vAA >= 0
//   if-gtz vAA, +BBBB : branch if (int) vAA > 0
//   if-lez vAA, +BBBB : branch if (int) vAA <= 0
//
// For OBJECT_REF, NULL_REF, UNINITIALIZED: the value is treated as 0 (which
// means if-ltz=fallthrough, if-gez=branch, if-gtz=fallthrough, if-lez=branch).
// This matches Dalvik's behavior of converting null to 0 for int comparisons.
// ============================================================================

bool DalvikExecutionEngine::execute_if_ltz(uint32_t pc, InstructionTrace& trace) {
    // Format: 21t [op] vAA, +BBBB  — branch if (int) vAA < 0
    // EXP-059: Now correctly dispatched for opcode 0x3A (per AOSP).
    //   Per AOSP: 0x3A = if-ltz ("branch if v < 0").
    // Previously the runtime had if-ltz at 0x39 (off-by-one), which collided
    // with the actual if-nez. The EXP-058 hack treated INT32 if-ltz as if-nez
    // to work around that collision. With the opcode table fixed, if-ltz now
    // correctly means "branch if < 0" for INT32, matching AOSP semantics.
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }
    uint16_t instr = bytecode_[pc];
    uint8_t test_reg = (instr >> 8) & 0xFF;
    int16_t offset = static_cast<int16_t>(bytecode_[pc + 1]);
    DalvikValue val = get_register(test_reg);

    bool taken = false;
    if (val.type == DalvikType::OBJECT_REF) {
        // OBJECT_REF can't be < 0; never branch.
        taken = false;
    } else if (val.type == DalvikType::NULL_REF) {
        // null == 0 → 0 < 0 is false; never branch.
        taken = false;
    } else if (val.type == DalvikType::INT32 || val.type == DalvikType::BOOLEAN ||
               val.type == DalvikType::BYTE || val.type == DalvikType::SHORT ||
               val.type == DalvikType::CHAR) {
        // Standard AOSP if-ltz: branch if val < 0.
        taken = (val.int_val < 0);
    } else if (val.type == DalvikType::INT64) {
        taken = (static_cast<int64_t>(val.long_val) < 0);
    } else {
        // UNINITIALIZED, REGISTER_UNSET, VOID_ → don't branch.
        taken = false;
    }

    if (taken) {
        uint32_t target = pc + offset;
        if (target < bytecode_.size()) {
            trace.status = InstructionTrace::Status::BRANCH_TAKEN;
            pc_ = target;
        } else if (target == bytecode_.size()) {
            // goto past end = exit method
            halted_ = true;
            halted_on_return_ = true;
            pc_ = pc + 2;
            return true;
        } else {
            pc_ = pc + 2;
        }
    } else {
        trace.status = InstructionTrace::Status::BRANCH_NOT_TAKEN;
        pc_ = pc + 2;
    }
    trace.operands.push_back({"v" + std::to_string(test_reg), val.to_string()});
    trace.operands.push_back({"taken", taken ? "yes" : "no"});
    return true;
}

bool DalvikExecutionEngine::execute_if_gez(uint32_t pc, InstructionTrace& trace) {
    // Format: 21t [op] vAA, +BBBB  — branch if (int) vAA >= 0
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }
    uint16_t instr = bytecode_[pc];
    uint8_t test_reg = (instr >> 8) & 0xFF;
    int16_t offset = static_cast<int16_t>(bytecode_[pc + 1]);
    DalvikValue val = get_register(test_reg);
    int32_t ival = 0;
    if (val.type == DalvikType::INT32 || val.type == DalvikType::BOOLEAN ||
        val.type == DalvikType::BYTE || val.type == DalvikType::SHORT ||
        val.type == DalvikType::CHAR) {
        ival = val.int_val;
    } else if (val.type == DalvikType::INT64) {
        ival = static_cast<int32_t>(val.long_val);
    }
    bool taken = (ival >= 0);
    if (taken) {
        uint32_t target = pc + offset;
        // EXP-051: target >= bytecode_.size() = D8 unreachable marker (exit method).
        if (target >= bytecode_.size()) {
            halted_ = true; halted_on_return_ = true;
            trace.status = InstructionTrace::Status::HALT_RETURN;
            pc_ = pc + 2;
            return true;
        }
        trace.status = InstructionTrace::Status::BRANCH_TAKEN;
        pc_ = target;
    } else {
        trace.status = InstructionTrace::Status::BRANCH_NOT_TAKEN;
        pc_ = pc + 2;
    }
    trace.operands.push_back({"v" + std::to_string(test_reg), std::to_string(ival)});
    trace.operands.push_back({"taken", taken ? "yes" : "no"});
    return true;
}

bool DalvikExecutionEngine::execute_if_gtz(uint32_t pc, InstructionTrace& trace) {
    // Format: 21t [op] vAA, +BBBB  — branch if (int) vAA > 0
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }
    uint16_t instr = bytecode_[pc];
    uint8_t test_reg = (instr >> 8) & 0xFF;
    int16_t offset = static_cast<int16_t>(bytecode_[pc + 1]);
    DalvikValue val = get_register(test_reg);
    int32_t ival = 0;
    if (val.type == DalvikType::INT32 || val.type == DalvikType::BOOLEAN ||
        val.type == DalvikType::BYTE || val.type == DalvikType::SHORT ||
        val.type == DalvikType::CHAR) {
        ival = val.int_val;
    } else if (val.type == DalvikType::INT64) {
        ival = static_cast<int32_t>(val.long_val);
    }
    bool taken = (ival > 0);
    if (taken) {
        uint32_t target = pc + offset;
        // EXP-051: target >= bytecode_.size() = D8 unreachable marker (exit method).
        if (target >= bytecode_.size()) {
            halted_ = true; halted_on_return_ = true;
            trace.status = InstructionTrace::Status::HALT_RETURN;
            pc_ = pc + 2;
            return true;
        }
        trace.status = InstructionTrace::Status::BRANCH_TAKEN;
        pc_ = target;
    } else {
        trace.status = InstructionTrace::Status::BRANCH_NOT_TAKEN;
        pc_ = pc + 2;
    }
    trace.operands.push_back({"v" + std::to_string(test_reg), std::to_string(ival)});
    trace.operands.push_back({"taken", taken ? "yes" : "no"});
    return true;
}

bool DalvikExecutionEngine::execute_if_lez(uint32_t pc, InstructionTrace& trace) {
    // Format: 21t [op] vAA, +BBBB  — branch if (int) vAA <= 0
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }
    uint16_t instr = bytecode_[pc];
    uint8_t test_reg = (instr >> 8) & 0xFF;
    int16_t offset = static_cast<int16_t>(bytecode_[pc + 1]);
    DalvikValue val = get_register(test_reg);
    int32_t ival = 0;
    if (val.type == DalvikType::INT32 || val.type == DalvikType::BOOLEAN ||
        val.type == DalvikType::BYTE || val.type == DalvikType::SHORT ||
        val.type == DalvikType::CHAR) {
        ival = val.int_val;
    } else if (val.type == DalvikType::INT64) {
        ival = static_cast<int32_t>(val.long_val);
    }
    bool taken = (ival <= 0);
    if (taken) {
        uint32_t target = pc + offset;
        // EXP-051: target >= bytecode_.size() = D8 unreachable marker (exit method).
        if (target >= bytecode_.size()) {
            halted_ = true; halted_on_return_ = true;
            trace.status = InstructionTrace::Status::HALT_RETURN;
            pc_ = pc + 2;
            return true;
        }
        trace.status = InstructionTrace::Status::BRANCH_TAKEN;
        pc_ = target;
    } else {
        trace.status = InstructionTrace::Status::BRANCH_NOT_TAKEN;
        pc_ = pc + 2;
    }
    trace.operands.push_back({"v" + std::to_string(test_reg), std::to_string(ival)});
    trace.operands.push_back({"taken", taken ? "yes" : "no"});
    return true;
}

// ============================================================================
// EXP-037 Phase B (BLOCKER-018): 22t format if-* opcodes
// Format 22t: B1|A|op CCCC  → 2 code units
//   code[0]: bits 0-7 = opcode, bits 8-11 = vA (4 bits), bits 12-15 = vB (4 bits)
//   code[1]: 16-bit signed branch offset (CCCC)
// Branch target = pc + offset (signed)
// ============================================================================

namespace {

// Helper: extract two 4-bit registers from a 22t opcode word.
// vA = high nibble of low byte  = (instr >> 8) & 0xF
// vB = high nibble of high byte = (instr >> 12) & 0xF
struct If22tRegs {
    uint8_t vA;
    uint8_t vB;
    int16_t offset;
};

If22tRegs decode_22t(uint16_t instr, uint16_t next_word) {
    If22tRegs r;
    r.vA = static_cast<uint8_t>((instr >> 8) & 0xF);
    r.vB = static_cast<uint8_t>((instr >> 12) & 0xF);
    r.offset = static_cast<int16_t>(next_word);
    return r;
}

// Helper: common branch logic for 22t if-* opcodes.
// `taken` is whether the comparison evaluated true.
// On take: pc = pc + offset; On fall-through: pc = pc + 2.
bool do_22t_branch(uint32_t pc, int16_t offset, bool taken,
                   const std::string& opcode_name,
                   uint8_t vA, uint8_t vB,
                   const DalvikValue& a, const DalvikValue& b,
                   InstructionTrace& trace, DalvikExecutionEngine* engine_unused = nullptr) {
    (void)engine_unused;  // signature placeholder
    if (taken) {
        uint32_t target = pc + offset;
        // Note: target may legitimately equal pc + 2 (fall-through) when offset=2,
        // or be backward when offset is negative.
        trace.status = InstructionTrace::Status::BRANCH_TAKEN;
        trace.pc_after = target;
        // We can't directly set pc_ here since it's a member; the caller does that.
    } else {
        trace.status = InstructionTrace::Status::BRANCH_NOT_TAKEN;
    }
    trace.operands.push_back({"vA", "v" + std::to_string(vA) + "=" + a.to_string()});
    trace.operands.push_back({"vB", "v" + std::to_string(vB) + "=" + b.to_string()});
    trace.operands.push_back({"taken", taken ? "yes" : "no"});
    trace.operands.push_back({"offset", std::to_string(offset)});
    (void)opcode_name;
    return true;
}

} // anonymous namespace

#define IMPLEMENT_IF_22T(name, op, op_name) \
bool DalvikExecutionEngine::execute_##name(uint32_t pc, InstructionTrace& trace) { \
    /* CONT-7 §12 branch-decision diagnostics (shared across all six 22t) */ \
    static thread_local const bool r337_c7_trace = \
        std::getenv("MINIANDROID_C7_IF_TRACE") != nullptr; \
    static thread_local uint64_t r337_c7_if_n = 0; \
    if (pc + 1 >= bytecode_.size()) return false; \
    uint16_t instr = bytecode_[pc]; \
    If22tRegs r = decode_22t(instr, bytecode_[pc + 1]); \
    DalvikValue a = get_register(r.vA); \
    DalvikValue b = get_register(r.vB); \
    /* CHAR-PROBE campaign: extract the numeric value from EVERY integer-like \
       primitive type, not just INT32. Per the Dalvik spec if-eq/if-ne/... \
       22t only ever compare same-width ints, but the interpreter's typed \
       registers (CHAR/BOOLEAN/BYTE/SHORT from signature-aware invoke and \
       field/array loads) all carry their value in int_val. The previous \
       "(type==INT32) ? int_val : 0" collapsed every other primitive to 0 — \
       a char param compared as 0 and EMPTY BOARD CELLS matched it. Same \
       zero-tolerance law as the EXP-093 if-eqz fix. */ \
    auto if22t_int = [](const DalvikValue& v) -> int32_t { return dalvik_int_value(v); }; \
    int32_t a_val = if22t_int(a); \
    int32_t b_val = if22t_int(b); \
    bool taken = false; \
    /* F-069: CLASS_REF participates in reference comparison like
       OBJECT_REF/NULL_REF — its identity token (stable per descriptor,
       see execute_const_class) is the compared word. Kotlin/Java compare
       Class objects with == (Intrinsics.areEqual fast path, map keys,
       KClass lookups); the old code fell to the int_val path where every
       CLASS_REF carried int_val=0, so if-eq on two DIFFERENT Class
       values was TAKEN and if-eq on two SAME-Class values was
       indistinguishable from any other zero. */ \
    /* CODER7 WAVE-11 (P-58): STRING_REF participates in reference \
       comparison — the engine's STRING_REF is a VALUE (no identity; equal \
       contents collapse to one value), so two string registers compare BY \
       CONTENT, and a string-vs-null pair answers never-equal (a string \
       value is never the null reference). The old set excluded STRING_REF: \
       every pair fell to the int tail where dalvik_int_value collapses \
       both to 0 — if-eq TAKEN and if-ne NOT taken for ANY two strings \
       (`str != "lit"` never branched, `str == null` always true). The \
       N10 evidence: `lastSelArg0 != "unset"` answered false for content \
       "2" — the delete loop never ran. */ \
    bool a_is_ref = (a.type == DalvikType::OBJECT_REF || a.type == DalvikType::NULL_REF || a.type == DalvikType::CLASS_REF || a.type == DalvikType::STRING_REF); \
    bool b_is_ref = (b.type == DalvikType::OBJECT_REF || b.type == DalvikType::NULL_REF || b.type == DalvikType::CLASS_REF || b.type == DalvikType::STRING_REF); \
    if (a_is_ref && b_is_ref && a.type == DalvikType::CLASS_REF && b.type == DalvikType::CLASS_REF) { \
        /* F-NEW-225d (completes F-NEW-218/F-069) — CLASS TOKEN DESCRIPTOR \
           IDENTITY LAW. ART: a class has exactly ONE Class object, so \
           `clsA == clsB` holds IFF they name the same class. Engine \
           minted tokens carry ref_id = instruction_sequence_ (F-NEW-218 \
           getClass law) — EVERY token mints a fresh id, so ref_id \
           comparison answers never-equal for two tokens of the SAME \
           class. Observable face (opencalc vc53): Gson's \
           ReflectiveTypeAdapterFactory.getBoundFields loop guard \
           `while (raw != Object.class)` never terminated — the Object \
           token comparison missed, the loop climbed one level further, \
           fed getGenericSuperclass(Object)==null into \
           TypeToken.get(null) → $Gson$Types.getRawType IAE → \
           MainActivity.onCreate APP-BOUNDARY death. LAW: CLASS_REF vs \
           CLASS_REF compares the CANONICAL descriptor (F-NEW-224 form), \
           not the mint id. */ \
        taken = (framework::normalize_class_desc(a.class_desc) op \
                 framework::normalize_class_desc(b.class_desc)); \
        { \
            static thread_local uint64_t f225d_n = 0; \
            if (f225d_n < 24) { \
                ++f225d_n; \
                std::cerr << "[F-NEW-225d] " << op_name << " a=" << a.class_desc \
                          << " b=" << b.class_desc << " taken=" << (taken ? "YES" : "NO") \
                          << " caller=" << current_class_ << "." << current_method_ \
                          << std::endl; \
            } \
        } \
    } else if (a_is_ref && b_is_ref) { \
        /* ── F-C4-569 (W6, 4APP4): CLASS-TOKEN REFERENCE-IDENTITY LAW ── \
           ART (art::mirror::Class, one Class object per classloader+name): \
           `tokenA == tokenB` on Class references is TRUE iff the two \
           tokens name the SAME class. The engine mints heap Class tokens \
           at multiple sites (const-class cache, F-NEW-282 iput \
           materialization, Class.forName bridges, getClass law) — two \
           DISTINCT oids for one referent made every if-eq/if-ne on a \
           Class-token pair answer never-equal. Kotlin compiles `==` on \
           statically NON-NULL Class references (e.g. ClassReference.\
           equals' `jClass == other.jClass`) to a PLAIN if-ne — NOT to \
           Intrinsics.areEqual / Object.equals — so the W5 laws \
           F-C4-567/F-C4-568 (equals bridge + hashCode) never saw this \
           compare at all. Live root (Thunderbird v24, Koin): every \
           ConcurrentHashMap.get(Node) chain-walk compare died at the \
           Kotlin ClassReference.equals if-ne on two heap tokens for the \
           same referent → NoDefinitionFoundException ×32 (the 510 CHM \
           puts + 596 nodes all stored fine — laws 566/568 — the GET \
           simply never matched). Same opcode also answers the CHM \
           getNode `(ek = e.key) == key` fast path. LAW: a Class-token \
           pair in if-eq/if-ne compares REFERENT IDENTITY — the register \
           form's canonical class_desc, the heap form's __referent_desc \
           (F-069/F-103 convention; the W4 567 companion for the opcode \
           path). Non-quantified pairs keep the oid law (OpenJDK \
           reference identity). */ \
        bool f569_a_tok = false, f569_b_tok = false; \
        std::string f569_a_ref, f569_b_ref; \
        if (a.type == DalvikType::CLASS_REF) { \
            f569_a_tok = true; \
            f569_a_ref = a.class_desc; \
        } else if (a.type == DalvikType::OBJECT_REF && a.object_id != 0 && \
                   heap_.has_object(a.object_id)) { \
            const auto* f569_ao = heap_.get(a.object_id); \
            if (f569_ao && \
                f569_ao->class_descriptor == "Ljava/lang/Class;") { \
                auto f569_ar = heap_.get_object_field(a.object_id, \
                                                      "__referent_desc"); \
                if (f569_ar.has_value() && \
                    f569_ar->type == DalvikType::STRING_REF && \
                    !f569_ar->string_val.empty()) { \
                    f569_a_tok = true; \
                    f569_a_ref = f569_ar->string_val; \
                } \
            } \
        } \
        if (b.type == DalvikType::CLASS_REF) { \
            f569_b_tok = true; \
            f569_b_ref = b.class_desc; \
        } else if (b.type == DalvikType::OBJECT_REF && b.object_id != 0 && \
                   heap_.has_object(b.object_id)) { \
            const auto* f569_bo = heap_.get(b.object_id); \
            if (f569_bo && \
                f569_bo->class_descriptor == "Ljava/lang/Class;") { \
                auto f569_br = heap_.get_object_field(b.object_id, \
                                                      "__referent_desc"); \
                if (f569_br.has_value() && \
                    f569_br->type == DalvikType::STRING_REF && \
                    !f569_br->string_val.empty()) { \
                    f569_b_tok = true; \
                    f569_b_ref = f569_br->string_val; \
                } \
            } \
        } \
        if (f569_a_tok && f569_b_tok) { \
            taken = (f569_a_ref op f569_b_ref); \
            static thread_local const bool f569_diag = \
                std::getenv("MINIANDROID_F569_DIAG") != nullptr; \
            static thread_local uint64_t f569_n = 0; \
            if (f569_diag && f569_n++ < 40) { \
                std::cerr << "[F-C4-569] " << op_name \
                          << " a=" << f569_a_ref \
                          << " b=" << f569_b_ref \
                          << " taken=" << (taken ? "YES" : "NO") \
                          << " caller=" << current_class_ << "." \
                          << current_method_ << std::endl; \
            } \
        } else if (a.type == DalvikType::STRING_REF && \
                   b.type == DalvikType::STRING_REF) { \
            /* P-58 (the value-model identity arm): two string registers \
               compare BY CONTENT — the engine's STRING_REF carries no \
               identity, so content equality IS the interning law the \
               compiler's acmp-on-interned-literals realizes. std::string \
               wrappers: CowStr has ==/!= natively; the relational ops \
               compare content lexicographically through the const-string& \
               conversion (a string "reference" compare that reaches the \
               relational opcodes is a malformed-verifier shape anyway — \
               the content order is the honest total order). */ \
            taken = (std::string(a.string_val) op std::string(b.string_val)); \
        } else { \
            /* S231 (cODER-ohc) — STRING_REF vs a NON-STRING reference \
               (NULL_REF, OBJECT_REF, CLASS_REF) is ALWAYS unequal: a \
               materialized string value is never the null reference and \
               never a heap object. The old oid tail collapsed STRING_REF \
               to 0 (it is neither OBJECT_REF nor CLASS_REF), so \
               `str != null` compiled to if-ne answered 0 != 0 = false \
               (and if-eq answered true) — the exact opposite of AOSP \
               acmp law. SolitaireCG evidence: \
               SolitaireCG.onResume `GetRestoreState() != "STATS"` — \
               mRestoreState was null on a cold launch (the app's \
               getLastNonConfigurationInstance answered null, correctly), \
               yet the collapsed compare took the taken==false path and \
               called DisplayStats(), replacing the real game view with \
               the stats screen on every launch. */ \
            bool a_s = (a.type == DalvikType::STRING_REF); \
            bool b_s = (b.type == DalvikType::STRING_REF); \
            if (a_s != b_s) { \
                taken = (0 op 1); \
            } else { \
                uint32_t a_obj = (a.type == DalvikType::OBJECT_REF) ? a.object_id \
                                : (a.type == DalvikType::CLASS_REF) ? a.ref_id : 0; \
                uint32_t b_obj = (b.type == DalvikType::OBJECT_REF) ? b.object_id \
                                : (b.type == DalvikType::CLASS_REF) ? b.ref_id : 0; \
                taken = (a_obj op b_obj); \
            } \
        } \
    } else if (a_is_ref || b_is_ref) { \
        /* F-075 (S21): mixed reference-vs-const/4-zero compare. The zero \
           word is the null reference in a reference context (ART Zero \
           reg-type, convertible to any reference). Compare identities: \
           the zero side answers 0; a NON-zero int against a reference is \
           a verifier impossibility — answer never-equal (if-eq not taken, \
           if-ne taken) instead of collapsing the OBJECT_REF side to 0 \
           through dalvik_int_value. First real-APK hit: dooz LL/b.remove \
           `if (node !== newNode)` where newNode was a const/4-null return \
           tagged INT32(0) — the old int path compared 0==0 and skipped \
           the map rebuild (CME "Hash code of an element has changed"). */ \
        auto f075_ref_id = [](const DalvikValue& v) -> uint32_t { \
            if (v.type == DalvikType::OBJECT_REF) return v.object_id; \
            if (v.type == DalvikType::CLASS_REF)  return static_cast<uint32_t>(v.ref_id); \
            return 0; /* NULL_REF or the zero word */ \
        }; \
        auto f075_is_zero = [](const DalvikValue& v) -> bool { \
            return v.type == DalvikType::NULL_REF || \
                   (v.type == DalvikType::INT32 && v.int_val == 0); \
        }; \
        bool f075_mixed_zero = (a_is_ref ? f075_is_zero(b) : f075_is_zero(a)); \
        if (f075_mixed_zero) { \
            uint32_t a_obj = a_is_ref ? f075_ref_id(a) : 0; \
            uint32_t b_obj = b_is_ref ? f075_ref_id(b) : 0; \
            taken = (a_obj op b_obj); \
        } else { \
            /* ref vs non-zero int: verifier-impossible — never equal; \
               (0 op 1) yields ==:false, !=:true for any op token */ \
            taken = (0 op 1); \
        } \
    } else { \
        taken = (a_val op b_val); \
    } \
    /* EXP-071: Diagnostic for if-lt/if-eq in onConfirm */ \
    if (current_class_.find("PhoneView$6") != std::string::npos && \
        current_method_ == "onConfirm") { \
        std::cerr << "[EXP071-IF] " << op_name << " PC=" << pc \
                  << " v" << (int)r.vA << "(type=" << static_cast<int>(a.type) \
                  << " val=" << a_val << ") vs v" << (int)r.vB \
                  << "(type=" << static_cast<int>(b.type) \
                  << " val=" << b_val << ") → taken=" << (taken ? "YES" : "NO") \
                  << " target=" << (pc + r.offset) << std::endl; \
    } \
    /* EXP-092+ DIRECT TRACE: Log every if-* branch in onNextPressed to
       prove the exact condition that determines the needShowAlert side path.
       The critical branch is at PC=604: `if-lt v4, v2, +28 → PC=632`
       where v4=countryState and v2=1. */ \
    if (current_class_.find("LoginActivity$PhoneView") != std::string::npos && \
        current_method_ == "onNextPressed") { \
        std::cerr << "[EXP092-ONNEXT-IF] " << op_name << " PC=" << pc \
                  << " v" << (int)r.vA << "(type=" << static_cast<int>(a.type) \
                  << " val=" << a_val; \
        if (a.type == DalvikType::OBJECT_REF) { std::cerr << " obj=" << a.object_id; } \
        std::cerr << ") vs v" << (int)r.vB \
                  << "(type=" << static_cast<int>(b.type) \
                  << " val=" << b_val; \
        if (b.type == DalvikType::OBJECT_REF) { std::cerr << " obj=" << b.object_id; } \
        std::cerr << ") → taken=" << (taken ? "YES" : "NO") \
                  << " target_pc=" << (pc + r.offset) \
                  << " next_pc=" << (taken ? (pc + r.offset) : (pc + 2)) \
                  << std::endl; \
    } \
    /* EXP-092+ PHASE 1: Log every if-* branch in LoginActivity.setPage to
       determine what page_value=13 means. The setPage switch at PC=0-32
       checks for pages 0, 5, 6, 9, 10, 12, 16, 17. page_value=13 does NOT
       match any of these — need to trace the actual branch outcomes. */ \
    if (current_class_.find("LoginActivity;") != std::string::npos && \
        current_class_.find("PhoneView") == std::string::npos && \
        current_method_ == "setPage") { \
        std::cerr << "[EXP092-SETPAGE-IF] " << op_name << " PC=" << pc \
                  << " v" << (int)r.vA << "(val=" << a_val \
                  << ") vs v" << (int)r.vB \
                  << "(val=" << b_val \
                  << ") → taken=" << (taken ? "YES" : "NO") \
                  << " target_pc=" << (pc + r.offset) \
                  << " next_pc=" << (taken ? (pc + r.offset) : (pc + 2)) \
                  << std::endl; \
    } \
    /* EXP-092+ PHASE 1: Log every if-* branch in fillNextCodeParams to
       understand why page_value=13 is chosen even when the mock response
       has type=TL_auth_sentCodeTypeSms. The critical branch is at PC=67:
       if-eqz v3 (instance-of check for TL_auth_sentCodeTypeFirebaseSms).
       If the type field IS set to TL_auth_sentCodeTypeSms, the instance-of
       checks for FirebaseSms/App/Call should all be false, and the code
       should reach the Sms path. */ \
    if (current_class_.find("LoginActivity;") != std::string::npos && \
        current_class_.find("PhoneView") == std::string::npos && \
        current_method_ == "fillNextCodeParams") { \
        std::cerr << "[EXP092-FILLNEXT-IF] " << op_name << " PC=" << pc \
                  << " v" << (int)r.vA << "(val=" << a_val; \
        if (a.type == DalvikType::OBJECT_REF) { std::cerr << " obj=" << a.object_id << " cls=" << a.class_desc; } \
        std::cerr << ") vs v" << (int)r.vB \
                  << "(val=" << b_val; \
        if (b.type == DalvikType::OBJECT_REF) { std::cerr << " obj=" << b.object_id << " cls=" << b.class_desc; } \
        std::cerr << ") → taken=" << (taken ? "YES" : "NO") \
                  << " target_pc=" << (pc + r.offset) \
                  << " next_pc=" << (taken ? (pc + r.offset) : (pc + 2)) \
                  << std::endl; \
    } \
    /* CONT-7 §12 A/B (env-gated, bounded): every 22t branch decision with */ \
    /* exact operand values — the dooz Lek1.b Semaphore ISE fires on a */ \
    /* path that the static bytecode says is unreachable with p=0, so the */ \
    /* branch evaluation itself must be observed at runtime. */ \
    if (r337_c7_trace && r337_c7_if_n < 64) { \
        ++r337_c7_if_n; \
        std::cerr << "[C7-IF] " << op_name << " pc=" << pc \
                  << " v" << (int)r.vA << "(k" << (int)a.type << "=" << a_val \
                  << ") vs v" << (int)r.vB << "(k" << (int)b.type << "=" \
                  << b_val << ") taken=" << (taken ? "YES" : "NO") \
                  << " target=" << (pc + r.offset) \
                  << " caller=" << current_class_ << "." << current_method_ \
                  << std::endl; \
    } \
    do_22t_branch(pc, r.offset, taken, op_name, r.vA, r.vB, a, b, trace); \
    if (taken) { \
        uint32_t target = pc + r.offset; \
        /* EXP-051: D8 unreachable marker — branch target past end-of-method. */ \
        /* Treated as "exit method" (= return-void), same as goto-past-end. */ \
        if (target >= bytecode_.size()) { \
            halted_ = true; halted_on_return_ = true; \
            trace.status = InstructionTrace::Status::HALT_RETURN; \
            trace.operands.push_back({"target", "exit_method (past end)"}); \
            pc_ = pc + 2; \
        } else { \
            pc_ = target; \
        } \
    } else { pc_ = pc + 2; } \
    return true; \
}

IMPLEMENT_IF_22T(if_eq, ==, "if-eq")
IMPLEMENT_IF_22T(if_ne, !=, "if-ne")
IMPLEMENT_IF_22T(if_lt, <,  "if-lt")
IMPLEMENT_IF_22T(if_ge, >=, "if-ge")
IMPLEMENT_IF_22T(if_gt, >,  "if-gt")
IMPLEMENT_IF_22T(if_le, <=, "if-le")

// ============================================================================
// Unimplemented Handler
// ============================================================================

void DalvikExecutionEngine::handle_unimplemented(uint16_t opcode, uint32_t pc, 
                                                InstructionTrace& trace) {
    trace.status = InstructionTrace::Status::UNIMPLEMENTED;
    trace.error_message = "Unimplemented opcode: 0x" + to_hex16(opcode);
    
    log("  UNIMPLEMENTED: 0x" + to_hex16(opcode) + " at " + to_hex(pc)
        + " in " + current_class_ + "." + current_method_);
    // M4-F028 diag: dump the raw code units around the bad pc — evidence
    // for walk-alignment forensics (a pc landing inside a literal means an
    // earlier instruction size or branch was decoded wrong). Throttled per
    // (class, method, pc) so loops can't flood the log.
    {
        static thread_local std::string last_unimpl_site;
        std::string site = current_class_ + "." + current_method_ + "@" +
                           to_hex(pc);
        if (site != last_unimpl_site) {
            last_unimpl_site = site;
            std::string dump;
            uint32_t lo = (pc >= 4) ? pc - 4 : 0;
            uint32_t hi = (pc + 6 <= bytecode_.size()) ? pc + 6
                                                       : (uint32_t)bytecode_.size();
            for (uint32_t u = lo; u < hi; ++u) {
                char buf[16];
                std::snprintf(buf, sizeof(buf), "%04x ", bytecode_[u] & 0xffff);
                dump += (u == pc) ? std::string("[") + buf + "]"
                                  : std::string(" ") + buf;
            }
            std::cerr << "[UNIMPL-DIAG] " << site
                      << " units[pc-4..pc+5]: " << dump << std::endl;
        }
    }
    
    if (config_.stop_on_unimplemented) {
        halted_ = true;
        halt_reason_ = "Unimplemented opcode: 0x" + to_hex16(opcode) + " at PC=" + to_hex(pc);
    }

    // GP-INT-002 (issue #582): the old resume was unconditionally `pc + 1`,
    // so a multi-unit unsupported opcode resumed INSIDE its operand words
    // (PC desync — every later decode misaligned). Resume law now:
    //   - defined-but-unimplemented opcodes: spec-correct instruction width
    //     (the DEX opcode → size table below), so the next fetch lands on
    //     the next instruction boundary;
    //   - UNDEFINED opcode values (no spec format exists): there IS no
    //     valid boundary — the method halts with a structured unsupported
    //     report instead of silently continuing.
    static const uint8_t kDalvikWidth[256] = {
        1, 1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 1, 1, 1, 1, 1,  // 0x00-0x0f
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 3, 2, 1, 1, 2,  // 0x10-0x1f
        2, 1, 2, 2, 3, 3, 3, 1, 1, 2, 3, 3, 3, 2, 2, 2,  // 0x20-0x2f
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 0, 0,  // 0x30-0x3f
        0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,  // 0x40-0x4f
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,  // 0x50-0x5f
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3,  // 0x60-0x6f
        3, 3, 3, 0, 3, 3, 3, 3, 3, 0, 0, 1, 1, 1, 1, 1,  // 0x70-0x7f
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,  // 0x80-0x8f
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,  // 0x90-0x9f
        1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,  // 0xa0-0xaf
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,  // 0xb0-0xbf
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,  // 0xc0-0xcf
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,  // 0xd0-0xdf
        2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,  // 0xe0-0xef
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3,  // 0xf0-0xff
    };

    const uint8_t w = kDalvikWidth[opcode & 0xFF];
    if (w == 0) {
        // Undefined opcode value: no valid resume boundary exists.
        halted_ = true;
        halt_reason_ = "Undefined opcode 0x" + to_hex16(opcode) + " at PC=" +
                       to_hex(pc) + " — no DEX instruction width exists; "
                       "execution cannot resume at an instruction boundary";
        trace.opcode_name = "undefined(0x" + to_hex16(opcode) + ")";
        return;
    }
    pc_ = pc + w;  // spec-correct boundary for defined-but-unimplemented opcodes
}

// ============================================================================
// Register Helpers
// ============================================================================

void DalvikExecutionEngine::set_register(uint16_t reg, const DalvikValue& value) {
    if (current_registers_) {
        current_registers_->write_v(reg, value);
        current_registers_->set_pc(pc_);
    }
}

// F-028b (M4 §A1) — WIDE-PAIR SLOT LAW implementation. Writes the full
// wide value into vReg and the high 32 bits of its bit pattern into the
// vReg+1 shadow slot (INT32-tagged), exactly mirroring ART's physical
// two-slot layout. Bounds-safe: write_v ignores out-of-range registers.
void DalvikExecutionEngine::set_wide_pair(uint16_t reg, const DalvikValue& value) {
    if (!current_registers_) return;
    current_registers_->write_v(reg, value);
    current_registers_->set_pc(pc_);
    uint64_t bits = 0;
    if (value.type == DalvikType::INT64) {
        bits = static_cast<uint64_t>(value.long_val);
    } else if (value.type == DalvikType::FLOAT64) {
        std::memcpy(&bits, &value.double_val, sizeof(bits));
    } else {
        return; // not a wide value — no shadow to fill
    }
    DalvikValue shadow;
    shadow.type = DalvikType::INT32;
    shadow.int_val = static_cast<int32_t>(static_cast<uint32_t>(bits >> 32));
    current_registers_->write_v(static_cast<uint16_t>(reg + 1), shadow);
}

DalvikValue DalvikExecutionEngine::get_register(uint16_t reg) const {
    if (current_registers_) {
        return current_registers_->read_v(reg);
    }
    return DalvikValue::make_uninit();
}

std::string DalvikExecutionEngine::register_name(uint8_t reg) const {
    if (current_registers_ && reg >= current_registers_->get_ins_count()) {
        return "v" + std::to_string(reg);
    } else if (current_registers_) {
        return "p" + std::to_string(reg - (current_registers_->get_size() - current_registers_->get_ins_count()));
    }
    return "v" + std::to_string(reg);
}

// ============================================================================
// API Bridge
// ============================================================================

// CYCLE-E: parse a DEX method proto "(params)return" into per-param type
// strings. Wide types ('J','D') occupy one param slot but two registers.
std::vector<std::string> parse_proto_param_types(const std::string& proto) {
    std::vector<std::string> types;
    size_t lp = proto.find('(');
    size_t rp = proto.find(')');
    if (lp == std::string::npos || rp == std::string::npos || rp <= lp) return types;
    std::string params = proto.substr(lp + 1, rp - lp - 1);
    size_t i = 0;
    while (i < params.size()) {
        char c = params[i];
        if (c == 'L') {
            size_t semi = params.find(';', i);
            if (semi == std::string::npos) break;
            types.push_back(params.substr(i, semi - i + 1));
            i = semi + 1;
        } else if (c == '[') {
            size_t start = i;
            while (i < params.size() && params[i] == '[') i++;
            if (i < params.size() && params[i] == 'L') {
                size_t semi = params.find(';', i);
                if (semi == std::string::npos) break;
                types.push_back(params.substr(start, semi - start + 1));
                i = semi + 1;
            } else {
                types.push_back(params.substr(start, i - start + 1));
                i += 1;
            }
        } else {
            types.push_back(std::string(1, c));
            i += 1;
        }
    }
    return types;
}

// CYCLE-E: signature-aware invoke argument builder (see forward decl).
std::vector<DalvikValue> build_invoke_args(
    const std::vector<DalvikValue>& raw,
    const std::vector<std::string>& types,
    bool is_static) {
    if (types.empty()) return raw;   // unresolvable proto → legacy passthrough
    std::vector<DalvikValue> args;
    size_t idx = 0;
    if (!is_static) {
        // Receiver slot passes through unchanged (identity must be kept).
        if (raw.empty()) return args;
        args.push_back(raw[0]);
        idx = 1;
    }
    for (const std::string& pt : types) {
        if (pt == "J" || pt == "D") {
            if (idx >= raw.size()) break;   // malformed call — keep what we have
            DalvikValue lo = raw[idx];
            DalvikValue hi = (idx + 1 < raw.size())
                                 ? raw[idx + 1]
                                 : DalvikValue::make_int(0);
            if (lo.type == DalvikType::INT64) {
                if (pt == "D") {
                    double d; int64_t bits = lo.long_val;
                    std::memcpy(&d, &bits, sizeof(d));
                    args.push_back(DalvikValue::make_double(d));
                } else {
                    args.push_back(lo);
                }
            } else if (lo.type == DalvikType::FLOAT64) {
                // F-028b wide-pair law: a FLOAT64-tagged slot already holds
                // the FULL 64-bit value (the tagged-union model keeps the
                // whole wide in one register). Reinterpret its bits per the
                // param type instead of union-aliasing int_val (the low 32
                // bits) against the possibly-unwritten shadow register —
                // the defect that turned every delegated double param into
                // a ~1e-315 denormal (dooz TransferFunction IAE).
                if (pt == "D") {
                    args.push_back(lo);
                } else {
                    int64_t bits; std::memcpy(&bits, &lo.double_val, sizeof(bits));
                    args.push_back(DalvikValue::make_long(bits));
                }
            } else {
                int64_t combined = (static_cast<int64_t>(hi.int_val) << 32) |
                                   (static_cast<uint32_t>(lo.int_val));
                if (pt == "D") {
                    double d; int64_t bits = combined;
                    std::memcpy(&d, &bits, sizeof(d));
                    args.push_back(DalvikValue::make_double(d));
                } else {
                    args.push_back(DalvikValue::make_long(combined));
                }
            }
            idx += 2;
        } else {
            if (idx >= raw.size()) break;   // malformed call — keep what we have
            DalvikValue v = raw[idx];
            if ((pt[0] == 'L' || pt[0] == '[') &&
                v.type == DalvikType::INT32 && v.int_val == 0) {
                // F-030 (MASTER-5 §A) — ZERO-IS-NULL-AT-REFERENCE-USE LAW.
                // Dalvik registers are untyped 32-bit slots (F-028 law);
                // `const/4 vX, #0` loads the POLYMORPHIC zero word, which
                // is an int 0 in a primitive context and the NULL REFERENCE
                // in a reference context. ART's verifier materializes this
                // as the `Zero` reg-type, convertible to ANY reference type
                // (art/runtime/verifier/reg types: Zero -> any ref). The
                // tagged-union engine must therefore re-type an INT32(0)
                // argument as null when the callee's declared param type is
                // a reference (L...; or [...). Without this law the null
                // crosses the invoke boundary tagged INT32(0) and every
                // identity-sensitive consumer (AtomicReferenceArray CAS,
                // == compares) sees boxed-int-0 instead of null — the
                // first real-APK hit: dooz LY1/b;.D passes const/4 #0 as
                // the `expected` state of Segment cell CAS (LY1/j;.j) and
                // the lock-free state machine spins forever because the
                // CAS can never match (correct F-028h identity law: null
                // is not boxed Integer 0). No app special-casing: every
                // real DEX that passes const/4 null into object params
                // benefits (the standard Kotlin/Java `null` idiom).
                args.push_back(DalvikValue::make_null());
            } else if (pt == "F" && v.type == DalvikType::INT32) {
                // EXP-095 CM-019 law: float params arrive as raw bits.
                float f; int32_t bits = v.int_val;
                std::memcpy(&f, &bits, sizeof(f));
                args.push_back(DalvikValue::make_float(f));
            } else if (v.type == DalvikType::INT32) {
                // CHAR-PROBE campaign: signature-aware primitive retyping.
                // DEX registers are untyped; the proto's param char is the
                // only authority. Without this, char params leak their int
                // code into string concat ("88" for 'X') and boolean params
                // print "0"/"1" instead of "true"/"false".
                switch (pt.empty() ? 'I' : pt[0]) {
                    case 'C': {
                        DalvikValue c = v;
                        c.type = DalvikType::CHAR;
                        c.int_val &= 0xFFFF;
                        args.push_back(c);
                        break;
                    }
                    case 'Z':
                        args.push_back(DalvikValue::make_bool(v.int_val != 0));
                        break;
                    case 'B': {
                        DalvikValue b = v;
                        b.type = DalvikType::BYTE;
                        b.int_val = static_cast<int8_t>(v.int_val & 0xFF);
                        args.push_back(b);
                        break;
                    }
                    case 'S': {
                        DalvikValue s = v;
                        s.type = DalvikType::SHORT;
                        s.int_val = static_cast<int16_t>(v.int_val & 0xFFFF);
                        args.push_back(s);
                        break;
                    }
                    default:
                        args.push_back(v);
                        break;
                }
            } else {
                args.push_back(v);
            }
            idx += 1;
        }
    }
    return args;
}

// CYCLE-E: AOSP framework enum constant ordinals. The android.* framework
// is NOT defined in app DEX files, so framework enum <clinit> never runs
// and sget-object of e.g. Paint$Style.STROKE materialized NULL — breaking
// Paint.setStyle / Path.setFillType / PorterDuff modes for every real
// drawing call. Ordinals below are the fixed AOSP declaration orders.
static const miniandroid::dalvik::KvInt kOrdinals[] = {
    {"Landroid/graphics/Paint$Style;.FILL", 0},
    {"Landroid/graphics/Paint$Style;.STROKE", 1},
    {"Landroid/graphics/Paint$Style;.FILL_AND_STROKE", 2},
    {"Landroid/graphics/Paint$Cap;.BUTT", 0},
    {"Landroid/graphics/Paint$Cap;.ROUND", 1},
    {"Landroid/graphics/Paint$Cap;.SQUARE", 2},
    {"Landroid/graphics/Paint$Join;.MITER", 0},
    {"Landroid/graphics/Paint$Join;.ROUND", 1},
    {"Landroid/graphics/Paint$Join;.BEVEL", 2},
    {"Landroid/graphics/Paint$Align;.LEFT", 0},
    {"Landroid/graphics/Paint$Align;.CENTER", 1},
    {"Landroid/graphics/Paint$Align;.RIGHT", 2},
    {"Landroid/graphics/Path$FillType;.WINDING", 0},
    {"Landroid/graphics/Path$FillType;.EVEN_ODD", 1},
    {"Landroid/graphics/Path$FillType;.INVERSE_WINDING", 2},
    {"Landroid/graphics/Path$FillType;.INVERSE_EVEN_ODD", 3},
    {"Landroid/graphics/Path$Direction;.CCW", 0},
    {"Landroid/graphics/Path$Direction;.CW", 1},
    {"Landroid/graphics/PorterDuff$Mode;.CLEAR", 0},
    {"Landroid/graphics/PorterDuff$Mode;.SRC", 1},
    {"Landroid/graphics/PorterDuff$Mode;.DST", 2},
    {"Landroid/graphics/PorterDuff$Mode;.SRC_OVER", 3},
    {"Landroid/graphics/PorterDuff$Mode;.DST_OVER", 4},
    {"Landroid/graphics/PorterDuff$Mode;.SRC_IN", 5},
    {"Landroid/graphics/PorterDuff$Mode;.DST_IN", 6},
    {"Landroid/graphics/PorterDuff$Mode;.SRC_OUT", 7},
    {"Landroid/graphics/PorterDuff$Mode;.DST_OUT", 8},
    {"Landroid/graphics/PorterDuff$Mode;.SRC_ATOP", 9},
    {"Landroid/graphics/PorterDuff$Mode;.DST_ATOP", 10},
    {"Landroid/graphics/PorterDuff$Mode;.XOR", 11},
    {"Landroid/graphics/PorterDuff$Mode;.DARKEN", 12},
    {"Landroid/graphics/PorterDuff$Mode;.LIGHTEN", 13},
    {"Landroid/graphics/PorterDuff$Mode;.MULTIPLY", 14},
    {"Landroid/graphics/PorterDuff$Mode;.SCREEN", 15},
    {"Landroid/graphics/PorterDuff$Mode;.ADD", 16},
    {"Landroid/graphics/PorterDuff$Mode;.OVERLAY", 17},
    {"Landroid/graphics/Shader$TileMode;.CLAMP", 0},
    // S108 ROOT-022: java.nio.ByteOrder constants (OpenJDK order: BIG_ENDIAN
    // declared first). Telegram's NativeByteBuffer ctor does
    // ByteBuffer.allocate(n).order(ByteOrder.LITTLE_ENDIAN) — the sget of
    // LITTLE_ENDIAN answered NULL and order() NPE'd, killing every
    // ByteBuffer write path (NativeByteBuffer.writeInt32 chain).
    {"Ljava/nio/ByteOrder;.BIG_ENDIAN", 0},
    {"Ljava/nio/ByteOrder;.LITTLE_ENDIAN", 1},
    {"Landroid/graphics/Shader$TileMode;.REPEAT", 1},
    {"Landroid/graphics/Shader$TileMode;.MIRROR", 2},
    {"Landroid/graphics/Region$Op;.DIFFERENCE", 0},
    {"Landroid/graphics/Region$Op;.INTERSECT", 1},
    {"Landroid/graphics/Region$Op;.UNION", 2},
    {"Landroid/graphics/Region$Op;.XOR", 3},
    {"Landroid/graphics/Region$Op;.REVERSE_DIFFERENCE", 4},
    {"Landroid/graphics/Region$Op;.REPLACE", 5},
    {"Landroid/graphics/Bitmap$Config;.ALPHA_8", 0},
    {"Landroid/graphics/Bitmap$Config;.RGB_565", 1},
    {"Landroid/graphics/Bitmap$Config;.ARGB_4444", 2},
    {"Landroid/graphics/Bitmap$Config;.ARGB_8888", 3},
    // F-NEW-351: the full AOSP Bitmap.Config family (Bitmap.java decl
    // order; API 26+ adds RGBA_F16, API 26 adds HARDWARE). The compose
    // ImageBitmap config converter consults these by name — the two
    // missing members answered null in the dooz v23 icon draw.
    {"Landroid/graphics/Bitmap$Config;.RGBA_F16", 4},
    {"Landroid/graphics/Bitmap$Config;.HARDWARE", 5},
    // F-NEW-351: the FULL AOSP android.graphics.BlendMode family
    // (BlendMode.java declaration order — API 29). Paint.setBlendMode
    // consumers (compose DrawCache.clear = drawRect(Black, BlendMode
    // .Clear) — the vector-icon cache reset) previously sget NULL: the
    // blend mode never recorded and the cache reset painted SOLID BLACK
    // (the dooz material-icon black squares). Same table drives the sget
    // constant law → identity coherent with enum_arg_ordinal.
    {"Landroid/graphics/BlendMode;.CLEAR", 0},
    {"Landroid/graphics/BlendMode;.SRC", 1},
    {"Landroid/graphics/BlendMode;.DST", 2},
    {"Landroid/graphics/BlendMode;.SRC_OVER", 3},
    {"Landroid/graphics/BlendMode;.DST_OVER", 4},
    {"Landroid/graphics/BlendMode;.SRC_IN", 5},
    {"Landroid/graphics/BlendMode;.DST_IN", 6},
    {"Landroid/graphics/BlendMode;.SRC_OUT", 7},
    {"Landroid/graphics/BlendMode;.DST_OUT", 8},
    {"Landroid/graphics/BlendMode;.SRC_ATOP", 9},
    {"Landroid/graphics/BlendMode;.DST_ATOP", 10},
    {"Landroid/graphics/BlendMode;.XOR", 11},
    {"Landroid/graphics/BlendMode;.DARKEN", 12},
    {"Landroid/graphics/BlendMode;.LIGHTEN", 13},
    {"Landroid/graphics/BlendMode;.MULTIPLY", 14},
    {"Landroid/graphics/BlendMode;.SCREEN", 15},
    {"Landroid/graphics/BlendMode;.PLUS", 16},
    {"Landroid/graphics/BlendMode;.OVERLAY", 17},
    {"Landroid/graphics/BlendMode;.REDUCE", 18},
    {"Landroid/view/View$Visibility;.VISIBLE", 0},
    {"Landroid/view/View$Visibility;.INVISIBLE", 1},
    {"Landroid/view/View$Visibility;.GONE", 2},
    // F-NEW-216 ENUM-CONSTANT NAME LAW (OpenJDK TimeUnit.java): the member
    // is NANOSECONDS — "NANOS" is java.time.temporal.ChronoUnit's name and
    // TimeUnit has no such member. The fictional name made every sget of
    // TimeUnit.NANOSECONDS answer null (droidify face: kotlin toDuration
    // NPE'd on the null receiver inside the Dagger SettingsSerializer
    // chain — datastore settings never built, app died far from cause).
    {"Ljava/util/concurrent/TimeUnit;.NANOSECONDS", 0},
    {"Ljava/util/concurrent/TimeUnit;.MICROSECONDS", 1},
    {"Ljava/util/concurrent/TimeUnit;.MILLISECONDS", 2},
    {"Ljava/util/concurrent/TimeUnit;.SECONDS", 3},
    {"Ljava/util/concurrent/TimeUnit;.MINUTES", 4},
    {"Ljava/util/concurrent/TimeUnit;.HOURS", 5},
    {"Ljava/util/concurrent/TimeUnit;.DAYS", 6},
    {"Landroid/text/TextUtils$TruncateAt;.START", 0},
    {"Landroid/text/TextUtils$TruncateAt;.MIDDLE", 1},
    {"Landroid/text/TextUtils$TruncateAt;.END", 2},
    {"Landroid/text/TextUtils$TruncateAt;.MARQUEE", 3},
    {"Landroid/text/TextUtils$TruncateAt;.END_SMALL", 4},
    {"Landroid/widget/ImageView$ScaleType;.MATRIX", 0},
    {"Landroid/widget/ImageView$ScaleType;.FIT_XY", 1},
    {"Landroid/widget/ImageView$ScaleType;.FIT_START", 2},
    {"Landroid/widget/ImageView$ScaleType;.FIT_CENTER", 3},
    {"Landroid/widget/ImageView$ScaleType;.FIT_END", 4},
    {"Landroid/widget/ImageView$ScaleType;.CENTER", 5},
    {"Landroid/widget/ImageView$ScaleType;.CENTER_CROP", 6},
    {"Landroid/widget/ImageView$ScaleType;.CENTER_INSIDE", 7},
    // 371-CLOSEOUT: java.lang.Thread.State (OpenJDK Thread.java declaration
    // order) — Thread.State.values()/valueOf() used by thread-pool and
    // lifecycle inspection code across real apps.
    {"Ljava/lang/Thread$State;.NEW", 0},
    {"Ljava/lang/Thread$State;.RUNNABLE", 1},
    {"Ljava/lang/Thread$State;.BLOCKED", 2},
    {"Ljava/lang/Thread$State;.WAITING", 3},
    {"Ljava/lang/Thread$State;.TIMED_WAITING", 4},
    {"Ljava/lang/Thread$State;.TERMINATED", 5},
    // F-NEW-295 (CONT-35): android.text.Layout$Alignment — AOSP Layout.java
    // declaration order, decoded instruction-level from the toolchain's
    // android-34.jar clinit (ALIGN_NORMAL=0, ALIGN_OPPOSITE=1,
    // ALIGN_CENTER=2; NO ALIGN_LEFT/ALIGN_RIGHT members exist on this API
    // level). Compose's R8-inlined text-layout alignment resolver
    // (composeStopwatch Ljd1;.<clinit>) calls Layout.Alignment.values(),
    // searches the array for the names "ALIGN_LEFT"/"ALIGN_RIGHT" and falls
    // back to the ALIGN_NORMAL sget when absent — but with no table rows
    // the 371-CLOSEOUT values() arm found no constants and answered NULL,
    // so the clinit's array-length (pc=6) NPE'd and the text pass aborted.
    // Same table drives the sget constant law → identity coherent.
    {"Landroid/text/Layout$Alignment;.ALIGN_NORMAL", 0},
    {"Landroid/text/Layout$Alignment;.ALIGN_OPPOSITE", 1},
    {"Landroid/text/Layout$Alignment;.ALIGN_CENTER", 2},
};
int framework_enum_ordinal(const std::string& class_desc,
                                  const std::string& field_name) {
    return kvint_table_find(kOrdinals, sizeof(kOrdinals) / sizeof(kOrdinals[0]),
                            class_desc + "." + field_name, -1);
}

// 371-CLOSEOUT: framework-enum static accessor support. Returns the ORDERED
// (ordinal, name) constant list for a framework enum class by scanning the
// kOrdinals table above (entries are "Lcls;.NAME", ordinal). Art/Android
// semantics: every enum class has values() → the constants in declaration
// order, and valueOf(String) → the matching constant. The same table drives
// sget constant materialization, so identity is coherent across accessors.
std::vector<std::pair<int, std::string>>
framework_enum_constants(const std::string& class_desc) {
    std::vector<std::pair<int, std::string>> out;
    const std::string prefix = class_desc + ".";
    const size_t kTableSize = sizeof(kOrdinals) / sizeof(kOrdinals[0]);
    for (size_t i = 0; i < kTableSize; ++i) {
        std::string key = kOrdinals[i].k;
        if (key.rfind(prefix, 0) == 0) {
            out.emplace_back(kOrdinals[i].v, key.substr(prefix.size()));
        }
    }
    std::sort(out.begin(), out.end(),
              [](const std::pair<int, std::string>& a,
                 const std::pair<int, std::string>& b) {
                  return a.first < b.first;
              });
    return out;
}

// F-110e (S62+): framework static INT constant table (AOSP values).
// The sget (int) opcode on android.* static final ints previously fell to
// the typed-zero default because the class is not in app DEX and its
// <clinit> never runs. MotionEvent.ACTION_DOWN (0) compared correctly by
// accident, but every non-zero constant (ACTION_UP=1, MOVE=2, CANCEL=3)
// compared false — a touch listener's `event.getAction() == ACTION_UP`
// arm could never fire. Table = AOSP MotionEvent.java values.
int framework_static_int(const std::string& class_desc,
                                const std::string& field_name) {
    static const miniandroid::dalvik::KvInt kStaticInts[] = {
    {"Landroid/view/MotionEvent;.ACTION_DOWN", 0},
    {"Landroid/view/MotionEvent;.ACTION_UP", 1},
    {"Landroid/view/MotionEvent;.ACTION_MOVE", 2},
    {"Landroid/view/MotionEvent;.ACTION_CANCEL", 3},
    {"Landroid/view/MotionEvent;.ACTION_OUTSIDE", 4},
    {"Landroid/view/MotionEvent;.ACTION_POINTER_DOWN", 5},
    {"Landroid/view/MotionEvent;.ACTION_POINTER_UP", 6},
    {"Landroid/view/MotionEvent;.ACTION_MASK", 255},
    // S129 (R-NEW-425, CAP-INPUT-108): AOSP MotionEvent axis constants —
    // VelocityTracker.getAxisVelocity(AXIS_X|AXIS_Y) and the planar-axis
    // set in the native tracker law (VelocityTracker.cpp PLANAR_AXES).
    {"Landroid/view/MotionEvent;.AXIS_X", 0},
    {"Landroid/view/MotionEvent;.AXIS_Y", 1},
    {"Landroid/view/MotionEvent;.AXIS_SCROLL", 26},
    // S123 ROOT-CALC-B — android.view.Gravity constant family (AOSP
    // Gravity.java law). sget of Gravity.TOP in the lib chain previously
    // fell through every synthesis arm and answered NULL_REF; the null
    // register became TypedArray.getInt's defValue slot (non-INT32 →
    // default 0) and SlidingUpPanelLayout.setGravity(0) threw
    // IllegalArgumentException "gravity must be set to either top or
    // bottom" at the calculator's first inflate. AOSP values:
    //   LEFT = AXIS_SPECIFIED|AXIS_PULL_BEFORE<<AXIS_X_SHIFT = 3
    //   TOP  = AXIS_SPECIFIED|AXIS_PULL_BEFORE<<AXIS_Y_SHIFT = 48
    //   END/START carry RELATIVE_HORIZONTAL_GRAVITY (0x00800000).
    {"Landroid/view/Gravity;.NO_GRAVITY", 0},
    {"Landroid/view/Gravity;.LEFT", 3},
    {"Landroid/view/Gravity;.RIGHT", 5},
    {"Landroid/view/Gravity;.TOP", 48},
    {"Landroid/view/Gravity;.BOTTOM", 80},
    {"Landroid/view/Gravity;.CENTER_VERTICAL", 16},
    {"Landroid/view/Gravity;.CENTER_HORIZONTAL", 1},
    {"Landroid/view/Gravity;.CENTER", 17},
    {"Landroid/view/Gravity;.FILL_VERTICAL", 112},
    {"Landroid/view/Gravity;.FILL_HORIZONTAL", 7},
    {"Landroid/view/Gravity;.FILL", 119},
    {"Landroid/view/Gravity;.CLIP_VERTICAL", 128},
    {"Landroid/view/Gravity;.CLIP_HORIZONTAL", 8},
    {"Landroid/view/Gravity;.START", 8388611},       // 0x00800003
    {"Landroid/view/Gravity;.END", 8388613},         // 0x00800005
    {"Landroid/view/Gravity;.RELATIVE_LAYOUT_DIRECTION", 8388608},
    {"Landroid/view/Gravity;.DISPLAY_CLIP_VERTICAL", 0x10000000},
    {"Landroid/view/Gravity;.DISPLAY_CLIP_HORIZONTAL", 0x01000000},
    // S83-GFX-BASE §24/§25: GL constants (GL10 = ES1.0; GLES20 shares the
    // buffer-bit values). l6 evidence: GL10.GL_COLOR_BUFFER_BIT sget
    // resolved 0 → glClear(0) → GL_INVALID_VALUE → black frame.
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_COLOR_BUFFER_BIT", 0x4000},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_DEPTH_BUFFER_BIT", 0x100},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_STENCIL_BUFFER_BIT", 0x400},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_ACCUM_BUFFER_BIT", 0x200},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_TRUE", 1},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_FALSE", 0},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_BLEND", 0x0BE2},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_TEXTURE_2D", 0x0DE1},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_DEPTH_TEST", 0x0B71},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_ALPHA_TEST", 0x0BC0},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_SRC_ALPHA", 0x0302},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_ONE_MINUS_SRC_ALPHA", 0x0303},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_TRIANGLES", 0x0004},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_TRIANGLE_STRIP", 0x0005},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_TRIANGLE_FAN", 0x0006},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_VERTEX_ARRAY", 0x8074},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_COLOR_ARRAY", 0x8076},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_TEXTURE_COORD_ARRAY", 0x8078},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_MODELVIEW", 0x1700},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_PROJECTION", 0x1701},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_FLOAT", 0x1406},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_UNSIGNED_SHORT", 0x1403},
    {"Ljavax/microedition/khronos/opengles/GL10;.GL_UNSIGNED_BYTE", 0x1401},
    {"Landroid/opengl/GLES20;.GL_COLOR_BUFFER_BIT", 0x4000},
    {"Landroid/opengl/GLES20;.GL_DEPTH_BUFFER_BIT", 0x100},
    {"Landroid/opengl/GLES20;.GL_STENCIL_BUFFER_BIT", 0x400},
    {"Landroid/opengl/GLES20;.GL_TRUE", 1},
    {"Landroid/opengl/GLES20;.GL_FALSE", 0},
    {"Landroid/opengl/GLES20;.GL_FLOAT", 0x1406},
    {"Landroid/opengl/GLES20;.GL_TRIANGLES", 0x0004},
    {"Landroid/opengl/GLES20;.GL_TRIANGLE_STRIP", 0x0005},
    {"Landroid/opengl/GLES20;.GL_TRIANGLE_FAN", 0x0006},
    {"Landroid/opengl/GLES20;.GL_VERTEX_SHADER", 0x8B31},
    {"Landroid/opengl/GLES20;.GL_FRAGMENT_SHADER", 0x8B30},
    {"Landroid/opengl/GLES20;.GL_ARRAY_BUFFER", 0x8892},
    {"Landroid/opengl/GLES20;.GL_STATIC_DRAW", 0x88E4},
    {"Landroid/opengl/GLES20;.GL_TEXTURE_2D", 0x0DE1},
    {"Landroid/opengl/GLES20;.GL_RGBA", 0x1908},
    {"Landroid/opengl/GLES20;.GL_RGB", 0x1907},
    {"Landroid/opengl/GLES20;.GL_UNSIGNED_BYTE", 0x1401},
    {"Landroid/opengl/GLES20;.GL_SRC_ALPHA", 0x0302},
    {"Landroid/opengl/GLES20;.GL_ONE_MINUS_SRC_ALPHA", 0x0303},
    };
    const std::string key = class_desc + "." + field_name;
    for (const auto& e : kStaticInts)
        if (key == e.k) return e.v;
    if (std::getenv("MINIANDROID_S83_DEBUG") &&
        key.find("GL") != std::string::npos)
        std::cerr << "[S83-STATIC-MISS] " << class_desc << "." << field_name
                  << std::endl;
    return -1;
}

// EXP-051: Convert a DalvikValue (engine type) into a CallContext::Arg
// (shadow-registry type). This is the only translation point — keeping
// the engine and the shadow registry decoupled.
framework::CallContext::Arg dalvik_value_to_arg(const DalvikValue& v) {
    using namespace framework;
    CallContext::Arg a;
    switch (v.type) {
        case DalvikType::INT32:
        case DalvikType::BYTE:
        case DalvikType::SHORT:
        case DalvikType::CHAR:
            a.kind = CallContext::Arg::Kind::INT;
            a.int_val = v.int_val;
            break;
        case DalvikType::INT64:
            a.kind = CallContext::Arg::Kind::LONG;
            a.long_val = v.long_val;
            break;
        case DalvikType::FLOAT32:
            a.kind = CallContext::Arg::Kind::FLOAT;
            a.float_val = v.float_val;
            break;
        case DalvikType::FLOAT64:
            a.kind = CallContext::Arg::Kind::DOUBLE;
            a.double_val = v.double_val;
            break;
        case DalvikType::BOOLEAN:
            a.kind = CallContext::Arg::Kind::BOOL;
            a.bool_val = v.bool_val;
            break;
        case DalvikType::STRING_REF:
            a.kind = CallContext::Arg::Kind::STRING;
            a.string_val = v.string_val;
            break;
        case DalvikType::OBJECT_REF:
            a.kind = CallContext::Arg::Kind::OBJECT;
            a.object_id = v.object_id;
            a.object_class = v.class_desc;
            // EXP-091: Also copy string_val — when a String object is passed
            // as an argument (e.g., setText(stringFromLocaleController)),
            // the DalvikValue may have BOTH object_id AND string_val set.
            // The string_val comes from const-string/move-result-object paths
            // where the engine stores the resolved string alongside the ref.
            // Without this, arg_as_string() returns empty for OBJECT args,
            // causing setText(CharSequence) to set empty text on ViewShadow nodes.
            a.string_val = v.string_val;
            break;
        case DalvikType::NULL_REF:
            a.kind = CallContext::Arg::Kind::NULL_REF;
            break;
        case DalvikType::CLASS_REF:
            // MASTER-2 FIX-INTENT-001 (AOSP Intent(Context, Class) law):
            // const-class materializes a Class object whose descriptor is
            // the component identity. Folding CLASS_REF to NULL dropped the
            // descriptor, so Intent(Context, NoteEdit.class) left the
            // component UNSET and startActivity reported ACTIVITY_NOT_FOUND
            // (unote addNote). Carry the descriptor on the arg.
            // F-089 (R-NEW-315): Class IDENTITY law for key/hash surfaces.
            // OpenJDK: a Class object is a SINGLETON per class+loader — all
            // references to X.class are the SAME object and compare
            // equal. The engine materializes a fresh token per evaluation
            // (ref_id = instruction sequence), so identity-keyed surfaces
            // (map caches keyed by Class — androidx.navigation
            // NavigatorProvider's name cache, WeakHashMap<Class,...>)
            // collapsed: every lookup missed, and when ref_id collided at
            // 0 the cache returned the FIRST class's value for EVERY class
            // (dooz: all navigators cached under the name "navigation" →
            // getNavigator("composable") → ISE → composition death).
            // The descriptor IS the deterministic identity: carry it in
            // string_val so arg_as_string()/key builders use it.
            a.kind = CallContext::Arg::Kind::OBJECT;
            a.object_id = v.ref_id;
            a.object_class = v.class_desc;
            a.string_val = v.class_desc;
            break;
        default:
            // VOID_, UNINITIALIZED, REGISTER_UNSET.
            // Default to NULL_REF (treated as null object) which is
            // safe for most call sites.
            a.kind = CallContext::Arg::Kind::NULL_REF;
            break;
    }
    return a;
}

// EXP-051: Convert a CallResult (shadow-registry type) back into a
// DalvikValue (engine type).
DalvikValue call_result_to_dalvik(const framework::CallResult& r) {
    using namespace framework;
    switch (r.ret_kind) {
        case CallResult::RetKind::INT:     return DalvikValue::make_int(r.int_val);
        case CallResult::RetKind::LONG:    return DalvikValue::make_long(r.long_val);
        case CallResult::RetKind::FLOAT:   return DalvikValue::make_float(r.float_val);
        case CallResult::RetKind::DOUBLE:  return DalvikValue::make_double(r.double_val);
        case CallResult::RetKind::BOOL:    return DalvikValue::make_bool(r.bool_val);
        case CallResult::RetKind::STRING:  return DalvikValue::make_string(r.string_val, r.object_id);
        case CallResult::RetKind::OBJECT:  return DalvikValue::make_object(r.object_id, r.object_class);
        case CallResult::RetKind::NULL_REF:return DalvikValue::make_null();
        case CallResult::RetKind::VOID:
        default:                           return DalvikValue::make_void();
    }
}

// ────────────────────────────────────────────────────────────────────────
// F-105 (S59, R-NEW-379) — NOTE on the failed re-homing design: re-homing
// contradicted shadow references onto heap proxies was prototyped and
// REJECTED — the proxy id breaks the NEXT shadow hop (getTag/getParent on
// the proxy id find no ViewShadow node — the entity's id IS the shadow
// table key). The law lives in execute_instance_of instead: reconcile the
// register's creation-site class declaration with the heap record there.
// ────────────────────────────────────────────────────────────────────────

bool DalvikExecutionEngine::try_shadow_dispatch(const std::string& class_name,
                                                const std::string& method,
                                                const std::vector<DalvikValue>& args,
                                                DalvikValue& result,
                                                ApiCallTrace::Status& status) {
    if (shadow_registry_ == nullptr) return false;
    // F-NEW-267 (CONT-61): TOUCH-WINDOW BRIDGE probe — every bridge call the
    // dispatched DEX touch override makes (env-gated, bounded). Answers
    // which framework answers the compose input pipeline asked for and
    // which silently typed-defaulted (the consumed=false decode).
    if (touch_dispatch_active_) {
        static thread_local const bool tw_on =
            diag_env("MINIANDROID_TOUCH_WINDOW_TRACE");
        static thread_local uint64_t tw_n = 0;
        if (tw_on && tw_n++ < 400)
            std::cerr << "[TOUCHWIN-BRIDGE] " << class_name << "." << method
                      << " argc=" << args.size()
                      << " caller=" << current_class_ << "."
                      << current_method_ << std::endl;
    }
    // F-NEW-344 probe (CONT-61): every Landroid/text/Layout; bridge call —
    // the compose text intrinsic leg (getDesiredWidth family). Answers
    // whether the intrinsic path reaches the engine and with what args.
    if (class_name == "Landroid/text/Layout;") {
        static thread_local uint64_t lay_n = 0;
        if (lay_n++ < 40) {
            std::cerr << "[F344-LAYOUT] " << method
                      << " argc=" << args.size()
                      << " caller=" << current_class_ << "."
                      << current_method_ << std::endl;
        }
    }
    // CONT-36 (F-NEW-297 evidence): DRAW-OP ATTRIBUTION — env-gated,
    // bounded. Every Canvas draw-primitive bridge call INSIDE the
    // custom-view draw window, with the EXECUTING DEX caller. Answers
    // which DEX site records the frame canvas ops (the Compose draw walk
    // stops before the text path — where exactly?).
    {
        static thread_local const bool cdw_on =
            diag_env("MINIANDROID_CANVAS_DRAW_WIN_TRACE");
        static const char* cdw_faces[] = {
            "drawColor", "drawRect", "drawRoundRect", "drawCircle",
            "drawLine", "drawText", "drawTextRun", "drawPosText",
            "drawPath", "drawBitmap", "drawArc", "drawOval",
            "drawPoints", "drawLines", "saveLayer", "clipRect", "clipPath"};
        if (cdw_on && draw_window_active_) {
            for (const char* f : cdw_faces) {
                if (method == f) {
                    static thread_local uint64_t cdw_n = 0;
                    if (cdw_n++ < 400)
                        std::cerr << "[CDW-OP] " << class_name << "."
                                  << method << " caller=" << current_class_
                                  << "." << current_method_ << " recv="
                                  << (!args.empty() ? args[0].object_id : 0u)
                                  << std::endl;
                    break;
                }
            }
        }
    }
    // LAW-C/E/F DETERMINATION DIAG (CONT-18, bounded 60/env-gated): every
    // try_shadow_dispatch entry for a Java-8 default-method / view / stream
    // face — answers which class_name the engine routes, with which
    // receiver, and (paired with the CollectionShadow entry diag) whether
    // the collection shadow even sees the call.
    {
        static const bool lawcef_on =
            diag_env("MINIANDROID_LAWCEF_TRACE");
        static const char* lawcef_faces[] = {
            "removeIf", "getOrDefault", "forEach", "merge",
            "computeIfAbsent", "compute", "sort", "removeAll",
            "retainAll", "subList", "stream", "streamOf",
            "remove", "containsKey", "size", "of", "filter", "collect", "toList"};
        if (lawcef_on) {
            for (const char* f : lawcef_faces) {
                if (method == f) {
                    static thread_local uint64_t lawcef_n = 0;
                    if (lawcef_n++ < 60)
                        std::cerr << "[LAWCEF-ENG] " << class_name << "."
                                  << method << " recv="
                                  << (!args.empty() ? args[0].object_id : 0u)
                                  << " cls="
                                  << (!args.empty() ? std::string(args[0].class_desc)
                                                    : std::string("-"))
                                  << " caller=" << current_class_ << "."
                                  << current_method_ << std::endl;
                    break;
                }
            }
        }
    }

    // ────────────────────────────────────────────────────────────────────
    // S81 FIX-1 (VF-DIALOG-ITEMS) — dual-view of the bridge_to_api law:
    // AlertDialog$Builder.setItems reaches the DialogShadow through THIS
    // dispatch path when the receiver's runtime class is in the DEX index
    // (the bridge_to_api copy only covers the class-miss fallthrough, the
    // same two-view shape as R-NEW-339 getSystemService). Materialize the
    // heap array into the builder window's items BEFORE the shadow runs so
    // the dialog paints real item rows; the shadow still records the
    // listener + choice state afterwards.
    // ────────────────────────────────────────────────────────────────────
    if (method == "setItems" &&
        class_name.find("AlertDialog$Builder") != std::string::npos &&
        args.size() >= 2 &&
        args[0].type == DalvikType::OBJECT_REF && args[0].object_id != 0 &&
        args[1].type == DalvikType::OBJECT_REF && args[1].object_id != 0) {
        uint32_t arr_id = args[1].object_id;
        auto len_f = heap_.get_object_field(arr_id, "__array_length__");
        if (!len_f.has_value() || len_f->type != DalvikType::INT32)
            len_f = heap_.get_object_field(arr_id, "__new_array_length__");
        int32_t n_items = (len_f.has_value() && len_f->type == DalvikType::INT32)
                              ? len_f->int_val : 0;
        if (n_items > 0 && n_items < 512) {
            auto* dsh = shadow_registry_->find_as<framework::DialogShadow>();
            framework::DialogWindow* win =
                dsh ? dsh->window_by_obj(args[0].object_id) : nullptr;
            if (win) {
                win->items.clear();
                for (int32_t i = 0; i < n_items; ++i) {
                    auto el = heap_.get_object_field(
                        arr_id, "array[" + std::to_string(i) + "]");
                    if (el.has_value() && el->type == DalvikType::STRING_REF)
                        win->items.push_back(el->string_val);
                    else if (el.has_value() && el->type == DalvikType::OBJECT_REF &&
                             el->object_id != 0) {
                        auto st = heap_.get_object_field(el->object_id, "s");
                        if (st.has_value() && st->type == DalvikType::STRING_REF)
                            win->items.push_back(st->string_val);
                    }
                }
                std::cerr << "[S81-DIALOG-ITEMS] materialized "
                          << win->items.size() << "/" << n_items
                          << " items for builder obj=" << args[0].object_id
                          << std::endl;
            }
        }
    }

    // ────────────────────────────────────────────────────────────────────
    // R-NEW-339 companion law: Context.getSystemService(Class) must resolve
    // in BOTH dispatch layers. The bridge_to_api copy is only reached via
    // the class-miss fallthrough; when the receiver's runtime class IS in
    // class_info_index_ (ContextWrapper/ContextThemeWrapper-family or any
    // app Context subclass) the dex-body lookup fails differently and the
    // bridge block can be bypassed — the call then answered null, and
    // Compose's AndroidComposeView ctor checkNotNull
    // (getSystemService(AutofillManager::class.java)) threw
    // "Required value was null." on the second fetch (first fetch resolved,
    // producing exactly ONE [EXP093-SVC] autofill line — the dooz marker).
    // Same registry, two views — identical to the bridge_to_api block.
    // ────────────────────────────────────────────────────────────────────
    // F-NEW-197 CONFIG-CONTEXT dual-view law (companion to R-NEW-339):
    // Context.createConfigurationContext(Configuration) must NEVER answer
    // null for ANY context-family receiver. AOSP ContextImpl returns a
    // fresh Context sharing the base's resources identity with the override
    // configuration applied. Live evidence (opencalculator vc53):
    //   Lg/m (AppCompatActivity).attachBaseContext pc=180
    //     createConfigurationContext → pc=184 .getResources() NPE (f141),
    //   Ll/c (ContextThemeWrapper).getResources pc=39 → pc=43 .getResources()
    //     NPE on the unimplemented answer. The appcompat day-night attach
    //     chain aborts → activity never builds its ViewTree → white frame.
    // Identity: one FRESH context object per call (AOSP ContextImpl law —
    // never a shared singleton); the S110 base-context map records the
    // receiver so downstream getBaseContext/getResources resolve.
    // ────────────────────────────────────────────────────────────────────
    if (method == "createConfigurationContext") {
        uint32_t base_recv =
            (!args.empty() && args[0].type == DalvikType::OBJECT_REF)
                ? args[0].object_id
                : 0;
        if (base_recv != 0) {
            uint32_t derived = heap_.allocate("Landroid/content/Context;",
                                              pc_, 0);
            uint32_t override_cfg = 0;
            if (args.size() >= 2 &&
                args[1].type == DalvikType::OBJECT_REF)
                override_cfg = args[1].object_id;
            if (auto* ash =
                    shadow_registry_->find_as<framework::ActivityShadow>())
                ash->record_config_context(derived, base_recv, override_cfg);
            result = DalvikValue::make_object(derived,
                                              "Landroid/content/Context;");
            status = ApiCallTrace::Status::IMPLEMENTED;
            return true;
        }
    }
    if (method == "getSystemService") {
        // R-NEW-540 guard fix (CONT-36, site A): substring-only guard
        // missed Application/Service receivers whose runtime class lacks
        // the literal "Context"/"Activity" (the S85-FIX law shape — AOSP:
        // every Context-family instance answers getSystemService). chompass
        // live: receiver = the app Application class → the "jobscheduler"
        // map entry never consulted → null → SystemJobScheduler death.
        bool gss_ctx540 =
            class_name.find("Context") != std::string::npos ||
            class_name.find("Activity") != std::string::npos;
        if (!gss_ctx540) {
            static const char* const kGssRoots540[] = {
                "Landroid/content/Context;",
                "Landroid/app/Activity;",
                "Landroid/app/Application;",
                "Landroid/app/Service;",
                "Landroid/view/View;",
                "Landroid/view/ViewGroup;"};
            for (const char* root : kGssRoots540) {
                if (is_subclass_of(class_name, root)) {
                    gss_ctx540 = true;
                    break;
                }
            }
        }
        if (gss_ctx540) {
        std::string svc_name339;
        if (args.size() >= 2 && args[1].type == DalvikType::STRING_REF) {
            svc_name339 = args[1].string_val;
        } else if (args.size() >= 2 && args[1].type == DalvikType::CLASS_REF) {
            static const miniandroid::dalvik::KvPair t_svc_cls339[] = {
    {"Landroid/view/WindowManager;", "window"},
    {"Landroid/view/LayoutInflater;", "layout_inflater"},
    {"Landroid/app/ActivityManager;", "activity"},
    {"Landroid/view/inputmethod/InputMethodManager;", "input_method"},
    {"Landroid/app/NotificationManager;", "notification"},
    {"Landroid/app/AlarmManager;", "alarm"},
    {"Landroid/media/AudioManager;", "audio"},
    {"Landroid/content/ClipboardManager;", "clipboard"},
    {"Landroid/net/ConnectivityManager;", "connectivity"},
    {"Landroid/app/UiModeManager;", "uimode"},
    {"Landroid/app/SearchManager;", "search"},
    {"Landroid/app/KeyguardManager;", "keyguard"},
    {"Landroid/location/LocationManager;", "location"},
    {"Landroid/accounts/AccountManager;", "account"},
    {"Landroid/os/PowerManager;", "power"},
    {"Landroid/os/Vibrator;", "vibrator"},
    {"Landroid/hardware/SensorManager;", "sensor"},
    {"Landroid/hardware/display/DisplayManager;", "display"},
    {"Landroid/view/accessibility/AccessibilityManager;", "accessibility"},
    {"Landroid/view/autofill/AutofillManager;", "autofill"},
    // S83: input service — boxcars EbitenView.initialize registers an input
    // device listener at onCreate; a null InputManager NPE'd APP-BOUNDARY.
    {"Landroid/hardware/input/InputManager;", "input"},
    // R-NEW-540 (CONT-36): JobScheduler — AOSP Context.JOB_SCHEDULER_SERVICE
    // ("jobscheduler", API 21+, never-null on a live context). Live face
    // (chompass): androidx.work SystemJobScheduler.<init> first insn
    // JobSchedulerExtKt.getWmJobScheduler(ctx) →
    // getSystemService(JobScheduler::class.java) → NULL → the ctor NPE'd
    // at pc=0x0 and the whole WorkManager bootstrap died.
    {"Landroid/app/JobScheduler;", "jobscheduler"},
    // F-NEW-639 (S235-1): the AOSP TELEPHONY_SERVICE spelling ("phone") —
    // getSystemService(TelephonyManager.class) resolves through it.
    {"Landroid/telephony/TelephonyManager;", "phone"},
};
            const char* cn = kv_table_find(t_svc_cls339,
                    sizeof(t_svc_cls339) / sizeof(t_svc_cls339[0]),
                    args[1].class_desc);
            if (cn) svc_name339 = cn;
        }
        static const miniandroid::dalvik::KvPair t_svc_map339[] = {
    {"window", "Landroid/view/WindowManager;"},
    {"layout_inflater", "Landroid/view/LayoutInflater;"},
    {"activity", "Landroid/app/ActivityManager;"},
    {"input_method", "Landroid/view/inputmethod/InputMethodManager;"},
    {"notification", "Landroid/app/NotificationManager;"},
    {"alarm", "Landroid/app/AlarmManager;"},
    {"audio", "Landroid/media/AudioManager;"},
    {"clipboard", "Landroid/content/ClipboardManager;"},
    {"connectivity", "Landroid/net/ConnectivityManager;"},
    {"uimode", "Landroid/app/UiModeManager;"},
    {"search", "Landroid/app/SearchManager;"},
    {"keyguard", "Landroid/app/KeyguardManager;"},
    {"location", "Landroid/location/LocationManager;"},
    {"account", "Landroid/accounts/AccountManager;"},
    {"power", "Landroid/os/PowerManager;"},
    {"vibrator", "Landroid/os/Vibrator;"},
    {"sensor", "Landroid/hardware/SensorManager;"},
    {"display", "Landroid/hardware/display/DisplayManager;"},
    {"accessibility", "Landroid/view/accessibility/AccessibilityManager;"},
    {"autofill", "Landroid/view/autofill/AutofillManager;"},
    // F-NEW-639 (S235-1): the AOSP TELEPHONY_SERVICE spelling ("phone").
    {"phone", "Landroid/telephony/TelephonyManager;"},
    // S83: input service (see the class-table note above).
    {"input", "Landroid/hardware/input/InputManager;"},
    // R-NEW-540 (CONT-36): jobscheduler (see the class-table note above).
    {"jobscheduler", "Landroid/app/JobScheduler;"},
};
        const char* sv = kv_table_find(t_svc_map339,
                sizeof(t_svc_map339) / sizeof(t_svc_map339[0]),
                svc_name339);
        if (sv) {
            result = get_or_create_singleton(sv);
            status = ApiCallTrace::Status::IMPLEMENTED;
            std::cerr << "[R339-SVC] getSystemService(\"" << svc_name339
                      << "\") → " << sv
                      << " (shadow layer, caller=" << current_class_ << "."
                      << current_method_ << ")" << std::endl;
            return true;
        }
        }
    }

    // [S34-RFC] who cancels the frame callback?
    if (method == "removeFrameCallback" &&
        class_name == "Landroid/view/Choreographer;") {
        static thread_local uint64_t rfc_n = 0;
        ++rfc_n;
        if (rfc_n <= 6) {
            std::cerr << "[S34-RFC] removeFrameCallback #" << rfc_n
                      << " d=" << recursion_depth_ << " chain:";
            auto frames = call_stack_.snapshot_top_first();
            for (size_t fi = 0; fi < frames.size() && fi < 5; ++fi)
                std::cerr << " <" << frames[fi].first << "."
                          << frames[fi].second << ">";
            std::cerr << std::endl;
        }
    }

    // EXP-071 Phase 8: Generic static-method shadow dispatch fix.
    //
    // For static methods like AndroidUtilities.runOnUIThread(Runnable),
    // args[0] is the FIRST ARGUMENT (the Runnable), not `this`. The
    // previous code used args[0].class_desc as ctx.class_name, which
    // made HandlerShadow's "Lorg/telegram/messenger/AndroidUtilities;"
    // branch fail to match (because args[0].class_desc was the Runnable's
    // class, not "AndroidUtilities"). As a result, runOnUIThread was a
    // silent no-op, the runnable was never enqueued, and the entire
    // async callback chain (Lambda0 → lambda$onConfirm$1 → Lambda1 →
    // lambda$onConfirm$0 → onNextPressed → auth.sendCode) was broken.
    //
    // Fix: try dispatch with the DECLARED class_name FIRST. If the shadow
    // returns not_handled, retry with args[0].class_desc (the runtime
    // class of `this` for instance methods). This works for both:
    //   * Static calls  — class_name="Lorg/telegram/messenger/AndroidUtilities;"
    //   * Instance calls — class_name="Landroid/view/View;" (or args[0].class_desc
    //     for the actual runtime subclass like IntroActivity$4).
    auto build_ctx = [&](const std::string& chosen_class) {
        framework::CallContext ctx;
        ctx.caller = current_class_ + "." + current_method_ + " pc=" +
                     std::to_string(pc_);
        ctx.class_name = chosen_class;
        ctx.method = method;
        // EXP-071 Phase 8: For INSTANCE methods, args[0] is `this` (the receiver)
        // and the remaining args are the parameters. We shift them so that
        // ctx.args[0] is the first PARAMETER (not `this`), and set
        // ctx.receiver_id/receiver_class for `this`.
        //
        // For STATIC methods (current_invoke_is_static_), args[0] is already
        // the first PARAMETER — there's no `this`. We put ALL args in ctx.args
        // without shifting.
        //
        // Without this distinction, static calls like
        // AndroidUtilities.runOnUIThread(Runnable, long) would have their
        // Runnable stolen as `this` and never reach HandlerShadow's enqueue
        // (which expects ctx.args[0] to be the Runnable).
        if (!current_invoke_is_static_ &&
            !args.empty() && args[0].type == DalvikType::OBJECT_REF) {
            ctx.has_receiver = true;
            ctx.receiver_id = args[0].object_id;
            ctx.receiver_class = args[0].class_desc;
            for (size_t i = 1; i < args.size(); i++) {
                ctx.args.push_back(dalvik_value_to_arg(args[i]));
            }
        } else {
            for (const auto& a : args) {
                ctx.args.push_back(dalvik_value_to_arg(a));
            }
        }
        return ctx;
    };

    // Pass 1: try with the declared class_name.
    // ────────────────────────────────────────────────────────────────────
    // CONT-21 / #384 (F-NEW-272) — Thread UncaughtExceptionHandler laws.
    // AOSP Thread law (libcore Thread + AOSP RuntimeInit):
    //   Thread.getUncaughtExceptionHandler()  → the per-thread handler if
    //     set, ELSE Thread.defaultUncaughtExceptionHandler — and on a live
    //     ART runtime the default is NEVER null (RuntimeInit installs
    //     RuntimeInit$KillApplicationHandler at process start).
    //   Thread.setDefaultUncaughtExceptionHandler(h) (static) → installs h.
    //   Thread.getDefaultUncaughtExceptionHandler() (static) → the default.
    //   KillApplicationHandler.uncaughtException(t, e) → logs FATAL
    //     EXCEPTION (process-death modeling stays owned by the runtime's
    //     F-016 exception-honesty machinery — this call itself completes).
    // Runtime evidence (run/cont21/after/dooz_r2): kotlinx coroutine
    // machinery (Llo;.K pc=0x52) runs currentThread()
    // .getUncaughtExceptionHandler().uncaughtException(t,e) whenever a
    // coroutine scope fails; the prior no-op answered null → interface
    // invoke NPE → APP BOUNDARY (the registered CONT-20 next root).
    // Static-vs-instance disambiguation by arg shape (statics carry no
    // receiver): get = 0 args → static; set = 1 arg → static.
    // ────────────────────────────────────────────────────────────────────
    if ((class_name == "Ljava/lang/Thread;" || is_thread_receiver(class_name)) &&
        (method == "getUncaughtExceptionHandler" ||
         method == "setUncaughtExceptionHandler")) {
        auto ensure_default_handler = [&]() -> DalvikValue {
            if (default_uncaught_handler_.object_id != 0 &&
                heap_.has_object(default_uncaught_handler_.object_id))
                return default_uncaught_handler_;
            uint32_t hid = heap_.allocate(
                "Lcom/android/internal/os/RuntimeInit$KillApplicationHandler;",
                pc_, call_stack_.empty() ? 0 : call_stack_.top().frame_id);
            default_uncaught_handler_ = DalvikValue::make_object(
                hid,
                "Lcom/android/internal/os/RuntimeInit$KillApplicationHandler;");
            return default_uncaught_handler_;
        };
        if (method == "getUncaughtExceptionHandler") {
            if (args.empty()) {
                // static Thread.getDefaultUncaughtExceptionHandler()
                result = ensure_default_handler();
            } else {
                // instance: per-thread handler, else the default (AOSP law).
                uint32_t t_oid = args[0].type == DalvikType::OBJECT_REF
                                     ? args[0].object_id
                                     : 0;
                auto it = thread_uncaught_handlers_.find(t_oid);
                if (it != thread_uncaught_handlers_.end() &&
                    it->second.object_id != 0)
                    result = it->second;
                else
                    result = ensure_default_handler();
            }
            status = ApiCallTrace::Status::IMPLEMENTED;
            return true;
        }
        // setUncaughtExceptionHandler: 1 arg (static handler) vs
        // 2 args (instance receiver + handler).
        DalvikValue hv = args.size() >= 2 ? args[1] : args[0];
        if (hv.type == DalvikType::OBJECT_REF && hv.object_id != 0) {
            if (args.size() >= 2) {
                thread_uncaught_handlers_[args[0].object_id] = hv;
            } else {
                default_uncaught_handler_ = hv;
            }
        }
        result = DalvikValue::make_void();
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }
    if (method == "uncaughtException" &&
        class_name.find("KillApplicationHandler") != std::string::npos) {
        // AOSP RuntimeInit$KillApplicationHandler: log the fatal exception;
        // the process-death face is modeled by the runtime's existing
        // exception-honesty machinery, so the call itself completes.
        static thread_local uint64_t ueh_log = 0;
        if (ueh_log < 12) {
            ++ueh_log;
            std::cerr << "[UEH-DEFAULT] FATAL EXCEPTION (KillApplicationHandler)"
                      << " thread="
                      << (args.empty() ? 0 : args[0].object_id)
                      << " caller=" << current_class_ << "."
                      << current_method_ << std::endl;
        }
        result = DalvikValue::make_void();
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }
    // ────────────────────────────────────────────────────────────────────
    // F-NEW-166 (S134 wave 3): AOSP ContextWrapper BASE-CONTEXT law —
    // served for EVERY ContextWrapper-family receiver, not only Activities.
    // AOSP: getBaseContext()/attachBaseContext() are ContextWrapper
    // CONTRACT methods (mBase set during attach; never null after), and
    // ContextWrapper.<init>(Context base) DELEGATES to attachBaseContext.
    // The S110 law implementation lives inside ActivityShadow::dispatch,
    // but ActivityShadow::handles_class matches only Activity-shaped
    // names — a plain app-level ContextWrapper descendant (WhatsApp
    // LX/00J; extends ContextWrapper) never routed there:
    //   <init>(base)      → REC-MISS → ctor base argument DROPPED
    //   getBaseContext    → REC-MISS → stub null
    //   → the app's own Intrinsics check (LX/00i;.A06 → A0F) threw
    //     "INVOKE_RETURN must not be null" during attachBaseContext →
    //     Application.onCreate never ran → no window → WHITE screen.
    // Route the three shapes here for Context-family receivers,
    // delegating to the SAME law implementation (one state owner:
    // ActivityShadow base_contexts_/application fallbacks — never null).
    // Evidence: s134 WhatsApp run, [REC-MISS] ContextWrapper.<init> +
    // ContextWrapper.getBaseContext + THROWABLE-STACK chain
    // 004.attachBaseContext → 00J.<init> → 009.<init> → A06 → A0F.
    // ────────────────────────────────────────────────────────────────────
    if ((method == "getBaseContext" || method == "attachBaseContext" ||
         (method == "<init>" && !args.empty())) &&
        (class_name.find("ContextWrapper") != std::string::npos ||
         class_name.find("ContextThemeWrapper") != std::string::npos ||
         class_name.find("Context;") != std::string::npos)) {
        if (auto* as = shadow_registry_->find_as<framework::ActivityShadow>()) {
            framework::CallContext ctx166 = build_ctx(class_name);
            // AOSP ctor law: ContextWrapper.<init>(base) ==
            // attachBaseContext(base) — route through the same law.
            if (method == "<init>")
                ctx166.method = "attachBaseContext";
            auto cr166 = as->dispatch(ctx166);
            if (cr166.handled) {
                switch (cr166.status) {
                    case framework::ApiCallStatus::IMPLEMENTED:
                        status = ApiCallTrace::Status::IMPLEMENTED; break;
                    case framework::ApiCallStatus::STUBBED:
                        status = ApiCallTrace::Status::STUBBED; break;
                    default:
                        status = ApiCallTrace::Status::STUBBED; break;
                }
                result = call_result_to_dalvik(cr166);
                std::cerr << "[F166-BASECTX] " << method << " served for "
                          << class_name << " (receiver="
                          << ((!args.empty() &&
                               args[0].type == DalvikType::OBJECT_REF)
                                  ? args[0].object_id : 0u) << ")"
                          << std::endl;
                return true;
            }
        }
    }

    auto cr = shadow_registry_->dispatch(build_ctx(class_name));
    // F-NEW-267 (CONT-64 W1) ANSWER-VALUE probe — env-gated, bounded. The
    // compose relayout reads the view geometry through this bridge during
    // the tap dispatch; the decode needs the ANSWERED VALUES (the walk
    // consumes them for the root measure constraints). Print the geometry
    // getters' int answers when MINIANDROID_TOUCH_WINDOW_TRACE is on.
    if (touch_dispatch_active_ && cr.handled &&
        (class_name == "Landroid/view/View;" || class_name == "Lt4;" ||
         class_name == "Landroid/view/ViewGroup;")) {
        static thread_local uint64_t av_n = 0;
        if (av_n++ < 120 &&
            (method == "getWidth" || method == "getHeight" ||
             method == "getMeasuredWidth" || method == "getMeasuredHeight" ||
             method == "getLeft" || method == "getTop" ||
             method == "getRight" || method == "getBottom" ||
             method == "isLaidOut" || method == "isAttachedToWindow"))
            std::cerr << "[TOUCHWIN-ANSWER] " << class_name << "." << method
                      << " -> "
                      << (method == "isLaidOut" ||
                          method == "isAttachedToWindow"
                              ? std::to_string(cr.bool_val ? 1 : 0)
                              : std::to_string(cr.int_val))
                      << " caller=" << current_class_ << "."
                      << current_method_ << std::endl;
    }
    // M3-DIAG (temporary): why do tick-path setText calls miss the shadow?
    static const bool m3sd = std::getenv("MINIANDROID_M3_SHADOW_DIAG") != nullptr;
    if (m3sd && method.find("setText") != std::string::npos) {
        static thread_local uint64_t sd_log = 0;
        if (sd_log < 200) {
            sd_log++;
            fprintf(stderr,
                    "[M3-SHADOW] %s.%s pass1 handled=%d class=%s recv=%u/%s "
                    "args=%zu arg0=%d\n",
                    class_name.c_str(), method.c_str(), (int)cr.handled,
                    class_name.c_str(),
                    (!args.empty() && args[0].type == DalvikType::OBJECT_REF)
                        ? args[0].object_id : 0u,
                    (!args.empty() && args[0].type == DalvikType::OBJECT_REF)
                        ? args[0].class_desc.c_str() : "-",
                    args.size(),
                    args.empty() ? -1 : (int)args[0].type);
        }
    }
    // EXP-071 Phase 8 debug — log dispatch attempts for runOnUIThread.
    if (method == "runOnUIThread" || method == "executeOnUIThread") {
        std::cerr << "[EXP071-SHADOW-DISPATCH] pass1 class_name=" << class_name
                  << " method=" << method
                  << " handled=" << (cr.handled ? "YES" : "NO")
                  << std::endl;
    }
    if (cr.handled) {
        // ── F-NEW-259g-a: SHADOW EXCEPTION CHANNEL (conversion) ──────────
        // A shadow-detected JDK/ART contract violation (e.g. ArrayList.get
        // range law) becomes a deferred throw at THIS call site — the same
        // semantics as the engine-side F-141/F-036 throw_deferred laws.
        // ART: the exception surfaces at the invoking frame's call site;
        // the catch-handler redirect resolves at the interpreter boundary.
        if (cr.is_exc) {
            throw_deferred(cr.exc_class, cr.exc_msg, "SHADOW-EXC");
            result = DalvikValue::make_void();
            return true;
        }
        switch (cr.status) {
            case framework::ApiCallStatus::IMPLEMENTED:
                status = ApiCallTrace::Status::IMPLEMENTED; break;
            case framework::ApiCallStatus::STUBBED:
                status = ApiCallTrace::Status::STUBBED; break;
            default:
                status = ApiCallTrace::Status::STUBBED; break;
        }
        result = call_result_to_dalvik(cr);
        // CONT-159: pass-1 answer channel (same law as the pass-2 diag —
        // GLES20/GL statics answer here; the pass-2 diag never sees them).
        static thread_local const bool ans1_on =
            diag_env("MINIANDROID_SHADOW_ANSWER_TRACE");
        if (ans1_on) {
            static thread_local uint64_t ans1_n = 0;
            if (ans1_n < 300) {
                ++ans1_n;
                std::cerr << "[SHADOW-ANSWER-1] " << class_name << "."
                          << method << " ret_type="
                          << static_cast<int>(result.type)
                          << " int=" << result.int_val
                          << " obj=" << result.object_id
                          << " caller=" << current_class_ << "."
                          << current_method_ << std::endl;
            }
        }
        return true;
    }

    // Pass 2: try with args[0].class_desc (runtime class of `this`).
    // M3 F-020 ROOT FIX (F2 law extension): constructors are DIRECT
    // invocation targets resolved on the DECLARING class (ART ClassLinker:
    // no virtual constructor dispatch). The runtime-class retry is a
    // virtual-dispatch emulation — it must never route <init>/<clinit>,
    // or an app-named subclass of a framework class (R8 minted
    // `LF/d; extends AtomicInteger`) gets claimed by ViewShadow's
    // user-class catch-all and the real constructor argument is dropped.
    if (method == "<init>" || method == "<clinit>") {
        return false;
    }
    if (!args.empty() && args[0].type == DalvikType::OBJECT_REF &&
        !args[0].class_desc.empty() && args[0].class_desc != class_name) {
        cr = shadow_registry_->dispatch(build_ctx(args[0].class_desc));
        if (cr.handled) {
            // F-NEW-259g-a: shadow exception channel (pass-2 conversion).
            if (cr.is_exc) {
                throw_deferred(cr.exc_class, cr.exc_msg, "SHADOW-EXC");
                result = DalvikValue::make_void();
                return true;
            }
            switch (cr.status) {
                case framework::ApiCallStatus::IMPLEMENTED:
                    status = ApiCallTrace::Status::IMPLEMENTED; break;
                case framework::ApiCallStatus::STUBBED:
                    status = ApiCallTrace::Status::STUBBED; break;
                default:
                    status = ApiCallTrace::Status::STUBBED; break;
            }
            result = call_result_to_dalvik(cr);
            // CONT-159 (F-NEW-503 decode diag, env-gated): the shadow
            // answer channel — which (class, method) answered and with what
            // value shape. Pins int-return fidelity end-to-end.
            static thread_local const bool ans_on =
                diag_env("MINIANDROID_SHADOW_ANSWER_TRACE");
            if (ans_on) {
                static thread_local uint64_t ans_n = 0;
                if (ans_n < 300) {
                    ++ans_n;
                    std::cerr << "[SHADOW-ANSWER] " << class_name << "."
                              << method << " status="
                              << (status == ApiCallTrace::Status::IMPLEMENTED
                                      ? "IMPL"
                                      : "STUB")
                              << " ret_type=" << static_cast<int>(result.type)
                              << " int=" << result.int_val
                              << " obj=" << result.object_id
                              << " caller=" << current_class_ << "."
                              << current_method_ << std::endl;
                }
            }
            return true;
        }
    }

    // CAMPAIGN 013 (B4, §8): hierarchy-aware shadow dispatch.
    // Root cause: shadows claim framework classes by NAME. App classes whose
    // names match no claim (ChessClock, muellerma StopWatch, ...) never
    // reached ActivityShadow — setContentView/findViewById/getWindow became
    // SILENT no-ops and the app kept the synthetic default screen. The old
    // workarounds grew a hand-maintained list of app class names inside
    // ActivityShadow::handles_class — the per-app special-casing this
    // campaign forbids.
    // General fix (mirrors real Android virtual dispatch): walk the DEX
    // superclass chain of the receiver and retry the shadow registry with
    // each ancestor. ChessClock → android/app/Activity → ActivityShadow
    // handles setContentView exactly as for any other Activity subclass.
    //
    // MASTER CAMPAIGN FIX (F2 constructor-direct law): constructors are
    // DIRECT invocation targets resolved on the DECLARING class (ART
    // ClassLinker: there is no virtual constructor dispatch). The ancestor
    // walk emulates VIRTUAL dispatch only — it must never route <init>/
    // <clinit> to a shadow of an ANCESTOR class. Evidence: with <init>
    // walkable, ViewShadow's user-class catch-all claimed
    // Lfr/neamar/kiss/db/DBHelper;.<init> (an R8 merge target with 24
    // merged androidx/app subclasses) and swallowed real constructors.
    if (method == "<init>" || method == "<clinit>") {
        return false;
    }
    {
        std::string cur;
        if (!args.empty() && args[0].type == DalvikType::OBJECT_REF &&
            !args[0].class_desc.empty()) {
            cur = args[0].class_desc;
            // F-NEW-456 (CONT-112): ART virtual dispatch resolves on the
            // receiver's RUNTIME class, not the static type of the reference.
            // A Context-typed variable holding the Activity (every
            // (Context, AttributeSet) view ctor passes the activity as
            // Context — chess appcompat callers passed `this`, so the static
            // desc was already the runtime class; minimal probes and any
            // framework code holding Context lose the walk here). The heap
            // object knows the REAL class — start the walk from it.
            if (args[0].object_id != 0) {
                std::string rt_cls;
                if (heap_.get_object_class(args[0].object_id, rt_cls) &&
                    !rt_cls.empty()) {
                    cur = rt_cls;
                }
            }
        } else {
            cur = class_name;
        }
        int guard = 0;
        while (!cur.empty() && guard++ < 10) {
            auto sup_it = class_to_superclass_.find(cur);
            if (sup_it == class_to_superclass_.end()) break;
            const std::string sup = sup_it->second;
            if (sup.empty() || sup == cur) break;
            auto cr3 = shadow_registry_->dispatch(build_ctx(sup));
            if (cr3.handled) {
                std::cerr << "[C013-HIER] " << method << " dispatched via superclass chain: "
                          << cur << " -> " << sup
                          << " (declared=" << class_name
                          << " receiver=" << (!args.empty() &&
                             args[0].type == DalvikType::OBJECT_REF
                             ? std::string(args[0].class_desc) : std::string("-"))
                          << ")" << std::endl;
                // F-NEW-259g-a: shadow exception channel (hierarchy walk).
                if (cr3.is_exc) {
                    throw_deferred(cr3.exc_class, cr3.exc_msg, "SHADOW-EXC");
                    result = DalvikValue::make_void();
                    return true;
                }
                switch (cr3.status) {
                    case framework::ApiCallStatus::IMPLEMENTED:
                        status = ApiCallTrace::Status::IMPLEMENTED; break;
                    default:
                        status = ApiCallTrace::Status::STUBBED; break;
                }
                result = call_result_to_dalvik(cr3);
                return true;
            }
            cur = sup;
        }
    }
    return false;
}

// ────────────────────────────────────────────────────────────────────
// VISUAL-CAMPAIGN (EXT-01 gate G25): seed the virtual device identity.
// AOSP law: Build.VERSION.SDK_INT / Build.VERSION.RELEASE / Build.* and
// Settings.Secure.ANDROID_ID are FRAMEWORK-provided statics — a real
// device firmware defines them before any app code runs. MiniAndroid's
// honest virtual identity is Android 15 (SDK_INT=35, RELEASE="15") as of
// F-NEW-473 (CONT-150): the corpus's compose-ui 1.7 apps draw their
// content ONLY on a SDK>=35 device — AndroidComposeView.dispatchDraw's
// content path is gated by a private static predicate p() compiled to
// `SDK_INT >= 35` (byte-verified: Lt4;.p @dooz v23; on SDK<35 the recorded
// GraphicsLayer pipeline (RenderNode) is the only content path, and this
// software runtime implements the SDK>=35 dispatchDraw law instead).
// Insert-if-absent: a real app <clinit> always wins over a seed.
// Evidence: EXT-01 baseline (HelloWorldSelfAware) — AndroidInfo.getId()
// read SDK_INT=0, took the pre-O Build.SERIAL branch and rendered
// "i'm null"; with this seed it takes the Settings.Secure ANDROID_ID
// branch exactly like any Android 8+ device.
// ────────────────────────────────────────────────────────────────────
void DalvikExecutionEngine::seed_framework_device_statics() {
    auto seed = [this](const std::string& key, const DalvikValue& v) {
        static_field_storage_.emplace(key, v);  // insert-if-absent
        // R500 ROOT-REFLECTION-FIELD-IDENTITY: a framework-seeded static IS
        // a declared public field for the reflection surface (getField/
        // getDeclaredField consumers — real Android answers them from the
        // framework metadata the engine models with this seed registry).
        framework_declared_fields_.insert(key);
    };
    seed("Landroid/os/Build$VERSION;.SDK_INT", DalvikValue::make_int(35));
    seed("Landroid/os/Build$VERSION;.RELEASE", DalvikValue::make_string("15", 0));
    seed("Landroid/os/Build$VERSION;.CODENAME", DalvikValue::make_string("REL", 0));
    seed("Landroid/os/Build$VERSION;.SDK", DalvikValue::make_string("35", 0));
    seed("Landroid/os/Build$VERSION;.INCREMENTAL", DalvikValue::make_string("miniandroid.20260905", 0));
    seed("Landroid/os/Build;.MODEL", DalvikValue::make_string("MiniAndroid", 0));
    seed("Landroid/os/Build;.MANUFACTURER", DalvikValue::make_string("MiniAndroid", 0));
    seed("Landroid/os/Build;.BRAND", DalvikValue::make_string("MiniAndroid", 0));
    seed("Landroid/os/Build;.DEVICE", DalvikValue::make_string("miniandroid", 0));
    seed("Landroid/os/Build;.PRODUCT", DalvikValue::make_string("miniandroid", 0));
    seed("Landroid/os/Build;.HARDWARE", DalvikValue::make_string("miniandroid", 0));
    seed("Landroid/os/Build;.FINGERPRINT", DalvikValue::make_string("MiniAndroid/miniandroid/miniandroid:15/MINI.20260905/0:userdebug/test-keys", 0));
    seed("Landroid/os/Build;.SERIAL", DalvikValue::make_string("miniandroid", 0));
    // F-NEW-190 (FINAL CAMPAIGN PHASE 4 — device/context identity, AOSP
    // Build ABI law): Build.SUPPORTED_ABIS / SUPPORTED_64_BIT_ABIS /
    // SUPPORTED_32_BIT_ABIS / CPU_ABI / CPU_ABI2 are framework statics fed
    // from ro.product.cpu.abilist on a real device — NEVER null/empty on
    // any Android build. The runtime models an arm64 android-35 device
    // (SDK_INT=35 + fingerprint above); the list follows the AOSP
    // emulator-equivalent arm64 primary order. Measured face (WhatsApp
    // LX/0Cz;.A01 ×3): the app's own ABI utility threw ISE "No supported
    // ABIs found on this device" — the absent static made its fallback
    // classify the device as unsupported.
    {
        auto seed_array = [this, &seed](const std::string& key,
                                        const std::vector<std::string>& items) {
            uint32_t arr_id = heap_.allocate("[Ljava/lang/String;", 0, 0);
            DalvikValue len = DalvikValue::make_int((int32_t)items.size());
            heap_.set_object_field(arr_id, "__array_length__", len);
            heap_.set_object_field(arr_id, "__new_array_length__", len);
            heap_.set_object_field(arr_id, "__element_type__",
                DalvikValue::make_string("[Ljava/lang/String;", 0));
            for (size_t i = 0; i < items.size(); ++i)
                heap_.set_object_field(arr_id, "array[" + std::to_string(i) + "]",
                                       DalvikValue::make_string(items[i], 0));
            DalvikValue av;
            av.type = DalvikType::OBJECT_REF;
            av.object_id = arr_id;
            av.class_desc = "[Ljava/lang/String;";
            seed(key, av);
        };
        // ── #375 §5 CAPABILITY-HONESTY LAW (FALSE_ADVERTISED_MATRIX
        // FA-01): SUPPORTED_ABIS must not advertise non-executable ABIs
        // unless binary translation exists (AOSP ro.product.cpu.abilist is
        // the device's EXECUTABLE abi list — the app-install ABI matcher
        // and every app-side ABI gate read it as such). The previous seed
        // ([arm64-v8a, armeabi-v7a, armeabi] — an arm64 device persona)
        // advertised ARM native execution that the x86_64 host profile
        // does not have. HONEST seed = the host-executable ABI only
        // (executable_abis=[x86_64] in ENVIRONMENT_PROFILE ENV-005);
        // CPU_ABI2 = "" (AOSP: deprecated, commonly empty on API 21+).
        // App-visible behavior for arm-only APKs is UNCHANGED: the install
        // ABI law still extracts their ARM lib tree for provenance and a
        // load attempt reports the real dlopen refusal (NAT-05 shape).
        // Non-empty list keeps the F-NEW-190 face green (WhatsApp's ABI
        // utility only requires a non-empty list).
        seed_array("Landroid/os/Build;.SUPPORTED_ABIS", {"x86_64"});
        seed_array("Landroid/os/Build;.SUPPORTED_64_BIT_ABIS", {"x86_64"});
        seed_array("Landroid/os/Build;.SUPPORTED_32_BIT_ABIS", {});
        seed("Landroid/os/Build;.CPU_ABI",
             DalvikValue::make_string("x86_64", 0));
        seed("Landroid/os/Build;.CPU_ABI2",
             DalvikValue::make_string("", 0));
    }
    // AOSP: Settings.Secure.ANDROID_ID == the column name "android_id".
    seed("Landroid/provider/Settings$Secure;.ANDROID_ID", DalvikValue::make_string("android_id", 0));
    // Deterministic virtual-device ANDROID_ID (16 lowercase hex chars,
    // same shape as a real device; constant => Rule 12 determinism).
    resource_string_values_["android_id"] = "6f1c3a9d2e5b4780";
    // ────────────────────────────────────────────────────────────────────
    // CONT-366 ROOT-B — android.view.WindowInsets.CONSUMED (API 30+).
    // AOSP (WindowInsets.java): CONSUMED is a public static final
    // WindowInsets — "an empty insets instance where all insets have been
    // consumed". It is NEVER null on any API-30+ device.
    // Runtime evidence (memory v34, first-divergence trace):
    //   ActionBarOverlayLayout.<init> (appcompat decor) →
    //   androidx.core.view.WindowInsetsCompat <clinit> (s0;) → s0$k;
    //   <clinit> → J0.a() == sget WindowInsets.CONSUMED → engine typed-
    //   null → Kotlin/Objects.requireNonNull(x/h.g) NPE "getClass on null
    //   object reference" → s0.v/u unwind → ActionBarOverlayLayout ctor
    //   death → WHITE. Every appcompat-1.6+ decor inflation on the API-30
    //   path touches this static through the same clinit chain.
    // Seed: a REAL heap WindowInsets object (the deterministic empty/
    // consumed instance) — not a string, not a stub. Runtime field
    // identity + requireNonNull both observe an authentic object.
    // ────────────────────────────────────────────────────────────────────
    {
        uint32_t wi_id = heap_.allocate("Landroid/view/WindowInsets;", 0, 0);
        heap_.set_object_field(wi_id, "__insets_consumed__",
                               DalvikValue::make_bool(true));
        DalvikValue wi;
        wi.type = DalvikType::OBJECT_REF;
        wi.object_id = wi_id;
        wi.class_desc = "Landroid/view/WindowInsets;";
        seed("Landroid/view/WindowInsets;.CONSUMED", wi);
    }
    // ────────────────────────────────────────────────────────────────────
    // F-NEW-363 (CONT-67 W1, chessclock 29 first divergence —
    // runtime-proven): Settings.System.DEFAULT_RINGTONE_URI /
    // DEFAULT_NOTIFICATION_URI / DEFAULT_ALARM_ALERT_URI are FRAMEWORK
    // statics — AOSP Settings.java mints them in static init
    // (Uri.withAppendedPath(CONTENT_URI, "ringtone"|"notification_sound"|
    //  "alarm_alert") = content://settings/system/{...}) and they are
    // NEVER null on any device. Evidence: ChessClock.setUpGame reads
    //   sget-object Settings$System.DEFAULT_RINGTONE_URI
    //   invoke-virtual Uri.toString   (pc=321)
    // → engine typed-null → f141 NPE "invoke Uri.toString on a null
    // object reference" → APP-BOUNDARY unwind → the app's entire content
    // never inflates (blank face + 1 uncaught exception).
    // Seed: REAL heap Uri objects carrying uri_raw (the Uri.parse/toString
    // law's canonical field — toString then answers the true URI string,
    // and the SharedPreferences prefAlertSound roundtrip stores a real
    // string, not "null").
    // ────────────────────────────────────────────────────────────────────
    {
        auto seed_uri = [this, &seed](const std::string& key,
                                      const char* raw) {
            uint32_t uri_id = heap_.allocate("Landroid/net/Uri;", 0, 0);
            heap_.set_object_field(uri_id, "uri_raw",
                                   DalvikValue::make_string(raw, 0));
            DalvikValue uv;
            uv.type = DalvikType::OBJECT_REF;
            uv.object_id = uri_id;
            uv.class_desc = "Landroid/net/Uri;";
            seed(key, uv);
        };
        seed_uri("Landroid/provider/Settings$System;.DEFAULT_RINGTONE_URI",
                 "content://settings/system/ringtone");
        seed_uri(
            "Landroid/provider/Settings$System;.DEFAULT_NOTIFICATION_URI",
            "content://settings/system/notification_sound");
        seed_uri(
            "Landroid/provider/Settings$System;.DEFAULT_ALARM_ALERT_URI",
            "content://settings/system/alarm_alert");
    }
}

// ────────────────────────────────────────────────────────────────────
// VISUAL-CAMPAIGN (EXT-01 gate G25): the CYCLE-E Java format engine,
// extracted VERBATIM from the String.format handler (one canonical
// implementation, REUSE-FIRST). Applies
// %[argument_index$][flags][width][.precision]conversion
// with d/i/s/S/f/F/x/X/o/b/B/c/C/e/E/g/G/n, zero/space padding,
// left-align, explicit argument indexes; Java law: null → "null",
// boxed primitives read their "value" field.
// ────────────────────────────────────────────────────────────────────
std::string DalvikExecutionEngine::java_format_walk(
        const std::string& fmt, const std::vector<DalvikValue>& fargs) {
    std::string output;

        // Java-correct stringification of one format argument (§34: null
        // prints as "null", boxed primitives read their "value" field).
        auto elem_to_string = [&](const DalvikValue& v) -> std::string {
            switch (v.type) {
                case DalvikType::STRING_REF: return v.string_val;
                case DalvikType::INT32: return std::to_string(v.int_val);
                case DalvikType::INT64: return std::to_string(v.long_val);
                case DalvikType::FLOAT32: return std::to_string(v.float_val);
                case DalvikType::FLOAT64: return std::to_string(v.double_val);
                case DalvikType::BOOLEAN: return v.bool_val ? "true" : "false";
                case DalvikType::CHAR: return std::string(1, static_cast<char>(v.int_val));
                case DalvikType::OBJECT_REF: {
                    if (v.is_null || v.object_id == 0 || !heap_.has_object(v.object_id))
                        return "null";
                    auto fv = heap_.get_object_field(v.object_id, "value");
                    if (fv.has_value()) {
                        switch (fv->type) {
                            case DalvikType::INT32: return std::to_string(fv->int_val);
                            case DalvikType::INT64: return std::to_string(fv->long_val);
                            case DalvikType::BOOLEAN: return fv->bool_val ? "true" : "false";
                            case DalvikType::CHAR:
                                return std::string(1, static_cast<char>(fv->int_val));
                            case DalvikType::FLOAT32: return std::to_string(fv->float_val);
                            case DalvikType::FLOAT64: return std::to_string(fv->double_val);
                            case DalvikType::STRING_REF: return fv->string_val;
                            default: break;
                        }
                    }
                    // F-NEW-529 (CONT-34, telegram g5/q charset-factory
                    // face): AOSP %s == String.valueOf(obj) == obj.toString()
                    // — the engine answered "object@N", so protobuf/Conscrypt
                    // -style factory ISE messages rendered garbage and the
                    // charset gate killed the chain. Bridge-dispatch the
                    // object's toString (bounded depth; "object@N" stays the
                    // honest last resort for law-less classes).
                    {
                        static thread_local int f529_depth = 0;
                        if (f529_depth < 4) {
                            ++f529_depth;
                            DalvikValue ts_out;
                            ApiCallTrace::Status ts_st =
                                ApiCallTrace::Status::STUBBED;
                            std::vector<DalvikValue> ts_args;
                            ts_args.push_back(v);
                            if (bridge_to_api(v.class_desc, "toString",
                                              ts_args, ts_out, ts_st, 0) &&
                                ts_out.type == DalvikType::STRING_REF) {
                                --f529_depth;
                                return ts_out.string_val;
                            }
                            --f529_depth;
                        }
                    }
                    return "object@" + std::to_string(v.object_id);
                }
                case DalvikType::NULL_REF: return "null";
                default: return "";
            }
        };

        // Java decimal formatting with width/zero-pad/left-align.
        auto pad = [](std::string s, int width, bool zero, bool left) {
            if ((int)s.size() >= width) return s;
            std::string fill((size_t)width - s.size(), zero ? '0' : ' ');
            return left ? (s + fill) : (fill + s);
        };

        size_t arg_idx = 0;
        for (size_t i = 0; i < fmt.size();) {
            if (fmt[i] != '%') { output += fmt[i++]; continue; }
            size_t j = i + 1;
            if (j >= fmt.size()) { output += '%'; break; }
            if (fmt[j] == '%') { output += '%'; i = j + 1; continue; }
            // Optional explicit argument index: %2$s
            size_t spec_start = j;
            int explicit_idx = 0;
            {
                size_t k = j;
                while (k < fmt.size() && isdigit((unsigned char)fmt[k])) k++;
                if (k < fmt.size() && fmt[k] == '$' && k > j) {
                    explicit_idx = std::atoi(fmt.substr(j, k - j).c_str());
                    j = k + 1;
                }
            }
            // Flags
            bool left = false, zero = false, alt = false, plus = false;
            while (j < fmt.size()) {
                char f = fmt[j];
                if (f == '-') left = true;
                else if (f == '0') zero = true;
                else if (f == '#') alt = true;
                else if (f == '+') plus = true;
                else if (f == ' ' || f == ',') { /* accepted, no-op */ }
                else break;
                j++;
            }
            // Width
            int width = 0;
            {
                size_t k = j;
                while (k < fmt.size() && isdigit((unsigned char)fmt[k])) k++;
                if (k > j) { width = std::atoi(fmt.substr(j, k - j).c_str()); j = k; }
            }
            // Precision
            int prec = -1;
            if (j < fmt.size() && fmt[j] == '.') {
                size_t k = j + 1;
                while (k < fmt.size() && isdigit((unsigned char)fmt[k])) k++;
                prec = std::atoi(fmt.substr(j + 1, k - j - 1).c_str());
                j = k;
            }
            if (j >= fmt.size()) { output += fmt.substr(i); break; }
            char conv = fmt[j];

            // Resolve the argument (explicit index is 1-based).
            DalvikValue elem;
            bool have = false;
            if (explicit_idx > 0) {
                size_t pos = (size_t)(explicit_idx - 1);
                if (pos < fargs.size()) { elem = fargs[pos]; have = true; }
            } else {
                if (arg_idx < fargs.size()) { elem = fargs[arg_idx]; have = true; }
                arg_idx++;
            }
            (void)spec_start;

            std::string piece;
            switch (conv) {
                case 'd': case 'i': {
                    int64_t n = 0;
                    if (have) {
                        if (elem.type == DalvikType::INT32) n = elem.int_val;
                        else if (elem.type == DalvikType::INT64) n = elem.long_val;
                        else if (elem.type == DalvikType::OBJECT_REF) {
                            auto fv = heap_.has_object(elem.object_id)
                                          ? heap_.get_object_field(elem.object_id, "value")
                                          : std::nullopt;
                            if (fv.has_value() && fv->type == DalvikType::INT32) n = fv->int_val;
                            else if (fv.has_value() && fv->type == DalvikType::INT64) n = fv->long_val;
                        }
                    }
                    piece = std::to_string(n);
                    if (plus && n >= 0) piece = "+" + piece;
                    piece = pad(piece, width, zero, left);
                    break;
                }
                case 'x': case 'X': {
                    uint64_t n = 0;
                    if (have) {
                        if (elem.type == DalvikType::INT32) n = (uint32_t)elem.int_val;
                        else if (elem.type == DalvikType::INT64) n = (uint64_t)elem.long_val;
                        else if (elem.type == DalvikType::OBJECT_REF) {
                            auto fv = heap_.has_object(elem.object_id)
                                          ? heap_.get_object_field(elem.object_id, "value")
                                          : std::nullopt;
                            if (fv.has_value() && fv->type == DalvikType::INT32)
                                n = (uint32_t)fv->int_val;
                        }
                    }
                    piece = alt ? ("0x" + (conv == 'x'
                                        ? [] (uint64_t v) { std::string s; std::stringstream ss; ss << std::hex << v; s = ss.str(); return s; }(n)
                                        : [] (uint64_t v) { std::string s; std::stringstream ss; ss << std::uppercase << std::hex << v; s = ss.str(); return s; }(n)))
                                : (conv == 'x'
                                        ? [] (uint64_t v) { std::string s; std::stringstream ss; ss << std::hex << v; s = ss.str(); return s; }(n)
                                        : [] (uint64_t v) { std::string s; std::stringstream ss; ss << std::uppercase << std::hex << v; s = ss.str(); return s; }(n));
                    piece = pad(piece, width, zero, left);
                    break;
                }
                case 'f': case 'F': {
                    double d = 0.0;
                    if (have) {
                        if (elem.type == DalvikType::FLOAT32) d = elem.float_val;
                        else if (elem.type == DalvikType::FLOAT64) d = elem.double_val;
                        else if (elem.type == DalvikType::INT32) d = elem.int_val;
                        else if (elem.type == DalvikType::OBJECT_REF) {
                            auto fv = heap_.has_object(elem.object_id)
                                          ? heap_.get_object_field(elem.object_id, "value")
                                          : std::nullopt;
                            if (fv.has_value() && fv->type == DalvikType::FLOAT32) d = fv->float_val;
                            else if (fv.has_value() && fv->type == DalvikType::FLOAT64) d = fv->double_val;
                            else if (fv.has_value() && fv->type == DalvikType::INT32) d = fv->int_val;
                        }
                    }
                    char buf[64];
                    snprintf(buf, sizeof(buf), "%.*f", prec >= 0 ? prec : 6, d);
                    piece = pad(buf, width, zero, left);
                    break;
                }
                case 's': case 'S': {
                    piece = have ? elem_to_string(elem) : "null";
                    if (prec >= 0 && (int)piece.size() > prec) piece = piece.substr(0, prec);
                    if (conv == 'S')
                        std::transform(piece.begin(), piece.end(), piece.begin(), ::toupper);
                    piece = pad(piece, width, /*zero=*/false, left);
                    break;
                }
                case 'b': case 'B': {
                    bool b = have && !(elem.type == DalvikType::BOOLEAN && !elem.bool_val);
                    piece = b ? "true" : "false";
                    if (conv == 'B')
                        std::transform(piece.begin(), piece.end(), piece.begin(), ::toupper);
                    break;
                }
                case 'c': case 'C': {
                    piece = have ? elem_to_string(elem) : "";
                    break;
                }
                case 'e': case 'E': case 'g': case 'G': {
                    double d = 0.0;
                    if (have && elem.type == DalvikType::FLOAT64) d = elem.double_val;
                    else if (have && elem.type == DalvikType::FLOAT32) d = elem.float_val;
                    char buf[64];
                    snprintf(buf, sizeof(buf),
                             conv == 'e' ? "%.*e" : conv == 'E' ? "%.*E" : conv == 'g' ? "%.*g" : "%.*G",
                             prec >= 0 ? prec : 6, d);
                    piece = pad(buf, width, zero, left);
                    break;
                }
                case 'o': {
                    int64_t n = have && elem.type == DalvikType::INT32 ? elem.int_val : 0;
                    char buf[32]; snprintf(buf, sizeof(buf), "%llo", (long long)n);
                    piece = buf;
                    break;
                }
                case 'n': piece = "\n"; break;
                default:
                    // Unknown conversion — Java throws; we keep the spec
                    // verbatim and emit a diagnostic (§34).
                    std::cerr << "UNSUPPORTED_FORMAT_SPECIFICATION spec=%"
                              << conv << std::endl;
                    piece = fmt.substr(i, j - i + 1);
                    break;
            }
            output += piece;
            i = j + 1;
        }
    return output;
}

// R-NEW-345: run one Thread.start() body — the target is either a Runnable
// object (recorded ctor target: Room transaction executor) or the thread
// ITSELF (self-run law for Thread subclasses: kotlinx scheduler Worker,
// Looper threads — they override run() and start with no Runnable). Both
// paths invoke the receiver's REAL DEX run() — AOSP Thread.start()
// virtual-dispatch law, no fake callback.
void DalvikExecutionEngine::run_thread_start_body(uint32_t thread_oid,
                                                  uint32_t target_oid) {
    if (shadow_registry_ == nullptr) return;
    auto* ts_shadow = shadow_registry_->find_as<framework::ThreadShadow>();
    uint32_t run_oid = target_oid ? target_oid : thread_oid;
    // Resolve the receiver's RUNTIME class from the heap (lambda/interface
    // impls and Thread subclasses each live in their own classes).
    std::string rcls = "Ljava/lang/Object;";
    if (heap_.has_object(run_oid)) {
        const auto* robj = heap_.get(run_oid);
        if (robj && !robj->class_descriptor.empty())
            rcls = robj->class_descriptor;
    }
    DalvikValue self = DalvikValue::make_object(run_oid, rcls);
    DalvikValue run_ret;
    DalvikExecutionResult run_res;
    std::vector<DalvikValue> run_args{self};
    // F-110d (S62+): while this body runs, Thread.currentThread() resolves
    // to THIS thread's heap object (AOSP identity law). Save/restore so a
    // nested drain (a body starting another thread) restores the outer
    // identity when the inner body ends.
    uint32_t saved_active_thread = 0;
    if (ts_shadow) {
        saved_active_thread = ts_shadow->current_thread_id() ==
                                      ts_shadow->main_thread_id()
                                  ? 0
                                  : ts_shadow->current_thread_id();
        ts_shadow->set_active_drained_thread(thread_oid);
    }
    // F-110b companion: a drained body runs at drain depth >= 1, so the
    // THREAD-SLEEP YIELD LAW (Thread.sleep inside a drained body) is
    // eligible. Without depth accounting, an infinite while(running)
    // {cycle; sleep(TICK);} body spins at the start site until the
    // loop-visit cap halts it (anuto GameLoop.run).
    int saved_drain_depth = park_drain_last_depth_;
    park_drain_last_depth_ = (saved_drain_depth < 1) ? 1 : saved_drain_depth;
    bool ran = try_recursive_invoke(rcls, "run", run_args, run_ret, run_res,
                                    "()V");
    park_drain_last_depth_ = saved_drain_depth;
    if (ts_shadow) ts_shadow->set_active_drained_thread(saved_active_thread);
    if (park_yield_pending_) {
        park_yield_pending_ = false;  // parked worker frame chain fully unwound
        // F-150 (S72-W4): the body is BLOCKED on Thread.sleep (AOSP), not
        // dead — register it with its WAKE time so the first scheduler
        // boundary at/after the wake re-drains the body. Deterministic
        // counterpart of the sleep elapsing on a real concurrent runtime.
        if (ts_shadow)
            ts_shadow->mark_thread_yielded(thread_oid,
                                           target_oid ? target_oid
                                                      : thread_oid,
                                           park_yield_wake_at_);
    } else if (ts_shadow && thread_oid != 0) {
        // Body completed (loop exit / return) — never re-drain it.
        ts_shadow->clear_thread_yielded(thread_oid);
        // [S193-C8] F-C8-185 TERMINATION LAW: a body that ran to
        // completion (returned or loop-exited without parking) has
        // TERMINATED — JDK Thread state law. isAlive() flips false;
        // join() on this target returns. Was (this line): no state,
        // isAlive() answered true forever.
        ts_shadow->mark_thread_terminated(thread_oid);
        std::cerr << "[THREAD-LIFE] thread o" << thread_oid
                  << " body completed → TERMINATED" << std::endl;
    }
    std::cerr << "[THREAD-START] drained oid=" << run_oid << " cls=" << rcls
              << (target_oid == thread_oid && thread_oid != 0
                      ? " (self-run law)"
                      : "")
              << " → " << (ran ? "REAL DEX run() executed"
                               : "no run() found (no-op)")
              << std::endl;
}

// R-NEW-345: park = deterministic yield point. See the law note at the
// LockSupport case in bridge_to_api. Bounded rounds; reentrancy-guarded so
// a park reached THROUGH drained work yields instead of recursing.
// Returns the work units consumed (0 = global quiescence).
uint64_t DalvikExecutionEngine::drain_park_queues_bounded(const char* reason) {
    static thread_local int park_drain_depth = 0;
    if (park_drain_depth >= 3) return 0;  // nested park: yield only
    if (!shadow_registry_) return 0;
    ++park_drain_depth;
    park_drain_last_depth_ = park_drain_depth;
    auto* hs = shadow_registry_->find_as<framework::HandlerShadow>();
    auto* cs = shadow_registry_->find_as<framework::ChoreographerShadow>();
    auto* ts = shadow_registry_->find_as<framework::ThreadShadow>();
    static thread_local uint64_t park_log = 0;
    bool do_log = park_log < 24;
    uint64_t work_units = 0;
    for (int round = 0; round < 4; ++round) {
        bool did_work = false;
        // 1) main MessageQueue runnables (Executor family + Handler.post +
        //    dispatcher trampoline all enqueue here — one-queue law).
        if (hs) {
            for (int r = 0; r < 16; ++r) {
                std::vector<std::pair<uint32_t, uint32_t>> drained;
                if (hs->drain_ready_ex(&drained) == 0) break;
                did_work = true;
                for (auto& rid_pair : drained) {
                    const uint32_t rid = rid_pair.first;
                    const uint32_t delivery_tid = rid_pair.second;
                    // Same routing as ExecutionEngine::invoke_handler_runnable:
                    // framework tokens ride the touch dispatcher, app runnables
                    // run their REAL DEX run().
                    if (rid >= framework::HandlerShadow::kFrameworkTokenBase)
                        continue;
                    if (!heap_.has_object(rid)) continue;
                    std::string rcls = "Ljava/lang/Object;";
                    if (const auto* robj = heap_.get(rid))
                        if (!robj->class_descriptor.empty())
                            rcls = robj->class_descriptor;
                    DalvikValue ret;
                    DalvikExecutionResult res;
                    std::vector<DalvikValue> run_args{
                        DalvikValue::make_object(rid, rcls)};
                    // F-NEW-289 (CONT-31) MAIN-QUEUE DELIVERY IDENTITY LAW
                    // (AOSP Looper/Handler model): code delivered by the
                    // main MessageQueue ALWAYS executes on the MAIN thread —
                    // inside every main-queue Runnable,
                    //   Thread.currentThread() == Looper.getMainLooper().getThread()
                    // (the DefaultTaskExecutor.isMainThread contract behind
                    // androidx LiveData.assertMainThread). The deterministic
                    // park drain runs NESTED inside a worker thread's
                    // run-to-completion body (F-110d binds the worker
                    // identity there — correct for the body itself), so
                    // without this re-bind the delivery INHERITS the worker
                    // identity and main-thread asserts throw
                    // (composeStopwatch ground truth: R8-renamed
                    // DefaultTaskExecutor.isMainThread Lca;.P()Z answered
                    // false -> Lcm0;.a ISE "Cannot invoke setValue on a
                    // background thread" -> DEFAULT_BACKGROUND_ONLY frame).
                    // Save/restore mirrors run_thread_start_body's F-110d
                    // pattern; 0 = main identity. No-op when already main.
                    //
                    // F-C4-593 (W10): the law is now PER-TASK —
                    // delivery_thread_id 0 (Handler.post on the main
                    // Looper) keeps the main identity verbatim;
                    // non-zero (an Executor.execute task) binds the
                    // EXECUTOR'S worker identity (AOSP ThreadPoolExecutor
                    // delivery — Room's assertNotMainThread must see a
                    // worker thread, or every background query ISE'd).
                    uint32_t saved_mq_identity = 0;
                    bool bound_mq_identity = false;
                    if (ts) {
                        if (ts->current_thread_id() !=
                                ts->main_thread_id() ||
                            delivery_tid != 0) {
                            saved_mq_identity = ts->current_thread_id();
                            ts->set_active_drained_thread(delivery_tid);
                            bound_mq_identity = true;
                        }
                    }
                    try_recursive_invoke(rcls, "run", run_args, ret, res, "()V");
                    if (bound_mq_identity)
                        ts->set_active_drained_thread(saved_mq_identity);
                }
                work_units += drained.size();
            }
        }
        // 2) Choreographer due frame callbacks (vsync during park — the
        //    withFrameNanos continuation resume path). F-NEW-289: doFrame
        //    is a MAIN-looper delivery (AOSP Choreographer rides the main
        //    thread) — same identity law as arm 1.
        if (cs && cs->has_pending_callbacks()) {
            auto due = cs->take_due_callbacks();
            for (auto& d : due) {
                ++work_units;
                DalvikValue ret;
                DalvikExecutionResult res;
                std::vector<DalvikValue> cb_args{
                    DalvikValue::make_object(d.callback_id, d.callback_class),
                    DalvikValue::make_long(d.frame_time_nanos)};
                uint32_t saved_frame_identity = 0;
                bool bound_frame_identity = false;
                if (ts && ts->current_thread_id() != ts->main_thread_id()) {
                    saved_frame_identity = ts->current_thread_id();
                    ts->set_active_drained_thread(0);
                    bound_frame_identity = true;
                }
                try_recursive_invoke(d.callback_class, "doFrame", cb_args, ret,
                                     res);
                if (bound_frame_identity)
                    ts->set_active_drained_thread(saved_frame_identity);
            }
            if (!due.empty()) did_work = true;
        }
        // 3) pending Thread starts (worker spawns observed while parked).
        if (ts) {
            uint32_t t_oid = 0, r_oid = 0;
            int started = 0;
            while (started < 4 && ts->consume_pending_start(t_oid, r_oid)) {
                ++started;
                ++work_units;
                did_work = true;
                run_thread_start_body(t_oid, r_oid);
            }
        }
        if (!did_work) break;
    }
    --park_drain_depth;
    park_drain_last_depth_ = park_drain_depth;
    // R-NEW-345: work dispatched through THIS drain that parked mid-way has
    // unwound by now; clear the yield flag so the caller's loop (main-thread
    // joinBlocking or the worker loop itself) resumes normally.
    park_yield_pending_ = false;
    if (do_log) {
        ++park_log;
        std::cerr << "[PARK-DRAIN] " << reason << " depth=" << park_drain_depth
                  << " work_units=" << work_units << std::endl;
    }
    return work_units;
}

// ─────────────────────────────────────────────────────────────────────────
// F-103 (S58, R-NEW-378): OpenJDK Class.isAssignableFrom assignability walk.
// Law (OpenJDK Class.java / AOSP): `to.isAssignableFrom(from)` is true iff
// `from` is the same class, a subclass, a implementor of `to` (transitively),
// or — for arrays — component-covariant into `to`. `java.lang.Object`
// accepts every reference type. Primitives only match themselves. The walk
// is bounded (16 super hops / 8 interface expansions) like the existing
// try_recursive_invoke_on_super bound.
// ─────────────────────────────────────────────────────────────────────────
bool DalvikExecutionEngine::dalvik_class_assignable(const std::string& from_desc,
                                                    const std::string& to_desc) {
    if (from_desc.empty() || to_desc.empty()) return false;
    if (from_desc == to_desc) return true;
    if (to_desc == "Ljava/lang/Object;") {
        // Reference types (L...; and [...) are Objects; primitives are not.
        return from_desc[0] == 'L' || from_desc[0] == '[';
    }
    // Array covariance: X[] assignable to Y[] iff X assignable to Y;
    // every array is assignable to Object[]'s super-chain (Object,
    // Cloneable, java.io.Serializable).
    if (from_desc[0] == '[' && to_desc[0] == '[') {
        // Component-wise: strip one bracket pair and recurse.
        return dalvik_class_assignable(from_desc.substr(1), to_desc.substr(1));
    }
    if (from_desc[0] == '[' && (to_desc == "Ljava/lang/Cloneable;" ||
                                to_desc == "Ljava/io/Serializable;")) {
        return true;  // JLS: arrays implement Cloneable + Serializable
    }
    // Primitive descriptors only match by identity (handled above).
    if (from_desc.size() == 1 || to_desc.size() == 1) return false;
    // ── CONT-124 (F-NEW-469): SUPERINTERFACE CLOSURE LAW ────────────────────
    // JVMS 5.1 / ART Class::IsAssignableFrom: an interface S is assignable
    // to interface T when S extends T TRANSITIVELY (iface→iface chains of
    // any depth). The prior walk checked each hop's DIRECTLY declared
    // interfaces only — a three-level chain (class implements I3; I3
    // extends I2; I2 extends I1) answered FALSE and the aput-object
    // store-check threw a BOGUS ArrayStoreException on a legal store.
    // Live face (dooz v23, binary 04a89c52): Liw0;.b stored Lf6; (implements
    // Lbu0;) into [Lxt0; — Lbu0; extends Lvt0; extends Lxt0; — the walk
    // answered FALSE, the AIOOBE escaped the Lr;.g recovery re-throw, the
    // LayoutNode placement pass (Lel0;.c/.d) unwound, no Placeable.position
    // write ever landed, and dooz rendered the bare themed background.
    // Law: BFS the superinterface graph from every interface encountered
    // (the start class's own list AND every superclass hop's list) through
    // BOTH the DEX tables (class_to_interfaces_) and the F-NEW-236 framework
    // tables (framework_implements), visited-set bounded. Only previously-
    // FALSE answers can flip to TRUE — permissive in exactly the direction
    // the JVMS law demands; illegal stores are still rejected.
    auto interface_reaches = [&](const std::string& iface,
                                 const std::string& target) -> bool {
        if (iface == target) return true;
        std::vector<std::string> work{iface};
        std::unordered_set<std::string> visited{iface};
        int hops = 0;
        while (!work.empty() && hops < 64) {
            std::string cur = work.back();
            work.pop_back();
            ++hops;
            auto it = class_to_interfaces_.find(cur);
            if (it != class_to_interfaces_.end()) {
                for (const auto& sup : it->second) {
                    if (sup == target) return true;
                    if (visited.insert(sup).second) work.push_back(sup);
                }
            }
            // Platform interfaces carry their parents only in the framework
            // tables (libcore law) — same consult the F-NEW-253 tail makes.
            std::unordered_set<std::string> fw_closure;
            framework::framework_interface_closure(cur, fw_closure);
            for (const auto& sup : fw_closure) {
                if (sup == target) return true;
                if (visited.insert(sup).second) work.push_back(sup);
            }
        }
        return false;
    };
    // R-NEW-010 store-check completion (CONT-122, tower3d live face):
    // JVMS 5.1 / AOSP Class.isAssignableFrom — the STARTING class's OWN
    // declared interfaces count. The walk below only inspects interfaces
    // of the SUPERCLASSES it hops through, so an anonymous class that
    // DIRECTLY implements the target interface
    // (Lcom/badlogic/gdx/backends/android/AndroidApplication$1; implements
    // Lcom/badlogic/gdx/LifecycleListener;) answered FALSE and the
    // aput-object store-check rejected a legal LifecycleListener[] store.
    if (to_desc[0] == 'L') {
        auto own_ifc = class_to_interfaces_.find(from_desc);
        if (own_ifc != class_to_interfaces_.end()) {
            for (const auto& ifc : own_ifc->second)
                if (interface_reaches(ifc, to_desc)) return true;
        }
        if (framework::framework_implements(from_desc, to_desc)) return true;
    }
    // Superclass walk (bounded, same bound as try_recursive_invoke_on_super).
    static constexpr int kMaxAssignHops = 16;
    std::string walk = from_desc;
    for (int hop = 0; hop < kMaxAssignHops; ++hop) {
        auto sup_it = class_to_superclass_.find(walk);
        // F-NEW-254 (CONT-7 W3): DEX + FRAMEWORK HIERARCHY COMPOSITION —
        // one walk. When the DEX tables end at the platform boundary
        // (e.g. Ljava/util/concurrent/CancellationException; has no
        // class_def in the APK), continue through the F-NEW-236 framework
        // extends table instead of stopping — the SAME fallback law
        // is_subclass_of (instance-of path) already implements. Without
        // it, Class.isInstance(Throwable-target) on a platform exception
        // subclass answered FALSE and kotlinx Finishing threw its own
        // ISE "State is …" during dooz composition.
        std::string sup = (sup_it != class_to_superclass_.end())
                              ? sup_it->second
                              : framework::framework_superclass_of(walk);
        if (sup.empty()) break;
        walk = sup;
        if (walk.empty()) break;
        if (walk == to_desc) return true;
        // Interface declared anywhere along the super chain counts —
        // through the FULL superinterface closure (F-NEW-469), not just
        // the directly declared list.
        auto ifc_it = class_to_interfaces_.find(walk);
        if (ifc_it != class_to_interfaces_.end()) {
            for (const auto& ifc : ifc_it->second)
                if (interface_reaches(ifc, to_desc)) return true;
        }
        // F-NEW-292: the hop class may itself be a PLATFORM class whose
        // libcore implements metadata lives in the framework tables
        // (Ljava/lang/Enum; implements Serializable, Comparable — an
        // R8-minified app enum carries those edges ONLY through this hop;
        // its own class_def declares none). Same consult the F-NEW-253
        // tail performs for from_desc, applied per hop so every
        // intermediate platform hop sees the same boot-classpath truth.
        if (framework::framework_implements(walk, to_desc)) return true;
    }
    // Directly-declared interfaces of `from` itself.
    auto ifc_it = class_to_interfaces_.find(from_desc);
    if (ifc_it != class_to_interfaces_.end()) {
        for (const auto& ifc : ifc_it->second)
            if (interface_reaches(ifc, to_desc)) return true;
    }
    // ── F-NEW-253 (CONT-7 W3): PLATFORM HIERARCHY FALLBACK — one central
    // point. Class.isInstance/isAssignableFrom ask assignability between
    // types that may be ENGINE-SHADOWED PLATFORM classes (Landroid/os/Bundle;
    // etc.) with no DEX class_def and no entry in class_to_superclass_ /
    // class_to_interfaces_. The F-NEW-236 framework tables (libcore +
    // android.os source law) are the runtime's boot-classpath metadata:
    // consult the same transitive closure here, after the DEX walk, so
    // EVERY consumer of this walk (the F-103 isInstance law, the
    // saveable platform check, future reflection-family callers) sees
    // the same truth ART sees from its boot classpath.
    // Live face (dooz v23): Parcelable.isInstance(Bundle) answered FALSE
    // → rememberSaveable IAE at registerValue → composition died before
    // the first app frame.
    {
        std::unordered_set<std::string> platform_closure;
        framework::framework_interface_closure(from_desc, platform_closure);
        if (platform_closure.count(to_desc)) return true;
    }
    return false;
}

// ────────────────────────────────────────────────────────────────────────
// F-NEW-223 (user campaign §H) — VIRTUAL EXTERNAL-STORAGE VOLUME LAW.
// AOSP Environment.java + StorageManager: every device has a PRIMARY
// external storage volume, EMULATED, mounted at /storage/emulated/0,
// state MEDIA_MOUNTED, readable+writable by the app. Apps probe it at
// startup (user evidence: opencalc's onCreate died because the path
// "does not exist" — the honest R-NEW-346 metadata law answered ABSENT
// for the raw absolute path, which on real hardware is a MOUNT POINT
// that always exists). The runtime emulates a device: the volume is a
// VIRTUAL MOUNT backed physically by <data_root>/storage/emulated/0
// (the ONE sandbox root law — no writes escape the sandbox, deterministic
// across runs). Translation is a pure prefix map; the backing root is
// materialized on demand so exists() on the mount point is TRUE without
// any app-side mkdirs (AOSP: the volume is mounted at boot, before any
// app runs).
// ────────────────────────────────────────────────────────────────────────
static std::string host_path_for_virtual_volume(const std::string& p) {
    static const char* kMount = "/storage/emulated/0";
    if (p.empty() || p.rfind(kMount, 0) != 0)
        return p;
    namespace fs = std::filesystem;
    fs::path backing =
        fs::path(Storage::app_data_root()) / "storage" / "emulated" / "0";
    // The mount point itself exists from boot (materialize once, idempotent).
    std::error_code mk_ec;
    fs::create_directories(backing, mk_ec);
    std::string rest = p.size() > strlen(kMount) ? p.substr(strlen(kMount)) : "";
    std::string hp = (backing.string() + rest);
    // Collapse the mount point to its canonical host form without
    // touching the caller's spelling of the virtual path.
    return hp;
}

// ─── CONT-97 T1: bridge dispatch census (env MINIANDROID_BRIDGE_CENSUS=1) ───
// Answers: which (class,method) keys consume the measured 145.7K cycles/call
// aggregate? Bounded map keyed on the call's (class,method); RAII record on
// scope exit so the WHOLE law-chain cost is attributed to the key. Zero cost
// when disabled (one relaxed load). Prints at atexit, top 48 by ticks.

// ── CODER7 WAVE-2: the service BRING-DOWN path (AOSP ActiveServices
// bringDownServiceLocked). Law: when a live service is torn down by ANY
// caller (stopService / stopSelf / stopSelfResult) while bound connections
// exist, onUnbind(bindingIntent) is delivered BEFORE onDestroy — exactly as
// the unbind-driven destruction path already does. The wave-1 tree delivered
// onUnbind only on the unbind path; the stop paths skipped it (recorded
// PENDING in the wave-1 issue §7). onDestroy ALWAYS follows on the
// bring-down path (an onUnbind==true return does NOT keep the instance
// alive here — ActiveServices continues bringDownServiceLocked after the
// unbind delivery).
void DalvikExecutionEngine::c7_service_bring_down(ServiceInstance& svc,
                                                  const char* reason) {
    if (!svc.created || svc.destroyed) return;
    if (svc.bindings > 0) {
        // The binding intent of the FIRST live connection is the onUnbind
        // argument (AOSP passes the binding Intent; with several
        // connections the dispatcher delivers one onUnbind for the record —
        // same shape as the unbind path).
        uint32_t c7_bint_oid = 0;
        for (const auto& [conn_oid, cb] : svc.conn_bindings) {
            if (cb.bind_intent_oid != 0) {
                c7_bint_oid = cb.bind_intent_oid;
                break;
            }
        }
        DalvikValue c7_bint =
            (c7_bint_oid != 0 && heap_.has_object(c7_bint_oid))
                ? DalvikValue::make_object(c7_bint_oid,
                                           "Landroid/content/Intent;")
                : DalvikValue::make_null();
        DalvikValue c7_ub;
        bool c7_has_unbind = invoke_lifecycle_method(
            svc.oid, svc.cls, "onUnbind", {c7_bint}, c7_ub);
        miniandroid::diagnostics::FileIoTrace::instance().record(
            "SVC-UNBIND", svc.cls, true,
            std::string("bring-down (") + reason + "): onUnbind delivered" +
                (c7_has_unbind ? " (override answered)" : " (default)"),
            current_class_ + "." + current_method_);
    }
    DalvikValue c7_ignore;
    invoke_lifecycle_method(svc.oid, svc.cls, "onDestroy", {}, c7_ignore);
    svc.destroyed = true;
    svc.started = false;
    svc.bindings = 0;
    svc.conn_bindings.clear();
    miniandroid::diagnostics::FileIoTrace::instance().record(
        "SVC-STOP", svc.cls, true,
        std::string(reason) + " → onDestroy delivered",
        current_class_ + "." + current_method_);
}

namespace {
// ── C9-7 (CODER 9) — in-memory PNG encode (Bitmap.compress FORMAT_PNG) ──
// libpng-backed RGBA encoder (the SAME library the runtime's PNG decoder
// uses — one PNG authority). The write callback appends to a std::vector.
// Error-path note: the setjmp branch leaks only the `rows` pointer array
// (h * sizeof(void*) — bounded, error-only); no other C++ object crosses
// the longjmp.
bool c9_png_encode_rgba(int w, int h,
                               const std::vector<uint8_t>& rgba,
                               std::vector<uint8_t>* out) {
    if (w <= 0 || h <= 0 || rgba.size() != (size_t)w * h * 4 || !out)
        return false;
    png_structp p = png_create_write_struct(PNG_LIBPNG_VER_STRING,
                                            nullptr, nullptr, nullptr);
    if (!p) return false;
    png_infop info = png_create_info_struct(p);
    if (!info) {
        png_destroy_write_struct(&p, nullptr);
        return false;
    }
    std::vector<uint8_t*> rows(h);
    for (int y = 0; y < h; ++y)
        rows[y] = const_cast<uint8_t*>(&rgba[(size_t)y * w * 4]);
    if (setjmp(png_jmpbuf(p))) {
        png_destroy_write_struct(&p, &info);
        return false;
    }
    auto write_fn = [](png_structp pp, png_bytep data, png_size_t len) {
        static_cast<std::vector<uint8_t>*>(png_get_io_ptr(pp))
            ->insert(static_cast<std::vector<uint8_t>*>(png_get_io_ptr(pp))
                         ->end(),
                     data, data + len);
    };
    auto flush_fn = [](png_structp) {};
    png_set_write_fn(p, out, write_fn, flush_fn);
    png_set_IHDR(p, info, (png_uint_32)w, (png_uint_32)h, 8,
                 PNG_COLOR_TYPE_RGBA, PNG_INTERLACE_NONE,
                 PNG_COMPRESSION_TYPE_DEFAULT, PNG_FILTER_TYPE_DEFAULT);
    png_write_info(p, info);
    png_write_image(p, rows.data());
    png_write_end(p, nullptr);
    png_destroy_write_struct(&p, &info);
    return true;
}

// ── C9-10 (CODER 9) — DisplayMetrics device-profile law ────────────────
// ONE density authority: resources::device_config() — the SAME
// ResTableConfig the bucket selection (AssetManager2 match) and the C9-1
// BitmapFactory inTargetDensity use. The previous constants
// (2.625/420/1080x1920 hardcoded) diverged from the runtime device the
// moment MINIANDROID_DENSITY selected another bucket (the registered §2
// gap: densityDpi answered 420 while the bucket law served 160/240-
// selected resources). density = dpi/160 (AOSP DisplayMetrics law);
// scaledDensity = density (fontScale 1.0); xdpi/ydpi = densityDpi.
void c9_fill_display_metrics(DalvikHeap& heap,
                                    uint32_t dm_id) {
    if (dm_id == 0 || !heap.has_object(dm_id)) return;
    const auto& cfg = resources::device_config();
    const float density = (float)cfg.density / 160.0f;
    auto set_f = [&](const char* f, float v) {
        heap.set_object_field(dm_id, f, DalvikValue::make_float(v));
    };
    auto set_i = [&](const char* f, int32_t v) {
        heap.set_object_field(dm_id, f, DalvikValue::make_int(v));
    };
    set_f("density", density);
    set_i("densityDpi", (int32_t)cfg.density);
    set_f("scaledDensity", density);
    set_i("widthPixels", (int32_t)cfg.screenWidth);
    set_i("heightPixels", (int32_t)cfg.screenHeight);
    set_f("xdpi", (float)cfg.density);
    set_f("ydpi", (float)cfg.density);
    static thread_local uint64_t c9_dm_log = 0;
    if (c9_dm_log++ < 8)
        std::cerr << "[C9-10] DisplayMetrics <- device_config(): density="
                  << density << " dpi=" << cfg.density << " "
                  << cfg.screenWidth << "x" << cfg.screenHeight
                  << std::endl;
}
}  // namespace

// ── F-NEW-659 (#588 Games-g2) — the framework (0x01-package) string-id
// table.android-4.4w_r1 public.xml (docs/upstream/aosp/public.xml,
// byte-verified ids) × the tag's own core/res/res/values/strings.xml
// (values fetched + verified per row from the googlesource tag; the two
// newer-than-4.4w rows 0x01040018/0x01040019 are NOT carried — their
// texts cannot be verified in this tag). The GATE-A law resolves from
// this table BEFORE the NotFoundException throw: GameControl.newGame
// pc=52 died on android.R.string.unknownName (0x0104000e) — a framework
// id the APK's ARSC table never carries. NOTE: the 4.4w truth for
// unknownName is "(Unknown)" (the lane's log paraphrased "Unknown");
// every value here is the tag's byte-verified English default.
struct F659FrameworkString { uint32_t id; const char* text; };
static const F659FrameworkString f659_table[] = {
    {0x01040000, "Cancel"},
    {0x01040001, "Copy"},
    {0x01040002, "Copy URL"},
    {0x01040003, "Cut"},
    {0x01040004, "Voicemail"},
    {0x01040005, "MSISDN1"},
    {0x01040006, "(No phone number)"},
    {0x01040007, "Couldn't open the page because the URL is invalid."},
    {0x01040008, "The protocol isn't supported."},
    {0x01040009, "Cancel"},                 // android.R.string.no
    {0x0104000a, "OK"},                     // android.R.string.ok
    {0x0104000b, "Paste"},
    {0x0104000c, "Search"},
    {0x0104000d, "Select all"},
    {0x0104000e, "(Unknown)"},              // android.R.string.unknownName
    {0x0104000f, "<Untitled>"},
    {0x01040010, "OK"},
    {0x01040011, "Can't play this video."},
    {0x01040012, "Video problem"},
    {0x01040013, "OK"},                     // android.R.string.yes
    {0x01040014, "Attention"},
    {0x01040015, "This video isn't valid for streaming to this device."},
    {0x01040016, "Select text"},
    {0x01040017, "999+"},
};
const char* framework_string_id_text(uint32_t resid) {
    for (const auto& row : f659_table)
        if (row.id == resid) return row.text;
    return nullptr;
}
} // namespace dalvik
} // namespace miniandroid
