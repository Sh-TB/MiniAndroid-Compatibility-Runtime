// s254_version_identity_law_test — ISSUE-607 item 8 (P2).
// W22 integration: renamed from the recovered #607 patch s249
// (main's s249/s248 names are owned by the W20-K contract tests;
// provenance: #607 issuecomment patch, base 9dafaadd).
//
// The repository shipped three disagreeing identity strings (CHANGELOG
// v0.0.6.2, README UNIFIED_011.1, code "v0.1"). The fix makes ONE generated
// source authoritative: VERSION + git HEAD -> build/generated/
// miniandroid_version.h, consumed by both the Make and CMake builds and by
// the runtime's `version` command.
//
// This law asserts the invariant that keeps them from drifting again:
//   1. the generated header EXISTS and defines MINIANDROID_VERSION /
//      MINIANDROID_COMMIT (pre-fix: it did not exist at all -> FAIL);
//   2. MINIANDROID_VERSION equals the VERSION file, byte-for-byte;
//   3. MINIANDROID_COMMIT is the current `git rev-parse HEAD` (or "unknown"
//      outside a checkout) — release artifacts are commit-pinned;
//   4. CHANGELOG.md carries the same semantic version (release identity);
//   5. README.md no longer advertises a contradictory identity.
//
// Runs from the repo root (the Makefile/CTest working directory, same as the
// font law tests).
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

static int g_pass = 0, g_fail = 0;
static void record(bool ok, const std::string& what) {
    std::cout << (ok ? "  PASS  " : "  FAIL  ") << what << "\n";
    if (ok) ++g_pass; else ++g_fail;
}

static bool read_file(const std::string& path, std::string& out) {
    std::ifstream in(path, std::ios::binary);
    if (!in) return false;
    std::ostringstream ss;
    ss << in.rdbuf();
    out = ss.str();
    return true;
}

static std::string strip(const std::string& s) {
    size_t a = s.find_first_not_of(" \t\r\n");
    if (a == std::string::npos) return "";
    size_t b = s.find_last_not_of(" \t\r\n");
    return s.substr(a, b - a + 1);
}

// Pull the quoted value of a #define NAME "value" out of header text.
static bool define_value(const std::string& text, const std::string& name,
                         std::string& out) {
    std::string key = "#define " + name + " \"";
    size_t p = text.find(key);
    if (p == std::string::npos) return false;
    p += key.size();
    size_t e = text.find('"', p);
    if (e == std::string::npos) return false;
    out = text.substr(p, e - p);
    return true;
}

static bool is_hex40(const std::string& s) {
    if (s.size() != 40) return false;
    for (char c : s)
        if (!std::isxdigit(static_cast<unsigned char>(c))) return false;
    return true;
}

// Locate the generated header: the Make build writes build/generated/, CMake
// writes <binary-dir>/generated/. Probe the Make path, then a CMake env hint.
static bool find_header(std::string& path) {
    const char* candidates[] = {
        "build/generated/miniandroid_version.h",
        "generated/miniandroid_version.h",
        nullptr,
    };
    const char* env = std::getenv("MINIANDROID_VERSION_HEADER");
    for (const char** c = candidates; *c; ++c) {
        std::string probe = *c;
        std::ifstream in(probe);
        if (in) { path = probe; return true; }
    }
    if (env && *env) {
        std::ifstream in(env);
        if (in) { path = env; return true; }
    }
    return false;
}

int main() {
    // L1: the generated header exists and defines both macros.
    std::string header_path, header;
    bool have_header = find_header(header_path) && read_file(header_path, header);
    record(have_header, "L1.0 generated miniandroid_version.h exists");

    std::string hdr_version, hdr_commit;
    if (have_header) {
        record(define_value(header, "MINIANDROID_VERSION", hdr_version),
               "L1.1 header defines MINIANDROID_VERSION");
        record(define_value(header, "MINIANDROID_COMMIT", hdr_commit),
               "L1.2 header defines MINIANDROID_COMMIT");
    }

    // L2: VERSION file is the single source and matches the header.
    std::string version_raw;
    bool have_version = read_file("VERSION", version_raw);
    record(have_version, "L2.0 VERSION file exists");
    if (have_version && have_header) {
        record(strip(version_raw) == hdr_version,
               "L2.1 VERSION (" + strip(version_raw) + ") == header (" +
                   hdr_version + ")");
    }

    // L3: the commit is pinned to the current git HEAD (or honestly unknown).
    std::string git_head;
    bool have_git = false;
    {
        std::string cmd = "git rev-parse HEAD 2>/dev/null";
        FILE* p = popen(cmd.c_str(), "r");
        if (p) {
            char buf[128];
            if (fgets(buf, sizeof(buf), p)) { git_head = strip(buf); have_git = true; }
            pclose(p);
        }
    }
    if (have_header) {
        if (have_git && is_hex40(git_head)) {
            record(hdr_commit == git_head,
                   "L3.1 header commit == git HEAD (" + git_head.substr(0, 12) +
                       "...)");
        } else {
            record(hdr_commit == "unknown",
                   "L3.1 no git HEAD -> header commit is 'unknown'");
        }
        record(is_hex40(hdr_commit) || hdr_commit == "unknown",
               "L3.2 commit is a 40-hex SHA or 'unknown'");
    }

    // L4: CHANGELOG carries the same semantic version (release identity).
    std::string changelog;
    bool have_changelog = read_file("CHANGELOG.md", changelog);
    record(have_changelog, "L4.0 CHANGELOG.md exists");
    if (have_changelog && have_version) {
        std::string v = strip(version_raw);
        // Keep a Changelog headers are `## [v0.0.6.2]` or `## [0.0.6.2]`.
        bool listed = changelog.find("[" + v + "]") != std::string::npos ||
                      changelog.find("[v" + v + "]") != std::string::npos;
        record(listed, "L4.1 CHANGELOG mentions [" + v + "] (or [v" + v + "])");
    }

    // L5: README no longer advertises a contradictory identity string.
    std::string readme;
    bool have_readme = read_file("README.md", readme);
    record(have_readme, "L5.0 README.md exists");
    if (have_readme) {
        record(readme.find("UNIFIED_011.1 canonical") == std::string::npos,
               "L5.1 README drops the stale UNIFIED_011.1 identity");
        record(readme.find("MiniAndroid Runtime v0.1") == std::string::npos,
               "L5.2 README drops the stale 'v0.1' literal");
    }

    std::cout << "== " << g_pass << " passed / " << g_fail << " failed ==\n";
    std::cout << (g_fail == 0 ? "VERSION IDENTITY DOMAIN CLOSED\n"
                              : "VERSION IDENTITY DOMAIN STILL OPEN\n");
    return g_fail == 0 ? 0 : 1;
}
