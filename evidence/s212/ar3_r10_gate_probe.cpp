// ar3_r10_gate_probe.cpp — 5 assertions over mininet::http_get with the
// real build/api/http_client.o; expected final line: R10 GATE PROBE: 5/5 PASS
#include "api/http_client.h"
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
static int failures = 0;
static void check(const char* name, bool ok, const std::string& detail) {
    std::printf("[%s] %s — %s\n", ok ? "PASS" : "FAIL", name, detail.c_str());
    if (!ok) ++failures;
}
int main() {
    unsetenv("MINIANDROID_HTTP_MODE");
    { auto r = mininet::http_get("http://127.0.0.1:1/x", 0, 500);
      check("live-default-not-consumed", r.error.find("NET-002") == std::string::npos,
            "err='" + r.error + "'"); }
    setenv("MINIANDROID_HTTP_MODE", "deny", 1);
    { auto r = mininet::http_get("http://example.invalid/x", 0, 500);
      check("deny-consumes", r.status == 0 &&
            r.error.find("MINIANDROID_HTTP_MODE=deny") != std::string::npos &&
            r.error.find("NET-002") != std::string::npos,
            "status=" + std::to_string(r.status) + " err='" + r.error + "'"); }
    const char* mf = "/tmp/ar3_mock_fixture.txt";
    { std::ofstream f(mf); f << "DETERMINISTIC-FIXTURE-BODY"; }
    setenv("MINIANDROID_HTTP_MODE", "mock", 1);
    setenv("MINIANDROID_HTTP_MOCK_FILE", mf, 1);
    { auto r = mininet::http_get("https://fixture.example/api", 0, 500);
      check("mock-fixture-200", r.status == 200 && r.body == "DETERMINISTIC-FIXTURE-BODY",
            "status=" + std::to_string(r.status) + " body='" + r.body + "'"); }
    setenv("MINIANDROID_HTTP_MOCK_FILE", "/tmp/ar3_no_such_fixture_xyz", 1);
    { auto r = mininet::http_get("https://fixture.example/api", 0, 500);
      check("mock-missing-fixture", r.status == 0 &&
            r.error.find("no fixture available") != std::string::npos,
            "status=" + std::to_string(r.status) + " err='" + r.error + "'"); }
    setenv("MINIANDROID_HTTP_MODE", "warp", 1);
    { auto r = mininet::http_get("https://fixture.example/api", 0, 500);
      check("unknown-mode", r.status == 0 &&
            r.error.find("unknown MINIANDROID_HTTP_MODE 'warp'") != std::string::npos,
            "status=" + std::to_string(r.status) + " err='" + r.error + "'"); }
    std::printf(failures == 0 ? "R10 GATE PROBE: 5/5 PASS\n" : "R10 GATE PROBE: FAILURES\n");
    return failures == 0 ? 0 : 1;
}
