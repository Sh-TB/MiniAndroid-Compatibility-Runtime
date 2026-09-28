    // 3. S114 LAYOUT CORE — the containing-block model (CSS 2.1 §10):
    // one positional law for every element. Flow (block + flex column/row)
    // records STATIC positions for out-of-flow children; the positioned pass
    // then places absolute/fixed boxes against their nearest positioned
    // ancestor (or the initial containing block), with margins, shrink-to-
    // fit and offset-computed sizes. No package checks anywhere.
    std::function<int(DomNode*)> measure_w = [&](DomNode* n) -> int {
        int extra = n->border_box ? 0 : 2 * n->border_w + n->pad_l + n->pad_r;
        int cw2 = 0;
        std::string t = own_text_of(n);
        if (!t.empty()) {
            auto& sh = fonts::TextShaper::instance();
            if (sh.available())
                cw2 = std::max(cw2, int(sh.shape(t, n->eff_font_size, n->eff_bold,
                                                 face_of(n)).width));
        }
        for (auto& c : n->children) {
            if (c->tag == "#text" || c->inline_el) continue;
            if (c->display_none || c->positioned) continue;   // hidden keeps slot (visibility law)
            if (c->has_w)
                cw2 = std::max(cw2, c->w + (c->border_box ? 0 : 2 * c->border_w + c->pad_l + c->pad_r));
            else if (c->w_pct >= 0 || !c->w_raw.empty()) continue;
            else cw2 = std::max(cw2, measure_w(c.get()));
        }
        return cw2 + extra;
    };
    // row height law: line-height (px > factor > legacy 1.6) — CSS 2.1 §10.8
    auto line_h_of = [&](DomNode* n) -> int {
        if (n->line_h_px > 0) return n->line_h_px;
        if (n->line_h_num > 0) return int(n->line_h_num * n->eff_font_size);
        return int(n->eff_font_size * 1.6f) + 4;
    };

    // forward decls (flow ⇄ positioned mutual recursion)
    std::function<int(DomNode*, int, int, int, int)> layout_inflow;
    struct CBBox { int x = 0, y = 0, w = 0, h = 0; };
    std::function<void(DomNode*, const CBBox&)> layout_positioned_tree;

    // cb length resolver — % against the CB box on the requested axis
    auto cb_len = [](const std::string& v, float vw_, float vh_, float cbw, float cbh,
                     float em_, float dflt, int axis) -> float {
        if (v.empty()) return dflt;
        CssCtx c;
        c.vw = vw_; c.vh = vh_; c.pctw = cbw; c.pcth = cbh; c.em = em_;
        return css_eval(v, c, dflt, axis);
    };
    auto outer_w_of = [&](DomNode* c) -> int {
        // explicit width → OUTER width (border-box folds pad+border, the
        // content-box law adds them — CSS 2.1 §10.3)
        if (!c->has_w) return -1;
        return c->border_box ? c->w : c->w + 2 * c->border_w + c->pad_l + c->pad_r;
    };

    // in-flow stack: one pass placing block/flex children (used directly and
    // by the 2-pass justify-center law)
    auto layout_stack_once = [&](DomNode* n, int content_x, int content_y,
                                 int content_w, int cy_shift, int avail_h) -> int {
        int cy = content_y + cy_shift;
        int cx = content_x;                       // flex-row cursor
        std::vector<int> widths(n->children.size(), -1);
        std::vector<int> heights(n->children.size(), 0);
        for (size_t i = 0; i < n->children.size(); ++i) {
            DomNode* c = n->children[i].get();
            if (c->tag == "#text") {
                if (is_ws_text(c->text)) continue;
                int tw = 0;
                auto& sh = fonts::TextShaper::instance();
                if (sh.available() && !c->text.empty())
                    tw = int(sh.shape(c->text, n->eff_font_size, n->eff_bold,
                                      face_of(n)).width);
                widths[i] = tw;
                heights[i] = line_h_of(n);
                continue;
            }
            if (c->tag == "script" || c->tag == "style" || c->tag == "head" ||
                c->tag == "title" || c->tag == "link" || c->tag == "meta" ||
                c->tag == "audio")
                continue;
            if (c->display_none) continue;        // visibility:hidden keeps its slot
            if (c->inline_el) { widths[i] = -2; continue; }   // merged into parent text
            // STATIC POSITION RECORD — where this box would sit if it were
            // in-flow (CSS 2.1 §10.3.7: auto offsets use the static position)
            c->static_x = n->flex_row ? cx + c->mar_l : content_x;
            c->static_y = n->flex_row ? content_y : cy;
            if (c->positioned) continue;          // out of flow — placed later vs the CB
            int extra = c->border_box ? 0 : 2 * c->border_w + c->pad_l + c->pad_r;
            int ow = outer_w_of(c);
            if (ow >= 0) widths[i] = ow;
            else if (c->w_pct >= 0) widths[i] = int(float(content_w) * c->w_pct / 100.f);
            else if (!c->w_raw.empty())
                widths[i] = int(cb_len(c->w_raw, float(w), float(h),
                                       float(content_w), float(avail_h > 0 ? avail_h : content_w),
                                       c->font_size, content_w, 0));
            else if (n->flex && n->align_items == 1)
                widths[i] = std::min(measure_w(c), content_w);  // flex center shrink
            else widths[i] = content_w;                         // block fill law
            if (c->max_w >= 0 && widths[i] > c->max_w) widths[i] = c->max_w;
            widths[i] = std::max(widths[i], 2 * c->border_w);
        }
        // flex-ROW cross-size pass: tallest child governs the line height
        int row_h = 0;
        if (n->flex && n->flex_row)
            for (size_t i = 0; i < n->children.size(); ++i)
                if (widths[i] >= 0 && heights[i] == 0) heights[i] = -1;  // element child marker
        for (size_t i = 0; i < n->children.size(); ++i) {
            DomNode* c = n->children[i].get();
            if (c->tag == "#text") {
                if (is_ws_text(c->text)) continue;
                int x = content_x + (n->eff_align == 1
                          ? std::max(0, content_w - widths[i]) / 2
                          : n->eff_align == 2 ? std::max(0, content_w - widths[i]) : 0);
                if (n->flex_row) { heights[i] = line_h_of(n); row_h = std::max(row_h, heights[i]); c->static_x = x; }
                text_line[c] = {cy, widths[i]};
                if (!n->flex_row) cy += heights[i];
                continue;
            }
            if (widths[i] < 0) continue;
            int x;
            if (n->flex_row) x = cx + c->mar_l;
            else x = content_x + c->mar_l;
            if (!n->flex_row && (n->align_items == 1 || c->mar_lr_auto))
                x = content_x + std::max(0, content_w - widths[i]) / 2;
            int hb;
            if (heights[i] == -1) heights[i] = 0;   // marker consumed
            hb = layout_inflow(c, x, cy, widths[i], avail_h);
            if (n->flex_row) {
                row_h = std::max(row_h, hb + c->mar_t + c->mar_b);
                cx += widths[i] + c->mar_l + c->mar_r;
                // vertical centering of the row member (align-items law)
                int dy = 0;   // align start (stretch behaves as start here)
                if (n->align_items == 1) dy = std::max(0, (row_h - (hb + c->mar_t + c->mar_b)) / 2);
                if (dy) {
                    int need = dy - 0;
                    (void)need;
                }
                heights[i] = hb;
            } else {
                cy += hb + c->mar_b;
            }
        }
        // second sweep for flex-row vertical centering (2-pass shift law)
        if (n->flex && n->flex_row && n->align_items == 1 && row_h > 0) {
            cx = content_x;
            for (size_t i = 0; i < n->children.size(); ++i) {
                DomNode* c = n->children[i].get();
                if (c->tag == "#text" || widths[i] < 0) {
                    if (c->tag == "#text" && !is_ws_text(c->text) && widths[i] >= 0) cx += widths[i];
                    continue;
                }
                if (c->positioned || c->display_none || c->inline_el) continue;
                int hb = heights[i];
                int dy = std::max(0, (row_h - (hb + c->mar_t + c->mar_b)) / 2);
                layout_inflow(c, cx + c->mar_l, content_y + dy, widths[i], avail_h);
                cx += widths[i] + c->mar_l + c->mar_r;
            }
        }
        if (n->flex && n->flex_row) return row_h;
        return cy - content_y - cy_shift;
    };

    // in-flow layout: places n at (x,y) with outer width w_in, lays out its
    // in-flow children, applies height % and the relative-offset shift.
    layout_inflow = [&](DomNode* n, int x, int y, int w_in, int avail_h) -> int {
        // relative offset shift (CSS 2.1 §9.4.3): the flow slot stays, the
        // box moves by left/top (or negative right/bottom)
        if (n->pos_mode == 1 && n->parent) {
            DomNode* cbn = nullptr;
            for (DomNode* p = n->parent; p; p = p->parent)
                if (p->pos_mode != 0 && p->laid_out) { cbn = p; break; }
            float cbw = cbn ? float(cbn->w) : float(w);
            float cbh = cbn ? float(cbn->h) : float(h);
            int dx = 0, dy = 0;
            if (!n->off_l.empty()) dx = int(cb_len(n->off_l, float(w), float(h), cbw, cbh, n->font_size, 0, 0));
            else if (!n->off_r.empty()) dx = -int(cb_len(n->off_r, float(w), float(h), cbw, cbh, n->font_size, 0, 0));
            if (!n->off_t.empty()) dy = int(cb_len(n->off_t, float(w), float(h), cbw, cbh, n->font_size, 0, 1));
            else if (!n->off_b.empty()) dy = -int(cb_len(n->off_b, float(w), float(h), cbw, cbh, n->font_size, 0, 1));
            x += dx; y += dy;
        }
        n->x = x; n->y = y; n->w = w_in; n->laid_out = true;
        if (wv_trace())
            std::cerr << "[WV-BOX] tag=" << n->tag
                      << " class=" << (n->attrs.count("class") ? n->attrs.at("class") : "")
                      << " box=" << x << "," << y << " " << w_in << "x" << n->h
                      << " pos=" << n->pos_mode << " flex=" << n->flex
                      << " row=" << n->flex_row << " fs=" << n->eff_font_size << std::endl;
        // height % (border-box folds pad+border)
        if (!n->has_h && n->h_pct >= 0 && avail_h > 0) {
            n->h = int(float(avail_h) * n->h_pct / 100.f);
            if (!n->border_box) n->h += 2 * n->border_w + n->pad_t + n->pad_b;
            if (n->h_raw.empty()) n->has_h = true;
        }
        // calc/%-bearing height strings for FLOW boxes resolve against the
        // available height (else auto)
        if (!n->has_h && !n->h_raw.empty() && avail_h > 0) {
            float pv = cb_len(n->h_raw, float(w), float(h), float(w_in),
                              float(avail_h), n->font_size, -1, 1);
            if (pv >= 0) {
                n->h = int(pv);
                if (!n->border_box) n->h += 2 * n->border_w + n->pad_t + n->pad_b;
                n->has_h = true;
            }
        }
        int content_w = w_in - (n->border_box ? 0 : 0) - 2 * n->border_w - n->pad_l - n->pad_r;
        if (content_w < 0) content_w = 0;
        int fixed_inner = -1;
        if (n->has_h) fixed_inner = n->h - 2 * n->border_w - n->pad_t - n->pad_b;
        int child_avail = fixed_inner > 0 ? fixed_inner : 0;
        int used = layout_stack_once(n, x + n->border_w + n->pad_l,
                                     y + n->border_w + n->pad_t, content_w, 0, child_avail);
        if (n->flex && n->justify_content == 1 && fixed_inner > 0 && used < fixed_inner) {
            int shift = (fixed_inner - used) / 2;
            layout_stack_once(n, x + n->border_w + n->pad_l,
                              y + n->border_w + n->pad_t, content_w, shift, child_avail);
            used = fixed_inner;
        }
        // leaf min-height law (legacy flow parity for leaf rows)
        if (!n->has_h && n->h_pct < 0) {
            bool leaf = true;
            for (auto& c : n->children)
                if (c->tag != "#text" && !c->inline_el) { leaf = false; break; }
            if (leaf) {
                int min_h = line_h_of(n);
                if (used < min_h) used = min_h;
            }
        }
        if (!n->has_h)
            n->h = used + 2 * n->border_w + n->pad_t + n->pad_b;
        return n->h;
    };

    // positioned placement: absolute/fixed against the containing block
    layout_positioned_tree = [&](DomNode* n, const CBBox& cb_in) {
        for (auto& cc : n->children) {
            DomNode* c = cc.get();
            if (c->tag == "script" || c->tag == "style" || c->tag == "head" ||
                c->tag == "title" || c->tag == "link" || c->tag == "meta") continue;
            if (c->display_none) continue;
            if (c->pos_mode >= 2) {
                // fixed → the ICB, absolute → the passed CB (CSS 2.1 §10.1)
                CBBox box = c->pos_mode == 3 ? CBBox{0, 0, w, h} : cb_in;
                float l = -1, t = -1, r_ = -1, b_ = -1;
                if (!c->off_l.empty()) l = cb_len(c->off_l, float(w), float(h), float(box.w), float(box.h), c->font_size, 0, 0);
                if (!c->off_t.empty()) t = cb_len(c->off_t, float(w), float(h), float(box.w), float(box.h), c->font_size, 0, 1);
                if (!c->off_r.empty()) r_ = cb_len(c->off_r, float(w), float(h), float(box.w), float(box.h), c->font_size, 0, 0);
                if (!c->off_b.empty()) b_ = cb_len(c->off_b, float(w), float(h), float(box.w), float(box.h), c->font_size, 0, 1);
                // ── width (§10.3.7 ladder) ──
                int ow = outer_w_of(c);
                if (ow < 0 && c->w_pct >= 0) ow = int(float(box.w) * c->w_pct / 100.f);
                if (ow < 0 && !c->w_raw.empty())
                    ow = int(cb_len(c->w_raw, float(w), float(h), float(box.w), float(box.h),
                                    c->font_size, -1, 0));
                if (ow < 0 && l >= 0 && r_ >= 0)
                    ow = int(float(box.w) - l - r_ - float(c->mar_l + c->mar_r));
                int avail_w = int(float(box.w) - std::max(0.f, l) - std::max(0.f, r_)
                                 - float(c->mar_l + c->mar_r));
                if (ow < 0) ow = std::min(measure_w(c), std::max(0, avail_w));
                if (c->max_w >= 0 && ow > c->max_w) ow = c->max_w;
                ow = std::max(ow, 2 * c->border_w);
                // ── height ──
                int oh = -1;
                if (c->has_h) oh = c->border_box ? c->h : c->h + 2 * c->border_w + c->pad_t + c->pad_b;
                else if (c->h_pct >= 0) oh = int(float(box.h) * c->h_pct / 100.f);
                else if (!c->h_raw.empty())
                    oh = int(cb_len(c->h_raw, float(w), float(h), float(box.w), float(box.h),
                                    c->font_size, -1, 1));
                if (oh < 0 && t >= 0 && b_ >= 0) oh = int(float(box.h) - t - b_ - float(c->mar_t + c->mar_b));
                // ── placement (auto offsets → the static position) ──
                int x2, y2;
                if (l >= 0) x2 = box.x + int(l) + c->mar_l;
                else if (r_ >= 0) x2 = box.x + box.w - int(r_) - c->mar_r - ow;
                else x2 = c->static_x + c->mar_l;
                if (t >= 0) y2 = box.y + int(t) + c->mar_t;
                else if (b_ >= 0 && oh >= 0) y2 = box.y + box.h - int(b_) - c->mar_b - oh;
                else y2 = c->static_y + c->mar_t;
                // provisional height for auto boxes; layout_inflow refines it
                if (oh >= 0) { c->h = oh; c->has_h = true; }
                layout_inflow(c, x2, y2, ow, box.h);
                // bottom-offset law: height was auto → anchor via the measured h
                if (t < 0 && b_ >= 0 && c->pos_mode != 3)
                    layout_inflow(c, x2, box.y + box.h - int(b_) - c->mar_b - c->h, ow, box.h);
                // recurse: this box is the CB for ITS positioned descendants
                CBBox inner;
                inner.x = c->x + c->border_w + c->pad_l;
                inner.y = c->y + c->border_w + c->pad_t;
                inner.w = c->w - 2 * c->border_w - c->pad_l - c->pad_r;
                inner.h = c->h - 2 * c->border_w - c->pad_t - c->pad_b;
                if (inner.w < 0) inner.w = 0;
                if (inner.h < 0) inner.h = 0;
                layout_positioned_tree(c, inner);
            } else {
                // in-flow child — its own box becomes the CB when positioned-
                // relative; otherwise pass the CB through unchanged
                CBBox pass = cb_in;
                if (c->pos_mode == 1 && c->laid_out) {
                    pass.x = c->x + c->border_w + c->pad_l;
                    pass.y = c->y + c->border_w + c->pad_t;
                    pass.w = c->w - 2 * c->border_w - c->pad_l - c->pad_r;
                    pass.h = c->h - 2 * c->border_w - c->pad_t - c->pad_b;
                    if (pass.w < 0) pass.w = 0;
                    if (pass.h < 0) pass.h = 0;
                }
                layout_positioned_tree(c, pass);
            }
        }
    };

    // flow root: the body fills the ICB width; height % chains start there
    DomNode* body_n = impl->body();
    layout_inflow(body_n, 0, 0, w, h);
    // body (position:relative per UA resets) is the first containing block
    CBBox body_cb;
    body_cb.x = body_n->x + body_n->border_w + body_n->pad_l;
    body_cb.y = body_n->y + body_n->border_w + body_n->pad_t;
    body_cb.w = body_n->w - 2 * body_n->border_w - body_n->pad_l - body_n->pad_r;
    body_cb.h = body_n->h - 2 * body_n->border_w - body_n->pad_t - body_n->pad_b;
    if (body_cb.w < 0) body_cb.w = 0;
    if (body_cb.h < 0) body_cb.h = 0;
    layout_positioned_tree(body_n, body_cb);

