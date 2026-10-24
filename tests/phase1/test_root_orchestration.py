"""Root ``tools/team.py`` orchestration: fail-closed Phase 1 preflight and pass order."""

from contextlib import redirect_stderr, redirect_stdout
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from mmbu_phase1 import authority, scope

REPO = Path(__file__).resolve().parents[2]


def load_team():
    spec = importlib.util.spec_from_file_location("team_for_phase1_orchestration", REPO / "tools/team.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Phase1PreflightTests(unittest.TestCase):
    def setUp(self):
        self.team = load_team()
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(os.path.realpath(temp.name))
        shutil.copytree(REPO / "docs/phase1", self.root / "docs/phase1")
        authority.bootstrap(self.root)
        (self.root / "tests/phase1").mkdir(parents=True)
        for name in scope.REQUIRED_PHASE1_TEST_MODULES:
            shutil.copy2(REPO / "tests/phase1" / name, self.root / "tests/phase1" / name)

    def run_team(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = self.team.main(["--root", str(self.root), *args])
        return code, stdout.getvalue() + stderr.getvalue()

    def test_repository_preflight_passes(self):
        self.assertEqual(self.team.phase1_preflight(REPO), [])
        self.assertEqual(self.team.phase1_preflight(self.root, allow_bootstrap=True), [])

    def test_test_command_fails_closed_when_each_authority_file_is_missing(self):
        for relative in authority.AUTHORITY_PATHS:
            with self.subTest(relative=relative):
                target = self.root / relative
                saved = target.read_bytes()
                target.unlink()
                code, output = self.run_team("test")
                self.assertNotEqual(code, 0)
                self.assertIn(relative, output)
                target.write_bytes(saved)

    def test_test_command_fails_closed_on_invalid_authority_bytes(self):
        target = self.root / authority.OPENING_RECEIPT_REGISTRY_PATH
        record = json.loads(target.read_bytes())
        record["generation"] = 1
        target.write_bytes(json.dumps(record).encode())
        code, output = self.run_team("test")
        self.assertNotEqual(code, 0)
        self.assertIn("opening-receipt-registry.json", output)

    def test_test_command_fails_closed_when_scoped_suite_member_is_missing(self):
        for name in (scope.REQUIRED_PHASE1_TEST_MODULES[0], scope.REQUIRED_PHASE1_TEST_MODULES[-1]):
            with self.subTest(name=name):
                target = self.root / "tests/phase1" / name
                saved = target.read_bytes()
                target.unlink()
                code, output = self.run_team("test")
                self.assertNotEqual(code, 0)
                self.assertIn(name, output)
                target.write_bytes(saved)

    def test_phase1_package_marker_would_double_run_and_is_rejected(self):
        (self.root / "tests/phase1/__init__.py").write_text("")
        code, output = self.run_team("test")
        self.assertNotEqual(code, 0)
        self.assertIn("__init__.py", output)

    def test_contract_gate_still_runs_before_the_preflight(self):
        shutil.rmtree(self.root / "config")
        member = self.root / "docs/phase1/CONTRACT.md"
        raw = member.read_bytes()
        member.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
        code, output = self.run_team("test")
        self.assertNotEqual(code, 0)
        self.assertIn("contract integrity", output)

    def test_required_module_list_matches_the_scoped_suite(self):
        actual = sorted(p.name for p in (REPO / "tests/phase1").glob("test*.py"))
        self.assertEqual(sorted(scope.REQUIRED_PHASE1_TEST_MODULES), actual)
        self.assertIn("test_contract_manifest.py", scope.REQUIRED_PHASE1_TEST_MODULES)


class Phase1PassTests(unittest.TestCase):
    def setUp(self):
        self.team = load_team()

    def test_zero_test_phase1_pass_fails_even_when_unittest_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            stderr = io.StringIO()
            with redirect_stdout(io.StringIO()), redirect_stderr(stderr):
                code = self.team.run_counted([sys.executable, "-m", "unittest", "discover", "-s", tmp], Path(tmp), dict(os.environ))
            self.assertNotEqual(code, 0)

    def test_counted_pass_reports_nonzero_count_and_preserves_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "test_one.py").write_text("import unittest\nclass T(unittest.TestCase):\n    def test_a(self):\n        pass\n")
            stdout = io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(io.StringIO()):
                code = self.team.run_counted([sys.executable, "-m", "unittest", "discover", "-s", tmp, "-v"], Path(tmp), dict(os.environ))
            self.assertEqual(code, 0)
            self.assertIn("Phase 1 CPU test count: 1", stdout.getvalue())
            Path(tmp, "test_one.py").write_text("import unittest\nclass T(unittest.TestCase):\n    def test_a(self):\n        self.fail()\n")
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                code = self.team.run_counted([sys.executable, "-m", "unittest", "discover", "-s", tmp], Path(tmp), dict(os.environ))
            self.assertNotEqual(code, 0)

    def test_root_test_runs_historical_then_repository_then_one_phase1_pass(self):
        calls = []

        def fake_run_commands(commands, cwd, env=None):
            calls.append(("plain", [list(c) for c in commands], Path(cwd), (env or {}).get("PYTHONPATH")))
            return 0

        def fake_run_counted(command, cwd, env):
            calls.append(("counted", [list(command)], Path(cwd), env.get("PYTHONPATH")))
            return 0

        self.team.run_commands = fake_run_commands
        self.team.run_counted = fake_run_counted
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            self.assertEqual(self.team.main(["--root", str(REPO), "test"]), 0)
        self.assertEqual([c[0] for c in calls], ["plain", "plain", "counted"])
        self.assertEqual(calls[0][2], REPO / "outputs/mmbu-precompute")
        self.assertEqual(calls[1][2], REPO)
        self.assertEqual(calls[2][2], REPO)
        self.assertEqual(calls[2][3], str(REPO / "src"))
        self.assertEqual(calls[2][1][0][-4:], ["discover", "-s", "tests/phase1", "-v"])
        self.assertEqual(calls[1][1][0][-4:], ["discover", "-s", "tests", "-v"])

    def test_general_repository_pass_excludes_phase1_tests(self):
        probe = (
            "import unittest, json\n"
            "def walk(s):\n"
            "    for t in s:\n"
            "        yield from (walk(t) if isinstance(t, unittest.TestSuite) else [t.id()])\n"
            "print(json.dumps(sorted(walk(unittest.defaultTestLoader.discover('tests')))))\n"
        )
        env = {**os.environ, "PYTHONPATH": str(REPO / "outputs/mmbu-precompute/src"), "PYTHONDONTWRITEBYTECODE": "1"}
        result = subprocess.run([sys.executable, "-c", probe], cwd=REPO, capture_output=True, text=True, env=env, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)
        ids = json.loads(result.stdout)
        self.assertTrue(ids)
        phase1_modules = {name[:-3] for name in scope.REQUIRED_PHASE1_TEST_MODULES}
        self.assertFalse([i for i in ids if i.split(".")[0] in phase1_modules or i.startswith("phase1.")])
        self.assertFalse((REPO / "tests/phase1/__init__.py").exists())


class HistoricalImmutabilityTests(unittest.TestCase):
    def test_historical_bundle_remains_byte_immutable(self):
        team = load_team()
        self.assertEqual(team.verify_evidence(REPO), [])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(os.path.realpath(tmp))
            for relative in ("outputs", "research", "work/source-expansion"):
                shutil.copytree(REPO / relative, root / relative, ignore=shutil.ignore_patterns("__pycache__"))
            self.assertEqual(team.verify_evidence(root), [])
            manifest = json.loads((root / "outputs/mmbu-precompute/evidence/bundle-manifest.json").read_bytes())
            name = next(n for n in sorted(manifest["files"]) if manifest["files"][n]["bytes"] > 0)
            victim = root / "outputs/mmbu-precompute" / name
            raw = victim.read_bytes()
            victim.write_bytes(raw[:-1] + bytes([raw[-1] ^ 1]))
            errors = "\n".join(team.verify_evidence(root))
            self.assertIn("SHA-256 differs", errors)


if __name__ == "__main__":
    unittest.main()
