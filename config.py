import os
import torch
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Config:
    workspace_dir: str = './workspace'
    datasets_cache: str = './datasets_cache'
    models_dir: str = './models_local'
    embedding_dim: int = 768
    hidden_dims: list = field(default_factory=lambda: [1024, 512, 256, 128])
    num_classes: int = 1
    dropout: float = 0.3
    learning_rate: float = 0.001
    batch_size: int = 32
    num_epochs: int = 20
    user_name: str = 'User'
    ai_name: str = 'OpenSaw'
    device: str = 'auto'
    model_name: str = '/home/bitplugg/opensaw/models_local/qwen3-0.6b-heretic-q8_0.gguf'
    max_tokens: int = 150
    temperature: float = 0.7
    stream_mode: bool = True
    memory_mode: str = 'hybrid'  # 'tfidf', 'semantic', 'hybrid'

    def __post_init__(self):
        if self.device == 'auto':
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self._ensure_dirs()

    def _ensure_dirs(self):
        for d in [self.workspace_dir, self.datasets_cache, self.models_dir]:
            os.makedirs(d, exist_ok=True)

    @property
    def workspace_path(self) -> Path:
        return Path(self.workspace_dir).resolve()

    @property
    def memory_path(self) -> Path:
        return self.workspace_path / 'memory'


config = Config()
