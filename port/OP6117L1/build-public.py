"""Prepare the public build from a hash-pinned R7, with factory ADB trust."""
import sys
from pathlib import Path
import pack

raw = Path(sys.argv[1]).read_bytes()
stock = pack.STOCK.read_bytes()
pack.check(pack.sha(raw) == '3c34bec8828e77c188cb36cea38e0e245743238934a1f3849e2dd42acbe067d9', 'wrong R7')
pack.check(pack.sha(stock) == pack.HASH, 'wrong factory image')
entries, factory = pack.unpack(raw), pack.unpack(stock)
key = entries['adb_keys'][1].split()[0]
pack.check(len(key) > 500 and factory['adb_keys'][1] == b'/product/etc/security/adb_keys', 'unexpected ADB keys')
entries['adb_keys'] = factory['adb_keys']
pack.check(not any(key in data for _, data in entries.values()), 'preauthorized host still present')
pack.check(entries['system/bin/adbd'] == factory['system/bin/adbd'], 'adbd differs from stock')
secure = [p for p in entries['prop.default'][1].splitlines() if p.startswith(b'ro.adb.secure=')]
pack.check(secure and all(p == b'ro.adb.secure=1' for p in secure), 'ADB authentication disabled')
out = Path('out/public/skyward-OP6117L1-r7.img')
pack.check(not out.exists() and not out.with_suffix('.img.sha256').exists(), 'refusing to overwrite release')
pack.finish_image(raw, entries, out)
