"""金币雨主窗口（CoinRainWindow）+ 相关纯逻辑。"""
from __future__ import annotations


def _compute_amount(*, income: int, nth: int, total: int) -> int:
    """多次/单次模式下本次触发要显示的到账金额。

    - nth ∈ [1, total]；nth == total 时返回 income（闭合）
    - 否则按整数元四舍五入到 round(income * nth / total)
    """
    if nth == total:
        return income
    return round(income * nth / total)
