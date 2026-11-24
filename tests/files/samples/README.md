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
