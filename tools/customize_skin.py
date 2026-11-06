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
        # Old status buttons overlap the thumbnail and description in this layout.
        if 'img=images/badge_stable.svg' in line or 'img=images/badge_tested.svg' in line: continue
        if any(f'img=images/badge_{kind}.svg' in line for kind in ('beta','cpu','old')):
            cx=850 if 'badge_beta' in line else 944 if 'badge_cpu' in line else 1070
            line=re.sub(r'cx=\d+',f'cx={cx}',line)
            line=re.sub(r'cy=(\d+)',lambda m:f'cy={int(m[1])+5}',line)
        if re.search(r'key=r[123]_(init|kindtxt|meta|chan|cpu|old|tested|tested_txt|size|sha)\b',line): continue
        if re.search(r'key=card[123]\b',line):
            line=line.replace('tx=125','tx=208').replace('ttw=640','ttw=580').replace('tth=50','tth=39').replace('tsize=46','tsize=34')
        redesigned.append(line)
        match=re.search(r'key=card([123])\b',line)
        if match:
            row=int(match.group(1));y=210+(row-1)*128
            files=','.join(f'images/previews/preview_{i}.png' for i in range(len(previews)+2))
            redesigned.append(f'picture x=40 y={y+14} w=176 h=86 key=r{row}_preview files="{files}"')
            for suffix,cy,size in [('desc1',y+56,31),('desc2',y+82,31),('meta',y+106,18)]:
                height=26 if suffix.startswith('desc') else 18
                redesigned.append(f'readout box=0 w=580 h={height} cx=522 cy={cy} label="" key=r{row}_{suffix} tsize={size} tcolor=b4b7bc tpad=0 talign=left when=r{row}_vis:on')
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

    remote=json.loads((vst/'params.json').read_text())
    for key in ['remote_status','remote_ip','remote_password','remote_storage']:
        remote['params'].append(dict(key=key,name=key,type='readout',display='string'))
    for key in ['remote_enable','remote_disable','remote_show']:
        remote['params'].append(dict(key=key,name=key,type='trigger',momentary=True))
    (vst/'params.json').write_text(json.dumps(remote,indent=2)+'\n')
    art('remote.svg',1280,628,'<rect width="1280" height="628" fill="#0c0c0d"/>'+text(32,70,'REMOTE ACCESS',38)+text(32,116,'SSH / SFTP',24)+text(32,160,'Connect using the IP below, port 22.',23)+text(32,205,'Login: root / mpc. Disable saves your choice across reboots.',23))
    lines=['\n[tab REMOTE ACCESS]','art file=images/remote.svg']
    for key,y in [('remote_status',330),('remote_ip',390),('remote_password',450),('remote_storage',510)]:
        lines.append(f'readout box=0 w=1180 h=48 cx=640 cy={y} label="" key={key} tsize=40 tcolor=e9edff tpad=0')
    for key,label,x,w in [('remote_enable','Enable remote access',320,570),('remote_disable','Disable remote access',960,570)]:
        button(key+'.svg',label,w,72,font=32)
        lines.append(f'button cx={x} cy=620 label="" key={key} img=images/{key}.svg w={w} h=72 when=remote_can_{"enable" if key=="remote_enable" else "disable"}:yes')
    with (vst/'layout.conf').open('a') as f:f.write('\n'.join(lines)+'\n')

    # Larger touch targets and one-point text increase on the catalog/install view.
    layout_path = vst/'layout.conf'
    sections = layout_path.read_text().split('[tab FIND]', 1)
    catalog = re.sub(r'tsize=(\d+)', lambda m: f'tsize={int(m[1])+1}', sections[0])
    catalog = catalog.replace('cx=46 cy=678', 'cx=48 cy=676').replace('cx=166 cy=678', 'cx=176 cy=676')
    catalog = catalog.replace('cx=106 cy=678', 'cx=112 cy=676')
    catalog = '\n'.join(line.replace('w=44 h=44', 'w=64 h=64') if 'key=page_' in line else line for line in catalog.split('\n'))
    layout_path.write_text(catalog + '[tab FIND]' + sections[1])

    # Append controls after all existing parameter IDs to preserve saved projects.
    parameters=json.loads((vst/'params.json').read_text())
    for key in ['locations_drive','locations_info','locations_summary','locations_status','storage_internal','storage_preferred']:
        parameters['params'].append(dict(key=key,name=key,type='readout',display='string'))
    for key in ['locations_scan','locations_prev','locations_next','locations_plan','locations_confirm','locations_cancel','locations_repair','locations_log','locations_log_prev','locations_log_next']:
        parameters['params'].append(dict(key=key,name=key,type='trigger',momentary=True))
    parameters['params'].append(dict(key='locations_ready',name='Confirm storage change',options=['no','move','repair','log','return','info']))
    for key in ['locations_can_move','locations_can_choose','locations_can_repair','locations_idle','locations_can_log','locations_log_older','locations_log_newer']:
        parameters['params'].append(dict(key=key,name=key,options=['no','yes']))
    for key in ['locations_status1','locations_status2','locations_status3']:
        parameters['params'].append(dict(key=key,name=key,type='readout',display='string'))
    parameters['params'].append(dict(key='locations_return',name='Return plugins to Internal',type='trigger',momentary=True))
    parameters['params'].append(dict(key='locations_can_return',name='Return available',options=['no','yes']))
    for key in ['storage_warning','storage_tip']:
        parameters['params'].append(dict(key=key,name=key,type='readout',display='string'))
    for key in ['storage_list','storage_details','storage_has_prev','storage_has_next']:
        parameters['params'].append(dict(key=key,name=key,options=['no','yes']))
    for key in ['storage_prev','storage_next']:
        parameters['params'].append(dict(key=key,name=key,type='trigger',momentary=True))
    for row in range(1,4):
        parameters['params'].append(dict(key=f'storage_move_{row}',name='Move here',type='trigger',momentary=True))
        for suffix in ['visible','move']:
            parameters['params'].append(dict(key=f'storage_row{row}_{suffix}',name=suffix,options=['no','yes','blocked'] if suffix=='move' else ['no','yes']))
        for suffix in ['label','space','status']:
            parameters['params'].append(dict(key=f'storage_row{row}_{suffix}',name=suffix,type='readout',display='string'))
    for row in range(1,4):
        parameters['params'].append(dict(key=f'storage_row{row}_busy',name='Calculating move',options=['no','yes']))
    (vst/'params.json').write_text(json.dumps(parameters,indent=2)+'\n')
    art('locations.svg',1280,628,'<rect width="1280" height="628" fill="#0c0c0d"/>'+text(32,55,'PLUGIN STORAGE',40))
    art('storage_row.svg',1232,98,'<rect width="1232" height="98" rx="12" fill="#151a23"/>')
    lines=['\n[tab STORAGE]','art file=images/locations.svg']
    for key,y,size in [('storage_warning',177,32),('storage_tip',211,27)]:
        lines.append(f'readout box=0 w=1180 h=36 cx=640 cy={y} label="" key={key} tsize={size} tcolor=e9edff tpad=0 when=storage_list:yes')
    button('storage_move.svg','Move here',350,64,True,font=32)
    art('storage_move_blocked.svg',350,64,'<rect width="350" height="64" rx="12" fill="#343a43"/>'+text(18,41,'Move here',32,'#aeb4bf'))
    art('storage_calculating.svg',350,64,'<rect width="350" height="64" rx="12" fill="#454b54"/>'+'<text x="175" y="43" text-anchor="middle" font-family="Titillium Web, sans-serif" font-size="30" fill="#c7cbd1">Calculating...</text>')
    for row in range(1,4):
        y=280+(row-1)*110
        lines.append(f'art file=images/storage_row.svg x=24 y={y-44} w=1232 h=98 when=storage_row{row}_visible:yes')
        for suffix,x,cy,w,size in [('label',245,y-12,390,42),('space',655,y-12,340,38),('status',440,y+26,780,29)]:
            lines.append(f'readout box=0 w={w} h=40 cx={x} cy={cy} label="" key=storage_row{row}_{suffix} tsize={size} tcolor=e9edff tpad=0 when=storage_row{row}_visible:yes')
        lines.append(f'art file=images/storage_calculating.svg x=875 y={y-32} w=350 h=64 when=storage_row{row}_busy:yes')
        lines.append(f'button cx=1050 cy={y} label="" key=storage_move_{row} img=images/storage_move.svg w=350 h=64 when=storage_row{row}_move:yes')
        lines.append(f'art file=images/storage_move_blocked.svg x=875 y={y-32} w=350 h=64 when=storage_row{row}_move:blocked')
    for key,y,size in [('locations_drive',270,42),('locations_info',320,36),('locations_status1',400,38),('locations_status2',445,38),('locations_status3',490,38)]:
        lines.append(f'readout box=0 w=1180 h=46 cx=640 cy={y} label="" key={key} tsize={size} tcolor=e9edff tpad=0 when=storage_details:yes')
    for key,label,x,y,w,h,primary,condition,asset in [
        ('storage_prev','Previous',200,577,300,44,False,'storage_has_prev:yes','previous'),
        ('storage_next','More drives',1080,577,300,44,False,'storage_has_next:yes','next'),
        ('locations_scan','Refresh drives',180,642,300,72,False,'locations_idle:yes','refresh'),
        ('locations_log','View debug log',510,642,230,44,False,'locations_can_log:yes','log'),
        ('locations_repair','Repair plugin skins',980,642,500,72,False,'locations_can_repair:yes','repair'),
        ('locations_log_prev','Older event',320,562,570,64,False,'locations_log_older:yes','older'),
        ('locations_log_next','Newer event',960,562,570,64,False,'locations_log_newer:yes','newer'),
        ('locations_cancel','Back to Storage',640,642,570,72,False,'locations_ready:log','back_log'),
        ('locations_cancel','Back to Storage',640,642,570,72,False,'locations_ready:info','back_info'),
        ('locations_cancel','Go back',320,642,570,72,False,'locations_ready:move','back_move'),
        ('locations_cancel','Go back',320,642,570,72,False,'locations_ready:repair','back_repair'),
        ('locations_cancel','Go back',320,642,570,72,False,'locations_ready:return','back_return'),
        ('locations_confirm','Move & restart',960,642,570,72,True,'locations_ready:move','move'),
        ('locations_confirm','Repair skins & restart',960,642,570,72,True,'locations_ready:repair','repair_confirm'),
        ('locations_confirm','Return & restart',960,642,570,72,True,'locations_ready:return','return_confirm')]:
        if asset=='log':
            art('locations_log.svg',w,h,text(12,30,label,26,'#9ba4b2'))
        else:
            button('locations_'+asset+'.svg',label,w,h,primary,font=30)
        lines.append(f'button cx={x} cy={y} label="" key={key} img=images/locations_{asset}.svg w={w} h={h} when={condition}')
    with (vst/'layout.conf').open('a') as f:f.write('\n'.join(lines)+'\n')
    # The catalog header shows both internal and configured download-drive space.
    layout=(vst/'layout.conf').read_text().splitlines()
    layout=[line for line in layout if 'key=disk ' not in line and 'key=disk_txt ' not in line]
    index=next(i for i,line in enumerate(layout) if '[tab CATALOG]' in line)+1
    layout[index:index]=[
        'readout box=0 w=530 h=32 cx=980 cy=103 label="" key=storage_internal tsize=30 tcolor=ececed talign=right tpad=0',
        'readout box=0 w=530 h=32 cx=980 cy=137 label="" key=storage_preferred tsize=30 tcolor=72e6cc talign=right tpad=0']
    layout=[line.replace('x=930 y=104','x=570 y=104') if 'images/net_' in line else line for line in layout]
    (vst/'layout.conf').write_text('\n'.join(layout)+'\n')
    # Remove the old static INTERNAL caption, bar and subtitle from background art.
    import xml.etree.ElementTree as ET
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    bg=vst/'images/bg.svg';tree=ET.parse(bg);root=tree.getroot()
    for e in list(root):
        if e.tag.endswith('text') and (''.join(e.itertext()) in ['INTERNAL','COMMUNITY INSTRUMENTS & PLUGINS']):root.remove(e)
        elif e.tag.endswith('rect') and e.get('x') in ['1036','1056']:root.remove(e)
    tree.write(bg,encoding='unicode')

    for key in ['remote_can_enable','remote_can_disable']:
        parameters=json.loads((vst/'params.json').read_text())
        parameters['params'].append(dict(key=key,name=key,options=['no','yes']))
        (vst/'params.json').write_text(json.dumps(parameters,indent=2)+'\n')

    # Readable navigation in the unused strip below the third card.
    data=json.loads((vst/'params.json').read_text())
    data['params'].append(dict(key='catalog_downloads_available',name='Download counts available',options=['no','yes']))
    data['params'].append(dict(key='catalog_dates_available',name='Update dates available',options=['no','yes']))
    controls=[]
    for mode,label,x,width in [('az','A-Z',16,64),('za','Z-A',88,64),('updated','Newest',160,96),('downloads','Popular',368,152),('oldest','Oldest',264,96)]:
        key='catalog_sort_'+mode
        if mode!='oldest':data['params'].append(dict(key=key,name=label,type='trigger',momentary=True))
        available=' when=catalog_downloads_available:yes' if mode=='downloads' else ' when=catalog_dates_available:yes' if mode in ('updated','oldest') else ''
        font=25
        color='#263c50' if mode in ('az','za') else '#493c32' if mode in ('updated','oldest') else '#59402c'
        art(key+'.svg',width,48,f'<rect width="{width}" height="48" rx="12" fill="{color}"/>'+f'<text x="{width/2:g}" y="33" text-anchor="middle" font-family="Titillium Web" font-size="{font}" fill="#e9edff">{html.escape(label)}</text>')
        controls.append(f'button cx={x+width//2} cy=618 label="" key={key} img=images/{key}.svg w={width} h=48'+available)
    labels=['hidden','#','Back','A-D','E-H','I-L','M-P','Q-T','U-Z']+list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    variants=[['Back'],['A-D','A','E','I','M','Q','U'],['E-H','B','F','J','N','R','V'],['I-L','C','G','K','O','S','W'],['M-P','D','H','L','P','T','X'],['Q-T','Y'],['U-Z','Z']]
    for group,label in enumerate(['#','A-D','E-H','I-L','M-P','Q-T','U-Z']):
        key=f'catalog_jump_{group}';show=f'catalog_jump_available_{group}'
        data['params'].append(dict(key=key,name='Jump '+label,type='trigger',momentary=True))
        data['params'].append(dict(key=show,name='Has '+label,options=['no','yes']))
        data['params'].append(dict(key=f'catalog_jump_label_{group}',name='Jump letter artwork',options=labels))
        for label in variants[group]:
            image=f'catalog_letter_{labels.index(label)}.svg'
            # A single bitmap button, including its label: no readout covers it.
            color='#233d53' if label=='Back' else '#354a5c'
            art(image,92,48,f'<rect width="92" height="48" rx="12" fill="{color}"/>'+f'<text x="46" y="33" text-anchor="middle" font-family="Titillium Web" font-size="28" fill="#e9edff">{html.escape(label)}</text>')
            # Keep legacy parameter IDs, but omit # and leave a 32px section gap.
            column=group-1 if '-' in label else group
            controls.append(f'button cx={598+column*100} cy=618 label="" key={key} img=images/{image} w=92 h=48 when=catalog_jump_label_{group}:{label}')
    data['params'].append(dict(key='catalog_sort_oldest',name='Oldest',type='trigger',momentary=True))
    (vst/'params.json').write_text(json.dumps(data,indent=2)+'\n')
    layout=(vst/'layout.conf').read_text()
    (vst/'layout.conf').write_text(layout.replace('[tab FIND]','\n'.join(controls)+'\n\n[tab FIND]'))

    art('about.svg',1280,628,
        '<rect width="1280" height="628" fill="#0c0c0d"/>' +
        text(40,54,'MagicStino OpenPlugin',44) +
        text(40,98,'OpenPlugin Manager 0.9.0',32,'#a4e5d3') +
        text(40,148,'MANUAL & SOURCE',24,'#a4e5d3') +
        text(40,183,'github.com/MagicStino/force-openplugin',28) +
        text(40,258,'NoQuestion & dustyslices — first documented VST method',28,'#a4e5d3') +
        text(40,292,'MPC-Forums: Proof of Concept: Custom Standalone Plugins · Sep 2026',25) +
        text(40,346,'poloq — original Plugin Manager',28,'#a4e5d3') +
        text(40,380,'github.com/poloq-instruments/mpc-vst-manager',26) +
        text(40,434,'sd88me / Open MPC — catalog setup, collection & tooling',28,'#a4e5d3') +
        text(40,468,'github.com/open-mpc/mpc-vst-plugins',26) +
        text(40,522,'MockbaTheBorg / MockbaMod — SSH, screen & mouse resources',28,'#a4e5d3') +
        text(40,556,'github.com/MockbaTheBorg/MockbaMod',26))
    with (vst/'layout.conf').open('a') as f:f.write('\n[tab ABOUT]\nart file=images/about.svg\n')

    # Keep the complete functional control set small; artwork is ordinary PNGs.
    data=json.loads((vst/'params.json').read_text())
    assert len(data['params'])<=256
    assert not any(p['key'].startswith(('previewpx_', 'preview_live_')) for p in data['params'])
