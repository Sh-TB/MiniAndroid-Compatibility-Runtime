#!/usr/bin/env python3
"""
MiniAndroid HelloWorld APK Generator - FIXED
EXP-002: Generates a minimal but valid HelloWorld.apk
"""

import struct
import zlib
import os
import zipfile
import io


class DexGenerator:
    """Generates minimal valid DEX files"""
    
    DEX_MAGIC = b'dex\n035\x00'
    ENDIAN_TAG = 0x12345678
    HEADER_SIZE = 0x70  # 112 bytes
    
    def __init__(self):
        self.strings = []          # String pool
        self.type_descriptors = [] # Type descriptor pool (indices into strings)
        self.protos = []           # Proto definitions
        self.methods = []          # Method definitions
        self.classes = []          # Class definitions
        self.type_indices = {}     # Named type indices for easy access
    
    def add_string(self, s):
        """Add string to pool, return index"""
        if s in self.strings:
            return self.strings.index(s)
        idx = len(self.strings)
        self.strings.append(s)
        return idx
    
    def add_type(self, descriptor):
        """
        Add type descriptor.
        Returns: index into type_ids array
        """
        if descriptor in self.type_descriptors:
            return self.type_descriptors.index(descriptor)
        
        # Ensure string exists first
        self.add_string(descriptor)
        idx = len(self.type_descriptors)
        self.type_descriptors.append(descriptor)
        return idx
    
    def get_string_index_for_type(self, type_idx):
        """Get string index for a given type index"""
        if type_idx < len(self.type_descriptors):
            desc = self.type_descriptors[type_idx]
            return self.strings.index(desc)
        return 0
    
    def generate_hello_world_dex(self):
        """Generate DEX for com.miniandroid.hello.MainActivity"""
        
        # Define all strings
        strings = {
            'main_activity': 'Lcom/miniandroid/hello/MainActivity;',
            'activity': 'Landroid/app/Activity;',
            'bundle': 'Landroid/os/Bundle;',
            'textview': 'Landroid/widget/TextView;',
            'void': 'V',
            'init': '<init>',
            'onCreate': 'onCreate',
            'setText': 'setText',
            'hello_text': 'Hello MiniAndroid',
            'source_file': 'MainActivity.java',
            'shorty_v': 'V',
            'shorty_vb': 'VB',
        }
        
        # Add all strings
        s = {k: self.add_string(v) for k, v in strings.items()}
        
        # Type IDs (each returns index into type_ids array)
        t = {}
        t['main_activity'] = self.add_type(strings['main_activity'])
        t['activity'] = self.add_type(strings['activity'])
        t['bundle'] = self.add_type(strings['bundle'])
        t['textview'] = self.add_type(strings['textview'])
        t['void'] = self.add_type(strings['void'])
        
        # Store for later use
        self.type_indices = t.copy()
        
        # Proto IDs
        p_void = len(self.protos)
        self.protos.append({
            'shorty_idx': s['shorty_v'],
            'return_type_idx': t['void'],
            'parameters_off': 0
        })
        
        p_bundle_void = len(self.protos)
        self.protos.append({
            'shorty_idx': s['shorty_vb'],
            'return_type_idx': t['void'],
            'parameters_off': 0xFFFFFFFF  # Placeholder
        })
        
        # Method IDs
        m = {}
        m['init'] = len(self.methods)
        self.methods.append({
            'class_idx': t['main_activity'],
            'proto_idx': p_void,
            'name_idx': s['init']
        })
        
        m['onCreate'] = len(self.methods)
        self.methods.append({
            'class_idx': t['main_activity'],
            'proto_idx': p_bundle_void,
            'name_idx': s['onCreate']
        })
        
        m['setText'] = len(self.methods)
        self.methods.append({
            'class_idx': t['textview'],
            'proto_idx': p_void,
            'name_idx': s['setText']
        })
        
        m['tv_init'] = len(self.methods)
        self.methods.append({
            'class_idx': t['textview'],
            'proto_idx': p_void,
            'name_idx': s['init']
        })
        
        # Bytecode for onCreate()
        bytecode_oncreate = [
            0x001A, 0x0000, s['hello_text'],     # const-string v0, "Hello"
            0x0022, 0x0001, t['textview'],       # new-instance v1, TextView
            0x0070, 0x0001, m['tv_init'],         # invoke-direct {v1}, init
            0x006E, 0x0002, m['setText'],         # invoke-virtual {v0,v1}, setText
            0x000E,                               # return-void
        ]
        
        bytecode_init = [0x000E]  # return-void
        
        code_item_init = self._build_code_item(1, 0, 0, 0, 0, bytecode_init)
        code_item_oncreate = self._build_code_item(2, 1, 2, 0, 0, bytecode_oncreate)
        
        # Class definition
        main_class = {
            'class_idx': t['main_activity'],
            'access_flags': 0x00000001,  # PUBLIC
            'superclass_idx': t['activity'],
            'interfaces_off': 0,
            'source_file_idx': s['source_file'],
            'annotations_off': 0,
            'class_data_off': 0,
            'static_values_off': 0,
            'direct_methods': [
                {'idx': 0, 'flags': 0x10001, 'code': 0},   # <init>
                {'idx': 1, 'flags': 0x00004, 'code': 0},   # onCreate (public)
            ],
            'virtual_methods': [],
            'code_items': [code_item_init, code_item_oncreate]
        }
        
        self.classes.append(main_class)
        
        return self._assemble()
    
    def _build_code_item(self, regs, ins, outs, tries, debug, bytecode):
        """Build code_item structure"""
        header = struct.pack('<HHHHII', regs, ins, outs, tries, debug, len(bytecode))
        insn = b''.join(struct.pack('<H', x & 0xFFFF) for x in bytecode)
        return header + insn
    
    def _uleb128(self, value):
        """Encode unsigned LEB128"""
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
    
    def _assemble(self):
        """Assemble complete DEX file"""
        
        # Calculate sizes and offsets
        num_strings = len(self.strings)
        num_types = len(self.type_descriptors)
        num_protos = len(self.protos)
        num_fields = 0  # No fields
        num_methods = len(self.methods)
        num_classes = len(self.classes)
        
        # Header is 0x70 (112) bytes
        string_ids_off = self.HEADER_SIZE
        type_ids_off = string_ids_off + num_strings * 4
        proto_ids_off = type_ids_off + num_types * 4
        field_ids_off = proto_ids_off + num_protos * 12
        method_ids_off = field_ids_off + num_fields * 8
        class_defs_off = method_ids_off + num_methods * 8
        data_off = class_defs_off + num_classes * 32
        
        # Build data section
        data = bytearray()
        
        # String data items
        str_data_offs = []
        for s in self.strings:
            str_data_offs.append(data_off + len(data))
            encoded = s.encode('utf-8')
            data += self._uleb128(len(encoded))
            data += encoded
            data += b'\x00'
        
        # Type list for Bundle parameter (if needed)
        for p in self.protos:
            if p.get('parameters_off', 0) == 0xFFFFFFFF:
                p['parameters_off'] = data_off + len(data)
                data += struct.pack('<IH', 1, self.type_indices['bundle'])  # 1 param, Bundle type
        
        # Code items
        for cls in self.classes:
            offsets = []
            for ci in cls.get('code_items', []):
                offsets.append(data_off + len(data))
                data += ci
                while len(data) % 4:
                    data += b'\x00'
            cls['code_offsets'] = offsets
        
        # Class data items
        cls_data_offs = []
        for cls in self.classes:
            cls_data_offs.append(data_off + len(data))
            
            dm = cls.get('direct_methods', [])
            vm = cls.get('virtual_methods', [])
            
            data += self._uleb128(0)  # static_fields
            data += self._uleb128(0)  # instance_fields  
            data += self._uleb128(len(dm))  # direct_methods
            data += self._uleb128(len(vm))  # virtual_methods
            
            # Encode direct methods
            idx = 0
            for i, m in enumerate(dm):
                diff = m['idx'] - idx
                data += self._uleb128(diff)
                data += self._uleb128(m['flags'])
                data += self._uleb128(cls['code_offsets'][i] if i < len(cls.get('code_offsets', [])) else 0)
                idx = m['idx']
            
            # Encode virtual methods
            idx = 0
            for m in vm:
                diff = m['idx'] - idx
                data += self._uleb128(diff)
                data += self._uleb128(m['flags'])
                data += self._uleb128(0)
                idx = m['idx']
            
            cls['class_data_off'] = cls_data_offs[-1]
        
        data_size = len(data)
        
        # Build header
        hdr = bytearray(self.HEADER_SIZE)
        hdr[0:8] = self.DEX_MAGIC
        # checksum at 8 (filled later)
        # signature at 12-31 (zeros, 20 bytes)
        struct.pack_into('<I', hdr, 32, 0)  # file_size (placeholder, updated later)
        struct.pack_into('<I', hdr, 36, self.HEADER_SIZE)  # header_size = 0x70
        struct.pack_into('<I', hdr, 40, self.ENDIAN_TAG)  # endian_tag = 0x12345678
        # link_size at 44 (zero)
        # link_off at 48 (zero)
        # map_off at 52 (zero)
        
        struct.pack_into('<I', hdr, 56, num_strings)
        struct.pack_into('<I', hdr, 60, string_ids_off)
        struct.pack_into('<I', hdr, 64, num_types)
        struct.pack_into('<I', hdr, 68, type_ids_off)
        struct.pack_into('<I', hdr, 72, num_protos)
        struct.pack_into('<I', hdr, 76, proto_ids_off)
        struct.pack_into('<I', hdr, 80, num_fields)
        struct.pack_into('<I', hdr, 84, field_ids_off)
        struct.pack_into('<I', hdr, 88, num_methods)
        struct.pack_into('<I', hdr, 92, method_ids_off)
        struct.pack_into('<I', hdr, 96, num_classes)
        struct.pack_into('<I', hdr, 100, class_defs_off)
        struct.pack_into('<I', hdr, 104, data_size)
        struct.pack_into('<I', hdr, 108, data_off)
        
        # Build ID arrays
        # String IDs (uint32 offsets into data)
        string_ids = b''.join(struct.pack('<I', o) for o in str_data_offs)
        
        # Type IDs (uint32 string indices) - FIXED: was using <H (16-bit), should be <I (32-bit)
        type_ids = b''
        for desc in self.type_descriptors:
            si = self.strings.index(desc)
            type_ids += struct.pack('<I', si)  # uint32, not uint16!
        
        # Proto IDs (12 bytes each)
        proto_ids = b''
        for p in self.protos:
            proto_ids += struct.pack('<III', p['shorty_idx'], p['return_type_idx'], p['parameters_off'])
        
        # Method IDs (8 bytes each)
        method_ids_arr = b''
        for m in self.methods:
            method_ids_arr += struct.pack('<HHI', m['class_idx'], m['proto_idx'], m['name_idx'])
        
        # Class Defs (32 bytes each)
        class_defs = b''
        for cls in self.classes:
            cd = struct.pack('<IIIIIIII',
                cls['class_idx'],
                cls['access_flags'],
                cls['superclass_idx'],
                cls['interfaces_off'],
                cls['source_file_idx'],
                cls['annotations_off'],
                cls['class_data_off'],
                cls['static_values_off']
            )
            print(f"      DEBUG class_def: class_idx={cls['class_idx']}, super={cls['superclass_idx']}, source={cls['source_file_idx']}, data_off={cls['class_data_off']}")
            print(f"      DEBUG packed bytes: {cd.hex()}")
            class_defs += cd
        
        # Assemble
        dex = bytearray(hdr)
        print(f"      DEBUG After header: {len(dex)} bytes")
        dex += string_ids
        print(f"      DEBUG After string_ids: {len(dex)} bytes (added {len(string_ids)})")
        dex += type_ids
        print(f"      DEBUG After type_ids: {len(dex)} bytes (added {len(type_ids)})")
        dex += proto_ids
        print(f"      DEBUG After proto_ids: {len(dex)} bytes (added {len(proto_ids)})")
        # field_ids (empty)
        dex += method_ids_arr
        print(f"      DEBUG After method_ids: {len(dex)} bytes (added {len(method_ids_arr)})")
        print(f"      DEBUG Expected class_defs offset: {len(dex):#x}")
        dex += class_defs
        print(f"      DEBUG After class_defs: {len(dex)} bytes (added {len(class_defs)})")
        dex += data
        print(f"      DEBUG After data: {len(dex)} bytes (added {len(data)})")
        
        # Debug: Verify class_defs in final DEX
        print(f"      DEBUG Final DEX size: {len(dex)}")
        print(f"      DEBUG class_defs in final DEX at {class_defs_off:#x}:")
        print(f"      {bytes(dex[class_defs_off:class_defs_off+32]).hex()}")
        
        # Update file size
        struct.pack_into('<I', dex, 32, len(dex))
        
        # Calculate checksum
        crc = zlib.adler32(dex[12:]) & 0xFFFFFFFF
        struct.pack_into('<I', dex, 8, crc)
        
        return bytes(dex)


def generate_manifest():
    """Generate AndroidManifest.xml"""
    return '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.miniandroid.hello"
    android:versionCode="1"
    android:versionName="1.0">
    
    <uses-sdk android:minSdkVersion="21"/>
    
    <application
        android:label="@string/app_name">
        
        <activity
            android:name=".MainActivity"
            android:label="@string/app_name"
            android:exported="true">
            
            <intent-filter>
                <action android:name="android.intent.action.MAIN"/>
                <category android:name="android.intent.category.LAUNCHER"/>
            </intent-filter>
        </activity>
        
    </application>
    
</manifest>'''.encode('utf-8')


def main():
    print("=" * 60)
    print("MiniAndroid HelloWorld APK Generator")
    print("EXP-002 - Fixed Version")
    print("=" * 60)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    output_dir = os.path.join(project_dir, 'test_apks')
    os.makedirs(output_dir, exist_ok=True)
    
    apk_path = os.path.join(output_dir, 'HelloWorld.apk')
    dex_path = os.path.join(output_dir, 'classes.dex')
    
    print(f"\n[1/4] Generating classes.dex...")
    
    gen = DexGenerator()
    dex_data = gen.generate_hello_world_dex()
    
    with open(dex_path, 'wb') as f:
        f.write(dex_data)
    
    print(f"      ✓ DEX: {len(dex_data)} bytes")
    print(f"      ✓ Strings: {len(gen.strings)}")
    print(f"      ✓ Types: {len(gen.type_descriptors)}")
    print(f"      ✓ Methods: {len(gen.methods)}")
    print(f"      ✓ Classes: {len(gen.classes)}")
    
    # Debug output
    print(f"\n      Debug info:")
    for i, s in enumerate(gen.strings):
        print(f"        string[{i}] = {s}")
    for i, t in enumerate(gen.type_descriptors):
        si = gen.strings.index(t)
        print(f"        type[{i}] -> string[{si}] = {t}")
    
    print(f"\n[2/4] Building APK...")
    
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('AndroidManifest.xml', generate_manifest())
        zf.writestr('classes.dex', dex_data)
        zf.writestr('res/layout/main.xml', b'''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:gravity="center">
    <TextView android:id="@+id/tv" android:layout_width="wrap_content"
        android:layout_height="wrap_content" android:text="Hello"/>
</LinearLayout>''')
        zf.writestr('res/values/strings.xml', b'''<?xml version="1.0" encoding="utf-8"?>
<resources><string name="app_name">MiniAndroid</string></resources>''')
    
    with open(apk_path, 'wb') as f:
        f.write(buf.getvalue())
    
    print(f"      ✓ APK: {apk_path} ({os.path.getsize(apk_path)} bytes)")
    
    print("\n" + "=" * 60)
    print("Done!")
    print("=" * 60)
    
    return apk_path


if __name__ == '__main__':
    main()
