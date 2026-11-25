# 成员 A · D1 桌面基线

**2026-11-24 验收通过。** 从团队固定标签构建了 Caneda 0.4.0，在 Windows 桌面启动主窗口并新建了第二张空白原理图。左侧元件面板能找到电阻与电容。这组截图可供鸿蒙端对照。

| 项目 | 取值 |
|---|---|
| 团队仓库 | [xiaotaop/caneda-harmonyos](https://github.com/xiaotaop/caneda-harmonyos) |
| 构建源码 | 标签 `caneda-upstream-base`，提交 `e0c11869cd0282c4d30c78c7d976b09271050214` |
| 工作分支 | `feature/a-schematic` |
| 运行环境 | Windows x86-64，Qt 5.15.2，Qwt 6.1.6 |
| 构建工具 | CMake 3.30.2，Ninja 1.12.1；生成器 `Ninja Multi-Config`，`CMAKE_CONFIGURATION_TYPES=Release`，构建与安装均指定 `--config Release` |
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

复现时，从固定标签导出源码。用 Qt 5.15.2 的 `qmake src.pro -spec win32-g++ CONFIG+=release` 在 Qwt 6.1.6 的 `src` 目录生成 Makefile，以 `mingw32-make -f Makefile.Release` 构建库。

固定标签的 `CMakeLists.txt` 第 42 行确实设置了 `CMAKE_BUILD_TYPE Debug`。本次没有修改或临时覆盖该行，使用的是 **Ninja Multi-Config**：配置由 `CMAKE_CONFIGURATION_TYPES` 和构建时的 `--config` 选择。原说明漏写了生成器；仅给单配置 Ninja 传入 `-DCMAKE_BUILD_TYPE=Release` 不能复现本次配置。参见 [CMake 多配置生成器说明](https://cmake.org/cmake/help/latest/generator/Ninja%20Multi-Config.html)。

下面为原构建命令的参数化写法。先把 `$src`、`$build`、`$prefix` 分别设为固定标签的源码目录、全新的构建目录和安装目录；`$qt` 为 Qt 5.15.2 前缀，`$gcc` 为 MinGW 8.1.0 的 bin 目录，`$qwt` 为已构建的 Qwt 6.1.6 目录。将编译器与 Qt 的 bin 目录加入当前进程 PATH 后执行：

```powershell
cmake -S "$src" -B "$build" -G "Ninja Multi-Config" `
  -DCMAKE_CONFIGURATION_TYPES=Release `
  "-DCMAKE_CXX_COMPILER=$gcc/g++.exe" "-DCMAKE_C_COMPILER=$gcc/gcc.exe" `
  "-DCMAKE_PREFIX_PATH=$qt" "-DCMAKE_INSTALL_PREFIX=$prefix" `
  "-DQWT_INCLUDE_DIR:PATH=$qwt/src" "-DQWT_LIBRARY:FILEPATH=$qwt/lib/libqwt.a" `
  "-DCMAKE_INCLUDE_PATH=$qwt/src" "-DCMAKE_LIBRARY_PATH=$qwt/lib" `
  "-DCMAKE_EXE_LINKER_FLAGS=-Wl,--dynamicbase,--nxcompat"
cmake --build "$build" --config Release --parallel 6
cmake --install "$build" --config Release
```

[构建配置证据](evidence/a-d1/build-config.txt) 包含原始构建日志中的配置、构建与安装命令，以及现存缓存、Ninja 生成的完整 `main.cpp` 编译命令和对应 `.ninja_log` 完成记录。有效参数为 `-O3 -DNDEBUG`，对象路径为 `src/CMakeFiles/caneda.dir/Release/main.cpp.obj`。2026-11-25 复核确认构建目录中的 `CMakeLists.txt` 与固定标签内容一致（仅归一化 CRLF），应用 SHA-256 仍与 D1、D2 记录一致。本次补充证据没有重建或更换被测应用。

Windows 版在应用清单中声明进程使用 UTF-8。在下列两个文件所在目录执行 `windres -i windows-utf8.rc -O coff -o caneda-utf8.o`，将生成的对象加入 Caneda 可执行文件的链接输入即可。[Windows 应用清单](evidence/a-d1/windows-utf8.manifest) · [资源脚本](evidence/a-d1/windows-utf8.rc) · [Microsoft 的进程代码页说明](https://learn.microsoft.com/en-us/windows/apps/design/globalizing/use-utf8-code-page)

## 人工复核

1. 在 Windows 桌面启动本次构建的 `caneda.exe`。确认出现主窗口、原理图编辑区和元件浏览器。
2. 点击工具栏“新建”，在 **New File** 对话框选中 **Schematic file** 并确认。
3. 确认新增一个原理图标签，画布上没有放置元件或导线。在左侧 **Components** 元件树内找到 **Resistor** 和 **Capacitor**。

基线通过 CMake 的 `CMAKE_INSTALL_PREFIX` 确定元件库、图片等资源路径。复核时从原安装位置启动。在另一台机器上复现时，按该机的安装路径重新配置、构建并安装。
