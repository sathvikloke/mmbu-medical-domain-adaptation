#!/bin/bash
#SBATCH --job-name=mmbu-source-prep
#SBATCH --partition=epyc-cpu
#SBATCH --qos=u-default
#SBATCH --account=allusers
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=12:00:00

set -euo pipefail
umask 077

module load python/3.12.12

: "${MMBU_REPO_ROOT:?Set MMBU_REPO_ROOT to the staged repository checkout}"
: "${MMBU_LANE1_ROOT:?Set MMBU_LANE1_ROOT to the dedicated scratch run root}"
: "${MMBU_VENV_ROOT:=/storage/home/npl015/mmbu-b1-preflight/2026-10-23-run1/venv}"

SOURCE_ROOT="${MMBU_LANE1_ROOT}/sources"
RUN_ROOT="${MMBU_LANE1_ROOT}/shakedown"
mkdir -p "${SOURCE_ROOT}" "${RUN_ROOT}"

BUS_BRA="${SOURCE_ROOT}/BUSBRA.zip"
PATH_MNIST="${SOURCE_ROOT}/pathmnist_224.npz"

curl --fail --location --retry 4 --continue-at - \
  --output "${BUS_BRA}" \
  https://zenodo.org/api/records/8231412/files/BUSBRA.zip/content
curl --fail --location --retry 4 --continue-at - \
  --output "${PATH_MNIST}" \
  https://zenodo.org/api/records/10519652/files/pathmnist_224.npz/content

printf '%s  %s\n' '1f8b2be6476d58fc97bfb5e5a1ea9bab' "${BUS_BRA}" | md5sum --check --strict
printf '%s  %s\n' '2c51a510bcdc9cf8ddb2af93af1eadec' "${PATH_MNIST}" | md5sum --check --strict

cd "${MMBU_REPO_ROOT}"
"${MMBU_VENV_ROOT}/bin/python" -B tools/prepare_biomedical_portfolio.py \
  --busbra "${BUS_BRA}" \
  --pathmnist "${PATH_MNIST}" \
  --output "${RUN_ROOT}/compiled-portfolio.json"
