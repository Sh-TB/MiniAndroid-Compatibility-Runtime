#!/usr/bin/env python3
"""CONT-34 F-NEW-528: ApplicationInfo.metaData reference-typed values resolve
through the ARSC (AOSP PackageParser.parseMetaData law).

Ground truth (telegram CONT-34 run): GoogleApiAvailability (Lf6/g;.b pc=153)
reads metaData.getInt("com.google.android.gms.version"); the manifest declares
android:value=@0x7f0a000a (AXML TYPE_REFERENCE) — manifest_reader's
get_attribute_value answers "@0x7f0a000a" for REFERENCES, the seeding sites
store that STRING, Bundle.getInt → 0 → GooglePlayServicesMissingManifestValue
Exception ISE "A required meta-data tag ... does not exist" → APP BOUNDARY.
AOSP: android:value reference-typed meta-data lands as the RESOLVED integer
(Bundle.putInt; PackageParser dereferences through the resource table).
Fix: ArscParser::resolve_int (scalar twin of resolve_int_array) + both
ApplicationInfo.metaData seeding sites convert @0x... refs (resolve → int;
honest fallback = the resource id itself, nonzero — the caller gate is a
presence/nonzero check)."""
from pathlib import Path

ARSC_H = Path("miniandroid/src/resources/arsc_parser.h")
ARSC_C = Path("miniandroid/src/resources/arsc_parser.cpp")
ENG_C = Path("miniandroid/src/dex/dalvik_engine.cpp")

def patch():
    n = 0
    # 1. header decl
    h = ARSC_H.read_text()
    if "resolve_int(" not in h:
        anchor = ("    std::optional<std::vector<int32_t>> resolve_int_array(\n"
                  "        uint32_t resource_id) const;")
        assert anchor in h, "h anchor missing"
        h = h.replace(anchor, anchor + (
            "\n\n    // F-NEW-528 (CONT-34): scalar integer entry — the twin of\n"
            "    // resolve_int_array for android:value=\"@integer/@color/@bool\"\n"
            "    // meta-data references (AOSP PackageParser.parseMetaData\n"
            "    // Bundle.putInt contract). One reference hop is dereferenced\n"
            "    // (ResolveAttributeReference law); non-integer answers nullopt.\n"
            "    std::optional<int32_t> resolve_int(uint32_t resource_id) const;"), 1)
        ARSC_H.write_text(h); n += 1
        print("1. header decl added")
    # 2. impl after resolve_int_array
    c = ARSC_C.read_text()
    if "ArscParser::resolve_int(" not in c:
        anchor = ("    for (const auto& it : items) out.push_back(it.second);\n"
                  "    return out;\n"
                  "}\n")
        assert anchor in c, "cpp anchor missing"
        c = c.replace(anchor, anchor + (
            "\n// F-NEW-528 (CONT-34): scalar integer entry (see header).\n"
            "std::optional<int32_t> ArscParser::resolve_int(\n"
            "    uint32_t resource_id) const {\n"
            "    auto r = resolve(resource_id);\n"
            "    if (!r) return std::nullopt;\n"
            "    const ArscEntry* e = r->best_for(device_config());\n"
            "    if (!e) return std::nullopt;\n"
            "    if (e->is_complex) return std::nullopt;\n"
            "    if (e->value.is_reference()) {\n"
            "        // one hop dereference (ResolveAttributeReference law).\n"
            "        auto rr = resolve(e->value.ref_id);\n"
            "        if (!rr) return std::nullopt;\n"
            "        const ArscEntry* re = rr->best_for(device_config());\n"
            "        if (!re || re->is_complex || re->value.is_reference())\n"
            "            return std::nullopt;\n"
            "        return (int32_t)re->value.data;\n"
            "    }\n"
            "    if (e->value.is_string()) return std::nullopt;\n"
            "    return (int32_t)e->value.data;\n"
            "}\n"), 1)
        ARSC_C.write_text(c); n += 1
        print("2. resolve_int implemented")
    # 3. both seeding sites: @0x refs -> resolved int
    e = ENG_C.read_text()
    old_loop = """                        for (const auto& [k, v] : application_meta_data_) {
                            static const std::string digits = "0123456789";
                            bool numeric = !v.empty() &&
                                v.find_first_not_of(digits) == std::string::npos;
                            if (numeric)
                                heap_.set_object_field(bundle_id, "bundle:" + k,
                                    DalvikValue::make_int(std::stoi(v)));
                            else
                                heap_.set_object_field(bundle_id, "bundle:" + k,
                                    DalvikValue::make_string(v, 0));
                        }"""
    if old_loop not in e:
        print("3. loop anchor differs — checking count")
        raise SystemExit(1)
    new_loop = """                        for (const auto& [k, v] : application_meta_data_) {
                            static const std::string digits = "0123456789";
                            bool numeric = !v.empty() &&
                                v.find_first_not_of(digits) == std::string::npos;
                            // F-NEW-528: "@0x…" reference-typed values land as
                            // the RESOLVED integer (AOSP Bundle.putInt law) —
                            // gms.version evidence: the string form made
                            // Bundle.getInt answer 0 → play-services manifest
                            // gate ISE at APP BOUNDARY. Honest fallback = the
                            // resource id itself (nonzero; the play-services
                            // caller gates on presence/nonzero).
                            if (v.rfind("@0x", 0) == 0 && v.size() > 3) {
                                int32_t md_int = 0;
                                bool md_ok = false;
                                try {
                                    uint32_t md_resid =
                                        (uint32_t)std::stoul(v.substr(3),
                                                             nullptr, 16);
                                    auto& md_rt =
                                        resources::ResourceRuntime::instance();
                                    if (md_rt.loaded() ||
                                        md_rt.ensure_loaded(apk_path_)) {
                                        auto mi =
                                            md_rt.arsc().resolve_int(md_resid);
                                        if (mi) { md_int = *mi; md_ok = true; }
                                    }
                                    if (!md_ok) {
                                        md_int = (int32_t)md_resid;
                                        md_ok = true;
                                    }
                                } catch (...) { md_ok = false; }
                                if (md_ok) {
                                    heap_.set_object_field(bundle_id,
                                        "bundle:" + k,
                                        DalvikValue::make_int(md_int));
                                    continue;
                                }
                            }
                            if (numeric)
                                heap_.set_object_field(bundle_id, "bundle:" + k,
                                    DalvikValue::make_int(std::stoi(v)));
                            else
                                heap_.set_object_field(bundle_id, "bundle:" + k,
                                    DalvikValue::make_string(v, 0));
                        }"""
    cnt = e.count(old_loop)
    print(f"3. loop occurrences: {cnt}")
    e = e.replace(old_loop, new_loop)
    ENG_C.write_text(e); n += 1
    print(f"patched {n} steps")

if __name__ == "__main__":
    patch()
