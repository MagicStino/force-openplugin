"""Native cached bitmap thumbnails with indexed visibility; no per-pixel controls."""
import json
from pathlib import Path
import shutil
COLS, LINES, CELL = 60, 30, 6

def add_parameters(data):
    for row in range(1,4):
        for pixel in range(COLS*LINES):
            data['params'].append(dict(key=f'previewpx_{row}_{pixel}',name='Catalog image pixel',min=0,max=4095,default=273))

def add_ready_parameters(data):
    # Append after all existing controls; preserve saved project parameter IDs.
    for row in range(1,4):
        data['params'].append(dict(key=f'preview_live_{row}',name='Online artwork ready',min=0,max=1,default=0))

def install(vst,tui):
    """Standard Image components; only one cached bitmap is visible per row."""
    vst,tui=Path(vst),Path(tui)
    params=json.loads((vst/'params.json').read_text())['params']
    ids={p['key']:i for i,p in enumerate(params)}
    data=json.loads(tui.read_text())
    catalog=next(x['value'] for x in data['pageData']['componentDefinitions']['localComponentDefinitions'] if x['key']=='CATALOG|CATALOG')
    preview_handles={f'Parameter {ids[f"r{row}_preview"]}' for row in range(1,4)}
    catalog['componentsData']=[n for n in catalog['componentsData'] if n.get('componentData',{}).get('name') not in ('Live preview cell','Bitmap thumbnail','Online fallback cell') and not any(h.split('/',3)[-1] in preview_handles for h in n['bounds'].get('additionalInvalidatingHandles',[]))]
    count=len(next(p for p in params if p['key']=='r1_preview')['options'])
    for i in range(count):
        shutil.copyfile(vst/f'images/previews/preview_{i}.png', tui.parent/f'catalog-preview-{i}.png')
    for row in range(1,4):
        for i in range(count):
            catalog['componentsData'].append({
                'version':2,
                'componentData':{'version':1,'name':'Bitmap thumbnail','type':'Image','data':{
                    'version':2,'imageType':'Regular','colour':'0','image':f'catalog-preview-{i}.png'}},
                'handle remapping':{'version':1,'map':[]},
                'bounds':{'version':2,'acceptsHWFocus':'No','showWhenDataModelInvalid':'Show',
                    'whenVisible':'Always','boundsType':'Absolute','bounds':f'40 {138+(row-1)*128} 176 86',
                    'additionalInvalidatingHandles':[f'IndexedEnabling/{i}/{count}/Parameter {ids[f"r{row}_preview"]}']}})
    (tui.parent/'catalog-thumbnails.png').unlink(missing_ok=True)
    from PIL import Image
    palette=Image.new('RGB',(1,4096))
    palette.putdata([((v>>8)*17,((v>>4)&15)*17,(v&15)*17) for v in range(4096)])
    palette.save(tui.parent/'online-preview-palette.png')
    for row in range(1,4):
        for y in range(15):
            for x in range(30):
                left=40+x*176//30;top=138+(row-1)*128+y*86//15
                w=(x+1)*176//30-x*176//30;h=(y+1)*86//15-y*86//15
                catalog['componentsData'].append({'version':2,'componentData':{'version':1,'name':'Online fallback cell','type':'Image','data':{'version':2,'imageType':'FilmStrip','colour':'0','image':'online-preview-palette.png','numFrames':4096,'handleName':'Data','animated':False}},'handle remapping':{'version':1,'map':[{'key':'Data','value':f'Parameter {ids[f"previewpx_{row}_{y*120+x*2}"]}'}]},'bounds':{'version':2,'acceptsHWFocus':'No','showWhenDataModelInvalid':'Hide','whenVisible':'Always','boundsType':'Absolute','bounds':f'{left} {top} {w} {h}','additionalInvalidatingHandles':[f'IndexedEnabling/1/2/Parameter {ids[f"preview_live_{row}"]}',f'IndexedEnabling/1/{count}/Parameter {ids[f"r{row}_preview"]}']}})
    tui.write_text(json.dumps(data,indent=2)+'\n')
    return len(ids)
