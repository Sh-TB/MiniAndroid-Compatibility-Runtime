// S109 WEBVIEW-ENGINE — HTML parser + minimal CSS. See html_dom.h for laws.
#include "html_dom.h"
#include <algorithm>
#include <cctype>
#include <sstream>

namespace miniandroid { namespace webview {

static std::string lower(std::string s) {
    for (auto& c : s) c = char(::tolower((unsigned char)c));
    return s;
}
static std::string trim(const std::string& s) {
    size_t a = s.find_first_not_of(" \t\r\n");
    if (a == std::string::npos) return "";
    size_t b = s.find_last_not_of(" \t\r\n");
    return s.substr(a, b - a + 1);
}
static std::string decode_entities(const std::string& s) {
    std::string out; out.reserve(s.size());
    for (size_t i = 0; i < s.size();) {
        if (s[i] == '&') {
            size_t sc = s.find(';', i);
            if (sc != std::string::npos && sc - i <= 10) {
                std::string ent = s.substr(i + 1, sc - i - 1);
                if (ent == "amp") out += '&';
                else if (ent == "lt") out += '<';
                else if (ent == "gt") out += '>';
                else if (ent == "quot") out += '"';
                else if (ent == "apos") out += '\'';
                else if (ent == "nbsp") out += ' ';
                else if (ent == "hellip") out += 0xE2, out += 0x80, out += 0xA6;
                else if (!ent.empty() && ent[0] == '#') {
                    int cp = 0;
                    if (ent.size() > 2 && (ent[1] == 'x' || ent[1] == 'X'))
                        cp = int(strtol(ent.c_str() + 2, nullptr, 16));
                    else cp = atoi(ent.c_str() + 1);
                    if (cp < 0x80) out += char(cp);
                    else if (cp < 0x800) {
                        out += char(0xC0 | (cp >> 6)); out += char(0x80 | (cp & 63));
                    } else {
                        out += char(0xE0 | (cp >> 12)); out += char(0x80 | ((cp >> 6) & 63));
                        out += char(0x80 | (cp & 63));
                    }
                } else out += '&' + ent + ';';
                i = sc + 1; continue;
            }
        }
        out += s[i++];
    }
    return out;
}

// tokenizer over tags
namespace {
struct Cursor { const std::string& s; size_t i = 0; };
}

static void append_text(DomNode* parent, const std::string& raw) {
    std::string t = decode_entities(raw);
    if (t.empty()) return;
    // merge with previous text node (DOM text coalescing law)
    if (!parent->children.empty() && parent->children.back()->tag == "#text") {
        parent->children.back()->text += t;
        return;
    }
    auto n = std::make_unique<DomNode>();
    n->tag = "#text"; n->text = t; n->parent = parent;
    parent->children.push_back(std::move(n));
}

static std::unique_ptr<DomNode> make_element(const std::string& tag) {
    auto n = std::make_unique<DomNode>();
    n->tag = lower(tag);
    if (n->tag == "canvas") n->is_canvas = true;
    return n;
}

static void collect_scripts(DomNode* n, ParsedDocument& doc,
                            const std::string& html,
                            std::vector<DomNode*>* script_order) {
    // walk; for <script>: inline content → inline_scripts (in order),
    // src= → external_scripts
    (void)html; (void)script_order;
    if (n->tag == "script") {
        std::string src = n->attrs.count("src") ? n->attrs["src"] : "";
        if (!src.empty()) doc.external_scripts.push_back({src, ""});
        else if (!n->text.empty()) doc.inline_scripts.push_back(n->text);
        doc.script_nodes_total++;
    }
    for (auto& c : n->children) collect_scripts(c.get(), doc, html, script_order);
}

ParsedDocument HtmlParser::parse(const std::string& html) {
    ParsedDocument doc;
    auto html_el = make_element("html");
    html_el->parent = nullptr;
    DomNode* cur = html_el.get();
    std::vector<DomNode*> open_stack{html_el.get()};
    size_t i = 0;
    while (i < html.size()) {
        size_t lt = html.find('<', i);
        if (lt == std::string::npos) {
            append_text(cur, html.substr(i));
            break;
        }
        if (lt > i) append_text(cur, html.substr(i, lt - i));
        // comment / doctype
        if (html.compare(lt, 4, "<!--") == 0) {
            size_t end = html.find("-->", lt);
            i = end == std::string::npos ? html.size() : end + 3;
            continue;
        }
        if (html.compare(lt, 9, "<!doctype") == 0 || html.compare(lt, 2, "<!") == 0) {
            size_t end = html.find('>', lt);
            i = end == std::string::npos ? html.size() : end + 1;
            continue;
        }
        bool closing = lt + 1 < html.size() && html[lt + 1] == '/';
        size_t tag_end = lt + 1;
        while (tag_end < html.size() && html[tag_end] != '>' &&
               !isspace((unsigned char)html[tag_end])) ++tag_end;
        std::string tag = lower(html.substr(lt + (closing ? 2 : 1), tag_end - lt - (closing ? 2 : 1)));
        // find end of the open tag ('>' honoring quoted attrs)
        size_t gt = lt + 1;
        char q = 0;
        while (gt < html.size()) {
            char c = html[gt];
            if (q) { if (c == q) q = 0; }
            else if (c == '"' || c == '\'') q = c;
            else if (c == '>') break;
            ++gt;
        }
        if (gt >= html.size()) break;
        std::string tag_body = html.substr(lt + 1, gt - lt - 1);
        i = gt + 1;
        if (closing) {
            // pop to the nearest matching open tag (HTML error recovery law)
            for (int s = int(open_stack.size()) - 1; s >= 1; --s) {
                if (open_stack[s]->tag == tag) {
                    open_stack.resize(s);
                    cur = open_stack.back();
                    break;
                }
            }
            continue;
        }
        auto el = make_element(tag);
        // attributes
        {
            size_t p = 1;
            while (p < tag_body.size() && !isspace((unsigned char)tag_body[p])) ++p;
            while (p < tag_body.size()) {
                while (p < tag_body.size() && isspace((unsigned char)tag_body[p])) ++p;
                size_t a0 = p;
                while (p < tag_body.size() && tag_body[p] != '=' &&
                       !isspace((unsigned char)tag_body[p])) ++p;
                std::string name = lower(tag_body.substr(a0, p - a0));
                std::string val;
                if (p < tag_body.size() && tag_body[p] == '=') {
                    ++p;
                    if (p < tag_body.size() && (tag_body[p] == '"' || tag_body[p] == '\'')) {
                        char q = tag_body[p++];
                        size_t v0 = p;
                        while (p < tag_body.size() && tag_body[p] != q) ++p;
                        val = tag_body.substr(v0, p - v0);
                        ++p;
                    } else {
                        size_t v0 = p;
                        while (p < tag_body.size() && !isspace((unsigned char)tag_body[p])) ++p;
                        val = tag_body.substr(v0, p - v0);
                    }
                }
                if (!name.empty()) {
                    if (name == "id" && tag == "canvas") {}
                    el->attrs[name] = decode_entities(val);
                }
            }
        }
        // raw text elements: script/style — content up to the matching close tag
        bool raw = (tag == "script" || tag == "style");
        el->parent = cur;
        DomNode* elp = el.get();
        cur->children.push_back(std::move(el));
        if (raw) {
            std::string close = "</" + tag;
            size_t cs = i;
            // case-insensitive search
            std::string lower_html; lower_html.reserve(html.size() - i);
            for (size_t k = i; k < html.size(); ++k)
                lower_html += char(::tolower((unsigned char)html[k]));
            size_t pos = lower_html.find(close);
            if (pos == std::string::npos) {
                elp->text = html.substr(i);
                i = html.size();
            } else {
                elp->text = html.substr(i, pos);
                size_t close_gt = html.find('>', i + pos);
                i = close_gt == std::string::npos ? html.size() : close_gt + 1;
            }
            if (tag == "title") doc.title = trim(elp->text);
        } else if (tag == "meta") {
            if (tag_body.find("charset") != std::string::npos) {}
        }
        bool self_closing = tag_body.back() == '/' ||
                            tag == "meta" || tag == "link" || tag == "br" ||
                            tag == "img" || tag == "input" || tag == "hr";
        if (!raw && !self_closing) {
            open_stack.push_back(elp);
            cur = elp;
        }
    }
    // collect scripts in document order
    for (auto& c : html_el->children) collect_scripts(c.get(), doc, html, nullptr);
    doc.root = std::move(html_el);
    return doc;
}

std::unique_ptr<DomNode> HtmlParser::parse_fragment(const std::string& html) {
    auto doc = parse(html);
    // wrap: return the container holding html's children
    auto box = make_element("#fragment");
    for (auto& c : doc.root->children) {
        c->parent = box.get();
        box->children.push_back(std::move(c));
    }
    return box;
}

// ── CSS ─────────────────────────────────────────────────────────────────
static void parse_prop_list(const std::string& body, std::map<std::string, std::string>& out) {
    size_t p = 0;
    while (p < body.size()) {
        size_t colon = body.find(':', p);
        if (colon == std::string::npos) break;
        size_t semi = body.find(';', colon);
        if (semi == std::string::npos) semi = body.size();
        std::string name = lower(trim(body.substr(p, colon - p)));
        std::string val = trim(body.substr(colon + 1, semi - colon - 1));
        if (!name.empty() && !val.empty()) out[name] = val;
        p = semi + 1;
    }
}

std::vector<CssRule> HtmlParser::parse_stylesheet(const std::string& css) {
    std::vector<CssRule> rules;
    // strip comments
    std::string s;
    s.reserve(css.size());
    for (size_t i = 0; i < css.size();) {
        if (css.compare(i, 2, "/*") == 0) {
            size_t e = css.find("*/", i);
            i = e == std::string::npos ? css.size() : e + 2;
        } else s += css[i++];
    }
    size_t p = 0;
    while (p < s.size()) {
        size_t brace = s.find('{', p);
        if (brace == std::string::npos) break;
        std::string selectors = trim(s.substr(p, brace - p));
        size_t close = s.find('}', brace);
        if (close == std::string::npos) close = s.size();
        std::string body = s.substr(brace + 1, close - brace - 1);
        p = close + 1;
        if (selectors.find('@') != std::string::npos) continue;  // @media etc. skipped
        size_t sp = 0;
        while (sp < selectors.size()) {
            size_t comma = selectors.find(',', sp);
            if (comma == std::string::npos) comma = selectors.size();
            std::string sel = trim(selectors.substr(sp, comma - sp));
            if (!sel.empty()) {
                CssRule r; r.selector = sel;
                parse_prop_list(body, r.props);
                rules.push_back(std::move(r));
            }
            sp = comma + 1;
        }
    }
    return rules;
}

static bool selector_matches(const std::string& sel, const DomNode* n) {
    // supports "tag", ".class", "#id", "tag.class", "tag#id", "tag .class"
    std::string tag, id, cls;
    size_t sp = sel.rfind(' ');
    std::string last = sp == std::string::npos ? sel : sel.substr(sp + 1);
    size_t dot = last.find('.'), hash = last.find('#');
    tag = last.substr(0, std::min(dot == std::string::npos ? last.size() : dot,
                                    hash == std::string::npos ? last.size() : hash));
    if (dot != std::string::npos) {
        size_t end = hash == std::string::npos ? last.size() : hash;
        if (dot < end) cls = last.substr(dot + 1, end - dot - 1);
    }
    if (hash != std::string::npos) id = last.substr(hash + 1);
    if (!tag.empty() && tag != "*" && n->tag != lower(tag)) return false;
    if (!id.empty() && (!n->attrs.count("id") || n->attrs.at("id") != id)) return false;
    if (!cls.empty()) {
        auto it = n->attrs.find("class");
        if (it == n->attrs.end()) return false;
        // token match
        std::istringstream ss(it->second);
        std::string tok; bool found = false;
        while (ss >> tok) if (tok == cls) { found = true; break; }
        if (!found) return false;
    }
    return true;
}

static std::string resolve_vars(const std::string& val,
                                const std::map<std::string, std::string>& custom) {
    std::string out = val;
    for (int guard = 0; guard < 8; ++guard) {
        size_t p = out.find("var(");
        if (p == std::string::npos) break;
        // find the matching close paren (fallback may itself contain parens)
        size_t e = p + 4, depth = 1;
        while (e < out.size() && depth) {
            depth += out[e] == '(' ? 1 : 0;
            depth -= out[e] == ')' ? 1 : 0;
            ++e;
        }
        if (depth) break;
        std::string inner = out.substr(p + 4, e - p - 5);
        // CSS Variables law: var(--name) → custom prop value;
        // var(--name, fallback) → fallback when the prop is unset.
        std::string name = inner, fallback;
        size_t comma = inner.find(',');
        if (comma != std::string::npos) {
            name = inner.substr(0, comma);
            fallback = inner.substr(comma + 1);
        }
        name = trim(name);
        std::string rep = custom.count(name) ? custom.at(name) : trim(fallback);
        out = out.substr(0, p) + rep + out.substr(e);
    }
    return out;
}

static void apply_rule_to(DomNode* n, const std::map<std::string, std::string>& props,
                          const std::map<std::string, std::string>& custom) {
    for (auto& kv : props) {
        std::string v = resolve_vars(kv.second, custom);
        // inheritable: color, font-size, font-weight, text-align
        if (kv.first == "color" && (v == "inherit")) continue;
        n->style[kv.first] = v;
    }
}

void HtmlParser::apply_css(DomNode* node, const std::vector<CssRule>& rules,
                           std::map<std::string, std::string>* custom_props) {
    if (!node) return;
    // collect custom props from :root/html/body
    if (node->tag == "html" || node->tag == "body") {
        for (auto& r : rules) {
            if (r.selector == ":root" || r.selector == "html" || r.selector == "body") {
                for (auto& kv : r.props)
                    if (kv.first.rfind("--", 0) == 0 && custom_props)
                        custom_props->insert(kv);
            }
        }
    }
    // gather custom props visible at this node (walk-up merge happens via caller)
    static thread_local std::map<std::string, std::string> t_custom;
    // html AND body: re-sync from the accumulated root-level custom props —
    // body defines --background1 in its own rule and its own background-color
    // resolves in this visit, so the copy must happen AFTER the collection.
    if (node->tag == "html" || node->tag == "body")
        t_custom = custom_props ? *custom_props : t_custom;
    for (auto& kv : node->style)
        if (kv.first.rfind("--", 0) == 0) t_custom[kv.first] = kv.second;

    // stylesheet rules (specificity: id > class > tag — apply in that order)
    for (int pass = 0; pass < 3; ++pass) {
        for (auto& r : rules) {
            bool is_id = r.selector[0] == '#';
            bool is_class = r.selector[0] == '.';
            bool pass_ok = (pass == 0 && !is_id && !is_class) ||
                           (pass == 1 && is_class) || (pass == 2 && is_id);
            if (!pass_ok) continue;
            if (selector_matches(r.selector, node))
                apply_rule_to(node, r.props, t_custom);
        }
    }
    // inline style wins (specificity law)
    auto it = node->attrs.find("style");
    if (it != node->attrs.end()) parse_prop_list(it->second, node->style);

    for (auto& c : node->children) apply_css(c.get(), rules, custom_props);
}

std::string HtmlParser::inner_html(const DomNode* n) {
    // approximation: concatenation of child text (enough for corpus reads)
    std::string out;
    for (auto& c : n->children) {
        if (c->tag == "#text") out += c->text;
        else {
            out += "<" + c->tag;
            for (auto& a : c->attrs) out += " " + a.first + "=\"" + a.second + "\"";
            out += ">" + inner_html(c.get()) + "</" + c->tag + ">";
        }
    }
    return out;
}

std::string HtmlParser::text_content(const DomNode* n) {
    std::string out;
    for (auto& c : n->children) {
        if (c->tag == "#text") out += c->text;
        else out += text_content(c.get());
    }
    return out;
}

}} // namespace miniandroid::webview
