#!/usr/bin/env python3
"""
EXP-063: Minimal ARSC (Android Resource Table) parser.

Parses resources.arsc from an APK and resolves resource IDs to values.
This is a GENERIC parser — not Telegram-specific.

Format reference: AOSP frameworks/base/include/androidfw/ResourceTypes.h

Key structures:
  ResTable_header: type(u2), header_size(u2), total_size(u4), package_count(u4)
  ResStringPool: type(u2), header_size(u2), total_size(u4), string_count(u4), ...
  ResTable_package: type(u2), header_size(u2), total_size(u4), id(u4), name[256], ...
  ResTable_type: type(u2), header_size(u2), total_size(u4), id(u1), flags(u1), entry_count(u4), ...

Usage:
  python3 exp063_arsc_parser.py <apk_path> [resource_id ...]
"""
import struct, sys, zipfile

class ARSCParser:
    def __init__(self, arsc_data):
        self.data = arsc_data
        self.global_strings = []  # String pool entries
        self.packages = {}  # package_id → {type_id → {entry_idx → value}}
        self.package_names = {}  # package_id → name
        self._parse()

    def _read_uleb128(self, offset):
        result = 0; shift = 0
        while True:
            b = self.data[offset]; offset += 1
            result |= (b & 0x7f) << shift
            shift += 7
            if not (b & 0x80): break
        return result, offset

    def _parse_string_pool(self, offset):
        """Parse a ResStringPool at the given offset."""
        type_val, header_size, total_size = struct.unpack_from('<HHI', self.data, offset)
        # header: type(2), header_size(2), total_size(4), string_count(4), style_count(4), flags(4), strings_start(4), styles_start(4)
        string_count, style_count, flags, strings_start, styles_start = struct.unpack_from('<IIIHH', self.data, offset + 8)
        # Actually the ResStringPool_header is:
        # type(2), header_size(2), total_size(4), string_count(4), style_count(4), flags(4), strings_start(4), styles_start(4)
        string_count, style_count, flags, strings_start, styles_start = struct.unpack_from('<IIIII', self.data, offset + 8)
        
        is_utf8 = (flags & 0x100) != 0
        offsets_start = offset + header_size
        abs_strings_start = offset + strings_start
        
        strings = []
        for i in range(string_count):
            str_off = struct.unpack_from('<I', self.data, offsets_start + i * 4)[0]
            pos = abs_strings_start + str_off
            if is_utf8:
                # UTF-8 string pool entry format (per AOSP ResStringPool.cpp):
                # uleb128: utf16_length (number of UTF-16 code units)
                # uleb128: byte_length (number of UTF-8 bytes)
                # Then byte_length bytes of string data, then null terminator
                # NOTE: BOTH uleb128 values are ALWAYS present, even when
                # utf16_length < 0x80.
                utf16_len, pos = self._read_uleb128(pos)
                byte_len, pos = self._read_uleb128(pos)
                # EXP-063: Bounds check to prevent OOM
                if byte_len < 0 or byte_len > 100000:
                    strings.append('')
                else:
                    strings.append(self.data[pos:pos+byte_len].decode('utf-8', errors='replace'))
            else:
                # UTF-16: u2 length, then UTF-16 chars, then null
                length = struct.unpack_from('<H', self.data, pos)[0]
                if length > 0:
                    s = self.data[pos+2:pos+2+length*2].decode('utf-16-le', errors='replace')
                    strings.append(s)
                else:
                    strings.append('')
        return strings

    def _parse(self):
        """Parse the entire ARSC."""
        if len(self.data) < 12:
            return
        
        # RES_TABLE_TYPE header
        type_val, header_size, total_size = struct.unpack_from('<HHI', self.data, 0)
        if type_val != 0x0002:
            return
        
        # Parse global string pool at offset header_size
        pos = header_size
        if pos >= len(self.data): return
        
        pool_type = struct.unpack_from('<H', self.data, pos)[0]
        if pool_type == 0x0001:  # RES_STRING_POOL_TYPE
            pool_total_size = struct.unpack_from('<I', self.data, pos + 4)[0]
            self.global_strings = self._parse_string_pool(pos)
            pos += pool_total_size
        
        # EXP-063: Telegram's ARSC uses a non-standard format where a large
        # container chunk (type=0x0200) wraps the package data.
        # The container header is 288 bytes, and inside it are:
        #   - String pool (type names like "string", "drawable")
        #   - String pool (key names like "StartMessaging")
        #   - PACKAGE + TYPE chunk pairs
        # We parse the sub-chunks directly.
        
        # Check if the next chunk is a container (type=0x0200 with large hs)
        if pos + 8 <= len(self.data):
            ct = struct.unpack_from('<H', self.data, pos)[0]
            chs = struct.unpack_from('<H', self.data, pos + 2)[0]
            cts = struct.unpack_from('<I', self.data, pos + 4)[0]
            
            if ct == 0x0200 and chs > 20:
                # This is a container — parse sub-chunks
                self._parse_container(pos, chs, cts)
                return
        
        # Standard format: parse PACKAGE chunks directly
        while pos < len(self.data):
            if pos + 8 > len(self.data): break
            chunk_type = struct.unpack_from('<H', self.data, pos)[0]
            chunk_header_size = struct.unpack_from('<H', self.data, pos + 2)[0]
            chunk_total_size = struct.unpack_from('<I', self.data, pos + 4)[0]
            
            if chunk_type == 0x0202:  # RES_TABLE_PACKAGE_TYPE
                self._parse_package(pos, chunk_header_size, chunk_total_size)
            
            if chunk_total_size == 0: break
            pos += chunk_total_size

    def _parse_container(self, offset, header_size, total_size):
        """Parse a non-standard container chunk (Telegram resource shrinking format).

        The container has header_size bytes of header, then sub-chunks:
        - String pool (type names)
        - String pool (key names)
        - PACKAGE + TYPE chunk pairs
        """
        # Parse the type name string pool and key name string pool
        sub_pos = offset + header_size
        end_pos = offset + total_size

        type_names = []
        key_names = []
        current_pkg_id = 0  # Track the current package ID for TYPE chunks

        # First two sub-chunks should be string pools
        for i in range(2):
            if sub_pos + 8 > len(self.data) or sub_pos >= end_pos: break
            ct = struct.unpack_from('<H', self.data, sub_pos)[0]
            chs = struct.unpack_from('<H', self.data, sub_pos + 2)[0]
            cts = struct.unpack_from('<I', self.data, sub_pos + 4)[0]

            if ct == 0x0001:  # STRING_POOL
                pool = self._parse_string_pool(sub_pos)
                if i == 0:
                    type_names = pool
                else:
                    key_names = pool

            sub_pos += cts

        # Now parse PACKAGE + TYPE pairs
        while sub_pos < end_pos:
            if sub_pos + 8 > len(self.data): break
            ct = struct.unpack_from('<H', self.data, sub_pos)[0]
            chs = struct.unpack_from('<H', self.data, sub_pos + 2)[0]
            cts = struct.unpack_from('<I', self.data, sub_pos + 4)[0]

            if ct == 0x0202:  # PACKAGE
                # ResTable_package: type(2), header(2), total(4), id(4), name[256], type_sp_off(4), key_sp_off(4)
                current_pkg_id = struct.unpack_from('<I', self.data, sub_pos + 8)[0]
                if current_pkg_id not in self.packages:
                    self.packages[current_pkg_id] = {}
                    self.package_names[current_pkg_id] = f"pkg{current_pkg_id}"
            elif ct == 0x0201:  # TYPE (actual resource data)
                # EXP-075: Use the ACTUAL package ID from the most recent PACKAGE chunk,
                # not hardcoded 0. This is critical for resolving resource IDs like
                # 0x7f040008 (package 0x7f, type 0x04, entry 0x0008).
                self._parse_type_data(sub_pos, chs, cts, current_pkg_id, type_names, key_names)

            if cts == 0: break
            sub_pos += cts

    def _parse_package(self, offset, header_size, total_size):
        """Parse a RES_TABLE_PACKAGE chunk."""
        # Package header: type(2), header_size(2), total_size(4), id(4), name[256], type_string_pool_off(4), key_string_pool_off(4)
        pkg_id = struct.unpack_from('<I', self.data, offset + 8)[0]
        name_bytes = self.data[offset+12:offset+12+256]
        name = name_bytes.decode('utf-16-le', errors='replace').rstrip('\x00')
        
        type_string_pool_off = struct.unpack_from('<I', self.data, offset + 12 + 256)[0]
        key_string_pool_off = struct.unpack_from('<I', self.data, offset + 12 + 256 + 4)[0]
        
        # Parse type string pool (names of types like "string", "drawable", etc.)
        type_names = []
        if type_string_pool_off > 0:
            type_names = self._parse_string_pool(offset + type_string_pool_off)
        
        # Parse key string pool (names of resources)
        key_names = []
        if key_string_pool_off > 0:
            key_names = self._parse_string_pool(offset + key_string_pool_off)
        
        self.package_names[pkg_id] = name
        self.packages[pkg_id] = {}
        
        # Parse sub-chunks (type specs and type data)
        pos = offset + header_size
        while pos < offset + total_size:
            if pos + 8 > len(self.data): break
            chunk_type = struct.unpack_from('<H', self.data, pos)[0]
            chunk_hs = struct.unpack_from('<H', self.data, pos + 2)[0]
            chunk_ts = struct.unpack_from('<I', self.data, pos + 4)[0]
            
            if chunk_type == 0x0201:  # RES_TABLE_TYPE_TYPE (actual data)
                self._parse_type_data(pos, chunk_hs, chunk_ts, pkg_id, type_names, key_names)
            elif chunk_type == 0x0200:  # RES_TABLE_TYPE_SPEC_TYPE
                pass  # Skip type specs for now
            
            if chunk_ts == 0: break
            pos += chunk_ts

    def _parse_type_data(self, offset, header_size, total_size, pkg_id, type_names, key_names):
        """Parse a RES_TABLE_TYPE chunk (contains actual resource values)."""
        # EXP-063: The header layout differs from standard AOSP.
        # Standard: type(2), header_size(2), total_size(4), id(1), flags(1), entry_count(4), entries_start(4), config...
        # Telegram ARSC: type(2), header_size(2), total_size(4), id(4), entry_count(4), entries_start(4), config...
        # The id field is 4 bytes instead of 1+1, and entry_count is at offset+12.
        type_id_raw = struct.unpack_from('<I', self.data, offset + 8)[0]
        type_id = type_id_raw & 0xFF  # Low byte is the actual type ID
        entry_count = struct.unpack_from('<I', self.data, offset + 12)[0]
        entries_start = struct.unpack_from('<I', self.data, offset + 16)[0]

        type_name = type_names[type_id - 1] if type_names and type_id <= len(type_names) else f"type{type_id}"
        
        if pkg_id not in self.packages:
            self.packages[pkg_id] = {}
        if type_name not in self.packages[pkg_id]:
            self.packages[pkg_id][type_name] = {}
        
        # Parse entry offset table
        offsets_start = offset + header_size  # After the header
        for i in range(entry_count):
            if offsets_start + i * 4 + 4 > len(self.data): break
            entry_off = struct.unpack_from('<I', self.data, offsets_start + i * 4)[0]
            if entry_off == 0xFFFFFFFF:
                continue  # No entry
            
            abs_off = offset + entries_start + entry_off
            if abs_off + 8 > len(self.data): continue
            
            # ResTable_entry: size(2), flags(2), key(4)
            entry_size, entry_flags, key_idx = struct.unpack_from('<HHI', self.data, abs_off)
            
            key_name = key_names[key_idx] if key_idx < len(key_names) else f"key{key_idx}"
            
            # If entry_flags & 0x0001 (FLAG_COMPLEX), value is a ResTable_map
            if entry_flags & 0x0001:
                # Skip complex entries for now
                continue
            
            # Res_value: size(2), res0(1), dataType(1), data(4)
            val_off = abs_off + 8  # After ResTable_entry
            val_size, res0, data_type, data_val = struct.unpack_from('<HBBi', self.data, val_off)
            
            # Resolve value based on dataType
            resolved = None
            if data_type == 0x03:  # TYPE_STRING
                if 0 <= data_val < len(self.global_strings):
                    resolved = self.global_strings[data_val]
                else:
                    resolved = f"<string:{data_val}>"
            elif data_type == 0x01:  # TYPE_REFERENCE
                resolved = f"@0x{data_val & 0xFFFFFFFF:08x}"
            elif data_type == 0x10:  # TYPE_INT_DEC
                resolved = data_val
            elif data_type == 0x11:  # TYPE_INT_HEX
                resolved = f"0x{data_val & 0xFFFFFFFF:08x}"
            elif data_type == 0x1d:  # TYPE_INT_BOOLEAN
                resolved = bool(data_val)
            else:
                resolved = f"type{data_type}:0x{data_val & 0xFFFFFFFF:08x}"
            
            # Resource ID = (pkg_id << 24) | (type_id << 16) | entry_index
            res_id = (pkg_id << 24) | (type_id << 16) | i
            
            # EXP-063: Only store if not already present (first occurrence wins).
            # Multiple TYPE chunks (one per locale) have the same entries.
            # The first one defines the resource ID mapping.
            if key_name not in self.packages[pkg_id][type_name]:
                self.packages[pkg_id][type_name][key_name] = {
                    'res_id': res_id,
                    'value': resolved,
                    'data_type': data_type,
                }

    def resolve_string(self, res_id):
        """Resolve a resource ID to a string value.

        The AXML uses runtime package IDs (typically 0x7f) but the ARSC
        stores resource IDs with internal package IDs (e.g., 0x03). We match
        on the low 24 bits (type_id + entry_idx) which are the same in both.
        """
        target_low = res_id & 0x00FFFFFF

        # First try exact match
        pkg_id = (res_id >> 24) & 0xFF
        if pkg_id in self.packages:
            for type_name, entries in self.packages[pkg_id].items():
                for key_name, info in entries.items():
                    if info['res_id'] == res_id:
                        return info['value']

        # Fall back to matching on low 24 bits (type_id + entry_idx)
        for pid in self.packages:
            for type_name, entries in self.packages[pid].items():
                for key_name, info in entries.items():
                    if (info['res_id'] & 0x00FFFFFF) == target_low:
                        return info['value']
        return None

    def resolve_layout_path(self, res_id):
        """Resolve a layout resource ID to its AXML file path in the APK."""
        val = self.resolve_string(res_id)
        if val and isinstance(val, str) and val.startswith('res/layout'):
            return val
        return None

    def dump_summary(self, max_per_type=5):
        """Print a summary of all resources."""
        for pkg_id, name in self.package_names.items():
            print(f"Package: {name} (id={pkg_id})")
            for type_name, entries in self.packages.get(pkg_id, {}).items():
                count = len(entries)
                print(f"  {type_name}: {count} entries")
                for key_name, info in list(entries.items())[:max_per_type]:
                    print(f"    {key_name}: {info['value']!r}")


def main():
    apk_path = sys.argv[1] if len(sys.argv) > 1 else \
        '/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/download/exp038_telegram/Telegram.apk'
    
    with zipfile.ZipFile(apk_path) as z:
        arsc_data = z.read('resources.arsc')
    
    print(f"resources.arsc: {len(arsc_data)} bytes")
    parser = ARSCParser(arsc_data)
    
    print(f"\nGlobal string pool: {len(parser.global_strings)} strings")
    print(f"Packages: {len(parser.packages)}")
    
    parser.dump_summary()
    
    # Resolve test IDs
    if len(sys.argv) > 2:
        print("\nResolving resource IDs:")
        for arg in sys.argv[2:]:
            rid = int(arg, 0)
            result = parser.resolve_string(rid)
            print(f"  0x{rid:08x}: {result!r}")


if __name__ == '__main__':
    main()
