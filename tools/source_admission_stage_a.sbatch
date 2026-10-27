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
: "${STAGE_A_ACQUISITION_EXTERNAL_POLICY:?acquisition policy path is required}"
: "${STAGE_A_ACQUISITION_EXTERNAL_POLICY_PIN:?acquisition policy pin is required}"
: "${STAGE_A_ACQUISITION_EXTERNAL_PUBLIC_KEY:?acquisition public key path is required}"
: "${STAGE_A_ACQUISITION_EXTERNAL_PUBLIC_KEY_PIN:?acquisition public key pin is required}"
: "${STAGE_A_ACQUISITION_EXTERNAL_REVOCATION:?acquisition revocation path is required}"
: "${STAGE_A_ACQUISITION_EXTERNAL_REVOCATION_PIN:?acquisition revocation pin is required}"
: "${STAGE_A_ACQUISITION_EXTERNAL_SIGNATURE:?acquisition signature path is required}"
: "${STAGE_A_ACQUISITION_EXTERNAL_PRINCIPAL:?acquisition principal is required}"
: "${STAGE_A_ACQUISITION_EXTERNAL_SIGNED_AT:?acquisition signing time is required}"
: "${STAGE_A_ACQUISITION_EXTERNAL_VERIFIER:?acquisition verifier path is required}"
: "${STAGE_A_ACQUISITION_EXTERNAL_VERIFIER_PIN:?acquisition verifier pin is required}"

readonly source_ids=(bus-bra pathmnist-224 busi-whu)
readonly source_id="${source_ids[${SLURM_ARRAY_TASK_ID:?missing array task ID}]}"
readonly tool="${STAGE_A_RUN_ROOT}/repo/tools/source_admission_stage_a.py"
readonly packet="${STAGE_A_RUN_ROOT}/records/acquisition-packet.json"
readonly records="${STAGE_A_RUN_ROOT}/records/acquisition-authority.json"

exec "${STAGE_A_PYTHON}" "${tool}" acquire-source \
  --packet "${packet}" \
  --records "${records}" \
  --acquisition-external-policy "${STAGE_A_ACQUISITION_EXTERNAL_POLICY}" \
  --acquisition-external-policy-pin "${STAGE_A_ACQUISITION_EXTERNAL_POLICY_PIN}" \
  --acquisition-external-public-key "${STAGE_A_ACQUISITION_EXTERNAL_PUBLIC_KEY}" \
  --acquisition-external-public-key-pin "${STAGE_A_ACQUISITION_EXTERNAL_PUBLIC_KEY_PIN}" \
  --acquisition-external-revocation "${STAGE_A_ACQUISITION_EXTERNAL_REVOCATION}" \
  --acquisition-external-revocation-pin "${STAGE_A_ACQUISITION_EXTERNAL_REVOCATION_PIN}" \
  --acquisition-external-signature "${STAGE_A_ACQUISITION_EXTERNAL_SIGNATURE}" \
  --acquisition-external-principal "${STAGE_A_ACQUISITION_EXTERNAL_PRINCIPAL}" \
  --acquisition-external-signed-at "${STAGE_A_ACQUISITION_EXTERNAL_SIGNED_AT}" \
  --acquisition-external-verifier "${STAGE_A_ACQUISITION_EXTERNAL_VERIFIER}" \
  --acquisition-external-verifier-pin "${STAGE_A_ACQUISITION_EXTERNAL_VERIFIER_PIN}" \
  --source-id "${source_id}"
