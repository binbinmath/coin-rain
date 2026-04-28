"""金币雨主窗口（CoinRainWindow）+ 相关纯逻辑。

V2 升级：
- 6 张真实金币 PNG 随机混合下落（assets/coins/*.png）
- 雨势 4 档（light/medium/heavy/storm）控制数量/速度/时长
- 中央 count-up 大字配色对齐墨黑金主题
"""
from __future__ import annotations

import math
import random
import winsound
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QPointF, QElapsedTimer, QRectF, Signal
from PySide6.QtGui import QColor, QGuiApplication, QPainter, QPen, QFont, QBrush, QPixmap
from PySide6.QtWidgets import QWidget

from config import resource_path

# ================= 雨势参数 =================
#
# 物理模型：每枚金币从屏幕顶端"轻轻弹一下"再自然加速下落 ——
#   - 初速度 vy_init 取负值（向上弹起 30~80px）
#   - 之后受 gravity 拉回，速度越往下越大
# 这样观感像烧瓶里冒出泡泡：起步缓 → 中段提速 → 落到底已经很快
#
# vy_init: (lo, hi)  两个值都是负数，越负 = 弹得越高
# gravity: 像 px/s² 的"重力"。越大 = 加速越凶。

INTENSITY_PARAMS: dict[str, dict] = {
    "light":  {"count": (15, 25),   "duration_ms": 5500, "vy_init": (-160, -60), "gravity": 280, "batches": 5,  "interval_ms": 500},
    "medium": {"count": (30, 50),   "duration_ms": 6500, "vy_init": (-140, -50), "gravity": 360, "batches": 8,  "interval_ms": 380},
    "heavy":  {"count": (60, 90),   "duration_ms": 7500, "vy_init": (-120, -40), "gravity": 470, "batches": 10, "interval_ms": 320},
    "storm":  {"count": (100, 140), "duration_ms": 8500, "vy_init": (-100, -20), "gravity": 600, "batches": 12, "interval_ms": 260},
}

# ================= 视觉/物理常量 =================

# 直径范围扩大近一倍，且随机差异更大（原 36~64 → 现 60~140）
COIN_DIAMETER_MIN = 60
COIN_DIAMETER_MAX = 140
VX_INIT_ABS_MAX = 70.0
ROT_SPEED_MIN = 2.5
ROT_SPEED_MAX = 8.0
FPS = 60
TIMEOUT_SAFETY_MS = 16000

SHADOW_COLOR = QColor(0, 0, 0, 80)

# 金币 PNG 文件名（assets/coins/）—— 6 款混合
COIN_FILES = ("datang.png", "song.png", "ducat.png", "sovereign.png", "napoleon.png", "fine999.png")

# ============== 中央到账大字（墨黑金配色） ==============

AMOUNT_FONT_FAMILY = "Fraunces"
AMOUNT_COLOR = QColor("#f7dd8c")           # 鲜亮金（设计 token --B-gold-2）
AMOUNT_SHADOW_COLOR = QColor(0, 0, 0, 200)
AMOUNT_GLOW_COLOR = QColor(247, 221, 140, 130)
AMOUNT_SIZE_RATIO = 0.16                   # 数字高度 = 屏幕高 * 此值
LABEL_FONT_FAMILY = "Noto Serif SC"
LABEL_COLOR = QColor("#fff4cc")            # 高光暖白（设计 token --B-gold-1）
LABEL_SIZE_RATIO = 0.022

COUNTUP_DURATION_MS = 2200   # 老虎机总滚动时长（更慢、看得清每位 reel 在转）
COIN_START_DELAY_MS = 2400   # count-up 全部 settle 之后再下币
REEL_CYCLES = 3              # 每位 reel 在 settle 前会滚过多少整圈
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
    style_idx: int  # 0..len(COIN_FILES)-1


def _load_coin_pixmaps() -> list[QPixmap]:
    """加载所有可用的金币 PNG。失败的跳过；全失败时返回空列表（绘制时降级为金圆）。"""
    out: list[QPixmap] = []
    for name in COIN_FILES:
        p: Path = resource_path(f"assets/coins/{name}")
        if p.exists():
            pm = QPixmap(str(p))
            if not pm.isNull():
                out.append(pm)
    return out


class CoinRainWindow(QWidget):
    """全屏透明 + 置顶 + 鼠标穿透的金币雨动画窗口。

    完整跑完一次会 emit `finished`，同时 self.close() —— 父进程／父窗口决定要不要退出 app。
    """

    finished = Signal()

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
        self._intensity = "medium"
        self._params = INTENSITY_PARAMS["medium"]
        self._total_to_spawn = random.randint(*self._params["count"])
        self._spawned = 0
        self._batch_index = 0

        # 加载金币 PNG
        self._pixmaps: list[QPixmap] = _load_coin_pixmaps()

        self._elapsed = QElapsedTimer()
        self._last_tick_ms: int | None = None
        # 是否已经触发首次 paintEvent（用于把 _elapsed 挪到真正"用户看见第一帧"时再启动）
        self._first_paint_done = False
        self._finishing = False

        self.timer = QTimer(self)
        self.timer.setInterval(int(1000 / FPS))
        self.timer.timeout.connect(self._tick)

        self.safety_timer = QTimer(self)
        self.safety_timer.setSingleShot(True)
        self.safety_timer.timeout.connect(self._on_finish)

        self._setup_sound()

        # 到账大字状态（slot-machine 直接根据时间渲染，不再保存中间值）
        self._target_amount = 300
        self._label_text = "今 日 到 账"

        # spec v3 惊喜层：副标 / 视觉 overrides / 幸运币 / 金币模式
        self._subtitle_text: str | None = None    # None = 用 _label_text 兜底（向后兼容）
        self._flip_all = False
        self._size_scale = 1.0
        self._lucky_enabled = False
        self._coin_mode: int | None = None        # None = 混合（每枚独立）
        self._lucky_spawned = False               # 幸运币只生成一枚

    # ---- 对外配置 ----

    def set_amount(self, amount: int, label: str) -> None:
        """在 start() 之前调用，设置本次到账大字的目标值和副标。"""
        self._target_amount = amount
        self._label_text = label

    def set_intensity(self, intensity: str) -> None:
        """light / medium / heavy / storm。"""
        self._intensity = intensity if intensity in INTENSITY_PARAMS else "medium"
        self._params = INTENSITY_PARAMS[self._intensity]
        self._total_to_spawn = random.randint(*self._params["count"])

    def set_subtitle(self, text: str | None) -> None:
        """覆盖中央 ¥X 大字下方那行小字。在 start() 之前调用；None 走原 _label_text。"""
        self._subtitle_text = text

    def set_visual_overrides(self, overrides: dict) -> None:
        """spec §7.2：{} | {"flip_all": True} | {"size_scale": 2.0}"""
        self._flip_all = bool(overrides.get("flip_all", False))
        self._size_scale = float(overrides.get("size_scale", 1.0))

    def set_lucky_coin(self, enabled: bool) -> None:
        """spec §8：本场雨是否触发幸运币。"""
        self._lucky_enabled = bool(enabled)

    def set_coin_mode(self, mode: int | None) -> None:
        """spec §9：None=混合（每枚独立抽），int=全场固定 style_idx。"""
        self._coin_mode = mode

    # ---- 启动 ----

    def _setup_sound(self) -> None:
        slot = resource_path("assets/slot_spin.wav")
        coin = resource_path("assets/coin_drop.wav")
        self._slot_wav: str | None = str(slot) if slot.exists() else None
        self._coin_wav: str | None = str(coin) if coin.exists() else None

    def _play_slot(self) -> None:
        if self._slot_wav:
            winsound.PlaySound(self._slot_wav, winsound.SND_FILENAME | winsound.SND_ASYNC)

    def _play_coin(self) -> None:
        # winsound 同时只能放一个 —— 这次 PlaySound 会自动覆盖掉 slot 那段
        if self._coin_wav:
            winsound.PlaySound(self._coin_wav, winsound.SND_FILENAME | winsound.SND_ASYNC)

    def start(self) -> None:
        self.show()
        # 关键：_elapsed 不在这里启动 —— 留到首次 paintEvent 真正发生时再启动，
        # 这样用户第一眼看见的就是 count-up "0"，而不是错过了一大半。
        self.timer.start()

    def _start_coins(self) -> None:
        # 切到金币下落音，覆盖之前的 slot 转动声
        self._play_coin()
        # spec §8：幸运币（如果命中）—— 比最大币更大、慢、屏幕中上方掉下
        if self._lucky_enabled and self._pixmaps and not self._lucky_spawned:
            self._lucky_spawned = True
            d = COIN_DIAMETER_MAX * 1.8 * self._size_scale
            vy_lo, vy_hi = self._params["vy_init"]
            base_angle = random.uniform(0, math.tau)
            if self._flip_all:
                base_angle += math.pi
            self.coins.append(Coin(
                x=self._screen_w / 2 + random.uniform(-40, 40),
                y=-120,
                vx=random.uniform(-15, 15),
                vy=random.uniform(vy_lo, vy_hi) * 0.7,   # 慢一点多停留
                diameter=d,
                angle=base_angle,
                angular_v=random.uniform(ROT_SPEED_MIN, ROT_SPEED_MAX) * 0.6
                          * random.choice((-1, 1)),
                style_idx=random.randrange(len(self._pixmaps)),
            ))
        self._spawn_batch()

    def _spawn_batch(self) -> None:
        batches = self._params["batches"]
        if self._batch_index >= batches:
            return
        remaining_batches = batches - self._batch_index
        remaining_coins = self._total_to_spawn - self._spawned
        this_batch = math.ceil(remaining_coins / remaining_batches)
        for _ in range(this_batch):
            self.coins.append(self._make_coin())
            self._spawned += 1
        self._batch_index += 1
        if self._batch_index < batches:
            QTimer.singleShot(self._params["interval_ms"], self._spawn_batch)

    def _make_coin(self) -> Coin:
        # spec §7.2: 11/11 直径加倍（_size_scale）
        d = random.uniform(COIN_DIAMETER_MIN, COIN_DIAMETER_MAX) * self._size_scale
        vy_lo, vy_hi = self._params["vy_init"]
        # 出生在屏幕顶端附近（不再远在屏幕之上），让"先弹一下"的动作可见
        spawn_y = random.uniform(-d * 0.4, d * 0.6)
        # spec §9：固定 style_idx 还是每枚独立抽
        if self._pixmaps:
            if self._coin_mode is not None:
                style = self._coin_mode % len(self._pixmaps)
            else:
                style = random.randrange(len(self._pixmaps))
        else:
            style = 0
        # spec §7.2: 4/1 整场翻面 —— 起始 angle 加 π，让 cos 缩放从负向开始
        base_angle = random.uniform(0, math.tau)
        if self._flip_all:
            base_angle += math.pi
        return Coin(
            x=random.uniform(-d * 0.2, self._screen_w + d * 0.2),
            y=spawn_y,
            vx=random.uniform(-VX_INIT_ABS_MAX, VX_INIT_ABS_MAX),
            vy=random.uniform(vy_lo, vy_hi),  # 负值 = 起步向上一弹
            diameter=d,
            angle=base_angle,
            angular_v=random.uniform(ROT_SPEED_MIN, ROT_SPEED_MAX) * random.choice((-1, 1)),
            style_idx=style,
        )

    def _tick(self) -> None:
        # 还没首次 paint —— 啥都不做，只是请求 paint
        if not self._first_paint_done:
            self.update()
            return

        now = self._elapsed.elapsed()

        if self._last_tick_ms is None:
            dt = 1.0 / FPS
        else:
            dt = (now - self._last_tick_ms) / 1000.0
        self._last_tick_ms = now

        gravity = self._params["gravity"]
        alive: list[Coin] = []
        for c in self.coins:
            c.vy += gravity * dt
            c.x += c.vx * dt
            c.y += c.vy * dt
            c.angle += c.angular_v * dt
            # 越过屏幕底部才算"完事"；上方还在向上弹的留住
            if c.y - c.diameter / 2 <= self._screen_h + 10:
                alive.append(c)
        self.coins = alive

        all_spawned = self._spawned >= self._total_to_spawn
        after_countup = now >= COUNTUP_DURATION_MS
        if all_spawned and not self.coins and after_countup:
            self._on_finish()
            return

        self.update()

    def _on_finish(self) -> None:
        """动画完整跑完或安全 timeout 触发：停掉所有 timer，emit finished，关掉自己。"""
        if self._finishing:
            return
        self._finishing = True
        self.timer.stop()
        self.safety_timer.stop()
        # 主动停掉 winsound（可能还在尾巴上）—— 与 close 同时，避免父进程继续听到尾音
        try:
            winsound.PlaySound(None, winsound.SND_PURGE)
        except Exception:
            pass
        self.finished.emit()
        self.close()

    # ---- 绘制 ----

    def paintEvent(self, _event) -> None:
        # 首次 paint：现在才启动 _elapsed 和后续定时器，避开 show()→实际渲染之间的延迟
        if not self._first_paint_done:
            self._first_paint_done = True
            self._elapsed.start()
            timeout = self._params["duration_ms"] + COIN_START_DELAY_MS + 5000
            self.safety_timer.start(max(timeout, TIMEOUT_SAFETY_MS))
            # 先放老虎机转动声（与中央 reel 同步）
            self._play_slot()
            # count-up 结束后再下币 + 切到金币音
            QTimer.singleShot(COIN_START_DELAY_MS, self._start_coins)

        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)
        self._draw_amount(p)
        for c in self.coins:
            self._draw_coin(p, c)
        p.end()

    def _draw_coin(self, p: QPainter, c: Coin) -> None:
        # 阴影（椭圆）
        p.save()
        p.translate(c.x, c.y + c.diameter * 0.55)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(SHADOW_COLOR))
        p.drawEllipse(QPointF(0, 0), c.diameter * 0.45, c.diameter * 0.12)
        p.restore()

        scale_x = max(0.08, abs(math.cos(c.angle)))

        if not self._pixmaps:
            # 降级：金色圆 + 简单中心点
            p.save()
            p.translate(c.x, c.y)
            p.scale(scale_x, 1.0)
            r = c.diameter / 2
            p.setBrush(QBrush(QColor("#f7dd8c")))
            p.setPen(QPen(QColor("#a07820"), max(1.0, c.diameter * 0.025)))
            p.drawEllipse(QPointF(0, 0), r, r)
            p.restore()
            return

        # 真实金币 PNG（cos 缩放模拟翻面）
        pm = self._pixmaps[c.style_idx % len(self._pixmaps)]
        target_w = c.diameter * scale_x
        target_h = c.diameter
        rect = QRectF(c.x - target_w / 2, c.y - target_h / 2, target_w, target_h)
        p.drawPixmap(rect, pm, QRectF(pm.rect()))

    def _draw_amount(self, p: QPainter) -> None:
        """绘制中央 slot-machine 滚动金色数字 + 下方中文副标。"""
        w = self._screen_w
        h = self._screen_h

        num_px = int(h * AMOUNT_SIZE_RATIO)
        label_px = int(h * LABEL_SIZE_RATIO)

        target_str = str(self._target_amount)
        n_digits = len(target_str)

        num_font = QFont(AMOUNT_FONT_FAMILY)
        num_font.setPixelSize(num_px)
        num_font.setWeight(QFont.Medium)
        p.setFont(num_font)
        fm = p.fontMetrics()

        # 数字格子的等宽（取 0-9 中最宽的那个），让滚动时左右不抖
        cell_w = max(fm.horizontalAdvance(str(d)) for d in range(10))
        yen_w = fm.horizontalAdvance("¥")
        gap = int(num_px * 0.08)  # ¥ 与第一位数字的小空隙

        total_w = yen_w + gap + cell_w * n_digits
        base_x = (w - total_w) / 2
        base_y = h * 0.44 + fm.ascent() / 2

        elapsed = self._elapsed.elapsed()

        # 绘制 ¥ 前缀（不滚动，保持金光层叠效果）
        self._draw_text_layered(p, base_x, base_y, "¥")

        # 每位数字独立滚动 reel —— 前 60% 时长所有 reel 一起转，最后 40% 左→右依次定格
        for i, ch in enumerate(target_str):
            final_d = int(ch)
            if n_digits == 1:
                settle_at = COUNTUP_DURATION_MS
            else:
                settle_at = COUNTUP_DURATION_MS * (0.6 + 0.4 * i / (n_digits - 1))
            digit_value = self._reel_position(elapsed, settle_at, final_d)
            cell_x = base_x + yen_w + gap + i * cell_w
            self._draw_reel_digit(p, cell_x, base_y, cell_w, digit_value, fm)

        # 下方中文副标：subtitle 优先，否则用 label（向后兼容）
        text_main = self._subtitle_text if self._subtitle_text else self._label_text
        label_font = QFont(LABEL_FONT_FAMILY)
        label_font.setPixelSize(label_px)
        label_font.setWeight(QFont.Medium)
        label_font.setLetterSpacing(QFont.PercentageSpacing, 200)
        p.setFont(label_font)
        fm2 = p.fontMetrics()
        lw = fm2.horizontalAdvance(text_main)
        lx = (w - lw) / 2
        ly = base_y + label_px * 2.2

        p.save()
        p.setPen(AMOUNT_SHADOW_COLOR)
        p.drawText(QPointF(lx + 2, ly + 2), text_main)
        p.restore()
        p.setPen(LABEL_COLOR)
        p.drawText(QPointF(lx, ly), text_main)

        # spec §8：幸运币命中时，¥X 上方多一行小字
        if self._lucky_enabled:
            tip = "✦   接  住  一  枚  幸  运  币   ✦"
            tw = fm2.horizontalAdvance(tip)
            tx = (w - tw) / 2
            ty = base_y - num_px * 0.85
            p.save()
            p.setPen(AMOUNT_SHADOW_COLOR)
            p.drawText(QPointF(tx + 2, ty + 2), tip)
            p.restore()
            p.setPen(LABEL_COLOR)
            p.drawText(QPointF(tx, ty), tip)

    # ---- slot-machine helpers ----

    def _reel_position(self, elapsed_ms: float, settle_at_ms: float, final_digit: int) -> float:
        """该位 reel 当前显示的数字值。

        - 已 settle：返回 final_digit（整数）
        - 滚动中：温和 ease-out，从 0 滚到 (REEL_CYCLES 圈 + final_digit)；整数部分 = 当前数字，
          小数部分 = 往下一个数字过渡的进度（0..1）
        圈数较少 + 较温和的 ease，让每位数字"看得见在转"，而不是闪成一团模糊。
        """
        if elapsed_ms <= 0:
            return 0.0
        if elapsed_ms >= settle_at_ms:
            return float(final_digit)
        progress = elapsed_ms / settle_at_ms       # 0 → 1
        eased = 1 - (1 - progress) ** 1.7          # ease-out 比 cubic 更温和
        total_scroll = REEL_CYCLES * 10 + final_digit
        return total_scroll * eased

    def _draw_reel_digit(self, p: QPainter, x: float, y: float, cell_w: float,
                         digit_value: float, fm) -> None:
        """在 cell (x, y baseline) 处绘制一位老虎机滚动数字。

        digit_value 整数部分 = 当前数字；小数部分 = 滚到下一个数字的进度。
        视觉：当前数字向上滑出格子，下一个数字从下方滑入（计数器/odometer 风格）。
        """
        integer = int(digit_value)
        fraction = digit_value - integer

        cur_d = str(integer % 10)
        next_d = str((integer + 1) % 10)

        cur_w = fm.horizontalAdvance(cur_d)
        next_w = fm.horizontalAdvance(next_d)
        cur_x = x + (cell_w - cur_w) / 2
        next_x = x + (cell_w - next_w) / 2

        ascent = fm.ascent()
        descent = fm.descent()
        line_h = ascent + descent  # 一位数字格子的视觉高度

        # 滚动偏移（向上）
        cur_y = y - fraction * line_h
        next_y = y + (1 - fraction) * line_h

        # 用与一位数字等高的 clip rect 模拟"窗口"
        clip_top = int(y - ascent - 1)
        clip_h = int(line_h + 2)

        p.save()
        p.setClipRect(int(x - 2), clip_top, int(cell_w + 4), clip_h)
        self._draw_text_layered(p, cur_x, cur_y, cur_d)
        # settle 之后 fraction=0，next 完全在 clip 之外，能省一次绘制
        if fraction > 0.0001:
            self._draw_text_layered(p, next_x, next_y, next_d)
        p.restore()

    def _draw_text_layered(self, p: QPainter, x: float, y: float, text: str) -> None:
        """金光三层：glow + shadow + 主色，匹配中央大字风格。"""
        p.save()
        p.setPen(AMOUNT_GLOW_COLOR)
        for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-3, 0), (3, 0)):
            p.drawText(QPointF(x + dx, y + dy), text)
        p.restore()

        p.save()
        p.setPen(AMOUNT_SHADOW_COLOR)
        p.drawText(QPointF(x + 4, y + 6), text)
        p.restore()

        p.save()
        p.setPen(AMOUNT_COLOR)
        p.drawText(QPointF(x, y), text)
        p.restore()
