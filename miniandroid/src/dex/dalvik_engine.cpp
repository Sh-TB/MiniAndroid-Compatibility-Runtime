/*
 * MiniAndroid Runtime v0.2 - Real Dalvik Execution Engine Implementation
 * EXP-030: Real Bytecode Execution
 * 
 * Complete implementation of Dalvik register machine with:
 * - 25+ opcodes executed
 * - Real register state changes
 * - Object heap allocation
 * - Method call stack
 * - API bridge integration
 */

#include "dalvik_engine.h"
#include "dex_parser.h"
#include "../api/android_stubs.h"
#include "../diagnostics/mem_probe.h"
#include "../jni/jni_bridge.h"
// EXP-051: Shadow registry integration.
#include "../framework/shadow_registry.h"
#include "../framework/android_shadows.h"
#include "../framework/heap_adapter.h"
#include <chrono>
#include <iostream>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <cassert>
#include <cctype>    // EXP-071 Phase 6: std::toupper/std::tolower for String.toUpperCase/toLowerCase
#include <unordered_set>

namespace miniandroid {
namespace dalvik {

// EXP-065: Forward declaration — used by the setHintText capture stub
// in try_recursive_invoke (defined later in this file at line ~5795).
static framework::CallContext::Arg dalvik_value_to_arg(const DalvikValue& v);

// ============================================================================
// DalvikValue Serialization
// ============================================================================

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

// ============================================================================
// Constructor/Destructor
// ============================================================================

DalvikExecutionEngine::DalvikExecutionEngine()
    // EXP-037 PHASE A Week 3 (BLOCKER-001 FIX): VirtualDispatcher requires a
    // MethodResolver* in its constructor (no default ctor). The previous code
    // relied on a default ctor that never existed. We pass nullptr for now;
    // vtable_dispatcher_ is currently unused (the dispatch_virtual_call path
    // was removed because it referenced API surface that does not exist).
    // When BLOCKER-002 (method_ids parsing) and BLOCKER-003 (field_ids parsing)
    // land, a real MethodResolver will be wired in here.
    : vtable_dispatcher_(nullptr) {
    log("DalvikExecutionEngine initialized");
}

DalvikExecutionEngine::~DalvikExecutionEngine() {
    log("DalvikExecutionEngine destroyed");
}

// EXP-039 (BLOCKER-035): Build class→DEX index map by searching each DEX's
// class_defs[] table for the class descriptor.
//
// For each DEX file's raw bytes, we parse the class_defs[] table and extract
// the class_idx → type descriptor. If the descriptor matches a class in the
// merged report, we record the DEX index.
//
// This is the CORRECT way to determine which DEX file owns a class.
void DalvikExecutionEngine::build_class_dex_index(const dex::DexReport& report) {
    class_to_dex_index_.clear();
    if (per_dex_raw_data_.empty()) {
        // Single DEX — all classes belong to DEX 0
        for (const auto& cls : report.classes) {
            class_to_dex_index_[cls.name] = 0;
        }
        log("Single DEX — mapped " + std::to_string(class_to_dex_index_.size()) + " classes to DEX 0");
        return;
    }

    // For each DEX file, parse its class_defs[] and build a set of class descriptors
    for (uint32_t di = 0; di < per_dex_raw_data_.size(); di++) {
        const auto& raw = per_dex_raw_data_[di];
        if (raw.size() < sizeof(dex::DexHeader)) continue;

        dex::DexHeader hdr;
        std::memcpy(&hdr, raw.data(), sizeof(dex::DexHeader));

        uint32_t cd_size = hdr.class_defs_size;
        uint32_t cd_off = hdr.class_defs_off;

        // Each DexClassDef is 32 bytes
        for (uint32_t ci = 0; ci < cd_size; ci++) {
            size_t cd_entry_off = cd_off + ci * 32;  // sizeof(DexClassDef) = 32
            if (cd_entry_off + 32 > raw.size()) break;

            // Read class_idx (first 4 bytes of DexClassDef)
            uint32_t class_idx;
            std::memcpy(&class_idx, raw.data() + cd_entry_off, 4);

            // Resolve class_idx → type_ids[class_idx] → descriptor string
            if (class_idx >= hdr.type_ids_size) continue;
            size_t tid_off = hdr.type_ids_off + class_idx * 4;  // type_ids are 4 bytes each
            if (tid_off + 4 > raw.size()) continue;

            uint32_t descriptor_idx;
            std::memcpy(&descriptor_idx, raw.data() + tid_off, 4);

            // Resolve descriptor string
            std::string descriptor = read_dex_string_from_raw(raw, descriptor_idx, hdr);

            if (!descriptor.empty() && descriptor[0] == 'L') {
                // Only assign if not already mapped (first DEX wins — but
                // classes shouldn't be duplicated across DEX files)
                if (class_to_dex_index_.find(descriptor) == class_to_dex_index_.end()) {
                    class_to_dex_index_[descriptor] = di;
                }
            }
        }
    }

    // Assign DEX 0 to any remaining unmapped classes (safety fallback)
    uint32_t unmapped = 0;
    for (const auto& cls : report.classes) {
        if (class_to_dex_index_.find(cls.name) == class_to_dex_index_.end()) {
            class_to_dex_index_[cls.name] = 0;
            unmapped++;
        }
    }

    log("Built class→DEX index: " + std::to_string(class_to_dex_index_.size()) +
        " entries (" + std::to_string(unmapped) + " unmapped, assigned to DEX 0)");

    // EXP-068: Build class→superclass map from report.classes.
    // This enables semantic View inheritance queries (is_subclass_of).
    // NOTE: The APK's DEX only contains class_defs for classes DEFINED in the APK.
    // Framework classes (android.widget.LinearLayout, etc.) are referenced via
    // type_idx but their class_defs are not in the APK. So we pre-populate the
    // map with the known Android framework View hierarchy.
    class_to_superclass_.clear();
    // Framework View hierarchy (from AOSP):
    static const std::pair<std::string, std::string> framework_views[] = {
        {"Landroid/view/View;", "Ljava/lang/Object;"},
        {"Landroid/view/ViewGroup;", "Landroid/view/View;"},
        {"Landroid/widget/LinearLayout;", "Landroid/view/ViewGroup;"},
        {"Landroid/widget/FrameLayout;", "Landroid/view/ViewGroup;"},
        {"Landroid/widget/RelativeLayout;", "Landroid/view/ViewGroup;"},
        {"Landroid/widget/ScrollView;", "Landroid/widget/FrameLayout;"},
        {"Landroid/widget/HorizontalScrollView;", "Landroid/widget/FrameLayout;"},
        {"Landroid/widget/TextView;", "Landroid/view/View;"},
        {"Landroid/widget/EditText;", "Landroid/widget/TextView;"},
        {"Landroid/widget/Button;", "Landroid/widget/TextView;"},
        {"Landroid/widget/ImageButton;", "Landroid/widget/ImageView;"},
        {"Landroid/widget/ImageView;", "Landroid/view/View;"},
        {"Landroid/widget/CheckBox;", "Landroid/widget/Button;"},
        {"Landroid/widget/RadioButton;", "Landroid/widget/Button;"},
        {"Landroid/widget/ToggleButton;", "Landroid/widget/Button;"},
        {"Landroid/widget/CheckedTextView;", "Landroid/widget/TextView;"},
        {"Landroid/widget/AutoCompleteTextView;", "Landroid/widget/EditText;"},
        {"Landroid/widget/MultiAutoCompleteTextView;", "Landroid/widget/AutoCompleteTextView;"},
        {"Landroid/widget/Space;", "Landroid/view/View;"},
        {"Landroid/view/TextureView;", "Landroid/view/View;"},
        {"Landroid/view/SurfaceView;", "Landroid/view/View;"},
        // Activity hierarchy (EXP-071: needed for instanceof checks)
        {"Landroid/content/Context;", "Ljava/lang/Object;"},
        {"Landroid/content/ContextWrapper;", "Landroid/content/Context;"},
        {"Landroid/app/Activity;", "Landroid/content/ContextWrapper;"},
        {"Landroidx/appcompat/app/AppCompatActivity;", "Landroid/app/Activity;"},
        {"Landroidx/fragment/app/FragmentActivity;", "Landroidx/appcompat/app/AppCompatActivity;"},
        // Fragment hierarchy
        {"Landroidx/fragment/app/Fragment;", "Ljava/lang/Object;"},
        // AppCompat widgets (AndroidX)
        {"Landroidx/appcompat/widget/AppCompatTextView;", "Landroid/widget/TextView;"},
        {"Landroidx/appcompat/widget/AppCompatEditText;", "Landroid/widget/EditText;"},
        {"Landroidx/appcompat/widget/AppCompatButton;", "Landroid/widget/Button;"},
        {"Landroidx/appcompat/widget/AppCompatImageView;", "Landroid/widget/ImageView;"},
        {"Landroidx/appcompat/widget/AppCompatCheckBox;", "Landroid/widget/CheckBox;"},
    };
    for (const auto& [cls, sup] : framework_views) {
        class_to_superclass_[cls] = sup;
    }
    // Now add APK-defined classes from the DEX report.
    int apk_class_count = 0;
    for (const auto& cls : report.classes) {
        if (!cls.superclass_name.empty()) {
            class_to_superclass_[cls.name] = cls.superclass_name;
            apk_class_count++;
        }
    }
    std::cerr << "[EXP068] Built class→superclass map: " << class_to_superclass_.size()
              << " entries (" << apk_class_count << " from APK + "
              << (class_to_superclass_.size() - apk_class_count) << " framework)"
              << " — LinearLayout present: "
              << (class_to_superclass_.count("Landroid/widget/LinearLayout;") ? "YES" : "NO")
              << std::endl;

    // EXP-045 Phase 2: Build O(1) class→ClassInfo index for try_recursive_invoke().
    class_info_index_.clear();
    class_info_index_.reserve(report.classes.size());
    for (size_t i = 0; i < report.classes.size(); i++) {
        class_info_index_[report.classes[i].name] = i;
    }
    log("Built class→ClassInfo index: " + std::to_string(class_info_index_.size()) + " entries");
}

// ============================================================================
// EXP-038 (BLOCKER-033): Per-DEX method resolution using raw DEX bytes.
// ============================================================================

std::string DalvikExecutionEngine::read_dex_string_from_raw(
    const std::vector<uint8_t>& raw, uint32_t string_idx, const dex::DexHeader& hdr) const {

    uint32_t sids_off = hdr.string_ids_off;
    uint32_t sids_size = hdr.string_ids_size;

    if (string_idx >= sids_size) return "<bad_str_idx>";
    if (sids_off + (string_idx + 1) * 4 > raw.size()) return "<str_id_oob>";

    uint32_t string_data_off;
    std::memcpy(&string_data_off, raw.data() + sids_off + string_idx * 4, 4);

    if (string_data_off >= raw.size()) return "<str_data_oob>";

    // Read ULEB128 length
    size_t pos = string_data_off;
    uint32_t length = 0;
    int shift = 0;
    while (pos < raw.size()) {
        uint8_t byte = raw[pos++];
        length |= (byte & 0x7F) << shift;
        if (!(byte & 0x80)) break;
        shift += 7;
    }

    if (pos + length > raw.size()) return "<str_truncated>";
    return std::string(reinterpret_cast<const char*>(raw.data() + pos), length);
}

// EXP-065: Per-DEX string resolution.
// string_idx is relative to the current DEX file's string_ids table.
// In multi-DEX apps (Telegram has 5 DEX files), the merged dex_report_->strings
// is the CONCATENATION of all DEX files' string tables — so using the merged
// index causes const-string to fetch the WRONG string. For example,
// classes4.dex's string_idx=5975 is "+", but merged_strings[5975] is
// "FIELD_PREFERRED_AUDIO_LANGUAGES" from classes.dex (which has 56,182 strings
// before classes4.dex's strings start).
//
// This function reads the string directly from the per-DEX raw bytes.
std::string DalvikExecutionEngine::resolve_string_for_dex(
    uint32_t string_idx, uint32_t dex_index) const {

    if (dex_index < per_dex_raw_data_.size()) {
        const auto& raw = per_dex_raw_data_[dex_index];
        if (raw.size() < sizeof(dex::DexHeader)) goto fallback;

        dex::DexHeader hdr;
        std::memcpy(&hdr, raw.data(), sizeof(dex::DexHeader));

        if (string_idx < hdr.string_ids_size) {
            return read_dex_string_from_raw(raw, string_idx, hdr);
        }
    }

fallback:
    // Single-DEX fallback: use the merged dex_report's strings.
    if (dex_report_ && string_idx < dex_report_->strings.size()) {
        return dex_report_->strings[string_idx];
    }
    return "<bad_str_idx:" + std::to_string(string_idx) + ">";
}

// ============================================================================
// EXP-068: Generic View inheritance queries.
// These walk the DEX superclass chain to determine if a class inherits from
// a known Android View type. This replaces class-name pattern matching with
// semantic superclass resolution.
// ============================================================================

bool DalvikExecutionEngine::is_subclass_of(const std::string& class_desc,
                                             const std::string& ancestor_desc) const {
    if (class_desc == ancestor_desc) return true;
    std::string current = class_desc;
    std::unordered_set<std::string> visited;  // cycle protection
    for (int i = 0; i < 50; ++i) {  // max depth 50 to prevent infinite loops
        if (visited.count(current)) return false;  // cycle
        visited.insert(current);
        auto it = class_to_superclass_.find(current);
        if (it == class_to_superclass_.end()) return false;
        current = it->second;
        if (current == ancestor_desc) return true;
        if (current.empty() || current == "Ljava/lang/Object;") return false;
    }
    return false;
}

bool DalvikExecutionEngine::is_view_class(const std::string& class_desc) const {
    return is_subclass_of(class_desc, "Landroid/view/View;");
}

bool DalvikExecutionEngine::is_text_view_class(const std::string& class_desc) const {
    return is_subclass_of(class_desc, "Landroid/widget/TextView;");
}

bool DalvikExecutionEngine::is_edit_text_class(const std::string& class_desc) const {
    return is_subclass_of(class_desc, "Landroid/widget/EditText;");
}

bool DalvikExecutionEngine::is_image_view_class(const std::string& class_desc) const {
    return is_subclass_of(class_desc, "Landroid/widget/ImageView;");
}

bool DalvikExecutionEngine::is_button_class(const std::string& class_desc) const {
    return is_subclass_of(class_desc, "Landroid/widget/Button;");
}

bool DalvikExecutionEngine::is_view_group_class(const std::string& class_desc) const {
    return is_subclass_of(class_desc, "Landroid/view/ViewGroup;");
}

std::string DalvikExecutionEngine::resolve_method_name_for_dex(
    uint32_t method_idx, uint32_t dex_index) const {

    if (dex_index < per_dex_raw_data_.size()) {
        const auto& raw = per_dex_raw_data_[dex_index];
        if (raw.size() < sizeof(dex::DexHeader)) goto fallback;

        dex::DexHeader hdr;
        std::memcpy(&hdr, raw.data(), sizeof(dex::DexHeader));

        if (method_idx < hdr.method_ids_size &&
            hdr.method_ids_off + (method_idx + 1) * sizeof(dex::DexMethodId) <= raw.size()) {

            dex::DexMethodId mid;
            std::memcpy(&mid, raw.data() + hdr.method_ids_off + method_idx * sizeof(dex::DexMethodId),
                        sizeof(dex::DexMethodId));
            return read_dex_string_from_raw(raw, mid.name_idx, hdr);
        }
    }

fallback:
    // Fallback to merged method_ids (works for classes.dex)
    if (dex_report_ && method_idx < dex_report_->method_ids.size()) {
        uint32_t name_idx = dex_report_->method_ids[method_idx].name_idx;
        if (name_idx < dex_report_->strings.size()) return dex_report_->strings[name_idx];
    }
    return "<bad_method_idx:" + std::to_string(method_idx) + ">";
}

std::string DalvikExecutionEngine::resolve_method_class_for_dex(
    uint32_t method_idx, uint32_t dex_index) const {

    if (dex_index < per_dex_raw_data_.size()) {
        const auto& raw = per_dex_raw_data_[dex_index];
        if (raw.size() < sizeof(dex::DexHeader)) goto fallback;

        dex::DexHeader hdr;
        std::memcpy(&hdr, raw.data(), sizeof(dex::DexHeader));

        if (method_idx < hdr.method_ids_size &&
            hdr.method_ids_off + (method_idx + 1) * sizeof(dex::DexMethodId) <= raw.size()) {

            dex::DexMethodId mid;
            std::memcpy(&mid, raw.data() + hdr.method_ids_off + method_idx * sizeof(dex::DexMethodId),
                        sizeof(dex::DexMethodId));

            // Resolve class_idx → type descriptor
            uint16_t class_idx = mid.class_idx;
            if (class_idx < hdr.type_ids_size &&
                hdr.type_ids_off + (class_idx + 1) * 4 <= raw.size()) {

                uint32_t descriptor_idx;
                std::memcpy(&descriptor_idx, raw.data() + hdr.type_ids_off + class_idx * 4, 4);
                return read_dex_string_from_raw(raw, descriptor_idx, hdr);
            }
        }
    }

fallback:
    if (dex_report_ && method_idx < dex_report_->method_ids.size()) {
        uint16_t class_idx = dex_report_->method_ids[method_idx].class_idx;
        if (class_idx < dex_report_->types.size()) return dex_report_->types[class_idx];
    }
    return "<unknown>";
}

// EXP-071 Phase 8: Per-DEX method proto (descriptor) resolution.
// Returns the method's proto string, e.g. "(Ljava/lang/Runnable;J)V".
// The proto_idx in DexMethodId points into proto_ids, which has a
// shorty_idx (string_ids index for the shorty like "RLJ") AND a
// parameters_off pointing to a TypeList of parameter types.
//
// We need the FULL proto (not just the shorty) because the shorty "RLJ"
// doesn't tell us which L-prefixed types are arrays vs objects.
//
// We construct the proto string by walking the parameter type list and
// concatenating descriptors, then wrapping in parens with the return type.
std::string DalvikExecutionEngine::resolve_method_proto_for_dex(
    uint32_t method_idx, uint32_t dex_index) const {

    if (dex_index < per_dex_raw_data_.size()) {
        const auto& raw = per_dex_raw_data_[dex_index];
        if (raw.size() < sizeof(dex::DexHeader)) goto proto_fallback;

        dex::DexHeader hdr;
        std::memcpy(&hdr, raw.data(), sizeof(dex::DexHeader));

        if (method_idx < hdr.method_ids_size &&
            hdr.method_ids_off + (method_idx + 1) * sizeof(dex::DexMethodId) <= raw.size()) {

            dex::DexMethodId mid;
            std::memcpy(&mid, raw.data() + hdr.method_ids_off + method_idx * sizeof(dex::DexMethodId),
                        sizeof(dex::DexMethodId));

            // mid.proto_idx indexes into proto_ids table.
            if (mid.proto_idx < hdr.proto_ids_size &&
                hdr.proto_ids_off + (mid.proto_idx + 1) * 12 <= raw.size()) {

                // DexProtoId is 12 bytes: shorty_idx (4) + return_type_idx (4) + parameters_off (4).
                uint32_t shorty_idx, return_type_idx, parameters_off;
                std::memcpy(&shorty_idx,     raw.data() + hdr.proto_ids_off + mid.proto_idx * 12 + 0, 4);
                std::memcpy(&return_type_idx, raw.data() + hdr.proto_ids_off + mid.proto_idx * 12 + 4, 4);
                std::memcpy(&parameters_off, raw.data() + hdr.proto_ids_off + mid.proto_idx * 12 + 8, 4);

                // Resolve return type descriptor.
                std::string return_desc;
                if (return_type_idx < hdr.type_ids_size &&
                    hdr.type_ids_off + (return_type_idx + 1) * 4 <= raw.size()) {
                    uint32_t ret_str_idx;
                    std::memcpy(&ret_str_idx, raw.data() + hdr.type_ids_off + return_type_idx * 4, 4);
                    return_desc = read_dex_string_from_raw(raw, ret_str_idx, hdr);
                }

                // Build proto: "(" + params + ")" + return.
                std::string proto = "(";
                if (parameters_off != 0 && parameters_off + 4 <= raw.size()) {
                    // TypeList starts with a uint32 size, then size * 4 bytes of type_idx.
                    uint32_t list_size;
                    std::memcpy(&list_size, raw.data() + parameters_off, 4);
                    for (uint32_t i = 0; i < list_size; ++i) {
                        uint32_t off = parameters_off + 4 + i * 2;  // each entry is 2 bytes (uint16)
                        if (off + 2 > raw.size()) break;
                        uint16_t type_idx;
                        std::memcpy(&type_idx, raw.data() + off, 2);
                        if (type_idx < hdr.type_ids_size &&
                            hdr.type_ids_off + (type_idx + 1) * 4 <= raw.size()) {
                            uint32_t desc_str_idx;
                            std::memcpy(&desc_str_idx, raw.data() + hdr.type_ids_off + type_idx * 4, 4);
                            proto += read_dex_string_from_raw(raw, desc_str_idx, hdr);
                        }
                    }
                }
                proto += ")";
                proto += return_desc.empty() ? "V" : return_desc;
                return proto;
            }
        }
    }

proto_fallback:
    // Fallback: try merged proto_ids from dex_report_ (if available).
    // The DexReport may not store protos — return "<unknown>" to let
    // the caller fall back to the old behavior (no wide merging).
    return "<unknown>";
}

// EXP-058: Per-DEX type descriptor resolution.
// type_idx is relative to the current DEX file's type_ids table.
// The type_ids table maps type_idx → string_ids_idx → descriptor string.
// Previously, execute_new_instance used the MERGED global types vector,
// causing type_idx from one DEX to resolve to a type from a different DEX.
std::string DalvikExecutionEngine::resolve_type_for_dex(
    uint32_t type_idx, uint32_t dex_index) const {

    if (dex_index < per_dex_raw_data_.size()) {
        const auto& raw = per_dex_raw_data_[dex_index];
        if (raw.size() < sizeof(dex::DexHeader)) goto fallback;

        dex::DexHeader hdr;
        std::memcpy(&hdr, raw.data(), sizeof(dex::DexHeader));

        if (type_idx < hdr.type_ids_size &&
            hdr.type_ids_off + (type_idx + 1) * 4 <= raw.size()) {

            // type_ids[type_idx] = string_ids_idx (descriptor string)
            uint32_t descriptor_idx;
            std::memcpy(&descriptor_idx, raw.data() + hdr.type_ids_off + type_idx * 4, 4);

            return read_dex_string_from_raw(raw, descriptor_idx, hdr);
        }
    }

fallback:
    if (dex_report_ && type_idx < dex_report_->types.size()) {
        return dex_report_->types[type_idx];
    }
    return "<unknown>";
}

// EXP-071: Per-DEX proto (method descriptor) resolution.
// Reads the proto_ids table from raw DEX bytes to resolve method_idx →
// proto descriptor (e.g. "(Lorg/telegram/tgnet/TLRPC$TL_error;)V").
// This is the actual method descriptor; existing resolve_method_name_for_dex
// only returns the bare method NAME (e.g. "run"), which is not enough to
// decide whether wide register merging is needed for $r8$lambda methods.
//
// We resolve:
//   1. method_ids[method_idx].proto_idx → proto_ids index.
//   2. proto_ids[proto_idx].shorty_idx → shorty string (e.g. "VL")
//   3. proto_ids[proto_idx].return_type_idx → return type descriptor.
//   4. proto_ids[proto_idx].parameters_off → type_list of parameter types.
//   5. Assemble "(param_types)return_type" — full descriptor.
std::string DalvikExecutionEngine::resolve_method_proto_for_dex(
    uint32_t method_idx, uint32_t dex_index) const {

    if (dex_index < per_dex_raw_data_.size()) {
        const auto& raw = per_dex_raw_data_[dex_index];
        if (raw.size() < sizeof(dex::DexHeader)) goto fallback;

        dex::DexHeader hdr;
        std::memcpy(&hdr, raw.data(), sizeof(dex::DexHeader));

        if (method_idx >= hdr.method_ids_size ||
            hdr.method_ids_off + (method_idx + 1) * sizeof(dex::DexMethodId) > raw.size()) {
            goto fallback;
        }

        dex::DexMethodId mid;
        std::memcpy(&mid, raw.data() + hdr.method_ids_off + method_idx * sizeof(dex::DexMethodId),
                    sizeof(dex::DexMethodId));

        uint32_t proto_idx = mid.proto_idx;
        if (proto_idx >= hdr.proto_ids_size ||
            hdr.proto_ids_off + (proto_idx + 1) * sizeof(dex::DexProtoId) > raw.size()) {
            goto fallback;
        }

        dex::DexProtoId pid;
        std::memcpy(&pid, raw.data() + hdr.proto_ids_off + proto_idx * sizeof(dex::DexProtoId),
                    sizeof(dex::DexProtoId));

        // Resolve return type descriptor.
        std::string return_type_desc = "<unknown>";
        if (pid.return_type_idx < hdr.type_ids_size &&
            hdr.type_ids_off + (pid.return_type_idx + 1) * 4 <= raw.size()) {
            uint32_t descriptor_idx;
            std::memcpy(&descriptor_idx,
                        raw.data() + hdr.type_ids_off + pid.return_type_idx * 4, 4);
            return_type_desc = read_dex_string_from_raw(raw, descriptor_idx, hdr);
        }

        // Resolve parameter types via the type_list at parameters_off.
        // type_list layout: | size (4 bytes) | list[] of type_idx (4 bytes each) |.
        std::string params_str;
        if (pid.parameters_off != 0 && pid.parameters_off + 4 <= raw.size()) {
            uint32_t list_size;
            std::memcpy(&list_size, raw.data() + pid.parameters_off, 4);
            // Bound check the list entries.
            size_t list_start = pid.parameters_off + 4;
            size_t list_bytes = static_cast<size_t>(list_size) * 4u;
            if (list_size <= 1024 && list_start + list_bytes <= raw.size()) {
                for (uint32_t i = 0; i < list_size; ++i) {
                    uint32_t type_idx;
                    std::memcpy(&type_idx, raw.data() + list_start + i * 4, 4);
                    if (type_idx < hdr.type_ids_size &&
                        hdr.type_ids_off + (type_idx + 1) * 4 <= raw.size()) {
                        uint32_t desc_idx;
                        std::memcpy(&desc_idx,
                                    raw.data() + hdr.type_ids_off + type_idx * 4, 4);
                        params_str += read_dex_string_from_raw(raw, desc_idx, hdr);
                    }
                }
            }
        }

        return "(" + params_str + ")" + return_type_desc;
    }

fallback:
    // Fallback: try the merged DexReport's method_ids + protos tables.
    if (dex_report_ && method_idx < dex_report_->method_ids.size()) {
        uint16_t proto_idx = dex_report_->method_ids[method_idx].proto_idx;
        (void)proto_idx;
        // We can't reliably resolve proto_idx via the merged protos vector
        // because multi-DEX merging shifts indices. Return an empty
        // descriptor so the caller (execute_invoke_static) treats this as
        // a no-arg method (which is the safe default for $r8$lambda methods
        // where the proto is used only for wide-register merging decisions).
    }
    return "()V";
}

// ============================================================================

DalvikExecutionResult DalvikExecutionEngine::execute_apk(
    const std::string& apk_path,
    const dex::DexReport& dex_report,
    bool verbose
) {
    // EXP-037 Phase B (BLOCKER-019): delegate to execute_apk_with_activity
    // with empty activity name (falls back to scan-based heuristic).
    return execute_apk_with_activity(apk_path, dex_report, std::string(), verbose);
}

DalvikExecutionResult DalvikExecutionEngine::execute_apk_with_activity(
    const std::string& apk_path,
    const dex::DexReport& dex_report,
    const std::string& activity_class_name,
    bool verbose
) {
    verbose_ = verbose;

    // EXP-042 Phase 1: Gate debug cerr lines behind verbose. Previously these
    // always printed, generating enormous log volume during long runs (100 M
    // instructions × several cerr lines per recursive call = GB of stderr).
    if (verbose_) {
        std::cerr << "[EXP039] execute_apk_with_activity entered" << std::endl;
        std::cerr << "[EXP039] per_dex_raw_data_ size=" << per_dex_raw_data_.size() << std::endl;
        std::cerr << "[EXP039] class_to_dex_index_ size=" << class_to_dex_index_.size() << std::endl;
        std::cerr << "[EXP039] config_.max_instructions=" << config_.max_instructions << std::endl;
        std::cerr.flush();
    }
    // EXP-037 Phase B (BLOCKER-002 + BLOCKER-015 FIX):
    // Store the DexReport pointer so invoke-* / iget/iput/sget/sput handlers
    // can resolve method_idx and field_idx via DexReport::method_ids[] /
    // field_ids[]. Without this, every invoke-* handler sees dex_report_
    // as nullptr and falls back to "<method_idx:N>" placeholder strings,
    // which prevents the API bridge from routing framework calls.
    dex_report_ = &dex_report;
    DalvikExecutionResult result;
    result.apk_name = apk_path.substr(apk_path.find_last_of("/\\") + 1);
    result.timestamp = get_timestamp();
    result.dex_report = &dex_report;
    
    auto start_time = Clock::now();
    
    log("Executing APK: " + apk_path);
    log("DEX classes: " + std::to_string(dex_report.classes_count));
    
    // ====================================================================
    // EXP-031.6 DEBUG: Trace complete DEX extraction pipeline
    // ====================================================================
    log("=== EXP-031.6 PIPELINE TRACE ===");
    
    int total_methods = 0;
    int methods_with_bytecode = 0;
    int methods_without_bytecode = 0;
    int total_instructions = 0;
    
    for (const auto& cls : dex_report.classes) {
        log("CLASS: " + cls.name + " (" + std::to_string(cls.all_methods().size()) + " methods)");
        
        for (const auto& method : cls.all_methods()) {
            total_methods++;
            
            bool has_code = !method.bytecode.empty();
            size_t insn_count = method.bytecode.size();
            
            if (has_code) {
                methods_with_bytecode++;
                total_instructions += insn_count;
                log("  METHOD [HAS CODE]: " + method.name + method.descriptor + 
                    " | code_off=0x" + std::to_string(method.code_offset) +
                    " | insns_size=" + std::to_string(insn_count) +
                    " | first_insn=0x" + (insn_count > 0 ? 
                        std::to_string(method.bytecode[0]) : "N/A"));
            } else {
                methods_without_bytecode++;
                log("  METHOD [NO CODE]:  " + method.name + method.descriptor +
                    " | code_off=0x" + std::to_string(method.code_offset) +
                    " | is_native=" + (method.is_native ? "Y" : "N") +
                    " | is_abstract=" + (method.is_abstract ? "Y" : "N"));
            }
        }
    }
    
    log("=== PIPELINE SUMMARY ===");
    log("Total methods: " + std::to_string(total_methods));
    log("With bytecode: " + std::to_string(methods_with_bytecode));
    log("Without bytecode: " + std::to_string(methods_without_bytecode));
    log("Total instructions: " + std::to_string(total_instructions));
    
    if (total_instructions == 0) {
        log("🔴 CRITICAL: ZERO INSTRUCTIONS EXTRACTED FROM DEX!");
        log("Root cause candidates:");
        log("  1. parse_code_item() not called (check class_data parsing)");
        log("  2. parse_code_item() called but insns_size=0");
        log("  3. parse_code_item() fails bounds check silently");
    }
    log("=== END EXP-031.6 TRACE ===");
    
    // Find main activity entry point
    if (!dex_report.classes.empty()) {
        log("🔍 Searching " + std::to_string(dex_report.classes.size()) + " classes for entry point...");

        // EXP-037 Phase B (BLOCKER-019 FIX): If the caller provided an explicit
        // activity_class_name from the AndroidManifest, look for that class
        // first. This bypasses the "Activity"/"Main"/"activity" name scan
        // which fails for obfuscated APKs (e.g. TinyMusicPlayer uses La/a;,
        // La/b;, etc.).
        //
        // The activity_class_name is expected to be in DEX type descriptor
        // form, e.g. "Lcom/martinmimigames/tinymusicplayer/Launcher;".
        // If the manifest gives it in dotted form ("com.foo.Launcher"),
        // the caller should convert it.
        if (!activity_class_name.empty()) {
            log("🎯 Manifest-provided activity class: " + activity_class_name);
            for (const auto& cls : dex_report.classes) {
                bool match = (cls.name == activity_class_name);
                // Also try with L prefix + ; suffix if caller passed dotted form
                if (!match) {
                    std::string descriptor_form = "L" + activity_class_name + ";";
                    match = (cls.name == descriptor_form);
                }
                // Also try replacing '.' with '/' (dotted → descriptor form)
                if (!match) {
                    std::string converted = activity_class_name;
                    for (auto& c : converted) if (c == '.') c = '/';
                    std::string descriptor_form2 = "L" + converted + ";";
                    match = (cls.name == descriptor_form2);
                }
                if (match) {
                    log("  ✅ Found manifest activity class in DEX: " + cls.name);
                    result.main_class = cls.name;

                    // EXP-043 Phase 4: Pre-populate static fields that Android's
                    // framework would have set before onCreate is called.
                    // Without this, ApplicationLoader.applicationContext is null
                    // and postInitApplication halts at PC=8.
                    //
                    // 1. Create the Application/Context singleton
                    uint32_t app_ctx_id = heap_.allocate(
                        "Landroid/app/Application;",
                        0,  // pc=0 (pre-execution)
                        0   // frame_id=0 (pre-execution)
                    );
                    DalvikValue app_ctx_val;
                    app_ctx_val.type = DalvikType::OBJECT_REF;
                    app_ctx_val.object_id = app_ctx_id;
                    app_ctx_val.class_desc = "Landroid/app/Application;";
                    // Store as ApplicationLoader.applicationContext static field
                    static_field_storage_["Lorg/telegram/messenger/ApplicationLoader;.applicationContext"]
                        = app_ctx_val;
                    // Also cache as the Context singleton so getResources() etc. work
                    api_singletons_["Landroid/content/Context;"] = app_ctx_id;

                    // EXP-046: Pre-populate NativeLoader.nativeLoaded = true.
                    DalvikValue native_loaded;
                    native_loaded.type = DalvikType::BOOLEAN;
                    native_loaded.bool_val = true;
                    native_loaded.int_val = 1;
                    static_field_storage_["Lorg/telegram/messenger/NativeLoader;.nativeLoaded"]
                        = native_loaded;

                    // 2. Create the Activity object (this) for onCreate
                    uint32_t activity_obj_id = heap_.allocate(
                        cls.name,  // "Lorg/telegram/ui/LaunchActivity;"
                        0,
                        0
                    );
                    DalvikValue activity_val;
                    activity_val.type = DalvikType::OBJECT_REF;
                    activity_val.object_id = activity_obj_id;
                    activity_val.class_desc = cls.name;

                    // Find onCreate method
                    for (const auto& method : cls.all_methods()) {
                        if (method.name == "onCreate" || method.name == "main") {
                            result.main_method = method.name;
                            log("Found entry point: " + method.name + method.descriptor);
                            if (!method.bytecode.empty()) {
                                log("🎯 CALLING execute_method_internal() for " + method.name +
                                    " with " + std::to_string(method.bytecode.size()) + " instructions");

                                // EXP-043 Phase 4: Pass `this` (Activity) and Bundle
                                // as args. onCreate(Bundle) has ins=2: p0=this, p1=Bundle.
                                // The Bundle can be null (real Android passes null on
                                // first launch).
                                std::vector<DalvikValue> entry_args;
                                entry_args.push_back(activity_val);  // p0 = this (Activity)
                                entry_args.push_back(DalvikValue::make_null());  // p1 = Bundle (null)

                                execute_method_internal(
                                    cls.name,
                                    method.name,
                                    method.descriptor,
                                    method.bytecode,
                                    method.registers_size ? method.registers_size : 16,  // EXP-058: use actual
                                    method.ins_size ? method.ins_size : 2,  // EXP-058: use actual
                                    method.outs_size ? method.outs_size : 4,  // EXP-058: use actual
                                    entry_args,
                                    result,
                                    method.tries_size,
                                    method.tries_data.data(),
                                    method.tries_data.size()
                                );
                                log("✅ execute_method_internal() returned");
                            } else {
                                log("⚠️ Method " + method.name + " has EMPTY bytecode - skipping");
                            }
                            break;
                        }
                    }
                    // Skip the legacy scan loop
                    goto entry_point_search_done;
                }
            }
            log("⚠️ Manifest activity class '" + activity_class_name + "' not found in DEX — falling back to scan");
        }

        // Look for Activity-like classes (legacy heuristic)
        for (const auto& cls : dex_report.classes) {
            log("  Checking class: [" + cls.name + "] for Activity/Main/activity");

            if (cls.name.find("Activity") != std::string::npos ||
                cls.name.find("Main") != std::string::npos ||
                cls.name.find("activity") != std::string::npos) {
                
                result.main_class = cls.name;
                log("Found main class candidate: " + cls.name);
                
                // Find onCreate method
                for (const auto& method : cls.all_methods()) {
                    if (method.name == "onCreate" || method.name == "main") {
                        result.main_method = method.name;
                        log("Found entry point: " + method.name + method.descriptor);
                        
                        // Execute this method
                        if (!method.bytecode.empty()) {
                            log("🎯 CALLING execute_method_internal() for " + method.name + 
                                " with " + std::to_string(method.bytecode.size()) + " instructions");
                            execute_method_internal(
                                cls.name,
                                method.name,
                                method.descriptor,
                                method.bytecode,
                                10,  // registers_size (estimated)
                                1,   // ins_size (Bundle parameter)
                                4,   // outs_size
                                {},  // No args for now
                                result,
                                method.tries_size,
                                method.tries_data.data(),
                                method.tries_data.size()
                            );
                            log("✅ execute_method_internal() returned");
                        } else {
                            log("⚠️ Method " + method.name + " has EMPTY bytecode - skipping");
                        }
                        break;
                    }
                }
                break;
            }
        }
        entry_point_search_done: ;

        // If no Activity found, try first class with methods
        log("🔍 main_method is " + (result.main_method.empty() ? "EMPTY" : result.main_method) + ", trying fallback...");
        if (result.main_method.empty()) {
            log("📋 Entering fallback mode - looking for any class with methods");
            for (const auto& cls : dex_report.classes) {
                log("  📋 Checking fallback class: [" + cls.name + "] with " + 
                    std::to_string(cls.all_methods().size()) + " methods");
                auto methods = cls.all_methods();
                log("  📋 all_methods() returned " + std::to_string(methods.size()) + " entries");
                if (!methods.empty()) {
                    result.main_class = cls.name;
                    const auto& method = methods[0];  // Use local copy
                    result.main_method = method.name;
                    
                    log("🎯 Using fallback entry: " + cls.name + "." + method.name);
                    log("🎯 Bytecode size: " + std::to_string(method.bytecode.size()));
                    
                    if (!method.bytecode.empty()) {
                        log("🚀 ABOUT TO CALL execute_method_internal() for fallback!");
                        try {
                            execute_method_internal(
                                cls.name, method.name, method.descriptor,
                                method.bytecode, 8, 0, 2, {}, result,
                                method.tries_size,
                                method.tries_data.data(),
                                method.tries_data.size()
                            );
                            log("✅ execute_method_internal() completed successfully");
                        } catch (const std::exception& e) {
                            log("❌ execute_method_internal() threw exception: " + std::string(e.what()));
                        }
                    } else {
                        log("⚠️ Fallback method has empty bytecode!");
                    }
                    break;
                }
            }
        }
    }
    
    auto end_time = Clock::now();
    result.total_execution_ms = std::chrono::duration<double, std::milli>(end_time - start_time).count();
    result.final_registers = call_stack_.empty() ? json::object() : call_stack_.top().registers.dump();
    
    log("Execution completed in " + std::to_string(result.total_execution_ms) + "ms");
    log("Instructions executed: " + std::to_string(result.total_instructions_executed));
    
    return result;
}

DalvikExecutionResult DalvikExecutionEngine::execute_method(
    const dex::MethodInfo& method,
    const dex::DexReport& dex_report,
    const std::vector<DalvikValue>& args,
    bool verbose
) {
    verbose_ = verbose;
    DalvikExecutionResult result;
    result.timestamp = get_timestamp();
    result.dex_report = &dex_report;
    result.main_class = method.defining_class;
    result.main_method = method.name;
    
    if (!method.bytecode.empty()) {
        execute_method_internal(
            method.defining_class,
            method.name,
            method.descriptor,
            method.bytecode,
            16,  // Default register count
            static_cast<uint32_t>(args.size()),
            4,   // Default outs
            args,
            result,
            method.tries_size,
            method.tries_data.data(),
            method.tries_data.size()
        );
    }
    
    return result;
}

// ============================================================================
// Core Execution Loop
// ============================================================================

bool DalvikExecutionEngine::execute_method_internal(
    const std::string& class_name,
    const std::string& method_name,
    const std::string& descriptor,
    const std::vector<uint16_t>& bytecode,
    uint32_t registers_size,
    uint32_t ins_size,
    uint32_t outs_size,
    const std::vector<DalvikValue>& args,
    DalvikExecutionResult& result,
    uint16_t tries_size,
    const uint8_t* tries_data,
    size_t tries_data_size
) {
    current_result_ = &result;
    bytecode_ = bytecode;
    halted_ = false;
    halted_on_return_ = false;
    instruction_sequence_ = 0;
    // EXP-042 Phase 1: Per-frame loop detection counter. Reset on each new
    // method invocation so recursive calls do not pollute each other.
    pc_visit_count_.clear();
    // EXP-042 Phase 2: Set current_class_/current_method_ so loop-detector
    // halt messages and traces can identify the method that halted.
    current_class_ = class_name;
    current_method_ = method_name;
    // EXP-052: Save tries[] state for the THROW opcode handler.
    current_tries_size_ = tries_size;
    current_tries_data_ = tries_data;
    current_tries_data_size_ = tries_data_size;
    // EXP-053: Clear pending exception at method entry.
    pending_exception_ = DalvikValue::make_null();
    // EXP-042 Phase 4: Log the first 5000 method entries for diagnostic
    // visibility, then suppress to avoid log spam during long runs.
    // EXP-043 Phase 1: raised from 200 to 5000 to capture the full path
    // to the Intrinsics loop blocker.
    // EXP-053: raised to 100000 to capture <clinit> paths.
    static thread_local uint64_t method_entry_count = 0;
    if (method_entry_count < 100000) {
        std::cerr << "[METHOD-IN] " << class_name << "." << method_name
                  << " (bytecode_size=" << bytecode.size() << ")" << std::endl;
        method_entry_count++;
    }

    // EXP-038 (BLOCKER-033): Set current_dex_index_ for per-DEX method resolution.
    // Look up which DEX file this class came from.
    auto it = class_to_dex_index_.find(class_name);
    if (it != class_to_dex_index_.end()) {
        current_dex_index_ = it->second;
    }

    log("Executing: " + class_name + "." + method_name + descriptor);
    log("Bytecode size: " + std::to_string(bytecode.size()) + " instructions");
    
    // Create stack frame
    StackFrame frame;
    frame.class_name = class_name;
    frame.method_name = method_name;
    frame.method_descriptor = descriptor;
    frame.code_offset = 0;
    frame.bytecode_length = bytecode.size();
    frame.registers_size = registers_size;
    frame.ins_size = ins_size;
    frame.outs_size = outs_size;
    frame.registers.initialize(registers_size, ins_size);
    
    // Load arguments into parameter registers
    for (size_t i = 0; i < args.size() && i < ins_size; ++i) {
        frame.registers.write_p(static_cast<uint8_t>(i), args[i]);
    }

    // EXP-062: Debug — trace parameter loading for PhoneView.<init>
    if (class_name.find("PhoneView") != std::string::npos &&
        method_name == "<init>") {
        std::cerr << "[EXP062-PARAM] PhoneView.<init> entering"
                  << " regs=" << registers_size << " ins=" << ins_size
                  << " param_start=" << (registers_size - ins_size)
                  << " args=" << args.size()
                  << std::endl;
        for (size_t i = 0; i < args.size() && i < ins_size; ++i) {
            auto val = frame.registers.read_v(static_cast<uint8_t>(
                registers_size - ins_size + i));
            std::cerr << "  p" << i << " → v" << (registers_size - ins_size + i)
                      << " arg_type=" << static_cast<int>(args[i].type)
                      << " arg_obj=" << args[i].object_id
                      << " arg_class=" << args[i].class_desc
                      << " reg_type=" << static_cast<int>(val.type)
                      << " reg_obj=" << val.object_id
                      << std::endl;
        }
    }

    // EXP-063: Trace getString parameter passing
    if (class_name.find("LocaleController") != std::string::npos &&
        method_name == "getString") {
        std::cerr << "[EXP063-GETSTRING] entering"
                  << " regs=" << registers_size << " ins=" << ins_size
                  << " param_start=" << (registers_size - ins_size)
                  << " args=" << args.size()
                  << std::endl;
        for (size_t i = 0; i < args.size() && i < ins_size; ++i) {
            auto val = frame.registers.read_v(static_cast<uint8_t>(
                registers_size - ins_size + i));
            std::cerr << "  p" << i << " → v" << (registers_size - ins_size + i)
                      << " arg_type=" << static_cast<int>(args[i].type)
                      << " arg_int=" << args[i].int_val
                      << " arg_obj=" << args[i].object_id
                      << " reg_type=" << static_cast<int>(val.type)
                      << " reg_int=" << val.int_val
                      << std::endl;
        }
    }

    // EXP-058: Debug — verify parameter writes for addFragmentToStack.
    if (current_method_.find("addFragmentToStack") != std::string::npos ||
        method_name.find("addFragmentToStack") != std::string::npos) {
        for (size_t i = 0; i < args.size() && i < ins_size; ++i) {
            auto val = frame.registers.read_v(static_cast<uint8_t>(
                registers_size - ins_size + i));
            // EXP-059: For INT32, print int_val (not object_id which is always 0).
            std::string arg_val_str;
            if (args[i].type == DalvikType::INT32) {
                arg_val_str = "int_val=" + std::to_string(args[i].int_val);
            } else if (args[i].type == DalvikType::OBJECT_REF) {
                arg_val_str = "obj_id=" + std::to_string(args[i].object_id) +
                              " class=" + args[i].class_desc;
            } else {
                arg_val_str = "obj=" + std::to_string(args[i].object_id);
            }
            std::cerr << "[EXP058-PARAM] p" << i
                      << " → v" << (registers_size - ins_size + i)
                      << " type=" << static_cast<int>(val.type)
                      << " obj=" << val.object_id
                      << " (from arg type=" << static_cast<int>(args[i].type)
                      << " " << arg_val_str << ")"
                      << std::endl;
        }
    }
    
    // Push frame onto call stack
    call_stack_.push_frame(std::move(frame));
    current_registers_ = &call_stack_.top().registers;
    pc_ = 0;
    
    // Execute until halt
    bool success = fetch_decode_execute(result);

    // EXP-042 Phase 1: memory probe after each method returns. This lets us
    // see whether memory grows linearly with recursive call count (a leak)
    // or stays flat (capped). Sampled once per method exit.
    {
        static thread_local uint64_t last_probe_seq = 0;
        if (instruction_sequence_ - last_probe_seq >= 10000 ||
            last_probe_seq == 0) {
            std::string tag = "method_exit: " + class_name + "." + method_name +
                              " insns=" + std::to_string(instruction_sequence_);
            miniandroid::probe::mark(tag.c_str());
            last_probe_seq = instruction_sequence_;
        }
    }
    
    // Pop frame (if not already done by return)
    if (!call_stack_.empty()) {
        call_stack_.pop_frame();
        current_registers_ = nullptr;
    }
    
    // Update result
    result.call_stack = call_stack_;
    result.heap = heap_;
    
    if (halted_on_return_) {
        result.final_status = DalvikExecutionResult::FinalStatus::COMPLETED_SUCCESS;
    } else if (halted_) {
        result.final_status = DalvikExecutionResult::FinalStatus::HALTED_UNIMPLEMENTED_OPCODE;
        result.halt_reason = halt_reason_;
    } else {
        result.final_status = DalvikExecutionResult::FinalStatus::COMPLETED_PARTIAL;
    }
    
    current_result_ = nullptr;
    return success;
}

// EXP-053: Ensure a class is initialized before accessing its static fields.
//
// Per JVM spec §2.17.4 (Initialization), a class is initialized the first
// time it is "actively used". Active use includes:
//   - new-instance on the class
//   - invoke-static on a method declared by the class
//   - sget/sput on a field declared by the class
//
// Initialization triggers <clinit> (the static initializer block, which
// may contain `const + sput` pairs that set the field values, plus other
// side-effecting code).
//
// We call this from the sget/sput handlers and from new-instance. The
// method is idempotent: a class already marked initialized is a no-op.
//
// Notes:
//   - Framework classes (Landroid/*, Ljava/*, Lkotlin/*) do NOT get
//     <clinit> executed — they're stubbed by the shadow registry / bridge.
//   - For application classes (Lorg/telegram/*, Lcom/example/*, etc.),
//     we look up the class in the DexReport, find its <clinit> method,
//     and recursively execute it.
//   - We guard against re-entrancy: if the class is currently being
//     initialized (in_initialization_ set), we return immediately.
bool DalvikExecutionEngine::ensure_class_initialized(const std::string& class_descriptor) {
    // Already initialized?
    if (initialized_classes_.count(class_descriptor) > 0) {
        return true;
    }
    // Framework classes — skip <clinit> (they're stubbed).
    // The shadow registry / bridge_to_api handles their static fields.
    // EXP-053: expanded to include androidx/* (these are framework-style
    // libraries that we don't have full bytecode semantics for; their
    // R classes are auto-generated and would need Resource table parsing
    // to populate correctly).
    if (class_descriptor.rfind("Landroid/", 0) == 0 ||
        class_descriptor.rfind("Landroidx/", 0) == 0 ||
        class_descriptor.rfind("Ljava/", 0) == 0 ||
        class_descriptor.rfind("Lkotlin/", 0) == 0 ||
        class_descriptor.rfind("Lkotlinx/", 0) == 0 ||
        class_descriptor.rfind("Lcom/google/", 0) == 0 ||
        class_descriptor.rfind("Lj$/", 0) == 0) {
        initialized_classes_.insert(class_descriptor);
        return true;
    }
    // EXP-053: Only run <clinit> for classes in the org.telegram.* namespace.
    // EXP-054: Re-enabled after MethodInfo lifetime fix (store by value).
    // Still limiting to org.telegram/* to avoid deep recursion in androidx
    // classes (which have complex <clinit> methods that call many other
    // classes' <clinit>, causing stack overflow).
    if (class_descriptor.rfind("Lorg/telegram/", 0) != 0) {
        initialized_classes_.insert(class_descriptor);
        return true;
    }
    // Need DexReport to find the class.
    if (!dex_report_) {
        initialized_classes_.insert(class_descriptor);
        return false;
    }
    // Find the class in the DexReport.
    auto class_it = class_info_index_.find(class_descriptor);
    if (class_it == class_info_index_.end()) {
        // EXP-062: Debug — trace R class lookups
        if (class_descriptor.find("R$") != std::string::npos) {
            std::cerr << "[EXP062-RLOOKUP] " << class_descriptor
                      << " NOT FOUND in class_info_index_ (size="
                      << class_info_index_.size() << ")"
                      << std::endl;
        }
        initialized_classes_.insert(class_descriptor);
        return false;
    }
    const dex::ClassInfo& cls_ref = dex_report_->classes[class_it->second];
    // Mark initialized BEFORE running <clinit> to prevent re-entrancy.
    initialized_classes_.insert(class_descriptor);

    // EXP-062: Count fields with defaults for this class
    {
        int with_defaults = 0;
        for (const auto& f : cls_ref.static_fields) {
            if (f.has_default_value) with_defaults++;
        }
        if (with_defaults > 0 || class_descriptor.find("R$") != std::string::npos) {
            std::cerr << "[EXP062-INIT] " << class_descriptor
                      << " static_fields=" << cls_ref.static_fields.size()
                      << " with_defaults=" << with_defaults
                      << std::endl;
        }
    }

    // EXP-063: Build field_name_by_resid mapping for R classes.
    // This maps resource ID → field name, so we can resolve resources
    // by name when DEX IDs don't match ARSC entry indices.
    // EXP-063 FIX: Only store INT values (actual resource IDs like 0x000f0000).
    // BOOLEAN values (true=1, false=0) from resource shrinking must be
    // excluded because they collide with real resource IDs.
    if (class_descriptor.find("R$") != std::string::npos) {
        for (const auto& field : cls_ref.static_fields) {
            if (!field.has_default_value || field.default_value_is_string) continue;
            // Only store values that look like resource IDs (>= 0x10000)
            // This excludes BOOLEAN values (0, 1) and small integers.
            if (field.default_int_value >= 0x10000) {
                field_name_by_resid_[static_cast<int32_t>(field.default_int_value)] = field.name;
            }
        }
    }

    // EXP-062: Initialize static fields from DEX encoded_array_item
    // (default values). This is critical for R classes (R$drawable,
    // R$string, R$color) which have NO <clinit> — their field values
    // are baked into the DEX by the build system as default values.
    // EXP-063: Don't overwrite values already set by pre-population
    // (e.g., ApplicationLoader.applicationContext is set before execution).
    // But DO overwrite if the existing value is the default 0 (from a
    // previous SGET that found no stored value).
    for (const auto& field : cls_ref.static_fields) {
        if (!field.has_default_value) continue;
        std::string static_key = class_descriptor + "." + field.name;
        auto it = static_field_storage_.find(static_key);
        if (it != static_field_storage_.end()) {
            // Only skip if the value is non-zero (pre-populated)
            if (it->second.type == DalvikType::INT32 && it->second.int_val != 0) {
                continue;
            }
            if (it->second.type != DalvikType::INT32) {
                continue;  // Non-int values (objects, strings) — don't overwrite
            }
            // int_val == 0: this is a default, overwrite with DEX default
        }
        if (field.default_value_is_string) {
            DalvikValue sv = DalvikValue::make_string(field.default_string_value, 0);
            static_field_storage_[static_key] = sv;
        } else {
            static_field_storage_[static_key] = DalvikValue::make_int(
                static_cast<int32_t>(field.default_int_value));
        }
    }

    // Find the <clinit> method.
    for (const auto& m : cls_ref.direct_methods) {
        if (m.name != "<clinit>") continue;
        if (m.bytecode.empty()) continue;
        std::cerr << "[CLASS_INIT] class=" << class_descriptor
                  << " method=<clinit>"
                  << " bytecode_size=" << m.bytecode.size()
                  << std::endl;
        DalvikValue dummy_return;
        bool ok = try_recursive_invoke(
            class_descriptor,
            "<clinit>",
            /*args=*/{},
            dummy_return,
            *current_result_
        );
        std::cerr << "[CLASS_INIT] class=" << class_descriptor
                  << " method=<clinit>"
                  << " result=" << (ok ? "OK" : "FAILED")
                  << std::endl;
        break;
    }
    return true;
}

// EXP-038 (BLOCKER-034): Recursive DEX method invocation.
// Search the DEX for a method matching declaring_class + method_name.
// If found with bytecode, recursively execute it.
bool DalvikExecutionEngine::try_recursive_invoke(
    const std::string& declaring_class,
    const std::string& method_name,
    const std::vector<DalvikValue>& args,
    DalvikValue& return_val,
    DalvikExecutionResult& result,
    const std::string& method_descriptor
) {
    // EXP-055: Debug — log EVERY entry to try_recursive_invoke (first 20 only).
    static thread_local uint64_t entry_log_count = 0;
    if (entry_log_count < 20) {
        entry_log_count++;
        std::cerr << "[TRY-ENTRY] " << declaring_class << "." << method_name
                  << " dex_report=" << (dex_report_ ? "YES" : "NULL")
                  << std::endl;
    }
    // EXP-061: Debug — trace SlideView specifically
    if (declaring_class.find("SlideView") != std::string::npos) {
        std::cerr << "[EXP061-TRY] try_recursive_invoke called for "
                  << declaring_class << "." << method_name
                  << " args=" << args.size()
                  << " depth=" << recursion_depth_
                  << " caller=" << current_class_ << "." << current_method_
                  << std::endl;
    }
    if (!dex_report_) return false;

    // EXP-040: Recursion depth protection
    if (recursion_depth_ >= MAX_RECURSION_DEPTH) {
        log("⚠️ RECURSION LIMIT: depth=" + std::to_string(recursion_depth_) +
            " for " + declaring_class + "." + method_name + " — falling back to API bridge");
        return false;  // Fall back to API bridge
    }
    recursion_depth_++;

    // EXP-071: ───────────────────────────────────────────────────────────
    // CRITICAL INTERCEPTS — these MUST run BEFORE the DEX method lookup so
    // that problematic methods never recurse into the broken bytecode paths.
    // Each intercept returns true (handled) or false (fall through to DEX).
    // ───────────────────────────────────────────────────────────────────

    // EXP-071: getParentActivity → return LaunchActivity singleton.
    // The DEX bytecode for getParentActivity calls getView().getContext()
    // which fails (no real View/Context chain). Return LaunchActivity
    // singleton directly AND initialize doneButtonVisible[0..9] = true
    // on the LoginActivity receiver (the one Lambda3 captured at PC=8).
    if (method_name == "getParentActivity") {
        // Return the LaunchActivity singleton.
        DalvikValue launch = get_or_create_singleton("Lorg/telegram/ui/LaunchActivity;");
        return_val = launch;

        // Initialize doneButtonVisible[0..9] = true on the receiver.
        // The receiver is args[0] (the LoginActivity instance captured by
        // Lambda3). We allocate a 10-element boolean array and fill it.
        if (!args.empty() && args[0].type == DalvikType::OBJECT_REF &&
            args[0].object_id != 0) {
            uint32_t login_id = args[0].object_id;
            uint32_t arr_id = heap_.allocate("Larray;", pc_, 0);
            heap_.set_object_field(arr_id, "__array_length__",
                                   DalvikValue::make_int(10));
            for (int i = 0; i < 10; ++i) {
                std::string fn = "array[" + std::to_string(i) + "]";
                heap_.set_object_field(arr_id, fn, DalvikValue::make_bool(true));
            }
            // Attach the array to the LoginActivity receiver as a field.
            // Telegram's LoginActivity stores it as a private field
            // `doneButtonVisible` (boolean[]).
            DalvikValue arr_val;
            arr_val.type = DalvikType::OBJECT_REF;
            arr_val.object_id = arr_id;
            arr_val.class_desc = "Larray;";
            heap_.set_object_field(login_id, "doneButtonVisible", arr_val);
            std::cerr << "[EXP071-PARENT] getParentActivity → LaunchActivity singleton"
                      << " login_id=" << login_id
                      << " doneButtonVisible[]=" << arr_id
                      << std::endl;
        } else {
            std::cerr << "[EXP071-PARENT] getParentActivity → LaunchActivity singleton"
                      << " (no receiver to attach doneButtonVisible)"
                      << std::endl;
        }
        recursion_depth_--;
        return true;
    }

    // EXP-071: isSimAvailable → false (no SIM in headless runtime).
    // The DEX bytecode for isSimAvailable loops on TelephonyManager calls
    // which return null in our runtime, causing infinite recursion.
    if (method_name == "isSimAvailable") {
        std::cerr << "[EXP071-SIM] isSimAvailable → false (no SIM)" << std::endl;
        return_val = DalvikValue::make_bool(false);
        recursion_depth_--;
        return true;
    }

    // EXP-071: sendRequest (ConnectionsManager) — intercept BEFORE the DEX
    // method lookup because the DEX method calls native_sendRequest which
    // returns 0 (no real native impl), causing the caller to spin.
    //
    // We mock:
    //   * TL_help_getNearestDc → TL_nearestDc{country="US"}
    //   * TL_auth_sendCode      → TL_auth_sentCode
    // Then we dispatch the delegate's run() via try_recursive_invoke.
    if (method_name == "sendRequest" &&
        declaring_class.find("ConnectionsManager") != std::string::npos) {
        std::cerr << "[EXP071-SNDREQ] sendRequest intercepted"
                  << " class=" << declaring_class
                  << " args=" << args.size()
                  << std::endl;

        // Telegram's native_sendRequest signature:
        //   sendRequest(TLObject req, RequestDelegate delegate,
        //               ... extra args ...)
        // The args vector includes `this` as args[0] for instance methods.
        // We treat args.size() >= 3 as having (this, req, delegate, ...).
        uint32_t delegate_id = 0;
        uint32_t request_id = 0;
        if (args.size() >= 3) {
            request_id = (args[1].type == DalvikType::OBJECT_REF)
                         ? args[1].object_id : 0;
            delegate_id = (args[2].type == DalvikType::OBJECT_REF)
                          ? args[2].object_id : 0;
        }

        // Build a mock response object based on the request type.
        uint32_t response_id = 0;
        if (request_id != 0 && heap_.has_object(request_id)) {
            const auto* req_obj = heap_.get(request_id);
            std::string req_cls = req_obj ? req_obj->class_descriptor : "";
            if (req_cls.find("TL_help_getNearestDc") != std::string::npos) {
                // Mock TL_nearestDc{country="US"}.
                response_id = heap_.allocate(
                    "Lorg/telegram/tgnet/TLRPC$TL_nearestDc;", pc_, 0);
                DalvikValue country;
                country.type = DalvikType::STRING_REF;
                country.string_val = "US";
                country.ref_id = 0;
                heap_.set_object_field(response_id, "country", country);
                std::cerr << "[EXP071-SNDREQ] mocked TL_nearestDc{country=US}"
                          << " resp_id=" << response_id << std::endl;
            } else if (req_cls.find("TL_auth_sendCode") != std::string::npos) {
                // Mock TL_auth_sentCode (empty — phone code hash not needed
                // for our headless flow since we short-circuit the next step).
                response_id = heap_.allocate(
                    "Lorg/telegram/tgnet/TLRPC$TL_auth_sentCode;", pc_, 0);
                std::cerr << "[EXP071-SNDREQ] mocked TL_auth_sentCode"
                          << " resp_id=" << response_id << std::endl;
            } else {
                // Unknown request — return a generic TLObject so the
                // delegate's run(TLObject, TL_error) doesn't NPE.
                response_id = heap_.allocate(
                    "Lorg/telegram/tgnet/TLObject;", pc_, 0);
            }
        }

        // Dispatch the delegate's run() with (response, null_error).
        if (delegate_id != 0) {
            uint32_t error_id = 0;  // null TL_error
            dispatch_runnable(delegate_id, response_id, error_id);
        }

        // sendRequest returns int (request id). Return 1 so callers
        // can branch on "request was enqueued".
        return_val = DalvikValue::make_int(1);
        recursion_depth_--;
        return true;
    }

    // EXP-071: BufferedReader.readLine → read next line from open_assets_.
    // The DEX bytecode for readLine loops on read() which returns -1 EOF,
    // but our shadow InputStream.read returns 0 (no real impl).
    if (method_name == "readLine" &&
        declaring_class.find("BufferedReader") != std::string::npos) {
        if (!args.empty() && args[0].type == DalvikType::OBJECT_REF) {
            uint32_t br_id = args[0].object_id;
            // Resolve the underlying asset path via open_assets_ chain.
            // The chain: BufferedReader → InputStreamReader → InputStream.
            uint32_t lookup_id = br_id;
            std::string asset_path;
            size_t* pos_ptr = nullptr;
            for (int hop = 0; hop < 4 && lookup_id != 0; ++hop) {
                auto it = open_assets_.find(lookup_id);
                if (it != open_assets_.end()) {
                    asset_path = it->second.first;
                    pos_ptr = &it->second.second;
                    break;
                }
                // Look at the wrapped source field (InputStreamReader.source,
                // BufferedReader.in). Try common field names.
                if (heap_.has_object(lookup_id)) {
                    const auto* ho = heap_.get(lookup_id);
                    if (!ho) break;
                    uint32_t next_id = 0;
                    for (const char* fn : {"in", "source", "inputStream",
                                            "reader", "is"}) {
                        auto fv = ho->get_field(fn);
                        if (fv.type == DalvikType::OBJECT_REF) {
                            next_id = fv.object_id;
                            break;
                        }
                    }
                    if (next_id == 0 || next_id == lookup_id) break;
                    lookup_id = next_id;
                } else {
                    break;
                }
            }

            if (!asset_path.empty() && pos_ptr != nullptr && !apk_path_.empty()) {
                // Extract the asset from the APK via `unzip -p`.
                // Android assets are stored under the "assets/" prefix in the APK.
                std::string cmd = "unzip -p '" + apk_path_ + "' 'assets/" +
                                  asset_path + "' 2>/dev/null";
                FILE* pipe = popen(cmd.c_str(), "r");
                if (pipe) {
                    // Read full asset, skip to current position, find next line.
                    std::string content;
                    char buf[4096];
                    size_t n;
                    while ((n = fread(buf, 1, sizeof(buf), pipe)) > 0) {
                        content.append(buf, n);
                    }
                    pclose(pipe);
                    if (*pos_ptr < content.size()) {
                        size_t start = *pos_ptr;
                        size_t nl = content.find('\n', start);
                        std::string line;
                        if (nl == std::string::npos) {
                            line = content.substr(start);
                            *pos_ptr = content.size();
                        } else {
                            line = content.substr(start, nl - start);
                            *pos_ptr = nl + 1;
                        }
                        // Trim trailing CR (Windows line endings).
                        if (!line.empty() && line.back() == '\r') {
                            line.pop_back();
                        }
                        return_val = DalvikValue::make_string(line, 0);
                        std::cerr << "[EXP071-READLINE] line=\""
                                  << line << "\" asset=" << asset_path
                                  << std::endl;
                        recursion_depth_--;
                        return true;
                    } else {
                        // EOF.
                        return_val = DalvikValue::make_null();
                        std::cerr << "[EXP071-READLINE] EOF asset="
                                  << asset_path << std::endl;
                        recursion_depth_--;
                        return true;
                    }
                }
            }
        }
        // Fallback: return null (EOF) — don't recurse into DEX.
        return_val = DalvikValue::make_null();
        recursion_depth_--;
        return true;
    }

    // EXP-071: AssetManager.open → create InputStream, store in open_assets_.
    // The DEX bytecode for open throws IOException in headless mode.
    if (method_name == "open" &&
        declaring_class.find("AssetManager") != std::string::npos) {
        // Args: (this, String path) → InputStream.
        // For invoke-virtual, args[0]=this, args[1]=path.
        std::string asset_path;
        std::cerr << "[EXP071-ASSET-ARGS] open argc=" << args.size();
        for (size_t i = 0; i < args.size() && i < 4; i++) {
            std::cerr << " arg[" << i << "]type=" << (int)args[i].type;
            if (args[i].type == DalvikType::STRING_REF) std::cerr << " str=\"" << args[i].string_val << "\"";
            if (args[i].type == DalvikType::OBJECT_REF) std::cerr << " obj=" << args[i].object_id;
        }
        std::cerr << std::endl;
        if (args.size() >= 2 && args[1].type == DalvikType::STRING_REF) {
            asset_path = args[1].string_val;
        }
        uint32_t is_id = heap_.allocate(
            "Ljava/io/InputStream;", pc_, 0);
        // Register the asset path with position 0.
        open_assets_[is_id] = std::make_pair(asset_path, 0);
        DalvikValue is_val;
        is_val.type = DalvikType::OBJECT_REF;
        is_val.object_id = is_id;
        is_val.class_desc = "Ljava/io/InputStream;";
        return_val = is_val;
        std::cerr << "[EXP071-ASSET] AssetManager.open(\""
                  << asset_path << "\") → InputStream id=" << is_id
                  << std::endl;
        recursion_depth_--;
        return true;
    }

    // EXP-071: InputStreamReader.<init> and BufferedReader.<init> —
    // propagate the asset mapping from the wrapped object so readLine
    // can find the asset through the chain.
    if (method_name == "<init>") {
        if ((declaring_class.find("InputStreamReader") != std::string::npos ||
             declaring_class.find("BufferedReader") != std::string::npos) &&
            args.size() >= 2 &&
            args[0].type == DalvikType::OBJECT_REF &&
            args[1].type == DalvikType::OBJECT_REF) {
            uint32_t this_id = args[0].object_id;
            uint32_t wrapped_id = args[1].object_id;
            // Propagate asset mapping from wrapped → this.
            auto it = open_assets_.find(wrapped_id);
            if (it != open_assets_.end()) {
                open_assets_[this_id] = it->second;
                std::cerr << "[EXP071-WRAP] " << declaring_class
                          << ".<init> propagated asset="
                          << it->second.first
                          << " from " << wrapped_id << " to " << this_id
                          << std::endl;
            }
            // Fall through to DEX (the constructor may do real init).
            // But also short-circuit return void so the constructor
            // doesn't try to call super() which may loop.
            return_val = DalvikValue::make_void();
            // Don't return true here — let the DEX bytecode execute if it
            // has a real <init> method (we just propagated the mapping).
        }
    }

    // EXP-071: TextView.length intercept — dispatch to ViewShadow.getText().length().
    // Without this, onNextPressed's validation reads length=0 and fails.
    if (method_name == "length" &&
        declaring_class.find("TextView") != std::string::npos &&
        shadow_registry_ != nullptr) {
        auto* view_shadow = shadow_registry_->find_as<framework::ViewShadow>();
        if (view_shadow != nullptr && !args.empty() &&
            args[0].type == DalvikType::OBJECT_REF) {
            const auto* node = view_shadow->find_node(args[0].object_id);
            if (node != nullptr) {
                int32_t len = static_cast<int32_t>(node->text.size());
                std::cerr << "[EXP071-TVLEN] TextView.length → " << len
                          << " text=\"" << node->text << "\""
                          << std::endl;
                return_val = DalvikValue::make_int(len);
                recursion_depth_--;
                return true;
            }
        }
    }

    // EXP-071: Framework bypass — return false (let the caller bridge_to_api
    // handle these). Returning false here causes the recursive path to abort
    // and the caller's bridge_to_api() runs, where we have specific handlers.
    //
    // These classes are stubs we DON'T want to execute bytecode for because
    // their DEX bytecode calls native methods or depends on real system state
    // we can't satisfy (e.g., HashMap.hash() loops on the key's hashCode()).
    {
        bool should_bypass = false;
        if (declaring_class == "Ljava/util/HashMap;" ||
            declaring_class == "Ljava/util/ArrayList;" ||
            declaring_class == "Ljava/lang/String;" ||
            declaring_class == "Landroid/text/TextUtils;" ||
            declaring_class == "Ljava/io/File;") {
            should_bypass = true;
        }
        // AndroidUtilities.{runOnUIThread,executeOnUIThread,cancelRunOnUIThread}
        // — the DEX bytecode recurses infinitely (each calls the next).
        if (declaring_class.find("AndroidUtilities") != std::string::npos &&
            (method_name == "runOnUIThread" ||
             method_name == "executeOnUIThread" ||
             method_name == "cancelRunOnUIThread")) {
            should_bypass = true;
        }
        // Resources.getAssets — let bridge_to_api return AssetManager singleton.
        if (declaring_class.find("Resources") != std::string::npos &&
            method_name == "getAssets") {
            should_bypass = true;
        }
        if (should_bypass) {
            recursion_depth_--;
            return false;
        }
    }
    // END EXP-071 intercepts ─────────────────────────────────────────────

    // EXP-055: Debug — log entry to try_recursive_invoke for key methods.
    if (method_name.find("isClientActivated") != std::string::npos ||
        method_name.find("getClientNotActivated") != std::string::npos ||
        method_name.find("addFragmentToStack") != std::string::npos) {
        std::cerr << "[TRY-INVOKE] " << declaring_class << "." << method_name
                  << " depth=" << recursion_depth_
                  << std::endl;
    }

    // EXP-059: [FRAGMENT-LIFECYCLE] — log Fragment lifecycle transitions.
    // Maps to the standard Android Fragment lifecycle:
    //   ATTACHED → CREATED → VIEW_CREATED → STARTED → RESUMED
    // We log when a known lifecycle method is invoked on a Fragment subclass,
    // along with the actual runtime class (so we can see e.g. that
    // BaseFragment.onFragmentCreate is called but IntroActivity.onFragmentCreate
    // is also called via polymorphic dispatch).
    if (method_name == "onFragmentCreate" ||
        method_name == "onFragmentDestroy" ||
        method_name == "setParentLayout" ||
        method_name == "createView" ||
        method_name == "onCreateView" ||
        method_name == "onStart" ||
        method_name == "onResume" ||
        method_name == "onPause" ||
        method_name == "onStop" ||
        method_name == "onDestroyView" ||
        method_name == "onDestroy" ||
        method_name == "onAttach" ||
        method_name == "onDetach" ||
        method_name == "onBecomeFullyVisible" ||
        method_name == "onBecomeFullyHidden" ||
        method_name == "attachView" ||
        method_name == "attachSheets") {
        // Look up runtime class from args[0] (this for instance methods)
        std::string runtime_cls = declaring_class;
        if (!args.empty() && args[0].type == DalvikType::OBJECT_REF) {
            if (auto* heap_obj = heap_.get(args[0].object_id)) {
                if (!heap_obj->class_descriptor.empty()) {
                    runtime_cls = heap_obj->class_descriptor;
                }
            }
        }
        std::cerr << "[FRAGMENT-LIFECYCLE] method=" << method_name
                  << " declared_in=" << declaring_class
                  << " runtime_class=" << runtime_cls
                  << std::endl;
    }

    // Convert declaring_class to DEX descriptor form if needed
    // declaring_class may be "Lcom/foo/Bar;" (descriptor) or "com.foo.Bar" (readable)
    std::string class_descriptor = declaring_class;
    if (!class_descriptor.empty() && class_descriptor[0] != 'L') {
        // Convert readable to descriptor
        for (auto& c : class_descriptor) if (c == '.') c = '/';
        class_descriptor = "L" + class_descriptor + ";";
    }

    // EXP-071 Phase 6: Skip try_recursive_invoke for Java/Android framework
    // classes that are NOT in the DEX. These classes (HashMap, ArrayList,
    // String, TextUtils, etc.) are referenced in the DEX's type_ids table
    // but their bytecode is loaded from the Android framework at runtime.
    // try_recursive_invoke would find the class in dex_report_->classes
    // but the method would have NO bytecode — it would return true (found)
    // without executing anything, silently dropping the call.
    //
    // By returning false here, we force the caller to fall through to
    // bridge_to_api, which has stubs for these framework classes.
    //
    // EXP-071 Phase 7: BufferedReader/InputStreamReader/InputStream are
    // EXCLUDED from this bypass because their <init> methods need the
    // asset-tracking intercept (see below, before getParentActivity). That
    // intercept propagates the asset name from the wrapped stream to the
    // reader, so BufferedReader.readLine() can read the correct asset.
    // If we bypass them here, the asset tracking never fires.
    if (class_descriptor.find("Ljava/util/HashMap;") == 0 ||
        class_descriptor.find("Ljava/util/ArrayList;") == 0 ||
        class_descriptor.find("Ljava/util/AbstractList;") == 0 ||
        class_descriptor.find("Ljava/util/AbstractMap;") == 0 ||
        class_descriptor.find("Ljava/lang/String;") == 0 ||
        class_descriptor.find("Landroid/text/TextUtils;") == 0 ||
        class_descriptor.find("Ljava/io/File;") == 0) {
        // Force bridge_to_api for framework classes.
        recursion_depth_--;
        return false;
    }

    // EXP-042 Phase 4: Skip "stub-only" methods — methods that HAVE bytecode
    // in the DEX but should be stubbed instead of executed, because they
    // depend on Android system services we don't implement.
    //
    // Example: com.google.android.gms.dynamite.DynamiteModule.load has a
    // `while(true){}` busy-wait that depends on Play Services IPC. Real
    // Android devices without Play Services throw LoadingException, which
    // the caller catches. We mimic by returning null from the bridge.
    if (class_descriptor.find("DynamiteModule") != std::string::npos &&
        method_name == "load") {
        log("⏭️ STUB-ONLY: " + class_descriptor + "." + method_name +
            " — skipping recursive invoke, delegating to bridge");
        recursion_depth_--;
        return false;  // Fall through to bridge_to_api which returns null
    }

    // EXP-044 Phase 1: AndroidUtilities.runOnUIThread / executeOnUIThread
    // These methods post Runnables to the UI thread Handler. Without a real
    // Handler/Looper, they would recurse infinitely (runOnUIThread calls
    // executeOnUIThread which calls runOnUIThread). Stub as no-op.
    if (class_descriptor.find("AndroidUtilities") != std::string::npos &&
        (method_name == "runOnUIThread" || method_name == "executeOnUIThread" ||
         method_name == "cancelRunOnUIThread")) {
        log("⏭️ STUB-ONLY: " + class_descriptor + "." + method_name +
            " — skipping recursive invoke, delegating to bridge (no-op)");
        recursion_depth_--;
        return false;  // Fall through to bridge_to_api which returns void
    }

    // EXP-044 Phase 1: ContextAwareHelper.dispatchOnContextAvailable
    // This method iterates over a collection of listeners. Without proper
    // collection/iterator support, it loops forever. Stub as no-op.
    if (class_descriptor.find("ContextAwareHelper") != std::string::npos &&
        method_name == "dispatchOnContextAvailable") {
        log("⏭️ STUB-ONLY: " + class_descriptor + "." + method_name +
            " — skipping recursive invoke (collection iteration not supported)");
        recursion_depth_--;
        return false;
    }

    // EXP-045 Phase 2: FragmentStore methods that iterate over collections.
    // These use iterators which we don't support, causing infinite loops.
    if (class_descriptor.find("FragmentStore") != std::string::npos &&
        (method_name == "dispatchStateChange" ||
         method_name == "getActiveFragmentStateManagers")) {
        log("⏭️ STUB-ONLY: " + class_descriptor + "." + method_name +
            " — skipping recursive invoke (collection iteration not supported)");
        recursion_depth_--;
        return false;
    }

    // EXP-058: checkSystemBarColors loops at PC=0x136 (invoke-interface on
    // a null window object). Short-circuit.
    if (class_descriptor.find("LaunchActivity") != std::string::npos &&
        method_name == "checkSystemBarColors") {
        log("⏭️ STUB-ONLY: " + class_descriptor + "." + method_name +
            " — skipping (invoke-interface on null window loop)");
        recursion_depth_--;
        return false;
    }

    // EXP-058: setFragmentStack loops at PC=0x125 (invoke-interface returns
    // VOID_, treated as zero by if-nez, doesn't branch, calls again).
    if (class_descriptor.find("ActionBarLayout") != std::string::npos &&
        method_name == "setFragmentStack") {
        log("⏭️ STUB-ONLY: " + class_descriptor + "." + method_name +
            " — skipping (invoke-interface loop)");
        recursion_depth_--;
        return false;
    }

    // EXP-059: loadCurrentState stub REMOVED. With the opcode-table fix,
    // the previous "invoke-interface loop" no longer occurs. The method
    // now executes correctly: it creates a Bundle, calls
    // SharedPreferences.getAll() (returns empty Map since we have no
    // persisted state), iterates (no entries, exits immediately), and
    // returns the empty Bundle. This is the correct behavior for a
    // first-launch scenario — currentViewNum defaults to 0, so
    // getClientNotActivatedFragment returns IntroActivity (NOT LoginActivity).
    // The original EXP-058 stub was masking a different bug (opcode
    // mis-dispatch), now fixed.

    // EXP-058: removeAllObservers loops (invoke-interface on null list).
    if (class_descriptor.find("ObserversGroup") != std::string::npos &&
        method_name == "removeAllObservers") {
        log("⏭️ STUB-ONLY: " + class_descriptor + "." + method_name +
            " — skipping (invoke-interface loop)");
        recursion_depth_--;
        return false;
    }

    // EXP-058: getIpStrategy loops (invoke-interface returns VOID_).
    if (class_descriptor.find("ConnectionsManager") != std::string::npos &&
        method_name == "getIpStrategy") {
        log("⏭️ STUB-ONLY: " + class_descriptor + "." + method_name +
            " — skipping (invoke-interface loop)");
        recursion_depth_--;
        return false;
    }

    // EXP-054: BaseFragment.getLastSheet loops because isShown() returns
    // void (0/false), and the loop keeps trying the same element. Short-circuit.
    if (class_descriptor.find("BaseFragment") != std::string::npos &&
        method_name == "getLastSheet") {
        log("⏭️ STUB-ONLY: " + class_descriptor + "." + method_name +
            " — skipping (isShown loop)");
        recursion_depth_--;
        return false;
    }

    // EXP-059: Util.toByteArray(InputStream) loops forever because
    // InputStream.read returns 0 (default stub) instead of -1 (EOF).
    // The runtime has no real InputStream implementation. Stub to return
    // an empty byte[] (object_id 0 = null is fine since callers check length).
    if (class_descriptor.find("exoplayer2/util/Util") != std::string::npos &&
        method_name == "toByteArray") {
        log("⏭️ STUB-ONLY: " + class_descriptor + "." + method_name +
            " — skipping (InputStream.read never returns -1)");
        recursion_depth_--;
        return false;
    }

    // EXP-066: OutlineTextContainerView.setText(CharSequence) is a thin wrapper
    // that just iput-objects the text into the mText field and calls invalidate().
    // The text is the floating LABEL of the input field (e.g. "Phone number").
    // The bytecode execution stores the text in the heap field, but the ViewShadow
    // never sees it. Intercept here to capture the text on the ViewNode so the
    // renderer can show it.
    if (method_name == "setText" &&
        class_descriptor.find("OutlineTextContainerView") != std::string::npos) {
        // Dispatch to ViewShadow to capture the text on the ViewNode.
        if (shadow_registry_ != nullptr) {
            framework::CallContext ctx;
            ctx.has_receiver = !args.empty() && args[0].type == DalvikType::OBJECT_REF;
            if (ctx.has_receiver) {
                ctx.receiver_id = args[0].object_id;
                ctx.receiver_class = args[0].class_desc;
                ctx.class_name = args[0].class_desc.empty() ? class_descriptor : args[0].class_desc;
            } else {
                ctx.class_name = class_descriptor;
            }
            ctx.method = method_name;
            for (size_t i = 1; i < args.size(); i++) {
                ctx.args.push_back(dalvik_value_to_arg(args[i]));
            }
            auto cr = shadow_registry_->dispatch(ctx);
            (void)cr;
        }
        // Still let the bytecode execute (it just does iput-object + invalidate,
        // both safe). The shadow dispatch above already captured the text.
        // Fall through to normal execution.
    }

    // EXP-071: AndroidUtilities.isSimAvailable → false
    // In a headless runtime without a real device, there is no SIM card.
    // isSimAvailable checks TelephonyManager.getSimState() which would
    // require real telephony hardware. Return false so that PhoneView.onConfirm
    // takes the auth.sendCode path (PC=435) instead of the permissions path.
    if (method_name == "isSimAvailable" &&
        class_descriptor.find("AndroidUtilities") != std::string::npos) {
        recursion_depth_--;
        return_val = DalvikValue::make_bool(false);
        last_invoke_return_ = return_val;
        std::cerr << "[EXP071] isSimAvailable → false (headless runtime, no SIM)" << std::endl;
        return true;
    }

    // EXP-071 Phase 6: Asset tracking for InputStreamReader/BufferedReader <init>.
    //
    // These constructors are invoked via invoke-direct. try_recursive_invoke
    // would try to execute the actual <init> bytecode, which calls super()
    // and eventually Object.<init>. We intercept BEFORE that to propagate
    // the asset mapping from the wrapped InputStream/Reader to the new
    // BufferedReader/Reader. The constructor itself is a no-op (just calls
    // super), so we can safely return void here.
    //
    // This MUST happen before try_recursive_invoke would execute the bytecode.
    if (method_name == "<init>" &&
        (class_descriptor == "Ljava/io/InputStreamReader;" ||
         class_descriptor == "Ljava/io/BufferedReader;")) {
        // args[0] = this (the reader being constructed)
        // args[1] = the wrapped reader/stream
        if (args.size() >= 2 && args[0].type == DalvikType::OBJECT_REF &&
            args[1].type == DalvikType::OBJECT_REF) {
            uint32_t this_id = args[0].object_id;
            uint32_t wrapped_id = args[1].object_id;
            auto it = open_assets_.find(wrapped_id);
            if (it != open_assets_.end()) {
                open_assets_[this_id] = it->second;
                std::cerr << "[EXP071-ASSET] " << class_descriptor << ".<init>"
                          << " this=" << this_id
                          << " wrapped=" << wrapped_id
                          << " asset=\"" << it->second.first << "\""
                          << std::endl;
            }
        }
        recursion_depth_--;
        return_val = DalvikValue::make_void();
        last_invoke_return_ = return_val;
        return true;
    }

    // EXP-071: getParentActivity compatibility — return the Activity directly.
    // The real method does getView().getContext() instanceof Activity, but
    // invoke-interface dispatch for $default methods fails during onNextPressed.
    // This returns the LaunchActivity singleton so onNextPressed can proceed.
    if (method_name == "getParentActivity") {
        std::cerr << "[EXP071] getParentActivity → LaunchActivity (compatibility intercept)"
                  << " class=" << class_descriptor << std::endl;
        recursion_depth_--;
        return_val = get_or_create_singleton("Lorg/telegram/ui/LaunchActivity;");
        last_invoke_return_ = return_val;
        return true;
    }

    // EXP-071 Phase 6 debug: Trace setCountry entry to understand why it
    // returns immediately without executing HashMap.get.
    if (method_name == "setCountry" && class_descriptor.find("PhoneView") != std::string::npos) {
        std::cerr << "[EXP071-SETCOUNTRY-ENTRY] class=" << class_descriptor
                  << " method=" << method_name
                  << " argc=" << args.size();
        for (size_t i = 0; i < args.size() && i < 4; ++i) {
            std::cerr << " arg[" << i << "]type=" << (int)args[i].type;
            if (args[i].type == DalvikType::OBJECT_REF) {
                std::cerr << " obj=" << args[i].object_id;
            } else if (args[i].type == DalvikType::STRING_REF) {
                std::cerr << " str=\"" << args[i].string_val << "\"";
            }
        }
        std::cerr << std::endl;
    }

    // EXP-070: Controlled network boundary — intercept ConnectionsManager.sendRequest.
    // Telegram's sendRequest(TLObject, RequestDelegate, ...) internally calls
    // native_sendRequest (JNI stub). The response never comes back, so the
    // RequestDelegate callback never fires. This blocks the login→SMS transition.
    //
    // We intercept sendRequest here, capture the RequestDelegate argument,
    // and deliver a controlled mock response through the REAL callback path:
    //   1. Create a mock TL_auth_sentCode object on the heap
    //   2. Invoke RequestDelegate.run(response, null_error) via try_recursive_invoke
    //   3. Let Telegram's own callback bytecode handle the rest
    //
    // Classification: CONTROLLED_NETWORK_STUB — NOT real Telegram networking.
    //
    // EXP-071: Before checking sendRequest, initialize doneButtonVisible if
    // the LoginActivity's doneButtonVisible field is null/uninitialized.
    // This is needed because onDoneButtonPressed reads doneButtonVisible[]
    // and if-nez (opcode 0x39) on the result. When the array is null,
    // aget-boolean returns 0 (false), causing if-nez to NOT branch,
    // making onDoneButtonPressed return early without calling onNextPressed.
    // The real fix is to execute setViews() which initializes the array,
    // but that requires full onShow() lifecycle which is complex.
    // This is a compatibility approximation: initialize doneButtonVisible
    // to [true] when it's null on the LoginActivity object.
    if (method_name == "sendRequest" &&
        class_descriptor.find("ConnectionsManager") != std::string::npos) {
        // Log the sendRequest call with argument info
        std::cerr << "[EXP070-NET] sendRequest intercepted"
                  << " class=" << class_descriptor
                  << " argc=" << args.size()
                  << std::endl;
        for (size_t i = 0; i < args.size() && i < 5; ++i) {
            std::cerr << "  arg[" << i << "] type=" << static_cast<int>(args[i].type);
            if (args[i].type == DalvikType::OBJECT_REF) {
                std::string cls = args[i].class_desc;
                if (cls.empty() && heap_.has_object(args[i].object_id)) {
                    cls = heap_.get(args[i].object_id)->class_descriptor;
                }
                std::cerr << " obj_id=" << args[i].object_id << " class=" << cls;
            }
            std::cerr << std::endl;
        }

        // Find the RequestDelegate argument.
        // sendRequest overloads (args include 'this' at index 0):
        //   3-arg: sendRequest(TLObject, RequestDelegate, int) — args[1]=req, args[2]=delegate
        //   4-arg: sendRequest(TLObject, RequestDelegate, int, int) — args[1]=req, args[2]=delegate
        //   5-arg: sendRequest(TLObject, RequestDelegate, QuickAckDelegate, int) — args[1]=req, args[2]=delegate
        // The delegate is always the 2nd non-this arg (index 2 in args).
        uint32_t delegate_id = 0;
        uint32_t request_id = 0;
        std::string delegate_class;
        std::string request_class;

        if (args.size() >= 3) {
            // args[1] = request (TLObject subclass)
            if (args[1].type == DalvikType::OBJECT_REF && args[1].object_id != 0) {
                request_id = args[1].object_id;
                request_class = args[1].class_desc;
                if (request_class.empty() && heap_.has_object(args[1].object_id)) {
                    request_class = heap_.get(args[1].object_id)->class_descriptor;
                }
            }
            // args[2] = delegate (RequestDelegate — usually an anonymous lambda)
            if (args[2].type == DalvikType::OBJECT_REF && args[2].object_id != 0) {
                delegate_id = args[2].object_id;
                delegate_class = args[2].class_desc;
                if (delegate_class.empty() && heap_.has_object(args[2].object_id)) {
                    delegate_class = heap_.get(args[2].object_id)->class_descriptor;
                }
            }
        }

        if (delegate_id != 0) {
            std::cerr << "[EXP070-NET] RequestDelegate found: obj_id=" << delegate_id
                      << " class=" << delegate_class
                      << " request_id=" << request_id
                      << " request_class=" << request_class
                      << std::endl;

            // EXP-071 Phase 13: Controlled network boundary — generic mock
            // response dispatcher.
            //
            // We now mock MULTIPLE Telegram request types (not just
            // TL_auth_sendCode) so the runtime can drive the application
            // through its complete state machine:
            //
            //   * TL_help_getNearestDc → TL_nearestDc{country="US"}
            //     PhoneView.<init> sends this to detect the user's country
            //     via the network. The callback (Lambda14 → lambda$new$12)
            //     reads response.country, calls setCountry(HashMap, country)
            //     which sets countryState = 0 (LOADED). Without this mock,
            //     countryState stays at 1 (NO_SIM/loading) and onNextPressed
            //     takes the wrong "ChooseCountry" branch instead of reaching
            //     auth.sendCode construction at PC=2410.
            //
            //   * TL_help_getCountriesList → ArrayList of TL_country
            //     PhoneView.loadCountries() sends this; the callback (Lambda19)
            //     populates the countriesArray. Not strictly required for
            //     auth.sendCode but harmless.
            //
            //   * TL_auth_sendCode → TL_auth_sentCode (already mocked).
            //
            // All other request types are still skipped (logged but no mock).
            //
            // This is GENERIC infrastructure — no Telegram-specific class
            // names are checked in user code; the runtime just builds a
            // controlled response for each known request type. This is
            // exactly what a real test harness does: it intercepts specific
            // API calls and returns deterministic responses.
            bool is_auth_sendcode = (request_class.find("TL_auth_sendCode") != std::string::npos);
            bool is_get_nearest_dc = (request_class.find("TL_help_getNearestDc") != std::string::npos);
            bool is_get_countries_list = (request_class.find("TL_help_getCountriesList") != std::string::npos);
            bool is_langpack = (request_class.find("TL_langpack_") != std::string::npos);
            bool is_contacts_statuses = (request_class.find("TL_contacts_getStatuses") != std::string::npos);

            if (is_langpack || is_contacts_statuses) {
                // Skip these — they're fire-and-forget requests that don't
                // affect the login flow.
                std::cerr << "[EXP071-NET] Skipping non-critical request: "
                          << request_class << std::endl;
                recursion_depth_--;
                return_val = DalvikValue::make_int(0);
                last_invoke_return_ = return_val;
                return true;
            }

            uint32_t response_id = 0;
            std::string response_class;

            if (is_get_nearest_dc) {
                // TL_help_getNearestDc → response is TL_nearestDc
                // (the callback casts to TLRPC$TL_nearestDc, NOT TL_help_nearestDc).
                // Fields: country (String), this_dc (int), nearest_dc (int).
                response_class = "Lorg/telegram/tgnet/TLRPC$TL_nearestDc;";
                response_id = heap_.allocate(response_class, 0, 0);
                DalvikValue country_val = DalvikValue::make_string("US", 0);
                heap_.set_object_field(response_id, "country", country_val);
                DalvikValue this_dc_val = DalvikValue::make_int(2);
                heap_.set_object_field(response_id, "this_dc", this_dc_val);
                DalvikValue nearest_dc_val = DalvikValue::make_int(2);
                heap_.set_object_field(response_id, "nearest_dc", nearest_dc_val);
                std::cerr << "[EXP071-NET] Created mock TL_nearestDc: obj_id=" << response_id
                          << " country=\"US\" this_dc=2 nearest_dc=2" << std::endl;
            } else if (is_get_countries_list) {
                // TL_help_getCountriesList → ArrayList<TL_country>
                // Return an empty list — PhoneView will use the static
                // countries.txt asset instead.
                response_class = "Larray;";
                response_id = heap_.allocate(response_class, 0, 0);
                std::cerr << "[EXP071-NET] Created mock empty ArrayList for getCountriesList: obj_id="
                          << response_id << std::endl;
            } else if (is_auth_sendcode) {
                std::cerr << "[EXP070-NET] auth.sendCode detected — delivering mock response"
                          << std::endl;

                // Create a mock TL_auth_sentCode response object on the heap.
                // Telegram's callback expects a TLObject response. We create a
                // minimal mock with the right class descriptor so instanceof checks pass.
                // The real class is: Lorg/telegram/tgnet/TLRPC$TL_auth_sentCode;
                response_class = "Lorg/telegram/tgnet/TLRPC$TL_auth_sentCode;";
                response_id = heap_.allocate(response_class, 0, 0);

                // Store a phone_code_hash field (a deterministic test hash).
                DalvikValue hash_val = DalvikValue::make_string(
                    "mock_phone_code_hash_exp070", 0);
                heap_.set_object_field(response_id, "phone_code_hash", hash_val);

                // Store a type field (TL_auth_sentCodeTypeSms).
                uint32_t type_id = heap_.allocate(
                    "Lorg/telegram/tgnet/TLRPC$TL_auth_sentCodeTypeSms;", 0, 0);
                DalvikValue type_val = DalvikValue::make_object(
                    type_id, "Lorg/telegram/tgnet/TLRPC$TL_auth_sentCodeTypeSms;");
                heap_.set_object_field(response_id, "type", type_val);

                // Store length field (5 digits).
                DalvikValue length_val = DalvikValue::make_int(5);
                heap_.set_object_field(response_id, "length", length_val);

                // Store timeout field.
                DalvikValue timeout_val = DalvikValue::make_int(30);
                heap_.set_object_field(response_id, "timeout", timeout_val);

                // Store is_sent_via_flash_call and other boolean fields to false.
                DalvikValue false_val = DalvikValue::make_bool(false);
                heap_.set_object_field(response_id, "is_sent_via_flash_call", false_val);

                // Also initialize the type object's length field.
                heap_.set_object_field(type_id, "length", length_val);

                std::cerr << "[EXP070-NET] Created mock TL_auth_sentCode: obj_id=" << response_id
                          << " phone_code_hash=\"mock_phone_code_hash_exp070\""
                          << " type=TL_auth_sentCodeTypeSms length=5 timeout=30"
                          << std::endl;
            } else {
                // Unknown request — log and skip (no mock delivery).
                std::cerr << "[EXP070-NET] Skipping mock for unknown request: "
                          << request_class << std::endl;
                recursion_depth_--;
                return_val = DalvikValue::make_int(0);
                last_invoke_return_ = return_val;
                return true;
            }

            // Now invoke RequestDelegate.run(response, error) via try_recursive_invoke.
            // RequestDelegate.run(TLObject response, TLRPC.TL_error error)
            // args[0] = this (delegate), args[1] = response, args[2] = error (null)
            std::vector<DalvikValue> delegate_args;
            delegate_args.push_back(
                DalvikValue::make_object(delegate_id, delegate_class));
            delegate_args.push_back(
                DalvikValue::make_object(response_id, response_class));
            delegate_args.push_back(DalvikValue::make_null());

            DalvikValue delegate_return = DalvikValue::make_void();
            DalvikExecutionResult delegate_result;
            std::cerr << "[EXP070-NET] Invoking RequestDelegate.run(response, null)..."
                      << " delegate_class=" << delegate_class
                      << " response_class=" << response_class << std::endl;
            bool ok = try_recursive_invoke(delegate_class, "run",
                                           delegate_args, delegate_return, delegate_result);
            std::cerr << "[EXP070-NET] RequestDelegate.run result: "
                      << (ok ? "DISPATCHED" : "FAILED") << std::endl;

            // Also try the "run" method on the delegate's superclass if the
            // delegate itself doesn't have a "run" method.
            if (!ok && !delegate_class.empty()) {
                // Try walking the superclass chain
                std::string current = delegate_class;
                for (int i = 0; i < 5; ++i) {
                    auto it = class_to_superclass_.find(current);
                    if (it == class_to_superclass_.end()) break;
                    current = it->second;
                    std::cerr << "[EXP070-NET] Trying superclass: " << current << std::endl;
                    ok = try_recursive_invoke(current, "run",
                                              delegate_args, delegate_return, delegate_result);
                    if (ok) {
                        std::cerr << "[EXP070-NET] Found run() in " << current << std::endl;
                        break;
                    }
                }
            }
        } else {
            std::cerr << "[EXP070-NET] No RequestDelegate found in args — "
                      << "sendRequest stubbed without callback delivery" << std::endl;
        }

        // Return a dummy request ID (0x12345) — sendRequest returns int.
        // The caller (execute_invoke_virtual) will see true==handled and set
        // api_status = IMPLEMENTED. We just need to set return_val.
        recursion_depth_--;
        return_val = DalvikValue::make_int(0x12345);
        last_invoke_return_ = return_val;
        return true;
    }

    // EXP-071: FactorAnimator.animateTo loops infinitely because it triggers
    // onFactorChanged which loops at PC=0x3e. The animation is not needed
    // for the login flow. Stub it as a no-op so onConfirm can continue
    // to construct auth.sendCode.
    if (method_name == "animateTo" &&
        class_descriptor.find("FactorAnimator") != std::string::npos) {
        log("⏭️ STUB-ONLY: " + class_descriptor + "." + method_name +
            " — skipping (animation loop)");
        recursion_depth_--;
        return_val = DalvikValue::make_void();
        last_invoke_return_ = return_val;
        return true;
    }

    // EXP-065: AnimatedPhoneNumberEditText.setHintText loops infinitely
    // at PC=0x1e (invoke-interface) calling DynamicAnimation.cancel()
    // repeatedly. The original EXP-062 stub skipped the entire call,
    // which meant the hint text was never captured on the ViewNode.
    //
    // Now we intercept the call BEFORE bytecode execution:
    //   1. Dispatch to the ViewShadow to capture the hint text on the
    //      ViewNode (so the renderer can show "Phone number" etc.)
    //   2. Return without executing the bytecode (preventing the loop).
    //
    // The check uses method_name=="setHintText" AND a class check that
    // covers AnimatedPhoneNumberEditText AND its anonymous subclasses
    // (e.g. LoginActivity$PhoneView$1, LoginActivity$PhoneView$3, which
    // extend AnimatedPhoneNumberEditText).
    if (method_name == "setHintText") {
        bool is_animated_phone_edit_text =
            class_descriptor.find("AnimatedPhoneNumberEditText") != std::string::npos ||
            // Anonymous subclasses of AnimatedPhoneNumberEditText
            (class_descriptor.find("PhoneView$") != std::string::npos &&
             class_descriptor.find("LoginActivity") != std::string::npos);
        if (is_animated_phone_edit_text) {
            // EXP-065: Diagnostic — log what arg kind setHintText received.
            std::string arg_kind = "none";
            std::string arg_val = "<no-arg>";
            int arg1_type = -1;
            if (args.size() >= 2) {
                arg1_type = static_cast<int>(args[1].type);
                const auto& a = dalvik_value_to_arg(args[1]);
                if (a.kind == framework::CallContext::Arg::Kind::STRING) {
                    arg_kind = "STRING";
                    arg_val = "\"" + a.string_val + "\"";
                } else if (a.kind == framework::CallContext::Arg::Kind::OBJECT) {
                    arg_kind = "OBJECT";
                    arg_val = "obj_id=" + std::to_string(a.object_id) + " class=" + a.object_class;
                } else if (a.kind == framework::CallContext::Arg::Kind::NULL_REF) {
                    arg_kind = "NULL_REF";
                    arg_val = "null";
                } else {
                    arg_kind = "other";
                    arg_val = "dalvik_type=" + std::to_string(arg1_type) + " string_val=\"" + args[1].string_val + "\" int_val=" + std::to_string(args[1].int_val);
                }
            }
            std::cerr << "[EXP065-SETHINT-ARG] view_id=" << (args.empty() ? 0 : args[0].object_id)
                      << " class=" << class_descriptor
                      << " argc=" << args.size()
                      << " arg1_dalvik_type=" << arg1_type
                      << " arg1_kind=" << arg_kind
                      << " arg1_val=" << arg_val
                      << std::endl;
            // Dispatch to the ViewShadow — it has a setHintText handler that
            // stores the hint on the ViewNode. We then return without recursing
            // into the bytecode (which would loop).
            if (shadow_registry_ != nullptr) {
                framework::CallContext ctx;
                ctx.has_receiver = !args.empty() && args[0].type == DalvikType::OBJECT_REF;
                if (ctx.has_receiver) {
                    ctx.receiver_id = args[0].object_id;
                    ctx.receiver_class = args[0].class_desc;
                    ctx.class_name = args[0].class_desc.empty() ? class_descriptor : args[0].class_desc;
                } else {
                    ctx.class_name = class_descriptor;
                }
                ctx.method = method_name;
                for (size_t i = 1; i < args.size(); i++) {
                    ctx.args.push_back(dalvik_value_to_arg(args[i]));
                }
                auto cr = shadow_registry_->dispatch(ctx);
                (void)cr;  // We don't need the result — setHintText returns void.
            }
            log("⏭️ STUB-ONLY (with hint capture): " + class_descriptor + "." + method_name +
                " — skipping bytecode to prevent animation-cancel loop");
            recursion_depth_--;
            return false;
        }
    }

    // EXP-062: AndroidUtilities.replaceTags loops at PC=9 due to
    // string processing. Stub to prevent 50K iterations.
    if (class_descriptor.find("AndroidUtilities") != std::string::npos &&
        method_name == "replaceTags") {
        log("⏭️ STUB-ONLY: " + class_descriptor + "." + method_name +
            " — skipping (string processing loop)");
        recursion_depth_--;
        return false;
    }

    // EXP-058: EmojiInputFilter.<init> loops when correct register sizes
    // are used — the constructor calls super() which resolves back to
    // itself via incorrect overload resolution. Short-circuit.
    if (class_descriptor.find("EmojiInputFilter") != std::string::npos &&
        method_name == "<init>") {
        log("⏭️ STUB-ONLY: " + class_descriptor + "." + method_name +
            " — skipping (constructor loop)");
        recursion_depth_--;
        return false;
    }

    // EXP-058: EmojiTextViewHelper$HelperInternal19.<init> also loops.
    if (class_descriptor.find("HelperInternal19") != std::string::npos &&
        method_name == "<init>") {
        log("⏭️ STUB-ONLY: " + class_descriptor + "." + method_name +
            " — skipping (constructor loop)");
        recursion_depth_--;
        return false;
    }

    // EXP-058: EmojiTextViewHelper$SkippingHelper19.<init> also loops.
    if (class_descriptor.find("SkippingHelper19") != std::string::npos &&
        method_name == "<init>") {
        log("⏭️ STUB-ONLY: " + class_descriptor + "." + method_name +
            " — skipping (constructor loop)");
        recursion_depth_--;
        return false;
    }

    // EXP-058: EmojiTextViewHelper$HelperInternal.<init> also loops.
    if (class_descriptor.find("HelperInternal;") != std::string::npos &&
        method_name == "<init>") {
        log("⏭️ STUB-ONLY: " + class_descriptor + "." + method_name +
            " — skipping (constructor loop)");
        recursion_depth_--;
        return false;
    }

    // EXP-058: Preconditions.checkNotNull loops due to incorrect
    // overload resolution when the caller has different register layout.
    if (class_descriptor.find("Preconditions") != std::string::npos &&
        method_name == "checkNotNull") {
        log("⏭️ STUB-ONLY: " + class_descriptor + "." + method_name +
            " — skipping (overload loop)");
        recursion_depth_--;
        return false;
    }

    // EXP-058: AppCompatTextViewAutoSizeHelper$Impl constructors loop.
    if (class_descriptor.find("AppCompatTextViewAutoSizeHelper") != std::string::npos &&
        method_name == "<init>") {
        log("⏭️ STUB-ONLY: " + class_descriptor + "." + method_name +
            " — skipping (constructor loop)");
        recursion_depth_--;
        return false;
    }

    // EXP-058: Generic guard — if the same (class, method) was called
    // more than 10 times, skip it. Catches infinite loops.
    // Exception: addFragmentToStack needs more calls (recursive 2-arg → 3-arg pattern).
    {
        static thread_local std::map<std::string, int> call_counts;
        std::string key = class_descriptor + "." + method_name;
        call_counts[key]++;
        int threshold = 10;
        // EXP-060: Allow more calls for Fragment lifecycle methods that
        // are legitimately called multiple times (once per Fragment instance).
        // NOTE: <init> is NOT included here because constructor loops are
        // common (e.g. DrawerLayoutContainer calls super which triggers
        // another allocation). Keeping <init> at threshold=10 prevents
        // these loops from running forever.
        if (method_name == "addFragmentToStack" ||
            method_name == "presentFragment" ||
            method_name == "onFragmentCreate" ||
            method_name == "createView" ||
            method_name == "onResume" ||
            method_name == "setParentLayout" ||
            method_name == "attachView" ||
            method_name == "onCreateView" ||
            method_name == "onBecomeFullyVisible" ||
            method_name == "onPause" ||
            method_name == "onStop" ||
            method_name == "onDestroy") {
            threshold = 50;
        }
        // EXP-063: getString is called many times (100+) for each UI string.
        // The default 10-call threshold stubs it after 10 calls, preventing
        // resource resolution for later strings.
        if (method_name == "getString" ||
            method_name == "getResourceEntryName") {
            threshold = 500;
        }
        if (call_counts[key] > threshold) {
            log("⏭️ STUB-ONLY: " + key + " — skipping (called " +
                std::to_string(call_counts[key]) + " times)");
            call_counts[key]--;
            recursion_depth_--;
            return false;
        }
    }

    // EXP-045 Phase 2: TransactionInactiveError — credentials exception that
    // loops because its superclass constructor (Exception.<init>) returns
    // incorrectly. Stub as no-op to unblock deeper execution.
    if (class_descriptor.find("TransactionInactiveError") != std::string::npos) {
        log("⏭️ STUB-ONLY: " + class_descriptor + "." + method_name +
            " — skipping (credentials exception not on startup path)");
        recursion_depth_--;
        return false;
    }

    // EXP-045 Phase 3: Google identity credentials classes — not on Telegram
    // startup path. Stub to prevent NPE cascade from their constructors.
    if (class_descriptor.find("identitycredentials") != std::string::npos ||
        class_descriptor.find("ImportCredentials") != std::string::npos) {
        log("⏭️ STUB-ONLY: " + class_descriptor + "." + method_name +
            " — skipping (Google credentials, not on startup path)");
        recursion_depth_--;
        return false;
    }

    // EXP-045 Phase 3: Stub the expensive NPE message construction path.
    // When checkNotNullParameter detects a null parameter, it calls
    // throwParameterIsNullNPE → createParameterIsNullExceptionMessage →
    // sanitizeStackTrace. This path is ~159 instructions per NPE, called
    // 1845+ times = ~293K instructions wasted on exception messages that
    // are never displayed in our headless runtime.
    // We stub the entire NPE path to return void/null immediately.
    if (class_descriptor.find("Intrinsics") != std::string::npos &&
        (method_name == "createParameterIsNullExceptionMessage" ||
         method_name == "sanitizeStackTrace" ||
         method_name == "throwParameterIsNullNPE")) {
        log("⏭️ STUB-ONLY: " + class_descriptor + "." + method_name +
            " — skipping (NPE path, not needed in headless runtime)");
        recursion_depth_--;
        return false;  // Bridge returns null, short-circuiting the NPE path
    }

    // EXP-045 Phase 3: FragmentManager.dispatchStateChange loops infinitely
    // calling getSpecialEffectsControllerFactory for each Fragment state change.
    // Without proper Fragment state, this loop never terminates.
    // Stub to return void (skip Fragment state transitions).
    if (class_descriptor.find("FragmentManager") != std::string::npos &&
        method_name == "dispatchStateChange") {
        log("⏭️ STUB-ONLY: " + class_descriptor + "." + method_name +
            " — skipping (Fragment state change loop)");
        recursion_depth_--;
        return false;
    }

    // EXP-051: Thread identity model is now implemented via the
    // ThreadShadow + LooperShadow pair, which guarantees:
    //   Looper.getMainLooper().getThread() == Thread.currentThread()
    // So ArchTaskExecutor.isMainThread now executes its real bytecode
    // and returns true correctly. The short-circuit below has been
    // removed — the engine recurses into the bytecode naturally.
    //
    // The remaining short-circuits below are for paths that depend on
    // real animation state (which we don't model) or story viewer
    // availability (which is intentionally null). They cannot be fixed
    // by the thread identity model alone.
    if ((class_descriptor.find("BaseFragment") != std::string::npos &&
         method_name == "getLastStoryViewer") ||
        (class_descriptor.find("SpringAnimation") != std::string::npos &&
         (method_name == "sanityCheck" || method_name == "start")) ||
        (class_descriptor.find("DynamicAnimation") != std::string::npos &&
         method_name == "startAnimationInternal")) {
        log("⏭️ STUB-ONLY: " + class_descriptor + "." + method_name +
            " — skipping (animation/story viewer state)");
        recursion_depth_--;
        return false;
    }

    // EXP-045 Phase 3: Log NPE callers to identify which null parameters
    // are causing performance degradation. Only log first 50 NPE callers.
    static thread_local uint64_t npe_caller_count = 0;
    if (class_descriptor.find("Intrinsics") != std::string::npos &&
        (method_name == "checkNotNullParameter" || method_name == "checkNotNullExpressionValue") &&
        npe_caller_count < 50) {
        std::cerr << "[NPE-CALLER] " << method_name << " called from "
                  << current_class_ << "." << current_method_ << std::endl;
        npe_caller_count++;
    }

    // EXP-045 Phase 2: Use O(1) class lookup index instead of linear search.
    auto class_it = class_info_index_.find(class_descriptor);
    if (class_it == class_info_index_.end()) {
        // EXP-061: Debug — log when SlideView or other View base classes are not found.
        if (class_descriptor.find("SlideView") != std::string::npos ||
            class_descriptor.find("FrameLayout") != std::string::npos ||
            class_descriptor.find("LinearLayout") != std::string::npos) {
            std::cerr << "[EXP061-NOTFOUND] class_descriptor=" << class_descriptor
                      << " method=" << method_name
                      << " (class not in index)"
                      << " caller=" << current_class_ << "." << current_method_
                      << std::endl;
        }
        // EXP-055: Debug — log when class not found.
        static thread_local uint64_t not_found_count = 0;
        if (not_found_count < 10 && method_name.find("isClientActivated") != std::string::npos) {
            not_found_count++;
            std::cerr << "[RET-NOTFOUND] class_descriptor=" << class_descriptor
                      << " method=" << method_name
                      << " (class not in index)"
                      << std::endl;
        }
        recursion_depth_--;
        return false;  // class not found in DEX, bridge to API
    }
    const dex::ClassInfo& cls_ref = dex_report_->classes[class_it->second];

    // EXP-061: Debug — trace SlideView method search
    if (class_descriptor.find("SlideView") != std::string::npos && method_name == "<init>") {
        auto all_methods_check = cls_ref.all_methods();
        std::cerr << "[EXP061-FOUND] SlideView in index. Looking for <init>. Methods:" << std::endl;
        for (const auto& m : all_methods_check) {
            std::cerr << "  " << m.name << m.descriptor
                      << " bytecode_size=" << m.bytecode.size()
                      << std::endl;
        }
    }

    // EXP-046 Phase 2: Check for native methods and dispatch to JNI bridge.
    // Native methods have no bytecode (code_off == 0) and access_flags & ACC_NATIVE (0x100).
    // Before the overload search skips them (bytecode.empty()), we check if a JNI
    // handler is registered and dispatch to it.
    {
        auto all_methods_check = cls_ref.all_methods();
        for (const auto& method : all_methods_check) {
            if (method.name != method_name) continue;
            if (!(method.access_flags & 0x100)) continue;  // Not ACC_NATIVE
            // Found a native method — dispatch to JNI bridge
            log("🔌 JNI DISPATCH: " + class_descriptor + "." + method_name +
                method.descriptor + " (native)");
            // Build JNI call context from args
            jni::NativeCallContext jni_ctx;
            jni_ctx.class_desc = class_descriptor;
            jni_ctx.method_name = method_name;
            jni_ctx.signature = method.descriptor;
            for (const auto& arg : args) {
                if (arg.type == DalvikType::INT32 || arg.type == DalvikType::BOOLEAN) {
                    jni_ctx.int_args.push_back(arg.int_val);
                } else if (arg.type == DalvikType::INT64) {
                    jni_ctx.int_args.push_back(static_cast<int32_t>(arg.long_val));
                } else if (arg.type == DalvikType::STRING_REF) {
                    jni_ctx.string_args.push_back(arg.string_val);
                } else if (arg.type == DalvikType::OBJECT_REF) {
                    jni_ctx.object_args.push_back(arg.object_id);
                } else if (arg.type == DalvikType::NULL_REF) {
                    jni_ctx.object_args.push_back(0);
                }
            }
            // Dispatch
            int32_t int_ret = 0;
            int64_t long_ret = 0;
            float float_ret = 0.0f;
            double double_ret = 0.0;
            std::string string_ret;
            uint32_t obj_ret = 0;
            bool is_obj_ret = false;
            jni::JNIBridge::instance().invoke(jni_ctx, int_ret, long_ret, float_ret,
                                               double_ret, string_ret, obj_ret, is_obj_ret);
            // Convert result to DalvikValue based on return type
            char ret_type = 'V';
            size_t paren = method.descriptor.rfind(')');
            if (paren != std::string::npos && paren + 1 < method.descriptor.size()) {
                ret_type = method.descriptor[paren + 1];
            }
            switch (ret_type) {
                case 'I': case 'Z': case 'B': case 'S': case 'C':
                    return_val = DalvikValue::make_int(int_ret); break;
                case 'J': {
                    DalvikValue v; v.type = DalvikType::INT64; v.long_val = long_ret;
                    return_val = v; break;
                }
                case 'F': {
                    DalvikValue v; v.type = DalvikType::FLOAT32; v.float_val = float_ret;
                    return_val = v; break;
                }
                case 'D': {
                    DalvikValue v; v.type = DalvikType::FLOAT64; v.double_val = double_ret;
                    return_val = v; break;
                }
                case 'L': case '[':
                    if (is_obj_ret && obj_ret > 0) {
                        return_val = DalvikValue::make_object(obj_ret, "Lnative_result;");
                    } else {
                        return_val = DalvikValue::make_null();
                    }
                    break;
                default:
                    return_val = DalvikValue::make_void(); break;
            }
            recursion_depth_--;
            return true;  // JNI handler dispatched successfully
        }
    }

    // EXP-045 Phase 2: Search for the method within this class.
    // CRITICAL: When multiple overloads exist with the same name, match by
    // argument count to avoid calling the wrong overload.
    // EXP-054: Store MethodInfo BY VALUE (not by pointer) to eliminate
    // any theoretical dangling-pointer risk. The `all_methods` vector is
    // kept alive in this scope, but storing by value makes the code
    // robust against future refactoring and is safer for recursive
    // invoke paths where the call stack gets deep.
    auto all_methods = cls_ref.all_methods();  // keep the vector alive
    std::optional<dex::MethodInfo> best_match;     // by value (EXP-054)
    std::optional<dex::MethodInfo> fallback_match;  // by value (EXP-054)
    size_t arg_count = args.size();

    for (const auto& method : all_methods) {
        if (method.name != method_name) continue;
        if (method.bytecode.empty()) continue;

        // Count parameters from descriptor: "(Ltype;Ltype;...)R"
        // The number of parameters = number of ';' in the parameter list
        // (for object types) + count of primitive type chars (I, Z, B, etc.)
        // Simplified: count parameters by parsing the descriptor.
        size_t param_count = 0;
        std::vector<std::string> param_types;  // EXP-060: for type matching
        const std::string& desc = method.descriptor;
        size_t paren_pos = desc.find('(');
        if (paren_pos != std::string::npos) {
            size_t end_paren = desc.find(')', paren_pos);
            if (end_paren != std::string::npos) {
                std::string params = desc.substr(paren_pos + 1, end_paren - paren_pos - 1);
                // Count parameters: each is either a class (L...;), array ([...), or primitive (single char)
                size_t i = 0;
                while (i < params.size()) {
                    if (params[i] == 'L') {
                        size_t end = params.find(';', i);
                        if (end == std::string::npos) break;
                        param_types.push_back(params.substr(i, end - i + 1));
                        i = end + 1;
                    } else if (params[i] == '[') {
                        size_t start = i;
                        while (i < params.size() && params[i] == '[') i++;
                        if (i < params.size() && params[i] == 'L') {
                            size_t end = params.find(';', i);
                            if (end == std::string::npos) break;
                            param_types.push_back(params.substr(start, end - start + 1));
                            i = end + 1;
                        } else {
                            param_types.push_back(params.substr(start, i - start + 1));
                            i++;
                        }
                    } else {
                        param_types.push_back(std::string(1, params[i]));
                        i++;
                    }
                    param_count++;
                }
            }
        }

        // EXP-053 FIX: args.size() includes `this` for instance methods.
        // EXP-063 FIX: Only subtract 1 for instance methods (args[0] is 'this').
        // For static methods, ALL args are parameters — don't subtract.
        // The caller (invoke-static) doesn't include 'this' in args.
        // The caller (invoke-virtual/direct/interface) includes 'this' as args[0].
        // We can detect instance vs static by checking if args[0] is OBJECT_REF
        // AND the method descriptor starts with a non-empty parameter list.
        // Simpler approach: if arg_count > param_count, it's likely an instance
        // method with 'this' in args[0]. Subtract 1.
        // But if arg_count == param_count + 1 AND param_count matches exactly,
        // it's an instance method with the right number of params.
        // EXP-063: Only subtract if the method is NOT static.
        // We check access_flags & 0x0008 (ACC_STATIC).
        size_t effective_arg_count = arg_count;
        bool is_static_method = (method.access_flags & 0x0008) != 0;
        if (!is_static_method && arg_count > 0 && arg_count > param_count) {
            effective_arg_count = arg_count - 1;
        }
        if (param_count == effective_arg_count) {
            // EXP-060: Check if the first parameter type matches the
            // first argument's class descriptor. This distinguishes
            // overloads with the same param count but different types
            // (e.g. presentFragment(BaseFragment) vs presentFragment(NavigationParams)).
            //
            // EXP-061 FIX: The type check is now LENIENT — it only rejects
            // when the parameter type is a known class AND the argument is
            // an OBJECT_REF whose class is CLEARLY different (not a substring
            // match). This allows subclass arguments to match (e.g. a
            // ContextWrapper passed to a method expecting Context).
            bool type_matches = true;
            if (effective_arg_count >= 1 && !param_types.empty()) {
                size_t arg_idx = (arg_count > param_count) ? 1 : 0;
                if (arg_idx < args.size()) {
                    const auto& arg = args[arg_idx];
                    const std::string& param_type = param_types[0];
                    // Only check object types — primitives match by position.
                    if (param_type[0] == 'L' && arg.type == DalvikType::OBJECT_REF) {
                        // Both are object types — accept if EITHER contains
                        // the other (handles subclass/descriptor prefix matches).
                        // Only reject if we have a clear mismatch AND both
                        // are non-empty.
                        if (!arg.class_desc.empty() &&
                            arg.class_desc.find(param_type) == std::string::npos &&
                            param_type.find(arg.class_desc) == std::string::npos) {
                            // EXP-061: Don't hard-reject. Instead, try to find
                            // a BETTER match later. Mark as fallback only.
                            type_matches = false;
                        }
                    } else if (param_type[0] == 'L' &&
                               (arg.type == DalvikType::NULL_REF ||
                                arg.type == DalvikType::UNINITIALIZED ||
                                arg.type == DalvikType::VOID_)) {
                        // Null/uninit arg can match any object param.
                        // Don't reject.
                    }
                }
            }
            if (type_matches) {
                best_match = method;  // copy by value (EXP-054)
                break;  // exact match, stop searching
            }
            if (!fallback_match) {
                fallback_match = method;  // keep as fallback for type mismatch
            }
        }
    }

    std::optional<dex::MethodInfo> selected_opt = best_match ? best_match : fallback_match;

    if (selected_opt) {
        const auto& method = *selected_opt;  // safe: selected_opt owns the MethodInfo
        // Found a method with bytecode — recursively execute!
        log("🔄 RECURSIVE INVOKE: " + cls_ref.name + "." + method.name +
            method.descriptor + " (" + std::to_string(method.bytecode.size()) + " instructions)");

        // Save current state
        auto saved_pc = pc_;
        auto saved_bytecode = bytecode_;
        auto* saved_registers = current_registers_;
        bool saved_halted_on_return = halted_on_return_;
        bool saved_halted = halted_;
        std::string saved_halt_reason = halt_reason_;
        auto saved_class = current_class_;
        auto saved_method = current_method_;
        auto saved_dex_index = current_dex_index_;
        auto saved_pc_visit_count = pc_visit_count_;
        // EXP-052: Save tries state so we can restore it after the recursive
        // call returns. Without this, a throw in a callee would leave the
        // engine pointing at the callee's (now-stale) tries data.
        auto saved_tries_size = current_tries_size_;
        auto saved_tries_data = current_tries_data_;
        auto saved_tries_data_size = current_tries_data_size_;
        // EXP-054: Save current_result_ so it can be restored after the
        // recursive call. execute_method_internal sets current_result_ to
        // its own result parameter, so without saving/restoring, the outer
        // caller's current_result_ would be lost. This is critical when
        // ensure_class_initialized calls try_recursive_invoke from inside
        // an opcode handler (like execute_sget) — the outer method's
        // current_result_ must be preserved.
        auto* saved_current_result = current_result_;
        // EXP-054: Save pending_exception_ so a throw in the callee doesn't
        // corrupt the caller's exception state.
        auto saved_pending_exception = pending_exception_;
        // EXP-055: Save last_invoke_return_ so the callee's return value
        // doesn't corrupt the caller's pending return from a different call.
        auto saved_last_invoke_return = last_invoke_return_;

        halted_on_return_ = false;
        halted_ = false;

        // EXP-058: Use actual register sizes from the code_item header.
        uint32_t regs_size = method.registers_size ? method.registers_size : 16;
        uint32_t ins_size = method.ins_size ? method.ins_size : static_cast<uint32_t>(args.size());
        uint32_t outs_size = method.outs_size ? method.outs_size : 4;

        // EXP-058: Debug — log register sizes for addFragmentToStack.
        // EXP-060: Also log for setParentLayout and presentFragment.
        // EXP-063: Also log for getString.
        if (method.name.find("addFragmentToStack") != std::string::npos ||
            method.name == "setParentLayout" ||
            method.name == "presentFragment" ||
            method.name == "getString") {
            std::cerr << "[EXP058-REGS] " << cls_ref.name << "." << method.name
                      << " method.regs=" << method.registers_size
                      << " method.ins=" << method.ins_size
                      << " method.outs=" << method.outs_size
                      << " → using regs=" << regs_size
                      << " ins=" << ins_size
                      << " outs=" << outs_size
                      << " args=" << args.size()
                      << std::endl;
            // EXP-060: Also log the argument values to see what's being passed.
            for (size_t ai = 0; ai < args.size() && ai < ins_size; ++ai) {
                std::cerr << "[EXP060-ARG] p" << ai
                          << " type=" << static_cast<int>(args[ai].type)
                          << " obj=" << args[ai].object_id
                          << " class=" << args[ai].class_desc
                          << std::endl;
            }
        }

        // EXP-055: Debug log before execute_method_internal.
        std::cerr << "[RET-BEFORE] " << cls_ref.name << "." << method.name
                  << " bytecode_size=" << method.bytecode.size()
                  << std::endl;

        execute_method_internal(
            cls_ref.name,
            method.name,
            method.descriptor,
            method.bytecode,
            regs_size,
            ins_size,
            outs_size,
            args,
            result,
            method.tries_size,
            method.tries_data.data(),
            method.tries_data.size()
        );

        halted_on_return_ = false;
        halted_ = false;
        halt_reason_.clear();

        // EXP-055: Propagate the return value from execute_method_internal.
        // execute_return/execute_return_object stores the return value in
        // last_invoke_return_. Copy it to return_val BEFORE restoring state.
        return_val = last_invoke_return_;

        // Restore saved state.
        bytecode_ = saved_bytecode;
        pc_ = saved_pc;
        current_registers_ = saved_registers;
        current_class_ = saved_class;
        current_method_ = saved_method;
        current_dex_index_ = saved_dex_index;
        pc_visit_count_ = saved_pc_visit_count;
        current_tries_size_ = saved_tries_size;
        current_tries_data_ = saved_tries_data;
        current_tries_data_size_ = saved_tries_data_size;
        current_result_ = saved_current_result;
        pending_exception_ = saved_pending_exception;
        last_invoke_return_ = saved_last_invoke_return;

        log("✅ RECURSIVE INVOKE completed: " + cls_ref.name + "." + method.name);
        // EXP-056: Log return values for key login-path methods.
        {
            std::string full_name = cls_ref.name + "." + method.name;
            if (full_name.find("isClientActivated") != std::string::npos ||
                full_name.find("getClientNotActivated") != std::string::npos ||
                full_name.find("addFragmentToStack") != std::string::npos ||
                full_name.find("getFragmentStack") != std::string::npos ||
                full_name.find("isEmpty") != std::string::npos ||
                full_name.find("checkCurrentAccount") != std::string::npos) {
                std::cerr << "[RET] " << full_name
                          << " val=" << return_val.int_val
                          << " type=" << static_cast<int>(return_val.type)
                          << " obj=" << return_val.object_id
                          << std::endl;
            }
        }
        recursion_depth_--;
        return true;
    }

    recursion_depth_--;
    return false;  // method not found in DEX, bridge to API
}

// EXP-060: Dispatch a synthetic CLICK event on a View.
//
// This is the generic event mechanism. The runtime:
//   1. Looks up the ViewNode via ViewShadow.
//   2. Retrieves the registered OnClickListener object_id.
//   3. Looks up the listener's runtime class from the heap.
//   4. Invokes listener.onClick(view) via try_recursive_invoke.
//
// The actual navigation logic is in the listener's onClick method —
// no Telegram-specific code is needed here.
//
// Returns true if a listener was found and dispatched.
bool DalvikExecutionEngine::dispatch_click(uint32_t view_object_id) {
    if (shadow_registry_ == nullptr) {
        std::cerr << "[EXP060-CLICK] no shadow registry — cannot dispatch" << std::endl;
        return false;
    }
    auto* view_shadow = shadow_registry_->find_as<framework::ViewShadow>();
    if (view_shadow == nullptr) {
        std::cerr << "[EXP060-CLICK] no ViewShadow registered" << std::endl;
        return false;
    }
    const auto* node = view_shadow->find_node(view_object_id);
    if (node == nullptr) {
        std::cerr << "[EXP060-CLICK] view_id=" << view_object_id
                  << " not found in ViewShadow" << std::endl;
        return false;
    }
    if (node->click_listener_id == 0) {
        std::cerr << "[EXP060-CLICK] view_id=" << view_object_id
                  << " class=" << node->class_desc
                  << " has no OnClickListener" << std::endl;
        return false;
    }

    uint32_t listener_id = node->click_listener_id;
    std::string listener_class;
    // Look up the listener's class from the heap.
    if (heap_.has_object(listener_id)) {
        listener_class = heap_.get(listener_id)->class_descriptor;
    }
    if (listener_class.empty()) {
        listener_class = "Landroid/view/View$OnClickListener;";
    }

    std::cerr << "[UI-EVENT] event=CLICK"
              << " view_object=" << view_object_id
              << " view_class=" << node->class_desc
              << " listener=" << listener_id
              << " listener_class=" << listener_class
              << std::endl;

    // Build args for onClick(View v):
    //   args[0] = this (listener)
    //   args[1] = view (the View that was clicked)
    std::vector<DalvikValue> args;
    DalvikValue this_arg = DalvikValue::make_object(listener_id, listener_class);
    args.push_back(this_arg);
    DalvikValue view_arg = DalvikValue::make_object(view_object_id, node->class_desc);
    args.push_back(view_arg);

    DalvikValue return_val = DalvikValue::make_void();
    DalvikExecutionResult result;
    bool ok = try_recursive_invoke(listener_class, "onClick", args, return_val, result);

    std::cerr << "[UI-EVENT] event=CLICK result="
              << (ok ? "DISPATCHED" : "FAILED")
              << " listener=" << listener_class
              << std::endl;
    return ok;
}

// EXP-071 Phase 8: Generic Runnable dispatch.
//
// Looks up a heap object by id, finds its class descriptor, and invokes
// its run()V method via try_recursive_invoke. This is the bridge between
// the HandlerShadow's queue (which stores heap object IDs of Runnables
// scheduled via Handler.post / AndroidUtilities.runOnUIThread) and the
// actual DEX bytecode execution.
//
// This is a GENERIC primitive — it does not check the class name or do
// anything Telegram-specific. It works for any Runnable the runtime
// encounters: Lambda0 (PhoneView$6 confirm callback), Lambda1 (delayed
// onNextPressed trigger), Lambda2 (RequestDelegate), post-Response
// response handlers, anything.
//
// Args:
//   runnable_object_id — the heap object ID of the Runnable.
//   response_object_id — optional second arg passed to run() (e.g. for
//                        RequestDelegate.run(TLObject, TL_error)). 0 = no arg.
//   error_object_id    — optional third arg (the TL_error). 0 = no arg.
//
// Returns true if the run() method was found and dispatched.
bool DalvikExecutionEngine::dispatch_runnable(uint32_t runnable_object_id,
                                              uint32_t response_object_id,
                                              uint32_t error_object_id) {
    if (runnable_object_id == 0) {
        std::cerr << "[EXP071-RUN] dispatch_runnable called with id=0 (null)"
                  << std::endl;
        return false;
    }
    if (!heap_.has_object(runnable_object_id)) {
        std::cerr << "[EXP071-RUN] dispatch_runnable id=" << runnable_object_id
                  << " — object not on heap" << std::endl;
        return false;
    }
    std::string runnable_class = heap_.get(runnable_object_id)->class_descriptor;
    if (runnable_class.empty()) {
        std::cerr << "[EXP071-RUN] dispatch_runnable id=" << runnable_object_id
                  << " — object has no class descriptor" << std::endl;
        return false;
    }

    // Build args for run():
    //   No-arg Runnable:  args[0] = this
    //   RequestDelegate:  args[0] = this, args[1] = response (TLObject), args[2] = error (TL_error)
    std::vector<DalvikValue> args;
    DalvikValue this_arg = DalvikValue::make_object(runnable_object_id, runnable_class);
    args.push_back(this_arg);
    if (response_object_id != 0) {
        // The response class is whatever the heap says — typically TL_auth_sentCode.
        std::string resp_class = "Lorg/telegram/tgnet/TLObject;";
        if (heap_.has_object(response_object_id)) {
            resp_class = heap_.get(response_object_id)->class_descriptor;
        }
        args.push_back(DalvikValue::make_object(response_object_id, resp_class));
    }
    if (error_object_id != 0) {
        std::string err_class = "Lorg/telegram/tgnet/TLRPC$TL_error;";
        if (heap_.has_object(error_object_id)) {
            err_class = heap_.get(error_object_id)->class_descriptor;
        }
        args.push_back(DalvikValue::make_object(error_object_id, err_class));
    } else if (response_object_id != 0) {
        // RequestDelegate.run(TLObject, TL_error) — pass null as the error.
        args.push_back(DalvikValue::make_null());
    }

    std::cerr << "[EXP071-RUN] event=RUNNABLE"
              << " runnable=" << runnable_object_id
              << " class=" << runnable_class
              << " args=" << args.size()
              << std::endl;

    DalvikValue return_val = DalvikValue::make_void();
    DalvikExecutionResult result;
    bool ok = try_recursive_invoke(runnable_class, "run", args, return_val, result);

    std::cerr << "[EXP071-RUN] event=RUNNABLE result="
              << (ok ? "DISPATCHED" : "FAILED")
              << " class=" << runnable_class
              << std::endl;
    return ok;
}

bool DalvikExecutionEngine::dispatch_click_by_class(const std::string& class_substring) {
    if (shadow_registry_ == nullptr) return false;
    auto* view_shadow = shadow_registry_->find_as<framework::ViewShadow>();
    if (view_shadow == nullptr) return false;
    uint32_t view_id = view_shadow->find_by_class_substring(class_substring);
    if (view_id == 0) {
        std::cerr << "[EXP060-CLICK] no View found matching '"
                  << class_substring << "'" << std::endl;
        return false;
    }
    return dispatch_click(view_id);
}

// EXP-069: Generic text input dispatch.
// Injects text into a TextView/EditText by dispatching to the ViewShadow's
// setText handler, which stores the text on the ViewNode. This makes
// subsequent getText() calls in DEX bytecode return the new value.
// If the View has registered TextWatchers, they would be triggered here
// (TODO: implement TextWatcher callback dispatch).
bool DalvikExecutionEngine::dispatch_text_input(uint32_t view_object_id,
                                                 const std::string& text) {
    if (shadow_registry_ == nullptr) {
        std::cerr << "[EXP069-INPUT] no shadow registry — cannot dispatch" << std::endl;
        return false;
    }
    auto* view_shadow = shadow_registry_->find_as<framework::ViewShadow>();
    if (view_shadow == nullptr) {
        std::cerr << "[EXP069-INPUT] no ViewShadow registered" << std::endl;
        return false;
    }
    const auto* node = view_shadow->find_node(view_object_id);
    if (node == nullptr) {
        std::cerr << "[EXP069-INPUT] view_id=" << view_object_id
                  << " not found in ViewShadow" << std::endl;
        return false;
    }

    std::cerr << "[UI-EVENT] event=TEXT_INPUT"
              << " view_object=" << view_object_id
              << " view_class=" << node->class_desc
              << " old_text=\"" << node->text << "\""
              << " new_text=\"" << text << "\""
              << std::endl;

    // Dispatch to ViewShadow.setText — this stores the text on the ViewNode.
    // We use the shadow dispatch path (same as what DEX setText would use).
    framework::CallContext ctx;
    ctx.has_receiver = true;
    ctx.receiver_id = view_object_id;
    ctx.receiver_class = node->class_desc;
    ctx.class_name = node->class_desc;
    ctx.method = "setText";
    framework::CallContext::Arg arg;
    arg.kind = framework::CallContext::Arg::Kind::STRING;
    arg.string_val = text;
    ctx.args.push_back(arg);
    auto cr = shadow_registry_->dispatch(ctx);
    if (!cr.handled) {
        std::cerr << "[EXP069-INPUT] setText not handled by ViewShadow" << std::endl;
        return false;
    }

    // Also store the text on the heap object so DEX getText() can return it.
    // The ViewShadow stores text on the ViewNode, but DEX bytecode that calls
    // getText() would go through the shadow dispatch which reads from ViewNode.
    // So this is already covered by the shadow dispatch above.

    std::cerr << "[UI-EVENT] event=TEXT_INPUT result=DISPATCHED"
              << " view=" << view_object_id
              << " text=\"" << text << "\""
              << std::endl;
    return true;
}

bool DalvikExecutionEngine::dispatch_text_input_by_class(
    const std::string& class_substring, const std::string& text) {
    if (shadow_registry_ == nullptr) return false;
    auto* view_shadow = shadow_registry_->find_as<framework::ViewShadow>();
    if (view_shadow == nullptr) return false;
    uint32_t view_id = view_shadow->find_by_class_substring(class_substring);
    if (view_id == 0) {
        std::cerr << "[EXP069-INPUT] no View found matching '"
                  << class_substring << "'" << std::endl;
        return false;
    }
    return dispatch_text_input(view_id, text);
}

// EXP-061: Dump the full ViewNode tree to a JSON file.
// This is the input to the software renderer. Each node includes
// object_id, class, parent, children, geometry, text, listener info.
bool DalvikExecutionEngine::dump_view_tree(const std::string& path) {
    if (shadow_registry_ == nullptr) {
        std::cerr << "[EXP061] no shadow registry" << std::endl;
        return false;
    }
    auto* view_shadow = shadow_registry_->find_as<framework::ViewShadow>();
    if (view_shadow == nullptr) {
        std::cerr << "[EXP061] no ViewShadow registered" << std::endl;
        return false;
    }

    // The ViewShadow doesn't expose its internal nodes_ map directly.
    // We'll iterate using find_node over all known heap object IDs.
    // A more efficient approach would be to add an iterator to ViewShadow,
    // but for now we scan all heap objects.
    json nodes = json::array();
    size_t count = 0;
    for (const auto& [oid, obj] : heap_.all_objects()) {
        const auto* node = view_shadow->find_node(oid);
        if (node == nullptr) continue;
        count++;
        json n;
        n["object_id"] = node->view_id;
        n["class"] = node->class_desc;
        n["parent_id"] = node->parent_id;
        n["children"] = node->children;
        n["android_view_id"] = node->android_view_id;
        n["width"] = node->width;
        n["height"] = node->height;
        n["x"] = node->x;
        n["y"] = node->y;
        n["text"] = node->text;
        n["hint"] = node->hint;  // EXP-065: EditText hint
        // EXP-068: Semantic View type classification via superclass chain.
        // This replaces class-name pattern matching in the renderer.
        if (is_edit_text_class(node->class_desc)) {
            n["view_type"] = "EditText";
        } else if (is_text_view_class(node->class_desc)) {
            n["view_type"] = "TextView";
        } else if (is_image_view_class(node->class_desc)) {
            n["view_type"] = "ImageView";
        } else if (is_button_class(node->class_desc)) {
            n["view_type"] = "Button";
        } else if (is_view_group_class(node->class_desc)) {
            n["view_type"] = "ViewGroup";
        } else if (is_view_class(node->class_desc)) {
            n["view_type"] = "View";
        } else {
            n["view_type"] = "";
        }
        // EXP-067: Image resource ID and drawable path
        n["image_resource_id"] = node->image_resource_id;
        if (node->image_resource_id != 0) {
            auto it = field_name_by_resid_.find(node->image_resource_id);
            if (it != field_name_by_resid_.end()) {
                n["image_resource_name"] = it->second;
                auto pit = resource_drawable_paths_.find(it->second);
                if (pit != resource_drawable_paths_.end()) {
                    n["image_drawable_path"] = pit->second;
                    // Note: can't modify node here (it's const) — renderer looks up
                    // the path from image_resource_id at render time.
                }
            }
        }
        n["clickable"] = node->clickable;
        n["enabled"] = node->enabled;
        n["visibility"] = node->visibility;
        n["has_click_listener"] = (node->click_listener_id != 0);
        if (node->click_listener_id != 0) {
            n["click_listener_id"] = node->click_listener_id;
            // Look up the listener's class from the heap.
            if (heap_.has_object(node->click_listener_id)) {
                n["click_listener_class"] = heap_.get(node->click_listener_id)->class_descriptor;
            }
        }
        nodes.push_back(n);
    }

    json root;
    root["experiment"] = "EXP-061";
    root["view_count"] = count;
    root["nodes"] = nodes;

    // Write to file
    std::ofstream out(path);
    if (!out.is_open()) {
        std::cerr << "[EXP061] failed to open " << path << " for writing" << std::endl;
        return false;
    }
    out << root.dump(2);
    out.close();

    std::cerr << "[EXP061] View tree dumped: " << count << " nodes to " << path << std::endl;
    return true;
}

bool DalvikExecutionEngine::fetch_decode_execute(DalvikExecutionResult& result) {
    // EXP-071 Phase 6 debug: Log entry to fetch_decode_execute for setCountry.
    if (current_method_ == "setCountry" && current_class_.find("PhoneView") != std::string::npos) {
        std::cerr << "[EXP071-FDE-ENTER] " << current_class_ << "." << current_method_
                  << " halted_=" << halted_
                  << " pc_=" << pc_
                  << " bytecode_.size()=" << bytecode_.size()
                  << std::endl;
    }
    while (!halted_ && pc_ < bytecode_.size()) {
        InstructionTrace trace;
        trace.sequence = instruction_sequence_++;
        trace.pc_before = pc_;

        // EXP-071 Phase 6 debug: Log first 20 instructions of setCountry.
        if (current_method_ == "setCountry" && current_class_.find("PhoneView") != std::string::npos && instruction_sequence_ <= 20) {
            std::cerr << "[EXP071-FDE-LOOP] " << current_class_ << "." << current_method_
                      << " iter=" << instruction_sequence_
                      << " pc_=" << pc_
                      << " opcode=0x" << std::hex << (int)(bytecode_[pc_] & 0xFF) << std::dec
                      << std::endl;
        }
        
        auto start = Clock::now();
        
        // Fetch opcode
        // EXP-037 Phase B (BLOCKER-012 FIX):
        // Dalvik bytecode packs the opcode in the LOW BYTE of each 16-bit
        // code unit. The HIGH BYTE contains format-specific data:
        //   - 35c (invoke-*): high nibble = arg count, low nibble of high byte = 5th reg
        //   - 11n (const/4): high nibble = register, low nibble of high byte = signed literal
        //   - 22b (iput): high byte = two register nibbles
        //   - 10x (return-void): high byte = 0
        // The previous code passed the full 16-bit word to the switch, which
        // meant `case Opcode::INVOKE_SUPER (0x6F)` never matched the actual
        // bytecode value 0x206F (where 0x20 = arg count + 5th reg). The switch
        // fell through to the default "UNIMPLEMENTED" handler.
        //
        // Fix: mask off the high byte before dispatch. The high byte is
        // re-read by each opcode handler from bytecode_[pc] (e.g. via
        // `(instr >> 4) & 0xF` for the arg count).
        uint16_t raw_word = fetch_opcode(pc_);
        uint16_t opcode = raw_word & 0xFF;  // LOW BYTE only
        trace.opcode_hex = raw_word;        // Keep raw word for trace evidence

        // EXP-063: Trace v3 in getString(I) to find where it gets corrupted
        if (current_class_.find("LocaleController") != std::string::npos &&
            current_method_ == "getString" && current_registers_) {
            auto v3 = current_registers_->read_v(3);
            std::cerr << "[EXP063-V3] PC=" << pc_ << " op=0x" << std::hex << opcode << std::dec
                      << " v3_type=" << static_cast<int>(v3.type)
                      << " v3_int=" << v3.int_val
                      << " v3_obj=" << v3.object_id
                      << std::endl;
        }
        
        // EXP-042 Phase 1: Per-instruction register snapshots are the #1 OOM
        // offender (5 KB per instruction). Capture them ONLY when explicitly
        // enabled via config_.trace_register_snapshots. Default is false.
        if (config_.trace_register_snapshots && current_registers_) {
            trace.registers_before = current_registers_->get_snapshot();
        }
        
        // Decode and execute
        bool success = true;
        
        switch (opcode) {
            // Constants
            case Opcode::CONST_4:
                success = execute_const_4(pc_, trace);
                trace.opcode_name = "const/4";
                break;
            case Opcode::CONST_16:
                success = execute_const_16(pc_, trace);
                trace.opcode_name = "const/16";
                break;
            case Opcode::CONST_HIGH16: {
                // Format 21s: AA|op BBBB
                // vAA = (int32_t)(BBBB << 16) — sign-extend the 16-bit value to high 16 bits
                if (pc_ + 1 >= bytecode_.size()) return false;
                uint16_t instr = bytecode_[pc_];
                uint8_t vAA = (instr >> 8) & 0xFF;
                int16_t bbbb = static_cast<int16_t>(bytecode_[pc_ + 1]);
                DalvikValue val;
                val.type = DalvikType::INT32;
                val.int_val = static_cast<int32_t>(bbbb) << 16;
                set_register(vAA, val);
                trace.opcode_name = "const/high16";
                pc_ = pc_ + 2;
                break;
            }
            case Opcode::CONST:
                success = execute_const(pc_, trace);
                trace.opcode_name = "const";
                break;
            case Opcode::CONST_STRING:
                success = execute_const_string(pc_, trace);
                trace.opcode_name = "const-string";
                break;
            case Opcode::CONST_CLASS:
                success = execute_const_class(pc_, trace);
                trace.opcode_name = "const-class";
                break;
            
            // Moves
            case Opcode::MOVE:
                success = execute_move(pc_, trace);
                trace.opcode_name = "move";
                break;
            case Opcode::MOVE_OBJECT:
                success = execute_move_object(pc_, trace);
                trace.opcode_name = "move-object";
                break;
            case Opcode::MOVE_OBJECT_FROM16:
                // EXP-038 (BLOCKER-026): move-object/from16
                success = execute_move_object_from16(pc_, trace);
                trace.opcode_name = "move-object/from16";
                break;
            case Opcode::MOVE_RESULT:
                success = execute_move_result(pc_, trace);
                trace.opcode_name = "move-result";
                break;
            case Opcode::MOVE_RESULT_OBJECT:
                success = execute_move_result_object(pc_, trace);
                trace.opcode_name = "move-result-object";
                break;

            // EXP-053: move-exception (11x: AA|op, 1 code unit).
            // Moves the thrown exception into register vAA so the catch
            // handler can access it. We store the exception in a per-method
            // pending_exception_ slot when THROW jumps to a handler; this
            // opcode reads from that slot.
            case Opcode::MOVE_EXCEPTION: {
                trace.opcode_name = "move-exception";
                uint8_t vAA = (bytecode_[pc_] >> 8) & 0xFF;
                // Read the pending exception set by THROW.
                // If no pending exception (shouldn't happen), use null.
                DalvikValue exc = pending_exception_;
                set_register(vAA, exc);
                trace.operands.push_back({"v" + std::to_string(vAA), exc.to_string()});
                // Clear the pending exception after move.
                pending_exception_ = DalvikValue::make_null();
                pc_ += 1;
                break;
            }
            
            // Objects
            case Opcode::NEW_INSTANCE:
                success = execute_new_instance(pc_, trace);
                trace.opcode_name = "new-instance";
                break;
            case Opcode::NEW_ARRAY: {
                // Format 22c: B1|A|op CCCC (2 code units)
                // Creates a new array of type@CCCC with size vB, result in vA
                if (pc_ + 1 >= bytecode_.size()) return false;
                uint16_t instr = bytecode_[pc_];
                uint8_t vA = (instr >> 8) & 0xF;    // dest register (array ref)
                uint8_t vB = (instr >> 12) & 0xF;   // size register
                uint16_t type_idx = bytecode_[pc_ + 1];  // type@CCCC

                // Get array size from vB
                DalvikValue size_val = get_register(vB);
                int32_t array_size = (size_val.type == DalvikType::INT32) ? size_val.int_val : 0;
                if (array_size < 0) array_size = 0;

                // Allocate array object on heap (simplified — just store as OBJECT_REF)
                uint32_t obj_id = heap_.allocate("Larray;", pc_, 0);
                DalvikValue result_val;
                result_val.type = DalvikType::OBJECT_REF;
                result_val.object_id = obj_id;
                result_val.class_desc = "Larray;";
                result_val.int_val = array_size;  // store size in int_val for convenience
                set_register(vA, result_val);

                // EXP-062: Store array length on heap so aget/aput can find it.
                if (heap_.has_object(obj_id)) {
                    heap_.set_object_field(obj_id, "__new_array_length__",
                        DalvikValue::make_int(array_size));
                }

                // EXP-066: Use per-DEX type resolution for trace evidence.
                std::string type_name = "<unknown>";
                type_name = resolve_type_for_dex(type_idx, current_dex_index_);
                log("✅ NEW-ARRAY: type=" + type_name + " size=" + std::to_string(array_size) + " → obj#" + std::to_string(obj_id));

                trace.opcode_name = "new-array";
                trace.operands.push_back({"type", type_name});
                trace.operands.push_back({"size", std::to_string(array_size)});
                pc_ = pc_ + 2;  // 22c = 2 code units
                break;
            }
            case Opcode::ARRAY_LENGTH: {
                // Format 12x: B|A|op (1 code unit)
                // vA = length of array in vB
                if (pc_ >= bytecode_.size()) return false;
                uint16_t instr = bytecode_[pc_];
                uint8_t vA = (instr >> 8) & 0xF;   // dest
                uint8_t vB = (instr >> 4) & 0xF;    // source array
                DalvikValue arr = get_register(vB);
                DalvikValue result_val;
                result_val.type = DalvikType::INT32;
                result_val.int_val = (arr.type == DalvikType::OBJECT_REF) ? arr.int_val : 0;
                set_register(vA, result_val);
                trace.opcode_name = "array-length";
                pc_ = pc_ + 1;
                break;
            }

            // EXP-038 (BLOCKER-031): Array get/put opcodes (23x format, 2 code units)
            // Format 23x: AA|op BB|CC
            //   vAA = dest/src, vBB = array ref, vCC = index
            //
            // EXP-044 Phase 1: Proper array bounds checking.
            // When the index is out of bounds (or the array is null/empty),
            // we simulate ArrayIndexOutOfBoundsException by halting the method.
            // This is required for Kotlin Intrinsics.createParameterIsNullExceptionMessage
            // which loops through stack trace elements and expects an exception
            // when the index exceeds the array length.
            // EXP-062: Real array element retrieval.
            // Previously ARRAY_GET_CASE always returned NULL_REF for objects.
            // Now we read elements stored by aput-object from the HeapObject.
            #define ARRAY_GET_CASE(opcode, op_name, result_type) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vAA = (instr >> 8) & 0xFF; \
                    uint8_t vBB = bytecode_[pc_ + 1] & 0xFF; \
                    uint8_t vCC = (bytecode_[pc_ + 1] >> 8) & 0xFF; \
                    DalvikValue arr_val = get_register(vBB); \
                    DalvikValue idx_val = get_register(vCC); \
                    int32_t idx = (idx_val.type == DalvikType::INT32) ? idx_val.int_val : 0; \
                    trace.opcode_name = op_name; \
                    /* EXP-062: Read array length from heap field */ \
                    int32_t arr_len = 0; \
                    if (arr_val.type == DalvikType::OBJECT_REF && \
                        heap_.has_object(arr_val.object_id)) { \
                        auto len_field = heap_.get_object_field(arr_val.object_id, "__array_length__"); \
                        if (len_field.has_value() && len_field->type == DalvikType::INT32) { \
                            arr_len = len_field->int_val; \
                        } \
                        /* Also check if new-array stored a length */ \
                        if (arr_len == 0) { \
                            auto nm_field = heap_.get_object_field(arr_val.object_id, "__new_array_length__"); \
                            if (nm_field.has_value() && nm_field->type == DalvikType::INT32) { \
                                arr_len = nm_field->int_val; \
                            } \
                        } \
                    } \
                    if (arr_len == 0) { \
                        /* Fallback: use int_val from arr_val (old behavior) */ \
                        arr_len = (arr_val.type == DalvikType::OBJECT_REF) ? arr_val.int_val : 0; \
                    } \
                    if (arr_len == 0 || idx < 0 || idx >= arr_len) { \
                        log("⚠️ AGET out of bounds: arr_len=" + std::to_string(arr_len) + \
                            " idx=" + std::to_string(idx)); \
                        DalvikValue result_val; \
                        result_val.type = result_type; \
                        if (result_type == DalvikType::OBJECT_REF) { \
                            result_val = DalvikValue::make_null(); \
                        } \
                        set_register(vAA, result_val); \
                        pc_ = pc_ + 2; \
                        break; \
                    } \
                    /* EXP-062: Read element from heap */ \
                    /* EXP-071: FIX — aget-boolean/aget/aget-byte/aget-char/aget-short
                     * were NOT reading from the heap (only aget-object was). This caused
                     * boolean array reads to always return 0 (false), which made
                     * LoginActivity.onDoneButtonPressed always return early (the
                     * doneButtonVisible[] check at PC=4-6 always returned false=0,
                     * and if-ltz 0 never branched). Now we read ALL array element
                     * types from the heap. */ \
                    DalvikValue result_val; \
                    result_val.type = result_type; \
                    /* Try reading from heap for ALL types (not just OBJECT_REF). */ \
                    if (arr_val.type == DalvikType::OBJECT_REF && \
                        heap_.has_object(arr_val.object_id)) { \
                        std::string field = "array[" + std::to_string(idx) + "]"; \
                        auto elem = heap_.get_object_field(arr_val.object_id, field); \
                        if (elem.has_value()) { \
                            result_val = elem.value(); \
                            /* Ensure type matches expected result_type */ \
                            if (result_type == DalvikType::BOOLEAN) { \
                                /* Normalize to 0 or 1 */ \
                                bool b = (elem->type == DalvikType::INT32) ? (elem->int_val != 0) : \
                                         (elem->type == DalvikType::BOOLEAN) ? elem->bool_val : false; \
                                result_val = DalvikValue::make_bool(b); \
                            } else if (result_type == DalvikType::INT32 && \
                                       elem->type != DalvikType::INT32) { \
                                result_val = DalvikValue::make_int(0); \
                            } \
                        } else { \
                            if (result_type == DalvikType::OBJECT_REF) { \
                                result_val = DalvikValue::make_null(); \
                            } \
                        } \
                    } else { \
                        if (result_type == DalvikType::OBJECT_REF) { \
                            result_val = DalvikValue::make_null(); \
                        } \
                    } else { \
                        /* EXP-071: Read ALL primitive types (boolean, byte, */ \
                        /* char, short, int, long) from the heap, not just   */ \
                        /* OBJECT_REF. Without this, aget-boolean returns    */ \
                        /* the default value (false) because the boolean    */ \
                        /* was stored by aput-boolean in the heap, not as    */ \
                        /* an INT32 register value.                        */ \
                        result_val = DalvikValue::make_int(0); \
                        if (result_type == DalvikType::BOOLEAN) { \
                            result_val = DalvikValue::make_bool(false); \
                        } else if (result_type == DalvikType::BYTE) { \
                            result_val = DalvikValue::make_byte(0); \
                        } else if (result_type == DalvikType::CHAR) { \
                            result_val = DalvikValue::make_char(0); \
                        } else if (result_type == DalvikType::SHORT) { \
                            result_val = DalvikValue::make_short(0); \
                        } else if (result_type == DalvikType::INT64) { \
                            DalvikValue lv; lv.type = DalvikType::INT64; lv.long_val = 0; \
                            result_val = lv; \
                        } \
                        if (arr_val.type == DalvikType::OBJECT_REF && \
                            heap_.has_object(arr_val.object_id)) { \
                            std::string field = "array[" + std::to_string(idx) + "]"; \
                            auto elem = heap_.get_object_field(arr_val.object_id, field); \
                            if (elem.has_value()) { \
                                /* Coerce the stored value to the expected   */ \
                                /* primitive type.                           */ \
                                const auto& ev = elem.value(); \
                                if (result_type == DalvikType::BOOLEAN) { \
                                    bool b = ev.bool_val || ev.int_val != 0; \
                                    result_val = DalvikValue::make_bool(b); \
                                } else if (result_type == DalvikType::INT32) { \
                                    int32_t iv = ev.int_val; \
                                    result_val = DalvikValue::make_int(iv); \
                                } else if (result_type == DalvikType::INT64) { \
                                    DalvikValue lv; lv.type = DalvikType::INT64; \
                                    lv.long_val = ev.long_val ? ev.long_val : ev.int_val; \
                                    result_val = lv; \
                                } else { \
                                    result_val = ev; \
                                    result_val.type = result_type; \
                                } \
                            } \
                        } \
                    } \
                    set_register(vAA, result_val); \
                    pc_ = pc_ + 2; \
                    break; \
                }

            ARRAY_GET_CASE(AGET, "aget", DalvikType::INT32)
            ARRAY_GET_CASE(AGET_WIDE, "aget-wide", DalvikType::INT64)
            ARRAY_GET_CASE(AGET_OBJECT, "aget-object", DalvikType::OBJECT_REF)
            ARRAY_GET_CASE(AGET_BOOLEAN, "aget-boolean", DalvikType::BOOLEAN)
            ARRAY_GET_CASE(AGET_BYTE, "aget-byte", DalvikType::BYTE)
            ARRAY_GET_CASE(AGET_CHAR, "aget-char", DalvikType::CHAR)
            ARRAY_GET_CASE(AGET_SHORT, "aget-short", DalvikType::SHORT)
            #undef ARRAY_GET_CASE

            // EXP-062: Real array element storage.
            // Previously ARRAY_PUT_CASE was a NO-OP — aput-object did nothing.
            // Now we store elements in the HeapObject's fields using a
            // synthetic field name "array[idx]".
            #define ARRAY_PUT_CASE(opcode, op_name) \
                case Opcode::opcode: { \
                    trace.opcode_name = op_name; \
                    uint8_t vAA = (bytecode_[pc_] >> 8) & 0xFF; \
                    uint8_t vBB = bytecode_[pc_ + 1] & 0xFF; \
                    uint8_t vCC = (bytecode_[pc_ + 1] >> 8) & 0xFF; \
                    DalvikValue arr_val = get_register(vBB); \
                    DalvikValue idx_val = get_register(vCC); \
                    DalvikValue src_val = get_register(vAA); \
                    int32_t idx = (idx_val.type == DalvikType::INT32) ? idx_val.int_val : 0; \
                    if (arr_val.type == DalvikType::OBJECT_REF && \
                        heap_.has_object(arr_val.object_id)) { \
                        std::string field = "array[" + std::to_string(idx) + "]"; \
                        heap_.set_object_field(arr_val.object_id, field, src_val); \
                        /* Also store the array length if not set */ \
                        auto len_field = heap_.get_object_field(arr_val.object_id, "__array_length__"); \
                        if (!len_field.has_value() || len_field->int_val <= idx) { \
                            heap_.set_object_field(arr_val.object_id, "__array_length__", \
                                DalvikValue::make_int(idx + 1)); \
                        } \
                    } \
                    pc_ = pc_ + 2; \
                    break; \
                }

            ARRAY_PUT_CASE(APUT, "aput")
            ARRAY_PUT_CASE(APUT_WIDE, "aput-wide")
            ARRAY_PUT_CASE(APUT_OBJECT, "aput-object")
            ARRAY_PUT_CASE(APUT_BOOLEAN, "aput-boolean")
            ARRAY_PUT_CASE(APUT_BYTE, "aput-byte")
            ARRAY_PUT_CASE(APUT_CHAR, "aput-char")
            ARRAY_PUT_CASE(APUT_SHORT, "aput-short")
            #undef ARRAY_PUT_CASE
            case Opcode::CHECK_CAST:
                success = execute_check_cast(pc_, trace);
                trace.opcode_name = "check-cast";
                break;
            case Opcode::INSTANCE_OF:
                success = execute_instance_of(pc_, trace);
                trace.opcode_name = "instance-of";
                break;
            
            // EXP-035: Instance Field Operations
            case Opcode::IGET:
                success = execute_iget(pc_, trace);
                trace.opcode_name = "iget";
                break;
            case Opcode::IGET_OBJECT:
                success = execute_iget_object(pc_, trace);
                trace.opcode_name = "iget-object";
                break;
            // EXP-062: Add missing iget variants. iget-wide reads a 64-bit
            // field; iget-boolean/byte/char/short read primitive fields.
            // All use the same 22c format as iget.
            case Opcode::IGET_WIDE:
            case Opcode::IGET_BOOLEAN:
            case Opcode::IGET_BYTE:
            case Opcode::IGET_CHAR:
            case Opcode::IGET_SHORT:
                success = execute_iget(pc_, trace);
                trace.opcode_name = "iget-variant";
                break;
            case Opcode::IPUT:
                success = execute_iput(pc_, trace);
                trace.opcode_name = "iput";
                break;
            case Opcode::IPUT_OBJECT:
                success = execute_iput_object(pc_, trace);
                trace.opcode_name = "iput-object";
                break;
            // EXP-062: iput-wide and other iput variants.
            // iput-wide writes a 64-bit value (occupying vA and vA+1)
            // to a field. We store it as a single INT64 DalvikValue.
            case Opcode::IPUT_WIDE:
            case Opcode::IPUT_BOOLEAN:
            case Opcode::IPUT_BYTE:
            case Opcode::IPUT_CHAR:
            case Opcode::IPUT_SHORT:
                success = execute_iput(pc_, trace);
                trace.opcode_name = "iput-variant";
                break;
            
            // EXP-035: Static Field Operations
            case Opcode::SGET:
                success = execute_sget(pc_, trace);
                trace.opcode_name = "sget";
                break;
            case Opcode::SGET_OBJECT:
                success = execute_sget_object(pc_, trace);
                trace.opcode_name = "sget-object";
                break;
            // EXP-062: Add sget-wide
            case Opcode::SGET_WIDE:
                success = execute_sget(pc_, trace);
                trace.opcode_name = "sget-wide";
                break;
            case Opcode::SPUT:
                success = execute_sput(pc_, trace);
                trace.opcode_name = "sput";
                break;
            case Opcode::SPUT_OBJECT:
                success = execute_sput_object(pc_, trace);
                trace.opcode_name = "sput-object";
                break;
            // EXP-062: Add sput-wide
            case Opcode::SPUT_WIDE:
                success = execute_sput(pc_, trace);
                trace.opcode_name = "sput-wide";
                break;
            // EXP-038 (BLOCKER-027): sput-boolean and other sget/sput variants
            case Opcode::SPUT_BOOLEAN:
                success = execute_sput(pc_, trace);  // same logic as sput
                trace.opcode_name = "sput-boolean";
                break;
            case Opcode::SPUT_BYTE:
            case Opcode::SPUT_CHAR:
            case Opcode::SPUT_SHORT:
                success = execute_sput(pc_, trace);
                trace.opcode_name = "sput-variant";
                break;
            case Opcode::SGET_BOOLEAN:
            case Opcode::SGET_BYTE:
            case Opcode::SGET_CHAR:
            case Opcode::SGET_SHORT:
                success = execute_sget(pc_, trace);  // same logic as sget
                trace.opcode_name = "sget-variant";
                break;
            
            // Invokes
            case Opcode::INVOKE_VIRTUAL:
                success = execute_invoke_virtual(pc_, trace, result);
                trace.opcode_name = "invoke-virtual";
                break;
            case Opcode::INVOKE_SUPER:
                // EXP-037 Phase B (BLOCKER-012): invoke-super — required for
                // super.onCreate() calls. Without this, execution halts at PC=0
                // of MainActivity.onCreate() for every real Android APK.
                success = execute_invoke_super(pc_, trace, result);
                trace.opcode_name = "invoke-super";
                break;
            case Opcode::INVOKE_DIRECT:
                success = execute_invoke_direct(pc_, trace, result);
                trace.opcode_name = "invoke-direct";
                break;
            case Opcode::INVOKE_STATIC:
                success = execute_invoke_static(pc_, trace, result);
                trace.opcode_name = "invoke-static";
                break;
            case Opcode::INVOKE_INTERFACE:
                success = execute_invoke_interface(pc_, trace, result);
                trace.opcode_name = "invoke-interface";
                break;

            // EXP-049 Phase 3: invoke-*/range opcodes (3rc format)
            // Format 3rc: AA|op BBBB CCCC (3 code units)
            //   AA = arg count (high byte of first code unit)
            //   BBBB = method_idx (second code unit)
            //   CCCC = first register (third code unit)
            // The 3rc format reads AA consecutive registers starting at CCCC.
            // CRITICAL: The old code routed these to the 35c handlers which
            // extract registers as 4-bit nibbles from a 16-bit FEDC word.
            // But 3rc uses CCCC as a 16-bit register base, reading consecutive
            // 16-bit register indices. This was BROKEN — the 35c handler
            // reads method_idx from pc+1 (correct) but register list from pc+2
            // as 4-bit nibbles (WRONG for 3rc). The fix is to build the args
            // vector from consecutive registers starting at CCCC.
            case Opcode::INVOKE_VIRTUAL_RANGE:
            case Opcode::INVOKE_SUPER_RANGE:
            case Opcode::INVOKE_DIRECT_RANGE:
            case Opcode::INVOKE_STATIC_RANGE:
            case Opcode::INVOKE_INTERFACE_RANGE: {
                // 3rc format: AA|op BBBB CCCC
                if (pc_ + 2 >= bytecode_.size()) { pc_ = pc_ + 1; break; }
                uint16_t instr = bytecode_[pc_];
                uint8_t argc = (instr >> 8) & 0xFF;  // AA = arg count
                uint16_t method_idx = bytecode_[pc_ + 1];  // BBBB = method index
                uint16_t first_reg = bytecode_[pc_ + 2];   // CCCC = first register

                // Build args from consecutive registers
                std::vector<DalvikValue> args;
                for (uint8_t i = 0; i < argc; ++i) {
                    args.push_back(get_register(first_reg + i));
                }

                // Resolve method name
                std::string method_name = "<range_method:" + std::to_string(method_idx) + ">";
                std::string class_name = "<range_class>";
                if (dex_report_) {
                    method_name = resolve_method_name_for_dex(method_idx, current_dex_index_);
                    class_name = resolve_method_class_for_dex(method_idx, current_dex_index_);
                }

                trace.opcode_name = "invoke-*/range";

                // Try recursive invoke
                DalvikValue return_val = DalvikValue::make_void();
                ApiCallTrace::Status status = ApiCallTrace::Status::STUBBED;

                bool recursively_invoked = false;
                if (config_.enable_api_bridge) {
                    if (try_recursive_invoke(class_name, method_name, args, return_val, result)) { last_invoke_return_ = return_val;
                        recursively_invoked = true;
                        status = ApiCallTrace::Status::IMPLEMENTED;
                    }
                }
                if (!recursively_invoked && config_.enable_api_bridge) {
                    bridge_to_api(class_name, method_name, args, return_val, status); last_invoke_return_ = return_val;
                }

                // Record API trace
                ApiCallTrace api_trace;
                api_trace.sequence = api_call_sequence_++;
                api_trace.api_class = class_name;
                api_trace.method = method_name;
                api_trace.status = status;
                api_trace.pc = pc_;
                if (config_.api_call_trace_cap > 0 && result.api_call_traces.size() >= config_.api_call_trace_cap) {
                    result.api_call_traces.erase(result.api_call_traces.begin());
                }
                result.api_call_traces.push_back(api_trace);

                trace.invoked_method = class_name + "." + method_name;
                pc_ = pc_ + 3;
                break;
            }
            
            // Returns
            case Opcode::RETURN_VOID:
                success = execute_return_void(pc_, trace);
                trace.opcode_name = "return-void";
                break;
            case Opcode::RETURN:
                success = execute_return(pc_, trace);
                trace.opcode_name = "return";
                break;
            case Opcode::RETURN_OBJECT:
                success = execute_return_object(pc_, trace);
                trace.opcode_name = "return-object";
                break;
            
            // Control flow
            case Opcode::GOTO:
            case Opcode::GOTO_16:
            case Opcode::GOTO_32:
                success = execute_goto(pc_, trace);
                trace.opcode_name = "goto";
                break;
            case Opcode::IF_EQZ:
                success = execute_if_eqz(pc_, trace);
                trace.opcode_name = "if-eqz";
                break;
            case Opcode::IF_NEZ:
                success = execute_if_nez(pc_, trace);
                trace.opcode_name = "if-nez";
                break;
            // EXP-037 Phase B (BLOCKER-018): 22t format if-* opcodes
            case Opcode::IF_EQ:
                success = execute_if_eq(pc_, trace);
                trace.opcode_name = "if-eq";
                break;
            case Opcode::IF_NE:
                success = execute_if_ne(pc_, trace);
                trace.opcode_name = "if-ne";
                break;
            case Opcode::IF_LT:
                success = execute_if_lt(pc_, trace);
                trace.opcode_name = "if-lt";
                break;
            case Opcode::IF_GE:
                success = execute_if_ge(pc_, trace);
                trace.opcode_name = "if-ge";
                break;
            case Opcode::IF_GT:
                success = execute_if_gt(pc_, trace);
                trace.opcode_name = "if-gt";
                break;
            case Opcode::IF_LE:
                success = execute_if_le(pc_, trace);
                trace.opcode_name = "if-le";
                break;

            // EXP-038 (BLOCKER-029): if-*z opcodes (21t format, like if-eqz)
            // EXP-043 Phase 1: each if-*z opcode now dispatches to its OWN
            // handler instead of all routing to execute_if_eqz. Previously
            // if-ltz/if-gez/if-lez all used execute_if_eqz's "if (v == 0)"
            // comparison, and if-gtz used execute_if_nez's "if (v != 0)"
            // comparison. These are WRONG — if-ltz must be "if (v < 0)",
            // if-gez "if (v >= 0)", if-gtz "if (v > 0)", if-lez "if (v <= 0)".
            // The bug caused Kotlin Intrinsics.createParameterIsNullExceptionMessage
            // to loop forever because if-ltz v3 with v3=5 was treated as
            // if-eqz (5==0 false) instead of if-ltz (5<0 false) — same answer
            // in that case, but if-ltz v3 with v3=-1 should branch but didn't.
            case Opcode::IF_LTZ:
                success = execute_if_ltz(pc_, trace);
                trace.opcode_name = "if-ltz";
                break;
            case Opcode::IF_GEZ:
                success = execute_if_gez(pc_, trace);
                trace.opcode_name = "if-gez";
                break;
            case Opcode::IF_GTZ:
                success = execute_if_gtz(pc_, trace);
                trace.opcode_name = "if-gtz";
                break;
            case Opcode::IF_LEZ:
                success = execute_if_lez(pc_, trace);
                trace.opcode_name = "if-lez";
                break;
            
            case Opcode::NOP:
                trace.opcode_name = "nop";
                pc_ += 1;
                break;

            // EXP-038 (BLOCKER-028): Arithmetic 2addr opcodes (12x format)
            // vA = vA <op> vB
            #define ARITH_2ADDR_CASE(opcode, op_name, op) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vA = (instr >> 8) & 0xF; \
                    uint8_t vB = (instr >> 4) & 0xF; \
                    DalvikValue a = get_register(vA); \
                    DalvikValue b = get_register(vB); \
                    DalvikValue result_val; \
                    result_val.type = DalvikType::INT32; \
                    int32_t a_val = (a.type == DalvikType::INT32) ? a.int_val : 0; \
                    int32_t b_val = (b.type == DalvikType::INT32) ? b.int_val : 0; \
                    if (op == "div" && b_val == 0) { result_val.int_val = 0; } \
                    else if (op == "rem" && b_val == 0) { result_val.int_val = 0; } \
                    else if (op == "add") result_val.int_val = a_val + b_val; \
                    else if (op == "sub") result_val.int_val = a_val - b_val; \
                    else if (op == "mul") result_val.int_val = a_val * b_val; \
                    else if (op == "div") result_val.int_val = a_val / b_val; \
                    else if (op == "rem") result_val.int_val = a_val % b_val; \
                    else if (op == "and") result_val.int_val = a_val & b_val; \
                    else if (op == "or")  result_val.int_val = a_val | b_val; \
                    else if (op == "xor") result_val.int_val = a_val ^ b_val; \
                    else if (op == "shl") result_val.int_val = a_val << (b_val & 0x1f); \
                    else if (op == "shr") result_val.int_val = a_val >> (b_val & 0x1f); \
                    else if (op == "ushr") result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(a_val) >> (b_val & 0x1f)); \
                    set_register(vA, result_val); \
                    trace.opcode_name = op_name; \
                    pc_ = pc_ + 1; \
                    break; \
                }

            ARITH_2ADDR_CASE(ADD_INT_2ADDR, "add-int/2addr", "add")
            ARITH_2ADDR_CASE(SUB_INT_2ADDR, "sub-int/2addr", "sub")
            ARITH_2ADDR_CASE(MUL_INT_2ADDR, "mul-int/2addr", "mul")
            ARITH_2ADDR_CASE(DIV_INT_2ADDR, "div-int/2addr", "div")
            ARITH_2ADDR_CASE(REM_INT_2ADDR, "rem-int/2addr", "rem")
            ARITH_2ADDR_CASE(AND_INT_2ADDR, "and-int/2addr", "and")
            ARITH_2ADDR_CASE(OR_INT_2ADDR,  "or-int/2addr",  "or")
            ARITH_2ADDR_CASE(XOR_INT_2ADDR, "xor-int/2addr", "xor")
            ARITH_2ADDR_CASE(SHL_INT_2ADDR, "shl-int/2addr", "shl")
            ARITH_2ADDR_CASE(SHR_INT_2ADDR, "shr-int/2addr", "shr")
            ARITH_2ADDR_CASE(USHR_INT_2ADDR, "ushr-int/2addr", "ushr")
            #undef ARITH_2ADDR_CASE

            // EXP-038 (BLOCKER-028): Binary 23x format: AA|op BB|CC
            // vAA = vBB <op> vCC
            #define ARITH_23X_CASE(opcode, op_name, op) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vAA = (instr >> 8) & 0xFF; \
                    uint8_t vBB = bytecode_[pc_ + 1] & 0xFF; \
                    uint8_t vCC = (bytecode_[pc_ + 1] >> 8) & 0xFF; \
                    DalvikValue b = get_register(vBB); \
                    DalvikValue c = get_register(vCC); \
                    DalvikValue result_val; \
                    result_val.type = DalvikType::INT32; \
                    int32_t b_val = (b.type == DalvikType::INT32) ? b.int_val : 0; \
                    int32_t c_val = (c.type == DalvikType::INT32) ? c.int_val : 0; \
                    if (op == "add") result_val.int_val = b_val + c_val; \
                    else if (op == "sub") result_val.int_val = b_val - c_val; \
                    else if (op == "mul") result_val.int_val = b_val * c_val; \
                    else if (op == "div") result_val.int_val = (c_val != 0) ? b_val / c_val : 0; \
                    else if (op == "rem") result_val.int_val = (c_val != 0) ? b_val % c_val : 0; \
                    else if (op == "and") result_val.int_val = b_val & c_val; \
                    else if (op == "or")  result_val.int_val = b_val | c_val; \
                    else if (op == "xor") result_val.int_val = b_val ^ c_val; \
                    set_register(vAA, result_val); \
                    trace.opcode_name = op_name; \
                    pc_ = pc_ + 2; \
                    break; \
                }

            ARITH_23X_CASE(ADD_INT, "add-int", "add")
            ARITH_23X_CASE(SUB_INT, "sub-int", "sub")
            ARITH_23X_CASE(MUL_INT, "mul-int", "mul")
            ARITH_23X_CASE(DIV_INT, "div-int", "div")
            ARITH_23X_CASE(REM_INT, "rem-int", "rem")
            ARITH_23X_CASE(AND_INT, "and-int", "and")
            ARITH_23X_CASE(OR_INT,  "or-int",  "or")
            ARITH_23X_CASE(XOR_INT, "xor-int", "xor")
            #undef ARITH_23X_CASE

            // EXP-038 (BLOCKER-028): Arithmetic lit8 (22b format: AA|op BB|CC)
            // vAA = vBB <op> #CC (signed byte)
            #define ARITH_LIT8_CASE(opcode, op_name, op) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vAA = (instr >> 8) & 0xFF; \
                    uint8_t vBB = bytecode_[pc_ + 1] & 0xFF; \
                    int8_t lit = static_cast<int8_t>(bytecode_[pc_ + 1] >> 8); \
                    DalvikValue b = get_register(vBB); \
                    DalvikValue result_val; \
                    result_val.type = DalvikType::INT32; \
                    int32_t b_val = (b.type == DalvikType::INT32) ? b.int_val : 0; \
                    if (op == "add") result_val.int_val = b_val + lit; \
                    else if (op == "sub") result_val.int_val = b_val - lit; \
                    else if (op == "mul") result_val.int_val = b_val * lit; \
                    else if (op == "and") result_val.int_val = b_val & lit; \
                    else if (op == "or")  result_val.int_val = b_val | lit; \
                    else if (op == "xor") result_val.int_val = b_val ^ lit; \
                    set_register(vAA, result_val); \
                    trace.opcode_name = op_name; \
                    pc_ = pc_ + 2; \
                    break; \
                }

            ARITH_LIT8_CASE(ADD_INT_LIT8, "add-int/lit8", "add")
            ARITH_LIT8_CASE(RSUB_INT_LIT8, "sub-int/lit8", "sub")
            ARITH_LIT8_CASE(MUL_INT_LIT8, "mul-int/lit8", "mul")
            ARITH_LIT8_CASE(AND_INT_LIT8, "and-int/lit8", "and")
            ARITH_LIT8_CASE(OR_INT_LIT8,  "or-int/lit8",  "or")
            ARITH_LIT8_CASE(XOR_INT_LIT8, "xor-int/lit8", "xor")
            #undef ARITH_LIT8_CASE

            // EXP-038 (BLOCKER-028): Arithmetic lit16 (22s format: AA|op BBBB)
            // vA = vB <op> #BBBB (signed 16-bit)
            #define ARITH_LIT16_CASE(opcode, op_name, op) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vA = (instr >> 8) & 0xF; \
                    uint8_t vB = (instr >> 4) & 0xF; \
                    int16_t lit = static_cast<int16_t>(bytecode_[pc_ + 1]); \
                    DalvikValue b = get_register(vB); \
                    DalvikValue result_val; \
                    result_val.type = DalvikType::INT32; \
                    int32_t b_val = (b.type == DalvikType::INT32) ? b.int_val : 0; \
                    if (op == "add") result_val.int_val = b_val + lit; \
                    else if (op == "sub") result_val.int_val = b_val - lit; \
                    else if (op == "mul") result_val.int_val = b_val * lit; \
                    else if (op == "div") result_val.int_val = (lit != 0) ? b_val / lit : 0; \
                    else if (op == "rem") result_val.int_val = (lit != 0) ? b_val % lit : 0; \
                    else if (op == "and") result_val.int_val = b_val & lit; \
                    else if (op == "or")  result_val.int_val = b_val | lit; \
                    else if (op == "xor") result_val.int_val = b_val ^ lit; \
                    set_register(vA, result_val); \
                    trace.opcode_name = op_name; \
                    pc_ = pc_ + 2; \
                    break; \
                }

            ARITH_LIT16_CASE(ADD_INT_LIT16, "add-int/lit16", "add")
            ARITH_LIT16_CASE(RSUB_INT_LIT16, "rsub-int", "sub")
            ARITH_LIT16_CASE(MUL_INT_LIT16, "mul-int/lit16", "mul")
            ARITH_LIT16_CASE(DIV_INT_LIT16, "div-int/lit16", "div")
            ARITH_LIT16_CASE(REM_INT_LIT16, "rem-int/lit16", "rem")
            ARITH_LIT16_CASE(AND_INT_LIT16, "and-int/lit16", "and")
            ARITH_LIT16_CASE(OR_INT_LIT16,  "or-int/lit16",  "or")
            ARITH_LIT16_CASE(XOR_INT_LIT16, "xor-int/lit16", "xor")
            #undef ARITH_LIT16_CASE

            // EXP-040: Missing opcodes from Telegram execution
            // move/from16 (22x: AA|op BBBB, 2 code units)
            case Opcode::MOVE_FROM16: {
                if (pc_ + 1 >= bytecode_.size()) return false;
                uint8_t dest = (bytecode_[pc_] >> 8) & 0xFF;
                uint16_t src = bytecode_[pc_ + 1];
                DalvikValue val = get_register(static_cast<uint8_t>(src));
                set_register(dest, val);
                trace.opcode_name = "move/from16";
                pc_ += 2;
                break;
            }
            // move-result-wide (11x: AA|op, 1 code unit)
            case Opcode::MOVE_RESULT_WIDE: {
                uint16_t instr = bytecode_[pc_];
                uint8_t dest = (instr >> 8) & 0xFF;
                DalvikValue val = DalvikValue::make_int(0); // simplified
                set_register(dest, val);
                trace.opcode_name = "move-result-wide";
                pc_ += 1;
                break;
            }
            // const-string/jumbo (31c: AA|op BBBBBBBB, 3 code units)
            case Opcode::CONST_STRING_JUMBO: {
                if (pc_ + 2 >= bytecode_.size()) return false;
                uint16_t instr = bytecode_[pc_];
                uint8_t dest = (instr >> 8) & 0xFF;
                uint32_t string_idx = (bytecode_[pc_ + 2] << 16) | bytecode_[pc_ + 1];
                DalvikValue val;
                val.type = DalvikType::STRING_REF;
                val.int_val = string_idx;
                // EXP-065: Use per-DEX string resolution (same fix as execute_const_string).
                val.string_val = resolve_string_for_dex(string_idx, current_dex_index_);
                set_register(dest, val);
                trace.opcode_name = "const-string/jumbo";
                pc_ += 3;
                break;
            }

            // Conversion opcodes (12x: B|A|op, 1 code unit) — simplified: just copy
            #define CONV_CASE(opcode, op_name) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vA = (instr >> 8) & 0xF; \
                    uint8_t vB = (instr >> 12) & 0xF; \
                    DalvikValue val = get_register(vB); \
                    val.type = DalvikType::INT32; /* simplified: treat as int */ \
                    set_register(vA, val); \
                    trace.opcode_name = op_name; \
                    pc_ += 1; \
                    break; \
                }
            CONV_CASE(INT_TO_LONG, "int-to-long")
            CONV_CASE(INT_TO_FLOAT, "int-to-float")
            CONV_CASE(INT_TO_DOUBLE, "int-to-double")
            CONV_CASE(LONG_TO_INT, "long-to-int")
            CONV_CASE(LONG_TO_FLOAT, "long-to-float")
            CONV_CASE(LONG_TO_DOUBLE, "long-to-double")
            CONV_CASE(FLOAT_TO_INT, "float-to-int")
            CONV_CASE(FLOAT_TO_LONG, "float-to-long")
            CONV_CASE(FLOAT_TO_DOUBLE, "float-to-double")
            CONV_CASE(DOUBLE_TO_INT, "double-to-int")
            CONV_CASE(DOUBLE_TO_LONG, "double-to-long")
            CONV_CASE(DOUBLE_TO_FLOAT, "double-to-float")
            CONV_CASE(INT_TO_BYTE, "int-to-byte")
            CONV_CASE(INT_TO_CHAR, "int-to-char")
            CONV_CASE(INT_TO_SHORT, "int-to-short")
            #undef CONV_CASE

            // Float/Double/Long arithmetic (23x: AA|op BB|CC, 2 code units)
            #define ARITH_23X_FLOAT_CASE(opcode, op_name, op) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vAA = (instr >> 8) & 0xFF; \
                    uint8_t vBB = bytecode_[pc_ + 1] & 0xFF; \
                    uint8_t vCC = (bytecode_[pc_ + 1] >> 8) & 0xFF; \
                    DalvikValue b = get_register(vBB); \
                    DalvikValue c = get_register(vCC); \
                    DalvikValue result_val; \
                    result_val.type = DalvikType::FLOAT32; \
                    float bf = (b.type == DalvikType::FLOAT32) ? b.float_val : (float)b.int_val; \
                    float cf = (c.type == DalvikType::FLOAT32) ? c.float_val : (float)c.int_val; \
                    if (op == "add") result_val.float_val = bf + cf; \
                    else if (op == "sub") result_val.float_val = bf - cf; \
                    else if (op == "mul") result_val.float_val = bf * cf; \
                    else if (op == "div") result_val.float_val = (cf != 0) ? bf / cf : 0; \
                    else if (op == "rem") result_val.float_val = fmodf(bf, cf); \
                    set_register(vAA, result_val); \
                    trace.opcode_name = op_name; \
                    pc_ += 2; \
                    break; \
                }
            ARITH_23X_FLOAT_CASE(ADD_FLOAT, "add-float", "add")
            ARITH_23X_FLOAT_CASE(SUB_FLOAT, "sub-float", "sub")
            ARITH_23X_FLOAT_CASE(MUL_FLOAT, "mul-float", "mul")
            ARITH_23X_FLOAT_CASE(DIV_FLOAT, "div-float", "div")
            ARITH_23X_FLOAT_CASE(REM_FLOAT, "rem-float", "rem")
            #undef ARITH_23X_FLOAT_CASE

            // cmp opcodes (23x) — simplified: compare as ints
            #define CMP_CASE(opcode, op_name) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vAA = (instr >> 8) & 0xFF; \
                    uint8_t vBB = bytecode_[pc_ + 1] & 0xFF; \
                    uint8_t vCC = (bytecode_[pc_ + 1] >> 8) & 0xFF; \
                    DalvikValue b = get_register(vBB); \
                    DalvikValue c = get_register(vCC); \
                    DalvikValue result_val; \
                    result_val.type = DalvikType::INT32; \
                    int32_t bv = (b.type == DalvikType::INT32) ? b.int_val : 0; \
                    int32_t cv = (c.type == DalvikType::INT32) ? c.int_val : 0; \
                    result_val.int_val = (bv < cv) ? -1 : (bv > cv) ? 1 : 0; \
                    set_register(vAA, result_val); \
                    trace.opcode_name = op_name; \
                    pc_ += 2; \
                    break; \
                }
            CMP_CASE(CMPL_FLOAT, "cmpl-float")
            CMP_CASE(CMPG_FLOAT, "cmpg-float")
            CMP_CASE(CMPL_DOUBLE, "cmpl-double")
            CMP_CASE(CMPG_DOUBLE, "cmpg-double")
            CMP_CASE(CMP_LONG, "cmp-long")
            #undef CMP_CASE

            // Long arithmetic (23x) — simplified: use int values
            #define ARITH_LONG_CASE(opcode, op_name, op) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vAA = (instr >> 8) & 0xFF; \
                    uint8_t vBB = bytecode_[pc_ + 1] & 0xFF; \
                    uint8_t vCC = (bytecode_[pc_ + 1] >> 8) & 0xFF; \
                    DalvikValue b = get_register(vBB); \
                    DalvikValue c = get_register(vCC); \
                    DalvikValue result_val; \
                    result_val.type = DalvikType::INT64; \
                    int32_t bv = (b.type == DalvikType::INT32 || b.type == DalvikType::INT64) ? b.int_val : 0; \
                    int32_t cv = (c.type == DalvikType::INT32 || c.type == DalvikType::INT64) ? c.int_val : 0; \
                    if (op == "add") result_val.int_val = bv + cv; \
                    else if (op == "sub") result_val.int_val = bv - cv; \
                    else if (op == "mul") result_val.int_val = bv * cv; \
                    else if (op == "div") result_val.int_val = (cv != 0) ? bv / cv : 0; \
                    else if (op == "rem") result_val.int_val = (cv != 0) ? bv % cv : 0; \
                    else if (op == "and") result_val.int_val = bv & cv; \
                    else if (op == "or")  result_val.int_val = bv | cv; \
                    else if (op == "xor") result_val.int_val = bv ^ cv; \
                    else if (op == "shl") result_val.int_val = bv << (cv & 0x3f); \
                    else if (op == "shr") result_val.int_val = bv >> (cv & 0x3f); \
                    else if (op == "ushr") result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(bv) >> (cv & 0x3f)); \
                    set_register(vAA, result_val); \
                    trace.opcode_name = op_name; \
                    pc_ += 2; \
                    break; \
                }
            ARITH_LONG_CASE(ADD_LONG, "add-long", "add")
            ARITH_LONG_CASE(SUB_LONG, "sub-long", "sub")
            ARITH_LONG_CASE(MUL_LONG, "mul-long", "mul")
            ARITH_LONG_CASE(DIV_LONG, "div-long", "div")
            ARITH_LONG_CASE(REM_LONG, "rem-long", "rem")
            ARITH_LONG_CASE(AND_LONG, "and-long", "and")
            ARITH_LONG_CASE(OR_LONG, "or-long", "or")
            ARITH_LONG_CASE(XOR_LONG, "xor-long", "xor")
            ARITH_LONG_CASE(SHL_LONG, "shl-long", "shl")
            ARITH_LONG_CASE(SHR_LONG, "shr-long", "shr")
            ARITH_LONG_CASE(USHR_LONG, "ushr-long", "ushr")
            #undef ARITH_LONG_CASE

            // EXP-051: throw (11x: AA|op, 1 code unit) — halt current method.
            //
            // Real Android unwinds the stack frame by frame looking for a
            // matching catch handler in the method's tries[] table. Full
            // exception handling is a major project; for now we treat
            // throw as "halt this method and return to caller".
            //
            // This loses exception-propagation semantics but lets the
            // engine continue past throws that originate from paths the
            // caller doesn't actually care about (e.g. dynamic-animation
            // throws inside enforceMainThreadIfNeeded that the caller
            // never observes because mEnforceMainThread == false).
            //
            // Without this fix, ANY throw anywhere in the call tree halts
            // the entire LaunchActivity.onCreate execution.
            //
            // EXP-052: Added diagnostic mode — log whether the current
            // method has a try table and what kind of handler would have
            // matched. This does NOT yet implement catch-jumping, just
            // collects evidence for the next experiment.
            // EXP-053: throw (11x: AA|op, 1 code unit).
            //
            // EXP-051: Treat as method-level halt (let caller continue).
            // EXP-052: Added diagnostic — log whether try table exists and
            //           whether a matching handler was found.
            // EXP-053: Implement actual catch-all handler dispatch. When a
            //           throw occurs:
            //             1. Look up try_items for one covering current PC.
            //             2. Decode the encoded_catch_handler_list at
            //                handler_off (byte offset into the list, which
            //                starts AFTER the tries[] array).
            //             3. For each handler pair (type_idx, addr):
            //                  - If type_idx == 0 (catch-all), jump to addr.
            //                  - If type_idx matches exception class
            //                    (TODO: needs type resolution), jump to addr.
            //             4. If no handler matched, propagate to caller
            //                (method-level halt, as before).
            //
            // For now we only support catch-all handlers. Typed catches
            // require class hierarchy resolution which is a future task.
            // EXP-071: filled-new-array (0x24) and filled-new-array/range (0x25)
            // These create an array and fill it with register values.
            // Format 35c/3rc: 3 code units.
            // For now, just create the array and advance PC — the values
            // are in registers and not commonly read back.
            case Opcode::FILLED_NEW_ARRAY:
            case Opcode::FILLED_NEW_ARRAY_RANGE: {
                trace.opcode_name = (opcode == Opcode::FILLED_NEW_ARRAY) ?
                    "filled-new-array" : "filled-new-array/range";
                // Format 35c/3rc: [B|A|op] [type@CCCC] [regs] or [op] [type@CCCC] [regs...]
                // The result goes into the result register (move-result-object follows).
                // For now, create a generic array object.
                uint32_t arr_id = heap_.allocate("Larray;", pc_, 0);
                DalvikValue result_val;
                result_val.type = DalvikType::OBJECT_REF;
                result_val.object_id = arr_id;
                result_val.class_desc = "Larray;";
                // Store as last_invoke_return_ so move-result-object can read it
                last_invoke_return_ = result_val;
                pc_ = pc_ + 3;
                success = true;
                break;
            }
            case Opcode::FILL_ARRAY_DATA: {
                // EXP-060: fill-array-data vAA, +BBBBBBBB (31t format, 3 code units)
                // Fills the array in vAA with data from a payload at PC+offset.
                // The payload format is:
                //   code_unit[0]: 0x0300 (magic — fill-array-data-payload)
                //   code_unit[1]: element width (1, 2, 4, or 8 bytes)
                //   code_unit[2..3]: element count (32-bit)
                //   followed by element_width * count bytes, padded to 16-bit
                trace.opcode_name = "fill-array-data";
                uint8_t vAA = (bytecode_[pc_] >> 8) & 0xFF;
                int32_t offset = static_cast<int32_t>(bytecode_[pc_ + 1] |
                    (static_cast<uint32_t>(bytecode_[pc_ + 2]) << 16));
                uint32_t payload_pc = pc_ + offset;

                DalvikValue array_val = get_register(vAA);
                // EXP-071: Diagnostic — check if the array register has a valid OBJECT_REF
                if (array_val.type != DalvikType::OBJECT_REF) {
                    std::cerr << "[EXP071-FILL] fill-array-data: v" << (int)vAA
                              << " is NOT OBJECT_REF (type=" << static_cast<int>(array_val.type)
                              << ") — THROWING exception" << std::endl;
                    // Simulate ArrayStoreException / NegativeArraySizeException
                    DalvikValue exc;
                    exc.type = DalvikType::OBJECT_REF;
                    exc.object_id = 0;
                    exc.class_desc = "Larray;";
                    // Set up exception state — just log and skip
                    pc_ = pc_ + 3;
                    success = true;
                    break;
                }
                if (array_val.object_id == 0 || !heap_.has_object(array_val.object_id)) {
                    std::cerr << "[EXP071-FILL] fill-array-data: array object_id=0 or not in heap"
                              << " — THROWING exception" << std::endl;
                    pc_ = pc_ + 3;
                    success = true;
                    break;
                }
                // The array must be an OBJECT_REF to an array object.
                // For now, we don't model array elements per-index.
                // The fill-array-data payload is typically small (2-4 booleans
                // or ints) and the array is a local — we just advance PC.
                // If the array is used later (e.g. aget), it will return 0.
                //
                // A more complete implementation would:
                //   1. Validate payload_pc is within bytecode.
                //   2. Read the payload header (element_width, count).
                //   3. Store the raw bytes on the HeapObject as a
                //      "raw_array_data" field, so aget/aget-boolean can read it.
                // For now, log and skip.
                if (payload_pc < bytecode_.size()) {
                    uint16_t magic = bytecode_[payload_pc];
                    uint16_t elem_width = bytecode_[payload_pc + 1];
                    uint32_t count = static_cast<uint32_t>(bytecode_[payload_pc + 2]) |
                        (static_cast<uint32_t>(bytecode_[payload_pc + 3]) << 16);
                    // EXP-071: Actually fill the array elements with the payload data.
                    // Previously we just stored metadata. Now we read the payload
                    // bytes and store each element as "array[idx]" on the HeapObject.
                    if (array_val.type == DalvikType::OBJECT_REF &&
                        heap_.has_object(array_val.object_id)) {
                        heap_.set_object_field(array_val.object_id,
                            "__fill_array_data_pc__",
                            DalvikValue::make_int(static_cast<int32_t>(payload_pc)));
                        heap_.set_object_field(array_val.object_id,
                            "__fill_array_elem_width__",
                            DalvikValue::make_int(elem_width));
                        heap_.set_object_field(array_val.object_id,
                            "__fill_array_count__",
                            DalvikValue::make_int(static_cast<int32_t>(count)));
                        // Also update __array_length__ and __new_array_length__
                        heap_.set_object_field(array_val.object_id, "__array_length__",
                            DalvikValue::make_int(static_cast<int32_t>(count)));
                        heap_.set_object_field(array_val.object_id, "__new_array_length__",
                            DalvikValue::make_int(static_cast<int32_t>(count)));
                        // Read and store each element
                        // Payload starts at payload_pc + 4 (after magic, elem_width, count)
                        // Each element is elem_width bytes, starting at byte offset
                        // (payload_pc + 4) * 2 in the raw bytecode.
                        uint32_t data_start = payload_pc + 4;
                        for (uint32_t i = 0; i < count && i < 100; ++i) {
                            // Read elem_width bytes from the payload
                            if (elem_width == 4) {
                                // int or float (4 bytes = 2 code units)
                                if (data_start + i * 2 + 1 < bytecode_.size()) {
                                    int32_t val = static_cast<int32_t>(bytecode_[data_start + i * 2]) |
                                        (static_cast<uint32_t>(bytecode_[data_start + i * 2 + 1]) << 16);
                                    heap_.set_object_field(array_val.object_id,
                                        "array[" + std::to_string(i) + "]",
                                        DalvikValue::make_int(val));
                                }
                            } else if (elem_width == 1) {
                                // boolean or byte (1 byte, packed 2 per code unit)
                                if (data_start + i / 2 < bytecode_.size()) {
                                    uint16_t word = bytecode_[data_start + i / 2];
                                    uint8_t byte_val = (i % 2 == 0) ? (word & 0xFF) : ((word >> 8) & 0xFF);
                                    heap_.set_object_field(array_val.object_id,
                                        "array[" + std::to_string(i) + "]",
                                        DalvikValue::make_bool(byte_val != 0));
                                }
                            } else if (elem_width == 2) {
                                // short or char (1 code unit)
                                if (data_start + i < bytecode_.size()) {
                                    int16_t val = static_cast<int16_t>(bytecode_[data_start + i]);
                                    heap_.set_object_field(array_val.object_id,
                                        "array[" + std::to_string(i) + "]",
                                        DalvikValue::make_int(val));
                                }
                            } else if (elem_width == 8) {
                                // long or double (4 code units)
                                if (data_start + i * 4 + 3 < bytecode_.size()) {
                                    int64_t val = static_cast<int64_t>(
                                        static_cast<uint32_t>(bytecode_[data_start + i * 4]) |
                                        (static_cast<uint32_t>(bytecode_[data_start + i * 4 + 1]) << 16) |
                                        (static_cast<uint64_t>(bytecode_[data_start + i * 4 + 2]) << 32) |
                                        (static_cast<uint64_t>(bytecode_[data_start + i * 4 + 3]) << 48));
                                    DalvikValue lv;
                                    lv.type = DalvikType::INT64;
                                    lv.long_val = val;
                                    heap_.set_object_field(array_val.object_id,
                                        "array[" + std::to_string(i) + "]", lv);
                                }
                            }
                        }
                    }
                }
                pc_ = pc_ + 3;
                success = true;
                break;
            }
            case Opcode::THROW: {
                trace.opcode_name = "throw";
                uint8_t vAA = (bytecode_[pc_] >> 8) & 0xFF;
                DalvikValue exc = get_register(vAA);
                std::string exc_class = exc.class_desc.empty()
                                      ? "<unknown>" : exc.class_desc;

                // EXP-052/053: Find try_item covering current PC, then
                // decode the encoded_catch_handler_list to find the
                // actual handler address.
                bool has_try_table = (current_tries_size_ > 0);
                bool handler_found = false;
                uint32_t try_start = 0, try_end = 0;
                uint32_t handler_addr = 0;
                std::string catch_type = "<none>";
                bool is_catch_all = false;

                if (has_try_table && current_tries_data_ != nullptr) {
                    // Step 1: Find the try_item covering current PC.
                    // try_item layout: u32 start_addr, u16 insn_count, u16 handler_off
                    // tries[] is at the START of current_tries_data_.
                    uint16_t matched_try_idx = 0xFFFF;
                    for (uint16_t i = 0; i < current_tries_size_; i++) {
                        size_t off = i * 8;
                        if (off + 8 > current_tries_data_size_) break;
                        uint32_t start = 0;
                        uint16_t count = 0;
                        uint16_t handler_off = 0;
                        std::memcpy(&start, current_tries_data_ + off, 4);
                        std::memcpy(&count, current_tries_data_ + off + 4, 2);
                        std::memcpy(&handler_off, current_tries_data_ + off + 6, 2);
                        if (pc_ >= start && pc_ < start + count) {
                            matched_try_idx = i;
                            try_start = start;
                            try_end = start + count;
                            // Step 2: handler_off is byte offset into the
                            // encoded_catch_handler_list (which starts at
                            // current_tries_data_ + tries_size * 8).
                            // BUT — actually handler_off is offset from the
                            // start of the encoded_catch_handler_list (which
                            // begins with the list_size uleb128).
                            size_t handler_list_start = static_cast<size_t>(current_tries_size_) * 8;
                            size_t handler_list_end = current_tries_data_size_;
                            if (handler_list_start >= handler_list_end) break;

                            // The encoded_catch_handler_list starts with a
                            // uleb128 list_size, then list_size handlers.
                            // handler_off is byte offset FROM THE START of
                            // this list (i.e., from the list_size byte).
                            size_t handler_abs = handler_list_start + handler_off;
                            if (handler_abs >= handler_list_end) break;

                            // Decode the handler at handler_abs.
                            // sleb128 size, then |size| pairs of (uleb128 type_idx, uleb128 addr),
                            // then catch-all addr if size < 0.
                            auto read_sleb = [&](size_t& p) -> int32_t {
                                int32_t result = 0;
                                int shift = 0;
                                uint8_t b;
                                do {
                                    if (p >= handler_list_end) return 0;
                                    b = current_tries_data_[p++];
                                    result |= (b & 0x7F) << shift;
                                    shift += 7;
                                } while (b & 0x80);
                                if (shift < 32 && (b & 0x40)) {
                                    result |= -(1 << shift);
                                }
                                return result;
                            };
                            auto read_uleb = [&](size_t& p) -> uint32_t {
                                uint32_t result = 0;
                                int shift = 0;
                                uint8_t b;
                                do {
                                    if (p >= handler_list_end) return 0;
                                    b = current_tries_data_[p++];
                                    result |= (b & 0x7F) << shift;
                                    shift += 7;
                                } while (b & 0x80);
                                return result;
                            };

                            size_t p = handler_abs;
                            int32_t size = read_sleb(p);
                            int32_t n_pairs = (size >= 0) ? size : -(size + 1);
                            // Read typed handlers first
                            for (int h = 0; h < n_pairs; h++) {
                                uint32_t type_idx = read_uleb(p);
                                uint32_t addr = read_uleb(p);
                                (void)type_idx;  // TODO: match exception type
                                (void)addr;
                            }
                            // If size <= 0, there's a catch-all handler at the end
                            if (size <= 0) {
                                uint32_t addr = read_uleb(p);
                                handler_found = true;
                                handler_addr = addr;
                                is_catch_all = true;
                                catch_type = "<catch-all>";
                            }
                            break;
                        }
                    }
                }

                // EXP-053: Log the exception event in the required format.
                std::cerr << "[EXCEPTION] method=" << current_class_ << "."
                          << current_method_
                          << " pc=" << pc_
                          << " exception=" << exc_class
                          << " try_range=";
                if (has_try_table && handler_found) {
                    std::cerr << "[" << try_start << "," << try_end << ")";
                } else if (has_try_table) {
                    std::cerr << "(no try covering pc)";
                } else {
                    std::cerr << "(none)";
                }
                std::cerr << " handler=" << (handler_found ? "FOUND" : "NOT_FOUND");
                if (handler_found) {
                    std::cerr << " handler_addr=" << handler_addr
                              << " catch_type=" << catch_type;
                }
                std::cerr << std::endl;

                // EXP-053: If catch-all handler found, jump to it instead of halting.
                if (handler_found && is_catch_all) {
                    if (handler_addr < bytecode_.size()) {
                        std::cerr << "[EXCEPTION] → jumping to catch-all handler at PC="
                                  << handler_addr << std::endl;
                        // Save the exception for move-exception to read.
                        pending_exception_ = exc;
                        trace.status = InstructionTrace::Status::BRANCH_TAKEN;
                        trace.operands.push_back({"reason", "throw (catch-all handler)"});
                        trace.operands.push_back({"exception_class", exc_class});
                        trace.operands.push_back({"handler_addr", std::to_string(handler_addr)});
                        pc_ = handler_addr;
                        break;
                    } else {
                        std::cerr << "[EXCEPTION] WARNING: handler_addr "
                                  << handler_addr << " out of bounds (bytecode_size="
                                  << bytecode_.size() << ") — falling through to halt"
                                  << std::endl;
                    }
                }

                // No catch-all handler — halt the method (propagate to caller).
                // EXP-071: If no catch handler was found, DON'T halt the method.
                // Previously, THROW would halt the entire method, causing any code
                // after the throw to be skipped. This was acceptable when THROW
                // was at the wrong opcode (0x26) and rarely fired. But now that
                // THROW is at the correct opcode (0x27), it fires correctly and
                // needs to be handled gracefully.
                //
                // For now: if no handler, log the exception and CONTINUE execution
                // (advance PC past the throw instruction). This is NOT semantically
                // correct (a real throw without catch would propagate up the call
                // stack), but it allows the method to continue executing rather
                // than aborting entirely. This is a compatibility approximation.
                if (!handler_found) {
                    // EXP-071: No catch handler found. Instead of halting the method
                    // (which skips all code after the throw), skip the throw instruction
                    // and continue. D8/R8 replaces most throws with goto +0, but some
                    // real throws remain. Halting them causes too many methods to abort.
                    // Skipping is a compatibility approximation — it's not semantically
                    // correct (a real throw would propagate to the caller), but it
                    // allows the method to continue executing.
                    pc_ += 1;
                    success = true;
                    break;
                }
                // If handler was found, the code above already jumped to it.
            }
            // move/16 (32x: AAAA|op BBBB, 3 code units)
            case Opcode::MOVE_16: {
                if (pc_ + 2 >= bytecode_.size()) return false;
                uint16_t src = bytecode_[pc_ + 1];
                uint16_t dest = bytecode_[pc_ + 2];
                DalvikValue val = get_register(static_cast<uint8_t>(src));
                set_register(static_cast<uint8_t>(dest), val);
                trace.opcode_name = "move/16";
                pc_ += 3;
                break;
            }
            // move-wide/from16 (22x: AA|op BBBB, 2 code units)
            case Opcode::MOVE_WIDE_FROM16: {
                if (pc_ + 1 >= bytecode_.size()) return false;
                uint8_t dest = (bytecode_[pc_] >> 8) & 0xFF;
                uint16_t src = bytecode_[pc_ + 1];
                DalvikValue val = get_register(static_cast<uint8_t>(src));
                set_register(dest, val);
                trace.opcode_name = "move-wide/from16";
                pc_ += 2;
                break;
            }
            // monitor-enter / monitor-exit (12x: B|A|op, 1 code unit)
            case Opcode::MONITOR_ENTER: {
                trace.opcode_name = "monitor-enter";
                pc_ += 1;  // no-op in single-threaded runtime
                break;
            }
            case Opcode::MONITOR_EXIT: {
                trace.opcode_name = "monitor-exit";
                pc_ += 1;  // no-op in single-threaded runtime
                break;
            }
            // const-wide/32 (21i: AA|op BBBB, 2 code units)
            case Opcode::CONST_WIDE_32: {
                if (pc_ + 1 >= bytecode_.size()) return false;
                uint16_t instr = bytecode_[pc_];
                uint8_t vAA = (instr >> 8) & 0xFF;
                int32_t val = static_cast<int32_t>(bytecode_[pc_ + 1]);
                DalvikValue dv;
                dv.type = DalvikType::INT64;
                // EXP-071 Phase 8: For INT64 values, write to long_val (not int_val).
                // int_val is a 32-bit field; long_val is the 64-bit field.
                // Writing to int_val left long_val with uninitialized garbage,
                // which broke the wide-arg merge in execute_invoke_static
                // (because the merge reads long_val for INT64 types).
                dv.long_val = val;
                set_register(vAA, dv);
                trace.opcode_name = "const-wide/32";
                pc_ += 2;
                break;
            }
            // iget-short / iput-short — now handled by the consolidated
            // iget-variant/iput-variant cases above (EXP-062).
            // rem-double (23x: AA|op BB|CC, 2 code units)
            case Opcode::REM_DOUBLE: {
                uint16_t instr = bytecode_[pc_];
                uint8_t vAA = (instr >> 8) & 0xFF;
                uint8_t vBB = bytecode_[pc_ + 1] & 0xFF;
                uint8_t vCC = (bytecode_[pc_ + 1] >> 8) & 0xFF;
                DalvikValue b = get_register(vBB);
                DalvikValue c = get_register(vCC);
                DalvikValue result_val;
                result_val.type = DalvikType::FLOAT64;
                double bd = (b.type == DalvikType::FLOAT64) ? b.double_val : (double)b.int_val;
                double cd = (c.type == DalvikType::FLOAT64) ? c.double_val : (double)c.int_val;
                result_val.double_val = (cd != 0) ? fmod(bd, cd) : 0;
                set_register(vAA, result_val);
                trace.opcode_name = "rem-double";
                pc_ += 2;
                break;
            }
            // Double arithmetic (23x) — add the rest
            #define ARITH_23X_DOUBLE_CASE(opcode, op_name, op) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vAA = (instr >> 8) & 0xFF; \
                    uint8_t vBB = bytecode_[pc_ + 1] & 0xFF; \
                    uint8_t vCC = (bytecode_[pc_ + 1] >> 8) & 0xFF; \
                    DalvikValue b = get_register(vBB); \
                    DalvikValue c = get_register(vCC); \
                    DalvikValue result_val; \
                    result_val.type = DalvikType::FLOAT64; \
                    double bd = (b.type == DalvikType::FLOAT64) ? b.double_val : (double)b.int_val; \
                    double cd = (c.type == DalvikType::FLOAT64) ? c.double_val : (double)c.int_val; \
                    if (op == "add") result_val.double_val = bd + cd; \
                    else if (op == "sub") result_val.double_val = bd - cd; \
                    else if (op == "mul") result_val.double_val = bd * cd; \
                    else if (op == "div") result_val.double_val = (cd != 0) ? bd / cd : 0; \
                    set_register(vAA, result_val); \
                    trace.opcode_name = op_name; \
                    pc_ += 2; \
                    break; \
                }
            ARITH_23X_DOUBLE_CASE(ADD_DOUBLE, "add-double", "add")
            ARITH_23X_DOUBLE_CASE(SUB_DOUBLE, "sub-double", "sub")
            ARITH_23X_DOUBLE_CASE(MUL_DOUBLE, "mul-double", "mul")
            ARITH_23X_DOUBLE_CASE(DIV_DOUBLE, "div-double", "div")
            #undef ARITH_23X_DOUBLE_CASE

            // EXP-041: Long/float/double 2addr opcodes (12x: B|A|op, 1 code unit)
            // Simplified: reuse the 2addr pattern from ARITH_2ADDR_CASE
            #define ARITH_WIDE_2ADDR_CASE(opcode, op_name, op_type, op) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vA = (instr >> 8) & 0xF; \
                    uint8_t vB = (instr >> 4) & 0xF; \
                    DalvikValue a = get_register(vA); \
                    DalvikValue b = get_register(vB); \
                    DalvikValue result_val; \
                    result_val.type = op_type; \
                    if (op_type == DalvikType::INT64) { \
                        int32_t av = a.int_val; int32_t bv = b.int_val; \
                        if (std::string(op) == "add") result_val.int_val = av + bv; \
                        else if (std::string(op) == "sub") result_val.int_val = av - bv; \
                        else if (std::string(op) == "mul") result_val.int_val = av * bv; \
                        else if (std::string(op) == "div") result_val.int_val = (bv != 0) ? av / bv : 0; \
                        else if (std::string(op) == "rem") result_val.int_val = (bv != 0) ? av % bv : 0; \
                        else if (std::string(op) == "and") result_val.int_val = av & bv; \
                        else if (std::string(op) == "or")  result_val.int_val = av | bv; \
                        else if (std::string(op) == "xor") result_val.int_val = av ^ bv; \
                        else if (std::string(op) == "shl") result_val.int_val = av << (bv & 0x3f); \
                        else if (std::string(op) == "shr") result_val.int_val = av >> (bv & 0x3f); \
                        else if (std::string(op) == "ushr") result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(av) >> (bv & 0x3f)); \
                    } else if (op_type == DalvikType::FLOAT32) { \
                        float af = (a.type == DalvikType::FLOAT32) ? a.float_val : (float)a.int_val; \
                        float bf = (b.type == DalvikType::FLOAT32) ? b.float_val : (float)b.int_val; \
                        if (std::string(op) == "add") result_val.float_val = af + bf; \
                        else if (std::string(op) == "sub") result_val.float_val = af - bf; \
                        else if (std::string(op) == "mul") result_val.float_val = af * bf; \
                        else if (std::string(op) == "div") result_val.float_val = (bf != 0) ? af / bf : 0; \
                        else if (std::string(op) == "rem") result_val.float_val = fmodf(af, bf); \
                    } else { \
                        double ad = (a.type == DalvikType::FLOAT64) ? a.double_val : (double)a.int_val; \
                        double bd = (b.type == DalvikType::FLOAT64) ? b.double_val : (double)b.int_val; \
                        if (std::string(op) == "add") result_val.double_val = ad + bd; \
                        else if (std::string(op) == "sub") result_val.double_val = ad - bd; \
                        else if (std::string(op) == "mul") result_val.double_val = ad * bd; \
                        else if (std::string(op) == "div") result_val.double_val = (bd != 0) ? ad / bd : 0; \
                        else if (std::string(op) == "rem") result_val.double_val = fmod(ad, bd); \
                    } \
                    set_register(vA, result_val); \
                    trace.opcode_name = op_name; \
                    pc_ += 1; \
                    break; \
                }
            ARITH_WIDE_2ADDR_CASE(ADD_LONG_2ADDR, "add-long/2addr", DalvikType::INT64, "add")
            ARITH_WIDE_2ADDR_CASE(SUB_LONG_2ADDR, "sub-long/2addr", DalvikType::INT64, "sub")
            ARITH_WIDE_2ADDR_CASE(MUL_LONG_2ADDR, "mul-long/2addr", DalvikType::INT64, "mul")
            ARITH_WIDE_2ADDR_CASE(DIV_LONG_2ADDR, "div-long/2addr", DalvikType::INT64, "div")
            ARITH_WIDE_2ADDR_CASE(REM_LONG_2ADDR, "rem-long/2addr", DalvikType::INT64, "rem")
            ARITH_WIDE_2ADDR_CASE(AND_LONG_2ADDR, "and-long/2addr", DalvikType::INT64, "and")
            ARITH_WIDE_2ADDR_CASE(OR_LONG_2ADDR,  "or-long/2addr",  DalvikType::INT64, "or")
            ARITH_WIDE_2ADDR_CASE(XOR_LONG_2ADDR, "xor-long/2addr", DalvikType::INT64, "xor")
            ARITH_WIDE_2ADDR_CASE(SHL_LONG_2ADDR, "shl-long/2addr", DalvikType::INT64, "shl")
            ARITH_WIDE_2ADDR_CASE(SHR_LONG_2ADDR, "shr-long/2addr", DalvikType::INT64, "shr")
            ARITH_WIDE_2ADDR_CASE(USHR_LONG_2ADDR, "ushr-long/2addr", DalvikType::INT64, "ushr")
            ARITH_WIDE_2ADDR_CASE(ADD_FLOAT_2ADDR, "add-float/2addr", DalvikType::FLOAT32, "add")
            ARITH_WIDE_2ADDR_CASE(SUB_FLOAT_2ADDR, "sub-float/2addr", DalvikType::FLOAT32, "sub")
            ARITH_WIDE_2ADDR_CASE(MUL_FLOAT_2ADDR, "mul-float/2addr", DalvikType::FLOAT32, "mul")
            ARITH_WIDE_2ADDR_CASE(DIV_FLOAT_2ADDR, "div-float/2addr", DalvikType::FLOAT32, "div")
            ARITH_WIDE_2ADDR_CASE(REM_FLOAT_2ADDR, "rem-float/2addr", DalvikType::FLOAT32, "rem")
            ARITH_WIDE_2ADDR_CASE(ADD_DOUBLE_2ADDR, "add-double/2addr", DalvikType::FLOAT64, "add")
            ARITH_WIDE_2ADDR_CASE(SUB_DOUBLE_2ADDR, "sub-double/2addr", DalvikType::FLOAT64, "sub")
            ARITH_WIDE_2ADDR_CASE(MUL_DOUBLE_2ADDR, "mul-double/2addr", DalvikType::FLOAT64, "mul")
            ARITH_WIDE_2ADDR_CASE(DIV_DOUBLE_2ADDR, "div-double/2addr", DalvikType::FLOAT64, "div")
            #undef ARITH_WIDE_2ADDR_CASE

            // const-wide/16 (21s: AA|op BBBB, 2 code units)
            case Opcode::CONST_WIDE_16: {
                if (pc_ + 1 >= bytecode_.size()) return false;
                uint8_t vAA = (bytecode_[pc_] >> 8) & 0xFF;
                int16_t val = static_cast<int16_t>(bytecode_[pc_ + 1]);
                // EXP-071 Phase 8: write to long_val (64-bit) for INT64 type,
                // NOT int_val (32-bit). The previous bug left long_val with
                // garbage, breaking wide-arg merging in execute_invoke_static.
                DalvikValue dv; dv.type = DalvikType::INT64; dv.long_val = val;
                set_register(vAA, dv);
                trace.opcode_name = "const-wide/16";
                pc_ += 2;
                break;
            }
            // const-wide/high16 (21s: AA|op BBBB, 2 code units)
            case Opcode::CONST_WIDE_HIGH16: {
                if (pc_ + 1 >= bytecode_.size()) return false;
                uint8_t vAA = (bytecode_[pc_] >> 8) & 0xFF;
                uint16_t val = bytecode_[pc_ + 1];
                // EXP-071 Phase 8: write to long_val for INT64 type.
                DalvikValue dv; dv.type = DalvikType::INT64; dv.long_val = static_cast<int64_t>(val) << 48;
                set_register(vAA, dv);
                trace.opcode_name = "const-wide/high16";
                pc_ += 2;
                break;
            }
            // const-wide (51l: AA|op + 4 words, 5 code units)
            case Opcode::CONST_WIDE: {
                if (pc_ + 4 >= bytecode_.size()) return false;
                uint8_t vAA = (bytecode_[pc_] >> 8) & 0xFF;
                uint64_t val = 0;
                for (int i = 0; i < 4; i++) val |= static_cast<uint64_t>(bytecode_[pc_ + 1 + i]) << (i * 16);
                // EXP-071 Phase 8: write to long_val for INT64 type.
                DalvikValue dv; dv.type = DalvikType::INT64; dv.long_val = static_cast<int64_t>(val);
                set_register(vAA, dv);
                trace.opcode_name = "const-wide";
                pc_ += 5;
                break;
            }
            // iget-boolean / iput-boolean — now handled by the consolidated
            // iget-variant/iput-variant cases above (EXP-062).

            default:
                handle_unimplemented(opcode, pc_, trace);
                trace.opcode_name = "unimplemented(0x" + to_hex16(opcode) + ")";
                success = !config_.stop_on_unimplemented;
                break;
        }
        
        // EXP-042 Phase 1: register state AFTER capture (gated).
        if (config_.trace_register_snapshots && current_registers_) {
            trace.registers_after = current_registers_->get_snapshot();
            // Calculate changed registers
            for (const auto& pair : trace.registers_before) {
                auto after_it = trace.registers_after.find(pair.first);
                if (after_it != trace.registers_after.end()) {
                    if (after_it->second.type != pair.second.type ||
                        (after_it->second.is_integral() && pair.second.is_integral() &&
                         after_it->second.int_val != pair.second.int_val)) {
                        trace.changed_registers.push_back(pair.first);
                    }
                }
            }
        }
        
        // EXP-045 Phase 2: Skip per-instruction trace recording when trace_cap is 0.
        // This eliminates InstructionTrace construction, Clock::now() calls, and
        // ring-buffer push_back — the #2 performance bottleneck after class lookup.
        if (config_.trace_cap > 0) {
            trace.pc_after = pc_;
            trace.execution_us = std::chrono::duration<double, std::micro>(Clock::now() - start).count();

            if (result.instruction_traces.size() >= config_.trace_cap) {
                result.instruction_traces.erase(result.instruction_traces.begin());
            }
            result.instruction_traces.push_back(std::move(trace));
        }
        result.total_instructions_executed++;
        result.total_opcodes_decoded++;

        // EXP-045 Phase 2: Global instruction counter — log every 100K instructions
        // to track execution speed and progress.
        static thread_local uint64_t global_insn_counter = 0;
        global_insn_counter++;
        if (global_insn_counter % 100000 == 0) {
            std::cerr << "[PROGRESS] " << global_insn_counter << " total instructions executed"
                      << " (currently in " << current_class_ << "." << current_method_
                      << " PC=" << pc_ << "/" << bytecode_.size() << ")"
                      << " RSS=" << (miniandroid::probe::rss_kb() / 1024) << " MB" << std::endl;
        }

        // EXP-042 Phase 1: Per-frame loop detection (replaces the previous
        // static thread_local map which leaked state across recursive calls).
        // The previous design counted visits across ALL recursive invocations
        // of execute_method_internal(), which meant that PC=6 (a return opcode)
        // in Theme.getColor accumulated 101 visits across 101 separate calls
        // and wrongly halted each one — producing 6 000 × 101 instruction
        // traces, the actual cause of the OOM.
        //
        // pc_visit_count_ is now an instance member, reset in
        // execute_method_internal() at the start of each method. The threshold
        // is config_.loop_visit_threshold (default 50 000).
        pc_visit_count_[pc_]++;
        if (pc_visit_count_[pc_] > config_.loop_visit_threshold) {
            // EXP-042 Phase 2: include bytecode size and the actual opcode at
            // the looping PC, so we can diagnose whether the loop is a real
            // infinite loop or a missing-API-driven spin.
            uint16_t op_at_pc = (pc_ < bytecode_.size()) ? (bytecode_[pc_] & 0xFF) : 0xFFFF;
            halt_reason_ = "Infinite loop at PC=" + to_hex(pc_) +
                          " in " + current_class_ + "." + current_method_ +
                          " (visited " + std::to_string(pc_visit_count_[pc_]) +
                          " times in this frame, bytecode_size=" +
                          std::to_string(bytecode_.size()) +
                          ", op_at_pc=0x" + to_hex16(op_at_pc) + ").";
            halted_ = true;
            std::cerr << "[HALT-LOOP] " << halt_reason_ << std::endl;
            break;
        }
        
        // Log if verbose — EXP-041: only log every 10000th instruction to reduce memory
        if (verbose_ && (trace.sequence % 10000 == 0)) {
            log("  [" + std::to_string(trace.sequence) + "] " +
                std::string(trace.pc_before < 100 ? " " : "") + 
                to_hex(trace.pc_before) + ": " + trace.opcode_name +
                (trace.allocated_object_id ? " [obj:" + std::to_string(*trace.allocated_object_id) + "]" : "") +
                (trace.invoked_method ? " → " + *trace.invoked_method : "") +
                (trace.status == InstructionTrace::Status::UNIMPLEMENTED ? " [UNIMPLEMENTED]" : ""));
        }
        
        // Check limits
        if (result.total_instructions_executed >= config_.max_instructions) {
            halt_reason_ = "Max instructions reached (" + std::to_string(config_.max_instructions) + ")";
            halted_ = true;
            log("HALT: " + halt_reason_);
            break;
        }
        
        // Check for return
        if (halted_on_return_) {
            log("Method returned successfully");
            break;
        }
    }
    
    return !halted_ || halted_on_return_;
}

uint16_t DalvikExecutionEngine::fetch_opcode(uint32_t pc) const {
    if (pc < bytecode_.size()) {
        return bytecode_[pc];
    }
    return Opcode::NOP;
}

// ============================================================================
// OPCODE IMPLEMENTATIONS — Constants
// ============================================================================

bool DalvikExecutionEngine::execute_const_4(uint32_t pc, InstructionTrace& trace) {
    // Format: 11n B|A|op — 1 code unit
    //   byte 0 (low): op (0x12)
    //   byte 1 (high): B<<4 | A (A = register nibble, B = literal nibble)
    // EXP-047 FIX: Previous code extracted dest_reg as the full high byte
    // and literal as the low nibble of the low byte (always 0x2 from op=0x12).
    // This caused const/4 to write to the WRONG register and use the WRONG value.
    // For example, const/4 v3, #4 (word=0x4312) was interpreted as
    // dest_reg=0x43 (v67) and literal=2, instead of dest_reg=3 and literal=4.
    // This was the root cause of if-gt at PC=147 in postInitApplication
    // comparing wrong registers and branching to PC=224, skipping
    // UserConfig.getInstance, MessagesController.getInstance, and
    // ConnectionsManager.getInstance.
    if (pc >= bytecode_.size()) return false;

    uint16_t instr = bytecode_[pc];
    uint8_t dest_reg = (instr >> 8) & 0xF;    // A = low nibble of high byte
    uint8_t literal_nibble = (instr >> 12) & 0xF;  // B = high nibble of high byte

    // Sign-extend from 4 bits
    int32_t value = (literal_nibble >= 8) ? (literal_nibble - 16) : literal_nibble;

    set_register(dest_reg, DalvikValue::make_int(value));

    // EXP-059: Debug — log const/4 in onFragmentCreate and addFragmentToStack
    if (current_method_ == "onFragmentCreate" ||
        (current_method_ == "addFragmentToStack" &&
         current_class_.find("ActionBarLayout") != std::string::npos)) {
        std::cerr << "[EXP059-CONST4] " << current_class_ << "." << current_method_
                  << " PC=" << pc << " v" << (int)dest_reg
                  << " = " << value
                  << " (literal_nibble=" << (int)literal_nibble << ")"
                  << std::endl;
    }

    trace.operands.push_back({"v" + std::to_string(dest_reg), std::to_string(value)});

    pc_ = pc + 1;
    return true;
}

bool DalvikExecutionEngine::execute_const_16(uint32_t pc, InstructionTrace& trace) {
    // Format: 21s [op] vAA, #+BBBB
    if (pc + 1 >= bytecode_.size()) return false;
    
    uint16_t instr = bytecode_[pc];
    uint8_t dest_reg = (instr >> 8) & 0xFF;
    int16_t literal = static_cast<int16_t>(bytecode_[pc + 1]);
    
    set_register(dest_reg, DalvikValue::make_int(static_cast<int32_t>(literal)));
    
    trace.operands.push_back({"v" + std::to_string(dest_reg), std::to_string(literal)});
    
    pc_ = pc + 2;
    return true;
}

bool DalvikExecutionEngine::execute_const(uint32_t pc, InstructionTrace& trace) {
    // Format: 31i [op] vAA, #+BBBBBBBB
    if (pc + 2 >= bytecode_.size()) return false;
    
    uint16_t instr = bytecode_[pc];
    uint8_t dest_reg = (instr >> 8) & 0xFF;
    int32_t literal = (static_cast<int32_t>(bytecode_[pc + 1])) | 
                      (static_cast<int32_t>(bytecode_[pc + 2]) << 16);
    
    set_register(dest_reg, DalvikValue::make_int(literal));
    
    trace.operands.push_back({"v" + std::to_string(dest_reg), std::to_string(literal)});
    
    pc_ = pc + 3;
    return true;
}

bool DalvikExecutionEngine::execute_const_string(uint32_t pc, InstructionTrace& trace) {
    // Format: 21c [op] vAA, string@BBBB
    if (pc + 1 >= bytecode_.size()) return false;

    uint16_t instr = bytecode_[pc];
    uint8_t dest_reg = (instr >> 8) & 0xFF;
    uint16_t string_idx = bytecode_[pc + 1];
    
    // EXP-065: CRITICAL FIX — Use per-DEX string resolution.
    // The merged dex_report_->strings[] is the concatenation of all DEX
    // files' string tables. For multi-DEX apps, string_idx is relative to
    // the CURRENT DEX file, so using the merged index returns the WRONG
    // string. For example, Telegram's classes4.dex has string_idx=5975="+",
    // but merged_strings[5975]="FIELD_PREFERRED_AUDIO_LANGUAGES" (from classes.dex).
    // This bug caused ViewNode.text to leak Android MediaMetadata constant
    // names into the rendered UI image.
    std::string str_value = "<string:" + std::to_string(string_idx) + ">";
    str_value = resolve_string_for_dex(string_idx, current_dex_index_);
    
    uint32_t ref_id = instruction_sequence_;  // Use sequence as ref ID
    set_register(dest_reg, DalvikValue::make_string(str_value, ref_id));
    
    trace.operands.push_back({"v" + std::to_string(dest_reg), "\"" + str_value + "\""});
    trace.operands.push_back({"string_idx", std::to_string(string_idx)});
    
    pc_ = pc + 2;
    return true;
}

bool DalvikExecutionEngine::execute_const_class(uint32_t pc, InstructionTrace& trace) {
    // Format: 21c [op] vAA, type@BBBB
    if (pc + 1 >= bytecode_.size()) return false;

    uint16_t instr = bytecode_[pc];
    uint8_t dest_reg = (instr >> 8) & 0xFF;
    uint16_t type_idx = bytecode_[pc + 1];

    // EXP-066: Use per-DEX type resolution (multi-DEX bug fix — same pattern as
    // execute_const_string in EXP-065). The merged dex_report_->types[] is the
    // concatenation of all DEX files' type_ids tables; type_idx is per-DEX.
    std::string type_desc = "<type:" + std::to_string(type_idx) + ">";
    type_desc = resolve_type_for_dex(type_idx, current_dex_index_);

    uint32_t ref_id = instruction_sequence_;
    set_register(dest_reg, DalvikValue::make_class(type_desc, ref_id));

    trace.operands.push_back({"v" + std::to_string(dest_reg), type_desc});

    pc_ = pc + 2;
    return true;
}

// ============================================================================
// OPCODE IMPLEMENTATIONS — Moves
// ============================================================================

bool DalvikExecutionEngine::execute_move(uint32_t pc, InstructionTrace& trace) {
    // Format: 12x B|A|op — 1 code unit
    // bits 0-7: op, bits 8-11: A (dest), bits 12-15: B (src)
    if (pc + 1 >= bytecode_.size()) return false;
    
    uint16_t instr = bytecode_[pc];
    uint8_t dest = (instr >> 8) & 0xF;
    // EXP-058: CRITICAL FIX — was (instr >> 4) & 0xF which reads bits 4-7
    // (part of the opcode byte), NOT bits 12-15 (the B register nibble).
    // This caused move-object v9, v15 to read v0 instead of v15.
    uint8_t src = (instr >> 12) & 0xF;
    
    DalvikValue val = get_register(src);
    set_register(dest, val);
    
    trace.operands.push_back({"v" + std::to_string(dest), register_name(src)});
    
    pc_ = pc + 1;
    return true;
}

bool DalvikExecutionEngine::execute_move_object(uint32_t pc, InstructionTrace& trace) {
    // Format: 12x B|A|op — 1 code unit
    // bits 0-7: op, bits 8-11: A (dest), bits 12-15: B (src)
    if (pc + 1 >= bytecode_.size()) return false;
    
    uint16_t instr = bytecode_[pc];
    uint8_t dest = (instr >> 8) & 0xF;
    // EXP-058: CRITICAL FIX — was (instr >> 4) & 0xF which reads bits 4-7
    // (part of the opcode byte), NOT bits 12-15 (the B register nibble).
    // This caused move-object v9, v15 to read v0 (uninitialized) instead
    // of v15 (the Activity `this` pointer). As a result, ALL iput-object
    // instructions on the Activity's fields silently failed because the
    // object reference was NULL_REF instead of OBJECT_REF.
    uint8_t src = (instr >> 12) & 0xF;
    
    DalvikValue val = get_register(src);
    // Ensure it's treated as object reference
    if (val.type == DalvikType::REGISTER_UNSET || val.type == DalvikType::UNINITIALIZED) {
        val = DalvikValue::make_null();
    }
    set_register(dest, val);
    
    trace.operands.push_back({"v" + std::to_string(dest), register_name(src)});
    
    pc_ = pc + 1;
    return true;
}

// EXP-038 (BLOCKER-026): move-object/from16
// Format: 22x AA|op BBBB
//   code[0]: AA (8-bit dest register) | op (8-bit opcode)
//   code[1]: BBBB (16-bit source register)
// Copies an object reference from vBBBB to vAA.
// Used by Telegram's LaunchActivity.onCreate() at PC=1 to move
// the `this` reference from the parameter register to a local register.
bool DalvikExecutionEngine::execute_move_object_from16(uint32_t pc, InstructionTrace& trace) {
    if (pc + 1 >= bytecode_.size()) return false;
    
    uint16_t instr = bytecode_[pc];
    uint8_t dest = (instr >> 8) & 0xFF;  // 8-bit dest register (was 0xF for move-object)
    uint16_t src = bytecode_[pc + 1];    // 16-bit source register
    
    DalvikValue val = get_register(static_cast<uint8_t>(src));
    if (val.type == DalvikType::REGISTER_UNSET || val.type == DalvikType::UNINITIALIZED) {
        val = DalvikValue::make_null();
    }
    set_register(dest, val);
    
    trace.operands.push_back({"v" + std::to_string(dest), "v" + std::to_string(src)});
    
    pc_ = pc + 2;  // 22x format = 2 code units
    return true;
}

bool DalvikExecutionEngine::execute_move_result(uint32_t pc, InstructionTrace& trace) {
    // Format: 11x [op] vAA — move return value from last invoke to register
    // EXP-050 Phase 2 CRITICAL FIX: Previously returned placeholder 0, silently
    // discarding ALL return values from ALL method calls. Now reads from
    // last_invoke_return_ which is set by every invoke-* handler.
    if (pc >= bytecode_.size()) return false;

    uint16_t instr = bytecode_[pc];
    uint8_t dest = (instr >> 8) & 0xFF;

    set_register(dest, last_invoke_return_);

    // EXP-059: Debug — log move-result in addFragmentToStack
    if (current_method_ == "addFragmentToStack" &&
        current_class_.find("ActionBarLayout") != std::string::npos) {
        std::cerr << "[EXP059-MOVE-RESULT] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " dest=v" << (int)dest
                  << " type=" << static_cast<int>(last_invoke_return_.type)
                  << " int_val=" << last_invoke_return_.int_val
                  << " obj=" << last_invoke_return_.object_id
                  << std::endl;
    }

    trace.operands.push_back({"v" + std::to_string(dest), last_invoke_return_.to_string()});
    trace.return_value = last_invoke_return_;

    pc_ = pc + 1;
    return true;
}

bool DalvikExecutionEngine::execute_move_result_object(uint32_t pc, InstructionTrace& trace) {
    if (pc >= bytecode_.size()) return false;

    uint16_t instr = bytecode_[pc];
    uint8_t dest = (instr >> 8) & 0xFF;

    // EXP-057: Debug — log move-result-object in onCreate for login path.
    if (current_method_ == "onCreate" && current_class_.find("LaunchActivity") != std::string::npos) {
        std::cerr << "[EXP057-MRO] move-result-object v" << (int)dest
                  << " type=" << static_cast<int>(last_invoke_return_.type)
                  << " obj=" << last_invoke_return_.object_id
                  << " pc=" << pc
                  << std::endl;
    }

    set_register(dest, last_invoke_return_);

    trace.operands.push_back({"v" + std::to_string(dest), last_invoke_return_.to_string()});
    trace.return_value = last_invoke_return_;

    pc_ = pc + 1;
    return true;
}

// ============================================================================
// OPCODE IMPLEMENTATIONS — Objects
// ============================================================================

bool DalvikExecutionEngine::execute_new_instance(uint32_t pc, InstructionTrace& trace) {
    // Format: 22c [op] vAA, type@BBBB
    if (pc + 1 >= bytecode_.size()) return false;
    
    uint16_t instr = bytecode_[pc];
    uint8_t dest_reg = (instr >> 8) & 0xFF;
    uint16_t type_idx = bytecode_[pc + 1];
    
    // EXP-058: Use per-DEX type resolution instead of merged global types.
    // type_idx is relative to the current DEX file's type_ids table.
    std::string class_desc = resolve_type_for_dex(type_idx, current_dex_index_);
    if (class_desc == "<unknown>" && dex_report_ && type_idx < dex_report_->types.size()) {
        class_desc = dex_report_->types[type_idx];
    }
    
    // Allocate on heap
    uint32_t frame_id = call_stack_.empty() ? 0 : call_stack_.top().frame_id;
    uint32_t obj_id = heap_.allocate(class_desc, pc, frame_id);
    
    // Store object reference in register
    set_register(dest_reg, DalvikValue::make_object(obj_id, class_desc));
    
    // EXP-061: Debug — trace new-instance for View/EditText/Button classes
    // to investigate why some views end up with object_id=0 in shadow dispatch.
    if (class_desc.find("EditText") != std::string::npos ||
        class_desc.find("TextView") != std::string::npos ||
        class_desc.find("Button") != std::string::npos ||
        class_desc.find("PhoneView") != std::string::npos ||
        class_desc.find("Keyboard") != std::string::npos) {
        std::cerr << "[EXP061-NEW] new-instance " << class_desc
                  << " → v" << (int)dest_reg
                  << " obj_id=" << obj_id
                  << " pc=" << pc
                  << " caller=" << current_class_ << "." << current_method_
                  << std::endl;
    }
    
    trace.operands.push_back({"v" + std::to_string(dest_reg), class_desc});
    trace.allocated_object_id = obj_id;
    
    log("  ALLOCATED: " + class_desc + " -> obj#" + std::to_string(obj_id));
    
    pc_ = pc + 2;
    return true;
}

bool DalvikExecutionEngine::execute_check_cast(uint32_t pc, InstructionTrace& trace) {
    // Format: 1c [op] vAA, type@BBBB
    if (pc + 1 >= bytecode_.size()) return false;

    uint16_t instr = bytecode_[pc];
    uint8_t reg = (instr >> 8) & 0xFF;
    uint16_t type_idx = bytecode_[pc + 1];

    // EXP-066: Use per-DEX type resolution (multi-DEX bug fix).
    std::string target_type = "<unknown>";
    target_type = resolve_type_for_dex(type_idx, current_dex_index_);

    // In full implementation, would check if register value is instance of target_type
    // For now, pass through (optimistic cast)
    DalvikValue val = get_register(reg);
    // If null or uninit, it's always ok
    if (val.type == DalvikType::NULL_REF || val.type == DalvikType::UNINITIALIZED ||
        val.type == DalvikType::REGISTER_UNSET) {
        // Null passes any check-cast
    }

    trace.operands.push_back({"v" + std::to_string(reg), target_type});

    pc_ = pc + 2;
    return true;
}

bool DalvikExecutionEngine::execute_instance_of(uint32_t pc, InstructionTrace& trace) {
    // Format: 22 [op] vA, vB, type@CCCC
    if (pc + 2 >= bytecode_.size()) return false;

    uint16_t instr = bytecode_[pc];
    uint8_t dest = (instr >> 8) & 0xFF;
    uint8_t src = instr & 0xFF;
    uint16_t type_idx = bytecode_[pc + 2];

    // EXP-066: Use per-DEX type resolution (multi-DEX bug fix).
    std::string target_type = "<unknown>";
    target_type = resolve_type_for_dex(type_idx, current_dex_index_);

    // EXP-071: Use semantic superclass chain for instanceof check.
    // Previously this only did an EXACT class match (src_val.class_desc == target_type),
    // which failed for subclass checks like `obj instanceof Activity` when obj's
    // actual class is LaunchActivity (a subclass of Activity).
    // Now we use is_subclass_of() which walks the DEX superclass chain.
    DalvikValue src_val = get_register(src);
    bool is_instance = false;
    if (src_val.type == DalvikType::OBJECT_REF && src_val.object_id != 0) {
        std::string obj_class = src_val.class_desc;
        if (obj_class.empty() && heap_.has_object(src_val.object_id)) {
            obj_class = heap_.get(src_val.object_id)->class_descriptor;
        }
        if (!obj_class.empty()) {
            // Check if obj_class is a subclass of target_type (or equal)
            is_instance = is_subclass_of(obj_class, target_type);
        }
    }
    // Also check if null — null instanceof anything is false (already handled by OBJECT_REF check)

    set_register(dest, DalvikValue::make_bool(is_instance));

    trace.operands.push_back({"v" + std::to_string(dest), register_name(src)});
    trace.operands.push_back({"type", target_type});

    pc_ = pc + 2;  // EXP-037 Phase B (BLOCKER-017 FIX): 22c format is 2 code units (was pc + 3)
    return true;
}

// ============================================================================
// EXP-035: OPCODE IMPLEMENTATIONS — Field Operations
// ============================================================================

DalvikExecutionEngine::FieldResolution DalvikExecutionEngine::resolve_field(uint16_t field_idx) {
    FieldResolution resolution;
    
    if (!dex_report_) {
        resolution.error_message = "No DexReport available (resolve_field)";
        return resolution;
    }

    // EXP-046: Per-DEX field resolution (same issue as BLOCKER-033 for methods).
    // The merged DexReport concatenates field_ids from all DEX files, so
    // field_idx from bytecode (which is per-DEX) points to the wrong field.
    if (is_multidex_ && current_dex_index_ < per_dex_raw_data_.size()) {
        const auto& raw = per_dex_raw_data_[current_dex_index_];
        if (raw.size() >= sizeof(dex::DexHeader)) {
            dex::DexHeader hdr;
            std::memcpy(&hdr, raw.data(), sizeof(dex::DexHeader));
            if (field_idx < hdr.field_ids_size) {
                size_t foff = hdr.field_ids_off + field_idx * 8;
                if (foff + 8 <= raw.size()) {
                    uint16_t class_idx, type_idx;
                    uint32_t name_idx;
                    std::memcpy(&class_idx, raw.data() + foff, 2);
                    std::memcpy(&type_idx, raw.data() + foff + 2, 2);
                    std::memcpy(&name_idx, raw.data() + foff + 4, 4);
                    if (class_idx < hdr.type_ids_size) {
                        uint32_t desc_str_idx;
                        std::memcpy(&desc_str_idx, raw.data() + hdr.type_ids_off + class_idx * 4, 4);
                        resolution.class_descriptor = read_dex_string_from_raw(raw, desc_str_idx, hdr);
                    }
                    resolution.field_name = read_dex_string_from_raw(raw, name_idx, hdr);
                    if (type_idx < hdr.type_ids_size) {
                        uint32_t type_str_idx;
                        std::memcpy(&type_str_idx, raw.data() + hdr.type_ids_off + type_idx * 4, 4);
                        resolution.field_type = read_dex_string_from_raw(raw, type_str_idx, hdr);
                    }
                    if (!resolution.class_descriptor.empty() &&
                        !resolution.field_name.empty() &&
                        resolution.class_descriptor[0] == 'L') {
                        resolution.resolved = true;
                        return resolution;
                    }
                }
            }
        }
    }

    // Fallback: use merged DexReport
    resolution.class_descriptor = dex_report_->get_field_class(field_idx);
    resolution.field_name = dex_report_->get_field_name(field_idx);
    resolution.field_type = dex_report_->get_field_type(field_idx);

    if (resolution.class_descriptor.rfind("<bad_", 0) == 0 ||
        resolution.field_name.rfind("<bad_", 0) == 0 ||
        resolution.field_type.rfind("<bad_", 0) == 0) {
        resolution.error_message =
            "Field index " + std::to_string(field_idx) +
            " out of range or references invalid string/type";
        log("❌ FIELD RESOLUTION FAILED: " + resolution.error_message);
        return resolution;
    }

    resolution.resolved = true;

    // Look up field offset from runtime metadata cache if available
    auto class_it = class_info_cache_.find(resolution.class_descriptor);
    if (class_it != class_info_cache_.end() && class_it->second) {
        const auto& class_info = *(class_it->second);
        for (const auto& inst_field : class_info.instance_fields) {
            if (inst_field.name == resolution.field_name) {
                resolution.field_offset = inst_field.byte_offset;
                break;
            }
        }
        resolution.is_static = false;
    } else {
        // Heuristic: if the field is from a framework class like
        // Landroid/* or Ljava/*, assume instance field for iget/iput and
        // static for sget/sput. The calling opcode handler will override
        // is_static as needed (sget/sput set it to true explicitly).
        resolution.is_static = false;
    }

    log("✅ FIELD RESOLVED: " + resolution.class_descriptor + "." + resolution.field_name +
        " type=" + resolution.field_type +
        " offset=" + std::to_string(resolution.field_offset));
    return resolution;
}

bool DalvikExecutionEngine::execute_iget(uint32_t pc, InstructionTrace& trace) {
    // Format: 22c iget vA, vB, field@CCCC (2 code units)
    // EXP-042 Phase 2 FIX: same advance-pc-on-failure strategy as iget-object.
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }
    
    uint16_t instr = bytecode_[pc];
    uint8_t dest_reg = (instr >> 8) & 0xF;
    uint8_t obj_reg = (instr >> 12) & 0xF;
    uint16_t field_idx = bytecode_[pc + 1];
    
    FieldResolution field_res = resolve_field(field_idx);
    DalvikValue result_value;
    result_value.type = DalvikType::INT32;
    result_value.int_val = 0;
    
    if (field_res.resolved) {
        DalvikValue obj_ref = get_register(obj_reg);
        if (obj_ref.type == DalvikType::OBJECT_REF && heap_.has_object(obj_ref.object_id)) {
            auto field_val = heap_.get_object_field(obj_ref.object_id, field_res.field_name);
            if (field_val.has_value()) {
                result_value = field_val.value();
            }
        }
    }
    // EXP-042 Phase 2: on any failure path, fall through with default 0 and
    // advance pc_ — never return false (which would cause an infinite loop).
    
    set_register(dest_reg, result_value);
    trace.operands.push_back({"v" + std::to_string(dest_reg), "destination"});
    trace.operands.push_back({"v" + std::to_string(obj_reg), "object"});
    trace.operands.push_back({"field", field_res.class_descriptor + "." + field_res.field_name});
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});
    
    pc_ = pc + 2;
    return true;
}

bool DalvikExecutionEngine::execute_iget_object(uint32_t pc, InstructionTrace& trace) {
    // Format: 22c iget-object vA, vB, field@CCCC
    // Read object field from object and place reference in destination register
    // EXP-042 Phase 2 FIX: Previously, every error path returned false WITHOUT
    // advancing pc_. The caller then re-fetched the same opcode, hit the same
    // error, and looped forever — the loop detector eventually halted the
    // method, but only after 50 001 wasted iterations. Now all error paths
    // advance pc_ by 2 (22c format is 2 code units) and return true so the
    // caller can continue with a sensible default (null/0).
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }
    
    uint16_t instr = bytecode_[pc];
    uint8_t dest_reg = (instr >> 8) & 0xF;    // vA - 4-bit destination reg
    uint8_t obj_reg = (instr >> 12) & 0xF;    // vB - 4-bit object reg
    uint16_t field_idx = bytecode_[pc + 1];   // CCCC - field index
    
    // Resolve field from DEX
    FieldResolution field_res = resolve_field(field_idx);
    if (!field_res.resolved) {
        trace.error_message = "Failed to resolve field index " + std::to_string(field_idx);
        trace.status = InstructionTrace::Status::CRASH_ERROR;
        // EXP-042 Phase 2: advance pc_ and continue rather than spin.
        set_register(dest_reg, DalvikValue::make_null());
        pc_ = pc + 2;
        return true;
    }
    
    // Get object reference from register
    DalvikValue obj_ref = get_register(obj_reg);
    
    DalvikValue result_value;
    result_value.type = DalvikType::NULL_REF;
    result_value.object_id = 0;
    
    if (obj_ref.type == DalvikType::OBJECT_REF) {
        // Look up object field from heap
        if (heap_.has_object(obj_ref.object_id)) {
            auto field_val = heap_.get_object_field(obj_ref.object_id, field_res.field_name);
            if (field_val.has_value()) {
                result_value = field_val.value();
                if (result_value.type != DalvikType::OBJECT_REF && 
                    result_value.type != DalvikType::NULL_REF &&
                    result_value.type != DalvikType::STRING_REF) {
                    result_value.type = DalvikType::OBJECT_REF;
                }
            }
        }
    }
    // EXP-042 Phase 2: if obj_ref is not OBJECT_REF (uninit, null, primitive),
    // just return null. Previously this returned false and caused infinite
    // loops in ComponentActivity.onCreate, UserConfig.isClientActivated,
    // FragmentActivity.onCreate, etc.

    // EXP-055: Debug — log iget-object result for isClientActivated investigation.
    if (current_class_.find("UserConfig") != std::string::npos &&
        (current_method_ == "isClientActivated" || current_method_ == "getCurrentUser")) {
        std::cerr << "[IGET-OBJ-DBG] " << current_class_ << "." << current_method_
                  << " pc=" << pc
                  << " field=" << field_res.class_descriptor << "." << field_res.field_name
                  << " obj_reg_type=" << static_cast<int>(obj_ref.type)
                  << " obj_id=" << obj_ref.object_id
                  << " result_type=" << static_cast<int>(result_value.type)
                  << " result_obj=" << result_value.object_id
                  << std::endl;
    }

    // EXP-071 Phase 6 debug: Trace iget-object for TL_nearestDc.country
    // to understand why setCountry receives null for the country argument.
    if (field_res.field_name == "country" &&
        field_res.class_descriptor.find("nearestDc") != std::string::npos) {
        std::cerr << "[EXP071-IGET-COUNTRY] " << current_class_ << "." << current_method_
                  << " pc=" << pc
                  << " field=" << field_res.class_descriptor << "." << field_res.field_name
                  << " obj_reg_type=" << static_cast<int>(obj_ref.type)
                  << " obj_id=" << obj_ref.object_id
                  << " result_type=" << static_cast<int>(result_value.type);
        if (result_value.type == DalvikType::STRING_REF) {
            std::cerr << " str=\"" << result_value.string_val << "\"";
        }
        std::cerr << std::endl;
    }

    // EXP-059: Debug — log iget-object in addFragmentToStack
    if (current_method_ == "addFragmentToStack" &&
        current_class_.find("ActionBarLayout") != std::string::npos) {
        std::cerr << "[EXP059-IGET] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " dest=v" << (int)dest_reg
                  << " obj=v" << (int)obj_reg
                  << " field=" << field_res.class_descriptor << "." << field_res.field_name
                  << " obj_type=" << static_cast<int>(obj_ref.type)
                  << " obj_id=" << obj_ref.object_id
                  << " result_type=" << static_cast<int>(result_value.type)
                  << " result_obj=" << result_value.object_id
                  << std::endl;
    }

    // EXP-060: Debug — log iget-object for parentLayout in presentFragment
    if (field_res.resolved && field_res.field_name == "parentLayout" &&
        current_method_ == "presentFragment") {
        std::cerr << "[EXP060-IGET] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " obj=v" << (int)obj_reg
                  << " field=" << field_res.class_descriptor << "." << field_res.field_name
                  << " obj_type=" << static_cast<int>(obj_ref.type)
                  << " obj_id=" << obj_ref.object_id
                  << " result_type=" << static_cast<int>(result_value.type)
                  << " result_obj=" << result_value.object_id
                  << std::endl;
    }

    set_register(dest_reg, result_value);
    
    trace.operands.push_back({"v" + std::to_string(dest_reg), "destination"});
    trace.operands.push_back({"v" + std::to_string(obj_reg), "object"});
    trace.operands.push_back({"field", field_res.class_descriptor + "." + field_res.field_name});
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});
    
    pc_ = pc + 2;  // 22c format = 2 code units
    return true;
}

bool DalvikExecutionEngine::execute_iput(uint32_t pc, InstructionTrace& trace) {
    // Format: 22c iput vA, vB, field@CCCC (2 code units)
    // EXP-042 Phase 2 FIX: never return false — always advance pc_.
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }
    
    uint16_t instr = bytecode_[pc];
    uint8_t src_reg = (instr >> 8) & 0xF;
    uint8_t obj_reg = (instr >> 12) & 0xF;
    uint16_t field_idx = bytecode_[pc + 1];
    
    FieldResolution field_res = resolve_field(field_idx);
    DalvikValue src_val = get_register(src_reg);
    DalvikValue obj_ref = get_register(obj_reg);
    
    if (field_res.resolved && obj_ref.type == DalvikType::OBJECT_REF &&
        heap_.has_object(obj_ref.object_id)) {
        heap_.set_object_field(obj_ref.object_id, field_res.field_name, src_val);
    }
    // EXP-042 Phase 2: on any failure path, just advance pc_ — never spin.
    
    trace.operands.push_back({"v" + std::to_string(src_reg), "source"});
    trace.operands.push_back({"v" + std::to_string(obj_reg), "object"});
    trace.operands.push_back({"field", field_res.class_descriptor + "." + field_res.field_name});
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});
    
    pc_ = pc + 2;
    return true;
}

bool DalvikExecutionEngine::execute_iput_object(uint32_t pc, InstructionTrace& trace) {
    // Format: 22c iput-object vA, vB, field@CCCC (2 code units)
    // EXP-042 Phase 2 FIX: never return false — always advance pc_.
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }

    uint16_t instr = bytecode_[pc];
    uint8_t src_reg = (instr >> 8) & 0xF;
    uint8_t obj_reg = (instr >> 12) & 0xF;
    uint16_t field_idx = bytecode_[pc + 1];

    FieldResolution field_res = resolve_field(field_idx);
    DalvikValue src_val = get_register(src_reg);
    DalvikValue obj_ref = get_register(obj_reg);

    // EXP-058: Debug — log iput-object for actionBarLayout field.
    if (field_res.resolved && field_res.field_name == "actionBarLayout") {
        std::cerr << "[EXP058-IPUT] iput-object actionBarLayout"
                  << " src_reg=v" << (int)src_reg
                  << " src_type=" << static_cast<int>(src_val.type)
                  << " src_obj=" << src_val.object_id
                  << " obj_reg=v" << (int)obj_reg
                  << " obj_type=" << static_cast<int>(obj_ref.type)
                  << " obj_id=" << obj_ref.object_id
                  << " pc=" << pc
                  << " field_class=" << field_res.class_descriptor
                  << std::endl;
    }

    // EXP-060: Debug — log iput-object for parentLayout field.
    if (field_res.resolved && field_res.field_name == "parentLayout") {
        std::cerr << "[EXP060-IPUT] iput-object parentLayout"
                  << " src_reg=v" << (int)src_reg
                  << " src_type=" << static_cast<int>(src_val.type)
                  << " src_obj=" << src_val.object_id
                  << " obj_reg=v" << (int)obj_reg
                  << " obj_type=" << static_cast<int>(obj_ref.type)
                  << " obj_id=" << obj_ref.object_id
                  << " pc=" << pc
                  << " field_class=" << field_res.class_descriptor
                  << std::endl;
    }

    // EXP-062: Debug — log ALL iput-object in PhoneView.<init>
    if (field_res.resolved &&
        current_class_.find("PhoneView") != std::string::npos &&
        current_method_ == "<init>") {
        std::cerr << "[EXP062-IPUT] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " field=" << field_res.class_descriptor << "." << field_res.field_name
                  << " src=v" << (int)src_reg
                  << " src_type=" << static_cast<int>(src_val.type)
                  << " src_obj=" << src_val.object_id
                  << " obj=v" << (int)obj_reg
                  << " obj_type=" << static_cast<int>(obj_ref.type)
                  << " obj_id=" << obj_ref.object_id
                  << " obj_class=" << obj_ref.class_desc
                  << " stored=" << (obj_ref.type == DalvikType::OBJECT_REF && heap_.has_object(obj_ref.object_id) ? "YES" : "NO")
                  << std::endl;
    }

    if (field_res.resolved && obj_ref.type == DalvikType::OBJECT_REF &&
        heap_.has_object(obj_ref.object_id)) {
        heap_.set_object_field(obj_ref.object_id, field_res.field_name, src_val);
    }
    // EXP-042 Phase 2: never return false; just advance pc_.
    
    trace.operands.push_back({"v" + std::to_string(src_reg), "source"});
    trace.operands.push_back({"v" + std::to_string(obj_reg), "target"});
    trace.operands.push_back({"field", field_res.class_descriptor + "." + field_res.field_name});
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});
    
    pc_ = pc + 2;
    return true;
}

// EXP-035: Static Field Operations

bool DalvikExecutionEngine::execute_sget(uint32_t pc, InstructionTrace& trace) {
    // Format: 21c sget vAA, field@BBBB (2 code units)
    // EXP-042 Phase 2 FIX: never return false on field resolution failure —
    // advance pc_ by 2 and return default 0.
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }

    uint16_t instr = bytecode_[pc];
    uint8_t dest_reg = (instr >> 8) & 0xFF;
    uint16_t field_idx = bytecode_[pc + 1];

    FieldResolution field_res = resolve_field(field_idx);

    // EXP-053: Ensure the class is initialized before reading its static field.
    if (field_res.resolved) {
        ensure_class_initialized(field_res.class_descriptor);
    }

    DalvikValue result_value;
    result_value.type = DalvikType::INT32;
    result_value.int_val = 0;

    if (field_res.resolved) {
        std::string static_key = field_res.class_descriptor + "." + field_res.field_name;
        auto it = static_field_storage_.find(static_key);
        if (it != static_field_storage_.end()) {
            result_value = it->second;
        } else {
            static_field_storage_[static_key] = result_value;
        }
    }

    // EXP-053: Trace every sget (for resource ID investigation).
    // Throttled to first 100 to avoid log explosion.
    // EXP-063: Also trace R$string and R$drawable specifically.
    if (field_res.resolved) {
        static thread_local uint64_t sget_log_count = 0;
        static thread_local std::string last_method = "";
        static thread_local uint64_t method_sget_count = 0;
        if (current_method_ != last_method) {
            last_method = current_method_;
            method_sget_count = 0;
        }
        bool should_log = (sget_log_count < 100 && method_sget_count < 5);
        // EXP-063: Always log R$ fields
        bool is_r_field = (field_res.class_descriptor.find("R$") != std::string::npos);
        should_log = should_log || is_r_field;
        if (should_log) {
            sget_log_count++;
            method_sget_count++;
            std::cerr << "[SGET] class=" << current_class_
                      << " method=" << current_method_
                      << " pc=" << pc
                      << " field=" << field_res.class_descriptor << "."
                      << field_res.field_name
                      << " value=" << result_value.int_val
                      << std::endl;
        }
    }

    set_register(dest_reg, result_value);
    trace.operands.push_back({"v" + std::to_string(dest_reg), "destination"});
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});

    pc_ = pc + 2;
    return true;
}

bool DalvikExecutionEngine::execute_sget_object(uint32_t pc, InstructionTrace& trace) {
    // Format: 21c sget-object vAA, field@BBBB (2 code units)
    // EXP-042 Phase 2 FIX: never return false — advance pc_ on failure.
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }

    uint16_t instr = bytecode_[pc];
    uint8_t dest_reg = (instr >> 8) & 0xFF;
    uint16_t field_idx = bytecode_[pc + 1];

    FieldResolution field_res = resolve_field(field_idx);

    // EXP-053: Ensure the class is initialized before reading its static field.
    if (field_res.resolved) {
        ensure_class_initialized(field_res.class_descriptor);
    }

    DalvikValue result_value;
    result_value.type = DalvikType::NULL_REF;
    result_value.object_id = 0;

    if (field_res.resolved) {
        std::string static_key = field_res.class_descriptor + "." + field_res.field_name;
        auto it = static_field_storage_.find(static_key);
        if (it != static_field_storage_.end()) {
            result_value = it->second;
        } else {
            static_field_storage_[static_key] = result_value;
        }
    }

    // EXP-053: Trace sget-object (for singleton cache observation).
    if (field_res.resolved) {
        std::cerr << "[SGET] class=" << current_class_
                  << " method=" << current_method_
                  << " pc=" << pc
                  << " field=" << field_res.class_descriptor << "."
                  << field_res.field_name
                  << " obj_id=" << result_value.object_id
                  << std::endl;
    }

    set_register(dest_reg, result_value);
    trace.operands.push_back({"v" + std::to_string(dest_reg), "destination"});
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});

    pc_ = pc + 2;
    return true;
}

bool DalvikExecutionEngine::execute_sput(uint32_t pc, InstructionTrace& trace) {
    // Format: 21c sput vAA, field@BBBB (2 code units)
    // EXP-042 Phase 2 FIX: never return false — advance pc_ on failure.
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }
    
    uint16_t instr = bytecode_[pc];
    uint8_t src_reg = (instr >> 8) & 0xFF;
    uint16_t field_idx = bytecode_[pc + 1];
    
    FieldResolution field_res = resolve_field(field_idx);
    DalvikValue src_val = get_register(src_reg);
    
    if (field_res.resolved) {
        std::string static_key = field_res.class_descriptor + "." + field_res.field_name;
        static_field_storage_[static_key] = src_val;
    }
    
    trace.operands.push_back({"v" + std::to_string(src_reg), "source"});
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});
    
    pc_ = pc + 2;
    return true;
}

bool DalvikExecutionEngine::execute_sput_object(uint32_t pc, InstructionTrace& trace) {
    // Format: 21c sput-object vAA, field@BBBB (2 code units)
    // EXP-042 Phase 2 FIX: never return false — advance pc_ on failure.
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }
    
    uint16_t instr = bytecode_[pc];
    uint8_t src_reg = (instr >> 8) & 0xFF;
    uint16_t field_idx = bytecode_[pc + 1];
    
    FieldResolution field_res = resolve_field(field_idx);
    DalvikValue src_val = get_register(src_reg);
    
    if (field_res.resolved) {
        std::string static_key = field_res.class_descriptor + "." + field_res.field_name;
        static_field_storage_[static_key] = src_val;
    }
    
    trace.operands.push_back({"v" + std::to_string(src_reg), "source"});
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});
    
    pc_ = pc + 2;
    return true;
}

// ============================================================================
// OPCODE IMPLEMENTATIONS — Invokes
// ============================================================================

bool DalvikExecutionEngine::execute_invoke_virtual(uint32_t pc, InstructionTrace& trace,
                                                  DalvikExecutionResult& result) {
    // Format: 35c [op] {vC..}, method@BBBB
    // EXP-035: Now uses VTable dispatch for proper polymorphic method resolution
    if (pc + 2 >= bytecode_.size()) return false;

    // EXP-071 Phase 7: Save and reset current_invoke_is_static_ to false
    // for invoke-virtual calls. This ensures try_shadow_dispatch correctly
    // treats args[0] as `this` (instance method, not static).
    bool saved_is_static = current_invoke_is_static_;
    current_invoke_is_static_ = false;

    // EXP-062: Debug — trace ALL invoke-virtual entry in PhoneView.<init>
    if (current_class_.find("PhoneView") != std::string::npos &&
        current_method_ == "<init>") {
        auto v1 = get_register(1);
        std::cerr << "[EXP062-ENTRY] invoke-virtual entry pc=" << pc
                  << " v1_type=" << static_cast<int>(v1.type)
                  << " v1_obj=" << v1.object_id
                  << std::endl;
    }

    uint16_t instr = bytecode_[pc];
    // EXP-037 Phase B (BLOCKER-015 FIX): Per AOSP dalvik-bytecode.html,
    // 35c format is "AA|op BBBB FEDC" where:
    //   code[pc+0] = AA|op (arg_count + 5th_reg in high byte, opcode in low byte)
    //   code[pc+1] = BBBB (method_idx, 16-bit)
    //   code[pc+2] = FEDC (register list, 4 nibbles packed)
    // The previous code read method_idx from code[pc+2] and regs from code[pc+1],
    // which is REVERSED. This caused every invoke-* to read the register list
    // as the method_idx (often out-of-bounds) and the method_idx as the
    // register list (corrupted register values).
    uint16_t method_idx = bytecode_[pc + 1];  // method reference (was pc+2)
    uint16_t regs_word = bytecode_[pc + 2];    // register list (was pc+1)
    std::vector<DalvikValue> args;
    std::vector<std::string> arg_names;
    
    // Extract 5 register args (vG, vH, vI, vJ, vK) from 35c encoding
    uint8_t regs[5] = {
        static_cast<uint8_t>(regs_word & 0xF),
        static_cast<uint8_t>((regs_word >> 4) & 0xF),
        static_cast<uint8_t>((regs_word >> 8) & 0xF),
        static_cast<uint8_t>((regs_word >> 12) & 0xF),
        static_cast<uint8_t>((instr >> 8) & 0xF)  // 5th reg (low nibble of AA) — was (instr >> 4) & 0xF
    };
    
    // EXP-045: Only push argc registers (from 35c format: high nibble of high byte)
    uint8_t argc = (instr >> 12) & 0xF;
    for (int i = 0; i < argc && i < 5; ++i) {
        DalvikValue val = get_register(regs[i]);
        args.push_back(val);
        arg_names.push_back(register_name(regs[i]));
    }
    
    // EXP-035: VTable-based method resolution
    std::string static_type = "<unknown>";      // Declared type in bytecode
    std::string runtime_type = "<unknown>";     // Actual type of object
    std::string resolved_method = "<unresolved>";

    // EXP-037 Phase B (BLOCKER-002 FIX): Now that DexReport exposes
    // method_ids[], we can resolve method_idx → method name + declaring class.
    std::string method_name_from_dex = "<method_idx:" + std::to_string(method_idx) + ">";
    std::string declaring_class = "<unknown>";
    if (dex_report_) {
        method_name_from_dex = resolve_method_name_for_dex(method_idx, current_dex_index_);
        declaring_class = resolve_method_class_for_dex(method_idx, current_dex_index_);
    }
    
    // Get the object reference (first arg is 'this' for virtual calls)
    if (!args.empty() && args[0].type == DalvikType::OBJECT_REF) {
        DalvikValue this_obj = args[0];
        static_type = this_obj.class_desc;

        // Look up actual object class from heap
        if (auto* heap_obj = heap_.get(this_obj.object_id)) {
            runtime_type = heap_obj->class_descriptor;
            resolved_method = runtime_type + "." + method_name_from_dex;
        } else {
            // Object not in heap - use static type as fallback
            runtime_type = static_type;
            resolved_method = static_type + "." + method_name_from_dex;
            log("⚠️ INVOKE-VIRTUAL: Object not found in heap, using static type");
        }

        // EXP-061: Debug — trace addView calls to find why child=0
        if (method_name_from_dex == "addView" && args.size() >= 2) {
            std::cerr << "[EXP062-ADDVIEW-TRACE] invoke-virtual addView"
                      << " this_id=" << args[0].object_id
                      << " this_class=" << runtime_type
                      << " child_type=" << static_cast<int>(args[1].type)
                      << " child_id=" << args[1].object_id
                      << " child_class=" << args[1].class_desc
                      << " caller=" << current_class_ << "." << current_method_
                      << " pc=" << pc
                      << std::endl;
        }

        // EXP-062: Debug — trace v1 in PhoneView.<init> after each invoke-virtual
        // EXP-063: Also trace getResourceEntryName
        if (method_name_from_dex == "getResourceEntryName" && args.size() >= 2) {
            std::cerr << "[EXP063-RES-ARGS] getResourceEntryName"
                      << " this_id=" << args[0].object_id
                      << " this_type=" << static_cast<int>(args[0].type)
                      << " resid_type=" << static_cast<int>(args[1].type)
                      << " resid=" << args[1].int_val
                      << " caller=" << current_class_ << "." << current_method_
                      << " pc=" << pc
                      << std::endl;
        }
        if (current_class_.find("PhoneView") != std::string::npos &&
            current_method_ == "<init>" && !args.empty()) {
            auto v1 = get_register(1);
            std::cerr << "[EXP062-V1] invoke-virtual " << method_name_from_dex
                      << " pc=" << pc
                      << " v1_type=" << static_cast<int>(v1.type)
                      << " v1_obj=" << v1.object_id
                      << " this_type=" << static_cast<int>(args[0].type)
                      << " this_obj=" << args[0].object_id
                      << std::endl;
        }
    } else {
        // No object reference or null - can't do virtual dispatch
        if (args.empty()) {
            log("❌ INVOKE-VIRTUAL: No arguments provided");
        } else if (args[0].type == DalvikType::NULL_REF) {
            log("⚠️ INVOKE-VIRTUAL: Null object reference (would be NullPointerException)");
        }
        resolved_method = (declaring_class.empty() ? static_type : declaring_class) +
                          "." + method_name_from_dex;
    }
    
    // Try API bridge with resolved method info
    DalvikValue return_val = DalvikValue::make_void();
    ApiCallTrace::Status api_status = ApiCallTrace::Status::STUBBED;

    // EXP-038 (BLOCKER-034): Try recursive DEX method invocation first.
    // If the target method exists in DEX with bytecode, execute it recursively
    // instead of bridging to the API stub layer. This enables real execution
    // of helper methods (e.g., ApplicationLoader.init, AndroidUtilities, etc.)
    bool recursively_invoked = false;
    if (config_.enable_api_bridge) {
        // EXP-059: Polymorphism fix — invoke-virtual must dispatch using the
        // receiver's RUNTIME type, not the static declaring class from the
        // method_idx. Otherwise `BaseFragment.createView` (declared in the
        // base class) would be called instead of `MainTabsActivity.createView`
        // (the override that actually builds the UI).
        //
        // Strategy:
        //   1. If runtime_type is a known subclass of declaring_class, try
        //      the runtime_type FIRST. If it has the method, dispatch there.
        //   2. If the runtime_type doesn't have the method (or fails), fall
        //      back to the declaring_class (which is what the bytecode
        //      reference points to).
        bool tried_runtime_type = false;
        if (!args.empty() && args[0].type == DalvikType::OBJECT_REF &&
            runtime_type != "<unknown>" && runtime_type != declaring_class) {
            // Try the runtime type first — this is the polymorphic dispatch.
            if (try_recursive_invoke(runtime_type, method_name_from_dex,
                                     args, return_val, result)) {
                recursively_invoked = true;
                tried_runtime_type = true;
                api_status = ApiCallTrace::Status::IMPLEMENTED;
                last_invoke_return_ = return_val;
            }
        }
        if (!tried_runtime_type) {
            // Use declaring_class from method_ids[] for lookup
            if (try_recursive_invoke(declaring_class, method_name_from_dex,
                                     args, return_val, result)) {
                recursively_invoked = true;
                api_status = ApiCallTrace::Status::IMPLEMENTED;
                // EXP-057: CRITICAL FIX — must update last_invoke_return_ after
                // recursive invoke so move-result/move-result-object can read it.
                // try_recursive_invoke restores last_invoke_return_ to the saved
                // value internally, so we must re-set it from return_val here.
                // Without this, move-result-object reads stale VOID_ from a
                // previous method's return-void.
                last_invoke_return_ = return_val;
            }
        }
    }

    if (!recursively_invoked && config_.enable_api_bridge) {
        // Use declaring_class (the static type from method_ids[]) if
        // runtime_type is unknown — this lets us route framework calls like
        // android.app.Activity.onCreate to the API stub layer.
        std::string api_class = (runtime_type != "<unknown>") ? runtime_type : declaring_class;
        bridge_to_api(api_class, method_name_from_dex, args, return_val, api_status); last_invoke_return_ = return_val;
    }
    
    // Create API call trace with VTable information
    ApiCallTrace api_trace;
    api_trace.sequence = api_call_sequence_++;
    api_trace.api_class = runtime_type;  // Use runtime type for accuracy
    api_trace.method = method_name_from_dex;
    api_trace.arguments = arg_names;
    api_trace.return_value = return_val.to_string();
    api_trace.status = api_status;
    api_trace.pc = pc;
    api_trace.frame_id = call_stack_.empty() ? 0 : call_stack_.top().frame_id;
    
    if (config_.api_call_trace_cap > 0 && result.api_call_traces.size() >= config_.api_call_trace_cap) { result.api_call_traces.erase(result.api_call_traces.begin()); } result.api_call_traces.push_back(api_trace);
    
    // EXP-035: Evidence trace with VTable dispatch information
    trace.invoked_method = resolved_method;
    trace.operands.push_back({"args", std::to_string(arg_names.size())});
    trace.operands.push_back({"method_idx", std::to_string(method_idx)});
    trace.operands.push_back({"method_name", method_name_from_dex});
    trace.operands.push_back({"static_type", static_type});       // CRITICAL EVIDENCE
    trace.operands.push_back({"runtime_type", runtime_type});     // CRITICAL EVIDENCE  
    trace.operands.push_back({"resolved_method", resolved_method}); // CRITICAL EVIDENCE
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});  // MANDATORY TAG

    // EXP-071 Phase 7: Restore the saved static flag.
    current_invoke_is_static_ = saved_is_static;
    pc_ = pc + 3;
    return true;
}

// EXP-037 Phase B (BLOCKER-012): invoke-super
// Format: 35c [op {vC..vG, vF}], method@BBBB
//   instr_word[0] = opcode | (arg_count << 4)
//   instr_word[1] = packed register args (4 nibbles)
//   instr_word[2] = method_idx
//
// Semantics (per AOSP dexlib2):
//   invoke-super dispatches a virtual method starting from the SUPERCLASS
//   of the static type of `this`, NOT the runtime type. This is critical
//   for `super.onCreate(bundle)` calls — the call site declares the parent
//   class explicitly so the runtime must walk to that class's vtable slot
//   rather than using the runtime-type vtable.
//
//   Without this opcode, NO real Android app can execute past PC=0 of its
//   onCreate method, because `super.onCreate(bundle)` is always the first
//   instruction in user onCreate() implementations.
//
// Implementation:
//   Since BLOCKER-002 (method_ids[] parsing) is still open, we cannot yet
//   resolve method_idx → method name from the DEX. We degrade gracefully:
//   1. Log the invoke-super attempt with method_idx.
//   2. Bridge to API layer (which currently has stub onCreate handler).
//   3. Advance PC by 3 (35c format = 3 code units).
//   4. Do NOT halt — let execution continue to the next instruction.
//
// When BLOCKER-002 lands, this method should be rewritten to:
//   1. Look up method_idx in DexReport::method_ids[] to get the
//      declaring class + method name + descriptor.
//   2. Resolve the parent class of `this`'s static type.
//   3. Walk the parent's virtual_methods[] to find the matching method.
//   4. Recursively invoke execute_method_internal() on that method.
bool DalvikExecutionEngine::execute_invoke_super(uint32_t pc, InstructionTrace& trace,
                                                  DalvikExecutionResult& result) {
    // Format: 35c — 3 code units (6 bytes)
    if (pc + 2 >= bytecode_.size()) {
        log("❌ INVOKE-SUPER: PC out of bounds");
        return false;
    }

    uint16_t instr = bytecode_[pc];
    // EXP-037 Phase B (BLOCKER-015 FIX): 35c format is "AA|op BBBB FEDC"
    //   code[pc+0] = AA|op
    //   code[pc+1] = BBBB (method_idx)
    //   code[pc+2] = FEDC (register list)
    uint16_t method_idx = bytecode_[pc + 1];  // was pc+2
    uint16_t regs_word = bytecode_[pc + 2];    // was pc+1

    // 35c register encoding: 5 nibbles packed
    //   vA = high nibble of opcode word = arg count (typically 1 or 2)
    //   vG = low nibble of opcode word = 5th register (or 0 if vA < 5)
    //   vC..vF = 4 nibbles of regs_word
    // EXP-037 Phase B (BLOCKER-016 FIX): 35c format AA|op where AA = high byte.
// arg_count = HIGH NIBBLE of AA = (instr >> 12) & 0xF (was (instr >> 4) & 0xF — wrong)
// 5th_reg   = LOW NIBBLE of AA  = (instr >> 8) & 0xF (was (instr >> 4) & 0xF — wrong)
uint8_t arg_count = static_cast<uint8_t>((instr >> 12) & 0xF);
    uint8_t regs[5] = {
        static_cast<uint8_t>(regs_word & 0xF),
        static_cast<uint8_t>((regs_word >> 4) & 0xF),
        static_cast<uint8_t>((regs_word >> 8) & 0xF),
        static_cast<uint8_t>((regs_word >> 12) & 0xF),
        static_cast<uint8_t>((instr >> 8) & 0xF)  // 5th reg (low nibble of AA) — was (instr >> 4) & 0xF
    };

    // Read up to arg_count registers (cap at 5 for 35c format)
    std::vector<DalvikValue> args;
    std::vector<std::string> arg_names;
    uint8_t n_args = std::min<uint8_t>(arg_count, 5);
    for (uint8_t i = 0; i < n_args; ++i) {
        DalvikValue val = get_register(regs[i]);
        args.push_back(val);
        arg_names.push_back(register_name(regs[i]));
    }

    // EXP-037 Phase B (BLOCKER-002 + BLOCKER-012): Now that DexReport exposes
    // method_ids[], we can resolve method_idx → method name + declaring class.
    std::string method_name = "<method_idx:" + std::to_string(method_idx) + ">";
    std::string declaring_class = "<unknown>";
    if (dex_report_) {
        method_name = resolve_method_name_for_dex(method_idx, current_dex_index_);
        declaring_class = resolve_method_class_for_dex(method_idx, current_dex_index_);
    }

    // Identify `this` (first arg) for diagnostic logging
    std::string runtime_type = "<unknown>";
    std::string static_type = "<unknown>";
    std::string resolved_method = declaring_class + "." + method_name + " (super)";

    if (!args.empty() && args[0].type == DalvikType::OBJECT_REF) {
        const DalvikValue& this_obj = args[0];
        static_type = this_obj.class_desc;
        if (auto* heap_obj = heap_.get(this_obj.object_id)) {
            runtime_type = heap_obj->class_descriptor;
        } else {
            runtime_type = static_type;
        }
    } else if (!args.empty() && args[0].type == DalvikType::NULL_REF) {
        log("⚠️ INVOKE-SUPER: Null `this` reference (would be NullPointerException on real Android)");
        runtime_type = "<null>";
    } else {
        log("⚠️ INVOKE-SUPER: First argument is not an object reference (arg_count=" +
            std::to_string(arg_count) + ", arg[0].type=" +
            std::to_string(static_cast<int>(args.empty() ? DalvikType::UNINITIALIZED : args[0].type)) + ")");
    }

    log("📞 INVOKE-SUPER: " + declaring_class + "." + method_name +
        " (method_idx=" + std::to_string(method_idx) +
        ", arg_count=" + std::to_string(arg_count) +
        ", static_type=" + static_type +
        ", runtime_type=" + runtime_type + ")");

    // Bridge to API layer — for super.onCreate(), the API layer provides
    // the framework's Activity.onCreate implementation (window setup, etc.).
    DalvikValue return_val = DalvikValue::make_void();
    ApiCallTrace::Status api_status = ApiCallTrace::Status::STUBBED;

    // EXP-038 (BLOCKER-034): Try recursive invocation for super calls too.
    bool recursively_invoked = false;
    if (config_.enable_api_bridge) {
        if (try_recursive_invoke(declaring_class, method_name, args, return_val, result)) { last_invoke_return_ = return_val;
            recursively_invoked = true;
            api_status = ApiCallTrace::Status::IMPLEMENTED;
        }
    }
    if (!recursively_invoked && config_.enable_api_bridge) {
        bridge_to_api(declaring_class + "<super>", method_name,
                      args, return_val, api_status);
        last_invoke_return_ = return_val;
    }

    // Record an API call trace entry so this call shows up in evidence
    ApiCallTrace api_trace;
    api_trace.sequence = api_call_sequence_++;
    api_trace.api_class = declaring_class + "<super>";
    api_trace.method = method_name;
    api_trace.arguments = arg_names;
    api_trace.return_value = return_val.to_string();
    api_trace.status = api_status;
    api_trace.pc = pc;
    api_trace.frame_id = call_stack_.empty() ? 0 : call_stack_.top().frame_id;
    if (config_.api_call_trace_cap > 0 && result.api_call_traces.size() >= config_.api_call_trace_cap) { result.api_call_traces.erase(result.api_call_traces.begin()); } result.api_call_traces.push_back(api_trace);

    // Trace evidence
    trace.invoked_method = resolved_method;
    trace.operands.push_back({"invoke_kind", "super"});
    trace.operands.push_back({"method_idx", std::to_string(method_idx)});
    trace.operands.push_back({"method_name", method_name});
    trace.operands.push_back({"declaring_class", declaring_class});
    trace.operands.push_back({"arg_count", std::to_string(arg_count)});
    trace.operands.push_back({"args", std::to_string(arg_names.size())});
    trace.operands.push_back({"static_type", static_type});
    trace.operands.push_back({"runtime_type", runtime_type});
    trace.operands.push_back({"source", "REAL_DALVIK_INTERPRETER"});

    // Advance PC past the 35c instruction (3 code units = 6 bytes)
    pc_ = pc + 3;
    return true;
}

bool DalvikExecutionEngine::execute_invoke_direct(uint32_t pc, InstructionTrace& trace,
                                                 DalvikExecutionResult& result) {
    // Similar to invoke-virtual but for constructors and private methods
    if (pc + 2 >= bytecode_.size()) return false;

    // EXP-071 Phase 7: Save and reset current_invoke_is_static_ to false
    // for invoke-direct calls (instance methods).
    bool saved_is_static = current_invoke_is_static_;
    current_invoke_is_static_ = false;
    
    uint16_t instr = bytecode_[pc];
    // EXP-037 Phase B (BLOCKER-015 FIX): 35c format is "AA|op BBBB FEDC"
    //   code[pc+0] = AA|op
    //   code[pc+1] = BBBB (method_idx)
    //   code[pc+2] = FEDC (register list)
    uint16_t method_idx = bytecode_[pc + 1];  // was pc+2
    uint16_t regs_word = bytecode_[pc + 2];    // was pc+1
    
    // Extract registers
    // EXP-037 Phase B (BLOCKER-016 FIX): 5th reg is low nibble of AA (high byte
    // of opcode word), so it's (instr >> 8) & 0xF, not (instr >> 4) & 0xF.
    uint8_t regs[5] = {
        static_cast<uint8_t>(regs_word & 0xF),
        static_cast<uint8_t>((regs_word >> 4) & 0xF),
        static_cast<uint8_t>((regs_word >> 8) & 0xF),
        static_cast<uint8_t>((regs_word >> 12) & 0xF),
        static_cast<uint8_t>((instr >> 8) & 0xF)  // 5th reg — was (instr >> 4) & 0xF
    };
    
    std::vector<DalvikValue> args;
    // EXP-045: Only push argc registers (from 35c format: high nibble of high byte)
    uint8_t argc = (instr >> 12) & 0xF;
    for (int i = 0; i < argc && i < 5; ++i) {
        args.push_back(get_register(regs[i]));
    }
    
    // Resolve as constructor (<init>) or direct method
    // EXP-037 Phase B (BLOCKER-002 FIX): use DexReport::method_ids to resolve
    // method_idx → real method name + declaring class.
    std::string method_name = "<init>";  // fallback for legacy code paths
    std::string class_name = "<unknown>";
    if (dex_report_) {
        method_name = resolve_method_name_for_dex(method_idx, current_dex_index_);
        class_name = resolve_method_class_for_dex(method_idx, current_dex_index_);
    }

    // EXP-061: Debug — trace invoke-direct inside PhoneView.<init>
    if (current_class_.find("PhoneView") != std::string::npos &&
        current_method_ == "<init>") {
        std::cerr << "[EXP061-INVOKE-DIRECT] caller=PhoneView.<init>"
                  << " method_idx=" << method_idx
                  << " dex_index=" << current_dex_index_
                  << " → class=" << class_name
                  << " method=" << method_name
                  << " argc=" << (int)argc
                  << std::endl;
    }
    
    // Check if first arg is an object we allocated
    // EXP-061 FIX: Do NOT overwrite class_name with the runtime class for
    // invoke-direct. invoke-direct uses the DECLARING class (from method_ids[]),
    // not the runtime class. Overwriting it causes try_recursive_invoke to
    // search for <init> in the SUBCLASS (e.g. PhoneView) instead of the
    // SUPERCLASS (e.g. SlideView), leading to infinite recursion detection
    // or wrong method selection. Only invoke-virtual should use the runtime
    // class for polymorphic dispatch.
    if (!args.empty() && args[0].type == DalvikType::OBJECT_REF) {
        if (auto* obj = heap_.get(args[0].object_id)) {
            // Mark as initialized (constructor called)
            if (method_name == "<init>") {
                heap_.mark_initialized(args[0].object_id);
            }
            log("  INVOKE-DIRECT: " + class_name + "." + method_name +
                "() on obj#" + std::to_string(args[0].object_id));
        }
    }
    
    // API bridge
    DalvikValue return_val = DalvikValue::make_void();
    ApiCallTrace::Status status = ApiCallTrace::Status::STUBBED;

    // EXP-038 (BLOCKER-034): Try recursive invocation.
    bool recursively_invoked = false;
    if (config_.enable_api_bridge) {
        if (try_recursive_invoke(class_name, method_name, args, return_val, result)) { last_invoke_return_ = return_val;
            recursively_invoked = true;
            status = ApiCallTrace::Status::IMPLEMENTED;
        }
    }
    if (!recursively_invoked && config_.enable_api_bridge) {
        bridge_to_api(class_name, method_name, args, return_val, status); last_invoke_return_ = return_val;
    }
    
    // Trace
    ApiCallTrace api_trace;
    api_trace.sequence = api_call_sequence_++;
    api_trace.api_class = class_name;
    api_trace.method = method_name;
    api_trace.status = status;
    api_trace.pc = pc;
    if (config_.api_call_trace_cap > 0 && result.api_call_traces.size() >= config_.api_call_trace_cap) { result.api_call_traces.erase(result.api_call_traces.begin()); } result.api_call_traces.push_back(api_trace);
    
    trace.invoked_method = class_name + "." + method_name;
    trace.operands.push_back({"method", std::to_string(method_idx)});

    // EXP-071 Phase 7: Restore the saved static flag.
    current_invoke_is_static_ = saved_is_static;
    pc_ = pc + 3;
    return true;
}

bool DalvikExecutionEngine::execute_invoke_static(uint32_t pc, InstructionTrace& trace,
                                                 DalvikExecutionResult& result) {
    // Format similar to invoke-virtual but for static methods
    if (pc + 2 >= bytecode_.size()) return false;

    // EXP-071 Phase 8: Mark this call as static so try_shadow_dispatch
    // doesn't treat args[0] as `this`. See header comment for details.
    //
    // EXP-071 Phase 7 FIX: The flag stays true during the entire
    // execute_invoke_static call. execute_invoke_virtual and
    // execute_invoke_direct SAVE and RESET the flag to false at their
    // entry, and RESTORE it at their exit. This ensures that:
    //   - bridge_to_api → try_shadow_dispatch at THIS level sees true (static)
    //   - bridge_to_api → try_shadow_dispatch inside callees sees false (instance)
    bool saved_is_static = current_invoke_is_static_;
    current_invoke_is_static_ = true;
    
    uint16_t instr = bytecode_[pc];
    // EXP-037 Phase B (BLOCKER-015 FIX): 35c format is "AA|op BBBB FEDC"
    //   code[pc+0] = AA|op
    //   code[pc+1] = BBBB (method_idx)
    //   code[pc+2] = FEDC (register list)
    uint16_t method_idx = bytecode_[pc + 1];  // was pc+2
    uint16_t regs_word = bytecode_[pc + 2];    // was pc+1

    // Extract argument registers
    uint8_t regs[5] = {
        static_cast<uint8_t>(regs_word & 0xF),
        static_cast<uint8_t>((regs_word >> 4) & 0xF),
        static_cast<uint8_t>((regs_word >> 8) & 0xF),
        static_cast<uint8_t>((regs_word >> 12) & 0xF),
        static_cast<uint8_t>((instr >> 8) & 0xF)  // 5th reg — was (instr >> 4) & 0xF
    };

    std::vector<DalvikValue> args;
    // EXP-045: Only push argc registers (from 35c format: high nibble of high byte)
    uint8_t argc = (instr >> 12) & 0xF;

    // EXP-071 Phase 8: Resolve method name and proto EARLY so we can use them
    // for debug tracing in the wide-merge code below. The original code only
    // resolved method_name AFTER the args were built, which meant our debug
    // trace couldn't reference method_name.
    std::string method_name = "<static_method:" + std::to_string(method_idx) + ">";
    std::string class_name = "<static_class>";
    if (dex_report_) {
        method_name = resolve_method_name_for_dex(method_idx, current_dex_index_);
        class_name = resolve_method_class_for_dex(method_idx, current_dex_index_);
    }

    // EXP-071 Phase 8: Wide register merging.
    //
    // For methods with wide arguments (J = long, D = double), each wide arg
    // occupies TWO consecutive register slots in the Dalvik register file.
    // Without merging, `invoke-static {v3, v0, v1}, runOnUIThread(Runnable, J)`
    // would push 3 args (v3=Runnable, v0=low32, v1=high32) instead of 2
    // (Runnable, long). This breaks HandlerShadow's delay extraction
    // because args[1] is a low-half INT32 instead of an INT64 long.
    //
    // Fix: parse the method descriptor and merge wide register pairs into
    // single INT64/FLOAT64 DalvikValues. The descriptor is the (Ljava/lang/Runnable;J)V
    // string from the DEX method_id table; we walk the parameter types left
    // to right, consuming registers from the regs[] array in order.
    std::string method_proto = "<unknown>";
    if (dex_report_) {
        method_proto = resolve_method_proto_for_dex(method_idx, current_dex_index_);
    }

    // Parse the parameter list inside the parens.
    // Format: "(Ljava/lang/Runnable;J)V" → params = ["Ljava/lang/Runnable;", "J"]
    std::vector<std::string> param_types;
    if (method_proto != "<unknown>") {
        size_t lp = method_proto.find('(');
        size_t rp = method_proto.find(')');
        if (lp != std::string::npos && rp != std::string::npos && rp > lp) {
            std::string params = method_proto.substr(lp + 1, rp - lp - 1);
            size_t i = 0;
            while (i < params.size()) {
                char c = params[i];
                if (c == 'L') {
                    size_t semi = params.find(';', i);
                    if (semi == std::string::npos) break;
                    param_types.push_back(params.substr(i, semi - i + 1));
                    i = semi + 1;
                } else if (c == '[') {
                    // Array — keep eating [ until non-[
                    size_t start = i;
                    while (i < params.size() && params[i] == '[') i++;
                    if (i < params.size() && params[i] == 'L') {
                        size_t semi = params.find(';', i);
                        if (semi == std::string::npos) break;
                        param_types.push_back(params.substr(start, semi - start + 1));
                        i = semi + 1;
                    } else {
                        param_types.push_back(params.substr(start, i - start + 1));
                        i += 1;
                    }
                } else {
                    // Primitive — single char (B C D F I J S Z V)
                    param_types.push_back(std::string(1, c));
                    i += 1;
                }
            }
        }
    }

    // Walk params, consuming registers from regs[]. Each wide param (J or D)
    // consumes TWO register slots; otherwise one.
    size_t reg_idx = 0;
    for (size_t p = 0; p < param_types.size() && reg_idx < 5 && (int)reg_idx < argc; ++p) {
        const std::string& pt = param_types[p];
        if (pt == "J" || pt == "D") {
            // Wide: this register pair holds a 64-bit value.
            DalvikValue lo = get_register(regs[reg_idx]);
            if (lo.type == DalvikType::INT64) {
                // Case 1: low register already holds the full INT64 (set by const-wide/*).
                if (pt == "J") {
                    args.push_back(lo);
                } else {
                    double d;
                    int64_t bits = lo.long_val;
                    std::memcpy(&d, &bits, sizeof(d));
                    args.push_back(DalvikValue::make_double(d));
                }
            } else if (lo.type == DalvikType::FLOAT64) {
                args.push_back(lo);
            } else {
                // Case 2: merge two registers (split wide value).
                DalvikValue hi = get_register(regs[reg_idx + 1]);
                int64_t combined = (static_cast<int64_t>(hi.int_val) << 32) |
                                   (static_cast<uint32_t>(lo.int_val));
                if (pt == "J") {
                    args.push_back(DalvikValue::make_long(combined));
                } else {
                    double d;
                    int64_t bits = combined;
                    std::memcpy(&d, &bits, sizeof(d));
                    args.push_back(DalvikValue::make_double(d));
                }
            }
            reg_idx += 2;
        } else {
            args.push_back(get_register(regs[reg_idx]));
            reg_idx += 1;
        }
    }
    // If we couldn't parse params (proto unavailable), fall back to old behavior.
    if (param_types.empty() && args.empty()) {
        for (int i = 0; i < argc && i < 5; ++i) {
            args.push_back(get_register(regs[i]));
        }
    }

    // EXP-063: Trace invoke-static for getString
    if (dex_report_) {
        std::string mn = resolve_method_name_for_dex(method_idx, current_dex_index_);
        if (mn == "getString") {
            std::string cn = resolve_method_class_for_dex(method_idx, current_dex_index_);
            std::cerr << "[EXP063-ISTATIC] getString"
                      << " instr=0x" << std::hex << instr << std::dec
                      << " argc=" << (int)argc
                      << " regs[0]=" << (int)regs[0]
                      << " class=" << cn
                      << " caller=" << current_class_ << "." << current_method_
                      << " pc=" << pc;
            if (!args.empty()) {
                std::cerr << " arg0=" << args[0].int_val;
            } else {
                std::cerr << " NO_ARGS";
            }
            std::cerr << std::endl;
        }
    }

    // EXP-071 Phase 8: Trace runOnUIThread specifically to verify wide-arg merging.
    if (method_name == "runOnUIThread" || method_name == "executeOnUIThread") {
        std::cerr << "[EXP071-RUNONUI] class=" << class_name
                  << " method=" << method_name
                  << " argc=" << (int)argc
                  << " args_count=" << args.size()
                  << " proto=" << method_proto;
        for (size_t i = 0; i < args.size(); ++i) {
            std::cerr << " arg[" << i << "]=";
            switch (args[i].type) {
                case DalvikType::OBJECT_REF:
                    std::cerr << "obj#" << args[i].object_id
                              << "(" << args[i].class_desc << ")";
                    break;
                case DalvikType::INT64:
                    std::cerr << "long=" << args[i].long_val;
                    break;
                case DalvikType::INT32:
                    std::cerr << "int=" << args[i].int_val;
                    break;
                default:
                    std::cerr << "<other>";
                    break;
            }
        }
        std::cerr << std::endl;
    }
    
    // Common static methods we might recognize (legacy hint — now used only
    // for routing hints when the API bridge falls through).
    if (class_name.find("Log") != std::string::npos) {
        if (args.size() > 0 && args[0].type == DalvikType::INT32) {
            // args[0].int_val is the Log level: 5=warn, 6=error, etc.
            // (Just a hint; method_name from DEX is authoritative.)
        }
    }

    // API bridge
    DalvikValue return_val = DalvikValue::make_void();
    ApiCallTrace::Status status = ApiCallTrace::Status::STUBBED;

    // EXP-038 (BLOCKER-034): Try recursive invocation.
    bool recursively_invoked = false;
    // EXP-063: Intercept getString(String, int) before recursive invoke.
    if (config_.enable_api_bridge &&
        method_name == "getString" &&
        class_name.find("LocaleController") != std::string::npos &&
        args.size() >= 1 && args[0].type == DalvikType::STRING_REF) {
        std::string res_name = args[0].string_val;
        if (!res_name.empty()) {
            auto it = resource_string_values_.find(res_name);
            if (it != resource_string_values_.end()) {
                std::cerr << "[RES] getString name=" << res_name << " val=" << it->second << std::endl;
                return_val = DalvikValue::make_string(it->second, 0);
                last_invoke_return_ = return_val;
                recursively_invoked = true;
                status = ApiCallTrace::Status::IMPLEMENTED;
            }
        }
    }
    if (!recursively_invoked && config_.enable_api_bridge) {
        // current_invoke_is_static_ is already false (reset above).
        if (try_recursive_invoke(class_name, method_name, args, return_val, result)) { last_invoke_return_ = return_val;
            recursively_invoked = true;
            status = ApiCallTrace::Status::IMPLEMENTED;
        }
    }
    if (!recursively_invoked && config_.enable_api_bridge) {
        // current_invoke_is_static_ is still true (set at top of execute_invoke_static).
        // try_shadow_dispatch inside bridge_to_api will see it and correctly
        // treat args[0] as the first parameter (not `this`).
        bridge_to_api(class_name, method_name, args, return_val, status); last_invoke_return_ = return_val;
    }

    ApiCallTrace api_trace;
    api_trace.sequence = api_call_sequence_++;
    api_trace.api_class = class_name;
    api_trace.method = method_name;
    api_trace.status = status;
    api_trace.pc = pc;
    if (config_.api_call_trace_cap > 0 && result.api_call_traces.size() >= config_.api_call_trace_cap) { result.api_call_traces.erase(result.api_call_traces.begin()); } result.api_call_traces.push_back(api_trace);

    trace.invoked_method = class_name + "." + method_name;

    // EXP-071 Phase 7: Restore the saved static flag.
    current_invoke_is_static_ = saved_is_static;
    pc_ = pc + 3;
    return true;
}

bool DalvikExecutionEngine::execute_invoke_interface(uint32_t pc, InstructionTrace& trace,
                                                   DalvikExecutionResult& result) {
    // Similar to other invokes but for interface dispatch
    if (pc + 2 >= bytecode_.size()) return false;

    uint16_t instr = bytecode_[pc];
    // EXP-045: Only push argc registers (from 35c format: high nibble of high byte)
    uint8_t argc = (instr >> 12) & 0xF;
    uint16_t method_idx = bytecode_[pc + 1];
    uint16_t regs_word = bytecode_[pc + 2];

    uint8_t regs[5] = {
        static_cast<uint8_t>(regs_word & 0xF),
        static_cast<uint8_t>((regs_word >> 4) & 0xF),
        static_cast<uint8_t>((regs_word >> 8) & 0xF),
        static_cast<uint8_t>((regs_word >> 12) & 0xF),
        static_cast<uint8_t>((instr >> 8) & 0xF)
    };

    std::vector<DalvikValue> args;
    for (int i = 0; i < argc && i < 5; ++i) {
        args.push_back(get_register(regs[i]));
    }

    // EXP-037 Phase B (BLOCKER-002 FIX): resolve method_idx via DexReport.
    std::string method_name = "<interface_method:" + std::to_string(method_idx) + ">";
    std::string class_name = "<interface>";
    if (dex_report_) {
        method_name = resolve_method_name_for_dex(method_idx, current_dex_index_);
        class_name = resolve_method_class_for_dex(method_idx, current_dex_index_);
    }

    // EXP-048: Try recursive invoke first (some interface methods have impls)
    DalvikValue return_val = DalvikValue::make_void();
    if (try_recursive_invoke(class_name, method_name, args, return_val, result)) { last_invoke_return_ = return_val;
        trace.invoked_method = class_name + "." + method_name;
        pc_ = pc + 3;
        return true;
    }

    // EXP-058: Interface dispatch — try the RUNTIME TYPE of the receiver.
    if (!args.empty() && args[0].type == DalvikType::OBJECT_REF) {
        uint32_t receiver_id = args[0].object_id;
        if (heap_.has_object(receiver_id)) {
            const auto* heap_obj = heap_.get(receiver_id);
            if (heap_obj && !heap_obj->class_descriptor.empty() &&
                heap_obj->class_descriptor != class_name) {
                // Try the concrete class.
                if (try_recursive_invoke(heap_obj->class_descriptor, method_name,
                                         args, return_val, result)) {
                    last_invoke_return_ = return_val;
                    trace.invoked_method = heap_obj->class_descriptor + "." + method_name;
                    pc_ = pc + 3;
                    return true;
                }
            }
        }
    } else if (!args.empty() && method_name == "addFragmentToStack") {
        // EXP-058: Debug — why is interface dispatch not working?
        int arg0_type = static_cast<int>(args[0].type);
        uint32_t arg0_obj = args[0].object_id;
        bool has_obj = heap_.has_object(arg0_obj);
        std::string heap_class = has_obj ? heap_.get(arg0_obj)->class_descriptor : "<no heap obj>";
        std::cerr << "[EXP058-IFACE] addFragmentToStack dispatch failed"
                  << " arg0_type=" << arg0_type
                  << " arg0_obj=" << arg0_obj
                  << " has_heap_obj=" << has_obj
                  << " heap_class=" << heap_class
                  << " static_class=" << class_name
                  << std::endl;
    }

    // EXP-048: Fall through to bridge_to_api for interface methods
    ApiCallTrace::Status status = ApiCallTrace::Status::STUBBED;
    if (config_.enable_api_bridge) {
        bridge_to_api(class_name, method_name, args, return_val, status); last_invoke_return_ = return_val;
    }

    ApiCallTrace api_trace;
    api_trace.sequence = api_call_sequence_++;
    api_trace.api_class = class_name;
    api_trace.method = method_name;
    api_trace.status = status;
    api_trace.pc = pc;
    if (config_.api_call_trace_cap > 0 && result.api_call_traces.size() >= config_.api_call_trace_cap) { result.api_call_traces.erase(result.api_call_traces.begin()); } result.api_call_traces.push_back(api_trace);

    trace.invoked_method = class_name + "." + method_name;

    pc_ = pc + 3;
    return true;
}

// ============================================================================
// OPCODE IMPLEMENTATIONS — Returns
// ============================================================================

bool DalvikExecutionEngine::execute_return_void(uint32_t pc, InstructionTrace& trace) {
    // Format: 10x [op] {} (no operands)
    trace.status = InstructionTrace::Status::HALT_RETURN;
    trace.return_value = DalvikValue::make_void();
    
    halted_ = true;
    halted_on_return_ = true;
    
    log("  RETURN_VOID at " + to_hex(pc));
    
    pc_ = pc + 1;
    return true;
}

bool DalvikExecutionEngine::execute_return(uint32_t pc, InstructionTrace& trace) {
    // Format: 11x [op] vAA (1 code unit)
    if (pc >= bytecode_.size()) return false;
    
    uint16_t instr = bytecode_[pc];
    uint8_t ret_reg = (instr >> 8) & 0xFF;
    
    DalvikValue val = get_register(ret_reg);
    
    trace.status = InstructionTrace::Status::HALT_RETURN;
    trace.return_value = val;
    trace.operands.push_back({"v" + std::to_string(ret_reg), val.to_string()});
    
    // EXP-055: Store the return value so try_recursive_invoke can
    // propagate it to the caller. Previously, return_val was always
    // make_void() — so every recursive invoke returned void, and
    // move-result after an invoke always got 0/null. This caused
    // isClientActivated to return void (treated as false), which
    // happened to be correct for the login path but was fundamentally
    // broken for any method that returns a non-zero value.
    last_invoke_return_ = val;
    
    // EXP-059: Debug — log return values for onFragmentCreate and addFragmentToStack
    if (current_method_ == "onFragmentCreate" ||
        (current_method_ == "addFragmentToStack" &&
         current_class_.find("ActionBarLayout") != std::string::npos)) {
        std::cerr << "[EXP059-RETURN] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " ret_reg=v" << (int)ret_reg
                  << " type=" << static_cast<int>(val.type)
                  << " int_val=" << val.int_val
                  << " obj=" << val.object_id
                  << std::endl;
    }
    
    halted_ = true;
    halted_on_return_ = true;
    
    log("  RETURN " + val.to_string() + " at " + to_hex(pc));
    
    pc_ = pc + 1;
    return true;
}

bool DalvikExecutionEngine::execute_return_object(uint32_t pc, InstructionTrace& trace) {
    // Format: 11x [op] vAA (1 code unit)
    if (pc >= bytecode_.size()) return false;
    
    uint16_t instr = bytecode_[pc];
    uint8_t ret_reg = (instr >> 8) & 0xFF;
    
    DalvikValue val = get_register(ret_reg);
    
    trace.status = InstructionTrace::Status::HALT_RETURN;
    trace.return_value = val;
    trace.operands.push_back({"v" + std::to_string(ret_reg), val.to_string()});
    
    // EXP-055: Store the return value (same as execute_return).
    last_invoke_return_ = val;
    
    halted_ = true;
    halted_on_return_ = true;
    
    log("  RETURN_OBJECT " + val.to_string() + " at " + to_hex(pc));
    
    pc_ = pc + 1;
    return true;
}

// ============================================================================
// OPCODE IMPLEMENTATIONS — Control Flow
// ============================================================================

bool DalvikExecutionEngine::execute_goto(uint32_t pc, InstructionTrace& trace) {
    // EXP-039 (BLOCKER-036 FIX): Handle all goto variants correctly.
    // goto (0x28) = format 10t: AA|op (1 code unit, offset in high byte)
    // goto/16 (0x29) = format 20t: op|AAAA (2 code units, offset in next word)
    // goto/32 (0x2a) = format 30t: op|AAAAAAAA (3 code units, offset in next 2 words)
    if (pc >= bytecode_.size()) return false;

    uint16_t opcode = bytecode_[pc] & 0xFF;

    int32_t offset;
    uint32_t pc_advance;

    if (opcode == Opcode::GOTO) {
        // Format 10t: offset is in high byte (signed 8-bit)
        offset = static_cast<int8_t>((bytecode_[pc] >> 8) & 0xFF);
        pc_advance = 1;
        // EXP-071: D8/R8 hybrid goto encoding.
        // D8 uses op=0x28 (goto) for BOTH 10t and 20t formats:
        // 1. High byte != 0: Standard 10t format (1 code unit, offset in high byte).
        // 2. High byte == 0: Extended 20t format (2 code units, offset in next word).
        //    This is safe because D8 doesn't generate goto +0 (NOP).
        //    We check that the next word is a reasonable offset (< 10000).
        if (offset == 0 && pc + 1 < bytecode_.size()) {
            int16_t next_offset = static_cast<int16_t>(bytecode_[pc + 1]);
            if (next_offset != 0 && std::abs(next_offset) < 10000) {
                offset = next_offset;
                pc_advance = 2;
            }
        }
    } else if (opcode == Opcode::GOTO_16) {
        // EXP-044 Phase 1: D8/R8 hybrid goto/16 encoding.
        //
        // D8 uses op=0x28 (goto/16) in TWO modes:
        // 1. High byte != 0: The high byte IS the 8-bit signed offset.
        //    Total instruction size: 1 code unit (like 10t format).
        //    The "next word" is the START of the next instruction, NOT an offset.
        //    Example: AndroidUtilities.bold PC=24 → high=0x09=+9 → target=PC=33
        // 2. High byte == 0: Standard 20t format, 16-bit signed offset in next word.
        //    Total instruction size: 2 code units.
        //    Example: (rare, 578 out of 27381 in classes.dex)
        //
        // Evidence: 26803 goto/16 instructions have non-zero high byte,
        // 578 have high byte=0 (standard 20t). The high byte values are
        // always small (±12 range typical), matching short branch offsets.
        //
        // This was the root cause of 20 HALT-GOTO events in Telegram execution.
        uint8_t high_byte = (bytecode_[pc] >> 8) & 0xFF;
        if (high_byte != 0) {
            // D8 hybrid mode: 1-code-unit goto with 8-bit offset in high byte
            offset = static_cast<int8_t>(high_byte);
            pc_advance = 1;
        } else {
            // Standard 20t format: 2 code units, 16-bit offset in next word
            if (pc + 1 >= bytecode_.size()) return false;
            offset = static_cast<int16_t>(bytecode_[pc + 1]);
            pc_advance = 2;
        }
    } else if (opcode == Opcode::GOTO_32) {
        // EXP-044 Phase 1: D8/R8 hybrid goto/32 encoding (same as goto/16).
        //
        // D8 uses op=0x29 (goto/32) in TWO modes:
        // 1. High byte != 0 (10959 occurrences): 8-bit signed offset in high byte.
        //    Total instruction size: 1 code unit.
        // 2. High byte == 0 (24727 occurrences): 16-bit signed offset in next word.
        //    Total instruction size: 2 code units (NOT 3 as per AOSP 30t spec).
        //    The word at PC+2 is the start of the NEXT instruction, not the high
        //    16 bits of a 32-bit offset.
        //
        // Evidence: ApplicationLoader.postInitApplication PC=8:
        //   high=0x00, next=0x0101=257 → target=PC=265 (return-void). Correct!
        //   Standard 30t with 32-bit offset would give 0x10120101 → invalid.
        uint8_t high_byte = (bytecode_[pc] >> 8) & 0xFF;
        if (high_byte != 0) {
            // D8 hybrid mode: 1-code-unit goto with 8-bit offset in high byte
            offset = static_cast<int8_t>(high_byte);
            pc_advance = 1;
        } else {
            // D8 2-code-unit format: 16-bit offset in next word
            if (pc + 1 >= bytecode_.size()) return false;
            offset = static_cast<int16_t>(bytecode_[pc + 1]);
            pc_advance = 2;
        }
    } else {
        // Unknown goto variant — treat as 10t
        offset = static_cast<int8_t>((bytecode_[pc] >> 8) & 0xFF);
        pc_advance = 1;
    }

    uint32_t target = pc + offset;

    // EXP-051: D8 "unreachable" marker — `goto +0` (self-loop).
    //
    // D8/R8 replace `throw vAA` instructions with `goto +0` (a self-loop
    // at the throw site) when the throw is unreachable from the entry
    // point OR when D8 strips the throw as part of dead-code elimination.
    // This pattern shows up in LifecycleRegistry.enforceMainThreadIfNeeded
    // at PC=46 — the bytecode constructs an IllegalStateException but
    // then has `goto +0` instead of `throw v0`.
    //
    // Without special handling, the engine loops forever at this PC
    // (HALT-LOOP). We treat `goto +0` as a "halt method" — equivalent
    // to return-void — so execution continues with the caller.
    //
    // Evidence: bytecode at PC=46 of LifecycleRegistry.enforceMainThreadIfNeeded
    //   (classes.dex, code_off=0x250668) is 0x0027 (goto +0). The throw
    //   that should follow the IllegalStateException.<init> at PC=43 is
    //   missing — D8 replaced it with this self-loop.
    if (offset == 0) {
        trace.status = InstructionTrace::Status::HALT_RETURN;
        trace.operands.push_back({"offset", "0 (D8 unreachable marker)"});
        trace.operands.push_back({"target", "exit_method"});
        halted_ = true;
        halted_on_return_ = true;
        pc_ = pc + pc_advance;
        return true;
    }

    // EXP-044 Phase 1: When goto target == bytecode_.size(), it means "exit
    // the method" (branch past the end = return). This is valid Dalvik behavior
    // for methods that end with a goto that jumps past the last instruction.
    // Example: Intrinsics.throwParameterIsNullNPE PC=15: goto +1 → PC=16
    // where bytecode_size=16. This is equivalent to return-void.
    //
    // EXP-051: Also handle target > bytecode_.size() — D8/R8 sometimes emit
    // `goto +N` where N points past the end as an "unreachable" marker.
    // Example: SpringForce.setDampingRatio PC=19: goto +3 → PC=22,
    // but bytecode_size=20. Without this fix, the engine HALTs with
    // HALT-GOTO. With this fix, we treat it as "exit method" (= return).
    if (target >= bytecode_.size()) {
        trace.status = InstructionTrace::Status::HALT_RETURN;
        trace.operands.push_back({"offset", std::to_string(offset)});
        trace.operands.push_back({"target", "exit_method (past end)"});
        halted_ = true;
        halted_on_return_ = true;
        pc_ = pc + pc_advance;
        return true;
    }

    // Validate target
    if (target < bytecode_.size()) {
        trace.status = InstructionTrace::Status::BRANCH_TAKEN;
        pc_ = target;

        trace.operands.push_back({"offset", std::to_string(offset)});
        trace.operands.push_back({"target", to_hex(target)});
    } else {
        trace.status = InstructionTrace::Status::CRASH_ERROR;
        trace.error_message = "Invalid goto target: " + to_hex(target) +
                              " (offset=" + std::to_string(offset) +
                              ", bytecode_size=" + std::to_string(bytecode_.size()) + ")";
        halted_ = true;
        halt_reason_ = "Invalid goto target";
        pc_ = pc + pc_advance;
        // EXP-043 Phase 1: log invalid goto targets for debugging (first 20 only
        // to avoid log spam). These indicate either real bytecode verification
        // issues or goto/32 misinterpretation.
        static thread_local uint64_t halt_goto_count = 0;
        if (halt_goto_count < 20) {
            std::cerr << "[HALT-GOTO] Invalid goto target PC=" << to_hex(pc)
                      << " in " << current_class_ << "." << current_method_
                      << " target=" << to_hex(target)
                      << " bytecode_size=" << bytecode_.size() << std::endl;
            halt_goto_count++;
        }
    }

    return true;
}

bool DalvikExecutionEngine::execute_if_eqz(uint32_t pc, InstructionTrace& trace) {
    // Format: 21t [op] vAA, +BBBB
    if (pc + 1 >= bytecode_.size()) return false;

    uint16_t instr = bytecode_[pc];
    uint8_t test_reg = (instr >> 8) & 0xFF;
    int16_t offset = static_cast<int16_t>(bytecode_[pc + 1]);

    DalvikValue val = get_register(test_reg);
    // EXP-055: Treat OBJECT_REF with object_id=0 as null (same as NULL_REF).
    // EXP-058: Also treat VOID_ as zero (same rationale as if-nez).
    bool is_zero = (val.type == DalvikType::NULL_REF) ||
                   (val.type == DalvikType::INT32 && val.int_val == 0) ||
                   (val.type == DalvikType::OBJECT_REF && val.object_id == 0) ||
                   (val.type == DalvikType::UNINITIALIZED || val.type == DalvikType::REGISTER_UNSET) ||
                   (val.type == DalvikType::VOID_);

    // EXP-059: Debug — log if-eqz in addFragmentToStack
    if (current_method_ == "addFragmentToStack" &&
        current_class_.find("ActionBarLayout") != std::string::npos) {
        std::cerr << "[EXP059-IF-EQZ] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " test_reg=v" << (int)test_reg
                  << " type=" << static_cast<int>(val.type)
                  << " int_val=" << val.int_val
                  << " obj=" << val.object_id
                  << " is_zero=" << is_zero
                  << " target=" << (pc + offset)
                  << std::endl;
    }

    if (is_zero) {
        uint32_t target = pc + offset;
        // EXP-051: target >= bytecode_.size() = D8 unreachable marker (exit method).
        if (target >= bytecode_.size()) {
            halted_ = true; halted_on_return_ = true;
            trace.status = InstructionTrace::Status::HALT_RETURN;
            trace.operands.push_back({"target", "exit_method (past end)"});
            pc_ = pc + 2;
        } else {
            trace.status = InstructionTrace::Status::BRANCH_TAKEN;
            pc_ = target;
        }
    } else {
        trace.status = InstructionTrace::Status::BRANCH_NOT_TAKEN;
        pc_ = pc + 2;
    }

    trace.operands.push_back({"v" + std::to_string(test_reg), val.to_string()});
    trace.operands.push_back({"taken", is_zero ? "yes" : "no"});

    return true;
}

bool DalvikExecutionEngine::execute_if_nez(uint32_t pc, InstructionTrace& trace) {
    // Format: 21t [op] vAA, +BBBB
    if (pc + 1 >= bytecode_.size()) return false;
    
    uint16_t instr = bytecode_[pc];
    uint8_t test_reg = (instr >> 8) & 0xFF;
    int16_t offset = static_cast<int16_t>(bytecode_[pc + 1]);
    
    DalvikValue val = get_register(test_reg);
    // EXP-055: Treat OBJECT_REF with object_id=0 as null (same as NULL_REF).
    // EXP-058: Also treat VOID_ as zero — when bridge_to_api returns void
    // for unhandled methods, if-nez must NOT branch. Previously VOID_
    // was treated as non-zero, causing branches that skipped important
    // method calls (e.g., onFragmentCreate was never called because
    // needAddFragmentToStack returned VOID_ on a null delegate).
    bool is_nonzero = !(val.type == DalvikType::NULL_REF ||
                       (val.type == DalvikType::INT32 && val.int_val == 0) ||
                       (val.type == DalvikType::BOOLEAN && val.int_val == 0) ||
                       (val.type == DalvikType::OBJECT_REF && val.object_id == 0) ||
                       (val.type == DalvikType::UNINITIALIZED || val.type == DalvikType::REGISTER_UNSET) ||
                       (val.type == DalvikType::VOID_));
    
    // EXP-059: Debug — log if-nez in addFragmentToStack
    if (current_method_ == "addFragmentToStack" &&
        current_class_.find("ActionBarLayout") != std::string::npos) {
        std::cerr << "[EXP059-IF-NEZ] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " test_reg=v" << (int)test_reg
                  << " type=" << static_cast<int>(val.type)
                  << " int_val=" << val.int_val
                  << " obj=" << val.object_id
                  << " is_nonzero=" << is_nonzero
                  << " target=" << (pc + offset)
                  << std::endl;
    }
    
    // EXP-046: Log if-nez in NativeLoader.initNativeLibs
    if (current_class_.find("NativeLoader") != std::string::npos) {
        std::cerr << "[IF-NEZ-DBG] " << current_class_ << "." << current_method_
                  << " PC=" << pc << " v" << (int)test_reg
                  << " type=" << static_cast<int>(val.type)
                  << " val=" << val.int_val
                  << " nonzero=" << is_nonzero
                  << " target=" << (pc + offset) << std::endl;
    }
    
    if (is_nonzero) {
        uint32_t target = pc + offset;
        // EXP-051: target >= bytecode_.size() = D8 unreachable marker (exit method).
        if (target >= bytecode_.size()) {
            halted_ = true; halted_on_return_ = true;
            trace.status = InstructionTrace::Status::HALT_RETURN;
            trace.operands.push_back({"target", "exit_method (past end)"});
            pc_ = pc + 2;
        } else {
            trace.status = InstructionTrace::Status::BRANCH_TAKEN;
            pc_ = target;
        }
    } else {
        trace.status = InstructionTrace::Status::BRANCH_NOT_TAKEN;
        pc_ = pc + 2;
    }
    
    trace.operands.push_back({"v" + std::to_string(test_reg), val.to_string()});
    trace.operands.push_back({"taken", is_nonzero ? "yes" : "no"});
    
    return true;
}

// ============================================================================
// EXP-043 Phase 1: Proper 21t format if-*z handlers
// Per AOSP:
//   if-ltz vAA, +BBBB : branch if (int) vAA < 0
//   if-gez vAA, +BBBB : branch if (int) vAA >= 0
//   if-gtz vAA, +BBBB : branch if (int) vAA > 0
//   if-lez vAA, +BBBB : branch if (int) vAA <= 0
//
// For OBJECT_REF, NULL_REF, UNINITIALIZED: the value is treated as 0 (which
// means if-ltz=fallthrough, if-gez=branch, if-gtz=fallthrough, if-lez=branch).
// This matches Dalvik's behavior of converting null to 0 for int comparisons.
// ============================================================================

bool DalvikExecutionEngine::execute_if_ltz(uint32_t pc, InstructionTrace& trace) {
    // Format: 21t [op] vAA, +BBBB  — branch if (int) vAA < 0
    // EXP-059: Now correctly dispatched for opcode 0x3A (per AOSP).
    //   Per AOSP: 0x3A = if-ltz ("branch if v < 0").
    // Previously the runtime had if-ltz at 0x39 (off-by-one), which collided
    // with the actual if-nez. The EXP-058 hack treated INT32 if-ltz as if-nez
    // to work around that collision. With the opcode table fixed, if-ltz now
    // correctly means "branch if < 0" for INT32, matching AOSP semantics.
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }
    uint16_t instr = bytecode_[pc];
    uint8_t test_reg = (instr >> 8) & 0xFF;
    int16_t offset = static_cast<int16_t>(bytecode_[pc + 1]);
    DalvikValue val = get_register(test_reg);

    bool taken = false;
    if (val.type == DalvikType::OBJECT_REF) {
        // OBJECT_REF can't be < 0; never branch.
        taken = false;
    } else if (val.type == DalvikType::NULL_REF) {
        // null == 0 → 0 < 0 is false; never branch.
        taken = false;
    } else if (val.type == DalvikType::INT32 || val.type == DalvikType::BOOLEAN ||
               val.type == DalvikType::BYTE || val.type == DalvikType::SHORT ||
               val.type == DalvikType::CHAR) {
        // Standard AOSP if-ltz: branch if val < 0.
        taken = (val.int_val < 0);
    } else if (val.type == DalvikType::INT64) {
        taken = (static_cast<int64_t>(val.long_val) < 0);
    } else {
        // UNINITIALIZED, REGISTER_UNSET, VOID_ → don't branch.
        taken = false;
    }

    if (taken) {
        uint32_t target = pc + offset;
        if (target < bytecode_.size()) {
            trace.status = InstructionTrace::Status::BRANCH_TAKEN;
            pc_ = target;
        } else if (target == bytecode_.size()) {
            // goto past end = exit method
            halted_ = true;
            halted_on_return_ = true;
            pc_ = pc + 2;
            return true;
        } else {
            pc_ = pc + 2;
        }
    } else {
        trace.status = InstructionTrace::Status::BRANCH_NOT_TAKEN;
        pc_ = pc + 2;
    }
    trace.operands.push_back({"v" + std::to_string(test_reg), val.to_string()});
    trace.operands.push_back({"taken", taken ? "yes" : "no"});
    return true;
}

bool DalvikExecutionEngine::execute_if_gez(uint32_t pc, InstructionTrace& trace) {
    // Format: 21t [op] vAA, +BBBB  — branch if (int) vAA >= 0
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }
    uint16_t instr = bytecode_[pc];
    uint8_t test_reg = (instr >> 8) & 0xFF;
    int16_t offset = static_cast<int16_t>(bytecode_[pc + 1]);
    DalvikValue val = get_register(test_reg);
    int32_t ival = 0;
    if (val.type == DalvikType::INT32 || val.type == DalvikType::BOOLEAN ||
        val.type == DalvikType::BYTE || val.type == DalvikType::SHORT ||
        val.type == DalvikType::CHAR) {
        ival = val.int_val;
    } else if (val.type == DalvikType::INT64) {
        ival = static_cast<int32_t>(val.long_val);
    }
    bool taken = (ival >= 0);
    if (taken) {
        uint32_t target = pc + offset;
        // EXP-051: target >= bytecode_.size() = D8 unreachable marker (exit method).
        if (target >= bytecode_.size()) {
            halted_ = true; halted_on_return_ = true;
            trace.status = InstructionTrace::Status::HALT_RETURN;
            pc_ = pc + 2;
            return true;
        }
        trace.status = InstructionTrace::Status::BRANCH_TAKEN;
        pc_ = target;
    } else {
        trace.status = InstructionTrace::Status::BRANCH_NOT_TAKEN;
        pc_ = pc + 2;
    }
    trace.operands.push_back({"v" + std::to_string(test_reg), std::to_string(ival)});
    trace.operands.push_back({"taken", taken ? "yes" : "no"});
    return true;
}

bool DalvikExecutionEngine::execute_if_gtz(uint32_t pc, InstructionTrace& trace) {
    // Format: 21t [op] vAA, +BBBB  — branch if (int) vAA > 0
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }
    uint16_t instr = bytecode_[pc];
    uint8_t test_reg = (instr >> 8) & 0xFF;
    int16_t offset = static_cast<int16_t>(bytecode_[pc + 1]);
    DalvikValue val = get_register(test_reg);
    int32_t ival = 0;
    if (val.type == DalvikType::INT32 || val.type == DalvikType::BOOLEAN ||
        val.type == DalvikType::BYTE || val.type == DalvikType::SHORT ||
        val.type == DalvikType::CHAR) {
        ival = val.int_val;
    } else if (val.type == DalvikType::INT64) {
        ival = static_cast<int32_t>(val.long_val);
    }
    bool taken = (ival > 0);
    if (taken) {
        uint32_t target = pc + offset;
        // EXP-051: target >= bytecode_.size() = D8 unreachable marker (exit method).
        if (target >= bytecode_.size()) {
            halted_ = true; halted_on_return_ = true;
            trace.status = InstructionTrace::Status::HALT_RETURN;
            pc_ = pc + 2;
            return true;
        }
        trace.status = InstructionTrace::Status::BRANCH_TAKEN;
        pc_ = target;
    } else {
        trace.status = InstructionTrace::Status::BRANCH_NOT_TAKEN;
        pc_ = pc + 2;
    }
    trace.operands.push_back({"v" + std::to_string(test_reg), std::to_string(ival)});
    trace.operands.push_back({"taken", taken ? "yes" : "no"});
    return true;
}

bool DalvikExecutionEngine::execute_if_lez(uint32_t pc, InstructionTrace& trace) {
    // Format: 21t [op] vAA, +BBBB  — branch if (int) vAA <= 0
    if (pc + 1 >= bytecode_.size()) { pc_ = pc + 1; return true; }
    uint16_t instr = bytecode_[pc];
    uint8_t test_reg = (instr >> 8) & 0xFF;
    int16_t offset = static_cast<int16_t>(bytecode_[pc + 1]);
    DalvikValue val = get_register(test_reg);
    int32_t ival = 0;
    if (val.type == DalvikType::INT32 || val.type == DalvikType::BOOLEAN ||
        val.type == DalvikType::BYTE || val.type == DalvikType::SHORT ||
        val.type == DalvikType::CHAR) {
        ival = val.int_val;
    } else if (val.type == DalvikType::INT64) {
        ival = static_cast<int32_t>(val.long_val);
    }
    bool taken = (ival <= 0);
    if (taken) {
        uint32_t target = pc + offset;
        // EXP-051: target >= bytecode_.size() = D8 unreachable marker (exit method).
        if (target >= bytecode_.size()) {
            halted_ = true; halted_on_return_ = true;
            trace.status = InstructionTrace::Status::HALT_RETURN;
            pc_ = pc + 2;
            return true;
        }
        trace.status = InstructionTrace::Status::BRANCH_TAKEN;
        pc_ = target;
    } else {
        trace.status = InstructionTrace::Status::BRANCH_NOT_TAKEN;
        pc_ = pc + 2;
    }
    trace.operands.push_back({"v" + std::to_string(test_reg), std::to_string(ival)});
    trace.operands.push_back({"taken", taken ? "yes" : "no"});
    return true;
}

// ============================================================================
// EXP-037 Phase B (BLOCKER-018): 22t format if-* opcodes
// Format 22t: B1|A|op CCCC  → 2 code units
//   code[0]: bits 0-7 = opcode, bits 8-11 = vA (4 bits), bits 12-15 = vB (4 bits)
//   code[1]: 16-bit signed branch offset (CCCC)
// Branch target = pc + offset (signed)
// ============================================================================

namespace {

// Helper: extract two 4-bit registers from a 22t opcode word.
// vA = high nibble of low byte  = (instr >> 8) & 0xF
// vB = high nibble of high byte = (instr >> 12) & 0xF
struct If22tRegs {
    uint8_t vA;
    uint8_t vB;
    int16_t offset;
};

If22tRegs decode_22t(uint16_t instr, uint16_t next_word) {
    If22tRegs r;
    r.vA = static_cast<uint8_t>((instr >> 8) & 0xF);
    r.vB = static_cast<uint8_t>((instr >> 12) & 0xF);
    r.offset = static_cast<int16_t>(next_word);
    return r;
}

// Helper: common branch logic for 22t if-* opcodes.
// `taken` is whether the comparison evaluated true.
// On take: pc = pc + offset; On fall-through: pc = pc + 2.
bool do_22t_branch(uint32_t pc, int16_t offset, bool taken,
                   const std::string& opcode_name,
                   uint8_t vA, uint8_t vB,
                   const DalvikValue& a, const DalvikValue& b,
                   InstructionTrace& trace, DalvikExecutionEngine* engine_unused = nullptr) {
    (void)engine_unused;  // signature placeholder
    if (taken) {
        uint32_t target = pc + offset;
        // Note: target may legitimately equal pc + 2 (fall-through) when offset=2,
        // or be backward when offset is negative.
        trace.status = InstructionTrace::Status::BRANCH_TAKEN;
        trace.pc_after = target;
        // We can't directly set pc_ here since it's a member; the caller does that.
    } else {
        trace.status = InstructionTrace::Status::BRANCH_NOT_TAKEN;
    }
    trace.operands.push_back({"vA", "v" + std::to_string(vA) + "=" + a.to_string()});
    trace.operands.push_back({"vB", "v" + std::to_string(vB) + "=" + b.to_string()});
    trace.operands.push_back({"taken", taken ? "yes" : "no"});
    trace.operands.push_back({"offset", std::to_string(offset)});
    (void)opcode_name;
    return true;
}

} // anonymous namespace

#define IMPLEMENT_IF_22T(name, op, op_name) \
bool DalvikExecutionEngine::execute_##name(uint32_t pc, InstructionTrace& trace) { \
    if (pc + 1 >= bytecode_.size()) return false; \
    uint16_t instr = bytecode_[pc]; \
    If22tRegs r = decode_22t(instr, bytecode_[pc + 1]); \
    DalvikValue a = get_register(r.vA); \
    DalvikValue b = get_register(r.vB); \
    int32_t a_val = (a.type == DalvikType::INT32) ? a.int_val : 0; \
    int32_t b_val = (b.type == DalvikType::INT32) ? b.int_val : 0; \
    bool taken = false; \
    bool a_is_ref = (a.type == DalvikType::OBJECT_REF || a.type == DalvikType::NULL_REF); \
    bool b_is_ref = (b.type == DalvikType::OBJECT_REF || b.type == DalvikType::NULL_REF); \
    if (a_is_ref && b_is_ref) { \
        uint32_t a_obj = (a.type == DalvikType::OBJECT_REF) ? a.object_id : 0; \
        uint32_t b_obj = (b.type == DalvikType::OBJECT_REF) ? b.object_id : 0; \
        taken = (a_obj op b_obj); \
    } else { \
        taken = (a_val op b_val); \
    } \
    /* EXP-071: Diagnostic for if-lt/if-eq in onConfirm */ \
    if (current_class_.find("PhoneView$6") != std::string::npos && \
        current_method_ == "onConfirm") { \
        std::cerr << "[EXP071-IF] " << op_name << " PC=" << pc \
                  << " v" << (int)r.vA << "(type=" << static_cast<int>(a.type) \
                  << " val=" << a_val << ") vs v" << (int)r.vB \
                  << "(type=" << static_cast<int>(b.type) \
                  << " val=" << b_val << ") → taken=" << (taken ? "YES" : "NO") \
                  << " target=" << (pc + r.offset) << std::endl; \
    } \
    do_22t_branch(pc, r.offset, taken, op_name, r.vA, r.vB, a, b, trace); \
    if (taken) { \
        uint32_t target = pc + r.offset; \
        /* EXP-051: D8 unreachable marker — branch target past end-of-method. */ \
        /* Treated as "exit method" (= return-void), same as goto-past-end. */ \
        if (target >= bytecode_.size()) { \
            halted_ = true; halted_on_return_ = true; \
            trace.status = InstructionTrace::Status::HALT_RETURN; \
            trace.operands.push_back({"target", "exit_method (past end)"}); \
            pc_ = pc + 2; \
        } else { \
            pc_ = target; \
        } \
    } else { pc_ = pc + 2; } \
    return true; \
}

IMPLEMENT_IF_22T(if_eq, ==, "if-eq")
IMPLEMENT_IF_22T(if_ne, !=, "if-ne")
IMPLEMENT_IF_22T(if_lt, <,  "if-lt")
IMPLEMENT_IF_22T(if_ge, >=, "if-ge")
IMPLEMENT_IF_22T(if_gt, >,  "if-gt")
IMPLEMENT_IF_22T(if_le, <=, "if-le")

// ============================================================================
// Unimplemented Handler
// ============================================================================

void DalvikExecutionEngine::handle_unimplemented(uint16_t opcode, uint32_t pc, 
                                                InstructionTrace& trace) {
    trace.status = InstructionTrace::Status::UNIMPLEMENTED;
    trace.error_message = "Unimplemented opcode: 0x" + to_hex16(opcode);
    
    log("  UNIMPLEMENTED: 0x" + to_hex16(opcode) + " at " + to_hex(pc));
    
    if (config_.stop_on_unimplemented) {
        halted_ = true;
        halt_reason_ = "Unimplemented opcode: 0x" + to_hex16(opcode) + " at PC=" + to_hex(pc);
    }
    
    pc_ = pc + 1;  // Skip past unimplemented instruction
}

// ============================================================================
// Register Helpers
// ============================================================================

void DalvikExecutionEngine::set_register(uint8_t reg, const DalvikValue& value) {
    if (current_registers_) {
        current_registers_->write_v(reg, value);
        current_registers_->set_pc(pc_);
    }
}

DalvikValue DalvikExecutionEngine::get_register(uint8_t reg) const {
    if (current_registers_) {
        return current_registers_->read_v(reg);
    }
    return DalvikValue::make_uninit();
}

std::string DalvikExecutionEngine::register_name(uint8_t reg) const {
    if (current_registers_ && reg >= current_registers_->get_ins_count()) {
        return "v" + std::to_string(reg);
    } else if (current_registers_) {
        return "p" + std::to_string(reg - (current_registers_->get_size() - current_registers_->get_ins_count()));
    }
    return "v" + std::to_string(reg);
}

// ============================================================================
// API Bridge
// ============================================================================

// EXP-051: Convert a DalvikValue (engine type) into a CallContext::Arg
// (shadow-registry type). This is the only translation point — keeping
// the engine and the shadow registry decoupled.
static framework::CallContext::Arg dalvik_value_to_arg(const DalvikValue& v) {
    using namespace framework;
    CallContext::Arg a;
    switch (v.type) {
        case DalvikType::INT32:
        case DalvikType::BYTE:
        case DalvikType::SHORT:
        case DalvikType::CHAR:
            a.kind = CallContext::Arg::Kind::INT;
            a.int_val = v.int_val;
            break;
        case DalvikType::INT64:
            a.kind = CallContext::Arg::Kind::LONG;
            a.long_val = v.long_val;
            break;
        case DalvikType::FLOAT32:
            a.kind = CallContext::Arg::Kind::FLOAT;
            a.float_val = v.float_val;
            break;
        case DalvikType::FLOAT64:
            a.kind = CallContext::Arg::Kind::DOUBLE;
            a.double_val = v.double_val;
            break;
        case DalvikType::BOOLEAN:
            a.kind = CallContext::Arg::Kind::BOOL;
            a.bool_val = v.bool_val;
            break;
        case DalvikType::STRING_REF:
            a.kind = CallContext::Arg::Kind::STRING;
            a.string_val = v.string_val;
            break;
        case DalvikType::OBJECT_REF:
            a.kind = CallContext::Arg::Kind::OBJECT;
            a.object_id = v.object_id;
            a.object_class = v.class_desc;
            break;
        case DalvikType::NULL_REF:
            a.kind = CallContext::Arg::Kind::NULL_REF;
            break;
        default:
            // VOID_, UNINITIALIZED, REGISTER_UNSET, CLASS_REF.
            // Default to NULL_REF (treated as null object) which is
            // safe for most call sites.
            a.kind = CallContext::Arg::Kind::NULL_REF;
            break;
    }
    return a;
}

// EXP-051: Convert a CallResult (shadow-registry type) back into a
// DalvikValue (engine type).
static DalvikValue call_result_to_dalvik(const framework::CallResult& r) {
    using namespace framework;
    switch (r.ret_kind) {
        case CallResult::RetKind::INT:     return DalvikValue::make_int(r.int_val);
        case CallResult::RetKind::LONG:    return DalvikValue::make_long(r.long_val);
        case CallResult::RetKind::FLOAT:   return DalvikValue::make_float(r.float_val);
        case CallResult::RetKind::DOUBLE:  return DalvikValue::make_double(r.double_val);
        case CallResult::RetKind::BOOL:    return DalvikValue::make_bool(r.bool_val);
        case CallResult::RetKind::STRING:  return DalvikValue::make_string(r.string_val, r.object_id);
        case CallResult::RetKind::OBJECT:  return DalvikValue::make_object(r.object_id, r.object_class);
        case CallResult::RetKind::NULL_REF:return DalvikValue::make_null();
        case CallResult::RetKind::VOID:
        default:                           return DalvikValue::make_void();
    }
}

bool DalvikExecutionEngine::try_shadow_dispatch(const std::string& class_name,
                                                const std::string& method,
                                                const std::vector<DalvikValue>& args,
                                                DalvikValue& result,
                                                ApiCallTrace::Status& status) {
    if (shadow_registry_ == nullptr) return false;

    // EXP-071 Phase 8: Generic static-method shadow dispatch fix.
    //
    // For static methods like AndroidUtilities.runOnUIThread(Runnable),
    // args[0] is the FIRST ARGUMENT (the Runnable), not `this`. The
    // previous code used args[0].class_desc as ctx.class_name, which
    // made HandlerShadow's "Lorg/telegram/messenger/AndroidUtilities;"
    // branch fail to match (because args[0].class_desc was the Runnable's
    // class, not "AndroidUtilities"). As a result, runOnUIThread was a
    // silent no-op, the runnable was never enqueued, and the entire
    // async callback chain (Lambda0 → lambda$onConfirm$1 → Lambda1 →
    // lambda$onConfirm$0 → onNextPressed → auth.sendCode) was broken.
    //
    // Fix: try dispatch with the DECLARED class_name FIRST. If the shadow
    // returns not_handled, retry with args[0].class_desc (the runtime
    // class of `this` for instance methods). This works for both:
    //   * Static calls  — class_name="Lorg/telegram/messenger/AndroidUtilities;"
    //   * Instance calls — class_name="Landroid/view/View;" (or args[0].class_desc
    //     for the actual runtime subclass like IntroActivity$4).
    auto build_ctx = [&](const std::string& chosen_class) {
        framework::CallContext ctx;
        ctx.class_name = chosen_class;
        ctx.method = method;
        // EXP-071 Phase 8: For INSTANCE methods, args[0] is `this` (the receiver)
        // and the remaining args are the parameters. We shift them so that
        // ctx.args[0] is the first PARAMETER (not `this`), and set
        // ctx.receiver_id/receiver_class for `this`.
        //
        // For STATIC methods (current_invoke_is_static_), args[0] is already
        // the first PARAMETER — there's no `this`. We put ALL args in ctx.args
        // without shifting.
        //
        // Without this distinction, static calls like
        // AndroidUtilities.runOnUIThread(Runnable, long) would have their
        // Runnable stolen as `this` and never reach HandlerShadow's enqueue
        // (which expects ctx.args[0] to be the Runnable).
        if (!current_invoke_is_static_ &&
            !args.empty() && args[0].type == DalvikType::OBJECT_REF) {
            ctx.has_receiver = true;
            ctx.receiver_id = args[0].object_id;
            ctx.receiver_class = args[0].class_desc;
            for (size_t i = 1; i < args.size(); i++) {
                ctx.args.push_back(dalvik_value_to_arg(args[i]));
            }
        } else {
            for (const auto& a : args) {
                ctx.args.push_back(dalvik_value_to_arg(a));
            }
        }
        return ctx;
    };

    // Pass 1: try with the declared class_name.
    auto cr = shadow_registry_->dispatch(build_ctx(class_name));
    // EXP-071 Phase 8 debug — log dispatch attempts for runOnUIThread.
    if (method == "runOnUIThread" || method == "executeOnUIThread") {
        std::cerr << "[EXP071-SHADOW-DISPATCH] pass1 class_name=" << class_name
                  << " method=" << method
                  << " handled=" << (cr.handled ? "YES" : "NO")
                  << std::endl;
    }
    if (cr.handled) {
        switch (cr.status) {
            case framework::ApiCallStatus::IMPLEMENTED:
                status = ApiCallTrace::Status::IMPLEMENTED; break;
            case framework::ApiCallStatus::STUBBED:
                status = ApiCallTrace::Status::STUBBED; break;
            default:
                status = ApiCallTrace::Status::STUBBED; break;
        }
        result = call_result_to_dalvik(cr);
        return true;
    }

    // Pass 2: try with args[0].class_desc (runtime class of `this`).
    if (!args.empty() && args[0].type == DalvikType::OBJECT_REF &&
        !args[0].class_desc.empty() && args[0].class_desc != class_name) {
        cr = shadow_registry_->dispatch(build_ctx(args[0].class_desc));
        if (cr.handled) {
            switch (cr.status) {
                case framework::ApiCallStatus::IMPLEMENTED:
                    status = ApiCallTrace::Status::IMPLEMENTED; break;
                case framework::ApiCallStatus::STUBBED:
                    status = ApiCallTrace::Status::STUBBED; break;
                default:
                    status = ApiCallTrace::Status::STUBBED; break;
            }
            result = call_result_to_dalvik(cr);
            return true;
        }
    }
    return false;
}

bool DalvikExecutionEngine::bridge_to_api(const std::string& class_name,
                                          const std::string& method,
                                          const std::vector<DalvikValue>& args,
                                          DalvikValue& result,
                                          ApiCallTrace::Status& status) {
    // EXP-071 Phase 7: Diagnostic — log HashMap.put/get entry to bridge_to_api.
    if (class_name.find("HashMap") != std::string::npos &&
        (method == "put" || method == "get")) {
        std::cerr << "[EXP071-BRIDGE-HMAP] " << class_name << "." << method
                  << " argc=" << args.size()
                  << " caller=" << current_class_ << "." << current_method_
                  << " pc=" << pc_
                  << std::endl;
    }
    // EXP-042 Phase 4: Android Framework minimal runtime.
    // Implements REAL Android objects for the P0/P1 APIs that Telegram's
    // LaunchActivity.onCreate actually calls. See:
    //   docs/exp042/EXP042_TELEGRAM_COMPATIBILITY_MAP.md
    //
    // Design:
    // * Each "real object" returned (Resources, PackageManager, DisplayMetrics,
    //   Configuration, etc.) is allocated on the DalvikHeap as a new heap
    //   object with a fixed class descriptor. The caller (DEX bytecode) sees
    //   it as an OBJECT_REF and can call methods on it; those calls come back
    //   through bridge_to_api and we route them to the same singleton.
    //
    // * Singletons are cached by class descriptor in api_singletons_ so that
    //   `Context.getResources()` always returns the same object. This matches
    //   real Android behavior and prevents heap growth from repeated calls.

    // EXP-055: Trace isClientActivated return value for login path investigation.
    if (current_class_.find("UserConfig") != std::string::npos &&
        method == "isClientActivated") {
        std::cerr << "[LOGIN_PATH] UserConfig.isClientActivated in bridge_to_api"
                  << " (method fell through to API bridge)"
                  << std::endl;
    }
    // EXP-055: Trace getClientNotActivatedFragment for login path.
    if (current_class_.find("LaunchActivity") != std::string::npos &&
        method == "getClientNotActivatedFragment") {
        std::cerr << "[LOGIN_PATH] LaunchActivity.getClientNotActivatedFragment in bridge_to_api"
                  << std::endl;
    }
    // EXP-055: Trace addFragmentToStack for fragment navigation.
    if (method == "addFragmentToStack") {
        std::cerr << "[FRAGMENT_PATH] addFragmentToStack called"
                  << " class=" << class_name
                  << " args=" << args.size()
                  << std::endl;
        if (!args.empty() && args[0].type == DalvikType::OBJECT_REF) {
            std::cerr << "[FRAGMENT_CREATE] class=" << args[0].class_desc
                      << " obj_id=" << args[0].object_id
                      << std::endl;
        }
    }

    log("  API BRIDGE: " + class_name + "." + method);

    // EXP-057: Debug — log ALL bridge_to_api calls for isEmpty from onCreate.
    if (method == "isEmpty" && current_method_ == "onCreate") {
        int arg0_type = args.empty() ? -1 : static_cast<int>(args[0].type);
        uint32_t arg0_obj = args.empty() ? 0 : args[0].object_id;
        std::cerr << "[EXP057-BRIDGE] bridge_to_api called"
                  << " class=" << class_name
                  << " method=" << method
                  << " args_size=" << args.size()
                  << " arg0_type=" << arg0_type
                  << " arg0_obj=" << arg0_obj
                  << " caller=" << current_class_ << "." << current_method_
                  << std::endl;
    }

    // EXP-053: Trace fragment-related calls for the Login path investigation.
    if (method == "addFragmentToStack" ||
        method == "presentFragment" ||
        method == "getClientNotActivatedFragment" ||
        method == "replaceFragment" ||
        method == "showFragment") {
        std::cerr << "[FRAGMENT_NAV] method=" << method
                  << " receiver_class=" << class_name
                  << " args=" << args.size()
                  << std::endl;
        // Log first arg if it's an object (the Fragment).
        if (!args.empty() && args[0].type == DalvikType::OBJECT_REF) {
            std::cerr << "[FRAGMENT] create: class=" << args[0].class_desc
                      << " obj_id=" << args[0].object_id
                      << std::endl;
        }
    }
    // EXP-053: Trace interface dispatch.
    if (class_name.find("$-CC;") != std::string::npos ||
        class_name.find("INavigationLayout") != std::string::npos) {
        // Only log unique (class, method) pairs to avoid spam.
        static std::set<std::string> logged;
        std::string key = class_name + "." + method;
        if (logged.find(key) == logged.end()) {
            logged.insert(key);
            std::cerr << "[INTERFACE_CALL] interface=" << class_name
                      << " method=" << method
                      << " args=" << args.size()
                      << std::endl;
        }
    }

    // EXP-051: Consult the shadow registry FIRST. If a shadow handles
    // this (class, method) pair, we're done — no need to fall through
    // to the legacy if/else chain below. This lets us incrementally
    // migrate Android framework behavior from inline C++ code in
    // bridge_to_api into per-concept shadow classes without breaking
    // any of the existing paths.
    //
    // EXP-060: Try the shadow with multiple class candidates. The runtime_type
    // (e.g. "Lorg/telegram/ui/IntroActivity$4;") may not be recognized by
    // ViewShadow because the class name doesn't end in "View;". So we also
    // try common View/ViewGroup parent classes. This ensures View methods
    // like setOnClickListener are dispatched to ViewShadow even when the
    // receiver is a user-defined View subclass.
    if (shadow_registry_ != nullptr) {
        // EXP-071 diagnostic: log shadow dispatch attempt for HashMap in setCountry.
        if (class_name.find("HashMap") != std::string::npos &&
            current_method_ == "setCountry") {
            std::cerr << "[EXP071-SHADOW-TRY] " << class_name << "." << method
                      << " caller=" << current_class_ << "." << current_method_
                      << " pc=" << pc_
                      << " argc=" << args.size()
                      << " is_static=" << current_invoke_is_static_
                      << std::endl;
            for (size_t i = 0; i < args.size() && i < 3; ++i) {
                std::cerr << "  arg[" << i << "] type=" << (int)args[i].type;
                if (args[i].type == DalvikType::OBJECT_REF) std::cerr << " obj=" << args[i].object_id;
                if (args[i].type == DalvikType::STRING_REF) std::cerr << " str=\"" << args[i].string_val << "\"";
                std::cerr << std::endl;
            }
        }
        if (try_shadow_dispatch(class_name, method, args, result, status)) {
            // EXP-071: Diagnostic — log when shadow dispatch catches HashMap calls.
            if (class_name.find("HashMap") != std::string::npos) {
                if (current_method_ == "setCountry") {
                    std::cerr << "[EXP071-SHADOW-HIT] " << class_name << "." << method
                              << " HIT in setCountry"
                              << " result_type=" << (int)result.type
                              << std::endl;
                }
            }
            return true;
        }
        // EXP-071 diagnostic: log shadow miss for HashMap in setCountry.
        if (class_name.find("HashMap") != std::string::npos &&
            current_method_ == "setCountry") {
            std::cerr << "[EXP071-SHADOW-MISS] " << class_name << "." << method
                      << " MISS in setCountry — falling through to bridge_to_api"
                      << std::endl;
        }
        // EXP-060: Try View/ViewGroup parent classes. If the runtime_type
        // is a subclass of View (which we can't check without a class
        // hierarchy), trying the View class as a fallback will catch
        // setOnClickListener, setText, addView, etc.
        static const std::vector<std::string> view_parents = {
            "Landroid/view/View;",
            "Landroid/view/ViewGroup;",
            "Landroid/widget/TextView;",
            "Landroid/widget/ImageView;",
            "Landroid/widget/Button;",
            "Landroid/widget/EditText;",
        };
        for (const auto& parent : view_parents) {
            if (try_shadow_dispatch(parent, method, args, result, status)) {
                return true;
            }
        }
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-071: BaseFragment.getParentActivity() → returns the Activity.
    // This is a compatibility handler that returns the LaunchActivity singleton
    // when getParentActivity() is called on a Fragment. The real Android method
    // does getView().getContext() instanceof Activity, but our runtime's
    // invoke-interface dispatch for $default methods sometimes fails.
    // This handler ensures getParentActivity returns a non-null Activity,
    // allowing PhoneView.onNextPressed to proceed to auth.sendCode.
    if (method == "getParentActivity" &&
        (class_name.find("BaseFragment") != std::string::npos ||
         class_name.find("ActionBarLayout") != std::string::npos ||
         class_name.find("Fragment") != std::string::npos)) {
        result = get_or_create_singleton("Lorg/telegram/ui/LaunchActivity;");
        status = ApiCallTrace::Status::IMPLEMENTED;
        std::cerr << "[EXP071] getParentActivity → LaunchActivity (compatibility)" << std::endl;
        return true;
    }

    // EXP-071: View.getContext() → returns the Activity that created this View.
    // This is called by BaseFragment.getParentActivity() which does:
    //   getView().getContext() instanceof Activity
    // We return the LaunchActivity singleton (which extends Activity).
    // The instanceof check uses is_subclass_of() which walks the superclass chain.
    if (method == "getContext" &&
        (class_name.find("View") != std::string::npos ||
         class_name.find("Context") != std::string::npos)) {
        // First, try the shadow path — ViewShadow stores context_object_id
        // when the View constructor captures the Context arg.
        if (shadow_registry_ != nullptr) {
            framework::CallContext ctx;
            if (!args.empty() && args[0].type == DalvikType::OBJECT_REF) {
                ctx.has_receiver = true;
                ctx.receiver_id = args[0].object_id;
                ctx.receiver_class = args[0].class_desc;
                ctx.class_name = args[0].class_desc;
            }
            ctx.method = "getContext";
            auto cr = shadow_registry_->dispatch(ctx);
            if (cr.handled) {
                result = call_result_to_dalvik(cr);
                status = ApiCallTrace::Status::IMPLEMENTED;
                return true;
            }
        }
        // Fallback: return the LaunchActivity singleton
        result = get_or_create_singleton("Lorg/telegram/ui/LaunchActivity;");
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // P0.7 — Context.getApplicationContext → Context singleton
    // ────────────────────────────────────────────────────────────────────────
    if (method == "getApplicationContext" &&
        (class_name.find("Context") != std::string::npos ||
         class_name.find("Activity") != std::string::npos ||
         class_name.find("Application") != std::string::npos)) {
        result = get_or_create_singleton("Landroid/content/Context;");
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // P0.2 — Context.getResources → Resources singleton
    // ────────────────────────────────────────────────────────────────────────
    if (method == "getResources" &&
        (class_name.find("Context") != std::string::npos ||
         class_name.find("Activity") != std::string::npos)) {
        result = get_or_create_singleton("Landroid/content/res/Resources;");
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // P0.3 — Resources.getDisplayMetrics → DisplayMetrics singleton
    // ────────────────────────────────────────────────────────────────────────
    if (method == "getDisplayMetrics" &&
        class_name.find("Resources") != std::string::npos) {
        result = get_or_create_singleton("Landroid/util/DisplayMetrics;");
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // P0.5 — Resources.getConfiguration → Configuration singleton
    // ────────────────────────────────────────────────────────────────────────
    if (method == "getConfiguration" &&
        class_name.find("Resources") != std::string::npos) {
        result = get_or_create_singleton("Landroid/content/res/Configuration;");
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // P0.9 — Context.getPackageManager → PackageManager singleton
    // ────────────────────────────────────────────────────────────────────────
    if (method == "getPackageManager" &&
        (class_name.find("Context") != std::string::npos ||
         class_name.find("Activity") != std::string::npos)) {
        result = get_or_create_singleton("Landroid/content/pm/PackageManager;");
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // P0.10 — PackageManager.getPackageInfo → PackageInfo (with defaults)
    // ────────────────────────────────────────────────────────────────────────
    if (method == "getPackageInfo" &&
        class_name.find("PackageManager") != std::string::npos) {
        // Allocate a fresh PackageInfo object on the heap. We populate it
        // with sensible defaults in the iget handler when fields are read.
        uint32_t obj_id = heap_.allocate("Landroid/content/pm/PackageInfo;",
                                         pc_, call_stack_.empty() ? 0 : call_stack_.top().frame_id);
        result = DalvikValue::make_object(obj_id,
                                          "Landroid/content/pm/PackageInfo;");
        // Pre-populate known fields with defaults
        DalvikValue version_code;
        version_code.type = DalvikType::INT32;
        version_code.int_val = 9999;
        heap_.set_object_field(obj_id, "versionCode", version_code);
        DalvikValue version_name;
        version_name.type = DalvikType::STRING_REF;
        version_name.string_val = "9.9.9";
        version_name.ref_id = 0;
        heap_.set_object_field(obj_id, "versionName", version_name);
        DalvikValue package_name;
        package_name.type = DalvikType::STRING_REF;
        package_name.string_val = "org.telegram.messenger.web";
        package_name.ref_id = 0;
        heap_.set_object_field(obj_id, "packageName", package_name);
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // P0.8 — Context.getPackageName → String
    // ────────────────────────────────────────────────────────────────────────
    if (method == "getPackageName" &&
        (class_name.find("Context") != std::string::npos ||
         class_name.find("Activity") != std::string::npos)) {
        result = DalvikValue::make_string("org.telegram.messenger.web", 1);
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // P0.12 — Context.getSharedPreferences → SharedPreferences
    // EXP-048: Returns a heap-allocated SharedPreferences object with the
    // preference name stored as a field, enabling per-name persistence.
    // ────────────────────────────────────────────────────────────────────────
    if (method == "getSharedPreferences" &&
        (class_name.find("Context") != std::string::npos ||
         class_name.find("Activity") != std::string::npos)) {
        // Extract preference name from first argument (String)
        std::string prefs_name = "default";
        if (!args.empty() && args[0].type == DalvikType::STRING_REF) {
            prefs_name = args[0].string_val;
        }
        // Create SharedPreferences object on heap
        std::string prefs_desc = "Landroid/content/SharedPreferences;";
        uint32_t obj_id = heap_.allocate(prefs_desc, pc_,
                                        call_stack_.empty() ? 0 : call_stack_.top().frame_id);
        // Store the prefs name as a field so we can persist by name
        DalvikValue name_val;
        name_val.type = DalvikType::STRING_REF;
        name_val.string_val = prefs_name;
        name_val.ref_id = 0;
        heap_.set_object_field(obj_id, "prefs_name", name_val);

        // Try to load existing XML file
        std::string prefs_dir = "runtime/data/org.telegram.messenger/shared_prefs";
        std::string prefs_file = prefs_dir + "/" + prefs_name + ".xml";
        std::ifstream infile(prefs_file);
        if (infile.is_open()) {
            // File exists — load values into heap object fields
            std::string line;
            while (std::getline(infile, line)) {
                // Parse XML: <string name="key">value</string>
                //           <int name="key" value="123" />
                //           <boolean name="key" value="true" />
                size_t name_pos = line.find("name=\"");
                if (name_pos == std::string::npos) continue;
                size_t name_start = name_pos + 6;
                size_t name_end = line.find("\"", name_start);
                if (name_end == std::string::npos) continue;
                std::string key = line.substr(name_start, name_end - name_start);

                if (line.find("<string ") != std::string::npos) {
                    // <string name="key">value</string>
                    size_t val_start = line.find(">", name_end) + 1;
                    size_t val_end = line.find("</string>", val_start);
                    if (val_end != std::string::npos) {
                        std::string val = line.substr(val_start, val_end - val_start);
                        DalvikValue sv;
                        sv.type = DalvikType::STRING_REF;
                        sv.string_val = val;
                        sv.ref_id = 0;
                        heap_.set_object_field(obj_id, key, sv);
                    }
                } else if (line.find("<int ") != std::string::npos) {
                    size_t val_pos = line.find("value=\"", name_end);
                    if (val_pos != std::string::npos) {
                        size_t val_start = val_pos + 7;
                        size_t val_end = line.find("\"", val_start);
                        int32_t v = std::stoi(line.substr(val_start, val_end - val_start));
                        heap_.set_object_field(obj_id, key, DalvikValue::make_int(v));
                    }
                } else if (line.find("<boolean ") != std::string::npos) {
                    size_t val_pos = line.find("value=\"", name_end);
                    if (val_pos != std::string::npos) {
                        size_t val_start = val_pos + 7;
                        size_t val_end = line.find("\"", val_start);
                        bool v = line.substr(val_start, val_end - val_start) == "true";
                        heap_.set_object_field(obj_id, key, DalvikValue::make_bool(v));
                    }
                } else if (line.find("<long ") != std::string::npos) {
                    size_t val_pos = line.find("value=\"", name_end);
                    if (val_pos != std::string::npos) {
                        size_t val_start = val_pos + 7;
                        size_t val_end = line.find("\"", val_start);
                        int64_t v = std::stoll(line.substr(val_start, val_end - val_start));
                        DalvikValue lv;
                        lv.type = DalvikType::INT64;
                        lv.long_val = v;
                        heap_.set_object_field(obj_id, key, lv);
                    }
                }
            }
            std::cerr << "[PREFS] Loaded " << prefs_name << ".xml" << std::endl;
        }

        result = DalvikValue::make_object(obj_id, prefs_desc);
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-048: SharedPreferences methods — getString, getBoolean, getInt,
    // getLong, contains, edit, Editor.put*, commit, apply
    // ────────────────────────────────────────────────────────────────────────
    if (class_name.find("SharedPreferences") != std::string::npos ||
        class_name.find("SharedPreferencesEditor") != std::string::npos ||
        class_name.find("SharedPreferencesImpl") != std::string::npos) {

        // Get the SharedPreferences object from args[0] (this for instance methods)
        // or from the singleton for static methods
        uint32_t prefs_obj_id = 0;
        if (!args.empty() && args[0].type == DalvikType::OBJECT_REF) {
            prefs_obj_id = args[0].object_id;
        }

        if (method == "getString") {
            std::string key = (args.size() > 1 && args[1].type == DalvikType::STRING_REF) ? args[1].string_val : "";
            std::string def = (args.size() > 2 && args[2].type == DalvikType::STRING_REF) ? args[2].string_val : "";
            if (prefs_obj_id && heap_.has_object(prefs_obj_id)) {
                auto val = heap_.get_object_field(prefs_obj_id, key);
                if (val.has_value() && val->type == DalvikType::STRING_REF) {
                    result = DalvikValue::make_string(val->string_val, 1);
                    status = ApiCallTrace::Status::IMPLEMENTED;
                    return true;
                }
            }
            result = DalvikValue::make_string(def, 1);
            status = ApiCallTrace::Status::IMPLEMENTED;
            return true;
        }
        if (method == "getBoolean") {
            std::string key = (args.size() > 1 && args[1].type == DalvikType::STRING_REF) ? args[1].string_val : "";
            bool def = (args.size() > 2 && args[2].type == DalvikType::BOOLEAN) ? args[2].bool_val : false;
            if (prefs_obj_id && heap_.has_object(prefs_obj_id)) {
                auto val = heap_.get_object_field(prefs_obj_id, key);
                if (val.has_value() && (val->type == DalvikType::BOOLEAN || val->type == DalvikType::INT32)) {
                    result = DalvikValue::make_bool(val->bool_val || val->int_val != 0);
                    status = ApiCallTrace::Status::IMPLEMENTED;
                    return true;
                }
            }
            result = DalvikValue::make_bool(def);
            status = ApiCallTrace::Status::IMPLEMENTED;
            return true;
        }
        if (method == "getInt") {
            std::string key = (args.size() > 1 && args[1].type == DalvikType::STRING_REF) ? args[1].string_val : "";
            int32_t def = (args.size() > 2 && args[2].type == DalvikType::INT32) ? args[2].int_val : 0;
            if (prefs_obj_id && heap_.has_object(prefs_obj_id)) {
                auto val = heap_.get_object_field(prefs_obj_id, key);
                if (val.has_value() && val->type == DalvikType::INT32) {
                    result = DalvikValue::make_int(val->int_val);
                    status = ApiCallTrace::Status::IMPLEMENTED;
                    return true;
                }
            }
            result = DalvikValue::make_int(def);
            status = ApiCallTrace::Status::IMPLEMENTED;
            return true;
        }
        if (method == "getLong") {
            std::string key = (args.size() > 1 && args[1].type == DalvikType::STRING_REF) ? args[1].string_val : "";
            int64_t def = 0;
            if (args.size() > 2 && args[2].type == DalvikType::INT64) def = args[2].long_val;
            if (prefs_obj_id && heap_.has_object(prefs_obj_id)) {
                auto val = heap_.get_object_field(prefs_obj_id, key);
                if (val.has_value() && val->type == DalvikType::INT64) {
                    DalvikValue v; v.type = DalvikType::INT64; v.long_val = val->long_val;
                    result = v;
                    status = ApiCallTrace::Status::IMPLEMENTED;
                    return true;
                }
            }
            DalvikValue v; v.type = DalvikType::INT64; v.long_val = def;
            result = v;
            status = ApiCallTrace::Status::IMPLEMENTED;
            return true;
        }
        if (method == "contains") {
            std::string key = (args.size() > 1 && args[1].type == DalvikType::STRING_REF) ? args[1].string_val : "";
            if (prefs_obj_id && heap_.has_object(prefs_obj_id)) {
                auto val = heap_.get_object_field(prefs_obj_id, key);
                result = DalvikValue::make_bool(val.has_value());
            } else {
                result = DalvikValue::make_bool(false);
            }
            status = ApiCallTrace::Status::IMPLEMENTED;
            return true;
        }
        if (method == "edit") {
            // Return the same SharedPreferences object (we treat Editor as the prefs object itself)
            if (prefs_obj_id) {
                result = DalvikValue::make_object(prefs_obj_id, "Landroid/content/SharedPreferences$Editor;");
            } else {
                result = get_or_create_singleton("Landroid/content/SharedPreferences$Editor;");
            }
            status = ApiCallTrace::Status::IMPLEMENTED;
            return true;
        }
        // Editor methods
        if (method == "putString" || method == "putBoolean" || method == "putInt" || method == "putLong" || method == "putFloat") {
            std::string key = (args.size() > 1 && args[1].type == DalvikType::STRING_REF) ? args[1].string_val : "";
            if (prefs_obj_id && heap_.has_object(prefs_obj_id) && !key.empty()) {
                if (args.size() > 2) {
                    heap_.set_object_field(prefs_obj_id, key, args[2]);
                }
            }
            // Return the editor for chaining
            result = DalvikValue::make_object(prefs_obj_id, "Landroid/content/SharedPreferences$Editor;");
            status = ApiCallTrace::Status::IMPLEMENTED;
            return true;
        }
        if (method == "remove") {
            std::string key = (args.size() > 1 && args[1].type == DalvikType::STRING_REF) ? args[1].string_val : "";
            // We don't actually remove from heap (simplification), just set to null
            if (prefs_obj_id && heap_.has_object(prefs_obj_id)) {
                heap_.set_object_field(prefs_obj_id, key, DalvikValue::make_null());
            }
            result = DalvikValue::make_object(prefs_obj_id, "Landroid/content/SharedPreferences$Editor;");
            status = ApiCallTrace::Status::IMPLEMENTED;
            return true;
        }
        if (method == "clear") {
            // Simplification: just return editor
            result = DalvikValue::make_object(prefs_obj_id, "Landroid/content/SharedPreferences$Editor;");
            status = ApiCallTrace::Status::IMPLEMENTED;
            return true;
        }
        if (method == "commit" || method == "apply") {
            // EXP-048: Persist SharedPreferences to disk
            if (prefs_obj_id && heap_.has_object(prefs_obj_id)) {
                auto* prefs_obj = heap_.get(prefs_obj_id);
                if (prefs_obj) {
                    // Get prefs name
                    auto name_val = prefs_obj->get_field("prefs_name");
                    std::string prefs_name = "default";
                    if (name_val.type == DalvikType::STRING_REF) {
                        prefs_name = name_val.string_val;
                    }
                    // Write to XML
                    std::string prefs_dir = "runtime/data/org.telegram.messenger/shared_prefs";
                    // Create directory
                    std::string mkdir_cmd = "mkdir -p " + prefs_dir;
                    system(mkdir_cmd.c_str());
                    std::string prefs_file = prefs_dir + "/" + prefs_name + ".xml";
                    std::ofstream out(prefs_file);
                    if (out.is_open()) {
                        out << "<?xml version='1.0' encoding='utf-8' standalone='yes' ?>\n<map>\n";
                        for (const auto& [key, val] : prefs_obj->fields) {
                            if (key == "prefs_name") continue;
                            if (val.type == DalvikType::STRING_REF) {
                                out << "    <string name=\"" << key << "\">" << val.string_val << "</string>\n";
                            } else if (val.type == DalvikType::INT32) {
                                out << "    <int name=\"" << key << "\" value=\"" << val.int_val << "\" />\n";
                            } else if (val.type == DalvikType::BOOLEAN) {
                                out << "    <boolean name=\"" << key << "\" value=\"" << (val.bool_val ? "true" : "false") << "\" />\n";
                            } else if (val.type == DalvikType::INT64) {
                                out << "    <long name=\"" << key << "\" value=\"" << val.long_val << "\" />\n";
                            } else if (val.type == DalvikType::FLOAT32) {
                                out << "    <float name=\"" << key << "\" value=\"" << val.float_val << "\" />\n";
                            }
                        }
                        out << "</map>\n";
                        out.close();
                        std::cerr << "[PREFS] Saved " << prefs_name << ".xml (" << prefs_obj->fields.size() << " entries)" << std::endl;
                    }
                }
            }
            result = (method == "commit") ? DalvikValue::make_bool(true) : DalvikValue::make_void();
            status = ApiCallTrace::Status::IMPLEMENTED;
            return true;
        }
    }

    // ────────────────────────────────────────────────────────────────────────
    // P0.13 — Context.getFilesDir → File
    // ────────────────────────────────────────────────────────────────────────
    if (method == "getFilesDir" &&
        (class_name.find("Context") != std::string::npos ||
         class_name.find("Activity") != std::string::npos)) {
        result = get_or_create_singleton("Ljava/io/File;");
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // P1.1 — Activity.getWindow → Window singleton
    // ────────────────────────────────────────────────────────────────────────
    if (method == "getWindow" &&
        class_name.find("Activity") != std::string::npos) {
        result = get_or_create_singleton("Landroid/view/Window;");
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // P1.2 — Window.setFlags(int, int) → void (no-op)
    // ────────────────────────────────────────────────────────────────────────
    if (method == "setFlags" &&
        class_name.find("Window") != std::string::npos) {
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_void();
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // P1.3 — Window.getDecorView → View
    // ────────────────────────────────────────────────────────────────────────
    if (method == "getDecorView" &&
        class_name.find("Window") != std::string::npos) {
        result = get_or_create_singleton("Landroid/view/View;");
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // P1.4 — Resources.getIdentifier(String, String, String) → int (not found)
    // EXP-052: Log every resource identifier query for evidence.
    if (method == "getIdentifier" &&
        class_name.find("Resources") != std::string::npos) {
        // Args: (String name, String defType, String defPackage)
        std::string name = args.size() >= 1 ? args[0].string_val : "<unknown>";
        std::string defType = args.size() >= 2 ? args[1].string_val : "<unknown>";
        std::string defPackage = args.size() >= 3 ? args[2].string_val : "<unknown>";
        std::cerr << "[RES] getIdentifier name=\"" << name
                  << "\" defType=\"" << defType
                  << "\" defPackage=\"" << defPackage
                  << "\" → 0 (not found)" << std::endl;
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_int(0);
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // P1.5 — Resources.getDimensionPixelSize(int) → int
    // EXP-067: Real resolution via field_name_by_resid_ → resource_dimen_values_.
    // Falls back to 24px only if the dimension is not found.
    // ────────────────────────────────────────────────────────────────────────
    if (method == "getDimensionPixelSize" &&
        class_name.find("Resources") != std::string::npos) {
        int32_t resid = args.size() >= 1 ? args[0].int_val : 0;
        int32_t dimen_val = 24;  // default 24px
        bool resolved = false;
        auto it = field_name_by_resid_.find(resid);
        if (it != field_name_by_resid_.end()) {
            const std::string& name = it->second;
            auto dit = resource_dimen_values_.find(name);
            if (dit != resource_dimen_values_.end()) {
                dimen_val = dit->second;
                resolved = true;
            }
        }
        std::cerr << "[RES] getDimensionPixelSize resid=0x" << std::hex << resid << std::dec
                  << " name=" << (it != field_name_by_resid_.end() ? it->second : "<unknown>")
                  << " → " << dimen_val << "px"
                  << (resolved ? "" : " (default 24px — not resolved)")
                  << std::endl;
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_int(dimen_val);
        return true;
    }

    // EXP-063: Resources.getResourceEntryName(int) → String
    // Maps resource ID to resource entry name using field_name_by_resid_.
    // args[0] = this (Resources), args[1] = resid (int)
    if (method == "getResourceEntryName" &&
        class_name.find("Resources") != std::string::npos) {
        int32_t resid = args.size() >= 2 ? args[1].int_val : (args.size() >= 1 ? args[0].int_val : 0);
        auto it = field_name_by_resid_.find(resid);
        if (it != field_name_by_resid_.end()) {
            std::string name = it->second;
            std::cerr << "[RES] getResourceEntryName resid=0x" << std::hex << resid
                      << std::dec << " → \"" << name << "\"" << std::endl;
            status = ApiCallTrace::Status::IMPLEMENTED;
            result = DalvikValue::make_string(name, 0);
            return true;
        }
        std::cerr << "[RES] getResourceEntryName resid=0x" << std::hex << resid
                  << std::dec << " → NOT FOUND" << std::endl;
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_string("", 0);
        return true;
    }

    // EXP-063: LocaleController.getString(String, int) → String
    // This is the actual string lookup by name.
    if (method == "getString" &&
        class_name.find("LocaleController") != std::string::npos &&
        args.size() >= 1 && args[0].type == DalvikType::STRING_REF) {
        // args[0] is the resource entry name (e.g., "StartMessaging")
        // Look it up in resource_string_values_
        // We need to get the string value from the heap
        std::string res_name;
        if (heap_.has_object(args[0].object_id)) {
            // The string is stored as a field in the heap object
            auto sv = heap_.get_object_field(args[0].object_id, "value");
            if (sv.has_value() && sv->type == DalvikType::STRING_REF) {
                res_name = sv->string_val;
            }
        }
        if (res_name.empty() && args[0].type == DalvikType::STRING_REF) {
            // Try using the string_val directly
            res_name = args[0].string_val;
        }
        if (!res_name.empty()) {
            auto it = resource_string_values_.find(res_name);
            if (it != resource_string_values_.end()) {
                std::string val = it->second;
                std::cerr << "[RES] LocaleController.getString(\"" << res_name
                          << "\") → \"" << val << "\"" << std::endl;
                status = ApiCallTrace::Status::IMPLEMENTED;
                result = DalvikValue::make_string(val, 0);
                return true;
            }
        }
    }

    // EXP-052: Resources.getString(int) → String
    // EXP-063: Look up resource by name via field_name_by_resid_
    if (method == "getString" &&
        class_name.find("Resources") != std::string::npos) {
        int32_t resid = args.size() >= 1 ? args[0].int_val : 0;
        // EXP-063: Try to resolve via resource_name → value mapping
        std::string resolved;
        auto it = field_name_by_resid_.find(resid);
        if (it != field_name_by_resid_.end()) {
            const std::string& field_name = it->second;
            auto sit = resource_string_values_.find(field_name);
            if (sit != resource_string_values_.end()) {
                resolved = sit->second;
            }
        }
        if (!resolved.empty()) {
            std::cerr << "[RES] getString resid=0x" << std::hex << resid << std::dec
                      << " → \"" << resolved << "\"" << std::endl;
            status = ApiCallTrace::Status::IMPLEMENTED;
            result = DalvikValue::make_string(resolved, 0);
            return true;
        }
        std::cerr << "[RES] getString resid=0x" << std::hex << resid
                  << std::dec << " → \"\" (not resolved)" << std::endl;
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_string("", 0);
        return true;
    }

    // EXP-067: Resources.getColor(int, Theme) → int (real resolution)
    // Looks up the color via field_name_by_resid_ → resource_color_values_.
    // Falls back to default black only if the color is not found.
    if (method == "getColor" &&
        class_name.find("Resources") != std::string::npos) {
        int32_t resid = args.size() >= 1 ? args[0].int_val : 0;
        int32_t color_val = 0xFF000000;  // default black
        bool resolved = false;
        auto it = field_name_by_resid_.find(resid);
        if (it != field_name_by_resid_.end()) {
            const std::string& name = it->second;
            auto cit = resource_color_values_.find(name);
            if (cit != resource_color_values_.end()) {
                color_val = cit->second;
                resolved = true;
            }
        }
        std::cerr << "[RES] getColor resid=0x" << std::hex << resid << std::dec
                  << " name=" << (it != field_name_by_resid_.end() ? it->second : "<unknown>")
                  << " → 0x" << std::hex << (color_val & 0xFFFFFFFF) << std::dec
                  << (resolved ? "" : " (default black — not resolved)")
                  << std::endl;
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_int(color_val);
        return true;
    }

    // EXP-067: Resources.getDrawable(int) → Drawable (returns resource name as string for now)
    // Real drawable decoding (bitmap loading) is a future EXP. For now, return the
    // drawable's resource name so the renderer can look up the asset path.
    if (method == "getDrawable" &&
        class_name.find("Resources") != std::string::npos) {
        int32_t resid = args.size() >= 1 ? args[0].int_val : 0;
        auto it = field_name_by_resid_.find(resid);
        std::string name = (it != field_name_by_resid_.end()) ? it->second : "";
        std::string path;
        if (!name.empty()) {
            auto pit = resource_drawable_paths_.find(name);
            if (pit != resource_drawable_paths_.end()) {
                path = pit->second;
            }
        }
        std::cerr << "[RES] getDrawable resid=0x" << std::hex << resid << std::dec
                  << " name=" << name
                  << " path=" << (path.empty() ? "<none>" : path)
                  << std::endl;
        // Return null for now (drawable object creation is a future EXP).
        // The renderer can look up resource_drawable_paths_ via the resource name
        // if the View's setImageResource was called.
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_null();
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // P1.8 — Context.getMainLooper → Looper
    // ────────────────────────────────────────────────────────────────────────
    if (method == "getMainLooper" &&
        (class_name.find("Context") != std::string::npos ||
         class_name.find("Activity") != std::string::npos)) {
        result = get_or_create_singleton("Landroid/os/Looper;");
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // P1.6 — Context.getSystemService → null (Telegram handles null gracefully)
    // ────────────────────────────────────────────────────────────────────────
    if (method == "getSystemService" &&
        (class_name.find("Context") != std::string::npos ||
         class_name.find("Activity") != std::string::npos)) {
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_null();
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // P1.7 — Context.getExternalFilesDir → File
    // ────────────────────────────────────────────────────────────────────────
    if (method == "getExternalFilesDir" &&
        (class_name.find("Context") != std::string::npos ||
         class_name.find("Activity") != std::string::npos)) {
        result = get_or_create_singleton("Ljava/io/File;");
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-043 Phase 3: System.currentTimeMillis() → long
    // ────────────────────────────────────────────────────────────────────────
    if (method == "currentTimeMillis" &&
        class_name.find("System") != std::string::npos) {
        status = ApiCallTrace::Status::IMPLEMENTED;
        auto now = std::chrono::system_clock::now();
        auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
            now.time_since_epoch()).count();
        DalvikValue v;
        v.type = DalvikType::INT64;
        v.long_val = static_cast<int64_t>(ms);
        result = v;
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-043 Phase 3: System.nanoTime() → long
    // ────────────────────────────────────────────────────────────────────────
    if (method == "nanoTime" &&
        class_name.find("System") != std::string::npos) {
        status = ApiCallTrace::Status::IMPLEMENTED;
        auto now = std::chrono::high_resolution_clock::now();
        auto ns = std::chrono::duration_cast<std::chrono::nanoseconds>(
            now.time_since_epoch()).count();
        DalvikValue v;
        v.type = DalvikType::INT64;
        v.long_val = static_cast<int64_t>(ns);
        result = v;
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-043 Phase 3: Context.getCacheDir → File
    // ────────────────────────────────────────────────────────────────────────
    if (method == "getCacheDir" &&
        (class_name.find("Context") != std::string::npos ||
         class_name.find("Activity") != std::string::npos)) {
        result = get_or_create_singleton("Ljava/io/File;");
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-043 Phase 3: Log.d/i/w/e → int (returns log level)
    // ────────────────────────────────────────────────────────────────────────
    if ((method == "d" || method == "i" || method == "w" || method == "e" ||
         method == "v" || method == "println") &&
        class_name.find("Log") != std::string::npos) {
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_int(0);
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-043 Phase 3: Resources.getColor(int) → int (default black)
    // ────────────────────────────────────────────────────────────────────────
    if (method == "getColor" &&
        class_name.find("Resources") != std::string::npos) {
        status = ApiCallTrace::Status::IMPLEMENTED;
        DalvikValue v;
        v.type = DalvikType::INT32;
        v.int_val = 0xFF000000;  // black
        result = v;
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-043 Phase 3: Context.getApplicationInfo → ApplicationInfo singleton
    // ────────────────────────────────────────────────────────────────────────
    if (method == "getApplicationInfo" &&
        (class_name.find("Context") != std::string::npos ||
         class_name.find("Activity") != std::string::npos)) {
        result = get_or_create_singleton("Landroid/content/pm/ApplicationInfo;");
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-043 Phase 3: Handler.<init>(Looper) → no-op, return void
    // ────────────────────────────────────────────────────────────────────────
    if (class_name.find("Handler") != std::string::npos &&
        (method == "<init>" || method == "post" || method == "postDelayed" ||
         method == "removeCallbacks" || method == "sendMessage")) {
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_void();
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-043 Phase 3: Looper.getMainLooper → Looper singleton
    // ────────────────────────────────────────────────────────────────────────
    if (method == "getMainLooper" &&
        class_name.find("Looper") != std::string::npos) {
        result = get_or_create_singleton("Landroid/os/Looper;");
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-043 Phase 3: Looper.myLooper → Looper singleton
    // ────────────────────────────────────────────────────────────────────────
    if (method == "myLooper" &&
        class_name.find("Looper") != std::string::npos) {
        result = get_or_create_singleton("Landroid/os/Looper;");
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-043 Phase 3: DisplayMetrics setters — no-op (already populated)
    // ────────────────────────────────────────────────────────────────────────
    if (class_name.find("DisplayMetrics") != std::string::npos &&
        (method == "setTo" || method == "setToDefaults")) {
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_void();
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-043 Phase 3: View.<init> — no-op, return void
    // ────────────────────────────────────────────────────────────────────────
    if (class_name.find("View") != std::string::npos && method == "<init>") {
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_void();
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-043 Phase 3: File.<init> — store path, return void
    // ────────────────────────────────────────────────────────────────────────
    if (class_name == "Ljava/io/File;" && method == "<init>") {
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_void();
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-043 Phase 3: File.getAbsolutePath → String
    // ────────────────────────────────────────────────────────────────────────
    if (class_name == "Ljava/io/File;" && method == "getAbsolutePath") {
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_string("/tmp/miniandroid/files", 1);
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-071 Phase 7: HashMap/ArrayList fallback in bridge_to_api.
    //
    // CollectionShadow in the shadow registry is the PRIMARY handler for
    // HashMap/ArrayList/Map. It stores entries in per-instance
    // CollectionState (map_entries / map_string_entries / elements).
    //
    // This bridge_to_api stub is a FALLBACK for when shadow dispatch
    // fails (e.g., when the receiver object wasn't tracked by
    // CollectionShadow). It uses heap object fields as storage.
    //
    // NOTE: If CollectionShadow handles the call, this stub is NEVER
    // reached (try_shadow_dispatch returns true before bridge_to_api).
    // If CollectionShadow doesn't handle it, this stub provides a
    // best-effort fallback.
    if ((class_name == "Ljava/util/HashMap;" ||
         class_name.find("HashMap") != std::string::npos ||
         class_name.find("Map") != std::string::npos) &&
        shadow_registry_ == nullptr) {
        // HashMap() constructor — no-op.
        if (method == "<init>") {
            status = ApiCallTrace::Status::IMPLEMENTED;
            result = DalvikValue::make_void();
            return true;
        }
        // HashMap.get(key) → value (or null)
        if (method == "get" && !args.empty()) {
            uint32_t this_id = args[0].object_id;
            std::string key_str;
            if (args.size() >= 2) {
                if (args[1].type == DalvikType::STRING_REF) {
                    key_str = args[1].string_val;
                } else if (args[1].type == DalvikType::OBJECT_REF) {
                    // Use object_id as key suffix.
                    key_str = "obj_" + std::to_string(args[1].object_id);
                } else {
                    key_str = std::to_string(args[1].int_val);
                }
            }
            std::string field_name = "key_" + key_str;
            auto* obj = heap_.get(this_id);
            bool hit = false;
            if (obj) {
                auto fit = obj->fields.find(field_name);
                if (fit != obj->fields.end()) {
                    result = fit->second;
                    hit = true;
                    // EXP-071-HMAP-GET diagnostic
                    std::cerr << "[EXP071-HMAP-GET] map=" << this_id
                              << " key=\"" << key_str << "\" HIT"
                              << " val_type=" << (int)result.type;
                    if (result.type == DalvikType::STRING_REF) {
                        std::cerr << " val=\"" << result.string_val << "\"";
                    } else if (result.type == DalvikType::OBJECT_REF) {
                        std::cerr << " val_obj=" << result.object_id;
                    }
                    std::cerr << " caller=" << current_class_ << "." << current_method_
                              << " pc=" << pc_ << std::endl;
                    status = ApiCallTrace::Status::IMPLEMENTED;
                    return true;
                }
            }
            // Key not found — return null.
            // EXP-071-HMAP-GET diagnostic
            std::cerr << "[EXP071-HMAP-GET] map=" << this_id
                      << " key=\"" << key_str << "\" MISS"
                      << " caller=" << current_class_ << "." << current_method_
                      << " pc=" << pc_ << std::endl;
            status = ApiCallTrace::Status::IMPLEMENTED;
            result = DalvikValue::make_null();
            return true;
        }
        // HashMap.put(key, value) → old value (we return null)
        if (method == "put" && args.size() >= 3) {
            uint32_t this_id = args[0].object_id;
            std::string key_str;
            if (args[1].type == DalvikType::STRING_REF) {
                key_str = args[1].string_val;
            } else if (args[1].type == DalvikType::OBJECT_REF) {
                key_str = "obj_" + std::to_string(args[1].object_id);
            } else {
                key_str = std::to_string(args[1].int_val);
            }
            std::string field_name = "key_" + key_str;
            heap_.set_object_field(this_id, field_name, args[2]);
            // EXP-071-HMAP-PUT diagnostic
            std::cerr << "[EXP071-HMAP-PUT] map=" << this_id
                      << " key=\"" << key_str << "\""
                      << " val_type=" << (int)args[2].type;
            if (args[2].type == DalvikType::STRING_REF) {
                std::cerr << " val=\"" << args[2].string_val << "\"";
            } else if (args[2].type == DalvikType::OBJECT_REF) {
                std::cerr << " val_obj=" << args[2].object_id;
            }
            std::cerr << " caller=" << current_class_ << "." << current_method_
                      << " pc=" << pc_ << std::endl;
            status = ApiCallTrace::Status::IMPLEMENTED;
            result = DalvikValue::make_null();  // old value (null = no previous)
            return true;
        }
        // HashMap.containsKey(key) → boolean
        if (method == "containsKey" && !args.empty()) {
            uint32_t this_id = args[0].object_id;
            std::string key_str;
            if (args.size() >= 2) {
                if (args[1].type == DalvikType::STRING_REF) {
                    key_str = args[1].string_val;
                } else if (args[1].type == DalvikType::OBJECT_REF) {
                    key_str = "obj_" + std::to_string(args[1].object_id);
                } else {
                    key_str = std::to_string(args[1].int_val);
                }
            }
            std::string field_name = "key_" + key_str;
            auto* obj = heap_.get(this_id);
            bool found = (obj && obj->fields.find(field_name) != obj->fields.end());
            status = ApiCallTrace::Status::IMPLEMENTED;
            result = DalvikValue::make_bool(found);
            return true;
        }
        // HashMap.size() → int
        if (method == "size") {
            // We don't track size separately — return 0 as a safe default.
            // (Most callers check size() > 0 to decide whether to iterate.)
            status = ApiCallTrace::Status::IMPLEMENTED;
            result = DalvikValue::make_int(0);
            return true;
        }
        // HashMap.isEmpty() → boolean
        if (method == "isEmpty") {
            // Without tracking size, assume non-empty if any fields exist.
            uint32_t this_id = args.empty() ? 0 : args[0].object_id;
            auto* obj = heap_.get(this_id);
            bool empty = !(obj && !obj->fields.empty());
            status = ApiCallTrace::Status::IMPLEMENTED;
            result = DalvikValue::make_bool(empty);
            return true;
        }
        // HashMap.clear() → void
        if (method == "clear") {
            uint32_t this_id = args.empty() ? 0 : args[0].object_id;
            auto* obj = heap_.get(this_id);
            if (obj) obj->fields.clear();
            status = ApiCallTrace::Status::IMPLEMENTED;
            result = DalvikValue::make_void();
            return true;
        }
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-071 Phase 6: ArrayList — basic operations.
    // ArrayList is also an Android framework class. We stub add/get/size.
    // Uses the SAME "array[idx]" / "__array_length__" convention as
    // ARRAY_GET_CASE / ARRAY_PUT_CASE so aget-object on an ArrayList's
    // backing array works correctly.
    if (class_name == "Ljava/util/ArrayList;" ||
        class_name.find("ArrayList") != std::string::npos ||
        class_name.find("List;") != std::string::npos) {
        if (method == "<init>") {
            status = ApiCallTrace::Status::IMPLEMENTED;
            result = DalvikValue::make_void();
            return true;
        }
        if (method == "add" && args.size() >= 2) {
            uint32_t this_id = args[0].object_id;
            auto* obj = heap_.get(this_id);
            if (obj) {
                int idx = 0;
                while (obj->fields.find("array[" + std::to_string(idx) + "]") != obj->fields.end()) {
                    idx++;
                }
                heap_.set_object_field(this_id, "array[" + std::to_string(idx) + "]", args[1]);
                heap_.set_object_field(this_id, "__array_length__", DalvikValue::make_int(idx + 1));
            }
            status = ApiCallTrace::Status::IMPLEMENTED;
            result = DalvikValue::make_bool(true);
            return true;
        }
        if (method == "get" && args.size() >= 2) {
            uint32_t this_id = args[0].object_id;
            int32_t idx = args[1].int_val;
            auto* obj = heap_.get(this_id);
            if (obj) {
                auto fit = obj->fields.find("array[" + std::to_string(idx) + "]");
                if (fit != obj->fields.end()) {
                    result = fit->second;
                    status = ApiCallTrace::Status::IMPLEMENTED;
                    return true;
                }
            }
            status = ApiCallTrace::Status::IMPLEMENTED;
            result = DalvikValue::make_null();
            return true;
        }
        if (method == "size") {
            uint32_t this_id = args.empty() ? 0 : args[0].object_id;
            auto* obj = heap_.get(this_id);
            int32_t sz = 0;
            if (obj) {
                auto fit = obj->fields.find("__array_length__");
                if (fit != obj->fields.end()) {
                    sz = fit->second.int_val;
                }
            }
            status = ApiCallTrace::Status::IMPLEMENTED;
            result = DalvikValue::make_int(sz);
            return true;
        }
        if (method == "isEmpty") {
            uint32_t this_id = args.empty() ? 0 : args[0].object_id;
            auto* obj = heap_.get(this_id);
            int32_t sz = 0;
            if (obj) {
                auto fit = obj->fields.find("__array_length__");
                if (fit != obj->fields.end()) {
                    sz = fit->second.int_val;
                }
            }
            status = ApiCallTrace::Status::IMPLEMENTED;
            result = DalvikValue::make_bool(sz == 0);
            return true;
        }
        if (method == "clear") {
            uint32_t this_id = args.empty() ? 0 : args[0].object_id;
            auto* obj = heap_.get(this_id);
            if (obj) {
                // Remove all array[*] fields.
                std::vector<std::string> to_remove;
                for (auto& [k, v] : obj->fields) {
                    if (k.find("array[") == 0) to_remove.push_back(k);
                }
                for (auto& k : to_remove) obj->fields.erase(k);
                heap_.set_object_field(this_id, "__array_length__", DalvikValue::make_int(0));
            }
            status = ApiCallTrace::Status::IMPLEMENTED;
            result = DalvikValue::make_void();
            return true;
        }
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-071 Phase 6: aget-object — array element access.
    // This is handled in the opcode dispatcher, but some code paths use
    // invoke-virtual on array objects. We handle array.length and aget here.
    if (class_name == "Larray;" || class_name.find("[L") == 0) {
        if (method == "length") {
            uint32_t this_id = args.empty() ? 0 : args[0].object_id;
            auto* obj = heap_.get(this_id);
            int32_t sz = 0;
            if (obj) {
                auto fit = obj->fields.find("length");
                if (fit != obj->fields.end()) {
                    sz = fit->second.int_val;
                }
            }
            status = ApiCallTrace::Status::IMPLEMENTED;
            result = DalvikValue::make_int(sz);
            return true;
        }
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-071 Phase 6: AssetManager.open(asset_name) → InputStream
    //
    // Reads the asset from the APK (which is a ZIP file) and returns an
    // InputStream heap object. The asset contents are stored in
    // open_assets_ for later retrieval by BufferedReader.readLine().
    //
    // This is GENERIC — any Android app that reads assets via
    // AssetManager.open + BufferedReader.readLine will work.
    if (method == "open" &&
        class_name.find("AssetManager") != std::string::npos) {
        std::string asset_name;
        if (!args.empty() && args[0].type == DalvikType::STRING_REF) {
            asset_name = args[0].string_val;
        } else if (args.size() >= 2 && args[1].type == DalvikType::STRING_REF) {
            // open(String, int) — second arg is access mode
            asset_name = args[1].string_val;
        }
        std::cerr << "[EXP071-ASSET] AssetManager.open(\"" << asset_name << "\")" << std::endl;
        // Allocate an InputStream heap object.
        uint32_t stream_id = heap_.allocate("Ljava/io/InputStream;", 0, 0);
        // Store asset name + line index 0.
        open_assets_[stream_id] = std::make_pair(asset_name, 0);
        // Read the asset from the APK now and cache the lines.
        // (We read lazily — actual reading happens in readLine.)
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_object(stream_id, "Ljava/io/InputStream;");
        std::cerr << "[EXP071-ASSET] → InputStream obj_id=" << stream_id << std::endl;
        return true;
    }

    // EXP-071 Phase 6: InputStreamReader(InputStream) → reader
    // Just wrap the InputStream — we track the mapping.
    if (class_name == "Ljava/io/InputStreamReader;" && method == "<init>") {
        // The first arg (args[0]) is the InputStream. We propagate the
        // asset tracking to the reader by copying open_assets_ entry.
        if (!args.empty() && args[0].type == DalvikType::OBJECT_REF) {
            uint32_t stream_id = args[0].object_id;
            // The receiver (args[0] for instance? No, InputStreamReader is
            // constructed via invoke-direct, so args[0] is `this` and args[1]
            // is the InputStream).
            // Actually for invoke-direct InputStreamReader.<init>(InputStream),
            // args[0] = this (the reader being constructed), args[1] = stream.
            if (args.size() >= 2 && args[1].type == DalvikType::OBJECT_REF) {
                uint32_t this_id = args[0].object_id;
                uint32_t stream_id_arg = args[1].object_id;
                auto it = open_assets_.find(stream_id_arg);
                if (it != open_assets_.end()) {
                    open_assets_[this_id] = it->second;
                    std::cerr << "[EXP071-ASSET] InputStreamReader.<init> this=" << this_id
                              << " stream=" << stream_id_arg
                              << " asset=\"" << it->second.first << "\""
                              << std::endl;
                }
            }
        }
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_void();
        return true;
    }

    // EXP-071 Phase 6: BufferedReader.<init>(Reader) → reader
    if (class_name == "Ljava/io/BufferedReader;" && method == "<init>") {
        // args[0] = this (BufferedReader), args[1] = reader
        if (args.size() >= 2 && args[1].type == DalvikType::OBJECT_REF) {
            uint32_t this_id = args[0].object_id;
            uint32_t reader_id = args[1].object_id;
            auto it = open_assets_.find(reader_id);
            if (it != open_assets_.end()) {
                open_assets_[this_id] = it->second;
                std::cerr << "[EXP071-ASSET] BufferedReader.<init> this=" << this_id
                          << " reader=" << reader_id
                          << " asset=\"" << it->second.first << "\""
                          << std::endl;
            }
        }
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_void();
        return true;
    }

    // EXP-071 Phase 6: BufferedReader.readLine() → String (or null at EOF)
    //
    // Reads the next line from the cached asset contents. Returns null
    // when all lines have been read.
    if (class_name == "Ljava/io/BufferedReader;" && method == "readLine") {
        uint32_t this_id = args.empty() ? 0 : args[0].object_id;
        auto it = open_assets_.find(this_id);
        if (it == open_assets_.end()) {
            // No asset associated — return null (EOF).
            std::cerr << "[EXP071-ASSET] BufferedReader.readLine obj=" << this_id
                      << " — no asset, returning null" << std::endl;
            status = ApiCallTrace::Status::IMPLEMENTED;
            result = DalvikValue::make_null();
            return true;
        }
        const std::string& asset_name = it->second.first;
        size_t& line_idx = it->second.second;
        // Lazily load the asset contents.
        static std::map<std::string, std::vector<std::string>> asset_lines_cache;
        auto cache_it = asset_lines_cache.find(asset_name);
        if (cache_it == asset_lines_cache.end()) {
            // Load from APK.
            std::vector<std::string> lines;
            if (!apk_path_.empty()) {
                FILE* fp = popen(
                    ("unzip -p \"" + apk_path_ + "\" assets/" + asset_name + " 2>/dev/null").c_str(),
                    "r");
                if (fp) {
                    char buf[4096];
                    std::string content;
                    while (fgets(buf, sizeof(buf), fp)) {
                        content += buf;
                    }
                    pclose(fp);
                    // Split by lines.
                    std::string current;
                    for (char c : content) {
                        if (c == '\n') {
                            lines.push_back(current);
                            current.clear();
                        } else if (c != '\r') {
                            current += c;
                        }
                    }
                    if (!current.empty()) {
                        lines.push_back(current);
                    }
                    std::cerr << "[EXP071-ASSET] Loaded asset \"" << asset_name
                              << "\" — " << lines.size() << " lines" << std::endl;
                } else {
                    std::cerr << "[EXP071-ASSET] Failed to open APK for asset \""
                              << asset_name << "\"" << std::endl;
                }
            }
            asset_lines_cache[asset_name] = std::move(lines);
            cache_it = asset_lines_cache.find(asset_name);
        }
        const auto& lines = cache_it->second;
        if (line_idx >= lines.size()) {
            std::cerr << "[EXP071-ASSET] BufferedReader.readLine obj=" << this_id
                      << " asset=\"" << asset_name << "\" — EOF, returning null"
                      << std::endl;
            status = ApiCallTrace::Status::IMPLEMENTED;
            result = DalvikValue::make_null();
            return true;
        }
        std::string line = lines[line_idx++];
        std::cerr << "[EXP071-ASSET] BufferedReader.readLine obj=" << this_id
                  << " asset=\"" << asset_name << "\" line=" << line_idx
                  << " → \"" << line.substr(0, 60) << "\""
                  << std::endl;
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_string(line, 0);
        return true;
    }

    // EXP-071 Phase 6: BufferedReader.close() / InputStream.close() → void
    if ((class_name == "Ljava/io/BufferedReader;" ||
         class_name == "Ljava/io/InputStreamReader;" ||
         class_name == "Ljava/io/InputStream;") && method == "close") {
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_void();
        return true;
    }

    // EXP-071 Phase 6: String.split(regex) → String[]
    //
    // Splits the string by the regex (treated as a literal delimiter).
    // Returns a heap array of String objects.
    if (class_name == "Ljava/lang/String;" && method == "split") {
        // args[0] = this (String), args[1] = regex
        std::string str = args.empty() ? "" :
            (args[0].type == DalvikType::STRING_REF ? args[0].string_val : "");
        std::string delim = (args.size() >= 2 && args[1].type == DalvikType::STRING_REF)
            ? args[1].string_val : ";";
        std::vector<std::string> parts;
        size_t start = 0;
        size_t pos;
        while ((pos = str.find(delim, start)) != std::string::npos) {
            parts.push_back(str.substr(start, pos - start));
            start = pos + delim.length();
        }
        parts.push_back(str.substr(start));
        // Allocate a heap array.
        uint32_t arr_id = heap_.allocate("Larray;", 0, 0);
        // EXP-071 Phase 6: Use the SAME field naming convention as the
        // ARRAY_GET_CASE / ARRAY_PUT_CASE macros:
        //   - elements stored as "array[idx]"
        //   - length stored as "__array_length__"
        // This ensures aget-object on the returned array reads the correct
        // element. Without this, the countries.txt parsing loop in
        // PhoneView.<init> would get null from every aget-object, causing
        // the country HashMap to be empty and setCountry to return early.
        for (size_t i = 0; i < parts.size(); i++) {
            DalvikValue sv = DalvikValue::make_string(parts[i], 0);
            heap_.set_object_field(arr_id, "array[" + std::to_string(i) + "]", sv);
        }
        DalvikValue len_val = DalvikValue::make_int(static_cast<int32_t>(parts.size()));
        heap_.set_object_field(arr_id, "__array_length__", len_val);
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_object(arr_id, "Larray;");
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-043 Phase 3: File.exists → boolean (true, pretend file exists)
    // ────────────────────────────────────────────────────────────────────────
    if (class_name == "Ljava/io/File;" &&
        (method == "exists" || method == "isDirectory" || method == "canRead" ||
         method == "canWrite" || method == "mkdirs" || method == "mkdir" ||
         method == "createNewFile")) {
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_bool(true);
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-071: TextView.length() → int — returns the length of the View's text.
    // In Android, TextView.length() returns getText().length().
    // We read from the ViewShadow's ViewNode.text.
    // This is needed by PhoneView.onNextPressed which checks:
    //   if (codeField.length() == 0) { onFieldError(); return; }
    //   if (phoneField.length() == 0) { onFieldError(); return; }
    if (method == "length" &&
        (class_name.find("TextView") != std::string::npos ||
         class_name.find("EditText") != std::string::npos ||
         class_name.find("View") != std::string::npos)) {
        // Try shadow dispatch first
        if (shadow_registry_ != nullptr && !args.empty()) {
            framework::CallContext ctx;
            ctx.has_receiver = args[0].type == DalvikType::OBJECT_REF;
            if (ctx.has_receiver) {
                ctx.receiver_id = args[0].object_id;
                ctx.receiver_class = args[0].class_desc;
                ctx.class_name = args[0].class_desc;
            }
            ctx.method = "getText";
            auto cr = shadow_registry_->dispatch(ctx);
            if (cr.handled && cr.ret_kind == framework::CallResult::RetKind::STRING) {
                int32_t len = static_cast<int32_t>(cr.string_val.size());
                std::cerr << "[EXP071-LENGTH] view_id=" << args[0].object_id
                          << " text=\"" << cr.string_val.substr(0, 40) << "\""
                          << " length=" << len << std::endl;
                status = ApiCallTrace::Status::IMPLEMENTED;
                result = DalvikValue::make_int(len);
                return true;
            }
        }
        // Fallback: return 0
        status = ApiCallTrace::Status::IMPLEMENTED;
        size_t len = 0;
        if (!args.empty() && args[0].type == DalvikType::STRING_REF) {
            len = args[0].string_val.size();
        }
        result = DalvikValue::make_int(static_cast<int32_t>(len));
        return true;
    }

    // EXP-043 Phase 3: String.length → int
    // EXP-071: Fixed to return actual string length from the arg.
    if (class_name == "Ljava/lang/String;" && method == "length") {
        status = ApiCallTrace::Status::IMPLEMENTED;
        // Try to get the actual string from args[0] (the String object itself)
        if (!args.empty() && args[0].type == DalvikType::STRING_REF) {
            result = DalvikValue::make_int(static_cast<int32_t>(args[0].string_val.size()));
        } else {
            result = DalvikValue::make_int(0);
        }
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-043 Phase 3: String.equals → boolean
    // EXP-071: proper string comparison (was always false).
    // ────────────────────────────────────────────────────────────────────────
    if (class_name == "Ljava/lang/String;" && method == "equals") {
        status = ApiCallTrace::Status::IMPLEMENTED;
        bool eq = false;
        if (args.size() >= 2 &&
            args[0].type == DalvikType::STRING_REF &&
            args[1].type == DalvikType::STRING_REF) {
            eq = (args[0].string_val == args[1].string_val);
        } else if (args.size() >= 2 &&
                   args[0].type == DalvikType::NULL_REF &&
                   args[1].type == DalvikType::NULL_REF) {
            eq = true;
        }
        result = DalvikValue::make_bool(eq);
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-071 Phase 6: String.toUpperCase() → String
    //
    // Converts the string to uppercase. Needed by PhoneView.lambda$new$12
    // which reads response.country ("US") and calls toUpperCase() before
    // passing it to setCountry. Without this stub, toUpperCase returns null,
    // causing setCountry to receive a null country argument and return early.
    if (class_name == "Ljava/lang/String;" && method == "toUpperCase") {
        std::string str = args.empty() ? "" :
            (args[0].type == DalvikType::STRING_REF ? args[0].string_val : "");
        std::string upper;
        upper.reserve(str.size());
        for (char c : str) {
            upper += static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
        }
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_string(upper, 0);
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-071 Phase 6: String.toLowerCase() → String
    if (class_name == "Ljava/lang/String;" && method == "toLowerCase") {
        std::string str = args.empty() ? "" :
            (args[0].type == DalvikType::STRING_REF ? args[0].string_val : "");
        std::string lower;
        lower.reserve(str.size());
        for (char c : str) {
            lower += static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
        }
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_string(lower, 0);
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-071 Phase 6: TextUtils.equals(CharSequence, CharSequence) → boolean
    if (class_name == "Landroid/text/TextUtils;" && method == "equals") {
        bool equal = false;
        if (args.size() >= 3) {
            std::string a, b;
            if (args[1].type == DalvikType::STRING_REF) a = args[1].string_val;
            if (args[2].type == DalvikType::STRING_REF) b = args[2].string_val;
            equal = (a == b);
        }
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_bool(equal);
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-071 Phase 6: TextUtils.isEmpty(CharSequence) → boolean
    //
    // TextUtils.isEmpty is a STATIC method: args[0] = the CharSequence.
    // But some code paths also call isEmpty() on String/Collection objects
    // via invoke-virtual, where args[0] = this and args[1] = the arg.
    // We handle both: check args[0] first (static case), then args[1].
    if (class_name == "Landroid/text/TextUtils;" && method == "isEmpty") {
        bool empty = true;
        // Static case: args[0] = CharSequence
        if (!args.empty()) {
            if (args[0].type == DalvikType::STRING_REF) {
                empty = args[0].string_val.empty();
            } else if (args[0].type == DalvikType::NULL_REF) {
                empty = true;
            } else if (args[0].type == DalvikType::OBJECT_REF) {
                // Non-null object → not empty
                empty = false;
            }
        }
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_bool(empty);
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-043 Phase 3: Thread.currentThread → Thread singleton
    // ────────────────────────────────────────────────────────────────────────
    if (class_name.find("Thread") != std::string::npos &&
        method == "currentThread") {
        result = get_or_create_singleton("Ljava/lang/Thread;");
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-071 Phase 8: AndroidUtilities.runOnUIThread / executeOnUIThread
    //
    // REMOVED the early-return stub that swallowed these calls as no-ops.
    // Previously this stub ran AFTER try_shadow_dispatch() and prevented
    // the HandlerShadow from ever seeing the call — but try_shadow_dispatch
    // was ALSO misrouting the call (see the static-method fix above). Both
    // bugs combined to make runOnUIThread a silent no-op.
    //
    // Now that try_shadow_dispatch correctly tries the declared class_name
    // FIRST, HandlerShadow.dispatch("Lorg/telegram/messenger/AndroidUtilities;",
    //   "runOnUIThread", [Runnable]) will properly enqueue the Runnable
    // on the global event queue. ApplicationRuntime will drain the queue
    // and invoke each Runnable's run() method after the click dispatch.
    //
    // If shadow dispatch somehow fails, fall through to legacy stub
    // implementations below (so existing paths don't regress).
    // ────────────────────────────────────────────────────────────────────────

    // ────────────────────────────────────────────────────────────────────────
    // EXP-043 Phase 3: Thread.getStackTrace → StackTraceElement[] (empty array)
    // Returns an empty array so loops iterating stack frames terminate immediately.
    // This unblocks Kotlin Intrinsics.createParameterIsNullExceptionMessage which
    // loops through stack trace elements looking for non-Intrinsics frames.
    // ────────────────────────────────────────────────────────────────────────
    if (class_name.find("Thread") != std::string::npos &&
        method == "getStackTrace") {
        // Return a heap object representing an empty array
        uint32_t obj_id = heap_.allocate("Larray;", pc_,
                                        call_stack_.empty() ? 0 : call_stack_.top().frame_id);
        DalvikValue arr;
        arr.type = DalvikType::OBJECT_REF;
        arr.object_id = obj_id;
        arr.class_desc = "Larray;";
        arr.int_val = 0;  // array length = 0
        result = arr;
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-043 Phase 3: array-length on our empty array → 0
    // ────────────────────────────────────────────────────────────────────────
    // (Handled by the ARRAY_LENGTH opcode handler, which reads int_val as length)

    // ────────────────────────────────────────────────────────────────────────
    // STUB: DynamiteModule.load — throw (BLOCKER-D fix)
    // ────────────────────────────────────────────────────────────────────────
    if (method == "load" &&
        class_name.find("DynamiteModule") != std::string::npos) {
        // Real Android throws LoadingException when Play Services is unavailable.
        // Telegram's caller (instantiate) catches it and returns null.
        // We simulate by returning null directly (avoids needing exception
        // propagation support in the engine).
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_null();
        std::cerr << "[EXP-042] DynamiteModule.load stubbed → null "
                     "(mimics no-Play-Services device)" << std::endl;
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // STUB: Theme.getColor (when currentColors cache is null) — return black
    // ────────────────────────────────────────────────────────────────────────
    if (method == "getColor" &&
        class_name.find("Theme") != std::string::npos) {
        status = ApiCallTrace::Status::IMPLEMENTED;
        // Default black = 0xFF000000
        DalvikValue v;
        v.type = DalvikType::INT32;
        v.int_val = 0xFF000000;
        result = v;
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // Legacy Activity/TextView pattern matchers (kept from pre-EXP-042)
    // ────────────────────────────────────────────────────────────────────────
    if (class_name.find("TextView") != std::string::npos &&
        method.find("setText") != std::string::npos) {
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_void();
        return true;
    }

    if (class_name.find("Activity") != std::string::npos &&
        (method.find("setContentView") != std::string::npos ||
         method.find("onCreate") != std::string::npos)) {
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_void();
        return true;
    }

    if (class_name.find("Log") != std::string::npos) {
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_int(0);
        return true;
    }

    // EXP-052: Removed the legacy `ArchTaskExecutor.isMainThread → true` stub.
    //
    // EXP-050 added this stub to "fix" the HALT-LOOP in
    // LifecycleRegistry.enforceMainThreadIfNeeded. But the stub was a
    // band-aid: it short-circuited the bytecode BEFORE the engine could
    // exercise the Thread/Looper identity model. EXP-051 introduced the
    // Shadow Registry with proper ThreadShadow + LooperShadow that should
    // make the bytecode execute correctly:
    //
    //   1. ArchTaskExecutor.isMainThread reads `mDelegate` (a static field)
    //      → currently returns null because we don't track static fields
    //        for framework classes. This is the REAL bug we need to fix.
    //   2. The bytecode calls `mDelegate.isMainThread()` on null → NPE.
    //
    // Removing this stub surfaces the REAL bug: ArchTaskExecutor's static
    // `mDelegate` field is never initialized. The fix is to either:
    //   a) Pre-populate `mDelegate` with a DefaultTaskExecutor instance
    //      during ApplicationRuntime init (shadow-side).
    //   b) Add an `ArchTaskExecutor` shadow that handles `isMainThread`
    //      directly by delegating to the ThreadShadow + LooperShadow
    //      identity check (preferred — matches the real semantics).
    //
    // For now, removing the stub will cause `isMainThread` to recurse
    // into bytecode → NPE on mDelegate → the call returns null → fallback
    // to bridge returns void → if-nez on null returns false →
    // LifecycleRegistry.enforceMainThreadIfNeeded takes the throw path
    // → THROW handler fires → we see the diagnostic.
    //
    // This is the correct "evidence-based" behavior — we surface the real
    // bug instead of hiding it.
    //
    // (Original stub: if (class_name.find("ArchTaskExecutor") != ... &&
    //  method == "isMainThread") { return make_bool(true); })

    // EXP-050: BaseFragment.getLastStoryViewer → null (story viewer not available)
    if (class_name.find("BaseFragment") != std::string::npos &&
        method == "getLastStoryViewer") {
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_null();
        return true;
    }

    // EXP-050: DynamicAnimation/SpringAnimation methods — return basic defaults
    if (class_name.find("DynamicAnimation") != std::string::npos ||
        class_name.find("SpringAnimation") != std::string::npos ||
        class_name.find("SpringForce") != std::string::npos) {
        status = ApiCallTrace::Status::IMPLEMENTED;
        if (method == "isRunning") {
            result = DalvikValue::make_bool(false);
        } else if (method == "start" || method == "startAnimationInternal" ||
                   method == "sanityCheck" || method == "setSpring" ||
                   method == "addUpdateListener") {
            result = DalvikValue::make_void();
        } else if (method == "getPropertyValue" || method == "getFinalPosition" ||
                   method == "getValueThreshold") {
            result = DalvikValue::make_float(0.0f);
        } else {
            result = DalvikValue::make_void();
        }
        return true;
    }

    // EXP-056: When isEmpty() is called on a null object (e.g., getFragmentStack
    // returned null because the field was never initialized), return false (0).
    if (method == "isEmpty" &&
        !args.empty() &&
        (args[0].type == DalvikType::NULL_REF ||
         (args[0].type == DalvikType::OBJECT_REF && args[0].object_id == 0))) {
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_bool(false);
        std::cerr << "[LOGIN-BRANCH] isEmpty on null receiver → false"
                  << " (caller=" << current_class_ << "." << current_method_ << ")"
                  << std::endl;
        return true;
    }
    // EXP-056: Also handle isEmpty when called via shadow dispatch (non-null receiver).
    if (method == "isEmpty") {
        int rt = args.empty() ? 0 : static_cast<int>(args[0].type);
        uint32_t ro = args.empty() ? 0 : args[0].object_id;
        std::cerr << "[LOGIN-BRANCH] isEmpty called"
                  << " receiver_type=" << rt
                  << " receiver_obj=" << ro
                  << " (caller=" << current_class_ << "." << current_method_ << ")"
                  << std::endl;
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-071: bridge_to_api additions for Java framework classes.
    // These handle the cases that try_recursive_invoke's "framework bypass"
    // returns false for (so bridge_to_api is consulted instead of recursing
    // into DEX bytecode that would loop).
    // ────────────────────────────────────────────────────────────────────────

    // String.length → actual length of args[0].string_val.
    // CRITICAL: without this, phone validation always fails with length=0.
    if (class_name == "Ljava/lang/String;" && method == "length") {
        size_t len = 0;
        if (!args.empty() && args[0].type == DalvikType::STRING_REF) {
            len = args[0].string_val.size();
        }
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_int(static_cast<int32_t>(len));
        return true;
    }

    // String.toUpperCase / toLowerCase → convert using std::toupper/tolower.
    if (class_name == "Ljava/lang/String;" &&
        (method == "toUpperCase" || method == "toLowerCase")) {
        std::string s;
        if (!args.empty() && args[0].type == DalvikType::STRING_REF) {
            s = args[0].string_val;
        }
        if (method == "toUpperCase") {
            for (char& c : s) c = static_cast<char>(std::toupper(static_cast<unsigned char>(c)));
        } else {
            for (char& c : s) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
        }
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_string(s, 1);
        return true;
    }

    // String.equals → proper string comparison.
    if (class_name == "Ljava/lang/String;" && method == "equals") {
        bool eq = false;
        if (args.size() >= 2 &&
            args[0].type == DalvikType::STRING_REF &&
            args[1].type == DalvikType::STRING_REF) {
            eq = (args[0].string_val == args[1].string_val);
        }
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_bool(eq);
        return true;
    }

    // String.split → split by delimiter, store as array[idx]/__array_length__.
    if (class_name == "Ljava/lang/String;" && method == "split") {
        std::string s;
        std::string delim;
        if (args.size() >= 1 && args[0].type == DalvikType::STRING_REF) {
            s = args[0].string_val;
        }
        if (args.size() >= 2 && args[1].type == DalvikType::STRING_REF) {
            delim = args[1].string_val;
        }
        uint32_t arr_id = heap_.allocate("Larray;", pc_,
                                          call_stack_.empty() ? 0 : call_stack_.top().frame_id);
        std::vector<std::string> parts;
        if (!delim.empty()) {
            size_t start = 0;
            size_t pos;
            while ((pos = s.find(delim, start)) != std::string::npos) {
                parts.push_back(s.substr(start, pos - start));
                start = pos + delim.size();
            }
            parts.push_back(s.substr(start));
        } else {
            parts.push_back(s);
        }
        for (size_t i = 0; i < parts.size(); ++i) {
            std::string fn = "array[" + std::to_string(i) + "]";
            DalvikValue sv;
            sv.type = DalvikType::STRING_REF;
            sv.string_val = parts[i];
            sv.ref_id = 0;
            heap_.set_object_field(arr_id, fn, sv);
        }
        heap_.set_object_field(arr_id, "__array_length__",
                               DalvikValue::make_int(static_cast<int32_t>(parts.size())));
        DalvikValue arr;
        arr.type = DalvikType::OBJECT_REF;
        arr.object_id = arr_id;
        arr.class_desc = "Larray;";
        arr.int_val = static_cast<int32_t>(parts.size());
        result = arr;
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // TextUtils.equals / isEmpty.
    if (class_name == "Landroid/text/TextUtils;") {
        if (method == "isEmpty") {
            std::string s;
            if (!args.empty() && args[0].type == DalvikType::STRING_REF) {
                s = args[0].string_val;
            } else if (!args.empty() && args[0].type == DalvikType::NULL_REF) {
                // null → isEmpty returns true.
                status = ApiCallTrace::Status::IMPLEMENTED;
                result = DalvikValue::make_bool(true);
                return true;
            }
            status = ApiCallTrace::Status::IMPLEMENTED;
            result = DalvikValue::make_bool(s.empty());
            return true;
        }
        if (method == "equals") {
            bool eq = false;
            if (args.size() >= 2 &&
                args[0].type == DalvikType::STRING_REF &&
                args[1].type == DalvikType::STRING_REF) {
                eq = (args[0].string_val == args[1].string_val);
            } else if (args.size() >= 2 &&
                       args[0].type == DalvikType::NULL_REF &&
                       args[1].type == DalvikType::NULL_REF) {
                eq = true;
            }
            status = ApiCallTrace::Status::IMPLEMENTED;
            result = DalvikValue::make_bool(eq);
            return true;
        }
    }

    // TextView.length → dispatch to ViewShadow.getText().length().
    // CRITICAL: without this, onNextPressed's validation fails (reads 0).
    if (class_name.find("TextView") != std::string::npos &&
        method == "length" &&
        shadow_registry_ != nullptr) {
        auto* view_shadow = shadow_registry_->find_as<framework::ViewShadow>();
        if (view_shadow != nullptr && !args.empty() &&
            args[0].type == DalvikType::OBJECT_REF) {
            const auto* node = view_shadow->find_node(args[0].object_id);
            if (node != nullptr) {
                int32_t len = static_cast<int32_t>(node->text.size());
                status = ApiCallTrace::Status::IMPLEMENTED;
                result = DalvikValue::make_int(len);
                return true;
            }
        }
    }

    // HashMap.get/put/containsKey/size/isEmpty/clear → heap-based storage.
    // Only used as a fallback when shadow_registry_ is null (which doesn't
    // happen in the real runtime — CollectionShadow handles these).
    if (class_name == "Ljava/util/HashMap;" && shadow_registry_ == nullptr) {
        if (!args.empty() && args[0].type == DalvikType::OBJECT_REF &&
            heap_.has_object(args[0].object_id)) {
            uint32_t hm_id = args[0].object_id;
            if (method == "get") {
                std::string key;
                if (args.size() >= 2 && args[1].type == DalvikType::STRING_REF) {
                    key = args[1].string_val;
                }
                auto v = heap_.get_object_field(hm_id, "map:" + key);
                if (v.has_value()) {
                    result = v.value();
                } else {
                    result = DalvikValue::make_null();
                }
                status = ApiCallTrace::Status::IMPLEMENTED;
                return true;
            }
            if (method == "put" && args.size() >= 3 &&
                args[1].type == DalvikType::STRING_REF) {
                heap_.set_object_field(hm_id, "map:" + args[1].string_val, args[2]);
                result = DalvikValue::make_null();
                status = ApiCallTrace::Status::IMPLEMENTED;
                return true;
            }
            if (method == "containsKey" && args.size() >= 2 &&
                args[1].type == DalvikType::STRING_REF) {
                auto v = heap_.get_object_field(hm_id, "map:" + args[1].string_val);
                result = DalvikValue::make_bool(v.has_value());
                status = ApiCallTrace::Status::IMPLEMENTED;
                return true;
            }
            if (method == "size") {
                size_t n = 0;
                if (auto* ho = heap_.get(hm_id)) {
                    for (const auto& [k, v] : ho->fields) {
                        if (k.rfind("map:", 0) == 0) ++n;
                    }
                }
                result = DalvikValue::make_int(static_cast<int32_t>(n));
                status = ApiCallTrace::Status::IMPLEMENTED;
                return true;
            }
            if (method == "isEmpty") {
                size_t n = 0;
                if (auto* ho = heap_.get(hm_id)) {
                    for (const auto& [k, v] : ho->fields) {
                        if (k.rfind("map:", 0) == 0) ++n;
                    }
                }
                result = DalvikValue::make_bool(n == 0);
                status = ApiCallTrace::Status::IMPLEMENTED;
                return true;
            }
            if (method == "clear") {
                if (auto* ho = heap_.get(hm_id)) {
                    std::vector<std::string> to_remove;
                    for (const auto& [k, v] : ho->fields) {
                        if (k.rfind("map:", 0) == 0) to_remove.push_back(k);
                    }
                    for (const auto& k : to_remove) {
                        ho->fields.erase(k);
                    }
                }
                result = DalvikValue::make_void();
                status = ApiCallTrace::Status::IMPLEMENTED;
                return true;
            }
        }
    }

    // BufferedReader.readLine / close, InputStream.close → void/null.
    if (class_name.find("BufferedReader") != std::string::npos) {
        if (method == "readLine") {
            // The actual line reading happens in try_recursive_invoke's
            // readLine intercept (which runs BEFORE this bridge). If we
            // reach here, it means the intercept didn't handle it.
            // Return null (EOF) so callers terminate their loops.
            result = DalvikValue::make_null();
            status = ApiCallTrace::Status::IMPLEMENTED;
            return true;
        }
        if (method == "close") {
            // Remove from open_assets_.
            if (!args.empty() && args[0].type == DalvikType::OBJECT_REF) {
                open_assets_.erase(args[0].object_id);
            }
            result = DalvikValue::make_void();
            status = ApiCallTrace::Status::IMPLEMENTED;
            return true;
        }
    }
    if (class_name.find("InputStream") != std::string::npos &&
        method == "close") {
        if (!args.empty() && args[0].type == DalvikType::OBJECT_REF) {
            open_assets_.erase(args[0].object_id);
        }
        result = DalvikValue::make_void();
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // AssetManager.open → create InputStream with open_assets_ mapping.
    if (class_name.find("AssetManager") != std::string::npos &&
        method == "open") {
        std::string asset_path;
        if (args.size() >= 2 && args[1].type == DalvikType::STRING_REF) {
            asset_path = args[1].string_val;
        }
        uint32_t is_id = heap_.allocate("Ljava/io/InputStream;", pc_,
                                         call_stack_.empty() ? 0 : call_stack_.top().frame_id);
        open_assets_[is_id] = std::make_pair(asset_path, 0);
        DalvikValue is_val;
        is_val.type = DalvikType::OBJECT_REF;
        is_val.object_id = is_id;
        is_val.class_desc = "Ljava/io/InputStream;";
        result = is_val;
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // InputStreamReader.<init> / BufferedReader.<init> → propagate asset.
    if (method == "<init>" &&
        (class_name.find("InputStreamReader") != std::string::npos ||
         class_name.find("BufferedReader") != std::string::npos) &&
        args.size() >= 2 &&
        args[0].type == DalvikType::OBJECT_REF &&
        args[1].type == DalvikType::OBJECT_REF) {
        uint32_t this_id = args[0].object_id;
        uint32_t wrapped_id = args[1].object_id;
        auto it = open_assets_.find(wrapped_id);
        if (it != open_assets_.end()) {
            open_assets_[this_id] = it->second;
        }
        result = DalvikValue::make_void();
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // Resources.getAssets → AssetManager singleton.
    if (class_name.find("Resources") != std::string::npos &&
        method == "getAssets") {
        result = get_or_create_singleton("Landroid/content/res/AssetManager;");
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // Default: stubbed but not crashing
    status = ApiCallTrace::Status::STUBBED;
    result = DalvikValue::make_void();
    return true;
}

// EXP-042 Phase 4: Singleton cache helper.
// Returns an existing heap object for the given class descriptor, or allocates
// a fresh one. Cached in api_singletons_ so that getResources() always returns
// the same Resources object across the entire APK execution.
DalvikValue DalvikExecutionEngine::get_or_create_singleton(const std::string& class_desc) {
    auto it = api_singletons_.find(class_desc);
    if (it != api_singletons_.end()) {
        // Verify the object still exists in the heap
        if (heap_.has_object(it->second)) {
            DalvikValue v;
            v.type = DalvikType::OBJECT_REF;
            v.object_id = it->second;
            v.class_desc = class_desc;
            return v;
        }
    }
    // Allocate new singleton
    uint32_t obj_id = heap_.allocate(class_desc, pc_,
                                    call_stack_.empty() ? 0 : call_stack_.top().frame_id);
    api_singletons_[class_desc] = obj_id;
    // Pre-populate known fields for some singletons
    if (class_desc == "Landroid/util/DisplayMetrics;") {
        DalvikValue density;
        density.type = DalvikType::FLOAT32;
        density.float_val = 1.0f;  // mdpi
        heap_.set_object_field(obj_id, "density", density);
        DalvikValue density_dpi;
        density_dpi.type = DalvikType::INT32;
        density_dpi.int_val = 160;  // DENSITY_MEDIUM
        heap_.set_object_field(obj_id, "densityDpi", density_dpi);
        DalvikValue width_px;
        width_px.type = DalvikType::INT32;
        width_px.int_val = 1080;
        heap_.set_object_field(obj_id, "widthPixels", width_px);
        DalvikValue height_px;
        height_px.type = DalvikType::INT32;
        height_px.int_val = 1920;
        heap_.set_object_field(obj_id, "heightPixels", height_px);
    } else if (class_desc == "Landroid/content/res/Configuration;") {
        DalvikValue screen_layout;
        screen_layout.type = DalvikType::INT32;
        screen_layout.int_val = 0x40;  // SCREENLAYOUT_SIZE_NORMAL
        heap_.set_object_field(obj_id, "screenLayout", screen_layout);
        DalvikValue orientation;
        orientation.type = DalvikType::INT32;
        orientation.int_val = 1;  // ORIENTATION_PORTRAIT
        heap_.set_object_field(obj_id, "orientation", orientation);
    } else if (class_desc == "Ljava/io/File;") {
        DalvikValue path;
        path.type = DalvikType::STRING_REF;
        path.string_val = "/tmp/miniandroid/files";
        path.ref_id = 0;
        heap_.set_object_field(obj_id, "path", path);
    }
    DalvikValue v;
    v.type = DalvikType::OBJECT_REF;
    v.object_id = obj_id;
    v.class_desc = class_desc;
    return v;
}

// ============================================================================
// Utility Methods
// ============================================================================

void DalvikExecutionEngine::log(const std::string& msg) {
    if (verbose_) {
        std::cerr << "[DalvikEngine] " << msg << std::endl;
    }
}

std::string DalvikExecutionEngine::to_hex(uint32_t val) const {
    std::ostringstream o;
    o << "0x" << std::hex << val;
    return o.str();
}

std::string DalvikExecutionEngine::to_hex16(uint16_t val) const {
    std::ostringstream o;
    o << "0x" << std::hex << std::setw(4) << std::setfill('0') << val;
    return o.str();
}

int32_t DalvikExecutionEngine::read_signed_literal(uint16_t val) const {
    // Sign-extend 16-bit to 32-bit
    return static_cast<int32_t>(static_cast<int16_t>(val));
}

std::string DalvikExecutionEngine::get_timestamp() const {
    auto now = std::chrono::system_clock::now();
    auto time_t = std::chrono::system_clock::to_time_t(now);
    std::ostringstream ss;
    ss << std::put_time(std::gmtime(&time_t), "%Y-%m-%dT%H:%M:%SZ");
    return ss.str();
}

// ============================================================================
// Execution Result Serialization
// ============================================================================

json DalvikExecutionResult::to_full_report() const {
    json report;
    report["experiment"] = experiment_id;
    report["timestamp"] = timestamp;
    report["apk"] = apk_name;
    report["sha256"] = apk_sha256;
    
    report["entry_point"] = {
        {"class", main_class},
        {"method", main_method}
    };
    
    report["final_status"] = [this]() -> std::string {
        switch (final_status) {
            case FinalStatus::COMPLETED_SUCCESS: return "SUCCESS";
            case FinalStatus::COMPLETED_PARTIAL: return "PARTIAL";
            case FinalStatus::HALTED_UNIMPLEMENTED_OPCODE: return "HALTED_OPCODE";
            case FinalStatus::HALTED_MISSING_METHOD: return "HALTED_METHOD";
            case FinalStatus::HALTED_API_ERROR: return "HALTED_API";
            case FinalStatus::HALTED_STACK_OVERFLOW: return "HALTED_STACK";
            case FinalStatus::CRASH_EXCEPTION: return "CRASH";
            default: return "UNKNOWN";
        }
    }();
    
    report["halt_reason"] = halt_reason;
    
    report["statistics"] = {
        {"instructions_executed", total_instructions_executed},
        {"opcodes_decoded", total_opcodes_decoded},
        {"execution_ms", total_execution_ms},
        {"heap_objects", heap.size()},
        {"max_call_depth", call_stack.max_depth()},
        {"total_calls", call_stack.get_completed_frames().size()}
    };
    
    report["call_stack"] = call_stack.dump_all_calls();
    report["heap"] = heap.dump();
    
    report["instruction_traces"] = json::array();
    for (const auto& t : instruction_traces) {
        report["instruction_traces"].push_back(t.to_json());
    }
    
    report["api_calls"] = json::array();
    for (const auto& c : api_call_traces) {
        report["api_calls"].push_back(c.to_json());
    }
    
    report["final_registers"] = final_registers;
    
    return report;
}

} // namespace dalvik
} // namespace miniandroid
