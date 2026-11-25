"""Offline, Windows-compatible packer for one hash-pinned PLR110 recovery. No USB I/O."""
from pathlib import Path
import hashlib, os, struct, subprocess, sys, tomllib, tempfile
ROOT=Path(__file__).resolve().parents[2]
os.chdir(ROOT)
sys.path.insert(0,str(ROOT/'target/inspect-python'))
import lz4.block
STOCK=Path('target/stock/OP6117L1/recovery_a.img')
HASH='0c32878ec6b628177af5bfcb893fc389b521b7c6ddcec956f9d85d4535f34fe9'
OUT=Path('out/skyward-OP6117L1-17.0.0.101-experimental.img')
BLOCK=8*1024*1024
MAGIC=bytes.fromhex('02214c18')
sha=lambda x:hashlib.sha256(x).hexdigest()
def check(cond,msg):
    if not cond: raise ValueError(msg)
def unpack(b):
    n=struct.unpack_from('<I',b,12)[0]; r=b[4096:4096+n];check(r[:4]==MAGIC,'not LZ4 legacy');o=bytearray();i=4
    while i<len(r):
        z=struct.unpack_from('<I',r,i)[0];i+=4;check(z>0 and i+z<=len(r),'invalid block');o.extend(lz4.block.decompress(r[i:i+z],uncompressed_size=BLOCK));i+=z
    entries={};i=0
    while i+110<=len(o):
        check(o[i:i+6]==b'070701','not newc');h=[int(o[i+j:i+j+8],16) for j in range(6,110,8)];name=o[i+110:i+109+h[11]].decode();st=(i+110+h[11]+3)&~3;i=(st+h[6]+3)&~3
        if name=='TRAILER!!!':
            check(not any(o[i:]),'more than one archive');return entries
        check(name not in entries,'duplicate '+name);entries[name]=(h,bytes(o[st:st+h[6]]))
    raise ValueError('missing trailer')
def record(name,h,data):
    nb=name.encode()+b'\0';h=h.copy();h[6]=len(data);h[11]=len(nb);head=b'070701'+b''.join(('%08x'%v).encode() for v in h)+nb
    return head+b'\0'*(-len(head)%4)+data+b'\0'*(-len(data)%4)
def elf(data,static):
    check(data[:6]==b'\x7fELF\x02\x01' and struct.unpack_from('<H',data,18)[0]==183,'not ARM64 ELF');off=struct.unpack_from('<Q',data,32)[0];sz,n=struct.unpack_from('<HH',data,54);ph=[struct.unpack_from('<I',data,off+j*sz)[0] for j in range(n)];check((3 not in ph)==static,'unexpected ELF interpreter')
def main():
    global OUT
    panel_fix = sys.argv[1:] == ['--hostadb-panel-fix']
    diagnostic = panel_fix or sys.argv[1:] == ['--diagnostic']
    check(diagnostic or len(sys.argv) == 1, 'expected --diagnostic or no arguments')
    if diagnostic:
        OUT = OUT.with_name(OUT.name.replace('experimental', 'diagnostic'))
    if panel_fix:
        host_image = OUT.with_name(OUT.stem + '-hostadb.img').read_bytes()
        check(sha(host_image) == '765d0901fa911d571fdeab9081170044f5ac3e1bdd31971573df4517315e222b', 'unexpected trusted diagnostic base')
        host_entries = unpack(host_image)
        OUT = OUT.with_name(OUT.stem + '-hostadb-panel-fix.img')
    original=STOCK.read_bytes();check(sha(original)==HASH and len(original)==104857600,'stock build mismatch');check(original[:8]==b'ANDROID!' and struct.unpack_from('<I',original,40)[0]==4 and struct.unpack_from('<I',original,8)[0]==struct.unpack_from('<I',original,1580)[0]==0,'unexpected boot header');e=unpack(original);old=e.copy();inode=max(h[0] for h,_ in e.values())+1
    def put(name,mode,data):
        nonlocal inode
        if name in e:
            h=e[name][0].copy();check(h[4]==1,'hardlink to edited file '+name);h[1]=mode
        else: h=[inode,mode,0,0,2 if mode>>12==4 else 1,0,0,0,0,0,0,0,0];inode+=1
        h[6]=len(data);h[11]=len(name.encode())+1;e[name]=(h,data)
    service=Path('target/aarch64-linux-android/release/skyward').read_bytes();si=Path('target/system-init/aarch64-linux-android/release/system-init').read_bytes();elf(service,False);elf(si,True)
    cfg=Path('devices/OP6117L1.toml');check(tomllib.loads(cfg.read_text('utf8'))['device']['codename']=='OP6117L1','wrong config')
    check('skyward' not in e and 'twres' not in e and 'FFiles' not in e,'unexpected base');put('skyward',0o040755,b'');put('system/bin/recovery',old['system/bin/recovery'][0][1],service)
    for cmd in ('7za','avbctl','resetprop','unzip','zstd'): put('system/bin/'+cmd,0o120777,b'recovery')
    if diagnostic:
        put('skyward/port-diagnostics', 0o100600, b'1')
    put('skyward/system-init',0o100755,si);put('skyward/device.toml',0o100644,cfg.read_bytes());
    for f in ('MiSansVF.ttf','KirkMono-Regular.ttf','KirkMono-OFL.txt'):put('skyward/'+f,0o100644,(Path('resources/fonts')/f).read_bytes())
    if 'system/etc/task_profiles.json' not in e: put('system/etc/task_profiles.json',0o100644,Path('crates/skyward-pack/src/task_profiles.json').read_bytes())
    # Keep OEM USB rules, stock debugging/OTA policy, SELinux, touch and vendor services.
    # No unauthenticated root ADB, added USB services or automatic downgrade permissions.
    check(all(old[k]==e[k] for k in ['prop.default','system/bin/adbd','system/etc/init/hw/init.rc','etc/recovery.fstab']),'stock policy changed')
    if panel_fix:
        e['adb_keys'] = host_entries['adb_keys']
        check(e.keys() == host_entries.keys() and all(e[k] == host_entries[k] for k in e if k != 'system/bin/recovery'), 'unexpected change to trusted diagnostic base')
    finish_image(original, e, OUT)

def finish_image(original, e, out):
    tr=[0]*13;tr[4]=1;raw=b''.join(record(k,h,d) for k,(h,d) in e.items())+record('TRAILER!!!',tr,b'');rd=bytearray(MAGIC)
    for i in range(0,len(raw),BLOCK):
        v=lz4.block.compress(raw[i:i+BLOCK],store_size=False);rd.extend(struct.pack('<I',len(v)));rd.extend(v)
    header=bytearray(original[:4096]);struct.pack_into('<I',header,12,len(rd));new=bytes(header+rd)+b'\0'*(-len(rd)%4096);check(unpack(new)==e,'archive round-trip failed')
    out.parent.mkdir(exist_ok=True);prog=[sys.executable,'target/avbtool.py'];
    with tempfile.TemporaryDirectory(dir=out.parent) as tmp:
        p=Path(tmp)/'recovery.img';p.write_bytes(new);subprocess.run(prog+['add_hash_footer','--image',str(p),'--partition_name','recovery','--partition_size',str(len(original)),'--algorithm','NONE','--salt',sha(new)],check=True);subprocess.run(prog+['verify_image','--image',str(p)],check=True);final=p.read_bytes();check(len(final)==len(original) and unpack(final)==e,'image verification failed');p.replace(out)
    out.with_suffix('.img.sha256').write_text(sha(final)+'  '+out.name+'\n',encoding='ascii');print(out,len(final),sha(final))
if __name__=='__main__': main()
