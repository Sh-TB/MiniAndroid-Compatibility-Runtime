#!/usr/bin/env python3
# cont42_registry.py — CONT-42 registry update: F-NEW-304 (the platform
# FragmentTransaction pending-op law + host-stage fragment lifecycle drain
# + PreferenceFragment content laws — the Fragment/Preference family's
# first slice, the CONT-41 recorded tananaev next-blocker).
import json

P = '/home/z/my-project/root_registry.json'
d = json.load(open(P))
ids = {r.get('id') for r in d['roots']}
assert 'F-NEW-304' not in ids, 'F-NEW-304 already present — dedup check'

entry = {
  "id": "F-NEW-304",
  "title": "Platform FragmentTransaction pending-op law + host-stage fragment lifecycle drain: every Landroid/app/FragmentTransaction op (add/replace/remove/...) was DROPPED at record time (fluent THIS only) and commit()/commitNow() answered 0/void — no platform Fragment ever materialized (tananaev calculator v1.10 MainActivity.onCreate replace(16908290, PrefsFragment).commit(): ContentFrameLayout children=0, verdict DEFAULT_BACKGROUND_ONLY; androidx ReportFragment inject equally silent). AOSP BackStackRecord/FragmentManagerImpl laws: ops record on the transaction heap object (__ftx_n__ + __ftx_<i>_{type,container,frag,tag}__); commit harvests into the FragmentManager queue with a real monotonic BackStackRecord id; the engine drains the queue at the HOST lifecycle windows — CREATED (onAttach(Context)+onCreate per fragment, replace detaches the container's current fragment view), STARTED (onCreateView → app-DEX override or the platform PreferenceFragment list law → onViewCreated → onActivityCreated → onStart; the view attaches into the transaction container node via add_child → requestLayout), RESUMED (onResume). Fragment state getters (getTag/getId/getView/isAdded/getArguments/getActivity/getContext) answer the drain-maintained __frag_*__ fields. PreferenceFragment.addPreferencesFromResource parses the REAL res/xml AXML (ARSC select_file; title/summary/key kinds incl. @string ref resolution) into __pref_*__ rows; the platform onCreateView law builds REAL LinearLayout/TextView rows through the canonical measure laws (no fixed geometry). Standing probe fixtures/frag_tx_probe FT-01..11 (transaction identity, commit id, the full lifecycle ladder, findFragmentByTag identity, isAdded+getView) 4-of-rows+2-dead PRE → 12/0 POST ×3. HONEST BOUNDS: the fragment subtree's final INK under a DEX-measuring parent stays gated — the companion native class-measure law was built and A/B'd (tananaev rows 1080x44 at real pitch, frame 0f649804d6e0486d, rc=0) but DETERMINISTICALLY moved the opencalc golden (a976d2f9 → 0a0b26cf ×3, non-CL nodes too) and is REVERTED pending the opencalc re-baseline decode; tananaev ships with the recorded PARTIAL frame d602648e (lifecycle drains live in-log, tree attached, preference rows parsed 4/4) and the overlay/measure face as the recorded next decode. hide/show/detach/attach ops recorded as the visibility-hop scope boundary.",
  "status": "ROOT_CAUSED_FIXED",
  "priority": "P1",
  "layer": "framework/fragment-host",
  "evidence": "evidence/cont42/FRAGMENT_TX_DRAIN.md",
  "probe": "fixtures/frag_tx_probe (FT-01..11)",
  "friend_note": "friend F-NEW-254/255/256 (Fragment commit drain + addPreferencesFromResource + preference tag mapping) — this entry implements the canonical slice; the friend's fixed-geometry preference rows were rejected as symptom-level per the CONT-41 audit",
  "binary": "0a6e39f38abd8636",
  "regression": "ZERO DRIFT: anchors 24/24 x3 byte-identical; battery == CONT-28..41 records; probes == records (fnew302 48/24 documented); simplecalc x3 rc=0 7960bce447ac6d8f",
}
d['roots'].append(entry)
json.dump(d, open(P, 'w'), indent=1, ensure_ascii=False)
print("registry:", len(d['roots']), "roots; F-NEW-304 appended")
