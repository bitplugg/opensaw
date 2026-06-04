# OpenSaw

**Локальный AI-ассистент с душой и инструментами.**

Работает полностью на твоём компьютере — никаких облаков, никаких подписок.

```bash
pip install -e .
opensaw chat
```

## Возможности

- **Модели**: GGUF/llama.cpp для CPU, transformers для GPU
- **Память**: TF-IDF + семантическая, поиск по смыслу между сессиями
- **Инструменты**: AI сам читает/пишет файлы и выполняет команды
- **Плагины**: `.plugin` файлы, 10 точек хуков, AI-валидация
- **UI**: TUI (Rich), GTK4 (плагин), можно Telegram/Web/Audio
- **Сервер**: FastAPI с `/docs`

## Быстрый старт

```bash
git clone git@github.com:bitplugg/opensaw.git
cd opensaw
python3 -m venv venv
source venv/bin/activate
pip install -e .
pip install -e ".[gguf]"
opensaw setup
opensaw chat
```

На слабых CPU (Celeron N5095, без AVX2):

```bash
./setup-gguf.sh
./venv/bin/opensaw chat
```

## Документация

| Раздел | О чём |
|--------|-------|
| [Setup](setup.md) | Пошаговая установка |
| [GGUF](gguf.md) | Сборка под старые CPU |
| [Model Guide](model-guide.md) | Какую модель выбрать |
| [CLI Reference](cli-reference.md) | Все команды |
| [Memory System](memory-system.md) | Как работает память |
| [Tools Reference](tools-reference.md) | Инструменты AI |
| [Plugins](plugins.md) | Система плагинов |
| [OpenSawCore](opensawcore.md) | SDK для плагинов |
| [Writing Plugins](writing-plugins.md) | Туториал |
| [Plugin Examples](plugin-examples.md) | Готовые плагины |
| [API](api.md) | FastAPI |
| [Architecture](architecture.md) | Устройство проекта |
| [Troubleshooting](troubleshooting.md) | Решение проблем |
| [FAQ](faq.md) | Вопросы и ответы |
