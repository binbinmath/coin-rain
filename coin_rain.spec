# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec —— 体积优化版。

PySide6 默认会把整个 Qt 运行时（含 Quick/QML/Pdf/OpenGL/Network 等）打进 exe，
~25 MB 的 DLL 我们一行代码都没用。--exclude-module 只挡 Python 层导入，DLL 还在；
所以这里在 Analysis 之后显式过滤 a.binaries / a.datas，把整个不需要的子树扔掉。
"""

EXCLUDED_QT_PYMOD = [
    "PySide6.QtNetwork",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtSpatialAudio",
    "PySide6.QtSql",
    "PySide6.QtBluetooth",
    "PySide6.QtSerialPort",
    "PySide6.QtSensors",
    "PySide6.QtPositioning",
    "PySide6.QtNfc",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebSockets",
    "PySide6.QtWebChannel",
    "PySide6.QtRemoteObjects",
    "PySide6.QtTest",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuickWidgets",
    "PySide6.QtQuick3D",
    "PySide6.QtScxml",
    "PySide6.QtStateMachine",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DRender",
    "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic",
    "PySide6.Qt3DAnimation",
    "PySide6.Qt3DExtras",
    "PySide6.QtConcurrent",
    "PySide6.QtDesigner",
    "PySide6.QtHelp",
    "PySide6.QtUiTools",
    "PySide6.QtTextToSpeech",
    "PySide6.QtLocation",
    "PySide6.QtAxContainer",
    "PySide6.QtHttpServer",
    "PySide6.QtOpenGL",
    "PySide6.QtOpenGLWidgets",
    "PySide6.QtSvgWidgets",   # 我们不用 QSvgWidget；QtSvg DLL 仍保留以防 QSS 渲染需要
]

# 这些 Qt DLL/插件没有被我们直接用，但 PySide6 默认会全打进去
QT_DLL_DROP_PATTERNS = [
    "Qt6Quick", "Qt6Qml", "Qt6QmlModels", "Qt6QmlMeta", "Qt6QmlWorkerScript",
    "Qt6Pdf",
    "Qt6Network",
    "Qt6OpenGL",
    "Qt6Multimedia", "Qt6SpatialAudio",
    "Qt6Sql",
    "Qt6Bluetooth", "Qt6SerialPort", "Qt6Sensors", "Qt6Positioning", "Qt6Nfc",
    "Qt6WebEngine", "Qt6WebSockets", "Qt6WebChannel",
    "Qt6RemoteObjects", "Qt6Test",
    "Qt6Charts", "Qt6DataVisualization",
    "Qt6Quick3D",
    "Qt6Scxml", "Qt6StateMachine",
    "Qt63D",
    "Qt6Concurrent",
    "Qt6Designer", "Qt6Help", "Qt6UiTools",
    "Qt6TextToSpeech", "Qt6Location",
    "Qt6HttpServer",
    "Qt6VirtualKeyboard",
    "Qt6OpenGLWidgets",
    "Qt6SvgWidgets",
    "Qt6PrintSupport",  # 我们不打印
    "Qt6Xml",           # QSS 不依赖
]

# Qt 插件（platforms/imageformats 等）没用到的也一起扔
QT_PLUGIN_DROP_DIRS = [
    "qml", "Qml",                  # QML modules
    "scxmldebugger",
    "multimedia",
    "position",
    "sensors",
    "geoservices",
    "sqldrivers",
    "tls",                          # 网络 TLS
    "networkinformation",
    "designer",
    "iconengines",                  # 我们没图标引擎
    "imageformats/qpdf.dll",        # PDF 图片
    "imageformats/qsvg",            # SVG 图片
    "imageformats/qtga",
    "imageformats/qtiff",
    "imageformats/qwbmp",
    "imageformats/qwebp",
    "imageformats/qicns",
    "imageformats/qico",            # 不显示 ico
    "generic",                      # 通用输入插件
    "platforminputcontexts",        # IME（用不到 Qt 自带 IME）
    "virtualkeyboard",
]


def _should_drop(path_in_pkg: str) -> bool:
    p = path_in_pkg.replace("\\", "/").lower()
    for pat in QT_DLL_DROP_PATTERNS:
        if pat.lower() in p:
            return True
    for d in QT_PLUGIN_DROP_DIRS:
        if d.lower() in p:
            return True
    return False


a = Analysis(
    ['coin_rain.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets/coin_drop.wav', 'assets'),
        ('assets/slot_spin.wav', 'assets'),
        ('assets/赞赏码.jpg', 'assets'),
        # 只打包 subset 字体（项目用到的字符），不要 -VariableFont（24M 全量）
        ('assets/fonts/Fraunces-Subset.ttf', 'assets/fonts'),
        ('assets/fonts/NotoSerifSC-Subset.ttf', 'assets/fonts'),
        ('assets/coins', 'assets/coins'),
        ('style.qss', '.'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDED_QT_PYMOD,
    noarchive=False,
    optimize=0,
)

# 显式从 binaries 和 datas 中过滤掉用不到的 Qt 子树
a.binaries = [b for b in a.binaries if not _should_drop(b[0])]
a.datas = [d for d in a.datas if not _should_drop(d[0])]

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='金币雨',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico',
)
