# S91 SANDBOX SAVE/RESUME — TWO-PROCESS ROUND-TRIP PROOF (2026-09-23)

Fixture: miniandroid/tests/fixtures/s91_resume_probe_data (data-layer probe,
source tracked in-repo; built with scripts/build/build_fixture_apk.sh from
ECJ + android-34 + D8, APK verified by the build script's SHA line).

Command (both runs, IDENTICAL --data-root):
  ./build/miniandroid run --execution-mode real-dalvik --frames 4 \
      --data-root <dir> -o <out> probe2b.apk

RUN 1 (fresh sandbox):  file created with withadd=1 (0+1), const=42, pureadd=8
RUN 2 (same sandbox):   withadd=2, nostatic=1

The app computes `putInt("withadd", readInt("withadd", 0) + 1)`. The value 2
in run 2 can only exist if the second process READ the persisted 1 from
<data-root>/com.miniandroid.s91resume/shared_prefs/resume.xml written by the
first process — the sandbox keeps the save, AOSP SharedPreferencesImpl
contract honored (read-modify-write round trip across process boundaries).

Evidence files:
- run1_after_first_process.xml  (state after run 1)
- run2_after_second_process.xml (state after run 2: withadd=2, nostatic=1)

Known remaining engine gap (F-NEW-195 candidate, open): the s91_resume_probe
STATIC-field face — sget(static) + add-int/lit8 immediately followed by
invoke-interface reads a stale 0 from the value register in this build; the
data layer is unaffected (probe above uses locals). Diagnostics: env-gated
MINIANDROID_F114_DIAG now covers put* argument identity.
