# Knowledge Transfer Log — external mechanism → MiniAndroid

Law (§20): no knowledge is "transferred" merely because it was read. An
entry becomes TRANSFERRED only when: mechanism understood → MiniAndroid
mapping written → implementation landed (commit) → focused test → runtime
validation → regression protection. This log records every step that
REACHED, and the queue that has NOT yet reached, that bar.

## TRANSFERRED this campaign (research→documentation→mapping)

KT-001 WineDroid identity + architecture knowledge
- External: rickbergs/winedroid a784c0b (Apache-2.0)
- Mapping: sibling userspace runtime; opposite execution model (AOT vs
  interpreter); 20 mechanisms cataloged with IDs
- Implementation: docs/research/winedroid-study.md (this commit series)
- Test: n/a (documentation transfer)
- Validation: file-by-file source citations re-checkable in clone
- Status: TRANSFERRED (knowledge layer)

KT-002 DEX check-order + cdex law (ART + WineDroid corroboration)
- Mapping: aosp-runtime-study.md AOSP-015/016
- Status: TRANSFERRED (documentation; implementation queued AOSP-016)

KT-003 AOSP layout contract confirmation
- Mapping: layout-study.md LAY-001..006 (line-exact citations)
- Status: TRANSFERRED (confirms existing implementation; UNSPECIFIED-row
  and GONE fixtures queued)

KT-004 Font Case-F upstream semantics (createFromAsset two failure modes)
- Mapping: font-runtime-study.md FONT-002 — the strongest evidence found
  this campaign for §27's "same event must not be reported the same" law
- Status: TRANSFERRED (diagnostics spec pinned; fixture queued)

KT-005 ARSC sparse/offset16 flag constants
- Mapping: arsc-resource-study.md ARSC-001 (verbatim constants)
- Status: TRANSFERRED (spec pinned; fixtures queued)

KT-006 Byte-exact round-trip methodology (droidsaw)
- Mapping: dex-runtime-study.md DEX-009 → queued ARSC round-trip fixture
- Status: TRANSFERRED (methodology; tool queued)

KT-007 Prior-session WineDroid knowledge reconciliation
- Previous records resolved "Winedroid" to winedroid.soham.sh (GPL,
  private repo, site-docs-only). This campaign's mandated exact URL
  (rickbergs/winedroid) proved to be a DIFFERENT, now-public Apache-2.0
  project. Both identities now live separately in the reference matrix
  and external-repositories.md; no knowledge was lost, the confusion is
  permanently disambiguated.
- Status: TRANSFERRED (record hygiene)

## QUEUE (understood + mapped; awaiting implementation cycles)

Q-1 WINEDROID-004 MUTF-8 cross-check tests (portable unit vectors)
Q-2 WINEDROID-006 multi-dex ordering test vector
Q-3 WINEDROID-007 zero-fill discriminator fixture
Q-4 WINEDROID-011 payload-is-data fixture
Q-5 AOSP-005 GONE-weighted-child fixture
Q-6 AOSP-010 CCW fill-and-stroke fixture
Q-7 AOSP-016 cdex rejection diagnostic
Q-8 ARSC-001 sparse/offset16 unit fixtures
Q-9 ARSC-003 ARSCLib JSON differential decode
Q-10 DEX-009 ARSC byte-exact round-trip harness
Q-11 FONT-002 Case-F distinct-event fixture
Q-12 G7 per-method link/reject report artifact
Q-13 WINEDROID-015/016 inspect report enrichment
Q-14 WINEDROID-017 size caps + sandbox posture doc

## REJECTED (studied, deliberately not transferred — with reasons)

R-1 waydroid LXC container model — full-Android container; MiniAndroid is
    a minimal userspace runtime (identity mismatch).
R-2 DroidVM hypervisor management — inverse problem (VMs ON Android).
R-3 crosvm/cuttlefish/AVF process isolation — no sandbox requirement yet;
    architecture patterns recorded for the future (GFX-004/G9).
R-4 skydnir Docker-Engine-API-shaped runtime — custom license forbids
    reuse; methodology-only value (already adopted: zero-skip gates).
R-5 DaliVM code — GPL-3.0; oracle-only (tables read, zero import).
R-6 qemu full device emulation — orthogonal scale; emugl translation
    concept noted only.
R-7 Bundletool split-APK machinery — no AAB-derived corpus APKs.
