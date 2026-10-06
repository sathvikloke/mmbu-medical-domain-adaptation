"""Local synthetic tests for the standalone read-only worker diagnostic."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "tools/einstein_preflight.py"
if SCRIPT.exists():
    spec = importlib.util.spec_from_file_location("einstein_preflight", SCRIPT)
    preflight = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preflight)
else:
    preflight = None


class PreflightTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(preflight, "standalone Einstein diagnostic is not implemented")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def executable(self, code):
        path = self.root / "nvidia-smi"
        path.write_text("#!" + sys.executable + "\n" + code + "\n")
        path.chmod(0o700)  # Only this temporary synthetic test fixture is made executable.
        return str(path)

    def test_missing_gpu_tool_is_explicit_without_fabricated_devices(self):
        with patch.object(preflight.shutil, "which", return_value=None):
            result = preflight.probe_nvidia_smi(timeout=1)
        self.assertEqual(result["status"], "missing_tool")
        self.assertIsNone(result["exit_code"])
        self.assertEqual(result["gpus"], [])

    def test_exact_query_parses_only_gpu_name_memory_and_driver(self):
        path = self.executable("import sys\nassert sys.argv[1:] == ['--query-gpu=name,memory.total,driver_version', '--format=csv,noheader,nounits']\nprint('NVIDIA Synthetic GPU, 40960, 555.42.02')")
        with patch.object(preflight.shutil, "which", return_value=path):
            result = preflight.probe_nvidia_smi(timeout=1)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(result["gpus"], [{"name": "NVIDIA Synthetic GPU", "memory_total_mib": 40960,
                                          "driver_version": "555.42.02"}])
        self.assertNotIn("uuid", json.dumps(result).lower())
        self.assertNotIn("serial", json.dumps(result).lower())

    def test_failed_gpu_query_preserves_exit_without_raw_diagnostics(self):
        path = self.executable("import sys\nprint('UNREQUESTED_RAW_DIAGNOSTIC', file=sys.stderr)\nsys.exit(7)")
        with patch.object(preflight.shutil, "which", return_value=path):
            result = preflight.probe_nvidia_smi(timeout=1)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["exit_code"], 7)
        self.assertTrue(result["stderr_present"])
        self.assertNotIn("UNREQUESTED_RAW_DIAGNOSTIC", json.dumps(result))

    def test_timeout_is_bounded_and_does_not_become_gpu_unavailable_claim(self):
        path = self.executable("import time\ntime.sleep(3)")
        with patch.object(preflight.shutil, "which", return_value=path):
            result = preflight.probe_nvidia_smi(timeout=0.05)
        self.assertEqual(result["status"], "timeout")
        self.assertIsNone(result["exit_code"])
        self.assertEqual(result["gpus"], [])

    def test_malformed_gpu_output_does_not_publish_unrequested_fields(self):
        for output in ("GPU, 80000, 555.1, UNREQUESTED_FIELD", "GPU, unknown, 555.1", ""):
            path = self.executable("print(" + repr(output) + ")")
            with patch.object(preflight.shutil, "which", return_value=path):
                result = preflight.probe_nvidia_smi(timeout=1)
            self.assertEqual(result["status"], "invalid_output")
            self.assertEqual(result["gpus"], [])
            self.assertNotIn("UNREQUESTED_FIELD", json.dumps(result))

    def test_scheduler_discovery_does_not_execute_scheduler_commands(self):
        sentinel = self.root / "scheduler-was-executed"
        path = self.executable("from pathlib import Path\nPath(" + repr(str(sentinel)) + ").write_text('bad')")
        with patch.object(preflight.shutil, "which", return_value=path):
            result = preflight.scheduler_availability()
        self.assertTrue(result["srun"])
        self.assertFalse(sentinel.exists())

    def test_default_report_skips_torch_import_and_never_claims_readiness(self):
        with patch.object(preflight.shutil, "which", return_value=None), patch.object(preflight, "probe_torch_cuda", side_effect=AssertionError("torch must be opt-in")):
            report = preflight.collect_report(torch_cuda=False, timeout=1)
        self.assertEqual(report["torch_cuda"]["status"], "not_requested")
        self.assertFalse(report["readiness_assessed"])
        self.assertFalse(report["allocation_verified"])
        self.assertEqual(report["nvidia_smi"]["status"], "missing_tool")
        for forbidden in ("hostname", "environment_variables", "gpu_hours", "serial", "uuid"):
            self.assertNotIn(forbidden, report)

    def test_optional_torch_query_uses_subprocess_and_validates_result(self):
        completed = subprocess.CompletedProcess([], 0, json.dumps({"status": "ok", "cuda_available": False,
            "device_count": 0, "cuda_runtime_version": None, "devices": []}), "")
        with patch.object(preflight.subprocess, "run", return_value=completed) as runner:
            result = preflight.probe_torch_cuda(timeout=1)
        self.assertEqual(result["status"], "ok")
        self.assertFalse(result["cuda_available"])
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(runner.call_args.args[0][:3], [sys.executable, "-I", "-c"])
        self.assertEqual(runner.call_args.kwargs["timeout"], 1)

    def test_optional_torch_timeout_and_invalid_json_remain_explicit(self):
        with patch.object(preflight.subprocess, "run", side_effect=subprocess.TimeoutExpired("python", 1)):
            self.assertEqual(preflight.probe_torch_cuda(timeout=1)["status"], "timeout")
        completed = subprocess.CompletedProcess([], 0, "unexpected non-JSON", "")
        with patch.object(preflight.subprocess, "run", return_value=completed):
            result = preflight.probe_torch_cuda(timeout=1)
        self.assertEqual(result["status"], "invalid_output")
        self.assertNotIn("unexpected non-JSON", json.dumps(result))

    def test_existing_output_is_never_overwritten(self):
        output = self.root / "report.json"
        output.write_bytes(b"existing report\n")
        result = subprocess.run([sys.executable, str(SCRIPT), "--output", str(output)],
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(output.read_bytes(), b"existing report\n")

    def test_invalid_timeout_fails_before_writing_output(self):
        for value in ("0", "-1", "nan", "inf", "61"):
            output = self.root / (value + ".json")
            result = subprocess.run([sys.executable, str(SCRIPT), "--output", str(output), "--timeout", value],
                                    text=True, capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
