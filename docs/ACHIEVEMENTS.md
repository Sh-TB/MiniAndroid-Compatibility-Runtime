# MiniAndroid — Canonical App / Game Achievements

> **S84/S85 law:** ONE record per title. This file is the
> authoritative per-title achievement reference, generated from
> `docs/evidence/canonical/registry.json`. One title → one
> canonical screenshot (interactive titles → one GIF). Screenshots
> are never copied across documents — other files link here and to
> the canonical artifact.

> **147 titles** (86 games · 60 apps · 1 fixtures). Wave history (pre-S84 narrative) is preserved in [docs/history/ACHIEVEMENTS_WAVE_HISTORY.md](history/ACHIEVEMENTS_WAVE_HISTORY.md).

> Chain per title: `Title → Source → APK+SHA → Execution session → Achievement → ONE canonical screenshot → root cause/issue`.


## Apps

### at.techbee.jtx

* **Package / identity:** `at.techbee.jtx` · type: app · version: 2.17.00.ose
* **Source:** [F-Droid page](https://f-droid.org/en/packages/at.techbee.jtx/) · [upstream source](https://github.com/TechbeeAT/jtxBoard)
* **APK SHA256:** `92fbd67fd935b52b…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** none — clean run at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Lnet/fortuna/ical4j/model/TimeZoneRegistryFactory;.cr
* **Notes:** S85 NEW-50 (app); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### Bnyro Clock

* **Package / identity:** `com.bnyro.clock` · type: app · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 · status: **OBSERVED** · rendering: L2_GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=False · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran / near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (apps__com.bnyro.clock_24__L2_GRAPHICALLY_INCOMPLETE.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

### Chess Clock

* **Package / identity:** `com.chessclock.android` · type: app · version: —
* **Source:** F-Droid
* **APK SHA256:** `5ca6f2c54c05efe7…`
* **Sessions:** S83 · status: **VERIFIED** · rendering: L0_LOADED_ONLY
* **Execution evidence:** launched=True · rendered=False · interacted=False · state_changed=False
* **Canonical screenshot:** [com.chessclock.android.jpg](evidence/canonical/com.chessclock.android.jpg) · SHA256 `c3209486dd0ab332…`
* **Root cause / law:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** graphics completeness beyond L3
* **Last success / first divergence:** full lifecycle + real frames (S83) / none recorded in S83 session
* **Notes:** S83 real-screenshot campaign evidence (apps__com.chessclock.android_29__L0_LOADED_ONLY.jpg)

### com.aurora.store

* **Package / identity:** `com.aurora.store` · type: app · version: 4.8.4
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.aurora.store/) · [upstream source](https://gitlab.com/AuroraOSS/AuroraStore)
* **APK SHA256:** `fd9c75d90d0f4a7c…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L1 / [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Ljava/lang/Object;.getClass' on a null object referen
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.beemdevelopment.aegis

* **Package / identity:** `com.beemdevelopment.aegis` · type: app · version: 3.4.3
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.beemdevelopment.aegis/) · [upstream source](https://github.com/beemdevelopment/Aegis)
* **APK SHA256:** `0eecec45de0da3ff…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-162 (OPEN, fan-out): androidx lifecycle/savedstate generated adapter + ExternalSyntheticLambda gaps → deferred unwind PARTIAL.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L1 / [SYNTH-EXC] R350-FORNAME (deferred): Ljava/lang/ClassNotFoundException; (kotlin.reflect.jvm.internal.ReflectionFactoryImpl) method=Lkotlin/jvm/internal/Reflecti
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.drdisagree.colorblendr

* **Package / identity:** `com.drdisagree.colorblendr` · type: app · version: v3.0.1
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.drdisagree.colorblendr/) · [upstream source](https://github.com/Mahmud0808/ColorBlendr)
* **APK SHA256:** `a30ea8f14ea9d634…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Ljava/lang/String;.split' on a null object reference)
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.forrestguice.suntimeswidget

* **Package / identity:** `com.forrestguice.suntimeswidget` · type: app · version: 0.17.5
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.forrestguice.suntimeswidget/) · [upstream source](https://github.com/forrestguice/SuntimesWidget)
* **APK SHA256:** `bd0fbe51f684895d…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** none (rc=0)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** full app-specific behavior beyond click probe
* **Last success / first divergence:** 8/8 frames captured, click pass executed / none
* **Notes:** S84 NEW title. rc_obs=0 errors=0 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.fsck.k9

* **Package / identity:** `com.fsck.k9` · type: app · version: 23.0
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.fsck.k9/) · [upstream source](https://github.com/thunderbird/thunderbird-android)
* **APK SHA256:** `92cd3a81c7a8d066…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-162 (OPEN, fan-out): androidx lifecycle/savedstate generated adapter + ExternalSyntheticLambda gaps → deferred unwind PARTIAL.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / [SYNTH-EXC] R350-FORNAME (deferred): Ljava/lang/ClassNotFoundException; (kotlin.reflect.jvm.internal.ReflectionFactoryImpl) method=Lkotlin/jvm/internal/Reflecti
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.gh4a

* **Package / identity:** `com.gh4a` · type: app · version: 4.6.15
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.gh4a/) · [upstream source](https://github.com/slapperwan/gh4a)
* **APK SHA256:** `66711fd47c0c0e65…`
* **Sessions:** S85 · status: **VERIFIED** · rendering: GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** [com.gh4a.jpg](evidence/canonical/com.gh4a.jpg) · SHA256 `29a8df4536d8222e…`
* **Root cause / law:** F-NEW-162 (OPEN, fan-out): androidx lifecycle/savedstate generated adapter + ExternalSyntheticLambda gaps → deferred unwind PARTIAL.
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** state-change evidence
* **Last success / first divergence:** obs 8 frames @L2 / [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke interface method 'Landroid/content/SharedPreferences$Editor;.remove' 
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1

### com.hegocre.nextcloudpasswords

* **Package / identity:** `com.hegocre.nextcloudpasswords` · type: app · version: 1.2.1
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.hegocre.nextcloudpasswords/) · [upstream source](https://github.com/hegocre/NextcloudPasswords)
* **APK SHA256:** `b8ee43950d3fd847…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=False · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope).
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed / first uncaught in-flight exception (see run/s84/com.hegocre.nextcloudpasswords/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=5 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.hfut.schedule

* **Package / identity:** `com.hfut.schedule` · type: app · version: 4.21.1
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.hfut.schedule/) · [upstream source](https://github.com/Chiu-xaH/HFUT-Schedule)
* **APK SHA256:** `bc2b586a58bd6eba…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: NONBLANK
* **Execution evidence:** launched=False · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope).
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed / first uncaught in-flight exception (see run/s84/com.hfut.schedule/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=32 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.034 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.jherkenhoff.qalculate

* **Package / identity:** `com.jherkenhoff.qalculate` · type: app · version: 0.2.1
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.jherkenhoff.qalculate/) · [upstream source](https://github.com/jherkenhoff/qalculate-android)
* **APK SHA256:** `31366f4dd3e750e5…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: NONBLANK
* **Execution evidence:** launched=False · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope).
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed / first uncaught in-flight exception (see run/s84/com.jherkenhoff.qalculate/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=32 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.007 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.justdeax.composeStopwatch

* **Package / identity:** `com.justdeax.composeStopwatch` · type: app · version: 1.9.1
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.justdeax.composeStopwatch/) · [upstream source](https://github.com/JustDeax/ComposeStopwatch)
* **APK SHA256:** `dbf937ebbe7c0b3d…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: NONBLANK
* **Execution evidence:** launched=False · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope).
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed / first uncaught in-flight exception (see run/s84/com.justdeax.composeStopwatch/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=5 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.034 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.kompact

* **Package / identity:** `com.kompact` · type: app · version: 2.0.0
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.kompact/) · [upstream source](https://git.naxod.com/luca/Kompact)
* **APK SHA256:** `9aacd0015ccd9aad…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=False · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope).
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed / first uncaught in-flight exception (see run/s84/com.kompact/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=11 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.kunzisoft.keepass.libre

* **Package / identity:** `com.kunzisoft.keepass.libre` · type: app · version: 4.5.4
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.kunzisoft.keepass.libre/) · [upstream source](https://github.com/Kunzisoft/KeePassDX)
* **APK SHA256:** `862f87a30baef061…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-162 (OPEN, fan-out): androidx lifecycle/savedstate generated adapter + ExternalSyntheticLambda gaps → deferred unwind PARTIAL.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / [SYNTH-EXC] R350-FORNAME (deferred): Ljava/lang/ClassNotFoundException; (kotlin.reflect.jvm.internal.ReflectionFactoryImpl) method=Lkotlin/jvm/internal/Reflecti
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.ma.tehro

* **Package / identity:** `com.ma.tehro` · type: app · version: 1.5.0
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.ma.tehro/) · [upstream source](https://github.com/mosayeb-a/tehran-metro)
* **APK SHA256:** `f5dbd2a88dfe9e64…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: NONBLANK
* **Execution evidence:** launched=False · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope).
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed / first uncaught in-flight exception (see run/s84/com.ma.tehro/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=3 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.007 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.maltaisn.notes.sync

* **Package / identity:** `com.maltaisn.notes.sync` · type: app · version: 1.6.2
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.maltaisn.notes.sync/) · [upstream source](https://github.com/maltaisn/another-notes-app/)
* **APK SHA256:** `176deff1189734d0…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / [SYNTH-EXC] R350-FORNAME (deferred): Ljava/lang/ClassNotFoundException; (kotlin.reflect.jvm.internal.ReflectionFactoryImpl) method=Lx2/r;.<clinit> pc=3 → deferr
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.nononsenseapps.notepad

* **Package / identity:** `com.nononsenseapps.notepad` · type: app · version: 7.2.6
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.nononsenseapps.notepad/) · [upstream source](https://github.com/spacecowboy/NotePad)
* **APK SHA256:** `ed44d7aff78498a5…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: LOADED_ONLY
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-162 (OPEN, fan-out): androidx lifecycle/savedstate generated adapter + ExternalSyntheticLambda gaps → deferred unwind PARTIAL.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L0 / [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke interface method 'Ljava/util/List;.contains' on a null object referen
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.sebiai.glyphport

* **Package / identity:** `com.sebiai.glyphport` · type: app · version: 2.0.3
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.sebiai.glyphport/) · [upstream source](https://github.com/SebiAi/GlyphPort)
* **APK SHA256:** `c95f8ca470b565fc…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L1 / [SYNTH-EXC] R350-FORNAME (deferred): Ljava/lang/ClassNotFoundException; (kotlin.reflect.jvm.internal.ReflectionFactoryImpl) method=Lw5/t;.<clinit> pc=3 → deferr
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.trianguloy.urlchecker

* **Package / identity:** `com.trianguloy.urlchecker` · type: app · version: 3.5
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.trianguloy.urlchecker/) · [upstream source](https://github.com/TrianguloY/UrlChecker)
* **APK SHA256:** `ddcbf344519bff30…`
* **Sessions:** S85 · status: **VERIFIED-INTERACTIVE** · rendering: GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=True · interacted=True · state_changed=True
* **Canonical screenshot:** [com.trianguloy.urlchecker.gif](evidence/canonical/com.trianguloy.urlchecker.gif) · SHA256 `ba1ae97c8e92dcf6…`
* **Root cause / law:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented.
* **Proven exactly:** LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED
* **Remaining:** compose/runtime init (see root cause)
* **Last success / first divergence:** obs 8 frames @L2 / [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Lorg/json/JSONObject;.put' on a null object reference
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1; probed=6; engine_state_changed=6

### com.vagujhelyigergely.calculatorm3

* **Package / identity:** `com.vagujhelyigergely.calculatorm3` · type: app · version: 1.5.2
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.vagujhelyigergely.calculatorm3/) · [upstream source](https://github.com/gergelyvagujhelyi/CalculatorM3)
* **APK SHA256:** `b224f071f7d34f76…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: NONBLANK
* **Execution evidence:** launched=False · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | 
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed / first uncaught in-flight exception (see run/s84/com.vagujhelyigergely.calculatorm3/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=0 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.007 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.vayunmathur.clock

* **Package / identity:** `com.vayunmathur.clock` · type: app · version: v2.6.4
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.vayunmathur.clock/) · [upstream source](https://github.com/vayun-mathur/Modern-Apps)
* **APK SHA256:** `143f8f7437486434…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=False · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope).
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed / first uncaught in-flight exception (see run/s84/com.vayunmathur.clock/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=11 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### de.danoeh.antennapod

* **Package / identity:** `de.danoeh.antennapod` · type: app · version: 3.12.2
* **Source:** [F-Droid page](https://f-droid.org/en/packages/de.danoeh.antennapod/) · [upstream source](https://github.com/AntennaPod/AntennaPod)
* **APK SHA256:** `3f43a4337a693cdb…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-162 (OPEN, fan-out): androidx lifecycle/savedstate generated adapter + ExternalSyntheticLambda gaps → deferred unwind PARTIAL.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / [SYNTH-EXC] R350-FORNAME (deferred): Ljava/lang/ClassNotFoundException; (android.os.Looper) method=Lorg/greenrobot/eventbus/android/AndroidDependenciesDetector;
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### de.markusfisch.android.binaryeye

* **Package / identity:** `de.markusfisch.android.binaryeye` · type: app · version: 1.75.4
* **Source:** [F-Droid page](https://f-droid.org/en/packages/de.markusfisch.android.binaryeye/) · [upstream source](https://github.com/markusfisch/BinaryEye)
* **APK SHA256:** `428c26249c706bd7…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Landroid/content/res/TypedArray;.hasValue' on a null 
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### de.schildbach.wallet

* **Package / identity:** `de.schildbach.wallet` · type: app · version: 11.03
* **Source:** [F-Droid page](https://f-droid.org/en/packages/de.schildbach.wallet/) · [upstream source](https://gitlab.com/bitcoin-wallet/bitcoin-wallet)
* **APK SHA256:** `bc6d078854a74281…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-162 (OPEN, fan-out): androidx lifecycle/savedstate generated adapter + ExternalSyntheticLambda gaps → deferred unwind PARTIAL.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Ljava/util/ServiceLoader;.iterator' on a null object 
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### de.seemoo.at_tracking_detection

* **Package / identity:** `de.seemoo.at_tracking_detection` · type: app · version: 3.1.2
* **Source:** [F-Droid page](https://f-droid.org/en/packages/de.seemoo.at_tracking_detection/) · [upstream source](https://github.com/seemoo-lab/AirGuard)
* **APK SHA256:** `583fc839caff840e…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=False · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope).
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed / first uncaught in-flight exception (see run/s84/de.seemoo.at_tracking_detection/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=20 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### de.taz.android.app.free

* **Package / identity:** `de.taz.android.app.free` · type: app · version: 2.1.2
* **Source:** [F-Droid page](https://f-droid.org/en/packages/de.taz.android.app.free/) · [upstream source](https://github.com/die-tageszeitung/taz-neo)
* **APK SHA256:** `86f14e1101e7f989…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=False · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope).
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed / first uncaught in-flight exception (see run/s84/de.taz.android.app.free/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=32 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### DeskClock

* **Package / identity:** `com.best.deskclock` · type: app · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 · status: **OBSERVED** · rendering: L2_GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=False · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran / near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (apps__com.best.deskclock_2036__L2_GRAPHICALLY_INCOMPLETE.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

### dev.lexip.hecate

* **Package / identity:** `dev.lexip.hecate` · type: app · version: 2.5.1
* **Source:** [F-Droid page](https://f-droid.org/en/packages/dev.lexip.hecate/) · [upstream source](https://github.com/xLexip/Adaptive-Theme)
* **APK SHA256:** `7e98bf1cf2a9e4a4…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L1 / [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Ljava/lang/Object;.getClass' on a null object referen
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### eu.faircode.email

* **Package / identity:** `eu.faircode.email` · type: app · version: 1.2337
* **Source:** [F-Droid page](https://f-droid.org/en/packages/eu.faircode.email/) · [upstream source](https://github.com/M66B/FairEmail)
* **APK SHA256:** `1e59bd1d82ccdf0a…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Landroid/content/Context;.getFilesDir' on a null obje
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### foehnix.widget

* **Package / identity:** `foehnix.widget` · type: app · version: 4.0
* **Source:** [F-Droid page](https://f-droid.org/en/packages/foehnix.widget/) · [upstream source](https://github.com/dzmanto/foehnix)
* **APK SHA256:** `960913f40cefe5f4…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** none (rc=0)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** full app-specific behavior beyond click probe
* **Last success / first divergence:** 8/8 frames captured, click pass executed / none
* **Notes:** S84 NEW title. rc_obs=0 errors=0 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### fr.corenting.convertisseureurofranc

* **Package / identity:** `fr.corenting.convertisseureurofranc` · type: app · version: 2.19
* **Source:** [F-Droid page](https://f-droid.org/en/packages/fr.corenting.convertisseureurofranc/) · [upstream source](https://github.com/corenting/InflationCalculator)
* **APK SHA256:** `257295104823c970…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=False · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope).
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed / first uncaught in-flight exception (see run/s84/fr.corenting.convertisseureurofranc/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=32 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### GameMasterDice

* **Package / identity:** `de.duenndns.gmdice` · type: app · version: —
* **Source:** F-Droid
* **APK SHA256:** `1621eda11b5dbc0c…`
* **Sessions:** S63/S83 · status: **VERIFIED** · rendering: L2_GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** [de.duenndns.gmdice.jpg](evidence/canonical/de.duenndns.gmdice.jpg) · SHA256 `1f38135926fa07e4…`
* **Root cause / law:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** graphics completeness beyond L3
* **Last success / first divergence:** full lifecycle + real frames (S83) / none recorded in S83 session
* **Notes:** S83 real-screenshot campaign evidence (apps__de.duenndns.gmdice_8__L2_GRAPHICALLY_INCOMPLETE.jpg)

### Heading Calculator

* **Package / identity:** `org.debian.eugen.headingcalculator` · type: app · version: —
* **Source:** F-Droid
* **APK SHA256:** `274ec873098eea51…`
* **Sessions:** S83 · status: **VERIFIED** · rendering: L2_GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** [org.debian.eugen.headingcalculator.jpg](evidence/canonical/org.debian.eugen.headingcalculator.jpg) · SHA256 `4de2a3f8f8b8c429…`
* **Root cause / law:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** graphics completeness beyond L3
* **Last success / first divergence:** full lifecycle + real frames (S83) / none recorded in S83 session
* **Notes:** S83 real-screenshot campaign evidence (apps__org.debian.eugen.headingcalculator_1__L2_GRAPHICALLY_INCOMPLETE.jpg)

### io.github.aoc_normal

* **Package / identity:** `io.github.aoc_normal` · type: app · version: 1.0
* **Source:** [F-Droid page](https://f-droid.org/en/packages/io.github.aoc_normal/) · [upstream source](https://archive.softwareheritage.org/browse/origin/https://github.com/Raidenxd2/always_on_clock_normal/directory/)
* **APK SHA256:** `7d049e2276f0c1ae…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: LOADED_ONLY
* **Execution evidence:** launched=True · rendered=False · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** none (rc=0)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** full app-specific behavior beyond click probe
* **Last success / first divergence:** 8/8 frames captured, click pass executed / none
* **Notes:** S84 NEW title. rc_obs=0 errors=0 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=1 entropy=-0.0 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### it.niedermann.nextcloud.deck

* **Package / identity:** `it.niedermann.nextcloud.deck` · type: app · version: 1.26.3
* **Source:** [F-Droid page](https://f-droid.org/en/packages/it.niedermann.nextcloud.deck/) · [upstream source](https://github.com/stefan-niedermann/nextcloud-deck)
* **APK SHA256:** `e7152b3062658082…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-162 (OPEN, fan-out): androidx lifecycle/savedstate generated adapter + ExternalSyntheticLambda gaps → deferred unwind PARTIAL.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Ljava/util/concurrent/CompletableFuture;.thenAcceptAs
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### me.river.nightbell

* **Package / identity:** `me.river.nightbell` · type: app · version: 3.13.0
* **Source:** [F-Droid page](https://f-droid.org/en/packages/me.river.nightbell/) · [upstream source](https://github.com/riveerxd/nightbell)
* **APK SHA256:** `e4972ad68a155033…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: NONBLANK
* **Execution evidence:** launched=False · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope).
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed / first uncaught in-flight exception (see run/s84/me.river.nightbell/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=23 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.007 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### me.timeto.app

* **Package / identity:** `me.timeto.app` · type: app · version: 2026.09.19
* **Source:** [F-Droid page](https://f-droid.org/en/packages/me.timeto.app/) · [upstream source](https://github.com/Medvedev91/timeto.me)
* **APK SHA256:** `cff24d4b5043e268…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: NONBLANK
* **Execution evidence:** launched=False · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope).
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed / first uncaught in-flight exception (see run/s84/me.timeto.app/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=32 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.007 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### MicroTimer

* **Package / identity:** `dubrowgn.microtimer` · type: app · version: —
* **Source:** F-Droid
* **APK SHA256:** `79c6f730f64886e7…`
* **Sessions:** S83 · status: **VERIFIED** · rendering: L2_GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** [dubrowgn.microtimer.jpg](evidence/canonical/dubrowgn.microtimer.jpg) · SHA256 `060e42e488c0f17e…`
* **Root cause / law:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** graphics completeness beyond L3
* **Last success / first divergence:** full lifecycle + real frames (S83) / none recorded in S83 session
* **Notes:** S83 real-screenshot campaign evidence (apps__dubrowgn.microtimer_8__L2_GRAPHICALLY_INCOMPLETE.jpg)

### NewsBlur

* **Package / identity:** `com.newsblur` · type: app · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 HIGH · status: **OBSERVED** · rendering: L2_GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=False · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran / near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (high__com.newsblur_289__L2_GRAPHICALLY_INCOMPLETE.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

### Notes (billthefarmer)

* **Package / identity:** `org.billthefarmer.notes` · type: app · version: —
* **Source:** F-Droid
* **APK SHA256:** `82cf8bc44c163748…`
* **Sessions:** S83 · status: **VERIFIED** · rendering: L2_GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** [org.billthefarmer.notes.jpg](evidence/canonical/org.billthefarmer.notes.jpg) · SHA256 `c67b0f528032b839…`
* **Root cause / law:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** graphics completeness beyond L3
* **Last success / first divergence:** full lifecycle + real frames (S83) / none recorded in S83 session
* **Notes:** S83 real-screenshot campaign evidence (apps__org.billthefarmer.notes_139__L2_GRAPHICALLY_INCOMPLETE.jpg)

### org.dystopia.email

* **Package / identity:** `org.dystopia.email` · type: app · version: 1.5.4
* **Source:** [F-Droid page](https://f-droid.org/en/packages/org.dystopia.email/) · [upstream source](https://framagit.org/dystopia-project/simple-email)
* **APK SHA256:** `e1545a2f2d3aab4b…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Landroid/content/res/TypedArray;.hasValue' on a null 
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.fossify.clock

* **Package / identity:** `org.fossify.clock` · type: app · version: 1.6.0
* **Source:** [F-Droid page](https://f-droid.org/en/packages/org.fossify.clock/) · [upstream source](https://github.com/FossifyOrg/Clock)
* **APK SHA256:** `43cf9f0ec45f1f1f…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / [SYNTH-EXC] R350-FORNAME (deferred): Ljava/lang/ClassNotFoundException; (org.fossify.clock.App_LifecycleAdapter) method=Landroidx/lifecycle/y;.b pc=113 → deferr
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.fossify.gallery

* **Package / identity:** `org.fossify.gallery` · type: app · version: 1.13.1
* **Source:** [F-Droid page](https://f-droid.org/en/packages/org.fossify.gallery/) · [upstream source](https://github.com/FossifyOrg/Gallery)
* **APK SHA256:** `ae7e699599e81f70…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / [SYNTH-EXC] F084-HALT-RETURN (deferred): Ljava/lang/VirtualMachineError; (F084 interpreter halt in callee (no return value): Infinite loop at PC=0x7 in Loc/w;.r
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.fossify.notes

* **Package / identity:** `org.fossify.notes` · type: app · version: 1.7.0
* **Source:** [F-Droid page](https://f-droid.org/en/packages/org.fossify.notes/) · [upstream source](https://github.com/FossifyOrg/Notes)
* **APK SHA256:** `5a56e0e39cc488e1…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / [SYNTH-EXC] R350-FORNAME (deferred): Ljava/lang/ClassNotFoundException; (kotlin.reflect.jvm.internal.ReflectionFactoryImpl) method=Lu4/w;.<clinit> pc=3 → deferr
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.nitri.opentopo

* **Package / identity:** `org.nitri.opentopo` · type: app · version: 1.38
* **Source:** [F-Droid page](https://f-droid.org/en/packages/org.nitri.opentopo/) · [upstream source](https://github.com/Pygmalion69/OpenTopoMapViewer)
* **APK SHA256:** `0fa0362afc6f8f0c…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=False · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope).
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed / first uncaught in-flight exception (see run/s84/org.nitri.opentopo/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=19 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### org.secuso.privacyfriendlyactivitytracker

* **Package / identity:** `org.secuso.privacyfriendlyactivitytracker` · type: app · version: 3.1.2
* **Source:** [F-Droid page](https://f-droid.org/en/packages/org.secuso.privacyfriendlyactivitytracker/) · [upstream source](https://github.com/SecUSo/privacy-friendly-pedometer)
* **APK SHA256:** `e4041cb724f97f48…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** none — clean run at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / none recorded
* **Notes:** S85 NEW-50 (app); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.secuso.privacyfriendlynotes

* **Package / identity:** `org.secuso.privacyfriendlynotes` · type: app · version: 2.2.2
* **Source:** [F-Droid page](https://f-droid.org/en/packages/org.secuso.privacyfriendlynotes/) · [upstream source](https://github.com/SecUSo/privacy-friendly-notes)
* **APK SHA256:** `71e874f45fa4655f…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** none — clean run at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / none recorded
* **Notes:** S85 NEW-50 (app); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.tasks

* **Package / identity:** `org.tasks` · type: app · version: 15.12
* **Source:** [F-Droid page](https://f-droid.org/en/packages/org.tasks/) · [upstream source](https://github.com/tasks/tasks)
* **APK SHA256:** `ed972cc1cec3456a…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-162 (OPEN, fan-out): androidx lifecycle/savedstate generated adapter + ExternalSyntheticLambda gaps → deferred unwind PARTIAL.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Ljava/util/logging/Logger;.setUseParentHandlers' on a
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.y20k.transistor

* **Package / identity:** `org.y20k.transistor` · type: app · version: 4.3.9
* **Source:** [F-Droid page](https://f-droid.org/en/packages/org.y20k.transistor/) · [upstream source](https://codeberg.org/y20k/transistor)
* **APK SHA256:** `762f4fe86bca8a66…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Ljava/lang/Boolean;.booleanValue' on a null object re
* **Notes:** S85 NEW-50 (app); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### P9 (tube42)

* **Package / identity:** `se.tube42.p9.android` · type: app · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S81/S83 · status: **OBSERVED** · rendering: L2_GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=False · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran / near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (apps__se.tube42.p9.android_11__L2_GRAPHICALLY_INCOMPLETE.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

### PMK-61 Calculator

* **Package / identity:** `com.cax.pmk` · type: app · version: —
* **Source:** source-first build (F-Droid/GitHub) · [upstream source](https://github.com/xvadim/pmk-android)
* **APK SHA256:** `—`
* **Sessions:** S64 · status: **VERIFIED** · rendering: L6
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** [com.cax.pmk.jpg](evidence/canonical/com.cax.pmk.jpg) · SHA256 `245ae472e4b390d1…`
* **Root cause / law:** see session report (S62-S65 spotlight reports)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** session-specific (see report)
* **Last success / first divergence:** see S64 report / see session report
* **Notes:** canonical harvested from docs/evidence/s64_spotlight/pmk_frame0_indicator.png

### Shopping List Calc

* **Package / identity:** `io.github.buildsbyben.shoppinglistcalc` · type: app · version: —
* **Source:** source-first build (F-Droid/GitHub) · [upstream source](https://github.com/buildsbyben/shopping-list-calc)
* **APK SHA256:** `—`
* **Sessions:** S64 · status: **VERIFIED** · rendering: L9
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** [io.github.buildsbyben.shoppinglistcalc.jpg](evidence/canonical/io.github.buildsbyben.shoppinglistcalc.jpg) · SHA256 `57b3ca45c8ff83c6…`
* **Root cause / law:** see session report (S62-S65 spotlight reports)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** session-specific (see report)
* **Last success / first divergence:** see S64 report / see session report
* **Notes:** canonical harvested from docs/evidence/s64_spotlight/sc_after_click.png

### SigGen

* **Package / identity:** `org.billthefarmer.siggen` · type: app · version: —
* **Source:** source-first build (F-Droid/GitHub) · [upstream source](https://github.com/billthefarmer/sig-gen)
* **APK SHA256:** `—`
* **Sessions:** S63 · status: **PARTIAL** · rendering: L5
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** [org.billthefarmer.siggen.jpg](evidence/canonical/org.billthefarmer.siggen.jpg) · SHA256 `338c5a8687d371c2…`
* **Root cause / law:** see session report (S62-S65 spotlight reports)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** session-specific (see report)
* **Last success / first divergence:** see S63 report / see session report
* **Notes:** canonical harvested from docs/evidence/s63_spotlight/siggen_frame0.png

### Simple Stopwatch

* **Package / identity:** `omegacentauri.mobi.simplestopwatch` · type: app · version: —
* **Source:** F-Droid
* **APK SHA256:** `b3ec1a5ec24ce53b…`
* **Sessions:** S64/S83 · status: **VERIFIED** · rendering: L2_GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** [omegacentauri.mobi.simplestopwatch.jpg](evidence/canonical/omegacentauri.mobi.simplestopwatch.jpg) · SHA256 `60c1f2f03ca5d9c6…`
* **Root cause / law:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** graphics completeness beyond L3
* **Last success / first divergence:** full lifecycle + real frames (S83) / none recorded in S83 session
* **Notes:** S83 real-screenshot campaign evidence (apps__omegacentauri.mobi.simplestopwatch_26__L2_GRAPHICALLY_INCOMPLETE.jpg)

### site.leos.apps.lespas

* **Package / identity:** `site.leos.apps.lespas` · type: app · version: 2.11.5
* **Source:** [F-Droid page](https://f-droid.org/en/packages/site.leos.apps.lespas/) · [upstream source](https://github.com/scubajeff/lespas)
* **APK SHA256:** `be129b43f84752e4…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: NONBLANK
* **Execution evidence:** launched=False · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope).
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed / first uncaught in-flight exception (see run/s84/site.leos.apps.lespas/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=14 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.034 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### Telegram

* **Package / identity:** `org.telegram.messenger.web` · type: app · version: 12.10.3 (vc70899)
* **Source:** https://telegram.org/dl/android/apk (official CDN) · [upstream source](https://github.com/DrKLO/Telegram)
* **APK SHA256:** `b6a13e876a8abfde…`
* **Sessions:** S85 (review: EXP-064..071 / MC4 / S74-ops / S85) · status: **OBSERVED** · rendering: L1_NONBLANK
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** Telegram app-init frontier (honest OBSERVED): multi-week native/TLS init chain; S85 divergence moved past S74 j$/stream + FragmentManager to ActionBarLayout.e0 List.isEmpty ×11 + ImageLoader cacheDirs File.isDirectory null ×9 (static-init chains not completed).
* **Proven exactly:** LOADED/LAUNCHED (frames render app shell only)
* **Remaining:** ImageLoader/ActionBarLayout static-init chains; native libs; TLS networking
* **Last success / first divergence:** launch + shell frames (S85) / ImageLoader.<init> pc=310 File.isDirectory null
* **Notes:** User-requested re-review at current HEAD: 10 frames L1 NONBLANK, rc=1, 29 deferred NPEs (ImageLoader cacheDirs File.isDirectory null ×9, ActionBarLayout List.isEmpty ×11). History: EXP-064..071 login UI + page transition; MC4 v12.10.1 parse/launch/themed-window; S74 v12.10.3 engine-default black. SHA matches S74 pin (b6a13e87…).

### tibarj.tranquilstopwatch

* **Package / identity:** `tibarj.tranquilstopwatch` · type: app · version: 1.12.1
* **Source:** [F-Droid page](https://f-droid.org/en/packages/tibarj.tranquilstopwatch/) · [upstream source](https://github.com/tibarj/tranquilstopwatch)
* **APK SHA256:** `7bc31fae5cd2e9d8…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=False · rendered=True · interacted=True · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope).
* **Proven exactly:** LOADED/RENDERED/INTERACTED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed / first uncaught in-flight exception (see run/s84/tibarj.tranquilstopwatch/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=20 frames=8/8 click: probed=2 state_changed=0. unique_colors=2 entropy=0.09 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### TimeLimit

* **Package / identity:** `io.timelimit.android.aosp.direct` · type: app · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 HIGH · status: **OBSERVED** · rendering: L2_GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=False · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran / near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (high__io.timelimit.android.aosp.direct_231__L2_GRAPHICALLY_INCOMPLETE.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

### uNote

* **Package / identity:** `app.varlorg.unote` · type: app · version: —
* **Source:** F-Droid
* **APK SHA256:** `be91103f0e7db443…`
* **Sessions:** S83 · status: **VERIFIED** · rendering: L2_GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** [app.varlorg.unote.jpg](evidence/canonical/app.varlorg.unote.jpg) · SHA256 `0926d80c165221c8…`
* **Root cause / law:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** graphics completeness beyond L3
* **Last success / first divergence:** full lifecycle + real frames (S83) / none recorded in S83 session
* **Notes:** S83 real-screenshot campaign evidence (apps__app.varlorg.unote_30__L2_GRAPHICALLY_INCOMPLETE.jpg)


## Fixtures

### TicTacToe3D self-aware fixture

* **Package / identity:** `org.miniandroid.helloworld` · type: fixture · version: —
* **Source:** source-first build (F-Droid/GitHub) · [upstream source](https://github.com/Applibered/HelloWorldSelfAware)
* **APK SHA256:** `—`
* **Sessions:** S45 · status: **VERIFIED** · rendering: L6
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** [org.miniandroid.helloworld.jpg](evidence/canonical/org.miniandroid.helloworld.jpg) · SHA256 `83720c1028f832d0…`
* **Root cause / law:** see session report (S62-S65 spotlight reports)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** session-specific (see report)
* **Last success / first divergence:** see S45 report / see session report
* **Notes:** canonical harvested from docs/evidence/external_hello_golden


## Games

### 2048

* **Package / identity:** `com.miniandroid.g2048` · type: game · version: —
* **Source:** in-house (games/2048)
* **APK SHA256:** `1b1c602a5f0a2723…`
* **Sessions:** S80/S83 · status: **VERIFIED-INTERACTIVE** · rendering: L2_GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=True · interacted=True · state_changed=True
* **Canonical screenshot:** [com.miniandroid.g2048.gif](evidence/canonical/com.miniandroid.g2048.gif) · SHA256 `d613d30fce792406…`
* **Root cause / law:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean
* **Proven exactly:** LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED
* **Remaining:** graphics completeness beyond L3
* **Last success / first divergence:** full lifecycle + real frames (S83) / none recorded in S83 session
* **Notes:** S83 real-screenshot campaign evidence (games__g2048_v1.0_vc1__L2_GRAPHICALLY_INCOMPLETE.jpg)

### Anuto TD

* **Package / identity:** `ch.logixisland.anuto` · type: game · version: —
* **Source:** source-first build (F-Droid/GitHub) · [upstream source](https://github.com/jogishop/AnutoTD)
* **APK SHA256:** `—`
* **Sessions:** S62+ / S85-sweep(shell at HEAD re-run; S-era canonical retained) · status: **VERIFIED** · rendering: L5
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** [ch.logixisland.anuto.jpg](evidence/canonical/ch.logixisland.anuto.jpg) · SHA256 `f876a103e2eae2f1…`
* **Root cause / law:** see session report (S62-S65 spotlight reports)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** session-specific (see report)
* **Last success / first divergence:** see S62+ report / see session report
* **Notes:** canonical harvested from docs/evidence/s62plus_spotlight/anuto_frame0_after_onDraw.png

### Astroloop

* **Package / identity:** `com.astroloop.game` · type: game · version: —
* **Source:** —
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** no prior root cause — rendered at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) / none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### Balance the Ball

* **Package / identity:** `com.jeffliu.balancetheball` · type: game · version: —
* **Source:** F-Droid
* **APK SHA256:** `6180534b151e4d50…`
* **Sessions:** S83 / S85-sweep(shell at HEAD re-run; S-era canonical retained) · status: **VERIFIED** · rendering: L2_GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** [com.jeffliu.balancetheball.jpg](evidence/canonical/com.jeffliu.balancetheball.jpg) · SHA256 `bfb8f34224084ad4…`
* **Root cause / law:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** graphics completeness beyond L3
* **Last success / first divergence:** full lifecycle + real frames (S83) / none recorded in S83 session
* **Notes:** S83 real-screenshot campaign evidence (games__com.jeffliu.balancetheball_4__L2_GRAPHICALLY_INCOMPLETE.jpg)

### Ball2Box

* **Package / identity:** `com.simondalvai.ball2box` · type: game · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 · status: **OBSERVED** · rendering: L0_LOADED_ONLY
* **Execution evidence:** launched=True · rendered=False · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran / near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (games__com.simondalvai.ball2box_69__L0_LOADED_ONLY.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

### bim.app

* **Package / identity:** `bim.app` · type: game · version: —
* **Source:** —
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** no prior root cause — rendered at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) / none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### Blackjack

* **Package / identity:** `crypto.o0o0o0o0o.games.blackjack` · type: game · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 · status: **OBSERVED** · rendering: L0_LOADED_ONLY
* **Execution evidence:** launched=True · rendered=False · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran / near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (games__crypto.o0o0o0o0o.games.blackjack_4__L0_LOADED_ONLY.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

### Boxcars

* **Package / identity:** `com.rocket9labs.boxcars` · type: game · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 · status: **OBSERVED** · rendering: L1_NONBLANK
* **Execution evidence:** launched=True · rendered=False · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran / near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (games__com.rocket9labs.boxcars_104090__L1_NONBLANK.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

### ca.rmen.nounours

* **Package / identity:** `ca.rmen.nounours` · type: game · version: 3.5.8
* **Source:** [F-Droid page](https://f-droid.org/en/packages/ca.rmen.nounours/) · [upstream source](https://github.com/caarmen/nounours-android)
* **APK SHA256:** `0e7da7b17b63d727…`
* **Sessions:** S84 · status: **VERIFIED-INTERACTIVE** · rendering: GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=False · rendered=True · interacted=True · state_changed=True
* **Canonical screenshot:** [ca.rmen.nounours.gif](evidence/canonical/ca.rmen.nounours.gif) · SHA256 `24a19ed30eda6be3…`
* **Root cause / law:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope).
* **Proven exactly:** LOADED/RENDERED/INTERACTED/STATE_CHANGED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed / first uncaught in-flight exception (see run/s84/ca.rmen.nounours/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=1 frames=8/8 click: probed=1 state_changed=1. unique_colors=2 entropy=0.918 resources(dex/classes)=?

### Chess (jwtc)

* **Package / identity:** `jwtc.android.chess` · type: game · version: —
* **Source:** —
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** no prior root cause — rendered at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) / none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.ahorcado

* **Package / identity:** `com.ahorcado` · type: game · version: 1.5.1
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.ahorcado/) · [upstream source](https://github.com/Webierta/ahorcandroid)
* **APK SHA256:** `7f4df3878508804b…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Landroid/security/NetworkSecurityPolicy;.isCleartextT
* **Notes:** S85 NEW-50 (game); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.clavierhaus.gnubg

* **Package / identity:** `com.clavierhaus.gnubg` · type: game · version: 1.0.2
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.clavierhaus.gnubg/) · [upstream source](https://github.com/clavierhaus/gnubg-android)
* **APK SHA256:** `a951da343ca91f10…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: NONBLANK
* **Execution evidence:** launched=False · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope).
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed / first uncaught in-flight exception (see run/s84/com.clavierhaus.gnubg/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=32 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.034 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.dozingcatsoftware.dodge

* **Package / identity:** `com.dozingcatsoftware.dodge` · type: game · version: 1.5.1
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.dozingcatsoftware.dodge/) · [upstream source](https://github.com/dozingcat/dodge-android)
* **APK SHA256:** `a5687d1bad7b2927…`
* **Sessions:** S84 · status: **VERIFIED-INTERACTIVE** · rendering: GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=False · rendered=True · interacted=True · state_changed=True
* **Canonical screenshot:** [com.dozingcatsoftware.dodge.gif](evidence/canonical/com.dozingcatsoftware.dodge.gif) · SHA256 `3ca88c8da8a90bc3…`
* **Root cause / law:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope).
* **Proven exactly:** LOADED/RENDERED/INTERACTED/STATE_CHANGED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed / first uncaught in-flight exception (see run/s84/com.dozingcatsoftware.dodge/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=4 frames=8/8 click: probed=7 state_changed=6. unique_colors=52 entropy=1.685 resources(dex/classes)=?

### com.galaxyrio.sudokusolver

* **Package / identity:** `com.galaxyrio.sudokusolver` · type: game · version: —
* **Source:** —
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** no prior root cause — rendered at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) / none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.games.boardgames.aeonsend

* **Package / identity:** `com.games.boardgames.aeonsend` · type: game · version: 1.0
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.games.boardgames.aeonsend/) · [upstream source](https://github.com/JanSvoboda/aeonsend-randomizer)
* **APK SHA256:** `9dbd85782b534a58…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: LOADED_ONLY
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** none — clean run at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L0 / [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Lcom/games/boardgames/aeonsend/database/DatabaseHandl
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.github.m374lx.alexvsbus

* **Package / identity:** `com.github.m374lx.alexvsbus` · type: game · version: 2025.06.16.0
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.github.m374lx.alexvsbus/) · [upstream source](https://github.com/M374LX/alexvsbus)
* **APK SHA256:** `ecec13afdae16e9f…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** none — clean run at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / none recorded
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.helddertierwelt.mentalmath

* **Package / identity:** `com.helddertierwelt.mentalmath` · type: game · version: 27
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.helddertierwelt.mentalmath/) · [upstream source](https://codeberg.org/Mental-Math/MentalMath)
* **APK SHA256:** `68af653d1dc0b184…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: NONBLANK
* **Execution evidence:** launched=False · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope).
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed / first uncaught in-flight exception (see run/s84/com.helddertierwelt.mentalmath/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=32 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.034 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.kaeruct.raumballer

* **Package / identity:** `com.kaeruct.raumballer` · type: game · version: 1.2
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.kaeruct.raumballer/) · [upstream source](https://github.com/KaeruCT/RaumBaller)
* **APK SHA256:** `e0eb9a7dfbd82162…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: LOADED_ONLY
* **Execution evidence:** launched=False · rendered=False · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope).
* **Proven exactly:** LOADED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed / first uncaught in-flight exception (see run/s84/com.kaeruct.raumballer/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=1 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=1 entropy=-0.0 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.kingalex.kingpong

* **Package / identity:** `com.kingalex.kingpong` · type: game · version: 1.1.2
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.kingalex.kingpong/) · [upstream source](https://github.com/KingAlexGilbert/king-pong)
* **APK SHA256:** `9545a66697a83c25…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: LOADED_ONLY
* **Execution evidence:** launched=True · rendered=False · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** none (rc=0)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** full app-specific behavior beyond click probe
* **Last success / first divergence:** 8/8 frames captured, click pass executed / none
* **Notes:** S84 NEW title. rc_obs=0 errors=0 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=1 entropy=-0.0 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.mufradat.africaquiz

* **Package / identity:** `com.mufradat.africaquiz` · type: game · version: 1.0
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.mufradat.africaquiz/) · [upstream source](https://codeberg.org/Mufradat/africa-quiz)
* **APK SHA256:** `649282d36bd5c237…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-162 (OPEN, fan-out): androidx lifecycle/savedstate generated adapter + ExternalSyntheticLambda gaps → deferred unwind PARTIAL.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L1 / [SYNTH-EXC] R350-FORNAME (deferred): Ljava/lang/ClassNotFoundException; (androidx.savedstate.Recreator_LifecycleAdapter) method=Landroidx/lifecycle/Lifecycling;
* **Notes:** S85 NEW-50 (game); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.octbit.rutmath

* **Package / identity:** `com.octbit.rutmath` · type: game · version: —
* **Source:** —
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** no prior root cause — rendered at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) / none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.qwde.ccm

* **Package / identity:** `com.qwde.ccm` · type: game · version: —
* **Source:** —
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** no prior root cause — rendered at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) / none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.sanskritbasics.memory

* **Package / identity:** `com.sanskritbasics.memory` · type: game · version: —
* **Source:** —
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** no prior root cause — rendered at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) / none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.serwylo.babydots

* **Package / identity:** `com.serwylo.babydots` · type: game · version: 1.10.0
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.serwylo.babydots/) · [upstream source](https://github.com/babydots/babydots)
* **APK SHA256:** `582d536d0aa435b5…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** none — clean run at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L1 / [SYNTH-EXC] R350-FORNAME (deferred): Ljava/lang/ClassNotFoundException; (kotlin.reflect.jvm.internal.ReflectionFactoryImpl) method=Lkotlin/jvm/internal/Reflecti
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0; probed=1; engine_state_changed=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.sidhant.bubbleshooter

* **Package / identity:** `com.sidhant.bubbleshooter` · type: game · version: —
* **Source:** —
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** no prior root cause — rendered at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) / none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.sidhant.puzzle

* **Package / identity:** `com.sidhant.puzzle` · type: game · version: —
* **Source:** —
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** no prior root cause — rendered at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) / none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.smorgasbork.hotdeath

* **Package / identity:** `com.smorgasbork.hotdeath` · type: game · version: 1.0.11
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.smorgasbork.hotdeath/) · [upstream source](https://github.com/jpriebe/hotdeath)
* **APK SHA256:** `8e6c19ead1795fa5…`
* **Sessions:** S84 · status: **VERIFIED-INTERACTIVE** · rendering: GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=True · interacted=True · state_changed=True
* **Canonical screenshot:** [com.smorgasbork.hotdeath.gif](evidence/canonical/com.smorgasbork.hotdeath.gif) · SHA256 `d6fdff53adfaa6fa…`
* **Root cause / law:** none (rc=0)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED
* **Remaining:** full app-specific behavior beyond click probe
* **Last success / first divergence:** 8/8 frames captured, click pass executed / none
* **Notes:** S84 NEW title. rc_obs=0 errors=0 frames=8/8 click: probed=6 state_changed=3. unique_colors=4 entropy=0.982 resources(dex/classes)=?

### com.towerillusion.abdal

* **Package / identity:** `com.towerillusion.abdal` · type: game · version: 1.0.0
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.towerillusion.abdal/) · [upstream source](https://github.com/towerillusionii/Abstract-Dots-and-Lines)
* **APK SHA256:** `50be6be690faaa59…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-162 (OPEN, fan-out): androidx lifecycle/savedstate generated adapter + ExternalSyntheticLambda gaps → deferred unwind PARTIAL.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Landroid/content/res/AssetManager;.open' on a null ob
* **Notes:** S85 NEW-50 (game); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### com.trianguloy.adnihilation

* **Package / identity:** `com.trianguloy.adnihilation` · type: game · version: 1.0
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.trianguloy.adnihilation/) · [upstream source](https://github.com/TrianguloY/Adnihilation)
* **APK SHA256:** `ae531b495cc39b21…`
* **Sessions:** S85 · status: **VERIFIED** · rendering: GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** [com.trianguloy.adnihilation.jpg](evidence/canonical/com.trianguloy.adnihilation.jpg) · SHA256 `541a877382de1031…`
* **Root cause / law:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented.
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** state-change evidence
* **Last success / first divergence:** obs 8 frames @L2 / [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Landroid/view/View;.getBackground' on a null object r
* **Notes:** S85 NEW-50 (game); rc_obs=1; frames=8; rc_click=1; probed=1; engine_state_changed=0

### com.vayunmathur.games.alchemist

* **Package / identity:** `com.vayunmathur.games.alchemist` · type: game · version: v2.6.5
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.vayunmathur.games.alchemist/) · [upstream source](https://github.com/vayun-mathur/Modern-Apps)
* **APK SHA256:** `88a0ac6f06e9c57f…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: NONBLANK
* **Execution evidence:** launched=False · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope).
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed / first uncaught in-flight exception (see run/s84/com.vayunmathur.games.alchemist/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=15 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.034 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.vovagorodok.blichess

* **Package / identity:** `com.vovagorodok.blichess` · type: game · version: 8.0.0+ble2.5.1
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.vovagorodok.blichess/) · [upstream source](https://github.com/vovagorodok/blichess/)
* **APK SHA256:** `3ae86223a7043951…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: NONBLANK
* **Execution evidence:** launched=False · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope).
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed / first uncaught in-flight exception (see run/s84/com.vovagorodok.blichess/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=2 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.034 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### com.vovagorodok.blidraughts

* **Package / identity:** `com.vovagorodok.blidraughts` · type: game · version: 2.3.0+ble2.5.1
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.vovagorodok.blidraughts/) · [upstream source](https://github.com/vovagorodok/blidraughts/)
* **APK SHA256:** `f7f4582fa24607d8…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: NONBLANK
* **Execution evidence:** launched=False · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope).
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed / first uncaught in-flight exception (see run/s84/com.vovagorodok.blidraughts/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=2 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.034 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### de.georgsieber.ballbreak

* **Package / identity:** `de.georgsieber.ballbreak` · type: game · version: 1.8.1
* **Source:** [F-Droid page](https://f-droid.org/en/packages/de.georgsieber.ballbreak/) · [upstream source](https://github.com/schorschii/ballBreak-Android)
* **APK SHA256:** `e6e9f37293d3aaac…`
* **Sessions:** S84 / S85-sweep(shell at HEAD re-run; S-era canonical retained) · status: **VERIFIED** · rendering: GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** [de.georgsieber.ballbreak.jpg](evidence/canonical/de.georgsieber.ballbreak.jpg) · SHA256 `b3c8930369dfe0b7…`
* **Root cause / law:** none (rc=0)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED/INTERACTED
* **Remaining:** full app-specific behavior beyond click probe
* **Last success / first divergence:** 8/8 frames captured, click pass executed / none
* **Notes:** S84 NEW title. rc_obs=0 errors=0 frames=8/8 click: probed=2 state_changed=0. unique_colors=25 entropy=0.096 resources(dex/classes)=?

### dev.lonami.klooni

* **Package / identity:** `dev.lonami.klooni` · type: game · version: 0.8.6
* **Source:** [F-Droid page](https://f-droid.org/en/packages/dev.lonami.klooni/) · [upstream source](https://codeberg.org/Lonami/Klooni1010)
* **APK SHA256:** `55641cdb5dba7f30…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Lcom/badlogic/gdx/backends/android/AndroidInput;.onRe
* **Notes:** S85 NEW-50 (game); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### Dooz (tic-tac-toe)

* **Package / identity:** `io.github.yamin8000.dooz` · type: game · version: —
* **Source:** F-Droid io.github.yamin8000.dooz
* **APK SHA256:** `d81292cd346dcb23…`
* **Sessions:** S66/S83 · status: **OBSERVED** · rendering: L1_NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** R-NEW-344 family (OPEN): compose WindowRecomposer context chain — app paints a near-blank loading shell (white + tiny header line); R-NEW-403 fixed the pre-frame keySet NPE, recomposer chain is the next dependency.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** graphics completeness beyond L3
* **Last success / first divergence:** full lifecycle + real frames (S83) / none recorded in S83 session
* **Notes:** S85 audit: the restored s83b evidence was a near-blank loading shell (99.9% white) — demoted per S54 gate; no honest UI claim at HEAD.

### eu.quelltext.counting

* **Package / identity:** `eu.quelltext.counting` · type: game · version: 1.3
* **Source:** [F-Droid page](https://f-droid.org/en/packages/eu.quelltext.counting/) · [upstream source](https://gitlab.com/niccokunzmann/12345)
* **APK SHA256:** `98fe65f21ff8e519…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: LOADED_ONLY
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** none — clean run at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L0 / none recorded
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### FireStrike

* **Package / identity:** `com.eightsines.firestrike.opensource` · type: game · version: —
* **Source:** —
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** no prior root cause — rendered at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) / none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### Fish Rings

* **Package / identity:** `eu.veldsoft.fish.rings` · type: game · version: —
* **Source:** source-first build (F-Droid/GitHub) · [upstream source](https://github.com/VelbazhdSoftwareLLC/FishRingsForAndroid)
* **APK SHA256:** `—`
* **Sessions:** S65 · status: **VERIFIED** · rendering: L10
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** [eu.veldsoft.fish.rings.jpg](evidence/canonical/eu.veldsoft.fish.rings.jpg) · SHA256 `28c952a6e1657b02…`
* **Root cause / law:** see session report (S62-S65 spotlight reports)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** session-specific (see report)
* **Last success / first divergence:** see S65 report / see session report
* **Notes:** canonical harvested from docs/evidence/visual_forensics/s65_reval/fishrings/after_tap3_full.png

### FreeKlondike

* **Package / identity:** `eu.veldsoft.free.klondike` · type: game · version: —
* **Source:** source-first build (F-Droid/GitHub) · [upstream source](https://github.com/VelbazhdSoftwareLLC/FreeKlondike)
* **APK SHA256:** `—`
* **Sessions:** S64 · status: **VERIFIED** · rendering: L10
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** [eu.veldsoft.free.klondike.jpg](evidence/canonical/eu.veldsoft.free.klondike.jpg) · SHA256 `7dd689bf2d692980…`
* **Root cause / law:** see session report (S62-S65 spotlight reports)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** session-specific (see report)
* **Last success / first divergence:** see S64 report / see session report
* **Notes:** canonical harvested from docs/evidence/s64_spotlight/fk_game_deal_response.png

### Guandan

* **Package / identity:** `page.codeberg.lanticy.guandan` · type: game · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 · status: **OBSERVED** · rendering: L2_GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=False · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran / near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (games__page.codeberg.lanticy.guandan_7__L2_GRAPHICALLY_INCOMPLETE.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

### Halma

* **Package / identity:** `app.halma` · type: game · version: —
* **Source:** —
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** no prior root cause — rendered at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) / none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### io.github.divverent.aaaaxy

* **Package / identity:** `io.github.divverent.aaaaxy` · type: game · version: 1.7.239+20260804.4198.805e2a0b
* **Source:** [F-Droid page](https://f-droid.org/en/packages/io.github.divverent.aaaaxy/) · [upstream source](https://github.com/divVerent/aaaaxy)
* **APK SHA256:** `976ebc08571af97d…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** none — clean run at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Ljava/lang/String;.equals' on a null object reference
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### io.github.ebraminio.bouncy

* **Package / identity:** `io.github.ebraminio.bouncy` · type: game · version: 0.0.1
* **Source:** [F-Droid page](https://f-droid.org/en/packages/io.github.ebraminio.bouncy/) · [upstream source](https://github.com/ebraminio/bouncy)
* **APK SHA256:** `a509db2afda544f6…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: LOADED_ONLY
* **Execution evidence:** launched=True · rendered=False · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** none (rc=0)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** full app-specific behavior beyond click probe
* **Last success / first divergence:** 8/8 frames captured, click pass executed / none
* **Notes:** S84 NEW title. rc_obs=0 errors=0 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=1 entropy=-0.0 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### io.github.hathibelagal.mykanji

* **Package / identity:** `io.github.hathibelagal.mykanji` · type: game · version: 1.6
* **Source:** [F-Droid page](https://f-droid.org/en/packages/io.github.hathibelagal.mykanji/) · [upstream source](https://github.com/hathibelagal-dev/MyKanji)
* **APK SHA256:** `b20274a0885d03ba…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: LOADED_ONLY
* **Execution evidence:** launched=True · rendered=False · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** none (rc=0)
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** full app-specific behavior beyond click probe
* **Last success / first divergence:** 8/8 frames captured, click pass executed / none
* **Notes:** S84 NEW title. rc_obs=0 errors=0 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=1 entropy=-0.0 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### io.github.johnathan.minesweeper

* **Package / identity:** `io.github.johnathan.minesweeper` · type: game · version: 1.5
* **Source:** [F-Droid page](https://f-droid.org/en/packages/io.github.johnathan.minesweeper/) · [upstream source](https://github.com/john-athan/minesweeper)
* **APK SHA256:** `3b52a2fd21c4b418…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: NONBLANK
* **Execution evidence:** launched=False · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope).
* **Proven exactly:** LOADED/RENDERED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed / first uncaught in-flight exception (see run/s84/io.github.johnathan.minesweeper/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=32 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=3 entropy=0.034 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### io.github.rotundtapir.fivehundred

* **Package / identity:** `io.github.rotundtapir.fivehundred` · type: game · version: 0.6.5
* **Source:** [F-Droid page](https://f-droid.org/en/packages/io.github.rotundtapir.fivehundred/) · [upstream source](https://github.com/rotundtapir/500)
* **APK SHA256:** `db215475793097c0…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-162 (OPEN, fan-out): androidx lifecycle/savedstate generated adapter + ExternalSyntheticLambda gaps → deferred unwind PARTIAL.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L1 / [SYNTH-EXC] R350-FORNAME (deferred): Ljava/lang/ClassNotFoundException; (androidx.savedstate.Recreator_LifecycleAdapter) method=Landroidx/lifecycle/Lifecycling;
* **Notes:** S85 NEW-50 (game); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### io.itch.pirate_solitaire

* **Package / identity:** `io.itch.pirate_solitaire` · type: game · version: 1.3
* **Source:** [F-Droid page](https://f-droid.org/en/packages/io.itch.pirate_solitaire/) · [upstream source](https://github.com/Pheonyxior/Pirate-Solitaire-Git-Repo/tree/master)
* **APK SHA256:** `b9fbe6023d8696b6…`
* **Sessions:** S84 · status: **OBSERVED** · rendering: LOADED_ONLY
* **Execution evidence:** launched=False · rendered=False · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-160 (FIXED this wave, S84 A/B-proven): Class.forName framework bridge — android.os.Build/Build$VERSION CNFE eliminated (9/50 titles hit); bridge restricted to pure-data Build family after foehnix.widget A/B regression proved instantiable artifacts (CloseGuard) must stay on the caught-CNFE path. | F-NEW-161 (OPEN, fan-out family): Compose UI runtime internals — kotlin-reflect forName CNFE (caught, faithful) followed by compose-runtime NPE/ISE (null Iterator in compose runtime setState chain, null View.getWidth in compose layout, IllegalStateException in setContent/onCreate) → ART process-death law PARTIAL. Static UI renders; dynamic compose machinery not implemented (S83-GFX-BASE P4 scope).
* **Proven exactly:** LOADED
* **Remaining:** compose/animation dynamics; deeper interaction
* **Last success / first divergence:** 8/8 frames captured, click pass executed / first uncaught in-flight exception (see run/s84/io.itch.pirate_solitaire/obs_obs.log EXC-PROPAGATE)
* **Notes:** S84 NEW title. rc_obs=1 errors=1 frames=8/8 click: probed=-1 state_changed=-1. unique_colors=1 entropy=-0.0 resources(dex/classes)=? [frame belongs to the shared/near-blank content class — not canonical visual evidence per S54 law]

### ir.hsn6.tpb

* **Package / identity:** `ir.hsn6.tpb` · type: game · version: 1.0.1
* **Source:** [F-Droid page](https://f-droid.org/en/packages/ir.hsn6.tpb/) · [upstream source](https://github.com/HassanHeydariNasab/2-player-battle)
* **APK SHA256:** `37ffc01c030e3d24…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / none recorded
* **Notes:** S85 NEW-50 (game); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### Mancala

* **Package / identity:** `com.willie.mancala` · type: game · version: —
* **Source:** —
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** no prior root cause — rendered at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) / none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### Memory

* **Package / identity:** `eu.quelltext.memory` · type: game · version: —
* **Source:** F-Droid
* **APK SHA256:** `4dd3957983e3c3f3…`
* **Sessions:** S83 · status: **VERIFIED** · rendering: L0_LOADED_ONLY
* **Execution evidence:** launched=True · rendered=False · interacted=False · state_changed=False
* **Canonical screenshot:** [eu.quelltext.memory.jpg](evidence/canonical/eu.quelltext.memory.jpg) · SHA256 `1f36d707ec9f685c…`
* **Root cause / law:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** graphics completeness beyond L3
* **Last success / first divergence:** full lifecycle + real frames (S83) / none recorded in S83 session
* **Notes:** S83 real-screenshot campaign evidence (games__eu.quelltext.memory_7__L0_LOADED_ONLY.jpg)

### Mines (premy)

* **Package / identity:** `cos.premy.mines` · type: game · version: —
* **Source:** F-Droid
* **APK SHA256:** `18faef7028457f4d…`
* **Sessions:** S85-sweep · status: **VERIFIED** · rendering: GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** [cos.premy.mines.jpg](evidence/canonical/cos.premy.mines.jpg) · SHA256 `f73b3c57ca712dd2…`
* **Root cause / law:** VERIFIED
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** interaction + canonical artifact harvest
* **Last success / first divergence:** obs frames @L2 (S85) / none recorded
* **Notes:** S85 sweep promotion: prior VERIFIED → L2 render

### Mini Tetris

* **Package / identity:** `com.miniandroid.tetris` · type: game · version: —
* **Source:** in-house (games/mini-tetris)
* **APK SHA256:** `cb2818dfe6c6cadb…`
* **Sessions:** S80/S83 · status: **VERIFIED-INTERACTIVE** · rendering: L3_STRUCT_CANDIDATE
* **Execution evidence:** launched=True · rendered=True · interacted=True · state_changed=True
* **Canonical screenshot:** [com.miniandroid.tetris.gif](evidence/canonical/com.miniandroid.tetris.gif) · SHA256 `927d966a5a7397a8…`
* **Root cause / law:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean
* **Proven exactly:** LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED
* **Remaining:** graphics completeness beyond L3
* **Last success / first divergence:** full lifecycle + real frames (S83) / none recorded in S83 session
* **Notes:** S83 real-screenshot campaign evidence (games__tetris_v1.0_vc1__L3_STRUCT_CANDIDATE.jpg)

### name.boyle.chris.sgtpuzzles

* **Package / identity:** `name.boyle.chris.sgtpuzzles` · type: game · version: 2025-09-12-1919-23762278-fdroid
* **Source:** [F-Droid page](https://f-droid.org/en/packages/name.boyle.chris.sgtpuzzles/) · [upstream source](https://github.com/chrisboyle/sgtpuzzles)
* **APK SHA256:** `6b36d5537984523c…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** none — clean run at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / none recorded
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### Navy Fleet Battle

* **Package / identity:** `net.tigr.navyfleetbattle` · type: game · version: —
* **Source:** —
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** no prior root cause — rendered at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) / none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### net.sourceforge.solitaire_cg

* **Package / identity:** `net.sourceforge.solitaire_cg` · type: game · version: 4.1
* **Source:** [F-Droid page](https://f-droid.org/en/packages/net.sourceforge.solitaire_cg/) · [upstream source](https://sourceforge.net/p/solitairecg/code)
* **APK SHA256:** `—`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** none — clean run at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Landroid/content/res/Resources;.getDisplayMetrics' on
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### No Thanks!

* **Package / identity:** `eu.veldsoft.no.thanks` · type: game · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 · status: **OBSERVED** · rendering: L1_NONBLANK
* **Execution evidence:** launched=True · rendered=False · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran / near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (games__eu.veldsoft.no.thanks_1__L1_NONBLANK.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

### OpenSudoku

* **Package / identity:** `cz.romario.opensudoku` · type: game · version: —
* **Source:** source-first build (F-Droid/GitHub) · [upstream source](https://github.com/romario333/opensudoku)
* **APK SHA256:** `—`
* **Sessions:** S62+ / S85-sweep(shell at HEAD re-run; S-era canonical retained) · status: **VERIFIED** · rendering: L5
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** [cz.romario.opensudoku.jpg](evidence/canonical/cz.romario.opensudoku.jpg) · SHA256 `1478e902a245a829…`
* **Root cause / law:** see session report (S62-S65 spotlight reports)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** session-specific (see report)
* **Last success / first divergence:** see S62+ report / see session report
* **Notes:** canonical harvested from docs/evidence/s62plus_spotlight/opensudoku_frame0_folderlist.png

### OPMT (One More Time…)

* **Package / identity:** `one.scarecrow.games.OPMT` · type: game · version: —
* **Source:** source-first build (F-Droid/GitHub) · [upstream source](https://github.com/scarecrowgames/OneMoreTimePuzzleGame)
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **VERIFIED** · rendering: GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** [one.scarecrow.games.OPMT.jpg](evidence/canonical/one.scarecrow.games.OPMT.jpg) · SHA256 `17aa411b313a5aa2…`
* **Root cause / law:** PARTIAL
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** interaction + canonical artifact harvest
* **Last success / first divergence:** obs frames @L2 (S85) / none recorded
* **Notes:** S85 sweep promotion: prior PARTIAL → L2 render

### org.andstatus.game2048

* **Package / identity:** `org.andstatus.game2048` · type: game · version: 1.16.2
* **Source:** [F-Droid page](https://f-droid.org/en/packages/org.andstatus.game2048/) · [upstream source](https://github.com/andstatus/game2048)
* **APK SHA256:** `2d6707624623fe88…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Ljava/lang/Object;.getClass' on a null object referen
* **Notes:** S85 NEW-50 (game); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.asafonov.accelerace

* **Package / identity:** `org.asafonov.accelerace` · type: game · version: 0.12
* **Source:** [F-Droid page](https://f-droid.org/en/packages/org.asafonov.accelerace/) · [upstream source](https://github.com/asafonov/accelerace.apk)
* **APK SHA256:** `fe705a1599e6ce0c…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: LOADED_ONLY
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** none — clean run at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L0 / none recorded
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.bobstuff.bobball

* **Package / identity:** `org.bobstuff.bobball` · type: game · version: 1.17
* **Source:** [F-Droid page](https://f-droid.org/en/packages/org.bobstuff.bobball/) · [upstream source](https://github.com/bobthekingofegypt/BobBall)
* **APK SHA256:** `fd43009a7ffdfaf8…`
* **Sessions:** S84 · status: **VERIFIED-INTERACTIVE** · rendering: GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=True · interacted=True · state_changed=True
* **Canonical screenshot:** [org.bobstuff.bobball.gif](evidence/canonical/org.bobstuff.bobball.gif) · SHA256 `788ce033de1ae0c3…`
* **Root cause / law:** none (rc=0)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED
* **Remaining:** full app-specific behavior beyond click probe
* **Last success / first divergence:** 8/8 frames captured, click pass executed / none
* **Notes:** S84 NEW title. rc_obs=0 errors=0 frames=8/8 click: probed=6 state_changed=6. unique_colors=57 entropy=0.672 resources(dex/classes)=?

### org.lufebe16.pysolfc

* **Package / identity:** `org.lufebe16.pysolfc` · type: game · version: 1.2.1
* **Source:** [F-Droid page](https://f-droid.org/en/packages/org.lufebe16.pysolfc/)
* **APK SHA256:** `5b8ba9abc4c11ba0…`
* **Sessions:** S84/S85 · status: **OBSERVED** · rendering: L1_NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** Kivy bootstrap family (honest PARTIAL): Color.parseColor('') IAE in PythonActivity.setBackgroundColor (faithful AOSP IAE on empty string — app input), AssetManager.open null recv, String.startsWith null recv inside org.kivy chains; frames render past the exceptions.
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** Kivy runtime bootstrap chain
* **Last success / first divergence:** obs 8 frames @L2 (S85) / [SYNTH-EXC] S67 Color.parseColor (deferred): Ljava/lang/IllegalArgumentException; (Unknown color: ) method=Lorg/kivy/android/PythonActivity;.setBackgroundColor 
* **Notes:** S84 BLOCKED verdict was a TRUNCATED APK (74.6MB > 48MB cap) — re-downloaded vc102130601; renders L2 frames with Kivy bootstrap exceptions (honest PARTIAL). | S85 near-blank gate: rendered frames are the engine-default shell class; Kivy chain does not paint real UI yet. | Vocabulary: OBSERVED = loaded/ran with near-blank frames (S84 law); Kivy exceptions recorded in run/s85 logs.

### org.mattvchandler.a2050

* **Package / identity:** `org.mattvchandler.a2050` · type: game · version: 1.0.10
* **Source:** [F-Droid page](https://f-droid.org/en/packages/org.mattvchandler.a2050/) · [upstream source](https://github.com/mattvchandler/2050)
* **APK SHA256:** `98a0e75e589c3190…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-161 (OPEN, fan-out): Compose UI runtime internals — static compose UI renders, dynamic recomposition not implemented.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke interface method 'Ljava/util/Iterator;.hasNext' on a null object refe
* **Notes:** S85 NEW-50 (game); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.og8.a1tox

* **Package / identity:** `org.og8.a1tox` · type: game · version: 1.00
* **Source:** [F-Droid page](https://f-droid.org/en/packages/org.og8.a1tox/) · [upstream source](https://gitlab.com/og8org/1tox)
* **APK SHA256:** `34895a84a638d53b…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: LOADED_ONLY
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** none — clean run at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L0 / none recorded
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.secuso.privacyfriendly2048

* **Package / identity:** `org.secuso.privacyfriendly2048` · type: game · version: 1.4.2
* **Source:** [F-Droid page](https://f-droid.org/en/packages/org.secuso.privacyfriendly2048/) · [upstream source](https://github.com/SecUSo/privacy-friendly-2048)
* **APK SHA256:** `02c799d3d582669d…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** none — clean run at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / none recorded
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.secuso.privacyfriendlydame

* **Package / identity:** `org.secuso.privacyfriendlydame` · type: game · version: 1.3.4
* **Source:** [F-Droid page](https://f-droid.org/en/packages/org.secuso.privacyfriendlydame/) · [upstream source](https://github.com/SecUSo/privacy-friendly-dame)
* **APK SHA256:** `41727c0121fef8ab…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** none — clean run at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / none recorded
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.secuso.privacyfriendlymemory

* **Package / identity:** `org.secuso.privacyfriendlymemory` · type: game · version: 1.1.3-google
* **Source:** [F-Droid page](https://f-droid.org/en/packages/org.secuso.privacyfriendlymemory/) · [upstream source](https://github.com/SecUSo/privacy-friendly-memo-game)
* **APK SHA256:** `82f83d9ea572240a…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** none — clean run at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / none recorded
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.secuso.privacyfriendlysolitaire

* **Package / identity:** `org.secuso.privacyfriendlysolitaire` · type: game · version: 1.1
* **Source:** [F-Droid page](https://f-droid.org/en/packages/org.secuso.privacyfriendlysolitaire/) · [upstream source](https://github.com/SecUSo/privacy-friendly-solitaire)
* **APK SHA256:** `b0e2adf991f94982…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** none — clean run at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / none recorded
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org.secuso.privacyfriendlysudoku

* **Package / identity:** `org.secuso.privacyfriendlysudoku` · type: game · version: 3.2.6
* **Source:** [F-Droid page](https://f-droid.org/en/packages/org.secuso.privacyfriendlysudoku/) · [upstream source](https://github.com/SecUSo/privacy-friendly-sudoku)
* **APK SHA256:** `1aff917f4ac9952b…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** none — clean run at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / none recorded
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### org99managers.futsal_edition

* **Package / identity:** `org99managers.futsal_edition` · type: game · version: v0.8.5
* **Source:** [F-Droid page](https://f-droid.org/en/packages/org99managers.futsal_edition/) · [upstream source](https://codeberg.org/dulvui/99managers-futsal-edition/)
* **APK SHA256:** `c9eeea657951f694…`
* **Sessions:** S85 · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** F-NEW-162 (OPEN, fan-out): androidx lifecycle/savedstate generated adapter + ExternalSyntheticLambda gaps → deferred unwind PARTIAL.
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs 8 frames @L2 / [SYNTH-EXC] f141-null-recv (deferred): Ljava/lang/NullPointerException; (Attempt to invoke virtual method 'Landroid/content/res/AssetManager;.open' on a null ob
* **Notes:** S85 NEW-50 (game); rc_obs=1; frames=8; rc_click=1 | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### PFBattleship

* **Package / identity:** `org.secuso.privacyfriendlybattleship` · type: game · version: —
* **Source:** —
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** no prior root cause — rendered at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) / none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### Queens

* **Package / identity:** `com.sidhant.queens` · type: game · version: —
* **Source:** —
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** no prior root cause — rendered at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) / none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### RetroWars

* **Package / identity:** `com.serwylo.retrowars` · type: game · version: —
* **Source:** —
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** no prior root cause — rendered at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) / none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### Snake Deluxe

* **Package / identity:** `com.miniandroid.snakedeluxe` · type: game · version: —
* **Source:** in-house (games/snake-deluxe)
* **APK SHA256:** `—`
* **Sessions:** S80/S83 · status: **VERIFIED-INTERACTIVE** · rendering: L3_STRUCT_CANDIDATE
* **Execution evidence:** launched=True · rendered=True · interacted=True · state_changed=True
* **Canonical screenshot:** [com.miniandroid.snakedeluxe.gif](evidence/canonical/com.miniandroid.snakedeluxe.gif) · SHA256 `f2dd621c662526fa…`
* **Root cause / law:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean
* **Proven exactly:** LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED
* **Remaining:** graphics completeness beyond L3
* **Last success / first divergence:** full lifecycle + real frames (S83) / none recorded in S83 session
* **Notes:** S83 real-screenshot campaign evidence (games__snake_deluxe_v1.0_vc1__L3_STRUCT_CANDIDATE.jpg)

### Solitaire (Bielefeld)

* **Package / identity:** `de.tobiasbielefeld.solitaire` · type: game · version: —
* **Source:** —
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** no prior root cause — rendered at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) / none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### Solitaire (vayunmathur)

* **Package / identity:** `com.vayunmathur.games.solitaire` · type: game · version: —
* **Source:** F-Droid
* **APK SHA256:** `—`
* **Sessions:** S83 · status: **OBSERVED** · rendering: L2_GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=False · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** S83 near-blank final-frame class (eb16ab5c… ×16, uniq=2-3): app renders status-bar-only content at campaign parameters; real UI evidence exists only for titles with dedicated interaction runs (s83b sweep)
* **Proven exactly:** LOADED/LAUNCHED (frames not visual evidence)
* **Remaining:** real-UI render under dedicated interaction protocol
* **Last success / first divergence:** 8/8 frames captured; lifecycle ran / near-blank framebuffer (no meaningful UI pixels)
* **Notes:** S83 campaign (games__com.vayunmathur.games.solitaire_20260804__L2_GRAPHICALLY_INCOMPLETE.jpg) is the shared near-blank frame class — no canonical visual per S54 law; evidence = run logs

### Surge Engine (OpenSurge)

* **Package / identity:** `org.opensurge2d.surgeengine` · type: game · version: —
* **Source:** —
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** no prior root cause — rendered at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) / none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### Tarok

* **Package / identity:** `si.palcka.tarok` · type: game · version: —
* **Source:** —
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** no prior root cause — rendered at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) / none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### TheXTech (SuperTux-like)

* **Package / identity:** `ru.wohlsoft.thextech.fdroid` · type: game · version: —
* **Source:** —
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** no prior root cause — rendered at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) / none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### TicTacToe Classic

* **Package / identity:** `com.emmanuelmess.tictactoe` · type: game · version: —
* **Source:** F-Droid com.emmanuelmess.tictactoe
* **APK SHA256:** `16510d7cb5dbcf7d…`
* **Sessions:** S83 · status: **VERIFIED-INTERACTIVE** · rendering: L2_GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=True · interacted=True · state_changed=True
* **Canonical screenshot:** [com.emmanuelmess.tictactoe.gif](evidence/canonical/com.emmanuelmess.tictactoe.gif) · SHA256 `b6811a17d271d5dc…`
* **Root cause / law:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean
* **Proven exactly:** LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED
* **Remaining:** graphics completeness beyond L3
* **Last success / first divergence:** full lifecycle + real frames (S83) / none recorded in S83 session
* **Notes:** S83 real-screenshot campaign evidence (games__tictactoeclassic__L2_GRAPHICALLY_INCOMPLETE.jpg)

### TicTacToe Deluxe (دوز)

* **Package / identity:** `com.miniandroid.tictactoedeluxe` · type: game · version: —
* **Source:** in-house (games/tictactoe-deluxe)
* **APK SHA256:** `—`
* **Sessions:** S83 NEW · status: **VERIFIED-INTERACTIVE** · rendering: L3_STRUCT_CANDIDATE
* **Execution evidence:** launched=True · rendered=True · interacted=True · state_changed=True
* **Canonical screenshot:** [com.miniandroid.tictactoedeluxe.gif](evidence/canonical/com.miniandroid.tictactoedeluxe.gif) · SHA256 `ade32b621e90fb27…`
* **Root cause / law:** S83 engine laws (APX-ACT, CANVAS-GEOMETRY, LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all fixed and regression-clean
* **Proven exactly:** LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED
* **Remaining:** graphics completeness beyond L3
* **Last success / first divergence:** full lifecycle + real frames (S83) / none recorded in S83 session
* **Notes:** S83 real-screenshot campaign evidence (games__tictactoe_deluxe_v1.0_vc1__L3_STRUCT_CANDIDATE.jpg)

### Tirailleur

* **Package / identity:** `com.bupkis.tirailleur` · type: game · version: —
* **Source:** —
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** no prior root cause — rendered at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) / none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

### TriPeaks

* **Package / identity:** `eu.veldsoft.tri.peaks` · type: game · version: —
* **Source:** source-first build (F-Droid/GitHub) · [upstream source](https://github.com/VelbazhdSoftwareLLC/TriPeaks)
* **APK SHA256:** `—`
* **Sessions:** S65 · status: **PARTIAL** · rendering: L10
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** [eu.veldsoft.tri.peaks.jpg](evidence/canonical/eu.veldsoft.tri.peaks.jpg) · SHA256 `8e1d41a151898010…`
* **Root cause / law:** see session report (S62-S65 spotlight reports)
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** session-specific (see report)
* **Last success / first divergence:** see S65 report / see session report
* **Notes:** canonical harvested from docs/evidence/visual_forensics/s65_reval/tripeaks/board_full.png

### Vector Pinball (bouncy)

* **Package / identity:** `com.dozingcatsoftware.bouncy` · type: game · version: —
* **Source:** [F-Droid page](https://f-droid.org/en/packages/com.dozingcatsoftware.bouncy/) · [upstream source](https://github.com/dozingcatsoftware/Bouncy)
* **APK SHA256:** `ffda0d9cb0b1b2aa…`
* **Sessions:** S62+ / S85-sweep · status: **VERIFIED-INTERACTIVE** · rendering: GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=True · interacted=True · state_changed=True
* **Canonical screenshot:** [com.dozingcatsoftware.bouncy.gif](evidence/canonical/com.dozingcatsoftware.bouncy.gif) · SHA256 `d96b48d7e8667b5b…`
* **Root cause / law:** none — interaction proven at current HEAD
* **Proven exactly:** LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED
* **Remaining:** graphics completeness beyond L3
* **Last success / first divergence:** click pass with state change (S85) / none
* **Notes:** S85 sweep: probed=12 state_changed=10

### x653.all_in_gold

* **Package / identity:** `x653.all_in_gold` · type: game · version: 1.2
* **Source:** [F-Droid page](https://f-droid.org/en/packages/x653.all_in_gold/) · [upstream source](https://gitlab.com/x653/all_in_gold)
* **APK SHA256:** `01f04f99173ead82…`
* **Sessions:** S85 · status: **VERIFIED** · rendering: GRAPHICALLY_INCOMPLETE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** [x653.all_in_gold.jpg](evidence/canonical/x653.all_in_gold.jpg) · SHA256 `658d0a2825cce720…`
* **Root cause / law:** none — clean run at current HEAD
* **Proven exactly:** LOADED/LAUNCHED/RENDERED
* **Remaining:** state-change evidence
* **Last success / first divergence:** obs 8 frames @L2 / none recorded
* **Notes:** S85 NEW-50 (game); rc_obs=0; frames=8; rc_click=0

### xyz.deepdaikon.quinb

* **Package / identity:** `xyz.deepdaikon.quinb` · type: game · version: —
* **Source:** —
* **APK SHA256:** `—`
* **Sessions:** S85-sweep · status: **OBSERVED** · rendering: NONBLANK_NEARBLANK_GATE
* **Execution evidence:** launched=True · rendered=True · interacted=False · state_changed=False
* **Canonical screenshot:** —
* **Root cause / law:** no prior root cause — rendered at current HEAD
* **Proven exactly:** LOADED/LAUNCHED
* **Remaining:** real UI render (near-blank engine-default shell class at HEAD)
* **Last success / first divergence:** obs frames @L2 (S85) / none recorded
* **Notes:** S85 sweep promotion: prior OBSERVED → L2 render | S85 near-blank gate: all frames match the engine-default shell class (nonbg_ratio=0.0113, white fb + black status region); no honest visual claim (S54 law).

