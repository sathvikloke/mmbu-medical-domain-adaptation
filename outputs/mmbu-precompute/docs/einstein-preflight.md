# Read-only Einstein worker diagnostic

`tools/einstein_preflight.py` creates a small JSON report from the current Python process and visible NVIDIA tooling. Run it **inside a worker allocation obtained through IT's supported workflow**, after access is restored. It does not connect to Einstein, obtain or verify an allocation, contact a scheduler, install anything, choose training settings or run a model.

From the preparation package directory, using the environment IT supports:

```sh
python3 tools/einstein_preflight.py --output einstein-worker-report-01.json
```

The script is standalone and needs only Python 3.11+ and its standard library for the default report. The output directory must already exist. Every output is created exclusively; an existing file or symlink is refused. Use a new filename for each observation. No previous report is overwritten.

If the supported environment already has PyTorch, an optional query checks CUDA availability and device capabilities in a separate process:

```sh
python3 tools/einstein_preflight.py \
  --torch-cuda --timeout 10 \
  --output einstein-worker-torch-report-01.json
```

This invokes the current interpreter with `-I` for an isolated Python subprocess, then queries `torch.cuda.is_available()`, `device_count()` and `get_device_capability()` plus the package's reported CUDA runtime version. It does not create tensors, load a model, run a forward pass, benchmark memory or train. Driver initialization may occur as part of the capability query. At most 64 devices are queried; a count outside that diagnostic bound is reported as a query error. The default report does not import PyTorch; reading installed package metadata does not execute the packages.

`--timeout` bounds each external query independently. It defaults to 10 seconds and must be finite, greater than zero and no more than 60. With the optional PyTorch probe, two bounded queries can run sequentially. The tool uses no shell command construction, network operation, SSH, download, package installation, permission change, scheduler submission or environment-variable dump. It does not request GPU serial numbers/UUIDs, hostname, job IDs, credentials or private keys. The only intentional persistent change is the requested new report file.

## Report contents

| Field | Meaning |
| --- | --- |
| `python`, `platform` | Python version/implementation and OS system/release/machine; no hostname |
| `packages` | Metadata versions for torch, torchvision, transformers, accelerate, peft, bitsandbytes, safetensors, tokenizers, NumPy and Pillow; missing/error metadata is explicit |
| `nvidia_smi` | Status and exit code from the fixed GPU name, total VRAM and driver query; parsed GPU list only on valid output |
| `scheduler_executables` | Boolean executable presence for selected Slurm, PBS and LSF command names; no scheduler command is executed |
| `torch_cuda` | `not_requested` by default, or the optional subprocess's status, exit code, availability/count/runtime/capability observations |
| `created_at_utc`, `script_sha256` | Local observation timestamp and the script's exact byte hash |
| `readiness_assessed`, `allocation_verified` | Always `false`; these are outside the tool's scope |

The NVIDIA query is exactly:

```text
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader,nounits
```

Its parsed records contain only `name`, `memory_total_mib` and `driver_version`. This is total memory reported by the tool, not free/usable memory, a reservation, the team's quota, available GPU hours or a model-fit estimate. A visible GPU or scheduler executable does not establish permission to use it. Scheduler discovery uses PATH lookup only and does not prove which scheduler, if any, controls the current session.

Probe statuses distinguish observations:

| Status | Interpretation |
| --- | --- |
| `ok` | The requested query completed and its restricted output parsed; no readiness inference |
| `missing_tool` | `nvidia-smi` was not found on this process's PATH |
| `missing_package` | The optional isolated PyTorch subprocess could not import a required module |
| `error` | The query returned a nonzero exit status, or a caught PyTorch query/import exception occurred |
| `execution_error` | The operating system could not start the subprocess; error class is recorded |
| `timeout` | The bounded query did not complete; no GPU availability conclusion is substituted |
| `invalid_output` | Output did not match the expected schema; no raw data or guessed values are included |
| `not_requested` | The optional PyTorch probe was not enabled |

Raw subprocess stdout/stderr are not retained in the report. Only validated fields, exit codes, an error class where available, and whether stderr was present are recorded. This keeps accidental unrequested diagnostic output out of the report. If IT needs additional diagnostics, follow its supported procedure separately.

The script's own exit code **0 means that a report was written**, including reports with missing tools or failed queries. Exit **2** means invalid arguments or failure to create the requested report. Inspect each probe's `status` and `exit_code`; do not use the top-level process exit code as GPU readiness evidence. A missing GPU tool on a laptop or login node does not diagnose a problem on an allocated Einstein worker.

After IT restores access, this report can inform the environment discussion. Source permissions, a settled evaluation contract, real model loading, native image inference, measured memory, model export/reload and run-time/cost measurements remain separate checks. This script does not infer an allocation duration or recommend hyperparameters.

## Local engineering evidence

The script was exercised locally on macOS with no Einstein connection. The default run reported `nvidia_smi.status: missing_tool` and `torch_cuda.status: not_requested`. A second local run used the already existing isolated processor-test environment: the optional torch subprocess returned `status: ok`, `cuda_available: false`, `device_count: 0` and `cuda_runtime_version: null`. Both reports kept `readiness_assessed: false` and `allocation_verified: false`. These are local CPU-only checks, not Einstein worker observations.

Saved outputs are [einstein-preflight-local-cpu.json](../evidence/einstein-preflight-local-cpu.json), [einstein-preflight-local-torch-cpu.json](../evidence/einstein-preflight-local-torch-cpu.json) and [einstein-preflight-execution.json](../evidence/einstein-preflight-execution.json), which preserves command arrays, process exit codes and report hashes. No new environment or dependency was installed for these checks.

Run the synthetic tests from the package directory:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 evidence/einstein-preflight-tests.py
```

The eleven tests cover a missing GPU tool, exact query arguments and parsed fields, nonzero exit retention, timeout handling, malformed output, scheduler discovery without execution, optional isolated torch queries, no default torch import, explicit unknown states, invalid timeout values and preservation of an existing output. Temporary command stubs are used for GPU success/error/timeout cases; no GPU operation is needed. The tests make only those temporary stub files executable. [einstein-preflight-red.txt](../evidence/einstein-preflight-red.txt) records the expected pre-implementation failures and [einstein-preflight-green.txt](../evidence/einstein-preflight-green.txt) records eleven passing tests on Python 3.14.7 with exit 0. The optional local torch query was executed on the existing Python 3.12.14 environment; Python 3.11 runtime behavior has not been separately exercised.
