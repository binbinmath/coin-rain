"""惊喜层规则的单元测试。"""
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
