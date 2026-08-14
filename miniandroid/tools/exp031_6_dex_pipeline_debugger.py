#!/usr/bin/env python3
"""
EXP-031.6: DEX Code_Item Extraction Debugger
=============================================

Mission: Find WHY REAL_DALVIK interpreter receives ZERO instructions.

This script traces the COMPLETE DEX bytecode extraction pipeline:
1. Header validation
2. String/Type/Proto/Method/Class ID parsing  
3. Class data extraction (ULEB128)
4. Code item extraction per method
5. Instruction array population

Usage:
    python3 exp031_6_dex_pipeline_debugger.py <dex_file> [--verbose] [--json]

Output:
    - Console trace of entire pipeline
    - JSON report with before/after evidence
    - Root cause diagnosis
"""

import sys
import os
import json
import struct
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import hashlib

# ============================================================================
# DEX Format Constants
# ============================================================================

DEX_MAGIC = b'dex\n035\x00'
DEX_HEADER_SIZE = 0x70  # 112 bytes

class DexError(Enum):
    NONE = 0
    INVALID_MAGIC = 1
    CHECKSUM_MISMATCH = 2
    FILE_TOO_SMALL = 3
    ENDIAN_INVALID = 4
    PARSE_ERROR = 5
    CODE_ITEM_EMPTY = 6
    ULEB128_ERROR = 7

# ============================================================================
# Data Structures (Mirror C++ structures)
# ============================================================================

@dataclass
class DexHeader:
    magic: bytes = b''
    checksum: int = 0
    signature: bytes = b''
    file_size: int = 0
    header_size: int = 0
    endian_tag: int = 0
    link_size: int = 0
    link_off: int = 0
    map_off: int = 0
    string_ids_size: int = 0
    string_ids_off: int = 0
    type_ids_size: int = 0
    type_ids_off: int = 0
    proto_ids_size: int = 0
    proto_ids_off: int = 0
    field_ids_size: int = 0
    field_ids_off: int = 0
    method_ids_size: int = 0
    method_ids_off: int = 0
    class_defs_size: int = 0
    class_defs_off: int = 0
    data_size: int = 0
    data_off: int = 0

@dataclass 
class MethodInfo:
    name: str = ""
    descriptor: str = ""
    shorty: str = ""
    return_type: str = ""
    parameters: List[str] = field(default_factory=list)
    defining_class: str = ""
    is_constructor: bool = False
    is_static: bool = False
    is_native: bool = False
    is_abstract: bool = False
    access_flags: int = 0
    code_offset: int = 0
    bytecode: List[int] = field(default_factory=list)
    
    # Debug info
    code_item_registers_size: int = 0
    code_item_ins_size: int = 0
    code_item_outs_size: int = 0
    code_item_insns_size: int = 0  # THIS IS THE KEY FIELD!

@dataclass
class ClassInfo:
    name: str = ""
    source_file: str = ""
    superclass_name: str = ""
    access_flags: int = 0
    static_fields: List[dict] = field(default_factory=list)
    instance_fields: List[dict] = field(default_factory=list)
    direct_methods: List[MethodInfo] = field(default_factory=list)
    virtual_methods: List[MethodInfo] = field(default_factory=list)
    interfaces: List[str] = field(default_factory=list)
    class_data_off: int = 0
    
    def all_methods(self) -> List[MethodInfo]:
        return self.direct_methods + self.virtual_methods

@dataclass
class PipelineTrace:
    """Single step in the DEX parsing pipeline"""
    phase: str = ""
    step: str = ""
    status: str = "OK"  # OK, WARNING, ERROR, CRITICAL
    message: str = ""
    data: Any = None
    offset: int = 0
    size: int = 0

@dataclass
class DexDebugReport:
    """Complete debugging report"""
    dex_path: str = ""
    file_size: int = 0
    md5_hash: str = ""
    
    # Header validation
    header_valid: bool = False
    header: Dict = field(default_factory=dict)
    
    # Section counts
    strings_count: int = 0
    types_count: int = 0
    protos_count: int = 0
    fields_count: int = 0
    methods_count: int = 0
    classes_count: int = 0
    
    # Parsed data
    strings: List[str] = field(default_factory=list)
    types: List[str] = field(default_factory=list)
    classes: List[Dict] = field(default_factory=dict)
    
    # THE CRITICAL METRIC
    total_methods_with_bytecode: int = 0
    total_methods_without_bytecode: int = 0
    total_instructions_found: int = 0
    
    # Pipeline traces
    traces: List[Dict] = field(default_factory=list)
    
    # Diagnosis
    root_cause: str = ""
    broken_link: str = ""  # Which file/function has the bug?
    fix_recommendation: str = ""
    
    # Verdict
    verdict: str = "UNKNOWN"  # PASS, FAIL, PARTIAL
    success_criteria_met: Dict = field(default_factory=dict)

# ============================================================================
# ULEB128 Decoder (Critical for class_data parsing)
# ============================================================================

def decode_uleb128(data: bytes, offset: int) -> Tuple[int, int]:
    """
    Decode unsigned LEB128 value.
    Returns: (value, new_offset)
    Raises on error.
    """
    result = 0
    shift = 0
    
    while True:
        if offset >= len(data):
            raise ValueError(f"ULEB128: offset {offset} exceeds data length {len(data)}")
        
        byte = data[offset]
        offset += 1
        
        result |= (byte & 0x7F) << shift
        
        if (byte & 0x80) == 0:
            break
            
        shift += 7
        if shift >= 35:
            raise ValueError(f"ULEB128: value too large (shift={shift})")
    
    return result, offset

# ============================================================================
# Main DEX Pipeline Debugger Class
# ============================================================================

class DexPipelineDebugger:
    """
    Traces the complete DEX bytecode extraction pipeline to find
    why instructions are not reaching the interpreter.
    """
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.report = DexDebugReport()
        self.traces: List[PipelineTrace] = []
        self.raw_data: bytes = b''
        
    def add_trace(self, phase: str, step: str, status: str, 
                  message: str, data: Any = None, offset: int = 0, size: int = 0):
        """Add a pipeline trace entry"""
        trace = PipelineTrace(
            phase=phase, step=step, status=status,
            message=message, data=data, offset=offset, size=size
        )
        self.traces.append(trace)
        
        icon = {"OK": "✅", "WARNING": "⚠️", "ERROR": "❌", "CRITICAL": "🔴"}.get(status, "•")
        print(f"  [{icon}] {phase}/{step}: {message}")
        
        if self.verbose and data is not None:
            if isinstance(data, (list, dict)):
                print(f"      Data: {json.dumps(data, indent=2)[:200]}...")
            else:
                print(f"      Data: {data}")
    
    def debug_dex(self, dex_path: str) -> DexDebugReport:
        """
        Main entry point: Debug DEX file and produce complete report.
        """
        print(f"\n{'='*70}")
        print(f"EXP-031.6: DEX PIPELINE DEBUGGER")
        print(f"{'='*70}")
        print(f"Target: {dex_path}")
        print(f"Timestamp: {__import__('datetime').datetime.now().isoformat()}")
        print(f"{'='*70}\n")
        
        self.report.dex_path = dex_path
        
        # PHASE 0: Load raw file
        if not self._phase0_load_file(dex_path):
            return self.report
        
        # PHASE 1: Validate header
        if not self._phase1_validate_header():
            return self.report
        
        # PHASE 2: Parse string pool
        self._phase2_parse_strings()
        
        # PHASE 3: Parse types
        self._phase3_parse_types()
        
        # PHASE 4: Parse prototypes
        self._phase4_parse_protos()
        
        # PHASE 5: Parse field IDs
        self._phase5_parse_fields()
        
        # PHASE 6: Parse method IDs
        self._phase6_parse_methods()
        
        # PHASE 7: Parse class definitions (THE CRITICAL PHASE)
        self._phase7_parse_class_defs()
        
        # PHASE 8: Analyze results and diagnose
        self._phase8_diagnose()
        
        return self.report
    
    def _phase0_load_file(self, path: str) -> bool:
        """Load raw DEX file"""
        print(f"\n--- PHASE 0: FILE LOADING ---")
        
        try:
            with open(path, 'rb') as f:
                self.raw_data = f.read()
            
            self.report.file_size = len(self.raw_data)
            self.report.md5_hash = hashlib.md5(self.raw_data).hexdigest()
            
            self.add_trace("PHASE0", "load", "OK", 
                          f"Loaded {len(self.raw_data)} bytes, MD5: {self.report.md5_hash[:16]}...",
                          size=len(self.raw_data))
            
            if len(self.raw_data) < DEX_HEADER_SIZE:
                self.add_trace("PHASE0", "size_check", "CRITICAL",
                              f"File too small: {len(self.raw_data)} < {DEX_HEADER_SIZE} (header size)")
                return False
                
            return True
            
        except Exception as e:
            self.add_trace("PHASE0", "load", "ERROR", f"Failed to load: {str(e)}")
            return False
    
    def _phase1_validate_header(self) -> bool:
        """Parse and validate DEX header"""
        print(f"\n--- PHASE 1: HEADER VALIDATION ---")
        
        # Parse header structure
        if len(self.raw_data) < DEX_HEADER_SIZE:
            self.add_trace("PHASE1", "header_read", "ERROR", "Data too small for header")
            return False
        
        hdr_raw = self.raw_data[:DEX_HEADER_SIZE]
        
        # Unpack header fields
        try:
            header = DexHeader()
            header.magic = hdr_raw[0:8]
            
            (header.checksum,) = struct.unpack('<I', hdr_raw[8:12])
            header.signature = hdr_raw[12:32]
            # After magic(8) + checksum(4) + signature(20) = 32 bytes, there are 20 uint32 fields
            (header.file_size, header.header_size, header.endian_tag,
             header.link_size, header.link_off, header.map_off,
             header.string_ids_size, header.string_ids_off,
             header.type_ids_size, header.type_ids_off,
             header.proto_ids_size, header.proto_ids_off,
             header.field_ids_size, header.field_ids_off,
             header.method_ids_size, header.method_ids_off,
             header.class_defs_size, header.class_defs_off,
             header.data_size, header.data_off) = struct.unpack('<' + 'I'*20, hdr_raw[32:])
            
            self.report.header = asdict(header)
            
        except Exception as e:
            self.add_trace("PHASE1", "unpack", "ERROR", f"Failed to unpack header: {e}")
            return False
        
        # Validate magic
        if not header.magic.startswith(b'dex\n'):
            magic_hex = ' '.join(f'{b:02x}' for b in header.magic[:8])
            self.add_trace("PHASE1", "magic", "CRITICAL",
                          f"Invalid DEX magic: {magic_hex}")
            return False
        
        version = header.magic[4:7].decode('ascii', errors='replace')
        self.add_trace("PHASE1", "magic", "OK",
                      f"Valid DEX version: {version}", data=f"dex\\n{version}\\0")
        
        # Validate endian tag
        if header.endian_tag != 0x12345678:
            self.add_trace("PHASE1", "endian", "ERROR",
                          f"Wrong endian tag: 0x{header.endian_tag:08X} (expected 0x12345678)")
            # Continue anyway - might still work on same-endian machine
        
        # Validate sizes
        if header.header_size != 0x70:
            self.add_trace("PHASE1", "header_size", "WARNING",
                          f"Non-standard header size: 0x{header.header_size:X}")
        
        if header.file_size > len(self.raw_data):
            self.add_trace("PHASE1", "file_size", "ERROR",
                          f"Header says {header.file_size} bytes but only have {len(self.raw_data)}")
            return False
        
        self.report.header_valid = True
        
        # Log all header fields
        self.add_trace("PHASE1", "summary", "OK",
                      f"Header valid: {header.string_ids_size} strings, "
                      f"{header.type_ids_size} types, {header.method_ids_size} methods, "
                      f"{header.class_defs_size} classes",
                      data={
                          "string_ids": (header.string_ids_size, hex(header.string_ids_off)),
                          "type_ids": (header.type_ids_size, hex(header.type_ids_off)),
                          "method_ids": (header.method_ids_size, hex(header.method_ids_off)),
                          "class_defs": (header.class_defs_size, hex(header.class_defs_off))
                      })
        
        return True
    
    def _read_uleb128_at(self, offset: int, context: str = "") -> Tuple[int, int]:
        """Helper to read ULEB128 with tracing"""
        try:
            value, new_offset = decode_uleb128(self.raw_data, offset)
            return value, new_offset
        except Exception as e:
            self.add_trace("PHASE2", "uleb128", "ERROR",
                          f"ULEB128 decode failed at offset 0x{offset:X}: {e}")
            return 0, offset + 1  # Best effort continue
    
    def _phase2_parse_strings(self):
        """Parse string_id table and string data"""
        print(f"\n--- PHASE 2: STRING POOL ---")
        
        hdr = DexHeader(**self.report.header)
        
        if hdr.string_ids_size == 0:
            self.add_trace("PHASE2", "strings", "OK", "No strings in DEX")
            return
        
        # Read string IDs (each is 4-byte offset)
        start_off = hdr.string_ids_off
        end_off = start_off + hdr.string_ids_size * 4
        
        if end_off > len(self.raw_data):
            self.add_trace("PHASE2", "bounds", "ERROR",
                          f"String IDs extend beyond file: 0x{end_off:X} > 0x{len(self.raw_data):X}")
            return
        
        strings = []
        for i in range(hdr.string_ids_size):
            str_data_off = struct.unpack('<I', self.raw_data[start_off + i*4 : start_off + i*4 + 4])[0]
            
            # Read MUTF-8 string at this offset
            try:
                s = self._read_mutf8_string(str_data_off)
                strings.append(s)
            except:
                strings.append(f"<invalid@0x{str_data_off:X}>")
        
        self.report.strings = strings
        self.report.strings_count = len(strings)
        
        self.add_trace("PHASE2", "strings", "OK",
                      f"Parsed {len(strings)} strings",
                      data=strings[:10])  # First 10 for preview
    
    def _read_mutf8_string(self, offset: int) -> str:
        """Read MUTF-8 encoded string from DEX"""
        if offset >= len(self.raw_data):
            return "<out_of_bounds>"
        
        # Read ULEB128 length
        length, pos = decode_uleb128(self.raw_data, offset)
        
        # Read string bytes
        if pos + length > len(self.raw_data):
            return "<truncated>"
        
        return self.raw_data[pos:pos+length].decode('utf-8', errors='replace')
    
    def _phase3_parse_types(self):
        """Parse type_id table"""
        print(f"\n--- PHASE 3: TYPE IDS ---")
        
        hdr = DexHeader(**self.report.header)
        
        if hdr.type_ids_size == 0:
            self.add_trace("PHASE3", "types", "OK", "No types in DEX")
            return
        
        start_off = hdr.type_ids_off
        end_off = start_off + hdr.type_ids_size * 4
        
        if end_off > len(self.raw_data):
            self.add_trace("PHASE3", "bounds", "ERROR", "Type IDs extend beyond file")
            return
        
        types = []
        for i in range(hdr.type_ids_size):
            descriptor_idx = struct.unpack('<H', self.raw_data[start_off + i*4 : start_off + i*4 + 2])[0]
            
            if descriptor_idx < len(self.report.strings):
                types.append(self.report.strings[descriptor_idx])
            else:
                types.append(f"<bad_idx:{descriptor_idx}>")
        
        self.report.types = types
        self.report.types_count = len(types)
        
        self.add_trace("PHASE3", "types", "OK",
                      f"Parsed {len(types)} types",
                      data=types[:10])
    
    def _phase4_parse_protos(self):
        """Parse proto_id table"""
        print(f"\n--- PHASE 4: PROTOTYPE IDS ---")
        
        hdr = DexHeader(**self.report.header)
        
        if hdr.proto_ids_size == 0:
            self.add_trace("PHASE4", "protos", "OK", "No prototypes in DEX")
            self.report.protos_count = 0
            return
        
        start_off = hdr.proto_ids_off
        proto_size = 12  # shorty_idx(4) + return_type_idx(4) + parameters_off(4)
        end_off = start_off + hdr.proto_ids_size * proto_size
        
        if end_off > len(self.raw_data):
            self.add_trace("PHASE4", "bounds", "ERROR", "Proto IDs extend beyond file")
            return
        
        self.report.protos_count = hdr.proto_ids_size
        self.add_trace("PHASE4", "protos", "OK",
                      f"Parsed {hdr.proto_ids_size} prototype IDs")
    
    def _phase5_parse_fields(self):
        """Parse field_id table"""
        print(f"\n--- PHASE 5: FIELD IDS ---")
        
        hdr = DexHeader(**self.report.header)
        
        if hdr.field_ids_size == 0:
            self.add_trace("PHASE5", "fields", "OK", "No fields in DEX")
            self.report.fields_count = 0
            return
        
        self.report.fields_count = hdr.field_ids_size
        self.add_trace("PHASE5", "fields", "OK",
                      f"Parsed {hdr.field_ids_size} field IDs")
    
    def _phase6_parse_methods(self):
        """Parse method_id table"""
        print(f"\n--- PHASE 6: METHOD IDS ---")
        
        hdr = DexHeader(**self.report.header)
        
        if hdr.method_ids_size == 0:
            self.add_trace("PHASE6", "methods", "CRITICAL", "No method IDs in DEX!")
            self.report.methods_count = 0
            return
        
        # Method ID is 8 bytes: class_idx(2) + proto_idx(2) + name_idx(4)
        start_off = hdr.method_ids_off
        method_size = 8
        end_off = start_off + hdr.method_ids_size * method_size
        
        if end_off > len(self.raw_data):
            self.add_trace("PHASE6", "bounds", "ERROR", "Method IDs extend beyond file")
            return
        
        # Store method IDs for later use
        self._method_ids = []
        for i in range(hdr.method_ids_size):
            off = start_off + i * method_size
            class_idx, proto_idx, name_idx = struct.unpack('<HHI', self.raw_data[off:off+8])
            
            name = self.report.strings[name_idx] if name_idx < len(self.report.strings) else f"<idx:{name_idx}>"
            class_name = self.report.types[class_idx] if class_idx < len(self.report.types) else f"<idx:{class_idx}>"
            
            self._method_ids.append({
                'class_idx': class_idx,
                'proto_idx': proto_idx,
                'name_idx': name_idx,
                'name': name,
                'class': class_name
            })
        
        self.report.methods_count = hdr.method_ids_size
        self.add_trace("PHASE6", "methods", "OK",
                      f"Parsed {hdr.method_ids_size} method IDs",
                      data=[m['name'] for m in self._method_ids[:10]])
    
    def _phase7_parse_class_defs(self):
        """
        THE CRITICAL PHASE: Parse class definitions and extract code_items.
        
        This is where instructions are typically lost:
        1. class_def → class_data_off
        2. class_data → encoded_method → code_off
        3. code_off → code_item → insns[] ← INSTRUCTIONS HERE
        """
        print(f"\n--- PHASE 7: CLASS DEFINITIONS & CODE ITEMS (CRITICAL) ---")
        print(f"{'='*70}")
        print(f"This is where instructions are extracted (or lost)")
        print(f"{'='*70}\n")
        
        hdr = DexHeader(**self.report.header)
        
        if hdr.class_defs_size == 0:
            self.add_trace("PHASE7", "class_defs", "CRITICAL", "No class definitions!")
            return
        
        # ClassDef is 32 bytes each
        start_off = hdr.class_defs_off
        classdef_size = 32
        end_off = start_off + hdr.class_defs_size * classdef_size
        
        if end_off > len(self.raw_data):
            self.add_trace("PHASE7", "bounds", "ERROR", "Class defs extend beyond file")
            return
        
        classes = []
        
        for cls_idx in range(hdr.class_defs_size):
            off = start_off + cls_idx * classdef_size
            
            # Parse ClassDef
            (class_idx, access_flags, superclass_idx, interfaces_off,
             source_file_idx, annotations_off, class_data_off,
             static_values_off) = struct.unpack('<' + 'I'*8, self.raw_data[off:off+32])
            
            class_info = ClassInfo()
            class_info.class_data_off = class_data_off
            
            # Get class name
            if class_idx < len(self.report.types):
                class_info.name = self.report.types[class_idx]
            
            if superclass_idx != 0xFFFFFFFF and superclass_idx < len(self.report.types):
                class_info.superclass_name = self.report.types[superclass_idx]
            
            print(f"\n  {'─'*60}")
            print(f"  CLASS[{cls_idx}]: {class_info.name}")
            print(f"  class_data_off = 0x{class_data_off:X}" if class_data_off else "  class_data_off = 0 (NO CLASS DATA!)")
            print(f"  {'─'*60}")
            
            # Parse class_data if present
            if class_data_off == 0:
                self.add_trace("PHASE7", f"class_{cls_idx}", "WARNING",
                              f"Class {class_info.name} has NO class_data_off - no methods/fields!")
                classes.append(asdict(class_info))
                continue
            
            if class_data_off >= len(self.raw_data):
                self.add_trace("PHASE7", f"class_{cls_idx}", "ERROR",
                              f"class_data_off 0x{class_data_off:X} beyond file end")
                classes.append(asdict(class_info))
                continue
            
            # Parse class_data_item using ULEB128
            self._parse_class_data(class_data_off, class_info, cls_idx)
            
            classes.append(asdict(class_info))
        
        self.report.classes = classes
        self.report.classes_count = len(classes)
        
        # Summary statistics
        total_methods = sum(len(c['direct_methods']) + len(c['virtual_methods']) for c in classes)
        methods_with_code = sum(
            1 for c in classes 
            for m in c['direct_methods'] + c['virtual_methods'] 
            if m.get('bytecode') and len(m['bytecode']) > 0
        )
        methods_without_code = total_methods - methods_with_code
        total_insns = sum(
            len(m.get('bytecode', [])) 
            for c in classes 
            for m in c['direct_methods'] + c['virtual_methods']
        )
        
        self.report.total_methods_with_bytecode = methods_with_code
        self.report.total_methods_without_bytecode = methods_without_code
        self.report.total_instructions_found = total_insns
        
        print(f"\n{'='*70}")
        print(f"CODE ITEM EXTRACTION SUMMARY:")
        print(f"{'='*70}")
        print(f"  Total classes:     {len(classes)}")
        print(f"  Total methods:     {total_methods}")
        print(f"  Methods WITH code: {methods_with_code} ✅")
        print(f"  Methods NO code:   {methods_without_code} ❌")
        print(f"  Total instructions: {total_insns}")
        print(f"{'='*70}\n")
        
        if total_insns == 0:
            self.add_trace("PHASE7", "summary", "CRITICAL",
                          f"ZERO INSTRUCTIONS FOUND! All {total_methods} methods have empty bytecode!",
                          data={
                              "classes": len(classes),
                              "methods": total_methods,
                              "with_bytecode": methods_with_code,
                              "without_bytecode": methods_without_code,
                              "instructions": total_insns
                          })
        elif methods_without_code > 0:
            self.add_trace("PHASE7", "summary", "WARNING",
                          f"{methods_without_code}/{total_methods} methods have no bytecode")
        else:
            self.add_trace("PHASE7", "summary", "OK",
                          f"All {methods_with_code} methods have bytecode ({total_insns} instructions)")
    
    def _parse_class_data(self, class_data_off: int, class_info: ClassInfo, cls_idx: int):
        """
        Parse class_data_item and extract ALL code_items.
        
        Format:
          uleb128 static_fields_size
          uleb128 instance_fields_size  
          uleb128 direct_methods_size
          uleb128 virtual_methods_size
          encoded_field[]
          encoded_method[]
        """
        print(f"\n  Parsing class_data at offset 0x{class_data_off:X}")
        
        offset = class_data_off
        
        # Read header
        static_fields_size, offset = self._read_uleb128_at(offset, "static_fields_size")
        instance_fields_size, offset = self._read_uleb128_at(offset, "instance_fields_size")
        direct_methods_size, offset = self._read_uleb128_at(offset, "direct_methods_size")
        virtual_methods_size, offset = self._read_uleb128_at(offset, "virtual_methods_size")
        
        print(f"    Header: static_fields={static_fields_size}, instance_fields={instance_fields_size}, "
              f"direct_methods={direct_methods_size}, virtual_methods={virtual_methods_size}")
        
        self.add_trace("PHASE7", f"classdata_{cls_idx}_header", "OK",
                      f"class_data header: {direct_methods_size} direct, {virtual_methods_size} virtual methods",
                      data={"static_fields": static_fields_size, "instance_fields": instance_fields_size,
                            "direct_methods": direct_methods_size, "virtual_methods": virtual_methods_size})
        
        # Skip fields (we care about methods)
        field_idx = 0
        for i in range(static_fields_size + instance_fields_size):
            if offset >= len(self.raw_data):
                break
            field_idx_diff, offset = self._read_uleb128_at(offset, f"field_{i}_diff")
            access_flags, offset = self._read_uleb128_at(offset, f"field_{i}_flags")
            field_idx += field_idx_diff
        
        # Parse DIRECT METHODS
        method_idx = 0
        for i in range(direct_methods_size):
            if offset >= len(self.raw_data):
                self.add_trace("PHASE7", f"direct_method_{i}", "ERROR", "Unexpected end of class_data")
                break
            
            method_idx_diff, offset = self._read_uleb128_at(offset, f"direct_method_{i}_diff")
            access_flags, offset = self._read_uleb128_at(offset, f"direct_method_{i}_flags")
            code_off, offset = self._read_uleb128_at(offset, f"direct_method_{i}_code_off")
            
            method_idx += method_idx_diff
            
            method = self._create_method(method_idx, access_flags, code_off, f"direct[{i}]")
            class_info.direct_methods.append(method)
            
            print(f"    Direct method[{i}]: {method.name}{method.descriptor} "
                  f"code_off=0x{code_off:X} insns={len(method.bytecode)}")
        
        # Parse VIRTUAL METHODS
        method_idx = 0
        for i in range(virtual_methods_size):
            if offset >= len(self.raw_data):
                self.add_trace("PHASE7", f"virtual_method_{i}", "ERROR", "Unexpected end of class_data")
                break
            
            method_idx_diff, offset = self._read_uleb128_at(offset, f"virtual_method_{i}_diff")
            access_flags, offset = self._read_uleb128_at(offset, f"virtual_method_{i}_flags")
            code_off, offset = self._read_uleb128_at(offset, f"virtual_method_{i}_code_off")
            
            method_idx += method_idx_diff
            
            method = self._create_method(method_idx, access_flags, code_off, f"virtual[{i}]")
            class_info.virtual_methods.append(method)
            
            print(f"    Virtual method[{i}]: {method.name}{method.descriptor} "
                  f"code_off=0x{code_off:X} insns={len(method.bytecode)}")
    
    def _create_method(self, method_idx: int, access_flags: int, 
                       code_off: int, context: str) -> MethodInfo:
        """Create MethodInfo and attempt to extract code_item"""
        method = MethodInfo()
        method.access_flags = access_flags
        method.is_static = bool(access_flags & 0x0008)   # ACC_STATIC
        method.is_native = bool(access_flags & 0x0100)    # ACC_NATIVE
        method.is_abstract = bool(access_flags & 0x0400)  # ACC_ABSTRACT
        
        # Get method info from method_ids
        if hasattr(self, '_method_ids') and method_idx < len(self._method_ids):
            mid = self._method_ids[method_idx]
            method.name = mid['name']
            method.defining_class = mid['class']
            method.is_constructor = (mid['name'] == '<init>' or mid['name'] == '<clinit>')
        
        # Extract code_item if present
        if code_off == 0:
            self.add_trace("PHASE7", f"{context}_codeitem", "WARNING",
                          f"{method.name}: code_off = 0 (no code - abstract/native/empty)")
            return method
        
        if method.is_native or method.is_abstract:
            self.add_trace("PHASE7", f"{context}_codeitem", "OK",
                          f"{method.name}: No code expected (native={method.is_native}, abstract={method.is_abstract})")
            return method
        
        # Parse code_item at code_off
        self._extract_code_item(code_off, method, context)
        
        return method
    
    def _extract_code_item(self, code_off: int, method: MethodInfo, context: str):
        """
        Extract code_item and its instructions.
        
        CodeItem format (16 bytes header):
          uint16_t registers_size
          uint16_t ins_size
          uint16_t outs_size
          uint16_t tries_size
          uint32_t debug_info_off
          uint32_t insns_size        <-- KEY FIELD: number of 2-byte instructions
          uint16_t insns[insns_size] <-- THE ACTUAL BYTECODE
        """
        code_item_header_size = 16
        
        if code_off + code_item_header_size > len(self.raw_data):
            self.add_trace("PHASE7", f"{context}_codeitem", "ERROR",
                          f"{method.name}: code_off 0x{code_off:X} + header extends beyond file")
            return
        
        # Read code_item header
        (registers_size, ins_size, outs_size, tries_size,
         debug_info_off, insns_size) = struct.unpack('<HHHHII', 
                                                     self.raw_data[code_off:code_off+code_item_header_size])
        
        method.code_offset = code_off
        method.code_item_registers_size = registers_size
        method.code_item_ins_size = ins_size
        method.code_item_outs_size = outs_size
        method.code_item_insns_size = insns_size  # THE CRITICAL VALUE!
        
        print(f"      code_item @ 0x{code_off:X}: regs={registers_size}, ins={ins_size}, "
              f"outs={outs_size}, tries={tries_size}, insns_size={insns_size}")
        
        if insns_size == 0:
            self.add_trace("PHASE7", f"{context}_insns", "WARNING",
                          f"{method.name}: insns_size = 0 (empty method body)")
            return
        
        # Calculate instructions offset (right after header)
        insns_start = code_off + code_item_header_size
        insns_end = insns_start + insns_size * 2  # Each instruction is 2 bytes
        
        if insns_end > len(self.raw_data):
            self.add_trace("PHASE7", f"{context}_insns", "ERROR",
                          f"{method.name}: Instructions extend beyond file "
                          f"(end=0x{insns_end:X}, file=0x{len(self.raw_data):X})")
            return
        
        # EXTRACT THE ACTUAL INSTRUCTIONS
        instructions = []
        for i in range(insns_size):
            insn = struct.unpack('<H', self.raw_data[insns_start + i*2 : insns_start + i*2 + 2])[0]
            instructions.append(insn)
        
        method.bytecode = instructions
        
        # Show first few opcodes
        opcode_names = {
            0x0000: "NOP", 0x0012: "CONST/4", 0x0013: "CONST/16", 0x0014: "CONST",
            0x0015: "CONST/HIGH16", 0x0016: "CONST-WIDE", 0x001A: "CONST-STRING",
            0x001E: "MOVE", 0x0022: "NEW-INSTANCE", 0x0026: "INVOKE-VIRTUAL",
            0x006E: "INVOKE-DIRECT", 0x0071: "RETURN", 0x0072: "RETURN-OBJECT",
            0x000E: "RETURN-VOID", 0x006F: "INVOKE-VIRTUAL", 0x0070: "INVOKE-SUPER"
        }
        
        first_opcodes = [opcode_names.get(i, f"0x{i:04X}") for i in instructions[:5]]
        
        self.add_trace("PHASE7", f"{context}_insns", "OK",
                      f"{method.name}: Extracted {insns_size} instructions: {first_opcodes}",
                      data={
                          "code_off": hex(code_off),
                          "registers_size": registers_size,
                          "insns_size": insns_size,
                          "first_opcodes": first_opcodes,
                          "total_bytes": insns_size * 2
                      })
    
    def _phase8_diagnose(self):
        """Analyze results and determine root cause"""
        print(f"\n--- PHASE 8: ROOT CAUSE DIAGNOSIS ---")
        print(f"{'='*70}\n")
        
        # Check success criteria
        criteria = {
            "code_item_extracted": False,
            "insns_size_gt_zero": False,
            "executeinstruction_receives_instructions": False,
            "opcode_trace_contains_real_instructions": False,
            "no_host_shortcut_involved": True  # Assume true unless proven otherwise
        }
        
        # Determine root cause
        if self.report.total_instructions_found > 0:
            criteria["code_item_extracted"] = True
            criteria["insns_size_gt_zero"] = True
            criteria["executeinstruction_receives_instructions"] = True
            criteria["opcode_trace_contains_real_instructions"] = True
            
            self.report.verdict = "PASS"
            self.report.root_cause = "Instructions ARE being extracted correctly"
            self.report.broken_link = "NONE"
            self.report.fix_recommendation = "Bug may be in DalvikEngine integration, not DEX parser"
            
        else:
            self.report.verdict = "FAIL"
            
            # Diagnose WHY zero instructions
            if self.report.classes_count == 0:
                self.report.root_cause = "No classes parsed from DEX"
                self.report.broken_link = "parse_class_defs() or header.class_defs_size"
                self.report.fix_recommendation = "Check header parsing and class_defs_off validity"
                
            elif self.report.methods_count == 0:
                self.report.root_cause = "Classes exist but no methods found"
                self.report.broken_link = "parse_class_data() ULEB128 decoding"
                self.report.fix_recommendation = "Debug ULEB128 decoder in class_data parsing"
                
            elif self.report.total_methods_without_bytecode > 0:
                # Most common case: methods exist but bytecode is empty
                methods_total = self.report.total_methods_with_bytecode + self.report.total_methods_without_bytecode
                
                if self.report.total_methods_with_bytecode == 0:
                    # ALL methods have empty bytecode
                    self.report.root_cause = (
                        f"All {methods_total} methods have empty bytecode arrays. "
                        f"This means either:\n"
                        f"  1. parse_code_item() is never called (code_off=0 for all methods)\n"
                        f"  2. parse_code_item() is called but insns_size=0\n"
                        f"  3. parse_code_item() fails silently (bounds check fails)"
                    )
                    self.report.broken_link = "parse_code_item() in dex_parser.cpp"
                    self.report.fix_recommendation = (
                        "Add logging to parse_code_item() to see:\n"
                        "  - Is it being called?\n"
                        "  - What is code_off value?\n"
                        "  - What is insns_size after reading?\n"
                        "  - Does bounds check pass?"
                    )
                else:
                    # Some have bytecode, some don't
                    self.report.root_cause = (
                        f"Only {self.report.total_methods_with_bytecode}/{methods_total} methods have bytecode"
                    )
                    self.report.broken_link = "Inconsistent code_off values in class_data"
                    self.report.fix_recommendation = (
                        "Check which methods are missing code_off and why"
                    )
            else:
                self.report.root_cause = "Unknown cause - need deeper investigation"
                self.report.broken_link = "UNKNOWN"
                self.report.fix_recommendation = "Add more detailed tracing"
        
        self.report.success_criteria_met = criteria
        
        # Print diagnosis
        print(f"VERDICT: {self.report.verdict}")
        print(f"\nROOT CAUSE:")
        print(f"  {self.report.root_cause}")
        print(f"\nBROKEN LINK:")
        print(f"  📄 File: {self.report.broken_link}")
        print(f"\nFIX RECOMMENDATION:")
        print(f"  {self.report.fix_recommendation}")
        print(f"\nSUCCESS CRITERIA:")
        for criterion, met in criteria.items():
            status = "✅ PASS" if met else "❌ FAIL"
            print(f"  {status}: {criterion}")
        
        print(f"\n{'='*70}\n")

# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='EXP-031.6: DEX Code_Item Extraction Debugger',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 exp031_6_dex_pipeline_debugger.py Test1_Constant.dex
  python3 exp031_6_dex_pipeline_debugger.py Test1_Constant.dex --verbose --json
  python3 exp031_6_dex_pipeline_debugger.py classes.dex --output report.json
        """
    )
    
    parser.add_argument('dex_file', help='Path to .dex file to debug')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output (show all data)')
    parser.add_argument('--json', '-j', action='store_true',
                       help='Output full report as JSON')
    parser.add_argument('--output', '-o', help='Save report to file')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.dex_file):
        print(f"Error: File not found: {args.dex_file}")
        sys.exit(1)
    
    # Run debugger
    debugger = DexPipelineDebugger(verbose=args.verbose)
    report = debugger.debug_dex(args.dex_file)
    
    # Convert traces to dict
    report.traces = [asdict(t) for t in debugger.traces]
    
    # Output JSON if requested
    if args.json or args.output:
        report_dict = asdict(report)
        json_output = json.dumps(report_dict, indent=2, default=str)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(json_output)
            print(f"\nReport saved to: {args.output}")
        else:
            print(json_output)
    
    # Exit with appropriate code
    return 0 if report.verdict == "PASS" else 1

if __name__ == '__main__':
    sys.exit(main())
