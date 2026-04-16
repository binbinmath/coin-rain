# 金币雨桌面彩蛋 · 设计文档

- **日期**：2026-04-15
- **项目路径**：`E:\Onedrive\Claude\Coin`
- **作者**：与 Claude Code 协作产出

---

## 1. 目标与场景

每天下午 17:00 在用户电脑的主屏幕上自动播放一段 **2-3 秒的金币下落动画**，伴随一次金币落地音效。作为一天工作尾声的小彩蛋，**不打断用户当前工作**（透明置顶 + 鼠标穿透）。

## 2. 核心需求

| 维度 | 决定 |
|---|---|
| 触发方式 | 每天 17:00 自动（Windows 任务计划程序） |
| 显示方式 | 全屏透明悬浮窗，鼠标穿透，位于所有窗口之上 |
| 时长与强度 | 约 2.5 秒，30-50 枚金币，分 3 批释放 |
| 素材来源 | 金币代码绘制；音效使用 CC0 免费素材 |
| 交互 | 无（无按钮、无配置界面，自动开自动关） |
| 运行环境 | Windows 11，Python 3.11.4（已具备） |

## 3. 整体架构

```
Windows 任务计划程序 (每天 17:00, 用户登录时)
        ↓ 调用
   coin_rain.exe   ←─ PyInstaller 打包自 coin_rain.py
        ↓ 启动
   PySide6 透明置顶窗口 (主屏幕全覆盖)
        ↓
   ┌─ 渲染循环 (~60 FPS, QTimer 驱动)
   │   · 分批生成 30-50 个金币对象
   │   · 每帧更新位置/旋转，QPainter 绘制
   │   · 金币落出屏幕底部即移除
   │
   ├─ 音频: 启动时播放一次 coin_drop.wav (QSoundEffect)
   │
   └─ 全部金币消失 → 窗口关闭 → 进程退出
```

### 关键技术点
1. **窗口属性组合**：
   `FramelessWindowHint | WindowStaysOnTopHint | Tool | WA_TranslucentBackground | WA_TransparentForMouseEvents`
   含义：无边框 + 置顶 + 不占任务栏 + 背景透明 + 鼠标事件穿透到下方窗口。
2. **打包**：PyInstaller `--onefile --windowed --add-data` 把音效嵌入单个 exe。
3. **调度**：Windows Task Scheduler，通过 PowerShell 脚本一键注册/卸载，无需手动点 GUI。

## 4. 目录结构

```
E:\Onedrive\Claude\Coin\
    ├── coin_rain.py              # 主程序源码，约 150-200 行
    ├── assets\
    │    └── coin_drop.wav        # 金币落地音效（CC0，~30-80 KB）
    ├── requirements.txt          # PySide6、pyinstaller
    ├── build.bat                 # 一键打包：pip install → PyInstaller 打包
    ├── install_schedule.ps1      # 注册每日 17:00 任务计划
    ├── uninstall_schedule.ps1    # 卸载任务计划
    ├── README.md                 # 使用说明（给人类）
    ├── CLAUDE.md                 # 项目说明（给未来的 AI 协作者）
    ├── 制作过程.md                # 本次完整交付过程流水账
    ├── docs\
    │    └── 2026-04-15-coin-rain-design.md   # 本文件
    └── dist\
         └── coin_rain.exe        # 打包产物
```

## 5. 动画与视觉细节

### 5.1 金币外观（QPainter 绘制，无需图片）

| 属性 | 取值 |
|---|---|
| 形状 | 圆形 |
| 直径 | 40-56 px 随机 |
| 填充 | 径向渐变：中心 `#FFE066` → 边缘 `#D4A017` |
| 描边 | 1 px `#8B6914` |
| 中心字符 | **¥**，加粗，深棕 `#5C4A0A` |
| 阴影 | 金币下方柔和黑色模糊光斑，透明度 30% |
| 旋转 | 水平方向缩放 `abs(cos(angle))` 模拟硬币自转翻面；每枚角速度随机 |

### 5.2 下落物理

| 参数 | 取值 |
|---|---|
| 生成位置 | `y = -60`，`x = random(0, screen_width)` |
| 初始 vx | 随机 -80 ~ +80 px/s（轻微斜向） |
| 初始 vy | 随机 200 ~ 400 px/s |
| 重力 g | 900 px/s² |
| 生成节奏 | 开场 0.3 秒内**分 3 批**释放（每批 10-17 枚） |
| 移除条件 | `y > screen_height` |
| 总时长 | 约 2.5 秒（最后一枚落出屏幕即退出） |

### 5.3 音效

- **文件**：`assets/coin_drop.wav`（CC0 许可，来自 freesound.org 或 pixabay）
- **时机**：程序启动时**播放一次**（30-50 枚同时叮当会变噪音，故不按枚触发）
- **音量**：70%
- **引擎**：`QSoundEffect`（低延迟，适合短音；比 QMediaPlayer 更合适短效场景）

## 6. 部署流程（用户侧三次双击）

1. 双击 `build.bat` → 自动 `pip install PySide6 pyinstaller` 并打包出 `dist\coin_rain.exe`
2. 右键 `install_schedule.ps1` →「使用 PowerShell 运行」→ 过 UAC → 注册完成
3. （可选）双击 `dist\coin_rain.exe` 立即测试效果；想卸载调度：右键 `uninstall_schedule.ps1`

## 7. 任务计划配置

| 项 | 值 |
|---|---|
| 任务名 | `CoinRainDaily` |
| 触发器 | 每天 17:00:00 |
| 动作 | 运行 `E:\Onedrive\Claude\Coin\dist\coin_rain.exe` |
| 只在用户登录时运行 | 是 |
| 要求 AC 电源 | 否（笔电拔电池也触发） |
| 唤醒计算机执行任务 | 否（睡眠则跳过，不补播） |
| 任务已运行时重复启动 | 否（防止重入） |

## 8. 错误与边界处理（YAGNI，只做必要的）

| 场景 | 处理 |
|---|---|
| 音效文件缺失 | 静默跳过，继续动画 |
| 屏幕分辨率 | `QGuiApplication.primaryScreen().geometry()` 自适应 |
| 多显示器 | 只在**主屏**播放 |
| 17:00 时程序已运行 | 任务计划禁止重复实例 |
| 17:00 时关机/睡眠 | 跳过，不补播 |
| 首次运行首包解压 | PyInstaller `--onefile` 首启动延迟 1-2 秒，可接受 |

## 9. 明确不做（YAGNI）

- ❌ 托盘图标 / 配置 GUI
- ❌ 暂停 / 跳过按钮
- ❌ 日志文件
- ❌ 自动更新机制
- ❌ 多屏同时播放
- ❌ 每枚金币单独音效

如需调整参数（数量、时长、颜色、字符），直接编辑 `coin_rain.py` 顶部的常量区，重跑 `build.bat` 即可。

## 10. 交付物清单

完成时应具备：
- [x] 本设计文档
- [ ] `coin_rain.py` 源码
- [ ] `assets/coin_drop.wav` 音效
- [ ] `build.bat` 打包脚本
- [ ] `install_schedule.ps1` / `uninstall_schedule.ps1`
- [ ] `requirements.txt`
- [ ] `README.md`（给人类的使用说明）
- [ ] `CLAUDE.md`（给未来 AI 的项目说明）
- [ ] `制作过程.md`（本次完整流水账）
- [ ] 打包后的 `dist\coin_rain.exe`
- [ ] 任务计划已注册并能按 17:00 触发
