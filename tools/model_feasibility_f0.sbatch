#!/bin/bash
#SBATCH --job-name=mmbu-f0
#SBATCH --array=0-4%5
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=96G
#SBATCH --gres=gpu:tesla_a100_80gb:1
#SBATCH --time=01:00:00

set -euo pipefail

module load python/3.12.12

: "${F0_REPO:?F0_REPO is required}"
: "${F0_RUN_ROOT:?F0_RUN_ROOT is required}"
: "${F0_SNAPSHOT_ROOT:?F0_SNAPSHOT_ROOT is required}"
: "${F0_PYTHON:?F0_PYTHON is required}"

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false

cd "$F0_REPO"
export PYTHONPATH="$F0_REPO/src"

"$F0_PYTHON" tools/model_feasibility_f0.py \
  --manifest config/phase1/model-feasibility-screen-2026-10-25.json \
  --candidate-index "$SLURM_ARRAY_TASK_ID" \
  --snapshot-root "$F0_SNAPSHOT_ROOT" \
  --output-root "$F0_RUN_ROOT/results/candidate-$SLURM_ARRAY_TASK_ID"
