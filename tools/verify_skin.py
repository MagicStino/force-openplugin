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
skin=vst/'build/skin/OPENPLUGIN - VST - OpenPlugin Manager/Plugin Skins'
data=json.loads((skin/'TUI.json').read_text())['pageData']
defs={x['key']:x['value'] for x in data['componentDefinitions']['localComponentDefinitions']}
params=json.loads((vst/'params.json').read_text())['params']
names={f'Parameter {i}':x['key'] for i,x in enumerate(params)}
assert [t['tabName'] for t in data['tabs']]==['CATALOG','FIND','REMOTE ACCESS','STORAGE','ABOUT']
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
assert len(touches)==2
# Exactly the applicable action is exposed in each running/stopped state.
remote_nodes=defs['REMOTE ACCESS|REMOTE ACCESS']['componentsData']
for running in [False,True]:
    shown=[]
    for node in remote_nodes:
        if not node['componentData']['type'].startswith('shTrig_'):continue
        mapping={m['key']:m['value'] for m in node['handle remapping']['map']}
        visible=True
        for handle in node['bounds'].get('additionalInvalidatingHandles',[]):
            if handle.startswith('IndexedEnabling/'):
                _,value,_,parameter=handle.split('/',3)
                key=names[parameter]
                flags={'remote_can_enable':not running,'remote_can_disable':running}
                visible &= int(value)==int(flags[key])
        if visible:shown.append(node)
    assert len(shown)==1
assert all(i<512 for i,p in enumerate(params) if p['key'].startswith(('remote_', 'locations_', 'storage_')))
assert len(params)<=256 and not any(p['key'].startswith(('previewpx_', 'preview_live_')) for p in params)
image.convert('RGB').save(a.output/'remote-access-preview.png')
print('REMOTE ACCESS: running/stopped actions, low control IDs, bounds/text/assets PASS (simulated preview)')

# Render each conditional state: impossible actions must not appear.
for state,flags,drive,message in [
    ('locations-preview',dict(locations_ready=0,locations_idle=1,locations_can_move=0,locations_can_choose=0,locations_can_repair=1),'No suitable destination','No suitable destination. Connect a drive that can run VSTs.'),
    ('locations-calculating',dict(locations_ready=0,locations_idle=0,locations_can_move=0,locations_can_choose=0,locations_can_repair=0),'SSD','Calculating move to SSD...'),
    ('locations-choose',dict(locations_ready=0,locations_idle=1,locations_can_move=1,locations_can_choose=1,locations_can_repair=1),'1 of 2: Plugin drive','Choose where to put your managed plugins.'),
    ('locations-move',dict(locations_ready=1,locations_idle=0,locations_can_move=0,locations_can_choose=0,locations_can_repair=0),'1 of 2: Plugin drive','Move 59 plugins (830.5 MB). Save your project before restarting. Copies verified before freeing Internal space.'),
    ('locations-repair',dict(locations_ready=2,locations_idle=0,locations_can_move=0,locations_can_choose=0,locations_can_repair=0),'No suitable destination','Repair 1 missing screen location. Save your project before restarting.'),
    ('locations-return-ready',dict(locations_ready=0,locations_idle=1,locations_can_move=0,locations_can_choose=0,locations_can_repair=1,locations_can_return=1),'Plugins moved; return to Internal is available','Internal copies will be checked before switching back.'),
    ('locations-return-confirm',dict(locations_ready=4,locations_idle=0,locations_can_move=0,locations_can_choose=0,locations_can_repair=0),'Return plugins to Internal','Return 59 plugins to verified Internal copies. Drive copies stay. Save your project before restarting.'),
    ('locations-log',dict(locations_ready=3,locations_idle=0,locations_can_move=0,locations_can_choose=0,locations_can_repair=0,locations_log_older=1,locations_log_newer=1),'Critical event 2 of 3','ERROR Copying JV-880: Cannot write copied plugin file. Original files retained.')]:
    flags.update(storage_list=int(flags['locations_ready']==0),storage_details=int(flags['locations_ready']!=0),storage_has_prev=0,storage_has_next=0)
    for row in range(1,4):
        flags[f'storage_row{row}_busy']=int(state=='locations-calculating' and row==2)
        flags[f'storage_row{row}_visible']=flags['storage_list']
        flags[f'storage_row{row}_move']=int(flags['storage_list'] and row>1 and state=='locations-choose')
    flags.setdefault('locations_can_return',0)
    flags.setdefault('locations_can_log',flags['locations_idle'])
    flags.setdefault('locations_log_older',0);flags.setdefault('locations_log_newer',0)
    image=Image.new('RGBA',(1280,628),'#0c0c0d');touches=[];keys=[]
    parts=[]
    while message:
        cut=len(message) if len(message)<=64 else message.rfind(' ',0,65)
        if cut<=0:cut=64
        parts.append(message[:cut]);message=message[cut:].lstrip()
    examples={'storage_internal':'Internal: 12.0 GB free','storage_preferred':'SSD: 238.4 GB free',
              'locations_drive':drive,'locations_info':'Photograph this screen for support' if flags['locations_ready']==3 else 'Storage: 238.4 GB free' if flags['locations_can_move'] or flags['locations_ready']==1 else 'Only compatible destinations appear here',
              **{f'locations_status{i+1}':parts[i] if len(parts)>i else '' for i in range(3)}}
    examples.update(storage_warning='Move only plugins installed with this manager.',storage_tip='Repair plugin skins if a plugin screen is missing.')
    for row,label,space,status in [(1,'Internal','3.2 GB free','Main plugin location'),(2,'SSD','45.3 GB free',''),(3,'MUSIC','8.1 GB free','')]:
        examples.update({f'storage_row{row}_label':label,f'storage_row{row}_space':space,f'storage_row{row}_status':status})
    if state=='locations-calculating':
        examples.update(storage_warning='Calculating move to SSD...',storage_tip='Please wait. You can review the result before moving anything.',storage_row2_status='Checking plugin files and available space...')
    for node in defs['STORAGE|STORAGE']['componentsData']:
        x,y,w,h=map(int,node['bounds']['bounds'].split())
        assert 0<=x and 0<=y and x+w<=1280 and y+h<=628,(x,y,w,h)
        active=True
        for handle in node['bounds'].get('additionalInvalidatingHandles',[]):
            if handle.startswith('IndexedEnabling/'):
                _,value,_,parameter=handle.split('/',3)
                active &= flags[names[parameter]]==int(value)
        if not active:continue
        comp=node['componentData'];typ=comp['type'];info=comp['data']
        mapping={m['key']:m['value'] for m in node['handle remapping']['map']}
        if typ=='Image':image.alpha_composite(Image.open(skin/info['image']).convert('RGBA'),(x,y))
        elif typ.startswith('shTrig_'):
            assert w>=44 and h>=44
            for ox,oy,ow,oh in touches:assert x+w<=ox or ox+ow<=x or y+h<=oy or oy+oh<=y
            touches.append((x,y,w,h))
            keys.append(names.get(mapping.get('Value',mapping.get('Data','')),''))
            button=next(c for c in defs[typ]['componentsData'] if c['componentData']['type']=='Button')
            image.alpha_composite(Image.open(skin/button['componentData']['data']['offImage']).convert('RGBA'),(x,y))
        elif typ.startswith('shReadout_'):
            text=examples[names[mapping['Data']]]
            style=defs[typ]['componentsData'][0]['componentData']['data']['textStyle']
            font=ImageFont.truetype(str(a.native/'dependencies/mpc-vst-plugins/tools/html_art/fonts/TitilliumWeb-Regular.ttf'),round(style['font']['height']/1.52))
            assert font.size>=17
            draw=ImageDraw.Draw(image);assert draw.textlength(text,font=font)<w,(state,text,w)
            draw.text((x+w/2,y+h/2),text,font=font,fill='#e9edff',anchor='mm')
    assert len(touches)=={'locations-calculating':0,'locations-preview':3,'locations-choose':5,'locations-move':2,'locations-repair':2,'locations-log':3,'locations-return-ready':3,'locations-return-confirm':2}[state],(state,len(touches))
    image.convert('RGB').save(a.output/(state+'.png'))
print('STORAGE: eight states, conditional actions, larger text, touch bounds PASS (simulated previews)')
