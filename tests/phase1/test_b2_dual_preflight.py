"""CPU contract tests for the synthetic native dual-objective preflight."""

from copy import deepcopy
from pathlib import Path
import unittest

from mmbu_phase1 import b2_dual_preflight, canonical
from mmbu_phase1.fields import ContractViolation


class B2DualPreflightTests(unittest.TestCase):
    def test_checked_in_config_is_canonical_and_closed(self):
        path = Path(__file__).resolve().parents[2] / "config/phase1/b2-dual-objective-preflight.json"
        record = b2_dual_preflight.load_preflight_config(path)
        self.assertEqual(path.read_bytes(), canonical.dumps(record) + b"\n")

    def test_scope_resource_and_objective_mutations_fail_closed(self):
        path = Path(__file__).resolve().parents[2] / "config/phase1/b2-dual-objective-preflight.json"
        base = b2_dual_preflight.load_preflight_config(path)
        mutations = []
        for section, key, value in (
            ("execution", "optimizer_steps", 2),
            ("execution", "biomedical_inputs_allowed", True),
            ("execution", "mmbu_inputs_allowed", True),
            ("scheduler", "gpu_count", 2),
            ("scheduler", "max_retries", 1),
            ("objective", "reduction", "mean_of_means"),
            ("objective", "task_unit_share", {"denominator": 1, "numerator": 1}),
            ("objective", "comparison_orders", [["u1-task", "u1-context", "u2-task"]]),
            ("objective", "microbatch_size", 2),
        ):
            changed = deepcopy(base)
            changed[section][key] = value
            changed["record_digest"] = canonical.record_digest(changed)
            mutations.append(changed)
        extra = deepcopy(base); extra["objective"]["new_policy"] = True
        extra["record_digest"] = canonical.record_digest(extra); mutations.append(extra)
        for record in mutations:
            with self.subTest(record=record), self.assertRaises(ContractViolation):
                b2_dual_preflight.validate_preflight_config(record)


if __name__ == "__main__":
    unittest.main()
