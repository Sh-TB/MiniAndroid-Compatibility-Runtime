# WAVE-8 Development Build Architecture — shared-library dev path (TESTED, isolated)
Production static build and Monolith fallback: **unchanged** (build/, `make DALVIK_SPLIT=0`).
The new path lives entirely in `build_dev_so/` + `scripts/w8_sodev.py` / `w8_loop.py`.
Rollback: `rm -rf build_dev_so/` (nothing else is touched).

## Architecture

```
one-time (114.6 s): -fPIC recompile of the 7 dalvik part TUs → build_dev_so/objects/
                    (same flags as production: -O2 -g0, interpreter keeps inline-budget
                    params, bridge keeps -Og; PIC overhead measured ≈ 0: 21.5 s vs 21.8 s)

per engine edit:    g++ -c (PIC TU)  →  libminiandroid_dalvik.so relink (0.18 s)
                    → test exes NOT relinked (they load the .so at runtime, rpath $ORIGIN)
                    → battery runs in 0.02 s

test exes & main:   tests/<t> and miniandroid_dev = stable core (75 objs) + quickjs + thunk
                    (STATIC, with debug) + -lminiandroid_dalvik (DYNAMIC) → linked only when
                    stable objects or test sources change (5.0/1.6/5.6 s, main 0.9 s)
```

## Why non-PIC .so was rejected (measured)

`ld` refuses: `R_X86_64_TPOFF32 against diag_env::count — recompile with -fPIC` (thread_local
in the objects; `-z notext` does not fix TLS relocations). PIC recompile of the volatile set
is therefore mandatory; the stable set stays non-PIC static (no TLS-related link penalty).

## Why two .so boundaries (dalvik vs stable)

The dalvik 7-TU set is the volatile set (every engine edit). The stable set (framework,
webview, storage, quickjs…) rarely changes and carries the 100+ MB debug payload — keeping it
static preserves full debuggability while excluding it from the per-edit loop. Changing one
stable object → relink that test exe (one-time ~5 s) but NOT the .so loop.

## Make-level dependency hygiene (adoption recipe)

Test exes must NOT depend on the .so file timestamp (else make relinks them every engine
edit). Standard practice: link against `libminiandroid_dalvik.so` via SONAME + a stamp file
that only changes on ABI/SONAME change (`libminiandroid_dalvik.so: <pic objects> …; stamp:
touch` rule). Not wired into the Makefile this wave (additive opt-in targets only proposed);
the measured driver scripts are the reproducible artifact.

## Measured end-to-end loops (fresh-process timing)

| Loop | Before (static) | After (.so dev path) | Reps |
|---|---:|---:|---|
| Interpreter edit→compile→link→tests | 36.4 s (23.9+12.5) | **20.7–21.1 s** (compile 20.5–20.9 + so 0.18 + tests 0.02) | ×3 |
| Opcode edit→…→tests | 12.8–17.5 s | **9.6–9.8 s** | ×2 |
| .so relink | n/a | 0.18 s (7/7 runs) | ×7 |

Runtime proof: 3 original APKs on `miniandroid_dev` (dynamic .so) — screenshot SHA-256
**identical to canonical**: Guess `87fe26766fc48d06c59d4c15` (rc=0), DiceRoller
`46b07062…`, TicTacToe `d55056a8…` (PARTIAL as documented; hashes byte-identical).
Battery on the .so path: 3/3 PASS. See `wave8_runtime_parity.json`.
