# 成员 C · D2 读写与保存重开记录

日期：2026-11-25（D2）。

按计划，D2–D3 要完成“验证沙箱路径与文件读写”和“验证工程保存后重开”两件事。这两件事都以同一个 HAP 为前提。本记录说明本次做到哪里、依据是什么，以及哪些结论必须等 HAP 就绪后才能下。

## 1. 本次范围与能力边界

本次工作在仓库的 Linux 环境里进行，无法启动宿主机的 DevEco 模拟器，也没有 Qt for HarmonyOS SDK 和 Caneda 的 HAP 产物。D1 记录的模拟器预检（MateBook Pro、HarmonyOS 7.0.0.107、API 26、x86_64）仍然有效，但它只覆盖设备与文件系统层，不含应用本身。

因此本次能做的是两条：

- 沿源码核对“保存 → 关闭 → 重开”的真实执行路径，判断哪些预期有代码支撑、哪些有缺口。
- 把 HAP 就绪后要执行的步骤、判据和需要留下的证据写成可照做的清单。

本次没有在 HAP 内执行任何用例，验收表里的状态一律不变，仍为`待验`。

## 2. 保存与重开的实际链路

保存：`MainWindow::save`（`src/mainwindow.cpp:275`）在文档没有文件名时转到 `saveAs`（`src/mainwindow.cpp:307`），否则调用 `SchematicDocument::save`（`src/idocument.cpp:604`）。后者确认后缀为 `xsch` 后交给 `FormatXmlSchematic::save`（`src/fileformats.cpp:65`），由 `saveText`（`src/fileformats.cpp:136`）经 `QXmlStreamWriter` 生成文本，再用 `QFile` 覆盖写入。保存成功后清空撤销栈（`src/idocument.cpp:621`），文档回到未修改状态。

重开：`FormatXmlSchematic::load`（`src/fileformats.cpp:100`）读入整个文件，交给 `loadFromText`（`src/fileformats.cpp:267`），依次调用 `loadComponents`（`:325`）、`loadPorts`、`loadWires`（`:397`）。元件数据由 `Component::saveData`（`src/component.cpp:254`）写出，加载时 `Component::loadData`（`src/component.cpp:279`）先用 name + library 从 `LibraryManager::componentData`（`src/library.cpp:365`）取库中定义，再读取工程里覆盖的属性。连线只存两个端点的场景坐标（`src/wire.cpp:173`），加载时按坐标回放（`:190`），不依赖元件 id。

这条链路本身是自洽的：属性按“库默认值 + 工程覆盖”合并，连线按坐标重建，与 D1 样例验证脚本采用的规则一致。下面逐条对照 A 组用例。

## 3. 逐用例核对

| 用例 | 代码路径结论 | 仍需在 HAP 内确认的点 |
|---|---|---|
| A2 保存后重开 | 链路完整。元件属性、可见性、坐标与连线坐标都会写出并在加载时恢复 | 库能正常加载时的实际显示；非 ASCII 标签（见 R4） |
| A3 覆盖保存 | 直接覆盖原文件，成功后才清空撤销栈；旧值不会残留 | 覆盖过程中断后的文件状态（见 R3） |
| A4 退出重启后打开 | 应用没有会话恢复逻辑，重启后走的是同一条打开链路，没有额外跨会话状态 | 应用重启后文件仍可打开；最近文件列表在沙箱内能否持久化 |
| A6 只读/无权限路径 | `QFile::open` 失败即弹出 `Cannot save document!` 并返回 false（`src/fileformats.cpp:77`），文档保持已修改，可继续编辑 | 模拟器上只读目录的实际报错路径与提示文案 |
| A7 保存取消 | 对话框取消时文件名为空，`saveAs` 直接返回，不改文档文件名与修改状态（`src/mainwindow.cpp:327`） | 平台文件对话框的取消回调是否走同一分支（D4） |

A2、A3 还有一个容易忽略的细节：`saveAs` 保存成功后会立刻调用 `open(fileName)` 重新加载文档（`src/mainwindow.cpp:340`）。也就是说“另存为”本身就会跑一遍保存再重开。如果这条路径在模拟器上正常，A2 的链路问题基本可以排除。

## 4. 静态审查发现

以下五项来自源码核对，均未在 HAP 内复现，先记为待复核。确认后再决定是否进入缺陷清单。

### R1 空文件被当作有效工程打开

`loadFromText` 只有在遇到非 `caneda` 的起始元素时才报错（`src/fileformats.cpp:305`）。0 字节文件没有任何起始元素，循环不进入，`hasError()` 为 false，函数返回 true。结果是打开一个空白原理图，没有任何提示。

这与 B1 的预期“报错并安全返回”不一致。建议加载前先判断是否读到 `caneda` 根元素，未读到时按非法文件报错。本次只记录，不改代码。

### R2 未知元件与缺库只写日志，界面无提示

`Component::loadData` 找不到库数据时打印 `qWarning` 并跳过该元件的属性（`src/component.cpp:296`），但 `loadComponents` 已经先 `new Component()` 并把对象加进场景（`src/fileformats.cpp:344`）。默认构造的元件没有端口和图形数据，会成为场景里的空对象；用户看不到任何提示。如果此时保存，`saveData` 会写出空的 name 与 library。

B5 预期“跳过该元件并告警，其余正常”、B6 预期“有明确提示”，当前实现只满足“不崩溃”。这条与 R5 叠加时影响最大：库目录解析失败会让两套样例的所有元件都变成空对象，而界面看上去只是“图是空的”。

### R3 保存是直接覆盖，且空内容也会写盘

`save` 用 `QFile` 以 `WriteOnly` 直接打开目标文件覆盖（`src/fileformats.cpp:77`），没有临时文件加改名。写到一半失败（磁盘满、进程被杀）会截断原文件，旧内容无法恢复。另外 `saveText` 返回空串时只打印一条 `qDebug`，仍会写出一个空文件并返回成功（`:74`）。

A8 要求的“提示可读，可继续编辑”在内存态是满足的：保存失败时撤销栈不清空，文档仍是已修改状态。风险在磁盘上的原文件。

### R4 保存编码依赖系统 locale，文件却声明 UTF-8

`saveText` 产出的是 `QString`，`save` 用 `QTextStream` 默认编码写入（`src/fileformats.cpp:84`）。Qt 5 下默认编码是系统 locale 编码，而 `QXmlStreamWriter::writeStartDocument` 写出的声明是 UTF-8。中文 Windows（GBK）上保存的中文标签，文件头仍写 UTF-8。

同一台机器同一 locale 下往返能自洽，因为读取时也用同一编码解码。跨环境就会出问题：Windows 上保存的文件拿到 UTF-8 环境的模拟器里打开，中文会乱码，甚至解析失败。两套样例全是 ASCII，不受影响；用户自定义中文标签会受影响。建议在 A2/A3 里加一条中文标签用例，作为待补验项。

### R5 库目录是编译期绝对路径，解析失败会退化到根目录

`LIBRARYDIR` 在编译期展开为 `${CMAKE_INSTALL_PREFIX}/share/caneda/libraries/`（`config.h.cmake:8`），`Caneda::libDirectory()` 对它取 `canonicalPath()` 后拼接（`src/global.cpp:56`）。`canonicalPath()` 在路径不存在时返回空串，函数于是返回 `/`，`Settings` 的默认库路径随之变成 `/components/...`（`src/settings.cpp:38`）。所有库加载失败，与 R2 叠加。

对 D2 的意义是：沙箱路径验收不只要确认“应用能读写”，还要确认打包后的 `LIBRARYDIR` 指向 HAP 内可读目录。这一项需要构建负责人确认 `CMAKE_INSTALL_PREFIX` 的设置，验收侧无法从应用外部判断。

## 5. HAP 就绪后的 D2 执行步骤

前提：模拟器已按 D1 记录启动，`hdc list targets` 能看到 `127.0.0.1:5555`，HAP 已安装并可启动。每一步都要留截图，涉及路径的再补一条 `hdc shell ls -l` 输出。

| 步骤 | 操作 | 通过判据 | 证据 |
|---|---|---|---|
| D2-0 | 打开两套样例，观察元件数与连线 | RC 为 4 元件、8 连线、3 端口；整流为 5 元件 | 截图；若为空图，先查 R5 |
| D2-1 | 新建原理图，放到一个电阻，保存到应用可写目录 | 生成 `.xsch`，无错误提示；`ls -l` 能看到文件 | 截图 + 路径 |
| D2-2 | 关闭文档，重新打开 D2-1 的文件 | 元件、连线、属性值与保存前一致 | 保存前后对照截图 |
| D2-3 | 改 R1 为 2 kΩ，保存后重开 | 值为 2 kΩ，旧值不残留 | 截图 |
| D2-4 | 改回 1 kΩ，保存后重开 | 值为 1 kΩ（C3 依赖这份未修改的样例） | 截图 |
| D2-5 | 保存到只读路径（如 `/system`） | 出现 `Cannot save document!`，应用可继续编辑与保存到别处 | 截图 + 日志 |
| D2-6 | 退出应用进程后重启，打开 D2-4 的文件 | 文件可打开，内容一致 | 截图 |
| D2-7 | 在属性里填中文标签，保存后重开 | 中文正常显示，无乱码 | 截图（对应 R4） |

D2-0 若出现空图，不要继续后面的步骤，先确认 `LIBRARYDIR` 指向的目录在 HAP 内是否存在（R5），这是后续所有用例的前提。

## 6. 结论

D2 的两项应用级验收仍未执行，原因与 D1 相同：本机没有 Qt for HarmonyOS SDK，也没有可安装的 HAP。本次完成的是保存与重开链路的源码核对，得到五项待复核发现，其中 R1（空文件被接受）和 R5（库目录退化）会直接影响 B1、B5、B6 与两套样例的打开。

下一步取决于 HAP：拿到包后按第 5 节执行，把结果回填验收表；R1、R2 是否需要修复，等复现后再定。
