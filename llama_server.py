import os
import sys
import time
import json
import signal
import atexit
import requests
import subprocess
import threading
from pathlib import Path
from typing import Optional, Generator
from urllib.parse import urljoin

SERVER_BIN = "/tmp/llama.cpp/install/bin/llama-server"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8188  # not to conflict with other services


def _find_server() -> Optional[str]:
    candidates = [
        SERVER_BIN,
        str(Path.home() / ".local" / "bin" / "llama-server"),
        "llama-server",
    ]
    for c in candidates:
        if c == "llama-server":
            import shutil
            if shutil.which(c):
                return c
        elif os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None


def build_server() -> bool:
    script = Path(__file__).parent / "build_llama.sh"
    if script.exists():
        print("🔨 Building llama.cpp server...")
        return subprocess.call(["bash", str(script)]) == 0
    print("❌ build_llama.sh not found")
    return False


class LlamaServer:
    def __init__(
        self,
        model_path: str,
        host: str = DEFAULT_HOST,
        port: int = DEFAULT_PORT,
        n_ctx: int = 4096,
        n_threads: int = 4,
        verbose: bool = False,
    ):
        self.model_path = model_path
        self.host = host
        self.port = port
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self.verbose = verbose
        self._process: Optional[subprocess.Popen] = None
        self._base_url = f"http://{host}:{port}"
        self._lock = threading.Lock()

    @property
    def ready(self) -> bool:
        return self._process is not None and self._process.poll() is None

    def start(self) -> bool:
        if self.ready:
            return True

        binary = _find_server()
        if not binary:
            print("llama-server not found. Run build_llama.sh first.")
            return False

        cmd = [
            binary,
            "-m", self.model_path,
            "--host", self.host,
            "--port", str(self.port),
            "--ctx-size", str(self.n_ctx),
            "--threads", str(self.n_threads),
            "--n-gpu-layers", "0",
            "--no-mmap",
        ]
        if not self.verbose:
            cmd.append("--log-disable")

        self._process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL if not self.verbose else None,
            stderr=subprocess.DEVNULL if not self.verbose else None,
        )

        # ждём пока сервер ответит
        for _ in range(60):
            if self._try_health():
                atexit.register(self.stop)
                return True
            time.sleep(0.5)

        self.stop()
        return False

    def stop(self):
        with self._lock:
            if self._process:
                self._process.terminate()
                try:
                    self._process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self._process.kill()
                self._process = None

    def _try_health(self) -> bool:
        try:
            r = requests.get(urljoin(self._base_url, "/health"), timeout=2)
            return r.status_code == 200
        except (requests.ConnectionError, requests.Timeout):
            return False

    def chat(
        self,
        system_prompt: str,
        user_input: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> str:
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            "max_tokens": max_tokens or 2048,
            "temperature": temperature,
            "top_p": 0.8,
            "stream": False,
        }
        r = requests.post(
            urljoin(self._base_url, "/v1/chat/completions"),
            json=payload,
            timeout=300,
        )
        r.raise_for_status()
        data = r.json()
        return data["choices"][0]["message"]["content"].strip()

    def chat_stream(
        self,
        system_prompt: str,
        user_input: str,
        max_tokens: Optional[int] = None,
        temperature: float = 0.7,
    ) -> Generator[str, None, None]:
        payload = {
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            "max_tokens": max_tokens or 2048,
            "temperature": temperature,
            "top_p": 0.8,
            "stream": True,
        }
        r = requests.post(
            urljoin(self._base_url, "/v1/chat/completions"),
            json=payload,
            stream=True,
            timeout=300,
        )
        r.raise_for_status()
        for line in r.iter_lines():
            if not line:
                continue
            if line.startswith(b"data: "):
                chunk = line[6:]
                if chunk.strip() == b"[DONE]":
                    break
                try:
                    data = json.loads(chunk)
                    delta = data["choices"][0]["delta"].get("content", "")
                    if delta:
                        yield delta
                except json.JSONDecodeError:
                    continue
