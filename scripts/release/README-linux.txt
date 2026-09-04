MiniAndroid __VERSION__ (Linux x64)

Run an APK:
  ./run-miniandroid.sh run /path/to/app.apk -o ./out -v

Real-APK execution proof (the included demo app changes its counter, box
position, box color and status text on every click; every click is real
DEX bytecode dispatched through the runtime):
  ./run-miniandroid.sh run miniandroid-demo.apk -o ./proof --click-count 8
  # -> proof/frames/frame_000..008.png + proof/frames/manifest.json

Reproducibility: every frame PNG carries a SHA256 in proof/frames/manifest.json.
Re-running the command above reproduces byte-identical frames (deterministic
software renderer, no GPU, no clock-dependent rendering).

Requirements: x86-64 Linux, glibc >= 2.38, libstdc++ (GCC 13),
libpng16, libjpeg.62, libwebp7, zlib1g — standard on most desktops.
No JVM, no GPU, no KVM. Full source and build instructions:
https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime
