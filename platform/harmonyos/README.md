# Build Caneda for HarmonyOS PC

Use the [Caneda debug HAP](#caneda-debug-hap-d4) to run the application and
bundled schematics. The [Qt platform probe](#qt-platform-probe-d2) checks
the Stage template and Qt Widgets on their own.

The validated target is the DevEco Studio MateBook Pro (2in1) emulator with
HarmonyOS 7.0.0.107, API 26 and x86_64. The Windows host baseline uses
DevEco Studio 26.0.0.865 and Native SDK 26.0.0.105.

## Qt platform probe (D2)

The generated DevEco Stage project loads `libcaneda_qt_probe.so` through the
Qt template's ArkTS platform entry and displays a Qt Widgets window.

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

### Simulator verification

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

### Prepare the Windows build host

Use PowerShell 7 and Python 3.9 or later. Set both environment variables in
the PowerShell session used for the build. Replace the example paths with
your installation paths.

| Input | Expected layout |
|---|---|
| `DEVECO_SDK_HOME` | SDK root containing `default/openharmony/native` |
| `DEVECO_CLI_CLT_PATH` | Command-line tools root containing `bin/hvigorw.bat` |
| Qt Stage template | Qt for HarmonyOS 5.15.16 source directory `qtbase/src/harmonyos/templates` |
| Qt prefix | HarmonyOS x86_64 Qt installation or cross-build tree with host tools and the Core, Gui, Widgets, Svg, PrintSupport, OpenGL, Concurrent and Network modules |
| Qt plugins | `platforms/libqohos.so`, `imageformats/libqsvg.so` and `iconengines/libqsvgicon.so` under the Qt prefix's `plugins` directory |
| Qwt | Qwt 6.1.6 headers and `libqwt.so` built for the same ABI and Qt prefix |

Build Qwt's `src/src.pro` with that Qt's qmake. With SDK Clang 15 and the
Qt OHOS mkspec's `-Werror`, pass
`QMAKE_CXXFLAGS+=-Wno-error=deprecated-copy-with-user-provided-copy`
to qmake for Qwt's legacy copy assignment warning.

```powershell
$env:DEVECO_SDK_HOME = 'C:/DevEco/command-line-tools/sdk'
$env:DEVECO_CLI_CLT_PATH = 'C:/DevEco/command-line-tools'
$hdc = Join-Path $env:DEVECO_SDK_HOME 'default/openharmony/toolchains/hdc.exe'
python --version
Test-Path (Join-Path $env:DEVECO_SDK_HOME 'default/openharmony/native/build/cmake/ohos.toolchain.cmake')
Test-Path (Join-Path $env:DEVECO_CLI_CLT_PATH 'bin/hvigorw.bat')
Test-Path $hdc
```

The build script checks the SDK tools, required runtime files, and the ELF
architecture of the Qt and Qwt libraries before compiling.

### Build and locate the HAP

Run from the repository root. Replace the input paths and use a fresh build
directory for each run.

```powershell
$buildDir = 'C:/caneda-build/debug-x86_64-01'
git rev-parse HEAD
./platform/harmonyos/build_caneda_hap.ps1 `
  -Template 'C:/qt-ohos/qtbase/src/harmonyos/templates' `
  -QtPrefix 'C:/qt-ohos/x86_64' `
  -QwtInclude 'C:/qwt-6.1.6/src' `
  -QwtLibrary 'C:/qwt-build/lib/libqwt.so' `
  -BuildDirectory $buildDir

$hap = Join-Path $buildDir 'stage/entry/build/default/outputs/default/entry-default-unsigned.hap'
Get-FileHash -LiteralPath $hap -Algorithm SHA256
```

The script cross-builds the current Caneda sources, stages native libraries
and resources, then runs Hvigor in debug mode. The unsigned debug HAP uses
`com.caneda.desktop` and the Qt Stage ability `QAbility`. It includes the
component library, Qwt, and the RC low-pass and diode rectifier samples.
See the [ngspice build and integration notes](../../scripts/ohos/README.md)
for the separate simulation engine work.

### Install and open the bundled RC sample

Start the API 26 x86_64 MateBook Pro emulator in DevEco Studio. In the same
PowerShell session, select its target ID and install the HAP. Use `install -r`
for an update over an existing debug installation.

```powershell
& $hdc list targets
$target = '<emulator target from hdc list targets>'
& $hdc -t $target shell param get const.product.cpu.abilist
& $hdc -t $target install $hap
& $hdc -t $target shell aa start -a QAbility -b com.caneda.desktop
```

Check the main window and component library. Then stop the running ability
and launch it with the packaged RC schematic as a Qt startup argument.
Quoting the JSON value for the device shell keeps the double quotes around
the path.

```powershell
$rc = '/data/storage/el1/bundle/entry/resources/resfile/share/caneda/samples/rc-lowpass/rc-lowpass.xsch'
$argsJson = ConvertTo-Json -InputObject @($rc) -Compress
$launchRc = "aa start -a QAbility -b com.caneda.desktop --ps io.qt.appArgsJson '$argsJson'"
& $hdc -t $target shell aa force-stop com.caneda.desktop
& $hdc -t $target shell $launchRc
```

Check that the `rc-lowpass.xsch` tab opens and the schematic and component
tree are visible. Record the Git commit, HAP SHA-256 and size, emulator
version and ABI, and the result with a screenshot or log. This smoke test
covers package installation, startup, libraries and sample loading.

### Checks and common build failures

GitHub Actions runs the Stage generator tests and the desktop CMake build
on Linux. Run the generator tests locally with
`python platform/harmonyos/test_prepare_hap.py`. The Windows build command
above performs the HarmonyOS cross-build and packaging. HDC and the emulator
provide the runtime check.

| Symptom | Check |
|---|---|
| `Missing build input` | Check the two DevEco roots and the exact path in the error. Verify the required Qt plugin or library exists under the selected prefix. |
| `Expected an x86_64 ELF library` | Use Qt and Qwt from the HarmonyOS x86_64 cross-build. |
| Stage output already exists | Pick another `-BuildDirectory`. |
| `hdc list targets` shows `[Empty]` | Start the emulator in DevEco Studio, wait for its desktop, and run the SDK's HDC command again. |

### D4 emulator evidence

On 2026-11-27, the D4 unsigned debug HAP built from the sources in
`c49f254f` installed and launched on the MateBook Pro emulator
(HarmonyOS 7.0.0.107, API 26, x86_64).

| Package field | Verified value |
|---|---|
| Bundle name | `com.caneda.desktop` |
| Version | `1.0.0` (version code `1000000`) |
| File size | 33,944,321 bytes |
| SHA-256 | `f7064c4785e9ef43666e848912f29a9e65d27c9cf58f1927c192a7bcd065e8a2` |

The [emulator screenshot](../../docs/evidence/leader-d4/01-open-rc-sample.jpeg)
shows the component library and bundled RC schematic after launching with
`io.qt.appArgsJson` pointing to
`/data/storage/el1/bundle/entry/resources/resfile/share/caneda/samples/rc-lowpass/rc-lowpass.xsch`.
This smoke test covered installation, startup, library loading, and opening
the bundled sample. Editing, saving, and ngspice execution were outside the
smoke test.
