"""Add a native touchscreen source page; artwork stays code-generated SVG."""
import html
import json
from pathlib import Path

CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789-._/: '

def customize(vst):
    vst = Path(vst)
    data = json.loads((vst / 'params.json').read_text())
    next(p for p in data['params'] if p['key']=='kind')['options']=['All','Instruments','Effects','Trackers','Samplers','Tools']
    data['params'].append(dict(key='source_mode', name='Find mode', options=['search','url']))
    for key in ['source_url', 'source_status']:
        data['params'].append(dict(key=key, name=key, type='readout', display='string'))
    keys = ['source_scan', 'source_back', 'source_clear', 'source_search'] + [f'source_key_{i}' for i in range(len(CHARS))]
    for key in keys:
        data['params'].append(dict(key=key, name=key, type='trigger', momentary=True))
    (vst / 'params.json').write_text(json.dumps(data, indent=2) + '\n')
    def art(name, width, height, body):
        (vst / 'images' / name).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">{body}</svg>\n')
    def text(x, y, value, size=24, fill='#e9edff'):
        return f'<text x="{x}" y="{y}" font-family="Titillium Web" font-size="{size}" fill="{fill}">{html.escape(value)}</text>'
    art('sources.svg', 1280, 628,
        '<rect width="1280" height="628" fill="#0c0c0d"/>'
        '<rect x="24" y="24" width="1232" height="4" rx="2" fill="#72e6cc"/>' +
        text(32, 82, 'SEARCH INSTRUMENTS & PLUGINS', 38) +
        text(32, 119, 'Source: MPC VST Plugins community catalog + your added sources. Browse all in CATALOG.', 23, '#aab1c8') +
        '<rect x="24" y="142" width="1232" height="72" rx="16" fill="#1d2231" stroke="#535c79"/>' +
        '<rect x="24" y="228" width="1232" height="58" rx="12" fill="#151a23"/>')
    def button(name, label, w=100, h=52, primary=False):
        color = '#72e6cc' if primary else '#222838'
        ink = '#0c1715' if primary else '#e9edff'
        art(name, w, h, f'<rect width="{w}" height="{h}" rx="12" fill="{color}"/>' + text(18, h//2+9, label, 25, ink))
    lines = ['\n[tab FIND]', 'art file=images/sources.svg',
        'readout box=0 w=1180 h=48 cx=640 cy=264 label="" key=source_url tsize=32 tcolor=e9edff tpad=0',
        'readout box=0 w=1180 h=44 cx=640 cy=349 label="" key=source_status tsize=23 tcolor=72e6cc tpad=0']
    # Skin coordinates include the host header's 86 px offset.
    keyboard=['1234567890-_','qwertyuiop/:','asdfghjkl.','zxcvbnm ']
    assert sorted(''.join(keyboard)) == sorted(CHARS)
    for row, keys in enumerate(keyboard):
        start=(1280-len(keys)*102+10)//2+46
        for col,char in enumerate(keys):
            i=CHARS.index(char)
            name = f'source_key_{i}.svg'
            button(name, char.upper() if char != ' ' else 'Space', 92, 52)
            lines.append(f'button cx={start+col*102} cy={414+row*62} label="" key=source_key_{i} img=images/{name} w=92 h=52')
    for key, label, x, width, primary in [('source_search','Add source',160,264,False), ('source_clear','Show all',460,264,False), ('source_back','Delete',760,264,False), ('source_scan','Filter catalog',1080,320,True)]:
        button(key+'.svg', label, width, 52, primary)
        when = ' when=source_mode:search' if key in ['source_search','source_scan','source_clear'] else ''
        lines.append(f'button cx={x} cy=662 label="" key={key} img=images/{key}.svg w={width} h=52{when}')
        if when:
            alternate = 'Back to search' if key == 'source_search' else 'Clear URL' if key=='source_clear' else 'Check source'
            button(key+'_url.svg',alternate,width,52,primary)
            lines.append(f'button cx={x} cy=662 label="" key={key} img=images/{key}_url.svg w={width} h=52 when=source_mode:url')
    with (vst / 'layout.conf').open('a') as f:
        f.write('\n'.join(lines) + '\n')
