#!/bin/bash
set -e

VENV_PYTHON="./venv/bin/python"
VENV_PIP="./venv/bin/pip"
MODEL_REPO="DavidAU/Qwen3-0.6B-heretic-abliterated-uncensored"
MODEL_SHORT="qwen3-0.6b-heretic"
OUTPUT="./models_local/${MODEL_SHORT}-q8_0.gguf"
CONVERTER_DIR="/tmp/llama.cpp"
HUB_CACHE="./datasets_cache"
CONFIG_FILE="./config.py"

echo "╔══════════════════════════════════════════╗"
echo "║    OpenSaw GGUF Build                    ║"
echo "╚══════════════════════════════════════════╝"
echo "Model: ${MODEL_REPO}"
echo ""

# Step 1
echo "──────────────────────────────────────────"
echo "STEP 1: llama-cpp-python (source build)"
echo "──────────────────────────────────────────"
echo "  Installing build deps..."
$VENV_PIP install scikit-build-core setuptools wheel pyproject-metadata flit_core cmake 2>&1 | tail -1
echo "  Compiling (может занять 15-30 мин)..."
CMAKE_ARGS="-DGGML_NATIVE=OFF -DGGML_CPU=ON -DGGML_AVX=OFF -DGGML_AVX2=OFF -DGGML_FMA=OFF -DGGML_SSE3=ON" \
  $VENV_PIP install \
  --no-binary :all: \
  --force-reinstall --no-cache-dir \
  --no-build-isolation \
  llama-cpp-python 2>&1 | tail -3

# Step 2
echo ""
echo "──────────────────────────────────────────"
echo "STEP 2: Conversion dependencies"
echo "──────────────────────────────────────────"
$VENV_PIP install gguf sentencepiece 2>&1 | tail -1

# Step 3
echo ""
echo "──────────────────────────────────────────"
echo "STEP 3: Converter script"
echo "──────────────────────────────────────────"
if [ -d "${CONVERTER_DIR}" ]; then
  echo "  already cloned"
else
  git clone --depth 1 https://github.com/ggml-org/llama.cpp.git "${CONVERTER_DIR}" 2>&1 | tail -1
fi

# Step 4
echo ""
echo "──────────────────────────────────────────"
echo "STEP 4: Download uncensored model"
echo "──────────────────────────────────────────"
$VENV_PYTHON -c "
import os; os.makedirs('${HUB_CACHE}', exist_ok=True)
from huggingface_hub import snapshot_download
snapshot_download('${MODEL_REPO}', cache_dir='${HUB_CACHE}')
print('  done')
" 2>&1

MODEL_DIR=$(find ${HUB_CACHE} -path "*/snapshots/*" -name "model.safetensors" | head -1)
MODEL_DIR=$(dirname "$MODEL_DIR")
echo "  cached at: ${MODEL_DIR}"

# Step 5
echo ""
echo "──────────────────────────────────────────"
echo "STEP 5: Convert → Q8_0 GGUF"
echo "──────────────────────────────────────────"
mkdir -p ./models_local
$VENV_PYTHON ${CONVERTER_DIR}/convert_hf_to_gguf.py \
  --outtype q8_0 \
  --outfile "${OUTPUT}" \
  "${MODEL_DIR}" 2>&1 | grep -E "(INFO.*output|WARNING|ERROR)"

if [ ! -f "${OUTPUT}" ]; then
  echo "[ERROR] Conversion failed"
  exit 1
fi
echo "  created: $(du -h ${OUTPUT} | cut -f1)"

# Step 6
echo ""
echo "──────────────────────────────────────────"
echo "STEP 6: Update config"
echo "──────────────────────────────────────────"
ABSOLUTE_OUTPUT=$(realpath "${OUTPUT}")
sed -i "s|model_name: str = '.*'|model_name: str = '${ABSOLUTE_OUTPUT}'|" "${CONFIG_FILE}"
echo "  config → ${ABSOLUTE_OUTPUT}"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  Done!  Run:  opensaw chat               ║"
echo "╚══════════════════════════════════════════╝"
