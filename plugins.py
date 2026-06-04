import importlib.machinery
import importlib.util
import inspect
import os
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Optional


class HookPoint(Enum):
    PRE_INPUT = auto()
    POST_INPUT = auto()
    PRE_GENERATION = auto()
    POST_GENERATION = auto()
    PRE_OUTPUT = auto()
    POST_OUTPUT = auto()
    PRE_TOOL = auto()
    POST_TOOL = auto()
    PRE_UI_LOOP = auto()
    POST_UI_LOOP = auto()


@dataclass
class Hook:
    point: HookPoint
    handler: Callable[[dict[str, Any]], Any]
    priority: int = 0
    plugin_name: str = ''


@dataclass
class PluginInfo:
    path: Path
    source: str
    meta: dict[str, str]
    plugin: 'PluginBase'


class PluginBase:
    name: str = ''
    version: str = ''
    description: str = ''
    author: str = ''
    commands: dict[str, Callable] = {}
    tools: dict[str, Callable] = {}

    def __init__(self):
        self._hooks: list[Hook] = []

    def on_load(self):
        pass

    def on_unload(self):
        pass

    def hook(self, point: HookPoint, priority: int = 0):
        def decorator(func):
            self._hooks.append(Hook(
                point=point, handler=func,
                priority=priority, plugin_name=self.name,
            ))
            return func
        return decorator


def _load_plugin_file(path: Path) -> Optional[PluginInfo]:
    mod_name = path.stem
    try:
        loader = importlib.machinery.SourceFileLoader(mod_name, str(path))
        spec = importlib.util.spec_from_loader(mod_name, loader, origin=str(path))
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    except Exception:
        return None

    meta = {
        'name': getattr(mod, 'NAME', ''),
        'version': getattr(mod, 'VERSION', '0.1'),
        'description': getattr(mod, 'DESCRIPTION', ''),
        'author': getattr(mod, 'AUTHOR', ''),
    }

    for attr_name in dir(mod):
        obj = getattr(mod, attr_name)
        if (
            inspect.isclass(obj)
            and issubclass(obj, PluginBase)
            and obj is not PluginBase
        ):
            plugin = obj()
            if meta['name']:
                plugin.name = meta['name']
            if meta['version']:
                plugin.version = meta['version']
            if meta['description']:
                plugin.description = meta['description']
            if meta['author']:
                plugin.author = meta['author']
            source = path.read_text(encoding='utf-8')
            return PluginInfo(path=path, source=source, meta=meta, plugin=plugin)

    return None


_plugin_dirs = ['./plugins', os.path.expanduser('~/.config/opensaw/plugins')]


def set_plugin_dirs(dirs: list[str]):
    global _plugin_dirs
    _plugin_dirs = dirs


VALIDATION_PROMPT = """Ты проверяешь плагин для OpenSaw на безопасность.
Плагин — Python код, который может:
- читать/писать файлы
- выполнять команды
- перехватывать ввод/вывод AI

Проанализируй код. Если видишь опасные операции (удаление файлов, netcat, reverse shell, загрузка вредоносного кода, обход проверок) — ответь UNSAFE и кратко почему.
Иначе ответь только SAFE.

Код плагина:
```python
{source}
```"""


class PluginManager:
    def __init__(self):
        self.plugins: list[PluginBase] = []
        self._pending: list[PluginInfo] = []
        self._hooks: list[Hook] = []
        self.commands: dict[str, Callable] = {}
        self.tools: dict[str, Callable] = {}
        self._validation_results: dict[str, bool] = {}

    def discover(self):
        for d in _plugin_dirs:
            plugins_dir = Path(d)
            if not plugins_dir.is_dir():
                continue
            for pf in sorted(plugins_dir.glob('*.plugin')):
                info = _load_plugin_file(pf)
                if info is not None:
                    self._pending.append(info)

    def validate_with_ai(self, lm) -> list[PluginInfo]:
        validated = []
        for info in self._pending:
            try:
                prompt = VALIDATION_PROMPT.format(source=info.source)
                response = lm.chat(
                    'Ты проверяешь плагины OpenSaw на безопасность. Отвечай только SAFE или UNSAFE.',
                    prompt,
                )
                resp_clean = response.strip().upper()
                if resp_clean.startswith('SAFE'):
                    self._validation_results[info.meta['name']] = True
                    validated.append(info)
                elif resp_clean.startswith('UNSAFE'):
                    reason = response[len('UNSAFE'):].strip().replace('\n', ' | ')
                    if not reason:
                        reason = 'unsafe'
                    print(f'[red]⛔ Plugin {info.meta["name"]}: {reason}[/red]')
                    self._validation_results[info.meta['name']] = False
                else:
                    validated.append(info)
            except Exception:
                validated.append(info)
        return validated

    def activate(self, plugin_list: list[PluginInfo]):
        for info in plugin_list:
            try:
                plugin = info.plugin
                plugin.on_load()
                self.plugins.append(plugin)
                self._hooks.extend(plugin._hooks)
                if plugin.commands:
                    self.commands.update(plugin.commands)
                if plugin.tools:
                    self.tools.update(plugin.tools)
                self._hooks.sort(key=lambda h: h.priority, reverse=True)
            except Exception:
                pass

    def register(self, plugin: PluginBase):
        self.activate([PluginInfo(path=Path(''), source='', meta={}, plugin=plugin)])

    def dispatch(self, point: HookPoint, context: dict[str, Any] = None) -> dict[str, Any]:
        if context is None:
            context = {}
        for hook in self._hooks:
            if hook.point == point:
                try:
                    result = hook.handler(context)
                    if result is not None:
                        if isinstance(result, dict):
                            context.update(result)
                except Exception:
                    continue
        return context

    def dispatch_capture(self, point: HookPoint, context: dict[str, Any] = None) -> Any:
        if context is None:
            context = {}
        for hook in self._hooks:
            if hook.point == point:
                try:
                    result = hook.handler(context)
                    if result is not None:
                        return result
                except Exception:
                    continue
        return None

    def handle_command(self, cmd: str, arg: str = '') -> Optional[bool]:
        handler = self.commands.get(cmd)
        if handler:
            try:
                handler(arg)
                return True
            except Exception:
                return None
        return None

    def handle_tool(self, tool_type: str, args: str) -> Optional[str]:
        handler = self.tools.get(tool_type)
        if handler:
            try:
                return handler(args)
            except Exception:
                return None
        return None


_manager: Optional[PluginManager] = None


def get_manager() -> PluginManager:
    global _manager
    if _manager is None:
        _manager = PluginManager()
    return _manager


def load_plugins():
    mgr = get_manager()
    mgr.discover()
    return mgr.plugins


def get_pending():
    return get_manager()._pending
