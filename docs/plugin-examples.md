# Примеры плагинов

## Погода

```python
# plugins/weather.plugin
NAME = "Weather"
VERSION = "1.0"
DESCRIPTION = "Погода через wttr.in"
AUTHOR = "me"

from opensawcore import PluginBase, HookPoint
import urllib.request

class WeatherPlugin(PluginBase):
    name = NAME
    version = VERSION
    description = DESCRIPTION
    author = AUTHOR
    commands = {}
    tools = {}

    def on_load(self):
        self.commands['weather'] = self._cmd_weather
        self.tools['WEATHER'] = self._tool_weather

    def _cmd_weather(self, arg: str):
        city = arg or "Moscow"
        url = f"https://wttr.in/{city}?format=3"
        data = urllib.request.urlopen(url).read().decode()
        from cli import chat_lines
        chat_lines.append(f'[cyan]🌤 {data.strip()}[/cyan]')

    def _tool_weather(self, args: str):
        city = args.strip() or "Moscow"
        url = f"https://wttr.in/{city}?format=3"
        return urllib.request.urlopen(url).read().decode().strip()
```

## Автосохранение диалогов

```python
# plugins/autosave.plugin
NAME = "AutoSave"
VERSION = "1.0"
DESCRIPTION = "Автосохранение в Markdown"
AUTHOR = "me"

from opensawcore import PluginBase, HookPoint
import datetime, os

class AutoSavePlugin(PluginBase):
    name = NAME
    description = DESCRIPTION
    commands = {}
    tools = {}

    def on_load(self):
        self._session_file = None

        @self.hook(HookPoint.POST_OUTPUT)
        def save(ctx):
            user = ctx.get('user_input', '')
            ai = ctx.get('response', '')
            if not user and not ai:
                return
            if not self._session_file:
                ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
                path = os.path.expanduser(f'~/.config/opensaw/logs/chat_{ts}.md')
                os.makedirs(os.path.dirname(path), exist_ok=True)
                self._session_file = path
            with open(self._session_file, 'a') as f:
                if user: f.write(f'## Ты\n{user}\n\n')
                if ai: f.write(f'## AI\n{ai}\n\n')
```

## Таймер

```python
# plugins/reminder.plugin
NAME = "Reminder"
VERSION = "1.0"
DESCRIPTION = "Команда /remind"
AUTHOR = "me"

from opensawcore import PluginBase
import threading, time

class ReminderPlugin(PluginBase):
    name = NAME
    commands = {}
    tools = {}

    def on_load(self):
        self.commands['remind'] = self._cmd_remind

    def _cmd_remind(self, arg: str):
        """/remind 10 Написать код"""
        from cli import chat_lines
        parts = arg.strip().split(maxsplit=1)
        if len(parts) < 2:
            chat_lines.append('[red]Исп: /remind <сек> <текст>[/red]')
            return
        seconds, text = int(parts[0]), parts[1]
        chat_lines.append(f'[yellow]⏰ {seconds}с: {text}[/yellow]')
        threading.Thread(target=lambda: (
            time.sleep(seconds),
            chat_lines.append(f'[bold yellow]⏰ {text}[/bold yellow]')
        ), daemon=True).start()
```
