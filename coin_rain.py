"""金币雨入口 —— 解析 argv，派发到动画 / 配置 UI / 管理 UI。"""
from __future__ import annotations

import argparse
import os
import sys


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Coin Rain")
    p.add_argument("--rain", action="store_true", help="进入动画模式（任务计划触发用）")
    p.add_argument("--test", action="store_true", help="测试模式（配合 --rain）")
    p.add_argument("--nth", type=int, default=1, help="多次模式中这是第几次（1-based）")
    p.add_argument("--total", type=int, default=1, help="多次模式总次数")
    return p.parse_args(argv)


def _run_rain(args: argparse.Namespace) -> int:
    from PySide6.QtWidgets import QApplication
    from rain_window import CoinRainWindow, _compute_amount
    from fonts import load_embedded_fonts
    from config import Config

    cfg = Config.load()
    income = cfg.income if cfg else 300

    app = QApplication(sys.argv)
    load_embedded_fonts()
    app.setQuitOnLastWindowClosed(False)

    amount = _compute_amount(income=income, nth=args.nth, total=args.total)
    is_final = (args.nth == args.total) or args.test
    label = "今 日 到 账" if is_final else "当 前 已 到 账"

    w = CoinRainWindow()
    w.set_amount(amount, label)
    if cfg is not None:
        w.set_coin_style(cfg.coin_style, cfg.mixed_coins)
    w.start()
    return app.exec()


def _run_ui() -> int:
    from PySide6.QtWidgets import QApplication
    from fonts import load_embedded_fonts
    from config import Config
    from config_window import SetupWindow, ManageWindow

    app = QApplication(sys.argv)
    load_embedded_fonts()
    if Config.exists():
        w: object = ManageWindow()
    else:
        w = SetupWindow()
    w.show()
    return app.exec()


def main(argv: list[str] | None = None) -> int:
    os.environ.setdefault("QT_LOGGING_RULES", "*.debug=false;qt.qpa.*=false")
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    if args.rain:
        return _run_rain(args)
    return _run_ui()


if __name__ == "__main__":
    sys.exit(main())
