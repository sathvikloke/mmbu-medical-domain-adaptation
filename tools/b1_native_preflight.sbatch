#!/usr/bin/env bash
#SBATCH --job-name=mmbu-b1-native
#SBATCH --partition=epyc-gpu
#SBATCH --account=allusers
#SBATCH --qos=u-default
#SBATCH --gres=gpu:tesla_a100_80gb:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=96G
#SBATCH --time=02:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --output=/storage/home/npl015/mmbu-b1-preflight/2026-10-23-run1/evidence/slurm-%j.out
#SBATCH --error=/storage/home/npl015/mmbu-b1-preflight/2026-10-23-run1/evidence/slurm-%j.err

set -euo pipefail
umask 077

readonly RUN_ROOT=/storage/home/npl015/mmbu-b1-preflight/2026-10-23-run1
readonly CODE_ROOT=${RUN_ROOT}/code
readonly VENV_ROOT=${RUN_ROOT}/venv
readonly OFFLINE_CACHE=/tmp/npl015-mmbu-b1-${SLURM_JOB_ID}

module purge
module load python/3.12.12
test "$(python3 -c 'import platform; print(platform.python_version())')" = 3.12.12
test -x "${VENV_ROOT}/bin/python"
test ! -e "${OFFLINE_CACHE}"
mkdir -m 700 -p "${OFFLINE_CACHE}"

export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=${CODE_ROOT}/src
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export HF_HOME=${OFFLINE_CACHE}
export HUGGINGFACE_HUB_CACHE=${OFFLINE_CACHE}/hub
export TRANSFORMERS_CACHE=${OFFLINE_CACHE}/transformers
export CUBLAS_WORKSPACE_CONFIG=:4096:8
export CUDA_VISIBLE_DEVICES=0

cd "${CODE_ROOT}"
"${VENV_ROOT}/bin/python" -B tools/b1_acquire.py verify
"${VENV_ROOT}/bin/python" -B tools/b1_native_preflight.py
"${VENV_ROOT}/bin/python" -B tools/b1_offline_reload.py
