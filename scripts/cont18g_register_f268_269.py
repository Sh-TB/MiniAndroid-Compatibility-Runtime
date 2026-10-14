#!/usr/bin/env python3
"""CONT-18g: register F-NEW-268 (exception-semantics law family) and
F-NEW-269 (split dual-handler divergence) in root_registry.json.
Both ROOT-CAUSED-FIXED with live probe + full-regression evidence at
binary be95a47f797d3d99. Zero inflation: every claim dispositioned."""
import json

REG = '/home/z/my-project/root_registry.json'
d = json.load(open(REG))
ids = [r.get('id') for r in d['roots']]
assert 'F-NEW-268' not in ids and 'F-NEW-269' not in ids

row268 = {
    "id": "F-NEW-268",
    "status": "ROOT-CAUSED-FIXED",
    "title": (
        "EXCEPTION-SEMANTICS LAW FAMILY (five faces found stated-but-never-fixed in the "
        "engine and in issue #381's claims audit; each now fixed to the ART/JLS law): "
        "(a) aget on a NULL array ref answered a silent default instead of NPE — aput had "
        "carried the mirror arm since EXP-038 (asymmetry); (b) aget/aput on a CONFIRMED "
        "zero-length array (recorded __array_length__==0) warn-and-continued instead of "
        "AIOOBE — the old guard treated recorded-0 as 'length unknown'; the unknown-length "
        "legacy gate is preserved and now strictly means 'never recorded'; (c) new-array "
        "with negative size was silently CLAMPED to 0 instead of NegativeArraySizeException; "
        "(d) iget/iget-object on a null receiver answered the field default instead of NPE "
        "(ART order kept: field resolution first, then the null check); (e) `throw null` "
        "dispatched an exception object with class '<unknown>' instead of NPE at the throw "
        "site (JLS 14.18; probe face: ECJ folds a provable-null dereference into athrow of "
        "the null register itself). All arms reuse f141_is_null_receiver (F-141 + F-266a "
        "untyped-register law: NULL_REF / OBJECT_REF-id-0 / INT32-0) and "
        "raise_synthetic_exception (catch handlers + UNIFIED_011.3 propagation law) — no "
        "app-specific knowledge."
    ),
    "priority": "P1",
    "layer": "dex/exceptions+arrays+fields",
    "evidence": (
        "issue #381 claims audit (sections C/E: 'the current aget guard is insufficient "
        "for arr_len == 0', aget/iget NPE arms, new-array negative, 'write_v silent "
        "discard', class_to_superclass end() claim); source review at 8ee839e718877216 "
        "confirmed every face live in dalvik_engine.cpp before the fix. "
        "evidence/cont18g/CONT18G_FINAL_REVIEW.md"
    ),
    "probe": (
        "fixtures/f268_exception_probe (real aapt2/ECJ/D8; apk sha16 089eea98dbe6dee2): "
        "12/12 PASS at binary be95a47f797d3d99 — A new-array-neg NASE; B aget "
        "confirmed-zero AIOOBE; C aget null NPE; D aput confirmed-zero AIOOBE; E iget "
        "null-recv NPE; F/G in-bounds controls unchanged; H split trailing-empty law; "
        "I split empty-delim per-char law; J split Pattern.quote law; K split control; "
        "L throw-null NPE. Rows are method-isolated with instanceof-only handlers "
        "(ECJ folds provable-null derefs into athrow — the probe's own blackhole "
        "nulls exercise the real opcode paths)."
    ),
    "verified_current": (
        "full regression at be95a47f797d3d99: anchors 6/6 x3 = 18/18 MATCH "
        "byte-identical (dooz d602648e8e401895, microtimer da73010a37dd0189, unote "
        "4f1a9e4e8f64fae8, gmdice f3b483fe7b7cf51b, opencalc a976d2f9fb675cb3, chess "
        "b5a7a35d5fe0564b); fcol 18/18; f259 7/7; f259g 12/13 honest row-L unchanged; "
        "f266 6/6; negatives 19/19; reinstall matrix 8/8; skill 13/13."
    ),
}

row269 = {
    "id": "F-NEW-269",
    "status": "ROOT-CAUSED-FIXED",
    "title": (
        "STRING.SPLIT DUAL-HANDLER DIVERGENCE: the engine had TWO live String.split "
        "implementations in different dispatch layers (invoke-layer dalvik_engine.cpp "
        "~49143 EXP-071 Phase 6 site and bridge-layer ~52416 site) with DIVERGENT "
        "semantics — the invoke layer stripped the Pattern.quote \\Q..\\E wrapper, the "
        "bridge layer did not; the bridge layer answered whole-string for an empty "
        "delimiter while the invoke layer HUNG FOREVER (find(\"\") returns the current "
        "position, start never advances — issue #381's observed ~5s timeout face); both "
        "retained trailing empty elements against the JDK split(String)=limit-0 law. "
        "Fix: LAW PARITY in both layers — (1) \\Q..\\E strip, (2) empty delimiter = "
        "JDK zero-length-match per-char law, (3) trailing empty strings removed. "
        "Remaining structural note (DEFERRED): the two sites are now law-identical by "
        "construction+comment, but a single shared implementation is the eventual "
        "cleanup (mechanical refactor, no semantic delta)."
    ),
    "priority": "P2",
    "layer": "dex/strings",
    "evidence": (
        "issue #381 section B/C claims ('Two separate String.split handlers existed', "
        "'the old empty-delimiter split path was actually observed to hang', 'retained "
        "trailing empty elements'); source review at 8ee839e718877216 confirmed both "
        "sites live with the divergence. evidence/cont18g/CONT18G_FINAL_REVIEW.md"
    ),
    "probe": (
        "fixtures/f268_exception_probe rows H/I/J/K at be95a47f797d3d99: trailing-empty "
        "removal (a,b,, -> len 2), empty-delim per-char (ab -> [a,b], no hang), "
        "Pattern.quote literal law (x.y -> [x,y]), control unchanged — PASS in both "
        "dispatch layers via the same public API surface."
    ),
    "verified_current": (
        "anchors 18/18 x3 byte-identical + fcol 18/18 + f259 7/7 + f259g 12/13 honest + "
        "f266 6/6 + negatives 19/19 at be95a47f797d3d99 (split is corpus-wide: zero "
        "behavior drift on every coherent input the anchors exercise)."
    ),
}

d['roots'].append(row268)
d['roots'].append(row269)
d['total_roots'] = len(d['roots'])
d['total'] = len(d['roots'])
json.dump(d, open(REG, 'w'), indent=1, ensure_ascii=False)
print('registered F-NEW-268 + F-NEW-269; total rows =', len(d['roots']))
