## CONT-37 ledger («گیت هاب به روز رسانی ادامه ادامه تا هدف نهایی»)

**Self-update**: the container was 331 commits behind (stale at e99c2fbd = CONT-10 era) — honest admission; synced to e9ba74d2 and the engine rebuilt BYTE-IDENTICALLY (60d377668b5a2649; dooz anchor 851cc176 reproduced pre-wave).

**«مشکلش حل شد» rows (pc-exact / live-evidenced):**

- **F-NEW-541 ROOT-CAUSED-FIXED** — the M3-19 active-cycle key dropped the CALLER-SITE pc: compose dispatches the same draw-block object per structural position from different walk sites; the (method,receiver,args)-complete key collided them and the active-cycle stub killed 9 dispatches of the draw-block dispatcher `Lho1;.b(Lf90;)`. DEX chain decoded end-to-end: board draw block `Lz6;.i` (530 units) ← `Lmy;.i` ← `Lp00;.j0` (iface) ← `Lgl0;.j0` ← `Lgi;.j0` ← `Ly3;.m` pc=42 ← `Ljt1;.drawLine` — both lambdas had ZERO invocations in the whole run. Fix = `~pc<N>` key part (strictly more specific; same-site cycles still stubbed; depth-80 backstop). Stub hits 9→6. Regression wall GREEN (anchors 6/6 byte-exact, games 7/7 exact, negatives 19/19, skill 13/13). **Honest: the dooz board still does not paint** — the same-site (~pc2) family (6 kills) + the destination parent-chain walk are the named next faces.
- **R-NEW-543 (F-NEW-542 instrument) ROOT-CAUSED-FIXED** — MINIANDROID_HEAP_CENSUS (live per-class allocation histogram + periodic emitter). **REFUTES the CONT-36 telegram envelope**: live_objects ≈ 10.5–11.7K, RSS FLAT at 2855MB from the first 400K instructions (2047MB@100K → 2854MB@400K → constant) — the 2.85GB bulk = the BOOT-TIME parsed representation (64MB APK → ~45×; per-method std::string copies × ~700K methods). The heap-GC lever is DEAD. Telegram levers re-ranked: (1) boot representation (interning/lazy materialization), (2) tri.resolve/em.setup throughput.
- **Telegram ADVANCEMENT (post-541)**: the 22s window reaches `LaunchActivity.onCreate`'s REAL UI draw dispatch (ActionBar/c4;.dispatchDraw, Components/pa;.onDraw, ActionBar/w;.onDraw, u4/g;.onDraw — 11 draw entries), BUDGET-bound (F084 in-draw, F298-KEEP), rc=1, NO OOM; the 60s rc=137 is the 3GB sandbox ceiling.

**«حداقل ۳ تا برنامه دیگر کامل لود» — MET WITH VISUAL EVIDENCE**: 5 titles render their COMPLETE first-launch UI at the standard census window — librecontacts (full settings UI), bouncy (full game menu), balance (full onboarding), wocheneindauf-class full forms (wocheneinkauf), listai (reader landing). Screenshots: run/cont37_batch50/r_*/screenshot.png (census: evidence/cont37/batch50_census.json). Honest provenance: SAME binary as CONT-36 — the delta is container execution speed, not a new engine law; recorded as evidence, not as a fix.

**Batch-50 census**: 50/50 rows at the current binary; 13 content rows; 37 blanks with named per-title faces (the 7 CONT-36 wagons advanced: how2vote/leradar/subster past AllowListPlugin; voyager past registerUriForScheme; chompass services resolve — each at its next face, honestly recorded).

**Registry 832→834 id-unique.** Push: e9ba74d2..2ca38aba. Evidence: evidence/cont37/CONT37_WAVE_LEDGER.md.

**Next wave**: dooz same-site (~pc2) re-entry family + destination parent-chain walk; telegram boot-representation bulk (interning/lazy materialization) + per-call machinery throughput; netguard gray-mask / peri double-paint dives.
