# Устранение проблем

## SIGILL

**Симптом:** `Illegal instruction`, процесс падает.

**Причина:** Сборка `llama-cpp-python` с AVX на CPU без AVX2.

**Решение:**

```bash
./setup-gguf.sh
```

## OOM / вылетает

Не хватает RAM. Используй модель меньше:

| RAM | Максимум |
|-----|----------|
| 4 ГБ | Qwen2.5-0.5B-Q8_0 |
| 8 ГБ | Qwen2.5-1.5B-Q8_0 |
| 16 ГБ | Qwen2.5-7B-Q4_K_M |

## PyGObject не найден

**Симптом:** GTK не загружается.

**Решение:**

```bash
# Ubuntu/Debian
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0

# Arch
sudo pacman -S python-gobject gtk4
```

## Сборка llama-cpp-python падает

```bash
pip install scikit-build-core flit_core meson-python ninja cmake
pip cache purge
pip install --no-binary :all: --no-build-isolation llama-cpp-python==0.3.25
```

## Ошибка загрузки модели

- Проверь путь: `ls -la /path/to/model.gguf`
- Проверь формат: `file model.gguf` → "GGUF"
- Скачай модель заново
- `opensaw setup` — укажи правильный путь
