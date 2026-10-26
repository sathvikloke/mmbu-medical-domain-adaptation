#!/bin/bash
#SBATCH --job-name=mmbu-f0-acquire
#SBATCH --partition=epyc-cpu
#SBATCH --qos=u-default
#SBATCH --account=allusers
#SBATCH --array=0-4%5
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --time=12:00:00

set -euo pipefail
umask 077

module load python/3.12.12

: "${F0_REPO:?F0_REPO is required}"
: "${F0_RUN_ROOT:?F0_RUN_ROOT is required}"
: "${F0_PYTHON:?F0_PYTHON is required}"

export HF_HOME="$F0_RUN_ROOT/acquisition/hf-home-$SLURM_ARRAY_TASK_ID"
export TOKENIZERS_PARALLELISM=false

cd "$F0_REPO"
export PYTHONPATH="$F0_REPO/src"

"$F0_PYTHON" tools/acquire_model_feasibility_snapshots.py \
  --manifest config/phase1/model-feasibility-screen-2026-10-25.json \
  --candidate-index "$SLURM_ARRAY_TASK_ID" \
  --snapshot-root "$F0_RUN_ROOT/snapshots" \
  --receipt-root "$F0_RUN_ROOT/acquisition/receipts"
