"""Replace only Skyward in the hash-pinned, touch-tested PLR110 image (no USB operations)."""
from pathlib import Path
import argparse
import pack

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('variant', choices=('initrc', 'nxp'), nargs='?', default='initrc')
variant = parser.parse_args().variant
before, after, expected = {
    'initrc': ('touch-r1', 'touch-r2-initrc', '8be09cb1d87e25eac69ca386d90d9e46d0185bce9ea6978ca508fc128f6ac4b5'),
    'nxp': ('touch-r2-initrc', 'touch-r3-nxp', '7b4543e650a8ef631b78c242b083c8394fe69d639ed185e7713c6d15f70c2991'),
}[variant]
base = pack.OUT.with_name(f'skyward-OP6117L1-17.0.0.101-diagnostic-hostadb-{before}.img')
raw = base.read_bytes()
pack.check(pack.sha(raw) == expected, f'{before} image mismatch')
entries = pack.unpack(raw)
name = 'system/bin/recovery'
header, old = entries[name]
new = Path('target/aarch64-linux-android/release/skyward').read_bytes()
pack.elf(new, False)
pack.check(header[4] == 1 and new != old, 'expected a rebuilt ARM64 recovery')
header = header.copy()
header[6] = len(new)
entries[name] = header, new
out = base.with_name(base.name.replace(before, after))
pack.check(not out.exists(), f'refusing to overwrite existing {out}')
pack.finish_image(raw, entries, out)
