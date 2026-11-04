#!/usr/bin/env python3
"""Derive Tracks16 from the pinned Open MPC release; preserve every other rootfs byte."""
import argparse,json,struct,subprocess,tempfile,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from openplugin.az01 import extract,pack
from openplugin.track_limits import CONFIG,patch_app,sha,locate_sites

def run(args):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True)
 if p.returncode:raise RuntimeError(p.stdout+p.stderr)
 return p.stdout+p.stderr

def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--device',choices=CONFIG,required=True);p.add_argument('--base',type=Path,required=True)
 p.add_argument('--stock-root',type=Path,required=True);p.add_argument('--qemu',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();cfg=CONFIG[a.device];out=a.output.resolve()
 if out.exists() or out==a.base.resolve():p.error('Output must be a new path')
 base=a.base.read_bytes()
 if sha(base)!=cfg['base_sha256']:p.error('Base image does not match the validated release')
 info,fs=extract(base);del base;out.parent.mkdir(parents=True,exist_ok=True)
 with tempfile.TemporaryDirectory(prefix='tracks16-',dir=out.parent) as t:
  t=Path(t);fp=t/'root.ext4';fp.write_bytes(fs);dump=t/'MPC'
  run(['debugfs','-R',f'dump /usr/bin/MPC "{dump}"',fp]);original=dump.read_bytes();patched=patch_app(original,a.device);sites=locate_sites(original)
  blocksize=1024<<struct.unpack_from('<I',fs,1048)[0];changed=bytearray(fs);mapping=[]
  for name in ['plugin','audio']:
   off=sites[name];logical,within=divmod(off,blocksize)
   result=run(['debugfs','-R',f'bmap /usr/bin/MPC {logical}',fp])
   physical=int(next(x.strip() for x in result.splitlines() if x.strip().isdigit()));pos=physical*blocksize+within
   if changed[pos:pos+4]!=original[off:off+4]:raise ValueError('Filesystem mapping mismatch')
   changed[pos:pos+4]=patched[off:off+4]
   mapping.append({'kind':name,'file_offset':hex(off),'filesystem_offset':hex(pos),'before':original[off:off+4].hex(),'after':patched[off:off+4].hex()})
  if sum(x!=y for x,y in zip(fs,changed))!=2:raise ValueError('Unexpected filesystem changes')
  fp.write_bytes(changed);dump.unlink();run(['debugfs','-R',f'dump /usr/bin/MPC "{dump}"',fp])
  if dump.read_bytes()!=patched:raise ValueError('Patched application dump mismatch')
  check=run(['e2fsck','-f','-n',fp]);out.with_suffix('.e2fsck.txt').write_text(check)
  print('Exact two-byte patch verified; filesystem clean',flush=True)
  final=pack(info,bytes(changed),'3.10.0-openplugin-v0.8.3-tracks16');verified,roundtrip=extract(final)
  if roundtrip!=changed or verified['boards']!=info['boards'] or verified['devices']!=info['devices']:raise ValueError('Container round-trip mismatch')
  candidate=t/'candidate.img';candidate.write_bytes(final)
  verifier=next(a.stock_root.rglob('az01-image'));result=run([a.qemu.resolve(),'-L',a.stock_root.resolve(),verifier.resolve(),'--verify',candidate])
  if 'verify: success' not in result:raise ValueError('Vendor verification failed')
  out.with_suffix('.verify.txt').write_text(result)
  if sha(a.base.read_bytes())!=cfg['base_sha256']:raise ValueError('Base changed during build')
  with out.open('xb') as f:f.write(final)
  report={'device':a.device,'audio_track_limit':16,'plugin_track_limit':16,'base_image':a.base.name,'base_sha256':cfg['base_sha256'],'output_sha256':sha(final),'output_size':len(final),'original_app_sha256':cfg['app_sha256'],'app_sha256':cfg['patched_sha256'],'patches':mapping,'validation':{'rootfs_changed_bytes':2,'all_other_rootfs_bytes':'identical to validated Open MPC base, including metadata, boot files and plugins','filesystem':'pass','az01_container':'pass','extract_roundtrip':'pass','vendor_verifier':'pass','hardware':'not performed by builder'},'limitations':['Track limits are not a performance guarantee.','Recording and projects above eight tracks need device testing.','Projects exceeding eight tracks may not load on unmodified firmware.']}
  out.with_suffix('.json').write_text(json.dumps(report,indent=2)+'\n');out.with_suffix('.sha256').write_text(sha(final)+'  '+out.name+'\n');print(json.dumps(report),flush=True)
if __name__=='__main__':main()
