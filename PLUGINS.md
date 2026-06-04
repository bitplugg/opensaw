# OpenSaw Plugin System

## Формат `.plugin`

Плагин — это Python-файл с расширением `.plugin`, который лежит в `./plugins/`
или `~/.config/opensaw/plugins/`. OpenSaw сам находит и загружает их при старте.

### Структура файла

```python
# Метаданные (обязательно)
NAME = "Название плагина"
VERSION = "1.0"
DESCRIPTION = "Краткое описание"
AUTHOR = "Разработчик"

from opensawcore import PluginBase, HookPoint

# Класс плагина — наследуется от PluginBase
class MyPlugin(PluginBase):
    name = NAME
    version = VERSION
    description = DESCRIPTION
    author = AUTHOR

    commands = {}   # слэш-команды:  {'cmd_name': handler}
    tools = {}      # инструменты:   {'TOOL_NAME': handler}

    def on_load(self):
        """Вызывается при загрузке плагина. Регистрируй хуки тут."""
        pass
```

## Хуки (HookPoint)

Хук перехватывает этап обработки и может изменить данные.

| HookPoint | Когда срабатывает | context |
|-----------|------------------|---------|
| `PRE_INPUT` | Перед запросом ввода | `{}` |
| `POST_INPUT` | После ввода пользователя | `raw`, `chat_lines` |
| `PRE_GENERATION` | Перед генерацией ответа | `user_input`, `context`, `n_found`, `scores_str` |
| `POST_GENERATION` | После генерации | `user_input`, `response`, `token_count`, `prompt_tokens`, `built_prompt`, `gen_elapsed` |
| `PRE_TOOL` | Перед выполнением инструмента `[CMD ...]` | `tool_type`, `args` |
| `POST_TOOL` | После выполнения инструмента | `tool_type`, `args`, `result` |
| `PRE_OUTPUT` | Перед выводом ответа (перед typing effect) | `response`, `tool_results` |
| `POST_OUTPUT` | После вывода ответа | `user_input`, `response` |
| `PRE_UI_LOOP` | Перед запуском TUI (может заменить UI целиком) | `console`, `lm`, `memory` |
| `POST_UI_LOOP` | После завершения TUI | `{}` |

```python
def on_load(self):
    @self.hook(HookPoint.POST_INPUT, priority=10)
    def on_input(ctx):
        raw = ctx['raw']
        if 'погода' in raw.lower():
            # изменить запрос перед генерацией
            pass

    @self.hook(HookPoint.POST_GENERATION)
    def on_output(ctx):
        response = ctx['response']
        # модифицировать ответ
        return {'response': '📢 ' + response}
```

## Слэш-команды

```python
class MyPlugin(PluginBase):
    commands = {}

    def on_load(self):
        self.commands['hello'] = self._cmd_hello
        self.commands['alert'] = self._cmd_alert

    def _cmd_hello(self, arg: str):
        from cli import chat_lines
        chat_lines.append(f'[bold]👋 {arg or "Привет!"}[/bold]')

    def _cmd_alert(self, arg: str):
        from cli import chat_lines
        chat_lines.append(f'[bold red]⚠️ {arg}[/bold red]')
```

В чате: `/hello мир`, `/alert Ошибка`

## Инструменты (аналог `[CMD ...]`)

Плагин может добавить свой тип инструмента в ответе AI:

```python
class MyPlugin(PluginBase):
    tools = {}

    def on_load(self):
        self.tools['CALC'] = self._tool_calc

    def _tool_calc(self, args: str):
        try:
            result = eval(args)
            return f'🧮 {args} = {result}'
        except:
            return f'❌ Ошибка: {args}'
```

AI сгенерирует `[CALC 2 + 2]`, плагин выполнит и вернёт `🧮 2 + 2 = 4`.

## Замена UI (PRE_UI_LOOP)

```python
def on_load(self):
    @self.hook(HookPoint.PRE_UI_LOOP)
    def start_gtk(ctx):
        from my_gtk_app import run_gtk
        lm = ctx['lm']
        memory = ctx['memory']
        run_gtk(lm, memory)
        return True  # TUI не запускается
```

## SDK

Плагин импортирует `opensawcore`:

```python
from opensawcore import (
    PluginBase, HookPoint,
    config,             # конфигурация (model_name, temperature, user_name...)
    OpenSawLM,          # модель
    MemoryEngine,       # векторная память
    read_file,          # чтение файла
    write_file,         # запись файла
    list_dir,           # список папки
    run_command,        # выполнить команду
    scan_hardware,      # информация о железе
    get_manager,        # PluginManager
    load_plugins,       # принудительная загрузка
)
```

Для доступа к чату и layout из TUI:
```python
from cli import chat_lines, layout, console, redraw
```

## Установка плагинов

Положить `.plugin` файл в `./plugins/` или `~/.config/opensaw/plugins/`:

```bash
mkdir -p ~/.config/opensaw/plugins
cp my_plugin.plugin ~/.config/opensaw/plugins/
opensaw chat
# → Plugin: MyPlugin 1.0
```

## Пример: минимальный плагин

```python
NAME = "Echo"
VERSION = "0.1"
DESCRIPTION = "Отвечает эхом на /echo"
AUTHOR = "me"

from opensawcore import PluginBase


class EchoPlugin(PluginBase):
    name = NAME
    version = VERSION
    description = DESCRIPTION
    author = AUTHOR
    commands = {}

    def on_load(self):
        self.commands['echo'] = self._echo

    def _echo(self, arg: str):
        from cli import chat_lines
        chat_lines.append(f'[dim]Эхо:[/dim] {arg}')
```
