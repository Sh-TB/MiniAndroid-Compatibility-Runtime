#!/usr/bin/env python3
"""F-NEW-639 (W27, issue #597) — the BOUNDED-append law patch.

append(CharSequence|char[], int start, int end) must append the SLICE
[start, end). The generic arm stringified args[1] and ignored
args[2]/args[3]: both bounded appends of a Kotlin replace(String,
transform) rebuild contributed the FULL accumulator — OpenCalc's
one-tap "777" face. Law: OpenJDK bounds (start<0 || end>len ||
start>end -> deferred StringIndexOutOfBoundsException, the R24 message
shape); a null sequence appends "null" (bounds on "null" length 4).
Bounds run on the stored UTF-8 BYTE length (the documented R24
byte-length approximation).
"""
from pathlib import Path

P = Path("/tmp/w27_int/miniandroid/src/dex/dalvik_engine.cpp")
s = P.read_text()

OLD = """        if (method == "append") {
            if (args.size() >= 2) {
                cur += stringify_arg(args[1]);
            }"""
NEW = """        if (method == "append") {
            // ── F-NEW-639 (W27, issue #597): the BOUNDED-append overload.
            // append(CharSequence|char[], int start, int end) appends the
            // SLICE [start, end) — not the whole sequence. The generic arm
            // below stringified args[1] and ignored args[2]/args[3]: both
            // bounded appends of a Kotlin replace(String, transform)
            // rebuild contributed the full accumulator — the one-tap
            // "777" face on OpenCalc. OpenJDK law: start < 0 ||
            // end > length || start > end is a deferred
            // StringIndexOutOfBoundsException (the R24 message shape); a
            // null sequence appends "null" (bounds on the "null" length).
            // Bounds run on the stored UTF-8 BYTE length — the documented
            // R24 byte-length approximation.
            if (args.size() >= 4 &&
                (args[2].type == DalvikType::INT32) &&
                (args[3].type == DalvikType::INT32)) {
                const std::string f639_seq = stringify_arg(args[1]);
                const int32_t f639_st = dalvik_int_value(args[2]);
                const int32_t f639_en = dalvik_int_value(args[3]);
                if (f639_st < 0 ||
                    f639_en > static_cast<int32_t>(f639_seq.size()) ||
                    f639_st > f639_en) {
                    static thread_local uint64_t f639_throws = 0;
                    if (f639_throws++ < 8)
                        std::cerr << "[F-NEW-639] append bounds throw ["
                                  << f639_st << "," << f639_en << ") of len="
                                  << f639_seq.size() << " (caller "
                                  << current_class_ << "." << current_method_
                                  << ")" << std::endl;
                    throw_deferred(
                        "Ljava/lang/StringIndexOutOfBoundsException;",
                        "start " + std::to_string(f639_st) + ", end " +
                            std::to_string(f639_en) + ", length " +
                            std::to_string(f639_seq.size()),
                        "F-NEW-639");
                    result = DalvikValue::make_null();
                    status = ApiCallTrace::Status::IMPLEMENTED;
                    return true;
                }
                static thread_local uint64_t f639_slices = 0;
                if (f639_slices++ < 8)
                    std::cerr << "[F-NEW-639] append bounded ["
                              << f639_st << "," << f639_en << ") of len="
                              << f639_seq.size() << " -> \\""
                              << f639_seq.substr(
                                     static_cast<size_t>(f639_st),
                                     static_cast<size_t>(f639_en) -
                                         static_cast<size_t>(f639_st))
                              << "\\" (caller " << current_class_ << "."
                              << current_method_ << ")" << std::endl;
                cur += f639_seq.substr(
                    static_cast<size_t>(f639_st),
                    static_cast<size_t>(f639_en) - static_cast<size_t>(f639_st));
                if (sb_id != 0 && heap_.has_object(sb_id)) {
                    heap_.set_object_field(
                        sb_id, "sb_value", DalvikValue::make_string(cur, 0));
                }
                status = ApiCallTrace::Status::IMPLEMENTED;
                // Per OpenJDK the bounded append also returns `this`.
                DalvikValue r639;
                r639.type = DalvikType::OBJECT_REF;
                r639.object_id = sb_id;
                r639.class_desc = class_name.c_str();
                result = r639;
                return true;
            }
            if (args.size() >= 2) {
                cur += stringify_arg(args[1]);
            }"""
assert OLD in s, "append arm not found"
P.write_text(s.replace(OLD, NEW, 1))

M = Path("/tmp/w27_int/miniandroid/Makefile")
m = M.read_text()
OLDM = "\ts234_w26_engine_laws_test s235_lane_laws_test s236_port_laws_test\n"
NEWM = ("\ts234_w26_engine_laws_test s235_lane_laws_test "
        "s236_port_laws_test s237_append_bounded_law_test\n")
assert OLDM in m, "TEST_LAW line not found"
M.write_text(m.replace(OLDM, NEWM, 1))
print("F-NEW-639 patched + battery registered")
