# Recovery forensics snapshot

- FORENSICS_SUMMARY.json — SHA-256 + member census of every recovered archive
  (UNIFIED_003..010_FINAL), all hash-verified against their recorded sidecars.
  Originals: /home/z/my-project/download/miniandroid_unified_campaign/ (000-002)
  and /tmp/my-project/download/miniandroid_unified_campaign/ (003-010).
- IMPORT_LOG.txt — file-by-file selective-import record (95 entries).
- Full extraction + diff data intentionally NOT packaged (size): keep the
  external forensics cache /home/z/my-project/u011_1_forensics/ until the
  next campaign, then re-derive from the archives at the paths above.
