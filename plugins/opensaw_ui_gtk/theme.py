import json
import os
from pathlib import Path

WAL_COLORS = Path(os.path.expanduser('~/.cache/wal/colors.json'))
GTK_THEME = ''


def load_wal_colors() -> dict[str, str]:
    if not WAL_COLORS.exists():
        return {}
    try:
        with open(WAL_COLORS) as f:
            raw = json.load(f)
        colors = raw.get('colors', {})
        out = {}
        for key, val in colors.items():
            out[key] = val.replace('#', '')
        return out
    except (json.JSONDecodeError, IOError):
        return {}


def build_css(wal: dict[str, str]) -> str:
    if not wal:
        return _default_css()

    bg = wal.get('color0', '1e1e2e')
    fg = wal.get('color7', 'cdd6f4')
    accent = wal.get('color4', '89b4fa')
    accent2 = wal.get('color5', 'f5c2e7')
    surface = wal.get('color8', '45475a')
    muted = wal.get('color10', 'a6e3a1')

    return f'''
window {{
    background-color: #{bg};
    color: #{fg};
}}

textview text {{
    background-color: #{bg};
    color: #{fg};
    font-family: 'Cantarell', sans-serif;
    font-size: 13px;
}}

textview text selection {{
    background-color: #{accent}44;
}}

entry {{
    background-color: #{surface};
    color: #{fg};
    border-radius: 8px;
    border: 1px solid #{surface};
    padding: 8px 12px;
    font-size: 13px;
    caret-color: #{accent};
    transition: border-color 200ms ease;
}}

entry:focus {{
    border-color: #{accent};
    background-color: #{surface}cc;
}}

button {{
    background-color: #{accent};
    color: #{bg};
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: bold;
    border: none;
    transition: all 200ms ease;
}}

button:hover {{
    background-color: #{accent2};
}}

button:active {{
    background-color: #{accent}cc;
}}

.label-header {{
    color: #{accent};
    font-weight: bold;
    font-size: 11px;
}}

.label-status {{
    color: #{surface};
    font-size: 11px;
}}

.label-user {{
    color: #{muted};
    font-weight: bold;
}}

.label-ai {{
    color: #{fg};
    font-weight: bold;
}}

.label-system {{
    color: #{surface};
    font-style: italic;
    font-size: 12px;
}}

scrollbar {{
    background-color: #{bg};
    min-width: 6px;
}}

scrollbar slider {{
    background-color: #{surface};
    border-radius: 3px;
    min-width: 6px;
}}

scrollbar slider:hover {{
    background-color: #{accent}88;
}}
'''


def _default_css() -> str:
    return '''
window {
    background-color: #1e1e2e;
    color: #cdd6f4;
}

textview text {
    background-color: #1e1e2e;
    color: #cdd6f4;
    font-family: 'Cantarell', sans-serif;
    font-size: 13px;
}

entry {
    background-color: #45475a;
    color: #cdd6f4;
    border-radius: 8px;
    border: 1px solid #45475a;
    padding: 8px 12px;
    font-size: 13px;
    caret-color: #89b4fa;
}

entry:focus {
    border-color: #89b4fa;
}

button {
    background-color: #89b4fa;
    color: #1e1e2e;
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: bold;
    border: none;
}

button:hover {
    background-color: #f5c2e7;
}

scrollbar slider {
    background-color: #45475a;
    border-radius: 3px;
    min-width: 6px;
}
'''
