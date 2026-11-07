#!/usr/bin/env python3
"""Post-process the W11 Persian report docx:
1. Remove empty <w:pgNumType/> from the cover section.
2. Footer PAGE fields: section-2 footer -> \\* ROMAN switch, section-3 footer -> \\* arabic.
   Mapping is resolved precisely via sectPr order -> footerReference r:id -> rels -> footer file.
"""
import re, shutil, sys, zipfile
from pathlib import Path

DOC = Path(sys.argv[1])
TMP = DOC.with_suffix('.tmp.docx')

zin = zipfile.ZipFile(DOC, 'r')
names = zin.namelist()
docxml = zin.read('word/document.xml').decode('utf-8')
rels = zin.read('word/_rels/document.xml.rels').decode('utf-8')

# 1. strip empty pgNumType
docxml2 = docxml.replace('<w:pgNumType/>', '')

# 1b. dedup TOC placeholder rows: drop a TOC row whose text (digits stripped)
# equals the NEXT TOC row's text (digits stripped) — placeholder script can
# emit one number-less duplicate of the first entry.
def strip_digits(s):
    return re.sub(r'[\d\u06f0-\u06f9\u0660-\u0669]+', '', s)

def toc_dedup(xml):
    changed = 0
    pat = re.compile(r'<w:p\b[^>]*>(?:(?!</w:p>).)*?<w:pStyle w:val="TOC\d"/>(?:(?!</w:p>).)*?</w:p>', re.S)
    while True:
        paras = list(pat.finditer(xml))
        removed = False
        for a, b in zip(paras, paras[1:]):
            ta = strip_digits(''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', a.group(0))))
            tb = strip_digits(''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', b.group(0))))
            if ta == tb and ta.strip():
                xml = xml[:a.start()] + xml[a.end():]
                changed += 1
                removed = True
                break
        if not removed:
            return xml, changed

docxml2, dedup_n = toc_dedup(docxml2)
print(f"TOC dedup: removed {dedup_n} duplicate row(s)")

# 2. map sectPr order -> default footerReference r:id
sect_blocks = re.findall(r'<w:sectPr[ >].*?</w:sectPr>', docxml2, re.S)
print(f"sectPr blocks: {len(sect_blocks)}")
rid_map = dict(re.findall(r'<Relationship Id="([^"]+)"[^>]*Target="([^"]+)"', rels))

footer_of_section = {}
for i, blk in enumerate(sect_blocks):
    m = re.search(r'<w:footerReference w:type="default" r:id="([^"]+)"', blk)
    if m:
        target = rid_map.get(m.group(1), '')
        footer_of_section[i] = 'word/' + target.lstrip('/').replace('word/', '')
print("section->footer:", footer_of_section)

# sections are in document order: 0=cover(no footer), 1=TOC(roman), 2=body(arabic)
fmt_for_file = {}
if 1 in footer_of_section:
    fmt_for_file[footer_of_section[1]] = 'ROMAN'
if 2 in footer_of_section:
    fmt_for_file[footer_of_section[2]] = 'arabic'
print("footer fmt:", fmt_for_file)

zout = zipfile.ZipFile(TMP, 'w', zipfile.ZIP_DEFLATED)
for item in zin.infolist():
    data = zin.read(item.filename)
    if item.filename == 'word/document.xml':
        data = docxml2.encode('utf-8')
    elif item.filename in fmt_for_file:
        xml = data.decode('utf-8')
        fmt = fmt_for_file[item.filename]
        xml2, n = re.subn(r'(<w:instrText[^>]*>)\s*PAGE\s*(</w:instrText>)',
                          rf'\1 PAGE \\* {fmt} \\* MERGEFORMAT \2', xml)
        print(f"{item.filename}: {fmt} switched ({n} fields)")
        data = xml2.encode('utf-8')
    zout.writestr(item, data)
zout.close()
zin.close()
shutil.move(TMP, DOC)
print("post-process done:", DOC.name)
