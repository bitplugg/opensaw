import gi
gi.require_version('Gtk', '4.0')
gi.require_version('GLib', '2.0')
gi.require_version('Pango', '1.0')
from gi.repository import GLib, Gtk, Pango

from opensawcore import config


class ChatDisplay:
    def __init__(self):
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)

        self._view = Gtk.TextView()
        self._view.set_editable(False)
        self._view.set_cursor_visible(False)
        self._view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._view.set_pixels_above_lines(4)
        self._view.set_left_margin(14)
        self._view.set_right_margin(14)
        self._view.set_top_margin(8)

        self._buffer = self._view.get_buffer()
        scrolled.set_child(self._view)
        self._widget = scrolled
        self._adj = scrolled.get_vadjustment()

        tags = self._buffer.get_tag_table()
        user_tag = self._buffer.create_tag('user')
        user_tag.set_property('weight', Pango.Weight.BOLD)
        user_tag.set_property('foreground', getattr(config, 'user_color', '#a6e3a1'))

        ai_tag = self._buffer.create_tag('ai')
        ai_tag.set_property('weight', Pango.Weight.NORMAL)
        ai_tag.set_property('foreground', getattr(config, 'ai_color', '#cdd6f4'))

        sys_tag = self._buffer.create_tag('system')
        sys_tag.set_property('style', Pango.Style.ITALIC)
        sys_tag.set_property('scale', 0.9)
        sys_tag.set_property('foreground', '#585b70')

        bold_tag = self._buffer.create_tag('bold')
        bold_tag.set_property('weight', Pango.Weight.BOLD)

        code_tag = self._buffer.create_tag('code')
        code_tag.set_property('family', 'monospace')
        code_tag.set_property('scale', 0.9)
        code_tag.set_property('background', '#313244')
        code_tag.set_property('foreground', '#fab387')

        self._tags = {
            'user': user_tag,
            'ai': ai_tag,
            'system': sys_tag,
            'bold': bold_tag,
            'code': code_tag,
        }

    def widget(self):
        return self._widget

    def clear(self):
        self._buffer.set_text('', 0)

    def add_message(self, role: str, text: str):
        end = self._buffer.get_end_iter()

        if role == 'user':
            prefix = f'{config.user_name}: '
            tag = 'user'
        elif role == 'ai':
            prefix = f'{config.ai_name}: '
            tag = 'ai'
        elif role == 'system':
            prefix = ''
            tag = 'system'
        else:
            prefix = ''
            tag = None

        if prefix:
            self._buffer.insert_with_tags(end, prefix, self._tags.get('bold'))
            end = self._buffer.get_end_iter()

        # Parse markdown-like formatting
        self._insert_formatted(end, text)

        self._buffer.insert(end, '\n\n', -1)
        self._auto_scroll()

    def _insert_formatted(self, end_iter, text: str):
        import re
        parts = re.split(r'(\*\*.*?\*\*|`.*?`)', text, flags=re.DOTALL)
        for part in parts:
            end = self._buffer.get_end_iter()
            if part.startswith('**') and part.endswith('**'):
                self._buffer.insert_with_tags(
                    end, part[2:-2], self._tags.get('bold'),
                )
            elif part.startswith('`') and part.endswith('`'):
                self._buffer.insert_with_tags(
                    end, part[1:-1], self._tags.get('code'),
                )
            else:
                self._buffer.insert(end, part, -1)

    def _auto_scroll(self):
        GLib.timeout_add(50, self._do_scroll)

    def _do_scroll(self):
        if self._adj:
            upper = self._adj.get_upper()
            page = self._adj.get_page_size()
            self._adj.set_value(max(0, upper - page))
        return False
