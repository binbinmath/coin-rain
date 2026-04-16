# 金币雨桌面彩蛋 · 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付一个每天 17:00 自动在主屏幕弹出 2.5 秒金币雨动画（透明置顶、鼠标穿透、伴随落地音效）的 Windows 桌面彩蛋程序。

**Architecture:** Python + PySide6 编写主程序；QPainter 手绘金币+物理下落；QSoundEffect 播放一次性音效；PyInstaller 打包为单个 `.exe`；PowerShell 脚本注册 Windows 任务计划程序实现每日定时触发。

**Tech Stack:** Python 3.11.4（已装）、PySide6、PyInstaller、Windows Task Scheduler（schtasks / PowerShell `ScheduledTasks` 模块）

**项目路径：** `E:\Onedrive\Claude\Coin`

**相关规格：** `docs/2026-04-15-coin-rain-design.md`

---

## 文件结构总览

```
E:\Onedrive\Claude\Coin\
    ├── coin_rain.py              # 主程序（唯一代码文件）
    ├── requirements.txt          # 依赖清单
    ├── assets\
    │    └── coin_drop.wav        # 落地音效（CC0）
    ├── build.bat                 # 一键打包脚本
    ├── install_schedule.ps1      # 注册任务计划
    ├── uninstall_schedule.ps1    # 卸载任务计划
    ├── README.md                 # 人类使用说明
    ├── CLAUDE.md                 # 给未来 AI 的项目说明
    ├── 制作过程.md                # 本次完整交付流水账
    ├── docs\
    │    ├── 2026-04-15-coin-rain-design.md
    │    └── 2026-04-15-coin-rain-plan.md  # 本文件
    └── dist\
         └── coin_rain.exe        # Task 6 生成
```

**文件职责划分**：
- `coin_rain.py`：单文件、约 200 行，包含常量区、`Coin` 数据类、`CoinRainWindow(QWidget)` 窗口类、`main()` 入口。结构单一、易读、方便日后改参数。
- 3 个批处理/PS1 脚本各司其职：**装依赖&打包**、**注册调度**、**卸载调度**，互不耦合。
- 2 份文档（README / CLAUDE.md）受众不同：一份写给人，一份写给 AI。
- `制作过程.md` 是本次交付的一次性流水账，不参与后续维护。

> **关于测试**：本项目是短生命周期的**视觉/桌面效果程序**，核心价值（透明置顶、鼠标穿透、金币下落、音效触发）依赖操作系统与 GUI 行为，无法用单元测试可靠覆盖。因此本计划以**手动验收 checklist**代替自动化测试——每个任务完成后给出具体的"启动命令 + 观察要点"供人工 / 代理确认。这是经过权衡的决策，不是偷懒。

---

## Task 1: 初始化项目骨架

**Files:**
- Create: `E:\Onedrive\Claude\Coin\requirements.txt`
- Create: `E:\Onedrive\Claude\Coin\assets\.gitkeep`（占位，音效 Task 2 下载）
- Verify: `E:\Onedrive\Claude\Coin\` 目录存在且只包含 `docs/`

- [ ] **Step 1: 确认项目根目录状态**

Run:
```bash
ls "E:/Onedrive/Claude/Coin"
```
Expected: 仅看到 `docs` 文件夹（其中已有两个 md 文件）。

- [ ] **Step 2: 创建 `assets` 目录和 `requirements.txt`**

Run:
```bash
mkdir -p "E:/Onedrive/Claude/Coin/assets"
```

Write `E:\Onedrive\Claude\Coin\requirements.txt`:
```
PySide6==6.7.2
pyinstaller==6.10.0
```

（版本锁定以保证环境可重现；PySide6 6.7.x 对 Python 3.11 兼容良好。）

- [ ] **Step 3: 安装依赖并验证 PySide6 可用**

Run:
```bash
cd "E:/Onedrive/Claude/Coin" && python -m pip install -r requirements.txt
```
Expected: 最后看到 `Successfully installed PySide6-6.7.2 ... pyinstaller-6.10.0 ...`（若已装则 `Requirement already satisfied`）。

Run:
```bash
python -c "from PySide6.QtCore import qVersion; print('Qt', qVersion())"
```
Expected: 输出 `Qt 6.7.x`（无 ImportError）。

- [ ] **Step 4: 提交骨架（若有 git；无 git 则跳过）**

在本项目中 `E:\Onedrive\Claude\Coin` 不是 git 仓库，**本任务无需 commit**。后续所有"commit"步骤同理跳过。（这是有意决定：该项目为一次性彩蛋工具，改动频率极低，不必引入 git。）

---

## Task 2: 获取金币落地音效

**Files:**
- Create: `E:\Onedrive\Claude\Coin\assets\coin_drop.wav`（从网络下载，CC0）

- [ ] **Step 1: 下载 CC0 金币音效**

从 pixabay 下载一段 CC0 授权的"coin"短音。pixabay 的直链格式示例（**以实际抓取时可用的链接为准**）：

Run（首选方案）：
```bash
curl -L -o "E:/Onedrive/Claude/Coin/assets/coin_drop.wav" "https://cdn.pixabay.com/download/audio/2022/03/15/audio_3d0d7d9fb1.mp3?filename=coin-collect-retro-8bit-sound-effect-145251.mp3"
```

> ⚠️ pixabay 的 URL 经常变，如果 404，改走下面的"兜底方案"：

**兜底方案**：如果下载失败，本 Task 允许回退到**程序内代码合成音效**（不依赖外部文件）：改用 PySide6 运行时生成一段 0.3 秒的短促 "叮" 音（两段正弦波叠加，1760 Hz + 2637 Hz），保存为 `assets/coin_drop.wav`。代码如下（在项目根目录执行）：

```python
# 保存为 tmp_gen_wav.py 后执行，生成完删除
import struct, wave, math
sr = 44100
dur = 0.35
n = int(sr * dur)
frames = []
for i in range(n):
    t = i / sr
    # 双音叠加 + 指数衰减包络
    env = math.exp(-t * 8)
    s1 = math.sin(2 * math.pi * 1760 * t)
    s2 = 0.6 * math.sin(2 * math.pi * 2637 * t)
    v = int(0.6 * env * (s1 + s2) * 32767 / 1.6)
    frames.append(struct.pack('<h', v))
with wave.open(r'E:\Onedrive\Claude\Coin\assets\coin_drop.wav', 'wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes(b''.join(frames))
print("OK")
```

Run:
```bash
cd "E:/Onedrive/Claude/Coin" && python tmp_gen_wav.py && rm tmp_gen_wav.py
```

- [ ] **Step 2: 验证音效文件存在且大小合理**

Run:
```bash
ls -la "E:/Onedrive/Claude/Coin/assets/coin_drop.wav"
```
Expected: 文件存在，大小在 20 KB ~ 500 KB 之间（太小说明下载出错，太大说明不是短音效）。

- [ ] **Step 3: 试听音效（可选但推荐）**

Windows 下双击 `E:\Onedrive\Claude\Coin\assets\coin_drop.wav` 用默认播放器听一下，确认是短促叮当声、不是静音、不刺耳。

---

## Task 3: 实现主程序 `coin_rain.py`

**Files:**
- Create: `E:\Onedrive\Claude\Coin\coin_rain.py`

- [ ] **Step 1: 写入完整源码**

Write `E:\Onedrive\Claude\Coin\coin_rain.py`:

```python
"""金币雨桌面彩蛋 —— 透明置顶窗口，30-50 枚金币下落，约 2.5 秒。"""
from __future__ import annotations

import math
import os
import random
import sys
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QUrl, QPointF
from PySide6.QtGui import QColor, QGuiApplication, QPainter, QRadialGradient, QPen, QFont, QBrush
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtWidgets import QApplication, QWidget

# ================= 可调参数（改这里即可） =================
COIN_COUNT_MIN = 30
COIN_COUNT_MAX = 50
BATCH_COUNT = 3
BATCH_INTERVAL_MS = 100          # 每批之间间隔
COIN_DIAMETER_MIN = 40
COIN_DIAMETER_MAX = 56
GRAVITY = 900.0                  # px / s^2
VY_INIT_MIN = 200.0
VY_INIT_MAX = 400.0
VX_INIT_ABS_MAX = 80.0
ROT_SPEED_MIN = 3.0              # rad / s
ROT_SPEED_MAX = 10.0
FPS = 60
SOUND_VOLUME = 0.7
TIMEOUT_SAFETY_MS = 8000         # 超时兜底（即使异常也 8 秒后退出）

COIN_FILL_CENTER = QColor("#FFE066")
COIN_FILL_EDGE = QColor("#D4A017")
COIN_STROKE = QColor("#8B6914")
COIN_SYMBOL = "¥"
COIN_SYMBOL_COLOR = QColor("#5C4A0A")
SHADOW_COLOR = QColor(0, 0, 0, 76)   # alpha 30%
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
    angle: float       # 当前旋转角度（弧度）
    angular_v: float   # 角速度


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
        self.sound = QSoundEffect(self)
        wav_path = resource_path("assets/coin_drop.wav")
        if wav_path.exists():
            self.sound.setSource(QUrl.fromLocalFile(str(wav_path)))
            self.sound.setVolume(SOUND_VOLUME)
        else:
            # 设计允许：音效文件缺失时静默继续
            self.sound = None  # type: ignore[assignment]

    def start(self) -> None:
        self.show()
        if self.sound is not None:
            self.sound.play()
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
        now = self._now_ms()
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

    @staticmethod
    def _now_ms() -> int:
        from PySide6.QtCore import QElapsedTimer
        # 懒汉式：首次调用时建一个全局 QElapsedTimer
        global _ELAPSED
        try:
            _ELAPSED
        except NameError:
            _ELAPSED = QElapsedTimer()
            _ELAPSED.start()
        return _ELAPSED.elapsed()

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        p.setRenderHint(QPainter.SmoothPixmapTransform, True)
        for c in self.coins:
            self._draw_coin(p, c)
        p.end()

    def _draw_coin(self, p: QPainter, c: Coin) -> None:
        # 阴影（稍微偏下、椭圆）
        p.save()
        p.translate(c.x, c.y + c.diameter * 0.55)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(SHADOW_COLOR))
        p.drawEllipse(QPointF(0, 0), c.diameter * 0.45, c.diameter * 0.12)
        p.restore()

        # 金币本体（通过水平缩放模拟旋转翻面）
        scale_x = abs(math.cos(c.angle))
        if scale_x < 0.08:
            scale_x = 0.08  # 避免完全看不见
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

        # 中心字符 ¥
        font = QFont()
        font.setBold(True)
        font.setPixelSize(int(c.diameter * 0.55))
        p.setFont(font)
        p.setPen(COIN_SYMBOL_COLOR)
        # Qt 的 drawText 锚点是基线，需要手动居中
        fm = p.fontMetrics()
        tw = fm.horizontalAdvance(COIN_SYMBOL)
        th = fm.ascent() - fm.descent()
        p.drawText(QPointF(-tw / 2, th / 2), COIN_SYMBOL)
        p.restore()


def main() -> int:
    # 防止 Qt 在某些 Windows 环境下把 stderr 写到不存在的句柄上
    os.environ.setdefault("QT_LOGGING_RULES", "*.debug=false;qt.qpa.*=false")
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    w = CoinRainWindow()
    w.start()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: 手动运行验证**

Run:
```bash
cd "E:/Onedrive/Claude/Coin" && python coin_rain.py
```

Expected 观察要点（**全部满足才算通过**）：
1. 屏幕顶部出现一批金币，自上而下下落，**约 2-3 秒内全部消失**
2. 金币**确实下落**（不是原地不动、也不是匀速——越往下越快）
3. 金币有**大小差异**、有**旋转翻面效果**（能看到金币宽度随旋转变化）
4. 中心显示 **¥** 字符
5. 播放一次"叮当"声
6. 金币下落过程中，**鼠标可以点击穿透到下方的窗口**（例如点击桌面图标能响应）
7. 动画结束后进程**自动退出**（不会留一个挂起的 python 进程）

如果某条不满足：
- 不下落 / 卡顿 → 检查 Step 1 代码是否完整粘贴
- 无声音 → 检查 `assets/coin_drop.wav` 是否存在、是否能用播放器打开
- 无法穿透 → 确认 `Qt.WindowTransparentForInput` 和 `WA_TransparentForMouseEvents` 都设置了
- 窗口不透明 → 确认 `WA_TranslucentBackground` 设置了、`paintEvent` 里没填充底色

- [ ] **Step 3: 再跑一次，确认**没有副作用**

Run:
```bash
cd "E:/Onedrive/Claude/Coin" && python coin_rain.py
```
同一个会话内连续跑两次应该都正常；跑完后任务管理器里不应该有残留的 `python.exe`。

---

## Task 4: 编写 `build.bat` 打包脚本

**Files:**
- Create: `E:\Onedrive\Claude\Coin\build.bat`

- [ ] **Step 1: 写入打包脚本**

Write `E:\Onedrive\Claude\Coin\build.bat`:

```bat
@echo off
REM 一键打包 coin_rain.exe
REM 用法：双击本文件即可

setlocal
cd /d "%~dp0"

echo [1/3] Installing dependencies...
python -m pip install -r requirements.txt || goto :err

echo [2/3] Cleaning old build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist coin_rain.spec del /q coin_rain.spec

echo [3/3] Building exe with PyInstaller...
python -m PyInstaller ^
  --onefile ^
  --windowed ^
  --name coin_rain ^
  --add-data "assets/coin_drop.wav;assets" ^
  coin_rain.py || goto :err

echo.
echo === Build succeeded: dist\coin_rain.exe ===
pause
exit /b 0

:err
echo.
echo === Build FAILED ===
pause
exit /b 1
```

关键点说明：
- `--onefile`：输出单个 exe 文件
- `--windowed`：不弹 console 窗口
- `--add-data "assets/coin_drop.wav;assets"`：把音效嵌入 exe；运行时解压到临时目录，代码里 `resource_path()` 通过 `sys._MEIPASS` 找到它
- `pause`：留住窗口方便看报错

- [ ] **Step 2: 执行打包并验证**

双击 `build.bat`，或命令行：
```bash
cd "E:/Onedrive/Claude/Coin" && cmd //c build.bat
```

Expected: 最后看到 `=== Build succeeded: dist\coin_rain.exe ===`，并且 `E:\Onedrive\Claude\Coin\dist\coin_rain.exe` 存在（约 30-50 MB）。

Run:
```bash
ls -la "E:/Onedrive/Claude/Coin/dist/coin_rain.exe"
```
Expected: 文件存在，大小在 25 MB ~ 60 MB 之间。

- [ ] **Step 3: 运行打包后的 exe 验证**

Run:
```bash
"E:/Onedrive/Claude/Coin/dist/coin_rain.exe"
```
（Windows 下也可以双击文件资源管理器里的 exe）

Expected 观察要点：与 Task 3 Step 2 相同（金币下落、有声、穿透、自动退出）。
首次运行可能有 1-2 秒"白屏"延迟（PyInstaller onefile 解压），这是正常的。

---

## Task 5: 注册 / 卸载 Windows 任务计划

**Files:**
- Create: `E:\Onedrive\Claude\Coin\install_schedule.ps1`
- Create: `E:\Onedrive\Claude\Coin\uninstall_schedule.ps1`

- [ ] **Step 1: 写入 `install_schedule.ps1`**

Write `E:\Onedrive\Claude\Coin\install_schedule.ps1`:

```powershell
# 注册每日 17:00 运行 coin_rain.exe 的任务计划
# 用法：右键 -> 使用 PowerShell 运行

$ErrorActionPreference = 'Stop'
$TaskName = 'CoinRainDaily'
$ExePath = Join-Path $PSScriptRoot 'dist\coin_rain.exe'

if (-not (Test-Path $ExePath)) {
    Write-Error "找不到 $ExePath。请先双击 build.bat 完成打包。"
    exit 1
}

# 如果已注册，先卸载旧的再装新的（幂等）
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Write-Host "检测到已存在的任务 $TaskName，先卸载..."
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

$Action = New-ScheduledTaskAction -Execute $ExePath
$Trigger = New-ScheduledTaskTrigger -Daily -At '17:00'
$Settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable:$false `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 1)
$Principal = New-ScheduledTaskPrincipal -UserId $env:UserName -LogonType Interactive -RunLevel Limited

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $Action `
    -Trigger $Trigger `
    -Settings $Settings `
    -Principal $Principal `
    -Description '每天 17:00 在主屏幕播放金币雨彩蛋动画（2-3 秒）' | Out-Null

Write-Host ""
Write-Host "=== 已注册任务：$TaskName ==="
Write-Host "触发：每天 17:00"
Write-Host "动作：$ExePath"
Write-Host ""
Write-Host "提示：可以在 Windows '任务计划程序' 里搜索 '$TaskName' 查看/调试。"
Write-Host "     卸载请运行 uninstall_schedule.ps1。"
Read-Host "按 Enter 退出"
```

关键配置对应设计文档：
- `-Daily -At '17:00'`：每天 17:00
- `-AllowStartIfOnBatteries -DontStopIfGoingOnBatteries`：笔电电池模式也触发
- `-StartWhenAvailable:$false`：不补播（电脑关机/睡眠就跳过）
- `-MultipleInstances IgnoreNew`：已在运行则忽略新触发
- `-LogonType Interactive -RunLevel Limited`：只在用户登录时运行、普通权限（不用管理员）
- `-ExecutionTimeLimit 1 min`：兜底，最长 1 分钟强制结束

- [ ] **Step 2: 写入 `uninstall_schedule.ps1`**

Write `E:\Onedrive\Claude\Coin\uninstall_schedule.ps1`:

```powershell
# 卸载 CoinRainDaily 任务计划
$TaskName = 'CoinRainDaily'
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "已卸载任务：$TaskName"
} else {
    Write-Host "任务 $TaskName 不存在，无需卸载。"
}
Read-Host "按 Enter 退出"
```

- [ ] **Step 3: 执行注册并验证**

在 PowerShell 里运行（或右键 ps1 -> 使用 PowerShell 运行）：
```bash
powershell -ExecutionPolicy Bypass -File "E:/Onedrive/Claude/Coin/install_schedule.ps1"
```

Expected: 输出 `=== 已注册任务：CoinRainDaily ===`。

- [ ] **Step 4: 在任务计划程序 GUI 里核对**

Run:
```bash
powershell -Command "Get-ScheduledTask -TaskName CoinRainDaily | Select-Object TaskName,State,@{N='NextRun';E={(Get-ScheduledTaskInfo \$_).NextRunTime}}"
```

Expected: 看到 `CoinRainDaily  Ready  NextRun=<今天或明天的 17:00:00>`。

- [ ] **Step 5: 立即触发一次任务以端到端验证**

不想等到 17:00？运行：
```bash
powershell -Command "Start-ScheduledTask -TaskName CoinRainDaily"
```

Expected: 几秒内屏幕出现金币雨动画，效果与 Task 4 Step 3 相同。

- [ ] **Step 6: 验证卸载脚本也能工作（测试后再装回）**

Run:
```bash
powershell -ExecutionPolicy Bypass -File "E:/Onedrive/Claude/Coin/uninstall_schedule.ps1"
```
Expected: `已卸载任务：CoinRainDaily`。然后再跑一次 Step 3 装回来。

---

## Task 6: 写 `README.md`（给人类）

**Files:**
- Create: `E:\Onedrive\Claude\Coin\README.md`

- [ ] **Step 1: 写入 README**

Write `E:\Onedrive\Claude\Coin\README.md`:

````markdown
# 金币雨桌面彩蛋

每天下午 **17:00** 自动在屏幕上播放约 2.5 秒的金币下落动画，带一次"叮当"落地音效。

- 透明悬浮，**不打断当前工作**（鼠标穿透，金币只是视觉覆盖层）
- 只在主屏播放，只在你登录时触发，电脑关机/睡眠则跳过
- 动画结束后自动关闭

## 安装（3 步）

1. **打包 exe**：双击 `build.bat`
   → 自动安装依赖 + 生成 `dist\coin_rain.exe`
2. **注册每日触发**：右键 `install_schedule.ps1` → 使用 PowerShell 运行
   → 自动注册名为 `CoinRainDaily` 的任务计划
3. **立即试一下**（不想等到 17:00）：
   ```powershell
   Start-ScheduledTask -TaskName CoinRainDaily
   ```

## 卸载

右键 `uninstall_schedule.ps1` → 使用 PowerShell 运行。
（exe 和源码不会被删除，你可以手动删 `E:\Onedrive\Claude\Coin` 整个文件夹。）

## 调参

想改数量/时长/颜色/字符？打开 `coin_rain.py`，顶部有 `========== 可调参数 ==========` 区块，改完重新双击 `build.bat` 即可。常见改法：

| 想要 | 改哪个常量 |
|---|---|
| 金币更多 | `COIN_COUNT_MIN/MAX` 调大 |
| 动画更久 | `VY_INIT_MIN/MAX` 调小（下落慢）或 `GRAVITY` 调小 |
| 换符号 | `COIN_SYMBOL = "$"` / `"元"` / `"¢"` |
| 换颜色 | `COIN_FILL_CENTER` / `COIN_FILL_EDGE` |
| 换时间 | 编辑 `install_schedule.ps1` 里的 `-At '17:00'` |
| 换音效 | 覆盖 `assets/coin_drop.wav` |

## 文件说明

| 文件 | 作用 |
|---|---|
| `coin_rain.py` | 主程序源码 |
| `assets/coin_drop.wav` | 落地音效 |
| `build.bat` | 一键打包脚本 |
| `install_schedule.ps1` | 注册每日 17:00 任务 |
| `uninstall_schedule.ps1` | 卸载任务 |
| `dist/coin_rain.exe` | 打包产物 |
| `docs/` | 设计文档和实施计划 |

## 排错

- **双击 exe 没反应**：在 cmd 里运行 `dist\coin_rain.exe`，看有无报错
- **没声音**：确认 `assets\coin_drop.wav` 存在且不是 0 字节；打包后若没嵌入，重跑 `build.bat`
- **17:00 没触发**：打开 "任务计划程序"，查找 `CoinRainDaily` 任务，看 "上次运行结果"
- **窗口不透明或无法穿透**：Windows 版本过低（需 Win10+），或显卡驱动异常
````

- [ ] **Step 2: 验证文件存在**

Run:
```bash
ls -la "E:/Onedrive/Claude/Coin/README.md"
```
Expected: 文件存在，非空。

---

## Task 7: 写 `CLAUDE.md`（给未来的 AI 协作者）

**Files:**
- Create: `E:\Onedrive\Claude\Coin\CLAUDE.md`

- [ ] **Step 1: 写入 CLAUDE.md**

Write `E:\Onedrive\Claude\Coin\CLAUDE.md`:

```markdown
# CLAUDE.md

本文档是给未来在此项目上工作的 Claude（或其他 AI 协作者）看的项目速览。

## 项目是什么

Windows 桌面小工具：每天 17:00 在主屏弹出 2.5 秒的金币雨动画 + 一次落地音效。透明置顶、鼠标穿透、结束后自动退出。

## 技术栈

- Python 3.11 + PySide6（Qt for Python）
- QPainter 手绘金币（无图片资源），QSoundEffect 播放短音
- PyInstaller 打包单 exe
- Windows 任务计划程序（通过 PowerShell `ScheduledTasks` 模块注册）

## 关键文件

- `coin_rain.py` — **唯一的代码文件**。单文件约 200 行，结构为：
  1. 常量区（`COIN_COUNT_MIN` 等，**所有可调参数都在这里**）
  2. `resource_path()` — 同时兼容开发态和 PyInstaller 打包态找资源
  3. `@dataclass Coin` — 单个金币的位置/速度/旋转状态
  4. `CoinRainWindow(QWidget)` — 窗口、渲染、物理、音效
  5. `main()` — 入口
- `assets/coin_drop.wav` — CC0 授权的短音效（打包时通过 `--add-data` 嵌入 exe）
- `build.bat` — 一键打包脚本
- `install_schedule.ps1` / `uninstall_schedule.ps1` — 任务计划的装/卸
- `dist/coin_rain.exe` — 打包产物
- `docs/2026-04-15-coin-rain-design.md` — 设计文档
- `docs/2026-04-15-coin-rain-plan.md` — 实施计划
- `制作过程.md` — 本次交付的过程记录

## 常用命令

| 操作 | 命令 |
|---|---|
| 本地运行（调试） | `python coin_rain.py` |
| 打包 exe | 双击 `build.bat`（或 cmd 里 `build.bat`） |
| 注册任务计划 | `powershell -ExecutionPolicy Bypass -File install_schedule.ps1` |
| 立即触发一次 | `powershell -Command "Start-ScheduledTask -TaskName CoinRainDaily"` |
| 查看任务状态 | `powershell -Command "Get-ScheduledTaskInfo -TaskName CoinRainDaily"` |
| 卸载任务 | `powershell -ExecutionPolicy Bypass -File uninstall_schedule.ps1` |

## 改动时的注意事项

- **改动画参数 ≠ 改逻辑**：改 `coin_rain.py` 顶部常量后，**必须重跑 `build.bat`** 才能生效（任务计划跑的是 exe，不是 py）
- **改时间**：编辑 `install_schedule.ps1` 里的 `-At '17:00'`，然后重跑一次 install 脚本（脚本是幂等的，会先卸载旧任务）
- **透明窗口 & 鼠标穿透依赖 4 个属性同时设置**：`FramelessWindowHint`、`WindowStaysOnTopHint`、`WA_TranslucentBackground`、`WA_TransparentForMouseEvents`。**别动这组**，少一个都会出问题。
- **不要加单元测试**：此项目核心价值是视觉/桌面效果，单测覆盖成本高、收益低。设计时已明确用手动 checklist 替代。
- **不要加日志/托盘/配置界面**：项目刻意保持 YAGNI，别过度工程化。

## 已知约束

- 仅支持 Windows（Qt 的 `WA_TransparentForMouseEvents` 在 Windows 上行为可靠；macOS/Linux 未测试）
- 仅在主屏播放（多显示器只覆盖主屏，这是设计决定，不是 bug）
- 电脑关机/睡眠时 17:00 不会补播（设计决定：彩蛋错过就错过）
```

- [ ] **Step 2: 验证文件存在**

Run:
```bash
ls -la "E:/Onedrive/Claude/Coin/CLAUDE.md"
```
Expected: 文件存在。

---

## Task 8: 写 `制作过程.md`（给人类看的流水账）

**Files:**
- Create: `E:\Onedrive\Claude\Coin\制作过程.md`

- [ ] **Step 1: 回顾本次完整过程并写成流水账**

Write `E:\Onedrive\Claude\Coin\制作过程.md` 的内容结构如下，**具体内容需在实施完成时根据实际过程填写**：

```markdown
# 金币雨彩蛋 · 制作过程记录

- 日期：2026-04-15
- 位置：E:\Onedrive\Claude\Coin
- 协作者：用户 + Claude Code (Opus 4.6)

## 一、起因（用户一句话）

> "我想做一个效果，就是到特定的时间点的时候会在屏幕上冒出很多金币，然后播放金币落地的音效。"

## 二、需求澄清（7 个问题）

用 brainstorming 技能按顺序问了 7 个问题，逐步收敛到精确需求：

| # | 问题 | 选项 | 用户答案 |
|---|---|---|---|
| 1 | 做在哪里？(PPT/网页/前端项目/桌面) | A/B/C/D | 桌面程序 |
| 2 | 触发方式 (定时/手动/事件) | A/B/C | 每天下午 17:00 自动 |
| 3 | 显示方式 (全屏/透明悬浮/小窗) | A/B/C | B 透明悬浮 |
| 4 | 时长强度 (2-3s / 5-8s / 10s+ / 自定义) | A/B/C/D | A 短促小惊喜 |
| 5 | 素材来源 (自动/提供/混合) | A/B/C | A 全部自动 |
| 6 | 技术方案 (PySide6 / Tauri) | 1/2 | 方案一 PySide6 |
| 7 | 路径和文档要求 | — | E:\Onedrive\Claude\Coin + CLAUDE.md + 制作过程.md |

## 三、关键决策与为什么

- **为什么选 PySide6 而非 Tauri**：Tauri 需要装 Rust 工具链，对 2-3 秒彩蛋收益低。PySide6 + PyInstaller 已足够漂亮且部署最简单。
- **为什么只播一次音效而非每枚响一次**：30-50 枚金币同时叮当会变噪音。
- **为什么不写单元测试**：核心价值（透明、穿透、下落视觉、系统调度）无法被单测可靠覆盖，改用手动 checklist。
- **为什么不加日志/托盘/配置 UI**：YAGNI，一次性彩蛋不值得这些工程。
- **为什么音效准备了"网络下载 + 代码合成"双路径**：pixabay 直链经常失效，代码合成做兜底保证任务必能完成。

## 四、实施顺序（对应 plan 的 Task 1-8）

1. Task 1：初始化骨架 + 装依赖 → <实际耗时>
2. Task 2：下载/合成音效 → <实际耗时>
3. Task 3：写 coin_rain.py 主程序 → <实际耗时>
4. Task 4：写 build.bat 并首次打包 → <实际耗时>
5. Task 5：写 install/uninstall 脚本并注册任务计划 → <实际耗时>
6. Task 6-8：写三份文档

## 五、遇到的问题与解决

<在实际实施时填写。模板：>
- **问题 X**：描述症状
  - **原因**：根因分析
  - **解决**：采取的措施

## 六、验收清单（最终确认）

- [ ] 双击 dist\coin_rain.exe 能看到 2.5 秒金币雨动画
- [ ] 动画期间鼠标能穿透点击下方窗口
- [ ] 能听到一次"叮当"落地音效
- [ ] Start-ScheduledTask -TaskName CoinRainDaily 能立即触发
- [ ] Get-ScheduledTaskInfo 显示 NextRunTime 是 17:00
- [ ] uninstall_schedule.ps1 能干净卸载

## 七、后续如果要改

- 改时间/数量/颜色/符号/音效 → 见 CLAUDE.md 的 "常用命令" 和 "改动时的注意事项"
```

- [ ] **Step 2: 填充实际内容**

在 Task 1-7 全部完成后回来补齐本文件的"实际耗时"、"遇到的问题与解决"、"验收清单勾选"。

---

## Task 9: 最终端到端验收

**Files:** 无（纯验证）

- [ ] **Step 1: 清点所有交付物**

Run:
```bash
ls -la "E:/Onedrive/Claude/Coin/" && ls -la "E:/Onedrive/Claude/Coin/dist/" && ls -la "E:/Onedrive/Claude/Coin/assets/" && ls -la "E:/Onedrive/Claude/Coin/docs/"
```

Expected: 项目根下有 `coin_rain.py`、`requirements.txt`、`build.bat`、`install_schedule.ps1`、`uninstall_schedule.ps1`、`README.md`、`CLAUDE.md`、`制作过程.md`；`assets/` 有 `coin_drop.wav`；`dist/` 有 `coin_rain.exe`；`docs/` 有 2 份 md。

- [ ] **Step 2: 端到端验证**

Run:
```bash
powershell -Command "Start-ScheduledTask -TaskName CoinRainDaily"
```

观察要点（全部满足才算项目完成）：
1. ✅ 几秒内屏幕顶部出现金币雨
2. ✅ 金币下落、旋转、有大小差异
3. ✅ 播放一次"叮当"音效
4. ✅ 鼠标可点击穿透到下方窗口
5. ✅ 约 2-3 秒后自动消失
6. ✅ 任务管理器里没有残留的 coin_rain.exe 进程

- [ ] **Step 3: 确认下次触发时间**

Run:
```bash
powershell -Command "Get-ScheduledTaskInfo -TaskName CoinRainDaily | Select-Object NextRunTime,LastRunTime,LastTaskResult"
```

Expected: `NextRunTime` 显示今天或明天的 17:00；`LastTaskResult = 0`（上次运行成功）。

- [ ] **Step 4: 向用户报告完成**

完整报告给用户：
- 所有交付物位置
- 如何立即测试（Start-ScheduledTask 命令）
- 如何卸载（uninstall_schedule.ps1）
- 如何调参（README.md 的"调参"表）

---

## 总结检查表（写计划时的自检）

- [x] 每个 task 文件清单明确（Create/Modify）
- [x] 每个 step 2-5 分钟粒度
- [x] 代码块给出完整代码，无占位符
- [x] 命令行给出 expected 输出
- [x] 测试策略明确（手动 checklist，已说明原因）
- [x] 覆盖 spec 每一节：
  - spec §1-2 需求 → 全部落在 Task 3 常量区 + Task 5 任务计划
  - spec §3 架构 → Task 3 + Task 4 + Task 5
  - spec §4 目录结构 → Task 1 骨架 + 各 Task 创建对应文件
  - spec §5 视觉细节 → Task 3 代码
  - spec §6 部署 → Task 4 + Task 5
  - spec §7 任务计划配置 → Task 5 脚本
  - spec §8 错误处理 → Task 3 代码里的 `wav_path.exists()` 判断、Task 5 的 `MultipleInstances IgnoreNew`、Task 3 的 safety_timer
  - spec §9 明确不做 → 无对应 task（YAGNI 已遵守）
  - spec §10 交付物清单 → Task 9 清点
