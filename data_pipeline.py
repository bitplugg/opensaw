import os
import re
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from typing import List, Optional, Tuple, Union
from pathlib import Path

from config import config


class OpenSawDataset(Dataset):
    def __init__(
        self,
        texts: Optional[List[str]] = None,
        labels: Optional[Union[List[int], np.ndarray]] = None,
        memory_texts: Optional[List[str]] = None,
        embedding_dim: Optional[int] = None,
    ):
        self.embedding_dim = embedding_dim or config.embedding_dim

        if texts is None:
            texts = self._load_from_cache()

        self.texts: List[str] = texts

        if labels is None:
            self.labels = np.zeros(len(self.texts), dtype=np.float32)
        else:
            self.labels = np.array(labels, dtype=np.float32)

        if memory_texts:
            self.texts.extend(memory_texts)
            memory_labels = np.ones(len(memory_texts), dtype=np.float32)
            self.labels = np.concatenate([self.labels, memory_labels])

        self.vectors: List[np.ndarray] = [self._vectorize(t) for t in self.texts]

    def _load_from_cache(self) -> List[str]:
        cache_dir = config.datasets_cache
        if os.path.exists(cache_dir):
            try:
                from datasets import load_from_disk
                ds = load_from_disk(cache_dir)
                if 'text' in ds.column_names:
                    return list(ds['text'])[:200]
                elif 'sentence' in ds.column_names:
                    return list(ds['sentence'])[:200]
                else:
                    col = ds.column_names[0]
                    return [str(s) for s in ds[col][:200]]
            except Exception:
                pass
        return ["sample initialization text for OpenSaw neural network training"] * 20

    def _vectorize(self, text: str) -> np.ndarray:
        vec = np.zeros(self.embedding_dim, dtype=np.float32)
        words = re.findall(r'[a-zA-Zа-яА-ЯёЁ]+', text.lower())
        if not words:
            return vec
        for word in words:
            idx = hash(word) % self.embedding_dim
            vec[idx] += 1.0
        norm = np.linalg.norm(vec)
        if norm > 1e-8:
            vec /= norm
        return vec

    def __len__(self) -> int:
        return len(self.vectors)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, torch.Tensor]:
        return (
            torch.FloatTensor(self.vectors[idx]),
            torch.FloatTensor([self.labels[idx]]),
        )


def create_dataloader(
    texts: Optional[List[str]] = None,
    labels: Optional[List[int]] = None,
    memory_texts: Optional[List[str]] = None,
    batch_size: Optional[int] = None,
    shuffle: bool = True,
) -> DataLoader:
    dataset = OpenSawDataset(
        texts=texts,
        labels=labels,
        memory_texts=memory_texts,
    )
    return DataLoader(
        dataset,
        batch_size=batch_size or config.batch_size,
        shuffle=shuffle,
    )
