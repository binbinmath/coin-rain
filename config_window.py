"""SetupWindow + ManageWindow —— 墨黑金 Lacquer Gold (V2)。

设计源：claude design 交付的 FINAL_SetupWindow_spec.html
"""
from __future__ import annotations

import re
from datetime import datetime

from PySide6.QtCore import Qt, QTime, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QButtonGroup, QFrame, QMessageBox,
    QTimeEdit, QDialog, QDialogButtonBox, QGraphicsOpacityEffect,
    QSizePolicy,
)

from config import Config, CONFIG_VERSION, resource_path


WIN_W, WIN_H = 960, 600
HERO_PANE_W = 330
HERO_COIN_SIZE = 260
HERO_COIN_OFFSET = 70  # 右下方各露出 70px

DEFAULT_INCOME = 300
DEFAULT_INTENSITY = "medium"
DEFAULT_MODE = "single"
DEFAULT_TIME = "17:00"
DEFAULT_TIMES = ["08:00", "13:00", "21:00"]
MAX_TIMES = 6

# 作者主页 + 赞赏码
AUTHOR_URL = "https://www.learnbuffett.com/about"
COFFEE_IMAGE = "赞赏码.jpg"

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


# ============== 动态文案（移植自 04_setup_C_states.html · makeQuote） ==============

# (上限h, cn, en)
_TIME_BUCKETS: list[tuple[int, str, str]] = [
    (6,  "夜 里", "a deep night"),
    (9,  "清 晨", "early morning"),
    (11, "上 午", "late morning"),
    (14, "正 午", "noon"),
    (17, "午 后", "afternoon"),
    (19, "傍 晚", "sunset"),
    (22, "夜 晚", "evening"),
    (24, "深 夜", "late at night"),
]
_RAIN_CN = {"light": "小 雨", "medium": "细 雨", "heavy": "大 雨", "storm": "骤 雨"}
_RAIN_EN = {
    "light":  "a light shower",
    "medium": "a soft drizzle",
    "heavy":  "a heavy rain",
    "storm":  "a sudden downpour",
}


def time_bucket(hhmm: str) -> tuple[str, str]:
    """HH:MM → (中文段, 英文段)。"""
    try:
        h = int(hhmm.split(":")[0])
    except (ValueError, AttributeError, IndexError):
        h = 17
    for upper, cn, en in _TIME_BUCKETS:
        if h < upper:
            return cn, en
    return "深 夜", "late at night"


def make_quote(*, intensity: str, mode: str, time: str | None, times: list[str]) -> tuple[str, str]:
    """根据 4 个字段实时拼出左下方的中文 + 英文短句。"""
    rain = intensity if intensity in _RAIN_CN else "medium"
    if mode == "single":
        cn_b, en_b = time_bucket(time or DEFAULT_TIME)
        cn = f"{cn_b}  一 场  {_RAIN_CN[rain]}"
        en = f"{_RAIN_EN[rain]} at {en_b}, gold falling on a black lacquer box."
        return cn, en
    # multi
    if not times:
        return f"待 添 加 时 刻  ·  {_RAIN_CN[rain]}", "add at least one moment to begin."
    buckets = list(dict.fromkeys(time_bucket(t)[0] for t in times))
    if len(buckets) >= 3:
        cn = f"{'   '.join(buckets[:3])}   数 阵  {_RAIN_CN[rain]}"
    elif len(buckets) == 2:
        cn = f"{buckets[0]}  与  {buckets[1]}  各 一 场  {_RAIN_CN[rain]}"
    else:
        cn = f"一 日 数 回  ·  {_RAIN_CN[rain]}"
    en = f"{len(times)} short rains through the day, each {_RAIN_EN[rain]}."
    return cn, en


# ============== 工具 ==============

def _load_qss() -> str:
    try:
        return resource_path("style.qss").read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _validate_income(text: str) -> int | None:
    try:
        n = int(text)
        if 10 <= n <= 99999:
            return n
    except ValueError:
        pass
    return None


def _validate_time(text: str) -> str | None:
    return text if _TIME_RE.match(text) else None


_active_rain_windows: list = []  # 占住引用，防止 CoinRainWindow 被 GC


def _launch_test_rain() -> None:
    """同进程内开一个 CoinRainWindow 预览动画（不再 spawn 子进程）。

    子进程版会让 winsound 在某些 Windows 音频路由下静音；同进程跑就和命令行
    `coin_rain --rain --test` 完全等价，音效路径一致。
    """
    from datetime import date, datetime
    from rain_window import CoinRainWindow, _compute_amount, _load_coin_pixmaps
    import surprise

    cfg = Config.load()
    income = cfg.income if cfg else 300
    intensity = cfg.intensity if cfg else "medium"
    installed_at = cfg.installed_at if cfg else ""
    amount = _compute_amount(income=income, nth=1, total=1)

    today = date.today()
    if installed_at:
        try:
            d0 = datetime.fromisoformat(installed_at).date()
            days = max((today - d0).days + 1, 1)
        except ValueError:
            days = 1
    else:
        days = 1

    w = CoinRainWindow()
    w.set_amount(amount, "今 日 到 账")
    w.set_intensity(intensity)
    w.set_subtitle(surprise.compute_subtitle(
        days_since_install=days,
        today=today,
        daily_income=income,
        is_last_trigger=True,
    ))
    w.set_visual_overrides(surprise.compute_visual_overrides(today=today))
    w.set_lucky_coin(surprise.pick_lucky())
    w.set_coin_mode(surprise.pick_coin_mode(n_styles=len(_load_coin_pixmaps())))

    _active_rain_windows.append(w)

    def _cleanup() -> None:
        if w in _active_rain_windows:
            _active_rain_windows.remove(w)
        w.deleteLater()

    w.finished.connect(_cleanup)
    w.start()


# ============== 共享小控件 ==============

def _make_about_link(prominent: bool = False) -> QLabel:
    """关于作者超链接（点击跳转默认浏览器）。

    - prominent=False（默认）：hero 区底部的小链接，比 quote_foot 更亮但仍是辅助
    - prominent=True：赞赏码弹窗里使用，居中加大，作为主视觉之一
    """
    if prominent:
        html = (
            f'<a href="{AUTHOR_URL}" '
            f'style="color:#fff4cc; text-decoration:underline; text-decoration-color:#d4a84a;">'
            f'关 于 作 者  ·  learnbuffett.com / about</a>'
        )
        obj = "about_link_prominent"
    else:
        html = (
            f'<a href="{AUTHOR_URL}" '
            f'style="color:#d4a84a; text-decoration:none;">'
            f'关 于 作 者  ·  learnbuffett.com / about</a>'
        )
        obj = "about_link"

    label = QLabel(html)
    label.setObjectName(obj)
    label.setTextFormat(Qt.RichText)
    label.setOpenExternalLinks(True)
    label.setCursor(Qt.PointingHandCursor)
    if prominent:
        label.setAlignment(Qt.AlignCenter)
    return label


# ============== 请喝咖啡弹窗 ==============

class _CoffeeDialog(QDialog):
    """点击"请我喝杯咖啡"按钮后弹出的赞赏码窗口。

    赞赏码图片本身已包含完整文案 + 头像 + 二维码，这里只做容器 + 收尾按钮。
    """

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setWindowTitle("请 我 喝 杯 咖 啡")
        self.setStyleSheet(_load_qss())
        self.setFixedSize(500, 600)

        v = QVBoxLayout(self)
        v.setContentsMargins(28, 22, 28, 18)
        v.setSpacing(10)

        eyebrow = QLabel("T H A N K   Y O U  ·  谢   谢")
        eyebrow.setObjectName("right_eyebrow")
        eyebrow.setAlignment(Qt.AlignCenter)
        v.addWidget(eyebrow)

        # 赞赏码图（已含文案/头像/footer 带）
        img = QLabel()
        img.setObjectName("coffee_image")
        img.setAlignment(Qt.AlignCenter)
        path = resource_path(f"assets/{COFFEE_IMAGE}")
        if path.exists():
            pm = QPixmap(str(path))
            if not pm.isNull():
                pm = pm.scaled(
                    400, 400,
                    Qt.KeepAspectRatio, Qt.SmoothTransformation,
                )
                img.setPixmap(pm)
        else:
            img.setText("（赞赏码图片缺失）")
        v.addWidget(img, 1)

        # 核心：关于作者链接（居中、放大、加粗）
        v.addSpacing(4)
        v.addWidget(_make_about_link(prominent=True))

        # 关闭按钮
        bottom = QHBoxLayout()
        bottom.addStretch()
        close = QPushButton("关 闭")
        close.setObjectName("btn_secondary")
        close.setCursor(Qt.PointingHandCursor)
        close.clicked.connect(self.accept)
        bottom.addWidget(close)
        v.addLayout(bottom)


def _make_coffee_button(parent: QWidget) -> QPushButton:
    """统一构造"请我喝杯咖啡"按钮，点击弹 _CoffeeDialog。"""
    btn = QPushButton("请 我 喝 杯 咖 啡  ☕")
    btn.setObjectName("btn_coffee")
    btn.setCursor(Qt.PointingHandCursor)
    # emoji 在 Windows 上会用系统字体（Segoe UI Emoji 等）渲染，宽度不可预测；
    # 钉一个偏宽的最小宽度，宁可有富余也不要截断
    btn.setMinimumWidth(260)

    def _open() -> None:
        dlg = _CoffeeDialog(parent)
        dlg.exec()

    btn.clicked.connect(_open)
    return btn


# ============== 添加时刻的小弹窗 ==============

class _AddTimeDialog(QDialog):
    def __init__(self, parent: QWidget, default: str = "12:00") -> None:
        super().__init__(parent)
        self.setWindowTitle("添 加 时 刻")
        self.setStyleSheet(_load_qss())
        self.setFixedSize(280, 160)

        v = QVBoxLayout(self)
        v.setContentsMargins(28, 22, 28, 18)
        v.setSpacing(14)

        title = QLabel("添 加 一 个 时 刻")
        title.setObjectName("right_title")
        v.addWidget(title)

        self.te = QTimeEdit()
        self.te.setObjectName("time_input")
        self.te.setDisplayFormat("HH:mm")
        try:
            h, m = map(int, default.split(":"))
            self.te.setTime(QTime(h, m))
        except ValueError:
            self.te.setTime(QTime(12, 0))
        v.addWidget(self.te)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        ok = bb.button(QDialogButtonBox.Ok)
        ok.setObjectName("btn_primary")
        ok.setText("确 定")
        cancel = bb.button(QDialogButtonBox.Cancel)
        cancel.setObjectName("btn_secondary")
        cancel.setText("取 消")
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        v.addWidget(bb)

    def get_time(self) -> str:
        return self.te.time().toString("HH:mm")


# ============== 时刻 chip 列表 ==============

class _TimesChipsWidget(QWidget):
    """多次模式：横向显示 chip + "+ 添加" 按钮。"""

    changed = Signal()

    def __init__(self, initial: list[str] | None = None) -> None:
        super().__init__()
        self._times: list[str] = list(initial or [])
        self._row = QHBoxLayout(self)
        self._row.setContentsMargins(0, 4, 0, 4)
        self._row.setSpacing(6)
        self._rebuild()

    def get_times(self) -> list[str]:
        return list(self._times)

    def set_times(self, ts: list[str]) -> None:
        self._times = list(ts)
        self._rebuild()
        self.changed.emit()

    def _rebuild(self) -> None:
        # 清空
        while self._row.count():
            item = self._row.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        # chips
        for t in sorted(self._times):
            chip = QPushButton(f"{t}   ×")
            chip.setObjectName("chip")
            chip.setCursor(Qt.PointingHandCursor)
            chip.setToolTip("点击删除此时刻")
            chip.clicked.connect(lambda _=False, tt=t: self._remove(tt))
            self._row.addWidget(chip)
        # add 按钮（仅当未达上限）
        if len(self._times) < MAX_TIMES:
            add = QPushButton("+  添 加")
            add.setObjectName("chip_add")
            add.setCursor(Qt.PointingHandCursor)
            add.clicked.connect(self._open_add_dialog)
            self._row.addWidget(add)
        self._row.addStretch()

    def _remove(self, t: str) -> None:
        if t in self._times:
            self._times.remove(t)
        self._rebuild()
        self.changed.emit()

    def _open_add_dialog(self) -> None:
        dlg = _AddTimeDialog(self, default="12:00")
        if dlg.exec() == QDialog.Accepted:
            t = dlg.get_time()
            if t and t not in self._times:
                self._times.append(t)
                self._rebuild()
                self.changed.emit()


# ============== SetupWindow ==============

class SetupWindow(QWidget):
    def __init__(self, initial: Config | None = None) -> None:
        super().__init__()
        self.setWindowTitle("金 币 雨  ·  Coin Rain")
        self.setFixedSize(WIN_W, WIN_H)

        self._mode = (initial.mode if initial else DEFAULT_MODE)
        self._intensity = (initial.intensity if initial else DEFAULT_INTENSITY)

        self._build_ui(initial)
        self.setStyleSheet(_load_qss())
        self._refresh_quote()

    # ----- UI 构造 -----

    def _build_ui(self, initial: Config | None) -> None:
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_left_pane())
        root.addWidget(self._build_right_pane(initial), 1)

    def _build_left_pane(self) -> QWidget:
        pane = QWidget()
        pane.setObjectName("hero_pane")
        pane.setFixedWidth(HERO_PANE_W)

        # hero coin（绝对定位，作为 pane 的子控件，layout 之外）
        coin_path = resource_path("assets/coins/datang.png")
        self.hero_coin = QLabel(pane)
        self.hero_coin.setObjectName("hero_coin")
        if coin_path.exists():
            pm = QPixmap(str(coin_path))
            pm = pm.scaled(
                HERO_COIN_SIZE, HERO_COIN_SIZE,
                Qt.KeepAspectRatio, Qt.SmoothTransformation,
            )
            self.hero_coin.setPixmap(pm)
        self.hero_coin.setGeometry(
            HERO_PANE_W - HERO_COIN_SIZE + HERO_COIN_OFFSET,
            WIN_H - HERO_COIN_SIZE + HERO_COIN_OFFSET,
            HERO_COIN_SIZE, HERO_COIN_SIZE,
        )
        self.hero_coin.lower()
        eff = QGraphicsOpacityEffect(self.hero_coin)
        eff.setOpacity(0.78)
        self.hero_coin.setGraphicsEffect(eff)

        # 上下两块 + 中间 stretch
        v = QVBoxLayout(pane)
        v.setContentsMargins(38, 48, 38, 48)
        v.setSpacing(0)

        # ---- 顶部 brand ----
        brand_box = QVBoxLayout()
        brand_box.setSpacing(6)
        eyebrow = QLabel("A  D A I L Y   R I T U A L  ·  №   0 0 1")
        eyebrow.setObjectName("brand_eyebrow")
        brand = QLabel("Coin Rain")
        brand.setObjectName("brand_en")
        brand_cn = QLabel("金   币   雨")
        brand_cn.setObjectName("brand_cn")
        brand_box.addWidget(eyebrow)
        brand_box.addWidget(brand)
        brand_box.addWidget(brand_cn)
        v.addLayout(brand_box)

        v.addStretch(1)

        # ---- 底部 quote ----
        quote_box = QVBoxLayout()
        quote_box.setSpacing(10)
        self.quote_cn = QLabel("傍 晚  一 场  细 雨")
        self.quote_cn.setObjectName("quote_cn")
        self.quote_cn.setWordWrap(True)
        self.quote_en = QLabel("a soft drizzle at sunset, gold falling on a black lacquer box.")
        self.quote_en.setObjectName("quote_en")
        self.quote_en.setWordWrap(True)
        foot = QLabel("—   f i r s t   r u n  ·  2026.spring")
        foot.setObjectName("quote_foot")
        quote_box.addWidget(self.quote_cn)
        quote_box.addWidget(self.quote_en)
        quote_box.addWidget(foot)
        quote_box.addWidget(_make_about_link())
        v.addLayout(quote_box)

        return pane

    def _build_right_pane(self, initial: Config | None) -> QWidget:
        pane = QWidget()
        pane.setObjectName("right_pane")

        v = QVBoxLayout(pane)
        v.setContentsMargins(44, 48, 44, 24)
        v.setSpacing(6)

        eyebrow = QLabel("F O U R   Q U E S T I O N S  ·  设   四   问")
        eyebrow.setObjectName("right_eyebrow")
        v.addWidget(eyebrow)
        v.addSpacing(8)

        title = QLabel(
            "先 告 诉 它"
            "<span style='color:#d4a84a;font-style:italic;'>  ·  </span>"
            "四  件  事"
        )
        title.setObjectName("right_title")
        title.setTextFormat(Qt.RichText)
        v.addWidget(title)

        sub = QLabel("一  次  即  可    ·    之  后  不  再  打  扰")
        sub.setObjectName("right_sub")
        v.addWidget(sub)
        v.addSpacing(18)

        # ---- 4 字段网格 ----
        body = QGridLayout()
        body.setHorizontalSpacing(22)
        body.setVerticalSpacing(18)
        body.addLayout(self._build_income(initial), 0, 0)
        body.addLayout(self._build_mode(initial), 0, 1)
        body.addLayout(self._build_intensity(initial), 1, 0, 1, 2)
        # 时刻字段：用一个 stack-like 容器，single/multi 切换
        body.addLayout(self._build_time_field(initial), 2, 0, 1, 2)
        v.addLayout(body)
        v.addStretch(1)

        # ---- 分隔线 + footer ----
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("hrule")
        v.addWidget(sep)

        foot = QHBoxLayout()
        foot.setSpacing(12)
        foot.addStretch()
        self.coffee_btn = _make_coffee_button(self)
        self.test_btn = QPushButton("先  试")
        self.test_btn.setObjectName("btn_secondary")
        self.test_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn = QPushButton("保  存   →")
        self.save_btn.setObjectName("btn_primary")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        foot.addWidget(self.coffee_btn)
        foot.addWidget(self.test_btn)
        foot.addWidget(self.save_btn)
        v.addLayout(foot)

        # ---- wire ----
        self.test_btn.clicked.connect(self._on_test_click)
        self.save_btn.clicked.connect(self._on_save_click)
        self.income_input.textChanged.connect(self._refresh_quote)
        self.time_input.timeChanged.connect(self._refresh_quote)
        self.times_widget.changed.connect(self._refresh_quote)
        self.mode_btns["single"].toggled.connect(self._on_mode_changed)
        self.mode_btns["multi"].toggled.connect(self._on_mode_changed)
        for btn in self.intensity_btns.values():
            btn.toggled.connect(self._on_intensity_changed)

        self._apply_mode_visibility()
        return pane

    # ----- 字段构造 -----

    def _field_label(self, num: str, cn: str) -> QHBoxLayout:
        row = QHBoxLayout()
        row.setSpacing(0)
        n = QLabel(num)
        n.setObjectName("lab_num")
        l = QLabel(cn)
        l.setObjectName("lab_cn")
        row.addWidget(n)
        row.addSpacing(6)
        row.addWidget(l)
        row.addStretch()
        return row

    def _build_income(self, initial: Config | None) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(8)
        col.addLayout(self._field_label("i.", "每  日  收  入"))
        line = QHBoxLayout()
        line.setSpacing(6)
        prefix = QLabel("¥")
        prefix.setObjectName("income_prefix")
        self.income_input = QLineEdit(str(initial.income if initial else DEFAULT_INCOME))
        self.income_input.setObjectName("income_input")
        suffix = QLabel("元")
        suffix.setObjectName("lab_suffix")
        line.addWidget(prefix)
        line.addWidget(self.income_input, 1)
        line.addWidget(suffix)
        col.addLayout(line)
        return col

    def _build_mode(self, initial: Config | None) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(8)
        col.addLayout(self._field_label("ii.", "触  发  方  式"))
        row = QHBoxLayout()
        row.setSpacing(6)
        self.mode_btns: dict[str, QPushButton] = {}
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        for key, name in [("single", "每  日  一  次"), ("multi", "一  日  数  回")]:
            btn = QPushButton(name)
            btn.setObjectName("tile")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setChecked(key == self._mode)
            self.mode_btns[key] = btn
            self.mode_group.addButton(btn)
            row.addWidget(btn, 1)
        col.addLayout(row)
        return col

    def _build_intensity(self, initial: Config | None) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(8)
        col.addLayout(self._field_label("iii.", "雨  势"))
        row = QHBoxLayout()
        row.setSpacing(6)
        self.intensity_btns: dict[str, QPushButton] = {}
        self.intensity_group = QButtonGroup(self)
        self.intensity_group.setExclusive(True)
        for key, name in [
            ("light",  "小  雨"),
            ("medium", "中  雨"),
            ("heavy",  "大  雨"),
            ("storm",  "暴  雨"),
        ]:
            btn = QPushButton(name)
            btn.setObjectName("tile")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setChecked(key == self._intensity)
            self.intensity_btns[key] = btn
            self.intensity_group.addButton(btn)
            row.addWidget(btn, 1)
        col.addLayout(row)
        return col

    def _build_time_field(self, initial: Config | None) -> QVBoxLayout:
        col = QVBoxLayout()
        col.setSpacing(8)
        self._time_label_row = self._field_label("iv.", "时  刻")
        col.addLayout(self._time_label_row)
        # 用一个容器装 single / multi 两套控件
        self._time_container = QWidget()
        cv = QVBoxLayout(self._time_container)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(0)

        # single
        self._single_row = QWidget()
        sr = QHBoxLayout(self._single_row)
        sr.setContentsMargins(0, 0, 0, 0)
        sr.setSpacing(8)
        self.time_input = QTimeEdit()
        self.time_input.setObjectName("time_input")
        self.time_input.setDisplayFormat("HH:mm")
        try:
            t = initial.time if (initial and initial.time) else DEFAULT_TIME
            h, m = map(int, t.split(":"))
            self.time_input.setTime(QTime(h, m))
        except (ValueError, AttributeError):
            self.time_input.setTime(QTime(17, 0))
        self.time_input.setFixedWidth(160)
        self.time_bucket_label = QLabel("傍 晚")
        self.time_bucket_label.setObjectName("lab_suffix")
        sr.addWidget(self.time_input)
        sr.addStretch()
        sr.addWidget(self.time_bucket_label)
        cv.addWidget(self._single_row)

        # multi
        initial_times = (initial.times if initial and initial.times else DEFAULT_TIMES)
        self.times_widget = _TimesChipsWidget(initial=initial_times)
        cv.addWidget(self.times_widget)

        col.addWidget(self._time_container)
        return col

    # ----- 交互 -----

    def _current_intensity(self) -> str:
        for key, btn in self.intensity_btns.items():
            if btn.isChecked():
                return key
        return "medium"

    def _on_mode_changed(self, checked: bool) -> None:
        if not checked:
            return
        self._mode = "single" if self.mode_btns["single"].isChecked() else "multi"
        self._apply_mode_visibility()
        self._refresh_quote()

    def _on_intensity_changed(self, checked: bool) -> None:
        if checked:
            self._refresh_quote()

    def _apply_mode_visibility(self) -> None:
        is_single = self._mode == "single"
        self._single_row.setVisible(is_single)
        self.times_widget.setVisible(not is_single)
        # 单次模式下显示时刻段，多次模式下用 chip 列表自带说明
        self.time_bucket_label.setVisible(is_single)

    def _refresh_quote(self) -> None:
        rain = self._current_intensity()
        time_str = self.time_input.time().toString("HH:mm")
        cn, en = make_quote(
            intensity=rain,
            mode=self._mode,
            time=time_str,
            times=self.times_widget.get_times(),
        )
        self.quote_cn.setText(cn)
        self.quote_en.setText(en)
        # 时刻段 suffix（单次模式用）
        cn_b, _ = time_bucket(time_str)
        self.time_bucket_label.setText(cn_b)

    def _mark_invalid(self, widget: QLineEdit, invalid: bool) -> None:
        widget.setProperty("invalid", "true" if invalid else "false")
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    # ----- 校验 + 保存 -----

    def _validate(self) -> Config | None:
        income = _validate_income(self.income_input.text())
        self._mark_invalid(self.income_input, income is None)
        if income is None:
            return None

        if self._mode == "single":
            t = self.time_input.time().toString("HH:mm")
            return Config(
                version=CONFIG_VERSION,
                income=income,
                intensity=self._current_intensity(),
                mode="single",
                time=t,
                times=[],
                installed_at=datetime.now().isoformat(timespec="seconds"),
            )

        # multi
        times = sorted(set(self.times_widget.get_times()))
        if not times:
            QMessageBox.warning(self, "请添加时刻", "「一日数回」模式下至少添加 1 个时刻。")
            return None
        return Config(
            version=CONFIG_VERSION,
            income=income,
            intensity=self._current_intensity(),
            mode="multi",
            time=None,
            times=times,
            installed_at=datetime.now().isoformat(timespec="seconds"),
        )

    def _on_test_click(self) -> None:
        _launch_test_rain()

    def _on_save_click(self) -> None:
        cfg = self._validate()
        if cfg is None:
            QMessageBox.warning(self, "配置不合法", "请检查标红字段后重试。")
            return
        cfg.save()
        try:
            from scheduler import register as scheduler_register
            scheduler_register(cfg)
        except ImportError:
            pass
        except Exception as e:
            QMessageBox.critical(
                self, "任务计划注册失败",
                f"config.json 已保存，但任务计划注册失败：\n\n{e}",
            )
            return
        QMessageBox.information(
            self, "已 启 用",
            "配置已保存并注册任务计划。\n\n每天按时落下一场金币雨。",
        )
        self.close()


# ============== ManageWindow（同样的墨黑金，但展示态） ==============

class ManageWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("金 币 雨  ·  设 置 与 管 理")
        self.setFixedSize(WIN_W, WIN_H)
        self._cfg = Config.load()
        try:
            from scheduler import status as scheduler_status
            self._status = scheduler_status()
        except Exception:
            class _Fallback:
                exists = False
                enabled = False
                next_run = None
            self._status = _Fallback()

        self._build_ui()
        self.setStyleSheet(_load_qss())

    def _build_ui(self) -> None:
        # 也用左 hero + 右内容的同一种骨架，强化"同一份产品"
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_hero())
        root.addWidget(self._build_content(), 1)

    def _build_hero(self) -> QWidget:
        pane = QWidget()
        pane.setObjectName("hero_pane")
        pane.setFixedWidth(HERO_PANE_W)

        # hero coin
        coin_path = resource_path("assets/coins/datang.png")
        coin = QLabel(pane)
        coin.setObjectName("hero_coin")
        if coin_path.exists():
            pm = QPixmap(str(coin_path)).scaled(
                HERO_COIN_SIZE, HERO_COIN_SIZE,
                Qt.KeepAspectRatio, Qt.SmoothTransformation,
            )
            coin.setPixmap(pm)
        coin.setGeometry(
            HERO_PANE_W - HERO_COIN_SIZE + HERO_COIN_OFFSET,
            WIN_H - HERO_COIN_SIZE + HERO_COIN_OFFSET,
            HERO_COIN_SIZE, HERO_COIN_SIZE,
        )
        coin.lower()
        eff = QGraphicsOpacityEffect(coin)
        eff.setOpacity(0.78)
        coin.setGraphicsEffect(eff)

        v = QVBoxLayout(pane)
        v.setContentsMargins(38, 48, 38, 48)
        v.setSpacing(0)

        eyebrow = QLabel(self._installed_str())
        eyebrow.setObjectName("brand_eyebrow")
        brand = QLabel("Coin Rain")
        brand.setObjectName("brand_en")
        brand_cn = QLabel("金   币   雨")
        brand_cn.setObjectName("brand_cn")
        v.addWidget(eyebrow)
        v.addSpacing(6)
        v.addWidget(brand)
        v.addSpacing(2)
        v.addWidget(brand_cn)

        v.addStretch(1)

        # 下面：动态 quote（根据当前 cfg）
        if self._cfg:
            cn, en = make_quote(
                intensity=self._cfg.intensity,
                mode=self._cfg.mode,
                time=self._cfg.time,
                times=self._cfg.times,
            )
        else:
            cn, en = "—  —  —", "—"
        q = QLabel(cn)
        q.setObjectName("quote_cn")
        q.setWordWrap(True)
        e = QLabel(en)
        e.setObjectName("quote_en")
        e.setWordWrap(True)
        f = QLabel(f"—  已 经 进 账  {self._days_running()}  天")
        f.setObjectName("quote_foot")
        v.addWidget(q)
        v.addSpacing(10)
        v.addWidget(e)
        v.addSpacing(10)
        v.addWidget(f)
        v.addSpacing(6)
        v.addWidget(_make_about_link())

        return pane

    def _build_content(self) -> QWidget:
        pane = QWidget()
        pane.setObjectName("right_pane")

        v = QVBoxLayout(pane)
        v.setContentsMargins(44, 48, 44, 24)
        v.setSpacing(6)

        # 顶部 toggle
        top = QHBoxLayout()
        eb = QLabel("M A N A G I N G  ·  设   置   与   管   理")
        eb.setObjectName("right_eyebrow")
        top.addWidget(eb)
        top.addStretch()
        toggle_label = QLabel("每  日  自  动  运  行")
        toggle_label.setObjectName("lab_cn")
        top.addWidget(toggle_label)
        self.toggle_on = QPushButton("启 用")
        self.toggle_on.setObjectName("toggle_on")
        self.toggle_on.setCursor(Qt.PointingHandCursor)
        self.toggle_off = QPushButton("停 用")
        self.toggle_off.setObjectName("toggle_off")
        self.toggle_off.setCursor(Qt.PointingHandCursor)
        top.addSpacing(10)
        top.addWidget(self.toggle_on)
        top.addWidget(self.toggle_off)
        v.addLayout(top)
        v.addSpacing(14)

        title = QLabel("已   为   你   运   行   中")
        title.setObjectName("right_title")
        v.addWidget(title)
        sub = QLabel("配  置  来  自   %APPDATA%\\CoinRain\\config.json")
        sub.setObjectName("right_sub")
        v.addWidget(sub)
        v.addSpacing(20)

        # 4 cells summary card
        card = QWidget()
        card.setObjectName("summary_card")
        cg = QGridLayout(card)
        cg.setContentsMargins(28, 22, 28, 22)
        cg.setHorizontalSpacing(28)
        income_txt = f"¥{self._cfg.income}" if self._cfg else "¥ - -"
        cells = [
            ("每  日  收  入",  income_txt,                "daily income"),
            ("雨   势",        self._intensity_name(),    self._intensity_meta()),
            ("触  发  方  式",  self._mode_name(),         self._mode_meta()),
            ("时   间",        self._time_display(),      "daily ritual"),
        ]
        for idx, (k, val, sub_t) in enumerate(cells):
            kl = QLabel(k); kl.setObjectName("cell_k")
            vl = QLabel(val); vl.setObjectName("cell_v")
            sl = QLabel(sub_t); sl.setObjectName("cell_sub")
            wrap = QVBoxLayout()
            wrap.setSpacing(4)
            wrap.addWidget(kl)
            wrap.addWidget(vl)
            wrap.addWidget(sl)
            cg.addLayout(wrap, 0, idx)
        v.addWidget(card)
        v.addSpacing(14)

        # schedule strip
        strip = QWidget()
        strip.setObjectName("schedule_strip")
        sh = QHBoxLayout(strip)
        sh.setContentsMargins(24, 14, 24, 14)
        l1 = QLabel("下  一  次  金  币  雨"); l1.setObjectName("strip_label")
        l2 = QLabel(self._next_run_text());    l2.setObjectName("strip_next")
        l3 = QLabel(self._remain_text());      l3.setObjectName("strip_remain")
        sh.addWidget(l1); sh.addStretch(); sh.addWidget(l2); sh.addStretch(); sh.addWidget(l3)
        v.addWidget(strip)

        v.addStretch(1)

        # footer
        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setObjectName("hrule")
        v.addWidget(sep)
        foot = QHBoxLayout()
        foot.setSpacing(12)
        foot.addStretch()
        self.coffee_btn = _make_coffee_button(self)
        self.test_btn = QPushButton("先  试")
        self.test_btn.setObjectName("btn_secondary")
        self.test_btn.setCursor(Qt.PointingHandCursor)
        self.edit_btn = QPushButton("修  改  配  置")
        self.edit_btn.setObjectName("btn_secondary")
        self.edit_btn.setCursor(Qt.PointingHandCursor)
        self.close_btn = QPushButton("关  闭")
        self.close_btn.setObjectName("btn_primary")
        self.close_btn.setCursor(Qt.PointingHandCursor)
        foot.addWidget(self.coffee_btn)
        foot.addWidget(self.test_btn)
        foot.addWidget(self.edit_btn)
        foot.addWidget(self.close_btn)
        v.addLayout(foot)

        # wire
        self.test_btn.clicked.connect(_launch_test_rain)
        self.edit_btn.clicked.connect(self._on_edit)
        self.close_btn.clicked.connect(self.close)
        self.toggle_on.clicked.connect(lambda: self._set_enabled(True))
        self.toggle_off.clicked.connect(lambda: self._set_enabled(False))

        self._enabled = self._status.enabled
        self._paint_toggle()

        return pane

    # ---- helpers ----

    def _installed_str(self) -> str:
        if self._cfg and self._cfg.installed_at:
            return f"I N S T A L L E D  {self._cfg.installed_at[:10].replace('-', ' · ')}"
        return "M A N A G I N G   ·   C O I N   R A I N"

    def _days_running(self) -> int:
        if self._cfg is None or not self._cfg.installed_at:
            return 0
        try:
            dt = datetime.fromisoformat(self._cfg.installed_at)
            return max(0, (datetime.now() - dt).days)
        except (ValueError, AttributeError):
            return 0

    def _intensity_name(self) -> str:
        if not self._cfg:
            return "—"
        return {"light": "小 雨", "medium": "中 雨", "heavy": "大 雨", "storm": "暴 雨"}.get(
            self._cfg.intensity, "中 雨"
        )

    def _intensity_meta(self) -> str:
        if not self._cfg:
            return ""
        return {
            "light":  "20 coins · 3.0s",
            "medium": "40 coins · 4.5s",
            "heavy":  "80 coins · 6.0s",
            "storm":  "120 coins · 7.0s",
        }.get(self._cfg.intensity, "")

    def _mode_name(self) -> str:
        if not self._cfg:
            return "—"
        if self._cfg.mode == "single":
            return "每 日 一 次"
        return f"每 日 {len(self._cfg.times)} 回"

    def _mode_meta(self) -> str:
        if not self._cfg:
            return ""
        return "today's full amount" if self._cfg.mode == "single" else "spread across the day"

    def _time_display(self) -> str:
        if not self._cfg:
            return "--:--"
        if self._cfg.mode == "single":
            return self._cfg.time or "--:--"
        # 最多展示前 3 个，多了用 …
        if not self._cfg.times:
            return "—"
        head = " · ".join(self._cfg.times[:3])
        if len(self._cfg.times) > 3:
            head += " …"
        return head

    def _next_run_text(self) -> str:
        if not self._cfg:
            return "未 配 置"
        if not self._status.exists:
            return "未 注 册"
        if self._status.next_run:
            t = self._status.next_run.strftime("%H:%M")
            try:
                from rain_window import _compute_amount
                if self._cfg.mode == "multi":
                    total = len(self._cfg.times)
                    nth = self._cfg.times.index(t) + 1 if t in self._cfg.times else 1
                    amount = _compute_amount(income=self._cfg.income, nth=nth, total=total)
                else:
                    amount = self._cfg.income
            except Exception:
                amount = self._cfg.income
            return f"{t}  ·  预 计 ¥{amount}"
        return f"今 天  ·  {self._time_display()}"

    def _remain_text(self) -> str:
        if not self._status.next_run:
            return ""
        delta = self._status.next_run - datetime.now()
        total_seconds = delta.total_seconds()
        if total_seconds < 60:
            return "正  在  触  发"
        minutes = int(total_seconds / 60)
        if minutes < 60:
            return f"in  about  {minutes}  min"
        hours = int(minutes / 60)
        if hours < 24:
            return f"in  about  {hours}  h"
        return f"in  about  {int(hours / 24)}  days"

    def _paint_toggle(self) -> None:
        # 选中态用 toggle_on 样式，未选中用 toggle_off
        self.toggle_on.setObjectName("toggle_on" if self._enabled else "toggle_off")
        self.toggle_off.setObjectName("toggle_off" if self._enabled else "toggle_on")
        for b in (self.toggle_on, self.toggle_off):
            b.style().unpolish(b)
            b.style().polish(b)

    def _set_enabled(self, enabled: bool) -> None:
        try:
            from scheduler import enable as sched_enable, disable as sched_disable
            if enabled:
                sched_enable()
            else:
                sched_disable()
        except ImportError:
            pass
        except Exception as e:
            QMessageBox.critical(self, "任务计划操作失败", str(e))
            return
        self._enabled = enabled
        self._paint_toggle()

    def _on_edit(self) -> None:
        self._setup = SetupWindow(initial=self._cfg)
        self._setup.show()
        self.close()
