#!/usr/bin/env python3
"""Fresh-process offline reload half of the bounded F0 gate."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from mmbu_phase1 import canonical, model_feasibility
from mmbu_phase1 import fields as f

from model_feasibility_f0 import (
    _device_batch, deterministic_prediction, encode, generated_image, load_native, validate_offline_environment,
)


def run(args: argparse.Namespace) -> None:
    validate_offline_environment(os.environ)
    manifest = model_feasibility.load_manifest(Path(args.manifest))
    candidate = model_feasibility.candidate_by_index(manifest, args.candidate_index)
    import torch
    from peft import PeftModel

    f.require(torch.cuda.is_available(), "f0.reload.cuda", "CUDA unavailable")
    torch.cuda.set_device(0)
    device = torch.device("cuda:0")
    torch.manual_seed(manifest["runtime"]["seed"])
    torch.cuda.manual_seed_all(manifest["runtime"]["seed"])
    torch.use_deterministic_algorithms(manifest["runtime"]["deterministic_algorithms"])
    processor, base = load_native(Path(args.snapshot), candidate)
    model = PeftModel.from_pretrained(base, args.adapter, local_files_only=True, is_trainable=False).to(device)
    image, fixture_sha = generated_image(manifest["fixture"])
    batch, _ = encode(processor, candidate["loader_family"], image, manifest["fixture"]["prompt"], None)
    inputs = _device_batch(batch, device)
    prediction = deterministic_prediction(model, inputs, batch["input_ids"].shape[1])
    result = {
        "candidate_id": candidate["candidate_id"],
        "fixture_sha256": fixture_sha,
        "network_disabled": True,
        "prediction_ids": prediction,
        "schema_id": "mmbu.phase1.model_feasibility_reload",
        "schema_version": 1,
    }
    Path(args.output).write_bytes(canonical.dumps(result) + b"\n")


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--candidate-index", required=True, type=int)
    parser.add_argument("--snapshot", required=True)
    parser.add_argument("--adapter", required=True)
    parser.add_argument("--output", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    run(arguments())
