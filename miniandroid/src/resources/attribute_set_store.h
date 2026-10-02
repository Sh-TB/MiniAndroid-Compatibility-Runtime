// attribute_set_store.h — F-NEW-197 XML-AttributeSet law.
//
// AOSP law (frameworks/base AttributeResolution.cpp / TypedArray.obtain):
// Context.obtainStyledAttributes(AttributeSet, int[] styleable, ...) resolves
// each styleable slot in a FIXED precedence: (1) the XML AttributeSet value
// carried by the view-constructor argument, (2) the style, (3) the theme
// chain, (4) absent → the caller's TypedArray default. The MiniAndroid view
// constructors receive their AttributeSet as a marker heap object
// (run_custom_view_constructor); the XML attribute data parsed by the
// inflater travels to the TypedArray producer through THIS store, keyed by
// the marker object id (one marker per constructor call — never shared
// across views).
//
// Generic Android semantics only: no package names, no class names — the
// store carries raw (attr_resid → typed value) pairs exactly as AAPT2
// compiled them into the binary XML (attr_resid comes from the AXML
// resource map, valid for android:* AND app/custom 0x7f attrs).
#pragma once

#include <cstdint>
#include <string>
#include <unordered_map>
#include <vector>

#include "arsc_parser.h"   // DataType

namespace miniandroid {
namespace resources {

struct XmlAttrRecord {
    uint32_t    resid = 0;   // full attr resource id (from AXML resource map)
    DataType    type = DataType::NULL_;
    int32_t     data = 0;    // raw data word (int/enum/color/boolean/dim raw)
    uint32_t    ref_id = 0;  // reference target id when REFERENCE
    std::string str;         // string value when STRING
};

// Typed-value families a TypedArray getInt/getBoolean/getResourceId slot can
// carry from XML (everything except STRING — a string slot is left to the
// theme path and logged, never force-decoded into an int).
inline bool xml_attr_is_int_family(DataType t) {
    switch (t) {
        case DataType::INT_DEC: case DataType::INT_HEX:
        case DataType::INT_BOOLEAN: case DataType::FLOAT:
        case DataType::DIMENSION: case DataType::FRACTION:
        case DataType::COLOR_ARGB8: case DataType::COLOR_RGB8:
        case DataType::COLOR_ARGB4: case DataType::COLOR_RGB4:
        case DataType::REFERENCE: case DataType::DYNAMIC_REFERENCE:
            return true;
        default:
            return false;
    }
}

class AttributeSetStore {
  public:
    static AttributeSetStore& instance() {
        static AttributeSetStore store;
        return store;
    }
    // One AttributeSet marker object per view-constructor call: install
    // replaces any prior record set for that id (fresh ids each ctor).
    void install(uint32_t attrs_id, std::vector<XmlAttrRecord> recs) {
        if (attrs_id == 0) return;
        map_[attrs_id] = std::move(recs);
    }
    const std::vector<XmlAttrRecord>* lookup(uint32_t attrs_id) const {
        auto it = map_.find(attrs_id);
        return it == map_.end() ? nullptr : &it->second;
    }
    // The AttributeSet for the FIRST XML attribute matching a styleable attr
    // id (AOSP: the XML set is scanned per attr id; last match wins as in
    // AOSP's TypedArray loop — files rarely repeat one attr id).
    const XmlAttrRecord* find(const std::vector<XmlAttrRecord>* recs,
                              uint32_t attr_id) const {
        if (!recs) return nullptr;
        const XmlAttrRecord* hit = nullptr;
        for (const auto& r : *recs) {
            if (r.resid == attr_id) hit = &r;   // last wins (AOSP scan order)
        }
        return hit;
    }

  private:
    AttributeSetStore() = default;
    std::unordered_map<uint32_t, std::vector<XmlAttrRecord>> map_;
};

}  // namespace resources
}  // namespace miniandroid
