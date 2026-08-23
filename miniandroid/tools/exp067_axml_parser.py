#!/usr/bin/env python3
"""
EXP-067 Phase 4: Generic AXML (Android Binary XML) parser.

Parses Android's compiled XML format (AXML) used in:
  - AndroidManifest.xml
  - res/layout/*.xml
  - res/drawable/*.xml
  - res/color/*.xml

Output: JSON tree of elements with attributes.
"""
import json
import os
import struct
import sys
import zipfile


# Chunk types (from AOSP ResourceTypes.h)
RES_STRING_POOL = 0x0001
RES_XML = 0x0003  # The file header type
RES_XML_RESOURCE_MAP = 0x0180
RES_XML_START_NAMESPACE = 0x0100
RES_XML_END_NAMESPACE = 0x0101
RES_XML_START_ELEMENT = 0x0102
RES_XML_END_ELEMENT = 0x0103
RES_XML_CDATA = 0x0104

UTF8_FLAG = 0x100

# TypedValue data types
TYPE_NULL = 0x00
TYPE_REFERENCE = 0x01
TYPE_ATTRIBUTE = 0x02
TYPE_STRING = 0x03
TYPE_FLOAT = 0x04
TYPE_DIMENSION = 0x05
TYPE_FRACTION = 0x06
TYPE_INT_DEC = 0x10
TYPE_INT_HEX = 0x11
TYPE_INT_BOOLEAN = 0x12
TYPE_INT_COLOR_ARGB8 = 0x1c
TYPE_INT_COLOR_RGB8 = 0x1d
TYPE_INT_COLOR_ARGB4 = 0x1e
TYPE_INT_COLOR_RGB4 = 0x1f


class AXMLParser:
    def __init__(self, data):
        self.data = data
        self.pos = 0
        self.strings = []
        self.resource_map = []
        self.namespaces = {}

    def parse(self):
        if len(self.data) < 8:
            raise ValueError("AXML too short")
        file_type, header_size, file_size = struct.unpack_from('<HHI', self.data, 0)
        if header_size != 0x0008:
            raise ValueError(f"Not AXML (header_size=0x{header_size:04x})")
        self.pos = header_size

        root = None
        stack = []

        while self.pos < len(self.data):
            chunk = self._read_chunk()
            if chunk is None:
                break
            ctype = chunk['type']
            if ctype == RES_STRING_POOL:
                self.strings = self._parse_string_pool(chunk['data'])
            elif ctype == RES_XML_RESOURCE_MAP:
                self.resource_map = self._parse_resource_map(chunk['data'])
            elif ctype == RES_XML_START_NAMESPACE:
                prefix, uri = self._parse_namespace(chunk['data'])
                self.namespaces[prefix] = uri
            elif ctype == RES_XML_END_NAMESPACE:
                pass
            elif ctype == RES_XML_START_ELEMENT:
                elem = self._parse_start_element(chunk['data'])
                if not stack:
                    root = elem
                else:
                    stack[-1]['children'].append(elem)
                stack.append(elem)
            elif ctype == RES_XML_END_ELEMENT:
                if stack:
                    stack.pop()
            elif ctype == RES_XML_CDATA:
                if stack:
                    cdata = self._parse_cdata(chunk['data'])
                    stack[-1]['children'].append({'type': 'cdata', 'text': cdata})

        return root

    def _read_chunk(self):
        if self.pos + 8 > len(self.data):
            return None
        ctype, header_size, size = struct.unpack_from('<HHI', self.data, self.pos)
        if size < 8 or self.pos + size > len(self.data):
            self.pos = len(self.data)
            return None
        # chunk_data starts AFTER the chunk header (header_size bytes).
        # For STRING_POOL: header_size=28 (8 chunk + 20 pool) — but the pool header
        #   is PART of the chunk header, so chunk_data starts after it.
        # Wait — that's wrong. Let me re-check.
        # Actually for STRING_POOL, header_size=28 means the chunk header is 28 bytes
        # (8 bytes type+header_size+size, then 20 bytes pool header). The pool header
        # is NOT part of chunk_data. chunk_data starts at pos+28.
        # For START_ELEMENT, header_size=16 means the chunk header is 16 bytes
        # (8 bytes type+header_size+size, then 8 bytes element header ns+name+...).
        # Wait — no. The element header is ns(4)+name(4)+attrStart(2)+attrSize(2)+attrCount(2)+
        # idIndex(2)+classIndex(2)+styleIndex(2) = 20 bytes. So header_size should be 28 (8+20).
        # But we see header_size=16. Let me re-check...
        # Actually the ResXMLTree_node header is: type(2)+headerSize(2)+lineNumber(4)+comment(4) = 16 bytes.
        # So header_size=16 means the node-specific header is 16 bytes (8 chunk + 8 node).
        # For START_ELEMENT, after the 16-byte header, the next 20 bytes are:
        #   ns(4)+name(4)+attrStart(2)+attrSize(2)+attrCount(2)+idIndex(2)+classIndex(2)+styleIndex(2)
        # These are the "attribute start" info, and they're at offset 16-36 in the chunk.
        # But chunk_data starts at pos+header_size=pos+16. So chunk_data[0:20] is the
        # ns/name/attrStart/... fields.
        # For STRING_POOL, header_size=28. The first 20 bytes of chunk_data are the
        # pool header (sc/stc/flags/ss/sts). So chunk_data[0:20] is the pool header.
        # Wait — if header_size=28 and the chunk starts with 8 bytes (type+hs+size) + 20 bytes
        # (pool header), then chunk_data = data[pos+28:pos+size] starts AFTER the pool header.
        # But we need the pool header to know string_count etc.!
        #
        # Let me reconsider. The header_size field tells us where the PAYLOAD starts.
        # For STRING_POOL: header_size=28 → payload (offsets + strings) starts at pos+28.
        #   The pool header (sc/stc/flags/ss/sts) is at pos+8 to pos+28 (20 bytes).
        #   So chunk_data should be data[pos+8:pos+size] to INCLUDE the pool header.
        #
        # Actually no — the standard AOSP chunk format is:
        #   chunk header: type(2) + header_size(2) + size(4)  = 8 bytes
        #   chunk-specific header: varies (pool header for STRING_POOL, node header for elements)
        #   chunk payload: the actual data
        # The header_size field includes BOTH the 8-byte chunk header AND the chunk-specific header.
        # So payload starts at pos+header_size.
        #
        # For STRING_POOL: header_size=28 → payload (offsets) at pos+28. Pool header at pos+8.
        # For START_ELEMENT: header_size=16 → payload (attrStart info + attrs) at pos+16.
        #   But wait — the START_ELEMENT header is: type(2)+hs(2)+lineNumber(4)+comment(4) = 12 bytes.
        #   Then ns(4)+name(4)+attrStart(2)+attrSize(2)+attrCount(2)+idIndex(2)+classIndex(2)+styleIndex(2)
        #   = 20 bytes. Total header = 12+20 = 32 bytes. But header_size=16??
        #
        # I think the confusion is: header_size=16 means the chunk header is 16 bytes
        # (8 chunk + 8 node: lineNumber+comment). The ns/name/attrStart/... are NOT part of
        # the header — they're part of the chunk PAYLOAD. So chunk_data = data[pos+16:pos+size]
        # and chunk_data[0:20] = ns/name/attrStart/...
        #
        # For STRING_POOL: header_size=28 means the chunk header is 28 bytes
        # (8 chunk + 20 pool: sc/stc/flags/ss/sts). The offsets and strings are the payload.
        # So chunk_data = data[pos+28:pos+size] starts at the offsets array, NOT the pool header.
        #
        # So my _parse_string_pool needs the pool header, but chunk_data doesn't include it!
        # Let me pass the FULL chunk data (pos+8 to pos+size) and have parsers use header_size
        # to find their specific header.
        chunk_data = self.data[self.pos + 8 : self.pos + size]  # everything after 8-byte chunk header
        self.pos += size
        return {'type': ctype, 'header_size': header_size, 'size': size, 'data': chunk_data}

    def _parse_string_pool(self, data):
        # data[0:20] = pool header: string_count, style_count, flags, strings_start, styles_start
        if len(data) < 20:
            return []
        string_count, style_count, flags, strings_start, styles_start = \
            struct.unpack_from('<IIIII', data, 0)
        is_utf8 = (flags & UTF8_FLAG) != 0
        # String offsets array starts at offset 20
        offsets = []
        for i in range(string_count):
            if 20 + i * 4 + 4 <= len(data):
                offsets.append(struct.unpack_from('<I', data, 20 + i * 4)[0])
            else:
                offsets.append(0)
        # strings_start is offset from chunk START (includes 8-byte chunk header).
        # data starts at chunk+8, so strings_data_offset = strings_start - 8.
        strings_data_offset = strings_start - 8
        if strings_data_offset < 0:
            strings_data_offset = 20 + string_count * 4  # fallback
        strings = []
        for off in offsets:
            pos = strings_data_offset + off
            if pos < 0 or pos >= len(data):
                strings.append("")
                continue
            s = self._read_string(data, pos, is_utf8)
            strings.append(s)
        return strings

    def _read_string(self, data, pos, is_utf8):
        if is_utf8:
            # UTF-8: uleb128 chars_count, uleb128 bytes_count, then UTF-8 bytes + null
            chars_count = data[pos]; pos += 1
            if chars_count & 0x80:
                chars_count = ((chars_count & 0x7F) << 8) | data[pos]; pos += 1
            bytes_count = data[pos]; pos += 1
            if bytes_count & 0x80:
                bytes_count = ((bytes_count & 0x7F) << 8) | data[pos]; pos += 1
            end = data.find(b'\x00', pos)
            if end == -1:
                end = pos + bytes_count
            return data[pos:end].decode('utf-8', errors='replace')
        else:
            # UTF-16: u2 chars_count, then UTF-16LE bytes + null
            if pos + 2 > len(data):
                return ""
            chars_count = struct.unpack_from('<H', data, pos)[0]; pos += 2
            if chars_count & 0x8000:
                chars_count = ((chars_count & 0x7FFF) << 16) | struct.unpack_from('<H', data, pos)[0]
                pos += 2
            end = pos + chars_count * 2
            if end > len(data):
                end = len(data)
            try:
                return data[pos:end].decode('utf-16-le', errors='replace')
            except:
                return ""

    def _parse_resource_map(self, data):
        count = len(data) // 4
        return list(struct.unpack_from(f'<{count}I', data, 0))

    def _parse_namespace(self, data):
        if len(data) < 8:
            return ("", "")
        ns_idx, uri_idx = struct.unpack_from('<II', data, 0)
        prefix = self.strings[ns_idx] if ns_idx < len(self.strings) else ""
        uri = self.strings[uri_idx] if uri_idx < len(self.strings) else ""
        return (prefix, uri)

    def _parse_start_element(self, data):
        # ResXMLTree_node header: type(2) + headerSize(2) + lineNumber(4) + comment(4) = 16 bytes
        # But chunk_data starts at pos+8 (after type+headerSize+size), so:
        #   data[0:4] = lineNumber
        #   data[4:8] = comment
        #   data[8:28] = ExtXMLNode: ns(4), name(4), attrStart(2), attrSize(2), attrCount(2),
        #                            idIndex(2), classIndex(2), styleIndex(2)
        if len(data) < 28:
            return {'type': 'element', 'name': '?', 'ns': '', 'attributes': {}, 'children': []}
        ns_idx, name_idx, attr_start, attr_size, attr_count, \
            id_idx, class_idx, style_idx = struct.unpack_from('<IIHHHHHH', data, 8)
        name = self.strings[name_idx] if name_idx < len(self.strings) else f"?{name_idx}"
        ns = self.strings[ns_idx] if ns_idx < len(self.strings) else ""
        full_name = f"{ns}:{name}" if ns else name

        attributes = {}
        # attr_start is the offset from the START of the ResXMLTree_node_ext struct
        # (which begins at chunk+16). So attrs are at chunk+16+attr_start.
        # In chunk_data (starts at chunk+8), attrs are at 16+attr_start-8 = 8+attr_start.
        attr_data_start = 8 + attr_start
        for i in range(attr_count):
            off = attr_data_start + i * attr_size
            if off < 0 or off + 20 > len(data):
                break
            attr_ns, attr_name, raw_value, \
                typed_size, typed_res0, typed_dtype, typed_data = \
                struct.unpack_from('<IIIHBBi', data, off)
            attr_full_name = self.strings[attr_name] if attr_name < len(self.strings) else f"?{attr_name}"
            attr_full_ns = self.strings[attr_ns] if attr_ns < len(self.strings) else ""
            key = f"{attr_full_ns}:{attr_full_name}" if attr_full_ns else attr_full_name
            value = self._resolve_typed_value(typed_dtype, typed_data, raw_value)
            attributes[key] = value

        return {
            'type': 'element',
            'name': full_name,
            'ns': ns,
            'attributes': attributes,
            'children': [],
        }

    def _parse_cdata(self, data):
        if len(data) < 4:
            return ""
        idx = struct.unpack_from('<I', data, 0)[0]
        return self.strings[idx] if idx < len(self.strings) else ""

    def _resolve_typed_value(self, dtype, data, raw_value_idx):
        if dtype == TYPE_STRING:
            return self.strings[raw_value_idx] if raw_value_idx < len(self.strings) else ""
        elif dtype == TYPE_INT_DEC:
            return data
        elif dtype == TYPE_INT_HEX:
            return data
        elif dtype == TYPE_INT_BOOLEAN:
            return data != 0
        elif dtype in (TYPE_INT_COLOR_ARGB8, TYPE_INT_COLOR_RGB8,
                       TYPE_INT_COLOR_ARGB4, TYPE_INT_COLOR_RGB4):
            return f"#{data & 0xFFFFFFFF:08x}"
        elif dtype == TYPE_REFERENCE:
            return f"@0x{data & 0xFFFFFFFF:08x}"
        elif dtype == TYPE_DIMENSION:
            unit = (data >> 24) & 0xFF
            val = data & 0x00FFFFFF
            units = {0: 'px', 1: 'dp', 2: 'sp', 3: 'pt', 4: 'in', 5: 'mm'}
            return f"{val}{units.get(unit, '?')}"
        elif dtype == TYPE_FRACTION:
            return f"{data}f"
        elif dtype == TYPE_FLOAT:
            import struct as s
            return s.unpack('<f', s.pack('<i', data))[0]
        else:
            return f"type{dtype}:0x{data & 0xFFFFFFFF:08x}"


def parse_axml(data):
    parser = AXMLParser(data)
    return parser.parse()


def main():
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <apk_path> <resource_path> [output_json]")
        sys.exit(1)
    apk_path = sys.argv[1]
    res_path = sys.argv[2]
    out_path = sys.argv[3] if len(sys.argv) > 3 else None

    with zipfile.ZipFile(apk_path) as z:
        try:
            with z.open(res_path) as f:
                data = f.read()
        except KeyError:
            print(f"Error: {res_path} not found in APK", file=sys.stderr)
            sys.exit(1)

    print(f"[AXML] Parsing {res_path} ({len(data)} bytes)")
    tree = parse_axml(data)

    if out_path:
        os.makedirs(os.path.dirname(out_path) or '.', exist_ok=True)
        with open(out_path, 'w') as f:
            json.dump(tree, f, indent=2, default=str)
        print(f"[AXML] Written to {out_path}")
    else:
        print(json.dumps(tree, indent=2, default=str)[:2000])


if __name__ == '__main__':
    main()
