import gi
gi.require_version('Gtk', '4.0')
gi.require_version('GLib', '2.0')
from gi.repository import GLib, Gtk


class InputArea:
    def __init__(self, on_submit):
        self._on_submit = on_submit
        self._box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._box.set_margin_start(14)
        self._box.set_margin_end(14)
        self._box.set_margin_top(8)
        self._box.set_margin_bottom(10)

        self._entry = Gtk.Entry()
        self._entry.set_hexpand(True)
        self._entry.set_placeholder_text('Спроси у OpenSaw…')
        self._entry.connect('activate', self._on_enter)
        self._box.append(self._entry)

        self._btn = Gtk.Button(label='→')
        self._btn.connect('clicked', self._on_click)
        self._box.append(self._btn)

    def widget(self):
        return self._box

    def focus(self):
        self._entry.grab_focus()

    def set_sensitive(self, sensitive: bool):
        self._entry.set_sensitive(sensitive)
        self._btn.set_sensitive(sensitive)

    def _on_enter(self, _entry):
        self._submit()

    def _on_click(self, _btn):
        self._submit()

    def _submit(self):
        text = self._entry.get_text().strip()
        if not text:
            self._shake()
            return
        self._entry.set_text('')
        self._on_submit(text)

    def _shake(self):
        """Minimal shake animation on empty submit."""
        orig_x = 0.0

        def tick(step=0):
            if step >= 6:
                self._entry.set_margin_start(0)
                return False
            offset = 3 if step % 2 == 0 else -3
            self._entry.set_margin_start(orig_x + offset)
            GLib.timeout_add(30, tick, step + 1)
            return False

        GLib.timeout_add(16, tick)
