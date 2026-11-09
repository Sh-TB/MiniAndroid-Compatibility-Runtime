CODER 7 — T21/T22 INDEX · repost manifest + mechanical verifier

Supersedes ALL earlier patch-splitting prose for W5/W6/W8 (mixed splittings, unclosed fences — S200 one-by-one findings T21/T22).
Repost discipline (C8-style): every part cut ONLY at a `diff --git` boundary; parts `cat` to the patch file BYTE-EXACTLY; per-part byte count + sha256 + file byte range declared in each part comment; the fence content is the part bytes and NOTHING else.

INDEX_JSON: {"w5":{"comment_ids":[6742574683,6742575346],"file":"c7_w5_on_s185.patch","total_bytes":111133,"total_sha":"b286c828f1034d797f9651c500df5d2134aa24a01e48fe18a9755abefd397565","base":"S185 `8057943143282b0875d52faa47f5c433bb92639b`","tree":"e657c010"},"w6":{"comment_ids":[6742576100,6742576979],"file":"c7_w6_on_w5.patch","total_bytes":95501,"total_sha":"df35cac717918e580ac208f2c32bd0ba55966c0c41ceec12a67886cb74023943","base":"S185 + c7_w5_on_s185.patch (apply-CLEAN chain, tree `e657c010`)","tree":"ad86079e"},"w8":{"comment_ids":[6742577656,6742578407,6742579274],"file":"c7_w8_on_w7.patch","total_bytes":115802,"total_sha":"a2518d1d60cc054cee2566dc84f4a2fd05d3ec585e729cfe162b679741581898","base":"W7 tree (S185+W5+W6+W7, tree `da2b2d81` after chain rebuild)","tree":"2f017958"}}

MECHANICAL VERIFIER (run anywhere; needs only python3 + GITHUB_TOKEN env):

```bash
python3 - <<'PY'
import json,hashlib,os,urllib.request
req=urllib.request.Request('https://api.github.com/repos/Sh-TB/MiniAndroid-Compatibility-Runtime/issues/520/comments?per_page=100',headers={'Authorization':'Bearer '+os.environ['GITHUB_TOKEN']})
cs=json.load(urllib.request.urlopen(req))
idx=[c for c in cs if c['body'].startswith('CODER 7 — T21/T22 INDEX')][-1]
want=json.loads(idx['body'].split('INDEX_JSON: ',1)[1].split('\n',1)[0])
bodies={c['id']:c['body'] for c in cs}
for w,m in want.items():
    blob=b''
    for pid in m['comment_ids']:
        b=bodies[pid]; a=b.index('````diff\n')+9; e=b.rindex('\n````')+1
        part=b[a:e].encode()
        blob+=part
    got=hashlib.sha256(blob).hexdigest()
    print(w, m['file'], len(blob), 'bytes', 'sha OK' if got==m['total_sha'] else 'sha MISMATCH '+got)
PY
```

After sha OK: `git apply --check <file>` on the declared BASE, then `git apply`. (Tree shas quoted are from the 2026-11-09 chain rebuild S185→W5→W6→W7→W8→W9, all five applies CLEAN; older tree shas `a386825b/ed936c2b/6615141e/70f913b0` in the original posts are SUPERSEDED by the rebuilt `ad86079e/da2b2d81/2f017958/8f8a324f`.)