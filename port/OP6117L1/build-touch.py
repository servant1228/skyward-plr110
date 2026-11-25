"""Make the touch/bring-up test from the verified PLR110 panel image (offline)."""
from pathlib import Path
import pack

base = pack.OUT.with_name('skyward-OP6117L1-17.0.0.101-diagnostic-hostadb-panel-fix.img')
raw = base.read_bytes()
pack.check(pack.sha(raw) == '45324b70fe76c424f79dc86f82fa3ca99f6c05e0137c53e6994dde0275397ad7', 'wrong panel image')
entries = pack.unpack(raw)
ino = max(h[0] for h, _ in entries.values()) + 1

def put(path, mode, data):
    global ino
    if path in entries:
        h = entries[path][0].copy()
        pack.check(h[4] == 1 and h[1] == mode, 'unexpected existing entry: ' + path)
    else:
        h = [ino,mode,0,0,2 if mode >> 12 == 4 else 1,0,0,0,0,0,0,0,0]; ino += 1
    h[6], h[11] = len(data), len(path.encode())+1
    entries[path] = h,data

for path, digest, mode in [
    ('system/bin/hw/vendor-oplus-hardware-touch-V2-hbp5-service', 'ddc3be1cf0c77975d9769f764e57cc3739c262371dc99451e1b032224a670071', 0o100755),
    ('system/lib64/vendor.oplus.hardware.touch-V2-ndk.so', '3bfcad17979bcaf8d08266f1d1c60f9680f0c3093fabfca709525919a52c097d', None),
]:
    blob = (Path('target/stock/OP6117L1/touch')/Path(path).name).read_bytes()
    pack.check(pack.sha(blob)==digest, 'installed ODM file mismatch: '+path)
    put(path, mode or entries[path][0][1], blob)

# Remove only the stale, write-once release from the recovery defaults. The
# existing adopt_installed_version() sets the actual value from mounted system.
prop = 'prop.default'; h,data = entries[prop]
old = b'ro.build.version.release=16\n'
pack.check(data.splitlines().count(old.rstrip())==1 and old in data, 'unexpected release property')
put(prop, h[1], data.replace(old,b''))
rc='system/etc/init/hw/init.rc'; h,data = entries[rc]
put(rc, h[1], data + b'''\n# Local diagnostic: use the installed macan firmware with the OEM touch HAL.
on boot
    start plr110-touch-stage

service plr110-touch-stage /system/bin/sh /skyward/stage-touch.sh
    class core
    disabled
    oneshot
    user root
    group root
    seclabel u:r:recovery:s0
''')
put('skyward/firmware-extra', 0o040755, b'')
put('skyward/firmware-extra/tp', 0o120777, b'/odm/firmware/tp')
put('skyward/stage-touch.sh', 0o100644, Path(__file__).with_name('stage-touch.sh').read_bytes().replace(b'\r\n',b'\n'))
pack.finish_image(raw, entries, base.with_name(base.name.replace('panel-fix','touch-r1')))
