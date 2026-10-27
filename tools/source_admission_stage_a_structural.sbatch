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
: "${STAGE_A_PACKET_SHA256:?STAGE_A_PACKET_SHA256 must bind the acknowledged packet bytes}"
: "${STAGE_A_OWNER_EXTERNAL_POLICY:?owner policy path is required}"
: "${STAGE_A_OWNER_EXTERNAL_POLICY_PIN:?owner policy pin is required}"
: "${STAGE_A_OWNER_EXTERNAL_PUBLIC_KEY:?owner public key path is required}"
: "${STAGE_A_OWNER_EXTERNAL_PUBLIC_KEY_PIN:?owner public key pin is required}"
: "${STAGE_A_OWNER_EXTERNAL_REVOCATION:?owner revocation path is required}"
: "${STAGE_A_OWNER_EXTERNAL_REVOCATION_PIN:?owner revocation pin is required}"
: "${STAGE_A_OWNER_EXTERNAL_SIGNATURE:?owner signature path is required}"
: "${STAGE_A_OWNER_EXTERNAL_PRINCIPAL:?owner principal is required}"
: "${STAGE_A_OWNER_EXTERNAL_SIGNED_AT:?owner signing time is required}"
: "${STAGE_A_OWNER_EXTERNAL_VERIFIER:?owner verifier path is required}"
: "${STAGE_A_OWNER_EXTERNAL_VERIFIER_PIN:?owner verifier pin is required}"
: "${STAGE_A_REVIEWER_EXTERNAL_POLICY:?reviewer policy path is required}"
: "${STAGE_A_REVIEWER_EXTERNAL_POLICY_PIN:?reviewer policy pin is required}"
: "${STAGE_A_REVIEWER_EXTERNAL_PUBLIC_KEY:?reviewer public key path is required}"
: "${STAGE_A_REVIEWER_EXTERNAL_PUBLIC_KEY_PIN:?reviewer public key pin is required}"
: "${STAGE_A_REVIEWER_EXTERNAL_REVOCATION:?reviewer revocation path is required}"
: "${STAGE_A_REVIEWER_EXTERNAL_REVOCATION_PIN:?reviewer revocation pin is required}"
: "${STAGE_A_REVIEWER_EXTERNAL_SIGNATURE:?reviewer signature path is required}"
: "${STAGE_A_REVIEWER_EXTERNAL_PRINCIPAL:?reviewer principal is required}"
: "${STAGE_A_REVIEWER_EXTERNAL_SIGNED_AT:?reviewer signing time is required}"
: "${STAGE_A_REVIEWER_EXTERNAL_VERIFIER:?reviewer verifier path is required}"
: "${STAGE_A_REVIEWER_EXTERNAL_VERIFIER_PIN:?reviewer verifier pin is required}"

readonly source_ids=(bus-bra pathmnist-224 busi-whu)
readonly source_id="${source_ids[${SLURM_ARRAY_TASK_ID:?missing array task ID}]}"
readonly tool="${STAGE_A_RUN_ROOT}/repo/tools/source_admission_stage_a.py"

exec "${STAGE_A_PYTHON}" "${tool}" structural-inspect \
  --packet "${STAGE_A_RUN_ROOT}/records/structural-opening-packet.json" \
  --packet-sha256 "${STAGE_A_PACKET_SHA256}" \
  --evidence-root "${STAGE_A_RUN_ROOT}/records/evidence" \
  --repository-commit "${STAGE_A_RUN_ROOT}/records/repository-commit.txt" \
  --owner-external-policy "${STAGE_A_OWNER_EXTERNAL_POLICY}" \
  --owner-external-policy-pin "${STAGE_A_OWNER_EXTERNAL_POLICY_PIN}" \
  --owner-external-public-key "${STAGE_A_OWNER_EXTERNAL_PUBLIC_KEY}" \
  --owner-external-public-key-pin "${STAGE_A_OWNER_EXTERNAL_PUBLIC_KEY_PIN}" \
  --owner-external-revocation "${STAGE_A_OWNER_EXTERNAL_REVOCATION}" \
  --owner-external-revocation-pin "${STAGE_A_OWNER_EXTERNAL_REVOCATION_PIN}" \
  --owner-external-signature "${STAGE_A_OWNER_EXTERNAL_SIGNATURE}" \
  --owner-external-principal "${STAGE_A_OWNER_EXTERNAL_PRINCIPAL}" \
  --owner-external-signed-at "${STAGE_A_OWNER_EXTERNAL_SIGNED_AT}" \
  --owner-external-verifier "${STAGE_A_OWNER_EXTERNAL_VERIFIER}" \
  --owner-external-verifier-pin "${STAGE_A_OWNER_EXTERNAL_VERIFIER_PIN}" \
  --reviewer-external-policy "${STAGE_A_REVIEWER_EXTERNAL_POLICY}" \
  --reviewer-external-policy-pin "${STAGE_A_REVIEWER_EXTERNAL_POLICY_PIN}" \
  --reviewer-external-public-key "${STAGE_A_REVIEWER_EXTERNAL_PUBLIC_KEY}" \
  --reviewer-external-public-key-pin "${STAGE_A_REVIEWER_EXTERNAL_PUBLIC_KEY_PIN}" \
  --reviewer-external-revocation "${STAGE_A_REVIEWER_EXTERNAL_REVOCATION}" \
  --reviewer-external-revocation-pin "${STAGE_A_REVIEWER_EXTERNAL_REVOCATION_PIN}" \
  --reviewer-external-signature "${STAGE_A_REVIEWER_EXTERNAL_SIGNATURE}" \
  --reviewer-external-principal "${STAGE_A_REVIEWER_EXTERNAL_PRINCIPAL}" \
  --reviewer-external-signed-at "${STAGE_A_REVIEWER_EXTERNAL_SIGNED_AT}" \
  --reviewer-external-verifier "${STAGE_A_REVIEWER_EXTERNAL_VERIFIER}" \
  --reviewer-external-verifier-pin "${STAGE_A_REVIEWER_EXTERNAL_VERIFIER_PIN}" \
  --source-id "${source_id}"
