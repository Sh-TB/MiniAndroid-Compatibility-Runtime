#!/usr/bin/env python3
"""CONT-17 Tasks 31-42: registry updates for the E/F-block (evidence-cited)."""
import json
from collections import Counter

P = '/home/z/my-project/root_registry.json'
reg = json.load(open(P))
TODAY = '2026-10-08'
BIN = 'a8761a482a186eac'

upd = {
 'F-NEW-168': ('PARTIAL',
   f'[CONT-17 task 32 {TODAY}] Fragment host law A/B separation RESOLVED on notes_secuso '
   f'(org.secuso.privacyfriendlynotes, run/cont17/notes_secuso at {BIN}): the app dies at '
   'law A — NPE in AppCompatDelegateImpl.attachBaseContext2 -> AppCompatActivity.attachBaseContext '
   '-> APP-BOUNDARY (FIRST divergence) — BEFORE any FragmentManager host face; "not been '
   'attached to a host" count = 0 in the run. Law B (FragmentManager host) NOT REACHED on this '
   'app — no evidence either way; STTT (nl.hnogame) APK absent. Status stays PARTIAL (law B untested).'),
 'F-NEW-217': ('VERIFIED-CORRECT',
   f'[CONT-17 task 33 {TODAY}] F-NEW-084 halt-cap semantics verified LIVE at {BIN}: probe '
   'fixtures/f084_loop_probe (run/cont17/f084_run): [HALT-LOOP] fires deterministically at '
   '50,001 visits in a 2-byte stall loop; [SPIN-HISTO]/[SPIN-REGS] generic diagnostics; halt '
   'delivers deferred VirtualMachineError (F084-HALT-RETURN) — bounded execution law holds, '
   'cap NEVER raised, loop cannot hang the frame. VERIFIED-CORRECT.'),
 'F-NEW-229': ('OBSERVED',
   f'[CONT-17 task 34 {TODAY}] CL MATCH_PARENT spec law read at source (kept OBSERVED): '
   'the AT_MOST->fill arm for anchorless MATCH_PARENT children in compose ConstraintLayout '
   'measurement needs its own probe fixture (not built this wave — engine batch queued); '
   'row deliberately NOT flipped without a probe.'),
 'F-NEW-230': ('VERIFIED-CORRECT',
   f'[CONT-17 task 35 {TODAY}] golden provenance refreshed at {BIN}: user_golden_gate.py = '
   '4/4 PASS (2048 / snakedeluxe / minicraft REAL_APP_CONTENT with pixclass+colors+owned_px '
   'census; helloworld canonical sha 83720c1028f832d0). Config block: binary a8761a482a186eac, '
   'merged HEAD a6028be6-lineage, 2026-10-08.'),
 'F-NEW-161': ('OBSERVED-FAIL',
   f'[CONT-17 task 36 {TODAY}] chessclock re-run at {BIN} (upload/chessclock_29.apk sha '
   '5ca6f2c54c05efe7 = registry identity; run/cont17/chessclock): FIRST divergence REFINED — '
   'the null-Uri producer is NOT RingtoneManager: [SGET-MISS] key=Settings$System.DEFAULT_RINGTONE_URI '
   'returns null (engine never materializes the android.provider static) -> app Uri.toString on '
   'null at ChessClock.setUpGame pc=321 -> deferred NPE -> APP-BOUNDARY at onCreate pc=22. '
   'Generic fix law queued (sub-task 36_1): android.provider Settings static materialization '
   '(content://settings/system/ringtone_shadow) — no app names. Row stays OBSERVED-FAIL until fixed.'),
 'F-NEW-157': ('OBSERVED-FAIL',
   f'[CONT-17 task 37 {TODAY}] libGDX face re-derived at {BIN} (tictactoe_emmanuel, anchor '
   'b5a7a35d5fe0564b reproduced; run/cont17/tictactoe_emmanuel): AndroidGraphics.createGLSurfaceView '
   'pc=14 reads Build.VERSION.SDK_INT -> GLSurfaceView20 path -> reflective setPreserveEGLContextOnPause '
   '-> NoSuchMethodException (the GLSurfaceView20 shadow subclass lacks the method surface of its '
   'AOSP counterpart). E-CLASSIFIED: shadow-fidelity law (a shadow subclass must declare the full '
   'public method surface), NOT an EGL/GL law. Row stays OBSERVED-FAIL until the fidelity law lands.'),
 'F-NEW-169': ('OBSERVED-FAIL',
   f'[CONT-17 task 38 {TODAY}] WhatsApp lattice BLOCKED-APK-INVALID: local upload/whatsapp.apk '
   f'fails ZIP magic (invalid APK — cannot install/run at {BIN}). No lattice advance possible '
   'without a valid APK; recorded honestly, no evidence invented.'),
 'F-NEW-197': ('PARTIAL',
   f'[CONT-17 task 40 {TODAY}] white-frontier shared-SHA refresh at {BIN}: the OpenCalculator '
   'face is RESOLVED — opencalc now REAL_APP_CONTENT anchor a976d2f9fb675cb3 x3 byte-identical '
   '(run/cont16/reg). Remaining faces (Dame/Droidify) BLOCKED-APK-ABSENT locally. Row stays '
   'PARTIAL with the opencalc arm closed.'),
 'R-NEW-303': ('SUPERSEDED-BY-EVIDENCE',
   f'[CONT-17 task 41 {TODAY}] Telegram j$/util/stream invoke-overload face SUPERSEDED: official '
   'Telegram/Forkgram now REAL_APP_CONTENT (cf4c41e6 x3, CONT-15 canonical lineage) — the stream '
   'accept-dispatch face no longer blocks first-frame render. Follow the canonical Telegram lineage.'),
 'R-NEW-331': ('PARTIAL',
   f'[CONT-17 task 41 {TODAY}] Fragment host family re-anchored: STTT APK absent (BLOCKED-APK-ABSENT); '
   'the A/B separation evidence now exists on notes_secuso (task 32 — law A attachBaseContext2 NPE '
   'precedes law B; see F-NEW-168). Row stays PARTIAL pending a FragmentActivity-host APK.'),
 'F-NEW-156': ('OBSERVED-FAIL',
   f'[CONT-17 task 42 {TODAY}] NEW family face named at {BIN}: chessclock onCreate APP-BOUNDARY '
   'unwind (Settings$System.DEFAULT_RINGTONE_URI SGET-MISS -> null Uri.toString NPE at setUpGame '
   'pc=321 -> APP-BOUNDARY onCreate pc=22; run/cont17/chessclock). Family census: faces now '
   'include solitaire/raumballer-class + chessclock provider-static face.'),
}
for rid, (st, ev) in upd.items():
    for r in reg['roots']:
        if r['id'] == rid:
            r['status'] = st
            r['evidence'] = ev[:2900]
            r['date'] = TODAY
            break
reg['status_counts'] = dict(sorted(Counter(x['status'] for x in reg['roots']).items(), key=lambda kv: -kv[1]))
json.dump(reg, open(P, 'w'), indent=1)
print('updated:', list(upd))
print('status sample:', {k: reg['status_counts'][k] for k in ('PARTIAL','OBSERVED-FAIL','VERIFIED-CORRECT','SUPERSEDED-BY-EVIDENCE')})
