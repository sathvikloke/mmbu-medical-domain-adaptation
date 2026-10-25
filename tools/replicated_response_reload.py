#!/usr/bin/env python3
"""Fresh-process offline reload for one replicated response condition."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mmbu_phase1 import canonical, replicated_response as response
from mmbu_phase1 import fields as f

from replicated_response_screen import ImageStore, evaluate, load_native, load_portfolio, select_populations


def run(args: argparse.Namespace) -> None:
    f.literal({key: os.environ.get(key) for key in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")},
              "response.reload.offline", {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
    manifest = response.load_manifest(Path(args.manifest))
    condition = response.condition_by_index(manifest, args.condition_index)
    candidate = response.candidate_by_id(manifest, condition["candidate_id"])
    portfolio = load_portfolio(Path(args.portfolio))
    populations = select_populations(portfolio, manifest, condition)

    import torch
    from peft import PeftModel

    f.require(torch.cuda.is_available(), "response.reload.cuda", "CUDA unavailable")
    torch.cuda.set_device(0)
    device = torch.device("cuda:0")
    seed = condition["training_seed"] if condition["training_seed"] is not None else manifest["training"]["seeds"][0]
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    processor, model = load_native(Path(args.snapshot_root) / candidate["snapshot_name"], candidate)
    if condition["profile"] != "base":
        f.require(args.adapter is not None, "response.reload.adapter", "adapted condition requires adapter")
        model = PeftModel.from_pretrained(
            model, args.adapter, local_files_only=True, is_trainable=False,
        )
    else:
        f.require(args.adapter is None, "response.reload.adapter", "base condition forbids adapter")
    model.to(device)
    store = ImageStore(Path(args.source_root))
    try:
        predictions, metrics = evaluate(
            model, processor, store, populations["development"], manifest, candidate, device,
        )
    finally:
        store.close()
    result = {
        "candidate_id": candidate["candidate_id"],
        "condition_id": condition["condition_id"],
        "metrics": metrics,
        "network_disabled": True,
        "predictions": predictions,
        "schema_id": "mmbu.biomedical.replicated_response_reload",
        "schema_version": 1,
    }
    Path(args.output).write_bytes(canonical.dumps(result) + b"\n")


def arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--condition-index", required=True, type=int)
    parser.add_argument("--portfolio", required=True)
    parser.add_argument("--snapshot-root", required=True)
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--adapter")
    parser.add_argument("--output", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    run(arguments())
