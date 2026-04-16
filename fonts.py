"""在 QApplication 启动后加载嵌入的 TTF 字体。"""
from __future__ import annotations

from PySide6.QtGui import QFontDatabase

from config import resource_path


def load_embedded_fonts() -> None:
    """加载 Fraunces + Noto Serif SC。失败则静默（QSS 会 fallback）。"""
    for ttf in ("Fraunces-VariableFont.ttf", "NotoSerifSC-VariableFont.ttf"):
        path = resource_path(f"assets/fonts/{ttf}")
        if path.exists():
            QFontDatabase.addApplicationFont(str(path))
