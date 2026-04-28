"""测试 Konami code 序列匹配的纯逻辑函数。"""
from PySide6.QtCore import Qt

from config_window import _konami_step, KONAMI_CODE


def _full_sequence() -> list:
    return list(KONAMI_CODE)


def test_full_sequence_triggers():
    buf: list = []
    triggered = False
    for k in _full_sequence():
        buf, triggered = _konami_step(buf, k)
    assert triggered is True
    assert buf == []


def test_partial_sequence_no_trigger():
    buf: list = []
    triggered = False
    for k in _full_sequence()[:5]:
        buf, triggered = _konami_step(buf, k)
    assert triggered is False
    assert len(buf) == 5


def test_wrong_key_resets_buffer():
    buf: list = []
    # 输入 ↑ ↑ ↓ ↓，然后按 X（不是 ←，是无关键）
    for k in [Qt.Key_Up, Qt.Key_Up, Qt.Key_Down, Qt.Key_Down]:
        buf, _ = _konami_step(buf, k)
    assert len(buf) == 4
    buf, triggered = _konami_step(buf, Qt.Key_X)
    assert buf == []
    assert triggered is False


def test_wrong_key_that_is_seq_start_restarts():
    buf: list = []
    # 输入 ↑ ↑ ↓ ↓，期待 ←；却按 ↑ —— 应该重启从 ↑ 开始
    for k in [Qt.Key_Up, Qt.Key_Up, Qt.Key_Down, Qt.Key_Down]:
        buf, _ = _konami_step(buf, k)
    buf, triggered = _konami_step(buf, Qt.Key_Up)
    assert buf == [Qt.Key_Up]
    assert triggered is False


def test_full_sequence_after_failed_attempt():
    """乱按后 buf 重置为空，再按完整序列也能触发（用一个无关键彻底清空）。"""
    buf: list = []
    for k in [Qt.Key_Up, Qt.Key_Down, Qt.Key_X]:  # X 把 buf 清空
        buf, _ = _konami_step(buf, k)
    assert buf == []
    triggered = False
    for k in _full_sequence():
        buf, triggered = _konami_step(buf, k)
    assert triggered is True
