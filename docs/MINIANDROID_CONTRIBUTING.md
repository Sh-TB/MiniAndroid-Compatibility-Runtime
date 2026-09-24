# CONTRIBUTING — MiniAndroid

> Welcome. MiniAndroid is a from-scratch C++17 **Android Compatibility
> Runtime**: it executes real Android APKs (DEX → framework → lifecycle →
> views → rendering → input → state change → screenshot), with every claim
> pinned to committed, hash-tracked evidence.
> Read [MINIANDROID_TICKET_GUIDE.md](MINIANDROID_TICKET_GUIDE.md) once — it
> is the law for how work is tracked.

## The 30-second version

1. Pick a ticket from [MINIANDROID_MASTER_QUEUE.md](MINIANDROID_MASTER_QUEUE.md)
   (or route yourself below).
2. Follow the 9-step chain in the ticket guide (source lookup first —
   never reproduce behavior from memory; CONSTITUTION §170).
3. Land: ticket update + fixture + battery green + APK before/after evidence.
4. Run `python3 tools/validate_control_system.py` before committing.

## Route yourself

**"I have 20 minutes"**

- Reproduce an existing failure: pick any `OBSERVED`/`PARTIAL` ticket
  (GFX-005 urlchecker chevrons is a good one) and record fresh evidence.
- Verify an APK SHA256 against its registry pin.
- Run a fixture: `bash scripts/test/run_test_battery.sh` and paste failures.
- Validate a control APK after someone's fix (nounours/unote/gmdice).
- Add a source citation to a ticket that lacks one (pin the exact file/symbol).

**"I have 30–60 minutes"**

- Add an upstream test fixture (PORT_TEST/PORT_FIXTURE) — see GFX-004
  NinePatch, TEXT-003 ellipsize, STORE-001 sqlite rollback.
- Trace one API through `tools/source_lookup.py` and file the law sentence
  into the ticket.
- Reproduce a ticket end-to-end with the capture protocol.

**"I have 1–3 hours"**

- Port an existing algorithm behind a fixture (GFX-002 weight law is
  fixture-ready; GFX-003 GIF disposal has 437 upstream test files).
- Add a semantic test to the battery (zero-skip law applies).
- Run a corpus fan-out measurement for a landed law (E6).

**"I can do advanced work"**

- Runtime implementation: DEX-001/CONC-001/JNI-001 (ART semantics,
  coroutines, JNI).
- Networking/TLS: NET-001 (P0) — curl/openssl adaptation through the
  existing shadow API surface.
- Media: AUDIO-001 real-APK traces; VIDEO-001 reuse matrix first.
- Browser: WEB-001 reuse matrix (litehtml vs lexbor vs html5ever) — no
  from-scratch engines, directive §13.

**"I research upstream"**

- Deep-read a registry `IDENTITY_ONLY` repo (57 waiting) and file exact
  file/symbol/test pointers into matching tickets.
- License-classify reuse candidates before any port (pinned-SHA evidence).

**"I can test / run APKs"**

- Control-APK duty after every fix; 3-run determinism sweeps; evidence
  hashing into `docs/evidence/`.

## Environment bootstrap (after any container reset)

```bash
cd /home/z/my-project/miniandroid && make -j          # runtime binary
bash scripts/build/bootstrap_toolchain.sh             # aapt2/ECJ/D8/stubs
bash scripts/test/run_test_battery.sh                 # expect 99/99 ALL PASS
python3 miniandroid/scripts/download_test_apks.py --only <titles>  # SHA-pinned corpus cache (outside repo)
```

External fixture note: EXT-01/02 fetch per
`docs/evidence/EXTERNAL_FIXTURE_HELLOWORLDSELFAWARE.md`
(APK SHA256 `009b4671…`, reference PNG `121d479c…`) into
`/home/z/corpus/external_hello/` (zero-APK-in-repo law).

## Non-negotiable rules

1. **Evidence or it didn't happen.** E-levels per the ticket guide; no
   visual claim without semantic evidence; no threshold tuning to pass.
2. **Source-first.** Registry lookup before any implementation; justify any
   custom code in the ticket (§18 of the control-system directive).
3. **One problem state.** Tickets live in TICKET_REGISTRY.json only; update
   them in the same commit as the change.
4. **Zero repo bloat.** No APKs/AABs/logs/toolchains in git (pre-receive
   rejects >100MB; backup branch is permanently blocked this way).
5. **No secrets, ever.** Tokens via env only; the pre-push secret guard is
   fail-closed.
6. **Controls must not regress.** Every fix re-runs ≥2 controls + battery.

## Good first issues (curated, 2026-09-25)

| Ticket | Task | Level |
|---|---|---|
| GFX-004 | NinePatch fixture APK + band golden | 30–60 min |
| TEXT-003 | Ellipsize fixture | 30–60 min |
| STORE-001 | SQLite rollback fixture test | 1–3 h |
| NET-002 | Diagnostic app skeleton (UI-only stages first) | 1–3 h |
| GFX-002 | Weight-law fixture (implementation ready to port) | 1–3 h |
| AUDIO-001 | First real-APK audio state trace | 1–3 h |
| NET-001 | Offline error-path fixtures | 1–3 h |
| WEB-001 | Browser reuse matrix (research doc) | advanced-research |
