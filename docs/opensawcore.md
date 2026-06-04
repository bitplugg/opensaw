# OpenSawCore SDK

`opensawcore` — публичное API для плагинов.

```python
from opensawcore import PluginBase, HookPoint
```

## Что экспортирует

| Символ | Назначение |
|--------|-----------|
| `PluginBase` | Базовый класс плагина |
| `HookPoint` | Enum точек хуков |
| `Hook` | Объект хука |
| `get_manager()` | Получить PluginManager |
| `load_plugins(lm)` | Перезагрузить плагины |
| `config` | Глобальный конфиг |
| `OpenSawLM` | Языковая модель |
| `MemoryEngine` | Векторная память |
| `read_file(path)` | Прочитать файл |
| `write_file(path, text)` | Записать файл |
| `list_dir(path)` | Список папки |
| `run_command(cmd)` | Выполнить команду |
| `scan_hardware()` | Инфо о железе |

## OpenSawLM

```python
lm = OpenSawLM()
lm.load('/path/to/model.gguf', n_ctx=2048)

response = lm.chat(
    system_prompt="Ты помощник.",
    user_input="Привет!",
    max_new_tokens=512,
)

for chunk in lm.stream(system_prompt="...", user_input="..."):
    print(chunk, end='', flush=True)
```

## MemoryEngine

```python
mem = MemoryEngine()
mem.add("Текст для запоминания")
results = mem.search("запрос", top_k=3)
```

## config

```python
from opensawcore import config
name = config.get('user_name')
config.set('temperature', 0.8)
config.save()
```

## Написание своего SDK

Создай файл-прослойку по аналогии с `opensawcore.py`:

```python
import os, sys
sys.path.insert(0, os.path.dirname(__file__))

from my_module import MyClass, my_func

__all__ = ['MyClass', 'my_func']
```

Плагины импортируют из этого файла, а не из внутренних модулей.
