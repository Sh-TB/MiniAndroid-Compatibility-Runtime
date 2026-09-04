/*
 * UNIFIED_007 — Real audio subsystem.
 *
 * AOSP-faithful audio state machines + REAL decoding:
 *   - MediaPlayer: IDLE → INITIALIZED → PREPARED → STARTED ⇄ PAUSED,
 *                  STOPPED, PLAYBACK_COMPLETED → (seekTo+start) — with the
 *                  exact AOSP legal-transition table and error states.
 *   - SoundPool:   sample load → play → stream lifecycle.
 *   - AudioTrack:  static/stream PCM write → PLAYING → STOPPED (drained).
 *
 * Decoding uses REAL codecs (no synthetic sine stand-ins at decode level):
 *   MP3  → libmpg123 (1.32)
 *   WAV/OGG/FLAC → libsndfile (1.2)
 * PLAYBACK_COMPLETED is fired position-accurately: when the playhead
 * crosses the decoded duration the state flips to PLAYBACK_COMPLETED and
 * the OnCompletionListener hook is invoked — the state machine bug named
 * by the master request is fixed HERE at state level, provable by test.
 */

#ifndef MINIANDROID_AUDIO_ENGINE_H
#define MINIANDROID_AUDIO_ENGINE_H

#include <cstdint>
#include <string>
#include <vector>
#include <functional>
#include <unordered_map>

namespace miniandroid {
namespace audio {

// ---------------------------------------------------------------------------
// Decoded PCM buffer
// ---------------------------------------------------------------------------
struct DecodedPcm {
    std::vector<int16_t> samples;   // interleaved
    int sample_rate = 0;
    int channels = 0;
    double duration_sec = 0.0;
    std::string error;
    bool ok() const { return !samples.empty() && sample_rate > 0 && channels > 0; }
};

// Decode any supported container (mp3 via mpg123; wav/ogg/flac via sndfile).
DecodedPcm decode_audio_file(const std::string& path);

// ---------------------------------------------------------------------------
// MediaPlayer — AOSP state machine
// ---------------------------------------------------------------------------
enum class MpState {
    IDLE,                // after construction
    INITIALIZED,         // after setDataSource
    PREPARED,            // after prepare()
    STARTED,             // after start()
    PAUSED,              // after pause()
    STOPPED,             // after stop()
    PLAYBACK_COMPLETED,  // playhead reached duration
    RELEASED,            // after release()
    ERROR                // illegal transition attempted
};

const char* mp_state_name(MpState s);

class MediaPlayer {
public:
    MediaPlayer();

    bool set_data_source(const std::string& path);
    bool prepare();
    bool start();
    bool pause();
    bool stop();
    bool seek_to(int64_t msec);
    void release();
    void reset();

    // Playback clock: advance by delta ms. Fires PLAYBACK_COMPLETED exactly
    // once per pass when position >= duration (and runs the listener).
    MpState advance_clock_msec(int64_t delta_ms);

    MpState state() const { return state_; }
    int64_t position_msec() const { return position_ms_; }
    int64_t duration_msec() const { return duration_ms_; }

    std::function<void()> on_completion;

    struct TransitionRecord {
        MpState from, to;
        bool legal;
        std::string method;
    };
    const std::vector<TransitionRecord>& transitions() const { return transitions_; }

private:
    bool transition(MpState next, const char* method, bool legal_path = true);
    MpState state_ = MpState::IDLE;
    int64_t position_ms_ = 0;
    int64_t duration_ms_ = 0;
    DecodedPcm decoded_;
    std::string source_path_;
    std::vector<TransitionRecord> transitions_;
    bool completion_fired_ = false;
};

// ---------------------------------------------------------------------------
// SoundPool — load/play cache semantics
// ---------------------------------------------------------------------------
enum class SpStreamState { NOT_LOADED, LOADED, PLAYING, PAUSED, STOPPED };

class SoundPool {
public:
    int load(const std::string& path);
    bool unload(int sound_id);
    int play(int sound_id, float left_vol = 1.0f, float right_vol = 1.0f,
             int loop = 0, float rate = 1.0f);
    void stop(int stream_id);
    void pause(int stream_id);
    void resume(int stream_id);
    SpStreamState stream_state(int stream_id) const;
    bool is_sample_loaded(int sound_id) const;
    size_t sample_count() const { return samples_.size(); }
private:
    struct Sample { std::string path; DecodedPcm pcm; bool loaded = false; };
    struct Stream { int sound_id; SpStreamState state; };
    std::unordered_map<int, Sample> samples_;
    std::unordered_map<int, Stream> streams_;
    int next_sound_id_ = 1;
    int next_stream_id_ = 1;
};

// ---------------------------------------------------------------------------
// AudioTrack — PCM streaming semantics
// ---------------------------------------------------------------------------
enum class AtState { UNINITIALIZED, INITIALIZED, PLAYING, STOPPED, RELEASED };

class AudioTrack {
public:
    bool init(int sample_rate, int channels);
    size_t write(const int16_t* data, size_t frames);
    bool play();
    bool stop();
    void release();
    AtState state() const { return state_; }
    size_t buffered_frames() const { return buffered_frames_; }
private:
    AtState state_ = AtState::UNINITIALIZED;
    int sample_rate_ = 0, channels_ = 0;
    size_t buffered_frames_ = 0;
};

}  // namespace audio
}  // namespace miniandroid

#endif  // MINIANDROID_AUDIO_ENGINE_H
