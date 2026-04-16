"""对纯逻辑函数的单元测试（不依赖 Qt / subprocess）。"""
from rain_window import _compute_amount
from config import Config


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


# ---- Config roundtrip tests ----

def test_config_roundtrip_single(tmp_path, monkeypatch):
    """单次模式配置保存→读回，字段完全一致。"""
    target = tmp_path / "config.json"
    monkeypatch.setattr("config.config_path", lambda: target)

    c = Config(
        version=1, income=300, intensity="medium", mode="single",
        time="17:00", first_time=None, last_time=None, count=None,
        coin_style="kaiyuan", mixed_coins=False,
        installed_at="2026-04-16T10:00:00",
    )
    c.save()
    loaded = Config.load()
    assert loaded == c


def test_config_roundtrip_multi(tmp_path, monkeypatch):
    """多次模式配置保存→读回，字段完全一致。"""
    target = tmp_path / "config.json"
    monkeypatch.setattr("config.config_path", lambda: target)

    c = Config(
        version=1, income=600, intensity="heavy", mode="multi",
        time=None, first_time="09:00", last_time="17:00", count=3,
        coin_style="yongle", mixed_coins=True,
        installed_at="2026-04-16T10:00:00",
    )
    c.save()
    loaded = Config.load()
    assert loaded == c


def test_config_load_missing_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr("config.config_path", lambda: tmp_path / "missing.json")
    assert Config.load() is None


def test_config_load_corrupted_returns_none(tmp_path, monkeypatch):
    target = tmp_path / "bad.json"
    target.write_text("{not json")
    monkeypatch.setattr("config.config_path", lambda: target)
    assert Config.load() is None


def test_config_exists(tmp_path, monkeypatch):
    target = tmp_path / "c.json"
    monkeypatch.setattr("config.config_path", lambda: target)
    assert Config.exists() is False
    target.write_text('{"version":1,"income":100,"intensity":"light","mode":"single","time":"17:00","first_time":null,"last_time":null,"count":null,"coin_style":"kaiyuan","mixed_coins":false,"installed_at":"2026-04-16T10:00:00"}')
    assert Config.exists() is True
