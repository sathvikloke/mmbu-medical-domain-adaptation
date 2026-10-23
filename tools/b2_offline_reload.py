#!/usr/bin/env python3
"""Fresh-process, socket-denied reload of the B2-P adapter."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
import socket
import sys
from typing import Any

from mmbu_phase1 import b2_preflight
from mmbu_phase1 import canonical
from mmbu_phase1 import fields as f


REPO = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO / "config/phase1/b2-mocs-preflight.json"


def install_network_guard() -> None:
    original_socket = socket.socket

    def denied(*args: Any, **kwargs: Any) -> Any:
        raise PermissionError("B2 offline reload forbids all socket connections")

    class DeniedConnectSocket(original_socket):
        def connect(self, *args: Any, **kwargs: Any) -> Any:
            return denied(*args, **kwargs)

        def connect_ex(self, *args: Any, **kwargs: Any) -> Any:
            return denied(*args, **kwargs)

    socket.create_connection = denied
    socket.socket = DeniedConnectSocket


def validate_reload(reference: Any, observed: Any) -> float:
    reference = f.closed(reference, "b2.reload.reference", (
        "fixture_id", "prompt", "input_ids", "attention_mask", "logits_first_32",
        "logit_atol", "pixel_values_sha256",
    ))
    observed = f.closed(observed, "b2.reload.observed", (
        "fixture_id", "input_ids", "attention_mask", "logits_first_32", "pixel_values_sha256",
    ))
    for key in ("fixture_id", "input_ids", "attention_mask", "pixel_values_sha256"):
        f.literal(observed[key], f"b2.reload.observed.{key}", reference[key])
    expected = f.array(reference["logits_first_32"], "b2.reload.reference.logits_first_32", nonempty=True)
    actual = f.array(observed["logits_first_32"], "b2.reload.observed.logits_first_32", nonempty=True)
    f.require(len(actual) == len(expected), "b2.reload.observed.logits_first_32", "length differs")
    tolerance = f.number(reference["logit_atol"], "b2.reload.reference.logit_atol", minimum=0)
    deltas = []
    for index, (left, right) in enumerate(zip(expected, actual)):
        f.number(left, f"b2.reload.reference.logits_first_32[{index}]")
        f.number(right, f"b2.reload.observed.logits_first_32[{index}]")
        delta = abs(left - right)
        f.require(math.isfinite(delta), f"b2.reload.observed.logits_first_32[{index}]", "delta is nonfinite")
        deltas.append(delta)
    maximum = max(deltas)
    f.require(maximum <= tolerance, "b2.reload.observed.logits_first_32", "drift exceeds tolerance")
    return maximum


def run() -> None:
    for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE"):
        f.literal(os.environ.get(key), f"environment.{key}", "1")
    config = b2_preflight.load_preflight_config(CONFIG_PATH)
    evidence_root = Path(config["paths"]["evidence_root"])
    adapter_root = evidence_root / "adapter"
    f.require(adapter_root.is_dir() and not adapter_root.is_symlink(), "b2.adapter", "adapter directory is missing")
    prior = canonical.loads((evidence_root / "native-preflight.json").read_bytes())
    reference = prior["reload_reference"]

    install_network_guard()
    try:
        socket.create_connection(("127.0.0.1", 9), timeout=0.01)
    except PermissionError:
        guard_proven = True
    else:
        f.fail("b2.network_guard", "negative-control connection was not denied")

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import b1_native_preflight as b1_native
    import b2_native_preflight as b2_native
    b1_native.verify_adapter_inventory(adapter_root, prior["adapter_files"])

    import torch
    from peft import PeftModel
    from safetensors import safe_open
    from transformers import Qwen2_5_VLForConditionalGeneration

    device = torch.device("cuda:0")
    model_root = Path(config["paths"]["model_root"])
    processor = b1_native.load_pil_processor(model_root)
    processor.tokenizer.padding_side = "left"
    base = Qwen2_5_VLForConditionalGeneration.from_pretrained(
        model_root, local_files_only=True, trust_remote_code=False,
        torch_dtype=torch.bfloat16, attn_implementation="sdpa", device_map=None,
    ).to(device)
    targets = b1_native.exact_lora_targets(name for name, _ in base.named_modules())
    projector = sorted(
        name for name, _ in base.named_parameters()
        if name.startswith(config["architecture"]["projector_module"] + ".")
    )
    f.literal(projector, "b2.reload.projector", config["architecture"]["projector_parameters"])
    saved_config = json.loads((adapter_root / "adapter_config.json").read_text(encoding="utf-8"))
    b1_native.validate_adapter_scope(saved_config, targets, str(model_root))
    f.literal(saved_config.get("modules_to_save"), "b2.reload.modules_to_save", config["architecture"]["modules_to_save"])
    with safe_open(adapter_root / "adapter_model.safetensors", framework="pt", device="cpu") as stream:
        b2_native.validate_adapter_state_keys(list(stream.keys()), targets, projector)

    model = PeftModel.from_pretrained(
        base, adapter_root, is_trainable=False, local_files_only=True,
    ).to(device)
    model.eval()
    specs = b1_native.fixture_specs()
    images, _ = b1_native.make_images([specs[0]])
    batch, _ = b1_native._encode(processor, images, [reference["prompt"]])
    inputs = b1_native._device_batch(batch, device)
    with torch.no_grad():
        output = model(**inputs, use_cache=False, return_dict=True)
    observed = {
        "fixture_id": specs[0]["id"],
        "input_ids": batch["input_ids"][0].tolist(),
        "attention_mask": batch["attention_mask"][0].tolist(),
        "logits_first_32": output.logits[0, -1, :32].float().cpu().tolist(),
        "pixel_values_sha256": b1_native._tensor_sha(batch["pixel_values"]),
    }
    maximum = validate_reload(reference, observed)
    receipt = {
        "schema": "mmbu.b2.projector_offline_reload.v1",
        "status": "passed",
        "network_guard_proven": guard_proven,
        "base_local_only": True,
        "adapter_local_only": True,
        "processor_local_only": True,
        "fresh_process": True,
        "max_abs_logit_delta": maximum,
        "logit_atol": reference["logit_atol"],
        "observed": observed,
    }
    (evidence_root / "offline-reload.json").write_bytes(canonical.dumps(receipt) + b"\n")


if __name__ == "__main__":
    try:
        run()
    except f.ContractViolation as exc:
        sys.stderr.write(str(exc) + "\n")
        raise SystemExit(2)
