#!/usr/bin/env python3
# cont33_heap_unordered.py — F-NEW-381 phase-2 heap-map representation lever.
#
# LAW (zero semantic drift):
#  1. The three hot string/uint-keyed maps (HeapObject.fields,
#     DalvikHeap.objects_, DalvikEngine.static_field_storage_) swap
#     std::map -> std::unordered_map. The interpreter hot path is
#     find/operator[] ONLY — order-independent.
#  2. Every externally-frozen ordered consumer keeps the historical
#     std::map iteration contract by sorting keys once per call:
#     - DalvikHeap::dump() / get_all_ids()           (id-ascending)
#     - view-tree fallback full-heap scan            (id-ascending)
#     - R-string resource-id scan (first-match IS semantic: the D8
#       shrinker remaps resource ids to small ordinals — collisions
#       between same-id fields are possible, so map order is behavior)
#  3. Bounded diagnostic stderr dumps may print in hash order — zero
#     semantic surface (regression-gated; ledger-noted).
import sys

H = "src/dex/dalvik_engine.h"
CPP = "src/dex/dalvik_engine.cpp"

def patch(path, pairs):
    src = open(path).read()
    for old, new in pairs:
        n = src.count(old)
        if n != 1:
            print(f"[FAIL] anchor count={n} (need 1) in {path}:\n---\n{old[:160]}\n---")
            sys.exit(1)
        src = src.replace(old, new, 1)
    open(path, "w").write(src)
    print(f"[OK] {path}: {len(pairs)} edit(s)")

patch(H, [
    # include for std::sort in the header now that get_all_ids sorts
    (
        "#include <map>\n#include <unordered_map>",
        "#include <map>\n#include <unordered_map>\n#include <algorithm>  // F-NEW-381 phase 2: get_all_ids sorted-order contract"
    ),
    # HeapObject::fields — the per-object instance-field map (iget/iput hot)
    (
        "    // Fields (simplified - would be full field table in production)\n"
        "    std::map<std::string, DalvikValue> fields;",
        "    // Fields (F-NEW-381 phase 2: unordered — the interpreter hot path\n"
        "    // is find/operator[] only; frozen ordered consumers sort keys\n"
        "    // explicitly, preserving the historical std::map iteration law)\n"
        "    std::unordered_map<std::string, DalvikValue> fields;"
    ),
    # DalvikHeap::objects_ — the object-id map (every heap access walks it)
    (
        "    std::map<uint32_t, HeapObject> objects_;",
        "    std::unordered_map<uint32_t, HeapObject> objects_;"
    ),
    # static_field_storage_ — the sget/sput static map
    (
        "    std::map<std::string, DalvikValue> static_field_storage_;  // key: \"class_descriptor.field_name\"",
        "    std::unordered_map<std::string, DalvikValue> static_field_storage_;  // key: \"class_descriptor.field_name\" (F-NEW-381 phase 2: unordered; the frozen first-match consumer sorts keys)"
    ),
    # DalvikHeap::dump() — id-ascending contract preserved
    (
        "    json dump() const {\n"
        "        json arr = json::array();\n"
        "        for (const auto& pair : objects_) {\n"
        "            arr.push_back(pair.second.to_json());\n"
        "        }\n"
        "        return arr;\n"
        "    }",
        "    json dump() const {\n"
        "        json arr = json::array();\n"
        "        for (const uint32_t oid : get_all_ids()) {  // F-NEW-381 phase 2: id-ascending\n"
        "            arr.push_back(objects_.at(oid).to_json());\n"
        "        }\n"
        "        return arr;\n"
        "    }"
    ),
    # get_all_ids() — id-ascending contract preserved
    (
        "    std::vector<uint32_t> get_all_ids() const {\n"
        "        std::vector<uint32_t> ids;\n"
        "        for (const auto& pair : objects_) ids.push_back(pair.first);\n"
        "        return ids;\n"
        "    }",
        "    std::vector<uint32_t> get_all_ids() const {\n"
        "        std::vector<uint32_t> ids;\n"
        "        ids.reserve(objects_.size());\n"
        "        for (const auto& pair : objects_) ids.push_back(pair.first);\n"
        "        std::sort(ids.begin(), ids.end());  // F-NEW-381 phase 2: std::map order preserved\n"
        "        return ids;\n"
        "    }"
    ),
])

patch(CPP, [
    # view-tree fallback full-heap scan (14862) — id-ascending contract
    (
        "        node_source = \"full-heap-scan (no tracked content root)\";\n"
        "        for (const auto& [oid, obj] : heap_.all_objects()) {\n"
        "            const auto* node = view_shadow->find_node(oid);\n"
        "            if (node == nullptr) continue;\n"
        "            ordered_nodes.push_back(node);\n"
        "        }",
        "        node_source = \"full-heap-scan (no tracked content root)\";\n"
        "        for (const uint32_t oid : heap_.get_all_ids()) {  // F-NEW-381 phase 2: id-ascending\n"
        "            const auto* node = view_shadow->find_node(oid);\n"
        "            if (node == nullptr) continue;\n"
        "            ordered_nodes.push_back(node);\n"
        "        }"
    ),
    # R-string resource-id scan (first-match IS semantic) — sorted keys
    (
        "                std::string r_string_prefix = \"Lorg/telegram/messenger/R$string;.\";\n"
        "                for (const auto& [skey, sval] : static_field_storage_) {\n"
        "                    if (skey.find(r_string_prefix) == 0 &&",
        "                std::string r_string_prefix = \"Lorg/telegram/messenger/R$string;.\";\n"
        "                std::vector<std::string> r337_sorted_keys; r337_sorted_keys.reserve(static_field_storage_.size());  // F-NEW-381 phase 2: first-match is semantic — preserve std::map order\n"
        "                for (const auto& skv337 : static_field_storage_) r337_sorted_keys.push_back(skv337.first);\n"
        "                std::sort(r337_sorted_keys.begin(), r337_sorted_keys.end());\n"
        "                for (const auto& skey : r337_sorted_keys) {\n"
        "                    const DalvikValue& sval = static_field_storage_.at(skey);\n"
        "                    if (skey.find(r_string_prefix) == 0 &&"
    ),
])
print("[DONE] F-NEW-381 phase-2 patch applied")
