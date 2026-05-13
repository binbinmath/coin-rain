# 金币雨 · Coin Rain

> 每天到点，电脑屏幕上「哗啦啦」掉一阵金币，中央弹出大字「今 日 到 账 ¥XXX」。3–6 秒后自动消失。
>
> 一张创可贴，给那些「钱已经不再让我有赚到了的感觉」的打工人。

![platform](https://img.shields.io/badge/platform-Windows%2010%2F11-blue)
![license](https://img.shields.io/badge/license-MIT-green)

---

## 它解决什么

工资制把每天的成就感打包、延迟、数字化，30 天后给你一个银行短信。
这个小工具想把那个「钱到手的瞬间」找回来——每天傍晚（或你自定义的任意时刻）在桌面上来一场金币雨 + 到账大字 + 真实的金属碰撞声。

- **透明置顶 + 鼠标穿透**：不会打断你手头任何工作，就 3 秒视觉覆盖
- **5 款金币随机混合**：开元通宝 / 永乐通宝 / 宣和通宝 / 壹圓龙洋 / 现代 ¥
- **count-up 大字到账**：从 ¥0 滚动到当日金额，老虎机式 reel 动画
- **多次模式**：可选每天一次（下班那一下）或分多次（早午晚阶梯）
- **零网络 / 零账号 / 零数据上传**：纯本地，关掉之后跟没存在过一样

## 下载与安装

### 方式一：直接下载 exe（推荐 · 不用装 Python）

到 [Releases](../../releases/latest) 页面下载 `金币雨.exe`，**双击即可**。

首次双击会弹出配置向导，填好日收入 / 雨势 / 触发时间，点「保 存 并 启 用」自动注册到 Windows 任务计划程序。之后每天到点自动播放。

再次双击 exe 进入管理窗口，可改配置 / 一键启停 / 先试一下。

### 方式二：从源码自己打包

需要 Windows 10/11 + Python 3.11+。

```bat
git clone https://github.com/<你的用户名>/coin-rain
cd coin-rain
build.bat
```

完成后产出 `dist\金币雨.exe`，双击使用即可。

## 卸载

打开管理窗口（双击 exe）→ 点「停 用」即可暂停每日触发。
彻底清除：管理窗口里没暴露删除按钮，可手动执行：

```powershell
schtasks /Delete /TN CoinRainDaily /F   # 单次模式
# 多次模式 N 次的话再清 CoinRainDaily_1 .. _N
Remove-Item "$env:APPDATA\CoinRain" -Recurse
```

然后删掉这个文件夹即可，无残留。

## 主要文件

| 文件 | 作用 |
|---|---|
| `coin_rain.py` | 入口，分发动画 / 配置 UI / 管理 UI |
| `rain_window.py` | 金币雨主窗口（含 5 款金币 PNG 混合下落、count-up 大字） |
| `config_window.py` | Setup / Manage 两个 UI 窗口 |
| `scheduler.py` | Windows 任务计划（`schtasks.exe` 封装） |
| `surprise.py` | 副标 / 幸运币 / 节日彩蛋等惊喜层 |
| `coin_rain.spec` | PyInstaller spec（含 Qt 子树裁剪，36 MB） |
| `build.bat` | 一键打包脚本 |
| `assets/` | 字体 / 金币 PNG / 音效 / 图标 |

## 调参

UI 里没暴露的参数，可以改源码再重打：

| 想要 | 改哪里 |
|---|---|
| 金币更大 / 更多 | `rain_window.py` 顶部常量 `COIN_DIAMETER_*`、`INTENSITY_PARAMS` |
| 雨势档位 | `INTENSITY_PARAMS`（4 档：light/medium/heavy/storm） |
| 换音效 | 覆盖 `assets/coin_drop.wav`（单声道 WAV），重跑 `build.bat` |
| 换图标 | 覆盖 `assets/icon.ico`，重跑 `build.bat` |
| 加新款金币 | 把 PNG 放进 `assets/coins/`，在 `rain_window.py` 的 `COIN_FILES` 加文件名 |

## 测试

```bat
python -m pytest tests/ -v
```

63 个单元测试，覆盖金额计算 / 配置持久化 / 时间分布 / 副标策略等纯逻辑。

## 已知限制

- 仅支持 **Windows 10/11**（依赖 `winsound` 标准库 + `schtasks.exe`）
- 仅在**主屏**播放
- 电脑**关机 / 睡眠**时不会补播
- exe 首次双击有 1–2 秒解压延迟（PyInstaller `--onefile` 特性）

## 排错

- **exe 双击没反应**：在 cmd 里跑一次 `dist\金币雨.exe`，看有无报错
- **没声音**：确认系统音量正常 + `assets\coin_drop.wav` 能用播放器打开
- **到点没触发**：打开「任务计划程序」搜索 `CoinRainDaily`，看「上次运行结果」；确认那个时刻你处于**已登录**状态
- **窗口不透明 / 鼠标无法穿透**：Windows 版本太旧（需 Win10+）

## 许可

MIT，详见 [LICENSE](LICENSE)。打包内嵌的字体 / 音效是各自原始作者的版权（OFL / CC0），详见 LICENSE 末尾的「第三方资源」一节。
