"""Build the R7 UI labels (model and OS version) offline from the verified R6 image."""
from pathlib import Path
import tomllib
import pack

base = pack.OUT.with_name('skyward-OP6117L1-17.0.0.101-diagnostic-hostadb-touch-r6-data-status.img')
out = base.with_name(base.name.replace('r6-data-status', 'r7-display-labels'))
pack.check(not out.exists() and not out.with_suffix('.img.sha256').exists(), 'refusing to overwrite existing output')
raw = base.read_bytes()
pack.check(pack.sha(raw) == '4db6f412b2023bccf1253846c3b118dfd06692b0a6ba6e5a04deb73e9821f8f9', 'wrong R6')
entries = pack.unpack(raw)
cfg_name = 'skyward/device.toml'
cfg = Path('devices/OP6117L1.toml').read_bytes()
expected = tomllib.loads(entries[cfg_name][1].decode())
expected['device'].update(model='OnePlus ACE 6T', use_market_name=False)
pack.check(tomllib.loads(cfg.decode()) == expected, 'unexpected device configuration change')
elf_name = 'system/bin/recovery'
elf = Path('target/aarch64-linux-android/release/skyward').read_bytes()
pack.elf(elf, False)
pack.check(pack.sha(entries[elf_name][1]) == '0a8587d8e5f94abbac47a127d28025f5cd31176cf72febb4cdf3ed76ad2d62b0', 'wrong base ELF')
for name, data in [(cfg_name, cfg), (elf_name, elf)]:
    header, old = entries[name]
    pack.check(header[4] == 1 and old != data, 'expected replacement for ' + name)
    header = header.copy()
    header[6] = len(data)
    entries[name] = header, data
pack.finish_image(raw, entries, out)
