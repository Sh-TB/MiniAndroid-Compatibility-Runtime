#!/usr/bin/env python3
"""
MiniAndroid Test APK Generator (EXP-031.5 PHASE 4)
Generates minimal deterministic test applications for opcode validation.

Each test targets specific opcodes and produces predictable execution traces.
"""

import struct
import os
import sys
import json
import hashlib
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Optional

# ============================================================================
# DEX FILE FORMAT CONSTANTS
# ============================================================================

DEX_MAGIC = b'dex\n035\x00'
DEX_HEADER_SIZE = 0x70

# String IDs
STRING_ID_ITEM_SIZE = 4

# Type IDs
TYPE_ID_ITEM_SIZE = 4

# Proto IDs
PROTO_ID_ITEM_SIZE = 12

# Field IDs
FIELD_ID_ITEM_SIZE = 8

# Method IDs
METHOD_ID_ITEM_SIZE = 8

# Class Defs
CLASS_DEF_ITEM_SIZE = 32

# Code Item
CODE_ITEM_HEADER_SIZE = 16


@dataclass
class DexString:
    index: int
    data: str
    
    def to_bytes(self) -> bytes:
        """Convert string to MUTF-8 with size prefix"""
        encoded = self.data.encode('utf-8')
        # ULEB128 length + data + null terminator
        result = []
        # Simple ULEB128 encoding (for small strings)
        length = len(encoded)
        while length > 0x7f:
            result.append((length & 0x7f) | 0x80)
            length >>= 7
        result.append(length)
        result.extend(encoded)
        result.append(0)  # null terminator
        return bytes(result)


@dataclass 
class DexMethod:
    class_name: str
    method_name: str
    descriptor: str
    bytecode: List[int]  # uint16 opcode array
    registers_size: int = 10
    ins_size: int = 1
    outs_size: int = 4


@dataclass
class DexClass:
    name: str
    superclass: str = "Ljava/lang/Object;"
    methods: List[DexMethod] = None
    
    def __post_init__(self):
        if self.methods is None:
            self.methods = []


class MinimalDexGenerator:
    """Generates minimal DEX files for testing"""
    
    def __init__(self):
        self.strings: List[DexString] = []
        self.types: List[str] = []
        self.methods: List[DexMethod] = []
        self.classes: List[DexClass] = []
        
        # Add default strings
        self._add_string("Ljava/lang/Object;")
        self._add_string("Ljava/lang/String;")
        self._add_string("Landroid/app/Activity;")
        self._add_string("Landroid/os/Bundle;")
        self._add_string("<init>")
        self._add_string("()V")
        self._add_string("(Landroid/os/Bundle;)V")
        self._add_string("Code")
        
    def _add_string(self, s: str) -> int:
        """Add a string and return its index"""
        for i, existing in enumerate(self.strings):
            if existing.data == s:
                return i
        idx = len(self.strings)
        self.strings.append(DexString(idx, s))
        return idx
    
    def _add_type(self, type_desc: str) -> int:
        """Add a type descriptor and return its index"""
        if type_desc not in self.types:
            self.types.append(type_desc)
        return self.types.index(type_desc)
    
    def add_class(self, cls: DexClass) -> None:
        """Add a class definition"""
        self._add_type(cls.name)
        if cls.superclass != "Ljava/lang/Object;":
            self._add_type(cls.superclass)
        for method in cls.methods:
            self._add_string(method.class_name)
            self._add_string(method.method_name)
            self._add_string(method.descriptor)
        self.classes.append(cls)
    
    def generate(self, output_path: str) -> bool:
        """Generate the DEX file"""
        try:
            # Build all sections
            string_data = self._build_string_data()
            type_list = self._build_type_list()
            
            # Calculate offsets (simplified - would need proper alignment in real impl)
            header_size = DEX_HEADER_SIZE
            string_ids_offset = header_size
            type_ids_offset = string_ids_offset + len(self.strings) * STRING_ID_ITEM_SIZE
            
            # Build header
            header = self._build_header(
                string_ids_offset=string_ids_offset,
                type_ids_offset=type_ids_offset,
                string_data_size=len(string_data)
            )
            
            # Write file
            with open(output_path, 'wb') as f:
                f.write(header)
                # Write string IDs (offsets into string data)
                for _ in self.strings:
                    f.write(struct.pack('<I', 0))  # Placeholder offsets
                # Write type IDs (indices into string list)
                for t in self.types:
                    f.write(struct.pack('<I', self._get_string_index(t)))
                # Write string data
                f.write(string_data)
            
            return True
            
        except Exception as e:
            print(f"Error generating DEX: {e}")
            return False
    
    def _build_header(self, string_ids_offset: int, type_ids_offset: int, string_data_size: int) -> bytes:
        """Build DEX header"""
        header = bytearray(DEX_HEADER_SIZE)
        
        # Magic
        header[0:8] = DEX_MAGIC
        
        # Checksum (placeholder - offset 8)
        # Signature (placeholder - offset 12)
        
        # File size (will update)
        # struct.pack_into('<I', header, 32, file_size)
        
        # Header size
        struct.pack_into('<I', header, 36, DEX_HEADER_SIZE)
        
        # Endian tag
        struct.pack_into('<I', header, 40, 0x12345678)
        
        # String IDs
        struct.pack_into('<I', header, 56, string_ids_offset)
        struct.pack_into('<I', header, 60, len(self.strings))
        
        # Type IDs
        struct.pack_into('<I', header, 64, type_ids_offset)
        struct.pack_into('<I', header, 68, len(self.types))
        
        return bytes(header)
    
    def _build_string_data(self) -> bytes:
        """Build string data section"""
        result = bytearray()
        for s in self.strings:
            result.extend(s.to_bytes())
        return bytes(result)
    
    def _build_type_list(self) -> bytes:
        """Build type list section"""
        result = bytearray()
        for t in self.types:
            result.extend(struct.pack('<I', self._get_string_index(t)))
        return bytes(result)
    
    def _get_string_index(self, s: str) -> int:
        for i, existing in enumerate(self.strings):
            if existing.data == s:
                return i
        return self._add_string(s)


# ============================================================================
# TEST CASE DEFINITIONS
# ============================================================================

def create_test1_constant() -> DexClass:
    """
    Test 1: Simple constant loading
    Expected opcodes: const, return
    """
    return DexClass(
        name="LTest1Constant;",
        methods=[
            DexMethod(
                class_name="LTest1Constant;",
                method_name="testConstant",
                descriptor="()I",
                bytecode=[
                    0x12, 0x00,  # const/4 v0, #5
                    0x0F, 0x00,  # return v0
                ],
                registers_size=2,
                ins_size=0,
                outs_size=0
            )
        ]
    )


def create_test2_method_call() -> DexClass:
    """
    Test 2: Method call
    Expected opcodes: invoke-direct/static, return
    """
    return DexClass(
        name="LTest2MethodCall;",
        methods=[
            DexMethod(
                class_name="LTest2MethodCall;",
                method_name="calculate",
                descriptor="()I",
                bytecode=[
                    0x12, 0x01,  # const/4 v1, #10
                    0x12, 0x02,  # const/4 v2, #20
                    0x70, 0x20, 0x01, 0x00, 0x00,  # invoke-direct LTest2;.add:(II)I
                    0x0F, 0x00,  # return
                ],
                registers_size=4,
                ins_size=0,
                outs_size=2
            ),
            DexMethod(
                class_name="LTest2MethodCall;",
                method_name="add",
                descriptor="(II)I",
                bytecode=[
                    0x90, 0x00,  # add-int v0, v1, v2
                    0x0F, 0x00,  # return v0
                ],
                registers_size=4,
                ins_size=2,
                outs_size=0
            )
        ]
    )


def create_test3_object_creation() -> DexClass:
    """
    Test 3: Object creation
    Expected opcodes: new-instance, invoke-direct
    """
    return DexClass(
        name="LTest3Object;",
        methods=[
            DexMethod(
                class_name="LTest3Object;",
                method_name="createCounter",
                descriptor="()LCounter;",
                bytecode=[
                    0x22, 0x00, 0xFF, 0xFF,  # new-instance v0, LCounter;
                    0x70, 0x30, 0x01, 0x00, 0x00,  # invoke-direct LCounter;<init>:()V
                    0x11, 0x00,  # return-object v0
                ],
                registers_size=4,
                ins_size=0,
                outs_size=1
            )
        ]
    )


def create_test4_virtual_dispatch() -> DexClass:
    """
    Test 4: Virtual dispatch (polymorphism)
    Expected opcodes: new-instance, invoke-virtual
    Evidence: Resolved method should be Dog.sound(), not Animal.sound()
    """
    return DexClass(
        name="LTest4Virtual;",
        methods=[
            DexMethod(
                class_name="LTest4Virtual;",
                method_name="testDispatch",
                descriptor="()V",
                bytecode=[
                    0x22, 0x00, 0xFF, 0xFF,  # new-instance v0, LDog;
                    0x70, 0x30, 0x01, 0x00, 0x00,  # invoke-direct LDog;<init>:()V
                    0x6E, 0x20, 0x01, 0x00, 0x00,  # invoke-virtual LAnimal;.sound:()V
                    0x0E,  # return-void
                ],
                registers_size=4,
                ins_size=0,
                outs_size=1
            )
        ]
    )


def create_test5_mini_activity() -> DexClass:
    """
    Test 5: Mini Activity lifecycle
    Expected: Activity.onCreate, invoke-virtual, const-string, View API calls
    """
    return DexClass(
        name="LMiniActivity;",
        superclass="Landroid/app/Activity;",
        methods=[
            DexMethod(
                class_name="LMiniActivity;",
                method_name="onCreate",
                descriptor="(Landroid/os/Bundle;)V",
                bytecode=[
                    0x37, 0x01, 0x00, 0x00,  # iput-object v1, v0, LActivity;.mToken:Landroid/os/Bundle;
                    0x62, 0x00, 0x01, 0x00, 0x00,  # new-instance v1, Landroid/widget/TextView;
                    0x70, 0x31, 0x02, 0x00, 0x00,  # invoke-direct LTextView;<init>:(LContext;)V
                    0x1A, 0x02, 0x03, 0x00, 0x00,  # const-string v2, "Hello"
                    0x6E, 0x32, 0x03, 0x00, 0x00,  # invoke-virtual LTextView;.setText:(Ljava/lang/CharSequence;)V
                    0x6E, 0x21, 0x01, 0x00, 0x00,  # invoke-virtual LActivity;.setContentView:(LView;)V
                    0x0E,  # return-void
                ],
                registers_size=8,
                ins_size=2,  # this + Bundle
                outs_size=3
            )
        ]
    )


# ============================================================================
# MAIN GENERATOR
# ============================================================================

def generate_all_tests(output_dir: str) -> dict:
    """Generate all test cases"""
    
    results = {
        "tests_generated": [],
        "output_dir": output_dir,
        "timestamp": None
    }
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    test_cases = [
        ("Test1_Constant", create_test1_constant()),
        ("Test2_MethodCall", create_test2_method_call()),
        ("Test3_ObjectCreation", create_test3_object_creation()),
        ("Test4_VirtualDispatch", create_test4_virtual_dispatch()),
        ("Test5_MiniActivity", create_test5_mini_activity()),
    ]
    
    for name, dex_class in test_cases:
        generator = MinimalDexGenerator()
        generator.add_class(dex_class)
        
        output_path = os.path.join(output_dir, f"{name}.dex")
        
        if generator.generate(output_path):
            results["tests_generated"].append({
                "name": name,
                "file": output_path,
                "class": dex_class.name,
                "methods": [m.method_name for m in dex_class.methods],
                "opcodes_expected": _count_opcodes(dex_class),
                "status": "GENERATED"
            })
            print(f"✅ Generated {name}")
        else:
            results["tests_generated"].append({
                "name": name,
                "status": "FAILED"
            })
            print(f"❌ Failed to generate {name}")
    
    # Save manifest
    manifest_path = os.path.join(output_dir, "test_manifest.json")
    with open(manifest_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    return results


def _count_opcodes(dex_class: DexClass) -> dict:
    """Count expected opcodes in test case"""
    opcodes = {}
    for method in dex_class.methods:
        i = 0
        while i < len(method.bytecode):
            opcode = method.bytecode[i]
            opcode_names = {
                0x12: "const/4", 0x13: "const/16", 0x14: "const",
                0x1A: "const-string", 0x22: "new-instance",
                0x0F: "return", 0x0E: "return-void", 0x11: "return-object",
                0x70: "invoke-direct", 0x67: "invoke-static",
                0x6E: "invoke-virtual", 0x72: "invoke-interface",
                0x28: "goto", 0x38: "if-eqz", 0x39: "if-nez"
            }
            name = opcode_names.get(opcode, f"unknown(0x{opcode:02x})")
            opcodes[name] = opcodes.get(name, 0) + 1
            
            # Skip instruction operands (simplified)
            i += 2  # Most instructions are 2+ units
            
    return opcodes


if __name__ == "__main__":
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "./test_apks/exp031_5"
    
    print("=" * 60)
    print("EXP-031.5 Test APK Generator")
    print("=" * 60)
    print(f"\nOutput directory: {output_dir}\n")
    
    results = generate_all_tests(output_dir)
    
    print("\n" + "=" * 60)
    print(f"Generated {len(results['tests_generated'])} test cases")
    print(f"Manifest: {os.path.join(output_dir, 'test_manifest.json')}")
    print("=" * 60)
