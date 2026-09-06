#!/usr/bin/env python3
"""
g12_dex_ctor_audit.py — G11/G12 Phase 1: audit app-code View/ViewGroup
CONSTRUCTOR bodies + onCreate for the evidence subset. Answers per APK:
  * which constructors exist (<init> signatures) on custom view classes
  * whether they call super(...) / addView / inflate / findViewById
  * whether onCreate performs programmatic addView / new-instance+init
Standard DEX parsing only. Evidence → docs/evidence/g11g12_evidence/.

Usage: python3 g12_dex_ctor_audit.py
"""
import json
import struct
import sys
import zipfile
from pathlib import Path

REPO = Path("/home/z/my-project/MiniAndroid-Compatibility-Runtime")
CACHE = REPO / "miniandroid" / "download"
OUT = REPO / "docs" / "evidence" / "g11g12_evidence"

TARGETS = {
    "org.debian.eugen.headingcalculator_1.apk":
        ["Lorg/debian/eugen/headingcalculator/CalculatorDisplay;",
         "Lorg/debian/eugen/headingcalculator/CalculatorKeypad;",
         "Lorg/debian/eugen/headingcalculator/ExplainableButton;",
         "Lorg/debian/eugen/headingcalculator/ExplainableTextView;",
         "Lorg/debian/eugen/headingcalculator/MainActivity;"],
    "dubrowgn.microtimer_8.apk":
        ["Ldubrowgn/microtimer/RoTimeControl;",
         "Ldubrowgn/microtimer/MicroTimerActivity;",  # guess; auto-added below
         "Lk/g;"],
    "omegacentauri.mobi.simplestopwatch_26.apk":
        ["Lomegacentauri/mobi/simplestopwatch/BigTextView;",
         "Lomegacentauri/mobi/simplestopwatch/ShowTime;"],
}

FORMAT_SIZE = {
    '10x': 1, '10t': 1, '11x': 1, '11n': 1, '12x': 1,
    '20t': 2, '21s': 2, '21h': 2, '21c': 2, '21t': 2, '22x': 2,
    '22b': 2, '22s': 2, '22c': 2, '22t': 2, '23x': 2,
    '30t': 3, '31i': 3, '31t': 3, '31c': 3, '32x': 3,
    '35c': 3, '3rc': 3, '51l': 5,
}

# opcode -> (name, format); only the ones needed for call-site analysis
OPCODES = {
    0x00: ('nop', '10x'), 0x01: ('move', '12x'), 0x02: ('move/from16', '22x'),
    0x07: ('move-object', '12x'), 0x08: ('move-object/from16', '22x'),
    0x0a: ('move-result', '11x'), 0x0c: ('move-result-object', '11x'),
    0x0e: ('return-void', '10x'), 0x0f: ('return', '11x'),
    0x11: ('return-object', '11x'), 0x12: ('const/4', '11n'),
    0x13: ('const/16', '21s'), 0x14: ('const', '31i'), 0x15: ('const/high16', '21h'),
    0x1a: ('const-string', '21c'), 0x1c: ('const-class', '21c'),
    0x1f: ('check-cast', '21c'), 0x20: ('instance-of', '22c'),
    0x22: ('new-instance', '21c'), 0x23: ('new-array', '22c'),
    0x27: ('goto', '10t'), 0x28: ('goto/16', '20t'), 0x29: ('goto/32', '30t'),
    0x2b: ('packed-switch', '31t'), 0x2c: ('sparse-switch', '31t'),
    0x52: ('iget', '22c'), 0x54: ('iget-object', '22c'),
    0x59: ('iput', '22c'), 0x5a: ('iput-object', '22c'),
    0x5f: ('sget', '21c'), 0x60: ('sget-object', '21c'),
    0x62: ('sget-object', '21c'), 0x67: ('sput', '21c'), 0x69: ('sput-object', '21c'),
    0x6e: ('invoke-virtual', '35c'), 0x6f: ('invoke-super', '35c'),
    0x70: ('invoke-direct', '35c'), 0x71: ('invoke-static', '35c'),
    0x72: ('invoke-interface', '35c'),
    0x74: ('invoke-virtual/range', '3rc'), 0x75: ('invoke-super/range', '3rc'),
    0x76: ('invoke-direct/range', '3rc'), 0x77: ('invoke-static/range', '3rc'),
    0x78: ('invoke-interface/range', '3rc'),
    0x0b: ('move-result-wide', '11x'), 0x09: ('move-object/16', '32x'),
    0x03: ('move/16', '32x'), 0x04: ('move-wide', '12x'),
    0x05: ('move-wide/from16', '22x'), 0x06: ('move-wide/16', '32x'),
    0x0d: ('move-exception', '11x'), 0x16: ('const-wide/16', '21s'),
    0x18: ('const-wide', '51l'), 0x19: ('const-wide/high16', '21h'),
    0x1b: ('const-string/jumbo', '31c'), 0x1d: ('monitor-enter', '11x'),
    0x1e: ('monitor-exit', '11x'), 0x21: ('array-length', '12x'),
    0x24: ('filled-new-array', '35c'), 0x25: ('fill-array-data', '31t'),
    0x26: ('throw', '11x'), 0x2a: ('sparse-switch', '31t'),
    0x51: ('iget-wide', '22c'), 0x53: ('iget-boolean', '22c'),
    0x55: ('iget-wide', '22c'), 0x56: ('iget-boolean', '22c'),
    0x57: ('iget-byte', '22c'), 0x58: ('iget-char', '22c'),
    0x5b: ('iput-wide', '22c'), 0x5c: ('iput-boolean', '22c'),
    0x5d: ('iput-byte', '22c'), 0x5e: ('iput-char', '22c'),
    0x61: ('sget', '21c'), 0x63: ('sget-wide', '21c'),
    0x64: ('sget-boolean', '21c'), 0x65: ('sget-byte', '21c'),
    0x66: ('sget-char', '21c'), 0x68: ('sput-wide', '21c'),
    0x6a: ('sput-boolean', '21c'), 0x6b: ('sput-byte', '21c'),
    0x6c: ('sput-char', '21c'),
    0x79: ('unused', '10x'), 0x7a: ('unused', '10x'),
    # arithmetic — treat generically (size only)
}
for _op in range(0x7b, 0x90):
    OPCODES.setdefault(_op, (f'op-{_op:#04x}', '12x'))
for _op in range(0x90, 0xb0):
    OPCODES.setdefault(_op, (f'op-{_op:#04x}', '23x'))
for _op in range(0xb0, 0xd0):
    OPCODES.setdefault(_op, (f'op-{_op:#04x}', '12x'))


class Dex:
    def __init__(self, data: bytes):
        self.d = data
        self.n_str, = struct.unpack_from("<I", data, 0x38)
        self.off_str, = struct.unpack_from("<I", data, 0x3c)
        self.n_type, self.off_type = struct.unpack_from("<II", data, 0x40)
        self.n_proto, self.off_proto = struct.unpack_from("<II", data, 0x48)
        self.n_field, self.off_field = struct.unpack_from("<II", data, 0x50)
        self.n_meth, self.off_meth = struct.unpack_from("<II", data, 0x58)
        self.n_cls, self.off_cls = struct.unpack_from("<II", data, 0x60)

    def uleb(self, off):
        r = s = 0
        while True:
            b = self.d[off]
            off += 1
            r |= (b & 0x7F) << s
            if not (b & 0x80):
                return r, off
            s += 7

    def s(self, idx):
        if idx >= self.n_str:
            return f"?str{idx}"
        so = struct.unpack_from("<I", self.d, self.off_str + idx * 4)[0]
        _, p = self.uleb(so)
        e = self.d.index(b"\x00", p)
        return self.d[p:e].decode("utf-8", "replace")

    def t(self, idx):
        if idx >= self.n_type:
            return f"?type{idx}"
        si = struct.unpack_from("<I", self.d, self.off_type + idx * 4)[0]
        return self.s(si)

    def proto(self, idx):
        base = self.off_proto + idx * 12
        shorty, ret, params = struct.unpack_from("<III", self.d, base)
        out = "("
        if params:
            n, p = self.uleb(params)
            for i in range(n):
                out += self.t(struct.unpack_from("<H", self.d, p + i * 2)[0])
        return out + ")" + self.t(ret)

    def method(self, idx):
        base = self.off_meth + idx * 8
        cls, p, name = struct.unpack_from("<HHI", self.d, base)
        return self.t(cls), self.s(name), self.proto(p)

    def field(self, idx):
        base = self.off_field + idx * 8
        cls, t, name = struct.unpack_from("<HHI", self.d, base)
        return self.t(cls), self.s(name), self.t(t)

    def class_methods(self, cls_desc):
        """yield (name, proto, code_off, regs, ins, code) for direct+virtual."""
        for i in range(self.n_cls):
            base = self.off_cls + i * 32
            cidx = struct.unpack_from("<I", self.d, base)[0]
            if self.t(cidx) != cls_desc:
                continue
            (class_data_off,) = struct.unpack_from("<I", self.d, base + 24)
            if not class_data_off:
                return
            off = class_data_off
            sf, off = self.uleb(off)
            inf, off = self.uleb(off)
            dm, off = self.uleb(off)
            vm, off = self.uleb(off)
            # SKIP the static_fields + instance_fields lists
            # (diff uleb idx + access flags uleb per entry)
            for _ in range(sf + inf):
                _fidx, off = self.uleb(off)
                _acc, off = self.uleb(off)
            dm_off = 0
            for _ in range(dm):
                midx, k2 = self.uleb(off); off = k2
                acc, k2 = self.uleb(off); off = k2
                code_off, k2 = self.uleb(off); off = k2
                dm_off += midx
                yield ("direct",) + self.method(dm_off) + (code_off,)
            vm_off = 0
            for _ in range(vm):
                midx, k2 = self.uleb(off); off = k2
                acc, k2 = self.uleb(off); off = k2
                code_off, k2 = self.uleb(off); off = k2
                vm_off += midx
                yield ("virtual",) + self.method(vm_off) + (code_off,)
            return

    def code_item(self, code_off):
        if code_off == 0:
            return None
        regs, ins, outs, tries, dbg, insns_size = struct.unpack_from(
            "<HHHHII", self.d, code_off)
        insns = self.d[code_off + 16:code_off + 16 + insns_size * 2]
        return regs, ins, outs, insns

    def disasm_calls(self, insns: bytes):
        """Return (calls, news, strings). Authoritative size table from the
        Dalvik bytecode format spec; skips pseudo payloads."""
        calls, news, strs = [], [], []
        u16 = lambda o: struct.unpack_from("<H", insns, o)[0]
        u32 = lambda o: struct.unpack_from("<I", insns, o)[0]

        def size_of(op):
            if op <= 0x0d: return 1
            if op <= 0x11: return 1
            if op == 0x12: return 1
            if op in (0x13, 0x15, 0x16, 0x19, 0x1a, 0x1c, 0x1f, 0x20,
                      0x22, 0x23): return 2
            if op in (0x14, 0x17, 0x1b, 0x24, 0x25, 0x26, 0x29, 0x2a,
                      0x2b, 0x2c): return 3
            if op == 0x18: return 5
            if op in (0x1d, 0x1e, 0x21, 0x27, 0x28): return 1
            if 0x2d <= op <= 0x31: return 2
            if 0x32 <= op <= 0x37: return 2
            if 0x38 <= op <= 0x3d: return 3
            if 0x3e <= op <= 0x43: return 1
            if 0x44 <= op <= 0x51: return 2
            if 0x52 <= op <= 0x5f: return 2   # 22c (iget/iput)
            if 0x60 <= op <= 0x6d: return 2   # 21c (sget/sput/const-class..)
            if 0x6e <= op <= 0x72: return 3   # 35c
            if op == 0x73: return 1
            if 0x74 <= op <= 0x78: return 3   # 3rc
            if op in (0x79, 0x7a): return 1
            if 0x7b <= op <= 0x8f: return 1   # 12x unop
            if 0x90 <= op <= 0xaf: return 2   # 23x binop
            if 0xb0 <= op <= 0xcf: return 1   # 12x/2addr
            if 0xd0 <= op <= 0xd7: return 2   # 22s
            if 0xd8 <= op <= 0xe2: return 3   # 22b
            return 1

        INVOKE = set(range(0x6e, 0x73)) | set(range(0x74, 0x79))
        off = 0
        n = len(insns) // 2
        while off < n:
            unit0 = u16(off * 2)
            op = unit0 & 0xFF
            if op == 0x00 and unit0 in (0x0100, 0x0200, 0x0300):
                if unit0 == 0x0300:  # fill-array-data payload
                    ew = u16(off * 2 + 2)
                    size = u32(off * 2 + 4)
                    off += (8 + size * ew + 1) // 2
                    continue
                size = u16(off * 2 + 2)
                # sparse: 4B hdr + size*8 bytes; packed: 8B hdr + size*4 bytes
                nbytes = (4 + size * 8) if unit0 == 0x0200 else (8 + size * 4)
                off += (nbytes + 1) // 2
                continue
            if op in INVOKE:
                bidx = u16(off * 2 + 2)
                if bidx >= self.n_meth:
                    # desync indicator — do not crash; record and skip 1 unit
                    print(f"  [desync] op={op:#04x} off={off:#x} bidx={bidx} "
                          f"n_meth={self.n_meth}", file=sys.stderr)
                    off += 1
                    continue
                cls, mname, proto = self.method(bidx)
                kind = {0x6e: 'invoke-virtual', 0x6f: 'invoke-super',
                        0x70: 'invoke-direct', 0x71: 'invoke-static',
                        0x72: 'invoke-interface', 0x74: 'invoke-virtual/range',
                        0x75: 'invoke-super/range', 0x76: 'invoke-direct/range',
                        0x77: 'invoke-static/range',
                        0x78: 'invoke-interface/range'}[op]
                calls.append((off, kind, f"{cls}->{mname}{proto}"))
            elif op == 0x22:  # new-instance 21c
                bidx = u16(off * 2 + 2)
                news.append((off, self.t(bidx)))
            elif op in (0x1a, 0x1b):  # const-string 21c / jumbo 31c
                bidx = u16(off * 2 + 2) if op == 0x1a else u32(off * 2 + 2)
                strs.append((off, self.s(bidx)))
            off += size_of(op)
        return calls, news, strs


def audit_apk(apk_name: str, classes: list[str]) -> dict:
    hits = list(CACHE.rglob(apk_name))
    if not hits:
        return {"apk": apk_name, "error": "not found"}
    rec = {"apk": apk_name, "classes": {}}
    with zipfile.ZipFile(hits[0]) as z:
        dex_names = sorted(n for n in z.namelist() if n.endswith(".dex"))
        for cls in classes:
            found = False
            for dn in dex_names:
                dx = Dex(z.read(dn))
                ms = list(dx.class_methods(cls))
                if not ms:
                    continue
                found = True
                entry = {"dex": dn, "methods": {}}
                for kind, _cls, mname, proto, code_off in ms:
                    item = dx.code_item(code_off)
                    if not item:
                        continue
                    regs, ins, outs, insns = item
                    calls, news, strs = dx.disasm_calls(insns)
                    interesting = [
                        {"off": o, "op": op, "target": tgt}
                        for o, op, tgt in calls
                        if any(k in tgt for k in
                               ("addView", "inflate", "setContentView",
                                "findViewById", "<init>", "setOrientation",
                                "removeAllViews", "setWillNotDraw", "onMeasure",
                                "setMeasuredDimension", "drawText", "setText",
                                "requestLayout", "invalidate"))]
                    entry["methods"][f"{mname}{proto} [{kind}]"] = {
                        "regs": regs, "ins": ins, "code_units": len(insns) // 2,
                        "interesting_calls": interesting[:60],
                        "new_instances": [c for _o, c in news][:40],
                        "strings": [s for _o, s in strs][:40],
                    }
                rec["classes"][cls] = entry
                break
            if not found:
                rec["classes"][cls] = {"error": "class not found"}
    return rec


def main():
    out = {}
    for apk, classes in TARGETS.items():
        print(f"===== {apk}")
        rec = audit_apk(apk, classes)
        out[apk] = rec
        for cls, cdata in rec["classes"].items():
            print(f"  {cls}")
            for sig, m in cdata.get("methods", {}).items():
                calls = m["interesting_calls"]
                print(f"    {sig} regs={m['regs']} ins={m['ins']} "
                      f"code={m['code_units']}")
                for c in calls[:40]:
                    print(f"      @{c['off']:5d} {c['op']:22s} {c['target']}")
                if m["new_instances"]:
                    print(f"      new: {m['new_instances'][:12]}")
    (OUT / "g12_ctor_audit.json").write_text(json.dumps(out, indent=1))
    print(f"\nwrote {OUT / 'g12_ctor_audit.json'}")


if __name__ == "__main__":
    main()
