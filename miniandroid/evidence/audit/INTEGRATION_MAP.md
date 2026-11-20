# INTEGRATION MAP — accepted contributions on the shared execution chain

```
APK (upload/handoff_apks, 15 originals)
 → Manifest/Resources  arsc_parser (TypedValue radix AUD-33) · axml_parser · manifest_reader
   · OPEN: nine-patch npTc (AUD-32) · GridLayout solver (AUD-30)
 → DEX / Class Loading  class_resolver · dex_parser
 → Dalvik Interpreter   dalvik_interpreter (wave-7 contract, -O2) · opcode laws:
   move/from16 move-wide/from16 lit8 lit16 const-string/jumbo (AUD-46, w15 law test)
 → Framework API        android_shadows + shadow_registry (BUG-7 duplicate OPEN AUD-49)
   · ScrollView wiring PARTIAL (AUD-31) · FORTIFY 3 symbols OPEN (AUD-34)
 → View / Adapter / Layout  layout_inflater.cpp (AUD-27) · real_layout · #606 closed
   · OPEN per #632: gravity 3-call-site laws, RelativeLayout anchors, weight laws
 → Canvas / Drawable    software_renderer · vector_decode (MG-010 partial AUD-41;
   MG-011 ok-fix NOT integrated AUD-40) · text_shaper FriBidi/HarfBuzz/FreeType (AUD-28)
 → Input                touch_dispatcher (real taps in gate runs)
 → State Change         battery law tests s1xx-s23x (49/49 rc0 today)
 → Rendered Output      screenshot SHA-256 gate vs canonical set (11/11 IDENTICAL today,
   incl. TicTacToe AUD-36) — no placeholder screenshots; hashes re-verified per build
 → Regression           .DELETE_ON_ERROR added (AUD-09) · battery manifest parity ·
   5-APK gate · ABBA A/B discipline (BUG-5 lesson AUD-22)
```

Build side (feeds every stage above):

```
core_sources.manifest (single source of truth; Makefile + CMakeLists both read it)
 → Make: 1× QuickJS OBJECT reuse (AUD-03) · all: $(EXECUTABLE) anchors (AUD-04)
   · FASTPROFILE=1 W24TIERS=1: 55 cold TUs at -O1 → −17.3% wall / −17.7% CPU
     (AUD-11/12, byte-identical candidate reps, battery+gate PASS)
   · canonical `make all` untouched; FASTPROFILE-only path preserved as fallback
 → CMake: parity GAP — builds without -DMINIANDROID_HAVE_WEBP (AUD-07 OPEN);
   QuickJS 2× compile (AUD-02 OPEN); battery loop without EXCLUDE_FROM_ALL (AUD-01 OPEN)
 → tools: ccache warm 25.4 s (INTEGRATED opt-in) · mold/lld/split-dwarf/ggc-min/
   var-tracking/Ninja/PCH: all REJECTED-MEASURED (REJECTED_AND_CORRECTED.md)
 → host: hypervisor steal ≈24% of every build window — capacity floor 288.4 s
   at current CPU work; not schedulable (AUD-14/15)
```

Rule applied: an accepted fix is mapped to its CONSUMER stage; a finding with
no consumer yet (MG-011, RC-12 oracle, layout apps, GridLayout solver) is
marked NOT-INTEGRATED on the map, not counted as a runtime capability.
