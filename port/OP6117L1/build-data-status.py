"""Build R6 offline: keep the tested R5 ramdisk apart from the recovery ELF."""
from pathlib import Path
import pack

base = pack.OUT.with_name('skyward-OP6117L1-17.0.0.101-diagnostic-hostadb-touch-r5-fsck-loader.img')
out = base.with_name(base.name.replace('r5-fsck-loader', 'r6-data-status'))
pack.check(not out.exists() and not out.with_suffix('.img.sha256').exists(), 'refusing to overwrite R6')
raw = base.read_bytes()
pack.check(pack.sha(raw) == '91b6a2d4ff609610a9547e4a99310ee7f08e925eac24d1957ef2f0629ccb4a12', 'wrong R5')
entries = pack.unpack(raw)
name = 'system/bin/recovery'
h, old = entries[name]
new = Path('target/aarch64-linux-android/release/skyward').read_bytes()
pack.elf(new, False)
pack.check(pack.sha(old) == 'fb37b88d84d3e801eb4fe4634be2836cf64001649d7ca858f0e65b011df74940', 'wrong base ELF')
pack.check(h[4] == 1 and b'data is mounted; owner storage confirmed=' in new and b'writable mount not attempted' in new, 'wrong release ELF')
h = h.copy()
h[6] = len(new)
entries[name] = h, new
pack.finish_image(raw, entries, out)
print('recovery ELF SHA-256:', pack.sha(new))
