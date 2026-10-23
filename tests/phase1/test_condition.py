"""Prompt/schema contract, closed execution condition, and the paired-condition contract."""

import copy
import unittest

from mmbu_phase1 import canonical, condition as conditions, prompt_contract
from mmbu_phase1.fields import ContractViolation

import pipeline_fixture as px

HMAC_VECTOR = {"seed_namespace": "mmbu.phase1a.hmac-vector-171", "parent_seed": 17, "name": "evaluation",
               "seed": 801549976211695900}


def setUpModule():
    px.executed()


def tearDownModule():
    px.cleanup()


class WorldCase(unittest.TestCase):
    def setUp(self):
        self.world, self.execution, _ = px.executed()
        self.condition = self.world.records["execution_condition"]
        self.contract = self.world.records["prompt_schema_contract"]

    def rejects(self, fragment, check, *args, **kwargs):
        with self.assertRaises(ContractViolation) as caught:
            check(*args, **kwargs)
        if fragment:
            self.assertIn(fragment, str(caught.exception))

    def store_with(self, *records):
        store = px.clone_store(self.world)
        for record in records:
            store.add(record)
        return store


class PromptSchemaContractTests(WorldCase):
    def test_prompt_schema_contract_is_digest_bound(self):
        prompt_contract.check_prompt_schema_contract(self.world.store, self.contract["record_digest"])
        self.assertEqual(self.contract["inference_settings_digest"],
                         prompt_contract.inference_settings_digest(self.condition))
        projection = prompt_contract.inference_settings_projection(self.condition)
        self.assertEqual(sorted(projection), ["batching", "cache_network", "call_isolation", "decoding", "failure_retry",
                                              "precision_backend"])
        self.assertNotIn("components", projection)
        for name in ("task_prompt_digest", "parser_digest", "validator_digest", "judge_policy_digest",
                     "requested_context_field_registry_digest"):
            with self.subTest(component=name):
                bad = px.reseal(self.contract, **{name: "0" * 64})
                self.rejects("", prompt_contract.check_prompt_schema_contract, self.store_with(bad), bad["record_digest"])

    def test_contract_local_rules(self):
        source = {"source_id": "brief", "source_role": "brief", "sha256": "a" * 64, "span": "page 3"}
        answer = {"source_id": "answer", "source_role": "organizer_answer", "sha256": "b" * 64, "span": "statement 7"}
        bad = (
            {"task_prompt_digest": self.contract["context_prompt_digest"]},
            {"geometry_threshold": {"denominator": 4, "numerator": 2}},
            {"geometry_threshold": 0.5},
            {"contract_status": "official"},
            {"official_source_digests": [source]},
            {"contract_status": "brief_snapshot"},
            {"contract_status": "brief_snapshot", "official_source_digests": [answer]},
            {"contract_status": "organizer_confirmed", "official_source_digests": [source]},
            {"contract_status": "brief_snapshot", "official_source_digests": [{**source, "source_role": "forum"}]},
            {"contract_status": "brief_snapshot", "official_source_digests": [{**source, "span": ""}]},
            {"schema_version": 2},
            {"extra": True},
        )
        for change in bad:
            with self.subTest(change=sorted(change)):
                self.rejects("", prompt_contract.validate_prompt_schema_contract, px.reseal(self.contract, **change))
        prompt_contract.validate_prompt_schema_contract(
            px.reseal(self.contract, contract_status="brief_snapshot", official_source_digests=[source]))
        prompt_contract.validate_prompt_schema_contract(
            px.reseal(self.contract, contract_status="organizer_confirmed",
                      official_source_digests=sorted([source, answer], key=canonical.dumps)))

    def test_unconfirmed_contract_is_not_official_equivalent(self):
        self.assertFalse(prompt_contract.official_equivalence_allowed(self.contract))
        relabeled = px.reseal(self.contract, contract_status="organizer_confirmed")
        self.rejects("organizer", prompt_contract.validate_prompt_schema_contract, relabeled)

    def test_threshold_projection_drift_rejects(self):
        bad = px.reseal(self.contract, geometry_threshold={"denominator": 3, "numerator": 1})
        self.rejects("validator", prompt_contract.check_prompt_schema_contract, self.store_with(bad), bad["record_digest"])

    def test_successor_must_keep_identity_and_follow(self):
        successor = px.reseal(self.contract, supersedes_digest=self.contract["record_digest"],
                              created_at="2099-01-01T00:00:00.000000Z")
        prompt_contract.check_prompt_schema_contract(self.store_with(successor), successor["record_digest"])
        renamed = px.reseal(successor, contract_id="other-contract")
        self.rejects("identity", prompt_contract.check_prompt_schema_contract, self.store_with(renamed), renamed["record_digest"])


class ConditionObjectTests(WorldCase):
    def objects(self):
        return {name: copy.deepcopy(self.condition[name]) for name in conditions.OBJECT_NAMES}

    def test_valid_condition_is_transitively_complete(self):
        conditions.check_execution_condition(self.world.store, self.condition["record_digest"])

    def test_decoding_cross_field_rules(self):
        decoding = self.condition["decoding"]
        bad = (
            {"temperature": 1.0}, {"do_sample": True}, {"num_beams": 2}, {"max_new_tokens": 0},
            {"repetition_penalty": 0}, {"stop_token_ids": [2, 1]}, {"stop_token_ids": [1, 1]},
            {"decoding_method": "sampling"},
            {"decoding_method": "beam", "num_beams": 1},
            {"decoding_method": "sampling", "do_sample": True, "temperature": 0.7, "top_p": 1.5, "top_k": 0},
            {"cache_enabled": "no"},
        )
        for change in bad:
            with self.subTest(change=sorted(change)):
                self.rejects("", conditions.validate_decoding, {**decoding, **change}, "decoding")
        conditions.validate_decoding({**decoding, "decoding_method": "sampling", "do_sample": True, "temperature": 0.7,
                                      "top_p": 0.9, "top_k": 40}, "decoding")
        conditions.validate_decoding({**decoding, "decoding_method": "beam", "num_beams": 3, "num_return_sequences": 2},
                                     "decoding")

    def test_randomness_derivation_formula_and_graph(self):
        randomness = self.condition["randomness"]
        conditions.validate_randomness(randomness, "randomness")
        self.assertEqual(conditions.derive_seed(HMAC_VECTOR["parent_seed"], HMAC_VECTOR["seed_namespace"],
                                                HMAC_VECTOR["name"]), HMAC_VECTOR["seed"])
        generation = {"name": "generation", "seed": 17, "algorithm": "mt19937", "version": "v", "derivation": "direct",
                      "parent_name": None}
        derived = {"name": "evaluation", "seed": HMAC_VECTOR["seed"], "algorithm": "mt19937", "version": "v",
                   "derivation": "hmac_sha256", "parent_name": "generation"}
        valid = {"seed_namespace": HMAC_VECTOR["seed_namespace"], "streams": [derived, generation]}
        conditions.validate_randomness(valid, "randomness")
        canonical.dumps(valid)
        bad = (
            {"seed_namespace": HMAC_VECTOR["seed_namespace"], "streams": [{**derived, "seed": derived["seed"] + 100}, generation]},
            {"seed_namespace": "other-namespace", "streams": [derived, generation]},
            {"seed_namespace": HMAC_VECTOR["seed_namespace"], "streams": [{**derived, "parent_name": None}, generation]},
            {"seed_namespace": HMAC_VECTOR["seed_namespace"], "streams": [{**derived, "parent_name": "evaluation"}, generation]},
            {"seed_namespace": HMAC_VECTOR["seed_namespace"], "streams": [generation, derived]},
            {"seed_namespace": HMAC_VECTOR["seed_namespace"], "streams": [derived]},
            {"seed_namespace": HMAC_VECTOR["seed_namespace"], "streams": [{**derived, "name": "generation"}, generation]},
            {"seed_namespace": HMAC_VECTOR["seed_namespace"], "streams": [{**generation, "seed": 2 ** 64}]},
            {"seed_namespace": HMAC_VECTOR["seed_namespace"], "streams": [{**generation, "derivation": "random"}]},
        )
        for index, item in enumerate(bad):
            with self.subTest(case=index):
                self.rejects("", conditions.validate_randomness, item, "randomness")
        with self.assertRaises(canonical.CanonicalJSONError):
            canonical.dumps({**generation, "seed": conditions.derive_seed(17, "mmbu.phase1a.synthetic", "evaluation")})

    def test_phase1a_runtime_batching_precision_and_retry_rules(self):
        objects = self.objects()
        mutations = (
            ("runtime", lambda o: o["devices"].append({**o["devices"][0], "device_id": "cpu1"})),
            ("runtime", lambda o: o["topology"].update(world_size=2)),
            ("runtime", lambda o: o["topology"].update(launcher="torchrun")),
            ("runtime", lambda o: o["cache_network"].update(network_denied=False)),
            ("runtime", lambda o: o["cache_network"].update(remote_request_count=1, request_log_digest="0" * 64)),
            ("runtime", lambda o: o["cache_network"].update(request_log_digest=None, hidden_fetch_count=1)),
            ("runtime", lambda o: o["software"].reverse()),
            ("batching", lambda o: o.update(shuffle=True)),
            ("batching", lambda o: o.update(worker_count=2)),
            ("batching", lambda o: o.update(batches=[o["row_order"]])),
            ("batching", lambda o: o.update(batches=list(reversed(o["batches"])))),
            ("batching", lambda o: o.update(truncation=True)),
            ("batching", lambda o: o.update(remainder_policy="error")),
            ("batching", lambda o: o.update(image_order="random")),
            ("precision_backend", lambda o: o.update(parameter_dtype="bfloat16")),
            ("precision_backend", lambda o: o.update(attention_backend="sdpa")),
            ("precision_backend", lambda o: o.update(compile_mode="reduce-overhead")),
            ("precision_backend", lambda o: o.update(cache_backend="dynamic")),
            ("precision_backend", lambda o: o.update(fallbacks=["cpu"])),
            ("failure_retry", lambda o: o.update(retry_mode="same_condition")),
            ("failure_retry", lambda o: o.update(maximum_attempts=2)),
            ("failure_retry", lambda o: o["terminal_rules"].pop()),
            ("failure_retry", lambda o: o["terminal_rules"][0].update(grade_contribution={"denominator": 2, "numerator": 0})),
            ("call_isolation", lambda o: o.update(kv_cache_reuse=True)),
            ("call_isolation", lambda o: o.update(cross_call_allowed_fields=["label"])),
            ("request_set", lambda o: o["rows"][0].update(context_request_digest=None)),
            ("request_set", lambda o: o["rows"][1].update(context_request_digest="0" * 64)),
            ("request_set", lambda o: o["rows"].append(dict(o["rows"][0]))),
            ("processor", lambda o: o.update(processor_digest=None)),
            ("components", lambda o: o.update(geometry_threshold={"denominator": 2, "numerator": 2})),
        )
        for name, mutate in mutations:
            with self.subTest(object=name, mutation=mutate):
                broken = copy.deepcopy(objects)
                mutate(broken[name])
                self.rejects("", conditions.validate_condition_objects, broken, "condition")

    def test_transitive_bindings_reject_projection_drift(self):
        condition = self.condition
        env = condition["runtime"]["environment_variables"]
        cases = {
            "environment_value": {"runtime": {**condition["runtime"], "environment_variables":
                                              [{**env[0], "value": env[0]["value"] + "x"}] + env[1:]}},
            "os": {"runtime": {**condition["runtime"], "os": "linux" if condition["runtime"]["os"] == "darwin" else "darwin"}},
            "locale": {"runtime": {**condition["runtime"], "locale": "en_US.UTF-8"}},
            "python_digest": {"runtime": {**condition["runtime"], "python_executable_digest": "0" * 64}},
            "request_order": {"request_set": {**condition["request_set"],
                                              "rows": [condition["request_set"]["rows"][1], condition["request_set"]["rows"][0]]
                                              + condition["request_set"]["rows"][2:]},
                              "batching": condition["batching"]},
            "parser_component": {"components": {**condition["components"], "parser_digest": condition["components"]["validator_digest"]}},
            "inference_projection": {"decoding": {**condition["decoding"], "max_new_tokens": 100}},
            "template_null": {"processor": {**condition["processor"], "template_digest": None}},
            "image_decoder_null": {"processor": {**condition["processor"], "image_decoder_digest": None}},
            "request_digest": {"request_set": {**condition["request_set"], "rows":
                                               [{**condition["request_set"]["rows"][0], "task_request_digest": "0" * 64}]
                                               + condition["request_set"]["rows"][1:]}},
        }
        for name, change in cases.items():
            with self.subTest(case=name):
                bad = px.reseal(condition, **change)
                self.rejects("", conditions.check_execution_condition, self.store_with(bad), bad["record_digest"])


class PairedConditionTests(WorldCase):
    def setUp(self):
        super().setUp()
        self.pairing = self.world.records["paired_condition_contract"]
        self.base = self.world.records["experiment_base"]
        self.adapted = self.world.records["experiment_adapted"]

    def test_paired_condition_allows_only_closed_model_identity_difference(self):
        conditions.check_paired_condition_contract(self.world.store, self.pairing["record_digest"])
        derived_unions = {"lineage_root_digests", "decision_execution_receipt_digests"}
        differing = {name for name in self.base if self.base[name] != self.adapted[name]
                     and name not in {"record_digest", "experiment_id", "created_at"}}
        self.assertLessEqual(differing - derived_unions, set(conditions.IDENTITY_FIELDS))
        self.assertEqual(set(self.base["non_model_lineage_root_digests"]), set(self.adapted["non_model_lineage_root_digests"]))
        fields = self.pairing["allowed_difference_fields"]
        variants = {
            "widened": sorted(fields + ["execution_condition_digest"]),
            "renamed": [("model_hash" if f == "model_digest" else f) for f in fields],
            "narrowed": fields[1:],
            "reordered": list(reversed(fields)),
        }
        for name, allowed in variants.items():
            with self.subTest(variant=name):
                bad = px.reseal(self.pairing, allowed_difference_fields=allowed)
                self.rejects("allowed_difference_fields", conditions.check_paired_condition_contract,
                             self.store_with(bad), bad["record_digest"])
        leaking = px.reseal(self.pairing, adapted_model_identity={**self.pairing["adapted_model_identity"],
                                                                  "execution_condition_digest": "0" * 64})
        self.rejects("closed object", conditions.check_paired_condition_contract, self.store_with(leaking),
                     leaking["record_digest"])
        no_edge = px.reseal(self.pairing, adapted_model_identity={**self.pairing["adapted_model_identity"],
                                                                  "adapted_from_model_digest": None})
        self.rejects("adapted from the base", conditions.check_paired_condition_contract, self.store_with(no_edge),
                     no_edge["record_digest"])

    def test_paired_condition_rejects_each_non_model_field_drift(self):
        replacements = {
            "purpose": "train",
            "authorization_registry_digest": "0" * 64,
            "source_record_digests": ["0" * 64],
            "purpose_authorization_digests": ["0" * 64],
            "source_manifest_digests": ["0" * 64],
            "split_manifest_digests": ["0" * 64],
            "non_model_lineage_root_digests": self.base["non_model_lineage_root_digests"][:1],
            "non_model_decision_execution_receipt_digests": ["0" * 64],
            "execution_condition_digest": "0" * 64,
            "prospective_lock_digest": "0" * 64,
            "decision_function_digest": "0" * 64,
        }
        self.assertEqual(sorted(replacements), sorted(conditions.MATCHED_FIELDS))
        for name, value in replacements.items():
            for side in ("base", "adapted"):
                with self.subTest(field=name, side=side):
                    experiment_record = self.base if side == "base" else self.adapted
                    drifted = px.reseal(experiment_record, **{name: value})
                    pairing = px.reseal(self.pairing, **{f"{side}_experiment_digest": drifted["record_digest"]})
                    self.rejects("", conditions.check_paired_condition_contract, self.store_with(drifted, pairing),
                                 pairing["record_digest"])
            with self.subTest(field=name, side="contract"):
                bad = px.reseal(self.pairing, matched_conditions={**self.pairing["matched_conditions"], name: value})
                self.rejects("matched_conditions", conditions.check_paired_condition_contract, self.store_with(bad),
                             bad["record_digest"])

    def test_late_or_self_paired_contract_rejects(self):
        same = px.reseal(self.pairing, adapted_experiment_digest=self.pairing["base_experiment_digest"])
        self.rejects("distinct", conditions.check_paired_condition_contract, self.store_with(same), same["record_digest"])
        early = px.reseal(self.pairing, created_at=self.base["created_at"])
        self.rejects("already immutable experiments", conditions.check_paired_condition_contract, self.store_with(early),
                     early["record_digest"])
        manifest = px.reseal(self.pairing, example_manifest_digest="0" * 64)
        self.rejects("example_manifest_digest", conditions.check_paired_condition_contract, self.store_with(manifest),
                     manifest["record_digest"])


if __name__ == "__main__":
    unittest.main()
