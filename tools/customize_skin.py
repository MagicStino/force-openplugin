"""Add a native touchscreen source page; artwork stays code-generated SVG."""
import html
import json
from pathlib import Path

CHARS = 'abcdefghijklmnopqrstuvwxyz0123456789-._/: '

def customize(vst):
    vst = Path(vst)
    data = json.loads((vst / 'params.json').read_text())
    previews=json.loads((Path(__file__).resolve().parents[1]/'assets/previews.lock.json').read_text())['entries']
    for row in range(1,4):
        data['params'].append(dict(key=f'r{row}_rom',name='ROM setup available',options=['no','yes']))
        data['params'].append(dict(key=f'r{row}_rom_install',name='Install ROMs + plugin',type='trigger',momentary=True))
        data['params'].append(dict(key=f'r{row}_preview',name='Preview snapshot',options=[str(i) for i in range(len(previews)+2)]))
        for suffix in ['desc1','desc2']:
            data['params'].append(dict(key=f'r{row}_{suffix}',name='Description',type='readout',display='string'))
    layout=(vst/'layout.conf').read_text().splitlines()
    import re
    redesigned=[]
    for line in layout:
        if re.search(r'key=r[123]_(init|kindtxt|meta|chan|cpu|old|tested|tested_txt|size|sha)\b',line): continue
        if re.search(r'key=card[123]\b',line):
            line=line.replace('tx=125','tx=208').replace('ttw=640','ttw=580').replace('tth=50','tth=39').replace('tsize=46','tsize=34')
        redesigned.append(line)
        match=re.search(r'key=card([123])\b',line)
        if match:
            row=int(match.group(1));y=210+(row-1)*128
            files=','.join(f'images/previews/preview_{i}.png' for i in range(len(previews)+2))
            redesigned.append(f'picture x=40 y={y+14} w=176 h=86 key=r{row}_preview files="{files}"')
            for suffix,cy,size in [('desc1',y+56,20),('desc2',y+77,20),('meta',y+101,18)]:
                redesigned.append(f'readout box=0 w=580 h=22 cx=522 cy={cy} label="" key=r{row}_{suffix} tsize={size} tcolor=b4b7bc tpad=0 talign=left when=r{row}_vis:on')
    (vst/'layout.conf').write_text('\n'.join(redesigned)+'\n')
    next(p for p in data['params'] if p['key']=='kind')['options']=['All','Instruments','Effects','Trackers','Samplers','Tools']
    data['params'].append(dict(key='source_mode', name='Find mode', options=['search','url']))
    for key in ['source_url', 'source_status']:
        data['params'].append(dict(key=key, name=key, type='readout', display='string'))
    keys = ['source_scan', 'source_back', 'source_clear', 'source_cleartext', 'source_search'] + [f'source_key_{i}' for i in range(len(CHARS))]
    for key in keys:
        data['params'].append(dict(key=key, name=key, type='trigger', momentary=True))
    for key in ['rom_status']+[f'rom_file_{i}' for i in range(5)]:
        data['params'].append(dict(key=key,name=key,type='readout',display='string'))
    for key in ['rom_check','rom_usb','rom_download']:
        data['params'].append(dict(key=key,name=key,type='trigger',momentary=True))
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
    def button(name, label, w=100, h=52, primary=False, font=25):
        color = '#72e6cc' if primary else '#222838'
        ink = '#0c1715' if primary else '#e9edff'
        art(name, w, h, f'<rect width="{w}" height="{h}" rx="12" fill="{color}"/>' + text(18, h//2+9, label, font, ink))
    lines = ['\n[tab FIND]', 'art file=images/sources.svg',
        'readout box=0 w=960 h=48 cx=520 cy=264 label="" key=source_url tsize=32 tcolor=e9edff tpad=0',
        'readout box=0 w=1180 h=44 cx=640 cy=349 label="" key=source_status tsize=23 tcolor=72e6cc tpad=0']
    button('source_cleartext.svg','Clear text',190,52)
    lines.append('button cx=1140 cy=264 label="" key=source_cleartext img=images/source_cleartext.svg w=190 h=52')
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


    button('refresh_catalog.svg','Refresh catalog',188,52,font=22)
    textlayout=(vst/'layout.conf').read_text()
    textlayout='\n'.join(line for line in textlayout.splitlines() if 'key=update_all ' not in line)+'\n'
    textlayout=textlayout.replace('[tab FIND]','button cx=924 cy=678 label="" key=refresh img=images/refresh_catalog.svg w=188 h=52\n\n[tab FIND]')
    (vst/'layout.conf').write_text(textlayout)
    button('rom_install.svg','Install ROMs + plugin',396,48,True)
    textlayout=(vst/'layout.conf').read_text()
    controls='\n'.join(f'button cx=1010 cy={293+(row-1)*128} label="" key=r{row}_rom_install img=images/rom_install.svg w=396 h=48 when=r{row}_rom:yes' for row in range(1,4))
    textlayout=textlayout.replace('[tab FIND]',controls+'\n\n[tab FIND]')
    (vst/'layout.conf').write_text(textlayout)
