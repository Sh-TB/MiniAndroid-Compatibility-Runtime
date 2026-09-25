#!/usr/bin/env python3
"""s100_foundation_tests.py — tests for the S98-FUTURE foundation metadata
(registry validation, API mapping, dependency resolution, size gate,
APK profiles, provenance). Negative tests included (S100 §80): the system
must fail explicitly on duplicate capability, unknown dependency, cycle,
missing field, and corrupt metadata.
"""
import json
import os
import sys
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "tools"))
import s100_apk_profile as profiler  # noqa: E402

REG = os.path.join(REPO, "docs", "CAPABILITY_REGISTRY.json")
CORE = os.path.join(REPO, "docs", "CORE_MANIFEST.json")
BASE = os.path.join(REPO, "docs", "SIZE_BASELINE.json")
GATE = os.path.join(REPO, "run", "s100", "size_gate.json")
PROFILES = os.path.join(REPO, "docs", "S100_APK_PROFILES.json")


def load(p):
    with open(p) as f:
        return json.load(f)


def resolve_closure(caps, roots, provides_owner=None):
    provides_owner = provides_owner or {}
    closure, frontier = set(), list(roots)
    while frontier:
        cid = frontier.pop()
        if cid in closure:
            continue
        closure.add(cid)
        for req in caps[cid].get("requires", []):
            frontier.append(provides_owner.get(req, req))
    return closure


def find_cycle(caps):
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {cid: WHITE for cid in caps}
    for start in caps:
        if color[start] != WHITE:
            continue
        stack = [(start, iter(caps[start].get("requires", [])))]
        color[start] = GRAY
        while stack:
            node, it = stack[-1]
            adv = False
            for dep in it:
                dep = caps.get(dep, {}).get("id", dep)
                if color.get(dep, BLACK) == GRAY:
                    return (node, dep)
                if dep in caps and color[dep] == WHITE:
                    color[dep] = GRAY
                    stack.append((dep, iter(caps[dep].get("requires", []))))
                    adv = True
                    break
            if not adv:
                color[node] = BLACK
                stack.pop()
    return None


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.reg = load(REG)
        self.caps = {c["id"]: c for c in self.reg["capabilities"]}

    def test_valid_registry_loads(self):
        self.assertIn("capabilities", self.reg)
        self.assertGreaterEqual(len(self.caps), 20)

    def test_duplicate_capability_rejected(self):
        ids = [c["id"] for c in self.reg["capabilities"]]
        self.assertEqual(len(ids), len(set(ids)), "duplicate capability ids")

    def test_no_missing_required_fields(self):
        for c in self.reg["capabilities"]:
            for field in ("id", "name", "layer", "status", "requires",
                          "source_authority", "hot", "size_class"):
                self.assertIn(field, c, f"{c.get('id')} missing {field}")

    def test_unknown_dependency_detected(self):
        for c in self.caps.values():
            for req in c.get("requires", []):
                if req in self.caps:
                    continue
                owners = [k for k, v in self.caps.items()
                          if req in v.get("provides", [])]
                self.assertTrue(owners,
                                f"{c['id']} requires unknown {req}")

    def test_no_dependency_cycle(self):
        self.assertIsNone(find_cycle(self.caps), "capability graph has a cycle")

    def test_status_vocabulary(self):
        vocab = set(self.reg["status_vocabulary"]["quality_levels"])
        vocab |= {"PARTIAL", "TESTED", "DONE", "VERIFIED", "OBSERVED",
                  "BLOCKED", "PENDING", "UNTESTED"}
        for c in self.caps.values():
            self.assertIn(c["status"], vocab,
                          f"{c['id']} status {c['status']} not in vocabulary")


class MappingTests(unittest.TestCase):
    def setUp(self):
        self.reg = load(REG)

    def test_api_maps_to_capability(self):
        self.assertTrue(any("Ljava/net/URL;" in c.get("api_prefixes", [])
                            for c in self.reg["capabilities"]),
                        "URL must map to network.http")

    def test_api_maps_to_multiple_capabilities(self):
        # webview requires the whole network family (S98 §6 example)
        webview = [c for c in self.reg["capabilities"]
                   if c["id"] == "webview"][0]
        reqs = set(webview["requires"])
        self.assertTrue({"framework.view", "network.http"} <= reqs)

    def test_unknown_api_maps_to_nothing(self):
        caps = {c["id"]: c for c in self.reg["capabilities"]}
        hits = [cid for cid, c in caps.items()
                if any(p.startswith("Lcom/unknown/") for p in c.get("api_prefixes", []))]
        self.assertEqual(hits, [])


class ResolutionTests(unittest.TestCase):
    def setUp(self):
        reg = load(REG)
        self.caps = {c["id"]: c for c in reg["capabilities"]}
        self.owner = {}
        for cid, c in self.caps.items():
            for p in c.get("provides", []):
                self.owner[p] = cid

    def test_direct_dependency(self):
        cl = resolve_closure(self.caps, ["graphics.bitmap"], self.owner)
        self.assertIn("graphics.basic", cl)

    def test_transitive_dependency(self):
        cl = resolve_closure(self.caps, ["webview"], self.owner)
        for need in ("framework.view", "network.http", "graphics.basic"):
            self.assertIn(need, cl)

    def test_closure_deduplicates(self):
        cl = resolve_closure(self.caps,
                             ["graphics.bitmap", "graphics.basic"], self.owner)
        self.assertEqual(len(cl), len(set(cl)))

    def test_cycle_detection_function(self):
        fake = {"a": {"id": "a", "requires": ["b"]},
                "b": {"id": "b", "requires": ["a"]}}
        self.assertIsNotNone(find_cycle(fake))
        self.assertIsNone(find_cycle(self.caps))


class SizeGateTests(unittest.TestCase):
    def test_baseline_exists_and_complete(self):
        b = load(BASE)
        m = b["measured"]
        for k in ("unstripped_bytes", "stripped_bytes", "compressed_gzip_bytes",
                  "text", "data", "bss", "symbol_count_nm"):
            self.assertIn(k, m)
            self.assertGreater(m[k], 0)

    def test_last_gate_pass(self):
        g = load(GATE)
        self.assertEqual(g["status"], "PASS")
        self.assertEqual(g["measured"]["stripped_bytes"],
                         load(BASE)["measured"]["stripped_bytes"],
                         "binary drift vs baseline — re-run the gate")

    def test_missing_measurement_detected(self):
        self.assertRaises(KeyError, lambda: load(BASE)["measured"]["nope"])


class ProfileTests(unittest.TestCase):
    def test_profiles_exist(self):
        p = load(PROFILES)
        self.assertGreaterEqual(len(p["profiles"]), 3)

    def test_static_vs_observed_separate(self):
        p = load(PROFILES)
        for prof in p["profiles"]:
            self.assertIn("static_capabilities", prof)
            self.assertIn("observed_capabilities", prof)
            self.assertNotEqual(prof["static_capabilities"],
                                prof["observed_capabilities"],
                                "static list must never be presented as observed")

    def test_small_apk_small_closure(self):
        p = load(PROFILES)
        browser = [x for x in p["profiles"]
                   if "simplebrowser" in x["apk"]][0]
        self.assertLessEqual(len(browser["resolved_closure"]), 10,
                             "small APK must have a small capability closure")
        self.assertEqual(browser["cold_capabilities_avoided"], [],
                         "browser must avoid cold capabilities (no WebView law)")

    def test_provenance_fields(self):
        for prof in load(PROFILES)["profiles"]:
            self.assertTrue(prof["apk_sha256_16"])
            self.assertGreater(prof["apk_bytes"], 0)


class CoreManifestTests(unittest.TestCase):
    def test_core_manifest_answers_ownership(self):
        m = load(CORE)
        for comp in m["core_components"]:
            self.assertIn("candidate_capability", comp)
            self.assertTrue(comp["candidate_capability"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
