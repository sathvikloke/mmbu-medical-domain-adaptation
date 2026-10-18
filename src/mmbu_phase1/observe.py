"""Concrete runtime facts for the prospective condition and the child's observation.

The same functions produce the prospective ``runtime`` object (parent, before
launch) and the observed one (child, during execution), so equality is a real
comparison of independently computed values.  The network guard is an
in-process Python socket block plus a denial probe; it is not an OS sandbox.
"""

from __future__ import annotations

import hashlib
import locale
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
import sysconfig
import time
from typing import Any

from mmbu_phase1 import canonical

PACKAGE_ROOT = Path(__file__).resolve().parent
DEVICE_ID = "cpu0"


def stdlib_root() -> str:
    return os.path.realpath(sysconfig.get_paths()["stdlib"])


def tree_digest(root: str, *, skip_dirs: tuple[str, ...] = ("site-packages", "__pycache__"),
                suffixes: tuple[str, ...] | None = None) -> str:
    """Identity digest of every regular file below ``root`` (relative path + SHA-256)."""
    members = []
    for directory, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in skip_dirs)
        for name in sorted(filenames):
            if name.endswith(".pyc") or (suffixes is not None and not name.endswith(suffixes)):
                continue
            full = os.path.join(directory, name)
            if os.path.islink(full) or not os.path.isfile(full):
                continue
            with open(full, "rb") as handle:
                digest = hashlib.file_digest(handle, "sha256").hexdigest()
            members.append({"path": os.path.relpath(full, root).replace(os.sep, "/"), "sha256": digest})
    members.sort(key=lambda item: item["path"].encode("utf-8"))
    return canonical.value_digest(members)


def file_digest(path: str) -> str:
    with open(path, "rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def software(python_executable: str) -> list[dict]:
    version = platform.python_version()
    rows = [
        {"name": "cpython", "version": version, "artifact_digest": file_digest(python_executable)},
        {"name": "cpython-stdlib", "version": version, "artifact_digest": tree_digest(stdlib_root())},
        {"name": "mmbu_phase1", "version": "phase1a", "artifact_digest": tree_digest(str(PACKAGE_ROOT), suffixes=(".py",))},
    ]
    return sorted(rows, key=lambda row: row["name"].encode("utf-8"))


def loaded_module_violations() -> list[str]:
    """Imported modules whose files lie outside the declared stdlib and package roots."""
    allowed = (stdlib_root() + os.sep, str(PACKAGE_ROOT) + os.sep)
    violations = []
    for name, module in sorted(sys.modules.items()):
        origin = getattr(getattr(module, "__spec__", None), "origin", None) or getattr(module, "__file__", None)
        if not origin or origin in {"built-in", "frozen"} or not os.path.isabs(origin):
            continue
        if not os.path.realpath(origin).startswith(allowed):
            violations.append(name)
    return violations


def filesystem_type(path: str) -> str:
    target = os.path.realpath(path)
    best, kind = "", "unknown"
    if sys.platform.startswith("linux"):
        with open("/proc/self/mounts", encoding="utf-8") as handle:
            for line in handle:
                parts = line.split()
                if len(parts) >= 3:
                    mount = parts[1].replace("\\040", " ")
                    if (target == mount or target.startswith(mount.rstrip("/") + "/")) and len(mount) > len(best):
                        best, kind = mount, parts[2]
        return kind
    output = subprocess.run(["/sbin/mount"], env={}, capture_output=True, text=True, check=True).stdout
    for line in output.splitlines():
        if " on " not in line or " (" not in line:
            continue
        mount = line.split(" on ", 1)[1].rsplit(" (", 1)[0]
        fstype = line.rsplit(" (", 1)[1].split(",", 1)[0].rstrip(")")
        if (target == mount or target.startswith(mount.rstrip("/") + "/")) and len(mount) >= len(best):
            best, kind = mount, fstype
    return kind


def cpu_model() -> str:
    if sys.platform == "darwin":
        result = subprocess.run(["/usr/sbin/sysctl", "-n", "machdep.cpu.brand_string"], env={}, capture_output=True,
                                text=True, check=False)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    try:
        with open("/proc/cpuinfo", encoding="utf-8") as handle:
            for line in handle:
                if line.lower().startswith(("model name", "hardware", "cpu model")):
                    return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.machine() or "unknown-cpu"


def ram_bytes() -> int:
    return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")


def effective_locale() -> str:
    return locale.setlocale(locale.LC_CTYPE)


def runtime(policy: dict, environment_rows: list[dict], *, observed_locale: str | None = None,
            observed_timezone: str | None = None, network: dict | None = None) -> dict:
    """The closed ``runtime`` object for this host and policy."""
    env = {row["name"]: row["value"] for row in environment_rows}
    return {
        "os": policy["platform"],
        "architecture": platform.machine(),
        "python_executable_digest": file_digest(policy["python_executable"]),
        "python_version": platform.python_version(),
        "locale": observed_locale if observed_locale is not None else env["LC_ALL"],
        "timezone": observed_timezone if observed_timezone is not None else env["TZ"],
        "filesystem": filesystem_type(policy["repository_root"]),
        "software": software(policy["python_executable"]),
        "environment_variables": environment_rows,
        "devices": [{"device_id": DEVICE_ID, "device_type": "cpu", "model": cpu_model(), "ordinal": 0,
                     "memory_bytes": ram_bytes()}],
        "topology": {"world_size": 1, "node_count": 1, "process_count": 1, "launcher": None,
                     "visible_device_order": [DEVICE_ID]},
        "cache_network": network or {"cache_root_digests": [], "snapshot_digests": [], "offline_requested": True,
                                     "network_denied": True, "remote_request_count": 0, "hidden_fetch_count": 0,
                                     "request_log_digest": None},
    }


def hardware() -> dict:
    return {"host_id": "host-" + hashlib.sha256(platform.node().encode("utf-8")).hexdigest()[:16],
            "architecture": platform.machine(), "cpu_model": cpu_model(), "cpu_count": os.cpu_count() or 1,
            "ram_bytes": ram_bytes(), "gpu_driver": None, "gpus": [], "scheduler": None}


class NetworkGuard:
    """Block every socket connection/resolution in-process and count attempts."""

    def __init__(self) -> None:
        self.attempts = 0
        self.probe_denied: bool | None = None
        self._saved: dict[str, Any] = {}

    def _deny(self, *args: Any, **kwargs: Any) -> Any:
        self.attempts += 1
        raise OSError("mmbu_phase1 network guard: network access is denied in Phase 1A")

    def install(self) -> "NetworkGuard":
        self._saved = {"connect": socket.socket.connect, "connect_ex": socket.socket.connect_ex,
                       "create_connection": socket.create_connection, "getaddrinfo": socket.getaddrinfo}
        socket.socket.connect = lambda sock, *a, **k: self._deny()  # type: ignore[method-assign]
        socket.socket.connect_ex = lambda sock, *a, **k: self._deny()  # type: ignore[method-assign]
        socket.create_connection = self._deny  # type: ignore[assignment]
        socket.getaddrinfo = self._deny  # type: ignore[assignment]
        return self

    def probe(self) -> bool:
        before = self.attempts
        try:
            socket.create_connection(("127.0.0.1", 9), timeout=1)
            self.probe_denied = False
        except OSError:
            self.probe_denied = True
        self.attempts = before
        return bool(self.probe_denied)

    def cache_network(self) -> dict:
        return {"cache_root_digests": [], "snapshot_digests": [], "offline_requested": True,
                "network_denied": bool(self.probe_denied), "remote_request_count": self.attempts,
                "hidden_fetch_count": self.attempts, "request_log_digest": None}


def utc_wall() -> float:
    return time.time()
