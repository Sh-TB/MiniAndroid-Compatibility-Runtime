#!/usr/bin/env python3
"""T279 P5 — reconcile the canonical registry with the T279 findings.

- Adds the 27 registry-absent achievements (15 S182 battery titles + 12
  S23-S27 easy-APK wave titles) as canonical rows in the EXISTING schema,
  status in the T279 8-label vocabulary (HISTORICAL-REAL / CURRENT-
  REPRODUCIBLE / INTERACTIVE / PARTIAL / REGRESSED / BLOCKED / PENDING /
  NOISE).
- Enriches the rows already in the registry with t279_* current-status
  fields WITHOUT touching their historical status (no erasure).
- count 152 -> 179; wave/generated updated.
"""
import hashlib
import json
from pathlib import Path

BASE = Path("/home/z/my-project")
REG = BASE / "docs/evidence/canonical/registry.json"
BIN_SHA16 = "1a21be9fc9f6b016"
ENGINE_COMMIT = "344774e66 (f9e1d3314 for uturn)"


def sha256(p):
    h = hashlib.sha256(Path(p).read_bytes())
    return h.hexdigest()


def row(pkg, title, type_, status, level, level_name, rendered, interacted,
        state_changed, apk, apk_sha, artifact, notes, first_divergence,
        proven, remaining, root_cause, session):
    return {
        "apk_sha256": apk_sha or "",
        "artifact": artifact,
        "artifact_kind": "screenshot" if artifact else "",
        "artifact_sha256": "",
        "first_divergence": first_divergence,
        "interacted": interacted,
        "last_success_stage": session,
        "launched": True,
        "level": level,
        "level_name": level_name,
        "notes": notes,
        "package": pkg,
        "proven": proven,
        "remaining": remaining,
        "rendered": rendered,
        "root_cause": root_cause,
        "session": session,
        "source": "",
        "state_changed": state_changed,
        "status": status,
        "title": title,
        "type": type_,
        "upstream": "",
        "version": "",
    }


T279 = ("T279 2026-11-28 two-run campaign (46/46 face-identical pairs; binary "
        f"9c5e456b pre-fix, {BIN_SHA16} post-fix; engine {ENGINE_COMMIT})")

NEW = [
    # ---- S182 REAL_APP_CONTENT (6 registry-absent) ----
    row("org.secuso.privacyfriendlydicer", "PF Dicer", "game",
        "CURRENT-REPRODUCIBLE", 3, "R3_PRIMARY_SCREEN_COMPLETE", True, False,
        False, "upload/fdroid_batch/org.secuso.privacyfriendlydicer_101.apk",
        "f2b4d3f021c3a6207c3c9e75a75fa325b88847bd46b4f99e41e28dc3be8fae7f",
        "evidence/t279/shots/pfdicer_r1.png",
        f"S182 2026-11-06 REAL face 31ffa499c59e3e41 BYTE-IDENTICAL on T279 "
        f"current build (r1==r2==ct1==ct2); {T279}; unc 12 nonfatal "
        f"(SavedStateHandleAttacher IAE, nonfatal); 0 clickable views at ct "
        f"census — interaction not yet proven by frame change",
        "none recorded", "LOADED/LAUNCHED/RENDERED",
        "clickable-view census 0 at dispatch time", "no prior root cause",
        "S182+T279"),
    row("com.maxistar.textpad", "TextPad", "app",
        "CURRENT-REPRODUCIBLE", 3, "R3_PRIMARY_SCREEN_COMPLETE", True, False,
        False, "upload/fdroid_batch/com.maxistar.textpad_63.apk",
        "322ba8b62ed791db8e2ad7b459ad4bc952992c933d30a61eb190256152d7fb2e",
        "evidence/t279/shots/textpad_r1.png",
        f"S182 2026-11-06 REAL face 27f44f4647bf76f2 BYTE-IDENTICAL on T279 "
        f"current build; {T279}; 0 clickable views at ct census",
        "none recorded", "LOADED/LAUNCHED/RENDERED",
        "clickable-view census 0 at dispatch time", "no prior root cause",
        "S182+T279"),
    row("com.ashkanrafiee.librecontactsbackup", "Libre Contacts Backup", "app",
        "INTERACTIVE", 3, "R3_PRIMARY_SCREEN_COMPLETE", True, True, True,
        "upload/fdroid_batch/com.ashkanrafiee.librecontactsbackup_32.apk",
        "1ae81c24dcaf2ec59908ba024dae1c11082069ed06ee396431cb5dba36968309",
        "evidence/t279/shots/librecontactsbackup_ct1.png",
        f"S182 2026-11-06 REAL (px 1,214,501); 2026-11-27 recheck px 720,117 "
        f"(drift, unc 4); T279 r1==r2 face 79bb8fa317311c9a px 720,117 + "
        f"CLICK-TEST state change ct face b0df57086f5178d0 px 902,277 "
        f"(ct1==ct2) = INTERACTIVE; face drift 1.21M->0.72M recorded as "
        f"open reconciliation item; {T279}",
        "content-set drift vs 2026-11-06 (px 1,214,501 -> 720,117)",
        "LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED",
        "face drift adjudication pending", "no prior root cause",
        "S182+T279"),
    row("ac.stresa.uturn", "UTurn", "game",
        "CURRENT-REPRODUCIBLE", 3, "R3_PRIMARY_SCREEN_COMPLETE", True, False,
        False, "upload/fdroid_batch/ac.stresa.uturn_22.apk",
        "dc8e08d4db9cc0c2b9d5e9c81c6345680f9e35151531d9b26dc96eb8b852806f",
        "evidence/t279/shots/uturn_f1.png",
        f"S182 2026-11-06 REAL face a53523e7ca331866; regressed to "
        f"DEFAULT_BACKGROUND_ONLY by 2026-11-27 (recheck, unc 8); T279 ROOT "
        f"CAUSE = engine MeasureSpec.getMode returned a 0/1/2 INDEX instead "
        f"of the AOSP bit pattern; compose convertMeasureSpec threw ISE at "
        f"dex pc=0x48 every measure pass. FIXED (commit f9e1d3314, F-NEW-714 "
        f"AOSP law): REAL_APP_CONTENT restored, face a53523e7ca331866 "
        f"== S182 historical face BYTE-IDENTICAL, px 10,782, unc 8->0, "
        f"f1==f2 on binary {BIN_SHA16}; law test f714 9/9 incl T7 compose "
        f"fence; 8 spot law batteries rc=0; 6 golden anchors byte-identical "
        f"pre/post (zero regressions)",
        "none — fixed", "LOADED/LAUNCHED/RENDERED",
        "interaction not yet re-tested post-fix",
        "MeasureSpec.getMode index-vs-pattern convention (FIXED)",
        "T279"),
    row("app.wocheneinkauf", "Wocheneinkauf", "app",
        "REGRESSED", 1, "R1_NO_VALID_VISUAL", True, False, False,
        "upload/fdroid_batch/app.wocheneinkauf_199.apk",
        "02c08e2a3a1e585faed41d713d7104fd7c306dfd3c1cfe69d3ed975ed6e46276",
        "",
        f"S182 2026-11-06 REAL face eee8d351d081b2c7 px 44,227; regressed by "
        f"2026-11-27 recheck (DEFAULT_BACKGROUND_ONLY unc 33); T279: the "
        f"convertMeasureSpec ISE layer is ELIMINATED by the MeasureSpec fix "
        f"(uncaught 33->32) but the deeper compose composition-state layer "
        f"remains (DEFAULT_BACKGROUND_ONLY px 0, face e75e653c66fe8290 = "
        f"default tint drift, f1==f2); historical achievement stands",
        "compose composition-state layer below convertMeasureSpec "
        "(uncaught 32)",
        "LOADED/LAUNCHED (no visual)", "next compose composition-state layer",
        "compose measure lambda chain ISE (post-MeasureSpec residue)",
        "S182+T279"),
    row("app.simple.peri", "Peri", "app",
        "REGRESSED", 1, "R1_NO_VALID_VISUAL", True, False, False,
        "upload/fdroid_batch/app.simple.peri_983.apk",
        "78e04d5811464f2b9d8276820b00e82b29571361c07671721c78e09f1a41ebc2",
        "",
        f"S182 2026-11-06 REAL face 8fc63a05e0d7b777 px 325,303 (61.3s); "
        f"regressed by 2026-11-27 recheck (unc 33); T279: convertMeasureSpec "
        f"ISE eliminated by the MeasureSpec fix (uncaught 33->32); deeper "
        f"compose composition-state layer remains (DEFAULT_BACKGROUND_ONLY, "
        f"f1==f2); historical achievement stands",
        "compose composition-state layer below convertMeasureSpec "
        "(uncaught 32)",
        "LOADED/LAUNCHED (no visual)", "next compose composition-state layer",
        "compose measure lambda chain ISE (post-MeasureSpec residue)",
        "S182+T279"),
    # ---- S182 PARTIAL (9 registry-absent; 8 APKs absent from disk) ----
    row("com.aeropayout.game", "AeroPayout", "game", "PARTIAL", 2,
        "R2_FIRST_FRAME", True, False, False,
        "upload/fdroid_batch/com.aeropayout.game_12.apk (ABSENT from disk at "
        "T279; F-Droid restorable per s182_restore_apks.sh)", "",
        "", "S182 2026-11-06 PARTIAL class; APK not on disk at T279 — "
        "re-test PENDING; historical evidence stands",
        "not re-measured at T279", "LOADED/LAUNCHED (S182)",
        "APK restore + re-test", "no prior root cause", "S182"),
    row("com.awagam.android", "Awagam", "game", "PARTIAL", 2,
        "R2_FIRST_FRAME", True, False, False,
        "upload/fdroid_batch/com.awagam.android_5.apk (ABSENT from disk at "
        "T279)", "", "",
        "S182 2026-11-06 PARTIAL class; APK not on disk at T279 — re-test "
        "PENDING; historical evidence stands",
        "not re-measured at T279", "LOADED/LAUNCHED (S182)",
        "APK restore + re-test", "no prior root cause", "S182"),
    row("org.secuso.privacyfriendlyludo", "PF Ludo", "game", "PARTIAL", 2,
        "R2_FIRST_FRAME", True, False, False,
        "upload/fdroid_batch/org.secuso.privacyfriendlyludo_100.apk "
        "(ABSENT from disk at T279)", "", "",
        "S182 2026-11-06 PARTIAL class; APK not on disk at T279 — re-test "
        "PENDING; historical evidence stands",
        "not re-measured at T279", "LOADED/LAUNCHED (S182)",
        "APK restore + re-test", "no prior root cause", "S182"),
    row("com.curryplayer.quicksettingssoundprofile",
        "QuickSettings Sound Profile", "app", "PARTIAL", 2,
        "R2_FIRST_FRAME", True, False, False,
        "upload/fdroid_batch/com.curryplayer.quicksettingssoundprofile_11.apk"
        " (ABSENT from disk at T279)", "", "",
        "S182 2026-11-06 PARTIAL class; APK not on disk at T279 — re-test "
        "PENDING; historical evidence stands",
        "not re-measured at T279", "LOADED/LAUNCHED (S182)",
        "APK restore + re-test", "no prior root cause", "S182"),
    row("com.cg.lrceditor", "LRC Editor", "app", "PARTIAL", 2,
        "R2_FIRST_FRAME", True, False, False,
        "upload/fdroid_batch/com.cg.lrceditor_57.apk (ABSENT from disk at "
        "T279)", "", "",
        "S182 2026-11-06 PARTIAL class; APK not on disk at T279 — re-test "
        "PENDING; historical evidence stands",
        "not re-measured at T279", "LOADED/LAUNCHED (S182)",
        "APK restore + re-test", "no prior root cause", "S182"),
    row("app.floatdeck", "FloatDeck", "app", "PARTIAL", 2,
        "R2_FIRST_FRAME", True, False, False,
        "upload/fdroid_batch/app.floatdeck_8.apk (ABSENT from disk at T279)",
        "", "", "S182 2026-11-06 PARTIAL class; APK not on disk at T279 — "
        "re-test PENDING; historical evidence stands",
        "not re-measured at T279", "LOADED/LAUNCHED (S182)",
        "APK restore + re-test", "no prior root cause", "S182"),
    row("com.chiranth7.webstack", "WebStack", "app", "PARTIAL", 2,
        "R2_FIRST_FRAME", True, False, False,
        "upload/fdroid_batch/com.chiranth7.webstack_6.apk (ABSENT from disk "
        "at T279)", "", "",
        "S182 2026-11-06 PARTIAL class; APK not on disk at T279 — re-test "
        "PENDING; historical evidence stands",
        "not re-measured at T279", "LOADED/LAUNCHED (S182)",
        "APK restore + re-test", "no prior root cause", "S182"),
    row("org.dmfs.tasks", "dmfs Tasks", "app", "PARTIAL", 2,
        "R2_FIRST_FRAME", True, False, False,
        "upload/fdroid_batch/org.dmfs.tasks_82200.apk (ABSENT from disk at "
        "T279)", "", "",
        "S182 2026-11-06 PARTIAL class; APK not on disk at T279 — re-test "
        "PENDING; historical evidence stands",
        "not re-measured at T279", "LOADED/LAUNCHED (S182)",
        "APK restore + re-test", "no prior root cause", "S182"),
    row("stack.tower3d", "Stack Tower 3D", "game", "PARTIAL", 1,
        "R1_NO_VALID_VISUAL", True, False, False,
        "upload/canonical_apks/stack.tower3d_1.apk",
        "ba5b0a48d74e33483d9dcb04" ,  # sha16-prefix; full sha on disk
        "evidence/t279/shots/stacktower3d_r1.png",
        f"S182 2026-11-06 PARTIAL; T279 two-run DEFAULT_BACKGROUND_ONLY px 0 "
        f"unc 0, face b5a7a35d5fe0564b r1==r2==ct1==ct2; {T279}",
        "DEFAULT_BACKGROUND_ONLY (game content never drawn)",
        "LOADED/LAUNCHED (no visual)", "game viewtree attach path",
        "no app pixels at frame census", "T279"),
    # ---- S23-S27 wave (12 registry-absent) ----
    row("name.livitski.games.puzzle.android", "n-Puzzle", "game",
        "INTERACTIVE", 3, "R3_PRIMARY_SCREEN_COMPLETE", True, True, True,
        "upload/handoff_apks/name.livitski.games.puzzle.android_2.apk",
        "99b9221d44677f65e6326bda6161a046c96206bc6939bc87ceed89fc267a6aac",
        "evidence/t279/shots/npuzzle_r1.png",
        "S23 2026-11-21: CLICK_HANDLER_EXECUTED x12/run, 2 frame hashes "
        "(STATE_CHANGED) x3 independent runs; S27 wall faces 35c4e53b,6375a3a3 "
        "last-frame IDENTICAL; T279 r1==r2 face 6375a3a3813af176 px 10,282 "
        "(== S23 post-click hash) + EXP060 listener registered (view_id=22) "
        "but ct frame unchanged (dispatch census timing) — interaction "
        "status rests on the S23 x3 evidence; F-NEW-714 MeasureSpec.getSize "
        "law originated HERE (W12 n-Puzzle resize collapse)",
        "ct dispatch census vs listener registration timing",
        "LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED (S23 x3)",
        "ct-frame-change re-verification with post-registration dispatch",
        "no prior root cause", "S23+T279"),
    row("ru.zxalexis.ugaday", "Hangman (Ugaday)", "game",
        "INTERACTIVE", 3, "R3_PRIMARY_SCREEN_COMPLETE", True, True, True,
        "upload/handoff_apks/ru.zxalexis.ugaday_15.apk",
        "000ae2e5751f9a85c331d6205881d3db5dc81a00d10522485d9026b0494f8c3d",
        "evidence/t279/shots/ugaday_r1.png",
        "S23 2026-11-21: XML onClick dispatched on activity (U0113-XMLCLICK), "
        "2 hashes STATE_CHANGED x3 runs; T279 r1==r2 face 87fe26766fc48d06 "
        "(== S27 wall) + CLICK-TEST state change ct face 204f8970cb238b5d "
        "(ct1==ct2) = INTERACTIVE on the current build",
        "none recorded", "LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED",
        "none recorded", "no prior root cause", "S23+T279"),
    row("org.blockinger.game", "Minesweeper (Blockinger)", "game",
        "INTERACTIVE", 3, "R3_PRIMARY_SCREEN_COMPLETE", True, True, True,
        "upload/handoff_apks/org.blockinger.game_14.apk",
        "0c51e2255401eeb16ada6ea4eaa8aec1c2b715a789b12a004355a3812fe1c111",
        "evidence/t279/shots/blockinger_ct1.png",
        "S23 2026-11-21: 6 click events, 2 hashes STATE_CHANGED x3 runs; "
        "T279 r1==r2 face 34d7ac0cf77898d8 px 121,920 + CLICK-TEST state "
        "change ct face 52875ecb030ab8b8 px 628,272 (ct1==ct2) — Highscores "
        "DIALOG rendered over the main menu (dialog path proven); DEFECT "
        "recorded: dialog button labels render reversed/mirrored",
        "dialog button-label glyphs render reversed (visual defect, recorded)",
        "LOADED/LAUNCHED/RENDERED/INTERACTED/STATE_CHANGED/DIALOG_RENDERED",
        "reversed dialog button-label glyphs", "no prior root cause",
        "S23+T279"),
    row("com.farmerbb.notepad", "Notepad (farmerbb)", "app",
        "PARTIAL", 1, "R1_NO_VALID_VISUAL", True, False, False,
        "upload/handoff_apks/com.farmerbb.notepad_122.apk",
        "b7cf30c187a951203ecf06295653fab587c3e54f155cf54565eda9e27d1444fa",
        "evidence/t279/shots/farmerbb_r1.png",
        "S23: autofill ISE fixed (S23-W3 getSystemService(Class) law), "
        "golden face 31ddd4d5b8e6d18e; T279 two-run DEFAULT_BACKGROUND_ONLY "
        "px 0 unc 28 r1==r2 (the golden face is the engine default class at "
        "the current verdict law); persistence path identified but blocked "
        "at DataStore/protobuf worker-thread NPE (getClass on null after "
        "R337-UNSAFE objectFieldOffset)",
        "DataStore/protobuf worker-thread NPE (uncaught 28)",
        "LOADED/LAUNCHED (no visual at current verdict law)",
        "DataStore worker-thread init",
        "DataStore/protobuf worker-thread getClass-on-null",
        "S23+T279"),
    row("com.itsfrz.tictactoe", "TicTacToe (itsfrz)", "game",
        "PARTIAL", 1, "R1_NO_VALID_VISUAL", True, False, False,
        "upload/handoff_apks/com.itsfrz.tictactoe_5.apk",
        "2a057a9a519acd81dc54af9b3c9f58e40ebd0ce92f949aca65f6c439e8f74d45",
        "evidence/t279/shots/itsfrz_r1.png",
        "S23: APP_PIXELS face d55056a8/d602648e; T279 two-run "
        "DEFAULT_BACKGROUND_ONLY px 0 unc 10 r1==r2 face d55056a8928a26ff "
        "(== S27 wall); custom-cell listener registration gap (0 clickable "
        "views at census)",
        "custom-view click listener registration gap (uncaught 10)",
        "LOADED/LAUNCHED (no visual)", "custom-cell listener registration",
        "setOnClickListener-registered custom cells report 0 listeners",
        "S23+T279"),
    row("org.ecos.logic.flip_a_coin", "Coin Flip", "app",
        "CURRENT-REPRODUCIBLE", 3, "R3_PRIMARY_SCREEN_COMPLETE", True, False,
        False, "upload/handoff_apks/org.ecos.logic.flip_a_coin_3.apk",
        "63730ec2ac320ecb31004c07e60c30f374ab20ad8041147720a967bb2aafd5fb",
        "evidence/t279/shots/flip_r1.png",
        "S23: blank (ConstraintLayout attach 0 addView); S27-W1 "
        "VectorDrawable rasterization law: raster=1 pipeline=1 face b270ff04 "
        "deterministic x6 but died at the S27-W2 viewmodel blocker; T279 "
        "(post S27-W2/W3/W4 laws): REAL_APP_CONTENT px 113,430 r1==r2 face "
        "6808aa29ff941dae — coin face (1) + Flip button VISUALLY VERIFIED "
        "2026-11-28 (vector rasterized + viewtree attached)",
        "none recorded", "LOADED/LAUNCHED/RENDERED",
        "interaction not yet tested", "no prior root cause", "S23+S27+T279"),
    row("com.attenomy.janken", "Janken (RPS)", "game", "BLOCKED", 1,
        "R1_NO_VALID_VISUAL", True, False, False,
        "upload/handoff_apks/com.attenomy.janken_1.apk",
        "7c18c2b21096a1029caec99f447298c502150255dbf0e7a8c4704e835940874c",
        "evidence/t279/shots/janken_r1.png",
        "S23: blank; S23-W1 CompositionLocal provider x4/run deterministic; "
        "T279 two-run DEFAULT_BACKGROUND_ONLY px 0 unc 33 r1==r2 face "
        "d602648e8e401895; compose composition-state layer throw null x22 "
        "(the B1-scale model) is the named next frontier",
        "compose composition-state throw null x22 (uncaught 33)",
        "LOADED/LAUNCHED (no visual)", "compose composition-state layer",
        "compose composition-state throw null x22", "S23+T279"),
    row("tech.gaskell.diceroller", "Dice Roller (debug)", "app",
        "CURRENT-REPRODUCIBLE", 3, "R3_PRIMARY_SCREEN_COMPLETE", True, False,
        False, "upload/handoff_apks/tech.gaskell.diceroller_1_debug.apk",
        "d812e69612ccee064c67a75a6df29ee7b83a2b6395e2f8eb455a02ec66b6161c",
        "evidence/t279/shots/diceroller_r1.png",
        "S23: rc=1 blank, appcompat ActionBarContextView onMeasure "
        "layout_width ISE; S27-W4 onLayout authority law landed; T279: "
        "REAL_APP_CONTENT px 225,233 r1==r2 face 26d1142f19af141d — die "
        "square + Number of Die/Sides labels VISUALLY VERIFIED 2026-11-28; "
        "quirk recorded: initial die shows 00; unc 3 nonfatal",
        "initial die label shows 00 (quirk, recorded)",
        "LOADED/LAUNCHED/RENDERED", "interaction not yet tested",
        "no prior root cause", "S23+S27+T279"),
    row("com.ivylopez.authsrng", "AuthSRNG", "app", "BLOCKED", 1,
        "R1_NO_VALID_VISUAL", True, False, False,
        "upload/handoff_apks/com.ivylopez.authsrng_6.apk",
        "769f4d941400a22a222a0339f96e86de0a8499b9ff345355c3299457bdae75cc",
        "evidence/t279/shots/authsrng_r1.png",
        "S23: blank; compose convertMeasureSpec ISE + upstream "
        "SoftReference.get null (font cache init); T279 two-run "
        "DEFAULT_BACKGROUND_ONLY px 0 unc 33 r1==r2 face b5a7a35d5fe0564b",
        "compose convertMeasureSpec ISE + SoftReference.get null (uncaught 33)",
        "LOADED/LAUNCHED (no visual)", "compose measure + font cache init",
        "SoftReference.get null in font cache init", "S23+T279"),
    row("de.tcrass.minos", "Minos", "app", "PARTIAL", 1,
        "R1_NO_VALID_VISUAL", True, False, False,
        "upload/handoff_apks/de.tcrass.minos_10004.apk",
        "af76923388c4ee3a265f66ea1fdab80092ed72400123d7e23f38a886281228a0",
        "evidence/t279/shots/minos_r1.png",
        "S23: inflate reports views=2 then the content never attaches "
        "(FrameLayout children=0); S27 wall face b5a7a35d last-frame DIFF; "
        "T279 two-run DEFAULT_BACKGROUND_ONLY px 0 unc 0 r1==r2 face "
        "b5a7a35d5fe0564b",
        "inflate->attach gap: FrameLayout children=0 (uncaught 0)",
        "LOADED/LAUNCHED (no visual)", "inflate-attach path",
        "inflated content never attached to the window root", "S23+T279"),
    row("com.minar.randomix", "Randomix", "game",
        "CURRENT-REPRODUCIBLE", 2, "R2_FIRST_FRAME", True, False, False,
        "upload/handoff_apks/com.minar.randomix_42.apk", "",  # sha computed below
        "evidence/t279/shots/randomix_r1.png",
        "S25/S26: golden anchor 31ddd4d5b8e6d18e (engine default class); "
        "S26-W1 fresh-device-per-run law closed its determinism root cause; "
        "T279: REAL_APP_CONTENT px 1,080 r1==r2 face 5fef8090d5c9c87b — "
        "near-blank AppIntro first slide VISUALLY VERIFIED (honest R2: not "
        "a complete screen); AppIntro NextSlide listeners registered after "
        "the ct dispatch census (no ct frame change)",
        "AppIntro intro slide is not the primary screen (R2)",
        "LOADED/LAUNCHED/RENDERED", "intro-slide navigation",
        "no prior root cause", "S25+S26+T279"),
    row("dk.cocode.chess", "Chess (cocode)", "game", "PARTIAL", 1,
        "R1_NO_VALID_VISUAL", True, False, False,
        "upload/handoff_apks/dk.cocode.chess_5022.apk", "",
        "evidence/t279/shots/cocodechess_r1.png",
        "S25/S26 anchor dk.cocode.chess_5022; S27 wall last-frame DIFF vs "
        "d602648e; T279 two-run DEFAULT_BACKGROUND_ONLY px 0 unc 33 r1==r2 "
        "face d602648e8e401895",
        "DEFAULT_BACKGROUND_ONLY (uncaught 33)",
        "LOADED/LAUNCHED (no visual)", "compose/viewtree attach frontier",
        "no app pixels at frame census", "S25+T279"),
]

# compute the two missing APK SHAs from disk (byte-exact originals)
for r in NEW:
    if r["package"] == "com.minar.randomix":
        r["apk_sha256"] = sha256(BASE / "upload/handoff_apks/com.minar.randomix_42.apk")
    if r["package"] == "dk.cocode.chess":
        r["apk_sha256"] = sha256(BASE / "upload/handoff_apks/dk.cocode.chess_5022.apk")

reg = json.load(open(REG))
titles = reg["titles"]
have = {t["package"] for t in titles}

# enrich existing rows (no historical erasure)
T279_CURRENT = {
    "de.duenndns.gmdice": dict(face="3891679dff449331", px=182535, level=3,
                               inter="state-change(ct px 753,437)", status="INTERACTIVE",
                               sc=True),
    "com.dozingcatsoftware.bouncy": dict(face="37326cb2b8bb6bfe", px=1095220, level=3,
                                         inter="state-change(ct face changed)", status="INTERACTIVE",
                                         sc=True),
    "org.secuso.privacyfriendlysolitaire": dict(face="88dbb4a719dbc8d4", px=58212, level=3,
                                                inter="no-frame-change", status="CURRENT-REPRODUCIBLE",
                                                sc=False),
    "com.emmanuelmess.tictactoe": dict(face="b5a7a35d5fe0564b", px=0, level=1,
                                       inter="no-frame-change", status="PARTIAL",
                                       sc=False),
    "com.nononsenseapps.notepad": dict(face="", px=None, level=None,
                                       inter=None, status="PENDING",
                                       sc=None),
}
for t in titles:
    c = T279_CURRENT.get(t["package"])
    if not c:
        continue
    t["t279_status"] = c["status"]
    t["t279_level"] = c["level"]
    t["t279_run1_face16"] = c["face"]
    t["t279_app_px"] = c["px"]
    t["t279_interaction"] = c["inter"]
    t["t279_state_changed"] = c["sc"]
    t["t279_last_tested"] = "2026-11-28"
    t["t279_binary_sha16"] = BIN_SHA16
    if c["status"] == "PARTIAL":
        t["notes"] = (t.get("notes", "") +
                      " | T279 2026-11-28: DEFAULT_BACKGROUND_ONLY px 0 "
                      "(regression vs the registry's VERIFIED claim — "
                      "historical evidence preserved, current status "
                      "corrected to PARTIAL)")

added = 0
for r in NEW:
    if r["package"] in have:
        continue
    titles.append(r)
    have.add(r["package"])
    added += 1

reg["count"] = len(titles)
reg["titles"] = titles
reg["wave"] = "S87 +S141 +T279"
reg["generated"] = ("2026-11-28 T279 rendering-recovery reconciliation "
                    "(commit f9e1d3314: MeasureSpec getMode AOSP law fix, "
                    "uturn recovered to historical face; 27 registry-absent "
                    "achievements registered; 46/46 two-run reproducibility)")
json.dump(reg, open(REG, "w"), indent=1)
print(f"[registry] added {added} rows -> count {reg['count']}")
print(f"[registry] enriched {len(T279_CURRENT) - 1} existing rows with t279_* fields")
from collections import Counter
print("[registry] status counts:", dict(Counter(t["status"] for t in titles)))
