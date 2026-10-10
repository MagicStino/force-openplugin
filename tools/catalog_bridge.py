#!/usr/bin/env python3
"""Bounded community catalog bridge. Reads JSON/API metadata; never executes packages."""
import argparse,datetime,json,os,re,tempfile,time,urllib.parse,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
REPO=re.compile(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z');ID=re.compile(r'[a-z0-9][a-z0-9-]{0,62}\Z');SHA=re.compile(r'[0-9a-fA-F]{64}\Z')
MAX_BYTES=8*1024*1024

def https(url,hosts=None):
 try:
  u=urllib.parse.urlsplit(url)
  return u.scheme=='https' and bool(u.hostname) and not u.username and not u.password and u.port in (None,443) and (hosts is None or u.hostname in hosts)
 except (TypeError,ValueError):return False

def read_json(url):
 if not https(url,{'api.github.com','raw.githubusercontent.com','sd88me.github.io'}):raise ValueError('Unapproved metadata host')
 headers={'User-Agent':'OpenPlugin-Research-catalog-bridge/1','Accept':'application/vnd.github+json'}
 token=os.environ.get('GITHUB_TOKEN')
 if token and urllib.parse.urlsplit(url).hostname=='api.github.com':headers['Authorization']='Bearer '+token
 request=urllib.request.Request(url,headers=headers)
 # No cross-host redirect can receive an authenticated API request.
 class NoRedirect(urllib.request.HTTPRedirectHandler):
  def redirect_request(self,*args,**kwargs):raise ValueError('Metadata redirects are not accepted')
 for attempt in range(3):
  try:
   with urllib.request.build_opener(NoRedirect()).open(request,timeout=20) as response:data=response.read(MAX_BYTES+1)
   if len(data)>MAX_BYTES:raise ValueError('Metadata too large')
   return json.loads(data)
  except urllib.error.HTTPError as e:
   if e.code not in (500,502,503,504) or attempt==2:raise
   time.sleep(attempt+1)

def validate_manifest(m,repo):
 if not isinstance(m,dict) or m.get('schema')!='openplugin.community/1':raise ValueError('Unsupported manifest schema')
 if m.get('repo')!=repo or not REPO.fullmatch(repo):raise ValueError('Repository identity mismatch')
 if not ID.fullmatch(m.get('id','')):raise ValueError('Invalid plugin ID')
 for key in ('name','author','summary','license'):
  if not isinstance(m.get(key),str) or not m[key].strip() or len(m[key])>1024:raise ValueError('Missing/invalid '+key)
 if m.get('kind') not in ('instrument','effect','addin'):raise ValueError('Invalid host plugin kind')
 if m.get('category') not in ('synth','effect','sampler','tracker','tool'):raise ValueError('Invalid browse category')
 if not isinstance(m.get('tags',[]),list) or any(not isinstance(t,str) or len(t)>80 for t in m.get('tags',[])):raise ValueError('Invalid tags')
 for url in m.get('images',[]):
  if not https(url,{'github.com','raw.githubusercontent.com','user-images.githubusercontent.com'}):raise ValueError('Invalid preview URL')
 for p in m.get('packages',[]):
  if p.get('arch')!='armv7' or p.get('layout')!='portable':raise ValueError('Unsupported package target')
  if not p.get('version') or not isinstance(p.get('size'),int) or p['size']<=0:raise ValueError('Invalid package metadata')
  if not https(p.get('url'),{'github.com'}) or not urllib.parse.urlsplit(p['url']).path.startswith('/'+repo+'/releases/download/'):raise ValueError('Package must belong to repository release')
  if not SHA.fullmatch(p.get('sha256','')):raise ValueError('Missing package SHA256')
  if not isinstance(p.get('devices'),list) or not p['devices'] or any(d not in ('force','mpc-gen1') for d in p['devices']):raise ValueError('Invalid declared device targets')
 return m

def normalize_plugin(p,source):
 if not isinstance(p,dict) or not ID.fullmatch(p.get('id','')) or not REPO.fullmatch(p.get('repo','')):raise ValueError('Invalid catalog identity')
 if not isinstance(p.get('name'),str) or not p['name'] or p.get('kind') not in ('instrument','effect','addin'):raise ValueError('Invalid catalog entry')
 p={k:v for k,v in p.items() if k in ('id','name','author','repo','kind','license','summary','screenshot','style','tags','source_available','distribution','versions','latest','components')};p['tags']=[t for t in p.get('tags',[]) if isinstance(t,str)][:32]
 p['versions']=[v for v in p.get('versions',[]) if isinstance(v,dict) and not v.get('yanked') and https(v.get('url'),{'github.com'}) and urllib.parse.urlsplit(v['url']).path.startswith('/'+p['repo']+'/releases/download/') and SHA.fullmatch(v.get('sha256',''))]
 p['versions']=[{k:value for k,value in v.items() if k in ('version','size','sha256','url','channel','yanked','cpu','tested','warnings','arch','max_glibc','os_compat')} for v in p['versions']]
 p['provenance']={'source':source,'repository':p['repo'],'hardware_verified_by_openplugin':False,'validation':'metadata-validated' if p['versions'] else 'listed-only'}
 return p

def atomic_json(path,value):
 path.parent.mkdir(parents=True,exist_ok=True)
 data=json.dumps(value,indent=2,ensure_ascii=False)+'\n'
 with tempfile.NamedTemporaryFile('w',dir=path.parent,delete=False,encoding='utf-8') as f:f.write(data);name=f.name
 os.replace(name,path)

def update(fetch=read_json):
 cfg=json.loads((ROOT/'catalog/sources.json').read_text());now=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
 # A failed primary source aborts before replacing any published file.
 upstream=fetch(cfg['upstream'])
 if upstream.get('schema')!=1 or not isinstance(upstream.get('plugins'),list) or not upstream['plugins']:raise ValueError('Invalid/empty upstream catalog; keeping prior output')
 if len(upstream['plugins'])>512:raise ValueError('Native catalog capacity exceeded')
 plugins=[];errors=[];ids=set()
 for item in upstream['plugins']:
  p=normalize_plugin(item,cfg['upstream'])
  if p['id'] in ids:raise ValueError('Duplicate upstream ID')
  ids.add(p['id']);plugins.append(p)
 repositories=set(cfg['repositories']);candidates={}
 if os.environ.get('GITHUB_TOKEN'):
  for query in cfg['search_queries'][:4]:
   try:
    result=fetch('https://api.github.com/search/repositories?q='+urllib.parse.quote(query)+'&per_page=15&sort=updated')
    for r in result.get('items',[]):
     repo=r.get('full_name','')
     if REPO.fullmatch(repo) and not r.get('archived'):candidates[repo]={'repo':repo,'name':r.get('name'), 'summary':r.get('description') or '', 'url':r.get('html_url'),'status':'discovered; not installable'}
   except Exception as e:errors.append({'stage':'search','query':query,'error':str(e)[:200]})
 known={p['repo'] for p in plugins}
 for repo in known:candidates.pop(repo,None)
 repositories.update(sorted(candidates)[:cfg['max_discovered_repositories']]);repositories-=known
 for repo in sorted(repositories)[:60]:
  if not REPO.fullmatch(repo):continue
  try:
   info=fetch('https://api.github.com/repos/'+repo);branch=info.get('default_branch','main')
   m=validate_manifest(fetch('https://raw.githubusercontent.com/'+repo+'/'+urllib.parse.quote(branch,safe='')+'/openplugin.json'),repo)
   if m['id'] in ids:raise ValueError('ID collision; review required')
   versions=[]
   # Publisher metadata alone cannot silently authorize an installer.
   if repo in cfg['reviewed_manifest_repositories']:
    for package in m.get('packages',[]):
     versions.append({'version':package['version'],'url':package['url'],'sha256':package['sha256'],'size':package['size'],'channel':'beta' if '-' in package['version'] else 'stable','yanked':False,'os_compat':['3.x'],'manifest':{'schema':1,'arch':'armv7','layout':'portable','kind':m['kind'],'source_repo':repo}})
   p=normalize_plugin({'id':m['id'],'name':m['name'],'author':m['author'],'summary':m['summary'],'license':m['license'],'kind':m['kind'],'style':m['category'],'tags':m.get('tags',[]),'repo':repo,'screenshot':next(iter(m.get('images',[])),''),'versions':versions},'https://github.com/'+repo+'/blob/'+branch+'/openplugin.json')
   plugins.append(p);ids.add(p['id']);candidates.pop(repo,None)
  except Exception as e:
   candidates.setdefault(repo,{'repo':repo,'url':'https://github.com/'+repo,'status':'needs compatible manifest; not installable'})
   errors.append({'stage':'manifest','repo':repo,'error':str(e)[:200]})
 # Compare the complete output: registered manifests are part of the previous catalog too.
 previous=ROOT/'website/catalog.json'
 if previous.exists():
  old=json.loads(previous.read_text()).get('plugins',[])
  if old and len(plugins)<len(old)*0.75:raise ValueError('Unexpected catalog shrink; manual review required')
 if len(plugins)>512:raise ValueError('Native catalog capacity exceeded')
 plugins.sort(key=lambda p:(p['name'].casefold(),p['id']))
 catalog={'schema':1,'bridge_schema':'openplugin.catalog/1','generated':now,'source':cfg['upstream'],'plugins':plugins}
 cards={'date':now,'source':cfg['upstream'],'plugins':[dict(p,download=bool(p['versions'])) for p in plugins]}
 report={'generated':now,'indexed':len(plugins),'candidates':list(candidates.values()),'errors':errors,'hardware_verified':False}
 atomic_json(ROOT/'website/catalog.json',catalog);atomic_json(ROOT/'website/assets/catalog.json',cards);atomic_json(ROOT/'website/discovery.json',report)
 print(f"Catalog: {len(plugins)} indexed; {len(candidates)} review candidates; {len(errors)} source notices")

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--validate',type=Path);p.add_argument('--repo');a=p.parse_args()
 if a.validate:
  if not a.repo:p.error('--repo is required')
  validate_manifest(json.loads(a.validate.read_text()),a.repo);print('Manifest metadata valid; binaries and hardware not tested')
 else:update()
if __name__=='__main__':main()
