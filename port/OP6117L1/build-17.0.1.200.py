"""Build R8 offline from the 17.0.1.200 recovery and the matching ODM touch HAL."""
from pathlib import Path
import struct
import tomllib

import pack

BASE = Path('target/stock/OP6117L1/17.0.1.200')
OUT = Path('out/skyward-OP6117L1-17.0.1.200-r8-candidate.img')
TOUCH = 'system/bin/hw/vendor-oplus-hardware-touch-V2-hbp5-service'
LIB = 'system/lib64/vendor.oplus.hardware.touch-V2-ndk.so'
RC = 'system/etc/init/hw/init.rc'
STAGE = b'''
# Stage the installed macan firmware before the OEM touch service starts.
on boot
    start plr110-touch-stage

service plr110-touch-stage /system/bin/sh /skyward/stage-touch.sh
    class core
    disabled
    oneshot
    user root
    group root
    seclabel u:r:recovery:s0
'''


def pinned(path, digest):
    data = path.read_bytes()
    pack.check(pack.sha(data) == digest, 'unexpected input: ' + str(path))
    return data


def build(executables=None):
    """Build the common stock-based tree. The R8 entry point pins its historical binaries."""
    raw = pinned(BASE/'recovery_b.img', '6bd5433e80bbbd4c86b0930242d6489710f003535d9257051d3977fb89325be4')
    pack.check(raw.startswith(b'ANDROID!') and len(raw) == 100 * 1024**2 and
               [struct.unpack_from('<I', raw, i)[0] for i in (8, 40, 1580)] == [0, 4, 0], 'not a standalone v4 recovery')
    stock = pack.unpack(raw)
    entries = stock.copy()
    ino = max(h[0] for h, _ in stock.values()) + 1

    def put(name, mode, data):
        nonlocal ino
        if name in stock:
            h = stock[name][0].copy()
            pack.check(h[4] == 1 and (h[1] >> 12) == (mode >> 12), 'unexpected entry: ' + name)
            h[1] = mode
        else:
            h = [ino,mode,0,0,2 if mode >> 12 == 4 else 1,0,0,0,0,0,0,0,0]
            ino += 1
        h[6], h[11] = len(data), len(name.encode()) + 1
        entries[name] = (h, data)

    if executables is None:
        app = pinned(Path('target/aarch64-linux-android/release/skyward'), '0b249ecf7f00151af1753e253292918cd6ca5ce561df5df0075bc5cf573d9d04')
        init = pinned(Path('target/system-init/aarch64-linux-android/release/system-init'), 'ee99a1dd7aea698a2dcf77b74d92d10dd2d254deb8047c4e39c22d179c87d09b')
    else:
        app, init = executables
    pack.elf(app, False)
    pack.elf(init, True)
    put('system/bin/recovery', stock['system/bin/recovery'][0][1], app)
    for tool in ('7za', 'avbctl', 'resetprop', 'unzip', 'zstd'):
        put('system/bin/' + tool, 0o120777, b'recovery')
    put('skyward', 0o040755, b'')
    put('skyward/system-init', 0o100755, init)
    cfg = Path('devices/OP6117L1.toml').read_bytes()
    device = tomllib.loads(cfg.decode())['device']
    pack.check((device['codename'], device['model'], device['use_market_name']) ==
               ('OP6117L1', 'OnePlus ACE 6T', False), 'wrong device settings')
    put('skyward/device.toml', 0o100644, cfg)
    for name in ('MiSansVF.ttf', 'KirkMono-Regular.ttf', 'KirkMono-OFL.txt'):
        put('skyward/' + name, 0o100644, (Path('resources/fonts')/name).read_bytes())
    put('system/etc/task_profiles.json', 0o100644, Path('crates/skyward-pack/src/task_profiles.json').read_bytes())

    for name, digest in ((TOUCH, 'daf6d42d894ec55387c1f0114b0d6dc8d99e96db684571520be9937b315b44f9'),
                         (LIB, '3bfcad17979bcaf8d08266f1d1c60f9680f0c3093fabfca709525919a52c097d')):
        data = pinned(BASE/'touch'/Path(name).name, digest)
        put(name, stock[name][0][1] if name in stock else 0o100755, data)
    put('skyward/firmware-extra', 0o040755, b'')
    put('skyward/firmware-extra/tp', 0o120777, b'/odm/firmware/tp')
    put('skyward/stage-touch.sh', 0o100644, Path(__file__).with_name('stage-touch.sh').read_bytes().replace(b'\r\n', b'\n'))
    put(RC, stock[RC][0][1], stock[RC][1] + STAGE)
    old = b'ro.build.version.release=16\n'
    props = stock['prop.default'][1]
    pack.check(props.count(old) == 1, 'unexpected build properties')
    put('prop.default', stock['prop.default'][0][1], props.replace(old, b''))
    pack.check(b'/system/bin/bootstrap/linker64\0' in stock['system/bin/fsck.f2fs'][1], 'unexpected checker')
    put('system/bin/bootstrap', 0o040755, b'')
    put('system/bin/bootstrap/linker64', 0o120777, b'../linker64')

    changed = {name for name in stock if entries[name] != stock[name]}
    pack.check(changed == {'prop.default', RC, LIB, 'system/bin/recovery', 'system/bin/unzip'}, 'unexpected stock changes')
    pack.check(entries['adb_keys'][1] == b'/product/etc/security/adb_keys' and
               {v for v in entries['prop.default'][1].splitlines() if v.startswith(b'ro.adb.secure=')} == {b'ro.adb.secure=1'}, 'ADB trust changed')
    return raw, entries


if __name__ == '__main__':
    pack.check(not OUT.exists() and not OUT.with_suffix('.img.sha256').exists(), 'candidate already exists')
    pack.finish_image(*build(), OUT)
