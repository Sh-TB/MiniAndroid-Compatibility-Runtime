#!/usr/bin/env python3
"""Full AXML element walk: print every START/END element name in order."""
import struct, sys, zipfile

apk = sys.argv[1]
with zipfile.ZipFile(apk) as z:
    data = z.read("AndroidManifest.xml")

pos = 8  # skip file header (type,size) + xml header chunk
strings = []
def parse_string_pool(d, i):
    typ, hsz, size = struct.unpack('<HHI', d[i:i+8])
    assert typ == 0x0001, hex(typ)
    scount, _ = struct.unpack('<II', d[i+8:i+16])
    flags, sstart, _ = struct.unpack('<III', d[i+16:i+28])
    base = i + sstart
    out = []
    for k in range(scount):
        o = struct.unpack('<I', d[i+hsz+4*k:i+hsz+4*k+4])[0]
        p = base + o
        if flags & 0x100:  # UTF-8: utf16_len, utf8_len, bytes
            nl = d[p]; n = d[p+1] if nl & 0x80 else nl
            s = d[p+2:p+2+n].decode('utf-8', 'replace')
        else:
            n = struct.unpack('<H', d[p:p+2])[0] & 0x7FFFFFFF
            s = d[p+2:p+2+2*n].decode('utf-16-le', 'replace')
        out.append(s)
    return out

while pos < len(data):
    typ, hsz, size = struct.unpack('<HHI', data[pos:pos+8])
    typ &= 0xFFFF
    if typ == 0x0001:
        strings = parse_string_pool(data, pos)
        print(f"# string pool: {len(strings)} strings")
    elif typ == 0x0102:  # START_ELEMENT
        # header: type,size,linenumber,comment | ns(name),name(name),attrStart,attrSize,attrCount...
        name_idx = struct.unpack('<I', data[pos+20:pos+24])[0]
        attr_count = struct.unpack('<H', data[pos+32:pos+34])[0]
        nm = strings[name_idx] if name_idx < len(strings) else f"?{name_idx}"
        attrs = []
        abase = pos + 36
        for k in range(attr_count):
            o = abase + k*20
            ans, an, rawv = struct.unpack('<III', data[o:o+12])
            at = struct.unpack('<H', data[o+14:o+16])[0] & 0xFF
            av = data[o+16:o+20]
            aval = strings[rawv] if (at == 3 and rawv < len(strings)) else (
                str(struct.unpack('<i', av)[0]) if at == 0x10 else
                ("bool:"+str(struct.unpack('<I', av)[0]) if at == 0x12 else f"t{at}"))
            aname = strings[an] if an < len(strings) else f"?{an}"
            attrs.append(f"{aname}={aval}")
        print(f"START {nm} [{'; '.join(attrs[:6])}]")
    elif typ == 0x0103:
        name_idx = struct.unpack('<I', data[pos+20:pos+24])[0]
        print(f"END   {strings[name_idx] if name_idx < len(strings) else '?'}")
    pos += size
