# Coin Rain · 惊喜与乐趣层（v3）实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不破坏 v2 核心 ritual 的前提下，给金币雨加上副标优先级引擎、节日招呼、累计/天数里程碑、隐藏日期彩蛋、3% 幸运币、80/20 单一/混合金币模式。

**Architecture:** 新增纯 Python 模块 `surprise.py`（无 Qt 依赖、可单测），承担所有日期/金额规则计算与文案池抽取。`coin_rain.py` 启动时调用 `surprise` 算出本次的副标 / 视觉 overrides / 幸运币 / 金币模式，传给 `CoinRainWindow`。`rain_window.py` 增加 setter + 渲染层，包括上方幸运币提示、下方副标行（覆盖原 `label`）、4/1 全反、11/11 直径加倍。配置 schema 不变（用 `installed_at` 现算天数）。

**Tech Stack:** Python 3.11、PySide6、pytest。新模块全部纯 Python；视觉改动落在 QPainter 层。

---

## 文件结构

| 文件 | 改动类型 | 责任 |
|---|---|---|
| `surprise.py` | 新建 | 副标优先级引擎、农历节日表、累计/天数节点公式、文案池、视觉 overrides、幸运币/金币模式抽签 |
| `tests/test_surprise.py` | 新建 | 覆盖以上规则的单元测试 |
| `rain_window.py` | 修改 | 新增 `set_subtitle / set_lucky_coin / set_visual_overrides / set_coin_mode`；新增上方幸运币提示绘制；副标行改用 `_subtitle`（替换 `_label_text` 用法）；`_make_coin` 读 visual overrides 决定翻面、直径倍率、style_idx；幸运币 hero 渲染 |
| `coin_rain.py` | 修改 | `_run_rain` 启动时调 surprise 算 subtitle/visual/lucky/coin_mode，传给窗口 |
| `config.py` | 不动 | `installed_at` 已存在 |

`surprise.py` 接口（all pure-Python）：

```python
def compute_subtitle(*, days_since_install: int, today: date,
                     daily_income: int, is_last_trigger: bool,
                     rng: random.Random | None = None) -> str: ...

def compute_visual_overrides(*, today: date) -> dict: ...
    # → {} | {"flip_all": True} | {"size_scale": 2.0}

def pick_lucky(*, rng: random.Random | None = None) -> bool: ...
    # → 3% True

def pick_coin_mode(*, n_styles: int, rng: random.Random | None = None) -> int | None: ...
    # → None = 混合（每枚独立）；非 None = 全场用这个 style_idx
```

---

## Task 1: 建 surprise.py 骨架与农历/清明日期表

**Files:**
- Create: `surprise.py`

- [ ] **Step 1: 写最小骨架（datetime import + 日期表常量 + 空函数）**

```python
"""惊喜与乐趣层：副标优先级引擎 + 节日表 + 视觉 overrides + 幸运币/金币模式抽签。

纯 Python（无 Qt 依赖），所有规则集中在此。
"""
from __future__ import annotations

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
```

- [ ] **Step 2: 提交骨架**

```bash
git add surprise.py
git commit -m "feat(surprise): scaffold module with lunar/qingming date tables"
```

---

## Task 2: 累计金额节点公式

**Files:**
- Create: `tests/test_surprise.py`
- Modify: `surprise.py`

- [ ] **Step 1: 写失败的测试**

```python
# tests/test_surprise.py
import random
from datetime import date
from surprise import _cumulative_node_amount


def test_cumulative_first_node_at_10x_daily():
    # I=200 → N=floor(log10(2000))=3 → 第 1 次节点 10^3=1000，命中第 5 天
    assert _cumulative_node_amount(days=4, income=200) is None  # 4*200=800 < 1000
    assert _cumulative_node_amount(days=5, income=200) == 1000  # 5*200=1000 ≥ 1000
    assert _cumulative_node_amount(days=6, income=200) is None  # 已过节点


def test_cumulative_second_node_at_10x_first():
    # I=200 第 2 次：10^4=10000，命中第 50 天
    assert _cumulative_node_amount(days=49, income=200) is None
    assert _cumulative_node_amount(days=50, income=200) == 10000


def test_cumulative_third_and_beyond_every_10pow_n_plus_1():
    # I=200，第 3 次 = 20000（第 100 天），第 4 次 = 30000（第 150 天）
    assert _cumulative_node_amount(days=100, income=200) == 20000
    assert _cumulative_node_amount(days=150, income=200) == 30000
    assert _cumulative_node_amount(days=149, income=200) is None


def test_cumulative_low_income():
    # I=50 → N=floor(log10(500))=2 → 第 1 次 100（第 2 天）；第 2 次 1000（第 20 天）
    assert _cumulative_node_amount(days=2, income=50) == 100
    assert _cumulative_node_amount(days=20, income=50) == 1000


def test_cumulative_high_income():
    # I=3000 → N=floor(log10(30000))=4 → 第 1 次 10000（第 4 天）；第 2 次 100000（第 34 天）
    assert _cumulative_node_amount(days=4, income=3000) == 10000
    assert _cumulative_node_amount(days=34, income=3000) == 100000
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_surprise.py -v`
Expected: FAIL with ImportError (`_cumulative_node_amount` 还没实现)

- [ ] **Step 3: 实现 `_cumulative_node_amount`**

在 `surprise.py` 顶部 import 下方加：

```python
import math


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
    # 第 1 次
    if total_yesterday < first <= total_today:
        return first
    # 第 2+ 次：second, 2*second, 3*second, ...
    if total_today >= second:
        # 找最大的 k 使 k*second ≤ total_today
        k_today = total_today // second
        k_yesterday = total_yesterday // second
        if k_today > k_yesterday:
            return int(k_today * second)
    return None
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest tests/test_surprise.py -v`
Expected: 5 passed

- [ ] **Step 5: 提交**

```bash
git add surprise.py tests/test_surprise.py
git commit -m "feat(surprise): cumulative milestone amount formula"
```

---

## Task 3: 节日命中检测（公历 + 农历 + 前一天）

**Files:**
- Modify: `surprise.py`, `tests/test_surprise.py`

- [ ] **Step 1: 写失败的测试**

加到 `tests/test_surprise.py`：

```python
from surprise import _holiday_subtitle


def test_holiday_chunjie_day_of():
    # 2026 春节：2/17
    assert _holiday_subtitle(date(2026, 2, 17)) == "春 节 快 乐  ✦"


def test_holiday_chunjie_eve():
    assert _holiday_subtitle(date(2026, 2, 16)) == "预 祝 春 节 快 乐"


def test_holiday_yuandan_day_of():
    assert _holiday_subtitle(date(2027, 1, 1)) == "元 旦 快 乐"


def test_holiday_yuandan_eve():
    # 12/31 是上一年的元旦前一天
    assert _holiday_subtitle(date(2026, 12, 31)) == "预 祝 元 旦 快 乐"


def test_holiday_qingming_2026():
    # 2026 清明 4/5
    assert _holiday_subtitle(date(2026, 4, 5)) == "清 明 节 安 康"
    assert _holiday_subtitle(date(2026, 4, 4)) == "预 祝 清 明 假 期"


def test_holiday_qingming_2028_is_april_4():
    # 2028 清明 4/4，前一天是 4/3
    assert _holiday_subtitle(date(2028, 4, 4)) == "清 明 节 安 康"
    assert _holiday_subtitle(date(2028, 4, 3)) == "预 祝 清 明 假 期"


def test_holiday_christmas_no_eve_reminder():
    assert _holiday_subtitle(date(2026, 12, 25)) == "圣 诞 快 乐  ★"
    # 圣诞前一天不提醒
    assert _holiday_subtitle(date(2026, 12, 24)) is None


def test_holiday_halloween_day_only():
    assert _holiday_subtitle(date(2026, 10, 31)) == "万 圣 节 快 乐  🎃"
    assert _holiday_subtitle(date(2026, 10, 30)) is None


def test_holiday_none():
    # 普通工作日
    assert _holiday_subtitle(date(2026, 6, 3)) is None


def test_holiday_dragon_boat():
    # 2026 端午 6/19
    assert _holiday_subtitle(date(2026, 6, 19)) == "端 午 安 康"
    assert _holiday_subtitle(date(2026, 6, 18)) == "预 祝 端 午 安 康"


def test_holiday_mid_autumn_and_national_day_collision():
    # 2028-10-03 是中秋且在国庆假里，按表里的优先级（国庆先匹配）
    # 我们的实现是按法定节日列表顺序，先到先得；这里只断言"非 None 即可"
    res = _holiday_subtitle(date(2028, 10, 3))
    assert res is not None
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_surprise.py::test_holiday_chunjie_day_of -v`
Expected: FAIL ImportError

- [ ] **Step 3: 实现 `_holiday_subtitle`**

加到 `surprise.py`：

```python
# (节日, 当天文案, 前一天文案 or None)
# 顺序即优先级（前面的先命中）
_FIXED_HOLIDAYS = [
    ((1, 1),  "元 旦 快 乐",         "预 祝 元 旦 快 乐"),
    ((5, 1),  "劳 动 节 快 乐",       "预 祝 五 一 快 乐"),
    ((10, 1), "国 庆 快 乐  ✦",       "预 祝 国 庆 快 乐"),
    ((10, 31),"万 圣 节 快 乐  🎃",   None),
    ((12, 25),"圣 诞 快 乐  ★",       None),
]

_LUNAR_HOLIDAYS = [
    (SPRING_FESTIVAL, "春 节 快 乐  ✦",    "预 祝 春 节 快 乐"),
    (DRAGON_BOAT,     "端 午 安 康",        "预 祝 端 午 安 康"),
    (MID_AUTUMN,      "中 秋 快 乐",        "预 祝 中 秋 团 圆"),
    (QINGMING,        "清 明 节 安 康",      "预 祝 清 明 假 期"),
]


def _holiday_subtitle(today: date) -> str | None:
    """如果今天 / 明天是节日，返回对应文案；否则 None。"""
    tomorrow = today + timedelta(days=1)
    # 法定 + 半法定（公历固定）
    for (m, d), day_text, eve_text in _FIXED_HOLIDAYS:
        if today.month == m and today.day == d:
            return day_text
        if eve_text and tomorrow.month == m and tomorrow.day == d:
            return eve_text
    # 农历 + 清明
    for table, day_text, eve_text in _LUNAR_HOLIDAYS:
        target = table.get(today.year)
        if target == today:
            return day_text
        target_next = table.get(tomorrow.year)
        if target_next and target_next == tomorrow and eve_text:
            return eve_text
    return None
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest tests/test_surprise.py -v`
Expected: 全部通过（含上一 task 的 5 个）

- [ ] **Step 5: 提交**

```bash
git add surprise.py tests/test_surprise.py
git commit -m "feat(surprise): holiday detection (fixed + lunar + eve reminders)"
```

---

## Task 4: 天数节点（7 / 30·N / 365·N）

**Files:**
- Modify: `surprise.py`, `tests/test_surprise.py`

- [ ] **Step 1: 写失败的测试**

```python
from surprise import _days_subtitle


def test_days_first_week():
    assert _days_subtitle(7) == "陪 你 赚 了  1 周"


def test_days_one_month():
    assert _days_subtitle(30) == "陪 你 赚 了  1 个 月"


def test_days_three_months():
    assert _days_subtitle(90) == "陪 你 赚 了  3 个 月"


def test_days_one_year():
    assert _days_subtitle(365) == "陪 你 赚 了  1 年"


def test_days_two_years():
    assert _days_subtitle(730) == "陪 你 赚 了  2 年"


def test_days_year_priority_over_month():
    # 365 不是 30 的倍数（365 % 30 = 5），所以本身没有冲突；
    # 但 360 是 30*12 → 给 "12 个月"，不是年
    assert _days_subtitle(360) == "陪 你 赚 了  12 个 月"
    assert _days_subtitle(365) == "陪 你 赚 了  1 年"


def test_days_no_node():
    assert _days_subtitle(1) is None
    assert _days_subtitle(8) is None
    assert _days_subtitle(31) is None
    assert _days_subtitle(100) is None  # 100 不是 30 或 365 的倍数
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_surprise.py::test_days_first_week -v`
Expected: FAIL

- [ ] **Step 3: 实现**

```python
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
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest tests/test_surprise.py -v`

- [ ] **Step 5: 提交**

```bash
git add surprise.py tests/test_surprise.py
git commit -m "feat(surprise): day milestone detection"
```

---

## Task 5: 隐藏日期彩蛋（4/1、11/11）+ 视觉 overrides

**Files:**
- Modify: `surprise.py`, `tests/test_surprise.py`

- [ ] **Step 1: 写失败的测试**

```python
from surprise import _easter_subtitle, compute_visual_overrides


def test_easter_april_fools():
    assert _easter_subtitle(date(2026, 4, 1)) == "愚 人 节 快 乐  ☘"


def test_easter_double_eleven():
    assert _easter_subtitle(date(2026, 11, 11)) == "今 天 晚 饭  有 人 陪 么 ?"


def test_easter_other_day():
    assert _easter_subtitle(date(2026, 5, 5)) is None


def test_visual_overrides_april_fools():
    assert compute_visual_overrides(today=date(2026, 4, 1)) == {"flip_all": True}


def test_visual_overrides_double_eleven():
    assert compute_visual_overrides(today=date(2026, 11, 11)) == {"size_scale": 2.0}


def test_visual_overrides_normal():
    assert compute_visual_overrides(today=date(2026, 5, 5)) == {}
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_surprise.py -v`

- [ ] **Step 3: 实现**

```python
def _easter_subtitle(today: date) -> str | None:
    if today.month == 4 and today.day == 1:
        return "愚 人 节 快 乐  ☘"
    if today.month == 11 and today.day == 11:
        return "今 天 晚 饭  有 人 陪 么 ?"
    return None


def compute_visual_overrides(*, today: date) -> dict:
    """spec §7.2：4/1 全反着掉，11/11 直径加倍。"""
    if today.month == 4 and today.day == 1:
        return {"flip_all": True}
    if today.month == 11 and today.day == 11:
        return {"size_scale": 2.0}
    return {}
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest tests/test_surprise.py -v`

- [ ] **Step 5: 提交**

```bash
git add surprise.py tests/test_surprise.py
git commit -m "feat(surprise): hidden date easter eggs (4/1 flip, 11/11 size)"
```

---

## Task 6: 默认随机文案池（45 句）

**Files:**
- Modify: `surprise.py`, `tests/test_surprise.py`

- [ ] **Step 1: 写失败的测试**

```python
from surprise import _default_caption, DEFAULT_CAPTIONS


def test_default_pool_size():
    # 14 + 15 + 15 - 1（spec §10.1 注释里说"周五倒计时"在周末过滤，但默认池本身有 44 句）
    assert len(DEFAULT_CAPTIONS) == 44


def test_default_caption_deterministic_with_seed():
    rng = random.Random(42)
    a = _default_caption(today=date(2026, 5, 5), rng=rng)
    rng2 = random.Random(42)
    b = _default_caption(today=date(2026, 5, 5), rng=rng2)
    assert a == b


def test_default_caption_friday_countdown_filled():
    rng = random.Random(0)
    # 反复抽，看 "周 五 倒 计 时" 出现时被填进了具体天数
    seen_friday_template = False
    for seed in range(200):
        c = _default_caption(today=date(2026, 5, 6), rng=random.Random(seed))  # 周三
        if "周 五 倒 计 时" in c:
            assert "X" not in c  # X 已经被替换
            assert "2 天" in c   # 周三离周五 2 天
            seen_friday_template = True
            break
    assert seen_friday_template
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_surprise.py -v`

- [ ] **Step 3: 实现**

```python
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
    pool = DEFAULT_CAPTIONS
    # spec §10.1 注释：周末过滤 "周五倒计时"
    if today.weekday() >= 5:
        pool = [c for c in pool if "周 五 倒 计 时" not in c]
    pick = rng.choice(pool)
    if "周 五 倒 计 时  X" in pick:
        # 周一(0)->4，周二(1)->3，..., 周四(3)->1，周五(4)->0（不会被抽到，因为非工作日已过滤过；
        # 但周五本身仍可能被抽到，那就显示 0 天 → 替换成"今天"）
        delta = (4 - today.weekday()) % 7
        if delta == 0:
            return "今 天 就 是 周 五"
        pick = pick.replace("X", f"{delta} 天")
    return pick
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest tests/test_surprise.py -v`

如果 `test_default_pool_size` 报 45 而非 44，是因为 14+15+15=44，把测试或 spec 对齐到 44。已对齐到 44。

- [ ] **Step 5: 提交**

```bash
git add surprise.py tests/test_surprise.py
git commit -m "feat(surprise): default caption pool (44 lines, friday countdown template)"
```

---

## Task 7: `compute_subtitle` 优先级引擎组装

**Files:**
- Modify: `surprise.py`, `tests/test_surprise.py`

- [ ] **Step 1: 写失败的测试**

```python
from surprise import compute_subtitle


def test_subtitle_priority_cumulative_beats_holiday():
    # 假设某天既是国庆又命中累计节点
    # I=200，第 50 天命中 ¥10000；构造一个 today 同时是国庆（10/1）
    # （技术上这是构造的边界：installed_at 让 days_since_install=50 在 10/1）
    out = compute_subtitle(
        days_since_install=50,
        today=date(2026, 10, 1),
        daily_income=200,
        is_last_trigger=True,
    )
    assert "累 计 突 破" in out
    assert "10,000" in out


def test_subtitle_holiday_beats_days():
    # 国庆当天 + 第 30 天：节日赢
    out = compute_subtitle(
        days_since_install=30,
        today=date(2026, 10, 1),
        daily_income=200,
        is_last_trigger=True,
    )
    assert "国 庆" in out


def test_subtitle_days_beats_easter():
    # 11/11 + 第 30 天：天数赢
    out = compute_subtitle(
        days_since_install=30,
        today=date(2026, 11, 11),
        daily_income=200,
        is_last_trigger=True,
    )
    assert "1 个 月" in out


def test_subtitle_easter_when_no_milestone():
    # 4/1 + 平凡天数：愚人节
    out = compute_subtitle(
        days_since_install=33,
        today=date(2026, 4, 1),
        daily_income=200,
        is_last_trigger=True,
    )
    assert "愚 人 节" in out


def test_subtitle_default_pool_fallback():
    # 平凡日子 → 从默认池抽
    out = compute_subtitle(
        days_since_install=11,
        today=date(2026, 5, 5),
        daily_income=200,
        is_last_trigger=True,
        rng=random.Random(0),
    )
    assert out in [c for c in __import__("surprise").DEFAULT_CAPTIONS if "周 五 倒 计 时" not in c] \
        or "周 五 倒 计 时" in out  # 取决于具体抽到什么


def test_subtitle_cumulative_only_on_last_trigger():
    # is_last_trigger=False → 累计节点不命中，回退到下一级
    out = compute_subtitle(
        days_since_install=50,
        today=date(2026, 6, 3),  # 平凡日
        daily_income=200,
        is_last_trigger=False,
        rng=random.Random(0),
    )
    assert "累 计 突 破" not in out


def test_subtitle_amount_thousand_separator():
    out = compute_subtitle(
        days_since_install=50,
        today=date(2026, 6, 3),
        daily_income=200,
        is_last_trigger=True,
    )
    assert "¥10,000" in out
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_surprise.py -v`

- [ ] **Step 3: 实现**

替换 `surprise.py` 里 `compute_subtitle` 的 `raise NotImplementedError`：

```python
def compute_subtitle(*, days_since_install: int, today: date,
                     daily_income: int, is_last_trigger: bool,
                     rng: random.Random | None = None) -> str:
    """spec §3 优先级引擎：累计 → 节日 → 天数 → 隐藏 → 默认池。"""
    rng = rng or random.Random()
    # 优先级 1：累计金额节点（仅最后一次触发）
    if is_last_trigger:
        node = _cumulative_node_amount(days=days_since_install, income=daily_income)
        if node is not None:
            return f"累 计 突 破   ¥{node:,}"
    # 优先级 2：节日
    h = _holiday_subtitle(today)
    if h is not None:
        return h
    # 优先级 3：天数
    d = _days_subtitle(days_since_install)
    if d is not None:
        return d
    # 优先级 4：隐藏日期彩蛋
    e = _easter_subtitle(today)
    if e is not None:
        return e
    # 优先级 5：默认池
    return _default_caption(today=today, rng=rng)
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest tests/test_surprise.py -v`

- [ ] **Step 5: 提交**

```bash
git add surprise.py tests/test_surprise.py
git commit -m "feat(surprise): compose 5-level subtitle priority engine"
```

---

## Task 8: 幸运币 / 金币模式抽签

**Files:**
- Modify: `surprise.py`, `tests/test_surprise.py`

- [ ] **Step 1: 写失败的测试**

```python
from surprise import pick_lucky, pick_coin_mode


def test_pick_lucky_about_3pct():
    rng = random.Random(0)
    hits = sum(pick_lucky(rng=rng) for _ in range(10000))
    # 3% ± 1.5%（10000 次足够紧）
    assert 150 <= hits <= 450, f"got {hits}, expected ~300"


def test_pick_coin_mode_80_20():
    rng = random.Random(0)
    n = 6
    mixed = 0
    single = 0
    for _ in range(10000):
        m = pick_coin_mode(n_styles=n, rng=rng)
        if m is None:
            mixed += 1
        else:
            assert 0 <= m < n
            single += 1
    # 期望 8000 single / 2000 mixed，给 ±400 浮动
    assert 7600 <= single <= 8400
    assert 1600 <= mixed <= 2400


def test_pick_coin_mode_zero_styles():
    # n_styles=0：只能返回 None（不可能选下标）
    assert pick_coin_mode(n_styles=0, rng=random.Random(0)) is None
```

- [ ] **Step 2: 跑测试确认失败**

Run: `python -m pytest tests/test_surprise.py -v`

- [ ] **Step 3: 实现**

```python
def pick_lucky(*, rng: random.Random | None = None) -> bool:
    """spec §8：3% 幸运币概率。"""
    rng = rng or random.Random()
    return rng.random() < 0.03


def pick_coin_mode(*, n_styles: int, rng: random.Random | None = None) -> int | None:
    """spec §9：80% 单一币种（返回 style_idx），20% 混合（返回 None）。"""
    rng = rng or random.Random()
    if n_styles <= 0:
        return None
    if rng.random() < 0.20:
        return None
    return rng.randrange(n_styles)
```

- [ ] **Step 4: 跑测试确认通过**

Run: `python -m pytest tests/test_surprise.py -v`

- [ ] **Step 5: 提交**

```bash
git add surprise.py tests/test_surprise.py
git commit -m "feat(surprise): lucky coin (3%) and coin mode (80/20) random pickers"
```

---

## Task 9: rain_window 接收 subtitle / visual_overrides / lucky / coin_mode

**Files:**
- Modify: `rain_window.py`

不写新测试（这层是 Qt UI 集成，靠 Task 14 的端到端冒烟测试覆盖）。

- [ ] **Step 1: 添加 4 个 setter + 状态字段**

打开 `rain_window.py`，找到 `set_intensity` 那段（约 168–172 行），紧接着加：

```python
    def set_subtitle(self, text: str) -> None:
        """覆盖中央 ¥X 大字下方那行小字。在 start() 之前调用。"""
        self._subtitle_text = text

    def set_visual_overrides(self, overrides: dict) -> None:
        """spec §7.2：{} | {"flip_all": True} | {"size_scale": 2.0}"""
        self._flip_all = bool(overrides.get("flip_all", False))
        self._size_scale = float(overrides.get("size_scale", 1.0))

    def set_lucky_coin(self, enabled: bool) -> None:
        """spec §8：本场雨是否触发幸运币。"""
        self._lucky_enabled = enabled

    def set_coin_mode(self, mode: int | None) -> None:
        """spec §9：None=混合（每枚独立抽），int=全场固定 style_idx。"""
        self._coin_mode = mode
```

- [ ] **Step 2: 在 `__init__` 末尾加默认值**

找到 `self._target_amount = 300` 那段，紧接着加：

```python
        self._subtitle_text: str | None = None    # None = 用 _label_text 兜底（向后兼容）
        self._flip_all = False
        self._size_scale = 1.0
        self._lucky_enabled = False
        self._coin_mode: int | None = None        # None = 混合（每枚独立）
        self._lucky_spawned = False               # 幸运币只生成一枚
```

- [ ] **Step 3: 跑现有测试确认 import 没坏**

Run: `python -m pytest tests/ -v`
Expected: 全部通过（surprise 测试 + 原 16 个）

- [ ] **Step 4: 提交**

```bash
git add rain_window.py
git commit -m "feat(rain): add setters for subtitle/visual_overrides/lucky/coin_mode"
```

---

## Task 10: rain_window 渲染副标 + 上方幸运币提示

**Files:**
- Modify: `rain_window.py`

- [ ] **Step 1: 修改 `_draw_amount` 用 `_subtitle_text` 兜底成 `_label_text`**

找到 `_draw_amount` 里 `self._label_text` 出现的位置（约 382 行），改为：

```python
        # 下方副标：subtitle 优先，没有再用 label（向后兼容）
        text_main = self._subtitle_text if self._subtitle_text else self._label_text
        lw = fm2.horizontalAdvance(text_main)
        lx = (w - lw) / 2
        ly = base_y + label_px * 2.2

        p.save()
        p.setPen(AMOUNT_SHADOW_COLOR)
        p.drawText(QPointF(lx + 2, ly + 2), text_main)
        p.restore()
        p.setPen(LABEL_COLOR)
        p.drawText(QPointF(lx, ly), text_main)
```

注意：原来 `_label_text` 直接用，现在用 `text_main`。把那两处的 `self._label_text` 也改成 `text_main`。

- [ ] **Step 2: 加 lucky 提示（数字大字上方）**

在 `_draw_amount` **末尾**加：

```python
        # spec §8：幸运币命中时，¥X 上方多一行小字
        if self._lucky_enabled:
            tip = "✦   接  住  一  枚  幸  运  币   ✦"
            tip_font = QFont(LABEL_FONT_FAMILY)
            tip_font.setPixelSize(label_px)
            tip_font.setWeight(QFont.Medium)
            tip_font.setLetterSpacing(QFont.PercentageSpacing, 200)
            p.setFont(tip_font)
            fm3 = p.fontMetrics()
            tw = fm3.horizontalAdvance(tip)
            tx = (w - tw) / 2
            ty = base_y - num_px * 0.85   # 在数字上方
            p.save()
            p.setPen(AMOUNT_SHADOW_COLOR)
            p.drawText(QPointF(tx + 2, ty + 2), tip)
            p.restore()
            p.setPen(LABEL_COLOR)
            p.drawText(QPointF(tx, ty), tip)
```

- [ ] **Step 3: 本地肉眼验证**

Run: `python coin_rain.py --rain --test`
Expected: 中央数字下方文案能正常显示（subtitle 还没接进来，会显示 "今 日 到 账"）。

- [ ] **Step 4: 提交**

```bash
git add rain_window.py
git commit -m "feat(rain): render subtitle + lucky coin tip above amount"
```

---

## Task 11: rain_window 应用 visual overrides + coin_mode 到 _make_coin

**Files:**
- Modify: `rain_window.py`

- [ ] **Step 1: 改 `_make_coin` 让 size_scale / flip_all / coin_mode 生效**

找到 `_make_coin`（约 216–230 行），整段替换为：

```python
    def _make_coin(self) -> Coin:
        # spec §7.2: 11/11 直径加倍
        d = random.uniform(COIN_DIAMETER_MIN, COIN_DIAMETER_MAX) * self._size_scale
        vy_lo, vy_hi = self._params["vy_init"]
        spawn_y = random.uniform(-d * 0.4, d * 0.6)
        # spec §9：固定 style_idx 还是每枚独立抽
        if self._pixmaps:
            if self._coin_mode is not None:
                style = self._coin_mode % len(self._pixmaps)
            else:
                style = random.randrange(len(self._pixmaps))
        else:
            style = 0
        # spec §7.2: 4/1 整场翻面 —— 起始 angle 加 π，让 cos 缩放从负向开始
        base_angle = random.uniform(0, math.tau)
        if self._flip_all:
            base_angle += math.pi
        return Coin(
            x=random.uniform(-d * 0.2, self._screen_w + d * 0.2),
            y=spawn_y,
            vx=random.uniform(-VX_INIT_ABS_MAX, VX_INIT_ABS_MAX),
            vy=random.uniform(vy_lo, vy_hi),
            diameter=d,
            angle=base_angle,
            angular_v=random.uniform(ROT_SPEED_MIN, ROT_SPEED_MAX) * random.choice((-1, 1)),
            style_idx=style,
        )
```

- [ ] **Step 2: 跑测试确认没坏旧逻辑**

Run: `python -m pytest tests/ -v`

- [ ] **Step 3: 本地肉眼验证 4/1 视觉**

临时修改 `coin_rain.py` 让它构造一个 4/1 触发，或在 Python 命令行：

```bash
python -c "
from PySide6.QtWidgets import QApplication
from rain_window import CoinRainWindow
import sys
app = QApplication(sys.argv)
w = CoinRainWindow()
w.set_intensity('medium')
w.set_visual_overrides({'flip_all': True})
w.finished.connect(app.quit)
w.start()
app.exec()
"
```

Expected: 金币明显在 cos 翻转的"反面相位"开始（背面朝外比例更高），整体观感是反着掉。

- [ ] **Step 4: 提交**

```bash
git add rain_window.py
git commit -m "feat(rain): apply visual overrides (flip/size) and coin_mode to spawn"
```

---

## Task 12: rain_window 幸运币生成（独立 hero coin）

**Files:**
- Modify: `rain_window.py`

- [ ] **Step 1: 在 `_start_coins` 开头加幸运币生成**

找到 `_start_coins`（约 197–200 行），改为：

```python
    def _start_coins(self) -> None:
        self._play_coin()
        # spec §8：幸运币（如果命中）—— 比最大币更大、慢、屏幕中上方掉下
        if self._lucky_enabled and self._pixmaps and not self._lucky_spawned:
            self._lucky_spawned = True
            d = COIN_DIAMETER_MAX * 1.8 * self._size_scale
            vy_lo, vy_hi = self._params["vy_init"]
            base_angle = random.uniform(0, math.tau)
            if self._flip_all:
                base_angle += math.pi
            self.coins.append(Coin(
                x=self._screen_w / 2 + random.uniform(-40, 40),
                y=-120,
                vx=random.uniform(-15, 15),
                vy=random.uniform(vy_lo, vy_hi) * 0.7,   # 慢一点多停留
                diameter=d,
                angle=base_angle,
                angular_v=random.uniform(ROT_SPEED_MIN, ROT_SPEED_MAX) * 0.6
                          * random.choice((-1, 1)),
                style_idx=random.randrange(len(self._pixmaps)),
            ))
        self._spawn_batch()
```

- [ ] **Step 2: 本地肉眼验证幸运币**

```bash
python -c "
from PySide6.QtWidgets import QApplication
from rain_window import CoinRainWindow
import sys
app = QApplication(sys.argv)
w = CoinRainWindow()
w.set_intensity('medium')
w.set_lucky_coin(True)
w.set_subtitle('再 来 一 波')
w.finished.connect(app.quit)
w.start()
app.exec()
"
```

Expected: 屏幕中上方先出一枚明显大的金币慢慢落下，¥X 数字上方出现 "✦ 接住一枚幸运币 ✦"，下方是 "再 来 一 波"。

- [ ] **Step 3: 提交**

```bash
git add rain_window.py
git commit -m "feat(rain): spawn oversized lucky coin from top-center"
```

---

## Task 13: coin_rain.py 接入 surprise 引擎

**Files:**
- Modify: `coin_rain.py`

- [ ] **Step 1: 改 `_run_rain` 计算 subtitle/visual/lucky/mode 并传给窗口**

整段替换 `_run_rain`：

```python
def _run_rain(args: argparse.Namespace) -> int:
    from datetime import date, datetime
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
    # 6 款 PNG —— 用 _load_coin_pixmaps 真实数量更稳，不会硬编码
    n_styles = len(_load_coin_pixmaps())
    coin_mode = surprise.pick_coin_mode(n_styles=n_styles)

    w = CoinRainWindow()
    w.set_amount(amount, "今 日 到 账" if is_last else "当 前 已 到 账")
    w.set_intensity(intensity)
    w.set_subtitle(subtitle)
    w.set_visual_overrides(visual)
    w.set_lucky_coin(lucky)
    w.set_coin_mode(coin_mode)
    w.finished.connect(app.quit)
    w.start()
    return app.exec()


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
    diff = (today - d0).days + 1
    return max(diff, 1)
```

- [ ] **Step 2: 跑现有测试确认没坏**

Run: `python -m pytest tests/ -v`

- [ ] **Step 3: 本地端到端冒烟**

Run: `python coin_rain.py --rain --test`
Expected:
- 中央 ¥X count-up 正常
- 数字下方文案是 surprise 算出来的（今天日期下默认池或某个节日，不再固定 "今 日 到 账"）
- 偶尔（3%）能触发幸运币（多跑几次）

- [ ] **Step 4: 提交**

```bash
git add coin_rain.py
git commit -m "feat(rain): wire surprise engine into rain entry point"
```

---

## Task 14: ManageWindow "先试一下" 走同一条路径（保证 UI 触发也吃到惊喜层）

**Files:**
- Modify: `config_window.py`（仅当当前 "先试" 路径绕过了 surprise）

- [ ] **Step 1: 看当前实现**

Run: `python -c "import config_window; import inspect; print(inspect.getsource(config_window.ManageWindow._launch_test_rain))" 2>&1 | head -60`

或直接：

```bash
grep -n "_launch_test_rain\|set_amount\|set_intensity" config_window.py
```

如果 `_launch_test_rain` 直接调用 `CoinRainWindow().set_amount(...).set_intensity(...).start()` —— 它走的是和 `_run_rain` 一样的 setter 逻辑，但**没经过 surprise**。

- [ ] **Step 2: 重构 `_launch_test_rain`**

把"算 amount/intensity → 创建窗口 → setter → start"那段抽出来，让它和 `_run_rain` 共享一个 helper。最小改动：

打开 `config_window.py`，找到 `_launch_test_rain`，在创建 `CoinRainWindow` 后、`start()` 前加：

```python
        from datetime import date
        import surprise
        from rain_window import _load_coin_pixmaps

        cfg_for_test = self._read_form_into_config()  # 用当前表单的草稿值，而非已存的
        income = cfg_for_test.income
        installed_at = cfg_for_test.installed_at or ""

        today = date.today()
        try:
            from datetime import datetime
            d0 = datetime.fromisoformat(installed_at).date() if installed_at else today
            days = max((today - d0).days + 1, 1)
        except ValueError:
            days = 1

        w.set_subtitle(surprise.compute_subtitle(
            days_since_install=days,
            today=today,
            daily_income=income,
            is_last_trigger=True,
        ))
        w.set_visual_overrides(surprise.compute_visual_overrides(today=today))
        w.set_lucky_coin(surprise.pick_lucky())
        w.set_coin_mode(surprise.pick_coin_mode(n_styles=len(_load_coin_pixmaps())))
```

如果 `_read_form_into_config` 名字不对（这是猜的），grep 找到当前 "先试" 是怎么拿配置值的，沿用那个：

```bash
grep -n "income\|intensity" config_window.py | grep -i "test\|launch"
```

- [ ] **Step 3: 本地点 "先试" 验证**

Run: `python coin_rain.py`，进入 ManageWindow，点 "先试一下"

Expected: 副标行不再是固定 "今 日 到 账"，而是默认池里的某句（或日历节日命中）。

- [ ] **Step 4: 提交**

```bash
git add config_window.py
git commit -m "feat(config-ui): pipe surprise engine through 先试 button"
```

---

## Task 15: 端到端日期模拟测试

**Files:**
- Modify: `tests/test_surprise.py`

- [ ] **Step 1: 加 4 个集成测试**

```python
def test_e2e_chunjie_eve_with_5y_milestone():
    # 2026-02-16 春节前一天，假设 days=1825（5年）
    # 累计 + 节日同存：累计赢
    out = compute_subtitle(
        days_since_install=1825,
        today=date(2026, 2, 16),
        daily_income=300,
        is_last_trigger=True,
    )
    assert "累 计 突 破" in out


def test_e2e_chunjie_eve_alone():
    # 第 100 天 + 春节前一天：累计不一定命中（看 income）；节日赢
    out = compute_subtitle(
        days_since_install=100,
        today=date(2026, 2, 16),
        daily_income=200,  # 100*200=20000，命中第 3 次累计节点
        is_last_trigger=True,
    )
    # 累计命中（20000），赢节日
    assert "累 计 突 破" in out


def test_e2e_april_first_visual_and_subtitle():
    today = date(2026, 4, 1)
    sub = compute_subtitle(
        days_since_install=11,
        today=today,
        daily_income=200,
        is_last_trigger=True,
    )
    assert "愚 人 节" in sub
    assert compute_visual_overrides(today=today) == {"flip_all": True}


def test_e2e_double_eleven_visual_and_subtitle():
    today = date(2026, 11, 11)
    sub = compute_subtitle(
        days_since_install=11,
        today=today,
        daily_income=200,
        is_last_trigger=True,
    )
    assert "晚 饭" in sub
    assert compute_visual_overrides(today=today) == {"size_scale": 2.0}
```

- [ ] **Step 2: 跑全部测试**

Run: `python -m pytest tests/ -v`
Expected: 全部通过

- [ ] **Step 3: 提交**

```bash
git add tests/test_surprise.py
git commit -m "test(surprise): end-to-end date scenarios"
```

---

## Task 16: 重打包 exe + 冒烟测试

**Files:**
- Modify: `coin_rain.spec`

- [ ] **Step 1: 确认 surprise.py 不需要在 spec 里显式列**

PyInstaller 默认会跟着 `coin_rain.py` 的 import 链把 `surprise.py` 打进去（同目录、被 import），不需要改 spec。验证：

```bash
grep -n "surprise" coin_rain.spec
```

如果输出空就对了——啥都不用改。

- [ ] **Step 2: 跑 build.bat**

Run: `build.bat`（双击或在 cmd 里）
Expected: `dist\coin_rain.exe` 生成成功，无 PyInstaller error。

- [ ] **Step 3: exe 冒烟**

Run: `dist\coin_rain.exe --rain --test`
Expected:
- 副标行变化（默认池 / 节日 / 天数 / 累计）
- 偶尔幸运币
- 4/1 当天测试可以临时改本机日期或在测试机上手动改 today（spec 没要求，跳过手测）

- [ ] **Step 4: 提交**

```bash
git status   # 看 dist/ 是否被 .gitignore；如果是就只提 spec 改动（如果有）
git add coin_rain.spec   # 仅当 spec 有改动
git commit -m "build: rebuild exe with surprise layer (no spec change required)" --allow-empty
```

如果 spec 完全没动，跳过 commit。

---

## Self-review checklist (写完后跑过一遍)

- [x] **Spec 覆盖**：
  - §3 优先级引擎 → Task 7
  - §4 累计金额 → Task 2
  - §5 节日表（含农历）→ Task 3
  - §6 天数节点 → Task 4
  - §7 隐藏日期彩蛋（文案+视觉）→ Task 5 + Task 11
  - §8 幸运币 → Task 8 + Task 9 + Task 10 + Task 12
  - §9 金币品种 80/20 → Task 8 + Task 11
  - §10 默认文案池 → Task 6
  - §11 数据流 → Task 13 + Task 14
  - §12 测试 → 散布在 Task 2/3/4/5/6/7/8/15
  - §13 不做 → 自动遵守（不持久化、不自定义生日）
  - §13.1 v3.1 待办 → 不做（spec 明确）

- [x] **占位符**：无 TBD/TODO；所有"if 名字不对" fallback 都给了 grep 命令找真实名字

- [x] **类型一致性**：
  - `compute_subtitle` 签名在 Task 1 / Task 7 / Task 13 / Task 14 一致
  - `compute_visual_overrides(today=...)` 签名一致
  - `pick_coin_mode(n_styles=...)` 签名一致
  - `set_visual_overrides({"flip_all": True})` 在 Task 5/9/11 一致

- [x] **决定级**：
  - Task 14 里假设 "先试" 函数名是 `_launch_test_rain` / `_read_form_into_config`，给了 grep 兜底命令
  - Task 16 里假设 `dist/` 在 .gitignore 里（项目实际如此）

---

## 时间估算

- Task 1–8（surprise.py + 测试）：~3 小时
- Task 9–12（rain_window 改造）：~2 小时
- Task 13–14（接入入口 + 先试）：~1 小时
- Task 15–16（集成测试 + 重打包冒烟）：~30 分钟
- 总：~6.5 小时（半个迭代日）
