#include "../native/manager.c"
#include <assert.h>
int main(void){
 mgr_t *m=calloc(1,sizeof *m);assert(m);pthread_mutex_init(&m->mu,NULL);pthread_cond_init(&m->cv,NULL);
 m->npkg=26;char out[96];int idx[MAXPKG];
 for(int k=0;k<26;k++){snprintf(m->pkg[k].id,48,"p%d",k);snprintf(m->pkg[k].name,96,"[SYN] %c synth",'Z'-k);strcpy(m->pkg[k].kind,"instrument");}
 m->pkg[0].queued=Q_INSTALL;
 visible(m,idx);assert(idx[0]==25&&idx[25]==0);
 mgr_set_param(m,"catalog_sort_za","1");visible(m,idx);assert(idx[0]==0&&idx[25]==25);
 // Every exact letter jumps to its containing page, including Y/Z in U-Z.
 for(int c='A';c<='Z';c++){
  m->jump_group=0;int group=1+(c-'A')/4;if(group>6)group=6;
  char key[64];snprintf(key,sizeof key,"catalog_jump_%d",group);mgr_set_param(m,key,"1");
  assert(m->page==((group-1)*4)/3);
  if(group<6){mgr_get_param(m,"catalog_jump_available_5",out,sizeof out);assert(!strcmp(out,"0"));mgr_get_param(m,"catalog_jump_available_6",out,sizeof out);assert(!strcmp(out,"0"));}
  unsigned rev=m->rev;int chosen=m->jump_group,page=m->page;
  for(int echo=0;echo<7;echo++){
   char field[64];snprintf(field,sizeof field,"catalog_jump_available_%d",echo);mgr_set_param(m,field,"1");
   snprintf(field,sizeof field,"catalog_jump_label_%d",echo);mgr_set_param(m,field,"1");
  }
  assert(m->rev==rev&&m->jump_group==chosen&&m->page==page);
  int slot=c-('A'+(group-1)*4)+1;snprintf(key,sizeof key,"catalog_jump_%d",slot);mgr_set_param(m,key,"1");
  assert(m->sort_mode==0&&m->page==(c-'A')/3);
 }
 m->pkg[7].downloads_known=1;m->pkg[7].downloads=100;m->pkg[3].downloads_known=1;m->pkg[3].downloads=0;
 mgr_set_param(m,"catalog_sort_downloads","1");visible(m,idx);assert(idx[0]==7&&idx[1]==3);
 m->pkg[10].updated=20261106;m->pkg[11].updated=20250101;
 mgr_set_param(m,"catalog_sort_updated","1");visible(m,idx);assert(idx[0]==10&&idx[1]==11);
 mgr_set_param(m,"catalog_sort_oldest","1");visible(m,idx);assert(idx[0]==11&&idx[1]==10&&m->pkg[idx[2]].updated==0);
 assert(m->pkg[0].queued==Q_INSTALL);
 for(int mode=2;mode<=4;mode++){
  m->sort_mode=mode;m->jump_group=1;m->rev++;
  for(int slot=0;slot<7;slot++){
   char key[64];snprintf(key,sizeof key,"catalog_jump_label_%d",slot);mgr_get_param(m,key,out,sizeof out);assert(!strcmp(out,"0"));
   snprintf(key,sizeof key,"catalog_jump_available_%d",slot);mgr_get_param(m,key,out,sizeof out);assert(!strcmp(out,"0"));
   snprintf(key,sizeof key,"catalog_jump_%d",slot);mgr_set_param(m,key,"1");assert(m->sort_mode==mode);
  }
 }
 mgr_set_param(m,"catalog_sort_za","1");mgr_get_param(m,"catalog_jump_available_1",out,sizeof out);assert(!strcmp(out,"1"));
 mgr_set_param(m,"catalog_sort_az","1");mgr_get_param(m,"catalog_jump_available_1",out,sizeof out);assert(!strcmp(out,"1"));
 strcpy(m->query,"M synth");m->rev++;mgr_get_param(m,"catalog_jump_available_4",out,sizeof out);assert(!strcmp(out,"1"));
 mgr_set_param(m,"catalog_jump_4","1");mgr_get_param(m,"catalog_jump_label_1",out,sizeof out);assert(atoi(out)==9+'M'-'A');
 mgr_get_param(m,"catalog_jump_available_2",out,sizeof out);assert(!strcmp(out,"0"));
 mgr_set_param(m,"catalog_jump_1","1");assert(m->page==0);
 assert(catalog_date("2024-02-29T12:00:00Z")==20240229);assert(!catalog_date("2025-02-29"));
 pkg_t p={0};assert(jobject("{\"downloads\":0,\"updated_at\":\"2026-11-06\"}",pkg_member,&p));assert(p.downloads_known&&p.downloads==0&&p.updated==20261106);
 memset(&p,0,sizeof p);assert(jobject("{\"updated\":\"2026-11-06\",\"downloads\":123}",pkg_member,&p));assert(p.updated==20261106&&p.downloads==123);
 ver_t release={0};assert(jobject("{\"date\":\"2026-10-05\"}",ver_member,&release));assert(release.updated==20261005);
 memset(&p,0,sizeof p);assert(jobject("{\"versions\":[{\"version\":\"1\",\"url\":\"https://example.org/a.zip\",\"date\":\"2026-10-05\"}]}",pkg_member,&p));assert(p.updated==20261005);
 memset(&p,0,sizeof p);assert(jobject("{\"versions\":[{\"version\":\"1\",\"url\":\"https://example.org/a.zip\",\"date\":\"2026-10-05\"}],\"updated\":\"2026-11-06\"}",pkg_member,&p));assert(p.updated==20261106);
 memset(&p,0,sizeof p);assert(jobject("{\"downloads\":-2}",pkg_member,&p));assert(!p.downloads_known);
 pthread_cond_destroy(&m->cv);pthread_mutex_destroy(&m->mu);free(m);return 0;
}
