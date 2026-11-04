/* Parse the actual merged snapshot through the device's native parser. */
#include "../native/manager.c"
#include <assert.h>
int main(int argc,char **argv) {
    assert(argc==3);
    pkg_t *fixture=calloc(MAXPKG,sizeof *fixture);assert(fixture);list_t test={fixture,0};
    assert(catalog_parse("{\"plugins\":[{\"id\":\"gen2\",\"name\":\"Gen2\",\"versions\":[{\"version\":\"1\",\"url\":\"https://github.com/o/r/releases/download/v1/Plugin-mpc-aarch64.zip\"}]}]}",&test));
    assert(!fixture[0].url[0]);memset(fixture,0,MAXPKG*sizeof *fixture);test.n=0;
    assert(catalog_parse("{\"plugins\":[{\"id\":\"gen2\",\"name\":\"Gen2\",\"versions\":[{\"version\":\"1\",\"arch\":\"aarch64\",\"url\":\"https://github.com/o/r/releases/download/v1/plugin.zip\"}]}]}",&test));
    assert(!fixture[0].url[0]);free(fixture);
    char *text=slurp(argv[1],16<<20);assert(text);
    pkg_t *packages=calloc(MAXPKG,sizeof *packages);assert(packages);
    list_t list={packages,0};assert(catalog_parse(text,&list));
    assert(list.n==atoi(argv[2]));
    int downloads=0;
    for(int i=0;i<list.n;i++) {
        assert(preview_frame(packages[i].id)>1);
        if(packages[i].url[0]) {assert(!strncmp(packages[i].url,"https://github.com/",19) || !strncmp(packages[i].url,"https://raw.githubusercontent.com/",34));assert(strlen(packages[i].sha)==64);assert(strspn(packages[i].sha,"0123456789abcdefABCDEF")==64);assert(packages[i].size>0);downloads++;}
    }
    printf("Native catalog: %d entries, %d validated downloads, all artwork IDs mapped\n",list.n,downloads);
    free(packages);free(text);return 0;
}
