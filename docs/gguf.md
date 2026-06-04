# GGUF на слабых CPU

Процессоры Celeron N5095/Pentium не имеют AVX2 — стандартная сборка `llama-cpp-python` упадёт с `SIGILL`.

## Автоматическая сборка

```bash
./setup-gguf.sh
./venv/bin/opensaw chat
```

## Что делает скрипт

1. Устанавливает зависимости сборки: `scikit-build-core`, `ninja`, `cmake`
2. Собирает `llama-cpp-python` из исходников:

```bash
CMAKE_ARGS="-DGGML_AVX=OFF -DGGML_AVX2=OFF -DGGML_FMA=OFF -DGGML_SSE3=ON" \
  pip install --no-binary :all: --no-build-isolation llama-cpp-python==0.3.25
```

3. Конвертирует модель в GGUF Q8_0

## Проверка

```bash
objdump -T venv/lib/python*/llama_cpp/libggml-cpu.so | grep -c 'vadd\|vfmadd'
# → 0 (AVX-инструкций нет)
```
