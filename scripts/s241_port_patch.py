#!/usr/bin/env python3
"""S241 port patch: String.compareToIgnoreCase — applied to a worktree's
dalvik_engine.cpp (survives sandbox recycles; re-runnable, idempotent)."""
import sys

WT = sys.argv[1] if len(sys.argv) > 1 else "/home/z/my-project/wt_s241"
P = f"{WT}/miniandroid/src/dex/dalvik_engine.cpp"
src = open(P).read()

PORT = '''    // ── S241: String.compareToIgnoreCase — the sweep's next confirmed
    // CONTENT-ABSENT String-family law (zero engine hits, same naked-comment
    // pattern regionMatches had). AOSP OpenJdk11: char-by-char
    // toUpperCase-folded comparison, first difference -> c1 - c2; else
    // len1 - len2. Bridge shape: (recv, other) -> INT32.
    if (class_name == "Ljava/lang/String;" && method == "compareToIgnoreCase" &&
        args.size() >= 2) {
        std::string a = (args[0].type == DalvikType::STRING_REF)
                            ? std::string(args[0].string_val) : std::string();
        std::string b = (args[1].type == DalvikType::STRING_REF)
                            ? std::string(args[1].string_val) : std::string();
        int32_t cmp = 0;
        size_t n = std::min(a.size(), b.size());
        for (size_t i = 0; i < n; i++) {
            int32_t ca = toupper((unsigned char)a[i]);
            int32_t cb = toupper((unsigned char)b[i]);
            if (ca != cb) { cmp = ca - cb; break; }
        }
        if (cmp == 0)
            cmp = (int32_t)a.size() - (int32_t)b.size();
        result = DalvikValue::make_int(cmp);
        status = ApiCallTrace::Status::IMPLEMENTED;
        return true;
    }
'''

ANCHOR = '''    if (class_name == "Ljava/lang/String;" && method == "regionMatches" &&
        args.size() >= 5) {'''

if 'compareToIgnoreCase' in src:
    print("already patched — skip")
else:
    assert ANCHOR in src, "regionMatches anchor not found"
    open(P, "w").write(src.replace(ANCHOR, PORT + ANCHOR, 1))
    print("compareToIgnoreCase port applied at", P)
