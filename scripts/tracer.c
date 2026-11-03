/* tracer.c — S156 phase-3: poor-man's RIP sampler via ptrace.
 * Spawns the engine (child), samples EVERY thread's RIP at ~20 Hz by
 * PTRACE_ATTACH -> GETREGS -> DETACH, records /proc/PID/maps (PIE base),
 * prints a per-PC histogram + per-thread CPU attribution at exit.
 * Zero engine modification, negligible perturbation (ms-scale stops).
 *
 * Build: gcc -O2 -o scripts/tracer scripts/tracer.c
 * Usage: scripts/tracer <out_rip_hist.txt> <engine> <args...>
 */
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/ptrace.h>
#include <sys/user.h>
#include <sys/wait.h>
#include <sys/types.h>
#include <dirent.h>
#include <time.h>

#define MAXPC 200000

typedef struct { unsigned long pc; long tid; long n; } PCRec;
static PCRec recs[MAXPC];
static int nrecs = 0;

static void add_pc(unsigned long pc, long tid) {
    for (int i = 0; i < nrecs; i++)
        if (recs[i].pc == pc && recs[i].tid == tid) { recs[i].n++; return; }
    if (nrecs < MAXPC) { recs[nrecs].pc = pc; recs[nrecs].tid = tid; recs[nrecs].n = 1; nrecs++; }
}

static int list_tids(pid_t pid, long* tids, int cap) {
    char path[64]; snprintf(path, sizeof path, "/proc/%d/task", pid);
    DIR* d = opendir(path); if (!d) return 0;
    int n = 0; struct dirent* e;
    while ((e = readdir(d)) && n < cap)
        if (e->d_name[0] >= '0' && e->d_name[0] <= '9')
            tids[n++] = atol(e->d_name);
    closedir(d); return n;
}

static void read_base(pid_t pid, char* exe, unsigned long* base) {
    char path[64]; snprintf(path, sizeof path, "/proc/%d/maps", pid);
    FILE* f = fopen(path, "r"); if (!f) return;
    char line[512];
    while (fgets(line, sizeof line, f))
        if (strstr(line, exe) && strstr(line, "r-xp") == NULL &&
            strstr(line, "r--p") != NULL) {
            *base = strtoul(line, NULL, 16); break;
        }
    /* fallback: first mapping of exe */
    if (!*base) { rewind(f);
        while (fgets(line, sizeof line, f))
            if (strstr(line, exe)) { *base = strtoul(line, NULL, 16); break; } }
    fclose(f);
}

int main(int argc, char** argv) {
    if (argc < 3) { fprintf(stderr, "usage: tracer <out> <engine> [args...]\n"); return 2; }
    const char* outp = argv[1];
    const char* engine = argv[2];
    char exe[256]; realpath(engine, exe);

    pid_t pid = fork();
    if (pid == 0) {
        execv(engine, argv + 2);
        _exit(127);
    }
    /* let the child boot into the spin (boot ~2s) */
    usleep(3000000);

    long tids[64]; unsigned long base = 0;
    read_base(pid, exe, &base);
    /* dump maps once mid-run (round ~40) for library resolution */
    char mapsp[512]; snprintf(mapsp, sizeof mapsp, "%s.maps", outp);
    struct timespec ts = {0, 50000000L}; /* 50 ms */
    long rounds = 0; int maps_dumped = 0;
    while (1) {
        int nt = list_tids(pid, tids, 64);
        if (nt == 0) break;
        if (!maps_dumped && rounds >= 40) {
            FILE* mf = fopen(mapsp, "w");
            if (mf) { char src[64]; snprintf(src, sizeof src, "/proc/%d/maps", pid);
                      FILE* s = fopen(src, "r"); char l2[1024];
                      while (s && fgets(l2, sizeof l2, s)) fputs(l2, mf);
                      if (s) fclose(s); fclose(mf); maps_dumped = 1; }
        }
        for (int i = 0; i < nt; i++) {
            long tid = tids[i];
            if (ptrace(PTRACE_ATTACH, tid, 0, 0) != 0) continue;
            int st; waitpid(tid, &st, __WALL);
            struct user_regs_struct regs;
            if (ptrace(PTRACE_GETREGS, tid, 0, &regs) == 0)
                add_pc((unsigned long)regs.rip, tid);
            ptrace(PTRACE_DETACH, tid, 0, 0);
        }
        rounds++;
        nanosleep(&ts, NULL);
        /* stop after ~120 s regardless (engine self-halts earlier) */
        if (rounds > 2400) break;
    }
    int status; waitpid(pid, &status, 0);

    FILE* out = fopen(outp, "w");
    fprintf(out, "# base=0x%lx exe=%s rounds=%ld\n", base, exe, rounds);
    /* sort by count desc */
    for (int i = 0; i < nrecs; i++)
        for (int j = i + 1; j < nrecs; j++)
            if (recs[j].n > recs[i].n) { PCRec t = recs[i]; recs[i] = recs[j]; recs[j] = t; }
    long total = 0;
    for (int i = 0; i < nrecs; i++) total += recs[i].n;
    for (int i = 0; i < nrecs && i < 60; i++)
        fprintf(out, "%6ld %6.2f%% tid=%ld vaddr=0x%lx\n", recs[i].n,
                total ? 100.0 * recs[i].n / total : 0.0, recs[i].tid, recs[i].pc - base);
    fprintf(out, "# total_samples=%ld uniq=%d\n", total, nrecs);
    fclose(out);
    fprintf(stderr, "tracer done: rounds=%ld samples=%ld -> %s\n", rounds, total, outp);
    return 0;
}
