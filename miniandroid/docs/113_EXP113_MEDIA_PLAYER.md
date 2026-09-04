# DOC 113 — EXP-113: Real MP3/OGG Playback (MediaPlayer Bridge)

Campaign: UNIFIED_005 · Date: 2026-08-28 · Commit: d6b4020
Owner priority: «حداقل بتونه یک mp3 ogg پخش کنی خیلی مهمه»

## 1. Claim (evidence-grade)

PROVEN on the current tree (commit d6b4020): the runtime decodes REAL MP3
(minimp3) and REAL OGG Vorbis (stb_vorbis) files into interleaved 16-bit PCM,
implements the android.media.MediaPlayer state machine around them, tracks
playback position in wall-clock time per the Android contract, and materializes
audible output as real playable WAV artifacts (the headless server has NO audio
device — this is recorded honestly; decode runs at 1381x–1617x realtime, so
realtime playback capability is demonstrated by decode throughput).

## 2. New source files

| file | role |
|---|---|
| src/audio/audio_decoders.h/.cpp | real decode (MP3+OGG), WAV writer, waveform RMS |
| src/audio/media_player.h/.cpp    | MediaPlayer lifecycle + position/duration/seek |
| tools/exp113_media_player_demo.cpp | 33-check harness + player UI renderer |

Third-party (vendored, both public-domain):
- third_party/audio/minimp3.h (76,831 B) — https://github.com/lieff/minimp3
- third_party/audio/stb_vorbis.c (192,790 B) — https://github.com/nothings/stb

## 3. Real input media (ffmpeg-generated, real encoded files)

- tone_440.mp3 — 440 Hz sine, 3 s, libmp3lame 128 kbps, 44100 Hz mono
- melody.ogg — C5→E5→G5 sequence, 5 s, libvorbis q4, 44100 Hz mono

## 4. Proof points (all 33/33 checks PASS, exit 0)

Lifecycle (both formats, per Android state diagram):
setDataSource→INITIALIZED, prepare→PREPARED (real decode inside), start→STARTED,
isPlaying=true, pause→PAUSED with FROZEN position (verified over a real 250 ms
wait: identical ms), seekTo clamped, resume, stop→STOPPED.

Timing (wall-clock, per Android contract):
position 0 at PREPARED; after a real 400 ms sleep position ∈ [330,470] ms;
after seekTo(2400)+200 ms the position advanced accordingly. UI frames rendered
at REAL positions 400 ms (frame A) and 2600 ms (frame B) — positions differ,
progress bar + waveform fill reflect each frame's own position.

Decode quality (independent oracle = ffprobe):
- OGG: decoded duration 5.000000 s — EXACT match with ffprobe format duration.
- MP3: decoded 3.0563 s vs ffprobe 3.0302 s (+0.9%) — expected LAME/MP3
  encoder delay padding (no gapless metadata consumed); sample rate 44100 and
  mono match exactly.
- WAV artifacts: tone_440.wav 269,612 B; melody.wav 441,044 B (44-byte header +
  16-bit PCM); both ffprobe-readable as valid RIFF/WAVE. These ARE the audible
  deliverable — copy them to any player and they play.

Speed: 1381.7x realtime (MP3), 1617.1x realtime (OGG) — single thread.

## 5. Graphical evidence

- run_exp005/media/exp113_frame_A.png / exp113_frame_B.png (1080x1920):
  dark-theme player UI with REAL waveform of the decoded PCM (the 440 Hz tone
  with its fade-in/out envelope is visibly drawn from actual samples),
  progress bar at each frame's true position, format chip
  ("MP3 - MPEG Layer III, 128 kbps"), state chip STARTED.
- run_exp005/media/audio_report.json — every measured value + 33 checks.

## 6. Honesty boundaries

- NO audio output device exists on this headless server: "playback" = wall-clock
  position tracking + decode-faster-than-realtime + playable WAV artifacts.
  Claiming ALSA/ PulseAudio output would be fabrication; it is NOT claimed.
- MP3 duration +0.9% vs ffprobe: decoder-level encoder-padding artifact,
  recorded openly, not hidden.
