# 金币雨 · 配置 UI + 到账大字 + 多次触发 · 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `coin_rain.py` 从"单文件玩具"升级为带首次配置 UI、到账大字、多次触发的可发布桌面小工具；沿用 editorial 米白金 serif 视觉风。

**Architecture:** 单 exe + CLI 参数分流：无参进 UI（Setup 或 Manage），`--rain` 进动画。Python 层拆 5 个平铺模块（`coin_rain.py` / `rain_window.py` / `config.py` / `config_window.py` / `scheduler.py`）。任务计划用 schtasks.exe subprocess；字体嵌入 TTF 保证跨机器一致。

**Tech Stack:** Python 3.11 · PySide6 6.7.2 · PyInstaller 6.10 · pytest（新增）· Windows schtasks.exe · winsound

**参考文档:** `docs/superpowers/specs/2026-04-16-coin-rain-config-ui-design.md`

---

## 阶段划分

- **阶段 0**（Pre-flight）：git 初始化、字体资源、依赖
- **阶段 1**（到账大字 + 开元通宝）：改 `coin_rain.py` 最小改动让大字可用
- **阶段 2**（配置与管理 UI）：拆文件、加 UI、argv 分流、config.json
- **阶段 3**（多次触发 + 任务计划 + 其余金币）：scheduler.py、多次模式、5 款金币、混合下落

每个阶段结束都有可打包、可跑的 exe。

---

## 阶段 0 · Pre-flight

### Task 0.1: 初始化 git 仓库（如尚未）

**Files:**
- Create: `.gitignore`

- [ ] **Step 1: 检查是否已是 git 仓库**

```bash
cd /e/Onedrive/Claude/Coin
git status 2>&1 | head -3
```

如果输出 `fatal: not a git repository`，继续 Step 2；否则跳到 Task 0.2。

- [ ] **Step 2: 初始化仓库并写 .gitignore**

创建 `.gitignore`：

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
.pytest_cache/

# PyInstaller
build/
dist/
*.spec.bak

# Visual companion 产物
.superpowers/

# 本地 IDE
.vscode/
.idea/
```

执行：

```bash
git init
git add .gitignore CLAUDE.md README.md requirements.txt build.bat \
        coin_rain.py coin_rain.spec install_schedule.ps1 uninstall_schedule.ps1 \
        "制作过程.md" assets/ docs/
git commit -m "chore: initialize repo with existing coin-rain baseline"
```

### Task 0.2: 下载并放置字体资源

**Files:**
- Create: `assets/fonts/Fraunces-VariableFont.ttf`
- Create: `assets/fonts/NotoSerifSC-VariableFont.ttf`

- [ ] **Step 1: 下载字体**

打开浏览器访问：
- `https://fonts.google.com/download?family=Fraunces` → 解压 → 取 `Fraunces-VariableFont_SOFT,WONK,opsz,wght.ttf`，重命名为 `Fraunces-VariableFont.ttf`
- `https://fonts.google.com/download?family=Noto%20Serif%20SC` → 解压 → 取 `NotoSerifSC-VariableFont_wght.ttf`（如只有静态字重，取 `NotoSerifSC-Medium.otf` 并在代码里改名），重命名为 `NotoSerifSC-VariableFont.ttf`

放入 `assets/fonts/` 目录（如不存在先 `mkdir assets/fonts`）。

- [ ] **Step 2: 验证文件存在**

```bash
ls -la assets/fonts/
```

Expected: 看到两个 TTF 文件，合计 2–5 MB。

- [ ] **Step 3: Commit**

```bash
git add assets/fonts/
git commit -m "chore: add Fraunces and Noto Serif SC fonts for embedded UI"
```

### Task 0.3: 添加 pytest 到依赖

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: 改 requirements.txt**

```
PySide6==6.7.2
pyinstaller==6.10.0
pytest==8.3.3
```

- [ ] **Step 2: 安装**

```bash
python -m pip install -r requirements.txt
```

Expected: pytest 安装成功。

- [ ] **Step 3: Commit**

```bash
git add requirements.txt
git commit -m "chore: add pytest to dependencies"
```

---

## 阶段 1 · 到账大字 + 开元通宝默认样式

> 本阶段不引入 UI、不动任务计划；只改 `coin_rain.py` 让动画本身有大字 + 默认金币换成开元通宝。阶段结束时双击 exe 或从命令行跑都直接看到新动画。

### Task 1.1: 拆出 resource_path 到 config.py（为后续模块共享）

**Files:**
- Create: `config.py`
- Modify: `coin_rain.py:41-44`

- [ ] **Step 1: 创建 config.py**

```python
"""配置数据模型 + 路径工具。

本模块故意不依赖 PySide6，保持纯 Python，方便 pytest 和 CLI 测试。
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def resource_path(rel: str) -> Path:
    """在开发态和 PyInstaller 打包态都能找到 assets/ 下的资源。"""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return base / rel


def config_dir() -> Path:
    """返回 %APPDATA%\\CoinRain（不存在则创建）。"""
    appdata = os.environ.get("APPDATA")
    if appdata:
        d = Path(appdata) / "CoinRain"
    else:
        d = Path.home() / ".coinrain"
    d.mkdir(parents=True, exist_ok=True)
    return d


def config_path() -> Path:
    return config_dir() / "config.json"
```

- [ ] **Step 2: 改 coin_rain.py 导入新位置的 resource_path**

Delete lines 41-44 (`def resource_path ...` block) in `coin_rain.py` and add at top (after the first docstring, with other imports):

```python
from config import resource_path
```

- [ ] **Step 3: 验证还能跑**

```bash
python coin_rain.py
```

Expected: 金币雨照常播（还没改大字和样式），约 4–5 秒后退出。

- [ ] **Step 4: Commit**

```bash
git add config.py coin_rain.py
git commit -m "refactor: move resource_path and config paths to config.py"
```

### Task 1.2: 新增 _compute_amount 纯函数 + pytest 测试

**Files:**
- Create: `rain_window.py`
- Create: `tests/__init__.py`
- Create: `tests/test_logic.py`

- [ ] **Step 1: 写测试**

Create `tests/__init__.py` as empty file. Create `tests/test_logic.py`:

```python
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
```

- [ ] **Step 2: 运行测试验证全部 FAIL**

```bash
python -m pytest tests/test_logic.py -v
```

Expected: ImportError（`rain_window` 还没创建）。

- [ ] **Step 3: 创建 rain_window.py 骨架**

Create `rain_window.py`:

```python
"""金币雨主窗口（CoinRainWindow）+ 相关纯逻辑。"""
from __future__ import annotations


def _compute_amount(*, income: int, nth: int, total: int) -> int:
    """多次/单次模式下本次触发要显示的到账金额。

    - nth ∈ [1, total]；nth == total 时返回 income（闭合）
    - 否则按整数元向下取整到 round(income * nth / total)
    """
    if nth == total:
        return income
    return round(income * nth / total)
```

- [ ] **Step 4: 运行测试验证全部 PASS**

```bash
python -m pytest tests/test_logic.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add rain_window.py tests/
git commit -m "feat: add _compute_amount pure function with TDD tests"
```

### Task 1.3: 把 CoinRainWindow 搬到 rain_window.py

**Files:**
- Modify: `rain_window.py`
- Modify: `coin_rain.py`

- [ ] **Step 1: 把 CoinRainWindow 及相关常量/dataclass 整块搬到 rain_window.py**

Replace `rain_window.py` with（把 `coin_rain.py` 里的常量区、`Coin`、`CoinRainWindow` 原样搬进来，**保留** `_compute_amount`）：

```python
"""金币雨主窗口（CoinRainWindow）+ 相关纯逻辑。"""
from __future__ import annotations

import math
import random
import winsound
from dataclasses import dataclass

from PySide6.QtCore import Qt, QTimer, QPointF, QElapsedTimer
from PySide6.QtGui import QColor, QGuiApplication, QPainter, QRadialGradient, QPen, QFont, QBrush
from PySide6.QtWidgets import QApplication, QWidget

from config import resource_path

# ================= 可调参数 =================
COIN_COUNT_MIN = 60
COIN_COUNT_MAX = 90
BATCH_COUNT = 8
BATCH_INTERVAL_MS = 350
COIN_DIAMETER_MIN = 36
COIN_DIAMETER_MAX = 60
GRAVITY = 550.0
VY_INIT_MIN = 120.0
VY_INIT_MAX = 240.0
VX_INIT_ABS_MAX = 80.0
ROT_SPEED_MIN = 3.0
ROT_SPEED_MAX = 10.0
FPS = 60
TIMEOUT_SAFETY_MS = 12000

COIN_FILL_CENTER = QColor("#FFE066")
COIN_FILL_EDGE = QColor("#D4A017")
COIN_STROKE = QColor("#8B6914")
COIN_SYMBOL = "¥"
COIN_SYMBOL_COLOR = QColor("#5C4A0A")
SHADOW_COLOR = QColor(0, 0, 0, 76)
# ============================================


def _compute_amount(*, income: int, nth: int, total: int) -> int:
    if nth == total:
        return income
    return round(income * nth / total)


@dataclass
class Coin:
    x: float
    y: float
    vx: float
    vy: float
    diameter: float
    angle: float
    angular_v: float


class CoinRainWindow(QWidget):
    # 完整复制 coin_rain.py 里原来的 CoinRainWindow class 代码，
    # 包括 __init__、_setup_sound、start、_spawn_batch、_make_coin、
    # _tick、paintEvent、_draw_coin 所有方法
    ...
```

> 注：`...` 处把 `coin_rain.py` 原来第 58–200 行的 `CoinRainWindow` class 整段内容原样贴进来。

- [ ] **Step 2: 改 coin_rain.py 为纯入口**

Replace entire `coin_rain.py`:

```python
"""金币雨入口 —— 解析 argv，派发到动画 / 配置 UI / 管理 UI。

当前阶段（阶段 1）只支持动画模式；UI 派发在阶段 2 接入。
"""
from __future__ import annotations

import os
import sys


def main() -> int:
    os.environ.setdefault("QT_LOGGING_RULES", "*.debug=false;qt.qpa.*=false")

    from PySide6.QtWidgets import QApplication
    from rain_window import CoinRainWindow

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    w = CoinRainWindow()
    w.start()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 3: 验证还能跑**

```bash
python coin_rain.py
```

Expected: 动画照常。

- [ ] **Step 4: 验证测试仍绿**

```bash
python -m pytest tests/test_logic.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add coin_rain.py rain_window.py
git commit -m "refactor: extract CoinRainWindow into rain_window.py"
```

### Task 1.4: 到账大字 count-up 层（B 巨字金光）

**Files:**
- Modify: `rain_window.py`

- [ ] **Step 1: 在 rain_window.py 顶部常量区追加大字样式常量**

在 `rain_window.py` 现有常量区末尾（`SHADOW_COLOR` 那行之后、`# ============================================` 之前）追加：

```python
# 到账大字样式
AMOUNT_FONT_FAMILY = "Fraunces"  # 阶段 2 才嵌入字体，此时先用 fallback
AMOUNT_COLOR = QColor("#f7d14a")
AMOUNT_SHADOW_COLOR = QColor(0, 0, 0, 160)
AMOUNT_GLOW_COLOR = QColor(247, 209, 74, 128)
AMOUNT_SIZE_RATIO = 0.16  # 数字高度 = 屏幕高 * 此值
CURRENCY_SIZE_RATIO = 0.46  # ¥ 字号 = 数字字号 * 此值
LABEL_FONT_FAMILY = "Noto Serif SC"
LABEL_COLOR = QColor("#f5e6c8")
LABEL_SIZE_RATIO = 0.022  # 中文副标字号 = 屏幕高 * 此值

COUNTUP_DURATION_MS = 1000  # count-up 持续时间
COIN_START_DELAY_MS = 1000  # 金币开始下落的延迟（对齐 count-up 结束）
```

- [ ] **Step 2: 在 CoinRainWindow.__init__ 末尾加大字状态字段**

在 `__init__` 方法的末尾（`self._setup_sound()` 之后）追加：

```python
        # 到账大字状态
        self._target_amount = 300  # 阶段 1 硬编码；阶段 2/3 从 config/argv 读
        self._current_amount = 0.0
        self._label_text = "今 日 到 账"
```

- [ ] **Step 3: 改 start() 把落币延后 1 秒、立即开始 count-up**

在 `rain_window.py` 里找 `def start(self)`，**替换**整个方法为：

```python
    def start(self) -> None:
        self.show()
        self._elapsed.start()
        # 阶段 1：大字和金币都跟着 _tick 驱动，count-up 在 0-1000ms，
        # 金币在 1000ms 后开始 spawn
        QTimer.singleShot(COIN_START_DELAY_MS, self._start_coins)
        self.timer.start()

    def _start_coins(self) -> None:
        if self._wav_path:
            winsound.PlaySound(self._wav_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        self._spawn_batch()
```

- [ ] **Step 4: 改 _tick 让 count-up 持续推进**

在 `_tick` 方法里，在 `now = self._elapsed.elapsed()` 之后、`if self._last_tick_ms is None` 之前，插入 count-up 推进：

```python
        # count-up 大字推进
        if now <= COUNTUP_DURATION_MS:
            progress = now / COUNTUP_DURATION_MS
            # ease-out cubic
            eased = 1 - (1 - progress) ** 3
            self._current_amount = eased * self._target_amount
        else:
            self._current_amount = float(self._target_amount)
```

且 `_tick` 的退出条件需要同时兼顾 "大字还没结束 或 金币还在"。把原来的退出条件：

```python
        all_spawned = self._spawned >= self._total_to_spawn
        if all_spawned and not self.coins:
            QApplication.quit()
            return
```

**替换**为：

```python
        # 大字淡出时间（动画结束后保留 400ms 再退）
        after_coins_done = self._spawned >= self._total_to_spawn and not self.coins
        after_countup_done = now >= COUNTUP_DURATION_MS
        if after_coins_done and after_countup_done:
            QApplication.quit()
            return
```

- [ ] **Step 5: 改 paintEvent 先画大字再画金币**

在 `paintEvent` 方法里，`for c in self.coins` 循环**之前**插入：

```python
        self._draw_amount(p)
```

然后在 class 末尾追加新方法 `_draw_amount`：

```python
    def _draw_amount(self, p: QPainter) -> None:
        """绘制中央金色大字 + 下方中文副标。"""
        import math as _m
        w = self._screen_w
        h = self._screen_h

        # 主数字字号
        num_px = int(h * AMOUNT_SIZE_RATIO)
        label_px = int(h * LABEL_SIZE_RATIO)

        num_text = f"¥{int(round(self._current_amount))}"

        # ---- Glow 层：多次模糊绘制模拟发光 ----
        p.save()
        glow_font = QFont(AMOUNT_FONT_FAMILY)
        glow_font.setPixelSize(num_px)
        glow_font.setWeight(QFont.Medium)
        p.setFont(glow_font)
        p.setPen(AMOUNT_GLOW_COLOR)
        fm = p.fontMetrics()
        tw = fm.horizontalAdvance(num_text)
        tx = (w - tw) / 2
        ty = h * 0.44 + fm.ascent() / 2
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1)]:
            p.drawText(QPointF(tx + dx, ty + dy), num_text)
        p.restore()

        # ---- Shadow ----
        p.save()
        num_font = QFont(AMOUNT_FONT_FAMILY)
        num_font.setPixelSize(num_px)
        num_font.setWeight(QFont.Medium)
        p.setFont(num_font)
        p.setPen(AMOUNT_SHADOW_COLOR)
        p.drawText(QPointF(tx + 4, ty + 6), num_text)
        p.restore()

        # ---- 主数字 ----
        p.save()
        p.setFont(num_font)
        p.setPen(AMOUNT_COLOR)
        p.drawText(QPointF(tx, ty), num_text)
        p.restore()

        # ---- 下方中文副标 ----
        p.save()
        label_font = QFont(LABEL_FONT_FAMILY)
        label_font.setPixelSize(label_px)
        label_font.setWeight(QFont.Medium)
        label_font.setLetterSpacing(QFont.PercentageSpacing, 200)
        p.setFont(label_font)
        p.setPen(LABEL_COLOR)
        fm2 = p.fontMetrics()
        lw = fm2.horizontalAdvance(self._label_text)
        lx = (w - lw) / 2
        ly = ty + label_px * 1.5
        # 影子
        p.save()
        p.setPen(AMOUNT_SHADOW_COLOR)
        p.drawText(QPointF(lx + 2, ly + 2), self._label_text)
        p.restore()
        p.setPen(LABEL_COLOR)
        p.drawText(QPointF(lx, ly), self._label_text)
        p.restore()
```

- [ ] **Step 6: 运行验证**

```bash
python coin_rain.py
```

Expected: 打开动画，**先 1 秒**看到中央金色 `¥0` → `¥300` 滚动 + 下方 "今 日 到 账"，1 秒后金币才开始下落 + 音效。约 5.5 秒结束。

- [ ] **Step 7: Commit**

```bash
git add rain_window.py
git commit -m "feat(rain): add count-up amount overlay with 1s pre-rain delay"
```

### Task 1.5: 把默认金币样式换成开元通宝

**Files:**
- Modify: `rain_window.py`

- [ ] **Step 1: 在 rain_window.py 常量区追加开元通宝色彩**

在 `SHADOW_COLOR` 之后、大字常量之前追加：

```python
# 开元通宝配色
KY_FILL_CENTER = QColor("#f4d88a")
KY_FILL_MID = QColor("#c89b4a")
KY_FILL_EDGE = QColor("#7a5420")
KY_STROKE = QColor("#3a2810")
KY_TEXT = QColor("#2a1810")
KY_HOLE_FILL = QColor("#1a1410")
KY_CHARS = ("开", "元", "通", "宝")  # 上 / 下 / 右 / 左 顺序
```

- [ ] **Step 2: 在 CoinRainWindow 类末尾追加新绘制函数 _draw_kaiyuan**

```python
    def _draw_kaiyuan(self, p: QPainter, c: Coin) -> None:
        """绘制开元通宝金币（方孔圆钱）。"""
        # 阴影
        p.save()
        p.translate(c.x, c.y + c.diameter * 0.55)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(SHADOW_COLOR))
        p.drawEllipse(QPointF(0, 0), c.diameter * 0.45, c.diameter * 0.12)
        p.restore()

        scale_x = abs(math.cos(c.angle))
        if scale_x < 0.08:
            scale_x = 0.08
        p.save()
        p.translate(c.x, c.y)
        p.scale(scale_x, 1.0)
        r = c.diameter / 2

        # 金币本体（径向渐变）
        grad = QRadialGradient(-r * 0.3, -r * 0.3, r * 1.5)
        grad.setColorAt(0.0, KY_FILL_CENTER)
        grad.setColorAt(0.4, KY_FILL_MID)
        grad.setColorAt(1.0, KY_FILL_EDGE)
        p.setBrush(QBrush(grad))
        p.setPen(QPen(KY_STROKE, max(1.0, c.diameter * 0.02)))
        p.drawEllipse(QPointF(0, 0), r, r)

        # 内圈线
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(KY_STROKE, 1))
        p.drawEllipse(QPointF(0, 0), r * 0.93, r * 0.93)

        # 方孔（边长 = 直径 0.36）
        hole = c.diameter * 0.36
        p.setBrush(QBrush(KY_HOLE_FILL))
        p.setPen(QPen(KY_STROKE, max(1.0, c.diameter * 0.025)))
        p.drawRect(int(-hole / 2), int(-hole / 2), int(hole), int(hole))

        # 4 字铭文：开 / 元 / 通 / 宝（上 下 右 左）
        font = QFont("Noto Serif SC")
        font.setPixelSize(int(c.diameter * 0.19))
        font.setBold(True)
        p.setFont(font)
        p.setPen(KY_TEXT)
        # 位置偏移（基于字号估算）
        off = c.diameter * 0.34
        positions = [
            (0, -off),    # 开（上）
            (0, off),     # 元（下）
            (off, 0),     # 通（右）
            (-off, 0),    # 宝（左）
        ]
        fm = p.fontMetrics()
        for (dx, dy), ch in zip(positions, KY_CHARS):
            tw = fm.horizontalAdvance(ch)
            th = fm.ascent() - fm.descent()
            p.drawText(QPointF(dx - tw / 2, dy + th / 2), ch)

        # 高光椭圆
        p.save()
        p.translate(-r * 0.35, -r * 0.4)
        p.rotate(-25)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 245, 210, 64))
        p.drawEllipse(QPointF(0, 0), r * 0.45, r * 0.22)
        p.restore()

        p.restore()
```

- [ ] **Step 3: 改 paintEvent 调用 _draw_kaiyuan 而非 _draw_coin**

找到 `paintEvent` 里的：

```python
        for c in self.coins:
            self._draw_coin(p, c)
```

**替换**为：

```python
        for c in self.coins:
            self._draw_kaiyuan(p, c)
```

> 注：旧的 `_draw_coin` 方法保留不删，阶段 3 会作为"现代 ¥ 样式"复用。

- [ ] **Step 4: 运行验证**

```bash
python coin_rain.py
```

Expected: 动画中金币变成了开元通宝（方孔圆钱，做旧金色，上下右左"开元通宝"4 字）。

- [ ] **Step 5: Commit**

```bash
git add rain_window.py
git commit -m "feat(rain): replace default coin with Kaiyuan Tongbao style"
```

### Task 1.6: 更新 build.bat / spec 支持新增 .py 文件

**Files:**
- Modify: `build.bat`

- [ ] **Step 1: 改 build.bat 显式包含所有 .py**

PyInstaller 会自动跟随 import，所以 `rain_window.py` / `config.py` 会被识别；但为明确性在 `--name coin_rain` 行之前追加明确的入口保留。保持当前 build.bat 不变即可（入口还是 `coin_rain.py`）。

只验证一次构建：

```bash
./build.bat
```

Expected: 构建成功，`dist/coin_rain.exe` 存在。

- [ ] **Step 2: 运行 exe 验证**

```bash
./dist/coin_rain.exe
```

Expected: 打开动画，开元通宝金币 + 先 1 秒大字 + 1 秒后落币。

- [ ] **Step 3: Commit (若 build.bat 有修改)**

```bash
# 如 build.bat 未改则跳过
git status
```

### Task 1.7: 阶段 1 checkpoint

- [ ] **Step 1: 手动 checklist**

验证所有下列行为：

- [ ] `python coin_rain.py` 打开动画
- [ ] 前 1.0 秒中央显示金色大字 `¥0` → `¥300`（count-up 滚动）+ 下方"今 日 到 账"
- [ ] 1.0 秒后金币开始从屏幕顶部落下 + "哗啦啦"音效
- [ ] 金币是开元通宝（方孔圆钱，上下右左"开元通宝"4 字）
- [ ] 约 5.5 秒后窗口自动关闭
- [ ] `pytest tests/ -v` 全绿（5 passed）
- [ ] `dist/coin_rain.exe` 打包成功、双击行为同 python 调用

- [ ] **Step 2: Tag 阶段 1 完成**

```bash
git tag stage-1-complete
```

---

## 阶段 2 · 配置与管理 UI

> 本阶段引入 argv 分流 + Setup/Manage 两个 UI 窗口。保存仅写 config.json，**不动**任务计划（保留老的 install_schedule.ps1 脚本）。阶段结束时：双击 exe 打开 UI；17:00 的触发仍靠老脚本。

### Task 2.1: Config dataclass + load/save + 测试

**Files:**
- Modify: `config.py`
- Modify: `tests/test_logic.py`

- [ ] **Step 1: 写测试**

在 `tests/test_logic.py` 末尾追加：

```python
import json
from pathlib import Path
from config import Config


def test_config_roundtrip_single(tmp_path, monkeypatch):
    """单次模式配置保存→读回，字段完全一致。"""
    target = tmp_path / "config.json"
    monkeypatch.setattr("config.config_path", lambda: target)

    c = Config(
        version=1,
        income=300,
        intensity="medium",
        mode="single",
        time="17:00",
        first_time=None,
        last_time=None,
        count=None,
        coin_style="kaiyuan",
        mixed_coins=False,
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
        version=1,
        income=600,
        intensity="heavy",
        mode="multi",
        time=None,
        first_time="09:00",
        last_time="17:00",
        count=3,
        coin_style="yongle",
        mixed_coins=True,
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
```

- [ ] **Step 2: 运行测试验证全部 FAIL**

```bash
python -m pytest tests/test_logic.py -v
```

Expected: 新增 5 个 test 失败（ImportError 或 Config 没定义）。

- [ ] **Step 3: 在 config.py 末尾追加 Config dataclass**

Append to `config.py`:

```python
import json
from dataclasses import dataclass, asdict


@dataclass
class Config:
    version: int
    income: int
    intensity: str      # "light" | "medium" | "heavy"
    mode: str           # "single" | "multi"
    time: str | None          # "HH:MM"，mode == "single" 时有值
    first_time: str | None    # "HH:MM"
    last_time: str | None
    count: int | None         # N ∈ [2, 12]
    coin_style: str     # "kaiyuan" | "yongle" | "xuanhe" | "longyang" | "modern_yuan"
    mixed_coins: bool
    installed_at: str   # ISO8601

    def save(self) -> None:
        config_path().write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2))

    @classmethod
    def load(cls) -> "Config | None":
        try:
            data = json.loads(config_path().read_text())
            return cls(**data)
        except (FileNotFoundError, json.JSONDecodeError, TypeError):
            return None

    @classmethod
    def exists(cls) -> bool:
        return config_path().exists()
```

- [ ] **Step 4: 运行测试验证 PASS**

```bash
python -m pytest tests/test_logic.py -v
```

Expected: 10 passed。

- [ ] **Step 5: Commit**

```bash
git add config.py tests/test_logic.py
git commit -m "feat: add Config dataclass with load/save roundtrip tests"
```

### Task 2.2: 嵌入字体到 exe + 运行时加载

**Files:**
- Create: `fonts.py`
- Modify: `build.bat`
- Modify: `coin_rain.spec`（如手动维护）

- [ ] **Step 1: 创建 fonts.py**

```python
"""在 QApplication 启动后加载嵌入的 TTF 字体。"""
from __future__ import annotations

from PySide6.QtGui import QFontDatabase

from config import resource_path


def load_embedded_fonts() -> None:
    """加载 Fraunces + Noto Serif SC。失败则静默（QSS 会 fallback）。"""
    for ttf in ("Fraunces-VariableFont.ttf", "NotoSerifSC-VariableFont.ttf"):
        path = resource_path(f"assets/fonts/{ttf}")
        if path.exists():
            QFontDatabase.addApplicationFont(str(path))
```

- [ ] **Step 2: 在 coin_rain.py main() 里调用字体加载**

在 `coin_rain.py` 的 `main()` 中，**替换**现有 `app = QApplication(sys.argv)` 行之后的内容：

```python
def main() -> int:
    os.environ.setdefault("QT_LOGGING_RULES", "*.debug=false;qt.qpa.*=false")

    from PySide6.QtWidgets import QApplication
    from rain_window import CoinRainWindow
    from fonts import load_embedded_fonts

    app = QApplication(sys.argv)
    load_embedded_fonts()  # 必须在 QApplication 之后
    app.setQuitOnLastWindowClosed(False)
    w = CoinRainWindow()
    w.start()
    return app.exec()
```

- [ ] **Step 3: 改 build.bat 的 --add-data 包含字体**

在 `build.bat` 中，找到：

```
  --add-data "assets/coin_drop.wav;assets" ^
```

**追加**一行：

```
  --add-data "assets/coin_drop.wav;assets" ^
  --add-data "assets/fonts;assets/fonts" ^
```

- [ ] **Step 4: 重新打包并验证**

```bash
./build.bat
```

Expected: 构建成功，`dist/coin_rain.exe` 增大 2–5 MB。

```bash
./dist/coin_rain.exe
```

Expected: 动画仍正常（字体加载不 raise，此阶段大字用字体已生效）。

- [ ] **Step 5: Commit**

```bash
git add fonts.py coin_rain.py build.bat
git commit -m "feat: embed Fraunces and Noto Serif SC fonts via QFontDatabase"
```

### Task 2.3: coin_rain.py 入口添加 argv 分流

**Files:**
- Modify: `coin_rain.py`

- [ ] **Step 1: 重写 coin_rain.py**

```python
"""金币雨入口 —— 解析 argv，派发到动画 / 配置 UI / 管理 UI。"""
from __future__ import annotations

import argparse
import os
import sys


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Coin Rain")
    p.add_argument("--rain", action="store_true", help="进入动画模式（任务计划触发用）")
    p.add_argument("--test", action="store_true", help="测试模式（配合 --rain）")
    p.add_argument("--nth", type=int, default=1, help="多次模式中这是第几次（1-based）")
    p.add_argument("--total", type=int, default=1, help="多次模式总次数")
    return p.parse_args(argv)


def _run_rain(args: argparse.Namespace) -> int:
    from PySide6.QtWidgets import QApplication
    from rain_window import CoinRainWindow, _compute_amount
    from fonts import load_embedded_fonts
    from config import Config

    cfg = Config.load()
    if cfg is None:
        # 没 config 时默认值（开发态/测试）
        income = 300
    else:
        income = cfg.income

    app = QApplication(sys.argv)
    load_embedded_fonts()
    app.setQuitOnLastWindowClosed(False)

    amount = _compute_amount(income=income, nth=args.nth, total=args.total)
    is_final = (args.nth == args.total) or args.test
    label = "今 日 到 账" if is_final else "当 前 已 到 账"

    w = CoinRainWindow()
    w.set_amount(amount, label)
    w.start()
    return app.exec()


def _run_ui() -> int:
    from PySide6.QtWidgets import QApplication
    from fonts import load_embedded_fonts
    from config import Config
    from config_window import SetupWindow, ManageWindow

    app = QApplication(sys.argv)
    load_embedded_fonts()
    if Config.exists():
        w = ManageWindow()
    else:
        w = SetupWindow()
    w.show()
    return app.exec()


def main(argv: list[str] | None = None) -> int:
    os.environ.setdefault("QT_LOGGING_RULES", "*.debug=false;qt.qpa.*=false")
    args = _parse_args(sys.argv[1:] if argv is None else argv)
    if args.rain:
        return _run_rain(args)
    return _run_ui()


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 在 rain_window.py CoinRainWindow 加 set_amount 方法**

在 `CoinRainWindow` class 的 `__init__` 之后、`_setup_sound` 之前追加：

```python
    def set_amount(self, amount: int, label: str) -> None:
        """在 start() 之前调用，设置本次到账大字的目标值和副标。"""
        self._target_amount = amount
        self._label_text = label
```

- [ ] **Step 3: 验证 --rain 分支仍能跑**

```bash
python coin_rain.py --rain
```

Expected: 直接进动画（大字 ¥300）。

- [ ] **Step 4: 验证无参分支**

```bash
python coin_rain.py
```

Expected: 此刻会 ImportError 因为 `config_window` 还不存在。下一 task 解决。先确认错误来自 import 即可。

- [ ] **Step 5: Commit**

```bash
git add coin_rain.py rain_window.py
git commit -m "feat: add argv dispatch for --rain vs UI mode"
```

### Task 2.4: SetupWindow 骨架（布局 + 4 字段 + 2 按钮）

**Files:**
- Create: `config_window.py`

- [ ] **Step 1: 创建 config_window.py**

```python
"""SetupWindow + ManageWindow：editorial 米白金风 PySide6 窗口。"""
from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QLineEdit, QPushButton, QButtonGroup, QFrame
)

from config import Config


DEFAULT_INCOME = 300
DEFAULT_INTENSITY = "medium"
DEFAULT_MODE = "single"
DEFAULT_TIME = "17:00"
DEFAULT_FIRST = "09:00"
DEFAULT_LAST = "17:00"
DEFAULT_COUNT = 3
DEFAULT_COIN = "kaiyuan"


class SetupWindow(QWidget):
    def __init__(self, initial: Config | None = None) -> None:
        super().__init__()
        self.setWindowTitle("金币雨 · 首次配置")
        self.setFixedSize(960, 600)
        self._mode = (initial.mode if initial else DEFAULT_MODE)
        self._intensity = (initial.intensity if initial else DEFAULT_INTENSITY)
        self._build_ui(initial)

    def _build_ui(self, initial: Config | None) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(44, 24, 44, 20)
        root.setSpacing(18)

        # --- Header ---
        hdr = QHBoxLayout()
        brand = QLabel("金币雨 · Rain")
        brand.setObjectName("brand")
        hdr.addWidget(brand)
        hdr.addStretch()
        eyebrow = QLabel("A Daily Ritual · № 001")
        eyebrow.setObjectName("eyebrow")
        hdr.addWidget(eyebrow)
        root.addLayout(hdr)

        # --- 2x2 grid of fields ---
        grid = QGridLayout()
        grid.setHorizontalSpacing(56)
        grid.setVerticalSpacing(44)

        grid.addLayout(self._build_income_field(initial), 0, 0)
        grid.addLayout(self._build_mode_field(initial), 0, 1)
        grid.addLayout(self._build_intensity_field(initial), 1, 0)
        grid.addLayout(self._build_time_field(initial), 1, 1)

        root.addLayout(grid, 1)

        # --- Separator + buttons ---
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setObjectName("hrule")
        root.addWidget(sep)

        foot = QHBoxLayout()
        self.note_label = QLabel(f"配置写入 %APPDATA%\\CoinRain\\config.json")
        self.note_label.setObjectName("note")
        foot.addWidget(self.note_label)
        foot.addStretch()
        self.test_btn = QPushButton("先 试 一 下")
        self.test_btn.setObjectName("btn_secondary")
        foot.addWidget(self.test_btn)
        self.save_btn = QPushButton("保 存 并 启 用  ⟶")
        self.save_btn.setObjectName("btn_primary")
        foot.addWidget(self.save_btn)
        root.addLayout(foot)

        # 初次绑定：测试/保存尚未接线（后续 Task）

    # --- 字段构建 helper 们 ---
    def _field_head(self, num: str, label: str) -> QHBoxLayout:
        box = QHBoxLayout()
        n = QLabel(num); n.setObjectName("field_num")
        l = QLabel(label); l.setObjectName("field_label")
        box.addWidget(n)
        box.addWidget(l)
        box.addStretch()
        return box

    def _build_income_field(self, initial: Config | None) -> QVBoxLayout:
        col = QVBoxLayout()
        col.addLayout(self._field_head("01", "每 日 收 入"))
        row = QHBoxLayout()
        prefix = QLabel("¥"); prefix.setObjectName("income_prefix")
        self.income_input = QLineEdit(str(initial.income if initial else DEFAULT_INCOME))
        self.income_input.setObjectName("income_input")
        suffix = QLabel("元 / 天"); suffix.setObjectName("field_suffix")
        row.addWidget(prefix)
        row.addWidget(self.income_input, 1)
        row.addWidget(suffix)
        col.addLayout(row)
        return col

    def _build_intensity_field(self, initial: Config | None) -> QVBoxLayout:
        col = QVBoxLayout()
        col.addLayout(self._field_head("02", "雨 势"))
        row = QHBoxLayout()
        row.setSpacing(8)
        self.intensity_btns: dict[str, QPushButton] = {}
        self.intensity_group = QButtonGroup(self)
        self.intensity_group.setExclusive(True)
        for key, name, meta in [
            ("light", "小 雨", "20 · 3s"),
            ("medium", "中 雨", "40 · 4.5s"),
            ("heavy", "大 雨", "80 · 6s"),
        ]:
            btn = QPushButton(f"{name}\n{meta}")
            btn.setObjectName("tile")
            btn.setCheckable(True)
            btn.setChecked(key == self._intensity)
            self.intensity_btns[key] = btn
            self.intensity_group.addButton(btn)
            row.addWidget(btn)
        col.addLayout(row)
        return col

    def _build_mode_field(self, initial: Config | None) -> QVBoxLayout:
        col = QVBoxLayout()
        col.addLayout(self._field_head("03", "触 发 方 式"))
        row = QHBoxLayout()
        row.setSpacing(8)
        self.mode_btns: dict[str, QPushButton] = {}
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        for key, name, meta in [
            ("single", "每 天 · 一 次", "today's full amount"),
            ("multi", "每 天 · 多 次", "累计到账"),
        ]:
            btn = QPushButton(f"{name}\n{meta}")
            btn.setObjectName("tile")
            btn.setCheckable(True)
            btn.setChecked(key == self._mode)
            self.mode_btns[key] = btn
            self.mode_group.addButton(btn)
            row.addWidget(btn)
        col.addLayout(row)
        return col

    def _build_time_field(self, initial: Config | None) -> QVBoxLayout:
        col = QVBoxLayout()
        col.addLayout(self._field_head("04", "触 发 时 间"))
        row = QHBoxLayout()
        self.time_input = QLineEdit(initial.time if (initial and initial.time) else DEFAULT_TIME)
        self.time_input.setObjectName("time_input")
        self.time_input.setFixedWidth(140)
        self.time_hint = QLabel("每天 17:00，落下\n「今日到账 ¥300」的金币雨")
        self.time_hint.setObjectName("time_hint")
        row.addWidget(self.time_input)
        row.addWidget(self.time_hint, 1)
        col.addLayout(row)
        # 多次模式子字段（先创建隐藏）
        self.multi_row = QHBoxLayout()
        self.first_input = QLineEdit(initial.first_time if initial and initial.first_time else DEFAULT_FIRST)
        self.last_input = QLineEdit(initial.last_time if initial and initial.last_time else DEFAULT_LAST)
        self.count_input = QLineEdit(str(initial.count if initial and initial.count else DEFAULT_COUNT))
        for le in (self.first_input, self.last_input, self.count_input):
            le.setObjectName("time_input")
            le.setFixedWidth(110)
        self.multi_row.addWidget(QLabel("首"))
        self.multi_row.addWidget(self.first_input)
        self.multi_row.addWidget(QLabel("末"))
        self.multi_row.addWidget(self.last_input)
        self.multi_row.addWidget(QLabel("次数"))
        self.multi_row.addWidget(self.count_input)
        self.multi_row.addStretch()
        self._multi_widgets = [self.first_input, self.last_input, self.count_input]
        for w in self._multi_widgets:
            w.hide()
        col.addLayout(self.multi_row)
        return col
```

- [ ] **Step 2: 创建 ManageWindow 占位（本 Task 只要能 import 成功）**

在 `config_window.py` 末尾追加：

```python
class ManageWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("金币雨 · 设置与管理")
        self.setFixedSize(960, 600)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("ManageWindow · 骨架（Task 2.10 填充）"))
```

- [ ] **Step 3: 跑一下**

```bash
python coin_rain.py
```

Expected: 无 config 时打开一个 960×600 的空白窗口，标题"金币雨 · 首次配置"，能看到标题+编号+字段布局，但样式是 Qt 默认灰色（下 task 加样式）。

- [ ] **Step 4: Commit**

```bash
git add config_window.py
git commit -m "feat(ui): add SetupWindow skeleton with 2x2 field grid"
```

### Task 2.5: SetupWindow QSS 样式（editorial 米白金）

**Files:**
- Create: `style.qss`
- Modify: `config_window.py`

- [ ] **Step 1: 创建 style.qss**

```css
/* editorial 米白金 · Setup & Manage 共用 */

QWidget {
    background-color: #faf3e4;
    color: #241810;
    font-family: "Noto Serif SC", serif;
    font-size: 14px;
}

/* Header */
QLabel#brand {
    font-family: "Fraunces", "Noto Serif SC", serif;
    font-size: 30px;
    font-weight: 500;
    letter-spacing: 2px;
    color: #241810;
}
QLabel#eyebrow {
    font-family: "Fraunces", serif;
    font-size: 10px;
    letter-spacing: 5px;
    color: #8a6830;
    text-transform: uppercase;
}

/* Field headings */
QLabel#field_num {
    font-family: "Fraunces", serif;
    font-size: 20px;
    color: #b8925a;
    font-style: italic;
}
QLabel#field_label {
    font-family: "Noto Serif SC", serif;
    font-size: 13px;
    font-weight: 500;
    letter-spacing: 3px;
    color: #241810;
    padding-left: 10px;
}
QLabel#field_suffix {
    font-family: "Noto Serif SC", serif;
    font-size: 12px;
    color: #6b5339;
    letter-spacing: 2px;
}

/* Income row */
QLabel#income_prefix {
    font-family: "Fraunces", serif;
    font-size: 26px;
    color: #b8925a;
}
QLineEdit#income_input {
    font-family: "Fraunces", serif;
    font-size: 38px;
    color: #241810;
    background: transparent;
    border: none;
    border-bottom: 1px solid #d8c9a8;
    padding: 2px 4px;
}
QLineEdit#income_input:focus {
    border-bottom: 1px solid #b8925a;
}

/* Tiles (intensity + mode) */
QPushButton#tile {
    background: rgba(255, 252, 243, 0.5);
    border: 1px solid #d8c9a8;
    color: #241810;
    padding: 12px 8px;
    font-family: "Noto Serif SC", serif;
    font-size: 13px;
    letter-spacing: 2px;
    min-height: 52px;
}
QPushButton#tile:hover {
    border: 1px solid #d4b67a;
    background: rgba(255, 252, 243, 1);
}
QPushButton#tile:checked {
    border: 1px solid #b8925a;
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(212,182,122,0.16), stop:1 rgba(184,146,90,0.06));
    color: #8a6830;
    font-weight: 500;
}

/* Time input */
QLineEdit#time_input {
    font-family: "Fraunces", serif;
    font-size: 38px;
    color: #241810;
    background: transparent;
    border: none;
    border-bottom: 1px solid #d8c9a8;
    padding: 2px 4px;
}
QLineEdit#time_input:focus {
    border-bottom: 1px solid #b8925a;
}
QLabel#time_hint {
    font-family: "Fraunces", serif;
    font-style: italic;
    font-size: 12px;
    color: #6b5339;
}

/* Separator */
QFrame#hrule {
    color: rgba(216, 201, 168, 0.5);
    background: rgba(216, 201, 168, 0.5);
    max-height: 1px;
}

/* Note */
QLabel#note {
    font-family: "Fraunces", serif;
    font-style: italic;
    font-size: 11px;
    color: #a08c6c;
    letter-spacing: 1px;
}

/* Buttons */
QPushButton#btn_secondary {
    background: transparent;
    border: 1px solid #b8925a;
    color: #8a6830;
    font-family: "Noto Serif SC", serif;
    font-size: 13px;
    letter-spacing: 3px;
    padding: 10px 24px;
    font-weight: 500;
}
QPushButton#btn_secondary:hover {
    background: rgba(184, 146, 90, 0.08);
}
QPushButton#btn_primary {
    background: #241810;
    color: #faf3e4;
    border: 1px solid #241810;
    font-family: "Noto Serif SC", serif;
    font-size: 13px;
    letter-spacing: 3px;
    padding: 10px 26px;
    font-weight: 500;
}
QPushButton#btn_primary:hover {
    background: #8a6830;
    border: 1px solid #8a6830;
}

/* Validation error */
QLineEdit[invalid="true"] {
    border-bottom: 1px solid #a83e2e;
}
```

- [ ] **Step 2: 在 config_window.py 顶部加载 QSS**

在 `config_window.py` imports 下方追加 helper：

```python
from config import resource_path


def _load_qss() -> str:
    try:
        return resource_path("style.qss").read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""
```

在 `SetupWindow.__init__` 方法末尾（`self._build_ui(initial)` 之后）加：

```python
        self.setStyleSheet(_load_qss())
```

同样在 `ManageWindow.__init__` 末尾加一行：

```python
        self.setStyleSheet(_load_qss())
```

- [ ] **Step 3: 改 build.bat 把 style.qss 打进 exe**

在 `build.bat` 的 `--add-data` 行之间追加：

```
  --add-data "style.qss;." ^
```

- [ ] **Step 4: 跑一下看效果**

```bash
python coin_rain.py
```

Expected: SetupWindow 现在是米白纸本底 + 金色强调，字段、tile 按钮、主/次按钮的样式与 mockup 视觉接近。

- [ ] **Step 5: Commit**

```bash
git add style.qss config_window.py build.bat
git commit -m "feat(ui): apply editorial cream-and-gold QSS to SetupWindow"
```

### Task 2.6: 单次/多次模式切换时字段展开

**Files:**
- Modify: `config_window.py`

- [ ] **Step 1: 连接 mode 按钮信号 → 显隐相应字段**

在 `SetupWindow._build_ui` 末尾（在 `foot` 那行之后、末尾处理之前）追加：

```python
        # 触发方式切换 → 时间字段显隐
        self.mode_btns["single"].toggled.connect(self._on_mode_changed)
        self.mode_btns["multi"].toggled.connect(self._on_mode_changed)
        self._apply_mode_visibility()
```

在 `SetupWindow` class 末尾追加方法：

```python
    def _on_mode_changed(self, checked: bool) -> None:
        # Only act on the one that became checked
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
```

- [ ] **Step 2: 同时追加 intensity 切换的状态同步**

在 class 末尾继续追加：

```python
    def _current_intensity(self) -> str:
        for key, btn in self.intensity_btns.items():
            if btn.isChecked():
                return key
        return "medium"
```

- [ ] **Step 3: 手动验证**

```bash
python coin_rain.py
```

Expected: 点「每天·多次」按钮，时间字段区从一个 `17:00` 变成 3 个输入框（首/末/次数）；切回「每天·一次」回到单 input。

- [ ] **Step 4: Commit**

```bash
git add config_window.py
git commit -m "feat(ui): toggle single/multi time fields in SetupWindow"
```

### Task 2.7: 表单校验（invalid 红线）

**Files:**
- Modify: `config_window.py`

- [ ] **Step 1: 添加校验函数**

在 `config_window.py` 顶部（imports 之后）追加：

```python
import re

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


def _validate_income(text: str) -> int | None:
    try:
        n = int(text)
        if 0 < n <= 99999:
            return n
    except ValueError:
        pass
    return None


def _validate_time(text: str) -> str | None:
    if _TIME_RE.match(text):
        return text
    return None


def _time_to_minutes(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)
```

- [ ] **Step 2: 在 SetupWindow 里加 _validate() 和 _mark_invalid**

在 `SetupWindow` class 末尾追加：

```python
    def _mark_invalid(self, widget: QLineEdit, invalid: bool) -> None:
        widget.setProperty("invalid", "true" if invalid else "false")
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def _validate(self) -> Config | None:
        """返回 Config 对象（合法时）或 None（任一字段非法时）。"""
        ok = True

        income = _validate_income(self.income_input.text())
        self._mark_invalid(self.income_input, income is None)
        if income is None:
            ok = False

        if self._mode == "single":
            t = _validate_time(self.time_input.text())
            self._mark_invalid(self.time_input, t is None)
            if t is None: ok = False
            first = last = None; count = None
        else:
            first = _validate_time(self.first_input.text())
            last = _validate_time(self.last_input.text())
            self._mark_invalid(self.first_input, first is None)
            self._mark_invalid(self.last_input, last is None)
            try:
                count = int(self.count_input.text())
                count_ok = 2 <= count <= 12
            except ValueError:
                count = None; count_ok = False
            self._mark_invalid(self.count_input, not count_ok)
            t = None

            if not (first and last and count_ok):
                ok = False
            else:
                diff = _time_to_minutes(last) - _time_to_minutes(first)
                if diff < (count - 1):
                    self._mark_invalid(self.first_input, True)
                    self._mark_invalid(self.last_input, True)
                    ok = False

        if not ok:
            return None

        from datetime import datetime
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
```

- [ ] **Step 3: 手动验证**

```bash
python coin_rain.py
```

Expected: 把 income 改成 `-1` 或 `abc`，保存按钮（下 task 接线）还没连着；但可以在 Python REPL 里跑 `_validate_income("abc")` 验证返回 None。

- [ ] **Step 4: Commit**

```bash
git add config_window.py
git commit -m "feat(ui): add form validation helpers for SetupWindow"
```

### Task 2.8: "先试一下"按钮 subprocess 启动

**Files:**
- Modify: `config_window.py`

- [ ] **Step 1: 在 SetupWindow 绑定 test_btn**

在 `_build_ui` 末尾的 mode 切换信号连接下方再追加：

```python
        self.test_btn.clicked.connect(self._on_test_click)
```

在 class 末尾追加方法：

```python
    def _on_test_click(self) -> None:
        """子进程启动当前 exe --rain --test，主窗口不退。"""
        import subprocess
        exe = sys.executable if sys.argv[0].endswith(".py") else sys.argv[0]
        if sys.argv[0].endswith(".py"):
            cmd = [sys.executable, sys.argv[0], "--rain", "--test"]
        else:
            cmd = [sys.argv[0], "--rain", "--test"]
        subprocess.Popen(cmd, close_fds=True)
```

（`import sys` 放文件顶部，如还没有的话。）

- [ ] **Step 2: 手动验证**

```bash
python coin_rain.py
```

打开 SetupWindow → 点「先 试 一 下」。

Expected: 一个新的动画窗口出现、播 4–5 秒后退出；主 Setup 窗口仍在。

- [ ] **Step 3: Commit**

```bash
git add config_window.py
git commit -m "feat(ui): wire test button to subprocess --rain --test"
```

### Task 2.9: "保存并启用"写 config.json（阶段 2 暂不注册任务）

**Files:**
- Modify: `config_window.py`

- [ ] **Step 1: 绑定 save_btn**

在 `_build_ui` 末尾追加：

```python
        self.save_btn.clicked.connect(self._on_save_click)
```

在 class 末尾追加方法：

```python
    def _on_save_click(self) -> None:
        from PySide6.QtWidgets import QMessageBox
        cfg = self._validate()
        if cfg is None:
            QMessageBox.warning(self, "配置不合法", "请检查标红字段后重试。")
            return
        cfg.save()
        QMessageBox.information(
            self, "已保存",
            "配置已写入。\n（阶段 2 暂未接入任务计划，请继续沿用 install_schedule.ps1 注册定时）"
        )
        self.close()
```

- [ ] **Step 2: 手动验证**

```bash
python coin_rain.py
```

首次没 config → SetupWindow；填入收入 300、选中雨、每天一次、17:00、点「保存并启用」。

Expected: 弹确认框；`%APPDATA%\CoinRain\config.json` 文件出现。

```bash
cat "$APPDATA/CoinRain/config.json"
```

Expected: JSON 里 income=300、mode=single、time=17:00 等。

再次运行 `python coin_rain.py` → 打开的是 ManageWindow 占位（Task 2.10 填内容）。

- [ ] **Step 3: Commit**

```bash
git add config_window.py
git commit -m "feat(ui): save config.json on setup completion"
```

### Task 2.10: ManageWindow（摘要 + 开关 + 下次预告 + 3 按钮）

**Files:**
- Modify: `config_window.py`
- Modify: `style.qss`

- [ ] **Step 1: 在 style.qss 末尾追加 Manage 专用样式**

```css
/* ManageWindow */
QWidget#summary_card {
    background: rgba(255, 252, 243, 0.5);
    border: 1px solid #d8c9a8;
}
QLabel#cell_k {
    font-family: "Noto Serif SC", serif;
    font-size: 10px;
    color: #8a6830;
    letter-spacing: 4px;
}
QLabel#cell_v {
    font-family: "Fraunces", serif;
    font-size: 32px;
    color: #241810;
    letter-spacing: 1px;
}
QLabel#cell_sub {
    font-family: "Fraunces", serif;
    font-style: italic;
    font-size: 11px;
    color: #a08c6c;
    letter-spacing: 1px;
}
QWidget#schedule_strip {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(212,182,122,0.12), stop:1 rgba(184,146,90,0.04));
    border: 1px solid #b8925a;
}
QLabel#strip_label {
    font-family: "Noto Serif SC", serif;
    font-size: 11px;
    color: #8a6830;
    letter-spacing: 4px;
}
QLabel#strip_next {
    font-family: "Fraunces", serif;
    font-size: 22px;
    color: #241810;
}
QLabel#strip_remain {
    font-family: "Fraunces", serif;
    font-style: italic;
    font-size: 13px;
    color: #6b5339;
}
QPushButton#toggle_on {
    background: #241810;
    color: #faf3e4;
    border: 1px solid #b8925a;
    padding: 8px 20px;
    font-family: "Noto Serif SC", serif;
    letter-spacing: 3px;
}
QPushButton#toggle_off {
    background: rgba(255,252,243,0.5);
    color: #6b5339;
    border: 1px solid #b8925a;
    padding: 8px 20px;
    font-family: "Noto Serif SC", serif;
    letter-spacing: 3px;
}
QLabel#tag_line {
    font-family: "Fraunces", serif;
    font-style: italic;
    font-size: 12px;
    color: #6b5339;
}
```

- [ ] **Step 2: 重写 ManageWindow**

替换 `config_window.py` 里 `ManageWindow` class（包括 __init__）为：

```python
class ManageWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("金币雨 · 设置与管理")
        self.setFixedSize(960, 600)
        self._cfg = Config.load()
        self._build_ui()
        self.setStyleSheet(_load_qss())

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(44, 24, 44, 20)
        root.setSpacing(18)

        # Header + toggle
        hdr = QHBoxLayout()
        left = QVBoxLayout()
        eyebrow = QLabel(self._installed_str()); eyebrow.setObjectName("eyebrow")
        brand = QLabel("金币雨 · Rain"); brand.setObjectName("brand")
        tag = QLabel(f"— 已为你自动运行 {self._days_running()} 天"); tag.setObjectName("tag_line")
        left.addWidget(eyebrow)
        left.addWidget(brand)
        left.addWidget(tag)
        hdr.addLayout(left, 1)

        right = QVBoxLayout()
        right.setAlignment(Qt.AlignRight | Qt.AlignTop)
        toggle_label = QLabel("每 日 自 动 运 行"); toggle_label.setObjectName("cell_k")
        toggle_label.setAlignment(Qt.AlignRight)
        right.addWidget(toggle_label)
        toggle_row = QHBoxLayout()
        toggle_row.setSpacing(0)
        toggle_row.addStretch()
        self.toggle_on = QPushButton("启 用"); self.toggle_on.setObjectName("toggle_on")
        self.toggle_off = QPushButton("停 用"); self.toggle_off.setObjectName("toggle_off")
        toggle_row.addWidget(self.toggle_on)
        toggle_row.addWidget(self.toggle_off)
        right.addLayout(toggle_row)
        hdr.addLayout(right)
        root.addLayout(hdr)

        # Summary 4 cells
        card = QWidget(); card.setObjectName("summary_card")
        cg = QGridLayout(card)
        cg.setContentsMargins(32, 24, 32, 24)
        cg.setHorizontalSpacing(30)
        cells = [
            ("每 日 收 入", f"¥{self._cfg.income}", "daily income"),
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

        # Next schedule strip
        strip = QWidget(); strip.setObjectName("schedule_strip")
        sh = QHBoxLayout(strip)
        sh.setContentsMargins(28, 18, 28, 18)
        l1 = QLabel("下 一 次 金 币 雨"); l1.setObjectName("strip_label")
        l2 = QLabel(self._next_run_text()); l2.setObjectName("strip_next")
        l3 = QLabel(self._remain_text()); l3.setObjectName("strip_remain")
        sh.addWidget(l1); sh.addStretch(); sh.addWidget(l2); sh.addStretch(); sh.addWidget(l3)
        root.addWidget(strip)

        # Footer buttons
        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setObjectName("hrule")
        root.addWidget(sep)
        foot = QHBoxLayout()
        note = QLabel(f"配置来自 %APPDATA%\\CoinRain\\config.json"); note.setObjectName("note")
        foot.addWidget(note)
        foot.addStretch()
        self.test_btn = QPushButton("先 试 一 下"); self.test_btn.setObjectName("btn_secondary")
        self.edit_btn = QPushButton("修 改 配 置"); self.edit_btn.setObjectName("btn_secondary")
        self.close_btn = QPushButton("关 闭 窗 口"); self.close_btn.setObjectName("btn_primary")
        foot.addWidget(self.test_btn); foot.addWidget(self.edit_btn); foot.addWidget(self.close_btn)
        root.addLayout(foot)

        # Wire
        self.test_btn.clicked.connect(self._on_test)
        self.edit_btn.clicked.connect(self._on_edit)
        self.close_btn.clicked.connect(self.close)
        # 阶段 2：开关仅反映当前视觉状态，还没真正调 schedule
        self._enabled = True
        self.toggle_on.clicked.connect(lambda: self._set_enabled(True))
        self.toggle_off.clicked.connect(lambda: self._set_enabled(False))

    # helpers
    def _installed_str(self) -> str:
        return f"Managing · Installed {self._cfg.installed_at[:10].replace('-', '·')}"

    def _days_running(self) -> int:
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(self._cfg.installed_at)
            return max(0, (datetime.now() - dt).days)
        except ValueError:
            return 0

    def _intensity_name(self) -> str:
        return {"light": "小 雨", "medium": "中 雨", "heavy": "大 雨"}.get(self._cfg.intensity, "中 雨")

    def _intensity_meta(self) -> str:
        return {"light": "20 coins · 3s", "medium": "40 coins · 4.5s", "heavy": "80 coins · 6s"}[self._cfg.intensity]

    def _mode_name(self) -> str:
        return "每 天 一 次" if self._cfg.mode == "single" else f"每 天 {self._cfg.count} 次"

    def _mode_meta(self) -> str:
        return "today's full amount" if self._cfg.mode == "single" else "累计到账"

    def _time_display(self) -> str:
        if self._cfg.mode == "single":
            return self._cfg.time or "--:--"
        return f"{self._cfg.first_time} · {self._cfg.last_time}"

    def _next_run_text(self) -> str:
        # 阶段 2：暂用 config 字段拼；阶段 3 接入 scheduler.status
        amount = self._cfg.income
        t = self._time_display()
        return f"今 天 · {t} · 今日到账 ¥{amount}"

    def _remain_text(self) -> str:
        return "in pending · 需阶段 3 接入任务计划"

    def _set_enabled(self, enabled: bool) -> None:
        self._enabled = enabled
        self.toggle_on.setObjectName("toggle_on" if enabled else "toggle_off")
        self.toggle_off.setObjectName("toggle_off" if enabled else "toggle_on")
        self.toggle_on.style().unpolish(self.toggle_on); self.toggle_on.style().polish(self.toggle_on)
        self.toggle_off.style().unpolish(self.toggle_off); self.toggle_off.style().polish(self.toggle_off)

    def _on_test(self) -> None:
        import subprocess, sys
        if sys.argv[0].endswith(".py"):
            cmd = [sys.executable, sys.argv[0], "--rain", "--test"]
        else:
            cmd = [sys.argv[0], "--rain", "--test"]
        subprocess.Popen(cmd, close_fds=True)

    def _on_edit(self) -> None:
        self._setup = SetupWindow(initial=self._cfg)
        self._setup.show()
        self.close()
```

- [ ] **Step 2: 手动验证**

```bash
python coin_rain.py
```

（假定上一 task 已经存了 config）

Expected: 打开 ManageWindow：摘要 4 字段显示正确；下方金色预告条显示今天+时间+金额；底部三按钮可见；右上角开关 toggle 能切换视觉。点「修改配置」会切到 SetupWindow 并带回现有值。

- [ ] **Step 3: Commit**

```bash
git add config_window.py style.qss
git commit -m "feat(ui): add ManageWindow with summary, toggle, and schedule strip"
```

### Task 2.11: 阶段 2 checkpoint

- [ ] **Step 1: 手动 checklist**

- [ ] 删除现有 config.json 后 `python coin_rain.py` 打开 SetupWindow
- [ ] 4 字段默认值、切换单次/多次、表单校验红线
- [ ] 「先试一下」子进程独立动画
- [ ] 「保存并启用」写 config.json
- [ ] 再次 `python coin_rain.py` 打开 ManageWindow
- [ ] 摘要与 config 一致、开关切换视觉变化
- [ ] 「修改配置」回到 SetupWindow
- [ ] `pytest tests/ -v` 全绿（10 passed）
- [ ] `./build.bat` 构建成功，`./dist/coin_rain.exe` 行为同 python

- [ ] **Step 2: Tag**

```bash
git tag stage-2-complete
```

---

## 阶段 3 · 多次触发 + 任务计划 + 其余金币

### Task 3.1: _distribute_times 纯函数 + 测试

**Files:**
- Modify: `tests/test_logic.py`
- Create: `scheduler.py`

- [ ] **Step 1: 写测试**

在 `tests/test_logic.py` 末尾追加：

```python
from scheduler import _distribute_times


def test_distribute_times_basic():
    assert _distribute_times("09:00", "17:00", 3) == ["09:00", "13:00", "17:00"]


def test_distribute_times_half_hours():
    assert _distribute_times("09:30", "17:30", 5) == ["09:30", "11:30", "13:30", "15:30", "17:30"]


def test_distribute_times_two_triggers():
    assert _distribute_times("10:00", "18:00", 2) == ["10:00", "18:00"]


def test_distribute_times_minute_precision():
    # 8:00 - 9:00 = 60min, N=7 -> 10min 间隔：08:00,08:10,08:20,08:30,08:40,08:50,09:00
    assert _distribute_times("08:00", "09:00", 7) == [
        "08:00", "08:10", "08:20", "08:30", "08:40", "08:50", "09:00"
    ]
```

- [ ] **Step 2: 运行测试验证 FAIL**

```bash
python -m pytest tests/test_logic.py -v
```

Expected: 4 new tests 失败（ImportError scheduler）。

- [ ] **Step 3: 创建 scheduler.py**

```python
"""Windows 任务计划封装 · schtasks.exe subprocess。"""
from __future__ import annotations


def _distribute_times(first: str, last: str, count: int) -> list[str]:
    """在 [first, last] 区间上均匀分布 count 个时间点（首尾含）。

    - first/last 格式 "HH:MM"
    - count >= 2
    - 分钟向最近整数取整
    """
    fh, fm = map(int, first.split(":"))
    lh, lm = map(int, last.split(":"))
    first_min = fh * 60 + fm
    last_min = lh * 60 + lm
    total_diff = last_min - first_min
    step = total_diff / (count - 1)
    result = []
    for i in range(count):
        m = first_min + round(step * i)
        h, mm = divmod(m, 60)
        result.append(f"{h:02d}:{mm:02d}")
    return result
```

- [ ] **Step 4: 测试 PASS**

```bash
python -m pytest tests/test_logic.py -v
```

Expected: 14 passed.

- [ ] **Step 5: Commit**

```bash
git add scheduler.py tests/test_logic.py
git commit -m "feat: add _distribute_times pure function with TDD"
```

### Task 3.2: scheduler.py 的 schtasks 封装骨架

**Files:**
- Modify: `scheduler.py`

- [ ] **Step 1: 扩展 scheduler.py**

在 `scheduler.py` 追加：

```python
import subprocess
from dataclasses import dataclass
from datetime import datetime

from config import Config

TASK_NAME = "CoinRainDaily"


class SchedulerError(RuntimeError):
    pass


@dataclass
class TaskStatus:
    exists: bool
    enabled: bool
    next_run: datetime | None


def _run(args: list[str], timeout: int = 10) -> subprocess.CompletedProcess:
    """统一的 schtasks 调用入口。"""
    return subprocess.run(
        args, capture_output=True, text=True, timeout=timeout,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )


def status() -> TaskStatus:
    """查询当前任务状态。任务不存在时 returncode != 0。"""
    r = _run(["schtasks.exe", "/Query", "/TN", TASK_NAME, "/FO", "LIST", "/V"])
    if r.returncode != 0:
        return TaskStatus(exists=False, enabled=False, next_run=None)
    # 粗略解析 Enabled / Next Run Time
    enabled = True
    next_run: datetime | None = None
    for line in r.stdout.splitlines():
        s = line.strip().lower()
        if s.startswith("scheduled task state"):
            enabled = "disabled" not in s
        if s.startswith("next run time:"):
            val = line.split(":", 1)[1].strip()
            try:
                next_run = datetime.strptime(val, "%m/%d/%Y %H:%M:%S")
            except ValueError:
                next_run = None
    return TaskStatus(exists=True, enabled=enabled, next_run=next_run)


def enable() -> None:
    r = _run(["schtasks.exe", "/Change", "/TN", TASK_NAME, "/ENABLE"])
    if r.returncode != 0:
        raise SchedulerError(r.stderr or r.stdout)


def disable() -> None:
    r = _run(["schtasks.exe", "/Change", "/TN", TASK_NAME, "/DISABLE"])
    if r.returncode != 0:
        raise SchedulerError(r.stderr or r.stdout)


def unregister() -> None:
    r = _run(["schtasks.exe", "/Delete", "/F", "/TN", TASK_NAME])
    if r.returncode != 0 and "cannot find" not in (r.stderr or "").lower():
        raise SchedulerError(r.stderr or r.stdout)
```

- [ ] **Step 2: Commit**

```bash
git add scheduler.py
git commit -m "feat(scheduler): add schtasks wrapper with status/enable/disable"
```

### Task 3.3: register() 单次模式

**Files:**
- Modify: `scheduler.py`

- [ ] **Step 1: 追加 register 函数**

在 `scheduler.py` 末尾追加：

```python
import sys
from pathlib import Path


def _exe_path() -> str:
    """当前运行的 exe/脚本绝对路径。"""
    if getattr(sys, "frozen", False):
        return sys.executable
    return str(Path(sys.argv[0]).resolve())


def _build_xml(exe: str, times: list[str], total: int) -> str:
    """构造 schtasks /XML 格式的 Task XML。N 个 CalendarTrigger。"""
    triggers_xml = ""
    for i, t in enumerate(times, start=1):
        args = f"--rain --nth={i} --total={total}"
        triggers_xml += f"""
    <CalendarTrigger>
      <StartBoundary>2026-01-01T{t}:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>
    </CalendarTrigger>"""
    # 注：单任务下多触发器无法为每个触发器绑不同参数；所以多次模式改为 N 个独立任务
    # 这个函数仅在"所有触发器共享同一命令行参数"时使用（此处用不到了）
    raise NotImplementedError("use register() directly")


def register(cfg: Config) -> None:
    """根据 config 注册任务计划。先卸载旧任务，再注册新的。"""
    unregister()
    exe = _exe_path()
    if cfg.mode == "single":
        _register_single(exe, cfg.time)
    else:
        times = _distribute_times(cfg.first_time, cfg.last_time, cfg.count)
        _register_multi(exe, times)


def _register_single(exe: str, time: str) -> None:
    tr = f'"{exe}" --rain --nth=1 --total=1'
    r = _run([
        "schtasks.exe", "/Create", "/F", "/TN", TASK_NAME,
        "/SC", "DAILY", "/ST", time, "/TR", tr, "/RL", "LIMITED",
    ])
    if r.returncode != 0:
        raise SchedulerError(r.stderr or r.stdout)
```

> 多次模式的实现放下一 task，因为它涉及 XML。

- [ ] **Step 2: Commit**

```bash
git add scheduler.py
git commit -m "feat(scheduler): register single-mode task via schtasks /Create"
```

### Task 3.4: register() 多次模式（N 个独立任务，不走 XML）

**Files:**
- Modify: `scheduler.py`

- [ ] **Step 1: 重新思考：多次模式改用 N 个独立任务**

schtasks 对同一任务的多触发器不支持"每个触发器带不同参数"。为避免 XML 的复杂度，**改为每次创建 N 个独立任务**：`CoinRainDaily_1`、`CoinRainDaily_2` 等。

- [ ] **Step 2: 改写 scheduler.py 的任务名常量和相关函数**

替换 `scheduler.py` 里的：

```python
TASK_NAME = "CoinRainDaily"
```

为：

```python
TASK_NAME_BASE = "CoinRainDaily"


def _task_names(mode: str, count: int | None) -> list[str]:
    """多次模式返回 N 个任务名；单次返回 1 个。"""
    if mode == "single":
        return [TASK_NAME_BASE]
    return [f"{TASK_NAME_BASE}_{i}" for i in range(1, (count or 1) + 1)]
```

相应修改原来调用 `TASK_NAME` 的函数改为迭代：

```python
def status() -> TaskStatus:
    # 查询是否任何一个任务存在 + 是否启用
    cfg = Config.load()
    if cfg is None:
        return TaskStatus(exists=False, enabled=False, next_run=None)
    names = _task_names(cfg.mode, cfg.count)

    any_exists = False
    all_enabled = True
    earliest: datetime | None = None
    for name in names:
        r = _run(["schtasks.exe", "/Query", "/TN", name, "/FO", "LIST", "/V"])
        if r.returncode != 0:
            continue
        any_exists = True
        enabled = True
        nr: datetime | None = None
        for line in r.stdout.splitlines():
            s = line.strip().lower()
            if s.startswith("scheduled task state"):
                if "disabled" in s:
                    enabled = False
            if s.startswith("next run time:"):
                val = line.split(":", 1)[1].strip()
                try:
                    nr = datetime.strptime(val, "%m/%d/%Y %H:%M:%S")
                except ValueError:
                    pass
        if not enabled:
            all_enabled = False
        if nr and (earliest is None or nr < earliest):
            earliest = nr
    return TaskStatus(exists=any_exists, enabled=(any_exists and all_enabled), next_run=earliest)


def enable() -> None:
    cfg = Config.load()
    if cfg is None: return
    for name in _task_names(cfg.mode, cfg.count):
        r = _run(["schtasks.exe", "/Change", "/TN", name, "/ENABLE"])
        if r.returncode != 0 and "cannot find" not in (r.stderr or "").lower():
            raise SchedulerError(r.stderr or r.stdout)


def disable() -> None:
    cfg = Config.load()
    if cfg is None: return
    for name in _task_names(cfg.mode, cfg.count):
        r = _run(["schtasks.exe", "/Change", "/TN", name, "/DISABLE"])
        if r.returncode != 0 and "cannot find" not in (r.stderr or "").lower():
            raise SchedulerError(r.stderr or r.stdout)


def unregister() -> None:
    # 尽量删除所有可能的任务名（base + base_1..12）
    candidates = [TASK_NAME_BASE] + [f"{TASK_NAME_BASE}_{i}" for i in range(1, 13)]
    for name in candidates:
        _run(["schtasks.exe", "/Delete", "/F", "/TN", name])  # 忽略失败
```

删除 `_build_xml` 函数，重写 `register`：

```python
def register(cfg: Config) -> None:
    unregister()
    exe = _exe_path()
    if cfg.mode == "single":
        _register_one(TASK_NAME_BASE, exe, cfg.time, nth=1, total=1)
    else:
        times = _distribute_times(cfg.first_time, cfg.last_time, cfg.count)
        for i, t in enumerate(times, start=1):
            _register_one(f"{TASK_NAME_BASE}_{i}", exe, t, nth=i, total=cfg.count)


def _register_one(name: str, exe: str, time: str, nth: int, total: int) -> None:
    tr = f'"{exe}" --rain --nth={nth} --total={total}'
    r = _run([
        "schtasks.exe", "/Create", "/F", "/TN", name,
        "/SC", "DAILY", "/ST", time, "/TR", tr, "/RL", "LIMITED",
    ])
    if r.returncode != 0:
        raise SchedulerError(r.stderr or r.stdout)
```

删掉之前 Task 3.3 写的 `_register_single`（被 `_register_one` 取代）。

- [ ] **Step 2: 手动测试（不集成 UI）**

```bash
python -c "from config import Config; from scheduler import register, status, unregister, disable, enable
from datetime import datetime
c = Config(version=1, income=300, intensity='medium', mode='multi',
           time=None, first_time='09:00', last_time='11:00', count=3,
           coin_style='kaiyuan', mixed_coins=False,
           installed_at=datetime.now().isoformat(timespec='seconds'))
c.save()
register(c)
print(status())
disable()
print(status())
enable()
print(status())
unregister()
print(status())
"
```

Expected: 能看到 `exists=True` → `enabled=False` → `enabled=True` → `exists=False` 的流转。用 `schtasks /Query /FO LIST | findstr CoinRain` 交叉验证。

- [ ] **Step 3: Commit**

```bash
git add scheduler.py
git commit -m "feat(scheduler): register multi-mode as N independent tasks with --nth/--total args"
```

### Task 3.5: SetupWindow 集成 scheduler.register

**Files:**
- Modify: `config_window.py`

- [ ] **Step 1: 改 _on_save_click**

在 `config_window.py` 顶部 imports 追加：

```python
from scheduler import register as scheduler_register, SchedulerError
```

把 `_on_save_click` 替换为：

```python
    def _on_save_click(self) -> None:
        from PySide6.QtWidgets import QMessageBox
        cfg = self._validate()
        if cfg is None:
            QMessageBox.warning(self, "配置不合法", "请检查标红字段后重试。")
            return
        cfg.save()
        try:
            scheduler_register(cfg)
        except SchedulerError as e:
            QMessageBox.critical(
                self, "任务计划注册失败",
                f"config.json 已保存，但任务计划注册失败：\n\n{e}\n\n"
                f"可以稍后手动重试或卸载旧任务后再打开此程序。"
            )
            return
        QMessageBox.information(
            self, "已启用",
            f"配置已保存并注册任务计划。\n每天按时打开您的金币雨。"
        )
        self.close()
```

- [ ] **Step 2: 手动验证**

```bash
python coin_rain.py
```

删除已有 config.json → SetupWindow → 填写配置 → 保存并启用。

Expected: 弹成功提示；`schtasks /Query /FO LIST | findstr CoinRain` 显示有 CoinRainDaily 任务。

- [ ] **Step 3: Commit**

```bash
git add config_window.py
git commit -m "feat(ui): integrate scheduler.register in SetupWindow save"
```

### Task 3.6: ManageWindow 集成 scheduler.status + 开关

**Files:**
- Modify: `config_window.py`

- [ ] **Step 1: 改 ManageWindow 用 scheduler.status() 填充预告条和初始开关状态**

在 `config_window.py` 顶部追加：

```python
from scheduler import status as scheduler_status, enable as scheduler_enable, disable as scheduler_disable
```

把 `ManageWindow.__init__` 里 `self._cfg = Config.load()` 之后追加：

```python
        self._status = scheduler_status()
```

把 `_next_run_text` 和 `_remain_text` 替换为：

```python
    def _next_run_text(self) -> str:
        if self._status.next_run is None:
            return "未注册"
        t = self._status.next_run.strftime("%H:%M")
        amount = self._cfg.income  # 简化：显示全额；阶段 3.9 用 _compute_amount
        return f"下次 · {t} · 预计到账 ¥{amount}"

    def _remain_text(self) -> str:
        if self._status.next_run is None:
            return ""
        from datetime import datetime
        delta = self._status.next_run - datetime.now()
        hours = delta.total_seconds() / 3600
        if hours < 1:
            return f"in about {int(delta.total_seconds() / 60)} min"
        if hours < 24:
            return f"in about {int(hours)} h"
        return f"in about {int(hours / 24)} days"
```

把 `_set_enabled` 替换为：

```python
    def _set_enabled(self, enabled: bool) -> None:
        from PySide6.QtWidgets import QMessageBox
        try:
            if enabled:
                scheduler_enable()
            else:
                scheduler_disable()
        except SchedulerError as e:
            QMessageBox.critical(self, "任务计划操作失败", str(e))
            return
        self._enabled = enabled
        # swap visuals
        self.toggle_on.setObjectName("toggle_on" if enabled else "toggle_off")
        self.toggle_off.setObjectName("toggle_off" if enabled else "toggle_on")
        self.toggle_on.style().unpolish(self.toggle_on); self.toggle_on.style().polish(self.toggle_on)
        self.toggle_off.style().unpolish(self.toggle_off); self.toggle_off.style().polish(self.toggle_off)
```

- [ ] **Step 2: 初始化 toggle 视觉按 status.enabled 显示**

在 `_build_ui` 末尾（所有 wire 之后）追加：

```python
        # 初始化 toggle 视觉
        self._enabled = self._status.enabled
        self._set_enabled(self._enabled)  # 注：这里会再调一次 scheduler，为避免循环改为仅视觉初始化：
```

**实际上**为避免初始化时又调 schedule，把上面替换为：

```python
        # 初始化 toggle 视觉（不调 scheduler）
        self._enabled = self._status.enabled
        self.toggle_on.setObjectName("toggle_on" if self._enabled else "toggle_off")
        self.toggle_off.setObjectName("toggle_off" if self._enabled else "toggle_on")
        self.toggle_on.style().unpolish(self.toggle_on); self.toggle_on.style().polish(self.toggle_on)
        self.toggle_off.style().unpolish(self.toggle_off); self.toggle_off.style().polish(self.toggle_off)
```

- [ ] **Step 3: 手动验证**

```bash
python coin_rain.py
```

Expected: ManageWindow 初始显示正确状态；下次预告条显示真实下次触发时间；切换开关 schtasks 状态随动（`schtasks /Query` 验证）。

- [ ] **Step 4: Commit**

```bash
git add config_window.py
git commit -m "feat(ui): integrate scheduler status and toggle into ManageWindow"
```

### Task 3.7: 添加其余 4 款金币样式

**Files:**
- Modify: `rain_window.py`

> 代码量较大，但结构固定。每款金币一个 `_draw_<style>` 方法。完整代码见实施时参考 mockup `coin-designs-v1.html` 的 SVG（可从中复制 gradient 色值和字符位置）。

- [ ] **Step 1: 追加 4 个绘制函数骨架**

在 `rain_window.py` 末尾（class 内，`_draw_kaiyuan` 之后）追加：

```python
    def _draw_yongle(self, p: QPainter, c: Coin) -> None:
        """永乐通宝 · 鎏金亮面 + 方孔。"""
        # 阴影
        p.save()
        p.translate(c.x, c.y + c.diameter * 0.55)
        p.setPen(Qt.NoPen); p.setBrush(QBrush(SHADOW_COLOR))
        p.drawEllipse(QPointF(0, 0), c.diameter * 0.45, c.diameter * 0.12)
        p.restore()

        scale_x = max(0.08, abs(math.cos(c.angle)))
        p.save(); p.translate(c.x, c.y); p.scale(scale_x, 1.0)
        r = c.diameter / 2
        grad = QRadialGradient(-r*0.3, -r*0.3, r*1.6)
        grad.setColorAt(0.0, QColor("#fff0b8"))
        grad.setColorAt(0.3, QColor("#f7d14a"))
        grad.setColorAt(0.7, QColor("#a87420"))
        grad.setColorAt(1.0, QColor("#6a4818"))
        p.setBrush(QBrush(grad))
        p.setPen(QPen(QColor("#2a1810"), max(1.0, c.diameter*0.03)))
        p.drawEllipse(QPointF(0, 0), r, r)
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(255,240,180,76), 1))
        p.drawEllipse(QPointF(0, 0), r*0.93, r*0.93)

        hole = c.diameter * 0.36
        p.setBrush(QBrush(QColor("#1a1410")))
        p.setPen(QPen(QColor("#2a1810"), max(1.0, c.diameter*0.03)))
        p.drawRect(int(-hole/2), int(-hole/2), int(hole), int(hole))

        font = QFont("Noto Serif SC"); font.setBold(True); font.setPixelSize(int(c.diameter*0.19))
        p.setFont(font); p.setPen(QColor("#1a1008"))
        off = c.diameter * 0.34
        chars = ("永", "乐", "通", "宝")
        positions = [(0, -off), (0, off), (off, 0), (-off, 0)]
        fm = p.fontMetrics()
        for (dx, dy), ch in zip(positions, chars):
            tw = fm.horizontalAdvance(ch); th = fm.ascent() - fm.descent()
            p.drawText(QPointF(dx - tw/2, dy + th/2), ch)
        p.restore()

    def _draw_xuanhe(self, p: QPainter, c: Coin) -> None:
        """宣和通宝 · 瘦金体温润古金。"""
        # Shadow
        p.save(); p.translate(c.x, c.y + c.diameter*0.55)
        p.setPen(Qt.NoPen); p.setBrush(QBrush(SHADOW_COLOR))
        p.drawEllipse(QPointF(0, 0), c.diameter*0.45, c.diameter*0.12)
        p.restore()

        scale_x = max(0.08, abs(math.cos(c.angle)))
        p.save(); p.translate(c.x, c.y); p.scale(scale_x, 1.0)
        r = c.diameter / 2
        grad = QRadialGradient(-r*0.3, -r*0.3, r*1.5)
        grad.setColorAt(0.0, QColor("#e8c880"))
        grad.setColorAt(0.35, QColor("#b88838"))
        grad.setColorAt(0.75, QColor("#6a4818"))
        grad.setColorAt(1.0, QColor("#3a2810"))
        p.setBrush(QBrush(grad))
        p.setPen(QPen(QColor("#2a1810"), max(1.0, c.diameter*0.025)))
        p.drawEllipse(QPointF(0, 0), r, r)

        hole = c.diameter * 0.36
        p.setBrush(QBrush(QColor("#1a1410")))
        p.setPen(QPen(QColor("#2a1810"), max(1.0, c.diameter*0.025)))
        p.drawRect(int(-hole/2), int(-hole/2), int(hole), int(hole))

        # 瘦金体风味：italic
        font = QFont("Noto Serif SC"); font.setItalic(True); font.setPixelSize(int(c.diameter*0.20))
        p.setFont(font); p.setPen(QColor("#1a1008"))
        off = c.diameter * 0.34
        chars = ("宣", "和", "通", "宝")
        positions = [(0, -off), (0, off), (off, 0), (-off, 0)]
        fm = p.fontMetrics()
        for (dx, dy), ch in zip(positions, chars):
            tw = fm.horizontalAdvance(ch); th = fm.ascent() - fm.descent()
            p.drawText(QPointF(dx - tw/2, dy + th/2), ch)
        p.restore()

    def _draw_longyang(self, p: QPainter, c: Coin) -> None:
        """壹圓龙洋 · 齿边无孔 · 中央大字 + ✦ + 桂叶。"""
        p.save(); p.translate(c.x, c.y + c.diameter*0.55)
        p.setPen(Qt.NoPen); p.setBrush(QBrush(SHADOW_COLOR))
        p.drawEllipse(QPointF(0, 0), c.diameter*0.45, c.diameter*0.12)
        p.restore()

        scale_x = max(0.08, abs(math.cos(c.angle)))
        p.save(); p.translate(c.x, c.y); p.scale(scale_x, 1.0)
        r = c.diameter / 2

        grad = QRadialGradient(-r*0.3, -r*0.3, r*1.55)
        grad.setColorAt(0.0, QColor("#f8e8b8"))
        grad.setColorAt(0.4, QColor("#d4a838"))
        grad.setColorAt(0.85, QColor("#8a5818"))
        grad.setColorAt(1.0, QColor("#5a3810"))
        p.setBrush(QBrush(grad))
        p.setPen(QPen(QColor("#2a1810"), max(1.0, c.diameter*0.028)))
        p.drawEllipse(QPointF(0, 0), r, r)

        # 齿边 reeds
        p.setPen(QPen(QColor(42, 24, 16, 140), max(0.8, c.diameter*0.015)))
        for i in range(26):
            ang = math.tau * i / 26
            rx1 = math.cos(ang) * r * 0.98
            ry1 = math.sin(ang) * r * 0.98
            rx2 = math.cos(ang) * r * 0.88
            ry2 = math.sin(ang) * r * 0.88
            p.drawLine(QPointF(rx1, ry1), QPointF(rx2, ry2))

        # 内圈
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(42,24,16,150), 1))
        p.drawEllipse(QPointF(0, 0), r*0.8, r*0.8)

        # 中央 壹圓 大字
        font = QFont("Noto Serif SC"); font.setBold(True); font.setPixelSize(int(c.diameter*0.35))
        p.setFont(font); p.setPen(QColor("#1a1008"))
        fm = p.fontMetrics()
        for ch, dy in (("壹", -c.diameter*0.15), ("圓", c.diameter*0.2)):
            tw = fm.horizontalAdvance(ch); th = fm.ascent() - fm.descent()
            p.drawText(QPointF(-tw/2, dy + th/2), ch)

        # 顶部 ✦ ✦
        star_font = QFont("Fraunces"); star_font.setPixelSize(int(c.diameter*0.13))
        p.setFont(star_font); p.setPen(QColor(26, 16, 8, 200))
        p.drawText(QPointF(-c.diameter*0.18, -c.diameter*0.32), "✦")
        p.drawText(QPointF(c.diameter*0.08, -c.diameter*0.32), "✦")
        p.restore()

    def _draw_modern_yuan(self, p: QPainter, c: Coin) -> None:
        """现代 ¥ 金币 · 抛光强光 + 大号 ¥。"""
        p.save(); p.translate(c.x, c.y + c.diameter*0.55)
        p.setPen(Qt.NoPen); p.setBrush(QBrush(SHADOW_COLOR))
        p.drawEllipse(QPointF(0, 0), c.diameter*0.45, c.diameter*0.12)
        p.restore()

        scale_x = max(0.08, abs(math.cos(c.angle)))
        p.save(); p.translate(c.x, c.y); p.scale(scale_x, 1.0)
        r = c.diameter / 2

        grad = QRadialGradient(-r*0.35, -r*0.4, r*1.6)
        grad.setColorAt(0.0, QColor("#fff4c8"))
        grad.setColorAt(0.25, QColor("#f7d14a"))
        grad.setColorAt(0.6, QColor("#c89434"))
        grad.setColorAt(0.9, QColor("#7a5418"))
        grad.setColorAt(1.0, QColor("#3a2810"))
        p.setBrush(QBrush(grad))
        p.setPen(QPen(QColor("#3a2810"), max(1.0, c.diameter*0.028)))
        p.drawEllipse(QPointF(0, 0), r, r)

        # Inner ring
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(255, 248, 200, 100), 1))
        p.drawEllipse(QPointF(0, 0), r*0.89, r*0.89)

        # Big ¥
        font = QFont("Fraunces"); font.setPixelSize(int(c.diameter*0.8)); font.setWeight(QFont.Medium)
        p.setFont(font); p.setPen(QColor("#2a1810"))
        fm = p.fontMetrics()
        tw = fm.horizontalAdvance("¥"); th = fm.ascent() - fm.descent()
        p.drawText(QPointF(-tw/2, th/2 + c.diameter*0.06), "¥")

        # Highlight
        p.save()
        p.translate(-r*0.35, -r*0.45); p.rotate(-28)
        p.setPen(Qt.NoPen); p.setBrush(QColor(255, 248, 220, 102))
        p.drawEllipse(QPointF(0, 0), r*0.5, r*0.24)
        p.restore()

        p.restore()
```

- [ ] **Step 2: 加一个统一的 dispatch：_draw_coin_by_style**

在 `_draw_modern_yuan` 之后追加：

```python
    def _draw_coin_by_style(self, p: QPainter, c: Coin, style: str) -> None:
        fn = {
            "kaiyuan": self._draw_kaiyuan,
            "yongle": self._draw_yongle,
            "xuanhe": self._draw_xuanhe,
            "longyang": self._draw_longyang,
            "modern_yuan": self._draw_modern_yuan,
        }.get(style, self._draw_kaiyuan)
        fn(p, c)
```

- [ ] **Step 3: 临时让 paintEvent 循环所有 5 种样式验证**

临时改 `paintEvent` 里金币循环为（仅用于目测验证 5 款）：

```python
        styles = ["kaiyuan", "yongle", "xuanhe", "longyang", "modern_yuan"]
        for i, c in enumerate(self.coins):
            self._draw_coin_by_style(p, c, styles[i % 5])
```

- [ ] **Step 4: 跑一下**

```bash
python coin_rain.py --rain
```

Expected: 5 款金币交错下落，都能看到。如有个别渲染异常，记录下来、回到对应 _draw_ 调整。

- [ ] **Step 5: 恢复 paintEvent 暂用 config 的 coin_style 决定**

把临时循环改为：

```python
        for c in self.coins:
            self._draw_coin_by_style(p, c, self._coin_style)
```

并在 `CoinRainWindow.__init__` 里初始化：

```python
        self._coin_style = "kaiyuan"
        self._mixed = False
        self._mix_styles = ["kaiyuan"]
```

并加 setter：

```python
    def set_coin_style(self, style: str, mixed: bool = False) -> None:
        self._coin_style = style
        self._mixed = mixed
        if mixed:
            self._mix_styles = ["kaiyuan", "yongle", "xuanhe", "longyang", "modern_yuan"]
```

把 `_draw_coin_by_style` 调用改为：

```python
        for c in self.coins:
            style = random.choice(self._mix_styles) if self._mixed else self._coin_style
            self._draw_coin_by_style(p, c, style)
```

（或在 `_make_coin` 里直接为每枚 Coin 预选 style 存到 dataclass，避免 paintEvent 里每帧随机；改进留作 later。当前方案按 Coin 随机每帧 OK 因为视觉上不明显；若闪烁严重再修。）

**更稳健的做法**：给 `Coin` dataclass 加 `style_id: str` 字段，在 `_make_coin` 时抽一次：

```python
@dataclass
class Coin:
    x: float
    y: float
    vx: float
    vy: float
    diameter: float
    angle: float
    angular_v: float
    style_id: str = "kaiyuan"
```

在 `_make_coin` 末尾：

```python
        coin.style_id = random.choice(self._mix_styles) if self._mixed else self._coin_style
        return coin
```

（注：需要把 `return Coin(...)` 拆成先赋值再返回。）

paintEvent 改成：

```python
        for c in self.coins:
            self._draw_coin_by_style(p, c, c.style_id)
```

- [ ] **Step 6: Commit**

```bash
git add rain_window.py
git commit -m "feat(rain): add yongle/xuanhe/longyang/modern_yuan coin styles + mixed mode"
```

### Task 3.8: coin_rain.py 主流程对接 config 的金币样式和混合

**Files:**
- Modify: `coin_rain.py`

- [ ] **Step 1: 在 _run_rain 里读 cfg 的样式并传入**

把 `coin_rain.py` 的 `_run_rain` 里：

```python
    w = CoinRainWindow()
    w.set_amount(amount, label)
    w.start()
```

**替换**为：

```python
    w = CoinRainWindow()
    w.set_amount(amount, label)
    if cfg is not None:
        w.set_coin_style(cfg.coin_style, cfg.mixed_coins)
    w.start()
```

- [ ] **Step 2: 在 SetupWindow 里加一个金币样式选择行（阶段 3 补）**

这个 UI 字段先简化：在 SetupWindow 暂不加（YAGNI，默认就是 kaiyuan）；若未来要用户切换，再补一行 tile 选择。本 task 不加。

- [ ] **Step 3: 手动验证**

```bash
python coin_rain.py --rain
```

Expected: 按 config.coin_style 渲染（默认 kaiyuan）；若手动改 config.json 里 `mixed_coins=true`，5 款混合下落。

- [ ] **Step 4: Commit**

```bash
git add coin_rain.py
git commit -m "feat: propagate coin_style and mixed_coins from config to RainWindow"
```

### Task 3.9: ManageWindow 下次预告金额按 nth/total 算

**Files:**
- Modify: `config_window.py`

- [ ] **Step 1: 改 _next_run_text 用 _compute_amount**

在 `config_window.py` 顶部追加：

```python
from rain_window import _compute_amount
```

改 `_next_run_text`：

```python
    def _next_run_text(self) -> str:
        if self._status.next_run is None:
            return "未注册"
        t = self._status.next_run.strftime("%H:%M")
        if self._cfg.mode == "single":
            amount = self._cfg.income
        else:
            # 找出 next_run 是 N 次里的第几次
            times = _distribute_times(self._cfg.first_time, self._cfg.last_time, self._cfg.count)
            target = t
            try:
                nth = times.index(target) + 1
            except ValueError:
                nth = 1
            amount = _compute_amount(income=self._cfg.income, nth=nth, total=self._cfg.count)
        return f"下次 · {t} · 预计到账 ¥{amount}"
```

在顶部 import 追加：

```python
from scheduler import _distribute_times
```

- [ ] **Step 2: 手动验证**

改 config 为 multi 模式 N=3、first=09:00、last=17:00；重新保存 → ManageWindow 查看下次预告条的金额是否按 nth 累计（比如当前 10 点，下次应该是 13:00 显示 ¥200）。

- [ ] **Step 3: Commit**

```bash
git add config_window.py
git commit -m "feat(ui): compute next-run amount based on nth/total in ManageWindow"
```

### Task 3.10: 阶段 3 checkpoint + build.bat 再跑一次 + 全量 checklist

**Files:**
（无代码变更）

- [ ] **Step 1: 打包**

```bash
./build.bat
```

Expected: 构建成功，exe 约 45–50 MB。

- [ ] **Step 2: 干净 VM（或本机）上完整 checklist**

- [ ] 删除本机现有 config.json + schtasks 任务
- [ ] `dist/coin_rain.exe` 双击 → Setup 打开
- [ ] 填 ¥300 / 中雨 / 每天一次 / 17:00 → 保存并启用
- [ ] 再双击 exe → Manage 打开，摘要正确、开关为启用
- [ ] `schtasks /Query /TN CoinRainDaily` 任务存在、Enabled
- [ ] `schtasks /Run /TN CoinRainDaily` 立即触发一次 → 动画：先 1s 大字 → 开元通宝金币 → 音效
- [ ] Manage 开关切到"停用"→ `schtasks /Query` Enabled=Disabled
- [ ] 切回启用
- [ ] "修改配置"→ 改为多次模式 first=09:00 last=11:00 count=3 → 保存
- [ ] `schtasks /Query | findstr CoinRain` 看到 3 个任务 CoinRainDaily_1/_2/_3
- [ ] 立即跑一次 `schtasks /Run /TN CoinRainDaily_1` → 看到 "当前已到账 ¥100"
- [ ] `schtasks /Run /TN CoinRainDaily_3` → 看到 "今日到账 ¥300"
- [ ] 最后：手动改 `%APPDATA%\CoinRain\config.json` 把 mixed_coins 改 true → 立即触发 → 5 种金币混合下落
- [ ] `pytest tests/ -v` 全绿（14 passed）

- [ ] **Step 3: Tag 阶段 3**

```bash
git tag stage-3-complete
```

- [ ] **Step 4: 更新 TODO 文件记录进度**

改 `docs/2026-04-16-coin-rain-todo.md` 末尾追加：

```
✅ 已完成：2026-04-XX 阶段 1 到账大字（参考 stage-1-complete）
✅ 已完成：2026-04-XX 阶段 2 配置与管理 UI（参考 stage-2-complete）
✅ 已完成：2026-04-XX 阶段 3 多次触发 + 任务计划 + 5 款金币（参考 stage-3-complete）
```

```bash
git add docs/2026-04-16-coin-rain-todo.md
git commit -m "docs: mark all 3 stages complete in coin-rain todo"
```

---

## 附录 A：变更影响文件清单

| 文件 | 动作 |
|---|---|
| `coin_rain.py` | 重写为入口派发 |
| `rain_window.py` | 新建，承载 CoinRainWindow 和 5 款金币绘制 |
| `config.py` | 新建，Config dataclass + 路径 |
| `config_window.py` | 新建，Setup + Manage UI |
| `scheduler.py` | 新建，schtasks 封装 |
| `fonts.py` | 新建，字体加载 |
| `style.qss` | 新建，UI 样式表 |
| `tests/__init__.py` | 新建 |
| `tests/test_logic.py` | 新建，3+ 单元测试 |
| `assets/fonts/*.ttf` | 新建，字体资源 |
| `build.bat` | 追加 --add-data 条目 |
| `requirements.txt` | 追加 pytest |
| `.gitignore` | 新建 |
| `install_schedule.ps1` | 保留不动（命令行备用） |
| `uninstall_schedule.ps1` | 保留不动 |

## 附录 B：可能的 pitfall

1. **schtasks `/TR` 参数里含空格**：必须把 exe 路径用 `"` 包起来，命令行 arg 在引号外
2. **schtasks `/ST` 时间格式**：必须 `HH:MM`（24h），不能带秒
3. **QSS 里 `#tile:checked` 伪类**：需要 `QPushButton.setCheckable(True)` 才有效
4. **QLineEdit property 生效**：改 property 后需要 `unpolish/polish` 让样式重算
5. **PyInstaller --onefile 的 _MEIPASS**：每次运行解压到新临时目录，路径不稳定；但 `resource_path()` 会重算，没问题
6. **字体加载失败**：`addApplicationFont` 返回 -1，QSS 中 `font-family` 会 fallback 到系统 serif；测试时在无字体机器上验证
7. **多次模式下手动改 config.json 到不合法值**：Config.load 不校验字段合法性（TypeError 被 catch 回 None，会被当首次配置）；用户绕过 UI 的风险可接受
8. **`schtasks /Query` 在中文 Windows 上输出列名可能是中文**：`"Scheduled Task State"` 变成 `"计划任务状态"` → 解析失败。当前 scheduler.status() 只认英文。如果遇到可改为 `locale.getdefaultlocale()` 判断后用中文 header，或改用 `/FO CSV` 格式更稳

---

**Plan complete and saved to `docs/superpowers/plans/2026-04-16-coin-rain-config-ui.md`. 两种执行方式：**

1. **Subagent-Driven（推荐）** — 每个 Task 派发一个独立 subagent，我在两 Task 之间 review
2. **Inline Execution** — 本会话内逐 Task 执行，checkpoint 时你 review

**选哪个？**
