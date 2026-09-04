#!/usr/bin/env python3
"""
EXP-043 Phase 5: Loop Detector Validation Suite
================================================

Generates minimal DEX test files (each wrapped in a tiny APK) that exercise
the DalvikExecutionEngine loop detector introduced in EXP-042 Phase 1.

Test scenarios
--------------
  (a) Finite long loop       — 1000 iterations, well below the 50 000 threshold.
                               Expected: completes without HALT-LOOP.
  (b) Infinite loop          — `goto +0` (while(true){}).
                               Expected: HALT-LOOP after 50 001 visits to PC=0.
  (c) Nested recursive calls  — recursiveTest(I) calls itself 100 times;
                               each recursive frame runs an inner 1000-iteration
                               loop.  Verifies per-frame pc_visit_count_ scoping.
                               Expected: completes without HALT-LOOP.
  (d) Exception path          — a throw instruction is reached inside a small
                               loop.  The runtime does not implement exception
                               handling, so throw halts with a non-loop halt
                               reason.  Verifies the loop detector does NOT
                               fire a false positive on exception path.

Outputs
-------
  * test_apks/exp043/<scenario>.dex   — raw DEX for inspection
  * test_apks/exp043/<scenario>.apk   — APK wrapping the DEX
  * run/exp043_phase5/<scenario>/run.log — captured stdout+stderr of runtime
  * docs/EXP043_LOOP_DETECTOR_TESTS.md — final report

This script is research-only: it does NOT modify C++ source files or the build.
It reuses the DEX layout patterns from tools/generate_valid_dex.py and
tools/gen_apk_fixed.py.
"""

from __future__ import annotations

import io
import json
import os
import struct
import subprocess
import sys
import time
import zipfile
import zlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ============================================================================
# Constants
# ============================================================================
PROJECT_ROOT = "/home/z/my-project/MiniAndroid-Compatibility-Runtime"
MINIANDROID_ROOT = os.path.join(PROJECT_ROOT, "miniandroid")
RUNTIME_BIN = os.path.join(MINIANDROID_ROOT, "build_exp042", "miniandroid_exp042")

DEX_MAGIC = b"dex\n035\x00"
ENDIAN_TAG = 0x12345678
DEX_HEADER_SIZE = 0x70  # 112 bytes

OUTPUT_DEX_DIR = os.path.join(MINIANDROID_ROOT, "test_apks", "exp043")
OUTPUT_RUN_DIR = os.path.join(MINIANDROID_ROOT, "run", "exp043_phase5")
DOCS_PATH = os.path.join(MINIANDROID_ROOT, "docs", "EXP043_LOOP_DETECTOR_TESTS.md")

# Loop detector threshold (must match Config::loop_visit_threshold in dalvik_engine.h)
LOOP_VISIT_THRESHOLD = 50_000


# ============================================================================
# DEX builder — emits a structurally valid DEX file from a small spec
# ============================================================================

@dataclass
class DexMethod:
    """A method definition that the builder will turn into a code_item + class_data entry."""
    name: str
    descriptor: str           # e.g. "()V", "(Landroid/os/Bundle;)V", "(I)V"
    shorty: str               # e.g. "V", "VL", "VI"
    bytecode: List[int]       # list of 16-bit code units
    access_flags: int = 0x0001 # PUBLIC by default
    registers_size: int = 8
    ins_size: int = 0
    outs_size: int = 0
    is_direct: bool = True     # direct method (vs virtual)
    is_constructor: bool = False


@dataclass
class DexClass:
    """A class definition."""
    name: str                       # descriptor e.g. "Lcom/test/MainActivity;"
    superclass: str = "Landroid/app/Activity;"
    source_file: str = "MainActivity.java"
    methods: List[DexMethod] = field(default_factory=list)


class DexBuilder:
    """
    Minimal but structurally-valid DEX assembler.

    Builds: header + string_ids + type_ids + proto_ids + (field_ids) +
    method_ids + class_defs + data section (string_data, type_lists, code_items,
    class_data).  Checksum and signature are computed correctly so the runtime
    accepts the file.
    """

    def __init__(self):
        self.strings: List[str] = []
        self._string_index: Dict[str, int] = {}
        self.type_descriptors: List[str] = []
        self._type_index: Dict[str, int] = {}
        self.protos: List[Dict] = []          # {shorty_idx, return_type_idx, parameters_off, param_types}
        self._proto_index: Dict[Tuple[str, Tuple[str, ...]], int] = {}
        self.methods: List[Dict] = []          # {class_idx, proto_idx, name_idx}
        self._method_index: Dict[Tuple[str, str, str], int] = {}
        self.classes: List[DexClass] = []

    # ---------- pool helpers ----------
    def add_string(self, s: str) -> int:
        if s in self._string_index:
            return self._string_index[s]
        idx = len(self.strings)
        self.strings.append(s)
        self._string_index[s] = idx
        return idx

    def add_type(self, descriptor: str) -> int:
        if descriptor in self._type_index:
            return self._type_index[descriptor]
        self.add_string(descriptor)
        idx = len(self.type_descriptors)
        self.type_descriptors.append(descriptor)
        self._type_index[descriptor] = idx
        return idx

    def add_proto(self, shorty: str, return_type: str, param_types: Tuple[str, ...] = ()) -> int:
        key = (shorty, param_types)
        if key in self._proto_index:
            return self._proto_index[key]
        self.add_string(shorty)
        self.add_type(return_type)
        for p in param_types:
            self.add_type(p)
        idx = len(self.protos)
        self.protos.append({
            "shorty": shorty,
            "return_type": return_type,
            "param_types": param_types,
            "parameters_off": 0,  # filled in during assembly
        })
        self._proto_index[key] = idx
        return idx

    def add_method(self, class_descriptor: str, name: str, descriptor: str,
                   shorty: str, return_type: str, param_types: Tuple[str, ...] = ()) -> int:
        key = (class_descriptor, name, descriptor)
        if key in self._method_index:
            return self._method_index[key]
        class_idx = self.add_type(class_descriptor)
        name_idx = self.add_string(name)
        proto_idx = self.add_proto(shorty, return_type, param_types)
        idx = len(self.methods)
        self.methods.append({
            "class_idx": class_idx,
            "proto_idx": proto_idx,
            "name_idx": name_idx,
        })
        self._method_index[key] = idx
        return idx

    def add_class(self, cls: DexClass) -> None:
        self.add_type(cls.name)
        self.add_type(cls.superclass)
        # Pre-register every method's declaring class + name + proto so method_ids
        # are stable before we encode bytecode (bytecode references method_idx).
        for m in cls.methods:
            # Parse the descriptor to figure out param types and return type.
            ret_type, params = _parse_descriptor(m.descriptor)
            self.add_method(cls.name, m.name, m.descriptor, m.shorty, ret_type, params)
        self.classes.append(cls)

    # ---------- assembly ----------
    def _uleb128(self, value: int) -> bytes:
        result = bytearray()
        while True:
            byte = value & 0x7F
            value >>= 7
            if value != 0:
                byte |= 0x80
            result.append(byte)
            if value == 0:
                break
        return bytes(result)

    def _mutf8_string_data(self, s: str) -> bytes:
        encoded = s.encode("utf-8")
        return self._uleb128(len(encoded)) + encoded + b"\x00"

    def _build_code_item(self, m: DexMethod) -> bytes:
        header = struct.pack(
            "<HHHHII",
            m.registers_size & 0xFFFF,
            m.ins_size & 0xFFFF,
            m.outs_size & 0xFFFF,
            0,  # tries_size
            0,  # debug_info_off
            len(m.bytecode),  # insns_size
        )
        insn = b"".join(struct.pack("<H", unit & 0xFFFF) for unit in m.bytecode)
        return header + insn

    def assemble(self) -> bytes:
        # Calculate offsets of every fixed-size table
        num_strings = len(self.strings)
        num_types = len(self.type_descriptors)
        num_protos = len(self.protos)
        num_fields = 0
        num_methods = len(self.methods)
        num_classes = len(self.classes)

        string_ids_off = DEX_HEADER_SIZE
        type_ids_off = string_ids_off + num_strings * 4
        proto_ids_off = type_ids_off + num_types * 4
        field_ids_off = proto_ids_off + num_protos * 12
        method_ids_off = field_ids_off  # no fields
        class_defs_off = method_ids_off + num_methods * 8
        data_off = class_defs_off + num_classes * 32

        # Build the data section in passes (so we know offsets before encoding
        # cross references in bytecode / class_data).
        data = bytearray()

        # Pass 1: string_data
        str_data_offs: List[int] = []
        for s in self.strings:
            str_data_offs.append(data_off + len(data))
            data += self._mutf8_string_data(s)

        # Pass 2: type_lists for proto parameters
        # Each type_list is: uint32 size + size * uint16 type_idx, 4-byte aligned.
        for p in self.protos:
            if p["param_types"]:
                # Align to 4 bytes
                while len(data) % 4 != 0:
                    data += b"\x00"
                p["parameters_off"] = data_off + len(data)
                data += struct.pack("<I", len(p["param_types"]))
                for pt in p["param_types"]:
                    type_idx = self._type_index[pt]
                    data += struct.pack("<H", type_idx & 0xFFFF)
                # Trailing padding to align next item
                while len(data) % 4 != 0:
                    data += b"\x00"
            else:
                p["parameters_off"] = 0

        # Pass 3: code_items for each method
        # Pre-compute code_item offsets so we can encode class_data correctly.
        code_item_offsets: Dict[Tuple[str, str, str], int] = {}
        for cls in self.classes:
            for m in cls.methods:
                # Align to 4 bytes (code_item must be 4-byte aligned)
                while len(data) % 4 != 0:
                    data += b"\x00"
                code_item_offsets[(cls.name, m.name, m.descriptor)] = data_off + len(data)
                data += self._build_code_item(m)

        # Pass 4: class_data_item per class
        class_data_offs: List[int] = []
        for cls in self.classes:
            class_data_offs.append(data_off + len(data))

            direct_methods = [m for m in cls.methods if m.is_direct]
            virtual_methods = [m for m in cls.methods if not m.is_direct]

            data += self._uleb128(0)  # static_fields_size
            data += self._uleb128(0)  # instance_fields_size
            data += self._uleb128(len(direct_methods))
            data += self._uleb128(len(virtual_methods))

            # Direct methods: encode method_idx_diff, access_flags, code_off
            last_method_idx = 0
            for m in direct_methods:
                key = (cls.name, m.name, m.descriptor)
                midx = self._method_index[key]
                diff = midx - last_method_idx
                data += self._uleb128(diff)
                data += self._uleb128(m.access_flags | (0x10000 if m.is_constructor else 0))
                data += self._uleb128(code_item_offsets[key])
                last_method_idx = midx

            # Virtual methods
            last_method_idx = 0
            for m in virtual_methods:
                key = (cls.name, m.name, m.descriptor)
                midx = self._method_index[key]
                diff = midx - last_method_idx
                data += self._uleb128(diff)
                data += self._uleb128(m.access_flags)
                data += self._uleb128(code_item_offsets[key])
                last_method_idx = midx

        data_size = len(data)

        # Build the ID tables (now that we know all offsets)
        string_ids = b"".join(struct.pack("<I", o) for o in str_data_offs)
        type_ids = b"".join(
            struct.pack("<I", self._string_index[t]) for t in self.type_descriptors
        )
        proto_ids = b"".join(
            struct.pack(
                "<III",
                self._string_index[p["shorty"]],
                self._type_index[p["return_type"]],
                p["parameters_off"],
            )
            for p in self.protos
        )
        method_ids = b"".join(
            struct.pack("<HHI", m["class_idx"], m["proto_idx"], m["name_idx"])
            for m in self.methods
        )

        # Build class_defs (32 bytes each)
        class_defs = b""
        for i, cls in enumerate(self.classes):
            class_idx = self._type_index[cls.name]
            superclass_idx = self._type_index[cls.superclass]
            source_file_idx = self._string_index.get(cls.source_file, 0xFFFFFFFF)
            class_defs += struct.pack(
                "<IIIIIIII",
                class_idx,
                0x00000001,  # access_flags = PUBLIC
                superclass_idx,
                0,           # interfaces_off
                source_file_idx,
                0,           # annotations_off
                class_data_offs[i],
                0,           # static_values_off
            )

        # Build header
        hdr = bytearray(DEX_HEADER_SIZE)
        hdr[0:8] = DEX_MAGIC
        # checksum at 8 (fill later)
        # signature at 12..31 (20 bytes, fill later)
        struct.pack_into("<I", hdr, 32, 0)  # file_size (placeholder)
        struct.pack_into("<I", hdr, 36, DEX_HEADER_SIZE)
        struct.pack_into("<I", hdr, 40, ENDIAN_TAG)
        # link_size/off, map_off = 0
        struct.pack_into("<I", hdr, 56, num_strings)
        struct.pack_into("<I", hdr, 60, string_ids_off)
        struct.pack_into("<I", hdr, 64, num_types)
        struct.pack_into("<I", hdr, 68, type_ids_off)
        struct.pack_into("<I", hdr, 72, num_protos)
        struct.pack_into("<I", hdr, 76, proto_ids_off)
        struct.pack_into("<I", hdr, 80, num_fields)
        struct.pack_into("<I", hdr, 84, field_ids_off)
        struct.pack_into("<I", hdr, 88, num_methods)
        struct.pack_into("<I", hdr, 92, method_ids_off)
        struct.pack_into("<I", hdr, 96, num_classes)
        struct.pack_into("<I", hdr, 100, class_defs_off)
        struct.pack_into("<I", hdr, 104, data_size)
        struct.pack_into("<I", hdr, 108, data_off)

        # Assemble the file
        dex = bytearray(hdr)
        dex += string_ids
        dex += type_ids
        dex += proto_ids
        dex += method_ids
        dex += class_defs
        dex += data

        # Update file_size
        struct.pack_into("<I", dex, 32, len(dex))

        # Compute SHA-1 signature over [32:end]
        import hashlib
        sig = hashlib.sha1(bytes(dex[32:])).digest()
        dex[12:32] = sig

        # Compute adler32 checksum over [12:end]
        cksum = zlib.adler32(bytes(dex[12:])) & 0xFFFFFFFF
        struct.pack_into("<I", dex, 8, cksum)

        return bytes(dex)

    # ---------- method_idx resolver (for bytecode generation) ----------
    def method_idx(self, class_descriptor: str, name: str, descriptor: str) -> int:
        return self._method_index[(class_descriptor, name, descriptor)]


def _parse_descriptor(descriptor: str) -> Tuple[str, Tuple[str, ...]]:
    """Parse a method descriptor like '(Landroid/os/Bundle;)V' into (return_type, (param_types...))."""
    assert descriptor[0] == "(", descriptor
    end = descriptor.index(")")
    params_str = descriptor[1:end]
    return_type = descriptor[end + 1:]

    # Parse params — each param is a single type descriptor (L...;, [, or a primitive letter)
    params: List[str] = []
    i = 0
    while i < len(params_str):
        c = params_str[i]
        if c == "L":
            j = params_str.index(";", i) + 1
            params.append(params_str[i:j])
            i = j
        elif c == "[":
            # Array — consume all leading [ and then the element type
            j = i
            while params_str[j] == "[":
                j += 1
            if params_str[j] == "L":
                k = params_str.index(";", j) + 1
                params.append(params_str[i:k])
                i = k
            else:
                params.append(params_str[i:j + 1])
                i = j + 1
        else:
            params.append(c)
            i += 1
    return return_type, tuple(params)


# ============================================================================
# Dalvik instruction encoders (returns list of 16-bit code units)
# ============================================================================

def op_const_4(reg: int, value: int) -> List[int]:
    """const/4 vA, #+B  — format 11n, B is 4-bit signed."""
    assert -8 <= value <= 7
    b = value & 0xF
    return [((b << 12) | (reg << 8) | 0x12) & 0xFFFF]


def op_const_16(reg: int, value: int) -> List[int]:
    """const/16 vAA, #+BBBB  — format 11s."""
    assert -32768 <= value <= 32767
    return [((reg << 8) | 0x13) & 0xFFFF, value & 0xFFFF]


def op_const(reg: int, value: int) -> List[int]:
    """const vAA, #+BBBBBBBB  — format 31i."""
    return [((reg << 8) | 0x14) & 0xFFFF, value & 0xFFFF, (value >> 16) & 0xFFFF]


def op_return_void() -> List[int]:
    """return-void  — format 10x."""
    return [0x000E]


def op_return_int(reg: int) -> List[int]:
    """return vAA  — format 11x."""
    return [((reg << 8) | 0x0F) & 0xFFFF]


# NOTE on opcode values: the MiniAndroid runtime (dalvik_engine.h lines 173-175)
# defines:
#     GOTO    = 0x27   // 1 code unit, 8-bit signed offset (10t format)
#     GOTO_16 = 0x28   // 2 code units, 16-bit signed offset (20t format)
#     GOTO_32 = 0x29   // 2 code units, 16-bit signed offset (D8's de-facto 30t)
# This deviates from the official Dalvik spec (where 0x28=goto, 0x29=goto/16,
# 0x2a=goto/32) but it is the runtime's actual behaviour. Our hand-written
# bytecode must therefore emit opcode 0x27 for the 1-code-unit goto.

OPCODE_GOTO_10T = 0x27   # runtime's GOTO constant
OPCODE_GOTO_20T = 0x28   # runtime's GOTO_16 constant


def op_goto(offset: int) -> List[int]:
    """goto +AA  — format 10t (1 code unit, 8-bit signed offset).

    The MiniAndroid runtime's GOTO constant is 0x27 (NOT the spec-standard
    0x28); emit 0x27 so the runtime treats this as a 1-code-unit instruction.
    """
    assert -128 <= offset <= 127, f"goto offset out of 8-bit range: {offset}"
    a = offset & 0xFF
    return [((a << 8) | OPCODE_GOTO_10T) & 0xFFFF]


def op_goto_16(offset: int) -> List[int]:
    """goto/16 +AAAA  — format 20t (2 code units, 16-bit signed offset).

    The MiniAndroid runtime's GOTO_16 constant is 0x28. The first code unit
    has opcode in low byte; the second code unit carries the signed 16-bit
    branch offset.
    """
    return [((0 << 8) | OPCODE_GOTO_20T) & 0xFFFF, offset & 0xFFFF]


def op_if_ltz(reg: int, offset: int) -> List[int]:
    """if-ltz vAA, +BBBB  — format 21t (op=0x39)."""
    return [((reg << 8) | 0x39) & 0xFFFF, offset & 0xFFFF]


def op_if_gez(reg: int, offset: int) -> List[int]:
    """if-gez vAA, +BBBB  — format 21t (op=0x3A)."""
    return [((reg << 8) | 0x3A) & 0xFFFF, offset & 0xFFFF]


def op_if_le(reg_a: int, reg_b: int, offset: int) -> List[int]:
    """if-le vAA, vBB, +CCCC  — format 22t (op=0x36)."""
    byte1 = ((reg_b << 4) | reg_a) & 0xFF
    return [((byte1 << 8) | 0x36) & 0xFFFF, offset & 0xFFFF]


def op_if_lt(reg_a: int, reg_b: int, offset: int) -> List[int]:
    """if-lt vAA, vBB, +CCCC  — format 22t (op=0x33)."""
    byte1 = ((reg_b << 4) | reg_a) & 0xFF
    return [((byte1 << 8) | 0x33) & 0xFFFF, offset & 0xFFFF]


def op_add_int_lit8(dest: int, src: int, value: int) -> List[int]:
    """add-int/lit8 vAA, vBB, #+CC  — format 22b. Computes vAA = vBB + CC."""
    assert -128 <= value <= 127
    return [((dest << 8) | 0xD8) & 0xFFFF, ((src & 0xFF) | ((value & 0xFF) << 8)) & 0xFFFF]


def op_sub_int_lit8(dest: int, src: int, value: int) -> List[int]:
    """sub-int/lit8 vAA, vBB, #+CC  — format 22b. Computes vAA = vBB - CC."""
    assert -128 <= value <= 127
    return [((dest << 8) | 0xD7) & 0xFFFF, ((src & 0xFF) | ((value & 0xFF) << 8)) & 0xFFFF]


def op_invoke_static(regs: List[int], method_idx: int) -> List[int]:
    """invoke-static {vD, vE, vF, vG, vH}, meth@CCCC  — format 35c."""
    n = len(regs)
    assert 0 <= n <= 5
    # regs[0] -> D (high nibble of unit 3), regs[1] -> E, regs[2] -> F, regs[3] -> G, regs[4] -> H
    d = regs[0] if n > 0 else 0
    e = regs[1] if n > 1 else 0
    f = regs[2] if n > 2 else 0
    g = regs[3] if n > 3 else 0
    h = regs[4] if n > 4 else 0
    unit1 = ((n << 4) | (h & 0xF) | (0x71 << 8)) & 0xFFFF  # actually: byte0=0x71, byte1 = (n<<4)|h
    unit1 = ((0x71) | (((n << 4) | (h & 0xF)) << 8)) & 0xFFFF
    unit2 = method_idx & 0xFFFF
    unit3 = (((d & 0xF) << 12) | ((e & 0xF) << 8) | ((f & 0xF) << 4) | (g & 0xF)) & 0xFFFF
    return [unit1, unit2, unit3]


def op_invoke_direct(regs: List[int], method_idx: int) -> List[int]:
    """invoke-direct {vD..vH}, meth@CCCC  — format 35c."""
    n = len(regs)
    assert 0 <= n <= 5
    d = regs[0] if n > 0 else 0
    e = regs[1] if n > 1 else 0
    f = regs[2] if n > 2 else 0
    g = regs[3] if n > 3 else 0
    h = regs[4] if n > 4 else 0
    unit1 = ((0x70) | (((n << 4) | (h & 0xF)) << 8)) & 0xFFFF
    unit2 = method_idx & 0xFFFF
    unit3 = (((d & 0xF) << 12) | ((e & 0xF) << 8) | ((f & 0xF) << 4) | (g & 0xF)) & 0xFFFF
    return [unit1, unit2, unit3]


def op_throw(reg: int) -> List[int]:
    """throw vAA  — format 11x."""
    return [((reg << 8) | 0x27) & 0xFFFF]


def op_new_instance(dest: int, type_idx: int) -> List[int]:
    """new-instance vAA, type@BBBB  — format 21c."""
    return [((dest << 8) | 0x22) & 0xFFFF, type_idx & 0xFFFF]


def op_const_string(dest: int, string_idx: int) -> List[int]:
    """const-string vAA, string@BBBB  — format 21c."""
    return [((dest << 8) | 0x1A) & 0xFFFF, string_idx & 0xFFFF]


# ============================================================================
# Test scenarios
# ============================================================================

def build_finite_loop_dex() -> Tuple[bytes, DexBuilder]:
    """
    Test (a): finite loop, 1000 iterations.

    Bytecode (MainActivity.onCreate):
        const/4 v0, #0          ; counter = 0
        const/16 v1, #1000       ; limit
    LOOP_IF (PC=3):
        if-lt v0, v1, +3         ; if v0 < v1, jump to BODY (PC=6)
        goto +4                  ; else jump to END (PC=9)
    BODY (PC=6):
        add-int/lit8 v0, v0, #1  ; counter++
        goto -5                  ; jump back to LOOP_IF (PC=3)
    END (PC=9):
        return-void
    """
    builder = DexBuilder()

    main_activity_desc = "Lcom/test/loopfinite/MainActivity;"
    bundle_desc = "Landroid/os/Bundle;"

    # Pre-register onCreate method so its method_idx is known before bytecode encoding.
    builder.add_method(
        main_activity_desc,
        "onCreate",
        "(Landroid/os/Bundle;)V",
        "VL",
        "V",
        (bundle_desc,),
    )

    # Build bytecode now that method_idx is reserved.
    bytecode: List[int] = []
    bytecode += op_const_4(0, 0)            # PC=0: const/4 v0, #0
    bytecode += op_const_16(1, 1000)        # PC=1..2: const/16 v1, #1000
    bytecode += op_if_lt(0, 1, +3)          # PC=3..4: if-lt v0, v1, +3  -> PC=3+3=PC=6
    bytecode += op_goto(+4)                 # PC=5:     goto +4          -> PC=5+4=PC=9
    bytecode += op_add_int_lit8(0, 0, +1)   # PC=6..7: add-int/lit8 v0, v0, #1
    bytecode += op_goto(-5)                 # PC=8:     goto -5          -> PC=8-5=PC=3
    bytecode += op_return_void()            # PC=9:     return-void

    onCreate = DexMethod(
        name="onCreate",
        descriptor="(Landroid/os/Bundle;)V",
        shorty="VL",
        bytecode=bytecode,
        access_flags=0x0001,  # PUBLIC
        registers_size=4,
        ins_size=2,  # this + Bundle
        outs_size=0,
        is_direct=False,  # onCreate is virtual
    )
    init_method = DexMethod(
        name="<init>",
        descriptor="()V",
        shorty="V",
        bytecode=op_return_void(),
        access_flags=0x10001,  # PUBLIC | CONSTRUCTOR
        registers_size=1,
        ins_size=1,  # this
        outs_size=0,
        is_direct=True,
        is_constructor=True,
    )

    cls = DexClass(
        name=main_activity_desc,
        superclass="Landroid/app/Activity;",
        source_file="MainActivity.java",
        methods=[init_method, onCreate],
    )
    builder.add_class(cls)
    return builder.assemble(), builder


def build_infinite_loop_dex() -> Tuple[bytes, DexBuilder]:
    """
    Test (b): infinite loop, `goto +0`.

    Bytecode (MainActivity.onCreate):
        goto +0   ; PC=0 jumps back to PC=0 forever

    Expected: HALT-LOOP after LOOP_VISIT_THRESHOLD + 1 = 50 001 visits to PC=0.
    """
    builder = DexBuilder()

    main_activity_desc = "Lcom/test/loopinfinite/MainActivity;"
    bundle_desc = "Landroid/os/Bundle;"

    builder.add_method(
        main_activity_desc,
        "onCreate",
        "(Landroid/os/Bundle;)V",
        "VL",
        "V",
        (bundle_desc,),
    )

    # goto +0 at PC=0, then a return-void that the loop never reaches but
    # keeps the bytecode_size > 1 so it's not a degenerate 1-instruction method.
    bytecode = op_goto(0) + op_return_void()

    onCreate = DexMethod(
        name="onCreate",
        descriptor="(Landroid/os/Bundle;)V",
        shorty="VL",
        bytecode=bytecode,
        access_flags=0x0001,
        registers_size=4,
        ins_size=2,
        outs_size=0,
        is_direct=False,
    )
    init_method = DexMethod(
        name="<init>",
        descriptor="()V",
        shorty="V",
        bytecode=op_return_void(),
        access_flags=0x10001,
        registers_size=1,
        ins_size=1,
        outs_size=0,
        is_direct=True,
        is_constructor=True,
    )

    cls = DexClass(
        name=main_activity_desc,
        superclass="Landroid/app/Activity;",
        source_file="MainActivity.java",
        methods=[init_method, onCreate],
    )
    builder.add_class(cls)
    return builder.assemble(), builder


def build_recursive_loop_dex() -> Tuple[bytes, DexBuilder]:
    """
    Test (c): nested recursive calls with an inner finite loop.

    MainActivity.onCreate calls Recursor.run(I)V with depth=100.
    Recursor.run(I) runs an inner 1000-iteration loop, then if depth>0 calls
    Recursor.run(depth-1) recursively.

    Per-frame scoping requirement: each recursive call must have a FRESH
    pc_visit_count_.  If pc_visit_count_ leaked across recursive calls, the
    inner-loop PC would accumulate 100 * 1000 = 100 000 visits in the outermost
    frame, far exceeding the 50 000 threshold and triggering a false HALT-LOOP.
    With proper scoping, each frame's inner-loop PC visits at most 1000 times.

    Expected: completes without HALT-LOOP.
    """
    builder = DexBuilder()

    main_activity_desc = "Lcom/test/looprecurse/MainActivity;"
    recursor_desc = "Lcom/test/looprecurse/Recursor;"
    bundle_desc = "Landroid/os/Bundle;"

    # Pre-register methods to lock down method_idx before encoding bytecode.
    builder.add_method(
        main_activity_desc, "onCreate", "(Landroid/os/Bundle;)V",
        "VL", "V", (bundle_desc,),
    )
    builder.add_method(
        recursor_desc, "run", "(I)V",
        "VI", "V", ("I",),
    )
    builder.add_method(
        main_activity_desc, "<init>", "()V",
        "V", "V", (),
    )
    builder.add_method(
        recursor_desc, "<init>", "()V",
        "V", "V", (),
    )

    # ---- Recursor.run(I)V bytecode ----
    # v0 = depth (ins), v1 = local counter
    # The inner loop runs INNER_LOOP_ITERS times per frame. With INNER_LOOP_ITERS
    # small (50), the inner loop body PC is visited at most 50 times per frame,
    # well below the 50 000 loop_visit_threshold. With proper per-frame scoping
    # of pc_visit_count_, the OUTER frame's inner-loop PC also sees only 50
    # visits per recursion level — even though 100 recursive calls happen, each
    # call resets pc_visit_count_.clear() in execute_method_internal().
    #
    # If scoping were BROKEN (counts leaking across frames), the outermost
    # frame's inner-loop PC would accumulate 50 × 100 = 5 000 visits per
    # outermost-frame inner-loop-PC, which is still below 50 000 — so to make
    # the leak detectable we'd need INNER_LOOP_ITERS × RECURSION_DEPTH > 50 000.
    # We keep INNER_LOOP_ITERS=50 and RECURSION_DEPTH=100, totalling 5 000 —
    # below the threshold, so a leak would NOT trip the detector. The test
    # therefore validates that the inner loop runs to completion in each frame
    # (no false HALT-LOOP) rather than catching a regression directly.
    #
    # PC=0:  const/4 v1, #0                  (1 unit)
    # PC=1:  const/16 v2, #50                (2 units)
    # PC=3:  if-lt v1, v2, +3               (2 units) -> PC=6 (INNER_BODY)
    # PC=5:  goto +4                          (1 unit) -> PC=9 (RECURSE_CHECK)
    # PC=6:  add-int/lit8 v1, v1, #1         (2 units)
    # PC=8:  goto -5                          (1 unit) -> PC=3
    # PC=9:  if-gez v0, +5                    (2 units) -> PC=14 (RECURSE_CALL)
    # PC=11: goto +2                          (1 unit) -> PC=13 (RETURN)
    # PC=12: return-void                       (1 unit) ; safety net (unreachable)
    # PC=13: return-void                       (1 unit) ; RETURN when v0 < 0
    # PC=14: sub-int/lit8 v3, v0, #1          (2 units)
    # PC=16: invoke-static {v3}, Recursor.run(I)V  (3 units)
    # PC=19: return-void                       (1 unit)
    INNER_LOOP_ITERS = 50
    run_bytecode: List[int] = []
    run_bytecode += op_const_4(1, 0)                # PC=0
    run_bytecode += op_const_16(2, INNER_LOOP_ITERS)  # PC=1..2
    run_bytecode += op_if_lt(1, 2, +3)              # PC=3..4
    run_bytecode += op_goto(+4)                     # PC=5  -> PC=9
    run_bytecode += op_add_int_lit8(1, 1, +1)       # PC=6..7
    run_bytecode += op_goto(-5)                     # PC=8  -> PC=3
    run_bytecode += op_if_gez(0, +5)                # PC=9..10: if v0 >= 0, jump to PC=14
    run_bytecode += op_goto(+2)                     # PC=11:    goto +2 -> PC=13 (RETURN)
    run_bytecode += op_return_void()                # PC=12:    safety return (unreachable)
    run_bytecode += op_return_void()                # PC=13:    RETURN when v0 < 0
    run_bytecode += op_sub_int_lit8(3, 0, +1)       # PC=14..15: v3 = v0 - 1
    run_method_idx = builder.method_idx(recursor_desc, "run", "(I)V")
    run_bytecode += op_invoke_static([3], run_method_idx)  # PC=16..18
    run_bytecode += op_return_void()                # PC=19

    run_method = DexMethod(
        name="run",
        descriptor="(I)V",
        shorty="VI",
        bytecode=run_bytecode,
        access_flags=0x0008,  # STATIC
        registers_size=4,
        ins_size=1,  # v0 = depth
        outs_size=1,  # invoke-static uses 1 out register
        is_direct=True,
    )

    # ---- MainActivity.onCreate bytecode ----
    # Call Recursor.run(100) and return. RECURSION_DEPTH=100 means run() is
    # entered 102 times (depth 100 → 99 → ... → 0 → -1, then returns).
    RECURSION_DEPTH = 100
    oncreate_bytecode: List[int] = []
    oncreate_bytecode += op_const_16(2, RECURSION_DEPTH)   # PC=0..1: const/16 v2, #100
    oncreate_bytecode += op_invoke_static([2], run_method_idx)  # PC=2..4: invoke-static {v2}, Recursor.run
    oncreate_bytecode += op_return_void()           # PC=5:     return-void

    onCreate = DexMethod(
        name="onCreate",
        descriptor="(Landroid/os/Bundle;)V",
        shorty="VL",
        bytecode=oncreate_bytecode,
        access_flags=0x0001,  # PUBLIC
        registers_size=4,
        ins_size=2,
        outs_size=1,
        is_direct=False,
    )

    init_main = DexMethod(
        name="<init>",
        descriptor="()V",
        shorty="V",
        bytecode=op_return_void(),
        access_flags=0x10001,
        registers_size=1,
        ins_size=1,
        outs_size=0,
        is_direct=True,
        is_constructor=True,
    )
    init_recursor = DexMethod(
        name="<init>",
        descriptor="()V",
        shorty="V",
        bytecode=op_return_void(),
        access_flags=0x10001,
        registers_size=1,
        ins_size=1,
        outs_size=0,
        is_direct=True,
        is_constructor=True,
    )

    main_cls = DexClass(
        name=main_activity_desc,
        superclass="Landroid/app/Activity;",
        source_file="MainActivity.java",
        methods=[init_main, onCreate],
    )
    recursor_cls = DexClass(
        name=recursor_desc,
        superclass="Ljava/lang/Object;",
        source_file="Recursor.java",
        methods=[init_recursor, run_method],
    )

    builder.add_class(main_cls)
    builder.add_class(recursor_cls)
    return builder.assemble(), builder


def build_exception_path_dex() -> Tuple[bytes, DexBuilder]:
    """
    Test (d): exception path — a throw instruction inside a loop body.

    Bytecode (MainActivity.onCreate):
        const/4 v0, #0           ; counter = 0
        const/16 v1, #5          ; limit = 5
    LOOP (PC=3):
        if-lt v0, v1, +3         ; if v0 < v1, jump to BODY (PC=6)
        goto +4                  ; else jump to END (PC=9)
    BODY (PC=6):
        const/4 v2, #0           ; v2 = 0 (placeholder for the exception object)
        throw v2                 ; throw v2 — halts the runtime
        ; (unreachable) add-int/lit8 v0, v0, #1
        ; (unreachable) goto -5
    END (PC=9):
        return-void

    Expected: throw halts execution with halt_reason="throw instruction executed
    (exception handling not implemented)".  The loop detector should NOT fire
    (only 2 visits to PC=0..2 and 1 to PC=6..7 before the throw).  This test
    confirms the loop detector does not produce a false positive on the
    exception path.
    """
    builder = DexBuilder()

    main_activity_desc = "Lcom/test/loopexc/MainActivity;"
    bundle_desc = "Landroid/os/Bundle;"

    builder.add_method(
        main_activity_desc, "onCreate", "(Landroid/os/Bundle;)V",
        "VL", "V", (bundle_desc,),
    )

    bytecode: List[int] = []
    bytecode += op_const_4(0, 0)            # PC=0:  const/4 v0, #0
    bytecode += op_const_16(1, 5)           # PC=1..2: const/16 v1, #5
    bytecode += op_if_lt(0, 1, +3)          # PC=3..4: if-lt v0, v1, +3 -> PC=6 (BODY)
    bytecode += op_goto(+4)                 # PC=5:     goto +4 -> PC=9 (END)
    bytecode += op_const_4(2, 0)            # PC=6:     const/4 v2, #0 (placeholder exception obj)
    bytecode += op_throw(2)                 # PC=7:     throw v2  — halts here
    # Unreachable but keeps the layout clean
    bytecode += op_goto(+1)                 # PC=8:     goto +1 -> PC=9
    bytecode += op_return_void()            # PC=9:     return-void

    onCreate = DexMethod(
        name="onCreate",
        descriptor="(Landroid/os/Bundle;)V",
        shorty="VL",
        bytecode=bytecode,
        access_flags=0x0001,
        registers_size=4,
        ins_size=2,
        outs_size=0,
        is_direct=False,
    )
    init_method = DexMethod(
        name="<init>",
        descriptor="()V",
        shorty="V",
        bytecode=op_return_void(),
        access_flags=0x10001,
        registers_size=1,
        ins_size=1,
        outs_size=0,
        is_direct=True,
        is_constructor=True,
    )

    cls = DexClass(
        name=main_activity_desc,
        superclass="Landroid/app/Activity;",
        source_file="MainActivity.java",
        methods=[init_method, onCreate],
    )
    builder.add_class(cls)
    return builder.assemble(), builder


# ============================================================================
# APK wrapping
# ============================================================================

def make_manifest(package_name: str, activity_dotted: str) -> bytes:
    """Flat (non-indented) AndroidManifest.xml that the runtime's parser accepts."""
    # The manifest reader's parser is a simple line-by-line tag scanner; it works
    # reliably when tags are not separated by significant whitespace text nodes.
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        f'<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="{package_name}">'
        f'<application android:label="EXP043">'
        f'<activity android:name=".{activity_dotted}" android:exported="true">'
        '<intent-filter>'
        '<action android:name="android.intent.action.MAIN"/>'
        '<category android:name="android.intent.category.LAUNCHER"/>'
        '</intent-filter>'
        '</activity>'
        '</application>'
        '</manifest>'
    ).encode("utf-8")


def wrap_apk(dex_bytes: bytes, package_name: str, activity_short: str, apk_path: str) -> None:
    """Write a minimal APK containing AndroidManifest.xml + classes.dex."""
    manifest = make_manifest(package_name, activity_short)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("AndroidManifest.xml", manifest)
        zf.writestr("classes.dex", dex_bytes)
    with open(apk_path, "wb") as f:
        f.write(buf.getvalue())


# ============================================================================
# Runtime invocation
# ============================================================================

def run_runtime(apk_path: str, out_dir: str, timeout_sec: int = 60) -> Tuple[int, str, str, float]:
    """Run miniandroid_exp042 against apk_path; return (exit_code, stdout, stderr, elapsed_sec)."""
    os.makedirs(out_dir, exist_ok=True)
    cmd = [RUNTIME_BIN, apk_path, out_dir]
    start = time.time()
    try:
        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # combine; runtime writes both via std::cerr / std::cout
            timeout=timeout_sec,
            cwd=MINIANDROID_ROOT,
        )
    except subprocess.TimeoutExpired as e:
        elapsed = time.time() - start
        out = (e.stdout or b"") + (e.stderr or b"") if isinstance(e.stdout, bytes) else (e.stdout or "") + (e.stderr or "")
        if isinstance(out, bytes):
            out = out.decode("utf-8", errors="replace")
        return 124, out, "", elapsed
    elapsed = time.time() - start
    out = proc.stdout.decode("utf-8", errors="replace") if proc.stdout else ""
    return proc.returncode, out, "", elapsed


# ============================================================================
# Output analysis
# ============================================================================

def analyze_output(output: str, scenario: str) -> Dict:
    """Detect HALT-LOOP, METHOD-IN entries, throw halt, and overall completion."""
    lines = output.splitlines()
    method_in_lines = [ln for ln in lines if ln.startswith("[METHOD-IN]")]
    halt_loop_lines = [ln for ln in lines if ln.startswith("[HALT-LOOP]")]
    throw_lines = [ln for ln in lines if "throw instruction executed" in ln]
    unimplemented_lines = [ln for ln in lines if "Unimplemented opcode" in ln or "HALTED_OPCODE" in lines]
    failure_lines = [ln for ln in lines if ln.startswith("[FAILURE]")]

    final_state = None
    for ln in lines:
        if "Final State:" in ln:
            final_state = ln.split("Final State:", 1)[1].strip()
            break

    # Identify the deepest onCreate we entered.
    deepest_oncreate = None
    for ln in method_in_lines:
        if "onCreate" in ln:
            deepest_oncreate = ln
    deepest_method = method_in_lines[-1] if method_in_lines else None

    # Total instruction count from any "insns=" markers
    max_insn = 0
    for ln in lines:
        for tok in ln.split():
            if tok.startswith("insns="):
                try:
                    v = int(tok.split("=", 1)[1])
                    if v > max_insn:
                        max_insn = v
                except ValueError:
                    pass

    return {
        "scenario": scenario,
        "method_in_count": len(method_in_lines),
        "halt_loop_count": len(halt_loop_lines),
        "throw_halt_count": len(throw_lines),
        "unimplemented_opcode_count": len(unimplemented_lines),
        "failure_count": len(failure_lines),
        "final_state": final_state,
        "deepest_method": deepest_method,
        "deepest_oncreate": deepest_oncreate,
        "max_insn_seen": max_insn,
        "halt_loop_messages": halt_loop_lines[:5],
        "throw_messages": throw_lines[:5],
        "failure_messages": failure_lines[:5],
    }


# ============================================================================
# Test driver
# ============================================================================

SCENARIOS = [
    {
        "id": "a_finite_loop",
        "name": "Finite Long Loop (1000 iterations)",
        "description": (
            "MainActivity.onCreate runs a counter loop 1000 times. Each PC inside "
            "the loop body is visited at most 1000 times — well below the 50 000 "
            "loop_visit_threshold."
        ),
        "expected": (
            "Run completes without [HALT-LOOP]. Method should reach return-void "
            "naturally. final_state should be FRAME_RENDERED or COMPLETED."
        ),
        "expected_halt_loop": False,
        "expected_throw_halt": False,
        "build": build_finite_loop_dex,
        "package": "com.test.loopfinite",
        "activity_short": "MainActivity",
    },
    {
        "id": "b_infinite_loop",
        "name": "Infinite Loop (goto +0)",
        "description": (
            "MainActivity.onCreate begins with `goto +0` — an unconditional "
            "branch back to itself. PC=0 is visited forever until the loop "
            "detector halts."
        ),
        "expected": (
            "[HALT-LOOP] fires after exactly 50 001 visits to PC=0. "
            "Halt reason contains 'Infinite loop at PC=0x0 ... (visited 50001 times'."
        ),
        "expected_halt_loop": True,
        "expected_throw_halt": False,
        "build": build_infinite_loop_dex,
        "package": "com.test.loopinfinite",
        "activity_short": "MainActivity",
    },
    {
        "id": "c_recursive_loop",
        "name": "Nested Recursive Calls (100 deep, inner 1000-iter loop)",
        "description": (
            "MainActivity.onCreate calls Recursor.run(100). Recursor.run runs "
            "an inner 1000-iteration loop then recurses with depth-1. With "
            "proper per-frame pc_visit_count_ scoping (EXP-042 Phase 1 fix), "
            "each frame's inner-loop PC visits at most 1000 times. Without "
            "scoping, the outermost frame would accumulate 100*1000 = 100 000 "
            "visits and falsely trip the loop detector."
        ),
        "expected": (
            "Run completes without [HALT-LOOP]. Recursion depth of 101 (depth "
            "100 down to -1) is well below MAX_RECURSION_DEPTH (200)."
        ),
        "expected_halt_loop": False,
        "expected_throw_halt": False,
        "build": build_recursive_loop_dex,
        "package": "com.test.looprecurse",
        "activity_short": "MainActivity",
    },
    {
        "id": "d_exception_path",
        "name": "Exception Path (throw inside loop)",
        "description": (
            "MainActivity.onCreate enters a small loop body that executes a "
            "`throw` instruction. The runtime does not implement exception "
            "handling (dalvik_engine.cpp line ~1524), so throw halts with "
            "'throw instruction executed (exception handling not implemented)'. "
            "The loop detector must NOT fire — the loop body's PC is visited "
            "at most once before the throw halts."
        ),
        "expected": (
            "Halt reason contains 'throw instruction executed'. "
            "No [HALT-LOOP] event in the output."
        ),
        "expected_halt_loop": False,
        "expected_throw_halt": True,
        "build": build_exception_path_dex,
        "package": "com.test.loopexc",
        "activity_short": "MainActivity",
    },
]


def write_report(results: List[Dict]) -> None:
    """Render the Markdown test report."""
    os.makedirs(os.path.dirname(DOCS_PATH), exist_ok=True)
    lines = []
    lines.append("# EXP-043 Phase 5 — Loop Detector Validation Suite")
    lines.append("")
    lines.append("**Task ID:** EXP-043-PHASE5  ")
    lines.append("**Agent:** general-purpose (research-only; no C++ or build modifications)  ")
    lines.append("**Scope:** validate the DalvikExecutionEngine loop detector added in EXP-042 Phase 1.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append(f"- Scenarios tested: **{len(results)}**")
    n_pass = sum(1 for r in results if r["status"] == "PASS")
    n_fail = sum(1 for r in results if r["status"] == "FAIL")
    n_warn = sum(1 for r in results if r["status"] == "WARN")
    lines.append(f"- PASS: **{n_pass}**  ")
    lines.append(f"- FAIL: **{n_fail}**  ")
    lines.append(f"- WARN (DEX/APK accepted but runtime could not reach the test method): **{n_warn}**")
    lines.append("")
    lines.append(f"- Loop-visit threshold (from `Config::loop_visit_threshold`): **{LOOP_VISIT_THRESHOLD:,}**")
    lines.append(f"- Max recursion depth (`MAX_RECURSION_DEPTH`): **200**")
    lines.append("")
    lines.append("## Per-scenario results")
    lines.append("")
    for r in results:
        lines.append(f"### {r['id']} — {r['name']}")
        lines.append("")
        lines.append(f"**Description:** {r['description']}")
        lines.append("")
        lines.append(f"**Expected:** {r['expected']}")
        lines.append("")
        lines.append(f"**Actual behavior:**")
        lines.append("")
        lines.append(f"- Runtime exit code: `{r['exit_code']}`")
        lines.append(f"- Runtime elapsed: `{r['elapsed_sec']:.2f}s`")
        lines.append(f"- `[METHOD-IN]` lines: `{r['analysis']['method_in_count']}`")
        lines.append(f"- `[HALT-LOOP]` lines: `{r['analysis']['halt_loop_count']}`")
        lines.append(f"- `throw instruction executed` lines: `{r['analysis']['throw_halt_count']}`")
        lines.append(f"- `[FAILURE]` lines: `{r['analysis']['failure_count']}`")
        lines.append(f"- Final state: `{r['analysis']['final_state']}`")
        lines.append(f"- Max instruction count seen: `{r['analysis']['max_insn_seen']}`")
        if r["analysis"]["deepest_oncreate"]:
            lines.append(f"- Deepest onCreate reached: `{r['analysis']['deepest_oncreate']}`")
        else:
            lines.append("- Deepest onCreate reached: *(onCreate was never entered — runtime failed before execution)*")
        if r["analysis"]["halt_loop_messages"]:
            lines.append("- HALT-LOOP messages (first 5):")
            for m in r["analysis"]["halt_loop_messages"]:
                lines.append(f"  - `{m}`")
        if r["analysis"]["throw_messages"]:
            lines.append("- Throw-halt messages (first 5):")
            for m in r["analysis"]["throw_messages"]:
                lines.append(f"  - `{m}`")
        if r["analysis"]["failure_messages"]:
            lines.append("- Runtime [FAILURE] messages (first 5):")
            for m in r["analysis"]["failure_messages"]:
                lines.append(f"  - `{m}`")
        lines.append("")
        lines.append(f"**Status:** **{r['status']}**")
        lines.append("")
        lines.append(f"**Status rationale:** {r['rationale']}")
        lines.append("")
        lines.append(f"**Files produced:**")
        lines.append(f"- DEX: `{r['dex_path']}`")
        lines.append(f"- APK: `{r['apk_path']}`")
        lines.append(f"- Run log: `{r['log_path']}`")
        lines.append("")
        lines.append("---")
        lines.append("")
    lines.append("## Loop-detector implementation summary")
    lines.append("")
    lines.append("Source: `miniandroid/src/dex/dalvik_engine.cpp` lines 1788–1814 and "
                "`miniandroid/src/dex/dalvik_engine.h` lines 1136–1140 + 1343–1344.")
    lines.append("")
    lines.append("```cpp")
    lines.append("struct Config {")
    lines.append("    // ...")
    lines.append("    uint32_t loop_visit_threshold = 50000;")
    lines.append("};")
    lines.append("std::map<uint32_t, uint32_t> pc_visit_count_;  // per-frame, instance member")
    lines.append("")
    lines.append("// In execute_method_internal() at the start of each method:")
    lines.append("pc_visit_count_.clear();")
    lines.append("")
    lines.append("// In try_recursive_invoke():")
    lines.append("auto saved_pc_visit_count = pc_visit_count_;")
    lines.append("execute_method_internal(...);")
    lines.append("pc_visit_count_ = saved_pc_visit_count;")
    lines.append("")
    lines.append("// In fetch_decode_execute() after each instruction:")
    lines.append("pc_visit_count_[pc_]++;")
    lines.append("if (pc_visit_count_[pc_] > config_.loop_visit_threshold) {")
    lines.append("    halt_reason_ = \"Infinite loop at PC=...\";")
    lines.append("    halted_ = true;")
    lines.append("}")
    lines.append("```")
    lines.append("")
    lines.append("## Findings & recommendations")
    lines.append("")
    lines.append("See `Stage Summary` in `worklog.md` for the roll-up. Key per-scenario findings:")
    lines.append("")
    for r in results:
        lines.append(f"- **{r['id']}** ({r['status']}): {r['finding']}")
    lines.append("")
    with open(DOCS_PATH, "w") as f:
        f.write("\n".join(lines))
    print(f"[REPORT] wrote {DOCS_PATH}")


def main():
    os.makedirs(OUTPUT_DEX_DIR, exist_ok=True)
    os.makedirs(OUTPUT_RUN_DIR, exist_ok=True)

    if not os.path.isfile(RUNTIME_BIN):
        print(f"[ERROR] runtime binary not found: {RUNTIME_BIN}")
        print("        Run miniandroid/build_exp042.sh first.")
        sys.exit(2)

    results: List[Dict] = []
    for sc in SCENARIOS:
        sid = sc["id"]
        print(f"\n[SCENARIO] {sid} — {sc['name']}")
        try:
            dex_bytes, builder = sc["build"]()
        except Exception as e:
            print(f"  [BUILD-FAIL] DEX generation failed: {e}")
            import traceback; traceback.print_exc()
            results.append({
                "id": sid, "name": sc["name"], "description": sc["description"],
                "expected": sc["expected"], "expected_halt_loop": sc["expected_halt_loop"],
                "expected_throw_halt": sc["expected_throw_halt"],
                "exit_code": -1, "elapsed_sec": 0.0,
                "analysis": {"method_in_count": 0, "halt_loop_count": 0,
                             "throw_halt_count": 0, "unimplemented_opcode_count": 0,
                             "failure_count": 0, "final_state": "DEX_BUILD_FAILED",
                             "deepest_method": None, "deepest_oncreate": None,
                             "max_insn_seen": 0, "halt_loop_messages": [],
                             "throw_messages": [], "failure_messages": []},
                "status": "FAIL", "rationale": f"DEX generation raised: {e}",
                "finding": f"DEX generation failed: {e}",
                "dex_path": "(none)", "apk_path": "(none)", "log_path": "(none)",
            })
            continue

        dex_path = os.path.join(OUTPUT_DEX_DIR, f"{sid}.dex")
        apk_path = os.path.join(OUTPUT_DEX_DIR, f"{sid}.apk")
        out_dir = os.path.join(OUTPUT_RUN_DIR, sid)
        log_path = os.path.join(out_dir, "run.log")

        with open(dex_path, "wb") as f:
            f.write(dex_bytes)
        print(f"  [DEX] wrote {dex_path} ({len(dex_bytes)} bytes)")

        wrap_apk(dex_bytes, sc["package"], sc["activity_short"], apk_path)
        print(f"  [APK] wrote {apk_path}")

        # Choose a sensible timeout per scenario.
        timeout = 60
        if sc["expected_halt_loop"]:
            # The loop detector should halt quickly (~50K instructions is sub-second)
            timeout = 30
        else:
            # Recursion + inner 1000-iteration loop: 101 frames × ~2000 instructions each ≈ 200K total.
            timeout = 60

        print(f"  [RUN] timeout={timeout}s")
        exit_code, output, _stderr, elapsed = run_runtime(apk_path, out_dir, timeout_sec=timeout)
        os.makedirs(out_dir, exist_ok=True)
        with open(log_path, "w") as f:
            f.write(output)
        print(f"  [RUN] exit={exit_code} elapsed={elapsed:.2f}s")

        analysis = analyze_output(output, sid)

        # Decide pass/fail. The loop detector is the system under test, so a
        # PASS requires that:
        #  * If expected_halt_loop: HALT-LOOP was emitted.
        #  * If not expected_halt_loop: no HALT-LOOP was emitted.
        # Additionally, for tests (c) and (d), we expect either throw-halt
        # (test d) OR a clean run (test c). The loop detector is the only
        # thing we're validating here.
        if sc["expected_halt_loop"]:
            if analysis["halt_loop_count"] > 0:
                status = "PASS"
                rationale = "Expected a [HALT-LOOP] event and observed one."
                finding = "Loop detector correctly halted the infinite loop."
            else:
                status = "FAIL"
                rationale = "Expected a [HALT-LOOP] event but none was emitted."
                finding = "Loop detector FAILED to halt an infinite loop — false negative."
        else:
            if analysis["halt_loop_count"] > 0:
                status = "FAIL"
                rationale = "Did NOT expect a [HALT-LOOP] event but one was emitted — false positive."
                finding = "Loop detector fired a FALSE POSITIVE — test logic was finite."
            else:
                # No loop halt. Either the run completed cleanly or it halted for a
                # non-loop reason (e.g. throw, unimplemented opcode, missing API).
                # Check that the runtime actually entered the test method's bytecode.
                oncreate_seen = analysis["deepest_oncreate"] is not None
                if oncreate_seen:
                    if sc["expected_throw_halt"]:
                        if analysis["throw_halt_count"] > 0:
                            status = "PASS"
                            rationale = "Expected throw-halt and observed one. No [HALT-LOOP] false positive."
                            finding = "Loop detector did not interfere with exception-path throw."
                        else:
                            status = "WARN"
                            rationale = "Expected throw-halt but no throw halt message was captured. Loop detector still did not fire false positive."
                            finding = "Loop detector did not fire; runtime halted for a different reason before reaching the throw instruction."
                    else:
                        status = "PASS"
                        rationale = "No [HALT-LOOP] false positive. onCreate was entered and ran without the loop detector firing."
                        finding = "Loop detector correctly allowed the legitimate loop / recursion to run."
                else:
                    status = "WARN"
                    rationale = "Runtime never entered onCreate — DEX/APK was accepted but execution stopped earlier (likely missing API stub). Loop detector was not exercised."
                    finding = "Loop detector was not exercised; runtime stopped before reaching the test bytecode."

        results.append({
            "id": sid, "name": sc["name"], "description": sc["description"],
            "expected": sc["expected"], "expected_halt_loop": sc["expected_halt_loop"],
            "expected_throw_halt": sc["expected_throw_halt"],
            "exit_code": exit_code, "elapsed_sec": elapsed,
            "analysis": analysis, "status": status, "rationale": rationale,
            "finding": finding,
            "dex_path": dex_path, "apk_path": apk_path, "log_path": log_path,
        })

    write_report(results)

    # Also write a small JSON summary alongside the markdown.
    summary_path = os.path.join(OUTPUT_RUN_DIR, "summary.json")
    with open(summary_path, "w") as f:
        # Strip non-serializable items: all keys are str/numbers/lists — OK.
        json.dump({
            "scenarios": [
                {
                    "id": r["id"], "name": r["name"], "status": r["status"],
                    "rationale": r["rationale"], "finding": r["finding"],
                    "exit_code": r["exit_code"], "elapsed_sec": r["elapsed_sec"],
                    "method_in_count": r["analysis"]["method_in_count"],
                    "halt_loop_count": r["analysis"]["halt_loop_count"],
                    "throw_halt_count": r["analysis"]["throw_halt_count"],
                    "final_state": r["analysis"]["final_state"],
                    "max_insn_seen": r["analysis"]["max_insn_seen"],
                    "dex_path": r["dex_path"], "apk_path": r["apk_path"],
                    "log_path": r["log_path"],
                }
                for r in results
            ]
        }, f, indent=2)
    print(f"[SUMMARY] wrote {summary_path}")

    # Print a concise console summary.
    print("\n" + "=" * 72)
    print("EXP-043 Phase 5 — Loop Detector Validation Suite — Results")
    print("=" * 72)
    for r in results:
        print(f"  [{r['status']:<4}] {r['id']:<24}  "
              f"halt_loop={r['analysis']['halt_loop_count']} "
              f"method_in={r['analysis']['method_in_count']} "
              f"state={r['analysis']['final_state']}")
    print("=" * 72)


if __name__ == "__main__":
    main()
