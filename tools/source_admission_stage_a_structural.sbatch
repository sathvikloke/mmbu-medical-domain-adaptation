#!/bin/bash
#SBATCH --job-name=mmbu-stage-a-structural
#SBATCH --partition=epyc-cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=02:00:00
#SBATCH --array=0-2%3
#SBATCH --no-requeue

set -euo pipefail

: "${STAGE_A_RUN_ROOT:?STAGE_A_RUN_ROOT must name the sealed structural root}"
: "${STAGE_A_PYTHON:?STAGE_A_PYTHON must name the sealed measured runtime}"

readonly source_ids=(bus-bra pathmnist-224 busi-whu)
readonly source_id="${source_ids[${SLURM_ARRAY_TASK_ID:?missing array task ID}]}"
readonly tool="${STAGE_A_RUN_ROOT}/repo/tools/source_admission_stage_a.py"

exec "${STAGE_A_PYTHON}" "${tool}" structural-inspect \
  --packet "${STAGE_A_RUN_ROOT}/records/structural-opening-packet.json" \
  --packet-sha256 "eb8dba78a2de705b84b0120153a21fcc82b156137d6a81ff8c52512ea16952c1" \
  --evidence-root "${STAGE_A_RUN_ROOT}/records/evidence" \
  --repository-commit "${STAGE_A_RUN_ROOT}/records/repository-commit.txt" \
  --owner-statement "${STAGE_A_RUN_ROOT}/records/owner-statement.txt" \
  --reviewer-statement "${STAGE_A_RUN_ROOT}/records/reviewer-statement.txt" \
  --source-id "${source_id}"
