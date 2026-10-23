#!/usr/bin/env python3
"""Fresh-process, socket-denied reload of the B1 base and exported adapter."""

from __future__ import annotations

import math
import os
from pathlib import Path
import socket
import sys
from typing import Any

from mmbu_phase1 import canonical
from mmbu_phase1 import fields as f
from mmbu_phase1 import b1_preflight


REPO = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO / "config/phase1/b1-mocs-preflight.json"


def install_network_guard() -> None:
    original_socket = socket.socket
    def denied(*args: Any, **kwargs: Any) -> Any:
        raise PermissionError("B1 offline reload forbids all socket connections")
    class DeniedConnectSocket(original_socket):
        def connect(self, *args: Any, **kwargs: Any) -> Any:
            return denied(*args, **kwargs)
        def connect_ex(self, *args: Any, **kwargs: Any) -> Any:
            return denied(*args, **kwargs)
    socket.create_connection = denied
    socket.socket = DeniedConnectSocket


def validate_reload(reference: Any, observed: Any) -> float:
    reference = f.closed(reference, "reload.reference", (
        "fixture_id", "prompt", "input_ids", "attention_mask", "logits_first_32",
        "logit_atol", "pixel_values_sha256",
    ))
    observed = f.closed(observed, "reload.observed", (
        "fixture_id", "input_ids", "attention_mask", "logits_first_32", "pixel_values_sha256",
    ))
    for key in ("fixture_id", "input_ids", "attention_mask", "pixel_values_sha256"):
        f.literal(observed[key], f"reload.observed.{key}", reference[key])
    expected_logits = f.array(reference["logits_first_32"], "reload.reference.logits_first_32", nonempty=True)
    observed_logits = f.array(observed["logits_first_32"], "reload.observed.logits_first_32", nonempty=True)
    f.require(len(observed_logits) == len(expected_logits), "reload.observed.logits_first_32", "length differs")
    tolerance = f.number(reference["logit_atol"], "reload.reference.logit_atol", minimum=0)
    deltas = []
    for index, (expected, actual) in enumerate(zip(expected_logits, observed_logits)):
        f.number(expected, f"reload.reference.logits_first_32[{index}]")
        f.number(actual, f"reload.observed.logits_first_32[{index}]")
        delta = abs(actual - expected)
        f.require(math.isfinite(delta), f"reload.observed.logits_first_32[{index}]", "delta is nonfinite")
        deltas.append(delta)
    maximum = max(deltas)
    f.require(maximum <= tolerance, "reload.observed.logits_first_32", "drift exceeds tolerance")
    return maximum


def run() -> None:
    for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE"):
        f.literal(os.environ.get(key), f"environment.{key}", "1")
    config = b1_preflight.load_preflight_config(CONFIG_PATH)
    evidence_root = Path(config["paths"]["evidence_root"])
    adapter_root = evidence_root / "adapter"
    f.require(adapter_root.is_dir() and not adapter_root.is_symlink(), "adapter", "adapter directory is missing")
    prior = canonical.loads((evidence_root / "native-preflight.json").read_bytes())
    reference = prior["reload_reference"]

    install_network_guard()
    try:
        socket.create_connection(("127.0.0.1", 9), timeout=0.01)
    except PermissionError:
        guard_proven = True
    else:
        f.fail("network_guard", "negative-control connection was not denied")

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import b1_native_preflight as native
    native.verify_adapter_inventory(adapter_root, prior["adapter_files"])
    import torch
    from peft import PeftModel
    from transformers import Qwen2_5_VLForConditionalGeneration

    device = torch.device("cuda:0")
    model_root = Path(config["paths"]["model_root"])
    processor = native.load_pil_processor(model_root)
    processor.tokenizer.padding_side = "left"
    base = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        model_root, local_files_only=True, trust_remote_code=False, torch_dtype=torch.bfloat16,
        attn_implementation="sdpa", device_map=None,
    ).to(device)
    model = PeftModel.from_pretrained(base, adapter_root, is_trainable=False, local_files_only=True).to(device)
    model.eval()
    specs = native.fixture_specs()
    images, _ = native.make_images([specs[0]])
    batch, _ = native._encode(processor, images, [reference["prompt"]])
    inputs = native._device_batch(batch, device)
    with torch.no_grad():
        output = model(**inputs, use_cache=False, return_dict=True)
    observed = {
        "fixture_id": specs[0]["id"],
        "input_ids": batch["input_ids"][0].tolist(),
        "attention_mask": batch["attention_mask"][0].tolist(),
        "logits_first_32": output.logits[0, -1, :32].float().cpu().tolist(),
        "pixel_values_sha256": native._tensor_sha(batch["pixel_values"]),
    }
    maximum = validate_reload(reference, observed)
    receipt = {
        "schema": "mmbu.b1.offline_reload.v1", "status": "passed", "network_guard_proven": guard_proven,
        "base_local_only": True, "adapter_local_only": True, "processor_local_only": True,
        "fresh_process": True, "max_abs_logit_delta": maximum, "logit_atol": reference["logit_atol"],
        "observed": observed,
    }
    (evidence_root / "offline-reload.json").write_bytes(canonical.dumps(receipt) + b"\n")


if __name__ == "__main__":
    try:
        run()
    except f.ContractViolation as exc:
        sys.stderr.write(str(exc) + "\n")
        raise SystemExit(2)
