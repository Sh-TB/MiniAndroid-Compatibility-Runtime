# RELEASE v0.0.4-Chantecler — provenance & evidence

Date: 2026-09-10. HEAD: `ad4349a9` (M8). Predecessor: v0.0.3-Chantecler
(tag `7e18cd72`, HEAD f3e992f7).

## What this release contains (one paragraph, honest)

One generic runtime upgrade family — **F-050 (Choreographer frame-pump
family)** — landed, micro-proven, and regression-verified, advancing the
dooz Compose first-frame chain by four blocker layers. The final Compose
frame is STILL NOT RENDERED (deterministic blank); no visual success is
claimed. Battery: **91/91 ALL PASS**. 3-run byte-identical: dooz,
real-APK TicTacToe, and the new f050 fixture.

## Roots in this release (each: upstream law + live evidence + micro-proof)

| Root | Law | Upstream | Proof |
|---|---|---|---|
| F-050a | Choreographer singleton + FIFO frame callbacks + one shared monotonic frame time per vsync tick; runtime pumps doFrame(J) at frame boundaries | AOSP Choreographer.java; AndroidX AndroidUiDispatcher | f050 L6/L7 bands; doFrame tick t=1016666667ns |
| F-050c | AtomicLongFieldUpdater getAnd* / *AndGet exact-name epochs (getAndIncrement = +1, returns OLD) | OpenJDK AtomicLongFieldUpdater.java | f050 L1/L2; dooz corruption 0→-1 eliminated |
| F-050d | Boolean.TRUE/FALSE non-null singletons (R8 valueOf rewrite) | OpenJDK Boolean.java | f050 L3/L4; "Channel was cancelled" cascade eliminated |
| F-050b | Throwable detailMessage law | OpenJDK Throwable.java | f050 L5; [EXCEPTION] logs message-visible |
| F-050e | §6 registry invariant count law | repo invariant | battery stage 34: 24 checks, 0 failures |

Evidence documents: `docs/ROOT_IMPACT_MATRIX.md`,
`docs/APK_LOADING_IMPACT_MATRIX.md`, `docs/ROOT_DISCOVERY_INDEX.md`,
`docs/COMPATIBILITY_CLOSURE_MATRIX.md`.

## Release gates (all enforced)

1. Battery 91/91 ALL PASS at the packaged binary (`logs/battery_m8_full.log`).
2. f050 micro-proof 7/7 bands GREEN, 3-run byte-identical.
3. dooz 3-run rc=0 byte-identical (honest deterministic BLANK — 0 non-white;
   NO Compose visual claim).
4. Real-APK TicTacToe 3-run rc=0 byte-identical (T3/BLANK boundary preserved).
5. Telegram: BLOCKED (1.2 MB stub served vs pinned 82 MB artifact; fetch
   rejects) — recorded, not silently skipped.
6. Release-content gate: PASS (0 development artifacts) — the packaging
   script now treats the Windows asset as optional with an honest omission
   note (v0.0.3 precedent).

## Asset provenance

| Asset | SHA-256 |
|---|---|
| MiniAndroid-v0.0.4-Chantecler-linux-x64.tar.gz | `5c9cc5c6869f3f31a1f0aae6a7d00018a3b4d7ae26ef7e4203621583beecb939` |
| Windows asset | honestly omitted — no Windows toolchain in this build environment (v0.0.3 precedent) |

Built from the repo tree at `ad4349a9` by `scripts/package_release.sh`
(validated by `scripts/validate_release_content.py`).
