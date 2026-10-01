#!/usr/bin/env python3
"""S112: decode dalvik bytecode of WebViewFeatureInternal.isSupported — find the divergent call."""
import struct, sys
sys.path.insert(0, '/home/z/my-project/scripts')
from s112_dexdump import Dex

d = Dex('/home/z/my-project/external_backup/s112/blid/classes.dex')  # Phase-1 hygiene: tmp/ payload moved out of git (SHA256 c4ca8802a0992675042dfe2e1e7de7d2b43fe81f3648bfa8e80390a58269e88e, ledger docs/history/final_campaign_phase1/)
b = d.b

def mname(idx):
    cls_idx, _, name_idx = struct.unpack_from('<HHI', b, d.method_ids_off + idx*8)
    return d.type_at(cls_idx) + '->' + d.str_at(name_idx)
def tname(idx):
    return d.type_at(idx)
def fname(idx):
    _, t_idx, n_idx = struct.unpack_from('<HHI', b, d.field_ids_off + idx*8)
    return d.str_at(n_idx) + ':' + d.type_at(t_idx)

off = d.find_class('Landroidx/webkit/internal/WebViewFeatureInternal;')
code_off = None
for kind, cn, mn, co in d.class_methods(off):
    if mn == 'isSupported' and co == 0x260d3c:
        code_off = co
units = d.code_units(code_off)

OPS = {
    0x00:('nop',0),0x0a:('move-result',1),0x0b:('move-result-wide',1),
    0x0c:('move-result-object',1),0x0f:('return',1),0x11:('return-object',1),
    0x1a:('const-string',2),0x1b:('const-string/jumbo',3),0x13:('const/16',2),
    0x12:('const/4',1),0x14:('const',3),0x1f:('const-class',2),
    0x22:('new-instance',2),0x23:('new-array',2),0x62:('sget-object',2),
    0x60:('sget',2),0x66:('sput-object',2),0x54:('iget-object',2),
    0x2b:('packed-switch',3),0x2c:('sparse-switch',3),
    0x28:('goto',1),0x29:('goto/16',2),0x32:('if-eq',3),0x33:('if-ne',3),
    0x35:('if-ge',3),0x36:('if-gt',3),0x37:('if-le',3),0x34:('if-lt',3),
    0x38:('if-eqz',2),0x39:('if-nez',2),0x3a:('if-ltz',2),0x3b:('if-gez',2),
    0x6e:('invoke-virtual-range',3),0x6f:('invoke-super-range',3),
    0x70:('invoke-direct',3),0x71:('invoke-static',3),0x72:('invoke-virtual',3),
    0x74:('invoke-virtual-range',3),0x77:('invoke-static-range',3),
    0x21:('array-length',1),0x44:('aget',2),0x46:('aget-object',2),
    0x4b:('aput',2),0x4d:('aput-object',2),0x05:('move',1),0x07:('move-object',2),
}
pc = 0
out = []
while pc < len(units):
    u = units[pc]
    op = u & 0xFF
    name, size = OPS.get(op, ('op-%02x' % op, (u >> 8) & 0xFF if op < 0x100 else 1))
    line = 'pc=%3d %s' % (pc, name)
    if name == 'new-instance':
        line += ' v%d %s' % ((u >> 8) & 0xFF, tname(units[pc+1]))
    elif name in ('invoke-direct','invoke-static','invoke-virtual'):
        line += ' {v%d..}' % (u & 0xF) + ' %s' % mname(units[pc+1])
    elif name in ('invoke-virtual-range','invoke-static-range'):
        line += ' %s' % mname(units[pc+1])
    elif name == 'const-string':
        line += ' v%d "%s"' % ((u >> 8) & 0xFF, d.str_at(units[pc+1]))
    elif name == 'sget-object' or name == 'sget':
        line += ' v%d %s' % ((u >> 8) & 0xFF, fname(units[pc+1]))
    elif name == 'const-class':
        line += ' v%d %s' % ((u >> 8) & 0xFF, tname(units[pc+1]))
    elif name.startswith('if-'):
        line += ' +%d' % struct.unpack_from('<h', struct.pack('<H', units[pc+1]))[0]
    elif name == 'const/16':
        line += ' v%d %d' % ((u >> 8) & 0xFF, struct.unpack_from('<h', struct.pack('<H', units[pc+1]))[0])
    elif name == 'const/4':
        line += ' v%d %d' % (((u >> 8) & 0xF), ((u >> 12) & 0xF))
    out.append(line)
    pc += max(size, 1)
print('\n'.join(out))
