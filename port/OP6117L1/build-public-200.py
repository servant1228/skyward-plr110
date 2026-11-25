"""Build the public .200 candidate from stock and locally compiled release programs, never a hostadb image."""
from pathlib import Path
import runpy
import tomllib

import pack
from usb200 import add_mtp

OUT = Path('out/public/skyward-OP6117L1-17.0.1.200-rc1.img')
ROOT = Path('target/public-200')
PHOENIX = b'''
# The stock UI acknowledges the default Phoenix timer with the next sequence.
on property:init.svc.recovery=running && property:vendor.oplus.phoenix.recovery.cmd=reboot_300_0
    setprop vendor.oplus.phoenix.recovery.cmd done_0_1
'''


def replace(entries, name, body):
    h = entries[name][0].copy()
    h[6] = len(body)
    entries[name] = h, body


def build():
    common = runpy.run_path(str(Path(__file__).with_name('build-17.0.1.200.py')))
    programs = tuple((ROOT / f'{folder}/aarch64-linux-android/release/{name}').read_bytes()
                     for folder, name in [('app', 'skyward'), ('init', 'system-init')])
    homes = {str(Path.home()).encode().lower(), Path.home().as_posix().encode().lower()}
    for program in programs:
        pack.check(not any(home in program.lower() for home in homes), 'builder home path in release binary; build with -Public')
    raw, entries = common['build'](executables=programs)
    stock = pack.unpack(raw)
    cfg, rc = 'skyward/device.toml', common['RC']
    config = entries[cfg][1].replace(b'\r\n', b'\n') + b'\n[firmware]\npartition = "modem"\n'
    settings = tomllib.loads(config.decode())
    pack.check(settings['manual_file_transfer'] and settings['wlan']['interface_wait_seconds'] == 45 and
               settings['firmware']['partition'] == settings['wlan']['firmware_partition'] == 'modem', 'wrong .200 config')
    replace(entries, cfg, config)
    init = entries[rc][1]
    pack.check(b'vendor.oplus.phoenix.recovery.cmd' not in init, 'unexpected Phoenix rules')
    replace(entries, rc, add_mtp(init + PHOENIX, entries))
    pack.check(all(entries[n] == stock[n] for n in ('adb_keys', 'system/bin/adbd', 'system/etc/recovery.fstab')) and
               entries['adb_keys'][0][1] >> 12 == 0o12 and entries['adb_keys'][1] == b'/product/etc/security/adb_keys',
               'factory ADB trust or fstab modified')
    pack.check('skyward/ese-diag' not in entries and 'skyward/port-diagnostics' not in entries and
               b'plr110-ese-diag' not in entries[rc][1], 'diagnostics enabled')
    return raw, entries


if __name__ == '__main__':
    pack.check(not OUT.exists() and not OUT.with_suffix('.img.sha256').exists(), 'refusing to overwrite RC1')
    pack.finish_image(*build(), OUT)
