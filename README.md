
╔═══════════════════════════════════════╗
║              OpenSaw                  ║
║    Локальный AI-ассистент             ║
║    с душой и инструментами            ║
╚═══════════════════════════════════════╝

```bash
pip install -e .
opensaw chat
```

---

## Что это?

**OpenSaw** — AI-ассистент, который работает **полностью на твоём компьютере**.
Никаких облаков, никаких подписок, никакой отправки твоих данных куда-то.

Он умеет:
- Отвечать на вопросы (как ChatGPT, но локально)
- Помнить, что ты говорил раньше (даже между сессиями)
- Читать и писать файлы, выполнять команды на твоём компьютере
- Загружать и анализировать документы (PDF, DOCX, XLSX)
- Расширяться через плагины — ты сам пишешь `.plugin` файлы

Всё, что ему нужно — одна GGUF-модель (2-8 ГБ) и Python.

---

## Что нужно знать перед началом

Базовые вещи:
- **Терминал** — чёрное окно с текстом, куда вводят команды
- **Python** — язык программирования, на котором написан OpenSaw
- **venv** — виртуальное окружение, изолированная папка с Python+пакетами
- **pip** — программа, которая ставит Python-пакеты
- **Git** — система для скачивания кода

Всё это, скорее всего, уже есть в твоей системе, если ты разработчик.
Если нет — гайды есть в интернете по запросу "как установить Python на [твоя ОС]".

---

## Быстрый старт (для тех, кто знаком с терминалом)

```bash
# 1. Скачать код
git clone git@github.com:bitplugg/opensaw.git
cd opensaw

# 2. Создать виртуальное окружение
python3 -m venv venv

# 3. Активировать его
source venv/bin/activate

# 4. Установить OpenSaw
pip install -e .

# 5. Установить GGUF-бекенд (обязательно для CPU)
pip install -e ".[gguf]"

# 6. Настройка — задать имя, модель и т.д.
opensaw setup

# 7. Запуск!
opensaw chat
```

### Пошагово для новичка

**Шаг 1: Открой терминал**

В Linux: `Ctrl + Alt + T` или найди "Terminal" в меню.

**Шаг 2: Скачай OpenSaw**

```bash
git clone git@github.com:bitplugg/opensaw.git
cd opensaw
```

`git clone` — скачивает проект. `cd opensaw` — заходит в папку с ним.

**Шаг 3: Создай виртуальное окружение**

```bash
python3 -m venv venv
```

Это создаст папку `venv/`, внутри которой будет изолированный Python со своими пакетами.
Это нужно, чтобы пакеты OpenSaw не перемешались с системными.

**Шаг 4: Активируй окружение**

```bash
source venv/bin/activate
```

После этой команды в начале строки терминала появится `(venv)`.
Это значит — ты внутри изолированного окружения.

**Шаг 5: Установи OpenSaw**

```bash
pip install -e .
```

`pip` — установщик пакетов. `install -e .` — установить текущую папку как пакет в режиме разработки (флаг `-e` значит, что правки в коде будут сразу подхватываться).

**Шаг 6: Установи GGUF-бекенд**

```bash
pip install -e ".[gguf]"
```

GGUF — формат моделей, оптимизированный для CPU.
Скобки `[gguf]` — дополнительная опция, которая ставит `llama-cpp-python`.

**Шаг 7: Настройка**

```bash
opensaw setup
```

Скрипт спросит:
- Твоё имя (как к тебе обращаться)
- Имя AI-ассистента (как его называть)
- Путь к GGUF-модели (если модель уже есть)

**Шаг 8: Запуск**

```bash
opensaw chat
```

Откроется чат. Пиши сообщения — AI отвечает.
`/exit` — выйти. `/help` — список команд.

---

## Если у тебя слабый CPU (Celeron, Pentium, без AVX2)

Процессоры вроде Intel Celeron N5095 не поддерживают AVX2-инструкции.
Обычные сборки `llama-cpp-python` упадут с ошибкой `SIGILL` (запрещённая инструкция).

Для таких CPU нужна **сборка из исходников** с правильными флагами:

```bash
./setup-gguf.sh
./venv/bin/opensaw chat
```

Этот скрипт:
1. Устанавливает всё, что нужно для компиляции (`cmake`, `ninja`, `scikit-build-core` и т.д.)
2. Собирает `llama-cpp-python` из исходников с SSE3, но без AVX/AVX2
3. Конвертирует модель в GGUF Q8_0

Сборка занимает 5-15 минут. Ход можно смотреть:

```bash
tail -f build_gguf.log
```

## Как скачать модель

OpenSaw работает с моделями в формате GGUF.
Вот где их брать:

- **[Hugging Face](https://huggingface.co/)** — поиск `GGUF q8_0`
- Рекомендуемые на CPU: `Qwen2.5-1.5B-Instruct-Q8_0` (~1.6 ГБ), `Qwen2.5-3B-Instruct-Q8_0` (~3.2 ГБ), `Mistral-7B-Instruct-Q4_K_M` (~4.1 ГБ)
- Положи `.gguf` файл куда-нибудь и укажи путь в `opensaw setup`

Пример:

```bash
wget https://huggingface.co/bartowski/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/Qwen2.5-1.5B-Instruct-Q8_0.gguf
opensaw setup  # и укажи путь к скачанному файлу
```

---

## Возможности (подробно)

### Модели

OpenSaw поддерживает два движка:

| Движок | Когда нужен | Плюсы | Минусы |
|--------|-------------|-------|--------|
| `llama.cpp` (GGUF) | CPU, слабые машины | Быстро на CPU, мало RAM | Нет GPU-ускорения |
| `transformers` | Есть NVIDIA GPU | Точнее, GPU-ускорение | Требует ~6+ ГБ VRAM |

Переключение: `opensaw setup`, пункт "backend".

### Память

OpenSaw помнит, что ты говорил, даже после перезапуска.

| Режим | Как работает | Когда выбрать |
|-------|-------------|--------------|
| `simple` | Поиск по ключевым словам (TF-IDF) | Быстро, мало RAM, базовые задачи |
| `semantic` | По смыслу (sentence-transformers) | Точнее, понимает суть, а не слова |
| `hybrid` | Оба сразу | Лучший результат, но больше RAM |

Переключение: `opensaw setup` → memory_backend.

### Инструменты

AI может сам выполнять действия на твоём компьютере.
Он видит описание инструмента и сам решает, когда его применить.

```
Ты: "напиши hello.py и запусти"
AI: [WRITE hello.py → print("Hello!")]
    [CMD python hello.py]
    "Готово! Скрипт написан и выполнен."
```

| Инструмент | Что делает | Пример |
|-----------|-----------|--------|
| `[CMD ...]` | Выполнить команду в терминале | `[CMD ls -la]` |
| `[READ ...]` | Прочитать файл | `[READ config.json]` |
| `[WRITE ...]` | Записать файл | `[WRITE hello.py → print("Hi")]` |
| `[LS ...]` | Показать папку | `[LS src/]` |

### Плагины

Плагины — это Python-файлы с расширением `.plugin`.
Они могут:
- Добавлять команды (`/translate`, `/summarize`, `/save`)
- Добавлять инструменты AI (`[WEATHER Moscow]`, `[DRAW cat]`)
- Реагировать на события (хуки) — до/после генерации, до/после вывода, и т.д.
- Полностью заменить интерфейс — вместо TUI запустить своё GTK/Telegram/Web окно

Плагины лежат в:
- `./plugins/` — рядом с OpenSaw (локальные)
- `~/.config/opensaw/plugins/` — глобальные, для всех проектов

Каждый плагин проверяется AI-моделью на безопасность при загрузке.
Если модель считает код опасным — плагин не активируется.

### Интерфейсы

| Интерфейс | Как запустить | Особенности |
|-----------|--------------|-------------|
| **TUI** (Rich) | `opensaw chat` | Встроен, работает сразу |
| **GTK4** | Поставить `pip install PyGObject` + плагин | Цвета из pywal, анимации |
| **Telegram** | Плагин (напиши свой) | Удалённый доступ |
| **Web** | `opensaw server` | FastAPI, Swagger на `/docs` |
| **Голос** | `opensaw voice` | Микрофон → AI → голос (TTS) |

---

## Команды в чате

| Команда | Что делает |
|---------|-----------|
| `/exit` | Выйти |
| `/help` | Список команд TUI |
| `/regen` | Перегенерировать последний ответ |
| `/edit <текст>` | Заменить последнее сообщение |
| `/cont` | Продолжить последний ответ |
| `/search <запрос>` | Поиск по памяти |
| `/export` | Экспорт последнего ответа в файл |
| `/model download <имя>` | Скачать модель |
| `/pin` | Закрепить сообщение (оно всегда в контексте) |
| `/unpin` | Открепить |
| `/clear` | Очистить историю |
| `//текст` | Отправить текст без генерации (как заметка) |

Команды от плагинов тоже работают — `/hello`, `/translate`, `/weather` и т.д.

---

## Конфиг

Настройки хранятся в `~/.config/opensaw/config.json`:

```json
{
  "user_name": "Ты",
  "ai_name": "Saw",
  "model_path": "/home/user/models/qwen.gguf",
  "system_prompt": "Ты дружелюбный ассистент.",
  "memory_backend": "hybrid",
  "temperature": 0.7,
  "max_tokens": 2048,
  "prompt_style": "qwen"
}
```

Можно менять через `opensaw setup` или вручную.

---

## Что делать, если...

### ...ошибка SIGILL (запрещённая инструкция)

Твой CPU слишком старый для AVX-инструкций из стандартной сборки.

→ `./setup-gguf.sh` — пересобирает `llama-cpp-python` с правильными флагами.

### ...не хватает памяти (OOM / вылетает)

Используй модель поменьше или меньшую квантизацию:
- Qwen2.5-1.5B-Q8_0 (~1.6 ГБ) — минимум
- Qwen2.5-3B-Q4_K_M (~2 ГБ) — баланс
- Mistral-7B-Q4_K_M (~4 ГБ) — если есть 8+ ГБ RAM

В TUI нажми `Ctrl+C` чтобы прервать генерацию.

### ...не работает PyGObject

PyGObject — нативная библиотека GTK, не ставится через `pip` просто так.
Нужны системные пакеты:

```bash
# Ubuntu/Debian
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0

# Fedora
sudo dnf install python3-gobject gtk4

# Arch
sudo pacman -S python-gobject gtk4
```

### ...не могу найти модель

GGUF-модели ищутся на [Hugging Face](https://huggingface.co).
Ищи по запросу `GGUF Q8_0` или `GGUF Q4_K_M`.
Модели от 1.5 до 7 миллиардов параметров — оптимально для CPU.

Скачай `.gguf` файл и укажи путь в `opensaw setup`.

---

## GTK4 UI — как подключить

```bash
# 1. Установи PyGObject (см. выше про системные пакеты)
pip install PyGObject

# 2. Установи GTK плагин
mkdir -p ~/.config/opensaw/plugins
cp plugins/opensaw-ui-gtk.plugin ~/.config/opensaw/plugins/
cp -r plugins/opensaw_ui_gtk/ ~/.config/opensaw/plugins/

# 3. Запуск → откроется GTK4 окно
opensaw chat
```

Цвета и тема берутся из pywal (`~/.cache/wal/colors.json`).
Если pywal не настроен — используются дефолтные серые тона.

## Структура проекта

```
opensaw/
├── opensawcore.py      # SDK для плагинов (публичное API)
├── plugins.py           # Система плагинов: загрузка, хуки, валидация
├── cli.py               # Точка входа, TUI, цикл чата
├── model.py             # Загрузка и запуск моделей
├── memory_engine.py     # Векторная память
├── tools.py             # Инструменты AI: [CMD], [READ], [WRITE], [LS]
├── config.py            # Конфиг (сохраняется в ~/.config/)
├── hardware_scanner.py  # Определение CPU/GPU/RAM
├── server.py            # FastAPI сервер для удалённого доступа
├── voice.py             # Голосовой ввод и вывод (TTS/STT)
├── plugins/             # Штатные плагины
│   ├── opensaw-ui-gtk.plugin
│   └── opensaw_ui_gtk/
└── docs/                # Документация
```

---

## Авторы

**OpenSaw Team**

- [bitplugg](https://github.com/bitplugg) — создатель, архитектура, код

*В разработке участвуют плагины сообщества. Стать автором — пиши `.plugin` файлы.*

---

## Документация

- [GitHub Pages](https://bitplugg.github.io/opensaw/) — сайт документации (MkDocs Material)
- [Wiki](https://github.com/bitplugg/opensaw/wiki) — полная документация
- [Setup](https://github.com/bitplugg/opensaw/wiki/Setup) — установка и настройка
- [CLI Reference](https://github.com/bitplugg/opensaw/wiki/CLI-Reference) — все команды
- [Plugins](https://github.com/bitplugg/opensaw/wiki/Plugins) — система плагинов
- [OpenSawCore](https://github.com/bitplugg/opensaw/wiki/OpenSawCore) — SDK для плагинов
- [Writing Plugins](https://github.com/bitplugg/opensaw/wiki/Writing-Plugins) — как написать свой плагин
- [Plugin Examples](https://github.com/bitplugg/opensaw/wiki/Plugin-Examples) — готовые примеры
- [Model Guide](https://github.com/bitplugg/opensaw/wiki/Model-Guide) — выбор модели, квантизация
- [GGUF](https://github.com/bitplugg/opensaw/wiki/GGUF) — сборка под слабые CPU
- [Memory System](https://github.com/bitplugg/opensaw/wiki/Memory-System) — TF-IDF, semantic, hybrid
- [Tools Reference](https://github.com/bitplugg/opensaw/wiki/Tools-Reference) — CMD/READ/WRITE/LS
- [API](https://github.com/bitplugg/opensaw/wiki/API) — FastAPI эндпоинты
- [Troubleshooting](https://github.com/bitplugg/opensaw/wiki/Troubleshooting) — частые ошибки
- [FAQ](https://github.com/bitplugg/opensaw/wiki/FAQ) — вопросы и ответы
- [Architecture](https://github.com/bitplugg/opensaw/wiki/Architecture) — устройство проекта
- [PLUGINS.md](PLUGINS.md) — детальное описание системы плагинов

## Лицензия

MIT &copy; 2026 OpenSaw Team
