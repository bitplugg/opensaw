import gi
gi.require_version('Gtk', '4.0')
gi.require_version('GLib', '2.0')
from gi.repository import GLib, Gtk

from opensawcore import config
from .theme import load_wal_colors, build_css
from .chat_display import ChatDisplay
from .input_area import InputArea
from .generation import GenerationManager


class OpenSawApp:
    def __init__(self, lm, memory, sem_memory=None):
        self.lm = lm
        self.memory = memory
        self.sem_memory = sem_memory
        self._app = None
        self._gen = GenerationManager(lm, memory, sem_memory)

    def run(self):
        GLib.set_application_id('app.opensaw.gtk')
        app = Gtk.Application(application_id='app.opensaw.gtk')
        self._app = app
        app.connect('activate', self._on_activate)
        app.run(None)

    def _on_activate(self, app):
        wal = load_wal_colors()
        css = build_css(wal)

        provider = Gtk.CssProvider()
        provider.load_from_string(css)
        Gtk.StyleContext.add_provider_for_display(
            Gtk.Display.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        win = Gtk.ApplicationWindow(application=app)
        model_short = config.model_name.split('/')[-1].replace('.gguf', '')
        win.set_title(f'OpenSaw — {model_short}')
        win.set_default_size(860, 640)
        win.connect('close-request', self._on_close)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        win.set_child(box)

        # Header
        header_label = Gtk.Label(
            label=f'<b>OpenSaw</b>  ·  {config.user_name}  ·  {model_short}',
            use_markup=True,
        )
        header_label.set_margin_start(14)
        header_label.set_margin_end(14)
        header_label.set_margin_top(10)
        header_label.set_margin_bottom(6)
        header_label.set_xalign(0)
        header_label.get_style_context().add_class('label-header')
        box.append(header_label)

        # Separator
        sep = Gtk.Separator()
        sep.set_opacity(0.3)
        box.append(sep)

        # Chat area
        self._chat = ChatDisplay()
        self._chat.widget().set_vexpand(True)
        box.append(self._chat.widget())

        # Generation indicator (hidden by default)
        self._indicator = Gtk.Label(label='')
        self._indicator.set_margin_start(14)
        self._indicator.set_margin_end(14)
        self._indicator.set_margin_top(2)
        self._indicator.set_margin_bottom(2)
        self._indicator.set_xalign(0)
        self._indicator.set_opacity(0.0)
        self._indicator.get_style_context().add_class('label-system')
        box.append(self._indicator)

        # Status bar
        self._status = Gtk.Label(label=self._status_text())
        self._status.set_margin_start(14)
        self._status.set_margin_end(14)
        self._status.set_margin_top(2)
        self._status.set_margin_bottom(6)
        self._status.set_xalign(0)
        self._status.get_style_context().add_class('label-status')
        box.append(self._status)

        # Input area
        self._input = InputArea(self._on_submit)
        box.append(self._input.widget())

        self._chat.add_message('system', f'OpenSaw GTK запущен. Модель: {model_short}')

        # Fade in animation
        win.set_opacity(0.0)
        win.present()
        self._fade_in(win, 0.0, 1.0, 300)

    def _status_text(self):
        docs = len(self.memory.documents) if self.memory else 0
        return f'{docs} документов · t={config.temperature} · max={config.max_tokens}'

    def _fade_in(self, win, start, end, duration_ms):
        steps = 30
        step_ms = duration_ms // steps
        delta = (end - start) / steps

        def tick(step=0):
            if step >= steps:
                return False
            val = start + delta * (step + 1)
            win.set_opacity(min(val, 1.0))
            GLib.timeout_add(step_ms, tick, step + 1)
            return False

        GLib.timeout_add(16, tick)

    def _animate_property(self, widget, prop, start, end, duration_ms):
        steps = max(duration_ms // 16, 1)
        delta = (end - start) / steps

        def tick(step=0):
            if step >= steps:
                widget.set_property(prop, end)
                return False
            val = start + delta * (step + 1)
            widget.set_property(prop, val)
            GLib.timeout_add(16, tick, step + 1)
            return False

        GLib.timeout_add(16, tick)

    def _show_generating(self):
        self._dots = 0

        def tick():
            self._dots = (self._dots + 1) % 4
            dots = '.' * self._dots
            self._indicator.set_label(f'OpenSaw печатает{dots}')
            self._indicator.set_opacity(0.7)
            return self._generating

        self._generating = True
        GLib.timeout_add(400, tick)

    def _on_submit(self, text: str):
        if not text.strip():
            return
        self._input.set_sensitive(False)
        self._chat.add_message('user', text)

        if text.startswith('/'):
            self._handle_command(text[1:].strip())
            self._input.set_sensitive(True)
            self._input.focus()
            return

        self._show_generating()

        def on_done(response: str):
            self._generating = False
            self._indicator.set_opacity(0.0)
            self._chat.add_message('ai', response)
            self._status.set_label(self._status_text())
            self._input.set_sensitive(True)
            self._input.focus()

        def on_error(error: str):
            self._generating = False
            self._indicator.set_opacity(0.0)
            self._chat.add_message('system', f'Ошибка: {error}')
            self._input.set_sensitive(True)
            self._input.focus()

        self._gen.generate(text, on_done=on_done, on_error=on_error)

    def _handle_command(self, cmd_line: str):
        parts = cmd_line.split()
        cmd = parts[0].lower() if parts else ''
        arg = ' '.join(parts[1:]) if len(parts) > 1 else ''

        if cmd == 'clear':
            self._chat.clear()
        elif cmd == 'help':
            self._chat.add_message('system',
                '/help   — помощь\n'
                '/clear  — очистить чат\n'
                '/stats  — статистика\n'
                '/exit   — выход')
        elif cmd == 'stats':
            s = f'Model: {config.model_name}\nTemp: t={config.temperature}\nMax: {config.max_tokens}'
            if self.memory:
                s += f'\nDocs: {len(self.memory.documents)}'
            self._chat.add_message('system', s)
        elif cmd == 'exit':
            if self._app:
                self._app.quit()

    def _on_close(self, _win):
        self._generating = False
