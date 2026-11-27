"""Check the R1--C1 drawing saved by the D4 desktop or emulator exercise."""
import argparse
import xml.etree.ElementTree as ET


def check(path):
    drawing = ET.parse(path).getroot()
    parts = []
    for part in drawing.findall("./components/component"):
        label = part.find("./properties/property[@name='label']")
        parts.append((part.get("name"), label.get("value") if label is not None else None,
                      part.get("pos"), part.get("transform")))
    expected = [("Resistor", "R1", "-80,0", "1,0,0,1,0,0"),
                ("Capacitor", "C1", "80,0", "1,0,0,1,0,0")]
    if len(parts) != 2 or set(parts) != set(expected):
        raise ValueError(f"Unexpected components: {parts}")
    wires = drawing.findall("./wires/wire")
    if len(wires) != 1 or {wires[0].get("start"), wires[0].get("end")} != {"-60,0", "60,0"}:
        raise ValueError(f"Unexpected wires: {[wire.attrib for wire in wires]}")
    print("PASS: R1 and C1 at the expected positions; one wire joins their inner pins.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("schematic")
    check(parser.parse_args().schematic)
