#!/usr/bin/env python3
"""Run or check the real-valued ngspice raw file for rc-step.cir."""

import argparse
from bisect import bisect_left
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys


def read_rc_raw(path):
    """Read the single ASCII transient plot with time and v(out)."""
    with path.open(encoding="utf-8") as raw:
        header = {}
        for line in raw:
            key, sep, value = line.partition(":")
            if not sep:
                raise ValueError("invalid raw header")
            if key == "Variables":
                break
            header[key] = value.strip()
        else:
            raise ValueError("missing raw variables")

        if (header.get("Plotname"), header.get("Flags"), header.get("No. Variables")) != (
            "Transient Analysis", "real", "2"
        ):
            raise ValueError("expected one real transient plot with two variables")
        if raw.readline().split() != ["0", "time", "time"]:
            raise ValueError("missing time axis")
        if raw.readline().split() != ["1", "v(out)", "voltage"]:
            raise ValueError("missing v(out) waveform")
        if raw.readline().strip() != "Values:":
            raise ValueError("expected ASCII raw data")

        expected_count = int(header["No. Points"])
        if expected_count < 2:
            raise ValueError("expected at least two points")
        samples = []
        # Blank lines may separate successive points.
        values = (line.split() for line in raw if line.strip())
        for index in range(expected_count):
            time_fields = next(values, [])
            voltage_fields = next(values, [])
            if len(time_fields) != 2 or time_fields[0] != str(index) or len(voltage_fields) != 1:
                raise ValueError(f"missing or malformed point {index}")
            time_s, volts = float(time_fields[1]), float(voltage_fields[0])
            if not (math.isfinite(time_s) and math.isfinite(volts)):
                raise ValueError(f"non-finite point {index}")
            if samples and not 0 < time_s - samples[-1][0] <= 10.1e-6:
                raise ValueError(f"time step at point {index} must be positive and at most 10.1 us")
            samples.append((time_s, volts))

        if next(values, None) is not None:
            raise ValueError("unexpected data after transient plot")
    return samples


def compare(samples):
    stop = 0.007
    if len(samples) < 2 or abs(samples[0][0]) > 1e-9 or abs(samples[-1][0] - stop) > 1e-9:
        raise ValueError("expected coverage from 0 to 7 ms")

    # Exact response to a linear 1 us input rise starting at 1 ms.
    tau, rise, delay = 0.001, 0.000001, 0.001
    at_end_of_rise = 5 * (1 + tau / rise * math.expm1(-rise / tau))
    times = [time_s for time_s, _ in samples]
    # Match the checkpoint times of the rc-lowpass schematic sample.
    for time_s in (0.0005, 0.002003, 0.004003, 0.006003, stop):
        if time_s == stop:
            measured = samples[-1][1]
        else:
            i = bisect_left(times, time_s)
            t0, v0 = samples[i - 1]
            t1, v1 = samples[i]
            measured = v0 + (v1 - v0) * (time_s - t0) / (t1 - t0)
        expected = (
            0.0 if time_s < delay else
            5 - (5 - at_end_of_rise) * math.exp(-(time_s - delay - rise) / tau)
        )
        error = abs(measured - expected)
        print(f"{time_s * 1e3:.3f} ms: {measured:.6f} V, expected {expected:.6f} V, error {error:.6f} V")
        if error > 0.003:
            raise ValueError(f"v(out) at {time_s * 1e3:.3f} ms exceeds 3 mV tolerance")
    print(f"PASS: {len(samples)} points, all checkpoints within 3 mV")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--ngspice", help="run the netlist with this ngspice executable")
    mode.add_argument("--raw", type=Path, help="check an existing ASCII raw file from rc-step.cir")
    parser.add_argument("--output", type=Path, help="new directory for the raw file and log from --ngspice")
    args = parser.parse_args()
    if bool(args.ngspice) != bool(args.output):
        parser.error("--ngspice requires --output, which must not already exist")

    try:
        raw_path = args.raw
        if args.ngspice:
            executable = shutil.which(args.ngspice)
            if executable is None:
                raise ValueError(f"ngspice executable not found: {args.ngspice}")
            executable = str(Path(executable).resolve())
            output = args.output.resolve()
            output.mkdir()
            raw_path = output / "rc-step.raw"
            log_path = output / "rc-step.log"
            netlist = Path(__file__).with_name("rc-step.cir").resolve()
            env = dict(os.environ, LC_ALL="C", SPICE_ASCIIRAWFILE="1")
            with log_path.open("wb") as log:
                run = subprocess.run(
                    [executable, "-n", "-b", "-r", raw_path.name, str(netlist)],
                    cwd=output, env=env, stdin=subprocess.DEVNULL,
                    stdout=log, stderr=subprocess.STDOUT, timeout=30, check=False,
                )
            if run.returncode != 0:
                raise ValueError(f"ngspice exited with {run.returncode}; see {log_path}")
        compare(read_rc_raw(raw_path))
    except (OSError, ValueError, KeyError, subprocess.TimeoutExpired) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
