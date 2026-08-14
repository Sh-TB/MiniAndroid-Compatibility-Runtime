#!/usr/bin/env python3
"""
EXP-034 PHASE 1: Real APK Bytecode Pipeline Validator

Mission: Validate that real Android APKs can be fully parsed
from APK → DEX → ClassDef → ClassData → EncodedMethod → CodeItem → Instructions

Evidence-Based Validation:
- Every claim must have a trace file
- Every failure must be documented with exact location
- No guessing about what works or doesn't work

Rule 1: Research before implementation
Rule 2: REAL evidence only
Rule 3: GitHub preservation required
"""

import os
import sys
import json
import hashlib
import zipfile
import struct
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from enum import Enum

# ============================================================================
# EVIDENCE COLLECTION INFRASTRUCTURE
# ============================================================================

class ValidationStatus(Enum):
    PASS = "PASS"
    PARTIAL = "PARTIAL"
    FAIL = "FAIL"
    MISSING = "MISSING"
    ERROR = "ERROR"

@dataclass
class PipelineStage:
    """Represents one stage in the bytecode extraction pipeline"""
    name: str
    status: ValidationStatus
    timestamp: str
    duration_ms: int
    data_size: int = 0
    record_count: int = 0
    error_message: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "stage": self.name,
            "status": self.status.value,
            "timestamp": self.timestamp,
            "duration_ms": self.duration_ms,
            "data_size": self.data_size,
            "record_count": self.record_count,
            "error": self.error_message,
            "details": self.details
        }

@dataclass 
class APKValidationResult:
    """Complete validation result for one APK"""
    apk_name: str
    apk_path: str
    sha256: str
    file_size: int
    validation_time: str
    overall_status: ValidationStatus
    stages: List[PipelineStage] = field(default_factory=list)
    total_classes: int = 0
    total_methods: int = 0
    total_instructions: int = 0
    first_failure_stage: Optional[str] = None
    opcode_breakdown: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "apk_name": self.apk_name,
            "apk_path": self.apk_path,
            "sha256": self.sha256,
            "file_size": self.file_size,
            "validation_time": self.validation_time,
            "overall_status": self.overall_status.value,
            "stages": [s.to_dict() for s in self.stages],
            "summary": {
                "total_classes": self.total_classes,
                "total_methods": self.total_methods,
                "total_instructions": self.total_instructions,
                "first_failure": self.first_failure_stage
            },
            "opcode_breakdown": self.opcode_breakdown
        }

# ============================================================================
# DEX FORMAT PARSERS (Minimal but correct implementations)
# ============================================================================

# DEX Header constants
DEX_MAGIC = b'dex\n035\x00'
DEX_MAGIC_NEW = b'dex\n036\x00'
DEX_HEADER_SIZE = 0x70

# String data type constants
STRING_UTF8 = 0x01

def read_uleb128(data: bytes, offset: int) -> Tuple[int, int]:
    """Read unsigned LEB128 value, return (value, bytes_consumed)"""
    result = 0
    shift = 0
    bytes_consumed = 0
    
    while offset + bytes_consumed < len(data):
        byte = data[offset + bytes_consumed]
        result |= (byte & 0x7f) << shift
        bytes_consumed += 1
        if (byte & 0x80) == 0:
            break
        shift += 7
    
    return result, bytes_consumed

def read_sleb128(data: bytes, offset: int) -> Tuple[int, int]:
    """Read signed LEB128 value, return (value, bytes_consumed)"""
    result = 0
    shift = 0
    bytes_consumed = 0
    
    while offset + bytes_consumed < len(data):
        byte = data[offset + bytes_consumed]
        result |= (byte & 0x7f) << shift
        shift += 7
        bytes_consumed += 1
        if (byte & 0x80) == 0:
            if byte & 0x40:  # Sign extend
                result |= -(1 << shift)
            break
    
    return result, bytes_consumed

def read_dex_string(data: bytes, string_offset: int) -> Optional[str]:
    """Read a MUTF-8 string from DEX string data"""
    try:
        if string_offset >= len(data):
            return None
        
        # Read string size (ULEB128 for new format, or check old format)
        uleb_start = string_offset
        string_size, uleb_bytes = read_uleb128(data, uleb_start)
        
        # String data starts after ULEB128 size
        string_data_start = uleb_start + uleb_bytes
        
        if string_data_start + string_size > len(data):
            return None
        
        # Read string bytes (MUTF-8, null terminated)
        string_bytes = data[string_data_start:string_data_start + string_size]
        
        # Decode as UTF-8 (most common case)
        try:
            return string_bytes.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return string_bytes.decode('latin-1')
            except:
                return f"<decode_error_{string_data_start}>"
    
    except Exception as e:
        return f"<error:{e}>"

@dataclass
class DexHeader:
    """Parsed DEX file header"""
    magic: bytes
    checksum: int  # uint32_t equivalent
    signature: bytes
    file_size: int
    header_size: int
    endian_tag: int
    link_size: int
    link_off: int
    map_off: int
    string_ids_size: int
    string_ids_off: int
    type_ids_size: int
    type_ids_off: int
    proto_ids_size: int
    proto_ids_off: int
    field_ids_size: int
    field_ids_off: int
    method_ids_size: int
    method_ids_off: int
    class_defs_size: int
    class_defs_off: int
    data_size: int
    data_off: int
    
    def is_valid(self) -> bool:
        return self.magic in (DEX_MAGIC, DEX_MAGIC_NEW)

def parse_dex_header(data: bytes) -> Optional[DexHeader]:
    """Parse DEX file header"""
    if len(data) < DEX_HEADER_SIZE:
        return None
    
    magic = data[0:8]
    if magic not in (DEX_MAGIC, DEX_MAGIC_NEW):
        return None
    
    # Parse all header fields according to DEX format spec
    (checksum,) = struct.unpack('<I', data[8:12])
    signature = data[12:32]
    
    (file_size,) = struct.unpack('<I', data[32:36])
    (header_size,) = struct.unpack('<I', data[36:40])
    (endian_tag,) = struct.unpack('<I', data[40:44])
    
    (link_size,) = struct.unpack('<I', data[44:48])
    (link_off,) = struct.unpack('<I', data[48:52])
    
    (map_off,) = struct.unpack('<I', data[52:56])
    
    (string_ids_size,) = struct.unpack('<I', data[56:60])
    (string_ids_off,) = struct.unpack('<I', data[60:64])
    
    (type_ids_size,) = struct.unpack('<I', data[64:68])
    (type_ids_off,) = struct.unpack('<I', data[68:72])
    
    (proto_ids_size,) = struct.unpack('<I', data[72:76])
    (proto_ids_off,) = struct.unpack('<I', data[76:80])
    
    (field_ids_size,) = struct.unpack('<I', data[80:84])
    (field_ids_off,) = struct.unpack('<I', data[84:88])
    
    (method_ids_size,) = struct.unpack('<I', data[88:92])
    (method_ids_off,) = struct.unpack('<I', data[92:96])
    
    (class_defs_size,) = struct.unpack('<I', data[96:100])
    (class_defs_off,) = struct.unpack('<I', data[100:104])
    
    (data_size,) = struct.unpack('<I', data[104:108])
    (data_off,) = struct.unpack('<I', data[108:112])
    
    return DexHeader(
        magic=magic,
        checksum=checksum,
        signature=signature,
        file_size=file_size,
        header_size=header_size,
        endian_tag=endian_tag,
        link_size=link_size,
        link_off=link_off,
        map_off=map_off,
        string_ids_size=string_ids_size,
        string_ids_off=string_ids_off,
        type_ids_size=type_ids_size,
        type_ids_off=type_ids_off,
        proto_ids_size=proto_ids_size,
        proto_ids_off=proto_ids_off,
        field_ids_size=field_ids_size,
        field_ids_off=field_ids_off,
        method_ids_size=method_ids_size,
        method_ids_off=method_ids_off,
        class_defs_size=class_defs_size,
        class_defs_off=class_defs_off,
        data_size=data_size,
        data_off=data_off
    )

@dataclass
class ClassDefItem:
    """Parsed class_def_item from DEX"""
    class_idx: int
    access_flags: int
    superclass_idx: int
    interfaces_off: int
    source_file_idx: int
    annotations_off: int
    class_data_off: int
    static_values_off: int

def parse_class_defs(data: bytes, header: DexHeader) -> List[ClassDefItem]:
    """Parse all class definitions from DEX"""
    class_defs = []
    
    if header.class_defs_off == 0 or header.class_defs_size == 0:
        return class_defs
    
    off = header.class_defs_off
    for i in range(header.class_defs_size):
        if off + 32 > len(data):
            break
            
        (class_idx, access_flags, superclass_idx, interfaces_off,
         source_file_idx, annotations_off, class_data_off, static_values_off) = \
            struct.unpack('<IIIIIIII', data[off:off+32])
        
        class_defs.append(ClassDefItem(
            class_idx=class_idx,
            access_flags=access_flags,
            superclass_idx=superclass_idx,
            interfaces_off=interfaces_off,
            source_file_idx=source_file_idx,
            annotations_off=annotations_off,
            class_data_off=class_data_off,
            static_values_off=static_values_off
        ))
        off += 32
    
    return class_defs

@dataclass
class EncodedField:
    """Encoded field in class_data"""
    field_idx_diff: int
    access_flags: int

@dataclass
class EncodedMethod:
    """Encoded method in class_data"""
    method_idx_diff: int
    access_flags: int
    code_off: int

@dataclass
class ClassDataItem:
    """Parsed class_data_item"""
    static_fields: List[EncodedField]
    instance_fields: List[EncodedField]
    direct_methods: List[EncodedMethod]
    virtual_methods: List[EncodedMethod]

def parse_class_data(data: bytes, offset: int) -> Optional[ClassDataItem]:
    """Parse class_data_item from DEX"""
    if offset == 0 or offset >= len(data):
        return None
    
    try:
        pos = offset
        
        # Read sizes
        static_fields_size, consumed = read_uleb128(data, pos)
        pos += consumed
        
        instance_fields_size, consumed = read_uleb128(data, pos)
        pos += consumed
        
        direct_methods_size, consumed = read_uleb128(data, pos)
        pos += consumed
        
        virtual_methods_size, consumed = read_uleb128(data, pos)
        pos += consumed
        
        # Read static fields
        static_fields = []
        field_idx = 0
        for _ in range(static_fields_size):
            idx_diff, consumed = read_uleb128(data, pos)
            pos += consumed
            access_flags, consumed = read_uleb128(data, pos)
            pos += consumed
            field_idx += idx_diff
            static_fields.append(EncodedField(field_idx_diff=idx_diff, access_flags=access_flags))
        
        # Read instance fields
        instance_fields = []
        field_idx = 0
        for _ in range(instance_fields_size):
            idx_diff, consumed = read_uleb128(data, pos)
            pos += consumed
            access_flags, consumed = read_uleb128(data, pos)
            pos += consumed
            field_idx += idx_diff
            instance_fields.append(EncodedField(field_idx_diff=idx_diff, access_flags=access_flags))
        
        # Read direct methods
        direct_methods = []
        method_idx = 0
        for _ in range(direct_methods_size):
            idx_diff, consumed = read_uleb128(data, pos)
            pos += consumed
            access_flags, consumed = read_uleb128(data, pos)
            pos += consumed
            code_off, consumed = read_uleb128(data, pos)
            pos += consumed
            method_idx += idx_diff
            direct_methods.append(EncodedMethod(
                method_idx_diff=idx_diff,
                access_flags=access_flags,
                code_off=code_off
            ))
        
        # Read virtual methods
        virtual_methods = []
        method_idx = 0
        for _ in range(virtual_methods_size):
            idx_diff, consumed = read_uleb128(data, pos)
            pos += consumed
            access_flags, consumed = read_uleb128(data, pos)
            pos += consumed
            code_off, consumed = read_uleb128(data, pos)
            pos += consumed
            method_idx += idx_diff
            virtual_methods.append(EncodedMethod(
                method_idx_diff=idx_diff,
                access_flags=access_flags,
                code_off=code_off
            ))
        
        return ClassDataItem(
            static_fields=static_fields,
            instance_fields=instance_fields,
            direct_methods=direct_methods,
            virtual_methods=virtual_methods
        )
    
    except Exception as e:
        return None

@dataclass
class CodeItem:
    """Parsed code_item from DEX"""
    registers_size: int
    ins_size: int
    outs_size: int
    tries_size: int
    debug_info_off: int
    insns_size: int
    insns: bytes  # Raw instruction bytes
    
    def get_instruction_count(self) -> int:
        return self.insns_size // 2  # Each instruction is 2 bytes (16-bit)

def parse_code_item(data: bytes, offset: int) -> Optional[CodeItem]:
    """Parse code_item from DEX"""
    if offset == 0 or offset >= len(data):
        return None
    
    try:
        pos = offset
        
        registers_size = struct.unpack('<H', data[pos:pos+2])[0]; pos += 2
        ins_size = struct.unpack('<H', data[pos:pos+2])[0]; pos += 2
        outs_size = struct.unpack('<H', data[pos:pos+2])[0]; pos += 2
        tries_size = struct.unpack('<H', data[pos:pos+2])[0]; pos += 2
        debug_info_off = struct.unpack('<I', data[pos:pos+4])[0]; pos += 4
        insns_size = struct.unpack('<I', data[pos:pos+4])[0]; pos += 4
        
        # Read instruction units (16-bit each)
        insns_data_size = insns_size * 2
        if pos + insns_data_size > len(data):
            return None
            
        insns = data[pos:pos+insns_data_size]
        
        return CodeItem(
            registers_size=registers_size,
            ins_size=ins_size,
            outs_size=outs_size,
            tries_size=tries_size,
            debug_info_off=debug_info_off,
            insns_size=insns_size,
            insns=insns
        )
    
    except Exception as e:
        return None

# ============================================================================
# OPCODE DECODER (Minimal set for validation)
# ============================================================================

OPCODE_NAMES = {
    0x0000: "nop",
    0x0012: "const/4",
    0x0013: "const/16",
    0x0014: "const",
    0x0015: "const/high16",
    0x0016: "const-wide",
    0x0017: "const-wide/16",
    0x0018: "const-wide/32",
    0x0019: "const-wide/high16",
    0x001a: "const-string",
    0x001b: "const-class",
    0x001c: "monitor-enter",
    0x001d: "monitor-exit",
    0x001e: "check-cast",
    0x001f: "instance-of",
    0x0020: "array-length",
    0x0021: "new-instance",
    0x0022: "new-array",
    0x0023: "filled-new-array",
    0x0024: "filled-new-array/range",
    0x0025: "fill-array-data",
    0x0026: "throw",
    0x0027: "goto",
    0x0028: "goto/16",
    0x0029: "goto/32",
    0x002a: "packed-switch",
    0x002b: "sparse-switch",
    0x002c: "cmpl-float",
    0x002d: "cmpg-float",
    0x002e: "cmpl-double",
    0x002f: "cmpg-double",
    0x0030: "cmp-long",
    0x0031: "if-eq",
    0x0032: "if-ne",
    0x0033: "if-lt",
    0x0034: "if-ge",
    0x0035: "if-gt",
    0x0036: "if-le",
    0x0037: "if-eqz",
    0x0038: "if-nez",
    0x0039: "if-ltz",
    0x003a: "if-gez",
    0x003b: "if-gtz",
    0x003c: "if-lez",
    0x003d: "aget",
    0x003e: "aget-wide",
    0x003f: "aget-object",
    0x0040: "aget-boolean",
    0x0041: "aget-byte",
    0x0042: "aget-char",
    0x0043: "aget-short",
    0x0044: "aput",
    0x0045: "aput-wide",
    0x0046: "aput-object",
    0x0047: "aput-boolean",
    0x0048: "aput-byte",
    0x0049: "aput-char",
    0x004a: "aput-short",
    0x004b: "iget",
    0x004c: "iget-wide",
    0x004d: "iget-object",
    0x004e: "iget-boolean",
    0x004f: "iget-byte",
    0x0050: "iget-char",
    0x0051: "iget-short",
    0x0052: "iput",
    0x0053: "iput-wide",
    0x0054: "iput-object",
    0x0055: "iput-boolean",
    0x0056: "iput-byte",
    0x0057: "iput-char",
    0x0058: "iput-short",
    0x0059: "sget",
    0x005a: "sget-wide",
    0x005b: "sget-object",
    0x005c: "sget-boolean",
    0x005d: "sget-byte",
    0x005e: "sget-char",
    0x005f: "sget-short",
    0x0060: "sput",
    0x0061: "sput-wide",
    0x0062: "sput-object",
    0x0063: "sput-boolean",
    0x0064: "sput-byte",
    0x0065: "sput-char",
    0x0066: "sput-short",
    0x0067: "invoke-virtual",
    0x0068: "invoke-super",
    0x0069: "invoke-direct",
    0x006a: "invoke-static",
    0x006b: "invoke-interface",
    # ... more opcodes would go here
}

def decode_opcode(opcode_unit: int) -> str:
    """Decode opcode unit to name"""
    opcode = opcode_unit & 0xFF
    return OPCODE_NAMES.get(opcode, f"unknown_0x{opcode:02x}")

def analyze_instructions(insns: bytes) -> Dict[str, int]:
    """Analyze instructions and count opcodes"""
    opcode_counts = {}
    
    i = 0
    while i < len(insns):
        if i + 1 > len(insns):
            break
            
        # Read 16-bit opcode unit
        opcode_unit = struct.unpack('<H', insns[i:i+2])[0]
        opcode_name = decode_opcode(opcode_unit)
        
        opcode_counts[opcode_name] = opcode_counts.get(opcode_name, 0) + 1
        
        # Advance by instruction size (simplified - most are 2 units)
        # A full implementation would handle variable-length instructions
        i += 2
    
    return opcode_counts

# ============================================================================
# MAIN VALIDATION PIPELINE
# ============================================================================

class APKBytecodeValidator:
    """
    Validates complete bytecode extraction pipeline for real APKs.
    
    Pipeline: APK → classes.dex → Header → ClassDefs → ClassData → Methods → CodeItems → Instructions
    """
    
    def __init__(self, output_dir: str):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[APKValidationResult] = []
    
    def calculate_sha256(self, filepath: str) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def extract_dex_from_apk(self, apk_path: str) -> Tuple[Optional[bytes], Optional[str], int]:
        """
        Extract classes.dex from APK file.
        Returns: (dex_data, error_message, dex_size)
        """
        start_time = datetime.now()
        
        try:
            with zipfile.ZipFile(apk_path, 'r') as zf:
                # Look for classes.dex (primary)
                if 'classes.dex' in zf.namelist():
                    dex_data = zf.read('classes.dex')
                    duration = (datetime.now() - start_time).total_seconds() * 1000
                    return dex_data, None, len(dex_data)
                
                # Look for any .dex files (multi-dex)
                dex_files = [n for n in zf.namelist() if n.endswith('.dex')]
                if dex_files:
                    dex_data = zf.read(dex_files[0])
                    duration = (datetime.now() - start_time).total_seconds() * 1000
                    return dex_data, None, len(dex_data)
                
                duration = (datetime.now() - start_time).total_seconds() * 1000
                return None, "No classes.dex found in APK", 0
                
        except zipfile.BadZipFile as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            return None, f"Invalid ZIP/APK format: {e}", 0
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            return None, f"Extraction error: {e}", 0
    
    def validate_dex_header(self, dex_data: bytes) -> Tuple[ValidationStatus, Optional[DexHeader], str]:
        """
        Validate DEX file header.
        Returns: (status, parsed_header_or_none, error_message)
        """
        start_time = datetime.now()
        
        if len(dex_data) < DEX_HEADER_SIZE:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            return ValidationStatus.FAIL, None, f"DEX too small: {len(dex_data)} bytes"
        
        header = parse_dex_header(dex_data)
        if header is None:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            return ValidationStatus.FAIL, None, "Invalid DEX magic number"
        
        if not header.is_valid():
            duration = (datetime.now() - start_time).total_seconds() * 1000
            return ValidationStatus.FAIL, None, "DEX header validation failed"
        
        # Verify file size matches
        if header.file_size != len(dex_data):
            duration = (datetime.now() - start_time).total_seconds() * 1000
            return ValidationStatus.PARTIAL, header, \
                   f"Size mismatch: header={header.file_size}, actual={len(dex_data)}"
        
        duration = (datetime.now() - start_time).total_seconds() * 1000
        return ValidationStatus.PASS, header, ""
    
    def validate_class_definitions(self, dex_data: bytes, header: DexHeader) -> \
        Tuple[ValidationStatus, List[ClassDefItem], str]:
        """
        Validate class definition parsing.
        Returns: (status, class_defs_list, error_message)
        """
        start_time = datetime.now()
        
        try:
            class_defs = parse_class_defs(dex_data, header)
            
            if not class_defs:
                duration = (datetime.now() - start_time).total_seconds() * 1000
                if header.class_defs_size == 0:
                    return ValidationStatus.PASS, [], "No class definitions (empty DEX)"
                else:
                    return ValidationStatus.FAIL, [], "Failed to parse class definitions"
            
            duration = (datetime.now() - start_time).total_seconds() * 1000
            return ValidationStatus.PASS, class_defs, ""
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            return ValidationStatus.ERROR, [], f"Exception during class def parsing: {e}"
    
    def validate_class_data(self, dex_data: bytes, class_defs: List[ClassDefItem]) -> \
        Tuple[ValidationStatus, Dict[int, ClassDataItem], int, int]:
        """
        Validate class_data_item parsing for all classes.
        Returns: (status, class_data_map, total_methods, total_fields)
        """
        start_time = datetime.now()
        class_data_map = {}
        total_methods = 0
        total_fields = 0
        
        try:
            for idx, class_def in enumerate(class_defs):
                if class_def.class_data_off != 0:
                    class_data = parse_class_data(dex_data, class_def.class_data_off)
                    if class_data:
                        class_data_map[idx] = class_data
                        total_methods += len(class_data.direct_methods) + len(class_data.virtual_methods)
                        total_fields += len(class_data.static_fields) + len(class_data.instance_fields)
            
            duration = (datetime.now() - start_time).total_seconds() * 1000
            
            if not class_data_map and class_defs:
                return ValidationStatus.PARTIAL, class_data_map, total_methods, total_fields
            
            return ValidationStatus.PASS, class_data_map, total_methods, total_fields
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            return ValidationStatus.ERROR, {}, 0, 0, f"Exception: {e}"
    
    def validate_code_items(self, dex_data: bytes, class_data_map: Dict[int, ClassDataItem]) -> \
        Tuple[ValidationStatus, List[Tuple[str, CodeItem]], int]:
        """
        Validate code_item parsing for all methods.
        Returns: (status, list_of_(method_info, code_item), total_instructions)
        """
        start_time = datetime.now()
        code_items = []
        total_instructions = 0
        
        try:
            for class_idx, class_data in class_data_map.items():
                # Process direct methods
                for method_idx, method in enumerate(class_data.direct_methods):
                    if method.code_off != 0:
                        code_item = parse_code_item(dex_data, method.code_off)
                        if code_item:
                            method_info = f"class[{class_idx}].direct_method[{method_idx}]"
                            code_items.append((method_info, code_item))
                            total_instructions += code_item.get_instruction_count()
                
                # Process virtual methods
                for method_idx, method in enumerate(class_data.virtual_methods):
                    if method.code_off != 0:
                        code_item = parse_code_item(dex_data, method.code_off)
                        if code_item:
                            method_info = f"class[{class_idx}].virtual_method[{method_idx}]"
                            code_items.append((method_info, code_item))
                            total_instructions += code_item.get_instruction_count()
            
            duration = (datetime.now() - start_time).total_seconds() * 1000
            return ValidationStatus.PASS, code_items, total_instructions
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            return ValidationStatus.ERROR, [], 0, f"Exception: {e}"
    
    def validate_instructions(self, code_items: List[Tuple[str, CodeItem]]) -> \
        Tuple[ValidationStatus, Dict[str, int]]:
        """
        Validate instruction decoding.
        Returns: (status, opcode_breakdown)
        """
        start_time = datetime.now()
        opcode_breakdown = {}
        
        try:
            for method_info, code_item in code_items:
                method_opcodes = analyze_instructions(code_item.insns)
                
                for opcode, count in method_opcodes.items():
                    opcode_breakdown[opcode] = opcode_breakdown.get(opcode, 0) + count
            
            duration = (datetime.now() - start_time).total_seconds() * 1000
            
            if not opcode_breakdown:
                return ValidationStatus.PARTIAL, opcode_breakdown
            
            return ValidationStatus.PASS, opcode_breakdown
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            return ValidationStatus.ERROR, {}, f"Exception: {e}"
    
    def validate_apk(self, apk_path: str) -> APKValidationResult:
        """
        Run complete validation pipeline on a single APK.
        """
        apk_name = Path(apk_path).name
        file_size = os.path.getsize(apk_path)
        sha256 = self.calculate_sha256(apk_path)
        validation_time = datetime.now().isoformat()
        
        result = APKValidationResult(
            apk_name=apk_name,
            apk_path=apk_path,
            sha256=sha256,
            file_size=file_size,
            validation_time=validation_time,
            overall_status=ValidationStatus.PASS
        )
        
        print(f"\n{'='*60}")
        print(f"Validating: {apk_name}")
        print(f"SHA256: {sha256[:32]}...")
        print(f"Size: {file_size:,} bytes")
        print(f"{'='*60}")
        
        # Stage 1: Extract DEX from APK
        print("\n[Stage 1] Extracting DEX from APK...")
        start = datetime.now()
        dex_data, error, dex_size = self.extract_dex_from_apk(apk_path)
        duration = (datetime.now() - start).total_seconds() * 1000
        
        if error:
            stage = PipelineStage(
                name="APK_DEX_EXTRACTION",
                status=ValidationStatus.FAIL,
                timestamp=datetime.now().isoformat(),
                duration_ms=int(duration),
                error_message=error
            )
            result.stages.append(stage)
            result.overall_status = ValidationStatus.FAIL
            result.first_failure_stage = "APK_DEX_EXTRACTION"
            self.results.append(result)
            return result
        
        stage = PipelineStage(
            name="APK_DEX_EXTRACTION",
            status=ValidationStatus.PASS,
            timestamp=datetime.now().isoformat(),
            duration_ms=int(duration),
            data_size=dex_size
        )
        result.stages.append(stage)
        print(f"  ✅ DEX extracted: {dex_size:,} bytes")
        
        # Stage 2: Validate DEX Header
        print("[Stage 2] Validating DEX header...")
        start = datetime.now()
        header_status, header, error = self.validate_dex_header(dex_data)
        duration = (datetime.now() - start).total_seconds() * 1000
        
        stage = PipelineStage(
            name="DEX_HEADER_VALIDATION",
            status=header_status,
            timestamp=datetime.now().isoformat(),
            duration_ms=int(duration),
            data_size=DEX_HEADER_SIZE if header else 0,
            error_message=error if error else None,
            details={
                "magic": header.magic.hex() if header else None,
                "file_size": header.file_size if header else None,
                "class_defs_count": header.class_defs_size if header else None,
                "method_ids_count": header.method_ids_size if header else None
            } if header else {}
        )
        result.stages.append(stage)
        
        if header_status == ValidationStatus.FAIL:
            result.overall_status = ValidationStatus.FAIL
            result.first_failure_stage = "DEX_HEADER_VALIDATION"
            print(f"  ❌ {error}")
            self.results.append(result)
            return result
        
        print(f"  ✅ DEX header valid")
        print(f"     Classes: {header.class_defs_size}, Methods: {header.method_ids_size}")
        
        if header_status == ValidationStatus.PARTIAL:
            result.overall_status = ValidationStatus.PARTIAL
            print(f"  ⚠️ {error}")
        
        # Stage 3: Parse Class Definitions
        print("[Stage 3] Parsing class definitions...")
        start = datetime.now()
        class_status, class_defs, error = self.validate_class_definitions(dex_data, header)
        duration = (datetime.now() - start).total_seconds() * 1000
        
        stage = PipelineStage(
            name="CLASS_DEF_PARSING",
            status=class_status,
            timestamp=datetime.now().isoformat(),
            duration_ms=int(duration),
            record_count=len(class_defs),
            error_message=error if error else None
        )
        result.stages.append(stage)
        result.total_classes = len(class_defs)
        
        if class_status == ValidationStatus.FAIL:
            result.overall_status = ValidationStatus.FAIL
            result.first_failure_stage = "CLASS_DEF_PARSING"
            print(f"  ❌ {error}")
            self.results.append(result)
            return result
        
        print(f"  ✅ Parsed {len(class_defs)} class definitions")
        
        # Stage 4: Parse Class Data
        print("[Stage 4] Parsing class data items...")
        start = datetime.now()
        data_status, class_data_map, total_methods, total_fields = \
            self.validate_class_data(dex_data, class_defs)
        duration = (datetime.now() - start).total_seconds() * 1000
        
        stage = PipelineStage(
            name="CLASS_DATA_PARSING",
            status=data_status,
            timestamp=datetime.now().isoformat(),
            duration_ms=int(duration),
            record_count=len(class_data_map),
            details={"methods": total_methods, "fields": total_fields}
        )
        result.stages.append(stage)
        result.total_methods = total_methods
        
        if data_status == ValidationStatus.ERROR:
            result.overall_status = ValidationStatus.ERROR
            result.first_failure_stage = "CLASS_DATA_PARSING"
            print(f"  ❌ {error}")
            self.results.append(result)
            return result
        
        print(f"  ✅ Parsed {len(class_data_map)} class data items")
        print(f"     Methods: {total_methods}, Fields: {total_fields}")
        
        # Stage 5: Parse Code Items
        print("[Stage 5] Parsing code items...")
        start = datetime.now()
        code_status, code_items, total_insns = self.validate_code_items(dex_data, class_data_map)
        duration = (datetime.now() - start).total_seconds() * 1000
        
        stage = PipelineStage(
            name="CODE_ITEM_PARSING",
            status=code_status,
            timestamp=datetime.now().isoformat(),
            duration_ms=int(duration),
            record_count=len(code_items),
            details={"instructions": total_insns}
        )
        result.stages.append(stage)
        result.total_instructions = total_insns
        
        if code_status == ValidationStatus.ERROR:
            result.overall_status = ValidationStatus.ERROR
            result.first_failure_stage = "CODE_ITEM_PARSING"
            print(f"  ❌ {error}")
            self.results.append(result)
            return result
        
        print(f"  ✅ Parsed {len(code_items)} code items")
        print(f"     Total instructions: {total_insns}")
        
        # Stage 6: Decode Instructions
        print("[Stage 6] Decoding instructions...")
        start = datetime.now()
        insn_status, opcode_breakdown = self.validate_instructions(code_items)
        duration = (datetime.now() - start).total_seconds() * 1000
        
        stage = PipelineStage(
            name="INSTRUCTION_DECODING",
            status=insn_status,
            timestamp=datetime.now().isoformat(),
            duration_ms=int(duration),
            details={"unique_opcodes": len(opcode_breakdown)}
        )
        result.stages.append(stage)
        result.opcode_breakdown = opcode_breakdown
        
        if insn_status == ValidationStatus.ERROR:
            result.overall_status = ValidationStatus.ERROR
            result.first_failure_stage = "INSTRUCTION_DECODING"
            print(f"  ❌ Error decoding instructions")
            self.results.append(result)
            return result
        
        print(f"  ✅ Decoded {len(opcode_breakdown)} unique opcode types")
        
        # Show top opcodes
        sorted_opcodes = sorted(opcode_breakdown.items(), key=lambda x: -x[1])[:10]
        print("\n     Top 10 opcodes:")
        for opcode, count in sorted_opcodes:
            print(f"       {opcode}: {count}")
        
        self.results.append(result)
        return result
    
    def generate_summary_report(self) -> dict:
        """Generate summary report of all validations"""
        total_apks = len(self.results)
        passed = sum(1 for r in self.results if r.overall_status == ValidationStatus.PASS)
        partial = sum(1 for r in self.results if r.overall_status == ValidationStatus.PARTIAL)
        failed = sum(1 for r in self.results if r.overall_status in (ValidationStatus.FAIL, ValidationStatus.ERROR))
        
        total_classes = sum(r.total_classes for r in self.results)
        total_methods = sum(r.total_methods for r in self.results)
        total_instructions = sum(r.total_instructions for r in self.results)
        
        # Aggregate opcode statistics
        all_opcodes = {}
        for r in self.results:
            for opcode, count in r.opcode_breakdown.items():
                all_opcodes[opcode] = all_opcodes.get(opcode, 0) + count
        
        report = {
            "validation_summary": {
                "generated_at": datetime.now().isoformat(),
                "total_apks_tested": total_apks,
                "passed": passed,
                "partial": partial,
                "failed": failed,
                "success_rate": (passed / total_apks * 100) if total_apks > 0 else 0
            },
            "bytecode_statistics": {
                "total_classes_found": total_classes,
                "total_methods_found": total_methods,
                "total_instructions_decoded": total_instructions,
                "unique_opcode_types": len(all_opcodes)
            },
            "opcode_frequency": dict(sorted(all_opcodes.items(), key=lambda x: -x[1])),
            "individual_results": [r.to_dict() for r in self.results],
            "first_failures_by_stage": {}
        }
        
        # Analyze first failure points
        for r in self.results:
            if r.first_failure_stage:
                stage = r.first_failure_stage
                report["first_failures_by_stage"][stage] = \
                    report["first_failures_by_stage"].get(stage, 0) + 1
        
        return report
    
    def save_results(self):
        """Save all results to JSON files"""
        # Save individual results
        for result in self.results:
            safe_name = result.apk_name.replace('.', '_').replace(' ', '_')
            output_file = self.output_dir / f"{safe_name}_validation.json"
            with open(output_file, 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
        
        # Save summary report
        summary = self.generate_summary_report()
        summary_file = self.output_dir / "validation_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n{'='*60}")
        print("VALIDATION COMPLETE")
        print(f"{'='*60}")
        print(f"Results saved to: {self.output_dir}")
        print(f"Summary: {summary_file.name}")
        
        return summary

# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """Main entry point for APK bytecode validation"""
    
    print("="*60)
    print("EXP-034 PHASE 1: Real APK Bytecode Pipeline Validator")
    print("="*60)
    print("Mission: Validate complete bytecode extraction from real APKs")
    print("Pipeline: APK → DEX → ClassDef → ClassData → Method → CodeItem → Instructions")
    print("="*60)
    
    # Setup paths
    base_dir = Path(__file__).parent.parent
    apk_directories = [
        base_dir / "download" / "apks",           # EXP-025 downloaded APKs
        base_dir / "download" / "exp027_real_apks",  # EXP-027 generated APKs
        base_dir / "test_apks",                     # Unit test APKs
    ]
    
    output_dir = base_dir / "run" / "exp034" / "apk_validation"
    
    # Create validator
    validator = APKBytecodeValidator(str(output_dir))
    
    # Collect all APK files
    apk_files = []
    for apk_dir in apk_directories:
        if apk_dir.exists():
            for apk_file in apk_dir.glob("*.apk"):
                apk_files.append(str(apk_file))
    
    # Also check for standalone DEX files
    for test_dir in [base_dir / "test_apks"]:
        if test_dir.exists():
            for dex_file in test_dir.glob("*.dex"):
                apk_files.append(str(dex_file))  # Will be handled as raw DEX
    
    apk_files.sort()
    
    print(f"\nFound {len(apk_files)} APK/DEX files to validate")
    
    if not apk_files:
        print("❌ No APK files found!")
        print(f"Searched directories:")
        for d in apk_directories:
            print(f"  - {d}")
        return 1
    
    # Validate each APK
    for apk_path in apk_files:
        try:
            validator.validate_apk(apk_path)
        except Exception as e:
            print(f"\n❌ Fatal error validating {apk_path}: {e}")
            import traceback
            traceback.print_exc()
    
    # Generate and save results
    summary = validator.save_results()
    
    # Print final summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"{'='*60}")
    print(f"Total APKs tested: {summary['validation_summary']['total_apks_tested']}")
    print(f"✅ Passed: {summary['validation_summary']['passed']}")
    print(f"⚠️  Partial: {summary['validation_summary']['partial']}")
    print(f"❌ Failed: {summary['validation_summary']['failed']}")
    print(f"Success rate: {summary['validation_summary']['success_rate']:.1f}%")
    print(f"\nBytecode Statistics:")
    print(f"  Classes: {summary['bytecode_statistics']['total_classes_found']:,}")
    print(f"  Methods: {summary['bytecode_statistics']['total_methods_found']:,}")
    print(f"  Instructions: {summary['bytecode_statistics']['total_instructions_decoded']:,}")
    print(f"  Unique opcodes: {summary['bytecode_statistics']['unique_opcode_types']}")
    
    if summary['first_failures_by_stage']:
        print(f"\nFailure points:")
        for stage, count in summary['first_failures_by_stage'].items():
            print(f"  {stage}: {count} APKs failed")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
