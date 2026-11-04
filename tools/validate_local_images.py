import sys,json,hashlib,subprocess,tempfile,os
from pathlib import Path
import argparse
parser=argparse.ArgumentParser(description='Compare stock and candidate firmware and run the stock ARM verifier.')
parser.add_argument('--stock',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
parser.add_argument('--qemu',type=Path,required=True)
args=parser.parse_args()
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from openplugin.az01 import extract
QEMU=args.qemu.resolve();STOCK=args.stock.resolve();OUT=args.output.resolve()
locks=json.loads((ROOT/'inputs.json').read_text())
def run(args,**kw):
 r=subprocess.run(list(map(str,args)),capture_output=True,text=True,**kw)
 if r.returncode:raise RuntimeError(f'{args}: {r.returncode}\n{r.stdout}\n{r.stderr}')
 return r.stdout+r.stderr
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
for device,v in locks.items():
 name=('Force' if device=='force' else 'MPC')+'-3.10.0'+('' if device=='force' else '-Gen1')+'-openplugin-v0.8.3-local-20261104-update.img'
 image=OUT/name; stock=STOCK/v['filename'];assert sha(stock)==v['sha256']
 report=json.loads(image.with_suffix('.json').read_text())
 assert sha(image)==report['output_sha256']
 with tempfile.TemporaryDirectory(prefix='validate-',dir=ROOT.parent) as td:
  td=Path(td); trees={}; infos={}
  for label,source in [('stock',stock),('candidate',image)]:
   info,data=extract(source.read_bytes());info.pop('compressed');infos[label]=info
   fs=td/(label+'.ext4');fs.write_bytes(data);del data
   log=run(['e2fsck','-fn',fs]);(OUT/(device+'-'+label+'-e2fsck.txt')).write_text(log)
   tree=td/label;tree.mkdir();run(['debugfs','-R',f'rdump / {tree}',fs]);trees[label]=tree
   fs.unlink()
  assert infos['stock']['boards']==infos['candidate']['boards']
  assert infos['stock']['devices']==infos['candidate']['devices']
  changed=[];checked=0
  for p in trees['stock'].rglob('*'):
   rel=p.relative_to(trees['stock']);dest=trees['candidate']/rel
   if p.is_symlink():
    assert dest.is_symlink() and os.readlink(p)==os.readlink(dest),rel
   elif p.is_file():
    assert dest.is_file(),rel
    if sha(p)!=sha(dest):changed.append(str(rel))
    checked+=1
  assert set(changed)<= {'etc/shadow'},changed
  verifier=next(trees['stock'].rglob('az01-image'))
  vendor=run([QEMU,'-L',trees['stock'],verifier,'--verify',image])
  (OUT/(device+'-vendor-verify.txt')).write_text(vendor)
  load=run([QEMU,'-L',trees['stock'],ROOT/'.deps/test-load-arm',ROOT/'build/native/plugin_manager.so'])
  native=run([QEMU,'-L',trees['stock'],ROOT/'.deps/test-native-arm'],cwd=td)
  snapshot=run([QEMU,'-L',trees['stock'],ROOT/'.deps/test-catalog-arm',ROOT/'website/catalog.json','200'],cwd=td)
  assert 'Native catalog: 200 entries, 188 validated downloads' in snapshot, snapshot
  report['validation']['arm_catalog_snapshot']='pass'
  print(snapshot,flush=True)
  report['validation'].update(vendor_verifier='pass',arm_plugin_load='pass',arm_native_tests='pass',stock_regular_files_compared=checked,stock_changed_files=changed,stock_symlinks='unchanged')
  report['container']=infos['candidate'];report['candidate_label']='Local 2026-11-04 catalog refresh; not the published v0.8.3 image'
  assert sha(stock)==v['sha256']
  image.with_suffix('.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
  print(device,checked,'stock files compared;',vendor,load,native,flush=True)
