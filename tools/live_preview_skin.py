"""Native live thumbnails: immutable RGB444 palette + display-only pixel values.

Akai caches skin PNGs, so replacing a file cannot update an already open view.
FilmStrip is a stock native Image mode. These cells change values instead of
paths, with one shared 3x12288 palette (4096 frames), no filesystem UI hook.
"""
import json
from pathlib import Path
from PIL import Image
COLS, LINES, CELL = 60, 30, 3

def add_parameters(data):
    for row in range(1,4):
        for pixel in range(COLS*LINES):
            data['params'].append(dict(key=f'previewpx_{row}_{pixel}',name='Catalog image pixel',min=0,max=4095,default=273))

def install(vst,tui):
    vst,tui=Path(vst),Path(tui)
    skin=tui.parent
    palette=Image.new('RGBA',(CELL,4096*CELL))
    for value in range(4096):
        colour=(((value>>8)&15)*17,((value>>4)&15)*17,(value&15)*17,255)
        for dy in range(CELL):
            for dx in range(CELL):palette.putpixel((dx,value*CELL+dy),colour)
    palette.save(skin/'live-preview-palette.png')
    params=json.loads((vst/'params.json').read_text())['params']
    ids={p['key']:i for i,p in enumerate(params)}
    data=json.loads(tui.read_text())
    catalog=next(x['value'] for x in data['pageData']['componentDefinitions']['localComponentDefinitions'] if x['key']=='CATALOG|CATALOG')
    # Static indexed pictures remain the immediate bundled fallback. Live cells
    # cover them when the matching worker snapshot is ready, never on stale rows.
    catalog['componentsData']=[n for n in catalog['componentsData'] if n.get('componentData',{}).get('name')!='Live preview cell']
    for row in range(1,4):
        for pixel in range(COLS*LINES):
            parameter=f'Parameter {ids[f"previewpx_{row}_{pixel}"]}'
            x=40+(pixel%COLS)*CELL
            y=210+(row-1)*128+14-86+(pixel//COLS)*CELL
            catalog['componentsData'].append({
                'version':2,
                'componentData':{'version':1,'name':'Live preview cell','type':'Image','data':{
                    'version':2,'imageType':'FilmStrip','colour':'0','image':'live-preview-palette.png',
                    'numFrames':4096,'handleName':'Data','animated':False}},
                'handle remapping':{'version':1,'map':[{'key':'Data','value':parameter}]},
                'bounds':{'version':2,'acceptsHWFocus':'No','showWhenDataModelInvalid':'Hide',
                    'whenVisible':'Always','boundsType':'Absolute','bounds':f'{x} {y} {CELL} {CELL}',
                    'additionalInvalidatingHandles':([f'IndexedEnabling/1/NormalisedValue/Parameter {ids[f"r{row}_vis"]}'] if f'r{row}_vis' in ids else [])}})
    tui.write_text(json.dumps(data,indent=2)+'\n')
    return len(ids)
