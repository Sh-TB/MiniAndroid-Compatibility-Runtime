/*
 * UNIFIED_007 — AXML (compiled binary XML) parser.
 *
 * Parses Android compiled XML resources directly from the APK
 * (res/layout XML, res/menu XML, AndroidManifest). This is the REAL
 * binary format: RES_XML_TYPE (0x0003) → string pool → resource map →
 * start/end element nodes with typed attribute values.
 *
 * No external tool, no JSON sidecar: bytes in → element tree out.
 */

#ifndef MINIANDROID_AXML_PARSER_H
#define MINIANDROID_AXML_PARSER_H

#include <cstdint>
#include <string>
#include <vector>
#include <map>
#include <optional>
#include <sstream>

#include "arsc_parser.h"  // DataType, ResValue reuse

namespace miniandroid {
namespace resources {

struct AxmlAttribute {
    std::string ns;          // "android" | "app" | "" (raw ns URI not needed)
    std::string name;        // e.g. "layout_width", "text", "id", "onClick"
    std::string raw_value;   // raw string if present
    ResValue value;          // typed value (string/int/bool/ref/dim/color)
    uint32_t attr_resid = 0; // android:* attribute resource id from resource map
};

struct AxmlElement {
    std::string name;                       // e.g. "LinearLayout", "TextView"
    std::vector<AxmlAttribute> attributes;  // in file order
    std::vector<AxmlElement> children;
    std::string cdata;                      // text content (rare in layouts)

    const AxmlAttribute* attr(const std::string& n, const std::string& ns = "android") const {
        for (const auto& a : attributes)
            if (a.name == n && (ns.empty() || a.ns == ns)) return &a;
        return nullptr;
    }
};

class AxmlParser {
public:
    bool parse(const std::vector<uint8_t>& data);
    bool valid() const { return valid_; }
    const std::string& last_error() const { return last_error_; }

    // Root element of the document
    const AxmlElement& root() const { return root_; }
    // "android" namespace URI detected from start-namespace chunks
    const std::string& android_ns() const { return android_ns_; }

    // Debug/JSON dump
    std::string to_json() const;

private:
    bool parse_string_pool(const uint8_t* p, size_t avail, size_t& consumed);
    void parse_node(const uint8_t* p, size_t avail, size_t pos, size_t end);
    static std::string ns_short(const std::string& uri);

    bool valid_ = false;
    std::string last_error_;
    std::vector<std::string> strings_;
    std::vector<uint32_t> resource_map_;  // attr index → android attr resid
    std::string android_ns_;
    AxmlElement root_;
    size_t depth_ = 0;
    std::vector<AxmlElement*> stack_;     // build stack
};

} // namespace resources
} // namespace miniandroid

#endif // MINIANDROID_AXML_PARSER_H
