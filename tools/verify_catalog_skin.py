#!/usr/bin/env python3
"""Render actual generated CATALOG assets with sample metadata; not a hardware capture."""
import argparse,json,textwrap
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=argparse.ArgumentParser(description=__doc__);p.add_argument('native',type=Path);p.add_argument('output',type=Path);p.add_argument('--jv',action='store_true');a=p.parse_args()
root=Path(__file__).resolve().parents[1];vst=a.native/'source/vst';skin=vst/'build/skin/poloq - VST - Plugin Manager/Plugin Skins'
data=json.loads((skin/'TUI.json').read_text())['pageData'];defs={x['key']:x['value'] for x in data['componentDefinitions']['localComponentDefinitions']}
params=json.loads((vst/'params.json').read_text())['params'];names={f'Parameter {i}':p['key'] for i,p in enumerate(params)}
lock=json.loads((root/'assets/previews.lock.json').read_text())['entries'];catalog=json.loads((root/'website/assets/catalog.json').read_text())['plugins']
values={p['key']:0 for p in params};values.update(net=0,loaded=1,disk_txt='Sample metadata',status='Rendered interface preview',page_txt='1 / 24')
if a.jv:catalog=sorted(catalog,key=lambda p:(p['id'] not in ('jv-880','dexed-dx7','dub-force-siren'),p['id']))[:3]
for row,plugin in enumerate(catalog[:3],1):
 wrapped=textwrap.wrap(plugin.get('summary') or 'No description supplied by the author.',78)
 values.update({f'card{row}_1':plugin['name'],f'r{row}_vis':1,f'r{row}_state':1,f'r{row}_preview':next(i+2 for i,x in enumerate(lock) if x['id']==plugin['id']),f'r{row}_desc1':wrapped[0],f'r{row}_desc2':wrapped[1] if len(wrapped)>1 else '',f'r{row}_meta':f"by {plugin['author'][:32]} | {plugin.get('license','See source')[:28]}",f'r{row}_ver':'',f'r{row}_size':'',f'r{row}_sha':'',f'r{row}_from':''})
if a.jv:
 for row,plugin in enumerate(catalog[:3],1):
  if plugin['id']=='jv-880':
   values.update({f'r{row}_rom':1,f'r{row}_desc1':'Save first: installs ROMs + plugin, then restarts the app.',f'r{row}_desc2':'Required files checked before installation.'})
image=Image.new('RGBA',(1280,628),'#0c0c0d');previews=0

def render(nodes,ox=0,oy=0,key=None,depth=0):
 global previews
 for node in nodes:
  bounds=node['bounds'];x,y,w,h=map(int,bounds['bounds'].split());x+=ox;y+=oy
  assert x>=0 and y>=0 and x+w<=1280 and y+h<=628,(x,y,w,h)
  active=True
  for handle in bounds.get('additionalInvalidatingHandles',[]):
   if handle.startswith('IndexedEnabling/'):
    _,value,_,parameter=handle.split('/',3);active &= values.get(names[parameter],0)==int(value)
  if not active:continue
  mapping={m['key']:m['value'] for m in node['handle remapping']['map']};current=names.get(mapping.get('Data'),key)
  comp=node['componentData'];typ=comp['type'];info=comp['data']
  if typ=='Image':
   asset=Image.open(skin/info['image']).convert('RGBA');assert asset.size==(w,h)
   image.alpha_composite(asset,(x,y))
   if any(names.get(h.split('/',3)[-1],'').endswith('_preview') for h in bounds.get('additionalInvalidatingHandles',[])):previews+=1
  elif typ=='Button':
   asset=info['offImage'];image.alpha_composite(Image.open(skin/asset).convert('RGBA'),(x,y))
  elif typ=='Label':
   value=values.get(current,'');text=str(value) if value else ''
   if not text:continue
   style=info['textStyle'];font=ImageFont.truetype(str(a.native/'dependencies/mpc-vst-plugins/tools/html_art/fonts/TitilliumWeb-Regular.ttf'),round(style['font']['height']/1.52))
   draw=ImageDraw.Draw(image)
   assert draw.textlength(text,font=font)<=w,(current,text,w)
   left='left' in style['justification'];right='right' in style['justification'];anchor='lm' if left else 'rm' if right else 'mm';tx=x if left else x+w if right else x+w/2
   draw.text((tx,y+h/2),text,font=font,fill='#'+style['colour'][-6:],anchor=anchor)
  elif typ in defs:render(defs[typ]['componentsData'],x,y,current,depth+1)
render(defs['CATALOG|CATALOG']['componentsData']);assert previews==3,previews
for row in range(1,4):
 parameter=next(p for p in params if p['key']==f'r{row}_preview');assert len(parameter['options'])==73
assert Image.open(vst/'images/previews/preview_0.png').getbbox() is None
assert len(list((vst/'images/previews').glob('*.png')))==73
a.output.parent.mkdir(parents=True,exist_ok=True);image.convert('RGB').save(a.output)
print('CATALOG: three previews, 73 frames per row, bounds and sample text PASS; simulated host rendering only')
