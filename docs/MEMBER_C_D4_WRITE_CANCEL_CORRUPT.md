# 成员 C · D4 读写取消与损坏文件（HAP 内实测）

日期：2026-11-27（D4）。执行环境：DevEco Studio 模拟器，MateBook Pro（2in1），HarmonyOS 7.0.0.107，API 26，x86_64。

本记录覆盖 A4、A6、A7、A8、B1–B7 与 D4。结论严格区分“工程能安全打开”和“网表/仿真行为已验证”：B7 只实测了工程打开，网表跳过悬空节点尚未实测；B6 虽能跳过失库元件继续打开，但没有用户可见提示，因此不记为完整通过。

## 1. 被测产物与环境

| 项目 | 值 |
|---|---|
| 包名 / 版本 | `com.caneda.desktop` 1.0.0 |
| HAP | `entry-default-unsigned.hap`，32,039,938 字节 |
| HAP SHA-256 | `1eb50c2796ac9685d44f31c72bc575d6102da0df4b088c35598078b0827f0b19` |
| `libcaneda.so` SHA-256 | `982cdb0097149bcd8bcc47e477110efd29c17fc54f1fdf9fac009d4b44e39592` |
| 模拟器 | MateBook Pro，HarmonyOS 7.0.0.107，API 26，x86_64 |
| hdc 目标 | `127.0.0.1:5555` |
| Qt / Qwt | Qt for HarmonyOS 5.15.16；Qwt 6.1.6，x86_64 交叉构建 |

本轮 HAP 在 D3 包基础上加入负例测试资源，元件库和测试文件均从应用包内资源目录加载：

`/data/storage/el1/bundle/entry/resources/resfile/caneda/testcases/`

测试时曾尝试直接从 `/data/local/tmp` 启动负例，但该目录不在应用沙箱可见范围内，应用显示 `Cannot load document...`。因此 B1–B7 的有效结果全部来自上面的包内 `resfile` 路径，不使用该次调试记录。包内目录只读，也用于构造 A6/A8 的写入失败。

## 2. 测试输入与完整性

负例源文件位于 `tests/files/corrupt/`。

| 文件 | 字节数 | SHA-256 |
|---|---:|---|
| `empty.xsch` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `truncated.xsch` | 1,081 | `0baf83a2cdb921c6da7b7ab0b8dd498ad5dfd44ed0363d040b98c6e0cef3ab98` |
| `wrong-root.xsch` | 80 | `caf18c0fcb1c39faf77ae96a6c8442479a34f48d38f0acd01299995d9e276079` |
| `future-version.xsch` | 2,162 | `4c70c97040dcfcefad062d46066ad2f2a79b33529f3ef6d6d50118adc73a4919` |
| `unknown-component.xsch` | 2,164 | `6cf06803d6789af4559089199629bd16ba944d20a7a0735b480f1b53e134fa61` |
| `missing-library.xsch` | 2,165 | `c78b8b7c440197c82ff1f6c1efedc293af7be2f879b8d927b34c16c9851bec5a` |
| `dangling-wire.xsch` | 2,202 | `7f032402d0573d1b0292409a4e748ab1b9fdf909e8c4533141a5edd3c8b4bcea` |

## 3. 结果总览

| 用例 | 结果 | 结论边界 |
|---|---|---|
| A4 退出重启后打开 | **通过** | 结束应用进程后重启，再打开同一文件，RC 内容完整 |
| A6 只读/无权限路径保存 | **通过** | 显示 `Cannot save document!`，应用不崩溃；重复提示问题单列于 A8 |
| A7 保存取消 | **通过** | 取消系统保存对话框后标题和画布内容不变；未做媒体目录级残留文件核验 |
| A8 保存失败提示 | **部分通过** | 首个提示可读；关闭后出现标题为路径、正文为空的重复错误框 |
| B1 空文件 | **通过** | `Premature end of document.`，安全返回 |
| B2 截断 XML | **通过** | `Premature end of document.`，安全返回 |
| B3 非法根元素 | **通过** | `Not a caneda file or probably malformatted file` |
| B4 版本过高 | **通过** | 拒绝打开并显示通用 XML 错误，应用不崩溃 |
| B5 未知元件 | **通过** | 跳过 `NoSuchPart`，其余元件正常显示，日志有告警 |
| B6 缺库符号 | **部分通过** | 跳过缺失元件并可打开，但只有日志告警，无界面提示 |
| B7 悬空连线 | **部分通过** | 工程打开且悬空线段可见；网表跳过未连接节点未实测 |
| D4 文件选择取消 | **通过** | 取消打开对话框后返回原文档，应用不崩溃 |

## 4. A 组：保存、重启与取消

### A4 退出重启后打开

步骤与结果：

1. 先通过系统保存对话框保存当前 RC 文档。
2. 结束 Caneda 应用进程后从桌面重新启动；测试时观察到进程 PID 从 `7621` 变为 `12031`。
3. 重新启动后通过系统文件选择器打开刚保存的文件。

重开后标题、标签页和画布内容均在，`in` 端口、`R1 = 1k`、`C1 = 1u`、脉冲源 `PW=20m / V1=0 / V2=5 / per=40m`、`Sim1 tstep=10u tstop=7m` 均保持。因此 A4 **通过**。

证据：[重启后的空窗口](evidence/c-d4/a4-restarted.jpeg) · [重新打开文件选择器](evidence/c-d4/a4-open-picker2.jpeg) · [进程重启后重开成功](evidence/c-d4/a4-reopened-after-restart.jpeg)

说明：D3 使用默认后缀保存，文件名成为 `.xsch`，所以本轮截图中的标题为 `.xsch`。这不影响 A4 的“退出重启后仍可打开”结论；用户自定义文件名仍未覆盖。

### A6 只读/无权限路径保存

步骤与结果：

1. 打开包内只读工程。
2. 执行 Save，目标仍是 `resfile/testcases/` 下的只读路径。
3. 应用弹出 `Error` 对话框，正文为 `Cannot save document!`。
4. 关闭提示后进程仍存活，可在应用内继续操作。

A6 的“明确失败提示、应用不崩溃”目标达到，记为 **通过**。错误提示闭环的重复空框问题在 A8 单独登记。

证据：[只读保存失败提示](evidence/c-d4/a6-save-readonly.jpeg)

### A7 保存取消

步骤与结果：

1. 打开一个已有工程，记录标题和画布内容。
2. 选择 File → Save as，进入系统保存对话框。
3. 点击取消，返回原文档。

取消后没有进入保存成功分支，标题、标签页和画布内容均保持原样，应用不崩溃。A7 记为 **通过**。

证据：[系统保存对话框](evidence/c-d4/a7-save-as-dialog2.jpeg) · [取消后的原文档](evidence/c-d4/a7-after-save-cancel.jpeg)

边界：系统媒体目录对 shell 不可读，本轮以界面状态确认未发生保存，没有做目录级“无残留临时文件”校验。

### A8 保存失败提示

步骤与结果：

1. 沿用只读目标的保存失败路径。
2. 首次出现 `Cannot save document!`，该提示可读。
3. 关闭首次提示后，应用又弹出第二个错误框；标题被替换为只读文件路径，正文为空。
4. 关闭第二个空错误框后应用仍可操作。

因此 A8 **部分通过**：失败提示存在，应用可恢复，但错误提示重复且第二次正文为空。

根因可从源码直接确认：

- `src/fileformats.cpp:78-81`：打开目标文件失败时先弹出 `Cannot save document!` 并直接返回 `false`，没有写入 `errorMessage`。
- `src/idocument.cpp:604-619`：`SchematicDocument::save()` 收到 `format->save()` 的失败结果后直接返回，没有补齐错误信息。
- `src/mainwindow.cpp:288-291`：外层仍以 `errorMessage` 构造第二个 `QMessageBox::critical`，于是产生标题为路径、正文为空的重复错误框。

证据：[重复且为空的错误框](evidence/c-d4/a8-save-error-detail.jpeg) · [关闭错误后应用仍可操作](evidence/c-d4/a8-after-error-still-responsive.jpeg)

## 5. B 组：损坏与异常输入

### B1 空文件

打开 0 字节的 `empty.xsch`，应用显示 `Xml parse error`，正文为 `Premature end of document.`；关闭后可继续使用，未崩溃。**通过**。

证据：[空文件错误](evidence/c-d4/b1-empty-pkg.jpeg)

### B2 截断 XML

打开写到一半的 `truncated.xsch`，应用显示同样的 `Premature end of document.`；关闭后安全返回。**通过**。

证据：[截断 XML 错误](evidence/c-d4/b2-truncated.jpeg)

### B3 非法根元素

打开根元素为 `notcaneda` 的 `wrong-root.xsch`，应用显示 `Not a caneda file or probably malformatted file`，未崩溃。**通过**。

证据：[非法根元素错误](evidence/c-d4/b3-wrong-root.jpeg)

### B4 版本过高

打开 `version="9.9.9"` 的 `future-version.xsch`，应用拒绝打开并显示通用 XML 错误，未崩溃。**通过**。

证据：[高版本文件被拒绝](evidence/c-d4/b4-future-version.jpeg)

边界：提示没有单独说明“文件版本高于当前支持版本”，只显示通用格式错误；本轮按“拒绝打开并提示”判通过。

### B5 未知元件

`unknown-component.xsch` 含 `NoSuchPart`。工程成功打开，缺失元件被跳过，其余 `V1`、`R1`、`C1`、`Sim1` 正常显示。持久化日志中记录：

```text
11-27 11:13:33.722  5398  5567 W A00000/Caneda: Warning: Found unknown element "NoSuchPart" , skipping...
```

**通过**。

证据：[未知元件被跳过后工程仍打开](evidence/c-d4/b5-unknown-component.jpeg) · [持久化日志](evidence/c-d4/b5-b6-b7-persist-hilog.log)

### B6 缺库符号

`missing-library.xsch` 将 `Voltage Source Pulse` 的库指定为不存在的 `MissingLib`。工程成功打开，缺失元件被跳过，其余 `R1`、`C1`、`Sim1` 正常显示，未崩溃。持久化日志中记录：

```text
11-27 11:13:39.558  5523  5683 W A00000/Caneda: Warning: Found unknown element "Voltage Source Pulse" , skipping...
```

但界面上没有出现任何缺库/元件被跳过的提示。B6 的“有明确提示”未达到，记为 **部分通过**。

源码依据：`src/component.cpp:293-299` 在元件数据加载失败时只调用 `qWarning()`，随后读取并跳过该元素，没有向界面返回告警。用户只能在日志中发现问题。

证据：[缺库元件被静默跳过后工程仍打开](evidence/c-d4/b6-missing-library.jpeg) · [持久化日志](evidence/c-d4/b5-b6-b7-persist-hilog.log)

### B7 悬空连线

打开 `dangling-wire.xsch` 后工程正常显示，悬空线段可见，未崩溃。随后尝试运行仿真，在网表生成前出现红色 `Missing simulator backend...`，因此无法从本轮界面结果证明应用生成过网表。

网表行为只能做源码推导，不能记为实测通过：

- `src/idocument.cpp:524` 附近先检查仿真后端；后端缺失时直接显示错误，不进入网表生成。
- `src/fileformats.cpp:1432-1466` 的拓扑生成只遍历元件端口，独立悬空线不会成为拓扑条目。
- `src/fileformats.cpp:1155-1158` 会跳过未正确加载的元件。
- `src/mainwindow.cpp:708-720` 的 Show circuit netlist 只是打开相邻 `.net` 文件，不会触发生成。

因此 B7 记为 **部分通过**：打开行为通过；网表跳过未连接节点**未实测**。

证据：[含悬空线的工程正常打开](evidence/c-d4/b7-dangling-wire.jpeg) · [仿真在网表前被后端缺失拦截](evidence/c-d4/b7-simulate-attempt.jpeg)

## 6. D4 文件选择取消

步骤与结果：

1. 当前已有打开文档。
2. 选择 File → Open，进入系统文件选择器。
3. 点击取消。

应用返回原文档，标签页与画布内容保持，进程未崩溃。D4 **通过**。

证据：[取消打开后返回原文档](evidence/c-d4/d4-cancel-open.jpeg)

## 7. 缺陷与未测项

### 本轮缺陷

| 编号 | 用例 | 现象 | 严重度 | 状态 |
|---|---|---|---|---|
| C-D4-01 | A8 | 保存失败后首个提示可读，但关闭后再次弹出标题为路径、正文为空的错误框 | 中 | 已复现，待修复 |
| C-D4-02 | B6 | 缺失库元件被静默跳过，只在日志告警，界面无提示 | 中 | 已复现，待修复 |

### 本轮未测

- A1 新建并保存、A3 修改属性后覆盖保存。
- 用户自定义文件名保存；本轮默认后缀生成的文件名为 `.xsch`。
- 保存目标目录中临时/残留文件的目录级核验。
- B7 的实际网表生成与未连接节点跳过行为；本包缺少仿真后端。
- C2–C6 样例编辑与仿真。
- D5 应用自身可写目录读写。
- 真机与正式签名包行为。
