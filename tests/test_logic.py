"""对纯逻辑函数的单元测试（不依赖 Qt / subprocess）。"""
from rain_window import _compute_amount
from config import Config, CONFIG_VERSION
from config_window import make_quote, time_bucket


# ---- _compute_amount ----

def test_compute_amount_single_mode():
    """单次模式等价于 nth=1, total=1，直接 = income。"""
    assert _compute_amount(income=300, nth=1, total=1) == 300


def test_compute_amount_multi_first():
    assert _compute_amount(income=300, nth=1, total=3) == 100


def test_compute_amount_multi_last():
    """nth==total 必须等于 income（累计闭合）。"""
    assert _compute_amount(income=300, nth=3, total=3) == 300


def test_compute_amount_rounds_to_nearest_int():
    assert _compute_amount(income=100, nth=1, total=3) == 33
    assert _compute_amount(income=100, nth=2, total=3) == 67
    assert _compute_amount(income=100, nth=3, total=3) == 100


def test_compute_amount_last_always_equals_income():
    for income in [1, 7, 100, 9999]:
        for total in [1, 2, 5, 10]:
            assert _compute_amount(income=income, nth=total, total=total) == income


# ---- Config roundtrip ----

def test_config_roundtrip_single(tmp_path, monkeypatch):
    target = tmp_path / "config.json"
    monkeypatch.setattr("config.config_path", lambda: target)

    c = Config(
        version=CONFIG_VERSION, income=300, intensity="medium", mode="single",
        time="17:00", times=[],
        installed_at="2026-04-28T10:00:00",
    )
    c.save()
    loaded = Config.load()
    assert loaded == c


def test_config_roundtrip_multi(tmp_path, monkeypatch):
    target = tmp_path / "config.json"
    monkeypatch.setattr("config.config_path", lambda: target)

    c = Config(
        version=CONFIG_VERSION, income=600, intensity="storm", mode="multi",
        time=None, times=["08:00", "13:00", "21:00"],
        installed_at="2026-04-28T10:00:00",
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
    target.write_text(
        '{"version":2,"income":100,"intensity":"light","mode":"single",'
        '"time":"17:00","times":[],"installed_at":"2026-04-28T10:00:00"}',
        encoding="utf-8",
    )
    assert Config.exists() is True


def test_config_v1_migrates_to_v2(tmp_path, monkeypatch):
    """V1 老 config（first/last/count）可以自动升级到 V2 的 times 列表。"""
    target = tmp_path / "config.json"
    monkeypatch.setattr("config.config_path", lambda: target)
    target.write_text(
        '{"version":1,"income":300,"intensity":"medium","mode":"multi",'
        '"time":null,"first_time":"09:00","last_time":"17:00","count":3,'
        '"coin_style":"kaiyuan","mixed_coins":false,'
        '"installed_at":"2026-04-16T10:00:00"}',
        encoding="utf-8",
    )
    loaded = Config.load()
    assert loaded is not None
    assert loaded.version == 2
    assert loaded.mode == "multi"
    assert loaded.times == ["09:00", "13:00", "17:00"]


# ---- 动态文案 makeQuote ----

def test_time_bucket_basic():
    assert time_bucket("08:00")[0] == "清 晨"
    assert time_bucket("17:00")[0] == "傍 晚"
    assert time_bucket("23:00")[0] == "深 夜"
    assert time_bucket("03:00")[0] == "夜 里"


def test_make_quote_single():
    cn, en = make_quote(intensity="medium", mode="single", time="17:00", times=[])
    assert "傍 晚" in cn
    assert "细 雨" in cn
    assert "sunset" in en


def test_make_quote_storm_single():
    cn, _ = make_quote(intensity="storm", mode="single", time="13:00", times=[])
    assert "正 午" in cn
    assert "骤 雨" in cn


def test_make_quote_multi_three():
    cn, en = make_quote(
        intensity="heavy", mode="multi", time=None,
        times=["08:00", "13:00", "21:00"],
    )
    assert "数 阵" in cn
    assert "大 雨" in cn
    assert "3" in en


def test_make_quote_multi_empty():
    cn, _ = make_quote(intensity="medium", mode="multi", time=None, times=[])
    assert "待 添 加" in cn
