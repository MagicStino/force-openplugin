'use strict';
const $ = s => document.querySelector(s);
const photoDialog = $('#photo-dialog');
let photoOpener;
for (const button of document.querySelectorAll('[data-photo]')) button.addEventListener('click', () => {
 photoOpener=button;
 $('#photo-title').textContent=button.dataset.title;
 $('#photo-caption').textContent=button.dataset.caption;
 $('#photo-image').src=button.dataset.photo;
 $('#photo-image').alt=button.dataset.title+' on a physical Akai Force';
 $('#photo-view').style.setProperty('--photo-ratio',button.dataset.ratio);
 $('#photo-view').classList.toggle('photo-rotated',button.dataset.rotate==='true');
 photoDialog.showModal();
});
$('#close-photo').addEventListener('click',()=>photoDialog.close());
photoDialog.addEventListener('click',event=>{if(event.target===photoDialog)photoDialog.close();});
photoDialog.addEventListener('close',()=>photoOpener?.focus());
$('#device').addEventListener('change',event=>{
 const messages={force:'A candidate was built from the exact examined Force image. The owner reports successful Force boot, touch, plugin use and ROM download. Combined 3.9.1.7 setup and SSH login remain unverified.',mpc:'A candidate exists for the exact examined MPC Gen1 image. Target model, updater acceptance and device operation still require validation.',other:'No validated adapter is established for this device. A similar model name does not establish image compatibility.','':'Select a device for its research status. This is not installation advice.'};
 $('#device-result').textContent=messages[event.target.value];
});
for(const button of document.querySelectorAll('[data-copy]')) button.addEventListener('click',async()=>{
 try{await navigator.clipboard.writeText(document.getElementById(button.dataset.copy).innerText);$('#toast').textContent='Copied. Nothing was executed.';setTimeout(()=>$('#toast').textContent='',2800);}
 catch{ $('#toast').textContent='Clipboard unavailable. Select and copy the text manually.';setTimeout(()=>$('#toast').textContent='',4000);}
});
$('#faq-query').addEventListener('input',event=>{const query=event.target.value.toLocaleLowerCase();let count=0;for(const item of document.querySelectorAll('#faq-list details')){const show=item.textContent.toLocaleLowerCase().includes(query);item.hidden=!show;if(show)count++;}$('#faq-empty').hidden=!!count;});
let catalog=[],kind='all',limit=12;
function renderCatalog(){
 const query=$('#catalog-query').value.trim().toLocaleLowerCase();
 const matches=catalog.filter(p=>(kind==='all'||p.kind===kind||(kind==='sampler'&&(p.tags.includes('sampler')||p.style==='sampler'))||(kind==='tracker'&&(p.tags.includes('tracker')||p.style==='tracker')))&&[p.name,p.summary,p.author,p.id,p.kind,...p.tags].join(' ').toLocaleLowerCase().includes(query));
 $('#catalog-cards').replaceChildren();
 const labels={instrument:'Instrument',effect:'Effect',addin:'Tool / addin',tracker:'Tracker',sampler:'Sampler'};
 for(const p of matches.slice(0,limit)){
  const article=document.createElement('article');article.className='catalog-item';
  const badge=document.createElement('span');badge.className='badge';badge.textContent=(p.tags.includes('sampler')||p.style==='sampler')?'Sampler':labels[p.kind]||p.kind;
  const title=document.createElement('h3');title.textContent=p.name;
  const author=document.createElement('p');author.textContent='Author: '+p.author;
  const tags=document.createElement('p');tags.className='tags';tags.textContent=p.tags.join(' · ')||'No tags';
  const state=document.createElement('p');state.textContent=p.download?'Package listed · device compatibility unverified':'Source only · no compatible download';
  const repo=/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/.test(p.repo)?'https://github.com/'+p.repo:null;
  const media=document.createElement(repo?'a':'div');media.className='plugin-media';
  if(repo){media.href=repo;media.setAttribute('aria-label','View '+p.name+' project');}
  let imageURL;try{imageURL=new URL(p.screenshot);}catch{}
  if(imageURL&&imageURL.protocol==='https:'&&['raw.githubusercontent.com','github.com','user-images.githubusercontent.com'].includes(imageURL.hostname)){
   const img=document.createElement('img');img.src=imageURL.href;img.alt=p.name+' — upstream screenshot';img.loading='lazy';img.referrerPolicy='no-referrer';img.addEventListener('error',()=>{img.remove();media.textContent='Preview unavailable';});media.append(img);
  }else{media.textContent='No upstream image';}
  const summary=document.createElement('p');summary.textContent=p.summary||'';
  const links=document.createElement('p');if(repo){const link=document.createElement('a');link.href=repo;link.textContent='Project & documentation ↗';links.append(link);}
  const actions=document.createElement('p');actions.className='card-actions';
  const version=(p.versions||[]).find(v=>!v.yanked&&v.url);
  const action=document.createElement('a');action.className='button';
  action.href=version&&repo?repo+'/releases':repo||'#sources';action.textContent=version?'View release ↗':'View source ↗';actions.append(action);
  
  const provenance=document.createElement('p');provenance.className='tags';provenance.textContent='Source: '+(p.provenance?.source||'Saved upstream catalog')+' · hardware unverified';
  const license=document.createElement('p');license.className='tags';license.textContent='License: '+(p.license||'See upstream');
  const details=document.createElement('details'),label=document.createElement('summary');label.textContent='Details & source';details.append(label,tags,license,provenance);
  state.textContent=p.download?'Package listed':'Source only';
  article.append(media,badge,title,author,summary,state,actions,details);$('#catalog-cards').append(article);
 }
 $('#catalog-count').textContent=matches.length?`${matches.length} of ${catalog.length} indexed entries · ${Math.min(limit,matches.length)} shown`:'No matching entries. Try All or clear the filter.';
 $('#catalog-more').hidden=matches.length<=limit;
}
for(const button of document.querySelectorAll('[data-kind]'))button.addEventListener('click',()=>{kind=button.dataset.kind;limit=12;for(const b of document.querySelectorAll('[data-kind]')){b.classList.toggle('selected',b===button);b.setAttribute('aria-pressed',String(b===button));}renderCatalog();});
$('#catalog-query').addEventListener('input',()=>{limit=12;renderCatalog();});
for(const button of document.querySelectorAll('[data-example]'))button.addEventListener('click',()=>{$('#catalog-query').value=button.dataset.example;document.querySelector('[data-kind="all"]').click();});
$('#catalog-more').addEventListener('click',()=>{limit+=12;renderCatalog();});
fetch('assets/catalog.json').then(r=>{if(!r.ok)throw new Error('catalog');return r.json();}).then(data=>{catalog=data.plugins;renderCatalog();}).catch(()=>{$('#catalog-count').textContent='The saved catalog could not load. The guides remain available; use the upstream catalog to browse.';});
