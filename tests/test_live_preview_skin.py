import importlib.util,json,tempfile,unittest
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('live',ROOT/'tools/live_preview_skin.py');live=importlib.util.module_from_spec(spec);spec.loader.exec_module(live)
class BitmapTests(unittest.TestCase):
 def test_three_bitmaps_and_legacy_ids(self):
  with tempfile.TemporaryDirectory() as tmp:
   r=Path(tmp);(r/'images/previews').mkdir(parents=True)
   data={'params':[]}
   for row in range(1,4):data['params'] += [dict(key=f'r{row}_preview',options=['0','1','2']),dict(key=f'r{row}_vis')]
   (r/'params.json').write_text(json.dumps(data))
   for i in range(3):Image.new('RGBA',(176,86),(i*80,0,0,255)).save(r/f'images/previews/preview_{i}.png')
   t=r/'TUI.json';t.write_text(json.dumps({'pageData':{'componentDefinitions':{'localComponentDefinitions':[{'key':'CATALOG|CATALOG','value':{'componentsData':[]}}]}}}))
   live.install(r,t);live.install(r,t)
   nodes=json.loads(t.read_text())['pageData']['componentDefinitions']['localComponentDefinitions'][0]['value']['componentsData']
   self.assertEqual(len(nodes),9)
   for n in nodes:
    for handle in n["bounds"].get("additionalInvalidatingHandles",[]):
     prefix,index,count,param=handle.split("/",3)
     self.assertEqual(prefix,"IndexedEnabling")
     self.assertTrue(count.isdigit(),handle)
     self.assertLess(int(index),int(count))
   self.assertFalse((r/'online-preview-palette.png').exists())
   self.assertFalse((r/'catalog-thumbnails.png').exists())
   for i in range(3):
    with Image.open(r/f'catalog-preview-{i}.png') as frame:
     self.assertEqual(frame.size,(176,86));self.assertEqual(frame.getpixel((0,0)),(i*80,0,0,255))
   for row in range(3):
    for i in range(3):
     n=nodes[row*3+i]
     self.assertEqual(n['componentData']['data']['imageType'],'Regular')
     self.assertEqual(n['bounds']['additionalInvalidatingHandles'],[f'IndexedEnabling/{i}/3/Parameter {row*2}'])
