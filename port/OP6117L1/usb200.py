"""Offline adaptation of Skyward's MTP rules to the pinned .200 stock gadget."""
from pathlib import Path
import pack


def once(blob, old, new):
    pack.check(blob.count(old) == 1, 'unexpected rule: ' + repr(old))
    return blob.replace(old, new)


def add_mtp(init, entries):
    pack.check(b'ffs.mtp' not in init and b'on property:sys.usb.config=adb\n    start adbd\n' in init and
               b'mkdir /config/usb_gadget/g1/functions/ffs.adb' in init, 'unexpected gadget rules')
    pack.check(not any(b'sys.usb.config_disable' in data for n, (_, data) in entries.items()
                       if n.endswith(('.rc', '.prop')) or n == 'prop.default'), 'review stock USB disable policy')
    # This stock init starts authenticated adbd without a config_disable property.
    mtp = Path('crates/skyward-pack/src/mtp.rc').read_bytes().replace(b'\r\n', b'\n')
    mtp = once(mtp, b'on property:sys.usb.config=mtp,adb && property:sys.usb.config_disable=0\n    start adbd',
               b'on property:sys.usb.config=mtp,adb && property:sys.usb.configfs=1\n    start adbd')
    # Take both functions off before acknowledging 'none'.
    footer = b'# The stock rules take the first function off; this takes the second.\non property:sys.usb.config=none && property:sys.usb.configfs=1\n    rm /config/usb_gadget/g1/configs/b.1/f2\n'
    mtp = once(mtp, footer, b'')
    f1 = b'    rm /config/usb_gadget/g1/configs/b.1/f1\n'
    init = once(init, f1 + b'    setprop sys.usb.state', f1 + f1.replace(b'/f1', b'/f2') + b'    setprop sys.usb.state')
    return init + b'\n' + mtp
