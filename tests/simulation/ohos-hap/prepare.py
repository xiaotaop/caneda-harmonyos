"""Generate an isolated Stage HAP to exercise the two ngspice backends."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sdk", type=Path, help="DevEco OpenHarmony Native SDK")
    parser.add_argument("abi", choices=("arm64-v8a", "x86_64"))
    parser.add_argument("cli_stage", type=Path)
    parser.add_argument("shared_stage", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    fixture = here.parent / "rc-step.cir"
    arch = "aarch64" if args.abi == "arm64-v8a" else "x86_64"
    compiler = args.sdk / "llvm/bin" / f"{arch}-unknown-linux-ohos-clang++"
    runtime = args.sdk / "llvm/lib" / f"{arch}-linux-ohos" / "libc++_shared.so"
    cli = args.cli_stage / "ngspice"
    library = args.shared_stage / "libngspice.so"
    license_file = args.shared_stage / "NGSPICE-COPYING"
    inputs = (fixture, compiler, runtime, cli, library, args.shared_stage / "sharedspice.h",
              license_file)
    for path in inputs:
        if not path.is_file():
            parser.error(f"missing input: {path}")

    machine = 183 if args.abi == "arm64-v8a" else 62
    for path in (cli, library, runtime):
        with path.open("rb") as elf:
            header = elf.read(20)
        if header[:6] != b"\x7fELF\x02\x01" or int.from_bytes(header[18:20], "little") != machine:
            parser.error(f"expected a 64-bit little-endian {args.abi} ELF: {path}")

    out = args.output.resolve()
    out.mkdir()

    def write(path, data):
        target = out / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(data, encoding="utf-8")

    def config(path, data):
        write(path, json.dumps(data, indent=2) + "\n")

    config("oh-package.json5", {
        "name": "caneda-ngspice-d3-probe", "version": "0.1.0", "modelVersion": "6.0.0",
        "dependencies": {},
    })
    config("hvigor/hvigor-config.json5", {"modelVersion": "6.0.0", "dependencies": {}})
    write("hvigorfile.ts", "import { appTasks } from '@ohos/hvigor-ohos-plugin';\n"
          "export default { system: appTasks, plugins: [] };\n")
    write("entry/hvigorfile.ts", "import { hapTasks } from '@ohos/hvigor-ohos-plugin';\n"
          "export default { system: hapTasks, plugins: [] };\n")
    config("build-profile.json5", {
        "app": {
            "products": [{
                "name": "default", "compatibleSdkVersion": "26.0.0",
                "targetSdkVersion": "26.0.0", "runtimeOS": "HarmonyOS",
            }],
            "buildModeSet": [{"name": "debug"}],
        },
        "modules": [{"name": "entry", "srcPath": "./entry",
                     "targets": [{"name": "default", "applyToProducts": ["default"]}]}],
    })
    config("entry/build-profile.json5", {
        "apiType": "stageMode", "buildOption": {}, "targets": [{"name": "default"}],
    })
    config("entry/oh-package.json5", {
        "name": "entry", "version": "0.1.0",
        "dependencies": {"libngspice_probe.so": "file:./types/ngspice_probe"},
    })
    config("entry/types/ngspice_probe/oh-package.json5", {
        "name": "libngspice_probe.so", "version": "0.1.0", "types": "./index.d.ts",
    })
    write("entry/types/ngspice_probe/index.d.ts", "export const run: (dir: string) => string;\n")
    config("AppScope/app.json5", {"app": {
        "bundleName": "com.example.canedangspiceprobe", "vendor": "Caneda test",
        "versionCode": 1, "versionName": "0.1.0",
        "label": "$string:app_name", "icon": "$media:probe",
    }})
    config("AppScope/resources/base/element/string.json", {
        "string": [{"name": "app_name", "value": "Caneda ngspice Probe"}],
    })
    write("AppScope/resources/base/media/probe.svg",
          '<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96">'
          '<rect width="96" height="96" fill="#176977"/></svg>\n')
    module = "entry/src/main"
    config(f"{module}/module.json5", {"module": {
        "name": "entry", "type": "entry", "mainElement": "EntryAbility",
        "deviceTypes": ["2in1"], "deliveryWithInstall": True, "installationFree": False,
        "pages": "$profile:main_pages",
        "abilities": [{
            "name": "EntryAbility", "srcEntry": "./ets/entryability/EntryAbility.ets",
            "icon": "$media:probe", "label": "$string:app_name",
            "startWindowIcon": "$media:probe", "startWindowBackground": "$color:background",
            "exported": True,
        }],
    }})
    config(f"{module}/resources/base/element/color.json", {
        "color": [{"name": "background", "value": "#FFFFFF"}],
    })
    config(f"{module}/resources/base/profile/main_pages.json", {"src": ["pages/Index"]})
    for filename, subdir in (("EntryAbility.ets", "entryability"), ("Index.ets", "pages")):
        write(f"{module}/ets/{subdir}/{filename}", (here / filename).read_text(encoding="utf-8"))

    raw = out / module / "resources/rawfile"
    raw.mkdir()
    shutil.copyfile(fixture, raw / fixture.name)
    shutil.copyfile(cli, raw / "ngspice.bin")
    shutil.copyfile(license_file, raw / license_file.name)

    libs = out / "entry/libs" / args.abi
    libs.mkdir(parents=True)
    shutil.copyfile(library, libs / library.name)
    shutil.copyfile(runtime, libs / runtime.name)
    subprocess.run([
        str(compiler.resolve()), "-std=c++17", "-Wall", "-Wextra", "-Werror", "-fPIC", "-shared",
        "-I", str(args.shared_stage.resolve()), str(here / "probe.cpp"), "-L", str(libs),
        "-lngspice", "-lace_napi.z", "-o", str(libs / "libngspice_probe.so"),
    ], check=True)


if __name__ == "__main__":
    main()
