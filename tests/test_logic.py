"""对纯逻辑函数的单元测试（不依赖 Qt / subprocess）。"""
from rain_window import _compute_amount


def test_compute_amount_single_mode():
    """单次模式等价于 nth=1, total=1，直接 = income。"""
    assert _compute_amount(income=300, nth=1, total=1) == 300


def test_compute_amount_multi_first():
    """多次模式第 1 次 = income / total。"""
    assert _compute_amount(income=300, nth=1, total=3) == 100


def test_compute_amount_multi_last():
    """多次模式最后一次 = income（累计闭合）。"""
    assert _compute_amount(income=300, nth=3, total=3) == 300


def test_compute_amount_rounds_to_nearest_int():
    """金额取整到整数元。"""
    assert _compute_amount(income=100, nth=1, total=3) == 33
    assert _compute_amount(income=100, nth=2, total=3) == 67
    assert _compute_amount(income=100, nth=3, total=3) == 100


def test_compute_amount_last_always_equals_income():
    """无论 income/total 如何，nth==total 时必须 == income。"""
    for income in [1, 7, 100, 9999]:
        for total in [1, 2, 5, 10]:
            assert _compute_amount(income=income, nth=total, total=total) == income
