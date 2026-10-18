"""Closed Phase 1A child-process environment: prospective policy, launcher, receipt.

The launcher starts from an empty mapping, passes exactly the policy's ordered
``name``/``value`` projection (nine portable rows, plus one UID-derived row on
Darwin), invokes the absolute policy Python directly without a shell, and keeps
a fresh 32-byte parent canary out of the child.  The child captures its complete
``os.environ`` before importing any Phase 1 application module.  Equality, not
a self-declared secret classifier, is the only acceptance rule.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
import posixpath
import secrets
import stat
import subprocess
import sys
from typing import Any, Callable

from mmbu_phase1 import canonical, fields as f, paths
from mmbu_phase1.store import RecordStore

POLICY_KEYS = (
    "schema_id",
    "schema_version",
    "policy_id",
    "platform",
    "launch_uid",
    "repository_root",
    "run_root",
    "python_executable",
    "python_executable_digest",
    "working_directory",
    "environment",
    "parent_canary_name",
    "created_at",
    "record_digest",
)
RECEIPT_KEYS = (
    "schema_id",
    "schema_version",
    "receipt_id",
    "policy_digest",
    "python_executable",
    "argv",
    "working_directory",
    "passed_environment",
    "child_environment",
    "parent_canary",
    "started_at",
    "child_captured_at",
    "ended_at",
    "exit_code",
    "terminal_status",
    "stdout_digest",
    "stderr_digest",
    "record_digest",
)
SAFE_NAMES = ("HOME", "LANG", "LC_ALL", "PYTHONDONTWRITEBYTECODE", "PYTHONHASHSEED", "PYTHONPATH", "PYTHONUTF8",
              "TMPDIR", "TZ")
CANARY_NAME = "MMBU_PHASE1_PARENT_SECRET_CANARY"
PLATFORMS = ("linux", "darwin")
VALUE_SOURCES = ("fixed_literal", "derived_path", "platform_derived")

# Executed with ``python -S -c``: capture first, import the application second.
CHILD_BOOTSTRAP = (
    "import os, sys\n"
    "_captured = sorted(os.environ.items())\n"
    "_loaded = sorted(n for n in sys.modules if n == 'mmbu_phase1' or n.startswith('mmbu_phase1.'))\n"
    "import json\n"
    "from datetime import datetime, timezone\n"
    "_at = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')\n"
    "with open(sys.argv[1], 'x', encoding='utf-8') as _handle:\n"
    "    json.dump({'captured_at': _at, 'environment': [{'name': k, 'value': v} for k, v in _captured],\n"
    "               'phase1_modules_loaded_before_capture': _loaded}, _handle, sort_keys=True, separators=(',', ':'))\n"
    "from mmbu_phase1.child import main as _main\n"
    "raise SystemExit(_main(sys.argv[2:]))\n"
)
CAPTURE_NAME = "child-environment-capture.json"


def current_platform() -> str:
    if sys.platform.startswith("linux"):
        return "linux"
    if sys.platform == "darwin":
        return "darwin"
    f.fail("environment", f"unsupported platform {sys.platform!r}; only linux and darwin are valid")


def expected_environment(platform: str, launch_uid: int, repository_root: str, run_root: str) -> list[dict]:
    """The exact closed, UTF-8-name-sorted policy rows for one platform branch."""
    f.one_of(platform, "platform", PLATFORMS)
    f.integer(launch_uid, "launch_uid", minimum=0)
    rows = [
        {"name": "HOME", "value_source": "derived_path", "value": posixpath.normpath(run_root + "/home")},
        {"name": "LANG", "value_source": "fixed_literal", "value": "C.UTF-8"},
        {"name": "LC_ALL", "value_source": "fixed_literal", "value": "C.UTF-8"},
        {"name": "PYTHONDONTWRITEBYTECODE", "value_source": "fixed_literal", "value": "1"},
        {"name": "PYTHONHASHSEED", "value_source": "fixed_literal", "value": "0"},
        {"name": "PYTHONPATH", "value_source": "derived_path", "value": posixpath.normpath(repository_root + "/src")},
        {"name": "PYTHONUTF8", "value_source": "fixed_literal", "value": "1"},
        {"name": "TMPDIR", "value_source": "derived_path", "value": posixpath.normpath(run_root + "/tmp")},
        {"name": "TZ", "value_source": "fixed_literal", "value": "UTC"},
    ]
    if platform == "darwin":
        rows.append({"name": "__CF_USER_TEXT_ENCODING", "value_source": "platform_derived",
                     "value": f"0x{launch_uid:X}:0x0:0x0"})
    return sorted(rows, key=lambda row: row["name"].encode("utf-8"))


def projection(policy: dict) -> list[dict]:
    """The ordered ``name``/``value`` projection that is the complete child mapping."""
    return [{"name": row["name"], "value": row["value"]} for row in policy["environment"]]


def _rows(value: Any, path: str, keys: tuple[str, ...]) -> list[dict]:
    rows = f.array(value, path, nonempty=True)
    for index, row in enumerate(rows):
        label = f"{path}[{index}]"
        f.closed(row, label, keys)
        for key in ("name", "value"):
            f.text(row[key], f"{label}.{key}", allow_empty=key == "value")
            f.require("\x00" not in row[key], f"{label}.{key}", "must not contain NUL")
    f.sorted_unique(rows, path, lambda row: row["name"].encode("utf-8"))
    return rows


def validate_environment_launch_policy(record: Any, path: str = "environment_launch_policy") -> dict:
    f.record(record, "environment_launch_policy", POLICY_KEYS, path)
    f.text(record["policy_id"], f"{path}.policy_id")
    platform = f.one_of(record["platform"], f"{path}.platform", PLATFORMS)
    uid = f.integer(record["launch_uid"], f"{path}.launch_uid", minimum=0)
    for name in ("repository_root", "run_root", "python_executable", "working_directory"):
        paths.absolute_path(record[name], f"{path}.{name}")
    f.require(record["working_directory"] == record["repository_root"], f"{path}.working_directory",
              "the repository root and working directory are the same directory")
    f.digest(record["python_executable_digest"], f"{path}.python_executable_digest")
    rows = _rows(record["environment"], f"{path}.environment", ("name", "value_source", "value"))
    for index, row in enumerate(rows):
        f.one_of(row["value_source"], f"{path}.environment[{index}].value_source", VALUE_SOURCES)
    expected = expected_environment(platform, uid, record["repository_root"], record["run_root"])
    f.require(f.same(rows, expected), f"{path}.environment",
              "must equal exactly the platform-specific safe rows (no unknown, missing, reordered, or changed entry)")
    for row in rows:
        if row["value_source"] == "derived_path":
            paths.absolute_path(row["value"], f"{path}.environment.{row['name']}")
    f.literal(record["parent_canary_name"], f"{path}.parent_canary_name", CANARY_NAME)
    f.timestamp(record["created_at"], f"{path}.created_at")
    return record


def _file_digest(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def build_policy(repository_root: str, run_root: str, python_executable: str, created_at: str | None = None) -> dict:
    """Construct the prospective policy (before the child exists)."""
    for name, value in (("repository_root", repository_root), ("run_root", run_root),
                        ("python_executable", python_executable)):
        paths.absolute_path(value, name)
    platform = current_platform()
    uid = os.getuid()
    created = created_at or f.utc_now()
    body = {
        "platform": platform,
        "launch_uid": uid,
        "repository_root": repository_root,
        "run_root": run_root,
        "python_executable": python_executable,
        "python_executable_digest": _file_digest(python_executable),
        "working_directory": repository_root,
        "environment": expected_environment(platform, uid, repository_root, run_root),
        "parent_canary_name": CANARY_NAME,
        "created_at": created,
    }
    record = {"schema_id": f.SCHEMA_PREFIX + "environment_launch_policy", "schema_version": 1,
              "policy_id": "environment-launch-policy-" + canonical.value_digest(body)[:24], **body}
    return validate_environment_launch_policy(canonical.seal(record))


def preflight_policy(policy: dict, path: str = "environment_launch_policy") -> None:
    """Filesystem and identity proofs immediately before launch."""
    validate_environment_launch_policy(policy, path)
    f.require(policy["platform"] == current_platform(), f"{path}.platform", "differs from the launcher OS")
    f.require(policy["launch_uid"] == os.getuid(), f"{path}.launch_uid", "differs from the launcher getuid()")
    for name in ("repository_root", "working_directory", "python_executable"):
        paths.lstat_chain(policy[name], f"{path}.{name}")
    root = os.lstat(policy["repository_root"])
    f.require(stat.S_ISDIR(root.st_mode), f"{path}.repository_root", "must be an existing directory")
    src = paths.lstat_chain(posixpath.join(policy["repository_root"], "src"), f"{path}.repository_root/src")[-1]
    f.require(stat.S_ISDIR(src.st_mode), f"{path}.repository_root/src", "must be an existing non-symlink directory")
    python = os.lstat(policy["python_executable"])
    f.require(stat.S_ISREG(python.st_mode), f"{path}.python_executable", "must be a regular file")
    f.require(bool(python.st_mode & (stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)), f"{path}.python_executable",
              "must have an executable bit")
    f.require(python.st_nlink == 1, f"{path}.python_executable", "link count must be exactly one")
    f.require(_file_digest(policy["python_executable"]) == policy["python_executable_digest"],
              f"{path}.python_executable_digest", "does not cover the executable's raw bytes")
    f.require(not os.path.lexists(policy["run_root"]), f"{path}.run_root", "must not exist before this attempt")
    paths.lstat_chain(posixpath.dirname(policy["run_root"]), f"{path}.run_root.parent")
    for row in policy["environment"]:
        if row["name"] == "PYTHONPATH":
            paths.lstat_chain(row["value"], f"{path}.environment.PYTHONPATH")


def create_run_root(policy: dict) -> None:
    root = policy["run_root"]
    os.mkdir(root, 0o700)
    os.chmod(root, 0o700)
    for name in ("home", "tmp"):
        child = posixpath.join(root, name)
        os.mkdir(child, 0o700)
        os.chmod(child, 0o700)
    verify_run_root(policy)


def verify_run_root(policy: dict, path: str = "environment_launch_policy.run_root") -> None:
    for name in ("", "home", "tmp"):
        target = posixpath.join(policy["run_root"], name) if name else policy["run_root"]
        paths.lstat_chain(target, path)
        info = os.lstat(target)
        f.require(stat.S_ISDIR(info.st_mode), path, f"{target} must be a directory")
        f.require(info.st_uid == policy["launch_uid"], path, f"{target} is owned by another user")
        f.require(stat.S_IMODE(info.st_mode) == 0o700, path, f"{target} must have mode 0700")
        if name:
            f.require(not os.listdir(target), path, f"{target} must be fresh and empty")


@dataclass
class LaunchResult:
    receipt: dict
    stdout: bytes
    stderr: bytes
    capture: dict
    capture_bytes: bytes


def child_argv(policy: dict, capture_path: str, payload: list[str], bootstrap: str = CHILD_BOOTSTRAP) -> list[str]:
    expected = canonical.value_digest(projection(policy))
    return [policy["python_executable"], "-S", "-c", bootstrap, capture_path, "--expected-environment-digest",
            expected, *payload]


def launch(
    policy: dict,
    payload: list[str],
    *,
    timeout: float = 900,
    _mutate_mapping: Callable[[dict], dict] | None = None,
    _bootstrap: str | None = None,
) -> LaunchResult:
    """Launch one Phase 1A child; ``_mutate_mapping``/``_bootstrap`` exist only for adversarial tests."""
    preflight_policy(policy)
    create_run_root(policy)
    capture_path = posixpath.join(policy["run_root"], "tmp", CAPTURE_NAME)
    argv = child_argv(policy, capture_path, payload, _bootstrap or CHILD_BOOTSTRAP)
    canary = secrets.token_bytes(32).hex()
    previous = os.environ.get(CANARY_NAME)
    os.environ[CANARY_NAME] = canary
    try:
        present_in_parent = os.environ.get(CANARY_NAME) == canary
        mapping = {row["name"]: row["value"] for row in projection(policy)}
        if _mutate_mapping is not None:
            mapping = _mutate_mapping(dict(mapping))
        started = f.utc_now()
        try:
            completed = subprocess.run(argv, env=mapping, cwd=policy["working_directory"], shell=False,
                                       stdin=subprocess.DEVNULL, capture_output=True, close_fds=True,
                                       timeout=timeout, check=False)
            code, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
        except subprocess.TimeoutExpired as exc:
            code, stdout, stderr = -9, exc.stdout or b"", (exc.stderr or b"") + b"\nlauncher: child timed out\n"
        ended = f.utc_now()
    finally:
        if previous is None:
            os.environ.pop(CANARY_NAME, None)
        else:  # pragma: no cover - a pre-existing canary would already be a policy violation
            os.environ[CANARY_NAME] = previous
    try:
        capture_bytes = paths.member_bytes(posixpath.dirname(capture_path), CAPTURE_NAME)
        capture = json.loads(capture_bytes.decode("utf-8"))
    except (f.ContractViolation, OSError, ValueError):
        capture_bytes, capture = b"", {"captured_at": None, "environment": [], "phase1_modules_loaded_before_capture": None}
    child_rows = sorted(({"name": r["name"], "value": r["value"]} for r in capture.get("environment", [])),
                        key=lambda row: row["name"].encode("utf-8"))
    passed_rows = sorted(({"name": k, "value": v} for k, v in mapping.items()), key=lambda row: row["name"].encode("utf-8"))
    receipt = canonical.seal({
        "schema_id": f.SCHEMA_PREFIX + "environment_launch_receipt",
        "schema_version": 1,
        "receipt_id": "environment-launch-receipt-" + canonical.value_digest([policy["record_digest"], started])[:24],
        "policy_digest": policy["record_digest"],
        "python_executable": policy["python_executable"],
        "argv": argv,
        "working_directory": policy["working_directory"],
        "passed_environment": passed_rows,
        "child_environment": child_rows,
        "parent_canary": {
            "name": CANARY_NAME,
            "value_digest": canonical.raw_digest(canary.encode("utf-8")),
            "present_in_parent": present_in_parent,
            "present_in_child": any(row["name"] == CANARY_NAME for row in child_rows),
        },
        "started_at": started,
        "child_captured_at": capture.get("captured_at") or ended,
        "ended_at": ended,
        "exit_code": code,
        "terminal_status": "succeeded" if code == 0 else "failed",
        "stdout_digest": canonical.raw_digest(stdout),
        "stderr_digest": canonical.raw_digest(stderr),
    })
    return LaunchResult(receipt, stdout, stderr, capture, capture_bytes)


def validate_environment_launch_receipt(record: Any, path: str = "environment_launch_receipt") -> dict:
    f.record(record, "environment_launch_receipt", RECEIPT_KEYS, path)
    f.text(record["receipt_id"], f"{path}.receipt_id")
    f.digest(record["policy_digest"], f"{path}.policy_digest")
    paths.absolute_path(record["python_executable"], f"{path}.python_executable")
    argv = f.array(record["argv"], f"{path}.argv", nonempty=True)
    for index, item in enumerate(argv):
        f.text(item, f"{path}.argv[{index}]", allow_empty=True)
    paths.absolute_path(record["working_directory"], f"{path}.working_directory")
    _rows(record["passed_environment"], f"{path}.passed_environment", ("name", "value"))
    _rows(record["child_environment"], f"{path}.child_environment", ("name", "value"))
    canary = f.closed(record["parent_canary"], f"{path}.parent_canary",
                      ("name", "value_digest", "present_in_parent", "present_in_child"))
    f.text(canary["name"], f"{path}.parent_canary.name")
    f.digest(canary["value_digest"], f"{path}.parent_canary.value_digest")
    f.boolean(canary["present_in_parent"], f"{path}.parent_canary.present_in_parent")
    f.boolean(canary["present_in_child"], f"{path}.parent_canary.present_in_child")
    started = f.timestamp(record["started_at"], f"{path}.started_at")
    captured = f.timestamp(record["child_captured_at"], f"{path}.child_captured_at")
    ended = f.timestamp(record["ended_at"], f"{path}.ended_at")
    f.require(started <= captured <= ended, f"{path}.child_captured_at", "launch timestamps must be ordered")
    code = f.integer(record["exit_code"], f"{path}.exit_code")
    status = f.one_of(record["terminal_status"], f"{path}.terminal_status", ("succeeded", "failed"))
    f.require((status == "succeeded") == (code == 0), f"{path}.terminal_status", "succeeded exactly at exit code zero")
    f.digest(record["stdout_digest"], f"{path}.stdout_digest")
    f.digest(record["stderr_digest"], f"{path}.stderr_digest")
    return record


def check_environment_launch_receipt(store: RecordStore, receipt_digest: Any, path: str = "environment_launch_receipt",
                                     *, capture: dict | None = None) -> dict:
    """Receipt-to-policy equality; any inherited, unknown, missing, or changed entry rejects."""
    receipt = validate_environment_launch_receipt(store.get(receipt_digest, "environment_launch_receipt", path), path)
    policy = validate_environment_launch_policy(store.get(receipt["policy_digest"], "environment_launch_policy",
                                                          f"{path}.policy_digest"))
    f.require(receipt["python_executable"] == policy["python_executable"], f"{path}.python_executable",
              "must byte-equal the policy Python")
    f.require(receipt["working_directory"] == policy["working_directory"], f"{path}.working_directory",
              "must byte-equal the policy working directory")
    f.require(receipt["argv"][0] == policy["python_executable"], f"{path}.argv", "first member must be the policy Python")
    capture_path = posixpath.join(policy["run_root"], "tmp", CAPTURE_NAME)
    expected_argv_prefix = child_argv(policy, capture_path, [])
    f.require(receipt["argv"][:len(expected_argv_prefix)] == expected_argv_prefix, f"{path}.argv",
              "must use the frozen capture-before-import bootstrap directly (no shell)")
    expected = projection(policy)
    f.require(f.same(receipt["passed_environment"], expected), f"{path}.passed_environment",
              "passed mapping differs from the policy projection")
    f.require(f.same(receipt["child_environment"], expected), f"{path}.child_environment",
              "child environment differs from the policy projection (inherited, unknown, missing, or changed entry)")
    canary = receipt["parent_canary"]
    f.require(canary["name"] == policy["parent_canary_name"], f"{path}.parent_canary.name", "must equal the policy")
    f.require(canary["present_in_parent"] is True, f"{path}.parent_canary", "parent canary was absent before launch")
    f.require(canary["present_in_child"] is False, f"{path}.parent_canary", "parent canary reached the child")
    f.require(f.timestamp(receipt["started_at"], path) >= f.timestamp(policy["created_at"], path), f"{path}.started_at",
              "launch cannot precede its prospective policy")
    if capture is not None:
        f.closed(capture, f"{path}.capture", ("captured_at", "environment", "phase1_modules_loaded_before_capture"))
        capture_rows = _rows(capture["environment"], f"{path}.capture.environment", ("name", "value"))
        loaded = f.array(capture["phase1_modules_loaded_before_capture"],
                         f"{path}.capture.phase1_modules_loaded_before_capture")
        for index, name in enumerate(loaded):
            f.text(name, f"{path}.capture.phase1_modules_loaded_before_capture[{index}]")
        f.require(capture["captured_at"] == receipt["child_captured_at"], f"{path}.capture.captured_at",
                  "must equal the receipt capture timestamp")
        f.require(f.same(capture_rows, receipt["child_environment"]), f"{path}.capture.environment",
                  "must equal the receipt child environment")
        f.require(loaded == [], f"{path}.capture",
                  "child captured its environment after importing a Phase 1 module")
    return receipt
