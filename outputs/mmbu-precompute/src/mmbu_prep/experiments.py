"""Offline experiment declarations, local byte receipts, and confirmation events.

These are audit aids, not filesystem immutability, access controls, data-use
permission, model execution, or evidence that a declared policy was followed.
Keep the returned hashes independently; editable files cannot anchor themselves.
"""

from copy import deepcopy
from datetime import datetime, timedelta
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import stat


_HASH = re.compile(r"[0-9a-f]{64}\Z")
_EVENT_FILES = ("00-frozen.json", "01-opened.json", "02-result.json", "03-retired.json")
_STATUSES = ("frozen_unopened", "opened", "result_recorded", "retired_to_development")


def _fields(value, names, label):
    if not isinstance(value, dict) or set(value) != set(names.split()):
        raise ValueError(f"{label} must contain exactly: {names}")
    return value


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonblank string")
    return value


def _revision(value, label):
    value = _text(value, label)
    if value.lower() in {"main", "master", "head", "latest", "pending", "unresolved", "tbd", "unknown", "none"}:
        raise ValueError(f"{label} must be an explicit pinned revision, not a placeholder/branch alias")
    return value


def _sha(value):
    if not isinstance(value, str) or not _HASH.fullmatch(value):
        raise ValueError("sha256 must be 64 lowercase hexadecimal characters")
    return value


def _time(value):
    value = _text(value, "UTC timestamp")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("timestamp must be an ISO-8601 UTC datetime") from exc
    if "T" not in value or result.tzinfo is None or result.utcoffset() != timedelta(0):
        raise ValueError("timestamp must be an ISO-8601 UTC datetime with UTC offset")
    return result


def _relative(value):
    value = _text(value, "artifact path")
    path = PurePosixPath(value)
    if path.is_absolute() or value != path.as_posix() or ".." in path.parts or value == "." or "\\" in value:
        raise ValueError("artifact paths must be canonical relative POSIX paths without parent traversal")
    return value


def _scope(values):
    if not isinstance(values, list) or not values:
        raise ValueError("artifact scope must be a nonempty list")
    paths = [_relative(value) for value in values]
    for index, first in enumerate(paths):
        for second in paths[index + 1:]:
            if first == second or first.startswith(second + "/") or second.startswith(first + "/"):
                raise ValueError("artifact scope must not contain duplicate or overlapping selections")
    return sorted(paths)


def _canonical(value):
    try:
        return json.dumps(value, ensure_ascii=False, allow_nan=False,
                          sort_keys=True, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("value must be finite JSON") from exc


def _seal(payload, key):
    return {**payload, key: hashlib.sha256(_canonical(payload)).hexdigest()}


def _check_seal(value, key, expected):
    _sha(expected)
    if not isinstance(value, dict) or key not in value:
        raise ValueError("missing digest")
    actual = _sha(value[key])
    computed = hashlib.sha256(_canonical({k: v for k, v in value.items() if k != key})).hexdigest()
    if actual != expected or computed != expected:
        raise ValueError("digest mismatch against retained anchor")


def validate_experiment_record(record):
    """Require explicit pre-run provenance, returning a deep copy without defaults.

    This validates the declaration's shape and references. It does not read
    artifacts, inspect model formats, validate manifests, or approve their use.
    """
    _fields(record, "schema_version record_kind experiment_id owner created_at_utc purpose hypothesis "
            "baseline candidate seeds artifact_scope artifacts protocol processor grading source weights "
            "comparison execution evaluation_manifest_artifact confirmation", "experiment record")
    if type(record["schema_version"]) is not int or record["schema_version"] != 1:
        raise ValueError("schema_version must be integer 1")
    if record["record_kind"] != "pre_run_experiment":
        raise ValueError("record_kind must be pre_run_experiment; old templates are not executable records")
    if record["purpose"] not in ("engineering", "development", "confirmation"):
        raise ValueError("purpose must be explicitly engineering, development or confirmation")
    for field in ("experiment_id", "owner", "hypothesis"):
        _text(record[field], field)
    _time(record["created_at_utc"])
    _scope(record["artifact_scope"])
    artifacts = record["artifacts"]
    if not isinstance(artifacts, dict) or not artifacts:
        raise ValueError("artifacts must be a nonempty named mapping")
    paths = []
    for name, artifact in artifacts.items():
        _text(name, "artifact name")
        _fields(artifact, "path sha256", "artifact")
        paths.append(_relative(artifact["path"]))
        _sha(artifact["sha256"])
    if len(paths) != len(set(paths)):
        raise ValueError("each local artifact path must occur once")
    if any(not any(path == scope or path.startswith(scope + "/") for scope in record["artifact_scope"]) for path in paths):
        raise ValueError("every artifact must be inside the explicitly declared scope")

    def reference(value):
        if _text(value, "artifact reference") not in artifacts:
            raise ValueError("artifact reference does not name a declared artifact")

    for role in ("baseline", "candidate"):
        identity = _fields(record[role], "model_id revision checkpoint_artifact", role)
        _text(identity["model_id"], role + ".model_id")
        _revision(identity["revision"], role + ".revision")
        reference(identity["checkpoint_artifact"])
    _fields(record["seeds"], "training inference bootstrap", "seeds")
    if any(type(seed) is not int for seed in record["seeds"].values()):
        raise ValueError("all seeds must be explicit integers, not booleans")
    for field, names, ref in (("protocol", "revision profile artifact", "artifact"),
                              ("processor", "revision artifact", "artifact"),
                              ("source", "revision registry_artifact", "registry_artifact")):
        section = _fields(record[field], names, field)
        _revision(section["revision"], field + ".revision")
        reference(section[ref])
    _text(record["protocol"]["profile"], "protocol.profile")
    grading = _fields(record["grading"], "judge_model_id judge_revision policy_artifact", "grading")
    _text(grading["judge_model_id"], "judge_model_id")
    _revision(grading["judge_revision"], "judge_revision")
    reference(grading["policy_artifact"])
    weights = _fields(record["weights"], "mode artifact", "weights")
    if weights["mode"] not in ("explicit_uniform", "record_id"):
        raise ValueError("weights.mode must be explicit_uniform or record_id")
    reference(weights["artifact"])
    comparison = _fields(record["comparison"], "estimand multiplicity_policy practical_gain_threshold max_task_regression artifact", "comparison")
    for field in ("estimand", "multiplicity_policy"):
        _text(comparison[field], "comparison." + field)
    for field in ("practical_gain_threshold", "max_task_regression"):
        value = comparison[field]
        if type(value) not in (int, float) or not 0 <= value <= 1 or not math.isfinite(value):
            raise ValueError("comparison thresholds must be finite numbers in [0, 1]")
    reference(comparison["artifact"])
    execution = _fields(record["execution"], "configuration_artifact code_artifact environment_artifact python_version", "execution")
    for field in ("configuration_artifact", "code_artifact", "environment_artifact"):
        reference(execution[field])
    _revision(execution["python_version"], "python_version")
    reference(record["evaluation_manifest_artifact"])
    if record["purpose"] == "confirmation":
        confirmation = _fields(record["confirmation"], "set_id selected_on selection_decision_artifact mechanical_failure_rule", "confirmation")
        _text(confirmation["set_id"], "confirmation.set_id")
        if confirmation["selected_on"] != "external_development_only":
            raise ValueError("confirmation must be selected on external development only")
        reference(confirmation["selection_decision_artifact"])
        _text(confirmation["mechanical_failure_rule"], "mechanical_failure_rule")
    elif record["confirmation"] is not None:
        raise ValueError("non-confirmation records must explicitly set confirmation to null")
    _canonical(record)
    return deepcopy(record)


def _root(root):
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("artifact root must be a directory")
    return root


def _local(root, relative):
    path = root
    for part in PurePosixPath(_relative(relative)).parts:
        path = path / part
        if path.is_symlink():
            raise ValueError("symlinks are not supported in artifact paths")
    return path


def _file(root, path):
    before = path.stat()
    if not stat.S_ISREG(before.st_mode):
        raise ValueError("selected artifacts must be regular files")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    after = path.stat()
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
        raise ValueError("artifact changed while being hashed")
    return {"path": path.relative_to(root).as_posix(), "size_bytes": after.st_size, "sha256": digest.hexdigest()}


def _collect(root, selections, *, allow_missing=False):
    files = []
    for selection in selections:
        path = _local(root, selection["path"])
        if not path.exists():
            if allow_missing:
                continue
            raise ValueError(f"missing selected artifact: {selection['path']}")
        kind = "directory" if path.is_dir() else "file"
        if kind != selection["kind"]:
            raise ValueError(f"selected artifact changed kind: {selection['path']}")
        if kind == "file":
            files.append(_file(root, path))
        else:
            for child in sorted(path.rglob("*")):
                if child.is_symlink():
                    raise ValueError("symlinks are not supported in selected directories")
                if not child.is_dir():
                    files.append(_file(root, child))
    return sorted(files, key=lambda item: item["path"])


def _build_receipt(root, selections):
    paths = _scope(selections)
    scope = []
    for path in paths:
        local = _local(root, path)
        if not local.exists():
            raise ValueError(f"missing selected artifact: {path}")
        scope.append({"path": path, "kind": "directory" if local.is_dir() else "file"})
    artifacts = _collect(root, scope)
    if not artifacts:
        raise ValueError("receipt must cover at least one regular file")
    return _seal({"schema_version": 1, "kind": "local_artifact_receipt", "selections": scope,
                  "artifacts": artifacts}, "receipt_sha256")


def _outside_scope(path, root, selections):
    path = Path(path).resolve()
    for selection in selections:
        selected = root / selection["path"]
        if path == selected or selection["kind"] == "directory" and selected in path.parents:
            raise ValueError("receipt/ledger outputs must be outside the frozen artifact scope")


def _write_new(path, value):
    # Exclusive creation refuses existing files and symlinks, including empty files.
    encoded = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n"
    with Path(path).open("x", encoding="utf-8") as stream:
        stream.write(encoded)


def create_artifact_receipt(root, selections, output):
    """Hash explicit files/directories and exclusively create a new receipt file.

    Directory selections close the set of relevant files recursively. Files
    outside selections are outside the claim. Existing receipts are never edited.
    """
    root = _root(root)
    receipt = _build_receipt(root, selections)
    _outside_scope(output, root, receipt["selections"])
    _write_new(output, receipt)
    return receipt


def _receipt(receipt, expected):
    _fields(receipt, "schema_version kind selections artifacts receipt_sha256", "receipt")
    _check_seal(receipt, "receipt_sha256", expected)
    if type(receipt["schema_version"]) is not int or receipt["schema_version"] != 1 or receipt["kind"] != "local_artifact_receipt":
        raise ValueError("unsupported receipt format")
    if not isinstance(receipt["selections"], list):
        raise ValueError("receipt selections must be a list")
    for selection in receipt["selections"]:
        _fields(selection, "path kind", "selection")
        if selection["kind"] not in ("file", "directory"):
            raise ValueError("selection kind must be file or directory")
    _scope([item["path"] for item in receipt["selections"]])
    if not isinstance(receipt["artifacts"], list) or not receipt["artifacts"]:
        raise ValueError("receipt artifacts must be a nonempty list")
    paths = []
    for artifact in receipt["artifacts"]:
        _fields(artifact, "path size_bytes sha256", "receipt artifact")
        paths.append(_relative(artifact["path"]))
        _sha(artifact["sha256"])
        if type(artifact["size_bytes"]) is not int or artifact["size_bytes"] < 0:
            raise ValueError("artifact size must be a nonnegative integer")
        if not any(artifact["path"] == item["path"] or item["kind"] == "directory"
                   and artifact["path"].startswith(item["path"] + "/") for item in receipt["selections"]):
            raise ValueError("receipt artifact is outside its declared selections")
    if len(paths) != len(set(paths)):
        raise ValueError("duplicate receipt artifact paths")


def verify_artifact_receipt(root, receipt, *, expected_receipt_sha256):
    """Check a retained digest and return missing/extra/changed file paths.

    Malformed/tampered receipts and unsafe paths raise ValueError. Ordinary byte
    drift returns ok=False, including additions under selected directories.
    """
    _receipt(receipt, expected_receipt_sha256)
    observed = {item["path"]: item for item in _collect(_root(root), receipt["selections"], allow_missing=True)}
    expected = {item["path"]: item for item in receipt["artifacts"]}
    missing, extra = sorted(expected.keys() - observed.keys()), sorted(observed.keys() - expected.keys())
    changed = sorted(path for path in expected.keys() & observed.keys() if expected[path] != observed[path])
    return {"ok": not (missing or extra or changed), "missing": missing, "extra": extra, "changed": changed}


def _assert_record_artifacts(record, receipt):
    declared = {item["path"]: item["sha256"] for item in record["artifacts"].values()}
    actual = {item["path"]: item["sha256"] for item in receipt["artifacts"]}
    if declared != actual:
        raise ValueError("declared artifact paths/hashes do not exactly match selected local files")


def verify_experiment_record(record, root):
    """Verify the declaration and its exact local files for any declared purpose.

    No receipt is written and no confirmation state is created. The returned
    hashes are byte-provenance evidence only; source permissions stay separate.
    """
    record = validate_experiment_record(record)
    receipt = _build_receipt(_root(root), record["artifact_scope"])
    _assert_record_artifacts(record, receipt)
    return {"ok": True, "experiment_id": record["experiment_id"], "purpose": record["purpose"],
            "record_sha256": hashlib.sha256(_canonical(record)).hexdigest(),
            "artifact_count": len(receipt["artifacts"]), "receipt": receipt}


def freeze_confirmation(record, root, store, *, frozen_at_utc):
    """Reserve one local ledger per stable confirmation set ID, before opening.

    The store and set ID must be reused consistently by the caller. Another
    store, relabeled set, deleted history, or edits by other tools can bypass it.
    """
    record = validate_experiment_record(record)
    if record["purpose"] != "confirmation":
        raise ValueError("freezing confirmation requires purpose=confirmation")
    if _time(frozen_at_utc) < _time(record["created_at_utc"]):
        raise ValueError("freeze time precedes the experiment declaration")
    root = _root(root)
    receipt = _build_receipt(root, record["artifact_scope"])
    _assert_record_artifacts(record, receipt)
    store = Path(store).absolute()
    if store.is_symlink():
        raise ValueError("confirmation store cannot be a symlink")
    ledger = store / hashlib.sha256(record["confirmation"]["set_id"].encode("utf-8")).hexdigest()
    _outside_scope(ledger, root, receipt["selections"])
    event = _seal({"schema_version": 1, "kind": "confirmation_event", "status": "frozen_unopened",
                   "time_utc": frozen_at_utc, "previous_sha256": None, "record": record,
                   "receipt": receipt, "ledger_path": str(ledger)}, "event_sha256")
    store.mkdir(parents=True, exist_ok=True)
    ledger.mkdir()  # Deliberately never reuse even an empty/preexisting ledger.
    _write_new(ledger / _EVENT_FILES[0], event)
    return event


def _load(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key in confirmation event")
            result[key] = value
        return result
    def nonfinite(value):
        raise ValueError("nonfinite JSON value in confirmation event")
    value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique, parse_constant=nonfinite)
    _canonical(value)  # Also reject overflowing numeric literals such as 1e999.
    return value


def _chain(ledger, expected_freeze_sha256):
    ledger = Path(ledger)
    if ledger.is_symlink() or not ledger.is_dir():
        raise ValueError("confirmation ledger must be an existing directory, not a symlink")
    paths = sorted(ledger.iterdir())
    if not paths or [p.name for p in paths] != list(_EVENT_FILES[:len(paths)]):
        raise ValueError("confirmation event files must form one recognized contiguous sequence")
    events = []
    for index, path in enumerate(paths):
        if path.is_symlink() or not path.is_file():
            raise ValueError("confirmation event must be a regular file")
        event = _load(path)
        names = "schema_version kind status time_utc previous_sha256 event_sha256"
        names += (" record receipt ledger_path", "", " result", " reason result_informed_changes")[index]
        _fields(event, names, "confirmation event")
        expected = expected_freeze_sha256 if index == 0 else event["event_sha256"]
        _check_seal(event, "event_sha256", expected)
        if type(event["schema_version"]) is not int or event["schema_version"] != 1 or event["kind"] != "confirmation_event" or event["status"] != _STATUSES[index]:
            raise ValueError("unexpected confirmation event schema/status")
        timestamp = _time(event["time_utc"])
        if event["previous_sha256"] != (None if index == 0 else events[-1]["event_sha256"]):
            raise ValueError("confirmation event chain digest mismatch")
        if index and timestamp < _time(events[-1]["time_utc"]):
            raise ValueError("confirmation events must have nondecreasing times")
        if index == 0:
            record = validate_experiment_record(event["record"])
            if record["purpose"] != "confirmation" or timestamp < _time(record["created_at_utc"]):
                raise ValueError("invalid frozen confirmation declaration")
            _receipt(event["receipt"], event["receipt"]["receipt_sha256"])
            _assert_record_artifacts(record, event["receipt"])
        elif index == 2:
            _fields(event["result"], "path size_bytes sha256", "confirmation result")
            _relative(event["result"]["path"])
            _sha(event["result"]["sha256"])
            if type(event["result"]["size_bytes"]) is not int or event["result"]["size_bytes"] < 0:
                raise ValueError("result size must be a nonnegative integer")
        elif index == 3:
            _text(event["reason"], "retirement reason")
            if event["result_informed_changes"] is not True:
                raise ValueError("retirement must explicitly record result-informed changes")
        events.append(event)
    return ledger, events


def _append(ledger, events, status, timestamp, **details):
    index = len(events)
    if index >= len(_STATUSES) or status != _STATUSES[index]:
        raise ValueError("forbidden confirmation transition; opening/results cannot be reused")
    if _time(timestamp) < _time(events[-1]["time_utc"]):
        raise ValueError("confirmation transition cannot be backdated")
    event = _seal({"schema_version": 1, "kind": "confirmation_event", "status": status,
                   "time_utc": timestamp, "previous_sha256": events[-1]["event_sha256"], **details}, "event_sha256")
    _write_new(ledger / _EVENT_FILES[index], event)
    return event


def _no_drift(root, frozen):
    receipt = frozen["receipt"]
    check = verify_artifact_receipt(root, receipt, expected_receipt_sha256=receipt["receipt_sha256"])
    if not check["ok"]:
        raise ValueError("frozen artifacts have drifted: " + json.dumps(check, sort_keys=True))


def open_confirmation(ledger, root, *, expected_freeze_sha256, expected_latest_sha256, opened_at_utc):
    """Record intended first access once, after checking all frozen local bytes."""
    ledger, events = _chain(ledger, expected_freeze_sha256)
    _check_seal(events[-1], "event_sha256", expected_latest_sha256)
    _no_drift(root, events[0])
    return _append(ledger, events, "opened", opened_at_utc)


def record_confirmation_result(ledger, root, result_path, *, expected_freeze_sha256, expected_latest_sha256, recorded_at_utc):
    """Record one result's exact bytes without reading or selecting on its score.

    The result path must be a relative regular file outside the frozen scope.
    Preserve that file separately; this event records its hash, not a byte copy.
    """
    ledger, events = _chain(ledger, expected_freeze_sha256)
    _check_seal(events[-1], "event_sha256", expected_latest_sha256)
    root = _root(root)
    _no_drift(root, events[0])
    path = _local(root, result_path)
    _outside_scope(path, root, events[0]["receipt"]["selections"])
    result = _file(root, path)
    return _append(ledger, events, "result_recorded", recorded_at_utc, result=result)


def retire_confirmation(ledger, *, expected_freeze_sha256, expected_latest_sha256, reason, retired_at_utc):
    """Record result-informed changes; the terminal state permits no reselection."""
    ledger, events = _chain(ledger, expected_freeze_sha256)
    _check_seal(events[-1], "event_sha256", expected_latest_sha256)
    _text(reason, "retirement reason")
    return _append(ledger, events, "retired_to_development", retired_at_utc,
                   reason=reason, result_informed_changes=True)


def verify_confirmation(ledger, root, *, expected_freeze_sha256, expected_latest_sha256):
    """Verify history against independently retained first and latest event hashes.

    The latest anchor detects a truncated or rehashed tail. Checks current frozen
    artifact bytes and, after recording, result bytes; performs no state mutation.
    """
    _, events = _chain(ledger, expected_freeze_sha256)
    _check_seal(events[-1], "event_sha256", expected_latest_sha256)
    root = _root(root)
    receipt = events[0]["receipt"]
    artifacts = verify_artifact_receipt(root, receipt, expected_receipt_sha256=receipt["receipt_sha256"])
    result = None
    if len(events) >= 3:
        recorded = events[2]["result"]
        result_receipt = _seal({"schema_version": 1, "kind": "local_artifact_receipt",
                               "selections": [{"path": recorded["path"], "kind": "file"}],
                               "artifacts": [recorded]}, "receipt_sha256")
        result = verify_artifact_receipt(root, result_receipt,
                                        expected_receipt_sha256=result_receipt["receipt_sha256"])
    return {"ok": artifacts["ok"] and (result is None or result["ok"]),
            "status": events[-1]["status"], "event_count": len(events),
            "latest_event_sha256": events[-1]["event_sha256"], "artifacts": artifacts, "result": result}
