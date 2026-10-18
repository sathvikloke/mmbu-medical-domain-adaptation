"""Closed Phase 1A environment-launch policy and receipt (empty-mapping child launch)."""

import copy
import os
from pathlib import Path
import shutil
import stat
import sys
import tempfile
import unittest

from mmbu_phase1 import canonical, environment
from mmbu_phase1.fields import ContractViolation
from mmbu_phase1.store import RecordStore

REPO = Path(__file__).resolve().parents[2]
PYTHON = os.path.realpath(sys.executable)
PLATFORM = environment.current_platform()


def fresh_run_root(testcase):
    temp = tempfile.TemporaryDirectory()
    testcase.addCleanup(temp.cleanup)
    base = Path(os.path.realpath(temp.name))
    return str(base / "run")


def resealed(record, **changes):
    updated = copy.deepcopy(record)
    updated.update(changes)
    return canonical.seal(updated)


class PolicyConstructionTests(unittest.TestCase):
    def test_linux_branch_has_exactly_the_nine_portable_rows(self):
        rows = environment.expected_environment("linux", 1000, "/srv/repo", "/srv/run")
        self.assertEqual([row["name"] for row in rows], list(environment.SAFE_NAMES))
        self.assertEqual({row["name"]: row["value"] for row in rows}, {
            "HOME": "/srv/run/home", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0", "PYTHONPATH": "/srv/repo/src", "PYTHONUTF8": "1", "TMPDIR": "/srv/run/tmp", "TZ": "UTC",
        })
        self.assertEqual({row["name"]: row["value_source"] for row in rows}["HOME"], "derived_path")
        self.assertNotIn("PATH", [row["name"] for row in rows])

    def test_darwin_branch_adds_only_the_uid_derived_encoding_row(self):
        rows = environment.expected_environment("darwin", 503, "/srv/repo", "/srv/run")
        names = [row["name"] for row in rows]
        self.assertEqual(names, sorted(list(environment.SAFE_NAMES) + ["__CF_USER_TEXT_ENCODING"], key=str.encode))
        extra = [row for row in rows if row["name"] == "__CF_USER_TEXT_ENCODING"][0]
        self.assertEqual(extra, {"name": "__CF_USER_TEXT_ENCODING", "value_source": "platform_derived",
                                 "value": "0x1F7:0x0:0x0"})
        with self.assertRaises(ContractViolation):
            environment.expected_environment("win32", 0, "/srv/repo", "/srv/run")

    def test_policy_record_rejects_every_row_drift(self):
        policy = environment.build_policy(str(REPO), fresh_run_root(self), PYTHON)
        environment.validate_environment_launch_policy(policy)
        rows = policy["environment"]
        mutations = {
            "tenth_name": rows + [{"name": "ZZZ_EXTRA", "value_source": "fixed_literal", "value": "1"}],
            "omitted_row": rows[1:],
            "duplicate_name": [rows[0]] + rows,
            "noncanonical_order": list(reversed(rows)),
            "one_byte_value_change": [{**rows[0], "value": rows[0]["value"] + "x"}] + rows[1:],
            "path_insertion": sorted(rows + [{"name": "PATH", "value_source": "fixed_literal", "value": "/usr/bin"}],
                                     key=lambda r: r["name"].encode()),
            "wrong_value_source": [{**rows[0], "value_source": "fixed_literal"}] + rows[1:],
            "nul_value": [{**rows[0], "value": "a\x00b"}] + rows[1:],
            "canary_row": sorted(rows + [{"name": environment.CANARY_NAME, "value_source": "fixed_literal", "value": "0" * 64}],
                                 key=lambda r: r["name"].encode()),
        }
        for name, environment_rows in mutations.items():
            with self.subTest(mutation=name):
                with self.assertRaises(ContractViolation):
                    environment.validate_environment_launch_policy(resealed(policy, environment=environment_rows))
        for change in ({"platform": "windows"}, {"launch_uid": True}, {"launch_uid": -1},
                       {"python_executable": "python3"}, {"working_directory": "/tmp"},
                       {"parent_canary_name": "OTHER"}, {"repository_root": str(REPO) + "/"},
                       {"run_root": "relative/run"}):
            with self.subTest(change=sorted(change)):
                with self.assertRaises(ContractViolation):
                    environment.validate_environment_launch_policy(resealed(policy, **change))


class PolicyPreflightTests(unittest.TestCase):
    def test_preflight_accepts_fresh_absolute_unaliased_paths(self):
        policy = environment.build_policy(str(REPO), fresh_run_root(self), PYTHON)
        environment.preflight_policy(policy)

    def test_preflight_rejects_pre_existing_symlinked_or_relative_run_root(self):
        run_root = fresh_run_root(self)
        os.mkdir(run_root)
        with self.assertRaises(ContractViolation):
            environment.preflight_policy(environment.build_policy(str(REPO), run_root, PYTHON))
        base = Path(run_root).parent
        (base / "real").mkdir()
        (base / "alias").symlink_to(base / "real", target_is_directory=True)
        with self.assertRaises(ContractViolation):
            environment.preflight_policy(environment.build_policy(str(REPO), str(base / "alias/run"), PYTHON))
        with self.assertRaises(ContractViolation):
            environment.build_policy(str(REPO), "relative/run", PYTHON)

    def test_preflight_rejects_symlinked_hardlinked_or_relative_python(self):
        base = Path(fresh_run_root(self)).parent
        link = base / "python-link"
        link.symlink_to(PYTHON)
        with self.assertRaises(ContractViolation):
            environment.preflight_policy(environment.build_policy(str(REPO), str(base / "run"), str(link)))
        copied = base / "python-copy"
        shutil.copy2(PYTHON, copied)
        os.link(copied, base / "python-hardlink")
        with self.assertRaises(ContractViolation):
            environment.preflight_policy(environment.build_policy(str(REPO), str(base / "run"), str(copied)))
        with self.assertRaises(ContractViolation):
            environment.build_policy(str(REPO), str(base / "run"), "python3")

    def test_preflight_rejects_wrong_uid_platform_or_digest(self):
        policy = environment.build_policy(str(REPO), fresh_run_root(self), PYTHON)
        for change in ({"launch_uid": os.getuid() + 1}, {"python_executable_digest": "0" * 64},
                       {"platform": "linux" if PLATFORM == "darwin" else "darwin"}):
            with self.subTest(change=sorted(change)):
                mutated = dict(policy)
                mutated.update(change)
                if "platform" in change or "launch_uid" in change:
                    mutated["environment"] = environment.expected_environment(
                        mutated["platform"], mutated["launch_uid"], mutated["repository_root"], mutated["run_root"])
                with self.assertRaises(ContractViolation):
                    environment.preflight_policy(canonical.seal(mutated))


    def test_run_root_must_be_fresh_private_empty_and_owned(self):
        policy = environment.build_policy(str(REPO), fresh_run_root(self), PYTHON)
        environment.create_run_root(policy)
        environment.verify_run_root(policy)
        home = Path(policy["run_root"]) / "home"
        os.chmod(home, 0o755)
        with self.assertRaises(ContractViolation):
            environment.verify_run_root(policy)
        os.chmod(home, 0o700)
        (Path(policy["run_root"]) / "tmp/leftover").write_text("x")
        with self.assertRaises(ContractViolation):
            environment.verify_run_root(policy)


class LaunchTests(unittest.TestCase):
    def launch(self, **hooks):
        policy = environment.build_policy(str(REPO), fresh_run_root(self), PYTHON)
        result = environment.launch(policy, ["probe"], **hooks)
        store = RecordStore([policy, result.receipt])
        return policy, result, store

    def test_environment_launch_starts_empty_and_matches_policy_receipt(self):
        policy, result, store = self.launch()
        receipt = environment.check_environment_launch_receipt(store, result.receipt["record_digest"])
        self.assertEqual(receipt["exit_code"], 0, result.stderr)
        self.assertEqual(receipt["child_environment"], environment.projection(policy))
        self.assertEqual(receipt["passed_environment"], environment.projection(policy))
        self.assertEqual(receipt["parent_canary"]["present_in_parent"], True)
        self.assertEqual(receipt["parent_canary"]["present_in_child"], False)
        self.assertEqual(receipt["argv"][0], policy["python_executable"])
        self.assertNotIn(environment.CANARY_NAME, os.environ)
        self.assertNotIn(b"MMBU_PHASE1_PARENT_SECRET_CANARY", canonical.dumps(receipt["child_environment"]))
        self.assertEqual(result.capture["phase1_modules_loaded_before_capture"], [])
        for directory in ("home", "tmp"):
            info = os.lstat(Path(policy["run_root"]) / directory)
            self.assertEqual(stat.S_IMODE(info.st_mode), 0o700)

    def test_environment_launch_rejects_inheritance_unknown_change_and_parent_canary(self):
        cases = {
            "parent_environment_copying": lambda m: {**dict(os.environ), **m},
            "tenth_child_name": lambda m: {**m, "MMBU_EXTRA": "1"},
            "omitted_row": lambda m: {k: v for k, v in m.items() if k != "TZ"},
            "one_byte_value_change": lambda m: {**m, "PYTHONHASHSEED": "1"},
            "path_insertion": lambda m: {**m, "PATH": "/usr/bin:/bin"},
            "canary_inheritance": lambda m: {**m, environment.CANARY_NAME: os.environ[environment.CANARY_NAME]},
        }
        for name, mutate in cases.items():
            with self.subTest(case=name):
                policy, result, store = self.launch(_mutate_mapping=mutate)
                with self.assertRaises(ContractViolation):
                    environment.check_environment_launch_receipt(store, result.receipt["record_digest"])
                self.assertNotEqual(result.receipt["terminal_status"], "succeeded")

    def test_capture_after_application_import_rejects(self):
        late = "import mmbu_phase1.canonical\n" + environment.CHILD_BOOTSTRAP
        policy, result, store = self.launch(_bootstrap=late)
        self.assertTrue(result.capture["phase1_modules_loaded_before_capture"])
        with self.assertRaises(ContractViolation):
            environment.check_environment_launch_receipt(store, result.receipt["record_digest"])

    def test_receipt_record_rejects_duplicate_order_canary_and_digest_drift(self):
        policy, result, store = self.launch()
        receipt = result.receipt
        rows = receipt["child_environment"]
        mutations = {
            "duplicate_name": {"child_environment": [rows[0]] + rows},
            "noncanonical_order": {"child_environment": list(reversed(rows))},
            "extra_child_row": {"child_environment": rows + [{"name": "ZZZ", "value": "1"}]},
            "canary_in_child": {"parent_canary": {**receipt["parent_canary"], "present_in_child": True}},
            "canary_absent_in_parent": {"parent_canary": {**receipt["parent_canary"], "present_in_parent": False}},
            "canary_name": {"parent_canary": {**receipt["parent_canary"], "name": "OTHER"}},
            "policy_digest": {"policy_digest": "0" * 64},
            "shell_invocation": {"argv": ["/bin/sh", "-c", "python3 -m x"]},
            "relative_python_argv": {"argv": ["python3"] + receipt["argv"][1:]},
            "status_mismatch": {"exit_code": 0, "terminal_status": "failed"},
            "late_capture": {"child_captured_at": "2099-01-01T00:00:00.000000Z"},
            "working_directory": {"working_directory": "/tmp"},
        }
        for name, change in mutations.items():
            with self.subTest(mutation=name):
                mutated = resealed(receipt, **change)
                with self.assertRaises(ContractViolation):
                    environment.check_environment_launch_receipt(RecordStore([policy, mutated]), mutated["record_digest"])

    def test_policy_is_single_use(self):
        policy, result, store = self.launch()
        with self.assertRaises(ContractViolation):
            environment.launch(policy, ["probe"])


if __name__ == "__main__":
    unittest.main()
