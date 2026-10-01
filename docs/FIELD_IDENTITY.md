# FIELD IDENTITY TABLE — canonical (FINAL CAMPAIGN Phase 2)

Law authority: AOSP ART field resolution (fields occupy distinct slots per
declaring class; a superclass field cannot alias a subclass field) + F-NEW-160
(S134) + this phase's reflection/Unsafe extension. Zero package-name heuristics
(identity is decided by `is_dex_defined_class`, i.e. whether the runtime has a
DEX body for the class — NEVER by package prefix).

## 1. The identity law

```
DEX field identity  =  declaring-class + field-name (+ type from the DEX table)
storage key         =  is_dex_defined_class(declarer)
                          ? "<declarer>;-><name>"      (qualified primary)
                          : "<name>"                   (bare, framework-owned)
write convention    =  DEX-defined: dual-write (qualified primary + bare
                       legacy mirror) — interpreter iput, reflection Field.set
                       (this phase). Framework shadows: bare only.
read convention     =  DEX-defined: read qualified primary; miss ⇒ the field's
                       typed DEFAULT (AOSP law: a never-written field answers
                       its default, never another class's slot).
                       Framework-owned: read bare.
declarer resolution =  resolved_field_declarer(ref_cls, name): walk
                       class_to_superclass_ up to 32 hops, stop at the first
                       non-DEX-defined ancestor, return the class whose
                       dex instance_fields contain `name`; else ref_cls.
```

## 2. The table

| Access path | Identity used | Resolution | Storage key | Notes |
|---|---|---|---|---|
| interpreter `iget/iget-object/iput*` (F-NEW-160) | declarer+name | `resolve_field` + `resolved_field_declarer` | qualified primary; iput dual-writes bare mirror | `s134_dex_field_key` |
| interpreter `sget/sput*` | class+name | field table | `static_field_storage_["<cls>.<name>"]` | per-class keys cannot alias |
| reflection `Field.get` (PHASE-2 FIX) | Field's declaring_class metadata + name | `resolved_field_declarer(decl337,name)` | qualified primary; DEX-miss ⇒ typed default | same key as iget — property 6 |
| reflection `Field.set` (PHASE-2 FIX) | same | same | dual-write: qualified primary + bare mirror | same convention as iput — property 6 |
| reflection statics | `decl.name` | field table | `static_field_storage_` (same map as sget/sput) | one store, one key format |
| `sun.misc.Unsafe` all 14 get/put/CAS variants (PHASE-2 FIX) | offset registry `(declaring-class, field-name)` | `resolved_field_declarer` on the registry pair | qualified primary for DEX declarers, bare otherwise | single edit point: `field_name_for337` |
| instance-field initializer defaults (R-NEW-414) | declarer+name | `resolved_field_declarer` | qualified + bare mirror | property 8: defaults belong to the declarer |
| C++ shadow field accessors (`heap_adapter.h` → `Heap.get/set_object_field`) | caller-supplied name | — (framework-owned fields) | bare | property 5: shadow interop unchanged |
| engine-internal heap metadata (`path`, `tint_color`, `ts_*`, `array[i]`, `__array_length__`, `__reflect_*`) | engine namespace | — | bare | NOT DEX field identity — no collision surface (reserved-name conventions) |
| node-field fallbacks / debug serialization | engine namespace | — | bare | metadata only |

## 3. Mission property checklist (Phase 2 proof)

1. **DEX primary identity = declarer+name(+type)** — `s134_dex_field_key` (dalvik_engine.cpp:14620).
2. **ART declarer resolution** — `resolved_field_declarer` (dalvik_engine.cpp:14634), superclass walk, framework ancestor stop.
3. **Inherited access resolves to the real declarer** — the walk starts at the reference class; a subclass iget of an inherited field keys the DECLARER.
4. **Same-name unrelated classes never alias** — qualified primary includes the declarer; a never-written DEX field answers its default (iget law, dalvik_engine.cpp:14691).
5. **Framework-owned identities stay shadow-compatible** — bare keys preserved for every non-DEX-defined declarer (heap_adapter pass-throughs untouched).
6. **Reflection sees the same field** — PHASE-2 FIX: Field.get/set now use the interpreter's identity law (previously bare-only: a reflection `Field.set` wrote a slot the qualified read could never see — silent-wrong, Constitution §17).
7. **Unsafe sees the same field** — PHASE-2 FIX: all 14 Unsafe variants address the qualified identity via the offset registry pair (previously bare-only).
8. **Initializer defaults belong to the declaring class** — R-NEW-414 site keys the materialized default under the declarer-qualified identity.
9. **No generic shadow reads an unrelated DEX bare mirror** — the bare mirror is write-through additional storage; shadow bare reads observe DEX writes exactly as before F-NEW-160 (behavior preserved; no new aliasing surface).
10. **Goldens byte-identical** — dooz `ba8a95eb2278594f` ×3 (isolated `--data-root`), laws130 51/51 PASS after the fixes.

## 4. Known non-conflicts / records

- `simplestopwatch_26` golden (`e00fe7e082c385f8`) belongs to version 26 of the
  stopwatch APK, which is NOT in the current cache (only
  `com.github.muellerma.stopwatch_6.apk` is). stopwatch_6 renders
  deterministically `eb16ab5c68fa9b6c` ×3 (isolated data-root) — its own frame,
  not a regression. The S134-wave-6 worklog gate line that labels `eb16ab5c`
  as "WhatsApp" is a label conflation; corrected by this audit.
- Static seeds at `Lorg/telegram/messenger/ApplicationLoader;.applicationContext`
  (dalvik_engine.cpp:1675/4236) are app-named static seeds — flagged for the
  Phase 11 stub/call contract audit (they predate the final campaign's
  zero-app-specific rule; they are static-state injection points, not field
  identity bugs).
