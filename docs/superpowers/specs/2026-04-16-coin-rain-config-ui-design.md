# 金币雨改进 · 配置 UI + 到账大字 + 多次触发 · 设计文档

- **日期**：2026-04-16
- **状态**：Spec · 已与用户对齐方向（brainstorming 阶段已完成）
- **下一步**：进入 writing-plans 生成实施计划

## 1. 背景 & 目标

当前的金币雨（`coin_rain.py`）是一个 ~200 行的单文件 PySide6 程序：每天 17:00 由 Windows 任务计划触发，播 ~4.5 秒透明置顶的金币雨动画 + 音效，结束即退。所有参数（金币数、动画时长、触发时间等）都硬编码在代码顶部常量区或 PowerShell 脚本中。

本次改进的目标：把它从"个人玩具"升级为"可对外发布的桌面小工具"，引入：

1. **首次使用的图形配置界面**：用户双击 exe 第一次打开时，引导配置；之后无需再配置（除非想关闭或修改）。
2. **金币雨中同时显示「今日到账 ¥XXX」大字**：count-up 动效 + 先 1 秒出字再落币，强化"每日到账"的仪式感。
3. **支持每天多次触发**：用户填"首次时间/末次时间/次数 N"，N 次等距分布；文案在"当前已到账"→"今日到账"之间闭合切换。
4. **视觉升级**：editorial 米白+鎏金 serif 风配置 UI；5 款精良金币（默认开元通宝，支持混合下落）；字体嵌入 exe 保证跨机器一致。
5. **面向对外发布的文档留痕**：改进过程沿用 `制作过程.md` 的写法持续记录，便于日后整理成公开内容。

## 2. 用户故事

- **初次使用**：用户下载 `coin_rain.exe`，双击打开 → 看到配置向导（editorial 米白金风）→ 填完 4 字段 → 点「先试一下」看效果 → 满意后点「保存并启用」→ 每日自动触发。
- **日常使用**：到点金币雨自动触发；先看到金色大字 count-up "今日到账 ¥300"，1 秒后金币倾泻而下伴随"哗啦啦"音效。
- **修改设置**：双击 exe → 进入管理界面 → 点「修改配置」→ 改完保存。
- **想关掉**：双击 exe → 管理界面右上角切换"停用"→ 任务计划被禁用但不卸载。
- **恢复**：再次双击 exe → 切换"启用"即可。

## 3. 架构

单 exe + CLI 参数分流：

```
coin_rain.exe
  ├── --rain              → RainWindow（动画+大字+音效）           [任务计划调用]
  ├── --rain --test       → RainWindow(test=True)                  [UI「先试一下」]
  ├── --rain --nth=X --total=N  → 多次模式某一次                   [任务计划触发器]
  └── (无参数)
        ├── Config.exists() == False → SetupWindow                 [首次配置]
        └── Config.exists() == True  → ManageWindow                [管理/开关]
```

### 关键决策

| 项 | 决策 | 理由 |
|---|---|---|
| exe 拆分 | 单 exe + CLI 分流 | 一次构建、无需维护两份打包 |
| 配置路径 | `%APPDATA%\CoinRain\config.json` | Windows 用户级标准路径，无权限问题 |
| 任务计划 | `schtasks.exe` subprocess | 原生命令，不依赖 PowerShell 模块；UI 保存时直接调 |
| 字体策略 | Fraunces + 思源宋体 TTF 嵌入 exe | `QFontDatabase.addApplicationFont`；保证跨机器一致 |
| UI 框架 | 继续用 PySide6 | 与动画同框架；避免引入 Web 前端 |
| 向后兼容 | 保留 `install_schedule.ps1` / `uninstall_schedule.ps1` | 命令行高级用户仍可用；UI 不依赖它们 |

## 4. 组件

```
coin_rain/
├── __main__.py          入口。~40 行
│                        parse argv → 派发到 rain / setup / manage
│
├── config.py            配置数据模型与持久化。~80 行
│                        dataclass Config + load/save/exists
│                        纯函数、无 UI/Qt 依赖
│
├── scheduler.py         Windows 任务计划的注册/禁用/查询。~100 行
│                        register(config) / enable() / disable() / status() / unregister()
│                        通过 subprocess 调 schtasks.exe
│                        提供纯函数 _distribute_times(first, last, n) 用于多次模式
│
├── rain_window.py       CoinRainWindow（QWidget）。~300 行（原 200 + 新增 100）
│                        保留现有动画/音效；新增：
│                          · 到账大字 count-up 层（B「巨字金光」风格）
│                          · 前 1.0s 先出字、之后落币的分阶段时序
│                          · 5 款金币 QPainter 绘制函数（A/B/C/D/E）
│                          · 混合下落（每个 Coin.style_id 随机）
│                        提供纯函数 _compute_amount(income, nth, total)
│
├── config_window.py     SetupWindow + ManageWindow。~400 行（新增）
│                        两个 QWidget 共用 QSS 样式表（editorial 米白金）
│                        共享字段渲染基类；Setup/Manage 区别在于 editable 与否
│                        「修改配置」按钮 = ManageWindow 切换到 Setup 模式
│
└── assets/
    ├── coin_drop.wav            不动
    └── fonts/
        ├── Fraunces-VariableFont.ttf
        └── NotoSerifSC-VariableFont.ttf
```

## 5. 配置数据模型

### Config dataclass（`config.py`）

```python
@dataclass
class Config:
    version: int                  # schema version, 当前 = 1
    income: int                   # 每日收入（正整数，元）
    intensity: str                # "light" | "medium" | "heavy"
    mode: str                     # "single" | "multi"
    # single 模式
    time: str | None              # "HH:MM"，mode == "single" 时有值
    # multi 模式
    first_time: str | None        # "HH:MM"，mode == "multi" 时有值
    last_time: str | None         # "HH:MM"，mode == "multi" 时有值
    count: int | None             # N 次数，mode == "multi" 时 ∈ [2, 12]
    # 金币与样式
    coin_style: str               # "kaiyuan" | "yongle" | "xuanhe" | "longyang" | "modern_yuan"
    mixed_coins: bool             # 是否混合下落（5 款从池里随机抽）
    # 元数据
    installed_at: str             # ISO8601 首次保存时间，供"已运行 N 天"计算
```

### JSON schema（存盘格式，`%APPDATA%\CoinRain\config.json`）

```json
{
  "version": 1,
  "income": 300,
  "intensity": "medium",
  "mode": "single",
  "time": "17:00",
  "first_time": null,
  "last_time": null,
  "count": null,
  "coin_style": "kaiyuan",
  "mixed_coins": false,
  "installed_at": "2026-04-16T10:30:00"
}
```

### 强度档位映射（`rain_window.py` 内部常量）

| 档位 | 金币数 | 动画时长 |
|---|---|---|
| light | 20 | 3.0s |
| medium | 40 | 4.5s（当前默认）|
| heavy | 80 | 6.0s |

> 音量不做档位区分：`winsound` 标准库不支持程序调音量，靠系统音量。如后续需要可换 `simpleaudio` 或 `sounddevice`，但会增加打包体积，本 spec 不做。

## 6. 关键流程

### ① 首次启动（无参数，无 config）

1. `__main__.py` 检测 `Config.exists() == False`
2. 启动 `SetupWindow`，默认值：¥300 / medium / single / 17:00 / 开元通宝 / 不混合
3. 用户填完 → 点「保存并启用」
4. `Config.save()` 写 `%APPDATA%\CoinRain\config.json`，`installed_at = now()`
5. `Scheduler.register(config)` 调 schtasks 注册任务
6. QMessageBox 成功提示 → 窗口关闭

### ② 再次启动（无参数，有 config）

1. `__main__.py` 检测 `Config.exists() == True`
2. 启动 `ManageWindow`，从 config + `Scheduler.status()` 填充界面
3. 用户操作：
   - 「先试一下」→ `subprocess.Popen([exe_path, "--rain", "--test"])`
   - 「修改配置」→ 切换到 Setup 模式 → 保存 → `Scheduler.register()` 覆盖（`/F`）
   - 切换启用 ↔ 停用 → `Scheduler.enable()` / `disable()`
   - 「关闭窗口」→ `sys.exit(0)`

### ③ 任务触发（`--rain`）

1. `__main__.py` 解析 `--rain [--nth=X --total=N] [--test]`
2. 读 config，计算 `amount = _compute_amount(income, nth, total)`（单次 nth=1/total=1，等价于 income）
3. 启动 `RainWindow(config, amount, mode_is_final=nth==total, test=...)`
4. **阶段 1（0–1.0s）**：count-up 大字从 0 滚到 `amount`；金币还没开始
5. **阶段 2（1.0s–约 5.5s）**：金币开始下落 + winsound 播 wav
6. **阶段 3（结束）**：`sys.exit(0)`

### ④ 测试触发（`--rain --test`）

同 ③，但 `amount = income`（显示全额）、不论 mode，文案用「今日到账」。UI 父进程不退出。

### ⑤ 多次模式 · 金额与时间

```python
# 时间等距分布
_distribute_times("09:30", "17:30", 3) == ["09:30", "13:30", "17:30"]

# 金额累计
_compute_amount(income=300, nth=1, total=3) == 100
_compute_amount(income=300, nth=2, total=3) == 200
_compute_amount(income=300, nth=3, total=3) == 300  # 最后一次 = 全额，闭合
```

任务计划注册时：1 个任务 + N 个触发器，每个触发器命令行带 `--nth=X --total=N`。

### ⑥ 文案切换

- 单次模式 or 多次模式最后一次：「**今日到账** ¥XXX」
- 多次模式非最后一次：「**当前已到账** ¥XXX」

## 7. UI 设计规范

### 整体风格

Editorial serif · 米白纸本底 + 鎏金主色：

- 主色变量：
  - `--cream: #efe5d0`（外部深色模拟桌面）
  - `--paper: #faf3e4`（窗口主底）
  - `--ink: #241810`（主文字 / 主按钮底）
  - `--ink-soft: #6b5339`（次文字）
  - `--gold: #b8925a`（强调 / 装饰线）
  - `--gold-deep: #8a6830`（按钮描边 / hover）
  - `--rust: #a83e2e`（校验错误色）

- 字体：
  - 西文 display / italic：**Fraunces**（可变字重 300–600）
  - 中文正文 & 小字：**思源宋体 SC**（Noto Serif SC，字重 400/500/700）
  - 所有字体通过 `QFontDatabase.addApplicationFont` 加载嵌入的 TTF

### 窗口规格

- SetupWindow / ManageWindow 均为 **960 × 600 固定尺寸**
- Windows 原生 chrome（非 frameless），任务栏图标沿用
- 背景纸本质感：径向 gradient + 噪声 SVG（已在 mockup 验证）
- 四角微金线装饰（14px L 形）

### SetupWindow 布局

2 列 × 2 行表单，字段带 `01 02 03 04` 斜体编号：

```
┌──────────────────────────────────────────────────────────────┐
│ [titlebar · "金币雨 · 首次配置"]                              │
├──────────────────────────────────────────────────────────────┤
│  01 每日收入                    03 触发方式                    │
│  ¥ [300]   元 / 天              [每天一次] [每天多次]          │
│                                                               │
│  02 雨势                        04 触发时间                    │
│  [小雨][中雨][大雨]             17:00  每天此刻落下...         │
├──────────────────────────────────────────────────────────────┤
│  配置路径 …                     [先试一下]  [保存并启用 →]    │
└──────────────────────────────────────────────────────────────┘
```

多次模式下 03 字段区展开为 3 个并排子字段（首次 / 末次 / 次数）。

### ManageWindow 布局

顶部品牌 + 右上角启用/停用总开关；中段 4 字段配置摘要卡；下方金色横条显示"下次金币雨：今天 17:00 · 今日到账 ¥300 · in 2 hours"；底部 3 按钮：先试一下 / 修改配置 / 关闭窗口。品牌区彩蛋：「已为你自动运行 N 天」（基于 `installed_at`）。

### 按钮

- **primary**：`var(--ink)` 底 + `var(--paper)` 字，用于「保存并启用 →」/「关闭窗口」
- **secondary**：透明底 + `var(--gold-deep)` 描边文字，用于「先试一下 / 修改配置」

## 8. 金币样式规范

5 款金币（mockup 中的 A/B/C/D/E），默认 `coin_style = kaiyuan`，`mixed_coins = false`。打开混合下落（`mixed_coins = true`）时，每个 Coin 实例的 `style_id` 从全部 5 款中均匀随机抽取（本期不做"用户勾选池子"，YAGNI；如后续需要再加 `mixed_pool: list[str]` 字段）。

| id | 名称 | 风格要点 | 文字 |
|---|---|---|---|
| kaiyuan | 开元通宝（唐 · 默认） | 做旧金 + 铜绿 patina + 方孔 | 开 / 元 / 通 / 宝 |
| yongle | 永乐通宝（明） | 鎏金亮面 + 方孔 + 双重轮廓 | 永 / 乐 / 通 / 宝 |
| xuanhe | 宣和通宝（北宋） | 温润古金 + 瘦金体 | 宣 / 和 / 通 / 宝 |
| longyang | 壹圓龙洋（民国） | 齿边 + 无孔 + 居中大字 | 壹 / 圓 + ✦ 装饰 + 桂叶 |
| modern_yuan | 现代 ¥ 金币 | 抛光强光 + 弧形铭文 + 大号 ¥ | ¥（Fraunces serif）|

**实现**：每款写一个独立 QPainter 绘制函数，签名统一：

```python
def draw_kaiyuan(p: QPainter, cx: float, cy: float, radius: float, rot_cos: float):
    """在 (cx, cy) 处绘制开元通宝，外径 radius；rot_cos ∈ [-1, 1] 控制水平翻面缩放"""
```

5 款共用的辅助函数：`_draw_square_hole(p, size)` / `_draw_rim_reeds(p, r)` / `_draw_laurel_sprig(p, side)`。

## 9. 到账大字规范

选型 **B · 巨字金光**（mockup 中）：

- **位置**：屏幕中央（`QScreen.availableGeometry().center()`）
- **字号**：约 `height * 0.16`（响应式，1080p 上约 170px）
- **字体**：`Fraunces`，weight 400，`font-variation-settings: "SOFT" 80, "WONK" 1`
- **颜色**：`#f7d14a` 金色，多层 `text-shadow` 等效的 `QGraphicsDropShadowEffect` 叠加（外 40px 金色柔光 + 近 6px 黑色投影）
- **¥ 符号**：字号为主数字的 0.46 倍，vertical-align 向上偏移
- **中文副标「今日到账」/「当前已到账」**：位于主数字下方，`Noto Serif SC` 500 字重、letter-spacing 0.6em，黑色投影
- **时序**：
  - `t=0.0s`：副标淡入 + 主数字从 0 count-up
  - `t=1.0s`：count-up 结束（1.0 秒 ease-out 到目标值）
  - `t=1.0s`：金币开始下落
  - `t≈5.5s`：动画结束、进程退出

- **count-up 实现**：`QTimer` 驱动 60 FPS，每帧更新 `self.current_amount = ease_out(t/1.0) * target`，`paintEvent` 重绘数字。

## 10. 任务计划规范

### 注册（单次模式）

```
schtasks /Create /F /TN CoinRainDaily /SC DAILY /ST 17:00 ^
  /TR "\"<exe_path>\" --rain" /RL LIMITED
```

### 注册（多次模式 · N=3）

schtasks 支持一个任务下多个触发器，通过 XML 一次性创建：

```
schtasks /Create /F /TN CoinRainDaily /XML trigger.xml
```

`trigger.xml` 中包含 3 个 `<CalendarTrigger>`，每个 `<Arguments>` 分别是 `--rain --nth=1 --total=3` / `--rain --nth=2 --total=3` / `--rain --nth=3 --total=3`。

> 备选方案：建 3 个独立任务（`CoinRainDaily_1` / `_2` / `_3`），实现简单但 Manage 界面要查 N 个任务状态。采用主方案（单任务 + 多触发器）。

### 查询 / 启用 / 停用 / 卸载

```
schtasks /Query /TN CoinRainDaily /FO LIST /V     # 查询详情
schtasks /Change /TN CoinRainDaily /DISABLE       # 停用
schtasks /Change /TN CoinRainDaily /ENABLE        # 启用
schtasks /Delete /F /TN CoinRainDaily             # 卸载
```

`Scheduler.status()` 返回：`{"exists": bool, "enabled": bool, "next_run": datetime | None}`。ManageWindow 启动时调用此接口交叉验证 config 与实际任务。

## 11. 错误处理

仅在 4 个边界处理，业务内部不加 try/except。

| 边界 | 处理 |
|---|---|
| UI 表单输入 | 提交前校验（收入正整数、时间格式 HH:MM、多次 N∈[2,12]、first<last 且差值 ≥ N-1 分钟）；不合法时字段红色下划线 + 禁用保存 |
| Config.load() | `FileNotFoundError` / `JSONDecodeError` / `TypeError` 全返回 `None`，走首次配置流程（不自动备份损坏文件） |
| Scheduler subprocess | `subprocess.run` timeout=10s；`returncode != 0` 时 `raise SchedulerError(stderr)`；UI 层 catch 弹 QMessageBox + 重试 |
| 字体加载 | `QFontDatabase.addApplicationFont` 返回 -1 时不 raise，让 QSS fallback 到系统 serif |

## 12. 测试策略

### 手动 checklist（5 组）

- **① Setup**：首次双击 exe 打开 Setup 而非 Rain；4 字段默认值正确；多次模式切换时字段展开；非法输入红线；「先试一下」子进程不影响父 UI；「保存并启用」config + schtasks 双写成功
- **② Manage**：再次双击打开 Manage；摘要与 config 一致；计数、下次预告正确；停用/启用 schtasks 状态随动；修改配置覆盖旧任务
- **③ Rain**：先 1s count-up 再落币；单次 / 多次 nth<total / nth==total 三种文案正确；5 款金币渲染正常；混合下落视觉合理；结束无僵尸窗口
- **④ 任务计划**：单次 1 触发器、多次 N 触发器；触发器命令行带 --nth/--total；/F 覆盖无脏数据
- **⑤ 打包**：build.bat 后 exe 约 45–50 MB；干净 Windows VM（无字体）上 UI 仍正常；音效仍能播

### 单元测试（3 个小 pytest）

成本低、收益高的纯函数：

```python
# tests/test_logic.py
def test_config_roundtrip(tmp_path): ...
def test_distribute_times(): ...   # _distribute_times("09:30","17:30",3) == ["09:30","13:30","17:30"] 等
def test_compute_amount(): ...     # 单次 / 多次 / 边界 (nth=total)
```

不测 subprocess mock、不测 Qt 渲染、不测定时精度。

## 13. 打包与分发

### build.bat 变更

- 新增 `--add-data "assets/fonts/*.ttf;assets/fonts"`
- `--add-data` 已包含 wav，不变
- 预期 exe 体积：当前 44 MB → 约 46–50 MB（字体 ~2–3 MB）

### PyInstaller spec 变更

`coin_rain.spec` 的 `datas=[...]` 补充字体条目；`hiddenimports` 无变化。

### 首次运行的资源查找

沿用 `resource_path()` 兼容 dev 态（`__file__` 同级 `assets/`）和 onefile 态（`sys._MEIPASS`）。字体路径：`resource_path("assets/fonts/Fraunces.ttf")`。

## 14. 实施阶段

按"小步快跑 + 每阶段可打包"原则分 3 阶段，每阶段结束时有可用的 exe：

### 阶段 1：到账大字（最快见效）

- 修改 `coin_rain.py`（或先重构为 `rain_window.py`）
- 新增到账大字 count-up 图层
- 先 1 秒出字、之后落币的时序调整
- **暂不**改 UI、**暂不**改任务计划；金额硬编码常量
- 阶段结束：exe 可跑，动画里已经有大字

### 阶段 2：配置 + 管理 UI

- 拆文件：`__main__.py` / `config.py` / `config_window.py` / `rain_window.py`
- 实现 `SetupWindow` + `ManageWindow`（editorial 米白金风）
- 字体嵌入 + QSS 样式表
- `Config.load/save` + 双击 exe 分流逻辑
- "先试一下" 子进程打开 RainWindow
- **暂不**动任务计划（仍用老的 install_schedule.ps1）；"保存并启用" 暂时只写 config.json
- 阶段结束：exe 双击打开 UI；动画仍靠老脚本定时

### 阶段 3：多次触发 + 任务计划动态注册

- 实现 `scheduler.py`（schtasks 封装）
- `_distribute_times` + `_compute_amount` 纯函数
- SetupWindow 保存 → scheduler.register() 写任务计划
- ManageWindow 启用/停用开关、状态查询
- 多次模式的 XML 触发器生成
- 金币样式 5 款 + 混合下落
- 3 个小 pytest
- 阶段结束：完整功能闭环

## 15. Out of Scope

以下**不在本次**设计范围：

- 跨平台（macOS / Linux）—— 仍仅 Windows
- 多屏支持（当前只在主屏）
- 自动更新机制
- 托盘菜单 / 开机自启的 UI 开关（暂靠任务计划，不启动托盘）
- 历史到账记录 / 统计
- 在线商店、付费版、许可证
- "完全卸载"按钮（用户手动删 exe + 跑 uninstall_schedule.ps1 即可）

## 16. 验收标准

阶段 3 完成时满足以下条件即视为交付：

1. 在干净 Windows 11 VM（未装 Python、未装 Fraunces / 思源宋体）上：
   - 双击 `coin_rain.exe` 打开 SetupWindow，UI 字体为 Fraunces + 思源宋体
   - 完成配置后任务计划里出现 `CoinRainDaily` 任务
   - 到点触发 → 先 1s 大字 → 金币雨 → 音效 → 自动退
2. 单次模式和多次模式（N=3）均按预期
3. ManageWindow 的停用 → 任务不再触发；启用后恢复
4. 5 款金币样式都能正确渲染；开启混合下落时金币视觉有多样性
5. 3 个 pytest 全绿
6. 手动 checklist 5 组全部通过

---

**附录：设计过程中的 mockup 归档**

`.superpowers/brainstorm/853-*/content/` 目录下保留了以下验证过的 mockup：

- `config-form-v3.html` — SetupWindow 定稿（米白金 editorial · 960×600 横屏）
- `manage-v1.html` — ManageWindow 定稿
- `amount-display-v1.html` — 到账大字 3 选 1，最终选 B 巨字金光
- `coin-designs-v1.html` — 金币 6 款初版
- `coin-fixes-v2.html` — D/F 修订（F 已弃用）

---

_本 spec 由 brainstorming 技能在 2026-04-16 与用户逐段确认后定稿。实施计划由 writing-plans 技能接续生成。_
