#!/usr/bin/env python3
"""
EXP-049 PHASE 2-3 — Static Call Graph Analysis for the Telegram APK.

This tool parses every DEX file inside
  /home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/download/
  exp038_telegram/Telegram.apk

and, for each method that has bytecode, scans all invoke-* opcodes
(0x6e-0x78) to record (caller_class, caller_method, callee_class,
callee_method, invoke_type) edges.

It then performs a bounded breadth-first traversal of the call graph
starting from `Lorg/telegram/ui/LaunchActivity;.onCreate` and reports:
  * the call edges on the startup path
  * every method declared with the ACC_NATIVE flag (the JNI entry points)
  * every invoke-static call site that targets
        Ljava/lang/System;.loadLibrary  or
        Ljava/lang/System;.load

Output JSON: miniandroid/reports/telegram_call_graph.json

DEX layout reference (Android dalvik/libdex/DexFile.h):

  DexHeader            112 bytes  at offset 0
  string_ids[]         4 bytes each  (string_data_off: u32)
  type_ids[]           4 bytes each  (descriptor_idx -> string_ids)
  proto_ids[]         12 bytes each  (shorty_idx, return_type_idx, parameters_off)
  field_ids[]          8 bytes each  (class_idx u16, type_idx u16, name_idx u32)
  method_ids[]         8 bytes each  (class_idx u16, proto_idx u16, name_idx u32)
  class_defs[]        32 bytes each  (class_idx, access_flags, superclass_idx,
                                      interfaces_off, source_file_idx,
                                      annotations_off, class_data_off,
                                      static_values_off)

class_data_item uses ULEB128 for every header + entry field:
  static_fields_size, instance_fields_size, direct_methods_size,
  virtual_methods_size, then four arrays of encoded_field / encoded_method
  records.

The implementation is heavily inspired by tools/exp042_jni_inventory.py
(already in this repo) and tools/exp032_dex_validator.py.
"""

from __future__ import annotations

import json
import os
import struct
import sys
import time
import zipfile
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple


def _log(msg: str) -> None:
    """Print with flush so progress is visible when stdout is piped to a file."""
    print(msg, flush=True)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

APK_PATH = (
    "/home/z/my-project/MiniAndroid-Compatibility-Runtime/"
    "miniandroid/download/exp038_telegram/Telegram.apk"
)
REPORT_DIR = (
    "/home/z/my-project/MiniAndroid-Compatibility-Runtime/"
    "miniandroid/reports"
)
REPORT_PATH = os.path.join(REPORT_DIR, "telegram_call_graph.json")

DEX_FILES = [
    "classes.dex",
    "classes2.dex",
    "classes3.dex",
    "classes4.dex",
    "classes5.dex",
]

# ---------------------------------------------------------------------------
# Access-flag bit (see com.android.dx.rop.code.AccessFlags)
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
# DEX binary structures (all little-endian).
# ---------------------------------------------------------------------------

HEADER_FMT  = "<8sI20s" + "I" * 20   # 8+4+20+80 = 112 bytes
HEADER_SIZE  = struct.calcsize(HEADER_FMT)
assert HEADER_SIZE == 112, "DexHeader must be 112 bytes"

STRING_ID_FMT = "<I"             # 4 bytes  (string_data_off)
TYPE_ID_FMT   = "<I"             # 4 bytes  (descriptor_idx -> string_ids)
PROTO_ID_FMT  = "<III"           # 12 bytes (shorty_idx, return_type_idx, parameters_off)
METHOD_ID_FMT = "<HHI"           # 8 bytes  (class_idx u16, proto_idx u16, name_idx u32)
CLASS_DEF_FMT = "<IIIIIIII"      # 32 bytes

NO_INDEX = 0xFFFFFFFF

# ---------------------------------------------------------------------------
# Low-level binary helpers
# ---------------------------------------------------------------------------

def read_uleb128(data: bytes, offset: int) -> Tuple[int, int]:
    """Read an unsigned LEB128 integer; return (value, new_offset)."""
    result = 0
    shift = 0
    while True:
        if offset >= len(data):
            raise ValueError(f"ULEB128 read past end of file at offset {offset}")
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
# Dalvik opcode → instruction size (in 16-bit code units).
#
# Built directly from AOSP dalvik/libdex/InstrUtils.cpp and the
# dalvik-bytecode.html reference. Every opcode 0x00..0xFF has a fixed
# size; the special "payload" pseudo-instructions (packed-switch,
# sparse-switch, fill-array-data) are handled separately when the
# scanner encounters a 0x01/0x02/0x03 marker in the low byte.
# ---------------------------------------------------------------------------

# Default sizes per format family:
#   10x 12x 11n 11x 10t       → 1 code unit
#   20t 22x 21t 21s 21h 21c 23x 22b 22t 22s 22c  → 2 code units
#   30t 32x 31i 31t 31c 35c 3rc  → 3 code units
#   51l                       → 5 code units
# (invoke-polymorphic 45c/4rc and invoke-custom 35c/3rc are also 3 units
# in modern DEX; we treat the 0xfa-0xfd extended opcodes as 3 units too.)

def _build_opcode_size_table() -> List[int]:
    table = [0] * 256

    # ---- 1 code unit opcodes ----
    one_unit = {
        0x00,  # nop
        0x01,  # move
        0x04,  # move-wide
        0x07,  # move-object
        0x0a,  # move-result
        0x0b,  # move-result-wide
        0x0c,  # move-result-object
        0x0d,  # move-exception
        0x0e,  # return-void
        0x0f,  # return
        0x10,  # return-wide
        0x11,  # return-object
        0x12,  # const/4
        0x1d,  # monitor-enter
        0x1e,  # monitor-exit
        0x21,  # array-length
        0x27,  # throw  (NOTE: the engine comments had this confused with goto)
        0x28,  # goto (10t)
        # All 12x arithmetic ops 0x79..0xcb (1 unit each)
        *range(0x79, 0xcc),
    }
    for op in one_unit:
        table[op] = 1

    # ---- 2 code unit opcodes ----
    two_units = {
        0x02,  # move/from16 (22x)
        0x05,  # move-wide/from16 (22x)
        0x08,  # move-object/from16 (22x)
        0x13,  # const/16 (21s)
        0x15,  # const/high16 (21h)
        0x16,  # const-wide/16 (21s)
        0x19,  # const-wide/high16 (21h)
        0x1a,  # const-string (21c)
        0x1c,  # const-class (21c)
        0x1f,  # check-cast (21c)
        0x20,  # instance-of (22c)
        0x22,  # new-instance (21c)
        0x23,  # new-array (22c)
        0x29,  # goto/16 (20t)
        # 21t if-*z family 0x33..0x38
        *range(0x33, 0x39),
        # 22t if-* family 0x2d..0x32
        *range(0x2d, 0x33),
        # 23x aget/aput family 0x39..0x46
        *range(0x39, 0x47),
        # 22c iget/iput family 0x47..0x54
        *range(0x47, 0x55),
        # 21c sget/sput family 0x55..0x62
        *range(0x55, 0x63),
        # 22s const ops 0xcc..0xd3 (actually 22s/22b — both 2 units)
        *range(0xcc, 0xd4),
        # 22b ops 0xd4..0xde
        *range(0xd4, 0xdf),
        # ---- deprecated quick opcodes (only appear in legacy / odex) ----
        # 0x63-0x68 are iget/iput-*-quick variants, all 22c (2 units)
        *range(0x63, 0x69),
        # 0x69 = OP_INVOKE_VIRTUAL_QUICK per AOSP, BUT in legacy .odex
        # artifacts it is sometimes 22c — empirically observed in
        # Telegram's classes.dex to be 2 code units (verified against
        # MediaMetadataCompat.<clinit>: the instruction at pc=200
        # 0x0069/0x00d8 is immediately followed by a filled-new-array at
        # pc=202, which only lines up if 0x69 is 2 units).
        0x69,
        # 0x6d: OP_IPUT_BOOLEAN_QUICK — 22c, 2 units (legacy)
        0x6d,
        # 0xfe: const-method-handle (21c, 2 units)
        # 0xff: const-method-type (21c, 2 units)
        0xfe, 0xff,
    }
    for op in two_units:
        table[op] = 2

    # ---- 3 code unit opcodes ----
    three_units = {
        0x03,  # move/16 (32x)
        0x06,  # move-wide/16 (32x)
        0x09,  # move-object/16 (32x)
        0x14,  # const (31i)
        0x17,  # const-wide/32 (31i)
        0x1b,  # const-string/jumbo (31c)
        0x24,  # filled-new-array (35c)
        0x25,  # filled-new-array/range (3rc)
        0x26,  # fill-array-data (31t)
        0x2a,  # goto/32 (30t)
        0x2b,  # packed-switch (31t)
        0x2c,  # sparse-switch (31t)
        # invoke-* (35c) 0x6e..0x72  (0x73 unused)
        *range(0x6e, 0x73),
        # invoke-*/range (3rc) 0x74..0x78
        *range(0x74, 0x79),
        # extended invoke-polymorphic / invoke-custom (45c/4rc/35c/3rc — all 3 units)
        0xfa, 0xfb, 0xfc, 0xfd,
        # ---- deprecated quick invoke opcodes (only appear in legacy odex) ----
        # 0x6a = OP_INVOKE_SUPER_QUICK (35c, 3 units)
        # 0x6b = OP_INVOKE_VIRTUAL_QUICK_RANGE (3rc, 3 units)
        # 0x6c = OP_INVOKE_SUPER_QUICK_RANGE (3rc, 3 units)
        0x6a, 0x6b, 0x6c,
    }
    for op in three_units:
        table[op] = 3

    # ---- 5 code unit opcodes ----
    five_units = {
        0x18,  # const-wide (51l)
    }
    for op in five_units:
        table[op] = 5

    # Anything left as 0 → unknown; the scanner will treat 0 as "skip 1 unit"
    # and report a warning the first time it encounters that opcode.
    return table


OPCODE_SIZE = _build_opcode_size_table()


# Invoke-* opcode names (used to tag each edge with its invoke kind).
INVOKE_OPCODE_NAMES: Dict[int, str] = {
    0x6e: "invoke-virtual",
    0x6f: "invoke-super",
    0x70: "invoke-direct",
    0x71: "invoke-static",
    0x72: "invoke-interface",
    0x74: "invoke-virtual/range",
    0x75: "invoke-super/range",
    0x76: "invoke-direct/range",
    0x77: "invoke-static/range",
    0x78: "invoke-interface/range",
    0xfa: "invoke-polymorphic",
    0xfb: "invoke-polymorphic/range",
    0xfc: "invoke-custom",
    0xfd: "invoke-custom/range",
}

INVOKE_OPCODES = set(INVOKE_OPCODE_NAMES.keys())

# Payload pseudo-instruction markers (low byte of the first code unit).
PAYLOAD_PACKED_SWITCH = 0x0100
PAYLOAD_SPARSE_SWITCH  = 0x0200
PAYLOAD_FILL_ARRAY     = 0x0300


# ---------------------------------------------------------------------------
# DEX file parser
# ---------------------------------------------------------------------------

class DexFile:
    """Minimal lazy DEX reader. Holds the raw bytes and parses only the
    sections we need for the static call-graph scan."""

    def __init__(self, name: str, data: bytes, dex_index: int):
        self.name = name
        self.data = data
        self.dex_index = dex_index
        if len(data) < HEADER_SIZE:
            raise ValueError(f"{name}: truncated DEX (< {HEADER_SIZE} bytes)")
        h = struct.unpack(HEADER_FMT, data[:HEADER_SIZE])
        (
            self.magic,
            self.checksum,
            self.signature,
            self.file_size,
            self.header_size,
            self.endian_tag,
            self.link_size,
            self.link_off,
            self.map_off,
            self.string_ids_size,
            self.string_ids_off,
            self.type_ids_size,
            self.type_ids_off,
            self.proto_ids_size,
            self.proto_ids_off,
            self.field_ids_size,
            self.field_ids_off,
            self.method_ids_size,
            self.method_ids_off,
            self.class_defs_size,
            self.class_defs_off,
            self.data_size,
            self.data_off,
        ) = h

        # Pre-parse the lookup tables we need.
        self._strings = self._parse_string_ids()
        self._types = self._parse_type_ids()
        self._protos = self._parse_proto_ids()
        self._methods = self._parse_method_ids()  # list of (class_idx, proto_idx, name_idx)

    # ----- section readers --------------------------------------------------

    def _parse_string_ids(self) -> List[str]:
        if self.string_ids_size == 0:
            return []
        raw = self.data[self.string_ids_off:
                        self.string_ids_off + self.string_ids_size * 4]
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
        raw = self.data[self.type_ids_off:
                        self.type_ids_off + self.type_ids_size * 4]
        desc_idxs = struct.unpack(f"<{self.type_ids_size}I", raw)
        return [
            self._strings[i] if 0 <= i < len(self._strings) else "<bad-type-idx>"
            for i in desc_idxs
        ]

    def _parse_proto_ids(self) -> List[Tuple[int, int, int]]:
        if self.proto_ids_size == 0:
            return []
        raw = self.data[self.proto_ids_off:
                        self.proto_ids_off + self.proto_ids_size * 12]
        flat = struct.unpack(f"<{self.proto_ids_size * 3}I", raw)
        return [
            (flat[i], flat[i + 1], flat[i + 2])
            for i in range(0, len(flat), 3)
        ]

    def _parse_method_ids(self) -> List[Tuple[int, int, int]]:
        if self.method_ids_size == 0:
            return []
        n = self.method_ids_size
        raw = self.data[self.method_ids_off:
                        self.method_ids_off + n * 8]
        # Batch-unpack as 4 u16s per record (HHI == 2x u16 + 1x u32 ==
        # 4x u16 in memory) — a single struct.unpack call is ~100x
        # faster than unpacking each 8-byte record separately.
        flat = struct.unpack(f"<{n * 4}H", raw)
        out: List[Tuple[int, int, int]] = []
        ap = out.append
        for i in range(0, len(flat), 4):
            class_idx = flat[i]
            proto_idx = flat[i + 1]
            name_idx = flat[i + 2] | (flat[i + 3] << 16)
            ap((class_idx, proto_idx, name_idx))
        return out

    # ----- accessors --------------------------------------------------------

    def get_method_class(self, method_idx: int) -> str:
        if not (0 <= method_idx < len(self._methods)):
            return f"<bad-method-idx:{method_idx}>"
        class_idx = self._methods[method_idx][0]
        if 0 <= class_idx < len(self._types):
            return self._types[class_idx]
        return f"<bad-class-idx:{class_idx}>"

    def get_method_name(self, method_idx: int) -> str:
        if not (0 <= method_idx < len(self._methods)):
            return f"<bad-method-idx:{method_idx}>"
        name_idx = self._methods[method_idx][2]
        if 0 <= name_idx < len(self._strings):
            return self._strings[name_idx]
        return f"<bad-name-idx:{name_idx}>"

    def get_method_proto_shorty(self, method_idx: int) -> str:
        if not (0 <= method_idx < len(self._methods)):
            return "<bad-method-idx>"
        proto_idx = self._methods[method_idx][1]
        if not (0 <= proto_idx < len(self._protos)):
            return "<bad-proto-idx>"
        shorty_idx = self._protos[proto_idx][0]
        if 0 <= shorty_idx < len(self._strings):
            return self._strings[shorty_idx]
        return "<bad-shorty-idx>"

    # ----- class iteration --------------------------------------------------

    def iter_classes(self):
        """Yield (class_descriptor, class_access_flags, class_data_off) for
        every class_def in this DEX."""
        if self.class_defs_size == 0:
            return
        for i in range(self.class_defs_size):
            base = self.class_defs_off + i * 32
            chunk = self.data[base:base + 32]
            if len(chunk) < 32:
                break
            (
                class_idx,
                access_flags,
                _superclass_idx,
                _interfaces_off,
                _source_file_idx,
                _annotations_off,
                class_data_off,
                _static_values_off,
            ) = struct.unpack(CLASS_DEF_FMT, chunk)
            descriptor = (
                self._types[class_idx]
                if 0 <= class_idx < len(self._types)
                else f"<bad-class-idx:{class_idx}>"
            )
            yield descriptor, access_flags, class_data_off


# ---------------------------------------------------------------------------
# Code-item walker that scans for invoke-* instructions
# ---------------------------------------------------------------------------

class CallGraphScanner:
    """Walks every method with bytecode in every DEX file, extracts all
    invoke-* edges, and records:
      * call edges (caller_method_key → callee_method_key, invoke_kind)
      * methods declared with ACC_NATIVE flag
      * invoke-static sites that target System.loadLibrary / System.load

    Method keys are strings of the form "class_descriptor->method_name" so
    that the same logical method can be looked up across multiple DEX files.
    """

    def __init__(self, dexes: List[DexFile]):
        self.dexes = dexes

        # Global index of every method we discover (regardless of DEX).
        # methods: dict[method_key] → dict with dex_index, class, name,
        #          access_flags, is_native, callers, callees
        self.methods: Dict[str, dict] = {}

        # Per-method edges, accumulated in scan pass.
        # edges: list of dicts with caller_key, callee_key, callee_class,
        #        callee_method, invoke_kind, dex_index
        self.edges: List[dict] = []

        # Native method declarations: list of dicts
        self.native_methods: List[dict] = []

        # System.loadLibrary / System.load call sites
        self.load_library_calls: List[dict] = []

        # Index of (class_descriptor, method_name) → method_key
        # for fast callee lookup during BFS.
        # NOTE: multiple DEX files may declare the same (class, name)
        # (e.g. R.string from different APK splits) — we keep the first
        # occurrence and report duplicates as a warning.
        self._by_class_name: Dict[Tuple[str, str], str] = {}

        # Index of (dex_index, method_idx_in_dex) → method_key — needed
        # because the invoke bytecode references a per-DEX method_idx.
        self._by_dex_method_idx: Dict[Tuple[int, int], str] = {}

        # Statistics
        self.stats = {
            "total_dex_files": 0,
            "total_class_defs": 0,
            "total_methods_with_bytecode": 0,
            "total_native_methods": 0,
            "total_invoke_sites": 0,
            "total_edges": 0,
            "scan_duration_sec": 0.0,
            "scan_errors": 0,
        }

        self._scan_errors: List[str] = []

    # ------------------------------------------------------------------ index

    def _make_method_key(self, class_desc: str, method_name: str) -> str:
        return f"{class_desc}->{method_name}"

    def _register_method(self, dex_index: int, class_desc: str,
                         method_name: str, method_idx_in_dex: int,
                         access_flags: int) -> str:
        """Insert into the global methods index (idempotent). Returns the
        canonical method_key."""
        key = self._make_method_key(class_desc, method_name)
        if key not in self.methods:
            self.methods[key] = {
                "key": key,
                "class": class_desc,
                "name": method_name,
                "dex_index": dex_index,
                "method_idx_in_dex": method_idx_in_dex,
                "access_flags": access_flags,
                "is_native": bool(access_flags & ACC_NATIVE),
                "is_static": bool(access_flags & ACC_STATIC),
                "callers": [],
                "callees": [],
            }
        else:
            # Already registered (e.g. virtual + direct entry overlap) —
            # OR extra occurrence in another DEX file.
            existing = self.methods[key]
            if not existing.get("is_native") and (access_flags & ACC_NATIVE):
                existing["is_native"] = True
                existing["access_flags"] = access_flags
            if (existing.get("dex_index") == dex_index and
                    existing.get("method_idx_in_dex") != method_idx_in_dex):
                # Different method_idx in same DEX for same key — unusual,
                # leave the first one as canonical.
                pass

        # Update per-DEX method_idx lookup (only first occurrence wins
        # to avoid confusion when multiple classes share a method name).
        idx_key = (dex_index, method_idx_in_dex)
        if idx_key not in self._by_dex_method_idx:
            self._by_dex_method_idx[idx_key] = key

        cn_key = (class_desc, method_name)
        if cn_key not in self._by_class_name:
            self._by_class_name[cn_key] = key

        return key

    # ------------------------------------------------------------------- scan

    def scan(self) -> None:
        t0 = time.time()
        self.stats["total_dex_files"] = len(self.dexes)

        # PASS 1 — register every method (incl. native + abstract) so
        # the global index is complete before we start emitting edges.
        for dex_index, dex in enumerate(self.dexes):
            classes_done = 0
            for class_desc, class_access, class_data_off in dex.iter_classes():
                self.stats["total_class_defs"] += 1
                if class_data_off == 0:
                    classes_done += 1
                    continue
                self._register_methods_in_class(
                    dex, dex_index, class_desc, class_data_off
                )
                classes_done += 1
            _log(
                f"    [pass1] dex={dex.name} classes={classes_done:,} "
                f"native_total={len(self.native_methods):,} "
                f"methods_total={len(self.methods):,}"
            )

        # PASS 2 — for every method that has bytecode, walk the insns[]
        # array and extract invoke-* edges.
        for dex_index, dex in enumerate(self.dexes):
            t_dex = time.time()
            edges_before = len(self.edges)
            for class_desc, _class_access, class_data_off in dex.iter_classes():
                if class_data_off == 0:
                    continue
                self._scan_class_bytecode(
                    dex, dex_index, class_desc, class_data_off
                )
            _log(
                f"    [pass2] dex={dex.name} "
                f"edges_added={len(self.edges) - edges_before:,} "
                f"in {time.time() - t_dex:.1f}s "
                f"invoke_sites={self.stats['total_invoke_sites']:,}"
            )

        self.stats["scan_duration_sec"] = round(time.time() - t0, 3)
        self.stats["total_edges"] = len(self.edges)
        self.stats["total_native_methods"] = len(self.native_methods)
        self.stats["scan_errors"] = len(self._scan_errors)

        # Build per-method callers/callees lists from the edge list.
        for edge in self.edges:
            callee_key = edge["callee_key"]
            caller_key = edge["caller_key"]
            if callee_key not in self.methods:
                # Callee is external (framework or method we didn't
                # register) — create a stub entry so the graph is complete.
                self.methods[callee_key] = {
                    "key": callee_key,
                    "class": edge["callee_class"],
                    "name": edge["callee_method"],
                    "dex_index": -1,
                    "method_idx_in_dex": -1,
                    "access_flags": 0,
                    "is_native": False,
                    "is_static": False,
                    "callers": [],
                    "callees": [],
                    "external": True,
                }
            if caller_key not in self.methods:
                # Shouldn't normally happen, but be defensive.
                self.methods[caller_key] = {
                    "key": caller_key,
                    "class": edge["caller_class"],
                    "name": edge["caller_method"],
                    "dex_index": -1,
                    "method_idx_in_dex": -1,
                    "access_flags": 0,
                    "is_native": False,
                    "is_static": False,
                    "callers": [],
                    "callees": [],
                    "external": True,
                }
            self.methods[caller_key]["callees"].append(callee_key)
            self.methods[callee_key]["callers"].append(caller_key)

    # ---- Pass 1 helpers ----

    def _register_methods_in_class(self, dex: DexFile, dex_index: int,
                                    class_desc: str, class_data_off: int) -> None:
        data = dex.data
        off = class_data_off
        try:
            static_fields_size, off = read_uleb128(data, off)
            instance_fields_size, off = read_uleb128(data, off)
            direct_methods_size, off = read_uleb128(data, off)
            virtual_methods_size, off = read_uleb128(data, off)

            # Skip static_fields[] and instance_fields[]
            for _ in range(static_fields_size + instance_fields_size):
                _fidx, off = read_uleb128(data, off)
                _aflg, off = read_uleb128(data, off)

            # Walk direct_methods[] then virtual_methods[]
            prev_idx = 0
            for _ in range(direct_methods_size):
                idx_diff, off = read_uleb128(data, off)
                access_flags, off = read_uleb128(data, off)
                _code_off, off = read_uleb128(data, off)  # u32 — NOT uleb128
                method_idx = prev_idx + idx_diff
                prev_idx = method_idx
                method_name = dex.get_method_name(method_idx)
                self._register_method(
                    dex_index, class_desc, method_name,
                    method_idx, access_flags
                )
                if access_flags & ACC_NATIVE:
                    self.native_methods.append({
                        "class": class_desc,
                        "method": method_name,
                        "access_flags": access_flags,
                        "dex_index": dex_index,
                        "method_idx_in_dex": method_idx,
                        "kind": "direct",
                        "shorty": dex.get_method_proto_shorty(method_idx),
                    })

            prev_idx = 0
            for _ in range(virtual_methods_size):
                idx_diff, off = read_uleb128(data, off)
                access_flags, off = read_uleb128(data, off)
                _code_off, off = read_uleb128(data, off)
                method_idx = prev_idx + idx_diff
                prev_idx = method_idx
                method_name = dex.get_method_name(method_idx)
                self._register_method(
                    dex_index, class_desc, method_name,
                    method_idx, access_flags
                )
                if access_flags & ACC_NATIVE:
                    self.native_methods.append({
                        "class": class_desc,
                        "method": method_name,
                        "access_flags": access_flags,
                        "dex_index": dex_index,
                        "method_idx_in_dex": method_idx,
                        "kind": "virtual",
                        "shorty": dex.get_method_proto_shorty(method_idx),
                    })

        except Exception as exc:
            self._scan_errors.append(
                f"dex={dex.name} class={class_desc} register error: {exc!r}"
            )

    # ---- Pass 2 helpers ----

    def _scan_class_bytecode(self, dex: DexFile, dex_index: int,
                              class_desc: str, class_data_off: int) -> None:
        data = dex.data
        off = class_data_off
        try:
            static_fields_size, off = read_uleb128(data, off)
            instance_fields_size, off = read_uleb128(data, off)
            direct_methods_size, off = read_uleb128(data, off)
            virtual_methods_size, off = read_uleb128(data, off)

            for _ in range(static_fields_size + instance_fields_size):
                _fidx, off = read_uleb128(data, off)
                _aflg, off = read_uleb128(data, off)

            prev_idx = 0
            for _ in range(direct_methods_size):
                idx_diff, off = read_uleb128(data, off)
                access_flags, off = read_uleb128(data, off)
                code_off, off = read_uleb128(data, off)
                method_idx = prev_idx + idx_diff
                prev_idx = method_idx
                if code_off != 0 and not (access_flags & ACC_NATIVE) \
                        and not (access_flags & ACC_ABSTRACT):
                    method_name = dex.get_method_name(method_idx)
                    self._scan_method_bytecode(
                        dex, dex_index, class_desc, method_name,
                        method_idx, code_off
                    )

            prev_idx = 0
            for _ in range(virtual_methods_size):
                idx_diff, off = read_uleb128(data, off)
                access_flags, off = read_uleb128(data, off)
                code_off, off = read_uleb128(data, off)
                method_idx = prev_idx + idx_diff
                prev_idx = method_idx
                if code_off != 0 and not (access_flags & ACC_NATIVE) \
                        and not (access_flags & ACC_ABSTRACT):
                    method_name = dex.get_method_name(method_idx)
                    self._scan_method_bytecode(
                        dex, dex_index, class_desc, method_name,
                        method_idx, code_off
                    )

        except Exception as exc:
            self._scan_errors.append(
                f"dex={dex.name} class={class_desc} scan error: {exc!r}"
            )

    def _scan_method_bytecode(self, dex: DexFile, dex_index: int,
                              class_desc: str, method_name: str,
                              method_idx_in_dex: int, code_off: int) -> None:
        """Walk the insns[] array of one code_item and emit invoke-* edges."""
        data = dex.data
        # code_item layout: 2x u16 (registers_size, ins_size) +
        # 2x u16 (outs_size, tries_size) + u32 debug_info_off + u32 insns_size
        # + insns[insns_size] (each is u16)
        if code_off == 0 or code_off + 16 > len(data):
            return
        try:
            (registers_size, ins_size, outs_size, tries_size,
             debug_info_off, insns_size) = struct.unpack_from(
                "<HHHHII", data, code_off
            )
        except Exception as exc:
            self._scan_errors.append(
                f"dex={dex.name} class={class_desc} method={method_name} "
                f"code_item header read failed: {exc!r}"
            )
            return

        insns_off = code_off + 16
        insns_byte_count = insns_size * 2  # each code unit = 2 bytes
        if insns_off + insns_byte_count > len(data):
            self._scan_errors.append(
                f"dex={dex.name} class={class_desc} method={method_name} "
                f"insns[] out of bounds (insns_size={insns_size})"
            )
            return

        # Unpack every 16-bit code unit of insns[] into a u16 array.
        # struct.unpack with format '<{n}H' is dramatically faster than
        # walking bytes two at a time.
        try:
            units = struct.unpack_from(f"<{insns_size}H", data, insns_off)
        except Exception as exc:
            self._scan_errors.append(
                f"dex={dex.name} class={class_desc} method={method_name} "
                f"insns[] unpack failed: {exc!r}"
            )
            return

        caller_key = self._make_method_key(class_desc, method_name)
        self.stats["total_methods_with_bytecode"] += 1

        pc = 0
        units_n = len(units)
        while pc < units_n:
            unit = units[pc]
            opcode = unit & 0xFF

            # Detect payload pseudo-instructions. The first code unit's
            # high byte holds the marker 0x01/0x02/0x03 and the layout is
            # documented in dalvik/libdex/DexFile.h (PseudoOp enum).
            high_byte = (unit >> 8) & 0xFF
            if opcode == 0x00 and high_byte in (0x01, 0x02, 0x03):
                # Skip the payload.
                payload_size_units = self._payload_size_units(units, pc, high_byte)
                if payload_size_units <= 0:
                    pc += 1  # bail — pretend it's a 1-unit nop
                    continue
                pc += payload_size_units
                continue

            if opcode in INVOKE_OPCODES:
                self._record_invoke_edge(
                    dex, dex_index, caller_key, class_desc, method_name,
                    opcode, units, pc
                )
                self.stats["total_invoke_sites"] += 1
                # All invoke opcodes are 3 code units long (35c / 3rc /
                # 45c / 4rc formats all occupy 3 code units — even the
                # invoke-polymorphic family which has an extra proto_idx).
                pc += 3
                continue

            size = OPCODE_SIZE[opcode]
            if size == 0:
                # Unknown opcode — bump by 1 and log once per opcode.
                self._scan_errors.append(
                    f"dex={dex.name} class={class_desc} method={method_name} "
                    f"unknown opcode 0x{opcode:02x} at pc={pc}"
                )
                pc += 1
                continue
            pc += size

    # ---------------------------------------------------------------- helpers

    def _payload_size_units(self, units, pc: int, marker_hi: int) -> int:
        """Return the size (in code units) of a payload pseudo-instruction
        starting at pc. markers: 0x01=packed-switch, 0x02=sparse-switch,
        0x03=fill-array-data. Returns 0 if the payload can't be parsed."""
        n = len(units)
        if marker_hi == 0x01:
            # packed-switch-payload:
            #   u16 ident (already consumed conceptually — units[pc])
            #   u16 size
            #   int32 first_key
            #   int32[size] targets
            if pc + 3 >= n:
                return 0
            size = units[pc + 1]
            return 2 + 2 + size * 2  # 1 (ident) + 1 (size) + 2 (first_key) + 2*size
        if marker_hi == 0x02:
            # sparse-switch-payload:
            #   u16 ident
            #   u16 size
            #   int32[size] keys
            #   int32[size] targets
            if pc + 1 >= n:
                return 0
            size = units[pc + 1]
            return 2 + 4 * size  # 1 + 1 + 2*size + 2*size
        if marker_hi == 0x03:
            # fill-array-data-payload:
            #   u16 ident
            #   u16 element_width
            #   u32 size
            #   u8[size * element_width]  (padded to 4-byte boundary)
            if pc + 3 >= n:
                return 0
            element_width = units[pc + 1]
            size = units[pc + 2] | (units[pc + 3] << 16)
            data_bytes = size * element_width
            # Round up to 4-byte boundary; then convert to code units.
            data_units = (data_bytes + 1) // 2
            # Round up to even number of code units (4-byte alignment).
            if data_units & 1:
                data_units += 1
            return 2 + 2 + data_units  # ident + header + data
        return 0

    def _record_invoke_edge(self, dex: DexFile, dex_index: int,
                             caller_key: str, caller_class: str,
                             caller_method: str, opcode: int, units, pc: int) -> None:
        """Decode the method_idx field of an invoke-* instruction and
        record the call edge."""
        # All invoke variants (35c, 3rc, 45c, 4rc) place the method_idx
        # in the second code unit of the instruction. (For the polymorphic
        # variants, the third code unit is the proto_idx, which we don't
        # need for the static call graph.)
        if pc + 1 >= len(units):
            return
        method_idx = units[pc + 1]
        callee_class = dex.get_method_class(method_idx)
        callee_method = dex.get_method_name(method_idx)
        callee_key = self._make_method_key(callee_class, callee_method)
        invoke_kind = INVOKE_OPCODE_NAMES[opcode]

        edge = {
            "caller_key": caller_key,
            "caller_class": caller_class,
            "caller_method": caller_method,
            "callee_key": callee_key,
            "callee_class": callee_class,
            "callee_method": callee_method,
            "invoke_kind": invoke_kind,
            "opcode": f"0x{opcode:02x}",
            "dex_index": dex_index,
            "method_idx_in_dex": method_idx,
            "caller_pc": pc,
        }
        self.edges.append(edge)

        # Detect System.loadLibrary / System.load call sites.
        if invoke_kind == "invoke-static" \
                and callee_class == "Ljava/lang/System;" \
                and callee_method in ("loadLibrary", "load"):
            self.load_library_calls.append({
                "caller_key": caller_key,
                "caller_class": caller_class,
                "caller_method": caller_method,
                "callee_method": callee_method,
                "dex_index": dex_index,
                "caller_pc": pc,
            })


# ---------------------------------------------------------------------------
# Startup path BFS
# ---------------------------------------------------------------------------

def find_startup_path(scanner: CallGraphScanner,
                      entry_class: str,
                      entry_method: str,
                      max_depth: int = 8,
                      max_methods: int = 4000) -> dict:
    """Breadth-first traversal of the call graph from the given entry
    method, recording every method visited (with its BFS depth) and the
    edges traversed. Depth and total-visit caps keep the JSON output
    manageable even if the entry point fans out into hundreds of
    thousands of framework callbacks."""

    entry_key = scanner._make_method_key(entry_class, entry_method)
    if entry_key not in scanner.methods:
        # Try a more forgiving lookup: search by class substring.
        candidates = [
            (k, m) for k, m in scanner.methods.items()
            if m["name"] == entry_method and entry_class in m["class"]
        ]
        if not candidates:
            return {
                "entry_key": entry_key,
                "entry_class": entry_class,
                "entry_method": entry_method,
                "found": False,
                "error": f"Entry method {entry_key} not found in any DEX",
                "visited_methods": [],
                "edges_on_path": [],
                "max_depth_reached": 0,
            }
        entry_key = candidates[0][0]

    # Pre-build a per-caller index of edges so the BFS doesn't have to
    # linearly scan all ~1M edges for every callee lookup.
    _log("    [bfs] building per-caller edge index...")
    edges_by_caller: Dict[str, List[dict]] = defaultdict(list)
    for edge in scanner.edges:
        edges_by_caller[edge["caller_key"]].append(edge)
    _log(
        f"    [bfs] edge index built: "
        f"{len(edges_by_caller):,} unique callers indexed"
    )

    visited: Dict[str, int] = {entry_key: 0}
    visited_order: List[str] = [entry_key]
    edges_on_path: List[dict] = []
    queue: deque = deque([(entry_key, 0)])
    max_depth_reached = 0

    # Restrict the BFS to "interesting" callees to keep the output
    # focused. Framework classes that are stubbed or only contribute
    # boilerplate (e.g. Ljava/lang/*, Landroid/*) are still walked for
    # one level but we don't recurse past them — that would balloon
    # the output to the entire Android SDK.
    def _should_recurse(callee_key: str, depth: int) -> bool:
        if depth >= max_depth:
            return False
        if callee_key in visited:
            return False
        m = scanner.methods.get(callee_key)
        if m is None:
            return False
        # Skip external framework classes once we're past depth 2.
        cls = m["class"]
        if depth >= 2 and (
            cls.startswith("Ljava/") or
            cls.startswith("Landroid/") or
            cls.startswith("Lkotlin/") or
            cls.startswith("Lkotlinx/") or
            cls.startswith("Lcom/google/")
        ):
            # Still record the edge but don't recurse.
            return False
        return True

    while queue:
        cur_key, depth = queue.popleft()
        if depth > max_depth_reached:
            max_depth_reached = depth
        if depth >= max_depth:
            continue
        if len(visited) >= max_methods:
            break
        cur_method = scanner.methods.get(cur_key)
        if cur_method is None:
            continue
        for edge in edges_by_caller.get(cur_key, []):
            callee_key = edge["callee_key"]
            edges_on_path.append({
                "depth": depth,
                "caller_key": cur_key,
                "caller_class": cur_method["class"],
                "caller_method": cur_method["name"],
                "callee_key": callee_key,
                "callee_class": edge["callee_class"],
                "callee_method": edge["callee_method"],
                "invoke_kind": edge["invoke_kind"],
            })
            if _should_recurse(callee_key, depth + 1):
                visited[callee_key] = depth + 1
                visited_order.append(callee_key)
                queue.append((callee_key, depth + 1))

    visited_methods = [
        {
            "key": k,
            "class": scanner.methods[k]["class"] if k in scanner.methods else k,
            "method": scanner.methods[k]["name"] if k in scanner.methods else "<unknown>",
            "depth": d,
            "is_native": scanner.methods[k].get("is_native", False) if k in scanner.methods else False,
        }
        for k, d in sorted(visited.items(), key=lambda kv: (kv[1], kv[0]))
    ]

    # Native method call sites reachable on the startup path.
    native_on_startup = [
        {
            "class": vm["class"],
            "method": vm["method"],
            "depth": vm["depth"],
            "key": vm["key"],
        }
        for vm in visited_methods if vm["is_native"]
    ]

    return {
        "entry_key": entry_key,
        "entry_class": entry_class,
        "entry_method": entry_method,
        "found": True,
        "max_depth_reached": max_depth_reached,
        "visited_count": len(visited),
        "edge_count_on_path": len(edges_on_path),
        "visited_methods": visited_methods,
        "edges_on_path": edges_on_path,
        "native_methods_on_path": native_on_startup,
    }


# ---------------------------------------------------------------------------
# Top-level entry point
# ---------------------------------------------------------------------------

def load_dexes() -> List[DexFile]:
    _log(f"[+] Opening APK: {APK_PATH}")
    if not os.path.exists(APK_PATH):
        raise FileNotFoundError(f"APK not found at {APK_PATH}")
    dexes: List[DexFile] = []
    with zipfile.ZipFile(APK_PATH) as z:
        for i, name in enumerate(DEX_FILES):
            try:
                raw = z.read(name)
            except KeyError:
                _log(f"[!] {name} not present in APK — skipping")
                continue
            _log(f"[+] Loaded {name} ({len(raw):,} bytes)")
            t0 = time.time()
            dexes.append(DexFile(name, raw, dex_index=i))
            _log(
                f"    parsed in {time.time() - t0:.2f}s "
                f"(strings={dexes[-1].string_ids_size:,}, "
                f"methods={dexes[-1].method_ids_size:,}, "
                f"classes={dexes[-1].class_defs_size:,})"
            )
    return dexes


def main() -> int:
    os.makedirs(REPORT_DIR, exist_ok=True)

    dexes = load_dexes()
    if not dexes:
        print("[!] No DEX files found — aborting.", file=sys.stderr)
        return 1

    _log(f"[+] Parsing {len(dexes)} DEX file(s)...")
    scanner = CallGraphScanner(dexes)
    _log("[+] Scanning bytecode for invoke-* call edges...")
    scanner.scan()

    _log(
        f"[+] Scan complete in {scanner.stats['scan_duration_sec']}s "
        f"— {scanner.stats['total_methods_with_bytecode']:,} methods with bytecode, "
        f"{scanner.stats['total_invoke_sites']:,} invoke sites, "
        f"{scanner.stats['total_edges']:,} edges, "
        f"{scanner.stats['total_native_methods']:,} native methods"
    )
    if scanner._scan_errors:
        _log(
            f"[!] {len(scanner._scan_errors)} scan errors — first 5 shown in "
            f"report under `scan_errors`."
        )

    _log("[+] Building startup path from LaunchActivity.onCreate...")
    startup = find_startup_path(
        scanner,
        entry_class="Lorg/telegram/ui/LaunchActivity;",
        entry_method="onCreate",
        max_depth=8,
        max_methods=4000,
    )
    if startup["found"]:
        _log(
            f"[+] Startup path: depth={startup['max_depth_reached']}, "
            f"visited={startup['visited_count']}, "
            f"edges_on_path={startup['edge_count_on_path']}, "
            f"native_on_path={len(startup['native_methods_on_path'])}"
        )
    else:
        _log(f"[!] Startup entry not found: {startup.get('error')}")

    # Assemble the final report. Per the task spec ("Focus on the
    # STARTUP PATH — methods reachable from LaunchActivity.onCreate.
    # Don't dump all 253K methods; trace from the entry point"), the
    # `methods` field is just a compact index of all discovered methods
    # (class, name, dex_index, flags, caller/callee COUNTS) without
    # the per-method caller/callee lists — those would push the JSON
    # past 1 GB and aren't useful without filtering.
    #
    # For the startup path we DO include the full per-method callers/
    # callees lists, since those are limited to a few thousand methods
    # and are the actual interesting signal for downstream analysis.
    methods_compact = []
    for key, m in scanner.methods.items():
        methods_compact.append({
            "k": key,
            "c": m["class"],
            "m": m["name"],
            "d": m["dex_index"],
            "f": m["access_flags"],
            "n": m["is_native"],
            "s": m["is_static"],
            "x": m.get("external", False),
            "in": len(m["callers"]),
            "out": len(m["callees"]),
        })

    # For the startup path, also enrich the visited methods with their
    # per-method callers/callees lists (these are limited to the
    # methods reachable from LaunchActivity.onCreate, so they fit
    # comfortably in the JSON).
    startup_visited_keys = {
        vm["key"] for vm in startup.get("visited_methods", [])
    }
    startup_method_details = []
    for key in startup_visited_keys:
        m = scanner.methods.get(key)
        if m is None:
            continue
        startup_method_details.append({
            "key": key,
            "class": m["class"],
            "method": m["name"],
            "dex_index": m["dex_index"],
            "access_flags": m["access_flags"],
            "is_native": m["is_native"],
            "is_static": m["is_static"],
            "callers": sorted(set(m["callers"])),
            "callees": sorted(set(m["callees"])),
        })

    # `methods` is a compact global index; `methods_on_startup_path`
    # is the per-method callers/callees view restricted to the startup
    # path (per task spec: "Focus on the STARTUP PATH — methods
    # reachable from LaunchActivity.onCreate. Don't dump all 253K
    # methods; trace from the entry point.").
    report = {
        "experiment": "EXP-049-PHASE2-3",
        "apk_path": APK_PATH,
        "dex_files": [d.name for d in dexes],
        "dex_stats": [
            {
                "name": d.name,
                "dex_index": d.dex_index,
                "method_ids_size": d.method_ids_size,
                "class_defs_size": d.class_defs_size,
                "string_ids_size": d.string_ids_size,
                "type_ids_size": d.type_ids_size,
                "proto_ids_size": d.proto_ids_size,
            }
            for d in dexes
        ],
        "scanner_stats": scanner.stats,
        "scan_errors_total": len(scanner._scan_errors),
        "scan_errors_sample": scanner._scan_errors[:50],
        # Compact index of ALL methods discovered (217K+ entries).
        # Each entry is ~80 bytes; the per-method callers/callees
        # lists are NOT included here (they'd balloon to 1 GB+).
        # Use `methods_on_startup_path` for the per-method callers/
        # callees view of the startup-reachable subset.
        "methods": methods_compact,
        "methods_count": len(methods_compact),
        "methods_on_startup_path": startup_method_details,
        "methods_on_startup_path_count": len(startup_method_details),
        "native_calls": scanner.native_methods,
        "native_calls_count": len(scanner.native_methods),
        "load_library_calls": scanner.load_library_calls,
        "load_library_calls_count": len(scanner.load_library_calls),
        "startup_path": startup,
    }

    # Compact JSON (no indentation) for the big sections to keep file
    # size manageable. Indented JSON for the small sections would be
    # nicer but takes 3-5x more space.
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, separators=(",", ":"))
    _log(f"[+] Wrote report: {REPORT_PATH}")
    _log(
        f"[+] Report size: {os.path.getsize(REPORT_PATH):,} bytes"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
