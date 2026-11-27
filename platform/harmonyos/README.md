# Caneda HarmonyOS PC D2 · Qt platform probe

This standalone probe leaves the upstream desktop build intact. The generated
DevEco Stage project loads libcaneda_qt_probe.so through the Qt template's
ArkTS platform entry and displays a Qt Widgets window.

Target: MateBook Pro emulator (2in1), HarmonyOS 7.0.0.107, API 26, x86_64.
Host baseline: DevEco Studio 26.0.0.865 and Native SDK 26.0.0.105.

1. Obtain Qt for HarmonyOS 5.15.16, its Stage template under
   qtbase/src/harmonyos/templates, and a Qt installation built for HarmonyOS
   x86_64. Run with Python 3.9 or newer:

   ```sh
   python platform/harmonyos/prepare_hap.py <qt-template> <qt-x86-prefix> <new-output-directory>
   ```

2. Follow the Qt template packaging instructions to stage the x86_64 runtime
   libraries and libqohos.so in entry/libs/x86_64. Check all transitive ELF
   dependencies. Build from the generated project in DevEco Studio, using
   a PC-compatible module manifest and local debug signing.
3. D3 acceptance: install the debug HAP on the matching PC emulator and
   verify that the Caneda Qt Widgets window opens. Full Caneda, Qwt and
   ngspice integration are subsequent work.

[Qt Stage and CMake guide](https://wiki.qt.io/Qt_for_HarmonyOS/user_development/deveco_cmake_guide_cross_compile)
## Simulator verification

SDK 26.0.0.105 configured Qt for x86_64 with EGL and OpenGL ES. The full
qtbase build stopped in the unused EGLFS plugin; Qt Core, Gui and Widgets
were already available. Building the HarmonyOS platform plugin directly
with the generated qmake and mingw32-make produced platforms/libqohos.so.
The qtbase build directory can be used as the Qt prefix for the probe.

The official Stage template generated with API 26 built with Hvigor.
The debug HAP installed with hdc and QAbility displayed the
Caneda · Qt Widgets window on MateBook Pro (HarmonyOS 7.0, x86_64).
This confirms the platform probe.

## Caneda debug HAP (D4)

On Windows, use DevEco Studio 26 with Native SDK 26 and the DevEco CLI
configured in `DEVECO_SDK_HOME` and `DEVECO_CLI_CLT_PATH`. Run with
PowerShell 7 and Python 3.9 or later.

Prepare the following inputs:

- The official Qt 5.15.16 HarmonyOS Stage template under
  `qtbase/src/harmonyos/templates`.
- A HarmonyOS x86_64 Qt prefix with the host build tools, the Core, Gui,
  Widgets, Svg, PrintSupport, OpenGL, Concurrent and Network modules, and
  the OHOS platform and SVG plugins. A Qt cross-build tree with these
  components in the expected prefix layout also works.
- Qwt 6.1.6 headers and `libqwt.so` built for the same ABI and Qt prefix.
  Build `src/src.pro` with that Qt's qmake. With SDK Clang 15 and the Qt
  OHOS mkspec's `-Werror`, pass
  `QMAKE_CXXFLAGS+=-Wno-error=deprecated-copy-with-user-provided-copy`
  to qmake for Qwt's legacy copy assignment warning.

From the repository root, replace the following paths with your local inputs.
Use a new build directory for each packaging run.

```powershell
./platform/harmonyos/build_caneda_hap.ps1 `
  -Template C:/qt-ohos/qtbase/src/harmonyos/templates `
  -QtPrefix C:/qt-ohos/x86_64 `
  -QwtInclude C:/qwt-6.1.6/src `
  -QwtLibrary C:/qwt-build/lib/libqwt.so `
  -BuildDirectory C:/caneda-build/d4
```

The script cross-builds the current Caneda sources, stages native libraries
and resources, then runs Hvigor in debug mode. It prints the HAP path and
SHA-256. The HAP uses `com.caneda.desktop` with the official Qt Stage ability
entry. The retained probe command above still generates the template bundle.

On the API 26 x86_64 PC emulator, install this unsigned debug package
and start the application:

```powershell
hdc list targets
hdc install C:/caneda-build/d4/stage/entry/build/default/outputs/default/entry-default-unsigned.hap
hdc shell aa start -a QAbility -b com.caneda.desktop
```

Verify that the Caneda main window and component library load. Use the bundled
RC sample at `share/caneda/samples/rc-lowpass/rc-lowpass.xsch` under the app
resource directory for a file-open smoke test. This debug build contains Qwt
for the waveform view. The ngspice engine is integrated separately.

GitHub Actions checks the Stage generator and the desktop build on a hosted
Linux runner. The PowerShell script runs the HarmonyOS packaging on the
configured DevEco host.
