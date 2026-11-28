# 成员 C · D5 样例回归与验收表更新

- 日期：2026-11-28
- 分支：`feature/c-d5-samples-acceptance`
- 计划项：D5「更新样例和验收表」
- 结论：两套样例桌面回归通过，样例数值无需调整；B4 版本过高用例补测通过；D5「应用自身可写目录读写」已在最新 HAP 中完成保存、关闭和重新打开闭环，判定**通过**。

## 1. 环境

| 项目 | 值 |
|---|---|
| 桌面系统 | Windows 11 10.0.26300 |
| Python | 3.13.11 |
| ngspice | ngspice-47 |
| 模拟器 | HarmonyOS 7.0.0.107，API 26，x86_64，2in1 |
| hdc 目标 | `127.0.0.1:5555` |
| HAP（样例回归/B4） | `com.caneda.desktop` 1.0.0，SHA-256 `1eb50c2796ac9685d44f31c72bc575d6102da0df4b088c35598078b0827f0b19`，32,039,938 字节 |
| HAP（D5 最终读写） | `com.caneda.desktop` 1.0.0，SHA-256 `026ec6d601c3bdc2f855a835f7f00550fab318fb9d4760888952ddda38a57a4d`，32,043,122 字节，未签名调试包 |

## 2. 样例回归

执行命令：

```powershell
python tests/files/verify_samples.py --ngspice D:\msys64\ucrt64\bin\ngspice.exe
```

结果：

| 样例 | 检查点 | 期望 | 实测 | 偏差 | 结果 |
|---|---:|---:|---:|---:|---|
| RC 低通 @ 0.500 ms | - | 0.000000 V | 0.000000 V | 0.000000 V | OK |
| RC 低通 @ 2.003 ms | - | 3.165195 V | 3.164797 V | 0.000398 V | OK |
| RC 低通 @ 4.003 ms | - | 4.751686 V | 4.751636 V | 0.000050 V | OK |
| RC 低通 @ 6.003 ms | - | 4.966394 V | 4.966388 V | 0.000006 V | OK |
| RC 低通 @ 7.000 ms | - | 4.987600 V | 4.987601 V | 0.000001 V | OK |
| 二极管整流 @ 30 ms | - | 9.064500 V | 9.158440 V | 0.093940 V | OK |
| 二极管整流 @ 40 ms | - | 8.888400 V | 8.965638 V | 0.077238 V | OK |
| 二极管整流 @ 50 ms | - | 9.064500 V | 9.158440 V | 0.093940 V | OK |

- RC 低通：719 点、3 变量，`PASS`，最大偏差 `0.000398 V`（容差 `0.01 V`）。
- 二极管整流：6008 点、3 变量，`PASS`，最大偏差 `0.093940 V`（容差 `0.3 V`）。
- 命令退出码：`0`。
- 完整输出：[verify-samples.log](evidence/c-d5/verify-samples.log)。

对 `expected.json`、两套 `.xsch` 执行忽略行尾差异的 Git 比对，退出码为 `0`，说明本次没有需要提交的样例内容改动。既有预期值继续有效，不因 D5 回归调整。样例文件哈希见 [samples-sha256.txt](evidence/c-d5/samples-sha256.txt)。

## 3. B4 版本过高补测

D4 的 B4 因子截图与 B3 重复而保持待验。本次先修正 `aa start` 的引号传递方式，再重新启动 `future-version.xsch`：

```powershell
$json='["/data/storage/el1/bundle/entry/resources/resfile/caneda/testcases/future-version.xsch"]'
$remote="aa start -a QAbility -b com.caneda.desktop --ps io.qt.appArgsJson '$json'"
& $hdc -t 127.0.0.1:5555 shell $remote
```

关键点是让远端 shell 保留 JSON 值内部的双引号。若把 JSON 作为独立 PowerShell 参数直接传给 hdc，Want 中会退化为 `[/data/.../future-version.xsch]`，Qt 将其判为非法参数并直接退出；该无效尝试不计入验收。

有效结果：

- `QAbilityStage::onAcceptWant` 日志记录 `io.qt.appArgsJson` 的值为 `[\"/data/storage/el1/bundle/entry/resources/resfile/caneda/testcases/future-version.xsch\"]`，能把本次启动与 `future-version.xsch` 唯一关联。
- 应用显示 `Xml parse error` / `Not a caneda file or probably malformatted file`，文件未被打开。
- 截图时应用进程 PID `6859` 仍存活，未崩溃。
- `src/global.cpp::checkVersion()` 对高于当前版本的文件返回 `false`，`src/fileformats.cpp::FormatXmlSchematic::loadFromText()` 随即走拒绝分支。
- 结论：B4 **通过**。提示文案是通用 XML 错误，不能单独区分 B3/B4，但启动参数日志、截图时间与源码路径已形成独立证据链。

证据：[截图](evidence/c-d5/b4-future-version-d5.jpeg) · [hilog](evidence/c-d5/b4-future-version-d5-hilog.log)。

## 4. D5 应用可写目录读写

**通过。**

最新 HAP 在模拟器内覆盖安装后，完成以下闭环：

1. `MainWindow::saveAs()` 在 `Q_OS_OHOS` 下改用 Qt 非原生 `QFileDialog`，默认目录设为 `QStandardPaths::HomeLocation`，设备侧解析为 `/data/app/el2/100/base/com.caneda.desktop/files`。对话框预填 `rc-lowpass.xsch`，点击 Save 后成功写入。
2. 设备侧确认文件存在：3575 字节，SHA-256 `c1f46aebd0f8168d2f87a1f44e309d0b994973654ec3ae7a93f35a8d52afeaaf`。
3. `MainWindow::open()` 同样使用 Qt 非原生 `QFileDialog`。覆盖安装并重启应用后，`File > Open` 打开的是 Qt `Open File` 对话框，`Look in` 指向应用私有 `files` 目录（截图因宽度省略为 `/dat…files`），文件列表显示 `rc-lowpass.xsch`。
4. 选择并打开该文件后，标题栏和标签页变为 `rc-lowpass.xsch`，RC 元件、连线、属性与仿真指令正常显示。
5. 执行 `File > Close`，文档关闭且仅保留 `Untitled`；再次执行 `File > Open` 重开同一文件，文档与图形正常显示。
6. 验证结束时进程 `com.caneda.desktop`（PID 24164）保持存活。

最终被测 HAP 为 `026ec6d601c3bdc2f855a835f7f00550fab318fb9d4760888952ddda38a57a4d`（32,043,122 字节），使用 `hdc install -r` 覆盖安装成功。完整命令结果、文件元数据和截图索引见 [d5-final-verification.log](evidence/c-d5/d5-final-verification.log)。

关键证据：

- [Save As 对话框（私有目录与预填文件名）](evidence/c-d5/d5-qt-saveas2.jpeg)
- [保存后的应用界面](evidence/c-d5/d5-saved.jpeg)
- [设备侧文件检查](evidence/c-d5/d5-saved-file-check.log) · [回传文件](evidence/c-d5/rc-lowpass-saved.xsch)
- [最新 HAP 的 Open File 对话框](evidence/c-d5/d5-final-open-dialog.jpeg)
- [覆盖安装并重启后的打开结果](evidence/c-d5/d5-final-reopen.jpeg)
- [关闭文档后的界面](evidence/c-d5/d5-final-closed.jpeg)
- [关闭后再次打开的结果](evidence/c-d5/d5-final-reopen-after-close.jpeg)
- [libcaneda.so 构建日志](evidence/c-d5/d5-qt-dialogs-build.log) · [HAP 构建日志](evidence/c-d5/d5-hap-build.log)

## 5. 本次归档

| 文件 | 用途 |
|---|---|
| `docs/evidence/c-d5/verify-samples.log` | 两套样例完整回归输出与退出码 |
| `docs/evidence/c-d5/samples-sha256.txt` | 样例、预期值与校验脚本 SHA-256 |
| `docs/evidence/c-d5/b4-future-version-d5.jpeg` | B4 拒绝提示截图 |
| `docs/evidence/c-d5/b4-future-version-d5-hilog.log` | B4 启动参数与弹窗关联日志 |
| `docs/evidence/c-d5/d5-qt-saveas2.jpeg`、`d5-saved.jpeg` | 应用私有目录 Save As 与保存结果 |
| `docs/evidence/c-d5/d5-saved-file-check.log`、`rc-lowpass-saved.xsch` | 设备侧文件存在性、哈希与回传文件 |
| `docs/evidence/c-d5/d5-final-*.jpeg`、`d5-final-verification.log` | 最新 HAP 的 Open、Close、重新打开证据与测试记录 |
| `docs/evidence/c-d5/d5-qt-dialogs-build.log`、`d5-hap-build.log` | 源码修改后的库与 HAP 构建结果 |
| `src/mainwindow.cpp` | OHOS 下 Open/Save As 改用可达应用私有目录的 Qt 文件对话框 |
| `tests/files/samples/README.md` | 增加 D5 回归命令、结果与证据入口 |
| `docs/MEMBER_C_ACCEPTANCE.md` | 更新 B4 与 D5 为通过并链接本记录 |
| `docs/MEMBER_C_PLAN.md` | 追加 D5 完成进展 |