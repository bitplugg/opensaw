#!/usr/bin/env bash
set -e

LLAMA_DIR="/tmp/llama.cpp"
BUILD_DIR="$LLAMA_DIR/build"
INSTALL_DIR="$LLAMA_DIR/install"
SERVER_BIN="$INSTALL_DIR/bin/llama-server"

if [ -f "$SERVER_BIN" ]; then
    echo "✅ llama-server already built at $SERVER_BIN"
    exit 0
fi

echo ":: Cloning llama.cpp..."
if [ ! -d "$LLAMA_DIR" ]; then
    git clone --depth 1 https://github.com/ggml-org/llama.cpp "$LLAMA_DIR"
fi

echo ":: Building llama.cpp server (SSE3 only, no AVX)..."
mkdir -p "$BUILD_DIR"
cmake -S "$LLAMA_DIR" -B "$BUILD_DIR" \
    -DCMAKE_INSTALL_PREFIX="$INSTALL_DIR" \
    -DGGML_AVX=OFF \
    -DGGML_AVX2=OFF \
    -DGGML_AVX512=OFF \
    -DGGML_FMA=OFF \
    -DGGML_SSE3=ON \
    -DLLAMA_BUILD_SERVER=ON \
    -DLLAMA_BUILD_EXAMPLES=OFF \
    -DLLAMA_BUILD_TESTS=OFF \
    -DCMAKE_C_FLAGS="-mno-avx -mno-avx2 -mno-fma" \
    -DCMAKE_CXX_FLAGS="-mno-avx -mno-avx2 -mno-fma" \
    -DCMAKE_BUILD_TYPE=Release

cmake --build "$BUILD_DIR" --target llama-server -- -j$(nproc)
cmake --install "$BUILD_DIR"

echo ""
echo "✅ llama-server built: $SERVER_BIN"

echo ""
echo ":: Checking for AVX instructions..."
AVX_COUNT=$(objdump -d "$SERVER_BIN" | grep -c 'vadd\|vfmadd' 2>/dev/null || echo 0)
echo "   AVX instructions found: $AVX_COUNT"
if [ "$AVX_COUNT" -eq 0 ]; then
    echo "   ✅ Clean — no AVX instructions"
else
    echo "   ⚠️  AVX instructions present — check CFLAGS"
fi
