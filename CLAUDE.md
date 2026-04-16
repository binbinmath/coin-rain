# CLAUDE.md

本文档是给未来在此项目上工作的 Claude（或其他 AI 协作者）看的项目速览。

## 项目是什么

Windows 桌面小工具：每天 17:00 在主屏弹出约 4.5 秒的金币雨动画 + 连续"哗啦啦"金币碰撞音效。透明置顶、鼠标穿透、结束后自动退出。

## 技术栈

- **Python 3.11 + PySide6**（Qt for Python）
- QPainter 手绘金币（无图片资源）；水平缩放 `abs(cos(angle))` 模拟硬币自转翻面
- **`winsound`**（Python 标准库）播放 WAV —— 注意：**不用 QSoundEffect**，因为 QSoundEffect 依赖的 Qt 多媒体插件在 PyInstaller `--onefile` 打包后不稳定（实测声音失效）。winsound 是 Windows 原生 API，打包后必然可用。
- PyInstaller 打包单 exe（约 44 MB）
- Windows 任务计划程序（通过 PowerShell `ScheduledTasks` 模块注册）

## 关键文件

- `coin_rain.py` —— **唯一的代码文件**。单文件约 200 行，结构为：
  1. 常量区（`COIN_COUNT_MIN` 等，**所有可调参数都在这里**）
  2. `resource_path()` —— 同时兼容开发态（`__file__`）和 PyInstaller 打包态（`sys._MEIPASS`）找资源
  3. `@dataclass Coin` —— 单个金币的位置/速度/旋转状态
  4. `CoinRainWindow(QWidget)` —— 窗口、渲染、物理、音效
  5. `main()` —— 入口
- `assets/coin_drop.wav` —— 代码合成的金币瀑布音效（28 个叮在 beta 分布时间点上叠加，模拟"哗啦啦"）。打包时通过 `--add-data` 嵌入 exe，运行时解压到 `sys._MEIPASS` 临时目录。
- `build.bat` —— 一键打包脚本
- `install_schedule.ps1` / `uninstall_schedule.ps1` —— 任务计划的装/卸（uninstall 会同时清掉可能存在的 `CoinRainTest` 一次性测试任务）
- `dist/coin_rain.exe` —— 打包产物
- `docs/2026-04-15-coin-rain-design.md` —— 设计文档
- `docs/2026-04-15-coin-rain-plan.md` —— 实施计划
- `docs/2026-04-16-coin-rain-todo.md` —— **后续改进 TODO**（对外发布记录、到账大字显示、首次使用配置界面 + frontdesign 优化）
- `docs/superpowers/specs/2026-04-16-coin-rain-config-ui-design.md` —— 上述 TODO 的设计文档（架构/组件/数据流/UI 规范/金币样式/错误处理/测试/3 阶段交付）
- `制作过程.md` —— 本次完整的交付过程记录

## 常用命令

| 操作 | 命令 |
|---|---|
| 本地运行（调试） | `python coin_rain.py` |
| 打包 exe | 双击 `build.bat`（或 cmd 里 `build.bat`） |
| 注册每日任务 | `powershell -ExecutionPolicy Bypass -File install_schedule.ps1` |
| 立即触发一次 | `powershell -Command "Start-ScheduledTask -TaskName CoinRainDaily"` |
| 查看任务状态 | `powershell -Command "Get-ScheduledTaskInfo -TaskName CoinRainDaily"` |
| 卸载所有任务 | `powershell -ExecutionPolicy Bypass -File uninstall_schedule.ps1` |

## 重新生成音效（如需）

如果你要改音效（比如改成 3 秒、换音色），修改下面脚本并覆盖 `assets/coin_drop.wav`，然后**重跑 `build.bat`** 让新音效打包进 exe：

```python
import struct, wave, math, random
sr = 44100; total_dur = 4.0; n = int(sr * total_dur)
buf = [0.0] * n; random.seed(42)
num_pings = 28
ping_times = sorted(random.betavariate(2.0, 2.5) * 3.3 for _ in range(num_pings))
for t in ping_times:
    f1 = random.uniform(1400, 2800); f2 = f1 * random.choice([1.25, 1.5, 1.85])
    dur = random.uniform(0.08, 0.16); amp = random.uniform(0.35, 0.75); dec = random.uniform(14, 24)
    i0 = int(t*sr); n_p = int(dur*sr)
    for i in range(n_p):
        if i0+i >= n: break
        tau = i/sr; env = math.exp(-tau*dec)
        buf[i0+i] += amp*env*(math.sin(2*math.pi*f1*tau)+0.5*math.sin(2*math.pi*f2*tau))
peak = max(abs(v) for v in buf); scale = 0.85/peak if peak else 1
frames = bytearray()
for v in buf:
    s = max(-32768, min(32767, int(v*scale*32767)))
    frames.extend(struct.pack('<h', s))
with wave.open(r'assets/coin_drop.wav','wb') as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(sr); w.writeframes(bytes(frames))
```

## 改动时的注意事项

- **改动画参数 ≠ 改逻辑**：改 `coin_rain.py` 顶部常量后，**必须重跑 `build.bat`** 才能生效（任务计划跑的是 exe，不是 py）。
- **改时间**：编辑 `install_schedule.ps1` 里的 `-At '17:00'`，然后重跑一次 install 脚本（脚本幂等，会自动卸载旧任务再装新的）。
- **透明窗口 & 鼠标穿透依赖 4 个属性同时设置**：`FramelessWindowHint`、`WindowStaysOnTopHint`、`WA_TranslucentBackground`、`WA_TransparentForMouseEvents`、`WindowTransparentForInput`。**别动这组**，少一个都会出问题。
- **不要用 QSoundEffect / QMediaPlayer**：PyInstaller 打包后 Qt 多媒体插件加载不稳定，用 `winsound.PlaySound(path, SND_FILENAME | SND_ASYNC)` 就够了。
- **不要加单元测试**：此项目核心价值是视觉/桌面效果，单测覆盖成本高、收益低。交付时已用手动 checklist 替代。
- **不要加日志/托盘/配置界面**：项目刻意保持 YAGNI，别过度工程化。

## 已知约束

- 仅支持 Windows（`winsound` 仅 Windows 可用；`WA_TransparentForMouseEvents` 在 Windows 上行为最可靠）
- 仅在主屏播放（多显示器只覆盖主屏，设计决定，不是 bug）
- 电脑关机/睡眠时 17:00 不会补播（设计决定：彩蛋错过就错过）
- exe 首次运行有 1-2 秒解压延迟（PyInstaller `--onefile` 的特性）
