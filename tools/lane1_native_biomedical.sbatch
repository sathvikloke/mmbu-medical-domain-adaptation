#!/bin/bash
#SBATCH --job-name=mmbu-lane1
#SBATCH --partition=epyc-gpu
#SBATCH --qos=u-default
#SBATCH --account=allusers
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=96G
#SBATCH --gres=gpu:tesla_a100_80gb:1
#SBATCH --array=0-4%5
#SBATCH --time=06:00:00

set -euo pipefail
umask 077

module load python/3.12.12

: "${MMBU_REPO_ROOT:?Set MMBU_REPO_ROOT to the staged repository checkout}"
: "${MMBU_LANE1_ROOT:?Set MMBU_LANE1_ROOT to the dedicated scratch run root}"
: "${MMBU_VENV_ROOT:=/storage/home/npl015/mmbu-b1-preflight/2026-10-23-run1/venv}"

export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export PYTHONHASHSEED=0

cd "${MMBU_REPO_ROOT}"
"${MMBU_VENV_ROOT}/bin/python" -B tools/lane1_native_biomedical.py \
  --config config/phase1/biomedical-lane1-shakedown.json \
  --arm-index "${SLURM_ARRAY_TASK_ID}" \
  --output-root "${MMBU_LANE1_ROOT}/shakedown/results"
