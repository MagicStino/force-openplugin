#!/usr/bin/env python3
"""Package the native manager and skin together without a firmware image."""
import argparse,gzip,hashlib,io,json,subprocess,tarfile,zipfile,stat,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native',type=Path,default=ROOT/'build/manager-preview');p.add_argument('--output',type=Path,default=ROOT/'dist/manager');p.add_argument('--version',default='0.9.0');p.add_argument('--instructions',type=Path,default=ROOT/'docs/MANAGER-UPDATE.md');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 source=a.output/'OpenPlugin-Manager-source.tar.gz';data=io.BytesIO()
 with tarfile.open(fileobj=data,mode='w') as archive:
  for name in ['native','tools','runtime','assets','tests','docs','dependencies.json','requirements-build.txt','README.md','LICENSE']:
   path=ROOT/name
   files=sorted(path.rglob('*')) if path.is_dir() else [path]
   for f in files:
    if not f.is_file() or '__pycache__' in f.parts:continue
    raw=f.read_bytes();info=tarfile.TarInfo('force-openplugin/'+str(f.relative_to(ROOT)));info.size=len(raw);info.mode=0o644;info.mtime=0;archive.addfile(info,io.BytesIO(raw))
  for name in ['mpc-vst-plugins','mpc-vst-manager']:
   raw=subprocess.check_output(['git','-C',str(ROOT/'.deps'/name),'archive','HEAD'])
   with tarfile.open(fileobj=io.BytesIO(raw)) as upstream:
    for member in upstream:
     if not member.isfile():continue
     content=upstream.extractfile(member).read();member.name=name+'/'+member.name;member.mtime=0;archive.addfile(member,io.BytesIO(content))
 with source.open('wb') as file:
  with gzip.GzipFile(fileobj=file,mode='wb',filename='',mtime=0) as stream:stream.write(data.getvalue())
 native=a.native.resolve();skin=native/'payload/usr/share/Akai/Content/Synths/OPENPLUGIN - VST - OpenPlugin Manager'
 subprocess.run(['python3',str(ROOT/'.deps/mpc-vst-plugins/tools/release.py'),'--so',str(native/'plugin_manager.so'),'--skin',str(skin),'--entry',str(native/'source/vst/build/pluginlist-entry.xml'),'--version',a.version,'--id','openplugin-manager','--repo','MagicStino/force-openplugin','--license','MIT','--about','Standalone experimental manager update. No firmware image; verify on hardware before release.','--extra',str(source)+':source/OpenPlugin-Manager-source.tar.gz','--extra',str(native/'payload/usr/share/openplugin')+':notices','-o',str(a.output)],check=True)
 zpath=a.output/f'OpenPlugin-Manager-{a.version}-mpc-armv7.zip'
 with zipfile.ZipFile(zpath) as z:files={i.filename:(z.read(i),i.external_attr) for i in z.infolist()}
 top=f'OpenPlugin-Manager-{a.version}/'
 for name,(raw,mode) in list(files.items()):
  if name.endswith('/plugin-meta.xml'):
   files[name]=(raw.replace(b'name="OpenPlugin Manager"',b'name=" OpenPlugin Manager"').replace(b'descriptiveName="OpenPlugin Manager"',b'descriptiveName=" OpenPlugin Manager"'),mode)
 files[top+'INSTALL.md']=(a.instructions.read_bytes(),(stat.S_IFREG|0o644)<<16)
 version=top+'portable/OPENPLUGIN - VST - OpenPlugin Manager/version.xml'
 files[version]=(re.sub(rb'<version>[^<]+</version>',b'<version>'+a.version.split('-')[0].encode()+b'.0</version>',files[version][0]),files[version][1])
 files[top+'SHA256SUMS']=(''.join(hashlib.sha256(raw).hexdigest()+'  '+name[len(top):]+'\n' for name,(raw,_) in sorted(files.items()) if name!=top+'SHA256SUMS').encode(),(stat.S_IFREG|0o644)<<16)
 with zipfile.ZipFile(zpath,'w') as z:
  for name,(raw,mode) in sorted(files.items()):
   info=zipfile.ZipInfo(name,date_time=(2026,1,1,0,0,0));info.create_system=3;info.external_attr=mode;info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,raw)
 digest=hashlib.sha256(zpath.read_bytes()).hexdigest();zpath.with_suffix('.zip.sha256').write_text(digest+'  '+zpath.name+'\n');print(zpath,digest)
if __name__=='__main__':main()
