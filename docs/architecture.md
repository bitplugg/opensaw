# Архитектура

## Схема

```
cli.py (точка входа)
  │
  ├── config.py → config.json
  ├── plugins.py → PluginManager
  │    ├── discover() → .plugin файлы
  │    ├── validate_with_ai(lm) → SAFE/UNSAFE
  │    └── activate() → on_load()
  │
  ├── _run_chat() → TUI (Rich)
  │    └── _run_generation()
  │         ├── POST_INPUT хук
  │         ├── memory.search()
  │         ├── PRE_GENERATION хук
  │         ├── lm.chat() / lm.stream()
  │         │    ├── model.py (transformers / llama.cpp)
  │         │    └── tools.py [CMD][READ][WRITE][LS]
  │         ├── POST_GENERATION хук
  │         └── POST_OUTPUT хук
  │
  ├── opensaw info → дашборд
  └── opensaw serve → server.py → FastAPI
```

## Модули

| Модуль | Назначение |
|--------|-----------|
| `cli.py` | Точка входа, TUI, цикл генерации |
| `plugins.py` | Система плагинов |
| `model.py` | Загрузка модели, инференс |
| `memory_engine.py` | Векторная память |
| `tools.py` | Инструменты AI |
| `config.py` | Конфиг |
| `hardware_scanner.py` | Инфо о железе |
| `server.py` | FastAPI |
| `voice.py` | Голосовой ввод/вывод |
| `opensawcore.py` | SDK для плагинов |

## Поток генерации

```
Пользователь → POST_INPUT хук
    → memory.search → контекст
    → PRE_GENERATION хук
    → OpenSawLM.chat()
        → [CMD] / [READ] / [WRITE] / [LS]
        → PRE_TOOL / POST_TOOL хуки
    → POST_GENERATION хук
    → PRE_OUTPUT хук
    → Рендер
    → POST_OUTPUT хук
```
