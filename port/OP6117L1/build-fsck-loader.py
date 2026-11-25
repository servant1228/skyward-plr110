"""Build the PLR110 R5 from the verified R4; no device access."""
from pathlib import Path
from io import BytesIO
import pack
from elftools.elf.elffile import ELFFile

base = pack.OUT.with_name('skyward-OP6117L1-17.0.0.101-diagnostic-hostadb-touch-r4-haptics-wlan.img')
out = base.with_name(base.name.replace('touch-r4-haptics-wlan', 'touch-r5-fsck-loader'))
pack.check(not out.exists() and not out.with_suffix('.img.sha256').exists(), 'refusing to overwrite R5')
raw = base.read_bytes()
pack.check(pack.sha(raw) == '3e5f8c75882a4d753627574a86055de20a77e1190850979e9eeb29ee3d75e447', 'wrong R4')
entries = pack.unpack(raw)
checker = entries['system/bin/fsck.f2fs'][1]
interp = [p.get_interp_name() for p in ELFFile(BytesIO(checker)).iter_segments() if p.header.p_type == 'PT_INTERP']
parent = 'system/bin/bootstrap'
loader = parent + '/linker64'
pack.check(interp == ['/' + loader], 'unexpected fsck interpreter')
pack.check(pack.sha(entries['system/bin/linker64'][1]) == 'de6136e56e6afc1f82a17aaf438e2f4421fba117e2416d2e065687c20c9673e4', 'wrong tested linker')
ino = max(h[0] for h, _ in entries.values()) + 1
for name, mode, nlink, data in [(parent, 0o040755, 2, b''), (loader, 0o120777, 1, b'../linker64')]:
    pack.check(name not in entries, 'unexpected existing ' + name)
    entries[name] = [ino, mode, 0, 0, nlink, 0, len(data), 0, 0, 0, 0, len(name.encode())+1, 0], data
    ino += 1

# The only existing file replaced: recovery refuses a writable mount if
# the check fails. Keep the checker, libraries and vendor fstab intact.
recovery = 'system/bin/recovery'
h, old = entries[recovery]
new = Path('target/aarch64-linux-android/release/skyward').read_bytes()
pack.elf(new, False)
pack.check(h[4] == 1 and new != old and b'writable mount not attempted' in new, 'missing pre-mount guard')
h = h.copy()
h[6] = len(new)
entries[recovery] = h, new
pack.finish_image(raw, entries, out)
print('recovery ELF SHA-256:', pack.sha(new))
