// M-16 litehtml adapter implementation (#596 §2.5) — see the header contract.
#include "litehtml_adapter.h"

#ifdef MINIANDROID_USE_LITEHTML

#include <sys/socket.h>
#include <iostream>
#include <netdb.h>
#include <unistd.h>
#include <algorithm>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <fstream>
#include <sstream>

namespace miniandroid {

// --- the fetch hook (probe-local; engine http_client reuse lands with the
// webview_engine wiring pass — this hook keeps the adapter independent) ---
bool litehtml_fetch_url(const std::string& url, std::string& out,
                        std::string& content_type) {
    content_type.clear();
    if (url.rfind("file://", 0) == 0 || (!url.empty() && url[0] == '/')) {
        std::string path =
            url.rfind("file://", 0) == 0 ? url.substr(7) : url;
        std::ifstream f(path, std::ios::binary);
        if (!f) return false;
        std::ostringstream ss;
        ss << f.rdbuf();
        out = ss.str();
        content_type = "file";
        return true;
    }
    if (url.rfind("http://", 0) != 0) return false; // https needs the
        // engine http_client (TLS) — recorded PENDING, never guessed.
    // Minimal HTTP/1.0 GET: parse host[:port][/path], one request,
    // 200 + headers parsed for Content-Type, body appended.
    size_t hp = url.find('/', 7);
    std::string hostport = hp == std::string::npos ? url.substr(7) : url.substr(7, hp - 7);
    std::string path = hp == std::string::npos ? "/" : url.substr(hp);
    size_t colon = hostport.find(':');
    std::string host = colon == std::string::npos ? hostport : hostport.substr(0, colon);
    int port = colon == std::string::npos ? 80 : std::atoi(hostport.c_str() + colon + 1);
    int fd = ::socket(AF_INET, SOCK_STREAM, 0);
    if (fd < 0) return false;
    hostent* he = gethostbyname(host.c_str());
    if (!he) { ::close(fd); return false; }
    sockaddr_in addr{};
    addr.sin_family = AF_INET;
    addr.sin_port = htons((uint16_t)port);
    std::memcpy(&addr.sin_addr.s_addr, he->h_addr_list[0], 4);
    if (::connect(fd, (sockaddr*)&addr, sizeof(addr)) != 0) {
        ::close(fd);
        return false;
    }
    std::string req = "GET " + path +
        " HTTP/1.0\r\nHost: " + hostport +
        "\r\nUser-Agent: MiniAndroid-LitehtmlProbe\r\nConnection: close\r\n\r\n";
    ::send(fd, req.data(), req.size(), 0);
    char buf[8192];
    std::string raw;
    ssize_t n;
    while ((n = ::recv(fd, buf, sizeof(buf), 0)) > 0) raw.append(buf, n);
    ::close(fd);
    size_t hdr_end = raw.find("\r\n\r\n");
    if (hdr_end == std::string::npos) return false;
    std::string headers = raw.substr(0, hdr_end);
    if (headers.rfind("HTTP/", 0) == 0) {
        // status line: HTTP/1.x CODE
        size_t sp = headers.find(' ');
        if (sp != std::string::npos)
            std::cerr << "[M16-PROBE] css fetch status="
                      << headers.substr(sp + 1, 3) << " bytes="
                      << (raw.size() - hdr_end - 4) << std::endl;
        size_t ct = headers.find("Content-Type:");
        if (ct != std::string::npos) {
            size_t e = headers.find("\r\n", ct);
            content_type = headers.substr(ct + 13,
                (e == std::string::npos ? std::string::npos : e - ct - 13));
        }
    }
    out = raw.substr(hdr_end + 4);
    return true;
}

MiniLitehtmlContainer::MiniLitehtmlContainer(int width, int height)
    : width_(width), height_(height), fb_(width, height) {
    clip_.x = 0; clip_.y = 0;
    clip_.width = width_; clip_.height = height_;
}

bool MiniLitehtmlContainer::clip_and_push(int x, int y, int w, int h) {
    litehtml::position next(x, y, w, h);
    if (has_clip_) {
        int l = std::max(next.x, clip_.x);
        int t = std::max(next.y, clip_.y);
        int r = std::min(next.x + next.width, clip_.x + clip_.width);
        int b = std::min(next.y + next.height, clip_.y + clip_.height);
        if (r <= l || b <= t) return false;
        next.x = l; next.y = t;
        next.width = r - l; next.height = b - t;
    }
    clip_ = next;
    has_clip_ = true;
    return true;
}
void MiniLitehtmlContainer::pop_clip() { has_clip_ = false; }

void MiniLitehtmlContainer::fill_rect(int x, int y, int w, int h,
                                      const litehtml::web_color& c) {
    int cx = has_clip_ ? (int)clip_.x : 0;
    int cy = has_clip_ ? (int)clip_.y : 0;
    int cw = has_clip_ ? (int)clip_.width : width_;
    int ch = has_clip_ ? (int)clip_.height : height_;
    int l = std::max(x, cx);
    int t = std::max(y, cy);
    int r = std::min(x + w, cx + cw);
    int b = std::min(y + h, cy + ch);
    if (r <= l || b <= t) return;
    for (int yy = t; yy < b; ++yy)
        for (int xx = l; xx < r; ++xx)
            fb_.set_pixel(xx, yy, renderer::RGBA(c.red, c.green, c.blue, c.alpha));
}

// --- fonts: engine TextShaper (FreeType/HarfBuzz) — REAL shaping ---
litehtml::uint_ptr MiniLitehtmlContainer::create_font(
    const litehtml::font_description& descr, const litehtml::document*,
    litehtml::font_metrics* fm) {
    FontSpec spec{std::max(6, (int)descr.size),
                  descr.weight >= 600};
    fonts_.push_back(spec);
    int idx = (int)fonts_.size();
    if (fm) {
        float asc = 0, desc = 0, lh = 0;
        fonts::TextShaper::instance().metrics((float)spec.size_px, spec.bold,
                                       fonts::FACE_SYSTEM, &asc, &desc,
                                       &lh);
        fm->ascent = asc;
        fm->descent = desc;
        fm->height = lh;
        fm->x_height = asc * 0.5f;
    }
    std::cerr << "[M16-PROBE] create_font size=" << spec.size_px
              << " bold=" << spec.bold << std::endl;
    return (litehtml::uint_ptr)idx;
}
void MiniLitehtmlContainer::delete_font(litehtml::uint_ptr) {}

litehtml::pixel_t MiniLitehtmlContainer::text_width(const char* text,
                                                    litehtml::uint_ptr hFont) {
    if (!text || !*text || hFont == 0 || hFont > fonts_.size()) return 0;
    const FontSpec& f = fonts_[hFont - 1];
    const auto& sh = fonts::TextShaper::instance().shape(text, (float)f.size_px,
                                                  f.bold);
    return (litehtml::pixel_t)sh.width;
}

void MiniLitehtmlContainer::draw_text(litehtml::uint_ptr, const char* text,
                                      litehtml::uint_ptr hFont,
                                      litehtml::web_color color,
                                      const litehtml::position& pos) {
    if (!text || !*text || hFont == 0 || hFont > fonts_.size()) return;
    const FontSpec& f = fonts_[hFont - 1];
    const auto& sh = fonts::TextShaper::instance().shape(text, (float)f.size_px,
                                                  f.bold);
    // litehtml pos = the text box; baseline = box top + ascent.
    fonts::TextShaper::instance().draw(fb_, text, (float)pos.x,
        (float)pos.y + sh.ascent, (float)f.size_px,
        renderer::RGBA(color.red, color.green, color.blue, color.alpha),
        f.bold);
}

litehtml::pixel_t MiniLitehtmlContainer::pt_to_px(float pt) const {
    return (litehtml::pixel_t)(pt * 96.0f / 72.0f); // 96dpi device law
}
litehtml::pixel_t MiniLitehtmlContainer::get_default_font_size() const {
    return 16;
}
const char* MiniLitehtmlContainer::get_default_font_name() const {
    return "sans-serif";
}

// --- backgrounds / borders / markers ---
void MiniLitehtmlContainer::draw_solid_fill(
    litehtml::uint_ptr, const litehtml::background_layer& layer,
    const litehtml::web_color& color) {
    fill_rect(layer.border_box.x, layer.border_box.y, layer.border_box.width,
              layer.border_box.height, color);
}
void MiniLitehtmlContainer::draw_linear_gradient(
    litehtml::uint_ptr, const litehtml::background_layer& layer,
    const litehtml::background_layer::linear_gradient&) {
    // Gradient rasterization = PENDING (#596 §2.5); honest placeholder fill.
    fill_rect(layer.border_box.x, layer.border_box.y, layer.border_box.width,
              layer.border_box.height, litehtml::web_color(64, 96, 160, 255));
    std::cerr << "[M16-PROBE] linear-gradient placeholder fill" << std::endl;
}
void MiniLitehtmlContainer::draw_radial_gradient(
    litehtml::uint_ptr hdc, const litehtml::background_layer& layer,
    const litehtml::background_layer::radial_gradient&) {
    draw_linear_gradient(hdc, layer, {});
}
void MiniLitehtmlContainer::draw_conic_gradient(
    litehtml::uint_ptr hdc, const litehtml::background_layer& layer,
    const litehtml::background_layer::conic_gradient&) {
    draw_linear_gradient(hdc, layer, {});
}
void MiniLitehtmlContainer::draw_image(
    litehtml::uint_ptr, const litehtml::background_layer& layer,
    const std::string& url, const std::string&) {
    // Image decode through the engine stack = PENDING; the box outline is
    // the recorded placeholder (never a fabricated image).
    litehtml::web_color c(220, 220, 220, 255);
    fill_rect(layer.border_box.x, layer.border_box.y, layer.border_box.width,
              layer.border_box.height, c);
    std::cerr << "[M16-PROBE] image placeholder box: " << url << std::endl;
}
void MiniLitehtmlContainer::draw_borders(
    litehtml::uint_ptr, const litehtml::borders& b,
    const litehtml::position& draw_pos, bool) {
    struct Side { const litehtml::border* b; int x, y, w, h; };
    Side sides[4] = {
        {&b.left, draw_pos.x, draw_pos.y, (int)b.left.width, draw_pos.height},
        {&b.top, draw_pos.x, draw_pos.y, draw_pos.width, (int)b.top.width},
        {&b.right, draw_pos.x + draw_pos.width - (int)b.right.width,
         draw_pos.y, (int)b.right.width, draw_pos.height},
        {&b.bottom, draw_pos.x,
         draw_pos.y + draw_pos.height - (int)b.bottom.width,
         draw_pos.width, (int)b.bottom.width}};
    for (auto& s : sides) {
        if (s.b->style == litehtml::border_style_none || s.w <= 0 || s.h <= 0)
            continue;
        fill_rect(s.x, s.y, s.w, s.h, s.b->color);
    }
}
void MiniLitehtmlContainer::draw_list_marker(
    litehtml::uint_ptr, const litehtml::list_marker& marker) {
    int m = std::max(2, (int)marker.pos.height / 3);
    fill_rect(marker.pos.x, marker.pos.y, m, m, marker.color);
}

// --- images: decode PENDING this pass ---
void MiniLitehtmlContainer::load_image(const char* src, const char*, bool) {
    std::cerr << "[M16-PROBE] load_image deferred: " << (src ? src : "?")
              << std::endl;
}
void MiniLitehtmlContainer::get_image_size(const char*, const char*,
                                           litehtml::size& sz) {
    sz.width = sz.height = 0; // no fabricated dimensions
}

// --- chrome / navigation / events ---
void MiniLitehtmlContainer::set_caption(const char*) {}
void MiniLitehtmlContainer::set_base_url(const char* base_url) {
    base_url_ = base_url ? base_url : "";
}
void MiniLitehtmlContainer::link(const std::shared_ptr<litehtml::document>&,
                                 const litehtml::element::ptr&) {}
void MiniLitehtmlContainer::on_anchor_click(const char*, const litehtml::element::ptr&) {}
void MiniLitehtmlContainer::on_mouse_event(const litehtml::element::ptr&,
                                           litehtml::mouse_event) {}
void MiniLitehtmlContainer::set_cursor(const char*) {}

void MiniLitehtmlContainer::transform_text(std::string& text,
                                           litehtml::text_transform tt) {
    if (tt == litehtml::text_transform_uppercase) {
        std::transform(text.begin(), text.end(), text.begin(), ::toupper);
    } else if (tt == litehtml::text_transform_lowercase) {
        std::transform(text.begin(), text.end(), text.begin(), ::tolower);
    } else if (tt == litehtml::text_transform_capitalize) {
        bool word_start = true;
        for (auto& ch : text) {
            if (::isspace((unsigned char)ch)) word_start = true;
            else if (word_start) { ch = ::toupper((unsigned char)ch); word_start = false; }
        }
    }
}

// --- EXTERNAL CSS: the @import hook (http:// + file:// through the hook) ---
void MiniLitehtmlContainer::import_css(std::string& text,
                                       const std::string& url,
                                       std::string& baseurl) {
    std::string body, ct;
    std::string full = url;
    std::cerr << "[M16-PROBE] import_css url='" << url << "' baseurl='"
              << baseurl << "' doc_base='" << base_url_ << "'" << std::endl;
    auto is_abs = [](const std::string& u) {
        return u.rfind("http://", 0) == 0 || u.rfind("file://", 0) == 0 ||
               (!u.empty() && u[0] == '/');
    };
    if (!is_abs(full)) {
        // CSS spec: a relative @import resolves against the IMPORTING
        // STYLESHEET's URL (the baseurl litehtml passes), NOT the document
        // base. Fall back to the document base only when the importer's
        // base is unknown.
        const std::string& base = baseurl.empty() ? base_url_ : baseurl;
        if (base.rfind("http", 0) == 0) {
            size_t sp = base.rfind('/');
            if (sp != std::string::npos && sp >= 7)
                full = base.substr(0, sp + 1) + full;
        }
    }
    if (litehtml_fetch_url(full, body, ct)) {
        text = body;
        std::cerr << "[M16-PROBE] import_css fetched " << full << " ("
                  << body.size() << " bytes)" << std::endl;
    } else {
        std::cerr << "[M16-PROBE] import_css FETCH FAILED: " << full
                  << std::endl;
    }
}

void MiniLitehtmlContainer::set_clip(
    const litehtml::position& pos, const litehtml::border_radiuses&) {
    clip_and_push(pos.x, pos.y, pos.width, pos.height);
}
void MiniLitehtmlContainer::del_clip() { pop_clip(); }

void MiniLitehtmlContainer::get_viewport(litehtml::position& viewport) const {
    viewport.x = 0; viewport.y = 0;
    viewport.width = width_; viewport.height = height_;
}

litehtml::element::ptr MiniLitehtmlContainer::create_element(
    const char*, const litehtml::string_map&,
    const std::shared_ptr<litehtml::document>&) {
    return nullptr; // no custom element tags
}

void MiniLitehtmlContainer::get_media_features(
    litehtml::media_features& media) const {
    media.type = litehtml::media_type_screen;
    media.width = width_; media.height = height_;
    media.device_width = width_; media.device_height = height_;
    media.resolution = 96; media.color = 8; media.color_index = 24;
    media.monochrome = 0;
}
void MiniLitehtmlContainer::get_language(std::string& language,
                                         std::string& culture) const {
    language = "en"; culture = "en-US";
}
void MiniLitehtmlContainer::split_text(
    const char* text, const std::function<void(const char*)>& on_word,
    const std::function<void(const char*)>& on_space) {
    const char* p = text;
    while (*p) {
        if (::isspace((unsigned char)*p)) {
            const char* s = p;
            while (*p && ::isspace((unsigned char)*p)) ++p;
            on_space(std::string(s, p - s).c_str());
        } else {
            const char* w = p;
            while (*p && !::isspace((unsigned char)*p)) ++p;
            on_word(std::string(w, p - w).c_str());
        }
    }
}

bool MiniLitehtmlContainer::render_document(const std::string& html,
                                            const std::string& master_css,
                                            const std::string& user_css) {
    auto doc = litehtml::document::createFromString(html, this,
                                                    master_css, user_css);
    if (!doc) return false;
    doc->render(width_);
    litehtml::position clip(0, 0, width_, height_);
    doc->draw((litehtml::uint_ptr)this, 0, 0, &clip);
    return true;
}

} // namespace miniandroid

#endif // MINIANDROID_USE_LITEHTML
