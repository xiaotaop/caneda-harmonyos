# 成员 C · D5 样例回归与验收表更新

- 日期：2026-11-28
- 分支：`feature/c-d5-samples-acceptance`
- 计划项：D5「更新样例和验收表」
- 结论：两套样例桌面回归通过，样例数值无需调整；B4 版本过高用例补测通过；D5「应用自身可写目录读写」仍待验。

## 1. 环境

| 项目 | 值 |
|---|---|
| 桌面系统 | Windows 11 10.0.26300 |
| Python | 3.13.11 |
| ngspice | ngspice-47 |
| 模拟器 | HarmonyOS 7.0.0.107，API 26，x86_64，2in1 |
| hdc 目标 | `127.0.0.1:5557` |
| HAP | `com.caneda.desktop` 1.0.0，SHA-256 `1eb50c2796ac9685d44f31c72bc575d6102da0df4b088c35598078b0827f0b19`，32,039,938 字节 |

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
& $hdc -t 127.0.0.1:5557 shell $remote
```

关键点是让远端 shell 保留 JSON 值内部的双引号。若把 JSON 作为独立 PowerShell 参数直接传给 hdc，Want 中会退化为 `[/data/.../future-version.xsch]`，Qt 将其判为非法参数并直接退出；该无效尝试不计入验收。

有效结果：

- `QAbilityStage::onAcceptWant` 日志记录 `io.qt.appArgsJson` 的值为 `[\"/data/storage/el1/bundle/entry/resources/resfile/caneda/testcases/future-version.xsch\"]`，能把本次启动与 `future-version.xsch` 唯一关联。
- 应用显示 `Xml parse error` / `Not a caneda file or probably malformatted file`，文件未被打开。
- 截图时应用进程 PID `6859` 仍存活，未崩溃。
- `src/global.cpp::checkVersion()` 对高于当前版本的文件返回 `false`，`src/fileformats.cpp::FormatXmlSchematic::loadFromText()` 随即走拒绝分支。
- 结论：B4 **通过**。提示文案是通用 XML 错误，不能单独区分 B3/B4，但启动参数日志、截图时间与源码路径已形成独立证据链。

证据：[截图](evidence/c-d5/b4-future-version-d5.jpeg) · [hilog](evidence/c-d5/b4-future-version-d5-hilog.log)。

## 4. D5 状态

`D5` 要求“在应用可写目录读写样例”，必须在 HAP 内对应用自身沙箱可写路径完成实际写入和重开。本次桌面样例回归和 B4 补测都不能替代该项，因此验收表 D5 继续标记为**待验**。

后续执行需要先确认应用可写的沙箱路径，再在应用内打开样例、另存到该路径、关闭并重新打开，保留文件名/路径与读写结果的关联证据。

## 5. 本次归档

| 文件 | 用途 |
|---|---|
| `docs/evidence/c-d5/verify-samples.log` | 两套样例完整回归输出与退出码 |
| `docs/evidence/c-d5/samples-sha256.txt` | 样例、预期值与校验脚本 SHA-256 |
| `docs/evidence/c-d5/b4-future-version-d5.jpeg` | B4 拒绝提示截图 |
| `docs/evidence/c-d5/b4-future-version-d5-hilog.log` | B4 启动参数与弹窗关联日志 |
| `tests/files/samples/README.md` | 增加 D5 回归命令、结果与证据入口 |
| `docs/MEMBER_C_ACCEPTANCE.md` | 更新 B4 为通过，D5 保持待验并链接本记录 |
| `docs/MEMBER_C_PLAN.md` | 追加 D5 进展 |