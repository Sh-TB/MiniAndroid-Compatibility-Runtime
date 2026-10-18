#!/usr/bin/env python3
"""CONT-94 app-registry refresh: APP-012 Telegram + APP-013 WhatsApp +
Forkgram row, re-graded at current HEAD (7cf6fe7f3d6abb81) with honest
per-checkpoint states from the CONT-94 evidence runs."""
import json

REG = "canonical/app_registry.json"
d = json.load(open(REG))
apps = d["apps"]


def upsert(app_id, patch):
    for a in apps:
        if a.get("id") == app_id:
            a.update(patch)
            return
    a = {"id": app_id}
    a.update(patch)
    apps.append(a)


upsert("APP-012", {
    "id": "APP-012",
    "title": "Telegram official (org.telegram.messenger.web 12.10.5 vc71059, sha16 e37aced2a49c1dbb)",
    "package": "org.telegram.messenger.web",
    "status": "PARTIAL",
    "checkpoints": {"L0": True, "L1": True, "L2": True, "L3": True, "L4": True, "L5": False, "L7": False},
    "note": ("CONT-94 F-NEW-396 fix: getParentActivity live-identity law ended the "
             "synthetic-activity NPE chain (H x3 -> APP-BOUNDARY unwind x3). Login screen "
             "now paints REAL app-owned pixels: '+' country-code box, phone-field borders, "
             "accent-blue text (9340/2073600 non-white, top-anchored — bounds/offset "
             "frontier named). Pre-fix face was 188 px (3 grey colors, NOT a render). "
             "Remaining uncaught 15 (billing UOE chain, UnsatisfiedLinkError native-lib "
             "boundary, FirebaseInitProvider Ll9/j) — boot-init boundaries, not UI."),
    "sessions": "S123/S124 + CONT-94",
    "evidence_refs": [
        "run/cont94/tg_post1/screenshot.png",
        "run/cont94/tg_official_1/stderr.log (pre face)",
        "evidence/cont94/evidence.json",
    ],
})

upsert("APP-013", {
    "id": "APP-013",
    "title": "WhatsApp 2.26.38.74 (upload/whatsapp.apk is a 5,615-byte stub, NOT a usable artifact)",
    "package": "com.whatsapp",
    "status": "BLOCKED",
    "checkpoints": {"L0": False, "L1": False, "L2": False, "L3": False, "L7": False},
    "note": ("CONT-94 artifact verdict (CONT-91 W1 law): upload/whatsapp.apk sha16 "
             "c473ad25086720a8 is 5,615 bytes — not a real WhatsApp APK. Verdict "
             "NOT_AVAILABLE: no legally usable WhatsApp artifact in the corpus; no "
             "private source access claimed. Cross-family control = Forkgram + Telegram "
             "(same-lineage) and Signal if/when an artifact is added."),
    "sessions": "S123/S124 + CONT-94",
    "evidence_refs": ["evidence/cont94/evidence.json"],
})

upsert("APP-014", {
    "id": "APP-014",
    "title": "Forkgram Classic (org.forkgram.classic 12.10.8.0 vc709208, sha16 3baeecb3288577e9)",
    "package": "org.forkgram.classic",
    "status": "PARTIAL",
    "checkpoints": {"L0": True, "L1": True, "L2": True, "L3": True, "L4": True, "L5": False, "L7": False},
    "note": ("CONT-94 F-NEW-396 fan-out control (same lineage, independent APK hash): "
             "188 px -> 15599 px after the live-identity fix. Real login widgets: 'Your "
             "Number' header, phone field, QRLoginButton, 'Disable'. Named residuals: "
             "top-anchored layout, honest '[resid:0x2131745245]' string fallback."),
    "sessions": "CONT-94",
    "evidence_refs": ["run/cont94/fk_post/screenshot.png", "evidence/cont94/evidence.json"],
})

d["generated"] = "2026-10-18T06:30:00Z"
json.dump(d, open(REG, "w"), indent=1, ensure_ascii=False)
print("app_registry updated:", len(apps), "apps")
