"""Build the R4 hardware test from the pinned R3 image. No USB access."""
from pathlib import Path
import tomllib
import pack

base = pack.OUT.with_name('skyward-OP6117L1-17.0.0.101-diagnostic-hostadb-touch-r3-nxp.img')
out = base.with_name(base.name.replace('touch-r3-nxp', 'touch-r4-haptics-wlan'))
pack.check(not out.exists() and not out.with_suffix('.img.sha256').exists(), 'refusing to overwrite R4')
raw = base.read_bytes()
pack.check(pack.sha(raw) == '1c161412cd5275abfc06fe9677307546a2d568593db45070354a75720db617b7', 'wrong R3')
entries = pack.unpack(raw)
new = Path('target/aarch64-linux-android/release/skyward').read_bytes()
pack.elf(new, False)
cfg = Path('devices/OP6117L1.toml').read_bytes()
new_cfg = tomllib.loads(cfg.decode())
old_cfg = tomllib.loads(entries['skyward/device.toml'][1].decode())
pack.check(new_cfg.pop('haptics')['timed_led'] == '/sys/class/leds/vibrator', 'no LED backend')
pack.check(new_cfg.pop('wlan')['modules'] == ['rfkill', 'qca_cld3_wcn7750'] and new_cfg == old_cfg, 'unexpected device config')
for name, data in [('system/bin/recovery', new), ('skyward/device.toml', cfg)]:
    h, old = entries[name]
    pack.check(h[4] == 1 and old != data, 'expected replacement for ' + name)
    h = h.copy()
    h[6] = len(data)
    entries[name] = h, data
pack.finish_image(raw, entries, out)
print('recovery ELF SHA-256:', pack.sha(new))
