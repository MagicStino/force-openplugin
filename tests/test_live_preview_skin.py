"""Check the cache-independent native display wiring and palette endpoint colours."""
import importlib.util,json,tempfile,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('live',ROOT/'tools/live_preview_skin.py')
live=importlib.util.module_from_spec(spec);spec.loader.exec_module(live)
class LiveSkinTests(unittest.TestCase):
 def test_palette_and_all_pixel_handles(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);data={'params':[dict(key='existing',min=0,max=1)]};live.add_parameters(data)
   self.assertEqual(data['params'][0]['key'],'existing');self.assertEqual(len(data['params']),5401)
   (root/'params.json').write_text(json.dumps(data));tui=root/'TUI.json'
   tui.write_text(json.dumps({'pageData':{'componentDefinitions':{'localComponentDefinitions':[{'key':'CATALOG|CATALOG','value':{'componentsData':[]}}]}}}))
   live.install(root,tui)
   palette=Image.open(root/'live-preview-palette.png');self.assertEqual(palette.size,(3,12288))
   for index,colour in [(0,(0,0,0,255)),(4095,(255,255,255,255)),(0xf83,(255,136,51,255))]:self.assertEqual(palette.getpixel((1,index*3+1)),colour)
   nodes=json.loads(tui.read_text())['pageData']['componentDefinitions']['localComponentDefinitions'][0]['value']['componentsData']
   self.assertEqual(len(nodes),5400);seen=set()
   for node in nodes:
    d=node['componentData']['data'];self.assertEqual(d['imageType'],'FilmStrip');self.assertEqual(d['numFrames'],4096)
    seen.add(node['handle remapping']['map'][0]['value'])
    x,y,w,h=map(int,node['bounds']['bounds'].split());self.assertTrue(0<=x<x+w<=1280 and 0<=y<y+h<=628)
    self.assertFalse(d['image'].startswith('/data/'))
   self.assertEqual(len(seen),5400)
