#!/usr/bin/env python3
"""Read-only diagnostics to run inside an already allocated Einstein worker.

No SSH, scheduler invocation, installation, network, model/tensor execution,
environment-variable dump, GPU serial/UUID query, or permission changes.
Writing one new JSON report is the only intentional persistent change.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import io
import json
import math
from pathlib import Path
import platform
import re
import shutil
import subprocess
import sys


PACKAGES = ("torch", "torchvision", "transformers", "accelerate", "peft",
            "bitsandbytes", "safetensors", "tokenizers", "numpy", "Pillow")
SCHEDULERS = ("srun", "sbatch", "salloc", "sinfo", "squeue", "qsub", "qstat", "bsub", "bjobs")
GPU_ARGUMENTS = ["--query-gpu=name,memory.total,driver_version", "--format=csv,noheader,nounits"]

_TORCH_QUERY = '''import json, sys
try:
    import torch
except ModuleNotFoundError:
    print(json.dumps({"status": "missing_package"}))
    sys.exit(2)
except Exception as exc:
    print(json.dumps({"status": "error", "error_type": type(exc).__name__}))
    sys.exit(2)
try:
    available = bool(torch.cuda.is_available())
    count = int(torch.cuda.device_count())
    if count < 0 or count > 64:
        raise ValueError("device count outside diagnostic bound")
    devices = [{"index": index, "capability": list(torch.cuda.get_device_capability(index))}
               for index in range(count)] if available else []
    print(json.dumps({"status": "ok", "cuda_available": available, "device_count": count,
                      "cuda_runtime_version": torch.version.cuda, "devices": devices}))
except Exception as exc:
    print(json.dumps({"status": "error", "error_type": type(exc).__name__}))
    sys.exit(2)
'''


def _timeout(value):
    try:
        value = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError("timeout must be a finite number in (0, 60]") from exc
    if not math.isfinite(value) or not 0 < value <= 60:
        raise ValueError("timeout must be a finite number in (0, 60]")
    return value


def _run(command, timeout):
    """Run one fixed query; raw output stays internal and is never a report field."""
    try:
        process = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, text=True, errors="replace",
                                 timeout=_timeout(timeout), check=False)
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "exit_code": None, "stderr_present": None}, None
    except OSError as exc:
        return {"status": "execution_error", "exit_code": None, "error_type": type(exc).__name__,
                "stderr_present": None}, None
    return {"status": "ok" if process.returncode == 0 else "error", "exit_code": process.returncode,
            "stderr_present": bool(process.stderr)}, process.stdout


def probe_nvidia_smi(*, timeout):
    """Query only name, total memory MiB and driver, with no device identifiers."""
    _timeout(timeout)
    executable = shutil.which("nvidia-smi")
    if executable is None:
        return {"status": "missing_tool", "exit_code": None, "gpus": []}
    result, stdout = _run([executable, *GPU_ARGUMENTS], timeout)
    result["gpus"] = []
    if result["status"] != "ok":
        return result
    try:
        rows = list(csv.reader(io.StringIO(stdout)))
        if not rows:
            raise ValueError("no GPU rows")
        devices = []
        for row in rows:
            if len(row) != 3:
                raise ValueError("unexpected GPU columns")
            name, memory, driver = (value.strip() for value in row)
            if not name or len(name) > 200 or not memory.isdigit() or int(memory) <= 0:
                raise ValueError("invalid name or total memory")
            if not re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,3}", driver):
                raise ValueError("invalid driver version")
            devices.append({"name": name, "memory_total_mib": int(memory), "driver_version": driver})
        result["gpus"] = devices
    except (csv.Error, TypeError, ValueError):
        result["status"] = "invalid_output"
    return result


def scheduler_availability():
    """Discover executable names only; never contact a scheduler or submit work."""
    return {name: shutil.which(name) is not None for name in SCHEDULERS}


def _torch_payload(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result
    def nonfinite(value):
        raise ValueError("nonfinite value")
    data = json.loads(raw, object_pairs_hook=unique, parse_constant=nonfinite)
    if not isinstance(data, dict):
        raise ValueError("expected object")
    if data == {"status": "missing_package"}:
        return data
    if set(data) == {"status", "error_type"} and data["status"] == "error":
        if not isinstance(data["error_type"], str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", data["error_type"]):
            raise ValueError("invalid error type")
        return data
    if set(data) != {"status", "cuda_available", "device_count", "cuda_runtime_version", "devices"} or data["status"] != "ok":
        raise ValueError("unexpected torch fields")
    count, available, version, devices = (data[k] for k in ("device_count", "cuda_available", "cuda_runtime_version", "devices"))
    if type(available) is not bool or type(count) is not int or not 0 <= count <= 64 or not isinstance(devices, list):
        raise ValueError("invalid CUDA availability/count/devices")
    if version is not None and (not isinstance(version, str) or not re.fullmatch(r"[0-9]+(?:\.[0-9]+){1,3}", version)):
        raise ValueError("invalid CUDA runtime version")
    if len(devices) != (count if available else 0):
        raise ValueError("device results do not match availability/count")
    for index, device in enumerate(devices):
        if not isinstance(device, dict) or set(device) != {"index", "capability"} or type(device["index"]) is not int or device["index"] != index:
            raise ValueError("invalid device index")
        capability = device["capability"]
        if not isinstance(capability, list) or len(capability) != 2 or any(type(v) is not int or v < 0 for v in capability):
            raise ValueError("invalid CUDA capability")
    return data


def probe_torch_cuda(*, timeout):
    """Opt-in bounded query in an isolated subprocess; no tensor allocation."""
    result, stdout = _run([sys.executable, "-I", "-c", _TORCH_QUERY], timeout)
    if stdout is None:
        return result
    try:
        payload = _torch_payload(stdout)
        if (result["exit_code"] == 0) != (payload["status"] == "ok"):
            raise ValueError("torch status and exit code disagree")
        result.update(payload)
    except (ValueError, TypeError, KeyError):
        result["status"] = "invalid_output"
    return result


def collect_report(*, torch_cuda, timeout):
    """Collect observations, without inferring allocation, GPU hours or readiness."""
    timeout = _timeout(timeout)
    packages = {}
    for name in PACKAGES:
        try:
            packages[name] = {"status": "installed", "version": importlib.metadata.version(name)}
        except importlib.metadata.PackageNotFoundError:
            packages[name] = {"status": "missing", "version": None}
        except Exception as exc:
            packages[name] = {"status": "metadata_error", "version": None, "error_type": type(exc).__name__}
    return {
        "schema_version": 1, "kind": "einstein_read_only_worker_diagnostic",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "readiness_assessed": False, "allocation_verified": False,
        "python": {"version": platform.python_version(), "implementation": platform.python_implementation()},
        "platform": {"system": platform.system(), "release": platform.release(), "machine": platform.machine()},
        "packages": packages, "query_timeout_seconds": timeout,
        "nvidia_smi": probe_nvidia_smi(timeout=timeout),
        "scheduler_executables": scheduler_availability(),
        "torch_cuda": probe_torch_cuda(timeout=timeout) if torch_cuda else {"status": "not_requested"},
        "interpretation": "Observations from this process only; no worker allocation, usable GPU memory, GPU hours, model fit, or training readiness inferred.",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New JSON path in an existing directory; never overwrites")
    parser.add_argument("--torch-cuda", action="store_true", help="Opt in to a subprocess CUDA availability/capability query; no tensors")
    parser.add_argument("--timeout", default=10.0, type=float, help="Seconds per query, greater than zero and at most 60 (default: 10)")
    args = parser.parse_args(argv)
    try:
        _timeout(args.timeout)
        if args.output.exists() or args.output.is_symlink():
            raise FileExistsError("output already exists")
        report = collect_report(torch_cuda=args.torch_cuda, timeout=args.timeout)
        encoded = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(encoded)
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "report_not_written", "error_type": type(exc).__name__, "error": str(exc)}), file=sys.stderr)
        return 2
    print(json.dumps({"status": "report_written", "output": str(args.output), "readiness_assessed": False}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
