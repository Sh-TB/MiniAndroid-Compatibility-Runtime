# UNIFIED_011_1_CANONICAL_HANDOFF — START HERE

This package = the complete MiniAndroid canonical repository (full .git history,
tag v0.11.1-unified-011-1) + recovery forensics. ZERO APK / ZERO AAB / ZERO secrets.

Restore:
    unzip UNIFIED_011_1_CANONICAL_HANDOFF.zip -d miniandroid_011_1
    cd miniandroid_011_1/UNIFIED_011_1_CANONICAL_HANDOFF
    git log --oneline -5          # verify history intact
    git describe --tags           # v0.11.1-unified-011-1

Read (in order):
    miniandroid/START_HERE.md
    HELPER_SOURCE_LIST.md                     <- official open-source source & tool intelligence (لیست کمکی, K-43)
    miniandroid/CODER_HANDOFF_011_1.md        <- entry point after UNIFIED_011.1
    miniandroid/MASTER_RECONCILIATION_011_1.md (what was recovered from where)
    miniandroid/docs/CROSS_CAMPAIGN_RECOVERY_011_1.md (12-campaign map)
    miniandroid/docs/CURRENT_TRUTH_011_1.md + miniandroid/status_011_1.json
    miniandroid/docs/MASTER_TIMELINE_011_1.md, miniandroid/docs/MASTER_KNOWLEDGE_011_1.md

Build + test:
    cd miniandroid && make -j$(nproc)
    python3 scripts/u011_test_matrix.py --apk-dir <external_apk_cache>
    python3 scripts/download_test_apks.sh    # fetch APKs OUTSIDE the repo, SHA-verified

Push (owner with credentials):
    git push origin main && git push origin --tags

Recovery forensics: recovery/ (archive hashes, import log, read-me).
