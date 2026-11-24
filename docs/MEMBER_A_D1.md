# 成员 A · D1 桌面基线

**2026-11-24 验收通过。** 从团队固定标签构建了 Caneda 0.4.0，在 Windows 桌面启动主窗口并新建了第二张空白原理图。左侧元件面板能找到电阻与电容。这组截图可供鸿蒙端对照。

| 项目 | 取值 |
|---|---|
| 团队仓库 | [xiaotaop/caneda-harmonyos](https://github.com/xiaotaop/caneda-harmonyos) |
| 构建源码 | 标签 `caneda-upstream-base`，提交 `e0c11869cd0282c4d30c78c7d976b09271050214` |
| 工作分支 | `feature/a-schematic` |
| 运行环境 | Windows x86-64，Qt 5.15.2，Qwt 6.1.6 |
| 构建工具 | CMake 3.30.2，Ninja 1.12.1，Release 配置 |
| 编译与链接 | MinGW-w64 GCC 8.1.0 编译 Caneda 和 Qwt。最终由 GCC 14.2.0 驱动 GNU ld 2.43 链接同一批 Caneda 目标文件，并嵌入 Windows UTF-8 应用清单 |

## 验收记录

| 操作 | 实测结果 | 证据 |
|---|---|---|
| 启动程序 | 主窗口显示一个 `Untitled` 标签、原理图画布和已填充的 Components Browser | [启动截图](evidence/a-d1/01-startup.png) |
| 从工具栏新建文件 | **New File** 对话框显示并选中 **Schematic file** | [对话框截图](evidence/a-d1/02-new-dialog.png) |
| 确认新建 | 标签从一个变为两个，活动视图 `Caneda::GraphicsView` 已切换到新场景，用户绘制项为 0 | [新建后的画布](evidence/a-d1/03-new-schematic.png) |
| 检查元件面板 | 展开 `Components / Passive`，可见 `Resistor` 和 `Capacitor`，两项均可在运行中的元件树中定位 | [运行时记录](evidence/a-d1/desktop.json) |

另以普通启动方式打开了相同的可执行文件，窗口标题为 `Untitled - Caneda`，可从主窗口正常关闭。[构建记录与可执行文件 SHA-256](evidence/a-d1/build.json)

## Windows 编码与构建复现

首次启动时，`amplifier.xsym` 和 `opamp.xsym` 报解析错误，元件面板只显示内置工具。固定版的 `FormatXmlSymbol::load()` 通过 `QTextStream` 读取这些 UTF-8 文件。本机使用 Windows 代码页 936。用 Qt 5.15.2 逐一读入 107 个符号文件时，默认编码出现 9 个 XML 解析错误，显式选择 UTF-8 后为 0。已逐一核对安装的符号文件与固定标签导出的内容，Windows 导出的换行为 CRLF。

复现时，从固定标签导出源码。用 Qt 5.15.2 的 `qmake src.pro -spec win32-g++ CONFIG+=release` 在 Qwt 6.1.6 的 `src` 目录生成 Makefile，以 `mingw32-make -f Makefile.Release` 构建库。配置 Caneda 时向 CMake 提供 Qt 前缀、`QWT_INCLUDE_DIR`、`QWT_LIBRARY` 和 `CMAKE_INSTALL_PREFIX`，以 Release 配置构建并安装运行资源。

Windows 版在应用清单中声明进程使用 UTF-8。在下列两个文件所在目录执行 `windres -i windows-utf8.rc -O coff -o caneda-utf8.o`，将生成的对象加入 Caneda 可执行文件的链接输入即可。[Windows 应用清单](evidence/a-d1/windows-utf8.manifest) · [资源脚本](evidence/a-d1/windows-utf8.rc) · [Microsoft 的进程代码页说明](https://learn.microsoft.com/en-us/windows/apps/design/globalizing/use-utf8-code-page)

## 人工复核

1. 在 Windows 桌面启动本次构建的 `caneda.exe`。确认出现主窗口、原理图编辑区和元件浏览器。
2. 点击工具栏“新建”，在 **New File** 对话框选中 **Schematic file** 并确认。
3. 确认新增一个原理图标签，画布上没有放置元件或导线。在左侧 **Components** 元件树内找到 **Resistor** 和 **Capacitor**。

基线通过 CMake 的 `CMAKE_INSTALL_PREFIX` 确定元件库、图片等资源路径。复核时从原安装位置启动。在另一台机器上复现时，按该机的安装路径重新配置、构建并安装。
