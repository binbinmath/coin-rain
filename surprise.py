"""惊喜与乐趣层：副标优先级引擎 + 节日表 + 视觉 overrides + 幸运币/金币模式抽签。

纯 Python（无 Qt 依赖），所有规则集中在此。
"""
from __future__ import annotations

import math
import random
from datetime import date, timedelta


# 农历节日：spec §5.3，覆盖 2026–2035
SPRING_FESTIVAL: dict[int, date] = {
    2026: date(2026, 2, 17),
    2027: date(2027, 2, 6),
    2028: date(2028, 1, 26),
    2029: date(2029, 2, 13),
    2030: date(2030, 2, 3),
    2031: date(2031, 1, 23),
    2032: date(2032, 2, 11),
    2033: date(2033, 1, 31),
    2034: date(2034, 2, 19),
    2035: date(2035, 2, 8),
}

DRAGON_BOAT: dict[int, date] = {
    2026: date(2026, 6, 19),
    2027: date(2027, 6, 9),
    2028: date(2028, 5, 28),
    2029: date(2029, 6, 16),
    2030: date(2030, 6, 5),
    2031: date(2031, 6, 24),
    2032: date(2032, 6, 12),
    2033: date(2033, 6, 1),
    2034: date(2034, 6, 21),
    2035: date(2035, 6, 10),
}

MID_AUTUMN: dict[int, date] = {
    2026: date(2026, 9, 25),
    2027: date(2027, 9, 15),
    2028: date(2028, 10, 3),
    2029: date(2029, 9, 22),
    2030: date(2030, 9, 12),
    2031: date(2031, 10, 1),
    2032: date(2032, 9, 19),
    2033: date(2033, 9, 8),
    2034: date(2034, 9, 27),
    2035: date(2035, 9, 16),
}

QINGMING: dict[int, date] = {
    2026: date(2026, 4, 5),
    2027: date(2027, 4, 5),
    2028: date(2028, 4, 4),
    2029: date(2029, 4, 4),
    2030: date(2030, 4, 5),
    2031: date(2031, 4, 5),
    2032: date(2032, 4, 4),
    2033: date(2033, 4, 4),
    2034: date(2034, 4, 5),
    2035: date(2035, 4, 5),
}


def _cumulative_node_amount(*, days: int, income: int) -> int | None:
    """如果第 `days` 天命中累计节点，返回该节点金额；否则 None。

    规则 (spec §4.1)：
      N = floor(log10(10*I))
      第 1 次节点：10^N（在前 10 天内必命中）
      第 2 次节点：10^(N+1)（10–100 天）
      之后每涨一个 10^(N+1) 命中一次（2·10^(N+1)、3·10^(N+1)、...）
    """
    if income <= 0 or days < 1:
        return None
    total_today = days * income
    total_yesterday = (days - 1) * income
    n = int(math.floor(math.log10(10 * income)))
    first = 10 ** n
    second = 10 ** (n + 1)
    if total_yesterday < first <= total_today:
        return first
    if total_today >= second:
        k_today = total_today // second
        k_yesterday = total_yesterday // second
        if k_today > k_yesterday:
            return int(k_today * second)
    return None


# (公历日期, 当天文案, 前一天文案 or None)
# 顺序即优先级（前面的先命中）
_FIXED_HOLIDAYS = [
    ((1, 1),   "元 旦 快 乐",       "预 祝 元 旦 快 乐"),
    ((5, 1),   "劳 动 节 快 乐",     "预 祝 五 一 快 乐"),
    ((10, 1),  "国 庆 快 乐  ✦",     "预 祝 国 庆 快 乐"),
    ((10, 31), "万 圣 节 快 乐  🎃",  None),
    ((12, 25), "圣 诞 快 乐  ★",     None),
]

_LUNAR_HOLIDAYS = [
    (SPRING_FESTIVAL, "春 节 快 乐  ✦",  "预 祝 春 节 快 乐"),
    (DRAGON_BOAT,     "端 午 安 康",      "预 祝 端 午 安 康"),
    (MID_AUTUMN,      "中 秋 快 乐",      "预 祝 中 秋 团 圆"),
    (QINGMING,        "清 明 节 安 康",    "预 祝 清 明 假 期"),
]


def _holiday_subtitle(today: date) -> str | None:
    """如果今天 / 明天是节日，返回对应文案；否则 None。"""
    tomorrow = today + timedelta(days=1)
    for (m, d), day_text, eve_text in _FIXED_HOLIDAYS:
        if today.month == m and today.day == d:
            return day_text
        if eve_text and tomorrow.month == m and tomorrow.day == d:
            return eve_text
    for table, day_text, eve_text in _LUNAR_HOLIDAYS:
        target = table.get(today.year)
        if target == today:
            return day_text
        target_next = table.get(tomorrow.year)
        if target_next and target_next == tomorrow and eve_text:
            return eve_text
    return None


def compute_subtitle(*, days_since_install: int, today: date,
                     daily_income: int, is_last_trigger: bool,
                     rng: random.Random | None = None) -> str:
    raise NotImplementedError


def compute_visual_overrides(*, today: date) -> dict:
    raise NotImplementedError


def pick_lucky(*, rng: random.Random | None = None) -> bool:
    raise NotImplementedError


def pick_coin_mode(*, n_styles: int, rng: random.Random | None = None) -> int | None:
    raise NotImplementedError
