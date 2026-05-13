"""在 QApplication 启动后加载嵌入的 TTF 字体。

打包后只随 exe 走 -Subset.ttf（项目实际用到的字符，~600 KB）；
仓库里的 -VariableFont.ttf 是用来跑 scripts/subset_fonts.py 的源料。
"""
from __future__ import annotations

from PySide6.QtGui import QFontDatabase

from config import resource_path


# 优先级：subset 版（生产）→ variable 版（开发态没跑过 subset 时的 fallback）
FONT_CANDIDATES = (
    ("Fraunces-Subset.ttf",         "Fraunces-VariableFont.ttf"),
    ("NotoSerifSC-Subset.ttf",      "NotoSerifSC-VariableFont.ttf"),
)


def load_embedded_fonts() -> None:
    """加载 Fraunces + Noto Serif SC。失败则静默（QSS 会 fallback）。"""
    for primary, fallback in FONT_CANDIDATES:
        for name in (primary, fallback):
            path = resource_path(f"assets/fonts/{name}")
            if path.exists():
                QFontDatabase.addApplicationFont(str(path))
                break
