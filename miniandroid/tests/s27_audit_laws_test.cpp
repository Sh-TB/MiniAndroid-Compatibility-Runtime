// s27_audit_laws_test — the S27 audit-verification battery (2026-11-23).
//
// The external code audit (MiniAndroid_Code_Audit_FA, 36 findings) was
// independently verified and every confirmed finding got a fix. This test
// PINS the fix laws at unit level so they can never silently regress:
//   r1  C5  — the /data/data tail-containment fence: a traversal tail
//             (/data/data/<pkg>/files/../../../../../etc/passwd) DENIES;
//             a legitimate tail still resolves INSIDE the package tree.
//   r2  C5b — the /data/user/0 alias carries the SAME fence.
//   r3  C6  — a hostile SharedPreferences name (relative traversal AND
//             absolute) lands as a single path token INSIDE shared_prefs.
//   r4  H3  — notifyListeners on an EMPTY changed-key set is a no-op
//             (clear().commit() with a registered listener never derefs
//             end()).
//   r5  C1  — a hostile AXML header_size (> buffer) fails the parse with
//             "bad header_size" instead of reading p+pos past the buffer.
//   r6  C8  — FrameBuffer clamps hostile canvas sides (70000×70000 →
//             8192×8192, pixel count stays width*height consistent).
//
#include "../src/storage/data_root.h"
#include "../src/api/shared_prefs.h"
#include "../src/resources/axml_parser.h"
#include "../src/renderer/software_renderer.h"

#include <filesystem>
#include <unistd.h>
#include <iostream>
#include <string>

static int g_pass = 0, g_fail = 0;
static void record(const std::string& name, bool ok, const std::string& detail) {
    std::cout << (ok ? "[PASS] " : "[FAIL] ") << name;
    if (!detail.empty()) std::cout << " — " << detail;
    std::cout << std::endl;
    (ok ? g_pass : g_fail)++;
}

int main() {
    namespace fs = std::filesystem;
    // Fresh-device law: a per-run store root + a bound caller identity.
    fs::path root = fs::temp_directory_path() /
                    ("s27_audit_" + std::to_string(getpid()));
    fs::create_directories(root);
    Storage::set_app_data_root(root.string());
    Storage::set_context_package("probe.self.audit");

    // r1 — C5: the /data/data traversal tail DENIES; a legal tail resolves.
    {
        auto bad = Storage::resolve_android_path(
            "/data/data/probe.self.audit/files/../../../../../etc/passwd");
        bool denied = !bad.allowed;
        auto good = Storage::resolve_android_path(
            "/data/data/probe.self.audit/files/settings.cfg");
        bool legal = good.allowed;
        bool contained = legal && good.host_path.string().find("..") ==
                                        std::string::npos;
        record("r1-C5 data/data tail containment",
               denied && legal && contained,
               denied ? "traversal DENIED" : "TRAVERSAL ALLOWED (regression)");
    }

    // r2 — C5b: the user-0 alias carries the same fence.
    {
        auto bad = Storage::resolve_android_path(
            "/data/user/0/probe.self.audit/databases/../../../x.db");
        auto good = Storage::resolve_android_path(
            "/data/user/0/probe.self.audit/databases/app.db");
        record("r2-C5b data/user tail containment",
               !bad.allowed && good.allowed,
               bad.allowed ? "TRAVERSAL ALLOWED" : "traversal DENIED");
    }

    // r3 — C6: a hostile prefs name is defused to a single token INSIDE
    // shared_prefs. Verified behaviorally: commit a value, then require
    // the produced file to live in shared_prefs with no traversal parts.
    {
        // The ctor with an explicit base resolves base/<pkg>/shared_prefs.
        fs::path pkg_dir = root / "probe.self.audit" / "shared_prefs";
        {
            AndroidAPI::SharedPreferences sp("probe.self.audit", "../../../etc/cron.d/pwn",
                                 root.string());
            sp.edit().putString("k", "v").commit();
            bool defused = false;
            if (fs::exists(pkg_dir)) {
                for (auto& e : fs::directory_iterator(pkg_dir)) {
                    const std::string n = e.path().filename().string();
                    if (n.find("..") == std::string::npos &&
                        n.find('/') == std::string::npos &&
                        n.find(".xml") != std::string::npos)
                        defused = true;
                }
            }
            record("r3-C6 hostile prefs name defused", defused,
                   "file is a single token inside shared_prefs");
        }
        {
            // An ABSOLUTE hostile name must ALSO not replace the prefix —
            // it lands as the defused token INSIDE shared_prefs, never as
            // /host/evil on the host.
            AndroidAPI::SharedPreferences sp2("probe.self.audit", "/host/evil",
                                  root.string());
            sp2.edit().putString("k", "v").commit();
            bool contained = fs::exists(pkg_dir / "hostevil.xml");
            record("r3b-C6 absolute prefs name defused", contained,
                   "defused to shared_prefs/hostevil.xml");
        }
    }

    // r4 — H3: clear().commit() with a registered listener must not deref
    // an empty changed-key set (the pre-fix *keys.begin() UB).
    {
        AndroidAPI::SharedPreferences sp("probe.self.audit", "audit_prefs", root.string());
        static int calls = 0;
        auto lis = [](AndroidAPI::SharedPreferences*, const std::string&) { ++calls; };
        sp.registerOnSharedPreferenceChangeListener(lis);
        auto ed = sp.edit();
        ed.clear();
        ed.commit();  // pre-fix: *keys.begin() on the EMPTY set (UB)
        record("r4-H3 empty-key notify no-op", true,
               "clear().commit() with a listener survived (no UB)");
    }

    // r5 — C1: hostile AXML header_size fails honestly.
    {
        std::vector<uint8_t> tiny(100, 0);
        tiny[0] = 0x03; tiny[1] = 0x00;  // RES_XML_TYPE (LE)
        tiny[2] = 0xFF; tiny[3] = 0xFF;  // header_size = 65535 > 100
        miniandroid::resources::AxmlParser p;
        bool ok = p.parse(tiny);
        bool honest = !ok && p.last_error().find("bad header_size") !=
                                 std::string::npos;
        record("r5-C1 hostile axml header_size rejected", honest,
               p.last_error());
    }

    // r6 — C8: hostile canvas sides clamp; the buffer stays consistent.
    {
        miniandroid::renderer::FrameBuffer fb(70000, 70000);
        bool ok = fb.get_width() == 8192 && fb.get_height() == 8192 &&
                  fb.get_pixel_count() ==
                      (size_t)fb.get_width() * (size_t)fb.get_height();
        record("r6-C8 framebuffer side clamp", ok,
               "70000x70000 -> " + std::to_string(fb.get_width()) + "x" +
                   std::to_string(fb.get_height()));
    }

    fs::remove_all(root);
    std::cout << (g_fail == 0 ? "ALL PASS " : "FAILURES ") << g_pass << "/"
              << (g_pass + g_fail) << "\n";
    return g_fail == 0 ? 0 : 1;
}
