// M-16 litehtml adapter (#596 §2.5) — the REAL optional prototype.
//
// Contract (audit/m16-litehtml, MINIANDROID_USE_LITEHTML, OFF by default):
//  - litehtml is the RENDER-ONLY DOM: html_dom.{h,cpp} stays the single
//    JS-facing DOM owner (QuickJS mutations land there; no unsynchronized
//    DOM pair — the synchronization owner is html_dom, and a litehtml
//    render is a fresh parse of the document bytes, never a shadow of
//    mutated engine state).
//  - The adapter paints into the EXISTING software FrameBuffer using the
//    EXISTING TextShaper (FreeType/HarfBuzz) — one font/image/clip stack,
//    no second paint backend, no host browser.
//  - Everything unmodeled is recorded on stderr and stays honest
//    (image decode and gradients are placeholder fills this pass).
#ifndef MINIANDROID_LITEHTML_ADAPTER_H
#define MINIANDROID_LITEHTML_ADAPTER_H

#ifdef MINIANDROID_USE_LITEHTML

#include "../fonts/text_shaper.h"
#include "../renderer/software_renderer.h"
#include "litehtml.h"

#include <string>
#include <vector>

namespace miniandroid {

// Fetch hook for external CSS (http:// and file://) — used by import_css
// and by the probe. Returns false when the URL scheme is unsupported.
bool litehtml_fetch_url(const std::string& url, std::string& out,
                        std::string& content_type);

class MiniLitehtmlContainer : public litehtml::document_container {
  public:
    MiniLitehtmlContainer(int width, int height);

    bool render_document(const std::string& html, const std::string& master_css,
                         const std::string& user_css);
    renderer::FrameBuffer& framebuffer() { return fb_; }

    // document_container (vendored ebb9d32b28cb interface)
    litehtml::uint_ptr create_font(const litehtml::font_description& descr,
                                   const litehtml::document* doc,
                                   litehtml::font_metrics* fm) override;
    void delete_font(litehtml::uint_ptr hFont) override;
    litehtml::pixel_t text_width(const char* text,
                                 litehtml::uint_ptr hFont) override;
    void draw_text(litehtml::uint_ptr hdc, const char* text,
                   litehtml::uint_ptr hFont, litehtml::web_color color,
                   const litehtml::position& pos) override;
    litehtml::pixel_t pt_to_px(float pt) const override;
    litehtml::pixel_t get_default_font_size() const override;
    const char* get_default_font_name() const override;
    void draw_list_marker(litehtml::uint_ptr hdc,
                          const litehtml::list_marker& marker) override;
    void load_image(const char* src, const char* baseurl,
                    bool redraw_on_ready) override;
    void get_image_size(const char* src, const char* baseurl,
                        litehtml::size& sz) override;
    void draw_image(litehtml::uint_ptr hdc, const litehtml::background_layer& layer,
                    const std::string& url, const std::string& base_url) override;
    void draw_solid_fill(litehtml::uint_ptr hdc,
                         const litehtml::background_layer& layer,
                         const litehtml::web_color& color) override;
    void draw_linear_gradient(litehtml::uint_ptr hdc,
                              const litehtml::background_layer& layer,
                              const litehtml::background_layer::linear_gradient& g) override;
    void draw_radial_gradient(litehtml::uint_ptr hdc,
                              const litehtml::background_layer& layer,
                              const litehtml::background_layer::radial_gradient& g) override;
    void draw_conic_gradient(litehtml::uint_ptr hdc,
                             const litehtml::background_layer& layer,
                             const litehtml::background_layer::conic_gradient& g) override;
    void draw_borders(litehtml::uint_ptr hdc, const litehtml::borders& borders,
                      const litehtml::position& draw_pos, bool root) override;
    void set_caption(const char* caption) override;
    void set_base_url(const char* base_url) override;
    void link(const std::shared_ptr<litehtml::document>& doc,
              const litehtml::element::ptr& el) override;
    void on_anchor_click(const char* url,
                         const litehtml::element::ptr& el) override;
    void on_mouse_event(const litehtml::element::ptr& el,
                        litehtml::mouse_event event) override;
    void set_cursor(const char* cursor) override;
    void transform_text(std::string& text, litehtml::text_transform tt) override;
    void import_css(std::string& text, const std::string& url,
                    std::string& baseurl) override;
    void set_clip(const litehtml::position& pos,
                  const litehtml::border_radiuses& bdr_radius) override;
    void del_clip() override;
    void get_viewport(litehtml::position& viewport) const override;
    litehtml::element::ptr create_element(
        const char* tag_name, const litehtml::string_map& attributes,
        const std::shared_ptr<litehtml::document>& doc) override;
    void get_media_features(litehtml::media_features& media) const override;
    void get_language(std::string& language, std::string& culture) const override;
    void split_text(const char* text,
                    const std::function<void(const char*)>& on_word,
                    const std::function<void(const char*)>& on_space) override;

  private:
    struct FontSpec { int size_px; bool bold; };
    bool clip_and_push(int x, int y, int w, int h);
    void pop_clip();
    void fill_rect(int x, int y, int w, int h, const litehtml::web_color& c);

    int width_, height_;
    renderer::FrameBuffer fb_;
    std::vector<FontSpec> fonts_;
    litehtml::position clip_;
    bool has_clip_ = false;
    std::string base_url_;
};

} // namespace miniandroid

#endif // MINIANDROID_USE_LITEHTML
#endif // MINIANDROID_LITEHTML_ADAPTER_H
