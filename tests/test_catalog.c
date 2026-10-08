/* Read-only smoke test for a saved real catalog; never starts services/installers. */
#include "../native/manager.c"
#include <assert.h>
int main(int argc,char **argv) {
    if (argc!=2) return 2;
    char *text=slurp(argv[1],16<<20);assert(text);
    pkg_t *packages=calloc(MAXPKG,sizeof *packages);assert(packages);
    list_t list={packages,0};const char *end=jobject(text,top_member,&list);
    assert(end && !*ws(end) && list.n>0);
    int downloads=0;
    for (int i=0;i<list.n;i++) if (packages[i].url[0]) {
        assert(!strncmp(packages[i].url,"https://",8));
        assert(strlen(packages[i].sha)==64);
        assert(strspn(packages[i].sha,"0123456789abcdefABCDEF")==64);
        downloads++;
    }
    printf("Real catalog: %d packages, %d HTTPS/SHA256 downloads PASS\n",list.n,downloads);
    free(packages);free(text);return 0;
}
