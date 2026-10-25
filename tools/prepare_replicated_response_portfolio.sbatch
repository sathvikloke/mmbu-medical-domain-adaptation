#!/bin/bash
#SBATCH --job-name=mmbu-response-prep
#SBATCH --partition=epyc-cpu
#SBATCH --qos=u-default
#SBATCH --account=allusers
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=32G
#SBATCH --time=02:00:00

set -euo pipefail
umask 077

module load python/3.12.12

: "${MMBU_REPO_ROOT:?Set MMBU_REPO_ROOT to the staged repository checkout}"
: "${MMBU_RESPONSE_ROOT:?Set MMBU_RESPONSE_ROOT to the fresh scratch run root}"
: "${MMBU_SOURCE_ROOT:?Set MMBU_SOURCE_ROOT to the verified source directory}"
: "${MMBU_PYTHON:?Set MMBU_PYTHON to the pinned virtual-environment Python}"

BUS_BRA="${MMBU_SOURCE_ROOT}/BUSBRA.zip"
PATH_MNIST="${MMBU_SOURCE_ROOT}/pathmnist_224.npz"
OUTPUT="${MMBU_RESPONSE_ROOT}/portfolio/compiled-portfolio.json"

test -f "${BUS_BRA}"
test -f "${PATH_MNIST}"

cd "${MMBU_REPO_ROOT}"
"${MMBU_PYTHON}" -B tools/prepare_replicated_response_portfolio.py \
  --busbra "${BUS_BRA}" \
  --pathmnist "${PATH_MNIST}" \
  --output "${OUTPUT}"
