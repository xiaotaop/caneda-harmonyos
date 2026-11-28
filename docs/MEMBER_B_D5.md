# 成员 B · D5 RC 对照归档

2026-11-28 复跑了 macOS arm64 上的 ngspice 47 桌面基准，并回读 D1–D4 的原始波形。固定网表、样例工具生成的 RC 网表、arm64 调试 HAP 内的 libngspice，以及坏网表后的重试，均得到相同的 719 个时间点和 `v(out)` 值。[逐点比较记录](evidence/b-d5/trace-comparison.txt)

| 归档文件 | 实测来源 |
|---|---|
| [desktop-fixed.raw.gz](evidence/b-d5/desktop-fixed.raw.gz) | D2，ngspice 47 读取固定网表，保存 `time` 和 `v(out)`。[桌面对照 PR](https://github.com/xiaotaop/caneda-harmonyos/pull/9) |
| [desktop-schematic.raw.gz](evidence/b-d5/desktop-schematic.raw.gz) | D2，样例工具从 `rc-lowpass.xsch` 生成网表，桌面 ngspice 保存 `time`、`v(in)` 和 `v(out)`。 |
| [arm64-hap.raw.gz](evidence/b-d5/arm64-hap.raw.gz) | D4，MateBook Pro 模拟器，HarmonyOS 7.0.0.107 SP8，API 26。独立调试 HAP 由应用进程写出并经 HDC 导出，首轮与重试的 RAW 两份字节相同，归档保留一份。[包内复测 PR](https://github.com/xiaotaop/caneda-harmonyos/pull/14) |
| [rc-lowpass.net.gz](evidence/b-d5/rc-lowpass.net.gz) | 桌面样例和 D4 调试 HAP 使用的网表，两个来源的网表字节相同。 |

固定网表和 HAP 的五点检查使用同一解析解与 3 mV 容差。样例工具按最近采样点对照 `expected.json`，最大误差约 0.398 mV。固定网表与 HAP 使用插值后再比较，最大误差约 22 µV。

| 检查时间 | 插值后实测 | 解析值 |
|---:|---:|---:|
| 0.500 ms | 0.000000 V | 0.000000 V |
| 2.003 ms | 3.165218 V | 3.165195 V |
| 4.003 ms | 4.751693 V | 4.751686 V |
| 6.003 ms | 4.966396 V | 4.966394 V |
| 7.000 ms | 4.987601 V | 4.987600 V |

D4 实测的 arm64 HAP SHA-256 为 `95ad1e2748537aca1a0e6a33fe96d81f7770106c1eb2d828b59d8668a38fb9af`。应用私有目录中的 CLI 在 `execve` 返回 `EACCES`。进程内 libngspice 遇到坏网表时，报告 `unknown subckt` 且 plot 仍为 `const`，随后重新运行有效网表。x86_64 探针已有构建产物。待验范围是 x86_64 运行、Caneda C++ 网表导出以及在统一调试 HAP 中显示 Qwt 波形。[D4 实测记录和双 ABI 包哈希](../tests/simulation/ohos-hap/README.md#2026-11-27-d4-验证结果)

## 复核

从仓库根目录运行以下命令。SHA-256 对解压后的原始文件计算。三个 RAW 使用各自的解析器，再比较共同的 `time` 与 `v(out)`。

```sh
archive="$PWD/docs/evidence/b-d5"
work=$(mktemp -d)
for file in "$archive"/*.gz; do
  gzip -dc "$file" > "$work/$(basename "$file" .gz)"
done
(cd "$work" && shasum -a 256 -c "$archive/SHA256SUMS")
python3 tests/simulation/check_rc.py --raw "$work/desktop-fixed.raw"
python3 tests/simulation/check_rc.py --raw "$work/arm64-hap.raw"
python3 - "$work" <<'PY'
from pathlib import Path
import runpy
import sys

work = Path(sys.argv[1])
read_rc = runpy.run_path("tests/simulation/check_rc.py")["read_rc_raw"]
read_sample = runpy.run_path("tests/files/verify_samples.py")["read_raw"]
names, rows = read_sample(work / "desktop-schematic.raw")
t, vout = names.index("time"), names.index("v(out)")
schematic = [(row[t], row[vout]) for row in rows]
assert len(schematic) == 719
assert schematic == read_rc(work / "desktop-fixed.raw") == read_rc(work / "arm64-hap.raw")
print("PASS: all 719 time and v(out) pairs match across the three archived traces")
PY
```

桌面重跑可使用 `python3 tests/simulation/check_rc.py --ngspice ngspice --output "$work/new-rc"` 与 `python3 tests/files/verify_samples.py --ngspice ngspice rc-lowpass`。
