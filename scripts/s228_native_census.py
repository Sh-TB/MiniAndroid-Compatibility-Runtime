#!/usr/bin/env python3
"""S228 — native-route census metadata for the #582 GP mandate (comment 6821150791).

For every candidate APK: package/version/launch component (AXML parse),
SHA-256, ABI list (lib/<abi> dirs), per-library ELF SHA-256 + class/machine +
DT_NEEDED closure. Emits JSON + a markdown route-matrix fragment.

Route profile classes (mandate §3):
  JNI-only   — small JNI libs called from Java/Compose Activity (no engine)
  SDL2/SDL3  — SDL main-loop route (libmain + SDL libs)
  libGDX     — libgdx + box2d/freetype natives
  PURE-DEX   — no lib/*.so at all (control population)
"""
import hashlib
import json
import struct
import subprocess
import sys
import zipfile
from pathlib import Path

BASE = Path('/home/z/my-project')
APK_DIR = BASE / 'upload/canonical_apks'
OUT = BASE / 'evidence/s228_census'
OUT.mkdir(parents=True, exist_ok=True)

CANDIDATES = sorted(APK_DIR.glob('*.apk')) + [BASE / 'upload/chess_jwtc_298.apk']


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def elf_info(data: bytes) -> dict:
    """Parse ELF header + DT_NEEDED from a .so blob."""
    if len(data) < 64 or data[:4] != b'\x7fELF':
        return {'error': 'not-elf'}
    ei_class, ei_data = data[4], data[5]
    if ei_class == 1:  # ELF32
        e_machine = struct.unpack_from('<H', data, 18)[0]
        e_shoff = struct.unpack_from('<I', data, 32)[0]
        e_shentsize = struct.unpack_from('<H', data, 46)[0]
        e_shnum = struct.unpack_from('<H', data, 48)[0]
        fmt, off_e, sz_e = '<II', 0, 8
        fmt_s, off_s = '<IIIIIIIIII', 0
    else:  # ELF64
        e_machine = struct.unpack_from('<H', data, 18)[0]
        e_shoff = struct.unpack_from('<Q', data, 40)[0]
        e_shentsize = struct.unpack_from('<H', data, 58)[0]
        e_shnum = struct.unpack_from('<H', data, 60)[0]
        fmt, off_e, sz_e = '<QQ', 0, 16
        fmt_s, off_s = '<IIQQQQIIQQ', 0

    MACHINE = {3: 'x86', 62: 'x86_64', 40: 'arm', 183: 'aarch64'}

    # locate .dynamic + .dynstr via section headers
    dyn, dynstr = None, None
    for i in range(e_shnum):
        base = e_shoff + i * e_shentsize
        if base + 64 > len(data):
            break
        if ei_class == 1:
            sh_name, sh_type = struct.unpack_from('<II', data, base)
            sh_offset, sh_size = struct.unpack_from('<II', data, base + 16)
            sh_link = struct.unpack_from('<I', data, base + 24)[0]
        else:
            sh_name, sh_type = struct.unpack_from('<II', data, base)
            sh_offset, sh_size = struct.unpack_from('<QQ', data, base + 24)
            sh_link = struct.unpack_from('<I', data, base + 40)[0]
        if sh_type == 6:  # SHT_DYNAMIC
            dyn = (sh_offset, sh_size, sh_link)
        elif sh_type == 3:  # SHT_STRTAB (dynstr candidate)
            if dyn is not None and dynstr is None and sh_link == 0:
                pass
    if dyn is None:
        return {'machine': MACHINE.get(e_machine, e_machine), 'dt_needed': [],
                'note': 'no SHT_DYNAMIC (static or stripped sections)'}

    doff, dsize, dlink = dyn
    # find the linked strtab section
    strtab_off, strtab_sz = None, None
    for i in range(e_shnum):
        base = e_shoff + i * e_shentsize
        if base + 64 > len(data):
            break
        if ei_class == 1:
            sh_type = struct.unpack_from('<II', data, base)[1]
            sh_offset, sh_size = struct.unpack_from('<II', data, base + 16)
        else:
            sh_type = struct.unpack_from('<II', data, base)[1]
            sh_offset, sh_size = struct.unpack_from('<QQ', data, base + 24)
        if i == dlink and sh_type in (2, 3):
            strtab_off, strtab_sz = sh_offset, sh_size
    needed = []
    entsz = 8 if ei_class == 1 else 16
    for o in range(doff, min(doff + dsize, len(data)) - entsz + 1, entsz):
        if ei_class == 1:
            tag, val = struct.unpack_from('<iI', data, o)
        else:
            tag, val = struct.unpack_from('<qQ', data, o)
        if tag == 0:
            break
        if tag == 1:  # DT_NEEDED
            if strtab_off is not None and val < strtab_sz:
                s = data[strtab_off + val: strtab_off + strtab_sz]
                needed.append(s.split(b'\0')[0].decode('ascii', 'replace'))
    return {'machine': MACHINE.get(e_machine, e_machine),
            'class': 'ELF32' if ei_class == 1 else 'ELF64',
            'dt_needed': needed}


def parse_axml(axml: bytes) -> dict:
    """Minimal binary AXML walker: string pool + start elements + attributes."""
    if axml[:4] != b'\x03\x00\x08\x00' and struct.unpack_from('<H', axml, 0)[0] != 0x0003:
        return {'error': 'not RES_XML_TYPE'}
    strings = []
    off = 8
    total = len(axml)
    while off + 8 <= total:
        ctype, hdrsz, size = struct.unpack_from('<HHI', axml, off)
        if ctype == 0x0001:  # string pool
            strcount, stylecount, flags, sstart, stylstart = \
                struct.unpack_from('<IIIII', axml, off + 8)
            utf8 = bool(flags & (1 << 8))
            offs = [struct.unpack_from('<I', axml, off + hdrsz + 4 * i)[0]
                    for i in range(strcount)]
            data0 = off + sstart
            for o in offs:
                p = data0 + o
                if utf8:
                    u16len = axml[p]
                    u8len = axml[p + 1]
                    s = axml[p + 2: p + 2 + u8len].decode('utf-8', 'replace')
                else:
                    ln = struct.unpack_from('<H', axml, p)[0]
                    s = axml[p + 2: p + 2 + 2 * ln].decode('utf-16-le', 'replace')
                strings.append(s)
        elif ctype == 0x0102:  # start element
            name_ref = struct.unpack_from('<i', axml, off + 20)[0]
            attr_start = struct.unpack_from('<H', axml, off + 24)[0]
            attr_size = struct.unpack_from('<H', axml, off + 26)[0]
            attr_count = struct.unpack_from('<H', axml, off + 28)[0]
            elname = strings[name_ref] if 0 <= name_ref < len(strings) else '?'
            attrs = {}
            for i in range(attr_count):
                b = off + 16 + attr_start + i * attr_size
                ans, anm, araw = struct.unpack_from('<iii', axml, b)
                dt = axml[b + 15]
                d = struct.unpack_from('<I', axml, b + 16)[0]
                nm = strings[anm] if 0 <= anm < len(strings) else '?'
                val = (strings[araw] if 0 <= araw < len(strings)
                       and araw != -1 else (d if dt in (0x10, 0x11) else d))
                attrs[nm] = val
            yield_ = {'el': elname, 'attrs': attrs}
            yield_el = yield_
            axml_events.append(yield_el)
        off += size if size else 8
    return {}


def axml_manifest(apk: Path) -> dict:
    """Extract package / versionCode / launch activity from binary AXML."""
    global axml_events
    with zipfile.ZipFile(apk) as z:
        axml = z.read('AndroidManifest.xml')
    axml_events = []
    parse_axml(axml)
    ev = axml_events
    out = {}
    for e in ev:
        if e['el'] == 'manifest':
            out['package'] = e['attrs'].get('package')
            out['versionCode'] = e['attrs'].get('versionCode')
            out['versionName'] = e['attrs'].get('versionName')
    # walk activity nodes; collect intent-filter action/category children
    launch = []
    cur_act = None
    depth_act = -1
    depth_filter = -1
    has_main = has_launcher = False
    for e in ev:
        if e['el'] == 'activity':
            cur_act = e['attrs'].get('name')
            depth_act = 0
            has_main = has_launcher = False
        elif e['el'] == 'intent-filter' and cur_act:
            depth_filter = 0
        elif e['el'] == 'action' and cur_act:
            a = e['attrs'].get('name', '')
            if a == 'android.intent.action.MAIN':
                has_main = True
        elif e['el'] == 'category' and cur_act:
            a = e['attrs'].get('name', '')
            if a == 'android.intent.category.LAUNCHER':
                has_launcher = True
        if cur_act and has_main and has_launcher and cur_act not in launch:
            launch.append(cur_act)
    out['launcher_activities'] = launch
    out['all_activities'] = [e['attrs'].get('name') for e in ev
                             if e['el'] == 'activity'][:12]
    # application label
    for e in ev:
        if e['el'] == 'application':
            out['app_label'] = e['attrs'].get('label')
            break
    return out


axml_events = []


def main():
    rows = []
    for apk in CANDIDATES:
        if not apk.exists():
            continue
        row = {'apk': str(apk.relative_to(BASE)),
               'apk_sha256_16': sha256_file(apk)[:16],
               'size': apk.stat().st_size}
        try:
            with zipfile.ZipFile(apk) as z:
                libs = sorted(n for n in z.namelist()
                              if n.startswith('lib/') and n.endswith('.so'))
                abis = sorted({n.split('/')[1] for n in libs})
                row['abis'] = abis
                row['libs'] = {}
                for n in libs:
                    data = z.read(n)
                    info = elf_info(data)
                    info['sha256_16'] = hashlib.sha256(data).hexdigest()[:16]
                    info['size'] = len(data)
                    row['libs'][n] = info
                row['route'] = (
                    'PURE-DEX' if not libs else
                    'libGDX' if any('libgdx' in n for n in libs) else
                    'SDL3' if any('SDL3' in n for n in libs) else
                    'SDL2' if any('SDL2' in n for n in libs) else
                    'JNI-libs')
                if 'AndroidManifest.xml' in z.namelist():
                    row['manifest'] = axml_manifest(apk)
        except Exception as e:
            row['error'] = repr(e)
        rows.append(row)
        print(f"{row['apk']}: route={row.get('route')} abis={row.get('abis')} "
              f"libs={len(row.get('libs', {}))}")

    (OUT / 'native_census.json').write_text(json.dumps(rows, indent=1))
    print(f"\nwrote {OUT/'native_census.json'} ({len(rows)} rows)")


if __name__ == '__main__':
    main()
