"""配置数据模型 + 路径工具。

本模块故意不依赖 PySide6，保持纯 Python，方便 pytest 和 CLI 测试。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def resource_path(rel: str) -> Path:
    """在开发态和 PyInstaller 打包态都能找到 assets/ 下的资源。"""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return base / rel


def config_dir() -> Path:
    """返回 %APPDATA%\\CoinRain（不存在则创建）。"""
    appdata = os.environ.get("APPDATA")
    if appdata:
        d = Path(appdata) / "CoinRain"
    else:
        d = Path.home() / ".coinrain"
    d.mkdir(parents=True, exist_ok=True)
    return d


def config_path() -> Path:
    return config_dir() / "config.json"


import json
from dataclasses import dataclass, asdict


@dataclass
class Config:
    version: int
    income: int
    intensity: str      # "light" | "medium" | "heavy"
    mode: str           # "single" | "multi"
    time: str | None
    first_time: str | None
    last_time: str | None
    count: int | None
    coin_style: str     # "kaiyuan" | "yongle" | "xuanhe" | "longyang" | "modern_yuan"
    mixed_coins: bool
    installed_at: str   # ISO8601

    def save(self) -> None:
        config_path().write_text(
            json.dumps(asdict(self), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls) -> "Config | None":
        try:
            data = json.loads(config_path().read_text(encoding="utf-8"))
            return cls(**data)
        except (FileNotFoundError, json.JSONDecodeError, TypeError):
            return None

    @classmethod
    def exists(cls) -> bool:
        return config_path().exists()
