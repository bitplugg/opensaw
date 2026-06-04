# Выбор модели

## Квантизация

| Уровень | 7B модель | Качество |
|---------|-----------|----------|
| Q8_0 | ~7.2 ГБ | Оригинал |
| Q6_K | ~5.6 ГБ | Почти оригинал |
| Q5_K_M | ~4.8 ГБ | Хорошее |
| Q4_K_M | ~4.1 ГБ | Хорошее |
| Q3_K_M | ~3.3 ГБ | Среднее |
| Q2_K | ~2.7 ГБ | Плохое |

## Рекомендации по CPU/RAM

| CPU | RAM | Модель |
|-----|-----|--------|
| Celeron N5095 | 4 ГБ | Qwen2.5-0.5B-Q8_0 |
| Celeron N5095 | 8 ГБ | Qwen2.5-1.5B-Q8_0 |
| Core i3/i5 | 8 ГБ | Qwen2.5-3B-Q4_K_M |
| Core i5/i7 | 16 ГБ | Qwen2.5-7B-Q4_K_M |
| + NVIDIA GPU | 8+ VRAM | Любая 7B через CUDA |

## Где скачать

[Hugging Face](https://huggingface.co/) — поиск `GGUF Q8_0` или `GGUF Q4_K_M`.

```bash
wget https://huggingface.co/bartowski/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/Qwen2.5-1.5B-Instruct-Q8_0.gguf
opensaw setup  # укажи путь
```
