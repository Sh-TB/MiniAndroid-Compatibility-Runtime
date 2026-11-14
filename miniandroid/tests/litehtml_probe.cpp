// M-16 litehtml probe (#596 §2.5/§2.7) — the REAL optional prototype runner.
//
// Renders LOCAL and EXTERNAL (http://) HTML/CSS through the MiniLitehtml
// Container into the engine's software FrameBuffer and writes a P6 PPM
// screenshot + a pixel-hash receipt. OFF by default: the target exists only
// when MINIANDROID_USE_LITEHTML=ON.
//
// usage: build/litehtml_probe --html FILE --css URL --width W --height H
//        --out FILE.ppm [--master-css URL]
#include "../src/webview/litehtml_adapter.h"

#ifdef MINIANDROID_USE_LITEHTML

#include <cstring>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>

static unsigned long long fnv1a(const unsigned char* p, size_t n) {
    unsigned long long h = 1469598103934665603ULL;
    for (size_t i = 0; i < n; ++i) {
        h ^= p[i];
        h *= 1099511628211ULL;
    }
    return h;
}

int main(int argc, char** argv) {
    std::string html_path, css_url, master_url, out_path = "probe.ppm";
    int w = 480, h = 800;
    for (int i = 1; i < argc; ++i) {
        std::string a = argv[i];
        auto next = [&]() -> std::string { return (i + 1 < argc) ? argv[++i] : ""; };
        if (a == "--html") html_path = next();
        else if (a == "--css") css_url = next();
        else if (a == "--master-css") master_url = next();
        else if (a == "--width") w = std::atoi(next().c_str());
        else if (a == "--height") h = std::atoi(next().c_str());
        else if (a == "--out") out_path = next();
    }
    if (html_path.empty()) {
        std::cerr << "usage: litehtml_probe --html FILE [--css URL] "
                     "[--master-css URL] [--width W] [--height H] "
                     "[--out FILE.ppm]\n";
        return 2;
    }
    // LOCAL html: file read (the document bytes themselves).
    std::ifstream f(html_path, std::ios::binary);
    if (!f) {
        std::cerr << "[M16-PROBE] FAIL open html: " << html_path << std::endl;
        return 1;
    }
    std::ostringstream ss;
    ss << f.rdbuf();
    std::string html = ss.str();

    // EXTERNAL css: fetched and appended as the user stylesheet — the run
    // records the fetch (status/bytes) in the adapter log.
    std::string user_css;
    if (!css_url.empty()) {
        std::string ct;
        if (miniandroid::litehtml_fetch_url(css_url, user_css, ct)) {
            std::cerr << "[M16-PROBE] external css OK: " << css_url << " ("
                      << user_css.size() << " bytes, type=" << ct << ")"
                      << std::endl;
        } else {
            std::cerr << "[M16-PROBE] external css FETCH FAILED: " << css_url
                      << std::endl;
            return 3; // an external-CSS run must not silently pass
        }
    }
    std::string master_css;
    if (!master_url.empty()) {
        std::string ct;
        if (!miniandroid::litehtml_fetch_url(master_url, master_css, ct)) {
            std::cerr << "[M16-PROBE] master css FETCH FAILED" << std::endl;
            return 3;
        }
    }

    miniandroid::MiniLitehtmlContainer container(w, h);
    bool ok = container.render_document(html, master_css.empty()
                                                   ? litehtml::master_css
                                                   : master_css,
                                        user_css);
    if (!ok) {
        std::cerr << "[M16-PROBE] FAIL: litehtml parse/render error"
                  << std::endl;
        return 4;
    }
    auto& fb = container.framebuffer();
    // Non-blank receipt: count non-white pixels (the visual check law).
    const auto& px = fb.get_pixels();
    int nonwhite = 0;
    for (const auto& c : px)
        if (!(c.r > 250 && c.g > 250 && c.b > 250)) ++nonwhite;
    std::ofstream o(out_path, std::ios::binary);
    o << "P6\n" << fb.get_width() << " " << fb.get_height() << "\n255\n";
    for (const auto& c : px) {
        o.put((char)c.r); o.put((char)c.g); o.put((char)c.b);
    }
    o.close();
    std::cerr << "[M16-PROBE] RESULT html_bytes=" << html.size()
              << " css_bytes=" << user_css.size()
              << " viewport=" << fb.get_width() << "x" << fb.get_height()
              << " nonwhite=" << nonwhite
              << " pxhash=" << std::hex << fnv1a(
                     (const unsigned char*)px.data(), px.size() * 4)
              << std::dec << " out=" << out_path << std::endl;
    return nonwhite > 0 ? 0 : 5;
}

#else // !MINIANDROID_USE_LITEHTML

#include <cstdio>
int main() {
    std::puts(
        "[M16-PROBE] litehtml probe NOT BUILT — MINIANDROID_USE_LITEHTML is "
        "OFF (the default law: the prototype is optional, the portable "
        "runtime never requires it)");
    return 9;
}

#endif
