#!/usr/bin/env python3
"""
EXP-052: Exception Handling Validation Suite
=============================================

Generates minimal DEX test files that exercise the interpreter's behavior
around throw / try / catch.

Test scenarios
--------------
  Case 1: Exception without catch
    Method throws, no try table. Expected: exception propagates to caller
    (in our runtime: method-level halt, caller continues).

  Case 2: Exception with local catch
    Method throws inside try{}; matching catch handler exists. Expected:
    execution jumps to handler, method continues normally, returns 0.

  Case 3: Nested call with caller catch
    A() calls B(); B() throws; A() has try/catch. Expected: stack unwinds
    from B to A, A's handler runs, A returns "caught".

  Case 4: Catch-all handler
    Method throws RuntimeException inside try; catch(Throwable) handler.
    Expected: catch-all matches, handler runs.

  Case 5 (regression): Throw in D8 unreachable block
    Method has `goto +0` after a throw-builder block (D8 unreachable marker).
    Expected: throw fires first; method-level halt; caller continues.

Outputs
-------
  * test_apks/exp052/<case>.dex         — raw DEX for inspection
  * test_apks/exp052/<case>.apk        — APK wrapping the DEX
  * run/exp052_exceptions/<case>/run.log — captured runtime output

This script is RESEARCH-ONLY: it does NOT modify C++ source.
"""

from __future__ import annotations

import io
import os
import struct
import subprocess
import sys
import time
import zipfile
import zlib
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

# ============================================================================
# Minimal DEX builder — enough for our test cases.
# Each test is a single class with a single method `run()I`.
# ============================================================================

class DexBuilder:
    """Builds a minimal DEX file with one class and one method."""

    def __init__(self):
        self.strings: List[str] = []
        self.string_data: Dict[int, bytes] = {}  # idx -> mutf-8 bytes
        self.type_ids: List[int] = []  # type_ids[i] = string_idx of descriptor
        self.proto_ids: List[Tuple[int, int]] = []  # (shorty_idx, return_type_idx)
        self.field_ids: List[Tuple[int, int, int]] = []  # (class_idx, type_idx, name_idx)
        self.method_ids: List[Tuple[int, int, int]] = []  # (class_idx, proto_idx, name_idx)
        self.class_defs: List[dict] = []
        self._string_cache: Dict[str, int] = {}

    # ---- strings ----
    def add_string(self, s: str) -> int:
        if s in self._string_cache:
            return self._string_cache[s]
        idx = len(self.strings)
        self.strings.append(s)
        # MUTF-8 encoding: uleb128 length + utf-8 bytes + \0
        encoded = s.encode("utf-8")
        # uleb128 of length
        length = len(encoded)
        uleb = bytearray()
        while True:
            b = length & 0x7F
            length >>= 7
            if length:
                uleb.append(b | 0x80)
            else:
                uleb.append(b)
                break
        self.string_data[idx] = bytes(uleb) + encoded + b"\x00"
        self._string_cache[s] = idx
        return idx

    def add_type(self, descriptor: str) -> int:
        sid = self.add_string(descriptor)
        for i, t in enumerate(self.type_ids):
            if t == sid:
                return i
        idx = len(self.type_ids)
        self.type_ids.append(sid)
        return idx

    def add_proto(self, shorty: str, return_type: str) -> int:
        sid = self.add_string(shorty)
        rid = self.add_type(return_type)
        for i, (s, r) in enumerate(self.proto_ids):
            if s == sid and r == rid:
                return i
        idx = len(self.proto_ids)
        self.proto_ids.append((sid, rid))
        return idx

    def add_method(self, class_desc: str, shorty: str, return_type: str, name: str) -> int:
        cid = self.add_type(class_desc)
        pid = self.add_proto(shorty, return_type)
        nid = self.add_string(name)
        for i, (c, p, n) in enumerate(self.method_ids):
            if c == cid and p == pid and n == nid:
                return i
        idx = len(self.method_ids)
        self.method_ids.append((cid, pid, nid))
        return idx

    def add_class(self, desc: str, superclass: str = "Ljava/lang/Object;",
                  access: int = 1) -> int:
        # access=1 PUBLIC
        cid = self.add_type(desc)
        sc = self.add_type(superclass)
        # We'll fill in class_data later via set_class_data
        idx = len(self.class_defs)
        self.class_defs.append({
            "class_idx": cid,
            "access_flags": access,
            "superclass_idx": sc,
            "interfaces_off": 0,
            "source_file_idx": 0xFFFFFFFF,
            "annotations_off": 0,
            "class_data_off": 0,  # filled in at serialize
            "static_values_off": 0,
            "class_data": None,
        })
        return idx

    def set_class_data(self, class_idx: int, direct_methods: list, virtual_methods: list = None):
        """direct_methods is a list of dicts:
            {name, shorty, return_type, access, bytecode: List[int],
             tries: Optional[List[dict]]}
        """
        cd = self.class_defs[class_idx]
        cid = cd["class_idx"]
        # Add method_ids for each
        for m in direct_methods:
            mid = self.add_method(self.strings[self.type_ids[cid]],
                                  m["shorty"], m["return_type"], m["name"])
            m["method_idx"] = mid
        cd["class_data"] = {"direct_methods": direct_methods,
                            "virtual_methods": virtual_methods or [],
                            "static_fields": [],
                            "instance_fields": []}

    # ---- serialization ----
    def serialize(self) -> bytes:
        # Layout:
        # 0x00 header (112 bytes)
        # string_ids   (string_ids_size * 4 bytes)
        # type_ids     (type_ids_size * 4 bytes)
        # proto_ids    (proto_ids_size * 12 bytes)
        # field_ids    (field_ids_size * 8 bytes)
        # method_ids   (method_ids_size * 8 bytes)
        # class_defs   (class_defs_size * 32 bytes)
        # data section (string_data + class_data_items + code_items)
        string_ids_size = len(self.strings)
        type_ids_size = len(self.type_ids)
        proto_ids_size = len(self.proto_ids)
        field_ids_size = 0  # we don't generate fields
        method_ids_size = len(self.method_ids)
        class_defs_size = len(self.class_defs)

        # Compute offsets
        offset = DEX_HEADER_SIZE
        string_ids_off = offset; offset += string_ids_size * 4
        type_ids_off = offset; offset += type_ids_size * 4
        proto_ids_off = offset; offset += proto_ids_size * 12
        field_ids_off = offset; offset += field_ids_size * 8
        method_ids_off = offset; offset += method_ids_size * 8
        class_defs_off = offset; offset += class_defs_size * 32
        data_off = offset

        # Now lay out the data section.
        # String data first.
        string_data_off = offset
        string_data_bytes = bytearray()
        string_data_offsets = []
        for i in range(string_ids_size):
            string_data_offsets.append(string_data_off + len(string_data_bytes))
            string_data_bytes.extend(self.string_data[i])

        offset = string_data_off + len(string_data_bytes)
        # Align to 4
        while offset % 4 != 0:
            string_data_bytes.append(0)
            offset += 1

        # Class data items + code items per class
        class_data_offsets = []
        code_items: List[Tuple[int, bytes]] = []  # (offset, bytes)

        # We'll write class_data + code_item for each class
        for cd in self.class_defs:
            class_data_offsets.append(offset)
            data = cd["class_data"]
            if data is None:
                continue
            # Build class_data_item: uleb128 sizes, then field/method lists
            cd_bytes = bytearray()
            def uleb(v):
                while True:
                    b = v & 0x7F
                    v >>= 7
                    if v:
                        cd_bytes.append(b | 0x80)
                    else:
                        cd_bytes.append(b)
                        break
            uleb(len(data["static_fields"]))
            uleb(len(data["instance_fields"]))
            uleb(len(data["direct_methods"]))
            uleb(len(data["virtual_methods"]))
            # Static fields (none)
            # Instance fields (none)
            # Direct methods
            prev_method_idx = 0
            for m in data["direct_methods"]:
                diff = m["method_idx"] - prev_method_idx
                uleb(diff)
                prev_method_idx = m["method_idx"]
                uleb(m["access"])
                # code_off — we'll patch this in later
                uleb(0)  # placeholder
                m["_cd_byte_pos"] = len(cd_bytes)  # to patch later
            # Virtual methods (none)
            # Append to data section
            # We need to patch the code_off after we know where to put the code_item
            class_data_size = len(cd_bytes)
            offset += class_data_size
            # Align to 4
            while offset % 4 != 0:
                cd_bytes.append(0)
                offset += 1

            # Now write each method's code_item
            for m in data["direct_methods"]:
                code_off = offset
                m["code_off"] = code_off
                # Build code_item: registers_size, ins_size, outs_size, tries_size,
                # debug_info_off, insns_size, insns[], [padding], [tries[]],
                # [encoded_catch_handler_list]
                bc = m["bytecode"]
                tries = m.get("tries", [])
                tries_size = len(tries)
                code_bytes = bytearray()
                # code_item header
                code_bytes += struct.pack("<HHHHI",
                                          m.get("registers_size", 4),
                                          m.get("ins_size", 0),
                                          m.get("outs_size", 2),
                                          tries_size,
                                          0)  # debug_info_off
                code_bytes += struct.pack("<I", len(bc))
                # insns
                for cu in bc:
                    code_bytes += struct.pack("<H", cu)
                # padding
                if len(bc) % 2 != 0:
                    code_bytes += b"\x00\x00"  # 2 bytes padding
                # tries[] + encoded_catch_handler_list
                if tries_size > 0:
                    # tries[]: 8 bytes each
                    for t in tries:
                        code_bytes += struct.pack("<IHH",
                                                  t["start_addr"],
                                                  t["insn_count"],
                                                  t["handler_off"])
                    # encoded_catch_handler_list: uleb128 size, then handlers
                    # For our tests, we always have 1 handler
                    code_bytes += _uleb128(1)  # list_size=1
                    # handler at offset 1 (relative to start of handler list, after size byte)
                    # Each handler: sleb128 size, then pairs
                    for h in tries:
                        # h["handlers"] is a list of (type_descriptor, addr) pairs
                        # If type_descriptor is None, it's a catch-all
                        pairs = h["handlers"]
                        n_pairs = len([p for p in pairs if p[0] is not None])
                        has_catch_all = any(p[0] is None for p in pairs)
                        if has_catch_all:
                            size_sleb = -(n_pairs + 1)
                        else:
                            size_sleb = n_pairs
                        code_bytes += _sleb128(size_sleb)
                        for type_desc, addr in pairs:
                            if type_desc is not None:
                                type_idx = self.add_type(type_desc)
                                code_bytes += _uleb128(type_idx)
                                code_bytes += _uleb128(addr)
                        if has_catch_all:
                            # Find catch-all addr
                            for type_desc, addr in pairs:
                                if type_desc is None:
                                    code_bytes += _uleb128(addr)
                                    break
                    # Pad to 4-byte alignment
                    while len(code_bytes) % 4 != 0:
                        code_bytes.append(0)

                # Patch code_off in class_data_item
                # The class_data was already written, but we need to go back and patch.
                # For simplicity, regenerate class_data with correct code_off values.
                # Actually, the class_data has uleb128 code_off=0 placeholder.
                # We need to rebuild cd_bytes with the actual code_off values.
                # Let's regenerate cd_bytes now that we know code_off.
                pass  # We'll regenerate the whole class_data section below

                code_items.append((code_off, bytes(code_bytes)))
                offset += len(code_bytes)
                while offset % 4 != 0:
                    offset += 1

        # Regenerate class_data with correct code_off values
        # For simplicity, rewrite the whole data section
        # Recompute data section offsets from scratch
        offset = string_data_off + len(string_data_bytes)
        # Align
        while offset % 4 != 0:
            offset += 1

        new_class_data_offsets = []
        new_code_items = []
        for cd_idx, cd in enumerate(self.class_defs):
            new_class_data_offsets.append(offset)
            data = cd["class_data"]
            if data is None:
                continue
            cd_bytes = bytearray()
            def uleb(v):
                while True:
                    b = v & 0x7F
                    v >>= 7
                    if v:
                        cd_bytes.append(b | 0x80)
                    else:
                        cd_bytes.append(b)
                        break
            uleb(len(data["static_fields"]))
            uleb(len(data["instance_fields"]))
            uleb(len(data["direct_methods"]))
            uleb(len(data["virtual_methods"]))
            prev_method_idx = 0
            for m in data["direct_methods"]:
                diff = m["method_idx"] - prev_method_idx
                uleb(diff)
                prev_method_idx = m["method_idx"]
                uleb(m["access"])
                uleb(m["code_off"])
            # Write class_data
            offset += len(cd_bytes)
            while offset % 4 != 0:
                cd_bytes.append(0)
                offset += 1
            # Write code items
            for m in data["direct_methods"]:
                code_off = offset
                m["code_off"] = code_off
                bc = m["bytecode"]
                tries = m.get("tries", [])
                tries_size = len(tries)
                code_bytes = bytearray()
                code_bytes += struct.pack("<HHHHI",
                                          m.get("registers_size", 4),
                                          m.get("ins_size", 0),
                                          m.get("outs_size", 2),
                                          tries_size,
                                          0)
                code_bytes += struct.pack("<I", len(bc))
                for cu in bc:
                    code_bytes += struct.pack("<H", cu)
                if len(bc) % 2 != 0:
                    code_bytes += b"\x00\x00"
                if tries_size > 0:
                    for t in tries:
                        code_bytes += struct.pack("<IHH",
                                                  t["start_addr"],
                                                  t["insn_count"],
                                                  t["handler_off"])
                    code_bytes += _uleb128(1)  # list_size=1
                    for h in tries:
                        pairs = h["handlers"]
                        n_pairs = len([p for p in pairs if p[0] is not None])
                        has_catch_all = any(p[0] is None for p in pairs)
                        if has_catch_all:
                            size_sleb = -(n_pairs + 1)
                        else:
                            size_sleb = n_pairs
                        code_bytes += _sleb128(size_sleb)
                        for type_desc, addr in pairs:
                            if type_desc is not None:
                                type_idx = self.add_type(type_desc)
                                code_bytes += _uleb128(type_idx)
                                code_bytes += _uleb128(addr)
                        if has_catch_all:
                            for type_desc, addr in pairs:
                                if type_desc is None:
                                    code_bytes += _uleb128(addr)
                                    break
                    while len(code_bytes) % 4 != 0:
                        code_bytes.append(0)
                new_code_items.append((offset, bytes(code_bytes)))
                offset += len(code_bytes)
                while offset % 4 != 0:
                    offset += 1
            # Stash the (final) cd_bytes for this class
            cd["_cd_bytes"] = bytes(cd_bytes)

        # Now we have all offsets. Build the data section.
        data_size = offset - data_off
        # Build final bytes
        out = bytearray(DEX_HEADER_SIZE)

        # string_ids
        out += struct.pack(f"<{string_ids_size}I", *string_data_offsets[:string_ids_size])
        # type_ids
        out += struct.pack(f"<{type_ids_size}I", *self.type_ids)
        # proto_ids
        for sid, rid in self.proto_ids:
            out += struct.pack("<III", sid, rid, 0)  # parameters_off=0
        # field_ids (none)
        # method_ids
        for cid, pid, nid in self.method_ids:
            out += struct.pack("<HHI", cid, pid, nid)
        # class_defs
        for i, cd in enumerate(self.class_defs):
            out += struct.pack("<IIIIIIII",
                               cd["class_idx"],
                               cd["access_flags"],
                               cd["superclass_idx"],
                               cd["interfaces_off"],
                               cd["source_file_idx"],
                               cd["annotations_off"],
                               new_class_data_offsets[i],
                               cd["static_values_off"])

        # data section: string_data + class_data + code_items
        # string_data
        out += string_data_bytes
        # Pad
        while len(out) % 4 != 0:
            out.append(0)
        # class_data + code_items interleaved per class
        for i, cd in enumerate(self.class_defs):
            if cd["class_data"] is None:
                continue
            out += cd["_cd_bytes"]
            while len(out) % 4 != 0:
                out.append(0)
            for m in cd["class_data"]["direct_methods"]:
                # Find the code_item with matching offset
                for co, cb in new_code_items:
                    if co == m["code_off"]:
                        out += cb
                        while len(out) % 4 != 0:
                            out.append(0)
                        break

        # Compute checksum + signature
        # checksum = adler32 of everything after the first 12 bytes
        checksum = zlib.adler32(bytes(out[12:]))
        struct.pack_into("<I", out, 8, checksum)
        # signature = SHA-1 of everything after the first 32 bytes
        import hashlib
        sig = hashlib.sha1(bytes(out[32:])).digest()
        out[12:32] = sig

        # Header
        out[0:8] = DEX_MAGIC
        struct.pack_into("<I", out, 8, checksum)
        struct.pack_into("<I", out, 12, 0)  # not used; signature fills 12-31
        # Wait, let me redo the header layout
        # 0-7: magic
        # 8-11: checksum
        # 12-31: signature (20 bytes)
        # 32-35: file_size
        # 36-39: header_size (0x70)
        # 40-43: endian_tag
        # 44-47: link_size
        # 48-51: link_off
        # 52-55: map_off
        # 56-59: string_ids_size
        # 60-63: string_ids_off
        # 64-67: type_ids_size
        # 68-71: type_ids_off
        # ...
        struct.pack_into("<I", out, 0, 0x7865640a)  # dex\n
        struct.pack_into("<I", out, 4, 0x00353500)  # 035\0
        out[0:8] = DEX_MAGIC
        struct.pack_into("<I", out, 8, checksum)
        out[12:32] = sig
        file_size = len(out)
        struct.pack_into("<I", out, 32, file_size)
        struct.pack_into("<I", out, 36, DEX_HEADER_SIZE)
        struct.pack_into("<I", out, 40, ENDIAN_TAG)
        struct.pack_into("<I", out, 44, 0)  # link_size
        struct.pack_into("<I", out, 48, 0)  # link_off
        struct.pack_into("<I", out, 52, 0)  # map_off (optional)
        struct.pack_into("<I", out, 56, string_ids_size)
        struct.pack_into("<I", out, 60, string_ids_off if string_ids_size else 0)
        struct.pack_into("<I", out, 64, type_ids_size)
        struct.pack_into("<I", out, 68, type_ids_off if type_ids_size else 0)
        struct.pack_into("<I", out, 72, proto_ids_size)
        struct.pack_into("<I", out, 76, proto_ids_off if proto_ids_size else 0)
        struct.pack_into("<I", out, 80, field_ids_size)
        struct.pack_into("<I", out, 84, field_ids_off if field_ids_size else 0)
        struct.pack_into("<I", out, 88, method_ids_size)
        struct.pack_into("<I", out, 92, method_ids_off if method_ids_size else 0)
        struct.pack_into("<I", out, 96, class_defs_size)
        struct.pack_into("<I", out, 100, class_defs_off if class_defs_size else 0)
        struct.pack_into("<I", out, 104, len(out) - data_off)  # data_size
        struct.pack_into("<I", out, 108, data_off)

        return bytes(out)


def _uleb128(v: int) -> bytes:
    out = bytearray()
    while True:
        b = v & 0x7F
        v >>= 7
        if v:
            out.append(b | 0x80)
        else:
            out.append(b)
            break
    return bytes(out)

def _sleb128(v: int) -> bytes:
    out = bytearray()
    while True:
        b = v & 0x7F
        v >>= 7
        if (v == 0 and (b & 0x40) == 0) or (v == -1 and (b & 0x40)):
            out.append(b)
            break
        else:
            out.append(b | 0x80)
    return bytes(out)


# ============================================================================
# Test case builders
# ============================================================================

# Opcodes
OP_CONST_4 = 0x12
OP_CONST_STRING = 0x1a
OP_NEW_INSTANCE = 0x22
OP_INVOKE_DIRECT = 0x70
OP_INVOKE_VIRTUAL = 0x6e
OP_INVOKE_STATIC = 0x71
OP_INVOKE_SUPER = 0x6f
OP_MOVE_RESULT = 0x0a
OP_MOVE_RESULT_OBJECT = 0x0c
OP_MOVE_EXCEPTION = 0x0d
OP_RETURN = 0x0f
OP_RETURN_VOID = 0x0e
OP_RETURN_OBJECT = 0x11
OP_THROW = 0x26
OP_GOTO = 0x27
# EXP-059: Fixed opcode values to match AOSP source code.
# Per https://cs.android.com/android/platform/superproject/+/main:art/libdexfile/dex/dex_instruction_list.h
#   0x38 if-eqz, 0x39 if-nez, 0x3a if-ltz, 0x3b if-gez, 0x3c if-gtz, 0x3d if-lez
# Previous values (0x37 if-eqz, 0x38 if-nez) were off-by-one and only worked
# by coincidence (test outcomes happened to be the same under either
# interpretation).
OP_IF_NEZ = 0x39
OP_IF_EQZ = 0x38

def build_case1_no_catch() -> bytes:
    """Case 1: Method throws, no try table.
    Class: Ltest/exp052/TestActivity; (must match the manifest's main activity).
    Method: onCreate()V (matches Activity.onCreate signature).
        new-instance v0, Ljava/lang/RuntimeException;
        invoke-direct {v0}, RuntimeException.<init>()V
        throw v0
    Expected: throw fires, method halts (no try table).
    """
    b = DexBuilder()
    # Add strings we'll need (string_idx order = add order)
    b.add_string("Ltest/exp052/TestActivity;")  # 0
    b.add_string("onCreate")                      # 1
    b.add_string("(Landroid/os/Bundle;)V")        # 2
    b.add_string("V")                              # 3
    b.add_string("Ljava/lang/Object;")             # 4
    b.add_string("Ljava/lang/RuntimeException;")   # 5
    b.add_string("<init>")                          # 6
    b.add_string("()V")                             # 7
    # Add type Landroid/os/Bundle;
    b.add_string("Landroid/os/Bundle;")             # 8
    b.add_class("Ltest/exp052/TestActivity;", superclass="Landroid/app/Activity;")
    # Method: onCreate(Landroid/os/Bundle;)V
    # Need method_idx for <init> and onCreate
    # Let's add them via add_method
    # <init>: class=RuntimeException, proto=()V, name=<init>
    b.add_method("Ljava/lang/RuntimeException;", "V", "V", "<init>")
    # onCreate: class=TestActivity, proto=(Landroid/os/Bundle;)V, name=onCreate
    b.add_method("Ltest/exp052/TestActivity;", "V", "V", "onCreate")
    # Get type_idx for RuntimeException (index in type_ids list)
    # type_ids are added in add_type calls. We added them implicitly via add_class + add_proto.
    # Better to use add_type explicitly.
    # Let's rebuild with explicit type ordering.
    b2 = DexBuilder()
    # Strings (in fixed order)
    b2.add_string("Ltest/exp052/TestActivity;")  # str_idx=0
    b2.add_string("Ljava/lang/Object;")            # str_idx=1
    b2.add_string("Ljava/lang/RuntimeException;") # str_idx=2
    b2.add_string("Landroid/os/Bundle;")           # str_idx=3
    b2.add_string("<init>")                        # str_idx=4
    b2.add_string("()V")                           # str_idx=5
    b2.add_string("onCreate")                      # str_idx=6
    b2.add_string("(Landroid/os/Bundle;)V")        # str_idx=7
    b2.add_string("V")                             # str_idx=8
    # Types (in fixed order)
    type_test = b2.add_type("Ltest/exp052/TestActivity;")  # type_idx=0
    type_obj = b2.add_type("Ljava/lang/Object;")            # type_idx=1
    type_re = b2.add_type("Ljava/lang/RuntimeException;")  # type_idx=2
    type_bundle = b2.add_type("Landroid/os/Bundle;")        # type_idx=3
    type_V = b2.add_type("V")                                # type_idx=4
    # Protos
    proto_init = b2.add_proto("V", "V")                     # proto_idx=0
    proto_oncreate = b2.add_proto("V", "V")                  # proto_idx=1 (param: Bundle, but proto.shorty = "V")
    # Methods
    method_init = b2.add_method("Ljava/lang/RuntimeException;", "V", "V", "<init>")
    method_oncreate = b2.add_method("Ltest/exp052/TestActivity;", "V", "V", "onCreate")
    # Class
    b2.add_class("Ltest/exp052/TestActivity;", superclass="Landroid/app/Activity;")
    bytecode = [
        # PC=0: new-instance v0, RuntimeException  (type_idx=2)
        (OP_NEW_INSTANCE << 8) | 0x00, 0x0002,
        # PC=2: invoke-direct {v0}, RuntimeException.<init>()V  (method@0)
        (0x10 << 8) | 0x70, 0x0000, 0x0000,
        # PC=5: throw v0
        (0x00 << 8) | 0x26,
    ]
    b2.set_class_data(0, [{
        "name": "onCreate",
        "shorty": "V",
        "return_type": "V",
        "access": 0x1,  # PUBLIC
        "registers_size": 2,
        "ins_size": 2,  # this + Bundle
        "outs_size": 1,
        "bytecode": bytecode,
        "tries": [],
    }])
    return b2.serialize()


def build_case2_local_catch() -> bytes:
    """Case 2: Method throws inside try; catch-all handler exists.
    Expected: handler runs, method returns normally.
    """
    b = DexBuilder()
    b.add_string("Ltest/exp052/TestActivity;")  # 0
    b.add_string("Ljava/lang/Object;")            # 1
    b.add_string("Ljava/lang/RuntimeException;") # 2
    b.add_string("Landroid/os/Bundle;")           # 3
    b.add_string("<init>")                        # 4
    b.add_string("()V")                           # 5
    b.add_string("onCreate")                      # 6
    b.add_string("(Landroid/os/Bundle;)V")        # 7
    b.add_string("V")                             # 8
    b.add_type("Ltest/exp052/TestActivity;")      # type_idx=0
    b.add_type("Ljava/lang/Object;")               # 1
    b.add_type("Ljava/lang/RuntimeException;")    # 2
    b.add_type("Landroid/os/Bundle;")              # 3
    b.add_type("V")                                # 4
    b.add_proto("V", "V")                          # proto_idx=0 (init)
    b.add_proto("V", "V")                          # proto_idx=1 (onCreate)
    b.add_method("Ljava/lang/RuntimeException;", "V", "V", "<init>")  # 0
    b.add_method("Ltest/exp052/TestActivity;", "V", "V", "onCreate")   # 1
    b.add_class("Ltest/exp052/TestActivity;", superclass="Landroid/app/Activity;")
    bytecode = [
        # PC=0: new-instance v2, RuntimeException  (type_idx=2)
        (OP_NEW_INSTANCE << 8) | 0x02, 0x0002,
        # PC=2: invoke-direct {v2}, RuntimeException.<init>()V  (method@0)
        (0x10 << 8) | 0x70, 0x0000, 0x0200,
        # PC=5: throw v2  <- exception source
        (0x02 << 8) | 0x26,
        # PC=6: return-void  <- catch handler start
        (0x00 << 8) | 0x0e,
    ]
    b.set_class_data(0, [{
        "name": "onCreate",
        "shorty": "V",
        "return_type": "V",
        "access": 0x1,
        "registers_size": 4,
        "ins_size": 2,
        "outs_size": 1,
        "bytecode": bytecode,
        "tries": [{
            "start_addr": 0,
            "insn_count": 6,  # PC 0..5 covered
            "handler_off": 1,
            "handlers": [(None, 6)],  # catch-all at PC=6
        }],
    }])
    return b.serialize()


def build_case3_nested_catch() -> bytes:
    """Case 3: onCreate() calls helper(); helper() throws; onCreate() has catch."""
    b = DexBuilder()
    b.add_string("Ltest/exp052/TestActivity;")  # 0
    b.add_string("Ljava/lang/Object;")            # 1
    b.add_string("Ljava/lang/RuntimeException;") # 2
    b.add_string("Landroid/os/Bundle;")           # 3
    b.add_string("<init>")                        # 4
    b.add_string("()V")                           # 5
    b.add_string("onCreate")                      # 6
    b.add_string("(Landroid/os/Bundle;)V")        # 7
    b.add_string("helper")                        # 8
    b.add_string("V")                             # 9
    b.add_type("Ltest/exp052/TestActivity;")      # 0
    b.add_type("Ljava/lang/Object;")               # 1
    b.add_type("Ljava/lang/RuntimeException;")    # 2
    b.add_type("Landroid/os/Bundle;")              # 3
    b.add_type("V")                                # 4
    b.add_proto("V", "V")                          # 0 (init)
    b.add_proto("V", "V")                          # 1 (onCreate)
    b.add_proto("V", "V")                          # 2 (helper)
    b.add_method("Ljava/lang/RuntimeException;", "V", "V", "<init>")  # 0
    b.add_method("Ltest/exp052/TestActivity;", "V", "V", "onCreate")   # 1
    b.add_method("Ltest/exp052/TestActivity;", "V", "V", "helper")    # 2
    b.add_class("Ltest/exp052/TestActivity;", superclass="Landroid/app/Activity;")
    # onCreate: try { invoke-static helper() } catch-all { return-void }
    bytecode_oncreate = [
        # PC=0: invoke-static {}, TestActivity.helper()V  (method@2)
        (0x00 << 8) | 0x71, 0x0002, 0x0000,
        # PC=3: return-void  (won't reach)
        (0x00 << 8) | 0x0e,
        # PC=4: return-void  <- catch handler start
        (0x00 << 8) | 0x0e,
    ]
    # helper: new RuntimeException, throw
    bytecode_helper = [
        # PC=0: new-instance v0, RuntimeException  (type_idx=2)
        (OP_NEW_INSTANCE << 8) | 0x00, 0x0002,
        # PC=2: invoke-direct {v0}, RuntimeException.<init>()V  (method@0)
        (0x10 << 8) | 0x70, 0x0000, 0x0000,
        # PC=5: throw v0
        (0x00 << 8) | 0x26,
    ]
    b.set_class_data(0, [
        {
            "name": "onCreate",
            "shorty": "V",
            "return_type": "V",
            "access": 0x1,
            "registers_size": 4,
            "ins_size": 2,
            "outs_size": 1,
            "bytecode": bytecode_oncreate,
            "tries": [{
                "start_addr": 0,
                "insn_count": 4,  # PC 0..3 covered
                "handler_off": 1,
                "handlers": [(None, 4)],  # catch-all at PC=4
            }],
        },
        {
            "name": "helper",
            "shorty": "V",
            "return_type": "V",
            "access": 0x9,  # PUBLIC STATIC
            "registers_size": 1,
            "ins_size": 0,
            "outs_size": 1,
            "bytecode": bytecode_helper,
            "tries": [],
        },
    ])
    return b.serialize()


def build_case4_catch_all() -> bytes:
    """Case 4: Catch-all (catch Throwable) — same as Case 2 in this minimal test."""
    return build_case2_local_catch()


def wrap_in_apk(dex_bytes: bytes, package: str = "test.exp052") -> bytes:
    """Wrap DEX in a minimal APK with AndroidManifest.xml."""
    # Minimal AndroidManifest.xml binary XML
    manifest = build_minimal_manifest(package)
    # Build APK
    apk_bytes = io.BytesIO()
    with zipfile.ZipFile(apk_bytes, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('classes.dex', dex_bytes)
        z.writestr('AndroidManifest.xml', manifest)
    return apk_bytes.getvalue()


def build_minimal_manifest(package: str) -> bytes:
    """Build a minimal AndroidManifest.xml."""
    # Use a pre-baked minimal AXML. The runtime doesn't fully parse the
    # manifest — it just looks for the package name.
    template = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<manifest xmlns:android="http://schemas.android.com/apk/res/android"\n'
        '    package="{pkg}">\n'
        '    <application android:label="Test">\n'
        '        <activity android:name=".TestActivity">\n'
        '            <intent-filter>\n'
        '                <action android:name="android.intent.action.MAIN"/>\n'
        '                <category android:name="android.intent.category.LAUNCHER"/>\n'
        '            </intent-filter>\n'
        '        </activity>\n'
        '    </application>\n'
        '</manifest>\n'
    )
    return template.format(pkg=package).encode("utf-8")


def run_test(name: str, dex_bytes: bytes) -> dict:
    """Run a single test case. Returns result dict."""
    test_dir = os.path.join(MINIANDROID_ROOT, "run", "exp052_exceptions", name)
    os.makedirs(test_dir, exist_ok=True)
    dex_path = os.path.join(MINIANDROID_ROOT, "test_apks", "exp052", f"{name}.dex")
    apk_path = os.path.join(MINIANDROID_ROOT, "test_apks", "exp052", f"{name}.apk")
    os.makedirs(os.path.dirname(dex_path), exist_ok=True)
    with open(dex_path, "wb") as f:
        f.write(dex_bytes)
    apk_bytes = wrap_in_apk(dex_bytes)
    with open(apk_path, "wb") as f:
        f.write(apk_bytes)

    # Run the runtime
    cmd = [RUNTIME_BIN, apk_path, test_dir]
    print(f"[RUN] {name}")
    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        elapsed = time.time() - start
        log_path = os.path.join(test_dir, "run.log")
        with open(log_path, "w") as f:
            f.write(result.stdout)
            f.write("\n--- STDERR ---\n")
            f.write(result.stderr)
        return {
            "name": name,
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "elapsed": elapsed,
            "log_path": log_path,
        }
    except subprocess.TimeoutExpired:
        return {
            "name": name,
            "exit_code": -1,
            "stdout": "",
            "stderr": "TIMEOUT",
            "elapsed": 30,
            "log_path": None,
        }


def main():
    print("=== EXP-052 Exception Handling Validation Suite ===")
    print()

    cases = [
        ("case1_no_catch", build_case1_no_catch,
         "Throw with no try table — method should halt cleanly, caller continues."),
        ("case2_local_catch", build_case2_local_catch,
         "Throw inside try{}; catch-all handler exists — handler should run."),
        ("case3_nested_catch", build_case3_nested_catch,
         "B() throws; A() has catch — stack should unwind from B to A."),
        ("case4_catch_all", build_case4_catch_all,
         "Catch-all handler — same as case2."),
    ]

    results = []
    for name, builder, desc in cases:
        print(f"--- {name} ---")
        print(f"  Description: {desc}")
        dex = builder()
        result = run_test(name, dex)
        results.append(result)
        print(f"  Exit code: {result['exit_code']}")
        print(f"  Elapsed: {result['elapsed']:.2f}s")
        # Look for THROW / HALT in stderr
        if "[THROW]" in result["stderr"]:
            for line in result["stderr"].splitlines():
                if "[THROW]" in line:
                    print(f"  THROW: {line.strip()}")
        if "[HALT" in result["stderr"]:
            for line in result["stderr"].splitlines():
                if "[HALT" in line:
                    print(f"  HALT: {line.strip()}")
        print()

    # Write summary
    summary_path = os.path.join(MINIANDROID_ROOT, "docs", "EXP052_EXCEPTION_TESTS.md")
    with open(summary_path, "w") as f:
        f.write("# EXP-052 Exception Handling Validation Suite\n\n")
        f.write("**Date:** 2026-08-17\n\n")
        f.write("## Test Cases\n\n")
        for name, _, desc in cases:
            f.write(f"### {name}\n{desc}\n\n")
        f.write("## Results\n\n")
        f.write("| Case | Exit | THROW events | HALT events | Has try table (in test) |\n")
        f.write("|------|------|--------------|-------------|--------------------------|\n")
        for r in results:
            throws = [l for l in r["stderr"].splitlines() if "[THROW]" in l]
            halts = [l for l in r["stderr"].splitlines() if "[HALT" in l]
            f.write(f"| {r['name']} | {r['exit_code']} | {len(throws)} | {len(halts)} | — |\n")
        f.write("\n## Per-case Details\n\n")
        for r in results:
            f.write(f"### {r['name']}\n\n")
            f.write(f"- Exit code: {r['exit_code']}\n")
            f.write(f"- Elapsed: {r['elapsed']:.2f}s\n")
            throws = [l for l in r["stderr"].splitlines() if "[THROW]" in l]
            if throws:
                f.write(f"- THROW events ({len(throws)}):\n")
                for l in throws:
                    f.write(f"  - `{l.strip()}`\n")
            halts = [l for l in r["stderr"].splitlines() if "[HALT" in l]
            if halts:
                f.write(f"- HALT events ({len(halts)}):\n")
                for l in halts:
                    f.write(f"  - `{l.strip()}`\n")
            f.write("\n")
    print(f"Summary written to {summary_path}")


if __name__ == "__main__":
    main()
