#!/usr/bin/env python3
"""CONT-21 / Issue #384 ARCH-001 registry update.

  F-NEW-272 : CLASSIFIED -> ROOT-CAUSED-FIXED (Thread UncaughtExceptionHandler
              law: non-null default per AOSP RuntimeInit, per-thread override
              map, KillApplicationHandler log contract).
  F-NEW-273 : NEW ROOT-CAUSED-FIXED (component-info identity chain:
              ComponentName.<init> producer law + PackageManager.getProviderInfo
              consumer law + BaseBundle.keySet/containsKey/isEmpty reader law —
              the shared androidx.startup startup-cluster primitive across 5
              targets / 3 execution families).
  F-NEW-274 : NEW CLASSIFIED P0 (dooz next divergence after F-272/F-273:
              Lwg0;.y pc=17 iget Lrf1;.f on null — savedstate/coroutine chain).
  F-NEW-275 : NEW CLASSIFIED P1 (PackageInfo GET_SERVICES law gap —
              ServiceInfo.metaData iget on a null ServiceInfo; opencalc face;
              sibling of F-273 in the component-identity family).
  F-NEW-276 : NEW CLASSIFIED P2 (data-path duplication in stream resolution —
              "runtime/data/data/data/<pkg>/runtime/data/..." doubling; dooz
              DataStore settings.preferences_pb face; handled by the app, so
              non-blocking but a genuine path-law defect).
"""
import json, collections

REG = '/home/z/my-project/root_registry.json'
d = json.load(open(REG), object_pairs_hook=collections.OrderedDict)
rows = d['roots']
by_id = {r.get('id'): r for r in rows}

# ---------------------------------------------------------------- F-NEW-272
TOTAL_272 = ("THREAD DEFAULT UNCAUGHT-EXCEPTION-HANDLER LAW GAP — "
    "ROOT-CAUSED+FIXED. The engine had NO law for the Thread handler "
    "family: the instance getUncaughtExceptionHandler() answered the "
    "ThreadShadow no-op void (=null) and no static default existed, so "
    "kotlinx coroutine machinery (dooz Llo;.K pc=0x52: Thread."
    "currentThread().getUncaughtExceptionHandler() then invoke-interface "
    "uncaughtException) executed on a NULL handler and died at f141; the "
    "reporter NPE then propagated (Ltx;.run catch-all -> La12;.y no "
    "handler) into MainActivity.onCreate uncaught -> APP BOUNDARY. "
    "libcore/AOSP law: getUncaughtExceptionHandler() returns the per-thread "
    "handler if set, ELSE Thread.defaultUncaughtExceptionHandler, and on a "
    "live ART runtime the default is NEVER null (RuntimeInit installs "
    "RuntimeInit$KillApplicationHandler at process start); "
    "KillApplicationHandler.uncaughtException logs FATAL EXCEPTION and "
    "models process death (whose runtime face stays owned by the F-016 "
    "exception-honesty machinery — the call itself completes). FIX: engine "
    "Thread UEH law block (pre-shadow-dispatch): static getDefault/setDefault "
    "(engine default_uncaught_handler_ field), instance get/set (per-thread "
    "map thread_uncaught_handlers_), lazy non-null default handler heap "
    "object (Lcom/android/internal/os/RuntimeInit$KillApplicationHandler;), "
    "and the handler's uncaughtException log law. Zero app checks.")
EVID_272 = ("POST-FIX binary 882b7cdf389aabc3 (engine deltas: F273 chain + "
    "F272 law + Bundle keySet family): run/cont21/after/dooz_r3 — BOTH "
    "Thread$UncaughtExceptionHandler NPE faces GONE; [UEH-DEFAULT] FATAL "
    "EXCEPTION (KillApplicationHandler) thread=8123 caller=Llo;.K fires; "
    "zero APP BOUNDARY unwinds in the whole run (pre-fix: 2 + "
    "MainActivity.onCreate invoke_pc=317 death); Status PARTIAL SUCCESS "
    "with only the stub-census + frame-truth caveats; anchor d602648e "
    "unchanged. REGRESSION at 882b7cdf389aabc3: anchors 18/18 x3 "
    "BYTE-IDENTICAL (dooz d602648e8e401895, microtimer da73010a, unote "
    "4f1a9e4e, gmdice f3b483fe, opencalc a976d2f9, tictactoedeluxe "
    "af609429 — run/cont21/anchor_*); fcol 20/20; f259 7/7; f259g 12/13 "
    "(known honest L row F259-L, unchanged); f266 6/6; f268 12/12 "
    "(run/cont21/probes/probe_report.json); g2048 REAL_APP_CONTENT anchor "
    "59ca1526611c4622 MATCH; family sweep dooz/opencalc/stopwatch/telegram/"
    "forkgram all rc 1->0 with byte-identical screenshots "
    "(run/cont21/sweep_*).")

# ---------------------------------------------------------------- F-NEW-273
TOTAL_273 = ("COMPONENT-INFO IDENTITY CHAIN (PackageManager/ComponentName/"
    "Bundle) — ROOT-CAUSED+FIXED. ARCH-001 shared-primitive clustering "
    "(run/cont21/cluster_scan.json) ranked the #1 cross-family primitive: "
    "androidx.startup InitializationProvider.onCreate / AppInitializer."
    "discoverAndInitialize runs `new ComponentName(pkg, cls)` then "
    "PackageManager.getProviderInfo(cn, GET_META_DATA=128) then "
    "providerInfo.metaData.keySet() at EVERY androidx-startup app's process "
    "start. The engine had (a) NO ComponentName.<init> law (REC-MISS — "
    "mPackage/mClass empty), (b) NO PackageManager.getProviderInfo (REC-MISS "
    "-> null -> iget metaData NPE), (c) NO Bundle.keySet/containsKey "
    "(REC-MISS -> null -> Set.iterator NPE). Cluster: dooz (F6-compose), "
    "opencalc (F1), stopwatch (F1, FATAL pre-UI), telegram (F4), forkgram "
    "(F4) — 5 targets / 3 execution families. AOSP laws: ComponentName(pkg,"
    "cls) stores the identity (flattenToString contract); "
    "PackageManager.getProviderInfo returns the manifest-declared "
    "ProviderInfo — NEVER null (NameNotFoundException when absent) with "
    "metaData only under GET_META_DATA; BaseBundle.keySet() returns the key "
    "Set (never null; empty when absent). FIX mapped onto the existing "
    "abstraction: (1) ComponentName.<init> stores mPackage/mClass; "
    "(2) getProviderInfo resolves the component against "
    "manifest_provider_identity_ (exact/bare/suffix — the getActivityInfo "
    "matching law), seeds name/packageName/authority/authorities/"
    "grantUriPermissions/metaData from the same manifest tables the "
    "S1-PROVIDER install path uses (component_meta_data_, resource-id ints), "
    "NameNotFoundException via throw_deferred when absent; (3) Bundle "
    "keySet/containsKey/isEmpty enumerate the bundle: field namespace "
    "(ContentValues keySet materialization convention — array + ArrayList). "
    "Zero app/package checks.")
EVID_273 = ("PRE-FIX (binary b6ee41e77acb88ec, run/cont21/family/*): dooz "
    "log lines 62-68 [REC-MISS] PackageManager.getProviderInfo caller="
    "androidx.startup + [SYNTH-EXC] iget-null-recv ProviderInfo.metaData "
    "(InitializationProvider.onCreate pc=50); stopwatch dies uncaught at "
    "AppInitializer.discoverAndInitialize pc=34 -> APP BOUNDARY (white "
    "screen, colors=1); telegram/forkgram/opencalc same face. DEX law "
    "proven live: scripts/cont11_rawscan dooz InitializationProvider."
    "onCreate (getProviderInfo cn,128 / iget metaData / kc.c) + Lkc;.c "
    "(keySet/iterator chain). POST-FIX (882b7cdf389aabc3): "
    "[F273-PROVINFO] androidx.startup.InitializationProvider metaData "
    "entries=3 (dooz r1; x5 targets in sweep); ProviderInfo.metaData NPE "
    "face GONE x5; post-keySet the dooz startup chain advances through "
    "initializer discovery to the deeper savedstate face (F-NEW-274); "
    "stopwatch rc 1->0, no APP BOUNDARY. dooz dooz_r2 vs r3: startup "
    "clean-to-composition in both after the keySet law.")

# ---------------------------------------------------------------- F-NEW-274
TOTAL_274 = ("SAVEDSTATE/COROUTINE CHAIN NPE (the dooz next divergence after "
    "F-272/F-273). Live face (run/cont21/after/dooz_r3 line ~3036): "
    "[SYNTH-EXC] iget-null-recv NullPointerException 'Attempt to read from "
    "field Lrf1;.f on a null object reference' method=Lwg0;.y pc=17 -> "
    "uncaught (frame unwind + propagate). Lwg0 = lifecycle/savedstate "
    "provider family (SavedStateHandlesProvider neighborhood: Lwg0;.z "
    "populates the SavedStateHandlesProvider map earlier in the same run "
    "with androidx.lifecycle.internal.SavedStateHandlesProvider). The "
    "receiver (an Lrf1; slot) is null where upstream guarantees the "
    "provider/holder object. Generic savedstate/registry object-identity "
    "chain, NOT Compose-specific. NEXT ARMS: disassemble Lwg0;.y pc=17 and "
    "trace who constructs the Lrf1; receiver; audit the F089 map "
    "put/get pair that should hold it; classify producer-missing vs "
    "consumer-ordering.")

# ---------------------------------------------------------------- F-NEW-275
TOTAL_275 = ("PACKAGEINFO GET_SERVICES LAW GAP (sibling of F-NEW-273 in the "
    "component-identity family). Live face (run/cont21/sweep_opencalc "
    "line ~467): [SYNTH-EXC] iget-null-recv 'Attempt to read from field "
    "Landroid/content/pm/ServiceInfo;.metaData on a null object reference' "
    "method=Lg/t;.b pc=36 — the app iterates PackageInfo.services and the "
    "engine's getPackageInfo never fills the services array (only the "
    "GET_PROVIDERS providers path exists, GATE A #370). AOSP law: with "
    "GET_SERVICES (0x20) the returned PackageInfo.services array lists "
    "every manifest <service> as a ServiceInfo carrying name/"
    "packageName + metaData under GET_META_DATA. Generic component-"
    "identity work — no app checks. NEXT ARMS: mirror the providers "
    "array law for services (manifest service table + component meta-"
    "data), then re-run opencalc.")

# ---------------------------------------------------------------- F-NEW-276
TOTAL_276 = ("DATA-PATH DUPLICATION IN STREAM RESOLUTION (non-blocking but a "
    "genuine path-law defect). Live face (run/cont21/after/dooz_r3 line "
    "~1194, x15 in cluster logs): [SYNTH-EXC] STREAM-OPEN "
    "FileNotFoundException 'runtime/data/data/data/io.github.yamin8000.dooz"
    "/runtime/data/runtime/data/runtime/data/data/data/io.github.yamin8000"
    ".dooz/files/datastore/settings.preferences_pb (open failed: ENOENT)' "
    "method=Ly8;.q pc=59 — the <data-root>/data/data/<pkg> prefix is "
    "doubled/re-doubled across resolution layers (F-NEW-234 Context-"
    "anchored directory law interacting with a caller that already "
    "pre-pended it). The app catches the FileNotFoundException (DataStore "
    "first-run face), so the run continues — but the path corruption is "
    "engine-side. NEXT ARMS: capture the two path fragments at the join "
    "point; fix the single resolution law so both bare and absolute "
    "inputs resolve once; regression on microtimer (18 occurrences in "
    "its SUCCESS run) + unote.")

for r in rows:
    if r.get('id') == 'F-NEW-272':
        r['status'] = 'ROOT-CAUSED-FIXED'
        r['title'] = ('THREAD DEFAULT UNCAUGHT-EXCEPTION-HANDLER LAW GAP '
                      '(CLOSED): the engine answered the Thread handler '
                      'family with null/void; kotlinx coroutine exception '
                      'machinery executed UncaughtExceptionHandler.'
                      'uncaughtException on null and the reporter NPE '
                      'killed MainActivity. FIX: AOSP RuntimeInit law — '
                      'non-null lazy default handler + per-thread override '
                      'map + KillApplicationHandler log contract.')
        r['root_cause'] = TOTAL_272
        r['evidence'] = EVID_272
        r['probe'] = ('[UEH-DEFAULT] bounded diag (engine); dooz r2-vs-r3 '
                      'face diff (run/cont21/after/); anchors + probe '
                      'battery at 882b7cdf389aabc3.')
        r['verified_current'] = ('CONT-21 at 882b7cdf389aabc3: both NPE '
                                 'faces GONE; UEH-DEFAULT fires; zero APP '
                                 'BOUNDARY in dooz; anchors 18/18 x3 + '
                                 'probe battery identical to the recorded '
                                 'green state.')
        r['fix'] = ('miniandroid/src/dex/dalvik_engine.cpp — Thread UEH law '
                    'block in try_shadow_dispatch (pre-registry-dispatch): '
                    'static get/set + instance get/set + lazy non-null '
                    'default (RuntimeInit$KillApplicationHandler) + '
                    'uncaughtException log law; state fields '
                    'default_uncaught_handler_ / thread_uncaught_handlers_ '
                    'in dalvik_engine.h. No app checks.')
        r['date'] = '2026-10-08'

rows.append(collections.OrderedDict([
    ('id', 'F-NEW-273'),
    ('status', 'ROOT-CAUSED-FIXED'),
    ('title', 'COMPONENT-INFO IDENTITY CHAIN (ComponentName.<init> producer + '
              'PackageManager.getProviderInfo consumer + BaseBundle.keySet '
              'reader) — the ARCH-001 #1 shared primitive: androidx.startup '
              'process-start discovery NPEs at ProviderInfo.metaData / '
              'Set.iterator in every androidx-startup app (5 targets, 3 '
              'execution families: dooz/opencalc/stopwatch/telegram/'
              'forkgram).'),
    ('priority', 'P0'),
    ('layer', 'framework/package-manager + bundle'),
    ('root_cause', TOTAL_273),
    ('evidence', EVID_273),
    ('probe', ('scripts/cont21_cluster_scan.py (P1/P2 cluster counts across '
               '14 family runs); scripts/cont11_rawscan.py DEX laws; '
               '[F273-PROVINFO] bounded diag (engine); post-fix sweep '
               'rc-flip evidence run/cont21/sweep_*.')),
    ('verified_current', ('CONT-21 at 882b7cdf389aabc3: F273-PROVINFO fires '
                          'x5 targets with real metaData entries; '
                          'ProviderInfo.metaData + Set.iterator NPE faces '
                          'GONE x5; stopwatch rc 1->0 no APP BOUNDARY; '
                          'anchors 18/18 x3 + probes green.')),
    ('fix', ('miniandroid/src/dex/dalvik_engine.cpp — three laws in '
             'try_shadow_dispatch: (1) ComponentName.<init>(pkg,cls) stores '
             'mPackage/mClass; (2) PackageManager.getProviderInfo(Component'
             'Name, flags) resolves manifest_provider_identity_ + seeds '
             'ProviderInfo (name/packageName/authority/authorities/grants/'
             'metaData from component_meta_data_) with NameNotFoundException '
             'via throw_deferred; (3) BaseBundle keySet/containsKey/isEmpty '
             'over the bundle: field namespace (EXP-093 block). No app '
             'checks.')),
    ('date', '2026-10-08'),
]))

rows.append(collections.OrderedDict([
    ('id', 'F-NEW-274'),
    ('status', 'CLASSIFIED'),
    ('title', 'SAVEDSTATE/COROUTINE CHAIN NPE: Lwg0;.y pc=17 reads field '
              'Lrf1;.f on a null receiver (dooz next divergence after '
              'F-272/F-273; the run continues via compatibility-continue '
              'but this is the remaining uncaught face in dooz).'),
    ('priority', 'P0'),
    ('layer', 'framework/savedstate + coroutines'),
    ('root_cause', TOTAL_274),
    ('evidence', ('run/cont21/after/dooz_r3 (~line 3036) at '
                  '882b7cdf389aabc3: single remaining uncaught face; F089 '
                  'map put of SavedStateHandlesProvider present earlier in '
                  'the same run.')),
    ('probe', 'PENDING: cont11_rawscan Lwg0;.y + producer trace.'),
    ('date', '2026-10-08'),
]))

rows.append(collections.OrderedDict([
    ('id', 'F-NEW-275'),
    ('status', 'CLASSIFIED'),
    ('title', 'PACKAGEINFO GET_SERVICES LAW GAP: PackageInfo.services is '
              'never populated (only the GET_PROVIDERS path exists), so '
              'apps iterating services read ServiceInfo.metaData on a null '
              'element (opencalc Lg/t;.b pc=36). Sibling of F-NEW-273.'),
    ('priority', 'P1'),
    ('layer', 'framework/package-manager'),
    ('root_cause', TOTAL_275),
    ('evidence', ('run/cont21/sweep_opencalc (~line 467) at '
                  '882b7cdf389aabc3; opencalc continues via '
                  'compatibility-continue and keeps its REAL_APP_CONTENT '
                  'anchor.')),
    ('probe', 'PENDING: mirror the providers array law; opencalc re-run.'),
    ('date', '2026-10-08'),
]))

rows.append(collections.OrderedDict([
    ('id', 'F-NEW-276'),
    ('status', 'CLASSIFIED'),
    ('title', 'DATA-PATH DUPLICATION IN STREAM RESOLUTION: the '
              '<data-root>/data/data/<pkg> prefix doubles across resolution '
              'layers ("runtime/data/data/data/<pkg>/runtime/data/..."), '
              'ENOENT on DataStore files (dooz settings.preferences_pb; '
              'non-blocking — app-caught).'),
    ('priority', 'P2'),
    ('layer', 'storage/path resolution'),
    ('root_cause', TOTAL_276),
    ('evidence', ('run/cont21/after/dooz_r3 (~line 1194); cluster logs '
                  'microtimer x18 / telegram x25 / forkgram x12 '
                  '(run/cont21/cluster_scan.json P8).')),
    ('probe', 'PENDING: capture both fragments at the join point.'),
    ('date', '2026-10-08'),
]))

d['total_roots'] = len(rows)
d['total'] = len(rows)
d['status_counts'] = dict(collections.Counter(r.get('status', '?') for r in rows))
d['generated'] = '2026-10-08 CONT-21'
json.dump(d, open(REG, 'w'), indent=1)
print('registry updated:', len(rows), 'roots')
print(json.dumps(d['status_counts'], indent=1))
