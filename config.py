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
