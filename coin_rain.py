"""金币雨桌面彩蛋 —— 透明置顶窗口，30-50 枚金币下落，约 2.5 秒。"""
from __future__ import annotations

import math
import os
import random
import sys
import winsound
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QPointF, QElapsedTimer
from PySide6.QtGui import QColor, QGuiApplication, QPainter, QRadialGradient, QPen, QFont, QBrush
from PySide6.QtWidgets import QApplication, QWidget

# ================= 可调参数（改这里即可） =================
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
# =======================================================


def resource_path(rel: str) -> Path:
    """在开发态和 PyInstaller 打包态都能找到 assets/ 下的资源。"""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return base / rel


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
    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
            | Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        screen_geom = QGuiApplication.primaryScreen().geometry()
        self.setGeometry(screen_geom)
        self._screen_w = screen_geom.width()
        self._screen_h = screen_geom.height()

        self.coins: list[Coin] = []
        self._total_to_spawn = random.randint(COIN_COUNT_MIN, COIN_COUNT_MAX)
        self._spawned = 0
        self._batch_index = 0

        self._elapsed = QElapsedTimer()
        self._last_tick_ms: int | None = None

        self.timer = QTimer(self)
        self.timer.setInterval(int(1000 / FPS))
        self.timer.timeout.connect(self._tick)

        self.safety_timer = QTimer(self)
        self.safety_timer.setSingleShot(True)
        self.safety_timer.timeout.connect(QApplication.quit)
        self.safety_timer.start(TIMEOUT_SAFETY_MS)

        self._setup_sound()

    def _setup_sound(self) -> None:
        wav_path = resource_path("assets/coin_drop.wav")
        self._wav_path: str | None = str(wav_path) if wav_path.exists() else None

    def start(self) -> None:
        self.show()
        self._elapsed.start()
        if self._wav_path:
            # winsound 是 Windows 内置 API，不依赖任何 Qt 多媒体插件，
            # PyInstaller 打包后必然可用。SND_ASYNC 让播放不阻塞 GUI 线程。
            winsound.PlaySound(self._wav_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        self._spawn_batch()
        self.timer.start()

    def _spawn_batch(self) -> None:
        if self._batch_index >= BATCH_COUNT:
            return
        remaining_batches = BATCH_COUNT - self._batch_index
        remaining_coins = self._total_to_spawn - self._spawned
        this_batch = math.ceil(remaining_coins / remaining_batches)
        for _ in range(this_batch):
            self.coins.append(self._make_coin())
            self._spawned += 1
        self._batch_index += 1
        if self._batch_index < BATCH_COUNT:
            QTimer.singleShot(BATCH_INTERVAL_MS, self._spawn_batch)

    def _make_coin(self) -> Coin:
        d = random.uniform(COIN_DIAMETER_MIN, COIN_DIAMETER_MAX)
        return Coin(
            x=random.uniform(0, self._screen_w),
            y=-60.0 - random.uniform(0, 40),
            vx=random.uniform(-VX_INIT_ABS_MAX, VX_INIT_ABS_MAX),
            vy=random.uniform(VY_INIT_MIN, VY_INIT_MAX),
            diameter=d,
            angle=random.uniform(0, math.tau),
            angular_v=random.uniform(ROT_SPEED_MIN, ROT_SPEED_MAX) * random.choice((-1, 1)),
        )

    def _tick(self) -> None:
        now = self._elapsed.elapsed()
        if self._last_tick_ms is None:
            dt = 1.0 / FPS
        else:
            dt = (now - self._last_tick_ms) / 1000.0
        self._last_tick_ms = now

        alive: list[Coin] = []
        for c in self.coins:
            c.vy += GRAVITY * dt
            c.x += c.vx * dt
            c.y += c.vy * dt
            c.angle += c.angular_v * dt
            if c.y - c.diameter / 2 <= self._screen_h + 10:
                alive.append(c)
        self.coins = alive

        all_spawned = self._spawned >= self._total_to_spawn
        if all_spawned and not self.coins:
            QApplication.quit()
            return

        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)
        for c in self.coins:
            self._draw_coin(p, c)
        p.end()

    def _draw_coin(self, p: QPainter, c: Coin) -> None:
        # 阴影
        p.save()
        p.translate(c.x, c.y + c.diameter * 0.55)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(SHADOW_COLOR))
        p.drawEllipse(QPointF(0, 0), c.diameter * 0.45, c.diameter * 0.12)
        p.restore()

        # 金币本体（水平缩放模拟旋转翻面）
        scale_x = abs(math.cos(c.angle))
        if scale_x < 0.08:
            scale_x = 0.08
        p.save()
        p.translate(c.x, c.y)
        p.scale(scale_x, 1.0)

        r = c.diameter / 2
        grad = QRadialGradient(0, 0, r)
        grad.setColorAt(0.0, COIN_FILL_CENTER)
        grad.setColorAt(1.0, COIN_FILL_EDGE)
        p.setBrush(QBrush(grad))
        p.setPen(QPen(COIN_STROKE, 1))
        p.drawEllipse(QPointF(0, 0), r, r)

        font = QFont()
        font.setBold(True)
        font.setPixelSize(int(c.diameter * 0.55))
        p.setFont(font)
        p.setPen(COIN_SYMBOL_COLOR)
        fm = p.fontMetrics()
        tw = fm.horizontalAdvance(COIN_SYMBOL)
        th = fm.ascent() - fm.descent()
        p.drawText(QPointF(-tw / 2, th / 2), COIN_SYMBOL)
        p.restore()


def main() -> int:
    os.environ.setdefault("QT_LOGGING_RULES", "*.debug=false;qt.qpa.*=false")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    w = CoinRainWindow()
    w.start()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
