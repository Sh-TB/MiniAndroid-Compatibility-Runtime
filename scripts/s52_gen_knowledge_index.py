#!/usr/bin/env python3
"""S52: generate docs/KNOWLEDGE_INDEX.md — canonical knowledge-file inventory.
Per-file rows for knowledge-class trees; directory-summary rows for era trees.
Statuses: KEEP / HISTORY / GENERATED / EVIDENCE / LOCAL-AGENT / SUPERSEDED / MERGE-CANDIDATE.
"""
import json, re, subprocess, datetime

def sh(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout.strip()

files = sh("git ls-files '*.md'").splitlines()
jsons = sh("git ls-files '*.json'").splitlines()

SUBSYS = [
    (r'telegram', 'Telegram'),
    (r'whatsapp', 'WhatsApp'),
    (r'dooz', 'Dooz'),
    (r'compose', 'Compose'),
    (r'coroutine|atomicfu', 'coroutines/AtomicFU'),
    (r'kotlin', 'Kotlin'),
    (r'\bdex\b|dalvik|mutf|smali|dex_', 'DEX/Dalvik'),
    (r'\bart\b', 'ART'),
    (r'arsc|axml|resource|aapt|manifest', 'Resources/ARSC/AXML'),
    (r'render|frame|canvas|typograph|font|drawable|pixel', 'rendering'),
    (r'lifecycle|fragment', 'lifecycle'),
    (r'input|touch|\btap|gesture|\bime\b|keyboard', 'input'),
    (r'storage|sharedpref|sqlite|database|file_?dir|data_?dir', 'storage'),
    (r'concurren|thread|atomic|unsafe|volatile|lock', 'concurrency'),
    (r'openjdk|desugar|lambda|stream', 'OpenJDK/desugar'),
    (r'\baosp\b', 'AOSP'),
    (r'winedroid', 'WineDroid'),
    (r'droidvm', 'DroidVM'),
    (r'skydnir', 'Skydnir'),
    (r'androidrecomp|recomp', 'AndroidRecomp'),
    (r'robolectric', 'Robolectric'),
    (r'paparazzi', 'Paparazzi'),
    (r'bundletool|\baab\b', 'bundletool'),
    (r'\bavf\b|crosvm', 'AVF/crosvm'),
    (r'\basc\b|droidasc', 'ASC'),
    (r'game|tictactoe|chessclock|2048|minesweeper|sudoku|solitaire|yahtzee|\bdice|wordle|word_game|braincup|puzzle|roll|lexica|antimine', 'game compatibility'),
    (r'r-new|r_\d|root[-_]|registry|bug', 'runtime bugs (root registry)'),
]
ERAPAT = re.compile(r'(EXP\d|CAMPAIGN|BASELINE|_REPORT|REPORT_|S\d\d_|GOLDEN|G\d\d|u011|u013|campaign|m3_|master_)', re.I)

def classify(path, title):
    p = path.lower() + ' ' + title.lower()
    for pat, name in SUBSYS:
        if re.search(pat, p):
            return name
    return 'runtime general / project infra'

def title_of(path):
    try:
        with open(path, encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.startswith('# '):
                    return line[2:].strip()[:110]
    except OSError:
        pass
    return ''

def status_of(path):
    if path.startswith('docs/history/'): return 'HISTORY'
    if path.startswith('docs/evidence/'): return 'EVIDENCE'
    if path.startswith('docs/releases/'): return 'HISTORY (release notes)'
    if path.startswith('docs/agent-index/'): return 'GENERATED'
    if path in ('docs/INDEX.md',): return 'GENERATED (nav hub)'
    if path in ('README.md', 'worklog.md'): return 'KEEP (root)'
    if path.startswith('docs/maintenance/'): return 'KEEP (process)'
    if path.startswith('miniandroid/.agent/'): return 'LOCAL-AGENT (process notes)'
    if path == 'miniandroid/docs/README.md': return 'KEEP (module)'
    if path.startswith('docs/compatibility/'): return 'KEEP'
    if path.startswith('docs/research/'): return 'KEEP'
    if path.startswith('docs/runtime/knowledge/'): return 'KEEP (knowledge core)'
    if path.startswith('docs/runtime/'):
        base = path.rsplit('/', 1)[-1]
        parts = path.split('/')
        parent = parts[2] if len(parts) > 3 else ''  # docs/runtime/<subdir>/file.md only
        if parent: return 'HISTORY (era experiment dir)'
        if ERAPAT.search(base): return 'HISTORY (era experiment report)'
        return 'KEEP'
    return 'KEEP'

rows = []
for f in files:
    t = title_of(f)
    rows.append({'path': f, 'title': t, 'subsys': classify(f, t), 'status': status_of(f)})

# ---- per-file knowledge trees ----
PERFILE_DIRS = ('docs/runtime/knowledge/', 'docs/research/', 'docs/compatibility/',
                'docs/architecture/', 'docs/upstream/', 'docs/forensics/', 'docs/decisions/',
                'docs/security/', 'docs/testing/', 'docs/tooling/', 'docs/build/',
                'docs/development/', 'docs/demos/', 'docs/agent-index/',
                'docs/maintenance/', 'miniandroid/docs/')
perfile = [r for r in rows if r['path'].startswith(PERFILE_DIRS)]
perfile += [r for r in rows if r['path'] == 'docs/runtime/' + r['path'].split('/')[-1] and not ERAPAT.search(r['path'].split('/')[-1])]

# ---- era trees (dir-level summaries) ----
era_dirs = {}
for r in rows:
    if r['path'].startswith(('docs/history/', 'docs/evidence/', 'docs/releases/')): continue
    if r['status'].startswith('HISTORY') and r['path'].startswith('docs/runtime/'):
        d = '/'.join(r['path'].split('/')[:3]) if r['path'].count('/') > 2 else 'docs/runtime (root era reports)'
        era_dirs.setdefault(d, [0, r['status']])
        era_dirs[d][0] += 1
json_era = [j for j in jsons if j.startswith(('docs/history/', 'docs/evidence/', 'docs/runtime/research/raw/'))]

# ---- output ----
out = []
A = out.append
A('# KNOWLEDGE_INDEX — Canonical Inventory of Knowledge & Research Files')
A('')
A('> **SINGLE SOURCE OF TRUTH for knowledge navigation** (S52). Complements')
A('> [`docs/INDEX.md`](INDEX.md) (concept navigation hub) and')
A('> [`docs/EXECUTION_ACHIEVEMENTS.md`](EXECUTION_ACHIEVEMENTS.md) (execution')
A('> evidence). Generated from the tracked file tree; regenerate with')
A('> `python3 scripts/s52_gen_knowledge_index.py`. Knowledge files are NEVER')
A('> deleted without classification first; duplicates are merged only after')
A('> duplication is proven (S52 policy §7).')
A('')
n_keep = sum(1 for r in rows if r['status'].startswith('KEEP'))
n_hist = sum(1 for r in rows if r['status'].startswith('HISTORY'))
n_evi = sum(1 for r in rows if r['status'] == 'EVIDENCE')
A(f'Snapshot: {len(rows)} tracked `.md` files — {n_keep} KEEP (knowledge/process),'
  f' {n_hist} HISTORY (era records), {n_evi} EVIDENCE (compact, cited), plus'
  f' {len(jsons)} tracked `.json` (indexes/fixtures/oracles — classified below).')
A('')
A('## 1. Status legend')
A('')
A('| Status | Meaning |')
A('|---|---|')
A('| KEEP | current canonical knowledge — read these first |')
A('| KEEP (knowledge core) | distilled upstream/engine knowledge under `docs/runtime/knowledge/` |')
A('| HISTORY | era record (experiment/campaign report) — valid for its era, not current truth |')
A('| EVIDENCE | compact, cited evidence tree under `docs/evidence/` |')
A('| GENERATED | machine-generated index (regenerable) |')
A('| LOCAL-AGENT | working notes for the agent loop (`.agent/`), not project docs |')
A('| SUPERSEDED | pointer added; content absorbed by a canonical file |')
A('')
A('## 2. Knowledge files — per-file inventory (knowledge-class trees)')
A('')
A('| Path | Topic (first heading) | Subsystem | Status |')
A('|---|---|---|---|')
for r in sorted(perfile, key=lambda x: (x['subsys'], x['path'])):
    A(f"| `{r['path']}` | {r['title'] or '—'} | {r['subsys']} | {r['status']} |")
A('')
A(f'_rows: {len(perfile)}_')
A('')
A('## 3. Era trees — directory-level summaries (full lists via `git ls-files <dir>`)')
A('')
A('| Tree | Files (.md) | Status | What lives here |')
A('|---|---|---|---|')
A(f"| `docs/history/` | {sum(1 for r in rows if r['path'].startswith('docs/history/'))} | HISTORY | archived campaign/session history moved out of the active tree |")
A(f"| `docs/evidence/` | {sum(1 for r in rows if r['path'].startswith('docs/evidence/'))} | EVIDENCE | compact per-issue/per-campaign evidence + screenshot galleries + s52_asc cards + residue record |")
A(f"| `docs/releases/` | {sum(1 for r in rows if r['path'].startswith('docs/releases/'))} | HISTORY | release notes + manifests |")
for d, (c, st) in sorted(era_dirs.items()):
    A(f"| `{d}` | {c} | {st} | era experiment/campaign reports |")
A('')
A('Tracked JSON classes: battery/test indexes (`docs/testing/BATTERY_INDEX.json`),')
A('release manifests (`docs/releases/RELEASE_MANIFEST.json`), nav twins')
A('(`docs/INDEX.json`), generated agent index (`docs/agent-index/SYMBOL_INDEX.json`),')
A('per-run result records (`docs/evidence/**.result.json`), golden/expected oracles')
A('(`miniandroid/golden/`), registry (`miniandroid/APK_REGISTRY.json`,')
A('`root_registry.json` at repo root, 349 roots). Raw web-scrape dumps under')
A('`docs/runtime/research/raw/` were removed from the tree in S52 (record:')
A('`docs/evidence/S52_RESIDUE_RECORD.md`); conclusions survive in the research docs.')
A('')
A('## 4. Duplicate / merge candidates (merge only after proof; S52 findings)')
A('')
A('| Files | Finding | Action |')
A('|---|---|---|')
A('| `docs/evidence/SCREENSHOT_INDEX.md`, `_013.md`, `_S51.md` | era screenshot indexes — all superseded by the canonical achievements file | SUPERSEDED pointer added; content frozen |')
A('| `docs/INDEX.md` + `docs/INDEX.json` | twins by design (human + machine) | KEEP both, linked |')
A('| `docs/evidence/CURRENT_COMPATIBILITY_MATRIX.md` vs `docs/compatibility/MASTER_CURRENT_GAP_MATRIX.md` | two compatibility matrices with overlapping scope | MERGE-CANDIDATE — consolidate into `docs/APPLICATION_MATRIX.md` when the matrix lands |')
A('| `docs/CAMPAIGN_FINAL_REPORT*.md`, `MASTER_CAMPAIGN4_FINAL_REPORT.md`, `docs/evidence/campaign014/MASTER4_FINAL_REPORT.md` | era campaign finals, distinct scopes | KEEP as HISTORY (distinct era boundaries; merging would erase them) |')
A('')
A('## 5. Knowledge map — where to read for each pipeline stage')
A('')
A('`Android APK` → Manifest → Resources → DEX → Class loading → Interpreter →')
A('Android API → Lifecycle → View → Layout → Input → Rendering → Storage →')
A('Concurrency → Compose')
A('')
A('| Stage | Upstream knowledge | MiniAndroid implementation | Tests | App evidence | Blocker | Knowledge files |')
A('|---|---|---|---|---|---|---|')
A('| APK/zip | `docs/runtime/knowledge/` (zip/apk structure) | APK parser + `analyze` | battery G06-G08 | every corpus run | — | `docs/runtime/knowledge/*.md` |')
A('| Manifest | AXML docs (`docs/research/`) | AXML decoder, manifest binding | G-chain fixtures | ASC card: Telegram/chessclock manifests | — | research: axml/manifest files |')
A('| Resources/ARSC | ARSC research | aapt2-linked resources, ARSC/style chain (M3) | M3 battery chain | typography goldens | styles edge cases | `G31_FONT_SOURCE.md`, M3 docs |')
A('| DEX/class loading | `docs/runtime/knowledge/` dex files | dalvik_engine.cpp loader | EXP030/032 chain | all runs | — | dex/dalvik knowledge set |')
A('| Interpreter (opcodes) | bytecode docs | real-dalvik interpreter | semantic battery (long/cmp/conv/switch) + EXP052 reg suite | Dooz18 halt = opcode-level evidence | R-NEW-361 ScatterMap long-law | s38 shift-law fixture docs, `R-NEW-361` card |')
A('| Android API (shadows) | EXP032 AOSP reference map | shadow registry | API law battery | per-app REC-MISS counters | long-tail REC-MISS | `EXP032_AOSP_REFERENCE_MAP.md`, `COLLECTION_RUNTIME_STATUS.md` |')
A('| Lifecycle | EXP03x lifecycle research | ActivityThread law chain | F-0xx laws | all SUCCESS apps | fragment-host family R-NEW-331 | lifecycle knowledge set |')
A('| View/Layout | view shadow knowledge | ViewShadow/inflate | hello_widgets golden | unote R-NEW-368 (touch vs paint geometry) | **R-NEW-368** | S38/S39 records |')
A('| Input | AOSP touch law (View.java 17xxx) | tap/long-press pipeline | tictactoe 9/9 | tictactoe L9; chessclock L7 | IME stack boundary | input law docs |')
A('| Rendering | rendering research | frame pipeline + JPG evidence | pixel goldens | 6 full-render apps | blank Compose class `31ddd4d5` | rendering knowledge set |')
A('| Storage | prefs/db laws | SharedPreferences (R-NEW-367), SQLite file | S52 persistence experiment | chessclock/unote round-trip | state-delta ladder pending | R-NEW-367 record |')
A('| Concurrency | Unsafe/atomicfu contract (S39) | shadow dispatch + CAS | S24-COLL probe | dooz23 DI chain | R-NEW-344 recomposer suspension | S39/S40 records |')
A('| Compose | compose sources (`upstream/s43`) | composition machinery | F-016 honesty | dooz23 pipeline; blank frames | **R-NEW-344** + `31ddd4d5` frame class | `docs/upstream/INDEX.md`, S40-S43 records |')
A('| Telegram init | ASC startup card | — (init frontier) | — | 540 s init, no frame | REC-MISS init chain | `docs/evidence/s52_asc/README.md` |')
A('')
A('## 6. Subsystem coverage census (files per subsystem)')
A('')
census = {}
for r in rows:
    census[r['subsys']] = census.get(r['subsys'], 0) + 1
A('| Subsystem | .md files |')
A('|---|---|')
for k, v in sorted(census.items(), key=lambda kv: -kv[1]):
    A(f'| {k} | {v} |')
A('')
A('_Generated by `scripts/s52_gen_knowledge_index.py` — do not hand-edit rows;')
A('hand knowledge belongs in the files themselves._')

open('docs/KNOWLEDGE_INDEX.md', 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print(f'WROTE docs/KNOWLEDGE_INDEX.md: {len(out)} lines; per-file rows={len(perfile)}; era_dirs={len(era_dirs)}; md_total={len(rows)}')
