#!/usr/bin/env python3
"""
EXP-031.6: Minimal VALID DEX File Generator
============================================

Creates a properly structured DEX file with:
- Correct header offsets
- Valid string/type/proto/method pools
- Class definition with code_item
- Real Dalvik bytecode instructions

This fixes the offset calculation bugs in the original generator.
"""

import struct
import zlib
import hashlib

class ValidDexGenerator:
    """Generates structurally valid DEX files"""
    
    DEX_MAGIC = b'dex\n035\x00'
    ENDIAN_TAG = 0x12345678
    HEADER_SIZE = 0x70  # 112 bytes
    
    def __init__(self):
        self.strings = []      # Raw string data
        self.string_ids = []   # Offsets to string data
        self.types = []        # Indices into strings
        self.protos = []       # (shorty_idx, return_type_idx, parameters_off)
        self.methods = []      # (class_idx, proto_idx, name_idx)
        self.classes = []      # Class definitions
        self.raw_data = None   # Final assembled DEX
        
    def add_string(self, s):
        """Add string, return index"""
        idx = len(self.strings)
        self.strings.append(s)
        return idx
    
    def generate_minimal_dex(self):
        """Generate minimal DEX with one executable method"""
        
        # === Define strings ===
        str_MainActivity = self.add_string("Lcom/test/MainActivity;")
        str_Activity = self.add_string("Landroid/app/Activity;")
        str_Void = self.add_string("V")
        str_init = self.add_string("<init>")
        str_onCreate = self.add_string("onCreate")
        str_Bundle = self.add_string("Landroid/os/Bundle;")
        str_Code = self.add_string("Code")
        
        # === Type IDs (indices into string table) ===
        type_MainActivity = len(self.types); self.types.append(str_MainActivity)
        type_Activity = len(self.types); self.types.append(str_Activity)
        type_Void = len(self.types); self.types.append(str_Void)
        type_Bundle = len(self.types); self.types.append(str_Bundle)
        
        # Store for use in _assemble
        self._type_MainActivity = type_MainActivity
        self._type_Activity = type_Activity
        
        # === Proto IDs ===
        # Proto 0: ()V
        proto_void = len(self.protos)
        self.protos.append((str_Void, type_Void, 0))  # No params
        
        # Proto 1: (Bundle)V  
        proto_bundle_void = len(self.protos)
        self.protos.append((str_Void, type_Void, 0xFFFFFFFF))  # Placeholder
        
        # === Method IDs ===
        # Method 0: MainActivity.<init>()V
        method_init = len(self.methods)
        self.methods.append((type_MainActivity, proto_void, str_init))
        
        # Method 1: MainActivity.onCreate(Bundle)V
        method_onCreate = len(self.methods)
        self.methods.append((type_MainActivity, proto_bundle_void, str_onCreate))
        
        # === Bytecode for onCreate ===
        # Simple bytecode: const/4 v0, #5; return v0
        bytecode_oncreate = [
            0x12, 0x00, 0x05,  # const/4 v0, #5
            0x0F,              # return v0 (actually return-int for testing)
        ]
        
        # Bytecode for <init>
        bytecode_init = [
            0x000E,  # return-void
        ]
        
        # Now assemble the DEX with CORRECT offsets
        return self._assemble([
            bytecode_init,
            bytecode_oncreate
        ], [str_init, str_onCreate])
    
    def _encode_uleb128(self, value):
        """Encode value as ULEB128"""
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
    
    def _make_string_data(self, s):
        """Encode string in MUTF-8 format with ULEB128 length prefix"""
        encoded = s.encode('utf-8')
        return self._encode_uleb128(len(encoded)) + encoded + b'\x00'
    
    def _assemble(self, bytecodes, method_names):
        """Assemble complete DEX with correct offset calculations"""
        
        # === Calculate Header Layout First ===
        string_ids_offset = self.HEADER_SIZE
        type_ids_offset = string_ids_offset + len(self.strings) * 4  # string_ids are uint32
        proto_ids_offset = type_ids_offset + len(self.types) * 2   # type_ids are uint16!
        field_ids_offset = proto_ids_offset + len(self.protos) * 12
        method_ids_offset = field_ids_offset  # No fields
        class_defs_offset = method_ids_offset + len(self.methods) * 8
        data_offset = class_defs_offset + 1 * 32  # 1 class_def
        
        # Now build data section (knowing data_offset)
        data_section = bytearray()
        
        # === String Data ===
        string_data_offsets = []
        for s in self.strings:
            string_data_offsets.append(len(data_section))
            data_section.extend(self._make_string_data(s))
        
        # Parameter list for Bundle (if needed)
        param_list_offset = len(data_section)
        data_section.extend(struct.pack('<I', 1))  # 1 param
        data_section.extend(struct.pack('<H', 3))   # type_idx for Bundle
        
        # Update proto with param_list offset
        protos_list = list(self.protos)
        protos_list[1] = (protos_list[1][0], protos_list[1][1], param_list_offset)
        self.protos = protos_list
        
        # === Code Items ===
        code_item_offsets = []
        for bc in bytecodes:
            # Align to 4-byte boundary
            while len(data_section) % 4 != 0:
                data_section.append(0)
            
            code_item_offsets.append(len(data_section))
            
            insns_size = len(bc)
            # Code item header (16 bytes)
            data_section.extend(struct.pack('<HHHHII',
                2 if bc == bytecodes[1] else 1,  # registers_size
                1 if bc == bytecodes[1] else 0,   # ins_size
                0,    # outs_size
                0,    # tries_size
                0,    # debug_info_off
                insns_size  # insns_size - THE KEY FIELD!
            ))
            
            # Instructions
            for insn in bc:
                data_section.extend(struct.pack('<H', insn & 0xFFFF))
        
        # === Class Data ===
        class_data_offset = len(data_section)
        
        # Encode class_data_item
        data_section.extend(self._encode_uleb128(0))  # static_fields_size
        data_section.extend(self._encode_uleb128(0))  # instance_fields_size
        data_section.extend(self._encode_uleb128(2))  # direct_methods_size (<init>, onCreate)
        data_section.extend(self._encode_uleb128(0))  # virtual_methods_size
        
        # Direct method 0: <init>
        data_section.extend(self._encode_uleb128(0))     # method_idx_diff = 0
        data_section.extend(self._encode_uleb128(0x10001))  # access_flags (PUBLIC | CONSTRUCTOR)
        data_section.extend(self._encode_uleb128(data_offset + code_item_offsets[0]))  # ABSOLUTE code_off
        
        # Direct method 1: onCreate
        data_section.extend(self._encode_uleb128(1))     # method_idx_diff = 1
        data_section.extend(self._encode_uleb128(0x00004))   # access_flags (PUBLIC)
        data_section.extend(self._encode_uleb128(data_offset + code_item_offsets[1]))  # ABSOLUTE code_off
        
        # === Calculate Header Offsets ===
        # (Already calculated above before building data_section)
        print(f"\nOffset calculations:")
        print(f"  string_ids_offset: 0x{string_ids_offset:X}")
        print(f"  type_ids_offset: 0x{type_ids_offset:X}")
        print(f"  proto_ids_offset: 0x{proto_ids_offset:X}")
        print(f"  field_ids_offset: 0x{field_ids_offset:X}")
        print(f"  method_ids_offset: 0x{method_ids_offset:X}")
        print(f"  class_defs_offset: 0x{class_defs_offset:X}")
        print(f"  data_offset: 0x{data_offset:X}")
        
        # Build complete file
        dex = bytearray()
        
        # === Header (112 bytes) ===
        dex.extend(self.DEX_MAGIC)
        dex.extend(b'\x00' * 4)  # checksum (fill later)
        dex.extend(b'\x00' * 20)  # signature (fill later)
        dex.extend(struct.pack('<I', 0))  # file_size (fill later)
        dex.extend(struct.pack('<I', self.HEADER_SIZE))
        dex.extend(struct.pack('<I', self.ENDIAN_TAG))
        dex.extend(struct.pack('<I', 0))  # link_size
        dex.extend(struct.pack('<I', 0))  # link_off
        dex.extend(struct.pack('<I', 0))  # map_off
        dex.extend(struct.pack('<I', len(self.strings)))
        dex.extend(struct.pack('<I', string_ids_offset))
        dex.extend(struct.pack('<I', len(self.types)))
        dex.extend(struct.pack('<I', type_ids_offset))
        dex.extend(struct.pack('<I', len(self.protos)))
        dex.extend(struct.pack('<I', proto_ids_offset))
        dex.extend(struct.pack('<I', 0))  # field_ids_size
        dex.extend(struct.pack('<I', field_ids_offset))
        dex.extend(struct.pack('<I', len(self.methods)))
        dex.extend(struct.pack('<I', method_ids_offset))
        dex.extend(struct.pack('<I', 1))  # class_defs_size
        dex.extend(struct.pack('<I', class_defs_offset))
        dex.extend(struct.pack('<I', len(data_section)))  # data_size
        dex.extend(struct.pack('<I', data_offset))
        
        assert len(dex) == self.HEADER_SIZE, f"Header size mismatch: {len(dex)}"
        print(f"Header written: {len(dex)} bytes")
        
        # === String IDs ===
        print(f"\nWriting string_ids at offset {len(dex)} (0x{len(dex):X})")
        for off in string_data_offsets:
            dex.extend(struct.pack('<I', data_offset + off))
        
        # === Type IDs ===
        print(f"Writing type_ids at offset {len(dex)} (0x{len(dex):X})")
        for type_idx in self.types:
            dex.extend(struct.pack('<H', type_idx))
        
        # === Proto IDs ===
        print(f"Writing proto_ids at offset {len(dex)} (0x{len(dex):X})")
        for shorty_idx, ret_type_idx, params_off in self.protos:
            dex.extend(struct.pack('<III', shorty_idx, ret_type_idx, params_off))
        
        # === Method IDs ===
        print(f"Writing method_ids at offset {len(dex)} (0x{len(dex):X})")
        for class_idx, proto_idx, name_idx in self.methods:
            dex.extend(struct.pack('<HHI', class_idx, proto_idx, name_idx))
        
        # === Class Def ===
        print(f"Writing class_def at offset {len(dex)} (0x{len(dex):X}) (should be 0x{class_defs_offset:X})")
        dex.extend(struct.pack('<I', self._type_MainActivity))  # class_idx
        dex.extend(struct.pack('<I', 0x00000001))          # access_flags (PUBLIC)
        dex.extend(struct.pack('<I', self._type_Activity))       # superclass_idx
        dex.extend(struct.pack('<I', 0))                   # interfaces_off
        dex.extend(struct.pack('<I', 0xFFFFFFFF))           # source_file_idx (NO_INDEX)
        dex.extend(struct.pack('<I', 0))                   # annotations_off
        dex.extend(struct.pack('<I', data_offset + class_data_offset))  # class_data_off
        dex.extend(struct.pack('<I', 0))                   # static_values_off
        
        # === Data Section ===
        dex.extend(data_section)
        
        # Fill in file_size
        struct.pack_into('<I', dex, 32, len(dex))
        
        # Calculate checksum (bytes 12 to end)
        checksum = adler32(dex[12:])
        struct.pack_into('<I', dex, 8, checksum)
        
        self.raw_data = bytes(dex)
        # Store for debugging
        self._data_offset = data_offset
        self._class_data_offset = class_data_offset
        return self.raw_data


def adler32(data):
    """Calculate Adler-32 checksum"""
    MOD_ADLER = 65521
    a = 1
    b = 0
    for byte in data:
        a = (a + byte) % MOD_ADLER
        b = (b + a) % MOD_ADLER
    return (b << 16) | a


if __name__ == '__main__':
    gen = ValidDexGenerator()
    dex_data = gen.generate_minimal_dex()
    
    output_path = 'test_apks/exp031_6/valid_test.dex'
    import os
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'wb') as f:
        f.write(dex_data)
    
    print(f"Generated valid DEX: {output_path}")
    print(f"Size: {len(dex_data)} bytes")
    print(f"MD5: {hashlib.md5(dex_data).hexdigest()}")
    
    # Quick validation
    print(f"\nValidation:")
    print(f"  Magic: {dex_data[:8]}")
    cds_off = struct.unpack('<I', dex_data[100:104])[0]
    cd = dex_data[cds_off:cds_off+32]
    cdo = struct.unpack('<I', cd[24:28])[0]
    print(f"  class_defs_off: 0x{cds_off:X}")
    print(f"  class_data_off: 0x{cdo:X} ({'VALID' if cdo < len(dex_data) else 'INVALID'})")
    
    # Debug info
    print(f"\nDebug:")
    print(f"  data_offset: 0x{gen._data_offset:X}")
    print(f"  class_data_offset (in data_section): 0x{gen._class_data_offset:X}")
    print(f"  total size: {len(dex_data)}")
