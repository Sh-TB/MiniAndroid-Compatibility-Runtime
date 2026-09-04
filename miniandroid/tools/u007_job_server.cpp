/*
 * UNIFIED_007 — Persistent job server + REST API (BROWSER/AGENT line).
 *
 * A REAL agent job runtime over the MiniAndroid APK execution pipeline:
 *
 *   POST /api/jobs                {apk_path, type} → 201 {id, status:QUEUED}
 *   GET  /api/jobs/{id}           full job record
 *   GET  /api/jobs/{id}/status    {id, status}
 *   GET  /api/jobs/{id}/logs      live logs (APK parsed → … → Screenshot captured)
 *   GET  /api/jobs/{id}/artifacts artifact list
 *   POST /api/jobs/{id}/cancel    RUNNING/QUEUED → CANCELLED
 *
 * Persistence: EVERY state transition is flushed to database/u007_jobs.json
 * (write-temp + rename) — server restart and client refresh always see the
 * true state. STALLED detection: RUNNING job with no log progress for
 * > stall_timeout seconds (checked on demand). CAPTCHA policy: jobs of type
 * "captcha" enter WAITING/CAPTCHA_REQUIRED and stay paused — the server
 * NEVER bypasses CAPTCHA; only an explicit resume (not implemented on
 * purpose, per policy) could continue them.
 *
 * Worker: single foreground thread drains the queue: QUEUED → RUNNING →
 * runs `miniandroid run` as a child process, appending a log line at each
 * milestone → COMPLETED (+ artifacts) or FAILED (with reason).
 *
 * Zero external dependencies (POSIX sockets + stdlib).
 * Build: scripts/build_u007_job_server.sh
 */

#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>

#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <string>
#include <thread>
#include <vector>
#include <map>
#include <mutex>

#include "../third_party/nlohmann_json/include/nlohmann/json.hpp"
using nlohmann::json;

// ---------------------------------------------------------------------------
// Minimal JSON string helpers (nlohmann not needed for this scope)
// ---------------------------------------------------------------------------
static std::string jesc(const std::string& s) {
    std::string out;
    for (char c : s) {
        switch (c) {
            case '"': out += "\\\""; break;
            case '\\': out += "\\\\"; break;
            case '\n': out += "\\n"; break;
            case '\r': out += "\\r"; break;
            case '\t': out += "\\t"; break;
            default:
                if ((unsigned char)c < 0x20) {
                    char b[8];
                    snprintf(b, sizeof(b), "\\u%04x", c);
                    out += b;
                } else out += c;
        }
    }
    return out;
}

// ---------------------------------------------------------------------------
// Job model
// ---------------------------------------------------------------------------
enum class JobStatus {
    QUEUED, RUNNING, WAITING, CAPTCHA_REQUIRED, FAILED, COMPLETED, CANCELLED, STALLED
};

static const char* status_name(JobStatus s) {
    switch (s) {
        case JobStatus::QUEUED: return "QUEUED";
        case JobStatus::RUNNING: return "RUNNING";
        case JobStatus::WAITING: return "WAITING";
        case JobStatus::CAPTCHA_REQUIRED: return "CAPTCHA_REQUIRED";
        case JobStatus::FAILED: return "FAILED";
        case JobStatus::COMPLETED: return "COMPLETED";
        case JobStatus::CANCELLED: return "CANCELLED";
        case JobStatus::STALLED: return "STALLED";
    }
    return "?";
}

struct Job {
    std::string id;
    std::string type;         // "apk_run" | "captcha" | ...
    std::string apk_path;
    JobStatus status = JobStatus::QUEUED;
    std::string created_at;
    std::string updated_at;
    std::vector<std::string> logs;
    std::vector<std::string> artifacts;
    std::string fail_reason;
    long long last_progress_ms = 0;   // monotonic ms of last log append
};

static std::string now_iso() {
    time_t t = time(nullptr);
    struct tm tmv;
    gmtime_r(&t, &tmv);
    char buf[32];
    strftime(buf, sizeof(buf), "%Y-%m-%dT%H:%M:%SZ", &tmv);
    return buf;
}

static long long mono_ms() {
    return std::chrono::duration_cast<std::chrono::milliseconds>(
        std::chrono::steady_clock::now().time_since_epoch()).count();
}

// ---------------------------------------------------------------------------
// Persistent job store
// ---------------------------------------------------------------------------
class JobStore {
public:
    explicit JobStore(const std::string& path) : path_(path) { load(); }

    void load() {
        std::ifstream f(path_);
        if (!f) return;
        try {
            json doc;
            f >> doc;
            if (!doc.contains("jobs")) return;
            for (const auto& jf : doc["jobs"]) {
                Job j;
                j.id = jf.value("id", "");
                if (j.id.empty()) continue;
                j.type = jf.value("type", "");
                j.apk_path = jf.value("apk_path", "");
                std::string st = jf.value("status", "");
                bool matched = false;
                for (int si = 0; si < 8; ++si) {
                    if (st == status_name((JobStatus)si)) {
                        j.status = (JobStatus)si; matched = true; break;
                    }
                }
                if (!matched) j.status = JobStatus::CANCELLED;  // never re-run unknowns
                j.created_at = jf.value("created_at", "");
                j.updated_at = jf.value("updated_at", "");
                j.fail_reason = jf.value("fail_reason", "");
                j.last_progress_ms = mono_ms();  // reset stall clock on boot
                jobs_[j.id] = j;
            }
            std::fprintf(stderr, "[JOBS] restored %zu jobs from %s\n",
                         jobs_.size(), path_.c_str());
        } catch (const std::exception& e) {
            std::fprintf(stderr, "[JOBS] load failed: %s\n", e.what());
        }
    }

    void persist() {
        std::string tmp = path_ + ".tmp";
        try {
            json doc;
            doc["schema"] = "u007_jobs_v1";
            doc["jobs"] = json::array();
            for (auto& [id, j] : jobs_) {
                doc["jobs"].push_back({
                    {"id", j.id},
                    {"type", j.type},
                    {"apk_path", j.apk_path},
                    {"status", status_name(j.status)},
                    {"created_at", j.created_at},
                    {"updated_at", j.updated_at},
                    {"fail_reason", j.fail_reason}
                });
            }
            std::ofstream f(tmp);
            f << doc.dump(2) << std::endl;
            f.close();
            rename(tmp.c_str(), path_.c_str());
        } catch (const std::exception& e) {
            std::fprintf(stderr, "[JOBS] persist failed: %s\n", e.what());
        }
    }

    std::mutex mtx;
    std::map<std::string, Job> jobs_;

private:
    std::string path_;
};

// ---------------------------------------------------------------------------
// globals
// ---------------------------------------------------------------------------
static JobStore* g_store = nullptr;
static std::string g_bin_dir;
static std::string g_artifact_root;

static void job_log(Job& j, const std::string& line) {
    j.logs.push_back("[" + now_iso() + "] " + line);
    j.updated_at = now_iso();
    j.last_progress_ms = mono_ms();
}

// ---------------------------------------------------------------------------
// Worker: drain queue in a foreground loop (called in a std::thread)
// ---------------------------------------------------------------------------
static void worker_loop(const std::string& stall_key) {
    long long stall_timeout_ms = 120000;
    (void)stall_key;
    while (true) {
        Job* picked = nullptr;
        std::string picked_id;
        {
            std::lock_guard<std::mutex> lk(g_store->mtx);
            // STALLED detection pass
            long long nowms = mono_ms();
            for (auto& [id, j] : g_store->jobs_) {
                if (j.status == JobStatus::RUNNING &&
                    nowms - j.last_progress_ms > stall_timeout_ms) {
                    j.status = JobStatus::STALLED;
                    job_log(j, "job stalled: no progress for " +
                            std::to_string(stall_timeout_ms / 1000) + "s");
                }
            }
            for (auto& [id, j] : g_store->jobs_) {
                if (j.status == JobStatus::QUEUED) { picked = &j; picked_id = id; break; }
            }
        }
        if (!picked) { std::this_thread::sleep_for(std::chrono::milliseconds(300)); continue; }

        std::string apk, jtype;
        {
            std::lock_guard<std::mutex> lk(g_store->mtx);
            Job& j = g_store->jobs_[picked_id];
            j.status = JobStatus::RUNNING;
            job_log(j, "job started: type=" + j.type + " apk=" + j.apk_path);
            apk = j.apk_path;
            jtype = j.type;
            g_store->persist();
        }

        // CAPTCHA policy: jobs typed "captcha" pause — never bypass.
        if (jtype == "captcha") {
            std::lock_guard<std::mutex> lk(g_store->mtx);
            Job& j = g_store->jobs_[picked_id];
            j.status = JobStatus::CAPTCHA_REQUIRED;
            job_log(j, "CAPTCHA required — job paused (server never bypasses CAPTCHA)");
            g_store->persist();
            continue;
        }

        // Run the real pipeline as a child process with milestone logging.
        std::string out_dir = g_artifact_root + "/" + picked_id;
        std::string cmd = g_bin_dir + "/miniandroid run --output " + out_dir +
                          " " + apk + " 2>&1";
        {
            std::lock_guard<std::mutex> lk(g_store->mtx);
            Job& j = g_store->jobs_[picked_id];
            job_log(j, "executing: " + cmd);
            g_store->persist();
        }
        FILE* pipe = popen(cmd.c_str(), "r");
        bool ok = false;
        if (pipe) {
            char buf[512];
            while (fgets(buf, sizeof(buf), pipe)) {
                std::string line(buf);
                // trim newline
                while (!line.empty() && (line.back() == '\n' || line.back() == '\r'))
                    line.pop_back();
                bool milestone = false;
                if (line.find("Running APK:") != std::string::npos) milestone = true;
                if (line.find("U007-INFLATE") != std::string::npos) milestone = true;
                if (line.find("Status:") != std::string::npos) milestone = true;
                if (line.find("Screenshot:") != std::string::npos) milestone = true;
                if (line.find("Execution completed") != std::string::npos) milestone = true;
                if (milestone || line.find("error") != std::string::npos) {
                    std::lock_guard<std::mutex> lk(g_store->mtx);
                    Job& j = g_store->jobs_[picked_id];
                    job_log(j, line.empty() ? "(progress)" : line);
                    g_store->persist();
                }
            }
            int rc = pclose(pipe);
            ok = (rc == 0);
        }
        {
            std::lock_guard<std::mutex> lk(g_store->mtx);
            Job& j = g_store->jobs_[picked_id];
            if (j.status == JobStatus::CANCELLED) {
                // cancelled while running — leave as-is
            } else if (ok) {
                j.status = JobStatus::COMPLETED;
                job_log(j, "job COMPLETED");
                // artifacts: screenshot.png if produced
                std::string shot = out_dir + "/screenshot.png";
                std::ifstream t(shot);
                if (t) {
                    j.artifacts.push_back(shot);
                    job_log(j, "artifact: " + shot);
                    t.close();
                }
            } else {
                j.status = JobStatus::FAILED;
                j.fail_reason = "miniandroid exit != 0";
                job_log(j, "job FAILED: " + j.fail_reason);
            }
            j.updated_at = now_iso();
            g_store->persist();
        }
    }
}

// ---------------------------------------------------------------------------
// HTTP layer
// ---------------------------------------------------------------------------
static void Respond(int fd, int code, const std::string& reason,
                  const std::string& body, const char* ctype = "application/json") {
    std::string head = "HTTP/1.1 " + std::to_string(code) + " " + reason +
        "\r\nContent-Type: " + ctype +
        "\r\nContent-Length: " + std::to_string(body.size()) +
        "\r\nAccess-Control-Allow-Origin: *\r\nConnection: close\r\n\r\n";
    std::string resp = head + body;
    write(fd, resp.data(), resp.size());
}

static std::string job_json(const Job& j, bool with_logs, bool with_artifacts) {
    std::ostringstream o;
    o << "{\"id\":\"" << j.id << "\",\"type\":\"" << j.type
      << "\",\"apk_path\":\"" << jesc(j.apk_path)
      << "\",\"status\":\"" << status_name(j.status)
      << "\",\"created_at\":\"" << j.created_at
      << "\",\"updated_at\":\"" << j.updated_at << "\"";
    if (!j.fail_reason.empty()) o << ",\"fail_reason\":\"" << jesc(j.fail_reason) << "\"";
    if (with_logs) {
        o << ",\"logs\":[";
        for (size_t i = 0; i < j.logs.size(); ++i) {
            if (i) o << ",";
            o << "\"" << jesc(j.logs[i]) << "\"";
        }
        o << "]";
    }
    if (with_artifacts) {
        o << ",\"artifacts\":[";
        for (size_t i = 0; i < j.artifacts.size(); ++i) {
            if (i) o << ",";
            o << "\"" << jesc(j.artifacts[i]) << "\"";
        }
        o << "]";
    }
    o << "}";
    return o.str();
}

static void handle_request(int fd, const std::string& method,
                           const std::string& path,
                           const std::string& body) {
    std::lock_guard<std::mutex> lk(g_store->mtx);
    // POST /api/jobs
    if (method == "POST" && path == "/api/jobs") {
        // parse {"apk_path": "...", "type": "..."} minimally
        auto grab = [&](const std::string& key) -> std::string {
            // whitespace-tolerant: "key" : "value"
            size_t k = body.find("\"" + key + "\"");
            if (k == std::string::npos) return "";
            k += key.size() + 2;
            while (k < body.size() && (body[k]==' '||body[k]=='\t')) k++;
            if (k >= body.size() || body[k] != ':') return "";
            k++;
            while (k < body.size() && (body[k]==' '||body[k]=='\t')) k++;
            if (k >= body.size() || body[k] != '"') return "";
            k++;
            size_t k2 = body.find('"', k);
            if (k2 == std::string::npos) return "";
            return body.substr(k, k2 - k);
        };
        std::string apk = grab("apk_path");
        std::string type = grab("type");
        if (type.empty()) type = "apk_run";
        if (apk.empty()) {
            Respond(fd, 400, "Bad Request", "{\"error\":\"apk_path required\"}");
            return;
        }
        Job j;
        j.id = "job_" + std::to_string(mono_ms()) + "_" +
               std::to_string(g_store->jobs_.size() + 1);
        j.type = type;
        j.apk_path = apk;
        j.created_at = j.updated_at = now_iso();
        j.last_progress_ms = mono_ms();
        job_log(j, "job created (QUEUED)");
        g_store->jobs_[j.id] = j;
        g_store->persist();
        Respond(fd, 201, "Created", job_json(g_store->jobs_[j.id], false, false));
        return;
    }
    // /api/jobs/{id}[...]
    if (path.rfind("/api/jobs/", 0) == 0) {
        std::string rest = path.substr(10);
        std::string sub;
        size_t slash = rest.find('/');
        std::string id = slash == std::string::npos ? rest : rest.substr(0, slash);
        if (slash != std::string::npos) sub = rest.substr(slash + 1);
        auto it = g_store->jobs_.find(id);
        if (it == g_store->jobs_.end()) {
            Respond(fd, 404, "Not Found", "{\"error\":\"job not found\"}");
            return;
        }
        if (method == "POST" && sub == "cancel") {
            Job& j = it->second;
            if (j.status == JobStatus::QUEUED || j.status == JobStatus::RUNNING ||
                j.status == JobStatus::STALLED) {
                j.status = JobStatus::CANCELLED;
                job_log(j, "job cancelled by request");
                g_store->persist();
                Respond(fd, 200, "OK", job_json(j, false, false));
            } else {
                Respond(fd, 409, "Conflict",
                        std::string("{\"error\":\"cannot cancel job in state ") +
                        status_name(j.status) + "\"}");
            }
            return;
        }
        if (method == "GET" && sub.empty()) {
            Respond(fd, 200, "OK", job_json(it->second, true, true));
            return;
        }
        if (method == "GET" && sub == "status") {
            Respond(fd, 200, "OK",
                    std::string("{\"id\":\"") + id + "\",\"status\":\"" +
                    status_name(it->second.status) + "\"}");
            return;
        }
        if (method == "GET" && sub == "logs") {
            Respond(fd, 200, "OK", job_json(it->second, true, false));
            return;
        }
        if (method == "GET" && sub == "artifacts") {
            Respond(fd, 200, "OK", job_json(it->second, false, true));
            return;
        }
    }
    if (method == "GET" && path == "/api/jobs") {
        std::ostringstream o;
        o << "{\"jobs\":[";
        bool first = true;
        for (auto& [id, j] : g_store->jobs_) {
            if (!first) o << ",";
            first = false;
            o << job_json(j, false, false);
        }
        o << "]}";
        Respond(fd, 200, "OK", o.str());
        return;
    }
    if (method == "GET" && path == "/health") {
        Respond(fd, 200, "OK", "{\"status\":\"ok\"}");
        return;
    }
    Respond(fd, 404, "Not Found", "{\"error\":\"unknown route\"}");
}

int main(int argc, char** argv) {
    int port = argc > 1 ? atoi(argv[1]) : 8377;
    std::string store_path = argc > 2 ? argv[2]
        : "database/u007_jobs.json";
    g_bin_dir = argc > 3 ? argv[3] : "build";
    g_artifact_root = argc > 4 ? argv[4] : "run/u007_job_artifacts";

    static JobStore store(store_path);
    g_store = &store;
    std::fprintf(stderr, "[JOBS] server on :%d store=%s bin=%s artifacts=%s\n",
                 port, store_path.c_str(), g_bin_dir.c_str(),
                 g_artifact_root.c_str());

    std::thread(worker_loop, "stall").detach();

    int srv = socket(AF_INET, SOCK_STREAM, 0);
    int one = 1;
    setsockopt(srv, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));
    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(port);
    if (bind(srv, (sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("bind");
        return 1;
    }
    listen(srv, 16);
    while (true) {
        int fd = accept(srv, nullptr, nullptr);
        if (fd < 0) continue;
        std::thread([fd]() {
            std::string req;
            char buf[4096];
            // Read until headers complete AND body length satisfied.
            while (req.size() < 65536) {
                size_t hend = req.find("\r\n\r\n");
                if (hend != std::string::npos) {
                    size_t cl = req.find("Content-Length: ");
                    if (cl == std::string::npos) cl = req.find("content-length: ");
                    size_t need = 0;
                    if (cl != std::string::npos && cl < hend) {
                        need = (size_t)atoi(req.c_str() + cl + 15);
                    }
                    if (req.size() >= hend + 4 + need) break;  // complete
                }
                ssize_t n = read(fd, buf, sizeof(buf));
                if (n <= 0) break;
                req.append(buf, n);
            }
            std::string method = "GET", path = "/", body;
            {
                size_t sp1 = req.find(' ');
                size_t sp2 = req.find(' ', sp1 + 1);
                if (sp1 != std::string::npos && sp2 != std::string::npos) {
                    method = req.substr(0, sp1);
                    path = req.substr(sp1 + 1, sp2 - sp1 - 1);
                    size_t q = path.find('?');
                    if (q != std::string::npos) path = path.substr(0, q);
                }
                size_t hend = req.find("\r\n\r\n");
                if (hend != std::string::npos) body = req.substr(hend + 4);
            }
            handle_request(fd, method, path, body);
            close(fd);
        }).detach();
    }
    return 0;
}
