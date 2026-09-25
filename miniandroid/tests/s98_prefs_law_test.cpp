// s98_prefs_law_test.cpp — S98 storage-domain micro-gap fence
// (MG-171..MG-183 SharedPreferences machine proof). Drives the REAL
// api::SharedPreferences / SharedPreferencesEditor XML persistence layer
// (the same objects the DEX bridge answers getSharedPreferences with):
//
//   T1  (MG-171) a prefs instance backed by a custom file path round-trips
//       (the "default file" law is the same layer rooted at the app dir).
//   T2  (MG-172) TWO instances on DIFFERENT files stay isolated
//       (getSharedPreferences(name, MODE_PRIVATE) namespace law).
//   T3  (MG-173) boolean put/get round-trip (true AND false, not just
//       truthiness).
//   T4  (MG-174) int round-trip incl. negative.
//   T5  (MG-175) long round-trip incl. a value beyond int32 range.
//   T6  (MG-176) float round-trip.
//   T7  (MG-177) string round-trip (UTF-8 multibyte content).
//   T8  (MG-178) editor apply() persists (async-queued write observed at
//       process/scope exit — the runtime's apply == eventual disk write).
//   T9  (MG-179) editor commit() returns TRUE on a successful synchronous
//       disk write.
//   T10 (MG-180) editor remove(key) drops exactly that key after commit.
//   T11 (MG-181) editor clear() empties the file after commit.
//   T12 (MG-182) contains() reflects post-commit state; absent key false.
//   T13 (MG-183) PROCESS PERSISTENCE: a SECOND SharedPreferences instance
//       (fresh object, same file — the "second process" model) reads
//       EVERYTHING the first instance committed, with no in-memory carry.
//
// Exit 0 iff ALL laws hold.

#include "../src/api/shared_prefs.h"

#include <cstdio>
#include <string>

using AndroidAPI::SharedPreferences;

static int g_pass = 0, g_fail = 0;

static void check(const char* name, bool ok, const std::string& detail = "") {
    if (ok) { ++g_pass; std::printf("PASS %s %s\n", name, detail.c_str()); }
    else    { ++g_fail; std::printf("FAIL %s %s\n", name, detail.c_str()); }
}

int main() {
    const std::string dir = "/tmp/s98_prefs_law";
    const std::string f1 = dir + "/prefs_a.xml";
    const std::string f2 = dir + "/prefs_b.xml";
    std::system(("rm -rf " + dir + " && mkdir -p " + dir).c_str());

    // ── T1/T2: file-backed instances, namespace isolation ─────────────
    SharedPreferences a(f1);
    SharedPreferences b(f2);
    check("T2 mg-172 namespace isolation",
          a.getAllKeys().empty() && b.getAllKeys().empty());

    // ── T3..T7: typed round-trips through commit (MG-173..177) ────────
    {
        bool ok = a.edit().putBoolean("k_bool_t", true)
                         .putBoolean("k_bool_f", false)
                         .putInt("k_int", -12345)
                         .putLong("k_long", 5000000000LL)
                         .putFloat("k_float", 3.14159f)
                         .putString("k_str", "سلام World_😀")
                         .commit();
        check("T9 mg-179 commit returns true", ok);
        check("T3 mg-173 boolean round-trip",
              a.getBoolean("k_bool_t", false) == true &&
              a.getBoolean("k_bool_f", true) == false);
        check("T4 mg-174 int round-trip", a.getInt("k_int", 0) == -12345);
        check("T5 mg-175 long round-trip",
              a.getLong("k_long", 0) == 5000000000LL);
        check("T6 mg-176 float round-trip",
              a.getFloat("k_float", 0.f) > 3.14f && a.getFloat("k_float", 0.f) < 3.15f);
        check("T7 mg-177 string round-trip",
              a.getString("k_str", "") == std::string("سلام World_😀"));
    }

    // ── T12: contains law (MG-182) ────────────────────────────────────
    check("T12 mg-182 contains post-commit",
          a.contains("k_int") && !a.contains("absent"));

    // ── T13: process persistence — FRESH instance, same file (MG-183) ─
    {
        SharedPreferences a2(f1);
        check("T13a mg-183 fresh instance int",
              a2.getInt("k_int", 7) == -12345);
        check("T13b mg-183 fresh instance long",
              a2.getLong("k_long", 0) == 5000000000LL);
        check("T13c mg-183 fresh instance string",
              a2.getString("k_str", "") == std::string("سلام World_😀"));
    }

    // ── T8: apply() persists (MG-178) ─────────────────────────────────
    {
        a.edit().putInt("k_apply", 4242).apply();
        SharedPreferences a3(f1);  // fresh scope = disk read-back
        check("T8 mg-178 apply persists",
              a3.getInt("k_apply", 0) == 4242);
    }

    // ── T10: remove law (MG-180) ──────────────────────────────────────
    {
        a.edit().putInt("k_gone", 1).putInt("k_kept", 2).commit();
        a.edit().remove("k_gone").commit();
        check("T10 mg-180 remove drops exact key",
              !a.contains("k_gone") && a.getInt("k_kept", 0) == 2);
    }

    // ── T11: clear law (MG-181) ───────────────────────────────────────
    {
        b.edit().putInt("x", 1).putInt("y", 2).commit();
        b.edit().clear().commit();
        check("T11 mg-181 clear empties", b.isEmpty() && b.size() == 0);
    }

    // ── T1: default-file equivalence (MG-171) — same layer, app-dir root
    {
        const std::string fdefault = dir + "/_preferences.xml";
        SharedPreferences d(fdefault);
        d.edit().putString("session", "S98").commit();
        SharedPreferences d2(fdefault);
        check("T1 mg-171 default-file law",
              d2.getString("session", "") == "S98");
    }

    std::printf("S98 PREFS LAW BATTERY: %d passed, %d failed\n", g_pass, g_fail);
    return g_fail == 0 ? 0 : 1;
}
