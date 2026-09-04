/*
 * UNIFIED_007 — Real audio subsystem implementation.
 * See audio_engine.h for the design contract and AOSP transition table.
 */

#include "audio_engine.h"
// compile with -I src/audio

#include <mpg123.h>
#include <sndfile.h>

#include <cmath>
#include <cstdio>
#include <algorithm>

namespace miniandroid {
namespace audio {

// ---------------------------------------------------------------------------
// decode_audio_file
// ---------------------------------------------------------------------------
static DecodedPcm decode_mp3(const std::string& path) {
    DecodedPcm out;
    mpg123_handle* mh = mpg123_new(nullptr, nullptr);
    if (!mh) { out.error = "mpg123_new failed"; return out; }
    if (mpg123_open(mh, path.c_str()) != MPG123_OK) {
        out.error = "mpg123_open failed: " + path;
        mpg123_delete(mh);
        return out;
    }
    long rate = 0;
    int channels = 0, enc = 0;
    if (mpg123_getformat(mh, &rate, &channels, &enc) != MPG123_OK) {
        out.error = "mpg123_getformat failed";
        mpg123_delete(mh);
        return out;
    }
    mpg123_format_none(mh);
    mpg123_format(mh, rate, channels, MPG123_ENC_SIGNED_16);
    size_t bytes_per_frame = channels * 2;
    std::vector<unsigned char> buf(8192);
    size_t done = 0;
    int res = MPG123_OK;
    while ((res = mpg123_read(mh, buf.data(), buf.size(), &done)) != MPG123_DONE) {
        if (res != MPG123_OK && res != MPG123_NEW_FORMAT) {
            out.error = "mpg123_read failed res=" + std::to_string(res);
            break;
        }
        const int16_t* frames = reinterpret_cast<const int16_t*>(buf.data());
        out.samples.insert(out.samples.end(), frames, frames + done / 2);
    }
    mpg123_close(mh);
    mpg123_delete(mh);
    if (!out.error.empty()) return out;
    out.sample_rate = (int)rate;
    out.channels = channels;
    size_t total_frames = out.samples.size() / channels;
    out.duration_sec = total_frames > 0 ? (double)total_frames / rate : 0.0;
    return out;
}

static DecodedPcm decode_sndfile(const std::string& path) {
    DecodedPcm out;
    SF_INFO info{};
    SNDFILE* f = sf_open(path.c_str(), SFM_READ, &info);
    if (!f) {
        out.error = std::string("sf_open failed: ") + sf_strerror(nullptr);
        return out;
    }
    out.sample_rate = info.samplerate;
    out.channels = info.channels;
    sf_count_t total = info.frames * info.channels;
    out.samples.resize((size_t)total);
    sf_count_t read = sf_read_short(f, out.samples.data(), total);
    sf_close(f);
    if (read != total && read <= 0) {
        out.error = "sf_read_short short read";
        return out;
    }
    out.samples.resize((size_t)read);
    out.duration_sec = info.frames > 0
        ? (double)info.frames / info.samplerate : 0.0;
    return out;
}

DecodedPcm decode_audio_file(const std::string& path) {
    auto ends_with = [](const std::string& s, const std::string& suf) {
        if (s.size() < suf.size()) return false;
        return std::equal(suf.rbegin(), suf.rend(), s.rbegin(),
                          [](char a, char b) {
                              return std::tolower((unsigned char)a) ==
                                     std::tolower((unsigned char)b);
                          });
    };
    if (ends_with(path, ".mp3")) return decode_mp3(path);
    if (ends_with(path, ".wav") || ends_with(path, ".ogg") ||
        ends_with(path, ".flac") || ends_with(path, ".aiff"))
        return decode_sndfile(path);
    // Unknown extension — sniff by content: ID3/0xFFFB → mp3, else sndfile.
    FILE* f = fopen(path.c_str(), "rb");
    if (f) {
        uint8_t hdr[4] = {0};
        size_t n = fread(hdr, 1, 4, f);
        fclose(f);
        if (n >= 3 && hdr[0] == 'I' && hdr[1] == 'D' && hdr[2] == '3')
            return decode_mp3(path);
        if (n >= 2 && hdr[0] == 0xFF && (hdr[1] & 0xE0) == 0xE0)
            return decode_mp3(path);
    }
    return decode_sndfile(path);
}

// ---------------------------------------------------------------------------
// MediaPlayer state machine — AOSP transition table
// ---------------------------------------------------------------------------
const char* mp_state_name(MpState s) {
    switch (s) {
        case MpState::IDLE: return "IDLE";
        case MpState::INITIALIZED: return "INITIALIZED";
        case MpState::PREPARED: return "PREPARED";
        case MpState::STARTED: return "STARTED";
        case MpState::PAUSED: return "PAUSED";
        case MpState::STOPPED: return "STOPPED";
        case MpState::PLAYBACK_COMPLETED: return "PLAYBACK_COMPLETED";
        case MpState::RELEASED: return "RELEASED";
        case MpState::ERROR: return "ERROR";
    }
    return "?";
}

MediaPlayer::MediaPlayer() {
    transitions_.push_back({MpState::IDLE, MpState::IDLE, true, "<init>"});
}

bool MediaPlayer::transition(MpState next, const char* method, bool legal_path) {
    transitions_.push_back({state_, next, legal_path, method});
    if (!legal_path) {
        std::fprintf(stderr, "[AUDIO] ILLEGAL transition %s --%s--> %s\n",
                     mp_state_name(state_), method, mp_state_name(next));
        state_ = MpState::ERROR;
        return false;
    }
    state_ = next;
    return true;
}

bool MediaPlayer::set_data_source(const std::string& path) {
    // Legal from IDLE (and INITIALIZED to re-set? AOSP: IllegalStateException
    // in states other than IDLE).
    if (state_ != MpState::IDLE) {
        transition(MpState::ERROR, "setDataSource", false);
        return false;
    }
    source_path_ = path;
    return transition(MpState::INITIALIZED, "setDataSource");
}

bool MediaPlayer::prepare() {
    if (state_ != MpState::INITIALIZED && state_ != MpState::STOPPED) {
        transition(MpState::ERROR, "prepare", false);
        return false;
    }
    decoded_ = decode_audio_file(source_path_);
    if (!decoded_.ok()) {
        std::fprintf(stderr, "[AUDIO] decode FAILED: %s (%s)\n",
                     decoded_.error.c_str(), source_path_.c_str());
        transition(MpState::ERROR, "prepare", false);
        return false;
    }
    duration_ms_ = (int64_t)(decoded_.duration_sec * 1000.0);
    position_ms_ = 0;
    completion_fired_ = false;
    return transition(MpState::PREPARED, "prepare");
}

bool MediaPlayer::start() {
    // AOSP: legal in PREPARED, STARTED (no-op), PAUSED, PLAYBACK_COMPLETED
    // (with seekTo(0) semantics when combined), STOPPED (requires prepare).
    if (state_ == MpState::STARTED) return true;  // idempotent
    if (state_ == MpState::PREPARED || state_ == MpState::PAUSED) {
        return transition(MpState::STARTED, "start");
    }
    if (state_ == MpState::PLAYBACK_COMPLETED) {
        // AOSP allows start() after completion to replay from position;
        // we replay from 0 (standard user expectation) and re-arm completion.
        position_ms_ = 0;
        completion_fired_ = false;
        return transition(MpState::STARTED, "start-after-completed");
    }
    if (state_ == MpState::STOPPED) {
        // AOSP: must prepare() first — but start() from STOPPED is legal in
        // the state chart (goes through prepare internally per docs figure).
        if (!prepare()) return false;
        return transition(MpState::STARTED, "start-after-stop");
    }
    transition(MpState::ERROR, "start", false);
    return false;
}

bool MediaPlayer::pause() {
    if (state_ == MpState::PAUSED) return true;  // idempotent
    if (state_ == MpState::STARTED) return transition(MpState::PAUSED, "pause");
    transition(MpState::ERROR, "pause", false);
    return false;
}

bool MediaPlayer::stop() {
    if (state_ == MpState::IDLE || state_ == MpState::ERROR) {
        transition(MpState::ERROR, "stop", false);
        return false;
    }
    position_ms_ = 0;
    completion_fired_ = false;
    return transition(MpState::STOPPED, "stop");
}

bool MediaPlayer::seek_to(int64_t msec) {
    // AOSP: legal in PREPARED/PAUSED/STARTED/PLAYBACK_COMPLETED/STOPPED.
    switch (state_) {
        case MpState::PREPARED:
        case MpState::PAUSED:
        case MpState::STARTED:
        case MpState::PLAYBACK_COMPLETED:
        case MpState::STOPPED:
            position_ms_ = std::max<int64_t>(0, std::min(msec, duration_ms_));
            if (state_ == MpState::PLAYBACK_COMPLETED && position_ms_ < duration_ms_) {
                // Seek away from the end re-arms completion.
                completion_fired_ = false;
            }
            return true;
        default:
            transition(MpState::ERROR, "seekTo", false);
            return false;
    }
}

void MediaPlayer::release() {
    transition(MpState::RELEASED, "release");
}

void MediaPlayer::reset() {
    // AOSP: legal in any state → back to IDLE.
    position_ms_ = 0;
    duration_ms_ = 0;
    completion_fired_ = false;
    transitions_.push_back({state_, MpState::IDLE, true, "reset"});
    state_ = MpState::IDLE;
}

MpState MediaPlayer::advance_clock_msec(int64_t delta_ms) {
    if (state_ != MpState::STARTED) return state_;
    position_ms_ += delta_ms;
    if (position_ms_ >= duration_ms_ && duration_ms_ > 0) {
        position_ms_ = duration_ms_;
        if (!completion_fired_) {
            completion_fired_ = true;
            transition(MpState::PLAYBACK_COMPLETED, "playhead>=duration");
            if (on_completion) on_completion();
        }
    }
    return state_;
}

// ---------------------------------------------------------------------------
// SoundPool
// ---------------------------------------------------------------------------
int SoundPool::load(const std::string& path) {
    int id = next_sound_id_++;
    Sample s;
    s.path = path;
    s.pcm = decode_audio_file(path);
    s.loaded = s.pcm.ok();
    if (!s.loaded) {
        std::fprintf(stderr, "[AUDIO] SoundPool load FAILED: %s (%s)\n",
                     s.pcm.error.c_str(), path.c_str());
    }
    samples_[id] = std::move(s);
    return id;
}

bool SoundPool::unload(int sound_id) {
    return samples_.erase(sound_id) > 0;
}

int SoundPool::play(int sound_id, float left_vol, float right_vol,
                    int loop, float rate) {
    auto it = samples_.find(sound_id);
    if (it == samples_.end() || !it->second.loaded) return 0;
    int sid = next_stream_id_++;
    streams_[sid] = {sound_id, SpStreamState::PLAYING};
    (void)left_vol; (void)right_vol; (void)loop; (void)rate;
    return sid;
}

void SoundPool::stop(int stream_id) {
    auto it = streams_.find(stream_id);
    if (it != streams_.end()) it->second.state = SpStreamState::STOPPED;
}

void SoundPool::pause(int stream_id) {
    auto it = streams_.find(stream_id);
    if (it != streams_.end() && it->second.state == SpStreamState::PLAYING)
        it->second.state = SpStreamState::PAUSED;
}

void SoundPool::resume(int stream_id) {
    auto it = streams_.find(stream_id);
    if (it != streams_.end() && it->second.state == SpStreamState::PAUSED)
        it->second.state = SpStreamState::PLAYING;
}

SpStreamState SoundPool::stream_state(int stream_id) const {
    auto it = streams_.find(stream_id);
    return it != streams_.end() ? it->second.state : SpStreamState::STOPPED;
}

bool SoundPool::is_sample_loaded(int sound_id) const {
    auto it = samples_.find(sound_id);
    return it != samples_.end() && it->second.loaded;
}

// ---------------------------------------------------------------------------
// AudioTrack
// ---------------------------------------------------------------------------
bool AudioTrack::init(int sample_rate, int channels) {
    if (sample_rate <= 0 || channels <= 0) return false;
    sample_rate_ = sample_rate;
    channels_ = channels;
    buffered_frames_ = 0;
    state_ = AtState::INITIALIZED;
    return true;
}

size_t AudioTrack::write(const int16_t* data, size_t frames) {
    if (state_ != AtState::INITIALIZED && state_ != AtState::PLAYING) return 0;
    buffered_frames_ += frames;  // streaming sink: bytes accounted, not stored
    if (state_ == AtState::INITIALIZED) state_ = AtState::PLAYING;
    (void)data;
    return frames;
}

bool AudioTrack::play() {
    if (state_ != AtState::INITIALIZED && state_ != AtState::PLAYING) return false;
    state_ = AtState::PLAYING;
    return true;
}

bool AudioTrack::stop() {
    if (state_ != AtState::PLAYING) return false;
    buffered_frames_ = 0;  // drained
    state_ = AtState::STOPPED;
    return true;
}

void AudioTrack::release() {
    state_ = AtState::RELEASED;
}

}  // namespace audio
}  // namespace miniandroid
