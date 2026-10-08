import copy,importlib.util,json,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('bridge',Path(__file__).resolve().parents[1]/'tools/catalog_bridge.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
class BridgeTests(unittest.TestCase):
 def setUp(self):self.m=json.loads((b.ROOT/'catalog/example.openplugin.json').read_text())
 def test_example(self):self.assertEqual(b.validate_manifest(self.m,self.m['repo'])['id'],'example-sampler')
 def test_identity_collision(self):
  with self.assertRaises(ValueError):b.validate_manifest(self.m,'other/repo')
 def test_unsafe_images(self):
  self.m['images']=['http://localhost/private']
  with self.assertRaises(ValueError):b.validate_manifest(self.m,self.m['repo'])
 def test_package_integrity_and_target(self):
  p={'version':'1.0','size':42,'arch':'armv7','layout':'portable','devices':['force'],'url':'https://github.com/example/example-sampler/releases/download/v1/plugin.zip','sha256':'a'*64};self.m['packages']=[p];b.validate_manifest(self.m,self.m['repo']);p['arch']='x86_64'
  with self.assertRaises(ValueError):b.validate_manifest(self.m,self.m['repo'])
 def test_bad_download_is_not_installable(self):
  p={'id':'test','name':'Test','repo':'owner/repo','kind':'instrument','versions':[{'url':'file:///etc/passwd','sha256':'a'*64}]};self.assertEqual(b.normalize_plugin(p,'fixture')['versions'],[])
 def test_preserves_last_catalog_on_primary_failure(self):
  oldroot=b.ROOT
  with tempfile.TemporaryDirectory() as tmp:
   b.ROOT=Path(tmp);(b.ROOT/'catalog').mkdir();(b.ROOT/'website').mkdir();(b.ROOT/'catalog/sources.json').write_text(json.dumps({'upstream':'fixture'}));target=b.ROOT/'website/catalog.json';target.write_text('last good catalog')
   with self.assertRaises(ValueError):b.update(lambda _: {'schema':1,'plugins':[]})
   self.assertEqual(target.read_text(),'last good catalog')
  b.ROOT=oldroot
if __name__=='__main__':unittest.main()
