#!/usr/bin/env python3
"""EXP-052: Static discovery of LaunchActivity → Login UI path.

Walks the bytecode of LaunchActivity.onCreate and the surrounding methods
to find what UI-switching calls happen on the login path (when
UserConfig.isClientActivated() == false).

Usage: python3 tools/exp052_login_path_discovery.py
"""
import sys, zipfile, struct

APK = '/home/z/my-project/MiniAndroid-Compatibility-Runtime/miniandroid/download/exp038_telegram/Telegram.apk'

# Opcode constants
OP_CONST_STRING = 0x1a
OP_INVOKE_VIRTUAL = 0x6e
OP_INVOKE_DIRECT = 0x70
OP_INVOKE_STATIC = 0x71
OP_INVOKE_INTERFACE = 0x72
OP_INVOKE_SUPER = 0x6f
OP_INVOKE_VIRTUAL_RANGE = 0x74
OP_INVOKE_DIRECT_RANGE = 0x76
OP_INVOKE_STATIC_RANGE = 0x77
OP_NEW_INSTANCE = 0x22
OP_IGET_BOOLEAN = 0x55
OP_IGET_OBJECT = 0x54
OP_IF_NEZ = 0x38
OP_IF_EQZ = 0x37
OP_GOTO = 0x27
OP_GOTO_16 = 0x28
OP_RETURN_VOID = 0x0e

INVOKE_OPS = {
    OP_INVOKE_VIRTUAL: 'invoke-virtual',
    OP_INVOKE_DIRECT: 'invoke-direct',
    OP_INVOKE_STATIC: 'invoke-static',
    OP_INVOKE_INTERFACE: 'invoke-interface',
    OP_INVOKE_SUPER: 'invoke-super',
    OP_INVOKE_VIRTUAL_RANGE: 'invoke-virtual/range',
    OP_INVOKE_DIRECT_RANGE: 'invoke-direct/range',
    OP_INVOKE_STATIC_RANGE: 'invoke-static/range',
}

# Methods we're interested in (UI switching)
UI_METHODS_OF_INTEREST = {
    'startActivity', 'startActivityForResult', 'presentFragment',
    'replaceFragment', 'addFragment', 'removeFragment', 'switchToAccount',
    'presentFragmentAsDrawer', 'presentFragmentAsPreview',
    'finishFragment', 'closeLastFragment', 'needCloseLastFragment',
    'presentFragmentImpl', 'rebuildFragments',
    'showFragment', 'showLoginActivity', 'showIntroActivity',
}

class DexFile:
    def __init__(self, data, name=''):
        self.data = data
        self.name = name
        self._parse_header()

    def _parse_header(self):
        d = self.data
        self.string_ids_size = struct.unpack_from('<I', d, 0x38)[0]
        self.string_ids_off = struct.unpack_from('<I', d, 0x3c)[0]
        self.type_ids_size = struct.unpack_from('<I', d, 0x40)[0]
        self.type_ids_off = struct.unpack_from('<I', d, 0x44)[0]
        self.proto_ids_size = struct.unpack_from('<I', d, 0x48)[0]
        self.proto_ids_off = struct.unpack_from('<I', d, 0x4c)[0]
        self.field_ids_size = struct.unpack_from('<I', d, 0x50)[0]
        self.field_ids_off = struct.unpack_from('<I', d, 0x54)[0]
        self.method_ids_size = struct.unpack_from('<I', d, 0x58)[0]
        self.method_ids_off = struct.unpack_from('<I', d, 0x5c)[0]
        self.class_defs_size = struct.unpack_from('<I', d, 0x60)[0]
        self.class_defs_off = struct.unpack_from('<I', d, 0x64)[0]

    def _uleb(self, off):
        r = 0; s = 0
        while True:
            b = self.data[off]; off += 1
            r |= (b & 0x7F) << s
            if not (b & 0x80): break
            s += 7
        return r, off

    def get_string(self, idx):
        sid = struct.unpack_from('<I', self.data, self.string_ids_off + idx * 4)[0]
        p = sid
        while self.data[p] & 0x80: p += 1
        p += 1
        end = self.data.index(0, p)
        return self.data[p:end].decode('utf-8', errors='replace')

    def get_type_descriptor(self, type_idx):
        sid = struct.unpack_from('<I', self.data, self.type_ids_off + type_idx * 4)[0]
        return self.get_string(sid)

    def get_method_info(self, method_idx):
        m_off = self.method_ids_off + method_idx * 8
        class_idx = struct.unpack_from('<H', self.data, m_off)[0]
        proto_idx = struct.unpack_from('<H', self.data, m_off+2)[0]
        name_idx = struct.unpack_from('<I', self.data, m_off+4)[0]
        return (self.get_type_descriptor(class_idx), self.get_string(name_idx))

    def find_class(self, class_desc):
        for ti in range(self.type_ids_size):
            sid = struct.unpack_from('<I', self.data, self.type_ids_off + ti * 4)[0]
            s = self.get_string(sid)
            if s == class_desc:
                return ti
        return None

    def find_class_def(self, class_desc):
        ti = self.find_class(class_desc)
        if ti is None: return None
        for ci in range(self.class_defs_size):
            cd_off = self.class_defs_off + ci * 32
            class_idx = struct.unpack_from('<I', self.data, cd_off)[0]
            if class_idx == ti:
                class_data_off = struct.unpack_from('<I', self.data, cd_off + 24)[0]
                return (ci, class_data_off)
        return None

    def list_methods(self, class_desc):
        cd = self.find_class_def(class_desc)
        if cd is None or cd[1] == 0: return []
        off = cd[1]
        sf, off = self._uleb(off)
        iff, off = self._uleb(off)
        dm, off = self._uleb(off)
        vm, off = self._uleb(off)
        # Skip fields
        prev = 0
        for _ in range(sf):
            _, off = self._uleb(off); _, off = self._uleb(off)
        prev = 0
        for _ in range(iff):
            _, off = self._uleb(off); _, off = self._uleb(off)
        result = []
        for kind, count in [('direct', dm), ('virtual', vm)]:
            prev = 0
            for _ in range(count):
                diff, off = self._uleb(off)
                prev += diff
                access, off = self._uleb(off)
                code_off, off = self._uleb(off)
                cls, name = self.get_method_info(prev)
                result.append({
                    'kind': kind, 'method_idx': prev,
                    'access': access, 'code_off': code_off,
                    'class': cls, 'name': name,
                })
        return result

    def find_method(self, class_desc, method_name):
        for m in self.list_methods(class_desc):
            if m['name'] == method_name:
                return m
        return None

    def dump_invoke_calls(self, class_desc, method_name, max_calls=200):
        """Walk the bytecode and return all invoke-* calls."""
        m = self.find_method(class_desc, method_name)
        if m is None or m['code_off'] == 0:
            return None
        code_off = m['code_off']
        insns_size = struct.unpack_from('<I', self.data, code_off + 12)[0]
        insns_off = code_off + 16
        calls = []
        # Walk bytecode with simple size table
        SIZE = {
            0x00:1, 0x01:1, 0x02:2, 0x03:3, 0x04:1, 0x05:2, 0x06:3,
            0x07:1, 0x08:2, 0x09:3, 0x0a:1, 0x0b:1, 0x0c:1, 0x0d:1,
            0x0e:1, 0x0f:1, 0x10:1, 0x11:1, 0x12:1, 0x13:2, 0x14:3,
            0x15:2, 0x16:2, 0x17:2, 0x18:5, 0x19:2, 0x1a:2, 0x1b:3,
            0x1c:2, 0x1d:1, 0x1e:1, 0x1f:2, 0x20:2, 0x21:1, 0x22:2,
            0x23:2, 0x24:3, 0x25:3, 0x26:1, 0x27:1, 0x28:2, 0x29:3,
            0x2a:3, 0x2b:3, 0x2c:2, 0x2d:2, 0x2e:2, 0x2f:2, 0x30:2,
            0x31:2, 0x32:2, 0x33:2, 0x34:2, 0x35:2, 0x36:2,
            0x37:2, 0x38:2, 0x39:2, 0x3a:2, 0x3b:2, 0x3c:2,
        }
        for op in range(0x44, 0x52): SIZE[op] = 2  # array ops
        for op in range(0x52, 0x6e): SIZE[op] = 2  # iget/iput/sget/sput
        for op in range(0x91, 0xa7): SIZE[op] = 2  # binops
        for op in range(0xd0, 0xd8): SIZE[op] = 2  # lit16
        for op in range(0x9c, 0xa7): SIZE[op] = 2  # lit8 (override)
        # Invoke ops are all 3 code units (35c or 3rc)
        for op in [0x6e, 0x6f, 0x70, 0x71, 0x72, 0x74, 0x75, 0x76, 0x77, 0x78]:
            SIZE[op] = 3
        SIZE[0x1a] = 2  # const-string
        SIZE[0x1b] = 3  # const-string/jumbo
        SIZE[0x22] = 2  # new-instance
        SIZE[0x1f] = 2  # check-cast
        SIZE[0x23] = 2  # new-array
        SIZE[0x20] = 2  # instance-of
        SIZE[0x21] = 1  # array-length
        SIZE[0x1c] = 2  # const-class

        pc = 0
        while pc < insns_size:
            cu = struct.unpack_from('<H', self.data, insns_off + pc * 2)[0]
            op = cu & 0xFF
            if op in INVOKE_OPS:
                if pc + 1 < insns_size:
                    method_idx = struct.unpack_from('<H', self.data, insns_off + (pc+1) * 2)[0]
                    cls, name = self.get_method_info(method_idx)
                    calls.append({
                        'pc': pc, 'op': INVOKE_OPS[op],
                        'class': cls, 'method': name, 'method_idx': method_idx
                    })
                    if len(calls) >= max_calls: break
            sz = SIZE.get(op, 1)
            pc += sz
            if sz == 0: break
        return calls


def main():
    print('=== EXP-052 Login Path Discovery ===')
    with zipfile.ZipFile(APK) as z:
        dex_files = sorted(n for n in z.namelist() if n.endswith('.dex'))

    dexes = []
    for dex_name in dex_files:
        data = z.read(dex_name) if False else None
        # We'll lazily read inside the function
    # Open once
    with zipfile.ZipFile(APK) as z:
        for dex_name in dex_files:
            data = z.read(dex_name)
            dex = DexFile(data, dex_name)
            dexes.append(dex)

    # Find LaunchActivity.onCreate in any DEX
    target_class = 'Lorg/telegram/ui/LaunchActivity;'
    target_method = 'onCreate'

    found = False
    for dex in dexes:
        m = dex.find_method(target_class, target_method)
        if m:
            print(f'\nFound {target_class}.{target_method} in {dex.name}')
            print(f'  code_off=0x{m["code_off"]:x}')
            print(f'  access=0x{m["access"]:x} ({m["kind"]})')
            found = True

            # Dump all invoke-* calls
            calls = dex.dump_invoke_calls(target_class, target_method)
            if calls:
                print(f'\n  Total invoke-* calls: {len(calls)}')
                print(f'  UI-switching calls:')
                for c in calls:
                    if c['method'] in UI_METHODS_OF_INTEREST:
                        print(f'    PC={c["pc"]:4d}  {c["op"]:<22} → {c["class"]}.{c["method"]}')
                # Also list methods that look login-related
                print(f'\n  Login-related calls (containing "login" or "Login"):')
                for c in calls:
                    if 'login' in c['method'].lower() or 'Login' in c['class']:
                        print(f'    PC={c["pc"]:4d}  {c["op"]:<22} → {c["class"]}.{c["method"]}')
                # Show all invoke-direct (constructors of interest)
                print(f'\n  new-instance-related invoke-direct (constructors):')
                seen = set()
                for c in calls[:50]:
                    if c['method'] == '<init>' and c['class'] not in seen:
                        seen.add(c['class'])
                        print(f'    PC={c["pc"]:4d}  → new {c["class"]}')
            break

    if not found:
        print(f'  {target_class}.{target_method} not found in any DEX')
        return

    # Now look at LoginActivity itself
    print('\n=== Looking for LoginActivity ===')
    target_class = 'Lorg/telegram/ui/LoginActivity;'
    for dex in dexes:
        if dex.find_class(target_class) is not None:
            print(f'\n{target_class} found in {dex.name}')
            methods = dex.list_methods(target_class)
            print(f'  Total methods: {len(methods)}')
            # Show onCreate
            for m in methods:
                if m['name'] == 'onCreate':
                    print(f'  onCreate: code_off=0x{m["code_off"]:x}')
                    break
            break


if __name__ == '__main__':
    main()
