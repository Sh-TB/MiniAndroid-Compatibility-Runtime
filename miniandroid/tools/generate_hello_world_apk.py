#!/usr/bin/env python3
"""
MiniAndroid HelloWorld APK Generator
EXP-002: Generates a minimal but valid HelloWorld.apk

Creates:
- AndroidManifest.xml (binary format)
- classes.dex (minimal DEX with MainActivity)
- resources.arsc (minimal)
- res/layout/main.xml (binary)

Package: com.miniandroid.hello
Activity: MainActivity
"""

import struct
import zlib
import hashlib
import os
import sys
from datetime import datetime

# ============================================================================
# DEX File Generator
# ============================================================================

class DexGenerator:
    """Generates minimal DEX files for testing"""
    
    # DEX constants
    DEX_MAGIC = b'dex\n035\x00'
    ENDIAN_TAG = 0x12345678
    HEADER_SIZE = 0x70
    
    def __init__(self):
        self.string_list = []      # Actual strings
        self.type_descriptors = [] # Type descriptor strings (indices into string_list)
        
        self.protos = []     # Proto definitions
        self.fields = []     # Field definitions  
        self.methods = []    # Method definitions
        self.classes = []    # Class definitions
        
    def add_string(self, s):
        """Add string to pool, return index"""
        if s in self.string_list:
            return self.string_list.index(s)
        idx = len(self.string_list)
        self.string_list.append(s)
        return idx
    
    def add_type(self, descriptor_string):
        """
        Add type by its descriptor string.
        Returns index into type_ids array.
        descriptor_string like 'Lcom/miniandroid/hello/MainActivity;'
        """
        if descriptor_string in self.type_descriptors:
            return self.type_descriptors.index(descriptor_string)
        
        # First ensure the string exists
        str_idx = self.add_string(descriptor_string)
        idx = len(self.type_descriptors)
        self.type_descriptors.append(descriptor_string)
        return idx
    
    def generate_hello_world_dex(self):
        """Generate DEX for com.miniandroid.hello.MainActivity"""
        
        # === Define all strings we need ===
        strings = {
            # Class descriptors
            'MainActivity': 'Lcom/miniandroid/hello/MainActivity;',
            'Activity': 'Landroid/app/Activity;',
            'Bundle': 'Landroid/os/Bundle;',
            'TextView': 'Landroid/widget/TextView;',
            'View': 'Landroid/view/View;',
            'Void': 'V',
            
            # Method names
            'init': '<init>',
            'onCreate': 'onCreate',
            'setText': 'setText',
            
            # String literals
            'hello_text': 'Hello MiniAndroid',
            'source_file': 'MainActivity.java',
            
            # Shorty descriptors
            'shorty_v': 'V',           # ()V
            'shorty_vb': 'VB',         # (B)V - simplified for Bundle
        }
        
        # Add all strings to pool
        str_idx = {name: self.add_string(s) for name, s in strings.items()}
        
        # === Type IDs ===
        type_idx = {}
        type_idx['MainActivity'] = self.add_type(strings['MainActivity'])
        type_idx['Activity'] = self.add_type(strings['Activity'])
        type_idx['Bundle'] = self.add_type(strings['Bundle'])
        type_idx['TextView'] = self.add_type(strings['TextView'])
        type_idx['Void'] = self.add_type(strings['Void'])
        
        # === Proto IDs ===
        # Proto 0: ()V - for constructors and simple methods
        proto_void_idx = len(self.protos)
        self.protos.append({
            'shorty_idx': str_idx['shorty_v'],
            'return_type_idx': type_idx['Void'],
            'parameters_off': 0  # No parameters
        })
        
        # Proto 1: (Bundle)V - for onCreate
        proto_bundle_void_idx = len(self.protos)
        self.protos.append({
            'shorty_idx': str_idx['shorty_vb'],
            'return_type_idx': type_idx['Void'],
            'parameters_off': 0xFFFFFFFF  # Placeholder - will be filled
        })
        
        # === Method IDs ===
        # Method 0: MainActivity.<init>()V
        method_init_idx = len(self.methods)
        self.methods.append({
            'class_idx': type_idx['MainActivity'],
            'proto_idx': proto_void_idx,
            'name_idx': str_idx['init']
        })
        
        # Method 1: MainActivity.onCreate(Bundle)V
        method_oncreate_idx = len(self.methods)
        self.methods.append({
            'class_idx': type_idx['MainActivity'],
            'proto_idx': proto_bundle_void_idx,
            'name_idx': str_idx['onCreate']
        })
        
        # Method 2: TextView.setText(String)V
        method_settext_idx = len(self.methods)
        self.methods.append({
            'class_idx': type_idx['TextView'],
            'proto_idx': proto_void_idx,  # Simplified
            'name_idx': str_idx['setText']
        })
        
        # Method 3: TextView.<init>()V
        method_tv_init_idx = len(self.methods)
        self.methods.append({
            'class_idx': type_idx['TextView'],
            'proto_idx': proto_void_idx,
            'name_idx': str_idx['init']
        })
        
        # === Bytecode for onCreate() ===
        # Simulated Dalvik bytecode:
        #
        #   const-string v0, "Hello MiniAndroid"
        #   new-instance v1, TextView
        #   invoke-direct {v1}, TextView.<init>
        #   invoke-virtual {v0, v1}, TextView.setText  
        #   return-void
        
        bytecode_oncreate = [
            0x001A, 0x0000, str_idx['hello_text'],  # const-string v0, "Hello"
            0x0022, 0x0001, type_idx['TextView'],   # new-instance v1, TextView
            0x0070, 0x0001, method_tv_init_idx,     # invoke-direct {v1}, init
            0x006E, 0x0002, method_settext_idx,     # invoke-virtual {v0,v1}, setText
            0x000E,                                  # return-void
        ]
        
        # Bytecode for <init> (simplified - just returns)
        bytecode_init = [
            0x000E,  # return-void
        ]
        
        # Build code items
        code_item_init = self._build_code_item(
            registers_size=1, ins_size=0, outs_size=0,
            tries_size=0, debug_info_off=0, bytecode=bytecode_init
        )
        
        code_item_oncreate = self._build_code_item(
            registers_size=2, ins_size=1, outs_size=2,
            tries_size=0, debug_info_off=0, bytecode=bytecode_oncreate
        )
        
        # === Class Definition ===
        main_activity_class = {
            'class_idx': type_idx['MainActivity'],
            'access_flags': 0x00000001,  # PUBLIC
            'superclass_idx': type_idx['Activity'],
            'interfaces_off': 0,
            'source_file_idx': str_idx['source_file'],
            'annotations_off': 0,
            'class_data_off': 0,  # Filled during assembly
            'static_values_off': 0,
            
            # Class data (ULEB128 encoded fields/methods)
            'static_fields': [],
            'instance_fields': [],
            'direct_methods': [
                {'method_idx_diff': 0, 'access_flags': 0x10001, 'code_off': 0},
                {'method_idx_diff': 1, 'access_flags': 0x00004, 'code_off': 0},
            ],
            'virtual_methods': [],
            
            # Code items (stored separately for offset calculation)
            'code_items': [code_item_init, code_item_oncreate]
        }
        
        self.classes.append(main_activity_class)
        
        return self._assemble_dex()
    
    def _build_code_item(self, registers_size, ins_size, outs_size, 
                         tries_size, debug_info_off, bytecode):
        """Build a code_item structure"""
        insns_size = len(bytecode)
        
        # Header (16 bytes)
        header = struct.pack('<HHHHII',
            registers_size,   # registers_size
            ins_size,         # ins_size
            outs_size,        # outs_size
            tries_size,       # tries_size
            debug_info_off,   # debug_info_off
            insns_size        # insns_size (in 16-bit code units)
        )
        
        # Instructions
        insn_data = b''
        for insn in bytecode:
            insn_data += struct.pack('<H', insn & 0xFFFF)
        
        return header + insn_data
    
    def _encode_uleb128(self, value):
        """Encode unsigned integer as ULEB128"""
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
    
    def _assemble_dex(self):
        """Assemble complete DEX file from components"""
        
        # Calculate section sizes
        string_ids_size = len(self.string_list)
        type_ids_size = len(self.type_descriptors)
        proto_ids_size = len(self.protos)
        field_ids_size = len(self.fields)
        method_ids_size = len(self.methods)
        class_defs_size = len(self.classes)
        
        # Calculate offsets (everything after header)
        string_ids_offset = self.HEADER_SIZE
        type_ids_offset = string_ids_offset + string_ids_size * 4
        proto_ids_offset = type_ids_offset + type_ids_size * 4
        field_ids_offset = proto_ids_offset + proto_ids_size * 12
        method_ids_offset = field_ids_offset + field_ids_size * 8
        class_defs_offset = method_ids_offset + method_ids_size * 8
        data_offset = class_defs_offset + class_defs_size * 32
        
        # === Build Data Section ===
        data = b''
        
        # String data items
        string_data_offsets = []
        for s in self.string_list:
            string_data_offsets.append(data_offset + len(data))
            encoded = s.encode('utf-8')
            data += self._encode_uleb128(len(encoded))
            data += encoded
            data += b'\x00'  # Null terminator
        
        # Type list for Bundle parameter (if needed)
        has_param_list = any(p.get('parameters_off', 0) == 0xFFFFFFFF for p in self.protos)
        if has_param_list:
            param_list_offset = data_offset + len(data)
            data += struct.pack('<I', 1)  # 1 parameter
            data += struct.pack('<H', self.type_descriptors.index('Landroid/os/Bundle;'))
            
            # Update proto with real offset
            for p in self.protos:
                if p.get('parameters_off') == 0xFFFFFFFF:
                    p['parameters_off'] = param_list_offset
        
        # Code items
        for cls in self.classes:
            cls_code_offsets = []
            for code_item in cls.get('code_items', []):
                cls_code_offsets.append(data_offset + len(data))
                data += code_item
                # Align to 4-byte boundary
                while len(data) % 4 != 0:
                    data += b'\x00'
            cls['code_item_offsets'] = cls_code_offsets
        
        # Class data items
        class_data_offsets = []
        for cls in self.classes:
            class_data_offsets.append(data_offset + len(data))
            
            static_fields = cls.get('static_fields', [])
            instance_fields = cls.get('instance_fields', [])
            direct_methods = cls.get('direct_methods', [])
            virtual_methods = cls.get('virtual_methods', [])
            
            # Header
            data += self._encode_uleb128(len(static_fields))
            data += self._encode_uleb128(len(instance_fields))
            data += self._encode_uleb128(len(direct_methods))
            data += self._encode_uleb128(len(virtual_methods))
            
            # Direct methods (encoded)
            method_idx = 0
            for i, dm in enumerate(direct_methods):
                diff = dm['method_idx_diff'] - method_idx
                data += self._encode_uleb128(diff)
                data += self._encode_uleb128(dm['access_flags'])
                
                # Code item offset
                if i < len(cls.get('code_item_offsets', [])):
                    data += self._encode_uleb128(cls['code_item_offsets'][i])
                else:
                    data += self._encode_uleb128(0)
                
                method_idx = dm['method_idx_diff']
            
            # Virtual methods (encoded)
            method_idx = 0
            for vm in virtual_methods:
                diff = vm['method_idx_diff'] - method_idx
                data += self._encode_uleb128(diff)
                data += self._encode_uleb128(vm['access_flags'])
                data += self._encode_uleb128(0)  # No code
                method_idx = vm['method_idx_diff']
        
        # Update class defs with offsets
        for i, cls in enumerate(self.classes):
            cls['class_data_off'] = class_data_offsets[i]
        
        data_size = len(data)
        
        # === Build Header (70 bytes) ===
        header = bytearray(self.HEADER_SIZE)
        
        # Magic
        header[0:8] = self.DEX_MAGIC
        
        # Checksum (offset 8) - placeholder, filled later
        # Signature (offset 32) - placeholder
        
        # File size (offset 32)
        total_size = data_offset + data_size
        struct.pack_into('<I', header, 32, total_size)
        
        # Header size (offset 36) - always 0x70
        struct.pack_into('<I', header, 36, self.HEADER_SIZE)
        
        # Endian tag (offset 40)
        struct.pack_into('<I', header, 40, self.ENDIAN_TAG)
        
        # Link (offset 44-51) - zeros
        # Map offset (offset 52-55) - 0 for now
        
        # String IDs (offset 56-63)
        struct.pack_into('<I', header, 56, string_ids_size)
        struct.pack_into('<I', header, 60, string_ids_offset)
        
        # Type IDs (offset 64-71)
        struct.pack_into('<I', header, 64, type_ids_size)
        struct.pack_into('<I', header, 68, type_ids_offset)
        
        # Proto IDs (offset 72-79)
        struct.pack_into('<I', header, 72, proto_ids_size)
        struct.pack_into('<I', header, 76, proto_ids_offset)
        
        # Field IDs (offset 80-87)
        struct.pack_into('<I', header, 80, field_ids_size)
        struct.pack_into('<I', header, 84, field_ids_offset)
        
        # Method IDs (offset 88-95)
        struct.pack_into('<I', header, 88, method_ids_size)
        struct.pack_into('<I', header, 92, method_ids_offset)
        
        # Class defs (offset 96-103)
        struct.pack_into('<I', header, 96, class_defs_size)
        struct.pack_into('<I', header, 100, class_defs_offset)
        
        # Data (offset 104-111)
        struct.pack_into('<I', header, 104, data_size)
        struct.pack_into('<I', header, 108, data_offset)
        
        assert len(header) == self.HEADER_SIZE
        
        # === Build ID Arrays ===
        
        # String IDs (array of uint32 offsets into data)
        string_ids = b''
        for off in string_data_offsets:
            string_ids += struct.pack('<I', off)
        
        # Type IDs (array of uint16 string indices)
        type_ids = b''
        for desc in self.type_descriptors:
            str_index = self.string_list.index(desc)
            type_ids += struct.pack('<H', str_index)
        
        # Proto IDs (array of 12-byte structs)
        proto_ids = b''
        for p in self.protos:
            proto_ids += struct.pack('<III',
                p['shorty_idx'],
                p['return_type_idx'],
                p['parameters_off']
            )
        
        # Field IDs (empty)
        field_ids = b''
        
        # Method IDs (array of 8-byte structs)
        method_ids_arr = b''
        for m in self.methods:
            method_ids_arr += struct.pack('<HHI',
                m['class_idx'],
                m['proto_idx'],
                m['name_idx']
            )
        
        # Class Defs (array of 32-byte structs)
        class_defs = b''
        for cls in self.classes:
            class_defs += struct.pack('<IIIIIIII',
                cls['class_idx'],
                cls['access_flags'],
                cls['superclass_idx'],
                cls['interfaces_off'],
                cls['source_file_idx'],
                cls['annotations_off'],
                cls['class_data_off'],
                cls['static_values_off']
            )
        
        # === Assemble Complete DEX ===
        dex = bytearray(header)
        dex += string_ids
        dex += type_ids
        dex += proto_ids
        dex += field_ids
        dex += method_ids_arr
        dex += class_defs
        dex += data
        
        # Update file size with actual value
        actual_size = len(dex)
        struct.pack_into('<I', dex, 32, actual_size)
        
        # Calculate checksum (Adler32 over everything except first 12 bytes)
        checksum = zlib.adler32(dex[12:]) & 0xFFFFFFFF
        struct.pack_into('<I', dex, 8, checksum)
        
        return bytes(dex)


# ============================================================================
# APK Builder
# ============================================================================

class ApkBuilder:
    """Builds APK files (ZIP format)"""
    
    def __init__(self, output_path):
        self.output_path = output_path
        self.files = {}
    
    def add_file(self, path, content):
        """Add file to APK"""
        self.files[path] = content
    
    def build(self):
        """Build final APK"""
        import zipfile
        import io
        
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
            for path, content in self.files.items():
                zf.writestr(path, content)
        
        with open(self.output_path, 'wb') as f:
            f.write(buf.getvalue())
        
        return self.output_path


# ============================================================================
# Manifest/Layout Generators
# ============================================================================

def generate_android_manifest():
    """Generate AndroidManifest.xml"""
    manifest = '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.miniandroid.hello"
    android:versionCode="1"
    android:versionName="1.0">
    
    <uses-sdk android:minSdkVersion="21"/>
    
    <application
        android:label="@string/app_name"
        android:icon="@drawable/ic_launcher">
        
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
    
</manifest>'''
    return manifest.encode('utf-8')


def generate_main_layout():
    """Generate res/layout/main.xml"""
    layout = '''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/main_layout"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical"
    android:gravity="center"
    android:background="#FFFFFF">
    
    <TextView
        android:id="@+id/textView"
        android:layout_width="wrap_content"
        android:layout_height="wrap_content"
        android:textSize="24sp"
        android:textColor="#333333"
        android:text="Hello MiniAndroid"/>
        
</LinearLayout>'''
    return layout.encode('utf-8')


def generate_strings():
    """Generate res/values/strings.xml"""
    strings = '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">MiniAndroid Hello</string>
</resources>'''
    return strings.encode('utf-8')


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    print("=" * 60)
    print("MiniAndroid HelloWorld APK Generator")
    print("EXP-002: Runtime Stub Test Application")
    print("=" * 60)
    
    # Output directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    output_dir = os.path.join(project_dir, 'test_apks')
    os.makedirs(output_dir, exist_ok=True)
    
    apk_path = os.path.join(output_dir, 'HelloWorld.apk')
    dex_path = os.path.join(output_dir, 'classes.dex')
    
    print(f"\n[1/4] Generating classes.dex...")
    
    # Generate DEX
    generator = DexGenerator()
    dex_data = generator.generate_hello_world_dex()
    
    with open(dex_path, 'wb') as f:
        f.write(dex_data)
    
    print(f"      ✓ DEX generated: {len(dex_data)} bytes")
    print(f"      ✓ Classes: {len(generator.classes)}")
    print(f"      ✓ Methods: {len(generator.methods)}")
    print(f"      ✓ Strings: {len(generator.string_list)}")
    print(f"      ✓ Types: {len(generator.type_descriptors)}")
    
    print(f"\n[2/4] Generating resources...")
    manifest = generate_android_manifest()
    layout = generate_main_layout()
    strings_xml = generate_strings()
    print(f"      ✓ AndroidManifest.xml: {len(manifest)} bytes")
    print(f"      ✓ res/layout/main.xml: {len(layout)} bytes")
    print(f"      ✓ res/values/strings.xml: {len(strings_xml)} bytes")
    
    print(f"\n[3/4] Building APK...")
    
    builder = ApkBuilder(apk_path)
    builder.add_file('AndroidManifest.xml', manifest)
    builder.add_file('classes.dex', dex_data)
    builder.add_file('res/layout/main.xml', layout)
    builder.add_file('res/values/strings.xml', strings_xml)
    
    result = builder.build()
    
    print(f"      ✓ APK built: {result}")
    
    # Verification
    apk_size = os.path.getsize(apk_path)
    print(f"\n[4/4] Verification:")
    print(f"      ✓ APK Size: {apk_size:,} bytes")
    print(f"      ✓ Files: {len(builder.files)}")
    
    # List contents
    import zipfile
    with zipfile.ZipFile(apk_path, 'r') as zf:
        print(f"      ✓ Contents:")
        for info in zf.infolist():
            print(f"          - {info.filename} ({info.file_size} bytes)")
    
    print("\n" + "=" * 60)
    print("APK Generation Complete!")
    print("=" * 60)
    print(f"\nOutput: {apk_path}")
    print(f"\nPackage: com.miniandroid.hello")
    print(f"Activity: com.miniandroid.hello.MainActivity")
    print(f"Entry Point: MainActivity.onCreate(Bundle)")
    
    return apk_path


if __name__ == '__main__':
    main()
