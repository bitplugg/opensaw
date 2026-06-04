#!/bin/bash
# Run in background: nohup ./build_gguf.sh &
LOG="./build_gguf.log"
echo "=== Build started $(date) ===" > "$LOG"

# Need build deps for --no-build-isolation
echo "Installing build deps..." >> "$LOG"
./venv/bin/pip install scikit-build-core setuptools wheel pyproject-metadata flit_core 'meson-python>=0.13' ninja cmake 2>&1 | tee -a "$LOG"

echo "Building llama-cpp-python..." >> "$LOG"
CMAKE_ARGS="-DGGML_NATIVE=OFF -DGGML_CPU=ON -DGGML_AVX=OFF -DGGML_AVX2=OFF -DGGML_FMA=OFF -DGGML_SSE3=ON" \
  ./venv/bin/pip install \
  --no-binary :all: \
  --force-reinstall --no-cache-dir \
  --no-build-isolation \
  llama-cpp-python 2>&1 | tee -a "$LOG"

echo "=== Build finished $(date) ===" >> "$LOG"
