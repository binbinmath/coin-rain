"""配置数据模型 + 路径工具。

本模块故意不依赖 PySide6，保持纯 Python，方便 pytest 和 CLI 测试。

V2 schema（2026-04 升级，对应 claude design 的墨黑金新设计）：
- 雨势 4 档：light / medium / heavy / storm
- 多次模式直接存 times: list[str]，不再用 first/last/count 自动均分
- 不再保存 coin_style / mixed_coins —— 6 张 PNG 金币随机混合下落
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, asdict, field
from pathlib import Path


CONFIG_VERSION = 2


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


@dataclass
class Config:
    version: int
    income: int
    intensity: str               # "light" | "medium" | "heavy" | "storm"
    mode: str                    # "single" | "multi"
    time: str | None             # 单次模式：HH:MM
    times: list[str] = field(default_factory=list)  # 多次模式：["08:00", "13:00", ...]
    installed_at: str = ""       # ISO8601

    def save(self) -> None:
        config_path().write_text(
            json.dumps(asdict(self), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls) -> "Config | None":
        try:
            data = json.loads(config_path().read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return None
        # V1 → V2 兼容：把 first/last/count 转成 times
        if data.get("version", 1) < 2:
            data = _migrate_v1_to_v2(data)
        # 只保留我们认识的字段，丢掉历史多余字段
        keep = {"version", "income", "intensity", "mode", "time", "times", "installed_at"}
        clean = {k: v for k, v in data.items() if k in keep}
        try:
            return cls(**clean)
        except TypeError:
            return None

    @classmethod
    def exists(cls) -> bool:
        return config_path().exists()


def _migrate_v1_to_v2(data: dict) -> dict:
    """老 config（V1）→ 新 schema（V2）。"""
    mode = data.get("mode", "single")
    times: list[str] = []
    if mode == "multi":
        first = data.get("first_time")
        last = data.get("last_time")
        count = data.get("count")
        if first and last and count:
            times = _evenly_distribute(first, last, count)
    return {
        "version": CONFIG_VERSION,
        "income": data.get("income", 300),
        "intensity": data.get("intensity", "medium"),
        "mode": mode,
        "time": data.get("time"),
        "times": times,
        "installed_at": data.get("installed_at", ""),
    }


def _evenly_distribute(first: str, last: str, count: int) -> list[str]:
    """V1 兼容：把 [first, last] 上的 count 个均匀点列出来。"""
    fh, fm = map(int, first.split(":"))
    lh, lm = map(int, last.split(":"))
    f, l = fh * 60 + fm, lh * 60 + lm
    if count <= 1:
        return [first]
    step = (l - f) / (count - 1)
    return [f"{(f + round(step * i)) // 60:02d}:{(f + round(step * i)) % 60:02d}" for i in range(count)]
