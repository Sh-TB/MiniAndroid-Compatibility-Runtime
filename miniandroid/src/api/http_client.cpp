// S100 / NET-001 — HTTP(S) client implementation (see http_client.h).
#include "http_client.h"

#include <algorithm>
#include <arpa/inet.h>
#include <fcntl.h>
#include <netdb.h>
#include <openssl/err.h>
#include <openssl/ssl.h>
#include <sys/socket.h>
#include <sys/time.h>
#include <unistd.h>

#include <cctype>
#include <cerrno>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <iostream>
#include <mutex>
#include <vector>

namespace mininet {

namespace {

constexpr size_t kMaxBody = 8u << 20;  // 8 MiB response cap (honest bound)

std::string lower(std::string s) {
    for (char& c : s) c = (char)std::tolower((unsigned char)c);
    return s;
}

// Connect with timeout (non-blocking connect + select). Returns fd or -1.
int connect_host(const std::string& host, const std::string& port,
                 int timeout_ms) {
    struct addrinfo hints;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    struct addrinfo* res = nullptr;
    if (getaddrinfo(host.c_str(), port.c_str(), &hints, &res) != 0 || !res)
        return -1;
    int fd = -1;
    for (struct addrinfo* ai = res; ai; ai = ai->ai_next) {
        fd = socket(ai->ai_family, ai->ai_socktype, ai->ai_protocol);
        if (fd < 0) continue;
        // Non-blocking connect with select-based timeout.
        int flags = fcntl(fd, F_GETFL, 0);
        fcntl(fd, F_SETFL, flags | O_NONBLOCK);
        int rc = connect(fd, ai->ai_addr, ai->ai_addrlen);
        if (rc == 0) {
            fcntl(fd, F_SETFL, flags);
            break;
        }
        if (errno == EINPROGRESS) {
            fd_set wfds;
            FD_ZERO(&wfds);
            FD_SET(fd, &wfds);
            struct timeval tv{timeout_ms / 1000, (timeout_ms % 1000) * 1000};
            if (select(fd + 1, nullptr, &wfds, nullptr, &tv) > 0) {
                int err = 0;
                socklen_t len = sizeof(err);
                getsockopt(fd, SOL_SOCKET, SO_ERROR, &err, &len);
                if (err == 0) {
                    fcntl(fd, F_SETFL, flags);
                    break;
                }
            }
        }
        close(fd);
        fd = -1;
    }
    freeaddrinfo(res);
    return fd;
}

// Read one "line" (CRLF-terminated) from a plain fd or SSL stream.
bool read_line_ssl(SSL* ssl, int fd, std::string& line) {
    line.clear();
    char c;
    for (;;) {
        int n = ssl ? SSL_read(ssl, &c, 1) : (int)recv(fd, &c, 1, 0);
        if (n <= 0) return !line.empty();
        if (c == '\n') {
            if (!line.empty() && line.back() == '\r') line.pop_back();
            return true;
        }
        line.push_back(c);
        if (line.size() > 64 * 1024) {
            // GP-NET-002: the old bound returned `true` WITHOUT consuming
            // the rest of the peer's line — the next header read resumed in
            // the middle of the oversized line. Drain the remainder, then
            // report the line as unusable (false) so the caller aborts.
            char sink;
            int drained = 0;
            while ((ssl ? SSL_read(ssl, &sink, 1)
                        : (int)recv(fd, &sink, 1, 0)) == 1) {
                if (sink == '\n') break;
                if (++drained > (1 << 20)) break;
            }
            return false;
        }
    }
}

// Read exactly n body bytes (or until EOF).
// GP-NET-001 (issue #582): `n` is peer-controlled; the cap must bound what
// is READ/RETAINED, not truncate afterwards. read_exact clamps its own work
// to the response cap; callers pre-check their declared lengths and mark
// oversize bodies as transport errors (below).
std::string read_exact(SSL* ssl, int fd, size_t n) {
    if (n > kMaxBody) n = kMaxBody;
    std::string out;
    out.reserve(n < (1u << 20) ? n : (1u << 20));
    char buf[16384];
    while (out.size() < n) {
        size_t want = n - out.size();
        int r = ssl ? SSL_read(ssl, buf, (int)std::min(want, sizeof(buf)))
                    : (int)recv(fd, buf, (int)std::min(want, sizeof(buf)), 0);
        if (r <= 0) break;
        out.append(buf, (size_t)r);
    }
    return out;
}

// Chunked transfer decoding (RFC 7230 §4.1 — same law libcore implements).
std::string read_chunked(SSL* ssl, int fd) {
    std::string out;
    for (;;) {
        std::string sz_line;
        if (!read_line_ssl(ssl, fd, sz_line)) break;
        size_t semi = sz_line.find(';');
        if (semi != std::string::npos) sz_line = sz_line.substr(0, semi);
        // GP-NET-001: strict chunk-size parse (hex digits only, overflow
        // checked) — strtoul accepted overflow wraps and junk silently.
        if (sz_line.empty() ||
            sz_line.find_first_not_of("0123456789abcdefABCDEF") !=
                std::string::npos) {
            std::cerr << "[HTTP] malformed chunk size line — abort body"
                      << std::endl;
            break;
        }
        unsigned long long chunk = 0;
        bool ovf = false;
        for (char c : sz_line) {
            chunk = chunk * 16ull + (unsigned long long)
                (c <= '9' ? c - '0' : (c | 0x20) - 'a' + 10);
            if (chunk > (unsigned long long)kMaxBody) { ovf = true; break; }
        }
        if (ovf || chunk == 0) {
            if (chunk == 0) {
                // trailers until blank line
                std::string t;
                while (read_line_ssl(ssl, fd, t) && !t.empty()) {}
                break;
            }
            std::cerr << "[HTTP] chunk size exceeds body cap — abort body"
                      << std::endl;
            break;
        }
        if (out.size() + chunk > kMaxBody) {
            // budget enforced BEFORE the read: read only what remains,
            // then stop (the retained body never exceeds the cap).
            size_t remain = kMaxBody - out.size();
            out += read_exact(ssl, fd, remain);
            std::cerr << "[HTTP] chunked body exceeded 8 MiB cap — truncated "
                      << "at cap" << std::endl;
            break;
        }
        out += read_exact(ssl, fd, (size_t)chunk);
        std::string crlf;
        read_line_ssl(ssl, fd, crlf);  // consume chunk terminator
    }
    return out;
}


// ── S133 COOKIE STORE LAW (RFC 6265 §5.3/§5.4) ────────────────────────
// A real browser keeps a cookie store: Set-Cookie values are stored per
// host and echoed back on subsequent requests to that host (measured:
// chat.z.ai /api/v1/auths/ sets `token=<JWT>; HttpOnly; Path=/` and
// /api/models answers 403 without the echoed Cookie, 200 with it). The
// minimal honest subset:
//   * host-only storage (Domain attribute NOT honored → no cross-host leak)
//   * name=value pair before the first ';' (attributes ignored)
//   * session scope (process lifetime — no persistent cookie file)
//   * Cookie header only on https requests (the measured cookie is Secure)
struct CookieJar {
    std::mutex mu;
    std::map<std::string, std::map<std::string, std::string>> by_host;

    static std::string trim_copy(const std::string& s) {
        size_t b = s.find_first_not_of(" \t");
        if (b == std::string::npos) return "";
        size_t e = s.find_last_not_of(" \t");
        return s.substr(b, e - b + 1);
    }

    void store(const std::string& host, const std::string& set_cookie_value) {
        size_t semi = set_cookie_value.find(';');
        std::string nv = semi == std::string::npos
                             ? set_cookie_value
                             : set_cookie_value.substr(0, semi);
        size_t eq = nv.find('=');
        if (eq == std::string::npos) return;
        std::string name = trim_copy(nv.substr(0, eq));
        std::string value = trim_copy(nv.substr(eq + 1));
        if (name.empty()) return;   // RFC 6265 §5.2: ignore-name form skipped
        std::lock_guard<std::mutex> lk(mu);
        by_host[host][name] = value;
    }

    std::string header_for(const std::string& host) {
        std::lock_guard<std::mutex> lk(mu);
        auto it = by_host.find(host);
        if (it == by_host.end() || it->second.empty()) return "";
        std::string out;
        for (auto& [n, v] : it->second) {
            if (!out.empty()) out += "; ";
            out += n + "=" + v;
        }
        return out;
    }
};
CookieJar& cookie_jar() {
    static CookieJar j;
    return j;
}

// One request hop (no redirect following here).
HttpResponse fetch_once(const std::string& scheme, const std::string& host,
                        const std::string& port, const std::string& path,
                        int timeout_ms,
                        const std::map<std::string, std::string>* extra_headers = nullptr) {
    HttpResponse r;
    bool is_tls = (scheme == "https");
    int fd = connect_host(host, port.empty() ? (is_tls ? "443" : "80") : port,
                          timeout_ms);
    if (fd < 0) {
        r.error = "connect failed: " + host + ":" +
                  (port.empty() ? (is_tls ? "443" : "80") : port);
        return r;
    }

    SSL_CTX* ctx = nullptr;
    SSL* ssl = nullptr;
    if (is_tls) {
        SSL_load_error_strings();
        SSL_library_init();  // idempotent in OpenSSL 3.x
        ctx = SSL_CTX_new(TLS_client_method());
        if (!ctx) {
            close(fd);
            r.error = "ssl ctx failed";
            return r;
        }
        SSL_CTX_set_default_verify_paths(ctx);
        SSL_CTX_set_verify(ctx, SSL_VERIFY_NONE, nullptr);  // honest: no pinning yet
        ssl = SSL_new(ctx);
        SSL_set_fd(ssl, fd);
        SSL_set_tlsext_host_name(ssl, host.c_str());
        struct timeval tv{timeout_ms / 1000, (timeout_ms % 1000) * 1000};
        setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
        if (SSL_connect(ssl) != 1) {
            r.error = "tls handshake failed: " + host;
            SSL_free(ssl);
            SSL_CTX_free(ctx);
            close(fd);
            return r;
        }
    } else {
        struct timeval tv{timeout_ms / 1000, (timeout_ms % 1000) * 1000};
        setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof(tv));
    }

    std::string extra;
    if (extra_headers) {
        for (auto& [name, value] : *extra_headers) {
            // S133 header-injection law (RFC 7230 §3.2): each field line is
            // "name: value" CRLF; names are forwarded verbatim (the WHATWG
            // fetch Headers normalizes case at the JS layer, not here).
            extra += name + ": " + value + "\r\n";
        }
    }
    // S133 cookie-echo law (RFC 6265 §5.4): attach the host's cookie pairs
    // unless the request already carries an explicit Cookie header.
    if (is_tls && extra_headers &&
        extra_headers->find("Cookie") == extra_headers->end() &&
        extra_headers->find("cookie") == extra_headers->end()) {
        std::string cookie = cookie_jar().header_for(host);
        if (!cookie.empty()) extra += "Cookie: " + cookie + "\r\n";
    }
    std::string req = "GET " + path + " HTTP/1.1\r\n"
                      "Host: " + host +
                      (port.empty() ? "" : (":" + port)) + "\r\n"
                      "User-Agent: MiniAndroid/0.1 (S100 NET-001; Linux)\r\n"
                      "Accept: */*\r\n"
                      + extra +
                      "Connection: close\r\n\r\n";
    bool sent = ssl ? SSL_write(ssl, req.data(), (int)req.size()) ==
                            (int)req.size()
                    : send(fd, req.data(), req.size(), 0) == (ssize_t)req.size();
    if (!sent) {
        r.error = "send failed";
        if (ssl) SSL_free(ssl);
        if (ctx) SSL_CTX_free(ctx);
        close(fd);
        return r;
    }

    std::string status_line;
    if (!read_line_ssl(ssl, fd, status_line)) {
        r.error = "no status line";
        if (ssl) SSL_free(ssl);
        if (ctx) SSL_CTX_free(ctx);
        close(fd);
        return r;
    }
    r.status_line = status_line;
    // "HTTP/1.1 200 OK"
    if (status_line.size() > 12 && status_line.compare(0, 5, "HTTP/") == 0)
        r.status = atoi(status_line.c_str() + 9);
    std::vector<std::string> set_cookies;   // S133: preserve every Set-Cookie line
    // GP-NET-002 (issue #582): no aggregate header budget existed — a peer
    // could stream unlimited header lines. 256 KiB / 256 lines bound.
    size_t header_bytes = 0;
    size_t header_lines = 0;
    bool header_overflow = false;
    for (;;) {
        std::string h;
        if (!read_line_ssl(ssl, fd, h)) break;
        if (h.empty()) break;
        header_bytes += h.size() + 2;
        if (++header_lines > 256 || header_bytes > (256u << 10)) {
            std::cerr << "[HTTP] response header budget exceeded — headers "
                         "closed, body rejected" << std::endl;
            header_overflow = true;
            break;
        }
        size_t colon = h.find(':');
        if (colon != std::string::npos) {
            std::string name = lower(h.substr(0, colon));
            // S102 LAW 5 — HEADER-OWS-TRIM (RFC 7230 §3.2): "A field value
            // does not include leading or trailing whitespace" — OWS is
            // trimmed when composing the field line, NOT part of the value.
            // Real-APK evidence (Mini Browser → https://z.ai, fresh S102
            // run): z.ai answers `location: https://chat.z.ai/` with a
            // single leading space; the untrimmed value flowed into the
            // redirect hop as " https://chat.z.ai/" → parse_url failed →
            // http_get returned the 307 as its final answer and the page
            // never loaded. Curl/openSSL trim; so must we.
            std::string v = h.substr(colon + 1);
            size_t b = v.find_first_not_of(" \t");
            if (b == std::string::npos) v.clear();
            else {
                size_t e = v.find_last_not_of(" \t");
                v = v.substr(b, e - b + 1);
            }
            if (name == "set-cookie") set_cookies.push_back(v);
            else r.headers[name] = v;
        }
    }
    // S133 cookie-store law: every Set-Cookie lands in the host jar.
    for (auto& sc : set_cookies) cookie_jar().store(host, sc);

    if (header_overflow) {
        r.error = "response header budget exceeded";
        r.status = 0;
        if (ssl) SSL_free(ssl);
        if (ctx) SSL_CTX_free(ctx);
        close(fd);
        return r;
    }
    std::string te, cl;
    bool chunked = r.header("transfer-encoding", te) &&
                   te.find("chunked") != std::string::npos;
    bool has_len = r.header("content-length", cl);
    // GP-NET-001 (issue #582): every receive path enforces the 8 MiB cap
    // BEFORE reading/retaining; the declared length is parsed strictly
    // (digits only + overflow) instead of strtoul's silent wrap.
    if (chunked) {
        r.body = read_chunked(ssl, fd);
    } else if (has_len) {
        bool cl_ok = !cl.empty() &&
                     cl.find_first_not_of("0123456789") == std::string::npos;
        unsigned long long cl_len = 0;
        if (cl_ok) {
            cl_ok = cl.size() <= 19;  // 19 digits cannot overflow u64
            if (cl_ok) {
                for (char c : cl)
                    cl_len = cl_len * 10ull + (unsigned long long)(c - '0');
            }
        }
        if (!cl_ok) {
            r.error = "malformed Content-Length";
            r.status = 0;
        } else if (cl_len > kMaxBody) {
            r.error = "response body exceeds 8 MiB cap (Content-Length)";
            r.status = 0;
        } else {
            r.body = read_exact(ssl, fd, (size_t)cl_len);
        }
    } else {
        // read until close — append only while inside the cap.
        char buf[16384];
        int n;
        while ((n = ssl ? SSL_read(ssl, buf, sizeof(buf))
                        : (int)recv(fd, buf, sizeof(buf), 0)) > 0) {
            if (r.body.size() + (size_t)n > kMaxBody) {
                size_t take = kMaxBody - r.body.size();
                r.body.append(buf, take);
                std::cerr << "[HTTP] EOF-delimited body exceeded 8 MiB cap — "
                             "truncated at cap" << std::endl;
                break;
            }
            r.body.append(buf, (size_t)n);
        }
    }
    if (r.body.size() > kMaxBody) r.body.resize(kMaxBody);

    if (ssl) SSL_free(ssl);
    if (ctx) SSL_CTX_free(ctx);
    close(fd);
    return r;
}

}  // namespace

UrlParts parse_url(const std::string& url) {
    UrlParts p;
    size_t scheme_end = url.find("://");
    if (scheme_end == std::string::npos) return p;
    p.scheme = lower(url.substr(0, scheme_end));
    if (p.scheme != "http" && p.scheme != "https") return p;
    size_t host_start = scheme_end + 3;
    size_t path_start = url.find('/', host_start);
    std::string authority = (path_start == std::string::npos)
                                ? url.substr(host_start)
                                : url.substr(host_start, path_start - host_start);
    p.path = (path_start == std::string::npos) ? "/"
             : url.substr(path_start);
    size_t at = authority.rfind('@');  // userinfo ignored
    if (at != std::string::npos) authority = authority.substr(at + 1);
    size_t colon = authority.rfind(':');
    if (colon != std::string::npos &&
        authority.find(']', colon) == std::string::npos) {
        p.host = authority.substr(0, colon);
        p.port = authority.substr(colon + 1);
    } else {
        p.host = authority;
    }
    if (p.host.empty()) return p;
    p.valid = true;
    return p;
}

HttpResponse http_get(const std::string& url, int max_redirects,
                      int timeout_ms) {
    return http_get_ex(url, {}, max_redirects, timeout_ms);
}

namespace {

// ── [A-R3] R10 (A-R2 #578, lane P1) — the HTTP MODE GATE. §27's demand is
// a deterministic boundary: today every HttpURLConnection fetch performs
// REAL host network I/O inline on the DEX thread, with no mock layer, no
// recorded-response replay, and no env gate (A-R2 R10: `HTTP_MODE|HTTP_MOCK`
// 0 hits; this file read no getenv at all). The corpus stayed hermetic only
// because its apps happen not to touch the network — the determinism
// property was undocumented and unprotected. Gate semantics (K-4):
//   MINIANDROID_HTTP_MODE=live (default) — today's behavior, byte-identical.
//   MINIANDROID_HTTP_MODE=deny  — every fetch answers the honest transport
//                                 failure shape (status 0 + error string);
//                                 loud on stderr, census-visible.
//   MINIANDROID_HTTP_MODE=mock  — serve MINIANDROID_HTTP_MOCK_FILE's bytes
//                                 as a deterministic 200 (the §27
//                                 "deterministic injected response");
//                                 missing file → deny semantics.
// The gate sits at the http_get_ex funnel (http_get delegates here), so
// every engine fetch path (URL.openStream + the fetch-once block) is
// covered by one law. Contract: returns false ONLY for mode=live (the
// caller proceeds to the socket path); returns true with `out` filled for
// every gated mode (mock fixture or loud failure shape).
bool http_gate_consume(const std::string& url, HttpResponse& out) {
    const char* mode = std::getenv("MINIANDROID_HTTP_MODE");
    std::string m = mode ? mode : "live";
    if (m == "live") return false;  // caller proceeds — today's behavior
    if (m == "mock") {
        const char* mf = std::getenv("MINIANDROID_HTTP_MOCK_FILE");
        if (mf && *mf) {
            FILE* f = std::fopen(mf, "rb");
            if (f) {
                char buf[4096];
                size_t n;
                while ((n = std::fread(buf, 1, sizeof(buf), f)) > 0)
                    out.body.append(buf, n);
                std::fclose(f);
                out.status = 200;
                out.status_line = "HTTP/1.1 200 OK (mock)";
                out.headers["content-type"] = "application/octet-stream";
                out.final_url = url;
                std::cerr << "[NET-002] HTTP MOCK: " << out.body.size()
                          << " bytes from " << mf << " for " << url
                          << std::endl;
                return true;
            }
        }
        out.error = "HTTP mock requested (MINIANDROID_HTTP_MODE=mock) but no "
                    "fixture available (NET-002, A-R3 R10)";
    } else if (m == "deny") {
        out.error = "HTTP disabled by MINIANDROID_HTTP_MODE=deny (NET-002, "
                    "A-R3 R10)";
    } else {
        out.error = "unknown MINIANDROID_HTTP_MODE '" + m +
                    "' (valid: live|mock|deny) (NET-002, A-R3 R10)";
    }
    out.status = 0;
    out.status_line = "MINIANDROID_HTTP_MODE=" + m;
    std::cerr << "[NET-002] HTTP GATE " << out.status_line << " for " << url
              << " (A-R3 R10)" << std::endl;
    return true;
}

}  // namespace

HttpResponse http_get_ex(const std::string& url,
                         const std::map<std::string, std::string>& extra_headers,
                         int max_redirects, int timeout_ms) {
    // [A-R3] R10 — the determinism gate runs BEFORE any socket is opened.
    {
        HttpResponse gated;
        if (http_gate_consume(url, gated)) return gated;
    }
    HttpResponse combined;
    std::string current = url;
    for (int hop = 0; hop <= (max_redirects > 0 ? max_redirects : 0) + 1; ++hop) {
        UrlParts p = parse_url(current);
        if (!p.valid) {
            combined.error = "bad url: " + current;
            return combined;
        }
        HttpResponse r = fetch_once(p.scheme, p.host, p.port, p.path,
                                    timeout_ms, &extra_headers);
        combined = r;
        combined.final_url = current;
        combined.redirect_count = hop;
        bool redirect = (r.status == 301 || r.status == 302 || r.status == 303 ||
                         r.status == 307 || r.status == 308);
        if (redirect && hop < max_redirects + 1) {
            std::string loc;
            if (r.header("location", loc)) {
                // relative location resolution (RFC 7231 §7.1.2)
                if (!loc.empty() && loc[0] == '/') {
                    UrlParts base = parse_url(current);
                    current = base.scheme + "://" + base.host +
                              (base.port.empty() ? "" : ":" + base.port) + loc;
                } else if (loc.find("://") == std::string::npos) {
                    UrlParts base = parse_url(current);
                    std::string dir = base.path.substr(0, base.path.rfind('/') + 1);
                    current = base.scheme + "://" + base.host +
                              (base.port.empty() ? "" : ":" + base.port) + dir + loc;
                } else {
                    current = loc;
                }
                continue;
            }
        }
        return combined;
    }
    return combined;
}

}  // namespace mininet
