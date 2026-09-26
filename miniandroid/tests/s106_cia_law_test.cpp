// s106_canvas_input_audio_law_test.cpp — S106 micro-gap fence (third batch).
// Three families against the REAL engine objects:
//
// CANVAS (Affine2D from canvas_shadow.h — the exact matrix the draw path
// bakes into every recorded op; Skia SkCanvas pre-concat law):
//   C1  (MG-207 canvas translate)  — M∘T maps points by +t; composition
//                                    order law: T-then-S ≠ S-then-T.
//   C2  (MG-208 canvas scale)      — scale multiplies linear columns;
//                                    stroke width scales by mean_scale
//                                    (Skia sqrt|det| law).
//   C3  (MG-209 canvas rotate)     — +90° maps +x onto +y (y-down cw).
//   C4  (MG-210 nested transforms) — save/translate/rotate/draw/restore
//                                    composes M0∘T∘R exactly (hand math).
//   C5  (MG-204 filter quality)    — draw_image_region nearest-neighbour
//                                    upscale keeps block structure (the
//                                    Paint.FilterBitmap=false default law).
//
// INPUT (framework::TouchDispatcher — G06 canonical pipeline):
//   I1  (MG-146 event cancellation) — DOWN→CANCEL: unpressed, no click,
//                                     no long-press (View.java L17172).
//   I2  (MG-149 outside bounds)     — DOWN outside the view rect never
//                                     targets/presses it.
//
// AUDIO (audio::MediaPlayer / audio::SoundPool / decode_audio_file):
//   A1  (MG-232 MediaPlayer init)   — IDLE→INITIALIZED→PREPARED→STARTED
//                                     with the AOSP legal-transition table.
//   A2  (MG-231 SoundPool init)     — construct→load→play → sample loaded,
//                                     stream PLAYING.
//   A3  (MG-233 resource audio)     — a REAL RIFF/WAVE buffer decodes to
//                                     non-empty PCM with correct rate/chan.
//
// Exit 0 iff ALL laws hold.

#include "../src/audio/audio_engine.h"
#include "../src/framework/android_shadows.h"
#include "../src/framework/canvas_shadow.h"
#include "../src/framework/touch_dispatcher.h"
#include "../src/renderer/software_renderer.h"

#include "../src/dex/dalvik_engine.h"
#include "../src/framework/heap_adapter.h"

#include <cmath>
#include <cstdio>
#include <cstring>
#include <vector>

using namespace miniandroid;

static int g_pass = 0, g_fail = 0;
static void check(const char* name, bool ok, const std::string& detail = "") {
    if (ok) { ++g_pass; std::printf("PASS %s %s\n", name, detail.c_str()); }
    else { ++g_fail; std::printf("FAIL %s %s\n", name, detail.c_str()); }
}

static bool near(float a, float b, float eps = 0.75f) {
    return std::fabs(a - b) <= eps;
}

// ── CANVAS ──────────────────────────────────────────────────────────────────
static void canvas_family() {
    using framework::Affine2D;
    // C1 (MG-207): translate
    {
        Affine2D m; m.pre_translate(5.f, 3.f);
        float ox, oy; m.map(2.f, 2.f, ox, oy);
        check("C1 mg-207 translate maps by +t", near(ox, 7.f) && near(oy, 5.f),
              "map=" + std::to_string(ox) + "," + std::to_string(oy));
        // composition order: T then S != S then T (Skia pre-concat law)
        Affine2D ts; ts.pre_translate(10.f, 0.f); ts.pre_scale(2.f, 2.f);
        Affine2D st; st.pre_scale(2.f, 2.f); st.pre_translate(10.f, 0.f);
        float a1, b1, a2, b2;
        ts.map(1.f, 1.f, a1, b1); st.map(1.f, 1.f, a2, b2);
        check("C1 mg-207 order law T∘S != S∘T",
              near(a1, 12.f) && near(a2, 22.f), "ts=" + std::to_string(a1) +
              " st=" + std::to_string(a2));
    }
    // C2 (MG-208): scale + stroke width law
    {
        Affine2D m; m.pre_scale(3.f, 2.f);
        float ox, oy; m.map(4.f, 4.f, ox, oy);
        check("C2 mg-208 scale multiplies columns",
              near(ox, 12.f) && near(oy, 8.f),
              "map=" + std::to_string(ox) + "," + std::to_string(oy));
        check("C2 mg-208 mean_scale = sqrt|det| (Skia stroke law)",
              near(m.mean_scale(), std::sqrt(6.f), 0.01f),
              "ms=" + std::to_string(m.mean_scale()));
    }
    // C3 (MG-209): rotate
    {
        Affine2D m; m.pre_rotate(90.f);
        float ox, oy; m.map(1.f, 0.f, ox, oy);
        check("C3 mg-209 rot90 maps +x onto +y (y-down cw)",
              near(ox, 0.f, 0.01f) && near(oy, 1.f, 0.01f),
              "map=" + std::to_string(ox) + "," + std::to_string(oy));
        Affine2D r180; r180.pre_rotate(180.f);
        r180.map(3.f, -2.f, ox, oy);
        check("C3 mg-209 rot180 exact", near(ox, -3.f) && near(oy, 2.f),
              "map=" + std::to_string(ox) + "," + std::to_string(oy));
    }
    // C4 (MG-210): nested composition (save → translate → rotate → draw)
    {
        Affine2D base; base.pre_translate(100.f, 50.f);   // outer state
        Affine2D m = base;                                 // save()
        m.pre_translate(10.f, 0.f);                        // inner translate
        m.pre_rotate(90.f);                                // inner rotate
        float ox, oy; m.map(2.f, 0.f, ox, oy);
        // hand composition: rot90cw of (2,0) = (0,2); +translate(10,0) ->
        // (10,2); +base(100,50) -> (110,52)
        check("C4 mg-210 nested M0∘T∘R composes", near(ox, 110.f) &&
              near(oy, 52.f),
              "map=" + std::to_string(ox) + "," + std::to_string(oy));
    }
    // C5 (MG-204): nearest-neighbour upscale block law
    {
        renderer::FrameBuffer fb(8, 8);
        renderer::SoftwareCanvas canvas(&fb);
        // 2x2 source: red, blue / green, white
        std::vector<uint8_t> src = {255,0,0,255, 0,0,255,255,
                                    0,255,0,255, 255,255,255,255};
        canvas.draw_image_region(src.data(), 2, 2, 0, 0, 2, 2, 0, 0, 8, 8);
        auto px = [&](int x, int y) {
            auto q = fb.get_pixel(x, y);
            return std::make_tuple(q.r, q.g, q.b);
        };
        auto [r0, g0, b0] = px(1, 1);
        auto [r1, g1, b1] = px(6, 1);
        auto [r2, g2, b2] = px(1, 6);
        bool law = r0 == 255 && g0 == 0 && b0 == 0 &&
                   r1 == 0 && g1 == 0 && b1 == 255 &&
                   r2 == 0 && g2 == 255 && b2 == 0;
        check("C5 mg-204 nearest upscale keeps blocks", law,
              "q00=" + std::to_string(r0) + " q10=" + std::to_string(r1));
    }
}

// ── INPUT ───────────────────────────────────────────────────────────────────
struct InputRig {
    dalvik::DalvikHeap heap;
    framework::DalvikHeapAdapter heap_adapter{&heap};
    framework::ViewShadow views;
    framework::HandlerShadow handler;
    framework::TouchDispatcher dispatcher{&views, &handler};
    int clicks = 0, long_clicks = 0;
    uint32_t last_click = 0;

    InputRig() {
        views.init(&heap_adapter);
        handler.init(&heap_adapter);
        dispatcher.set_click_dispatch([&](uint32_t id) {
            ++clicks; last_click = id; return true;
        });
        dispatcher.set_long_click_dispatch([&](uint32_t id, bool& consumed) {
            ++long_clicks; consumed = false; return true;
        });
    }
    uint32_t button(int x, int y, int w, int h) {
        uint32_t id = views.create_view("Landroid/widget/Button;");
        auto* n = views.find_node(id);
        n->x = x; n->y = y; n->width = w; n->height = h;
        n->enabled = true; n->clickable = true;
        return id;
    }
    void drain() {
        for (int i = 0; i < 64; ++i) {
            std::vector<uint32_t> due;
            if (handler.drain_ready(&due) == 0) break;
            for (uint32_t id : due) dispatcher.fire_framework_callback(id, nullptr);
        }
    }
};

static void input_family() {
    // I1 (MG-146): CANCEL law
    {
        InputRig r;
        uint32_t b = r.button(100, 100, 200, 100);
        r.dispatcher.dispatch(b, {framework::TouchAction::DOWN, 150, 150});
        auto* n = r.views.find_node(b);
        bool pressed_after_down = n->pressed;
        r.dispatcher.dispatch(b, {framework::TouchAction::CANCEL, 150, 150});
        r.drain();
        check("I1 mg-146 DOWN armed press", pressed_after_down, "");
        check("I1 mg-146 CANCEL unpresses + no click",
              !n->pressed && r.clicks == 0 && r.long_clicks == 0,
              "clicks=" + std::to_string(r.clicks));
    }
    // I2 (MG-149): outside bounds
    {
        InputRig r;
        uint32_t b = r.button(100, 100, 100, 100);
        r.dispatcher.dispatch(b, {framework::TouchAction::DOWN, 300, 300});
        auto* n = r.views.find_node(b);
        r.dispatcher.dispatch(b, {framework::TouchAction::UP, 300, 300});
        r.drain();
        check("I2 mg-149 outside DOWN never presses", !n->pressed, "");
        check("I2 mg-149 outside gesture never clicks", r.clicks == 0 &&
              r.last_click == 0, "clicks=" + std::to_string(r.clicks));
        // in-bounds control: the SAME rig logic clicks when inside
        uint32_t c = r.button(0, 0, 100, 100);
        r.dispatcher.dispatch(c, {framework::TouchAction::DOWN, 50, 50});
        r.dispatcher.dispatch(c, {framework::TouchAction::UP, 50, 50});
        r.drain();
        check("I2 mg-149 in-bounds control clicks", r.clicks == 1 &&
              r.last_click == c, "clicks=" + std::to_string(r.clicks));
    }
}

// ── AUDIO ───────────────────────────────────────────────────────────────────
// Build a minimal deterministic RIFF/WAVE (16-bit mono 8 kHz, 0.25 s).
static std::vector<uint8_t> make_wav(int sample_rate, int ms) {
    int n = sample_rate * ms / 1000;
    std::vector<uint8_t> w;
    auto put = [&w](const char* s, size_t k) { w.insert(w.end(), s, s + k); };
    auto put32 = [&w](uint32_t v) { w.push_back(v & 0xFF); w.push_back((v >> 8) & 0xFF);
        w.push_back((v >> 16) & 0xFF); w.push_back((v >> 24) & 0xFF); };
    auto put16 = [&w](uint16_t v) { w.push_back(v & 0xFF); w.push_back((v >> 8) & 0xFF); };
    put("RIFF", 4); put32(36 + (uint32_t)n * 2); put("WAVE", 4);
    put("fmt ", 4); put32(16); put16(1); put16(1);
    put32(sample_rate); put32(sample_rate * 2); put16(2); put16(16);
    put("data", 4); put32((uint32_t)n * 2);
    for (int i = 0; i < n; ++i) {
        int16_t s = (int16_t)(8000.0 * std::sin(2 * 3.14159265 * 440.0 * i / sample_rate));
        w.push_back(s & 0xFF); w.push_back((s >> 8) & 0xFF);
    }
    return w;
}

static void audio_family() {
    // A3 (MG-233): real container decode
    {
        auto wav = make_wav(8000, 250);
        std::string path = "/tmp/s106_tone.wav";
        FILE* f = fopen(path.c_str(), "wb");
        fwrite(wav.data(), 1, wav.size(), f); fclose(f);
        auto pcm = audio::decode_audio_file(path);
        check("A3 mg-233 wav decodes to pcm", pcm.ok(), pcm.error);
        check("A3 mg-233 rate/channels/duration law",
              pcm.sample_rate == 8000 && pcm.channels == 1 &&
              pcm.duration_sec > 0.24 && pcm.duration_sec < 0.26,
              "rate=" + std::to_string(pcm.sample_rate) +
              " dur=" + std::to_string(pcm.duration_sec));
        // A1/A2 need a file too.
        // A1 (MG-232): MediaPlayer transition table
        {
            audio::MediaPlayer mp;
            bool init = mp.state() == audio::MpState::IDLE;
            bool ds = mp.set_data_source(path);
            bool prepared = mp.prepare();
            bool started = mp.start();
            bool running = mp.state() == audio::MpState::STARTED;
            auto after = mp.advance_clock_msec(300);
            check("A1 mg-232 idle→initialized→prepared→started",
                  init && ds && prepared && started && running,
                  "setds=" + std::to_string(ds) +
                  " prep=" + std::to_string(prepared));
            check("A1 mg-232 playhead completes once",
                  after == audio::MpState::PLAYBACK_COMPLETED,
                  audio::mp_state_name(after));
            // illegal transition law: start() from IDLE is ERROR
            audio::MediaPlayer bad;
            bool illegal = !bad.start() || bad.state() == audio::MpState::ERROR;
            check("A1 mg-232 illegal transition flagged", illegal, "");
        }
        // A2 (MG-231): SoundPool load→play
        {
            audio::SoundPool sp;
            int sid = sp.load(path);
            bool loaded = sid > 0 && sp.is_sample_loaded(sid);
            int stream = sp.play(sid);
            bool playing = stream > 0 &&
                           sp.stream_state(stream) == audio::SpStreamState::PLAYING;
            check("A2 mg-231 load→sample loaded", loaded,
                  "sid=" + std::to_string(sid));
            check("A2 mg-231 play→stream playing", playing,
                  "stream=" + std::to_string(stream));
            sp.stop(stream);
            check("A2 mg-231 stop→stream stopped",
                  sp.stream_state(stream) == audio::SpStreamState::STOPPED, "");
        }
    }
}

int main() {
    canvas_family();
    input_family();
    audio_family();
    std::printf("s106 canvas/input/audio laws %s %d/%d\n",
                g_fail == 0 ? "PASS" : "FAIL", g_pass, g_pass + g_fail);
    return g_fail == 0 ? 0 : 1;
}
