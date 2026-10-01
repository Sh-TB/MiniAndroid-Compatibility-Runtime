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
        // S133 ES-MODULE law: type="module" selects module parse goals.
        std::string stype;
        if (n->attrs.count("type")) stype = lower(n->attrs["type"]);
        bool is_module = stype.find("module") != std::string::npos;
        if (!src.empty()) doc.external_scripts.push_back({src, is_module ? "module" : ""});
        else if (!n->text.empty()) doc.inline_scripts.push_back({n->text, is_module});
        doc.script_nodes_total++;
    }
    for (auto& c : n->children) collect_scripts(c.get(), doc, html, script_order);
}

// S113: fragment parse must not double-collect <link> styles (the engine
// fetches them once at document level). Thread-local flag keeps the parser
// signature stable for existing callers.
static thread_local bool doc_is_fragment = false;

ParsedDocument HtmlParser::parse(const std::string& html) {
    ParsedDocument doc;
    doc_is_fragment = false;
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
        // S113: <link rel="stylesheet" href=...> → external stylesheet law
        // (elp is the stable pointer — el was already moved into the tree)
        if (tag == "link" && !doc_is_fragment) {
            std::string rel, href;
            auto it = elp->attrs.find("rel");
            if (it != elp->attrs.end()) rel = lower(it->second);
            it = elp->attrs.find("href");
            if (it != elp->attrs.end()) href = it->second;
            if (rel.find("stylesheet") != std::string::npos && !href.empty())
                doc.external_styles.push_back({href, ""});
        }
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
    doc_is_fragment = true;
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

// S113: value-length parser for shorthand lists ("24px", "14px 20px",
// "1px 2px 3px 4px") — px-only corpus law; returns count of values found.
static int split_lengths(const std::string& v, int out[4]) {
    std::istringstream ss(v);
    std::string tok;
    int n = 0;
    while (ss >> tok && n < 4) {
        out[n++] = int(::strtod(tok.c_str(), nullptr));
    }
    // CSS shorthand expansion law: 1=all, 2=(tb,lr), 3=(t,lr,b), 4=(t,r,b,l)
    if (n == 2) { out[2] = out[0]; out[3] = out[1]; }
    else if (n == 3) { out[3] = out[1]; }
    else if (n == 1) { out[1] = out[2] = out[3] = out[0]; }
    return n;
}

std::vector<CssRule> HtmlParser::parse_stylesheet(const std::string& css) {
    return parse_stylesheet_impl(css, -1, -1);
}

std::vector<CssRule> HtmlParser::parse_stylesheet_impl(const std::string& css,
                                                       int media_min_w, int media_max_w) {
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
        // S113: nested-brace matching law — @media blocks CONTAIN rules, so
        // the first '}' is an inner rule's close, not the block's. Depth-
        // count to the matching close for @-blocks; flat rules keep the
        // fast path. body_end = position of the closing '}'; p lands one
        // past it (a selector must never swallow a previous '}').
        size_t body_end, next_p;
        {
            size_t depth = 1, scan = brace + 1;
            bool nested = selectors.rfind("@", 0) == 0;
            if (nested) {
                while (scan < s.size() && depth) {
                    if (s[scan] == '{') ++depth;
                    else if (s[scan] == '}') --depth;
                    ++scan;
                }
                body_end = scan ? scan - 1 : scan;
                next_p = scan;
            } else {
                body_end = s.find('}', brace);
                if (body_end == std::string::npos) { body_end = s.size(); next_p = s.size(); }
                else next_p = body_end + 1;
            }
        }
        std::string body = s.substr(brace + 1, body_end - (brace + 1));
        p = next_p;
        // S113 @-rule law: @media hoists inner rules when the width constraint
        // is recorded (evaluated at render time); @font-face keeps its props;
        // @keyframes/other @-rules are dropped (static paint corpus).
        if (selectors.rfind("@media", 0) == 0) {
            int mn = media_min_w, mx = media_max_w;
            size_t lp = selectors.find('(');
            while (lp != std::string::npos) {
                size_t rp = selectors.find(')', lp);
                if (rp == std::string::npos) break;
                std::string cond = selectors.substr(lp + 1, rp - lp - 1);
                // tokenize feature:value
                size_t colon = cond.find(':');
                if (colon != std::string::npos) {
                    std::string feat = lower(trim(cond.substr(0, colon)));
                    int val = int(::strtod(cond.c_str() + colon + 1, nullptr));
                    if (feat == "max-width") mx = mx < 0 ? val : std::min(mx, val);
                    else if (feat == "min-width") mn = mn < 0 ? val : std::max(mn, val);
                }
                lp = selectors.find('(', rp);
            }
            // recurse into the media body with the constraint attached
            for (auto& r : parse_stylesheet_impl(body, mn, mx))
                rules.push_back(std::move(r));
            continue;
        }
        if (selectors.rfind("@font-face", 0) == 0) {
            CssRule r; r.selector = "@font-face";
            parse_prop_list(body, r.props);
            r.media_min_w = media_min_w; r.media_max_w = media_max_w;
            rules.push_back(std::move(r));
            continue;
        }
        if (selectors.find('@') != std::string::npos) continue;  // @keyframes etc. dropped
        size_t sp = 0;
        while (sp < selectors.size()) {
            size_t comma = selectors.find(',', sp);
            if (comma == std::string::npos) comma = selectors.size();
            std::string sel = trim(selectors.substr(sp, comma - sp));
            if (!sel.empty()) {
                CssRule r; r.selector = sel;
                parse_prop_list(body, r.props);
                r.media_min_w = media_min_w; r.media_max_w = media_max_w;
                // S113 pseudo-element law: "sel::before" / "sel::after" (also
                // legacy single-colon ":before"/":after" for non-pseudo classes)
                auto mark_pseudo = [&](const std::string& suffix, bool before) {
                    size_t pp = sel.rfind(suffix);
                    if (pp != std::string::npos && pp + suffix.size() == sel.size()) {
                        r.selector = trim(sel.substr(0, pp));
                        if (before) r.pseudo_before = true; else r.pseudo_after = true;
                    }
                };
                mark_pseudo("::before", true);
                mark_pseudo("::after", false);
                if (!r.pseudo_before) mark_pseudo(":before", true);
                if (!r.pseudo_after && !r.pseudo_before) mark_pseudo(":after", false);
                rules.push_back(std::move(r));
            }
            sp = comma + 1;
        }
    }
    return rules;
}

// S113 compound selector law: one part of a selector — optional tag/*,
// optional #id, optional .class list ("div.cls-a.cls-b", "*", ".x#y").
// S114 selector atoms: [attr], [attr=val], :checked — the state pseudo-
// class and attribute grammars exercised by form-driven HTML5 apps.
static bool atom_matches(const std::string& atom, const DomNode* n) {
    if (atom == ":checked") {
        auto it = n->attrs.find("checked");
        return it != n->attrs.end() &&
               (it->second.empty() || it->second == "checked" || it->second == "true");
    }
    // S118 positional pseudo-class law (CSS Selectors §6.6.5): :first-child,
    // :last-child, :nth-child(an+b), :nth-last-child(an+b) — position among
    // ELEMENT siblings (#text nodes never count). Modern stylesheets
    // differentiate stacked icon layers through these (the accelerace car's
    // three-layer stroke colorwork is pure :nth-child — without the law the
    // stroke rules never matched and the car painted nothing).
    auto element_index = [](const DomNode* nn) -> int {
        if (!nn->parent) return -1;
        int idx = 0;
        for (auto& c : nn->parent->children) {
            if (c->tag == "#text") continue;
            ++idx;
            if (c.get() == nn) return idx;
        }
        return -1;
    };
    auto element_count = [](const DomNode* nn) -> int {
        if (!nn->parent) return 0;
        int cnt = 0;
        for (auto& c : nn->parent->children) if (c->tag != "#text") ++cnt;
        return cnt;
    };
    auto nth_matches = [](const std::string& arg0, int idx) -> bool {
        if (idx <= 0) return false;
        std::string s = trim(arg0);
        // case-insensitive per spec
        for (auto& ch : s) ch = char(::tolower((unsigned char)ch));
        if (s.empty()) return false;
        if (s == "odd") return idx % 2 == 1;
        if (s == "even") return idx % 2 == 0;
        size_t np = s.find('n');
        if (np == std::string::npos) {          // plain integer
            for (char ch : s) if (ch != '+' && (ch < '0' || ch > '9')) return false;
            return atoi(s.c_str()) == idx;
        }
        std::string a_part = trim(s.substr(0, np));
        int a = 1;
        if (a_part == "-") a = -1;
        else if (!a_part.empty()) {
            for (char ch : a_part)
                if (ch != '+' && ch != '-' && (ch < '0' || ch > '9')) return false;
            a = atoi(a_part.c_str());
        }
        std::string b_part = trim(s.substr(np + 1));
        int b = 0;
        if (!b_part.empty()) {
            for (char ch : b_part)
                if (ch != '+' && ch != '-' && (ch < '0' || ch > '9')) return false;
            b = atoi(b_part.c_str());
        }
        if (a == 0) return idx == b;
        int diff = idx - b;
        return diff % a == 0 && diff / a >= 0;
    };
    if (atom == ":first-child") return element_index(n) == 1;
    if (atom == ":last-child") {
        int cnt = element_count(n);
        return cnt > 0 && element_index(n) == cnt;
    }
    if (atom.rfind(":nth-child(", 0) == 0 && atom.back() == ')')
        return nth_matches(atom.substr(11, atom.size() - 12), element_index(n));
    if (atom.rfind(":nth-last-child(", 0) == 0 && atom.back() == ')') {
        int cnt = element_count(n);
        return nth_matches(atom.substr(16, atom.size() - 17), cnt - element_index(n) + 1);
    }
    if (!atom.empty() && atom[0] == '[') {
        std::string body = atom.substr(1, atom.size() >= 2 ? atom.size() - 2 : 0);
        size_t eq = body.find('=');
        std::string key = eq == std::string::npos ? body : body.substr(0, eq);
        std::string want = eq == std::string::npos ? std::string() : body.substr(eq + 1);
        auto strip = [](std::string s) {
            s.erase(std::remove(s.begin(), s.end(), '"'), s.end());
            s.erase(std::remove(s.begin(), s.end(), '\''), s.end());
            return trim(s);
        };
        key = trim(lower(key));
        auto it = n->attrs.find(key);
        if (eq == std::string::npos) return it != n->attrs.end();
        return it != n->attrs.end() && strip(it->second) == strip(want);
    }
    return false;   // unknown atom never matches (honest)
}

static bool compound_matches(const std::string& c0, const DomNode* n) {
    std::string c = lower(trim(c0));
    if (c.empty()) return false;
    std::string tag, id;
    std::vector<std::string> classes, atoms;
    size_t i = 0;
    if (c[0] != '.' && c[0] != '#' && c[0] != ':') {
        size_t e = c.find_first_of(".#[:");
        tag = c.substr(0, e);
        i = e == std::string::npos ? c.size() : e;
    }
    while (i < c.size()) {
        char kind = c[i];
        if (kind == ':') {
            size_t e = c.find_first_of(".#[:", i + 1);
            atoms.push_back(c.substr(i, e - i));
            i = e == std::string::npos ? c.size() : e;
            continue;
        }
        if (kind == '[') {
            size_t e = c.find(']', i);
            if (e == std::string::npos) return false;
            atoms.push_back(c.substr(i, e - i + 1));
            i = e + 1;
            continue;
        }
        size_t e = c.find_first_of(".#[:", i + 1);
        std::string tok = c.substr(i + 1, e - i - 1);
        if (kind == '#') id = tok;
        else if (kind == '.') classes.push_back(tok);
        i = e == std::string::npos ? c.size() : e;
    }
    if (!tag.empty() && tag != "*" && n->tag != tag) return false;
    if (!id.empty() && (!n->attrs.count("id") || n->attrs.at("id") != id)) return false;
    for (auto& cls : classes) {
        auto it = n->attrs.find("class");
        if (it == n->attrs.end()) return false;
        std::istringstream ss(it->second);
        std::string tok; bool found = false;
        while (ss >> tok) if (tok == cls) { found = true; break; }
        if (!found) return false;
    }
    for (auto& a : atoms) if (!atom_matches(a, n)) return false;
    return true;
}

// S114 selector grammar: a sequence of compounds joined by combinators —
// ' ' descendant, '>' child, '+' adjacent sibling (CSS2.1 §5.1-§5.7).
// Matching walks right-to-left from the subject node.
static bool selector_matches(const std::string& sel, const DomNode* n) {
    // tokenize into (combinator, compound) pairs; combinator of the FIRST
    // entry is ' ' (root)
    struct Part { char comb; std::string compound; };
    std::vector<Part> parts;
    std::string cur;
    char pending_comb = ' ';
    size_t i = 0;
    std::string s = trim(sel);
    while (i <= s.size()) {
        char ch = i < s.size() ? s[i] : '\0';
        if (ch == '>' || ch == '+') {
            if (!trim(cur).empty()) {
                parts.push_back({pending_comb, trim(cur)});
                cur.clear();
            }
            pending_comb = ch;
            ++i;
            continue;
        }
        if (ch == ' ' || ch == '\0') {
            std::string t = trim(cur);
            if (!t.empty()) {
                // collapse: multiple spaces = single descendant combinator,
                // but a pending '+'/'>' always wins (A > B, A + B)
                parts.push_back({pending_comb, t});
                pending_comb = ' ';
                cur.clear();
            }
            ++i;
            continue;
        }
        cur += ch;
        ++i;
    }
    if (parts.empty()) return false;
    if (!compound_matches(parts.back().compound, n)) return false;
    const DomNode* cur_n = n;
    for (int p = int(parts.size()) - 1; p >= 1; --p) {
        char comb = parts[p].comb;
        if (comb == ' ') {
            // descendant: climb until a match (or fail at the root)
            const DomNode* anc = cur_n->parent;
            bool hit = false;
            while (anc) {
                if (anc->tag != "#text" && compound_matches(parts[p - 1].compound, anc)) {
                    cur_n = anc; hit = true; break;
                }
                anc = anc->parent;
            }
            if (!hit) return false;
        } else if (comb == '>') {
            const DomNode* par = cur_n->parent;
            if (!par || par->tag == "#text" ||
                !compound_matches(parts[p - 1].compound, par)) return false;
            cur_n = par;
        } else if (comb == '+') {
            // adjacent: previous ELEMENT sibling
            const DomNode* prev = cur_n->parent ? cur_n->previous_element_sibling() : nullptr;
            if (!prev || !compound_matches(parts[p - 1].compound, prev)) return false;
            cur_n = prev;
        }
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
        // S114 specificity law: JS/inline-authored keys outrank stylesheet
        // rules — never overwrite them (shorthand expansions skip too)
        if (n->inline_keys.count(kv.first)) continue;
        std::string v = resolve_vars(kv.second, custom);
        // inheritable: color, font-size, font-weight, text-align
        if (kv.first == "color" && (v == "inherit")) continue;
        n->style[kv.first] = v;
        // S114 cascade law: shorthands EXPAND into their longhands at apply
        // time, so a later longhand (or a later rule's longhand) correctly
        // overrides just its side (#field: universal `margin:0` then
        // `#field{margin-top:var(--size_3)}` — the longhand used to lose
        // against the stale shorthand key).
        if (kv.first == "margin") {
            if (v.find(' ') == std::string::npos) {   // single-value → expand;
                // multi-value shorthands stay for the shorthand parser
                for (const char* side : {"margin-top", "margin-right",
                                         "margin-bottom", "margin-left"}) {
                    if (n->inline_keys.count(side)) continue;
                    n->style[side] = v;
                }
            }
        } else if (kv.first == "padding") {
            if (v.find(' ') == std::string::npos) {
                for (const char* side : {"padding-top", "padding-right",
                                         "padding-bottom", "padding-left"}) {
                    if (n->inline_keys.count(side)) continue;
                    n->style[side] = v;
                }
            }
        }
    }
}

void HtmlParser::apply_css(DomNode* node, const std::vector<CssRule>& rules,
                           std::map<std::string, std::string>* custom_props) {
    apply_css_impl(node, rules, custom_props, false);
}

void HtmlParser::apply_css_impl(DomNode* node, const std::vector<CssRule>& rules,
                                std::map<std::string, std::string>* custom_props,
                                bool ignore_media) {
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
            // S113: ::before/::after rules style the PSEUDO-BOX, not the
            // element — applying them to the element leaked e.g.
            // .header::after { font-size:16px } onto .header itself.
            // The engine's style walk consumes their content separately.
            if (r.pseudo_before || r.pseudo_after) continue;
            if (r.media_min_w >= 0 || r.media_max_w >= 0) {
                if (ignore_media) continue;   // render-time evaluation handles these
            }
            if (selector_matches(r.selector, node))
                apply_rule_to(node, r.props, t_custom);
        }
    }
    // inline style wins (specificity law) — keys recorded so later rule
    // applications never overwrite them
    auto it = node->attrs.find("style");
    if (it != node->attrs.end()) {
        std::map<std::string, std::string> inline_props;
        parse_prop_list(it->second, inline_props);
        for (auto& kv : inline_props) {
            node->style[kv.first] = kv.second;
            node->inline_keys.insert(kv.first);
        }
    }

    for (auto& c : node->children) apply_css_impl(c.get(), rules, custom_props, ignore_media);
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

bool HtmlParser::matches_selector(const std::string& sel, const DomNode* n) {
    return selector_matches(sel, n);
}

std::string HtmlParser::resolve_var_string(const std::string& val,
                                           const std::map<std::string, std::string>& custom) {
    return resolve_vars(val, custom);
}

}} // namespace miniandroid::webview
