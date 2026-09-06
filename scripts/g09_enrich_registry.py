#!/usr/bin/env python3
"""g09_enrich_registry.py — add provenance + corpus paths to the G09 registry."""
import hashlib
import json
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MA = REPO / "miniandroid"
REG = REPO / "docs/evidence/g09_corpus/g09_corpus_registry.json"
APKS_JSON = json.loads((MA / "tests/corpus/apks.json").read_text())

# sha256-prefix → (source_url, note)
PROV = {}
for a in APKS_JSON["apks"]:
    PROV[a["sha256"]] = (a["download_url"], a["name"])

EXT01 = "009b467109c4d48d4b00610b06f37f3a77eed75178fbaae344a111acc848cc41"
CONNECTBOT = None
# locate ConnectBot file for hashing
cb = MA / "download/g08_corpus/org.connectbot_11009000.apk"
if cb.exists():
    h = hashlib.sha256()
    h.update(cb.read_bytes())
    CONNECTBOT = h.hexdigest()


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


reg = json.loads(REG.read_text())
for e in reg:
    s = e["sha256"]
    # corpus_rel (relative to miniandroid/)
    for cand in [
        f"download/tictactoe.apk",
        f"download/exp073_real_apps/{e['apk_file']}",
        f"download/exp076_corpus/{e['apk_file']}",
        f"download/g04_corpus/{e['apk_file']}",
        f"download/g08_corpus/{e['apk_file']}",
    ]:
        if (MA / cand).exists() and sha256(MA / cand) == s:
            e["corpus_rel"] = cand
            break
    else:
        if s == EXT01:
            e["corpus_rel"] = None
            e["apk_abs"] = "/home/z/corpus/external_hello/HelloWorldSelfAware-1.1.0-android.apk"
    # provenance
    if s in PROV:
        e["source_url"], e["source_name"] = PROV[s]
    elif s == EXT01:
        e["source_url"] = "https://github.com/Appliberated/HelloWorldSelfAware/releases (v1.1.0)"
        e["source_name"] = "HelloWorldSelfAware (Appliberated)"
    elif CONNECTBOT and s == CONNECTBOT:
        e["source_url"] = "https://f-droid.org/repo/org.connectbot_11009000.apk"
        e["source_name"] = "ConnectBot (F-Droid)"
    e["frozen_date"] = "2026-09-06"

# known drift / dead-URL findings
DRIFT = {
    "com.benny.openlauncher": {
        "corpus_drift": "F-Droid repo file for com.benny.openlauncher_39 now serves "
                        "SHA-256 b3320463a7a1ed46c52464bae83a97317d062b1e2097bd1885cdf265f2089f89; "
                        "the G0x-era frozen manifest recorded b7900f56ccbe4768… (re-signed/republished "
                        "upstream). G09 freezes TODAY's bytes and records both hashes.",
    },
}
for e in reg:
    if e["package"] in DRIFT:
        e["findings"] = DRIFT[e["package"]]

REG.write_text(json.dumps(reg, indent=2, sort_keys=True) + "\n")
print(f"enriched {len(reg)} entries; corpus_rel resolved for "
      f"{sum(1 for e in reg if e.get('corpus_rel') or e.get('apk_abs'))}")
