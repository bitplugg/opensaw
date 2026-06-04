<div class="opensaw-hero">
<pre><code>
╔═══════════════════════════════════════╗
║              OpenSaw                  ║
║    Локальный AI-ассистент             ║
║    с душой и инструментами            ║
╚═══════════════════════════════════════╝
</code></pre>
</div>

<div class="opensaw-tagline">
  Твой личный AI.
  Полностью офлайн.
  Полностью твой.
</div>

<div class="opensaw-sub">
  Никаких облаков, никаких подписок, никакой отправки данных.
  Просто работает на твоём компьютере.
</div>

<div class="opensaw-stats">
  <div class="opensaw-stat">
    <div class="opensaw-stat-value blue">4</div>
    <div class="opensaw-stat-label">Движка моделей</div>
  </div>
  <div class="opensaw-stat">
    <div class="opensaw-stat-value green">3</div>
    <div class="opensaw-stat-label">Режима памяти</div>
  </div>
  <div class="opensaw-stat">
    <div class="opensaw-stat-value purple">10</div>
    <div class="opensaw-stat-label">Точек хуков</div>
  </div>
  <div class="opensaw-stat">
    <div class="opensaw-stat-value pink">∞</div>
    <div class="opensaw-stat-label">Плагинов</div>
  </div>
</div>

<div class="opensaw-install">

```bash
pip install -e . && opensaw chat
```

</div>

## Возможности

<div class="opensaw-features">

<div class="opensaw-feature">
  <span class="opensaw-feature-icon">🧠</span>
  <div class="opensaw-feature-title">Модели</div>
  <div class="opensaw-feature-desc">GGUF/llama.cpp для CPU, transformers для GPU. Любая архитектура — Qwen, Mistral, Llama.</div>
</div>

<div class="opensaw-feature">
  <span class="opensaw-feature-icon">💾</span>
  <div class="opensaw-feature-title">Память</div>
  <div class="opensaw-feature-desc">TF-IDF, семантическая или гибрид. Помнит диалоги между сессиями. Индексация PDF/DOCX.</div>
</div>

<div class="opensaw-feature">
  <span class="opensaw-feature-icon">🔧</span>
  <div class="opensaw-feature-title">Инструменты</div>
  <div class="opensaw-feature-desc">AI сам читает/пишет файлы и выполняет команды. Расширяется плагинами.</div>
</div>

<div class="opensaw-feature">
  <span class="opensaw-feature-icon">🔌</span>
  <div class="opensaw-feature-title">Плагины</div>
  <div class="opensaw-feature-desc">`.plugin` файлы, 10 точек хуков, AI-валидация. Замена UI, новые команды, инструменты.</div>
</div>

<div class="opensaw-feature">
  <span class="opensaw-feature-icon">🖥️</span>
  <div class="opensaw-feature-title">Интерфейсы</div>
  <div class="opensaw-feature-desc">TUI (Rich), GTK4, Telegram, Web — любой интерфейс через плагины.</div>
</div>

<div class="opensaw-feature">
  <span class="opensaw-feature-icon">🌐</span>
  <div class="opensaw-feature-title">Сервер</div>
  <div class="opensaw-feature-desc">FastAPI с автодокументацией. REST API для интеграции с чем угодно.</div>
</div>

</div>

## Быстрый старт

```bash
git clone git@github.com:bitplugg/opensaw.git
cd opensaw
python3 -m venv venv
source venv/bin/activate
pip install -e .
pip install -e ".[gguf]"
opensaw setup
opensaw chat
```

На слабых CPU (Celeron N5095, без AVX2):

```bash
./setup-gguf.sh
./venv/bin/opensaw chat
```

## Документация

<div class="opensaw-links">

<a href="setup.md" class="opensaw-link-card">
  <span class="link-icon">📦</span>
  Установка
</a>

<a href="cli-reference.md" class="opensaw-link-card">
  <span class="link-icon">⌨️</span>
  CLI Reference
</a>

<a href="plugins.md" class="opensaw-link-card">
  <span class="link-icon">🔌</span>
  Плагины
</a>

<a href="opensawcore.md" class="opensaw-link-card">
  <span class="link-icon">📘</span>
  OpenSawCore SDK
</a>

<a href="writing-plugins.md" class="opensaw-link-card">
  <span class="link-icon">✍️</span>
  Написание плагина
</a>

<a href="plugin-examples.md" class="opensaw-link-card">
  <span class="link-icon">🎯</span>
  Примеры плагинов
</a>

<a href="model-guide.md" class="opensaw-link-card">
  <span class="link-icon">🤖</span>
  Выбор модели
</a>

<a href="gguf.md" class="opensaw-link-card">
  <span class="link-icon">⚙️</span>
  GGUF сборка
</a>

<a href="memory-system.md" class="opensaw-link-card">
  <span class="link-icon">💾</span>
  Система памяти
</a>

<a href="tools-reference.md" class="opensaw-link-card">
  <span class="link-icon">🔧</span>
  Инструменты AI
</a>

<a href="api.md" class="opensaw-link-card">
  <span class="link-icon">🌐</span>
  API сервер
</a>

<a href="architecture.md" class="opensaw-link-card">
  <span class="link-icon">🏗️</span>
  Архитектура
</a>

<a href="troubleshooting.md" class="opensaw-link-card">
  <span class="link-icon">🩹</span>
  Troubleshooting
</a>

<a href="faq.md" class="opensaw-link-card">
  <span class="link-icon">❓</span>
  FAQ
</a>

</div>
