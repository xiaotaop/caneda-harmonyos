# Caneda 首发版样例工程

两套样例用于首发版本的验收：同一份 HAP 必须能打开、编辑、保存重开，并交给 ngspice 仿真出波形。样例是普通 Caneda 工程文件，不含特制格式。

| 目录 | 电路 | 用途 |
|---|---|---|
| `rc-lowpass/` | 脉冲源 + R1 1 kΩ + C1 1 µF | 一阶低通阶跃响应，时间常数 1 ms，有闭式解可对照 |
| `diode-rectifier/` | 50 Hz 正弦源 + D1 + R1 1 kΩ ∥ C1 470 µF | 半波整流带滤波，覆盖二极管模型和稳态纹波 |

## 打开方式

直接打开各目录下的 `.xsch`。元件引用了 `libraries/components/` 中的库符号（Passive、Sources、Semiconductor、Simulations），因此库路径必须能被应用解析，与正常安装后的行为一致。

## 数值对照

`expected.json` 记录检查点。RC 样例的值来自有限上升沿的闭式解，与仿真器无关；整流样例的值来自 ngspice-47 实测。

```sh
python3 tests/files/verify_samples.py --ngspice ngspice
```

脚本会解析 `.xsch`、按几何重建网表连接、展开库中的 spice 模型、生成 `.net` 并调用 ngspice，再逐点比对。这条路径与 `FormatXmlSchematic::load` → `FormatSpice::generateNetlist` 一致，可在没有 GUI 的环境里回归"样例是否仍能仿真"。

## 已知限制

- 样例坐标落在网格上（引脚以 20 为单位），便于在模拟器里手动编辑。
- 仿真走 `.tran` 指令；`Transient Simulation` 元件的 `tstep`/`tstop` 已在样例中设好。
- 网表节点名为 `in`、`out` 和 `0`（`ground` 端口映射为 SPICE 地）。

## D5 回归记录（2026-11-28）

在 Windows 桌面环境使用 Python 3.13.11 与 ngspice-47 重新执行：

```powershell
python tests/files/verify_samples.py --ngspice D:\msys64\ucrt64\bin\ngspice.exe
```

| 样例 | 结果 | 检查点数 | 最大数值偏差 | 容差 |
|---|---|---:|---:|---:|
| RC 低通 | PASS | 719 | 0.000398 V | 0.01 V |
| 二极管整流 | PASS | 6008 | 0.093940 V | 0.3 V |

命令退出码为 0。两套样例的 `.xsch` 与 `expected.json` 均无需因本次回归修改；完整输出见 [verify-samples.log](../../../docs/evidence/c-d5/verify-samples.log)，文件哈希见 [samples-sha256.txt](../../../docs/evidence/c-d5/samples-sha256.txt)，D5 记录见 [MEMBER_C_D5_SAMPLES_ACCEPTANCE.md](../../../docs/MEMBER_C_D5_SAMPLES_ACCEPTANCE.md)。

该结果证明样例仍可生成正确网表并仿真。另在最新 HAP（SHA-256 `026ec6d6…`）中完成应用私有目录 `files/rc-lowpass.xsch` 的 Save As、覆盖安装重启后 Open、File > Close 后再次 Open，D5 应用内读写闭环已通过，见 [d5-final-verification.log](../../../docs/evidence/c-d5/d5-final-verification.log)。
