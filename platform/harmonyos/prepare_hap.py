"""Prepare a separate DevEco project from the Qt 5 HarmonyOS Stage template."""
import argparse
import json
from pathlib import Path
import re
import shutil


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("template", type=Path)
    parser.add_argument("qt_prefix", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    entry = args.template / "entry"
    constants = entry / "src/main/ets/common/QtAppConstants.ets"
    prefix = args.qt_prefix.resolve()
    output = args.output.resolve()
    if output.exists() or output.is_relative_to(args.template.resolve()):
        parser.error("output must be a new directory outside the template")
    if not constants.is_file() or not (entry / "build-profile.json5").is_file():
        parser.error("expected the Qt 5 HarmonyOS Stage template")
    if not (prefix / "lib/cmake/Qt5/Qt5Config.cmake").is_file():
        parser.error("expected an x86_64 HarmonyOS Qt 5 installation prefix")

    source = constants.read_text(encoding="utf-8")
    updated, count = re.subn(
        r'(APP_LIBRARY_NAME\s*=\s*)[\'\"].*?[\'\"]',
        r"\g<1>'libcaneda_qt_probe.so'", source,
    )
    if count != 1:
        parser.error("expected one APP_LIBRARY_NAME declaration")
    module_profile = (entry / "build-profile.json5").read_text(encoding="utf-8")
    if re.search(r'\bexternalNativeOptions\b', module_profile):
        parser.error("use the original stage template without externalNativeOptions")
    profile_start = re.search(r'(["\']?buildOption["\']?\s*:\s*\{)', module_profile)
    if not profile_start:
        parser.error("template entry/build-profile.json5 has no buildOption object")
    native = {
        "path": "./src/main/caneda-probe/CMakeLists.txt",
        "arguments": f'-DCANEDA_QT_PREFIX="{prefix.as_posix()}"',
        "abiFilters": ["x86_64"],
    }
    position = profile_start.end()
    remainder = module_profile[position:].lstrip()
    separator = "" if remainder.startswith("}") else ","
    updated_profile = (module_profile[:position] + "\n    externalNativeOptions: "
                       + json.dumps(native) + separator + module_profile[position:])

    shutil.copytree(args.template, output)
    target_entry = output / "entry"
    (output / constants.relative_to(args.template)).write_text(updated, encoding="utf-8")
    (target_entry / "build-profile.json5").write_text(updated_profile, encoding="utf-8")
    native_dir = target_entry / "src/main/caneda-probe"
    native_dir.mkdir()
    for name in ("CMakeLists.txt", "main.cpp"):
        shutil.copy2(Path(__file__).with_name(name), native_dir / name)


if __name__ == "__main__":
    main()
