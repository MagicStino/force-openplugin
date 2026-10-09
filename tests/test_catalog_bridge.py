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

class SubmissionFlowTests(unittest.TestCase):
 def test_registered_manifest_publishes_json_cards_and_version_updates(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'catalog').mkdir()
   cfg={'upstream':'fixture','repositories':['example/example-sampler'],'search_queries':[],'max_discovered_repositories':0,'reviewed_manifest_repositories':[]}
   (root/'catalog/sources.json').write_text(json.dumps(cfg))
   m=json.loads((b.ROOT/'catalog/example.openplugin.json').read_text())
   m['packages']=[{'version':'0.1','size':42,'arch':'armv7','layout':'portable','devices':['force','mpc-gen1'],'url':'https://github.com/example/example-sampler/releases/download/v0.1/plugin.zip','sha256':'a'*64}]
   def fetch(url):
    if url=='fixture':return {'schema':1,'plugins':[{'id':'existing','name':'Existing','repo':'owner/existing','kind':'instrument','versions':[]}]}
    if url=='https://api.github.com/repos/example/example-sampler':return {'default_branch':'main'}
    if url=='https://raw.githubusercontent.com/example/example-sampler/main/openplugin.json':return m
    raise AssertionError(url)
   with patch.object(b,'ROOT',root),patch.dict(b.os.environ,{'GITHUB_TOKEN':''}):
    b.update(fetch)
    catalog=json.loads((root/'website/catalog.json').read_text())
    card=json.loads((root/'website/assets/catalog.json').read_text())
    plugin=next(p for p in catalog['plugins'] if p['id']==m['id'])
    self.assertEqual(plugin['versions'],[])
    self.assertFalse(next(p for p in card['plugins'] if p['id']==m['id'])['download'])
    cfg['reviewed_manifest_repositories']=[m['repo']]
    (root/'catalog/sources.json').write_text(json.dumps(cfg));b.update(fetch)
    plugin=next(p for p in json.loads((root/'website/catalog.json').read_text())['plugins'] if p['id']==m['id'])
    self.assertEqual(plugin['versions'][0]['version'],'0.1')
    self.assertTrue(next(p for p in json.loads((root/'website/assets/catalog.json').read_text())['plugins'] if p['id']==m['id'])['download'])
    m['packages'][0].update(version='0.2',url='https://github.com/example/example-sampler/releases/download/v0.2/plugin.zip',sha256='b'*64)
    b.update(fetch)
    self.assertEqual(next(p for p in json.loads((root/'website/catalog.json').read_text())['plugins'] if p['id']==m['id'])['versions'][0]['version'],'0.2')
    self.assertEqual(next(p for p in json.loads((root/'website/assets/catalog.json').read_text())['plugins'] if p['id']==m['id'])['versions'][0]['version'],'0.2')


class ProposalReviewTests(unittest.TestCase):
 def test_repository_field_is_strict_and_accept_prepares_registry_only(self):
  import sys
  from unittest.mock import patch
  sys.path.insert(0,str(b.ROOT/'tools'))
  import accept_submission as a
  issue={'title':'[Catalog] Example Sampler','body':'### Public project URL\n\nhttps://github.com/example/example-sampler\n\n### Description\nA sampler'}
  self.assertEqual(a.proposal_repository(issue),'example/example-sampler')
  for url in ['https://evil.test/example/example-sampler','https://github.com/example/example-sampler?token=x','https://github.com/example/example-sampler/blob/main/file']:
   with self.assertRaises(ValueError):a.proposal_repository(dict(issue,body='### Public project URL\n\n'+url))
  m=json.loads((b.ROOT/'catalog/example.openplugin.json').read_text())
  def fetch(url):
   if url.endswith('/issues/12'):return issue
   if url=='https://api.github.com/repos/example/example-sampler':return {'default_branch':'main','private':False,'archived':False}
   if url.endswith('/main/openplugin.json'):return m
   raise AssertionError(url)
  with tempfile.TemporaryDirectory() as tmp,patch.dict(a.os.environ,{'GITHUB_REPOSITORY':'MagicStino/force-openplugin'}):
   root=Path(tmp);(root/'catalog').mkdir();path=root/'catalog/sources.json';path.write_text(json.dumps({'repositories':[],'reviewed_manifest_repositories':[]}))
   a.accept(12,fetch=fetch,root=root)
   self.assertEqual(json.loads(path.read_text()),{'repositories':['example/example-sampler'],'reviewed_manifest_repositories':[]})
   with self.assertRaises(ValueError):a.accept(12,reviewed=True,fetch=fetch,root=root)

if __name__=='__main__':unittest.main()
