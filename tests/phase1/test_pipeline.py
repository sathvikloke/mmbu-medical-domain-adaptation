"""End-to-end synthetic evaluator run: raw immutability, layers, failures, fixture, geometry, task change."""

import copy
import os
from pathlib import Path
import stat
import unittest

from mmbu_phase1 import canonical, condition as conditions, evaluator, experiment, layers, phase1a, summaries, synthetic
from mmbu_phase1.fields import ContractViolation

import pipeline_fixture as px


def setUpModule():
    px.executed()


def tearDownModule():
    px.cleanup()


class PipelineCase(unittest.TestCase):
    def setUp(self):
        self.world, self.execution, _ = px.executed()

    def side(self, side="base"):
        return px.layers_of(self.world, self.execution, side)

    def manifest(self):
        return self.world.records["example_manifest"]

    def chain(self, example, side="base", **replace):
        _, by_example = self.side(side)
        layer = dict(by_example[example])
        layer.update(replace)
        row = next(r for r in self.manifest()["rows"] if r["example_id"] == example)
        experiment_record = self.world.records[f"experiment_{side}"]
        layers.check_layer_chain(layer["raw_output"], layer["parsed_output"], layer["validated_output"],
                                 layer["judged_output"], row, self.manifest(), self.world.records["execution_condition"],
                                 experiment_record, example)


class EndToEndTests(PipelineCase):
    def test_complete_run_verifies_transitively(self):
        phase1a.verify_execution(self.world, self.execution, contract_manifest_digest=px.MANIFEST_SHA256)

    def test_runs_reproducibility_and_launch_are_bound(self):
        receipt = self.world.records["environment_launch_receipt"]
        for side in ("base", "adapted"):
            repro = self.execution.reproducibility[side]
            run = self.execution.runs[side]
            self.assertEqual(repro["environment_launch_receipt_digest"], receipt["record_digest"])
            self.assertEqual(run["reproducibility_record_digest"], repro["record_digest"])
            self.assertEqual(run["consumed_experiment_digest"], run["experiment_digest"])
            self.assertEqual(run["source_state_digest"], px.SOURCE_STATE)
        self.assertEqual(self.execution.observation["loaded_module_violations"], [])
        self.assertTrue(self.execution.observation["network_probe"]["denied"])

    def test_reproducibility_rejects_unbound_or_forged_child_capture(self):
        store = px.clone_store(self.world)
        forged_capture = store.add_artifact(canonical.dumps({
            "captured_at": self.world.records["environment_launch_receipt"]["child_captured_at"],
            "environment": [],
            "phase1_modules_loaded_before_capture": ["mmbu_phase1"],
        }))
        original = self.execution.reproducibility["base"]
        forged = px.reseal(original, environment_artifact_digests=[forged_capture])
        store.add(forged)

        with self.assertRaises(ContractViolation):
            experiment.check_reproducibility(
                store,
                forged["record_digest"],
                contract_manifest_digest=px.MANIFEST_SHA256,
                exposure=self.execution.observation["exposure"]["base"],
                rng_state_digests={"generation": self.world.files["runs/launch/rng-state-generation.json"]},
            )


class RawOutputTests(PipelineCase):
    def test_raw_output_is_immutable(self):
        output, by_example = self.side()
        for entry in output["entries"]:
            if entry["role"] != "raw_output":
                continue
            target = self.world.root / entry["path"]
            self.assertEqual(Path(entry["path"]).stem, entry["sha256"], "raw records are content-addressed")
            self.assertEqual(stat.S_IMODE(os.lstat(target).st_mode), 0o444)
            with self.assertRaises(PermissionError):
                with open(target, "r+b"):
                    pass
            with self.assertRaises(FileExistsError):
                from mmbu_phase1.phase1a_child import write_immutable
                write_immutable(self.world.root, entry["path"], b"{}")
            raw = by_example[entry["example_id"]]["raw_output"]
            for name in ("request_digest", "token_ids", "decoded_text", "finish_reason", "effective_generation_settings",
                         "timing", "runtime_status"):
                self.assertIn(name, raw)

    def test_mutated_raw_bytes_or_record_are_detected(self):
        output, by_example = self.side()
        entry = next(e for e in output["entries"] if e["role"] == "raw_output")
        original = self.world.read(entry["path"])
        tampered = original.replace(b'"runtime_status":"', b'"runtime_status":"x', 1)
        reader = lambda p: tampered if p == entry["path"] else self.world.read(p)  # noqa: E731
        with self.assertRaises(ContractViolation):
            layers.check_execution_output_manifest(self.world.store, output["record_digest"], reader)
        raw = by_example[entry["example_id"]]["raw_output"]
        resealed = px.reseal(raw, decoded_text=(raw["decoded_text"] or "") + " ")
        resealed_bytes = canonical.dumps(resealed)
        reader = lambda p: resealed_bytes if p == entry["path"] else self.world.read(p)  # noqa: E731
        with self.assertRaises(ContractViolation):
            layers.check_execution_output_manifest(self.world.store, output["record_digest"], reader)

    def test_downstream_fields_cannot_enter_raw(self):
        _, by_example = self.side()
        raw = by_example["cls-01"]["raw_output"]
        for leak in ({"parse_status": "parsed"}, {"task_grade": 1}, {"parsed_value": {}}):
            with self.subTest(leak=sorted(leak)):
                with self.assertRaises(ContractViolation):
                    layers.validate_raw_output(px.reseal(raw, **leak))

    def test_raw_is_written_before_parsing(self):
        _, by_example = self.side()
        for example, layer in by_example.items():
            raw, parsed = layer["raw_output"], layer["parsed_output"]
            self.assertEqual(parsed["raw_digest"], raw["record_digest"])
            self.assertLessEqual(raw["timing"]["ended_at"], raw["created_at"])
            self.assertLessEqual(raw["created_at"], parsed["created_at"])

    def test_runner_rejects_effective_decoding_drift(self):
        _, by_example = self.side()
        raw = by_example["cls-01"]["raw_output"]
        drifted = px.reseal(raw, effective_generation_settings={**raw["effective_generation_settings"], "max_new_tokens": 255})
        with self.assertRaises(ContractViolation):
            self.chain("cls-01", raw_output=drifted)


class LayerTests(PipelineCase):
    def test_parse_statuses_cover_strict_failures_without_repair(self):
        _, by_example = self.side()
        expected = {"cls-03": "invalid_json", "cls-04": "duplicate_key", "cls-05": "unknown_key",
                    "cls-06": "multiple_objects", "cls-07": "missing_required", "cnt-02": "nonfinite",
                    "det-06": "invalid_json", "cls-01": "parsed"}
        for example, status in expected.items():
            with self.subTest(example=example):
                parsed = by_example[example]["parsed_output"]
                self.assertEqual(parsed["parse_status"], status)
                if status != "parsed":
                    self.assertIsNone(parsed["parsed_value"])
                    self.assertEqual(by_example[example]["validated_output"]["validation_status"], "not_run")
                    self.assertEqual(by_example[example]["judged_output"]["terminal_outcome"], "parse_failure")

    def test_parser_never_extracts_or_repairs(self):
        row = next(r for r in self.manifest()["rows"] if r["example_id"] == "cls-03")
        for text, status in (('Answer: {"label":"alpha"}', "invalid_json"), ('{"label":"alpha"} trailing', "invalid_json"),
                             ('["alpha"]', "invalid_json"), ('{"label":"alpha","label":"beta"}', "duplicate_key"),
                             ('{"label":1e999}', "nonfinite"), ('{"label":0.1000000000000000055511151231257827}', "invalid_json")):
            with self.subTest(text=text):
                raw = {"runtime_status": "succeeded", **evaluator.transcript(synthetic.ok(text),
                                                                             synthetic.ok({"syn_view": "x"}))}
                self.assertEqual(evaluator.parse(raw, row), (status, None))

    def test_parsed_validated_and_judged_layers_bind_parent_hash(self):
        output, by_example = self.side()
        for example in by_example:
            self.chain(example)
        layer = by_example["cls-01"]
        changed_raw = px.reseal(layer["raw_output"], created_at=layer["raw_output"]["created_at"])
        changed_raw = px.reseal(changed_raw, finish_reason="length+stop")
        with self.assertRaises(ContractViolation):
            self.chain("cls-01", raw_output=changed_raw)
        changed_parsed = px.reseal(layer["parsed_output"], parsed_value={"context": None, "task": {"label": "alpha"}})
        with self.assertRaises(ContractViolation):
            self.chain("cls-01", parsed_output=changed_parsed)
        changed_validated = px.reseal(layer["validated_output"], validated_value=layer["validated_output"]["validated_value"])
        changed_validated = px.reseal(changed_validated, record_id="other-record")
        with self.assertRaises(ContractViolation):
            self.chain("cls-01", validated_output=changed_validated)

    def test_validation_cannot_rewrite_its_parent(self):
        _, by_example = self.side()
        layer = by_example["cls-01"]
        rewritten = px.reseal(layer["validated_output"], validated_value={"context": layer["parsed_output"]["parsed_value"]["context"],
                                                                         "task": {"label": "alpha"}})
        judged = px.reseal(layer["judged_output"], validated_digest=rewritten["record_digest"])
        with self.assertRaises(ContractViolation):
            self.chain("cls-01", validated_output=rewritten, judged_output=judged)


class FailureStateTests(PipelineCase):
    def test_runtime_failure_layer_state_is_legal(self):
        cases = (("base", "cls-09", "load_failed"), ("base", "cnt-04", "timeout"), ("adapted", "cnt-04", "oom"),
                 ("base", "cnt-05", "preprocess_failed"), ("adapted", "cls-10", "generation_failed"),
                 ("base", "det-05", "oom"))
        for side, example, status in cases:
            with self.subTest(side=side, example=example):
                layer = self.side(side)[1][example]
                self.assertEqual(layer["raw_output"]["runtime_status"], status)
                self.assertEqual(layer["parsed_output"]["parse_status"], "not_run")
                self.assertEqual(layer["validated_output"]["validation_status"], "not_run")
                self.assertEqual(layer["validated_output"]["geometry_status"], "not_run")
                self.assertEqual(layer["judged_output"]["judge_status"], "not_run")
                self.assertEqual(layer["judged_output"]["terminal_outcome"], "runtime_failure")
        partial = self.side("base")[1]["cnt-04"]["raw_output"]
        self.assertIsNotNone(partial["token_ids"])
        self.assertEqual(partial["finish_reason"], "task=none;context=stop")
        self.assertIsNone(self.side("base")[1]["det-05"]["raw_output"]["finish_reason"])
        empty = self.side("base")[1]["cls-09"]["raw_output"]
        self.assertIsNone(empty["token_ids"])
        self.assertIsNone(empty["decoded_text"])

    def test_failure_stages_remain_orthogonal(self):
        base = self.side("base")[1]
        self.assertEqual(base["cls-08"]["validated_output"]["validation_status"], "invalid_value")
        self.assertEqual(base["cls-08"]["judged_output"]["judge_status"], "not_run")
        self.assertEqual(base["cnt-03"]["validated_output"]["validation_status"], "invalid_schema")
        judge_failure = base["det-09"]
        self.assertEqual(judge_failure["validated_output"]["validation_status"], "valid")
        self.assertEqual(judge_failure["judged_output"]["judge_status"], "judge_failed")
        self.assertEqual(judge_failure["judged_output"]["terminal_outcome"], "judge_failure")
        layer = base["cls-09"]
        impossible = px.reseal(layer["parsed_output"], parse_status="parsed", parsed_value={"context": None, "task": {"label": ""}})
        with self.assertRaises(ContractViolation):
            self.chain("cls-09", parsed_output=impossible)
        fabricated = px.reseal(layer["raw_output"], decoded_text="", token_ids=[])
        with self.assertRaises(ContractViolation):
            self.chain("cls-09", raw_output=fabricated)

    def test_failures_remain_in_denominator(self):
        ids = [row["example_id"] for row in self.manifest()["rows"]]
        for side in ("base", "adapted"):
            output, by_example = self.side(side)
            self.assertEqual(sorted(by_example), sorted(ids))
            for role in ("raw_output", "parsed_output", "validated_output", "judged_output"):
                self.assertEqual(sorted(e["example_id"] for e in output["entries"] if e["role"] == role), sorted(ids))
        totals = self.execution.task_change["totals"]
        self.assertEqual(totals["example_count"], len(ids))
        self.assertEqual(self.execution.task_change["binary_summary"]["N"], len(ids))

    def test_incomplete_extra_or_opaque_output_populations_reject(self):
        output, _ = self.side()
        store = px.clone_store(self.world)
        judged = [e for e in output["entries"] if e["role"] == "judged_output"]
        variants = {
            "missing_judged_row": [e for e in output["entries"] if e is not judged[0]],
            "duplicate_layer_role": sorted(output["entries"] + [{**judged[0], "path": "runs/base/judged/duplicate.json"}],
                                           key=lambda e: e["path"].encode()),
            "opaque_entry": sorted(output["entries"] + [{"path": "runs/base/opaque.bin", "bytes": 3, "sha256": "0" * 64,
                                                          "media_type": "application/octet-stream", "schema_id": None,
                                                          "schema_version": None, "record_digest": None, "role": "log",
                                                          "example_id": None}], key=lambda e: e["path"].encode()),
            "self_inclusion": sorted(output["entries"] + [{"path": "runs/base/output-manifest.json", "bytes": 1,
                                                            "sha256": "1" * 64, "media_type": "application/json",
                                                            "schema_id": "mmbu.phase1.execution_output_manifest",
                                                            "schema_version": 1, "record_digest": "2" * 64,
                                                            "role": "failure", "example_id": None}],
                                     key=lambda e: e["path"].encode()),
        }
        for name, entries in variants.items():
            with self.subTest(variant=name):
                bad = px.reseal(output, entries=entries)
                store.add(bad)
                reader = lambda p: self.world.read(p) if p != "runs/base/judged/duplicate.json" else self.world.read(judged[0]["path"])  # noqa: E731
                with self.assertRaises(ContractViolation):
                    layers.check_execution_output_manifest(store, bad["record_digest"], reader)

    def test_geometry_judge_failure_preserves_validated_result(self):
        for side in ("base", "adapted"):
            row = next(r for r in self.execution.geometry[side]["rows"] if r["example_id"] == "det-09")
            self.assertEqual(row["reason_code"], "passed")
            self.assertEqual(row["row_iou"], {"denominator": 1, "numerator": 1})


class FixtureTests(PipelineCase):
    def test_fixture_covers_required_cases_with_deliberate_negatives(self):
        covers = {tag for case in synthetic.CASES for tag in case.covers}
        for required in ("classification", "counting", "one_box", "multiple_boxes", "dynamic_context_subset",
                         "inapplicable_context", "malformed_output", "runtime_failure", "judge_failure"):
            self.assertIn(required, covers)
        rows = {row["example_id"]: row for row in self.execution.task_change["rows"]}
        family = {case.example_id: case.family for case in synthetic.CASES}
        for kind in ("classification", "counting", "detection"):
            members = [r for k, r in rows.items() if family[k] == kind]
            self.assertTrue(any(r["state"] == "negative" or r["base_terminal_outcome"] != "success" for r in members), kind)
            self.assertTrue(any(r["base_terminal_outcome"] == "success" for r in members), kind)
        base = self.side("base")[1]
        adapted = self.side("adapted")[1]
        self.assertEqual(adapted["cls-01"]["judged_output"]["context_grades"], {"syn_modality": 1, "syn_stain": 0})
        self.assertEqual(base["cls-01"]["judged_output"]["context_grades"], {"syn_modality": 1, "syn_stain": 1})

    def test_task_scoring_works_with_no_applicable_context(self):
        judged = self.side("base")[1]["cls-02"]["judged_output"]
        self.assertEqual(judged["terminal_outcome"], "success")
        self.assertEqual(judged["task_grade"], 1)
        self.assertEqual(judged["context_grades"], {})

    def test_context_schema_uses_requested_field_subset(self):
        sizes = {len(row["requested_context_fields"]) for row in self.manifest()["rows"]}
        self.assertTrue({0, 1, 2, 3} <= sizes)
        cnt = next(r for r in self.manifest()["rows"] if r["example_id"] == "cnt-01")
        self.assertEqual(cnt["requested_context_fields"], ["syn_region", "syn_modality"])
        row = next(r for r in self.manifest()["rows"] if r["example_id"] == "cls-01")
        raw = {"runtime_status": "succeeded", **evaluator.transcript(
            synthetic.ok({"label": "alpha"}), synthetic.ok({"syn_modality": "a", "syn_stain": "b", "syn_view": "c"}))}
        self.assertEqual(evaluator.parse(raw, row), ("unknown_key", None))
        raw = {"runtime_status": "succeeded", **evaluator.transcript(synthetic.ok({"label": "alpha"}),
                                                                     synthetic.ok({"syn_modality": "a"}))}
        self.assertEqual(evaluator.parse(raw, row), ("missing_required", None))

    def test_task_context_calls_are_stateless(self):
        sentinels = [synthetic.TASK_SENTINEL, synthetic.CONTEXT_SENTINEL]
        for relative in self.world.files:
            if relative.startswith("artifacts/requests/"):
                data = self.world.read(relative)
                for sentinel in sentinels:
                    self.assertNotIn(sentinel.encode(), data, relative)
                for target in ("alpha", "beta", "gamma"):
                    if b'"call":"task"' in data:
                        self.assertNotIn(f'"{target}"'.encode(), data)
        isolation = self.world.records["execution_condition"]["call_isolation"]
        self.assertFalse(isolation["task_receives_context_output"] or isolation["context_receives_task_output"])
        self.assertEqual(self.execution.observation["observed_condition"]["call_isolation"], isolation)
        table = canonical.loads(self.world.read("artifacts/models/synthetic-base.json"))
        request = self.world.read("artifacts/requests/cls-01.context.json")
        self.assertEqual(synthetic.respond(table, request), synthetic.respond(table, request))

    def test_fixture_is_synthetic_and_frozen_after_opening(self):
        contract = self.world.records["prompt_schema_contract"]
        self.assertEqual(contract["contract_status"], "synthetic")
        self.assertEqual(contract["official_source_digests"], [])
        for name, record in self.world.records.items():
            if record["schema_id"] == "mmbu.phase1.lineage_receipt":
                self.assertEqual(record["origin_class"], "synthetic_engineering", name)
        store = px.clone_store(self.world)
        manifest = self.manifest()
        rows = copy.deepcopy(manifest["rows"])
        rows[0]["task_weight"] = 3
        changed = px.reseal(manifest, rows=rows)
        store.add(changed)
        condition = self.world.records["execution_condition"]
        moved = px.reseal(condition, request_set={**condition["request_set"], "example_manifest_digest": changed["record_digest"]})
        store.add(moved)
        experiment_record = px.reseal(self.world.records["experiment_adapted"], execution_condition_digest=moved["record_digest"])
        store.add(experiment_record)
        pairing = px.reseal(self.world.records["paired_condition_contract"],
                            adapted_experiment_digest=experiment_record["record_digest"])
        store.add(pairing)
        with self.assertRaises(ContractViolation):
            conditions.check_paired_condition_contract(store, pairing["record_digest"])


class GeometryEndToEndTests(PipelineCase):
    EXPECTED = {
        "det-01": ("passed", [(0, 0, 1, 1)]), "det-02": ("below_threshold", [(0, 0, 1, 3)]),
        "det-03": ("below_threshold", [(0, 0, 0, 1)]), "det-04": ("passed", [(0, 0, 1, 1)]),
        "det-05": ("runtime_failure", None), "det-06": ("parse_failure", None), "det-07": ("validation_failure", None),
        "det-08": ("validation_failure", None), "det-09": ("passed", [(0, 0, 1, 1)]),
        "det-10": ("invalid_prediction_box", None), "det-11": ("passed", [(0, 1, 1, 1)]),
        "det-12": ("prediction_count_mismatch", None), "det-13": ("passed", [(0, 1, 1, 1), (1, 0, 1, 1)]),
        "det-14": ("prediction_count_mismatch", None), "det-15": ("passed", [(0, 0, 1, 1), (1, 1, 1, 1)]),
        "det-16": ("invalid_prediction_box", None), "det-17": ("invalid_prediction_box", None),
        "det-18": ("invalid_prediction_box", None), "det-19": ("below_threshold", [(0, 0, 0, 1)]),
        "det-20": ("prediction_count_mismatch", None),
    }

    def test_normative_geometry_cases_trace_end_to_end(self):
        rows = {row["example_id"]: row for row in self.execution.geometry["base"]["rows"]}
        self.assertEqual(list(rows), list(self.EXPECTED))
        for example, (reason, pairs) in self.EXPECTED.items():
            with self.subTest(example=example):
                row = rows[example]
                self.assertEqual(row["reason_code"], reason)
                got = None if row["matched_pairs"] is None else [
                    (p["prediction_index"], p["target_index"], p["iou"]["numerator"], p["iou"]["denominator"])
                    for p in row["matched_pairs"]]
                self.assertEqual(got, pairs)
        self.assertIsNone(rows["det-07"]["predicted_boxes_digest"])
        self.assertTrue(rows["det-08"]["boxes_valid"])
        self.assertEqual(rows["det-08"]["prediction_count"], 1)
        self.assertEqual(rows["det-20"]["prediction_count"], 0)

    def test_tampered_geometry_summary_rejects(self):
        record = self.execution.geometry["base"]
        store = px.clone_store(self.world)
        condition = self.world.records["execution_condition"]
        mutations = (
            lambda rows: rows[0].update(reason_code="below_threshold", passed=False),
            lambda rows: rows[12].update(matched_pairs=list(reversed(rows[12]["matched_pairs"]))),
            lambda rows: rows[1].update(row_iou={"denominator": 6, "numerator": 2}),
            lambda rows: rows[11].update(matched_pairs=[]),
            lambda rows: rows[8].update(reason_code="judge_failure"),
            lambda rows: rows.pop(3),
            lambda rows: rows[0].update(predicted_boxes_digest="0" * 64),
        )
        for index, mutate in enumerate(mutations):
            with self.subTest(case=index):
                rows = copy.deepcopy(record["rows"])
                mutate(rows)
                bad = px.reseal(record, rows=rows)
                store.add(bad)
                with self.assertRaises(ContractViolation):
                    summaries.check_geometry_summary(store, bad["record_digest"], self.world.read, condition=condition)

    def test_prompt_geometry_threshold_matches_condition_evaluator_validator_and_summary(self):
        condition = self.world.records["execution_condition"]
        threshold = condition["components"]["geometry_threshold"]
        self.assertEqual(threshold, {"denominator": 2, "numerator": 1})
        self.assertEqual(self.world.records["prompt_schema_contract"]["geometry_threshold"], threshold)
        for spec in ("validator", "evaluator"):
            self.assertEqual(canonical.loads(self.world.read(f"artifacts/specs/{spec}.json"))["geometry_threshold"], threshold)
        for side in ("base", "adapted"):
            self.assertEqual(self.execution.geometry[side]["threshold"], threshold)
        store = px.clone_store(self.world)
        bad = px.reseal(self.execution.geometry["base"], threshold={"denominator": 3, "numerator": 1})
        store.add(bad)
        with self.assertRaises(ContractViolation):
            summaries.check_geometry_summary(store, bad["record_digest"], self.world.read, condition=condition)
        drifted = px.reseal(condition, components={**condition["components"], "geometry_threshold": {"denominator": 3, "numerator": 2}})
        store.add(drifted)
        with self.assertRaises(ContractViolation):
            conditions.check_execution_condition(store, drifted["record_digest"])


class TaskChangeEndToEndTests(PipelineCase):
    def run_check(self, store, digest, read, path):
        observation = self.execution.observation
        side = "base" if digest == self.execution.runs["base"]["record_digest"] else "adapted"
        return experiment.check_run(store, digest, read, path, contract_manifest_digest=px.MANIFEST_SHA256,
                                    exposure=observation["exposure"][side],
                                    rng_state_digests={"generation": self.world.files["runs/launch/rng-state-generation.json"]})

    def test_continuous_task_change_summary_recomputes(self):
        summaries.check_task_change_summary(self.world.store, self.execution.task_change["record_digest"], self.world.read,
                                            run_check=self.run_check)
        totals = self.execution.task_change["totals"]
        self.assertEqual(totals["example_count"], 36)
        self.assertEqual(self.execution.task_change["binary_summary"]["N"], 36)

    def test_tampered_or_late_task_change_rejects(self):
        record = self.execution.task_change
        store = px.clone_store(self.world)
        totals = copy.deepcopy(record["totals"])
        totals["weight_sum"] = {"denominator": 1, "numerator": 36}
        cases = {
            "wrong_denominator": px.reseal(record, totals=totals),
            "dropped_row": px.reseal(record, rows=record["rows"][1:]),
            "binary_without_rule_change": px.reseal(record, binary_summary=None),
            "wrong_judge": px.reseal(record, judge_policy_digest="0" * 64),
            "swapped_runs": px.reseal(record, base_run_digest=record["adapted_run_digest"],
                                      adapted_run_digest=record["base_run_digest"]),
        }
        for name, bad in cases.items():
            with self.subTest(case=name):
                store.add(bad)
                with self.assertRaises(ContractViolation):
                    summaries.check_task_change_summary(store, bad["record_digest"], self.world.read, run_check=self.run_check)
        pairing = self.world.records["paired_condition_contract"]
        late = px.reseal(pairing, created_at="2099-01-01T00:00:00.000000Z")
        store.add(late)
        bad = px.reseal(record, pairing_contract_digest=late["record_digest"])
        store.add(bad)
        with self.assertRaises(ContractViolation) as caught:
            summaries.check_task_change_summary(store, bad["record_digest"], self.world.read, run_check=self.run_check)
        self.assertIn("late contract", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
