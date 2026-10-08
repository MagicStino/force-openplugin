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
    mgr_t *m=calloc(1,sizeof *m);assert(m);m->npkg=list.n;memcpy(m->pkg,packages,list.n*sizeof *packages);
    int indices[MAXPKG];assert(visible(m,indices)==list.n);
    int categories[5];for(int i=1;i<=5;i++){m->kindf=i;categories[i-1]=visible(m,indices);}
    assert(categories[0]+categories[1]+categories[4]==list.n);
    printf("Browse index: all %d entries; %d instruments, %d effects, %d trackers, %d samplers, %d tools PASS\n",list.n,categories[0],categories[1],categories[2],categories[3],categories[4]);
    m->kindf=0;strcpy(m->query,"ambient");int n=visible(m,indices);assert(n>0); /* includes tags beyond the first two */
    free(m);
    free(packages);free(text);return 0;
}
