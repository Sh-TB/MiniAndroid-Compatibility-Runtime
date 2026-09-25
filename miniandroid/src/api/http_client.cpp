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
#include <cstring>

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
        if (line.size() > 64 * 1024) return true;  // header line bound
    }
}

// Read exactly n body bytes (or until EOF).
std::string read_exact(SSL* ssl, int fd, size_t n) {
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
        unsigned long chunk = strtoul(sz_line.c_str(), nullptr, 16);
        if (chunk == 0) {
            // trailers until blank line
            std::string t;
            while (read_line_ssl(ssl, fd, t) && !t.empty()) {}
            break;
        }
        out += read_exact(ssl, fd, chunk);
        std::string crlf;
        read_line_ssl(ssl, fd, crlf);  // consume chunk terminator
        if (out.size() > kMaxBody) break;
    }
    return out;
}

// One request hop (no redirect following here).
HttpResponse fetch_once(const std::string& scheme, const std::string& host,
                        const std::string& port, const std::string& path,
                        int timeout_ms) {
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

    std::string req = "GET " + path + " HTTP/1.1\r\n"
                      "Host: " + host +
                      (port.empty() ? "" : (":" + port)) + "\r\n"
                      "User-Agent: MiniAndroid/0.1 (S100 NET-001; Linux)\r\n"
                      "Accept: */*\r\n"
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
    for (;;) {
        std::string h;
        if (!read_line_ssl(ssl, fd, h)) break;
        if (h.empty()) break;
        size_t colon = h.find(':');
        if (colon != std::string::npos)
            r.headers[lower(h.substr(0, colon))] = h.substr(colon + 1);
    }

    std::string te, cl;
    bool chunked = r.header("transfer-encoding", te) &&
                   te.find("chunked") != std::string::npos;
    bool has_len = r.header("content-length", cl);
    if (chunked) {
        r.body = read_chunked(ssl, fd);
    } else if (has_len) {
        r.body = read_exact(ssl, fd, (size_t)strtoul(cl.c_str(), nullptr, 10));
    } else {
        // read until close
        char buf[16384];
        int n;
        while ((n = ssl ? SSL_read(ssl, buf, sizeof(buf))
                        : (int)recv(fd, buf, sizeof(buf), 0)) > 0)
            r.body.append(buf, (size_t)n);
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
    HttpResponse combined;
    std::string current = url;
    for (int hop = 0; hop <= (max_redirects > 0 ? max_redirects : 0) + 1; ++hop) {
        UrlParts p = parse_url(current);
        if (!p.valid) {
            combined.error = "bad url: " + current;
            return combined;
        }
        HttpResponse r = fetch_once(p.scheme, p.host, p.port, p.path,
                                    timeout_ms);
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
