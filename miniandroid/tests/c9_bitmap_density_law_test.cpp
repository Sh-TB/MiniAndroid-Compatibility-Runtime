/*
 * C9-1 (CODER 9) — BitmapFactory.Options density law, unit law test.
 *
 * Pins the pure law bitmap_factory_density_law() (bitmap_shadow.{h,cpp})
 * against the AOSP chain it mirrors:
 *   BitmapFactory.decodeResourceStream seeding (Java, master ~557-574),
 *   BitmapFactory.cpp native scale
 *     (iff inScaled && inDensity!=0 && inDensity!=DENSITY_NONE &&
 *          inTargetDensity!=0 && inDensity!=inTargetDensity;
 *      scale = target/in_density; scaled = (int)(dim*scale + 0.5f)),
 *   setDensityFromOptions (bitmap marked inDensity, then inTargetDensity
 *   when scaled), and the inSampleSize ceil law (dim + s - 1) / s.
 * out* carry FINAL dims (sample and density composed). Options has NO
 * public outDensity — the density lives on the Bitmap.
 *
 * Recorded honest divergence (documented in the law itself): degenerate
 * zero-scaled dims clamp to 1 instead of failing the decode.
 *
 * Build: link with the full C9 object set (see scripts/c9 docs / Issue
 * #521 ACH-1 §7) and run — expects 36/36.
 */

#include <framework/bitmap_shadow.h>

#include <cstdio>

using miniandroid::framework::BitmapFactoryDensityInput;
using miniandroid::framework::BitmapFactoryDensityResult;
using miniandroid::framework::bitmap_factory_density_law;

static int g_pass = 0, g_fail = 0;
#define LAW(cond, num, name)                                                    \
    do {                                                                        \
        if (cond) { ++g_pass; }                                                 \
        else { ++g_fail;                                                        \
            std::printf("  LAW %02d FAIL: %s\n", (num), (name)); }              \
    } while (0)

static constexpr int32_t DENSITY_NONE = 0xFFFF;

int main() {
    // ── F-A: degenerate inputs (laws 1–4) ────────────────────────────────
    {
        auto r = bitmap_factory_density_law({});
        LAW(!r.valid, 1, "degenerate: default input (0x0) invalid");
        LAW(r.width == 0 && r.height == 0, 2, "degenerate: dims stay 0");

        BitmapFactoryDensityInput in; in.raw_width = -5; in.raw_height = 30;
        LAW(!bitmap_factory_density_law(in).valid, 3, "degenerate: negative width");

        BitmapFactoryDensityInput in2; in2.raw_width = 60; in2.raw_height = -1;
        LAW(!bitmap_factory_density_law(in2).valid, 4, "degenerate: negative height");
    }

    // ── F-B: inSampleSize law (laws 5–10) ────────────────────────────────
    {
        BitmapFactoryDensityInput in; in.raw_width = 60; in.raw_height = 30;
        in.in_sample_size = 0;  // AOSP: never honor < 1
        auto r = bitmap_factory_density_law(in);
        LAW(r.valid && r.sampled_width == 60 && r.sampled_height == 30, 5,
            "sample: 0 clamps to 1 (identity)");

        BitmapFactoryDensityInput in2; in2.raw_width = 60; in2.raw_height = 30;
        in2.in_sample_size = -4;
        auto r2 = bitmap_factory_density_law(in2);
        LAW(r2.valid && r2.sampled_width == 60 && r2.sampled_height == 30, 6,
            "sample: negative clamps to 1");

        BitmapFactoryDensityInput in3; in3.raw_width = 61; in3.raw_height = 31;
        in3.in_sample_size = 2;
        auto r3 = bitmap_factory_density_law(in3);
        LAW(r3.sampled_width == 31 && r3.sampled_height == 16, 7,
            "sample: ceil law (61+1)/2=31, (31+1)/2=16");

        BitmapFactoryDensityInput in4; in4.raw_width = 30; in4.raw_height = 30;
        in4.in_sample_size = 2;
        auto r4 = bitmap_factory_density_law(in4);
        LAW(r4.sampled_width == 15 && r4.sampled_height == 15, 8,
            "sample: exact divide (30/2=15)");

        BitmapFactoryDensityInput in5; in5.raw_width = 62; in5.raw_height = 30;
        in5.in_sample_size = 4;
        auto r5 = bitmap_factory_density_law(in5);
        LAW(r5.sampled_width == 16 && r5.sampled_height == 8, 9,
            "sample: ceil law s=4 (62->16, 30->8)");

        BitmapFactoryDensityInput in6; in6.raw_width = 100; in6.raw_height = 100;
        in6.in_sample_size = 3;
        auto r6 = bitmap_factory_density_law(in6);
        LAW(r6.sampled_width == 34 && r6.sampled_height == 34, 10,
            "sample: non-power-of-two s=3 ((100+2)/3=34)");
    }

    // ── F-C: scale gates — each condition alone disables scaling (11–16) ─
    {
        BitmapFactoryDensityInput in; in.raw_width = 60; in.raw_height = 30;
        in.in_density = 0; in.in_target_density = 420;  // inDensity unset
        auto r = bitmap_factory_density_law(in);
        LAW(!r.density_scaled && r.width == 60 && r.height == 30, 11,
            "gate: inDensity==0 → no scale");

        BitmapFactoryDensityInput in2; in2.raw_width = 60; in2.raw_height = 30;
        in2.in_density = 240; in2.in_target_density = 0;  // target unset
        auto r2 = bitmap_factory_density_law(in2);
        LAW(!r2.density_scaled && r2.bitmap_density == 240, 12,
            "gate: target==0 → no scale, bitmap keeps inDensity");

        BitmapFactoryDensityInput in3; in3.raw_width = 60; in3.raw_height = 30;
        in3.in_density = 240; in3.in_target_density = 240;
        auto r3 = bitmap_factory_density_law(in3);
        LAW(!r3.density_scaled && r3.width == 60 && r3.bitmap_density == 240, 13,
            "gate: inDensity==target → identity");

        BitmapFactoryDensityInput in4; in4.raw_width = 60; in4.raw_height = 30;
        in4.in_density = 240; in4.in_target_density = 420; in4.in_scaled = false;
        auto r4 = bitmap_factory_density_law(in4);
        LAW(!r4.density_scaled && r4.width == 60 && r4.height == 30 &&
            r4.bitmap_density == 240, 14,
            "gate: inScaled=false → no scale, bitmap marked inDensity");

        BitmapFactoryDensityInput in5; in5.raw_width = 60; in5.raw_height = 30;
        in5.in_density = DENSITY_NONE; in5.in_target_density = 420;  // nodpi law
        auto r5 = bitmap_factory_density_law(in5);
        LAW(!r5.density_scaled && r5.width == 60 && r5.bitmap_density == DENSITY_NONE,
            15, "gate: DENSITY_NONE (nodpi) → never scaled");

        BitmapFactoryDensityInput in6; in6.raw_width = 40; in6.raw_height = 20;
        in6.in_density = 160; in6.in_target_density = 160;  // mdpi identity
        auto r6 = bitmap_factory_density_law(in6);
        LAW(!r6.density_scaled && r6.width == 40 && r6.height == 20, 16,
            "gate: unscaled keeps sampled dims and flag false");
    }

    // ── F-D: scale arithmetic (laws 17–23) ───────────────────────────────
    {
        BitmapFactoryDensityInput in; in.raw_width = 60; in.raw_height = 30;
        in.in_density = 240; in.in_target_density = 420;  // hdpi fixture @ xhdpi-ish
        auto r = bitmap_factory_density_law(in);
        LAW(r.width == 105 && r.height == 53, 17,
            "scale: 60x30 @240->420 = 105x53 ((int)(d*1.75+0.5))");
        LAW(r.bitmap_density == 420, 18,
            "scale: bitmap marked with TARGET density (setDensityFromOptions)");
        LAW(r.density_scaled, 19, "scale: density_scaled flag true");

        BitmapFactoryDensityInput in2; in2.raw_width = 60; in2.raw_height = 30;
        in2.in_density = 420; in2.in_target_density = 160;  // downscale
        auto r2 = bitmap_factory_density_law(in2);
        LAW(r2.width == 23 && r2.height == 11, 20,
            "scale: 60x30 @420->160 = 23x11 (round-half-up: floor(22.86+0.5), floor(11.43+0.5))");

        BitmapFactoryDensityInput in3; in3.raw_width = 40; in3.raw_height = 20;
        in3.in_density = 320; in3.in_target_density = 420;
        auto r3 = bitmap_factory_density_law(in3);
        LAW(r3.width == 53 && r3.height == 26, 21,
            "scale: 40x20 @320->420 = 53x26");

        BitmapFactoryDensityInput in4; in4.raw_width = 100; in4.raw_height = 50;
        in4.in_density = 160; in4.in_target_density = 240;
        auto r4 = bitmap_factory_density_law(in4);
        LAW(r4.width == 150 && r4.height == 75, 22,
            "scale: 100x50 @160->240 = 150x75 (exact x1.5)");

        BitmapFactoryDensityInput in5; in5.raw_width = 1; in5.raw_height = 1;
        in5.in_density = 160; in5.in_target_density = 240;
        auto r5 = bitmap_factory_density_law(in5);
        LAW(r5.width == 2 && r5.height == 2, 23,
            "scale: round-half-up 1x1 @1.5 = 2x2 ((int)(1.5+0.5))");
    }

    // ── F-E: sample + density composition (laws 24–27) ───────────────────
    {
        BitmapFactoryDensityInput in; in.raw_width = 60; in.raw_height = 30;
        in.in_density = 240; in.in_target_density = 420; in.in_sample_size = 2;
        auto r = bitmap_factory_density_law(in);
        LAW(r.sampled_width == 30 && r.sampled_height == 15, 24,
            "compose: sampled dims exposed (30x15)");
        LAW(r.width == 53 && r.height == 26, 25,
            "compose: final = scale(sample) → 53x26 (fixture CASE01 sample law)");
        LAW(r.bitmap_density == 420, 26,
            "compose: composed bitmap still marked target density");

        BitmapFactoryDensityInput in2; in2.raw_width = 108; in2.raw_height = 70;
        in2.in_density = 240; in2.in_target_density = 480; in2.in_sample_size = 7;
        auto r2 = bitmap_factory_density_law(in2);
        LAW(r2.sampled_width == 16 && r2.width == 32, 27,
            "compose: s=7 ceil (108->16) then x2.0 → 32");
    }

    // ── F-F: clamp divergence — recorded honestly (laws 28–29) ───────────
    {
        BitmapFactoryDensityInput in; in.raw_width = 1; in.raw_height = 1;
        in.in_density = 1000; in.in_target_density = 160;
        auto r = bitmap_factory_density_law(in);
        LAW(r.valid && r.density_scaled && r.width == 1 && r.height == 1, 28,
            "clamp: zero-scaled dims clamp to 1 (documented divergence)");

        BitmapFactoryDensityInput in2; in2.raw_width = 2; in2.raw_height = 2;
        in2.in_density = 2000; in2.in_target_density = 100;
        auto r2 = bitmap_factory_density_law(in2);
        LAW(r2.valid && r2.width == 1 && r2.height == 1 && r2.bitmap_density == 100,
            29, "clamp: clamp still marks the target density");
    }

    // ── F-G: density marking laws (laws 30–32) ───────────────────────────
    {
        BitmapFactoryDensityInput in; in.raw_width = 60; in.raw_height = 30;
        in.in_density = DENSITY_NONE; in.in_target_density = 0;
        auto r = bitmap_factory_density_law(in);
        LAW(r.bitmap_density == DENSITY_NONE, 30,
            "mark: DENSITY_NONE survives to Bitmap.getDensity");

        BitmapFactoryDensityInput in2; in2.raw_width = 60; in2.raw_height = 30;
        in2.in_density = 160; in2.in_target_density = 640;
        auto r2 = bitmap_factory_density_law(in2);
        LAW(r2.bitmap_density == 640 && r2.bitmap_density != in2.in_density, 31,
            "mark: scaled bitmap answers TARGET, never the source density");

        BitmapFactoryDensityInput in3; in3.raw_width = 60; in3.raw_height = 30;
        in3.in_density = 0; in3.in_target_density = 420;  // non-resource decode
        auto r3 = bitmap_factory_density_law(in3);
        LAW(r3.bitmap_density == 0, 32,
            "mark: inDensity unset → no setDensity call (0)");
    }

    // ── F-H: composed odd cases (laws 33–36) ─────────────────────────────
    {
        BitmapFactoryDensityInput in; in.raw_width = 61; in.raw_height = 31;
        in.in_density = 240; in.in_target_density = 420; in.in_sample_size = 2;
        auto r = bitmap_factory_density_law(in);
        LAW(r.width == 54 && r.height == 28, 33,
            "odd: 61x31 s=2 @240->420 → sampled 31x16 → 54x28");

        BitmapFactoryDensityInput in2; in2.raw_width = 70; in2.raw_height = 35;
        in2.in_density = 300; in2.in_target_density = 420;
        auto r2 = bitmap_factory_density_law(in2);
        LAW(r2.width == 98 && r2.height == 49, 34,
            "odd: non-bucket densities 300->420 = x1.4 exactly 98x49");

        BitmapFactoryDensityInput in3; in3.raw_width = 100; in3.raw_height = 100;
        in3.in_density = 160; in3.in_target_density = 320; in3.in_sample_size = 3;
        auto r3 = bitmap_factory_density_law(in3);
        LAW(r3.sampled_width == 34 && r3.width == 68 && r3.height == 68, 35,
            "odd: s=3 then x2.0 → 34 -> 68 (compose chain)");

        BitmapFactoryDensityInput in4; in4.raw_width = 105; in4.raw_height = 52;
        in4.in_density = 420; in4.in_target_density = 420; in4.in_sample_size = 2;
        auto r4 = bitmap_factory_density_law(in4);
        LAW(r4.width == 53 && r4.height == 26 && !r4.density_scaled &&
            r4.bitmap_density == 420, 36,
            "odd: identity densities with sample → sampled dims, marked 420");
    }

    std::printf("c9_bitmap_density_law_test: %d/%d PASS\n", g_pass, g_pass + g_fail);
    return g_fail == 0 ? 0 : 1;
}
