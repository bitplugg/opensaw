# Система памяти

Три режима: `simple` (TF-IDF), `semantic` (sentence-transformers), `hybrid`.

## Режимы

| Режим | Как работает | Когда |
|-------|-------------|-------|
| `simple` | Поиск по ключевым словам | Быстро, 0.1ms |
| `semantic` | По смыслу (embeddings) | Требует ~500 МБ RAM |
| `hybrid` | Оба сразу | Лучший результат |

## Конфигурация

```json
{
  "memory_backend": "hybrid",
  "n_memory_results": 5,
  "memory_min_score": 0.1
}
```

## Из плагина

```python
from opensawcore import MemoryEngine
mem = MemoryEngine()
mem.add("Пользователь любит Python")
results = mem.search("любимый язык", top_k=3)
# → [{'text': '...', 'score': 0.92}, ...]
```
