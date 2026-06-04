import os
import subprocess
from pathlib import Path
from typing import Optional

WORKSPACE_ROOT = os.getcwd()


def read_file(path: str) -> str:
    full = os.path.join(WORKSPACE_ROOT, path) if not os.path.isabs(path) else path
    full = os.path.normpath(full)
    if not full.startswith(WORKSPACE_ROOT):
        return "Error: access denied (path outside workspace)"
    try:
        with open(full, encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"


def write_file(path: str, content: str) -> str:
    full = os.path.join(WORKSPACE_ROOT, path) if not os.path.isabs(path) else path
    full = os.path.normpath(full)
    if not full.startswith(WORKSPACE_ROOT):
        return "Error: access denied (path outside workspace)"
    try:
        Path(full).parent.mkdir(parents=True, exist_ok=True)
        with open(full, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Written {len(content)} bytes to {path}"
    except Exception as e:
        return f"Error writing file: {e}"


def list_dir(path: str = '.') -> str:
    full = os.path.join(WORKSPACE_ROOT, path) if not os.path.isabs(path) else path
    full = os.path.normpath(full)
    if not full.startswith(WORKSPACE_ROOT):
        return "Error: access denied (path outside workspace)"
    try:
        items = os.listdir(full)
        lines = []
        for item in sorted(items):
            full_item = os.path.join(full, item)
            if os.path.isdir(full_item):
                lines.append(f"  📁 {item}/")
            else:
                size = os.path.getsize(full_item)
                lines.append(f"  📄 {item} ({size} B)")
        return '\n'.join(lines) if lines else '(empty)'
    except Exception as e:
        return f"Error listing directory: {e}"


def run_command(cmd: str) -> str:
    allowed_prefixes = ['ls', 'cat', 'pwd', 'echo', 'head', 'tail',
                        'wc', 'find', 'grep', 'sort', 'uniq', 'which',
                        'python3', 'pip list', 'pip freeze', 'date',
                        'whoami', 'hostname', 'uptime', 'free', 'df',
                        'ps aux', 'top', 'uname', 'id']
    safe = any(cmd.strip().startswith(p) for p in allowed_prefixes)
    if not safe:
        return (f"Error: command '{cmd.split()[0]}' not in allowed list.\n"
                f"Allowed: {', '.join(allowed_prefixes[:8])}...")
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30,
            cwd=WORKSPACE_ROOT,
        )
        out = result.stdout.strip()
        err = result.stderr.strip()
        if out and err:
            return f"{out}\n{err}"
        return out or err or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: command timed out (30s)"
    except Exception as e:
        return f"Error: {e}"
