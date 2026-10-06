"""Local-only preparation commands. No model execution or network calls."""

import argparse
import json
import math
from pathlib import Path
import sys
import zipfile

from .metrics import score_rows, source_balanced_weights, paired_cluster_bootstrap


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _bad_constant(value):
    raise ValueError(f"Non-finite JSON value: {value}")


def _decode(text):
    def finite_float(literal):
        value = float(literal)
        if not math.isfinite(value):
            raise ValueError("JSON number overflows the finite float range")
        return value
    return json.loads(text, object_pairs_hook=_unique_object, parse_constant=_bad_constant,
                      parse_float=finite_float)


def _load(path):
    return _decode(Path(path).read_text(encoding="utf-8"))


def _rows(path):
    path = Path(path)
    if path.suffix == ".jsonl":
        records = []
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.strip():
                try:
                    records.append(_decode(line))
                except ValueError as exc:
                    raise ValueError(f"{path.name}:{line_number}: {exc}") from exc
        return records
    rows = _load(path)
    if not isinstance(rows, list):
        raise ValueError("Manifest/grades must be a JSON array or .jsonl file")
    return rows


def _parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, default=Path.cwd(), help="Preparation package directory; defaults to current directory")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status", help="Show preparation state and external dependencies")
    commands.add_parser("demo", help="Validate shipped synthetic fixtures; never runs a model")
    score = commands.add_parser("score", help="Arithmetic over explicit pregraded rows; not an evaluator")
    score.add_argument("input", type=Path)
    score.add_argument("--weighting", choices=("natural", "balanced"), default="natural")
    score.add_argument("--bootstrap", type=int, default=0, metavar="DRAWS")
    score.add_argument("--seed", type=int, default=0)
    score.add_argument("--confidence", type=float, default=.95)
    validate = commands.add_parser("validate", help="Check manifest/source/lineage and optional file hashes")
    validate.add_argument("input", type=Path)
    validate.add_argument("--registry", type=Path)
    validate.add_argument("--image-root", type=Path)
    validate.add_argument("--purpose", choices=("engineering", "train", "dev", "confirmation", "official_dev"), default="engineering")
    split = commands.add_parser("split", help="Assign approved external lineage groups to named splits")
    split.add_argument("input", type=Path)
    split.add_argument("--registry", type=Path)
    split.add_argument("--image-root", type=Path)
    split.add_argument("--ratios", required=True, help='JSON object, for example {"train":0.8,"dev":0.1,"confirmation":0.1}')
    split.add_argument("--seed", type=int, required=True)
    split.add_argument("--output", type=Path, required=True, help="New file; refuses to overwrite an existing manifest")
    compare = commands.add_parser("compare", help="Joint paired candidate comparison over supplied grades")
    compare.add_argument("input", type=Path, help="JSON object mapping candidate names to grade arrays")
    compare.add_argument("--weights", type=Path, help="Optional JSON mapping record IDs to positive weights")
    compare.add_argument("--bootstrap", type=int, default=1000)
    compare.add_argument("--seed", type=int, default=0)
    compare.add_argument("--confidence", type=float, default=.95)
    diagnose = commands.add_parser("diagnose", help="Task/source and fixed-weight sensitivity over candidate grades")
    diagnose.add_argument("input", type=Path)
    diagnose.add_argument("--bootstrap", type=int, default=1000)
    diagnose.add_argument("--seed", type=int, default=0)
    diagnose.add_argument("--confidence", type=float, default=.95)
    calibrate = commands.add_parser("calibrate", help="Compare supplied judge and human grades by sampling frame")
    calibrate.add_argument("input", type=Path)
    inspect = commands.add_parser("inspect-images", help="Decode and inspect images with optional Pillow")
    inspect.add_argument("input", type=Path)
    inspect.add_argument("--image-root", type=Path, required=True)
    inspect.add_argument("--max-pixels", type=int, default=40_000_000)
    duplicates = commands.add_parser("near-duplicates", help="Read-only perceptual candidate triage; no automatic merging")
    duplicates.add_argument("input", type=Path)
    duplicates.add_argument("--image-root", type=Path, required=True)
    duplicates.add_argument("--max-distance", type=int, default=4)
    duplicates.add_argument("--max-aspect-ratio-difference", type=float, default=.05)
    intake = commands.add_parser("prepare-bbbc039", help="Quarantine source-training conversion from local official archives")
    intake.add_argument("archives", type=Path)
    intake.add_argument("--output", type=Path, required=True, help="New output directory; never overwrites")
    from ._cli_experiments import add_commands
    add_commands(commands)
    return parser


def _execute(args):
    workspace = args.workspace.resolve()
    if args.command in ("experiment-validate", "receipt-create", "receipt-verify") or args.command.startswith("confirmation-"):
        from ._cli_experiments import execute
        return execute(args, _load)
    if args.command == "status":
        protocol = _load(workspace / "configs/protocol-register.json")
        registry = _load(workspace / "configs/source-registry.json")
        resources = _load(workspace / "configs/resources.json")
        return {"scope": "CPU preparation only", "training_ready": False,
                "protocol_status": protocol["status"], "gpu": resources["gpu"],
                "sources": [{"source_id": s["source_id"], "status": s["status"], "allowed_purposes": s["allowed_purposes"]} for s in registry["sources"]],
                "remaining_gates": ["authoritative evaluation contract", "accepted biomedical source/record review", "GPU access and runtime verification", "native model load and BF16/FP16 export check"]}, 0
    if args.command == "score":
        if args.bootstrap < 0:
            raise ValueError("--bootstrap must be nonnegative")
        rows = _rows(args.input)
        weights = source_balanced_weights(rows) if args.weighting == "balanced" else None
        result = {"official_evaluation": False, "weighting": args.weighting,
                  "score": score_rows(rows, weights=weights),
                  "limits": ["Grades were supplied by the caller; no semantic judging occurred.", "No estimate of hidden leaderboard performance."]}
        if args.bootstrap:
            result["bootstrap"] = paired_cluster_bootstrap(rows, weights=weights,
                iterations=args.bootstrap, seed=args.seed, confidence=args.confidence)
        return result, 0
    if args.command == "compare":
        from .comparison import compare_candidates
        result = compare_candidates(_load(args.input), weights=_load(args.weights) if args.weights else None,
                                    iterations=args.bootstrap, seed=args.seed, confidence=args.confidence)
        return {"official_evaluation": False, "comparison": result}, 0
    if args.command == "diagnose":
        from .diagnostics import diagnose_candidates
        return diagnose_candidates(_load(args.input), iterations=args.bootstrap, seed=args.seed,
                                   confidence=args.confidence), 0
    if args.command == "calibrate":
        from .diagnostics import calibration_report
        return calibration_report(_rows(args.input)), 0
    if args.command == "inspect-images":
        from .images import inspect_images
        result = inspect_images(_rows(args.input), image_root=args.image_root, max_pixels=args.max_pixels)
        return result, 0 if result["ok"] else 2
    if args.command == "near-duplicates":
        from .duplicates import triage_duplicates
        return triage_duplicates(_rows(args.input), image_root=args.image_root,
                                 max_distance=args.max_distance,
                                 max_aspect_ratio_difference=args.max_aspect_ratio_difference), 0
    if args.command == "prepare-bbbc039":
        from .bbbc039 import prepare_quarantine
        return prepare_quarantine(args.archives, args.output), 0
    from .data import validate_manifest, assign_splits
    registry_path = getattr(args, "registry", None) or workspace / "configs/source-registry.json"
    registry = _load(registry_path)
    if args.command == "validate":
        result = validate_manifest(_rows(args.input), registry, image_root=args.image_root, purpose=args.purpose)
        return result, 0 if result["ok"] else 2
    if args.command == "split":
        rows = _rows(args.input)
        ratios = _decode(args.ratios)
        assigned = assign_splits(rows, registry=registry, seed=args.seed, ratios=ratios)
        validation = {}
        for split in sorted({record["split"] for record in assigned}):
            partition = [record for record in assigned if record["split"] == split]
            validation[split] = validate_manifest(partition, registry, image_root=args.image_root, purpose=split)
            if not validation[split]["ok"]:
                return validation[split], 2
        # Exclusive creation prevents accidentally replacing a frozen split file.
        with args.output.open("x", encoding="utf-8") as stream:
            for record in assigned:
                stream.write(json.dumps(record, allow_nan=False, sort_keys=True) + "\n")
        return {"output": str(args.output), "records": len(assigned), "seed": args.seed, "validation": validation,
                "note": "Assignment is not sufficient evidence of independence or source-transfer performance."}, 0
    if args.command == "demo":
        from .contracts import parse_task_output, box_iou
        manifest = validate_manifest(_rows(workspace / "examples/engineering-manifest.jsonl"), registry,
                                     image_root=workspace / "examples", purpose="engineering")
        scores = score_rows(_rows(workspace / "examples/pregraded-toy.jsonl"))
        parsing = {"brief_json": parse_task_output('{"answer":"shape","rationale":"Engineering fixture."}', "brief_json"),
                   "public_card": parse_task_output('Engineering fixture.\n{"answer":"shape"}', "public_card")}
        iou = box_iou([0, 0, 3, 2], [1, 0, 3, 2])
        ok = manifest["ok"] and all(p["ok"] for p in parsing.values()) and iou == .5
        return {"kind": "synthetic_engineering_demo", "official_evaluation": False, "model_executed": False,
                "manifest": manifest, "pregraded_toy_score": scores, "parser_diagnostics": parsing,
                "hand_checked_iou": iou, "ok": ok}, 0 if ok else 2
    raise ValueError("Unknown command")


def main(argv=None):
    args = _parser().parse_args(argv)
    try:
        result, code = _execute(args)
        print(json.dumps(result, indent=2, sort_keys=True, allow_nan=False))
        return code
    except (OSError, ValueError, TypeError, KeyError, OverflowError, zipfile.BadZipFile) as exc:
        print(json.dumps({"error": str(exc), "command": args.command}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
