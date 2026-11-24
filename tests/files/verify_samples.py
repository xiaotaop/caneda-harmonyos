#!/usr/bin/env python3
"""Regenerate Caneda netlists from sample schematics and check them in ngspice.

This tool mirrors what the application does at simulation time:

  FormatXmlSchematic::load  ->  FormatSpice::generateNetlist  ->  ngspice

It parses the .xsch file, rebuilds net connectivity from the geometry
(components, wires and port symbols all coincide by position), expands the
spice model syntax stored in each library .xsym file, and runs the resulting
netlist through ngspice.  The result is compared against the expected
checkpoints in expected.json.

Usage:
    python verify_samples.py                 # verify all samples
    python verify_samples.py rc-lowpass      # verify one sample
    python verify_samples.py --keep          # keep the generated work dir
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET


REPO = Path(__file__).resolve().parents[2]
SAMPLES = REPO / "tests" / "files" / "samples"
LIBS = REPO / "libraries" / "components"

# Directory name -> library name used in the .xsch files (see translations.xml)
LIBRARY_DIRS = {
    "Active": "active",
    "CMOS": "cmos",
    "Measurement": "measurement",
    "Miscellaneous": "miscellaneous",
    "Models": "models",
    "Passive": "passive",
    "Semiconductor": "semiconductor",
    "Simulations": "simulations",
    "Sources": "sources",
    "Transmission Lines": "transmission",
}


class NetlistError(Exception):
    pass


# --------------------------------------------------------------------------
# Library models
# --------------------------------------------------------------------------

def load_library_models():
    """Return {component name: {"syntax": str, "defaults": {prop: value}}}.

    Property defaults come from the symbol file.  When Caneda loads a
    schematic it calls Component::setComponentData(), which installs every
    property declared in the .xsym and then applies the values stored in the
    .xsch.  A property the schematic does not override therefore keeps its
    library default, which is why a sample never repeats m, scale, temp,
    dtemp, tc1, tc2 or noisy.
    """
    models = {}
    for lib_name, dir_name in LIBRARY_DIRS.items():
        directory = LIBS / dir_name
        if not directory.is_dir():
            continue
        for xsym in sorted(directory.glob("*.xsym")):
            try:
                root = ET.parse(xsym).getroot()
            except ET.ParseError as exc:
                raise NetlistError(f"{xsym}: {exc}") from exc
            name = root.get("name")
            if name is None:
                continue
            defaults = {"label": root.get("label", "")}
            group = root.find("properties")
            if group is not None:
                for prop in group.findall("property"):
                    key = prop.get("name")
                    if key:
                        defaults[key] = prop.get("default", "")
            models_node = root.find("models")
            if models_node is None:
                continue
            for model in models_node.findall("model"):
                if model.get("type") == "spice":
                    # XML attribute-value normalisation collapses tabs and
                    # newlines to single spaces.
                    syntax = re.sub(r"[\t\r\n]+", " ", model.get("syntax", ""))
                    models[name] = {"syntax": syntax, "defaults": defaults}
                    break
    return models


def load_library_ports():
    """Return {component name: [(port name, (x, y))]} for every library symbol."""
    ports = {}
    for lib_name, dir_name in LIBRARY_DIRS.items():
        directory = LIBS / dir_name
        if not directory.is_dir():
            continue
        for xsym in sorted(directory.glob("*.xsym")):
            root = ET.parse(xsym).getroot()
            name = root.get("name")
            if name is None:
                continue
            node = root.find("ports")
            entries = []
            if node is not None:
                for port in node.findall("port"):
                    x, y = (float(v) for v in port.get("pos", "0,0").split(","))
                    entries.append((port.get("name"), (x, y)))
            ports[name] = entries
    return ports


# --------------------------------------------------------------------------
# Schematic parsing
# --------------------------------------------------------------------------

def parse_point(text):
    x, y = text.split(",")
    # Caneda stores coordinates as QString::number(double), so integers have
    # no decimal part.  Round to tolerate representation noise.
    return (round(float(x), 6), round(float(y), 6))


def parse_schematic(path):
    root = ET.parse(path).getroot()
    if root.tag != "caneda":
        raise NetlistError(f"{path.name}: root element is <{root.tag}>, expected <caneda>")
    version = root.get("version", "")
    components, ports, wires = [], [], []
    for node in root:
        if node.tag == "components":
            for comp in node.findall("component"):
                props = {}
                group = comp.find("properties")
                if group is not None:
                    for prop in group.findall("property"):
                        props[prop.get("name")] = prop.get("value", "")
                components.append({
                    "name": comp.get("name"),
                    "library": comp.get("library"),
                    "pos": parse_point(comp.get("pos", "0,0")),
                    "properties": props,
                })
        elif node.tag == "ports":
            for port in node.findall("port"):
                ports.append({"name": port.get("name"), "pos": parse_point(port.get("pos", "0,0"))})
        elif node.tag == "wires":
            for wire in node.findall("wire"):
                wires.append((parse_point(wire.get("start", "0,0")), parse_point(wire.get("end", "0,0"))))
    return {"version": version, "components": components, "ports": ports, "wires": wires}


# --------------------------------------------------------------------------
# Connectivity (mirrors Port::getEquipotentialPorts / FormatSpice::generateNetlistTopology)
# --------------------------------------------------------------------------

class UnionFind:
    def __init__(self):
        self.parent = {}

    def find(self, item):
        self.parent.setdefault(item, item)
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[rb] = ra


def build_nets(schematic, library_ports):
    """Assign a net name to every component pin."""
    uf = UnionFind()

    # Each wire ties its two endpoints together.
    for start, end in schematic["wires"]:
        uf.union(start, end)

    # Each component pin sits at pos + symbol port offset.
    pins = []  # (component index, port name, position)
    for index, comp in enumerate(schematic["components"]):
        offsets = dict(library_ports.get(comp["name"], []))
        if not offsets:
            continue
        for port_name, (dx, dy) in offsets.items():
            pins.append((index, port_name, (round(comp["pos"][0] + dx, 6), round(comp["pos"][1] + dy, 6))))

    # Named port symbols rename the net they touch (ground/gnd -> 0).
    names = {}
    for port in schematic["ports"]:
        root = uf.find(port["pos"])
        label = (port["name"] or "").strip()
        if label.lower() in ("ground", "gnd", "0"):
            label = "0"
        names[root] = label

    net_of_pin = {}
    auto = 0
    seen_roots = {}
    for index, port_name, position in pins:
        root = uf.find(position)
        if root not in seen_roots:
            if root in names:
                seen_roots[root] = names[root]
            else:
                auto += 1
                seen_roots[root] = str(auto)
        net_of_pin[(index, port_name)] = seen_roots[root]
    return net_of_pin


# --------------------------------------------------------------------------
# Netlist generation (mirrors FormatSpice::generateNetlist)
# --------------------------------------------------------------------------

# FormatSpice::generateNetlist() uses the C++ char class
#   [\w =+-\\\\(\\)\n\*{}]
# where "\+-\\" is the RANGE 0x2B..0x5C.  Spelling the range out with
# explicit code points keeps the port faithful without depending on how a
# given engine treats an unescaped dash.  Note the range deliberately covers
# '.' and '(', which is what lets a directive like ".tran 10u 7m 0 10u" be
# collected at all.
_LONG_ARGS = r"[\w =+\x2b-\x5c\n*{}]"
CMD_PROPERTY = re.compile(r"%property\{([\w+-]+)\}")
CMD_PORT = re.compile(r"%port\{([\w+-]+)\}")
CMD_MODEL = re.compile(r"%model\{(" + _LONG_ARGS + r"+)\}")
CMD_DIRECTIVE = re.compile(r"%directive\{(" + _LONG_ARGS + r"+)\}")
CMD_SUBCIRCUIT = re.compile(r"%subcircuit\{(" + _LONG_ARGS + r"+)\}")


def expand_component(comp, index, net_of_pin, entry):
    """Expand one component's model syntax into a netlist line."""
    # Library defaults first, then whatever the schematic overrides.
    props = dict(entry["defaults"])
    props.update({k: v for k, v in comp["properties"].items() if v != ""})
    text = entry["syntax"]
    text = text.replace("%label", props.get("label", ""))
    text = text.replace("%n", "\n")

    def port_repl(match):
        key = (index, match.group(1))
        if key not in net_of_pin:
            raise NetlistError(f"{comp['name']} {comp['properties'].get('label')}: "
                               f"unknown port {match.group(1)}")
        return net_of_pin[key]

    text = CMD_PORT.sub(port_repl, text)
    text = CMD_PROPERTY.sub(lambda m: props.get(m.group(1), ""), text)

    collected = {"model": [], "directive": [], "subcircuit": []}
    for key, pattern in (("model", CMD_MODEL), ("directive", CMD_DIRECTIVE), ("subcircuit", CMD_SUBCIRCUIT)):
        for match in pattern.findall(text):
            if match not in collected[key]:
                collected[key].append(match)
        text = pattern.sub("", text)
    return text, collected


def generate_netlist(schematic, library_models, library_ports):
    net_of_pin = build_nets(schematic, library_ports)

    models, directives, subcircuits = [], [], []
    lines = []
    skipped = []
    for index, comp in enumerate(schematic["components"]):
        name = comp["name"]
        if name not in library_models:
            skipped.append(f"{name} ({comp['library']})")
            continue
        body, collected = expand_component(comp, index, net_of_pin, library_models[name])
        for model in collected["model"]:
            if model not in models:
                models.append(model)
        for directive in collected["directive"]:
            if directive not in directives:
                directives.append(directive)
        for sub in collected["subcircuit"]:
            if sub not in subcircuits:
                subcircuits.append(sub)
        body = body.strip()
        if body:
            lines.append(body)

    named_nodes = sorted({n for n in net_of_pin.values() if not n.isdigit() and n != "0"})

    out = ["* Spice automatic export. Generated by Caneda.", "", "* Spice netlist."]
    out.extend(lines)
    if models:
        out.append("")
        out.append("* Device models.")
        out.extend(f".model {m}" for m in models)
    if subcircuits:
        out.append("")
        out.append("* Subcircuits models.")
        for sub in subcircuits:
            out.extend([f".subckt {sub}", ".ends"])
    out.append("")
    out.append(".save " + " ".join(named_nodes) if named_nodes else ".save all")
    if directives:
        out.append("")
        out.append("* Spice directives.")
        out.extend(directives)

    text = "\n".join(out) + "\n"
    # Caneda collapses runs of spaces after assembly.
    text = re.sub(r" {2,}", " ", text)
    return text, skipped


# --------------------------------------------------------------------------
# RAW parsing
# --------------------------------------------------------------------------

def read_raw(path):
    """Parse the ASCII ngspice raw file written with SPICE_ASCIIRAWFILE=1."""
    with open(path, encoding="utf-8", errors="replace") as handle:
        lines = handle.read().splitlines()
    header = {}
    index = 0
    while index < len(lines):
        key, sep, value = lines[index].partition(":")
        if not sep:
            break
        header[key.strip()] = value.strip()
        index += 1
        if key.strip() == "Variables":
            break
    nvars = int(header["No. Variables"])
    npoints = int(header["No. Points"])
    names = []
    while lines[index].strip() != "Values:":
        names.append(lines[index].split()[1])
        index += 1
    index += 1
    samples = []
    for _ in range(npoints):
        row = []
        for _ in range(nvars):
            row.append(float(lines[index].split()[-1]))
            index += 1
        samples.append(row)
    return names, samples


def sample_at(names, samples, channel, moment):
    idx = names.index(channel)
    best = min(range(len(samples)), key=lambda i: abs(samples[i][0] - moment))
    return samples[best][idx], samples[best][0]


# --------------------------------------------------------------------------
# Runner
# --------------------------------------------------------------------------

def run_sample(sample_dir, ngspice, expected, keep):
    name = sample_dir.name
    xsch = sample_dir / f"{name}.xsch"
    if not xsch.is_file():
        raise NetlistError(f"missing {xsch}")

    library_models = load_library_models()
    library_ports = load_library_ports()
    schematic = parse_schematic(xsch)
    netlist, skipped = generate_netlist(schematic, library_models, library_ports)
    if skipped:
        raise NetlistError(f"components without a spice model: {', '.join(skipped)}")

    work = Path(tempfile.mkdtemp(prefix=f"caneda-{name}-"))
    try:
        net_path = work / f"{name}.net"
        raw_path = work / f"{name}.raw"
        net_path.write_text(netlist, encoding="ascii")

        env = dict(os.environ, SPICE_ASCIIRAWFILE="1", LC_ALL="C")
        result = subprocess.run(
            [ngspice, "-n", "-b", "-r", str(raw_path), str(net_path)],
            cwd=work, env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120, check=False,
        )
        if result.returncode != 0:
            raise NetlistError("ngspice failed:\n" + result.stdout.decode("utf-8", "replace"))
        if not raw_path.is_file():
            raise NetlistError("ngspice produced no raw file")

        names, samples = read_raw(raw_path)
        problems = []
        for check in expected["checkpoints"]:
            measured, actual_time = sample_at(names, samples, check["channel"], check["time"])
            error = abs(measured - check["value"])
            ok = error <= check["tolerance"]
            status = "ok" if ok else "FAIL"
            print(f"    {check['time']*1e3:9.3f} ms  {check['channel']:8s} "
                  f"expected {check['value']:.6f}  measured {measured:.6f}  "
                  f"delta {error:.6f}  {status}")
            if not ok:
                problems.append(f"{check['channel']} at {check['time']*1e3:.3f} ms: "
                                f"{measured:.6f} vs {check['value']:.6f}")
        if problems:
            raise NetlistError("; ".join(problems))
        print(f"    {len(samples)} points, {len(names)} variables")
        return work if keep else None
    finally:
        if not keep:
            shutil.rmtree(work, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("samples", nargs="*", help="sample names (default: all)")
    parser.add_argument("--ngspice", default=os.environ.get("NGSPICE", "ngspice"),
                        help="ngspice executable (default: ngspice from PATH)")
    parser.add_argument("--keep", action="store_true", help="keep the generated netlists")
    args = parser.parse_args()

    executable = shutil.which(args.ngspice) or args.ngspice
    expected_path = SAMPLES / "expected.json"
    if not expected_path.is_file():
        print(f"missing {expected_path}", file=sys.stderr)
        return 2
    expectations = json.loads(expected_path.read_text(encoding="utf-8"))

    selected = args.samples or [k for k in expectations if not k.startswith("_")]
    failures = 0
    for name in selected:
        if name not in expectations or name.startswith("_"):
            print(f"unknown sample {name}", file=sys.stderr)
            failures += 1
            continue
        print(f"[{name}]")
        try:
            kept = run_sample(SAMPLES / name, executable, expectations[name], args.keep)
            print("  PASS")
            if kept:
                print(f"  work dir: {kept}")
        except (NetlistError, OSError, KeyError, ValueError, subprocess.TimeoutExpired) as exc:
            print(f"  FAIL: {exc}")
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
