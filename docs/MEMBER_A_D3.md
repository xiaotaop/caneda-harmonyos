# 成员 A · D3 画布、元件面板与键盘焦点

2026-11-26，Windows 桌面对照通过。鸿蒙 PC 模拟器上的同组操作待验。D2 已核对鼠标选择电阻、格点落点与画布选中状态。D3 从空白原理图出发，检查键盘输入能否依次交给搜索框、结果树、画布，再回到搜索框。

| 操作 | Windows 实测结果 |
|---|---|
| 在 Components Browser 的搜索框输入 `capacitor` | 搜索框取得焦点。结果树包含 Capacitor，原来的 Resistor 行被过滤。 |
| 在搜索框按 ↓，再用 ↓ 移到 Passive → Capacitor，按 Enter | 第一次 ↓ 把焦点交给结果树。键盘选中了 Capacitor，按 Enter 后可在画布放置。[结果树截图](evidence/a-d3/01-search.png) |
| 在画布格点 (40, 30) 单击一次，按 Esc | 焦点在画布，场景中有且仅有一个元件，坐标为 (40, 30)。 |
| 再点搜索框，按 Ctrl+A，将内容替换为 `resistor` | 搜索框重新取得焦点。结果树显示 Resistor，Capacitor 行被过滤。画布上原来的电容 C1 仍在原处。[最终窗口](evidence/a-d3/02-return.png) |

**复核环境。** Caneda 0.4.0，固定源码 `e0c11869`，Windows x86-64，Qt 5.15.2，Qwt 6.1.6。沿用 [D1 的 Ninja Multi-Config Release 构建](https://github.com/xiaotaop/caneda-harmonyos/pull/5)，本次核对应用 SHA-256 为 `1486d753c933fa27334e03124454cdad5d24b613def64f6064d737ab89d6dd43`。测试插件使用配套 MinGW-w64 GCC 8.1.0 构建，SHA-256 为 `9e82396f7613aabc6fc7ef4ab7fd0b3f658b0e16ea9d04d875d92caea9b9d0aa`。

**桌面复跑。** 人工复核按表中顺序操作即可。自动复核使用[测试插件](../tests/schematic/d3/probe.cpp)，Qt Test 把键鼠事件发给已激活的顶层窗口，由应用分发。使用 Qt 5.15.2 和配套 MinGW，将两者的 bin 加入 PATH，在空构建目录运行 `qmake <源码目录>/tests/schematic/d3/probe.pro -spec win32-g++ CONFIG+=release` 和 `mingw32-make -f Makefile.Release`。在同一进程环境中设置下列变量，再从已安装元件库的 Caneda 程序目录运行 `caneda.exe -plugin caneda_d3`。

| 环境变量 | 值 |
|---|---|
| QT_PLUGIN_PATH | 构建目录下的 plugins 与 Qt 安装目录下的 plugins，使用绝对路径，以分号分隔 |
| QT_QPA_PLATFORM | windows |
| CANEDA_D3_OUTPUT | 已创建的空目录绝对路径，用于独立配置、两张 PNG 和 focus.json |

本次进程退出码为 0，[运行记录](evidence/a-d3/focus.json) 的 `error` 为空。

**模拟器补验。** 团队在 MateBook Pro 模拟器上已打开[组长的最小 Qt Widgets 窗口](../platform/harmonyos/README.md)。[该入口](../platform/harmonyos/main.cpp)只显示 QLabel。[成员 B 的 D3 包](https://github.com/xiaotaop/caneda-harmonyos/pull/10)验证了 ngspice 包内调用。成员 A 的补验需要能打开原理图、加载 Passive 元件库的调试 HAP。取得包后记录构建号、HAP SHA-256、模拟器机型、系统/API 和 ABI，用模拟器窗口的键鼠按上表复测，保留键盘选中电容及返回搜索框后的两张截图，并记录首次偏离预期的动作。
