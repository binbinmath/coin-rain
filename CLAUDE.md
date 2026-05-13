# CLAUDE.md

本文档是给未来在此项目上工作的 Claude（或其他 AI 协作者）看的项目速览。

## 项目是什么

Windows 桌面小工具：**每天按用户配置的时间**在主屏弹出 3–6 秒的金币雨动画 + 到账大字（count-up 0 → 日收入）+ 连续"哗啦啦"金币碰撞音效。透明置顶、鼠标穿透、结束后自动退出。

首次双击 exe 打开 editorial 米白金风的配置向导；配置后任务计划自动注册每日触发。再次双击 exe 打开管理窗口，可修改配置 / 一键启用停用 / 先试一下。

## 技术栈

- **Python 3.11 + PySide6 6.7.2**（Qt for Python）
- QPainter 手绘 5 款金币（开元通宝 / 永乐通宝 / 宣和通宝 / 壹圓龙洋 / 现代 ¥），水平缩放 `abs(cos(angle))` 模拟硬币自转翻面
- **`winsound`**（Python 标准库）播放 WAV —— **不用 QSoundEffect**，因 PyInstaller 打包后不稳定
- PyInstaller 打包单 exe（约 60 MB，含嵌入字体）
- Windows 任务计划程序：**用 `schtasks.exe` subprocess**（UI 层直接调，不再依赖 PowerShell 脚本）
- 嵌入字体：Fraunces（西文 serif）+ 思源宋体 SC（中文），运行时通过 `QFontDatabase.addApplicationFont` 加载
- pytest（15 个单元测试覆盖纯逻辑）

## 关键文件

### Python 模块（扁平布局，便于 PyInstaller）

- **`coin_rain.py`** —— 入口。解析 argv，派发到 rain 动画 / Setup UI / Manage UI
- **`rain_window.py`** —— `CoinRainWindow`（QWidget）
  - 所有可调动画参数的常量区（`COIN_COUNT_MIN` 等）
  - 到账大字 count-up（B 巨字金光风格，先 1 秒出字再落币）
  - 5 款金币 QPainter 绘制函数 `_draw_kaiyuan/_draw_yongle/_draw_xuanhe/_draw_longyang/_draw_coin`（后者复用原现代 ¥ 样式）
  - 纯函数 `_compute_amount(income, nth, total)` —— 多次模式金额计算
- **`config.py`** —— `Config` dataclass + `load/save/exists` + `resource_path` + `config_path`。纯 Python，无 Qt 依赖
- **`config_window.py`** —— `SetupWindow`（首次配置）+ `ManageWindow`（管理开关）。共用 QSS（`style.qss`）
- **`scheduler.py`** —— schtasks 封装
  - `register(cfg)` / `enable()` / `disable()` / `status()` / `unregister()`
  - 纯函数 `_distribute_times(first, last, count)` —— 多次模式时间等距分布
  - **多次模式 = N 个独立任务** `CoinRainDaily_1/_2/..._N`，每个触发器带 `--nth/--total` 参数
- **`fonts.py`** —— `load_embedded_fonts()` 加载 Fraunces + 思源宋体

### 资源与配置

- `style.qss` —— editorial 米白金 QSS 样式表（Setup + Manage 共用）
- `assets/coin_drop.wav` —— 代码合成的金币瀑布音效
- `assets/fonts/Fraunces-VariableFont.ttf` —— 西文 serif
- `assets/fonts/NotoSerifSC-VariableFont.ttf` —— 中文 serif（25 MB，后续可 subset 瘦身）
- `%APPDATA%\CoinRain\config.json` —— 用户配置持久化位置（运行时生成）

### 打包 / 测试

- `build.bat` —— 一键打包脚本（直接调 `coin_rain.spec`，不再删除重建）
- `coin_rain.spec` —— PyInstaller spec（**手维护**，含 Qt 子树裁剪 + icon + 所有 `--add-data`）。输出 `dist\金币雨.exe`
- `tests/test_logic.py` —— 15 个 pytest，覆盖 `_compute_amount` / `Config.load/save` / `_distribute_times`

### 文档

- `docs/2026-04-15-coin-rain-design.md` —— 第一版（单文件）设计
- `docs/2026-04-15-coin-rain-plan.md` —— 第一版实施计划
- `docs/2026-04-16-coin-rain-todo.md` —— 后续改进 TODO（已全部完成）
- `docs/superpowers/specs/2026-04-16-coin-rain-config-ui-design.md` —— 本次改进的设计文档
- `docs/superpowers/plans/2026-04-16-coin-rain-config-ui.md` —— 本次改进的实施计划
- `制作过程.md` —— 第一版交付过程记录

### 向后兼容保留

- `install_schedule.ps1` / `uninstall_schedule.ps1` —— **命令行备用**，UI 流程不依赖
- 原 `_draw_coin` 方法在 `rain_window.py` 中保留，作为"modern_yuan"样式复用

## 常用命令

| 操作 | 命令 |
|---|---|
| 本地运行（UI 或 config 不存在时） | `python coin_rain.py` |
| 本地运行（强制动画预览） | `python coin_rain.py --rain --test` |
| 打包 exe | 双击 `build.bat` |
| 跑测试 | `python -m pytest tests/ -v` |
| 查看任务状态 | `schtasks /Query /TN CoinRainDaily /FO LIST /V` |
| 立即触发一次 | `schtasks /Run /TN CoinRainDaily` |
| 清掉所有相关任务 | `powershell -ExecutionPolicy Bypass -File uninstall_schedule.ps1` |

## 改动时的注意事项

- **纯逻辑改 `rain_window.py` / `config.py` / `scheduler.py` 的常量或函数体**：重跑 `build.bat` 才能让 exe 生效
- **UI 调整先改 `style.qss`**：改 QSS 不需要重打包字体；但要用 `setProperty + unpolish/polish` 才能让动态属性（如 `[invalid="true"]`）生效
- **透明窗口依赖的 4 个属性**：`FramelessWindowHint` / `WindowStaysOnTopHint` / `WA_TranslucentBackground` / `WA_TransparentForMouseEvents` / `WindowTransparentForInput` —— **别动这组**
- **不要用 QSoundEffect / QMediaPlayer**：PyInstaller 打包不稳
- **任务计划改动**通过 `scheduler.register(cfg)` 或 UI 触发；直接改任务会被下次 UI 保存覆盖
- **schtasks `/Query` 输出解析**对中英文都做了兼容；如果遇到法文/德文等其他语种 Windows，可能需要扩展 `_single_task_status`
- **YAGNI**：不要加日志、托盘、多屏、统计、自更新。如需请先开新的 spec
- **字体瘦身**（若未来需要）：用 `fontTools subset` 按本项目实际用到的字（UI 文本 + 开元/永乐/宣和/壹/圓）裁剪，能把 25 MB 思源宋体砍到 < 1 MB

## 已知约束

- 仅支持 Windows（`winsound` 和 `schtasks.exe` 只在 Windows 可用）
- 仅在主屏播放
- 电脑关机/睡眠时不会补播
- exe 首次运行有 1–2 秒解压延迟（PyInstaller `--onefile` 特性）
- 含字体嵌入后 exe 约 60 MB，可 subset 优化到约 35 MB
