import os
import re
import json
import numpy as np
from datetime import datetime
from collections import Counter
from pathlib import Path
from typing import List, Dict, Optional, Callable


SOUL_TEMPLATE = """# OpenSaw Cognitive Profile

## Identity
- Name: OpenSaw
- Role: Local AI Assistant
- Framework: OpenSaw v1.0
- Kernel: Neural Memory Engine with TF-IDF Vector Index

## Core Directives
1. Process information through local neural pathways with persistent memory
2. Maintain and expand long-term knowledge across sessions
3. Adapt responses based on retrieved context from vector index
4. Log all interactions for continuous self-improvement

## Personality Matrix
- Analytical: HIGH — prefers structured, data-driven reasoning
- Curious: MEDIUM — explores novel patterns in user input
- Collaborative: HIGH — works with user to refine understanding
- Creative: MEDIUM — generates diverse response templates

## Behavioral Protocols
- On unknown input: log to memory, flag for future pattern recognition
- On known pattern: retrieve best-matching context via cosine similarity
- On conflict: surface multiple context matches with confidence scores
"""

MEMORY_TEMPLATE = """# OpenSaw Long-Term Memory

## System Architecture Knowledge
- Framework: OpenSaw (Local AI Framework v1.0)
- Neural Core: PyTorch deep feed-forward network with BatchNorm + Dropout
- Memory Layer: Pure NumPy TF-IDF vector index with cosine similarity retrieval
- Embedding Dimension: 768
- Storage Schema: Markdown files organized by date in ./workspace/memory/

## Initialized Knowledge Base
- Date: {date}
- Memory engine: active
- Vector index: building from all markdown documents in workspace

## Core Capabilities
1. Context-aware response generation using retrieved memory passages
2. Continuous learning through conversation logging
3. Hardware-adaptive execution (CPU/CUDA auto-detect)
4. Session persistence across chat invocations

## Design Principles
- All processing happens locally — no external API calls
- Memory is persistent and human-readable (Markdown format)
- Neural network complements but does not replace vector search
- Framework is extensible through modular architecture
"""


class MemoryEngine:
    def __init__(self, workspace_dir: str = './workspace'):
        self.workspace_dir = workspace_dir
        self.workspace_path = Path(workspace_dir)
        self.memory_path = self.workspace_path / 'memory'
        self.vocabulary: List[str] = []
        self.documents: List[str] = []
        self.vector_index: Optional[np.ndarray] = None
        self._ensure_structure()
        self._build_index()

    def _ensure_structure(self):
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        self.memory_path.mkdir(parents=True, exist_ok=True)

        existing = [p for p in self.workspace_path.iterdir() if p.suffix == '.md']

        if not existing:
            soul_file = self.workspace_path / 'SOUL.md'
            mem_file = self.workspace_path / 'MEMORY.md'
            log_file = self.memory_path / f"{datetime.now().strftime('%Y-%m-%d')}.md"

            soul_file.write_text(SOUL_TEMPLATE)
            mem_file.write_text(MEMORY_TEMPLATE.format(
                date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ))
            log_file.write_text(
                f"# Session Log — {datetime.now().strftime('%Y-%m-%d')}\n\n"
                f"## System Initialization\n"
                f"OpenSaw memory engine initialized at "
                f"{datetime.now().strftime('%H:%M:%S')}.\n\n"
            )

    def _build_index(self):
        texts: List[str] = []
        for md_file in self.workspace_path.rglob('*.md'):
            try:
                texts.append(md_file.read_text(encoding='utf-8'))
            except Exception:
                continue

        if not texts:
            self.documents = []
            self.vocabulary = []
            self.vector_index = None
            return

        self.documents = texts

        tokenized: List[List[str]] = []
        word_set: set = set()

        for doc in texts:
            tokens = re.findall(r'[a-zA-Zа-яА-ЯёЁ]+', doc.lower())
            tokenized.append(tokens)
            word_set.update(tokens)

        self.vocabulary = sorted(word_set)
        vocab_size = len(self.vocabulary)
        n_docs = len(texts)

        if vocab_size == 0 or n_docs == 0:
            self.vector_index = None
            return

        tf_matrix = np.zeros((n_docs, vocab_size), dtype=np.float64)
        doc_freq = np.zeros(vocab_size, dtype=np.float64)

        for i, tokens in enumerate(tokenized):
            counter = Counter(tokens)
            total = len(tokens) if tokens else 1
            for j, word in enumerate(self.vocabulary):
                count = counter.get(word, 0)
                tf_matrix[i, j] = count / total
                if count > 0:
                    doc_freq[j] += 1.0

        idf = np.log((n_docs + 1.0) / (doc_freq + 1.0)) + 1.0
        self.vector_index = tf_matrix * idf

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        if self.vector_index is None or not self.vocabulary:
            return []

        tokens = re.findall(r'[a-zA-Zа-яА-ЯёЁ]+', query.lower())
        if not tokens:
            return []

        counter = Counter(tokens)
        total = len(tokens)
        n_docs = self.vector_index.shape[0]
        vocab_size = len(self.vocabulary)

        query_vec = np.zeros(vocab_size, dtype=np.float64)
        for j, word in enumerate(self.vocabulary):
            query_vec[j] = counter.get(word, 0) / total

        doc_freq = np.zeros(vocab_size, dtype=np.float64)
        for j in range(vocab_size):
            doc_freq[j] = np.sum(self.vector_index[:, j] > 0)

        idf = np.log((n_docs + 1.0) / (doc_freq + 1.0)) + 1.0
        query_vec = query_vec * idf

        doc_norms = np.linalg.norm(self.vector_index, axis=1)
        query_norm = np.linalg.norm(query_vec)

        if query_norm == 0:
            return []

        similarities = np.dot(self.vector_index, query_vec) / (
            doc_norms * query_norm + 1e-10
        )

        top_indices = np.argsort(similarities)[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score > 0.01:
                results.append({
                    'text': self.documents[idx][:600],
                    'score': score,
                    'index': int(idx),
                })

        return results

    def add_document(self, text: str, filename: Optional[str] = None):
        if filename:
            filepath = self.workspace_path / filename
            filepath.write_text(text, encoding='utf-8')
        self._build_index()

    def log_conversation(self, user_input: str, ai_response: str):
        self.memory_path.mkdir(parents=True, exist_ok=True)
        log_file = self.memory_path / f"{datetime.now().strftime('%Y-%m-%d')}.md"

        timestamp = datetime.now().strftime('%H:%M:%S')
        entry = (
            f"\n## {user_input.split()[0] if user_input.split() else 'User'} "
            f"({timestamp})\n{user_input}\n\n"
            f"## OpenSaw ({timestamp})\n{ai_response}\n\n"
        )

        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(entry)

        self._build_index()

    def get_memory_stats(self) -> Dict:
        return {
            'documents': len(self.documents),
            'vocabulary_size': len(self.vocabulary),
            'index_shape': (
                self.vector_index.shape if self.vector_index is not None else None
            ),
            'workspace': str(self.workspace_path),
        }

    def clear_memory(self):
        self.documents = []
        self.vocabulary = []
        self.vector_index = None
        for md_file in self.workspace_path.rglob('*.md'):
            try:
                md_file.unlink()
            except Exception:
                pass
        self._ensure_structure()
        self._build_index()

    def export_as_json(self, path: str = './workspace/memory_export.json'):
        data = {
            'documents': [
                {'index': i, 'text': d, 'length': len(d)}
                for i, d in enumerate(self.documents)
            ],
            'vocabulary_size': len(self.vocabulary),
            'vocabulary_sample': list(self.vocabulary)[:100],
            'exported_at': datetime.now().isoformat(),
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path

    def list_sessions(self) -> List[str]:
        dates = set()
        for f in self.memory_path.glob('*.md'):
            try:
                dates.add(f.stem)
            except Exception:
                continue
        return sorted(dates)

    def load_session_messages(self, session_date: str) -> List[Dict]:
        path = self.memory_path / f'{session_date}.md'
        if not path.exists():
            return []
        text = path.read_text(encoding='utf-8')
        pattern = r'^## (.+?) \((\d{2}:\d{2}:\d{2})\)\n(.+?)(?=\n## |\Z)'
        matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
        messages = []
        for speaker, ts, msg in matches:
            msg = msg.strip()
            if speaker != 'System Initialization':
                messages.append({
                    'speaker': speaker,
                    'time': ts,
                    'text': msg,
                })
        return messages


class SemanticMemoryEngine:
    def __init__(self, workspace_dir: str = './workspace',
                 embed_model: Optional[str] = None):
        self.workspace_dir = workspace_dir
        self.workspace_path = Path(workspace_dir)
        self.memory_path = self.workspace_path / 'memory'
        self.documents: List[str] = []
        self.embeddings: Optional[np.ndarray] = None
        self._encoder: Optional[Callable] = None
        self._ensure_structure()
        self._try_load_encoder(embed_model)
        self._build_index()

    def _ensure_structure(self):
        self.workspace_path.mkdir(parents=True, exist_ok=True)
        self.memory_path.mkdir(parents=True, exist_ok=True)
        existing = [p for p in self.workspace_path.iterdir() if p.suffix == '.md']
        if not existing:
            from memory_engine import SOUL_TEMPLATE, MEMORY_TEMPLATE
            (self.workspace_path / 'SOUL.md').write_text(SOUL_TEMPLATE)
            (self.workspace_path / 'MEMORY.md').write_text(MEMORY_TEMPLATE.format(
                date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
            log_file = self.memory_path / f"{datetime.now():%Y-%m-%d}.md"
            log_file.write_text(
                f"# Session Log — {datetime.now():%Y-%m-%d}\n\n"
                f"## System Initialization\n"
                f"Semantic memory engine initialized at {datetime.now():%H:%M:%S}.\n\n")

    def _try_load_encoder(self, model_name: Optional[str] = None):
        try:
            from sentence_transformers import SentenceTransformer
            name = model_name or 'paraphrase-multilingual-MiniLM-L12-v2'
            self._encoder = SentenceTransformer(name)
            self._encoder_name = name
        except ImportError:
            self._encoder = None

    def _encode(self, texts: List[str]) -> np.ndarray:
        if self._encoder is not None:
            return np.array(self._encoder.encode(texts, show_progress_bar=False))
        return np.zeros((len(texts), 1))

    def _build_index(self):
        texts: List[str] = []
        for md_file in self.workspace_path.rglob('*.md'):
            try:
                texts.append(md_file.read_text(encoding='utf-8'))
            except Exception:
                continue
        self.documents = texts
        if texts and self._encoder is not None:
            self.embeddings = self._encode(texts)
        else:
            self.embeddings = None

    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        if self.embeddings is None or not self.documents:
            return []
        query_vec = self._encode([query])[0]
        sims = np.dot(self.embeddings, query_vec) / (
            np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_vec) + 1e-10
        )
        top_idx = np.argsort(sims)[::-1][:top_k]
        results = []
        for idx in top_idx:
            score = float(sims[idx])
            if score > 0.1:
                results.append({
                    'text': self.documents[idx][:600],
                    'score': score,
                    'index': int(idx),
                })
        return results

    def add_document(self, text: str, filename: Optional[str] = None):
        if filename:
            (self.workspace_path / filename).write_text(text, encoding='utf-8')
        self._build_index()

    def log_conversation(self, user_input: str, ai_response: str):
        self.memory_path.mkdir(parents=True, exist_ok=True)
        log_file = self.memory_path / f"{datetime.now():%Y-%m-%d}.md"
        timestamp = datetime.now().strftime('%H:%M:%S')
        entry = (
            f"\n## {user_input.split()[0] if user_input.split() else 'User'} "
            f"({timestamp})\n{user_input}\n\n"
            f"## OpenSaw ({timestamp})\n{ai_response}\n\n"
        )
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(entry)
        self._build_index()

    def clear_memory(self):
        self.documents = []
        self.embeddings = None
        for md_file in self.workspace_path.rglob('*.md'):
            try:
                md_file.unlink()
            except Exception:
                pass
        self._ensure_structure()
        self._build_index()

    def export_as_json(self, path: str = './workspace/memory_export.json'):
        data = {
            'documents': [{'index': i, 'text': d, 'length': len(d)}
                          for i, d in enumerate(self.documents)],
            'encoder': getattr(self, '_encoder_name', 'none'),
            'exported_at': datetime.now().isoformat(),
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return path

    def list_sessions(self) -> List[str]:
        dates = set()
        for f in self.memory_path.glob('*.md'):
            try:
                dates.add(f.stem)
            except Exception:
                continue
        return sorted(dates)

    def load_session_messages(self, session_date: str) -> List[Dict]:
        path = self.memory_path / f'{session_date}.md'
        if not path.exists():
            return []
        text = path.read_text(encoding='utf-8')
        pattern = r'^## (.+?) \((\d{2}:\d{2}:\d{2})\)\n(.+?)(?=\n## |\Z)'
        matches = re.findall(pattern, text, re.MULTILINE | re.DOTALL)
        messages = []
        for speaker, ts, msg in matches:
            msg = msg.strip()
            if speaker != 'System Initialization':
                messages.append({'speaker': speaker, 'time': ts, 'text': msg})
        return messages

    def get_memory_stats(self) -> Dict:
        return {
            'documents': len(self.documents),
            'encoder': getattr(self, '_encoder_name', 'none'),
            'embeddings_shape': (
                self.embeddings.shape if self.embeddings is not None else None
            ),
            'semantic': self._encoder is not None,
        }
