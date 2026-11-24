# 成员 A · D2 原理图窗口、画布与鼠标事件

2026-11-25。Windows 桌面对照通过，DevEco Studio 鸿蒙 PC 模拟器待测。此次交付覆盖单个电阻的面板选择、鼠标定位、对象选择与焦点交接。未发现需要修改产品源码的问题。

## 构建与环境

| 项目 | 实测值 |
|---|---|
| 团队分支及本次工作起点 | `feature/a-schematic`，`9b5b5e80` |
| 被测应用 | Caneda 0.4.0，`caneda-upstream-base`，源码 `e0c11869cd0282c4d30c78c7d976b09271050214` |
| Windows 构建 | D1 Release，x86-64，Qt 5.15.2，Qwt 6.1.6；本次复核 caneda.exe SHA-256 为 `1486d753c933fa27334e03124454cdad5d24b613def64f6064d737ab89d6dd43` |
| 测试环境 | Windows 11 25H2，构建 26200.9974，Qt 平台 windows，设备像素比 1，主窗口 1240 × 800 |
| 输入方式 | Qt Test 向运行中的 Caneda 顶层窗口发送鼠标移动、按下、释放和 Esc。由窗口把输入分发到侧栏或画布。 |

## 运行记录

| 操作 | 通过条件与本次观察 |
|---|---|
| 启动 Caneda，打开初始原理图 | 可见主窗口和 Caneda::GraphicsView，窗口内显示网格画布。 |
| 点击 Components → Passive → Resistor | 当前行变为 Resistor，树控件取得焦点。[面板截图](evidence/a-d2/01-panel.png) |
| 移动到目标格点，单击左键，按 Esc 结束连续放置 | 画布视口坐标 (346, 256) 映射为场景坐标 (40, 30)，Caneda 发出的坐标读数为 40 : 30。场景中恰有一个元件，实际位置 (40, 30)，点击后焦点已回到画布。 |
| 点击空白处，再点击电阻本体 | 空白处点击使选择集变空，再点击后同一个电阻的 isSelected() 为真，画布保持焦点。[选中截图](evidence/a-d2/02-selected.png) |

[Qt 运行记录](evidence/a-d2/interaction.json) · [探针源码](../tests/schematic/d2/probe.cpp)。坐标均为 Qt 逻辑单位。窗口布局变化后应复核同一场景格点，视口像素值可以变化。

## 复核方法

人工复核可直接照上表依次操作。点击前看状态栏的坐标，按 Esc 后确认只留下 R1；点击空白处及 R1，观察选择高亮变化。

自动复核使用同版本的桌面 Qt、与该 Qt 兼容的 MinGW、已安装资源的 Caneda，以及独立的临时构建目录和空输出目录。在构建目录用 Qt 5.15.2 的 qmake 读取 `tests/schematic/d2/probe.pro`，选择 `-spec win32-g++ CONFIG+=release` 后运行 `mingw32-make -f Makefile.Release`。将 Qt 与编译器 bin 加入当前进程 PATH，设置以下变量，再运行 `caneda.exe -plugin caneda_d2`。

| 环境变量 | 值 |
|---|---|
| QT_PLUGIN_PATH | 构建目录下的 plugins 和 Qt 安装下的 plugins 两个绝对路径，以分号分隔 |
| QT_QPA_PLATFORM | windows |
| CANEDA_D2_OUTPUT | 已创建的独立输出目录绝对路径 |

通过时进程退出码为 0，输出目录包含两张 PNG 和一份 error 为空的 interaction.json。本次交付复核在宿主环境使用 Qt 5.15.2 与 MinGW-w64 GCC 8.1.0，从空构建目录执行 qmake、moc、编译和链接，随后加载新生成的插件复测通过。截图和运行记录来自这次复测；被测 Caneda 可执行文件沿用上表所列构建。[插件构建记录与哈希](evidence/a-d2/build.json)

## 鸿蒙模拟器复测

工作区内尚未取得可识别为 Caneda 的调试 HAP。拿到包后登记应用构建号、HAP SHA-256、DevEco 模拟器机型、系统/API、ABI、显示缩放及输入方式。按上表顺序，从空白原理图开始，分别记录面板选择、格点落点、取消与重新选择、焦点返回的结果，并附同阶段截图。若某步失败，记录首次偏离预期的动作、坐标读数和界面状态。物理鼠标、高 DPI 和多屏行为本轮未覆盖。

## PR 交接

来源分支为 `test/a-d2-desktop`，由成员 B 审核。D1 已单独提交 [PR #5](https://github.com/xiaotaop/caneda-harmonyos/pull/5)，本 PR 暂以其 `feature/a-schematic` 分支为基底，只展示 D2 改动；D1 合入后再把本 PR 的目标分支调整为 `main`，由组长合并。改动涉及交互测试插件、构建记录、两张桌面截图、运行日志和本记录。测试插件只在显式加载时参与运行。回退时移除本次 D2 文档、证据和测试目录即可。PR 的模拟器结果应在取得 HAP 后补录。
