"""Deterministic standard-library backend for Lane 1 engineering tests."""

from __future__ import annotations

from fractions import Fraction

from mmbu_phase1 import canonical, rational
from mmbu_phase1.fields import ContractViolation, closed, literal, require


BASE_STATE_BYTES = canonical.dumps({
    "language_adapter": rational.to_wire(0),
    "projector_adapter": rational.to_wire(0),
})

_SCOPES = {
    "recipe_arch::B0": (),
    "recipe_arch::B1-L": ("language_adapter",),
    "recipe_arch::B2-P": ("language_adapter", "projector_adapter"),
}


class SyntheticBackend:
    """Tiny exact-arithmetic state machine with no file or network access."""

    def __init__(self):
        self.candidate_id = None
        self._architecture = None
        self._seed = None
        self._task_share = Fraction(0)
        self._context_share = Fraction(0)
        self._unit_mass = Fraction(0)
        self._state = {"language_adapter": Fraction(0), "projector_adapter": Fraction(0)}
        self._base_state = None

    def initialize(self, *, base_state: bytes, arm: dict, seed: int) -> None:
        state = canonical.loads_canonical(base_state)
        closed(state, "backend.base_state", ("language_adapter", "projector_adapter"))
        self._state = {
            "language_adapter": rational.from_wire(state["language_adapter"], "backend.base_state.language_adapter"),
            "projector_adapter": rational.from_wire(state["projector_adapter"], "backend.base_state.projector_adapter"),
        }
        self.candidate_id = arm["candidate_id"]
        self._architecture = arm["architecture_id"]
        self._task_share = rational.from_wire(arm["task_unit_share"], "backend.arm.task_unit_share")
        self._context_share = rational.from_wire(arm["context_unit_share"], "backend.arm.context_unit_share")
        self._unit_mass = rational.from_wire(arm["unit_total_mass"], "backend.arm.unit_total_mass")
        require(self._architecture in _SCOPES, "backend.arm.architecture_id", "unsupported architecture")
        self._seed = seed
        self._base_state = bytes(base_state)

    def trainable_parameter_names(self) -> tuple[str, ...]:
        require(self._architecture is not None, "backend", "must initialize before scope inspection")
        return _SCOPES[self._architecture]

    def base_state_bytes(self) -> bytes:
        require(self._base_state is not None, "backend", "must initialize before base-state inspection")
        return self._base_state

    def step(self, row: dict, *, objective_mode: str, learning_rate: Fraction) -> None:
        require(objective_mode in {"task", "dual"}, "backend.objective_mode", "must be task or dual")
        require(self._architecture != "recipe_arch::B0", "backend", "B0 cannot receive optimizer updates")
        feature = rational.from_wire(row["feature"], "backend.row.feature")
        task_signal = Fraction(1 if row["task_target"] else -1)
        context_signal = Fraction(1 if row["context_target"] else -1)
        combined = self._unit_mass * (
            self._task_share * task_signal + self._context_share * context_signal
        )
        if "language_adapter" in self.trainable_parameter_names():
            self._state["language_adapter"] += learning_rate * combined
        if "projector_adapter" in self.trainable_parameter_names():
            self._state["projector_adapter"] += learning_rate * combined * feature

    def predict(self, row: dict) -> tuple[int, int | None]:
        feature = rational.from_wire(row["feature"], "backend.row.feature")
        language = self._state["language_adapter"]
        projector = self._state["projector_adapter"]
        task = int(feature + language + projector * feature >= 0)
        context = int(feature - language + projector >= 0) if row["context_target"] is not None else None
        return task, context

    def dump_state(self) -> bytes:
        return canonical.dumps({key: rational.to_wire(value) for key, value in self._state.items()})

    def load_state(self, data: bytes) -> None:
        self._load(data, "backend.checkpoint")

    def export(self) -> bytes:
        return self.dump_state()

    def load_export(self, data: bytes) -> None:
        self._load(data, "backend.export")

    def _load(self, data: bytes, path: str) -> None:
        state = canonical.loads_canonical(data)
        closed(state, path, ("language_adapter", "projector_adapter"))
        self._state = {key: rational.from_wire(state[key], f"{path}.{key}") for key in state}


__all__ = ["BASE_STATE_BYTES", "ContractViolation", "SyntheticBackend"]
