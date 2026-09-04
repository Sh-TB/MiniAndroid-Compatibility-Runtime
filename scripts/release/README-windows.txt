MiniAndroid __VERSION__ (Windows x64)

Run an APK from a console (cmd.exe or PowerShell):
  MiniAndroid.exe run C:\path\to\app.apk -o out -v

Real-APK execution proof (the included demo app changes its counter, box
position, box color and status text on every click; every click is real
DEX bytecode dispatched through the runtime):
  MiniAndroid.exe run miniandroid-demo.apk -o proof --click-count 8
  # -> proof\frames\frame_000..008.png + proof\frames\manifest.json

The executable is a native PE32+ x86-64 binary. It imports only
KERNEL32.dll and the UCRT (api-ms-win-crt-*) — both ship with every
Windows 10/11 installation. No bundled DLLs are required or included.

Full source and build instructions:
https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime
