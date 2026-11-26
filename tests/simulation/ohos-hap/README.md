# D3 鸿蒙应用内 RC 探针

独立调试应用 `com.example.canedangspiceprobe`。每次启动时把固定 RC 网表复制到新的应用私有目录，记录 CLI 子进程失败阶段或退出码，再用 HAP 内的 libngspice 在同一应用进程中运行两次。两次共享库输出分别保存在 `shared.raw` 与 `shared-repeat.raw`。该测试工程用于确认引擎调用和波形回传；完整 Caneda、Qt/Qwt 及原理图导出由集成包验证。

## 构建与复测

先按 [交叉编译说明](../../../scripts/ohos/README.md) 构建同一 ABI 的 CLI 和共享库。下面是本机 macOS 命令，`cli_stage` 与 `shared_stage` 是两个构建输出中的 `stage/` 绝对路径。

```sh
app=/Applications/DevEco-Studio.app/Contents
sdk="$app/sdk/default/openharmony/native"
work=$(mktemp -d)
project="$work/caneda-spice"
python3 tests/simulation/ohos-hap/prepare.py "$sdk" arm64-v8a \
  "$cli_stage" "$shared_stage" "$project"
(
  cd "$project"
  export NODE_HOME="$app/tools/node" JAVA_HOME="$app/jbr/Contents/Home"
  export DEVECO_SDK_HOME="$app/sdk" PATH="$NODE_HOME/bin:$JAVA_HOME/bin:$PATH"
  "$app/tools/ohpm/bin/ohpm" install
  "$app/tools/hvigor/bin/hvigorw" --mode module -p module=entry@default \
    -p product=default -p buildMode=debug assembleHap --no-daemon --offline
)
```

将 `arm64-v8a` 及两个输入改为 `x86_64` 可复现另一包。用与产物匹配的 PC 模拟器。以下命令假定已连接且只选择了测试目标；同时连接多台设备时为每条命令显式指定 `hdc -t <target>`。

```sh
bundle=com.example.canedangspiceprobe
hdc install -r "$project/entry/build/default/outputs/default/entry-default-unsigned.hap"
hdc shell aa start -a EntryAbility -b "$bundle"
hdc shell hilog -x -T CanedaD3
# 将 run 设为上条日志中以 rc- 开头的本次运行目录。
for name in shared shared-repeat; do
  hdc file recv -b "$bundle" "./data/storage/el2/base/haps/entry/files/$run/$name.raw" "$work/$name.raw"
  python3 tests/simulation/check_rc.py --raw "$work/$name.raw"
done
```

## 2026-11-26 验证结果

- DevEco Native SDK 26.0.0.105，ngspice 47。arm64-v8a 与 x86_64 调试 HAP 均完成离线构建，核对了包内 ABI 与依赖。生成器会拒绝 ABI 不匹配的输入。
- MateBook Pro PC 模拟器，HarmonyOS 7.0.0.107 SP8，API 26，arm64-v8a。实际安装并启动 arm64 调试 HAP。应用私有目录允许写文件与设置执行位，CLI 子进程在 `execve` 阶段返回 `EACCES (13)`，没有产出 `cli.raw`。这个结果覆盖从本探针私有数据目录执行 CLI 的路径。
- 同一个 HAP 内的 libngspice 连续两次仿真成功。两次均由应用的同一 PID 11810 生成 719 点，取回的两份 RAW 字节完全一致，五个检查点最大误差约 22 µV，容差 3 mV。
- 初版探针在 `ngSpice_Init` 前调用 `ngSpice_nospinit` 时发生崩溃，故障栈位于 `ft_find_analysis`。最终探针移除了该前置调用。集成时应按已验证顺序初始化，再提交固定网表和读取向量。
- x86_64 HAP 尚无运行结果。建议 Caneda 的首轮仿真集成采用进程内 libngspice，并在团队的 x86_64 调试 HAP 上复跑 RC。

| 产物 | SHA-256 |
|---|---|
| arm64 调试 HAP | `ad416d538c82581ea1a29624cdcbebc99b8139d3e5da3a387a2c2db5dc02e684` |
| x86_64 调试 HAP | `d590960797916f542f50a036113c02457d7249195ecd9925cd26bb3aedb13723` |
| 应用导出的两份 RAW | `3425a177a919303ddb67db9f181f86b0ded5e9bacdb407557db6a2c03b608493` |

[DevEco 模拟器调试说明](https://developer.huawei.com/consumer/cn/doc/app/agc-help-debug-overview-0000001955332054/) · [通过 HDC 访问调试应用沙箱](https://developer.huawei.com/consumer/cn/doc/harmonyOS-guides/ide-device-file-explorer/)
