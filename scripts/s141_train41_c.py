#!/usr/bin/env python3
"""s141_train41_c.py — TRAIN-41 probe C: the lambda-interface law.

(1) For Luq; and Lq;: dump the class_def's interface list + declared methods
    (which functional interface does each implement — Function2/3/N?).
(2) Census the interface method invoked by the materialize folder Lq;.h at
    its factory arm (pc=160 Lk90;.f) and by Lom;.d pc=41 (Lj90;.h).
(3) List ALL classes implementing those interfaces whose factory bodies
    contain invoke-static of any Lpm; member (the factory family map).
Usage: s141_train41_c.py <apk>
"""
import sys, zipfile, importlib.util

spec = importlib.util.spec_from_file_location(
    's41', '/home/z/my-project/scripts/s141_train41_disasm.py')
s41 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s41)
cd = s41.cd


def class_iface(d, off):
    n = d.u(off + 32 + 16, 4)  # interfaces_off in class_def (after 32-byte header? layout: class_idx u32, access u32, superclass u32, interfaces_off u32 ...)
    # class_def layout: class_idx(0) access_flags(4) superclass_idx(8) interfaces_off(12) source_file_idx(16) annotations_off(20) class_data_off(24) static_values_off(28)
    ifc_off = d.u(off + 12, 4)
    out = []
    if ifc_off:
        cnt = d.u(ifc_off, 4)
        for i in range(cnt):
            out.append(d.type_str(d.u(ifc_off + 4 + i * 2, 2)))
    sup = d.u(off + 8, 4)
    supname = d.type_str(sup) if sup != 0xFFFFFFFF else 'NO-SUPER'
    return supname, out


def class_methods_named(d, off):
    info = d.class_methods(off)
    rows = []
    for kind in ('direct', 'virtual'):
        for mname, mdesc, acc, sz, code in info[kind]:
            rows.append((kind, mname, mdesc, sz))
    return rows


def main():
    apk = sys.argv[1]
    z = zipfile.ZipFile(apk)
    for name in z.namelist():
        if not (name.startswith('classes') and name.endswith('.dex')):
            continue
        d = cd.Dex(z.read(name))
        for i in range(d.class_defs_size):
            off = d.class_defs_off + i * 32
            desc = d.type_str(d.u(off, 4))
            if desc in ('Luq;', 'Lq;', 'Lj90;', 'Lk90;', 'Lom;'):
                sup, ifaces = class_iface(d, off)
                print(f'CLASS {desc}: super={sup} ifaces={ifaces}')
                for kind, mn, md, sz in class_methods_named(d, off):
                    print(f'   {kind:8s} {mn}{md} insns={sz}')
                print()
        # interface surface of the compose functional interfaces
        for i in range(d.class_defs_size):
            off = d.class_defs_off + i * 32
            desc = d.type_str(d.u(off, 4))
            if desc in ('Lj90;', 'Lk90;'):
                pass  # printed above


if __name__ == '__main__':
    main()
