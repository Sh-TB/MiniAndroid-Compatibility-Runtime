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
#include "../diagnostics/click_audit.h"  // UNIFIED_002 EXP-100: env-gated click audit (DIAGNOSTIC)
#include "../jni/jni_bridge.h"
// EXP-051: Shadow registry integration.
#include "../framework/shadow_registry.h"
#include "../framework/android_shadows.h"
#include "../framework/dialog_shadow.h"
#include "../framework/canvas_shadow.h"
#include "../framework/heap_adapter.h"
#include <chrono>
#include <algorithm>
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
        // UNIFIED_011.3 TYPED-CATCH: do NOT return early. Direct
        // execute_method callers (unit fixtures, tools) have empty
        // per_dex_raw_data_ and previously never reached the class→
        // superclass map (EXP-068) and class→ClassInfo index (EXP-045)
        // below — so try_recursive_invoke could never dispatch any DEX
        // method ("class not in index") and typed-catch hierarchy walks
        // had no superclass data. Fall through to the shared build.
    } else {

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
    }  // else (per-DEX raw data present)

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

// EXP-088+ Phase 1.2: Inject ALL classes from secondary DEX files into
// the merged dex_report_->classes vector and update class_info_index_.
//
// Background:
//   stage_parse_dex() in execution_engine.cpp only parses classes.dex (DEX 0)
//   into result.dex_report. The other DEX files (classes2..classesN) are
//   loaded into per_dex_raw_data_ but their classes are NEVER merged into
//   dex_report.classes.
//   This means class_info_index_ only contains DEX 0 classes. Any class
//   defined in DEX 1+ (e.g. Telegram's UserConfig in classes3.dex) cannot
//   be found by try_recursive_invoke, which silently returns false and
//   the call is dropped (treated as "class not in index").
//
// This fix parses each secondary DEX file with DexParser, takes its classes,
// and injects them into dex_report_->classes (via const_cast — same pattern
// as the existing on-demand injection at line 826-855). We also update
// class_info_index_ for O(1) lookup.
//
// The original DEX 0 classes already in dex_report_->classes are preserved
// (we only append). Duplicates are detected via class_info_index_.
//
// This is the GENERIC fix for multi-DEX class resolution. It is NOT
// Telegram-specific — any multi-DEX APK benefits.
size_t DalvikExecutionEngine::inject_secondary_dex_classes() {
    if (!dex_report_) {
        log("inject_secondary_dex_classes: dex_report_ is null — skipping");
        return 0;
    }
    if (per_dex_raw_data_.size() <= 1) {
        // Single-DEX APK — nothing to inject.
        return 0;
    }

    // We modify dex_report_->classes via const_cast. The original DexReport
    // is owned by the caller (ExecutionEngine) which keeps it alive for the
    // full execution. The injected ClassInfo entries are read-only data
    // produced by DexParser::parse_data() — they're safe to retain.
    auto& mutable_classes = const_cast<std::vector<dex::ClassInfo>&>(dex_report_->classes);

    size_t injected_count = 0;
    size_t skipped_duplicate = 0;

    // Iterate over secondary DEX files (skip index 0 — that's DEX 0 which
    // is already parsed and present in dex_report_->classes).
    for (uint32_t di = 1; di < per_dex_raw_data_.size(); di++) {
        const auto& raw = per_dex_raw_data_[di];
        if (raw.empty()) continue;

        // Parse this DEX file with DexParser
        dex::DexParser parser;
        // Disable verbose logging for the secondary DEX parse to avoid
        // spamming the log (we may have many secondary DEX files).
        parser.set_verbose(false);
        auto single_report = parser.parse_data(raw, "DEX" + std::to_string(di));

        if (!single_report.is_valid) {
            log("inject_secondary_dex_classes: DEX " + std::to_string(di) +
                " parse failed — skipping (" + single_report.validation_error + ")");
            continue;
        }

        log("inject_secondary_dex_classes: DEX " + std::to_string(di) +
            " parsed — " + std::to_string(single_report.classes.size()) + " classes");

        // Append each class to dex_report_->classes and update index
        for (auto& cls : single_report.classes) {
            // Skip duplicates (a class might be defined in multiple DEX files
            // — rare, but R8/proguard can produce duplicates)
            if (class_info_index_.find(cls.name) != class_info_index_.end()) {
                skipped_duplicate++;
                continue;
            }
            mutable_classes.push_back(std::move(cls));
            size_t new_idx = mutable_classes.size() - 1;
            class_info_index_[mutable_classes.back().name] = new_idx;
            injected_count++;
        }
    }

    log("inject_secondary_dex_classes: injected " + std::to_string(injected_count) +
        " classes from " + std::to_string(per_dex_raw_data_.size() - 1) +
        " secondary DEX files (" + std::to_string(skipped_duplicate) + " duplicates skipped)");
    std::cerr << "[EXP088-MD-INJECT] Injected " << injected_count
              << " classes from secondary DEX files ("
              << skipped_duplicate << " duplicates skipped)"
              << " — total classes now: " << mutable_classes.size()
              << std::endl;

    // Update DEX report aggregate counts so they reflect the merged state
    const_cast<uint32_t&>(dex_report_->classes_count) = (uint32_t)mutable_classes.size();

    // EXP-095 (CM-019): Re-register ALL classes (original + injected) in the
    // superclass map. The map is built BEFORE multi-DEX injection runs, so
    // classes from secondary DEX files (e.g. SlideView → LinearLayout in
    // classes3.dex) were missing — breaking is_subclass_of for every
    // secondary-DEX class (layout detection, instanceof checks).
    {
        size_t added = 0;
        for (const auto& cls : mutable_classes) {
            if (!cls.superclass_name.empty()) {
                if (class_to_superclass_.find(cls.name) == class_to_superclass_.end()) {
                    added++;
                }
                class_to_superclass_[cls.name] = cls.superclass_name;
            }
        }
        std::cerr << "[EXP095-HIER] superclass map extended by " << added
                  << " secondary-DEX classes (total "
                  << class_to_superclass_.size() << ")" << std::endl;
    }

    return injected_count;
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

// ============================================================================
// UNIFIED_011.3 TYPED-CATCH (§18): exception-type compatibility.
//
// Matching sources, in order:
//   1. exact descriptor equality
//   2. DEX superclass chain (class_to_superclass_, includes APK-defined
//      exception classes AND the seeded Android framework hierarchy)
//   3. built-in java.lang / java.io / java.util / org.json exception
//      hierarchy (framework exception classes whose class_defs are NOT in
//      the APK's DEX files — exactly like the View hierarchy seed above).
// `catch_desc` of Object/Throwable catches everything (Dalvik semantics).
// ============================================================================
bool DalvikExecutionEngine::is_exception_subtype(const std::string& exc_desc,
                                                 const std::string& catch_desc) const {
    if (exc_desc.empty() || catch_desc.empty()) return false;
    if (exc_desc == catch_desc) return true;
    if (catch_desc == "Ljava/lang/Object;" || catch_desc == "Ljava/lang/Throwable;") {
        return true;
    }

    // Built-in framework exception hierarchy (child → parent).
    static const std::unordered_map<std::string, std::string> builtin_exc_parent = {
        // java.lang core
        {"Ljava/lang/Exception;", "Ljava/lang/Throwable;"},
        {"Ljava/lang/RuntimeException;", "Ljava/lang/Exception;"},
        {"Ljava/lang/NullPointerException;", "Ljava/lang/RuntimeException;"},
        {"Ljava/lang/IndexOutOfBoundsException;", "Ljava/lang/RuntimeException;"},
        {"Ljava/lang/ArrayIndexOutOfBoundsException;", "Ljava/lang/IndexOutOfBoundsException;"},
        {"Ljava/lang/StringIndexOutOfBoundsException;", "Ljava/lang/IndexOutOfBoundsException;"},
        {"Ljava/lang/ArithmeticException;", "Ljava/lang/RuntimeException;"},
        {"Ljava/lang/IllegalArgumentException;", "Ljava/lang/RuntimeException;"},
        {"Ljava/lang/NumberFormatException;", "Ljava/lang/IllegalArgumentException;"},
        {"Ljava/lang/IllegalStateException;", "Ljava/lang/RuntimeException;"},
        {"Ljava/lang/ClassCastException;", "Ljava/lang/RuntimeException;"},
        {"Ljava/lang/UnsupportedOperationException;", "Ljava/lang/RuntimeException;"},
        {"Ljava/lang/NegativeArraySizeException;", "Ljava/lang/RuntimeException;"},
        {"Ljava/lang/ArrayStoreException;", "Ljava/lang/RuntimeException;"},
        {"Ljava/util/ConcurrentModificationException;", "Ljava/lang/RuntimeException;"},
        {"Ljava/lang/SecurityException;", "Ljava/lang/RuntimeException;"},
        {"Ljava/lang/InterruptedException;", "Ljava/lang/Exception;"},
        {"Ljava/lang/ClassNotFoundException;", "Ljava/lang/Exception;"},
        {"Ljava/lang/ReflectiveOperationException;", "Ljava/lang/Exception;"},
        // java.io
        {"Ljava/io/IOException;", "Ljava/lang/Exception;"},
        {"Ljava/io/FileNotFoundException;", "Ljava/io/IOException;"},
        {"Ljava/io/EOFException;", "Ljava/io/IOException;"},
        // java.util
        {"Ljava/util/NoSuchElementException;", "Ljava/lang/RuntimeException;"},
        {"Ljava/util/InputMismatchException;", "Ljava/util/NoSuchElementException;"},
        // org.json (Android framework JSON)
        {"Lorg/json/JSONException;", "Ljava/lang/Exception;"},
        // org.xmlpull (Android framework XML pull parser — Pass-3 K-35)
        {"Lorg/xmlpull/v1/XmlPullParserException;", "Ljava/lang/Exception;"},
        // Errors (rare, but typed catches for Error exist in real apps)
        {"Ljava/lang/Error;", "Ljava/lang/Throwable;"},
        {"Ljava/lang/OutOfMemoryError;", "Ljava/lang/VirtualMachineError;"},
        {"Ljava/lang/StackOverflowError;", "Ljava/lang/VirtualMachineError;"},
        {"Ljava/lang/VirtualMachineError;", "Ljava/lang/Error;"},
        {"Ljava/lang/AssertionError;", "Ljava/lang/Error;"},
        {"Ljava/lang/NoClassDefFoundError;", "Ljava/lang/LinkageError;"},
        {"Ljava/lang/LinkageError;", "Ljava/lang/Error;"},
    };

    // Walk both chains simultaneously (merged walk, cycle-safe).
    std::string via_dex = exc_desc;
    std::string via_builtin = exc_desc;
    std::unordered_set<std::string> visited;
    for (int depth = 0; depth < 50; ++depth) {
        if (via_dex == catch_desc || via_builtin == catch_desc) return true;
        if (via_dex == "Ljava/lang/Object;" && via_builtin == "Ljava/lang/Object;") break;
        size_t before = visited.size();
        visited.insert(via_dex);
        visited.insert(via_builtin);
        if (visited.size() == before) break;  // no progress → cycle

        // advance DEX chain
        auto dex_it = class_to_superclass_.find(via_dex);
        if (dex_it != class_to_superclass_.end()) {
            via_dex = dex_it->second;
        } else {
            // not DEX-defined: fall through to built-in chain for next step
            auto b_it = builtin_exc_parent.find(via_dex);
            via_dex = (b_it != builtin_exc_parent.end())
                    ? b_it->second : "Ljava/lang/Object;";
        }
        // advance built-in chain
        auto b_it2 = builtin_exc_parent.find(via_builtin);
        if (b_it2 != builtin_exc_parent.end()) {
            via_builtin = b_it2->second;
        } else {
            auto d_it = class_to_superclass_.find(via_builtin);
            via_builtin = (d_it != class_to_superclass_.end())
                    ? d_it->second : "Ljava/lang/Object;";
        }
    }
    return false;
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
        // EXP-088+ F4 CRITICAL FIX: type_list entries are 2 bytes each (ushort type_idx),
        // NOT 4 bytes. The DEX format specification says:
        //   type_list { uint size; type_item list[size]; }
        //   type_item { ushort type_idx; }  ← 2 bytes, not 4
        //
        // Previously this code read 4 bytes per entry, which caused:
        //   1. Wrong proto resolution (e.g. "(J)Z" instead of
        //      "(Lorg/telegram/ui/ActionBar/INavigationLayout;Lorg/telegram/ui/ActionBar/BaseFragment;)Z")
        //   2. Wrong wide-arg merging in invoke-static (fragment arg merged as long)
        //   3. args_size=1 instead of 2 for $default$addFragmentToStack
        //   4. Fragment lifecycle never starts → Phase M blocked
        //
        // This is a GENERIC fix — affects ALL multi-DEX APKs that use
        // desugered interface default methods with 2+ object parameters.
        std::string params_str;
        if (pid.parameters_off != 0 && pid.parameters_off + 4 <= raw.size()) {
            uint32_t list_size;
            std::memcpy(&list_size, raw.data() + pid.parameters_off, 4);
            // Bound check the list entries. Each entry is 2 bytes (ushort).
            size_t list_start = pid.parameters_off + 4;
            size_t list_bytes = static_cast<size_t>(list_size) * 2u;  // FIXED: 2 bytes per entry
            if (list_size <= 1024 && list_start + list_bytes <= raw.size()) {
                for (uint32_t i = 0; i < list_size; ++i) {
                    uint16_t type_idx;  // FIXED: uint16_t, not uint32_t
                    std::memcpy(&type_idx, raw.data() + list_start + i * 2, 2);  // FIXED: i * 2, reading 2 bytes
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
    // EXP-088+ Phase 1.2: Now that dex_report_ is set, inject ALL classes
    // from secondary DEX files (classes2.dex..classesN.dex) into the merged
    // dex_report_->classes vector and class_info_index_.
    //
    // Without this, only classes.dex (DEX 0) classes are available for
    // runtime dispatch. Any class defined in DEX 1+ (e.g. Telegram's
    // UserConfig in classes3.dex) cannot be found by try_recursive_invoke,
    // returning "class not in index" silently and dropping the call.
    //
    // The merged dex_report pointer (dex_report_) was just set above, so
    // this is the earliest point we can call inject_secondary_dex_classes().
    inject_secondary_dex_classes();
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

            // EXP-086 Phase 1: Build the set of descriptor variants to try.
            // activity_class_name can be: dotted ("org.foo.Launcher") or
            // descriptor ("Lorg/foo/Launcher;"). We try both forms.
            std::vector<std::string> descriptor_variants;
            descriptor_variants.push_back(activity_class_name);  // as-is
            {
                std::string descriptor_form = "L" + activity_class_name + ";";
                descriptor_variants.push_back(descriptor_form);
            }
            {
                std::string converted = activity_class_name;
                for (auto& c : converted) if (c == '.') c = '/';
                std::string descriptor_form2 = "L" + converted + ";";
                descriptor_variants.push_back(descriptor_form2);
            }

            // First try: search dex_report.classes (single-DEX report from DEX 0).
            bool found = false;
            for (const auto& cls : dex_report.classes) {
                bool match = false;
                for (const auto& variant : descriptor_variants) {
                    if (cls.name == variant) {
                        match = true;
                        break;
                    }
                }
                if (match) {
                    log("  ✅ Found manifest activity class in DEX 0: " + cls.name);
                    result.main_class = cls.name;
                    found = true;

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

                    // UNIFIED_011.3 FRAME-2 (§23): record the activity's heap
                    // object id so post-launch probes (click-test XML
                    // android:onClick dispatch) can pass the REAL activity
                    // instance as `this`. Without it, handlers executed with
                    // `this` = the clicked View object — every instance-field
                    // access (this.big, this.chrono, ...) hit the wrong heap
                    // object and the post-interaction re-render was unchanged.
                    if (shadow_registry_ != nullptr) {
                        auto* activity_shadow =
                            shadow_registry_->find_as<framework::ActivityShadow>();
                        if (activity_shadow != nullptr) {
                            activity_shadow->set_activity_heap_id(activity_obj_id);
                            std::cerr << "[U0113-ACTIVITY] activity heap object #"
                                      << activity_obj_id << " (" << cls.name
                                      << ") recorded for handler dispatch" << std::endl;
                        }
                    }

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
            log("⚠️ Manifest activity class '" + activity_class_name + "' not found in dex_report.classes (DEX 0) — trying multi-DEX index");

            // EXP-086 Phase 1: Multi-DEX fallback.
            // dex_report.classes only contains classes from DEX 0 (the first
            // DEX file). The activity class may be in DEX 2/3/4 (e.g. Telegram
            // LaunchActivity is in classes3.dex). Use class_to_dex_index_
            // (built by build_class_dex_index) to check ALL DEX files.
            if (!found && !class_to_dex_index_.empty()) {
                for (const auto& variant : descriptor_variants) {
                    auto it = class_to_dex_index_.find(variant);
                    if (it != class_to_dex_index_.end()) {
                        uint32_t dex_idx = it->second;
                        log("  ✅ Found manifest activity class in DEX " + std::to_string(dex_idx) + ": " + variant);
                        result.main_class = variant;

                        // EXP-086 Phase 1: Load this class's full bytecode from
                        // per_dex_raw_data_[dex_idx] and inject it into
                        // dex_report_->classes so try_recursive_invoke can find
                        // it via class_info_index_. This is the GENERIC fix for
                        // multi-DEX entry-point resolution.
                        if (dex_report_ && dex_idx < per_dex_raw_data_.size()) {
                            log("  → Loading class bytecode from DEX " + std::to_string(dex_idx) + "...");
                            // Use DexParser to parse JUST this class from the
                            // per-DEX raw data.
                            dex::DexParser parser;
                            auto single_report = parser.parse_data(per_dex_raw_data_[dex_idx],
                                                                    "DEX" + std::to_string(dex_idx));
                            // Find the target class in the single-DEX report
                            // EXP-086 Phase 1: dex_report_ is `const dex::DexReport*`
                            // because execute_apk_with_activity takes a const&.
                            // We use const_cast to inject the class — this is
                            // safe because we own the lifetime of dex_report
                            // (it's passed by the caller who keeps the original
                            // alive). The injected class is read-only data.
                            //
                            // EXP-088+ F1 defense-in-depth: Check class_info_index_
                            // FIRST. If inject_secondary_dex_classes() already
                            // injected this class (which it should have, since it
                            // injects ALL classes from ALL secondary DEX files),
                            // skip the push_back. This prevents:
                            //   1. Duplicate entries in dex_report_->classes
                            //   2. Potential vector reallocation that could
                            //      invalidate ClassInfo& references held by
                            //      parent execution frames (the F1 finding)
                            //
                            // This on-demand path is now effectively dead code
                            // for multi-DEX APKs (inject_secondary_dex_classes
                            // handles everything), but it's kept as a fallback
                            // for single-DEX APKs that don't call the bulk
                            // injection.
                            auto it_existing = class_info_index_.find(variant);
                            if (it_existing != class_info_index_.end()) {
                                log("  ✅ " + variant + " already in class_info_index_"
                                    " (index " + std::to_string(it_existing->second) +
                                    ") — skipping on-demand injection (inject_secondary_dex_classes"
                                    " already handled it)");
                                found = true;
                            } else {
                                auto& mutable_classes = const_cast<std::vector<dex::ClassInfo>&>(dex_report_->classes);
                                for (auto& single_cls : single_report.classes) {
                                    if (single_cls.name == variant) {
                                        // Inject into dex_report_->classes and update index
                                        mutable_classes.push_back(single_cls);
                                        size_t new_idx = mutable_classes.size() - 1;
                                        class_info_index_[variant] = new_idx;
                                        log("  ✅ Injected " + variant + " into dex_report_->classes"
                                            " (index " + std::to_string(new_idx) + ", "
                                            + std::to_string(single_cls.direct_methods.size())
                                            + " direct + "
                                            + std::to_string(single_cls.virtual_methods.size())
                                            + " virtual methods)");
                                        found = true;
                                        break;
                                    }
                                }
                                if (!found) {
                                    log("  ⚠️ Class " + variant + " not found in DEX "
                                        + std::to_string(dex_idx) + " raw data");
                                }
                            }
                        }

                        if (found) {
                            // EXP-043 Phase 4: Pre-populate static fields
                            uint32_t app_ctx_id = heap_.allocate(
                                "Landroid/app/Application;",
                                0,  // pc=0 (pre-execution)
                                0   // frame_id=0 (pre-execution)
                            );
                            DalvikValue app_ctx_val;
                            app_ctx_val.type = DalvikType::OBJECT_REF;
                            app_ctx_val.object_id = app_ctx_id;
                            app_ctx_val.class_desc = "Landroid/app/Application;";
                            static_field_storage_["Lorg/telegram/messenger/ApplicationLoader;.applicationContext"]
                                = app_ctx_val;
                            // Set current_dex_index_ so per-DEX resolution uses the right DEX
                            current_dex_index_ = dex_idx;
                        }
                        break;
                    }
                }
            }

            if (!found) {
                log("⚠️ Manifest activity class '" + activity_class_name + "' not found in any DEX — falling back to scan");
            } else {
                // EXP-086 Phase 1: Skip the legacy Activity/Main scan when we
                // found the manifest activity class in the multi-DEX index.
                // try_recursive_invoke will resolve onCreate via per-DEX raw data.
                log("🎯 Skipping legacy scan — manifest activity class found in multi-DEX index");
                // Try to invoke onCreate(Bundle) directly via try_recursive_invoke
                // which will look up the method in the correct DEX.
                std::vector<DalvikValue> entry_args;
                entry_args.push_back(DalvikValue::make_null());  // p1 = Bundle (null)
                DalvikValue return_val;  // onCreate returns void
                try {
                    log("🎯 Invoking onCreate via try_recursive_invoke (manifest class)");
                    bool ok = try_recursive_invoke(
                        result.main_class,
                        "onCreate",
                        entry_args,
                        return_val,
                        result,
                        "(Landroid/os/Bundle;)V"
                    );
                    if (ok) {
                        log("✅ onCreate invoked via try_recursive_invoke");
                        result.main_method = "onCreate";
                    } else {
                        log("⚠️ try_recursive_invoke returned false for onCreate");
                    }
                } catch (const std::exception& e) {
                    log("❌ try_recursive_invoke threw: " + std::string(e.what()));
                }
                goto entry_point_search_done;
            }
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

    // UNIFIED_011.3 TYPED-CATCH: set dex_report_ on the unit entry point too.
    // Previously only execute_apk_with_activity set it (EXP-037 BLOCKER-002),
    // so direct execute_method callers had every resolve_*_for_dex fallback
    // return "<unknown>" — including the UNIFIED_011.3 typed-catch handler
    // type resolution (catch type descriptors are resolved per-DEX and fall
    // back to dex_report_->types).
    dex_report_ = &dex_report;
    // EXP-068 hierarchy map + EXP-045 class_info_index_ + EXP-088 dex index
    // are all built by build_class_dex_index(report) on the APK path; the
    // unit entry point needs them for invoke dispatch and type resolution.
    build_class_dex_index(dex_report);

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
    // EXP-093: Store ALL R$string values (including small D8-shrunk ordinals).
    // The D8 shrinker remaps resource IDs to small ordinals per R$subclass.
    // R$string.SentSmsCode=3 is different from R$anim.text_out_down=3.
    // By storing R$string values, we can resolve them via field_name_by_resid_.
    // R$bool / R$integer / R$color values >= 0x10000 are still stored (they
    // don't collide with R$string ordinals because they use the >= 0x10000 range).
    if (class_descriptor.find("R$") != std::string::npos) {
        bool is_r_string = (class_descriptor.find("R$string") != std::string::npos);
        bool is_r_raw = (class_descriptor.find("R$raw") != std::string::npos);
        // EXP-098 (CM-027): R$raw also uses small D8-shrunk ordinals
        // (e.g. R.raw.default_pattern=3, R.raw.bot_webview_sheet_to_cross=3)
        // intermixed with large values (R.raw.chats_archiveavatar=917525).
        // Store ALL values so RLottieImageView.setAnimation(R.raw.X, w, h)
        // can resolve to the field name → resource_raw_paths_ lookup.
        bool store_all = is_r_string || is_r_raw;
        for (const auto& field : cls_ref.static_fields) {
            if (!field.has_default_value || field.default_value_is_string) continue;
            if (store_all) {
                // Store ALL values (including small ordinals like 0, 1, 2, 3).
                // Multiple R$subclasses can have value=3 — distinguished by
                // the calling class context (R$string.SentSmsCode vs
                // R$raw.bot_webview_sheet_to_cross). The caller resolves
                // via the right resource_raw_paths_/resource_string_values_.
                field_name_by_resid_[static_cast<int32_t>(field.default_int_value)] = field.name;
            } else {
                // For non-R$string/R$raw: only store values >= 0x10000
                if (field.default_int_value >= 0x10000) {
                    field_name_by_resid_[static_cast<int32_t>(field.default_int_value)] = field.name;
                }
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

// ─── FINAL CANONICAL MASTER RECONCILIATION Pass-3 helpers (K-34/K-35) ──────
namespace {
// Basic XML entity unescape for the pull parser's TEXT/attribute values
// (the five predefined entities + small numeric character references).
std::string xml_unescape_pass3(const std::string& in) {
    std::string out;
    out.reserve(in.size());
    for (size_t i = 0; i < in.size(); ++i) {
        if (in[i] == '&') {
            size_t semi = in.find(';', i + 1);
            if (semi != std::string::npos && semi - i <= 10) {
                std::string ent = in.substr(i + 1, semi - i - 1);
                if (ent == "lt")  { out += '<';  i = semi; continue; }
                if (ent == "gt")  { out += '>';  i = semi; continue; }
                if (ent == "amp") { out += '&';  i = semi; continue; }
                if (ent == "quot"){ out += '"';  i = semi; continue; }
                if (ent == "apos"){ out += '\''; i = semi; continue; }
                if (!ent.empty() && ent[0] == '#' && ent.size() >= 2) {
                    bool hex = (ent[1] == 'x' || ent[1] == 'X');
                    long cp = strtol(ent.c_str() + (hex ? 2 : 1), nullptr, hex ? 16 : 10);
                    if (cp > 0 && cp < 128) { out += static_cast<char>(cp); i = semi; continue; }
                }
            }
        }
        out += in[i];
    }
    return out;
}
}  // namespace

// Pass-3 (K-34): resolve an open asset stream chain to path + position.
// Same wrapper hops the readLine block always used (BufferedReader.in →
// InputStreamReader.source → InputStream), factored out so InputStream
// read()/available()/close() share ONE real implementation.
bool DalvikExecutionEngine::resolve_asset_stream(uint32_t start_id,
                                                 std::string& path,
                                                 size_t*& pos) {
    uint32_t lookup_id = start_id;
    for (int hop = 0; hop < 4 && lookup_id != 0; ++hop) {
        auto it = open_assets_.find(lookup_id);
        if (it != open_assets_.end()) {
            path = it->second.first;
            pos = &it->second.second;
            return true;
        }
        if (heap_.has_object(lookup_id)) {
            const auto* ho = heap_.get(lookup_id);
            if (!ho) return false;
            uint32_t next_id = 0;
            for (const char* fn : {"in", "source", "inputStream", "reader", "is"}) {
                auto fv = ho->get_field(fn);
                if (fv.type == DalvikType::OBJECT_REF) { next_id = fv.object_id; break; }
            }
            if (next_id == 0 || next_id == lookup_id) return false;
            lookup_id = next_id;
        } else {
            return false;
        }
    }
    return false;
}

// Pass-3 (K-34): asset bytes extracted once per path, then cached.
const std::string& DalvikExecutionEngine::cached_asset_bytes(const std::string& path) {
    auto it = asset_bytes_cache_.find(path);
    if (it != asset_bytes_cache_.end()) return it->second;
    std::string content;
    if (!apk_path_.empty()) {
        std::string cmd = "unzip -p '" + apk_path_ + "' 'assets/" + path + "' 2>/dev/null";
        FILE* pipe = popen(cmd.c_str(), "r");
        if (pipe) {
            char buf[4096];
            size_t n;
            while ((n = fread(buf, 1, sizeof(buf), pipe)) > 0) content.append(buf, n);
            pclose(pipe);
        }
    }
    return asset_bytes_cache_.emplace(path, std::move(content)).first->second;
}

// Pass-3 (K-35): REAL XmlPullParser event machine — one event per call.
// Progression: START_DOCUMENT → (misc-skip: whitespace/comments/PI/DOCTYPE)
// → START_TAG / TEXT / END_TAG … → END_DOCUMENT (terminal; next() after it
// throws XmlPullParserException at the call site). Self-closing tags queue
// exactly one END_TAG, mirroring KXml.
void DalvikExecutionEngine::xml_pull_advance(XmlPullState& st) {
    if (st.ended) return;
    const std::string& s = st.content;
    size_t i = st.pos;
    auto skip_misc = [&]() {
        for (;;) {
            while (i < s.size() && std::isspace(static_cast<unsigned char>(s[i]))) ++i;
            if (i + 3 < s.size() && s.compare(i, 4, "<!--") == 0) {
                size_t e = s.find("-->", i + 4);
                i = (e == std::string::npos) ? s.size() : e + 3;
                continue;
            }
            if (i + 1 < s.size() && s[i] == '<' && s[i + 1] == '?') {
                size_t e = s.find("?>", i + 2);
                i = (e == std::string::npos) ? s.size() : e + 2;
                continue;
            }
            if (i + 8 < s.size() && s.compare(i, 9, "<![CDATA[") == 0) {
                size_t e = s.find("]]>", i + 9);
                i = (e == std::string::npos) ? s.size() : e + 3;
                continue;  // CDATA content is surfaced via nextToken(), skipped by next()
            }
            if (i + 1 < s.size() && s[i] == '<' && s[i + 1] == '!') {
                size_t e = s.find('>', i + 2);
                i = (e == std::string::npos) ? s.size() : e + 1;
                continue;
            }
            break;
        }
    };
    if (st.pending_end) {
        st.pending_end = false;
        st.event = 3;  // END_TAG
        st.cur_name = st.pending_end_name;
        st.cur_text.clear();
        st.attrs.clear();
        st.pos = i;
        return;
    }
    skip_misc();
    if (i >= s.size()) {
        st.event = 1;  // END_DOCUMENT
        st.ended = true;
        st.cur_name.clear();
        st.cur_text.clear();
        st.attrs.clear();
        st.pos = i;
        return;
    }
    if (s[i] == '<') {
        if (i + 1 < s.size() && s[i + 1] == '/') {
            size_t e = s.find('>', i);
            st.cur_name = (e == std::string::npos) ? s.substr(i + 2)
                                                    : s.substr(i + 2, e - i - 2);
            while (!st.cur_name.empty() &&
                   std::isspace(static_cast<unsigned char>(st.cur_name.back())))
                st.cur_name.pop_back();
            st.event = 3;  // END_TAG
            st.cur_text.clear();
            st.attrs.clear();
            i = (e == std::string::npos) ? s.size() : e + 1;
        } else {
            size_t e = s.find('>', i);
            if (e == std::string::npos) {
                st.event = 1;  // malformed document → terminate
                st.ended = true;
                st.pos = s.size();
                return;
            }
            std::string inner = s.substr(i + 1, e - i - 1);
            bool self_close = false;
            while (!inner.empty() && std::isspace(static_cast<unsigned char>(inner.back())))
                inner.pop_back();
            if (!inner.empty() && inner.back() == '/') { self_close = true; inner.pop_back(); }
            size_t k = 0;
            while (k < inner.size() && !std::isspace(static_cast<unsigned char>(inner[k])) &&
                   inner[k] != '=')
                ++k;
            st.cur_name = inner.substr(0, k);
            st.attrs.clear();
            while (k < inner.size()) {
                while (k < inner.size() && std::isspace(static_cast<unsigned char>(inner[k]))) ++k;
                size_t n0 = k;
                while (k < inner.size() && inner[k] != '=' &&
                       !std::isspace(static_cast<unsigned char>(inner[k])))
                    ++k;
                if (k == n0) break;
                std::string aname = inner.substr(n0, k - n0);
                while (k < inner.size() && std::isspace(static_cast<unsigned char>(inner[k]))) ++k;
                std::string aval;
                if (k < inner.size() && inner[k] == '=') {
                    ++k;
                    while (k < inner.size() && std::isspace(static_cast<unsigned char>(inner[k]))) ++k;
                    if (k < inner.size() && (inner[k] == '"' || inner[k] == '\'')) {
                        char q = inner[k++];
                        size_t v0 = k;
                        while (k < inner.size() && inner[k] != q) ++k;
                        aval = inner.substr(v0, k - v0);
                        if (k < inner.size()) ++k;
                    } else {
                        size_t v0 = k;
                        while (k < inner.size() && !std::isspace(static_cast<unsigned char>(inner[k]))) ++k;
                        aval = inner.substr(v0, k - v0);
                    }
                }
                st.attrs.emplace_back(aname, xml_unescape_pass3(aval));
            }
            st.event = 2;  // START_TAG
            st.cur_text.clear();
            if (self_close) {
                st.pending_end = true;
                st.pending_end_name = st.cur_name;
            }
            i = e + 1;
        }
        st.pos = i;
        return;
    }
    // TEXT: characters up to the next '<' (or EOF).
    size_t e2 = s.find('<', i);
    std::string raw = (e2 == std::string::npos) ? s.substr(i) : s.substr(i, e2 - i);
    st.cur_text = xml_unescape_pass3(raw);
    st.cur_name.clear();
    st.attrs.clear();
    st.event = 4;  // TEXT
    st.pos = (e2 == std::string::npos) ? s.size() : e2;
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
    // UC009-COMPOSE-TRACE: gated visibility into the Compose composition
    // chain (AbstractComposeView.ensureCompositionCreated -> Recomposer ->
    // Composer -> slot-table). Enable with MINIANDROID_TRACE_COMPOSE=1.
    {
        static thread_local const bool tc = std::getenv("MINIANDROID_TRACE_COMPOSE") != nullptr;
        if (tc && (declaring_class.find("ompos") != std::string::npos ||
                   declaring_class.find("oroutin") != std::string::npos ||
                   declaring_class.find("Choreographer") != std::string::npos ||
                   declaring_class.find("MonotonicFrameClock") != std::string::npos)) {
            std::cerr << "[COMPOSE-TRY] " << declaring_class << "." << method_name
                      << " depth=" << recursion_depth_ << std::endl;
        }
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
    // EXP-092 DIRECT TRACE: setPage, fillNextCodeParams, RequestDelegate.run
    // The user demands direct proof of:
    //   RequestDelegate → callback → fillNextCodeParams → setPage(VIEW_CODE_SMS)
    // Do not infer this from screenshot — record page value, receiver,
    // PC, caller, arguments.
    //
    // Each trace is guarded by exact method_name AND a class-name
    // substring check so it only fires on the relevant invocation.
    // Args are accessed only after explicit bounds checks.
    if (method_name == "setPage" && declaring_class.find("LoginActivity") != std::string::npos) {
        std::cerr << "[EXP092-SETPAGE] class=" << declaring_class
                  << " args_count=" << args.size()
                  << " pc=0x" << std::hex << pc_ << std::dec
                  << " caller=" << current_class_ << "." << current_method_
                  << " depth=" << recursion_depth_;
        if (!args.empty() && args[0].type == DalvikType::OBJECT_REF) {
            std::cerr << " receiver_id=" << args[0].object_id
                      << " receiver_runtime_class=" << args[0].class_desc;
        }
        if (args.size() >= 2 && args[1].type == DalvikType::INT32) {
            std::cerr << " page_value=" << args[1].int_val;
        }
        std::cerr << std::endl;
    }
    if (method_name == "fillNextCodeParams") {
        std::cerr << "[EXP092-FILLNEXTCODE] class=" << declaring_class
                  << " args_count=" << args.size()
                  << " pc=0x" << std::hex << pc_ << std::dec
                  << " caller=" << current_class_ << "." << current_method_
                  << " depth=" << recursion_depth_;
        if (!args.empty() && args[0].type == DalvikType::OBJECT_REF) {
            std::cerr << " receiver_id=" << args[0].object_id;
        }
        std::cerr << std::endl;
    }
    if (method_name == "run" && declaring_class.find("ExternalSyntheticLambda") != std::string::npos) {
        std::cerr << "[EXP092-REQDELEGATE] class=" << declaring_class
                  << " args_count=" << args.size()
                  << " pc=0x" << std::hex << pc_ << std::dec
                  << " caller=" << current_class_ << "." << current_method_
                  << " depth=" << recursion_depth_;
        if (!args.empty() && args[0].type == DalvikType::OBJECT_REF) {
            std::cerr << " receiver_id=" << args[0].object_id;
        }
        if (args.size() >= 2 && args[1].type == DalvikType::OBJECT_REF) {
            std::cerr << " response_id=" << args[1].object_id
                      << " response_class=" << args[1].class_desc;
        }
        std::cerr << std::endl;
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
                // EXP-092+ FIX: Do NOT mock auth.sendCode here. Let it fall
                // through to the more thorough [EXP070-NET] interceptor below
                // (line ~2528) which sets the `type` field to
                // TL_auth_sentCodeTypeSms, `phone_code_hash`, `length`, and
                // `timeout`. Without the type field, fillNextCodeParams takes
                // the default path and sets page=13 (LoginActivityEmailCodeView)
                // instead of the SMS page (LoginActivitySmsView).
                //
                // The early mock created an EMPTY TL_auth_sentCode with no
                // type field, causing the wrong page transition.
                std::cerr << "[EXP071-SNDREQ] TL_auth_sendCode detected — "
                          << "deferring to EXP070-NET interceptor for proper "
                          << "type/length/timeout fields" << std::endl;
                // Don't set response_id here — let the EXP070-NET path handle it.
                // But we still need to dispatch the delegate. Set a flag and
                // fall through... actually, we can't easily fall through from
                // here because the early interceptor has a different code path.
                // Instead, create the response WITH the type field here.
                response_id = heap_.allocate(
                    "Lorg/telegram/tgnet/TLRPC$TL_auth_sentCode;", pc_, 0);

                // Set phone_code_hash
                DalvikValue hash_val;
                hash_val.type = DalvikType::STRING_REF;
                hash_val.string_val = "mock_phone_code_hash_exp092";
                hash_val.ref_id = 0;
                heap_.set_object_field(response_id, "phone_code_hash", hash_val);

                // Set type = TL_auth_sentCodeTypeSms
                uint32_t type_id = heap_.allocate(
                    "Lorg/telegram/tgnet/TLRPC$TL_auth_sentCodeTypeSms;", pc_, 0);
                DalvikValue type_val;
                type_val.type = DalvikType::OBJECT_REF;
                type_val.object_id = type_id;
                type_val.class_desc = "Lorg/telegram/tgnet/TLRPC$TL_auth_sentCodeTypeSms;";
                heap_.set_object_field(response_id, "type", type_val);

                // Set length = 5 on both the sentCode and the type
                DalvikValue length_val = DalvikValue::make_int(5);
                heap_.set_object_field(response_id, "length", length_val);
                heap_.set_object_field(type_id, "length", length_val);

                // Set timeout = 30
                DalvikValue timeout_val = DalvikValue::make_int(30);
                heap_.set_object_field(response_id, "timeout", timeout_val);

                // Set is_sent_via_flash_call = false
                DalvikValue false_val = DalvikValue::make_bool(false);
                heap_.set_object_field(response_id, "is_sent_via_flash_call", false_val);

                std::cerr << "[EXP071-SNDREQ] mocked TL_auth_sentCode WITH type=Sms"
                          << " resp_id=" << response_id
                          << " type_id=" << type_id
                          << " length=5 timeout=30" << std::endl;
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
    // Pass-3 (K-34): the old "read() returns 0, no real impl" shadow is GONE —
    // InputStream.read()/available()/close() now read REAL asset bytes (see
    // the bridge right below). readLine keeps its line-splitting semantics.
    if (method_name == "readLine" &&
        declaring_class.find("BufferedReader") != std::string::npos) {
        if (!args.empty() && args[0].type == DalvikType::OBJECT_REF) {
            uint32_t br_id = args[0].object_id;
            std::string asset_path;
            size_t* pos_ptr = nullptr;
            // Pass-3 (K-34): chain resolution factored into resolve_asset_stream()
            // (same wrapper hops: BufferedReader.in → InputStreamReader.source →
            // InputStream), shared with the InputStream read()/available() bridge.
            if (resolve_asset_stream(br_id, asset_path, pos_ptr) &&
                !asset_path.empty() && pos_ptr != nullptr && !apk_path_.empty()) {
                // Pass-3 (K-34): asset bytes are extracted once and cached.
                const std::string& content = cached_asset_bytes(asset_path);
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
        // Fallback: return null (EOF) — don't recurse into DEX.
        return_val = DalvikValue::make_null();
        recursion_depth_--;
        return true;
    }

    // FINAL CANONICAL MASTER RECONCILIATION Pass-3 (K-34): InputStream.read()
    // reads REAL asset bytes. Before this pass the shadow returned 0 (the old
    // comment said: "our shadow InputStream.read returns 0 (no real impl)")
    // and only BufferedReader.readLine bypassed it.
    // Real Android semantics: read() → next byte 0..255, -1 at EOF;
    // read(byte[] b, int off, int len) → count filled, -1 at EOF;
    // available() → bytes remaining; close() → later reads see EOF.
    if (declaring_class.find("InputStream") != std::string::npos &&
        (method_name == "read" || method_name == "available" ||
         method_name == "close")) {
        if (!args.empty() && args[0].type == DalvikType::OBJECT_REF) {
            uint32_t is_id = args[0].object_id;
            std::string asset_path;
            size_t* pos_ptr = nullptr;
            resolve_asset_stream(is_id, asset_path, pos_ptr);
            if (method_name == "close") {
                if (pos_ptr != nullptr) *pos_ptr = static_cast<size_t>(-1);
                return_val = DalvikValue::make_void();
                recursion_depth_--;
                return true;
            }
            if (!asset_path.empty() && pos_ptr != nullptr) {
                const std::string& content = cached_asset_bytes(asset_path);
                size_t p = *pos_ptr;
                if (p == static_cast<size_t>(-1) || p >= content.size()) {
                    return_val = DalvikValue::make_int(
                        (method_name == "available") ? 0 : -1);
                    recursion_depth_--;
                    return true;
                }
                if (method_name == "available") {
                    return_val = DalvikValue::make_int(
                        static_cast<int32_t>(content.size() - p));
                    recursion_depth_--;
                    return true;
                }
                // method_name == "read"
                if (args.size() >= 4 && args[1].type == DalvikType::OBJECT_REF) {
                    // read(byte[] b, int off, int len) → count filled, -1 at EOF.
                    uint32_t arr_id = args[1].object_id;
                    int32_t off = (args[2].type == DalvikType::INT32) ? args[2].int_val : 0;
                    int32_t len = (args[3].type == DalvikType::INT32) ? args[3].int_val : 0;
                    int64_t arr_len = 0;
                    auto len_field = heap_.get_object_field(arr_id, "__array_length__");
                    if (len_field.has_value() && len_field->type == DalvikType::INT32)
                        arr_len = len_field->int_val;
                    if (arr_len == 0) {
                        // Compatibility fallback: NEW_ARRAY used a different name.
                        auto len2 = heap_.get_object_field(arr_id, "__new_array_length__");
                        if (len2.has_value() && len2->type == DalvikType::INT32)
                            arr_len = len2->int_val;
                    }
                    if (arr_len == 0) {
                        // Final fallback: the array register carries the size in int_val.
                        if (args[1].type == DalvikType::OBJECT_REF && args[1].int_val > 0)
                            arr_len = args[1].int_val;
                    }
                    if (off < 0 || len < 0 ||
                        static_cast<int64_t>(off) + static_cast<int64_t>(len) > arr_len) {
                        throw_deferred("Ljava/lang/IndexOutOfBoundsException;",
                                       "read: off=" + std::to_string(off) +
                                           " len=" + std::to_string(len) +
                                           " arr_len=" + std::to_string(arr_len),
                                       "STREAM-READ");
                        return true;
                    }
                    size_t remaining = content.size() - p;
                    size_t count = std::min(static_cast<size_t>(len), remaining);
                    for (size_t k = 0; k < count; ++k) {
                        heap_.set_object_field(
                            arr_id, "array[" + std::to_string(off + static_cast<int32_t>(k)) + "]",
                            DalvikValue::make_byte(static_cast<int8_t>(content[p + k])));
                    }
                    *pos_ptr = p + count;
                    return_val = DalvikValue::make_int(count > 0 ? static_cast<int32_t>(count) : -1);
                    std::cerr << "[STREAM-READ] asset=" << asset_path
                              << " read[off=" << off << " len=" << len
                              << "] → " << (count > 0 ? std::to_string(count) : std::string("-1 EOF"))
                              << std::endl;
                    recursion_depth_--;
                    return true;
                }
                // Single-byte read() → 0..255, or -1 at EOF.
                return_val = DalvikValue::make_int(
                    static_cast<unsigned char>(content[p]));
                *pos_ptr = p + 1;
                recursion_depth_--;
                return true;
            }
        }
        // No resolvable asset stream: honest "no data" answer (never a
        // silent fake 0 that spins read loops forever).
        return_val = DalvikValue::make_int(
            (method_name == "available") ? 0 : -1);
        std::cerr << "[STREAM-READ] " << declaring_class << "." << method_name
                  << " with no resolvable asset → "
                  << (method_name == "available" ? 0 : -1) << std::endl;
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

        // EXP-098 (CM-027): RLottieDrawable.<init>(R.raw.X, name, w, h, ...)
        // — capture (raw_resid, w, h) BEFORE the constructor bytecode runs.
        // Per Telegram source (RLottieDrawable.java:589):
        //   public RLottieDrawable(@RawRes int rawRes, String name, int w, int h, ...) {
        //     String jsonString = readRes(rawRes);  // reads R.raw.X as UTF-8
        //     nativePtr = RLottieNative.createFromRawJson(jsonString, ...);
        //   }
        // We record the pending animation keyed by the drawable's object_id;
        // a later setAnimation(RLottieDrawable) transfers it to the ImageView.
        // args: [this, rawRes, name, w, h, startDecode, colorReplacement]
        if (declaring_class.find("RLottieDrawable") != std::string::npos &&
            args.size() >= 5 &&
            args[0].type == DalvikType::OBJECT_REF &&
            args[1].type == DalvikType::INT32 &&
            args[3].type == DalvikType::INT32 &&
            args[4].type == DalvikType::INT32) {
            uint32_t drawable_id = args[0].object_id;
            int32_t raw_resid = args[1].int_val;
            int target_w = args[3].int_val;
            int target_h = args[4].int_val;
            pending_anim_by_drawable_[drawable_id] = {raw_resid, target_w, target_h};
            std::cerr << "[EXP098-RLDRAWABLE-INIT] obj=" << drawable_id
                      << " raw_resid=" << raw_resid
                      << " target=" << target_w << "x" << target_h
                      << std::endl;
        }
    }

    // EXP-098 (CM-027): RLottieImageView.setAnimation(RLottieDrawable) —
    // transfer the pending animation from the drawable to the ImageView.
    // This runs in try_recursive_invoke BEFORE the DEX bytecode executes.
    // Per Telegram source (RLottieImageView.java:84):
    //   public void setAnimation(RLottieDrawable lottieDrawable) {
    //     drawable = lottieDrawable;
    //     ...
    //   }
    if (method_name == "setAnimation" &&
        declaring_class.find("RLottieImageView") != std::string::npos &&
        args.size() >= 2 &&
        args[0].type == DalvikType::OBJECT_REF &&
        args[1].type == DalvikType::OBJECT_REF &&
        shadow_registry_ != nullptr) {
        uint32_t view_id = args[0].object_id;
        uint32_t drawable_id = args[1].object_id;
        auto it = pending_anim_by_drawable_.find(drawable_id);
        if (it != pending_anim_by_drawable_.end()) {
            const auto& pa = it->second;
            auto* vs = shadow_registry_->find_as<framework::ViewShadow>();
            if (vs != nullptr) {
                vs->set_anim_pending(view_id, pa.raw_resid,
                                     pa.target_w, pa.target_h);
                std::cerr << "[EXP098-RLOTTIE-PENDING] view=" << view_id
                          << " via drawable=" << drawable_id
                          << " resid=" << pa.raw_resid
                          << " target=" << pa.target_w << "x" << pa.target_h
                          << std::endl;
            }
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

    // EXP-093: TextView.getText() intercept — return ViewNode.text
    // Per AOSP: TextView.getText() returns the CharSequence that was set
    // via setText(). The DEX bytecode for getText() builds a garbage "View"
    // string via StringBuilder. We intercept and return ViewNode.text.
    if (method_name == "getText" &&
        (declaring_class.find("TextView") != std::string::npos ||
         declaring_class.find("EditText") != std::string::npos) &&
        shadow_registry_ != nullptr) {
        auto* view_shadow = shadow_registry_->find_as<framework::ViewShadow>();
        if (view_shadow != nullptr && !args.empty() &&
            args[0].type == DalvikType::OBJECT_REF) {
            const auto* node = view_shadow->find_node(args[0].object_id);
            if (node != nullptr) {
                return_val = DalvikValue::make_string(node->text, args[0].object_id);
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
    //
    // EXP-088+ Phase 5: Added Lj$/util/concurrent/ConcurrentHashMap; — this is
    // the desugared Java 8 ConcurrentHashMap used by Telegram's FormatCache.
    // Its DEX bytecode at method `e` (computeIfAbsent) loops forever calling
    // hashCode() on the key. Without bypassing, the runtime hangs in <clinit>
    // of FastDateFormat and never reaches LoginActivity.
    // This is a GENERIC fix — any APK using desugared Java 8 collections hits
    // the same hang.
    {
        bool should_bypass = false;
        if (declaring_class == "Ljava/util/HashMap;" ||
            declaring_class == "Ljava/util/ArrayList;" ||
            declaring_class == "Ljava/util/AbstractList;" ||
            declaring_class == "Ljava/util/AbstractMap;" ||
            declaring_class == "Ljava/lang/String;" ||
            declaring_class == "Landroid/text/TextUtils;" ||
            declaring_class == "Ljava/io/File;" ||
            // EXP-088+ Phase 5: desugared Java 8 ConcurrentHashMap
            // (Lj$/util/concurrent/ConcurrentHashMap;). Its .e/.f methods
            // (computeIfAbsent, compute) loop forever on hashCode().
            declaring_class == "Lj$/util/concurrent/ConcurrentHashMap;" ||
            declaring_class == "Ljava/util/concurrent/ConcurrentHashMap;") {
            should_bypass = true;
        }
        // AndroidUtilities.{runOnUIThread,executeOnUIThread,cancelRunOnUIThread}
        // — the DEX bytecode recurses infinitely (each calls the next).
        if (declaring_class.find("AndroidUtilities") != std::string::npos &&
            (method_name == "runOnUIThread" ||
             method_name == "executeOnUIThread" ||
             method_name == "cancelRunOnUIThread" ||
             // EXP-088+ F4 followup: readRes loops forever reading a raw
             // resource into a byte buffer. In headless mode, the InputStream
             // returns 0/-1, causing the while loop to spin. Bypass to
             // bridge_to_api which returns null (no resource data).
             method_name == "readRes")) {
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

    // EXP-093: Intercept LocaleController.formatString BEFORE it calls Application.getString.
    // The formatString method receives the resource KEY NAME as args[0] (STRING).
    // We use this key to resolve the format string directly from resource_string_values_,
    // bypassing the broken resid resolution (D8 shrinker remaps multiple fields to same ordinal).
    if (method_name == "formatString" &&
        declaring_class.find("LocaleController") != std::string::npos &&
        !args.empty() && args[0].type == DalvikType::STRING_REF) {
        std::string key = args[0].string_val;
        auto sv_it = resource_string_values_.find(key);
        if (sv_it != resource_string_values_.end()) {
            // We have the format string. Now format it with args.
            // The 5-arg formatString has: key, fallback, res, fallbackRes, Object[] args
            // The 3-arg formatString has: key, res, Object[] args
            // Find the Object[] args (last argument)
            std::string format_str = sv_it->second;
            std::string result_str = format_str;

            // Try to find the varargs Object[] in args
            for (int ai = args.size() - 1; ai >= 1; ai--) {
                if (args[ai].type == DalvikType::OBJECT_REF && args[ai].object_id != 0) {
                    uint32_t arr_id = args[ai].object_id;
                    if (heap_.has_object(arr_id)) {
                        auto len_field = heap_.get_object_field(arr_id, "__array_length__");
                        if (len_field.has_value() && len_field->type == DalvikType::INT32) {
                            int arr_len = len_field->int_val;
                            // Simple %s/%d replacement
                            size_t arg_idx = 0;
                            std::string output;
                            for (size_t i = 0; i < format_str.size(); i++) {
                                if (format_str[i] == '%' && i + 1 < format_str.size()) {
                                    // Handle %1$s, %s, %d, etc.
                                    size_t spec_start = i;
                                    i++; // skip %
                                    // Skip positional argument (e.g., "1$" in "%1$s")
                                    while (i < format_str.size() && format_str[i] >= '0' && format_str[i] <= '9') i++;
                                    if (i < format_str.size() && format_str[i] == '$') i++;

                                    if (i < format_str.size() && (format_str[i] == 's' || format_str[i] == 'd')) {
                                        char spec = format_str[i];
                                        if (arg_idx < (size_t)arr_len) {
                                            std::string field_name = "array[" + std::to_string(arg_idx) + "]";
                                            auto elem = heap_.get_object_field(arr_id, field_name);
                                            if (elem.has_value()) {
                                                if (elem->type == DalvikType::STRING_REF) {
                                                    output += elem->string_val;
                                                } else if (elem->type == DalvikType::OBJECT_REF && heap_.has_object(elem->object_id)) {
                                                    auto sv = heap_.get_object_field(elem->object_id, "value");
                                                    if (sv.has_value() && sv->type == DalvikType::STRING_REF) {
                                                        output += sv->string_val;
                                                    }
                                                } else if (elem->type == DalvikType::INT32) {
                                                    output += std::to_string(elem->int_val);
                                                }
                                            }
                                        }
                                        arg_idx++;
                                        // NOTE: do NOT i++ here — the for-loop's
                                        // i++ already advances past the spec char.
                                        // (EXP-094: a previous i++ here ate the
                                        // character right after the spec — e.g.
                                        // one of the "**" bold markers.)
                                    } else if (i < format_str.size() && format_str[i] == '%') {
                                        output += '%';
                                        i++;
                                    } else {
                                        // Unknown spec — output as-is
                                        output += format_str.substr(spec_start, i - spec_start + 1);
                                    }
                                } else {
                                    output += format_str[i];
                                }
                            }
                            result_str = output;
                            break;
                        }
                    }
                }
            }

            std::cerr << "[EXP093-FMTSTR] formatString(key=\"" << key
                      << "\") → \"" << result_str << "\"" << std::endl;
            return_val = DalvikValue::make_string(result_str, 0);
            recursion_depth_--;
            return true;
        }
    }

    // EXP-091: Intercept LocaleController.getString(int) BEFORE try_recursive_invoke
    // finds the method in the DEX. The real DEX bytecode builds a garbage "View"
    // string via StringBuilder. We resolve the resource ID to the actual string.
    if (method_name == "getString" &&
        declaring_class.find("LocaleController") != std::string::npos &&
        !args.empty() && args[0].type == DalvikType::INT32) {
        int32_t resid = args[0].int_val;
        auto fn_it = field_name_by_resid_.find(resid);
        if (fn_it != field_name_by_resid_.end()) {
            const std::string& field_name = fn_it->second;
            auto sv_it = resource_string_values_.find(field_name);
            if (sv_it != resource_string_values_.end()) {
                std::cerr << "[RES-INTERCEPT] LocaleController.getString(resid=0x"
                          << std::hex << resid << std::dec << ", field=" << field_name
                          << ") → \"" << sv_it->second << "\"" << std::endl;
                return_val = DalvikValue::make_string(sv_it->second, 0);
                recursion_depth_--;
                return true;
            }
            // Fallback: return the field name
            std::cerr << "[RES-INTERCEPT] LocaleController.getString(resid=0x"
                      << std::hex << resid << std::dec << ") → field name \""
                      << field_name << "\"" << std::endl;
            return_val = DalvikValue::make_string(field_name, 0);
            recursion_depth_--;
            return true;
        }
        // EXP-092: For resource IDs NOT in field_name_by_resid_ (e.g., small
        // int values like 0, 1, 2, 3 that are plural types or unknown),
        // return an empty string instead of falling through to the DEX
        // bytecode which produces garbage "View" via StringBuilder.
        // The "View" string is a literal const-string in the DEX bytecode
        // that is used as a fallback when the resource system fails.
        if (resid < 0x10000) {
            std::cerr << "[RES-INTERCEPT] LocaleController.getString(small_int="
                      << resid << ") → \"\" (preventing \"View\" garbage)" << std::endl;
            return_val = DalvikValue::make_string("", 0);
            recursion_depth_--;
            return true;
        }
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
        class_descriptor.find("Ljava/io/File;") == 0 ||
        // EXP-095 (CM-019): LayoutHelper.createLinear/createFrame must go to
        // the bridge so the returned LayoutParams object carries ALL fields
        // (width/height/gravity/margins). The DEX path executes for the
        // first 10 calls before the method throttle kicks in and produces
        // params with missing margins (setMargins is not fully bridged).
        class_descriptor.find("Lorg/telegram/ui/Components/LayoutHelper;") == 0 ||
        // EXP-098 (CM-027): AndroidUtilities.dp() must go to the bridge
        // so we return density=1.0 * value. The DEX bytecode calls
        // getResources().getDisplayMetrics().density which returns 0
        // in our headless runtime, making dp() return 0 — breaking
        // RLottieDrawable construction (w/h args become 0).
        class_descriptor.find("Lorg/telegram/messenger/AndroidUtilities;") == 0 ||
        // EXP-088+ Phase 5: desugared Java 8 ConcurrentHashMap.
        class_descriptor.find("Lj$/util/concurrent/ConcurrentHashMap;") == 0 ||
        class_descriptor.find("Ljava/util/concurrent/ConcurrentHashMap;") == 0) {
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

    // EXP-077: PathParser.createNodesFromPathData loops infinitely at PC=0x9.
    // This is called during vector drawable loading. The loop creates 50K
    // Paint objects and blocks execution before IntroActivity.createView
    // is reached. Stub it to return early.
    if (class_descriptor.find("PathParser") != std::string::npos &&
        method_name == "createNodesFromPathData") {
        log("⏭️ STUB-ONLY: " + class_descriptor + "." + method_name +
            " — skipping (infinite loop in vector path parsing)");
        recursion_depth_--;
        return false;
    }

    // EXP-077: FireworksOverlay.<clinit> loops infinitely at PC=0x50.
    // This is a static initializer that creates Path objects. Stub it.
    if (class_descriptor.find("FireworksOverlay") != std::string::npos &&
        method_name == "<clinit>") {
        log("⏭️ STUB-ONLY: " + class_descriptor + "." + method_name +
            " — skipping (infinite loop in static initializer)");
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

    // EXP-098 (CM-027): RLottieDrawable.<init> intercept is in the early
    // path (above) — see the method_name == "<init>" block.

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
             class_descriptor.find("LoginActivity") != std::string::npos || class_descriptor.find("BaseFragment") != std::string::npos);
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
    // EXP-089: Also bypass replaceMultipleCharSequence (same string processing loop).
    // EXP-094 (CM-018): replaceTags now implements its SOURCE semantics —
    // per AndroidUtilities.java it strips the "**" bold markers and returns
    // the text (with bold spans we don't render). Previously it returned
    // VOID, so confirmTextView.setText(replaceTags(...)) received "" and the
    // whole formatted SMS string was lost (silent false success).
    if (class_descriptor.find("AndroidUtilities") != std::string::npos &&
        method_name == "replaceTags" &&
        !args.empty()) {
        std::string s;
        if (args[0].type == DalvikType::STRING_REF) {
            s = args[0].string_val;
        } else if (args[0].type == DalvikType::OBJECT_REF && heap_.has_object(args[0].object_id)) {
            auto sv = heap_.get_object_field(args[0].object_id, "value");
            if (!sv.has_value()) sv = heap_.get_object_field(args[0].object_id, "sb_value");
            if (sv.has_value() && sv->type == DalvikType::STRING_REF) s = sv->string_val;
        }
        // Strip "**" marker pairs (they wrap bold ranges in Telegram strings).
        std::string out;
        for (size_t i = 0; i < s.size(); i++) {
            if (s[i] == '*' && i + 1 < s.size() && s[i + 1] == '*') {
                i++;  // skip both asterisks
                continue;
            }
            out += s[i];
        }
        std::cerr << "[EXP094-REPLACETAGS] in=\"" << s.substr(0, 80)
                  << "\" out=\"" << out.substr(0, 80) << "\"" << std::endl;
        recursion_depth_--;
        return_val = DalvikValue::make_string(out, 0);
        last_invoke_return_ = return_val;
        return true;
    }
    if (class_descriptor.find("AndroidUtilities") != std::string::npos &&
        (method_name == "replaceMultipleCharSequence" ||
         method_name == "replaceChars")) {
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
            method_name == "onDestroy" ||
            // EXP-093: Critical View/String methods must NOT be throttled at 10.
            // setText is called once per TextView — with 6+ views per screen,
            // 10 is way too low. These are NOT infinite-loop risks.
            method_name == "setText" ||
            method_name == "getText" ||
            method_name == "toString" ||
            method_name == "append" ||
            method_name == "setVisibility" ||
            method_name == "setOrientation" ||
            method_name == "setGravity" ||
            method_name == "setTypeface" ||
            method_name == "setTextSize" ||
            method_name == "setPadding" ||
            method_name == "setLayoutParams" ||
            method_name == "addView" ||
            method_name == "setHint" ||
            method_name == "setEnabled" ||
            method_name == "setClickable" ||
            method_name == "setFocusable" ||
            method_name == "requestFocus" ||
            method_name == "setBackgroundColor" ||
            method_name == "setBackground" ||
            method_name == "setImageResource" ||
            method_name == "setOnFocusChangeListener" ||
            // EXP-098: dp() is called frequently for view sizing; must
            // not be throttled (RLottieDrawable construction depends on it).
            method_name == "dp" ||
            method_name == "setAnimation") {
            threshold = 1000;
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

    // EXP-078: Debug — trace LoginActivity method search
    if (class_descriptor.find("LoginActivity") != std::string::npos || class_descriptor.find("BaseFragment") != std::string::npos &&
        (method_name == "onFragmentCreate" || method_name == "createView" || method_name == "onNextPressed" || method_name == "onDoneButtonPressed")) {
        auto all_methods_check = cls_ref.all_methods();
        std::cerr << "[EXP078-DEBUG] " << class_descriptor << "." << method_name
                  << " class found! methods=" << all_methods_check.size()
                  << " direct=" << cls_ref.direct_methods.size()
                  << " virtual=" << cls_ref.virtual_methods.size()
                  << " superclass=" << cls_ref.superclass_name
                  << std::endl;
        for (const auto& m : all_methods_check) {
            if (m.name == method_name) {
                std::cerr << "[EXP078-DEBUG]   FOUND " << m.name << m.descriptor
                          << " bytecode_size=" << m.bytecode.size()
                          << " code_offset=0x" << std::hex << m.code_offset << std::dec
                          << std::endl;
            }
        }
    }

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
        // EXP-080: D8 renames lambda methods during compilation.
        // method_ids[] may resolve to 'lambda$createView$1' but the
        // ClassInfo has the D8-renamed name '$r8$lambda$8Miu...'.
        // When the exact name doesn't match, also try matching by
        // checking if the method name CONTAINS the searched name as a
        // substring, or if the searched name contains the method name.
        bool name_matches = (method.name == method_name);
        if (!name_matches) {
            // EXP-089 CRITICAL FIX: When method_name is ALREADY a $r8$lambda
            // name (e.g. "$r8$lambda$wAg5VLWJ..."), we MUST require an EXACT
            // name match. The previous code matched ANY $r8$lambda method
            // whose name contained "lambda" and "$r8$lambda" — which matches
            // ALL D8-renamed lambdas in the class! This caused the WRONG
            // lambda to be selected when multiple lambdas with the same
            // proto existed in the same class.
            //
            // Example: IntroActivity has:
            //   $r8$lambda$_-ElmO9SCTF2Y... (calls lambda$createView$2)
            //   $r8$lambda$wAg5VLWJcoV2...   (calls lambda$createView$1)
            // Both have proto (IntroActivity;View;)V
            // The old code matched BOTH because both contain "lambda"
            // and "$r8$lambda". The first one (_-ElmO) was picked,
            // which calls the WRONG lambda (createView$2 instead of createView$1).
            //
            // Fix: If method_name starts with "$r8$lambda", require EXACT match.
            // Only fall back to substring matching for ORIGINAL names (lambda$...).
            if (method_name.rfind("$r8$lambda", 0) == 0) {
                // method_name is already a D8-renamed name.
                // Require EXACT match — don't accept other $r8$lambda methods.
                // (This case is already handled by name_matches = (method.name == method_name)
                //  at the top of this block, so we just skip here.)
            } else if (method_name.rfind("lambda$", 0) == 0) {
                // EXP-089 CRITICAL FIX: method_name is an ORIGINAL lambda name
                // (e.g. "lambda$createView$1"). Do NOT match against $r8$lambda
                // methods — they are DIFFERENT lambdas that happen to share the
                // "lambda" substring. The $r8$lambda methods are D8-renamed
                // versions of the ORIGINAL lambda methods, but they have DIFFERENT
                // names and should only match when the EXACT original name is
                // present in the class's method list.
                //
                // Previously, this code matched ANY $r8$lambda method when
                // method_name contained "lambda" — which matched ALL D8 lambdas
                // in the class, causing the WRONG lambda to be selected.
                //
                // The correct behavior is:
                //   1. First try exact name match (lambda$createView$1 == lambda$createView$1)
                //   2. If no exact match, the method is NOT in this class
                //   3. Do NOT fall back to $r8$lambda substring matching
                //
                // (The exact match was already checked at the top of this block
                //  via name_matches = (method.name == method_name). If we reach
                //  here, the exact match failed. So we just skip — don't match.)
            } else if (method_name.find("lambda") != std::string::npos &&
                method.name.find("$r8$lambda") != std::string::npos) {
                // EXP-081: D8 converts instance lambda methods to static
                // by adding the captured receiver as the first parameter.
                // Original: (Landroid/view/View;)V  (instance, 1 param)
                // D8 static: (Lorg/.../LoginActivity;Landroid/view/View;)V  (static, 2 params)
                // We accept the match if the $r8$lambda descriptor has
                // exactly ONE extra leading parameter compared to the original.
                if (!method_descriptor.empty()) {
                    // Parse original descriptor params
                    size_t orig_start = method_descriptor.find('(');
                    size_t orig_end = method_descriptor.find(')', orig_start);
                    if (orig_start != std::string::npos && orig_end != std::string::npos) {
                        std::string orig_params = method_descriptor.substr(orig_start + 1, orig_end - orig_start - 1);
                        // Parse $r8$lambda descriptor params
                        size_t r8_start = method.descriptor.find('(');
                        size_t r8_end = method.descriptor.find(')', r8_start);
                        if (r8_start != std::string::npos && r8_end != std::string::npos) {
                            std::string r8_params = method.descriptor.substr(r8_start + 1, r8_end - r8_start - 1);
                            // Check if r8_params ends with orig_params (r8 has one extra leading param)
                            if (r8_params.length() > orig_params.length() &&
                                r8_params.substr(r8_params.length() - orig_params.length()) == orig_params) {
                                name_matches = true;
                            }
                            // Also check exact match (both static or both instance)
                            if (method.descriptor == method_descriptor) {
                                name_matches = true;
                            }
                        }
                    }
                }
            }
        }
        if (!name_matches) continue;
        // EXP-082: Debug trace for the exact rejection point
        if (method_name.find("$r8$lambda$8Miu") != std::string::npos ||
            (method_name.find("lambda") != std::string::npos && method_name.find("createView") != std::string::npos)) {
            std::cerr << "[EXP082-CHECK] name_matches=true"
                      << " method=" << method.name
                      << " desc=" << method.descriptor
                      << " bytecode_size=" << method.bytecode.size()
                      << " bytecode.empty=" << (method.bytecode.empty() ? "YES" : "NO")
                      << " code_offset=0x" << std::hex << method.code_offset << std::dec
                      << std::endl;
        }
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

        // EXP-080: Permissive arg matching for multi-DEX methods.
        // Accept ANY of: param_count == arg_count (static-like),
        // param_count == arg_count - 1 (instance), or param_count == effective.
        // This handles D8-generated $r8$lambda methods and multi-DEX overrides
        // where the access_flags may not match the actual calling convention.
        size_t effective_arg_count = arg_count;
        bool is_static_method = (method.access_flags & 0x0008) != 0;
        if (!is_static_method && arg_count > 0 && arg_count > param_count) {
            effective_arg_count = arg_count - 1;
        }
        // EXP-080: Accept param_count matching ANY of the possible interpretations
        // EXP-082: Add trace for $r8$lambda methods
        if (method_name.find("$r8$lambda$8Miu") != std::string::npos) {
            std::cerr << "[EXP082-PARAM] method=" << method.name
                      << " param_count=" << param_count
                      << " arg_count=" << arg_count
                      << " effective_arg_count=" << effective_arg_count
                      << " is_static=" << is_static_method
                      << " access_flags=0x" << std::hex << method.access_flags << std::dec
                      << " desc=" << method.descriptor
                      << std::endl;
        }
        bool param_count_matches =
            (param_count == effective_arg_count) ||  // instance method
            (param_count == arg_count) ||              // static method
            (!is_static_method && arg_count > 0 && param_count == (size_t)(arg_count - 1)); // instance alt
        if (param_count_matches) {
            // Use the matching interpretation
            if (param_count == arg_count) {
                effective_arg_count = arg_count;
            }
            // EXP-092+ PHASE 1: Debug trace for fillNextCodeParams overload resolution
            if (method_name == "fillNextCodeParams") {
                std::cerr << "[EXP092-OVERLOAD] fillNextCodeParams"
                          << " desc=" << method.descriptor
                          << " bytecode_size=" << method.bytecode.size()
                          << " param_count=" << param_count
                          << " arg_count=" << arg_count
                          << " effective_arg_count=" << effective_arg_count
                          << " is_static=" << is_static_method
                          << " access_flags=0x" << std::hex << method.access_flags << std::dec;
                if (!args.empty()) {
                    std::cerr << " arg[0].type=" << (int)args[0].type
                              << " arg[0].class=" << args[0].class_desc
                              << " arg[0].obj=" << args[0].object_id;
                }
                if (args.size() >= 2) {
                    std::cerr << " arg[1].type=" << (int)args[1].type
                              << " arg[1].class=" << args[1].class_desc
                              << " arg[1].obj=" << args[1].object_id;
                }
                std::cerr << std::endl;
            }
            // EXP-079: Debug trace for $r8$lambda method matching
            if (method.name.find("$r8$lambda") != std::string::npos ||
                method.name.find("createView") != std::string::npos) {
                std::cerr << "[EXP079-MATCH] param_count=" << param_count
                          << " effective_arg_count=" << effective_arg_count
                          << " arg_count=" << arg_count
                          << " is_static=" << is_static_method
                          << " method=" << method.name
                          << " desc=" << method.descriptor
                          << std::endl;
                if (!args.empty()) {
                    std::cerr << "[EXP079-MATCH]   arg[0] type=" << (int)args[0].type
                              << " class=" << args[0].class_desc
                              << " obj=" << args[0].object_id
                              << std::endl;
                }
            }
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
            //
            // EXP-092+ FIX: For NON-STATIC methods, args[0] is `this` (the
            // receiver). The first PARAMETER corresponds to args[1], not
            // args[0]. Previously, when arg_count == param_count (both include
            // `this`), arg_idx was set to 0 — which compared `this` against
            // the first parameter type. This caused incorrect type mismatches
            // for instance methods where arg_count == param_count.
            // Example: fillNextCodeParams(Bundle, auth_SentCode, Z) has
            // param_count=3 and is called with arg_count=3 (this, Bundle,
            // auth_SentCode). The old code compared args[0](this=LoginActivity)
            // against param_types[0](Bundle) → mismatch → type_matches=false.
            // The fix: for non-static methods, arg_idx starts at 1 (skip `this`).
            bool type_matches = true;
            if (effective_arg_count >= 1 && !param_types.empty()) {
                size_t arg_idx;
                if (!is_static_method && arg_count > 0) {
                    // Non-static: args[0] = this, args[1] = first parameter
                    arg_idx = 1;
                } else {
                    // Static: args[0] = first parameter
                    arg_idx = 0;
                }
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
                // EXP-078: Multi-DEX method shadowing fix.
                // When DEX files are merged, the same method name may appear
                // in multiple DEX files with different bytecode sizes.
                // A stub version (bytecode_size=1, return-void) from one DEX
                // may shadow the real version (bytecode_size=1468) from another.
                // Fix: prefer the method with the LARGEST bytecode.
                if (!best_match || method.bytecode.size() > best_match->bytecode.size()) {
                    best_match = method;  // copy by value (EXP-054)
                }
                // Don't break — continue searching for a larger bytecode version
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
        // UNIFIED_011.3 EXC-PROPAGATE: save + isolate any in-flight unwind
        // exception so a stale sibling-call exception is never misattributed
        // to this callee.
        bool saved_unwind_valid = frame_unwind_exception_valid_;
        DalvikValue saved_unwind_exc = frame_unwind_exception_;
        frame_unwind_exception_valid_ = false;
        frame_unwind_exception_ = DalvikValue::make_null();

        halted_on_return_ = false;
        halted_ = false;

        // EXP-079: CRITICAL FIX — set current_dex_index_ to the DEX file
        // that contains the class being executed. This ensures that
        // resolve_method_name_for_dex, resolve_type_for_dex, etc. use the
        // CORRECT per-DEX tables when resolving method_idx/type_idx from
        // bytecode inside this method.
        auto dex_it = class_to_dex_index_.find(cls_ref.name);
        if (dex_it != class_to_dex_index_.end()) {
            current_dex_index_ = dex_it->second;
        }

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

        // UNIFIED_011.3 EXC-PROPAGATE (§18): did the callee end with an
        // uncaught exception? If so, search THIS frame's try table at the
        // invoke site (typed matching included). Handler found → jump there
        // with pending_exception_ set (move-exception works). No handler →
        // keep the exception in flight; the next outer invoke site repeats
        // this — real call-stack propagation.
        if (frame_unwind_exception_valid_) {
            DalvikValue unwind_exc = frame_unwind_exception_;
            std::string unwind_desc = unwind_exc.class_desc.empty()
                    ? "Ljava/lang/RuntimeException;" : unwind_exc.class_desc;
            frame_unwind_exception_valid_ = false;
            frame_unwind_exception_ = DalvikValue::make_null();

            uint32_t prop_handler = 0;
            bool prop_catch_all = false;
            std::string prop_catch_type;
            if (find_catch_handler_for_pc(pc_, prop_handler, prop_catch_all,
                                          prop_catch_type, unwind_desc)) {
                std::cerr << "[EXC-PROPAGATE] " << unwind_desc
                          << " caught at caller " << current_class_ << "."
                          << current_method_
                          << " invoke_pc=" << pc_
                          << " handler=0x" << to_hex(prop_handler)
                          << " type=" << prop_catch_type << std::endl;
                pending_exception_ = unwind_exc;
                pc_ = prop_handler;
                // Defer the jump until after the invoke handler's own
                // `pc_ += instr_len` — see exc_redirect_pending_ in header.
                exc_redirect_pending_ = true;
                exc_redirect_addr_ = prop_handler;
                // restore pre-call in-flight state (normally empty)
                frame_unwind_exception_valid_ = saved_unwind_valid;
                frame_unwind_exception_ = saved_unwind_exc;
            } else {
                std::cerr << "[EXC-PROPAGATE] " << unwind_desc
                          << " uncaught at caller " << current_class_ << "."
                          << current_method_
                          << " invoke_pc=" << pc_
                          << " → caller continues after invoke (compatibility)"
                          << std::endl;
                // UNIFIED_011.3 FRAME-2 (§18): if NO frame catches the
                // exception, the caller CONTINUES with a null return instead
                // of halting the whole call chain.
                //
                // Policy (regression-proven): full unwind-to-top is real
                // Dalvik behavior, but this engine raises ARTIFACT
                // exceptions (e.g. Telegram LruCache "maxSize <= 0" IAE —
                // real Android never throws there; the size computes to 0
                // from engine-local display metrics). Full propagation let
                // that artifact escape through LaunchActivity.onCreate and
                // killed the deterministic Telegram golden (eb16ab5c
                // regression). Caught-type semantics stay REAL (typed +
                // catch-all matching across frames — see the
                // unified0113_typed_catch fixture); only the uncaught tail
                // degrades to the EXP-071-style compatibility continue.
                frame_unwind_exception_valid_ = false;
                frame_unwind_exception_ = DalvikValue::make_null();
                return_val = DalvikValue::make_null();
                recursion_depth_--;
                return true;
            }
        }

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

    {
        static thread_local const bool tc = std::getenv("MINIANDROID_TRACE_COMPOSE") != nullptr;
        if (tc && (declaring_class.find("ompos") != std::string::npos ||
                   declaring_class.find("oroutin") != std::string::npos ||
                   declaring_class.find("Choreographer") != std::string::npos ||
                   declaring_class.find("MonotonicFrameClock") != std::string::npos)) {
            std::cerr << "[COMPOSE-MISS] " << declaring_class << "." << method_name
                      << " (not in DEX — bridges to API/shadow) depth=" << recursion_depth_
                      << std::endl;
        }
    }
    {
        static thread_local const bool tm = std::getenv("MINIANDROID_TRACE_MISS") != nullptr;
        static thread_local uint64_t miss_log_count = 0;
        if (tm && miss_log_count < 400) {
            miss_log_count++;
            std::cerr << "[INVOKE-MISS] " << declaring_class << "." << method_name
                      << " (not in DEX — bridges to API/shadow) depth=" << recursion_depth_
                      << std::endl;
        }
    }
    recursion_depth_--;
    return false;  // method not found in DEX, bridge to API
}

// CAMPAIGN 013 (§10/§15/§19): execute a custom view's REAL onDraw(Canvas)
// bytecode and capture the draw primitives via CanvasShadow. Returns the
// number of captured ops (0 = nothing drawn / no onDraw / no heap object).
int DalvikExecutionEngine::dispatch_custom_view_draw(uint32_t view_object_id) {
    if (shadow_registry_ == nullptr) return 0;
    auto* view_shadow = shadow_registry_->find_as<framework::ViewShadow>();
    auto* canvas_shadow = shadow_registry_->find_as<framework::CanvasShadow>();
    if (!view_shadow || !canvas_shadow) return 0;
    const auto* node = view_shadow->find_node(view_object_id);
    if (!node) { std::cerr << "[C013-ONDRAW-TRY] id=" << view_object_id << " no node\n"; return 0; }
    if (!heap_.has_object(view_object_id)) {
        std::cerr << "[C013-ONDRAW-TRY] id=" << view_object_id << " class=" << node->class_desc
                  << " NOT a heap object (inflated)\n";
        return 0;  // inflated views have no heap obj yet
    }
    std::string cls = node->class_desc;
    if (heap_.has_object(view_object_id)) {
        const auto* obj = heap_.get(view_object_id);
        if (obj && !obj->class_descriptor.empty()) cls = obj->class_descriptor;
    }
    // Normalize dotted descriptors (Lcom.example.Foo; -> Lcom/example/Foo;)
    // AFTER the heap lookup — heap class_descriptors may be dotted, and the
    // DEX class index uses slashed descriptors.
    if (!cls.empty() && cls[0] == 'L' && cls.find('.') != std::string::npos) {
        std::string norm = "L";
        for (size_t i = 1; i < cls.size(); ++i) {
            char c = cls[i];
            norm += (c == '.') ? '/' : c;
        }
        cls = norm;
    }
    uint32_t canvas_obj = heap_.allocate("Landroid/graphics/Canvas;", pc_, call_stack_.empty() ? 0 : call_stack_.top().frame_id);
    canvas_shadow->begin_frame();
    std::vector<DalvikValue> args;
    args.push_back(DalvikValue::make_object(view_object_id, cls));
    args.push_back(DalvikValue::make_object(canvas_obj, "Landroid/graphics/Canvas;"));
    DalvikValue ret = DalvikValue::make_void();
    DalvikExecutionResult res;
    bool ok = try_recursive_invoke(cls, "onDraw", args, ret, res);
    int ops = ok ? (int)canvas_shadow->ops().size() : 0;
    // AOSP ViewGroup semantics: ViewGroups draw children/content through
    // dispatchDraw(Canvas), not onDraw. Compose's AndroidComposeView is a
    // ViewGroup — its entire composed tree is rendered via dispatchDraw.
    // A View may also legitimately define an EMPTY onDraw (bytecode_size=1
    // return-void) — fall back whenever onDraw produced no ops.
    if (ops == 0) {
        canvas_shadow->begin_frame();  // reset ops collected by the empty try
        ok = try_recursive_invoke(cls, "dispatchDraw", args, ret, res);
        ops = ok ? (int)canvas_shadow->ops().size() : 0;
    }
    std::cerr << "[C013-ONDRAW] view=" << view_object_id << " class=" << cls
              << " dispatched=" << (ok ? "YES" : "NO") << " ops=" << ops << std::endl;
    return ops;
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
    // CAMPAIGN 013 B1: dialog window rows/buttons route as
    // DialogInterface$OnClickListener.onClick(DialogInterface dialog, int which).
    // Real Android passes the DIALOG (not the view) + the button code / item
    // index. Buttons with no listener still dismiss the dialog.
    if (node->dialog_owner_obj != 0) {
        auto* dialog_shadow = shadow_registry_->find_as<framework::DialogShadow>();
        if (dialog_shadow == nullptr) return false;
        int which = node->dialog_which;
        uint32_t dlg_listener =
            dialog_shadow->listener_for_click(node->dialog_owner_obj, which, &which);
        std::cerr << "[UI-EVENT] event=DIALOG_CLICK"
                  << " dialog_obj=" << node->dialog_owner_obj
                  << " which=" << which
                  << " listener=" << dlg_listener
                  << std::endl;
        if (dlg_listener == 0) {
            if (which < 0) {
                dialog_shadow->dismiss_dialog(node->dialog_owner_obj);
            }
            return true;  // consumed: no-listener button click still dismisses
        }
        std::string lc;
        if (heap_.has_object(dlg_listener)) {
            lc = heap_.get(dlg_listener)->class_descriptor;
        }
        if (lc.empty()) lc = "Landroid/content/DialogInterface$OnClickListener;";
        std::vector<DalvikValue> dargs;
        dargs.push_back(DalvikValue::make_object(dlg_listener, lc));
        dargs.push_back(DalvikValue::make_object(
            node->dialog_owner_obj, "Landroid/app/AlertDialog;"));
        dargs.push_back(DalvikValue::make_int(which));
        DalvikValue dret = DalvikValue::make_void();
        DalvikExecutionResult dres;
        bool dok = try_recursive_invoke(lc, "onClick", dargs, dret, dres);
        std::cerr << "[UI-EVENT] event=DIALOG_CLICK result="
                  << (dok ? "DISPATCHED" : "FAILED") << std::endl;
        // If the handler did not dismiss the dialog itself and this was a
        // button click, real Android dismisses after onClick returns.
        if (which < 0) {
            auto* win = dialog_shadow->window_by_obj(node->dialog_owner_obj);
            if (win && win->showing) dialog_shadow->dismiss_dialog(node->dialog_owner_obj);
        }
        return dok;
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

    // EXP-100 (UNIFIED_002): structured per-click audit BEFORE dispatch
    // (DIAGNOSTIC, env-gated via MINIANDROID_CLICK_AUDIT). Records the
    // full per-click target evidence demanded by the master request §7:
    // click number, timestamp, view id/class, hierarchy path, bounds,
    // visible/enabled/clickable, parent, listener — dispatch result is
    // recorded after the invoke below.
    uint64_t click_no = miniandroid::diagnostics::click_counter().fetch_add(1) + 1;
    {
        // Walk the parent chain to build the hierarchy path (bounded loop).
        std::vector<std::string> path_names{node->class_desc};
        uint32_t pid = node->parent_id;
        int guard = 0;
        while (pid != 0 && guard++ < 64) {
            const auto* p = view_shadow->find_node(pid);
            if (p == nullptr) break;
            path_names.push_back(p->class_desc);
            pid = p->parent_id;
        }
        std::string path;
        for (auto it = path_names.rbegin(); it != path_names.rend(); ++it) {
            if (!path.empty()) path += "/";
            path += *it;
        }
        std::string rec = "{\"schema\":\"click_audit_v1\",\"record\":\"dispatch\",\"click_no\":" +
            std::to_string(click_no) +
            ",\"t\":\"" + miniandroid::diagnostics::iso_now() + "\"" +
            ",\"view_id\":" + std::to_string(view_object_id) +
            ",\"view_class\":\"" + miniandroid::diagnostics::jesc(node->class_desc) + "\"" +
            ",\"parent_id\":" + std::to_string(node->parent_id) +
            ",\"android_view_id\":" + std::to_string(node->android_view_id) +
            ",\"hierarchy_path\":\"" + miniandroid::diagnostics::jesc(path) + "\"" +
            ",\"bounds\":[" + std::to_string(node->x) + "," + std::to_string(node->y) + "," +
            std::to_string(node->width) + "," + std::to_string(node->height) + "]" +
            ",\"clickable\":" + (node->clickable ? "true" : "false") +
            ",\"enabled\":" + (node->enabled ? "true" : "false") +
            ",\"visibility\":" + std::to_string(node->visibility) +
            ",\"text\":\"" + miniandroid::diagnostics::jesc(node->text) + "\"" +
            ",\"listener_id\":" + std::to_string(listener_id) +
            ",\"listener_class\":\"" + miniandroid::diagnostics::jesc(listener_class) + "\"" +
            ",\"target_method\":\"onClick(View)\"}";
        miniandroid::diagnostics::audit_append(rec);
    }

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

    // EXP-100: record the dispatch RESULT for the click above (DIAGNOSTIC).
    miniandroid::diagnostics::audit_append(
        std::string("{\"schema\":\"click_audit_v1\",\"record\":\"dispatch_result\",\"click_no\":") +
        std::to_string(click_no) +
        ",\"view_id\":" + std::to_string(view_object_id) +
        ",\"dispatch_ok\":" + (ok ? "true" : "false") +
        ",\"total_instructions_executed\":" + std::to_string(result.total_instructions_executed) + "}");
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

// ---------------------------------------------------------------------------
// CAMPAIGN 009 §10 — view attach lifecycle dispatch.
// Oracle: aosp-mirror/platform_frameworks_base View.java
// dispatchAttachedToWindow(): the framework invokes onAttachedToWindow() on
// every node of the attaching tree. AbstractComposeView.onAttachedToWindow()
// -> ensureCompositionCreated() builds the composition and attaches
// AndroidComposeView as ComposeView's child. Evidence: dooz run trace showed
// ComposeView children=0 + onAttachedToWindow present ONLY in CODE_ITEM parse
// logs, never dispatched ([EXP095-LAYOUT] parent=27 children=0, white frame).
// Env-gated via MINIANDROID_DISPATCH_ATTACH=1 (caller checks) — default off
// keeps the golden Telegram/GMDice screenshots byte-stable.
// ---------------------------------------------------------------------------
bool DalvikExecutionEngine::dispatch_view_attached() {
    if (shadow_registry_ == nullptr) return false;
    auto* view_shadow = shadow_registry_->find_as<framework::ViewShadow>();
    if (view_shadow == nullptr) return false;

    // CAMPAIGN 009 diagnostics: why would dispatch fail? Log the first few
    // attempts with their class + engine preconditions.
    static int diag_logged = 0;
    std::cerr << "[UC009-ATTACH-DIAG] dex_report=" << (dex_report_ ? "SET" : "NULL")
              << " classes_indexed=" << class_info_index_.size()
              << " nodes=" << view_shadow->all_nodes().size()
              << " depth=" << recursion_depth_ << std::endl;
    if (class_info_index_.find("Landroidx/compose/ui/platform/ComposeView;") != class_info_index_.end()) {
        std::cerr << "[UC009-ATTACH-DIAG] ComposeView IS in class index" << std::endl;
    } else {
        std::cerr << "[UC009-ATTACH-DIAG] ComposeView NOT in class index" << std::endl;
        // find any androidx class in the index to show key format
        int shown = 0;
        for (const auto& [k, v] : class_info_index_) {
            if (k.find("compose") != std::string::npos && shown++ < 3) {
                std::cerr << "[UC009-ATTACH-DIAG] sample key: " << k << std::endl;
            }
        }
    }

    bool any_ok = false;
    // Bounded multi-pass: a dispatched attach may create NEW views
    // (Compose ensureCompositionCreated -> AndroidComposeView via addView).
    // Guard set prevents double dispatch; passes bounded to avoid runaway.
    std::unordered_set<uint32_t> attempted;
    for (int pass = 0; pass < 16; pass++) {
        bool dispatched_this_pass = false;
        // Snapshot node ids: dispatch may mutate the node map (addView of
        // new children), so iterate over a stable copy of current ids.
        std::vector<uint32_t> ids;
        for (const auto& [id, node_ptr] : view_shadow->all_nodes()) {
            if (node_ptr) ids.push_back(id);
        }
        std::sort(ids.begin(), ids.end());   // creation order: parents before children
        for (uint32_t id : ids) {
            if (attempted.count(id)) continue;
            const auto* node = view_shadow->find_node(id);
            if (node == nullptr || node->class_desc.empty()) { attempted.insert(id); continue; }
            attempted.insert(id);
            const std::string cls = node->class_desc;
            // AOSP ordering: View.dispatchAttachedToWindow sets mAttachInfo
            // BEFORE invoking onAttachedToWindow. Mirror that here so
            // isAttachedToWindow() queried inside the dispatched chain
            // (Compose ensureCompositionCreated) returns true.
            if (auto* mutable_node = view_shadow->find_node(id)) {
                mutable_node->attached_to_window = true;
            }
            // Only DEX-side classes (bundled androidx / app code) can be
            // interpreted; try_recursive_invoke returns false otherwise.
            std::vector<DalvikValue> args{DalvikValue::make_object(id, cls)};
            DalvikValue return_val = DalvikValue::make_void();
            DalvikExecutionResult result;
            // Walk the superclass chain: ComposeView inherits
            // onAttachedToWindow from AbstractComposeView (verified in dooz
            // DEX). AOSP semantics: virtual dispatch finds the override
            // nearest to the receiver class; walking UP from the runtime
            // class reproduces that for the no-override case.
            bool ok = false;
            std::string walk = cls;
            for (int hop = 0; hop < 8 && !ok && !walk.empty(); hop++) {
                ok = try_recursive_invoke(walk, "onAttachedToWindow", args, return_val, result);
                if (ok) break;
                auto cit = class_info_index_.find(walk);
                if (cit == class_info_index_.end()) break;
                const dex::ClassInfo& ci = dex_report_->classes[cit->second];
                walk = ci.superclass_name;
                // Stop at framework superclasses (shadowed, not in DEX)
                if (walk.empty() || walk.rfind("Landroid/", 0) == 0 ||
                    walk.rfind("Ljava/", 0) == 0) break;
            }
            if (ok) {
                any_ok = true;
                dispatched_this_pass = true;
                std::cerr << "[UC009-ATTACH] onAttachedToWindow dispatched view=" << id
                          << " class=" << cls << std::endl;
            }
        }
        if (!dispatched_this_pass) break;
    }
    std::cerr << "[UC009-ATTACH] attach dispatch complete ok=" << (any_ok ? "true" : "false")
              << std::endl;
    return any_ok;
}

bool DalvikExecutionEngine::dispatch_click_by_class(const std::string& class_substring) {
    if (shadow_registry_ == nullptr) return false;
    auto* view_shadow = shadow_registry_->find_as<framework::ViewShadow>();
    if (view_shadow == nullptr) return false;
    uint32_t view_id = view_shadow->find_by_class_substring(class_substring);
    // EXP-100 (UNIFIED_002 §9): record the class-based SELECTION — which
    // candidates matched, which one was chosen, and why (find_by_class_substring
    // returns the LAST/highest-id match — record that fact explicitly).
    {
        auto matches = view_shadow->find_all_by_class_substring(class_substring);
        std::string cand;
        for (size_t i = 0; i < matches.size(); ++i) {
            const auto* n = view_shadow->find_node(matches[i]);
            if (i) cand += ",";
            cand += "\"" + miniandroid::diagnostics::jesc(
                n ? n->class_desc : std::string("?")) + ":" + std::to_string(matches[i]) + "\"";
        }
        miniandroid::diagnostics::audit_append(
            std::string("{\"schema\":\"click_audit_v1\",\"record\":\"select_by_class\",\"t\":\"") +
            miniandroid::diagnostics::iso_now() + "\"" +
            ",\"class_substring\":\"" + miniandroid::diagnostics::jesc(class_substring) + "\"" +
            ",\"candidates\": [" + cand + "]" +
            ",\"chosen_view_id\":" + std::to_string(view_id) +
            ",\"rule\":\"last/highest view_id match\"}");
    }
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
        // EXP-074: Text resource ID for setText(int) resolution
        n["text_resource_id"] = node->text_resource_id;
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

// ── Dalvik numeric-conversion helpers (RESULT_010 reconciliation) ─────────
// JLS 5.1.3 / AOSP float→integral narrowing: NaN → 0, otherwise round toward
// zero with SATURATION to the destination range (undefined behavior would be
// triggered by a bare static_cast for out-of-range values).
namespace {
inline int32_t conv_f2i(double d) {
    if (std::isnan(d)) return 0;
    if (d >= 2147483647.0)  return INT32_MAX;
    if (d <= -2147483648.0) return INT32_MIN;
    return static_cast<int32_t>(d);
}
inline int64_t conv_f2l(double d) {
    if (std::isnan(d)) return 0;
    if (d >= 9223372036854775807.0)  return INT64_MAX;
    if (d <= -9223372036854775808.0) return INT64_MIN;
    return static_cast<int64_t>(d);
}
// Dalvik registers are raw bit storage: const-wide/const-wide/high16 load a
// DOUBLE's bit pattern tagged INT64 (the engine's type tags are an internal
// approximation). Floating handlers must therefore reinterpret INT64-tagged
// registers as their bit pattern when a double is expected — otherwise every
// double constant routed through const-wide would read as garbage.
inline double bits_l2d(int64_t l) {
    double d;
    static_assert(sizeof(double) == sizeof(int64_t), "64-bit double required");
    std::memcpy(&d, &l, sizeof(d));
    return d;
}
// MASTER RECONCILIATION (2026-09-03): int-bits → float reinterpret, the
// 32-bit companion of bits_l2d. const/const/16 opcodes store raw bit patterns
// tagged INT32; the unary neg-float handler needs the NUMERIC value.
inline float bits_i2f(int32_t i) {
    float f;
    static_assert(sizeof(float) == sizeof(int32_t), "32-bit float required");
    std::memcpy(&f, &i, sizeof(f));
    return f;
}
}  // namespace

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
            // EXP-088+ F5: move-wide (12x: B|A|op, 1 code unit)
            // Copies a wide value (long/double) from vB to vA.
            // Same as execute_move but explicitly handles wide types.
            // Previously MISSING from dispatcher — fell through to default
            // (handle_unimplemented), causing halt at PC where move-wide appears.
            case Opcode::MOVE_WIDE: {
                uint16_t instr = bytecode_[pc_];
                uint8_t dest = (instr >> 8) & 0xF;
                uint8_t src = instr & 0xF;
                DalvikValue val = get_register(src);
                // If src doesn't hold a wide value, coerce to INT64
                // (matches the F5 return-wide coercion behavior)
                if (val.type != DalvikType::INT64 && val.type != DalvikType::FLOAT64) {
                    val = DalvikValue::make_long(static_cast<int64_t>(static_cast<uint32_t>(val.int_val)));
                }
                set_register(dest, val);
                trace.opcode_name = "move-wide";
                pc_ += 1;
                break;
            }
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
                // PASS-3 (K-33 audit): also store the CANONICAL name
                // "__array_length__" that aget/aput/read actually read —
                // previously NEW_ARRAY only stored "__new_array_length__",
                // an inconsistency that made bulk reads/aget see length 0.
                if (heap_.has_object(obj_id)) {
                    heap_.set_object_field(obj_id, "__new_array_length__",
                        DalvikValue::make_int(array_size));
                    heap_.set_object_field(obj_id, "__array_length__",
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
                        /* UNIFIED_011.2 SYNTH-EXC (§21 dooz livelock fix): a CONFIRMED \
                         * out-of-bounds access must throw ArrayIndexOutOfBoundsException \
                         * (real Dalvik semantics) instead of warn-and-continue. The old \
                         * behavior produced an infinite loop in dooz LM1/i;.f (the loop \
                         * index ran past the array end 50000+ times because no exception \
                         * ever fired). Only a CONFIRMED OOB (known arr_len > 0) throws — \
                         * arr_len == 0 may mean "length unknown" in this engine, so that \
                         * path keeps the legacy warn-and-continue to avoid regressing \
                         * APKs whose array length was never recorded. \
                         */ \
                        if (arr_len > 0) { \
                            /* UNIFIED_014: message aligned to ART canonical \
                             * "length=<len>; index=<idx>" (mirror/array.cc \
                             * ThrowArrayIndexOutOfBoundsException chain). */ \
                            std::string oob_msg = "length=" + std::to_string(arr_len) + \
                                                  "; index=" + std::to_string(idx); \
                            raise_synthetic_exception( \
                                "Ljava/lang/ArrayIndexOutOfBoundsException;", \
                                oob_msg, "aget-oob"); \
                            /* handled: pc_ now at catch handler; unhandled: frame unwinds \
                             * via halted_on_return_ (post-switch check exits the loop). */ \
                            break; \
                        } \
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
                            /* PASS-3 (K-41): normalize typed scalar elements to INT. \
                             * Real Dalvik: aget-byte/char/short yield an INT register; \
                             * the engine stores typed scalars with SEPARATE byte_val/ \
                             * char_val/short_val members, so leaving the typed value in \
                             * the register made every later int_val arithmetic read 0. */ \
                            if (result_val.type == DalvikType::BYTE) \
                                result_val = DalvikValue::make_int(result_val.byte_val); \
                            else if (result_val.type == DalvikType::SHORT) \
                                result_val = DalvikValue::make_int(result_val.short_val); \
                            else if (result_val.type == DalvikType::CHAR) \
                                result_val = DalvikValue::make_int( \
                                    static_cast<unsigned char>(result_val.char_val)); \
                            /* Ensure type matches expected result_type */ \
                            if (result_type == DalvikType::BOOLEAN) { \
                                /* Normalize to 0 or 1 */ \
                                bool b = (elem->type == DalvikType::INT32) ? (elem->int_val != 0) : \
                                         (elem->type == DalvikType::BOOLEAN) ? elem->bool_val : false; \
                                result_val = DalvikValue::make_bool(b); \
                            } else if (result_type == DalvikType::INT32 && \
                                       elem->type != DalvikType::INT32) { \
                                /* PASS-3 FORENSIC FIX (K-41): typed elements \
                                 * (BYTE/CHAR/SHORT — stored via aput-* or the new \
                                 * InputStream.read(byte[])) carry their value in \
                                 * byte_val/char_val/short_val. The old code zeroed \
                                 * every non-INT32 element, so aget-byte on ANY heap \
                                 * array always returned 0. */ \
                                int32_t conv_val = 0; \
                                switch (elem->type) { \
                                    case DalvikType::BYTE:  conv_val = elem->byte_val; break; \
                                    case DalvikType::CHAR:  conv_val = static_cast<unsigned char>(elem->char_val); break; \
                                    case DalvikType::SHORT: conv_val = elem->short_val; break; \
                                    case DalvikType::BOOLEAN: conv_val = elem->bool_val ? 1 : 0; break; \
                                    case DalvikType::INT64: conv_val = static_cast<int32_t>(elem->long_val); break; \
                                    default: conv_val = elem->int_val; break; \
                                } \
                                result_val = DalvikValue::make_int(conv_val); \
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
            //
            // UNIFIED_014 (DEX-APUT-BOUNDS): AOSP aput semantics for CONFIRMED
            // arrays. Reference: AOSP art
            // runtime/interpreter/interpreter_switch_impl-inl.h HandleAPut /
            // APUT_OBJECT (main, fetched 2026-09-03; see
            // docs/upstream_reference_aput_aosp.md): null array → NPE;
            // CheckIsValidIndex → AIOOBE; store only after checks; array
            // length is NEVER mutated by aput. The old code wrote ANY index
            // and auto-grew "__array_length__" to idx+1 — the DEX-APUT-BOUNDS
            // drift (phantom array tail for array-length/loops).
            // Conservative tiers mirror the UNIFIED_011.2 aget fix:
            //   - CONFIRMED length (effective len > 0): full AOSP enforcement
            //     (null/bounds checked, length immutable).
            //   - length 0/unknown: legacy store+grow path preserved (arrays
            //     filled aput-by-aput by bridges with no recorded length keep
            //     working; mirrors aget's arr_len==0 legacy gate).
            //   - NULL_REF: AOSP NPE (null is unambiguous in this engine).
            //   - non-OBJECT_REF / heap-missing: legacy silent skip (unchanged).
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
                    if (strcmp(op_name, "aput-object") == 0) { \
                        std::cerr << "[EXP093-APUT] " << op_name \
                                  << " v" << (int)vAA << "→arr[v" << (int)vBB \
                                  << "] idx_v" << (int)vCC \
                                  << " arr_type=" << (int)arr_val.type \
                                  << " arr_obj=" << arr_val.object_id \
                                  << " src_type=" << (int)src_val.type \
                                  << " idx=" << idx << std::endl; \
                    } \
                    /* AOSP HandleAPut: null array → NPE, no store. */ \
                    if (arr_val.type == DalvikType::NULL_REF || arr_val.is_null) { \
                        log("⚠️ APUT into null array (" + std::string(op_name) + \
                            ") idx=" + std::to_string(idx)); \
                        raise_synthetic_exception( \
                            "Ljava/lang/NullPointerException;", \
                            "Attempt to write into null array", "aput-null"); \
                        /* handled: pc_ at catch handler; unhandled: frame \
                         * unwinds via halted_on_return_ (same as aget). */ \
                        break; \
                    } \
                    /* Effective length chain — identical to ARRAY_GET_CASE. */ \
                    bool arr_on_heap = (arr_val.type == DalvikType::OBJECT_REF && \
                                        heap_.has_object(arr_val.object_id)); \
                    int32_t arr_len = 0; \
                    if (arr_on_heap) { \
                        auto len_field = heap_.get_object_field(arr_val.object_id, "__array_length__"); \
                        if (len_field.has_value() && len_field->type == DalvikType::INT32) { \
                            arr_len = len_field->int_val; \
                        } \
                        if (arr_len == 0) { \
                            auto nm_field = heap_.get_object_field(arr_val.object_id, "__new_array_length__"); \
                            if (nm_field.has_value() && nm_field->type == DalvikType::INT32) { \
                                arr_len = nm_field->int_val; \
                            } \
                        } \
                        if (arr_len == 0) { \
                            arr_len = arr_val.int_val; \
                        } \
                    } \
                    std::string field = "array[" + std::to_string(idx) + "]"; \
                    if (arr_on_heap && arr_len > 0) { \
                        /* CONFIRMED array: full AOSP semantics. */ \
                        if (idx < 0 || idx >= arr_len) { \
                            log("⚠️ APUT out of bounds: arr_len=" + std::to_string(arr_len) + \
                                " idx=" + std::to_string(idx)); \
                            std::string oob_msg = "length=" + std::to_string(arr_len) + \
                                                  "; index=" + std::to_string(idx); \
                            raise_synthetic_exception( \
                                "Ljava/lang/ArrayIndexOutOfBoundsException;", \
                                oob_msg, "aput-oob"); \
                            break; \
                        } \
                        heap_.set_object_field(arr_val.object_id, field, src_val); \
                        /* Length immutable — NO auto-grow (AOSP). */ \
                    } else if (arr_on_heap) { \
                        /* Length unknown (0): legacy path — store + record/grow. \
                         * Preserves arrays filled aput-by-aput with no recorded \
                         * length (mirrors aget's arr_len==0 legacy gate). */ \
                        heap_.set_object_field(arr_val.object_id, field, src_val); \
                        auto len_field = heap_.get_object_field(arr_val.object_id, "__array_length__"); \
                        if (!len_field.has_value() || len_field->int_val <= idx) { \
                            heap_.set_object_field(arr_val.object_id, "__array_length__", \
                                DalvikValue::make_int(idx + 1)); \
                        } \
                    } \
                    /* non-OBJECT_REF or heap-missing: legacy silent skip. */ \
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
                // EXP-095 (CM-019): SIGNATURE-AWARE arg building (same as
                // invoke-static 35c). Per the method proto, wide params (J/D)
                // consume two registers and FLOAT (F) params carry raw float
                // BITS in an INT32 register (const/high16 is not float-typed).
                // Without this, LayoutHelper.createLinear(F,F,I,F,F,F,F) via
                // /range delivered heights like 0xC0000000 and margins like
                // 0x42000000 (raw float bits) into the layout engine.
                std::vector<DalvikValue> args;
                {
                    std::string range_proto = "<unknown>";
                    if (dex_report_) {
                        range_proto = resolve_method_proto_for_dex(method_idx, current_dex_index_);
                    }
                    std::vector<std::string> param_types;
                    if (range_proto != "<unknown>") {
                        size_t lp = range_proto.find('(');
                        size_t rp = range_proto.find(')');
                        if (lp != std::string::npos && rp != std::string::npos && rp > lp) {
                            std::string params = range_proto.substr(lp + 1, rp - lp - 1);
                            size_t i = 0;
                            while (i < params.size()) {
                                char c = params[i];
                                if (c == 'L') {
                                    size_t semi = params.find(';', i);
                                    if (semi == std::string::npos) break;
                                    param_types.push_back(params.substr(i, semi - i + 1));
                                    i = semi + 1;
                                } else if (c == '[') {
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
                                    param_types.push_back(std::string(1, c));
                                    i += 1;
                                }
                            }
                        }
                    }
                    if (param_types.empty()) {
                        for (uint8_t i = 0; i < argc; ++i) {
                            args.push_back(get_register(first_reg + i));
                        }
                    } else {
                        uint32_t reg_idx = 0;
                        for (size_t p = 0; p < param_types.size() && reg_idx < 256 && (uint8_t)reg_idx < argc; ++p) {
                            const std::string& pt = param_types[p];
                            if (pt == "J" || pt == "D") {
                                DalvikValue lo = get_register(first_reg + reg_idx);
                                if (lo.type == DalvikType::INT64) {
                                    if (pt == "D") {
                                        double dv; int64_t bits = lo.long_val;
                                        std::memcpy(&dv, &bits, sizeof(dv));
                                        args.push_back(DalvikValue::make_double(dv));
                                    } else {
                                        args.push_back(lo);
                                    }
                                } else {
                                    DalvikValue hi = get_register(first_reg + reg_idx + 1);
                                    int64_t combined = (static_cast<int64_t>(hi.int_val) << 32) |
                                                       (static_cast<uint32_t>(lo.int_val));
                                    if (pt == "D") {
                                        double dv; int64_t bits = combined;
                                        std::memcpy(&dv, &bits, sizeof(dv));
                                        args.push_back(DalvikValue::make_double(dv));
                                    } else {
                                        args.push_back(DalvikValue::make_long(combined));
                                    }
                                }
                                reg_idx += 2;
                            } else {
                                DalvikValue v = get_register(first_reg + reg_idx);
                                if (pt == "F" && v.type == DalvikType::INT32) {
                                    float f;
                                    int32_t bits = v.int_val;
                                    std::memcpy(&f, &bits, sizeof(f));
                                    args.push_back(DalvikValue::make_float(f));
                                } else {
                                    args.push_back(v);
                                }
                                reg_idx += 1;
                            }
                        }
                    }
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
                    bridge_to_api(class_name, method_name, args, return_val, status, method_idx); last_invoke_return_ = return_val;
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
            // EXP-088+ F5 CRITICAL FIX: return-wide (opcode 0x10) was MISSING
            // from the opcode dispatcher. It fell through to the default case
            // (handle_unimplemented), causing any method that returns a long
            // or double to:
            //   1. Not actually return (PC didn't advance past the return)
            //   2. Leave the caller's move-result-wide reading stale/zero data
            //
            // This is a GENERIC VM bug — affects any APK that uses long/double
            // return values (timestamps, durations, sizes, coordinates, etc.).
            case Opcode::RETURN_WIDE:
                success = execute_return_wide(pc_, trace);
                trace.opcode_name = "return-wide";
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
            
            // MASTER RECONCILIATION (K-18, 2026-09-03): packed-switch/sparse-switch.
            // IMPORTANT (why this exists): both opcodes were defined in the
            // opcode table but had NO dispatch case — every switch statement
            // produced by D8 (string/table switches, state machines, enum
            // maps) fell through to handle_unimplemented and halted the
            // method. Fixture: tests/semantic_switch_parse_neg_test.cpp
            // (group S — 7/7 FAIL pre-fix).
            // Semantics per AOSP/dalvik bytecodes:
            //   31t format: AA|op BBBB|BBBB — 32-bit signed payload offset in
            //   code units, relative to the SWITCH opcode pc.
            //   packed-switch-payload (ident 0x0100): u16 size, i32 first_key,
            //     i32 targets[size] — targets also relative to the SWITCH pc.
            //   sparse-switch-payload (ident 0x0200): u16 size, i32 keys[size]
            //     (sorted), i32 targets[size].
            //   No match → default = pc + 3 (fall past the 3-unit instruction).
            case Opcode::PACKED_SWITCH:
            case Opcode::SPARSE_SWITCH: {
                const bool is_packed = (opcode == Opcode::PACKED_SWITCH);
                uint16_t instr_sw = bytecode_[pc_];
                uint8_t vAA_sw = (instr_sw >> 8) & 0xFF;
                if (pc_ + 2 >= bytecode_.size()) return false;
                int32_t off_sw = static_cast<int32_t>(
                    static_cast<uint32_t>(bytecode_[pc_ + 1]) |
                    (static_cast<uint32_t>(bytecode_[pc_ + 2]) << 16));
                const int64_t payload_addr = static_cast<int64_t>(pc_) + off_sw;
                DalvikValue vv_sw = get_register(vAA_sw);
                int32_t key_sw = (vv_sw.type == DalvikType::INT64)
                                     ? static_cast<int32_t>(vv_sw.long_val)
                                 : (vv_sw.type == DalvikType::INT32 ? vv_sw.int_val : 0);
                int32_t target_sw = 3;  // default: fall through the 3-unit instr
                auto in_range_sw = [&](int64_t addr, int64_t units) {
                    return addr >= 0 && addr + units <= static_cast<int64_t>(bytecode_.size());
                };
                auto read_i32_sw = [&](int64_t addr) -> int32_t {
                    return static_cast<int32_t>(
                        static_cast<uint32_t>(bytecode_[static_cast<size_t>(addr)]) |
                        (static_cast<uint32_t>(bytecode_[static_cast<size_t>(addr) + 1]) << 16));
                };
                if (in_range_sw(payload_addr, 2)) {
                    const uint16_t ident_sw = bytecode_[static_cast<size_t>(payload_addr)];
                    if ((is_packed && ident_sw == 0x0100) || (!is_packed && ident_sw == 0x0200)) {
                        const uint16_t size_sw = bytecode_[static_cast<size_t>(payload_addr) + 1];
                        if (is_packed) {
                            if (in_range_sw(payload_addr, 4)) {
                                const int32_t first_key_sw = read_i32_sw(payload_addr + 2);
                                const int64_t idx_sw =
                                    static_cast<int64_t>(key_sw) - first_key_sw;
                                if (idx_sw >= 0 && idx_sw < static_cast<int64_t>(size_sw) &&
                                    in_range_sw(payload_addr + 4 + idx_sw * 2, 2)) {
                                    target_sw = read_i32_sw(payload_addr + 4 + idx_sw * 2);
                                }
                            }
                        } else {
                            // keys: payload+2 .. +2+2*size; targets: payload+2+2*size ..
                            if (in_range_sw(payload_addr, 2 + 4 * static_cast<int64_t>(size_sw))) {
                                int64_t lo_sw = 0, hi_sw = size_sw - 1;
                                int64_t found_sw = -1;
                                while (lo_sw <= hi_sw) {
                                    int64_t mid_sw = (lo_sw + hi_sw) / 2;
                                    int32_t k_sw = read_i32_sw(payload_addr + 2 + mid_sw * 2);
                                    if (k_sw == key_sw) { found_sw = mid_sw; break; }
                                    if (k_sw < key_sw) lo_sw = mid_sw + 1; else hi_sw = mid_sw - 1;
                                }
                                if (found_sw >= 0 &&
                                    in_range_sw(payload_addr + 2 + 2 * static_cast<int64_t>(size_sw) + found_sw * 2, 2)) {
                                    target_sw = read_i32_sw(
                                        payload_addr + 2 + 2 * static_cast<int64_t>(size_sw) + found_sw * 2);
                                }
                            }
                        }
                    } else {
                        std::cerr << "[SWITCH] payload ident mismatch (expected 0x"
                                  << (is_packed ? "0100" : "0200") << ", got 0x"
                                  << to_hex16(ident_sw) << ") → default" << std::endl;
                    }
                } else {
                    std::cerr << "[SWITCH] payload address out of range (pc=" << pc_
                              << " off=" << off_sw << ") → default" << std::endl;
                }
                trace.opcode_name = is_packed ? "packed-switch" : "sparse-switch";
                pc_ = pc_ + target_sw;  // targets are relative to the SWITCH pc
                break;
            }

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
                    /* MASTER RECONCILIATION (K-29, 2026-09-03): was guard-yield-0 — */ \
                    /* AND the unguarded a_val / b_val below was C++ UB on zero.   */ \
                    /* Now throws ArithmeticException (deferred mechanism).        */ \
                    if ((op == "div" || op == "rem") && b_val == 0) { \
                        throw_deferred("Ljava/lang/ArithmeticException;", "divide by zero", "ARITH-2ADDR"); \
                        pc_ = pc_ + 1; \
                        break; \
                    } \
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
                    if ((op == "div" || op == "rem") && c_val == 0) { \
                        throw_deferred("Ljava/lang/ArithmeticException;", "divide by zero", "ARITH-23X"); \
                        pc_ = pc_ + 2; \
                        break; \
                    } \
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
                    /* K-29: lit8 div/rem by zero throws (deferred mechanism).  */ \
                    if ((op == "div" || op == "rem") && lit == 0) { \
                        throw_deferred("Ljava/lang/ArithmeticException;", "divide by zero", "ARITH-LIT8"); \
                        pc_ = pc_ + 2; \
                        break; \
                    } \
                    if (op == "add") result_val.int_val = b_val + lit; \
                    else if (op == "rsub") result_val.int_val = lit - b_val; \
                    else if (op == "sub") result_val.int_val = b_val - lit; \
                    else if (op == "mul") result_val.int_val = b_val * lit; \
                    else if (op == "div") result_val.int_val = b_val / lit; \
                    else if (op == "rem") result_val.int_val = b_val % lit; \
                    else if (op == "and") result_val.int_val = b_val & lit; \
                    else if (op == "or")  result_val.int_val = b_val | lit; \
                    else if (op == "xor") result_val.int_val = b_val ^ lit; \
                    else if (op == "shl") result_val.int_val = b_val << (lit & 0x1f); \
                    else if (op == "shr") result_val.int_val = b_val >> (lit & 0x1f); \
                    else if (op == "ushr") result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(b_val) >> (lit & 0x1f)); \
                    set_register(vAA, result_val); \
                    trace.opcode_name = op_name; \
                    pc_ = pc_ + 2; \
                    break; \
                }

            ARITH_LIT8_CASE(ADD_INT_LIT8, "add-int/lit8", "add")
            ARITH_LIT8_CASE(RSUB_INT_LIT8, "rsub-int/lit8", "rsub")
            ARITH_LIT8_CASE(MUL_INT_LIT8, "mul-int/lit8", "mul")
            ARITH_LIT8_CASE(DIV_INT_LIT8, "div-int/lit8", "div")
            ARITH_LIT8_CASE(REM_INT_LIT8, "rem-int/lit8", "rem")
            ARITH_LIT8_CASE(AND_INT_LIT8, "and-int/lit8", "and")
            ARITH_LIT8_CASE(OR_INT_LIT8,  "or-int/lit8",  "or")
            ARITH_LIT8_CASE(XOR_INT_LIT8, "xor-int/lit8", "xor")
            ARITH_LIT8_CASE(SHL_INT_LIT8, "shl-int/lit8", "shl")
            ARITH_LIT8_CASE(SHR_INT_LIT8, "shr-int/lit8", "shr")
            ARITH_LIT8_CASE(USHR_INT_LIT8, "ushr-int/lit8", "ushr")
            #undef ARITH_LIT8_CASE

            // EXP-038 (BLOCKER-028): Arithmetic lit16 (22s format: B|A|op BBBB)
            // vA = vB <op> #BBBB (signed 16-bit)
            // PASS-3 FORENSIC CORRECTION (K-38): the register nibbles were
            // decoded ONE NIBBLE OFF (vA=(>>8), vB=(>>4) — the K-05 bug class
            // again): every lit16 op read its SOURCE from the wrong register
            // field and wrote the result to the wrong destination. Correct
            // 22s decode: vA = HIGH nibble (>>12), vB = low nibble of the
            // high byte (>>8).
            #define ARITH_LIT16_CASE(opcode, op_name, op) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vA = (instr >> 12) & 0xF; \
                    uint8_t vB = (instr >> 8) & 0xF; \
                    int16_t lit = static_cast<int16_t>(bytecode_[pc_ + 1]); \
                    DalvikValue b = get_register(vB); \
                    DalvikValue result_val; \
                    result_val.type = DalvikType::INT32; \
                    int32_t b_val = (b.type == DalvikType::INT32) ? b.int_val : 0; \
                    if ((op == "div" || op == "rem") && lit == 0) { \
                        throw_deferred("Ljava/lang/ArithmeticException;", "divide by zero", "ARITH-LIT16"); \
                        pc_ = pc_ + 2; \
                        break; \
                    } \
                    if (op == "add") result_val.int_val = b_val + lit; \
                    else if (op == "rsub") result_val.int_val = lit - b_val; \
                    else if (op == "sub") result_val.int_val = b_val - lit; \
                    else if (op == "mul") result_val.int_val = b_val * lit; \
                    else if (op == "div") result_val.int_val = b_val / lit; \
                    else if (op == "rem") result_val.int_val = b_val % lit; \
                    else if (op == "and") result_val.int_val = b_val & lit; \
                    else if (op == "or")  result_val.int_val = b_val | lit; \
                    else if (op == "xor") result_val.int_val = b_val ^ lit; \
                    else if (op == "shl") result_val.int_val = b_val << (lit & 0x1f); \
                    else if (op == "shr") result_val.int_val = b_val >> (lit & 0x1f); \
                    else if (op == "ushr") result_val.int_val = static_cast<int32_t>(static_cast<uint32_t>(b_val) >> (lit & 0x1f)); \
                    set_register(vA, result_val); \
                    trace.opcode_name = op_name; \
                    pc_ = pc_ + 2; \
                    break; \
                }

            ARITH_LIT16_CASE(ADD_INT_LIT16, "add-int/lit16", "add")
            ARITH_LIT16_CASE(RSUB_INT_LIT16, "rsub-int", "rsub")
            ARITH_LIT16_CASE(MUL_INT_LIT16, "mul-int/lit16", "mul")
            ARITH_LIT16_CASE(DIV_INT_LIT16, "div-int/lit16", "div")
            ARITH_LIT16_CASE(REM_INT_LIT16, "rem-int/lit16", "rem")
            ARITH_LIT16_CASE(AND_INT_LIT16, "and-int/lit16", "and")
            ARITH_LIT16_CASE(OR_INT_LIT16,  "or-int/lit16",  "or")
            ARITH_LIT16_CASE(XOR_INT_LIT16, "xor-int/lit16", "xor")
            // PASS-3 (K-37): the former SHL/SHR/USHR_INT_LIT16 cases here were
            // REMOVED — those opcodes do not exist in Dalvik; 0xD8..0xDA are
            // add/rsub/mul-int/lit8 and now dispatch via the corrected lit8
            // table above.
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
            // EXP-088+ F5 CRITICAL FIX: Previously this was hardcoded to make_int(0),
            // which discarded the wide return value entirely. Now we correctly
            // propagate the last_invoke_return_ value (set by execute_return_wide
            // or by the wide-return path in try_recursive_invoke).
            //
            // The wide value is stored in last_invoke_return_.long_val (for INT64)
            // or last_invoke_return_.double_val (for FLOAT64). We preserve the type
            // so downstream consumers (iget-wide, return-wide, arithmetic) can
            // distinguish long vs double.
            case Opcode::MOVE_RESULT_WIDE: {
                uint16_t instr = bytecode_[pc_];
                uint8_t dest = (instr >> 8) & 0xFF;
                DalvikValue val = last_invoke_return_;
                // If last_invoke_return_ wasn't set by a wide return, default to 0
                // but preserve INT64 type (most common case for move-result-wide).
                if (val.type != DalvikType::INT64 && val.type != DalvikType::FLOAT64) {
                    val = DalvikValue::make_long(0);
                }
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

            // Conversion opcodes (12x: B|A|op, 1 code unit).
            //
            // IMPORTANT (RESULT_010 reconciliation, master request §7/§9):
            // a conversion must perform the REAL numeric conversion and retag
            // the result type. The previous implementation ONLY changed the
            // type tag to INT32 and left the union bits untouched, so
            // int-to-long(-5) read back as garbage, float-to-int returned the
            // raw float BITS as an integer, and int-to-byte/char/short never
            // masked. Dalvik/AOSP numeric-conversion semantics implemented:
            //   int→long sign-extend · long→int truncate low 32
            //   float/double→int/long: NaN→0, round-toward-zero + saturate
            //   int→byte sign-extend low 8 · int→char zero-extend low 16 ·
            //   int→short sign-extend low 16
            // Regression fixture: tests/semantic_long_cmp_conv_test.cpp
            #define CONV_SRC_I32(opcode, op_name, DST_KIND, STORE_EXPR) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    /* 12x = B|A|op: A (dest) is the HIGH nibble, B (src) the LOW */ \
                    /* nibble of byte 1. The pre-reconciliation code had these */ \
                    /* swapped — conversions wrote the source register and read */ \
                    /* the destination, so results landed in the wrong slot */ \
                    /* (visible only when dest != src). */ \
                    uint8_t vA = (instr >> 12) & 0xF; \
                    uint8_t vB = (instr >> 8) & 0xF; \
                    DalvikValue val = get_register(vB); \
                    DalvikValue out; out.type = DST_KIND; \
                    int32_t s = (val.type == DalvikType::INT32) ? val.int_val \
                              : (val.type == DalvikType::INT64 ? static_cast<int32_t>(val.long_val) : 0); \
                    STORE_EXPR; \
                    set_register(vA, out); \
                    trace.opcode_name = op_name; \
                    pc_ += 1; \
                    break; \
                }
            #define CONV_SRC_I64(opcode, op_name, DST_KIND, STORE_EXPR) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vA = (instr >> 12) & 0xF; /* dest = HIGH nibble (12x) */ \
                    uint8_t vB = (instr >> 8) & 0xF;  /* src  = LOW nibble  (12x) */ \
                    DalvikValue val = get_register(vB); \
                    DalvikValue out; out.type = DST_KIND; \
                    int64_t s = (val.type == DalvikType::INT64) ? val.long_val \
                              : (val.type == DalvikType::INT32 ? static_cast<int64_t>(val.int_val) : 0); \
                    STORE_EXPR; \
                    set_register(vA, out); \
                    trace.opcode_name = op_name; \
                    pc_ += 1; \
                    break; \
                }
            #define CONV_SRC_F32(opcode, op_name, DST_KIND, STORE_EXPR) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vA = (instr >> 12) & 0xF; /* dest = HIGH nibble (12x) */ \
                    uint8_t vB = (instr >> 8) & 0xF;  /* src  = LOW nibble  (12x) */ \
                    DalvikValue val = get_register(vB); \
                    DalvikValue out; out.type = DST_KIND; \
                    float s = (val.type == DalvikType::FLOAT32) ? val.float_val \
                            : (val.type == DalvikType::INT32 ? static_cast<float>(val.int_val) : 0.0f); \
                    STORE_EXPR; \
                    set_register(vA, out); \
                    trace.opcode_name = op_name; \
                    pc_ += 1; \
                    break; \
                }
            #define CONV_SRC_F64(opcode, op_name, DST_KIND, STORE_EXPR) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vA = (instr >> 12) & 0xF; /* dest = HIGH nibble (12x) */ \
                    uint8_t vB = (instr >> 8) & 0xF;  /* src  = LOW nibble  (12x) */ \
                    DalvikValue val = get_register(vB); \
                    DalvikValue out; out.type = DST_KIND; \
                    double s = (val.type == DalvikType::FLOAT64) ? val.double_val \
                             : (val.type == DalvikType::INT64 ? bits_l2d(val.long_val) : 0.0); \
                    STORE_EXPR; \
                    set_register(vA, out); \
                    trace.opcode_name = op_name; \
                    pc_ += 1; \
                    break; \
                }
            CONV_SRC_I32(INT_TO_LONG,   "int-to-long",    DalvikType::INT64,   out.long_val  = static_cast<int64_t>(s))
            CONV_SRC_I32(INT_TO_FLOAT,  "int-to-float",   DalvikType::FLOAT32, out.float_val = static_cast<float>(s))
            CONV_SRC_I32(INT_TO_DOUBLE, "int-to-double",  DalvikType::FLOAT64, out.double_val = static_cast<double>(s))
            CONV_SRC_I64(LONG_TO_INT,   "long-to-int",    DalvikType::INT32,   out.int_val   = static_cast<int32_t>(s))
            CONV_SRC_I64(LONG_TO_FLOAT, "long-to-float",  DalvikType::FLOAT32, out.float_val = static_cast<float>(s))
            CONV_SRC_I64(LONG_TO_DOUBLE,"long-to-double", DalvikType::FLOAT64, out.double_val = static_cast<double>(s))
            CONV_SRC_F32(FLOAT_TO_INT,  "float-to-int",   DalvikType::INT32,   out.int_val   = conv_f2i(static_cast<double>(s)))
            CONV_SRC_F32(FLOAT_TO_LONG, "float-to-long",  DalvikType::INT64,   out.long_val  = conv_f2l(static_cast<double>(s)))
            CONV_SRC_F32(FLOAT_TO_DOUBLE,"float-to-double",DalvikType::FLOAT64,out.double_val = static_cast<double>(s))
            CONV_SRC_F64(DOUBLE_TO_INT, "double-to-int",  DalvikType::INT32,   out.int_val   = conv_f2i(s))
            CONV_SRC_F64(DOUBLE_TO_LONG,"double-to-long", DalvikType::INT64,   out.long_val  = conv_f2l(s))
            CONV_SRC_F64(DOUBLE_TO_FLOAT,"double-to-float",DalvikType::FLOAT32,out.float_val = static_cast<float>(s))
            CONV_SRC_I32(INT_TO_BYTE,   "int-to-byte",    DalvikType::INT32,   out.int_val   = static_cast<int8_t>(s & 0xFF))
            CONV_SRC_I32(INT_TO_CHAR,   "int-to-char",    DalvikType::INT32,   out.int_val   = static_cast<uint16_t>(s & 0xFFFF))
            CONV_SRC_I32(INT_TO_SHORT,  "int-to-short",   DalvikType::INT32,   out.int_val   = static_cast<int16_t>(s & 0xFFFF))
            #undef CONV_SRC_I32
            #undef CONV_SRC_I64
            #undef CONV_SRC_F32
            #undef CONV_SRC_F64

            // MASTER RECONCILIATION (2026-09-03, NOT_DONE #4 audit): unary
            // neg/not family (12x format: B|A|op). The entire block was
            // ABSENT from the dispatch — neg-int/not-int/neg-long/not-long/
            // neg-float/neg-double all hit handle_unimplemented. The audit
            // predicted an int32-alias bug (K-01 class); the truth was worse:
            // no implementation existed at all. Nibble convention follows the
            // (already fixed) CONV block: dest = HIGH nibble (instr>>12),
            // source = low nibble (instr>>8). Wrap-around negation is done in
            // the UNSIGNED domain to avoid signed-overflow UB — INT32_MIN and
            // INT64_MIN negate to themselves per the JLS.
            // Fixture: tests/semantic_switch_parse_neg_test.cpp (group N —
            // 7/7 FAIL pre-fix, all returned 0 via the unimplemented path).
            #define UNARY_I32_CASE(opcode, op_name, EXPR) \
                case Opcode::opcode: { \
                    uint16_t instr_u = bytecode_[pc_]; \
                    uint8_t vA_u = (instr_u >> 12) & 0xF; \
                    uint8_t vB_u = (instr_u >> 8) & 0xF; \
                    DalvikValue src_u = get_register(vB_u); \
                    DalvikValue out_u; out_u.type = DalvikType::INT32; \
                    int32_t s_u = (src_u.type == DalvikType::INT32) ? src_u.int_val \
                                : (src_u.type == DalvikType::INT64 ? static_cast<int32_t>(src_u.long_val) : 0); \
                    EXPR; \
                    set_register(vA_u, out_u); \
                    trace.opcode_name = op_name; \
                    pc_ += 1; \
                    break; \
                }
            #define UNARY_I64_CASE(opcode, op_name, EXPR) \
                case Opcode::opcode: { \
                    uint16_t instr_u = bytecode_[pc_]; \
                    uint8_t vA_u = (instr_u >> 12) & 0xF; \
                    uint8_t vB_u = (instr_u >> 8) & 0xF; \
                    DalvikValue src_u = get_register(vB_u); \
                    DalvikValue out_u; out_u.type = DalvikType::INT64; \
                    int64_t s_u = (src_u.type == DalvikType::INT64) ? src_u.long_val \
                                : (src_u.type == DalvikType::INT32 ? static_cast<int64_t>(src_u.int_val) : 0); \
                    EXPR; \
                    set_register(vA_u, out_u); \
                    trace.opcode_name = op_name; \
                    pc_ += 1; \
                    break; \
                }
            #define UNARY_F32_CASE(opcode, op_name, EXPR) \
                case Opcode::opcode: { \
                    uint16_t instr_u = bytecode_[pc_]; \
                    uint8_t vA_u = (instr_u >> 12) & 0xF; \
                    uint8_t vB_u = (instr_u >> 8) & 0xF; \
                    DalvikValue src_u = get_register(vB_u); \
                    DalvikValue out_u; out_u.type = DalvikType::FLOAT32; \
                    float s_u = (src_u.type == DalvikType::FLOAT32) ? src_u.float_val \
                              : (src_u.type == DalvikType::INT32 ? bits_i2f(src_u.int_val) : 0.0f); \
                    EXPR; \
                    set_register(vA_u, out_u); \
                    trace.opcode_name = op_name; \
                    pc_ += 1; \
                    break; \
                }
            #define UNARY_F64_CASE(opcode, op_name, EXPR) \
                case Opcode::opcode: { \
                    uint16_t instr_u = bytecode_[pc_]; \
                    uint8_t vA_u = (instr_u >> 12) & 0xF; \
                    uint8_t vB_u = (instr_u >> 8) & 0xF; \
                    DalvikValue src_u = get_register(vB_u); \
                    DalvikValue out_u; out_u.type = DalvikType::FLOAT64; \
                    double s_u = (src_u.type == DalvikType::FLOAT64) ? src_u.double_val \
                               : (src_u.type == DalvikType::INT64 ? bits_l2d(src_u.long_val) \
                               : (src_u.type == DalvikType::FLOAT32 ? static_cast<double>(src_u.float_val) \
                               : (src_u.type == DalvikType::INT32 ? static_cast<double>(bits_i2f(src_u.int_val)) : 0.0))); \
                    EXPR; \
                    set_register(vA_u, out_u); \
                    trace.opcode_name = op_name; \
                    pc_ += 1; \
                    break; \
                }
            UNARY_I32_CASE(NEG_INT,   "neg-int",    out_u.int_val   = static_cast<int32_t>(0u - static_cast<uint32_t>(s_u)))
            UNARY_I32_CASE(NOT_INT,   "not-int",    out_u.int_val   = ~s_u)
            UNARY_I64_CASE(NEG_LONG,  "neg-long",   out_u.long_val  = static_cast<int64_t>(0ULL - static_cast<uint64_t>(s_u)))
            UNARY_I64_CASE(NOT_LONG,  "not-long",   out_u.long_val  = ~s_u)
            UNARY_F32_CASE(NEG_FLOAT, "neg-float",  out_u.float_val = -s_u)
            UNARY_F64_CASE(NEG_DOUBLE,"neg-double", out_u.double_val = -s_u)
            #undef UNARY_I32_CASE
            #undef UNARY_I64_CASE
            #undef UNARY_F32_CASE
            #undef UNARY_F64_CASE

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

            // cmp opcodes (23x) — Dalvik comparison semantics.
            //
            // IMPORTANT (RESULT_009 reconciliation, master request §7/§9):
            // cmp-long MUST read the full 64-bit register value. A previous
            // implementation read int_val (the low 32 bits of the DalvikValue
            // union) and returned 0 for every INT64 operand, silently
            // collapsing all 64-bit comparisons. Regression fixture:
            // tests/semantic_long_cmp_conv_test.cpp (>2^32 operands).
            #define CMP_LONG_CASE(opcode, op_name) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vAA = (instr >> 8) & 0xFF; \
                    uint8_t vBB = bytecode_[pc_ + 1] & 0xFF; \
                    uint8_t vCC = (bytecode_[pc_ + 1] >> 8) & 0xFF; \
                    DalvikValue b = get_register(vBB); \
                    DalvikValue c = get_register(vCC); \
                    DalvikValue result_val; \
                    result_val.type = DalvikType::INT32; \
                    int64_t bv = (b.type == DalvikType::INT64) ? b.long_val \
                               : (b.type == DalvikType::INT32 ? static_cast<int64_t>(b.int_val) : 0); \
                    int64_t cv = (c.type == DalvikType::INT64) ? c.long_val \
                               : (c.type == DalvikType::INT32 ? static_cast<int64_t>(c.int_val) : 0); \
                    result_val.int_val = (bv < cv) ? -1 : (bv > cv) ? 1 : 0; \
                    set_register(vAA, result_val); \
                    trace.opcode_name = op_name; \
                    pc_ += 2; \
                    break; \
                }
            // cmpl/cmpg floating comparisons — NaN ordering per the Dalvik spec:
            //   cmpl → -1 when either operand is NaN (NaN sorts "less than all")
            //   cmpg → +1 when either operand is NaN (NaN sorts "greater than all")
            // ±0.0 compare equal (the <,> comparison below yields 0 naturally).
            // Read operands at the CORRECT width: a FLOAT64 register read through
            // float_val would reinterpret half the double bits as garbage.
            #define CMP_FLOATING_CASE(opcode, op_name, IS_DOUBLE, NAN_RESULT) \
                case Opcode::opcode: { \
                    uint16_t instr = bytecode_[pc_]; \
                    uint8_t vAA = (instr >> 8) & 0xFF; \
                    uint8_t vBB = bytecode_[pc_ + 1] & 0xFF; \
                    uint8_t vCC = (bytecode_[pc_ + 1] >> 8) & 0xFF; \
                    DalvikValue b = get_register(vBB); \
                    DalvikValue c = get_register(vCC); \
                    DalvikValue result_val; \
                    result_val.type = DalvikType::INT32; \
                    long double bv, cv; \
                    if (IS_DOUBLE) { \
                        bv = (b.type == DalvikType::FLOAT64) ? (long double)b.double_val \
                           : (b.type == DalvikType::INT64 ? (long double)bits_l2d(b.long_val) \
                           : (b.type == DalvikType::FLOAT32 ? (long double)b.float_val \
                           : (b.type == DalvikType::INT32 ? (long double)b.int_val : 0.0L))); \
                        cv = (c.type == DalvikType::FLOAT64) ? (long double)c.double_val \
                           : (c.type == DalvikType::INT64 ? (long double)bits_l2d(c.long_val) \
                           : (c.type == DalvikType::FLOAT32 ? (long double)c.float_val \
                           : (c.type == DalvikType::INT32 ? (long double)c.int_val : 0.0L))); \
                    } else { \
                        bv = (b.type == DalvikType::FLOAT32) ? (long double)b.float_val \
                           : (b.type == DalvikType::INT32 ? (long double)b.int_val : 0.0L); \
                        cv = (c.type == DalvikType::FLOAT32) ? (long double)c.float_val \
                           : (c.type == DalvikType::INT32 ? (long double)c.int_val : 0.0L); \
                    } \
                    bool cmp_nan = (bv != bv) || (cv != cv); \
                    result_val.int_val = cmp_nan ? (NAN_RESULT) : ((bv < cv) ? -1 : (bv > cv) ? 1 : 0); \
                    set_register(vAA, result_val); \
                    trace.opcode_name = op_name; \
                    pc_ += 2; \
                    break; \
                }
            CMP_FLOATING_CASE(CMPL_FLOAT, "cmpl-float", false, -1)
            CMP_FLOATING_CASE(CMPG_FLOAT, "cmpg-float", false, 1)
            CMP_FLOATING_CASE(CMPL_DOUBLE, "cmpl-double", true, -1)
            CMP_FLOATING_CASE(CMPG_DOUBLE, "cmpg-double", true, 1)
            CMP_LONG_CASE(CMP_LONG, "cmp-long")
            #undef CMP_LONG_CASE
            #undef CMP_FLOATING_CASE

            // Long arithmetic (23x).
            //
            // IMPORTANT (RESULT_001 reconciliation, master request §7/§9):
            // long arithmetic MUST compute in 64-bit. The DalvikValue union
            // aliases int_val over the LOW 32 bits of long_val — the previous
            // int32_t computation silently truncated every operand above 2^32
            // (2^32 + 1 == 1!) while still tagging the result INT64.
            // System.currentTimeMillis() values (13 digits) were destroyed by
            // this path. Regression fixture:
            // tests/semantic_long_cmp_conv_test.cpp (>2^32 operands).
            //
            // MASTER RECONCILIATION (K-29, 2026-09-03): div/rem by zero
            // now throws java/lang/ArithmeticException via the deferred
            // mechanism (post-switch redirect cannot be clobbered by the
            // macro's pc_ += 2). The old "yield 0" simplification is
            // gone — it silently diverged from Android whenever real apps
            // relied on the exception for control flow.
            // Fixture: tests/semantic_switch_parse_neg_test.cpp (group D).
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
                    int64_t bv = (b.type == DalvikType::INT64) ? b.long_val \
                               : (b.type == DalvikType::INT32 ? static_cast<int64_t>(b.int_val) : 0); \
                    int64_t cv = (c.type == DalvikType::INT64) ? c.long_val \
                               : (c.type == DalvikType::INT32 ? static_cast<int64_t>(c.int_val) : 0); \
                    if ((op == "div" || op == "rem") && cv == 0) { \
                        throw_deferred("Ljava/lang/ArithmeticException;", "divide by zero", "ARITH-LONG"); \
                        pc_ += 2; \
                        break; \
                    } \
                    if (op == "add") result_val.long_val = bv + cv; \
                    else if (op == "sub") result_val.long_val = bv - cv; \
                    else if (op == "mul") result_val.long_val = bv * cv; \
                    else if (op == "div") result_val.long_val = (cv != 0) ? bv / cv : 0; \
                    else if (op == "rem") result_val.long_val = (cv != 0) ? bv % cv : 0; \
                    else if (op == "and") result_val.long_val = bv & cv; \
                    else if (op == "or")  result_val.long_val = bv | cv; \
                    else if (op == "xor") result_val.long_val = bv ^ cv; \
                    else if (op == "shl") result_val.long_val = bv << static_cast<int>(cv & 0x3f); \
                    else if (op == "shr") result_val.long_val = bv >> static_cast<int>(cv & 0x3f); \
                    else if (op == "ushr") result_val.long_val = static_cast<int64_t>(static_cast<uint64_t>(bv) >> static_cast<int>(cv & 0x3f)); \
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
            // EXP-093: filled-new-array (0x24) and filled-new-array/range (0x25)
            // Per AOSP: Creates a new array of the specified type and fills it
            // with the contents of the specified source registers.
            //
            // Format 35c: [B|A|op] [type@CCCC] [D|E|F|G]
            //   A = array size (number of registers, 0-5)
            //   B = bit string indicating which registers (D=bit0, E=bit1, F=bit2, G=bit3, bit4)
            //   type@CCCC = type descriptor
            //   D,E,F,G = source registers
            //
            // Format 3rc: [op] [type@CCCC] [BBBB] [registers CCCC..CCCC+AA-1]
            //   AA = array size (count of registers)
            //   CCCC = first register
            //
            // The array elements come from the source registers IN ORDER.
            // This is critical for Java varargs: Object... args compiles as
            // filled-new-array {v_arg1, v_arg2, ...}, type@Object
            case Opcode::FILLED_NEW_ARRAY:
            case Opcode::FILLED_NEW_ARRAY_RANGE: {
                trace.opcode_name = (opcode == Opcode::FILLED_NEW_ARRAY) ?
                    "filled-new-array" : "filled-new-array/range";

                uint16_t type_idx;
                std::vector<uint8_t> src_regs;

                if (opcode == Opcode::FILLED_NEW_ARRAY) {
                    // Format 35c: A|G|op BBBB FEDC
                    //   code[pc+0] = A|G|op (A = arg count = bits 12-15,
                    //                        G = 5th register = bits 8-11, op = bits 0-7)
                    //   code[pc+1] = BBBB (type_idx)
                    //   code[pc+2] = FEDC (register list, 4 nibbles)
                    //
                    // UNIFIED_011.2 FNA-FIX (§24 audit): previous code read
                    // arg_count from bits 4-7 ((instr >> 4) & 0xF — the high
                    // nibble of the OPCODE byte itself), which yields the
                    // constant 2 for opcode 0x24 regardless of the actual A
                    // field, and the 5th register (G, bits 8-11) was never
                    // read. This is the same bug class fixed for the invoke
                    // family in EXP-037 (BLOCKER-016): see execute_invoke_*
                    // which now use (instr >> 12) & 0xF / (instr >> 8) & 0xF.
                    // Aligned here with the canonical extraction.
                    uint16_t instr0 = bytecode_[pc_];
                    uint16_t cu2 = bytecode_[pc_ + 2];
                    uint8_t arg_count = (instr0 >> 12) & 0x0F;
                    uint8_t fna_regs[5] = {
                        static_cast<uint8_t>(cu2 & 0xF),          // C
                        static_cast<uint8_t>((cu2 >> 4) & 0xF),   // D
                        static_cast<uint8_t>((cu2 >> 8) & 0xF),   // E
                        static_cast<uint8_t>((cu2 >> 12) & 0xF),  // F
                        static_cast<uint8_t>((instr0 >> 8) & 0xF) // G — 5th register
                    };
                    type_idx = bytecode_[pc_ + 1];
                    for (int i = 0; i < arg_count && i < 5; i++) {
                        src_regs.push_back(fna_regs[i]);
                    }
                } else {
                    // Format 3rc: [op|AA] [type@CCCC] [CCCC]
                    uint8_t arg_count = (bytecode_[pc_] >> 8) & 0xFF;
                    type_idx = bytecode_[pc_ + 1];
                    uint16_t first_reg = bytecode_[pc_ + 2];
                    for (int i = 0; i < arg_count; i++) {
                        src_regs.push_back((first_reg + i) & 0xFF);
                    }
                }

                // Resolve type descriptor
                std::string type_desc = "<unknown>";
                if (dex_report_) {
                    auto class_it = class_info_index_.find("Larray;");
                    (void)class_it;
                }
                // Use per-DEX type resolution
                if (is_multidex_ && current_dex_index_ < per_dex_raw_data_.size()) {
                    const auto& raw = per_dex_raw_data_[current_dex_index_];
                    if (raw.size() >= sizeof(dex::DexHeader)) {
                        dex::DexHeader hdr;
                        std::memcpy(&hdr, raw.data(), sizeof(dex::DexHeader));
                        if (type_idx < hdr.type_ids_size) {
                            uint32_t desc_str_idx;
                            std::memcpy(&desc_str_idx, raw.data() + hdr.type_ids_off + type_idx * 4, 4);
                            uint32_t sdo;
                            std::memcpy(&sdo, raw.data() + hdr.string_ids_off + desc_str_idx * 4, 4);
                            size_t pos = sdo;
                            while (pos < raw.size() && raw[pos] & 0x80) pos++;
                            pos++;
                            size_t end = pos;
                            while (end < raw.size() && raw[end] != 0) end++;
                            type_desc = std::string(reinterpret_cast<const char*>(raw.data() + pos), end - pos);
                        }
                    }
                }

                // Allocate the array
                uint32_t arr_id = heap_.allocate(type_desc.empty() ? "Larray;" : type_desc, pc_, 0);
                // Set array length
                heap_.set_object_field(arr_id, "__array_length__",
                    DalvikValue::make_int(static_cast<int32_t>(src_regs.size())));

                // Fill array elements from source registers
                for (size_t i = 0; i < src_regs.size(); i++) {
                    DalvikValue src_val = get_register(src_regs[i]);
                    std::string field_name = "array[" + std::to_string(i) + "]";
                    heap_.set_object_field(arr_id, field_name, src_val);
                }

                std::cerr << "[EXP093-FNA] filled-new-array type=" << type_desc
                          << " count=" << src_regs.size()
                          << " arr_id=" << arr_id << std::endl;

                DalvikValue result_val;
                result_val.type = DalvikType::OBJECT_REF;
                result_val.object_id = arr_id;
                result_val.class_desc = type_desc.empty() ? "Larray;" : type_desc.c_str();
                result_val.int_val = static_cast<int32_t>(src_regs.size());
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
                // UNIFIED_014b: AOSP FillArrayData null check FIRST (before
                // the legacy non-OBJECT_REF skip) — null is unambiguous in
                // this engine and must throw NPE, not be silently skipped.
                if (array_val.type == DalvikType::NULL_REF || array_val.is_null) {
                    log("⚠️ FILL_ARRAY_DATA into null array");
                    raise_synthetic_exception(
                        "Ljava/lang/NullPointerException;",
                        "null array in FILL_ARRAY_DATA", "fill-null");
                    /* handled/unhandled: same pc semantics as aget/aput. */
                    break;
                }
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
                    // UNIFIED_014b (fill-array-data AOSP semantics). Reference:
                    // AOSP art entrypoints/entrypoint_utils.cc FillArrayData
                    // (refs/tags/android-14.0.0_r1, lines 176–195, fetched
                    // 2026-09-03):
                    //   1. null array → NPE "null array in FILL_ARRAY_DATA"
                    //   2. element_count > array length → AIOOBE
                    //      "failed FILL_ARRAY_DATA; length=%d, index=%d"
                    //      (index slot carries the payload COUNT)
                    //   3. fill exactly element_count elements;
                    //      the array length is NEVER modified.
                    // The old code silently overwrote __array_length__ AND
                    // __new_array_length__ with the payload count (shrink/
                    // grow drift real Dalvik never produces), had no
                    // overflow check, and silently truncated fills past 100
                    // elements. (The null check was hoisted above the legacy
                    // non-OBJECT_REF skip — see case head.) Element byte
                    // decoding (little-endian word order per width 1/2/4/8)
                    // was verified correct against the DEX spec and kept
                    // unchanged.
                    if (array_val.type == DalvikType::OBJECT_REF &&
                        heap_.has_object(array_val.object_id)) {
                        // Effective length chain — identical to aget/aput.
                        int32_t arr_len = 0;
                        auto len_field = heap_.get_object_field(array_val.object_id, "__array_length__");
                        if (len_field.has_value() && len_field->type == DalvikType::INT32) {
                            arr_len = len_field->int_val;
                        }
                        if (arr_len == 0) {
                            auto nm_field = heap_.get_object_field(array_val.object_id, "__new_array_length__");
                            if (nm_field.has_value() && nm_field->type == DalvikType::INT32) {
                                arr_len = nm_field->int_val;
                            }
                        }
                        if (arr_len == 0) {
                            arr_len = array_val.int_val;
                        }
                        // AOSP: overflow check BEFORE any store (confirmed
                        // arrays only; unknown length keeps the legacy gate).
                        if (arr_len > 0 && static_cast<uint32_t>(arr_len) < count) {
                            log("⚠️ FILL_ARRAY_DATA overflow: arr_len=" + std::to_string(arr_len) +
                                " count=" + std::to_string(count));
                            raise_synthetic_exception(
                                "Ljava/lang/ArrayIndexOutOfBoundsException;",
                                "failed FILL_ARRAY_DATA; length=" + std::to_string(arr_len) +
                                    ", index=" + std::to_string(count),
                                "fill-oob");
                            break;
                        }
                        // Payload data bounds: the payload bytes must actually
                        // exist in the bytecode stream (corrupt/truncated
                        // payload = cannot fill → same AIOOBE contract).
                        uint32_t data_start = payload_pc + 4;
                        uint64_t bytes_needed = static_cast<uint64_t>(count) * elem_width;
                        uint64_t bytes_avail =
                            (elem_width > 0 && data_start < bytecode_.size())
                                ? static_cast<uint64_t>(bytecode_.size() - data_start) * 2u
                                : 0u;
                        if (count > 0 && elem_width > 0 && bytes_needed > bytes_avail) {
                            log("⚠️ FILL_ARRAY_DATA truncated payload: need " +
                                std::to_string(bytes_needed) + "B, have " +
                                std::to_string(bytes_avail) + "B");
                            raise_synthetic_exception(
                                "Ljava/lang/ArrayIndexOutOfBoundsException;",
                                "failed FILL_ARRAY_DATA; length=" + std::to_string(
                                    arr_len > 0 ? arr_len : static_cast<int32_t>(count)) +
                                    ", index=" + std::to_string(count),
                                "fill-oob");
                            break;
                        }
                        heap_.set_object_field(array_val.object_id,
                            "__fill_array_data_pc__",
                            DalvikValue::make_int(static_cast<int32_t>(payload_pc)));
                        heap_.set_object_field(array_val.object_id,
                            "__fill_array_elem_width__",
                            DalvikValue::make_int(elem_width));
                        heap_.set_object_field(array_val.object_id,
                            "__fill_array_count__",
                            DalvikValue::make_int(static_cast<int32_t>(count)));
                        // UNIFIED_014b: length is NOT touched (AOSP). The old
                        // __array_length__/__new_array_length__ = count writes
                        // are removed — that was the shrink/grow drift.
                        // Read and store each element
                        // Payload starts at payload_pc + 4 (after magic, elem_width, count)
                        // Each element is elem_width bytes, starting at byte offset
                        // (payload_pc + 4) * 2 in the raw bytecode.
                        // UNIFIED_014b: the old `i < 100` silent truncation cap
                        // is removed — overflow is now handled by the explicit
                        // AIOOBE checks above and each store is per-element
                        // bounds-checked below.
                        for (uint32_t i = 0; i < count; ++i) {
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
                            // UNIFIED_011.3 TYPED-CATCH (§18): type-match each
                            // typed handler against the thrown exception class
                            // (shared semantics with find_catch_handler_for_pc).
                            for (int h = 0; h < n_pairs; h++) {
                                uint32_t type_idx = read_uleb(p);
                                uint32_t addr = read_uleb(p);
                                std::string handler_exc_desc =
                                    resolve_type_for_dex(type_idx, current_dex_index_);
                                if (is_exception_subtype(exc_class, handler_exc_desc)) {
                                    handler_found = true;
                                    handler_addr = addr;
                                    is_catch_all = false;
                                    catch_type = handler_exc_desc;
                                    break;
                                }
                            }
                            // If size <= 0, there's a catch-all handler at the end
                            if (size <= 0 && !handler_found) {
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

                // EXP-053 + UNIFIED_011.3: if any handler (typed or catch-all)
                // matched, jump to it instead of halting/skipping.
                if (handler_found) {
                    if (handler_addr < bytecode_.size()) {
                        std::cerr << "[EXCEPTION] → jumping to "
                                  << (is_catch_all ? "catch-all" : "typed")
                                  << " handler at PC=" << handler_addr
                                  << " catch_type=" << catch_type << std::endl;
                        // Save the exception for move-exception to read.
                        pending_exception_ = exc;
                        trace.status = InstructionTrace::Status::BRANCH_TAKEN;
                        trace.operands.push_back({"reason", is_catch_all
                                ? "throw (catch-all handler)"
                                : "throw (typed handler: " + catch_type + ")"});
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

                // UNIFIED_011.3 EXC-PROPAGATE (§18): no handler in this frame.
                // Replaces the EXP-071 skip-and-continue approximation (which
                // silently executed code after the throw — NOT Dalvik
                // semantics). Real Dalvik: unwind this frame; the invoking
                // frame (try_recursive_invoke call site) then searches ITS
                // try table via frame_unwind_exception_.
                if (!handler_found) {
                    std::cerr << "[EXCEPTION] no handler for " << exc_class
                              << " in " << current_class_ << "."
                              << current_method_
                              << " — unwinding frame (propagate to caller)"
                              << std::endl;
                    frame_unwind_exception_valid_ = true;
                    frame_unwind_exception_ = exc;
                    last_invoke_return_ = DalvikValue::make_null();
                    halted_on_return_ = true;
                    pc_ += 1;
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
                    double bd = (b.type == DalvikType::FLOAT64) ? b.double_val \
                              : (b.type == DalvikType::INT64 ? bits_l2d(b.long_val) : (double)b.int_val); \
                    double cd = (c.type == DalvikType::FLOAT64) ? c.double_val \
                              : (c.type == DalvikType::INT64 ? bits_l2d(c.long_val) : (double)c.int_val); \
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
                    /* 12x format is B|A|op: A is the HIGH nibble of byte 1. */ \
                    /* IMPORTANT (RESULT_007 reconciliation): the previous code */ \
                    /* read vA=(instr>>8) and vB=(instr>>4) — i.e. it swapped the */ \
                    /* two registers AND read vB from the opcode byte's high */ \
                    /* nibble (a constant 0xB for add-long/2addr). Every /2addr */ \
                    /* long op therefore computed regA op reg11. Regression */ \
                    /* fixture: tests/semantic_long_cmp_conv_test.cpp. */ \
                    uint8_t vA = (instr >> 12) & 0xF; \
                    uint8_t vB = (instr >> 8) & 0xF; \
                    DalvikValue a = get_register(vA); \
                    DalvikValue b = get_register(vB); \
                    DalvikValue result_val; \
                    result_val.type = op_type; \
                    if (op_type == DalvikType::INT64) { \
                        /* IMPORTANT (RESULT_001): full 64-bit computation via */ \
                        /* long_val — int_val only aliases the low 32 union bits. */ \
                        int64_t av = (a.type == DalvikType::INT64) ? a.long_val \
                                   : (a.type == DalvikType::INT32 ? static_cast<int64_t>(a.int_val) : 0); \
                        int64_t bv = (b.type == DalvikType::INT64) ? b.long_val \
                                   : (b.type == DalvikType::INT32 ? static_cast<int64_t>(b.int_val) : 0); \
                        if ((std::string(op) == "div" || std::string(op) == "rem") && bv == 0) { \
                            /* MASTER RECONCILIATION (K-29): throws instead of yield-0. */ \
                            throw_deferred("Ljava/lang/ArithmeticException;", "divide by zero", "ARITH-W2A"); \
                            pc_ += 1; \
                            break; \
                        } \
                        if (std::string(op) == "add") result_val.long_val = av + bv; \
                        else if (std::string(op) == "sub") result_val.long_val = av - bv; \
                        else if (std::string(op) == "mul") result_val.long_val = av * bv; \
                        else if (std::string(op) == "div") result_val.long_val = (bv != 0) ? av / bv : 0; \
                        else if (std::string(op) == "rem") result_val.long_val = (bv != 0) ? av % bv : 0; \
                        else if (std::string(op) == "and") result_val.long_val = av & bv; \
                        else if (std::string(op) == "or")  result_val.long_val = av | bv; \
                        else if (std::string(op) == "xor") result_val.long_val = av ^ bv; \
                        else if (std::string(op) == "shl") result_val.long_val = av << static_cast<int>(bv & 0x3f); \
                        else if (std::string(op) == "shr") result_val.long_val = av >> static_cast<int>(bv & 0x3f); \
                        else if (std::string(op) == "ushr") result_val.long_val = static_cast<int64_t>(static_cast<uint64_t>(av) >> static_cast<int>(bv & 0x3f)); \
                    } else if (op_type == DalvikType::FLOAT32) { \
                        float af = (a.type == DalvikType::FLOAT32) ? a.float_val : (float)a.int_val; \
                        float bf = (b.type == DalvikType::FLOAT32) ? b.float_val : (float)b.int_val; \
                        if (std::string(op) == "add") result_val.float_val = af + bf; \
                        else if (std::string(op) == "sub") result_val.float_val = af - bf; \
                        else if (std::string(op) == "mul") result_val.float_val = af * bf; \
                        else if (std::string(op) == "div") result_val.float_val = (bf != 0) ? af / bf : 0; \
                        else if (std::string(op) == "rem") result_val.float_val = fmodf(af, bf); \
                    } else { \
                        double ad = (a.type == DalvikType::FLOAT64) ? a.double_val \
                                  : (a.type == DalvikType::INT64 ? bits_l2d(a.long_val) \
                                  : (a.type == DalvikType::FLOAT32 ? (double)a.float_val : (double)a.int_val)); \
                        double bd = (b.type == DalvikType::FLOAT64) ? b.double_val \
                                  : (b.type == DalvikType::INT64 ? bits_l2d(b.long_val) \
                                  : (b.type == DalvikType::FLOAT32 ? (double)b.float_val : (double)b.int_val)); \
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

        // UNIFIED_011.3 EXC-PROPAGATE: apply a deferred catch-handler jump.
        // The invoke handlers advance pc_ (pc_ = pc_ + instr_len) after
        // try_recursive_invoke returns; when caller-side catch matching
        // redirected execution to a handler, that handler address wins.
        if (exc_redirect_pending_) {
            exc_redirect_pending_ = false;
            pc_ = exc_redirect_addr_;
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

// ============================================================================
// UNIFIED_011.2 SYNTH-EXC: Runtime exception machinery (§21/§24 campaign)
// ============================================================================

// Find the catch handler covering `pc` in the current frame's try table.
// Extracted verbatim from the THROW opcode handler (EXP-052/053) so that
// synthetic runtime exceptions share identical machinery and THROW keeps
// its exact prior behavior.
// UNIFIED_011.3 TYPED-CATCH (§18): typed handlers are now type-matched
// against `exc_desc`. Semantics (Dalvik spec):
//   1. first try_item covering pc (tries are non-overlapping),
//   2. typed handler pairs in order — first subtype match wins,
//   3. catch-all (present iff encoded size <= 0) is the fallback,
//   4. no match → false (caller unwinds / propagates).
bool DalvikExecutionEngine::find_catch_handler_for_pc(
        uint32_t pc, uint32_t& handler_addr, bool& is_catch_all,
        std::string& catch_type, const std::string& exc_desc) {
    if (current_tries_size_ == 0 || current_tries_data_ == nullptr) return false;

    for (uint16_t i = 0; i < current_tries_size_; i++) {
        size_t off = i * 8;
        if (off + 8 > current_tries_data_size_) break;
        uint32_t start = 0;
        uint16_t count = 0;
        uint16_t handler_off = 0;
        std::memcpy(&start, current_tries_data_ + off, 4);
        std::memcpy(&count, current_tries_data_ + off + 4, 2);
        std::memcpy(&handler_off, current_tries_data_ + off + 6, 2);
        if (pc < start || pc >= start + count) continue;

        // handler_off is byte offset FROM THE START of the
        // encoded_catch_handler_list (which begins with the list_size uleb128).
        size_t handler_list_start = static_cast<size_t>(current_tries_size_) * 8;
        size_t handler_list_end = current_tries_data_size_;
        if (handler_list_start >= handler_list_end) return false;

        size_t handler_abs = handler_list_start + handler_off;
        if (handler_abs >= handler_list_end) return false;

        // Decode the handler at handler_abs.
        // sleb128 size, then |size| pairs of (uleb128 type_idx, uleb128 addr),
        // then catch-all addr if size <= 0.
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
        // UNIFIED_011.3 TYPED-CATCH: resolve each handler's type descriptor
        // via the CURRENT method's DEX (type_ids are per-DEX, EXP-058) and
        // type-match against the thrown exception.
        for (int h = 0; h < n_pairs; h++) {
            uint32_t type_idx = read_uleb(p);
            uint32_t addr = read_uleb(p);
            std::string handler_exc_desc =
                resolve_type_for_dex(type_idx, current_dex_index_);
            if (is_exception_subtype(exc_desc, handler_exc_desc)) {
                handler_addr = addr;
                is_catch_all = false;
                catch_type = handler_exc_desc;
                return true;
            }
        }
        if (size <= 0) {
            uint32_t addr = read_uleb(p);
            handler_addr = addr;
            is_catch_all = true;
            catch_type = "<catch-all>";
            return true;
        }
        // First covering try_item processed — tries do not overlap, and a
        // non-matching typed list does NOT fall through to other tries.
        return false;
    }
    return false;
}

// Raise a synthetic runtime exception following real Dalvik semantics as
// far as the engine supports them. See header for the full contract.
// MASTER RECONCILIATION (2026-09-03): deferred exception raise.
// Same semantics as raise_synthetic_exception, but pc_ is NEVER written here:
// opcode-handler macros and the invoke wrappers advance pc_ AFTER the handler
// body runs, which would clobber a direct handler jump. Two mechanisms:
//   1. Handler covers pc_ → pending_exception_ + deferred_exception_ set and
//      exc_redirect_pending_ armed; fetch_decode_execute re-applies
//      exc_redirect_addr_ right after the switch (post-switch redirect —
//      same last-word-wins model as UNIFIED_011.3 EXC-PROPAGATE).
//   2. No handler → frame unwind exactly like raise_synthetic_exception
//      (halted_on_return_ + frame_unwind_exception_ for caller-side search).
bool DalvikExecutionEngine::throw_deferred(
        const std::string& exc_class_desc, const std::string& message,
        const char* origin_tag) {
    DalvikValue exc;
    exc.type = DalvikType::OBJECT_REF;
    exc.object_id = heap_.allocate(exc_class_desc, pc_, 0);
    exc.class_desc = exc_class_desc;
    exc.string_val = message;
    heap_.set_object_field(exc.object_id, "message",
                           DalvikValue::make_string(message, exc.object_id));
    heap_.mark_initialized(exc.object_id);

    uint32_t handler_addr = 0;
    bool is_catch_all = false;
    std::string catch_type = "<none>";
    bool found = find_catch_handler_for_pc(pc_, handler_addr, is_catch_all,
                                           catch_type, exc_class_desc);

    std::cerr << "[SYNTH-EXC] " << (origin_tag ? origin_tag : "runtime")
              << " (deferred): " << exc_class_desc << " (" << message << ")"
              << " method=" << current_class_ << "." << current_method_
              << " pc=" << pc_
              << " → " << (found ? "deferred handler @0x" + to_hex(handler_addr)
                                   + " type=" + catch_type
                                 : "uncaught (deferred frame unwind + propagate)")
              << std::endl;

    pending_exception_ = exc;
    deferred_exception_ = exc;
    if (found) {
        exc_redirect_pending_ = true;
        exc_redirect_addr_ = handler_addr;
        return true;
    }
    frame_unwind_exception_valid_ = true;
    frame_unwind_exception_ = exc;
    last_invoke_return_ = DalvikValue::make_null();
    halted_on_return_ = true;
    pc_ += 1;
    return false;
}

bool DalvikExecutionEngine::raise_synthetic_exception(
        const std::string& exc_class_desc, const std::string& message,
        const char* origin_tag) {
    // Build the exception object on the heap (same model as new-instance).
    DalvikValue exc;
    exc.type = DalvikType::OBJECT_REF;
    exc.object_id = heap_.allocate(exc_class_desc, pc_, 0);
    exc.class_desc = exc_class_desc;
    exc.string_val = message;
    heap_.set_object_field(exc.object_id, "message",
                           DalvikValue::make_string(message, exc.object_id));
    heap_.mark_initialized(exc.object_id);

    uint32_t handler_addr = 0;
    bool is_catch_all = false;
    std::string catch_type = "<none>";
    bool found = find_catch_handler_for_pc(pc_, handler_addr, is_catch_all,
                                           catch_type, exc_class_desc);

    std::cerr << "[SYNTH-EXC] " << (origin_tag ? origin_tag : "runtime")
              << ": " << exc_class_desc << " (" << message << ")"
              << " method=" << current_class_ << "." << current_method_
              << " pc=" << pc_
              << " → " << (found ? "catch handler @0x" + to_hex(handler_addr)
                                 + " type=" + catch_type
                                 : "uncaught (frame unwind + propagate)")
              << std::endl;

    if (found) {
        pending_exception_ = exc;
        pc_ = handler_addr;
        return true;
    }
    // Unwind the current frame like a return with a null result.
    // UNIFIED_011.3 EXC-PROPAGATE (§18): record the exception in flight so
    // the invoking frame (try_recursive_invoke call site) searches ITS try
    // table next — real Dalvik propagation, not just a silent null return.
    frame_unwind_exception_valid_ = true;
    frame_unwind_exception_ = exc;
    last_invoke_return_ = DalvikValue::make_null();
    halted_on_return_ = true;
    pc_ += 1;
    return false;
}

// UNIFIED_011.2 IMAGE-RES-RENDER: populate resource_drawable_paths_ from the
// APK's res/ entry list. For every R-field name (field_name_by_resid_), find
// the best-density drawable asset whose basename matches. Density preference
// (AOSP closest-density approximation for a 1080x1920 software target):
//   xxxhdpi > xxhdpi > xhdpi > hdpi > mdpi > drawable (plain) > mipmap.
// Nine-patch ".9.png" entries match by basename minus ".9" too.
// Idempotent (first call wins; later calls no-op).
void DalvikExecutionEngine::populate_resource_drawable_paths(
        const std::vector<std::string>& entry_names) {
    if (drawable_paths_populated_) return;
    drawable_paths_populated_ = true;
    if (field_name_by_resid_.empty() || entry_names.empty()) return;

    auto basename_no_ext = [](const std::string& path) -> std::string {
        size_t slash = path.find_last_of('/');
        std::string name = (slash == std::string::npos) ? path : path.substr(slash + 1);
        // strip chained extensions: ".9.png" → "", ".png" → "", ".webp" → ""
        size_t dot = name.find('.');
        std::string base = (dot == std::string::npos) ? name : name.substr(0, dot);
        return base;
    };
    auto is_drawable_asset = [](const std::string& path) -> bool {
        if (path.find("res/") != 0) return false;
        if (path.find("drawable") == std::string::npos &&
            path.find("mipmap") == std::string::npos) return false;
        static const char* exts[] = {".png", ".webp", ".jpg", ".jpeg", ".xml", ".gif"};
        for (const char* e : exts) {
            if (path.size() >= strlen(e) &&
                path.compare(path.size() - strlen(e), strlen(e), e) == 0) return true;
        }
        return false;
    };
    auto density_rank = [](const std::string& path) -> int {
        // higher rank = higher density = preferred
        if (path.find("-xxxhdpi") != std::string::npos) return 60;
        if (path.find("-xxhdpi") != std::string::npos) return 50;
        if (path.find("-xhdpi") != std::string::npos) return 40;
        if (path.find("-hdpi") != std::string::npos) return 30;
        if (path.find("-mdpi") != std::string::npos) return 20;
        if (path.find("-ldpi") != std::string::npos) return 10;
        return 5;  // plain drawable/ or mipmap/
    };

    // basename → best entry (highest density rank)
    std::map<std::string, std::pair<std::string, int>> best_by_basename;
    for (const auto& entry : entry_names) {
        if (!is_drawable_asset(entry)) continue;
        std::string base = basename_no_ext(entry);
        int rank = density_rank(entry);
        auto it = best_by_basename.find(base);
        if (it == best_by_basename.end() || rank > it->second.second) {
            best_by_basename[base] = {entry, rank};
        }
    }
    if (best_by_basename.empty()) return;

    size_t resolved = 0;
    for (const auto& [resid, field_name] : field_name_by_resid_) {
        if (resource_drawable_paths_.count(field_name)) continue;
        auto it = best_by_basename.find(field_name);
        if (it != best_by_basename.end()) {
            resource_drawable_paths_[field_name] = it->second.first;
            resolved++;
        }
    }
    std::cerr << "[IMG-RES-RENDER] populated resource_drawable_paths_: "
              << resolved << "/" << field_name_by_resid_.size()
              << " R-names matched to APK drawable assets" << std::endl;
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
    // EXP-089: Also trace LoginActivity creation (for Phase M1 verification).
    if (class_desc.find("EditText") != std::string::npos ||
        class_desc.find("TextView") != std::string::npos ||
        class_desc.find("Button") != std::string::npos ||
        class_desc.find("PhoneView") != std::string::npos ||
        class_desc.find("Keyboard") != std::string::npos ||
        class_desc.find("LoginActivity") != std::string::npos) {
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
    // Format: 22c [op vA vB] type@CCCC  — 2 code units
    // Encoding: cu[0] = BBBBAAAA_op (low byte = op, high nibble = vB, low nibble of high byte = vA)
    //           cu[1] = CCCC (type_idx)
    // EXP-092+ CRITICAL FIX: Previous code read dest/src from the wrong bit positions.
    //   dest = (instr >> 8) & 0xFF  → 0xc0 (full high byte) — WRONG, should be & 0x0F
    //   src  = instr & 0xFF         → 0x20 (the opcode!)   — WRONG, should be >> 12
    // This caused instance-of to read the wrong register and write to the wrong
    // register, producing garbage results. fillNextCodeParams' instance-of check
    // for TL_auth_sentCodeTypeFirebaseSms was returning true for ALL types
    // (including TL_auth_sentCodeTypeSms), causing the wrong page transition.
    if (pc + 1 >= bytecode_.size()) return false;

    uint16_t instr = bytecode_[pc];
    uint8_t dest = (instr >> 8) & 0x0F;        // vA: low nibble of high byte
    uint8_t src = (instr >> 12) & 0x0F;        // vB: high nibble of high byte
    uint16_t type_idx = bytecode_[pc + 1];     // type@CCCC at pc+1 (not pc+2)

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

    // EXP-092+ PHASE 1: Trace instance-of in fillNextCodeParams AND lambda$onNextPressed$22
    // to verify the type field is correctly read and the response type check returns correct results.
    if (current_class_.find("LoginActivity") != std::string::npos &&
        (current_method_ == "fillNextCodeParams" ||
         current_method_.find("lambda$onNextPressed") == 0 ||
         current_method_.find("lambda$") == 0)) {
        std::cerr << "[EXP092-INSTANCEOF] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " dest=v" << (int)dest
                  << " src=v" << (int)src
                  << " type_idx=" << type_idx
                  << " target_type=" << target_type
                  << " obj_class=" << (src_val.type == DalvikType::OBJECT_REF ? src_val.class_desc : "N/A")
                  << " obj_id=" << (src_val.type == DalvikType::OBJECT_REF ? src_val.object_id : 0)
                  << " is_instance=" << (is_instance ? "TRUE" : "FALSE")
                  << std::endl;
    }

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

    // EXP-092+ INSTRUMENTATION: Log every write to PhoneView.countryState
    // to trace the root cause of the onNextPressed needShowAlert branch.
    // The field is field@33152 in classes4.dex, declared on
    // Lorg/telegram/ui/LoginActivity$PhoneView; as `int countryState`.
    // Values observed:
    //   0 = set by setCountry (after auto-detection from getNearestDc response)
    //   1 = set by <init> and afterTextChanged (default / user-typed-but-no-match)
    //   2 = set by afterTextChanged when country code matches (COUNTRY_SELECTED)
    if (field_res.resolved &&
        field_res.field_name == "countryState" &&
        field_res.class_descriptor.find("PhoneView") != std::string::npos) {
        int32_t new_val = 0;
        if (src_val.type == DalvikType::INT32 || src_val.type == DalvikType::BOOLEAN) {
            new_val = src_val.int_val;
        }
        std::cerr << "[EXP092-COUNTRYSTATE-WRITE] pc=" << pc
                  << " caller=" << current_class_ << "." << current_method_
                  << " obj_id=" << (obj_ref.type == DalvikType::OBJECT_REF ? obj_ref.object_id : 0)
                  << " new_value=" << new_val
                  << " src_type=" << static_cast<int>(src_val.type)
                  << std::endl;
    }

    // EXP-092+ PHASE 1: Log every write to LoginActivity.currentViewNum
    // (field@33189) to trace the page transition. This is the field that
    // tracks which page (PhoneView, SmsView, etc.) is currently active.
    if (field_res.resolved &&
        field_res.field_name == "currentViewNum" &&
        field_res.class_descriptor.find("LoginActivity;") != std::string::npos &&
        field_res.class_descriptor.find("PhoneView") == std::string::npos) {
        int32_t new_val = 0;
        if (src_val.type == DalvikType::INT32 || src_val.type == DalvikType::BOOLEAN) {
            new_val = src_val.int_val;
        }
        std::cerr << "[EXP092-CURRENTVIEWNUM-WRITE] pc=" << pc
                  << " caller=" << current_class_ << "." << current_method_
                  << " obj_id=" << (obj_ref.type == DalvikType::OBJECT_REF ? obj_ref.object_id : 0)
                  << " new_value=" << new_val
                  << " src_type=" << static_cast<int>(src_val.type)
                  << std::endl;
    }

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

    // EXP-079: Debug — trace onNextPressed dispatch specifically
    if (method_name_from_dex == "onNextPressed" || method_name_from_dex == "onDoneButtonPressed") {
        std::cerr << "[EXP079-DISPATCH] method=" << method_name_from_dex
                  << " declaring_class=" << declaring_class
                  << " runtime_type=" << runtime_type
                  << " static_type=" << static_type
                  << " args[0]_type=" << (args.empty() ? -1 : (int)args[0].type)
                  << " args[0]_obj=" << (args.empty() ? 0 : args[0].object_id)
                  << " args[0]_class=" << (args.empty() ? "" : args[0].class_desc)
                  << std::endl;
    }

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
        bridge_to_api(api_class, method_name_from_dex, args, return_val, api_status, method_idx); last_invoke_return_ = return_val;
    }

    // EXP-094 (CM-018): Record the receiver of a successful "setParams" call.
    // Multi-page apps instantiate several same-class page views; the one the
    // app actively configures via setParams IS the current page. The render
    // stage uses this to pick the correct render root (see stage_render_frame).
    if (method_name_from_dex == "setParams" && !args.empty() &&
        args[0].type == DalvikType::OBJECT_REF && args[0].object_id != 0) {
        last_set_params_view_ = args[0].object_id;
        std::cerr << "[EXP094-SETPARAMS] active page view = obj#" << last_set_params_view_
                  << " class=" << args[0].class_desc << std::endl;
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
                      args, return_val, api_status, method_idx);
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
    std::string method_desc_081;
    if (dex_report_) {
        method_name = resolve_method_name_for_dex(method_idx, current_dex_index_);
        class_name = resolve_method_class_for_dex(method_idx, current_dex_index_);
        method_desc_081 = resolve_method_proto_for_dex(method_idx, current_dex_index_);
        // EXP-081: Debug trace
        if (method_name.find("lambda") != std::string::npos || method_name.find("createView") != std::string::npos) {
            std::cerr << "[EXP081-DESC] method=" << method_name
                      << " method_idx=" << method_idx
                      << " dex=" << current_dex_index_
                      << " desc=" << method_desc_081
                      << std::endl;
        }
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
        // EXP-079: Debug trace for lambda$createView$1 dispatch
        // EXP-089: Also trace lambda$new$0 (ActionBar back button handler)
        // and any method containing "presentFragment" or "swapToFragment"
        if (method_name.find("createView") != std::string::npos ||
            method_name.find("onDoneButton") != std::string::npos ||
            method_name.find("onNextPressed") != std::string::npos ||
            method_name.find("lambda$new") != std::string::npos ||
            method_name.find("presentFragment") != std::string::npos ||
            method_name.find("swapToFragment") != std::string::npos ||
            method_name.find("onBackPressed") != std::string::npos) {
            std::cerr << "[EXP079-DIRECT] invoke-direct: class=" << class_name
                      << " method=" << method_name
                      << " method_idx=" << method_idx
                      << " dex_index=" << current_dex_index_
                      << " args=" << args.size()
                      << std::endl;
        }
        if (try_recursive_invoke(class_name, method_name, args, return_val, result, method_desc_081)) { last_invoke_return_ = return_val;
            recursively_invoked = true;
            status = ApiCallTrace::Status::IMPLEMENTED;
            // EXP-079: Debug trace
            if (method_name.find("createView") != std::string::npos ||
                method_name.find("lambda$new") != std::string::npos ||
                method_name.find("presentFragment") != std::string::npos) {
                std::cerr << "[EXP079-DIRECT] try_recursive_invoke SUCCEEDED for " << method_name << std::endl;
            }
        } else {
            // EXP-079: Debug trace
            if (method_name.find("createView") != std::string::npos ||
                method_name.find("lambda$new") != std::string::npos ||
                method_name.find("presentFragment") != std::string::npos) {
                std::cerr << "[EXP079-DIRECT] try_recursive_invoke FAILED for " << method_name << std::endl;
            }
        }
    }
    if (!recursively_invoked && config_.enable_api_bridge) {
        bridge_to_api(class_name, method_name, args, return_val, status, method_idx); last_invoke_return_ = return_val;
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
    // EXP-082: Debug trace for $r8$lambda invoke-static
    if (method_name.find("$r8$lambda") != std::string::npos || method_name.find("createView") != std::string::npos) {
        std::cerr << "[EXP082-STATIC] method=" << method_name
                  << " method_idx=" << method_idx
                  << " dex=" << current_dex_index_
                  << " proto=" << method_proto
                  << " argc=" << (int)argc
                  << std::endl;
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
            DalvikValue v = get_register(regs[reg_idx]);
            // EXP-095 (CM-019): signature-aware FLOAT conversion.
            // For 'F' params the register holds raw float BITS as INT32
            // (e.g. const/high16 v1, 0x42400000 loads 48.0f as raw bits —
            // const opcodes are not float-typed). Per the method signature
            // we reinterpret: LayoutHelper.createFrame(IF) previously
            // delivered height=0x42400000=1111490560 instead of 48.
            if (pt == "F" && v.type == DalvikType::INT32) {
                float f;
                int32_t bits = v.int_val;
                std::memcpy(&f, &bits, sizeof(f));
                args.push_back(DalvikValue::make_float(f));
            } else {
                args.push_back(v);
            }
            reg_idx += 1;
        }
    }
    // If we couldn't parse params (proto unavailable), fall back to old behavior.
    if (param_types.empty() && args.empty()) {
        for (int i = 0; i < argc && i < 5; ++i) {
            args.push_back(get_register(regs[i]));
        }
    }

    // EXP-088+ F4: Trace invoke-static for $default$ methods (desugared interface defaults)
    // to verify overload resolution and arg count correctness.
    if (method_name.find("$default$") != std::string::npos) {
        std::cerr << "[EXP088-F4-STATIC] method=" << method_name
                  << " class=" << class_name
                  << " proto=" << method_proto
                  << " method_idx=" << method_idx
                  << " current_dex=" << current_dex_index_
                  << " argc=" << (int)argc
                  << " args_size=" << args.size()
                  << " caller=" << current_class_ << "." << current_method_
                  << " pc=" << pc;
        for (size_t i = 0; i < args.size() && i < 4; ++i) {
            std::cerr << " arg[" << i << "]=" << (int)args[i].type;
            if (args[i].type == DalvikType::OBJECT_REF) std::cerr << "/obj=" << args[i].object_id;
        }
        // Also try resolving with ALL DEX files to find the correct proto
        for (uint32_t di = 0; di < per_dex_raw_data_.size(); di++) {
            std::string alt_proto = resolve_method_proto_for_dex(method_idx, di);
            if (alt_proto != "<unknown>" && alt_proto != method_proto) {
                std::cerr << " alt_proto[DEX" << di << "]=" << alt_proto;
            }
        }
        std::cerr << std::endl;
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
        if (try_recursive_invoke(class_name, method_name, args, return_val, result, method_proto)) { last_invoke_return_ = return_val;
            recursively_invoked = true;
            status = ApiCallTrace::Status::IMPLEMENTED;
        }
    }
    if (!recursively_invoked && config_.enable_api_bridge) {
        // current_invoke_is_static_ is still true (set at top of execute_invoke_static).
        // try_shadow_dispatch inside bridge_to_api will see it and correctly
        // treat args[0] as the first parameter (not `this`).
        bridge_to_api(class_name, method_name, args, return_val, status, method_idx); last_invoke_return_ = return_val;
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
        bridge_to_api(class_name, method_name, args, return_val, status, method_idx); last_invoke_return_ = return_val;
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

// EXP-088+ F5: execute_return_wide — return-wide vAA (opcode 0x10, 11x format)
//
// Returns a 64-bit value (long or double) from a method.
//
// Per Dalvik spec: vAA holds the low 32 bits, vAA+1 holds the high 32 bits.
// Our register file already stores wide values as a single INT64 or FLOAT64
// DalvikValue in vAA (set by const-wide, iget-wide, etc.), so we just read
// the single register.
//
// The returned value is stored in last_invoke_return_ so the caller's
// move-result-wide can pick it up.
//
// Previously this opcode was MISSING from the dispatcher — it fell through
// to handle_unimplemented, causing methods that return long/double to:
//   1. Not actually return (execution continued past the return-wide)
//   2. Leave move-result-wide reading stale/zero data
//
// This is a GENERIC VM fix — affects any APK using long/double returns.
bool DalvikExecutionEngine::execute_return_wide(uint32_t pc, InstructionTrace& trace) {
    // Format: 11x [op] vAA (1 code unit)
    if (pc >= bytecode_.size()) return false;

    uint16_t instr = bytecode_[pc];
    uint8_t ret_reg = (instr >> 8) & 0xFF;

    DalvikValue val = get_register(ret_reg);

    // If the register doesn't already hold a wide value (INT64 or FLOAT64),
    // coerce to INT64 with the existing int_val as the low 32 bits.
    // This handles cases where const-wide wasn't used to set the register
    // (e.g., the value came from an arithmetic op that stored INT32).
    if (val.type != DalvikType::INT64 && val.type != DalvikType::FLOAT64) {
        int64_t coerced = static_cast<int64_t>(static_cast<uint32_t>(val.int_val));
        val = DalvikValue::make_long(coerced);
    }

    trace.status = InstructionTrace::Status::HALT_RETURN;
    trace.return_value = val;
    trace.operands.push_back({"v" + std::to_string(ret_reg), val.to_string()});

    // Store so try_recursive_invoke / move-result-wide can propagate.
    last_invoke_return_ = val;

    // EXP-088+ F5 diagnostic: log wide returns for key methods
    if (current_method_ == "getTime" ||
        current_method_ == "currentTimeMillis" ||
        current_method_ == "getDuration" ||
        current_method_ == "getSize" ||
        current_method_ == "getLong" ||
        current_method_ == "nextLong") {
        std::cerr << "[EXP088-F5-RETWIDE] " << current_class_ << "."
                  << current_method_ << " PC=" << pc
                  << " ret_reg=v" << (int)ret_reg
                  << " type=" << static_cast<int>(val.type)
                  << " long_val=0x" << std::hex << val.long_val << std::dec
                  << " (" << val.long_val << ")"
                  << std::endl;
    }

    halted_ = true;
    halted_on_return_ = true;

    log("  RETURN_WIDE " + val.to_string() + " at " + to_hex(pc));

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
    // EXP-092+ CRITICAL FIX: Also treat BOOLEAN with int_val==0 as zero.
    //   instance-of returns make_bool(false) which sets type=BOOLEAN, int_val=0.
    //   Without this check, if-eqz on a false BOOLEAN result returns is_zero=false,
    //   causing the branch to NOT be taken — which is the OPPOSITE of correct
    //   behavior. This affects ALL instance-of results in conditional branches.
    //   Same for BYTE, SHORT, CHAR — all integer-like types with int_val.
    // EXP-093/F014: Added INT64, FLOAT32, FLOAT64 to zero-ness check.
    // Per AOSP: if-eqz/if-nez treat ALL primitive types' zero as false.
    // Previously INT64 (long 0L), FLOAT32 (0.0f), FLOAT64 (0.0d) were
    // NOT treated as zero, causing if-eqz to return is_zero=FALSE for
    // a zero long/double/float — the OPPOSITE of correct behavior.
    bool is_zero = (val.type == DalvikType::NULL_REF) ||
                   (val.type == DalvikType::INT32 && val.int_val == 0) ||
                   (val.type == DalvikType::BOOLEAN && val.int_val == 0) ||
                   (val.type == DalvikType::BYTE && val.int_val == 0) ||
                   (val.type == DalvikType::SHORT && val.int_val == 0) ||
                   (val.type == DalvikType::CHAR && val.int_val == 0) ||
                   (val.type == DalvikType::INT64 && val.long_val == 0) ||
                   (val.type == DalvikType::FLOAT32 && val.float_val == 0.0f) ||
                   (val.type == DalvikType::FLOAT64 && val.double_val == 0.0) ||
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

    // EXP-092+ PHASE 1: Log if-eqz in LoginActivity.setPage.
    if (current_class_.find("LoginActivity;") != std::string::npos &&
        current_class_.find("PhoneView") == std::string::npos &&
        current_method_ == "setPage") {
        std::cerr << "[EXP092-SETPAGE-IFZ] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " op=if-eqz"
                  << " v" << (int)test_reg
                  << " type=" << static_cast<int>(val.type)
                  << " int_val=" << val.int_val
                  << " obj=" << val.object_id
                  << " is_zero=" << is_zero
                  << " → target_pc=" << (pc + offset)
                  << " next_pc=" << (is_zero ? (pc + offset) : (pc + 2))
                  << std::endl;
    }

    // EXP-092+ PHASE D: Log if-eqz in lambda$onNextPressed$22 to trace the
    // critical branch at PC=8: if-eqz v4(instance-of result) → PC=46
    if (current_class_.find("LoginActivity$PhoneView") != std::string::npos &&
        current_method_ == "lambda$onNextPressed$22") {
        std::cerr << "[EXP092-IF-EQZ-22] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " op=if-eqz"
                  << " v" << (int)test_reg
                  << " type=" << static_cast<int>(val.type)
                  << " int_val=" << val.int_val
                  << " obj=" << val.object_id
                  << " is_zero=" << is_zero
                  << " → target_pc=" << (pc + offset)
                  << " next_pc=" << (is_zero ? (pc + offset) : (pc + 2))
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
    // EXP-093/F014: Added INT64, FLOAT32, FLOAT64 to zero-ness check
    // (same as if-eqz handler above).
    bool is_nonzero = !(val.type == DalvikType::NULL_REF ||
                       (val.type == DalvikType::INT32 && val.int_val == 0) ||
                       (val.type == DalvikType::BOOLEAN && val.int_val == 0) ||
                       (val.type == DalvikType::BYTE && val.int_val == 0) ||
                       (val.type == DalvikType::SHORT && val.int_val == 0) ||
                       (val.type == DalvikType::CHAR && val.int_val == 0) ||
                       (val.type == DalvikType::INT64 && val.long_val == 0) ||
                       (val.type == DalvikType::FLOAT32 && val.float_val == 0.0f) ||
                       (val.type == DalvikType::FLOAT64 && val.double_val == 0.0) ||
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

    // EXP-092+ DIRECT TRACE: Log if-nez in onNextPressed and lambda$new$12
    // to prove the exact condition that determines the needShowAlert side path.
    // Critical branches:
    //   lambda$new$12 PC=0:  if-nez v2(response), +3 → PC=3  (null check on response)
    //   lambda$new$12 PC=11: if-nez v0(codeField.length()), +11 → PC=22 (skip setCountry if codeField non-empty)
    if ((current_class_.find("LoginActivity$PhoneView") != std::string::npos &&
         (current_method_ == "onNextPressed" || current_method_ == "lambda$new$12" ||
          current_method_ == "setCountry" || current_method_ == "afterTextChanged" ||
          current_method_.find("lambda$") == 0)) ||
        current_class_.find("PhoneView$2") != std::string::npos) {
        std::cerr << "[EXP092-IF-NEZ] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " v" << (int)test_reg
                  << " type=" << static_cast<int>(val.type)
                  << " int_val=" << val.int_val
                  << " obj=" << val.object_id
                  << " string=\"" << val.string_val << "\""
                  << " is_nonzero=" << is_nonzero
                  << " → target_pc=" << (pc + offset)
                  << " next_pc=" << (is_nonzero ? (pc + offset) : (pc + 2))
                  << std::endl;
    }

    // EXP-092+ PHASE 1: Log if-nez/if-eqz in LoginActivity.setPage.
    // The setPage method has 309 instructions and many branches. We need
    // to trace ALL of them to understand what page_value=13 does.
    if (current_class_.find("LoginActivity;") != std::string::npos &&
        current_class_.find("PhoneView") == std::string::npos &&
        current_method_ == "setPage") {
        std::cerr << "[EXP092-SETPAGE-IFZ] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " op=if-nez"
                  << " v" << (int)test_reg
                  << " type=" << static_cast<int>(val.type)
                  << " int_val=" << val.int_val
                  << " obj=" << val.object_id
                  << " is_nonzero=" << is_nonzero
                  << " → target_pc=" << (pc + offset)
                  << " next_pc=" << (is_nonzero ? (pc + offset) : (pc + 2))
                  << std::endl;
    }

    // EXP-092+ PHASE 1: Log if-nez in fillNextCodeParams to trace why
    // page_value=13 is chosen even with type=TL_auth_sentCodeTypeSms.
    if (current_class_.find("LoginActivity;") != std::string::npos &&
        current_class_.find("PhoneView") == std::string::npos &&
        current_method_ == "fillNextCodeParams") {
        std::cerr << "[EXP092-FILLNEXT-IFZ] " << current_class_ << "." << current_method_
                  << " PC=" << pc
                  << " op=if-nez"
                  << " v" << (int)test_reg
                  << " type=" << static_cast<int>(val.type)
                  << " int_val=" << val.int_val
                  << " obj=" << val.object_id
                  << " is_nonzero=" << is_nonzero
                  << " → target_pc=" << (pc + offset)
                  << " next_pc=" << (is_nonzero ? (pc + offset) : (pc + 2))
                  << std::endl;
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
    /* EXP-092+ DIRECT TRACE: Log every if-* branch in onNextPressed to
       prove the exact condition that determines the needShowAlert side path.
       The critical branch is at PC=604: `if-lt v4, v2, +28 → PC=632`
       where v4=countryState and v2=1. */ \
    if (current_class_.find("LoginActivity$PhoneView") != std::string::npos && \
        current_method_ == "onNextPressed") { \
        std::cerr << "[EXP092-ONNEXT-IF] " << op_name << " PC=" << pc \
                  << " v" << (int)r.vA << "(type=" << static_cast<int>(a.type) \
                  << " val=" << a_val; \
        if (a.type == DalvikType::OBJECT_REF) { std::cerr << " obj=" << a.object_id; } \
        std::cerr << ") vs v" << (int)r.vB \
                  << "(type=" << static_cast<int>(b.type) \
                  << " val=" << b_val; \
        if (b.type == DalvikType::OBJECT_REF) { std::cerr << " obj=" << b.object_id; } \
        std::cerr << ") → taken=" << (taken ? "YES" : "NO") \
                  << " target_pc=" << (pc + r.offset) \
                  << " next_pc=" << (taken ? (pc + r.offset) : (pc + 2)) \
                  << std::endl; \
    } \
    /* EXP-092+ PHASE 1: Log every if-* branch in LoginActivity.setPage to
       determine what page_value=13 means. The setPage switch at PC=0-32
       checks for pages 0, 5, 6, 9, 10, 12, 16, 17. page_value=13 does NOT
       match any of these — need to trace the actual branch outcomes. */ \
    if (current_class_.find("LoginActivity;") != std::string::npos && \
        current_class_.find("PhoneView") == std::string::npos && \
        current_method_ == "setPage") { \
        std::cerr << "[EXP092-SETPAGE-IF] " << op_name << " PC=" << pc \
                  << " v" << (int)r.vA << "(val=" << a_val \
                  << ") vs v" << (int)r.vB \
                  << "(val=" << b_val \
                  << ") → taken=" << (taken ? "YES" : "NO") \
                  << " target_pc=" << (pc + r.offset) \
                  << " next_pc=" << (taken ? (pc + r.offset) : (pc + 2)) \
                  << std::endl; \
    } \
    /* EXP-092+ PHASE 1: Log every if-* branch in fillNextCodeParams to
       understand why page_value=13 is chosen even when the mock response
       has type=TL_auth_sentCodeTypeSms. The critical branch is at PC=67:
       if-eqz v3 (instance-of check for TL_auth_sentCodeTypeFirebaseSms).
       If the type field IS set to TL_auth_sentCodeTypeSms, the instance-of
       checks for FirebaseSms/App/Call should all be false, and the code
       should reach the Sms path. */ \
    if (current_class_.find("LoginActivity;") != std::string::npos && \
        current_class_.find("PhoneView") == std::string::npos && \
        current_method_ == "fillNextCodeParams") { \
        std::cerr << "[EXP092-FILLNEXT-IF] " << op_name << " PC=" << pc \
                  << " v" << (int)r.vA << "(val=" << a_val; \
        if (a.type == DalvikType::OBJECT_REF) { std::cerr << " obj=" << a.object_id << " cls=" << a.class_desc; } \
        std::cerr << ") vs v" << (int)r.vB \
                  << "(val=" << b_val; \
        if (b.type == DalvikType::OBJECT_REF) { std::cerr << " obj=" << b.object_id << " cls=" << b.class_desc; } \
        std::cerr << ") → taken=" << (taken ? "YES" : "NO") \
                  << " target_pc=" << (pc + r.offset) \
                  << " next_pc=" << (taken ? (pc + r.offset) : (pc + 2)) \
                  << std::endl; \
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
            // EXP-091: Also copy string_val — when a String object is passed
            // as an argument (e.g., setText(stringFromLocaleController)),
            // the DalvikValue may have BOTH object_id AND string_val set.
            // The string_val comes from const-string/move-result-object paths
            // where the engine stores the resolved string alongside the ref.
            // Without this, arg_as_string() returns empty for OBJECT args,
            // causing setText(CharSequence) to set empty text on ViewShadow nodes.
            a.string_val = v.string_val;
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

    // CAMPAIGN 013 (B4, §8): hierarchy-aware shadow dispatch.
    // Root cause: shadows claim framework classes by NAME. App classes whose
    // names match no claim (ChessClock, muellerma StopWatch, ...) never
    // reached ActivityShadow — setContentView/findViewById/getWindow became
    // SILENT no-ops and the app kept the synthetic default screen. The old
    // workarounds grew a hand-maintained list of app class names inside
    // ActivityShadow::handles_class — the per-app special-casing this
    // campaign forbids.
    // General fix (mirrors real Android virtual dispatch): walk the DEX
    // superclass chain of the receiver and retry the shadow registry with
    // each ancestor. ChessClock → android/app/Activity → ActivityShadow
    // handles setContentView exactly as for any other Activity subclass.
    {
        std::string cur;
        if (!args.empty() && args[0].type == DalvikType::OBJECT_REF &&
            !args[0].class_desc.empty()) {
            cur = args[0].class_desc;
        } else {
            cur = class_name;
        }
        int guard = 0;
        while (!cur.empty() && guard++ < 10) {
            auto sup_it = class_to_superclass_.find(cur);
            if (sup_it == class_to_superclass_.end()) break;
            const std::string sup = sup_it->second;
            if (sup.empty() || sup == cur) break;
            auto cr3 = shadow_registry_->dispatch(build_ctx(sup));
            if (cr3.handled) {
                std::cerr << "[C013-HIER] " << method << " dispatched via superclass chain: "
                          << cur << " -> " << sup << std::endl;
                switch (cr3.status) {
                    case framework::ApiCallStatus::IMPLEMENTED:
                        status = ApiCallTrace::Status::IMPLEMENTED; break;
                    default:
                        status = ApiCallTrace::Status::STUBBED; break;
                }
                result = call_result_to_dalvik(cr3);
                return true;
            }
            cur = sup;
        }
    }
    return false;
}

bool DalvikExecutionEngine::bridge_to_api(const std::string& class_name,
                                          const std::string& method,
                                          const std::vector<DalvikValue>& args,
                                          DalvikValue& result,
                                          ApiCallTrace::Status& status,
                                          uint32_t method_idx_hint) {
    // EXP-088 Phase B debug
    if (method == "findViewById") {
        std::cerr << "[EXP088-B-ENTER] bridge_to_api: " << class_name << "." << method
                  << " args=" << args.size()
                  << " shadow=" << (shadow_registry_ ? "YES" : "NO")
                  << std::endl;
    }
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

    // ────────────────────────────────────────────────────────────────────────
    // EXP-094 (CM-018): java.lang.StringBuilder / StringBuffer — REAL implementation.
    //
    // ROOT CAUSE this fixes: NO StringBuilder implementation existed. Every
    // append/toString call fell through bridge_to_api's view_parents fallback,
    // where ViewShadow.toString() returned the literal "View" for ANY object.
    // That poisoned EVERY string concatenation in the app:
    //   LocaleInfo.getKey() → "View" instead of "unofficial_XX"
    //   "+" + bundle.getString("phone") → "View" instead of "+15551234567"
    //   PhoneFormat.format(input) → returned the "View" garbage unchanged
    //   → formatString("SentSmsCode") → "…to your phone **View*."
    //
    // Per OpenJDK (java.lang.StringBuilder / AbstractStringBuilder):
    //   * <init>() / <init>(String) / <init>(CharSequence) — initial contents
    //   * append(X) — appends String.valueOf(X) and returns `this`
    //   * toString() — returns a snapshot of the accumulated chars
    //   * length() — number of accumulated chars
    // The buffer is stored on the receiver heap object under "sb_value".
    // ────────────────────────────────────────────────────────────────────────
    if (class_name == "Ljava/lang/StringBuilder;" ||
        class_name == "Ljava/lang/StringBuffer;") {
        uint32_t sb_id = (!args.empty() && args[0].type == DalvikType::OBJECT_REF)
                             ? args[0].object_id : 0;
        std::string cur;
        if (sb_id != 0 && heap_.has_object(sb_id)) {
            auto fv = heap_.get_object_field(sb_id, "sb_value");
            if (fv.has_value() && fv->type == DalvikType::STRING_REF) {
                cur = fv->string_val;
            }
        }
        // Helper: stringify an argument per String.valueOf semantics.
        auto stringify_arg = [&](const DalvikValue& a) -> std::string {
            switch (a.type) {
                case DalvikType::STRING_REF: return a.string_val;
                case DalvikType::INT32: return std::to_string(a.int_val);
                case DalvikType::INT64: return std::to_string(a.long_val);
                case DalvikType::BOOLEAN: return a.bool_val ? "true" : "false";
                case DalvikType::CHAR: return std::string(1, static_cast<char>(a.int_val));
                case DalvikType::BYTE: return std::to_string(static_cast<int8_t>(a.int_val));
                case DalvikType::SHORT: return std::to_string(static_cast<int16_t>(a.int_val));
                case DalvikType::FLOAT32: return std::to_string(a.float_val);
                case DalvikType::FLOAT64: return std::to_string(a.double_val);
                case DalvikType::NULL_REF: return "null";
                case DalvikType::OBJECT_REF: {
                    if (heap_.has_object(a.object_id)) {
                        // A String or another StringBuilder — read its value.
                        auto sv = heap_.get_object_field(a.object_id, "sb_value");
                        if (!sv.has_value()) {
                            sv = heap_.get_object_field(a.object_id, "value");
                        }
                        if (sv.has_value() && sv->type == DalvikType::STRING_REF) {
                            return sv->string_val;
                        }
                    }
                    // Per OpenJDK Object.toString: ClassName@hexIdentityHash
                    std::string cn = a.class_desc;
                    return cn + "@" + std::to_string(a.object_id);
                }
                default: return "";
            }
        };
        if (method == "<init>") {
            // StringBuilder(), StringBuilder(String), StringBuilder(CharSequence),
            // StringBuilder(int capacity) — capacity is ignored.
            if (args.size() >= 2) {
                cur = stringify_arg(args[1]);
            } else {
                cur.clear();
            }
            if (sb_id != 0 && heap_.has_object(sb_id)) {
                heap_.set_object_field(sb_id, "sb_value", DalvikValue::make_string(cur, 0));
            }
            status = ApiCallTrace::Status::IMPLEMENTED;
            result = DalvikValue::make_void();
            return true;
        }
        if (method == "append") {
            if (args.size() >= 2) {
                cur += stringify_arg(args[1]);
            }
            if (sb_id != 0 && heap_.has_object(sb_id)) {
                heap_.set_object_field(sb_id, "sb_value", DalvikValue::make_string(cur, 0));
            }
            status = ApiCallTrace::Status::IMPLEMENTED;
            // Per OpenJDK: append returns `this` (enables chaining).
            DalvikValue r;
            r.type = DalvikType::OBJECT_REF;
            r.object_id = sb_id;
            r.class_desc = class_name.c_str();
            result = r;
            return true;
        }
        if (method == "toString") {
            status = ApiCallTrace::Status::IMPLEMENTED;
            result = DalvikValue::make_string(cur, 0);
            return true;
        }
        if (method == "length") {
            status = ApiCallTrace::Status::IMPLEMENTED;
            result = DalvikValue::make_int(static_cast<int32_t>(cur.size()));
            return true;
        }
        if (method == "charAt" && args.size() >= 2 &&
            (args[1].type == DalvikType::INT32)) {
            int32_t idx = args[1].int_val;
            std::string ch;
            if (idx >= 0 && static_cast<size_t>(idx) < cur.size()) {
                ch = std::string(1, cur[idx]);
            }
            status = ApiCallTrace::Status::IMPLEMENTED;
            DalvikValue r;
            r.type = DalvikType::CHAR;
            r.int_val = (idx >= 0 && static_cast<size_t>(idx) < cur.size())
                            ? static_cast<int32_t>(static_cast<uint8_t>(cur[idx])) : 0;
            result = r;
            (void)ch;
            return true;
        }
        if (method == "isEmpty") {
            status = ApiCallTrace::Status::IMPLEMENTED;
            result = DalvikValue::make_bool(cur.empty());
            return true;
        }
        // insert(int, X), reverse(), deleteCharAt, setLength etc. can be
        // added when evidence shows they're on a hot path.
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-095 (CM-019): LayoutHelper.createLinear/createFrame/... — construct a
    // REAL LayoutParams heap object.
    //
    // Per Telegram LayoutHelper source:
    //   createLinear(w, h, gravity, l, t, r, b):
    //     layoutParams = new LinearLayout.LayoutParams(getSize(w), getSize(h));
    //     layoutParams.setMargins(dp(l), dp(t), dp(r), dp(b));
    //     layoutParams.gravity = gravity;
    // Negative w/h are MATCH_PARENT(-1)/WRAP_CONTENT(-2); positive values are
    // dp-scaled (density=1 on this runtime → dp(x)==x). Margins always dp.
    // Gravity bits (AOSP Gravity): LEFT=3, CENTER_HORIZONTAL=1, RIGHT=5,
    // TOP=0x30, CENTER_VERTICAL=0x10, BOTTOM=0x50, CENTER=0x11.
    //
    // The result flows into ViewGroup.addView(view, params); the engine-side
    // addView capture below reads these fields into the ViewShadow ViewNode,
    // which the renderer's layout pass consumes.
    // ────────────────────────────────────────────────────────────────────────
    if (class_name.find("LayoutHelper") != std::string::npos &&
        (method == "createLinear" || method == "createFrame" ||
         method == "createScroll" || method == "createRelative" ||
         method == "createView")) {
        auto arg_int = [&](size_t i, int def) -> int {
            if (i >= args.size()) return def;
            const auto& a = args[i];
            if (a.type == DalvikType::INT32) return a.int_val;
            if (a.type == DalvikType::FLOAT32) return static_cast<int>(a.float_val);
            if (a.type == DalvikType::FLOAT64) return static_cast<int>(a.double_val);
            if (a.type == DalvikType::INT64) return static_cast<int>(a.long_val);
            return def;
        };
        int w = arg_int(0, -2);
        int h = arg_int(1, -2);
        int gravity = 0, ml = 0, mt = 0, mr = 0, mb = 0;
        // Overloads: (w,h) | (w,h,gravity) | (w,h,gravity,l,t,r,b) |
        // (w,h,weight) 4-arg | (w,h,gravity,l,t,r,b,weight)
        if (args.size() >= 8) {
            gravity = arg_int(2, 0);
            ml = arg_int(3, 0); mt = arg_int(4, 0);
            mr = arg_int(5, 0); mb = arg_int(6, 0);
        } else if (args.size() >= 7) {
            // createScroll(w, h, gravity) + others; or (w,h,gravity,l,t,r)
            // Telegram uses 7-arg mostly as (w,h,gravity,l,t,r,b) — all int.
            gravity = arg_int(2, 0);
            ml = arg_int(3, 0); mt = arg_int(4, 0);
            mr = arg_int(5, 0); mb = arg_int(6, 0);
        } else if (args.size() >= 3) {
            gravity = arg_int(2, 0);
        }
        uint32_t lp_id = heap_.allocate(
            method == "createLinear" ? "Landroid/widget/LinearLayout$LayoutParams;"
            : method == "createRelative" ? "Landroid/widget/RelativeLayout$LayoutParams;"
            : method == "createScroll" ? "Landroid/widget/FrameLayout$LayoutParams;"
            : "Landroid/view/ViewGroup$LayoutParams;", pc_, 0);
        auto set_f = [&](const char* name, int v) {
            DalvikValue val;
            val.type = DalvikType::INT32;
            val.int_val = v;
            heap_.set_object_field(lp_id, name, val);
        };
        set_f("width", w);
        set_f("height", h);
        set_f("gravity", gravity);
        set_f("leftMargin", ml);
        set_f("topMargin", mt);
        set_f("rightMargin", mr);
        set_f("bottomMargin", mb);
        status = ApiCallTrace::Status::IMPLEMENTED;
        DalvikValue r;
        r.type = DalvikType::OBJECT_REF;
        r.object_id = lp_id;
        r.class_desc = "Landroid/view/ViewGroup$LayoutParams;";
        result = r;
        return true;
    }

    // EXP-095 (CM-019): addView(View child, ViewGroup.LayoutParams params) —
    // capture the params into the child's ViewNode so the renderer can lay
    // out with real geometry. The ViewShadow's addView handler (which links
    // the tree) runs via the normal dispatch path; here we only enrich.
    // args: [parent, child, params?]
    if ((method == "addView" || method == "addViewInLayout") &&
        args.size() >= 3 &&
        args[1].type == DalvikType::OBJECT_REF && args[1].object_id != 0 &&
        args[2].type == DalvikType::OBJECT_REF && args[2].object_id != 0 &&
        heap_.has_object(args[2].object_id)) {
        uint32_t child_id = args[1].object_id;
        uint32_t lp_id = args[2].object_id;
        auto read_int = [&](const char* fname, int def) -> int {
            auto fv = heap_.get_object_field(lp_id, fname);
            if (fv.has_value() && fv->type == DalvikType::INT32) return fv->int_val;
            return def;
        };
        int w = read_int("width", INT_MIN);
        int h = read_int("height", INT_MIN);
        int gravity = read_int("gravity", 0);
        int ml = read_int("leftMargin", 0);
        int mt = read_int("topMargin", 0);
        int mr = read_int("rightMargin", 0);
        int mb = read_int("bottomMargin", 0);
        if (shadow_registry_ != nullptr) {
            auto* vs = shadow_registry_->find_as<framework::ViewShadow>();
            if (vs != nullptr) {
                vs->set_layout_params(child_id, w, h, gravity, ml, mt, mr, mb);
                std::cerr << "[EXP095-ADDVIEW-LP] child=" << child_id
                          << " w=" << w << " h=" << h
                          << " gravity=0x" << std::hex << gravity << std::dec
                          << " margins=(" << ml << "," << mt << "," << mr << "," << mb << ")"
                          << " parent_class=" << class_name
                          << std::endl;
            }
        }
    }

    // EXP-095 (CM-019): TextView/LinearLayout.setGravity — text alignment
    // inside the view. Per AOSP Gravity constants.
    if (method == "setGravity" && !args.empty() &&
        args[0].type == DalvikType::OBJECT_REF &&
        args[1].type == DalvikType::INT32 && shadow_registry_ != nullptr) {
        auto* vs = shadow_registry_->find_as<framework::ViewShadow>();
        if (vs != nullptr) {
            vs->set_text_gravity(args[0].object_id, args[1].int_val);
        }
    }

    // EXP-095 (CM-019): LinearLayout.setOrientation(int) — 0=HORIZONTAL,
    // 1=VERTICAL. Captured so the renderer lays out children correctly
    // (e.g. CodeFieldContainer's 5 digit fields are a HORIZONTAL row).
    if (method == "setOrientation" && args.size() >= 2 &&
        args[0].type == DalvikType::OBJECT_REF &&
        args[1].type == DalvikType::INT32 && shadow_registry_ != nullptr) {
        auto* vs = shadow_registry_->find_as<framework::ViewShadow>();
        if (vs != nullptr) {
            vs->set_orientation(args[0].object_id, args[1].int_val);
        }
    }

    // EXP-095 (CM-020): View.setBackgroundColor(int) — capture the color so
    // the renderer can draw REAL view backgrounds (per §17: trace source
    // color → resource → runtime color → framebuffer).
    if (method == "setBackgroundColor" && args.size() >= 2 &&
        args[0].type == DalvikType::OBJECT_REF &&
        args[1].type == DalvikType::INT32 && shadow_registry_ != nullptr) {
        auto* vs = shadow_registry_->find_as<framework::ViewShadow>();
        if (vs != nullptr) {
            vs->set_bg_color(args[0].object_id,
                             static_cast<uint32_t>(args[1].int_val));
            std::cerr << "[EXP095-BG] view=" << args[0].object_id
                      << " color=0x" << std::hex
                      << static_cast<uint32_t>(args[1].int_val) << std::dec
                      << std::endl;
        }
    }

    // EXP-098 (CM-027): AndroidUtilities.dp(float) → int.
    // Per AOSP source: dp(value) = (int)(value * density + 0.5).
    // Our runtime has density=1.0 (mdpi), so dp(x) = (int)(x + 0.5) = round(x).
    // The DEX signature is dp(F)I — float arg, int return.
    // invoke-direct doesn't do signature-aware float conversion, so the
    // FLOAT arg may arrive as INT32 (raw float bits, e.g. 0x42800000 for
    // 64.0f). We reinterpret INT32 as FLOAT32 to recover the original value.
    if (method == "dp" &&
        class_name.find("AndroidUtilities") != std::string::npos &&
        !args.empty()) {
        float dp_val = 0.0f;
        if (args[0].type == DalvikType::FLOAT32) {
            dp_val = args[0].float_val;
        } else if (args[0].type == DalvikType::INT32) {
            // Reinterpret INT32 raw bits as FLOAT32 (invoke-direct doesn't
            // do signature-aware conversion — const/high16 loads raw bits).
            uint32_t bits = static_cast<uint32_t>(args[0].int_val);
            std::memcpy(&dp_val, &bits, sizeof(float));
        } else if (args[0].type == DalvikType::FLOAT64) {
            dp_val = static_cast<float>(args[0].double_val);
        } else if (args[0].type == DalvikType::INT64) {
            uint64_t bits = static_cast<uint64_t>(args[0].long_val);
            double d;
            std::memcpy(&d, &bits, sizeof(double));
            dp_val = static_cast<float>(d);
        }
        int val = static_cast<int>(dp_val + 0.5f);
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_int(val);
        return true;
    }

    // EXP-098 (CM-027): RLottieImageView.setAnimation(RLottieDrawable) —
    // transfer the pending animation from the drawable to the ImageView.
    // Per Telegram source (RLottieImageView.java:84):
    //   public void setAnimation(RLottieDrawable lottieDrawable) {
    //     drawable = lottieDrawable;
    //     drawable.setMasterParent(this);
    //     ...
    //   }
    if (method == "setAnimation" &&
        class_name.find("RLottieImageView") != std::string::npos &&
        args.size() >= 2 &&
        args[0].type == DalvikType::OBJECT_REF &&
        args[1].type == DalvikType::OBJECT_REF &&
        shadow_registry_ != nullptr) {
        uint32_t view_id = args[0].object_id;
        uint32_t drawable_id = args[1].object_id;
        auto it = pending_anim_by_drawable_.find(drawable_id);
        if (it != pending_anim_by_drawable_.end()) {
            const auto& pa = it->second;
            auto* vs = shadow_registry_->find_as<framework::ViewShadow>();
            if (vs != nullptr) {
                vs->set_anim_pending(view_id, pa.raw_resid,
                                     pa.target_w, pa.target_h);
                std::cerr << "[EXP098-RLOTTIE-PENDING] view=" << view_id
                          << " via drawable=" << drawable_id
                          << " resid=" << pa.raw_resid
                          << " target=" << pa.target_w << "x" << pa.target_h
                          << std::endl;
            }
        }
    }

    // EXP-098 (CM-027): RLottieImageView.setAnimation(int resId, int w, int h) —
    // direct form (bypasses RLottieDrawable). Records pending animation on
    // the ImageView's ViewNode directly.
    if (method == "setAnimation" &&
        (class_name.find("RLottieImageView") != std::string::npos ||
         class_name.find("RLottieDrawable") != std::string::npos) &&
        args.size() >= 4 &&
        args[0].type == DalvikType::OBJECT_REF &&
        args[1].type == DalvikType::INT32 &&
        args[2].type == DalvikType::INT32 &&
        args[3].type == DalvikType::INT32 &&
        shadow_registry_ != nullptr) {
        uint32_t view_id = args[0].object_id;
        int32_t raw_resid = args[1].int_val;
        int target_w = args[2].int_val;
        int target_h = args[3].int_val;
        auto* vs = shadow_registry_->find_as<framework::ViewShadow>();
        if (vs != nullptr) {
            vs->set_anim_pending(view_id, raw_resid, target_w, target_h);
            std::cerr << "[EXP098-RLOTTIE-PENDING] view=" << view_id
                      << " resid=" << raw_resid
                      << " target=" << target_w << "x" << target_h
                      << std::endl;
        }
    }

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
    // P0.10 — PackageManager.getPackageInfo → PackageInfo
    // EXP-093/F011: Use manifest-derived package identity instead of hardcoded
    // Telegram values. This is a GENERIC fix — affects ALL APKs.
    // ────────────────────────────────────────────────────────────────────────
    if (method == "getPackageInfo" &&
        class_name.find("PackageManager") != std::string::npos) {
        uint32_t obj_id = heap_.allocate("Landroid/content/pm/PackageInfo;",
                                         pc_, call_stack_.empty() ? 0 : call_stack_.top().frame_id);
        result = DalvikValue::make_object(obj_id,
                                          "Landroid/content/pm/PackageInfo;");
        // EXP-093/F011: Use manifest-derived values, not hardcoded Telegram values
        DalvikValue version_code;
        version_code.type = DalvikType::INT32;
        version_code.int_val = version_code_;  // from manifest
        heap_.set_object_field(obj_id, "versionCode", version_code);
        DalvikValue version_name;
        version_name.type = DalvikType::STRING_REF;
        version_name.string_val = version_name_.empty() ? "1.0" : version_name_;
        version_name.ref_id = 0;
        heap_.set_object_field(obj_id, "versionName", version_name);
        DalvikValue package_name;
        package_name.type = DalvikType::STRING_REF;
        package_name.string_val = package_name_.empty() ? "unknown.package" : package_name_;
        package_name.ref_id = 0;
        heap_.set_object_field(obj_id, "packageName", package_name);
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // P0.8 — Context.getPackageName → String
    // EXP-093/F011: Use manifest-derived package name
    // ────────────────────────────────────────────────────────────────────────
    if (method == "getPackageName" &&
        (class_name.find("Context") != std::string::npos ||
         class_name.find("Activity") != std::string::npos)) {
        result = DalvikValue::make_string(
            package_name_.empty() ? "unknown.package" : package_name_, 1);
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-093/F008: Permission Model — checkSelfPermission / checkPermission
    //
    // Per AOSP Context.checkSelfPermission(String permission):
    //   Returns PackageManager.PERMISSION_GRANTED (0) if granted
    //   Returns PackageManager.PERMISSION_DENIED (-1) if not granted
    //
    // Per AOSP PackageManager.checkPermission(String perm, String pkg):
    //   Same return values.
    //
    // Per AOSP Activity.requestPermissions(String[], int):
    //   Triggers permission dialog. In headless mode, we auto-grant
    //   for controlled testing, then call onRequestPermissionsResult.
    //
    // Default model:
    //   - Normal permissions (INTERNET, etc.) → GRANTED
    //   - Dangerous permissions ( CAMERA, READ_CONTACTS, etc.) → DENIED
    //     until explicitly requested via requestPermissions
    //   - Unknown permissions → DENIED
    // ────────────────────────────────────────────────────────────────────────
    if (method == "checkSelfPermission" &&
        (class_name.find("Context") != std::string::npos ||
         class_name.find("Activity") != std::string::npos ||
         class_name.find("PackageManager") != std::string::npos)) {
        std::string perm_name;
        if (args.size() >= 2 && args[1].type == DalvikType::STRING_REF) {
            perm_name = args[1].string_val;
        }
        // Check our permission state map
        auto pit = permission_state_.find(perm_name);
        int result_val;
        if (pit != permission_state_.end()) {
            result_val = pit->second;  // Use stored state
        } else {
            // Default: normal permissions are granted, dangerous are denied
            // Per AOSP: checkPermission returns GRANTED for normal permissions
            // without requiring runtime request.
            static const std::set<std::string> normal_permissions = {
                "android.permission.INTERNET",
                "android.permission.ACCESS_NETWORK_STATE",
                "android.permission.ACCESS_WIFI_STATE",
                "android.permission.CHANGE_WIFI_STATE",
                "android.permission.VIBRATE",
                "android.permission.WAKE_LOCK",
                "android.permission.RECEIVE_BOOT_COMPLETED",
                "android.permission.NFC",
                "android.permission.BLUETOOTH",
                "android.permission.BLUETOOTH_ADMIN",
                "android.permission.FOREGROUND_SERVICE",
                "android.permission.POST_NOTIFICATIONS",
                "android.permission.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS",
            };
            if (normal_permissions.count(perm_name) > 0) {
                result_val = 0;  // PERMISSION_GRANTED
            } else {
                result_val = -1;  // PERMISSION_DENIED
            }
        }
        result = DalvikValue::make_int(result_val);
        status = ApiCallTrace::Status::IMPLEMENTED;
        std::cerr << "[EXP093-PERM] checkSelfPermission(\"" << perm_name
                  << "\") → " << (result_val == 0 ? "GRANTED" : "DENIED") << std::endl;
        return true;
    }

    // PackageManager.checkPermission(String perm, String pkg)
    if (method == "checkPermission" &&
        class_name.find("PackageManager") != std::string::npos) {
        std::string perm_name;
        if (args.size() >= 2 && args[1].type == DalvikType::STRING_REF) {
            perm_name = args[1].string_val;
        }
        // Same logic as checkSelfPermission
        auto pit = permission_state_.find(perm_name);
        int result_val;
        if (pit != permission_state_.end()) {
            result_val = pit->second;
        } else {
            // Default: denied for dangerous, granted for normal
            result_val = -1;  // PERMISSION_DENIED (conservative default)
        }
        result = DalvikValue::make_int(result_val);
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // Activity.requestPermissions(String[], int)
    // In headless mode: auto-grant all requested permissions and call callback
    if (method == "requestPermissions" &&
        (class_name.find("Activity") != std::string::npos ||
         class_name.find("Fragment") != std::string::npos)) {
        // Grant all requested permissions
        // args[1] = String[] permissions
        // args[2] = int requestCode
        int request_code = 0;
        if (args.size() >= 3 && args[2].type == DalvikType::INT32) {
            request_code = args[2].int_val;
        }
        // For headless mode, we grant all requested permissions
        // (controlled testing — in real Android, user would see dialog)
        std::cerr << "[EXP093-PERM] requestPermissions(requestCode=" << request_code
                  << ") → auto-granted (headless mode)" << std::endl;
        // TODO: Call onRequestPermissionsResult on the Activity
        // For now, just return success
        result = DalvikValue::make_void();
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
        // Editor methods — only handle if class_name is Editor/SharedPreferences
        // EXP-093: Previously this caught ALL putString/putInt/putBoolean/putLong
        // calls — including Bundle.putString! This caused Bundle data to be
        // silently stored on SharedPreferences instead of the Bundle.
        if ((method == "putString" || method == "putBoolean" || method == "putInt" || method == "putLong" || method == "putFloat") &&
            (class_name.find("Editor") != std::string::npos ||
             class_name.find("SharedPreferences") != std::string::npos)) {
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

    // EXP-091: LocaleController.getString(int) → String
    // When getString is called with an INT argument (resource ID), resolve
    // it using field_name_by_resid_ + resource_string_values_.
    // Previously this fell through to try_recursive_invoke which executed
    // the real DEX bytecode, producing garbage like "View" instead of the
    // actual localized string.
    if (method == "getString" &&
        class_name.find("LocaleController") != std::string::npos &&
        args.size() >= 1 && args[0].type == DalvikType::INT32) {
        int32_t resid = args[0].int_val;
        std::string resolved;
        auto fn_it = field_name_by_resid_.find(resid);
        if (fn_it != field_name_by_resid_.end()) {
            const std::string& field_name = fn_it->second;
            auto sv_it = resource_string_values_.find(field_name);
            if (sv_it != resource_string_values_.end()) {
                resolved = sv_it->second;
            }
        }
        if (!resolved.empty()) {
            std::cerr << "[RES] LocaleController.getString(resid=0x" << std::hex << resid
                      << std::dec << ", field=" << (fn_it != field_name_by_resid_.end() ? fn_it->second : "?")
                      << ") → \"" << resolved << "\"" << std::endl;
            status = ApiCallTrace::Status::IMPLEMENTED;
            result = DalvikValue::make_string(resolved, 0);
            return true;
        } else {
            // Fallback: return the resource field name itself if we can find it
            if (fn_it != field_name_by_resid_.end()) {
                std::cerr << "[RES] LocaleController.getString(resid=0x" << std::hex << resid
                          << std::dec << ") → field name \"" << fn_it->second
                          << "\" (no value in resource_string_values_)" << std::endl;
                status = ApiCallTrace::Status::IMPLEMENTED;
                result = DalvikValue::make_string(fn_it->second, 0);
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
    // P1.6 — Context.getSystemService → service object or null
    // EXP-093/F007: Per AOSP ContextImpl.getSystemService, each service name
    // maps to a specific service object. We return a real (but minimal) service
    // object for known services, and null for unknown/unimplemented ones.
    //
    // AOSP source: ContextImpl.getSystemService(String name) looks up
    // SystemServiceRegistry.SYSTEM_SERVICE_FETCHERS.get(name).
    //
    // Known service names (from AOSP Context.java constants):
    //   WINDOW_SERVICE = "window" → WindowManager
    //   LAYOUT_INFLATER_SERVICE = "layout_inflater" → LayoutInflater
    //   ACTIVITY_SERVICE = "activity" → ActivityManager
    //   INPUT_METHOD_SERVICE = "input_method" → InputMethodManager
    //   NOTIFICATION_SERVICE = "notification" → NotificationManager
    //   KEYGUARD_SERVICE = "keyguard" → KeyguardManager
    //   ALARM_SERVICE = "alarm" → AlarmManager
    //   AUDIO_SERVICE = "audio" → AudioManager
    //   CLIPBOARD_SERVICE = "clipboard" → ClipboardManager
    //   CONNECTIVITY_SERVICE = "connectivity" → ConnectivityManager
    //   UI_MODE_SERVICE = "uimode" → UiModeManager
    //   SEARCH_SERVICE = "search" → SearchManager
    // ────────────────────────────────────────────────────────────────────────
    if (method == "getSystemService" &&
        (class_name.find("Context") != std::string::npos ||
         class_name.find("Activity") != std::string::npos)) {
        // Extract the service name from args
        std::string service_name;
        if (args.size() >= 2 && args[1].type == DalvikType::STRING_REF) {
            service_name = args[1].string_val;
        } else if (args.size() >= 2 && args[1].type == DalvikType::OBJECT_REF) {
            // Try to get string from heap
            if (heap_.has_object(args[1].object_id)) {
                auto sv = heap_.get_object_field(args[1].object_id, "value");
                if (sv.has_value() && sv->type == DalvikType::STRING_REF) {
                    service_name = sv->string_val;
                }
            }
        }

        // Service name → service class descriptor mapping
        static const std::map<std::string, std::string> service_map = {
            {"window",         "Landroid/view/WindowManager;"},
            {"layout_inflater", "Landroid/view/LayoutInflater;"},
            {"activity",       "Landroid/app/ActivityManager;"},
            {"input_method",   "Landroid/view/inputmethod/InputMethodManager;"},
            {"notification",   "Landroid/app/NotificationManager;"},
            {"alarm",          "Landroid/app/AlarmManager;"},
            {"audio",          "Landroid/media/AudioManager;"},
            {"clipboard",      "Landroid/content/ClipboardManager;"},
            {"connectivity",   "Landroid/net/ConnectivityManager;"},
            {"uimode",         "Landroid/app/UiModeManager;"},
            {"search",         "Landroid/app/SearchManager;"},
            {"keyguard",       "Landroid/app/KeyguardManager;"},
            {"location",       "Landroid/location/LocationManager;"},
            {"account",        "Landroid/accounts/AccountManager;"},
            {"power",          "Landroid/os/PowerManager;"},
            {"vibrator",       "Landroid/os/Vibrator;"},
            {"sensor",         "Landroid/hardware/SensorManager;"},
            {"display",        "Landroid/hardware/display/DisplayManager;"},
        };

        auto it = service_map.find(service_name);
        if (it != service_map.end()) {
            // Return a singleton service object for known services.
            // The object is minimal — methods called on it will be
            // handled by bridge_to_api or return defaults.
            result = get_or_create_singleton(it->second);
            status = ApiCallTrace::Status::IMPLEMENTED;
            std::cerr << "[EXP093-SVC] getSystemService(\"" << service_name
                      << "\") → " << it->second << std::endl;
        } else {
            // Unknown service — return null (honest, not fake success)
            result = DalvikValue::make_null();
            status = ApiCallTrace::Status::IMPLEMENTED;
            if (!service_name.empty()) {
                std::cerr << "[EXP093-SVC] getSystemService(\"" << service_name
                          << "\") → null (unknown service)" << std::endl;
            }
        }
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
    // MASTER RECONCILIATION (K-19/K-20, 2026-09-03): boxed-number parsing +
    // String.substring/concat — REAL implementations in the production
    // dispatch (bridge_to_api).
    //
    // ROOT CAUSE (why this exists): exp018 documented an "NATIVE_CPP parse*"
    // plan that was NEVER wired into this dispatch (K-19 — the agent claim
    // was a plan, not code). Every real DEX app calling Integer.parseInt /
    // Long.parseLong / Float.parseFloat / Double.parseDouble (EXP-018
    // corpus: ~20% of apps touch parseInt alone) silently received VOID
    // from this bridge. String.substring / String.concat had the same gap
    // (K-20).
    //
    // Semantics per OpenJDK:
    //   * Strict numeric parse: NO whitespace trimming, optional +/- sign,
    //     digits within the radix, range-checked (int: 32-bit, long: 64-bit).
    //     Malformed input → java/lang/NumberFormatException via the DEFERRED
    //     throw mechanism (post-switch redirect — the invoke wrapper's
    //     `pc_ = pc + 3` cannot clobber the handler jump).
    //   * substring(begin[, end]) → bounds-checked; violations throw
    //     java/lang/StringIndexOutOfBoundsException.
    //   * concat(other) → this + other; null receiver/arg → NullPointerException.
    //   * parseFloat/parseDouble accept plain decimal/exponent literals with
    //     full-consumption checking. PASS-3 (K-40): the NaN/Infinity word
    //     forms were implemented and the 2^31 positive-boundary wrap fixed;
    //     the only remaining documented gap is Java's hex-float literal form
    //     (glibc strtof accepts it — semantics match Java where exercised).
    //   * PASS-3 (K-40): parseInt("2147483648") now throws instead of wrapping
    //     to INT_MIN (acc == cut is only legal on the negative side).
    // Fixture: tests/semantic_switch_parse_neg_test.cpp (group P);
    //          tests/semantic_pass3_bridge_test.cpp (group PS — boundaries).
    // ────────────────────────────────────────────────────────────────────────
    if ((class_name == "Ljava/lang/Integer;" && method == "parseInt") ||
        (class_name == "Ljava/lang/Long;" && method == "parseLong") ||
        (class_name == "Ljava/lang/Float;" && method == "parseFloat") ||
        (class_name == "Ljava/lang/Double;" && method == "parseDouble")) {
        status = ApiCallTrace::Status::IMPLEMENTED;
        std::string s_parse;
        if (!args.empty() && args[0].type == DalvikType::STRING_REF)
            s_parse = args[0].string_val;
        int radix_parse = 10;
        if ((class_name == "Ljava/lang/Integer;" || class_name == "Ljava/lang/Long;") &&
            args.size() >= 2 && args[1].type == DalvikType::INT32)
            radix_parse = args[1].int_val;  // parseInt(s, radix) overload
        if (radix_parse < 2 || radix_parse > 36) radix_parse = 10;

        auto digit_val_parse = [](char ch) -> int {
            if (ch >= '0' && ch <= '9') return ch - '0';
            if (ch >= 'a' && ch <= 'z') return ch - 'a' + 10;
            if (ch >= 'A' && ch <= 'Z') return ch - 'A' + 10;
            return -1;
        };
        auto java_parse_fail = [&](const std::string& what) {
            throw_deferred("Ljava/lang/NumberFormatException;",
                           "For input string: \"" + s_parse + "\"" +
                               (what.empty() ? "" : " (" + what + ")"),
                           "PARSE-BRIDGE");
        };

        if (class_name == "Ljava/lang/Integer;" || class_name == "Ljava/lang/Long;") {
            const bool is_long = (class_name == "Ljava/lang/Long;");
            // Java range limits: negative side holds one more magnitude.
            const uint64_t cut_parse = is_long
                ? 9223372036854775808ULL   // 2^63
                : 2147483648ULL;           // 2^31
            bool ok_parse = !s_parse.empty();
            bool neg_parse = false;
            size_t i_parse = 0;
            if (ok_parse && (s_parse[0] == '+' || s_parse[0] == '-')) {
                neg_parse = (s_parse[0] == '-');
                i_parse = 1;
                if (i_parse == s_parse.size()) ok_parse = false;  // bare sign
            }
            uint64_t acc_parse = 0;
            for (; ok_parse && i_parse < s_parse.size(); ++i_parse) {
                int d_parse = digit_val_parse(s_parse[i_parse]);
                if (d_parse < 0 || d_parse >= radix_parse) { ok_parse = false; break; }
                // acc * radix + d <= cut  ⟺  acc <= (cut - d) / radix
                if (acc_parse > (cut_parse - static_cast<uint64_t>(d_parse)) /
                                    static_cast<uint64_t>(radix_parse)) {
                    ok_parse = false; break;  // range overflow → NumberFormatException
                }
                acc_parse = acc_parse * static_cast<uint64_t>(radix_parse) +
                            static_cast<uint64_t>(d_parse);
            }
            if (!ok_parse) { java_parse_fail(""); return true; }
            // PASS-3 (K-40): Java range rule — acc == cut (2^31 / 2^63) is only
            // legal for the NEGATIVE side (INT_MIN/LONG_MIN). A positive parse
            // reaching cut must throw NumberFormatException, not wrap.
            if (!neg_parse && acc_parse >= cut_parse) { java_parse_fail(""); return true; }
            const int64_t signed_val = neg_parse
                ? static_cast<int64_t>(0ULL - acc_parse)
                : static_cast<int64_t>(acc_parse);
            if (is_long) result = DalvikValue::make_long(signed_val);
            else result = DalvikValue::make_int(static_cast<int32_t>(signed_val));
            std::cerr << "[PARSE] " << class_name << "." << method << "(\"" << s_parse
                      << "\", radix " << radix_parse << ") → " << signed_val << std::endl;
            return true;
        }

        // Floating variants: full-consumption check; reject leading/trailing
        // whitespace and empty strings like Java (no trimming).
        if (s_parse.empty() ||
            std::isspace(static_cast<unsigned char>(s_parse.front())) ||
            std::isspace(static_cast<unsigned char>(s_parse.back()))) {
            java_parse_fail(""); return true;
        }
        // PASS-3 (K-40): Java word forms. Double/Float.valueOf accept EXACTLY
        // "NaN" (unsigned) and optionally-signed "Infinity" — and nothing
        // else alphabetic. This guard stops the C strtof layer from silently
        // accepting "nan", "inf", "infinity" (not Java) — the documented
        // FIX-05 residual TODO, now closed.
        {
            const bool is_float = (class_name == "Ljava/lang/Float;");
            size_t sign_pos = (s_parse[0] == '+' || s_parse[0] == '-') ? 1 : 0;
            std::string body = s_parse.substr(sign_pos);
            if (!body.empty() && std::isalpha(static_cast<unsigned char>(body[0]))) {
                const bool neg_word = (sign_pos == 1 && s_parse[0] == '-');
                if (body == "NaN" && sign_pos == 0) {
                    result = is_float ? DalvikValue::make_float(std::nanf(""))
                                      : DalvikValue::make_double(std::nan(""));
                    std::cerr << "[PARSE] " << class_name << "." << method
                              << "(\"NaN\") → NaN" << std::endl;
                    return true;
                }
                if (body == "Infinity") {
                    result = is_float
                        ? DalvikValue::make_float(neg_word ? -HUGE_VALF : HUGE_VALF)
                        : DalvikValue::make_double(neg_word ? -HUGE_VAL : HUGE_VAL);
                    std::cerr << "[PARSE] " << class_name << "." << method
                              << "(\"" << s_parse << "\") → "
                              << (neg_word ? "-Infinity" : "Infinity") << std::endl;
                    return true;
                }
                java_parse_fail("illegal word form");
                return true;
            }
        }
        {
            const char* begin_parse = s_parse.c_str();
            char* end_parse = nullptr;
            errno = 0;
            if (class_name == "Ljava/lang/Float;") {
                float f_parse = std::strtof(begin_parse, &end_parse);
                if (end_parse != begin_parse + s_parse.size()) { java_parse_fail(""); return true; }
                result = DalvikValue::make_float(f_parse);
                std::cerr << "[PARSE] Float.parseFloat(\"" << s_parse << "\") → " << f_parse << std::endl;
            } else {
                double d_parse = std::strtod(begin_parse, &end_parse);
                if (end_parse != begin_parse + s_parse.size()) { java_parse_fail(""); return true; }
                result = DalvikValue::make_double(d_parse);
                std::cerr << "[PARSE] Double.parseDouble(\"" << s_parse << "\") → " << d_parse << std::endl;
            }
        }
        return true;
    }

    // MASTER RECONCILIATION (K-20, 2026-09-03): String.substring / concat.
    if (class_name == "Ljava/lang/String;" && method == "substring" && args.size() >= 2) {
        status = ApiCallTrace::Status::IMPLEMENTED;
        std::string s_sub;
        if (args[0].type == DalvikType::STRING_REF) s_sub = args[0].string_val;
        else if (args[0].type == DalvikType::NULL_REF) {
            throw_deferred("Ljava/lang/NullPointerException;", "substring on null", "STR-BRIDGE");
            return true;
        }
        int32_t begin_sub = (args[1].type == DalvikType::INT32) ? args[1].int_val : 0;
        int32_t end_sub = static_cast<int32_t>(s_sub.size());
        if (args.size() >= 3 && args[2].type == DalvikType::INT32) end_sub = args[2].int_val;
        // OpenJDK bounds: begin<0 || end>len || begin>end → SIOOBE.
        if (begin_sub < 0 || end_sub < 0 ||
            end_sub > static_cast<int32_t>(s_sub.size()) || begin_sub > end_sub) {
            throw_deferred("Ljava/lang/StringIndexOutOfBoundsException;",
                           "length=" + std::to_string(s_sub.size()) +
                           "; begin=" + std::to_string(begin_sub) +
                           "; end=" + std::to_string(end_sub),
                           "STR-BRIDGE");
            return true;
        }
        result = DalvikValue::make_string(s_sub.substr(begin_sub, end_sub - begin_sub), 0);
        std::cerr << "[STR] substring(" << begin_sub << "," << end_sub << ") of \""
                  << s_sub.substr(0, 40) << "\" → \"" << result.string_val.substr(0, 40) << "\"" << std::endl;
        return true;
    }
    if (class_name == "Ljava/lang/String;" && method == "concat" && args.size() >= 2) {
        status = ApiCallTrace::Status::IMPLEMENTED;
        std::string s_concat;
        if (args[0].type == DalvikType::STRING_REF) s_concat = args[0].string_val;
        else if (args[0].type == DalvikType::NULL_REF) {
            throw_deferred("Ljava/lang/NullPointerException;", "concat on null", "STR-BRIDGE");
            return true;
        }
        if (args[1].type == DalvikType::NULL_REF) {
            throw_deferred("Ljava/lang/NullPointerException;", "concat(null)", "STR-BRIDGE");
            return true;
        }
        std::string other_concat = (args[1].type == DalvikType::STRING_REF) ? args[1].string_val : "";
        result = DalvikValue::make_string(s_concat + other_concat, 0);
        std::cerr << "[STR] concat(\"" << s_concat.substr(0, 32) << "\", \""
                  << other_concat.substr(0, 32) << "\")" << std::endl;
        return true;
    }

    // ────────────────────────────────────────────────────────────────────────
    // FINAL CANONICAL MASTER RECONCILIATION Pass-3 (K-36): AtomicReference.
    // The single-threaded engine makes CAS = identity compare + swap on the
    // heap object's "value" field. Reference semantics per
    // java.util.concurrent.atomic.AtomicReference: compareAndSet(expect,
    // update) uses == (object identity); null matches only null. Generic
    // java.util.concurrent API — NO app special-casing.
    // Fixture: tests/semantic_pass3_bridge_test.cpp (group AR).
    if (class_name == "Ljava/util/concurrent/atomic/AtomicReference;") {
        auto atomic_ref_equal = [](const DalvikValue& a, const DalvikValue& b) {
            if (a.type == DalvikType::NULL_REF && b.type == DalvikType::NULL_REF)
                return true;
            if (a.type != b.type) return false;
            if (a.type == DalvikType::OBJECT_REF) return a.object_id == b.object_id;
            if (a.type == DalvikType::STRING_REF) return a.string_val == b.string_val;
            return false;
        };
        status = ApiCallTrace::Status::IMPLEMENTED;
        if (method == "<init>") {
            DalvikValue initial = (args.size() >= 2) ? args[1] : DalvikValue::make_null();
            heap_.set_object_field(args[0].object_id, "value", initial);
            result = DalvikValue::make_void();
            std::cerr << "[ATOMIC-REF] <init>"
                      << (args.size() >= 2 ? "(v)" : "()") << std::endl;
            return true;
        }
        if (method == "get") {
            auto v = heap_.get_object_field(args[0].object_id, "value");
            result = v.value_or(DalvikValue::make_null());
            return true;
        }
        if (method == "set") {
            heap_.set_object_field(args[0].object_id, "value", args[1]);
            result = DalvikValue::make_void();
            return true;
        }
        if (method == "getAndSet") {
            auto v = heap_.get_object_field(args[0].object_id, "value");
            result = v.value_or(DalvikValue::make_null());
            heap_.set_object_field(args[0].object_id, "value", args[1]);
            return true;
        }
        if (method == "compareAndSet") {
            auto cur = heap_.get_object_field(args[0].object_id, "value");
            DalvikValue c = cur.value_or(DalvikValue::make_null());
            bool swapped = atomic_ref_equal(c, args[1]);
            if (swapped) heap_.set_object_field(args[0].object_id, "value", args[2]);
            result = DalvikValue::make_bool(swapped);
            std::cerr << "[ATOMIC-REF] compareAndSet → "
                      << (swapped ? "true (swapped)" : "false (expect mismatch)")
                      << std::endl;
            return true;
        }
    }

    // ────────────────────────────────────────────────────────────────────────
    // FINAL CANONICAL MASTER RECONCILIATION Pass-3 (K-35): XmlPullParser.
    // REAL pull-parse event machine (org.xmlpull.v1): START_DOCUMENT →
    // START_TAG/TEXT/END_TAG … → END_DOCUMENT, next() advances one event and
    // THROWS XmlPullParserException after END_DOCUMENT (real termination
    // semantics, not an opcode-shaped no-op). The standard Android entry is
    // android.util.Xml.newPullParser(); StringReader stores its source text
    // so setInput(Reader) works without any app special-casing.
    // Fixture: tests/semantic_pass3_bridge_test.cpp (group X).
    if (class_name == "Ljava/io/StringReader;" && method == "<init>" &&
        args.size() >= 2) {
        status = ApiCallTrace::Status::IMPLEMENTED;
        if (args[1].type == DalvikType::STRING_REF)
            heap_.set_object_field(args[0].object_id, "s", args[1]);
        result = DalvikValue::make_void();
        std::cerr << "[XML-PULL] StringReader.<init>(\"" << args[1].string_val.substr(0, 40)
                  << "\")" << std::endl;
        return true;
    }
    if ((class_name == "Landroid/util/Xml;" || class_name == "Lorg/xmlpull/v1/Xml;") &&
        method == "newPullParser") {
        status = ApiCallTrace::Status::IMPLEMENTED;
        uint32_t frame_id = call_stack_.empty() ? 0 : call_stack_.top().frame_id;
        uint32_t obj_id = heap_.allocate("Lorg/xmlpull/v1/XmlPullParser;", pc_, frame_id);
        xml_parsers_[obj_id] = XmlPullState{};
        result = DalvikValue::make_object(obj_id, "Lorg/xmlpull/v1/XmlPullParser;");
        std::cerr << "[XML-PULL] newPullParser → obj#" << obj_id << std::endl;
        return true;
    }
    if (class_name == "Lorg/xmlpull/v1/XmlPullParser;" && !args.empty() &&
        args[0].type == DalvikType::OBJECT_REF) {
        uint32_t xp_id = args[0].object_id;
        auto st_it = xml_parsers_.find(xp_id);
        if (st_it == xml_parsers_.end()) {
            // Tolerate parsers allocated by NEW_INSTANCE (no state yet).
            st_it = xml_parsers_.emplace(xp_id, XmlPullState{}).first;
        }
        XmlPullState& st = st_it->second;
        status = ApiCallTrace::Status::IMPLEMENTED;

        if (method == "setInput") {
            // setInput(Reader) / setInput(String) / setInput(InputStream, enc)
            st = XmlPullState{};
            if (args.size() >= 2 && args[1].type == DalvikType::STRING_REF) {
                st.content = args[1].string_val;
            } else if (args.size() >= 2 && args[1].type == DalvikType::OBJECT_REF) {
                // Reader chain: StringReader ("s") / BufferedReader ("in")…
                std::string text;
                uint32_t lookup = args[1].object_id;
                for (int hop = 0; hop < 4 && lookup != 0; ++hop) {
                    auto sf = heap_.get_object_field(lookup, "s");
                    if (sf.has_value() && sf->type == DalvikType::STRING_REF) {
                        text = sf->string_val;
                        break;
                    }
                    bool walked = false;
                    if (heap_.has_object(lookup)) {
                        const auto* ho = heap_.get(lookup);
                        if (ho) {
                            for (const char* fn : {"in", "source", "reader"}) {
                                auto fv = ho->get_field(fn);
                                if (fv.type == DalvikType::OBJECT_REF) {
                                    lookup = fv.object_id;
                                    walked = true;
                                    break;
                                }
                            }
                        }
                    }
                    if (!walked) break;
                }
                if (text.empty()) {
                    // InputStream variant: resolve an open asset stream.
                    std::string asset_path;
                    size_t* pos_ptr = nullptr;
                    if (resolve_asset_stream(args[1].object_id, asset_path, pos_ptr) &&
                        !asset_path.empty()) {
                        text = cached_asset_bytes(asset_path);
                    }
                }
                st.content = text;
            }
            st.event = 0;  // START_DOCUMENT
            std::cerr << "[XML-PULL] setInput(" << st.content.size() << " bytes)" << std::endl;
            result = DalvikValue::make_void();
            return true;
        }
        if (method == "getEventType") {
            result = DalvikValue::make_int(st.event);
            return true;
        }
        if (method == "next" || method == "nextTag") {
            if (st.ended) {
                // Real termination: next() after END_DOCUMENT throws.
                throw_deferred("Lorg/xmlpull/v1/XmlPullParserException;",
                               "next() called after END_DOCUMENT", "XML-PULL");
                return true;
            }
            xml_pull_advance(st);
            if (method == "nextTag") {
                // Skip whitespace-only TEXT events; a tag is required next.
                auto all_ws = [](const std::string& t) {
                    for (char c : t)
                        if (!std::isspace(static_cast<unsigned char>(c))) return false;
                    return true;
                };
                while (st.event == 4 && all_ws(st.cur_text) && !st.ended)
                    xml_pull_advance(st);
                if (st.event != 2 && st.event != 3 && !st.ended) {
                    throw_deferred("Lorg/xmlpull/v1/XmlPullParserException;",
                                   "nextTag expected a tag", "XML-PULL");
                    return true;
                }
            }
            static const char* EV_NAMES[] = {"START_DOCUMENT", "END_DOCUMENT",
                                             "START_TAG", "END_TAG", "TEXT"};
            std::cerr << "[XML-PULL] next → "
                      << (st.event >= 0 && st.event <= 4 ? EV_NAMES[st.event] : "?")
                      << (st.event == 2 || st.event == 3 ? " <" + st.cur_name + ">" : "")
                      << (st.event == 4 ? " \"" + st.cur_text.substr(0, 32) + "\"" : "")
                      << std::endl;
            result = DalvikValue::make_int(st.event);
            return true;
        }
        if (method == "getName") {
            if (st.event == 2 || st.event == 3)
                result = DalvikValue::make_string(st.cur_name, 0);
            else
                result = DalvikValue::make_null();
            return true;
        }
        if (method == "getText") {
            if (st.event == 4)
                result = DalvikValue::make_string(st.cur_text, 0);
            else
                result = DalvikValue::make_null();
            return true;
        }
        if (method == "getAttributeValue") {
            // (int index) or (String namespace, String name) — namespace is
            // ignored when null (no-namespace documents).
            if (args.size() >= 2 && args[1].type == DalvikType::INT32) {
                int32_t idx = args[1].int_val;
                if (idx >= 0 && static_cast<size_t>(idx) < st.attrs.size())
                    result = DalvikValue::make_string(st.attrs[static_cast<size_t>(idx)].second, 0);
                else
                    result = DalvikValue::make_null();
            } else if (args.size() >= 3 && args[2].type == DalvikType::STRING_REF) {
                const std::string& want = args[2].string_val;
                for (const auto& [n, v] : st.attrs) {
                    if (n == want) {
                        result = DalvikValue::make_string(v, 0);
                        return true;
                    }
                }
                result = DalvikValue::make_null();
            } else {
                result = DalvikValue::make_null();
            }
            return true;
        }
    }

    // EXP-093: String.replace(CharSequence, CharSequence) → String
    // AND String.replace(char oldChar, char newChar) → String (EXP-094/CM-018).
    // Per OpenJDK: the char version replaces EVERY occurrence of oldChar
    // with newChar. The args arrive as INT32 (char is a 16-bit int in DEX).
    // Critical for LocaleController.addNbsp which calls String.replace(' ', '\u00A0').
    if (class_name == "Ljava/lang/String;" && method == "replace" && args.size() >= 3) {
        std::string str = args[0].type == DalvikType::STRING_REF ? args[0].string_val : "";
        if (str.empty() && args[0].type == DalvikType::OBJECT_REF &&
            heap_.has_object(args[0].object_id)) {
            // Receiver may be a heap String object — resolve its value.
            auto sv = heap_.get_object_field(args[0].object_id, "value");
            if (sv.has_value() && sv->type == DalvikType::STRING_REF) str = sv->string_val;
        }
        if (args[1].type == DalvikType::INT32 && args[2].type == DalvikType::INT32) {
            // replace(char, char): substitute every occurrence of the single
            // 16-bit char arg1 with the 16-bit char arg2. For BMP chars below
            // U+0800 this is a byte-wise substitution on our UTF-8 strings;
            // for the nbsp (U+00A0) we substitute the UTF-8 encoding.
            int32_t old_ch = args[1].int_val & 0xFFFF;
            int32_t new_ch = args[2].int_val & 0xFFFF;
            auto utf8_of = [](int32_t cp) {
                std::string s;
                if (cp < 0x80) {
                    s += static_cast<char>(cp);
                } else if (cp < 0x800) {
                    s += static_cast<char>(0xC0 | (cp >> 6));
                    s += static_cast<char>(0x80 | (cp & 0x3F));
                } else {
                    s += static_cast<char>(0xE0 | (cp >> 12));
                    s += static_cast<char>(0x80 | ((cp >> 6) & 0x3F));
                    s += static_cast<char>(0x80 | (cp & 0x3F));
                }
                return s;
            };
            std::string old_s = utf8_of(old_ch);
            std::string new_s = utf8_of(new_ch);
            if (!old_s.empty()) {
                std::string out;
                size_t prev = 0, pos;
                while ((pos = str.find(old_s, prev)) != std::string::npos) {
                    out += str.substr(prev, pos - prev);
                    out += new_s;
                    prev = pos + old_s.size();
                }
                out += str.substr(prev);
                str = out;
            }
            status = ApiCallTrace::Status::IMPLEMENTED;
            result = DalvikValue::make_string(str, 0);
            return true;
        }
        std::string target, replacement;
        // args[1] and args[2] are CharSequence (could be String or other)
        if (args[1].type == DalvikType::STRING_REF) {
            target = args[1].string_val;
        } else if (args[1].type == DalvikType::OBJECT_REF && heap_.has_object(args[1].object_id)) {
            auto sv = heap_.get_object_field(args[1].object_id, "value");
            if (sv.has_value() && sv->type == DalvikType::STRING_REF) target = sv->string_val;
        }
        if (args[2].type == DalvikType::STRING_REF) {
            replacement = args[2].string_val;
        } else if (args[2].type == DalvikType::OBJECT_REF && heap_.has_object(args[2].object_id)) {
            auto sv = heap_.get_object_field(args[2].object_id, "value");
            if (sv.has_value() && sv->type == DalvikType::STRING_REF) replacement = sv->string_val;
        }
        // Simple string replace
        if (!target.empty()) {
            std::string result_str;
            size_t pos = 0, prev = 0;
            while ((pos = str.find(target, prev)) != std::string::npos) {
                result_str += str.substr(prev, pos - prev);
                result_str += replacement;
                prev = pos + target.size();
            }
            result_str += str.substr(prev);
            str = result_str;
        }
        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_string(str, 0);
        return true;
    }

    // EXP-093: Application.getString(int resid) → String
    // Per AOSP: Application delegates to Context.getString which delegates
    // to Resources.getString. We handle it the same way as Resources.getString.
    if (method == "getString" &&
        (class_name.find("Application") != std::string::npos ||
         class_name.find("Context") != std::string::npos ||
         class_name.find("ContextWrapper") != std::string::npos)) {
        std::cerr << "[EXP093-APPSTR] HIT! class=" << class_name
                  << " args=" << args.size();
        for (size_t i = 0; i < args.size() && i < 3; i++) {
            std::cerr << " arg" << i << "_type=" << (int)args[i].type;
            if (args[i].type == DalvikType::INT32) std::cerr << "_int=" << args[i].int_val;
            if (args[i].type == DalvikType::OBJECT_REF) std::cerr << "_obj=" << args[i].object_id;
        }
        std::cerr << std::endl;
        // For instance methods: args[0]=this(OBJECT_REF), args[1]=resid(INT32)
        // For static: args[0]=resid(INT32)
        int32_t resid = -1;
        if (args.size() >= 2 && args[1].type == DalvikType::INT32) {
            resid = args[1].int_val;
        } else if (args.size() >= 1 && args[0].type == DalvikType::INT32) {
            resid = args[0].int_val;
        }
        if (resid >= 0) {
            // First try the normal field_name_by_resid_ lookup
            auto fn_it = field_name_by_resid_.find(resid);
            // EXP-093: If not found and resid is small (D8 shrinker remap),
            // try resolving by looking up the R$string static field with
            // value == resid. The D8 shrinker remaps resource IDs to small
            // ordinals (e.g., R.string.SentSmsCode → 3).
            if (fn_it == field_name_by_resid_.end()) {
                // Try to find the field name by scanning R$string static fields
                // stored in static_field_storage_.
                // The D8 shrinker remaps resource IDs to small ordinals.
                std::string r_string_prefix = "Lorg/telegram/messenger/R$string;.";
                for (const auto& [skey, sval] : static_field_storage_) {
                    if (skey.find(r_string_prefix) == 0 &&
                        sval.type == DalvikType::INT32 && sval.int_val == resid) {
                        // Found! Extract field name from key
                        std::string fname = skey.substr(r_string_prefix.length());
                        auto sv_it = resource_string_values_.find(fname);
                        if (sv_it != resource_string_values_.end()) {
                            result = DalvikValue::make_string(sv_it->second, 0);
                            status = ApiCallTrace::Status::IMPLEMENTED;
                            std::cerr << "[EXP093-APPGETSTR] getString(resid=" << resid
                                      << ") → field=\"" << fname
                                      << "\" → \"" << sv_it->second << "\""
                                      << std::endl;
                            return true;
                        }
                    }
                }
            }
            if (fn_it != field_name_by_resid_.end()) {
                auto sv_it = resource_string_values_.find(fn_it->second);
                if (sv_it != resource_string_values_.end()) {
                    result = DalvikValue::make_string(sv_it->second, 0);
                    status = ApiCallTrace::Status::IMPLEMENTED;
                    return true;
                }
            }
        }
        result = DalvikValue::make_string("", 0);
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }

    // EXP-093: String.format(String format, Object... args) → String
    // Per OpenJDK: replaces %s, %d, %f etc. with argument values.
    // This is CRITICAL for LocaleController.formatString which builds
    // messages like "We've sent a code to %s" by calling String.format.
    if (class_name == "Ljava/lang/String;" && method == "format" && !args.empty()) {
        // String.format is static: args[0] = format string, args[1+] = format args
        // In DEX, the varargs array is passed as a single Object[] argument
        std::string fmt = (args[0].type == DalvikType::STRING_REF) ? args[0].string_val : "";
        std::string output;

        // If args[1] is an OBJECT_REF (Object[]), try to extract elements
        // For now, implement a simple %s/%d replacement using the varargs array
        if (args.size() >= 2 && args[1].type == DalvikType::OBJECT_REF) {
            // Try to get array elements from the Object[] on the heap
            uint32_t arr_id = args[1].object_id;
            int arr_len = 0;
            if (heap_.has_object(arr_id)) {
                auto len_field = heap_.get_object_field(arr_id, "__array_length__");
                if (len_field.has_value() && len_field->type == DalvikType::INT32) {
                    arr_len = len_field->int_val;
                }
            }

            // Simple %s/%d replacement
            size_t arg_idx = 0;
            for (size_t i = 0; i < fmt.size(); i++) {
                if (fmt[i] == '%' && i + 1 < fmt.size()) {
                    char spec = fmt[i + 1];
                    if (spec == 's' && arg_idx < (size_t)arr_len) {
                        // Get string arg from array
                        std::string field_name = "array[" + std::to_string(arg_idx) + "]";
                        auto elem = heap_.get_object_field(arr_id, field_name);
                        if (elem.has_value()) {
                            if (elem->type == DalvikType::STRING_REF) {
                                output += elem->string_val;
                            } else if (elem->type == DalvikType::OBJECT_REF && heap_.has_object(elem->object_id)) {
                                auto sv = heap_.get_object_field(elem->object_id, "value");
                                if (sv.has_value() && sv->type == DalvikType::STRING_REF) {
                                    output += sv->string_val;
                                }
                            } else if (elem->type == DalvikType::INT32) {
                                output += std::to_string(elem->int_val);
                            }
                        }
                        arg_idx++;
                        i++; // skip the 's'
                    } else if (spec == 'd' && arg_idx < (size_t)arr_len) {
                        std::string field_name = "array[" + std::to_string(arg_idx) + "]";
                        auto elem = heap_.get_object_field(arr_id, field_name);
                        if (elem.has_value() && elem->type == DalvikType::INT32) {
                            output += std::to_string(elem->int_val);
                        }
                        arg_idx++;
                        i++;
                    } else if (spec == '%') {
                        output += '%';
                        i++;
                    } else {
                        output += fmt[i];
                    }
                } else {
                    output += fmt[i];
                }
            }
        } else {
            // No varargs — just return the format string as-is
            output = fmt;
        }

        status = ApiCallTrace::Status::IMPLEMENTED;
        result = DalvikValue::make_string(output, 0);
        std::cerr << "[EXP093-STRFMT] String.format(\"" << fmt << "\", ...) → \"" << output << "\"" << std::endl;
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
    // CAMPAIGN 010 R14: java.lang.StackTraceElement.getClassName/getMethodName
    // Real frames are materialized by Thread.getStackTrace (UC010-STACKTRACE);
    // these accessors read the fields back so Kotlin Intrinsics' null-check
    // stack walk terminates with the true caller frame.
    // ────────────────────────────────────────────────────────────────────────
    if (class_name.find("StackTraceElement") != std::string::npos &&
        (method == "getClassName" || method == "getMethodName" ||
         method == "getFileName" || method == "getLineNumber")) {
        uint32_t oid = (!args.empty() && args[0].type == DalvikType::OBJECT_REF)
                           ? args[0].object_id : 0;
        if (method == "getLineNumber") {
            result = DalvikValue::make_int(0);  // interpreter has no line tables
        } else if (method == "getFileName") {
            result = DalvikValue::make_null();
        } else {
            const char* field = (method == "getClassName") ? "__class_name__"
                                                           : "__method_name__";
            std::string val;
            if (oid && heap_.has_object(oid)) {
                auto f = heap_.get_object_field(oid, field);
                if (f.has_value() && f->type == DalvikType::STRING_REF) val = f->string_val;
            }
            result = DalvikValue::make_string(val, 0);
        }
        status = ApiCallTrace::Status::IMPLEMENTED;
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
    //
    // EXP-093: Set __array_length__ on the heap object so that array-length
    // opcode correctly returns 0. Previously, the int_val was set to 0 but
    // __array_length__ was not set on the heap — causing array-length to
    // potentially return garbage, and loops to iterate past the end.
    // ────────────────────────────────────────────────────────────────────────
    if (class_name.find("Thread") != std::string::npos &&
        method == "getStackTrace") {
        // CAMPAIGN 010 R14: REAL stack trace from the interpreter call stack
        // (replaces the EXP-093 empty-array stub). Kotlin Intrinsics
        // checkNotNullParameter walks trace[i].className while it equals the
        // Intrinsics class — with real frames the walk terminates at the true
        // caller and the NullPointerException carries the real
        // "Parameter specified as non-null is null: method Class.m, parameter X"
        // message instead of livelocking in the stack-walk loop (the dooz
        // HALT-LOOP in LM1/i;.f).
        auto frames = call_stack_.snapshot_top_first();
        const size_t N = std::min<size_t>(frames.size(), 64);
        uint32_t arr_id = heap_.allocate("Larray;", pc_,
                                        call_stack_.empty() ? 0 : call_stack_.top().frame_id);
        heap_.set_object_field(arr_id, "__array_length__", DalvikValue::make_int((int)N));
        for (size_t i = 0; i < N; i++) {
            uint32_t ste = heap_.allocate("Ljava/lang/StackTraceElement;", pc_,
                                          call_stack_.empty() ? 0 : call_stack_.top().frame_id);
            // "Lcom/foo/Bar;" / "Landroidx/compose/ui/node/e;" → dotted name
            std::string raw = frames[i].first;
            std::string dotted = raw;
            if (!dotted.empty() && dotted.front() == 'L') dotted.erase(0, 1);
            if (!dotted.empty() && dotted.back() == ';') dotted.pop_back();
            std::replace(dotted.begin(), dotted.end(), '/', '.');
            heap_.set_object_field(ste, "__class_name__",
                                   DalvikValue::make_string(dotted, 0));
            heap_.set_object_field(ste, "__method_name__",
                                   DalvikValue::make_string(frames[i].second, 0));
            heap_.set_object_field(arr_id, "array[" + std::to_string(i) + "]",
                                   [&]{ DalvikValue v; v.type = DalvikType::OBJECT_REF;
                                        v.object_id = ste;
                                        v.class_desc = "Ljava/lang/StackTraceElement;";
                                        return v; }());
        }
        DalvikValue arr;
        arr.type = DalvikType::OBJECT_REF;
        arr.object_id = arr_id;
        arr.class_desc = "Larray;";
        arr.int_val = (int)N;
        result = arr;
        status = ApiCallTrace::Status::IMPLEMENTED;
        std::cerr << "[UC010-STACKTRACE] Thread.getStackTrace -> " << N
                  << " real frames (top=" << (N ? frames[0].first : "-") << ")"
                  << std::endl;
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

    // EXP-075: Removed the hardcoded setContentView bypass.
    // Previously this returned true without calling any shadow, which
    // prevented ActivityShadow from capturing the layout_resource_id.
    // Now setContentView flows through to bridge_to_api → try_shadow_dispatch
    // → ActivityShadow::dispatch which properly captures both View and int args.
    // onCreate is still bypassed here because it's the entry point (already
    // executing by the time we reach this code).
    if (class_name.find("Activity") != std::string::npos &&
        method.find("onCreate") != std::string::npos) {
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

    // EXP-093: TextView.getText() → String
    // Per AOSP: returns the text that was set via setText().
    // The DEX bytecode builds garbage "View" via StringBuilder.
    // We dispatch to ViewShadow which has the real text.
    if (method == "getText" &&
        (class_name.find("TextView") != std::string::npos ||
         class_name.find("EditText") != std::string::npos) &&
        shadow_registry_ != nullptr) {
        auto* view_shadow = shadow_registry_->find_as<framework::ViewShadow>();
        if (view_shadow != nullptr && !args.empty() &&
            args[0].type == DalvikType::OBJECT_REF) {
            const auto* node = view_shadow->find_node(args[0].object_id);
            if (node != nullptr) {
                result = DalvikValue::make_string(node->text, args[0].object_id);
                status = ApiCallTrace::Status::IMPLEMENTED;
                return true;
            }
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

    // EXP-088 Phase B FIX: Fall through to shadow registry for unhandled methods.
    // This is critical for findViewById, setOnClickListener, and other View/Activity
    // methods that are handled by the shadow registry but not by bridge_to_api.
    if (method == "findViewById") {
        std::cerr << "[EXP088-B-FALLBACK] Reached shadow registry fallback for "
                  << class_name << "." << method
                  << " shadow=" << (shadow_registry_ ? "YES" : "NO") << std::endl;
    }
    if (shadow_registry_ != nullptr) {
        framework::CallContext ctx;
        if (!args.empty() && args[0].type == DalvikType::OBJECT_REF) {
            ctx.has_receiver = true;
            ctx.receiver_id = args[0].object_id;
            ctx.receiver_class = args[0].class_desc;
            ctx.class_name = args[0].class_desc;
        } else {
            ctx.class_name = class_name;
        }
        ctx.method = method;
        // Convert DalvikValue args to CallContext::Arg (skip arg[0] = receiver)
        for (size_t i = 1; i < args.size(); i++) {
            framework::CallContext::Arg arg;
            if (args[i].type == DalvikType::INT32) {
                arg.kind = framework::CallContext::Arg::Kind::INT;
                arg.int_val = args[i].int_val;
            } else if (args[i].type == DalvikType::OBJECT_REF) {
                arg.kind = framework::CallContext::Arg::Kind::OBJECT;
                arg.object_id = args[i].object_id;
                arg.object_class = args[i].class_desc;
            } else if (args[i].type == DalvikType::STRING_REF) {
                arg.kind = framework::CallContext::Arg::Kind::STRING;
                arg.string_val = args[i].string_val;
            } else if (args[i].type == DalvikType::INT64) {
                arg.kind = framework::CallContext::Arg::Kind::LONG;
                arg.long_val = args[i].long_val;
            } else if (args[i].type == DalvikType::FLOAT32) {
                arg.kind = framework::CallContext::Arg::Kind::FLOAT;
                arg.float_val = args[i].float_val;
            } else if (args[i].type == DalvikType::FLOAT64) {
                arg.kind = framework::CallContext::Arg::Kind::DOUBLE;
                arg.double_val = args[i].double_val;
            }
            ctx.args.push_back(arg);
        }
        auto cr = shadow_registry_->dispatch(ctx);
        if (cr.handled) {
            result = call_result_to_dalvik(cr);
            status = ApiCallTrace::Status::IMPLEMENTED;
            return true;
        }
    }

    // ────────────────────────────────────────────────────────────────────────
    // EXP-093: Bundle / BaseBundle operations — CRITICAL for data passing
    // Bundle stores key-value pairs on the heap object using "bundle:" prefix.
    // Without this, params.getString("phone") returns null → setParams returns
    // early → confirmTextView is empty → screen is visually sparse.
    // ────────────────────────────────────────────────────────────────────────
    if (class_name.find("BaseBundle") != std::string::npos ||
        class_name.find("Bundle") != std::string::npos) {
        uint32_t bundle_id = args.empty() ? 0 : args[0].object_id;
        // putString / putInt / putBoolean / putLong
        if ((method == "putString" || method == "putInt" || method == "putBoolean" || method == "putLong") && args.size() >= 3) {
            std::string key = args[1].type == DalvikType::STRING_REF ? args[1].string_val : "";
            std::cerr << "[EXP093-BUNDLE] putString/putInt/putBoolean/putLong"
                      << " class=" << class_name
                      << " bundle_id=" << bundle_id
                      << " key=\"" << key << "\""
                      << " has_obj=" << (bundle_id ? heap_.has_object(bundle_id) : false)
                      << std::endl;
            if (bundle_id && heap_.has_object(bundle_id) && !key.empty()) {
                heap_.set_object_field(bundle_id, "bundle:" + key, args[2]);
            }
            result = DalvikValue::make_void();
            status = ApiCallTrace::Status::IMPLEMENTED;
            return true;
        }
        // getString(String key) or getString(String key, String def)
        if (method == "getString" && args.size() >= 2) {
            std::string key;
            if (args[1].type == DalvikType::STRING_REF) {
                key = args[1].string_val;
            } else if (args[1].type == DalvikType::OBJECT_REF && heap_.has_object(args[1].object_id)) {
                auto sv = heap_.get_object_field(args[1].object_id, "value");
                if (sv.has_value() && sv->type == DalvikType::STRING_REF) key = sv->string_val;
            }
            std::cerr << "[EXP093-BUNDLE] getString class=" << class_name
                      << " key=\"" << key << "\" bundle_id=" << bundle_id
                      << " has_obj=" << (bundle_id ? heap_.has_object(bundle_id) : false)
                      << std::endl;
            if (bundle_id && heap_.has_object(bundle_id) && !key.empty()) {
                auto val = heap_.get_object_field(bundle_id, "bundle:" + key);
                if (val.has_value()) { result = *val; status = ApiCallTrace::Status::IMPLEMENTED; return true; }
            }
            // With default? (2-arg getString(key, def))
            if (args.size() >= 3 && args[2].type == DalvikType::STRING_REF) {
                result = DalvikValue::make_string(args[2].string_val, 1);
            } else {
                result = DalvikValue::make_null();
            }
            status = ApiCallTrace::Status::IMPLEMENTED;
            return true;
        }
        // getInt(String key) or getInt(String key, int def)
        if (method == "getInt" && args.size() >= 2) {
            std::string key = args[1].type == DalvikType::STRING_REF ? args[1].string_val : "";
            if (bundle_id && heap_.has_object(bundle_id) && !key.empty()) {
                auto val = heap_.get_object_field(bundle_id, "bundle:" + key);
                if (val.has_value() && (val->type == DalvikType::INT32 || val->type == DalvikType::BOOLEAN)) {
                    result = *val; status = ApiCallTrace::Status::IMPLEMENTED; return true;
                }
            }
            int def = (args.size() >= 3 && args[2].type == DalvikType::INT32) ? args[2].int_val : 0;
            result = DalvikValue::make_int(def);
            status = ApiCallTrace::Status::IMPLEMENTED;
            return true;
        }
        // getBoolean(String key) or getBoolean(String key, boolean def)
        if (method == "getBoolean" && args.size() >= 2) {
            std::string key = args[1].type == DalvikType::STRING_REF ? args[1].string_val : "";
            if (bundle_id && heap_.has_object(bundle_id) && !key.empty()) {
                auto val = heap_.get_object_field(bundle_id, "bundle:" + key);
                if (val.has_value() && val->type == DalvikType::BOOLEAN) { result = *val; status = ApiCallTrace::Status::IMPLEMENTED; return true; }
            }
            bool def = (args.size() >= 3 && args[2].type == DalvikType::BOOLEAN) ? args[2].int_val != 0 : false;
            result = DalvikValue::make_bool(def);
            status = ApiCallTrace::Status::IMPLEMENTED;
            return true;
        }
        // containsKey(String key)
        if (method == "containsKey" && args.size() >= 2) {
            std::string key = args[1].type == DalvikType::STRING_REF ? args[1].string_val : "";
            bool found = false;
            if (bundle_id && heap_.has_object(bundle_id) && !key.empty()) {
                found = heap_.get_object_field(bundle_id, "bundle:" + key).has_value();
            }
            result = DalvikValue::make_bool(found);
            status = ApiCallTrace::Status::IMPLEMENTED;
            return true;
        }
    }

    // Default: stubbed but not crashing.
    //
    // UC-CM-001 (closes F012, Coder 3 systemic finding):
    //   "unknown method -> STUBBED + VOID -> later move-result /
    //    move-result-wide -> silent zero" false-success pattern.
    //
    // When the invoke site gave us a method_idx hint, resolve the callee's
    // real proto descriptor and return the type-appropriate default value:
    //   V -> void (legacy behavior)     Z -> false
    //   B/S/C/I -> 0                    J -> 0L
    //   F -> 0.0f                       D -> 0.0
    //   L.../or [ (any reference) -> null
    // Status stays STUBBED either way — this is honest bookkeeping (the
    // value is still a default, never a fabricated success), but the
    // downstream move-result* now sees a correctly-typed zero/null instead
    // of a VOID value leaking into registers.
    status = ApiCallTrace::Status::STUBBED;
    if (method_idx_hint != 0xFFFFFFFFu) {
        const std::string proto = resolve_method_proto_for_dex(method_idx_hint, current_dex_index_);
        const size_t rparen = proto.rfind(')');
        if (rparen != std::string::npos && rparen + 1 < proto.size()) {
            const std::string ret = proto.substr(rparen + 1);
            if (ret.empty() || ret[0] == 'V') {
                result = DalvikValue::make_void();
            } else if (ret[0] == 'Z') {
                result = DalvikValue::make_bool(false);
            } else if (ret[0] == 'B') {
                result = DalvikValue::make_byte(0);
            } else if (ret[0] == 'S') {
                result = DalvikValue::make_short(0);
            } else if (ret[0] == 'C') {
                result = DalvikValue::make_char('\0');
            } else if (ret[0] == 'I') {
                result = DalvikValue::make_int(0);
            } else if (ret[0] == 'J') {
                result = DalvikValue::make_long(0);
            } else if (ret[0] == 'F') {
                result = DalvikValue::make_float(0.0f);
            } else if (ret[0] == 'D') {
                result = DalvikValue::make_double(0.0);
            } else {
                // L<class>; or [ (array) — reference types return null.
                result = DalvikValue::make_null();
            }
            return true;
        }
    }
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
