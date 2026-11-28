#!/usr/bin/env python3
"""T279 P6 — build the MiniAndroid Showcase (manifest + HTML + offline zip).

Outputs to showcase_build/:
  showcase_manifest.json      — machine manifest (179 registry titles, the
                                27 T279-recovered rows carry current-status
                                detail + evidence URLs)
  MiniAndroid-Showcase.html   — responsive static gallery; loads the
                                manifest via fetch() when served over HTTP,
                                falls back to the INLINE embedded manifest
                                when opened from file:// (offline law)
  MiniAndroid-Showcase-Offline.zip — HTML + assets/ (all referenced images
                                local) + showcase_manifest.json

Image law: ONLY genuine runtime captures. Historical screenshots come from
docs/evidence/canonical/ (tracked), current captures from
evidence/t279/shots/ (tracked at T279-A). No stock images anywhere.
"""
import hashlib
import json
import zipfile
from pathlib import Path

BASE = Path("/home/z/my-project")
OUT = BASE / "showcase_build"
ASSETS = OUT / "assets"
OUT.mkdir(exist_ok=True)

RAW = ("https://raw.githubusercontent.com/Sh-TB/MiniAndroid-Compatibility-Runtime/"
       "main/")
CANON_DIR = BASE / "docs/evidence/canonical"
SHOTS_DIR = BASE / "evidence/t279/shots"
LEDGER = BASE / "evidence/t279/SHA256SUMS.txt"

TRACKERS = {  # per-app tracker issues #473-#491
    "de.duenndns.gmdice": 473, "org.telegram.messenger.web": 474,
    "com.emmanuelmess.tictactoe": 475, "com.chessclock.android": 476,
    "omegacentauri.mobi.simplestopwatch": 477, "dubrowgn.microtimer": 478,
    "app.varlorg.unote": 479, "org.billthefarmer.notes": 480,
    "org.debian.eugen.headingcalculator": 481,
    "com.martinmimigames.tinymusicplayer": 482,
    "rkr.simplekeyboard.inputmethod": 483,
    "org.secuso.privacyfriendly2048": 484, "de.saschahlusiak.freebloks": 485,
    "org.kirkezz.rttt": 486, "org.secuso.privacyfriendlydicer": 487,
    "dev.lucanlm.antimine": 488, "com.itsfrz.tictactoe": 489,
    "com.benny.openlauncher": 490, "com.serwylo.lexica": 491,
}
CAMPAIGN_SHOTS = {  # tag -> campaign run ids available
    "gmdice", "bouncy", "pfdicer", "pfsolitaire", "textpad",
    "librecontactsbackup", "uturn", "wocheneinkauf", "peri", "stacktower3d",
    "emmanuelttt", "npuzzle", "ugaday", "blockinger", "farmerbb", "itsfrz",
    "flip", "janken", "diceroller", "authsrng", "minos", "randomix",
    "cocodechess",
}
PKG_TAG = {
    "de.duenndns.gmdice": "gmdice",
    "com.dozingcatsoftware.bouncy": "bouncy",
    "org.secuso.privacyfriendlydicer": "pfdicer",
    "org.secuso.privacyfriendlysolitaire": "pfsolitaire",
    "com.maxistar.textpad": "textpad",
    "com.ashkanrafiee.librecontactsbackup": "librecontactsbackup",
    "ac.stresa.uturn": "uturn",
    "app.wocheneinkauf": "wocheneinkauf",
    "app.simple.peri": "peri",
    "stack.tower3d": "stacktower3d",
    "com.emmanuelmess.tictactoe": "emmanuelttt",
    "name.livitski.games.puzzle.android": "npuzzle",
    "ru.zxalexis.ugaday": "ugaday",
    "org.blockinger.game": "blockinger",
    "com.farmerbb.notepad": "farmerbb",
    "com.itsfrz.tictactoe": "itsfrz",
    "org.ecos.logic.flip_a_coin": "flip",
    "com.attenomy.janken": "janken",
    "tech.gaskell.diceroller": "diceroller",
    "com.ivylopez.authsrng": "authsrng",
    "de.tcrass.minos": "minos",
    "com.minar.randomix": "randomix",
    "dk.cocode.chess": "cocodechess",
}
TAG_CURRENT_RUN = {"uturn": "f1"}  # post-fix capture preferred


def canon_url(artifact_name):
    if artifact_name and (CANON_DIR / artifact_name).exists():
        return RAW + "docs/evidence/canonical/" + artifact_name
    return ""


def shot_url(tag, rid):
    p = SHOTS_DIR / f"{tag}_{rid}.png"
    if p.exists():
        return RAW + "evidence/t279/shots/" + f"{tag}_{rid}.png"
    return ""


def local_asset_name(url):
    return "assets/" + url.rsplit("/", 1)[-1]


def build_manifest():
    reg = json.load(open(BASE / "docs/evidence/canonical/registry.json"))
    entries = []
    for t in reg["titles"]:
        pkg = t["package"]
        tag = PKG_TAG.get(pkg)
        status = t.get("t279_status") or t["status"]
        # current evidence (campaign) beats nothing; historical canonical next
        cur_url = ""
        ct_url = ""
        cur_face = t.get("t279_run1_face16") or ""
        if tag:
            rid = TAG_CURRENT_RUN.get(tag, "r1")
            cur_url = shot_url(tag, rid) or shot_url(tag, TAG_CURRENT_RUN.get(tag, "r1"))
            ct_rid = "ct1"
            ct_url = shot_url(tag, ct_rid)
        hist_url = canon_url(t.get("artifact", "") or
                             (t.get("artifact", "").rsplit("/", 1)[-1]
                              if t.get("artifact") else ""))
        # registry artifact sometimes is a path under docs/evidence/canonical
        if not hist_url and t.get("artifact"):
            name = t["artifact"].rsplit("/", 1)[-1]
            hist_url = canon_url(name)
        entry = {
            "package": pkg,
            "title": t.get("title") or pkg,
            "type": t.get("type") or "app",
            "status": status,                      # T279 8-label (or legacy)
            "status_legacy": t["status"],          # registry claim
            "level_current": t.get("t279_level"),
            "level_hist": t.get("level"),
            "rendered_hist": bool(t.get("rendered")),
            "interacted_hist": bool(t.get("interacted")),
            "state_changed_hist": bool(t.get("state_changed")),
            "interacted_current": bool(t.get("t279_state_changed")),
            "apk_sha256": (t.get("apk_sha256") or "")[:64],
            "engine_commit": t.get("engine_commit") or "344774e66..aa3541195",
            "binary_sha16": t.get("binary_sha16") or "9c5e456b/1a21be9f",
            "last_tested": t.get("t279_last_tested") or t.get("session") or "",
            "session_hist": t.get("session") or "",
            "first_divergence": t.get("first_divergence") or "",
            "notes": (t.get("notes") or "")[:700],
            "root_cause": t.get("root_cause") or "",
            "historical_image": hist_url,
            "current_image": cur_url,
            "current_interaction_image": ct_url,
            "tracker_issue": TRACKERS.get(pkg),
            "ledger_issue": 472,
        }
        entries.append(entry)
    from collections import Counter
    sc = Counter(e["status"] for e in entries)
    legacy = Counter(e["status_legacy"] for e in entries)
    manifest = {
        "generated": "2026-11-28",
        "generator": "scripts/t279_build_showcase.py",
        "source_of_truth": "docs/evidence/canonical/registry.json",
        "engine": {
            "commit_range": "344774e66 (base) -> f9e1d3314 (MeasureSpec fix)",
            "binary_sha16": ["9c5e456b4790299e (pre-fix campaign)",
                             "1a21be9fc9f6b016 (post-fix verification)"],
            "version": "v0.0.6.2+HEAD",
        },
        "status_counts": dict(sc),
        "legacy_status_counts": dict(legacy),
        "counts": {
            "total": len(entries),
            "historical_real": sum(1 for e in entries
                                   if e["status"] == "HISTORICAL-REAL"
                                   or e["status_legacy"] in ("VERIFIED", "OBSERVED")),
            "current_reproducible": sum(1 for e in entries if e["status"] == "CURRENT-REPRODUCIBLE"),
            "interactive": sum(1 for e in entries if e["status"] == "INTERACTIVE"),
            "partial": sum(1 for e in entries if e["status"] == "PARTIAL"),
            "regressed": sum(1 for e in entries if e["status"] == "REGRESSED"),
            "blocked": sum(1 for e in entries if e["status"] == "BLOCKED"),
        },
        "title_count": len(entries),
        "entries": entries,
    }
    json.dump(manifest, open(OUT / "showcase_manifest.json", "w"), indent=1)
    print(f"[showcase] manifest: {len(entries)} entries; counts={manifest['counts']}")
    return manifest


HTML_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>MiniAndroid Showcase — genuine runtime achievements</title>
<style>
:root { --bg:#0f1216; --card:#171c23; --ink:#e8eaed; --mut:#9aa3ad;
        --ok:#79dcd2; --warn:#e8b45a; --bad:#e87a7a; --acc:#8ab4f8; }
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--ink);
       font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; }
main { max-width:1180px; margin:0 auto; padding:clamp(12px,3vw,28px); }
h1 { font-size:clamp(1.6rem,6vw,2.6rem); margin:.2em 0; }
h2 { font-size:clamp(1.2rem,4vw,1.6rem); margin-top:1.6em; }
.sub { color:var(--mut); max-width:70ch; }
.stats { display:grid; gap:10px; grid-template-columns:repeat(auto-fit,minmax(140px,1fr));
         margin:1.2em 0; }
.stat { background:var(--card); border-radius:12px; padding:12px 14px; }
.stat b { display:block; font-size:clamp(1.3rem,4vw,1.9rem); color:var(--ok); }
.stat span { color:var(--mut); font-size:.85rem; }
.controls { display:flex; flex-wrap:wrap; gap:8px; margin:1em 0 1.4em; }
.controls input[type=search] { flex:1 1 240px; min-width:180px; padding:.6em .8em;
    border-radius:10px; border:1px solid #2a313b; background:#1a2027; color:var(--ink); }
.chip { padding:.45em .8em; border-radius:999px; border:1px solid #2a313b;
    background:#1a2027; color:var(--mut); cursor:pointer; font-size:.88rem; }
.chip.on { color:#0f1216; background:var(--ok); border-color:var(--ok); font-weight:600; }
.grid { display:grid; gap:14px; grid-template-columns:repeat(auto-fill,minmax(300px,1fr)); }
.card { background:var(--card); border-radius:14px; overflow:hidden; display:flex;
        flex-direction:column; }
.card header { padding:10px 14px 6px; }
.card h3 { margin:0; font-size:1.05rem; }
.card .pkg { color:var(--mut); font-size:.8rem; word-break:break-all; }
.badges { display:flex; flex-wrap:wrap; gap:6px; padding:4px 14px; }
.badge { font-size:.72rem; padding:.2em .6em; border-radius:999px; font-weight:600; }
.b-CURRENT-REPRODUCIBLE { background:#173a37; color:var(--ok); }
.b-INTERACTIVE { background:#14401f; color:#8ce99a; }
.b-PARTIAL, .b-HISTORICAL-REAL { background:#3a3317; color:var(--warn); }
.b-REGRESSED, .b-BLOCKED { background:#431f1f; color:var(--bad); }
.b-VERIFIED, .b-OBSERVED { background:#1c2a45; color:var(--acc); }
.b-noise { background:#333; color:#aaa; }
.compare { display:flex; gap:8px; padding:8px 14px; }
.compare figure { flex:1; margin:0; min-width:0; }
.compare img { width:100%; height:auto; max-height:280px; object-fit:contain;
    background:#0b0e12; border-radius:8px; cursor:zoom-in; }
.compare figcaption { font-size:.72rem; color:var(--mut); padding-top:3px; }
.card details { padding:6px 14px 12px; color:var(--mut); font-size:.85rem; }
.card details div { margin:.25em 0; word-break:break-word; }
.card details b { color:var(--ink); }
a { color:var(--acc); }
.empty { color:var(--mut); padding:2em 0; }
#lb { position:fixed; inset:0; background:rgba(0,0,0,.88); display:none;
      align-items:center; justify-content:center; cursor:zoom-out; z-index:9; }
#lb img { max-width:96vw; max-height:94vh; }
footer { color:var(--mut); font-size:.8rem; padding:2em 0 3em; max-width:75ch; }
@media (max-width:640px){ .compare { flex-direction:column; } }
</style>
</head>
<body>
<main>
<h1>MiniAndroid Showcase</h1>
<p class="sub">Genuine runtime captures from MiniAndroid — a CPU-first Android APK
compatibility runtime for Linux. Every image below is a screenshot produced by the
MiniAndroid engine executing the original release APK; there are no mockups, no stock
images, and no manually reconstructed app faces. Historical captures and current
reproductions are kept strictly separate: a historical screenshot is evidence of its
own session, never proof of today's engine.</p>
<div class="stats" id="stats"></div>
<h2>Applications &amp; games</h2>
<div class="controls">
  <input id="q" type="search" placeholder="Search by name or package…">
  <span id="chips"></span>
</div>
<div class="grid" id="grid"></div>
<p class="empty" id="empty" hidden>No entries match the current filter.</p>
<footer>
  Evidence chain: original APK (SHA256-pinned) → execution session → engine frame
  census (REAL_APP_CONTENT requires window root + measure + layout + draw + app-owned
  pixels) → screenshot → registry record → this gallery. Current-status captions come
  from the T279 two-run campaign (46/46 byte-identical reproducibility pairs;
  interactive claims additionally require an observable state change). Master ledger:
  <a href="https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/472">issue #472</a>.
  Machine manifest: showcase_manifest.json. Generated 2026-11-28.
</footer>
</main>
<div id="lb"><img id="lbimg" alt=" enlarged evidence capture"></div>
<script>
const MANIFEST_URL = "showcase_manifest.json";
const INLINE = /*MANIFEST_JSON*/;
const STATUS_ORDER = ["INTERACTIVE","CURRENT-REPRODUCIBLE","HISTORICAL-REAL","PARTIAL","REGRESSED","BLOCKED","PENDING","NOISE"];
let DATA=null, FILTER="ALL", QUERY="";
const esc = s => String(s??"").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
function shortSha(s){ return s ? s.slice(0,12)+"…" : "—"; }
function stats(m){
  const c=m.counts, S=document.getElementById("stats");
  const rows=[[c.total,"titles registered"],[c.interactive,"interactive (state change proven)"],
    [c.current_reproducible,"current reproducible (2-run)"],[c.partial,"partial"],
    [c.regressed+0,"regressed (history preserved)"],[c.blocked,"blocked (frontier named)"]];
  S.innerHTML=rows.map(r=>`<div class="stat"><b>${r[0]}</b><span>${r[1]}</span></div>`).join("");
}
function chips(m){
  const el=document.getElementById("chips");
  const all=["ALL",...STATUS_ORDER.filter(s=>m.status_counts[s])];
  el.innerHTML=all.map(s=>`<button class="chip ${s===FILTER?"on":""}" data-s="${s}">${s} (${s==="ALL"?m.title_count:(m.status_counts[s]||0)})</button>`).join(" ");
  el.querySelectorAll(".chip").forEach(b=>b.onclick=()=>{FILTER=b.dataset.s;chips(m);render(m);});
}
function cardHTML(e){
  const imgs=[];
  if(e.current_image) imgs.push(["current_image",e.current_image,"CURRENT reproduction ("+esc(e.status)+") — "+esc(e.last_tested||"")]);
  if(e.current_interaction_image && e.current_interaction_image!==e.current_image) imgs.push(["ct",e.current_interaction_image,"CURRENT after interaction (state change)"]);
  if(e.historical_image) imgs.push(["hist",e.historical_image,"HISTORICAL capture ("+esc(e.status_legacy)+", session "+esc(e.session_hist||"")+")"]);
  const im=imgs.map(i=>`<figure><img src="${i[1]}" loading="lazy" alt="${esc(e.title)} evidence" data-full="${i[1]}" onerror="this.onerror=null;this.src='assets/'+this.dataset.full.split('/').pop()"><figcaption>${i[2]}</figcaption></figure>`).join("");
  const tracker=e.tracker_issue?` · <a href="https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/${e.tracker_issue}">tracker #${e.tracker_issue}</a>`:"";
  return `<article class="card" data-status="${esc(e.status)}" data-q="${esc((e.title+" "+e.package).toLowerCase())}">
  <header><h3>${esc(e.title)}</h3><div class="pkg">${esc(e.package)} · ${esc(e.type)}</div></header>
  <div class="badges"><span class="badge b-${esc(e.status)}">${esc(e.status)}</span>
  <span class="badge b-${esc(e.status_legacy)}">registry: ${esc(e.status_legacy)}</span></div>
  <div class="compare">${im||'<div class="empty">no genuine capture for this status — nothing fabricated</div>'}</div>
  <details><div><b>Render level:</b> ${e.level_current!=null?("R"+e.level_current+" (current) / L"+e.level_hist+" (historical)"):"L"+e.level_hist+" (historical)"}</div>
  <div><b>APK SHA256:</b> ${shortSha(e.apk_sha256)}</div>
  <div><b>Engine:</b> ${esc(e.engine_commit)} · binary ${esc(e.binary_sha16)}</div>
  <div><b>Last tested:</b> ${esc(e.last_tested||e.session_hist||"—")}</div>
  <div><b>First divergence:</b> ${esc(e.first_divergence||"none recorded")}</div>
  <div><b>Notes:</b> ${esc(e.notes)}</div>
  <div><b>Evidence:</b> <a href="https://github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/472">ledger #472</a>${tracker}</div></details>
  </article>`;
}
function render(m){
  const g=document.getElementById("grid");
  const list=m.entries.filter(e=>(FILTER==="ALL"||e.status===FILTER||e.status_legacy===FILTER)
    &&(!QUERY||(e.title+" "+e.package).toLowerCase().includes(QUERY)));
  g.innerHTML=list.map(cardHTML).join("");
  document.getElementById("empty").hidden=list.length>0;
  g.querySelectorAll("img[data-full]").forEach(im=>im.onclick=()=>{
    const lb=document.getElementById("lb");
    document.getElementById("lbimg").src=im.dataset.full; lb.style.display="flex";});
}
document.getElementById("lb").onclick=()=>document.getElementById("lb").style.display="none";
document.getElementById("q").oninput=ev=>{QUERY=ev.target.value.toLowerCase();if(DATA)render(DATA);};
function localize(m){ for (const e of m.entries){ for (const k of ["historical_image","current_image","current_interaction_image"]) if(e[k]) e[k]="assets/"+e[k].split("/").pop(); } return m; }
function boot(m){ DATA=m; stats(m); chips(m); render(m); }
fetch(MANIFEST_URL).then(r=>r.ok?r.json():Promise.reject(r.status))
  .then(boot).catch(()=>boot(localize(INLINE)));
</script>
</body>
</html>
"""


def build_html(manifest):
    inline = json.dumps(manifest, separators=(",", ":"))
    html = HTML_HEAD.replace("/*MANIFEST_JSON*/", inline)
    (OUT / "MiniAndroid-Showcase.html").write_text(html)
    print(f"[showcase] HTML written ({len(html)//1024} KB incl. inline manifest)")


def build_offline(manifest):
    zipp = OUT / "MiniAndroid-Showcase-Offline.zip"
    copied = set()
    with zipfile.ZipFile(zipp, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(OUT / "MiniAndroid-Showcase.html", "MiniAndroid-Showcase.html")
        z.write(OUT / "showcase_manifest.json", "showcase_manifest.json")
        for e in manifest["entries"]:
            for key in ("historical_image", "current_image",
                        "current_interaction_image"):
                url = e.get(key)
                if not url:
                    continue
                name = url.rsplit("/", 1)[-1]
                if name in copied:
                    continue
                src = CANON_DIR / name
                if not src.exists():
                    src = SHOTS_DIR / name
                if src.exists():
                    z.write(src, "assets/" + name)
                    copied.add(name)
    print(f"[showcase] offline zip: {zipp.stat().st_size//1024} KB, "
          f"{len(copied)} images")
    return copied


def main():
    m = build_manifest()
    build_html(m)
    build_offline(m)
    # sha ledger for the published artifacts
    for name in ("MiniAndroid-Showcase.html", "showcase_manifest.json",
                 "MiniAndroid-Showcase-Offline.zip"):
        p = OUT / name
        h = hashlib.sha256(p.read_bytes()).hexdigest()
        print(f"[showcase] sha256 {name}: {h}")


if __name__ == "__main__":
    main()
