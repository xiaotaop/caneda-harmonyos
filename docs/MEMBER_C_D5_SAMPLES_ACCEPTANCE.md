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
| HAP（D5 原始读写，已被下一条取代） | `com.caneda.desktop` 1.0.0，SHA-256 `026ec6d601c3bdc2f855a835f7f00550fab318fb9d4760888952ddda38a57a4d`，32,043,122 字节。该包的私有目录写入记录早于包本身生成，按组长意见不再作为读写结论依据 |
| HAP（P1/P2 复验，最终） | `com.caneda.desktop` 1.0.0，SHA-256 `e18dea274b17489dc0331236aa8a1befe5751af9cc3c837c8169e68f9c49a756`，32,047,426 字节，未签名调试包。保留系统选择器入口并新增应用存储入口后的重建包，第 4 节全部结论以此包为准 |
| libcaneda.so（P1/P2，最终） | SHA-256 `67d893432423b5af24ea7293c1352dc38d3fa4335d3e87855c288d9bca89ebcb` |

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

**通过。** 本节结论全部基于最终 HAP `e18dea274b17489dc0331236aa8a1befe5751af9cc3c837c8169e68f9c49a756`（32,047,426 字节）。

### 4.1 入口设计（按组长 P1 意见调整）

上一版在 `Q_OS_OHOS` 下把 `open()` 与 `saveAs()` 强制改成 Qt 非原生对话框，虽然能进入应用私有目录，但同时去掉了系统文件选择器入口，通过系统选择器打开外部工程、另存到共享位置的流程因此不可达。现改为两个入口并存：

| 菜单项 | 对话框 | 用途 |
|---|---|---|
| `File > Open...` | 系统文件选择器 | 打开共享位置的外部工程 |
| `File > Open from App Storage...` | Qt 对话框，根目录为私有 `files` | 打开应用私有目录内的工程 |
| `File > Save as...` | 系统保存对话框 | 另存到共享位置 |
| `File > Save as to App Storage...` | Qt 对话框，预填当前文件名、根目录为私有 `files` | 另存到应用私有目录 |

实现：`saveAs()` 与 `saveAsToAppStorage()` 共用 `saveAsTo(bool useAppStorage)`；两个新动作仅在 `Q_OS_OHOS` 下注册并插入 File 菜单，其他平台菜单不变。

### 4.2 P1：系统选择器入口可用（外部工程 + 共享位置）

| 步骤 | 结果 | 证据 |
|---|---|---|
| `File > Open...` | 弹出**系统文件选择器**（"安全访问文件"），列出共享目录中的 `rc-lowpass-d5`、`.xsch` | [菜单](evidence/c-d5/d5-p1-menu.jpeg) · [系统选择器](evidence/c-d5/d5-p1-open-system-picker.jpeg) |
| 选择外部工程 `rc-lowpass-d5` | 打开成功，标题 `rc-lowpass-d5.xsch`，RC 元件、属性与 `Sim1` 指令正常 | [打开结果](evidence/c-d5/d5-p1-external-opened.jpeg) |
| `File > Save as...` | 弹出**系统保存对话框**（"选择路径"），文件名预填 `.xsch`，位置为共享目录 | [系统保存对话框](evidence/c-d5/d5-p1-saveas-system-picker.jpeg) |
| 确认保存（覆盖同名文件） | 保存成功，文档标题变为 `.xsch`；共享目录同名文件修改时间由 11-27 11:29 更新为 **11-28 14:16** | [保存结果](evidence/c-d5/d5-p1-saveas-shared-done.jpeg) |

### 4.3 P2：最终 HAP 在私有目录另存新副本，重启后打开

| 步骤 | 结果 | 证据 |
|---|---|---|
| 前置状态 | 私有目录 `…/com.caneda.desktop/files` 仅有旧文件 `rc-lowpass.xsch`（11:30，3575 字节） | [文件检查](evidence/c-d5/d5-p2-file-check.log) |
| 打开外部工程后执行 `File > Save as to App Storage...` | Qt 保存对话框根目录为私有 `files`，文件名预填 `rc-lowpass-d5.xsch` | [保存对话框](evidence/c-d5/d5-p2-appstorage-saveas-dialog.jpeg) |
| 点击 Save | 私有目录新增 `rc-lowpass-d5.xsch`，**修改时间 2026-11-28 14:20**，3575 字节 | [保存后](evidence/c-d5/d5-p2-private-saved.jpeg) · [文件检查](evidence/c-d5/d5-p2-file-check.log) |
| 回传并校验 | SHA-256 `c1f46aebd0f8168d2f87a1f44e309d0b994973654ec3ae7a93f35a8d52afeaaf` | [回传文件](evidence/c-d5/rc-lowpass-d5-saved.xsch) |
| 结束进程并重启 | PID `2885` → `7213`，界面回到 `Untitled` | [重启后](evidence/c-d5/d5-p2-restarted.jpeg) |
| `File > Open from App Storage...` | Qt 打开对话框列出私有目录两个文件（`rc-lowpass.xsch`、`rc-lowpass-d5.xsch`） | [打开对话框](evidence/c-d5/d5-p2-appstorage-open-dialog.jpeg) |
| 选择新副本打开 | 标题与标签页为 `rc-lowpass-d5.xsch`；`in` 端口、`R1 = 1k`、`C1 = 1u`、脉冲源四参数与 `Sim1` 两条指令均正常 | [重开结果](evidence/c-d5/d5-p2-reopen-private.jpeg) |

结论：最终 HAP 在应用私有目录写出了**新副本**（文件名、修改时间与 SHA-256 均已记录），重启后经应用存储入口重新打开，内容完整。

### 4.4 与上一版的差异

- 上一版私有目录写入记录（11:30）早于其被测 HAP（11:46 生成、11:47 安装），不能作为该包的证据；本节已用最终包重做并留下新副本的时间与哈希。
- 上一版删除的系统选择器入口已恢复，并在同一个 HAP 上验证了外部工程打开与共享位置另存。

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
| `docs/evidence/c-d5/d5-p1-*.jpeg` | 系统选择器入口复验：菜单、系统打开/保存对话框、外部工程打开、共享位置另存 |
| `docs/evidence/c-d5/d5-p2-*.jpeg`、`d5-p2-file-check.log` | 私有目录另存新副本、重启、经应用存储入口重开；含文件时间与哈希 |
| `docs/evidence/c-d5/rc-lowpass-d5-saved.xsch` | 最终 HAP 写出的私有目录副本（回传件，3575 字节，SHA-256 `c1f46aeb…`） |
| `src/mainwindow.cpp`、`src/mainwindow.h` | OHOS 下保留系统选择器入口，新增 `Open from App Storage`/`Save as to App Storage` 两个入口；`saveAs` 抽出 `saveAsTo(bool)` |
| `docs/MEMBER_C_ACCEPTANCE.md` | 更新 B4 与 D5 为通过并链接本记录 |
| `tests/files/samples/README.md` | 增加 D5 回归命令、结果与证据入口 |
| `docs/MEMBER_C_ACCEPTANCE.md` | 更新 B4 与 D5 为通过并链接本记录 |
| `docs/MEMBER_C_PLAN.md` | 追加 D5 完成进展 |