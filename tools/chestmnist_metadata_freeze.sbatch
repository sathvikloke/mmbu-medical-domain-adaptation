#!/bin/bash
#SBATCH --job-name=mmbu-chest-meta
#SBATCH --partition=epyc-cpu
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --time=00:30:00

set -euo pipefail
umask 077

: "${CHEST_RUN_ROOT:?CHEST_RUN_ROOT is required}"
: "${CHEST_REPO:?CHEST_REPO is required}"

inputs="${CHEST_RUN_ROOT}/inputs"
outputs="${CHEST_RUN_ROOT}/outputs"
mkdir -p "${inputs}" "${outputs}"

mapping="${inputs}/chestmnist_split_info.csv"
train_val="${inputs}/train_val_list.txt"
test_list="${inputs}/test_list.txt"

test ! -e "${mapping}"
test ! -e "${train_val}"
test ! -e "${test_list}"

curl --fail --location --retry 0 \
  'https://drive.usercontent.google.com/download?id=1eY4En_i6XYWzwzXxI2JKDsFspW-ho__I&export=download&confirm=t' \
  --output "${mapping}"
curl --fail --location --retry 0 \
  'https://nihcc.app.box.com/index.php?rm=box_download_shared_file&shared_name=zx7xbtg7oj9ko9ghmgmsm5zd7tnhhscp&file_id=f_256056636701' \
  --output "${train_val}"
curl --fail --location --retry 0 \
  'https://nihcc.app.box.com/index.php?rm=box_download_shared_file&shared_name=zx7xbtg7oj9ko9ghmgmsm5zd7tnhhscp&file_id=f_256055473534' \
  --output "${test_list}"

test "$(wc -c < "${mapping}")" -eq 2836941
test "$(wc -c < "${train_val}")" -eq 1470907
test "$(wc -c < "${test_list}")" -eq 435131
echo '3cfe66207037f1f99b1bf457f1f009b0cfc2346ea7a710505a23e02c8ff492e9  '"${mapping}" | sha256sum --check --status
echo '61fbe896321c1c1c8b75f3e4f3a08e4fef6486d95ef8a667c31d4d60dca6cb81  '"${train_val}" | sha256sum --check --status
echo '38ca5ef7f756092946f57c1a59faca882ed589a1ab1f72590b45dc06c6d5e1cc  '"${test_list}" | sha256sum --check --status

PYTHONPATH="${CHEST_REPO}/src" python3 "${CHEST_REPO}/tools/audit_chestmnist_mapping.py" \
  --mapping "${mapping}" \
  --train-count 78468 \
  --val-count 11219 \
  --test-count 22433 \
  --patient-count 30805 \
  > "${outputs}/mapping-audit.json"

PYTHONPATH="${CHEST_REPO}/src" python3 "${CHEST_REPO}/tools/freeze_chestmnist_patient_roles.py" \
  --official-train-val "${train_val}" \
  --official-test "${test_list}" \
  --roles-output "${outputs}/patient-roles.csv" \
  --receipt-output "${outputs}/patient-role-freeze-receipt.json"

PYTHONPATH="${CHEST_REPO}/src" python3 "${CHEST_REPO}/tools/compile_chestmnist_development.py" \
  --mapping "${mapping}" \
  --official-train-val "${train_val}" \
  --official-test "${test_list}" \
  --patient-roles "${outputs}/patient-roles.csv" \
  --output "${outputs}/development-manifest.json"

sha256sum "${outputs}/mapping-audit.json" \
  "${outputs}/patient-roles.csv" \
  "${outputs}/patient-role-freeze-receipt.json" \
  "${outputs}/development-manifest.json" \
  > "${outputs}/SHA256SUMS"

printf 'passed\n' > "${outputs}/STATUS"
