/*
 * UNIFIED_007 — ARSC Parser (Priority 1 blocker fix)
 *
 * COMPLETE parsing of Android compiled resource table (resources.arsc):
 *   RES_TABLE_TYPE            (0x0002)  root table
 *   RES_STRING_POOL_TYPE      (0x0001)  global + package string pools (UTF-8/UTF-16)
 *   RES_TABLE_PACKAGE_TYPE    (0x0200)  package: id, name, typeStrings, keyStrings
 *   RES_TABLE_TYPE_TYPE       (0x0201)  type (per config): entries incl. SPARSE
 *   RES_TABLE_TYPE_SPEC_TYPE  (0x0202)  (skipped; config mask not needed)
 *
 * Res_value dataTypes handled: NULL, REFERENCE, ATTRIBUTE, STRING, FLOAT,
 * DIMENSION, FRACTION, INT_DEC, INT_HEX, INT_BOOLEAN, COLOR_ARGB8, COLOR_RGB8,
 * COLOR_ARGB4, COLOR_RGB4, DYNAMIC_REFERENCE.
 *
 * Resolution API:
 *   resolve(resource_id)          -> entry name + best-config value
 *   find_id(package, type, name)  -> resource id (via key pool)
 *   list_type(package, type)      -> all entries of a type (id → name)
 * Layouts/drawables/raw/fonts resolved to APK entry paths via type+name.
 *
 * GOLDEN DEBUG PROTOCOL: no fake data; every failure reported.
 */

#ifndef MINIANDROID_ARSC_PARSER_H
#define MINIANDROID_ARSC_PARSER_H

#include <cstdint>
#include <cstring>
#include <string>
#include <vector>
#include <map>
#include <unordered_map>
#include <optional>
#include <sstream>
#include <algorithm>

namespace miniandroid {
namespace resources {

// ---------------------------------------------------------------------------
// Android resource constants (from AOSP ResourceTypes.h)
// ---------------------------------------------------------------------------
static constexpr uint16_t RES_STRING_POOL_TYPE      = 0x0001;
static constexpr uint16_t RES_TABLE_TYPE            = 0x0002;
static constexpr uint16_t RES_XML_START_ELEMENT     = 0x0102;
static constexpr uint16_t RES_XML_END_ELEMENT       = 0x0103;
static constexpr uint16_t RES_XML_RESOURCE_MAP      = 0x0180;
static constexpr uint16_t RES_TABLE_PACKAGE_TYPE    = 0x0200;
static constexpr uint16_t RES_TABLE_TYPE_TYPE       = 0x0201;
static constexpr uint16_t RES_TABLE_TYPE_SPEC_TYPE  = 0x0202;

static constexpr uint32_t RES_STRING_POOL_UTF8_FLAG = 1u << 8;
static constexpr uint32_t NO_ENTRY                  = 0xFFFFFFFFu;

// Res_value dataType
enum class DataType : uint8_t {
    NULL_ = 0x00, REFERENCE = 0x01, ATTRIBUTE = 0x02, STRING = 0x03,
    FLOAT = 0x04, DIMENSION = 0x05, FRACTION = 0x06,
    INT_DEC = 0x10, INT_HEX = 0x11, INT_BOOLEAN = 0x12,
    COLOR_ARGB8 = 0x1C, COLOR_RGB8 = 0x1D, COLOR_ARGB4 = 0x1E, COLOR_RGB4 = 0x1F,
    DYNAMIC_REFERENCE = 0x07,
};

// ResTable_entry flags
static constexpr uint16_t ENTRY_FLAG_COMPLEX = 0x0001;
static constexpr uint16_t ENTRY_FLAG_WEAK    = 0x0002;
// ResTable_type flags
static constexpr uint8_t  TYPE_FLAG_SPARSE   = 0x01;

// Dimension units (Res_value.dataType == DIMENSION, data = COMPLEX_MANTISSA|unit<<4)
enum DimUnit : uint8_t { DIM_PX = 0, DIM_DIP = 1, DIM_SP = 2, DIM_PT = 3, DIM_IN = 4, DIM_MM = 5 };

struct ResValue {
    DataType  type = DataType::NULL_;
    uint32_t  data = 0;          // raw data word
    std::string string_value;    // resolved for STRING
    // For DIMENSION: decoded
    float     dim_value = 0.0f;
    uint8_t   dim_unit = DIM_PX;
    // For REFERENCE: target resource id
    uint32_t  ref_id = 0;

    bool is_reference() const { return type == DataType::REFERENCE || type == DataType::ATTRIBUTE || type == DataType::DYNAMIC_REFERENCE; }
    bool is_string()    const { return type == DataType::STRING; }
    bool is_color()     const {
        switch (type) {
            case DataType::COLOR_ARGB8: case DataType::COLOR_RGB8:
            case DataType::COLOR_ARGB4: case DataType::COLOR_RGB4: return true;
            default: return false;
        }
    }
    bool is_dimension() const { return type == DataType::DIMENSION; }
    bool is_bool()      const { return type == DataType::INT_BOOLEAN; }
    bool is_int()       const { return type == DataType::INT_DEC || type == DataType::INT_HEX; }
    bool is_null()      const { return type == DataType::NULL_; }
};

// One concrete resource value bound to a config
struct ArscEntry {
    uint32_t  resource_id = 0;
    uint32_t  package_id = 0;
    uint16_t  type_index = 0;      // 1-based index into package type strings
    uint16_t  entry_index = 0;     // index within type
    std::string type_name;         // e.g. "layout", "string", "drawable"
    std::string name;              // entry key name, e.g. "activity_main"
    std::string config_desc;       // human-readable config qualifiers ("", "en", "hdpi"...)
    ResValue   value;              // best value (for complex: first item)
    bool       is_complex = false;
    std::vector<ResValue> complex_items;  // for arrays/attrs
};

// Full resolution result: id → every config's entry
struct ResolvedResource {
    uint32_t id = 0;
    std::string package_name;
    std::string type_name;
    std::string name;
    std::vector<ArscEntry> configs;   // all configs, default-first ordering applied on demand
    const ArscEntry* best() const;    // best/default config (see .cpp)
};

class ArscParser {
public:
    ArscParser() = default;

    // Parse resources.arsc bytes. Returns false + last_error on failure.
    bool parse(const std::vector<uint8_t>& data);

    bool valid() const { return valid_; }
    const std::string& last_error() const { return last_error_; }

    // --- Lookup API ---------------------------------------------------------
    // Resolve full resource by id.
    std::optional<ResolvedResource> resolve(uint32_t resource_id) const;
    // Find id by name (first package containing it). type e.g. "layout".
    std::optional<uint32_t> find_id(const std::string& package, const std::string& type,
                                    const std::string& name) const;
    // Convenience: resolve id → value of best config (follows one REFERENCE hop).
    std::optional<ResValue> resolve_value(uint32_t resource_id) const;
    // Resolve string by id (no reference hop).
    std::optional<std::string> resolve_string(uint32_t resource_id) const;
    // All entry names of a type in a package ("layout" → ids+names)
    std::vector<std::pair<uint32_t, std::string>> list_type(const std::string& package,
                                                            const std::string& type) const;
    // APK path for a resource of file-backed type (layout → "res/layout/x.xml")
    // Searches raw file paths from the APK (caller supplies path list).
    std::optional<std::string> apk_path_for(uint32_t resource_id,
                                            const std::vector<std::string>& apk_paths) const;

    // --- Stats / evidence ----------------------------------------------------
    struct Stats {
        uint32_t package_count = 0;
        uint32_t global_string_count = 0;
        uint32_t type_count = 0;       // total (package,type) chunks
        uint32_t entry_count = 0;      // total entries across all configs
        uint32_t named_ids = 0;        // distinct resource ids with names
        std::map<std::string, uint32_t> entries_by_type;
    };
    const Stats& stats() const { return stats_; }

    // JSON dump for evidence artifacts
    std::string to_json(size_t max_entries = 200) const;

private:
    struct Pool {
        bool utf8 = false;
        std::vector<std::string> strings;
        const std::string* get(uint32_t idx) const {
            return idx < strings.size() ? &strings[idx] : nullptr;
        }
    };

    std::vector<ArscEntry> type_entries_;                    // flat: one per (id,config)
    std::unordered_map<uint32_t, std::vector<ArscEntry*>> by_id_;  // id → configs
    std::unordered_map<uint32_t, void*> pkg_of_id_;          // id → Package* (opaque)

    struct TypeChunk {
        uint8_t  type_id = 0;          // 1-based
        uint32_t entry_count = 0;
        std::string config_desc;
        std::vector<int32_t> entry_offsets;  // -1 = NO_ENTRY
        std::vector<uint32_t> entry_positions; // byte offsets into chunk data
    };

    struct Package {
        uint32_t id = 0;
        std::string name;
        Pool type_strings;
        Pool key_strings;
        // type_id → list of type chunks (one per config)
        std::map<uint8_t, std::vector<TypeChunk>> types;
        // entry_index → resource id mapping is implicit: id = (package<<24)|(type<<16)|entry
    };

    bool parse_string_pool(const uint8_t* base, size_t avail, size_t chunk_offset, Pool& out);
    bool parse_package(const uint8_t* base, size_t avail, size_t chunk_offset, size_t chunk_size);
    bool parse_type_chunk(const uint8_t* base, size_t avail, Package& pkg,
                          size_t chunk_offset, size_t chunk_size);
    void finish_index();
    static bool decode_res_value(const uint8_t* p, size_t avail, const Pool& global,
                                 const Package& pkg, ResValue& out);
    static std::string config_to_string(const uint8_t* cfg, size_t cfg_size);

    const uint8_t* data_ = nullptr;
    size_t size_ = 0;
    Pool global_strings_;
    std::vector<Package> packages_;
    bool valid_ = false;
    std::string last_error_;
    Stats stats_;
    // id → (package_idx, type_id, entry_index)
    std::unordered_map<uint32_t, std::tuple<size_t, uint8_t, uint32_t>> id_index_;
};

} // namespace resources
} // namespace miniandroid

// shared complex-dimension decoder (defined in arsc_parser.cpp)
namespace miniandroid { namespace resources { float complex_to_float(uint32_t data); } }

#endif // MINIANDROID_ARSC_PARSER_H
