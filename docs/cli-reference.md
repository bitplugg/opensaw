# CLI Reference

```bash
opensaw [OPTIONS] COMMAND [ARGS]...
```

## Команды

### `opensaw setup`

Интерактивная настройка: имя, модель, бекенд, память.

### `opensaw chat`

TUI-чат с AI.

| Команда | Действие |
|---------|----------|
| `/exit` | Выйти |
| `/help` | Список команд |
| `/regen` | Перегенерировать ответ |
| `/edit <текст>` | Заменить последнее |
| `/cont` | Продолжить |
| `/search <запрос>` | Поиск по памяти |
| `/export` | Экспорт в файл |
| `/pin` / `/unpin` | Закрепить/открепить |
| `/clear` | Очистить историю |

### `opensaw info`

Дашборд: версия, модель, плагины, CPU/GPU/RAM.

### `opensaw help`

Развёрнутая справка.

### `opensaw serve` (требуется `[server]`)

FastAPI:

```bash
opensaw serve --host 0.0.0.0 --port 8000
```
