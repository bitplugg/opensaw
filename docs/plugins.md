# Система плагинов

Плагины — Python-файлы с расширением `.plugin` в `./plugins/` или `~/.config/opensaw/plugins/`.

## Минимальный плагин

```python
NAME = "MyPlugin"
VERSION = "1.0"
DESCRIPTION = "Описание"
AUTHOR = "me"

from opensawcore import PluginBase, HookPoint

class MyPlugin(PluginBase):
    name = NAME
    version = VERSION
    description = DESCRIPTION
    author = AUTHOR
    commands = {}
    tools = {}

    def on_load(self):
        self.commands['hello'] = self._cmd_hello

    def _cmd_hello(self, arg: str):
        from cli import chat_lines
        chat_lines.append(f'[cyan]👋 {arg or "мир"}[/cyan]')
```

## HookPoint

| Хук | Когда |
|-----|-------|
| `PRE_INPUT` | Перед вводом |
| `POST_INPUT` | После ввода |
| `PRE_GENERATION` | Перед генерацией |
| `POST_GENERATION` | После генерации |
| `PRE_OUTPUT` | Перед выводом |
| `POST_OUTPUT` | После вывода |
| `PRE_TOOL` | Перед инструментом |
| `POST_TOOL` | После инструмента |
| `PRE_UI_LOOP` | Перед TUI (можно отменить) |
| `POST_UI_LOOP` | После TUI |

## Замена UI

```python
@self.hook(HookPoint.PRE_UI_LOOP, priority=200)
def replace_ui(ctx):
    run_my_app(ctx['lm'], ctx['memory'])
    return True  # TUI не запускается
```

## AI-валидация

Каждый плагин проверяется моделью на безопасность.
При ответе `UNSAFE` плагин не активируется.
