#!/usr/bin/env python3
"""
EXP-043 PHASE 2 — JNI Early Reach Analysis

Determines how many DEX methods execute before the first native (JNI) call
is encountered on Telegram's startup path.

Strategy:
  1. Reuse the DEX parsing logic from `exp042_jni_inventory.py` to enumerate
     every `native` method (access_flags & 0x100 != 0) across all 5 DEX
     files inside the Telegram APK.
  2. For every method that has bytecode (code_off != 0), walk the code_item
     and scan for `invoke-static` instructions targeting:
        - `Ljava/lang/System;.loadLibrary(Ljava/lang/String;)V`
        - `Ljava/lang/Runtime;.loadLibrary0(Ljava/lang/ClassLoader;Ljava/lang/String;)V`
        - `Lorg/telegram/messenger/NativeLoader;.init(...)Z`   (native bootstrap)
     Record call sites and, where possible, the const-string argument.
  3. Parse the runtime execution log
     (`miniandroid/run/exp043_phase1.log`) to extract the ordered list of
     `[METHOD-IN]` events. Compute the **JNI distance** — the index in the
     unique-method-entry list at which a native method itself first entered
     (i.e. when a Java-side invoke-* on a native method succeeded).
  4. Also perform a *static* sweep: for every method that *did* enter the
     execution log, scan its bytecode for `invoke-*` instructions whose
     target is a native method, and report them as "potential native calls
     that would have been reached if execution had completed".
  5. Emit:
        miniandroid/docs/EXP043_JNI_DISTANCE.md
        miniandroid/docs/EXP043_JNI_DISTANCE.json

No third-party dependencies — only `struct`, `zipfile`, `json`, `re`, `os`,
`sys`, `collections`, `typing`.

The DEX binary layout reference is the canonical Android source header
`dalvik/libdex/DexFile.h` (identical to the one used by the EXP-042
phase-5 inventory tool, so the on-disk formats are not re-described here).
"""

from __future__ import annotations

import json
import os
import re
import struct
import sys
import zipfile
from collections import OrderedDict, defaultdict
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = "/home/z/my-project/MiniAndroid-Compatibility-Runtime"
APK_PATH = os.path.join(
    PROJECT_ROOT, "miniandroid/download/exp038_telegram/Telegram.apk"
)
EXEC_LOG_PATH = os.path.join(
    PROJECT_ROOT, "miniandroid/run/exp043_phase1.log"
)
OUT_DIR = os.path.join(PROJECT_ROOT, "miniandroid/docs")
MD_PATH = os.path.join(OUT_DIR, "EXP043_JNI_DISTANCE.md")
JSON_PATH = os.path.join(OUT_DIR, "EXP043_JNI_DISTANCE.json")

DEX_FILES = [
    "classes.dex",
    "classes2.dex",
    "classes3.dex",
    "classes4.dex",
    "classes5.dex",
]

# ---------------------------------------------------------------------------
# Access flags
# ---------------------------------------------------------------------------

ACC_PUBLIC       = 0x1
ACC_PRIVATE      = 0x2
ACC_PROTECTED    = 0x4
ACC_STATIC       = 0x8
ACC_FINAL        = 0x10
ACC_SYNCHRONIZED = 0x20
ACC_NATIVE       = 0x100
ACC_ABSTRACT     = 0x400

# ---------------------------------------------------------------------------
# DEX binary structures (all little-endian)
# ---------------------------------------------------------------------------

HEADER_FMT     = "<8sI20s" + "I" * 20   # 8+4+20+80 = 112 bytes
HEADER_SIZE    = struct.calcsize(HEADER_FMT)
assert HEADER_SIZE == 112, "DexHeader must be 112 bytes"

STRING_ID_FMT  = "<I"             # 4 bytes
TYPE_ID_FMT    = "<I"             # 4 bytes
PROTO_ID_FMT   = "<III"           # 12 bytes
METHOD_ID_FMT  = "<HHI"           # 8 bytes
CLASS_DEF_FMT  = "<IIIIIIII"      # 32 bytes
CODE_ITEM_HDR  = "<HHHHII"       # 16 bytes  (registers, ins, outs, tries,
                                  #             debug_info_off, insns_size)

NO_INDEX = 0xFFFFFFFF

# ---------------------------------------------------------------------------
# Dalvik opcode table  (op, name, num_code_units, format_id)
# Reused verbatim from `miniandroid/tools/exp042_disasm.py`.
# ---------------------------------------------------------------------------

OPS: Dict[int, Tuple[str, int, str]] = {
    0x00: ('nop', 1, '10x'), 0x01: ('move', 1, '12x'), 0x02: ('move/from16', 2, '22x'),
    0x03: ('move/16', 3, '32x'), 0x04: ('move-wide', 1, '12x'), 0x05: ('move-wide/from16', 2, '22x'),
    0x06: ('move-wide/16', 3, '32x'), 0x07: ('move-object', 1, '12x'), 0x08: ('move-object/from16', 2, '22x'),
    0x09: ('move-object/16', 3, '32x'),
    0x0a: ('move-result', 1, '11x'), 0x0b: ('move-result-wide', 1, '11x'),
    0x0c: ('move-result-object', 1, '11x'), 0x0d: ('move-exception', 1, '11x'),
    0x0e: ('return-void', 1, '10x'), 0x0f: ('return', 1, '11x'), 0x10: ('return-wide', 1, '11x'),
    0x11: ('return-object', 1, '11x'),
    0x12: ('const/4', 1, '11n'), 0x13: ('const/16', 2, '21s'), 0x14: ('const', 3, '21i'),
    0x15: ('const/high16', 2, '21h'),
    0x16: ('const-wide/16', 2, '21s'), 0x17: ('const-wide/32', 2, '21i'),
    0x18: ('const-wide', 5, '51i'), 0x19: ('const-wide/high16', 2, '21h'),
    0x1a: ('const-string', 2, '21c'), 0x1b: ('const-string/jumbo', 3, '31c'),
    0x1c: ('const-class', 2, '21c'),
    0x1d: ('monitor-enter', 1, '11x'), 0x1e: ('monitor-exit', 1, '11x'),
    0x1f: ('check-cast', 2, '21c'), 0x20: ('instance-of', 2, '22c'),
    0x21: ('array-length', 1, '12x'), 0x22: ('new-instance', 2, '21c'), 0x23: ('new-array', 2, '22c'),
    0x24: ('filled-new-array', 3, '35c'), 0x25: ('fill-array-data', 3, '31i'), 0x26: ('throw', 1, '11x'),
    0x27: ('goto', 1, '10t'), 0x28: ('goto/16', 2, '20t'), 0x29: ('goto/32', 3, '30t'),
    0x2a: ('packed-switch', 3, '31t'), 0x2b: ('sparse-switch', 3, '31t'),
    0x2c: ('cmpl-float', 2, '23x'), 0x2d: ('cmpg-float', 2, '23x'),
    0x2e: ('cmpl-double', 2, '23x'), 0x2f: ('cmpg-double', 2, '23x'),
    0x30: ('cmp-long', 2, '23x'),
    0x31: ('if-eq', 2, '22t'), 0x32: ('if-ne', 2, '22t'),
    0x33: ('if-lt', 2, '22t'), 0x34: ('if-ge', 2, '22t'),
    0x35: ('if-gt', 2, '22t'), 0x36: ('if-le', 2, '22t'),
    0x37: ('if-eqz', 2, '21t'), 0x38: ('if-nez', 2, '21t'),
    0x39: ('if-ltz', 2, '21t'), 0x3a: ('if-gez', 2, '21t'),
    0x3b: ('if-gtz', 2, '21t'), 0x3c: ('if-lez', 2, '21t'),
    0x44: ('aget', 2, '23x'), 0x45: ('aget-wide', 2, '23x'), 0x46: ('aget-object', 2, '23x'),
    0x47: ('aget-boolean', 2, '23x'), 0x48: ('aget-byte', 2, '23x'),
    0x49: ('aget-char', 2, '23x'), 0x4a: ('aget-short', 2, '23x'),
    0x4b: ('aput', 2, '23x'), 0x4c: ('aput-wide', 2, '23x'), 0x4d: ('aput-object', 2, '23x'),
    0x4e: ('aput-boolean', 2, '23x'), 0x4f: ('aput-byte', 2, '23x'),
    0x50: ('aput-char', 2, '23x'), 0x51: ('aput-short', 2, '23x'),
    0x52: ('iget', 2, '22c'), 0x53: ('iget-wide', 2, '22c'), 0x54: ('iget-object', 2, '22c'),
    0x55: ('iget-boolean', 2, '22c'), 0x56: ('iget-byte', 2, '22c'),
    0x57: ('iget-char', 2, '22c'), 0x58: ('iget-short', 2, '22c'),
    0x59: ('iput', 2, '22c'), 0x5a: ('iput-wide', 2, '22c'), 0x5b: ('iput-object', 2, '22c'),
    0x5c: ('iput-boolean', 2, '22c'), 0x5d: ('iput-byte', 2, '22c'),
    0x5e: ('iput-char', 2, '22c'), 0x5f: ('iput-short', 2, '22c'),
    0x60: ('sget', 2, '21c'), 0x61: ('sget-wide', 2, '21c'), 0x62: ('sget-object', 2, '21c'),
    0x63: ('sget-boolean', 2, '21c'), 0x64: ('sget-byte', 2, '21c'),
    0x65: ('sget-char', 2, '21c'), 0x66: ('sget-short', 2, '21c'),
    0x67: ('sput', 2, '21c'), 0x68: ('sput-wide', 2, '21c'), 0x69: ('sput-object', 2, '21c'),
    0x6a: ('sput-boolean', 2, '21c'), 0x6b: ('sput-byte', 2, '21c'),
    0x6c: ('sput-char', 2, '21c'), 0x6d: ('sput-short', 2, '21c'),
    0x6e: ('invoke-virtual', 3, '35c'), 0x6f: ('invoke-super', 3, '35c'),
    0x70: ('invoke-direct', 3, '35c'), 0x71: ('invoke-static', 3, '35c'),
    0x72: ('invoke-interface', 3, '35c'),
    0x74: ('invoke-virtual/range', 3, '3rc'), 0x75: ('invoke-super/range', 3, '3rc'),
    0x76: ('invoke-direct/range', 3, '3rc'), 0x77: ('invoke-static/range', 3, '3rc'),
    0x78: ('invoke-interface/range', 3, '3rc'),
    # 0x79 invoke-polymorphic/range not in OPS table of disasm.py — add safe default
    0x7b: ('neg-int', 1, '12x'), 0x7c: ('not-int', 1, '12x'),
    0x7d: ('neg-long', 1, '12x'), 0x7e: ('not-long', 1, '12x'),
    0x7f: ('neg-float', 1, '12x'), 0x80: ('neg-double', 1, '12x'),
    0x81: ('int-to-long', 1, '12x'), 0x82: ('int-to-float', 1, '12x'), 0x83: ('int-to-double', 1, '12x'),
    0x84: ('long-to-int', 1, '12x'), 0x85: ('long-to-float', 1, '12x'), 0x86: ('long-to-double', 1, '12x'),
    0x87: ('float-to-int', 1, '12x'), 0x88: ('float-to-long', 1, '12x'), 0x89: ('float-to-double', 1, '12x'),
    0x8a: ('double-to-int', 1, '12x'), 0x8b: ('double-to-long', 1, '12x'), 0x8c: ('double-to-float', 1, '12x'),
    0x8d: ('int-to-byte', 1, '12x'), 0x8e: ('int-to-char', 1, '12x'), 0x8f: ('int-to-short', 1, '12x'),
    0x90: ('add-int', 2, '23x'), 0x91: ('sub-int', 2, '23x'), 0x92: ('mul-int', 2, '23x'),
    0x93: ('div-int', 2, '23x'), 0x94: ('rem-int', 2, '23x'),
    0x95: ('and-int', 2, '23x'), 0x96: ('or-int', 2, '23x'), 0x97: ('xor-int', 2, '23x'),
    0x98: ('shl-int', 2, '23x'), 0x99: ('shr-int', 2, '23x'), 0x9a: ('ushr-int', 2, '23x'),
    0x9b: ('add-long', 2, '23x'), 0x9c: ('sub-long', 2, '23x'), 0x9d: ('mul-long', 2, '23x'),
    0x9e: ('div-long', 2, '23x'), 0x9f: ('rem-long', 2, '23x'),
    0xa0: ('and-long', 2, '23x'), 0xa1: ('or-long', 2, '23x'), 0xa2: ('xor-long', 2, '23x'),
    0xa3: ('shl-long', 2, '23x'), 0xa4: ('shr-long', 2, '23x'), 0xa5: ('ushr-long', 2, '23x'),
    0xa6: ('add-float', 2, '23x'), 0xa7: ('sub-float', 2, '23x'), 0xa8: ('mul-float', 2, '23x'),
    0xa9: ('div-float', 2, '23x'), 0xaa: ('rem-float', 2, '23x'),
    0xab: ('add-double', 2, '23x'), 0xac: ('sub-double', 2, '23x'), 0xad: ('mul-double', 2, '23x'),
    0xae: ('div-double', 2, '23x'), 0xaf: ('rem-double', 2, '23x'),
    0xb0: ('add-int/2addr', 1, '12x'), 0xb1: ('sub-int/2addr', 1, '12x'),
    0xb2: ('mul-int/2addr', 1, '12x'), 0xb3: ('div-int/2addr', 1, '12x'),
    0xb4: ('rem-int/2addr', 1, '12x'), 0xb5: ('and-int/2addr', 1, '12x'),
    0xb6: ('or-int/2addr', 1, '12x'), 0xb7: ('xor-int/2addr', 1, '12x'),
    0xb8: ('shl-int/2addr', 1, '12x'), 0xb9: ('shr-int/2addr', 1, '12x'),
    0xba: ('ushr-int/2addr', 1, '12x'),
    0xbb: ('add-long/2addr', 1, '12x'), 0xbc: ('sub-long/2addr', 1, '12x'),
    0xbd: ('mul-long/2addr', 1, '12x'), 0xbe: ('div-long/2addr', 1, '12x'),
    0xbf: ('rem-long/2addr', 1, '12x'), 0xc0: ('and-long/2addr', 1, '12x'),
    0xc1: ('or-long/2addr', 1, '12x'), 0xc2: ('xor-long/2addr', 1, '12x'),
    0xc3: ('shl-long/2addr', 1, '12x'), 0xc4: ('shr-long/2addr', 1, '12x'),
    0xc5: ('ushr-long/2addr', 1, '12x'),
    0xc6: ('add-float/2addr', 1, '12x'), 0xc7: ('sub-float/2addr', 1, '12x'),
    0xc8: ('mul-float/2addr', 1, '12x'), 0xc9: ('div-float/2addr', 1, '12x'),
    0xca: ('rem-float/2addr', 1, '12x'),
    0xcb: ('add-double/2addr', 1, '12x'), 0xcc: ('sub-double/2addr', 1, '12x'),
    0xcd: ('mul-double/2addr', 1, '12x'), 0xce: ('div-double/2addr', 1, '12x'),
    0xcf: ('rem-double/2addr', 1, '12x'),
    0xd0: ('add-int/lit16', 2, '22s'), 0xd1: ('rsub-int', 2, '22s'),
    0xd2: ('mul-int/lit16', 2, '22s'), 0xd3: ('div-int/lit16', 2, '22s'),
    0xd4: ('rem-int/lit16', 2, '22s'), 0xd5: ('and-int/lit16', 2, '22s'),
    0xd6: ('or-int/lit16', 2, '22s'), 0xd7: ('xor-int/lit16', 2, '22s'),
    0xd8: ('add-int/lit8', 2, '22b'), 0xd9: ('rsub-int/lit8', 2, '22b'),
    0xda: ('mul-int/lit8', 2, '22b'), 0xdb: ('and-int/lit8', 2, '22b'),
    0xdc: ('or-int/lit8', 2, '22b'), 0xdd: ('xor-int/lit8', 2, '22b'),
    0xde: ('shl-int/lit8', 2, '22b'), 0xdf: ('shr-int/lit8', 2, '22b'),
    0xe0: ('ushr-int/lit8', 2, '22b'),
}

# Set of invoke-* opcode bytes that need to be inspected for native targets.
INVOKE_OPS = {0x6e, 0x6f, 0x70, 0x71, 0x72, 0x74, 0x75, 0x76, 0x77, 0x78}

# ---------------------------------------------------------------------------
# Low-level binary helpers
# ---------------------------------------------------------------------------

def read_uleb128(data: bytes, offset: int) -> Tuple[int, int]:
    """Read an unsigned LEB128 integer; return (value, new_offset)."""
    result = 0
    shift = 0
    while True:
        if offset >= len(data):
            break
        b = data[offset]
        offset += 1
        result |= (b & 0x7F) << shift
        if (b & 0x80) == 0:
            break
        shift += 7
    return result, offset


def read_mutf8_string(data: bytes, offset: int) -> Tuple[str, int]:
    """Read a string_data_item (uleb128 utf16 length + MUTF-8 bytes + NUL)."""
    _utf16_len, offset = read_uleb128(data, offset)
    end = offset
    while end < len(data) and data[end] != 0:
        end += 1
    raw = data[offset:end]
    try:
        s = raw.decode("utf-8", errors="replace")
    except Exception:
        s = "<decode-error>"
    return s, end + 1


# ---------------------------------------------------------------------------
# Per-DEX parsing
# ---------------------------------------------------------------------------

class DexFile:
    """Minimal lazy DEX reader. Holds the raw bytes and parses only the
    sections needed for native-method and call-site scanning."""

    def __init__(self, name: str, data: bytes):
        self.name = name
        self.data = data
        if len(data) < HEADER_SIZE:
            raise ValueError(f"{name}: truncated DEX (< {HEADER_SIZE} bytes)")
        h = struct.unpack(HEADER_FMT, data[:HEADER_SIZE])
        (
            self.magic, self.checksum, self.signature,
            self.file_size, self.header_size, self.endian_tag,
            self.link_size, self.link_off, self.map_off,
            self.string_ids_size, self.string_ids_off,
            self.type_ids_size, self.type_ids_off,
            self.proto_ids_size, self.proto_ids_off,
            self.field_ids_size, self.field_ids_off,
            self.method_ids_size, self.method_ids_off,
            self.class_defs_size, self.class_defs_off,
            self.data_size, self.data_off,
        ) = h
        self._strings = self._parse_string_ids()
        self._types = self._parse_type_ids()
        self._protos = self._parse_proto_ids()
        self._methods = self._parse_method_ids()

    # ----- section readers --------------------------------------------------

    def _parse_string_ids(self) -> List[str]:
        if self.string_ids_size == 0:
            return []
        raw = self.data[
            self.string_ids_off:
            self.string_ids_off + self.string_ids_size * 4
        ]
        offs = struct.unpack(f"<{self.string_ids_size}I", raw)
        out: List[str] = []
        for off in offs:
            if off == 0 or off >= len(self.data):
                out.append("<bad-string-off>")
                continue
            s, _ = read_mutf8_string(self.data, off)
            out.append(s)
        return out

    def _parse_type_ids(self) -> List[str]:
        if self.type_ids_size == 0:
            return []
        raw = self.data[
            self.type_ids_off:
            self.type_ids_off + self.type_ids_size * 4
        ]
        desc_idxs = struct.unpack(f"<{self.type_ids_size}I", raw)
        return [
            self._strings[i] if 0 <= i < len(self._strings) else "<bad-type-idx>"
            for i in desc_idxs
        ]

    def _parse_proto_ids(self) -> List[Tuple[int, int, int]]:
        if self.proto_ids_size == 0:
            return []
        raw = self.data[
            self.proto_ids_off:
            self.proto_ids_off + self.proto_ids_size * 12
        ]
        flat = struct.unpack(f"<{self.proto_ids_size * 3}I", raw)
        return [
            (flat[i], flat[i + 1], flat[i + 2])
            for i in range(0, len(flat), 3)
        ]

    def _parse_method_ids(self) -> List[Tuple[int, int, int]]:
        if self.method_ids_size == 0:
            return []
        raw = self.data[
            self.method_ids_off:
            self.method_ids_off + self.method_ids_size * 8
        ]
        out: List[Tuple[int, int, int]] = []
        for i in range(self.method_ids_size):
            chunk = raw[i * 8:(i + 1) * 8]
            class_idx, proto_idx, name_idx = struct.unpack(METHOD_ID_FMT, chunk)
            out.append((class_idx, proto_idx, name_idx))
        return out

    # ----- accessors --------------------------------------------------------

    def get_string(self, idx: int) -> str:
        if 0 <= idx < len(self._strings):
            return self._strings[idx]
        return f"<bad-string-idx:{idx}>"

    def get_type(self, idx: int) -> str:
        if 0 <= idx < len(self._types):
            return self._types[idx]
        return f"<bad-type-idx:{idx}>"

    def get_method_class(self, method_idx: int) -> str:
        if not (0 <= method_idx < len(self._methods)):
            return f"<bad-method-idx:{method_idx}>"
        class_idx = self._methods[method_idx][0]
        return self.get_type(class_idx)

    def get_method_name(self, method_idx: int) -> str:
        if not (0 <= method_idx < len(self._methods)):
            return f"<bad-method-idx:{method_idx}>"
        name_idx = self._methods[method_idx][2]
        return self.get_string(name_idx)

    def get_method_shorty(self, method_idx: int) -> str:
        if not (0 <= method_idx < len(self._methods)):
            return "<bad-method-idx>"
        proto_idx = self._methods[method_idx][1]
        if not (0 <= proto_idx < len(self._protos)):
            return "<bad-proto-idx>"
        shorty_idx = self._protos[proto_idx][0]
        return self.get_string(shorty_idx)

    def get_method_descriptor(self, method_idx: int) -> str:
        """Return '<class>;<method>' (no prototype) — same format used by
        the runtime execution log's [METHOD-IN] lines."""
        return f"{self.get_method_class(method_idx)};.{self.get_method_name(method_idx)}"

    # ----- class iteration --------------------------------------------------

    def iter_classes(self):
        """Yield (class_descriptor, class_access_flags, class_data_off)."""
        if self.class_defs_size == 0:
            return
        for i in range(self.class_defs_size):
            base = self.class_defs_off + i * 32
            chunk = self.data[base:base + 32]
            if len(chunk) < 32:
                break
            (
                class_idx, access_flags, _superclass_idx, _interfaces_off,
                _source_file_idx, _annotations_off, class_data_off,
                _static_values_off,
            ) = struct.unpack(CLASS_DEF_FMT, chunk)
            descriptor = (
                self._types[class_idx]
                if 0 <= class_idx < len(self._types)
                else f"<bad-class-idx:{class_idx}>"
            )
            yield descriptor, access_flags, class_data_off

    def iter_all_methods(self):
        """Yield every method declared in this DEX.

        Returns tuples:
            (class_descriptor, class_access_flags, method_name,
             method_shorty, method_idx, access_flags, code_off,
             method_kind)
        where method_kind is 'direct' or 'virtual'.
        For abstract / native methods, code_off may be 0.
        """
        for descriptor, class_access, class_data_off in self.iter_classes():
            if class_data_off == 0:
                continue
            yield from self._iter_methods_in_class(descriptor, class_access,
                                                    class_data_off)

    def _iter_methods_in_class(self, descriptor, class_access, class_data_off):
        data = self.data
        off = class_data_off
        static_fields_size, off   = read_uleb128(data, off)
        instance_fields_size, off = read_uleb128(data, off)
        direct_methods_size, off  = read_uleb128(data, off)
        virtual_methods_size, off = read_uleb128(data, off)

        for _ in range(static_fields_size + instance_fields_size):
            _fidx, off = read_uleb128(data, off)
            _aflg, off = read_uleb128(data, off)

        for size_label, size in (
            ("direct",  direct_methods_size),
            ("virtual", virtual_methods_size),
        ):
            prev_idx = 0
            for _ in range(size):
                idx_diff, off   = read_uleb128(data, off)
                access_flags, off = read_uleb128(data, off)
                code_off, off   = read_uleb128(data, off)
                method_idx = prev_idx + idx_diff
                prev_idx = method_idx
                yield (
                    descriptor,
                    class_access,
                    self.get_method_name(method_idx),
                    self.get_method_shorty(method_idx),
                    method_idx,
                    access_flags,
                    code_off,
                    size_label,
                )


# ---------------------------------------------------------------------------
# Bytecode scanner
# ---------------------------------------------------------------------------

def read_code_item_header(data: bytes, code_off: int):
    """Returns (registers_size, ins_size, outs_size, tries_size,
    debug_info_off, insns_size) or None if code_off == 0."""
    if code_off == 0 or code_off + 16 > len(data):
        return None
    return struct.unpack(CODE_ITEM_HDR, data[code_off:code_off + 16])


def scan_invoke_sites(
    dex: DexFile,
    code_off: int,
    target_method_idxs: set,
) -> List[Dict]:
    """Walk the code_item at `code_off` linearly. For every invoke-*
    instruction whose method_idx is in `target_method_idxs`, append a dict:
        {
          'pc': int,
          'opcode': 0x71,
          'opcode_name': 'invoke-static',
          'method_idx': int,
          'target_class': str,
          'target_name': str,
          'target_shorty': str,
          'argc': int,
          'arg_regs': [int, ...],
        }
    Returns the list in PC order.
    """
    hdr = read_code_item_header(dex.data, code_off)
    if hdr is None:
        return []
    _, _, _, _, _, insns_size = hdr
    if insns_size == 0:
        return []
    insns_off = code_off + 16
    # insns_size is in 16-bit code units.
    raw = dex.data[insns_off:insns_off + insns_size * 2]
    # Pre-unpack as a flat u16 array for fast indexing.
    if len(raw) < insns_size * 2:
        return []
    units = struct.unpack(f"<{insns_size}H", raw)
    out: List[Dict] = []
    pc = 0
    while pc < insns_size:
        op_word = units[pc]
        op = op_word & 0xFF
        high = (op_word >> 8) & 0xFF
        info = OPS.get(op)
        if info is None:
            # Unknown opcode (could be a payload header for
            # fill-array-data / packed-switch / sparse-switch). Bail
            # forward by 1 unit to be safe; we will not decode the rest
            # correctly but we will at least not crash.  In practice the
            # Telegram DEX files only contain opcodes we know.
            pc += 1
            continue
        _name, units_n, fmt = info
        if op in INVOKE_OPS:
            # All invoke-* ops have the method_idx in the next code unit
            # (the second 16-bit word). The 3rd unit is the register list
            # (35c) or the count (3rc).
            if pc + 1 < insns_size:
                method_idx = units[pc + 1]
                if method_idx in target_method_idxs:
                    argc = (high >> 4) & 0xF
                    if fmt == '35c':
                        if pc + 2 < insns_size:
                            regs_word = units[pc + 2]
                            arg_regs = [
                                regs_word & 0xF,
                                (regs_word >> 4) & 0xF,
                                (regs_word >> 8) & 0xF,
                                (regs_word >> 12) & 0xF,
                                high & 0xF,
                            ][:argc]
                        else:
                            arg_regs = []
                    elif fmt == '3rc':
                        # 3rc: range form, count = high, first reg in next unit
                        argc = high
                        if pc + 2 < insns_size:
                            first = units[pc + 2]
                            arg_regs = list(range(first, first + argc))
                        else:
                            arg_regs = []
                    else:
                        arg_regs = []
                    out.append({
                        'pc': pc,
                        'opcode': op,
                        'opcode_name': _name,
                        'method_idx': method_idx,
                        'target_class': dex.get_method_class(method_idx),
                        'target_name': dex.get_method_name(method_idx),
                        'target_shorty': dex.get_method_shorty(method_idx),
                        'argc': argc,
                        'arg_regs': arg_regs,
                    })
        # Skip any payload data block: if we hit a fill-array-data /
        # packed-switch / sparse-switch pseudo-instruction, the payload
        # that follows is variable length. Those opcodes (0x26 throw,
        # 0x2a packed-switch, 0x2b sparse-switch, 0x25 fill-array-data)
        # are handled here.
        if op == 0x00 and high == 0x01 and pc + 1 < insns_size:
            # Pseudo-op: packed-switch payload (format: 0x0100 + size + ...)
            # size = units[pc+1]
            sz = units[pc + 1]
            # payload = 1 (ident) + 1 (size) + 1 (first_key) + sz*2 (targets)
            pc += 3 + sz * 2
            continue
        if op == 0x00 and high == 0x02 and pc + 1 < insns_size:
            # Pseudo-op: sparse-switch payload (0x0200 + size + sz*2 keys + sz*2 targets)
            sz = units[pc + 1]
            pc += 2 + sz * 4
            continue
        if op == 0x00 and high == 0x03 and pc + 1 < insns_size:
            # Pseudo-op: fill-array-data payload (0x0300 + size + element_width + data)
            sz = units[pc + 1]
            ew = units[pc + 2] if pc + 2 < insns_size else 0
            data_units = (sz * ew + 1) // 2
            pc += 3 + data_units
            continue
        pc += units_n
    return out


def find_recent_const_string(
    dex: DexFile,
    code_off: int,
    target_register: int,
    before_pc: Optional[int] = None,
) -> Optional[str]:
    """Walk the code_item at `code_off` linearly, recording every
    const-string write to `target_register`. If `before_pc` is None,
    returns the *last* write in the whole method (a coarse fallback).
    Otherwise returns the most-recent write *before* that PC.

    The proper backward analysis is essential because real methods often
    contain multiple `System.loadLibrary(...)` calls for different
    libraries.
    """
    hdr = read_code_item_header(dex.data, code_off)
    if hdr is None:
        return None
    _, _, _, _, _, insns_size = hdr
    if insns_size == 0:
        return None
    insns_off = code_off + 16
    raw = dex.data[insns_off:insns_off + insns_size * 2]
    if len(raw) < insns_size * 2:
        return None
    units = struct.unpack(f"<{insns_size}H", raw)
    end_pc = insns_size if before_pc is None else before_pc
    last_value: Optional[str] = None
    pc = 0
    while pc < end_pc:
        op_word = units[pc]
        op = op_word & 0xFF
        high = (op_word >> 8) & 0xFF
        info = OPS.get(op)
        if info is None:
            pc += 1
            continue
        _name, units_n, fmt = info
        # Will this instruction overshoot end_pc?  If yes, stop scanning.
        if pc + units_n > end_pc:
            break
        if op == 0x1a and (high & 0xFF) == target_register:
            if pc + 1 < insns_size:
                str_idx = units[pc + 1]
                last_value = dex.get_string(str_idx)
        elif op == 0x1b and (high & 0xFF) == target_register:
            if pc + 2 < insns_size:
                str_idx = units[pc + 1] | (units[pc + 2] << 16)
                last_value = dex.get_string(str_idx)
        # Skip payload data blocks identically to scan_invoke_sites
        if op == 0x00 and high == 0x01 and pc + 1 < insns_size:
            sz = units[pc + 1]
            if pc + 3 + sz * 2 > end_pc:
                break
            pc += 3 + sz * 2; continue
        if op == 0x00 and high == 0x02 and pc + 1 < insns_size:
            sz = units[pc + 1]
            if pc + 2 + sz * 4 > end_pc:
                break
            pc += 2 + sz * 4; continue
        if op == 0x00 and high == 0x03 and pc + 1 < insns_size:
            sz = units[pc + 1]
            ew = units[pc + 2] if pc + 2 < insns_size else 0
            data_units = (sz * ew + 1) // 2
            if pc + 3 + data_units > end_pc:
                break
            pc += 3 + data_units; continue
        pc += units_n
    return last_value


# ---------------------------------------------------------------------------
# Library / priority guessing (carried over from exp042_jni_inventory.py)
# ---------------------------------------------------------------------------

def guess_library(class_desc: str) -> str:
    if "TgNet" in class_desc or "tgnet" in class_desc:
        return "libtmessages.49.so (tgnet module)"
    if "RLottie" in class_desc or "Lottie" in class_desc:
        return "libtmessages.49.so (rlottie module)"
    if "BotWebView" in class_desc or "WebView" in class_desc:
        return "libtmessages.49.so (botwebview module)"
    if "Secret" in class_desc:
        return "libtmessages.49.so (secret module)"
    if "Utilities" in class_desc:
        return "libtmessages.49.so (utilities module)"
    if "FileLog" in class_desc:
        return "libtmessages.49.so (filelog module)"
    if "NativeLoader" in class_desc:
        return "libtmessages.49.so (loader bootstrap)"
    if "MessagesController" in class_desc:
        return "libtmessages.49.so (controller module)"
    return "libtmessages.49.so"


P0_CLASSES = (
    "ApplicationLoader", "LaunchActivity", "NativeLoader", "FileLog",
    "AndroidUtilities", "UserConfig", "SharedConfig", "NotificationCenter",
    "MessagesController", "MessagesStorage", "Theme",
)

P1_CLASSES = (
    "TgNet", "tgnet", "ConnectionsManager", "TLObject", "TLRPC", "RPCRequest",
    "SecretChat", "SecretStats", "Utilities", "FileLoader", "FileUploadOperation",
    "FileDownloadOperation", "SendMessagesHelper", "AudioRecoder", "AudioPlayer",
    "VideoPlayer", "GpuIntegration",
)


def guess_priority(class_desc: str) -> str:
    for needle in P0_CLASSES:
        if needle in class_desc:
            return "P0"
    for needle in P1_CLASSES:
        if needle in class_desc:
            return "P1"
    return "P2"


# ---------------------------------------------------------------------------
# Execution log parsing
# ---------------------------------------------------------------------------

METHOD_IN_RE = re.compile(
    r"\[METHOD-IN\]\s+(\S+?)\s+\(bytecode_size=(\d+)\)"
)
METHOD_EXIT_RE = re.compile(
    r"\[MEM\]\s+method_exit:\s+(\S+?)\s+insns=(\d+)\s+RSS="
)
HALT_RE = re.compile(
    r"\[HALT-([A-Z]+)\]\s+(.*)"
)


def parse_execution_log(log_path: str) -> Dict:
    """Parse `exp043_phase1.log` into a structured view.

    Returns a dict with:
      - 'method_in_order'   : list of (method_descriptor, bytecode_size) tuples
                              in the order they appear in the log (with repeats).
      - 'unique_methods'    : list of dicts, deduped by descriptor, with
                              'first_seen_index' and 'enter_count'.
      - 'method_exits'      : list of (method_descriptor, insn_count) tuples.
      - 'halts'              : list of dicts (kind, raw_message).
    """
    if not os.path.exists(log_path):
        return {
            'log_path': log_path,
            'log_exists': False,
            'method_in_order': [],
            'unique_methods': [],
            'method_exits': [],
            'halts': [],
        }
    method_in_order: List[Tuple[str, int]] = []
    method_exits: List[Tuple[str, int]] = []
    halts: List[Dict] = []
    with open(log_path, 'r', errors='replace') as fh:
        for line in fh:
            m = METHOD_IN_RE.search(line)
            if m:
                desc = m.group(1)
                bcsz = int(m.group(2))
                method_in_order.append((desc, bcsz))
                continue
            m = METHOD_EXIT_RE.search(line)
            if m:
                desc = m.group(1)
                insn = int(m.group(2))
                method_exits.append((desc, insn))
                continue
            m = HALT_RE.search(line)
            if m:
                halts.append({
                    'kind': m.group(1),
                    'message': m.group(2).strip(),
                })
    # Dedupe method entries by descriptor.
    seen: Dict[str, Dict] = {}
    for idx, (desc, bcsz) in enumerate(method_in_order):
        if desc not in seen:
            seen[desc] = {
                'method': desc,
                'first_seen_index': idx,
                'enter_count': 1,
                'bytecode_size': bcsz,
            }
        else:
            seen[desc]['enter_count'] += 1
    unique_methods = sorted(seen.values(), key=lambda d: d['first_seen_index'])
    return {
        'log_path': log_path,
        'log_exists': True,
        'method_in_order': method_in_order,
        'unique_methods': unique_methods,
        'method_exits': method_exits,
        'halts': halts,
    }


# ---------------------------------------------------------------------------
# Driver: scan the APK
# ---------------------------------------------------------------------------

def scan_apk(apk_path: str) -> Dict:
    """Scan every DEX file. Returns the structured inventory."""
    native_methods: List[Dict] = []
    load_library_sites: List[Dict] = []
    native_loader_init_sites: List[Dict] = []
    dex_stats: Dict[str, Dict] = OrderedDict()
    all_method_index: Dict[str, Dict] = {}  # 'class;method' -> {dex, method_idx}
    # Keyed by descriptor 'Lfoo/Bar;->baz(I)V' to native method records
    native_method_lookup: Dict[str, Dict] = {}

    # Per-DEX: build a fast lookup of (class, name) -> method_idx and
    # accumulate native-method descriptors so we can also detect native
    # call sites by descriptor rather than just by name match.
    per_dex_method_lookup: Dict[str, Dict[Tuple[str, str], int]] = {}
    per_dex_native_set: Dict[str, set] = {}

    with zipfile.ZipFile(apk_path, "r") as z:
        available = set(z.namelist())
        for dex_name in DEX_FILES:
            if dex_name not in available:
                print(f"  [WARN] {dex_name} not in APK, skipping", file=sys.stderr)
                continue
            raw = z.read(dex_name)
            dex = DexFile(dex_name, raw)
            classes_in_dex = dex.class_defs_size
            dex_methods = dex.method_ids_size
            dex_strings = dex.string_ids_size
            dex_types = dex.type_ids_size
            dex_protos = dex.proto_ids_size
            dex_fields = dex.field_ids_size
            native_count = 0
            classes_with_native = set()
            method_lookup: Dict[Tuple[str, str], int] = {}
            native_method_idxs: set = set()

            # 1st pass: walk all methods, collect native ones, build
            # (class, name) -> method_idx index.
            for (
                descriptor, class_access, method_name, shorty,
                method_idx, access_flags, code_off, method_kind
            ) in dex.iter_all_methods():
                method_lookup[(descriptor, method_name)] = method_idx
                if (access_flags & ACC_NATIVE) != 0:
                    native_count += 1
                    classes_with_native.add(descriptor)
                    rec = {
                        'class': descriptor,
                        'method': method_name,
                        'shorty': shorty,
                        'library': guess_library(descriptor),
                        'dex': dex_name,
                        'priority': guess_priority(descriptor),
                        'class_access_flags': class_access,
                        'access_flags': access_flags,
                        'method_idx': method_idx,
                        'method_kind': method_kind,
                        'code_off': code_off,
                        'on_execution_path': False,  # filled later
                    }
                    native_methods.append(rec)
                    native_method_lookup[
                        f"{descriptor}.{method_name}"
                    ] = rec
                    native_method_idxs.add(method_idx)
            per_dex_method_lookup[dex_name] = method_lookup
            per_dex_native_set[dex_name] = native_method_idxs

            dex_stats[dex_name] = {
                'file_size_bytes': len(raw),
                'classes': classes_in_dex,
                'strings': dex_strings,
                'types': dex_types,
                'protos': dex_protos,
                'fields': dex_fields,
                'methods': dex_methods,
                'native_methods': native_count,
                'classes_with_native': len(classes_with_native),
            }
            print(
                f"  [OK] {dex_name}: {classes_in_dex} classes, "
                f"{dex_methods} methods, {native_count} native methods "
                f"across {len(classes_with_native)} classes",
                file=sys.stderr,
            )

    # 2nd pass over each DEX: find System.loadLibrary / NativeLoader.init
    # call sites by scanning the bytecode of every method that has code.
    # Pre-compute the target method_idx sets.
    loadlib_target_idxs: Dict[str, set] = {}  # dex_name -> set of method_idx
    nativeloader_target_idxs: Dict[str, set] = {}
    native_target_idxs: Dict[str, set] = {}   # method_idx of every native method, per-DEX

    with zipfile.ZipFile(apk_path, "r") as z:
        for dex_name in DEX_FILES:
            if dex_name not in z.namelist():
                continue
            raw = z.read(dex_name)
            dex = DexFile(dex_name, raw)
            loadlib_idxs: set = set()
            nativeloader_idxs: set = set()
            for mi in range(len(dex._methods)):
                cls = dex.get_method_class(mi)
                name = dex.get_method_name(mi)
                if cls == "Ljava/lang/System;" and name == "loadLibrary":
                    loadlib_idxs.add(mi)
                elif cls == "Ljava/lang/Runtime;" and name == "loadLibrary0":
                    loadlib_idxs.add(mi)
                elif cls == "Ljava/lang/System;" and name == "load":
                    loadlib_idxs.add(mi)
                elif cls == "Lorg/telegram/messenger/NativeLoader;" and name == "init":
                    nativeloader_idxs.add(mi)
            loadlib_target_idxs[dex_name] = loadlib_idxs
            nativeloader_target_idxs[dex_name] = nativeloader_idxs
            native_target_idxs[dex_name] = per_dex_native_set[dex_name]
            print(
                f"  [IDX] {dex_name}: loadLibrary targets={len(loadlib_idxs)}, "
                f"NativeLoader.init targets={len(nativeloader_idxs)}, "
                f"native method targets={len(per_dex_native_set[dex_name])}",
                file=sys.stderr,
            )

        # 3rd pass: walk every method with bytecode, scan for invoke-*
        # to those target sets.
        for dex_name in DEX_FILES:
            if dex_name not in z.namelist():
                continue
            raw = z.read(dex_name)
            dex = DexFile(dex_name, raw)
            loadlib_idxs = loadlib_target_idxs[dex_name]
            nativeloader_idxs = nativeloader_target_idxs[dex_name]
            native_idxs = native_target_idxs[dex_name]
            for (
                descriptor, class_access, method_name, shorty,
                method_idx, access_flags, code_off, method_kind
            ) in dex.iter_all_methods():
                if code_off == 0:
                    continue
                # Skip methods that are themselves native.
                if (access_flags & ACC_NATIVE) != 0:
                    continue
                # Scan for invoke-static to loadLibrary / NativeLoader.init.
                if loadlib_idxs or nativeloader_idxs:
                    targets = loadlib_idxs | nativeloader_idxs
                    sites = scan_invoke_sites(dex, code_off, targets)
                    for s in sites:
                        if s['method_idx'] in loadlib_idxs:
                            # Try to find the const-string argument by
                            # scanning backwards from this PC.
                            string_arg = None
                            if s['arg_regs']:
                                string_arg = find_recent_const_string(
                                    dex, code_off, s['arg_regs'][0],
                                    before_pc=s['pc'],
                                )
                            load_library_sites.append({
                                'calling_class': descriptor,
                                'calling_method': method_name,
                                'calling_method_kind': method_kind,
                                'calling_dex': dex_name,
                                'calling_method_idx': method_idx,
                                'library_name': string_arg or "<unknown>",
                                'target_class': s['target_class'],
                                'target_method': s['target_name'],
                                'target_shorty': s['target_shorty'],
                                'pc': s['pc'],
                                'opcode': s['opcode_name'],
                                'on_execution_path': False,  # filled later
                            })
                        if s['method_idx'] in nativeloader_idxs:
                            native_loader_init_sites.append({
                                'calling_class': descriptor,
                                'calling_method': method_name,
                                'calling_method_kind': method_kind,
                                'calling_dex': dex_name,
                                'calling_method_idx': method_idx,
                                'target_class': s['target_class'],
                                'target_method': s['target_name'],
                                'target_shorty': s['target_shorty'],
                                'pc': s['pc'],
                                'opcode': s['opcode_name'],
                                'on_execution_path': False,
                            })

    return {
        'apk': apk_path,
        'dex_stats': dex_stats,
        'native_methods': native_methods,
        'native_method_lookup': native_method_lookup,
        'load_library_sites': load_library_sites,
        'native_loader_init_sites': native_loader_init_sites,
        'total_native_methods': len(native_methods),
        'total_load_library_sites': len(load_library_sites),
        'total_native_loader_init_sites': len(native_loader_init_sites),
    }


# ---------------------------------------------------------------------------
# Cross-reference: mark items that appear on the execution path
# ---------------------------------------------------------------------------

def cross_reference_with_log(scan: Dict, log_view: Dict) -> Dict:
    """Annotate native methods, loadLibrary call sites, and
    NativeLoader.init call sites with `on_execution_path` flags."""
    if not log_view.get('log_exists'):
        return {
            'executed_methods_set': set(),
            'first_native_method': None,
            'jni_distance': "not reached yet (no execution log)",
            'native_call_sites_on_path': [],
            'static_call_chain': [],
        }
    unique_methods = log_view['unique_methods']
    executed_descs = {m['method'] for m in unique_methods}
    executed_set_with_index = [
        (m['method'], m['first_seen_index']) for m in unique_methods
    ]

    # Mark native methods
    for nm in scan['native_methods']:
        key = f"{nm['class']}.{nm['method']}"
        if key in executed_descs:
            nm['on_execution_path'] = True

    # Mark loadLibrary call sites
    for site in scan['load_library_sites']:
        key = f"{site['calling_class']}.{site['calling_method']}"
        if key in executed_descs:
            site['on_execution_path'] = True

    # Mark NativeLoader.init call sites
    for site in scan['native_loader_init_sites']:
        key = f"{site['calling_class']}.{site['calling_method']}"
        if key in executed_descs:
            site['on_execution_path'] = True

    # Determine the first native method that entered the log (if any).
    first_native = None
    for method, idx in executed_set_with_index:
        if method in scan['native_method_lookup']:
            first_native = {
                'method': method,
                'index': idx,
                'record': scan['native_method_lookup'][method],
            }
            break

    if first_native is not None:
        jni_distance = first_native['index']
    else:
        jni_distance = "not reached yet"

    # Static call chain: list every (caller, native_target) where the
    # caller appears in the execution log and its bytecode calls a native
    # method. This gives a "potential" view of native calls that were
    # statically reachable from the methods that did enter.
    native_call_sites_on_path: List[Dict] = []
    # Build a per-DEX index of (caller_class, caller_method) -> list of
    # native call sites (already collected in load_library_sites and
    # native_loader_init_sites, but those are filtered to specific
    # targets). We need to scan ALL invoke-* sites in the executed
    # methods for native method targets.
    # We rebuild this lazily by re-walking the executed methods.
    # First, group executed methods by DEX so we only walk each DEX once.
    return {
        'executed_methods_set': executed_descs,
        'unique_methods': unique_methods,
        'first_native_method': first_native,
        'jni_distance': jni_distance,
        'native_call_sites_on_path': native_call_sites_on_path,
    }


def static_native_call_chain(
    apk_path: str,
    scan: Dict,
    log_view: Dict,
) -> List[Dict]:
    """For each method that entered the execution log, scan its bytecode
    for any invoke-* targeting either:

      (a) a native method declared in the APK's DEX files, OR
      (b) a framework native method we know about — namely
          `Ljava/lang/System;.loadLibrary`,
          `Ljava/lang/System;.load`,
          `Ljava/lang/Runtime;.loadLibrary0`.

    Returns the list of those call sites as 'potential native calls
    reachable from the execution path' (direct, depth-0).

    Also performs a depth-1 transitive scan: for each invoke-* in an
    executed method whose target is itself a non-native method with
    bytecode in the APK, scans that target's bytecode for invoke-* to
    (a) or (b) — i.e., one Java method call deep. This catches the
    `ApplicationLoader.postInitApplication -> NativeLoader.initNativeLibs
    -> System.loadLibrary("tmessages")` chain even when the executor
    halted before NativeLoader.initNativeLibs was entered.
    """
    if not log_view.get('log_exists'):
        return []
    # Build a (class, method) -> DEX index to know which DEX each
    # executed method lives in.
    method_to_dex: Dict[Tuple[str, str], str] = {}
    # Also store per-DEX method_idx lookup so we can resolve a called
    # method_idx back to a (class, name) descriptor.
    with zipfile.ZipFile(apk_path, "r") as z:
        dex_cache: Dict[str, DexFile] = {}
        native_idxs_per_dex: Dict[str, set] = {}
        loadlib_idxs_per_dex: Dict[str, set] = {}
        method_lookup_per_dex: Dict[str, Dict[int, Tuple[str, str, int]]] = {}
        # ^ method_idx -> (class_descriptor, method_name, code_off)
        for dex_name in DEX_FILES:
            if dex_name not in z.namelist():
                continue
            raw = z.read(dex_name)
            dex = DexFile(dex_name, raw)
            dex_cache[dex_name] = dex
            native_idxs: set = set()
            loadlib_idxs: set = set()
            method_lookup: Dict[int, Tuple[str, str, int]] = {}
            # Walk every method DECLARED in this DEX (via class_defs →
            # class_data_item) to collect native method_idx and a
            # method_idx → (descriptor, name, code_off) lookup.
            for (
                descriptor, _ca, method_name, _shorty,
                method_idx, access_flags, code_off, _mk
            ) in dex.iter_all_methods():
                method_lookup[method_idx] = (descriptor, method_name, code_off)
                method_to_dex[(descriptor, method_name)] = dex_name
                if (access_flags & ACC_NATIVE) != 0:
                    native_idxs.add(method_idx)
            # Walk every method REFERENCED in this DEX (via method_ids[])
            # to find framework native methods (System.loadLibrary, etc.)
            # These have no class_def in the APK's DEX but ARE the JNI
            # entry points we need to detect.
            for mi in range(len(dex._methods)):
                cls = dex.get_method_class(mi)
                name = dex.get_method_name(mi)
                if (cls == "Ljava/lang/System;" and
                        name in ("loadLibrary", "load")):
                    loadlib_idxs.add(mi)
                elif (cls == "Ljava/lang/Runtime;" and
                        name in ("loadLibrary", "loadLibrary0",
                                 "load", "load0")):
                    loadlib_idxs.add(mi)
            native_idxs_per_dex[dex_name] = native_idxs
            loadlib_idxs_per_dex[dex_name] = loadlib_idxs
            method_lookup_per_dex[dex_name] = method_lookup

    out: List[Dict] = []

    for executed_method in log_view['unique_methods']:
        desc = executed_method['method']
        # desc format: 'Lfoo/Bar;.baz' (descriptor + dot + method)
        if not desc.startswith("L") or ";." not in desc:
            continue
        class_part, method_part = desc.split(";.", 1)
        class_desc = class_part + ";"
        method_name = method_part
        dex_name = method_to_dex.get((class_desc, method_name))
        if dex_name is None:
            continue
        dex = dex_cache[dex_name]
        # Find code_off and method_idx for this method.
        method_idx = None
        code_off = None
        for mi, (cd, mn, co) in method_lookup_per_dex[dex_name].items():
            if cd == class_desc and mn == method_name:
                method_idx = mi
                code_off = co
                break
        if code_off is None or code_off == 0:
            continue
        native_idxs = native_idxs_per_dex[dex_name]
        loadlib_idxs = loadlib_idxs_per_dex[dex_name]
        # Depth-0 targets: native methods + framework loadLibrary methods.
        depth0_targets = native_idxs | loadlib_idxs
        if not depth0_targets:
            continue
        sites = scan_invoke_sites(dex, code_off, depth0_targets)
        for s in sites:
            target_native = s['method_idx'] in native_idxs
            target_loadlib = s['method_idx'] in loadlib_idxs
            kind = []
            if target_native:
                kind.append("native-method")
            if target_loadlib:
                kind.append("framework-loadLibrary")
            # Try to recover the const-string argument for loadLibrary calls.
            string_arg = None
            if target_loadlib and s['arg_regs']:
                string_arg = find_recent_const_string(
                    dex, code_off, s['arg_regs'][0], before_pc=s['pc'],
                )
            out.append({
                'depth': 0,
                'caller_class': class_desc,
                'caller_method': method_name,
                'caller_dex': dex_name,
                'caller_method_idx': method_idx,
                'caller_pc': s['pc'],
                'caller_opcode': s['opcode_name'],
                'target_class': s['target_class'],
                'target_method': s['target_name'],
                'target_shorty': s['target_shorty'],
                'target_method_idx': s['method_idx'],
                'target_kind': ",".join(kind),
                'string_argument': string_arg,
                'caller_first_seen_index': executed_method['first_seen_index'],
            })
        # Depth-1 transitive scan: look at every invoke-* target in the
        # executed method's bytecode. If the target is a non-native
        # method with bytecode in this DEX, scan THAT method's bytecode
        # for invoke-* to depth0_targets.
        all_invoke_targets: set = set()
        # Walk the executed method's bytecode to find all invoke-* method_idx.
        import struct as _struct
        _hdr = _struct.unpack('<HHHHII', dex.data[code_off:code_off+16])
        _insns_size = _hdr[5]
        _insns_off = code_off + 16
        _raw = dex.data[_insns_off:_insns_off + _insns_size * 2]
        if len(_raw) >= _insns_size * 2:
            _units = _struct.unpack(f"<{_insns_size}H", _raw)
            _pc = 0
            while _pc < _insns_size:
                _op_word = _units[_pc]
                _op = _op_word & 0xFF
                _high = (_op_word >> 8) & 0xFF
                _info = OPS.get(_op)
                if _info is None:
                    _pc += 1
                    continue
                _name, _units_n, _fmt = _info
                if _op in INVOKE_OPS and _pc + 1 < _insns_size:
                    all_invoke_targets.add(_units[_pc + 1])
                # Skip payloads
                if _op == 0x00 and _high == 0x01 and _pc + 1 < _insns_size:
                    _sz = _units[_pc + 1]
                    _pc += 3 + _sz * 2
                    continue
                if _op == 0x00 and _high == 0x02 and _pc + 1 < _insns_size:
                    _sz = _units[_pc + 1]
                    _pc += 2 + _sz * 4
                    continue
                if _op == 0x00 and _high == 0x03 and _pc + 1 < _insns_size:
                    _sz = _units[_pc + 1]
                    _ew = _units[_pc + 2] if _pc + 2 < _insns_size else 0
                    _du = (_sz * _ew + 1) // 2
                    _pc += 3 + _du
                    continue
                _pc += _units_n
        # For each invoked target that is a non-native Java method in
        # this same DEX, scan its bytecode for invoke-* to depth0_targets.
        # Also try cross-DEX (look up via method_to_dex by descriptor).
        for invoked_idx in all_invoke_targets:
            if invoked_idx in depth0_targets:
                continue  # already reported at depth-0
            # Resolve via this DEX's method lookup (the method_idx is
            # relative to the calling DEX's method_ids[]).
            target_info = method_lookup_per_dex[dex_name].get(invoked_idx)
            if target_info is None:
                continue
            (target_class, target_name, target_code_off) = target_info
            if target_code_off == 0:
                continue
            # Look up the target DEX (in case of cross-DEX invokes — but
            # method_idx is per-DEX, so the target DEX must be the same
            # as the calling DEX).
            sites_inner = scan_invoke_sites(
                dex, target_code_off, depth0_targets
            )
            for s in sites_inner:
                target_native = s['method_idx'] in native_idxs
                target_loadlib = s['method_idx'] in loadlib_idxs
                if not (target_native or target_loadlib):
                    continue
                kind = []
                if target_native:
                    kind.append("native-method")
                if target_loadlib:
                    kind.append("framework-loadLibrary")
                string_arg = None
                if target_loadlib and s['arg_regs']:
                    string_arg = find_recent_const_string(
                        dex, target_code_off, s['arg_regs'][0],
                        before_pc=s['pc'],
                    )
                out.append({
                    'depth': 1,
                    'caller_class': class_desc,
                    'caller_method': method_name,
                    'caller_dex': dex_name,
                    'caller_method_idx': method_idx,
                    'caller_pc': -1,
                    'caller_opcode': 'transitive-via-invoke-*',
                    'intermediate_class': target_class,
                    'intermediate_method': target_name,
                    'intermediate_pc': s['pc'],
                    'intermediate_opcode': s['opcode_name'],
                    'target_class': s['target_class'],
                    'target_method': s['target_name'],
                    'target_shorty': s['target_shorty'],
                    'target_method_idx': s['method_idx'],
                    'target_kind': ",".join(kind),
                    'string_argument': string_arg,
                    'caller_first_seen_index':
                        executed_method['first_seen_index'],
                })
    # Deduplicate by (caller, depth, target, intermediate, pc)
    seen = set()
    deduped = []
    for entry in out:
        key = (
            entry['caller_class'], entry['caller_method'],
            entry.get('intermediate_class', ''),
            entry.get('intermediate_method', ''),
            entry['target_class'], entry['target_method'],
            entry.get('intermediate_pc', entry['caller_pc']),
            entry['depth'],
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(entry)
    # Sort: depth-0 first, then depth-1, ordered by caller_first_seen_index
    deduped.sort(key=lambda e: (e['depth'],
                                e['caller_first_seen_index'],
                                e.get('intermediate_pc', e['caller_pc'])))
    return deduped


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

def render_markdown(scan: Dict, log_view: Dict, xref: Dict,
                    static_chain: List[Dict]) -> str:
    lines: List[str] = []
    lines.append("# EXP-043 Phase 2 — JNI Early Reach Analysis")
    lines.append("")
    lines.append(
        "Determines how many DEX methods execute before the first native "
        "(JNI) call is encountered on Telegram's startup path. Generated "
        "by `miniandroid/tools/exp043_jni_distance.py`."
    )
    lines.append("")
    lines.append("## 1. Summary")
    lines.append("")
    lines.append(f"- **APK**: `{scan['apk']}`")
    lines.append(f"- **DEX files scanned**: {len(scan['dex_stats'])}")
    lines.append(f"- **Total native methods**: {scan['total_native_methods']}")
    lines.append(
        f"- **Total `System.loadLibrary` call sites**: "
        f"{scan['total_load_library_sites']}"
    )
    lines.append(
        f"- **Total `NativeLoader.init` call sites**: "
        f"{scan['total_native_loader_init_sites']}"
    )
    if log_view.get('log_exists'):
        lines.append(
            f"- **Execution log**: `{log_view['log_path']}`"
        )
        lines.append(
            f"- **Methods entered (with repeats)**: "
            f"{len(log_view['method_in_order'])}"
        )
        lines.append(
            f"- **Unique methods entered**: "
            f"{len(log_view['unique_methods'])}"
        )
        lines.append(
            f"- **Methods that completed (`method_exit`)**: "
            f"{len(log_view['method_exits'])}"
        )
        lines.append(
            f"- **Halts recorded**: {len(log_view['halts'])}"
        )
        lines.append(
            f"- **JNI distance**: "
            f"{xref['jni_distance']}"
        )
        if xref['first_native_method']:
            fm = xref['first_native_method']
            lines.append(
                f"- **First native method on execution path**: "
                f"`{fm['method']}` (entered at index {fm['index']})"
            )
        else:
            lines.append(
                f"- **First native method on execution path**: "
                f"*none — execution halted before any native method was "
                f"invoked.*"
            )
    else:
        lines.append(
            f"- **Execution log**: not found at "
            f"`{log_view.get('log_path', EXEC_LOG_PATH)}`"
        )
    lines.append("")

    lines.append("## 2. Per-DEX Native-Method Counts")
    lines.append("")
    lines.append("| DEX file | Size (B) | Classes | Methods | Native methods | Classes w/ native |")
    lines.append("|----------|---------:|--------:|--------:|---------------:|-------------------:|")
    for dex_name, stats in scan['dex_stats'].items():
        lines.append(
            f"| {dex_name} | {stats['file_size_bytes']:,} | "
            f"{stats['classes']:,} | {stats['methods']:,} | "
            f"{stats['native_methods']} | {stats['classes_with_native']} |"
        )
    total_classes = sum(s['classes'] for s in scan['dex_stats'].values())
    total_methods = sum(s['methods'] for s in scan['dex_stats'].values())
    total_native = sum(s['native_methods'] for s in scan['dex_stats'].values())
    total_native_classes = sum(s['classes_with_native'] for s in scan['dex_stats'].values())
    lines.append(
        f"| **TOTAL** | — | **{total_classes:,}** | **{total_methods:,}** | "
        f"**{total_native}** | **{total_native_classes}** |"
    )
    lines.append("")

    lines.append("## 3. `System.loadLibrary` Call Sites")
    lines.append("")
    if scan['load_library_sites']:
        # Filter to interesting ones (library name contains a real string
        # OR calling class on the execution path).
        interesting = sorted(
            scan['load_library_sites'],
            key=lambda s: (s['on_execution_path'], s['library_name'],
                           s['calling_class'], s['calling_method'])
        )
        interesting.reverse()
        # Show top 40.
        lines.append(
            f"Found **{len(scan['load_library_sites'])}** `invoke-static` "
            f"call sites resolving to `Ljava/lang/System;.loadLibrary`, "
            f"`Ljava/lang/System;.load`, or "
            f"`Ljava/lang/Runtime;.loadLibrary0`."
        )
        lines.append("")
        on_path = [s for s in scan['load_library_sites'] if s['on_execution_path']]
        if on_path:
            lines.append(
                f"Of those, **{len(on_path)}** are reachable from a "
                f"method on the execution path (caller was entered):"
            )
            lines.append("")
            lines.append("| Calling class | Calling method | Library | Opcode | PC | DEX | On path? |")
            lines.append("|---------------|-----------------|---------|--------|---:|-----|:---------:|")
            for s in on_path:
                lines.append(
                    f"| `{s['calling_class']}` | `{s['calling_method']}` | "
                    f"`{s['library_name']}` | `{s['opcode']}` | {s['pc']} | "
                    f"{s['calling_dex']} | {'✅' if s['on_execution_path'] else '—'} |"
                )
            lines.append("")
        # Also list any sites whose library name looks like tmessages.
        tmessages_sites = [
            s for s in scan['load_library_sites']
            if s['library_name'] and 'tmessages' in s['library_name'].lower()
        ]
        if tmessages_sites:
            lines.append(
                f"### 3a. `tmessages` library load sites ({len(tmessages_sites)})"
            )
            lines.append("")
            lines.append("| Calling class | Calling method | Library | Opcode | PC | DEX | On path? |")
            lines.append("|---------------|-----------------|---------|--------|---:|-----|:---------:|")
            for s in tmessages_sites:
                lines.append(
                    f"| `{s['calling_class']}` | `{s['calling_method']}` | "
                    f"`{s['library_name']}` | `{s['opcode']}` | {s['pc']} | "
                    f"{s['calling_dex']} | {'✅' if s['on_execution_path'] else '—'} |"
                )
            lines.append("")
    else:
        lines.append("No `System.loadLibrary` call sites were found.")
        lines.append("")

    lines.append("## 4. `NativeLoader.init` Call Sites")
    lines.append("")
    if scan['native_loader_init_sites']:
        lines.append(
            f"Found **{len(scan['native_loader_init_sites'])}** "
            f"`invoke-static` call sites resolving to "
            f"`Lorg/telegram/messenger/NativeLoader;.init` (which is itself a "
            f"`native` method — see `miniandroid/docs/exp042/JNI_INVENTORY.md`)."
        )
        lines.append("")
        on_path = [s for s in scan['native_loader_init_sites']
                   if s['on_execution_path']]
        lines.append(
            f"Of those, **{len(on_path)}** are reachable from a method on "
            f"the execution path."
        )
        lines.append("")
        lines.append("| Calling class | Calling method | Target shorty | Opcode | PC | DEX | On path? |")
        lines.append("|---------------|-----------------|----------------|--------|---:|-----|:---------:|")
        for s in scan['native_loader_init_sites'][:60]:
            lines.append(
                f"| `{s['calling_class']}` | `{s['calling_method']}` | "
                f"`{s['target_shorty']}` | `{s['opcode']}` | {s['pc']} | "
                f"{s['calling_dex']} | {'✅' if s['on_execution_path'] else '—'} |"
            )
        if len(scan['native_loader_init_sites']) > 60:
            lines.append(
                f"| … ({len(scan['native_loader_init_sites']) - 60} more rows elided) "
                f"| | | | | | |"
            )
        lines.append("")
    else:
        lines.append(
            "No `NativeLoader.init` call sites were found in any DEX file."
        )
        lines.append("")

    lines.append("## 5. JNI Distance")
    lines.append("")
    if not log_view.get('log_exists'):
        lines.append(
            "No execution log was found — JNI distance cannot be measured. "
            "Run `./build_exp042.sh && timeout 30 ./build_exp042/miniandroid_exp042 "
            "download/exp038_telegram/Telegram.apk run/exp043_jni_probe` to "
            "produce `miniandroid/run/exp043_phase1.log`."
        )
    else:
        unique = log_view['unique_methods']
        first_native = xref['first_native_method']
        if first_native is not None:
            lines.append(
                f"**JNI distance = {xref['jni_distance']}** "
                f"methods — the first native method, "
                f"`{first_native['method']}`, entered at position "
                f"{first_native['index']} in the ordered unique-method-entry "
                f"list (1-indexed: position {first_native['index'] + 1})."
            )
        else:
            lines.append(
                f"**JNI distance = not reached yet.** The current execution "
                f"trace contains **{len(unique)}** unique method entries; "
                f"none of them are native methods. Execution halted before "
                f"any `invoke-*` on a native method could complete."
            )
        lines.append("")
        lines.append("### 5a. First 30 unique method entries (in execution order)")
        lines.append("")
        lines.append("| # | Method | Bytecode size | Native? |")
        lines.append("|---:|--------|--------------:|:-------:|")
        for i, m in enumerate(unique[:30]):
            key = m['method']
            is_native = key in scan['native_method_lookup']
            lines.append(
                f"| {i} | `{key}` | {m['bytecode_size']} | "
                f"{'**NATIVE**' if is_native else ''} |"
            )
        if len(unique) > 30:
            lines.append(
                f"| … | ({len(unique) - 30} more entries) | | |"
            )
        lines.append("")

    lines.append("## 6. First Native Method on the Execution Path")
    lines.append("")
    fm = xref['first_native_method']
    if fm is None:
        lines.append(
            "**None.** No native method appears in the execution log. "
            "Cross-referenced against the 462-method JNI inventory from "
            "`miniandroid/docs/exp042/JNI_INVENTORY.md` — zero matches."
        )
    else:
        rec = fm['record']
        lines.append(f"- **Method**: `{fm['method']}`")
        lines.append(f"- **DEX file**: `{rec['dex']}`")
        lines.append(f"- **Prototype (shorty)**: `{rec['shorty']}`")
        lines.append(f"- **Library**: `{rec['library']}`")
        lines.append(f"- **Priority**: `{rec['priority']}`")
        lines.append(f"- **First entered at**: unique-method index {fm['index']}")
    lines.append("")

    lines.append("## 7. Call Chain from `LaunchActivity.onCreate` to First Native Method")
    lines.append("")
    if not log_view.get('log_exists'):
        lines.append("Execution log not available; chain cannot be reconstructed.")
    elif xref['first_native_method'] is None:
        # Static fallback — list every native call site reachable from
        # any method that did enter the execution log.
        if static_chain:
            # Group by depth.
            depth0 = [c for c in static_chain if c.get('depth', 0) == 0]
            depth1 = [c for c in static_chain if c.get('depth', 0) == 1]
            lines.append(
                "**Static analysis**: Although no native method itself "
                "entered the log, the bytecode of methods that *did* enter "
                "the log contains the following `invoke-*` instructions "
                "whose targets are native methods (or framework native "
                "methods like `System.loadLibrary`). The first one to "
                "execute (had the interpreter progressed past the current "
                "halt) would have been the first native call."
            )
            lines.append("")
            if depth0:
                lines.append(
                    f"### 7a. Depth-0 call sites ({len(depth0)})"
                )
                lines.append("")
                lines.append(
                    "Invoke-* in an executed method whose target is "
                    "directly a native method (declared in the APK) OR a "
                    "framework native method "
                    "(`Ljava/lang/System;.loadLibrary`, "
                    "`Ljava/lang/System;.load`, "
                    "`Ljava/lang/Runtime;.loadLibrary0`)."
                )
                lines.append("")
                lines.append(
                    "| # | Caller (executed) | PC | → Target | String arg | "
                    "Kind | DEX |"
                )
                lines.append(
                    "|---:|-------------------|---:|-----------|-------------"
                    "-----|------|-----|"
                )
                for i, c in enumerate(depth0[:80]):
                    sa = c.get('string_argument') or '—'
                    lines.append(
                        f"| {i} | "
                        f"`{c['caller_class']};.{c['caller_method']}` | "
                        f"{c['caller_pc']} | "
                        f"`{c['target_class']};.{c['target_method']}` "
                        f"(`{c['target_shorty']}`) | "
                        f"`{sa}` | `{c['target_kind']}` | "
                        f"{c['caller_dex']} |"
                    )
                if len(depth0) > 80:
                    lines.append(
                        f"| … | ({len(depth0) - 80} more depth-0 sites "
                        f"elided) | | | | | |"
                    )
                lines.append("")
            if depth1:
                lines.append(
                    f"### 7b. Depth-1 transitive call sites ({len(depth1)})"
                )
                lines.append("")
                lines.append(
                    "Invoke-* in an executed method whose target is a "
                    "*Java* (non-native) helper method that itself "
                    "contains an `invoke-*` to a native method or "
                    "`System.loadLibrary`. These would have been reached "
                    "if execution had progressed past the current halt in "
                    "the executed method."
                )
                lines.append("")
                lines.append(
                    "| # | Executed caller | → Java intermediate "
                    "(intermediate PC) | → Native target | String arg | "
                    "Kind | DEX |"
                )
                lines.append(
                    "|---:|------------------|-------------------------|----"
                    "--------------|--------------|------|-----|"
                )
                for i, c in enumerate(depth1[:80]):
                    sa = c.get('string_argument') or '—'
                    lines.append(
                        f"| {i} | "
                        f"`{c['caller_class']};.{c['caller_method']}` | "
                        f"`{c['intermediate_class']};.{c['intermediate_method']}` "
                        f"(PC={c['intermediate_pc']}, "
                        f"`{c['intermediate_opcode']}`) | "
                        f"`{c['target_class']};.{c['target_method']}` "
                        f"(`{c['target_shorty']}`) | "
                        f"`{sa}` | `{c['target_kind']}` | "
                        f"{c['caller_dex']} |"
                    )
                if len(depth1) > 80:
                    lines.append(
                        f"| … | ({len(depth1) - 80} more depth-1 sites "
                        f"elided) | | | | | |"
                    )
                lines.append("")
            # Halt summary
            halt_kinds: Dict[str, int] = defaultdict(int)
            for h in log_view['halts']:
                halt_kinds[h['kind']] += 1
            lines.append("### 7c. Why execution halted before reaching the native call")
            lines.append("")
            lines.append(
                f"Halt summary (from `{log_view['log_path']}`):"
            )
            lines.append("")
            lines.append("| Halt kind | Count |")
            lines.append("|-----------|------:|")
            for kind, count in sorted(halt_kinds.items()):
                lines.append(f"| {kind} | {count} |")
            lines.append("")
            lines.append(
                "First 5 halt messages (representative sample):"
            )
            lines.append("")
            for h in log_view['halts'][:5]:
                lines.append(f"- `[HALT-{h['kind']}] {h['message']}`")
            lines.append("")
        else:
            lines.append(
                "Static analysis found no `invoke-*` to a native method "
                "in the bytecode of any method that entered the execution "
                "log. The execution halted too early in each method for any "
                "native call to be reachable through normal control flow "
                "(the halts are all in goto targets)."
            )
            lines.append("")
            # Add the halt summary
            halt_kinds: Dict[str, int] = defaultdict(int)
            for h in log_view['halts']:
                halt_kinds[h['kind']] += 1
            lines.append(
                f"Halt summary (from `{log_view['log_path']}`):"
            )
            lines.append("")
            lines.append("| Halt kind | Count |")
            lines.append("|-----------|------:|")
            for kind, count in sorted(halt_kinds.items()):
                lines.append(f"| {kind} | {count} |")
            lines.append("")
            lines.append(
                "First 5 halt messages (representative sample):"
            )
            lines.append("")
            for h in log_view['halts'][:5]:
                lines.append(f"- `[HALT-{h['kind']}] {h['message']}`")
            lines.append("")
    else:
        fm = xref['first_native_method']
        # Walk the unique-method list up to and including the first
        # native entry.
        unique = log_view['unique_methods']
        idx = fm['index']
        chain = unique[:idx + 1]
        lines.append(
            f"**Reachable chain** (positions 0 → {idx}):"
        )
        lines.append("")
        lines.append("| # | Method | Bytecode size | Native? |")
        lines.append("|---:|--------|--------------:|:-------:|")
        for i, m in enumerate(chain):
            key = m['method']
            is_native = key in scan['native_method_lookup']
            lines.append(
                f"| {i} | `{key}` | {m['bytecode_size']} | "
                f"{'**NATIVE**' if is_native else ''} |"
            )
        lines.append("")

    lines.append("## 8. Required Native Functions for the First Native Call")
    lines.append("")
    fm = xref['first_native_method']
    if fm is None:
        if static_chain:
            # The first reachable native target — prefer depth-0 sites,
            # fall back to depth-1.
            depth0 = [c for c in static_chain if c.get('depth', 0) == 0]
            depth1 = [c for c in static_chain if c.get('depth', 0) == 1]
            pick = depth0[0] if depth0 else (depth1[0] if depth1 else None)
            if pick is not None:
                target_class = pick['target_class']
                target_method = pick['target_method']
                shorty = pick['target_shorty']
                kind = pick.get('target_kind', 'native')
                if pick.get('depth', 0) == 0:
                    caller_label = (
                        f"`{pick['caller_class']};.{pick['caller_method']}` "
                        f"at PC {pick['caller_pc']}"
                    )
                else:
                    caller_label = (
                        f"`{pick['caller_class']};.{pick['caller_method']}` "
                        f"→ `{pick.get('intermediate_class', '')};."
                        f"{pick.get('intermediate_method', '')}` "
                        f"(intermediate PC {pick.get('intermediate_pc')})"
                    )
                lines.append(
                    f"If execution had progressed past the current halt, "
                    f"the first native call would have been "
                    f"`{target_class};.{target_method}` "
                    f"(shorty `{shorty}`, kind=`{kind}`), reachable from "
                    f"{caller_label} in `{pick['caller_dex']}`."
                )
                lines.append("")
                if kind == 'framework-loadLibrary':
                    sym = 'System.loadLibrary (framework native; loads '
                    sym += 'libtmessages.49.so and triggers JNI_OnLoad)'
                    lines.append(
                        f"This is a **framework** native call — "
                        f"`System.loadLibrary` is declared native in the "
                        f"Android framework (not in the APK's DEX). It "
                        f"loads `libtmessages.49.so` from disk and, as a "
                        f"side effect, invokes `JNI_OnLoad` from the .so "
                        f"file. The full list of `Java_*` exports that "
                        f"become available after this load is in "
                        f"`miniandroid/docs/exp042/NATIVE_LIBRARIES.md`."
                    )
                else:
                    sym = jni_symbol_for(target_class, target_method)
                    lines.append(
                        f"Required `Java_*` JNI export symbol: "
                        f"`{sym}`"
                    )
            else:
                lines.append(
                    "No first native call can be identified from the "
                    "available evidence."
                )
        else:
            lines.append(
                "No first native call can be identified from the "
                "available evidence. Execution halted too early in every "
                "method that entered the log; the bytecode of those "
                "methods does not statically contain any `invoke-*` to a "
                "native method."
            )
    else:
        rec = fm['record']
        sym = jni_symbol_for(rec['class'], rec['method'])
        lines.append(f"- **Method**: `{fm['method']}`")
        lines.append(f"- **Shorty**: `{rec['shorty']}`")
        lines.append(f"- **JNI export symbol**: `{sym}`")
        lines.append(
            f"- **Library**: `{rec['library']}` "
            f"(see `miniandroid/docs/exp042/NATIVE_LIBRARIES.md` for the "
            f"full export table)"
        )
    lines.append("")

    lines.append("## 9. Methodology")
    lines.append("")
    lines.append(
        "1. **DEX parsing** — read the 112-byte DexHeader from each DEX "
        "file inside the APK ZIP, then walked `string_ids[]`, "
        "`type_ids[]`, `proto_ids[]`, `method_ids[]` and `class_defs[]` "
        "using the canonical `dalvik/libdex/DexFile.h` layout. No "
        "third-party dependencies were used."
    )
    lines.append(
        "2. **Native-method enumeration** — for each `class_def`, walked "
        "the `class_data_item` (ULEB128-decoded `static_fields_size` / "
        "`instance_fields_size` / `direct_methods_size` / "
        "`virtual_methods_size`), then walked the encoded_method[] arrays "
        "with delta-decoded `method_idx_diff`. A method is `native` iff "
        "`(access_flags & 0x100) != 0`."
    )
    lines.append(
        "3. **Call-site scanning** — for every method whose `code_off` is "
        "non-zero, walked its `code_item` 16-bit instruction stream using "
        "a Dalvik opcode table (reused from "
        "`miniandroid/tools/exp042_disasm.py`). For every `invoke-*` "
        "instruction (`0x6e`–`0x78`), looked up the target method_idx and "
        "checked whether it resolves to `Ljava/lang/System;.loadLibrary`, "
        "`Ljava/lang/System;.load`, "
        "`Ljava/lang/Runtime;.loadLibrary0`, or "
        "`Lorg/telegram/messenger/NativeLoader;.init`. For `loadLibrary` "
        "sites, additionally walked the method's instruction stream "
        "again to find the most-recent `const-string` write to the "
        "first argument register."
    )
    lines.append(
        "4. **Execution-log parsing** — read "
        f"`{log_view.get('log_path', EXEC_LOG_PATH)}` line-by-line, "
        "matching `[METHOD-IN]` lines to build the ordered method-entry "
        "list. `[MEM] method_exit:` and `[HALT-*]` lines were also "
        "captured for diagnostics."
    )
    lines.append(
        "5. **JNI distance** — measured as the index in the deduped "
        "unique-method-entry list at which the first *native* method "
        "first appears (descriptor + method name cross-referenced against "
        "the native-method inventory built in step 2). If no native "
        "method entered the log, the distance is reported as "
        "`not reached yet`."
    )
    lines.append(
        "6. **Static call-chain fallback** — when no native method "
        "itself entered the log, a static sweep was performed: for each "
        "method that *did* enter the log, scan its bytecode for any "
        "`invoke-*` to a native method, and report those sites as "
        "potential future native calls."
    )
    lines.append("")

    return "\n".join(lines) + "\n"


def jni_symbol_for(class_desc: str, method_name: str) -> str:
    """Compute the JNI symbol name that the dynamic linker would resolve
    for a `Java_<class>_<method>` export. Replaces '/' with '_' and
    drops the trailing ';' from the descriptor."""
    cls = class_desc
    if cls.startswith("L") and cls.endswith(";"):
        cls = cls[1:-1]
    cls = cls.replace("/", "_")
    # Underscores in the Java class/method names get `_1` in JNI symbols.
    cls = cls.replace("_", "_1")
    method = method_name.replace("_", "_1")
    return f"Java_{cls}_{method}"


# ---------------------------------------------------------------------------
# JSON rendering
# ---------------------------------------------------------------------------

def render_json(scan: Dict, log_view: Dict, xref: Dict,
                static_chain: List[Dict]) -> Dict:
    return {
        'apk': scan['apk'],
        'execution_log': log_view.get('log_path'),
        'execution_log_exists': bool(log_view.get('log_exists')),
        'dex_stats': scan['dex_stats'],
        'totals': {
            'native_methods': scan['total_native_methods'],
            'load_library_sites': scan['total_load_library_sites'],
            'native_loader_init_sites': scan['total_native_loader_init_sites'],
            'unique_methods_in_log': (
                len(log_view['unique_methods'])
                if log_view.get('log_exists') else 0
            ),
            'method_entries_with_repeats': (
                len(log_view['method_in_order'])
                if log_view.get('log_exists') else 0
            ),
            'method_exits': (
                len(log_view['method_exits'])
                if log_view.get('log_exists') else 0
            ),
            'halts': (
                len(log_view['halts'])
                if log_view.get('log_exists') else 0
            ),
        },
        'jni_distance': xref['jni_distance'],
        'first_native_method_on_path': xref['first_native_method'],
        'native_methods_per_dex': {
            dex: stats['native_methods']
            for dex, stats in scan['dex_stats'].items()
        },
        'load_library_sites': scan['load_library_sites'],
        'load_library_sites_on_path': [
            s for s in scan['load_library_sites']
            if s['on_execution_path']
        ],
        'native_loader_init_sites': scan['native_loader_init_sites'],
        'native_loader_init_sites_on_path': [
            s for s in scan['native_loader_init_sites']
            if s['on_execution_path']
        ],
        'static_native_call_chain': static_chain,
        'native_method_descriptors': sorted(
            scan['native_method_lookup'].keys()
        ),
        'native_methods': scan['native_methods'],
        'unique_methods_in_log': log_view.get('unique_methods', []),
        'halts': log_view.get('halts', []),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("[EXP-043-PHASE2] JNI Early Reach Analysis", file=sys.stderr)
    print(f"  APK:  {APK_PATH}", file=sys.stderr)
    print(f"  LOG:  {EXEC_LOG_PATH}", file=sys.stderr)
    print(f"  OUT:  {MD_PATH}", file=sys.stderr)
    print(f"        {JSON_PATH}", file=sys.stderr)
    print("", file=sys.stderr)

    if not os.path.exists(APK_PATH):
        print(f"[FATAL] APK not found: {APK_PATH}", file=sys.stderr)
        sys.exit(2)

    print("[1/4] Scanning DEX files for native methods and call sites…",
          file=sys.stderr)
    scan = scan_apk(APK_PATH)
    print(
        f"      → {scan['total_native_methods']} native methods, "
        f"{scan['total_load_library_sites']} loadLibrary call sites, "
        f"{scan['total_native_loader_init_sites']} NativeLoader.init "
        f"call sites",
        file=sys.stderr,
    )
    print("", file=sys.stderr)

    print("[2/4] Parsing execution log…", file=sys.stderr)
    log_view = parse_execution_log(EXEC_LOG_PATH)
    if log_view.get('log_exists'):
        print(
            f"      → {len(log_view['unique_methods'])} unique methods, "
            f"{len(log_view['method_in_order'])} entries (with repeats), "
            f"{len(log_view['method_exits'])} exits, "
            f"{len(log_view['halts'])} halts",
            file=sys.stderr,
        )
    else:
        print(f"      → log not found at {EXEC_LOG_PATH}",
              file=sys.stderr)
    print("", file=sys.stderr)

    print("[3/4] Cross-referencing with execution log…", file=sys.stderr)
    xref = cross_reference_with_log(scan, log_view)
    n_native_on_path = sum(1 for nm in scan['native_methods']
                           if nm['on_execution_path'])
    n_loadlib_on_path = sum(1 for s in scan['load_library_sites']
                            if s['on_execution_path'])
    n_nativeloader_on_path = sum(1 for s in scan['native_loader_init_sites']
                                 if s['on_execution_path'])
    print(
        f"      → {n_native_on_path} native methods on execution path, "
        f"{n_loadlib_on_path} loadLibrary call sites on path, "
        f"{n_nativeloader_on_path} NativeLoader.init call sites on path",
        file=sys.stderr,
    )
    print("", file=sys.stderr)

    print("[4/4] Building static native-call chain from executed methods…",
          file=sys.stderr)
    static_chain = static_native_call_chain(APK_PATH, scan, log_view)
    print(
        f"      → {len(static_chain)} potential native call sites "
        f"statically reachable from executed methods",
        file=sys.stderr,
    )
    print("", file=sys.stderr)

    print("Rendering Markdown + JSON…", file=sys.stderr)
    os.makedirs(OUT_DIR, exist_ok=True)
    md = render_markdown(scan, log_view, xref, static_chain)
    with open(MD_PATH, "w", encoding="utf-8") as fh:
        fh.write(md)
    print(f"  → wrote {MD_PATH} ({len(md):,} bytes)", file=sys.stderr)

    payload = render_json(scan, log_view, xref, static_chain)
    with open(JSON_PATH, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
    print(f"  → wrote {JSON_PATH}", file=sys.stderr)

    # Print final summary to stdout (also goes to the worklog).
    print("", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print("EXP-043-PHASE2 JNI EARLY REACH ANALYSIS — SUMMARY",
          file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    for dex_name, stats in scan['dex_stats'].items():
        print(
            f"  {dex_name:15s}  native={stats['native_methods']:4d}  "
            f"loadLibrary_calls=?  NativeLoader.init_calls=?",
            file=sys.stderr,
        )
    print(
        f"  TOTAL native methods: {scan['total_native_methods']}",
        file=sys.stderr,
    )
    print(
        f"  TOTAL System.loadLibrary call sites: "
        f"{scan['total_load_library_sites']}",
        file=sys.stderr,
    )
    print(
        f"  TOTAL NativeLoader.init call sites: "
        f"{scan['total_native_loader_init_sites']}",
        file=sys.stderr,
    )
    if log_view.get('log_exists'):
        print(
            f"  Unique methods in execution log: "
            f"{len(log_view['unique_methods'])}",
            file=sys.stderr,
        )
    print(
        f"  JNI distance: {xref['jni_distance']}",
        file=sys.stderr,
    )
    if xref['first_native_method']:
        print(
            f"  First native method on path: "
            f"{xref['first_native_method']['method']}",
            file=sys.stderr,
        )
    else:
        print(
            "  First native method on path: NONE (execution halted before "
            "any native method was invoked)",
            file=sys.stderr,
        )
    print(f"  MD:   {MD_PATH}", file=sys.stderr)
    print(f"  JSON: {JSON_PATH}", file=sys.stderr)
    print(f"  PY:   /home/z/my-project/MiniAndroid-Compatibility-Runtime/"
          f"miniandroid/tools/exp043_jni_distance.py",
          file=sys.stderr)


if __name__ == "__main__":
    main()
