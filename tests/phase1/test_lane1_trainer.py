"""Competition Lane 1 CPU-only synthetic trainer conformance tests."""

from copy import deepcopy
import ast
import builtins
import importlib.util
import io
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from mmbu_phase1 import canonical, lane1_synthetic, lane1_trainer
from mmbu_phase1.fields import ContractViolation
from test_package_f_manifest_v2 import (
    B0,
    B1_DUAL,
    B1_TASK,
    B2_DUAL,
    B2_TASK,
    valid_v2_manifest,
    reseal,
)


ARM_IDS = (B0, B1_TASK, B1_DUAL, B2_TASK, B2_DUAL)


def q(numerator, denominator=1):
    return {"denominator": denominator, "numerator": numerator}


def row(row_id, unit_id, feature, task, context):
    return {
        "context_target": context,
        "feature": feature,
        "independent_unit_id": unit_id,
        "row_id": row_id,
        "task_target": task,
    }


def valid_fixture():
    return {
        "biomedical_content": False,
        "evaluation_rows": [
            row("eval-1", "eval-unit-1", q(-1), 0, 0),
            row("eval-2", "eval-unit-2", q(1), 1, 1),
            row("eval-3", "eval-unit-3", q(0), 1, None),
        ],
        "fixture_id": "lane1-fixture-v1",
        "mmbu_public_content": False,
        "origin_class": "synthetic_engineering",
        "schema_id": "mmbu.synthetic.lane1_fixture",
        "schema_version": 1,
        "train_rows": [
            row("train-1", "train-unit-1", q(1), 1, 0),
            row("train-2", "train-unit-2", q(1), 1, 0),
        ],
    }


def valid_config(fixture=None):
    fixture = valid_fixture() if fixture is None else fixture
    return {
        "allowed_fixture_digest": canonical.value_digest(fixture),
        "checkpoint_after_updates": 1,
        "epochs": 1,
        "learning_rate": q(1, 2),
        "schema_id": "mmbu.synthetic.lane1_config",
        "schema_version": 1,
        "seed": 17,
        "trainable_names_by_architecture": {
            "recipe_arch::B0": [],
            "recipe_arch::B1-L": ["language_adapter"],
            "recipe_arch::B2-P": ["language_adapter", "projector_adapter"],
        },
    }


class FixtureContractTests(unittest.TestCase):
    def test_valid_fixture_and_config_are_closed(self):
        fixture = valid_fixture()
        self.assertEqual(lane1_trainer.validate_fixture(fixture), fixture)
        self.assertEqual(lane1_trainer.validate_config(valid_config(fixture), fixture), valid_config(fixture))

    def test_fixture_rejects_origin_flags_unknowns_and_bad_rationals(self):
        mutations = (
            ("origin", lambda value: value.__setitem__("origin_class", "biomedical")),
            ("biomedical", lambda value: value.__setitem__("biomedical_content", True)),
            ("public", lambda value: value.__setitem__("mmbu_public_content", True)),
            ("unknown", lambda value: value.__setitem__("surprise", False)),
            ("bad-rational", lambda value: value["train_rows"][0].__setitem__("feature", q(2, 2))),
            ("missing-train-context", lambda value: value["train_rows"][0].__setitem__("context_target", None)),
            ("zero-eval-context", lambda value: [item.__setitem__("context_target", None)
                                                   for item in value["evaluation_rows"]]),
        )
        for label, mutate in mutations:
            value = valid_fixture()
            mutate(value)
            with self.subTest(label=label), self.assertRaises(ContractViolation):
                lane1_trainer.validate_fixture(value)

    def test_fixture_rejects_duplicate_or_overlapping_ids(self):
        for field in ("row_id", "independent_unit_id"):
            for placement in ("within-train", "across-splits"):
                value = valid_fixture()
                if placement == "within-train":
                    value["train_rows"][1][field] = value["train_rows"][0][field]
                else:
                    value["evaluation_rows"][0][field] = value["train_rows"][0][field]
                with self.subTest(field=field, placement=placement), self.assertRaises(ContractViolation):
                    lane1_trainer.validate_fixture(value)

    def test_config_rejects_digest_budget_and_scope_drift(self):
        fixture = valid_fixture()
        mutations = (
            ("digest", lambda value: value.__setitem__("allowed_fixture_digest", "0" * 64)),
            ("checkpoint-zero", lambda value: value.__setitem__("checkpoint_after_updates", 0)),
            ("checkpoint-final", lambda value: value.__setitem__("checkpoint_after_updates", 2)),
            ("base-trainable", lambda value: value["trainable_names_by_architecture"]
             ["recipe_arch::B0"].append("bad")),
            ("b1-empty", lambda value: value["trainable_names_by_architecture"]
             .__setitem__("recipe_arch::B1-L", [])),
            ("b2-not-superset", lambda value: value["trainable_names_by_architecture"]
             .__setitem__("recipe_arch::B2-P", ["other"])),
            ("scope-order", lambda value: value["trainable_names_by_architecture"]
             .__setitem__("recipe_arch::B2-P", ["projector_adapter", "language_adapter"])),
        )
        for label, mutate in mutations:
            value = valid_config(fixture)
            mutate(value)
            with self.subTest(label=label), self.assertRaises(ContractViolation):
                lane1_trainer.validate_config(value, fixture)

    def test_caller_cannot_self_approve_an_unreviewed_fixture_digest(self):
        fixture = valid_fixture()
        fixture["fixture_id"] = "unreviewed-fixture"
        config = valid_config(fixture)
        with self.assertRaises(ContractViolation):
            lane1_trainer.validate_config(config, fixture)


class ArmContractTests(unittest.TestCase):
    def test_manifest_resolves_exact_five_arm_order_and_modes(self):
        arms = lane1_trainer.resolve_arms(valid_v2_manifest())
        self.assertEqual(tuple(arm["candidate_id"] for arm in arms), ARM_IDS)
        self.assertEqual(tuple(arm["objective_mode"] for arm in arms), ("base", "task", "dual", "task", "dual"))

    def test_missing_extra_disabled_or_reordered_arm_rejects(self):
        for label, mutate in (
            ("missing", lambda value: value["candidate_universe"].pop()),
            ("extra", lambda value: value["candidate_universe"].append(deepcopy(value["candidate_universe"][-1]))),
            ("disabled", lambda value: value["candidate_universe"][-1].__setitem__("enabled", False)),
            ("reordered", lambda value: value["candidate_universe"].__setitem__(
                slice(1, 3), list(reversed(value["candidate_universe"][1:3])))),
        ):
            value = valid_v2_manifest()
            mutate(value)
            with self.subTest(label=label), self.assertRaises(ContractViolation):
                lane1_trainer.resolve_arms(value)


class RecordingBackend(lane1_synthetic.SyntheticBackend):
    def __init__(self, registry, *, fail_candidate=None):
        super().__init__()
        self.registry = registry
        self.fail_candidate = fail_candidate
        self.calls = []
        registry.append(self)

    def initialize(self, *, base_state, arm, seed):
        self.calls.append(("initialize", bytes(base_state), arm["candidate_id"], seed))
        return super().initialize(base_state=base_state, arm=arm, seed=seed)

    def step(self, row, *, objective_mode, learning_rate):
        self.calls.append(("step", row["independent_unit_id"], objective_mode))
        if self.candidate_id == self.fail_candidate:
            raise RuntimeError("injected update failure")
        return super().step(row, objective_mode=objective_mode, learning_rate=learning_rate)


class MatchedExecutionTests(unittest.TestCase):
    def test_five_arms_share_base_seed_units_and_have_exact_scopes(self):
        instances = []
        result = lane1_trainer.run_lane1(
            valid_v2_manifest(), valid_fixture(), valid_config(),
            backend_factory=lambda: RecordingBackend(instances),
        )
        rows = result["arm_results"]
        self.assertEqual([item["candidate_id"] for item in rows], list(ARM_IDS))
        self.assertEqual([item["status"] for item in rows], ["passed"] * 5)
        self.assertEqual([item["optimizer_updates"] for item in rows], [0, 2, 2, 2, 2])
        self.assertEqual(rows[0]["trainable_parameter_names"], [])
        self.assertEqual(rows[1]["trainable_parameter_names"], ["language_adapter"])
        self.assertEqual(rows[2]["trainable_parameter_names"], ["language_adapter"])
        self.assertEqual(rows[3]["trainable_parameter_names"], ["language_adapter", "projector_adapter"])
        self.assertEqual(rows[4]["trainable_parameter_names"], ["language_adapter", "projector_adapter"])
        self.assertEqual(len({item["ordered_unit_digest"] for item in rows[1:]}), 1)
        initializations = [call for instance in instances for call in instance.calls if call[0] == "initialize"]
        self.assertTrue(initializations)
        self.assertEqual({call[1] for call in initializations}, {lane1_synthetic.BASE_STATE_BYTES})
        self.assertEqual({call[3] for call in initializations}, {17})
        steps = [call for instance in instances for call in instance.calls if call[0] == "step"]
        # Each adapted arm executes one uninterrupted path and one checkpoint/resume replay.
        self.assertEqual([call[2] for call in steps].count("task"), 8)
        self.assertEqual([call[2] for call in steps].count("dual"), 8)

    def test_scope_drift_fails_before_first_update_and_stops_later_arms(self):
        instances = []

        class ScopeDriftBackend(RecordingBackend):
            def trainable_parameter_names(self):
                names = super().trainable_parameter_names()
                return ("unexpected",) if self.candidate_id == B1_TASK else names

        result = lane1_trainer.run_lane1(
            valid_v2_manifest(), valid_fixture(), valid_config(),
            backend_factory=lambda: ScopeDriftBackend(instances),
        )
        self.assertEqual([item["status"] for item in result["arm_results"]],
                         ["passed", "failed", "not_run", "not_run", "not_run"])
        failing = next(instance for instance in instances if instance.candidate_id == B1_TASK)
        self.assertFalse(any(call[0] == "step" for call in failing.calls))

    def test_runtime_failure_retains_exact_five_rows_and_does_not_continue(self):
        instances = []
        result = lane1_trainer.run_lane1(
            valid_v2_manifest(), valid_fixture(), valid_config(),
            backend_factory=lambda: RecordingBackend(instances, fail_candidate=B1_TASK),
        )
        self.assertEqual(len(result["arm_results"]), 5)
        self.assertEqual([item["status"] for item in result["arm_results"]],
                         ["passed", "failed", "not_run", "not_run", "not_run"])
        self.assertEqual(result["arm_results"][1]["failure_stage"], "update")
        self.assertFalse(any(instance.candidate_id in ARM_IDS[2:] for instance in instances))

    def test_digest_mismatch_rejects_before_backend_factory(self):
        calls = []
        config = valid_config()
        config["allowed_fixture_digest"] = "0" * 64
        with self.assertRaises(ContractViolation):
            lane1_trainer.run_lane1(
                valid_v2_manifest(), valid_fixture(), config,
                backend_factory=lambda: calls.append(True),
            )
        self.assertEqual(calls, [])

    def test_dual_updates_obey_manifest_shares(self):
        original = lane1_trainer.run_lane1(valid_v2_manifest(), valid_fixture(), valid_config())
        changed_manifest = valid_v2_manifest()
        dual = next(item for item in changed_manifest["training_contract"]["objective_profiles"]
                    if item["profile_id"] == "profile::dual")
        dual["task_unit_share"] = q(1, 2)
        dual["context_unit_share"] = q(1, 2)
        reseal(changed_manifest)
        changed = lane1_trainer.run_lane1(changed_manifest, valid_fixture(), valid_config())
        original_dual = next(item for item in original["arm_results"] if item["candidate_id"] == B1_DUAL)
        changed_dual = next(item for item in changed["arm_results"] if item["candidate_id"] == B1_DUAL)
        self.assertNotEqual(original_dual["final_state_digest"], changed_dual["final_state_digest"])


class ResumeReloadAndMetricTests(unittest.TestCase):
    def test_resume_reload_and_hand_worked_metrics_are_exact(self):
        instances = []
        result = lane1_trainer.run_lane1(
            valid_v2_manifest(), valid_fixture(), valid_config(),
            backend_factory=lambda: RecordingBackend(instances),
        )
        rows = {item["candidate_id"]: item for item in result["arm_results"]}
        self.assertIsNone(rows[B0]["resume_state_match"])
        self.assertTrue(rows[B0]["reload_prediction_match"])
        for candidate_id in ARM_IDS[1:]:
            self.assertTrue(rows[candidate_id]["resume_state_match"])
            self.assertTrue(rows[candidate_id]["resume_prediction_match"])
            self.assertTrue(rows[candidate_id]["reload_prediction_match"])

        one = q(1)
        zero = q(0)
        two_thirds = q(2, 3)
        minus_eleven_forty_fifths = q(-11, 45)
        self.assertEqual(
            (rows[B0]["task_accuracy"], rows[B0]["context_accuracy"], rows[B0]["score_proxy"]),
            (one, one, zero),
        )
        self.assertEqual(
            (rows[B1_TASK]["task_accuracy"], rows[B1_TASK]["context_accuracy"],
             rows[B1_TASK]["score_proxy"]),
            (two_thirds, one, minus_eleven_forty_fifths),
        )
        for candidate_id in (B1_DUAL, B2_TASK, B2_DUAL):
            self.assertEqual(
                (rows[candidate_id]["task_accuracy"], rows[candidate_id]["context_accuracy"],
                 rows[candidate_id]["score_proxy"]),
                (one, one, zero),
            )

        comparisons = {
            (item["candidate_id"], item["comparator_id"]): item
            for item in result["comparisons"]
        }
        self.assertEqual(comparisons[(B1_TASK, B0)]["task_delta"], q(-1, 3))
        self.assertEqual(comparisons[(B1_TASK, B0)]["context_delta"], zero)
        self.assertEqual(comparisons[(B1_TASK, B0)]["score_proxy_delta"], minus_eleven_forty_fifths)
        self.assertEqual(comparisons[(B1_DUAL, B1_TASK)]["task_delta"], q(1, 3))
        self.assertEqual(comparisons[(B1_DUAL, B1_TASK)]["score_proxy_delta"], q(11, 45))
        self.assertEqual(len(comparisons), 8)
        self.assertFalse(any("selected" in key for key in result))
        canonical.dumps(result)

    def test_corrupt_checkpoint_fails_current_arm_and_closes_population(self):
        instances = []

        class CorruptCheckpointBackend(RecordingBackend):
            def load_state(self, data):
                if self.candidate_id == B1_TASK:
                    data = b"not-json"
                return super().load_state(data)

        result = lane1_trainer.run_lane1(
            valid_v2_manifest(), valid_fixture(), valid_config(),
            backend_factory=lambda: CorruptCheckpointBackend(instances),
        )
        self.assertEqual([item["status"] for item in result["arm_results"]],
                         ["passed", "failed", "not_run", "not_run", "not_run"])
        self.assertEqual(result["arm_results"][1]["failure_stage"], "checkpoint_reload")
        self.assertTrue(all(item["status"] == "unavailable" for item in result["comparisons"]))

    def test_reload_prediction_drift_is_not_reported_as_passed(self):
        instances = []

        class ReloadDriftBackend(RecordingBackend):
            def load_export(self, data):
                super().load_export(data)
                if self.candidate_id == B0:
                    self._state["language_adapter"] += 10

        result = lane1_trainer.run_lane1(
            valid_v2_manifest(), valid_fixture(), valid_config(),
            backend_factory=lambda: ReloadDriftBackend(instances),
        )
        self.assertEqual(result["arm_results"][0]["status"], "failed")
        self.assertEqual(result["arm_results"][0]["failure_stage"], "export_reload_prediction")
        self.assertEqual([item["status"] for item in result["arm_results"][1:]], ["not_run"] * 4)

    def test_resumed_state_drift_is_not_reported_as_passed(self):
        instances = []

        class ResumeDriftBackend(RecordingBackend):
            resumed = False

            def load_state(self, data):
                super().load_state(data)
                self.resumed = True

            def dump_state(self):
                if not self.resumed:
                    return super().dump_state()
                self._state["language_adapter"] += 1
                try:
                    return super().dump_state()
                finally:
                    self._state["language_adapter"] -= 1

        result = lane1_trainer.run_lane1(
            valid_v2_manifest(), valid_fixture(), valid_config(),
            backend_factory=lambda: ResumeDriftBackend(instances),
        )
        self.assertEqual(result["arm_results"][1]["status"], "failed")
        self.assertEqual(result["arm_results"][1]["failure_stage"], "resume_state")

    def test_corrupt_export_is_not_reported_as_passed(self):
        instances = []

        class CorruptExportBackend(RecordingBackend):
            def export(self):
                return b"corrupt" if self.candidate_id == B0 else super().export()

        result = lane1_trainer.run_lane1(
            valid_v2_manifest(), valid_fixture(), valid_config(),
            backend_factory=lambda: CorruptExportBackend(instances),
        )
        self.assertEqual(result["arm_results"][0]["status"], "failed")
        self.assertEqual(result["arm_results"][0]["failure_stage"], "export_reload")


class OfflineBoundaryTests(unittest.TestCase):
    def test_native_runner_attempts_no_files_network_or_model_framework_imports(self):
        attempts = []
        original_import = builtins.__import__

        def guarded_import(name, *args, **kwargs):
            root = name.split(".", 1)[0]
            if root in {"torch", "transformers", "peft", "datasets", "requests", "urllib"}:
                attempts.append(("import", name))
                raise AssertionError(f"forbidden import: {name}")
            return original_import(name, *args, **kwargs)

        def forbidden_file(*args, **kwargs):
            attempts.append(("file", args[0] if args else None))
            raise AssertionError("backend attempted file access")

        def forbidden_socket(*args, **kwargs):
            attempts.append(("socket", args))
            raise AssertionError("backend attempted socket access")

        with mock.patch("builtins.__import__", side_effect=guarded_import), \
             mock.patch("builtins.open", side_effect=forbidden_file), \
             mock.patch.object(io, "open", side_effect=forbidden_file), \
             mock.patch.object(os, "open", side_effect=forbidden_file), \
             mock.patch.object(socket, "socket", side_effect=forbidden_socket):
            result = lane1_trainer.run_lane1(valid_v2_manifest(), valid_fixture(), valid_config())
        self.assertEqual([item["status"] for item in result["arm_results"]], ["passed"] * 5)
        self.assertEqual(attempts, [])

    def test_backend_modules_have_a_standard_library_only_static_dependency_surface(self):
        allowed_roots = {"__future__", "fractions", "typing", "mmbu_phase1"}
        for name in ("lane1_trainer.py", "lane1_synthetic.py"):
            path = Path(__file__).resolve().parents[2] / "src/mmbu_phase1" / name
            tree = ast.parse(path.read_text())
            imports = {
                alias.name.split(".", 1)[0]
                for node in ast.walk(tree) if isinstance(node, ast.Import)
                for alias in node.names
            }
            imports.update(
                (node.module or "").split(".", 1)[0]
                for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)
            )
            self.assertLessEqual(imports, allowed_roots)

    def test_public_star_export_resolves_every_declared_symbol(self):
        namespace = {}
        exec("from mmbu_phase1.lane1_trainer import *", namespace)
        self.assertIs(namespace["ContractViolation"], ContractViolation)


class Lane1CliTests(unittest.TestCase):
    @staticmethod
    def load_cli_module():
        path = Path(__file__).resolve().parents[2] / "tools/lane1_synthetic.py"
        spec = importlib.util.spec_from_file_location("lane1_cli_for_test", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def run_cli(self, root, manifest, fixture, config, output):
        manifest_path = root / "manifest.json"
        fixture_path = root / "fixture.json"
        config_path = root / "config.json"
        manifest_path.write_bytes(canonical.dumps(manifest))
        fixture_path.write_bytes(canonical.dumps(fixture))
        config_path.write_bytes(canonical.dumps(config))
        return subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve().parents[2] / "tools/lane1_synthetic.py"),
                "--manifest", str(manifest_path),
                "--fixture", str(fixture_path),
                "--config", str(config_path),
                "--output", str(output),
            ],
            cwd=Path(__file__).resolve().parents[2],
            capture_output=True,
            text=True,
            check=False,
            env={"PATH": "", "PYTHONDONTWRITEBYTECODE": "1"},
        )

    def test_cli_writes_exact_canonical_line_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "result.json"
            completed = self.run_cli(root, valid_v2_manifest(), valid_fixture(), valid_config(), output)
            self.assertEqual(completed.returncode, 0, completed.stderr)
            raw = output.read_bytes()
            value = canonical.loads(raw)
            self.assertEqual(raw, canonical.dumps(value) + b"\n")
            sentinel = raw
            repeated = self.run_cli(root, valid_v2_manifest(), valid_fixture(), valid_config(), output)
            self.assertNotEqual(repeated.returncode, 0)
            self.assertEqual(output.read_bytes(), sentinel)

    def test_cli_preflight_failure_creates_no_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "result.json"
            fixture = valid_fixture()
            fixture["biomedical_content"] = True
            completed = self.run_cli(root, valid_v2_manifest(), fixture, valid_config(fixture), output)
            self.assertNotEqual(completed.returncode, 0)
            self.assertFalse(output.exists())

    def test_cli_runtime_failure_writes_closed_result_once_and_exits_nonzero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "result.json"
            fixture = valid_fixture()
            fixture["fixture_id"] = "lane1-runtime-failure-v1"
            # Each component is representable, but the B2 projector update multiplies
            # the denominators and fails when serializing its synthetic state.
            fixture["train_rows"][0]["feature"] = q(1, 9007199254740991)
            fixture["train_rows"][1]["feature"] = q(1, 9007199254740991)
            config = valid_config(fixture)
            config["learning_rate"] = q(1, 9007199254740991)
            completed = self.run_cli(root, valid_v2_manifest(), fixture, config, output)
            self.assertEqual(completed.returncode, 1, completed.stderr)
            value = canonical.loads(output.read_bytes())
            self.assertEqual(len(value["arm_results"]), 5)
            self.assertIn("failed", [item["status"] for item in value["arm_results"]])

    def test_atomic_publication_failure_leaves_no_partial_output(self):
        cli = self.load_cli_module()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            output = root / "result.json"
            with mock.patch.object(os, "link", side_effect=OSError("injected publish failure")):
                with self.assertRaises(OSError):
                    cli._publish_exclusive(output, b"complete-bytes")
            self.assertFalse(output.exists())
            self.assertEqual(list(root.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
