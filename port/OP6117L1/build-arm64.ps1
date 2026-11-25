$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '../..')
$env:RUSTUP_HOME = "$PWD/target/rustup"
$env:CARGO_HOME = "$PWD/target/cargo-home"
$env:RUSTUP_TOOLCHAIN = '1.100.0-x86_64-pc-windows-gnu'
$tc = "$env:LOCALAPPDATA/Android/Sdk/ndk/29.0.14206865/toolchains/llvm/prebuilt/windows-x86_64/bin"
$hostbin = "$env:RUSTUP_HOME/toolchains/$env:RUSTUP_TOOLCHAIN/lib/rustlib/x86_64-pc-windows-gnu/bin/self-contained"
$env:PATH = "$env:CARGO_HOME/bin;$PWD/target/mingw/bin;$hostbin;$tc;$env:PATH"
$env:CC_aarch64_linux_android = "$tc/clang.exe"
$env:CXX_aarch64_linux_android = "$tc/clang++.exe"
$env:CFLAGS_aarch64_linux_android = '--target=aarch64-linux-android30'
$env:CXXFLAGS_aarch64_linux_android = '--target=aarch64-linux-android30'
$env:AR_aarch64_linux_android = "$tc/llvm-ar.exe"
$env:CARGO_TARGET_AARCH64_LINUX_ANDROID_LINKER = "$tc/aarch64-linux-android30-clang.cmd"
$env:CARGO_BUILD_JOBS='6'
cargo build --locked --release --target aarch64-linux-android -p skyward
if ($LASTEXITCODE) { exit $LASTEXITCODE }
$env:RUSTFLAGS='-C target-feature=+crt-static'
cargo build --locked --release --target aarch64-linux-android -p skyward-system-init --target-dir target/system-init
exit $LASTEXITCODE
