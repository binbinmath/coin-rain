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
