# W24 Build Resource Profile (today, internally-consistent set)

- Cores: 2 vCPU (cpuset 0,1), no cgroup CPU quota (cfs_quota -1).
- RAM: 4 GB; peak build RSS 1221 MB (FASTPROFILE) / 1425 MB (canonical -g).
- Disk: overlay rootfs ~1.8-2.3 GB free; build dirs are created per profile
  and removed after measurement (sha kept).
- Hypervisor steal (per-build /proc/stat deltas, w24_combo_steal.txt):
  base_a +220.9 s / 440 s window (25% of 2-core budget), base_b +170.8 s
  (24.4%), cand_a +138.5 s (24%), cand_b +139.9 s (24%) — ~24% of every
  build window is stolen by the host; lifetime steal ~14% of user time.
- Effective parallel capacity: 0.739-0.743 (CPU/(wall×2)) — matched across
  the candidate A/B, so the −17.3% wall win is pure work elimination.
- CPU inflation -j2 vs -j1: +2.5% only — the loss is idle/steal, not
  contention-inflated work.
- Candidate RSS 1167 MB (−54 MB vs base: -O1 TUs allocate less).
- Phase structure (heavy TU): parse ~19%, lang-deferred ~7%,
  opt+generate ~76%, GC ~3%; link 1.5 s; anchors ~3 s.
- Duplicated header parse (gcc -E × consumers): ~25-28 CPU-s total across
  the top-13 headers (json.hpp 43 × 0.158 s the largest single item).
