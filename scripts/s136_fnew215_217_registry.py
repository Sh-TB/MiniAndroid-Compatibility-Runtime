#!/usr/bin/env python3
"""S136 — register F-NEW-215/216 (IMPLEMENTED) + F-NEW-217 (PENDING, evidence) in the
root registry, then regenerate the master worklist. Methodology fields follow the
existing entry schema exactly (id/status/priority/layer/title/law/evidence/...)."""
import json, subprocess, sys
from pathlib import Path

REG = Path('/home/z/my-project/canonical/root_cause_registry.json')
WL = Path('/home/z/my-project/canonical/master_worklist.json')

NEW = [
    {
        "id": "F-NEW-215",
        "status": "IMPLEMENTED",
        "priority": "P0",
        "layer": "dex/class-initialization",
        "title": "DEEP-AUDIT (new campaign §6) CLASS-INIT HONESTY LAW: failed <clinit> left the class silently INITIALIZED — ensure_class_initialized marked initialized BEFORE <clinit> ran, ignored try_recursive_invoke's false, and returned true on failure; all active-use sites (sget/sput/new-instance/Class.forName) consumed the bool nowhere; the EXP-088 method-bypass lists swallowed <clinit> itself (TWO independent class-level lists), so desugared j$-CHM's 11 statics never materialized (droidify: okhttp ConnectionPool + DI CursorOwner died far from the cause).",
        "law": "JVMS 5.5 / AOSP ClassLinker::EnsureInitialized: a <clinit> that threw leaves the class ERRONEOUS — never re-run, never silently INITIALIZED; first ACTIVE USE (sget/sput/new-instance/forName) must observe the failure (NoClassDefFoundError). The initialization protocol is NOT bridge-interceptable: <clinit> is exempt from every method-bypass list (compute-methods stay bypassed). sput is ACTIVE USE — it must trigger initialization exactly like sget. Evidence-only bounded lines: [F-NEW-215] CLINIT-FAILED / ERRONEOUS-REUSE / ACTIVE-USE / CLINIT-BYPASS-LIFTED (8/run caps).",
        "evidence": "[F-NEW-215] CLINIT-FAILED class=Lj$/util/concurrent/ConcurrentHashMap; evidence= (empty pre-fix) + ACTIVE-USE new-instance caller=Lokhttp3/ConnectionPool;.<init> + CursorOwner.<init> NCDFE; post-bypass-fix the clinit runs and the okhttp/CursorOwner NCDFE faces are GONE from the droidify run; laws130 51/51; goldens x3 byte-identical (dooz d602648e8e401895, ssw 10446aaf0cd642cc, headingcalc be1cea9cf994b26a, microtimer da73010a37dd0189, whatsapp 31ddd4d5b8e6d18e)",
        "fanout": "every desugared APK (j$/*), every app whose <clinit> throws, all static-registry/DI patterns",
        "test": "3-run protocol + goldens byte-identical",
        "source": "user campaign §6 + droidify first-divergence",
        "current": "IMPLEMENTED+TESTED",
        "risk": "NoClassDefFoundError at active use is JVM-correct; default runs keep goldens byte-identical (proven)",
        "fix": "dalvik_engine.cpp: failed_clinit_classes_ registry + honest return-false; <clinit> exemption in both bypass lists; sput/sput-object init-trigger + erroneous checks; new-instance/forName erroneous checks",
        "after": "droidify chain advances: j$-CHM statics materialize (NANOSECONDS obj cached), okhttp ConnectionPool/CursorOwner proceed to DataStore/kotlinx flow",
        "before": "droidify: j$-CHM clinit silently bypassed (empty-evidence FAILED), NCDFE family at ConnectionPool/CursorOwner",
        "aff": [],
    },
    {
        "id": "F-NEW-216",
        "status": "IMPLEMENTED",
        "priority": "P0",
        "layer": "framework/enum-constant-identity",
        "title": "ENUM-CONSTANT NAME LAW (kOrdinals): the table carried a FICTIONAL member TimeUnit.NANOS (that name belongs to java.time.temporal.ChronoUnit); OpenJDK TimeUnit.java has NANOSECONDS. Every sget of TimeUnit.NANOSECONDS answered null -> kotlin toDuration NPE'd on the null receiver inside the Dagger SettingsSerializer chain -> datastore settings never built (droidify face; the far-from-cause white-screen generator).",
        "law": "SOURCE-FIRST (OpenJDK/AOSP): enum-constant tables must carry the EXACT AOSP member names — a fictional name is a silent-failure magnet because the miss answers null instead of erroring. Constant materialization must be cached per static_key so identity (==) holds (CYCLE-E law).",
        "evidence": "droidify [SGET-MISS] key=Ljava/util/concurrent/TimeUnit;.NANOSECONDS same_class_keys=1 first=TimeUnit;.SECONDS; post-fix [SGET] TimeUnit;.NANOSECONDS obj_id=201 cached across DurationUnit.<clinit> and InstantKt.toDuration; laws130 51/51; goldens x3 byte-identical",
        "fanout": "every kotlinx/desugared duration/time API user (toDuration, datastore settings, timeout configs)",
        "test": "3-run protocol + goldens byte-identical",
        "source": "user campaign §10/§23 + droidify first-divergence",
        "current": "IMPLEMENTED+TESTED",
        "risk": "low — name correction to AOSP source of truth",
        "fix": "kOrdinals entry NANOS -> NANOSECONDS (dalvik_engine.cpp) + law comment",
        "after": "toDuration proceeds; SettingsSerializer chain builds",
        "before": "TimeUnit.NANOSECONDS -> null -> NPE at kotlin/time/InstantKt;.toDuration pc=22",
        "aff": [],
    },
    {
        "id": "F-NEW-217",
        "status": "PENDING",
        "priority": "P1",
        "layer": "runtime/virtual-concurrency",
        "title": "kotlinx-coroutines virtual-concurrency frontier: MutexImpl.unlock F084 spin (50,001 visits, bytecode_size=66) with owner$volatile=NO_OWNER + _availablePermits$volatile=0 + head$volatile=obj#366; sibling face SemaphoreAndMutexImpl.release ISE 'The number of released permits cannot be greater than 1' from okhttp _UtilJvmKt$$ExternalSyntheticLambda0;.m$2. CAS resolution PROVEN NOT the cause ([F-NEW-217] UNSAFE-CAS-UNRESOLVED observability added — zero hits; all offsets registered: owner$volatile->104, _availablePermits$volatile->312). Suspected: waiter-resume protocol across the virtual thread park/resume model (SegmentedQueue/CancellableContinuation resume retry loop) and/or permit bookkeeping across continuation re-entry.",
        "law": "§18/§19: FROZEN/spin must be classified with bounded evidence, never timeout-bumped. Concurrency semantics (release/permit invariant) must hold across virtual suspension: a resumed continuation must not re-run release/finally paths twice.",
        "evidence": "droidify4/droidify5 SPIN-REGS + SPIN-HISTO + THROWABLE-STACK (full capture); AtomicReferenceFieldUpdater.newUpdater REC-MISS at MutexImpl.<clinit> (fallback path taken); Unsafe CAS family bridged and resolving",
        "fanout": "every kotlinx-coroutines app (datastore, okhttp async, lifecycle scopes) — droidify, and the corpus family using coroutines",
        "test": "bounded spin capture + 3-run",
        "source": "user campaign §18/§19",
        "current": "OBSERVED (evidence captured, fix next wave)",
        "risk": "deep subsystem — needs the resume-protocol audit before any patch",
        "fix": "",
        "after": "",
        "before": "MutexImpl.unlock F084 spin; release-permits ISE family (6 APP-BOUNDARY unwinds at MainActivity.onCreate invoke_pc=38/41/52/154/202)",
        "aff": [],
    },
]

def main():
    # AUTHORITATIVE: root_registry.json feeds s128 worklist; the canonical/
    # root_cause_registry.json mirror is kept in sync (S55 sync law).
    for reg_path in (Path('/home/z/my-project/root_registry.json'), REG):
        rc = json.loads(reg_path.read_text())
        items = rc['roots'] if 'roots' in rc else (rc if isinstance(rc, list) else rc.get('items', []))
        key = 'roots' if 'roots' in rc else ('items' if 'items' in rc else None)
        ids = {i.get('id') for i in items}
        for entry in NEW:
            if entry['id'] in ids:
                for i, it in enumerate(items):
                    if it.get('id') == entry['id']:
                        items[i] = entry
                        break
            else:
                items.append(entry)
        out = items if key is None else {**rc, key: items}
        reg_path.write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n')
        print(reg_path.name, 'now', len(items), 'roots')
    # Regenerate worklist
    r = subprocess.run([sys.executable, '/home/z/my-project/scripts/s128_build_master_worklist.py'],
                       capture_output=True, text=True)
    print('worklist regen rc=', r.returncode, (r.stdout or r.stderr)[-200:])

if __name__ == '__main__':
    main()
