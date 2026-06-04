
╔═══════════════════════════════════════╗
║              OpenSaw                  ║
║    Локальный AI-ассистент             ║
║    с душой и инструментами            ║
╚═══════════════════════════════════════╝

```bash
pip install -e .
opensaw chat
```

## Как это работает

```
  Ты ──→ [Ввод] ──→ Память (TF-IDF + Semantic)
                        │
                   Контекст
                        │
                        ↓
                    Модель ──→ [CMD] [READ] [WRITE] [LS]
                    (GGUF /      │
                 Transformers)   ↓
                        │    Файлы / Команды
                        ↓
                   Ответ ←─── Плагины (хуки)
                        │
                        ↓
               ┌───────┴────────┐
               │                │
             TUI (Rich)    GTK4 / Telegram / Web
                           (плагины)
```

| Компонент | Что делает |
|-----------|-----------|
| **model.py** | Загрузка transformers / GGUF, инференс |
| **memory_engine.py** | Векторная память (TF-IDF + sentence-transformers) |
| **plugins.py** | Система плагинов: хуки, команды, инструменты, AI-валидация |
| **opensawcore.py** | SDK для плагинов |
| **tools.py** | `[CMD]`, `[READ]`, `[WRITE]`, `[LS]` — файлы и команды |
| **cli.py** | TUI на Rich, точка входа, цикл генерации |
| **config.py** | Конфиг (модель, температура, имя) |
| **hardware_scanner.py** | Определение CPU/GPU/RAM |
| **server.py** | FastAPI для удалённого доступа |
| **voice.py** | Голосовой ввод/вывод |

## Авторы

**OpenSaw Team**

- [bitplugg](https://github.com/bitplugg) — создатель, архитектура, код

*В разработке участвуют плагины сообщества. Стать автором — пиши `.plugin` файлы.*

---

## Возможности

- **Модели**: transformers (CPU/GPU) + GGUF/llama.cpp для медленных CPU
- **Память**: TF-IDF + семантическая, режимы `tfidf`, `semantic`, `hybrid`
- **Инструменты**: AI сам читает/пишет файлы, выполняет команды
- **Плагины**: `.plugin` файлы, 10 точек хуков, замена UI, AI-валидация
- **UI**: TUI (Rich) встроен, GTK4 плагином, можно Telegram/Web/Audio
- **Сервер**: FastAPI, документация на `/docs`

## Быстрый старт

```bash
git clone git@github.com:bitplugg/opensaw.git
cd opensaw
python3 -m venv venv
source venv/bin/activate
pip install -e .
pip install -e ".[gguf]"       # если нужен GGUF backend

opensaw setup
opensaw chat
```

На слабых CPU (Celeron N5095, без AVX2):

```bash
./setup-gguf.sh
./venv/bin/opensaw chat
```

## Плагины

`.plugin` файлы в `./plugins/` или `~/.config/opensaw/plugins/`.

```python
NAME = "MyPlugin"
VERSION = "1.0"
DESCRIPTION = "Что делает"
AUTHOR = "me"

from opensawcore import PluginBase, HookPoint

class MyPlugin(PluginBase):
    def on_load(self):
        self.commands['hello'] = self._hello
        self.tools['CALC'] = self._calc

        @self.hook(HookPoint.POST_OUTPUT)
        def on_output(ctx):
            ctx['response'] += '\n\n— добавлено плагином'
```

Подробнее: [PLUGINS.md](PLUGINS.md)

## GTK UI

```bash
pip install PyGObject
# Положить plugins/opensaw-ui-gtk.plugin в ~/.config/opensaw/plugins/
opensaw chat   # ← GTK4 окно
```

Цвета из pywal (`~/.cache/wal/colors.json`).

## Wiki

Вики проекта: [github.com/bitplugg/opensaw/wiki](https://github.com/bitplugg/opensaw/wiki)

Темы:
- [Установка и настройка](https://github.com/bitplugg/opensaw/wiki/Setup)
- [Система плагинов](https://github.com/bitplugg/opensaw/wiki/Plugins)
- [GGUF на слабых CPU](https://github.com/bitplugg/opensaw/wiki/GGUF)
- [Написание своего плагина](https://github.com/bitplugg/opensaw/wiki/Writing-Plugins)
- [API и сервер](https://github.com/bitplugg/opensaw/wiki/API)

## Лицензия

MIT &copy; 2026 OpenSaw Team
