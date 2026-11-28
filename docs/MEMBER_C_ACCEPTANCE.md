# 成员 C · 首发验收表

每条记录包含构建号、测试环境、步骤、结果及截图或日志。本期没有真机，全部在 DevEco Studio 模拟器上验收；镜像无法覆盖的 PC 专属行为按未测记录。

**状态约定**：`待验` 未开始；`通过` 已留证；`部分通过` 核心路径已验证，但仍有明确边界或缺陷未满足完整预期；`失败` 有缺陷单；`未测` 环境不覆盖，需在记录里写原因。

## 环境

| 项目 | 值 | 记录人 | 日期 |
|---|---|---|---|
| HAP（D4） | `com.caneda.desktop` 1.0.0，SHA-256 `1eb50c2796ac9685d44f31c72bc575d6102da0df4b088c35598078b0827f0b19`，32,039,938 字节，未签名调试包。**仅用于** A4、A6、A7、A8、B1–B7、D4 | 成员 C | 2026-11-27 |
| HAP（D3） | `com.caneda.desktop` 1.0.0，SHA-256 `d5970a8bc0b13c662ca4ec8ad82460395b560838a4c6af0d4537bb4e3b353122`，32,028,826 字节，未签名调试包。**仅用于** A2、A5、C1、D2、D3 | 成员 C | 2026-11-26 |
| HAP（D5 final） | `com.caneda.desktop` 1.0.0，SHA-256 `e18dea274b17489dc0331236aa8a1befe5751af9cc3c837c8169e68f9c49a756`，32,047,426 字节，未签名调试包。保留系统选择器入口并新增应用存储入口后的重建包，**用于** A5（另存）、D3（文件选择回调）、D5 | 成员 C | 2026-11-28 |
| Qt for HarmonyOS | 5.15.16，源码标签 `4af606551a1ca1f91869284eb13650b2204d7161`，x86_64 交叉构建 | 成员 C | 2026-11-26 |
| Qwt | 6.1.6，x86_64 交叉构建，源码 SHA-256 `99460d31c115ee4117b0175d885f47c2c590d784206f09815dc058fbe5ede1f6` | 成员 C | 2026-11-26 |
| 模拟器镜像 / API / ABI | HarmonyOS 7.0.0.107，API 26，x86_64，2in1（MateBook Pro） | 成员 C | 2026-11-24 |
| 模拟器版本 / hdc | Emulator 26.0.0.400 / hdc 3.2.0f | 成员 C | 2026-11-24 |
| 桌面 ngspice 版本 | ngspice-47 | 成员 C | 2026-11-24 |
| 样例校验脚本 | `tests/files/verify_samples.py` | 成员 C | 2026-11-24 |

## A. 工程读写

| # | 用例 | 步骤 | 预期 | 状态 | 证据 |
|---|---|---|---|---|---|
| A1 | 新建并保存 | 新建原理图，放置元件，保存到应用可写目录 | 生成 `.xsch`，无错误提示 | 待验 | 本次未执行新建、放置元件并保存；D3 的保存来自打开既有 RC 样例后另存，不能作为 A1 证据，见 A5 与 `docs/MEMBER_C_D3_SAVE_REOPEN.md` §2 D3-3 |
| A2 | 保存后重开 | 关闭文档，重新打开 A5 另存的 RC 样例副本 | 元件、连线、属性值与保存前一致 | **通过**（D3 包） | 应用内实测（A5 另存副本）：标题栏、元件 R1=1k、C1=1u、脉冲源四参数与 Sim1 两条指令保存前后逐项一致。证据来自 **D3 包**（`d5970a8b`），D4 未复测本项。[08-reopened](evidence/c-d3/08-reopened.jpeg) |
| A3 | 覆盖保存 | 修改属性后再次保存，再重开 | 新值生效，旧值不残留 | 待验 | 本次未执行修改属性后覆盖保存；D3 只完成 A5 另存，不能作为 A3 证据，D4 补 |
| A4 | 退出重启后打开 | 保存后退出应用，重启再打开 | 文件仍可打开，内容一致 | **通过** | 结束应用进程后重启（PID 7621→12031），从系统文件选择器重开已保存文件；RC 元件、连线、属性值与仿真指令完整。文件名因 D3 使用默认后缀而为 `.xsch`，不影响本用例。[重启后](evidence/c-d4/a4-restarted.jpeg) · [打开选择器](evidence/c-d4/a4-open-picker2.jpeg) · [重开结果](evidence/c-d4/a4-reopened-after-restart.jpeg) · [D4 记录](MEMBER_C_D4_WRITE_CANCEL_CORRUPT.md) |
| A5 | 另存为 | 另存到不同路径，打开新文件 | 新文件可独立打开 | **通过**（D3 包 + D5 最终包） | D3 包：另存后新文件出现在系统选择器并可独立打开（[04-save-as-dialog](evidence/c-d3/04-save-as-dialog.jpeg) · [07-open-dialog-saved-file](evidence/c-d3/07-open-dialog-saved-file.jpeg)）。D5 最终包 `e18dea27…`：`File > Save as...` 走系统保存对话框写入共享位置，`File > Save as to App Storage...` 写入应用私有目录并可重开。[共享位置另存](evidence/c-d5/d5-p1-saveas-shared-done.jpeg) · [D5 记录 §4](MEMBER_C_D5_SAMPLES_ACCEPTANCE.md) |
| A6 | 只读/无权限路径 | 保存到不可写路径 | 有明确失败提示，应用不崩溃 | **通过** | 对包内只读路径执行保存，弹出 `Cannot save document!`，关闭后进程仍存活。错误提示闭环的重复空框问题在 A8 单独记录。[只读保存失败](evidence/c-d4/a6-save-readonly.jpeg) · [D4 记录](MEMBER_C_D4_WRITE_CANCEL_CORRUPT.md) |
| A7 | 保存取消 | 在文件对话框中取消 | 文档保持未修改状态，无残留文件 | 部分通过 | 已验证：取消系统保存对话框后，标题、标签页和画布内容均不变，应用不崩溃。未验证：保存目标目录是否残留临时/空文件——媒体目录对 shell 不可读，未做目录级核验，该项保留待验。[保存对话框](evidence/c-d4/a7-save-as-dialog2.jpeg) · [取消后](evidence/c-d4/a7-after-save-cancel.jpeg) · [D4 记录](MEMBER_C_D4_WRITE_CANCEL_CORRUPT.md) |
| A8 | 保存失败提示 | 构造写入失败（如磁盘满或路径失效） | 提示可读，可继续编辑 | 部分通过 | **已验证的是打开失败路径**：对包内只读目标执行保存时 `QFile::open` 失败，首个 `Cannot save document!` 可读；关闭后又出现标题为文件路径、正文为空的重复错误框，关闭后应用仍可操作（缺陷 C-D4-01）。**未验证写入/关闭失败路径**（打开成功后 `stream << text` 或 `file.close()` 失败）：需构造磁盘满或目标被替换，仍待验，判据为错误提示可读、撤销栈不清空且文档仍标为已修改、原文件不被截断（承接 D2-8）。[空错误框](evidence/c-d4/a8-save-error-detail.jpeg) · [错误后仍可操作](evidence/c-d4/a8-after-error-still-responsive.jpeg) · [D4 记录](MEMBER_C_D4_WRITE_CANCEL_CORRUPT.md) |

## B. 损坏与异常输入

| # | 用例 | 步骤 | 预期 | 状态 | 证据 |
|---|---|---|---|---|---|
| B1 | 空文件 | 打开 0 字节 `.xsch` | 报错并安全返回，不崩溃 | **通过** | 显示 `Premature end of document.`，关闭后应用继续可用。[空文件错误](evidence/c-d4/b1-empty-pkg.jpeg) |
| B2 | 截断 XML | 打开写到一半的 `.xsch` | 报错并安全返回 | **通过** | 显示 `Premature end of document.`，应用未崩溃。[截断 XML 错误](evidence/c-d4/b2-truncated.jpeg) |
| B3 | 非法根元素 | 根元素不是 `caneda` | 提示"不是 Caneda 文件" | **通过** | 显示 `Not a caneda file or probably malformatted file`。[非法根元素错误](evidence/c-d4/b3-wrong-root.jpeg) |
| B4 | 版本过高 | `version` 高于 0.4.0 | 拒绝打开并提示 | **通过** | 2026-11-28 补测：`io.qt.appArgsJson` 日志明确指向 `future-version.xsch`，界面显示 `Xml parse error / Not a caneda file or probably malformatted file`，进程 PID 6859 保持存活。[截图](evidence/c-d5/b4-future-version-d5.jpeg) · [日志](evidence/c-d5/b4-future-version-d5-hilog.log) · [D5 记录](MEMBER_C_D5_SAMPLES_ACCEPTANCE.md) |
| B5 | 未知元件 | 引用库中不存在的元件名 | 跳过该元件并告警，其余正常 | **通过** | 跳过 `NoSuchPart`，其余 `V1/R1/C1/Sim1` 正常显示；持久化日志记录 `Warning: Found unknown element "NoSuchPart" , skipping...`。[工程仍打开](evidence/c-d4/b5-unknown-component.jpeg) · [持久化日志](evidence/c-d4/b5-b6-b7-persist-hilog.log) |
| B6 | 缺库符号 | 库路径不可达 | 有明确提示，不崩溃 | **部分通过** | 缺失 `MissingLib` 中的 `Voltage Source Pulse` 被跳过，其余元件正常显示且不崩溃；但界面无提示，仅日志告警。已登记 C-D4-02。[工程仍打开](evidence/c-d4/b6-missing-library.jpeg) · [持久化日志](evidence/c-d4/b5-b6-b7-persist-hilog.log) · [D4 记录](MEMBER_C_D4_WRITE_CANCEL_CORRUPT.md) |
| B7 | 悬空连线 | 打开含未连接引脚的工程 | 正常打开，网表跳过未连接节点 | **部分通过** | 工程打开且悬空线段可见。仿真在网表生成前被 `Missing simulator backend...` 拦截，网表跳过未连接节点未实测；源码推导见 D4 记录 §5。[工程打开](evidence/c-d4/b7-dangling-wire.jpeg) · [仿真尝试](evidence/c-d4/b7-simulate-attempt.jpeg) · [D4 记录](MEMBER_C_D4_WRITE_CANCEL_CORRUPT.md) |

## C. 样例端到端

| # | 用例 | 步骤 | 预期 | 状态 | 证据 |
|---|---|---|---|---|---|
| C1 | RC 样例打开 | 打开 `tests/files/samples/rc-lowpass/rc-lowpass.xsch` | 4 个元件与连线正确显示 | **通过**（D3 包） | HAP 内实测：`in` 端口、`R1 = 1k`、`C1 = 1u`、脉冲源 `PW=20m / V1=0 / V2=5 / per=40m`、`Sim1 tstep=10u tstop=7m` 全部正确渲染。证据来自 **D3 包**（`d5970a8b`），D4 未复测本项。[02-open-rc-sample](evidence/c-d3/02-open-rc-sample.jpeg) |
| C2 | RC 样例编辑 | 修改 R1 为 2 kΩ 后保存重开 | 值持久化。注意本用例把时间常数改为 2 ms，只用于验证读写，不作为 C3 的仿真输入 | 待验 | |
| C3 | RC 样例仿真 | 重新打开**未修改**的 `rc-lowpass.xsch`（不要沿用 C2 改过 R1 的文件），运行仿真 | 波形为 1 ms 时间常数的上升曲线（R1 = 1 kΩ、C1 = 1 µF） | 待验 | |
| C4 | 整流样例打开 | 打开 `tests/files/samples/diode-rectifier/diode-rectifier.xsch` | 5 个元件与连线正确显示 | 待验 | |
| C5 | 整流样例仿真 | 运行仿真 | 输出约 9 V，纹波约 0.36 V 峰峰 | 待验 | |
| C6 | 仿真失败后恢复 | 构造仿真失败（如移除库路径） | 有失败提示，仍可继续编辑与保存 | 待验 | |

## D. 平台与安装

| # | 用例 | 步骤 | 预期 | 状态 | 证据 |
|---|---|---|---|---|---|
| D1 | 干净安装 | 卸载后重新安装候选包 | 安装成功，可启动 | 部分通过 | 覆盖安装成功并可启动；未先卸载，干净安装待 D15 候选包阶段执行 |
| D2 | 安装后首次启动 | 首次启动应用 | 窗口正常，无崩溃 | **通过**（D3 包） | 主窗口、菜单栏、元件面板与画布正常；首版因缺 `libQt5OpenGL.so` 启动即崩，补齐后稳定。证据来自 **D3 包**（`d5970a8b`）；D4 包沿用同一 `libcaneda.so` 与库集合，但未单独留启动截图。[01-launch](evidence/c-d3/01-launch.jpeg) |
| D3 | 文件选择回调 | 通过平台桥接选择样例文件 | 能拿到路径并打开 | **通过**（D3 包 + D5 最终包） | D3 包：系统选择器选中文件可打开，`io.qt.appArgsJson` 启动参数亦能把路径传入 `main()`（[07-open-dialog-saved-file](evidence/c-d3/07-open-dialog-saved-file.jpeg)）。D5 最终包 `e18dea27…`：`File > Open...` 仍走系统选择器，成功打开共享目录中的外部工程 `rc-lowpass-d5.xsch`（[系统选择器](evidence/c-d5/d5-p1-open-system-picker.jpeg) · [打开结果](evidence/c-d5/d5-p1-external-opened.jpeg)） |
| D4 | 文件选择取消 | 在系统文件对话框中取消 | 应用收到取消状态，不崩溃 | **通过** | 系统打开对话框取消后返回原文档，标签页与画布内容保持，应用不崩溃。[取消后](evidence/c-d4/d4-cancel-open.jpeg) · [D4 记录](MEMBER_C_D4_WRITE_CANCEL_CORRUPT.md) |
| D5 | 沙箱路径 | 在应用可写目录读写样例 | 读写均成功 | **通过** | 最终 HAP `e18dea27…` 用 `File > Save as to App Storage...` 在私有目录 `/data/app/el2/100/base/com.caneda.desktop/files` 写出**新副本** `rc-lowpass-d5.xsch`（修改时间 2026-11-28 14:20，3575 字节，SHA-256 `c1f46aebd0f8168d2f87a1f44e309d0b994973654ec3ae7a93f35a8d52afeaaf`）；结束进程并重启（PID 2885→7213）后，用 `File > Open from App Storage...` 打开该副本，内容完整。同一 HAP 上系统选择器入口仍可用（见 A5 与 D5 记录 §4.2）。[文件检查](evidence/c-d5/d5-p2-file-check.log) · [保存对话框](evidence/c-d5/d5-p2-appstorage-saveas-dialog.jpeg) · [重开结果](evidence/c-d5/d5-p2-reopen-private.jpeg) · [D5 记录](MEMBER_C_D5_SAMPLES_ACCEPTANCE.md) |

### D5 辅助观察

| 编号 | 观察项 | 结果 | 证据 |
|---|---|---|---|
| D5-O1 | 包内 `resfile` 读取 | 通过。元件库与 RC 样例均从 `/data/storage/el1/bundle/entry/resources/resfile/caneda/` 加载。 | [01-launch](evidence/c-d3/01-launch.jpeg) · [02-open-rc-sample](evidence/c-d3/02-open-rc-sample.jpeg) |
| D5-O2 | 系统文件选择器保存 | 通过。通过系统选择器将当前文档另存为副本，保存后标题与标签页更新。 | [04-save-as-dialog](evidence/c-d3/04-save-as-dialog.jpeg) · [05-after-save](evidence/c-d3/05-after-save.jpeg) |

D5 的最终通过依据是上表中的应用私有 `files` 目录保存与重开闭环；上述两项保留为包内资源读取和系统选择器路径的辅助证据。

## 桌面基线（D1、D5）

无 GUI 环境下的样例回归，用于确认样例本身仍有效。D5 于 2026-11-28 重新执行并归档结果：

| 项目 | 结果 | 证据 |
|---|---|---|
| RC 样例网表生成 | 通过，719 点 | `verify_samples.py` |
| RC 数值对照 | 通过，最大偏差 0.000398 V（容差 0.01 V） | 闭式解对照 |
| 整流样例网表生成 | 通过，6008 点 | `verify_samples.py` |
| 整流数值对照 | 通过，最大偏差 0.094 V（容差 0.3 V） | ngspice-47 |
| 几何连通性 | 通过，无悬空线端 | 连线端点检查 |

桌面基线不等于 HAP 验收。上表只能说明样例文件本身正确、Python 生成的网表通过数值对照。

以下各项未由桌面基线覆盖，仍按 A–D 组用例在模拟器上待验：

- Caneda 自己打开工程文件并正确显示元件与连线（C1、C4）。
- Caneda 自己从原理图导出网表（C3、C5），而不是由 `verify_samples.py` 生成。
- Caneda 自己调用 ngspice 运行仿真并显示波形（C3、C5）。
- 界面操作、保存后重开与退出重启（A 组、C2）。

## 模拟器环境预检（2026-11-24）

本机 DevEco Studio 已可启动 MateBook Pro 模拟器，用于确认后续验收的环境前提。以下结果只覆盖设备与文件系统层，**不含 Caneda 应用本身**。

| 项目 | 结果 | 证据 |
|---|---|---|
| 模拟器启动 | 通过 | Emulator 26.0.0.400，`hdc list targets` 返回 `127.0.0.1:5555` |
| 设备类型 / ABI | 2in1，x86_64 | `const.product.devicetype`、`const.product.cpu.abilist` |
| 系统版本 / API | HarmonyOS 7.0.0.107，API 26 | `const.product.software.version` |
| 沙箱写读 | 通过 | `/data/local/tmp` 建目录、写 13 字节、读回一致 |
| 只读路径保护 | 通过 | 写 `/system` 返回 Read-only file system |
| 样例文件下发 | 通过 | 两套样例经 `hdc file send` 传至模拟器，MD5 与本地一致 |
| 样例回传解析 | 通过 | 回传的 `rc-lowpass.xsch` 仍解析为 4 元件、8 连线、3 端口 |

### D4 后仍未覆盖

D4 已完成 A4、A6、A7、A8、B1–B7 与 D4 的模拟器实测，结果和边界见 `docs/MEMBER_C_D4_WRITE_CANCEL_CORRUPT.md`。以下项目仍未覆盖：

- A1、A3：新建并保存、修改属性后覆盖保存。
- 用户自定义文件名保存；本轮默认后缀生成的文件名为 `.xsch`。
- 保存中断后的文件完整性，以及保存目标目录的字节级/残留文件校验。
- B7 的实际网表生成与未连接节点跳过；本包缺少仿真后端。
- C2–C6（样例编辑、仿真、失败恢复）。
- D1 的干净安装（需先卸载）。
- A8 重复空错误框和 B6 缺库无界面提示需修复后复测。

## 缺陷清单

| # | 日期 | 用例 | 现象 | 严重度 | 负责人 | 状态 |
|---|---|---|---|---|---|---|
| C-D4-01 | 2026-11-27 | A8 | 保存失败首个提示关闭后，再次弹出标题为文件路径、正文为空的错误框；`FormatXmlSchematic::save()` 失败时未回填 `errorMessage` | 中 | 待分配 | 待修复 |
| C-D4-02 | 2026-11-27 | B6 | 缺失库元件仅写日志并被跳过，界面无缺库提示 | 中 | 待分配 | 待修复 |

静态审查另有 5 项待复核发现（R1–R5），见 `docs/MEMBER_C_D2_WRITE_REOPEN.md` §4。均未在 HAP 内复现，确认后再进入本表。

## 待补验项

- A1 新建并保存、A3 修改属性后覆盖保存。
- 用户自定义文件名保存（模拟器输入法授权页阻断文本注入，见 `docs/MEMBER_C_D3_SAVE_REOPEN.md` §4）。
- A7 的「保存目录无残留文件」核验（系统媒体目录对 shell 不可读）。
- A8 的写入/关闭失败分支：打开成功后 `stream << text` 或 `file.close()` 失败时的提示、撤销栈与文档状态、原文件完整性（承接 D2-8）。
- 保存中断后的文件完整性，以及保存后文件的字节级校验（保存目标经系统文件访问框架落盘，`/storage/media/100/local/files` 对 shell 不可读）。
- B7 的实际网表生成与未连接节点跳过（本包缺少仿真后端）。
- C2–C6 样例编辑、仿真与失败恢复。
- D1 干净安装（候选包阶段执行）。
- A8 重复空错误框、B6 缺库无界面提示修复后复测。
- 非 ASCII 标签的保存与重开（保存编码依赖系统 locale，见 D2 记录 R4）。
- PC 窗口尺寸、键鼠行为与真机行为本期不覆盖，按计划记录。
