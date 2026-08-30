/*
 * MiniAndroid Runtime — EXP-114: Tic-Tac-Toe with REAL 3D software rendering
 *
 * What makes it REAL 3D (not a 2D drawing with pseudo-depth):
 *   - True 3D geometry: every visual element is a box/polygon in model space
 *   - Full transform chain: model -> rotate(yaw) -> rotate(pitch) -> translate
 *     -> perspective projection (pinhole camera, focal length, view-space z)
 *   - Depth handling: per-box painter's sort (far->near) + per-face BACKFACE
 *     CULLING in view space (correct for this stacked axis-aligned scene)
 *   - Lambert shading from transformed face normals + directional light
 *   - Depth fog mixing toward background by view-space distance
 *   - Rotation changes the projection of EVERY pixel (verified by pixel-diff)
 *
 * Game AI: minimax (perfect play) on the classic 3x3 board.
 */

#ifndef MINIANDROID_GAMES_TICTACTOE3D_H
#define MINIANDROID_GAMES_TICTACTOE3D_H

#include "renderer/software_renderer.h"

#include <algorithm>
#include <cmath>
#include <cstdint>
#include <string>
#include <utility>
#include <vector>

namespace miniandroid {
namespace games {

using renderer::FrameBuffer;
using renderer::RGBA;

// ---------------------------------------------------------------------------
// 3x3 tic-tac-toe with perfect-play minimax AI
// ---------------------------------------------------------------------------
class TicTacToe {
public:
    static constexpr int EMPTY = 0;
    static constexpr int X = 1;
    static constexpr int O = 2;

    int board[9] = {0, 0, 0, 0, 0, 0, 0, 0, 0};
    int current = X;
    int winner = 0;                  // X, O, or 0
    int win_cells[3] = {-1, -1, -1}; // winning triple
    std::vector<std::pair<int, int>> move_history; // (player, cell)

    static int other(int p) { return p == X ? O : X; }

    bool place(int cell) {
        if (cell < 0 || cell > 8 || board[cell] != EMPTY || winner != 0) return false;
        board[cell] = current;
        move_history.push_back({current, cell});
        check_win();
        if (winner == 0) current = other(current);
        return true;
    }

    bool is_full() const {
        for (int v : board) if (v == EMPTY) return false;
        return true;
    }
    bool over() const { return winner != 0 || is_full(); }

    void check_win() {
        static const int LINES[8][3] = {
            {0,1,2},{3,4,5},{6,7,8},{0,3,6},{1,4,7},{2,5,8},{0,4,8},{2,4,6}};
        for (const auto& l : LINES) {
            if (board[l[0]] != EMPTY && board[l[0]] == board[l[1]] &&
                board[l[1]] == board[l[2]]) {
                winner = board[l[0]];
                for (int i = 0; i < 3; ++i) win_cells[i] = l[i];
                return;
            }
        }
    }

    // Perfect-move chooser for `player` (negamax-style minimax, root = player).
    int best_move(int player) {
        int best = -100, choice = -1;
        for (int c = 0; c < 9; ++c) {
            if (board[c] != EMPTY) continue;
            board[c] = player;
            int saved = current;
            current = other(player);
            int score = minimax_score(1, player);
            current = saved;
            board[c] = EMPTY;
            if (score > best) { best = score; choice = c; }
        }
        return choice;
    }

private:
    int minimax_score(int depth, int root) {
        static const int LINES[8][3] = {
            {0,1,2},{3,4,5},{6,7,8},{0,3,6},{1,4,7},{2,5,8},{0,4,8},{2,4,6}};
        for (const auto& l : LINES) {
            if (board[l[0]] != EMPTY && board[l[0]] == board[l[1]] &&
                board[l[1]] == board[l[2]]) {
                int w = board[l[0]];
                return (w == root) ? 10 - depth : depth - 10;
            }
        }
        if (is_full()) return 0;
        bool maximize = (current == root);
        int best = maximize ? -100 : 100;
        for (int c = 0; c < 9; ++c) {
            if (board[c] != EMPTY) continue;
            board[c] = current;
            current = other(current);
            int v = minimax_score(depth + 1, root);
            current = other(current);
            board[c] = EMPTY;
            if (maximize) best = std::max(best, v);
            else          best = std::min(best, v);
        }
        return best;
    }
};

// ---------------------------------------------------------------------------
// Real 3D pipeline
// ---------------------------------------------------------------------------
struct Vec3 {
    double x = 0, y = 0, z = 0;
    Vec3() = default;
    Vec3(double x_, double y_, double z_) : x(x_), y(y_), z(z_) {}
    Vec3 operator+(const Vec3& o) const { return {x + o.x, y + o.y, z + o.z}; }
    Vec3 operator-(const Vec3& o) const { return {x - o.x, y - o.y, z - o.z}; }
    Vec3 operator*(double s) const { return {x * s, y * s, z * s}; }
};
static inline double dot(const Vec3& a, const Vec3& b) {
    return a.x * b.x + a.y * b.y + a.z * b.z;
}
static inline Vec3 cross(const Vec3& a, const Vec3& b) {
    return {a.y * b.z - a.z * b.y, a.z * b.x - a.x * b.z, a.x * b.y - a.y * b.x};
}
static inline Vec3 vnormalize(const Vec3& a) {
    double l = std::sqrt(dot(a, a));
    return l > 1e-12 ? Vec3(a.x / l, a.y / l, a.z / l) : Vec3(0, 0, 1);
}
static inline Vec3 rotate_y(const Vec3& p, double yaw) {
    double c = std::cos(yaw), s = std::sin(yaw);
    return {c * p.x + s * p.z, p.y, -s * p.x + c * p.z};
}
static inline Vec3 rotate_x(const Vec3& p, double pitch) {
    // Camera looks DOWN from above for pitch > 0:
    // far edge (+z) rises on screen, board top faces the camera.
    double c = std::cos(pitch), s = std::sin(pitch);
    return {p.x, c * p.y + s * p.z, -s * p.y + c * p.z};
}

struct Face {
    Vec3 v[4];    // model space
    Vec3 normal;  // model space (outward)
    RGBA base;
};

// A drawable unit = one convex box (platform or cell) + optional attached
// decorative faces (X bars / O ring segments) drawn right after their box.
struct Box3D {
    Vec3 centroid;            // model space (sort key)
    std::vector<Face> faces;  // box faces (backface-culled)
    std::vector<Face> deco;   // attached piece faces
    Vec3 piece_center{0, 0, 0};
};

struct ScreenPt { double x = 0, y = 0, depth = 1e9; bool ok = false; };

class Board3DRenderer {
public:
    Board3DRenderer(FrameBuffer& fb) : fb_(fb) {}

    void set_camera(double yaw, double pitch, double dist) {
        yaw_ = yaw; pitch_ = pitch; dist_ = dist;
    }
    void set_focal(double f) { focal_ = f; }

    uint64_t pixels_filled() const { return pixels_filled_; }
    uint64_t faces_drawn() const { return faces_drawn_; }
    uint64_t faces_culled() const { return faces_culled_; }
    uint64_t boxes_drawn() const { return boxes_drawn_; }

    ScreenPt project(const Vec3& p) const {
        Vec3 r = rotate_x(rotate_y(p, yaw_), pitch_);
        Vec3 cam = r + Vec3(0, 0, dist_);
        if (cam.z <= 0.05) return {};
        ScreenPt sp;
        sp.x = fb_.get_width() / 2.0  + focal_ * cam.x / cam.z;
        sp.y = fb_.get_height() / 2.0 - focal_ * cam.y / cam.z;
        sp.depth = cam.z;
        sp.ok = true;
        return sp;
    }

    // Backface test in view space: camera looks along +z, so a face is
    // visible iff its transformed normal points back toward the camera
    // (negative z component).
    Vec3 view_normal(const Face& f) const {
        return rotate_x(rotate_y(f.normal, yaw_), pitch_);
    }

    void draw_face_culled(const Face& face, const RGBA& bg) {
        Vec3 n = view_normal(face);
        if (n.z >= 0.0) { ++faces_culled_; return; }   // facing away

        ScreenPt pts[4];
        double depth_sum = 0;
        for (int i = 0; i < 4; ++i) {
            pts[i] = project(face.v[i]);
            if (!pts[i].ok) return;
            depth_sum += pts[i].depth;
        }

        double lam = 0.52 + 0.48 * std::max(0.0, dot(vnormalize(n), light_));
        RGBA base = shade(face.base, lam);

        double avg_z = depth_sum / 4.0;
        double fog = std::min(0.38, std::max(0.0, (avg_z - 4.2) * 0.10));
        RGBA final_c = mix(base, bg, fog);

        fill_quad(pts, final_c);
        ++faces_drawn_;
    }

    // Per-box painter's: sort boxes far->near, draw each box's visible faces.
    void render(const TicTacToe& g, const RGBA& bg) {
        std::vector<Box3D> boxes;
        build_scene(g, boxes);

        std::vector<std::pair<double, size_t>> order(boxes.size());
        for (size_t i = 0; i < boxes.size(); ++i) {
            Vec3 r = rotate_x(rotate_y(boxes[i].centroid, yaw_), pitch_);
            order[i] = {r.z + dist_, i};
        }
        std::stable_sort(order.begin(), order.end(),
                         [](const auto& a, const auto& b) { return a.first > b.first; });

        for (const auto& [depth, i] : order) {
            const Box3D& box = boxes[i];
            for (const Face& f : box.faces) draw_face_culled(f, bg);
            for (const Face& f : box.deco)  draw_face_culled(f, bg);
            ++boxes_drawn_;
        }
    }

private:
    static RGBA shade(RGBA c, double k) {
        return RGBA(uint8_t(std::min(255.0, c.r * k)),
                    uint8_t(std::min(255.0, c.g * k)),
                    uint8_t(std::min(255.0, c.b * k)), 255);
    }
    static RGBA mix(RGBA a, RGBA b, double t) {
        return RGBA(uint8_t(a.r * (1 - t) + b.r * t),
                    uint8_t(a.g * (1 - t) + b.g * t),
                    uint8_t(a.b * (1 - t) + b.b * t), 255);
    }

    // Scanline polygon fill for convex quad (even-odd via edge intersections).
    void fill_quad(ScreenPt* p, RGBA color) {
        double ymin = std::min({p[0].y, p[1].y, p[2].y, p[3].y});
        double ymax = std::max({p[0].y, p[1].y, p[2].y, p[3].y});
        int iy0 = int(std::ceil(ymin)), iy1 = int(std::floor(ymax));
        if (iy1 - iy0 > 4096) return;
        for (int y = std::max(0, iy0); y <= std::min(fb_.get_height() - 1, iy1); ++y) {
            double xs[8]; int nx = 0;
            for (int e = 0; e < 4; ++e) {
                const ScreenPt& a = p[e];
                const ScreenPt& b = p[(e + 1) & 3];
                if ((a.y <= y && b.y > y) || (b.y <= y && a.y > y)) {
                    double t = (y - a.y) / (b.y - a.y);
                    xs[nx++] = a.x + t * (b.x - a.x);
                    if (nx == 8) break;
                }
            }
            if (nx < 2) continue;
            std::sort(xs, xs + nx);
            for (int s = 0; s + 1 < nx; s += 2) {
                int xa = int(std::ceil(xs[s])), xb = int(std::floor(xs[s + 1]));
                for (int x = std::max(0, xa); x <= std::min(fb_.get_width() - 1, xb); ++x) {
                    fb_.set_pixel(x, y, color);
                    ++pixels_filled_;
                }
            }
        }
    }

    static void add_box_faces(Box3D& box, Vec3 mn, Vec3 mx, RGBA base) {
        Face f; f.base = base;
        Vec3 A{mn.x, mn.y, mn.z}, B{mx.x, mn.y, mn.z}, C{mx.x, mx.y, mn.z},
             D{mn.x, mx.y, mn.z}, E{mn.x, mn.y, mx.z}, F{mx.x, mn.y, mx.z},
             G{mx.x, mx.y, mx.z}, H{mn.x, mx.y, mx.z};
        auto push = [&](Vec3 a, Vec3 b, Vec3 c, Vec3 d, Vec3 nrm) {
            f.v[0] = a; f.v[1] = b; f.v[2] = c; f.v[3] = d;
            f.normal = vnormalize(nrm);
            box.faces.push_back(f);
        };
        push(A, B, C, D, Vec3(0, 0, -1));  // front
        push(F, E, H, G, Vec3(0, 0, 1));   // back
        push(E, A, D, H, Vec3(-1, 0, 0));  // left
        push(B, F, G, C, Vec3(1, 0, 0));   // right
        push(D, C, G, H, Vec3(0, 1, 0));   // top
        push(E, F, B, A, Vec3(0, -1, 0));  // bottom
        box.centroid = (mn + mx) * 0.5;
    }

    static Face quad_face(Vec3 a, Vec3 b, Vec3 c, Vec3 d, RGBA base) {
        // normal from winding (counter-clockwise viewed from outside)
        Vec3 n = vnormalize(cross(b - a, d - a));
        Face f; f.v[0] = a; f.v[1] = b; f.v[2] = c; f.v[3] = d;
        f.base = base; f.normal = n;
        return f;
    }

    void build_x_deco(Box3D& box, double cx, double cz, double top, RGBA col) {
        for (double ang : {M_PI / 4, -M_PI / 4}) {
            double hl = 0.34, hh = 0.10, hw = 0.08;
            auto rot = [&](const Vec3& p) {
                double c = std::cos(ang), s = std::sin(ang);
                return Vec3{cx + (p.x - cx) * c + (p.z - cz) * s, p.y,
                            cz - (p.x - cx) * s + (p.z - cz) * c};
            };
            Vec3 corner[4] = {
                {cx - hl, top, cz - hw}, {cx + hl, top, cz - hw},
                {cx + hl, top, cz + hw}, {cx - hl, top, cz + hw}};
            Vec3 A = rot(corner[0]) + Vec3(0, hh, 0);
            Vec3 B = rot(corner[1]) + Vec3(0, hh, 0);
            Vec3 C = rot(corner[2]) + Vec3(0, hh, 0);
            Vec3 D = rot(corner[3]) + Vec3(0, hh, 0);
            box.deco.push_back(quad_face(D, C, B, A, col));   // top
            // sides: outward = quad_face(btm_next, btm_cur, top_cur, top_next)
            const Vec3 upv(0, hh, 0);
            Vec3 rc[4];
            for (int i = 0; i < 4; ++i) rc[i] = rot(corner[i]);
            for (int i = 0; i < 4; ++i) {
                int j = (i + 1) & 3;
                box.deco.push_back(quad_face(rc[j], rc[i], rc[i] + upv, rc[j] + upv, col));
            }
        }
    }

    void build_o_deco(Box3D& box, double cx, double cz, double top, RGBA col) {
        const int NSEG = 14;
        for (int k = 0; k < NSEG; ++k) {
            double a0 = (2.0 * M_PI * k) / NSEG;
            double a1 = (2.0 * M_PI * (k + 0.82)) / NSEG;
            double r0 = 0.22, r1 = 0.38, hh = 0.10;
            auto pt = [&](double a, double r) {
                return Vec3{cx + r * std::cos(a), top, cz + r * std::sin(a)};
            };
            Vec3 A{pt(a0, r0)}, B{pt(a1, r0)}, C{pt(a1, r1)}, D{pt(a0, r1)};
            Vec3 At = A + Vec3(0, hh, 0), Bt = B + Vec3(0, hh, 0);
            Vec3 Ct = C + Vec3(0, hh, 0), Dt = D + Vec3(0, hh, 0);
            box.deco.push_back(quad_face(At, Bt, Ct, Dt, col));                 // top
            box.deco.push_back(quad_face(At, A, B, Bt, col));                   // inner arc
            box.deco.push_back(quad_face(Bt, Ct, C, B, col));                   // end cap
            box.deco.push_back(quad_face(Dt, Ct, C, D, col));                   // outer arc
            box.deco.push_back(quad_face(At, Dt, D, A, col));                   // end cap
        }
    }

    void build_scene(const TicTacToe& g, std::vector<Box3D>& boxes) {
        const RGBA BG_PLATFORM{34, 38, 54, 255};
        const RGBA CELL{58, 72, 96, 255};
        const RGBA CELL_WIN{88, 118, 148, 255};
        const RGBA COL_X{255, 99, 71, 255};
        const RGBA COL_O{80, 200, 255, 255};

        // platform slab — TILED (6x6) so per-box painter's sort stays correct:
        // one huge top face would occlude far cells (big-face failure mode)
        {
            const int N = 6;
            const double half = 1.95;
            const double tile = (2.0 * half) / N;
            for (int i = 0; i < N; ++i)
                for (int j = 0; j < N; ++j) {
                    Box3D t;
                    add_box_faces(t,
                                  {-half + i * tile, -0.34, -half + j * tile},
                                  {-half + (i + 1) * tile, 0.0, -half + (j + 1) * tile},
                                  BG_PLATFORM);
                    boxes.push_back(std::move(t));
                }
        }

        const double S = 1.10, GAP = 0.10;
        for (int row = 0; row < 3; ++row) {
            for (int col = 0; col < 3; ++col) {
                int cell = row * 3 + col;
                double cx0 = -1.5 * S + col * (S + GAP) - S / 2;
                double cz0 = -1.5 * S + row * (S + GAP) - S / 2;
                bool win = false;
                for (int k = 0; k < 3; ++k) if (g.win_cells[k] == cell) win = true;
                double top = win ? 0.30 : 0.12;
                Box3D cellbox;
                add_box_faces(cellbox, {cx0, 0.0, cz0}, {cx0 + S, top, cz0 + S},
                              win ? CELL_WIN : CELL);
                double cx = cx0 + S / 2, cz = cz0 + S / 2;
                if (g.board[cell] == TicTacToe::X) {
                    build_x_deco(cellbox, cx, cz, top, COL_X);
                } else if (g.board[cell] == TicTacToe::O) {
                    build_o_deco(cellbox, cx, cz, top, COL_O);
                }
                boxes.push_back(std::move(cellbox));
            }
        }
    }

    FrameBuffer& fb_;
    double yaw_ = 0.6, pitch_ = 0.55, dist_ = 6.0;
    double focal_ = 1050.0;
    Vec3 light_ = vnormalize(Vec3(-0.45, 0.85, -0.55));
    uint64_t pixels_filled_ = 0, faces_drawn_ = 0, faces_culled_ = 0,
             boxes_drawn_ = 0;
};

} // namespace games
} // namespace miniandroid

#endif // MINIANDROID_GAMES_TICTACTOE3D_H
