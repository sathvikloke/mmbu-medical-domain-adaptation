"""One command to generate, and one to validate, the Phase 1A evidence bundle.

``python3 -m mmbu_phase1.bundle generate --bundle DIR --retention FILE`` records the
source state, runs the synthetic base/adapted evaluator through the empty-mapping
launcher, records every required command (argv, stdout/stderr, exit code, times)
bound to the source-state and experiment digests, derives claims, trace, and the
phase decision, computes the evidence manifest last, and writes the external
retention receipt outside the bundle.  ``validate`` re-derives everything from
bundle bytes and rejects any forged decision, invalid root, or self-reference.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any

from mmbu_phase1 import (authority, canonical, claims as claim_rules, decisions, evidence, fields as f, lineage, paths,
                         phase1a, prompt_contract, scope, status)
from mmbu_phase1.store import RecordStore

COMMANDS = (
    ("verify-contract", ["tools/team.py", "verify-contract"], False),
    ("authority-verify", ["-m", "mmbu_phase1.authority", "verify", "--root", "."], True),
    ("phase1-focused-tests", ["-m", "unittest", "discover", "-s", "tests/phase1", "-v"], True),
    ("team-test", ["tools/team.py", "test"], False),
    ("smoke", ["tools/team.py", "smoke"], False),
    ("verify-evidence", ["tools/team.py", "verify-evidence"], False),
    ("verify-links", ["tools/team.py", "verify-links"], False),
)
ROW_COMMANDS = {"P1-00": ("team-test", "verify-evidence"), "P1-01": ("authority-verify",),
                "P1-20": ("verify-contract",)}
TEST_LINE = re.compile(r"^(\w+) \(([\w.]+)\)(?: \.\.\.|\n)")
OUTCOME_LINE = re.compile(r"^(\w+) \(([\w.]+)\)(?:\n.*?)? \.\.\. (ok|FAIL|ERROR|skipped.*|expected failure|unexpected success)$",
                          re.M)
FAILED_LINE = re.compile(r"^(FAIL|ERROR): (\w+) \(([\w.]+)\)", re.M)


def parse_test_inventory(stderr: str) -> list[dict]:
    outcomes: dict[str, str] = {}
    for match in OUTCOME_LINE.finditer(stderr):
        outcomes[match.group(2)] = "passed" if match.group(3) == "ok" else (
            "skipped" if match.group(3).startswith("skipped") else "failed")
    for match in FAILED_LINE.finditer(stderr):
        test_id = match.group(3).split(" ")[0]
        outcomes[test_id] = "failed"
    return [{"outcome": outcomes[t], "test_id": t} for t in sorted(outcomes, key=str.encode)]


def run_command(world: phase1a.World, name: str, args: list[str], phase1_path: bool, repo: Path, bindings: dict) -> dict:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if phase1_path:
        env["PYTHONPATH"] = str(repo / "src")
    argv = [sys.executable, *args]
    started = world.clock()
    result = subprocess.run(argv, cwd=repo, env=env, capture_output=True, check=False)
    ended = world.clock()
    stdout = world.write(f"commands/{name}.stdout", result.stdout)
    stderr = world.write(f"commands/{name}.stderr", result.stderr)
    record = {"kind": "mmbu.phase1a.command_record", "version": 1, "name": name, "argv": argv, "cwd": str(repo),
              "environment": "inherited developer environment" + ("; PYTHONPATH=src" if phase1_path else ""),
              "started_at": started, "ended_at": ended, "exit_code": result.returncode, "stdout_sha256": stdout,
              "stderr_sha256": stderr, **bindings}
    world.artifact(f"commands/{name}.json", record)
    return {**record, "stderr_text": result.stderr.decode("utf-8", errors="replace")}


def expand(prefixes: tuple[str, ...], inventory: dict[str, str], label: str) -> list[str]:
    found = set()
    for prefix in prefixes:
        matches = {t for t in inventory if t == prefix or (prefix.endswith(".") and t.startswith(prefix))}
        f.require(bool(matches), label, f"no test matches {prefix!r} (the scope table names a missing test)")
        found |= matches
    return sorted(found, key=str.encode)


def build_claims(world: phase1a.World, inventory: dict[str, str], commands: dict[str, dict], source_state: dict,
                 present: set[str]) -> tuple[dict, dict]:
    rows, trace_rows = [], []
    for rid in claim_rules.INPUT_IDS:
        spec = scope.ROW_SPECS.get(rid)
        code, prefixes, behaviors, evidence_paths, limitations = spec if spec else ((), (), {}, (), ())
        tests = expand(prefixes, inventory, rid) if (prefixes and inventory) else []
        evidence_paths = sorted(set(evidence_paths), key=str.encode)
        if rid in scope.DEFERRED_ROWS:
            status = scope.DEFERRED_ROWS[rid]
            notes = [scope.DEFERRAL_REASONS[rid], *limitations]
            evidence_paths = []
        elif rid in scope.VALIDATION_ONLY_ROWS:
            status, notes = "untested", list(limitations)
        else:
            notes = list(limitations)
            needed = list(scope.COMMON_EVIDENCE) + list(evidence_paths)
            commands_ok = all(commands.get(name, {}).get("exit_code") == 0
                              for name in ("phase1-focused-tests", *ROW_COMMANDS.get(rid, ())))
            evidence_ok = all(p in present for p in needed)
            tests_ok = bool(tests) and all(inventory.get(t) == "passed" for t in tests)
            if tests and any(inventory.get(t) == "failed" for t in tests):
                status = "failed"
            elif commands and any(commands.get(name, {}).get("exit_code") not in (None, 0)
                                  for name in ("phase1-focused-tests", *ROW_COMMANDS.get(rid, ()))):
                status = "failed"
            elif commands_ok and evidence_ok and tests_ok:
                status = "verified"
                evidence_paths = sorted(set(needed), key=str.encode)
            else:
                status = "untested"
                notes.append("Required command logs, test inventory, or evidence artifacts are absent from this bundle.")
        if status != "verified":
            evidence_paths = [p for p in evidence_paths if p in present]
        digests = [world.files[p] for p in evidence_paths]
        rows.append({"requirement_id": rid, "status": status, "code_paths": sorted(code, key=str.encode),
                     "test_ids": tests, "evidence_paths": evidence_paths, "evidence_digests": digests,
                     "limitations": notes or ["No additional limitation beyond the bundle limitations document."]})
        trace_rows.append({"requirement_id": rid, "test_ids": tests, "evidence_paths": evidence_paths,
                           "behaviors": [{"behavior": name, "test_ids": expand(test_prefixes, inventory, rid)}
                                         for name, test_prefixes in sorted(behaviors.items())] if inventory else []})
    claims = world.record("claims", "claims.json", {
        "schema_id": f.SCHEMA_PREFIX + "claims", "schema_version": 1, "source_state_digest": source_state["record_digest"],
        "claims": rows, "created_at": world.clock()})
    trace = world.record("requirement_trace", "requirement-trace.json", {
        "schema_id": f.SCHEMA_PREFIX + "requirement_trace", "schema_version": 1,
        "source_state_digest": source_state["record_digest"], "claims_digest": claims["record_digest"],
        "rows": trace_rows, "created_at": world.clock()})
    return claims, trace


def evaluate_predicates(store: RecordStore, read: Any, claims: dict, inventory: dict[str, str], manifest_paths: dict,
                        commands: dict[str, dict], contract_manifest_digest: str) -> dict[str, bool]:
    statuses = {row["requirement_id"]: row["status"] for row in claims["claims"]}
    predicates = {name: False for name in claim_rules.REJECTION_PREDICATES}
    predicates["failed_mandatory_row"] = "failed" in statuses.values()
    forced = set(scope.DEFERRED_ROWS) | set(scope.VALIDATION_ONLY_ROWS)
    predicates["deferred_row_verified"] = any(statuses[r] == "verified" for r in forced if statuses[r] != "blocked_external")
    for row in claims["claims"]:
        if row["status"] != "verified":
            continue
        bound = all(manifest_paths.get(p) == d for p, d in zip(row["evidence_paths"], row["evidence_digests"]))
        tested = all(inventory.get(t) == "passed" for t in row["test_ids"])
        if not (bound and tested and row["evidence_paths"] and row["test_ids"]):
            predicates["verified_row_lacks_bound_evidence"] = True
    predicates["self_reference"] = any(set(row["evidence_paths"]) & claim_rules.SELF_REFERENTIAL_PATHS
                                       for row in claims["claims"])
    try:
        verified = phase1a.verify_records(store, read, contract_manifest_digest=contract_manifest_digest)
    except f.ContractViolation:
        predicates["run_not_bound_to_declarations"] = True
        verified = None
    if verified is not None:
        manifest = store.get(verified["condition"]["request_set"]["example_manifest_digest"], "example_manifest")
        for run in verified["runs"].values():
            output = store.get(run["output_manifest_digest"], "execution_output_manifest")
            raw_ids = sorted(e["example_id"] for e in output["entries"] if e["role"] == "raw_output")
            if raw_ids != sorted(row["example_id"] for row in manifest["rows"]):
                predicates["raw_output_missing_or_repaired"] = True
        observed = verified["observation"]["observed_condition"]["call_isolation"]
        predicates["task_context_state_shared"] = any(observed[k] for k in (
            "conversation_reuse", "kv_cache_reuse", "task_receives_context_output", "context_receives_task_output"))
        totals = verified["task_change"]["totals"]
        predicates["failed_rows_left_denominator"] = totals["example_count"] != len(manifest["rows"])
    for record in store.records("lineage_receipt"):
        if record["origin_class"] == "official_rule_summary" and not lineage.is_official_rule_summary(store, record["artifact_digest"]):
            predicates["rule_summary_without_two_reviewer_extraction"] = True
    for experiment_record in store.records("experiment"):
        for root in experiment_record["lineage_root_digests"]:
            receipt = store.get(root, "lineage_receipt")
            try:
                ancestry = lineage.walk(store, receipt["artifact_digest"])
            except f.ContractViolation:
                predicates["public_content_in_development_or_decision"] = True
                continue
            if any(r["origin_class"] in {"mmbu_official", "mmbu_derivative"} for r in ancestry):
                predicates["public_content_in_development_or_decision"] = True
    for receipt in store.records("decision_execution_receipt"):
        try:
            decisions.check_decision_receipt(store, receipt["record_digest"])
        except f.ContractViolation:
            predicates["promotable_decision_missing_controls"] = True
    for contract in store.records("prompt_schema_contract"):
        try:
            prompt_contract.validate_prompt_schema_contract(contract)
        except f.ContractViolation:
            predicates["unconfirmed_contract_called_official_equivalent"] = True
    if commands.get("verify-evidence", {}).get("exit_code") not in (None, 0):
        predicates["historical_bundle_changed"] = True
    predicates["synthetic_called_medical_or_model_evidence"] = any(
        statuses[r] == "verified" for r in ("P1-04", "P1-11", "P1-13", "P1-14", "P1-15", "P1-16"))
    predicates["external_upload_without_user_step"] = statuses["P1-17b"] == "verified"
    predicates["local_preflight_called_external_r0"] = statuses["P1-17b"] == "verified"
    for schema, flag in (("forward_backward", "native_backward_missed_declared_modules"),
                         ("resource_measurement", "resource_facts_estimated")):
        if store.records(schema):
            predicates[flag] = True  # Phase 1A implements no validator for these records; any such record fails closed
    return predicates


LIMITATIONS = """# Phase 1A limitations

* Synthetic engineering mechanics only: no model, GPU, real biomedical source, public MMBU content, or network
  resource was used. Nothing here is medical, model-performance, official-harness, or competition evidence.
* The overall Phase 1 disposition is derived by the contract decision function; Phase 1A completion is a separate
  implementation-slice statement.
* The decision firewall validates declared records and synthetic canaries only; it does not prove that an operating
  system restricted mounts, traced reads, or denied networking. The child's network denial is an in-process socket
  guard plus a probe, not an OS sandbox.
* The synthetic adapter packs the separate task and context call transcripts into the single per-example raw record;
  any call or pass failure fails the whole evaluation row.
* Precision/backend fields are the declared Phase 1A CPU values; the synthetic responder performs no tensor
  computation. RNG streams are declared and their state is recorded, but greedy synthetic decoding consumes none.
* Command logs were produced in the inherited developer environment of the generating checkout; only the evaluator
  child runs under the closed empty-mapping environment policy.
* Executable sampling, conversion, approval, extraction, and decision functions are bound by digest and checked by
  their stated projections, not re-executed.
"""


def generate(repo: Path, bundle_root: Path, retention_path: Path, *, run_commands: bool = True,
             run_root: str | None = None) -> dict:
    repo = Path(os.path.realpath(repo))
    bundle_root = Path(os.path.realpath(bundle_root.parent)) / bundle_root.name
    f.require(not os.path.lexists(bundle_root), "bundle", "the bundle directory must not exist")
    f.require(not str(Path(os.path.realpath(retention_path.parent)) / retention_path.name).startswith(str(bundle_root) + "/"),
              "retention", "the retention receipt must live outside the bundle")
    pins = authority.contract_pins(repo)
    authority.load_authority(repo)
    authority_bytes = {p: paths.member_bytes(repo, p) for p in authority.AUTHORITY_PATHS}
    status_record = canonical.loads_canonical(authority_bytes[authority.STATUS_PATH])
    runtime_evidence = authority.runtime_status_evidence_bytes(repo, status_record)
    clock = phase1a.Clock()
    source_state, patch = evidence.build_source_state(repo, clock())
    run_root = run_root or str(Path(os.path.realpath(tempfile.gettempdir())) /
                               f"phase1a-run-{canonical.value_digest([clock(), os.getpid()])[:16]}")
    world = phase1a.build_world(bundle_root, repository_root=str(repo), run_root=run_root,
                                python_executable=os.path.realpath(sys.executable), authority_files=authority_bytes,
                                clock=clock)
    for key, data in runtime_evidence.items():
        world.write(authority.RUNTIME_EVIDENCE_BUNDLE_PATHS[key], data)
    world.record("source_state", "source-state.json", source_state)
    if patch:
        world.write("source/canonical.patch", patch)
    execution = phase1a.execute(world, source_state_digest=source_state["record_digest"],
                                contract_manifest_digest=pins.manifest_sha256)
    phase1a.verify_execution(world, execution, contract_manifest_digest=pins.manifest_sha256)
    bindings = {"source_state_digest": source_state["record_digest"], "contract_manifest_sha256": pins.manifest_sha256,
                "experiment_digests": {side: world.records[f"experiment_{side}"]["record_digest"] for side in ("base", "adapted")}}
    commands: dict[str, dict] = {}
    inventory: dict[str, str] = {}
    if run_commands:
        for name, args, phase1_path in COMMANDS:
            commands[name] = run_command(world, name, args, phase1_path, repo, bindings)
        parsed = parse_test_inventory(commands["phase1-focused-tests"]["stderr_text"])
        world.artifact("tests/phase1-test-inventory.json", {"kind": "mmbu.phase1a.test_inventory", "version": 1,
                                                            "command": "phase1-focused-tests", "tests": parsed, **bindings})
        inventory = {row["test_id"]: row["outcome"] for row in parsed}
    world.write("limitations.md", LIMITATIONS.encode("utf-8"))
    present = set(world.files)
    claims, trace = build_claims(world, inventory, commands, source_state, present)
    predicates = evaluate_predicates(world.store, world.read, claims, inventory, dict(world.files), commands,
                                     pins.manifest_sha256)
    decision = claim_rules.derive_decision(claims["claims"], predicates)
    world.record("phase_decision", "phase-decision.json", {
        "schema_id": f.SCHEMA_PREFIX + "phase_decision", "schema_version": 1, "claims_digest": claims["record_digest"],
        "trace_digest": trace["record_digest"], "decision": decision,
        "rejection_predicates": claim_rules.predicate_rows(predicates), "derived_at": clock()})
    bundle_id = "phase1a-bundle-" + source_state["record_digest"][:16] + "-" + canonical.value_digest([clock()])[:8]
    _, root = evidence.build_evidence_manifest(bundle_root, bundle_id, clock())
    receipt = evidence.retention_receipt("external-retention:" + str(retention_path), bundle_id, root)
    descriptor = os.open(retention_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o444)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(canonical.dumps(receipt))
    validated = validate(bundle_root, retention_path, repo)
    return {"bundle": str(bundle_root), "root_sha256": root, "decision": validated,
            "statuses": {row["requirement_id"]: row["status"] for row in claims["claims"]},
            "source_state_digest": source_state["record_digest"], "patch_sha256": source_state["patch_sha256"]}


def load_bundle(bundle_root: Path) -> tuple[RecordStore, dict[str, str]]:
    store = RecordStore()
    manifest_paths = {}
    manifest = canonical.loads_canonical(paths.member_bytes(bundle_root, evidence.MANIFEST_NAME))
    for member in manifest["members"]:
        data = paths.member_bytes(bundle_root, member["path"])
        manifest_paths[member["path"]] = member["sha256"]
        store.add_artifact(data)
        if member["schema_id"] is not None:
            store.add(canonical.loads_canonical(data))
    return store, manifest_paths


def validate(bundle_root: Path, retention_path: Path, repo: Path | None = None) -> str:
    """Standalone validator: root, records, source state, claims/trace, and the derived decision."""
    bundle_root = Path(bundle_root)
    receipt = canonical.loads_canonical(paths.member_bytes(Path(retention_path).parent, Path(retention_path).name))
    evidence.verify_bundle_root(bundle_root, receipt)
    store, manifest_paths = load_bundle(bundle_root)
    read = lambda relative: paths.member_bytes(bundle_root, relative)  # noqa: E731
    pins_digest = "15daeff7a4f162a0c6adf1aae4d8d772bcbaa23351ab3120cd284a7ca8835cce"
    states = store.records("source_state")
    f.require(len(states) == 1, "bundle", "exactly one source-state record")
    source_state = evidence.validate_source_state(states[0])
    current_status = canonical.loads_canonical(read("authority/current-status.json"))
    statuses = store.records("current_status")
    status_digests = {row["record_digest"] for row in statuses}
    expected_status_digests = {current_status["record_digest"]}
    if current_status["phase"] == "phase1_returned_blocked":
        predecessor = next(
            row for row in current_status["facts"]
            if row["fact_id"] == status.PREDECESSOR_FACT_ID
        )
        expected_status_digests.add(predecessor["value"])
    f.require(
        len(statuses) == len(expected_status_digests)
        and status_digests == expected_status_digests,
        "bundle", "current-status records must be exactly the authority head and its bound predecessor",
    )
    authority.validate_runtime_status_evidence(current_status, store)
    if repo is not None:
        patch = read("source/canonical.patch") if "source/canonical.patch" in manifest_paths else None
        evidence.check_source_state(source_state, Path(repo), patch)
        f.require(read("authority/current-status.json") == paths.member_bytes(Path(repo), authority.STATUS_PATH),
                  "authority/current-status.json", "evidence copy is not byte-identical to the repository status")
        authority.contract_pins(Path(repo))
    claim_records = store.records("claims")
    f.require(len(claim_records) == 1, "bundle", "exactly one claims record")
    claims = claim_rules.validate_claims(claim_records[0])
    f.require(claims["source_state_digest"] == source_state["record_digest"], "claims", "binds another source state")
    trace_records = store.records("requirement_trace")
    f.require(len(trace_records) == 1, "bundle", "exactly one requirement-trace record")
    trace = claim_rules.validate_requirement_trace(trace_records[0], claims)
    decision_records = store.records("phase_decision")
    f.require(len(decision_records) == 1, "bundle", "exactly one phase-decision record")
    decision = decision_records[0]
    inventory = {}
    if "tests/phase1-test-inventory.json" in manifest_paths:
        inventory = {row["test_id"]: row["outcome"] for row in canonical.loads(read("tests/phase1-test-inventory.json"))["tests"]}
    commands = {}
    for relative in manifest_paths:
        if relative.startswith("commands/") and relative.endswith(".json"):
            record = canonical.loads(read(relative))
            commands[record["name"]] = record
            f.require(record["source_state_digest"] == source_state["record_digest"], relative,
                      "command record binds another source state")
    predicates = evaluate_predicates(store, read, claims, inventory, manifest_paths, commands, pins_digest)
    return claim_rules.check_decision(decision, claims, trace, predicates)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m mmbu_phase1.bundle", description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=("generate", "validate"))
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--retention", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--skip-commands", action="store_true", help="omit command logs (claims stay unverified)")
    args = parser.parse_args(argv)
    try:
        if args.command == "generate":
            summary = generate(args.root, args.bundle, args.retention, run_commands=not args.skip_commands)
            print(canonical.dumps(summary).decode("utf-8"))
        else:
            print("phase decision:", validate(args.bundle, args.retention, args.root))
    except (f.ContractViolation, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
