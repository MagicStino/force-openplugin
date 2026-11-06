"""Test a built standalone manager ZIP without touching device services/settings."""
import hashlib,json,os,subprocess,tempfile,unittest,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class ManagerPackage(unittest.TestCase):
 def test_upgrade_preserves_single_uid_and_boot_sync(self):
  archive=Path(os.environ.get('OPENPLUGIN_MANAGER_PACKAGE',str(ROOT/'dist/manager/Plugin-Manager-0.7.1-rc1-mpc-armv7.zip')))
  if not archive.exists():self.skipTest('Build/package the standalone manager first')
  with tempfile.TemporaryDirectory() as tmp:
   tmp=Path(tmp)
   with zipfile.ZipFile(archive) as z:
    assert all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist());z.extractall(tmp/'unpacked')
   package=next((tmp/'unpacked').iterdir());manifest=json.loads((package/'mpc-plugin.json').read_text());uid=manifest['uid'];self.assertEqual(manifest['id'],'openplugin-manager')
   for row in (package/'SHA256SUMS').read_text().splitlines():
    sha,name=row.split('  ',1);self.assertEqual(hashlib.sha256((package/name).read_bytes()).hexdigest(),sha)
   self.assertEqual(manifest['name'],'OpenPlugin Manager');skin=manifest['skin'];self.assertEqual(skin,'OPENPLUGIN - VST - OpenPlugin Manager');builtin=tmp/'builtin'/'poloq - VST - Plugin Manager';builtin.mkdir(parents=True);(builtin/'plugin_manager.so').write_bytes(b'original firmware fixture')
   meta=(package/'portable'/skin/'plugin-meta.xml').read_text();self.assertIn('name=" OpenPlugin Manager"',meta);old=meta.replace('%payload-path%/'+skin,str(builtin)).replace('name="OpenPlugin Manager"','name="Plugin Manager"').replace('manufacturer="OPENPLUGIN"','manufacturer="poloq"');(builtin/'plugin-meta.xml').write_text(meta.replace(skin,builtin.name).replace('name="OpenPlugin Manager"','name="Plugin Manager"').replace('manufacturer="OPENPLUGIN"','manufacturer="poloq"'))
   settings=tmp/'MPC.settings';settings.write_text('<PROPERTIES>\n<VALUE name="pluginList-arm"><KNOWNPLUGINS>\n'+old+'\n</KNOWNPLUGINS></VALUE>\n</PROPERTIES>\n')
   target=tmp/'Synths';log=tmp/'service-log';env=dict(os.environ,MPC_INSTALL_TEST='1',MPC_SETTINGS=str(settings),MPC_TEST_LOG=str(log),MPC_LEGACY_ROOT=str(tmp))
   for _ in range(2):subprocess.run(['sh','install.sh','-y','-t',str(target)],cwd=package,env=env,check=True,stdout=subprocess.DEVNULL)
   for helper in ['skin-locations','locations-tool','locations-display']:
    if (package/'portable'/skin/helper).exists():self.assertTrue(os.access(target/skin/helper,os.X_OK),helper+' must remain executable')
   upgraded=settings.read_text();self.assertEqual(upgraded.count(' uid="'+uid+'"'),1);self.assertIn(str(target),upgraded);self.assertEqual((builtin/'plugin_manager.so').read_bytes(),b'original firmware fixture')
   # Boot registration considers built-in content; a valid portable UID must win.
   sync=ROOT/'.deps/mpc-vst-plugins/tools/release/sync.sh'
   subprocess.run(['sh',str(sync),'-y','-n','-t',str(tmp/'builtin')],env=env,check=True,stdout=subprocess.DEVNULL);self.assertEqual(settings.read_text(),upgraded)
   subprocess.run(['sh','uninstall.sh','-y','-t',str(target)],cwd=package,env=env,check=True,stdout=subprocess.DEVNULL)
   subprocess.run(['sh',str(sync),'-y','-n','-t',str(tmp/'builtin')],env=env,check=True,stdout=subprocess.DEVNULL)
   self.assertIn(str(builtin/'plugin_manager.so'),settings.read_text());self.assertEqual(settings.read_text().count(' uid="'+uid+'"'),1)
   self.assertEqual(log.read_text().splitlines(),['stop','start','stop','start','stop','start'])
if __name__=='__main__':unittest.main()
