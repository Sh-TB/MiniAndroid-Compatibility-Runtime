// dalvik_value_glue.cpp — ISSUE-612 WAVE-3 PILOT extraction TU.
//
// Wave-3 pilot for the dalvik_engine.cpp (94,194-line) modularization:
// the DalvikValue serialization family (to_string / to_json) moved OUT of
// the monolith behind the DALVIK_MODULAR switch.
//
// Mode contract (paired with the #ifndef guards in dalvik_engine.cpp):
//   DALVIK_MODULAR=0 (default, monolithic fallback):
//       dalvik_engine.cpp defines both methods; THIS TU compiles EMPTY —
//       exactly one definition exists, no ODR violation.
//   DALVIK_MODULAR=1 (modular):
//       dalvik_engine.cpp's copies are compiled out; THIS TU provides the
//       only definitions. Semantics preserved verbatim (no edits).
//
// Dependency map (recorded before extraction, per the wave plan):
//   * fields type/int_val/long_val/float_val/double_val/bool_val/string_val/
//     class_desc/object_id/ref_id — declared in DalvikValue (dex/dalvik_engine.h)
//   * DalvikType enum — dex/dalvik_engine.h
//   * nlohmann::json — third_party/nlohmann_json
//   * NO anonymous-namespace helpers, NO static/global state, NO callers
//     inside dalvik_engine.cpp besides the public call sites that use the
//     header-declared API.
//
// Compile-cost note: this pilot's purpose is the SAFE EXTRACTION MECHANISM
// (guards, switch, equivalence protocol), not compile-time movement — the
// family is 41 lines. Family-scale extraction of the ~73K-line law-families
// requires the dalvik_detail internal-interface step and lands as separate
// commits, each with this same equivalence protocol.

#ifdef MINIANDROID_DALVIK_MODULAR

#include "dex/dalvik_engine.h"

// The monolith defines these inside namespace miniandroid::dalvik (matching
// the class declared in dalvik_engine.h) — the glue TU must define them in
// the SAME namespace to be the same entity (one definition, no new symbols).
namespace miniandroid {
namespace dalvik {

std::string DalvikValue::to_string() const {
    switch (type) {
        case DalvikType::INT32: return std::to_string(int_val);
        case DalvikType::INT64: return std::to_string(long_val) + "L";
        case DalvikType::FLOAT32: return std::to_string(float_val) + "f";
        case DalvikType::FLOAT64: return std::to_string(double_val) + "d";
        case DalvikType::BOOLEAN: return bool_val ? "true" : "false";
        case DalvikType::STRING_REF: return "\"" + string_val + "\"";
        case DalvikType::OBJECT_REF: return class_desc + "#" + std::to_string(object_id);
        case DalvikType::CLASS_REF: return "[class] " + class_desc;
        case DalvikType::NULL_REF: return "null";
        case DalvikType::VOID_: return "void";
        case DalvikType::UNINITIALIZED:
        case DalvikType::REGISTER_UNSET: return "<uninit>";
        default: return "<???>";
    }
}

json DalvikValue::to_json() const {
    json j;
    j["type"] = [this]() -> std::string {
        switch (type) {
            case DalvikType::INT32: return "int32";
            case DalvikType::INT64: return "int64";
            case DalvikType::FLOAT32: return "float";
            case DalvikType::FLOAT64: return "double";
            case DalvikType::STRING_REF: return "string";
            case DalvikType::OBJECT_REF: return "object";
            case DalvikType::CLASS_REF: return "class";
            case DalvikType::NULL_REF: return "null";
            case DalvikType::BOOLEAN: return "boolean";
            case DalvikType::VOID_: return "void";
            default: return "uninit";
        }
    }();

    switch (type) {
        case DalvikType::INT32: j["value"] = int_val; break;
        case DalvikType::INT64: j["value"] = long_val; break;
        case DalvikType::FLOAT32: j["value"] = float_val; break;
        case DalvikType::FLOAT64: j["value"] = double_val; break;
        case DalvikType::BOOLEAN: j["value"] = bool_val; break;
        case DalvikType::STRING_REF:
            j["value"] = string_val;
            j["ref_id"] = ref_id;
            break;
        case DalvikType::OBJECT_REF:
            j["class"] = class_desc;
            j["object_id"] = object_id;
            break;
        case DalvikType::CLASS_REF:
            j["descriptor"] = class_desc;
            j["ref_id"] = ref_id;
            break;
        case DalvikType::NULL_REF: j["is_null"] = true; break;
        default: j["value"] = nullptr; break;
    }
    return j;
}

}  // namespace dalvik
}  // namespace miniandroid

#endif  // MINIANDROID_DALVIK_MODULAR
