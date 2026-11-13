# S156-T7 — ConnectBot (org.connectbot, vc=11101000) five-stage frontier

Engine: S155 rebuild `35cd06374f3c457b` + anchor law `a9b58de1d4e56f01`
(control — unchanged face across both, byte-identical). APK pin
`96cf501a83e89284`, **vc=11101000 FIXED this wave** (the standing open
question), versionName 1.11.1-oss, minSdk 24, targetSdk 36, 1 dex, main
`org.connectbot.ui.MainActivity`, app class `ConnectBotApplication`
(androguard-verified).

## Stage 1 — PIN

sha16 `96cf501a83e89284`, zip magic OK. Compose (2503) + trilead ssh2 (127)
+ dagger (30) + navigation (93). Note: NO koin refs (dagger DI family).

## Stage 2 — androguard profile

Families: compose/ui=940, foundation=732, material=396, runtime=270,
coroutines=253, appcompat=194, trilead/ssh2=127, navigation=93,
material(google)=86, lifecycle=84, fragment=50, dagger=30.

## Stage 3 — BOOT

Face `b5a7a35d5fe0564b` (chrome-only blank; byte-identical to the tictactoe
blank — the DEFAULT_BACKGROUND_ONLY family), 12/12 frames, wall 3.3 s,
13 uncaught, 7 NPE rows, stable across both engine builds.

## Stage 4 — ROOT CAUSE (full evidenced chain)

+        if tag not in EXPECT:
            continue
        r = run_once(tag, APK_DIR / fname, package, "postA")
        out["anchors"][tag] = {
            "face": r["face"], "expected": EXPECT[tag],
            "match": r["face"] == EXPECT[tag], "uncaught": r["uncaught"],
        }
        print(tag, r["face"], "match", r["face"] == EXPECT[tag])
    out["apps"] = {}
    for tag in ("tusky", "nextcloud", "connectbot", "thunderbird"):
        try:
            row = boot(tag, 100, 12)
            out["apps"][tag] = {
                "face": row["screenshot_sha16"], "wall_s": row["wall_s"],
                "uncaught": row["uncaught"], "npe": row["npe_rows"],
                "ndfe": row["ndfe"][:6], "frames": row["n_frames_captured"],
            }
        except Exception as e:
            out["apps"][tag] = {"error": str(e)[:200]}
    (EVID / "RERUN_AFTER_ANCHORS.json").write_text(json.dumps(out, indent=1))
    print("WROTE", EVID / "RERUN_AFTER_ANCHORS.json")


if __name__ == "__main__":
    main()

--- S230 RECOVERY NOTE: the patch segment as posted on #586 was TRUNCATED by the comment body: hunk declares 67 new lines, 53 were posted. The recovered content above is everything that arrived; the tail was not recoverable from the comment. ---
