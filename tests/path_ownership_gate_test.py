#!/usr/bin/env python3
"""S214-WP2 required gate tests (#587 comment 6853939129) + S213 policy tests.

Positive: legit runtime source, maintained test, minimal fixture, approved image,
pinned upstream manifest, baseline-covered image, exception-covered image all PASS.
Negative: unregistered directory, frozen-area new file, oversized PNG, oversized
JPEG, duplicate screenshot, raw log, machine path, consumer-less scratch file,
escaping symlink, budget breach, .rej residue — ALL FAIL with a precise reason.
Each negative asserts the exact validator code. The clean-clone no-residue proof
runs separately: scripts/s229_clean_clone_residue_test.sh.
"""
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
from PIL import Image

VALIDATOR = TOOLS / "policy_validator.py"


def build_fixture_repo(tmp):
    """A minimal git repo exercising every gate with its own registries."""
    r = Path(tmp)
    (r / "miniandroid/src/dex").mkdir(parents=True)
    (r / "tests").mkdir(parents=True)
    (r / "fixtures").mkdir(parents=True)
    (r / "docs").mkdir(parents=True)
    (r / "upstream/pinned").mkdir(parents=True)
    (r / "canonical").mkdir(parents=True)
    (r / "hist").mkdir(parents=True)
    (r / "approvedarea").mkdir(parents=True)

    files = {
        "miniandroid/src/dex/engine.cpp": "int main(){return 0;}\n",
        "tests/test_ok.py": "def test_ok():\n    assert True\n",
        "fixtures/input.bin": bytes(range(256)),
        "upstream/pinned/MANIFEST.json": json.dumps({"pinned": True}),
        "canonical/small.png": None,          # filled below (small image)
        "hist/old.json": "{}\n",              # frozen-area member
        "approvedarea/ok.txt": "hello\n",
        "README.md": "# fixture\n",
    }
    # canonical small PNG (approved area, within budget)
    buf = io.BytesIO(); Image.new("RGB", (40, 40), (9, 9, 9)).save(buf, format="PNG")
    files["canonical/small.png"] = buf.getvalue()

    for path, data in files.items():
        p = r / path
        if data is None:
            p.write_bytes(b"")
        elif isinstance(data, bytes):
            p.write_bytes(data)
        else:
            p.write_text(data)

    frozen_members = ["hist/old.json"]
    snap = hashlib.sha256("\n".join(sorted(frozen_members)).encode()).hexdigest()
    # baseline + exception fixtures (150KB PNG paths pre-declared)
    noisy = Image.new("RGB", (300, 300))
    noisy.putdata([(i * 7 % 256, i * 13 % 256, i * 29 % 256) for i in range(300 * 300)])
    b2 = io.BytesIO(); noisy.save(b2, format="PNG")
    (r / "evidence_legacy.png").write_bytes(b2.getvalue())      # 300x300 noise ~= 150KB? check
    if (r / "evidence_legacy.png").stat().st_size < 100 * 1024:
        big = Image.new("RGB", (600, 600))
        big.putdata([(i * 7 % 256, i * 13 % 256, i * 29 % 256) for i in range(600 * 600)])
        b3 = io.BytesIO(); big.save(b3, format="PNG")
        (r / "evidence_legacy.png").write_bytes(b3.getvalue())
    legacy_size = (r / "evidence_legacy.png").stat().st_size

    (r / "docs" / "IMAGE_POLICY_BASELINE.json").write_text(json.dumps({
        "legacy_images": [{"path": "evidence_legacy.png", "bytes": legacy_size,
                           "sha256": hashlib.sha256((r / "evidence_legacy.png").read_bytes()).hexdigest()}]}))
    (r / "docs" / "IMAGE_EXCEPTIONS.json").write_text(json.dumps({"exceptions": []}))
    (r / "docs" / "PATH_OWNERSHIP.json").write_text(json.dumps({
        "top_level": {t: {"owner": "t", "purpose": "fixture"} for t in
                      ("miniandroid", "tests", "fixtures", "docs", "upstream",
                       "canonical", "hist", "approvedarea", ".gitignore")},
        "approved_dirs": ["README.md", ".gitignore", "miniandroid", "miniandroid/src",
                          "tests", "fixtures", "docs", "upstream", "upstream/pinned",
                          "canonical", "hist", "approvedarea", "evidence_legacy.png",
                          "docs/IMAGE_POLICY_BASELINE.json", "docs/IMAGE_EXCEPTIONS.json",
                          "docs/PATH_OWNERSHIP.json", "docs/SIZE_BUDGET.json"],
        "frozen_snapshot": {"hist": {"tracked_file_count": 1, "snapshot_sha256": snap}},
        "scratch_rules": {
            "regex": [r"_out\d*\.txt$", r"(^|/)scratch"],
            "exempt_prefixes": [], "exempt_extensions": [".py"]},
        "wave_evidence_registered": {"path": ""}}))
    (r / "docs" / "SIZE_BUDGET.json").write_text(json.dumps({
        "areas": {"approvedarea": {"budget_bytes": 8 * 1024 * 1024}}}))
    (r / ".gitignore").write_text("")

    def git(*args):
        subprocess.run(["git", "-C", str(r)] + list(args), capture_output=True, check=True)
    git("init", "-q")
    git("add", "-A")
    git("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-qm", "fixture")
    return r


def run_validator(root):
    env = dict(os.environ, MINIANDROID_REPO_ROOT=str(root))
    p = subprocess.run([sys.executable, str(VALIDATOR)], capture_output=True, text=True, env=env)
    return p.returncode, p.stdout


def add_and_commit(root, relpath, data, as_symlink_target=None):
    p = root / relpath
    p.parent.mkdir(parents=True, exist_ok=True)
    if as_symlink_target:
        os.symlink(as_symlink_target, p)
    else:
        p.write_bytes(data if isinstance(data, bytes) else data.encode())
    subprocess.run(["git", "-C", str(root), "add", "-A"], capture_output=True, check=True)
    subprocess.run(["git", "-C", str(root), "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-qm", "add " + relpath], capture_output=True, check=True)


class PathOwnershipGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = tempfile.mkdtemp(prefix="pog_base_")
        build_fixture_repo(cls.base)

    def _violations(self, root):
        rc, out = run_validator(root)
        return rc, out

    # ---------- POSITIVE (clean fixture passes) ----------
    def test_00_positive_fixture_passes(self):
        rc, out = self._violations(self.base)
        self.assertEqual(rc, 0, "positive fixture must pass, got:\n" + out)
        self.assertIn("0 violation", out)

    # ---------- NEGATIVE ----------
    def test_10_unregistered_directory_fails(self):
        root = self._fresh()
        add_and_commit(root, "newwave_s999/run1/report.json", "{}\n")
        rc, out = self._violations(root)
        self.assertNotEqual(rc, 0)
        self.assertIn("UNREGISTERED_DIRECTORY", out)
        self.assertIn("newwave_s999", out)

    def test_11_frozen_area_new_file_fails(self):
        root = self._fresh()
        add_and_commit(root, "hist/brand_new.json", "{}\n")
        rc, out = self._violations(root)
        self.assertNotEqual(rc, 0)
        self.assertIn("FROZEN_SNAPSHOT_DRIFT", out)
        self.assertIn("hist", out)

    def test_12_oversized_png_without_exception_fails(self):
        import random
        root = self._fresh()
        rng = random.Random(212)
        big = Image.frombytes("RGB", (700, 700),
                              bytes(rng.randrange(256) for _ in range(700 * 700 * 3)))
        buf = io.BytesIO(); big.save(buf, format="PNG")
        self.assertGreater(buf.tell(), 100 * 1024)
        add_and_commit(root, "approvedarea/big.png", buf.getvalue())
        rc, out = self._violations(root)
        self.assertNotEqual(rc, 0)
        self.assertIn("IMAGE_POLICY_NEW", out)
        self.assertIn("approvedarea/big.png", out)

    def test_13_oversized_jpeg_over_200kib_fails(self):
        root = self._fresh()
        noise = Image.new("RGB", (1600, 1600))
        noise.putdata([(i * 7 % 256, i * 13 % 256, i * 29 % 256) for i in range(1600 * 1600)])
        buf = io.BytesIO(); noise.save(buf, format="JPEG", quality=95)
        self.assertGreater(buf.tell(), 200 * 1024)
        add_and_commit(root, "approvedarea/huge.jpg", buf.getvalue())
        rc, out = self._violations(root)
        self.assertNotEqual(rc, 0)
        self.assertIn("IMAGE_POLICY_NEW", out)

    def test_14_duplicate_screenshot_fails(self):
        import random
        root = self._fresh()
        rng = random.Random(214)
        noise = Image.frombytes("RGB", (500, 500),
                                bytes(rng.randrange(256) for _ in range(500 * 500 * 3)))
        buf = io.BytesIO(); noise.save(buf, format="PNG")
        data = buf.getvalue()
        self.assertGreater(len(data), 100 * 1024)
        add_and_commit(root, "approvedarea/shot_a.png", data)
        add_and_commit(root, "approvedarea/shot_b.png", data)
        rc, out = self._violations(root)
        self.assertNotEqual(rc, 0)
        self.assertIn("DUPLICATE_OVER_100KB", out)

    def test_15_raw_log_fails(self):
        root = self._fresh()
        add_and_commit(root, "approvedarea/build_out2.txt", "x\n")
        rc, out = self._violations(root)
        self.assertNotEqual(rc, 0)
        self.assertIn("SCRATCH_RESIDUE", out)
        self.assertIn("build_out2.txt", out)

    def test_16_machine_path_in_maintained_area_fails(self):
        root = self._fresh()
        add_and_commit(root, "tests/leak.py", 'P = "/home/z/my-project/x"\n')
        rc, out = self._violations(root)
        self.assertNotEqual(rc, 0)
        self.assertIn("MACHINE_PATH_MAINTAINED", out)

    def test_17_consumer_less_scratch_file_fails(self):
        root = self._fresh()
        add_and_commit(root, "approvedarea/scratch_tmp.json", "{}\n")
        rc, out = self._violations(root)
        self.assertNotEqual(rc, 0)
        self.assertIn("SCRATCH_RESIDUE", out)

    def test_18_symlink_escape_fails(self):
        root = self._fresh()
        outside = Path(tempfile.mkdtemp(prefix="pog_outside_")) / "target.txt"
        outside.write_text("secret\n")
        add_and_commit(root, "approvedarea/escape.lnk", None,
                       as_symlink_target=str(outside))
        rc, out = self._violations(root)
        self.assertNotEqual(rc, 0)
        self.assertIn("SYMLINK_ESCAPE", out)

    def test_19_budget_breach_fails(self):
        root = self._fresh()
        budget = json.loads((root / "docs/SIZE_BUDGET.json").read_text())
        budget["areas"]["approvedarea"]["budget_bytes"] = 1024 * 1024
        (root / "docs/SIZE_BUDGET.json").write_text(json.dumps(budget))
        add_and_commit(root, "approvedarea/payload.bin", bytes(2 * 1024 * 1024))
        rc, out = self._violations(root)
        self.assertNotEqual(rc, 0)
        self.assertIn("SIZE_BUDGET_EXCEEDED", out)
        self.assertIn("approvedarea", out)

    def test_20_patch_reject_residue_fails_everywhere(self):
        root = self._fresh()
        add_and_commit(root, "miniandroid/src/dex/engine.cpp.rej", "hunk\n")
        rc, out = self._violations(root)
        self.assertNotEqual(rc, 0)
        self.assertIn("SCRATCH_RESIDUE", out)
        self.assertIn(".rej", out)

    # ---------- exception/baseline acceptance ----------
    def test_30_exception_covered_image_passes(self):
        import random
        root = self._fresh()
        reg = json.loads((root / "docs/IMAGE_EXCEPTIONS.json").read_text())
        reg["exceptions"].append({"path": "approvedarea/big.png", "owner": "t",
                                  "reason": "diagram", "review_trigger": "2027-01-01"})
        (root / "docs/IMAGE_EXCEPTIONS.json").write_text(json.dumps(reg))
        rng = random.Random(212)
        big = Image.frombytes("RGB", (700, 700),
                              bytes(rng.randrange(256) for _ in range(700 * 700 * 3)))
        buf = io.BytesIO(); big.save(buf, format="PNG")
        self.assertGreater(buf.tell(), 100 * 1024)
        add_and_commit(root, "approvedarea/big.png", buf.getvalue())
        rc, out = self._violations(root)
        self.assertEqual(rc, 0, out)

    def _fresh(self):
        d = tempfile.mkdtemp(prefix="pog_clone_")
        root = Path(d) / "repo"
        subprocess.run(["git", "clone", "-q", self.base, str(root)], check=True)
        return root

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.base, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
