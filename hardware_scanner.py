import psutil
import torch
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class HardwareProfile:
    cpu_count: int = 0
    cpu_percent: float = 0.0
    ram_total_gb: float = 0.0
    ram_available_gb: float = 0.0
    cuda_available: bool = False
    cuda_device_count: int = 0
    cuda_device_name: str = ''
    vram_total_gb: float = 0.0
    optimal_device: str = 'cpu'


def scan_hardware() -> HardwareProfile:
    profile = HardwareProfile()

    # CPU
    profile.cpu_count = psutil.cpu_count(logical=True)
    profile.cpu_percent = psutil.cpu_percent(interval=0.5)

    # RAM
    mem = psutil.virtual_memory()
    profile.ram_total_gb = round(mem.total / (1024 ** 3), 2)
    profile.ram_available_gb = round(mem.available / (1024 ** 3), 2)

    # CUDA
    profile.cuda_available = torch.cuda.is_available()
    if profile.cuda_available:
        profile.cuda_device_count = torch.cuda.device_count()
        profile.cuda_device_name = torch.cuda.get_device_name(0)
        profile.vram_total_gb = round(
            torch.cuda.get_device_properties(0).total_memory / (1024 ** 3), 2
        )

    profile.optimal_device = 'cuda' if profile.cuda_available else 'cpu'

    return profile


def get_device() -> str:
    return 'cuda' if torch.cuda.is_available() else 'cpu'
