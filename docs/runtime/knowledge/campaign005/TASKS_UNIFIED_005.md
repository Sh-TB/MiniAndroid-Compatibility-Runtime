# TASKS_UNIFIED_005.md — MiniAndroid Unified Campaign 005

> numbering continues from 113 (per owner instruction)
> rule: real tools only, evidence-grade terminology, no fabrication.
> NOTE (honesty): Campaign 003/004 artifacts from earlier turns are NOT on the
> current filesystem (lost between sessions). On-disk truth: git 8f0a85b (UNIFIED_002),
> archives 000/001/002 only. Campaign 005 rebuilds from that state. Nothing is
> claimed from the lost sessions unless re-proven here.

## A. MEDIA — MP3/OGG real playback (owner priority: "خیلی مهمه")
- [x] 113  minimp3 (public-domain) vendored + real MP3 decode path        [PASS 33/33 exp113]
- [x] 114  stb_vorbis (public-domain) vendored + real OGG decode path     [PASS]
- [x] 115  android.media.MediaPlayer lifecycle state machine (IDLE→…→STOPPED) [PASS]
- [x] 116  real-time playback timing: wall-clock position, pause freeze, seek+resume [PASS]
- [x] 117  playable WAV artifacts exported from decoded PCM + ffprobe cross-check
       (OGG 5.000000s exact; MP3 3.0563s vs ffprobe 3.0302s = LAME padding) [PASS]
- [x] 118  decode speed 1381x–1617x realtime measured (playback-capable)  [PASS]
- [x] 119  player UI rendered from REAL player state — 2 frames @ pos 400ms/2600ms [PASS]

## B. GAME — tic-tac-toe with real 3D graphics (owner priority)
- [x] 120  pinhole perspective camera (yaw/pitch/dist, focal 1050)         [PASS 16/16 exp114]
- [x] 121  backface culling in view space + per-box painter depth sort
- [x] 122  Lambert shading + depth fog from transformed normals
- [x] 123  minimax AI (perfect X; seeded-random first O reply for decisive result)
- [x] 124  win triple detection + raised win cells rendered
- [x] 125  rotation strip 0/60/120/180/240/300 deg — 6 distinct pixel hashes
       (PROOF: whole scene re-projected = real 3D, not 2D fake)          [PASS]
- [x] 126  full move-by-move frame sequence (intro, 7 moves, final)       [PASS]

## C. CORPUS — lightweight APKs really loading (owner priority: 2–3 apps)
- [x] 127  gmdice.apk run → exit 0 + screenshot.png (real render)          [PROVEN]
- [x] 128  simplestopwatch.apk run → exit 0 + screenshot.png               [PROVEN]
- [x] 129  stopwatch.apk run → PARTIAL SUCCESS (known: 0 activities) + PNG [PROVEN]
- [x] 130  unote.apk run → exit 0 + screenshot.png                         [PROVEN]
- [x] 131  microtimer.apk run → exit 0 + screenshot.png                    [PROVEN]
- [x] 132  notes.apk run → exit 0 + screenshot.png                         [PROVEN]
- [x] 133  tictactoe.apk (real Android game) run → exit 0 + PNG (1s)       [PROVEN]
- [x] 134  dooz.apk (real Persian tic-tac-toe) run → exit 0 + PNG (76s)    [PROVEN]
       HONEST NOTE: corpus UIs render the known default screen (title bar +
       white body) — app UI content needs ARSC/inflation work (task 142).

## D. SOURCE & PACKAGING
- [x] 135  commit EXP-113/114 source (d6b4020)                            [PROVEN]
- [x] 136  docs 113–115 written (media, 3d, campaign report)
- [x] 137  UNIFIED_005.zip built + SHA256 + predecessors 000/001/002 byte-verified
- [x] 138  validation: archive integrity + overclaim scan + numbering monotonic

## E. TELEGRAM FORWARD (carried over; next campaign if batch time allows)
- [ ] 139  re-verify Telegram.apk hash + v12 run reproducibility on current tree
- [ ] 140  EngineClock virtual time (Robolectric-style) to kill 12–27s waits
- [ ] 141  RLottie @RawRes disambiguation completion
- [ ] 142  ARSC string map extension (from 11,314 → full coverage)
- [ ] 143  Uri bridge real-call proof on corpus apps (dyn counts)
- [ ] 144  SystemClock bridge real-call proof on corpus apps
- [ ] 145  sound pool API (SoundPool) bridge on top of EXP-113 decoders
- [ ] 146  AudioTrack streaming bridge (PCM callback)
- [ ] 147  3D renderer: camera animation → multi-frame sprite strip
- [ ] 148  touch input → interactive 3D board (click cell to place)
- …
- [ ] 172  reserve: Campaign 006 planning (numbering from 173)

## STATUS SNAPSHOT (final for this turn)
- executed & closed: 113–138 (26 tasks)
- new bugs found & fixed (buffer rule): 5 —
  1) stb_vorbis `L` macro collision with local symbol (compile failure)
  2) stb_vorbis pull-API wrong signature (short** vs short*)
  3) rotate_x sign inverted → camera rendered board from BELOW
  4) painter's algorithm big-face failure (platform top over far cells) → tiled platform
  5) X-bar / O-ring face winding inverted → backface culling hid visible faces
