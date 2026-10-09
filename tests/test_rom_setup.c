/* No ROM bytes, network, or device changes needed. */
#include "../native/manager.c"
#include <assert.h>
int main(void){
 char dir[]="/tmp/openplugin-rom-test-XXXXXX";assert(mkdtemp(dir));
 char src[512],dst[512];snprintf(src,sizeof src,"%s/source",dir);snprintf(dst,sizeof dst,"%s/destination",dir);
 FILE *f=fopen(src,"wb");assert(f);fputs("new",f);fclose(f);
 assert(rom_regular(src,3));assert(!rom_regular(src,4));assert(rom_copy_missing(src,dst));
 f=fopen(dst,"wb");assert(f);fputs("user-state",f);fclose(f);
 assert(rom_copy_missing(src,dst));assert(rom_regular(dst,10)); /* NVRAM is preserved */
 unlink(dst);assert(!symlink(src,dst));assert(!rom_regular(dst,3));unlink(dst);
 assert(!symlink(src,dst));assert(rom_copy_missing(src,dst));assert(rom_regular(src,3));
 unlink(dst);unlink(src);rmdir(dir);
 device_t *d=calloc(1,sizeof *d);char folder[768];assert(!rom_folder(d,folder,sizeof folder));
 d->nent=1;strcpy(d->ent[0].uid,"4a563838");strcpy(d->ent[0].file,"/tmp/unrelated/jv880.so");assert(!rom_folder(d,folder,sizeof folder));free(d);
 mgr_t *m=calloc(1,sizeof *m);assert(m);pthread_mutex_init(&m->mu,0);m->dev=calloc(1,sizeof *m->dev);m->npkg=1;m->sel=m->menu=-1;
 strcpy(m->pkg[0].id,"jv-880");strcpy(m->pkg[0].name,"JV-880");strcpy(m->pkg[0].installed,"1.0.6");
 strcpy(m->pkg[0].url,"https://github.com/sd88me/mpc-vst-jv880/releases/download/test/test.zip");strcpy(m->query,"880");int idx[MAXPKG];assert(visible(m,idx)==1);
 char b[160];mgr_get_param(m,"r1_rom",b,sizeof b);assert(!strcmp(b,"1"));
 mgr_set_param(m,"r1_rom_install","1");assert(m->job==J_JV_INSTALL);assert(m->pkg[0].queued==Q_INSTALL);assert(strstr(m->status,"step 1/2"));
 m->pkg[0].installed[0]=0;mgr_get_param(m,"r1_rom",b,sizeof b);assert(!strcmp(b,"1"));
 m->job=J_NONE;m->busy=J_REFRESH;mgr_set_param(m,"r1_rom_install","1");assert(m->job==J_NONE && strstr(m->status,"Please wait"));
 m->busy=J_NONE;strcpy(m->pkg[0].id,"other");m->query[0]=0;mgr_get_param(m,"r1_rom",b,sizeof b);assert(!strcmp(b,"0"));
 FILE *script=tmpfile();assert(script);rom_write_apply(script,"/tmp/Synths");rewind(script);char output[8192];size_t len=fread(output,1,sizeof output-1,script);output[len]=0;assert(strstr(output,"cp -n") && strstr(output,"wc -c") && strstr(output,"jv880_nvram.bin"));fclose(script);
 pthread_mutex_destroy(&m->mu);free(m->dev);free(m);
 puts("ROM setup tests passed");return 0;
}
