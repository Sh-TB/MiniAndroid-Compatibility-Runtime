#!/usr/bin/env python3
"""
extract_format_engine.py — VISUAL-CAMPAIGN EXT-01 gate G25 refactor.

1. Extracts the CYCLE-E Java format engine (lambdas + conversion walk) from
   the inline String.format handler in DalvikExecutionEngine::bridge_to_api
   into a new private member: DalvikExecutionEngine::java_format_walk().
   Rationale (AOSP law): Resources.getString(int, Object...) delegates to
   String.format — Context.getString(resId, formatArgs) must reuse the SAME
   engine, not a second copy (REUSE-FIRST: one canonical implementation).
2. Adds DalvikExecutionEngine::seed_framework_device_statics() — seeds the
   virtual device identity statics (Build.VERSION.SDK_INT/RELEASE, Build.*,
   Settings.Secure.ANDROID_ID) insert-if-absent.

Marker-based surgery: exact-anchor matching, no line numbers.
"""
from pathlib import Path

SRC = Path("/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/src/dex/dalvik_engine.cpp")
text = SRC.read_text()

M1 = "        // Java-correct stringification of one format argument"
M2 = ("        status = ApiCallTrace::Status::IMPLEMENTED;\n"
      "        result = DalvikValue::make_string(output, 0);\n"
      "        std::cerr << \"[EXP093-STRFMT] String.format")

i1 = text.find(M1)
assert i1 != -1, "M1 (walk start) not found"
i2 = text.find(M2, i1)
assert i2 != -1, "M2 (walk end) not found"

extracted = text[i1:i2].rstrip() + "\n"
assert "arg_idx" in extracted and "case 's'" in extracted, "extracted body looks wrong"

new_handler_segment = (
    "        // VISUAL-CAMPAIGN (EXT-01 gate G25): the format engine was\n"
    "        // extracted verbatim into java_format_walk() so the SAME engine\n"
    "        // also serves Context.getString(resId, formatArgs) (AOSP law:\n"
    "        // Resources.getString(int, Object...) == String.format(load, args)).\n"
    "        std::string output = java_format_walk(fmt, fargs);\n\n"
)

text = text[:i1] + new_handler_segment + text[i2:]

# --- build the two new method definitions ---------------------------------
seed_fn = (
    "// ────────────────────────────────────────────────────────────────────\n"
    "// VISUAL-CAMPAIGN (EXT-01 gate G25): seed the virtual device identity.\n"
    "// AOSP law: Build.VERSION.SDK_INT / Build.VERSION.RELEASE / Build.* and\n"
    "// Settings.Secure.ANDROID_ID are FRAMEWORK-provided statics — a real\n"
    "// device firmware defines them before any app code runs. MiniAndroid's\n"
    "// honest virtual identity tracks the android-34 stubs used by its\n"
    "// fixture toolchain (SDK_INT=34, RELEASE=\"14\"). Insert-if-absent:\n"
    "// a real app <clinit> always wins over a seed.\n"
    "// Evidence: EXT-01 baseline (HelloWorldSelfAware) — AndroidInfo.getId()\n"
    "// read SDK_INT=0, took the pre-O Build.SERIAL branch and rendered\n"
    "// \"i'm null\"; with this seed it takes the Settings.Secure ANDROID_ID\n"
    "// branch exactly like any Android 8+ device.\n"
    "// ────────────────────────────────────────────────────────────────────\n"
    "void DalvikExecutionEngine::seed_framework_device_statics() {\n"
    "    auto seed = [this](const std::string& key, const DalvikValue& v) {\n"
    "        static_field_storage_.emplace(key, v);  // insert-if-absent\n"
    "    };\n"
    "    seed(\"Landroid/os/Build$VERSION;.SDK_INT\", DalvikValue::make_int(34));\n"
    "    seed(\"Landroid/os/Build$VERSION;.RELEASE\", DalvikValue::make_string(\"14\", 0));\n"
    "    seed(\"Landroid/os/Build$VERSION;.CODENAME\", DalvikValue::make_string(\"REL\", 0));\n"
    "    seed(\"Landroid/os/Build$VERSION;.SDK\", DalvikValue::make_string(\"34\", 0));\n"
    "    seed(\"Landroid/os/Build$VERSION;.INCREMENTAL\", DalvikValue::make_string(\"miniandroid.20260905\", 0));\n"
    "    seed(\"Landroid/os/Build;.MODEL\", DalvikValue::make_string(\"MiniAndroid\", 0));\n"
    "    seed(\"Landroid/os/Build;.MANUFACTURER\", DalvikValue::make_string(\"MiniAndroid\", 0));\n"
    "    seed(\"Landroid/os/Build;.BRAND\", DalvikValue::make_string(\"MiniAndroid\", 0));\n"
    "    seed(\"Landroid/os/Build;.DEVICE\", DalvikValue::make_string(\"miniandroid\", 0));\n"
    "    seed(\"Landroid/os/Build;.PRODUCT\", DalvikValue::make_string(\"miniandroid\", 0));\n"
    "    seed(\"Landroid/os/Build;.HARDWARE\", DalvikValue::make_string(\"miniandroid\", 0));\n"
    "    seed(\"Landroid/os/Build;.FINGERPRINT\", DalvikValue::make_string(\"MiniAndroid/miniandroid/miniandroid:14/MINI.20260905/0:userdebug/test-keys\", 0));\n"
    "    seed(\"Landroid/os/Build;.SERIAL\", DalvikValue::make_string(\"miniandroid\", 0));\n"
    "    // AOSP: Settings.Secure.ANDROID_ID == the column name \"android_id\".\n"
    "    seed(\"Landroid/provider/Settings$Secure;.ANDROID_ID\", DalvikValue::make_string(\"android_id\", 0));\n"
    "    // Deterministic virtual-device ANDROID_ID (16 lowercase hex chars,\n"
    "    // same shape as a real device; constant => Rule 12 determinism).\n"
    "    resource_string_values_[\"android_id\"] = \"6f1c3a9d2e5b4780\";\n"
    "}\n\n"
)

format_fn_header = (
    "// ────────────────────────────────────────────────────────────────────\n"
    "// VISUAL-CAMPAIGN (EXT-01 gate G25): the CYCLE-E Java format engine,\n"
    "// extracted VERBATIM from the String.format handler (one canonical\n"
    "// implementation, REUSE-FIRST). Applies\n"
    "// %[argument_index$][flags][width][.precision]conversion\n"
    "// with d/i/s/S/f/F/x/X/o/b/B/c/C/e/E/g/G/n, zero/space padding,\n"
    "// left-align, explicit argument indexes; Java law: null → \"null\",\n"
    "// boxed primitives read their \"value\" field.\n"
    "// ────────────────────────────────────────────────────────────────────\n"
    "std::string DalvikExecutionEngine::java_format_walk(\n"
    "        const std::string& fmt, const std::vector<DalvikValue>& fargs) {\n"
    "    std::string output;\n\n"
)

format_fn_footer = "    return output;\n}\n\n"

anchor = "bool DalvikExecutionEngine::bridge_to_api("
ia = text.find(anchor)
assert ia != -1, "bridge_to_api definition not found"
text = text[:ia] + seed_fn + format_fn_header + extracted + format_fn_footer + text[ia:]

SRC.write_text(text)
print("OK: format engine extracted + device statics seeded.")
print("extracted walk length:", len(extracted), "bytes")
