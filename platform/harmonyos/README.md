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
This confirms the platform probe. Caneda project editing, Qwt and ngspice
still require application integration.
