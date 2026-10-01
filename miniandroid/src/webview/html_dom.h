// S109 WEBVIEW-ENGINE — DOM tree + HTML parser + minimal CSS engine.
//
// SEMANTIC LAW (WHATWG HTML — parsing; CSS 2.1 + custom properties):
// * Inline <script> executes during parse, in document order, when the
//   closing </script> is seen (parser blocking law). <script src=...>
//   fetches then executes synchronously when present in the APK assets.
// * <style> content applies as author CSS. Selector support: tag, .class,
//   #id, and comma lists — the subset actually exercised by the WebView
//   corpus. CSS custom properties (--x) on :root/html/body resolve into
//   var(--x) references.
// * style="" attribute wins over stylesheet rules (inline specificity).
// * The DOM is live: JS mutations (appendChild/remove/style.display=...)
//   are visible to the compositor on the next render pass.
#pragma once
#include "canvas2d.h"
#include <map>
#include <memory>
#include <set>
#include <string>
#include <vector>

namespace miniandroid { namespace webview {

struct DomNode {
    std::string tag;                    // lowercase; "#text" for text nodes
    std::map<std::string, std::string> attrs;
    std::vector<std::unique_ptr<DomNode>> children;
    DomNode* parent = nullptr;
    std::string text;                   // #text payload
    std::map<std::string, std::string> style;   // computed (inline + css, var-resolved)
    // S114: keys set by the style ATTRIBUTE or by JS style writes — these
    // OUTRANK every stylesheet rule (CSS specificity: inline > selector);
    // rule application must never overwrite them (the Block'Buster bricks:
    // JS margin-left vs the universal `*{margin:0}` rule)
    std::set<std::string> inline_keys;
    // layout (compositor)
    int x = 0, y = 0, w = 0, h = 0;
    bool visible = true;
    uint32_t bg = 0, fg = 0;
    bool has_bg = false, has_fg = false;
    float font_size = 14.f;
    bool bold = false;
    int z_index = 0;
    bool positioned = false;            // fixed/absolute
    bool display_none = false;
    int text_align = 0;                 // 0 left, 1 center, 2 right

    // ── S113 CSS BOX MODEL + PAINT (full-GUI render law) ────────────────
    int pad_t = 0, pad_r = 0, pad_b = 0, pad_l = 0;
    int mar_t = 0, mar_r = 0, mar_b = 0, mar_l = 0;
    bool mar_lr_auto = false;           // margin-left/right:auto → horizontal center
    int border_w = 0; uint32_t border_col = 0; bool has_border = false;
    int radius = 0;                     // border-radius (uniform)
    bool flex = false;                  // display:flex
    int align_items = 0;                // 0 start/stretch, 1 center
    int justify_content = 0;            // 0 start, 1 center
    bool has_w = false, has_h = false;  // explicit px sizes
    float w_pct = -1, h_pct = -1;       // %-of-containing-block
    int max_w = -1;                     // max-width px
    std::string bg_image;               // unresolved url(...) from background-image/background
    bool bg_contain = false;            // background-size: contain
    bool bg_mirror = false;             // transform: scaleX(-1)
    bool grad = false;                  // linear-gradient background
    int grad_dir = 0;                   // S114: 0 down, 1 up (0deg), 2 right, 3 left
    uint32_t grad_from = 0, grad_to = 0;
    bool grad_diag = false;             // "to bottom right" diagonal law
    int bg_alpha = 255;                 // alpha of background-color (rgba law)
    std::string pseudo_before, pseudo_after;   // ::before/::after content strings
    bool text_shadow = false; uint32_t text_shadow_col = 0;
    bool box_shadow = false;            // non-inset box-shadow present
    int font_face = -1;                 // @font-face registered face index (-1 = system)
    bool inline_el = false;             // display:inline — text merges into parent flow
    // S133 ATOMIC INLINE-BOX law (CSS 2.1 §9.2.2): inline-block is an
    // atomic inline-level box — its content does NOT merge into the
    // parent's text run; the box itself flows horizontally with wrapping.
    bool inline_block = false;          // display:inline-block
    // inherited chains (filled by the render-time style walk, parent→child)
    uint32_t eff_fg = 0; bool eff_fg_valid = false;
    int eff_face = -1;
    float eff_font_size = 28.f;
    bool eff_bold = false;
    int eff_align = 0;
    // ── S114 GENERIC CSS LAYOUT CORE ────────────────────────────────────
    // One positional model for every element (WHATWG/CSS2.1 §9 + §10):
    // static flow, relative offsets, absolute (containing block = nearest
    // positioned ancestor, else the initial containing block), fixed (ICB).
    int pos_mode = 0;                   // 0 static, 1 relative, 2 absolute, 3 fixed
    bool z_given = false;               // z-index explicitly set (not "auto")
    std::string off_l, off_t, off_r, off_b;   // raw offset strings (layout-time resolve)
    std::string w_raw, h_raw;           // width/height strings containing % (deferred to CB)
    bool vis_hidden_own = false;        // visibility:hidden (own prop)
    bool eff_vis_hidden = false;        // inherited visibility chain
    bool border_box = false;            // box-sizing: border-box
    bool flex_row = false;              // flex-direction: row
    bool overflow_hidden = false;       // clip children to the padding box
    float line_h_num = -1.f;            // line-height unitless factor (-1 unset)
    int line_h_px = 0;                  // line-height <length> (0 = legacy 1.6 law)
    bool grad_text = false;             // -webkit-background-clip:text → gradient glyphs
    int sh_ox = 0, sh_oy = 0, sh_blur = 0, sh_spread = 0;   // box-shadow parts
    uint32_t sh_col = 0; bool sh_col_valid = false;
    float bg_size_pct = -1.f;           // background-size: N% (single-value width law)
    int static_x = 0, static_y = 0;     // flow position where the box would be placed
    bool static_pos_recorded = false;   // S114: distinguishes a real (0,0) static
                                        // slot from "never in flow" (inline subtrees)
    // layout result for hit-testing/paint
    bool laid_out = false;

    // canvas backing (tag == "canvas")
    bool is_canvas = false;
    std::unique_ptr<Canvas2D> canvas;

    DomNode* get_attr_child(const std::string& id) {
        for (auto& c : children)
            if (c->attrs.count("id") && c->attrs["id"] == id) return c.get();
        return nullptr;
    }
    size_t index_in_parent() const {
        if (!parent) return 0;
        for (size_t i = 0; i < parent->children.size(); ++i)
            if (parent->children[i].get() == this) return i;
        return 0;
    }
    // S114: nearest previous sibling that is an element (not #text) —
    // the CSS adjacent-sibling combinator ('+') ground truth.
    DomNode* previous_element_sibling() const {
        if (!parent) return nullptr;
        DomNode* prev = nullptr;
        for (auto& c : parent->children) {
            if (c.get() == this) return prev;
            if (c->tag != "#text") prev = c.get();
        }
        return nullptr;
    }
};

struct CssRule {
    std::string selector;               // tag / .class / #id / compound+descendant / @font-face
    std::map<std::string, std::string> props;
    // S113 conditional/structural rules:
    int media_max_w = -1, media_min_w = -1;   // @media constraints (-1 = unconditional)
    bool pseudo_before = false, pseudo_after = false;  // selector targets ::before/::after
};

struct ParsedDocument {
    std::unique_ptr<DomNode> root;      // html element
    std::string title;
    std::vector<std::pair<std::string, std::string>> external_scripts; // (src, type:""|"module")
    std::vector<std::pair<std::string, std::string>> external_styles;
    // S133 ES-MODULE law: <script type=module> inline code records
    // is_module — module scripts parse with module goals (import/export
    // allowed) and execute after their dependencies (WHATWG §4.12.21).
    std::vector<std::pair<std::string, bool>> inline_scripts; // (code, is_module)
    size_t script_nodes_total = 0;
};

class HtmlParser {
public:
    // Parse a full HTML document.
    static ParsedDocument parse(const std::string& html);
    // Parse a fragment (innerHTML law) → returns a detached container node.
    static std::unique_ptr<DomNode> parse_fragment(const std::string& html);
    // Parse a stylesheet body into rules (exposed for the WebView engine).
    // S113: @media constraints recorded on rules; @font-face kept; pseudo-
    // element rules (::before/::after) tagged — evaluated by the engine.
    static std::vector<CssRule> parse_stylesheet(const std::string& css);
    static std::vector<CssRule> parse_stylesheet_impl(const std::string& css,
                                                      int media_min_w, int media_max_w);
    // Apply the collected <style> rules + inline styles; resolve var().
    // ignore_media=true skips rules with @media constraints (render-time law).
    static void apply_css(DomNode* node, const std::vector<CssRule>& rules,
                          std::map<std::string, std::string>* custom_props);
    static void apply_css_impl(DomNode* node, const std::vector<CssRule>& rules,
                               std::map<std::string, std::string>* custom_props,
                               bool ignore_media);
    // Serialize children HTML (innerHTML getter approximation).
    static std::string inner_html(const DomNode* n);
    static std::string text_content(const DomNode* n);
    // S113: selector matcher exposed for the engine's pseudo-element pass.
    static bool matches_selector(const std::string& sel, const DomNode* n);
    // S114: var() substitution exposed for the engine's pseudo-box styling.
    static std::string resolve_var_string(const std::string& val,
                                          const std::map<std::string, std::string>& custom);
};

}} // namespace miniandroid::webview
