#!/usr/bin/env python3
"""
Ultra-simple valid DEX generator.
Creates minimal DEX with proven structure.
"""

import struct
import hashlib
import zlib

def uleb128(v):
    r = bytearray()
    while True:
        b = v & 0x7F; v >>= 7
        if v: b |= 0x80
        r.append(b)
        if not v: break
    return bytes(r)

def mutf8(s):
    return uleb128(len(s.encode('utf-8'))) + s.encode('utf-8') + b'\x00'

def main():
    H = 112  # Header size
    
    # === Define content ===
    strings = [
        "Lcom/test/Test;",           # 0: class
        "Ljava/lang/Object;",       # 1: superclass (Object, not Activity for simplicity)
        "Hello",                     # 2: string constant
        "<init>",                    # 3: constructor
        "()V",                       # 4: void descriptor  
        "V",                         # 5: void type
        "onCreate",                  # 6: method name
        "code.java",                 # 7: source file
    ]
    
    # Build string data
    str_data = b""
    str_offs = []
    for s in strings:
        str_offs.append(len(str_data))
        str_data += mutf8(s)
    
    print(f"String data: {len(str_data)} bytes")
    for i, s in enumerate(strings):
        print(f"  [{i}] @ {str_offs[i]}: \"{s}\"")
    
    # Bytecode: const-string v0, "Hello"; return-void
    bytecode = struct.pack('<HhH', 0x001a, 2, 0x000e)  # 6 bytes, 3 insns
    
    # Code item
    code_item = struct.pack('<HHHHI', 1, 0, 0, 0, 0) + struct.pack('<I', 3) + bytecode
    # regs=1, ins=0, outs=0, tries=0, debug=0, insns_size=3, then 3 instructions
    
    print(f"\nCode item: {len(code_item)} bytes")
    
    # Class data (ULEB128 encoded)
    # Format: [static_fields] [instance_fields] [direct_methods] [virtual_methods]
    class_data = b""
    class_data += uleb128(0)   # static_fields_size = 0
    class_data += uleb128(0)   # instance_fields_size = 0
    class_data += uleb128(1)   # direct_methods_size = 1 (<init>)
    class_data += uleb128(1)   # virtual_methods_size = 1 (onCreate)
    
    # Direct method 0: <init> (no code)
    class_data += uleb128(0)          # method_idx_diff = 0
    class_data += uleb128(0x10001)   # access_flags = PUBLIC | CONSTRUCTOR
    class_data += struct.pack('<I', 0)  # code_off = 0 (none)
    
    # Virtual method 0: onCreate (HAS CODE!)
    class_data += uleb128(1)          # method_idx_diff = 1
    class_data += uleb128(0x0001)     # access_flags = PUBLIC
    # code_off will be right after this 4-byte field
    code_item_offset_in_data = len(str_data) + len(class_data) + 4
    class_data += struct.pack('<I', code_item_offset_in_data)
    
    print(f"Class data: {len(class_data)} bytes")
    print(f"Code item will be at data+{code_item_offset_in_data}")
    
    # Data section = strings + class_data + code_item
    data_section = str_data + class_data + code_item
    print(f"\nData section: {len(data_section)} bytes")
    print(f"  Strings: [0, {len(str_data)})")
    print(f"  Class data: [{len(str_data)}, {len(str_data)+len(class_data)})")  
    print(f"  Code item: [{len(str_data)+len(class_data)}, {len(data_section)})")
    
    # === Tables ===
    num_strings = len(strings)
    num_types = 2
    num_protos = 1  # Only ()V needed for <init>
    num_methods = 2
    num_classes = 1
    
    # String IDs table (absolute offsets into file)
    # We don't know absolute offsets yet, use placeholders
    # Will fix after we know data_section_start
    
    # Type IDs table
    type_ids_table = struct.pack('<II', 0, 1)  # Test=0, Object=1
    
    # Proto IDs table
    proto_ids_table = struct.pack('<III', 5, 5, 0)  # ()V: shorty="V"(idx5), ret="V"(idx5), params=none
    
    # Method IDs table
    method_ids_table = b""
    # Method 0: Object.<init>:()V -> class=Object(1), proto=0(()V), name=<init>(3)
    method_ids_table += struct.pack('<HHI', 1, 0, 3)
    # Method 1: Test.onCreate:()V -> class=Test(0), proto=0(()V), name=onCreate(6)
    method_ids_table += struct.pack('<HHI', 0, 0, 6)
    
    # Calculate positions
    string_ids_table_size = num_strings * 4  # Placeholder size
    
    tables_start = H  # Right after header
    string_ids_start = tables_start
    type_ids_start = string_ids_start + string_ids_table_size
    proto_ids_start = type_ids_start + len(type_ids_table)
    method_ids_start = proto_ids_start + len(proto_ids_table)
    class_defs_start = method_ids_start + len(method_ids_table)
    data_section_start = class_defs_start + (num_classes * 32)  # After 1 class_def (32 bytes)
    
    total_size = data_section_start + len(data_section)
    
    print(f"\n=== LAYOUT ===")
    print(f"Header:         [0x{H:02X}, 0x{tables_start:02X})")
    print(f"string_ids:     [0x{string_ids_start:02X}, 0x{type_ids_start:02X})")
    print(f"type_ids:       [0x{type_ids_start:02X}, 0x{proto_ids_start:02X})")
    print(f"proto_ids:      [0x{proto_ids_start:02X}, 0x{method_ids_start:02X})")
    print(f"method_ids:     [0x{method_ids_start:02X}, 0x{class_defs_start:02X})")
    print(f"class_defs:     [0x{class_defs_start:02X}, 0x{data_section_start:02X})")
    print(f"data_section:   [0x{data_section_start:02X}, 0x{total_size:02X})")
    print(f"TOTAL:          {total_size} bytes")
    
    # Now build string_ids with correct absolute offsets
    string_ids_table = b""
    for rel_off in str_offs:
        abs_off = data_section_start + rel_off
        string_ids_table += struct.pack('<I', abs_off)
    
    assert len(string_ids_table) == string_ids_table_size
    
    # Update positions based on actual string_ids_table size
    type_ids_start = string_ids_start + len(string_ids_table)
    proto_ids_start = type_ids_start + len(type_ids_table)
    method_ids_start = proto_ids_start + len(proto_ids_table)
    class_defs_start = method_ids_start + len(method_ids_table)
    data_section_start = class_defs_start + 32
    total_size = data_section_start + len(data_section)
    
    # Rebuild string_ids with updated base
    string_ids_table = b""
    for rel_off in str_offs:
        abs_off = data_section_start + rel_off
        string_ids_table += struct.pack('<I', abs_off)
    
    # Final position check
    type_ids_start = string_ids_start + len(string_ids_table)
    proto_ids_start = type_ids_start + len(type_ids_table)
    method_ids_start = proto_ids_start + len(proto_ids_table)
    class_defs_start = method_ids_start + len(method_ids_table)
    data_section_start = class_defs_start + 32
    total_size = data_section_start + len(data_section)
    
    # === Build header ===
    header = bytearray(H)
    header[0:8] = b'dex\n035\x00'
    struct.pack_into('<I', header, 8, 0)               # checksum placeholder
    # signature[12:31] stays zero
    struct.pack_into('<I', header, 32, total_size)    # file_size
    struct.pack_into('<I', header, 36, H)             # header_size
    struct.pack_into('<I', header, 40, 0x12345678)    # endian_tag
    struct.pack_into('<I', header, 44, 0)             # link_size
    struct.pack_into('<I', header, 48, 0)             # link_off
    struct.pack_into('<I', header, 52, 0)             # map_off
    struct.pack_into('<I', header, 56, num_strings)   # string_ids_size
    struct.pack_into('<I', header, 60, string_ids_start)
    struct.pack_into('<I', header, 64, num_types)      # type_ids_size
    struct.pack_into('<I', header, 68, type_ids_start)
    struct.pack_into('<I', header, 72, num_protos)     # proto_ids_size
    struct.pack_into('<I', header, 76, proto_ids_start)
    struct.pack_into('<I', header, 80, 0)             # field_ids_size
    struct.pack_into('<I', header, 84, 0)             # field_ids_off
    struct.pack_into('<I', header, 88, num_methods)    # method_ids_size
    struct.pack_into('<I', header, 92, method_ids_start)
    struct.pack_into('<I', header, 96, num_classes)    # class_defs_size
    struct.pack_into('<I', header, 100, class_defs_start)
    struct.pack_into('<I', header, 104, len(data_section))
    struct.pack_into('<I', header, 108, data_section_start)
    
    # Class defs
    class_defs = struct.pack('<IIIIIIII',
        0,                  # class_idx = Test(0)
        0x0001,             # access_flags = PUBLIC
        1,                  # superclass = Object(1)
        0,                  # interfaces = none
        7,                  # source_file = "code.java"(7)
        0,                  # annotations = none
        data_section_start, # class_data_off -> our data!
        0                   # static_values = none
    )
    
    # Assemble
    dex = bytes(header) + string_ids_table + type_ids_table + proto_ids_table + method_ids_table + class_defs + data_section
    
    assert len(dex) == total_size, f"Size mismatch: {len(dex)} != {total_size}"
    
    # Checksum & signature
    cksum = zlib.adler32(dex[12:]) & 0xFFFFFFFF
    dex = dex[:8] + struct.pack('<I', cksum) + dex[12:]
    sig = hashlib.sha1(dex[32:]).digest()
    dex = dex[:20] + sig + dex[40:]  # sig goes to [12:32]
    
    # Verify before saving
    fsize = struct.unpack_from('<I', dex, 32)[0]
    hsize = struct.unpack_from('<I', dex, 36)[0]
    endian = struct.unpack_from('<I', dex, 40)[0]
    
    if fsize != len(dex) or hsize != H or endian != 0x12345678:
        print(f"\n❌ VERIFICATION FAILED!")
        print(f"  file_size: {fsize} vs {len(dex)}")
        print(f"  header_size: {hsize} vs {H}")
        return None
    
    # Save
    path = '/home/z/my-project/miniandroid/test_apks/exp032_valid_test.dex'
    with open(path, 'wb') as f:
        f.write(dex)
    
    print(f"\n✅ SAVED: {path}")
    print(f"   Size: {len(dex)} bytes")
    print(f"   SHA256: {hashlib.sha256(dex).hexdigest()[:32]}...")
    
    # Show first string offset as sanity check
    first_str_id_off = struct.unpack_from('<I', dex, string_ids_start)[0]
    print(f"\\nFirst string_id points to: {first_str_id_off}")
    if first_str_id_off < len(dex):
        data_at = dex[first_str_id_off:first_str_id_off+25]
        print(f"Data there: {data_at.hex()}")
        
    return path

if __name__ == '__main__':
    main()
