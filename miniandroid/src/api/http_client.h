#pragma once
// ============================================================================
// S100 / NET-001 (MG-247/248) — REAL HTTP(S) CLIENT for the MiniAndroid
// runtime host side.
//
// Upstream provenance (source-first law):
//   * libcore luni URL/HttpURLConnection semantics (status, headers,
//     redirects, getInputStream).
//   * okhttp connection reuse model is NOT needed at this stage: one
//     connectionless GET per HttpURLConnection object, no pooling.
//   * TLS: OpenSSL (the reference implementation BoringSSL is a fork of) —
//     https via libssl, http via plain POSIX sockets.
//
// Scope (honest): GET with redirects (301/302/303/307/308, max 5),
// Content-Length and chunked bodies, connect/read timeouts, response caps.
// No POST, no cookies, no proxy, no keep-alive, no HTTP/2. Deviations
// from libcore are recorded at the call site by the bridge.
// ============================================================================
#include <map>
#include <string>

namespace mininet {

struct HttpResponse {
    int status = 0;                                  // 200/301/…/0 = transport error
    std::string status_line;
    std::map<std::string, std::string> headers;      // lower-cased keys
    std::string body;
    std::string final_url;                           // after redirects
    std::string error;                               // non-empty => transport failure
    int redirect_count = 0;

    bool ok() const { return status >= 200 && status < 300 && error.empty(); }
    bool header(const char* name, std::string& out) const {
        auto it = headers.find(name);
        if (it == headers.end()) return false;
        out = it->second;
        return true;
    }
};

// Perform an HTTP(S) GET. max_redirects <= 0 means no redirects.
// timeout_ms clamps connect and per-read waits. body cap: 8 MiB.
HttpResponse http_get(const std::string& url, int max_redirects = 5,
                      int timeout_ms = 15000);

// Parse "scheme://host[:port]/path?query" (path defaults "/").
struct UrlParts {
    std::string scheme, host, port, path;   // port empty => default
    bool valid = false;
};
UrlParts parse_url(const std::string& url);

}  // namespace mininet
