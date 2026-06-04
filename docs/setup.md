# Установка

## Зависимости

- Python >= 3.10
- `pip`, `venv`

## Пошаговая установка

**Шаг 1 — скачай код:**

```bash
git clone git@github.com:bitplugg/opensaw.git
cd opensaw
```

**Шаг 2 — создай виртуальное окружение:**

```bash
python3 -m venv venv
```

**Шаг 3 — активируй:**

```bash
source venv/bin/activate
```

В начале строки терминала появится `(venv)`.

**Шаг 4 — установи OpenSaw:**

```bash
pip install -e .
```

**Шаг 5 — установи GGUF-бекенд (обязательно для CPU):**

```bash
pip install -e ".[gguf]"
```

**Шаг 6 — настройка:**

```bash
opensaw setup
```

Скрипт спросит имя, имя AI, путь к модели.

**Шаг 7 — запуск:**

```bash
opensaw chat
```

## Дополнительные компоненты

```bash
pip install -e ".[semantic]"   # семантическая память
pip install -e ".[docs]"       # PDF/DOCX/XLSX
pip install -e ".[server]"     # FastAPI
pip install -e ".[voice]"      # голосовой ввод/вывод
pip install -e ".[all]"        # всё сразу
```
