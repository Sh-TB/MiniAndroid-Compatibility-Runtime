/*
 * UNIFIED_007 — AXML parser implementation.
 * Layout verified empirically against real APKs (gmdice/bgclock/dooz):
 *   START_ELEMENT: {type,headerSize=16,size, line, comment, ns, name,
 *                   attrStart=20, attrSize=20, attrCount, idIdx, classIdx, styleIdx}
 *   attributes at chunk + 16 + attrStart + i*attrSize
 *     attr = {ns 4, name 4, rawValue 4, typedValue{size 2,res0 1,type 1,data 4}}
 *   resource map: attr resid indexed by attribute NAME string index.
 */
#include "axml_parser.h"
#include <functional>

namespace miniandroid {
namespace resources {

static inline uint16_t ax_rd16(const uint8_t* p) { return (uint16_t)(p[0] | (p[1] << 8)); }
static inline uint32_t ax_rd32(const uint8_t* p) {
    return (uint32_t)p[0] | ((uint32_t)p[1] << 8) | ((uint32_t)p[2] << 16) | ((uint32_t)p[3] << 24);
}

static constexpr uint16_t RES_XML_TYPE            = 0x0003;
static constexpr uint16_t RES_STRING_POOL_TYPE_   = 0x0001;
static constexpr uint16_t RES_XML_RESOURCE_MAP_   = 0x0180;
static constexpr uint16_t RES_XML_START_NS        = 0x0100;
static constexpr uint16_t RES_XML_END_NS          = 0x0101;
static constexpr uint16_t RES_XML_START_ELEM      = 0x0102;
static constexpr uint16_t RES_XML_END_ELEM        = 0x0103;
static constexpr uint16_t RES_XML_CDATA           = 0x0104;

std::string AxmlParser::ns_short(const std::string& uri) {
    if (uri == "http://schemas.android.com/apk/res/android") return "android";
    if (uri == "http://schemas.android.com/apk/res-auto") return "app";
    if (uri.empty()) return "";
    const std::string pfx = "http://schemas.android.com/apk/res/";
    if (uri.compare(0, pfx.size(), pfx) == 0) return "app";
    return uri;
}

bool AxmlParser::parse_string_pool(const uint8_t* p, size_t avail, size_t& consumed) {
    consumed = 0;
    if (avail < 28) { last_error_ = "pool truncated"; return false; }
    uint16_t type = ax_rd16(p);
    uint16_t header_size = ax_rd16(p + 2);
    uint32_t size = ax_rd32(p + 4);
    if (type != RES_STRING_POOL_TYPE_) { last_error_ = "not string pool"; return false; }
    if (size > avail) { last_error_ = "pool overruns"; return false; }
    uint32_t count = ax_rd32(p + 8);
    uint32_t flags = ax_rd32(p + 16);
    uint32_t strings_start = ax_rd32(p + 20);
    bool utf8 = (flags & RES_STRING_POOL_UTF8_FLAG) != 0;
    strings_.clear();
    strings_.resize(count);
    const uint32_t* offs = (const uint32_t*)(p + header_size);
    const uint8_t* sdata = p + strings_start;
    for (uint32_t i = 0; i < count; i++) {
        uint32_t off = offs[i];
        if (strings_start + off >= size) continue;
        const uint8_t* s = sdata + off;
        size_t remain = size - strings_start - off;
        if (utf8) {
            size_t o = 0;
            while (o < remain && (s[o] & 0x80)) o++;
            o++;                              // last u16len byte
            size_t u8len = 0;
            if (o < remain) {
                if (s[o] & 0x80) { u8len = ((s[o] & 0x7F) << 8) | s[o + 1]; o += 2; }
                else { u8len = s[o]; o++; }
            }
            size_t cap = std::min(u8len, remain - o);
            strings_[i].assign((const char*)(s + o), cap);
        } else {
            uint16_t c0 = ax_rd16(s);
            uint32_t u16len; size_t o;
            if (c0 & 0x8000) { u16len = ((c0 & 0x7FFF) << 16) | ax_rd16(s + 2); o = 4; }
            else { u16len = c0; o = 2; }
            size_t bytes = std::min<size_t>(u16len * 2, (remain - o) & ~1u);
            std::string raw((const char*)(s + o), bytes);
            std::string utf8out; utf8out.reserve(bytes / 2);
            for (size_t ci = 0; ci + 1 < raw.size(); ci += 2) {
                uint32_t ch = (uint8_t)raw[ci] | ((uint32_t)(uint8_t)raw[ci + 1] << 8);
                if (ch >= 0xD800 && ch <= 0xDBFF && ci + 3 < raw.size()) {
                    uint32_t lo = (uint8_t)raw[ci + 2] | ((uint32_t)(uint8_t)raw[ci + 3] << 8);
                    if (lo >= 0xDC00 && lo <= 0xDFFF) {
                        ch = 0x10000 + ((ch - 0xD800) << 10) + (lo - 0xDC00);
                        ci += 2;
                    }
                }
                if (ch < 0x80) utf8out += (char)ch;
                else if (ch < 0x800) {
                    utf8out += (char)(0xC0 | (ch >> 6));
                    utf8out += (char)(0x80 | (ch & 0x3F));
                } else if (ch < 0x10000) {
                    utf8out += (char)(0xE0 | (ch >> 12));
                    utf8out += (char)(0x80 | ((ch >> 6) & 0x3F));
                    utf8out += (char)(0x80 | (ch & 0x3F));
                } else {
                    utf8out += (char)(0xF0 | (ch >> 18));
                    utf8out += (char)(0x80 | ((ch >> 12) & 0x3F));
                    utf8out += (char)(0x80 | ((ch >> 6) & 0x3F));
                    utf8out += (char)(0x80 | (ch & 0x3F));
                }
            }
            strings_[i] = std::move(utf8out);
        }
    }
    consumed = size;
    return true;
}

bool AxmlParser::parse(const std::vector<uint8_t>& data) {
    valid_ = false;
    strings_.clear();
    resource_map_.clear();
    root_ = AxmlElement{};

    if (data.size() < 8) { last_error_ = "too small"; return false; }
    const uint8_t* p = data.data();
    size_t avail = data.size();
    uint16_t type = ax_rd16(p);
    uint16_t header_size = ax_rd16(p + 2);
    uint32_t total = ax_rd32(p + 4);
    if (type != RES_XML_TYPE) { last_error_ = "not RES_XML_TYPE"; return false; }
    if (total > avail) { last_error_ = "size overrun"; return false; }

    size_t pos = header_size;
    {
        size_t consumed = 0;
        if (!parse_string_pool(p + pos, avail - pos, consumed)) return false;
        pos += consumed;
    }

    // Flat node assembly (no pointer invalidation).
    struct FlatNode {
        size_t parent;       // index into flat list; SIZE_MAX = root
        AxmlElement el;
    };
    std::vector<FlatNode> flat;
    std::vector<size_t> stack;

    while (pos + 8 <= total) {
        uint16_t ctype = ax_rd16(p + pos);
        uint32_t csize = ax_rd32(p + pos + 4);
        if (csize < 8 || pos + csize > total) break;
        if (ctype == RES_XML_RESOURCE_MAP_) {
            uint32_t n = (csize - 8) / 4;
            for (uint32_t i = 0; i < n; i++)
                resource_map_.push_back(ax_rd32(p + pos + 8 + i * 4));
        } else if (ctype == RES_XML_START_NS) {
            uint32_t prefix_idx = ax_rd32(p + pos + 16);
            std::string prefix = prefix_idx < strings_.size() ? strings_[prefix_idx] : "";
            if (prefix == "android") {
                uint32_t uri_idx = ax_rd32(p + pos + 20);
                if (uri_idx < strings_.size()) android_ns_ = strings_[uri_idx];
            }
        } else if (ctype == RES_XML_START_ELEM) {
            uint32_t name_idx = ax_rd32(p + pos + 20);
            uint16_t attr_start = ax_rd16(p + pos + 24);
            uint16_t attr_size = ax_rd16(p + pos + 26);
            uint16_t attr_count = ax_rd16(p + pos + 28);

            FlatNode fn;
            fn.parent = stack.empty() ? SIZE_MAX : stack.back();
            if (name_idx < strings_.size()) fn.el.name = strings_[name_idx];
            for (uint16_t a = 0; a < attr_count; a++) {
                size_t ap = pos + 16 + attr_start + (size_t)a * attr_size;
                if (ap + 20 > avail) break;
                AxmlAttribute attr;
                uint32_t ans = ax_rd32(p + ap);
                uint32_t aname = ax_rd32(p + ap + 4);
                uint32_t araw = ax_rd32(p + ap + 8);
                uint8_t dtype = p[ap + 15];
                uint32_t ddata = ax_rd32(p + ap + 16);
                attr.ns = (ans != 0xFFFFFFFF && ans < strings_.size()) ? ns_short(strings_[ans]) : "";
                attr.name = aname < strings_.size() ? strings_[aname] : "";
                attr.raw_value = (araw != 0xFFFFFFFF && araw < strings_.size()) ? strings_[araw] : "";
                attr.value.type = (DataType)dtype;
                attr.value.data = ddata;
                if (attr.value.is_reference() || attr.value.is_string())
                    attr.value.ref_id = ddata;   // for typed refs: target resource id
                if (attr.value.is_string() && ddata < strings_.size())
                    attr.value.string_value = strings_[ddata];
                if (attr.value.is_dimension()) {
                    attr.value.dim_value = complex_to_float(ddata);
                    attr.value.dim_unit = (uint8_t)(ddata & 0xF);  // COMPLEX_UNIT_SHIFT = 0
                }
                if (attr.name.compare(0, 8, "android:") == 0) {
                    attr.name = attr.name.substr(8);
                    attr.ns = "android";
                }
                // attribute resource id via resource map (name index)
                if (aname < resource_map_.size()) attr.attr_resid = resource_map_[aname];
                fn.el.attributes.push_back(std::move(attr));
            }
            flat.push_back(std::move(fn));
            stack.push_back(flat.size() - 1);
        } else if (ctype == RES_XML_END_ELEM) {
            if (!stack.empty()) stack.pop_back();
        } else if (ctype == RES_XML_CDATA) {
            uint32_t data_idx = ax_rd32(p + pos + 16);
            std::string text = data_idx < strings_.size() ? strings_[data_idx] : "";
            if (!stack.empty()) flat[stack.back()].el.cdata += text;
        }
        pos += csize;
    }

    // Assemble tree via index tree (children index lists) — no pointer reuse.
    std::vector<std::vector<size_t>> kids(flat.size());
    size_t root_idx = SIZE_MAX;
    for (size_t i = 0; i < flat.size(); i++) {
        if (flat[i].parent == SIZE_MAX) { root_idx = i; continue; }
        kids[flat[i].parent].push_back(i);
    }
    std::function<void(AxmlElement&, size_t)> attach = [&](AxmlElement& parent_el, size_t idx) {
        // Pre-reserve to keep references stable during recursion
        parent_el.children.reserve(kids[idx].size());
        for (size_t c : kids[idx]) {
            parent_el.children.push_back(std::move(flat[c].el));
            attach(parent_el.children.back(), c);
        }
    };
    if (root_idx != SIZE_MAX) {
        root_.name = std::move(flat[root_idx].el.name);
        root_.cdata = std::move(flat[root_idx].el.cdata);
        root_.attributes = std::move(flat[root_idx].el.attributes);
        attach(root_, root_idx);
    }

    if (root_.name.empty()) { last_error_ = "no root element"; return false; }
    valid_ = true;
    return true;
}

std::string AxmlParser::to_json() const {
    std::function<void(const AxmlElement&, std::ostringstream&)> dump =
        [&](const AxmlElement& el, std::ostringstream& o) {
            o << "{\"name\":\"" << el.name << "\",\"attrs\":[";
            bool first = true;
            for (const auto& a : el.attributes) {
                if (!first) o << ",";
                first = false;
                o << "{\"ns\":\"" << a.ns << "\",\"name\":\"" << a.name << "\",\"raw\":\""
                  << a.raw_value << "\",\"dtype\":" << (int)a.value.type
                  << ",\"resid\":0x" << std::hex << a.attr_resid << std::dec;
                if (a.value.is_string()) o << ",\"value\":\"" << a.value.string_value << "\"";
                else o << ",\"data\":" << a.value.data;
                o << "}";
            }
            o << "],\"children\":[";
            first = true;
            for (const auto& c : el.children) {
                if (!first) o << ",";
                first = false;
                dump(c, o);
            }
            o << "]}";
        };
    std::ostringstream o;
    dump(root_, o);
    return o.str();
}

} // namespace resources
} // namespace miniandroid
