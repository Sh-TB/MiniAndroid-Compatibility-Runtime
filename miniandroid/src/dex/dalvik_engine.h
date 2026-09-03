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

#ifndef MINIANDROID_REAL_DALVIK_ENGINE_H
#define MINIANDROID_REAL_DALVIK_ENGINE_H

#include "dex_parser.h"
#include "class_resolver.h"
#include "../runtime/runtime_metadata.h"
#include "../runtime/vtable_dispatch.h"
#include "../api/android_stubs.h"
// EXP-051: Shadow registry forward-declarations.
namespace miniandroid { namespace framework {
class ShadowRegistry;
class HeapAllocator;
}}
#include <string>
#include <vector>
#include <map>
#include <unordered_map>
#include <stack>
#include <memory>
#include <cstdint>
#include <optional>
#include <functional>
#include <sstream>
#include <iomanip>
#include <chrono>
#include <set>

#include "../../third_party/nlohmann_json/include/nlohmann/json.hpp"

namespace miniandroid {
namespace dalvik {

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
    
    // Reference types
    std::string string_val;       // For STRING_REF
    std::string class_desc;       // For CLASS_REF or OBJECT_REF
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
    
    void write_v(uint8_t reg, const DalvikValue& value) {
        if (reg < size_) {
            registers_[reg] = value;
            written_.insert(reg);
        }
    }
    
    void write_p(uint8_t param_idx, const DalvikValue& value) {
        uint8_t reg = param_start_ + param_idx;
        if (reg < size_) {
            registers_[reg] = value;
            written_.insert(reg);
        }
    }
    
    DalvikValue read_v(uint8_t reg) const {
        if (reg < size_) return registers_[reg];
        return DalvikValue::make_uninit();
    }
    
    DalvikValue read_p(uint8_t param_idx) const {
        uint8_t reg = param_start_ + param_idx;
        if (reg < size_) return registers_[reg];
        return DalvikValue::make_uninit();
    }
    
    void set_pc(uint32_t pc) { pc_ = pc; }
    uint32_t get_pc() const { return pc_; }
    
    uint32_t get_size() const { return size_; }
    uint32_t get_ins_count() const { return ins_count_; }
    
    std::vector<uint8_t> get_written_registers() const {
        return std::vector<uint8_t>(written_.begin(), written_.end());
    }
    
    json dump() const {
        json result;
        result["size"] = size_;
        result["ins_count"] = ins_count_;
        result["param_start"] = param_start_;
        result["pc"] = pc_;
        result["registers"] = json::array();
        
        for (uint8_t i = 0; i < size_; ++i) {
            json entry;
            bool is_param = (i >= param_start_);
            entry["name"] = is_param ? ("p" + std::to_string(i - param_start_)) 
                                     : ("v" + std::to_string(i));
            entry["index"] = i;
            entry["value"] = registers_[i].to_json();
            entry["written"] = (written_.count(i) > 0);
            result["registers"].push_back(entry);
        }
        return result;
    }
    
    std::map<std::string, DalvikValue> get_snapshot() const {
        std::map<std::string, DalvikValue> snap;
        for (uint8_t i = 0; i < size_; ++i) {
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
    std::set<uint8_t> written_;
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
    std::string readable_class;     // android.widget.TextView
    
    bool initialized = false;
    uint64_t creation_sequence = 0;
    uint32_t creator_pc = 0;
    uint32_t creator_frame_id = 0;
    
    // Fields (simplified - would be full field table in production)
    std::map<std::string, DalvikValue> fields;
    
    // Bridge to Android API stub
    std::shared_ptr<api::AndroidObject> api_object;
    
    HeapObject() = default;
    
    HeapObject(uint32_t id, const std::string& desc, uint64_t seq, uint32_t pc, uint32_t frame)
        : object_id(id), class_descriptor(desc), creation_sequence(seq), 
          creator_pc(pc), creator_frame_id(frame) {
        readable_class = descriptor_to_readable(desc);
    }
    
    void set_field(const std::string& name, const DalvikValue& value) {
        fields[name] = value;
    }
    
    DalvikValue get_field(const std::string& name) const {
        auto it = fields.find(name);
        return (it != fields.end()) ? it->second : DalvikValue::make_uninit();
    }
    
    json to_json() const {
        json obj;
        obj["object_id"] = object_id;
        obj["class_descriptor"] = class_descriptor;
        obj["readable_class"] = readable_class;
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
    
    uint32_t allocate(const std::string& class_desc, uint32_t pc, uint32_t frame_id) {
        HeapObject obj(next_id_++, class_desc, alloc_sequence_++, pc, frame_id);
        objects_[obj.object_id] = obj;
        
        // EXP-042 Phase 1: ring-buffer the allocation log. Each json entry is
        // ~256 B; uncapped, 10 M allocations would consume 2.5 GB. With cap=1000
        // we keep the last 1 000 allocations (~256 KB) — enough for diagnostic
        // purposes.
        if (allocation_log_cap_ > 0 &&
            allocation_log_.size() >= allocation_log_cap_) {
            // nlohmann::json::array() uses a vector internally; erase from
            // the front is O(N) but N=1000 is trivial.
            allocation_log_.erase(allocation_log_.begin());
        }
        allocation_log_.push_back({
            {"object_id", obj.object_id},
            {"class", class_desc},
            {"pc", pc},
            {"frame_id", frame_id},
            {"sequence", alloc_sequence_ - 1}
        });
        
        return obj.object_id;
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
    
    json dump() const {
        json arr = json::array();
        for (const auto& pair : objects_) {
            arr.push_back(pair.second.to_json());
        }
        return arr;
    }
    
    json get_allocation_log() const {
        return allocation_log_;
    }
    
    std::vector<uint32_t> get_all_ids() const {
        std::vector<uint32_t> ids;
        for (const auto& pair : objects_) ids.push_back(pair.first);
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
        if (val.type == DalvikType::UNINITIALIZED || val.type == DalvikType::REGISTER_UNSET) {
            return std::nullopt;
        }
        return val;
    }
    
    bool set_object_field(uint32_t object_id, const std::string& field_name, const DalvikValue& value) {
        auto it = objects_.find(object_id);
        if (it == objects_.end()) {
            return false;
        }
        it->second.set_field(field_name, value);
        return true;
    }

    // EXP-060: Read-only access to the entire heap. Used by the
    // synthetic-click campaign to scan for newly-created objects
    // (e.g. LoginActivity) after a click is dispatched.
    const std::map<uint32_t, HeapObject>& all_objects() const {
        return objects_;
    }

private:
    std::map<uint32_t, HeapObject> objects_;
    uint32_t next_id_;
    uint64_t alloc_sequence_;
    json allocation_log_;
    size_t allocation_log_cap_;  // EXP-042 Phase 1: 0 = unbounded.
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
        
        stack_.push(std::move(frame));
        current_depth_ = stack_.size();
        if (current_depth_ > max_depth_) max_depth_ = current_depth_;
    }
    
    StackFrame pop_frame() {
        if (stack_.empty()) return StackFrame{};
        
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
        // OOM. The cap keeps the last N frames; older frames are discarded.
        if (completed_frame_cap_ > 0 &&
            completed_frames_.size() >= completed_frame_cap_) {
            completed_frames_.erase(completed_frames_.begin());
        }
        completed_frames_.push_back(frame);
        current_depth_ = stack_.size();
        
        return frame;
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
class DalvikExecutionEngine {
public:
    DalvikExecutionEngine();
    ~DalvikExecutionEngine();

    // EXP-038 (BLOCKER-033): Set per-DEX raw data for correct method_idx resolution.
    // Call this before execute_apk() to enable per-DEX method resolution.
    void set_per_dex_raw_data(std::vector<std::vector<uint8_t>> data) {
        per_dex_raw_data_ = std::move(data);
        is_multidex_ = (per_dex_raw_data_.size() > 1);
    }
    // EXP-071 Phase 6: Set the APK path so AssetManager.open can read assets.
    void set_apk_path(const std::string& path) { apk_path_ = path; }
    // EXP-093/F011: Manifest-derived package identity
    void set_package_info(const std::string& pkg, int vcode, const std::string& vname) {
        package_name_ = pkg; version_code_ = vcode; version_name_ = vname;
    }

    // EXP-038 (BLOCKER-033): Build class→DEX index map from DexReport.
    // Must be called after dex_report is set and before execution begins.
    void build_class_dex_index(const dex::DexReport& report);

    // EXP-088+ Phase 1.2 (secondary-DEX injection): Inject ALL classes from
    // ALL secondary DEX files (per_dex_raw_data_[1..N-1]) into the merged
    // dex_report_->classes vector and update class_info_index_.
    //
    // Without this, only classes.dex (DEX 0) classes are available for
    // runtime dispatch. Any class defined in classes2.dex/classes3.dex/etc.
    // (e.g. Telegram's UserConfig, LoginActivity) cannot be found by
    // try_recursive_invoke, returning "class not in index" silently.
    //
    // The previous on-demand injection (only for the manifest activity class)
    // was insufficient: it injected exactly ONE class. Every other multi-DEX
    // class (called recursively from onCreate) was still missing.
    //
    // This method is idempotent: calling it twice does NOT duplicate classes
    // (we check class_info_index_ before inserting).
    //
    // Returns the number of newly-injected classes.
    size_t inject_secondary_dex_classes();
    
    /**
     * Execute APK through real DEX bytecode interpretation
     */
    DalvikExecutionResult execute_apk(
        const std::string& apk_path,
        const dex::DexReport& dex_report,
        bool verbose = false
    );

    /**
     * EXP-037 Phase B (BLOCKER-019): Execute APK with explicit activity class
     * name from the AndroidManifest.xml. This bypasses the class-name-scan
     * heuristic in execute_apk() which fails for obfuscated APKs (e.g.
     * TinyMusicPlayer uses La/a;, La/b;, etc.).
     *
     * `activity_class_name` is the manifest's main_activity in DEX type
     * descriptor form, e.g. "Lcom/martinmimigames/tinymusicplayer/Launcher;".
     * If empty, falls back to the scan-based heuristic.
     */
    DalvikExecutionResult execute_apk_with_activity(
        const std::string& apk_path,
        const dex::DexReport& dex_report,
        const std::string& activity_class_name,
        bool verbose = false
    );

    // EXP-060: Dispatch a synthetic CLICK event on a View. Looks up the
    // ViewNode via ViewShadow, retrieves its registered OnClickListener,
    // and invokes listener.onClick(view) via try_recursive_invoke. This
    // is the generic event mechanism — no Telegram-specific code.
    //
    // `view_object_id` is the heap object_id of the target View.
    // Returns true if a listener was found and dispatched.
    bool dispatch_click(uint32_t view_object_id);
    // CAMPAIGN 013: run a custom view's REAL onDraw(Canvas) bytecode.
    int dispatch_custom_view_draw(uint32_t view_object_id);

    // EXP-060: Convenience wrapper — find a View by class descriptor
    // substring (e.g. "IntroActivity$4" or "startMessagingButton") and
    // dispatch a click on it. Returns true if a matching View with a
    // registered listener was found.
    bool dispatch_click_by_class(const std::string& class_substring);

    // CAMPAIGN 009 §10: view attach lifecycle dispatch.
    // AOSP View.java: when the view tree attaches to the window,
    // View.dispatchAttachedToWindow invokes onAttachedToWindow() on every
    // node. AbstractComposeView.onAttachedToWindow ->
    // ensureCompositionCreated() is what turns an empty ComposeView into a
    // real composition (AndroidComposeView child + render content). The
    // runtime previously swallowed this callback (ViewShadow handled_void),
    // so every Compose APK rendered a white frame with children=0.
    // Env-gated: MINIANDROID_DISPATCH_ATTACH=1 (default off for golden
    // regression safety). Bounded multi-pass: attach may create new views.
    bool dispatch_view_attached();

    // EXP-071 Phase 8: Generic Runnable dispatch.
    // Invokes run()V (or run(TLObject, TL_error)V for RequestDelegate) on the
    // heap object identified by runnable_object_id. Used by the event loop
    // to drain queued Runnables after Handler.post / runOnUIThread calls.
    // The response/error_object_id args are 0 for plain Runnables, or
    // non-zero for RequestDelegate runnables that take a (response, error) pair.
    bool dispatch_runnable(uint32_t runnable_object_id,
                          uint32_t response_object_id = 0,
                          uint32_t error_object_id = 0);

    // EXP-069: Generic text input dispatch.
    // Injects text into a TextView/EditText by:
    //   1. Storing the text on the ViewNode (ViewShadow.setText)
    //   2. Storing it on the heap object (for getText() in DEX bytecode)
    //   3. Triggering any registered TextWatchers
    // Returns true if the view was found and text was set.
    bool dispatch_text_input(uint32_t view_object_id, const std::string& text);

    // EXP-069: Convenience — find an EditText by class descriptor substring
    // and dispatch text input. Returns true if a matching view was found.
    bool dispatch_text_input_by_class(const std::string& class_substring,
                                       const std::string& text);

    // EXP-061: Dump the full ViewNode tree (from ViewShadow) to a JSON
    // file. Each node includes object_id, class, parent, children,
    // geometry (x,y,width,height), text, visibility, clickable,
    // listener_present. This is the input to the software renderer.
    bool dump_view_tree(const std::string& path);
    
    /**
     * Execute specific method from DEX report
     */
    DalvikExecutionResult execute_method(
        const dex::MethodInfo& method,
        const dex::DexReport& dex_report,
        const std::vector<DalvikValue>& args = {},
        bool verbose = false
    );
    
    /**
     * Access post-execution state
     */
    const CallStack& get_call_stack() const { return call_stack_; }
    const DalvikHeap& get_heap() const { return heap_; }
    // EXP-042 Phase 1: non-const accessors so ApplicationRuntime can configure
    // ring-buffer caps before execution begins.
    CallStack& get_call_stack() { return call_stack_; }
    DalvikHeap& get_heap() { return heap_; }
    std::string get_last_error() const { return last_error_; }
    
    // Configuration
    struct Config {
        bool verbose = false;
        bool debug_output = false;
        uint64_t max_instructions = 100000000;  // EXP-042: 100M (was 10M)
        bool stop_on_unimplemented = false;  // EXP-089: Don't halt on unimplemented opcodes
        bool generate_trace = true;
        bool enable_api_bridge = true;
        // EXP-042 Phase 1: Per-instruction register snapshots are the #1 memory
        // offender (registers_before + registers_after = 2 × 16 × 152 B ≈ 5 KB
        // per instruction). When disabled (default), trace.registers_before/after
        // remain empty and the diff loop is skipped. Enable explicitly only when
        // debugging a specific opcode.
        bool trace_register_snapshots = false;
        // EXP-042 Phase 1: Ring-buffer caps. These bound memory regardless of
        // how many instructions execute. Set to 0 to disable capping (NOT
        // recommended for real APKs — will OOM).
        size_t trace_cap = 2000;             // last N instruction traces
        size_t api_call_trace_cap = 5000;    // last N API call traces
        size_t completed_frame_cap = 100;   // last N completed stack frames
        size_t allocation_log_cap = 1000;    // last N heap allocations
        // EXP-042 Phase 1: Loop detection. Halts only when the same PC is
        // visited this many times within the SAME frame. 50 000 allows
        // legitimate loops (e.g. Theme.getColor iterating color tables) while
        // still catching true infinite loops.
        uint32_t loop_visit_threshold = 50000;
    };

    // EXP-039: Public access to config for ApplicationRuntime
    Config config_;

    // EXP-040: Recursion depth tracking
    uint32_t recursion_depth_ = 0;
    // EXP-053: Lowered from 200 to 80 to avoid C++ stack overflow when
    // running with class init enabled. Each recursive invoke uses ~80KB
    // of C++ stack (InstructionTrace + vectors + locals). 80 * 80KB = 6.4MB
    // — within the default 8MB stack limit.
    static constexpr uint32_t MAX_RECURSION_DEPTH = 80;

    // EXP-051: Public singleton accessor so the shadow registry can
    // share the engine's singleton cache (which guarantees that
    // getResources(), getMainLooper(), etc. all return the same heap
    // object_id across the entire APK execution).
    DalvikValue get_or_create_singleton_public(const std::string& class_desc) {
        return get_or_create_singleton(class_desc);
    }

    // EXP-068 + UNIFIED_011.3: Generic class inheritance queries.
    // These walk the DEX superclass chain (class_to_superclass_) to determine
    // if a class inherits from a known Android View type.
    bool is_subclass_of(const std::string& class_desc, const std::string& ancestor_desc) const;
    bool is_view_class(const std::string& class_desc) const;
    bool is_text_view_class(const std::string& class_desc) const;
    bool is_edit_text_class(const std::string& class_desc) const;
    bool is_image_view_class(const std::string& class_desc) const;
    bool is_button_class(const std::string& class_desc) const;
    bool is_view_group_class(const std::string& class_desc) const;

    // EXP-051: Public heap accessor for the shadow registry adapter.
    DalvikHeap& get_heap_public() { return heap_; }

    // EXP-051: Attach a shadow registry. The engine does NOT own the
    // registry — it's owned by ApplicationRuntime so the runtime can
    // also drain the HandlerShadow queue and read IntentShadow state.
    void set_shadow_registry(framework::ShadowRegistry* reg) { shadow_registry_ = reg; }
    framework::ShadowRegistry* get_shadow_registry() const { return shadow_registry_; }

    // EXP-051: Try to dispatch a method call via the shadow registry.
    // Returns true if a shadow handled the call (in which case `result`
    // and `status` are populated). Returns false if no shadow claimed
    // the call — the caller should fall back to the legacy bridge.
    bool try_shadow_dispatch(const std::string& class_name,
                              const std::string& method,
                              const std::vector<DalvikValue>& args,
                              DalvikValue& result,
                              ApiCallTrace::Status& status);

public:
    // EXP-077: try_recursive_invoke made public for fragment lifecycle advancement
    // EXP-038 (BLOCKER-033): Per-DEX raw data for correct method_idx resolution.
    // Stored in DalvikExecutionEngine (NOT in DexReport) to avoid memory layout
    // issues that cause SEGV when DexReport struct is modified.
    // Each entry is the raw bytes of a DEX file, used to resolve method_idx
    // using the correct per-DEX method_ids[] table.
    std::vector<std::vector<uint8_t>> per_dex_raw_data_;
    bool is_multidex_ = false;

    // EXP-038 (BLOCKER-033): Map class descriptor → source DEX index.
    // Built during execute_apk() by scanning dex_report.classes.
    std::map<std::string, uint32_t> class_to_dex_index_;
    // EXP-068: class_to_superclass_ maps class descriptor → direct superclass descriptor.
    // Built from dex_report_->classes[i].superclass_name.
    // Used by is_subclass_of() for semantic View inheritance resolution.
    std::map<std::string, std::string> class_to_superclass_;

    // EXP-045 Phase 2: O(1) class lookup index for try_recursive_invoke().
    // Maps class descriptor → index into dex_report_->classes vector.
    // Using index instead of raw pointer to avoid dangling pointer issues
    // when the classes vector is reallocated.
    std::unordered_map<std::string, size_t> class_info_index_;

    // Core execution loop
    bool execute_method_internal(
        const std::string& class_name,
        const std::string& method_name,
        const std::string& descriptor,
        const std::vector<uint16_t>& bytecode,
        uint32_t registers_size,
        uint32_t ins_size,
        uint32_t outs_size,
        const std::vector<DalvikValue>& args,
        DalvikExecutionResult& result,
        // EXP-052: optional tries[] data for exception-handling diagnostics.
        // When non-null, the THROW opcode handler can scan the tries table
        // for a matching catch handler.
        uint16_t tries_size = 0,
        const uint8_t* tries_data = nullptr,
        size_t tries_data_size = 0
    );

    // EXP-038 (BLOCKER-034): Recursive DEX method invocation.
    // Given a declaring_class and method_name, search the DEX for a matching
    // method with bytecode. If found, recursively call execute_method_internal()
    // and return true (with result stored in return_val).
    // If not found (framework method), return false and let the caller bridge
    // to the API stub layer.
    // EXP-077: Made public so ApplicationRuntime can dispatch createView
    // on fragments that need lifecycle advancement.
    bool try_recursive_invoke(
        const std::string& declaring_class,
        const std::string& method_name,
        const std::vector<DalvikValue>& args,
        DalvikValue& return_val,
        DalvikExecutionResult& result,
        const std::string& method_descriptor = ""
    );
    
    bool fetch_decode_execute(DalvikExecutionResult& result);
    uint16_t fetch_opcode(uint32_t pc) const;

    // UNIFIED_011.2 SYNTH-EXC (§21/§24 campaign): runtime exception machinery.
    //
    // find_catch_handler_for_pc: search the current frame's try table for a
    // handler covering `pc`. Extracted verbatim from the THROW opcode handler
    // (EXP-052/053) so synthetic runtime exceptions share the same machinery.
    // UNIFIED_011.3 TYPED-CATCH (§18): typed handlers are now TYPE-MATCHED
    // against `exc_desc` (DEX superclass chain via class_to_superclass_ +
    // built-in java.lang/java.io/java.util exception hierarchy). First
    // matching typed handler wins; catch-all is the fallback; no match →
    // returns false (caller unwinds/propagates).
    bool find_catch_handler_for_pc(uint32_t pc, uint32_t& handler_addr,
                                   bool& is_catch_all, std::string& catch_type,
                                   const std::string& exc_desc);

    // UNIFIED_011.3 TYPED-CATCH: exception-type compatibility check.
    // Exact match, DEX superclass-chain walk, and built-in framework
    // exception hierarchy (see exception_hierarchy_table in dalvik_engine.cpp).
    bool is_exception_subtype(const std::string& exc_desc,
                              const std::string& catch_desc) const;

    // raise_synthetic_exception: raise a runtime exception
    // (ArrayIndexOutOfBoundsException, NullPointerException, ...).
    //   1. Handler covering pc_ → pending_exception_ = exc, pc_ = handler,
    //      returns true (execution continues at the handler).
    //   2. No handler → unwind the current frame (halted_on_return_ like a
    //      return with null result) AND record the exception in
    //      frame_unwind_exception_ so the invoking frame can search ITS try
    //      table (full Dalvik propagation, UNIFIED_011.3 §18). This
    //      eliminates the livelock that warn-and-continue produced
    //      (dooz LM1/i;.f aget OOB loop).
    bool raise_synthetic_exception(const std::string& exc_class_desc,
                                   const std::string& message,
                                   const char* origin_tag);

    // MASTER RECONCILIATION (2026-09-03): deferred exception raise for use
    // INSIDE opcode handlers and bridge_to_api callbacks. Unlike
    // raise_synthetic_exception it never writes pc_ directly — the caller
    // (ARITH_*_CASE macros, invoke wrappers `pc_ = pc + len`) would clobber
    // that jump. Instead it records a post-switch redirect
    // (exc_redirect_pending_ / exc_redirect_addr_) when a handler covers
    // pc_, or arms the frame-unwind machinery when uncaught.
    // Used by: div/rem by zero → ArithmeticException (K-29),
    // parse* malformed input → NumberFormatException (K-19).
    // Returns true if a handler covers pc_ (execution continues at the
    // handler via the post-switch redirect), false if the frame unwinds.
    bool throw_deferred(const std::string& exc_class_desc,
                        const std::string& message,
                        const char* origin_tag);

    // FINAL CANONICAL MASTER RECONCILIATION Pass-3 (K-35): REAL XmlPullParser
    // pull-parse state — event machine advances on next().
    // NOTE: struct must precede the member-function declarations below.
    struct XmlPullState {
        std::string content;   // full XML text
        size_t pos = 0;        // parse cursor
        int event = 0;         // current event (XmlPullParser constants)
        std::string cur_name;  // current tag name (START_TAG/END_TAG)
        std::string cur_text;  // current text (TEXT)
        std::vector<std::pair<std::string, std::string>> attrs;  // (name, value)
        bool ended = false;    // saw END_DOCUMENT
        bool pending_end = false;          // self-closing tag → END_TAG queued
        std::string pending_end_name;
    };

    // FINAL CANONICAL MASTER RECONCILIATION Pass-3 (K-34): resolve an open
    // asset stream chain (InputStream / InputStreamReader / BufferedReader
    // wrappers) to its asset path + live position pointer.
    bool resolve_asset_stream(uint32_t start_id, std::string& path, size_t*& pos);
    // Pass-3 (K-34): full asset bytes, extracted once per path and cached.
    const std::string& cached_asset_bytes(const std::string& path);
    // Pass-3 (K-35): advance an XmlPullParser state by one event — REAL event
    // progression (START_DOCUMENT → tags/text → END_DOCUMENT) with termination.
    void xml_pull_advance(XmlPullState& st);

    // UNIFIED_011.3 EXC-PROPAGATE: exception in flight while unwinding.
    // Set by raise_synthetic_exception / THROW-no-handler in the frame that
    // could not catch it. Consumed by try_recursive_invoke at the caller's
    // invoke site: caller's try table is searched; if a handler covers the
    // invoke pc, the caller jumps to it with pending_exception_ set
    // (move-exception works); otherwise the exception continues up.
    bool frame_unwind_exception_valid_ = false;
    DalvikValue frame_unwind_exception_ = DalvikValue::make_null();
    // Post-switch pc redirect: the invoke handlers do `pc_ = pc_ + len`
    // AFTER try_recursive_invoke returns, which would clobber a
    // handler-jump made during caller-side catch search. When this flag is
    // set, fetch_decode_execute re-applies exc_redirect_addr_ right after
    // the switch — the last word on pc_ belongs to the redirect.
    bool exc_redirect_pending_ = false;
    uint32_t exc_redirect_addr_ = 0;
    // Exception object in flight for the deferred redirect (move-exception
    // reads it after the handler jump).
    DalvikValue deferred_exception_ = DalvikValue::make_null();
    void clear_frame_unwind_exception() { frame_unwind_exception_valid_ = false;
                                          frame_unwind_exception_ = DalvikValue::make_null(); }

    
    // Opcode implementations — Constants
    bool execute_const_4(uint32_t pc, InstructionTrace& trace);
    bool execute_const_16(uint32_t pc, InstructionTrace& trace);
    bool execute_const(uint32_t pc, InstructionTrace& trace);
    bool execute_const_string(uint32_t pc, InstructionTrace& trace);
    bool execute_const_class(uint32_t pc, InstructionTrace& trace);
    
    // Opcode implementations — Moves
    bool execute_move(uint32_t pc, InstructionTrace& trace);
    bool execute_move_object(uint32_t pc, InstructionTrace& trace);
    // EXP-038 (BLOCKER-026): move-object/from16 (0x08, format 22x)
    // Required by Telegram's LaunchActivity.onCreate() at PC=1.
    bool execute_move_object_from16(uint32_t pc, InstructionTrace& trace);
    bool execute_move_result(uint32_t pc, InstructionTrace& trace);
    bool execute_move_result_object(uint32_t pc, InstructionTrace& trace);
    
    // Opcode implementations — Objects
    bool execute_new_instance(uint32_t pc, InstructionTrace& trace);
    bool execute_check_cast(uint32_t pc, InstructionTrace& trace);
    bool execute_instance_of(uint32_t pc, InstructionTrace& trace);
    
    // EXP-035: Field System Integration - Instance Field Operations
    bool execute_iget(uint32_t pc, InstructionTrace& trace);
    bool execute_iget_object(uint32_t pc, InstructionTrace& trace);
    bool execute_iput(uint32_t pc, InstructionTrace& trace);
    bool execute_iput_object(uint32_t pc, InstructionTrace& trace);
    
    // EXP-035: Field System Integration - Static Field Operations  
    bool execute_sget(uint32_t pc, InstructionTrace& trace);
    bool execute_sget_object(uint32_t pc, InstructionTrace& trace);
    bool execute_sput(uint32_t pc, InstructionTrace& trace);
    bool execute_sput_object(uint32_t pc, InstructionTrace& trace);
    
    // EXP-035: Field resolution helper (connects to runtime_metadata.h)
    struct FieldResolution {
        std::string class_descriptor;
        std::string field_name;
        std::string field_type;
        uint32_t field_offset = 0;
        bool is_static = false;
        bool resolved = false;
        std::string error_message;
    };
    FieldResolution resolve_field(uint16_t field_idx);
    
    // Opcode implementations — Invokes
    bool execute_invoke_virtual(uint32_t pc, InstructionTrace& trace, DalvikExecutionResult& result);
    bool execute_invoke_direct(uint32_t pc, InstructionTrace& trace, DalvikExecutionResult& result);
    bool execute_invoke_static(uint32_t pc, InstructionTrace& trace, DalvikExecutionResult& result);
    bool execute_invoke_interface(uint32_t pc, InstructionTrace& trace, DalvikExecutionResult& result);
    // EXP-037 Phase B (BLOCKER-012): invoke-super — needed for super.onCreate()
    // calls. Real Android apps almost always call super.onCreate(bundle) as the
    // first instruction in their onCreate; without this handler, NO real app
    // can execute past its entry method's first instruction.
    bool execute_invoke_super(uint32_t pc, InstructionTrace& trace, DalvikExecutionResult& result);
    
    // Opcode implementations — Returns
    bool execute_return_void(uint32_t pc, InstructionTrace& trace);
    bool execute_return(uint32_t pc, InstructionTrace& trace);
    bool execute_return_object(uint32_t pc, InstructionTrace& trace);
    // EXP-088+ F5: return-wide (opcode 0x10) — returns a long/double value.
    // Reads the wide register pair (vAA, vAA+1) and stores the combined
    // 64-bit value in last_invoke_return_.long_val (INT64) or
    // last_invoke_return_.double_val (FLOAT64).
    bool execute_return_wide(uint32_t pc, InstructionTrace& trace);
    
    // Opcode implementations — Control flow
    bool execute_goto(uint32_t pc, InstructionTrace& trace);
    bool execute_if_eqz(uint32_t pc, InstructionTrace& trace);
    bool execute_if_nez(uint32_t pc, InstructionTrace& trace);
    // EXP-043 Phase 1: Proper 21t format if-*z handlers (previously all
    // dispatched to execute_if_eqz with wrong comparison semantics).
    bool execute_if_ltz(uint32_t pc, InstructionTrace& trace);
    bool execute_if_gez(uint32_t pc, InstructionTrace& trace);
    bool execute_if_gtz(uint32_t pc, InstructionTrace& trace);
    bool execute_if_lez(uint32_t pc, InstructionTrace& trace);
    // EXP-037 Phase B (BLOCKER-018): 22t format if-* opcodes
    // (if-lt, if-ge, if-gt, if-le) — required for numeric comparisons.
    // Existing if-eq/if-ne are in a different file path (or unused).
    bool execute_if_lt(uint32_t pc, InstructionTrace& trace);
    bool execute_if_ge(uint32_t pc, InstructionTrace& trace);
    bool execute_if_gt(uint32_t pc, InstructionTrace& trace);
    bool execute_if_le(uint32_t pc, InstructionTrace& trace);
    // Also add if-eq/if-ne for completeness (22t format)
    bool execute_if_eq(uint32_t pc, InstructionTrace& trace);
    bool execute_if_ne(uint32_t pc, InstructionTrace& trace);
    
    // Unimplemented handler
    void handle_unimplemented(uint16_t opcode, uint32_t pc, InstructionTrace& trace);
    
    // Register access helpers
    void set_register(uint8_t reg, const DalvikValue& value);
    DalvikValue get_register(uint8_t reg) const;
    std::string register_name(uint8_t reg) const;
    
    // API bridge
    // UC-CM-001 (F012): method_idx_hint lets the catch-all STUBBED path
    // resolve the callee proto and return a TYPE-AWARE default (0 / false /
    // null / 0.0f / 0L) instead of always returning VOID. When the hint is
    // absent (legacy callers) behavior is unchanged (void + STUBBED).
    bool bridge_to_api(const std::string& class_name, const std::string& method,
                       const std::vector<DalvikValue>& args, DalvikValue& result,
                       ApiCallTrace::Status& status,
                       uint32_t method_idx_hint = 0xFFFFFFFFu);
    // EXP-042 Phase 4: Singleton cache helper for Android framework objects.
    DalvikValue get_or_create_singleton(const std::string& class_desc);
    
    // Utility
    void log(const std::string& msg);
    std::string to_hex(uint32_t val) const;
    std::string to_hex16(uint16_t val) const;
    int32_t read_signed_literal(uint16_t val) const;
    std::string get_timestamp() const;
    
    // State
    std::vector<uint16_t> bytecode_;
    const dex::DexReport* dex_report_ = nullptr;
    DexRegisterFile* current_registers_ = nullptr;
    CallStack call_stack_;
    DalvikHeap heap_;
    
    // EXP-035: Field System State
    // NOTE: DalvikValue is in miniandroid::dalvik (this namespace), not miniandroid::runtime.
    // EXP-037 PHASE A Week 3 (BLOCKER-001 FIX): corrected namespace reference; the
    // previous commit (3392b03 EXP-035) referenced runtime::DalvikValue which does
    // not exist, breaking the entire build since EXP-035.
    std::map<std::string, DalvikValue> static_field_storage_;  // key: "class_descriptor.field_name"
    std::map<std::string, std::shared_ptr<runtime::RuntimeClassInfo>> class_info_cache_;  // cached class metadata

    // EXP-042 Phase 4: Singleton cache for Android framework objects.
    // Key: class descriptor (e.g. "Landroid/content/res/Resources;").
    // Value: heap object ID. Returns the same heap object across all calls,
    // matching real Android behavior where getResources() always returns the
    // same Resources instance for a given Context.
    std::map<std::string, uint32_t> api_singletons_;
    
    // EXP-035: VTable Dispatch State
    runtime::VirtualDispatcher vtable_dispatcher_;  // VTable-based method resolution
    
    uint32_t pc_ = 0;
    uint64_t instruction_sequence_ = 0;
    uint64_t api_call_sequence_ = 0;
    uint64_t object_sequence_ = 0;
    
    // EXP-035: Current execution context (for VTable evidence)
    std::string current_class_ = "<unknown>";
    std::string current_method_ = "<unknown>";
    // EXP-071 Phase 8: Tracks whether the current invoke is static.
    // Set to true by execute_invoke_static, false by execute_invoke_virtual/direct.
    // try_shadow_dispatch uses this to decide whether args[0] is `this` (instance)
    // or the first parameter (static). Without this flag, static calls like
    // AndroidUtilities.runOnUIThread(Runnable, long) would have their Runnable
    // stolen as `this` and never reach HandlerShadow's enqueue.
    bool current_invoke_is_static_ = false;
    // EXP-038 (BLOCKER-033): Current DEX index for per-DEX method resolution.
    uint32_t current_dex_index_ = 0;

    // EXP-038 (BLOCKER-033): Per-DEX method name resolution using raw DEX bytes.
    std::string resolve_method_name_for_dex(uint32_t method_idx, uint32_t dex_index) const;
    std::string resolve_method_class_for_dex(uint32_t method_idx, uint32_t dex_index) const;
    // EXP-071 Phase 8: Resolve the method's proto descriptor, e.g. "(Ljava/lang/Runnable;J)V".
    // Used to parse parameter types so we can merge wide register pairs (J=long, D=double)
    // when invoking static methods. Without this, runOnUIThread(Runnable, long) would
    // pass 3 args (Runnable, low32, high32) instead of 2 (Runnable, long).
    std::string resolve_method_proto_for_dex(uint32_t method_idx, uint32_t dex_index) const;
    // EXP-058: Per-DEX type descriptor resolution.
    // type_idx is relative to the current DEX file's type_ids table,
    // NOT the merged global types vector.
    std::string resolve_type_for_dex(uint32_t type_idx, uint32_t dex_index) const;
    std::string read_dex_string_from_raw(const std::vector<uint8_t>& raw, uint32_t string_idx,
                                          const dex::DexHeader& hdr) const;
    // EXP-065: Per-DEX string resolution.
    // string_idx is relative to the current DEX file's string_ids table,
    // NOT the merged global strings vector. Using the merged index causes
    // const-string to fetch the WRONG string in multi-DEX apps (e.g.
    // Telegram's classes4.dex string_idx=5975 is "+", but merged_strings[5975]
    // is "FIELD_PREFERRED_AUDIO_LANGUAGES" from classes.dex).
    std::string resolve_string_for_dex(uint32_t string_idx, uint32_t dex_index) const;
    
    bool halted_ = false;
    bool halted_on_return_ = false;
    std::string halt_reason_;
    std::string last_error_;
    // EXP-042 Phase 1: Per-frame loop detection. Reset in execute_method_internal().
    std::map<uint32_t, uint32_t> pc_visit_count_;
    
    // EXP-050 Phase 2: Store the return value from the last invoke-* instruction.
    // move-result and move-result-object read from this. Previously, these
    // opcodes returned placeholder values (0/null), silently discarding ALL
    // return values from ALL method calls. This was a critical hidden bug
    // affecting every if-eqz/if-nez after an invoke, every field access
    // after a getter, and every object creation after new-instance.
    DalvikValue last_invoke_return_ = DalvikValue::make_void();

    // EXP-094 (CM-018): The receiver of the LAST successful "setParams"
    // invoke. Apps with multi-page login flows (Telegram LoginActivity)
    // instantiate SEVERAL views of the same class (one per auth type:
    // MESSAGE/SMS/FLASH_CALL/CALL) — only the one the app configures via
    // setParams is the ACTIVE page. The renderer must use THAT instance,
    // not the first/newest one. This is the app's own navigation signal.
    uint32_t last_set_params_view_ = 0;

public:
    uint32_t last_set_params_view() const { return last_set_params_view_; }
private:

    // EXP-051: Shadow registry pointer. Non-owning. Set by ApplicationRuntime
    // before execution begins. When non-null, bridge_to_api consults the
    // registry BEFORE falling through to the legacy if/else chain.
    framework::ShadowRegistry* shadow_registry_ = nullptr;

    // EXP-052: Exception-handling diagnostic state for the currently
    // executing method. Updated by execute_method_internal() each time
    // a new method is entered. The THROW opcode handler reads these to
    // log whether the current method has a try table and (eventually)
    // find a matching catch handler.
    //
    // The real exception-handling flow is:
    //   1. throw vAA executes.
    //   2. Engine looks up the exception object's class descriptor.
    //   3. Engine scans current_method's tries[] for a try_item whose
    //      [start_addr, start_addr+insn_count) range contains the
    //      current PC.
    //   4. Engine decodes the encoded_catch_handler at handler_off.
    //   5. For each (type_idx, addr) pair in the handler:
    //        - If type_idx == 0 (catch-all) or matches the exception
    //          class, jump to addr.
    //   6. If no handler matched, unwind to the caller's frame and
    //      repeat from step 3 with the caller's PC = the invoke-*
    //      site that called this method.
    //
    // EXP-052 only implements steps 1 + 3 (lookup + log) — the actual
    // handler jump (step 5) is implemented in a later experiment after
    // the diagnostic mode has been validated with small DEX test cases.
    uint16_t current_tries_size_ = 0;
    const uint8_t* current_tries_data_ = nullptr;
    size_t current_tries_data_size_ = 0;

    // EXP-053: Pending exception for move-exception opcode.
    // When THROW jumps to a catch handler, the exception object is
    // stored here. The next move-exception instruction reads from
    // this slot and clears it.
    DalvikValue pending_exception_ = DalvikValue::make_null();
    // (frame_unwind_exception_ members declared near raise_synthetic_exception)

    // EXP-063: Resource lookup maps.
    // field_name_by_resid: maps resource ID → field name (built during R class init)
    // Used to resolve resources when DEX IDs don't match ARSC IDs.
public:
    std::map<int32_t, std::string> field_name_by_resid_;
    // resource_string_values: maps field name → string value (loaded from JSON)
    std::map<std::string, std::string> resource_string_values_;
    // EXP-067: resource_color_values_ maps field name → ARGB int (e.g. 0xFF1A1A1A).
    // Loaded from resource_values.json["color"].
    std::map<std::string, int32_t> resource_color_values_;
    // EXP-067: resource_dimen_values_ maps field name → dimension in pixels (int).
    // Loaded from resource_values.json["dimen"] (values are like "16dp" → 16*dp_factor).
    std::map<std::string, int32_t> resource_dimen_values_;
    // EXP-067: resource_drawable_paths_ maps field name → APK asset path (e.g. "res/abc.webp").
    // Loaded from resource_values.json["drawable"] and ["mipmap"].
    std::map<std::string, std::string> resource_drawable_paths_;
    // UNIFIED_011.2 IMAGE-RES-RENDER (§13/§14 campaign): populate
    // resource_drawable_paths_ from the APK's actual res/ entry list by
    // matching R-field names to drawable file basenames. Prior to this the
    // map was read but NEVER populated (dead resolution chain): the render
    // stage could only draw an "IMG" placeholder for runtime
    // setImageResource() calls. Resolution order per §14 density rule:
    // xxxhdpi > xxhdpi > xhdpi > hdpi > mdpi > plain drawable/.
    void populate_resource_drawable_paths(const std::vector<std::string>& entry_names);
    bool drawable_paths_populated_ = false;
    // EXP-098 (CM-027): resource_raw_paths_ maps R.raw.X name → APK asset
    // path (e.g. "res/-si.json" for R.raw.sms_incoming_info). Used by
    // RLottieImageView.setAnimation(R.raw.X, w, h) → RLottieDrawable →
    // AndroidUtilities.readRes(R.raw.X) → openRawResource. Loaded from
    // resource_values.json["raw"].
    std::map<std::string, std::string> resource_raw_paths_;
    // EXP-098 (CM-027): pending_anim_by_drawable_ maps RLottieDrawable
    // object_id → (raw_resid, w, h). When `new RLottieDrawable(R.raw.X,
    // name, w, h, ...)` is constructed, we record (resid, w, h) here.
    // When the drawable is later attached to an RLottieImageView via
    // setAnimation(RLottieDrawable), the ImageView inherits the pending
    // animation and the render stage decodes the Lottie frame.
    struct PendingAnim {
        int32_t raw_resid = 0;
        int target_w = 0;
        int target_h = 0;
    };
    std::map<uint32_t, PendingAnim> pending_anim_by_drawable_;
    // EXP-067: resource_integer_values_ maps field name → int value.
    std::map<std::string, int32_t> resource_integer_values_;
    // EXP-067: resource_bool_values_ maps field name → bool value.
    std::map<std::string, bool> resource_bool_values_;
    // EXP-071 Phase 6: Asset reading support.
    // When AssetManager.open(asset_name) is called, we extract the asset
    // from the APK and store its contents in a per-InputStream buffer.
    // BufferedReader.readLine() then reads from this buffer line by line.
    // This is needed because Telegram's PhoneView.<init> reads countries.txt
    // from assets to populate the country HashMap — without it, the HashMap
    // is empty, setCountry() returns early, and countryState stays at 1
    // (NO_SIM), causing onNextPressed to take the wrong "ChooseCountry"
    // branch instead of reaching auth.sendCode construction.
    std::string apk_path_;  // path to the APK file
    // EXP-093/F011: Manifest-derived package identity (replaces hardcoded Telegram values)
    std::string package_name_;
    int version_code_ = 0;
    std::string version_name_;
    // EXP-093/F008: Permission state map (permission_name → 0=GRANTED, -1=DENIED)
    std::map<std::string, int> permission_state_;
    // Map: heap object_id (InputStream) → (asset_name, line_index)
    std::map<uint32_t, std::pair<std::string, size_t>> open_assets_;
    // FINAL CANONICAL MASTER RECONCILIATION Pass-3 (K-34): full asset bytes
    // extracted once per path and cached, so InputStream.read()/available()
    // (and readLine) read REAL bytes without re-running `unzip -p` per call.
    std::map<std::string, std::string> asset_bytes_cache_;
    // Pass-3 (K-35): one parser state per parser object (heap id keyed).
    std::map<uint32_t, XmlPullState> xml_parsers_;
private:

    // EXP-053: Set of class descriptors whose <clinit> has been executed.
    // Used to avoid re-running <clinit> on every sget/sput.
    // Per JVM spec, <clinit> runs exactly once when a class is first
    // initialized (typically at first active use: sget/sput/invoke-static
    // /new-instance on the class).
    std::set<std::string> initialized_classes_;

    // EXP-053: Ensure a class is initialized before accessing its static
    // fields. If the class has a <clinit> method and has not been marked
    // initialized, execute <clinit> recursively, then mark it.
    // Returns true if the class is initialized (or initialization was
    // attempted without crashing).
    bool ensure_class_initialized(const std::string& class_descriptor);

    DalvikExecutionResult* current_result_ = nullptr;
    // config_ moved to public section above
    
    bool verbose_ = false;

    // EXP-071: APK path, open_assets_, and current_invoke_is_static_ are
    // declared earlier in this class (lines ~1624-1640). The duplicate
    // declarations that were here were removed in EXP-075 to fix a
    // redeclaration error introduced by the EXP-071 merge.
};

} // namespace dalvik
} // namespace miniandroid

#endif // MINIANDROID_REAL_DALVIK_ENGINE_H
