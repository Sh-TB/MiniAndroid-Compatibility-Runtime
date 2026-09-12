# DOC 115 — UNIFIED Campaign 005 Executive Report

Date: 2026-08-28 · Base commit: 8f0a85b (UNIFIED_002) → HEAD: d6b4020
Deliverable: UNIFIED_005.zip (this archive)

## 1. Session context (honest)

Campaign 003/004 artifacts referenced in earlier chat turns are NOT on the
current filesystem (sessions were interrupted; intermediate archives
UNIFIED_003/004 and their docs were lost). On-disk truth at campaign start:
git 8f0a85b, archives UNIFIED_000/001/002 only. Campaign 005 therefore
rebuilds from the verified 002 state. Numbering jumps 002 → 005 to match the
owner's campaign counter; the gap is recorded here and nothing from the lost
sessions is claimed unless re-proven below.

## 2. Owner's asks this turn → status

| Owner request («درخواست») | Status | Evidence |
|---|---|---|
| «حداقل یک mp3/ogg پخش کنی خیلی مهمه» | **PROVEN** | EXP-113: 33/33 checks, real decoders, WAV artifacts, 2 UI frames |
| «بازی دوز … حداقل 3D کمی داشته باشه» | **PROVEN** | EXP-114: 16/16 checks, 6-distinct-hash rotation strip, win state rendered |
| «۲-۳ برنامه کم‌حجم رو واقعا لود کن» | **EXECUTED (exit 0)** | 8 corpus APKs ran; screenshots captured; UI content = known default-screen limit |
| «تلگرام رو ببر جلو» | CARRIED | Telegram runs remain from 002 baseline; forward push needs EngineClock/ARSC (tasks 139-144) |
| «ابزارها را واقعاً لود کن» | **PROVEN** | minimp3 + stb_vorbis vendored and EXECUTED inside the runtime; ffmpeg used for inputs; ffprobe used as oracle |
| «بدون خروج زودهنگام / کلی کار ناتموم داری» | honored | buffer rule applied: 5 new bugs found & fixed mid-turn (see §4) |

## 3. New capabilities vs 002 (byte-verified delta)

1. android.media.MediaPlayer bridge with REAL decode (MP3+OGG) — first audio
   capability of the runtime (grep: MediaPlayer/SoundPool/AudioTrack had zero
   matches in src/ before this campaign).
2. Real 3D software rendering path (perspective + culling + painter sort +
   Lambert + fog) — first true-3D rendering capability.
3. Playable audio artifacts + waveform visualization from real PCM.
4. Corpus re-run on current tree: gmdice/simplestopwatch/unote/microtimer/
   notes/tictactoe/dooz exit 0 (+ stopwatch exit 1, known PARTIAL).

## 4. Bugs found & fixed this turn (owner's buffer rule)

1. stb_vorbis `L` macro collided with a local symbol → compile failure → renamed.
2. stb_vorbis pull-API signature misuse (short** vs short* buffer) → fixed.
3. 3D camera: rotate_x sign inverted → board seen from below → fixed.
4. Painter's big-face failure (platform top occluded far cells) → 6x6 tiling.
5. X/O piece face winding inverted → culling hid visible faces → rewound.

## 5. Checks summary (all machine-verified, JSON reports included)

- EXP-113 audio: 33/33 PASS (lifecycle, timing, decode, WAV, UI frames)
- EXP-114 3D: 16/16 PASS (projection, culling, sort, game, rotation hashes)
- ffprobe oracle: OGG exact 5.000000 s; MP3 3.0563 s vs 3.0302 s (+0.9%,
  LAME padding, disclosed); WAVs valid RIFF.

## 6. What MiniAndroid can do NOW that it could not at 002

- You hand it a real .mp3 or .ogg → it decodes to PCM, tracks playback like a
  real MediaPlayer, exports a playable .wav, and draws a player screen with the
  song's actual waveform at the actual playback position.
- It renders a perspective-3D board game with a minimax AI and raised win
  cells, and PROVES the 3D by rotating the camera (6 distinct pixel hashes).

## 7. Next campaign (006, numbering from 173)

Highest-value order per owner priorities: EngineClock virtual time (kill the
12-27 s waits), then ARSC full map (unlock real corpus UIs beyond the default
screen — this is what still makes dooz/tictactoe render blank), then
SoundPool/AudioTrack on top of EXP-113 decoders, then interactive touch input
for the 3D board, then Telegram forward (sign-in chain visuals).
