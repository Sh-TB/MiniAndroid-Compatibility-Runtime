/*
 * MiniAndroid Runtime v0.2 - Real Dalvik Execution Engine
 * EXP-030: Real Bytecode Execution
 * 
 * Complete Dalvik register machine implementation with:
 * - Full opcode execution (25+ opcodes)
 * - Method call stack (StackFrame)
 * - Object heap management
 * - API bridge integration
 * - Comprehensive evidence generation
 */

#ifndef MINIANDROID_DALVIK_ENGINE_TYPES_H
#define MINIANDROID_DALVIK_ENGINE_TYPES_H

#include <iostream>  // S224-TAPDRAIN probe line (header inline method)
#include <cstdint>
#include <set>
#include <map>
#include <string>

// S224-TAPDRAIN: the insertAt census sets are shared between the engine
// body (.cpp definitions) and the tap-path drain (header inline method).
namespace miniandroid::dalvik {
extern std::set<uint32_t> g_d7_node_ids;
extern std::set<uint32_t> g_s221_bridged;
}

// The .cpp defines these inside `namespace miniandroid::dalvik { namespace
// { ... } }` — move them OUT of the anonymous namespace so the header's
// externs bind. (sed applied below in the .cpp edit.)

#include "class_resolver.h"
#include "c7_package_index.h"        // CODER7 WAVE-5: PMS-lite (cross-package index)
#include "../runtime/runtime_metadata.h"
#include "../runtime/vtable_dispatch.h"
#include "../api/android_stubs.h"
#include "../resources/arsc_parser.h"   // GOLDEN-03: canonical resolver hook
#include "../resources/attribute_set_store.h"  // F-NEW-197: XML AttributeSet law
#include "../resources/res_config.h"    // G04 §4: device_config() (inTargetDensity)
#include "../storage/sqlite_shadow.h"   // M3 F-ROOM-CHAIN: databases dir wiring
#include "../storage/data_root.h"       // M3 FINDING-012: app-data root law
#include "../framework/adapter_scrap_bin.h"  // F-S231-A: RecycleBin scrap contract
#include <fstream>                      // LOADING-CAMPAIGN (ST-2): OpenWriter.ofstream
// EXP-051: Shadow registry forward-declarations.
namespace miniandroid { namespace framework {
class ShadowRegistry;
struct CallResult;   // F-105: the reconciliation law documents CallResult's
                     // (object_id, class) declaration contract
class HeapAllocator;
}}
#include <string>
#include <vector>
#include <algorithm>  // CODER7 W8-L1: std::find in c7_check_provider_access
#include <filesystem>
#include <map>
#include <unordered_map>
#include <algorithm>  // F-NEW-381 phase 2: get_all_ids sorted-order contract
#include <stack>
#include <tuple>                       // CONT-102: manifest activity attrs
#include <memory>
#include <atomic>                      // CONT-32 F-NEW-381 lever: COW cell refcounts
#include <cstdint>
#include <optional>
#include <functional>
#include <sstream>
#include <iomanip>
#include <chrono>
#include <set>
#include <unordered_set>  // CONT-42: M3 active-key set (lookup-only)

#include "../../third_party/nlohmann_json/include/nlohmann/json.hpp"

namespace miniandroid {
namespace dalvik {

// ── TRAIN-59 (S144) ContentValues flat mirror ───────────────────────────
// The SQLiteDatabase.update arm lives in storage::DatabaseShadow, which
// holds no engine reference; the ContentValues key/value state lives in
// DalvikExecutionEngine::content_values_ (filled by the #371 PHASE B1
// put() handler). put() ALSO flattens each entry into this process-wide
// mirror (boxed values unwrapped through their canonical "value" field —
// the getAsInteger law) at the moment the heap object is live; the shadow
// reads the snapshot to build the REAL sqlite3 UPDATE SET binds. Kind
// codes: 0=null, 1=int64, 2=double, 3=text.
struct CvFlat {
    std::string key;
    int kind = 0;  // 0 null / 1 int64 / 2 double / 3 text
    int64_t i = 0;
    double d = 0.0;
    std::string s;
};
std::vector<CvFlat> content_values_flat_snapshot(uint32_t oid);

using json = nlohmann::json;
using Clock = std::chrono::high_resolution_clock;

// ============================================================================
// OPCODE DEFINITIONS — Complete Dalvik Instruction Set (EXP-030 Scope)
// ============================================================================

namespace Opcode {
    // Constants (10 opcodes)
    constexpr uint16_t NOP = 0x0000;
    constexpr uint16_t CONST_4 = 0x12;       // const/4 vAA, #+BBBB
    constexpr uint16_t CONST_16 = 0x13;      // const/16 vAA, #+BBBB
    constexpr uint16_t CONST = 0x14;         // const vAA, #+BBBBBBBB
    constexpr uint16_t CONST_HIGH16 = 0x15;  // const/high16 vAA, #+BBBB0000
    // EXP-041: const-wide opcodes (correct values per AOSP)
    constexpr uint16_t CONST_WIDE_16 = 0x16;   // const-wide/16 vAA, #+BBBB (21s, 2 code units)
    constexpr uint16_t CONST_WIDE_32 = 0x17;    // const-wide/32 vAA, #+BBBBBBBB (31i, 3 code units)
    constexpr uint16_t CONST_WIDE = 0x18;      // const-wide vAA, #+BBBBBBBBBBBBBBBB (51l, 5 code units)
    constexpr uint16_t CONST_WIDE_HIGH16 = 0x19; // const-wide/high16 vAA, #+BBBB000000000000 (21s, 2 code units)
    constexpr uint16_t CONST_STRING = 0x1A;  // const-string vAA, string@BBBB
    constexpr uint16_t CONST_STRING_JUMBO = 0x1B; // const-string/jumbo vAA, string@BBBBBBBB
    constexpr uint16_t CONST_CLASS = 0x1C;   // const-class vAA, type@BBBB
    constexpr uint16_t MONITOR_ENTER = 0x1D; // monitor-enter vAA
    constexpr uint16_t MONITOR_EXIT = 0x1E;  // monitor-exit vAA
    
    // Moves (11 opcodes)
    constexpr uint16_t MOVE = 0x01;          // move vA, vB
    constexpr uint16_t MOVE_FROM16 = 0x02;   // move/from16 vAA, vBBBB
    constexpr uint16_t MOVE_16 = 0x03;       // move/16 vAAAA, vBBBB
    constexpr uint16_t MOVE_WIDE = 0x04;     // move-wide vA, vB
    constexpr uint16_t MOVE_WIDE_FROM16 = 0x05; // move-wide/from16 vAA, vBBBB
    // S211 KNOWLEDGE-TRANSFER PROBE (#529 D-P0-5 residue): 0x06 was the only
    // member of the move family with NO constant here and NO dispatch case —
    // any method using it died at the unimplemented-opcode handler. AOSP
    // instruction-formats: 32x, "move-wide/16 vAAAA, vBBBB".
    constexpr uint16_t MOVE_WIDE_16 = 0x06;  // move-wide/16 vAAAA, vBBBB (32x)
    constexpr uint16_t MOVE_OBJECT = 0x07;   // move-object vA, vB
    constexpr uint16_t MOVE_OBJECT_FROM16 = 0x08; // move-object/from16 vAA, vBBBB
    constexpr uint16_t MOVE_OBJECT_16 = 0x09; // move-object/16 vAAAA, vBBBB
    constexpr uint16_t MOVE_RESULT = 0x0A;   // move-result vAA
    // EXP-037 Phase B (BLOCKER-021 FIX): Previous code had MOVE_RESULT_OBJECT
    // = 0x0B and MOVE_RESULT_WIDE = 0x0C — SWAPPED. Per AOSP:
    //   0x0a = move-result
    //   0x0b = move-result-wide
    //   0x0c = move-result-object
    // TinyMusicPlayer's onCreate hits 0x0c (move-result-object) at PC=6 and
    // was being dispatched to execute_move_result_wide handler (which doesn't
    // exist — falls through to "unimplemented").
    constexpr uint16_t MOVE_RESULT_WIDE = 0x0B;   // move-result-wide vAA
    constexpr uint16_t MOVE_RESULT_OBJECT = 0x0C; // move-result-object vAA
    constexpr uint16_t MOVE_EXCEPTION = 0x0D; // move-exception vAA
    
    // Returns (4 opcodes)
    constexpr uint16_t RETURN_VOID = 0x0E;   // return-void {}
    constexpr uint16_t RETURN = 0x0F;        // return {} vAA
    constexpr uint16_t RETURN_WIDE = 0x10;   // return-wide {} vAA
    constexpr uint16_t RETURN_OBJECT = 0x11; // return-object {} vAA
    
    // Objects (3 opcodes)
    constexpr uint16_t INSTANCE_OF = 0x20;   // instance-of vA, vB, type@CCCC
    constexpr uint16_t CHECK_CAST = 0x1F;    // check-cast vAA, type@BBBB
    constexpr uint16_t NEW_INSTANCE = 0x22;  // new-instance vAA, type@BBBB
    constexpr uint16_t NEW_ARRAY = 0x23;     // new-array vA, vB, type@CCCC (EXP-038)
    constexpr uint16_t ARRAY_LENGTH = 0x21;  // array-length vA, vB

    // EXP-038 (BLOCKER-031): Array get/put opcodes (23x format)
    constexpr uint16_t AGET = 0x44;           // aget vAA, vBB, vCC
    constexpr uint16_t AGET_WIDE = 0x45;      // aget-wide vAA, vBB, vCC
    constexpr uint16_t AGET_OBJECT = 0x46;     // aget-object vAA, vBB, vCC
    constexpr uint16_t AGET_BOOLEAN = 0x47;    // aget-boolean vAA, vBB, vCC
    constexpr uint16_t AGET_BYTE = 0x48;      // aget-byte vAA, vBB, vCC
    constexpr uint16_t AGET_CHAR = 0x49;      // aget-char vAA, vBB, vCC
    constexpr uint16_t AGET_SHORT = 0x4A;     // aget-short vAA, vBB, vCC
    constexpr uint16_t APUT = 0x4B;           // aput vAA, vBB, vCC
    constexpr uint16_t APUT_WIDE = 0x4C;      // aput-wide vAA, vBB, vCC
    constexpr uint16_t APUT_OBJECT = 0x4D;    // aput-object vAA, vBB, vCC
    constexpr uint16_t APUT_BOOLEAN = 0x4E;   // aput-boolean vAA, vBB, vCC
    constexpr uint16_t APUT_BYTE = 0x4F;      // aput-byte vAA, vBB, vCC
    constexpr uint16_t APUT_CHAR = 0x50;      // aput-char vAA, vBB, vCC
    constexpr uint16_t APUT_SHORT = 0x51;     // aput-short vAA, vBB, vCC
    
    // Instance Field Operations (EXP-035: Field System Integration)
    constexpr uint16_t IGET = 0x52;          // iget vA, vB, field@CCCC
    constexpr uint16_t IGET_WIDE = 0x53;     // iget-wide vA, vB, field@CCCC
    constexpr uint16_t IGET_OBJECT = 0x54;   // iget-object vA, vB, field@CCCC
    constexpr uint16_t IGET_BOOLEAN = 0x55;  // iget-boolean vA, vB, field@CCCC
    constexpr uint16_t IGET_BYTE = 0x56;     // iget-byte vA, vB, field@CCCC
    constexpr uint16_t IGET_CHAR = 0x57;     // iget-char vA, vB, field@CCCC
    constexpr uint16_t IGET_SHORT = 0x58;    // iget-short vA, vB, field@CCCC
    constexpr uint16_t IPUT = 0x59;          // iput vA, vB, field@CCCC
    constexpr uint16_t IPUT_WIDE = 0x5A;     // iput-wide vA, vB, field@CCCC
    constexpr uint16_t IPUT_OBJECT = 0x5B;   // iput-object vA, vB, field@CCCC
    constexpr uint16_t IPUT_BOOLEAN = 0x5C;  // iput-boolean vA, vB, field@CCCC
    constexpr uint16_t IPUT_BYTE = 0x5D;     // iput-byte vA, vB, field@CCCC
    constexpr uint16_t IPUT_CHAR = 0x5E;     // iput-char vA, vB, field@CCCC
    constexpr uint16_t IPUT_SHORT = 0x5F;    // iput-short vA, vB, field@CCCC
    
    // Static Field Operations (EXP-035: Static Field Integration)
    constexpr uint16_t SGET = 0x60;          // sget vAA, field@BBBB
    constexpr uint16_t SGET_WIDE = 0x61;     // sget-wide vAA, field@BBBB
    constexpr uint16_t SGET_OBJECT = 0x62;   // sget-object vAA, field@BBBB
    constexpr uint16_t SGET_BOOLEAN = 0x63;  // sget-boolean vAA, field@BBBB
    constexpr uint16_t SGET_BYTE = 0x64;     // sget-byte vAA, field@BBBB
    constexpr uint16_t SGET_CHAR = 0x65;     // sget-char vAA, field@BBBB
    constexpr uint16_t SGET_SHORT = 0x66;    // sget-short vAA, field@BBBB
    constexpr uint16_t SPUT = 0x67;          // sput vAA, field@BBBB
    constexpr uint16_t SPUT_WIDE = 0x68;     // sput-wide vAA, field@BBBB
    constexpr uint16_t SPUT_OBJECT = 0x69;   // sput-object vAA, field@BBBB
    constexpr uint16_t SPUT_BOOLEAN = 0x6A;  // sput-boolean vAA, field@BBBB
    constexpr uint16_t SPUT_BYTE = 0x6B;     // sput-byte vAA, field@BBBB
    constexpr uint16_t SPUT_CHAR = 0x6C;     // sput-char vAA, field@BBBB
    constexpr uint16_t SPUT_SHORT = 0x6D;    // sput-short vAA, field@BBBB
    
    // Invokes (7 core opcodes)
    constexpr uint16_t INVOKE_VIRTUAL = 0x6E;    // invoke-virtual {vC..}, method@BBBB
    constexpr uint16_t INVOKE_SUPER = 0x6F;      // invoke-super {vC..}, method@BBBB
    constexpr uint16_t INVOKE_DIRECT = 0x70;     // invoke-direct {vC..}, method@BBBB
    constexpr uint16_t INVOKE_STATIC = 0x71;     // invoke-static {vC..}, method@BBBB
    constexpr uint16_t INVOKE_INTERFACE = 0x72;  // invoke-interface {vC..}, method@BBBB

    // EXP-038 (BLOCKER-030): invoke-*/range opcodes (3rc format)
    // These are used for method calls with many arguments (>5).
    constexpr uint16_t INVOKE_VIRTUAL_RANGE = 0x74;   // invoke-virtual/range {vCCCC..vNNNN}, meth@BBBB
    constexpr uint16_t INVOKE_SUPER_RANGE = 0x75;     // invoke-super/range
    constexpr uint16_t INVOKE_DIRECT_RANGE = 0x76;    // invoke-direct/range
    constexpr uint16_t INVOKE_STATIC_RANGE = 0x77;    // invoke-static/range
    constexpr uint16_t INVOKE_INTERFACE_RANGE = 0x78; // invoke-interface/range
    
    // Control flow (basic set)
    // EXP-043 Phase 1: Fixed goto opcode values (off-by-one regression).
    // Per AOSP dalvik-bytecode.html:
    //   0x27 goto (10t format), 0x28 goto/16 (20t), 0x29 goto/32 (30t)
    // Previous code had GOTO=0x28 (which is goto/16, not goto), and
    // GOTO_16=0x27 (which is goto, not goto/16). Both were swapped.
    // This bug caused real `goto` opcodes (most common in Dalvik bytecode)
    // to be incorrectly dispatched as `goto/16`, which reads the next
    // code unit as the offset instead of using the high byte of the
    // current opcode. Result: wrong branch targets, infinite loops
    // in compact goto-heavy methods.
    // EXP-071: CORRECTED opcode values per AOSP dalvik-bytecode.html.
    // All opcodes now match AOSP canonical values:
    //   0x24 = filled-new-array
    //   0x25 = filled-new-array/range
    //   0x26 = fill-array-data (FIXED — was 0x25)
    //   0x27 = throw (FIXED — was 0x26)
    //   0x28 = goto (FIXED — was 0x27, now has D8/R8 hybrid handler)
    //   0x29 = goto/16
    //   0x2A = goto/32
    constexpr uint16_t FILLED_NEW_ARRAY = 0x24;           // filled-new-array
    constexpr uint16_t FILLED_NEW_ARRAY_RANGE = 0x25;     // filled-new-array/range
    constexpr uint16_t FILL_ARRAY_DATA = 0x26;             // fill-array-data (31t, 3 code units) — FIXED!
    constexpr uint16_t THROW = 0x27;                       // throw vAA (11x, 1 code unit) — FIXED!
    constexpr uint16_t GOTO = 0x28;                        // goto +AA (10t, 1 code unit) — FIXED!
    constexpr uint16_t GOTO_16 = 0x29;                     // goto/16 +AAAA (20t, 2 code units)
    constexpr uint16_t GOTO_32 = 0x2A;                     // goto/32 +AAAAAAAA (30t, 3 code units)
    // EXP-059 ROOT CAUSE FIX: The if-* opcode table was OFF BY ONE
    // vs the actual AOSP source code.
    //
    // Per https://cs.android.com/android/platform/superproject/+/main:art/libdexfile/dex/dex_instruction_list.h
    //   0x30 cmpg-double, 0x31 cmp-long
    //   0x32 if-eq, 0x33 if-ne, 0x34 if-lt, 0x35 if-ge, 0x36 if-gt, 0x37 if-le
    //   0x38 if-eqz, 0x39 if-nez, 0x3a if-ltz, 0x3b if-gez, 0x3c if-gtz, 0x3d if-lez
    //
    // Previously we had: 0x31 if-eq, 0x37 if-eqz, 0x38 if-nez, 0x39 if-ltz.
    // That was WRONG — every if-* was dispatched to the wrong handler.
    //
    // Symptom: ActionBarLayout.addFragmentToStack returned 0 (false) at PC=24
    // because byte 0x38 (intended: if-eqz) was dispatched to execute_if_nez,
    // which inverts the branch direction. When fragmentsStack.contains returned
    // VOID_ (treated as 0), if-eqz should branch to PC=27 (continue with
    // setParentLayout), but if-nez did not branch, so the method fell through to
    // `return false`.
    //
    // The EXP-058 "if-ltz INT32 hack" was a workaround for this same bug:
    // when byte 0x39 (intended: if-nez) was dispatched to execute_if_ltz,
    // we added special INT32 handling that made if-ltz behave like if-nez for
    // boolean returns. With the opcode table fixed, the hack is no longer
    // needed and is removed.
    constexpr uint16_t CMP_LONG = 0x31;       // cmp-long vAA, vBB, vCC (23x format)
    constexpr uint16_t IF_EQ = 0x32;          // if-eq vAA, vBB, +CCCC (22t format)
    constexpr uint16_t IF_NE = 0x33;          // if-ne vAA, vBB, +CCCC
    constexpr uint16_t IF_LT = 0x34;          // if-lt vAA, vBB, +CCCC
    constexpr uint16_t IF_GE = 0x35;          // if-ge vAA, vBB, +CCCC
    constexpr uint16_t IF_GT = 0x36;          // if-gt vAA, vBB, +CCCC
    constexpr uint16_t IF_LE = 0x37;          // if-le vAA, vBB, +CCCC
    constexpr uint16_t IF_EQZ = 0x38;         // if-eqz vAA, +BBBB (21t format)
    constexpr uint16_t IF_NEZ = 0x39;         // if-nez vAA, +BBBB
    constexpr uint16_t IF_LTZ = 0x3A;         // if-ltz vAA, +BBBB
    constexpr uint16_t IF_GEZ = 0x3B;         // if-gez vAA, +BBBB
    constexpr uint16_t IF_GTZ = 0x3C;          // if-gtz vAA, +BBBB
    constexpr uint16_t IF_LEZ = 0x3D;          // if-lez vAA, +BBBB

    // EXP-038 (BLOCKER-028): Arithmetic 2addr opcodes (12x format)
    // These are heavily used in real Android bytecode for local variable math.
    // EXP-059: Also fixed the same off-by-one here. Per AOSP:
    //   0xB0 add-int/2addr, 0xB1 sub-int/2addr, ..., 0xBA ushr-int/2addr
    //   0xBB add-long/2addr, 0xBC sub-long/2addr, ..., 0xC5 ushr-long/2addr
    //   0xC6 add-float/2addr, 0xC7 sub-float/2addr, ..., 0xCA rem-float/2addr
    //   0xCB add-double/2addr, 0xCC sub-double/2addr, ..., 0xCF div-double/2addr
    //   0xD0 rem-double/2addr
    constexpr uint16_t ADD_INT_2ADDR = 0xB0;    // add-int/2addr vA, vB
    constexpr uint16_t SUB_INT_2ADDR = 0xB1;    // sub-int/2addr vA, vB
    constexpr uint16_t MUL_INT_2ADDR = 0xB2;    // mul-int/2addr vA, vB
    constexpr uint16_t DIV_INT_2ADDR = 0xB3;    // div-int/2addr vA, vB
    constexpr uint16_t REM_INT_2ADDR = 0xB4;    // rem-int/2addr vA, vB
    constexpr uint16_t AND_INT_2ADDR = 0xB5;    // and-int/2addr vA, vB
    constexpr uint16_t OR_INT_2ADDR  = 0xB6;    // or-int/2addr vA, vB
    constexpr uint16_t XOR_INT_2ADDR = 0xB7;    // xor-int/2addr vA, vB
    constexpr uint16_t SHL_INT_2ADDR = 0xB8;    // shl-int/2addr vA, vB
    constexpr uint16_t SHR_INT_2ADDR = 0xB9;    // shr-int/2addr vA, vB
    constexpr uint16_t USHR_INT_2ADDR = 0xBA;   // ushr-int/2addr vA, vB

    // EXP-041: Long/float/double 2addr opcodes (12x format)
    constexpr uint16_t ADD_LONG_2ADDR = 0xBB;  // add-long/2addr vA, vB
    constexpr uint16_t SUB_LONG_2ADDR = 0xBC;  // sub-long/2addr
    constexpr uint16_t MUL_LONG_2ADDR = 0xBD;  // mul-long/2addr
    constexpr uint16_t DIV_LONG_2ADDR = 0xBE;  // div-long/2addr
    constexpr uint16_t REM_LONG_2ADDR = 0xBF;  // rem-long/2addr
    constexpr uint16_t AND_LONG_2ADDR = 0xC0;  // and-long/2addr
    constexpr uint16_t OR_LONG_2ADDR  = 0xC1;  // or-long/2addr
    constexpr uint16_t XOR_LONG_2ADDR = 0xC2; // xor-long/2addr
    constexpr uint16_t SHL_LONG_2ADDR = 0xC3;  // shl-long/2addr
    constexpr uint16_t SHR_LONG_2ADDR = 0xC4;  // shr-long/2addr
    constexpr uint16_t USHR_LONG_2ADDR = 0xC5; // ushr-long/2addr
    constexpr uint16_t ADD_FLOAT_2ADDR = 0xC6;  // add-float/2addr
    constexpr uint16_t SUB_FLOAT_2ADDR = 0xC7;  // sub-float/2addr
    constexpr uint16_t MUL_FLOAT_2ADDR = 0xC8;  // mul-float/2addr
    constexpr uint16_t DIV_FLOAT_2ADDR = 0xC9;  // div-float/2addr
    constexpr uint16_t REM_FLOAT_2ADDR = 0xCA;  // rem-float/2addr
    constexpr uint16_t ADD_DOUBLE_2ADDR = 0xCB; // add-double/2addr
    constexpr uint16_t SUB_DOUBLE_2ADDR = 0xCC; // sub-double/2addr
    constexpr uint16_t MUL_DOUBLE_2ADDR = 0xCD; // mul-double/2addr
    constexpr uint16_t DIV_DOUBLE_2ADDR = 0xCE; // div-double/2addr
    // PASS-3 FORENSIC CORRECTION (K-37): rem-double/2addr is 0xCF (AOSP).
    // The old value 0xD0 collided with ADD_INT_LIT16 (also 0xD0 there),
    // making one of the two unreachable.
    constexpr uint16_t REM_DOUBLE_2ADDR = 0xCF; // rem-double/2addr

    // Arithmetic lit8 (22b format: AA|op BB|CC)
    // PASS-3 FORENSIC CORRECTION (K-37): the ENTIRE lit8 table was still
    // SHIFTED +3 against AOSP after the Pass-2 "K-31 fix" — that fix had
    // corrected dispatch coverage but re-derived the byte values from the
    // same shifted table, and its fixture used the same header constants,
    // so it was self-consistent and could not catch the residual shift.
    // Corpus evidence (scan_lit8_opcodes.py, 6 APKs): real bytecode uses
    //   0xD8 add-int/lit8, 0xD9 rsub-int/lit8, 0xDA mul-int/lit8,
    //   0xDB div-int/lit8 (×2361), 0xDC rem-int/lit8, 0xDD and-int/lit8,
    //   0xDE or-int/lit8, 0xDF xor-int/lit8, 0xE0 shl-int/lit8 (×3399),
    //   0xE1 shr-int/lit8, 0xE2 ushr-int/lit8 — per AOSP dex_instruction_list.
    // NOTE: there are NO shl/shr/ushr-int/lit16 opcodes in Dalvik; the
    // Pass-2 "SHL/SHR/USHR_INT_LIT16" constants at 0xD8..0xDA were
    // inventions that collided with real add/rsub/mul-int/lit8.
    constexpr uint16_t ADD_INT_LIT8 = 0xD8;     // add-int/lit8 vAA, vBB, #+CC
    constexpr uint16_t RSUB_INT_LIT8 = 0xD9;    // rsub-int/lit8 (lit − vB)
    constexpr uint16_t MUL_INT_LIT8 = 0xDA;     // mul-int/lit8
    constexpr uint16_t DIV_INT_LIT8 = 0xDB;     // div-int/lit8
    constexpr uint16_t REM_INT_LIT8 = 0xDC;     // rem-int/lit8
    constexpr uint16_t AND_INT_LIT8 = 0xDD;     // and-int/lit8
    constexpr uint16_t OR_INT_LIT8  = 0xDE;     // or-int/lit8
    constexpr uint16_t XOR_INT_LIT8 = 0xDF;     // xor-int/lit8
    constexpr uint16_t SHL_INT_LIT8 = 0xE0;     // shl-int/lit8
    constexpr uint16_t SHR_INT_LIT8 = 0xE1;     // shr-int/lit8
    constexpr uint16_t USHR_INT_LIT8 = 0xE2;    // ushr-int/lit8

    // Arithmetic lit16 (22s format: AA|op BBBB)
    constexpr uint16_t ADD_INT_LIT16 = 0xD0;    // add-int/lit16 vA, vB, #+BBBB
    constexpr uint16_t RSUB_INT_LIT16 = 0xD1;     // rsub-int (reverse subtract)
    constexpr uint16_t MUL_INT_LIT16 = 0xD2;    // mul-int/lit16
    constexpr uint16_t DIV_INT_LIT16 = 0xD3;    // div-int/lit16
    constexpr uint16_t REM_INT_LIT16 = 0xD4;    // rem-int/lit16
    constexpr uint16_t AND_INT_LIT16 = 0xD5;    // and-int/lit16
    constexpr uint16_t OR_INT_LIT16  = 0xD6;    // or-int/lit16
    constexpr uint16_t XOR_INT_LIT16 = 0xD7;     // xor-int/lit16

    // Binary 23x format: AA|op BB|CC (3 registers)
    // EXP-059: Fixed off-by-one for INT binop range. Per AOSP:
    //   0x90 add-int, 0x91 sub-int, 0x92 mul-int, 0x93 div-int, 0x94 rem-int,
    //   0x95 and-int, 0x96 or-int, 0x97 xor-int, 0x98 shl-int, 0x99 shr-int,
    //   0x9A ushr-int, 0x9B add-long, ...
    // Previous code had ADD_INT=0x91 etc. (off by 1, because INT_TO_SHORT was
    // wrongly placed at 0x90 instead of 0x8F).
    constexpr uint16_t ADD_INT = 0x90;          // add-int vAA, vBB, vCC
    constexpr uint16_t SUB_INT = 0x91;          // sub-int vAA, vBB, vCC
    constexpr uint16_t MUL_INT = 0x92;          // mul-int vAA, vBB, vCC
    constexpr uint16_t DIV_INT = 0x93;          // div-int vAA, vBB, vCC
    constexpr uint16_t REM_INT = 0x94;          // rem-int vAA, vBB, vCC
    constexpr uint16_t AND_INT = 0x95;          // and-int vAA, vBB, vCC
    constexpr uint16_t OR_INT  = 0x96;          // or-int vAA, vBB, vCC
    constexpr uint16_t XOR_INT = 0x97;          // xor-int vAA, vBB, vCC
    constexpr uint16_t SHL_INT = 0x98;         // shl-int vAA, vBB, vCC
    constexpr uint16_t SHR_INT = 0x99;         // shr-int vAA, vBB, vCC
    constexpr uint16_t USHR_INT = 0x9A;        // ushr-int vAA, vBB, vCC

    // EXP-040: Missing opcodes discovered from Telegram execution
    // MASTER RECONCILIATION (2026-09-03, NOT_DONE #4 audit): the unary
    // neg/not family (12x format: B|A|op) was MISSING ENTIRELY — neither
    // constants nor dispatch cases existed, so any real APK executing
    // neg-* / not-* (hashing, Math.abs inlining, crypto) halted at
    // handle_unimplemented. AOSP layout:
    //   0x7B neg-int, 0x7C not-int, 0x7D neg-long, 0x7E not-long,
    //   0x7F neg-float, 0x80 neg-double
    constexpr uint16_t NEG_INT = 0x7B;         // neg-int vA, vB
    constexpr uint16_t NOT_INT = 0x7C;         // not-int vA, vB
    constexpr uint16_t NEG_LONG = 0x7D;        // neg-long vA, vB
    constexpr uint16_t NOT_LONG = 0x7E;        // not-long vA, vB
    constexpr uint16_t NEG_FLOAT = 0x7F;       // neg-float vA, vB
    constexpr uint16_t NEG_DOUBLE = 0x80;      // neg-double vA, vB

    // Conversion opcodes (12x format: B|A|op, 1 code unit)
    // EXP-059: Fixed off-by-one for conversion range. Per AOSP:
    //   0x81 int-to-long, 0x82 int-to-float, 0x83 int-to-double,
    //   0x84 long-to-int, 0x85 long-to-float, 0x86 long-to-double,
    //   0x87 float-to-int, 0x88 float-to-long, 0x89 float-to-double,
    //   0x8A double-to-int, 0x8B double-to-long, 0x8C double-to-float,
    //   0x8D int-to-byte, 0x8E int-to-char, 0x8F int-to-short
    constexpr uint16_t INT_TO_LONG = 0x81;     // int-to-long vA, vB
    constexpr uint16_t INT_TO_FLOAT = 0x82;    // int-to-float vA, vB
    constexpr uint16_t INT_TO_DOUBLE = 0x83;    // int-to-double vA, vB
    constexpr uint16_t LONG_TO_INT = 0x84;     // long-to-int vA, vB
    constexpr uint16_t LONG_TO_FLOAT = 0x85;   // long-to-float vA, vB
    constexpr uint16_t LONG_TO_DOUBLE = 0x86;  // long-to-double vA, vB
    constexpr uint16_t FLOAT_TO_INT = 0x87;    // float-to-int vA, vB
    constexpr uint16_t FLOAT_TO_LONG = 0x88;   // float-to-long vA, vB
    constexpr uint16_t FLOAT_TO_DOUBLE = 0x89; // float-to-double vA, vB
    constexpr uint16_t DOUBLE_TO_INT = 0x8A;   // double-to-int vA, vB
    constexpr uint16_t DOUBLE_TO_LONG = 0x8B;  // double-to-long vA, vB
    constexpr uint16_t DOUBLE_TO_FLOAT = 0x8C; // double-to-float vA, vB
    constexpr uint16_t INT_TO_BYTE = 0x8D;     // int-to-byte vA, vB
    constexpr uint16_t INT_TO_CHAR = 0x8E;     // int-to-char vA, vB
    constexpr uint16_t INT_TO_SHORT = 0x8F;    // int-to-short vA, vB

    // Float/Double arithmetic (23x format: AA|op BB|CC, 2 code units)
    // EXP-059: Fixed off-by-one for cmp-* opcodes too. Per AOSP:
    //   0x2B packed-switch, 0x2C sparse-switch
    //   0x2D cmpl-float, 0x2E cmpg-float, 0x2F cmpl-double, 0x30 cmpg-double, 0x31 cmp-long
    // Previous code had all values shifted by 1 (CMPL_FLOAT=0x2C etc.).
    // The duplicate CMP_LONG=0x31 at line 206 is the AOSP-correct one; this
    // block now uses the same values for cmpl-float etc.
    constexpr uint16_t PACKED_SWITCH = 0x2B;   // packed-switch vAA, +BBBB (31t format)
    constexpr uint16_t SPARSE_SWITCH = 0x2C;   // sparse-switch vAA, +BBBB (31t format)
    constexpr uint16_t CMPL_FLOAT = 0x2D;      // cmpl-float vAA, vBB, vCC
    constexpr uint16_t CMPG_FLOAT = 0x2E;      // cmpg-float vAA, vBB, vCC
    constexpr uint16_t CMPL_DOUBLE = 0x2F;     // cmpl-double vAA, vBB, vCC
    constexpr uint16_t CMPG_DOUBLE = 0x30;    // cmpg-double vAA, vBB, vCC
    // CMP_LONG = 0x31 is defined above (next to the IF_* opcodes).
    constexpr uint16_t ADD_FLOAT = 0xA6;        // add-float vAA, vBB, vCC (was 0xA7, AOSP-corrected)
    constexpr uint16_t SUB_FLOAT = 0xA7;        // sub-float vAA, vBB, vCC
    constexpr uint16_t MUL_FLOAT = 0xA8;        // mul-float vAA, vBB, vCC (AOSP-corrected)
    constexpr uint16_t DIV_FLOAT = 0xA9;        // div-float vAA, vBB, vCC
    constexpr uint16_t REM_FLOAT = 0xAA;        // rem-float vAA, vBB, vCC
    constexpr uint16_t ADD_DOUBLE = 0xAB;       // add-double vAA, vBB, vCC
    constexpr uint16_t SUB_DOUBLE = 0xAC;       // sub-double vAA, vBB, vCC
    constexpr uint16_t MUL_DOUBLE = 0xAD;       // mul-double vAA, vBB, vCC
    constexpr uint16_t DIV_DOUBLE = 0xAE;       // div-double vAA, vBB, vCC
    constexpr uint16_t REM_DOUBLE = 0xAF;       // rem-double vAA, vBB, vCC (was 0xB0, AOSP-corrected)

    // Long arithmetic (23x format)
    constexpr uint16_t ADD_LONG = 0x9B;         // add-long vAA, vBB, vCC
    constexpr uint16_t SUB_LONG = 0x9C;         // sub-long vAA, vBB, vCC
    constexpr uint16_t MUL_LONG = 0x9D;         // mul-long vAA, vBB, vCC
    constexpr uint16_t DIV_LONG = 0x9E;         // div-long vAA, vBB, vCC
    constexpr uint16_t REM_LONG = 0x9F;         // rem-long vAA, vBB, vCC
    constexpr uint16_t AND_LONG = 0xA0;         // and-long vAA, vBB, vCC
    constexpr uint16_t OR_LONG = 0xA1;          // or-long vAA, vBB, vCC
    constexpr uint16_t XOR_LONG = 0xA2;         // xor-long vAA, vBB, vCC
    constexpr uint16_t SHL_LONG = 0xA3;         // shl-long vAA, vBB, vCC
    constexpr uint16_t SHR_LONG = 0xA4;         // shr-long vAA, vBB, vCC
    constexpr uint16_t USHR_LONG = 0xA5;        // ushr-long vAA, vBB, vCC

    // EXP-040: Conversion opcodes already defined above, just add dispatch cases
}

// ============================================================================
// VALUE TYPES — Extended Register Value System
// ============================================================================

enum class DalvikType {
    UNINITIALIZED,
    INT32,
    INT64,      // Long
    FLOAT32,
    FLOAT64,    // Double
    STRING_REF,
    CLASS_REF,
    OBJECT_REF,
    NULL_REF,
    BOOLEAN,
    BYTE,
    SHORT,
    CHAR,
    VOID_,
    REGISTER_UNSET
};

// ─── F-NEW-381 STRUCTURAL LEVER (CONT-32): out-of-band COW string cell ─────
// DalvikValue carried TWO by-value std::string members (~112B per value);
// every register read/write copied both (~60-90M copies per dooz run — the
// measured F-NEW-381 throughput-wall constant: cost is the per-instruction
// value-copy constant, not any single method). CowStr stores the string
// out-of-band in a refcounted cell: copy = one 8B pointer (+ an atomic inc
// ONLY when a cell exists); unset cells (non-ref values — the vast majority
// of interpreter traffic) are a null pointer with ZERO atomics and zero
// string ctor/dtor churn. VALUE-IDENTICAL BY CONSTRUCTION: every read
// returns the same string content as the old by-value member.
struct StrCell {
    mutable std::atomic<int64_t> rc;
    std::string s;
    explicit StrCell(std::string&& v) : rc(1), s(std::move(v)) {}
    explicit StrCell(const std::string& v) : rc(1), s(v) {}
};

class CowStr {
public:
    CowStr() = default;
    // Converting ctors (non-explicit): let `cond ? cowstr : "literal"`
    // ternaries find a common type (the char array converts to CowStr);
    // conversions FROM CowStr remain exactly one (operator const string&),
    // so no new overload ambiguity is created anywhere.
    CowStr(std::string s) { if (!s.empty()) cell_ = new StrCell(std::move(s)); }
    CowStr(const char* s) : cell_(nullptr) {
        if (s && *s) cell_ = new StrCell(std::string(s));
    }
    CowStr(const CowStr& o) noexcept : cell_(o.cell_) {
        if (cell_) cell_->rc.fetch_add(1, std::memory_order_relaxed);
    }
    CowStr(CowStr&& o) noexcept : cell_(o.cell_) { o.cell_ = nullptr; }
    CowStr& operator=(const CowStr& o) noexcept {
        if (this != &o) {
            release();
            cell_ = o.cell_;
            if (cell_) cell_->rc.fetch_add(1, std::memory_order_relaxed);
        }
        return *this;
    }
    CowStr& operator=(CowStr&& o) noexcept {
        if (this != &o) { release(); cell_ = o.cell_; o.cell_ = nullptr; }
        return *this;
    }
    ~CowStr() { release(); }

    // Mutation sites (census: whole-string assignment only — the 1605
    // member-access sites never mutate the buffer in place).
    CowStr& operator=(const std::string& s) { assign(s); return *this; }
    CowStr& operator=(const char* s) {
        if (s && *s) assign(std::string(s)); else reset_to_empty();
        return *this;
    }

    // Implicit conversion keeps every read site source-compatible:
    // comparisons, map finds, concatenation, nlohmann json, std::to_string.
    operator const std::string&() const {
        static const std::string kEmpty;
        return cell_ ? cell_->s : kEmpty;
    }

    // Const forwarding — the exact method surface of the member-access
    // census: size/length/empty/c_str/data/back/substr/find/operator[]/at.
    size_t size() const { return cell_ ? cell_->s.size() : 0; }
    size_t length() const { return size(); }
    bool empty() const { return !cell_ || cell_->s.empty(); }
    const char* c_str() const { return cell_ ? cell_->s.c_str() : ""; }
    const char* data() const { return c_str(); }
    char back() const { return cell_ ? cell_->s.back() : '\0'; }
    char operator[](size_t i) const { return cell_ ? cell_->s[i] : '\0'; }
    char at(size_t i) const { return cell_ ? cell_->s.at(i) : '\0'; }
    std::string substr(size_t pos = 0, size_t n = std::string::npos) const {
        return static_cast<const std::string&>(*this).substr(pos, n);
    }
    size_t find(const std::string& needle, size_t pos = 0) const {
        return static_cast<const std::string&>(*this).find(needle, pos);
    }
    size_t find(const char* needle, size_t pos = 0) const {
        return static_cast<const std::string&>(*this).find(needle, pos);
    }
    size_t find(char c, size_t pos = 0) const {
        return static_cast<const std::string&>(*this).find(c, pos);
    }
    size_t rfind(const std::string& needle, size_t pos = std::string::npos) const {
        return static_cast<const std::string&>(*this).rfind(needle, pos);
    }
    size_t rfind(const char* needle, size_t pos = std::string::npos) const {
        return static_cast<const std::string&>(*this).rfind(needle, pos);
    }
    size_t rfind(char c, size_t pos = std::string::npos) const {
        return static_cast<const std::string&>(*this).rfind(c, pos);
    }

private:
    void assign(const std::string& s) {
        if (cell_) {
            if (cell_->rc.load(std::memory_order_relaxed) == 1) {
                cell_->s = s;   // unique owner: mutate in place
                return;
            }
            release();          // shared: drop our ref, fall through to clone
        }
        if (!s.empty()) cell_ = new StrCell(s);   // empty string = null cell
    }
    void reset_to_empty() {
        if (cell_) {
            if (cell_->rc.load(std::memory_order_relaxed) == 1) {
                cell_->s.clear();
                return;
            }
            release();
        }
    }
    void release() {
        if (cell_ && cell_->rc.fetch_sub(1, std::memory_order_acq_rel) == 1)
            delete cell_;
        cell_ = nullptr;
    }
    StrCell* cell_ = nullptr;
};

// ── CowStr free operators (ADL law) ────────────────────────────────────────
// std::string's free operator+/operator<< live in namespace std and are only
// reachable via ADL when an operand IS a std type — CowStr (miniandroid::
// dalvik) never drags them in, so the mixed-shape concat/compare sites fail
// to compile on conversion alone. This set covers every census shape with an
// exact-match candidate (no ambiguity against std's operator set: whenever a
// std operand IS present, these exact-match overloads win outright).
inline std::string operator+(const CowStr& a, const CowStr& b) {
    return static_cast<const std::string&>(a) + static_cast<const std::string&>(b);
}
inline std::string operator+(const CowStr& a, const std::string& b) {
    return static_cast<const std::string&>(a) + b;
}
inline std::string operator+(const std::string& a, const CowStr& b) {
    return a + static_cast<const std::string&>(b);
}
inline std::string operator+(const CowStr& a, const char* b) {
    return static_cast<const std::string&>(a) + b;
}
inline std::string operator+(const char* a, const CowStr& b) {
    return a + static_cast<const std::string&>(b);
}
inline std::string operator+(const CowStr& a, char b) {
    return static_cast<const std::string&>(a) + b;
}
inline std::string operator+(char a, const CowStr& b) {
    return a + static_cast<const std::string&>(b);
}
inline std::ostream& operator<<(std::ostream& os, const CowStr& v) {
    return os << static_cast<const std::string&>(v);
}
inline bool operator==(const CowStr& a, const CowStr& b) {
    return static_cast<const std::string&>(a) == static_cast<const std::string&>(b);
}
inline bool operator==(const CowStr& a, const std::string& b) {
    return static_cast<const std::string&>(a) == b;
}
inline bool operator==(const std::string& a, const CowStr& b) {
    return a == static_cast<const std::string&>(b);
}
inline bool operator==(const CowStr& a, const char* b) {
    return static_cast<const std::string&>(a) == b;
}
inline bool operator==(const char* a, const CowStr& b) {
    return a == static_cast<const std::string&>(b);
}
inline bool operator!=(const CowStr& a, const CowStr& b) {
    return static_cast<const std::string&>(a) != static_cast<const std::string&>(b);
}
inline bool operator!=(const CowStr& a, const std::string& b) {
    return static_cast<const std::string&>(a) != b;
}
inline bool operator!=(const std::string& a, const CowStr& b) {
    return a != static_cast<const std::string&>(b);
}
inline bool operator!=(const CowStr& a, const char* b) {
    return static_cast<const std::string&>(a) != b;
}
inline bool operator!=(const char* a, const CowStr& b) {
    return a != static_cast<const std::string&>(b);
}

struct DalvikValue {
    DalvikType type = DalvikType::REGISTER_UNSET;
    
    union {
        int32_t int_val = 0;
        int64_t long_val;
        float float_val;
        double double_val;
        bool bool_val;
        int8_t byte_val;
        int16_t short_val;
        char char_val;
    };
    
    // Reference types — F-NEW-381 structural lever (CONT-32): out-of-band
    // COW cells (CowStr above). Value-identical; register copies are 8B.
    CowStr string_val;            // For STRING_REF
    CowStr class_desc;            // For CLASS_REF or OBJECT_REF
    uint32_t object_id = 0;       // For OBJECT_REF
    uint32_t ref_id = 0;          // Unique reference ID
    
    bool is_null = false;
    
    // Factory methods
    static DalvikValue make_int(int32_t val) {
        DalvikValue v; v.type = DalvikType::INT32; v.int_val = val; return v;
    }
    
    static DalvikValue make_long(int64_t val) {
        DalvikValue v; v.type = DalvikType::INT64; v.long_val = val; return v;
    }
    
    static DalvikValue make_string(const std::string& str, uint32_t id) {
        DalvikValue v; v.type = DalvikType::STRING_REF; 
        v.string_val = str; v.ref_id = id; return v;
    }
    
    static DalvikValue make_object(uint32_t obj_id, const std::string& cls) {
        DalvikValue v; v.type = DalvikType::OBJECT_REF;
        v.object_id = obj_id; v.class_desc = cls; return v;
    }
    
    static DalvikValue make_class(const std::string& desc, uint32_t id) {
        DalvikValue v; v.type = DalvikType::CLASS_REF;
        v.class_desc = desc; v.ref_id = id; return v;
    }
    
    static DalvikValue make_null() {
        DalvikValue v; v.type = DalvikType::NULL_REF; v.is_null = true; return v;
    }
    
    static DalvikValue make_uninit() {
        DalvikValue v; v.type = DalvikType::UNINITIALIZED; return v;
    }
    
    static DalvikValue make_void() {
        DalvikValue v; v.type = DalvikType::VOID_; return v;
    }
    
    static DalvikValue make_bool(bool b) {
        DalvikValue v; v.type = DalvikType::BOOLEAN; v.bool_val = b; return v;
    }

    static DalvikValue make_float(float f) {
        DalvikValue v; v.type = DalvikType::FLOAT32; v.float_val = f; return v;
    }

    static DalvikValue make_double(double d) {
        DalvikValue v; v.type = DalvikType::FLOAT64; v.double_val = d; return v;
    }

    static DalvikValue make_byte(int8_t b) {
        DalvikValue v; v.type = DalvikType::BYTE; v.byte_val = b; return v;
    }

    static DalvikValue make_short(int16_t s) {
        DalvikValue v; v.type = DalvikType::SHORT; v.short_val = s; return v;
    }

    static DalvikValue make_char(char c) {
        DalvikValue v; v.type = DalvikType::CHAR; v.char_val = c; return v;
    }
    
    std::string to_string() const;
    json to_json() const;
    
    bool is_integral() const {
        return type == DalvikType::INT32 || type == DalvikType::INT64 ||
               type == DalvikType::BOOLEAN || type == DalvikType::BYTE ||
               type == DalvikType::SHORT || type == DalvikType::CHAR;
    }
    
    bool is_reference() const {
        return type == DalvikType::STRING_REF || type == DalvikType::OBJECT_REF ||
               type == DalvikType::CLASS_REF || type == DalvikType::NULL_REF;
    }
};

// ============================================================================
// REGISTER FILE — Dalvik Virtual Machine Registers
// ============================================================================

class DexRegisterFile {
public:
    DexRegisterFile() : size_(0), pc_(0) {}
    
    void initialize(uint32_t count, uint32_t ins_count = 0) {
        size_ = count;
        ins_count_ = ins_count;
        registers_.clear();
        registers_.resize(count, DalvikValue::make_uninit());
        // FINAL-CAMPAIGN item 21-REG-5 (written-set metadata law): the
        // written-register bitmap is metadata ONLY (zero semantic consumers —
        // get_written_registers() has no call sites in the runtime). It is
        // now DYNAMICALLY SIZED to the register count so the F-NEW-171
        // width family (uint8/uint16 truncation, bits silently dropped past
        // a fixed word count) can never re-enter through diagnostics.
        written_bits_.assign(((size_t)count + 63) / 64 + 1, 0ULL);
        
        // Mark parameter registers (last N registers are 'p' registers)
        // EXP-058: CRITICAL FIX — was `ins_count < count` which failed when
        // ins_count == count (all registers are parameters). This caused
        // param_start_ = count, making all write_p() calls go to non-existent
        // registers, silently dropping all parameter values.
        if (ins_count > 0 && ins_count <= count) {
            param_start_ = count - ins_count;
        } else {
            param_start_ = count;
        }
    }
    
    // FINAL-CAMPAIGN PHASE 3 (register width law): DEX register numbers are
    // UNSIGNED 16-BIT in the /16 and /range instruction formats (DEX spec:
    // "vAAAA"); R8 emits them precisely when a method needs more than 255
    // registers. The file already resizes to any count — only the accessor
    // width truncated v256+ onto v0.., aliasing live registers.
    void write_v(uint16_t reg, const DalvikValue& value) {
        if (reg < size_) {
            registers_[reg] = value;
            // F-109a (S62): written-set as a fixed bitmap — the old
            // std::set<uint8_t> did a red-black tree insert PER REGISTER
            // WRITE (the hot path writes 2-5 registers per instruction).
            // Same ordered iteration semantics for get_written_registers().
            if ((reg >> 6) < written_bits_.size())
                written_bits_[reg >> 6] |= (1ULL << (reg & 63));
        }
    }
    
    void write_p(uint8_t param_idx, const DalvikValue& value) {
        // FINAL-CAMPAIGN PHASE 3 (register width law): the ABSOLUTE register
        // is param_start_ + idx — for methods with >255 registers param_start_
        // exceeds uint8_t and the sum TRUNCATED, landing arguments (incl.
        // `this`) in wrong registers (measured: WhatsApp LX/07r;.<init> →
        // "invoke LX/00D;.<init> on a null object reference").
        uint32_t reg = static_cast<uint32_t>(param_start_) + param_idx;
        if (reg < size_) {
            registers_[reg] = value;
            if ((reg >> 6) < written_bits_.size())
                written_bits_[reg >> 6] |= (1ULL << (reg & 63));
        }
    }
    
    DalvikValue read_v(uint16_t reg) const {
        if (reg < size_) return registers_[reg];
        return DalvikValue::make_uninit();
    }
    
    DalvikValue read_p(uint8_t param_idx) const {
        uint32_t reg = static_cast<uint32_t>(param_start_) + param_idx;
        if (reg < size_) return registers_[reg];
        return DalvikValue::make_uninit();
    }
    
    void set_pc(uint32_t pc) { pc_ = pc; }
    uint32_t get_pc() const { return pc_; }
    
    uint32_t get_size() const { return size_; }
    uint32_t get_ins_count() const { return ins_count_; }
    
    std::vector<uint16_t> get_written_registers() const {
        // F-109a: iterate the bitmap in ascending register order (identical
        // output to the old ordered set). 21-REG-5: uint16_t — register
        // numbers are 16-bit (DEX /16 formats); the old uint8_t return
        // WRAPPED every register >= 256 in the diagnostics it fed.
        std::vector<uint16_t> out;
        for (uint32_t w = 0; w < written_bits_.size(); ++w) {
            if (w * 64ULL >= size_) break;
            uint64_t bits = written_bits_[w];
            while (bits) {
                unsigned b = (unsigned)(__builtin_ctzll(bits));
                uint32_t r = w * 64 + b;
                if (r < size_) out.push_back((uint16_t)r);
                bits &= bits - 1;
            }
        }
        return out;
    }
    
    json dump() const {
        json result;
        result["size"] = size_;
        result["ins_count"] = ins_count_;
        result["param_start"] = param_start_;
        result["pc"] = pc_;
        result["registers"] = json::array();
        
        for (uint32_t i = 0; i < size_; ++i) {
            json entry;
            bool is_param = (i >= param_start_);
            entry["name"] = is_param ? ("p" + std::to_string(i - param_start_)) 
                                     : ("v" + std::to_string(i));
            entry["index"] = i;
            entry["value"] = registers_[i].to_json();
            entry["written"] = ((i >> 6) < written_bits_.size() &&
                                ((written_bits_[i >> 6] >> (i & 63)) & 1ULL) != 0);
            result["registers"].push_back(entry);
        }
        return result;
    }
    
    std::map<std::string, DalvikValue> get_snapshot() const {
        std::map<std::string, DalvikValue> snap;
        for (uint32_t i = 0; i < size_; ++i) {
            bool is_param = (i >= param_start_);
            std::string name = is_param ? ("p" + std::to_string(i - param_start_)) 
                                       : ("v" + std::to_string(i));
            snap[name] = registers_[i];
        }
        return snap;
    }

private:
    uint32_t size_ = 0;
    uint32_t ins_count_ = 0;
    uint32_t param_start_ = 0;
    uint32_t pc_ = 0;
    std::vector<DalvikValue> registers_;
    // F-109a: written-register bitmap — 21-REG-5: dynamically sized to the
    // register count (metadata only; zero semantic consumers).
    std::vector<uint64_t> written_bits_;
};

// ============================================================================
// STACK FRAME — Method Call Context
// ============================================================================

struct StackFrame {
    uint32_t frame_id;
    std::string class_name;
    std::string method_name;
    std::string method_descriptor;
    std::string source_file;
    
    // Execution state
    uint32_t return_address = 0xFFFFFFFF;  // PC to return to
    uint32_t caller_pc = 0;                // PC of call instruction
    DalvikValue return_value;              // Return value register
    
    // Register file for this frame
    DexRegisterFile registers;
    
    // Method metadata
    uint32_t code_offset = 0;
    uint32_t bytecode_length = 0;
    uint32_t registers_size = 0;
    uint32_t ins_size = 0;
    uint32_t outs_size = 0;
    
    // Timing
    Clock::time_point enter_time;
    Clock::time_point exit_time;
    double duration_ms = 0;
    
    // Status
    enum class Status {
        ACTIVE,
        RETURNED,
        EXCEPTION_PENDING,
        HALTED
    } status = Status::ACTIVE;
    
    std::string halt_reason;
    
    json to_json() const {
        json frame;
        frame["frame_id"] = frame_id;
        frame["class"] = class_name;
        frame["method"] = method_name;
        frame["descriptor"] = method_descriptor;
        frame["return_address"] = std::string("0x") + 
            ([&]() { std::ostringstream o; o << std::hex << return_address; return o.str(); })();
        frame["caller_pc"] = caller_pc;
        frame["status"] = status == Status::ACTIVE ? "ACTIVE" :
                           status == Status::RETURNED ? "RETURNED" :
                           status == Status::EXCEPTION_PENDING ? "EXCEPTION" : "HALTED";
        frame["duration_ms"] = duration_ms;
        frame["registers"] = registers.dump();
        return frame;
    }
};

// ============================================================================
// HEAP OBJECT — Runtime Object Representation
// ============================================================================

struct HeapObject {
    uint32_t object_id = 0;
    std::string class_descriptor;   // Landroid/widget/TextView;
    // S166-Z3 (CONT-42 train): the per-object readable_class member is GONE.
    // Census 2026-11-05: its ONLY consumer was to_json() (heap report) — every
    // other `readable_class` in the tree belongs to the ClassResolution Trace
    // struct (class_resolver.h:32 / dex_interpreter_batch.h:199). Removing the
    // member kills one string transform (substr alloc) AND one heap string
    // (~64B for app-class names) PER ALLOCATION; to_json() derives it
    // on demand, so the report content is byte-identical.
    
    bool initialized = false;
    uint64_t creation_sequence = 0;
    uint32_t creator_pc = 0;
    uint32_t creator_frame_id = 0;
    
    // Fields (F-NEW-381 phase 2: unordered — the interpreter hot path
    // is find/operator[] only; frozen ordered consumers sort keys
    // explicitly, preserving the historical std::map iteration law)
    std::unordered_map<std::string, DalvikValue> fields;
    
    // Bridge to Android API stub
    std::shared_ptr<api::AndroidObject> api_object;

    // R-NEW-548 (CONT-38): the dense array backing store (see set_field).
    bool is_array = false;
    int32_t array_length = 0;                 // capacity hint (grow-on-write)
    std::vector<DalvikValue> array_store;     // dense elements, unset = REGISTER_UNSET
    
    HeapObject() = default;
    
    HeapObject(uint32_t id, const std::string& desc, uint64_t seq, uint32_t pc, uint32_t frame)
        : object_id(id), class_descriptor(desc), creation_sequence(seq), 
          creator_pc(pc), creator_frame_id(frame) {
        // S166-Z3: readable_class derived on demand in to_json() only.
    }
    
    void set_field(const std::string& name, const DalvikValue& value) {
        // R-NEW-548 (CONT-38): TYPED ARRAY BACKING — array elements no longer
        // land in the fields map. The per-index "array[N]" string keys cost
        // ~110-140B of map-node+key overhead PER ELEMENT (unordered_map node
        // + heap string key + DalvikValue) — a 1MB byte[] inflated to
        // ~140MB. Telegram's startup (SVG/SQLite/crypto/network buffers)
        // materializes MB-scale arrays: the +2.7GB execute_application bulk
        // (run/cont39 ENGINE-MEM: glibc in-use only ~350MB vs RSS 2.85GB —
        // the rest was live map nodes behind ~13K heap objects). Elements
        // now live in a DENSE DalvikValue vector; the "array[N]" field-name
        // API (184 engine call sites) is an adapter. The length channels
        // (__array_length__ / __new_array_length__) stay ordinary map
        // fields — one entry per array, zero behavior change there.
        int32_t ai;
        if (parse_array_index(name, ai)) {
            is_array = true;
            if (ai >= 0) {
                if (ai >= array_length) {
                    array_length = ai + 1;
                    if ((int32_t)array_store.size() < array_length)
                        array_store.resize(array_length);
                }
                array_store[ai] = value;
            }
            return;
        }
        fields[name] = value;
    }

    DalvikValue get_field(const std::string& name) const {
        int32_t ai;
        if (parse_array_index(name, ai)) {
            if (is_array && ai >= 0 && ai < (int32_t)array_store.size())
                return array_store[ai];
            return DalvikValue::make_uninit();
        }
        auto it = fields.find(name);
        return (it != fields.end()) ? it->second : DalvikValue::make_uninit();
    }

    // R-NEW-548: array-shaped field-name test + index extraction.
    static bool parse_array_index(const std::string& name, int32_t& out) {
        if (name.size() < 7 || name.compare(0, 6, "array[") != 0)
            return false;
        if (name.back() != ']') return false;
        out = (int32_t)strtol(name.c_str() + 6, nullptr, 10);
        return true;
    }
    
    json to_json() const {
        json obj;
        obj["object_id"] = object_id;
        obj["class_descriptor"] = class_descriptor;
        obj["readable_class"] = descriptor_to_readable(class_descriptor);
        obj["initialized"] = initialized;
        obj["creation_sequence"] = creation_sequence;
        obj["creator_pc"] = creator_pc;
        obj["creator_frame_id"] = creator_frame_id;
        obj["field_count"] = fields.size();
        return obj;
    }

private:
    std::string descriptor_to_readable(const std::string& desc) const {
        if (desc.empty()) return desc;
        std::string result = desc;
        if (result[0] == 'L' && result.back() == ';') {
            result = result.substr(1, result.size() - 2);
        }
        for (char& c : result) { if (c == '/') c = '.'; }
        return result;
    }
};

// ============================================================================
// OBJECT HEAP — Dynamic Memory Management
// ============================================================================

class DalvikHeap {
public:
    DalvikHeap() : next_id_(1), alloc_sequence_(0), allocation_log_cap_(1000) {}
    
    // EXP-042 Phase 1: cap the allocation log ring buffer.
    void set_allocation_log_cap(size_t cap) { allocation_log_cap_ = cap; }

    // ── F-NEW-251 (CONT-7 §13A) — SHARED FIELD-IDENTITY RESOLVER ──────────
    // LAW: every heap instance-field access that bypasses the interpreter
    // (shadow hooks: Atomic*FieldUpdater family, future consumers) MUST land
    // in the SAME storage slot the interpreter's iput/iget use — the S134
    // F-NEW-160 qualified key "<declarer>-><name>" for DEX-declared fields.
    // The engine installs a resolver; the heap applies it centrally so every
    // consumer is fixed at once (no per-shadow key logic to drift).
    // Resolver contract: (receiver runtime class, bare field name) → storage
    // key; returns "" = keep the bare key (engine-synthetic fields:
    // "ordinal", "array[i]", "__array_length__", framework-owned objects,
    // or any name that is not a DEX-declared instance field).
    using FieldKeyResolver = std::function<std::string(
        const std::string& class_desc, const std::string& bare_name)>;
    void set_field_key_resolver(FieldKeyResolver resolver) {
        field_key_resolver_ = std::move(resolver);
    }
    // Bare-name guard shared by get/set: synthetic/engine shapes never
    // participate in qualified resolution.
    static bool is_resolvable_bare_name(const std::string& name) {
        if (name.empty()) return false;
        if (name.find("->") != std::string::npos) return false;  // qualified
        if (name.rfind("__", 0) == 0) return false;              // engine meta
        if (name.find("array[") != std::string::npos) return false; // arrays
        return true;
    }
    
    uint32_t allocate(const std::string& class_desc, uint32_t pc, uint32_t frame_id) {
        // R-NEW-555 (CONT-42 TRAIN 4): CONSTRUCT IN PLACE — the old form
        // built a local HeapObject then `objects_[oid] = obj` COPIED the
        // whole object (class_descriptor + readable_class + the ENTIRE
        // fields unordered_map + array_store vector + api_object
        // shared_ptr) once per allocation. gprof (TRAIN 3, -fno-icf build):
        // HeapObject COPY-CTOR 5,490,924 calls in the dooz 60s window —
        // exactly one per allocate() call (5.5M allocations/run), i.e.
        // every allocation paid a full deep copy of an always-empty fields
        // map plus two strings. try_emplace constructs the HeapObject
        // DIRECTLY in the map node (zero copies). Generic engine law — no
        // app knowledge, semantics identical (same id, same seq, same
        // readable_class derivation, same census/trace/log rows).
        const uint32_t oid = next_id_++;
        const uint64_t seq = alloc_sequence_++;
        HeapObject& obj =
            objects_.try_emplace(oid, oid, class_desc, seq, pc, frame_id)
                .first->second;
        // F-NEW-542: env-gated live allocation histogram (see the member
        // comment). One cached-branch load per allocation when unset.
        if (heap_census_enabled()) note_alloc_class(class_desc);
        // CONT-28 (generic diagnostic): env-gated allocation trace. When
        // MINIANDROID_ALLOC_TRACE names a class-descriptor substring, every
        // heap allocation whose class matches logs object_id + class + pc +
        // frame_id to stderr (bounded 200). Read-only, zero app knowledge —
        // names the ENGINE allocation site for ctor-skip faces (AOSP law:
        // an object whose <init> never ran must be identifiable).
        {
            static thread_local const char* alloc_trace_env =
                getenv("MINIANDROID_ALLOC_TRACE");
            if (alloc_trace_env && *alloc_trace_env &&
                !class_desc.empty() &&
                class_desc.find(alloc_trace_env) != std::string::npos) {
                static thread_local uint64_t alloc_trace_n = 0;
                if (alloc_trace_n < 200) {
                    fprintf(stderr,
                            "[ALLOC-TRACE] obj#%u %s pc=%u frame=%u seq=%llu\n",
                            oid, class_desc.c_str(), pc, frame_id,
                            (unsigned long long)seq);
                    ++alloc_trace_n;
                }
            }
        }
        
        // EXP-042 Phase 1: ring-buffer the allocation log. Each json entry is
        // ~256 B; uncapped, 10 M allocations would consume 2.5 GB. With cap=1000
        // we keep the last 1 000 allocations (~256 KB) — enough for diagnostic
        // purposes.
        //
        // S166-Z1 (CONT-42 train): the log is WRITE-ONLY — read-back census
        // 2026-11-05: get_allocation_log() has ZERO callers in src/ and
        // heap.dump() (the only report path) returns the object array, never
        // the log. Every allocate() paid a 4-entry nlohmann json build
        // (~5 heap allocations) plus an O(cap) vector erase — 5.5M dead json
        // builds per dooz 60s window (R-NEW-555 census). Default OFF;
        // MINIANDROID_ALLOC_LOG=1 restores the historical diagnostic exactly.
        if (allocation_log_cap_ > 0 && alloc_log_enabled()) {
            if (allocation_log_.size() >= allocation_log_cap_) {
                // nlohmann::json::array() uses a vector internally; erase from
                // the front is O(N) but N=1000 is trivial.
                allocation_log_.erase(allocation_log_.begin());
            }
            allocation_log_.push_back({
                {"object_id", oid},
                {"class", class_desc},
                {"pc", pc},
                {"frame_id", frame_id},
                {"sequence", seq}
            });
        }
        
        return oid;
    }
    
    HeapObject* get(uint32_t id) {
        auto it = objects_.find(id);
        return (it != objects_.end()) ? &it->second : nullptr;
    }
    
    const HeapObject* get(uint32_t id) const {
        auto it = objects_.find(id);
        return (it != objects_.end()) ? &it->second : nullptr;
    }
    
    void mark_initialized(uint32_t id) {
        if (auto* obj = get(id)) obj->initialized = true;
    }
    
    void bind_api_object(uint32_t id, std::shared_ptr<api::AndroidObject> api_obj) {
        if (auto* obj = get(id)) obj->api_object = api_obj;
    }
    
    size_t size() const { return objects_.size(); }
    
    // ── F-NEW-542 (CONT-37): INCREMENTAL PER-CLASS ALLOCATION HISTOGRAM ────
    // Env-gated (MINIANDROID_HEAP_CENSUS): the interpreter's progress
    // sampler emits the live top-K class counts + object population so an
    // unbounded-heap face (telegram RSS 2.9GB@15s → container OOM rc=137,
    // the CONT-36-named #1 structural lever) names its TOP ALLOCATOR
    // live — no SIGKILL flush loss. Maintained ONLY when the env is set
    // (heap_census_enabled(), cached once) so the default run pays one
    // cached-branch load per allocation, zero map work.
    static bool heap_census_enabled() {
        static const bool on = std::getenv("MINIANDROID_HEAP_CENSUS") != nullptr;
        return on;
    }
    // S166-Z1: allocation-log opt-in (default OFF — the log is a write-only
    // diagnostic; MINIANDROID_ALLOC_LOG=1 restores it exactly).
    static bool alloc_log_enabled() {
        static const bool on = std::getenv("MINIANDROID_ALLOC_LOG") != nullptr;
        return on;
    }
    void note_alloc_class(const std::string& class_desc) {
        ++class_histogram_[class_desc];
    }
    const std::unordered_map<std::string, uint64_t>& class_histogram() const {
        return class_histogram_;
    }
    
    json dump() const {
        json arr = json::array();
        for (const uint32_t oid : get_all_ids()) {  // F-NEW-381 phase 2: id-ascending
            arr.push_back(objects_.at(oid).to_json());
        }
        return arr;
    }
    
    json get_allocation_log() const {
        return allocation_log_;
    }
    
    std::vector<uint32_t> get_all_ids() const {
        std::vector<uint32_t> ids;
        ids.reserve(objects_.size());
        for (const auto& pair : objects_) ids.push_back(pair.first);
        std::sort(ids.begin(), ids.end());  // F-NEW-381 phase 2: std::map order preserved
        return ids;
    }
    
    // EXP-035: Field access helpers
    bool has_object(uint32_t id) const {
        return objects_.find(id) != objects_.end();
    }
    
    std::optional<DalvikValue> get_object_field(uint32_t object_id, const std::string& field_name) const {
        auto it = objects_.find(object_id);
        if (it == objects_.end()) {
            return std::nullopt;
        }

        DalvikValue val = it->second.get_field(field_name);
        // F-NEW-321 (CONT-50): QUALIFIED-FIRST read for resolvable bare
        // names on DEX-defined objects. The S134 dual-write's legacy
        // mirror now lands in the plain slot RAW (superclass writes must
        // not re-resolve onto a subclass's shadowed slot), so BOTH slots
        // can be populated and the plain slot can be STALE (the
        // Atomic*FieldUpdater face: interpreter set→qualified, bare
        // get→plain hit = the F-NEW-251 split-brain reborn). One logical
        // field, one storage identity: for a DEX-declared field the
        // QUALIFIED slot is authoritative; the plain slot is the legacy
        // compatibility channel only (C++ writers that predate the
        // resolver). Framework-owned objects keep bare keys end to end.
        if (field_key_resolver_ && is_resolvable_bare_name(field_name)) {
            const std::string qualified =
                field_key_resolver_(it->second.class_descriptor, field_name);
            if (!qualified.empty() && qualified != field_name) {
                const DalvikValue qv = it->second.get_field(qualified);
                const bool q_missing =
                    qv.type == DalvikType::UNINITIALIZED ||
                    qv.type == DalvikType::REGISTER_UNSET;
                if (!q_missing) return qv;
                // qualified never written: the bare value (if any) is the
                // only writer's truth (legacy C++ authorship).
                if (val.type != DalvikType::UNINITIALIZED &&
                    val.type != DalvikType::REGISTER_UNSET)
                    return val;
                return std::nullopt;
            }
        }
        if (val.type == DalvikType::UNINITIALIZED ||
            val.type == DalvikType::REGISTER_UNSET) {
            return std::nullopt;
        }
        return val;
    }
    
    bool set_object_field(uint32_t object_id, const std::string& field_name, const DalvikValue& value) {
        auto it = objects_.find(object_id);
        if (it == objects_.end()) {
            return false;
        }
        // F-NEW-251: a bare-name write to a DEX-declared field MUST land in
        // the interpreter's qualified slot (the Atomic*FieldUpdater family
        // previously forked a parallel bare slot and the semaphore/mutex
        // accounting split-brained — dooz Lek1 evidence).
        std::string key = field_name;
        if (field_key_resolver_ && is_resolvable_bare_name(field_name)) {
            const std::string qualified =
                field_key_resolver_(it->second.class_descriptor, field_name);
            if (!qualified.empty() && qualified != field_name)
                key = qualified;
        }
        it->second.set_field(key, value);
        return true;
    }

    // F-NEW-321 (CONT-50): RAW exact-key write — no F-NEW-251 bare-name
    // redirect. The interpreter's S134 dual-write legacy mirror is the one
    // caller that already KNOWS the field identity (it computed the
    // qualified primary itself); routing its mirror through the
    // runtime-class resolver re-resolves the bare name against the
    // receiver's most-derived declarer, so a SUPERCLASS field write's
    // mirror lands in the SUBCLASS's shadowed qualified slot (solitaire 71:
    // ay$a.<init>'s mObservable mirror clobbered c$b.a = the outer
    // presenter; probe fnew320 N2/PRE face). ART law: a field of a
    // superclass occupies a distinct slot from a subclass field of the
    // same name; the mirror is a legacy compatibility channel, not a
    // second identity resolution.
    bool set_object_field_raw(uint32_t object_id, const std::string& key,
                              const DalvikValue& value) {
        auto it = objects_.find(object_id);
        if (it == objects_.end()) {
            return false;
        }
        it->second.set_field(key, value);
        return true;
    }

    // EXP-060: Read-only access to the entire heap. Used by the
    // synthetic-click campaign to scan for newly-created objects
    // (e.g. LoginActivity) after a click is dispatched.
    // F-NEW-381 phase 2: unordered storage; consumers that need the
    // historical id-ascending order use get_all_ids() (sorted).
    const std::unordered_map<uint32_t, HeapObject>& all_objects() const {
        return objects_;
    }

    // R-NEW-464 closeout: object identity accessor — the annotation-proxy
    // accessor law needs the receiver's RUNTIME class descriptor to verify
    // the receiver is an annotation proxy (interface body, no DEX code)
    // before claiming the accessor route. Answers the object's
    // class_descriptor ("Lcom/probe/r464/EventAnn;") or false when the id
    // is not a live heap object.
    bool get_object_class(uint32_t object_id, std::string& out_class) const {
        auto it = objects_.find(object_id);
        if (it == objects_.end()) return false;
        out_class = it->second.class_descriptor;
        return true;
    }

private:
    std::unordered_map<uint32_t, HeapObject> objects_;
    std::unordered_map<std::string, uint64_t> class_histogram_;  // F-NEW-542
    uint32_t next_id_;
    uint64_t alloc_sequence_;
    json allocation_log_;
    size_t allocation_log_cap_;  // EXP-042 Phase 1: 0 = unbounded.
    FieldKeyResolver field_key_resolver_;  // F-NEW-251 shared field identity
};

// ============================================================================
// METHOD CALL STACK — Invocation Tracking
// ============================================================================

class CallStack {
public:
    CallStack() : next_frame_id_(1), max_depth_(0), current_depth_(0),
                  completed_frame_cap_(100) {}
    
    // EXP-042 Phase 1: Ring-buffer cap on completed frames. Older frames are
    // evicted to bound memory. The cap is consulted from DalvikExecutionEngine
    // via set_completed_frame_cap() once config is loaded.
    void set_completed_frame_cap(size_t cap) { completed_frame_cap_ = cap; }
    
    void push_frame(StackFrame&& frame) {
        frame.frame_id = next_frame_id_++;
        frame.enter_time = Clock::now();
        // R-NEW-339: record the invoke site pc in the CALLER frame so
        // THROWABLE-STACK-PC forensics can localize which invoke inside a
        // big method (e.g. AndroidComposeView.<init>) made the failing call.
        if (!stack_.empty()) {
            frame.caller_pc = last_invoke_pc_;
        }

        stack_.push(std::move(frame));
        current_depth_ = stack_.size();
        if (current_depth_ > max_depth_) max_depth_ = current_depth_;
    }

    // R-NEW-339: the engine sets this right before dispatching an invoke;
    // push_frame() copies it into the new frame's caller_pc.
    uint32_t last_invoke_pc_ = 0;
    void set_last_invoke_pc(uint32_t pc) { last_invoke_pc_ = pc; }
    
    // CONT-42 THROUGHPUT LAW (gprof, dooz 60s profile): pop_frame was the
    // single hottest engine function (12.7% of wall, 1.27M calls): (a) the
    // EXP-042 cap erased ONE element from the FRONT on every push at cap —
    // vector::erase(begin) is O(n) per pop, the exact shape the F-107b law
    // already banned for the trace vectors; (b) the frame was COPIED twice
    // (push_back(frame) + return frame) although the only call site discards
    // the return. Fix: F-107b BATCHED erase (drop a batch in one erase —
    // identical FIFO order, identical survivor set modulo the documented
    // bounded BATCH lag), move into completed_frames_, and return void (the
    // sole caller never consumed the returned copy).
    static constexpr size_t kCompletedFrameBatch = 64;
    void pop_frame() {
        if (stack_.empty()) return;

        Frame frame = std::move(stack_.top());
        stack_.pop();

        frame.exit_time = Clock::now();
        frame.duration_ms = std::chrono::duration<double, std::milli>(
            frame.exit_time - frame.enter_time).count();
        frame.status = StackFrame::Status::RETURNED;

        // EXP-042 Phase 1: Cap completed_frames_ to bound memory. Each frame
        // embeds a DexRegisterFile (~16 DalvikValue entries × 88 B + set + map
        // = ~2 KB). For deep recursive APKs (Telegram's Theme.getColor recurses
        // 6 000+ times), an uncapped vector grows past 12 MB and pushes toward
        // OOM. The cap keeps the last N frames; older frames are discarded
        // (F-107b batched erase — one O(n) memmove per BATCH, not per pop).
        if (completed_frame_cap_ > 0 &&
            completed_frames_.size() >= completed_frame_cap_ +
                                            kCompletedFrameBatch) {
            completed_frames_.erase(completed_frames_.begin(),
                                    completed_frames_.begin() +
                                        static_cast<long>(kCompletedFrameBatch));
        }
        completed_frames_.push_back(std::move(frame));
        current_depth_ = stack_.size();
    }
    
    StackFrame& top() { return stack_.top(); }
    const StackFrame& top() const { return stack_.top(); }
    
    bool empty() const { return stack_.empty(); }
    size_t depth() const { return stack_.size(); }
    size_t max_depth() const { return max_depth_; }
    
    const std::vector<StackFrame>& get_completed_frames() const { 
        return completed_frames_; 
    }
    
    // CAMPAIGN 010 R14: real stack-trace support for
    // Thread.getStackTrace()/Kotlin Intrinsics. Returns live frames
    // TOP (innermost) FIRST — the order Java's getStackTrace() uses.
    std::vector<std::pair<std::string, std::string>> snapshot_top_first() const {
        std::vector<std::pair<std::string, std::string>> out;
        auto temp = stack_;
        while (!temp.empty()) {
            out.emplace_back(temp.top().class_name, temp.top().method_name);
            temp.pop();
        }
        return out;
    }

    // R-NEW-339 forensics: frames with caller PC (top-first). For frame i,
    // caller_pc is the invoke site pc INSIDE frame i+1 (the caller) —
    // pinpoints which invoke in a big <init> threw.
    struct FramePc { std::string cls; std::string method; uint32_t caller_pc; };
    std::vector<FramePc> snapshot_frames_top_first() const {
        std::vector<FramePc> out;
        auto temp = stack_;
        while (!temp.empty()) {
            out.push_back({temp.top().class_name, temp.top().method_name,
                           temp.top().caller_pc});
            temp.pop();
        }
        return out;
    }

    // S72 forensics: deep-copy snapshots of the top-N LIVE frames (top
    // first). Bounded N (~5 frames ≈ 10 KB) and env-gated call sites keep
    // this diagnostic-only. Returned by value — no dangling pointers.
    std::vector<StackFrame> peek_frames_top_first(size_t n) const {
        std::vector<StackFrame> out;
        auto temp = stack_;
        while (!temp.empty() && out.size() < n) {
            out.push_back(temp.top());
            temp.pop();
        }
        return out;
    }

    json dump_current_stack() const {
        json arr = json::array();
        
        // Copy stack to vector (can't iterate stack easily in reverse)
        std::vector<const Frame*> frames;
        auto temp = stack_;
        while (!temp.empty()) {
            frames.push_back(&temp.top());
            temp.pop();
        }
        
        for (auto it = frames.rbegin(); it != frames.rend(); ++it) {
            arr.push_back((*it)->to_json());
        }
        
        return arr;
    }
    
    json dump_all_calls() const {
        json result;
        result["max_depth"] = max_depth_;
        result["total_calls"] = completed_frames_.size() + stack_.size();
        result["current_stack"] = dump_current_stack();
        result["completed_calls"] = json::array();
        for (const auto& f : completed_frames_) {
            result["completed_calls"].push_back(f.to_json());
        }
        return result;
    }

private:
    using Frame = StackFrame;
    std::stack<Frame> stack_;
    std::vector<Frame> completed_frames_;
    uint32_t next_frame_id_;
    size_t max_depth_;
    size_t current_depth_;
    // EXP-042 Phase 1: 0 = unbounded (NOT recommended for real APKs).
    size_t completed_frame_cap_;
};

// ============================================================================
// INSTRUCTION TRACE — Per-Instruction Evidence
// ============================================================================

struct InstructionTrace {
    uint64_t sequence = 0;
    uint32_t pc_before = 0;
    uint32_t pc_after = 0;
    
    std::string opcode_name;
    uint16_t opcode_hex = 0;
    
    struct Operand {
        std::string name;
        std::string value;
        int64_t numeric = 0;
    };
    std::vector<Operand> operands;
    
    enum class Status {
        SUCCESS,
        UNIMPLEMENTED,
        HALT_RETURN,
        CRASH_ERROR,
        BRANCH_TAKEN,
        BRANCH_NOT_TAKEN
    };
    Status status = Status::SUCCESS;
    
    // State changes
    std::map<std::string, DalvikValue> registers_before;
    std::map<std::string, DalvikValue> registers_after;
    std::vector<std::string> changed_registers;
    
    // Side effects
    std::optional<uint32_t> allocated_object_id;
    std::optional<std::string> invoked_method;
    std::optional<DalvikValue> return_value;
    
    // Error info
    std::optional<std::string> error_message;
    // EXP-037 PHASE A Week 3 (BLOCKER-001 FIX): halt_reason was referenced by
    // execute_iget/iput/sget/sput-object handlers in dalvik_engine.cpp but was
    // never declared on this struct, breaking the build. Treat it as a peer
    // of error_message (used by the trace consumer for halt diagnostics).
    std::string halt_reason;
    
    // Timing
    double execution_us = 0;
    
    json to_json() const {
        json trace;
        trace["sequence"] = sequence;
        trace["pc_before"] = pc_before;
        trace["pc_after"] = pc_after;
        trace["opcode"] = opcode_name;
        trace["opcode_hex"] = "0x" + [this]() {
            std::ostringstream o; o << std::hex << std::setw(4) << std::setfill('0') << opcode_hex; return o.str();
        }();
        trace["status"] = status == Status::SUCCESS ? "SUCCESS" :
                         status == Status::UNIMPLEMENTED ? "UNIMPLEMENTED" :
                         status == Status::HALT_RETURN ? "RETURN" :
                         status == Status::CRASH_ERROR ? "ERROR" :
                         status == Status::BRANCH_TAKEN ? "BRANCH_TAKEN" : "BRANCH_NOT_TAKEN";
        trace["operands"] = json::array();
        for (const auto& op : operands) {
            trace["operands"].push_back({{"name", op.name}, {"value", op.value}});
        }
        trace["changed_registers"] = changed_registers;
        if (allocated_object_id) trace["allocated_object"] = *allocated_object_id;
        if (invoked_method) trace["invoked"] = *invoked_method;
        if (return_value) trace["return_value"] = return_value->to_json();
        if (error_message) trace["error"] = *error_message;
        trace["execution_us"] = execution_us;
        return trace;
    }
};

// ============================================================================
// API CALL TRACE — Android API Invocation Evidence
// ============================================================================

struct ApiCallTrace {
    uint64_t sequence = 0;
    std::string api_class;      // android.widget.TextView
    std::string method;          // setText
    std::string descriptor;      // (Ljava/lang/CharSequence;)V
    std::vector<std::string> arguments;
    std::string return_value;
    
    enum class Status {
        IMPLEMENTED,
        STUBBED,
        MISSING,
        ERROR
    };
    Status status = Status::STUBBED;
    
    uint32_t pc = 0;
    uint32_t frame_id = 0;
    double execution_us = 0;
    
    json to_json() const {
        json call;
        call["sequence"] = sequence;
        call["api"] = api_class + "." + method;
        call["class"] = api_class;
        call["method"] = method;
        call["descriptor"] = descriptor;
        call["arguments"] = arguments;
        call["return_value"] = return_value;
        call["status"] = status == Status::IMPLEMENTED ? "IMPLEMENTED" :
                        status == Status::STUBBED ? "STUBBED" :
                        status == Status::MISSING ? "MISSING" : "ERROR";
        call["pc"] = pc;
        call["frame_id"] = frame_id;
        call["execution_us"] = execution_us;
        return call;
    }
};

// ============================================================================
// EXECUTION RESULT — Complete Run Evidence
// ============================================================================

struct DalvikExecutionResult {
    std::string experiment_id = "EXP-030";
    std::string timestamp;
    std::string apk_name;
    std::string apk_sha256;
    
    // DEX report reference (non-owning pointer for execution)
    const dex::DexReport* dex_report = nullptr;
    
    // Entry point
    std::string main_class;
    std::string main_method;
    
    // Final state
    enum class FinalStatus {
        COMPLETED_SUCCESS,
        COMPLETED_PARTIAL,
        HALTED_UNIMPLEMENTED_OPCODE,
        HALTED_MISSING_METHOD,
        HALTED_API_ERROR,
        HALTED_STACK_OVERFLOW,
        CRASH_EXCEPTION
    };
    FinalStatus final_status = FinalStatus::COMPLETED_SUCCESS;
    std::string halt_reason;

    // M3 FINDING-016 (exception-honesty law, ROADMAP family G): exceptions
    // that unwound past a frame with NO handler. ART law: an exception that
    // escapes the outermost app frame kills the process. Default mode
    // records + reports (run can never report plain SUCCESS); strict mode
    // (MINIANDROID_EXC_STRICT=1) halts the DEX dispatch (CRASH).
    size_t uncaught_in_flight_count = 0;
    std::vector<std::string> uncaught_in_flight_log;
    
    // Statistics
    uint64_t total_instructions_executed = 0;
    uint64_t total_opcodes_decoded = 0;
    double total_execution_ms = 0;
    
    // Components
    CallStack call_stack;
    DalvikHeap heap;
    
    // Traces
    std::vector<InstructionTrace> instruction_traces;
    std::vector<ApiCallTrace> api_call_traces;
    // CONT-42 THROUGHPUT LAW: the O(1) survivor-ring cursor for
    // api_call_traces (batched_cap_push ring form). 0 = chronological;
    // nonzero = physical ring order. ring_normalize_chrono() restores
    // true FIFO order once at execution end (single O(cap) rotate).
    size_t api_call_ring_cursor = 0;
    
    // Final register state (from top frame if exists)
    json final_registers;
    
    // Output artifacts
    std::string screenshot_path;
    std::string report_path;
    
    json to_full_report() const;
};

// ============================================================================
// MAIN DALVIK EXECUTION ENGINE
// ============================================================================

/**
 * Real Dalvik Bytecode Execution Engine
 * 
 * EXP-030 Implementation:
 * - Executes actual DEX bytecode instructions
 * - Maintains real register state
 * - Allocates objects on heap
 * - Tracks method invocations via call stack
 * - Bridges to Android API stubs
 */
    // P0 SPLIT: dispatch frame for the bridge domain ranges — defined
    // in dex/dalvik_bridge_frame.h (references only here; no include
    // to keep the engine-header dependency graph unchanged).
    struct DalvikBridgeFrame;


} // namespace dalvik
} // namespace miniandroid

#endif  // MINIANDROID_DALVIK_ENGINE_TYPES_H
