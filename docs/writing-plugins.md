# Написание плагина

Полный туториал по созданию `.plugin` файла.

## Структура

Простой плагин — один `.plugin` файл:

```
plugins/
  weather.plugin
```

Сложный — `.plugin` + поддиректория с пакетом:

```
plugins/
  ui-gtk.plugin
  opensaw_ui_gtk/
    __init__.py
    app.py
```

## Шаблон

```python
NAME = "MyPlugin"
VERSION = "1.0"
DESCRIPTION = "Что делает"
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
        # Регистрируем всё здесь
        self.commands['hello'] = self._cmd_hello
        self.tools['CALC'] = self._tool_calc

    def _cmd_hello(self, arg: str):
        # /hello имя → выводит приветствие
        from cli import chat_lines
        chat_lines.append(f'[cyan]👋 {arg or "мир"}[/cyan]')

    def _tool_calc(self, args: str):
        # AI пишет [CALC 2+2]
        try:
            return str(eval(args))
        except Exception as e:
            return f'❌ {e}'
```

## Команды

Добавляются в `self.commands`. Ключ — имя (без `/`):

```python
self.commands['summarize'] = self._cmd_summarize

def _cmd_summarize(self, arg: str):
    from cli import chat_lines, last_response
    text = arg or last_response
    short = text[:100] + '...'
    chat_lines.append(f'[bold]📝 {short}[/bold]')
```

## Инструменты для AI

AI вызывает по `[ИМЯ аргументы]`:

```python
self.tools['WEATHER'] = self._tool_weather

def _tool_weather(self, args: str):
    import urllib.request
    city = args.strip() or "Moscow"
    url = f"https://wttr.in/{city}?format=3"
    return urllib.request.urlopen(url).read().decode().strip()
```

## Хуки

```python
@self.hook(HookPoint.POST_OUTPUT)
def on_output(ctx):
    ctx['response'] += '\n\n— добавлено плагином'
```

## Полная замена UI

```python
@self.hook(HookPoint.PRE_UI_LOOP, priority=200)
def start_my_ui(ctx):
    lm, memory = ctx['lm'], ctx['memory']
    run_my_app(lm, memory)
    return True  # TUI не запускается
```
