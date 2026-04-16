"""金币雨入口 —— 解析 argv，派发到动画 / 配置 UI / 管理 UI。

当前阶段（阶段 1）只支持动画模式；UI 派发在阶段 2 接入。
"""
from __future__ import annotations

import os
import sys


def main() -> int:
    os.environ.setdefault("QT_LOGGING_RULES", "*.debug=false;qt.qpa.*=false")

    from PySide6.QtWidgets import QApplication
    from rain_window import CoinRainWindow

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    w = CoinRainWindow()
    w.start()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
