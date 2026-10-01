#!/usr/bin/env python3
"""FINAL CAMPAIGN Phase 3 wave 1 — registry bookkeeping: append F-NEW-170/171
to root_registry.json (both copies) + canonical/master_worklist.json.

Honest wave-close states:
  F-NEW-170 StandardCharsets platform law      ROOT-CAUSED-FIXED this wave
  F-NEW-170b (same entry) clinit-honesty       recorded residual (EIIIE law)
  F-NEW-171 DEX register-width law             ROOT-CAUSED-FIXED (move-object/16
                                               opcode + uint16 accessor width +
                                               write_p param_start truncation)
  F-NEW-172 createHashTable probe spin         NEW (observed, next frontier):
                                               RegularImmutableMap.createHashTable
                                               hash-probe loop spins 50001+ and
                                               trips F084 — bounded investigation
                                               queued (aget-byte/aput-byte [B
                                               semantics or table-size feed).
"""
import json
from pathlib import Path

BASE = Path('/home/z/my-project')

ENTRIES = [
    {
        'id': 'F-NEW-170', 'status': 'ROOT-CAUSED-FIXED', 'priority': 'P0',
        'summary': 'StandardCharsets platform-constant law: the engine had no '
                   'Ljava/nio/charset/StandardCharsets; statics, so sget UTF_8 '
                   'answered null; WhatsApp 08D.<clinit> invoked Charset.name() '
                   'on that null; 08C.<clinit> died leaving its static Set '
                   'fields unwritten (SGET-MISS -> null) and the downstream '
                   'Set.contains NPE chain killed Main.onCreate (white screen). '
                   'Fix: sget arm materializes the six JDK constants as heap '
                   'Charset objects (__charset_name__) under the same identity '
                   'as the Charset.forName law. Residual (recorded, own wave): '
                   'clinit-failure honesty — the engine records CLASS_INIT '
                   'result=OK even when the clinit frame unwound; ART law is '
                   'class-erroneous + ExceptionInInitializerError on access.',
        'evidence': 'FINAL-CAMPAIGN Phase 3 wave 1: wa_full.log lines 988-997 '
                    '(SGET-MISS StandardCharsets.UTF_8 -> SYNTH-EXC Charset.name '
                    'null -> 08C unwind); post-fix wa_full2.log: StandardCharsets '
                    'SGET-MISS count=0, Set.contains face GONE. Gates: laws130 '
                    '51/51, dooz ba8a95eb2278594f x3, stopwatch_6 eb16ab5c68fa9b6c x3.',
        'layer': 'DEX/JVM statics + java.nio.charset',
    },
    {
        'id': 'F-NEW-171', 'status': 'ROOT-CAUSED-FIXED', 'priority': 'P0',
        'summary': 'DEX register-width law (three faces, one root): (1) opcode '
                   '0x09 move-object/16 was DEFINED but had NO interpreter case '
                   '— the default arm skipped 1 unit instead of 3, desyncing pc '
                   '(07r.<init> @0x5a garbage decode -> new-instance 00D flow '
                   'corrupted -> "invoke 00D.<init> on null"); (2) DexRegisterFile '
                   'accessors were uint8_t — /16 formats (emitted exactly when '
                   'reg indices exceed 255) truncated v256+ onto v0.. (register '
                   'ALIASING: Builder.put receiver became a boxed Integer); '
                   '(3) write_p computed the ABSOLUTE register as uint8_t '
                   'param_start_+idx — methods with >255 regs landed arguments '
                   '(incl. this) in wrong registers. Fix: move-object/16 handler '
                   '(32x, 3 units); read_v/write_v/get_register/set_register/'
                   'set_wide_pair widened to uint16_t; written_bits_ 4->16 words; '
                   'write_p/read_p absolute-register arithmetic widened to uint32.',
        'evidence': 'FINAL-CAMPAIGN Phase 3 wave 1: wa_full2.log 1416-1419 '
                    '(UNIMPL-DIAG 07r @0x5a + 00D-null); wa_full4.log IGET-MISS-'
                    'DIAG "asked=Builder->size obj#21003 cls=Ljava/lang/Integer" '
                    '(register aliasing smoking gun); wa_full5/6.log: 00D-null '
                    'count 0, chain advanced deep into 07r.A0Q -> ImmutableMap '
                    'build. Gates: laws130 51/51, dooz x3 byte-identical, '
                    'stopwatch_6 x3.',
        'layer': 'DEX interpreter / register file',
    },
    {
        'id': 'F-NEW-172', 'status': 'OBSERVED-FAIL', 'priority': 'P0',
        'summary': 'RegularImmutableMap.createHashTable hash-probe loop spins '
                   '>50001 visits (F084 halt) during WhatsApp 07r.A0Q MobileConfig '
                   'map build. The loop is O(tableSize) in guava — a real run '
                   'never spins. Candidate semantics: [B aget-byte/aput-byte/'
                   'Arrays.fill byte-table state or the if-ge exit comparison on '
                   'the entry count; bounded disassembly-driven investigation '
                   'queued (createHashTable 341 units, spin PC=0xaf, op 0xb5).',
        'evidence': 'FINAL-CAMPAIGN Phase 3 wave 1: wa_full6.log 1470-1476 '
                    '(PROGRESS 700k-1.1M instructions inside createHashTable -> '
                    'HALT-LOOP visited 50001); disasm run/cht_disasm.txt.',
        'layer': 'DEX interpreter / array + loop semantics',
    },
]


def main():
    updated = []
    for rel in ['canonical/root_cause_registry.json', 'root_registry.json']:
        p = BASE / rel
        if not p.exists():
            continue
        d = json.load(open(p))
        roots = d.get('roots')
        if roots is None:
            continue
        existing = {r.get('id') for r in roots}
        for e in ENTRIES:
            if e['id'] in existing:
                for r in roots:
                    if r.get('id') == e['id']:
                        r.update({k: v for k, v in e.items() if k != 'id'})
                        break
            else:
                roots.append(dict(e, title=e['id'], law=None))
        d['total'] = len(roots)
        with open(p, 'w') as f:
            json.dump(d, f, indent=1)
        updated.append(f'{rel}: {len(roots)} roots')
    print(' | '.join(updated))


if __name__ == '__main__':
    main()
