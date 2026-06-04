# OpenSaw

Локальный AI-ассистент с векторной памятью, инструментами, плагинами и сменным UI.

```bash
pip install -e .
opensaw chat
```

## Возможности

- **Модели**: transformers (CPU/GPU) + GGUF/llama.cpp для медленных CPU
- **Память**: TF-IDF + семантическая (sentence-transformers), режимы `tfidf`, `semantic`, `hybrid`
- **Инструменты**: AI сам читает/пишет файлы, выполняет команды — `[CMD ls]`, `[READ file]`, `[WRITE path content]`
- **Плагины**: `.plugin` файлы, хуки на любом этапе, замена UI, AI-валидация безопасности
- **UI**: встроенный TUI (Rich), GTK4 плагин, можно сделать Telegram/Web/Audio плагином
- **Сервер**: FastAPI эндпоинт для удалённого доступа

## Быстрый старт

```bash
# Установка
git clone git@github.com:bitplugg/opensaw.git
cd opensaw
python3 -m venv venv
source venv/bin/activate
pip install -e .
pip install -e ".[gguf]"  # если нужен GGUF backend

# Настройка
opensaw setup

# Запуск
opensaw chat
```

На слабых CPU (Celeron N5095, без AVX):

```bash
./setup-gguf.sh     # собирает llama-cpp-python + GGUF модель
./venv/bin/opensaw chat
```

## Плагины

Плагины — `.plugin` файлы в `./plugins/` или `~/.config/opensaw/plugins/`.

```python
NAME = "MyPlugin"
VERSION = "1.0"
DESCRIPTION = "Что делает"
AUTHOR = "me"

from opensawcore import PluginBase, HookPoint

class MyPlugin(PluginBase):
    def on_load(self):
        self.commands['hello'] = self._hello         # /hello
        self.tools['CALC'] = self._calc               # [CALC 2+2]

        @self.hook(HookPoint.POST_OUTPUT)
        def on_output(ctx):
            ctx['response'] += '\n\n— добавлено плагином'
```

Подробнее: [PLUGINS.md](PLUGINS.md)

## GTK UI

```bash
pip install PyGObject
# Положить plugins/opensaw-ui-gtk.plugin в ~/.config/opensaw/plugins/
opensaw chat   # ← откроется GTK4 окно
```

Цвета подхватываются из pywal (`~/.cache/wal/colors.json`).

## Проект

```
cli.py              — TUI чат + точка входа
model.py            — загрузка моделей (transformers / GGUF)
memory_engine.py    — векторная память
plugins.py          — система плагинов (хуки, менеджер, AI-валидация)
opensawcore.py      — SDK для плагинов
config.py           — конфиг
tools.py            — файловые операции
hardware_scanner.py — определение железа
server.py           — FastAPI сервер
voice.py            — голосовой ввод/вывод
setup-gguf.sh       — сборка GGUF бекенда под Celeron
build_gguf.sh       — фоновый скрипт сборки llama-cpp-python
```

## Лицензия

MIT
