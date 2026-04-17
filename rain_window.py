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
COIN_DIAMETER_MIN = 48
COIN_DIAMETER_MAX = 76
GRAVITY = 550.0
VY_INIT_MIN = 120.0
VY_INIT_MAX = 240.0
VX_INIT_ABS_MAX = 80.0
ROT_SPEED_MIN = 3.0
ROT_SPEED_MAX = 10.0
FPS = 60
TIMEOUT_SAFETY_MS = 12000

COIN_FILL_CENTER = QColor("#fff3a8")  # 更亮
COIN_FILL_EDGE = QColor("#e8ac1a")    # 更饱和
COIN_STROKE = QColor("#8B6914")
COIN_SYMBOL = "¥"
COIN_SYMBOL_COLOR = QColor("#3a2408")  # 更深，对比更强
SHADOW_COLOR = QColor(0, 0, 0, 76)

# 开元通宝配色（鲜亮黄金色，不做旧）
KY_FILL_CENTER = QColor("#fff2a8")   # 高光中心，近乎白金
KY_FILL_MID = QColor("#f7c84a")      # 鲜亮金色
KY_FILL_EDGE = QColor("#b8852a")     # 温暖铜金（不发黑）
KY_STROKE = QColor("#5a3a10")
KY_TEXT = QColor("#3a1a05")          # 深棕黑，对比度够
KY_HOLE_FILL = QColor("#2a1410")
KY_CHARS = ("开", "元", "通", "宝")  # 上 / 下 / 右 / 左 顺序
KY_TEXT_SIZE_RATIO = 0.28            # 字号占直径比例（原 0.19 太小）
KY_TEXT_OFFSET_RATIO = 0.36          # 字到中心距离

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
COIN_START_DELAY_MS = 1000  # 金币开始下落的延迟
# ============================================


def _compute_amount(*, income: int, nth: int, total: int) -> int:
    """多次/单次模式下本次触发要显示的到账金额。

    - nth ∈ [1, total]；nth == total 时返回 income（闭合）
    - 否则按整数元四舍五入到 round(income * nth / total)
    """
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

        # 到账大字状态
        self._target_amount = 300  # 阶段 1 硬编码；阶段 2/3 从 config/argv 读
        self._current_amount = 0.0
        self._label_text = "今 日 到 账"
        self._coin_style = "kaiyuan"
        self._mixed = False
        self._mix_styles = ["kaiyuan"]

    def set_amount(self, amount: int, label: str) -> None:
        """在 start() 之前调用，设置本次到账大字的目标值和副标。"""
        self._target_amount = amount
        self._label_text = label

    def set_coin_style(self, style: str, mixed: bool = False) -> None:
        """设置金币样式。mixed=True 时从全部 5 款中均匀随机抽取。"""
        self._coin_style = style
        self._mixed = mixed
        if mixed:
            self._mix_styles = ["kaiyuan", "yongle", "xuanhe", "longyang", "modern_yuan"]
        else:
            self._mix_styles = [style]

    def _setup_sound(self) -> None:
        wav_path = resource_path("assets/coin_drop.wav")
        self._wav_path: str | None = str(wav_path) if wav_path.exists() else None

    def start(self) -> None:
        self.show()
        self._elapsed.start()
        # 先 1 秒显示 count-up 大字，之后才开始落币 + 音效
        QTimer.singleShot(COIN_START_DELAY_MS, self._start_coins)
        self.timer.start()

    def _start_coins(self) -> None:
        if self._wav_path:
            winsound.PlaySound(self._wav_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
        self._spawn_batch()

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

        # count-up 大字推进
        if now <= COUNTUP_DURATION_MS:
            progress = now / COUNTUP_DURATION_MS
            eased = 1 - (1 - progress) ** 3  # ease-out cubic
            self._current_amount = eased * self._target_amount
        else:
            self._current_amount = float(self._target_amount)

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

        # 大字完成 + 所有币落下 + 无残留 = 退出
        all_spawned = self._spawned >= self._total_to_spawn
        after_countup = now >= COUNTUP_DURATION_MS
        if all_spawned and not self.coins and after_countup:
            QApplication.quit()
            return

        self.update()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self._draw_amount(p)
        for c in self.coins:
            style = random.choice(self._mix_styles) if self._mixed else self._coin_style
            self._draw_coin_by_style(p, c, style)
        p.end()

    def _draw_coin_by_style(self, p: QPainter, c: Coin, style: str) -> None:
        fn = {
            "kaiyuan": self._draw_kaiyuan,
            "yongle": self._draw_yongle,
            "xuanhe": self._draw_xuanhe,
            "longyang": self._draw_longyang,
            "modern_yuan": self._draw_coin,  # 复用原来的 ¥ 绘制
        }.get(style, self._draw_kaiyuan)
        fn(p, c)

    def _draw_kaiyuan(self, p: QPainter, c: Coin) -> None:
        """开元通宝 · 鲜亮金色 · 方孔圆钱。"""
        # 阴影
        p.save()
        p.translate(c.x, c.y + c.diameter * 0.55)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(SHADOW_COLOR))
        p.drawEllipse(QPointF(0, 0), c.diameter * 0.45, c.diameter * 0.12)
        p.restore()

        scale_x = max(0.08, abs(math.cos(c.angle)))
        p.save()
        p.translate(c.x, c.y)
        p.scale(scale_x, 1.0)
        r = c.diameter / 2

        grad = QRadialGradient(-r * 0.3, -r * 0.3, r * 1.5)
        grad.setColorAt(0.0, KY_FILL_CENTER)
        grad.setColorAt(0.45, KY_FILL_MID)
        grad.setColorAt(1.0, KY_FILL_EDGE)
        p.setBrush(QBrush(grad))
        p.setPen(QPen(KY_STROKE, max(1.0, c.diameter * 0.02)))
        p.drawEllipse(QPointF(0, 0), r, r)

        # 内圈
        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(KY_STROKE, 1))
        p.drawEllipse(QPointF(0, 0), r * 0.92, r * 0.92)

        # 方孔
        hole = c.diameter * 0.32  # 缩小孔，给字让出空间
        p.setBrush(QBrush(KY_HOLE_FILL))
        p.setPen(QPen(KY_STROKE, max(1.0, c.diameter * 0.025)))
        p.drawRect(int(-hole / 2), int(-hole / 2), int(hole), int(hole))

        # 4 字：开 元 通 宝（上 下 右 左）—— 字号和偏移都加大
        font = QFont("Noto Serif SC")
        font.setPixelSize(int(c.diameter * KY_TEXT_SIZE_RATIO))
        font.setBold(True)
        p.setFont(font)
        p.setPen(KY_TEXT)
        off = c.diameter * KY_TEXT_OFFSET_RATIO
        positions = [(0, -off), (0, off), (off, 0), (-off, 0)]
        fm = p.fontMetrics()
        for (dx, dy), ch in zip(positions, KY_CHARS):
            tw = fm.horizontalAdvance(ch)
            th = fm.ascent() - fm.descent()
            p.drawText(QPointF(dx - tw / 2, dy + th / 2), ch)

        # 高光
        p.save()
        p.translate(-r * 0.35, -r * 0.4)
        p.rotate(-25)
        p.setPen(Qt.NoPen)
        p.setBrush(QColor(255, 255, 220, 110))  # 高光更亮
        p.drawEllipse(QPointF(0, 0), r * 0.5, r * 0.24)
        p.restore()

        p.restore()

    def _draw_yongle(self, p: QPainter, c: Coin) -> None:
        """永乐通宝 · 鎏金亮面 + 方孔。"""
        p.save()
        p.translate(c.x, c.y + c.diameter * 0.55)
        p.setPen(Qt.NoPen); p.setBrush(QBrush(SHADOW_COLOR))
        p.drawEllipse(QPointF(0, 0), c.diameter * 0.45, c.diameter * 0.12)
        p.restore()

        scale_x = max(0.08, abs(math.cos(c.angle)))
        p.save(); p.translate(c.x, c.y); p.scale(scale_x, 1.0)
        r = c.diameter / 2

        grad = QRadialGradient(-r*0.3, -r*0.3, r*1.6)
        grad.setColorAt(0.0, QColor("#fffad8"))   # 高光中心
        grad.setColorAt(0.35, QColor("#ffdc5a"))  # 鲜亮金
        grad.setColorAt(0.75, QColor("#c88c22"))  # 温金边缘
        grad.setColorAt(1.0, QColor("#8a5818"))
        p.setBrush(QBrush(grad))
        p.setPen(QPen(QColor("#5a3810"), max(1.0, c.diameter*0.03)))
        p.drawEllipse(QPointF(0, 0), r, r)

        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(255, 250, 200, 130), 1))
        p.drawEllipse(QPointF(0, 0), r*0.92, r*0.92)

        hole = c.diameter * 0.32
        p.setBrush(QBrush(QColor("#1a1410")))
        p.setPen(QPen(QColor("#5a3810"), max(1.0, c.diameter*0.03)))
        p.drawRect(int(-hole/2), int(-hole/2), int(hole), int(hole))

        font = QFont("Noto Serif SC"); font.setBold(True); font.setPixelSize(int(c.diameter*0.28))
        p.setFont(font); p.setPen(QColor("#2a1408"))
        off = c.diameter * 0.36
        chars = ("永", "乐", "通", "宝")
        positions = [(0, -off), (0, off), (off, 0), (-off, 0)]
        fm = p.fontMetrics()
        for (dx, dy), ch in zip(positions, chars):
            tw = fm.horizontalAdvance(ch); th = fm.ascent() - fm.descent()
            p.drawText(QPointF(dx - tw/2, dy + th/2), ch)

        # 高光
        p.save()
        p.translate(-r*0.35, -r*0.4); p.rotate(-28)
        p.setPen(Qt.NoPen); p.setBrush(QColor(255, 255, 230, 120))
        p.drawEllipse(QPointF(0, 0), r*0.5, r*0.24)
        p.restore()
        p.restore()

    def _draw_xuanhe(self, p: QPainter, c: Coin) -> None:
        """宣和通宝 · 瘦金体明亮古金。"""
        p.save(); p.translate(c.x, c.y + c.diameter*0.55)
        p.setPen(Qt.NoPen); p.setBrush(QBrush(SHADOW_COLOR))
        p.drawEllipse(QPointF(0, 0), c.diameter*0.45, c.diameter*0.12)
        p.restore()

        scale_x = max(0.08, abs(math.cos(c.angle)))
        p.save(); p.translate(c.x, c.y); p.scale(scale_x, 1.0)
        r = c.diameter / 2
        grad = QRadialGradient(-r*0.3, -r*0.3, r*1.5)
        grad.setColorAt(0.0, QColor("#ffec98"))   # 明亮浅金
        grad.setColorAt(0.4, QColor("#e8b838"))   # 鲜亮金
        grad.setColorAt(0.85, QColor("#a0701c"))  # 温金边
        grad.setColorAt(1.0, QColor("#6a4818"))
        p.setBrush(QBrush(grad))
        p.setPen(QPen(QColor("#4a2810"), max(1.0, c.diameter*0.025)))
        p.drawEllipse(QPointF(0, 0), r, r)

        hole = c.diameter * 0.32
        p.setBrush(QBrush(QColor("#1a1410")))
        p.setPen(QPen(QColor("#4a2810"), max(1.0, c.diameter*0.025)))
        p.drawRect(int(-hole/2), int(-hole/2), int(hole), int(hole))

        font = QFont("Noto Serif SC"); font.setItalic(True); font.setBold(True); font.setPixelSize(int(c.diameter*0.28))
        p.setFont(font); p.setPen(QColor("#2a1408"))
        off = c.diameter * 0.36
        chars = ("宣", "和", "通", "宝")
        positions = [(0, -off), (0, off), (off, 0), (-off, 0)]
        fm = p.fontMetrics()
        for (dx, dy), ch in zip(positions, chars):
            tw = fm.horizontalAdvance(ch); th = fm.ascent() - fm.descent()
            p.drawText(QPointF(dx - tw/2, dy + th/2), ch)

        p.save()
        p.translate(-r*0.35, -r*0.4); p.rotate(-25)
        p.setPen(Qt.NoPen); p.setBrush(QColor(255, 250, 210, 100))
        p.drawEllipse(QPointF(0, 0), r*0.5, r*0.24)
        p.restore()
        p.restore()

    def _draw_longyang(self, p: QPainter, c: Coin) -> None:
        """壹圓龙洋 · 齿边无孔 · 中央大字 + ✦ 装饰。"""
        p.save(); p.translate(c.x, c.y + c.diameter*0.55)
        p.setPen(Qt.NoPen); p.setBrush(QBrush(SHADOW_COLOR))
        p.drawEllipse(QPointF(0, 0), c.diameter*0.45, c.diameter*0.12)
        p.restore()

        scale_x = max(0.08, abs(math.cos(c.angle)))
        p.save(); p.translate(c.x, c.y); p.scale(scale_x, 1.0)
        r = c.diameter / 2

        grad = QRadialGradient(-r*0.3, -r*0.3, r*1.55)
        grad.setColorAt(0.0, QColor("#fff4c8"))
        grad.setColorAt(0.4, QColor("#f7c840"))  # 鲜亮金
        grad.setColorAt(0.85, QColor("#a87020"))
        grad.setColorAt(1.0, QColor("#6a4010"))
        p.setBrush(QBrush(grad))
        p.setPen(QPen(QColor("#4a2810"), max(1.0, c.diameter*0.028)))
        p.drawEllipse(QPointF(0, 0), r, r)

        # 齿边 reeds
        p.setPen(QPen(QColor(74, 40, 16, 180), max(0.8, c.diameter*0.015)))
        for i in range(26):
            ang = math.tau * i / 26
            rx1 = math.cos(ang) * r * 0.98
            ry1 = math.sin(ang) * r * 0.98
            rx2 = math.cos(ang) * r * 0.88
            ry2 = math.sin(ang) * r * 0.88
            p.drawLine(QPointF(rx1, ry1), QPointF(rx2, ry2))

        p.setBrush(Qt.NoBrush)
        p.setPen(QPen(QColor(74, 40, 16, 180), 1))
        p.drawEllipse(QPointF(0, 0), r*0.8, r*0.8)

        # 大字 壹圓 —— 字号从 0.35 提到 0.42
        font = QFont("Noto Serif SC"); font.setBold(True); font.setPixelSize(int(c.diameter*0.42))
        p.setFont(font); p.setPen(QColor("#2a1408"))
        fm = p.fontMetrics()
        for ch, dy in (("壹", -c.diameter*0.14), ("圓", c.diameter*0.22)):
            tw = fm.horizontalAdvance(ch); th = fm.ascent() - fm.descent()
            p.drawText(QPointF(-tw/2, dy + th/2), ch)

        star_font = QFont(); star_font.setPixelSize(int(c.diameter*0.15))
        p.setFont(star_font); p.setPen(QColor(42, 20, 8, 220))
        p.drawText(QPointF(-c.diameter*0.2, -c.diameter*0.32), "✦")
        p.drawText(QPointF(c.diameter*0.08, -c.diameter*0.32), "✦")

        # 高光
        p.save()
        p.translate(-r*0.35, -r*0.45); p.rotate(-28)
        p.setPen(Qt.NoPen); p.setBrush(QColor(255, 250, 220, 110))
        p.drawEllipse(QPointF(0, 0), r*0.5, r*0.24)
        p.restore()
        p.restore()

    def _draw_amount(self, p: QPainter) -> None:
        """绘制中央金色大字 + 下方中文副标。"""
        w = self._screen_w
        h = self._screen_h

        num_px = int(h * AMOUNT_SIZE_RATIO)
        label_px = int(h * LABEL_SIZE_RATIO)

        num_text = f"¥{int(round(self._current_amount))}"

        num_font = QFont(AMOUNT_FONT_FAMILY)
        num_font.setPixelSize(num_px)
        num_font.setWeight(QFont.Medium)

        p.setFont(num_font)
        fm = p.fontMetrics()
        tw = fm.horizontalAdvance(num_text)
        tx = (w - tw) / 2
        ty = h * 0.44 + fm.ascent() / 2

        # Glow 层：多次偏移绘制模拟发光
        p.save()
        p.setPen(AMOUNT_GLOW_COLOR)
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-3, 0), (3, 0)]:
            p.drawText(QPointF(tx + dx, ty + dy), num_text)
        p.restore()

        # Shadow
        p.save()
        p.setPen(AMOUNT_SHADOW_COLOR)
        p.drawText(QPointF(tx + 4, ty + 6), num_text)
        p.restore()

        # 主数字
        p.save()
        p.setPen(AMOUNT_COLOR)
        p.drawText(QPointF(tx, ty), num_text)
        p.restore()

        # 下方中文副标
        label_font = QFont(LABEL_FONT_FAMILY)
        label_font.setPixelSize(label_px)
        label_font.setWeight(QFont.Medium)
        label_font.setLetterSpacing(QFont.PercentageSpacing, 200)
        p.setFont(label_font)
        fm2 = p.fontMetrics()
        lw = fm2.horizontalAdvance(self._label_text)
        lx = (w - lw) / 2
        ly = ty + label_px * 2.2

        p.save()
        p.setPen(AMOUNT_SHADOW_COLOR)
        p.drawText(QPointF(lx + 2, ly + 2), self._label_text)
        p.restore()
        p.setPen(LABEL_COLOR)
        p.drawText(QPointF(lx, ly), self._label_text)

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
        font.setPixelSize(int(c.diameter * 0.70))  # ¥ 更大
        p.setFont(font)
        p.setPen(COIN_SYMBOL_COLOR)
        fm = p.fontMetrics()
        tw = fm.horizontalAdvance(COIN_SYMBOL)
        th = fm.ascent() - fm.descent()
        p.drawText(QPointF(-tw / 2, th / 2), COIN_SYMBOL)
        p.restore()
