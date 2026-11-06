"""Native cached bitmap thumbnails with indexed visibility; no per-pixel controls."""
import json
from pathlib import Path
import shutil

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
    (tui.parent/'online-preview-palette.png').unlink(missing_ok=True)
    tui.write_text(json.dumps(data,indent=2)+'\n')
    return len(ids)
