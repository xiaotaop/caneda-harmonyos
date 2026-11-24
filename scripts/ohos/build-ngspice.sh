#!/bin/sh
set -eu

usage() {
    printf 'Usage: %s NATIVE_SDK {arm64-v8a|x86_64} {cli|shared} NGSPICE_47_TAR_GZ NEW_OUTPUT_DIR\n' "$0" >&2
    exit 2
}

[ "$#" -eq 5 ] || usage
[ -d "$1" ] || usage
sdk_dir=$(cd "$1" && pwd -P)
abi=$2
mode=$3
case "$abi" in
    arm64-v8a) arch=aarch64; machine=AArch64 ;;
    x86_64) arch=x86_64; machine='Advanced Micro Devices X86-64' ;;
    *) usage ;;
esac
case "$mode" in
    cli) ngshared_flag=--without-ngshared ;;
    shared) ngshared_flag=--with-ngshared ;;
    *) usage ;;
esac
[ -f "$4" ] || usage
archive="$(cd "$(dirname "$4")" && pwd -P)/$(basename "$4")"
output=$5
script_dir=$(CDPATH='' cd "$(dirname "$0")" && pwd -P)
jobs=${JOBS:-4}
case "$jobs" in ''|0|*[!0-9]*) usage ;; esac

sdk_bin="$sdk_dir/llvm/bin"
target="$arch-unknown-linux-ohos"
CC="$sdk_bin/$target-clang"
CXX="$sdk_bin/$target-clang++"
LD="$sdk_bin/ld.lld"
AR="$sdk_bin/llvm-ar"
RANLIB="$sdk_bin/llvm-ranlib"
NM="$sdk_bin/llvm-nm"
STRIP="$sdk_bin/llvm-strip"
readelf="$sdk_bin/llvm-readelf"
export CC CXX LD AR RANLIB NM STRIP
for tool in "$CC" "$CXX" "$LD" "$AR" "$RANLIB" "$NM" "$STRIP" "$readelf"; do
    if [ ! -x "$tool" ]; then
        printf 'Missing SDK tool: %s\n' "$tool" >&2
        exit 1
    fi
done
checksum=894e649651f1838a14095e5a5439e7d3aa63e87ede14d283173fda4fcdef675f
if command -v sha256sum >/dev/null 2>&1; then
    hash_output=$(sha256sum < "$archive")
else
    hash_output=$(shasum -a 256 < "$archive")
fi
if [ "${hash_output%% *}" != "$checksum" ]; then
    printf 'ngspice 47 archive SHA-256 mismatch\n' >&2
    exit 1
fi

# Fail if the output already exists so old binaries cannot be mistaken for this run.
mkdir "$output"
output=$(cd "$output" && pwd -P)
tar -xzf "$archive" -C "$output"
source="$output/ngspice-47"
patch -d "$source" -p1 < "$script_dir/patches/ngspice-47-no-xspice.patch"
patch -d "$source" -p1 < "$script_dir/patches/ngspice-47-ohos-tempfile.patch"
mkdir "$output/build"
cd "$output/build"

# config.sub from this release rejects linux-ohos. The SDK wrappers above select
# the real OHOS target and sysroot. The host alias is for configure/libtool.
if ! "$source/configure" --build="$("$source/config.guess")" --host="$arch-unknown-linux-gnu" \
    --prefix=/usr --without-x --disable-xspice --disable-osdi --disable-openmp \
    --with-fftw3=no --with-readline=no "$ngshared_flag" > "$output/configure.log" 2>&1; then
    tail -30 "$output/configure.log" >&2
    exit 1
fi
if [ "$mode" = shared ]; then
    # Match the SONAME to the filename that is packaged in the HAP.
    set -- 'libngspice_la_LDFLAGS=-shared -lstdc++ -avoid-version'
else
    set --
fi
if ! make -j"$jobs" "$@" > "$output/build.log" 2>&1; then
    tail -30 "$output/build.log" >&2
    exit 1
fi

if [ "$mode" = cli ]; then
    artifact=src/ngspice
    name=ngspice
else
    artifact=src/.libs/libngspice.so
    name=libngspice.so
fi
export LC_ALL=C
"$readelf" -h -l -d "$artifact" > "$output/elf.txt"
if ! grep -F "$machine" "$output/elf.txt" | grep -q 'Machine:'; then
    printf 'ELF machine mismatch for %s\n' "$abi" >&2
    exit 1
fi
if [ "$mode" = cli ]; then
    grep -F "interpreter: /lib/ld-musl-$arch.so.1]" "$output/elf.txt" >/dev/null
else
    grep -F "Library soname: [libngspice.so]" "$output/elf.txt" >/dev/null
    "$readelf" --dyn-syms --wide "$artifact" > "$output/exports.txt"
    for symbol in ngSpice_Init ngSpice_Circ ngSpice_Command ngSpice_CurPlot ngGet_Vec_Info ngSpice_Reset; do
        if ! grep -E "[[:space:]]$symbol$" "$output/exports.txt" | grep -vq '[[:space:]]UND[[:space:]]'; then
            printf 'Missing libngspice export: %s\n' "$symbol" >&2
            exit 1
        fi
    done
fi

# A staging directory for the HAP integrator. The toolchain's C++ runtime
# is resolved when assembling the HAP alongside Qt.
mkdir -p "$output/stage/share/ngspice/scripts"
cp "$artifact" "$output/stage/$name"
cp src/spinit "$output/stage/share/ngspice/scripts/spinit"
cp "$source/COPYING" "$output/stage/NGSPICE-COPYING"
if [ "$mode" = shared ]; then
    cp "$source/src/include/ngspice/sharedspice.h" "$output/stage/"
fi
printf 'ngspice 47 %s %s\nStaged in %s\nELF metadata in %s\n' "$abi" "$mode" "$output/stage" "$output/elf.txt"
