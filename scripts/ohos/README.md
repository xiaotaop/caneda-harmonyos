# 鸿蒙 ngspice 构建和联调

此脚本从固定的 [ngspice 47 源码包](https://sourceforge.net/projects/ngspice/files/ng-spice-rework/47/ngspice-47.tar.gz/download) 生成鸿蒙 CLI 或共享库。输入包会按 SHA-256 校验。需要 DevEco Native SDK、make、Bison、Flex、patch 和 tar，验证使用 Native SDK 26.0.0.105。构建目录建议放在 ASCII 且无空格的路径，以兼容 ngspice 自带的 Autotools。

```sh
sdk='/Applications/DevEco-Studio.app/Contents/sdk/default/openharmony/native'
src='/absolute/path/ngspice-47.tar.gz'
work=$(mktemp -d)
JOBS=8 scripts/ohos/build-ngspice.sh "$sdk" arm64-v8a cli "$src" "$work/cli"
JOBS=8 scripts/ohos/build-ngspice.sh "$sdk" arm64-v8a shared "$src" "$work/shared"
```

将 `arm64-v8a` 换成 `x86_64` 可构建对应 ABI。每次要给新目录。成功后的 `stage/` 包含 ELF、`share/ngspice/scripts/spinit` 和 `NGSPICE-COPYING`。共享库还包含 `sharedspice.h`，其 ELF SONAME 与入包文件名同为 `libngspice.so`。`elf.txt` 记录架构、解释器和直接依赖，共享构建还记录 C API 的导出。构建日志在输出目录。

SDK 的 Clang wrapper 和 LLD 负责 OHOS 目标与 sysroot。ngspice 47 的 `config.sub` 用 GNU/Linux 别名完成配置。首发验证的构建关闭 X11、XSPICE、OSDI、OpenMP、FFTW 和交互式 readline，保留常规 SPICE 模拟器件和 KLU。关闭 XSPICE 需要修复上游在此配置下引用未声明枚举项的问题。

鸿蒙 CLI 在读取网表前会先产生一个临时文件。未修复时，PC 模拟器的 ngspice 在系统临时目录上报 `tmpfile(): Permission denied`。补丁在 OHOS 上改用调用方提供的私有工作目录，创建唯一临时文件后立即解除目录项。应用须在启动前为每次运行建立可写目录，并用它作为 cwd。

## HAP 接入和验证

- 为目标 ABI 选择对应的 `stage/`。检查 `elf.txt`，由打包流程为 Qt 与 ngspice 一起协调同 ABI 的 `libc++_shared.so`。将所用 ngspice 版本、许可证和组件配置交给发布材料负责人。
- CLI 用包内可执行文件的绝对路径和独立参数运行。工作目录由应用创建，绝对的 `SPICE_LIB_DIR` 指向可读的 `share/ngspice`，`SPICE_ASCIIRAWFILE=1`。运行 `ngspice -n -b -r rc-step.raw rc-step.cir`，记录启动错误、退出码及日志，并取回 RAW。
- 若应用无法启动子进程，在进程内装载 `libngspice.so`，在工作线程按次串行调用。以控制退出回调、命令状态、有数据的瞬态 plot 和数值检查一起判定。ngspice 的向量描述结构会在后续查询时被复用，向量数据也归库所有，交给应用前要复制。
- 使用成员 B 的 [RC 基线 PR](https://github.com/xiaotaop/caneda-harmonyos/pull/1) 中的 `rc-step.cir` 与 `check_rc.py` 核对 RAW。验收仍需在统一 HAP 中复跑正常、错误和恢复链路。模拟器 shell 只验证 ELF、依赖和引擎行为。

### 共享库探针

[probe_ngspice_shared.c](../../tests/simulation/probe_ngspice_shared.c) 是独立测试程序。按以下方式交叉编译到与共享库一致的 ABI。它连续运行两次固定 RC，每次保存独立的 RAW。两轮之间销毁 plot 和移除旧电路，以验证新结果确实出自下一次运行。

```sh
clang="$sdk/llvm/bin/aarch64-unknown-linux-ohos-clang"
"$clang" -std=c11 -Wall -Wextra -Werror -I "$work/shared/stage" \
  tests/simulation/probe_ngspice_shared.c -L "$work/shared/stage" -lngspice \
  -o "$work/shared/stage/probe-ngspice-shared"
```

选择新的可写目录，将探针、同 ABI 的 `libngspice.so`、C++ 运行库和 `rc-step.cir` 放入该目录，再以该目录作为 cwd 执行探针。若通过 HDC shell 预检，在运行时把这个测试目录加入 `LD_LIBRARY_PATH`，并用 `SPICE_LIB_DIR` 指向暂存的运行资源。收到 `rc-first.raw`、`rc-second.raw` 后分别使用 `check_rc.py --raw` 校验。

### 11/24 验证记录

| 验证环境 | 结果 |
|---|---|
| Native SDK 26.0.0.105 | arm64-v8a 和 x86_64 的 CLI、共享库共四种构建通过；两种共享库的 SONAME 与预期 C API 导出均已核对。 |
| MateBook Pro 模拟器，HarmonyOS 7.0.0.107、API 26、arm64，HDC shell | CLI 正常、坏网表、重新运行的退出码为 0、1、0。坏网表没有生成 RAW；检查未发现残留的临时文件。两份有效 RAW 各 719 点，四个检查点最大误差约 11 µV（容差 3 mV）。 |
| 同一模拟器，HDC shell | 共享库探针在同一进程连续运行两次。两份结果各 719 点，均通过同一组数值检查。 |
| x86_64 模拟器、Caneda HAP | 仍待运行验证。 |
