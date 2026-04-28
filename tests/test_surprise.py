"""惊喜层规则的单元测试。"""
import random
from datetime import date

from surprise import (
    _cumulative_node_amount,
    _holiday_subtitle,
    _days_subtitle,
    _easter_subtitle,
    compute_visual_overrides,
)


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


def test_holiday_chunjie_day_of():
    assert _holiday_subtitle(date(2026, 2, 17)) == "春 节 快 乐  ✦"


def test_holiday_chunjie_eve():
    assert _holiday_subtitle(date(2026, 2, 16)) == "预 祝 春 节 快 乐"


def test_holiday_yuandan_day_of():
    assert _holiday_subtitle(date(2027, 1, 1)) == "元 旦 快 乐"


def test_holiday_yuandan_eve():
    # 12/31 是上一年的元旦前一天
    assert _holiday_subtitle(date(2026, 12, 31)) == "预 祝 元 旦 快 乐"


def test_holiday_qingming_2026():
    assert _holiday_subtitle(date(2026, 4, 5)) == "清 明 节 安 康"
    assert _holiday_subtitle(date(2026, 4, 4)) == "预 祝 清 明 假 期"


def test_holiday_qingming_2028_is_april_4():
    assert _holiday_subtitle(date(2028, 4, 4)) == "清 明 节 安 康"
    assert _holiday_subtitle(date(2028, 4, 3)) == "预 祝 清 明 假 期"


def test_holiday_christmas_no_eve_reminder():
    assert _holiday_subtitle(date(2026, 12, 25)) == "圣 诞 快 乐  ★"
    assert _holiday_subtitle(date(2026, 12, 24)) is None


def test_holiday_halloween_day_only():
    assert _holiday_subtitle(date(2026, 10, 31)) == "万 圣 节 快 乐  🎃"
    assert _holiday_subtitle(date(2026, 10, 30)) is None


def test_holiday_none():
    assert _holiday_subtitle(date(2026, 6, 3)) is None


def test_holiday_dragon_boat():
    assert _holiday_subtitle(date(2026, 6, 19)) == "端 午 安 康"
    assert _holiday_subtitle(date(2026, 6, 18)) == "预 祝 端 午 安 康"


def test_holiday_mid_autumn_or_national_overlap():
    # 2028-10-03 既在国庆假里，又是当年的中秋
    res = _holiday_subtitle(date(2028, 10, 3))
    assert res is not None


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
    assert _days_subtitle(360) == "陪 你 赚 了  12 个 月"
    assert _days_subtitle(365) == "陪 你 赚 了  1 年"


def test_days_no_node():
    assert _days_subtitle(1) is None
    assert _days_subtitle(8) is None
    assert _days_subtitle(31) is None
    assert _days_subtitle(100) is None


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
