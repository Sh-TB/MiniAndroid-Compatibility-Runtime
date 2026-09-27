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
};

struct CssRule {
    std::string selector;               // tag / .class / #id
    std::map<std::string, std::string> props;
};

struct ParsedDocument {
    std::unique_ptr<DomNode> root;      // html element
    std::string title;
    std::vector<std::pair<std::string, std::string>> external_scripts; // src order
    std::vector<std::pair<std::string, std::string>> external_styles;
    std::vector<std::string> inline_scripts;   // in document order
    size_t script_nodes_total = 0;
};

class HtmlParser {
public:
    // Parse a full HTML document.
    static ParsedDocument parse(const std::string& html);
    // Parse a fragment (innerHTML law) → returns a detached container node.
    static std::unique_ptr<DomNode> parse_fragment(const std::string& html);
    // Parse a stylesheet body into rules (exposed for the WebView engine).
    static std::vector<CssRule> parse_stylesheet(const std::string& css);
    // Apply the collected <style> rules + inline styles; resolve var().
    static void apply_css(DomNode* node, const std::vector<CssRule>& rules,
                          std::map<std::string, std::string>* custom_props);
    // Serialize children HTML (innerHTML getter approximation).
    static std::string inner_html(const DomNode* n);
    static std::string text_content(const DomNode* n);
};

}} // namespace miniandroid::webview
