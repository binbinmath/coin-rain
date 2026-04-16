# 金币雨桌面彩蛋

每天下午 **17:00** 自动在屏幕上播放约 4.5 秒的金币下落动画，伴随"哗啦啦"瀑布音效。

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
   或直接双击 `dist\coin_rain.exe`。

## 卸载

右键 `uninstall_schedule.ps1` → 使用 PowerShell 运行（会清掉 `CoinRainDaily` 和 `CoinRainTest` 两个任务，如果都存在）。
（exe 和源码不会被删除，想彻底删除手动删 `E:\Onedrive\Claude\Coin` 文件夹即可。）

## 调参

想改数量/时长/颜色/字符？打开 `coin_rain.py`，顶部有 `========== 可调参数 ==========` 区块。改完重新双击 `build.bat` 重打包。

| 想要 | 改哪个常量 |
|---|---|
| 金币更多 | `COIN_COUNT_MIN/MAX` 调大 |
| 动画更久 | `GRAVITY` 调小 或 `VY_INIT_MAX` 调小 |
| 换符号 | `COIN_SYMBOL = "$"` / `"元"` / `"¢"` |
| 换颜色 | `COIN_FILL_CENTER` / `COIN_FILL_EDGE` |
| 换时间 | 编辑 `install_schedule.ps1` 里的 `-At '17:00'`，重跑 install |
| 换音效 | 覆盖 `assets/coin_drop.wav`（单声道 WAV），重跑 `build.bat` |

## 文件说明

| 文件 | 作用 |
|---|---|
| `coin_rain.py` | 主程序源码 |
| `assets/coin_drop.wav` | 4 秒金币瀑布音效（代码合成，CC0） |
| `build.bat` | 一键打包脚本 |
| `install_schedule.ps1` | 注册每日 17:00 任务 |
| `uninstall_schedule.ps1` | 卸载任务 |
| `dist/coin_rain.exe` | 打包产物（约 44 MB） |
| `docs/` | 设计文档和实施计划 |

## 排错

- **双击 exe 没反应**：在 cmd 里运行 `dist\coin_rain.exe`，看有无报错；首次启动会有 1-2 秒解压延迟（PyInstaller onefile 的正常表现）
- **没声音**：确认系统音量没静音；确认 `assets\coin_drop.wav` 能用播放器打开；若仍无声，重跑 `build.bat` 重打包
- **17:00 没触发**：打开「任务计划程序」，查找 `CoinRainDaily`，看「上次运行结果」；确认触发时你处于**登录状态**（未登录不触发）
- **窗口不透明或无法穿透**：Windows 版本过低（需 Win10+），或显卡驱动异常
