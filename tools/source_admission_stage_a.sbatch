#!/bin/bash
#SBATCH --job-name=mmbu-stage-a
#SBATCH --partition=epyc-cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=08:00:00
#SBATCH --array=0-2%3
#SBATCH --no-requeue

set -euo pipefail

: "${STAGE_A_RUN_ROOT:?STAGE_A_RUN_ROOT must name the sealed scratch root}"
: "${STAGE_A_PYTHON:?STAGE_A_PYTHON must name the sealed measured runtime}"

readonly source_ids=(bus-bra pathmnist-224 busi-whu)
readonly source_id="${source_ids[${SLURM_ARRAY_TASK_ID:?missing array task ID}]}"
readonly tool="${STAGE_A_RUN_ROOT}/repo/tools/source_admission_stage_a.py"
readonly packet="${STAGE_A_RUN_ROOT}/records/acquisition-packet.json"
readonly records="${STAGE_A_RUN_ROOT}/records/acquisition-authority.json"

exec "${STAGE_A_PYTHON}" "${tool}" acquire-source \
  --packet "${packet}" \
  --records "${records}" \
  --source-id "${source_id}"
