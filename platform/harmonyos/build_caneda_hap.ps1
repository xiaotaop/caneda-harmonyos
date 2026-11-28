# Build the Caneda application and package it using the official Qt Stage template.
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Template,
    [Parameter(Mandatory)][string]$QtPrefix,
    [Parameter(Mandatory)][string]$QwtInclude,
    [Parameter(Mandatory)][string]$QwtLibrary,
    [Parameter(Mandatory)][string]$BuildDirectory
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

function Invoke-BuildStep {
    param([string]$Program, [string[]]$Arguments)
    & $Program @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Program exited with code $LASTEXITCODE."
    }
}

if (!$env:DEVECO_SDK_HOME -or !$env:DEVECO_CLI_CLT_PATH) {
    throw 'Set DEVECO_SDK_HOME and DEVECO_CLI_CLT_PATH to the DevEco SDK and command-line tools.'
}
$repo = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$templatePath = (Resolve-Path -LiteralPath $Template).Path
$qt = (Resolve-Path -LiteralPath $QtPrefix).Path
$qwtIncludePath = (Resolve-Path -LiteralPath $QwtInclude).Path
$qwt = (Resolve-Path -LiteralPath $QwtLibrary).Path
if ((Split-Path -Leaf $qwt) -ne 'libqwt.so') {
    throw 'Qwt must be the HarmonyOS x86_64 libqwt.so.'
}
$nativeSdk = Join-Path $env:DEVECO_SDK_HOME 'default/openharmony/native'
$cmake = Join-Path $nativeSdk 'build-tools/cmake/bin/cmake.exe'
$ninja = Join-Path $nativeSdk 'build-tools/cmake/bin/ninja.exe'
$toolchain = Join-Path $nativeSdk 'build/cmake/ohos.toolchain.cmake'
$hvigor = Join-Path $env:DEVECO_CLI_CLT_PATH 'bin/hvigorw.bat'
$runtime = @(
    $qwt
    (Join-Path $nativeSdk 'llvm/lib/x86_64-linux-ohos/libc++_shared.so')
    (Join-Path $qt 'plugins/platforms/libqohos.so')
    (Join-Path $qt 'plugins/imageformats/libqsvg.so')
    (Join-Path $qt 'plugins/iconengines/libqsvgicon.so')
)
$runtime += @('Core','Gui','Widgets','Svg','PrintSupport','OpenGL','Concurrent','Network') |
    ForEach-Object { Join-Path $qt "lib/libQt5$_.so" }
foreach ($file in @($cmake, $ninja, $toolchain, $hvigor) + $runtime) {
    if (!(Test-Path -LiteralPath $file -PathType Leaf)) {
        throw "Missing build input: $file"
    }
}
$readelf = Join-Path $nativeSdk 'llvm/bin/llvm-readelf.exe'
foreach ($file in $runtime) {
    $elf = & $readelf -h $file
    if ($LASTEXITCODE -ne 0 -or !($elf -match 'Machine:.*X86-64')) {
        throw "Expected an x86_64 ELF library: $file"
    }
}

$build = (New-Item -ItemType Directory -Path $BuildDirectory -Force).FullName
$stage = Join-Path $build 'stage'
$nativeBuild = Join-Path $build 'native'
$installed = Join-Path $build 'installed'
$deviceResfile = '/data/storage/el1/bundle/entry/resources/resfile'

Invoke-BuildStep python @((Join-Path $PSScriptRoot 'prepare_hap.py'), $templatePath, $qt, $stage, '--caneda')
Invoke-BuildStep $cmake @(
    '-S', $repo, '-B', $nativeBuild, '-G', 'Ninja',
    "-DCMAKE_MAKE_PROGRAM=$ninja", "-DCMAKE_TOOLCHAIN_FILE=$toolchain",
    '-DOHOS_ARCH=x86_64', "-DCANEDA_QT_PREFIX=$qt",
    "-DCMAKE_INSTALL_PREFIX=$deviceResfile",
    "-DQWT_INCLUDE_DIR=$qwtIncludePath", "-DQWT_LIBRARY=$qwt"
)
Invoke-BuildStep $cmake @('--build', $nativeBuild, '--parallel', '8')
Invoke-BuildStep $cmake @('--install', $nativeBuild, '--prefix', $installed)

$libs = (New-Item -ItemType Directory -Path (Join-Path $stage 'entry/libs/x86_64') -Force).FullName
Copy-Item -LiteralPath ($runtime + (Join-Path $installed 'bin/libcaneda.so')) -Destination $libs
$resfile = (New-Item -ItemType Directory -Path (Join-Path $stage 'entry/src/main/resources/resfile') -Force).FullName
$share = (New-Item -ItemType Directory -Path (Join-Path $resfile 'share') -Force).FullName
Copy-Item -LiteralPath (Join-Path $installed 'share/caneda') -Destination $share -Recurse
Copy-Item -LiteralPath (Join-Path $repo 'tests/files/samples') -Destination (Join-Path $resfile 'share/caneda') -Recurse

Push-Location $stage
try {
    Invoke-BuildStep $hvigor @('assembleHap', '--mode', 'module', '-p', 'module=entry@default', '-p', 'buildMode=debug', '--no-daemon')
} finally {
    Pop-Location
}
$hap = Join-Path $stage 'entry/build/default/outputs/default/entry-default-unsigned.hap'
Get-FileHash -LiteralPath $hap -Algorithm SHA256
