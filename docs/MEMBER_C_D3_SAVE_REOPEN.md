# 成员 C · D3 工程保存后重开（HAP 内实测）

日期：2026-11-26（D3）。执行环境：DevEco Studio 模拟器，MateBook Pro（2in1），HarmonyOS 7.0.0.107，API 26，x86_64。

与 D2 不同，本次**取得了可安装的 Caneda HAP 并在模拟器内完成了打开既有 RC 样例、另存 A5 副本、关闭文档与重开该副本的应用级验收**，不再是源码核对。D3 计划项据此通过，但结论仅限这条实际跑通的链路。

## 1. 被测产物

| 项目 | 值 |
|---|---|
| 包名 | `com.caneda.desktop` |
| HAP | `entry-default-unsigned.hap`，32,028,826 字节 |
| HAP SHA-256 | `d5970a8bc0b13c662ca4ec8ad82460395b560838a4c6af0d4537bb4e3b353122` |
| `libcaneda.so` SHA-256 | `982cdb0097149bcd8bcc47e477110efd29c17fc54f1fdf9fac009d4b44e39592` |
| Caneda 源码 | 标签 `caneda-upstream-base`，`e0c11869cd0282c4d30c78c7d976b09271050214` |
| Qt | Qt for HarmonyOS 5.15.16，源码标签 `4af606551a1ca1f91869284eb13650b2204d7161` |
| Qwt | 6.1.6，源码 SHA-256 `99460d31c115ee4117b0175d885f47c2c590d784206f09815dc058fbe5ede1f6`（与成员 A D1 记录同源） |
| 架构 | x86_64，交叉编译，`OHOS_STL=c++_shared` |

构建方式、依赖闭包与环境坑见 `qt-harmonyos/BUILD_ENV.md`（工作区外，工具链目录）。要点：

- Qt 交叉构建需主机 MinGW 8.1.0；msys2 GCC 16 的头文件与 Qt 5.15.16 冲突。
- `LIBRARYDIR` 等资源路径编译期写死，本次设为 `/data/storage/el1/bundle/entry/resources/resfile/caneda/`，元件库与样例随 HAP 一并下发。
- `libqwt.so` 依赖 `libQt5Concurrent.so` 与 `libQt5OpenGL.so`；缺任一个会导致 `dlopen` 失败、应用启动即崩。

## 2. 验收结果（既有 RC 样例另存、关闭与重开 A5 副本）

| 步骤 | 操作 | 结果 | 证据 |
|---|---|---|---|
| D3-1 | 安装 HAP 并启动 | 通过。主窗口出现，标题 `Untitled - Caneda`，元件树加载出 Active / CMOS / Measurement / Miscellaneous 等分组 | [01-launch](evidence/c-d3/01-launch.jpeg) |
| D3-2 | 打开 RC 样例 `rc-lowpass.xsch` | 通过。标题与标签页变为 `rc-lowpass.xsch`，画布显示 `in` 端口、`R1 = 1k`、`C1 = 1u`、`PW=20m / V1=0 / V2=5 / per=40m`、`Sim1 tstep=10u tstop=7m` | [02-open-rc-sample](evidence/c-d3/02-open-rc-sample.jpeg) |
| D3-3 | 另存为 | 通过。File 菜单列出 New / Open / Close / Save / Save all / Save as / Print / Export image / Quit；另存对话框为系统文件选择器，保存后标题与标签页变为新文件名 | [03-file-menu](evidence/c-d3/03-file-menu.jpeg) · [04-save-as-dialog](evidence/c-d3/04-save-as-dialog.jpeg) · [05-after-save](evidence/c-d3/05-after-save.jpeg) |
| D3-4 | 关闭文档 | 通过。标签页关闭，标题回到 `Caneda`，无残留未保存提示 | [06-closed](evidence/c-d3/06-closed.jpeg) |
| D3-5 | 重新打开刚保存的文件 | 通过。标题与标签页为新文件名，**画布内容与保存前逐项一致**：`in` 端口、`R1 = 1k`、`C1 = 1u`、脉冲源四个参数、`Sim1` 两条指令 | [07-open-dialog-saved-file](evidence/c-d3/07-open-dialog-saved-file.jpeg) · [08-reopened](evidence/c-d3/08-reopened.jpeg) |

结论：本次实际通过范围仅限 **打开既有 RC 样例 → 另存为 A5 副本 → 关闭文档 → 重开 A5 副本**，重开后元件、属性值与仿真指令全部保持。A2 仅指上述 A5 副本的重开；A1（新建并保存）、A3（修改属性后覆盖保存）、A4（退出进程后重启）未执行，D5（应用自身可写目录读写）未完成，均保持待验。

### 2.1 D5 补充观察（不改变 D5 状态）

| 编号 | 观察项 | 结果 | 证据 |
|---|---|---|---|
| D5-O1 | 包内 `resfile` 读取 | 通过。元件树与 RC 样例从 `/data/storage/el1/bundle/entry/resources/resfile/caneda/` 正常加载。 | [01-launch](evidence/c-d3/01-launch.jpeg) · [02-open-rc-sample](evidence/c-d3/02-open-rc-sample.jpeg) |
| D5-O2 | 系统文件选择器保存 | 通过。通过系统选择器另存副本，保存后标题与标签页更新。 | [04-save-as-dialog](evidence/c-d3/04-save-as-dialog.jpeg) · [05-after-save](evidence/c-d3/05-after-save.jpeg) |

以上两项是独立观察，不等同于 D5 通过。D5 仍待应用在自身可写目录中实际完成读写后再更新状态。

## 3. 复现步骤

前提：模拟器已启动（`hdc list targets` 返回 `127.0.0.1:5555`），HAP 已安装。

```sh
# 1. 安装（开发者模拟器接受未签名包）
hdc install -r entry-default-unsigned.hap

# 2. 直接打开包内样例（无需文件对话框）
hdc shell aa start -a QAbility -b com.caneda.desktop \
  --ps io.qt.appArgsJson \
  '["/data/storage/el1/bundle/entry/resources/resfile/caneda/samples/rc-lowpass/rc-lowpass.xsch"]'

# 3. 截图取证
hdc shell snapshot_display -f /data/local/tmp/s.jpeg
hdc file recv /data/local/tmp/s.jpeg ./s.jpeg
```

`io.qt.appArgsJson` 是 Qt for HarmonyOS QPA 约定的启动参数，`libqohos.so` 会把它转成 `main()` 的 `argv`，Caneda 的 `initFiles()` 随之打开对应工程。这条路径也解释了验收表 D3「文件选择回调」的应用侧行为。

## 4. 本次未能覆盖的部分

除第 2 节明确限定的通过范围外，A1、A3、A4 本次未执行，D5 未完成，验收表均保持待验。以下三项是**环境限制**，不是应用缺陷，需在下一工作日或由组长补环境后复测：

1. **自定义文件名保存**。模拟器聚焦任何文本输入框都会弹「小艺输入法」授权页，`uinput` 注入的文本被该页拦截，无法自动输入文件名。本次保存采用了系统选择器预填的后缀名，文件名为 `.xsch`；保存与重开本身已验证，但「用户自定义文件名」尚未实测。
2. **保存到只读路径的失败提示（A6）**。应用沙箱 `/data/app/el2/100/base/com.caneda.desktop/**` 对 `hdc shell` 只读、`hdc file send` 亦被拒，无法构造只读目标；包内 `resfile` 本身只读，但当前文档保存走系统选择器，未触发该分支。
3. **字节级文件校验**。保存目标经系统文件访问框架（URI）落盘，`/storage/media/100/local/files` 对 shell 不可读，因此只能以界面比对留证，未取得保存后文件的校验和。

另：本次为未签名调试包。正式签名、上传与提交仍由组长负责，D3 结论不受影响。

## 5. 对 D2 遗留发现的处理

| 编号 | D2 时状态 | D3 结论 |
|---|---|---|
| R5 库目录编译期绝对路径 | 待复核，担心解析失败退化到 `/` | 在包内 `resfile` 场景下**未复现**（对应 D5-O1）。元件树完整加载在 `resfile/caneda/libraries` 路径下，说明编译期路径与打包路径一致时工作正常；该观察不构成 D5 通过，应用自身可写目录读写仍待验。风险仍在：路径变更需同步改 `config.h` 并重编。 |
| R2 未知元件只写日志 | 待复核 | 未触发（样例元件都在库中）。仍待 B 组用例确认。 |
| R1 空文件被当有效工程 | 待复核 | 未覆盖，下次一并验。 |
| R3 写入失败无提示 | 待复核 | 未覆盖（同第 4 节第 2 项）。 |
| R4 编码依赖 locale | 待复核 | 未覆盖；`libQt5Core` 在 HarmonyOS 为 musl 环境，locale 行为需单独确认。 |

## 6. 下一步

- D4 计划项「验证工程读写接口及取消、损坏文件用例」：请求组长在模拟器上放开文本输入（预置输入法授权或提供可写共享目录），否则取消与自定义文件名两类用例无法自动化。
- 元件库若改为随正式包分发，需复核 `LIBRARYDIR` 与 `CMAKE_INSTALL_PREFIX` 的一致性，避免重演 R5。
