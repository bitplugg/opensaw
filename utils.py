import json
import random
import os
from typing import Dict, Optional
from pathlib import Path


PREFIXES = [
    "Neon", "Cyber", "Quantum", "Neural", "Digital",
    "Synthetic", "Crystal", "Shadow", "Phantom", "Echo",
    "Plasma", "Binary", "Vector", "Matrix", "Core",
    "Flux", "Nova", "Pixel", "Rogue", "Vertex",
]

SUFFIXES = [
    "Core", "Mind", "Brain", "Engine", "Spike",
    "Node", "Matrix", "Vector", "Pulse", "Wave",
    "Blade", "Forge", "Link", "Mesh", "Spark",
    "Drive", "Hub", "Lens", "Port", "Shard",
]

VERSIONS = [f"v{i}" for i in range(1, 21)]


def generate_model_name() -> str:
    prefix = random.choice(PREFIXES)
    suffix = random.choice(SUFFIXES)
    version = random.choice(VERSIONS)
    return f"{prefix}-{suffix}-{version}"


LOGO = r"""
╔══════════════════════════════════════════════════════╗
║                                                      ║
║    ██████╗ ██████╗ ███████╗███╗   ██╗███████╗ █████╗ ██╗    ║
║   ██╔═══██╗██╔══██╗██╔════╝████╗  ██║██╔════╝██╔══██╗██║    ║
║   ██║   ██║██████╔╝█████╗  ██╔██╗ ██║███████╗███████║██║    ║
║   ██║   ██║██╔═══╝ ██╔══╝  ██║╚██╗██║╚════██║██╔══██║██║    ║
║   ╚██████╔╝██║     ███████╗██║ ╚████║███████║██║  ██║██║    ║
║    ╚═════╝ ╚═╝     ╚══════╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝╚═╝    ║
║                                                      ║
║          LOCAL AI FRAMEWORK  —  v1.0                ║
║        Tools: files · terminal · memory             ║
╚══════════════════════════════════════════════════════╝
"""


def get_logo() -> str:
    return LOGO


BUILD_HISTORY_FILE = 'build_history.json'
PROFILE_FILE = 'profile.json'


def save_build(model_name: str, metrics: Dict) -> Dict:
    history = []
    if os.path.exists(BUILD_HISTORY_FILE):
        try:
            with open(BUILD_HISTORY_FILE, 'r') as f:
                history = json.load(f)
        except (json.JSONDecodeError, IOError):
            history = []

    entry = {
        'model_name': model_name,
        'metrics': metrics,
        'build_id': len(history) + 1,
    }
    history.append(entry)

    with open(BUILD_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

    return entry


def load_build_history() -> list:
    if not os.path.exists(BUILD_HISTORY_FILE):
        return []
    try:
        with open(BUILD_HISTORY_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_profile(user_name: str, ai_name: str):
    profile = {
        'user_name': user_name,
        'ai_name': ai_name,
    }
    with open(PROFILE_FILE, 'w') as f:
        json.dump(profile, f, indent=2)


def load_profile() -> Dict:
    if not os.path.exists(PROFILE_FILE):
        return {}
    try:
        with open(PROFILE_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}
