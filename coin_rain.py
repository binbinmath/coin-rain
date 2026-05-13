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


def _days_since(installed_at: str, today) -> int:
    """从 ISO8601 字符串算到今天的天数（含今天 → +1，第一天即第 1 天）。
    config 没填或解析失败时回退为 1。"""
    from datetime import datetime
    if not installed_at:
        return 1
    try:
        d0 = datetime.fromisoformat(installed_at).date()
    except ValueError:
        return 1
    return max((today - d0).days + 1, 1)


def _run_rain(args: argparse.Namespace) -> int:
    from datetime import date
    from PySide6.QtWidgets import QApplication
    from rain_window import CoinRainWindow, _compute_amount, _load_coin_pixmaps
    from fonts import load_embedded_fonts
    from config import Config
    import surprise

    cfg = Config.load()
    income = cfg.income if cfg else 300
    intensity = cfg.intensity if cfg else "medium"
    installed_at = cfg.installed_at if cfg else ""

    app = QApplication(sys.argv)
    load_embedded_fonts()

    amount = _compute_amount(income=income, nth=args.nth, total=args.total)
    is_last = (args.nth == args.total) or args.test
    label = "今 日 到 账" if is_last else "当 前 已 到 账"

    today = date.today()
    days = _days_since(installed_at, today)

    subtitle = surprise.compute_subtitle(
        days_since_install=days,
        today=today,
        daily_income=income,
        is_last_trigger=is_last,
    )
    visual = surprise.compute_visual_overrides(today=today)
    lucky = surprise.pick_lucky()
    n_styles = len(_load_coin_pixmaps())
    coin_mode = surprise.pick_coin_mode(n_styles=n_styles)

    w = CoinRainWindow()
    w.set_amount(amount, label)
    w.set_intensity(intensity)
    w.set_subtitle(subtitle)
    w.set_visual_overrides(visual)
    w.set_lucky_coin(lucky)
    w.set_coin_mode(coin_mode)
    w.finished.connect(app.quit)
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
