# 金币雨 · 后续改进 TODO

> 创建日期：2026-04-16
> 用途：记录本项目后续的改进方向与规划项，供未来开发时参考与追踪。

## 改进项列表

### 1. 为对外发布做准备：同步记录制作过程

- **目标**：未来将此项目整理成可对外发布的开源/教程型内容。
- **要点**：
  - 每一次功能迭代、每一个关键决策，都应在制作过程中同步留档（延续 `制作过程.md` 的写法）。
  - 记录内容包括：遇到的问题、为什么这样选（比如为什么弃用 QSoundEffect）、踩坑过程、最终效果。
  - 输出物可以是：博客文章、视频脚本、GitHub README 展示部分。
- **落地方式**：
  - 每次合并一个 TODO 项时，先开一个 `制作过程-<主题>.md` 或追加到 `制作过程.md`。
  - 截图/录屏放到 `docs/assets/` 下，命名规范。

### 2. 金币雨中叠加「今日到账 XX 元」大字显示

- **目标**：金币掉落的同时，屏幕中央（或醒目位置）用大字显示当前到账金额，增强情绪反馈。
- **交互细节**：
  - 字体：大号、粗体、金色或带描边，和金币色调呼应。
  - 出现时机：与金币雨一起出现，可做一个数字滚动累加的动效（从 0 快速跳到目标金额）。
  - 单位：元（可配置）。
- **技术点**：
  - 在 `CoinRainWindow` 的 `paintEvent` 里用 `QPainter.drawText` 绘制。
  - 数字滚动用 `QTimer` 驱动，或直接在主动画循环里按时间插值。
  - 注意透明窗口下文字渲染的抗锯齿与描边叠加效果。

### 3. 首次使用的前端配置界面

- **目标**：第一次启动时弹出设置界面，用户自定义基本参数，之后按配置每日自动运行。
- **配置项**：
  - 每日收入（元）
  - 金币数量（或动画强度档位）
  - 显示时间段 & 显示次数：
    - 可以是「每天几点到几点之间显示 N 次」。
    - **仅 1 次**：文案为「今日到账 XX 元」（全天总额）。
    - **多次**：文案为「当前到账 XX 元」（按次数均摊的累计值）。
- **技术点**：
  - 设置界面独立于主动画窗口，可以是一个普通的 QWidget / QDialog（不透明、带标准边框）。
  - 配置持久化：写到 `%APPDATA%/CoinRain/config.json` 或 `~/.coinrain/config.json`。
  - 首次启动检测：若配置文件不存在则弹出设置向导；否则直接跑动画。
  - 时间段 + 次数要重新生成 Windows 任务计划（改 `install_schedule.ps1` 或在 Python 里直接调 `schtasks`）。
- **UI/样式**：
  - 用 **frontdesign 技巧/原则** 改善界面美观度（配色、排版、圆角、间距）。
  - 金币样式、到账大字样式也一并做一次视觉升级。

## 设计与实施产物

- **设计文档**：`docs/superpowers/specs/2026-04-16-coin-rain-config-ui-design.md`（brainstorming 已完成）
- **实施计划**：由 writing-plans 生成，路径见设计文档末尾追加

## 后续追踪

- 完成一项后，在本文件末尾追加"✅ 已完成：<日期> <简述>"。
- 若新增改进想法，继续往「改进项列表」追加编号小节。

---

## ✅ 已完成

- **2026-04-16 阶段 1**：到账大字 count-up（B 巨字金光风格）+ 先 1 秒出字再落币 + 默认金币换成开元通宝（附永乐/宣和/龙洋/现代¥ 共 5 款备选）。tag: `stage-1-complete`
- **2026-04-16 阶段 2**：editorial 米白金风 SetupWindow + ManageWindow；`%APPDATA%\CoinRain\config.json` 持久化；Fraunces + 思源宋体 TTF 嵌入 exe。tag: `stage-2-complete`
- **2026-04-16 阶段 3**：`scheduler.py` schtasks 封装（单次 1 任务 / 多次 N 独立任务带 `--nth/--total`）；ManageWindow 开关联动 schtasks；下次预告条基于 `scheduler.status()`；5 款金币 + 混合下落（配置里开 `mixed_coins`）。tag: `stage-3-complete`

**打包产物**：`dist/coin_rain.exe` 约 60 MB（比未加字体的 44 MB 增加 16 MB，主要来自 25 MB 的 Noto Serif SC 完整变体字体；未来可用 `fontTools subset` 裁剪到 <1 MB 大幅瘦身）。

**交付模块清单**：
- `coin_rain.py` — 入口 + argv 分流
- `rain_window.py` — CoinRainWindow + 5 款金币绘制 + 到账大字 count-up
- `config.py` — Config dataclass + 路径工具
- `config_window.py` — SetupWindow + ManageWindow
- `scheduler.py` — schtasks 封装 + 时间分布
- `fonts.py` — 字体加载
- `style.qss` — editorial 米白金 QSS 样式表
- `assets/fonts/*.ttf` — 嵌入字体
- `tests/test_logic.py` — 15 个 pytest，覆盖 `_compute_amount` / `Config.load/save` / `_distribute_times`
