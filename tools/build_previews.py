#!/usr/bin/env python3
"""Build bounded, offline device thumbnails from hash-locked upstream screenshots."""
import argparse, hashlib, io, json, os
from pathlib import Path
import urllib.request, urllib.parse
from concurrent.futures import ThreadPoolExecutor
from PIL import Image, ImageDraw, ImageFont, ImageOps
ROOT=Path(__file__).resolve().parents[1]
LIMIT=4*1024*1024
Image.MAX_IMAGE_PIXELS=16_000_000

def allowed(url):
    u=urllib.parse.urlsplit(url)
    return u.scheme=='https' and not u.username and not u.password and u.port in (None,443) and (u.hostname in ('github.com','raw.githubusercontent.com','user-images.githubusercontent.com') or (u.hostname or '').endswith('.githubusercontent.com'))
class Redirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        if not allowed(newurl): raise ValueError('Unapproved screenshot redirect')
        return super().redirect_request(req,fp,code,msg,headers,newurl)
def fetch(url):
    if not allowed(url): raise ValueError('Unapproved screenshot URL')
    with urllib.request.build_opener(Redirects()).open(urllib.request.Request(url,headers={'User-Agent':'OpenPlugin-Research-preview-builder/1'}),timeout=25) as r:
        data=r.read(LIMIT+1)
    if len(data)>LIMIT: raise ValueError('Screenshot exceeds 4 MiB')
    with Image.open(io.BytesIO(data)) as image:
        if image.format not in ('PNG','JPEG','WEBP','GIF') or image.width*image.height>16_000_000: raise ValueError('Unsupported or oversized image')
        image.load()
    return data

def index_header(entries):
    ids=',\n'.join('    '+json.dumps(p['id']) for p in entries)
    return '/* Generated from assets/previews.lock.json; slots 0 blank, 1 unavailable. */\nstatic const char *const preview_ids[] = {\n'+ids+'\n};\nstatic int preview_frame(const char *id) {\n    for (unsigned i=0;i<sizeof preview_ids/sizeof *preview_ids;i++)\n        if (!strcmp(id,preview_ids[i])) return (int)i+2;\n    return 1;\n}\n'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cache',type=Path,default=ROOT/'.deps/previews')
    p.add_argument('--output',type=Path)
    p.add_argument('--update-lock',action='store_true',help='Explicitly refresh screenshot inputs from the website snapshot')
    args=p.parse_args();args.cache.mkdir(parents=True,exist_ok=True)
    lockpath=ROOT/'assets/previews.lock.json'
    if args.update_lock:
        source=json.loads((ROOT/'website/assets/catalog.json').read_text())['plugins']
        def capture(item):
            entry={k:item.get(k,'') for k in ('id','name','repo','license','screenshot')}
            entry['sha256']=None
            if entry['screenshot']:
                try:
                    data=fetch(entry['screenshot']);sha=hashlib.sha256(data).hexdigest();(args.cache/sha).write_bytes(data);entry['sha256']=sha
                except Exception as e: entry['unavailable_reason']=type(e).__name__
            return entry
        with ThreadPoolExecutor(max_workers=4) as pool: entries=list(pool.map(capture,sorted(source,key=lambda x:x['id'])))
        lock={'schema':1,'snapshot_date':'2026-10-08','entries':entries}
        lockpath.write_text(json.dumps(lock,indent=2)+'\n')
        (ROOT/'native/preview_index.h').write_text(index_header(entries))
    else:
        lock=json.loads(lockpath.read_text());entries=lock['entries']
        if (ROOT/'native/preview_index.h').read_text()!=index_header(entries): raise SystemExit('Preview index differs from lock; regenerate deliberately')
    if args.output:
        args.output.mkdir(parents=True,exist_ok=True)
        Image.new('RGBA',(176,86)).save(args.output/'preview_0.png')
        fallback=Image.new('RGB',(176,86),'#20252c');d=ImageDraw.Draw(fallback);d.rectangle((12,12,164,74),outline='#69717a');d.text((88,43),'NO PREVIEW',fill='#c4c9cf',anchor='mm')
        fallback.save(args.output/'preview_1.png')
        for i,entry in enumerate(entries,2):
            sha=entry['sha256'];thumb=fallback.copy()
            if sha:
                file=args.cache/sha
                if not file.exists(): file.write_bytes(fetch(entry['screenshot']))
                data=file.read_bytes()
                if hashlib.sha256(data).hexdigest()!=sha: raise SystemExit('Screenshot hash changed: '+entry['id']+'; review and update the lock explicitly')
                with Image.open(io.BytesIO(data)) as image:
                    image=ImageOps.exif_transpose(image).convert('RGBA');image.thumbnail((176,86),Image.Resampling.LANCZOS)
                    thumb=Image.new('RGB',(176,86),'#13161b');thumb.paste(image,((176-image.width)//2,(86-image.height)//2),image)
            thumb.save(args.output/f'preview_{i}.png',optimize=False)
    print(f'Preview lock: {len(entries)} entries, {sum(bool(x["sha256"]) for x in entries)} upstream images; unknown IDs use fallback')
if __name__=='__main__': main()
