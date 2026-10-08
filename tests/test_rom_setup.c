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
 puts("ROM setup tests passed");return 0;
}
