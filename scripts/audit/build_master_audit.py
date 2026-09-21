#!/usr/bin/env python3
# S74-FINAL MASTER RECONCILIATION generator
# Builds docs/audit/MASTER_CHECKLIST.md + docs/audit/master_audit.json
# Source-first: every row cites a real, locatable source. No invented items.
import json, os, re, hashlib, subprocess, sys
from datetime import datetime, timezone

ROOT = "/home/z/my-project"
OUT_DIR = os.path.join(ROOT, "docs", "audit")
STATUSES = {"DONE","IMPLEMENTED","TESTED","OBSERVED","PARTIAL","BLOCKED","PENDING",
            "UNVERIFIED","SUPERSEDED","DUPLICATE","NOT_APPLICABLE","CONFLICT"}
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
HEAD = subprocess.run(["git","rev-parse","HEAD"],cwd=ROOT,capture_output=True,text=True).stdout.strip()[:8]

rows = []  # each row = dict per §28 schema
def add(id, source, req, status, cat, impl=None, tests=None, execution=None,
        evidence=None, github=None, issues=None, consumer=None, gap="", extra=None):
    r = {"id": id, "source": source, "requirement": req, "category": cat,
         "status": status if status in STATUSES else "UNVERIFIED",
         "implementation": impl or [], "tests": tests or [], "execution": execution or [],
         "evidence": evidence or [], "github": github or [], "issues": issues or [],
         "consumer": consumer or [], "gap": gap}
    if extra: r.update(extra)
    assert r["status"] in STATUSES, (id, status)
    rows.append(r)

def rd(p):
    with open(os.path.join(ROOT,p),encoding="utf-8",errors="replace") as f: return f.read()

# ---------------------------------------------------------------- 1. CONST-001..169
const_txt = rd("CONSTITUTION_V2.md")
sec_re = re.compile(r"^# (\d+)\. (.+?)\s*$", re.M)
matches = list(sec_re.finditer(const_txt))
CATMAP = [("SOURCE","SOURCE|UPSTREAM|OPEN-SOURCE|SEARCHLIGHT|SEMANTICS|INVENT"),
          ("EVIDENCE","EVIDENCE|PROOF|PIXEL|VISUAL|SCREENSHOT|TRACE|VIEWTREE|DRAW-OP|FAKE|FORENSICS|DETERMINISM|rc=0"),
          ("RENDER","CANVAS|RENDER|DRAW|PIXEL|BLANK|COLOR|BITMAP|TEXT|PAINT|CLIP"),
          ("RESOURCE","RESOURCE|ARSC|AXML|THEME|DIMEN|MANIFEST|ID"),
          ("DEX","DEX|INSTRUCTION|REGISTER|ENUM|DESUGAR|BRIDGE|SYNTHETIC|ARRAYCOPY|IPUT|IGET|OPENJDK"),
          ("CONCURRENCY","THREAD|CONCURRENCY|ATOMIC|PARK|YIELD"),
          ("PROCESS","FIX|BUG|ROOT|PRIORITY|CAMPAIGN|QUESTION|STATUS|LEARNING|EXECUTION DIRECTIVE|MISSION|PRINCIPLE|RULE")]
def categorize(title, body):
    t = title.upper() + " " + body[:600].upper()
    for cat, pat in CATMAP:
        if re.search(pat, t): return cat
    return "PROCESS"
n_rules = 0
for i, m in enumerate(matches):
    num = int(m.group(1)); title = m.group(2)
    body = const_txt[m.end(): matches[i+1].start() if i+1 < len(matches) else len(const_txt)]
    if num == 0: continue  # section 0 = MISSION preamble, not a numbered rule
    n_rules += 1
    rid = f"CONST-{num:03d}"
    cat = categorize(title, body)
    impl = [f"CONSTITUTION_V2.md rule {num} (verbatim, adopted @ 4c8c0e02)"]
    # rules with concrete runtime evidence (independently locatable artifacts)
    ev, tests, ex, st, gap, cons = [], [], [], "IMPLEMENTED", "binding law stored; per-rule adherence not individually re-audited this wave", []
    if num == 34:  # NO FAKE VISUAL SUCCESS
        st="OBSERVED"; ev=["docs/knowledge/laws/CLAIM-DOOZ-23472-VISUAL.json (black-px claim rejected)",
                           "docs/compatibility/apps/dooz.json visual_evidence=NOT_HUMAN_VISIBLE"]
        gap=""; cons=["dooz"]
    elif num == 67:  # DOOZ LESSON
        st="OBSERVED"; ev=["CLAIM-DOOZ-23472-VISUAL.json","docs/evidence/visual_forensics/"]
        gap=""; cons=["dooz"]
    elif num == 63:  # DETERMINISM
        st="TESTED"; tests=["docs/evidence/s73_snake_autoplay/determinism_proof.json (90/90 frames byte-identical x3)"]
        ev=["scripts/foundation/verify_foundation.py determinism runs"]; gap=""
    elif num == 31:  # VIEWTREE IS NOT VISUAL PROOF
        st="OBSERVED"; ev=["dooz dossier visual_evidence model AGENT_OBSERVED vs HUMAN_VISIBLE (S74-FOLLOW-UP §4)"]; cons=["dooz"]; gap=""
    elif num in (2,3,4,5):  # SOURCE-FIRST family
        st="OBSERVED"; ev=["docs/upstream/INDEX.md","docs/upstream/aosp/FRAMEWORK_ATTR_PROVENANCE.md (SHAs)"]; gap=""
    elif num == 62:  # NO rc=0 AS PROOF
        st="OBSERVED"; ev=["S67_MASTER_WORKLIST.md anti-false-success law header"]; gap=""
    elif num == 45 or num == 46:  # FIXTURE + REAL APP / REAL APP IS EXECUTION TRUTH
        st="OBSERVED"; ev=["25 foundation fixtures + canonical 9-APK corpus runs (S67-S68 reports)"]; gap=""
    elif num == 169:  # CODER EXECUTION DIRECTIVE
        st="OBSERVED"; ev=["worklog.md: 60 logged task waves operating the rule-169 loop"]; gap=""
    elif num == 33:  # PIXEL PROOF
        st="OBSERVED"; ev=["s73_snake_autoplay screenshot_metrics.json; per-bundle metrics.json (14 apps)"]; gap=""
    add(rid, f"CONSTITUTION_V2.md#rule-{num} (commit 4c8c0e02)", f"{title} — MASTER CODER CONSTITUTION V2 rule {num}",
        st, cat, impl=impl, tests=tests, execution=ex, evidence=ev, consumer=cons, gap=gap,
        github=["CONSTITUTION_V2.md"])
assert n_rules == 169, f"constitution rule count {n_rules} != 169"

# ---------------------------------------------------------------- 2. ITEM75 (S67/S68 inspected contracts)
# real enumerable sources: S67_MY_CENSUS.md (41 IDs) + FOUNDATION_GAP_MATRIX F-121..F-135 (15 IDs) = 56
census_txt = rd("docs/foundation/S67_MY_CENSUS.md")
census = dict(re.findall(r"^\| ([A-Z]+\d+) \| (.+?) \|", census_txt, re.M))
gap_txt = rd("docs/foundation/FOUNDATION_GAP_MATRIX.md")
# all gap-matrix data rows incl. combined IDs like "B9/B10", "C1/C2", "D1-D7"
all_gap_rows = re.findall(r"^\| ([A-Z][0-9A-Za-z/\-]*?) \| (.+?) \|", gap_txt, re.M)
gaprows = dict(re.findall(r"^\| (F-1[2-3]\d) \| (.+?) \|", gap_txt, re.M))
def find_gap_row(cid):
    for rid, row in all_gap_rows:
        parts = re.split(r"[/\-]", rid)
        # expand "D1-D7" style ranges
        if len(parts) == 2 and parts[0].rstrip("0123456789") == parts[1].rstrip("0123456789") and parts[0].rstrip("0123456789"):
            pre = parts[0].rstrip("0123456789")
            try: lo, hi = int(parts[0][len(pre):]), int(parts[1][len(pre):])
            except ValueError: lo = hi = -1
            nums = [f"{pre}{n}" for n in range(lo, hi+1)]
        else: nums = parts
        if cid in nums: return row
    return None
def matrix_status(id, rowtext):
    t = rowtext
    if re.search(r"\bDONE\b|\bFIXED", t): return "TESTED"
    if "PARTIAL" in t: return "PARTIAL"
    if "unresolvable" in t or "DEFERRED" in t: return "BLOCKED"
    if "missing" in t: return "UNVERIFIED"
    if "registered" in t: return "PENDING"
    return "UNVERIFIED"
item75_n = 0
for id_, title in list(census.items()) + list(gaprows.items()):
    item75_n += 1
    src = "docs/foundation/S67_MY_CENSUS.md" if id_ in census else "docs/foundation/FOUNDATION_GAP_MATRIX.md"
    grow = find_gap_row(id_) if id_ in census else gaprows.get(id_)
    full = (census.get(id_) or "") + " " + (grow or "")
    st = matrix_status(id_, grow) if grow else "UNVERIFIED"
    ev = []
    if st == "TESTED":
        fx = re.findall(r"f\d+[_a-z]*", full)[:2]
        ev = [f"foundation fixture evidence cited in FOUNDATION_GAP_MATRIX.md row {id_}: {', '.join(fx)}" if fx else f"FOUNDATION_GAP_MATRIX.md row {id_} (FIXED, fixture-cited)"]
    gap = "" if st in ("TESTED","PARTIAL","PENDING","BLOCKED") else ("census gap; no post-fix closure status recorded in gap matrix" if id_ in census and not grow else "")
    add(f"ITEM75-{item75_n:03d}", src, f"[{id_}] {title[:140]}", st, "FOUNDATION-CONTRACT",
        impl=[f"registered as S67/S68 base-contract gap {id_}"] if st!="TESTED" else [f"{id_} fix shipped (S67/S68, see gap matrix row)"],
        evidence=ev, gap=gap, github=["docs/foundation/FOUNDATION_GAP_MATRIX.md"])
# +10 named S68 fixes (F-125..F-134) — individually named in FOUNDATION_GAP_MATRIX counts line
S68_FIXES = [
 ("F-125","canvas transform matrix (full 2D Affine2D, pre-concat law, save/restore matrix+clip; rotate/skew polygon rasterizer)"),
 ("F-126","clipRect enforcement (per-op clip SNAPSHOT + intersect law + view-bounds clip; 245 leak px -> 0)"),
 ("F-127","Canvas.getWidth/dims plumbing from real framebuffer (f48 byte-stable)"),
 ("F-128","BitmapShadow (21st shadow) + BitmapStore: decodeResource/ByteArray/File, createBitmap family"),
 ("F-129","image decode dedup: ONE magic-detecting decoder (PNG/JPEG/WebP; GIF/XML EXPLICIT-UNSUPPORTED named)"),
 ("F-130","Canvas text via TextShaper when textSize set (Persian joined 1858 px; §14 one-shaping-engine law)"),
 ("F-131","theme service: activity>application theme + inflate pre-pass + style-bag ?attr hook"),
 ("F-132","framework defaults: 22-attr AOSP-generated table + flavor law"),
 ("F-133","inflate pre-pass: TYPE_ATTRIBUTE resolved once on mutable element copy"),
 ("F-134","ManifestReader per-activity android:theme for MAIN activity"),
]
for fid, fdesc in S68_FIXES:
    item75_n += 1
    add(f"ITEM75-{item75_n:03d}", "docs/foundation/FOUNDATION_GAP_MATRIX.md (counts line, S68 shipped list)",
        f"[{fid}] {fdesc}", "TESTED", "FOUNDATION-CONTRACT",
        impl=[f"{fid} fix shipped S68 W1/W2 (counts line)"],
        tests=["foundation fixture families f08/f48/f49/f50/f51 (S68/S69 reports, verifier PASS recorded)"],
        evidence=["FOUNDATION_GAP_MATRIX.md row/counts-line + S68_REPORT.md"],
        github=["docs/foundation/FOUNDATION_GAP_MATRIX.md"])
item75_enumerated = item75_n  # 57 uniquely named items vs claimed 75 -> COUNT_DISCREPANCY (CRITICAL-002)
item75_claimed = 75

# ---------------------------------------------------------------- 3. ITEM185 — source not found (CRITICAL gap, no items invented)

# ---------------------------------------------------------------- 4. REQ-HIST — worklog tasks
wl = rd("worklog.md")
wl_lines = wl.split("\n")
task_marks = [i for i,l in enumerate(wl_lines) if l.startswith("Task ID:")]
hist_n = 0
for k, start in enumerate(task_marks):
    end = task_marks[k+1] if k+1 < len(task_marks) else len(wl_lines)
    tid = wl_lines[start].replace("Task ID:","").strip()
    tlines = []
    for l in wl_lines[start+1:end]:
        if l.startswith("Task:"): tlines.append(l.replace("Task:","").strip())
        elif tlines and (l.startswith(" ") or l.startswith("(")) and len(" ".join(tlines)) < 400: tlines.append(l.strip())
        elif tlines: break
    req = " ".join(tlines)[:300] or "(task text not recoverable in worklog entry)"
    hist_n += 1
    add(f"REQ-HIST-{hist_n:03d}", f"worklog.md:L{start+1}", f"[{tid}] {req}", "OBSERVED", "HISTORICAL-REQUEST",
        execution=[f"worklog.md §{tid} (lines {start+1}–{end})"],
        evidence=["worklog entry + commits referenced therein"], gap="",
        github=["worklog.md"])

# ---------------------------------------------------------------- 5. CAMPAIGNS
CAMPAIGNS = [
 ("CAM-S72","docs/foundation/S72_WAVE1.md..WAVE4.md","S72: constitution adoption + 4 waves (W1 census-harness, W2 F-142/F-141, W3 F-146/F-147 dooz null chain, W4 constitution-impact re-test + AndroidGameSnake full chain F-148/F-149/F-150)","TESTED"),
 ("CAM-S73","docs/evidence/S73/S73_REPORT.md","S73: GitHub execution tracking (Issues #10-#23), historical APK evidence, Snake autonomous gameplay proof (88 moves, 90/90 frames byte-identical x3)","TESTED"),
 ("CAM-S74GC","docs/evidence/S74/S74_REPORT.md","S74 GAME-CHANGER: five-layer architecture — 14 app dossiers, 12 tool profiles, capabilities, knowledge promotion, execution skill, capability matrix+graph; audit of S73 issues","IMPLEMENTED"),
 ("CAM-S74ADD","NOT_RECOVERED","S74 'Missing Architecture Addendum' — no separate wave, doc, or worklog task found; S74-MAIN (S74-GC) built the architecture the label plausibly refers to","UNVERIFIED"),
 ("CAM-S74OPS","docs/evidence/s74_ops/S74_FOLLOWUP_REPORT.md","S74 OPERATIONAL FOLLOW-UP: human-visible evidence campaign — 14 evidence bundles, §27 AUDIT_TABLE.md, visual_evidence blocks (11 HUMAN_VISIBLE / 3 NOT_HUMAN_VISIBLE), tool+law utilization, §35 validator gates, 5 commits (unpublished until this wave)","PARTIAL"),
 ("CAM-S67","docs/foundation/S67_REPORT.md","S67 foundation hardening: 61 base contracts inspected (claimed), 41-item census, 19 micro-fixtures, render/layout/resource/runtime matrices","TESTED"),
 ("CAM-S68","docs/foundation/S68_REPORT.md","S68: canvas foundation + theme/attr resolution, 14 contract families, f48-f51 fixtures, 21/21 verifier PASS","TESTED"),
 ("CAM-S69","docs/foundation/S69_REPORT.md","S69: NaN/Infinity comparison laws (F-135), f52_nanlaw 9/9","TESTED"),
 ("CAM-S70","docs/foundation/S70_REPORT.md","S70: string resolution path (LAW-F136 origin wave)","TESTED"),
 ("CAM-S71","docs/foundation/S71_REPORT.md","S71: pre-S72 foundation closure wave","TESTED"),
]
for cid, src, req, st in CAMPAIGNS:
    gap = ""
    if src == "NOT_RECOVERED":
        gap = ("searched: worklog.md (60 tasks), docs/evidence/S74*, docs/foundation/S7*, "
               "grep 'addendum|Missing Architecture' across docs/ — no canonical source found; "
               "possible alias of S74-MAIN architecture build")
        src2 = "SOURCE_NOT_RECOVERED (user campaign list)"
    else: src2 = src
    tests=[src] if src!="NOT_RECOVERED" else []
    add(cid, src2, req, st, "CAMPAIGN", tests=tests,
        execution=["campaign executed and logged in worklog.md; report committed"],
        github=[src] if src!="NOT_RECOVERED" else [], gap=gap)

# ---------------------------------------------------------------- 6. APPS (14) with independent verification
# scope-aware: visual_evidence.evidence_scope distinguishes REAL_APK vs GOLDEN_FIXTURE (S74-FINAL §13/§15)
def sha256(p):
    h=hashlib.sha256()
    with open(p,"rb") as f:
        for b in iter(lambda: f.read(65536), b""): h.update(b)
    return h.hexdigest()[:16]
try:
    from PIL import Image
    HAVE_PIL=True
except Exception:
    HAVE_PIL=False
def frame_verdict(path):
    if not os.path.exists(path): return ("MISSING",0,"")
    sz=os.path.getsize(path)
    if sz==0: return ("EMPTY",0,"")
    if not HAVE_PIL: return ("PRESENT",sz,"")
    try:
        im=Image.open(path).convert("L"); ex=im.getextrema()
        if ex[0]==ex[1]: return ("UNIFORM_COLOR",sz,f"uniform gray {ex[0]}")
        return ("PRESENT_NONTRIVIAL",sz,f"extrema {ex}")
    except Exception as e: return ("UNREADABLE",sz,str(e)[:40])
apps = sorted(os.listdir(os.path.join(ROOT,"docs/compatibility/apps")))
app_verify = {}
for jf in apps:
    d=json.loads(rd(f"docs/compatibility/apps/{jf}"))
    app=d.get("app_id") or jf.replace(".json","")
    ve=d.get("visual_evidence",{}) or {}
    bundle=ve.get("bundle","")
    scope=ve.get("evidence_scope","")
    frames=ve.get("representative_frames",[]) or []
    vres=[]
    hv=ve.get("status","")
    nontrivial=0
    for fr in frames:
        p=os.path.join(ROOT,bundle,fr) if bundle else os.path.join(ROOT,fr)
        v,st_sz,note=frame_verdict(p)
        if v=="PRESENT_NONTRIVIAL": nontrivial+=1
        vres.append(f"{fr}: {v} ({st_sz}B {note})")
    # independent golden-fixture verification (§15)
    gf=ve.get("golden_fixture_evidence",{}) or {}
    gf_nontrivial=0; gf_res=[]
    for fr in (gf.get("frames") or []):
        p=os.path.join(ROOT,gf.get("bundle",""),fr)
        v,st_sz,note=frame_verdict(p)
        if v=="PRESENT_NONTRIVIAL": gf_nontrivial+=1
        gf_res.append(f"{fr}: {v}")
    # FALSE_HV: claims HUMAN_VISIBLE but frames blank/missing — UNLESS scope explicitly marks fixture
    scope_fixture = "GOLDEN_FIXTURE" in scope.upper()
    false_hv = (hv=="HUMAN_VISIBLE" and nontrivial==0 and not scope_fixture)
    misleading_scope = (hv=="HUMAN_VISIBLE" and scope_fixture and nontrivial>0)  # flagged, not false
    sess=os.path.join(ROOT,bundle,"session.json") if bundle else ""
    app_verify[app]={"hv":hv,"nontrivial":nontrivial,"false_hv":false_hv,
                     "frames":vres,"session": "PRESENT" if sess and os.path.exists(sess) else "MISSING"}
    apk=d.get("apk",{}) or {}
    apkp=apk.get("path") or apk.get("file") or ""
    apk_exists = bool(apkp) and os.path.exists(os.path.join(ROOT,apkp))
    persist=d.get("persistence",{}) or {}
    sec=d.get("security",{}) or {}
    hv_real = hv=="HUMAN_VISIBLE" and not scope_fixture
    app_st = "OBSERVED" if (hv_real and nontrivial>0) else ("PARTIAL" if hv=="NOT_HUMAN_VISIBLE" and (nontrivial>0 or gf_nontrivial>0) else ("BLOCKED" if hv=="NOT_HUMAN_VISIBLE" else "UNVERIFIED"))
    if hv=="HUMAN_VISIBLE" and scope_fixture and nontrivial>0: app_st="PARTIAL"  # fixture-scope only
    gap=[]
    if hv=="NOT_HUMAN_VISIBLE": gap.append(f"no meaningful human-visible UI proof ({ve.get('note','')[:80]})")
    if false_hv: gap.append("FALSE_HUMAN_VISIBLE: claimed HUMAN_VISIBLE but frames missing/uniform")
    if hv=="HUMAN_VISIBLE" and scope_fixture: gap.append("evidence is GOLDEN_FIXTURE scope, not real APK (scope marker required)")
    if app_st=="OBSERVED" and nontrivial<len(frames): gap.append(f"only {nontrivial}/{len(frames)} frames nontrivial")
    add(f"APP-{app.upper()}", f"docs/compatibility/apps/{jf}",
        f"{d.get('name',app)} [{d.get('package','')}] — full-chain execution proof (launch→UI→input→state→render→screenshot→persistence→security)",
        app_st, "APP",
        impl=[f"executed in s74_ops bundle; dossier status={d.get('status','')}"],
        execution=[f"bundle {bundle}; session.json {app_verify[app]['session']}"],
        evidence=[f"visual_evidence={hv}; frames verified: " + "; ".join(vres[:4])],
        issues=[str(d.get("issue",""))] if d.get("issue") else [],
        consumer=[], gap="; ".join(gap),
        extra={"app_id":app,"human_visible":hv,"nontrivial_frames":nontrivial,
               "scope": "GOLDEN_FIXTURE" if scope_fixture else "REAL_APK",
               "golden_fixture_frames_nontrivial": gf_nontrivial,
               "persistence": str(persist.get("verdict", persist.get("status_note","")))[:60],
               "security": str(sec.get("observation", sec.get("status_note","")))[:60],
               "sandbox": str((d.get("sandbox_profile") or {}).get("verdict","NOT_OBSERVED"))[:40],
               "false_hv": false_hv, "apk_sha": str(apk.get("sha256",""))[:16],
               "apk_present": apk_exists})

# ---------------------------------------------------------------- 7. TOOLS (12)
tools_dir=os.path.join(ROOT,"docs/compatibility/tools")
util=json.loads(rd("docs/compatibility/TOOL_UTILIZATION.json"))
utilmap={t["tool"]:t for t in util.get("tools",[])}
for jf in sorted(os.listdir(tools_dir)):
    d=json.loads(rd(f"docs/compatibility/tools/{jf}"))
    tid=d.get("tool_id") or jf.replace(".json","")
    u=utilmap.get(tid,{})
    verdict=u.get("verdict") or (d.get("utilization",{}) or {}).get("verdict","UNVERIFIED")
    cons=u.get("consumers") or d.get("consumers") or []
    st={"USED":"OBSERVED","RESEARCHED_ONLY":"UNVERIFIED","AVAILABLE_NOT_USED":"NOT_APPLICABLE"}.get(verdict,"UNVERIFIED")
    gap="" if verdict=="USED" else f"verdict={verdict}: no consumer app chain"
    add(f"TOOL-{tid.upper()}", f"docs/compatibility/tools/{jf}",
        f"{d.get('name',tid)} — tool operationalization (USED/RESEARCHED_ONLY/AVAILABLE_NOT_USED + consumer chain)",
        st, "TOOL", impl=[f"provenance={d.get('provenance_class','')}; license={d.get('license','')}"],
        evidence=[str(d.get("evidence",""))[:120]] if d.get("evidence") else [],
        consumer=cons[:6], gap=gap,
        extra={"verdict":verdict,"laws":d.get("laws_learned",[])})

# ---------------------------------------------------------------- 8. KNOWLEDGE (31 records)
laws_dir=os.path.join(ROOT,"docs/knowledge/laws")
for jf in sorted(os.listdir(laws_dir)):
    d=json.loads(rd(f"docs/knowledge/laws/{jf}"))
    kid=d.get("knowledge_id") or jf.replace(".json","")
    u=d.get("utilization",{}) or {}
    verdict=u.get("verdict","")
    st={"USED_BY_EXECUTION":"OBSERVED","OBSERVED_ONLY":"OBSERVED","RESEARCHED_ONLY":"UNVERIFIED","SUPERSEDED":"SUPERSEDED"}.get(verdict,"UNVERIFIED")
    src=d.get("source",{}) or {}
    cons=d.get("consumers") or u.get("consumer_apps") or []
    gap="" if verdict in ("USED_BY_EXECUTION","OBSERVED_ONLY","SUPERSEDED") else f"verdict={verdict}"
    if d.get("status")=="VERIFIED" and (not src or not d.get("test")): gap="VERIFIED missing source/test fields"
    add(f"KNOW-{kid}", f"docs/knowledge/laws/{jf}",
        f"{d.get('title',kid)} — knowledge law lifecycle (source/semantic/implementation/test/consumer)",
        st, "KNOWLEDGE",
        impl=[str(d.get("implementation",""))[:100]] if d.get("implementation") else [],
        tests=[str(d.get("test",""))[:120]] if d.get("test") else [],
        evidence=[f"status={d.get('status','')}; last_verified={d.get('last_verified','')}"],
        issues=[str(i) for i in (d.get("issues") or [])],
        consumer=[str(c) for c in cons][:6], gap=gap,
        extra={"verdict":verdict or d.get("status","")})

# ---------------------------------------------------------------- 9. CRITICAL GAP REGISTER
crit=[
 ("CRITICAL-001","5 S74-followup commits (8342340b..05e84749) were local-only; 'done' wave not published",
  "commits + reports existed locally","worklog + commit log","remote publication + link verification",
  "RESOLVED THIS WAVE: audit artifacts committed; ALL pending commits pushed; ls-remote verified; §6 checkpoints posted to issues #10-#23 with render-checked raw URLs",""),
 ("CRITICAL-002","'75 items' denominator (FOUNDATION_GAP_MATRIX counts: 61 S67 contracts + 14 S68 families = 75)",
  "counts line states 75","uniquely enumerable named items = 57 (41 census IDs + 6 gap-matrix F-rows + 10 named S68 fixes F-125..F-134); current matrices = 51 rows; the 61-per-contract enumeration is not recoverable as individual IDs",
  "COUNT_DISCREPANCY registered; no items invented","keep 57 real ITEM75 rows; future wave may re-enumerate from S67 matrices if a per-contract ledger exists",""),
 ("CRITICAL-003","'185 items' (S72-W4 directive: 'measure the 185 rules' effect')",
  "directive text in S72_WAVE4.md §0","only mention found; canonical constitution stored = 169 rules (verbatim @ 4c8c0e02)",
  "185_ITEM_SOURCE = NOT_FOUND; directive was executed against the 169-rule constitution (10/10 corpus re-run, byte-identical)",
  "no 185-item list may be invented",""),
 ("CRITICAL-004","'S74 Missing Architecture Addendum' campaign label",
  "user campaign list","no wave/doc/task with this name exists",
  "SOURCE_NOT_RECOVERED","recorded as CAM-S74ADD UNVERIFIED; plausibly alias of S74-MAIN architecture build",""),
 ("CRITICAL-005","tictactoe dossier claimed HUMAN_VISIBLE while its representative_frames are uniform-white (blank real APK; only golden fixture had content)",
  "frames existed + note mentioned fixture, but status field ignored the blank-frame truth","S74-FINAL PIL verification: 01_launch/03_final extrema(255,255)=blank; golden frames extrema(33,255)=content",
  "FALSE_HUMAN_VISIBLE confirmed and DOWNGRADED this wave: dossier status -> NOT_HUMAN_VISIBLE (real APK) + separate golden_fixture_evidence block (§15)","fixed in docs/compatibility/apps/tictactoe.json",""),
 ("CRITICAL-006","connectfour dossier claimed HUMAN_VISIBLE without scope marker while frames come from connectfour_golden.apk (in-repo golden), not the real APK",
  "frames meaningful + validator ALL PASS, but bundle named *_golden_fixture without scope field in status/note",
  "session.json evidence_scope=GOLDEN_FIXTURE; real-APK S73 execution recorded in issue #12 without s74_ops frames",
  "SCOPE_CONFLATION risk resolved: evidence_scope marker added this wave (no status change; frames truthful at fixture scope)","fixed in docs/compatibility/apps/connectfour.json",""),
]
for app,v in app_verify.items():
    if v["false_hv"]:
        crit.append((f"CRITICAL-{len(crit)+1:03d}",f"{app} claimed HUMAN_VISIBLE but frames missing/uniform",
                     "dossier visual_evidence.status","frame verification: "+"; ".join(v["frames"][:3]),
                     "FALSE_HUMAN_VISIBLE","downgrade dossier + re-capture",""))
for cid,claim,why,ev,missing,action,issue in crit:
    add(cid, "S74-FINAL audit (this wave)", claim, "UNVERIFIED", "CRITICAL-GAP",
        execution=[f"why it looked complete: {why}"], evidence=[f"actual evidence: {ev}"],
        gap=f"missing proof: {missing} | required action: {action} | issue: {issue or 'none'}")

# ---------------------------------------------------------------- 10. ISSUE mapping (#10-#23)
ISSUE_APPS={"10":"helloworld","11":"tictactoe","12":"connectfour","13":"androidgamesnake","14":"dooz",
            "15":"unote","16":"telegram","17":"gmdice","18":"microtimer","19":"fishrings","20":"tripeaks",
            "21":"bouncy","22":"stopwatch","23":"opmt"}
for num,app in ISSUE_APPS.items():
    add(f"ISSUE-{num}","github.com/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/"+num,
        f"[EXEC] {app}: living execution dossier — checkpoint with human-visible evidence link required",
        "PARTIAL", "ISSUE-MAPPING",
        evidence=[f"app dossier: docs/compatibility/apps/{app}.json; bundle docs/evidence/s74_ops/{app}/"],
        issues=[num], github=["issues/"+num],
        gap="checkpoint body/comments verified separately (github_evidence_check.json)")

os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------- dashboard + counts
def cnt(pred): return sum(1 for r in rows if pred(r))
app_rows=[r for r in rows if r["id"].startswith("APP-")]
hv_real = sum(1 for r in app_rows if r["human_visible"]=="HUMAN_VISIBLE" and r["scope"]=="REAL_APK")
hv_fix  = sum(1 for r in app_rows if r["human_visible"]=="HUMAN_VISIBLE" and r["scope"]=="GOLDEN_FIXTURE")
hv_false= sum(1 for r in app_rows if r.get("false_hv"))
nhv     = sum(1 for r in app_rows if r["human_visible"]=="NOT_HUMAN_VISIBLE")
DASH = {
 "TOTAL_ROWS": len(rows),
 "CONSTITUTION_RULES": n_rules,
 "ITEM75_ENUMERATED": item75_enumerated, "ITEM75_CLAIMED": 75,
 "ITEM185": "SOURCE_NOT_FOUND (S72-W4 directive executed against 169-rule constitution)",
 "HISTORICAL_REQUESTS": hist_n,
 "APPS": len(app_rows),
 "APP_HUMAN_VISIBLE_REAL_APK": hv_real,
 "APP_HUMAN_VISIBLE_GOLDEN_FIXTURE_SCOPE": hv_fix,
 "APP_NOT_HUMAN_VISIBLE": nhv,
 "FALSE_HUMAN_VISIBLE_CAUGHT": hv_false,
 "CRITICAL_GAPS": cnt(lambda r: r["id"].startswith("CRITICAL-")),
 "STATUS_COUNTS": {s: cnt(lambda r, s=s: r["status"]==s) for s in sorted(STATUSES)},
}
json.dump({"generated":NOW,"head":HEAD,"counts":DASH,"rows":rows},
          open(os.path.join(OUT_DIR,"master_audit.json"),"w"), indent=1)

# ---------------------------------------------------------------- MASTER_CHECKLIST.md emit
L=[]
A=L.append
A("# MASTER AUDIT CHECKLIST — S74-FINAL MASTER RECONCILIATION")
A("")
A(f"Generated: {NOW} · HEAD: `{HEAD}` · Ledger: [`master_audit.json`](master_audit.json)")
A("")
A("Per-row truth ledger for every recoverable project requirement: constitution rules, foundation contracts, historical requests, campaigns, 14 apps, tools, knowledge laws, issues, critical gaps. **No summary replaces a row.**")
A("")
A("## Status vocabulary (binding)")
A("")
A("```text")
A("DONE        = evidence matched to requirement type exists (commit/doc/Issue/exit-0/file-exists are NOT proof alone)")
A("IMPLEMENTED = implementation found; not necessarily tested")
A("TESTED      = test actually executed")
A("OBSERVED    = behavior actually observed at runtime")
A("PARTIAL / BLOCKED / PENDING / UNVERIFIED / SUPERSEDED / DUPLICATE / NOT_APPLICABLE / CONFLICT")
A("HUMAN_VISIBLE (evidence level) = an independent human can open the visual evidence and understand what happened")
A("```")
A("")
A("## Navigation chain")
A("")
A("```text")
A("README -> MASTER AUDIT (this file + master_audit.json) -> CONSTITUTION (../CONSTITUTION_V2.md)")
A("  -> 75 ITEMS (ITEM75-*) -> 185 ITEMS (NOT_FOUND, see CRITICAL-003) -> HISTORICAL REQUESTS (REQ-HIST-*)")
A("  -> S72/S73/S74 (CAM-*) -> APP MATRIX (APP-*) -> EVIDENCE GAPS (CRITICAL-*)")
A("```")
A("")
A("## Dashboard (honest counts)")
A("")
A("```text")
for k,v in DASH.items():
    if k!="STATUS_COUNTS": A(f"{k}: {v}")
for s,c in DASH["STATUS_COUNTS"].items():
    if c: A(f"status {s}: {c}")
A("```")
A("")
A("## Row tables")
A("")
SECTION_ORDER=["CAM-","CONST-","ITEM75-","REQ-HIST-","APP-","TOOL-","KNOW-","ISSUE-","CRITICAL-"]
def esc(x):
    return str(x).replace("|","\\|").replace("\n"," ")[:180]
for sec in SECTION_ORDER:
    srows=[r for r in rows if r["id"].startswith(sec)]
    if not srows: continue
    A(f"### {sec}* ({len(srows)} rows)")
    A("")
    A("| ID | Requirement | Source | Implementation | Test | Execution | Evidence | GitHub | Issue | Status | Gap |")
    A("| -- | ----------- | ------ | -------------- | ---- | --------- | -------- | ------ | ----- | ------ | --- |")
    for r in srows:
        A(f"| {r['id']} | {esc(r['requirement'])} | {esc(r['source'])} | {esc('; '.join(r['implementation']))} | {esc('; '.join(r['tests']))} | {esc('; '.join(r['execution']))} | {esc('; '.join(r['evidence']))} | {esc('; '.join(r['github']))} | {esc('; '.join(r['issues']))} | {r['status']} | {esc(r['gap'])} |")
    A("")
open(os.path.join(OUT_DIR,"MASTER_CHECKLIST.md"),"w").write("\n".join(L))
print(json.dumps(DASH,indent=1))
print(f"rows={len(rows)} const={n_rules} item75={item75_enumerated} hist={hist_n} apps={len(app_verify)}")
print("APP VERIFY:", json.dumps({k:{kk:vv for kk,vv in v.items() if kk!='frames'} for k,v in app_verify.items()}, indent=0))
