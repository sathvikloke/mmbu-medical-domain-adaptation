"""``mmbu.phase1.prompt_schema_contract``: versioned prompt/schema adapter binding.

No status here is official-harness equivalence: ``synthetic`` binds no official
source, ``brief_snapshot`` stays provisional, and ``organizer_confirmed`` needs a
written organizer-answer source.  ``inference_settings_digest`` is the RFC 8785
digest of the exact projection of the bound execution condition, not a handle.
"""

from __future__ import annotations

from typing import Any

from mmbu_phase1 import canonical, fields as f, rational
from mmbu_phase1.store import RecordStore
from mmbu_phase1.vocab import CONTRACT_STATUSES

KEYS = (
    "schema_id",
    "schema_version",
    "contract_id",
    "contract_status",
    "task_prompt_digest",
    "context_prompt_digest",
    "task_output_schema_digest",
    "context_output_schema_digest",
    "requested_context_field_registry_digest",
    "parser_digest",
    "validator_digest",
    "judge_policy_digest",
    "geometry_threshold",
    "inference_settings_digest",
    "official_source_digests",
    "supersedes_digest",
    "created_at",
    "record_digest",
)
SOURCE_KEYS = ("source_id", "source_role", "sha256", "span")
SOURCE_ROLES = ("brief", "rules", "site", "dataset_card", "organizer_answer", "other_official")
PROJECTION_FIELDS = ("decoding", "call_isolation", "failure_retry", "batching", "precision_backend")


def validate_prompt_schema_contract(record: Any, path: str = "prompt_schema_contract") -> dict:
    f.record(record, "prompt_schema_contract", KEYS, path)
    f.text(record["contract_id"], f"{path}.contract_id")
    status = f.one_of(record["contract_status"], f"{path}.contract_status", CONTRACT_STATUSES)
    distinct = ("task_prompt_digest", "context_prompt_digest", "task_output_schema_digest", "context_output_schema_digest")
    for name in distinct + ("requested_context_field_registry_digest", "parser_digest", "validator_digest",
                            "judge_policy_digest", "inference_settings_digest"):
        f.digest(record[name], f"{path}.{name}")
    f.require(len({record[name] for name in distinct}) == len(distinct), path,
              "task/context prompt and output-schema digests must be distinct")
    rational.from_wire(record["geometry_threshold"], f"{path}.geometry_threshold")
    sources = f.array(record["official_source_digests"], f"{path}.official_source_digests")
    for index, item in enumerate(sources):
        label = f"{path}.official_source_digests[{index}]"
        f.closed(item, label, SOURCE_KEYS)
        f.text(item["source_id"], f"{label}.source_id")
        f.one_of(item["source_role"], f"{label}.source_role", SOURCE_ROLES)
        f.digest(item["sha256"], f"{label}.sha256")
        f.text(item["span"], f"{label}.span")
    f.sorted_unique(sources, f"{path}.official_source_digests", canonical.dumps)
    roles = {item["source_role"] for item in sources}
    if status == "synthetic":
        f.require(not sources, f"{path}.official_source_digests", "a synthetic contract binds no official source")
    else:
        f.require(bool(roles - {"organizer_answer"}), f"{path}.official_source_digests",
                  "a brief_snapshot/organizer_confirmed contract binds at least one exact published source")
    if status == "organizer_confirmed":
        f.require("organizer_answer" in roles, f"{path}.official_source_digests",
                  "organizer_confirmed requires a written organizer-answer source")
    f.nullable(f.digest, record["supersedes_digest"], f"{path}.supersedes_digest")
    f.timestamp(record["created_at"], f"{path}.created_at")
    return record


def inference_settings_projection(condition: dict) -> dict:
    """The closed object whose RFC 8785 digest is ``inference_settings_digest``.

    It excludes ``components.prompt_schema_contract_digest`` so the prompt
    contract and execution condition remain acyclic.
    """
    projection = {name: condition[name] for name in PROJECTION_FIELDS}
    projection["cache_network"] = condition["runtime"]["cache_network"]
    return projection


def inference_settings_digest(condition: dict) -> str:
    return canonical.value_digest(inference_settings_projection(condition))


def official_equivalence_allowed(contract: dict) -> bool:
    """Phase 1 never labels a contract official-harness equivalent."""
    validate_prompt_schema_contract(contract)
    return False


def check_prompt_schema_contract(store: RecordStore, digest: Any, path: str = "prompt_schema_contract") -> dict:
    """Resolve every bound prompt/schema/adapter artifact and the field registry."""
    record = validate_prompt_schema_contract(store.get(digest, "prompt_schema_contract", path), path)
    for name in ("task_prompt_digest", "context_prompt_digest", "task_output_schema_digest",
                 "context_output_schema_digest", "parser_digest", "validator_digest", "judge_policy_digest"):
        store.artifact(record[name], f"{path}.{name}")
    registry = canonical.loads_canonical(store.artifact(record["requested_context_field_registry_digest"],
                                                        f"{path}.requested_context_field_registry_digest"))
    f.require(type(registry) is dict and "fields" in registry, f"{path}.requested_context_field_registry_digest",
              "registry must declare its fields")
    f.string_set(registry["fields"], f"{path}.requested_context_field_registry.fields", nonempty=True)
    validator = canonical.loads_canonical(store.artifact(record["validator_digest"], f"{path}.validator_digest"))
    f.require(type(validator) is dict and f.same(validator.get("geometry_threshold"), record["geometry_threshold"]),
              f"{path}.geometry_threshold", "must equal the bound validator's threshold")
    if record["supersedes_digest"] is not None:
        prior = validate_prompt_schema_contract(store.get(record["supersedes_digest"], "prompt_schema_contract", path))
        f.require(prior["contract_id"] == record["contract_id"], f"{path}.supersedes_digest",
                  "a successor keeps the contract identity")
        f.require(f.timestamp(prior["created_at"], path) < f.timestamp(record["created_at"], path), path,
                  "a successor must follow its predecessor")
    return record


def field_registry(store: RecordStore, contract: dict) -> list[str]:
    return canonical.loads_canonical(store.artifact(contract["requested_context_field_registry_digest"]))["fields"]
