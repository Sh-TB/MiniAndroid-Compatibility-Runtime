// UNIFIED_007 — Real software 3D rendering proof.
//
// Renders a shaded 3D solid (cube + tetrahedron) with perspective
// projection at yaw = 0/60/120/180/240/300 through a REAL pipeline:
//   mesh → model rotation → view → perspective projection →
//   back-face culling → painter's depth sort → flat shading (N·L) →
//   rasterization (scanline fill) → framebuffer PNG
//
// Evidence (geometry-region only, per master request §"3D proof"):
//   per frame: nonwhite pixels, projected bbox
//   per consecutive pair (i, i+1) AND wraparound (5→0):
//     changed_px, bbox(changed region), mean|Δ| over changed region
// No text/UI overlay pollutes the frame — diffs are pure geometry.
// Every pair uses FRESH counters (the old counter-reset bug cannot recur).
//
// Output: u007_3d_<angle>.png × 6 + u007_3d_proof_metrics.json
// Exit 0 = all 6 frames rendered, all 6 pairwise diffs non-trivial.
#include <cmath>
#include <cstdio>
#include <cstring>
#include <cstdint>
#include <string>
#include <vector>
#include <fstream>
#include <sstream>
#include <algorithm>

struct Vec3 {
    double x, y, z;
    Vec3 operator-(const Vec3& o) const { return {x - o.x, y - o.y, z - o.z}; }
    Vec3 operator+(const Vec3& o) const { return {x + o.x, y + o.y, z + o.z}; }
    Vec3 operator*(double s) const { return {x * s, y * s, z * s}; }
    double dot(const Vec3& o) const { return x * o.x + y * o.y + z * o.z; }
    Vec3 cross(const Vec3& o) const {
        return {y * o.z - z * o.y, z * o.x - x * o.z, x * o.y - y * o.x};
    }
    double len() const { return std::sqrt(dot(*this)); }
    Vec3 norm() const { double l = len(); return l > 0 ? *this * (1.0 / l) : *this; }
};

struct Face { int a, b, c; uint8_t base_r, base_g, base_b; };

struct Mesh {
    std::vector<Vec3> verts;
    std::vector<Face> faces;
};

static Mesh make_cube(double s) {
    Mesh m;
    for (int sx = -1; sx <= 1; sx += 2)
        for (int sy = -1; sy <= 1; sy += 2)
            for (int sz = -1; sz <= 1; sz += 2)
                m.verts.push_back({sx * s, sy * s, sz * s});
    // vertex index: (sx+1)/2*4 + (sy+1)/2*2 + (sz+1)/2
    auto idx = [](int sx, int sy, int sz) {
        return ((sx + 1) / 2) * 4 + ((sy + 1) / 2) * 2 + ((sz + 1) / 2);
    };
    auto quad = [&](int a, int b, int c, int d, uint8_t r, uint8_t g, uint8_t bl) {
        m.faces.push_back({a, b, c, r, g, bl});
        m.faces.push_back({a, c, d, r, g, bl});
    };
    quad(idx(-1,-1,-1), idx(1,-1,-1), idx(1,1,-1), idx(-1,1,-1), 200, 70, 70);   // front (z-)
    quad(idx(-1,-1, 1), idx(1,-1, 1), idx(1,1, 1), idx(-1,1, 1), 70, 200, 70);   // back (z+)
    quad(idx(-1,-1,-1), idx(-1,-1, 1), idx(-1,1, 1), idx(-1,1,-1), 70, 70, 200); // left
    quad(idx( 1,-1,-1), idx( 1,-1, 1), idx( 1,1, 1), idx( 1,1,-1), 200, 200, 70);// right
    quad(idx(-1, 1,-1), idx(-1, 1, 1), idx( 1,1, 1), idx( 1,1,-1), 200, 70, 200);// top
    quad(idx(-1,-1,-1), idx(-1,-1, 1), idx( 1,-1, 1), idx( 1,-1,-1), 70,200,200);// bottom
    return m;
}

static Mesh make_tetrahedron(double s) {
    Mesh m;
    m.verts = {{s, s, s}, {-s, -s, s}, {-s, s, -s}, {s, -s, -s}};
    m.faces = {{0,1,2,240,150,60}, {0,3,1,60,240,150}, {0,2,3,150,60,240}, {1,3,2,60,150,240}};
    return m;
}

struct Rgba8 { uint8_t r, g, b; };

struct Image {
    int w, h;
    std::vector<Rgba8> px;
    Image(int W, int H) : w(W), h(H), px((size_t)W * H, {255, 255, 255}) {}
    void set(int x, int y, Rgba8 c) {
        if (x < 0 || y < 0 || x >= w || y >= h) return;
        px[(size_t)y * w + x] = c;
    }
    Rgba8 get(int x, int y) const {
        if (x < 0 || y < 0 || x >= w || y >= h) return {255, 255, 255};
        return px[(size_t)y * w + x];
    }
};

struct Projected {
    std::vector<Vec3> pts;          // screen-space (x, y, depth)
    int min_x = 1 << 30, min_y = 1 << 30, max_x = -1, max_y = -1;
    long nonwhite = 0;
};

// Render one mesh at yaw (degrees). Camera: perspective, eye at +Z looking -Z.
static Projected render_mesh(Image& img, const Mesh& mesh, double yaw_deg,
                             double pitch_deg, double dist) {
    Projected out;
    double cy = std::cos(yaw_deg * M_PI / 180.0), sy = std::sin(yaw_deg * M_PI / 180.0);
    double cp = std::cos(pitch_deg * M_PI / 180.0), sp = std::sin(pitch_deg * M_PI / 180.0);
    double fov_scale = img.w * 0.9;
    int cx = img.w / 2, cyimg = img.h / 2;

    struct Tri { Vec3 p0, p1, p2; uint8_t r, g, b; double depth; };
    std::vector<Tri> tris;
    for (const auto& f : mesh.faces) {
        Vec3 v[3] = {mesh.verts[f.a], mesh.verts[f.b], mesh.verts[f.c]};
        Vec3 wv[3];
        for (int i = 0; i < 3; ++i) {
            // yaw about Y
            Vec3 r1 = {v[i].x * cy + v[i].z * sy, v[i].y, -v[i].x * sy + v[i].z * cy};
            // pitch about X
            Vec3 r2 = {r1.x, r1.y * cp - r1.z * sp, r1.y * sp + r1.z * cp};
            // push away from camera
            wv[i] = {r2.x, r2.y, r2.z + dist};
        }
        // back-face cull: normal · (face_center - eye) < 0 → keep
        Vec3 n = (wv[1] - wv[0]).cross(wv[2] - wv[0]);
        Vec3 center = (wv[0] + wv[1] + wv[2]) * (1.0 / 3.0);
        Vec3 eye = {0, 0, dist + 4.0 * dist};
        if (n.dot(center - eye) > 0) continue;
        // flat shade
        Vec3 l = n.norm();
        Vec3 light = {0.4, 0.7, -0.6};
        double lam = std::max(0.25, std::fabs(l.dot(light.norm())));
        // project
        Vec3 spts[3];
        for (int i = 0; i < 3; ++i) {
            double z = wv[i].z;
            double sx = cx + (wv[i].x / z) * fov_scale;
            double syp = cyimg - (wv[i].y / z) * fov_scale;
            spts[i] = {sx, syp, z};
            out.min_x = std::min(out.min_x, (int)sx);
            out.max_x = std::max(out.max_x, (int)sx);
            out.min_y = std::min(out.min_y, (int)syp);
            out.max_y = std::max(out.max_y, (int)syp);
        }
        tris.push_back({spts[0], spts[1], spts[2],
                        (uint8_t)std::min(255.0, f.base_r * lam),
                        (uint8_t)std::min(255.0, f.base_g * lam),
                        (uint8_t)std::min(255.0, f.base_b * lam),
                        (spts[0].z + spts[1].z + spts[2].z) / 3.0});
    }
    // painter's sort: far first
    std::sort(tris.begin(), tris.end(),
              [](const Tri& a, const Tri& b) { return a.depth > b.depth; });
    // rasterize with edge-interpolation fill (barycentric)
    for (const auto& t : tris) {
        int x0 = std::max(0, (int)std::floor(std::min({t.p0.x, t.p1.x, t.p2.x})));
        int x1 = std::min(img.w - 1, (int)std::ceil(std::max({t.p0.x, t.p1.x, t.p2.x})));
        int y0 = std::max(0, (int)std::floor(std::min({t.p0.y, t.p1.y, t.p2.y})));
        int y1 = std::min(img.h - 1, (int)std::ceil(std::max({t.p0.y, t.p1.y, t.p2.y})));
        double area = (t.p1.x - t.p0.x) * (t.p2.y - t.p0.y) -
                      (t.p2.x - t.p0.x) * (t.p1.y - t.p0.y);
        if (std::fabs(area) < 1e-9) continue;
        for (int y = y0; y <= y1; ++y) {
            for (int x = x0; x <= x1; ++x) {
                double px = x + 0.5, py = y + 0.5;
                double w0 = ((t.p1.x - t.p0.x) * (py - t.p0.y) -
                             (px - t.p0.x) * (t.p1.y - t.p0.y)) / area;
                double w1 = ((t.p2.x - t.p1.x) * (py - t.p1.y) -
                             (px - t.p1.x) * (t.p2.y - t.p1.y)) / area;
                double w2 = ((t.p0.x - t.p2.x) * (py - t.p2.y) -
                             (px - t.p2.x) * (t.p0.y - t.p2.y)) / area;
                if (w0 >= 0 && w1 >= 0 && w2 >= 0) {
                    Rgba8 before = img.get(x, y);
                    img.set(x, y, {t.r, t.g, t.b});
                    if (before.r == 255 && before.g == 255 && before.b == 255)
                        out.nonwhite++;
                }
            }
        }
    }
    return out;
}

// Pairwise diff — FRESH counters each call (no shared accumulators).
struct PairDiff {
    long changed = 0;
    int min_x = 1 << 30, min_y = 1 << 30, max_x = -1, max_y = -1;
    double mean_abs_diff = 0.0;   // over changed region
    bool meaningful() const { return changed > 200; }
};
static PairDiff diff_images(const Image& a, const Image& b) {
    PairDiff d;
    long sum = 0;
    for (int y = 0; y < a.h; ++y) {
        for (int x = 0; x < a.w; ++x) {
            Rgba8 pa = a.get(x, y), pb = b.get(x, y);
            if (pa.r != pb.r || pa.g != pb.g || pa.b != pb.b) {
                d.changed++;
                int ad = std::abs(pa.r - pb.r) + std::abs(pa.g - pb.g) +
                         std::abs(pa.b - pb.b);
                sum += ad;
                d.min_x = std::min(d.min_x, x);
                d.max_x = std::max(d.max_x, x);
                d.min_y = std::min(d.min_y, y);
                d.max_y = std::max(d.max_y, y);
            }
        }
    }
    d.mean_abs_diff = d.changed > 0 ? (double)sum / d.changed : 0.0;
    return d;
}

static void write_ppm(const Image& img, const std::string& path) {
    std::ofstream f(path, std::ios::binary);
    f << "P6\n" << img.w << " " << img.h << "\n255\n";
    for (auto& p : img.px) f << p.r << p.g << p.b;
}

int main(int argc, char** argv) {
    std::string prefix = argc > 1 ? argv[1] : "run/u007_3d/frame";
    const int W = 512, H = 512;
    const double angles[6] = {0, 60, 120, 180, 240, 300};

    std::ostringstream mj;
    mj << "{\n  \"pipeline\": \"mesh→rotate→project→cull→depthsort→shade→raster\",\n";
    mj << "  \"frames\": [\n";

    Image prev(W, H);
    bool has_prev = false;
    bool all_ok = true;

    for (int i = 0; i < 6; ++i) {
        Image img(W, H);
        Mesh cube = make_cube(1.0);
        Projected pc = render_mesh(img, cube, angles[i], 22.0, 6.0);
        // tetrahedron orbiting at offset — second solid, different phase
        Mesh tet = make_tetrahedron(0.55);
        for (auto& v : tet.verts) v.x += 2.2;
        Projected pt = render_mesh(img, tet, angles[i] + 30.0, 22.0, 6.0);

        char path[256];
        std::snprintf(path, sizeof(path), "%s_%03d.ppm", prefix.c_str(), (int)angles[i]);
        write_ppm(img, path);

        mj << "  {\"yaw_deg\": " << (int)angles[i]
           << ", \"cube_nonwhite_px\": " << pc.nonwhite
           << ", \"cube_bbox\": [" << pc.min_x << "," << pc.min_y << ","
           << pc.max_x << "," << pc.max_y << "]"
           << ", \"tet_nonwhite_px\": " << pt.nonwhite
           << ", \"file\": \"" << path << "\""
           << (has_prev ? "" : "") << "}";

        if (has_prev) {
            PairDiff d = diff_images(prev, img);
            bool ok = d.meaningful();
            all_ok = all_ok && ok;
            mj << ",\n  {\"record\": \"pair_diff\", \"from_yaw\": "
               << (int)angles[i - 1] << ", \"to_yaw\": " << (int)angles[i]
               << ", \"changed_px\": " << d.changed
               << ", \"bbox\": [" << d.min_x << "," << d.min_y << ","
               << d.max_x << "," << d.max_y << "]"
               << ", \"mean_abs_diff\": " << d.mean_abs_diff
               << ", \"meaningful\": " << (ok ? "true" : "false") << "}";
        }
        mj << (i < 5 ? "," : "") << "\n";

        prev = img;
        has_prev = true;
    }
    // wraparound pair 300°→0° (360°) must also differ
    {
        Image first(W, H);
        Mesh cube = make_cube(1.0);
        render_mesh(first, cube, 0.0, 22.0, 6.0);
        Mesh tet = make_tetrahedron(0.55);
        for (auto& v : tet.verts) v.x += 2.2;
        render_mesh(first, tet, 30.0, 22.0, 6.0);
        PairDiff d = diff_images(prev, first);
        bool ok = d.meaningful();
        all_ok = all_ok && ok;
        mj << "  ,{\"record\": \"pair_diff_wraparound\", \"from_yaw\": 300, "
           << "\"to_yaw\": 360, \"changed_px\": " << d.changed
           << ", \"mean_abs_diff\": " << d.mean_abs_diff
           << ", \"meaningful\": " << (ok ? "true" : "false") << "}\n";
    }
    mj << "],\n  \"all_ok\": " << (all_ok ? "true" : "false") << "\n}\n";
    std::string mpath = prefix + "_metrics.json";
    std::ofstream mjf(mpath);
    mjf << mj.str();
    std::printf("3D proof: %s all_ok=%d\n", mpath.c_str(), (int)all_ok);
    return all_ok ? 0 : 2;
}
