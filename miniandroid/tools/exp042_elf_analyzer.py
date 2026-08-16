#!/usr/bin/env python3
"""
exp042_elf_analyzer.py

Self-contained ELF analyzer for the Telegram APK's native libraries
(lib/<abi>/*.so). Produces a metadata report (Markdown + JSON) describing:

  * ELF header metadata (class, endianness, machine type).
  * Exported JNI entry points (symbols starting with `Java_`).
  * `JNI_OnLoad` presence.
  * DT_NEEDED dependencies pulled from the `.dynamic` section.
  * Library / version strings pulled from the `.rodata` section.

A focused SUMMARY is also produced for `libtmessages.49.so` (any ABI):
  * JNI entry points grouped by Java class.
  * Total JNI entry count.
  * Top 5 classes by JNI method count.
  * All DT_NEEDED dependencies.

This script is research-only: it does NOT modify any source files and does
NOT depend on pyelftools. ELF parsing is performed directly with the
`struct` module so the script is fully self-contained.

Usage:
    python3 exp042_elf_analyzer.py [--apk APK] [--abi ABI] [--out-md PATH]
                                    [--out-json PATH]

Defaults:
    --apk       miniandroid/download/exp038_telegram/Telegram.apk
    --abi       arm64-v8a  (ABI used for the libtmessages.49.so SUMMARY)
    --out-md    miniandroid/docs/exp042/NATIVE_LIBRARIES.md
    --out-json  miniandroid/docs/exp042/NATIVE_LIBRARIES.json
"""

from __future__ import annotations

import argparse
import json
import os
import re
import struct
import sys
import tempfile
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# ELF constants
# ---------------------------------------------------------------------------

ELF_MAGIC = b"\x7fELF"

# e_ident[EI_CLASS]
ELFCLASSNONE = 0
ELFCLASS32 = 1
ELFCLASS64 = 2

# e_ident[EI_DATA]
ELFDATANONE = 0
ELFDATA2LSB = 1  # little-endian
ELFDATA2MSB = 2  # big-endian

# e_machine
EM_MAP = {
    0: "EM_NONE",
    3: "EM_386",
    40: "EM_ARM",
    62: "EM_X86_64",
    183: "EM_AARCH64",
}

# Section header types
SHT_NULL = 0
SHT_PROGBITS = 1
SHT_SYMTAB = 2
SHT_STRTAB = 3
SHT_DYNAMIC = 6
SHT_DYNSYM = 11
SHT_NOBITS = 8

# Section header name lookup (by sh_type) for diagnostics
SHT_NAMES = {
    SHT_NULL: "NULL",
    SHT_PROGBITS: "PROGBITS",
    SHT_SYMTAB: "SYMTAB",
    SHT_STRTAB: "STRTAB",
    SHT_DYNAMIC: "DYNAMIC",
    SHT_DYNSYM: "DYNSYM",
    SHT_NOBITS: "NOBITS",
}

# Dynamic tags
DT_NULL = 0
DT_NEEDED = 1
DT_STRTAB = 5
DT_SYMTAB = 6
DT_STRSZ = 10
DT_SYMENT = 11
DT_SONAME = 14

# Symbol binding (high nibble of st_info)
STB_LOCAL = 0
STB_GLOBAL = 1
STB_WEAK = 2

# Symbol type (low nibble of st_info)
STT_FUNC = 2
STT_OBJECT = 1

# Special section indices
SHN_UNDEF = 0


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Section:
    name: str
    sh_type: int
    sh_type_name: str
    sh_offset: int
    sh_size: int
    sh_addr: int


@dataclass
class Symbol:
    name: str
    st_info: int
    st_other: int
    st_shndx: int
    st_value: int
    st_size: int

    @property
    def bind(self) -> int:
        return (self.st_info >> 4) & 0xF

    @property
    def type(self) -> int:
        return self.st_info & 0xF

    @property
    def is_exported(self) -> bool:
        # Exported if defined in this object (st_shndx != SHN_UNDEF)
        # and bind is GLOBAL or WEAK.
        if self.st_shndx == SHN_UNDEF:
            return False
        return self.bind in (STB_GLOBAL, STB_WEAK)


@dataclass
class LibReport:
    apk_entry: str           # e.g. "lib/arm64-v8a/libtmessages.49.so"
    file_name: str           # "libtmessages.49.so"
    abi: str                 # "arm64-v8a"
    size: int                # bytes (uncompressed)
    elf_class: str           # "ELF32" / "ELF64"
    endianness: str          # "little" / "big"
    e_machine: int
    e_machine_name: str
    e_type: int
    e_type_name: str
    jni_onload_present: bool
    jni_symbols: List[str] = field(default_factory=list)
    dt_needed: List[str] = field(default_factory=list)
    version_strings: List[str] = field(default_factory=list)
    section_count: int = 0
    dynsym_count: int = 0
    errors: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# ELF parser (self-contained, uses struct only)
# ---------------------------------------------------------------------------

class ElfParser:
    """Minimal self-contained ELF parser supporting 32/64-bit, little/big endian."""

    def __init__(self, path: str):
        self.path = path
        with open(path, "rb") as fh:
            self.data = fh.read()
        self._parse_header()

    # -- header --
    def _parse_header(self) -> None:
        d = self.data
        if len(d) < 64 or d[:4] != ELF_MAGIC:
            raise ValueError(f"{self.path}: not an ELF file (bad magic)")
        ei_class = d[4]
        ei_data = d[5]
        if ei_class == ELFCLASS32:
            self.is64 = False
            self.elf_class = "ELF32"
        elif ei_class == ELFCLASS64:
            self.is64 = True
            self.elf_class = "ELF64"
        else:
            raise ValueError(f"{self.path}: unknown ELF class {ei_class}")

        if ei_data == ELFDATA2LSB:
            self.endian = "<"
            self.endianness = "little"
        elif ei_data == ELFDATA2MSB:
            self.endian = ">"
            self.endianness = "big"
        else:
            raise ValueError(f"{self.path}: unknown endianness {ei_data}")

        e = self.endian
        if self.is64:
            # e_type, e_machine, e_version, e_entry, e_phoff, e_shoff, e_flags,
            # e_ehsize, e_phentsize, e_phnum, e_shentsize, e_shnum, e_shstrndx
            (self.e_type, self.e_machine, self.e_version,
             self.e_entry, self.e_phoff, self.e_shoff, self.e_flags,
             self.e_ehsize, self.e_phentsize, self.e_phnum,
             self.e_shentsize, self.e_shnum, self.e_shstrndx) = struct.unpack(
                e + "HHIQQQIHHHHHH", d[16:64])
        else:
            (self.e_type, self.e_machine, self.e_version,
             self.e_entry, self.e_phoff, self.e_shoff, self.e_flags,
             self.e_ehsize, self.e_phentsize, self.e_phnum,
             self.e_shentsize, self.e_shnum, self.e_shstrndx) = struct.unpack(
                e + "HHIIIIIHHHHHH", d[16:52])

    # -- section headers --
    def parse_sections(self) -> List[Section]:
        if self.e_shoff == 0 or self.e_shnum == 0:
            return []
        e = self.endian
        sections: List[Section] = []
        # shstrtab section: read raw section entries first, then resolve names.
        raw_entries: List[Tuple[int, int, int, int]] = []
        for i in range(self.e_shnum):
            base = self.e_shoff + i * self.e_shentsize
            if self.is64:
                # Elf64_Shdr: name(u32) type(u32) flags(u64) addr(u64)
                #            offset(u64) size(u64) link(u32) info(u32)
                #            addralign(u64) entsize(u64)
                (sh_name, sh_type, _sh_flags, sh_addr,
                 sh_offset, sh_size, _sh_link, _sh_info,
                 _sh_align, _sh_entsize) = struct.unpack(
                    e + "IIQQQQIIQQ", self.data[base:base + 64])
            else:
                # Elf32_Shdr: name(u32) type(u32) flags(u32) addr(u32)
                #            offset(u32) size(u32) link(u32) info(u32)
                #            addralign(u32) entsize(u32)
                (sh_name, sh_type, _sh_flags, sh_addr,
                 sh_offset, sh_size, _sh_link, _sh_info,
                 _sh_align, _sh_entsize) = struct.unpack(
                    e + "IIIIIIIIII", self.data[base:base + 40])
            raw_entries.append((sh_name, sh_type, sh_offset, sh_size, sh_addr))

        # Resolve section names from .shstrtab.
        if self.e_shstrndx and self.e_shstrndx < len(raw_entries):
            _, _, str_off, str_size, _ = raw_entries[self.e_shstrndx]
            strtab = self.data[str_off:str_off + str_size]
        else:
            strtab = b""

        for sh_name, sh_type, sh_offset, sh_size, sh_addr in raw_entries:
            name = self._cstr(strtab, sh_name)
            sections.append(
                Section(
                    name=name,
                    sh_type=sh_type,
                    sh_type_name=SHT_NAMES.get(sh_type, f"0x{sh_type:x}"),
                    sh_offset=sh_offset,
                    sh_size=sh_size,
                    sh_addr=sh_addr,
                )
            )
        return sections

    @staticmethod
    def _cstr(buf: bytes, off: int) -> str:
        if off < 0 or off >= len(buf):
            return ""
        end = buf.find(b"\x00", off)
        if end < 0:
            end = len(buf)
        try:
            return buf[off:end].decode("utf-8", "replace")
        except Exception:
            return buf[off:end].decode("latin-1", "replace")

    def read_section_bytes(self, sec: Section) -> bytes:
        if sec.sh_type == SHT_NOBITS:
            return b""
        return self.data[sec.sh_offset:sec.sh_offset + sec.sh_size]

    # -- dynamic symbols --
    def parse_dynsym(self, sections: List[Section]) -> Tuple[List[Symbol], bytes]:
        dynsym = next((s for s in sections if s.sh_type == SHT_DYNSYM), None)
        if not dynsym:
            return [], b""
        # The matching strtab is referenced via sh_link on the dynsym section,
        # but we re-parse raw to capture sh_link. Re-read it here.
        if self.is64:
            fmt_sym = self.endian + "IBBHQQ"
            sym_size = 24
            # st_name(u32) st_info(u8) st_other(u8) st_shndx(u16) st_value(u64) st_size(u64)
        else:
            # Elf32_Sym: st_name(u32) st_value(u32) st_size(u32)
            #           st_info(u8) st_other(u8) st_shndx(u16)
            fmt_sym = self.endian + "IIIBBH"
            sym_size = 16

        # Determine sh_link to find the corresponding strtab section.
        sh_link_idx = self._section_link(dynsym)
        if sh_link_idx and sh_link_idx < len(sections):
            strtab_sec = sections[sh_link_idx]
            strtab = self.read_section_bytes(strtab_sec)
        else:
            # Fall back to .dynstr by name.
            dynstr = next((s for s in sections if s.name == ".dynstr"), None)
            strtab = self.read_section_bytes(dynstr) if dynstr else b""

        syms: List[Symbol] = []
        count = dynsym.sh_size // sym_size if sym_size else 0
        for i in range(count):
            base = dynsym.sh_offset + i * sym_size
            chunk = self.data[base:base + sym_size]
            if len(chunk) < sym_size:
                break
            if self.is64:
                st_name, st_info, st_other, st_shndx, st_value, st_size = \
                    struct.unpack(fmt_sym, chunk)
            else:
                st_name, st_value, st_size, st_info, st_other, st_shndx = \
                    struct.unpack(fmt_sym, chunk)
            name = self._cstr(strtab, st_name)
            syms.append(Symbol(
                name=name, st_info=st_info, st_other=st_other,
                st_shndx=st_shndx, st_value=st_value, st_size=st_size,
            ))
        return syms, strtab

    def _section_link(self, sec: Section) -> int:
        """Return the sh_link value for a section (re-parsed from disk)."""
        # We don't store sh_link on Section; re-read it for this section index.
        # Find section index by offset match (good enough for our use).
        for i in range(self.e_shnum):
            base = self.e_shoff + i * self.e_shentsize
            if self.is64:
                (_n, _t, _f, _a, sh_off, _sz, sh_link, _info,
                 _align, _ent) = struct.unpack(
                    self.endian + "IIQQQQIIQQ", self.data[base:base + 64])
            else:
                (_n, _t, _f, _a, sh_off, _sz, sh_link, _info,
                 _align, _ent) = struct.unpack(
                    self.endian + "IIIIIIIIII", self.data[base:base + 40])
            if sh_off == sec.sh_offset:
                return sh_link
        return 0

    # -- dynamic section --
    def parse_dynamic(self, sections: List[Section], dynstr: bytes) -> List[str]:
        dyn = next((s for s in sections if s.sh_type == SHT_DYNAMIC), None)
        if not dyn:
            # Fall back to .dynamic by name.
            dyn = next((s for s in sections if s.name == ".dynamic"), None)
        if not dyn:
            return []

        if self.is64:
            ent_size = 16
            fmt = self.endian + "qQ"  # d_tag (i64), d_un (u64)
        else:
            ent_size = 8
            fmt = self.endian + "iI"  # d_tag (i32), d_un (u32)

        # Use the dynstr we already loaded for resolving NEEDED names.
        needed: List[str] = []
        count = dyn.sh_size // ent_size if ent_size else 0
        for i in range(count):
            base = dyn.sh_offset + i * ent_size
            chunk = self.data[base:base + ent_size]
            if len(chunk) < ent_size:
                break
            d_tag, d_un = struct.unpack(fmt, chunk)
            if d_tag == DT_NULL:
                break
            if d_tag == DT_NEEDED:
                name = self._cstr(dynstr, d_un)
                if name:
                    needed.append(name)
        return needed

    # -- rodata scan --
    def scan_rodata_version_strings(self, sections: List[Section],
                                    limit: int = 40) -> List[str]:
        rodata = next((s for s in sections if s.name == ".rodata"), None)
        if not rodata:
            return []
        blob = self.read_section_bytes(rodata)
        if not blob:
            return []

        # Cap scanning at 4MB to avoid pathological cases.
        scan = blob[:4 * 1024 * 1024]
        # Extract printable ASCII strings of length >= 4.
        pattern = re.compile(rb"[\x20-\x7e]{4,}")
        matches = pattern.findall(scan)

        # Heuristic: keep strings that look like version markers.
        version_re = re.compile(
            r"(?i)(version|lib|build|v\s*=|^\d+\.\d+(?:\.\d+)?([\-+][\w.]+)?$)"
        )
        seen = set()
        results: List[str] = []
        for m in matches:
            try:
                s = m.decode("utf-8", "replace")
            except Exception:
                continue
            if s in seen:
                continue
            if version_re.search(s):
                seen.add(s)
                results.append(s)
                if len(results) >= limit:
                    break
        return results


# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------

def abi_from_entry(apk_entry: str) -> str:
    parts = apk_entry.split("/")
    if len(parts) >= 2 and parts[0] == "lib":
        return parts[1]
    return "unknown"


def file_name_from_entry(apk_entry: str) -> str:
    return os.path.basename(apk_entry)


def parse_jni_class(symbol: str) -> Tuple[str, str]:
    """
    Split a JNI symbol name into (class_path, method_name).

    JNI naming convention:
        Java_<pkg>_<...>_<Class>_<method>           (simple)
        Java_<pkg>_<...>_<Class>_<inner>_<method>     (inner class)

    The first token is always "Java". The LAST token is the method name.
    Everything in between is the fully-qualified Java class identifier
    (with underscores replacing dots). We collapse the middle into a
    single "class" string for grouping.
    """
    if not symbol.startswith("Java_"):
        return "", ""
    body = symbol[len("Java_"):]
    parts = body.split("_")
    if len(parts) < 2:
        # e.g. Java_something with no underscore — degenerate.
        return body, ""
    method = parts[-1]
    class_path = "_".join(parts[:-1])
    return class_path, method


def analyze_so(apk: zipfile.ZipFile, apk_entry: str) -> LibReport:
    info = apk.getinfo(apk_entry)
    file_name = file_name_from_entry(apk_entry)
    abi = abi_from_entry(apk_entry)
    report = LibReport(
        apk_entry=apk_entry,
        file_name=file_name,
        abi=abi,
        size=info.file_size,
        elf_class="",
        endianness="",
        e_machine=0,
        e_machine_name="",
        e_type=0,
        e_type_name="",
        jni_onload_present=False,
    )

    with tempfile.NamedTemporaryFile(suffix=".so", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        with apk.open(apk_entry) as src, open(tmp_path, "wb") as dst:
            dst.write(src.read())

        try:
            ep = ElfParser(tmp_path)
        except Exception as exc:
            report.errors.append(f"ELF parse failed: {exc}")
            return report

        report.elf_class = ep.elf_class
        report.endianness = ep.endianness
        report.e_machine = ep.e_machine
        report.e_machine_name = EM_MAP.get(ep.e_machine, f"0x{ep.e_machine:x}")
        report.e_type = ep.e_type
        report.e_type_name = {
            1: "ET_REL",
            2: "ET_EXEC",
            3: "ET_DYN",
            4: "ET_CORE",
        }.get(ep.e_type, f"0x{ep.e_type:x}")

        sections = ep.parse_sections()
        report.section_count = len(sections)

        syms, dynstr = ep.parse_dynsym(sections)
        report.dynsym_count = len(syms)

        jni_syms: List[str] = []
        for s in syms:
            if not s.name:
                continue
            if s.name == "JNI_OnLoad":
                report.jni_onload_present = True
                continue
            if s.name.startswith("Java_"):
                # Only count exported (defined) symbols; if all are imported
                # (SHN_UNDEF), still include them because some libraries
                # register via RegisterNatives and may not export Java_*
                # directly. We list any Java_* symbol for completeness.
                jni_syms.append(s.name)

        # Deduplicate while preserving order.
        seen = set()
        deduped: List[str] = []
        for sym in jni_syms:
            if sym not in seen:
                seen.add(sym)
                deduped.append(sym)
        report.jni_symbols = deduped

        report.dt_needed = ep.parse_dynamic(sections, dynstr)
        report.version_strings = ep.scan_rodata_version_strings(sections)
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
    return report


# ---------------------------------------------------------------------------
# Markdown / JSON writers
# ---------------------------------------------------------------------------

def build_summary_block(lib_reports: List[LibReport], target_abi: str,
                        target_name: str = "libtmessages.49.so") -> Dict[str, Any]:
    """Build the libtmessages.49.so-focused SUMMARY data structure."""
    candidate = next(
        (r for r in lib_reports if r.file_name == target_name and r.abi == target_abi),
        None,
    )
    if candidate is None:
        # Fall back to any ABI.
        candidate = next(
            (r for r in lib_reports if r.file_name == target_name), None,
        )

    if candidate is None:
        return {"error": f"{target_name} not found in APK"}

    grouped: Dict[str, List[str]] = defaultdict(list)
    for sym in candidate.jni_symbols:
        cls, method = parse_jni_class(sym)
        if cls:
            grouped[cls].append(method)

    class_counts = sorted(
        ((cls, len(methods)) for cls, methods in grouped.items()),
        key=lambda x: x[1], reverse=True,
    )
    top5 = class_counts[:5]

    grouped_serializable = {
        cls: sorted(set(methods)) for cls, methods in grouped.items()
    }

    return {
        "library": candidate.file_name,
        "abi": candidate.abi,
        "elf_class": candidate.elf_class,
        "endianness": candidate.endianness,
        "e_machine": candidate.e_machine,
        "e_machine_name": candidate.e_machine_name,
        "e_type": candidate.e_type,
        "e_type_name": candidate.e_type_name,
        "file_size": candidate.size,
        "jni_onload_present": candidate.jni_onload_present,
        "jni_entry_total": len(candidate.jni_symbols),
        "dt_needed": candidate.dt_needed,
        "class_count": len(grouped),
        "top5_classes_by_jni_method_count": [
            {"class": cls, "jni_method_count": n, "methods": sorted(set(grouped[cls]))}
            for cls, n in top5
        ],
        "jni_symbols_grouped_by_class": grouped_serializable,
    }


def render_markdown(lib_reports: List[LibReport], summary: Dict[str, Any],
                    apk_path: str, target_abi: str) -> str:
    lines: List[str] = []
    L = lines.append
    L("# EXP-042 — Telegram Native Libraries (ELF Metadata)")
    L("")
    L(f"- **APK:** `{apk_path}`")
    L(f"- **Summary ABI focus:** `{target_abi}`")
    L(f"- **Total `.so` entries in APK:** {len(lib_reports)}")
    L(f"- **Analyzer:** `miniandroid/tools/exp042_elf_analyzer.py` "
      f"(self-contained, `struct`-only; no pyelftools)")
    L("")
    L("---")
    L("")
    L("## Table of Contents")
    L("")
    L("1. [All native libraries](#all-native-libraries)")
    L("2. [libtmessages.49.so SUMMARY](#libtmessages49so-summary)")
    L("3. [Per-library detail](#per-library-detail)")
    L("")
    L("---")
    L("")
    L("## All native libraries")
    L("")
    L("| APK entry | ABI | ELF class | Machine | Endian | Size | JNI symbols | JNI_OnLoad | DT_NEEDED |")
    L("|---|---|---|---|---|---:|---:|:---:|---:|")
    for r in lib_reports:
        L(f"| `{r.apk_entry}` | {r.abi} | {r.elf_class} | "
          f"{r.e_machine_name} ({r.e_machine}) | {r.endianness} | "
          f"{r.size:,} | {len(r.jni_symbols)} | "
          f"{'yes' if r.jni_onload_present else 'no'} | "
          f"{len(r.dt_needed)} |")
    L("")
    L("---")
    L("")
    L("## libtmessages.49.so SUMMARY")
    L("")
    if "error" in summary:
        L(f"**ERROR:** {summary['error']}")
    else:
        L(f"- **Library:** `{summary['library']}`")
        L(f"- **ABI used for summary:** `{summary['abi']}`")
        L(f"- **ELF class:** {summary['elf_class']}")
        L(f"- **Machine:** {summary['e_machine_name']} "
          f"(e_machine={summary['e_machine']})")
        L(f"- **Endianness:** {summary['endianness']}")
        L(f"- **ELF type:** {summary['e_type_name']} "
          f"(e_type={summary['e_type']})")
        L(f"- **File size:** {summary['file_size']:,} bytes")
        L(f"- **`JNI_OnLoad` present:** "
          f"{'yes' if summary['jni_onload_present'] else 'no'}")
        L(f"- **Total exported JNI symbols (`Java_*`):** "
          f"{summary['jni_entry_total']}")
        L(f"- **Distinct Java classes exposed via JNI:** "
          f"{summary['class_count']}")
        L(f"- **DT_NEEDED dependencies:** {len(summary['dt_needed'])}")
        L("")
        L("### DT_NEEDED dependencies")
        L("")
        if summary['dt_needed']:
            for dep in summary['dt_needed']:
                L(f"- `{dep}`")
        else:
            L("_(none — fully self-contained link set)_")
        L("")
        L("### Top 5 Java classes by JNI method count")
        L("")
        L("| # | Java class (underscore-encoded) | JNI method count | Sample methods |")
        L("|---:|---|---:|---|")
        for i, item in enumerate(summary['top5_classes_by_jni_method_count'], 1):
            sample = ", ".join(f"`{m}`" for m in item['methods'][:5])
            if len(item['methods']) > 5:
                sample += f", … (+{len(item['methods']) - 5} more)"
            L(f"| {i} | `{item['class']}` | {item['jni_method_count']} | "
              f"{sample} |")
        L("")
        L("### JNI entry points grouped by Java class")
        L("")
        L("<details><summary>Expand full grouped list</summary>")
        L("")
        for cls in sorted(summary['jni_symbols_grouped_by_class'].keys()):
            methods = summary['jni_symbols_grouped_by_class'][cls]
            L(f"- **`{cls}`** ({len(methods)} methods):")
            for m in methods:
                L(f"  - `{m}`")
        L("")
        L("</details>")
    L("")
    L("---")
    L("")
    L("## Per-library detail")
    L("")
    for r in lib_reports:
        L(f"### `{r.apk_entry}`")
        L("")
        L(f"- **ABI:** `{r.abi}`")
        L(f"- **File name:** `{r.file_name}`")
        L(f"- **Uncompressed size:** {r.size:,} bytes")
        L(f"- **ELF class:** {r.elf_class}")
        L(f"- **Endianness:** {r.endianness}")
        L(f"- **e_machine:** {r.e_machine_name} ({r.e_machine})")
        L(f"- **e_type:** {r.e_type_name} ({r.e_type})")
        L(f"- **Section count:** {r.section_count}")
        L(f"- **Dynamic symbols parsed:** {r.dynsym_count}")
        L(f"- **Exported JNI symbols (`Java_*`):** {len(r.jni_symbols)}")
        L(f"- **`JNI_OnLoad` present:** "
          f"{'yes' if r.jni_onload_present else 'no'}")
        if r.errors:
            L(f"- **Errors:**")
            for er in r.errors:
                L(f"  - {er}")
        L("")
        L("#### DT_NEEDED dependencies")
        L("")
        if r.dt_needed:
            for dep in r.dt_needed:
                L(f"- `{dep}`")
        else:
            L("_(none)_")
        L("")
        L("#### Exported JNI symbols (`Java_*`)")
        L("")
        if r.jni_symbols:
            L("<details><summary>Expand JNI symbols</summary>")
            L("")
            for sym in r.jni_symbols:
                L(f"- `{sym}`")
            L("")
            L("</details>")
        else:
            L("_(none — JNI methods likely registered via `RegisterNatives`)_")
        L("")
        L("#### Version / library strings from `.rodata`")
        L("")
        if r.version_strings:
            L("<details><summary>Expand version strings</summary>")
            L("")
            for vs in r.version_strings:
                L(f"- `{vs}`")
            L("")
            L("</details>")
        else:
            L("_(no obvious version markers found in first 4MB of `.rodata`)_")
        L("")
        L("---")
        L("")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

DEFAULT_APK = "/home/z/my-project/MiniAndroid-Compatibility-Runtime/" \
              "miniandroid/download/exp038_telegram/Telegram.apk"
DEFAULT_MD = "/home/z/my-project/MiniAndroid-Compatibility-Runtime/" \
             "miniandroid/docs/exp042/NATIVE_LIBRARIES.md"
DEFAULT_JSON = "/home/z/my-project/MiniAndroid-Compatibility-Runtime/" \
               "miniandroid/docs/exp042/NATIVE_LIBRARIES.json"
DEFAULT_ABI = "arm64-v8a"


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1] if __doc__ else "")
    p.add_argument("--apk", default=DEFAULT_APK, help="Path to Telegram.apk")
    p.add_argument("--abi", default=DEFAULT_ABI,
                   help="ABI to use for libtmessages.49.so SUMMARY")
    p.add_argument("--out-md", default=DEFAULT_MD,
                   help="Output Markdown report path")
    p.add_argument("--out-json", default=DEFAULT_JSON,
                   help="Output JSON report path")
    args = p.parse_args(argv)

    if not os.path.isfile(args.apk):
        print(f"ERROR: APK not found at {args.apk}", file=sys.stderr)
        return 2

    os.makedirs(os.path.dirname(args.out_md), exist_ok=True)
    os.makedirs(os.path.dirname(args.out_json), exist_ok=True)

    print(f"[exp042] Opening APK: {args.apk}")
    with zipfile.ZipFile(args.apk, "r") as apk:
        so_entries = sorted(
            n for n in apk.namelist()
            if n.startswith("lib/") and n.endswith(".so")
        )
        print(f"[exp042] Found {len(so_entries)} .so entries:")
        for n in so_entries:
            print(f"           - {n}")

        lib_reports: List[LibReport] = []
        for entry in so_entries:
            print(f"[exp042] Analyzing {entry} ...")
            r = analyze_so(apk, entry)
            lib_reports.append(r)
            print(f"           {r.elf_class} / {r.e_machine_name} / "
                  f"{r.endianness} | size={r.size:,} | "
                  f"jni_symbols={len(r.jni_symbols)} | "
                  f"JNI_OnLoad={'yes' if r.jni_onload_present else 'no'} | "
                  f"dt_needed={len(r.dt_needed)}")

    summary = build_summary_block(lib_reports, target_abi=args.abi,
                                 target_name="libtmessages.49.so")

    # Build JSON.
    json_doc = {
        "apk": os.path.abspath(args.apk),
        "summary_abi_focus": args.abi,
        "total_so_entries": len(lib_reports),
        "libraries": [asdict(r) for r in lib_reports],
        "libtmessages_summary": summary,
    }

    with open(args.out_json, "w", encoding="utf-8") as fh:
        json.dump(json_doc, fh, indent=2, ensure_ascii=False)
    print(f"[exp042] Wrote JSON: {args.out_json}")

    md = render_markdown(lib_reports, summary,
                         apk_path=args.apk, target_abi=args.abi)
    with open(args.out_md, "w", encoding="utf-8") as fh:
        fh.write(md)
    print(f"[exp042] Wrote Markdown: {args.out_md}")

    # Console summary.
    print()
    print("=" * 70)
    print("EXP-042 ELF ANALYSIS — SUMMARY")
    print("=" * 70)
    print(f"Total native .so files: {len(lib_reports)}")
    if "error" not in summary:
        print(f"libtmessages.49.so ({summary['abi']}):")
        print(f"  ELF class:   {summary['elf_class']}")
        print(f"  Machine:     {summary['e_machine_name']} "
              f"(e_machine={summary['e_machine']})")
        print(f"  JNI symbols: {summary['jni_entry_total']}")
        print(f"  JNI_OnLoad:  "
              f"{'present' if summary['jni_onload_present'] else 'absent'}")
        print(f"  DT_NEEDED:   {summary['dt_needed']}")
        print(f"  Top 5 classes by JNI method count:")
        for i, item in enumerate(summary['top5_classes_by_jni_method_count'], 1):
            print(f"    {i}. {item['class']} — {item['jni_method_count']} methods")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
