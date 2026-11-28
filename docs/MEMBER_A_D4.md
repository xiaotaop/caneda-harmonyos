# 成员 A · D4 元件放置与连线

2026-11-27。在 Windows Caneda 0.4.0 中，从空白原理图放置一个电阻和一个电容，连接两者内侧引脚并保存，桌面对照通过。鸿蒙 PC 模拟器上的同组编辑操作待取得团队 D4 调试 HAP 后补验。

## 操作与验收

| 操作 | 本次观察 |
|---|---|
| 在 Components Browser → Passive 中选 Resistor，点击格点 (-80, 0)，按 Esc。再选 Capacitor，点击 (80, 0)，按 Esc。 | 放置 R1 和 C1。初始四个端口各自独立，画布没有导线。 |
| 点击工具栏 Wire，依次点击 R1 右端 (-60, 0) 和 C1 左端 (60, 0)，按 Esc。 | 只留下一条水平导线。对每个端点检查运行中 Caneda 的连接列表，组件端口与对应导线端口互相包含。最外侧两个端口仍只有自身。[截图](evidence/a-d4/wired.png) · [运行记录](evidence/a-d4/wiring.json) |
| 保存图纸，并从磁盘独立读取 XML。 | 两个元件的位置、方向、编号以及单条导线的两个端点均符合上表。[Caneda 实际保存的图纸](evidence/a-d4/d4-rc.xsch) |

从仓库根目录运行 `python tests/schematic/d4/check_saved.py docs/evidence/a-d4/d4-rc.xsch` 可复核保存结果。本次另用副本将导线终点从 (60, 0) 改为 (50, 0)，检查器拒绝了短一格的导线。图中有意保留两个外侧开路端口，用于观察和核对连接状态。

## 桌面复跑

被测应用沿用 [D1 桌面构建](https://github.com/xiaotaop/caneda-harmonyos/pull/5)，源码 `e0c11869`，Windows x86-64，Qt 5.15.2，Qwt 6.1.6，应用 SHA-256 为 `1486d753c933fa27334e03124454cdad5d24b613def64f6064d737ab89d6dd43`。测试用 Qt Test 将键鼠操作发给顶层窗口，使用同一 ABI 的 Caneda 头文件读取连接关系。[测试源码](../tests/schematic/d4/probe.cpp)

1. 在空构建目录，使用匹配的 Qt 5.15.2 和 MinGW-w64 GCC 8.1.0，运行 `qmake <仓库>/tests/schematic/d4/probe.pro -spec win32-g++ "CANEDA_BUILD=<含 config.h 的 Caneda 构建目录>" CONFIG+=release`，再运行 `mingw32-make -f Makefile.Release`。
2. 新建空输出目录，将绝对路径设为 `CANEDA_D4_OUTPUT`。在该目录新建 `d4-rc.xsch`，内容为 `<?xml version="1.0"?><!DOCTYPE caneda><caneda version="0.4.0"><components/><ports/><wires/></caneda>`。该图会被填入元件和连线。
3. 将 Qt 和编译器的 bin 加入 PATH，设置 `QT_QPA_PLATFORM=windows`，`QT_PLUGIN_PATH` 为本次构建的 plugins 和 Qt 安装目录的 plugins，以分号分隔。从应用程序目录运行 `caneda.exe -plugin caneda_d4 "<输出目录>/d4-rc.xsch"`。
4. 检查退出码为 0、`wiring.json` 中的 `error` 为空，再对输出目录中的 `d4-rc.xsch` 运行上述 XML 检查器。本次两项均通过。

## 鸿蒙 PC 模拟器复测

使用[团队 D4 调试包](https://github.com/xiaotaop/caneda-harmonyos/pull/13)时，记录实际 HAP 的 SHA-256、模拟器机型、系统/API 和 ABI。从新图依次执行表中的面板选择、放置和连线动作，以状态栏的场景坐标定位。截取带 R1、C1、内侧导线和外侧空端口的画布，将图纸另存到可写位置。从模拟器取回该文件，用同一 XML 检查器核对；记录键鼠操作、截图和检查输出。当前桌面记录的坐标可直接用于对照。
