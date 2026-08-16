#!/usr/bin/env python3
"""
EXP-046 PHASE 1 — Native Method Map for Telegram APK

Scans all 5 DEX files inside the production Telegram APK and produces a
prioritized, machine-readable native-method map.  For every Java method
whose `access_flags` has the `ACC_NATIVE` (0x100) bit set, this tool
records:

  * Class descriptor                  e.g. Lorg/telegram/tgnet/ConnectionsManager;
  * Method name                       e.g. native_getCurrentTime
  * Prototype / shorty                e.g. II   (takes int, returns int)
  * Full signature                    e.g. Lorg/telegram/tgnet/ConnectionsManager;->native_getCurrentTime(I)I
  * DEX file                          classes.dex / classes3.dex / ...
  * Access flags (static/instance/etc.)
  * Priority bucket                   P0/P1/P2/P3
  * on_execution_path flag            True if the declaring class itself
                                      appears among the 154 unique methods
                                      reached by the EXP-046 baseline run.

It also locates:
  * Every `invoke-static` of `Ljava/lang/System;.loadLibrary`,
    `Ljava/lang/System;.load`, `Ljava/lang/Runtime;.loadLibrary0`,
    `Ljava/lang/Runtime;.load`, `Ljava/lang/Runtime;.load0`.
  * The definition of `Lorg/telegram/messenger/NativeLoader;.initNativeLibs`
    (the non-native bootstrap that performs `System.loadLibrary("tmessages.49")`),
    every call site of it across the APK, and the loadLibrary calls made
    inside its own body.

Priority scheme (per EXP-046-PHASE1 spec):

  P0  Called before or during Application init
      (NativeLoader, ConnectionsManager, ApplicationLoader, tgnet bootstrap)
  P1  Called during Activity onCreate
      (RLottie, SQLite, Intro, Utilities, AnimatedFileNative)
  P2  Called during message send/receive
      (VoIP, WebRTC, NativeByteBuffer, MediaController, SecretChat)
  P3  Rarely called (ExoPlayer decoders, Ffmpeg, Flac, Opus, Vpx, Av1,
      BotWebView)

Inputs:
  /home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/download/exp038_telegram/Telegram.apk
  /home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/run/exp046_baseline.log

Outputs:
  miniandroid/docs/EXP046_NATIVE_MAP.md
  miniandroid/docs/EXP046_NATIVE_MAP.json

No third-party dependencies — only `struct`, `zipfile`, `json`, `re`, `os`,
`sys`, `collections`, `typing`.

DEX binary layout reference is the canonical Android `dalvik/libdex/DexFile.h`
(identical to that used by `exp042_jni_inventory.py` and
`exp043_jni_distance.py`).
"""

from __future__ import annotations

import json
import os
import re
import struct
import sys
import zipfile
from collections import OrderedDict, defaultdict
from typing import Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

PROJECT_ROOT = "/home/z/my-project/MiniAndroid-Compatibility-Runtime"
APK_PATH = os.path.join(
    PROJECT_ROOT, "miniandroid/download/exp038_telegram/Telegram.apk"
)
EXEC_LOG_PATH = os.path.join(
    PROJECT_ROOT, "miniandroid/run/exp046_baseline.log"
)
OUT_DIR = os.path.join(PROJECT_ROOT, "miniandroid/docs")
MD_PATH = os.path.join(OUT_DIR, "EXP046_NATIVE_MAP.md")
JSON_PATH = os.path.join(OUT_DIR, "EXP046_NATIVE_MAP.json")

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

HEADER_FMT    = "<8sI20s" + "I" * 20   # 8+4+20+80 = 112 bytes
HEADER_SIZE   = struct.calcsize(HEADER_FMT)
assert HEADER_SIZE == 112, "DexHeader must be 112 bytes"

METHOD_ID_FMT  = "<HHI"            # 8 bytes
CLASS_DEF_FMT  = "<IIIIIIII"       # 32 bytes
CODE_ITEM_HDR  = "<HHHHII"        # 16 bytes
TYPE_LIST_HDR  = "<I"              # 4 bytes (size), then size * u16 type_idx

NO_INDEX = 0xFFFFFFFF

# ---------------------------------------------------------------------------
# Dalvik opcode table  (op, name, num_code_units, format_id)
# Reused verbatim from `miniandroid/tools/exp043_jni_distance.py`.
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
    0xd8: ('add-int/lit8', 2, '22b'), 0xd9: ('rsub-int', 2, '22b'),
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
    sections needed for the native-method scan and call-site analysis."""

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

    def get_method_param_types(self, method_idx: int) -> List[str]:
        """Resolve the parameter type descriptors of a method via its
        proto_id's `parameters_off` field, which points to a type_list."""
        if not (0 <= method_idx < len(self._methods)):
            return []
        proto_idx = self._methods[method_idx][1]
        if not (0 <= proto_idx < len(self._protos)):
            return []
        _shorty_idx, _return_idx, parameters_off = self._protos[proto_idx]
        if parameters_off == 0 or parameters_off + 4 > len(self.data):
            return []
        size = struct.unpack(TYPE_LIST_HDR, self.data[parameters_off:parameters_off + 4])[0]
        if size == 0:
            return []
        # Each type_list entry is a u16 type_idx (2 bytes, no padding).
        raw = self.data[parameters_off + 4: parameters_off + 4 + size * 2]
        if len(raw) < size * 2:
            return []
        idxs = struct.unpack(f"<{size}H", raw)
        return [self.get_type(i) for i in idxs]

    def get_method_return_type(self, method_idx: int) -> str:
        if not (0 <= method_idx < len(self._methods)):
            return "<bad-method-idx>"
        proto_idx = self._methods[method_idx][1]
        if not (0 <= proto_idx < len(self._protos)):
            return "<bad-proto-idx>"
        return_idx = self._protos[proto_idx][1]
        return self.get_type(return_idx)

    def get_method_full_signature(self, method_idx: int) -> str:
        """Return e.g. 'Lorg/telegram/tgnet/ConnectionsManager;->native_getCurrentTime(I)I'."""
        cls = self.get_method_class(method_idx)
        name = self.get_method_name(method_idx)
        params = self.get_method_param_types(method_idx)
        rtype = self.get_method_return_type(method_idx)
        param_str = "".join(params)
        return f"{cls}->{name}({param_str}){rtype}"

    def get_method_descriptor(self, method_idx: int) -> str:
        """Return '<class>;.<method>' (no prototype) — same format used by
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
    target_method_idxs: Set[int],
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

    Returns the list in PC order.  Properly skips payload-data blocks
    (packed-switch / sparse-switch / fill-array-data) so the scan stays
    in sync with the instruction stream.
    """
    hdr = read_code_item_header(dex.data, code_off)
    if hdr is None:
        return []
    _, _, _, _, _, insns_size = hdr
    if insns_size == 0:
        return []
    insns_off = code_off + 16
    raw = dex.data[insns_off:insns_off + insns_size * 2]
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
            pc += 1
            continue
        _name, units_n, fmt = info
        if op in INVOKE_OPS and pc + 1 < insns_size:
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
        # Skip payload blocks identically.
        if op == 0x00 and high == 0x01 and pc + 1 < insns_size:
            sz = units[pc + 1]
            pc += 3 + sz * 2
            continue
        if op == 0x00 and high == 0x02 and pc + 1 < insns_size:
            sz = units[pc + 1]
            pc += 2 + sz * 4
            continue
        if op == 0x00 and high == 0x03 and pc + 1 < insns_size:
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
    `const-string` write to `target_register`.  If `before_pc` is None,
    returns the *last* write in the whole method (a coarse fallback).
    Otherwise returns the most-recent write *before* that PC."""
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
# Priority bucketing (EXP-046-PHASE1 scheme)
# ---------------------------------------------------------------------------
# P0  Called before or during Application init
#     (NativeLoader, ConnectionsManager, ApplicationLoader, tgnet bootstrap)
P0_CLASSES = (
    "NativeLoader",
    "ConnectionsManager",
    "ApplicationLoader",
)
# tgnet module is P0 too — it's the bootstrap of the ConnectionsManager.
P0_KEYWORDS = (
    "tgnet",  # tgnet/TLObject, tl-NativeByteBuffer etc. — tgnet bootstrap
)

# P1  Called during Activity onCreate
#     (RLottie, SQLite, Intro, Utilities, AnimatedFileNative)
P1_CLASSES = (
    "RLottie",
    "Lottie",
    "AnimatedFileNative",
    "SQLite",
    "Intro",
    "Utilities",
)

# P2  Called during message send/receive
#     (VoIP, WebRTC, NativeByteBuffer, MediaController, SecretChat,
#      BotWebView, GroupCallMessagesController)
P2_CLASSES = (
    "VoIPController",
    "NativeInstance",
    "ConferenceCall",
    "VLog",
    "GroupCallMessagesController",
    "MediaController",
    "SecretChat",
    "BotWebView",
)
P2_KEYWORDS = (
    "webrtc",  # all of org.webrtc.*
)

# P3  Rarely called (ExoPlayer decoders, Ffmpeg, Flac, Opus, Vpx, Av1)
P3_KEYWORDS = (
    "exoplayer",
    "ffmpeg",
    "Flac",
    "Opus",
    "Vpx",
    "Av1",
    "mlkit",  # language-id JNI from mlkit — also rare
)


def guess_priority(class_desc: str) -> str:
    """Priority bucket — P0/P1/P2/P3 — per the EXP-046-PHASE1 spec."""
    # P0 first (highest priority)
    for needle in P0_CLASSES:
        if needle in class_desc:
            return "P0"
    for kw in P0_KEYWORDS:
        if kw in class_desc:
            return "P0"
    # P1 next
    for needle in P1_CLASSES:
        if needle in class_desc:
            return "P1"
    # P2 next
    for needle in P2_CLASSES:
        if needle in class_desc:
            return "P2"
    for kw in P2_KEYWORDS:
        if kw in class_desc.lower():
            return "P2"
    # P3 last (ExoPlayer decoders, mlkit, etc.)
    for kw in P3_KEYWORDS:
        if kw in class_desc:
            return "P3"
    return "P3"  # default — unknown / rarely-called


# ---------------------------------------------------------------------------
# Library attribution (carried over from EXP-042)
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
    if "webrtc" in class_desc:
        return "libtmessages.49.so (webrtc module)"
    if "exoplayer" in class_desc or "ffmpeg" in class_desc or "Flac" in class_desc \
            or "Opus" in class_desc or "Vpx" in class_desc or "Av1" in class_desc:
        return "libtmessages.49.so (exoplayer module)"
    return "libtmessages.49.so"


def access_flags_string(access_flags: int) -> str:
    """Human-readable access-flags summary, e.g. 'public static native'."""
    parts = []
    if access_flags & ACC_PUBLIC:     parts.append("public")
    if access_flags & ACC_PRIVATE:    parts.append("private")
    if access_flags & ACC_PROTECTED:   parts.append("protected")
    if access_flags & ACC_STATIC:      parts.append("static")
    if access_flags & ACC_FINAL:      parts.append("final")
    if access_flags & ACC_SYNCHRONIZED: parts.append("synchronized")
    if access_flags & ACC_NATIVE:     parts.append("native")
    if access_flags & ACC_ABSTRACT:   parts.append("abstract")
    return " ".join(parts) if parts else "package-private"


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
    """Parse `exp046_baseline.log` into a structured view."""
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
    """Scan every DEX file in the APK. Returns the structured inventory."""
    native_methods: List[Dict] = []
    load_library_sites: List[Dict] = []
    native_loader_init_sites: List[Dict] = []
    dex_stats: Dict[str, Dict] = OrderedDict()
    # Map '<class>.<method>' -> native-method record, for cross-reference.
    native_method_lookup: Dict[str, Dict] = {}

    # Per-DEX caches for the 2nd / 3rd pass.
    dex_cache: Dict[str, DexFile] = {}
    per_dex_method_lookup: Dict[str, Dict[Tuple[str, str], int]] = {}
    per_dex_native_set: Dict[str, Set[int]] = {}
    loadlib_target_idxs: Dict[str, Set[int]] = {}
    nativeloader_initnativelibs_idxs: Dict[str, Set[int]] = {}

    with zipfile.ZipFile(apk_path, "r") as z:
        available = set(z.namelist())
        for dex_name in DEX_FILES:
            if dex_name not in available:
                print(f"  [WARN] {dex_name} not in APK, skipping", file=sys.stderr)
                continue
            raw = z.read(dex_name)
            dex = DexFile(dex_name, raw)
            dex_cache[dex_name] = dex
            classes_in_dex = dex.class_defs_size
            dex_methods = dex.method_ids_size
            dex_strings = dex.string_ids_size
            dex_types = dex.type_ids_size
            dex_protos = dex.proto_ids_size
            dex_fields = dex.field_ids_size
            native_count = 0
            classes_with_native: Set[str] = set()
            method_lookup: Dict[Tuple[str, str], int] = {}
            native_method_idxs: Set[int] = set()

            # 1st pass: walk all methods, collect native ones, build
            # (class, name) -> method_idx index for cross-reference.
            for (
                descriptor, class_access, method_name, shorty,
                method_idx, access_flags, code_off, method_kind
            ) in dex.iter_all_methods():
                method_lookup[(descriptor, method_name)] = method_idx
                if (access_flags & ACC_NATIVE) != 0:
                    native_count += 1
                    classes_with_native.add(descriptor)
                    full_sig = dex.get_method_full_signature(method_idx)
                    rec = {
                        'class': descriptor,
                        'method': method_name,
                        'shorty': shorty,
                        'full_signature': full_sig,
                        'library': guess_library(descriptor),
                        'dex': dex_name,
                        'priority': guess_priority(descriptor),
                        'class_access_flags': class_access,
                        'method_access_flags': access_flags,
                        'access_flags_string': access_flags_string(access_flags),
                        'method_idx': method_idx,
                        'method_kind': method_kind,
                        'code_off': code_off,
                        'on_execution_path': False,  # filled later
                        'jni_symbol': jni_symbol_for(descriptor, method_name,
                                                     access_flags),
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

        # 2nd pass: build the method_idx sets for:
        #   - System.loadLibrary / System.load / Runtime.loadLibrary0 etc.
        #   - NativeLoader.initNativeLibs
        for dex_name in DEX_FILES:
            if dex_name not in dex_cache:
                continue
            dex = dex_cache[dex_name]
            loadlib_idxs: Set[int] = set()
            initnativelibs_idxs: Set[int] = set()
            for mi in range(len(dex._methods)):
                cls = dex.get_method_class(mi)
                name = dex.get_method_name(mi)
                if cls == "Ljava/lang/System;" and name in ("loadLibrary", "load"):
                    loadlib_idxs.add(mi)
                elif cls == "Ljava/lang/Runtime;" and name in (
                        "loadLibrary", "loadLibrary0", "load", "load0"):
                    loadlib_idxs.add(mi)
                elif (cls == "Lorg/telegram/messenger/NativeLoader;"
                      and name == "initNativeLibs"):
                    initnativelibs_idxs.add(mi)
            loadlib_target_idxs[dex_name] = loadlib_idxs
            nativeloader_initnativelibs_idxs[dex_name] = initnativelibs_idxs
            print(
                f"  [IDX] {dex_name}: loadLibrary/load targets="
                f"{len(loadlib_idxs)}, NativeLoader.initNativeLibs targets="
                f"{len(initnativelibs_idxs)}",
                file=sys.stderr,
            )

        # 3rd pass: walk every method with bytecode, scan for invoke-*
        # to the target sets built above.
        for dex_name in DEX_FILES:
            if dex_name not in dex_cache:
                continue
            dex = dex_cache[dex_name]
            loadlib_idxs = loadlib_target_idxs[dex_name]
            initnativelibs_idxs = nativeloader_initnativelibs_idxs[dex_name]
            if not (loadlib_idxs or initnativelibs_idxs):
                continue
            targets = loadlib_idxs | initnativelibs_idxs
            for (
                descriptor, class_access, method_name, shorty,
                method_idx, access_flags, code_off, method_kind
            ) in dex.iter_all_methods():
                if code_off == 0:
                    continue
                if (access_flags & ACC_NATIVE) != 0:
                    continue
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
                    if s['method_idx'] in initnativelibs_idxs:
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
        'dex_cache': dex_cache,
        'per_dex_method_lookup': per_dex_method_lookup,
    }


# ---------------------------------------------------------------------------
# JNI symbol-name mangling
# ---------------------------------------------------------------------------

def jni_mangle_class(class_desc: str) -> str:
    """Mangle a class descriptor into the JNI C symbol segment.

    JNI uses '_' for '/' and '_1' for '_'.  For our purposes the typical
    Telegram classes only need the '/' -> '_' substitution.
    """
    s = class_desc
    if s.startswith("L") and s.endswith(";"):
        s = s[1:-1]
    # '_' -> '_1' first, then '/' -> '_'
    s = s.replace("_", "_1").replace("/", "_")
    return s


def jni_mangle_method(name: str) -> str:
    """Mangle a method name for the JNI C symbol segment."""
    # JNI name mangling for method names: '_' -> '_1', ';' -> '_2',
    # '[' -> '_3', '<' -> '_4', '>' -> '_8'.  Most native methods have
    # plain-ASCII identifiers so this is mostly a no-op.
    return (name
            .replace("_", "_1")
            .replace(";", "_2")
            .replace("[", "_3")
            .replace("<", "_4")
            .replace(">", "_8"))


def jni_symbol_for(class_desc: str, method_name: str,
                   access_flags: int) -> str:
    """Return the JNI export symbol name for a native method, e.g.
       Java_org_1telegram_1tgnet_1ConnectionsManager_native_1getCurrentTime

    NOTE: Telegram's libtmessages.49.so registers most of its native
    methods at runtime via `RegisterNatives()` in `JNI_OnLoad`, so the
    JNI symbol name may not be exported as a `Java_*` ELF symbol.  This
    field is informational only.
    """
    return "Java_" + jni_mangle_class(class_desc) + "_" + jni_mangle_method(method_name)


# ---------------------------------------------------------------------------
# Cross-reference: mark items on the execution path
# ---------------------------------------------------------------------------

def cross_reference_with_log(scan: Dict, log_view: Dict) -> Dict:
    """Annotate native methods, loadLibrary call sites, and
    NativeLoader.initNativeLibs call sites with `on_execution_path` flags.

    A native method is marked on-execution-path if its declaring class
    appears among the unique methods reached by the baseline run.  Because
    native methods are not yet invoked by the runtime (the JNI bridge is
    not implemented), a native method itself never appears in the log as
    `[METHOD-IN]`; we therefore mark by *class match*, not by method
    match.  This catches the case where e.g. the log contains
    `Lorg/telegram/messenger/ApplicationLoader;.postInitApplication` and
    a native method `Lorg/telegram/tgnet/ConnectionsManager;.native_getCurrentTime`
    should be flagged because its declaring class `ConnectionsManager`
    was reached (it is the class on whose static methods the runtime
    would call native_getCurrentTime).
    """
    if not log_view.get('log_exists'):
        return {
            'executed_methods_set': set(),
            'executed_classes_set': set(),
            'first_native_method': None,
            'jni_distance': "not reached yet (no execution log)",
            'first_static_native_chain_entry': None,
        }
    unique_methods = log_view['unique_methods']
    executed_descs = {m['method'] for m in unique_methods}

    # Extract unique class descriptors (the 'Lfoo/Bar;' prefix of each
    # `[METHOD-IN] Lfoo/Bar;.baz' line).
    executed_classes: Set[str] = set()
    for desc in executed_descs:
        if desc.startswith("L") and ";." in desc:
            cls = desc.split(";.", 1)[0] + ";"
            executed_classes.add(cls)

    # Mark native methods — by *class match* (see docstring).
    for nm in scan['native_methods']:
        if nm['class'] in executed_classes:
            nm['on_execution_path'] = True

    # Mark loadLibrary / NativeLoader.initNativeLibs call sites — by
    # exact (class, method) match.
    for site in scan['load_library_sites']:
        key = f"{site['calling_class']}.{site['calling_method']}"
        if key in executed_descs:
            site['on_execution_path'] = True

    for site in scan['native_loader_init_sites']:
        key = f"{site['calling_class']}.{site['calling_method']}"
        if key in executed_descs:
            site['on_execution_path'] = True

    # Determine the first native method that entered the log (by exact
    # descriptor match — would happen only if the runtime started
    # invoking native methods, which it does not yet do).
    first_native = None
    for m in unique_methods:
        if m['method'] in scan['native_method_lookup']:
            first_native = {
                'method': m['method'],
                'index': m['first_seen_index'],
                'record': scan['native_method_lookup'][m['method']],
            }
            break

    if first_native is not None:
        jni_distance = first_native['index']
    else:
        jni_distance = "not reached yet (no native method itself entered the log)"

    return {
        'executed_methods_set': executed_descs,
        'executed_classes_set': executed_classes,
        'first_native_method': first_native,
        'jni_distance': jni_distance,
    }


# ---------------------------------------------------------------------------
# Static call chain: for each executed method, scan its bytecode for
# invoke-* to a native method or a framework loadLibrary method.
# ---------------------------------------------------------------------------

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
          `Ljava/lang/Runtime;.loadLibrary0`,
          `Ljava/lang/Runtime;.load`, `Ljava/lang/Runtime;.load0`,
          `Lorg/telegram/messenger/NativeLoader;.initNativeLibs`.

    Returns the list of those call sites as 'potential native calls
    reachable from the execution path' (direct, depth-0).
    """
    if not log_view.get('log_exists'):
        return []

    dex_cache: Dict[str, DexFile] = scan['dex_cache']
    per_dex_lookup: Dict[str, Dict[Tuple[str, str], int]] = scan['per_dex_method_lookup']

    # Build per-DEX indexes of:
    #   - method_idx of every native method
    #   - method_idx of every framework loadLibrary / Runtime.load*
    #     method (these are *referenced* but not declared in the APK).
    #   - method_idx of NativeLoader.initNativeLibs
    #   - method_idx -> (descriptor, name, code_off) for every method
    #     DECLARED in this DEX, used for depth-1 transitive scans.
    native_idxs_per_dex: Dict[str, Set[int]] = {}
    loadlib_idxs_per_dex: Dict[str, Set[int]] = {}
    initnativelibs_idxs_per_dex: Dict[str, Set[int]] = {}
    method_lookup_per_dex: Dict[str, Dict[int, Tuple[str, str, int]]] = {}

    for dex_name, dex in dex_cache.items():
        native_idxs: Set[int] = set()
        loadlib_idxs: Set[int] = set()
        initnativelibs_idxs: Set[int] = set()
        method_lookup: Dict[int, Tuple[str, str, int]] = {}
        for (
            descriptor, _ca, method_name, _shorty,
            method_idx, access_flags, code_off, _mk
        ) in dex.iter_all_methods():
            method_lookup[method_idx] = (descriptor, method_name, code_off)
            if (access_flags & ACC_NATIVE) != 0:
                native_idxs.add(method_idx)
        # Walk every method REFERENCED in this DEX (via method_ids[])
        # to find framework native methods (System.loadLibrary, etc.)
        # and NativeLoader.initNativeLibs.
        for mi in range(len(dex._methods)):
            cls = dex.get_method_class(mi)
            name = dex.get_method_name(mi)
            if cls == "Ljava/lang/System;" and name in ("loadLibrary", "load"):
                loadlib_idxs.add(mi)
            elif cls == "Ljava/lang/Runtime;" and name in (
                    "loadLibrary", "loadLibrary0", "load", "load0"):
                loadlib_idxs.add(mi)
            elif (cls == "Lorg/telegram/messenger/NativeLoader;"
                  and name == "initNativeLibs"):
                initnativelibs_idxs.add(mi)
        native_idxs_per_dex[dex_name] = native_idxs
        loadlib_idxs_per_dex[dex_name] = loadlib_idxs
        initnativelibs_idxs_per_dex[dex_name] = initnativelibs_idxs
        method_lookup_per_dex[dex_name] = method_lookup

    out: List[Dict] = []

    for executed_method in log_view['unique_methods']:
        desc = executed_method['method']
        if not desc.startswith("L") or ";." not in desc:
            continue
        class_part, method_part = desc.split(";.", 1)
        class_desc = class_part + ";"
        method_name = method_part
        # Find the DEX that declares this (class, method).
        dex_name = None
        for dn, lookup in per_dex_lookup.items():
            if (class_desc, method_name) in lookup:
                dex_name = dn
                break
        if dex_name is None:
            continue
        dex = dex_cache[dex_name]
        method_idx = per_dex_lookup[dex_name].get((class_desc, method_name))
        if method_idx is None:
            continue
        # Resolve code_off via this DEX's method lookup.
        info = method_lookup_per_dex[dex_name].get(method_idx)
        if info is None:
            continue
        (_cd, _mn, code_off) = info
        if code_off == 0:
            continue
        native_idxs = native_idxs_per_dex[dex_name]
        loadlib_idxs = loadlib_idxs_per_dex[dex_name]
        initnativelibs_idxs = initnativelibs_idxs_per_dex[dex_name]
        depth0_targets = native_idxs | loadlib_idxs | initnativelibs_idxs
        if not depth0_targets:
            continue
        sites = scan_invoke_sites(dex, code_off, depth0_targets)
        for s in sites:
            target_native = s['method_idx'] in native_idxs
            target_loadlib = s['method_idx'] in loadlib_idxs
            target_initnativelibs = s['method_idx'] in initnativelibs_idxs
            kind = []
            if target_native:
                kind.append("native-method")
            if target_loadlib:
                kind.append("framework-loadLibrary")
            if target_initnativelibs:
                kind.append("NativeLoader.initNativeLibs")
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

    # Deduplicate by (caller, target, pc).
    seen: Set[Tuple] = set()
    deduped: List[Dict] = []
    for entry in out:
        key = (
            entry['caller_class'], entry['caller_method'],
            entry['target_class'], entry['target_method'],
            entry['caller_pc'], entry['depth'],
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(entry)
    deduped.sort(key=lambda e: (e['depth'],
                                e['caller_first_seen_index'],
                                e['caller_pc']))
    return deduped


# ---------------------------------------------------------------------------
# Markdown rendering
# ---------------------------------------------------------------------------

PRI_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


def render_markdown(
    scan: Dict,
    log_view: Dict,
    xref: Dict,
    static_chain: List[Dict],
) -> str:
    lines: List[str] = []
    lines.append("# EXP-046 Phase 1 — Native Method Map")
    lines.append("")
    lines.append(
        "Generated by `miniandroid/tools/exp046_native_map.py`. Scans "
        "every DEX file inside the production Telegram APK, lists every "
        "Java method whose `access_flags` has the `ACC_NATIVE` (0x100) "
        "bit set, cross-references each one against the 154 unique "
        "methods reached by the EXP-046 baseline run, and prioritizes "
        "them by likelihood of being on the startup path."
    )
    lines.append("")

    # ----- 1. Summary -----
    lines.append("## 1. Summary")
    lines.append("")
    lines.append(f"- **APK**: `{scan['apk']}`")
    lines.append(f"- **DEX files scanned**: {len(scan['dex_stats'])} of 5 expected")
    lines.append(f"- **Total native methods**: {scan['total_native_methods']}")
    lines.append(f"- **Total classes with native methods**: "
                 f"{len({nm['class'] for nm in scan['native_methods']})}")
    lines.append(f"- **`System.loadLibrary` / `System.load` call sites**: "
                 f"{scan['total_load_library_sites']}")
    lines.append(f"- **`NativeLoader.initNativeLibs` call sites**: "
                 f"{scan['total_native_loader_init_sites']}")
    if log_view.get('log_exists'):
        lines.append(f"- **Execution log**: `{log_view['log_path']}`")
        lines.append(f"- **Unique methods entered (with repeats deduped)**: "
                     f"{len(log_view['unique_methods'])}")
        lines.append(f"- **Unique classes entered**: "
                     f"{len(xref.get('executed_classes_set', set()))}")
        lines.append(f"- **First native method on execution path**: "
                     f"{format_first_native(xref.get('first_native_method'))}")
        lines.append(f"- **JNI distance**: {xref.get('jni_distance')}")
    else:
        lines.append("- **Execution log**: not found")
    lines.append("")

    # ----- 2. Per-DEX Breakdown -----
    lines.append("## 2. Per-DEX Native Method Breakdown")
    lines.append("")
    lines.append("| DEX file | Size (B) | Classes | Methods | Native methods "
                 "| Classes w/ native |")
    lines.append("|----------|---------:|--------:|--------:|---------------:|"
                 "-------------------:|")
    for dex_name, st in scan["dex_stats"].items():
        lines.append(
            f"| {dex_name} | {st['file_size_bytes']:,} | {st['classes']:,} | "
            f"{st['methods']:,} | {st['native_methods']} | "
            f"{st['classes_with_native']} |"
        )
    lines.append("")

    # ----- 3. Priority Distribution -----
    lines.append("## 3. Priority Distribution")
    lines.append("")
    lines.append("- **P0** — Called before or during Application init "
                 "(NativeLoader, ConnectionsManager, ApplicationLoader, "
                 "tgnet bootstrap).")
    lines.append("- **P1** — Called during Activity onCreate "
                 "(RLottie, SQLite, Intro, Utilities, AnimatedFileNative).")
    lines.append("- **P2** — Called during message send/receive "
                 "(VoIP, WebRTC, NativeByteBuffer, MediaController, "
                 "SecretChat, BotWebView).")
    lines.append("- **P3** — Rarely called (ExoPlayer decoders, Ffmpeg, "
                 "Flac, Opus, Vpx, Av1, mlkit).")
    lines.append("")
    pri_counts = defaultdict(int)
    for nm in scan['native_methods']:
        pri_counts[nm['priority']] += 1
    pri_on_path_counts = defaultdict(int)
    for nm in scan['native_methods']:
        if nm['on_execution_path']:
            pri_on_path_counts[nm['priority']] += 1
    lines.append("| Priority | Native methods | On execution path |")
    lines.append("|:--------:|---------------:|------------------:|")
    for pri in ("P0", "P1", "P2", "P3"):
        lines.append(f"| {pri} | {pri_counts.get(pri, 0)} | "
                     f"{pri_on_path_counts.get(pri, 0)} |")
    lines.append("")

    # ----- 4. Top Classes by Native-Method Count -----
    lines.append("## 4. Top Classes by Native-Method Count")
    lines.append("")
    lines.append("| Rank | Class | Native methods | Library (guess) | Priority |")
    lines.append("|-----:|-------|---------------:|-----------------|:--------:|")
    by_class = defaultdict(list)
    for nm in scan['native_methods']:
        by_class[nm['class']].append(nm)
    class_summary = sorted(by_class.items(),
                           key=lambda kv: (-len(kv[1]), kv[0]))
    for rank, (cls, items) in enumerate(class_summary[:25], 1):
        lib = guess_library(cls)
        pri = guess_priority(cls)
        lines.append(f"| {rank} | `{cls}` | {len(items)} | {lib} | {pri} |")
    lines.append("")

    # ----- 5. System.loadLibrary / System.load call sites -----
    lines.append("## 5. `System.loadLibrary` / `System.load` Call Sites")
    lines.append("")
    if not scan['load_library_sites']:
        lines.append("_(none found)_")
    else:
        lines.append("| Calling class | Calling method | DEX | PC | Target | "
                     "Library name | On path |")
        lines.append("|-------|--------|------|----:|--------|--------------|"
                     ":-------:|")
        # Sort: on-path first, then by (calling_class, calling_method, pc)
        sorted_sites = sorted(
            scan['load_library_sites'],
            key=lambda s: (not s['on_execution_path'],
                           s['calling_class'], s['calling_method'], s['pc'])
        )
        for s in sorted_sites:
            on_path = "yes" if s['on_execution_path'] else ""
            target = f"{s['target_class']}.{s['target_method']}"
            libname = s['library_name'].replace("|", "\\|")
            lines.append(
                f"| `{s['calling_class']}` | `{s['calling_method']}` | "
                f"{s['calling_dex']} | {s['pc']} | `{target}` | "
                f"`{libname}` | {on_path} |"
            )
    lines.append("")

    # ----- 6. NativeLoader.initNativeLibs call chain -----
    lines.append("## 6. `NativeLoader.initNativeLibs` Call Chain")
    lines.append("")
    if not scan['native_loader_init_sites']:
        lines.append("_(no `invoke-*` of `NativeLoader.initNativeLibs` found "
                     "anywhere in the APK — typically called via "
                     "`ApplicationLoader.postInitApplication`)_")
    else:
        lines.append("| Calling class | Calling method | DEX | PC | "
                     "On path |")
        lines.append("|-------|--------|------|----:|:-------:|")
        sorted_sites = sorted(
            scan['native_loader_init_sites'],
            key=lambda s: (not s['on_execution_path'],
                           s['calling_class'], s['calling_method'], s['pc'])
        )
        for s in sorted_sites:
            on_path = "yes" if s['on_execution_path'] else ""
            lines.append(
                f"| `{s['calling_class']}` | `{s['calling_method']}` | "
                f"{s['calling_dex']} | {s['pc']} | {on_path} |"
            )
    lines.append("")

    # ----- 7. Static call chain (depth-0) -----
    lines.append("## 7. Static Native Call Chain (Depth-0)")
    lines.append("")
    lines.append(
        "For every method that *did* enter the EXP-046 baseline log, "
        "scans its bytecode for `invoke-*` to a native method or a "
        "framework loadLibrary method.  This is the set of potential "
        "native calls reachable directly from the executed methods."
    )
    lines.append("")
    if not static_chain:
        lines.append("_(none found)_")
    else:
        lines.append("| # | Caller class | Caller method | Caller PC | "
                     "Target class | Target method | Kind | String arg | "
                     "Caller first-seen index |")
        lines.append("|---:|-------|--------|----:|--------|--------|------|"
                     "------|----:|")
        for i, e in enumerate(static_chain, 1):
            string_arg = (e.get('string_argument') or "").replace("|", "\\|")
            lines.append(
                f"| {i} | `{e['caller_class']}` | `{e['caller_method']}` | "
                f"{e['caller_pc']} | `{e['target_class']}` | "
                f"`{e['target_method']}` | {e['target_kind']} | "
                f"`{string_arg}` | {e['caller_first_seen_index']} |"
            )
    lines.append("")

    # ----- 8. Full Native Method Inventory (sorted by priority) -----
    lines.append("## 8. Full Native Method Inventory")
    lines.append("")
    lines.append(
        f"All {scan['total_native_methods']} native methods, sorted by "
        "(priority, class, method)."
    )
    lines.append("")
    lines.append("| Priority | Class | Method | Shorty | Full signature | "
                 "Access flags | DEX | On path | JNI symbol (info) |")
    lines.append("|:--------:|-------|--------|--------|-----------------|"
                 "--------------|------|:-------:|------|")
    sorted_inv = sorted(
        scan['native_methods'],
        key=lambda e: (PRI_ORDER.get(e['priority'], 9),
                       e['class'],
                       e['method']),
    )
    for e in sorted_inv:
        cls = e['class'].replace("|", "\\|")
        mtd = e['method'].replace("|", "\\|")
        sho = e['shorty'].replace("|", "\\|")
        sig = e['full_signature'].replace("|", "\\|")
        aflg = e['access_flags_string']
        on_path = "yes" if e['on_execution_path'] else ""
        jni_sym = e['jni_symbol']
        lines.append(
            f"| {e['priority']} | `{cls}` | `{mtd}` | `{sho}` | `{sig}` | "
            f"{aflg} | {e['dex']} | {on_path} | `{jni_sym}` |"
        )
    lines.append("")

    # ----- 9. Methodology -----
    lines.append("## 9. Methodology")
    lines.append("")
    lines.append("1. APK opened as ZIP; each `classesN.dex` read into memory.")
    lines.append("2. DEX header parsed at offset 0 (112 bytes, little-endian).")
    lines.append("3. `string_ids[]`, `type_ids[]`, `proto_ids[]`, "
                 "`method_ids[]` and `class_defs[]` sections loaded.")
    lines.append("4. For each `class_def_item`, `class_data_off` resolved and "
                 "the ULEB128-encoded `class_data_item` parsed: "
                 "`static_fields_size`, `instance_fields_size`, "
                 "`direct_methods_size`, `virtual_methods_size`, then the "
                 "encoded field / method arrays.")
    lines.append("5. Both `direct_methods[]` and `virtual_methods[]` lists "
                 "walked. For each `encoded_method`, "
                 "`access_flags & 0x100` decides if the method is native.")
    lines.append("6. Native methods are resolved back to (class, name, shorty, "
                 "full-signature) via `method_ids[]` → `proto_ids[]` → "
                 "`type_ids[]` → `string_ids[]`. The full signature walks "
                 "the proto's `parameters_off` type_list for parameter types.")
    lines.append("7. JNI symbol name is computed by mangling the class and "
                 "method name per the JNI specification "
                 "(`Java_<class>_<method>`). Note: Telegram's "
                 "`libtmessages.49.so` registers most of its native methods "
                 "at runtime via `RegisterNatives()` in `JNI_OnLoad`, so "
                 "many JNI symbols are not present as `Java_*` ELF exports.")
    lines.append("8. `System.loadLibrary` / `System.load` call sites found "
                 "by walking the `method_ids[]` table for any method "
                 "reference whose class is `Ljava/lang/System;` or "
                 "`Ljava/lang/Runtime;` and whose name is `loadLibrary`, "
                 "`load`, `loadLibrary0`, or `load0`, then scanning every "
                 "method's bytecode for `invoke-*` instructions targeting "
                 "those method_idx values. The const-string library-name "
                 "argument is recovered by a backward scan from the "
                 "invoke site for `const-string` writes to the argument "
                 "register.")
    lines.append("9. `NativeLoader.initNativeLibs` call sites found the same "
                 "way; this is the Java-side bootstrap that calls "
                 "`System.loadLibrary(\"tmessages.49\")`.")
    lines.append("10. Priority bucketing is heuristic, based on the declaring-"
                 "class descriptor (see the python source for the exact "
                 "keyword tables). P0 = startup bootstrap, P1 = Activity "
                 "onCreate, P2 = message send/receive, P3 = rare.")
    lines.append("11. `on_execution_path` is set to True if the declaring "
                 "class of the native method appears among the 154 unique "
                 "method entries in `run/exp046_baseline.log`. (Native "
                 "methods themselves are not yet invoked by the runtime, "
                 "so we match on class, not on method.)")
    lines.append("12. The static call chain (depth-0) re-scans each method "
                 "that entered the log for any `invoke-*` targeting a native "
                 "method, a framework loadLibrary method, or "
                 "`NativeLoader.initNativeLibs`.")
    lines.append("")

    return "\n".join(lines)


def format_first_native(first_native: Optional[Dict]) -> str:
    if not first_native:
        return "_(none — runtime does not yet invoke native methods)_"
    return f"`{first_native['method']}` (index {first_native['index']})"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    if not os.path.exists(APK_PATH):
        print(f"ERROR: APK not found at {APK_PATH}", file=sys.stderr)
        return 2

    print(f"Scanning {APK_PATH} ...", file=sys.stderr)
    scan = scan_apk(APK_PATH)

    print(f"\nParsing execution log {EXEC_LOG_PATH} ...", file=sys.stderr)
    log_view = parse_execution_log(EXEC_LOG_PATH)

    print(f"Cross-referencing {len(scan['native_methods'])} native methods "
          f"against {len(log_view.get('unique_methods', []))} executed methods ...",
          file=sys.stderr)
    xref = cross_reference_with_log(scan, log_view)

    print(f"Building static call chain ...", file=sys.stderr)
    static_chain = static_native_call_chain(APK_PATH, scan, log_view)

    print(f"\nWriting {MD_PATH} ...", file=sys.stderr)
    md_text = render_markdown(scan, log_view, xref, static_chain)
    with open(MD_PATH, "w", encoding="utf-8") as f:
        f.write(md_text)

    print(f"Writing {JSON_PATH} ...", file=sys.stderr)
    json_payload = {
        'apk': scan['apk'],
        'execution_log': EXEC_LOG_PATH,
        'execution_log_exists': log_view.get('log_exists', False),
        'total_native_methods': scan['total_native_methods'],
        'total_load_library_sites': scan['total_load_library_sites'],
        'total_native_loader_init_sites': scan['total_native_loader_init_sites'],
        'unique_methods_entered': len(log_view.get('unique_methods', [])),
        'unique_classes_entered': len(xref.get('executed_classes_set', set())),
        'first_native_method_on_path': xref.get('first_native_method'),
        'jni_distance': xref.get('jni_distance'),
        'dex_stats': scan['dex_stats'],
        'priority_distribution': dict(sorted(
            {p: sum(1 for nm in scan['native_methods']
                    if nm['priority'] == p)
             for p in ('P0', 'P1', 'P2', 'P3')}.items()
        )),
        'native_methods_on_path_count': sum(
            1 for nm in scan['native_methods'] if nm['on_execution_path']
        ),
        'load_library_sites': scan['load_library_sites'],
        'native_loader_init_sites': scan['native_loader_init_sites'],
        'static_call_chain': static_chain,
        'native_methods': scan['native_methods'],
    }
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(json_payload, f, indent=2, ensure_ascii=False)

    print("\n=== Done ===", file=sys.stderr)
    print(f"  Total native methods:     "
          f"{scan['total_native_methods']}", file=sys.stderr)
    print(f"  P0 (startup path):        "
          f"{sum(1 for nm in scan['native_methods'] if nm['priority']=='P0')}",
          file=sys.stderr)
    print(f"  P1 (Activity onCreate):   "
          f"{sum(1 for nm in scan['native_methods'] if nm['priority']=='P1')}",
          file=sys.stderr)
    print(f"  P2 (msg send/recv):       "
          f"{sum(1 for nm in scan['native_methods'] if nm['priority']=='P2')}",
          file=sys.stderr)
    print(f"  P3 (rare):                "
          f"{sum(1 for nm in scan['native_methods'] if nm['priority']=='P3')}",
          file=sys.stderr)
    print(f"  Native methods on path:   "
          f"{sum(1 for nm in scan['native_methods'] if nm['on_execution_path'])}",
          file=sys.stderr)
    print(f"  loadLibrary sites:        "
          f"{scan['total_load_library_sites']}", file=sys.stderr)
    print(f"  NativeLoader.init sites:  "
          f"{scan['total_native_loader_init_sites']}", file=sys.stderr)
    print(f"  Static chain entries:     "
          f"{len(static_chain)}", file=sys.stderr)
    print(f"  Markdown written to:      {MD_PATH}", file=sys.stderr)
    print(f"  JSON written to:          {JSON_PATH}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
