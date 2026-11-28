# 成员 B · 仿真与波形执行计划

目标是在同一个首发 HAP 中，从 Caneda 原理图生成网表、运行包内 ngspice、显示 RC 和二极管整流波形，并保留可复跑的数值和错误恢复证据。团队在 DevEco Studio 模拟器上验收。主分支由组长合并，B 审核 A 的 PR，B 的 PR 由 C 审核。

| 日期 | 成员 B 的工作和验收证据 |
|---|---|
| 11/24–11/25（D1–D2） | 盘点当前调用链、依赖和输出格式。运行固定 RC 网表，记录版本、原始波形和解析解对照。 |
| 11/26–11/30（D3–D7） | 按组长确认的 ABI 交叉编译。用 HAP 从沙箱工作目录启动包内 CLI，并检查退出状态、日志和有效 RAW。若 Qt 子进程不可用或系统拒绝启动，验证同 ABI 的 libngspice 进程内方案。11/30 两条路线均未取回 RC 波形时，按总计划请求全组支援。 |
| 12/01–12/04（D8–D11） | 接入 Caneda 生成的网表，复用现有波形视图。跟 A 验证入口和运行状态，跟 C 对齐 RC／整流的工程、节点、模型和检查点。在同一 Alpha 包上记录波形数据、错误提示和失败后重试结果。 |
| 12/05–12/07（D12–D14） | 归档日志和模拟器覆盖；在功能冻结前完成两套样例数值对照。 |
| 12/08–12/14（D15–D21） | 在候选包复跑两套样例、连续运行和失败后重试。修复仿真阻断，12/10 提供功能与限制说明，最终归档包号、模拟器镜像、API、ABI 和验证日志。 |

## D1 盘点

盘点基线为团队仓库导入的 Caneda [e0c11869](https://github.com/Caneda/Caneda/commit/e0c11869cd0282c4d30c78c7d976b09271050214)，版本 0.4.0。

| 环节 | 已有实现 | 首发工作 |
|---|---|---|
| 发起仿真 | [MainWindow::simulate](../src/mainwindow.cpp#L676) 调用文档的仿真方法。[SchematicDocument::simulate](../src/idocument.cpp#L511) 从 `.xsch` 导出网表。[TextDocument::simulate](../src/idocument.cpp#L1404) 支持打开 SPICE 网表直接运行。 | 保留原理图入口，先用固定网表隔离引擎、打包和读回问题。 |
| 网表和调用 | [FormatSpice::save](../src/fileformats.cpp#L1075) 把 `.net` 写在工程同目录；[设置](../src/settings.cpp#L77) 默认是 `ngspice -b -r %filename.raw %filename.net`。QProcess 以工程目录为 cwd 写同名 `.log` 和 `.raw`。 | 用包内绝对路径和独立参数；用应用可写目录隔离每次运行，并为样例保留明确的相对模型解析路径。与 C 确认工程输入由哪里交给仿真。 |
| 完成和失败 | 原理图路径当前有同步的 `ngspice -v` 查找，忽略了 `FormatSpice::save()` 返回值；完成回调只收退出码，默认使用当前工程名字找 RAW。 | 验证 Qt/系统能否起子进程；将导出失败、启动失败、非零退出或崩溃、超时、缺失或坏 RAW 分开处理。回调使用启动时的运行目录，连续运行和失败重试不读旧结果。 |
| 结果和波形 | [FormatRawSimulation](../src/fileformats.cpp#L1525) 读取 ASCII 或小端 double 的二进制 RAW，创建 `ChartSeries`；[ChartScene](../src/chartscene.cpp#L37) 和 [ChartView](../src/chartview.cpp) 依赖 Qwt。默认输出二进制。当前 loader 在文件能打开时即报告加载成功，对截断和多 plot 的处理需要验证。 | 包内探针先用 ASCII 检查真实瞬态结果，Caneda 接入后验证实际波形视图。从单 plot、秒与伏特起步，检查解析错误能返回给界面。 |
| 构建与分发 | [CMake](../CMakeLists.txt) 要求 Qt5 Widgets、Svg、PrintSupport、LinguistTools 和 Qwt ≥ 6.1.2，Caneda 没有链接 ngspice。 | 与组长核对鸿蒙 Qt/Qwt ABI。ngspice 核对 ELF 架构、动态依赖以及运行期脚本或 code model 是否需要入包。向 C 提供实际启用组件的版本、许可证与 notices。Caneda 仓库根目录的 `COPYING` 是 GPLv2 全文；ngspice 47 的源码包另有 `COPYING`，包含 Modified BSD 和部分组件适用的其他许可，构建脚本将其暂存为 `NGSPICE-COPYING`。 |

### 包内探针的判定

1. 组长提供可安装调试 HAP 和实测用的镜像、API、ABI；B 记录同一包的构建号和 ngspice 版本。
2. 在 HAP 进程内把本目录记录的 [RC 网表](../tests/simulation/rc-step.cir) 放到应用可写目录。用绝对路径和独立 argv 尝试包内 CLI，捕获启动错误、退出码、stdout/stderr，读回实际 RAW。仅有交叉编译产物或 HDC shell 里运行成功均不能证明应用内调用成功。
3. 用 `check_rc.py --raw` 对读回文件做解析和数值校验。若 CLI 失败，保留原始错误，再尝试同 ABI 的 `libngspice`，核对动态装载、`ngSpice_Init`／`ngSpice_Circ`／`ngSpice_Command` 和向量返回；仿真放到工作线程、按次串行并拷贝数据后再交给界面。
4. A 在集成阶段验证“仿真中／完成／失败”的界面状态。C 和 B 共同确定整流样例的电路、模型、输出节点和稳态检查点。最终在同一个 HAP 中验收两套原理图保存重开并显示波形，再故意使一次仿真失败并恢复。

## 桌面 RC 对照

`rc-step.cir` 是固定的引擎探针，与 [rc-lowpass 原理图样例](../tests/files/samples/rc-lowpass/rc-lowpass.xsch) 使用相同的脉冲源、1 kΩ 电阻、1 µF 电容和瞬态配置。固定网表用于隔离引擎运行和读回；样例路径用于检查原理图、库符号和网表连接。固定网表检查器读取 ASCII transient RAW 的 `time` 与 `v(out)`，按样例的五个检查时刻比较有限上升沿的解析解，容差统一为 3 mV。中间检查点使用线性插值，7 ms 使用结束点。

```sh
# 先将 ngspice 加入 PATH，或替换成安装后的可执行文件绝对路径。
work=$(mktemp -d)
python3 tests/simulation/check_rc.py --ngspice ngspice --output "$work/rc desktop"
python3 tests/simulation/check_rc.py --raw "$work/rc desktop/rc-step.raw"
```

运行输出目录必须是新目录，避免把已有 RAW 误认为本次结果。ngspice 缺失时不会创建目录；引擎启动后若失败，保留日志供排查。后续需实测 Caneda 生成的网表、波形视图和保存重开。

### 11/24 首次桌面对照记录

在 Apple Silicon macOS 上，从 [ngspice 47 源码包](https://sourceforge.net/projects/ngspice/files/ng-spice-rework/47/ngspice-47.tar.gz/download) 构建。源码 SHA-256 为 `894e649651f1838a14095e5a5439e7d3aa63e87ede14d283173fda4fcdef675f`。配置参数为 `--without-x --disable-osdi --disable-openmp --with-fftw3=no --with-readline=no`，保留默认 XSPICE 和 KLU。

| 时刻 | ngspice | 解析解 | 绝对误差 |
|---|---:|---:|---:|
| 0.500 ms | 0.000000 V | 0.000000 V | 0.000000 V |
| 2.001 ms | 3.161533 V | 3.161522 V | 0.000011 V |
| 4.001 ms | 4.751195 V | 4.751189 V | 0.000006 V |
| 6.001 ms | 4.966328 V | 4.966327 V | 0.000001 V |

运行生成 719 点。运行模式和读取已有 RAW 模式均通过。检查器拒绝截断数据、能解析但波形错误的数据，以及复用已有输出目录；用新目录重跑结果一致。此记录覆盖桌面 ngspice CLI 和固定网表，Caneda UI、HAP 与模拟器内调用待验。

### 11/25 D2 样例对照

使用同一 ngspice 47 复跑固定网表，并由仓库的样例工具从 `rc-lowpass.xsch` 生成网表后执行仿真。

```sh
python3 tests/files/verify_samples.py --ngspice ngspice --keep rc-lowpass
```

| 入口 | 采样 | 五个检查点 |
|---|---:|---|
| 固定网表，插值后对解析解 | 719 点 | 全部通过，最大误差约 22 µV |
| 原理图样例，最近采样点对 `expected.json` | 719 点 | 全部通过，最大误差约 0.398 mV |

逐点比较两份 RAW，719 个时间值和 `v(out)` 值完全一致。两份报告的检查点误差不同，因为固定网表插值到目标时刻，样例工具读取最近的实际采样点。本轮样例网表来自 Python 测试工具，Caneda C++ 网表导出与 HAP 内仿真等待集成测试。

11/28 D5 已归档固定网表、桌面样例和 arm64 HAP 的原始 RC 波形及复核命令。[D5 RC 对照归档](MEMBER_B_D5.md)

参考 [ngspice 源码发布页](https://ngspice.sourceforge.io/download.html)、[ngspice Shared Library](https://ngspice.sourceforge.io/shared.html) 和 [Qt 5.15.16 鸿蒙移植说明](https://wiki.qt.io/Qt_for_HarmonyOS/Qt5.15.16_Open_Source_Release_for_HarmonyOS)。
