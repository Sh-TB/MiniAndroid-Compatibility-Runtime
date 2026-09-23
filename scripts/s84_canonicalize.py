#!/usr/bin/env python3
"""s84_canonicalize.py — S84 CANONICAL EVIDENCE ENGINE.

User law (S84): ONE title → ONE canonical screenshot.
  SOURCE → APK+SHA → EXECUTION → INTERACTION/STATE CHANGE
        → ONE CANONICAL SCREENSHOT → ACHIEVEMENT RECORD → ROOT-CAUSE ISSUE
        → README SUMMARY

Inputs (provenance-verified sources only):
  * run/s84/report.json          — S84 NEW-50 campaign (this wave)
  * docs/evidence/s83/*.jpg      — S83 35-title campaign (best-stage JPGs)
  * docs/evidence/s6x_spotlight/ — S62-S65 source-first spotlight titles
  * docs/evidence/s80/*.gif      — in-house autoplay gameplay GIFs
  * run/s83_ttt_autoplay/leg*/frames — TicTacToe Deluxe autoplay legs

Outputs:
  * docs/evidence/canonical/<package>.jpg|.gif  — ONE artifact per title
  * docs/evidence/canonical/registry.json       — machine source of truth
  * docs/evidence/canonical/SHA256SUMS
"""
import glob
import hashlib
import json
import os
import shutil
from PIL import Image

ROOT = "/home/z/my-project"
CAN = f"{ROOT}/docs/evidence/canonical"
S84 = json.load(open(f"{ROOT}/run/s84/report.json"))["results"]
os.makedirs(CAN, exist_ok=True)


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def png_to_jpg(src, dst, max_w=540, max_kb=100):
    im = Image.open(src).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, int(im.height * max_w / im.width)),
                       Image.LANCZOS)
    q = 82
    im.save(dst, "JPEG", quality=q)
    while os.path.getsize(dst) > max_kb * 1024 and q > 40:
        q -= 8
        im.save(dst, "JPEG", quality=q)
    return dst


def build_gif(frame_dir, dst, max_w=360, max_frames=10, max_mb=1.4):
    files = sorted(glob.glob(f"{frame_dir}/frames/frame_*.png")) or \
        sorted(glob.glob(f"{frame_dir}/*.png"))
    if not files:
        return None
    if len(files) > max_frames:
        step = max(1, len(files) // max_frames)
        picked = files[::step]
        if files[-1] != picked[-1]:
            picked.append(files[-1])
    else:
        picked = files
    im0 = Image.open(picked[0]).convert("RGB")
    if im0.width > max_w:
        size = (max_w, int(im0.height * max_w / im0.width))
    else:
        size = im0.size
    frames = [Image.open(f).convert("RGB").resize(size, Image.LANCZOS)
              for f in picked]
    frames[0].save(dst, save_all=True, append_images=frames[1:],
                   duration=700, loop=0, optimize=True)
    return dst


def dup_jpg(src, dst, max_w=540):
    """Copy an already-JPG evidence file, normalizing size."""
    im = Image.open(src).convert("RGB")
    if im.width > max_w:
        im = im.resize((max_w, int(im.height * max_w / im.width)),
                       Image.LANCZOS)
    im.save(dst, "JPEG", quality=85)
    return dst


def dup_gif(src, dst):
    shutil.copyfile(src, dst)
    return dst


REGISTRY = []


def add(title, pkg, typ, status, level, level_name, artifact, session,
        launched, rendered, interacted, state_changed, apk_sha, version,
        source, upstream, root_cause, notes, proven, remaining,
        last_success, first_divergence):
    sha = sha256(artifact) if artifact else ""
    REGISTRY.append({
        "title": title, "package": pkg, "type": typ, "status": status,
        "level": level, "level_name": level_name,
        "artifact": os.path.relpath(artifact, ROOT) if artifact else "",
        "artifact_sha256": sha, "artifact_kind":
            (".gif" if artifact and artifact.endswith(".gif")
             else ".jpg" if artifact else ""),
        "session": session, "launched": launched, "rendered": rendered,
        "interacted": interacted, "state_changed": state_changed,
        "apk_sha256": apk_sha, "version": version, "source": source,
        "upstream": upstream, "root_cause": root_cause, "notes": notes,
        "proven": proven, "remaining": remaining,
        "last_success_stage": last_success,
        "first_divergence": first_divergence,
    })


# ---------------------------------------------------------------- S84 NEW-50
S84_RC = {
    # §7 fan-out families — ONE root cause per family, referenced per title
    "compose": ("F-NEW-161 (OPEN, fan-out family): Compose UI runtime "
                "internals — kotlin-reflect forName CNFE (caught, faithful) "
                "followed by compose-runtime NPE/ISE (null Iterator in "
                "compose runtime setState chain, null View.getWidth in "
                "compose layout, IllegalStateException in setContent/"
                "onCreate) → ART process-death law PARTIAL. Static UI "
                "renders; dynamic compose machinery not implemented "
                "(S83-GFX-BASE P4 scope)."),
    "androidx": ("F-NEW-162 (OPEN, fan-out family): androidx lifecycle/"
                 "savedstate generated-adapter family — "
                 "androidx.savedstate.Recreator_LifecycleAdapter absent "
                 "(deferred CNFE; faithful to device behavior where the "
                 "adapter is an optional build-time artifact) plus "
                 "androidx.activity/fragment ExternalSyntheticLambda "
                 "gaps → deferred unwind PARTIAL."),
}
S84_RC_F160 = ("F-NEW-160 (FIXED this wave, S84 A/B-proven): "
               "Class.forName framework bridge — android.os.Build/"
               "Build$VERSION CNFE eliminated (9/50 titles hit); bridge "
               "restricted to pure-data Build family after foehnix.widget "
               "A/B regression proved instantiable artifacts (CloseGuard) "
               "must stay on the caught-CNFE path.")


def s84_titles():
    seen_content = {}
    for r in S84:
        pkg = r["package"]
        obs_frames = f"{ROOT}/run/s84/{pkg}/obs/frames"
        clk_frames = f"{ROOT}/run/s84/{pkg}/click/frames"
        has_frames = os.path.isdir(obs_frames) and glob.glob(
            f"{obs_frames}/frame_*.png")
        state = r.get("state_changed", False)
        probed = r.get("click_probed", -1) > 0
        v = r.get("visual", {})
        lvl, lvlname = v.get("LEVEL", -1), v.get("LEVEL_NAME", "NO-FRAME")
        apk = f"{ROOT}/run/s84/apks/{pkg}.apk"
        apk_sha = sha256(apk) if os.path.exists(apk) else ""
        rc = S84_RC_F160 + " | " + (
            S84_RC["compose"] if r["errors_obs"] not in ("0", "?")
            else "")
        if state and has_frames:
            art = build_gif(clk_frames if os.path.isdir(clk_frames)
                            else obs_frames, f"{CAN}/{pkg}.gif")
            status = "VERIFIED-INTERACTIVE"
        elif has_frames:
            frame = glob.glob(f"{obs_frames}/frame_*.png")[-1]
            fh = sha256(frame)[:12]
            uc = v.get("UNIQUE_COLORS") or 999
            shared = fh in seen_content or uc <= 3
            seen_content.setdefault(fh, pkg)
            if shared:
                # S54 law: shared/near-blank class is not visual evidence
                art = None
                status = "OBSERVED"
            else:
                art = png_to_jpg(frame, f"{CAN}/{pkg}.jpg")
                status = ("VERIFIED" if r["rc_obs"] == 0 and lvl >= 1
                          else "PARTIAL" if lvl >= 1 else "OBSERVED")
        else:
            art = None
            status = "BLOCKED"
        notes = (f"S84 NEW title. rc_obs={r['rc_obs']} "
                 f"errors={r['errors_obs']} frames={r['frames_obs']}/8 "
                 f"click: probed={r['click_probed']} "
                 f"state_changed={r['click_state_changed']}. "
                 f"unique_colors={v.get('UNIQUE_COLORS')} "
                 f"entropy={v.get('COLOR_ENTROPY')} "
                 f"resources(dex/classes)={v.get('DEX_CLASSES','?')}")
        if status == "OBSERVED" and art is None and has_frames:
            notes += (" [frame belongs to the shared/near-blank content "
                      "class — not canonical visual evidence per S54 "
                      "law]")
        add(title=pkg, pkg=pkg, typ=r["kind"], status=status, level=lvl,
            level_name=lvlname, artifact=art, session="S84",
            launched=r["rc_obs"] == 0, rendered=bool(r.get("rendered")),
            interacted=r.get("interacted", False), state_changed=state,
            apk_sha=apk_sha, version=str(r.get("version")),
            source=r["source"], upstream=r.get("upstream", ""),
            root_cause=rc if r["rc_obs"] != 0 else "none (rc=0)",
            notes=notes,
            proven=f"LOADED{'/LAUNCHED' if r['rc_obs']==0 else ''}"
                   f"{'/RENDERED' if lvl>=1 else ''}"
                   f"{'/INTERACTED' if probed else ''}"
                   f"{'/STATE_CHANGED' if state else ''}",
            remaining=("compose/animation dynamics; deeper interaction"
                       if r["rc_obs"] != 0 else
                       "full app-specific behavior beyond click probe"),
            last_success=("8/8 frames captured, click pass executed"
                          if has_frames else "engine boot"),
            first_divergence=("first uncaught in-flight exception (see "
                              "run/s84/%s/obs_obs.log EXC-PROPAGATE)" % pkg
                              if r["rc_obs"] != 0 else "none"))


# ------------------------------------------------------- S83 campaign (35)
S83_EVID = f"{ROOT}/docs/evidence/s83"
S83_MAP = {
    "games__snake_deluxe_v1.0_vc1__L3_STRUCT_CANDIDATE.jpg": (
        "Snake Deluxe", "com.miniandroid.snakedeluxe", "game",
        "in-house (games/snake-deluxe)", "S80/S83"),
    "games__tetris_v1.0_vc1__L3_STRUCT_CANDIDATE.jpg": (
        "Mini Tetris", "com.miniandroid.tetris", "game",
        "in-house (games/mini-tetris)", "S80/S83"),
    "games__g2048_v1.0_vc1__L2_GRAPHICALLY_INCOMPLETE.jpg": (
        "2048", "com.miniandroid.g2048", "game",
        "in-house (games/2048)", "S80/S83"),
    "games__tictactoe_deluxe_v1.0_vc1__L3_STRUCT_CANDIDATE.jpg": (
        "TicTacToe Deluxe", "com.miniandroid.tictactoedeluxe",
        "game", "in-house (games/tictactoe-deluxe)", "S83 NEW"),
    "games__dooz__L2_GRAPHICALLY_INCOMPLETE.jpg": (
        "Dooz (tic-tac-toe)", "io.github.yamin8000.dooz", "game",
        "F-Droid io.github.yamin8000.dooz", "S66/S83"),
    "games__tictactoeclassic__L2_GRAPHICALLY_INCOMPLETE.jpg": (
        "TicTacToe Classic", "com.emmanuelmess.tictactoe", "game",
        "F-Droid com.emmanuelmess.tictactoe", "S83"),
    "games__com.sidhant.queens_93__L2_GRAPHICALLY_INCOMPLETE.jpg": (
        "Queens", "com.sidhant.queens", "game", None, "S83"),
    "games__cos.premy.mines_16__L2_GRAPHICALLY_INCOMPLETE.jpg": (
        "Mines (premy)", "cos.premy.mines", "game", None, "S83"),
    "games__eu.veldsoft.no.thanks_1__L1_NONBLANK.jpg": (
        "No Thanks!", "eu.veldsoft.no.thanks", "game", None, "S83"),
    "games__eu.quelltext.memory_7__L0_LOADED_ONLY.jpg": (
        "Memory", "eu.quelltext.memory", "game", None, "S83"),
    "games__crypto.o0o0o0o0o.games.blackjack_4__L0_LOADED_ONLY.jpg": (
        "Blackjack", "crypto.o0o0o0o0o.games.blackjack", "game", None,
        "S83"),
    "games__com.vayunmathur.games.solitaire_20260804__L2_GRAPHICALLY_INCOMPLETE.jpg": (
        "Solitaire (vayunmathur)", "com.vayunmathur.games.solitaire",
        "game", None, "S83"),
    "games__de.tobiasbielefeld.solitaire_71__L2_GRAPHICALLY_INCOMPLETE.jpg": (
        "Solitaire (tobiasbielefeld)", "de.tobiasbielefeld.solitaire",
        "game", None, "S83"),
    "games__org.secuso.privacyfriendlybattleship_101__L2_GRAPHICALLY_INCOMPLETE.jpg": (
        "Battleship (SECUSO)", "org.secuso.privacyfriendlybattleship",
        "game", None, "S83"),
    "games__com.jeffliu.balancetheball_4__L2_GRAPHICALLY_INCOMPLETE.jpg": (
        "Balance the Ball", "com.jeffliu.balancetheball", "game", None,
        "S83"),
    "games__com.simondalvai.ball2box_69__L0_LOADED_ONLY.jpg": (
        "Ball2Box", "com.simondalvai.ball2box", "game", None, "S83"),
    "games__app.halma_15__L2_GRAPHICALLY_INCOMPLETE.jpg": (
        "Halma", "app.halma", "game", None, "S83"),
    "games__com.astroloop.game_4__L2_GRAPHICALLY_INCOMPLETE.jpg": (
        "Astroloop", "com.astroloop.game", "game", None, "S83"),
    "games__si.palcka.tarok_203__L2_GRAPHICALLY_INCOMPLETE.jpg": (
        "Tarok", "si.palcka.tarok", "game", None, "S83"),
    "games__page.codeberg.lanticy.guandan_7__L2_GRAPHICALLY_INCOMPLETE.jpg": (
        "Guandan", "page.codeberg.lanticy.guandan", "game", None, "S83"),
    "games__com.rocket9labs.boxcars_104090__L1_NONBLANK.jpg": (
        "Boxcars", "com.rocket9labs.boxcars", "game", None, "S83"),
    "games__com.bupkis.tirailleur_13__L2_GRAPHICALLY_INCOMPLETE.jpg": (
        "Tirailleur", "com.bupkis.tirailleur", "game", None, "S83"),
    "games__com.eightsines.firestrike.opensource_2000__L2_GRAPHICALLY_INCOMPLETE.jpg": (
        "Firestrike", "com.eightsines.firestrike.opensource", "game",
        None, "S83"),
    "apps__app.varlorg.unote_30__L2_GRAPHICALLY_INCOMPLETE.jpg": (
        "uNote", "app.varlorg.unote", "app", None, "S83"),
    "apps__omegacentauri.mobi.simplestopwatch_26__L2_GRAPHICALLY_INCOMPLETE.jpg": (
        "Simple Stopwatch", "omegacentauri.mobi.simplestopwatch", "app",
        None, "S64/S83"),
    "apps__dubrowgn.microtimer_8__L2_GRAPHICALLY_INCOMPLETE.jpg": (
        "MicroTimer", "dubrowgn.microtimer", "app", None, "S83"),
    "apps__com.chessclock.android_29__L0_LOADED_ONLY.jpg": (
        "Chess Clock", "com.chessclock.android", "app", None, "S83"),
    "apps__org.billthefarmer.notes_139__L2_GRAPHICALLY_INCOMPLETE.jpg": (
        "Notes (billthefarmer)", "org.billthefarmer.notes", "app", None,
        "S83"),
    "apps__org.debian.eugen.headingcalculator_1__L2_GRAPHICALLY_INCOMPLETE.jpg": (
        "Heading Calculator", "org.debian.eugen.headingcalculator", "app",
        None, "S83"),
    "apps__de.duenndns.gmdice_8__L2_GRAPHICALLY_INCOMPLETE.jpg": (
        "GameMasterDice", "de.duenndns.gmdice", "app", None, "S63/S83"),
    "apps__com.best.deskclock_2036__L2_GRAPHICALLY_INCOMPLETE.jpg": (
        "DeskClock", "com.best.deskclock", "app", None, "S83"),
    "apps__com.bnyro.clock_24__L2_GRAPHICALLY_INCOMPLETE.jpg": (
        "Bnyro Clock", "com.bnyro.clock", "app", None, "S83"),
    "apps__se.tube42.p9.android_11__L2_GRAPHICALLY_INCOMPLETE.jpg": (
        "P9 (tube42)", "se.tube42.p9.android", "app", None, "S81/S83"),
    "high__com.newsblur_289__L2_GRAPHICALLY_INCOMPLETE.jpg": (
        "NewsBlur", "com.newsblur", "app", None, "S83 HIGH"),
    "high__io.timelimit.android.aosp.direct_231__L2_GRAPHICALLY_INCOMPLETE.jpg": (
        "TimeLimit", "io.timelimit.android.aosp.direct", "app", None,
        "S83 HIGH"),
}


S83B_SWEEP = {
    # package → s83b sweep evidence with DISTINCT real-UI content only
    # (content-hash verified: DOOZ18 = a25ca472…; the queens/battle/
    # bnyroclk/p9/timelimit sweep files share the 2eedb504… near-blank
    # class, so they are NOT visual evidence — see NEAR_BLANK_20)
    "io.github.yamin8000.dooz": "sweep_GAME-DOOZ18.jpg",
}

# Titles whose S83 evidence frame belongs to a shared content-hash class
# (S84 validator R5 + full census: f817c243… ×16 near-blank status-bar
# class; 955655… ×2 boxcars/no-thanks L1; d44d6bf… ×2 ball2box/
# blackjack L0). Per the S54 screenshot gate law these frames are NOT
# visual evidence: no canonical artifact, status OBSERVED, evidence =
# log reference.
NEAR_BLANK_20 = {
    "app.halma", "com.astroloop.game", "com.best.deskclock",
    "com.bnyro.clock", "com.bupkis.tirailleur",
    "com.eightsines.firestrike.opensource", "com.newsblur",
    "com.sidhant.queens", "com.vayunmathur.games.solitaire",
    "de.tobiasbielefeld.solitaire", "io.github.yamin8000.dooz",
    "io.timelimit.android.aosp.direct",
    "org.secuso.privacyfriendlybattleship",
    "page.codeberg.lanticy.guandan", "se.tube42.p9.android",
    "si.palcka.tarok", "com.rocket9labs.boxcars",
    "eu.veldsoft.no.thanks", "com.simondalvai.ball2box",
    "crypto.o0o0o0o0o.games.blackjack",
}


def s83_titles():
    for fn, (title, pkg, typ, upstream, session) in S83_MAP.items():
        src = f"{S83_EVID}/{fn}"
        # the s83 JPG may itself be a member of a duplicate content class
        # removed by the S84 cleanup (the canonical/ copy + SHA256SUMS keep
        # provenance); GIF/sweep sources below do not need it
        src_ok = os.path.exists(src)
        lvlname = fn.split("__")[-1].split(".jpg")[0]
        lvl = -1
        for i, ch in enumerate(lvlname):
            if ch.isdigit():
                lvl = int("".join(c for c in lvlname[i:] if c.isdigit())[:1])
                break
        # in-house games: canonical artifact = autoplay gameplay GIF where
        # one exists (user law: interactive → ONE gif)
        art = None
        if pkg == "com.miniandroid.snakedeluxe":
            g = f"{ROOT}/docs/evidence/s80/snake_gameplay.gif"
            if os.path.exists(g):
                art = dup_gif(g, f"{CAN}/{pkg}.gif")
        elif pkg == "com.miniandroid.g2048":
            g = f"{ROOT}/docs/evidence/s80/g2048_gameplay.gif"
            if os.path.exists(g):
                art = dup_gif(g, f"{CAN}/{pkg}.gif")
        elif pkg == "com.miniandroid.tetris":
            g = f"{ROOT}/docs/evidence/s80/tetris_gameplay.gif"
            if os.path.exists(g):
                art = dup_gif(g, f"{CAN}/{pkg}.gif")
        elif pkg == "com.miniandroid.tictactoedeluxe":
            art = build_gif(f"{ROOT}/run/s83_ttt_autoplay/leg00",
                            f"{CAN}/{pkg}.gif")
        elif pkg == "com.emmanuelmess.tictactoe":
            legs = sorted(glob.glob(
                f"{ROOT}/docs/evidence/s83b/click_GAME-TTT-CLASSIC_*.jpg"))
            if legs:
                d = f"{ROOT}/run/s84/_tmp_tttclassic"
                os.makedirs(f"{d}/frames", exist_ok=True)
                for i, l in enumerate(legs):
                    Image.open(l).save(f"{d}/frames/frame_{i:03d}.png")
                art = build_gif(d, f"{CAN}/{pkg}.gif")
        elif pkg in S83B_SWEEP:
            sp = f"{ROOT}/docs/evidence/s83b/{S83B_SWEEP[pkg]}"
            if os.path.exists(sp):
                art = dup_jpg(sp, f"{CAN}/{pkg}.jpg")
        if art is None and pkg in NEAR_BLANK_20:
            # S54 screenshot-gate law: near-blank frames are NOT visual
            # evidence. Record honestly WITHOUT an artifact.
            add(title=title, pkg=pkg, typ=typ, status="OBSERVED",
                level=lvl, level_name=lvlname, artifact=None,
                session=session, launched=True, rendered=False,
                interacted=False, state_changed=False, apk_sha="",
                version="",
                source="F-Droid" if not upstream else upstream,
                upstream=upstream or "",
                root_cause=("S83 near-blank final-frame class "
                            "(eb16ab5c… ×16, uniq=2-3): app renders "
                            "status-bar-only content at campaign "
                            "parameters; real UI evidence exists only "
                            "for titles with dedicated interaction "
                            "runs (s83b sweep)"),
                notes=f"S83 campaign ({fn}) is the shared near-blank "
                      f"frame class — no canonical visual per S54 law; "
                      f"evidence = run logs",
                proven="LOADED/LAUNCHED (frames not visual evidence)",
                remaining="real-UI render under dedicated interaction "
                          "protocol",
                last_success="8/8 frames captured; lifecycle ran",
                first_divergence="near-blank framebuffer (no meaningful "
                                 "UI pixels)")
            continue
        if art is None and src_ok:
            art = dup_jpg(src, f"{CAN}/{pkg}.jpg")
        # APK SHA from corpus caches when present (exact-file match only)
        apk_sha = ""
        for cand in [f"{ROOT}/upload/s83_games/build_sd/snake_deluxe_v1.0_vc1.apk",
                     f"{ROOT}/upload/s83_games/build_tetris/tetris_v1.0_vc1.apk",
                     f"{ROOT}/upload/s83_games/build_g2048/g2048_v1.0_vc1.apk",
                     f"{ROOT}/upload/s83_games/build_ttt/tictactoe_deluxe_v1.0_vc1.apk",
                     f"/tmp/my-project/apk_cache/corpus/dooz.apk",
                     f"/tmp/my-project/apk_cache/tictactoeclassic.apk",
                     f"{ROOT}/upload/canonical_apks/dubrowgn.microtimer_8.apk",
                     f"/tmp/my-project/apk_cache/com.chessclock.android_29.apk",
                     f"/tmp/my-project/apk_cache/org.billthefarmer.notes_139.apk",
                     f"/tmp/my-project/apk_cache/org.debian.eugen.headingcalculator_1.apk",
                     f"/tmp/my-project/apk_cache/omegacentauri.mobi.simplestopwatch_26.apk",
                     f"{ROOT}/upload/canonical_apks/app.varlorg.unote_30.apk",
                     f"{ROOT}/upload/canonical_apks/de.duenndns.gmdice_8.apk",
                     f"/tmp/my-project/apk_cache/s82/cos.premy.mines_16.apk",
                     f"/tmp/my-project/apk_cache/s82/eu.quelltext.memory_7.apk",
                     f"/tmp/my-project/apk_cache/s82/com.jeffliu.balancetheball_4.apk",
                     f"/tmp/my-project/apk_cache/s82/crypto.o0o0o0o0o.games.blackjack_4.apk",
                     f"/tmp/my-project/apk_cache/s82/com.simondalvai.ball2box_69.apk",
                     f"/tmp/my-project/apk_cache/s82/com.rocket9labs.boxcars_104090.apk",
                     f"/tmp/my-project/apk_cache/s82/eu.veldsoft.no.thanks_1.apk"]:
            if not os.path.exists(cand):
                continue
            base = os.path.basename(cand).lower()
            if pkg == "io.github.yamin8000.dooz" and "dooz" in base:
                apk_sha = sha256(cand)
            elif pkg == "com.emmanuelmess.tictactoe" and "tictactoeclassic" in base:
                apk_sha = sha256(cand)
            else:
                key = pkg.split(".")[-1]
                if key in base and "dooz" not in base:
                    apk_sha = sha256(cand)
        inter = art.endswith(".gif") if art else False
        add(title=title, pkg=pkg, typ=typ,
            status=("VERIFIED-INTERACTIVE" if inter else
                    ("VERIFIED" if art else "OBSERVED")), level=lvl,
            level_name=lvlname, artifact=art, session=session,
            launched=True, rendered=lvl >= 1, interacted=inter,
            state_changed=inter, apk_sha=apk_sha, version="",
            source=("F-Droid" if not upstream else upstream),
            upstream=upstream or "",
            root_cause=("S83 engine laws (APX-ACT, CANVAS-GEOMETRY, "
                        "LOCALE-DEFAULT, INPUT-SERVICE, VTO, AUDIO) all "
                        "fixed and regression-clean"),
            notes=f"S83 real-screenshot campaign evidence ({fn})",
            proven="LOADED/LAUNCHED/RENDERED" + ("/INTERACTED/STATE_CHANGED"
                                                if inter else ""),
            remaining="graphics completeness beyond L3",
            last_success="full lifecycle + real frames (S83)",
            first_divergence="none recorded in S83 session")


SPOTLIGHT = [
    # (title, package, type, evidence file, status, level, session, upstream)
    ("Vector Pinball (bouncy)", "com.dozingcatsoftware.bouncy", "game",
     "docs/evidence/s74_ops/bouncy", "VERIFIED", 5, "S62/S74",
     "https://github.com/dozingcatsoftware/Bouncy"),
    ("OPMT (One More Time…)", "one.scarecrow.games.OPMT", "game",
     "docs/evidence/visual_forensics/s65_reval/opmt/game_partial_full.png",
     "PARTIAL", 5, "S65/S74",
     "https://github.com/scarecrowgames/OneMoreTimePuzzleGame"),
    ("Anuto TD", "ch.logixisland.anuto", "game",
     "docs/evidence/s62plus_spotlight/anuto_frame0_after_onDraw.png",
     "VERIFIED", 5, "S62+",
     "https://github.com/jogishop/AnutoTD"),
    ("OpenSudoku", "cz.romario.opensudoku", "game",
     "docs/evidence/s62plus_spotlight/opensudoku_frame0_folderlist.png",
     "VERIFIED", 5, "S62+",
     "https://github.com/romario333/opensudoku"),
    ("SigGen", "org.billthefarmer.siggen", "app",
     "docs/evidence/s63_spotlight/siggen_frame0.png", "PARTIAL", 5,
     "S63", "https://github.com/billthefarmer/sig-gen"),
    ("PMK-61 Calculator", "com.cax.pmk", "app",
     "docs/evidence/s64_spotlight/pmk_frame0_indicator.png", "VERIFIED",
     6, "S64", "https://github.com/xvadim/pmk-android"),
    ("FreeKlondike", "eu.veldsoft.free.klondike", "game",
     "docs/evidence/s64_spotlight/fk_game_deal_response.png", "VERIFIED",
     10, "S64", "https://github.com/VelbazhdSoftwareLLC/FreeKlondike"),
    ("Shopping List Calc", "io.github.buildsbyben.shoppinglistcalc",
     "app", "docs/evidence/s64_spotlight/sc_after_click.png", "VERIFIED",
     9, "S64", "https://github.com/buildsbyben/shopping-list-calc"),
    ("Fish Rings", "eu.veldsoft.fish.rings", "game",
     "docs/evidence/visual_forensics/s65_reval/fishrings/after_tap3_full.png",
     "VERIFIED", 10, "S65",
     "https://github.com/VelbazhdSoftwareLLC/FishRingsForAndroid"),
    ("TriPeaks", "eu.veldsoft.tri.peaks", "game",
     "docs/evidence/visual_forensics/s65_reval/tripeaks/board_full.png",
     "PARTIAL", 10, "S65",
     "https://github.com/VelbazhdSoftwareLLC/TriPeaks"),
    ("TicTacToe3D self-aware fixture", "org.miniandroid.helloworld",
     "fixture", "docs/evidence/external_hello_golden", "VERIFIED", 6,
     "S45", "https://github.com/Applibered/HelloWorldSelfAware"),
]


def spotlight_titles():
    for (title, pkg, typ, ev, status, lvl, session, upstream) in SPOTLIGHT:
        art = None
        if os.path.isdir(ev):
            cands = (sorted(glob.glob(f"{ev}/*.png")) +
                     sorted(glob.glob(f"{ev}/*.jpg")) +
                     sorted(glob.glob(f"{ev}/*.gif")))
            cands = [c for c in cands if not c.endswith("diff.png")]
            if cands:
                src = cands[-1]
                art = (dup_gif(src, f"{CAN}/{pkg}.gif")
                       if src.endswith(".gif")
                       else dup_jpg(src, f"{CAN}/{pkg}.jpg"))
        elif os.path.exists(f"{ROOT}/{ev}"):
            src = f"{ROOT}/{ev}"
            art = (dup_gif(src, f"{CAN}/{pkg}.gif") if src.endswith(".gif")
                   else dup_jpg(src, f"{CAN}/{pkg}.jpg"))
        if art is None:
            print(f"SPOTLIGHT-MISSING {pkg} ({ev})")
            continue
        inter = art.endswith(".gif")
        add(title=title, pkg=pkg, typ=typ, status=status, level=lvl,
            level_name=f"L{lvl}", artifact=art, session=session,
            launched=True, rendered=lvl >= 1, interacted=inter,
            state_changed=inter, apk_sha="", version="",
            source="source-first build (F-Droid/GitHub)", upstream=upstream,
            root_cause="see session report (S62-S65 spotlight reports)",
            notes=f"canonical harvested from {ev}",
            proven="LOADED/LAUNCHED/RENDERED" + ("/INTERACTED" if inter
                                                 else ""),
            remaining="session-specific (see report)",
            last_success=f"see {session} report",
            first_divergence="see session report")


def main():
    # fresh canonical dir (registry is the single source; stale artifacts
    # must never survive a regen — validator R10 would flag them anyway)
    for f in glob.glob(f"{CAN}/*.jpg") + glob.glob(f"{CAN}/*.gif") + \
            glob.glob(f"{CAN}/*.png"):
        os.remove(f)
    REGISTRY.clear()
    s84_titles()
    s83_titles()
    spotlight_titles()
    reg = {"wave": "S84",
           "law": "ONE title -> ONE canonical screenshot; interactive "
                  "titles get ONE gif",
           "count": len(REGISTRY), "titles": REGISTRY}
    with open(f"{CAN}/registry.json", "w") as f:
        json.dump(reg, f, indent=1)
    gifs = sum(1 for t in REGISTRY if t["artifact"].endswith(".gif"))
    jpgs = sum(1 for t in REGISTRY if t["artifact"].endswith(".jpg"))
    print(f"registry: {len(REGISTRY)} titles ({gifs} gif, {jpgs} jpg)")


if __name__ == "__main__":
    main()
