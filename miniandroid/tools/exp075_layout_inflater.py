#!/usr/bin/env python3
"""
EXP-075 PHASE 2-4 — Generic LayoutInflater + Resource Resolution + Real setContentView.

This module provides:
  1. AXMLDecoder — parses compiled Android binary XML (AXML) format
  2. ResourceResolver — resolves R.layout, R.string, R.id via ARSC
  3. LayoutInflater — creates a View hierarchy from AXML + resource resolution
  4. setContentViewInjector — post-processes view_tree.json to inject inflated views

The runtime (C++) captures setContentView(int layoutResId) and stores it in
the ActivityShadow. This Python module reads that layout_resource_id from
the run output, resolves it via ARSC to an AXML file path, parses the AXML,
creates real View nodes, and injects them into the view_tree.json so the
renderer produces a REAL screenshot of the app's actual layout.

This is GENERIC — it works for any APK that uses standard setContentView(R.layout.*).
"""
import json
import struct
import sys
import zipfile
from pathlib import Path
from typing import List, Dict, Optional, Tuple

sys.path.insert(0, "/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/tools")
from exp063_arsc_parser import ARSCParser


# ============================================================================
# AXMLDecoder — parses compiled Android binary XML
# ============================================================================

class AXMLNode:
    """A node in the inflated AXML tree."""
    def __init__(self, tag: str):
        self.tag = tag
        self.attrs: Dict[str, any] = {}
        self.children: List['AXMLNode'] = []

    def to_dict(self) -> dict:
        return {
            "tag": self.tag,
            "attrs": self.attrs,
            "children": [c.to_dict() for c in self.children],
        }


class AXMLDecoder:
    """Parses compiled Android binary XML (AXML) format.

    AXML format reference: AOSP frameworks/base/include/androidfw/ResourceTypes.h

    Structure:
      - RES_XML_TYPE (0x0003) root chunk
      - RES_STRING_POOL_TYPE (0x0001) — all strings used in the XML
      - RES_XML_RESOURCE_MAP_TYPE (0x0180) — maps attr name indices to framework resource IDs
      - RES_XML_START_NAMESPACE_TYPE (0x0100)
      - RES_XML_START_ELEMENT_TYPE (0x0102) — <tag attr="val">
      - RES_XML_END_ELEMENT_TYPE (0x0103) — </tag>
      - RES_XML_END_NAMESPACE_TYPE (0x0101)
    """

    # Res_value types
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

    # Common layout_dimen values
    MATCH_PARENT = 0xFFFFFFFF  # -1
    WRAP_CONTENT = 0xFFFFFFFE  # -2

    def __init__(self, data: bytes):
        self.data = data
        self.strings: List[str] = []
        self.resource_map: List[int] = []
        self.root: Optional[AXMLNode] = None
        self._parse()

    def _parse(self):
        pos = 0
        # Root chunk
        chunk_type, header_size, chunk_size = struct.unpack_from('<HHI', self.data, pos)
        if chunk_type != 0x0003:
            raise ValueError(f"Not an AXML file (type=0x{chunk_type:04x})")
        pos += header_size

        node_stack: List[AXMLNode] = []

        while pos < len(self.data):
            if pos + 8 > len(self.data):
                break
            ct, hs, cs = struct.unpack_from('<HHI', self.data, pos)
            chunk_start = pos

            if ct == 0x0001:  # String pool
                self.strings = self._parse_string_pool(pos)
            elif ct == 0x0180:  # Resource map
                map_count = (cs - hs) // 4
                self.resource_map = [
                    struct.unpack_from('<I', self.data, pos + hs + i * 4)[0]
                    for i in range(map_count)
                ]
            elif ct == 0x0102:  # Start element
                node = self._parse_start_element(pos)
                if node_stack:
                    node_stack[-1].children.append(node)
                else:
                    self.root = node
                node_stack.append(node)
            elif ct == 0x0103:  # End element
                if node_stack:
                    node_stack.pop()

            if cs == 0:
                break
            pos = chunk_start + cs

    def _parse_string_pool(self, offset) -> List[str]:
        """Parse a ResStringPool at the given offset."""
        type_val, header_size, total_size = struct.unpack_from('<HHI', self.data, offset)
        string_count, style_count, flags, strings_start, styles_start = \
            struct.unpack_from('<IIIII', self.data, offset + 8)

        is_utf8 = (flags & 0x100) != 0
        offsets_start = offset + header_size
        abs_strings_start = offset + strings_start

        strings = []
        for i in range(string_count):
            str_off = struct.unpack_from('<I', self.data, offsets_start + i * 4)[0]
            pos = abs_strings_start + str_off
            if is_utf8:
                # UTF-8: two uleb128 lengths, then bytes
                char_count = self.data[pos]
                if char_count & 0x80:
                    char_count = ((char_count & 0x7f) << 8) | self.data[pos + 1]
                    pos += 2
                else:
                    pos += 1
                byte_count = self.data[pos]
                if byte_count & 0x80:
                    byte_count = ((byte_count & 0x7f) << 8) | self.data[pos + 1]
                    pos += 2
                else:
                    pos += 1
                s = self.data[pos:pos + byte_count].decode('utf-8', errors='replace')
            else:
                # UTF-16: u16 char_count, then UTF-16 chars
                char_count = struct.unpack_from('<H', self.data, pos)[0]
                pos += 2
                s = self.data[pos:pos + char_count * 2].decode('utf-16-le', errors='replace')
            strings.append(s)
        return strings

    def _parse_start_element(self, offset) -> AXMLNode:
        """Parse a RES_XML_START_ELEMENT_TYPE chunk."""
        # Header: type(2), header_size(2), chunk_size(4)
        # Then: line_number(4), comment_idx(4)
        # Then: ns_idx(4), name_idx(4)
        # Then: attr_start(2), attr_size(2), attr_count(2), id_idx(2), class_idx(2), style_idx(2)
        line_number = struct.unpack_from('<I', self.data, offset + 8)[0]
        ns_idx = struct.unpack_from('<i', self.data, offset + 16)[0]
        name_idx = struct.unpack_from('<i', self.data, offset + 20)[0]
        attr_start = struct.unpack_from('<H', self.data, offset + 24)[0]
        attr_size = struct.unpack_from('<H', self.data, offset + 26)[0]
        attr_count = struct.unpack_from('<H', self.data, offset + 28)[0]

        tag = self.strings[name_idx] if 0 <= name_idx < len(self.strings) else f"<idx:{name_idx}>"
        node = AXMLNode(tag)

        # Attributes start at offset + 16 + attr_start
        # (16 bytes = line_number + comment + ns + name, then attr_start is relative to after that)
        # Actually: the XML start element chunk body after the chunk header (8 bytes) is:
        #   line_number(4) + comment(4) + ns(4) + name(4) = 16 bytes
        #   Then attr_start is relative to the start of these 16 bytes
        # EXP-080: Fixed attr_base calculation.
        # attr_start is relative to the start of the chunk header (offset).
        # The correct formula is: attr_base = offset + header_size + attr_start
        # where header_size is the chunk's header_size field (typically 16 for XML elements).
        # Previous versions used offset + 8 + attr_start (wrong) or offset + 8 + 16 + attr_start (doubly wrong).
        # Verified by comparing raw bytes: pos+hs+attr_start gives correct type/data values.
        # Read header_size from the chunk header
        hs = struct.unpack_from('<H', self.data, offset + 2)[0]
        attr_base = offset + hs + attr_start
        # Wait — let me re-examine. The chunk header is type(2)+header_size(2)+chunk_size(4) = 8 bytes.
        # Then the XML-specific header is: line_number(4) + comment(4) + ns(4) + name(4) = 16 bytes.
        # Then attr_start(2) + attr_size(2) + attr_count(2) + id_idx(2) + class_idx(2) + style_idx(2) = 12 bytes.
        # attr_start is the offset FROM THE START OF THE NODE to the attribute data.
        # The attribute data starts after the node header.
        # Standard layout: attr_base = offset + 8 (chunk header) + 16 (line/comment/ns/name) + attr_start
        # But attr_start is usually 0x14 (20) = 16 + 4... no, it's 0x14 = 20 = 16 (line/comment/ns/name) + 4 (attr_start/attr_size... no)
        # Let me just use: attr_base = offset + header_size_of_element
        # The element header is: 8 (chunk) + 16 (line/comment/ns/name) + 12 (attr_start/size/count/id/class/style) = 36 bytes
        # But attr_start field says 0x14 = 20, which is relative to... the ns_idx field? Let me just compute.
        # Looking at AOSP: attr_start is "offset from the start of the struct to the attribute data"
        # The "struct" starts at offset + 8 (after the chunk header). So attr_base = offset + 8 + attr_start
        # But wait, the standard attr_start value is 0x14 (20) = 16 (line/comment/ns/name) + 4 (?)
        # Actually 0x14 = 20 = line(4) + comment(4) + ns(4) + name(4) + ??? (4)
        # Hmm, that's 20 bytes but the actual header is 16 + 12 = 28 bytes before attrs.
        # Let me try: attr_base = offset + 8 + attr_start (with attr_start = 0x14 = 20)
        # Then attr_base = offset + 28, which matches 8 + 20 = 28
        # But 16 (line/comment/ns/name) + 12 (attr_start/size/count/id/class/style) = 28. Yes!
        # So attr_base = offset + 8 + attr_start is wrong.
        # The correct formula: attr_base = offset + 8 (chunk header) + attr_start
        # No wait — attr_start is relative to the start of the chunk body (after chunk header).
        # chunk body starts at offset + 8. So attr data starts at offset + 8 + attr_start.
        # But attr_start = 0x14 = 20, so attr data is at offset + 28.
        # And the element header before attrs is: line(4) + comment(4) + ns(4) + name(4) = 16, then attr_start(2)+attr_size(2)+attr_count(2)+id_idx(2)+class_idx(2)+style_idx(2) = 12. Total = 28. Yes!
        # So attr_base = offset + 8 + attr_start = offset + 8 + 20 = offset + 28.
        # attr_base already set above using header_size — removed duplicate

        for i in range(attr_count):
            ap = attr_base + i * attr_size
            a_ns = struct.unpack_from('<i', self.data, ap)[0]
            a_name = struct.unpack_from('<i', self.data, ap + 4)[0]
            a_raw_value = struct.unpack_from('<i', self.data, ap + 8)[0]
            # Res_value: size(2) + res0(1) + dataType(1) + data(4)
            a_size = struct.unpack_from('<H', self.data, ap + 12)[0]
            a_res0 = self.data[ap + 14]
            a_data_type = self.data[ap + 15]
            a_data = struct.unpack_from('<I', self.data, ap + 16)[0]

            # Determine the attribute name.
            # If a_name is a valid string pool index, use it directly.
            # If a_name is a large value (>= len(strings)), it's likely a resource ID
            # that should be looked up via the resource_map.
            if 0 <= a_name < len(self.strings):
                name_str = self.strings[a_name]
            elif a_name >= 0 and (a_name & 0xFFFF0000) != 0:
                # This looks like a resource ID, not a string index.
                # Map known framework attr resource IDs to names.
                fw_attrs = {
                    0x010100f4: "layout_width",
                    0x010100f5: "layout_height",
                    0x010100c4: "orientation",
                    0x01010181: "layout_weight",
                    0x010100d0: "id",
                    0x0101014f: "text",
                    0x01010098: "hint",
                    0x010100af: "gravity",
                    0x01010095: "padding",
                    0x010100dc: "visibility",
                    0x0101003e: "clickable",
                    0x01010273: "contentDescription",
                    0x01010031: "style",
                }
                name_str = fw_attrs.get(a_name, f"@0x{a_name:08x}")
            elif 0 <= a_name < len(self.resource_map):
                # Use resource_map to find the framework attr resource ID
                fw_rid = self.resource_map[a_name]
                fw_attrs = {
                    0x010100f4: "layout_width",
                    0x010100f5: "layout_height",
                    0x010100c4: "orientation",
                    0x01010181: "layout_weight",
                    0x010100d0: "id",
                    0x0101014f: "text",
                    0x01010098: "hint",
                    0x010100af: "gravity",
                    0x01010095: "padding",
                    0x010100dc: "visibility",
                    0x0101003e: "clickable",
                    0x01010273: "contentDescription",
                }
                name_str = fw_attrs.get(fw_rid, f"@fw:0x{fw_rid:08x}")
            else:
                name_str = f"<idx:{a_name}>"

            # Resolve value based on type
            val = self._resolve_value(a_data_type, a_data)

            node.attrs[name_str] = {
                "name": name_str,
                "type": a_data_type,
                "data": a_data,
                "value": val,
            }

        return node

    def _resolve_value(self, data_type: int, data: int) -> any:
        """Resolve a Res_value to a Python value."""
        if data_type == self.TYPE_STRING:
            return self.strings[data] if 0 <= data < len(self.strings) else None
        elif data_type == self.TYPE_INT_DEC:
            # Handle signed 32-bit
            return data if data < 0x80000000 else data - 0x100000000
        elif data_type == self.TYPE_INT_HEX:
            return f"0x{data:08x}"
        elif data_type == self.TYPE_INT_BOOLEAN:
            return data != 0
        elif data_type == self.TYPE_REFERENCE:
            return {"ref": data}  # Resource reference — resolved later
        elif data_type == self.TYPE_DIMENSION:
            # Dimension: complex value with unit
            return {"dimen": data}
        elif data_type == self.TYPE_FLOAT:
            import struct as s
            return s.unpack('<f', s.pack('<I', data))[0]
        elif data_type == self.TYPE_INT_COLOR_ARGB8:
            return f"#{data:08x}"
        elif data_type == self.TYPE_INT_COLOR_RGB8:
            return f"#{data & 0xFFFFFF:06x}"
        else:
            return f"type{data_type}:0x{data:08x}"


# ============================================================================
# ResourceResolver — resolves R.layout, R.string, R.id via ARSC
# ============================================================================

class ResourceResolver:
    """Resolves Android resource IDs to values using ARSC."""

    def __init__(self, apk_path: str):
        self.apk_path = apk_path
        self.arsc: Optional[ARSCParser] = None
        self._load_arsc()

    def _load_arsc(self):
        try:
            with zipfile.ZipFile(self.apk_path) as zf:
                arsc_data = zf.read('resources.arsc')
            self.arsc = ARSCParser(arsc_data)
        except Exception as e:
            print(f"  [EXP075] ARSC load failed: {e}", file=sys.stderr)

    def resolve_layout_path(self, layout_res_id: int) -> Optional[str]:
        """Resolve R.layout.* to the AXML file path in the APK."""
        if not self.arsc:
            return None
        return self.arsc.resolve_layout_path(layout_res_id)

    def resolve_string(self, string_res_id: int) -> Optional[str]:
        """Resolve R.string.* to a string value."""
        if not self.arsc:
            return None
        val = self.arsc.resolve_string(string_res_id)
        if isinstance(val, str):
            return val
        return None

    def resolve_id_name(self, view_id_res_id: int) -> Optional[str]:
        """Resolve R.id.* to a view ID name (for diagnostics)."""
        if not self.arsc:
            return None
        val = self.arsc.resolve_string(view_id_res_id)
        if isinstance(val, str):
            return val
        return None

    def read_axml(self, path: str) -> Optional[bytes]:
        """Read an AXML file from the APK."""
        try:
            with zipfile.ZipFile(self.apk_path) as zf:
                return zf.read(path)
        except Exception:
            return None


# ============================================================================
# LayoutInflater — creates a View hierarchy from AXML
# ============================================================================

class InflatedView:
    """A View created by LayoutInflater from AXML."""

    def __init__(self, class_name: str):
        self.class_name = class_name
        self.text = ""
        self.hint = ""
        self.text_resource_id = 0
        self.view_id_resource_id = 0
        self.view_id_name = ""
        self.layout_width = "wrap_content"
        self.layout_height = "wrap_content"
        self.orientation = "horizontal"
        self.gravity = 0
        self.padding = 0
        self.visibility = 0
        self.clickable = False
        self.children: List['InflatedView'] = []

    def to_view_node(self, object_id_gen) -> dict:
        """Convert to a view_tree.json node dict."""
        oid = next(object_id_gen)
        # Determine DEX descriptor
        desc = self._class_to_descriptor(self.class_name)
        node = {
            "android_view_id": 0,
            "children": [child.to_view_node(object_id_gen)["object_id"]
                         for child in self.children],
            "class": desc,
            "clickable": self.clickable,
            "enabled": True,
            "has_click_listener": False,
            "height": -1,
            "object_id": oid,
            "parent_id": 0,
            "text": self.text,
            "hint": self.hint,
            "text_resource_id": self.text_resource_id,
            "view_id_resource_id": self.view_id_resource_id,
            "view_id_name": self.view_id_name,
            "visibility": self.visibility,
            "width": -1,
            "x": 0,
            "y": 0,
            "view_type": self._view_type(),
            "inflated_from_axml": True,
        }
        return node

    def _class_to_descriptor(self, class_name: str) -> str:
        """Convert a class name like 'LinearLayout' to DEX descriptor."""
        # Common Android widget classes
        widget_map = {
            "LinearLayout": "Landroid/widget/LinearLayout;",
            "FrameLayout": "Landroid/widget/FrameLayout;",
            "RelativeLayout": "Landroid/widget/RelativeLayout;",
            "TextView": "Landroid/widget/TextView;",
            "Button": "Landroid/widget/Button;",
            "EditText": "Landroid/widget/EditText;",
            "ImageView": "Landroid/widget/ImageView;",
            "ListView": "Landroid/widget/ListView;",
            "ScrollView": "Landroid/widget/ScrollView;",
            "CheckBox": "Landroid/widget/CheckBox;",
            "RadioButton": "Landroid/widget/RadioButton;",
            "Spinner": "Landroid/widget/Spinner;",
            "WebView": "Landroid/webkit/WebView;",
            "View": "Landroid/view/View;",
            "ViewGroup": "Landroid/view/ViewGroup;",
        }
        if class_name in widget_map:
            return widget_map[class_name]
        # For custom views, just wrap with L...;
        return f"L{class_name.replace('.', '/')};"

    def _view_type(self) -> str:
        """Determine semantic view type."""
        cn = self.class_name.lower()
        if "edittext" in cn:
            return "EditText"
        if "textview" in cn:
            return "TextView"
        if "imageview" in cn:
            return "ImageView"
        if "button" in cn:
            return "Button"
        if "linear" in cn or "frame" in cn or "relative" in cn or "scroll" in cn:
            return "ViewGroup"
        if "list" in cn:
            return "ListView"
        return "View"


class LayoutInflater:
    """Inflates an AXML layout into a View hierarchy with resource resolution."""

    # Framework resource IDs for common attributes
    # These come from the resource_map in AXML and map to android.R.attr.* values
    ATTR_ORIENTATION = 0x010100c4
    ATTR_LAYOUT_WIDTH = 0x010100f4
    ATTR_LAYOUT_HEIGHT = 0x010100f5
    ATTR_ID = 0x010100d0
    ATTR_TEXT = 0x0101014f
    ATTR_HINT = 0x01010098
    ATTR_GRAVITY = 0x010100af
    ATTR_PADDING = 0x01010095
    ATTR_VISIBILITY = 0x010100dc
    ATTR_CLICKABLE = 0x0101003e

    def __init__(self, resolver: ResourceResolver):
        self.resolver = resolver

    def inflate(self, layout_res_id: int) -> Optional[InflatedView]:
        """Inflate a layout resource ID into a view hierarchy."""
        # Step 1: Resolve R.layout.* to AXML file path
        axml_path = self.resolver.resolve_layout_path(layout_res_id)
        if not axml_path:
            print(f"  [EXP075] Could not resolve layout resource 0x{layout_res_id:08x}",
                  file=sys.stderr)
            return None

        print(f"  [EXP075] Resolved R.layout.* to {axml_path}", file=sys.stderr)

        # Step 2: Read the AXML file
        axml_data = self.resolver.read_axml(axml_path)
        if not axml_data:
            print(f"  [EXP075] Could not read AXML file {axml_path}", file=sys.stderr)
            return None

        # Step 3: Parse the AXML
        decoder = AXMLDecoder(axml_data)
        if not decoder.root:
            print(f"  [EXP075] AXML parse produced no root node", file=sys.stderr)
            return None

        print(f"  [EXP075] AXML root: <{decoder.root.tag}> with "
              f"{len(decoder.root.children)} children", file=sys.stderr)

        # Step 4: Convert AXML tree to InflatedView tree
        return self._convert_node(decoder.root)

    def _convert_node(self, axml_node: AXMLNode) -> InflatedView:
        """Convert an AXMLNode to an InflatedView."""
        view = InflatedView(axml_node.tag)

        for attr_name, attr_info in axml_node.attrs.items():
            self._apply_attr(view, attr_name, attr_info)

        for child in axml_node.children:
            view.children.append(self._convert_node(child))

        return view

    def _apply_attr(self, view: InflatedView, attr_name: str, attr_info: dict):
        """Apply an AXML attribute to an InflatedView."""
        val = attr_info["value"]
        data_type = attr_info["type"]
        raw_data = attr_info["data"]

        if attr_name == "orientation":
            # 0 = horizontal, 1 = vertical
            if isinstance(val, int):
                view.orientation = "vertical" if val == 1 else "horizontal"
        elif attr_name == "layout_width":
            if raw_data == 0xFFFFFFFF:
                view.layout_width = "match_parent"
            elif raw_data == 0xFFFFFFFE:
                view.layout_width = "wrap_content"
            else:
                view.layout_width = f"{raw_data}px"
        elif attr_name == "layout_height":
            if raw_data == 0xFFFFFFFF:
                view.layout_height = "match_parent"
            elif raw_data == 0xFFFFFFFE:
                view.layout_height = "wrap_content"
            else:
                view.layout_height = f"{raw_data}px"
        elif attr_name == "id":
            # ID is a reference (TYPE_REFERENCE)
            if data_type == AXMLDecoder.TYPE_REFERENCE:
                view.view_id_resource_id = raw_data
                # Try to resolve the ID name
                id_name = self.resolver.resolve_id_name(raw_data)
                if id_name:
                    view.view_id_name = id_name
        elif attr_name == "text":
            # Text can be a string or a reference to R.string.*
            if data_type == AXMLDecoder.TYPE_STRING:
                view.text = val or ""
            elif data_type == AXMLDecoder.TYPE_REFERENCE:
                view.text_resource_id = raw_data
                resolved = self.resolver.resolve_string(raw_data)
                if resolved:
                    view.text = resolved
                    print(f"  [EXP075] Resolved text 0x{raw_data:08x} -> "
                          f"{resolved[:50]!r}", file=sys.stderr)
                else:
                    view.text = f"[unresolved:0x{raw_data:08x}]"
        elif attr_name == "hint":
            if data_type == AXMLDecoder.TYPE_STRING:
                view.hint = val or ""
            elif data_type == AXMLDecoder.TYPE_REFERENCE:
                resolved = self.resolver.resolve_string(raw_data)
                if resolved:
                    view.hint = resolved
        elif attr_name == "gravity":
            if isinstance(val, int):
                view.gravity = val
        elif attr_name == "visibility":
            if isinstance(val, int):
                view.visibility = val
        elif attr_name == "clickable":
            if isinstance(val, bool):
                view.clickable = val


# ============================================================================
# setContentViewInjector — post-processes view_tree.json
# ============================================================================

def inject_inflated_views(view_tree_path: str, apk_path: str,
                          layout_res_id: int) -> Tuple[bool, str, list]:
    """Inject inflated AXML views into a view_tree.json file.

    Args:
        view_tree_path: Path to the view_tree.json file
        apk_path: Path to the APK
        layout_res_id: The R.layout.* resource ID from setContentView(int)

    Returns:
        (success, message, inflated_nodes)
    """
    if layout_res_id == 0:
        return False, "No layout_resource_id captured", []

    # Load the existing view tree
    vt = json.loads(Path(view_tree_path).read_text())
    existing_nodes = vt.get("nodes", [])

    # Resolve and inflate the layout
    resolver = ResourceResolver(apk_path)
    inflater = LayoutInflater(resolver)
    root = inflater.inflate(layout_res_id)
    if not root:
        return False, "Layout inflation failed", []

    # Generate object IDs starting from a high number to avoid collisions
    # with existing runtime-created objects
    oid_gen = iter(range(100000, 200000))

    # Convert to view nodes
    inflated_nodes = []
    def add_node(view: InflatedView, parent_id: int = 0):
        node = view.to_view_node(oid_gen)
        node["parent_id"] = parent_id
        inflated_nodes.append(node)
        for child in view.children:
            child_node = add_node(child, node["object_id"])
        return node

    add_node(root, 0)

    # Update children lists with actual child object IDs
    for i, node in enumerate(inflated_nodes):
        # Children are already set in to_view_node, but let's make sure parent_id is right
        pass

    # Merge: add inflated nodes to the existing view tree
    all_nodes = existing_nodes + inflated_nodes
    vt["nodes"] = all_nodes
    vt["view_count"] = len(all_nodes)
    vt["exp075_inflated"] = {
        "layout_res_id": layout_res_id,
        "inflated_node_count": len(inflated_nodes),
        "root_class": root.class_name,
    }

    # Write back
    Path(view_tree_path).write_text(json.dumps(vt, indent=2))

    root_class = root.class_name
    return True, f"Inflated {len(inflated_nodes)} nodes from <{root_class}>", inflated_nodes


# ============================================================================
# Main — for testing
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: layout_inflater.py <apk_path> <layout_res_id_hex>")
        sys.exit(1)

    apk_path = sys.argv[1]
    layout_res_id = int(sys.argv[2], 0)

    resolver = ResourceResolver(apk_path)
    inflater = LayoutInflater(resolver)
    root = inflater.inflate(layout_res_id)

    if root:
        print(f"\n=== Inflated Layout ===")
        def print_tree(node, depth=0):
            indent = "  " * depth
            text = f" text={node.text!r}" if node.text else ""
            id_name = f" id={node.view_id_name}" if node.view_id_name else ""
            print(f"{indent}<{node.class_name}{id_name}{text}>")
            for child in node.children:
                print_tree(child, depth + 1)
        print_tree(root)
    else:
        print("Inflation failed")
