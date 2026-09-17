# S56 — R-NEW-368 premise refuted: uNote main-menu buttons ARE hit-testable

## The refutation

The registry entry claimed "NO tap target is hit-testable anywhere on the
1080x1920 grid" based on 16 probes at x in {270,540,810,940} × y in
{300,450,660,760,860,1060,1200,1350,1500,1650,1780}.

The view tree (EXP092-RENDER) places the main-menu buttons in the BOTTOM
44-pixel band — y = 1876..1920 — a band the probe grid never touched:

```
[EXP092-RENDER] node=12 class=LinearLayout children=3 depth=1 pos=(0,1876) size=(1080x44)
[EXP092-RENDER] node=13 class=Button text="Add note" depth=2 pos=(0,1876) size=(360x44)
[EXP092-RENDER] node=14 class=Button text="Search"   depth=2 pos=(360,1876) size=(360x44)
[EXP092-RENDER] node=15 class=Button text="Quit"     depth=2 pos=(720,1876) size=(360x44)
```

## The proof: tap at the real coordinates

`./miniandroid/build/miniandroid run --tap 270,1898 apk_cache/app.varlorg.unote_30.apk`:

```
[G06-TAP] DOWN (270,1898) target=13 consumed=1
[G06-TAP] UP click_posted=1
[INTENT] startActivity called → Lapp/varlorg/unote/NoteEdition;
```

The canonical tap pipeline (hit-test → DOWN consumed by Button 13 → UP →
click) dispatched the listener, and the app itself launched its editor
activity (`NoteEdition`). That is the full L6 input→state→navigation
chain for uNote's main menu.

## Verdict

- R-NEW-368 "paint renders buttons but touch finds no target" is
  REFUTED: paint rect == touch rect (both y=1876-1920). The 16-probe
  grid predates the current layout law and simply never probed the
  button band.
- uNote main menu: input→state→navigation PROVEN at S56 HEAD.
- New (minor) surface observed in NoteEdition.onCreate (separate items,
  not blockers): PreferenceManager.getDefaultSharedPreferences,
  Activity.getApplicationContext REC-MISS.

## Repro

```
./miniandroid/build/miniandroid run --tap 270,1898 apk_cache/app.varlorg.unote_30.apk
```
