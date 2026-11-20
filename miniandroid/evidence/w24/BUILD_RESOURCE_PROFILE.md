# W24 Build Resource Profile (today, internally-consistent set)

- Cores: 2 vCPU (cpuset 0,1), no cgroup CPU quota (cfs_quota -1).
- RAM: 4 GB; peak build RSS 1221 MB (FASTPROFILE) / 1425 MB (canonical -g).
- Disk: overlay rootfs ~1.8-2.3 GB free; build dirs are created per profile
  and removed after measurement (sha kept).
- Hypervisor steal: ~14% lifetime of user time; during a 356 s build window
  +172.7 s steal = ~24% of the 2-core budget (w24_steal_sample.txt).
- Effective parallel capacity: 513.9 CPU-s / 349.35 s wall = 1.47 cores.
- CPU inflation -j2 vs -j1: +2.5% only — the loss is idle/steal, not
  contention-inflated work.
- Phase structure (heavy TU): parse ~19%, lang-deferred ~7%,
  opt+generate ~76%, GC ~3%; link 1.5 s; anchors ~3 s.
- Duplicated header parse (gcc -E × consumers): ~25-28 CPU-s total across
  the top-13 headers (json.hpp 43 × 0.158 s the largest single item).
