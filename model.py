import os
import torch
from typing import Optional, Generator
from threading import Thread
from pathlib import Path


from utils import generate_model_name

AVAILABLE_MODELS = {
    "qwen2.5-0.5b": "Qwen/Qwen2.5-0.5B-Instruct",
    "qwen2.5-1.5b": "Qwen/Qwen2.5-1.5B-Instruct",
    "qwen2.5-3b": "Qwen/Qwen2.5-3B-Instruct",
    "gemma2-2b": "google/gemma-2-2b-it",
    "phi3-mini": "microsoft/Phi-3-mini-4k-instruct",
    "llama3.2-1b": "meta-llama/Llama-3.2-1B-Instruct",
    "llama3.2-3b": "meta-llama/Llama-3.2-3B-Instruct",
    "deepseek-coder-1.3b": "deepseek-ai/deepseek-coder-1.3b-instruct",
    "qwen3-0.6b-uncensored": "DavidAU/Qwen3-0.6B-heretic-abliterated-uncensored",
}


AVAILABLE_GGUF = {
    "qwen3-0.6b-q4": ("MaziyarPanahi/Qwen3-0.6B-GGUF", "Qwen3-0.6B.Q4_K_M.gguf"),
}


def _is_gguf_reference(name: str) -> bool:
    return name.lower().endswith('.gguf') or ':' in name


def _is_gguf_alias(name: str) -> bool:
    return name in AVAILABLE_GGUF or name in [v[0] for v in AVAILABLE_GGUF.values()]


class OpenSawLM:
    def __init__(
        self,
        model_name: str = "Qwen/Qwen2.5-0.5B-Instruct",
        device: str = "cpu",
        max_new_tokens: int = 150,
        temperature: float = 0.7,
    ):
        self.model_name = model_name
        self.device = device
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.tokenizer = None
        self.model = None
        self._llama = None
        self._gguf_path = None
        self.tag = generate_model_name()
        self._cache_dir = None
        self._server = None

    def use_server_backend(self, server) -> None:
        self._server = server

    def resolve_alias(self, alias: str) -> str:
        if alias in AVAILABLE_MODELS:
            return AVAILABLE_MODELS[alias]
        if alias in AVAILABLE_GGUF:
            repo, file = AVAILABLE_GGUF[alias]
            return f"{repo}:{file}"
        if '/' in alias:
            return alias
        return alias

    def is_gguf(self) -> bool:
        return _is_gguf_reference(self.model_name) or self.model_name in AVAILABLE_GGUF

    def load(self, cache_dir: Optional[str] = None):
        self._cache_dir = cache_dir
        resolved = self.resolve_alias(self.model_name)

        if _is_gguf_reference(resolved) or resolved in [v[0] for v in AVAILABLE_GGUF.values()]:
            self._load_gguf(resolved)
        else:
            self._load_transformers(resolved, cache_dir)

    def _load_gguf(self, resolved: str):
        try:
            from llama_cpp import Llama
        except ImportError:
            raise ImportError(
                "llama-cpp-python not installed.\n"
                "Run:  CMAKE_ARGS='-DGGML_NATIVE=OFF -DGGML_CPU=ON' "
                "pip install -e '.[gguf]'"
            )

        if ':' in resolved:
            repo_id, filename = resolved.split(':', 1)
            model_path = Llama.download_model(
                repo_id=repo_id,
                filename=filename,
                local_dir=self._cache_dir,
            )
        else:
            model_path = resolved

        self._gguf_path = model_path
        self._llama = Llama(
            model_path=model_path,
            n_ctx=4096,
            n_threads=4,
            verbose=False,
        )

    def _load_transformers(self, hf_name: str, cache_dir: Optional[str] = None):
        from transformers import AutoModelForCausalLM, AutoTokenizer

        self.tokenizer = AutoTokenizer.from_pretrained(
            hf_name, cache_dir=cache_dir, trust_remote_code=True,
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            hf_name, cache_dir=cache_dir,
            torch_dtype=torch.float32, device_map=self.device,
            trust_remote_code=True,
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

    def reload(self, new_model_name: str):
        self.model_name = new_model_name
        self.tokenizer = None
        self.model = None
        self._llama = None
        self._gguf_path = None
        self.load(self._cache_dir)

    def count_tokens(self, system_prompt: str, user_input: str) -> int:
        if self._llama is not None:
            text = f"system: {system_prompt}\nuser: {user_input}"
            return len(self._llama.tokenize(text.encode('utf-8')))
        if self.tokenizer is None:
            return 0
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]
        prompt = self.tokenizer.apply_chat_template(
            messages, tokenize=True, add_generation_prompt=True,
            enable_thinking=False,
        )
        return len(prompt)

    def _build_prompt(self, system_prompt: str, user_input: str) -> str:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input},
        ]
        return self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True,
            enable_thinking=False,
        )

    def _parse_response(self, full_text: str, prompt: str) -> str:
        marker = "assistant"
        if marker in full_text:
            response = full_text.split(marker)[-1].strip()
        else:
            response = full_text[len(prompt):].strip()
        response = response.lstrip("\n: ")
        if '<think>' in response and '</think>' in response:
            response = response.split('</think>')[-1].strip()
        elif '<think>' in response:
            response = response.replace('<think>', '').strip()
        return response

    def chat(
        self,
        system_prompt: str,
        user_input: str,
        max_new_tokens: Optional[int] = None,
    ) -> str:
        if self._server is not None:
            return self._server.chat(system_prompt, user_input, max_new_tokens)
        if self._llama is not None:
            return self._chat_gguf(system_prompt, user_input, max_new_tokens)
        return self._chat_transformers(system_prompt, user_input, max_new_tokens)

    def _chat_gguf(self, system_prompt: str, user_input: str, max_new_tokens: Optional[int] = None) -> str:
        result = self._llama.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            max_tokens=max_new_tokens or self.max_new_tokens,
            temperature=self.temperature,
            top_p=0.8,
        )
        return result['choices'][0]['message']['content'].strip()

    def _chat_transformers(self, system_prompt: str, user_input: str, max_new_tokens: Optional[int] = None) -> str:
        if self.tokenizer is None or self.model is None:
            return "Model not loaded. Run load() first."

        prompt = self._build_prompt(system_prompt, user_input)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens or self.max_new_tokens,
                temperature=self.temperature,
                do_sample=True,
                top_p=0.8,
                repetition_penalty=1.1,
                pad_token_id=self.tokenizer.pad_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )

        full_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return self._parse_response(full_text, prompt)

    def chat_stream(
        self,
        system_prompt: str,
        user_input: str,
        max_new_tokens: Optional[int] = None,
    ) -> Generator[str, None, str]:
        if self._server is not None:
            yield from self._server.chat_stream(system_prompt, user_input, max_new_tokens)
            return
        if self._llama is not None:
            yield from self._chat_stream_gguf(system_prompt, user_input, max_new_tokens)
            return

        if self.tokenizer is None or self.model is None:
            yield "Model not loaded."
            return ""

        prompt = self._build_prompt(system_prompt, user_input)
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        from transformers import TextIteratorStreamer

        streamer = TextIteratorStreamer(
            self.tokenizer, skip_prompt=True, skip_special_tokens=True,
        )

        generation_kwargs = dict(
            **inputs,
            max_new_tokens=max_new_tokens or self.max_new_tokens,
            temperature=self.temperature,
            do_sample=True,
            top_p=0.8,
            repetition_penalty=1.1,
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
            streamer=streamer,
        )

        thread = Thread(target=self.model.generate, kwargs=generation_kwargs)
        thread.start()

        full_response = ""
        for token in streamer:
            if token:
                full_response += token
                yield token

        thread.join()
        parsed = self._parse_response(prompt + full_response, prompt)
        return parsed

    def _chat_stream_gguf(self, system_prompt: str, user_input: str, max_new_tokens: Optional[int] = None):
        result = self._llama.create_chat_completion(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input},
            ],
            max_tokens=max_new_tokens or self.max_new_tokens,
            temperature=self.temperature,
            top_p=0.8,
            stream=True,
        )
        for chunk in result:
            delta = chunk['choices'][0]['delta'].get('content', '')
            if delta:
                yield delta

    def save(self, path: str = './models_local') -> str:
        if self._llama is not None:
            return self._gguf_path or ""
        os.makedirs(path, exist_ok=True)
        save_path = os.path.join(path, self.tag)
        self.model.save_pretrained(save_path)
        self.tokenizer.save_pretrained(save_path)
        return save_path
