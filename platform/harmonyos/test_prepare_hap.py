import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class PrepareHapTest(unittest.TestCase):
    def test_updates_explicit_sdk_versions_to_api_26(self):
        cases = [
            {"compatibleSdkVersion": "6.0.0(20)"},
            {"compatibleSdkVersion": "6.0.0(20)", "targetSdkVersion": "6.1.1(24)"},
            {"compatibleSdkVersion": "6.0.0(20)", "targetSdkVersion": "26.0.0",
             "compileSdkVersion": "6.1.1(24)"},
        ]
        for versions in cases:
            with self.subTest(versions=versions), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                template = root / "template"
                entry = template / "entry"
                constants = entry / "src/main/ets/common/QtAppConstants.ets"
                constants.parent.mkdir(parents=True)
                constants.write_text('export const APP_LIBRARY_NAME = "libtest.so";')
                (entry / "build-profile.json5").write_text(
                    '{"buildOption": {"externalNativeOptions": {}}}'
                )
                product = {"name": "default", "runtimeOS": "HarmonyOS", **versions}
                profile = {"app": {"products": [product]}}
                source_profile = template / "build-profile.json5"
                source_profile.write_text(json.dumps(profile))
                qt = root / "Qt prefix"
                config = qt / "lib/cmake/Qt5/Qt5Config.cmake"
                config.parent.mkdir(parents=True)
                config.touch()
                output = root / "output"
                subprocess.run(
                    [sys.executable, str(Path(__file__).with_name("prepare_hap.py")),
                     str(template), str(qt), str(output)],
                    check=True,
                )
                generated = json.loads((output / "build-profile.json5").read_text())
                expected = {**product, **dict.fromkeys(versions, "26.0.0")}
                self.assertEqual(generated["app"]["products"], [expected])
                self.assertEqual(json.loads(source_profile.read_text()), profile)


if __name__ == "__main__":
    unittest.main()
