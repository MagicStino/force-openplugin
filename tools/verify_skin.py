#!/usr/bin/env python3
"""Check generated touch bounds and render a simulated FIND page from actual TUI assets."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('native',type=Path)
p.add_argument('output',type=Path)
a=p.parse_args()
vst=a.native/'source/vst'
skin=vst/'build/skin/poloq - VST - Plugin Manager/Plugin Skins'
data=json.loads((skin/'TUI.json').read_text())['pageData']
defs={x['key']:x['value'] for x in data['componentDefinitions']['localComponentDefinitions']}
params=json.loads((vst/'params.json').read_text())['params']
names={f'Parameter {i}':x['key'] for i,x in enumerate(params)}
assert [t['tabName'] for t in data['tabs']]==['CATALOG','FIND','REMOTE ACCESS']
a.output.mkdir(parents=True,exist_ok=True)
for mode in [0,1]:
    image=Image.new('RGBA',(1280,628),'#0c0c0d')
    touches=[]
    for node in defs['FIND|FIND']['componentsData']:
        bounds=node['bounds'];x,y,w,h=map(int,bounds['bounds'].split())
        assert 0<=x and 0<=y and x+w<=1280 and y+h<=628,(x,y,w,h)
        active=True
        for handle in bounds.get('additionalInvalidatingHandles',[]):
            if handle.startswith('IndexedEnabling/'):
                _,value,_,parameter=handle.split('/',3)
                assert names[parameter]=='source_mode'
                active &= int(value)==mode
        if not active: continue
        comp=node['componentData'];typ=comp['type'];info=comp['data']
        mapping={m['key']:m['value'] for m in node['handle remapping']['map']}
        if typ=='Image':
            image.alpha_composite(Image.open(skin/info['image']).convert('RGBA'),(x,y))
        elif typ.startswith('shTrig_'):
            assert w>=44 and h>=44
            for ox,oy,ow,oh in touches:
                assert x+w<=ox or ox+ow<=x or y+h<=oy or oy+oh<=y,'Overlapping touch targets'
            touches.append((x,y,w,h))
            button=next(c for c in defs[typ]['componentsData'] if c['componentData']['type']=='Button')
            name=button['componentData']['data']['offImage']
            image.alpha_composite(Image.open(skin/name).convert('RGBA'),(x,y))
        elif typ.startswith('shReadout_'):
            key=names[mapping['Data']]
            text=('reverb' if mode==0 else 'https://github.com/owner/repository') if key=='source_url' else ('Examples: acid, reverb, Airwindows. Browse everything in CATALOG; no search needed.' if mode==0 else 'Enter a community source link, then choose Check source.')
            style=defs[typ]['componentsData'][0]['componentData']['data']['textStyle']
            fontpath=a.native/'dependencies/mpc-vst-plugins/tools/html_art/fonts/TitilliumWeb-Regular.ttf'
            font=ImageFont.truetype(str(fontpath),round(style['font']['height']/1.52))
            draw=ImageDraw.Draw(image)
            assert draw.textlength(text,font=font)<w,'Text overflows readout'
            draw.text((x+w/2,y+h/2),text,font=font,fill='#e9edff',anchor='mm')
    assert len(touches)==47,len(touches)
    image.convert('RGB').save(a.output/('find-search.png' if mode==0 else 'find-source.png'))
print('FIND: both modes, 47 non-overlapping touch targets, bounds/text/assets PASS')
image=Image.new('RGBA',(1280,628),'#0c0c0d')
touches=[]
examples={'remote_status':'Running - SSH / SFTP port 22','remote_ip':'192.168.178.79','remote_password':'Username: root    Password: mpc    Port: 22','remote_storage':'SFTP: browse /media for internal storage, SD and USB mounts'}
for node in defs['REMOTE ACCESS|REMOTE ACCESS']['componentsData']:
    x,y,w,h=map(int,node['bounds']['bounds'].split())
    assert 0<=x and 0<=y and x+w<=1280 and y+h<=628,(x,y,w,h)
    comp=node['componentData'];typ=comp['type'];info=comp['data']
    mapping={m['key']:m['value'] for m in node['handle remapping']['map']}
    if typ=='Image':image.alpha_composite(Image.open(skin/info['image']).convert('RGBA'),(x,y))
    elif typ.startswith('shTrig_'):
        assert w>=44 and h>=44
        for ox,oy,ow,oh in touches:assert x+w<=ox or ox+ow<=x or y+h<=oy or oy+oh<=y
        touches.append((x,y,w,h))
        button=next(c for c in defs[typ]['componentsData'] if c['componentData']['type']=='Button')
        image.alpha_composite(Image.open(skin/button['componentData']['data']['offImage']).convert('RGBA'),(x,y))
    elif typ.startswith('shReadout_'):
        text=examples[names[mapping['Data']]]
        style=defs[typ]['componentsData'][0]['componentData']['data']['textStyle']
        font=ImageFont.truetype(str(a.native/'dependencies/mpc-vst-plugins/tools/html_art/fonts/TitilliumWeb-Regular.ttf'),round(style['font']['height']/1.52))
        draw=ImageDraw.Draw(image);assert draw.textlength(text,font=font)<w
        draw.text((x+w/2,y+h/2),text,font=font,fill='#e9edff',anchor='mm')
assert len(touches)==3
image.convert('RGB').save(a.output/'remote-access-preview.png')
print('REMOTE ACCESS: three touch targets, bounds/text/assets PASS (simulated preview)')
