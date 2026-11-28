# 鸿蒙应用内 ngspice RC 探针

独立调试应用 `com.example.canedangspiceprobe`。构建时用样例测试工具从 `rc-lowpass.xsch` 生成网表。应用启动后在新的私有目录试跑 CLI，再用包内 libngspice 执行 RC → 坏网表 → RC 重试，输出 `shared.raw` 和 `shared-retry.raw`。完整 Caneda、Qt/Qwt 及 C++ 网表导出由集成包验证。

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
hdc shell hilog -x -T CanedaSpice
# 将 run 设为上条日志中以 rc- 开头的本次运行目录。
for name in shared shared-retry; do
  hdc file recv -b "$bundle" "./data/storage/el2/base/haps/entry/files/$run/$name.raw" "$work/$name.raw"
  python3 tests/simulation/check_rc.py --raw "$work/$name.raw"
done
```

## 2026-11-27 D4 验证结果

arm64-v8a 和 x86_64 调试 HAP 离线打包通过。实际运行环境为 MateBook Pro PC 模拟器、HarmonyOS 7.0.0.107 SP8、API 26、arm64-v8a，应用 PID 5008。

| 操作 | 实测结果 |
|---|---|
| CLI 启动 | 已包含 `spinit` 并设置资源路径，应用私有目录内的可执行文件在 `execve` 阶段返回 `EACCES (13)`。 |
| libngspice 首轮 | 运行由样例工具导出的 RC 网表，得到 719 点。 |
| 坏网表 | 先清理上轮 plot，再提交引用未定义子电路的网表。收到 `unknown subckt`，当前 plot 仍为 `const`，没有残留上一轮曲线。 |
| libngspice 重试 | 重新加载 RC，得到 719 点。用 HDC 导出两份 RAW，字节一致，5 个检查点最大误差约 22 µV，容差 3 mV。 |

| D4 产物 | SHA-256 |
|---|---|
| arm64 调试 HAP | `95ad1e2748537aca1a0e6a33fe96d81f7770106c1eb2d828b59d8668a38fb9af` |
| x86_64 调试 HAP | `5d942f8c9557a804fac40e1d06a3558ff4ec40fb2666874f04d868848bc0b2fc` |
| 样例网表 | `0bbd85c348132daf28c476fe22098c2247c289d9ec4763dd44911f3a07407aa5` |
| 应用导出的两份 RAW | `1d2d6fc1f919566de543b1e6787634b54c6b1cf0f457c1c355f8cbb1ecff29f1` |

首轮 Caneda 集成建议使用进程内 libngspice，按次串行运行。包内样例在只读资源目录，需把 Caneda 导出网表、日志和 RAW 放到与工程路径分开的私有运行目录。只有当前次生成有效 plot 后才把结果交给 Qwt，错误后仍可再次开始。x86_64 调试包已构建，统一 Caneda HAP 和 x86_64 模拟器上的调用待验。

## 2026-11-26 D3 验证结果

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
