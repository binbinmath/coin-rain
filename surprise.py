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


def _days_subtitle(days: int) -> str | None:
    """spec §6：第 7 天 / 30 的倍数 / 365 的倍数。年优先于月。"""
    if days <= 0:
        return None
    if days >= 365 and days % 365 == 0:
        return f"陪 你 赚 了  {days // 365} 年"
    if days >= 30 and days % 30 == 0:
        return f"陪 你 赚 了  {days // 30} 个 月"
    if days == 7:
        return "陪 你 赚 了  1 周"
    return None


def _easter_subtitle(today: date) -> str | None:
    if today.month == 4 and today.day == 1:
        return "愚 人 节 快 乐  ☘"
    if today.month == 11 and today.day == 11:
        return "今 天 晚 饭  有 人 陪 么 ?"
    return None


DEFAULT_CAPTIONS: list[str] = [
    # 接地气职场（14）
    "晚 饭 加 鸡 腿",
    "今 天 又 值 了",
    "再 来 一 波",
    "周 五 倒 计 时  X",   # 模板，运行时填具体天数
    "领 导 今 天 笑 了 一 下",
    "摸 鱼 也 有 工 资",
    "打 工 人 之 光",
    "没 白 来",
    "今 天 再 撑 一 下",
    "钱 到 心 安",
    "今 日 KPI 已 完 成",
    "咖 啡 自 由 已 实 现",
    "晚 饭 涨 一 档",
    "社 畜 高 光 时 刻",
    # 文艺克制（15）
    "雨 落 如 约",
    "金 光 归 位",
    "今 夜 灯 下 值 得",
    "一 日 不 空",
    "钟 摆 不 停",
    "风 也 知 道",
    "账 上 有 光",
    "晚 一 些 也 没 关 系",
    "月 亮 也 在 看",
    "今 日 已 安",
    "落 雨 知 春",
    "青 灯 黄 卷",
    "河 水 不 急",
    "诚 意 已 至",
    "此 间 日 常",
    # 调皮温暖（15）
    "进 账 啦  ✦",
    "今 天 的 咖 啡 你 请",
    "奖 励 一 只 布 丁",
    "小 金 库 ＋＋",
    "钱 钱 来 了",
    "布 丁 自 由",
    "咖 啡 加 奶 油",
    "账 户 +1s",
    "来 了 来 了",
    "今 天 也 蛮 好 的",
    "留 一 颗 给 自 己",
    "小 happy 一 下",
    "gold gold gold",
    "日 子 在 鼓 掌",
    "我 替 你 高 兴",
]


def _default_caption(*, today: date, rng: random.Random) -> str:
    """从默认文案池随机抽一句。周末过滤掉"周五倒计时"模板。"""
    pool = DEFAULT_CAPTIONS
    if today.weekday() >= 5:  # 周六/周日
        pool = [c for c in pool if "周 五 倒 计 时" not in c]
    pick = rng.choice(pool)
    if "周 五 倒 计 时  X" in pick:
        # weekday: 周一=0 ... 周五=4 ... 周日=6
        delta = (4 - today.weekday()) % 7
        if delta == 0:
            return "今 天 就 是 周 五"
        pick = pick.replace("X", f"{delta} 天")
    return pick


def compute_subtitle(*, days_since_install: int, today: date,
                     daily_income: int, is_last_trigger: bool,
                     rng: random.Random | None = None) -> str:
    raise NotImplementedError


def compute_visual_overrides(*, today: date) -> dict:
    """spec §7.2：4/1 全反着掉，11/11 直径加倍。"""
    if today.month == 4 and today.day == 1:
        return {"flip_all": True}
    if today.month == 11 and today.day == 11:
        return {"size_scale": 2.0}
    return {}


def pick_lucky(*, rng: random.Random | None = None) -> bool:
    raise NotImplementedError


def pick_coin_mode(*, n_styles: int, rng: random.Random | None = None) -> int | None:
    raise NotImplementedError
