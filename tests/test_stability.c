/* Failure cases and persisted catalog, no network or device services. */
#include "../native/manager.c"
#include <assert.h>
int main(int argc,char **argv) {
 pkg_t *p=calloc(MAXPKG,sizeof *p);assert(p);list_t l={p,0};
 const char *valid="{\"plugins\":[{\"id\":\"test\",\"name\":\"Test\"}]}";
 assert(catalog_parse(valid,&l));l.n=0;assert(!catalog_parse("{\"plugins\":[]}",&l));
 assert(!catalog_parse("{\"plugins\":[{\"id\":\"test\",\"name\":\"Test\"}] trailing}",&l));
 l.n=0;assert(!catalog_parse("{\"plugins\":[{\"id\":\"a\",\"name\":\"A\"},{\"id\":\"a\",\"name\":\"B\"}]}",&l));
 char dir[]="/tmp/openplugin-cache-XXXXXX";assert(mkdtemp(dir));char path[512];snprintf(path,sizeof path,"%s/catalog.json",dir);
 catalog_save(path,valid);char *saved=slurp(path,10000);assert(saved&&!strcmp(saved,valid));free(saved);
 unlink(path);assert(!symlink("/dev/null",path));catalog_save(path,valid);saved=slurp(path,10000);assert(saved&&!strcmp(saved,valid));free(saved);unlink(path);rmdir(dir);
 if(argc==3){FILE *f=fopen(argv[1],"w");assert(f);fputs("#!/bin/sh\nset -e\n",f);rom_write_apply(f,argv[2]);fclose(f);}
 free(p);puts("Catalog persistence/failure tests passed");return 0;
}
