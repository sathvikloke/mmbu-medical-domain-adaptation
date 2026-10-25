#!/bin/bash
#SBATCH --job-name=mmbu-response
#SBATCH --partition=epyc-gpu
#SBATCH --qos=u-default
#SBATCH --account=allusers
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=96G
#SBATCH --gres=gpu:tesla_a100_80gb:1
#SBATCH --array=0-13%5
#SBATCH --time=04:00:00

set -euo pipefail
umask 077

module load python/3.12.12

: "${MMBU_REPO_ROOT:?Set MMBU_REPO_ROOT to the staged repository checkout}"
: "${MMBU_RESPONSE_ROOT:?Set MMBU_RESPONSE_ROOT to the fresh scratch run root}"
: "${MMBU_SOURCE_ROOT:?Set MMBU_SOURCE_ROOT to the verified source directory}"
: "${MMBU_SNAPSHOT_ROOT:?Set MMBU_SNAPSHOT_ROOT to the verified F0 snapshot directory}"
: "${MMBU_PYTHON:?Set MMBU_PYTHON to the pinned virtual-environment Python}"

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export PYTHONHASHSEED=0

cd "${MMBU_REPO_ROOT}"
"${MMBU_PYTHON}" -B tools/replicated_response_screen.py \
  --manifest config/phase1/replicated-response-screen-2026-10-25.json \
  --condition-index "${SLURM_ARRAY_TASK_ID}" \
  --portfolio "${MMBU_RESPONSE_ROOT}/portfolio/compiled-portfolio.json" \
  --snapshot-root "${MMBU_SNAPSHOT_ROOT}" \
  --source-root "${MMBU_SOURCE_ROOT}" \
  --output-root "${MMBU_RESPONSE_ROOT}/results/condition-${SLURM_ARRAY_TASK_ID}"
