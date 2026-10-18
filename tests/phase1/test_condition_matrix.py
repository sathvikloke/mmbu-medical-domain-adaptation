"""Normative one-field execution-condition mutation matrix (EVALUATOR_MECHANICS.md).

Start from one valid canonical condition.  Mutate exactly one leaf in only one
side (the adapted experiment's prospective condition) or in its observed
evidence (the adapted reproducibility record) by deletion, unknown-field
insertion, wrong JSON type, illegal null, invalid enum/range or unequal valid
value, alternate array order, or duplicate member.  Every local record digest
is recomputed, so each rejection is semantic rather than stale hashing.
"""

import copy
import unittest

from mmbu_phase1 import canonical, condition as conditions, experiment, layers, synthetic
from mmbu_phase1.fields import ContractViolation

import pipeline_fixture as px

SMALL = [c for c in synthetic.CASES if c.example_id in {"cls-01", "cnt-01", "det-13"}]


def leaves(value, path=()):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from leaves(item, path + (key,))
        if not value:
            yield path, value
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from leaves(item, path + (index,))
        if not value:
            yield path, value
    else:
        yield path, value


def containers(value, path=()):
    if isinstance(value, (dict, list)):
        yield path, value
        items = value.items() if isinstance(value, dict) else enumerate(value)
        for key, item in items:
            yield from containers(item, path + (key,))


def get(value, path):
    for key in path:
        value = value[key]
    return value


def other_value(value, label):
    if value is None:
        return "non-null-" + label
    if type(value) is bool:
        return not value
    if type(value) is int:
        return value + 1
    if type(value) is float:
        return value + 0.5
    if isinstance(value, str):
        if len(value) == 64 and all(c in "0123456789abcdef" for c in value):
            return canonical.raw_digest(("mutated:" + label).encode())
        return value + "-mutated"
    return None


def wrong_type(value):
    if isinstance(value, str):
        return 12345
    if type(value) in (int, float, bool):
        return "12345"
    if value is None:
        return 7
    if isinstance(value, list):
        return {"not": "a list"}
    return ["not", "an", "object"]


def mutations(objects):
    """Yield (label, mutated objects) for every applicable one-leaf mutation."""
    for path, value in list(leaves(objects)):
        label = "/".join(map(str, path))
        parent_path, key = path[:-1], path[-1] if path else None
        if path and isinstance(get(objects, parent_path), dict):
            mutated = copy.deepcopy(objects)
            del get(mutated, parent_path)[key]
            yield f"delete:{label}", mutated
        if path and isinstance(get(objects, parent_path), list) and len(get(objects, parent_path)) > 0:
            mutated = copy.deepcopy(objects)
            del get(mutated, parent_path)[key]
            yield f"remove_member:{label}", mutated
        if not path:
            continue
        mutated = copy.deepcopy(objects)
        get(mutated, parent_path)[key] = wrong_type(value)
        yield f"wrong_type:{label}", mutated
        if value is not None:
            mutated = copy.deepcopy(objects)
            get(mutated, parent_path)[key] = None
            yield f"illegal_null:{label}", mutated
        alternative = other_value(value, label)
        if alternative is not None and not isinstance(value, (dict, list)):
            mutated = copy.deepcopy(objects)
            get(mutated, parent_path)[key] = alternative
            yield f"unequal_value:{label}", mutated
    for path, value in list(containers(objects)):
        label = "/".join(map(str, path)) or "<top>"
        if isinstance(value, dict) and path:
            mutated = copy.deepcopy(objects)
            get(mutated, path)["unexpected_member"] = "x"
            yield f"unknown_field:{label}", mutated
        if isinstance(value, list) and len(value) >= 2:
            mutated = copy.deepcopy(objects)
            get(mutated, path).reverse()
            if mutated != objects:
                yield f"alternate_order:{label}", mutated
        if isinstance(value, list) and value:
            mutated = copy.deepcopy(objects)
            get(mutated, path).append(copy.deepcopy(value[0]))
            yield f"duplicate_member:{label}", mutated


class MutationMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.world, cls.execution, _ = px.executed(cases=SMALL)
        cls.condition = cls.world.records["execution_condition"]
        cls.objects = {name: copy.deepcopy(cls.condition[name]) for name in conditions.OBJECT_NAMES}
        cls.rng = {"generation": cls.world.files["runs/launch/rng-state-generation.json"]}

    @classmethod
    def tearDownClass(cls):
        px.cleanup()

    def prospective_rejects(self, mutated_condition):
        """Bind the mutated condition to the adapted experiment and the pairing contract."""
        store = px.clone_store(self.world)
        try:
            sealed = canonical.seal(mutated_condition)
            store.add(sealed)
            adapted = px.reseal(self.world.records["experiment_adapted"], execution_condition_digest=sealed["record_digest"])
            store.add(adapted)
            pairing = px.reseal(self.world.records["paired_condition_contract"],
                                adapted_experiment_digest=adapted["record_digest"])
            store.add(pairing)
            conditions.check_paired_condition_contract(store, pairing["record_digest"])
        except (ContractViolation, canonical.CanonicalJSONError):
            return True
        return False

    def observed_rejects(self, observed):
        store = px.clone_store(self.world)
        try:
            repro = px.reseal(self.execution.reproducibility["adapted"], observed_condition=observed)
            store.add(repro)
            run = px.reseal(self.execution.runs["adapted"], reproducibility_record_digest=repro["record_digest"])
            store.add(run)
            experiment.check_run(store, run["record_digest"], self.world.read, contract_manifest_digest=px.MANIFEST_SHA256,
                                 exposure=self.execution.observation["exposure"]["adapted"], rng_state_digests=self.rng)
        except (ContractViolation, canonical.CanonicalJSONError):
            return True
        return False

    def test_valid_starting_point_passes_both_placements(self):
        self.assertFalse(self.prospective_rejects(self.condition))
        self.assertFalse(self.observed_rejects(self.execution.reproducibility["adapted"]["observed_condition"]))

    def test_execution_condition_rejects_each_leaf_mutation(self):
        accepted = []
        count = 0
        for label, mutated in mutations(self.objects):
            count += 1
            condition = {**copy.deepcopy(self.condition), **mutated}
            if not self.prospective_rejects(condition):
                accepted.append("prospective " + label)
            if not self.observed_rejects(mutated):
                accepted.append("observed " + label)
        self.assertGreater(count, 300)
        self.assertEqual(accepted, [])

    def test_top_level_condition_members_reject(self):
        base = self.condition
        cases = {
            "schema_id": {**base, "schema_id": "mmbu.phase1.execution_condition_v2"},
            "schema_version": {**base, "schema_version": 2},
            "condition_id": {**base, "condition_id": ""},
            "created_at": {**base, "created_at": "2026-10-16 00:00:00"},
            "late_creation": {**base, "created_at": "2099-01-01T00:00:00.000000Z"},
            "policy_digest": {**base, "environment_launch_policy_digest": "0" * 64},
            "unknown_member": {**base, "unexpected_member": True},
            "missing_member": {k: v for k, v in base.items() if k != "batching"},
        }
        for name, record in cases.items():
            with self.subTest(case=name):
                self.assertTrue(self.prospective_rejects(record), name)
        stale = {**base, "condition_id": "renamed"}
        store = px.clone_store(self.world)
        with self.assertRaises(ContractViolation):
            store.add(stale)

    def test_execution_condition_matches_raw_run_and_reproducibility(self):
        output, by_example = px.layers_of(self.world, self.execution, "adapted")
        row = self.world.records["example_manifest"]["rows"][0]
        layer = by_example[row["example_id"]]
        other = canonical.raw_digest(b"other-condition")
        for name, value in (("execution_condition_digest", other), ("request_digest", other),
                            ("evaluator_digest", other), ("judge_policy_digest", other),
                            ("effective_generation_settings", {**layer["raw_output"]["effective_generation_settings"],
                                                               "repetition_penalty": 1.1})):
            with self.subTest(raw=name):
                raw = px.reseal(layer["raw_output"], **{name: value})
                with self.assertRaises(ContractViolation):
                    layers.check_layer_chain(raw, layer["parsed_output"], layer["validated_output"], layer["judged_output"],
                                             row, self.world.records["example_manifest"], self.condition,
                                             self.world.records["experiment_adapted"], "x")
        repro = self.execution.reproducibility["adapted"]
        projections = {
            "execution_condition_digest": other,
            "environment_launch_policy_digest": other,
            "locale": "POSIX",
            "timezone": "Europe/Paris",
            "filesystem": "tmpfs",
            "environment_variables": repro["environment_variables"][1:],
            "hardware": {**repro["hardware"], "cpu_model": "other-cpu"},
            "frameworks": {**repro["frameworks"], "python_version": "0.0.0"},
            "effective_numeric_settings": {**repro["effective_numeric_settings"], "compile_mode": "max-autotune"},
            "distributed_settings": {**repro["distributed_settings"], "accumulation_steps": 2},
            "worker_sampler_order": {**repro["worker_sampler_order"], "sampler_epoch": 1},
            "seed_namespaces": [{**repro["seed_namespaces"][0], "seed": 18}],
            "cache_network_policy": {**repro["cache_network_policy"], "network_denied": False},
            "command": repro["command"] + ["--extra"],
            "working_directory": "/",
        }
        for name, value in projections.items():
            with self.subTest(reproducibility=name):
                store = px.clone_store(self.world)
                changes = {name: value}
                if name == "command":
                    changes["command_digest"] = canonical.value_digest(value)
                bad = px.reseal(repro, **changes)
                store.add(bad)
                run = px.reseal(self.execution.runs["adapted"], reproducibility_record_digest=bad["record_digest"],
                                **({"command_digest": changes["command_digest"]} if "command_digest" in changes else {}))
                store.add(run)
                with self.assertRaises(ContractViolation):
                    experiment.check_run(store, run["record_digest"], self.world.read,
                                         contract_manifest_digest=px.MANIFEST_SHA256,
                                         exposure=self.execution.observation["exposure"]["adapted"],
                                         rng_state_digests=self.rng)
        for name, value in (("execution_condition_digest", other), ("output_manifest_digest", other),
                            ("input_manifest_digests", [other])):
            with self.subTest(run=name):
                store = px.clone_store(self.world)
                run = px.reseal(self.execution.runs["adapted"], **{name: value})
                store.add(run)
                with self.assertRaises(ContractViolation):
                    experiment.check_run(store, run["record_digest"], self.world.read,
                                         contract_manifest_digest=px.MANIFEST_SHA256,
                                         exposure=self.execution.observation["exposure"]["adapted"],
                                         rng_state_digests=self.rng)


if __name__ == "__main__":
    unittest.main()
