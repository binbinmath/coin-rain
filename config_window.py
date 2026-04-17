"""SetupWindow + ManageWindow：editorial 米白金风 PySide6 窗口。"""
from __future__ import annotations

import re
import subprocess
import sys
from datetime import datetime

from PySide6.QtCore import Qt, QTime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QButtonGroup, QFrame, QMessageBox,
    QTimeEdit, QSpinBox
)

from config import Config, resource_path


DEFAULT_INCOME = 300
DEFAULT_INTENSITY = "medium"
DEFAULT_MODE = "single"
DEFAULT_TIME = "17:00"
DEFAULT_FIRST = "09:00"
DEFAULT_LAST = "17:00"
DEFAULT_COUNT = 3
DEFAULT_COIN = "kaiyuan"

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _load_qss() -> str:
    try:
        return resource_path("style.qss").read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _validate_income(text: str) -> int | None:
    try:
        n = int(text)
        if 0 < n <= 99999:
            return n
    except ValueError:
        pass
    return None


def _validate_time(text: str) -> str | None:
    return text if _TIME_RE.match(text) else None


def _time_to_minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _launch_test_rain() -> None:
    """启动子进程打开 --rain --test 动画。"""
    if sys.argv[0].endswith(".py"):
        cmd = [sys.executable, sys.argv[0], "--rain", "--test"]
    else:
        cmd = [sys.argv[0], "--rain", "--test"]
    subprocess.Popen(cmd, close_fds=True)


class SetupWindow(QWidget):
    def __init__(self, initial: Config | None = None) -> None:
        super().__init__()
        self.setWindowTitle("金币雨 · 首次配置")
        self.setFixedSize(960, 600)
        self._mode = (initial.mode if initial else DEFAULT_MODE)
        self._intensity = (initial.intensity if initial else DEFAULT_INTENSITY)
        self._build_ui(initial)
        self.setStyleSheet(_load_qss())

    def _build_ui(self, initial: Config | None) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(44, 24, 44, 20)
        root.setSpacing(18)

        # Header
        hdr = QHBoxLayout()
        brand = QLabel("金币雨 · Rain"); brand.setObjectName("brand")
        hdr.addWidget(brand)
        hdr.addStretch()
        eyebrow = QLabel("A DAILY RITUAL · № 001"); eyebrow.setObjectName("eyebrow")
        hdr.addWidget(eyebrow)
        root.addLayout(hdr)

        # 2x2 grid
        grid = QGridLayout()
        grid.setHorizontalSpacing(56)
        grid.setVerticalSpacing(44)
        grid.addLayout(self._build_income_field(initial), 0, 0)
        grid.addLayout(self._build_mode_field(initial), 0, 1)
        grid.addLayout(self._build_intensity_field(initial), 1, 0)
        grid.addLayout(self._build_time_field(initial), 1, 1)
        root.addLayout(grid, 1)

        # Separator
        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setObjectName("hrule")
        root.addWidget(sep)

        # Footer
        foot = QHBoxLayout()
        note = QLabel("配置写入 %APPDATA%\\CoinRain\\config.json"); note.setObjectName("note")
        foot.addWidget(note); foot.addStretch()
        self.test_btn = QPushButton("先 试 一 下"); self.test_btn.setObjectName("btn_secondary")
        self.save_btn = QPushButton("保 存 并 启 用  ⟶"); self.save_btn.setObjectName("btn_primary")
        foot.addWidget(self.test_btn); foot.addWidget(self.save_btn)
        root.addLayout(foot)

        # Wire
        self.mode_btns["single"].toggled.connect(self._on_mode_changed)
        self.mode_btns["multi"].toggled.connect(self._on_mode_changed)
        self._apply_mode_visibility()
        self.test_btn.clicked.connect(self._on_test_click)
        self.save_btn.clicked.connect(self._on_save_click)

    # ---- Field builders ----

    def _field_head(self, num: str, label: str) -> QHBoxLayout:
        box = QHBoxLayout()
        n = QLabel(num); n.setObjectName("field_num")
        l = QLabel(label); l.setObjectName("field_label")
        box.addWidget(n); box.addWidget(l); box.addStretch()
        return box

    def _build_income_field(self, initial: Config | None) -> QVBoxLayout:
        col = QVBoxLayout()
        col.addLayout(self._field_head("01", "每 日 收 入"))
        row = QHBoxLayout()
        prefix = QLabel("¥"); prefix.setObjectName("income_prefix")
        self.income_input = QLineEdit(str(initial.income if initial else DEFAULT_INCOME))
        self.income_input.setObjectName("income_input")
        suffix = QLabel("元 / 天"); suffix.setObjectName("field_suffix")
        row.addWidget(prefix); row.addWidget(self.income_input, 1); row.addWidget(suffix)
        col.addLayout(row)
        return col

    def _build_intensity_field(self, initial: Config | None) -> QVBoxLayout:
        col = QVBoxLayout()
        col.addLayout(self._field_head("02", "雨 势"))
        row = QHBoxLayout(); row.setSpacing(8)
        self.intensity_btns: dict[str, QPushButton] = {}
        self.intensity_group = QButtonGroup(self); self.intensity_group.setExclusive(True)
        for key, name, meta in [
            ("light", "小 雨", "20 · 3s"),
            ("medium", "中 雨", "40 · 4.5s"),
            ("heavy", "大 雨", "80 · 6s"),
        ]:
            btn = QPushButton(f"{name}\n{meta}")
            btn.setObjectName("tile"); btn.setCheckable(True)
            btn.setChecked(key == self._intensity)
            self.intensity_btns[key] = btn
            self.intensity_group.addButton(btn)
            row.addWidget(btn)
        col.addLayout(row)
        return col

    def _build_mode_field(self, initial: Config | None) -> QVBoxLayout:
        col = QVBoxLayout()
        col.addLayout(self._field_head("03", "触 发 方 式"))
        row = QHBoxLayout(); row.setSpacing(8)
        self.mode_btns: dict[str, QPushButton] = {}
        self.mode_group = QButtonGroup(self); self.mode_group.setExclusive(True)
        for key, name, meta in [
            ("single", "每 天 · 一 次", "today's full amount"),
            ("multi", "每 天 · 多 次", "累计到账"),
        ]:
            btn = QPushButton(f"{name}\n{meta}")
            btn.setObjectName("tile"); btn.setCheckable(True)
            btn.setChecked(key == self._mode)
            self.mode_btns[key] = btn
            self.mode_group.addButton(btn)
            row.addWidget(btn)
        col.addLayout(row)
        return col

    def _build_time_field(self, initial: Config | None) -> QVBoxLayout:
        col = QVBoxLayout()
        col.addLayout(self._field_head("04", "触 发 时 间"))
        self.single_row = QHBoxLayout()
        self.time_input = self._make_time_edit(
            initial.time if (initial and initial.time) else DEFAULT_TIME,
            big=True,
        )
        self.time_input.setObjectName("time_input")
        self.time_input.setFixedWidth(160)
        self.time_hint = QLabel("每天按时落下\n「今日到账 ¥X」的金币雨")
        self.time_hint.setObjectName("time_hint")
        self.single_row.addWidget(self.time_input)
        self.single_row.addWidget(self.time_hint, 1)
        col.addLayout(self.single_row)

        # 多次模式 —— QTimeEdit 两个 + QSpinBox 一个
        self.multi_row = QHBoxLayout()
        self.multi_row.setSpacing(10)
        self.first_input = self._make_time_edit(
            initial.first_time if initial and initial.first_time else DEFAULT_FIRST,
            big=False,
        )
        self.last_input = self._make_time_edit(
            initial.last_time if initial and initial.last_time else DEFAULT_LAST,
            big=False,
        )
        for te in (self.first_input, self.last_input):
            te.setObjectName("time_input_small")
            te.setFixedWidth(108)
        self.count_input = QSpinBox()
        self.count_input.setObjectName("count_input")
        self.count_input.setRange(2, 12)
        self.count_input.setValue(initial.count if (initial and initial.count) else DEFAULT_COUNT)
        self.count_input.setFixedWidth(80)
        self.count_input.setSuffix(" 次")
        first_label = QLabel("首 次"); first_label.setObjectName("field_suffix")
        last_label = QLabel("末 次"); last_label.setObjectName("field_suffix")
        count_label = QLabel("次 数"); count_label.setObjectName("field_suffix")
        self.multi_row.addWidget(first_label)
        self.multi_row.addWidget(self.first_input)
        self.multi_row.addWidget(last_label)
        self.multi_row.addWidget(self.last_input)
        self.multi_row.addWidget(count_label)
        self.multi_row.addWidget(self.count_input)
        self.multi_row.addStretch()
        self._multi_widgets = [first_label, self.first_input, last_label, self.last_input, count_label, self.count_input]
        for w in self._multi_widgets:
            w.hide()
        col.addLayout(self.multi_row)
        return col

    def _make_time_edit(self, hhmm: str, big: bool) -> QTimeEdit:
        te = QTimeEdit()
        te.setDisplayFormat("HH:mm")
        te.setButtonSymbols(QTimeEdit.UpDownArrows)
        te.setAlignment(Qt.AlignCenter)
        te.setWrapping(True)
        try:
            h, m = map(int, hhmm.split(":"))
            te.setTime(QTime(h, m))
        except (ValueError, AttributeError):
            te.setTime(QTime(17, 0))
        return te

    # ---- Logic ----

    def _current_intensity(self) -> str:
        for key, btn in self.intensity_btns.items():
            if btn.isChecked():
                return key
        return "medium"

    def _on_mode_changed(self, checked: bool) -> None:
        if not checked:
            return
        if self.mode_btns["single"].isChecked():
            self._mode = "single"
        else:
            self._mode = "multi"
        self._apply_mode_visibility()

    def _apply_mode_visibility(self) -> None:
        is_single = self._mode == "single"
        self.time_input.setVisible(is_single)
        self.time_hint.setVisible(is_single)
        for w in self._multi_widgets:
            w.setVisible(not is_single)

    def _mark_invalid(self, widget: QLineEdit, invalid: bool) -> None:
        widget.setProperty("invalid", "true" if invalid else "false")
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def _validate(self) -> Config | None:
        ok = True

        income = _validate_income(self.income_input.text())
        self._mark_invalid(self.income_input, income is None)
        if income is None:
            ok = False

        if self._mode == "single":
            t = self.time_input.time().toString("HH:mm")
            first = last = None
            count = None
        else:
            first = self.first_input.time().toString("HH:mm")
            last = self.last_input.time().toString("HH:mm")
            count = self.count_input.value()
            t = None

            diff = _time_to_minutes(last) - _time_to_minutes(first)
            # first < last 且间距够容下 count 次（至少 N-1 分钟）
            if diff < (count - 1):
                QMessageBox.warning(
                    self, "时间范围不足",
                    f"「末次时间」必须晚于「首次时间」至少 {count - 1} 分钟，以容纳 {count} 次等距触发。",
                )
                ok = False

        if not ok:
            return None

        return Config(
            version=1,
            income=income,
            intensity=self._current_intensity(),
            mode=self._mode,
            time=t,
            first_time=first,
            last_time=last,
            count=count,
            coin_style=DEFAULT_COIN,
            mixed_coins=False,
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
        # 阶段 3 会接入 scheduler.register()，阶段 2 暂时不动任务计划
        try:
            from scheduler import register as scheduler_register, SchedulerError
            scheduler_register(cfg)
        except ImportError:
            pass  # 阶段 2：scheduler.py 尚未存在
        except Exception as e:
            QMessageBox.critical(
                self, "任务计划注册失败",
                f"config.json 已保存，但任务计划注册失败：\n\n{e}"
            )
            return
        QMessageBox.information(
            self, "已启用",
            "配置已保存并注册任务计划。\n每天按时打开您的金币雨。"
        )
        self.close()


class ManageWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("金币雨 · 设置与管理")
        self.setFixedSize(960, 600)
        self._cfg = Config.load()
        try:
            from scheduler import status as scheduler_status
            self._status = scheduler_status()
        except Exception:
            class _FallbackStatus:
                exists = False
                enabled = False
                next_run = None
            self._status = _FallbackStatus()

        self._build_ui()
        self.setStyleSheet(_load_qss())

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(44, 24, 44, 20)
        root.setSpacing(18)

        # Header + right-side toggle
        hdr = QHBoxLayout()
        left = QVBoxLayout()
        eyebrow = QLabel(self._installed_str()); eyebrow.setObjectName("eyebrow")
        brand = QLabel("金币雨 · Rain"); brand.setObjectName("brand")
        tag = QLabel(f"— 已为你自动运行 {self._days_running()} 天"); tag.setObjectName("tag_line")
        left.addWidget(eyebrow); left.addWidget(brand); left.addWidget(tag)
        hdr.addLayout(left, 1)

        right = QVBoxLayout()
        right.setAlignment(Qt.AlignRight | Qt.AlignTop)
        toggle_label = QLabel("每 日 自 动 运 行"); toggle_label.setObjectName("cell_k")
        toggle_label.setAlignment(Qt.AlignRight)
        right.addWidget(toggle_label)
        toggle_row = QHBoxLayout(); toggle_row.setSpacing(0); toggle_row.addStretch()
        self.toggle_on = QPushButton("启 用"); self.toggle_on.setObjectName("toggle_on")
        self.toggle_off = QPushButton("停 用"); self.toggle_off.setObjectName("toggle_off")
        toggle_row.addWidget(self.toggle_on); toggle_row.addWidget(self.toggle_off)
        right.addLayout(toggle_row)
        hdr.addLayout(right)
        root.addLayout(hdr)

        # Summary 4 cells
        card = QWidget(); card.setObjectName("summary_card")
        cg = QGridLayout(card)
        cg.setContentsMargins(32, 24, 32, 24)
        cg.setHorizontalSpacing(30)
        income_txt = f"¥{self._cfg.income}" if self._cfg else "¥--"
        cells = [
            ("每 日 收 入", income_txt, "daily income"),
            ("雨 势", self._intensity_name(), self._intensity_meta()),
            ("触 发 方 式", self._mode_name(), self._mode_meta()),
            ("时 间", self._time_display(), "daily ritual"),
        ]
        for idx, (k, v, sub) in enumerate(cells):
            kl = QLabel(k); kl.setObjectName("cell_k")
            vl = QLabel(v); vl.setObjectName("cell_v")
            sl = QLabel(sub); sl.setObjectName("cell_sub")
            col = QVBoxLayout()
            col.addWidget(kl); col.addWidget(vl); col.addWidget(sl)
            cg.addLayout(col, 0, idx)
        root.addWidget(card)

        # Schedule strip
        strip = QWidget(); strip.setObjectName("schedule_strip")
        sh = QHBoxLayout(strip)
        sh.setContentsMargins(28, 18, 28, 18)
        l1 = QLabel("下 一 次 金 币 雨"); l1.setObjectName("strip_label")
        l2 = QLabel(self._next_run_text()); l2.setObjectName("strip_next")
        l3 = QLabel(self._remain_text()); l3.setObjectName("strip_remain")
        sh.addWidget(l1); sh.addStretch(); sh.addWidget(l2); sh.addStretch(); sh.addWidget(l3)
        root.addWidget(strip)

        # Footer
        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setObjectName("hrule")
        root.addWidget(sep)
        foot = QHBoxLayout()
        note = QLabel("配置来自 %APPDATA%\\CoinRain\\config.json"); note.setObjectName("note")
        foot.addWidget(note); foot.addStretch()
        self.test_btn = QPushButton("先 试 一 下"); self.test_btn.setObjectName("btn_secondary")
        self.edit_btn = QPushButton("修 改 配 置"); self.edit_btn.setObjectName("btn_secondary")
        self.close_btn = QPushButton("关 闭 窗 口"); self.close_btn.setObjectName("btn_primary")
        foot.addWidget(self.test_btn); foot.addWidget(self.edit_btn); foot.addWidget(self.close_btn)
        root.addLayout(foot)

        # Wire
        self.test_btn.clicked.connect(lambda: _launch_test_rain())
        self.edit_btn.clicked.connect(self._on_edit)
        self.close_btn.clicked.connect(self.close)
        self.toggle_on.clicked.connect(lambda: self._set_enabled(True))
        self.toggle_off.clicked.connect(lambda: self._set_enabled(False))

        # Init toggle visual
        self._enabled = self._status.enabled
        self._paint_toggle()

    # ---- Helpers ----

    def _installed_str(self) -> str:
        if self._cfg and self._cfg.installed_at:
            return f"MANAGING · INSTALLED {self._cfg.installed_at[:10].replace('-', ' · ')}"
        return "MANAGING · COIN RAIN"

    def _days_running(self) -> int:
        if self._cfg is None:
            return 0
        try:
            dt = datetime.fromisoformat(self._cfg.installed_at)
            return max(0, (datetime.now() - dt).days)
        except (ValueError, AttributeError):
            return 0

    def _intensity_name(self) -> str:
        if not self._cfg:
            return "--"
        return {"light": "小 雨", "medium": "中 雨", "heavy": "大 雨"}.get(self._cfg.intensity, "中 雨")

    def _intensity_meta(self) -> str:
        if not self._cfg:
            return ""
        return {"light": "20 coins · 3s", "medium": "40 coins · 4.5s", "heavy": "80 coins · 6s"}[self._cfg.intensity]

    def _mode_name(self) -> str:
        if not self._cfg:
            return "--"
        return "每 天 一 次" if self._cfg.mode == "single" else f"每 天 {self._cfg.count} 次"

    def _mode_meta(self) -> str:
        if not self._cfg:
            return ""
        return "today's full amount" if self._cfg.mode == "single" else "累计到账"

    def _time_display(self) -> str:
        if not self._cfg:
            return "--:--"
        if self._cfg.mode == "single":
            return self._cfg.time or "--:--"
        return f"{self._cfg.first_time} · {self._cfg.last_time}"

    def _next_run_text(self) -> str:
        if not self._cfg:
            return "未配置"
        if not self._status.exists:
            return "未注册任务计划"
        if self._status.next_run:
            t = self._status.next_run.strftime("%H:%M")
            # 根据 next_run 判断是多次模式的第几次，计算金额
            try:
                from rain_window import _compute_amount
                from scheduler import _distribute_times
                if self._cfg.mode == "multi":
                    times = _distribute_times(self._cfg.first_time, self._cfg.last_time, self._cfg.count)
                    nth = times.index(t) + 1 if t in times else 1
                    amount = _compute_amount(income=self._cfg.income, nth=nth, total=self._cfg.count)
                else:
                    amount = self._cfg.income
            except Exception:
                amount = self._cfg.income
            return f"{t} · 预计到账 ¥{amount}"
        return f"今天 · {self._time_display()}"

    def _remain_text(self) -> str:
        if not self._status.next_run:
            return ""
        delta = self._status.next_run - datetime.now()
        total_seconds = delta.total_seconds()
        if total_seconds < 60:
            return "正在触发"
        minutes = int(total_seconds / 60)
        if minutes < 60:
            return f"in about {minutes} min"
        hours = int(minutes / 60)
        if hours < 24:
            return f"in about {hours} h"
        return f"in about {int(hours / 24)} days"

    def _paint_toggle(self) -> None:
        self.toggle_on.setObjectName("toggle_on" if self._enabled else "toggle_off")
        self.toggle_off.setObjectName("toggle_off" if self._enabled else "toggle_on")
        for b in (self.toggle_on, self.toggle_off):
            b.style().unpolish(b); b.style().polish(b)

    def _set_enabled(self, enabled: bool) -> None:
        try:
            from scheduler import enable as sched_enable, disable as sched_disable, SchedulerError
            if enabled:
                sched_enable()
            else:
                sched_disable()
        except ImportError:
            pass  # 阶段 2 前 scheduler 不存在
        except Exception as e:
            QMessageBox.critical(self, "任务计划操作失败", str(e))
            return
        self._enabled = enabled
        self._paint_toggle()

    def _on_edit(self) -> None:
        self._setup = SetupWindow(initial=self._cfg)
        self._setup.show()
        self.close()
